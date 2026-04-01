import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listVideos, type Video } from '../api/client';
import { mockListVideos } from '../api/mock';
import { SkeletonVideoRow } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';

const STATUS_LABELS: Record<Video['status'], { label: string; color: string }> = {
  pending: { label: 'Queued', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' },
  processing: { label: 'Processing', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  done: { label: 'Done', color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  error: { label: 'Failed', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVideos = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await (import.meta.env.VITE_USE_MOCK === 'true'
          ? mockListVideos()
          : listVideos());
        setVideos(data);
      } catch {
        setError('Failed to load videos. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchVideos();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <Link to="/" className="text-purple-400 hover:underline text-sm mb-1 block">
              ← Upload
            </Link>
            <h1 className="text-xl font-bold">My Videos</h1>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
          >
            + Upload
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }, (_, i) => (
              <SkeletonVideoRow key={i} />
            ))}
          </div>
        )}

        {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}

        {!loading && !error && videos.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-gray-500">
            <span className="text-5xl mb-4">📁</span>
            <p className="text-lg font-medium text-gray-300 mb-1">No videos yet</p>
            <p className="text-sm">Upload your first poker video to get started.</p>
            <Link
              to="/"
              className="mt-6 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm font-medium transition-colors"
            >
              Upload a video
            </Link>
          </div>
        )}

        {!loading && !error && videos.length > 0 && (
          <div className="space-y-3">
            {videos.map((video) => {
              const { label, color } = STATUS_LABELS[video.status];
              return (
                <Link
                  key={video.id}
                  to={`/review/${video.id}`}
                  className="flex items-center gap-4 p-4 bg-gray-900 hover:bg-gray-800 rounded-xl border border-gray-800 hover:border-gray-700 transition-all group"
                >
                  {/* Icon */}
                  <div className="w-16 h-12 bg-gray-800 rounded-lg flex items-center justify-center shrink-0 text-gray-600 group-hover:text-purple-400 transition-colors">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="w-6 h-6"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">{video.filename}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {video.status === 'done' && `${video.detectedCount} hand${video.detectedCount !== 1 ? 's' : ''} detected`}
                      {video.status === 'processing' && 'Detecting cards…'}
                      {video.status === 'pending' && 'Queued for processing'}
                      {video.status === 'error' && 'Processing failed'}
                      {' · '}
                      {timeAgo(video.createdAt)}
                    </p>
                  </div>

                  {/* Status badge */}
                  <span
                    className={`shrink-0 text-xs px-2.5 py-1 rounded-full border font-medium ${color}`}
                  >
                    {label}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
