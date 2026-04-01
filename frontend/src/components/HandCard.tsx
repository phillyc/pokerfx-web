import { useState } from 'react';
import type { DetectedHand } from '../api/client';

interface Props {
  hand: DetectedHand;
  onStatusChange: (id: string, status: 'accepted' | 'rejected') => void;
}

const CONFIDENCE_COLORS = {
  high: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-orange-100 text-orange-800 border-orange-200',
  none: 'bg-red-100 text-red-800 border-red-200',
};

const CARD_DISPLAY = {
  pending: 'opacity-50',
  accepted: 'ring-2 ring-green-500',
  rejected: 'ring-2 ring-red-500 grayscale',
};

export default function HandCard({ hand, onStatusChange }: Props) {
  const [imgError, setImgError] = useState(false);

  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden transition-all ${CARD_DISPLAY[hand.status]}`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100">
        {hand.frameThumbnailUrl && !imgError ? (
          <img
            src={hand.frameThumbnailUrl}
            alt={`Clip ${hand.clipNumber} — ${hand.cards}`}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
            No thumbnail
          </div>
        )}

        {/* Clip number badge */}
        <span className="absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded">
          #{hand.clipNumber}
        </span>

        {/* Confidence badge */}
        <span
          className={`absolute top-2 right-2 text-xs px-2 py-0.5 rounded border ${CONFIDENCE_COLORS[hand.confidence]}`}
        >
          {hand.confidence}
        </span>
      </div>

      {/* Card display */}
      <div className="p-4">
        <div className="text-center mb-3">
          <span className="text-2xl font-mono font-bold tracking-wider">
            {hand.cards === '??' || hand.cards === 'XX' ? (
              <span className="text-gray-400">?</span>
            ) : (
              hand.cards
            )}
          </span>
        </div>

        {/* Accept / Reject */}
        <div className="flex gap-2">
          <button
            onClick={() => onStatusChange(hand.id, 'accepted')}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
              hand.status === 'accepted'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-700'
            }`}
          >
            ✓ Accept
          </button>
          <button
            onClick={() => onStatusChange(hand.id, 'rejected')}
            className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
              hand.status === 'rejected'
                ? 'bg-red-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-700'
            }`}
          >
            ✗ Reject
          </button>
        </div>
      </div>
    </div>
  );
}
