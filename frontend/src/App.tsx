import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import WebcamDashboard from './WebcamDashboard';
import RoiDashboard from './RoiDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.nav}>
        <Link to="/" style={styles.link}>Webcam Stream</Link>
        <Link to="/roi" style={styles.link}>ROI History</Link>
      </div>
      <Routes>
        <Route path="/" element={<WebcamDashboard />} />
        <Route path="/roi" element={<RoiDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

const styles: Record<string, React.CSSProperties> = {
  nav: {
    padding: '16px',
    background: '#2c3e50',
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
  },
  link: {
    color: '#fff',
    textDecoration: 'none',
    fontWeight: 'bold',
    fontSize: '16px',
  }
};