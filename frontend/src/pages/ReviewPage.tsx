import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import HandGrid from '../components/HandGrid';
import { getVideo, exportVideo, type Video } from '../api/client';

export default function ReviewPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const [video, setVideo] = useState<Video | null>(null);
  const [verified, setVerified] = useState({ accepted: 0, rejected: 0, pending: 0 });
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_pollInterval, setPollInterval] = useState<number | null>(null);

  useEffect(() => {
    if (!videoId) return;
    getVideo(videoId)
      .then(setVideo)
      .catch(() => setVideo(null))
      .finally(() => setLoading(false));
  }, [videoId]);

  // Poll while processing
  useEffect(() => {
    if (!videoId || !video || video.status === 'processing') {
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
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  if (!video) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">Video not found.</p>
        <Link to="/" className="text-purple-400 hover:underline">← Back to upload</Link>
      </div>
    );
  }

  const total = video.detectedCount;
  const allReviewed = verified.accepted + verified.rejected === total && total > 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <Link to="/" className="text-purple-400 hover:underline text-sm mb-1 block">← Upload another</Link>
            <h1 className="text-xl font-bold">{video.filename}</h1>
            <p className="text-sm text-gray-500">
              {video.status === 'processing' && '⏳ Processing...'}
              {video.status === 'done' && `🎯 ${video.detectedCount} hand${video.detectedCount !== 1 ? 's' : ''} detected`}
              {video.status === 'error' && '❌ Processing failed'}
              {video.status === 'pending' && '⏳ Queued'}
            </p>
          </div>

          {video.status === 'done' && (
            <div className="flex items-center gap-6">
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
                {exporting ? 'Exporting...' : 'Export Verified'}
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
      <main className="max-w-6xl mx-auto px-6 py-8">
        {video.status === 'done' ? (
          <HandGrid videoId={videoId!} onVerifiedChange={handleVerifiedChange} />
        ) : (
          <div className="flex flex-col items-center justify-center py-24 text-gray-500">
            <div className="text-5xl mb-4">⏳</div>
            <p>Card detection is running...</p>
            <p className="text-sm mt-1">This usually takes 30–60 seconds.</p>
          </div>
        )}
      </main>
    </div>
  );
}
