// ─── Dashboard View (Student Profile/Home) ───────────────────────────────────

const DashboardView = {
  render() {
    if (!STATE.student) return App.navigate('home');
    const st = STATE.student;

    const blockedBanner = st.is_blocked
      ? `<div class="bg-red-50 border border-red-300 rounded-2xl p-4 mb-6 shadow-sm flex items-start gap-4">
           <svg class="w-8 h-8 text-red-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
           <div>
             <h3 class="text-xl font-bold text-red-800">Account Blocked</h3>
             <p class="text-red-700">You have pending fines. Please settle them at the library desk.</p>
           </div>
         </div>`
      : '';

    UI.render(`
      <div class="h-full flex flex-col p-8 fade-in">
        <!-- Top Nav -->
        <div class="flex justify-between items-center mb-10 bg-white/70 p-4 rounded-3xl border border-green-200 shadow-sm backdrop-blur-md">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full bg-green-100 border-2 border-green-300 flex items-center justify-center font-bold text-2xl text-green-800 shadow-lg shadow-green-200/50">
              ${st.full_name.charAt(0)}
            </div>
            <div>
              <h2 class="text-3xl font-bold text-green-900">${st.full_name}</h2>
              <p class="text-green-700 text-lg">${st.student_number}</p>
            </div>
          </div>
          <button class="btn btn-ghost text-red-600 hover:text-red-700 hover:bg-red-50 gap-2 border border-transparent hover:border-red-200" onclick="App.logout()">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
            Logout
          </button>
        </div>

        ${blockedBanner}

        <!-- Main Actions Grid -->
        <h3 class="text-2xl font-bold text-green-800 mb-6">What would you like to do?</h3>
        <div class="grid grid-cols-3 gap-6 mb-12">
          <!-- Action: Borrow -->
          <button class="action-card bg-white rounded-3xl p-8 border border-green-200 shadow-lg text-left transition-all hover:scale-[1.02] active:scale-95 group focus:outline-none" onclick="App.navigate('borrow')" ${st.is_blocked ? 'disabled' : ''}>
            <div class="w-16 h-16 rounded-2xl bg-emerald-100 border border-emerald-300 flex items-center justify-center mb-6 text-emerald-600 group-hover:bg-emerald-200 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            </div>
            <h4 class="text-2xl font-bold text-green-900 mb-2">Borrow a Book</h4>
            <p class="text-green-700/80 line-clamp-2">Place an available book on the scanner to borrow.</p>
          </button>
          
          <!-- Action: Return -->
          <button class="action-card bg-white rounded-3xl p-8 border border-green-200 shadow-lg text-left transition-all hover:scale-[1.02] active:scale-95 group focus:outline-none" onclick="App.navigate('return')">
            <div class="w-16 h-16 rounded-2xl bg-teal-100 border border-teal-300 flex items-center justify-center mb-6 text-teal-600 group-hover:bg-teal-200 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
            </div>
            <h4 class="text-2xl font-bold text-green-900 mb-2">Return a Book</h4>
            <p class="text-green-700/80 line-clamp-2">Return a book you have borrowed previously.</p>
          </button>

          <!-- Action: Search -->
          <button class="action-card bg-white rounded-3xl p-8 border border-green-200 shadow-lg text-left transition-all hover:scale-[1.02] active:scale-95 group focus:outline-none" onclick="App.navigate('search')">
            <div class="w-16 h-16 rounded-2xl bg-cyan-100 border border-cyan-300 flex items-center justify-center mb-6 text-cyan-600 group-hover:bg-cyan-200 group-hover:scale-110 transition-transform">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </div>
            <h4 class="text-2xl font-bold text-green-900 mb-2">Search Catalog</h4>
            <p class="text-green-700/80 line-clamp-2">Find books by title, author, or semantic topic.</p>
          </button>
        </div>

        <!-- Dashboard Stats & Lists -->
        <div class="grid grid-cols-2 gap-8 flex-1 min-h-0">
          
          <!-- Active Borrows Section -->
          <div class="bg-white/60 shadow-lg border border-green-200 rounded-3xl p-6 flex flex-col min-h-0">
            <div class="flex justify-between items-end mb-4 shrink-0">
              <h3 class="text-2xl font-bold text-green-900 flex items-center gap-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
                Active Borrows
              </h3>
              <span class="text-lg font-bold ${st.active_borrows >= CONFIG.MAX_BORROWS ? 'text-red-600' : 'text-green-700'}">${st.active_borrows} / ${CONFIG.MAX_BORROWS}</span>
            </div>
            <div id="dashboard-borrows-list" class="flex-1 overflow-y-auto space-y-4 pr-2 custom-scroll">
               <div class="text-center text-green-600/70 py-10">Loading active borrows...</div>
            </div>
          </div>

           <!-- Fines Section -->
          <div class="bg-white/60 shadow-lg border border-green-200 rounded-3xl p-6 flex flex-col min-h-0">
             <div class="flex justify-between items-end mb-4 shrink-0">
              <h3 class="text-2xl font-bold text-green-900 flex items-center gap-2">
                 <svg class="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                Fine History
              </h3>
            </div>
            <div id="dashboard-fines-list" class="flex-1 overflow-y-auto space-y-4 pr-2 custom-scroll">
               <div class="text-center text-green-600/70 py-10">Loading fines...</div>
            </div>
          </div>
        </div>
      </div>
    `);

    DashboardView.loadData(st.student_id);
  },

  async loadData(student_id) {
    try {
      const [borrows, fines] = await Promise.all([
        API.getStudentBorrows(student_id, true),
        API.getStudentFines(student_id)
      ]);

      const borrowsList = document.getElementById('dashboard-borrows-list');
      const finesList = document.getElementById('dashboard-fines-list');

      if (borrowsList) {
        if (borrows.length === 0) {
          borrowsList.innerHTML = `<div class="text-center text-green-600/70 py-12 text-lg">No active borrows.</div>`;
        } else {
          const html = await Promise.all(borrows.map(async b => {
            const now = new Date();
            const due = new Date(b.due_date);
            const isOverdue = now > due;

            return `
                  <div class="p-4 rounded-2xl bg-white border border-green-200 shadow-sm hover:border-green-400 transition-colors">
                     <div class="flex justify-between items-start mb-2">
                        <span class="text-sm text-green-700 bg-green-100 px-2 py-0.5 rounded font-mono border border-green-200">Borrow #${b.borrow_id}</span>
                        ${isOverdue ? '<span class="text-sm text-red-600 bg-red-100 px-2 py-0.5 rounded font-bold border border-red-200">OVERDUE</span>' : ''}
                     </div>
                     <div class="flex flex-col gap-1 text-sm text-green-900">
                        <div class="flex gap-2">
                          <span class="text-green-600 w-20 shrink-0">Borrowed:</span>
                          <span class="font-medium">${UI.fmtDateTime(b.borrowed_at)}</span>
                        </div>
                        <div class="flex gap-2">
                          <span class="text-green-600 w-20 shrink-0">Due Date:</span>
                          <span class="font-medium ${isOverdue ? 'text-red-600 font-bold' : ''}">${UI.fmtDate(b.due_date)}</span>
                        </div>
                     </div>
                  </div>
                `;
          }));
          borrowsList.innerHTML = html.join('');
        }
      }

      if (finesList) {
        if (fines.length === 0) {
          finesList.innerHTML = `<div class="text-center text-emerald-600/90 py-12 text-lg">No fines found. Excellent!</div>`;
        } else {
          const html = fines.map(f => {
            const colors = {
              pending: 'bg-red-50 text-red-700 border-red-200',
              paid: 'bg-emerald-50 text-emerald-700 border-emerald-200',
              waived: 'bg-gray-100 text-gray-700 border-gray-300',
            };
            return `
                  <div class="p-4 flex items-center justify-between rounded-2xl bg-white border border-green-200 shadow-sm">
                     <div>
                        <div class="text-xl font-bold text-green-900 mb-1">$${f.amount.toFixed(2)}</div>
                        <div class="text-sm text-green-600">Borrow #${f.borrow_id} • ${UI.fmtDate(f.created_at)}</div>
                     </div>
                     <span class="px-3 py-1 rounded-full text-sm font-bold border capitalize ${colors[f.status] || colors.pending}">${f.status}</span>
                  </div>
                `;
          });
          finesList.innerHTML = html.join('');
        }
      }

    } catch (err) {
      console.error(err);
      UI.showToast("Failed to load dashboard data.", "error");
    }
  }
};
