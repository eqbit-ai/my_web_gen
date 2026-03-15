import React, { createContext, useContext, useState, useEffect } from 'react';
import { signup as apiSignup, login as apiLogin, getMe } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            getMe(token)
                .then(setUser)
                .catch(() => {
                    localStorage.removeItem('token');
                    setToken(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [token]);

    const login = async (email, password) => {
        const data = await apiLogin(email, password);
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data;
    };

    const signup = async (formData) => {
        const data = await apiSignup(formData);
        localStorage.setItem('token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        localStorage.removeItem('token');
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
