import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import WebcamDashboard from './WebcamDashboard';
import RoiDashboard from './RoiDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.nav}>
        <NavLink 
          to="/" 
          end
          style={({ isActive }) => isActive ? { ...styles.link, ...styles.activeLink } : styles.link}
        >
          Webcam Stream
        </NavLink>
        <NavLink 
          to="/roi" 
          style={({ isActive }) => isActive ? { ...styles.link, ...styles.activeLink } : styles.link}
        >
          ROI History
        </NavLink>
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
    color: '#bdc3c7',
    textDecoration: 'none',
    fontWeight: 'bold',
    fontSize: '16px',
    padding: '8px 16px',
    borderRadius: '4px',
    transition: 'all 0.2s ease-in-out',
  },
  activeLink: {
    color: '#fff',
    backgroundColor: '#34495e',
  }
};