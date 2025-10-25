// src/components/ProgressBar.jsx
import React from "react";
import "../index.css"; // Ensure you have the .progress-wrapper styles

export default function ProgressBar() {
  return (
    <div className="progress-wrapper">
      <div className="progress-section red" />
      <div className="progress-section yellow" />
      <div className="progress-section green" />
    </div>
  );
}