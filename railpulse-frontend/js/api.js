import { CONFIG } from './config.js';
import { clearSession, getState } from './state.js';

export class ApiError extends Error {
    constructor(message, status = 0, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.details = details;
    }
}

function token() {
    return getState().session?.accessToken || '';
}

function normalizeDetail(detail, fallback) {
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg || item.message).filter(Boolean).join('. ');
    return fallback;
}

async function request(path, options = {}) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs || CONFIG.requestTimeoutMs);
    const headers = { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
    if (token()) headers.Authorization = `Bearer ${token()}`;

    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}${path}`, { ...options, headers, signal: controller.signal });
        const contentType = response.headers.get('content-type') || '';
        const payload = contentType.includes('json') ? await response.json() : await response.text();
        if (!response.ok) {
            if (response.status === 401) clearSession();
            const mapped = {
                401: 'Your session has expired. Please sign in again.',
                403: 'You do not have permission to perform this operation.',
                404: 'Train is not currently available in the live feed.',
                422: 'Some train information is invalid. Please try again.',
                500: 'RailPulse could not complete the request. Please check the backend service.',
            };
            const fallback = mapped[response.status] || `Request failed (${response.status}).`;
            throw new ApiError(normalizeDetail(payload?.detail, fallback), response.status, payload);
        }
        return payload;
    } catch (error) {
        if (error.name === 'AbortError') throw new ApiError('The request timed out. Check the backend and retry.', 408);
        if (error instanceof ApiError) throw error;
        throw new ApiError('RailPulse could not reach the FastAPI backend.', 0);
    } finally {
        window.clearTimeout(timeout);
    }
}

export const api = {
    get: (path, options = {}) => request(path, { ...options, method: 'GET' }),
    post: (path, body, options = {}) => request(path, { ...options, method: 'POST', body: JSON.stringify(body) }),
    put: (path, body, options = {}) => request(path, { ...options, method: 'PUT', body: JSON.stringify(body) }),
    del: (path, options = {}) => request(path, { ...options, method: 'DELETE' }),
};