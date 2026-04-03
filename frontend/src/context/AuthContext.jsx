import React, { createContext, useContext, useState, useEffect } from 'react';
import { signup as apiSignup, login as apiLogin, getMe } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// Per-tab token storage: sessionStorage is per-tab, localStorage is shared.
// On login, store in BOTH so new tabs from the same session auto-login,
// but each tab can independently switch users (e.g. admin impersonation).
function getStoredToken() {
    return sessionStorage.getItem('token') || localStorage.getItem('token') || null;
}
function storeToken(token) {
    sessionStorage.setItem('token', token);
    localStorage.setItem('token', token);
}
function clearToken() {
    sessionStorage.removeItem('token');
    localStorage.removeItem('token');
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(getStoredToken());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            // Ensure sessionStorage has the token for this tab
            sessionStorage.setItem('token', token);
            getMe(token)
                .then(setUser)
                .catch(() => {
                    clearToken();
                    setToken(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [token]);

    const login = async (email, password) => {
        const data = await apiLogin(email, password);
        storeToken(data.token);
        setToken(data.token);
        setUser(data.user);
        if (data.force_password_reset) {
            localStorage.setItem('force_password_reset', 'true');
        } else {
            localStorage.removeItem('force_password_reset');
        }
        return data;
    };

    const signup = async (formData) => {
        const data = await apiSignup(formData);
        storeToken(data.token);
        setToken(data.token);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        clearToken();
        setToken(null);
        setUser(null);
    };

    const refreshUser = async () => {
        if (token) {
            try {
                const data = await getMe(token);
                setUser(data);
            } catch { /* ignore */ }
        }
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, signup, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
}
