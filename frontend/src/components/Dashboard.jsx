// src/components/Dashboard.jsx

import config from '../config';
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listProjects, getProject, deleteProject, listTemplateCatalog, getTemplateFull, listDeployedSites, deleteDeployedSite, connectDomain, connectDomainAndWait, getDomainStatus, disconnectDomain, listDnsRecords, addDnsRecord, deleteDnsRecord, getDnsNameservers, getActiveAnnouncements, searchDomains, purchaseDomain, purchaseDomainAndWait, getDomainContact, updateDomainContact, requestDomainTransfer, cancelDomainTransfer, requestTokens, getMyTokenRequests, listUserDomains, getFormSubmissions, getUnreadCount, markSubmissionRead, deleteFormSubmission, exportSiteZip, getCustomCode, updateCustomCode, getSiteAnalytics, listAllUploads, uploadFile, deleteUpload } from '../services/api';

// CSS override injected into iframe srcDoc to force-show elements hidden by scroll animations
const IFRAME_VISIBILITY_FIX = `* { opacity: 1 !important; transform: none !important; transition: none !important; animation: none !important; } img { display: inline-block !important; }`;

// Trap every <a> click inside the preview iframe so href="#", empty hashes
// and full URLs can't navigate the iframe (which inherits the parent's
// origin and would otherwise replace the template preview with the dashboard
// or open the link in-place). Also disables form submissions.
const IFRAME_CLICK_TRAP = `
(function(){
  function stop(e){
    var a = e.target && e.target.closest && e.target.closest('a');
    if (a) { e.preventDefault(); e.stopPropagation(); return false; }
  }
  document.addEventListener('click', stop, true);
  document.addEventListener('submit', function(e){ e.preventDefault(); e.stopPropagation(); return false; }, true);
})();
`;

const buildSrcDoc = (css, html, withScripts = false) =>
    `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><base target="_blank"><style>${IFRAME_VISIBILITY_FIX}</style><style>${css || ''}</style></head><body>${html || ''}<script>${IFRAME_CLICK_TRAP}<\/script></body></html>`;


