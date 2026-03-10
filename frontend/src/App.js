// src/App.js

import React, { useRef, useState, useLayoutEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { gsap } from 'gsap';
import Navbar from './components/Navbar';
import { AuthProvider, useAuth } from './context/AuthContext';
import './meydan-theme.css';
import './App.css';

// Lazy-load route components for code splitting
const LandingPage = lazy(() => import('./components/LandingPage'));
const Login = lazy(() => import('./components/Login'));
const Signup = lazy(() => import('./components/Signup'));
const WebsiteGenerator = lazy(() => import('./components/WebsiteGenerator'));
const Dashboard = lazy(() => import('./components/Dashboard'));

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ minHeight: '100vh' }} />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

// ============================================
// SMOOTH PAGE TRANSITION — simple crossfade
// ============================================
function PageTransition({ children }) {
  const wrapperRef = useRef(null);
  const location = useLocation();
  const prevPath = useRef(location.pathname);
  const [displayLocation, setDisplayLocation] = useState(location);

  useLayoutEffect(() => {
    if (location.pathname === prevPath.current) {
      setDisplayLocation(location);
      return;
    }
    prevPath.current = location.pathname;

    const el = wrapperRef.current;
    if (!el) {
      setDisplayLocation(location);
      return;
    }

    // Fade out current page
    gsap.to(el, {
      opacity: 0,
      duration: 0.25,
      ease: 'power2.inOut',
      onComplete: () => {
        setDisplayLocation(location);
        window.scrollTo(0, 0);

        // Fade in new page
        gsap.to(el, {
          opacity: 1,
          duration: 0.3,
          ease: 'power2.out',
        });
      }
    });
  }, [location]);

  return (
    <div ref={wrapperRef} style={{ opacity: 1 }}>
      <Routes location={displayLocation}>
        {children}
      </Routes>
    </div>
  );
}

function AppLayout() {
  const location = useLocation();
  const hideNavbar = location.pathname === '/generator' || location.pathname === '/dashboard';

  return (
    <div className="app">
      {!hideNavbar && <Navbar />}
      <Suspense fallback={<div style={{ minHeight: '100vh' }} />}>
        <PageTransition>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/generator" element={<ProtectedRoute><WebsiteGenerator /></ProtectedRoute>} />
        </PageTransition>
      </Suspense>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </Router>
  );
}

export default App;
