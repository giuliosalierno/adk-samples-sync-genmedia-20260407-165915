import BackgroundVideo from '../../components/BackgroundVideo'
import { openFeedbackForm } from '../../components/FeedbackButton'
import type { FittingPipelineResult } from './productFittingApi'

interface ProductFittingPreviewProps {
  className?: string
  showVideo?: boolean
  isLoading?: boolean
  error?: string | null
  result?: FittingPipelineResult | null
}

function ProductFittingPreview({
  className = '',
  showVideo = true,
  isLoading = false,
  error,
  result,
}: ProductFittingPreviewProps) {
  const panelClass = showVideo
    ? 'glass-panel rounded-lg'
    : 'rounded-lg border border-black/[0.08] dark:border-white/10'

  // Error state
  if (error) {
    return (
      <div className={`${panelClass} flex items-center justify-center min-h-[600px] overflow-hidden relative sticky top-24 self-start ${className}`}>
        <div className="text-center px-8 relative z-10">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="text-red-500">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h2 className="text-xl font-semibold mb-2 text-red-500">Generation Failed</h2>
          <p className="text-sm text-gm-text-secondary-light dark:text-gm-text-secondary max-w-md mb-4">
            {error}
          </p>
          <button
            onClick={() => openFeedbackForm({ feedbackType: 'Bug / Error', capability: 'Product Fitting', errorMessage: error })}
            className="text-sm text-gm-accent hover:text-gm-accent-hover transition-colors underline underline-offset-2"
          >
            Report this issue
          </button>
        </div>
      </div>
    )
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={`${panelClass} flex items-center justify-center min-h-[600px] overflow-hidden relative sticky top-24 self-start ${className}`}>
        {showVideo && <BackgroundVideo opacity="opacity-30" />}
        <div className="absolute inset-0 bg-gradient-to-t from-gm-bg-light/80 via-gm-bg-light/40 to-transparent dark:from-gm-bg/80 dark:via-gm-bg/40"></div>

        <div className="text-center px-8 relative z-10">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-gm-accent/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-gm-accent animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-gm-accent">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-2">
            Generating <span className="text-gm-accent">Product Fitting</span>
          </h2>
          <p className="text-sm text-gm-text-secondary-light dark:text-gm-text-secondary">
            Fitting garments onto model and evaluating results...
          </p>
        </div>
      </div>
    )
  }

  // Results state
  if (result && (result.front || result.back)) {
    const sides = [
      result.front ? { label: 'Front', ...result.front } : null,
      result.back ? { label: 'Back', ...result.back } : null,
    ].filter(Boolean) as Array<{ label: string; imageUrl: string; status: string; totalAttempts: number; validation: any }>

    return (
      <div className={`${panelClass} flex flex-col min-h-[600px] overflow-hidden relative sticky top-24 self-start ${className}`}>
        <div className="flex-1 p-4 overflow-y-auto">
          <div className={`grid ${sides.length === 2 ? 'grid-cols-2' : 'grid-cols-1 max-w-md mx-auto'} gap-3`}>
            {sides.map((side) => (
              <div key={side.label} className="relative rounded-lg overflow-hidden bg-black/5 dark:bg-black/20">
                <img
                  src={side.imageUrl}
                  alt={`${side.label} fitting result`}
                  className="w-full aspect-[3/4] object-cover"
                />
                <div className="absolute bottom-2 left-2 flex gap-1">
                  <span className="px-2 py-0.5 rounded-full bg-black/50 backdrop-blur-sm text-white text-[10px] font-medium">
                    {side.label}
                  </span>
                  {side.validation?.garments_score !== undefined && (
                    <span className="px-2 py-0.5 rounded-full bg-black/50 backdrop-blur-sm text-white text-[10px] font-medium">
                      {side.validation.garments_score}%
                    </span>
                  )}
                </div>
                {side.status === 'discarded' && (
                  <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-yellow-500/80 backdrop-blur-sm text-white text-[10px] font-medium">
                    Best effort
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Default / empty state
  return (
    <div className={`${panelClass} flex items-center justify-center min-h-[600px] overflow-hidden relative sticky top-24 self-start ${className}`}>
      {showVideo && <BackgroundVideo />}
      <div className="absolute inset-0 bg-gradient-to-t from-gm-bg-light/50 via-gm-bg-light/20 to-transparent dark:from-gm-bg/50 dark:via-gm-bg/20"></div>

      <div className="text-center px-8 relative z-10 max-w-lg animate-fade-in-up">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gm-accent/10 dark:bg-gm-accent/20 flex items-center justify-center glow-accent">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-gm-accent">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        <h2 className="text-[40px] lg:text-[48px] font-display font-bold mb-4 leading-tight tracking-tight">
          Product{' '}
          <span className="text-gm-accent" style={{ textShadow: '0 0 40px rgba(138, 180, 248, 0.4), 0 0 80px rgba(138, 180, 248, 0.2)' }}>
            Fitting
          </span>
        </h2>
        <p className="text-body-lg text-gm-text-secondary-light dark:text-gm-text-secondary leading-relaxed">
          Upload garment images to generate AI-powered product fitting on models.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-2 mt-6">
          <span className="px-3 py-1.5 rounded-full bg-black/[0.08] dark:bg-white/[0.12] text-caption text-gm-text-secondary-light dark:text-gm-text-secondary">
            Gemini
          </span>
          <span className="px-3 py-1.5 rounded-full bg-black/[0.08] dark:bg-white/[0.12] text-caption text-gm-text-secondary-light dark:text-gm-text-secondary">
            AI Fitting
          </span>
          <span className="px-3 py-1.5 rounded-full bg-black/[0.08] dark:bg-white/[0.12] text-caption text-gm-text-secondary-light dark:text-gm-text-secondary">
            Multi-View
          </span>
        </div>
      </div>
    </div>
  )
}

export default ProductFittingPreview
