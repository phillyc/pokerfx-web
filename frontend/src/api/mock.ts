/**
 * Mock API layer for pokerfx-web frontend.
 * Intercepts fetch calls to /api/* and returns realistic mock data.
 * Enable via VITE_USE_MOCK=true env variable.
 */

import type { Video, DetectedHand } from './client';

const MOCK_DELAY = 600;

// Seed data
const MOCK_VIDEOS: Video[] = [
  {
    id: 'vid-001',
    filename: 'table_cam_session_01.mp4',
    status: 'done',
    clipCount: 3,
    detectedCount: 3,
    verifiedCount: 1,
    createdAt: new Date(Date.now() - 3600_000).toISOString(),
  },
  {
    id: 'vid-002',
    filename: 'mixed_game_nlhe_02.mp4',
    status: 'done',
    clipCount: 5,
    detectedCount: 5,
    verifiedCount: 0,
    createdAt: new Date(Date.now() - 7200_000).toISOString(),
  },
  {
    id: 'vid-003',
    filename: 'live_stream_highlights.mp4',
    status: 'processing',
    clipCount: 0,
    detectedCount: 0,
    verifiedCount: 0,
    createdAt: new Date(Date.now() - 1800_000).toISOString(),
  },
  {
    id: 'vid-004',
    filename: 'bad_beats_compilation.mp4',
    status: 'pending',
    clipCount: 0,
    detectedCount: 0,
    verifiedCount: 0,
    createdAt: new Date(Date.now() - 600_000).toISOString(),
  },
  {
    id: 'vid-005',
    filename: 'final_table_final_hand.mp4',
    status: 'done',
    clipCount: 7,
    detectedCount: 7,
    verifiedCount: 7,
    createdAt: new Date(Date.now() - 86400_000).toISOString(),
  },
];

const MOCK_HANDS: Record<string, DetectedHand[]> = {
  'vid-001': [
    {
      id: 'hand-001',
      videoId: 'vid-001',
      clipNumber: 1,
      cards: 'AKs',
      confidence: 'high',
      status: 'accepted',
      frameThumbnailUrl: null,
      detectedAt: new Date(Date.now() - 3500_000).toISOString(),
    },
    {
      id: 'hand-002',
      videoId: 'vid-001',
      clipNumber: 2,
      cards: 'QQ',
      confidence: 'high',
      status: 'pending',
      frameThumbnailUrl: null,
      detectedAt: new Date(Date.now() - 3400_000).toISOString(),
    },
    {
      id: 'hand-003',
      videoId: 'vid-001',
      clipNumber: 3,
      cards: '??',
      confidence: 'low',
      status: 'pending',
      frameThumbnailUrl: null,
      detectedAt: new Date(Date.now() - 3300_000).toISOString(),
    },
  ],
  'vid-002': Array.from({ length: 5 }, (_, i) => ({
    id: `hand-${200 + i}`,
    videoId: 'vid-002',
    clipNumber: i + 1,
    cards: ['AA', 'KK', 'AKo', 'JJ', 'TT'][i] ?? '??',
    confidence: (['high', 'high', 'medium', 'high', 'low'] as const)[i],
    status: 'pending' as const,
    frameThumbnailUrl: null,
    detectedAt: new Date(Date.now() - 7000_000 - i * 100_000).toISOString(),
  })),
  'vid-005': [
    {
      id: 'hand-501',
      videoId: 'vid-005',
      clipNumber: 1,
      cards: 'AA',
      confidence: 'high',
      status: 'accepted',
      frameThumbnailUrl: null,
      detectedAt: new Date(Date.now() - 86000_000).toISOString(),
    },
    {
      id: 'hand-502',
      videoId: 'vid-005',
      clipNumber: 2,
      cards: 'KK',
      confidence: 'high',
      status: 'accepted',
      frameThumbnailUrl: null,
      detectedAt: new Date(Date.now() - 85900_000).toISOString(),
    },
  ],
};

// Mutable state for mock persistence
const videoState: Video[] = JSON.parse(JSON.stringify(MOCK_VIDEOS));
const handState: Record<string, DetectedHand[]> = JSON.parse(JSON.stringify(MOCK_HANDS));

function delay(ms = MOCK_DELAY) {
  return new Promise((r) => setTimeout(r, ms));
}

function isMockEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK === 'true';
}

function mockFetch<T>(url: string, fallback: () => T, delayMs?: number): Promise<T> {
  if (!isMockEnabled()) throw new Error(`Non-mock fetch to ${url}`);
  return delay(delayMs).then(fallback);
}

export async function mockListVideos(): Promise<Video[]> {
  return mockFetch('/api/videos', () => [...videoState]);
}

export async function mockUploadVideo(file: File): Promise<{ videoId: string }> {
  return mockFetch('/api/videos/upload', () => {
    const id = `vid-${Date.now()}`;
    videoState.unshift({
      id,
      filename: file?.name ?? `upload_${Date.now()}.mp4`,
      status: 'pending',
      clipCount: 0,
      detectedCount: 0,
      verifiedCount: 0,
      createdAt: new Date().toISOString(),
    });
    return { videoId: id };
  }, 1200);
}

export async function mockGetVideo(id: string): Promise<Video> {
  return mockFetch(`/api/videos/${id}`, () => {
    const v = videoState.find((v) => v.id === id);
    if (!v) throw new Error('Video not found');
    return { ...v };
  });
}

export async function mockProcessVideo(id: string): Promise<void> {
  return mockFetch(`/api/videos/${id}/process`, () => {
    const v = videoState.find((v) => v.id === id);
    if (v) v.status = 'processing';
  }, 300);
}

export async function mockGetHands(videoId: string): Promise<DetectedHand[]> {
  return mockFetch(`/api/hands/${videoId}`, () => {
    return handState[videoId] ? [...handState[videoId]] : [];
  });
}

export async function mockUpdateHandStatus(
  id: string,
  status: 'accepted' | 'rejected'
): Promise<void> {
  return mockFetch(`/api/hands/${id}`, () => {
    for (const hands of Object.values(handState)) {
      const hand = hands.find((h) => h.id === id);
      if (hand) {
        hand.status = status;
        break;
      }
    }
  }, 200);
}

export async function mockExportVideo(_id: string): Promise<Blob> {
  void _id; // unused in mock

  return mockFetch('/api/videos/:id/export', () => {
    // Return a small empty zip-like blob
    return new Blob(['PK\x03\x04'], { type: 'application/zip' });
  }, 800);
}
