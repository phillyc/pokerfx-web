import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import HandGrid from '../components/HandGrid';
import VideoPlayer from '../components/VideoPlayer';
import ErrorState from '../components/ErrorState';
import { getVideo, exportVideo, type Video } from '../api/client';

export default function ReviewPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const [video, setVideo] = useState<Video | null>(null);
  const [verified, setVerified] = useState({ accepted: 0, rejected: 0, pending: 0 });
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_pollInterval, setPollInterval] = useState<number | null>(null);

  useEffect(() => {
    if (!videoId) return;
    setLoading(true);
    setError(null);
    getVideo(videoId)
      .then(setVideo)
      .catch(() => setError('Failed to load video. Please go back and try again.'))
      .finally(() => setLoading(false));
  }, [videoId]);

  // Poll while processing
  useEffect(() => {
    if (!videoId || video?.status === 'processing') {
      const interval = window.setInterval(async () => {
        try {
          const updated = await getVideo(videoId!);
          setVideo(updated);
          if (updated.status === 'done' || updated.status === 'error') {
            clearInterval(interval);
            setPollInterval(null);
          }
        } catch {
          // ignore poll errors
        }
      }, 3000);
      setPollInterval(interval);
      return () => clearInterval(interval);
    }
  }, [videoId, video?.status]);

  const handleVerifiedChange = useCallback((accepted: number, rejected: number, pending: number) => {
    setVerified({ accepted, rejected, pending });
  }, []);

  async function handleExport() {
    if (!videoId) return;
    setExporting(true);
    try {
      const blob = await exportVideo(videoId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${video?.filename ?? 'video'}_verified.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading video…</p>
        </div>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-4 px-6">
        <ErrorState
          title="Video not found"
          message={error ?? 'This video could not be loaded.'}
          onRetry={() => window.history.back()}
        />
        <Link to="/" className="text-purple-400 hover:underline text-sm">← Back to upload</Link>
      </div>
    );
  }

  const total = video.detectedCount;
  const allReviewed = verified.accepted + verified.rejected === total && total > 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Lightbox */}
      <VideoPlayer
        src={videoSrc}
        title={video.filename}
        onClose={() => setVideoSrc(null)}
      />

      {/* Header */}
      <header className="border-b border-gray-800 px-4 sm:px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="min-w-0">
            <Link to="/videos" className="text-purple-400 hover:underline text-sm mb-1 block">
              ← All videos
            </Link>
            <h1 className="text-base sm:text-xl font-bold truncate max-w-xs sm:max-w-none">
              {video.filename}
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {video.status === 'processing' && '⏳ Processing…'}
              {video.status === 'done' && `🎯 ${video.detectedCount} hand${video.detectedCount !== 1 ? 's' : ''} detected`}
              {video.status === 'error' && '❌ Processing failed'}
              {video.status === 'pending' && '⏳ Queued'}
            </p>
          </div>

          {video.status === 'done' && (
            <div className="flex flex-wrap items-center gap-4">
              {/* Stats */}
              <div className="flex gap-4 text-sm">
                <span className="text-green-400">✓ {verified.accepted}</span>
                <span className="text-red-400">✗ {verified.rejected}</span>
                {verified.pending > 0 && (
                  <span className="text-gray-500">{verified.pending} pending</span>
                )}
              </div>

              {/* Export */}
              <button
                onClick={handleExport}
                disabled={!allReviewed || exporting}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  allReviewed
                    ? 'bg-purple-600 hover:bg-purple-500 text-white'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                {exporting ? 'Exporting…' : 'Export Verified'}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Progress bar while processing */}
      {video.status === 'processing' && (
        <div className="h-1 bg-gray-800">
          <div className="h-full bg-purple-600 animate-pulse" style={{ width: '60%' }} />
        </div>
      )}

      {/* Hand grid */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {video.status === 'done' ? (
          <HandGrid videoId={videoId!} onVerifiedChange={handleVerifiedChange} />
        ) : (
          <div className="flex flex-col items-center justify-center py-24 text-gray-500">
            <div className="text-5xl mb-4">⏳</div>
            <p>Card detection is running…</p>
            <p className="text-sm mt-1 text-gray-600">This usually takes 30–60 seconds.</p>
          </div>
        )}
      </main>
    </div>
  );
}
