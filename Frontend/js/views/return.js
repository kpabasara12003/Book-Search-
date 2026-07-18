// ─── Return Book flow (no login required) ──────────────────────────────────

const ReturnView = {
    render() {
        UI.render(`
      <div class="view-container flex flex-col items-center justify-center min-h-full px-16 py-12 text-center relative overflow-hidden">
        
        <!-- Large animated background scanner ring -->
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-cyan-500/10 rounded-full animate-[spin_8s_linear_infinite_reverse] flex items-center justify-center -z-10">
           <!-- Scanner sweeping beam -->
           <div class="absolute w-[400px] h-2 bg-gradient-to-r from-teal-500/0 via-teal-400/30 to-teal-500/0 left-1/2 top-1/2 origin-left -translate-y-1/2 rounded-full pulse-ring"></div>
        </div>

        <div class="w-full max-w-2xl mb-8 relative z-10">
          <button class="btn btn-ghost text-green-400/70 gap-2 absolute left-0" onclick="App.navigate(STATE.student ? 'dashboard' : 'home')">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
            Cancel Return
          </button>
        </div>

        <div class="glass-card p-12 rounded-3xl w-full max-w-2xl mt-8 relative z-10 border-t border-teal-500/30">
            <!-- Icon -->
            <div class="w-24 h-24 mx-auto mb-8 rounded-2xl bg-teal-500/20 border border-teal-400/30 flex items-center justify-center relative">
              <svg class="w-12 h-12 text-teal-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
            </div>

            <h2 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-100 to-teal-300 mb-4">Express Return</h2>
            <p class="text-teal-200/70 text-xl mb-10 leading-relaxed font-light">Self-service quick drop. Place the borrowed book on the scanner.</p>

            <div class="relative max-w-md mx-auto mb-8">
              <input id="return-nfc-input"
                type="text"
                class="kiosk-input w-full bg-black/40 text-center border-teal-500/40 focus:border-teal-400"
                placeholder="Scan Book NFC Tag..."
                autofocus
                autocomplete="off"
                onkeydown="if(event.key==='Enter') ReturnView.submit()"/>
            </div>

            <button class="btn w-full max-w-md mx-auto text-xl py-4 flex justify-center gap-3 bg-teal-600 hover:bg-teal-500 text-white border-0 shadow-lg shadow-teal-900/50" onclick="ReturnView.submit()">
               Return Book
            </button>
        </div>
      </div>
    `);

        setTimeout(() => document.getElementById('return-nfc-input')?.focus(), 100);
    },

    async submit() {
        const input = document.getElementById('return-nfc-input');
        const book_nfc = input?.value.trim();
        if (!book_nfc) return;

        UI.showLoading('Returning book...');
        try {
            const res = await API.returnBook(book_nfc);

            // Update local student active count if they happen to be logged in and returned their own book
            if (STATE.student) STATE.student.active_borrows = Math.max(0, STATE.student.active_borrows - 1);

            UI.hideLoading();

            const isLate = res.fine_issued;
            if (isLate) {
                if (STATE.student) STATE.student.is_blocked = true;
                // Warning fine UI
                await UI.confirm(
                    "Return Successful... but Overdue! ⚠️",
                    `<div class="text-orange-200 text-lg mb-2">The book was returned ${res.days_overdue} days late.</div>
             <div class="text-orange-400 font-bold mb-4 text-2xl p-4 bg-orange-950/50 border border-orange-500/40 rounded-2xl inline-block">Fine Issued: $${res.fine_amount.toFixed(2)}</div>
             <p class="text-green-300/60 text-sm max-w-sm mx-auto">Please settle the balance at the library helpdesk. Your account may be temporarily blocked for new borrows.</p>`,
                    "Understood",
                    "bg-orange-600 hover:bg-orange-500 text-white"
                );
            } else {
                // Standard success UI
                await UI.confirm(
                    "Return Complete! ✅",
                    `<div class="text-teal-100 text-lg">Thank you. The book has been successfully returned and recorded. You may drop it in the return slot.</div>`,
                    "Done",
                    "bg-teal-600 hover:bg-teal-500 text-white"
                );
            }

            App.navigate(STATE.student ? 'dashboard' : 'home');

        } catch (err) {
            UI.hideLoading();
            UI.showToast(err.message, 'error', 6000);
            input.value = '';
            input.focus();
        }
    }
};
