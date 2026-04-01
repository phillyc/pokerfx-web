import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadVideo, processVideo } from '../api/client';

export default function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    if (!file.type.startsWith('video/')) {
      setError('Please upload a video file.');
      return;
    }
    if (file.size > 1024 * 1024 * 1024) {
      setError('File size must be under 1GB.');
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const { videoId } = await uploadVideo(file);
      await processVideo(videoId);
      navigate(`/review/${videoId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">PokerFX</h1>
          <p className="text-gray-400">Card Detection Verification</p>
        </div>

        {/* Upload zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => !uploading && inputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${
            dragOver
              ? 'border-purple-500 bg-purple-500/10'
              : 'border-gray-700 hover:border-gray-500 bg-gray-900'
          } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />

          {uploading ? (
            <>
              <div className="text-4xl mb-4 animate-pulse">📤</div>
              <p className="text-gray-300">Uploading...</p>
            </>
          ) : (
            <>
              <div className="text-5xl mb-4">🎥</div>
              <p className="text-lg font-medium mb-1">Drop your video here</p>
              <p className="text-sm text-gray-500">
                or click to browse · MP4, MOV, WebM · max 1GB
              </p>
            </>
          )}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-500/20 border border-red-500/40 rounded-lg text-red-300 text-sm text-center">
            {error}
          </div>
        )}

        <p className="text-center text-gray-600 text-xs mt-8">
          1 hand per video clip · Auto-detects card reveals
        </p>
      </div>
    </div>
  );
}
