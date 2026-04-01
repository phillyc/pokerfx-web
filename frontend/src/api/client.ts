import {
  mockListVideos,
  mockUploadVideo,
  mockGetVideo,
  mockGetHands,
  mockUpdateHandStatus,
  mockProcessVideo,
  mockExportVideo,
} from './mock';

const API_BASE = import.meta.env.VITE_API_URL || '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export interface Video {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'done' | 'error';
  clipCount: number;
  detectedCount: number;
  verifiedCount: number;
  createdAt: string;
}

export interface DetectedHand {
  id: string;
  videoId: string;
  clipNumber: number;
  cards: string;
  confidence: 'high' | 'medium' | 'low' | 'none';
  status: 'pending' | 'accepted' | 'rejected';
  frameThumbnailUrl: string | null;
  detectedAt: string;
}

export async function listVideos(): Promise<Video[]> {
  if (USE_MOCK) return mockListVideos();
  const res = await fetch(`${API_BASE}/videos`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  return res.json();
}

export async function uploadVideo(file: File): Promise<{ videoId: string }> {
  if (USE_MOCK) return mockUploadVideo(file);
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/videos/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function getVideo(id: string): Promise<Video> {
  if (USE_MOCK) return mockGetVideo(id);
  const res = await fetch(`${API_BASE}/videos/${id}`);
  if (!res.ok) throw new Error('Failed to fetch video');
  return res.json();
}

export async function getHands(videoId: string): Promise<DetectedHand[]> {
  if (USE_MOCK) return mockGetHands(videoId);
  const res = await fetch(`${API_BASE}/hands/${videoId}`);
  if (!res.ok) throw new Error('Failed to fetch hands');
  return res.json();
}

export async function updateHandStatus(
  id: string,
  status: 'accepted' | 'rejected'
): Promise<void> {
  if (USE_MOCK) return mockUpdateHandStatus(id, status);
  const res = await fetch(`${API_BASE}/hands/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error('Failed to update hand');
}

export async function processVideo(id: string): Promise<void> {
  if (USE_MOCK) return mockProcessVideo(id);
  const res = await fetch(`${API_BASE}/videos/${id}/process`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to queue processing');
}

export async function exportVideo(id: string): Promise<Blob> {
  if (USE_MOCK) return mockExportVideo(id);
  const res = await fetch(`${API_BASE}/videos/${id}/export`);
  if (!res.ok) throw new Error('Export failed');
  return res.blob();
}
