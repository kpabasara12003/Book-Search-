// ─── Home / Idle Screen ───────────────────────────────────────────────────────

const HomeView = {
    render() {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

        UI.render(`
      <div class="home-screen flex flex-col items-center justify-center min-h-full text-center px-16 py-12 select-none">
        <!-- Ambient orbs -->
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
        <div class="ambient-orb orb-3"></div>

        <!-- Library Logo / Icon -->
        <div class="relative mb-8">
          <div class="w-32 h-32 rounded-3xl bg-gradient-to-br from-green-400/30 to-emerald-600/30 border border-green-400/40 flex items-center justify-center backdrop-blur-md shadow-2xl shadow-green-500/20">
            <svg class="w-16 h-16 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
          </div>
          <div class="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/50 pulse-ring"></div>
        </div>

        <!-- Heading -->
        <h1 class="text-6xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-green-300 via-emerald-300 to-teal-300 mb-3">
          University Library
        </h1>
        <p class="text-2xl text-green-400/70 font-light mb-1">Self-Service Kiosk</p>

        <!-- Date & Time -->
        <div class="mt-6 mb-12">
          <div class="text-5xl font-bold text-green-200 tracking-widest clock-display">${time}</div>
          <div class="text-lg text-green-400/60 mt-1">${dateStr}</div>
        </div>

        <!-- Main CTA -->
        <div class="nfc-card-cta w-full max-w-xl bg-gradient-to-r from-green-900/60 to-emerald-900/60 border border-green-500/30 rounded-3xl p-10 backdrop-blur-md shadow-2xl mb-10 cursor-pointer hover:border-green-400/60 hover:shadow-green-500/20 transition-all duration-300 group"
          onclick="App.navigate('identify')">
          <div class="flex flex-col items-center gap-4">
            <div class="w-20 h-20 rounded-2xl bg-green-500/20 border border-green-400/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <svg class="w-10 h-10 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0"/>
              </svg>
            </div>
            <div>
              <p class="text-2xl font-bold text-green-200">Tap to Get Started</p>
              <p class="text-green-400/70 text-base mt-1">Identify yourself with your student NFC card</p>
            </div>
            <div class="flex gap-2 mt-2">
              <span class="h-2 w-2 rounded-full bg-green-400 animate-bounce" style="animation-delay:0ms"></span>
              <span class="h-2 w-2 rounded-full bg-emerald-400 animate-bounce" style="animation-delay:120ms"></span>
              <span class="h-2 w-2 rounded-full bg-teal-400 animate-bounce" style="animation-delay:240ms"></span>
            </div>
          </div>
        </div>

        <!-- Quick return option -->
        <button class="btn btn-ghost text-green-400/70 text-lg gap-2 hover:text-green-300" onclick="App.navigate('return')">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/>
          </svg>
          Quick Book Return (no login needed)
        </button>
      </div>
    `);

        // Live clock
        HomeView._clockInterval = setInterval(() => {
            const el = document.querySelector('.clock-display');
            if (el) el.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            else clearInterval(HomeView._clockInterval);
        }, 1000);
    },
};
