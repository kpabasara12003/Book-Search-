// ─── App Configuration ───────────────────────────────────────────────────────

const CONFIG = {
    API_BASE: 'http://localhost:8000',
    IDLE_TIMEOUT_MS: 60_000,   // Auto-return to home after 60s of inactivity
    SESSION_TIMEOUT_MS: 120_000, // Full session timeout 2 min
    FINE_PER_DAY: 10.00,
    MAX_BORROWS: 3,
    LOAN_DAYS: 14,
};

// Status colours (Tailwind classes)
const STATUS_COLORS = {
    available: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/40', dot: 'bg-emerald-400' },
    borrowed: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/40', dot: 'bg-amber-400' },
    lost: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/40', dot: 'bg-red-400' },
    damaged: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/40', dot: 'bg-orange-400' },
};
