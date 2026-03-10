import config from '../config';

const API_BASE_URL = `${config.apiUrl}/api`;

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
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

export const generateWebsiteStream = (prompt, sessionId = null, niche = null, onStage, onComplete, onError, templateId = null, currentPage = 'index') => {
    const controller = new AbortController();
    const headers = getAuthHeaders();

    const body = { prompt, sessionId, niche, currentPage };
    if (templateId) body.templateId = templateId;

    fetch(`${API_BASE_URL}/generator/generate-stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
    }).then(async (response) => {
        if (!response.ok) {
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
                        if (eventType === 'stage') onStage(data);
                        else if (eventType === 'complete') { completed = true; onComplete(data); }
                        else if (eventType === 'error') { completed = true; onError(data.message); }
                    } catch (e) { /* ignore parse errors */ }
                    eventType = null;
                }
            }
        }
        // Stream closed without complete/error event — notify the UI
        if (!completed) onError('Connection lost — generation may still be processing. Please try again.');
    }).catch((err) => {
        if (err.name !== 'AbortError') onError(err.message);
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

export const editElement = async (sessionId, elementHtml, elementPath, prompt, currentCode, currentPage = 'index') => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/edit-element`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                sessionId,
                elementHtml,
                elementPath,
                prompt,
                currentHtml: currentCode.html,
                currentCss: currentCode.css,
                currentPage,
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

export const restoreSession = async (html, css, js = '', projectId = null) => {
    try {
        const response = await fetch(`${API_BASE_URL}/generator/restore-session`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ html, css, js, projectId }),
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

export default {
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
};
