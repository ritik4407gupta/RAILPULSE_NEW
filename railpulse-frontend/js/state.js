const STORAGE_KEY = 'railpulse.session';

const state = {
    session: null,
    selectedTrain: '',
    trainState: null,
    latestPrediction: null,
    health: null,
};

export function getState() {
    return state;
}

export function restoreSession() {
    try {
        const stored = sessionStorage.getItem(STORAGE_KEY) || localStorage.getItem(STORAGE_KEY);
        state.session = stored ? JSON.parse(stored) : null;
    } catch {
        state.session = null;
    }
    return state.session;
}

export function setSession(session, remember = false) {
    clearSessionStorage();
    state.session = session;
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession() {
    clearSessionStorage();
    state.session = null;
    state.selectedTrain = '';
    state.trainState = null;
    state.latestPrediction = null;
}

function clearSessionStorage() {
    sessionStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY);
}

export function setTrainContext(trainNumber, trainState = null, prediction = null) {
    state.selectedTrain = trainNumber || '';
    state.trainState = trainState;
    state.latestPrediction = prediction;
}