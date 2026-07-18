// ─── Borrow Book flow ────────────────────────────────────────────────────────

const BorrowView = {
    render() {
        if (!STATE.student) return App.navigate('home');

        UI.render(`
      <div class="view-container flex flex-col items-center justify-center min-h-full px-16 py-12 text-center relative overflow-hidden">
        
        <!-- Large animated background scanner ring -->
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] border border-green-500/10 rounded-full animate-[spin_10s_linear_infinite] flex items-center justify-center -z-10">
           <div class="w-[600px] h-[600px] border border-green-400/10 rounded-full flex items-center justify-center">
              <div class="w-[400px] h-[400px] border border-green-300/10 rounded-full"></div>
           </div>
           <!-- Scanner sweeping beam -->
           <div class="absolute w-[400px] h-2 bg-gradient-to-r from-emerald-500/0 via-emerald-400/30 to-emerald-500/0 left-1/2 top-1/2 origin-left -translate-y-1/2 rounded-full pulse-ring"></div>
        </div>

        <div class="w-full max-w-2xl mb-8 relative z-10">
          <button class="btn btn-ghost text-green-400/70 gap-2 absolute left-0" onclick="App.navigate('dashboard')">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
            Cancel Borrowing
          </button>
        </div>

        <div class="glass-card p-12 rounded-3xl w-full max-w-2xl mt-8 relative z-10">
            <!-- Icon -->
            <div class="w-24 h-24 mx-auto mb-8 rounded-2xl bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center relative">
              <svg class="w-12 h-12 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4"/></svg>
              <div class="absolute -right-2 -bottom-2 w-8 h-8 rounded-full bg-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/50 animate-bounce">
                 <svg class="w-4 h-4 text-emerald-950" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
              </div>
            </div>

            <h2 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-100 to-emerald-300 mb-4">Place Book on Scanner</h2>
            <p class="text-green-400/70 text-xl mb-10 leading-relaxed font-light">Scan the NFC tag located on the back cover of the book you wish to borrow.</p>

            <div class="relative max-w-md mx-auto mb-8">
              <input id="borrow-nfc-input"
                type="text"
                class="kiosk-input w-full bg-black/40 text-center"
                placeholder="Scan Book NFC Tag..."
                autofocus
                autocomplete="off"
                onkeydown="if(event.key==='Enter') BorrowView.submit()"/>
            </div>

            <button class="btn btn-primary w-full max-w-md mx-auto text-xl py-4 flex justify-center gap-3" onclick="BorrowView.submit()">
               Checkout Book
               <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </button>
        </div>
      </div>
    `);

        setTimeout(() => document.getElementById('borrow-nfc-input')?.focus(), 100);
    },

    async submit() {
        const input = document.getElementById('borrow-nfc-input');
        const book_nfc = input?.value.trim();
        if (!book_nfc) return;

        UI.showLoading('Checking out book...');
        try {
            const res = await API.borrowBook(STATE.student.nfc_uid, book_nfc);

            // Update local student active count
            STATE.student.active_borrows++;

            UI.hideLoading();

            // Show success modal then go to dashboard
            await UI.confirm(
                "Success! 🎉",
                `<div class="text-green-100 text-lg mb-2">You have successfully borrowed this book.</div>
          <div class="text-green-400/80 mb-6 bg-green-950/40 p-4 rounded-xl border border-green-500/20 inline-block font-mono">Due back on <b>${UI.fmtDate(res.due_date)}</b></div>`,
                "Awesome!",
                "bg-emerald-600 hover:bg-emerald-500 text-white"
            );

            App.navigate('dashboard');

        } catch (err) {
            UI.hideLoading();
            UI.showToast(err.message, 'error', 6000);
            input.value = '';
            input.focus();
        }
    }
};
