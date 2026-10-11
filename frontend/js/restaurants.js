/**
 * VivaLeve - Guia & Localizador de Restaurantes com Recomendações Duplas
 */

const Restaurants = {
    list: [],
    currentCuisine: 'Todos',
    userCoords: null,
    cardStates: {}, // Guarda se cada card está exibindo a aba 'diet' ou 'cheat'

    async load() {
        await this.fetchRestaurants();
    },

    async fetchRestaurants(searchQuery = '') {
        const container = document.getElementById('restaurants-list-container');
        // 1. Render instantâneo de cache local
        if (!this.list || this.list.length === 0) {
            try {
                const cached = localStorage.getItem('vivaleve_restaurants');
                if (cached) {
                    this.list = JSON.parse(cached);
                    this.render();
                }
            } catch (e) {}
        }

        if (!this.list || this.list.length === 0) {
            container.innerHTML = `
                <div class="py-12 text-center text-slate-400 text-sm">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mb-2"></div>
                    <div>Buscando restaurantes e recomendações...</div>
                </div>
            `;
        }

        let url = `/api/restaurants?cuisine=${encodeURIComponent(this.currentCuisine)}`;
        if (searchQuery) url += `&q=${encodeURIComponent(searchQuery)}`;
        if (this.userCoords) {
            url += `&lat=${this.userCoords.latitude}&lng=${this.userCoords.longitude}`;
        }

        try {
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    this.list = data;
                    localStorage.setItem('vivaleve_restaurants', JSON.stringify(data));
                    this.render();
                }
            }
        } catch (err) {
            if (!this.list || this.list.length === 0) {
                container.innerHTML = `
                    <div class="p-8 text-center text-slate-500 text-sm">
                        Modo Offline: Nenhum restaurante salvo em cache ainda. Conecte-se para sincronizar.
                    </div>
                `;
            }
        }
    },

    getUserLocation() {
        if (!navigator.geolocation) {
            App.showToast("Geolocalização não é suportada pelo seu navegador.", "warning");
            return;
        }

        const btn = document.getElementById('btn-get-location');
        if (btn) btn.innerHTML = `<span>🛰️</span> <span>Localizando...</span>`;

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                this.userCoords = {
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude
                };
                App.showToast("Localização obtida! Mostrando restaurantes próximos.", "info");
                if (btn) btn.innerHTML = `<span>📍</span> <span>Localização Ativa</span>`;
                this.fetchRestaurants();
            },
            (err) => {
                console.warn("Erro ao obter GPS:", err);
                App.showToast("Não foi possível obter o GPS. Usando busca geral.", "warning");
                if (btn) btn.innerHTML = `<span>📍</span> <span>Usar Meu GPS</span>`;
            },
            { timeout: 8000 }
        );
    },

    filterByCuisine(cuisine) {
        this.currentCuisine = cuisine;

        // Atualizar estilos dos badges
        document.querySelectorAll('.cuisine-filter-btn').forEach(btn => {
            if (btn.getAttribute('data-cuisine') === cuisine) {
                btn.className = "cuisine-filter-btn px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-600 text-white shadow-sm transition-all";
            } else {
                btn.className = "cuisine-filter-btn px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white text-slate-600 border border-slate-200 hover:border-emerald-300 transition-all";
            }
        });

        const searchInput = document.getElementById('restaurant-search-input');
        this.fetchRestaurants(searchInput ? searchInput.value : '');
    },

    setCardTab(restId, mode) {
        this.cardStates[restId] = mode;
        const dietContent = document.getElementById(`rest-${restId}-diet-content`);
        const cheatContent = document.getElementById(`rest-${restId}-cheat-content`);
        const dietBtn = document.getElementById(`rest-${restId}-tab-diet`);
        const cheatBtn = document.getElementById(`rest-${restId}-tab-cheat`);

        if (mode === 'diet') {
            if (dietContent) dietContent.classList.remove('hidden');
            if (cheatContent) cheatContent.classList.add('hidden');
            if (dietBtn) {
                dietBtn.className = "flex-1 py-1.5 text-xs font-bold rounded-lg bg-white text-emerald-700 shadow-sm transition-all";
            }
            if (cheatBtn) {
                cheatBtn.className = "flex-1 py-1.5 text-xs font-semibold rounded-lg text-slate-500 hover:text-slate-700 transition-all";
            }
        } else {
            if (dietContent) dietContent.classList.add('hidden');
            if (cheatContent) cheatContent.classList.remove('hidden');
            if (dietBtn) {
                dietBtn.className = "flex-1 py-1.5 text-xs font-semibold rounded-lg text-slate-500 hover:text-slate-700 transition-all";
            }
            if (cheatBtn) {
                cheatBtn.className = "flex-1 py-1.5 text-xs font-bold rounded-lg bg-amber-500 text-white shadow-sm transition-all";
            }
        }
    },

    render() {
        const container = document.getElementById('restaurants-list-container');
        if (!container) return;

        if (this.list.length === 0) {
            container.innerHTML = `
                <div class="py-12 text-center text-slate-400 text-sm">
                    Nenhum restaurante encontrado com os filtros selecionados.
                </div>
            `;
            return;
        }

        container.innerHTML = this.list.map(r => {
            const currentMode = this.cardStates[r.id] || 'diet';

            return `
                <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:border-slate-200 transition-all mb-5">
                    <div class="flex items-start justify-between gap-2 mb-2">
                        <div>
                            <div class="flex items-center gap-2">
                                <h3 class="font-extrabold text-slate-800 text-base">${r.name}</h3>
                                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-600">${r.cuisine}</span>
                            </div>
                            <p class="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                                <span>📍 ${r.address}</span>
                                ${r.distance_km !== null ? `<span class="font-semibold text-emerald-600">• ${r.distance_km} km de você</span>` : ''}
                            </p>
                        </div>
                        <div class="flex items-center gap-1 text-amber-500 text-xs font-bold bg-amber-50 px-2 py-1 rounded-lg">
                            <span>⭐</span> <span>${r.rating}</span>
                        </div>
                    </div>

                    ${r.tips ? `
                        <div class="p-2.5 bg-slate-50 rounded-xl text-xs text-slate-600 mb-3.5 flex items-start gap-2 border-l-2 border-emerald-500">
                            <span class="text-emerald-600 font-bold">💡 Dica Nutri:</span>
                            <span>${r.tips}</span>
                        </div>
                    ` : ''}

                    <!-- Seletor de Modo Dieta vs Dia do Lixo -->
                    <div class="flex bg-slate-100 p-1 rounded-xl mb-3">
                        <button id="rest-${r.id}-tab-diet" onclick="Restaurants.setCardTab(${r.id}, 'diet')" 
                                class="flex-1 py-1.5 text-xs ${currentMode === 'diet' ? 'font-bold rounded-lg bg-white text-emerald-700 shadow-sm' : 'font-semibold rounded-lg text-slate-500'} transition-all">
                            🟢 Opção Dieta (Foco)
                        </button>
                        <button id="rest-${r.id}-tab-cheat" onclick="Restaurants.setCardTab(${r.id}, 'cheat')" 
                                class="flex-1 py-1.5 text-xs ${currentMode === 'cheat' ? 'font-bold rounded-lg bg-amber-500 text-white shadow-sm' : 'font-semibold rounded-lg text-slate-500'} transition-all">
                            🔥 Opção Dia do Lixo
                        </button>
                    </div>

                    <!-- Conteúdo Opção Dieta -->
                    <div id="rest-${r.id}-diet-content" class="${currentMode === 'diet' ? '' : 'hidden'} space-y-2">
                        ${r.diet_dishes.map(d => `
                            <div class="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="font-bold text-slate-800 text-xs">${d.name}</span>
                                    <span class="font-extrabold text-emerald-600 text-xs">${d.calories} kcal</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mb-1.5 leading-relaxed">${d.desc}</p>
                                <div class="flex items-center justify-between text-[10px]">
                                    <span class="bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded">${d.tag || 'Fit'}</span>
                                    <span class="text-slate-400">P:${d.protein} • C:${d.carbs} • G:${d.fat}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Conteúdo Opção Dia do Lixo -->
                    <div id="rest-${r.id}-cheat-content" class="${currentMode === 'cheat' ? '' : 'hidden'} space-y-2">
                        ${r.cheat_dishes.map(d => `
                            <div class="p-3 bg-amber-50/50 rounded-xl border border-amber-200/80">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="font-bold text-slate-800 text-xs">${d.name}</span>
                                    <span class="font-extrabold text-amber-600 text-xs">~${d.calories} kcal</span>
                                </div>
                                <p class="text-[11px] text-slate-500 mb-1.5 leading-relaxed">${d.desc}</p>
                                ${d.damage_control ? `
                                    <div class="p-2 bg-white rounded-lg border border-amber-200/60 text-[11px] text-amber-900 mt-1">
                                        <b class="text-amber-700">🛡️ Redução de Danos:</b> ${d.damage_control}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    },

    openAiMenuModal() {
        const modal = document.getElementById('modal-ai-menu');
        if (modal) modal.classList.remove('hidden');
    },

    closeAiMenuModal() {
        const modal = document.getElementById('modal-ai-menu');
        if (modal) modal.classList.add('hidden');
    },

    async submitAiMenuAnalysis() {
        const restNameInput = document.getElementById('ai-menu-restaurant-name');
        const textInput = document.getElementById('ai-menu-text');
        const resultContainer = document.getElementById('ai-menu-result-container');
        const loadingEl = document.getElementById('ai-menu-loading');

        const restName = restNameInput?.value.trim();
        const menuText = textInput?.value.trim();

        if (!restName) {
            App.showToast("Informe o nome do restaurante.", "warning");
            return;
        }

        if (loadingEl) loadingEl.classList.remove('hidden');
        if (resultContainer) resultContainer.classList.add('hidden');

        try {
            const res = await fetch('/api/restaurants/ai-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ restaurant_name: restName, menu_text: menuText || "Cardápio variado padrão da casa" })
            });

            const data = await res.json();
            if (loadingEl) loadingEl.classList.add('hidden');

            if (data.success && resultContainer) {
                resultContainer.classList.remove('hidden');
                resultContainer.innerHTML = `
                    <div class="space-y-4 pt-3 border-t border-slate-100">
                        <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                            <h4 class="font-bold text-emerald-800 text-xs mb-2">🟢 Melhores Opções para Manter a Dieta:</h4>
                            ${data.diet_recommendations.map(d => `
                                <div class="mb-2 last:mb-0">
                                    <div class="flex justify-between font-semibold text-xs text-slate-800">
                                        <span>${d.name}</span>
                                        <span class="text-emerald-700 font-bold">${d.calories} kcal</span>
                                    </div>
                                    <p class="text-[11px] text-slate-500">${d.strategy}</p>
                                </div>
                            `).join('')}
                        </div>

                        <div class="p-3 bg-amber-50 rounded-xl border border-amber-200">
                            <h4 class="font-bold text-amber-800 text-xs mb-2">🔥 Melhores Opções para o Dia do Lixo:</h4>
                            ${data.cheat_recommendations.map(d => `
                                <div class="mb-2 last:mb-0">
                                    <div class="flex justify-between font-semibold text-xs text-slate-800">
                                        <span>${d.name}</span>
                                        <span class="text-amber-700 font-bold">~${d.calories} kcal</span>
                                    </div>
                                    <p class="text-[11px] text-slate-500">${d.damage_control}</p>
                                </div>
                            `).join('')}
                        </div>

                        ${data.general_tip ? `
                            <p class="text-xs text-slate-500 italic text-center">💡 ${data.general_tip}</p>
                        ` : ''}
                    </div>
                `;
            } else {
                App.showToast(data.message || "Não foi possível analisar o cardápio.", "error");
            }
        } catch (err) {
            console.error(err);
            if (loadingEl) loadingEl.classList.add('hidden');
            App.showToast("Falha na análise com a IA.", "error");
        }
    }
};

window.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('restaurant-search-input');
    if (searchInput) {
        let debounceTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                Restaurants.fetchRestaurants(e.target.value);
            }, 300);
        });
    }
});
