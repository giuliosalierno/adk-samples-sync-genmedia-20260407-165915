import { useEffect, useRef } from 'react'

// Global variable to preserve video playback position across all components
let globalVideoTime = 0

interface BackgroundVideoProps {
  className?: string
  opacity?: string
}

function BackgroundVideo({ className = '', opacity = '' }: BackgroundVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // Restore saved position
    if (globalVideoTime > 0) {
      video.currentTime = globalVideoTime
    }

    // Save position periodically
    const saveTime = () => {
      if (video && !video.paused) {
        globalVideoTime = video.currentTime
      }
    }

    const interval = setInterval(saveTime, 250)

    // Also save on time update for more accuracy
    video.addEventListener('timeupdate', saveTime)

    return () => {
      clearInterval(interval)
      video.removeEventListener('timeupdate', saveTime)
      // Save final position
      if (video) {
        globalVideoTime = video.currentTime
      }
    }
  }, [])

  return (
    <video
      ref={videoRef}
      autoPlay
      loop
      muted
      playsInline
      className={`absolute inset-0 w-full h-full object-cover animate-video-bg ${opacity} ${className}`}
    >
      <source src="/assets/loaders/background-loop.mov" type="video/mp4" />
    </video>
  )
}

export default BackgroundVideo
