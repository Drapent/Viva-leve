/**
 * VivaLeve - Sistema de Foguinho e Ofensiva (Estilo Duolingo & TikTok)
 */

const Streak = {
    streakData: null,

    async load() {
        // 1. Render instantâneo de cache local
        try {
            const cached = localStorage.getItem('vivaleve_streak');
            if (cached) {
                this.streakData = JSON.parse(cached);
                this.renderHeaderBadge();
            }
        } catch (e) {}

        // 2. Busca atualizada em segundo plano
        try {
            const userId = Auth.getUserId();
            const date = App.currentDate || new Date().toISOString().split('T')[0];
            const res = await fetch(`/api/gamification/streak?user_id=${userId}&date=${date}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.streakData = data;
                    localStorage.setItem('vivaleve_streak', JSON.stringify(data));
                    this.renderHeaderBadge();
                }
            }
        } catch (err) {
            // Silencioso em offline
        }
    },

    renderHeaderBadge() {
        if (!this.streakData) return;
        const badge = document.getElementById('streak-counter-badge');
        const btn = document.getElementById('btn-streak-flame');
        const count = this.streakData.current_streak || 0;

        if (badge) {
            badge.textContent = count === 1 ? '1 Dia' : `${count} Dias`;
        }

        if (btn) {
            if (count > 0) {
                btn.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-gradient-to-r from-amber-100 to-orange-100 text-orange-800 font-black text-xs transition border border-orange-300 shadow-sm hover:scale-105";
            } else {
                btn.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-slate-100 text-slate-500 font-bold text-xs transition border border-slate-200 hover:bg-slate-200";
            }
        }
    },

    openModal() {
        const modal = document.getElementById('modal-streak');
        if (!modal) return;

        this.renderModalDetails();
        modal.classList.remove('hidden');
    },

    closeModal() {
        const modal = document.getElementById('modal-streak');
        if (modal) modal.classList.add('hidden');
    },

    renderModalDetails() {
        if (!this.streakData) return;

        const countEl = document.getElementById('streak-modal-count');
        const titleEl = document.getElementById('streak-modal-title');
        const msgEl = document.getElementById('streak-modal-msg');
        const freezesEl = document.getElementById('streak-modal-freezes');
        const calendarEl = document.getElementById('streak-modal-calendar');

        const count = this.streakData.current_streak || 0;

        if (countEl) countEl.textContent = count;
        if (titleEl) titleEl.textContent = this.streakData.flame_title || 'Ofensiva VivaLeve';
        if (msgEl) msgEl.textContent = this.streakData.motivational_message || 'Mantenha sua chama acesa diariamente!';
        if (freezesEl) {
            freezesEl.textContent = `${this.streakData.freezes_remaining || 2}/2 Proteções Ativas`;
        }

        if (calendarEl && this.streakData.history_7_days) {
            calendarEl.innerHTML = this.streakData.history_7_days.map(d => `
                <div class="flex flex-col items-center">
                    <div class="w-10 h-10 rounded-2xl flex items-center justify-center text-sm font-black transition-all ${
                        d.is_lit 
                            ? 'flame-day-lit scale-105' 
                            : 'flame-day-unlit'
                    } ${d.is_today ? 'ring-2 ring-emerald-500 ring-offset-2' : ''}">
                        ${d.is_lit ? '🔥' : '•'}
                    </div>
                    <span class="text-[10px] font-bold mt-1 ${d.is_today ? 'text-emerald-700 font-black' : 'text-slate-500'}">
                        ${d.day_name}
                    </span>
                </div>
            `).join('');
        }
    }
};
