import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ProfilePage from './pages/ProfilePage';
import HeartLinkScene from './pages/HeartLinkScene';
import DebugConnection from './pages/DebugConnection';
import DebugWebRTC from './pages/DebugWebRTC';

export default function App() {
  return (
    <Router basename="/calhacks25">
      <Routes>
        <Route path="/" element={<ProfilePage />} />
        <Route path="/heartlink" element={<HeartLinkScene />} />
        <Route path="/debug" element={<DebugConnection />} />
        <Route path="/debug-webrtc" element={<DebugWebRTC />} />
      </Routes>
    </Router>
  );
}