import config from '../config';

const API_BASE_URL = `${config.apiUrl}/api`;

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
};

// ── File Upload ─────────────────────────────────────────────────────────

export const uploadFiles = async (files) => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    const res = await fetch(`${API_BASE_URL}/generate/upload-files`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
};

// ── Generator ───────────────────────────────────────────────────────────

export const generateWebsite = async (prompt, sessionId = null, niche = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/generate`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ prompt, sessionId, niche }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to generate website');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const generateWebsiteStream = (prompt, sessionId = null, niche = null, onStage, onComplete, onError, templateId = null, currentPage = 'index', userImages = null) => {
    const controller = new AbortController();
    const headers = getAuthHeaders();

    const body = { prompt, sessionId, niche, currentPage };
    if (templateId) body.templateId = templateId;
    if (userImages && userImages.length > 0) body.userImages = userImages;

    // ── Keep-alive: Web Lock (keeps event loop active in background tabs) ──
    let lockRelease = null;
    if (navigator.locks) {
        navigator.locks.request('generate-stream-lock', { mode: 'exclusive', ifAvailable: true }, (lock) => {
            if (!lock) return;
            return new Promise((resolve) => { lockRelease = resolve; });
        });
    }

    // ── Keep-alive: Wake Lock (prevents screen sleep from killing connection) ──
    let wakeLock = null;
    const acquireWakeLock = async () => {
        try {
            if ('wakeLock' in navigator) {
                wakeLock = await navigator.wakeLock.request('screen');
                wakeLock.addEventListener('release', () => { wakeLock = null; });
            }
        } catch (_) { /* Wake Lock not available or denied */ }
    };
    acquireWakeLock();

    // Re-acquire wake lock when tab becomes visible again
    const handleVisibility = () => {
        if (document.visibilityState === 'visible' && !wakeLock) acquireWakeLock();
    };
    document.addEventListener('visibilitychange', handleVisibility);

    const cleanup = () => {
        if (lockRelease) { lockRelease(); lockRelease = null; }
        if (wakeLock) { try { wakeLock.release(); } catch (_) {} wakeLock = null; }
        document.removeEventListener('visibilitychange', handleVisibility);
    };

    // ── Recovery: poll session if stream drops to check if generation finished ──
    const pollForRecovery = async (sid) => {
        if (!sid) return false;
        onStage({ stage: -2, name: 'recovering', status: 'running', message: 'Reconnecting — checking if your website is ready...' });
        for (let attempt = 0; attempt < 80; attempt++) {
            await new Promise(r => setTimeout(r, 5000));
            try {
                const session = await getSession(sid);
                if (session && session.html && session.status !== 'generating') {
                    // Generation completed in the background!
                    onComplete({
                        website: { html: session.html, css: session.css || '', js: session.js || '' },
                        sessionId: sid,
                        plan: session.plan || {},
                        isMultipage: session.multipage || false,
                        pages: session.pages || null,
                        isNewDesign: false,
                        recovered: true,
                    });
                    return true;
                }
                // Session exists but no HTML yet — still generating
                if (session && session.status === 'generating') continue;
            } catch (_) { /* session not found or network error, keep polling */ }
        }
        return false;
    };

    // Track the session ID from stream events for recovery
    let trackedSessionId = sessionId;

    fetch(`${API_BASE_URL}/generator/generate-stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
    }).then(async (response) => {
        if (!response.ok) {
            cleanup();
            try {
                const data = await response.json();
                onError(data.detail || 'Stream failed');
            } catch {
                onError(`Server error (${response.status})`);
            }
            return;
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let eventType = null;
        let completed = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.slice(7).trim();
                } else if (line.startsWith('data: ') && eventType) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        // Track session ID for recovery
                        if (data.sessionId) trackedSessionId = data.sessionId;
                        if (eventType === 'stage') onStage(data);
                        else if (eventType === 'complete') { completed = true; onComplete(data); }
                        else if (eventType === 'error') { completed = true; onError(data.message); }
                    } catch (e) { /* ignore parse errors */ }
                    eventType = null;
                }
            }
        }
        cleanup();
        if (!completed) {
            // Stream dropped — try to recover by polling the session
            const recovered = await pollForRecovery(trackedSessionId);
            if (!recovered) {
                onError('Connection lost — generation may still be processing. Check your session or try again.');
            }
        }
    }).catch(async (err) => {
        cleanup();
        if (err.name === 'AbortError') return;
        // Network error — try recovery polling
        const recovered = await pollForRecovery(trackedSessionId);
        if (!recovered) {
            onError(err.message || 'Network error — please check your connection and try again.');
        }
    });

    return controller;
};

