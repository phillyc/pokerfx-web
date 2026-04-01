import { useEffect, useState } from 'react';
import HandCard from './HandCard';
import ErrorState from './ErrorState';
import { SkeletonHandGrid } from './Skeleton';
import { getHands, updateHandStatus, type DetectedHand } from '../api/client';

interface Props {
  videoId: string;
  onVerifiedChange: (accepted: number, rejected: number, pending: number) => void;
}

export default function HandGrid({ videoId, onVerifiedChange }: Props) {
  const [hands, setHands] = useState<DetectedHand[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getHands(videoId);
        if (!cancelled) {
          setHands(data);
          setError(null);
        }
      } catch {
        if (!cancelled) setError('Failed to load detected hands. Please refresh.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [videoId]);

  useEffect(() => {
    const accepted = hands.filter((h) => h.status === 'accepted').length;
    const rejected = hands.filter((h) => h.status === 'rejected').length;
    const pending = hands.filter((h) => h.status === 'pending').length;
    onVerifiedChange(accepted, rejected, pending);
  }, [hands, onVerifiedChange]);

  async function handleStatusChange(id: string, status: 'accepted' | 'rejected') {
    // Optimistic update
    setHands((prev) =>
      prev.map((h) => (h.id === id ? { ...h, status } : h))
    );
    try {
      await updateHandStatus(id, status);
    } catch {
      // Revert on failure
      setHands((prev) =>
        prev.map((h) => (h.id === id ? { ...h, status: 'pending' } : h))
      );
    }
  }

  if (loading) return <SkeletonHandGrid count={hands.length || 8} />;

  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  if (hands.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-gray-400">
        <span className="text-4xl mb-2" aria-hidden="true">🃏</span>
        <p>No hands detected in this video yet.</p>
        <p className="text-sm mt-1 text-gray-600">Check back after processing completes.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {hands.map((hand) => (
        <HandCard
          key={hand.id}
          hand={hand}
          onStatusChange={handleStatusChange}
        />
      ))}
    </div>
  );
}
