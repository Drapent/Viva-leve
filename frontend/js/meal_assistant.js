/**
 * VivaLeve - Assistente de Cardápio Semanal Inteligente
 * Sugestões balanceadas para Individual (com base no déficit calórico) ou Família (coletivo).
 * Permite trocar qualquer sugestão individualmente e reseta a cada nova semana.
 */

const MealAssistant = {
    mode: 'individual', // 'individual' | 'family'
    selectedDay: 'segunda',
    menuData: null,
    isLoading: false,

    dayKeys: ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo'],
    dayLabels: {
        'segunda': { short: 'Seg', full: 'Segunda-feira', emoji: '🌱' },
        'terca': { short: 'Ter', full: 'Terça-feira', emoji: '⚡' },
        'quarta': { short: 'Qua', full: 'Quarta-feira', emoji: '🥗' },
        'quinta': { short: 'Qui', full: 'Quinta-feira', emoji: '💪' },
        'sexta': { short: 'Sex', full: 'Sexta-feira', emoji: '🎉' },
        'sabado': { short: 'Sáb', full: 'Sábado', emoji: '☀️' },
        'domingo': { short: 'Dom', full: 'Domingo', emoji: '👑' }
    },

    mealLabels: {
        'breakfast': { name: 'Café da Manhã', icon: '🍳', color: 'amber' },
        'lunch': { name: 'Almoço Completo', icon: '🥗', color: 'emerald' },
        'snack': { name: 'Lanche da Tarde', icon: '🍎', color: 'cyan' },
        'dinner': { name: 'Jantar Leve', icon: '🍲', color: 'indigo' }
    },

    init() {
        this.selectTodayByDefault();
    },

    selectTodayByDefault() {
        const jsDay = new Date().getDay(); // 0 = domingo, 1 = segunda ... 6 = sábado
        const mapping = ['domingo', 'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado'];
        this.selectedDay = mapping[jsDay] || 'segunda';
    },

    async loadMenu(forceRegenerate = false) {
        this.isLoading = true;
        this.renderLoading();

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch(`/api/menu/weekly?user_id=${userId}&mode=${this.mode}&force_regenerate=${forceRegenerate}`);
            if (res.ok) {
                this.menuData = await res.json();
            } else {
                console.error("Falha ao carregar cardápio:", res.statusText);
            }
        } catch (err) {
            console.error("Erro na requisição do cardápio semanal:", err);
            if (typeof App !== 'undefined') App.showToast("Erro ao carregar cardápio semanal.", "error");
        } finally {
            this.isLoading = false;
            this.render();
        }
    },

    setMode(newMode) {
        if (this.mode === newMode) return;
        this.mode = newMode;
        this.loadMenu();
    },

    selectDay(dayKey) {
        this.selectedDay = dayKey;
        this.render();
    },

    async regenerateWeekly() {
        const confirmMsg = "Deseja gerar novas combinações de receitas para a semana inteira?";
        if (!confirm(confirmMsg)) return;

        await this.loadMenu(true);
        if (typeof App !== 'undefined') {
            App.showToast("🎲 Novo cardápio semanal gerado com sucesso!", "success");
            App.triggerConfetti();
        }
    },

    async swapDish(dayKey, mealType) {
        const cardEl = document.getElementById(`meal-card-${dayKey}-${mealType}`);
        if (cardEl) {
            cardEl.classList.add('opacity-50', 'scale-[0.98]');
        }

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/menu/weekly/swap-dish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    mode: this.mode,
                    day_key: dayKey,
                    meal_type: mealType
                })
            });

            const data = await res.json();
            if (data.success && data.menu) {
                this.menuData = data.menu;
                this.render();
                if (typeof App !== 'undefined') {
                    App.showToast(`🔄 Nova sugestão: ${data.dish.name}!`, "info");
                }
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao trocar prato.", "warning");
                this.render();
            }
        } catch (err) {
            console.error("Erro ao trocar prato:", err);
            if (typeof App !== 'undefined') App.showToast("Falha na comunicação com o servidor.", "error");
            this.render();
        }
    },

    async logToDiary(mealType, dishName) {
        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const currentDate = (typeof App !== 'undefined') ? App.currentDate : new Date().toISOString().split('T')[0];

            const res = await fetch('/api/menu/weekly/log-to-diary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    date: currentDate,
                    meal_type: mealType,
                    dish_name: dishName
                })
            });

            const data = await res.json();
            if (data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast(`🥗 "${dishName}" lançado no Diário de Hoje! (+10 pts)`, "success");
                    App.triggerConfetti();
                    if (typeof Diary !== 'undefined') {
                        Diary.load(currentDate);
                    }
                    if (typeof Streak !== 'undefined') {
                        Streak.load();
                    }
                }
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao lançar no diário.", "warning");
            }
        } catch (err) {
            console.error("Erro ao lançar refeição no diário:", err);
            if (typeof App !== 'undefined') App.showToast("Falha ao comunicar com o diário.", "error");
        }
    },

    renderLoading() {
        const container = document.getElementById('menu-assistant-content');
        if (!container) return;
        container.innerHTML = `
            <div class="py-16 text-center text-slate-400">
                <div class="text-4xl animate-bounce mb-3">🍽️</div>
                <h4 class="font-black text-slate-700 text-sm">Carregando cardápio semanal inteligente...</h4>
                <p class="text-xs text-slate-400 mt-1">Calculando calorias, macros e variedade brasileira.</p>
            </div>
        `;
    },

    render() {
        const container = document.getElementById('menu-assistant-content');
        if (!container) return;

        if (!this.menuData || !this.menuData.days) {
            container.innerHTML = `
                <div class="p-8 text-center bg-white rounded-3xl border border-slate-100 shadow-sm">
                    <p class="text-sm font-bold text-slate-600 mb-3">Nenhum cardápio disponível no momento.</p>
                    <button onclick="MealAssistant.loadMenu(true)" class="btn-primary-gradient px-4 py-2 rounded-2xl text-xs font-black">
                        Gerar Cardápio Agora 🎲
                    </button>
                </div>
            `;
            return;
        }

        const days = this.menuData.days;
        const currentDayData = days[this.selectedDay] || days['segunda'];
        const isFamily = this.mode === 'family';

        // Renderizar barra de dias da semana
        const dayPillsHtml = this.dayKeys.map(key => {
            const isSelected = key === this.selectedDay;
            const info = this.dayLabels[key];
            const jsDay = new Date().getDay();
            const mapping = ['domingo', 'segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado'];
            const isToday = mapping[jsDay] === key;

            return `
                <button onclick="MealAssistant.selectDay('${key}')"
                        class="flex-1 min-w-[50px] py-2.5 px-2 rounded-2xl text-center transition-all relative ${
                            isSelected
                                ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white font-black shadow-md shadow-emerald-500/25 scale-[1.03]'
                                : 'bg-white hover:bg-slate-100 text-slate-600 border border-slate-200/80 font-bold'
                        }">
                    <div class="text-[10px] uppercase tracking-wider ${isSelected ? 'text-emerald-100' : 'text-slate-400'}">${info.short}</div>
                    <div class="text-xs font-black mt-0.5">${info.emoji}</div>
                    ${isToday ? `<span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 border-2 border-white rounded-full"></span>` : ''}
                </button>
            `;
        }).join('');

        // Totais nutricionais do dia selecionado
        const totals = currentDayData.totals || { calories: 0, protein: 0, carbs: 0, fat: 0 };
        const targetCal = this.menuData.target_calories || 2000;

        // Renderizar refeições
        const mealTypes = ['breakfast', 'lunch', 'snack', 'dinner'];
        const mealsHtml = mealTypes.map(mType => {
            const dish = currentDayData.meals ? currentDayData.meals[mType] : null;
            if (!dish) return '';

            const mMeta = this.mealLabels[mType];
            const calPerPerson = isFamily ? Math.round(dish.calories / 3) : dish.calories;

            return `
                <div id="meal-card-${this.selectedDay}-${mType}"
                     class="bg-white rounded-3xl p-4 sm:p-5 border border-slate-100 shadow-sm hover:border-emerald-200 transition-all duration-300">
                    <div class="flex items-start justify-between gap-3 mb-3">
                        <div class="flex items-center gap-2.5">
                            <span class="w-10 h-10 rounded-2xl bg-emerald-50 text-xl flex items-center justify-center shrink-0">
                                ${mMeta.icon}
                            </span>
                            <div>
                                <span class="text-[10px] font-black uppercase tracking-wider text-slate-400">${mMeta.name}</span>
                                <h4 class="font-black text-sm sm:text-base text-slate-800 leading-snug">${dish.name}</h4>
                            </div>
                        </div>

                        <div class="text-right shrink-0">
                            <span class="inline-block px-3 py-1 rounded-full bg-emerald-100/80 text-emerald-800 text-xs font-black">
                                ${calPerPerson} kcal ${isFamily ? '<span class="text-[9px] font-bold text-emerald-700">/pessoa</span>' : ''}
                            </span>
                        </div>
                    </div>

                    <p class="text-xs text-slate-500 mb-3 bg-slate-50 p-2.5 rounded-2xl border border-slate-100">
                        ${dish.description || 'Opção rica em nutrientes e sabor brasileiro.'}
                    </p>

                    <!-- Detalhamento de Macros -->
                    <div class="grid grid-cols-3 gap-2 py-2 mb-3 text-center text-[11px] font-bold bg-slate-50/70 rounded-2xl border border-slate-100">
                        <div>
                            <span class="text-slate-400 block text-[9px] uppercase font-black">Proteína</span>
                            <span class="text-rose-700">${isFamily ? Math.round(dish.protein / 3) : dish.protein}g</span>
                        </div>
                        <div>
                            <span class="text-slate-400 block text-[9px] uppercase font-black">Carbo</span>
                            <span class="text-amber-700">${isFamily ? Math.round(dish.carbs / 3) : dish.carbs}g</span>
                        </div>
                        <div>
                            <span class="text-slate-400 block text-[9px] uppercase font-black">Gordura</span>
                            <span class="text-cyan-700">${isFamily ? Math.round(dish.fat / 3) : dish.fat}g</span>
                        </div>
                    </div>

                    <!-- Botões de Ação Interativa -->
                    <div class="flex items-center gap-2">
                        <button onclick="MealAssistant.swapDish('${this.selectedDay}', '${mType}')"
                                class="flex-1 py-2.5 px-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-black text-xs transition flex items-center justify-center gap-1.5"
                                title="Pedir outra sugestão de refeição">
                            <span>🔄</span>
                            <span>Trocar Prato</span>
                        </button>

                        <button onclick="MealAssistant.logToDiary('${mType}', '${dish.name.replace(/'/g, "\\'")}')"
                                class="flex-1 py-2.5 px-3 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs shadow-md shadow-emerald-500/20 transition flex items-center justify-center gap-1.5"
                                title="Registrar no Diário de Hoje">
                            <span>➕</span>
                            <span>Lançar no Diário</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Se for fim de semana e houver ideia de Dia do Lixo
        let weekendCheatHtml = '';
        if (currentDayData.weekend_cheat_idea) {
            const cheat = currentDayData.weekend_cheat_idea;
            weekendCheatHtml = `
                <div class="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 rounded-3xl p-5 text-white shadow-lg shadow-orange-500/20 mt-4 relative overflow-hidden">
                    <div class="absolute -right-4 -bottom-4 text-7xl opacity-20 select-none pointer-events-none">🍕</div>
                    <div class="flex items-center gap-3 mb-2">
                        <span class="text-2xl">🎉</span>
                        <div>
                            <span class="text-[10px] font-black uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-full">Sugestão de Refeição Livre</span>
                            <h4 class="font-black text-base text-white">${cheat.name}</h4>
                        </div>
                    </div>
                    <p class="text-xs text-amber-100 mb-3">${cheat.description}</p>
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-black bg-black/20 px-3 py-1 rounded-xl">~${cheat.calories} kcal estimada</span>
                        <button onclick="App.switchTab('dia-lixo')" class="px-3.5 py-1.5 rounded-xl bg-white text-orange-800 text-xs font-black shadow transition hover:bg-amber-50">
                            Ver Dicas no Dia do Lixo 🍔
                        </button>
                    </div>
                </div>
            `;
        }

        container.innerHTML = `
            <!-- Seletor de Modo: Individual vs Família -->
            <div class="bg-white p-2 rounded-2xl border border-slate-200/80 shadow-sm flex items-center gap-2 mb-4">
                <button onclick="MealAssistant.setMode('individual')"
                        class="flex-1 py-2.5 px-3 rounded-xl text-xs font-black transition flex items-center justify-center gap-2 ${
                            !isFamily
                                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-500/20'
                                : 'text-slate-600 hover:bg-slate-100'
                        }">
                    <span>👤</span>
                    <span>Individual (Déficit Calórico)</span>
                </button>
                <button onclick="MealAssistant.setMode('family')"
                        class="flex-1 py-2.5 px-3 rounded-xl text-xs font-black transition flex items-center justify-center gap-2 ${
                            isFamily
                                ? 'bg-teal-600 text-white shadow-md shadow-teal-500/20'
                                : 'text-slate-600 hover:bg-slate-100'
                        }">
                    <span>👨‍👩‍👧‍👦</span>
                    <span>Família (Receitas Coletivas)</span>
                </button>
            </div>

            <!-- Navegação pelos Dias da Semana -->
            <div class="flex items-center gap-1.5 sm:gap-2 overflow-x-auto pb-2 mb-4 no-scrollbar">
                ${dayPillsHtml}
            </div>

            <!-- Resumo Nutricional do Dia Selecionado -->
            <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 rounded-3xl p-4 sm:p-5 text-white shadow-md mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <span class="text-[10px] font-black uppercase tracking-wider text-emerald-200">
                        ${this.dayLabels[this.selectedDay]?.full || 'Dia'} ${isFamily ? '• Porção Família (3 a 4 pessoas)' : '• Meta Individual'}
                    </span>
                    <h3 class="text-base sm:text-lg font-black text-white">Planejamento do Dia</h3>
                    <p class="text-xs text-emerald-100 mt-0.5">
                        Total planejado: <b>${totals.calories} kcal</b> ${!isFamily ? `(Sua meta: ${targetCal} kcal)` : ''}
                    </p>
                </div>
                <div class="flex items-center gap-2 text-xs font-black shrink-0">
                    <span class="bg-white/15 px-3 py-1.5 rounded-xl border border-white/20">🥩 ${totals.protein}g P</span>
                    <span class="bg-white/15 px-3 py-1.5 rounded-xl border border-white/20">🌾 ${totals.carbs}g C</span>
                    <span class="bg-white/15 px-3 py-1.5 rounded-xl border border-white/20">🥑 ${totals.fat}g G</span>
                </div>
            </div>

            <!-- Lista de Pratos do Dia -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${mealsHtml}
            </div>

            <!-- Ideia de Dia do Lixo se houver -->
            ${weekendCheatHtml}

            <!-- Rodapé Informativo de Rotação Semanal -->
            <div class="mt-6 p-4 rounded-3xl bg-slate-100 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600">
                <div class="flex items-center gap-2.5">
                    <span class="text-2xl">🔄</span>
                    <div>
                        <b>Cardápio Rotativo Semanal:</b>
                        <p class="text-[11px] text-slate-500">A cada nova semana, novas combinações são geradas para não enjoar da dieta.</p>
                    </div>
                </div>
                <button onclick="MealAssistant.regenerateWeekly()" class="px-4 py-2.5 rounded-2xl bg-white hover:bg-slate-50 text-emerald-700 font-black border border-slate-200 shadow-sm shrink-0 transition flex items-center justify-center gap-1.5">
                    <span>🎲</span>
                    <span>Sortear Nova Semana</span>
                </button>
            </div>
        `;
    }
};

// Auto-inicializar se carregado
if (typeof window !== 'undefined') {
    window.MealAssistant = MealAssistant;
    MealAssistant.init();
}
