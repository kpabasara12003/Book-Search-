// ─── Student Identify View ────────────────────────────────────────────────────

const IdentifyView = {
  render() {
    UI.render(`
      <div class="view-container flex flex-col items-center justify-center min-h-full px-16 py-12">
        <div class="ambient-orb orb-1"></div>

        <!-- Back -->
        <div class="w-full max-w-2xl mb-6">
          <button class="btn btn-ghost text-green-700/80 gap-2 hover:bg-green-100" onclick="App.navigate('home')">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Back to Home
          </button>
        </div>

        <!-- Card -->
        <div class="w-full max-w-2xl glass-card p-12 rounded-3xl text-center">
          <!-- Icon -->
          <div class="w-24 h-24 mx-auto mb-6 rounded-2xl bg-green-100 border border-green-300 flex items-center justify-center">
            <svg class="w-12 h-12 text-green-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
          </div>

          <h2 class="text-4xl font-bold text-green-900 mb-2">Identify Yourself</h2>
          <p class="text-green-800/70 text-lg mb-10">Enter your Student NFC Card ID to continue</p>

          <!-- NFC Input -->
          <div class="space-y-6">
            <div class="relative">
              <label class="block text-green-800 text-sm font-semibold uppercase tracking-wider mb-2 text-left">Student NFC Card ID</label>
              <input id="nfc-input"
                type="text"
                class="kiosk-input w-full bg-white/80"
                placeholder="e.g. NFC-STUDENT-001"
                autofocus
                autocomplete="off"
                onkeydown="if(event.key==='Enter') IdentifyView.submit()"/>
              <div class="absolute right-4 top-1/2 translate-y-1/2">
                <svg class="w-6 h-6 text-green-600/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1"/>
                </svg>
              </div>
            </div>

            <button class="btn btn-primary w-full text-xl py-5" onclick="IdentifyView.submit()">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Identify Me
            </button>
          </div>

          <!-- Hint -->
          <p class="text-green-700/70 text-sm mt-8">
            Having trouble? Please visit the library helpdesk.
          </p>
        </div>
      </div>
    `);

    setTimeout(() => document.getElementById('nfc-input')?.focus(), 100);
  },

  async submit() {
    const input = document.getElementById('nfc-input');
    const nfc_uid = input?.value.trim();
    if (!nfc_uid) { UI.showToast('Please enter your NFC Card ID.', 'warning'); return; }

    UI.showLoading('Identifying student…');
    try {
      const student = await API.identifyStudent(nfc_uid);
      STATE.setStudent(student);
      UI.hideLoading();
      App.navigate('dashboard');
    } catch (err) {
      UI.hideLoading();
      UI.showToast(err.message, 'error', 5000);
    }
  },
};
