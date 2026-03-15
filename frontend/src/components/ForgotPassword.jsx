import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../services/api';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [resetUrl, setResetUrl] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        try {
            const data = await forgotPassword(email);
            setSuccess(true);
            if (data.reset_url) setResetUrl(data.reset_url);
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
                            <img src="/mfz-logo.webp" alt="Meydan Free Zone" style={{ height: 40, background: 'rgba(40, 75, 130, 0.85)', borderRadius: 10, padding: '6px 12px', display: 'block' }} />
                        </Link>
                        <h1>Reset Password</h1>
                        <p>Enter your email and we'll send you a reset link</p>
                    </div>

                    {success ? (
                        <div className="auth-form">
                            <div className="auth-success">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                                If an account with that email exists, a reset link has been generated.
                            </div>
                            {resetUrl && (
                                <div style={{ marginTop: 16, padding: 12, background: 'rgba(0,0,0,0.03)', borderRadius: 8, fontSize: 13 }}>
                                    <strong>Dev mode:</strong> <Link to={resetUrl}>Click here to reset</Link>
                                </div>
                            )}
                            <div style={{ marginTop: 20, textAlign: 'center' }}>
                                <Link to="/login" className="forgot-link">Back to Sign In</Link>
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
                                <label htmlFor="email">Email Address</label>
                                <div className="input-wrapper">
                                    <svg className="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                                    </svg>
                                    <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
                                </div>
                            </div>
                            <button type="submit" className="btn-primary full" disabled={isLoading}>
                                {isLoading ? <span className="spinner" /> : 'Send Reset Link'}
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

export default ForgotPassword;
