// ─── Main App Entry Point ────────────────────────────────────────────────────

const App = {
    views: {
        home: HomeView,
        identify: IdentifyView,
        dashboard: DashboardView,
        search: SearchView,
        borrow: BorrowView,
        return: ReturnView
    },

    viewStack: [],

    navigate(viewName) {
        if (!this.views[viewName]) {
            console.warn(`View ${viewName} not found!`);
            return;
        }

        UI.scrollTop();
        this.viewStack.push(STATE.currentView);
        STATE.currentView = viewName;

        // Smooth transition
        const main = document.getElementById('main-content');
        if (main.firstElementChild) {
            main.firstElementChild.classList.remove('fade-in');
            main.firstElementChild.classList.add('fade-out');
            setTimeout(() => this.views[viewName].render(), 200);
        } else {
            this.views[viewName].render();
        }
    },

    goBack() {
        if (this.viewStack.length === 0) return this.navigate('home');
        const prev = this.viewStack.pop();
        STATE.currentView = prev;

        UI.scrollTop();
        const main = document.getElementById('main-content');
        if (main.firstElementChild) {
            main.firstElementChild.classList.add('fade-out');
            setTimeout(() => this.views[prev].render(), 200);
        } else {
            this.views[prev].render();
        }
    },

    logout() {
        STATE.clearStudent();
        this.viewStack = [];
        this.navigate('home');
        UI.showToast('You have been logged out.', 'success');
    },

    start() {
        console.log("App starting...");
        STATE.resetIdleTimer();
        this.navigate('home');

        // Prevent default context menus and pinching for true kiosk
        document.addEventListener('contextmenu', e => e.preventDefault());

        // Top bar time
        setInterval(() => {
            const d = document.getElementById('topbar-time');
            if (d) d.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }, 1000);
    }
};

window.onload = () => App.start();
