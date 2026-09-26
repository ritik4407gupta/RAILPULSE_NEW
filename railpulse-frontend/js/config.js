export const CONFIG = Object.freeze({
    apiBaseUrl: window.RAILPULSE_API_BASE_URL || 'http://localhost:8000/api/v1',
    healthPollMs: 30000,
    requestTimeoutMs: 12000,
});