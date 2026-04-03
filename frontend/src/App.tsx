import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';

// Lazy-load pages for code-splitting
const UploadPage = lazy(() => import('./pages/UploadPage'));
const ReviewPage = lazy(() => import('./pages/ReviewPage'));
const VideosPage = lazy(() => import('./pages/VideosPage'));

const PageLoader = () => (
  <div className="min-h-screen bg-background flex items-center justify-center">
    <p className="font-label tracking-widest uppercase text-sm text-on-surface-variant">Loading...</p>
  </div>
);

function Layout() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<UploadPage />} />
            <Route path="/videos" element={<VideosPage />} />
            <Route path="/review/:videoId" element={<ReviewPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
