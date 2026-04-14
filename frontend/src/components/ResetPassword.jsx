import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../services/api';

const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    // Capture the token into state ONCE, then scrub it from the URL so it
    // doesn't sit in browser history, Referer headers (if any 3rd-party is
    // ever added to this page), or casual screenshots.
    const tokenRef = useRef(searchParams.get('token') || '');
    const token = tokenRef.current;
    useEffect(() => {
        if (window.location.search.includes('token=')) {
            window.history.replaceState(null, '', '/reset-password');
        }
    }, []);
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
        if (password !== confirm) { setError('Passwords do not match'); return; }
        if (!token) { setError('Invalid reset link — no token found'); return; }

        setIsLoading(true);
        try {
            await resetPassword(token, password);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 3000);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-bg"><div className="auth-gradient" /></div>
            <div className="auth-container">
                <div className="auth-card">
                    <div className="auth-header">
                        <Link to="/" className="auth-logo">
                            <img src="/mfz-logo.webp" alt="Web AI" style={{ height: 56, maxWidth: 180, objectFit: 'contain', display: 'block' }} />
                        </Link>
                        <h1>Set New Password</h1>
                        <p>Choose a strong password for your account</p>
                    </div>

                    {success ? (
                        <div className="auth-form">
                            <div className="auth-success">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                                Password reset successfully! Redirecting to login...
                            </div>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="auth-form">
                            {error && (
                                <div className="auth-error">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                                    {error}
                                </div>
                            )}
                            <div className="form-group">
                                <label htmlFor="password">New Password</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                    </svg>
                                    <input id="password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" required />
                                    <button type="button" className="toggle-password" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
                                        {showPassword ? (
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                                        ) : (
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div className="form-group">
                                <label htmlFor="confirm">Confirm Password</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                    </svg>
                                    <input id="confirm" type={showPassword ? 'text' : 'password'} value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Re-enter password" required />
                                </div>
                            </div>
                            <button type="submit" className="btn-primary full" disabled={isLoading}>
                                {isLoading ? <span className="spinner" /> : 'Reset Password'}
                            </button>
                        </form>
                    )}

                    <div className="auth-footer">
                        <p>Remember your password? <Link to="/login">Sign In</Link></p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResetPassword;
