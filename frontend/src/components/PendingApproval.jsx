import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PendingApproval = () => {
    const { user, logout, refreshUser } = useAuth();
    const [checking, setChecking] = React.useState(false);

    const handleCheckStatus = async () => {
        setChecking(true);
        await refreshUser();
        setChecking(false);
    };

    // If user is now approved, redirect
    if (user && user.is_approved) {
        window.location.href = '/dashboard';
        return null;
    }

    return (
        <div className="auth-page">
            <div className="auth-bg"><div className="auth-gradient" /></div>
            <div className="auth-container">
                <div className="auth-card" style={{ textAlign: 'center', padding: '48px 40px' }}>
                    <div className="auth-header">
                        <Link to="/" className="auth-logo">
                            <img src="/mfz-logo.webp" alt="Meydan Free Zone" style={{ height: 40, background: 'rgba(40, 75, 130, 0.85)', borderRadius: 10, padding: '6px 12px', display: 'block', margin: '0 auto' }} />
                        </Link>
                    </div>

                    <div style={{ margin: '32px 0 16px' }}>
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto' }}>
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 8v4"/>
                            <path d="M12 16h.01"/>
                        </svg>
                    </div>

                    <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 8 }}>Account Pending Approval</h1>
                    <p style={{ color: '#71717a', fontSize: 15, lineHeight: 1.6, maxWidth: 380, margin: '0 auto 24px' }}>
                        Your account has been created successfully. An administrator needs to approve your account before you can start using the platform.
                    </p>

                    {user && (
                        <div style={{
                            background: 'rgba(245,158,11,0.08)',
                            border: '1px solid rgba(245,158,11,0.2)',
                            borderRadius: 12,
                            padding: '16px 20px',
                            marginBottom: 24,
                            textAlign: 'left',
                            fontSize: 14,
                        }}>
                            <div style={{ marginBottom: 8 }}><strong>Name:</strong> {user.full_name}</div>
                            <div style={{ marginBottom: 8 }}><strong>Email:</strong> {user.email}</div>
                            {user.company_name && <div><strong>Company:</strong> {user.company_name}</div>}
                        </div>
                    )}

                    <button
                        onClick={handleCheckStatus}
                        className="btn-primary full"
                        disabled={checking}
                        style={{ marginBottom: 12 }}
                    >
                        {checking ? <span className="spinner" /> : 'Check Approval Status'}
                    </button>

                    <button
                        onClick={logout}
                        className="btn-secondary full"
                        style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.15)', color: '#a1a1aa' }}
                    >
                        Sign Out
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PendingApproval;
