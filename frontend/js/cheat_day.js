/**
 * VivaLeve - Sistema do Dia do Lixo & Banco Calórico Semanal
 */

const CheatDay = {
    data: null,

    async load() {
        // 1. Render instantâneo de cache local
        try {
            const cached = localStorage.getItem('vivaleve_cheat_day');
            if (cached) {
                this.data = JSON.parse(cached);
                this.render();
            }
        } catch (e) {}

        // 2. Busca atualizada em segundo plano
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/cheat-day?user_id=${userId}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.data = data;
                    localStorage.setItem('vivaleve_cheat_day', JSON.stringify(data));
                    this.render();
                }
            }
        } catch (err) {
            console.warn("Dia do Lixo em modo offline.");
        }
    },

    render() {
        if (!this.data) return;

        const {
            cheat_mode_active,
            meals_allowed_per_week,
            meals_used_this_week,
            meals_remaining,
            daily_bank_saving_kcal,
            adjusted_daily_target_kcal,
            normal_daily_target_kcal,
            banked_calories_pool,
            cheat_day_calorie_allowance,
            recent_logs,
            damage_control_checklist
        } = this.data;

        // Toggle do Modo Dia do Lixo
        const toggleBtn = document.getElementById('cheat-mode-toggle-btn');
        const modeBadge = document.getElementById('cheat-mode-status-badge');

        if (toggleBtn) {
            if (cheat_mode_active) {
                toggleBtn.className = "w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:opacity-95 text-white font-black text-sm sm:text-base shadow-lg shadow-amber-500/35 flex items-center justify-center gap-3 transition-all";
                toggleBtn.innerHTML = `<span>🎉</span> <span>MODO DIA DO LIXO ATIVADO (Clique para Finalizar)</span>`;
            } else {
                toggleBtn.className = "w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-500 hover:opacity-95 text-white font-extrabold text-sm sm:text-base shadow-md shadow-orange-500/25 flex items-center justify-center gap-3 transition-all";
                toggleBtn.innerHTML = `<span>🍔</span> <span>Ativar Modo Dia do Lixo Hoje</span>`;
            }
        }

        if (modeBadge) {
            if (cheat_mode_active) {
                modeBadge.className = "px-3 py-1 bg-amber-100 text-amber-800 font-bold rounded-full text-xs animate-pulse";
                modeBadge.textContent = "🔥 Modo Livre Ativo Hoje";
            } else {
                modeBadge.className = "px-3 py-1 bg-slate-100 text-slate-600 font-medium rounded-full text-xs";
                modeBadge.textContent = "Modo Foco / Dieta Padrão";
            }
        }

        // Estatísticas do Banco Calórico
        const poolEl = document.getElementById('cheat-bank-pool');
        const allowanceEl = document.getElementById('cheat-allowance-kcal');
        const quotaEl = document.getElementById('cheat-quota-display');
        const dailySavingEl = document.getElementById('cheat-daily-saving');
        const adjustedTargetEl = document.getElementById('cheat-adjusted-target');

        if (poolEl) poolEl.textContent = `+${Math.round(banked_calories_pool)} kcal`;
        if (allowanceEl) allowanceEl.textContent = `${Math.round(cheat_day_calorie_allowance)} kcal`;
        if (quotaEl) quotaEl.textContent = `${meals_used_this_week} de ${meals_allowed_per_week} usadas (${meals_remaining} restantes)`;
        if (dailySavingEl) dailySavingEl.textContent = `${Math.round(daily_bank_saving_kcal)} kcal/dia`;
        if (adjustedTargetEl) adjustedTargetEl.textContent = `${Math.round(adjusted_daily_target_kcal)} kcal`;

        // Checklist de Redução de Danos
        this.renderChecklist(damage_control_checklist);

        // Histórico de Refeições Livres
        this.renderHistory(recent_logs);
    },

    renderChecklist(checklist) {
        const container = document.getElementById('cheat-damage-control-list');
        if (!container || !checklist) return;

        // Carregar estado salvo localmente para a data atual
        const savedState = JSON.parse(localStorage.getItem(`damage_control_${App.currentDate}`) || '{}');

        container.innerHTML = checklist.map(item => {
            const isChecked = !!savedState[item.id];
            return `
                <label class="flex items-start gap-3 p-3 bg-white rounded-xl border border-slate-100 hover:border-amber-200 transition-all cursor-pointer select-none">
                    <input type="checkbox" onchange="CheatDay.toggleCheckItem('${item.id}', this.checked)" 
                           class="mt-1 w-5 h-5 rounded text-amber-500 focus:ring-amber-400 border-slate-300" 
                           ${isChecked ? 'checked' : ''}>
                    <div class="flex-1">
                        <div class="text-sm font-bold ${isChecked ? 'line-through text-slate-400' : 'text-slate-800'}">
                            ${item.title}
                        </div>
                        <p class="text-xs text-slate-500 mt-0.5">${item.desc}</p>
                    </div>
                </label>
            `;
        }).join('');
    },

    toggleCheckItem(itemId, checked) {
        const key = `damage_control_${App.currentDate}`;
        const savedState = JSON.parse(localStorage.getItem(key) || '{}');
        savedState[itemId] = checked;
        localStorage.setItem(key, JSON.stringify(savedState));
        this.load();
    },

    renderHistory(logs) {
        const container = document.getElementById('cheat-history-list');
        if (!container) return;

        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 text-slate-400 text-xs italic">
                    Nenhuma refeição livre registrada nesta semana. Parabéns pelo foco constante!
                </div>
            `;
            return;
        }

        container.innerHTML = logs.map(log => `
            <div class="p-3.5 bg-white rounded-xl border border-amber-100 shadow-sm flex items-center justify-between">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-base">🍕</span>
                        <span class="font-bold text-slate-800 text-sm">${log.title}</span>
                        ${log.restaurant_name ? `<span class="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">${log.restaurant_name}</span>` : ''}
                    </div>
                    <div class="text-xs text-slate-400 mt-1">Data: ${log.date} ${log.notes ? `• "${log.notes}"` : ''}</div>
                </div>
                <div class="text-right">
                    <div class="font-extrabold text-amber-600 text-sm">~${Math.round(log.estimated_calories)} kcal</div>
                    <div class="text-[10px] text-emerald-600 font-semibold">Refeição Livre</div>
                </div>
            </div>
        `).join('');
    },

    async toggleCheatMode() {
        if (!this.data) return;
        const willActivate = !this.data.cheat_mode_active;
        const userId = Auth.getUserId();

        try {
            const res = await fetch('/api/cheat-day/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, active: willActivate })
            });

            if (res.ok) {
                if (willActivate) {
                    App.showToast("🎉 Modo Dia do Lixo ATIVADO! Aproveite sua refeição livre!", "warning");
                } else {
                    App.showToast("Modo Dia do Lixo finalizado. De volta ao foco total!", "success");
                }
                await this.load();
                await Diary.load(App.currentDate);
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro ao alternar o modo do dia do lixo.", "error");
        }
    },

    openLogCheatModal() {
        const modal = document.getElementById('modal-log-cheat');
        if (modal) modal.classList.remove('hidden');
    },

    closeLogCheatModal() {
        const modal = document.getElementById('modal-log-cheat');
        if (modal) modal.classList.add('hidden');
    },

    async submitCheatMeal() {
        const titleInput = document.getElementById('cheat-meal-title');
        const restInput = document.getElementById('cheat-meal-restaurant');
        const calInput = document.getElementById('cheat-meal-calories');
        const notesInput = document.getElementById('cheat-meal-notes');

        const title = titleInput?.value.trim();
        const cal = parseFloat(calInput?.value) || 1200;

        if (!title) {
            App.showToast("Por favor dê um nome para sua refeição livre.", "warning");
            return;
        }

        const savedChecklist = JSON.parse(localStorage.getItem(`damage_control_${App.currentDate}`) || '{}');
        const userId = Auth.getUserId();

        try {
            const res = await fetch('/api/cheat-day/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    date: App.currentDate,
                    title: title,
                    restaurant_name: restInput?.value.trim() || "",
                    estimated_calories: cal,
                    damage_control: savedChecklist,
                    notes: notesInput?.value.trim() || ""
                })
            });

            if (res.ok) {
                App.showToast("Refeição livre registrada no histórico! Bom apetite!");
                this.closeLogCheatModal();
                this.load();
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro ao registrar refeição livre.", "error");
        }
    }
};
