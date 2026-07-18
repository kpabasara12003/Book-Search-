
const API = {
    async _fetch(method, path, body = null) {
        const opts = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(`${CONFIG.API_BASE}${path}`, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
        return data;
    },

    // ── Students ───────────────────────────────────────────────────────────────
    identifyStudent(nfc_uid) {
        return this._fetch('POST', '/students/identify', { nfc_uid });
    },
    getStudentBorrows(student_id, active_only = false) {
        return this._fetch('GET', `/students/${student_id}/borrows?active_only=${active_only}`);
    },
    getStudentFines(student_id) {
        return this._fetch('GET', `/students/${student_id}/fines`);
    },

    // ── Books ──────────────────────────────────────────────────────────────────
    searchBooks(query, limit = 10, searchType = 'semantic', categoryId = null) {
        if (searchType === 'semantic') {
            const q = encodeURIComponent(query);
            return this._fetch('GET', `/books/search/semantic?query=${q}&limit=${limit}`);
        } else {
            let url = `/books/search/standard?limit=${limit}`;
            if (query) url += `&query=${encodeURIComponent(query)}`;
            if (categoryId) url += `&category_id=${categoryId}`;
            return this._fetch('GET', url);
        }
    },
    getCategories() {
        return this._fetch('GET', '/categories');
    },
    getBook(book_id) {
        return this._fetch('GET', `/books/${book_id}`);
    },
    getBookCopies(book_id) {
        return this._fetch('GET', `/books/${book_id}/copies`);
    },

    // ── Borrows ────────────────────────────────────────────────────────────────
    borrowBook(student_nfc_uid, copy_nfc_id) {
        return this._fetch('POST', '/borrows', { student_nfc_uid, copy_nfc_id });
    },
    returnBook(copy_nfc_id) {
        return this._fetch('POST', '/borrows/return', { copy_nfc_id });
    },
};
