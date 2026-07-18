// ─── Search View ─────────────────────────────────────────────────────────────

const SearchView = {
    render() {
        UI.render(`
      <div class="h-full flex flex-col p-8 fade-in relative">
        <div class="ambient-orb orb-3 opacity-30"></div>

        <!-- Header -->
        <div class="flex items-center gap-6 mb-4 shrink-0">
          <button class="btn btn-ghost p-3 rounded-xl border border-green-500/20 text-green-300 hover:text-green-100 hover:border-green-400/50 hover:bg-green-500/10" onclick="App.goBack()">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <div class="flex-1 relative">
            <input id="search-input" type="text" class="kiosk-input w-full pl-16 text-2xl h-20 shadow-2xl z-10 relative bg-black/50" placeholder="Search by title, author, or story summary..." autocomplete="off">
            <svg class="w-8 h-8 text-green-500/50 absolute left-5 top-6 z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          </div>
          <button class="btn btn-primary h-20 px-10 text-2xl" onclick="SearchView.performSearch()">
            Search
          </button>
        </div>

        <!-- Controls -->
        <div class="flex gap-4 mb-8 shrink-0 z-10 relative h-14">
           <!-- Modes toggle -->
           <div class="bg-black/50 p-1.5 rounded-xl border border-green-500/20 flex shadow-inner h-full shrink-0">
               <button id="mode-semantic" class="px-6 rounded-lg text-lg font-bold bg-green-600 shadow-md text-white transition-all flex items-center justify-center" onclick="SearchView.setMode('semantic')">
                   Semantic (AI)
               </button>
               <button id="mode-standard" class="px-6 rounded-lg text-lg font-bold text-green-400 hover:text-green-200 transition-all flex items-center justify-center opacity-70" onclick="SearchView.setMode('standard')">
                   Standard (SQL)
               </button>
           </div>
           
           <select id="search-category" class="kiosk-input h-full flex-1 bg-black/50 border-green-500/20 text-lg hidden">
              <option value="">All Categories</option>
           </select>
        </div>

        <!-- Results container -->
        <div class="flex-1 min-h-0 bg-black/20 rounded-3xl border border-green-500/10 p-6 flex flex-col relative z-10 overflow-hidden">
           <div class="flex justify-between items-center mb-4 shrink-0 px-2" id="search-header">
               <h3 class="text-xl font-bold text-green-300/60 uppercase tracking-wider">Search Results</h3>
               <span id="results-count" class="text-green-500/60 font-mono">0 found</span>
           </div>
           
           <div id="search-results-list" class="flex-1 overflow-y-auto custom-scroll space-y-4 px-2 pb-4">
              <div class="h-full flex flex-col items-center justify-center text-green-500/30 select-none">
                 <svg class="w-24 h-24 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                 <p class="text-2xl font-light">Type something to explore the library</p>
                 <p class="text-lg mt-2 font-mono">Powered by vector semantic search</p>
              </div>
           </div>
        </div>
      </div>
    `);

        STATE.searchMode = STATE.searchMode || 'semantic';
        this.setMode(STATE.searchMode, false);

        // Asynchronously load categories
        this.loadCategories();

        // Restore previous results
        if (STATE.searchResults.length > 0) {
            SearchView.renderResults(STATE.searchResults);
        }

        // Auto focus
        setTimeout(() => {
            const inp = document.getElementById('search-input');
            if (inp) {
                inp.focus();
                inp.addEventListener('keydown', e => { if (e.key === 'Enter') SearchView.performSearch(); });
            }
        }, 100);
    },

    setMode(mode, clear = true) {
        STATE.searchMode = mode;
        const sem = document.getElementById('mode-semantic');
        const std = document.getElementById('mode-standard');
        const cat = document.getElementById('search-category');

        if (mode === 'semantic') {
            sem.className = "px-6 rounded-lg text-lg font-bold bg-green-600 shadow-md text-white transition-all flex items-center justify-center";
            std.className = "px-6 rounded-lg text-lg font-bold text-green-400 hover:text-green-200 transition-all flex items-center justify-center opacity-70";
            cat.classList.add('hidden');
        } else {
            std.className = "px-6 rounded-lg text-lg font-bold bg-green-600 shadow-md text-white transition-all flex items-center justify-center";
            sem.className = "px-6 rounded-lg text-lg font-bold text-green-400 hover:text-green-200 transition-all flex items-center justify-center opacity-70";
            cat.classList.remove('hidden');
        }

        if (clear) {
            document.getElementById('search-results-list').innerHTML = `<div class="h-full flex flex-col items-center justify-center text-green-500/30 select-none">
                    <p class="text-2xl font-light">Ready to search using ${mode === 'semantic' ? 'AI Semantics' : 'Standard Text & Categories'}</p>
                 </div>`;
            document.getElementById('results-count').textContent = '0 found';
            STATE.searchResults = [];
        }
    },

    async loadCategories() {
        try {
            const cats = await API.getCategories();
            const sel = document.getElementById('search-category');
            if (!sel) return;
            cats.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.category_id;
                opt.textContent = c.category_name;
                sel.appendChild(opt);
            });
        } catch (err) {
            console.error("Failed to load categories", err);
        }
    },

    async performSearch() {
        const q = document.getElementById('search-input')?.value.trim();
        const cat = document.getElementById('search-category')?.value;
        const mode = STATE.searchMode;

        if (mode === 'semantic' && !q) return;
        if (mode === 'standard' && !q && !cat) {
            UI.showToast('Please enter a query or select a category for standard search.', 'info');
            return;
        }

        UI.showLoading('Searching knowledge...');
        try {
            const results = await API.searchBooks(q, 10, mode, cat);
            STATE.searchResults = results;
            this.renderResults(results);
        } catch (err) {
            UI.showToast(err.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

    renderResults(results) {
        document.getElementById('results-count').textContent = `${results.length} found`;
        const list = document.getElementById('search-results-list');

        if (results.length === 0) {
            list.innerHTML = `<div class="h-full flex items-center justify-center text-2xl text-orange-200/50 font-light">No matches found for that query.</div>`;
            return;
        }

        const html = results.map(book => `
      <div class="glass-card hover:border-green-400/50 p-6 rounded-2xl flex gap-6 cursor-pointer transition-all active:scale-[0.99] group overflow-hidden relative" onclick="SearchView.viewDetails(${book.book_id})">
         <!-- highlight flare -->
         <div class="absolute -inset-0 bg-gradient-to-r from-green-400/0 via-green-400/5 to-green-400/0 -translate-x-[150%] group-hover:animate-[shimmer_1.5s_infinite]"></div>

         <div class="w-16 h-24 bg-green-950/80 border border-green-500/30 rounded flex-shrink-0 flex flex-col items-center justify-center shadow-lg">
            <svg class="w-8 h-8 text-green-500/50 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
         </div>
         <div class="flex-1 min-w-0 flex flex-col justify-center">
            <h4 class="text-2xl font-bold text-white mb-1 truncate">${book.title}</h4>
            <div class="text-green-300/80 text-sm mb-3 truncate flex gap-3">
               <span><strong class="text-green-500 mr-1">By</strong> ${book.authors.length ? book.authors.join(', ') : 'Unknown'}</span>
               <span class="text-green-500/50">•</span>
               <span><strong class="text-green-500 mr-1">Year</strong> ${book.publication_year || 'Unknown'}</span>
            </div>
            
            <p class="text-green-100/60 text-sm line-clamp-2 leading-relaxed max-w-4xl">
               ${book.summary || book.subtitle || 'No description available for this book.'}
            </p>
         </div>
         <div class="flex flex-col justify-end items-end shrink-0 pl-4 border-l border-green-500/20">
            <div class="text-xs text-green-500/50 uppercase tracking-widest font-bold mb-1 mr-1">Available Copies</div>
            <div class="text-3xl font-black ${book.total_copies > 0 ? 'text-emerald-400' : 'text-red-400'} mr-1">${book.total_copies}</div>
         </div>
      </div>
    `).join('');

        list.innerHTML = html;
    },

    async viewDetails(book_id) {
        UI.showLoading('Loading book details...');
        try {
            const [book, copies] = await Promise.all([
                API.getBook(book_id),
                API.getBookCopies(book_id)
            ]);
            book.copies = copies;
            STATE.selectedBook = book;
            this.renderDetails(book);
        } catch (err) {
            UI.showToast(err.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

    renderDetails(book) {
        const copiesHtml = book.copies.length === 0 ?
            '<div class="p-6 text-center text-green-400/50 border border-green-500/10 rounded-2xl">No physical copies configured in the system.</div>' :
            book.copies.map(c => `
           <div class="border border-green-500/20 rounded-xl p-4 bg-black/40 flex justify-between items-center hover:bg-green-900/10">
              <div>
                 <div class="font-mono text-xs text-green-300/50 mb-1">NFC: ${c.nfc_id}</div>
                 <div class="text-green-100 font-bold">${c.location.floor_name} • ${c.location.section_name} • Shelf ${c.location.shelf_code}</div>
              </div>
              <div>${UI.statusBadge(c.status)}</div>
           </div>
        `).join('');

        // Open a full-screen modal directly over the search view
        const overlay = document.getElementById('modal-overlay');
        const modal = document.getElementById('modal-box');

        // Override the modal box classes to be huge for book detail
        modal.className = "modal-inner glass-card p-0 rounded-3xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl relative overflow-hidden transition-all duration-300 transform scale-95 opacity-0";

        modal.innerHTML = `
        <div class="flex-1 overflow-y-auto custom-scroll p-10 flex flex-col">
           <!-- Top strip -->
           <div class="flex gap-4 mb-4 items-center mb-8">
              <span class="px-3 py-1 bg-green-900/50 border border-green-500/30 rounded-full text-xs font-bold text-green-300 tracking-wider">${book.category_name}</span>
              ${book.isbn ? `<span class="px-2 py-1 flex items-center gap-2 font-mono text-xs text-green-500/70"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg> ISBN: ${book.isbn}</span>` : ''}
              <div class="flex-1 border-b border-green-900/50 self-center"></div>
              <button onclick="document.getElementById('modal-overlay').classList.add('hidden')" class="btn btn-ghost rounded-full w-12 h-12 p-0 flex items-center justify-center text-green-500 hover:text-white bg-green-900/40 border border-green-500/30">
                 <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
           </div>
           
           <h2 class="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-100 to-emerald-200 mb-2 leading-tight py-1">${book.title}</h2>
           ${book.subtitle ? `<h3 class="text-2xl text-green-300/80 font-light mb-4">${book.subtitle}</h3>` : ''}
           
           <div class="text-lg text-green-400 mb-8 font-medium">By <span class="text-green-200">${book.authors.length ? book.authors.join(', ') : 'Unknown'}</span></div>
           
           <div class="grid grid-cols-[1fr_350px] gap-12 flex-1">
              <div>
                 <h4 class="text-xl font-bold text-green-500/80 border-b border-green-500/20 pb-2 mb-4 uppercase tracking-widest text-sm">Summary</h4>
                 <p class="text-green-100/80 leading-relaxed text-lg mb-8 whitespace-pre-wrap">${book.summary || 'No summary available.'}</p>
                 
                 <div class="grid grid-cols-2 gap-4 bg-green-950/30 rounded-2xl border border-green-500/20 p-6 mt-auto">
                    <div><span class="text-green-500/60 block text-xs uppercase mb-1">Publisher</span> <span class="text-green-100">${book.publisher || '—'}</span></div>
                    <div><span class="text-green-500/60 block text-xs uppercase mb-1">Year</span> <span class="text-green-100">${book.publication_year || '—'}</span></div>
                    <div><span class="text-green-500/60 block text-xs uppercase mb-1">Pages</span> <span class="text-green-100">${book.pages || '—'}</span></div>
                    <div><span class="text-green-500/60 block text-xs uppercase mb-1">Language</span> <span class="text-green-100">${book.language || '—'}</span></div>
                 </div>
              </div>
              
              <div class="border-l border-green-500/20 pl-8 flex flex-col">
                 <h4 class="text-xl font-bold text-green-500/80 border-b border-green-500/20 pb-2 mb-4 uppercase tracking-widest text-sm flex justify-between items-end">
                    Copies & Locations
                    <span class="text-xs font-mono text-green-400 bg-green-900/50 px-2 py-0.5 rounded-full">${book.total_copies} total</span>
                 </h4>
                 <div class="flex-1 overflow-y-auto custom-scroll space-y-3 pr-2">
                    ${copiesHtml}
                 </div>
              </div>
           </div>
        </div>
     `;

        overlay.classList.remove('hidden');
        // Small delay for CSS transition trigger
        requestAnimationFrame(() => {
            modal.classList.add('modal-show');
        });

        // Hook into the overlay click to dismiss, then tear down
        const closeHandler = e => {
            if (e.target === overlay) {
                modal.classList.remove('modal-show');
                setTimeout(() => {
                    overlay.classList.add('hidden');
                    // Reset classes back to normal modal
                    modal.className = "modal-inner glass-card p-10 rounded-3xl w-full max-w-md shadow-2xl relative transition-all duration-300 transform scale-95 opacity-0";
                    overlay.removeEventListener('click', closeHandler);
                }, 250);
            }
        };
        overlay.addEventListener('click', closeHandler);
    }
};