const Dashboard = () => {
    const { user, logout, refreshUser } = useAuth();

    // Refresh user data on mount, focus, and periodically (picks up admin approvals)
    useEffect(() => {
        refreshUser();
        const handleFocus = () => refreshUser();
        window.addEventListener('focus', handleFocus);
        const interval = setInterval(() => refreshUser(), 30000);
        return () => { window.removeEventListener('focus', handleFocus); clearInterval(interval); };
    }, []);
    const navigate = useNavigate();
    // Inline parked-domain picker (opens below the "Use Existing Domain"
    // button on the home tab — see render below for full reasoning).
    const [existingDomainPickerOpen, setExistingDomainPickerOpen] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [activeTab, setActiveTab] = useState(() => {
        const hash = window.location.hash.replace('#', '');
        const allowed = ['home', 'projects', 'templates', 'domains', 'inbox', 'gallery'];
        return allowed.includes(hash) ? hash : 'home';
    });
    const [expandedSections, setExpandedSections] = useState({});
    const userMenuRef = useRef(null);

    // Projects state
    const [projects, setProjects] = useState([]);
    const [projectsLoading, setProjectsLoading] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    // Templates state
    const [templates, setTemplates] = useState([]);
    const [templatesLoading, setTemplatesLoading] = useState(false);
    const [templatePreviews, setTemplatePreviews] = useState({});
    const [previewModal, setPreviewModal] = useState(null);

    // Domains state
    const [deployedSites, setDeployedSites] = useState([]);
    const [domainsLoading, setDomainsLoading] = useState(false);
    const [connectModal, setConnectModal] = useState(null); // site_id to connect
    const [domainInput, setDomainInput] = useState('');
    const [connecting, setConnecting] = useState(false);
    const [connectResult, setConnectResult] = useState(null);
    const [modalOwnedDomains, setModalOwnedDomains] = useState([]);
    const [connectingOwned, setConnectingOwned] = useState(null);
    const [disconnectConfirm, setDisconnectConfirm] = useState(null);
    const [dnsRecords, setDnsRecords] = useState({}); // { siteId: records[] }
    const [addRecordModal, setAddRecordModal] = useState(null); // site_id
    const [newRecord, setNewRecord] = useState({ name: '', type: 'A', value: '', ttl: 300 });
    const [addingRecord, setAddingRecord] = useState(false);
    const [deleteSiteConfirm, setDeleteSiteConfirm] = useState(null);
    const [newDesignModal, setNewDesignModal] = useState(false);
    const [newDesignPreview, setNewDesignPreview] = useState(null); // template id for preview inside new design modal
    const [nameservers, setNameservers] = useState({}); // { siteId: string[] }
    const [contactInfo, setContactInfo] = useState({}); // { domainRecordId: contactObj }
    const [contactLoading, setContactLoading] = useState({});
    const [contactEditing, setContactEditing] = useState(null); // domainRecordId being edited
    const [contactForm, setContactForm] = useState({});
    const [contactSaving, setContactSaving] = useState(false);
    const [transferModal, setTransferModal] = useState(null); // domainRecordId
    const [transferReason, setTransferReason] = useState('');
    const [transferSubmitting, setTransferSubmitting] = useState(false);
    const [transferResult, setTransferResult] = useState(null);

    // Token request state
    const [tokenRequestModal, setTokenRequestModal] = useState(false);
    const [tokenRequestAmount, setTokenRequestAmount] = useState('1');
    const [tokenRequestReason, setTokenRequestReason] = useState('');
    const [tokenRequestSubmitting, setTokenRequestSubmitting] = useState(false);
    const [tokenRequests, setTokenRequests] = useState([]);
    const [tokenRequestsLoaded, setTokenRequestsLoaded] = useState(false);
    // Gallery state
    const [galleryImages, setGalleryImages] = useState([]);
    const [galleryLoading, setGalleryLoading] = useState(false);
    const [galleryUploading, setGalleryUploading] = useState(false);
    const [galleryCopied, setGalleryCopied] = useState(null);
    const [galleryDeleteConfirm, setGalleryDeleteConfirm] = useState(null);
    const galleryFileRef = useRef(null);

    // Site features state
    const [customCodeModal, setCustomCodeModal] = useState(null); // site_id
    const [customHeadCode, setCustomHeadCode] = useState('');
    const [customBodyCode, setCustomBodyCode] = useState('');
    const [customCodeSaving, setCustomCodeSaving] = useState(false);
    const [analyticsModal, setAnalyticsModal] = useState(null); // site_id
    const [analyticsData, setAnalyticsData] = useState(null);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const [exporting, setExporting] = useState(null); // site_id

    // Inbox state
    const [submissions, setSubmissions] = useState([]);
    const [submissionsLoading, setSubmissionsLoading] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);
    const [inboxSiteFilter, setInboxSiteFilter] = useState('');
    const [inboxReadFilter, setInboxReadFilter] = useState('');
    const [expandedSubmission, setExpandedSubmission] = useState(null);
    const [deleteSubmissionConfirm, setDeleteSubmissionConfirm] = useState(null);

    // Toast notification state
    const [toast, setToast] = useState(null);
    const toastTimer = useRef(null);
    const showToast = (message, type = 'info') => {
        if (toastTimer.current) clearTimeout(toastTimer.current);
        setToast({ message, type });
        toastTimer.current = setTimeout(() => setToast(null), 4000);
    };

    const domainPollRef = useRef(null);
    const [announcements, setAnnouncements] = useState([]);
    const [dismissedAnnouncements, setDismissedAnnouncements] = useState(() => {
        try { return JSON.parse(localStorage.getItem('dismissed_announcements') || '[]'); } catch { return []; }
    });

    // Fetch active announcements
    useEffect(() => {
        getActiveAnnouncements().then(res => {
            setAnnouncements(res?.announcements || []);
        }).catch(() => { });
    }, []);

    const dismissAnnouncement = (id) => {
        const updated = [...dismissedAnnouncements, id];
        setDismissedAnnouncements(updated);
        localStorage.setItem('dismissed_announcements', JSON.stringify(updated));
    };

    const visibleAnnouncements = announcements.filter(a => !dismissedAnnouncements.includes(a.id));

    // Fetch user's available (unconnected) domains when connect modal opens
    useEffect(() => {
        if (!connectModal) { setModalOwnedDomains([]); return; }
        const token = sessionStorage.getItem('token') || localStorage.getItem('token');
        fetch(`${config.apiUrl}/api/deploy/${connectModal}/available-domains`, {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(r => r.json())
            .then(data => setModalOwnedDomains(data.available_domains || []))
            .catch(() => setModalOwnedDomains([]));
    }, [connectModal]);

    // Persist active tab in URL hash
    useEffect(() => {
        window.location.hash = activeTab;
    }, [activeTab]);

    const firstName = user?.full_name?.split(' ')[0] || 'there';

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good morning';
        if (hour < 18) return 'Good afternoon';
        return 'Good evening';
    };

    const toggleSection = (domainId, section) => {
        const key = `${domainId}-${section}`;
        setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const isSectionExpanded = (domainId, section) => {
        return expandedSections[`${domainId}-${section}`] === true;
    };

    const loadContactInfo = async (domainRecordId) => {
        if (!domainRecordId || contactInfo[domainRecordId] || contactLoading[domainRecordId]) return;
        setContactLoading(prev => ({ ...prev, [domainRecordId]: true }));
        try {
            const data = await getDomainContact(domainRecordId);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: data.contact || false }));
        } catch (err) {
            console.error('Failed to load contact:', err);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: false }));
        } finally {
            setContactLoading(prev => ({ ...prev, [domainRecordId]: false }));
        }
    };

    const handleContactEdit = (domainRecordId) => {
        const c = contactInfo[domainRecordId];
        setContactForm({
            first_name: c?.first_name || '',
            last_name: c?.last_name || '',
            company_name: c?.company_name || '',
            email: c?.email || '',
            phone: c?.phone || '',
        });
        setContactEditing(domainRecordId);
    };

    const handleContactSave = async (domainRecordId) => {
        setContactSaving(true);
        try {
            await updateDomainContact(domainRecordId, contactForm);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: { ...prev[domainRecordId], ...contactForm } }));
            setContactEditing(null);
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            setContactSaving(false);
        }
    };

    const handleTransferRequest = async () => {
        if (!transferModal) return;
        setTransferSubmitting(true);
        try {
            const result = await requestDomainTransfer(transferModal, transferReason);
            setTransferResult(result);
            // Refresh sites
            const data = await listDeployedSites();
            setDeployedSites(data.sites || []);
        } catch (err) {
            setTransferResult({ status: 'error', message: err.message });
        } finally {
            setTransferSubmitting(false);
        }
    };

    const handleCancelTransfer = async (domainRecordId) => {
        try {
            await cancelDomainTransfer(domainRecordId);
            const data = await listDeployedSites();
            setDeployedSites(data.sites || []);
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    // ── Token request handlers ──
    const loadTokenRequests = async () => {
        try {
            const data = await getMyTokenRequests();
            setTokenRequests(data.requests || []);
            setTokenRequestsLoaded(true);
        } catch { }
    };

    const handleTokenRequest = async () => {
        const websiteCount = parseInt(tokenRequestAmount);
        if (!websiteCount || websiteCount <= 0) return;
        const tokensPerWebsite = 150000;
        const totalTokens = websiteCount * tokensPerWebsite;
        const reason = `${websiteCount} additional website${websiteCount > 1 ? 's' : ''}${tokenRequestReason ? ' — ' + tokenRequestReason : ''}`;
        setTokenRequestSubmitting(true);
        try {
            await requestTokens(totalTokens, reason);
            setTokenRequestModal(false);
            setTokenRequestAmount('1');
            setTokenRequestReason('');
            loadTokenRequests();
            refreshUser();
            showToast('Request submitted! Admin will review it shortly.', 'success');
        } catch (err) {
            showToast(err.message, 'error');
        }
        setTokenRequestSubmitting(false);
    };

    // ── Gallery handlers ──
    const loadGallery = async () => {
        setGalleryLoading(true);
        try {
            const data = await listAllUploads();
            setGalleryImages(data.files || []);
        } catch (e) { console.error('Failed to load gallery:', e); }
        setGalleryLoading(false);
    };

    const handleGalleryUpload = async (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        setGalleryUploading(true);
        for (const file of files) {
            try {
                await uploadFile(file, '', 'image');
            } catch (err) { console.error('Upload failed:', err); }
        }
        await loadGallery();
        setGalleryUploading(false);
        if (galleryFileRef.current) galleryFileRef.current.value = '';
    };

    const handleGalleryDelete = async (filename) => {
        try {
            await deleteUpload(filename);
            setGalleryImages(prev => prev.filter(f => f.filename !== filename));
            setGalleryDeleteConfirm(null);
        } catch (e) { showToast(e.message, 'error'); }
    };

    const handleCopyImageUrl = (url) => {
        const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
        navigator.clipboard.writeText(fullUrl);
        setGalleryCopied(url);
        setTimeout(() => setGalleryCopied(null), 2000);
    };

    // ── Site feature handlers ──
    const handleExportZip = async (siteId, siteName) => {
        setExporting(siteId);
        try {
            const blob = await exportSiteZip(siteId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${siteName || 'site'}.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (e) { showToast(e.message, 'error'); }
        setExporting(null);
    };

    const handleOpenCustomCode = async (siteId) => {
        setCustomCodeModal(siteId);
        try {
            const data = await getCustomCode(siteId);
            setCustomHeadCode(data.head_code || '');
            setCustomBodyCode(data.body_code || '');
        } catch (_) {
            setCustomHeadCode('');
            setCustomBodyCode('');
        }
    };

    const handleSaveCustomCode = async () => {
        if (!customCodeModal) return;
        setCustomCodeSaving(true);
        try {
            await updateCustomCode(customCodeModal, customHeadCode, customBodyCode);
            showToast('Custom code saved! Redeploy to apply changes.', 'success');
            setCustomCodeModal(null);
        } catch (e) { showToast(e.message, 'error'); }
        setCustomCodeSaving(false);
    };

    const handleOpenAnalytics = async (siteId) => {
        setAnalyticsModal(siteId);
        setAnalyticsLoading(true);
        setAnalyticsData(null);
        try {
            const data = await getSiteAnalytics(siteId, 30);
            setAnalyticsData(data);
        } catch (e) { setAnalyticsData({ error: e.message }); }
        setAnalyticsLoading(false);
    };

    // ── Inbox handlers ──
    const loadSubmissions = async () => {
        setSubmissionsLoading(true);
        try {
            const params = {};
            if (inboxSiteFilter) params.siteId = inboxSiteFilter;
            if (inboxReadFilter === 'unread') params.isRead = false;
            if (inboxReadFilter === 'read') params.isRead = true;
            const data = await getFormSubmissions(params.siteId || null, params.isRead ?? null);
            setSubmissions(data.submissions || []);
            setUnreadCount(data.unread_count || 0);
        } catch (e) { console.error('Failed to load submissions:', e); }
        setSubmissionsLoading(false);
    };

    const loadUnreadCount = async () => {
        try {
            const data = await getUnreadCount();
            setUnreadCount(data.unread_count || 0);
        } catch (_) { /* ignore */ }
    };

    const handleExpandSubmission = async (sub) => {
        setExpandedSubmission(expandedSubmission?.id === sub.id ? null : sub);
        if (!sub.is_read) {
            try {
                await markSubmissionRead(sub.id);
                setSubmissions(prev => prev.map(s => s.id === sub.id ? { ...s, is_read: true } : s));
                setUnreadCount(prev => Math.max(0, prev - 1));
            } catch (_) { /* ignore */ }
        }
    };

    const handleDeleteSubmission = async (id) => {
        try {
            await deleteFormSubmission(id);
            setSubmissions(prev => prev.filter(s => s.id !== id));
            setDeleteSubmissionConfirm(null);
            loadUnreadCount();
        } catch (e) { showToast(e.message, 'error'); }
    };

    // ── Domain handlers ──
    const loadDeployedSites = async () => {
        setDomainsLoading(true);
        try {
            const data = await listDeployedSites();
            const sites = (data.sites || []).map(s => {
                // Derive cname_target from URL if backend didn't return it
                if (!s.cname_target && s.url) {
                    try { s.cname_target = new URL(s.url).hostname; } catch (_) { /* ignore */ }
                }
                return s;
            });
            setDeployedSites(sites);
            // Auto-load DNS records and nameservers for connected domains
            for (const site of sites) {
                if (site.domain) {
                    loadDnsRecords(site.id);
                    loadNameservers(site.id);
                }
            }
        } catch (e) { console.error('Failed to load sites:', e); }
        setDomainsLoading(false);
    };

    const loadDnsRecords = async (siteId) => {
        try {
            const data = await listDnsRecords(siteId);
            setDnsRecords(prev => ({ ...prev, [siteId]: data.records || [] }));
        } catch (e) {
            console.error('Failed to load DNS:', e);
            setDnsRecords(prev => ({ ...prev, [siteId]: [] }));
        }
    };

    const loadNameservers = async (siteId) => {
        try {
            const data = await getDnsNameservers(siteId);
            setNameservers(prev => ({ ...prev, [siteId]: data.nameservers || [] }));
        } catch (e) {
            console.error('Failed to load nameservers:', e);
            setNameservers(prev => ({ ...prev, [siteId]: [] }));
        }
    };

    const [connectError, setConnectError] = useState(null);
    const [domainSearchResults, setDomainSearchResults] = useState(null);
    const [connectStep, setConnectStep] = useState(1); // 1=search, 2=results, 3=success
    const [searchLoading, setSearchLoading] = useState(false);
    const [domainSubTab, setDomainSubTab] = useState('sites'); // 'sites' | 'mydomains'
    const [myDomains, setMyDomains] = useState([]);
    const [myDomainsLoading, setMyDomainsLoading] = useState(false);
    const [purchasing, setPurchasing] = useState(false);
    const [purchaseConfirm, setPurchaseConfirm] = useState(null); // { sld, tld, siteId, price }

    // ── Entry-flow modal: "Buy Domain or Build Website" gate ─────────────
    // stage: null | 'domainSearch' | 'domainConfirm' | 'purchasing' | 'domainSuccess'
    // (legacy 'choice' and 'pickOwned' stages were removed — the dashboard
    // home tab CTAs now navigate directly to the right entry point)
    const [entryStage, setEntryStage] = useState(null);
    const [entrySearchInput, setEntrySearchInput] = useState('');
    const [entrySearchResults, setEntrySearchResults] = useState(null);
    const [entrySearchLoading, setEntrySearchLoading] = useState(false);
    const [entrySearchError, setEntrySearchError] = useState(null);
    const [entryPurchaseTarget, setEntryPurchaseTarget] = useState(null); // { sld, tld, price }
    const [entryPurchasedDomain, setEntryPurchasedDomain] = useState(null); // { domain }
    // Prompt typed in the home chat input — preserved across the choice
    // modal so a typed prompt still flows through to the generator.
    const [pendingPrompt, setPendingPrompt] = useState('');

    // Opens the entry-flow modal at the domainSearch stage. Used by the
    // "Buy Domain" CTA on the home tab and the equivalent CTAs in the
    // Domains tab. The legacy 'choice' stage was removed — there's nothing
    // for the user to choose at this point because the home-tab buttons
    // already disambiguated the intent.
    const openEntryFlow = useCallback(() => {
        setEntryStage('domainSearch');
        setEntrySearchInput('');
        setEntrySearchResults(null);
        setEntrySearchError(null);
        setEntryPurchaseTarget(null);
        setEntryPurchasedDomain(null);
    }, []);

    const closeEntryFlow = useCallback(() => {
        setEntryStage(null);
        setEntryPurchaseTarget(null);
        setPendingPrompt('');
    }, []);

    // Derive a human-readable brand name from a domain. "acme-shop.shop" → "Acme Shop"
    const brandFromDomain = (domainStr) => {
        if (!domainStr) return '';
        const sld = String(domainStr).split('.')[0] || '';
        return sld
            .split(/[-_]/)
            .map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase())
            .join(' ');
    };

    const handleEntryUseOwnedDomain = (domainStr) => {
        const brand = brandFromDomain(domainStr);
        const carry = pendingPrompt;
        closeEntryFlow();
        navigate('/generator', {
            state: {
                newSession: true,
                wizardDomain: domainStr,
                wizardBrand: brand,
                ...(carry ? { wizardPrefill: carry } : {}),
            },
        });
    };

    const handleEntryDomainSearch = async (e) => {
        if (e?.preventDefault) e.preventDefault();
        const raw = entrySearchInput.trim();
        if (!raw) return;
        setEntrySearchLoading(true);
        setEntrySearchError(null);
        setEntrySearchResults(null);
        try {
            const parts = raw.includes('.') ? raw.split('.') : [raw];
            const sld = parts[0];
            const baseExts = [
                'com', 'ae', 'net', 'org', 'io',
                'co', 'app', 'shop', 'online', 'store',
                'site', 'tech', 'dev', 'me', 'xyz',
            ];
            const extensions = parts[1]
                ? [parts[1], ...baseExts.filter(x => x !== parts[1])].slice(0, 15)
                : baseExts;
            const data = await searchDomains(sld, extensions);
            setEntrySearchResults(data.results || []);
        } catch (err) {
            setEntrySearchError(err.message || 'Search failed');
        } finally {
            setEntrySearchLoading(false);
        }
    };

    const handleEntryPurchaseConfirm = async () => {
        if (!entryPurchaseTarget) return;
        setEntryStage('purchasing');
        setEntrySearchError(null);
        try {
            // Resilient buy: races the purchase call against polling
            // listUserDomains so we recover from ALB-timeout-induced hangs.
            const result = await purchaseDomainAndWait(
                entryPurchaseTarget.sld, entryPurchaseTarget.tld, null, 1,
            );
            setEntryPurchasedDomain({ domain: result.domain.domain_name });
            // If polling already gave us a fresh list, use it; otherwise refetch.
            if (result.domains && result.domains.length) {
                setMyDomains(result.domains);
            } else {
                loadMyDomains();
            }
            setEntryStage('domainSuccess');
        } catch (err) {
            // Timeout case: don't drop the user back to confirm — show the
            // success screen with a "still processing" note so they don't
            // accidentally retry and double-buy.
            if (err.code === 'PURCHASE_TIMEOUT') {
                setEntryPurchasedDomain({
                    domain: `${entryPurchaseTarget.sld}.${entryPurchaseTarget.tld}`,
                    pending: true,
                });
                loadMyDomains();
                setEntryStage('domainSuccess');
                return;
            }
            setEntrySearchError(err.message || 'Purchase failed');
            setEntryStage('domainConfirm');
        }
    };

    const handleSearchDomain = async () => {
        if (!domainInput.trim()) return;
        setSearchLoading(true);
        setConnectError(null);
        setDomainSearchResults(null);
        try {
            const d = domainInput.trim();
            const parts = d.includes('.') ? d.split('.') : [d];
            const sld = parts[0];
            // 15 extensions so the popup shows a rich list of alternatives.
            // If user typed a specific TLD, surface it first.
            const baseExts = [
                'com', 'ae', 'net', 'org', 'io',
                'co', 'app', 'shop', 'online', 'store',
                'site', 'tech', 'dev', 'me', 'xyz',
            ];
            const extensions = parts[1]
                ? [parts[1], ...baseExts.filter(e => e !== parts[1])].slice(0, 15)
                : baseExts;
            const results = await searchDomains(sld, extensions);
            setDomainSearchResults(results.results || []);
            setConnectStep(2);
        } catch (e) {
            setConnectError(e.message || 'Search failed');
        }
        setSearchLoading(false);
    };

    const handleConnectDomain = async (domainName) => {
        if (!connectModal) return;
        const domain = domainName || domainInput.trim();
        if (!domain) return;
        setConnecting(true);
        setConnectError(null);
        try {
            // Resilient connect: races the POST with getDomainStatus polling so
            // an ALB-60s-timeout-induced fetch hang can't strand the spinner.
            const result = await connectDomainAndWait(connectModal, domain);
            setConnectResult(result);
            setConnectStep(3);
            loadDeployedSites();
        } catch (e) {
            const msg = e.message || 'Failed to connect domain';
            if (e.code === 'CONNECT_TIMEOUT') {
                // Soft success — backend is still working in the background.
                // Refresh lists and advance the UI instead of showing an error.
                showToast(msg, 'info', 8000);
                loadDeployedSites();
                loadMyDomains();
                setConnectModal(null);
            } else if (msg.includes('not registered')) {
                setConnectError('not_registered');
                handleSearchDomain();
            } else {
                setConnectError(msg);
            }
        }
        setConnecting(false);
    };

    const loadMyDomains = async () => {
        setMyDomainsLoading(true);
        try {
            const data = await listUserDomains();
            setMyDomains(data.domains || data || []);
        } catch { /* ignore */ }
        setMyDomainsLoading(false);
    };

    const handleConnectOwnedDomain = async (domainName) => {
        if (!connectModal) return;
        setConnectingOwned(domainName);
        setConnectError(null);
        try {
            // Resilient connect: races the POST with getDomainStatus polling so
            // an ALB-60s-timeout-induced fetch hang can't strand the spinner.
            const result = await connectDomainAndWait(connectModal, domainName);
            setConnectResult(result);
            setConnectStep(3);
            loadDeployedSites();
        } catch (e) {
            if (e.code === 'CONNECT_TIMEOUT') {
                // Soft success — backend is still working in the background.
                showToast(e.message, 'info', 8000);
                loadDeployedSites();
                loadMyDomains();
                setConnectModal(null);
            } else {
                setConnectError(e.message || 'Failed to connect domain');
            }
        }
        setConnectingOwned(null);
    };

    const handleQuickPurchase = async (sld, tld, siteId) => {
        setPurchasing(true);
        try {
            // Resilient buy: races purchase API with listUserDomains polling
            // so an ALB-timeout-induced fetch hang doesn't strand the spinner.
            await purchaseDomainAndWait(sld, tld, siteId, 1);
            setPurchaseConfirm(null);
            setConnectModal(null);
            setConnectError(null);
            setDomainSearchResults(null);
            loadDeployedSites();
            loadMyDomains();
            showToast(`${sld}.${tld} purchased and connected successfully!`, 'success');
        } catch (e) {
            // Timeout case: domain is being registered in the background.
            // Don't surface as a hard error — give the user a useful nudge.
            if (e.code === 'PURCHASE_TIMEOUT') {
                setPurchaseConfirm(null);
                setConnectModal(null);
                loadDeployedSites();
                loadMyDomains();
                showToast(`${sld}.${tld} is registering in the background. Check My Domains in a minute.`, 'info', 8000);
            } else {
                const msg = typeof e.message === 'string' ? e.message : JSON.stringify(e.message);
                showToast(msg || 'Purchase failed', 'error');
            }
        }
        setPurchasing(false);
    };

    const handleDisconnect = async (siteId) => {
        try {
            await disconnectDomain(siteId);
            setDisconnectConfirm(null);
            loadDeployedSites();
        } catch (e) { showToast(e.message || 'Failed to disconnect', 'error'); }
    };

    const handleAddRecord = async () => {
        if (!addRecordModal || !newRecord.name || !newRecord.value) return;
        setAddingRecord(true);
        try {
            await addDnsRecord(addRecordModal, newRecord);
            setAddRecordModal(null);
            setNewRecord({ name: '', type: 'A', value: '', ttl: 300 });
            loadDnsRecords(addRecordModal);
        } catch (e) { showToast(e.message || 'Failed to add record', 'error'); }
        setAddingRecord(false);
    };

    const [deleteRecordConfirm, setDeleteRecordConfirm] = useState(null); // { siteId, record }

    const handleDeleteRecord = async (siteId, record) => {
        try {
            await deleteDnsRecord(siteId, { name: record.name, type: record.type, value: record.value });
            loadDnsRecords(siteId);
        } catch (e) { showToast(e.message || 'Failed to delete record', 'error'); }
    };

    const handleDeleteSite = async (siteId) => {
        try {
            await deleteDeployedSite(siteId);
            setDeleteSiteConfirm(null);
            loadDeployedSites();
        } catch (e) { showToast(e.message || 'Failed to delete site', 'error'); }
    };

    const statusColor = (s) => {
        if (s === 'active' || s === 'published') return 'green';
        if (s === 'pending' || s === 'pending_validation' || s === 'pending_deployment') return 'yellow';
        if (s === 'failed' || s === 'offline') return 'red';
        return 'gray';
    };

    // Load owned domains when the home tab activates so we know whether to
    // show the "Use Existing Domain" button (only shown if at least one
    // domain is parked / not connected to any site).
    useEffect(() => {
        if (activeTab === 'home') {
            loadMyDomains();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    useEffect(() => {
        if (activeTab === 'domains') {
            loadDeployedSites();
            // Poll domain status every 30s for sites with pending statuses
            domainPollRef.current = setInterval(async () => {
                try {
                    const data = await listDeployedSites();
                    const sites = data.sites || [];
                    setDeployedSites(sites);
                    // For any site with pending status, poll domain-status to trigger Phase 2
                    for (const site of sites) {
                        if (site.domain && (site.domain_status === 'pending_validation' || site.domain_status === 'pending_deployment' || site.domain_status === 'creating_cdn')) {
                            try { await getDomainStatus(site.id); } catch (_) { }
                        }
                    }
                } catch (_) { }
            }, 30000);
        }
        return () => { if (domainPollRef.current) clearInterval(domainPollRef.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    // Fetch unread count on mount (for inbox badge)
    useEffect(() => { loadUnreadCount(); }, []);

    // Load tab content on activation.
    useEffect(() => {
        if (activeTab === 'projects') {
            loadProjects();
        } else if (activeTab === 'templates') {
            loadTemplates();
        } else if (activeTab === 'domains') {
            // Unified domains view loads BOTH owned domains and deployed sites
            // since both are rendered together (no more sub-tabs).
            if (myDomains.length === 0) loadMyDomains();
        } else if (activeTab === 'inbox') {
            loadSubmissions();
            if (deployedSites.length === 0) loadDeployedSites();
        } else if (activeTab === 'gallery') {
            loadGallery();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, inboxSiteFilter, inboxReadFilter]);

    const loadProjects = async () => {
        setProjectsLoading(true);
        try {
            const data = await listProjects();
            setProjects(data.projects || []);
        } catch (err) {
            console.error('Failed to load projects:', err);
        } finally {
            setProjectsLoading(false);
        }
    };

    const loadTemplates = async () => {
        if (templates.length > 0) return; // already loaded
        setTemplatesLoading(true);
        try {
            const data = await listTemplateCatalog();
            setTemplates(data.templates || []);
            // Load previews for all templates
            for (const t of (data.templates || [])) {
                getTemplateFull(t.id).then(full => {
                    setTemplatePreviews(prev => ({ ...prev, [t.id]: full }));
                }).catch(() => { });
            }
        } catch (err) {
            console.error('Failed to load templates:', err);
        } finally {
            setTemplatesLoading(false);
        }
    };

    const handleUseTemplate = async (templateId) => {
        try {
            const data = await getTemplateFull(templateId);
            navigate('/generator', {
                state: {
                    projectData: {
                        name: data.name,
                        html: data.html,
                        css: data.css,
                        js: data.js || '',
                        isTemplate: true,
                    },
                },
            });
        } catch (err) {
            console.error('Failed to load template:', err);
        }
    };

    const handleOpenProject = async (projectId) => {
        try {
            const data = await getProject(projectId);
            navigate('/generator', { state: { projectData: data } });
        } catch (err) {
            console.error('Failed to open project:', err);
        }
    };

    const handleDeleteProject = async (projectId) => {
        try {
            await deleteProject(projectId);
            setProjects(prev => prev.filter(p => p.id !== projectId));
            setDeleteConfirm(null);
        } catch (err) {
            console.error('Failed to delete project:', err);
        }
    };

    // Auto-resize textarea
    // Close user menu on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
                setUserMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);


    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    const impersonating = sessionStorage.getItem('impersonating') || localStorage.getItem('impersonating');
    const impersonateInfo = impersonating ? JSON.parse(impersonating) : null;

    const stopImpersonating = () => {
        const adminToken = sessionStorage.getItem('admin_token_backup') || localStorage.getItem('admin_token_backup');
        if (adminToken) {
            sessionStorage.setItem('token', adminToken);
            sessionStorage.removeItem('admin_token_backup');
            localStorage.removeItem('admin_token_backup');
        }
        sessionStorage.removeItem('impersonating');
        localStorage.removeItem('impersonating');
        window.location.href = '/admin';
    };

    return (
        <div className={`dashboard${impersonateInfo ? ' impersonating' : ''}`}>
            {/* Toast notification */}
            {toast && (
                <div style={{
                    position: 'fixed', top: 24, right: 24, zIndex: 99999,
                    background: toast.type === 'error' ? '#ef4444' : toast.type === 'success' ? '#10b981' : '#3b82f6',
                    color: '#fff', padding: '12px 20px', borderRadius: 10,
                    boxShadow: '0 8px 24px rgba(0,0,0,0.2)', fontSize: 14, fontWeight: 500,
                    maxWidth: 380, animation: 'fadeInDown 0.3s ease',
                    display: 'flex', alignItems: 'center', gap: 8,
                }} onClick={() => setToast(null)}>
                    <span>{toast.type === 'error' ? '✕' : toast.type === 'success' ? '✓' : 'ℹ'}</span>
                    <span>{toast.message}</span>
                </div>
            )}
            {impersonateInfo && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
                    background: '#f59e0b', color: '#000', padding: '8px 16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
                    fontSize: 14, fontWeight: 600,
                }}>
                    <span>Viewing as: {impersonateInfo.email} (read-only, {impersonateInfo.expiresIn}min)</span>
                    <button onClick={stopImpersonating} style={{
                        background: '#000', color: '#fff', border: 'none', borderRadius: 4,
                        padding: '4px 12px', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                    }}>
                        Stop Impersonating
                    </button>
                </div>
            )}
            {/* Sidebar */}
            <aside className={`dash-sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
                <div className="dash-sidebar-top">
                    <div className="dash-sidebar-header">
                        <div className="dash-logo">
                            <img src="/mfz-logo.webp" alt="Web AI" style={{ height: 38, maxWidth: 150, objectFit: 'contain' }} />
                        </div>
                        <button
                            className="dash-sidebar-toggle"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            aria-label="Toggle sidebar"
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                {sidebarOpen ? (
                                    <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="15" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
                                ) : (
                                    <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
                                )}
                            </svg>
                        </button>
                    </div>

                    <button
                        className="dash-new-chat"
                        onClick={() => navigate('/generator', { state: { newSession: true } })}
                    >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        {sidebarOpen && <span>New Design</span>}
                    </button>

                    <nav className="dash-nav">
                        {/* Domains tab — moved to top so users can manage domain-first */}
                        <button
                            className={`dash-nav-item ${activeTab === 'domains' ? 'active' : ''}`}
                            onClick={() => setActiveTab('domains')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                            </svg>
                            {sidebarOpen && <span>Domains</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'home' ? 'active' : ''}`}
                            onClick={() => { setActiveTab('home'); refreshUser(); }}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" /><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" /><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" /><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
                            </svg>
                            {sidebarOpen && <span>Website Builder</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'projects' ? 'active' : ''}`}
                            onClick={() => setActiveTab('projects')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                            </svg>
                            {sidebarOpen && <span>Projects</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'templates' ? 'active' : ''}`}
                            onClick={() => setActiveTab('templates')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
                            </svg>
                            {sidebarOpen && <span>Templates</span>}
                        </button>
                        {/* Inbox promoted up the sidebar — high frequency for active users */}
                        <button
                            className={`dash-nav-item ${activeTab === 'inbox' ? 'active' : ''}`}
                            onClick={() => { setActiveTab('inbox'); window.location.hash = 'inbox'; }}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" /><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
                            </svg>
                            {sidebarOpen && (
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    Inbox
                                    {unreadCount > 0 && <span style={{ fontSize: '0.65rem', background: '#ef4444', color: 'white', padding: '1px 6px', borderRadius: 10, fontWeight: 700, minWidth: 18, textAlign: 'center' }}>{unreadCount}</span>}
                                </span>
                            )}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'gallery' ? 'active' : ''}`}
                            onClick={() => setActiveTab('gallery')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
                            </svg>
                            {sidebarOpen && <span>Gallery</span>}
                        </button>
                        {user?.is_admin && (
                            <button
                                className="dash-nav-item"
                                onClick={() => navigate('/admin')}
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                                    <circle cx="12" cy="12" r="3" />
                                </svg>
                                {sidebarOpen && <span>Admin</span>}
                            </button>
                        )}
                    </nav>
                </div>

                {/* User profile at bottom */}
                <div className="dash-sidebar-bottom" ref={userMenuRef}>
                    {userMenuOpen && (
                        <div className="dash-user-menu">
                            <div className="dash-user-menu-header">
                                <span className="dash-user-menu-name">{user?.full_name}</span>
                                <span className="dash-user-menu-email">{user?.email}</span>
                            </div>
                            <div className="dash-user-menu-divider" />
                            <button className="dash-user-menu-item" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                                </svg>
                                Generator
                            </button>
                            <div className="dash-user-menu-divider" />
                            <button className="dash-user-menu-item danger" onClick={handleLogout}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Log out
                            </button>
                        </div>
                    )}
                    <button
                        className="dash-user-profile"
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                    >
                        <div className="dash-avatar">
                            {firstName.charAt(0).toUpperCase()}
                        </div>
                        {sidebarOpen && (
                            <div className="dash-user-info">
                                <span className="dash-user-name">{user?.full_name}</span>
                                <span className="dash-user-company">{user?.company_name}</span>
                            </div>
                        )}
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className={`dash-main ${activeTab === 'home' ? 'dash-main-gradient' : ''}`}>
                {/* Announcements */}
                {visibleAnnouncements.length > 0 && (
                    <div style={{ padding: '12px 24px 0', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {visibleAnnouncements.map(a => {
                            const colors = { info: '#818cf8', warning: '#fbbf24', maintenance: '#f59e0b', success: '#34d399' };
                            const color = colors[a.type] || colors.info;
                            return (
                                <div key={a.id} style={{
                                    background: `${color}15`, border: `1px solid ${color}40`, borderRadius: 8,
                                    padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                                }}>
                                    <div>
                                        <strong style={{ color, fontSize: 13 }}>{a.title}</strong>
                                        <span style={{ color: '#e4e4e7', fontSize: 13, marginLeft: 8 }}>{a.message}</span>
                                    </div>
                                    <button onClick={() => dismissAnnouncement(a.id)} style={{
                                        background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: 16, padding: '0 4px',
                                    }}>×</button>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* ── Home Tab ────────────────────────────────────────── */}
                {activeTab === 'home' && (
                    <div className="dash-content">
                        <div className="dash-greeting">
                            <h1 className="dash-greeting-text">
                                {getGreeting()}, {firstName}
                            </h1>
                            <p className="dash-greeting-sub">
                                Pick how you'd like to start
                            </p>
                            {(() => {
                                const used = user?.generation_count || 0;
                                const max = user?.max_generations || 2;
                                const remaining = Math.max(0, max - used);
                                const isExhausted = remaining === 0;
                                const hasPending = tokenRequests.some(r => r.status === 'pending');
                                return (
                                    <div style={{
                                        marginTop: 20, maxWidth: 380, marginLeft: 'auto', marginRight: 'auto',
                                        display: 'flex', alignItems: 'center', gap: 14,
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid rgba(255,255,255,0.06)',
                                        borderRadius: 12, padding: '12px 18px',
                                    }}>
                                        <span style={{
                                            fontSize: 20, fontWeight: 700, minWidth: 28, textAlign: 'center',
                                            color: isExhausted ? '#6b7280' : '#34d399',
                                        }}>
                                            {remaining}
                                        </span>
                                        <span style={{ fontSize: 13, color: '#9ca3af', flex: 1 }}>
                                            {isExhausted
                                                ? 'No websites remaining'
                                                : <>website{remaining !== 1 ? 's' : ''} remaining</>}
                                        </span>
                                        {hasPending ? (
                                            <span style={{ fontSize: 11, color: '#fbbf24', whiteSpace: 'nowrap' }}>Pending</span>
                                        ) : (
                                            <button
                                                onClick={() => { setTokenRequestModal(true); if (!tokenRequestsLoaded) loadTokenRequests(); }}
                                                style={{
                                                    background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.25)',
                                                    color: '#34d399', padding: '5px 12px', borderRadius: 6,
                                                    fontSize: 11, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap',
                                                }}
                                            >
                                                Request More
                                            </button>
                                        )}
                                    </div>
                                );
                            })()}
                        </div>

                        {/* ── Action Buttons (replaces the legacy chatbox) ─── */}
                        {/*
                            Three CTAs:
                              1. Buy Domain — opens entry-flow modal at the
                                 domain search stage. After purchase the
                                 existing flow runs the wizard and auto-
                                 connects the new domain on deploy.
                              2. Create Website — straight to /generator
                                 (the wizard) with no domain attached.
                              3. Use Existing Domain — only shown if the
                                 user owns at least one parked domain
                                 (one without a site_id). Opens an inline
                                 popover that lists those parked domains;
                                 picking one navigates to /generator with
                                 wizardDomain set so the wizard auto-attaches
                                 it after deploy.
                        */}
                        {(() => {
                            const parkedDomains = (myDomains || []).filter(d => !d.site_id);
                            const hasParked = parkedDomains.length > 0;
                            return (
                                <>
                                    {/* Keyframes for the "Create Website" pulsing glow.
                                    Inlined here (instead of in App.css) so the
                                    animation lives next to the only consumer and
                                    can't get out of sync if the file is split. */}
                                    <style>{`
                                    @keyframes meydanCreateGlow {
                                        0%, 100% {
                                            border-color: rgba(129, 140, 248, 0.55);
                                            box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.25),
                                                        0 0 18px rgba(99, 102, 241, 0.28),
                                                        0 0 36px rgba(99, 102, 241, 0.12);
                                        }
                                        50% {
                                            border-color: rgba(165, 180, 252, 0.85);
                                            box-shadow: 0 0 0 1px rgba(165, 180, 252, 0.45),
                                                        0 0 28px rgba(99, 102, 241, 0.5),
                                                        0 0 60px rgba(99, 102, 241, 0.22);
                                        }
                                    }
                                    .meydan-create-website-btn {
                                        border: 1.5px solid rgba(129, 140, 248, 0.55) !important;
                                        animation: meydanCreateGlow 2.4s ease-in-out infinite;
                                    }
                                    .meydan-create-website-btn:hover {
                                        animation-play-state: paused;
                                        border-color: rgba(165, 180, 252, 1) !important;
                                        box-shadow: 0 0 0 1px rgba(165, 180, 252, 0.6),
                                                    0 0 32px rgba(99, 102, 241, 0.55),
                                                    0 0 70px rgba(99, 102, 241, 0.28) !important;
                                    }
                                `}</style>
                                    <div className="dash-action-buttons" style={{
                                        marginTop: 36, display: 'flex', gap: 16, flexWrap: 'wrap',
                                        justifyContent: 'center', maxWidth: 880, marginLeft: 'auto', marginRight: 'auto',
                                    }}>
                                        {/* Buy Domain */}
                                        <button
                                            type="button"
                                            onClick={() => { openEntryFlow(); }}
                                            style={{
                                                flex: '1 1 240px', minHeight: 140, padding: '24px 20px',
                                                background: 'linear-gradient(135deg, rgba(52,211,153,0.08), rgba(52,211,153,0.02))',
                                                border: '1px solid rgba(52,211,153,0.25)',
                                                borderRadius: 14, color: '#e5e7eb', cursor: 'pointer',
                                                display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                                                gap: 10, textAlign: 'left',
                                                transition: 'transform 0.2s, border-color 0.2s, background 0.2s',
                                            }}
                                            onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'rgba(52,211,153,0.5)'; }}
                                            onMouseOut={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'rgba(52,211,153,0.25)'; }}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%' }}>
                                                <div style={{
                                                    width: 44, height: 44, borderRadius: 10,
                                                    background: 'rgba(52,211,153,0.15)', display: 'flex',
                                                    alignItems: 'center', justifyContent: 'center',
                                                }}>
                                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                                    </svg>
                                                </div>
                                                <strong style={{ fontSize: 17, color: '#f3f4f6' }}>Buy Domain</strong>
                                            </div>
                                            <span style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5 }}>
                                                Register your domain.
                                            </span>
                                        </button>

                                        {/* Create Website — visually highlighted as the
                                        "default" CTA via a pulsing glow border defined
                                        in the <style> block above. The button itself
                                        is NOT actually default in any keyboard sense
                                        (Enter doesn't fire it, no autoFocus); the glow
                                        is purely visual. */}
                                        <button
                                            type="button"
                                            className="meydan-create-website-btn"
                                            onClick={() => navigate('/generator', { state: { newSession: true } })}
                                            style={{
                                                flex: '1 1 240px', minHeight: 140, padding: '24px 20px',
                                                background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(99,102,241,0.04))',
                                                borderRadius: 14, color: '#e5e7eb', cursor: 'pointer',
                                                display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                                                gap: 10, textAlign: 'left',
                                                transition: 'transform 0.2s, background 0.2s',
                                            }}
                                            onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; }}
                                            onMouseOut={e => { e.currentTarget.style.transform = 'none'; }}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%' }}>
                                                <div style={{
                                                    width: 44, height: 44, borderRadius: 10,
                                                    background: 'rgba(99,102,241,0.15)', display: 'flex',
                                                    alignItems: 'center', justifyContent: 'center',
                                                }}>
                                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" /><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" /><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" /><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
                                                    </svg>
                                                </div>
                                                <strong style={{ fontSize: 17, color: '#f3f4f6' }}>Create Website</strong>
                                            </div>
                                            <span style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5 }}>
                                                Generate your website with AI now, Associate the domain later.
                                            </span>
                                        </button>

                                        {/* Use Existing Domain — only if user has parked domains */}
                                        {hasParked && (
                                            <div style={{ flex: '1 1 240px', minHeight: 140, position: 'relative' }}>
                                                <button
                                                    type="button"
                                                    onClick={() => setExistingDomainPickerOpen(v => !v)}
                                                    style={{
                                                        width: '100%', minHeight: 140, padding: '24px 20px',
                                                        background: 'linear-gradient(135deg, rgba(251,191,36,0.08), rgba(251,191,36,0.02))',
                                                        border: '1px solid rgba(251,191,36,0.25)',
                                                        borderRadius: 14, color: '#e5e7eb', cursor: 'pointer',
                                                        display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                                                        gap: 10, textAlign: 'left',
                                                        transition: 'transform 0.2s, border-color 0.2s, background 0.2s',
                                                    }}
                                                    onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'rgba(251,191,36,0.5)'; }}
                                                    onMouseOut={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'rgba(251,191,36,0.25)'; }}
                                                >
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%' }}>
                                                        <div style={{
                                                            width: 44, height: 44, borderRadius: 10,
                                                            background: 'rgba(251,191,36,0.15)', display: 'flex',
                                                            alignItems: 'center', justifyContent: 'center',
                                                        }}>
                                                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                <rect x="2" y="3" width="20" height="14" rx="2" ry="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
                                                            </svg>
                                                        </div>
                                                        <strong style={{ fontSize: 17, color: '#f3f4f6' }}>
                                                            Use Existing Domain
                                                            <span style={{ marginLeft: 8, fontSize: 12, color: '#fbbf24', fontWeight: 500 }}>
                                                                ({parkedDomains.length})
                                                            </span>
                                                        </strong>
                                                    </div>
                                                    <span style={{ fontSize: 13, color: '#9ca3af', lineHeight: 1.5 }}>
                                                        Build a new website using one of your parked domains. Auto-connects after deploy.
                                                    </span>
                                                </button>

                                                {/* Parked-domain popover — opens below the button on click */}
                                                {existingDomainPickerOpen && (
                                                    <>
                                                        {/* Click-outside catcher */}
                                                        <button
                                                            type="button"
                                                            aria-label="Close domain picker"
                                                            onClick={() => setExistingDomainPickerOpen(false)}
                                                            style={{
                                                                position: 'fixed', inset: 0, background: 'transparent',
                                                                border: 'none', cursor: 'default', zIndex: 998,
                                                            }}
                                                        />
                                                        <div style={{
                                                            position: 'absolute', top: 'calc(100% + 8px)', left: 0, right: 0,
                                                            background: '#18181b', border: '1px solid #27272a',
                                                            borderRadius: 12, boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
                                                            zIndex: 999, maxHeight: 320, overflowY: 'auto', padding: 8,
                                                        }}>
                                                            <div style={{
                                                                fontSize: 11, fontWeight: 600, color: '#71717a',
                                                                textTransform: 'uppercase', letterSpacing: 0.5,
                                                                padding: '8px 10px 6px',
                                                            }}>
                                                                Parked domains — pick one
                                                            </div>
                                                            {parkedDomains.map(d => (
                                                                <button
                                                                    key={d.id || d.domain_name}
                                                                    type="button"
                                                                    onClick={() => {
                                                                        setExistingDomainPickerOpen(false);
                                                                        handleEntryUseOwnedDomain(d.domain_name);
                                                                    }}
                                                                    style={{
                                                                        display: 'block', width: '100%', textAlign: 'left',
                                                                        padding: '10px 12px', background: 'transparent',
                                                                        border: 'none', color: '#e5e7eb', cursor: 'pointer',
                                                                        borderRadius: 6, fontSize: 14,
                                                                        transition: 'background 0.15s',
                                                                    }}
                                                                    onMouseOver={e => { e.currentTarget.style.background = '#27272a'; }}
                                                                    onMouseOut={e => { e.currentTarget.style.background = 'transparent'; }}
                                                                >
                                                                    <strong>{d.domain_name}</strong>
                                                                    {d.status && d.status !== 'active' && (
                                                                        <span style={{ marginLeft: 8, fontSize: 11, color: '#fbbf24' }}>
                                                                            {d.status}
                                                                        </span>
                                                                    )}
                                                                </button>
                                                            ))}
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </>
                            );
                        })()}
                    </div>
                )}

                {/* ── Projects Tab ────────────────────────────────────── */}
                {activeTab === 'projects' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <h1 className="dash-domain-title">My Projects</h1>
                            <button className="dash-domain-add-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                </svg>
                                New Project
                            </button>
                        </div>

                        {projectsLoading ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
                                Loading projects...
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="dash-projects-empty">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#ccc' }}>
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                                </svg>
                                <h3>No projects yet</h3>
                                <p>Generate a website and save it to see it here</p>
                                <button className="dash-domain-add-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                    Create Your First Website
                                </button>
                            </div>
                        ) : (
                            <div className="dash-projects-grid">
                                {projects.map(project => (
                                    <div key={project.id} className="dash-project-card" onClick={() => handleOpenProject(project.id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOpenProject(project.id); }} role="button" tabIndex={0}>
                                        <div className="dash-project-thumb">
                                            {project.html ? (
                                                <iframe
                                                    title={project.name}
                                                    srcDoc={buildSrcDoc(project.css, project.html)}
                                                    sandbox="allow-same-origin allow-scripts"
                                                    scrolling="no"
                                                    className="dash-project-iframe"
                                                />
                                            ) : (
                                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#86EFCB' }}>
                                                    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                                                </svg>
                                            )}
                                        </div>
                                        <div className="dash-project-body">
                                            <h4 className="dash-project-name">{project.name}</h4>
                                            <div className="dash-project-meta">
                                                <span>v{project.current_version}</span>
                                                <span>{formatDate(project.updated_at)}</span>
                                            </div>
                                        </div>
                                        <div className="dash-project-actions" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                                            <button className="dash-project-open" onClick={() => handleOpenProject(project.id)}>Open</button>
                                            <button className="dash-project-delete" onClick={() => setDeleteConfirm(project.id)}>
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Delete confirmation */}
                        {deleteConfirm && (
                            <div className="dash-domain-modal-overlay" onClick={() => setDeleteConfirm(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setDeleteConfirm(null); }} role="button" tabIndex={0}>
                                <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                                    <h3>Delete Project</h3>
                                    <p>Are you sure? This will delete all versions and cannot be undone.</p>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setDeleteConfirm(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDeleteProject(deleteConfirm)}>Delete</button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Templates Tab ──────────────────────────────────── */}
                {/* ── Templates Tab ──────────────────────────────────── */}
                {activeTab === 'templates' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <div>
                                <h1 className="dash-domain-title">Website Templates</h1>
                                <p className="dash-domain-subtitle">Hand-crafted designs you can use as a starting point — edit them inline, chat with AI, or use the visual editor.</p>
                            </div>
                        </div>

                        {templatesLoading ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
                                Loading templates...
                            </div>
                        ) : templates.length === 0 ? (
                            <div className="dsite-empty">
                                <div className="dsite-empty-icon">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg>
                                </div>
                                <h3>No templates available</h3>
                                <p>Something went wrong loading the templates. Try refreshing.</p>
                            </div>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
                                {templates.map(template => {
                                    const preview = templatePreviews[template.id];
                                    return (
                                        <div
                                            key={template.id}
                                            style={{
                                                background: '#18181b',
                                                border: '1px solid #27272a',
                                                borderRadius: 14,
                                                overflow: 'hidden',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                transition: 'transform 0.2s, border-color 0.2s',
                                            }}
                                            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.borderColor = '#52525b'; }}
                                            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = '#27272a'; }}
                                        >
                                            {/* Thumbnail iframe — scaled down with pointer-events: none so clicks don't escape */}
                                            <button
                                                type="button"
                                                onClick={() => setPreviewModal(template.id)}
                                                style={{ background: '#0f0f1a', height: 260, position: 'relative', overflow: 'hidden', cursor: 'pointer', border: 'none', padding: 0, width: '100%' }}
                                            >
                                                {preview ? (
                                                    <iframe
                                                        title={template.name}
                                                        srcDoc={`<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=1400,initial-scale=1"><style>body{margin:0;overflow:hidden;pointer-events:none}${preview.css || ''}</style></head><body>${preview.html || ''}</body></html>`}
                                                        sandbox="allow-same-origin"
                                                        scrolling="no"
                                                        style={{
                                                            width: '1400px',
                                                            height: '900px',
                                                            border: 0,
                                                            transform: 'scale(0.25)',
                                                            transformOrigin: 'top left',
                                                            pointerEvents: 'none',
                                                        }}
                                                    />
                                                ) : (
                                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#52525b', fontSize: 13 }}>
                                                        Loading preview...
                                                    </div>
                                                )}
                                                <div style={{ position: 'absolute', top: 12, right: 12, background: 'rgba(0,0,0,0.6)', color: 'white', fontSize: 11, padding: '4px 10px', borderRadius: 999, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.4, backdropFilter: 'blur(6px)' }}>
                                                    {template.category}
                                                </div>
                                            </button>
                                            <div style={{ padding: '18px 20px 20px' }}>
                                                <h3 style={{ margin: '0 0 6px', fontSize: 17, fontWeight: 700, color: '#f3f4f6' }}>{template.name}</h3>
                                                <p style={{ margin: '0 0 16px', fontSize: 13, color: '#4B5563', lineHeight: 1.5, minHeight: 38 }}>{template.description}</p>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    <button
                                                        onClick={() => setPreviewModal(template.id)}
                                                        style={{ flex: 1, background: '#FFFFFF', border: '1px solid rgba(17,24,39,0.12)', color: '#0A0A0A', padding: '9px 14px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                                                    >
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                                                        Preview
                                                    </button>
                                                    <button
                                                        onClick={() => handleUseTemplate(template.id)}
                                                        style={{ flex: 1, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: 'white', padding: '9px 14px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                                                    >
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                                        Use Template
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Full-screen preview modal */}
                        {previewModal && (
                            <div
                                style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', flexDirection: 'column' }}
                                onClick={() => setPreviewModal(null)}
                                onKeyDown={(e) => { if (e.key === 'Escape') setPreviewModal(null); }}
                                role="button"
                                tabIndex={0}
                            >
                                <div
                                    onClick={e => e.stopPropagation()}
                                    onKeyDown={e => e.stopPropagation()}
                                    role="presentation"
                                    style={{ background: '#0f0f1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 24px', borderBottom: '1px solid #27272a' }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <button
                                            onClick={() => setPreviewModal(null)}
                                            style={{ background: '#FFFFFF', border: '1px solid rgba(17,24,39,0.12)', color: '#0A0A0A', padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
                                        >
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
                                            Back
                                        </button>
                                        <div style={{ color: '#0A0A0A', fontSize: 16, fontWeight: 700 }}>{templates.find(t => t.id === previewModal)?.name}</div>
                                        <span style={{ fontSize: 11, color: '#4B5563', background: 'rgba(17,24,39,0.06)', padding: '3px 10px', borderRadius: 999, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.4 }}>{templates.find(t => t.id === previewModal)?.category}</span>
                                    </div>
                                    <button
                                        onClick={() => { setPreviewModal(null); handleUseTemplate(previewModal); }}
                                        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: 'white', padding: '10px 22px', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8 }}
                                    >
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                        Use This Template
                                    </button>
                                </div>
                                <div style={{ flex: 1, background: '#fff', overflow: 'hidden' }}>
                                    {templatePreviews[previewModal] ? (
                                        <iframe
                                            title="Template Preview"
                                            srcDoc={buildSrcDoc(templatePreviews[previewModal].css, templatePreviews[previewModal].html)}
                                            sandbox="allow-same-origin allow-scripts"
                                            style={{ width: '100%', height: '100%', border: 0, display: 'block' }}
                                        />
                                    ) : (
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#52525b' }}>Loading preview...</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Domains Tab ─────────────────────────────────────── */}
                {activeTab === 'domains' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <div>
                                <h1 className="dash-domain-title">Domains & Sites</h1>
                                <p className="dash-domain-subtitle">Your purchased domains and the sites connected to them — all in one place.</p>
                            </div>
                            <button
                                className="dash-domain-add-btn"
                                onClick={() => { openEntryFlow(); }}
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                </svg>
                                Buy domain
                            </button>
                        </div>

                        {/* ─── My Domains section (always visible) ─── */}
                        <div style={{ marginBottom: 32 }}>
                            <h2 style={{ fontSize: 14, color: '#a1a1aa', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600, margin: '0 0 12px' }}>
                                My Domains {myDomains.length > 0 && <span style={{ color: '#52525b', fontWeight: 400 }}>({myDomains.length})</span>}
                            </h2>
                            {myDomainsLoading ? (
                                <div style={{ padding: 24, textAlign: 'center', color: '#71717a', fontSize: 13 }}>Loading domains…</div>
                            ) : myDomains.length === 0 ? (
                                <div style={{ background: '#0f172a', border: '1px dashed #27272a', borderRadius: 12, padding: '24px 20px', textAlign: 'center' }}>
                                    <p style={{ margin: '0 0 12px', fontSize: 13, color: '#9ca3af' }}>You don't own any domains yet.</p>
                                    <button
                                        className="dsite-cta-btn"
                                        onClick={() => { openEntryFlow(); }}
                                        style={{ display: 'inline-flex' }}
                                    >
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                                        Buy your first domain
                                    </button>
                                </div>
                            ) : (
                                <div style={{ display: 'grid', gap: 12 }}>
                                    {myDomains.map(d => (
                                        <div key={d.id} style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 12, padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                                            <div style={{ flex: 1, minWidth: 220 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                                                    <strong style={{ color: '#f3f4f6', fontSize: 15 }}>{d.domain_name}</strong>
                                                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, fontWeight: 500, background: d.status === 'active' ? 'rgba(34,197,94,0.12)' : 'rgba(251,191,36,0.12)', color: d.status === 'active' ? '#22c55e' : '#fbbf24' }}>
                                                        {d.status || 'pending'}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: 13, color: '#71717a', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                                                    <span>{d.site_id ? <>Connected to <strong style={{ color: '#a1a1aa' }}>{d.site_name || 'a site'}</strong></> : <span style={{ color: '#fbbf24' }}>Not connected</span>}</span>
                                                    {d.expiry_date && <span>Expires {new Date(d.expiry_date).toLocaleDateString()}</span>}
                                                    {d.ssl_status && <span>SSL: {d.ssl_status}</span>}
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', gap: 8 }}>
                                                {!d.site_id && deployedSites.length > 0 && (
                                                    <select onChange={e => { if (e.target.value) { handleConnectOwnedDomain(d.domain_name); } }} style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #374151', background: '#1f2937', color: '#e5e7eb', fontSize: 12 }}>
                                                        <option value="">Connect to site…</option>
                                                        {deployedSites.map(s => <option key={s.id} value={s.id}>{s.name || s.id}</option>)}
                                                    </select>
                                                )}
                                                {!d.site_id && deployedSites.length === 0 && (
                                                    <span style={{ fontSize: 12, color: '#6b7280' }}>Build a site to connect</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* ─── Deployed Sites section ─── */}
                        <h2 style={{ fontSize: 14, color: '#a1a1aa', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600, margin: '0 0 12px' }}>
                            Deployed Sites {deployedSites.length > 0 && <span style={{ color: '#52525b', fontWeight: 400 }}>({deployedSites.length})</span>}
                        </h2>
                        {domainsLoading ? (
                            <div className="dash-projects-empty"><p>Loading sites...</p></div>
                        ) : deployedSites.length === 0 ? (
                            <div className="dsite-empty">
                                <div className="dsite-empty-icon">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
                                </div>
                                <h3>Nothing deployed yet</h3>
                                <p>Buy a domain or build a website to get started.</p>
                                <button className="dsite-cta-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                    Get started
                                </button>
                            </div>
                        ) : (
                            <div className="dsite-list">
                                {deployedSites.map(site => {
                                    const sColor = statusColor(site.domain_status || site.status);
                                    const sLabel = (site.domain_status || site.status || 'draft').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                                    return (
                                        <div key={site.id} className="dsite-card">
                                            {/* Card Header */}
                                            <div className="dsite-card-top">
                                                <div className="dsite-info">
                                                    <div className="dsite-icon-wrap">
                                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                            <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                                        </svg>
                                                    </div>
                                                    <div className="dsite-meta">
                                                        <h3 className="dsite-name">{site.domain || site.name}</h3>
                                                        {site.url && (
                                                            <a href={site.url} target="_blank" rel="noopener noreferrer" className="dsite-url">
                                                                {site.url}
                                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                                <span className={`dsite-badge dsite-badge-${sColor}`}>{sLabel}</span>
                                            </div>

                                            {/* Quick Stats */}
                                            <div className="dsite-stats-row">
                                                <div className="dsite-stat">
                                                    <span className="dsite-stat-label">Domain</span>
                                                    <span className="dsite-stat-value">{site.domain || 'Not connected'}</span>
                                                </div>
                                                <div className="dsite-stat">
                                                    <span className="dsite-stat-label">SSL</span>
                                                    <span className="dsite-stat-value">{site.domain ? (site.cloudfront_domain ? 'Active' : 'Pending') : '—'}</span>
                                                </div>
                                                <div className="dsite-stat">
                                                    <span className="dsite-stat-label">CDN</span>
                                                    <span className="dsite-stat-value">{site.cloudfront_domain ? 'Active' : '—'}</span>
                                                </div>
                                                {site.last_deployed_at && (
                                                    <div className="dsite-stat">
                                                        <span className="dsite-stat-label">Deployed</span>
                                                        <span className="dsite-stat-value">{new Date(site.last_deployed_at).toLocaleDateString()}</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* CNAME Target — always shown */}
                                            <div style={{ background: '#1a1a2e', border: '1px solid #374151', borderRadius: 8, padding: 16, margin: '12px 0' }}>
                                                <h4 style={{ fontSize: 13, fontWeight: 600, color: site.domain_status === 'active' ? '#34d399' : site.domain ? '#fbbf24' : '#818cf8', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        {site.domain_status === 'active'
                                                            ? <><polyline points="20 6 9 17 4 12" /></>
                                                            : <><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></>
                                                        }
                                                    </svg>
                                                    {site.domain_status === 'active' ? 'Domain Active' : site.domain ? 'Domain Setup Required' : 'CNAME Target'}
                                                </h4>

                                                {/* CNAME record */}
                                                <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 10 }}>
                                                    {site.domain
                                                        ? 'Point your domain\'s CNAME record to this address:'
                                                        : 'Use this CNAME target to connect a custom domain:'}
                                                </p>
                                                <div style={{ background: '#0f0f1a', borderRadius: 6, padding: '10px 14px', fontFamily: 'monospace', fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <div>
                                                        {site.domain && (
                                                            <>
                                                                <span style={{ color: '#818cf8' }}>www.{site.domain}</span>
                                                                <span style={{ color: '#6b7280' }}> → CNAME → </span>
                                                            </>
                                                        )}
                                                        <span style={{ color: '#34d399' }}>{site.cname_target || site.cloudfront_domain || site.s3_hostname || '(pending)'}</span>
                                                    </div>
                                                    {(site.cname_target || site.cloudfront_domain || site.s3_hostname) && (
                                                        <button onClick={() => navigator.clipboard.writeText(site.cname_target || site.cloudfront_domain || site.s3_hostname)} style={{ padding: '3px 8px', borderRadius: 4, border: '1px solid #374151', background: 'none', color: '#9ca3af', fontSize: 11, cursor: 'pointer' }}>Copy</button>
                                                    )}
                                                </div>

                                                {/* Status line */}
                                                <p style={{ fontSize: 11, color: '#6b7280', marginTop: 8 }}>
                                                    {site.domain ? (
                                                        <>
                                                            Status: <span style={{ color: site.domain_status === 'pending_validation' ? '#fbbf24' : site.domain_status === 'active' ? '#22c55e' : '#818cf8' }}>{(site.domain_status || '').replace(/_/g, ' ')}</span>
                                                            {site.domain_status !== 'active' && ' · SSL and CDN will activate automatically once DNS propagates.'}
                                                        </>
                                                    ) : (
                                                        <>Add a CNAME record at your DNS provider pointing to the address above, then click "Connect Domain".</>
                                                    )}
                                                </p>

                                                {/* DNS records from backend */}
                                                {site.dns_records && site.dns_records.length > 0 && (
                                                    <div style={{ marginTop: 12, borderTop: '1px solid #374151', paddingTop: 10 }}>
                                                        <p style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', marginBottom: 6 }}>DNS Records</p>
                                                        {site.dns_records.map((rec, i) => (
                                                            <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12, fontFamily: 'monospace', padding: '3px 0', color: '#d1d5db' }}>
                                                                <span style={{ color: '#818cf8', minWidth: 50 }}>{rec.type}</span>
                                                                <span style={{ color: '#9ca3af', flex: 1 }}>{rec.name}</span>
                                                                <span style={{ color: '#34d399' }}>{rec.value}</span>
                                                                <span style={{ color: '#6b7280', fontSize: 10 }}>{rec.purpose}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Actions Bar */}
                                            <div className="dsite-actions">
                                                {!site.domain && site.status === 'published' && (
                                                    <button className="dsite-action-btn dsite-action-primary" onClick={() => { setConnectModal(site.id); setConnectResult(null); setDomainInput(''); setConnectStep(1); }}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                                        Connect Domain
                                                    </button>
                                                )}
                                                {site.url && (
                                                    <a href={site.url} target="_blank" rel="noopener noreferrer" className="dsite-action-btn">
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
                                                        Visit Site
                                                    </a>
                                                )}
                                                {site.domain && (
                                                    <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'dns'); if (!dnsRecords[site.id]) loadDnsRecords(site.id); }}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg>
                                                        DNS Records
                                                    </button>
                                                )}
                                                {site.domain && (
                                                    <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'ns'); if (!nameservers[site.id]) loadNameservers(site.id); }}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
                                                        Nameservers
                                                    </button>
                                                )}
                                                {site.domain_record_id && (
                                                    <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'contact'); loadContactInfo(site.domain_record_id); }}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                                                        Contact Info
                                                    </button>
                                                )}
                                                {/* Export ZIP */}
                                                {site.status === 'published' && (
                                                    <button className="dsite-action-btn" onClick={() => handleExportZip(site.id, site.name)} disabled={exporting === site.id}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                                                        {exporting === site.id ? 'Exporting...' : 'Export ZIP'}
                                                    </button>
                                                )}
                                                {/* Custom Code */}
                                                <button className="dsite-action-btn" onClick={() => handleOpenCustomCode(site.id)}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></svg>
                                                    Code Inject
                                                </button>
                                                {/* Analytics */}
                                                <button className="dsite-action-btn" onClick={() => handleOpenAnalytics(site.id)}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg>
                                                    Analytics
                                                </button>
                                                <div className="dsite-actions-right">
                                                    {site.domain && (
                                                        <button className="dsite-action-btn dsite-action-danger" onClick={() => setDisconnectConfirm(site.id)}>Disconnect</button>
                                                    )}
                                                    <button className="dsite-action-btn dsite-action-danger" onClick={() => setDeleteSiteConfirm(site.id)}>
                                                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /></svg>
                                                        Delete
                                                    </button>
                                                </div>
                                            </div>

                                            {/* DNS Records Panel */}
                                            {site.domain && isSectionExpanded(site.id, 'dns') && (
                                                <div className="dsite-panel">
                                                    <div className="dsite-panel-header">
                                                        <h4>DNS Records</h4>
                                                        <button className="dsite-panel-btn" onClick={() => setAddRecordModal(site.id)}>+ Add Record</button>
                                                    </div>
                                                    <table className="dash-domain-table">
                                                        <thead>
                                                            <tr><th>Type</th><th>Name</th><th>Value</th><th>TTL</th><th></th></tr>
                                                        </thead>
                                                        <tbody>
                                                            {(dnsRecords[site.id] || []).map((rec, i) => (
                                                                <tr key={i}>
                                                                    <td><span className="dash-domain-type-badge">{rec.type}</span></td>
                                                                    <td style={{ fontSize: 13 }}>{rec.name}</td>
                                                                    <td className="dash-domain-value-cell">{rec.is_alias ? `ALIAS \u2192 ${rec.alias_target || rec.value}` : rec.value}</td>
                                                                    <td>{rec.ttl || '\u2014'}</td>
                                                                    <td>
                                                                        {!rec.managed ? (
                                                                            <button className="dash-domain-edit-btn" title="Delete" onClick={() => setDeleteRecordConfirm({ siteId: site.id, record: rec })} style={{ color: '#ef4444' }}>
                                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /></svg>
                                                                            </button>
                                                                        ) : <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>System</span>}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                            {!dnsRecords[site.id] && (
                                                                <tr><td colSpan="5" className="dsite-panel-empty">Loading records...</td></tr>
                                                            )}
                                                            {dnsRecords[site.id] && dnsRecords[site.id].length === 0 && (
                                                                <tr><td colSpan="5" className="dsite-panel-empty">
                                                                    {site.route53_zone_id ? 'No DNS records found' : 'No hosted zone \u2014 connect a domain first'}
                                                                </td></tr>
                                                            )}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}

                                            {/* Nameservers Panel */}
                                            {site.domain && isSectionExpanded(site.id, 'ns') && (
                                                <div className="dsite-panel">
                                                    <div className="dsite-panel-header">
                                                        <h4>Nameservers</h4>
                                                    </div>
                                                    <p className="dsite-panel-hint">Point your domain to these nameservers at your registrar:</p>
                                                    <div className="dsite-ns-grid">
                                                        {!nameservers[site.id] ? (
                                                            <p className="dsite-panel-empty">Loading nameservers...</p>
                                                        ) : nameservers[site.id].length > 0 ? (
                                                            nameservers[site.id].map((ns, i) => (
                                                                <div key={i} className="dsite-ns-item">
                                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
                                                                    <code>{ns}</code>
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <p className="dsite-panel-empty">
                                                                {site.route53_zone_id ? 'No nameservers found' : 'No hosted zone \u2014 connect a domain first'}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Contact Info Panel */}
                                            {site.domain_record_id && isSectionExpanded(site.id, 'contact') && (
                                                <div className="dsite-panel">
                                                    <div className="dsite-panel-header">
                                                        <h4>Contact Information</h4>
                                                        {contactInfo[site.domain_record_id] && contactEditing !== site.domain_record_id && (
                                                            <button className="dsite-panel-btn" onClick={() => handleContactEdit(site.domain_record_id)}>Edit</button>
                                                        )}
                                                    </div>
                                                    {contactLoading[site.domain_record_id] || !(site.domain_record_id in contactInfo) ? (
                                                        <p className="dsite-panel-empty">Loading contact info...</p>
                                                    ) : !contactInfo[site.domain_record_id] ? (
                                                        <p className="dsite-panel-empty">No contact information available</p>
                                                    ) : contactEditing === site.domain_record_id ? (
                                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, padding: '8px 0' }}>
                                                            {['first_name', 'last_name', 'company_name', 'email', 'phone'].map(field => (
                                                                <div key={field} style={field === 'company_name' ? { gridColumn: '1 / -1' } : {}}>
                                                                    <label style={{ fontSize: 11, color: '#9ca3af', textTransform: 'capitalize', display: 'block', marginBottom: 3 }}>{field.replace(/_/g, ' ')}</label>
                                                                    <input
                                                                        value={contactForm[field] || ''}
                                                                        onChange={e => setContactForm(prev => ({ ...prev, [field]: e.target.value }))}
                                                                        style={{ width: '100%', padding: '6px 10px', fontSize: 13, background: '#1f2937', border: '1px solid #374151', borderRadius: 6, color: '#f3f4f6', outline: 'none', boxSizing: 'border-box' }}
                                                                    />
                                                                </div>
                                                            ))}
                                                            <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                                                                <button onClick={() => setContactEditing(null)} style={{ padding: '6px 14px', fontSize: 12, background: 'none', border: '1px solid #4b5563', borderRadius: 6, color: '#9ca3af', cursor: 'pointer' }}>Cancel</button>
                                                                <button onClick={() => handleContactSave(site.domain_record_id)} disabled={contactSaving} style={{ padding: '6px 14px', fontSize: 12, background: '#3b82f6', border: 'none', borderRadius: 6, color: '#fff', cursor: 'pointer', opacity: contactSaving ? 0.5 : 1 }}>{contactSaving ? 'Saving...' : 'Save'}</button>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 20px', padding: '8px 0' }}>
                                                            {[
                                                                ['Name', `${contactInfo[site.domain_record_id].first_name || ''} ${contactInfo[site.domain_record_id].last_name || ''}`.trim()],
                                                                ['Company', contactInfo[site.domain_record_id].company_name],
                                                                ['Email', contactInfo[site.domain_record_id].email],
                                                                ['Phone', contactInfo[site.domain_record_id].phone],
                                                            ].map(([label, value]) => (
                                                                <div key={label}>
                                                                    <span style={{ fontSize: 11, color: '#6b7280', display: 'block' }}>{label}</span>
                                                                    <span style={{ fontSize: 13, color: '#e5e7eb' }}>{value || '—'}</span>
                                                                </div>
                                                            ))}
                                                            {contactInfo[site.domain_record_id].address && (
                                                                <div style={{ gridColumn: '1 / -1' }}>
                                                                    <span style={{ fontSize: 11, color: '#6b7280', display: 'block' }}>Address</span>
                                                                    <span style={{ fontSize: 13, color: '#e5e7eb' }}>
                                                                        {[contactInfo[site.domain_record_id].address.street, contactInfo[site.domain_record_id].address.number, contactInfo[site.domain_record_id].address.city, contactInfo[site.domain_record_id].address.state, contactInfo[site.domain_record_id].address.country].filter(Boolean).join(', ')}
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Transfer Request section */}
                                                    <div style={{ borderTop: '1px solid #374151', marginTop: 12, paddingTop: 12 }}>
                                                        {site.transfer_requested_at ? (
                                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                                                    <span style={{ fontSize: 13, color: '#fbbf24' }}>Transfer requested on {new Date(site.transfer_requested_at).toLocaleDateString()}</span>
                                                                </div>
                                                                <button onClick={() => handleCancelTransfer(site.domain_record_id)} style={{ fontSize: 12, background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '4px 10px', color: '#9ca3af', cursor: 'pointer' }}>Cancel</button>
                                                            </div>
                                                        ) : (
                                                            <button
                                                                onClick={() => { setTransferModal(site.domain_record_id); setTransferReason(''); setTransferResult(null); }}
                                                                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '6px 14px', color: '#9ca3af', cursor: 'pointer' }}
                                                            >
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>
                                                                Request Domain Transfer
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Pending status notice with refresh */}
                                            {(site.domain_status === 'pending_validation' || site.domain_status === 'pending_deployment' || site.domain_status === 'creating_cdn') && (
                                                <div className="dsite-notice" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                                        {site.domain_status === 'pending_validation' ? 'SSL certificate pending validation...' :
                                                            site.domain_status === 'creating_cdn' ? 'Creating CDN distribution...' :
                                                                'CloudFront deployment in progress...'}
                                                    </div>
                                                    <button
                                                        onClick={async (e) => {
                                                            const btn = e.currentTarget;
                                                            btn.disabled = true;
                                                            btn.textContent = 'Checking...';
                                                            try {
                                                                const result = await getDomainStatus(site.id);
                                                                // Refresh the sites list
                                                                const data = await listDeployedSites();
                                                                setDeployedSites(data.sites || []);
                                                                if (result.domain_status === 'active') {
                                                                    btn.textContent = 'Active!';
                                                                    btn.style.color = '#34d399';
                                                                } else {
                                                                    btn.textContent = 'Still pending';
                                                                    setTimeout(() => { btn.textContent = 'Refresh'; btn.disabled = false; }, 2000);
                                                                }
                                                            } catch (err) {
                                                                btn.textContent = 'Error';
                                                                setTimeout(() => { btn.textContent = 'Refresh'; btn.disabled = false; }, 2000);
                                                            }
                                                        }}
                                                        style={{ background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '4px 12px', color: '#9ca3af', fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}
                                                    >
                                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>
                                                        Refresh
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* Connect Domain Modal — Multi-step */}
                {connectModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setConnectModal(null); setConnectResult(null); setConnectError(null); setConnectStep(1); setDomainSearchResults(null); setDomainInput(''); }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setConnectModal(null); setConnectResult(null); setConnectError(null); setConnectStep(1); setDomainSearchResults(null); setDomainInput(''); } }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 520 }}>
                            {/* Close button */}
                            <button onClick={() => { setConnectModal(null); setConnectResult(null); setConnectError(null); setConnectStep(1); setDomainSearchResults(null); setDomainInput(''); }} style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: 18 }}>×</button>

                            {/* Step 3: Success */}
                            {connectStep === 3 && connectResult ? (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#ecfdf5' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Domain Connected!</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>{connectResult.instructions}</p>
                                    {connectResult.nameservers && (
                                        <div style={{ background: '#1f2937', borderRadius: 8, padding: 16, marginBottom: 16, border: '1px solid #374151' }}>
                                            <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#d1d5db' }}>Set these nameservers at your registrar:</p>
                                            {connectResult.nameservers.map((ns, i) => (
                                                <div key={i} style={{ fontFamily: 'monospace', fontSize: 13, padding: '4px 0', color: '#e5e7eb' }}>{ns}</div>
                                            ))}
                                        </div>
                                    )}
                                    {connectResult.cname_target && (
                                        <div style={{ background: '#1f2937', borderRadius: 8, padding: 16, marginBottom: 16, border: '1px solid #374151' }}>
                                            <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#d1d5db' }}>Add this CNAME record at your DNS provider:</p>
                                            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                                <code style={{ fontSize: 13, color: '#e5e7eb', flex: 1 }}>www → {connectResult.cname_target}</code>
                                                <button onClick={() => navigator.clipboard.writeText(connectResult.cname_target)} style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid #374151', background: 'none', color: '#9ca3af', fontSize: 11, cursor: 'pointer' }}>Copy</button>
                                            </div>
                                        </div>
                                    )}
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-confirm" onClick={() => { setConnectModal(null); setConnectResult(null); setConnectStep(1); }}>Done</button>
                                    </div>
                                </>

                                /* Step 2: Search Results */
                            ) : connectStep === 2 && domainSearchResults ? (
                                <>
                                    <h3 style={{ marginBottom: 4, color: '#f3f4f6' }}>Domain Search Results</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                        Results for "<strong style={{ color: '#e5e7eb' }}>{domainInput}</strong>"
                                    </p>

                                    {connectError && <p style={{ fontSize: 13, color: '#ef4444', marginBottom: 12 }}>{connectError}</p>}

                                    <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: 16, borderRadius: 8, border: '1px solid #374151' }}>
                                        {domainSearchResults.map((r, i) => (
                                            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', borderBottom: i < domainSearchResults.length - 1 ? '1px solid #374151' : 'none', background: r.status === 'free' ? '#1a2332' : '#1f2937' }}>
                                                <div>
                                                    <span style={{ fontWeight: 600, fontSize: 14, color: '#f3f4f6' }}>{r.sld || r.domain?.split('.')[0]}</span>
                                                    <span style={{ color: '#9ca3af', fontSize: 14 }}>.{r.tld || r.domain?.split('.').slice(1).join('.')}</span>
                                                </div>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                    {r.status === 'free' ? (
                                                        <>
                                                            {r.price && <span style={{ fontSize: 13, color: '#34d399', fontWeight: 600 }}>${r.price.amount}/yr</span>}
                                                            <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 500 }}>Available</span>
                                                            <button onClick={() => setPurchaseConfirm({ sld: r.sld, tld: r.tld, siteId: connectModal, price: r.price })} style={{ padding: '5px 12px', borderRadius: 6, border: 'none', background: '#22c55e', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                                                                Buy & Connect
                                                            </button>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <span style={{ fontSize: 11, color: '#f59e0b', fontWeight: 500 }}>Registered</span>
                                                            <button onClick={() => handleConnectDomain(`${r.sld || r.domain?.split('.')[0]}.${r.tld || r.domain?.split('.').slice(1).join('.')}`)} disabled={connecting} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #374151', background: 'none', color: '#e5e7eb', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                                                                {connecting ? '...' : 'I own this'}
                                                            </button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => { setConnectStep(1); setDomainSearchResults(null); setConnectError(null); }}>
                                            ← Back to Search
                                        </button>
                                    </div>
                                </>

                                /* Step 1: Search */
                            ) : (
                                <>
                                    <h3 style={{ marginBottom: 4, color: '#f3f4f6' }}>Connect Domain</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                        Search for a domain to buy, or enter one you already own.
                                    </p>

                                    {connectError && connectError !== 'not_registered' && <p style={{ fontSize: 13, color: '#ef4444', marginBottom: 12 }}>{connectError}</p>}

                                    {/* Owned domains for quick connect */}
                                    {modalOwnedDomains.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 8 }}>Your available domains</p>
                                            <div style={{ borderRadius: 8, border: '1px solid #374151', overflow: 'hidden' }}>
                                                {modalOwnedDomains.map((d, i) => (
                                                    <div key={d.id} style={{ borderBottom: i < modalOwnedDomains.length - 1 ? '1px solid #374151' : 'none', background: '#1f2937' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px' }}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                                <span style={{ fontSize: 14, fontWeight: 600, color: '#f3f4f6' }}>{d.domain_name}</span>
                                                                {d.instant_connect && (
                                                                    <span style={{ fontSize: 10, fontWeight: 600, color: '#fbbf24', background: 'rgba(251,191,36,0.12)', padding: '2px 6px', borderRadius: 4 }}>Instant</span>
                                                                )}
                                                            </div>
                                                            <button onClick={() => handleConnectOwnedDomain(d.domain_name)} disabled={!!connectingOwned} style={{ padding: '5px 14px', borderRadius: 6, border: 'none', background: '#2563eb', color: '#fff', fontSize: 12, fontWeight: 600, cursor: connectingOwned ? 'wait' : 'pointer', opacity: connectingOwned ? 0.6 : 1 }}>
                                                                {connectingOwned === d.domain_name ? 'Connecting...' : 'Connect'}
                                                            </button>
                                                        </div>
                                                        {connectingOwned === d.domain_name && (
                                                            <div style={{ padding: '0 14px 10px', fontSize: 11, color: '#9ca3af' }}>
                                                                Setting up DNS &amp; SSL — this may take up to 60 seconds...
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0', color: '#6b7280', fontSize: 12 }}>
                                                <div style={{ flex: 1, height: 1, background: '#374151' }} />
                                                <span>or search for a domain</span>
                                                <div style={{ flex: 1, height: 1, background: '#374151' }} />
                                            </div>
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                        <input
                                            type="text"
                                            value={domainInput}
                                            onChange={e => setDomainInput(e.target.value)}
                                            placeholder="mybusiness.ae"
                                            style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid #374151', background: '#1f2937', color: '#f3f4f6', fontSize: 14 }}
                                            disabled={searchLoading}
                                            onKeyDown={e => e.key === 'Enter' && handleSearchDomain()}
                                        />
                                        <button className="dash-domain-modal-confirm" onClick={handleSearchDomain} disabled={searchLoading || !domainInput.trim()} style={{ whiteSpace: 'nowrap' }}>
                                            {searchLoading ? 'Searching...' : 'Search'}
                                        </button>
                                    </div>

                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => { setConnectModal(null); setConnectStep(1); setDomainInput(''); }}>Cancel</button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* Add DNS Record Modal */}
                {addRecordModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setAddRecordModal(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setAddRecordModal(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 420 }}>
                            <h3 style={{ marginBottom: 12 }}>Add DNS Record</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                <select value={newRecord.type} onChange={e => setNewRecord({ ...newRecord, type: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}>
                                    {['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'CAA'].map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                                <input placeholder="Name (e.g. mail, @, subdomain)" value={newRecord.name} onChange={e => setNewRecord({ ...newRecord, name: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                                <input placeholder={newRecord.type === 'MX' ? '10 mail.google.com' : 'Value'} value={newRecord.value} onChange={e => setNewRecord({ ...newRecord, value: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                                <input type="number" placeholder="TTL (default 300)" value={newRecord.ttl} onChange={e => setNewRecord({ ...newRecord, ttl: parseInt(e.target.value) || 300 })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                            </div>
                            <div className="dash-domain-modal-actions" style={{ marginTop: 16 }}>
                                <button className="dash-domain-modal-cancel" onClick={() => setAddRecordModal(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" onClick={handleAddRecord} disabled={addingRecord || !newRecord.name || !newRecord.value}>
                                    {addingRecord ? 'Adding...' : 'Add Record'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Disconnect Confirmation Modal */}
                {disconnectConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDisconnectConfirm(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setDisconnectConfirm(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                            <h3>Disconnect Domain?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                This will remove the custom domain, SSL certificate, CDN, and DNS zone from our platform. Your site will still be accessible via the S3 URL.
                            </p>
                            <p style={{ fontSize: 13, color: '#f59e0b', margin: '0 0 16px', fontWeight: 500 }}>
                                Important: You must manually update your nameservers back to default at your domain registrar (e.g. GoDaddy), otherwise your domain will stop resolving.
                            </p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDisconnectConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDisconnect(disconnectConfirm)}>Disconnect</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete Site Confirmation Modal */}
                {deleteSiteConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDeleteSiteConfirm(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setDeleteSiteConfirm(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                            <h3>Delete Deployed Site?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                This will permanently remove the site from S3, delete all associated domain resources (SSL, DNS, CDN), and cannot be undone.
                            </p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDeleteSiteConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDeleteSite(deleteSiteConfirm)}>Delete</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Domain Purchase Confirmation Modal */}
                {purchaseConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setPurchaseConfirm(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setPurchaseConfirm(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                            <h3>Confirm Domain Purchase</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 8px' }}>
                                You are about to purchase:
                            </p>
                            <div style={{ background: '#1a2332', borderRadius: 8, padding: '14px 16px', margin: '8px 0 16px', border: '1px solid #374151' }}>
                                <span style={{ fontWeight: 700, fontSize: 16, color: '#f3f4f6' }}>{purchaseConfirm.sld}.{purchaseConfirm.tld}</span>
                                {purchaseConfirm.price && <span style={{ marginLeft: 12, fontSize: 14, color: '#34d399', fontWeight: 600 }}>${purchaseConfirm.price.amount}/yr</span>}
                            </div>
                            <p style={{ fontSize: 12, color: '#f59e0b', margin: '0 0 16px', lineHeight: 1.5 }}>
                                This action is non-refundable. The domain will be registered and connected to your site immediately.
                            </p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setPurchaseConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#22c55e' }} disabled={purchasing} onClick={() => handleQuickPurchase(purchaseConfirm.sld, purchaseConfirm.tld, purchaseConfirm.siteId)}>
                                    {purchasing ? 'Processing...' : 'Confirm Purchase'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete DNS Record Confirmation Modal */}
                {deleteRecordConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDeleteRecordConfirm(null)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setDeleteRecordConfirm(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                            <h3>Delete DNS Record?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                Deleting this record cannot be undone. This may affect email delivery, domain verification, or other services using this record.
                            </p>
                            <div style={{ background: '#1f2937', borderRadius: 6, padding: 12, marginBottom: 16, fontSize: 13 }}>
                                <strong>{deleteRecordConfirm.record.type}</strong> {deleteRecordConfirm.record.name} → {deleteRecordConfirm.record.value}
                            </div>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDeleteRecordConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => { handleDeleteRecord(deleteRecordConfirm.siteId, deleteRecordConfirm.record); setDeleteRecordConfirm(null); }}>Delete Record</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Transfer Request Modal */}
                {transferModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setTransferModal(null); setTransferResult(null); }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setTransferModal(null); setTransferResult(null); } }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 440 }}>
                            {transferResult ? (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: transferResult.status === 'error' ? '#fef2f2' : '#ecfdf5' }}>
                                        {transferResult.status === 'error' ? (
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
                                        ) : (
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                                        )}
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>{transferResult.status === 'error' ? 'Error' : 'Transfer Requested'}</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>{transferResult.message}</p>
                                    <button className="dash-domain-modal-confirm" style={{ background: '#3b82f6', width: '100%' }} onClick={() => { setTransferModal(null); setTransferResult(null); }}>OK</button>
                                </>
                            ) : (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#fef3c7' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Request Domain Transfer</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                        Submit a request to transfer this domain away from the platform. Our team will review and process your request within 24-48 hours.
                                    </p>
                                    <div style={{ marginBottom: 16 }}>
                                        <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                                        <textarea
                                            value={transferReason}
                                            onChange={e => setTransferReason(e.target.value)}
                                            placeholder="e.g. Moving to a different hosting provider..."
                                            rows={3}
                                            style={{ width: '100%', padding: '8px 12px', fontSize: 13, background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6', outline: 'none', resize: 'vertical', boxSizing: 'border-box' }}
                                        />
                                    </div>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setTransferModal(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#f59e0b' }} onClick={handleTransferRequest} disabled={transferSubmitting}>
                                            {transferSubmitting ? 'Submitting...' : 'Submit Request'}
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* Custom Code Modal */}
                {customCodeModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setCustomCodeModal(null)} onKeyDown={e => { if (e.key === 'Escape') setCustomCodeModal(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 560 }}>
                            <button onClick={() => setCustomCodeModal(null)} style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: 18 }}>×</button>
                            <h3 style={{ marginBottom: 4, color: '#f3f4f6' }}>Custom Code Injection</h3>
                            <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>Add custom HTML, CSS, or JavaScript. Takes effect on next deploy.</p>

                            <div style={{ marginBottom: 14 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Head Code (before &lt;/head&gt;)</label>
                                <textarea
                                    value={customHeadCode}
                                    onChange={e => setCustomHeadCode(e.target.value)}
                                    placeholder="<!-- Google Analytics, custom meta tags, external CSS -->"
                                    style={{ width: '100%', minHeight: 100, padding: '10px 12px', background: '#1f2937', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, fontSize: 13, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }}
                                />
                            </div>

                            <div style={{ marginBottom: 16 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Body Code (before &lt;/body&gt;)</label>
                                <textarea
                                    value={customBodyCode}
                                    onChange={e => setCustomBodyCode(e.target.value)}
                                    placeholder="<!-- Chat widgets, custom scripts, tracking pixels -->"
                                    style={{ width: '100%', minHeight: 100, padding: '10px 12px', background: '#1f2937', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, fontSize: 13, fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="dash-domain-modal-cancel" onClick={() => setCustomCodeModal(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" onClick={handleSaveCustomCode} disabled={customCodeSaving}>
                                    {customCodeSaving ? 'Saving...' : 'Save Code'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Analytics Modal */}
                {analyticsModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setAnalyticsModal(null)} onKeyDown={e => { if (e.key === 'Escape') setAnalyticsModal(null); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 560 }}>
                            <button onClick={() => setAnalyticsModal(null)} style={{ position: 'absolute', top: 12, right: 12, background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: 18 }}>×</button>
                            <h3 style={{ marginBottom: 4, color: '#f3f4f6' }}>Site Analytics</h3>
                            <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>Page views for the last 30 days</p>

                            {analyticsLoading ? (
                                <p style={{ color: '#9ca3af', textAlign: 'center', padding: 20 }}>Loading analytics...</p>
                            ) : analyticsData?.error ? (
                                <p style={{ color: '#ef4444', textAlign: 'center', padding: 20 }}>{analyticsData.error}</p>
                            ) : analyticsData ? (
                                <div>
                                    {/* Summary stats */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 20 }}>
                                        <div style={{ background: '#1f2937', borderRadius: 10, padding: 14, textAlign: 'center' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: '#f3f4f6' }}>{analyticsData.total_views}</div>
                                            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>Views (30d)</div>
                                        </div>
                                        <div style={{ background: '#1f2937', borderRadius: 10, padding: 14, textAlign: 'center' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: '#f3f4f6' }}>{analyticsData.unique_visitors}</div>
                                            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>Unique Visitors</div>
                                        </div>
                                        <div style={{ background: '#1f2937', borderRadius: 10, padding: 14, textAlign: 'center' }}>
                                            <div style={{ fontSize: 24, fontWeight: 700, color: '#f3f4f6' }}>{analyticsData.all_time_views}</div>
                                            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>All Time</div>
                                        </div>
                                    </div>

                                    {/* Top pages */}
                                    {analyticsData.top_pages?.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <h4 style={{ fontSize: 13, fontWeight: 600, color: '#d1d5db', marginBottom: 8 }}>Top Pages</h4>
                                            {analyticsData.top_pages.map((p, i) => (
                                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #27272a', fontSize: 13 }}>
                                                    <span style={{ color: '#e5e7eb' }}>{p.path}</span>
                                                    <span style={{ color: '#9ca3af' }}>{p.views} views</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Top referrers */}
                                    {analyticsData.top_referrers?.length > 0 && (
                                        <div>
                                            <h4 style={{ fontSize: 13, fontWeight: 600, color: '#d1d5db', marginBottom: 8 }}>Top Referrers</h4>
                                            {analyticsData.top_referrers.map((r, i) => (
                                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #27272a', fontSize: 13 }}>
                                                    <span style={{ color: '#e5e7eb', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '70%' }}>{r.referrer}</span>
                                                    <span style={{ color: '#9ca3af' }}>{r.views}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {analyticsData.total_views === 0 && (
                                        <p style={{ color: '#6b7280', textAlign: 'center', padding: 20 }}>No page views recorded yet. Views are tracked automatically after deployment.</p>
                                    )}
                                </div>
                            ) : null}

                            <div style={{ marginTop: 16 }}>
                                <button className="dash-domain-modal-confirm" onClick={() => setAnalyticsModal(null)}>Close</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Token Request Modal */}
                {tokenRequestModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setTokenRequestModal(false)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setTokenRequestModal(false); }} role="button" tabIndex={0}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation" style={{ maxWidth: 440 }}>
                            <div className="dash-domain-modal-icon" style={{ background: '#ede9fe' }}>
                                <span style={{ fontSize: 24 }}>🌐</span>
                            </div>
                            <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Request More Websites</h3>
                            <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                Need to create more websites? Submit a request and the admin will review it.
                            </p>
                            <div style={{ marginBottom: 12 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>How many websites do you need?</label>
                                <div style={{ display: 'flex', gap: 8 }}>
                                    {[1, 2, 3, 5].map(n => (
                                        <button
                                            key={n}
                                            onClick={() => setTokenRequestAmount(String(n))}
                                            style={{
                                                flex: 1, padding: '10px 0', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer',
                                                background: tokenRequestAmount === String(n) ? 'rgba(99,102,241,0.2)' : '#1f2937',
                                                border: tokenRequestAmount === String(n) ? '2px solid #6366f1' : '1px solid #374151',
                                                color: tokenRequestAmount === String(n) ? '#818cf8' : '#d1d5db',
                                            }}
                                        >
                                            {n}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                                <textarea
                                    value={tokenRequestReason}
                                    onChange={e => setTokenRequestReason(e.target.value)}
                                    placeholder="e.g. Starting a new business project..."
                                    style={{ width: '100%', minHeight: 60, padding: '8px 12px', background: '#1f2937', color: '#f3f4f6', border: '1px solid #374151', borderRadius: 8, fontSize: 13, resize: 'vertical' }}
                                />
                            </div>

                            {/* Show past requests */}
                            {tokenRequests.length > 0 && (
                                <div style={{ marginBottom: 16, maxHeight: 120, overflow: 'auto' }}>
                                    <label style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 4 }}>Your Requests</label>
                                    {tokenRequests.map(r => (
                                        <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <span style={{ color: '#d1d5db' }}>{r.reason || `${Math.round(parseInt(r.amount) / 150000)} website(s)`}</span>
                                            <span style={{ color: r.status === 'approved' ? '#34d399' : r.status === 'rejected' ? '#f87171' : '#fbbf24', fontWeight: 600 }}>
                                                {r.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="dash-domain-modal-cancel" onClick={() => setTokenRequestModal(false)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#6366f1' }} onClick={handleTokenRequest} disabled={tokenRequestSubmitting}>
                                    {tokenRequestSubmitting ? 'Submitting...' : `Request ${tokenRequestAmount} Website${tokenRequestAmount !== '1' ? 's' : ''}`}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ─── Entry-flow Modal: Buy Domain or Build Website ─── */}
                {entryStage && (
                    <div
                        className="dash-domain-modal-overlay"
                        onClick={closeEntryFlow}
                        onKeyDown={(e) => { if (e.key === 'Escape') closeEntryFlow(); }}
                        role="button"
                        tabIndex={0}
                    >
                        <div
                            className="dash-domain-modal"
                            onClick={e => e.stopPropagation()}
                            onKeyDown={e => e.stopPropagation()}
                            role="presentation"
                            style={{ maxWidth: entryStage === 'domainSearch' ? 640 : 520, padding: 0, overflow: 'hidden' }}
                        >
                            {/* Close button (top-right) */}
                            <button
                                onClick={closeEntryFlow}
                                aria-label="Close"
                                style={{ position: 'absolute', top: 14, right: 14, background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer', padding: 6, borderRadius: 6, zIndex: 2 }}
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                            </button>

                            {/* Stage 2: domain search + results */}
                            {entryStage === 'domainSearch' && (
                                <div style={{ padding: '28px 28px 24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
                                        <button
                                            onClick={() => { closeEntryFlow(); setEntrySearchResults(null); setEntrySearchError(null); }}
                                            style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer', padding: 6, display: 'flex', alignItems: 'center', gap: 4, fontSize: 13 }}
                                        >
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
                                            Back
                                        </button>
                                    </div>
                                    <h2 style={{ margin: '0 0 6px', fontSize: 20, color: '#030303', fontWeight: 700 }}>Find your perfect domain</h2>
                                    <p style={{ margin: '0 0 18px', fontSize: 13, color: '#9ca3af' }}>Type your business name to see available extensions.</p>

                                    <form onSubmit={handleEntryDomainSearch} style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                                        <input
                                            type="text"
                                            value={entrySearchInput}
                                            onChange={e => setEntrySearchInput(e.target.value)}
                                            placeholder="e.g. mybusiness"
                                            autoFocus
                                            style={{ flex: 1, background: '#0f172a', border: '1px solid #334155', color: '#f3f4f6', padding: '12px 14px', borderRadius: 8, fontSize: 14, outline: 'none' }}
                                        />
                                        <button
                                            type="submit"
                                            disabled={entrySearchLoading || !entrySearchInput.trim()}
                                            style={{ background: '#3b82f6', border: 'none', color: '#fff', padding: '0 20px', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: entrySearchLoading ? 'wait' : 'pointer', opacity: entrySearchLoading || !entrySearchInput.trim() ? 0.5 : 1 }}
                                        >
                                            {entrySearchLoading ? 'Searching…' : 'Search'}
                                        </button>
                                    </form>

                                    {entrySearchError && (
                                        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', padding: '10px 12px', borderRadius: 8, fontSize: 13, marginBottom: 12 }}>
                                            {entrySearchError}
                                        </div>
                                    )}

                                    {entrySearchLoading && (
                                        <div style={{ textAlign: 'center', padding: 30, color: '#94a3b8', fontSize: 13 }}>
                                            Checking 15 extensions…
                                        </div>
                                    )}

                                    {entrySearchResults && !entrySearchLoading && (
                                        <div style={{ maxHeight: 360, overflowY: 'auto', borderRadius: 10, border: '1px solid #1f2937' }}>
                                            {entrySearchResults.length === 0 ? (
                                                <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>No results</div>
                                            ) : (
                                                entrySearchResults.map((r, i) => {
                                                    const isFree = r.status === 'free';
                                                    return (
                                                        <div
                                                            key={`${r.sld}.${r.tld}`}
                                                            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: i < entrySearchResults.length - 1 ? '1px solid #1f2937' : 'none', background: i % 2 === 0 ? '#0b1220' : '#0f172a' }}
                                                        >
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
                                                                <span style={{ fontSize: 14, fontWeight: 600, color: '#f3f4f6' }}>
                                                                    {r.sld}<span style={{ color: '#60a5fa' }}>.{r.tld}</span>
                                                                </span>
                                                                {isFree ? (
                                                                    <span style={{ fontSize: 10, fontWeight: 700, color: '#34d399', background: 'rgba(52,211,153,0.12)', padding: '2px 7px', borderRadius: 4, textTransform: 'uppercase', letterSpacing: 0.4 }}>Available</span>
                                                                ) : (
                                                                    <span style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', background: 'rgba(156,163,175,0.12)', padding: '2px 7px', borderRadius: 4, textTransform: 'uppercase', letterSpacing: 0.4 }}>Taken</span>
                                                                )}
                                                            </div>
                                                            {isFree && r.price ? (
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                                                    <span style={{ fontSize: 13, color: '#cbd5e1', fontWeight: 600 }}>${r.price.amount}/yr</span>
                                                                    <button
                                                                        onClick={() => { setEntryPurchaseTarget({ sld: r.sld, tld: r.tld, price: r.price }); setEntryStage('domainConfirm'); }}
                                                                        style={{ background: '#3b82f6', border: 'none', color: '#fff', padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                                                                    >
                                                                        Buy
                                                                    </button>
                                                                </div>
                                                            ) : (
                                                                <span style={{ fontSize: 12, color: '#6b7280' }}>—</span>
                                                            )}
                                                        </div>
                                                    );
                                                })
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Stage 3: confirm purchase */}
                            {entryStage === 'domainConfirm' && entryPurchaseTarget && (
                                <div style={{ padding: '32px 28px 28px' }}>
                                    <h2 style={{ margin: '0 0 8px', fontSize: 20, color: '#f3f4f6', fontWeight: 700 }}>Confirm purchase</h2>
                                    <p style={{ margin: '0 0 20px', fontSize: 13, color: '#9ca3af' }}>You're about to register this domain for 1 year.</p>

                                    <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 10, padding: 18, marginBottom: 18 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                                            <span style={{ fontSize: 12, color: '#94a3b8' }}>Domain</span>
                                            <span style={{ fontSize: 16, fontWeight: 700, color: '#f3f4f6' }}>{entryPurchaseTarget.sld}.{entryPurchaseTarget.tld}</span>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ fontSize: 12, color: '#94a3b8' }}>Total (1 year)</span>
                                            <span style={{ fontSize: 16, fontWeight: 700, color: '#34d399' }}>${entryPurchaseTarget.price.amount}</span>
                                        </div>
                                    </div>

                                    {entrySearchError && (
                                        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', padding: '10px 12px', borderRadius: 8, fontSize: 13, marginBottom: 12 }}>
                                            {entrySearchError}
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', gap: 10 }}>
                                        <button
                                            onClick={() => { setEntryStage('domainSearch'); setEntryPurchaseTarget(null); setEntrySearchError(null); }}
                                            style={{ flex: 1, background: 'transparent', border: '1px solid #334155', color: '#cbd5e1', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleEntryPurchaseConfirm}
                                            style={{ flex: 1, background: '#3b82f6', border: 'none', color: '#fff', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
                                        >
                                            Confirm purchase
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Stage 4: purchasing spinner */}
                            {entryStage === 'purchasing' && (
                                <div style={{ padding: 60, textAlign: 'center' }}>
                                    <div style={{ display: 'inline-block', width: 40, height: 40, border: '3px solid #1f2937', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                                    <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
                                    <h3 style={{ margin: '20px 0 6px', fontSize: 16, color: '#f3f4f6' }}>Registering your domain…</h3>
                                    <p style={{ margin: 0, fontSize: 13, color: '#9ca3af' }}>This usually takes 10–30 seconds.</p>
                                </div>
                            )}

                            {/* Stage 5: success → ready to build? */}
                            {entryStage === 'domainSuccess' && entryPurchasedDomain && (
                                <div style={{ padding: '36px 28px 28px', textAlign: 'center' }}>
                                    <div style={{ width: 64, height: 64, borderRadius: '50%', background: entryPurchasedDomain.pending ? 'rgba(251,191,36,0.18)' : 'rgba(52,211,153,0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: entryPurchasedDomain.pending ? '#fbbf24' : '#34d399', marginBottom: 16 }}>
                                        {entryPurchasedDomain.pending ? (
                                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                        ) : (
                                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                        )}
                                    </div>
                                    <h2 style={{ margin: '0 0 6px', fontSize: 20, color: '#f3f4f6', fontWeight: 700 }}>{entryPurchasedDomain.pending ? 'Almost there…' : 'Domain ready!'}</h2>
                                    <p style={{ margin: '0 0 6px', fontSize: 14, color: '#94a3b8' }}>
                                        <strong style={{ color: '#60a5fa' }}>{entryPurchasedDomain.domain}</strong> {entryPurchasedDomain.pending ? 'is being registered.' : 'is now in your account.'}
                                    </p>
                                    <p style={{ margin: '0 0 24px', fontSize: 13, color: '#9ca3af' }}>
                                        {entryPurchasedDomain.pending
                                            ? 'It usually finishes within a couple of minutes — refresh My Domains to confirm.'
                                            : <>You can find it under <strong>Domains → My Domains</strong>.</>}
                                    </p>

                                    <h3 style={{ margin: '0 0 14px', fontSize: 15, color: '#f3f4f6' }}>Build your website now?</h3>
                                    <div style={{ display: 'flex', gap: 10 }}>
                                        <button
                                            onClick={() => { closeEntryFlow(); }}
                                            style={{ flex: 1, background: 'transparent', border: '1px solid #334155', color: '#cbd5e1', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}
                                        >
                                            Maybe later
                                        </button>
                                        <button
                                            onClick={() => {
                                                const carry = pendingPrompt;
                                                const domainStr = entryPurchasedDomain?.domain;
                                                const brand = brandFromDomain(domainStr);
                                                closeEntryFlow();
                                                navigate('/generator', {
                                                    state: {
                                                        newSession: true,
                                                        ...(carry ? { wizardPrefill: carry } : {}),
                                                        ...(domainStr ? { wizardDomain: domainStr, wizardBrand: brand } : {}),
                                                    },
                                                });
                                            }}
                                            style={{ flex: 1, background: '#3b82f6', border: 'none', color: '#fff', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
                                        >
                                            Yes, build now
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* New Design Modal */}
                {newDesignModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setNewDesignModal(false); setNewDesignPreview(null); }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setNewDesignModal(false); setNewDesignPreview(null); } }} role="button" tabIndex={0}>
                        <div className="dash-newdesign-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                            {!newDesignPreview ? (
                                <>
                                    <div className="dash-newdesign-header">
                                        <h2>New Design</h2>
                                        <button className="dash-template-modal-close" onClick={() => setNewDesignModal(false)}>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                            </svg>
                                        </button>
                                    </div>

                                    {/* Start from scratch */}
                                    <div className="dash-newdesign-scratch" onClick={() => { setNewDesignModal(false); navigate('/generator', { state: { newSession: true } }); }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setNewDesignModal(false); navigate('/generator', { state: { newSession: true } }); } }} role="button" tabIndex={0}>
                                        <div className="dash-newdesign-scratch-icon">
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 style={{ margin: 0, fontSize: 15, color: '#e5e7eb' }}>Start from Scratch</h4>
                                            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#9ca3af' }}>Describe your website and let AI build it</p>
                                        </div>
                                    </div>

                                    {/* Or pick a template */}
                                    <div style={{ padding: '0 24px 8px', fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Or start from a template</div>

                                    <div className="dash-newdesign-templates">
                                        {templatesLoading ? (
                                            <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>Loading templates...</div>
                                        ) : (
                                            templates.map(template => {
                                                const preview = templatePreviews[template.id];
                                                return (
                                                    <div key={template.id} className="dash-newdesign-template-row">
                                                        <div className="dash-newdesign-template-thumb">
                                                            {preview ? (
                                                                <iframe
                                                                    title={template.name}
                                                                    srcDoc={buildSrcDoc(preview.css, preview.html)}
                                                                    sandbox="allow-same-origin allow-scripts"
                                                                    scrolling="no"
                                                                    tabIndex={-1}
                                                                />
                                                            ) : (
                                                                <div style={{ background: '#1f2937', width: '100%', height: '100%', borderRadius: 6 }} />
                                                            )}
                                                        </div>
                                                        <div className="dash-newdesign-template-info">
                                                            <span style={{ fontSize: 11, color: '#6366f1', textTransform: 'uppercase', fontWeight: 600 }}>{template.category}</span>
                                                            <h4 style={{ margin: '2px 0', fontSize: 14, color: '#e5e7eb' }}>{template.name}</h4>
                                                            <p style={{ margin: 0, fontSize: 12, color: '#9ca3af', lineHeight: 1.4 }}>{template.description}</p>
                                                        </div>
                                                        <div className="dash-newdesign-template-actions">
                                                            <button className="dash-template-preview-btn" onClick={() => setNewDesignPreview(template.id)}>
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                                                                </svg>
                                                                Preview
                                                            </button>
                                                            <button className="dash-template-use-btn" style={{ padding: '8px 16px', fontSize: 13 }} onClick={() => { setNewDesignModal(false); handleUseTemplate(template.id); }}>
                                                                Use
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </>
                            ) : (
                                <>
                                    {/* Template preview inside new design modal */}
                                    <div className="dash-newdesign-header">
                                        <button className="dash-template-preview-btn" onClick={() => setNewDesignPreview(null)} style={{ gap: 4 }}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="15 18 9 12 15 6" />
                                            </svg>
                                            Back
                                        </button>
                                        <h3 style={{ margin: 0, flex: 1, textAlign: 'center' }}>{templates.find(t => t.id === newDesignPreview)?.name}</h3>
                                        <button className="dash-template-use-btn" style={{ width: 'auto', padding: '8px 20px', fontSize: 13 }} onClick={() => { setNewDesignModal(false); setNewDesignPreview(null); handleUseTemplate(newDesignPreview); }}>
                                            Use This Template
                                        </button>
                                    </div>
                                    <iframe
                                        title="Template Preview"
                                        srcDoc={templatePreviews[newDesignPreview] ? buildSrcDoc(templatePreviews[newDesignPreview].css, templatePreviews[newDesignPreview].html) : ''}
                                        className="dash-newdesign-preview-iframe"
                                        sandbox="allow-same-origin allow-scripts"
                                    />
                                </>
                            )}
                        </div>
                    </div>
                )}
                {/* ── Gallery Tab ── */}
                {activeTab === 'gallery' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <div>
                                <h1 className="dash-domain-title">Image Gallery</h1>
                                <p className="dash-domain-subtitle">Upload and manage images for your websites</p>
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <input
                                    ref={galleryFileRef}
                                    type="file"
                                    accept="image/*"
                                    multiple
                                    onChange={handleGalleryUpload}
                                    style={{ display: 'none' }}
                                />
                                <button
                                    className="dsite-action-btn dsite-action-primary"
                                    onClick={() => galleryFileRef.current?.click()}
                                    disabled={galleryUploading}
                                    style={{ padding: '8px 16px' }}
                                >
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                    {galleryUploading ? 'Uploading...' : 'Upload Images'}
                                </button>
                            </div>
                        </div>

                        {galleryLoading ? (
                            <div className="dash-projects-empty"><p>Loading images...</p></div>
                        ) : galleryImages.length === 0 ? (
                            <div className="dsite-empty">
                                <div className="dsite-empty-icon">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
                                    </svg>
                                </div>
                                <h3>No images yet</h3>
                                <p>Upload images to use in your websites. You can also upload from the website editor.</p>
                                <button className="dsite-cta-btn" onClick={() => galleryFileRef.current?.click()}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                    Upload Your First Image
                                </button>
                            </div>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
                                {galleryImages.map(img => {
                                    const imgSrc = img.url?.startsWith('http') ? img.url : `${config.apiUrl}${img.url}`;
                                    return (
                                        <div key={img.id} style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 10, overflow: 'hidden', transition: 'all 0.15s' }}>
                                            <div style={{ position: 'relative', paddingBottom: '75%', overflow: 'hidden', background: '#111' }}>
                                                <img
                                                    src={imgSrc}
                                                    alt={img.original_name}
                                                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
                                                    loading="lazy"
                                                />
                                            </div>
                                            <div style={{ padding: '10px 12px' }}>
                                                <p style={{ fontSize: 12, color: '#e5e7eb', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{img.original_name}</p>
                                                <p style={{ fontSize: 11, color: '#6b7280', margin: '4px 0 0' }}>
                                                    {img.width && img.height ? `${img.width}×${img.height}` : ''}{img.size_bytes ? ` · ${(img.size_bytes / 1024).toFixed(0)}KB` : ''}
                                                </p>
                                                <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                                                    <button
                                                        onClick={() => handleCopyImageUrl(imgSrc)}
                                                        style={{ flex: 1, padding: '5px 0', borderRadius: 6, border: '1px solid #374151', background: 'none', color: galleryCopied === imgSrc ? '#34d399' : '#9ca3af', fontSize: 11, cursor: 'pointer' }}
                                                    >
                                                        {galleryCopied === imgSrc ? 'Copied!' : 'Copy URL'}
                                                    </button>
                                                    <button
                                                        onClick={() => setGalleryDeleteConfirm(img.filename)}
                                                        style={{ padding: '5px 8px', borderRadius: 6, border: '1px solid #374151', background: 'none', color: '#ef4444', fontSize: 11, cursor: 'pointer' }}
                                                    >
                                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /></svg>
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Delete Image Confirmation */}
                        {galleryDeleteConfirm && (
                            <div className="dash-domain-modal-overlay" onClick={() => setGalleryDeleteConfirm(null)} onKeyDown={e => { if (e.key === 'Enter') setGalleryDeleteConfirm(null); }} role="button" tabIndex={0}>
                                <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                                    <h3>Delete Image?</h3>
                                    <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>This image will be permanently deleted and any sites using it will show a broken image.</p>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setGalleryDeleteConfirm(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleGalleryDelete(galleryDeleteConfirm)}>Delete</button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Inbox Tab ── */}
                {activeTab === 'inbox' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <div>
                                <h1 className="dash-domain-title">Inbox</h1>
                                <p className="dash-domain-subtitle">Contact form submissions from your deployed websites</p>
                            </div>
                        </div>

                        {/* Filters */}
                        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
                            <select
                                value={inboxSiteFilter}
                                onChange={e => setInboxSiteFilter(e.target.value)}
                                style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #374151', background: '#1f2937', color: '#e5e7eb', fontSize: 13 }}
                            >
                                <option value="">All sites</option>
                                {deployedSites.map(s => <option key={s.id} value={s.id}>{s.name || s.domain || s.id}</option>)}
                            </select>
                            <select
                                value={inboxReadFilter}
                                onChange={e => setInboxReadFilter(e.target.value)}
                                style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #374151', background: '#1f2937', color: '#e5e7eb', fontSize: 13 }}
                            >
                                <option value="">All messages</option>
                                <option value="unread">Unread only</option>
                                <option value="read">Read only</option>
                            </select>
                            <button onClick={loadSubmissions} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #374151', background: 'none', color: '#9ca3af', fontSize: 13, cursor: 'pointer' }}>
                                Refresh
                            </button>
                        </div>

                        {submissionsLoading ? (
                            <div className="dash-projects-empty"><p>Loading submissions...</p></div>
                        ) : submissions.length === 0 ? (
                            <div className="dsite-empty">
                                <div className="dsite-empty-icon">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
                                        <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
                                    </svg>
                                </div>
                                <h3>No submissions yet</h3>
                                <p>When visitors submit contact forms on your deployed websites, they'll appear here.</p>
                            </div>
                        ) : (
                            <div style={{ display: 'grid', gap: 8 }}>
                                {submissions.map(sub => {
                                    const isExpanded = expandedSubmission?.id === sub.id;
                                    const _f = sub.fields || {};
                                    const senderName = _f.name || _f.full_name || _f.first_name || _f.your_name || _f.full_name_ || _f.your_full_name || _f.contact_name || _f.client_name || _f.Name || Object.entries(_f).find(([k]) => /^(name|full.?name|first.?name|your.?name)/i.test(k))?.[1] || 'Anonymous';
                                    const senderEmail = _f.email || _f.your_email || _f.email_address || _f.contact_email || Object.entries(_f).find(([k]) => /email/i.test(k))?.[1] || '';
                                    const message = _f.message || _f.your_message || _f.inquiry || _f.comments || _f.description || _f.details || Object.entries(_f).find(([k]) => /message|comment|inquiry|detail/i.test(k))?.[1] || '';
                                    const timeAgo = sub.submitted_at ? new Date(sub.submitted_at).toLocaleString() : '';

                                    return (
                                        <div key={sub.id} style={{ background: sub.is_read ? '#18181b' : '#1a1a2e', border: `1px solid ${sub.is_read ? '#27272a' : '#374191'}`, borderRadius: 10, overflow: 'hidden', transition: 'all 0.15s' }}>
                                            {/* Row */}
                                            <div
                                                onClick={() => handleExpandSubmission(sub)}
                                                style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px', cursor: 'pointer' }}
                                                role="button"
                                                tabIndex={0}
                                                onKeyDown={e => { if (e.key === 'Enter') handleExpandSubmission(sub); }}
                                            >
                                                {/* Unread dot */}
                                                <div style={{ width: 8, height: 8, borderRadius: '50%', background: sub.is_read ? 'transparent' : '#3b82f6', flexShrink: 0 }} />
                                                {/* Sender info */}
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                                                        <span style={{ fontWeight: sub.is_read ? 400 : 600, color: '#f3f4f6', fontSize: 14 }}>{senderName}</span>
                                                        {senderEmail && <span style={{ fontSize: 12, color: '#6b7280' }}>{senderEmail}</span>}
                                                    </div>
                                                    {message && (
                                                        <p style={{ margin: 0, fontSize: 13, color: '#9ca3af', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>
                                                            {message.slice(0, 120)}{message.length > 120 ? '...' : ''}
                                                        </p>
                                                    )}
                                                </div>
                                                {/* Meta */}
                                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                                                    <span style={{ fontSize: 11, color: '#6b7280' }}>{timeAgo}</span>
                                                    <span style={{ fontSize: 11, color: '#4b5563', background: '#27272a', padding: '2px 6px', borderRadius: 4 }}>{sub.site_name || 'Unknown site'}</span>
                                                </div>
                                            </div>

                                            {/* Expanded detail */}
                                            {isExpanded && (
                                                <div style={{ borderTop: '1px solid #27272a', padding: '16px 18px', background: '#111114' }}>
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px', marginBottom: 16 }}>
                                                        {Object.entries(sub.fields || {}).map(([key, value]) => (
                                                            <div key={key} style={key === 'message' || key === 'inquiry' || key === 'comments' || String(value).length > 80 ? { gridColumn: '1 / -1' } : {}}>
                                                                <span style={{ fontSize: 11, color: '#6b7280', textTransform: 'capitalize', display: 'block', marginBottom: 2 }}>{key.replace(/_/g, ' ')}</span>
                                                                <span style={{ fontSize: 13, color: '#e5e7eb', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{String(value)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
                                                        <div style={{ fontSize: 11, color: '#4b5563' }}>
                                                            {sub.source_page && <span>Page: {sub.source_page}</span>}
                                                            {sub.ip_address && <span style={{ marginLeft: 12 }}>IP: {sub.ip_address}</span>}
                                                        </div>
                                                        <div style={{ display: 'flex', gap: 8 }}>
                                                            {senderEmail && (
                                                                <a href={`mailto:${senderEmail}`} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #374151', background: 'none', color: '#3b82f6', fontSize: 12, textDecoration: 'none', cursor: 'pointer' }}>
                                                                    Reply via Email
                                                                </a>
                                                            )}
                                                            <button onClick={(e) => { e.stopPropagation(); setDeleteSubmissionConfirm(sub.id); }} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #374151', background: 'none', color: '#ef4444', fontSize: 12, cursor: 'pointer' }}>
                                                                Delete
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Delete Submission Confirmation */}
                        {deleteSubmissionConfirm && (
                            <div className="dash-domain-modal-overlay" onClick={() => setDeleteSubmissionConfirm(null)} onKeyDown={e => { if (e.key === 'Enter') setDeleteSubmissionConfirm(null); }} role="button" tabIndex={0}>
                                <div className="dash-domain-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                                    <h3>Delete Submission?</h3>
                                    <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>This submission will be permanently deleted.</p>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setDeleteSubmissionConfirm(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDeleteSubmission(deleteSubmissionConfirm)}>Delete</button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </main>

            {/* Projects tab styles */}
            <style>{`
                .dash-projects-empty {
                    text-align: center;
                    padding: 4rem 2rem;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 12px;
                }
                .dash-projects-empty h3 {
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                    margin: 0;
                }
                .dash-projects-empty p {
                    color: #888;
                    font-size: 14px;
                    margin: 0;
                }
                .dash-projects-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
                    gap: 16px;
                    padding: 0 0 24px;
                }
                .dash-project-card {
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                    overflow: hidden;
                    transition: all 0.2s;
                    cursor: pointer;
                }
                .dash-project-card:hover {
                    border-color: #6366f1;
                    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.1);
                }
                .dash-project-thumb {
                    height: 140px;
                    background: #f8f9fa;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    position: relative;
                    cursor: pointer;
                }
                .dash-project-iframe {
                    width: 1280px;
                    height: 900px;
                    border: none;
                    pointer-events: none;
                    transform: scale(0.22);
                    transform-origin: top left;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                .dash-project-body {
                    padding: 12px 16px 8px;
                }
                .dash-project-name {
                    font-size: 15px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin: 0;
                    cursor: pointer;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .dash-project-name:hover {
                    color: #6366f1;
                }
                .dash-project-meta {
                    display: flex;
                    gap: 12px;
                    margin-top: 6px;
                    font-size: 12px;
                    color: #888;
                }
                .dash-project-actions {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px 16px 12px;
                }
                .dash-project-open {
                    background: #6366f1;
                    color: white;
                    border: none;
                    padding: 6px 20px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .dash-project-open:hover {
                    background: #4f46e5;
                }
                .dash-project-delete {
                    background: none;
                    border: 1px solid #e5e5e5;
                    padding: 6px 8px;
                    border-radius: 8px;
                    cursor: pointer;
                    color: #888;
                    transition: all 0.2s;
                }
                .dash-project-delete:hover {
                    border-color: #ef4444;
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.05);
                }

                /* ── Templates Tab ─────────────────────────────── */
                .dash-templates-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    padding: 0 0 24px;
                }
                .dash-template-card {
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                    overflow: hidden;
                    transition: all 0.2s;
                }
                .dash-template-card:hover {
                    border-color: #6366f1;
                    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
                    transform: translateY(-2px);
                }
                .dash-template-thumb {
                    height: 200px;
                    background: #f4f4f5;
                    overflow: hidden;
                    position: relative;
                    cursor: pointer;
                }
                .dash-template-iframe {
                    width: 1280px;
                    height: 900px;
                    border: none;
                    pointer-events: none;
                    transform: scale(0.25);
                    transform-origin: top left;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                .dash-template-placeholder {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .dash-template-colors {
                    display: flex;
                    gap: 8px;
                }
                .dash-template-swatch {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
                }
                .dash-template-overlay {
                    position: absolute;
                    inset: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    opacity: 0;
                    transition: opacity 0.2s;
                }
                .dash-template-thumb:hover .dash-template-overlay {
                    opacity: 1;
                }
                .dash-template-body {
                    padding: 16px;
                }
                .dash-template-category {
                    display: inline-block;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: #6366f1;
                    background: rgba(99, 102, 241, 0.08);
                    padding: 3px 8px;
                    border-radius: 4px;
                    margin-bottom: 8px;
                }
                .dash-template-name {
                    font-size: 16px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin: 8px 0 6px;
                }
                .dash-template-desc {
                    font-size: 13px;
                    color: #666;
                    line-height: 1.5;
                    margin: 0 0 14px;
                }
                .dash-template-use-btn {
                    flex: 1;
                    background: #6366f1;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .dash-template-use-btn:hover {
                    background: #4f46e5;
                }
                .dash-template-preview-btn {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    background: transparent;
                    color: #9ca3af;
                    border: 1px solid #374151;
                    padding: 10px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }
                .dash-template-preview-btn:hover {
                    color: #e5e7eb;
                    border-color: #6366f1;
                    background: rgba(99, 102, 241, 0.1);
                }

                /* New Design Modal */
                .dash-newdesign-modal {
                    background: #111827;
                    border-radius: 16px;
                    width: 95vw;
                    max-width: 1200px;
                    height: 90vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    border: 1px solid #1f2937;
                }
                .dash-newdesign-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 20px 24px;
                    border-bottom: 1px solid #1f2937;
                }
                .dash-newdesign-header h2 {
                    margin: 0;
                    font-size: 18px;
                    color: #f3f4f6;
                }
                .dash-newdesign-scratch {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 20px 24px;
                    margin: 16px 24px;
                    background: #1f2937;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 1px solid transparent;
                }
                .dash-newdesign-scratch:hover {
                    border-color: #6366f1;
                    background: rgba(99, 102, 241, 0.08);
                }
                .dash-newdesign-scratch-icon {
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                    background: rgba(99, 102, 241, 0.15);
                    color: #6366f1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                .dash-newdesign-templates {
                    flex: 1;
                    overflow-y: auto;
                    padding: 0 24px 24px;
                }
                .dash-newdesign-template-row {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 14px;
                    border-radius: 10px;
                    border: 1px solid #1f2937;
                    margin-bottom: 10px;
                    transition: border-color 0.2s;
                }
                .dash-newdesign-template-row:hover {
                    border-color: #374151;
                }
                .dash-newdesign-template-thumb {
                    width: 100px;
                    height: 64px;
                    border-radius: 6px;
                    overflow: hidden;
                    flex-shrink: 0;
                    position: relative;
                    background: #1f2937;
                }
                .dash-newdesign-template-thumb iframe {
                    width: 400%;
                    height: 400%;
                    border: none;
                    transform: scale(0.25);
                    transform-origin: top left;
                    pointer-events: none;
                }
                .dash-newdesign-template-info {
                    flex: 1;
                    min-width: 0;
                }
                .dash-newdesign-template-actions {
                    display: flex;
                    gap: 8px;
                    flex-shrink: 0;
                }
                .dash-newdesign-preview-iframe {
                    flex: 1;
                    border: none;
                    width: 100%;
                    min-height: 0;
                }

                /* Template Preview Modal */
                .dash-template-modal-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0,0,0,0.7);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 24px;
                }
                .dash-template-modal {
                    background: white;
                    border-radius: 16px;
                    width: 100%;
                    max-width: 1200px;
                    height: 85vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .dash-template-modal-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 16px 20px;
                    border-bottom: 1px solid #e5e5e5;
                }
                .dash-template-modal-header h3 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                }
                .dash-template-modal-actions {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                }
                .dash-template-modal-actions .dash-template-use-btn {
                    width: auto;
                    padding: 8px 20px;
                }
                .dash-template-modal-close {
                    background: none;
                    border: 1px solid #e5e5e5;
                    border-radius: 8px;
                    padding: 6px;
                    cursor: pointer;
                    color: #666;
                    display: flex;
                    align-items: center;
                    transition: all 0.2s;
                }
                .dash-template-modal-close:hover {
                    border-color: #999;
                    color: #333;
                }
                .dash-template-modal-iframe {
                    flex: 1;
                    width: 100%;
                    border: none;
                }
            `}</style>
        </div>
    );
};

export default Dashboard;
