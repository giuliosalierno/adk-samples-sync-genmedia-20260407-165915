import { useRef, useEffect } from 'react'

interface VideoPreviewProps {
  src?: string
  autoPlay?: boolean
  loop?: boolean
  muted?: boolean
  controls?: boolean
  className?: string
  overlayContent?: React.ReactNode
  onEnded?: () => void
}

function VideoPreview({
  src,
  autoPlay = true,
  loop = true,
  muted = true,
  controls = false,
  className = '',
  overlayContent,
  onEnded
}: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current && src) {
      videoRef.current.load()
    }
  }, [src])

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {src ? (
        <video
          ref={videoRef}
          autoPlay={autoPlay}
          loop={loop}
          muted={muted}
          controls={controls}
          playsInline
          className="w-full h-full object-cover"
          onEnded={onEnded}
        >
          <source src={src} type="video/mp4" />
        </video>
      ) : (
        <div className="w-full h-full bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center">
          <span className="text-gm-text-tertiary">No video</span>
        </div>
      )}

      {overlayContent && (
        <div className="absolute inset-0">
          {overlayContent}
        </div>
      )}
    </div>
  )
}

export default VideoPreview