export const getSession = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/session/${sessionId}`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get session');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const getSessionVersions = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/session/${sessionId}/versions`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get versions');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const rollbackSession = async (sessionId, version) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/session/${sessionId}/rollback/${version}`, {
            method: 'POST',
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to rollback');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const clearSession = async (sessionId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/session/${sessionId}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to clear session');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const editElement = async (sessionId, elementData, prompt, currentCode, currentPage = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/edit-element`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                sessionId,
                elementHtml: elementData.outerHTML,
                elementPath: elementData.path,
                prompt,
                currentHtml: currentCode.html,
                currentCss: currentCode.css,
                currentPage,
                contextBefore: elementData.contextBefore || '',
                contextAfter: elementData.contextAfter || '',
                sectionId: elementData.sectionId || '',
                sectionType: elementData.sectionType || '',
                parentTag: elementData.parentTag || '',
                parentClass: elementData.parentClass || '',
            }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to edit element');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const getTemplates = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/templates/`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get templates');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const getNiches = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/niches`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get niches');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

// ── Projects ────────────────────────────────────────────────────────────

export const listProjects = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to list projects');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const getProject = async (projectId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get project');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const saveProject = async (data) => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/save`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || result.detail || 'Failed to save project');
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const getProjectVersions = async (projectId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/versions`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get versions');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const rollbackProject = async (projectId, versionNumber) => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/rollback`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ version_number: versionNumber }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to rollback');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const deleteProject = async (projectId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to delete project');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

// ── Images ──────────────────────────────────────────────────────────────

export const searchImages = async (query, count = 10) => {
    try {
        const response = await fetch(
            `${API_BASE_URL}/images/search?q=${encodeURIComponent(query)}&count=${count}`,
            { headers: getAuthHeaders() }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to search images');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

// ── Components ─────────────────────────────────────────────────────────

export const getComponents = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/components/`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get components');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const generateComponent = async (sessionId, componentType, variantKey, content = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/components/generate`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, componentType, variantKey, content }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to generate component');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const swapComponent = async (sessionId, sectionId, componentType, variantKey) => {
    try {
        const response = await fetch(`${API_BASE_URL}/components/swap`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, componentType, variantKey }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to swap component');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Sections ───────────────────────────────────────────────────────────

export const getSections = async (sessionId, pageSlug = 'index') => {
    try {
        const url = pageSlug && pageSlug !== 'index'
            ? `${API_BASE_URL}/sections/${sessionId}?page_slug=${encodeURIComponent(pageSlug)}`
            : `${API_BASE_URL}/sections/${sessionId}`;
        const response = await fetch(url, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get sections');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const reorderSections = async (sessionId, newOrder, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/reorder`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, newOrder, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to reorder');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const deleteSection = async (sessionId, sectionId, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/delete`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to delete section');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const duplicateSection = async (sessionId, sectionId, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/duplicate`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to duplicate section');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const regenerateSection = async (sessionId, sectionId, prompt, variantKey = null, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/regenerate`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, prompt, variantKey, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to regenerate section');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Design System ──────────────────────────────────────────────────────

export const updateDesignSystem = async (sessionId, designSystem) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/design-system`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, designSystem }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to update design system');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const generateDesignSystem = async (prompt, niche = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/design-system/generate`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ prompt, niche }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to generate design system');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Jobs (Async Generation) ─────────────────────────────────────────────

export const submitJob = async (prompt, niche = null, designSystem = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/submit`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ prompt, niche, designSystem }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to submit job');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const getJobStatus = async (jobId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get job status');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const listJobs = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to list jobs');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const cancelJob = async (jobId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
            method: 'DELETE', headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to cancel job');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Template Catalog ────────────────────────────────────────────────────

export const listTemplateCatalog = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/templates/`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to list templates');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const getTemplateFull = async (templateId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to get template');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Auth ────────────────────────────────────────────────────────────────

export const signup = async (data) => {
    const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Signup failed');
    return result;
};

export const login = async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Login failed');
    return result;
};

export const getMe = async (token) => {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to get user');
    return result;
};

export const restoreSession = async (html, css, js = '', projectId = null, { isMultipage = false, pages = null, currentPage = 'index' } = {}) => {
    try {
        const body = { html, css, js, projectId, isMultipage, currentPage };
        if (isMultipage && pages) body.pages = pages;
        const response = await fetch(`${API_BASE_URL}/generator/restore-session`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to restore session');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};

export const syncSession = async (sessionId, html, css, js = '', currentPage = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/sync-session`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, html, css, js, currentPage }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.detail || 'Failed to sync session');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Uploads / Media ─────────────────────────────────────────────────────

export const uploadFile = async (file, projectId = null, category = 'image') => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    if (projectId) formData.append('project_id', projectId);
    formData.append('category', category);
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/upload`, {
            method: 'POST',
            headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to upload file');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const listAllUploads = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/gallery`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to list uploads');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const listUploads = async (projectId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/list/${projectId}`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to list uploads');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const deleteUpload = async (mediaId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/${mediaId}`, {
            method: 'DELETE', headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to delete upload');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const saveStockPhoto = async (imageUrl, projectId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/from-url`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ url: imageUrl, project_id: projectId }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to save stock photo');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const transformImage = async (mediaId, crop, targetWidth, targetHeight) => {
    try {
        const response = await fetch(`${API_BASE_URL}/uploads/transform`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ media_id: mediaId, crop, target_width: targetWidth, target_height: targetHeight }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to transform image');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Section Controls (extended) ─────────────────────────────────────────

export const insertSection = async (sessionId, sectionHtml, sectionCss, referenceSectionId, position = 'after', pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/insert`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionHtml, sectionCss, referenceSectionId, position, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to insert section');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const toggleSectionVisibility = async (sessionId, sectionId, visible, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/toggle-visibility`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, visible, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to toggle visibility');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const updateSectionStyle = async (sessionId, sectionId, styles, pageSlug = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/update-style`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, styles, pageSlug }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to update section style');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Content Editors ─────────────────────────────────────────────────────

export const previewSwap = async (sessionId, sectionId, componentType, variantKey, content = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/components/preview-swap`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, sectionId, componentType, variantKey, content }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to preview swap');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const updateNavConfig = async (sessionId, navItems, sticky = false) => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/update-nav`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, items: navItems, sticky }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to update navigation');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const updateFooterConfig = async (sessionId, columns, copyrightText, socialLinks) => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/update-footer`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, columns, copyrightText, socialLinks }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to update footer');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const updateSiteMeta = async (sessionId, meta) => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/update-meta`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, ...meta }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to update site meta');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

export const updateContactConfig = async (sessionId, config) => {
    try {
        const response = await fetch(`${API_BASE_URL}/sections/update-contact`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ sessionId, ...config }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Failed to update contact config');
        return data;
    } catch (error) { console.error('API Error:', error); throw error; }
};

// ── Deploy & Domains ──────────────────────────────────────────────────

export const deleteDeployedSite = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/deploy/${siteId}`, {
        method: 'DELETE', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to delete site');
    return data;
};

export const listDeployedSites = async () => {
    const response = await fetch(`${API_BASE_URL}/deploy`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to list sites');
    return data;
};

export const connectDomain = async (siteId, domainName) => {
    const response = await fetch(`${API_BASE_URL}/deploy/${siteId}/connect-domain`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ domain_name: domainName }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to connect domain');
    return data;
};

export const getDomainStatus = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/deploy/${siteId}/domain-status`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get domain status');
    return data;
};

export const disconnectDomain = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/deploy/${siteId}/disconnect-domain`, {
        method: 'DELETE', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to disconnect domain');
    return data;
};

export const listDnsRecords = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/dns/${siteId}/records`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to list DNS records');
    return data;
};

export const addDnsRecord = async (siteId, record) => {
    const response = await fetch(`${API_BASE_URL}/dns/${siteId}/records`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify(record),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to add DNS record');
    return data;
};

export const deleteDnsRecord = async (siteId, record) => {
    const response = await fetch(`${API_BASE_URL}/dns/${siteId}/records`, {
        method: 'DELETE', headers: getAuthHeaders(),
        body: JSON.stringify(record),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to delete DNS record');
    return data;
};

export const getDnsNameservers = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/dns/${siteId}/nameservers`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get nameservers');
    return data;
};

// ── Site Features (Export, Custom Code, Analytics) ───────────────────

export const exportSiteZip = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/sites/${siteId}/export`, { headers: getAuthHeaders() });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Export failed');
    }
    return response.blob();
};

export const getCustomCode = async (siteId) => {
    const response = await fetch(`${API_BASE_URL}/sites/${siteId}/custom-code`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get custom code');
    return data;
};

export const updateCustomCode = async (siteId, headCode, bodyCode) => {
    const response = await fetch(`${API_BASE_URL}/sites/${siteId}/custom-code`, {
        method: 'PUT', headers: getAuthHeaders(),
        body: JSON.stringify({ head_code: headCode, body_code: bodyCode }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to save custom code');
    return data;
};

export const getSiteAnalytics = async (siteId, days = 30) => {
    const response = await fetch(`${API_BASE_URL}/sites/${siteId}/analytics?days=${days}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get analytics');
    return data;
};

// ── Form Inbox ────────────────────────────────────────────────────────

export const getFormSubmissions = async (siteId = null, isRead = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams({ limit, offset });
    if (siteId) params.append('site_id', siteId);
    if (isRead !== null) params.append('is_read', isRead);
    const response = await fetch(`${API_BASE_URL}/forms/submissions?${params}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch submissions');
    return data;
};

export const getUnreadCount = async () => {
    const response = await fetch(`${API_BASE_URL}/forms/unread-count`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) return { unread_count: 0 };
    return data;
};

export const markSubmissionRead = async (submissionId) => {
    const response = await fetch(`${API_BASE_URL}/forms/submissions/${submissionId}/read`, {
        method: 'PATCH', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to mark as read');
    return data;
};

export const deleteFormSubmission = async (submissionId) => {
    const response = await fetch(`${API_BASE_URL}/forms/submissions/${submissionId}`, {
        method: 'DELETE', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to delete');
    return data;
};

// ── Announcements ─────────────────────────────────────────────────────

export const getActiveAnnouncements = async () => {
    const response = await fetch(`${API_BASE_URL}/admin/announcements/active`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) return { announcements: [] };
    return data;
};

// ── Password Reset ─────────────────────────────────────────────────────

export const forgotPassword = async (email) => {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Request failed');
    return data;
};

export const resetPassword = async (token, newPassword) => {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Reset failed');
    return data;
};

export const changePassword = async (currentPassword, newPassword) => {
    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Change failed');
    return data;
};

// ── Admin ──────────────────────────────────────────────────────────────

export const adminGetStats = async () => {
    const response = await fetch(`${API_BASE_URL}/admin/stats`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetTokenStats = async () => {
    const response = await fetch(`${API_BASE_URL}/admin/token-stats`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminListUsers = async (limit = 50, offset = 0) => {
    const response = await fetch(`${API_BASE_URL}/admin/users?limit=${limit}&offset=${offset}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminDisableUser = async (userId) => {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/disable`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminEnableUser = async (userId) => {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/enable`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGrantTokens = async (userId, amount) => {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/grant-tokens`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ amount }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminResetPassword = async (userId) => {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/reset-password`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetSystemInfo = async () => {
    const response = await fetch(`${API_BASE_URL}/admin/system`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetGenerations = async (limit = 50, offset = 0) => {
    const response = await fetch(`${API_BASE_URL}/admin/generations?limit=${limit}&offset=${offset}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetModeration = async (limit = 50) => {
    const response = await fetch(`${API_BASE_URL}/admin/moderation?limit=${limit}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminResetCircuit = async (provider) => {
    const response = await fetch(`${API_BASE_URL}/admin/circuit/${provider}/reset`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetAnalytics = async (days = 30) => {
    const response = await fetch(`${API_BASE_URL}/admin/analytics?days=${days}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

export const adminGetUserDetail = async (userId) => {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed');
    return data;
};

// ── Domain Purchase & Management ─────────────────────────────────────

export const searchDomains = async (query, extensions) => {
    const params = new URLSearchParams({ q: query });
    if (extensions && Array.isArray(extensions)) params.append('extensions', extensions.join(','));
    else if (extensions) params.append('extensions', extensions);
    const response = await fetch(`${API_BASE_URL}/domains/search?${params}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Domain search failed');
    return data;
};

export const purchaseDomain = async (domainName, tld, siteId = null, period = 1) => {
    const response = await fetch(`${API_BASE_URL}/domains/purchase`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ domain_name: domainName, tld, period, site_id: siteId, auto_renew: true }),
    });
    const data = await response.json();
    if (!response.ok) {
        const detail = data.detail;
        const msg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ') : 'Domain purchase failed';
        throw new Error(msg);
    }
    return data;
};

export const listUserDomains = async () => {
    const response = await fetch(`${API_BASE_URL}/domains`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to list domains');
    return data;
};

export const getDomainDetail = async (domainId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get domain details');
    return data;
};

export const connectDomainToSite = async (domainId, siteId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/connect`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ site_id: siteId }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to connect domain to site');
    return data;
};

export const disconnectDomainFromSite = async (domainId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/disconnect`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to disconnect domain');
    return data;
};

export const retryDomainActivation = async (domainId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/retry-activation`, {
        method: 'POST', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to retry activation');
    return data;
};

export const getDomainContact = async (domainId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/contact`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch contact info');
    return data;
};

export const updateDomainContact = async (domainId, fields) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/contact`, {
        method: 'PUT', headers: getAuthHeaders(),
        body: JSON.stringify(fields),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to update contact');
    return data;
};

export const requestDomainTransfer = async (domainId, reason = '') => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/request-transfer`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ reason }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to request transfer');
    return data;
};

export const cancelDomainTransfer = async (domainId) => {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}/cancel-transfer`, {
        method: 'DELETE', headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to cancel transfer');
    return data;
};

// ── Token Requests ────────────────────────────────────────────────────

export const requestTokens = async (amount, reason = '') => {
    const response = await fetch(`${API_BASE_URL}/auth/token-request`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ amount, reason }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to submit request');
    return data;
};

export const getMyTokenRequests = async () => {
    const response = await fetch(`${API_BASE_URL}/auth/token-requests`, { headers: getAuthHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to fetch requests');
    return data;
};

const api = {
    generateWebsite, getSession, getSessionVersions, rollbackSession, clearSession,
    editElement, getNiches, getTemplates,
    listProjects, getProject, saveProject, getProjectVersions, rollbackProject, deleteProject,
    searchImages, signup, login, getMe,
    getComponents, generateComponent, swapComponent, previewSwap,
    getSections, reorderSections, deleteSection, duplicateSection, regenerateSection,
    insertSection, toggleSectionVisibility, updateSectionStyle,
    updateDesignSystem, generateDesignSystem,
    submitJob, getJobStatus, listJobs, cancelJob,
    listTemplateCatalog, getTemplateFull,
    restoreSession, syncSession,
    uploadFile, listUploads, deleteUpload, saveStockPhoto, transformImage,
    updateNavConfig, updateFooterConfig, updateSiteMeta, updateContactConfig,
    forgotPassword, resetPassword, changePassword,
    listDeployedSites, connectDomain, getDomainStatus, disconnectDomain,
    searchDomains, purchaseDomain, listUserDomains, getDomainDetail,
    connectDomainToSite, disconnectDomainFromSite, retryDomainActivation,
    getDomainContact, updateDomainContact, requestDomainTransfer, cancelDomainTransfer,
    listDnsRecords, addDnsRecord, deleteDnsRecord, getDnsNameservers,
    adminGetStats, adminGetTokenStats, adminListUsers, adminDisableUser,
    adminEnableUser, adminGrantTokens, adminResetPassword,
    adminGetSystemInfo, adminGetGenerations, adminGetModeration,
    adminResetCircuit, adminGetUserDetail, adminGetAnalytics,
};
export default api;
