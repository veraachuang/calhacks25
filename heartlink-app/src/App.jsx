import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ProfilePage from './pages/ProfilePage';
import HeartLinkScene from './pages/HeartLinkScene';
import DebugConnection from './pages/DebugConnection';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ProfilePage />} />
        <Route path="/heartlink" element={<HeartLinkScene />} />
        <Route path="/debug" element={<DebugConnection />} />
      </Routes>
    </Router>
  );
}