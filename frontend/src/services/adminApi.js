import config from '../config';

const API_BASE_URL = `${config.apiUrl}/api`;

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
};

const apiGet = async (path) => {
    const response = await fetch(`${API_BASE_URL}${path}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

const apiPost = async (path, body = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

const apiPut = async (path, body = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

const apiPatch = async (path, body = {}) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

const apiDelete = async (path) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

// ── Sites ────────────────────────────────────────────────────────────────

export const adminGetSites = async (page = 1, limit = 20, status = null, userId = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (status) qs += `&status=${status}`;
    if (userId) qs += `&user_id=${userId}`;
    return apiGet(`/admin/sites${qs}`);
};

export const adminGetSiteDetail = async (siteId) => {
    return apiGet(`/admin/sites/${siteId}`);
};

export const adminGetSitePreview = async (siteId) => {
    return apiGet(`/admin/sites/${siteId}/preview`);
};

export const adminRebuildSite = async (siteId) => {
    return apiPost(`/admin/sites/${siteId}/rebuild`);
};

// ── Generations ──────────────────────────────────────────────────────────

export const adminGetGenerations = async (page = 1, limit = 20, status = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (status) qs += `&status=${status}`;
    return apiGet(`/admin/generations${qs}`);
};

export const adminGetGenerationQueue = async () => {
    return apiGet('/admin/generations/queue');
};

export const adminGetFailedGenerations = async (page = 1, limit = 20) => {
    return apiGet(`/admin/generations/failed?page=${page}&limit=${limit}`);
};

export const adminRetryGeneration = async (logId) => {
    return apiPost(`/admin/generations/${logId}/retry`);
};

export const adminGetGenerationSuccessRate = async () => {
    return apiGet('/admin/generations/success-rate');
};

// ── Domains ──────────────────────────────────────────────────────────────

export const adminGetDomains = async (page = 1, limit = 20, status = null, tld = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (status) qs += `&status=${status}`;
    if (tld) qs += `&tld=${tld}`;
    return apiGet(`/admin/domains${qs}`);
};

export const adminGetDomainDetail = async (domainId) => {
    return apiGet(`/admin/domains/${domainId}`);
};

export const adminUpdateDomain = async (domainId, data) => {
    return apiPatch(`/admin/domains/${domainId}`, data);
};

export const adminGetExpiringDomains = async (days = 30) => {
    return apiGet(`/admin/domains/expiring?days=${days}`);
};

export const adminGetAeQueue = async () => {
    return apiGet('/admin/domains/ae-queue');
};

export const adminVerifyDomain = async (domainId, status, notes = '') => {
    return apiPost(`/admin/domains/${domainId}/verify`, { status, notes });
};

export const adminReprovisionSSL = async (domainId) => {
    return apiPost(`/admin/domains/${domainId}/ssl/reprovision`);
};

export const adminGetDomainHealth = async () => {
    return apiGet('/admin/domains/health');
};

// ── Users (enhanced) ─────────────────────────────────────────────────────

export const adminGetUsers = async (page = 1, limit = 20, search = '', isActive = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (search) qs += `&search=${encodeURIComponent(search)}`;
    if (isActive !== null) qs += `&is_active=${isActive}`;
    return apiGet(`/admin/users${qs}`);
};

export const adminGetUserDetail = async (userId) => {
    return apiGet(`/admin/users/${userId}`);
};

export const adminGetUserAudit = async (userId, page = 1, limit = 20) => {
    return apiGet(`/admin/users/${userId}/audit?page=${page}&limit=${limit}`);
};

export const adminGetUserLogins = async (userId, page = 1, limit = 20) => {
    return apiGet(`/admin/users/${userId}/logins?page=${page}&limit=${limit}`);
};

export const adminImpersonateUser = async (userId) => {
    return apiPost(`/admin/users/${userId}/impersonate`);
};

export const adminBulkAction = async (action, userIds, params = {}) => {
    return apiPost('/admin/users/bulk', { action, user_ids: userIds, ...params });
};

export const adminExportUsers = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/admin/users/export`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    if (!response.ok) throw new Error('Export failed');
    return response.blob();
};

export const adminVerifyLicence = async (userId, verified) => {
    return apiPatch(`/admin/users/${userId}/licence`, { verified });
};

export const adminDisableUser = async (userId) => {
    return apiPost(`/admin/users/${userId}/disable`);
};

export const adminEnableUser = async (userId) => {
    return apiPost(`/admin/users/${userId}/enable`);
};

export const adminGrantTokens = async (userId, amount) => {
    return apiPost(`/admin/users/${userId}/grant-tokens`, { amount });
};

export const adminResetPassword = async (userId) => {
    return apiPost(`/admin/users/${userId}/reset-password`);
};

// ── Tokens ───────────────────────────────────────────────────────────────

export const adminGetTransactions = async (page = 1, limit = 20, userId = null, type = null, dateRange = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (userId) qs += `&user_id=${userId}`;
    if (type) qs += `&type=${type}`;
    if (dateRange) qs += `&date_from=${dateRange.from}&date_to=${dateRange.to}`;
    return apiGet(`/admin/tokens/transactions${qs}`);
};

export const adminGetUserTransactions = async (userId, page = 1, limit = 20) => {
    return apiGet(`/admin/tokens/transactions?user_id=${userId}&page=${page}&limit=${limit}`);
};

export const adminGrantTokensWithExpiry = async (userId, amount, expiresAt, reason = '') => {
    return apiPost('/admin/tokens/grant', { user_id: userId, amount, expires_at: expiresAt, reason });
};

export const adminGetTokenPool = async () => {
    return apiGet('/admin/tokens/pool');
};

export const adminGetExpiringTokens = async () => {
    return apiGet('/admin/tokens/expiring');
};

// ── Operations ───────────────────────────────────────────────────────────

export const adminGetTemplates = async () => {
    return apiGet('/admin/templates');
};

export const adminUpdateTemplate = async (templateId, data) => {
    return apiPatch(`/admin/templates/${templateId}`, data);
};

export const adminGetAuditLogs = async (page = 1, limit = 20, actionType = null, userId = null) => {
    let qs = `?page=${page}&limit=${limit}`;
    if (actionType) qs += `&action_type=${actionType}`;
    if (userId) qs += `&user_id=${userId}`;
    return apiGet(`/admin/audit-logs${qs}`);
};

export const adminGetAnnouncements = async () => {
    return apiGet('/admin/announcements');
};

export const adminCreateAnnouncement = async (data) => {
    return apiPost('/admin/announcements', data);
};

export const adminUpdateAnnouncement = async (id, data) => {
    return apiPatch(`/admin/announcements/${id}`, data);
};

export const adminDeleteAnnouncement = async (id) => {
    return apiDelete(`/admin/announcements/${id}`);
};

export const adminGetActiveAnnouncements = async () => {
    return apiGet('/admin/announcements/active');
};

export const adminGetPrompts = async () => {
    return apiGet('/admin/prompts');
};

export const adminSavePrompt = async (key, content) => {
    return apiPost(`/admin/prompts/${encodeURIComponent(key)}`, { content });
};

export const adminPublishPrompt = async (key, version) => {
    return apiPost(`/admin/prompts/${encodeURIComponent(key)}/${encodeURIComponent(version)}/publish`);
};

export const adminGetSystemInfo = async () => {
    return apiGet('/admin/system');
};

export const adminResetCircuit = async (provider) => {
    return apiPost(`/admin/circuit/${provider}/reset`);
};

// ── Analytics ────────────────────────────────────────────────────────────

export const adminGetGrowthAnalytics = async (days = 30) => {
    return apiGet(`/admin/analytics/growth?days=${days}`);
};

export const adminGetGenerationStats = async (days = 30) => {
    return apiGet(`/admin/analytics/generation-success?days=${days}`);
};

export const adminGetTokenConsumption = async (days = 30) => {
    return apiGet(`/admin/analytics/token-consumption?days=${days}`);
};

export const adminGetStats = async () => {
    return apiGet('/admin/stats');
};
