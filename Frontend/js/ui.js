// ─── UI Helpers ──────────────────────────────────────────────────────────────

const UI = {
    // ── Toast notifications ───────────────────────────────────────────────────
    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const colors = {
            success: 'border-emerald-200 bg-white text-emerald-800 shadow-xl',
            error: 'border-red-200 bg-white text-red-800 shadow-xl',
            warning: 'border-amber-200 bg-white text-amber-800 shadow-xl',
            info: 'border-green-200 bg-white text-green-800 shadow-xl',
        };
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ',
        };

        const toast = document.createElement('div');
        toast.className = `toast flex items-center gap-3 px-5 py-4 rounded-xl border z-[999] backdrop-blur-md text-base font-medium shadow-2xl ${colors[type] || colors.info}`;
        toast.innerHTML = `
      <span class="text-xl font-bold">${icons[type] || icons.info}</span>
      <span>${message}</span>
    `;
        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => toast.classList.add('toast-visible'));

        setTimeout(() => {
            toast.classList.remove('toast-visible');
            setTimeout(() => toast.remove(), 400);
        }, duration);
    },

    // ── Loading overlay ───────────────────────────────────────────────────────
    showLoading(msg = 'Processing…') {
        const el = document.getElementById('loading-overlay');
        if (el) {
            el.querySelector('.loading-msg').textContent = msg;
            el.classList.remove('hidden');
        }
    },
    hideLoading() {
        const el = document.getElementById('loading-overlay');
        if (el) el.classList.add('hidden');
    },

    // ── Render main content ───────────────────────────────────────────────────
    render(html) {
        const main = document.getElementById('main-content');
        if (main) main.innerHTML = html;
    },

    // ── Status badge ─────────────────────────────────────────────────────────
    statusBadge(status) {
        const c = STATUS_COLORS[status] || STATUS_COLORS.damaged;
        return `<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold border ${c.bg} ${c.text} ${c.border}">
      <span class="w-2 h-2 rounded-full ${c.dot} animate-pulse"></span>
      ${status.charAt(0).toUpperCase() + status.slice(1)}
    </span>`;
    },

    // ── Generic confirm dialog ────────────────────────────────────────────────
    async confirm(title, message, confirmText = 'Confirm', confirmClass = 'btn-primary') {
        return new Promise(resolve => {
            const overlay = document.getElementById('modal-overlay');
            const modal = document.getElementById('modal-box');
            modal.innerHTML = `
        <h2 class="text-2xl font-bold text-green-900 mb-3">${title}</h2>
        <p class="text-green-800/80 text-lg mb-8">${message}</p>
        <div class="flex gap-4 justify-end">
          <button id="modal-cancel" class="btn btn-ghost text-green-800 text-lg px-8 py-3 hover:bg-green-100">Cancel</button>
          <button id="modal-confirm" class="btn ${confirmClass} text-lg px-8 py-3">${confirmText}</button>
        </div>
      `;
            overlay.classList.remove('hidden');
            overlay.querySelector('.modal-inner').classList.add('modal-show');

            const hide = () => {
                overlay.querySelector('.modal-inner').classList.remove('modal-show');
                setTimeout(() => overlay.classList.add('hidden'), 250);
            };

            document.getElementById('modal-cancel').onclick = () => { hide(); resolve(false); };
            document.getElementById('modal-confirm').onclick = () => { hide(); resolve(true); };
        });
    },

    // ── Format date ──────────────────────────────────────────────────────────
    fmtDate(str) {
        if (!str) return '—';
        return new Date(str).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    },
    fmtDateTime(str) {
        if (!str) return '—';
        return new Date(str).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    },

    // ── Scroll to top of main ────────────────────────────────────────────────
    scrollTop() {
        const main = document.getElementById('main-content');
        if (main) main.scrollTo({ top: 0, behavior: 'smooth' });
    },
};
