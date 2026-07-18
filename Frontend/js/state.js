// ─── Application State ───────────────────────────────────────────────────────

const STATE = {
    student: null,           // Currently identified student object
    searchResults: [],       // Latest book search results
    selectedBook: null,      // Book selected to view details
    currentView: 'home',     // Active view name
    idleTimer: null,
    sessionTimer: null,

    setStudent(data) {
        this.student = data;
        this.resetIdleTimer();
    },
    clearStudent() {
        this.student = null;
        this.searchResults = [];
        this.selectedBook = null;
    },
    resetIdleTimer() {
        clearTimeout(this.idleTimer);
        clearTimeout(this.sessionTimer);
        if (this.student) {
            this.idleTimer = setTimeout(() => {
                if (App && typeof App.navigate === 'function') {
                    UI.showToast('Session timed out due to inactivity.', 'warning');
                    setTimeout(() => App.navigate('home'), 1500);
                }
            }, CONFIG.IDLE_TIMEOUT_MS);
        }
    },
};

// Reset idle timer on any user interaction
document.addEventListener('click', () => STATE.resetIdleTimer());
document.addEventListener('touchstart', () => STATE.resetIdleTimer());
document.addEventListener('keydown', () => STATE.resetIdleTimer());
