interface Props {
  message?: string;
  onRetry?: () => void;
  title?: string;
}

/**
 * Full-page or inline error state component.
 */
export default function ErrorState({
  message = 'Something went wrong.',
  onRetry,
  title = 'Error',
}: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <span className="text-4xl mb-4" aria-hidden="true">
        ⚠️
      </span>
      <h2 className="text-lg font-semibold text-gray-200 mb-1">{title}</h2>
      <p className="text-sm text-gray-500 mb-4 max-w-xs">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors text-gray-300 border border-gray-700"
        >
          Try again
        </button>
      )}
    </div>
  );
}
