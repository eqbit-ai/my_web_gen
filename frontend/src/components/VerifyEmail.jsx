import React, { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { verifyEmail, resendVerification } from '../services/api';

const VerifyEmail = () => {
    const [params] = useSearchParams();
    const token = params.get('token');
    const [state, setState] = useState({ status: 'pending', message: '' });
    const [resendEmail, setResendEmail] = useState('');
    const [resendState, setResendState] = useState({ loading: false, message: '' });
    const ranRef = useRef(false);

    useEffect(() => {
        if (ranRef.current) return;
        ranRef.current = true;

        if (!token) {
            setState({ status: 'error', message: 'Missing verification token. Please use the link from your email.' });
            return;
        }
        verifyEmail(token)
            .then(res => setState({ status: 'success', message: res.message || 'Email confirmed.' }))
            .catch(err => setState({ status: 'error', message: err.message || 'Verification failed.' }));
    }, [token]);

    const handleResend = async () => {
        if (!resendEmail) return;
        setResendState({ loading: true, message: '' });
        try {
            const res = await resendVerification(resendEmail);
            setResendState({ loading: false, message: res.message || 'Confirmation link sent. Check your inbox.' });
        } catch (err) {
            setResendState({ loading: false, message: err.message || 'Failed to resend. Try again.' });
        }
    };

    const isPending = state.status === 'pending';
    const isSuccess = state.status === 'success';
    const isError = state.status === 'error';

    return (
        <div className="auth-page">
            <div className="auth-bg"><div className="auth-gradient" /></div>
            <div className="auth-container">
                <div className="auth-card">
                    <div className="auth-header">
                        <Link to="/" className="auth-logo">
                            <img src="/mfz-logo.webp" alt="Web AI" style={{ height: 56, maxWidth: 180, objectFit: 'contain', display: 'block' }} />
                        </Link>
                        <h1>{isPending ? 'Confirming…' : isSuccess ? 'Email Confirmed' : 'Verification Failed'}</h1>
                        <p>
                            {isPending && 'Just a moment while we verify your email address.'}
                            {isSuccess && 'Thanks — your email has been confirmed.'}
                            {isError && 'We could not confirm your email.'}
                        </p>
                    </div>

                    <div style={{ padding: '8px 4px 24px', color: '#475569', fontSize: 14, lineHeight: 1.6, textAlign: 'center' }}>
                        {isPending ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: 20 }}>
                                <span className="spinner" />
                            </div>
                        ) : (
                            <p>{state.message}</p>
                        )}
                        {isSuccess && (
                            <p style={{ marginTop: 16, fontSize: 13, color: '#64748b' }}>
                                An admin will review your account shortly. You'll get another email when it's approved.
                            </p>
                        )}
                    </div>

                    {isError && (
                        <div style={{ padding: '0 4px 20px' }}>
                            <p style={{ fontSize: 13, color: '#64748b', marginBottom: 12, textAlign: 'center' }}>
                                Your link may have expired. Enter your email to get a new confirmation link.
                            </p>
                            <div className="input-wrapper" style={{ marginBottom: 10 }}>
                                <input
                                    type="email"
                                    value={resendEmail}
                                    onChange={(e) => setResendEmail(e.target.value)}
                                    placeholder="you@company.com"
                                    style={{ width: '100%', padding: '10px 14px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 14 }}
                                />
                            </div>
                            {resendState.message && (
                                <div className="auth-error" style={{ background: '#ecfdf5', color: '#047857', borderColor: '#a7f3d0', marginBottom: 8 }}>
                                    {resendState.message}
                                </div>
                            )}
                            <button
                                type="button"
                                onClick={handleResend}
                                disabled={resendState.loading || !resendEmail}
                                style={{
                                    width: '100%', padding: '10px 16px', background: 'transparent',
                                    border: '1px solid #6366f1', borderRadius: 8, color: '#6366f1',
                                    fontWeight: 600, fontSize: 14, cursor: 'pointer', marginBottom: 12,
                                }}
                            >
                                {resendState.loading ? 'Sending…' : 'Resend confirmation link'}
                            </button>
                        </div>
                    )}

                    {!isPending && (
                        <Link to="/login" className="btn-primary full" style={{ display: 'inline-block', textAlign: 'center', textDecoration: 'none' }}>
                            Go to Sign In
                        </Link>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VerifyEmail;
