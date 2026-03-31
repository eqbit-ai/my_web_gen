// src/App.js

import React, { Component, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import { AuthProvider, useAuth } from './context/AuthContext';
import './meydan-theme.css';
import './App.css';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info?.componentStack);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#f8f9fa', fontFamily: 'system-ui, sans-serif', padding: 20,
        }}>
          <div style={{
            textAlign: 'center', maxWidth: 420, background: '#fff', padding: '3rem 2rem',
            borderRadius: 16, boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
          }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>⚠</div>
            <h2 style={{ margin: '0 0 8px', color: '#111827', fontSize: 20 }}>Something went wrong</h2>
            <p style={{ color: '#6b7280', fontSize: 15, lineHeight: 1.6, margin: '0 0 20px' }}>
              The page encountered an error. This is usually fixed by refreshing.
            </p>
            <button
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
              style={{
                background: '#4f46e5', color: '#fff', border: 'none', padding: '10px 24px',
                borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer',
              }}
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Retry wrapper for lazy imports — handles chunk load failures gracefully
function lazyRetry(importFn) {
  return lazy(() =>
    importFn().catch((err) => {
      // If chunk failed, try a full page reload once (clears any stale service worker / cache)
      const hasReloaded = sessionStorage.getItem('chunk_reload');
      if (!hasReloaded) {
        sessionStorage.setItem('chunk_reload', '1');
        window.location.reload();
        return new Promise(() => {}); // never resolves — page will reload
      }
      sessionStorage.removeItem('chunk_reload');
      throw err; // let ErrorBoundary catch it
    })
  );
}

// Lazy-load route components with retry
const LandingPage = lazyRetry(() => import('./components/LandingPage'));
const Login = lazyRetry(() => import('./components/Login'));
const Signup = lazyRetry(() => import('./components/Signup'));
const WebsiteGenerator = lazyRetry(() => import('./components/WebsiteGenerator'));
const Dashboard = lazyRetry(() => import('./components/Dashboard'));
const ForgotPassword = lazyRetry(() => import('./components/ForgotPassword'));
const ResetPassword = lazyRetry(() => import('./components/ResetPassword'));
const ForceResetPassword = lazyRetry(() => import('./components/ForceResetPassword'));
const PendingApproval = lazyRetry(() => import('./components/PendingApproval'));

// Admin — Layout + Pages
const AdminLayout = lazyRetry(() => import('./components/admin/AdminLayout'));
const OverviewPage = lazyRetry(() => import('./components/admin/OverviewPage'));
const SitesListPage = lazyRetry(() => import('./components/admin/SitesListPage'));
const SiteDetailPage = lazyRetry(() => import('./components/admin/SiteDetailPage'));
const GenerationQueuePage = lazyRetry(() => import('./components/admin/GenerationQueuePage'));
const FailedGenerationsPage = lazyRetry(() => import('./components/admin/FailedGenerationsPage'));
const DomainsListPage = lazyRetry(() => import('./components/admin/DomainsListPage'));
const DomainDetailPage = lazyRetry(() => import('./components/admin/DomainDetailPage'));
const InternalDomainsPage = lazyRetry(() => import('./components/admin/InternalDomainsPage'));
const InternalDomainDetailPage = lazyRetry(() => import('./components/admin/InternalDomainDetailPage'));
const UsersListPage = lazyRetry(() => import('./components/admin/UsersListPage'));
const UserDetailPage = lazyRetry(() => import('./components/admin/UserDetailPage'));
const TokenLedgerPage = lazyRetry(() => import('./components/admin/TokenLedgerPage'));
const TokenPoolPage = lazyRetry(() => import('./components/admin/TokenPoolPage'));
const ExpiringTokensPage = lazyRetry(() => import('./components/admin/ExpiringTokensPage'));
const TemplateManagerPage = lazyRetry(() => import('./components/admin/TemplateManagerPage'));
const AuditLogPage = lazyRetry(() => import('./components/admin/AuditLogPage'));
const AnnouncementsPage = lazyRetry(() => import('./components/admin/AnnouncementsPage'));
const PromptManagerPage = lazyRetry(() => import('./components/admin/PromptManagerPage'));
const SystemHealthPage = lazyRetry(() => import('./components/admin/SystemHealthPage'));
const GrowthChartPage = lazyRetry(() => import('./components/admin/GrowthChartPage'));
const GenerationStatsPage = lazyRetry(() => import('./components/admin/GenerationStatsPage'));
const TokenTrendPage = lazyRetry(() => import('./components/admin/TokenTrendPage'));
const PendingApprovalsPage = lazyRetry(() => import('./components/admin/PendingApprovalsPage'));
const TokenRequestsPage = lazyRetry(() => import('./components/admin/TokenRequestsPage'));

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
// PAGE WRAPPER — instant navigation, no transition
// ============================================
function PageWrapper({ children }) {
  const location = useLocation();

  return (
    <Routes location={location}>
      {children}
    </Routes>
  );
}

function AppLayout() {
  const location = useLocation();
  const hideNavbar = location.pathname === '/generator' || location.pathname === '/dashboard' || location.pathname === '/force-reset-password' || location.pathname === '/pending-approval' || location.pathname.startsWith('/admin');

  return (
    <div className="app">
      {!hideNavbar && <Navbar />}
      <Suspense fallback={
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa' }}>
          <div style={{ width: 36, height: 36, border: '3px solid #e5e7eb', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        </div>
      }>
        <PageWrapper>
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
            <Route path="pending-approvals" element={<PendingApprovalsPage />} />
            <Route path="token-requests" element={<TokenRequestsPage />} />
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
        </PageWrapper>
      </Suspense>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <AppLayout />
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
