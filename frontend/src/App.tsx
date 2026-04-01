import { BrowserRouter, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ReviewPage from './pages/ReviewPage';
import VideosPage from './pages/VideosPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/videos" element={<VideosPage />} />
        <Route path="/review/:videoId" element={<ReviewPage />} />
      </Routes>
    </BrowserRouter>
  );
}
