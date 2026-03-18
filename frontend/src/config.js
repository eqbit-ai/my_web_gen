// src/config.js
const getApiUrl = () => {
    if (process.env.REACT_APP_API_URL) return process.env.REACT_APP_API_URL;
    // In production, API is on the same host (behind ALB)
    if (window.location.hostname !== 'localhost') return window.location.origin;
    return 'http://localhost:8000';
};

const config = {
    apiUrl: getApiUrl()
};

export default config;
