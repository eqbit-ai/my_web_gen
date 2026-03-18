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
const ForgotPassword = lazy(() => import('./components/ForgotPassword'));
const ResetPassword = lazy(() => import('./components/ResetPassword'));
const ForceResetPassword = lazy(() => import('./components/ForceResetPassword'));
const PendingApproval = lazy(() => import('./components/PendingApproval'));

// Admin — Layout + Pages
const AdminLayout = lazy(() => import('./components/admin/AdminLayout'));
const OverviewPage = lazy(() => import('./components/admin/OverviewPage'));
const SitesListPage = lazy(() => import('./components/admin/SitesListPage'));
const SiteDetailPage = lazy(() => import('./components/admin/SiteDetailPage'));
const GenerationQueuePage = lazy(() => import('./components/admin/GenerationQueuePage'));
const FailedGenerationsPage = lazy(() => import('./components/admin/FailedGenerationsPage'));
const DomainsListPage = lazy(() => import('./components/admin/DomainsListPage'));
const DomainDetailPage = lazy(() => import('./components/admin/DomainDetailPage'));
const InternalDomainsPage = lazy(() => import('./components/admin/InternalDomainsPage'));
const InternalDomainDetailPage = lazy(() => import('./components/admin/InternalDomainDetailPage'));
const UsersListPage = lazy(() => import('./components/admin/UsersListPage'));
const UserDetailPage = lazy(() => import('./components/admin/UserDetailPage'));
const TokenLedgerPage = lazy(() => import('./components/admin/TokenLedgerPage'));
const TokenPoolPage = lazy(() => import('./components/admin/TokenPoolPage'));
const ExpiringTokensPage = lazy(() => import('./components/admin/ExpiringTokensPage'));
const TemplateManagerPage = lazy(() => import('./components/admin/TemplateManagerPage'));
const AuditLogPage = lazy(() => import('./components/admin/AuditLogPage'));
const AnnouncementsPage = lazy(() => import('./components/admin/AnnouncementsPage'));
const PromptManagerPage = lazy(() => import('./components/admin/PromptManagerPage'));
const SystemHealthPage = lazy(() => import('./components/admin/SystemHealthPage'));
const GrowthChartPage = lazy(() => import('./components/admin/GrowthChartPage'));
const GenerationStatsPage = lazy(() => import('./components/admin/GenerationStatsPage'));
const TokenTrendPage = lazy(() => import('./components/admin/TokenTrendPage'));

function ProtectedRoute({ children, allowForceReset, allowPending }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ minHeight: '100vh' }} />;
  if (!user) return <Navigate to="/login" replace />;
  if (!allowForceReset && localStorage.getItem('force_password_reset') === 'true') {
    return <Navigate to="/force-reset-password" replace />;
  }
  // Redirect unapproved users (except admins) to pending page
  if (!allowPending && user.is_approved === false && !user.is_admin) {
    return <Navigate to="/pending-approval" replace />;
  }
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
  const hideNavbar = location.pathname === '/generator' || location.pathname === '/dashboard' || location.pathname === '/force-reset-password' || location.pathname === '/pending-approval' || location.pathname.startsWith('/admin');

  return (
    <div className="app">
      {!hideNavbar && <Navbar />}
      <Suspense fallback={<div style={{ minHeight: '100vh' }} />}>
        <PageTransition>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/force-reset-password" element={<ProtectedRoute allowForceReset><ForceResetPassword /></ProtectedRoute>} />
          <Route path="/pending-approval" element={<ProtectedRoute allowPending><PendingApproval /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/generator" element={<ProtectedRoute><WebsiteGenerator /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
            <Route index element={<OverviewPage />} />
            <Route path="sites" element={<SitesListPage />} />
            <Route path="sites/:id" element={<SiteDetailPage />} />
            <Route path="generation-queue" element={<GenerationQueuePage />} />
            <Route path="failed-generations" element={<FailedGenerationsPage />} />
            <Route path="domains" element={<DomainsListPage />} />
            <Route path="domains/:id" element={<DomainDetailPage />} />
            <Route path="domains-internal" element={<InternalDomainsPage />} />
            <Route path="domains-internal/:id" element={<InternalDomainDetailPage />} />
            <Route path="users" element={<UsersListPage />} />
            <Route path="users/:id" element={<UserDetailPage />} />
            <Route path="token-ledger" element={<TokenLedgerPage />} />
            <Route path="token-pool" element={<TokenPoolPage />} />
            <Route path="expiring-tokens" element={<ExpiringTokensPage />} />
            <Route path="templates" element={<TemplateManagerPage />} />
            <Route path="audit-logs" element={<AuditLogPage />} />
            <Route path="announcements" element={<AnnouncementsPage />} />
            <Route path="prompts" element={<PromptManagerPage />} />
            <Route path="system" element={<SystemHealthPage />} />
            <Route path="growth" element={<GrowthChartPage />} />
            <Route path="generation-stats" element={<GenerationStatsPage />} />
            <Route path="token-trends" element={<TokenTrendPage />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Route>
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
