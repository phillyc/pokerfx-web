interface SkeletonProps {
  className?: string;
}

/**
 * Base skeleton primitive — animated shimmer block.
 */
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`bg-gray-800 rounded animate-pulse ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * Skeleton card matching HandCard dimensions.
 */
export function SkeletonHandCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Thumbnail */}
      <Skeleton className="aspect-video w-full" />
      {/* Card display */}
      <div className="p-4">
        <Skeleton className="h-8 w-24 mx-auto mb-3 rounded" />
        <div className="flex gap-2">
          <Skeleton className="flex-1 h-9 rounded-lg" />
          <Skeleton className="flex-1 h-9 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton row for video list items.
 */
export function SkeletonVideoRow() {
  return (
    <div className="flex items-center gap-4 p-4 bg-gray-900 rounded-xl border border-gray-800">
      {/* Thumbnail */}
      <Skeleton className="w-24 h-16 rounded-lg shrink-0" />
      {/* Info */}
      <div className="flex-1 min-w-0">
        <Skeleton className="h-4 w-48 mb-2 rounded" />
        <Skeleton className="h-3 w-32 rounded" />
      </div>
      {/* Status badge */}
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  );
}

/**
 * Skeleton grid for HandGrid placeholder.
 */
export function SkeletonHandGrid({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonHandCard key={i} />
      ))}
    </div>
  );
}
