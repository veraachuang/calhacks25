import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ProfilePage from "./pages/ProfilePage";
import HeartLinkScene from "./pages/HeartLinkScene";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ProfilePage />} />
        <Route path="/match" element={<HeartLinkScene />} />
      </Routes>
    </Router>
  );
}