import { useState, useCallback } from 'react'
import GlassesImageVTOForm from '../components/GlassesImageVTOForm'
import type { GlassesVTOFormData } from '../components/GlassesImageVTOForm'
import ImageVTOPreview from '../components/ImageVTOPreview'
import { generateGlassesVTO } from '../services/glassesVtoApi'
import type { VTOResult } from '../services/imageVtoApi'
import type { Product } from '../../config/featureConstraints'

interface GlassesImageVTOProps {
  uploadedImage?: string | null
  onRemoveImage?: () => void
  showVideo?: boolean
  currentProduct?: Product
  availableProducts?: Product[]
  onProductChange?: (product: Product) => void
  prefilledModelImage?: string
  prefilledGlassesImage?: string
}

function GlassesImageVTO({
  uploadedImage,
  onRemoveImage,
  showVideo = true,
  currentProduct,
  availableProducts,
  onProductChange,
  prefilledModelImage,
  prefilledGlassesImage
}: GlassesImageVTOProps) {
  const [results, setResults] = useState<VTOResult[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async (formData: GlassesVTOFormData) => {
    // Validate required fields
    if (!formData.glassesImage || !formData.modelImage) {
      setError('Please upload glasses and model images')
      return
    }

    // Reset state for new generation
    setResults([])
    setError(null)
    setIsGenerating(true)

    try {
      await generateGlassesVTO(
        {
          glassesImage: formData.glassesImage,
          modelImage: formData.modelImage,
          numVariations: 3,
        },
        // onResult callback - add each result as it streams in
        (result) => {
          setResults(prev => {
            const existing = prev.findIndex(r => r.index === result.index)
            if (existing >= 0) {
              const updated = [...prev]
              updated[existing] = result
              return updated
            }
            return [...prev, result]
          })
        },
        // onComplete callback
        (total) => {
          console.log(`Glasses VTO generation complete. ${total} variations processed.`)
          setIsGenerating(false)
        },
        // onError callback
        (errorMessage) => {
          console.error('Glasses VTO generation error:', errorMessage)
          setError(errorMessage)
          setIsGenerating(false)
        }
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred'
      setError(message)
      setIsGenerating(false)
    }
  }, [])

  return (
    <div className="grid grid-cols-[480px_1fr] gap-6">
      <GlassesImageVTOForm
        onSubmit={handleSubmit}
        isGenerating={isGenerating}
        uploadedImage={uploadedImage}
        onRemoveImage={onRemoveImage}
        currentProduct={currentProduct}
        availableProducts={availableProducts}
        onProductChange={onProductChange}
        prefilledModelImage={prefilledModelImage}
        prefilledGlassesImage={prefilledGlassesImage}
      />

      <div>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
        <ImageVTOPreview
          showVideo={showVideo}
          results={results}
          isLoading={isGenerating}
          numVariations={3}
          mode="glasses"
        />
      </div>
    </div>
  )
}

export default GlassesImageVTO
