import { useEffect, useRef } from 'react';

interface Props {
  src: string | null;
  title?: string;
  onClose: () => void;
}

/**
 * Lightbox video player modal.
 * Opens on top of the page with a darkened backdrop.
 * Closes on backdrop click, Escape key, or the close button.
 */
export default function VideoPlayer({ src, title, onClose }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Trap focus & handle Escape
  useEffect(() => {
    if (!src) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [src, onClose]);

  if (!src) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title ? `Video: ${title}` : 'Video player'}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/90 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        ref={dialogRef}
        className="relative z-10 w-full max-w-4xl bg-gray-950 rounded-2xl overflow-hidden shadow-2xl ring-1 ring-gray-800"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
          <p className="text-sm text-gray-400 truncate">{title ?? 'Video'}</p>
          <button
            onClick={onClose}
            className="ml-4 shrink-0 text-gray-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-gray-800"
            aria-label="Close video"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Video */}
        <div className="relative bg-black aspect-video">
          <video
            key={src}
            src={src}
            controls
            autoPlay
            className="w-full h-full object-contain"
            playsInline
          >
            Your browser does not support the video element.
          </video>
        </div>

        {/* Footer */}
        <div className="px-5 py-2 text-xs text-gray-600 text-right">
          Press <kbd className="font-mono bg-gray-800 px-1 rounded">Esc</kbd> to close
        </div>
      </div>
    </div>
  );
}
