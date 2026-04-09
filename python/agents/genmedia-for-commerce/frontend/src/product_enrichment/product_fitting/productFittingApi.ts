/**
 * API service for Product Fitting functionality.
 * Calls the production JSON endpoint that returns the best front + back results.
 */

import { dataUrlToBase64, base64ToImageUrl } from '../../image_vto/services/imageVtoApi'

const API_BASE_URL = '/api/product-enrichment/product-fitting'

export interface GenerateFittingRequest {
  garmentImages: string[] // data URLs (front + optional back views)
  scenario: string
  maxRetries?: number
  generationModel?: string
  ethnicity: string
  gender: string
  modelPhotos?: string[] // data URLs for custom model photos (bypasses ethnicity/gender preset)
}

export interface FittingValidation {
  garments_score: number
  garment_details: Array<{ explanation: string; score: number }>
  discard: boolean
  wearing_score: number
  wearing_explanation: string
}

export interface FittingSideResult {
  imageUrl: string
  status: 'ready' | 'discarded'
  validation: FittingValidation
  totalAttempts: number
}

export interface FittingPipelineResult {
  front: FittingSideResult | null
  back: FittingSideResult | null
}

/**
 * Generates product fitting images using the production pipeline endpoint.
 * Returns the single best front and back results.
 */
export async function generateFitting(
  request: GenerateFittingRequest
): Promise<FittingPipelineResult> {
  const payload: Record<string, unknown> = {
    garment_images_base64: request.garmentImages.map(img => dataUrlToBase64(img)),
    scenario: request.scenario,
    max_retries: request.maxRetries ?? 5,
    generation_model: request.generationModel ?? 'gemini-3.1-flash-image-preview',
    ethnicity: request.ethnicity,
    gender: request.gender,
  }
  if (request.modelPhotos && request.modelPhotos.length > 0) {
    payload.model_photos_base64 = request.modelPhotos.map(img => dataUrlToBase64(img))
  }

  const response = await fetch(`${API_BASE_URL}/generate-fitting-pipeline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `Request failed with status ${response.status}`)
  }

  const data = await response.json()

  function parseSide(side: any): FittingSideResult | null {
    if (!side) return null
    return {
      imageUrl: base64ToImageUrl(side.image_base64),
      status: side.status,
      validation: side.validation,
      totalAttempts: side.total_attempts,
    }
  }

  return {
    front: parseSide(data.front),
    back: parseSide(data.back),
  }
}
