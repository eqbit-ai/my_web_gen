// src/components/Navbar.jsx

import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
    const [scrolled, setScrolled] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const location = useLocation();

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 40);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        setMobileOpen(false);
    }, [location]);

    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const isAuth = location.pathname === '/login' || location.pathname === '/signup';

    return (
        <nav className={`navbar ${scrolled ? 'scrolled' : ''} ${isAuth ? 'navbar-auth' : ''}`}>
            <div className="navbar-inner">
                <Link to="/" className="nav-logo">
                    <img src="/mfz-logo.webp" alt="Meydan Free Zone" className="nav-logo-img" />
                </Link>

                <div className={`nav-links ${mobileOpen ? 'open' : ''}`}>
                    <a href="#showcase" className="nav-link">Generator</a>
                    <a href="#how-it-works" className="nav-link">How It Works</a>
                </div>

                <div className="nav-actions">
                    {user ? (
                        <>
                            <span className="nav-link" style={{ cursor: 'default' }}>{user.full_name}</span>
                            <button className="btn-primary btn-sm" onClick={() => { logout(); navigate('/'); }}>
                                Log Out
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link">Log In</Link>
                            <Link to="/signup" className="btn-primary btn-sm">
                                Get Started
                            </Link>
                        </>
                    )}
                </div>

                <button
                    className={`hamburger ${mobileOpen ? 'open' : ''}`}
                    onClick={() => setMobileOpen(!mobileOpen)}
                    aria-label="Toggle menu"
                >
                    <span /><span /><span />
                </button>
            </div>

            {mobileOpen && (
                <div className="mobile-menu">
                    <a href="#showcase" className="mobile-link" onClick={() => setMobileOpen(false)}>Generator</a>
                    <a href="#how-it-works" className="mobile-link" onClick={() => setMobileOpen(false)}>How It Works</a>
                    <div className="mobile-actions">
                        {user ? (
                            <button className="btn-primary full" onClick={() => { logout(); navigate('/'); setMobileOpen(false); }}>
                                Log Out
                            </button>
                        ) : (
                            <>
                                <Link to="/login" className="btn-secondary full">Log In</Link>
                                <Link to="/signup" className="btn-primary full">Get Started</Link>
                            </>
                        )}
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;
