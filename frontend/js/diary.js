/**
 * VivaLeve - Gerenciador do Diário Alimentar e Macros Coloridos
 */

const Diary = {
    data: null,
    currentMealType: 'lunch',
    selectedFood: null,

    async load(date) {
        // 1. RECUPERAÇÃO INSTANTÂNEA EM 0ms DO CACHE LOCAL:
        let hasLocal = false;
        try {
            const cached = localStorage.getItem('vivaleve_diary_' + date);
            if (cached) {
                this.data = JSON.parse(cached);
                hasLocal = true;
                this.render(); // Renderiza IMEDIATAMENTE em 0ms sem esperar a rede!
            }
        } catch (e) {}

        // Se ainda não houver dados gravados, renderiza esqueleto inicial
        if (!hasLocal && !this.data) {
            const targetCal = App.userProfile?.target_calories || 2000;
            this.data = {
                summary: {
                    consumed_calories: 0,
                    target_calories: targetCal,
                    remaining_calories: targetCal,
                    percentage: 0,
                    macros: {
                        protein: { consumed: 0, target: App.userProfile?.target_protein || 150 },
                        carbs: { consumed: 0, target: App.userProfile?.target_carbs || 200 },
                        fat: { consumed: 0, target: App.userProfile?.target_fat || 60 }
                    }
                },
                meals: {
                    breakfast: { name: "Café da Manhã", items: [], total_calories: 0 },
                    lunch: { name: "Almoço", items: [], total_calories: 0 },
                    snack: { name: "Lanche da Tarde", items: [], total_calories: 0 },
                    dinner: { name: "Jantar", items: [], total_calories: 0 },
                    extra: { name: "Ceia / Snacks", items: [], total_calories: 0 }
                },
                water: { consumed_ml: 0, target_ml: App.userProfile?.target_water || 2500 },
                cheat_mode_active: false
            };
            this.render();
        }

        // 2. SINCRONIZAÇÃO EM SEGUNDO PLANO COM O SERVIDOR:
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/diary?date=${date}&user_id=${userId}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.data = data;
                    localStorage.setItem('vivaleve_diary_' + date, JSON.stringify(data));
                    this.render(); // Atualiza suavemente com dados novos
                }
            }
        } catch (err) {
            // Em modo offline silencioso - dados locais já renderizados
        }
    },

    render() {
        if (!this.data) return;

        const { summary, meals, cheat_mode_active } = this.data;

        if (cheat_mode_active) {
            document.body.classList.add('cheat-mode-active');
            const cheatBanner = document.getElementById('diary-cheat-banner');
            if (cheatBanner) cheatBanner.classList.remove('hidden');
        } else {
            document.body.classList.remove('cheat-mode-active');
            const cheatBanner = document.getElementById('diary-cheat-banner');
            if (cheatBanner) cheatBanner.classList.add('hidden');
        }

        // Calorias
        const consumedEl = document.getElementById('calories-consumed');
        const targetEl = document.getElementById('calories-target');
        const remainingEl = document.getElementById('calories-remaining');
        const percentageBar = document.getElementById('calories-bar-fill');

        if (consumedEl) consumedEl.textContent = summary.consumed_calories;
        if (targetEl) targetEl.textContent = summary.target_calories;
        if (remainingEl) {
            remainingEl.textContent = summary.remaining_calories;
            if (summary.remaining_calories < 0 && !cheat_mode_active) {
                remainingEl.parentElement.classList.add('text-rose-500');
            } else {
                remainingEl.parentElement.classList.remove('text-rose-500');
            }
        }

        if (percentageBar) {
            const pct = Math.min(100, summary.percentage);
            percentageBar.style.width = `${pct}%`;
            if (cheat_mode_active) {
                percentageBar.className = "h-full bg-gradient-to-r from-amber-400 via-orange-400 to-amber-500 rounded-full transition-all duration-500";
            } else if (summary.remaining_calories < 0) {
                percentageBar.className = "h-full bg-gradient-to-r from-rose-500 to-red-600 rounded-full transition-all duration-500";
            } else {
                percentageBar.className = "h-full bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-500 rounded-full transition-all duration-500";
            }
        }

        // Medidor Circular Moderno (Gauge Ring)
        const gaugeCircle = document.getElementById('calorie-gauge-circle');
        const gaugePercent = document.getElementById('gauge-percent');
        if (gaugeCircle) {
            const circumference = 251.2;
            const pct = Math.min(100, Math.max(0, summary.percentage));
            const offset = circumference - (pct / 100) * circumference;
            gaugeCircle.style.strokeDashoffset = offset;
            if (cheat_mode_active) {
                gaugeCircle.setAttribute('stroke', '#f59e0b');
            } else if (summary.remaining_calories < 0) {
                gaugeCircle.setAttribute('stroke', '#f43f5e');
            } else {
                gaugeCircle.setAttribute('stroke', 'url(#calorieGradient)');
            }
        }
        if (gaugePercent) {
            gaugePercent.textContent = `${Math.round(summary.percentage)}%`;
        }

        // Macros Coloridos
        this.renderMacroBar('protein', summary.protein, 'bar-protein');
        this.renderMacroBar('carbs', summary.carbs, 'bar-carbs');
        this.renderMacroBar('fat', summary.fat, 'bar-fat');

        // Água
        this.renderWater(summary.water);

        // Refeições com novos estilos coloridos
        this.renderMeals(meals);
    },

    renderMacroBar(macroKey, data, barClass) {
        const consumedEl = document.getElementById(`${macroKey}-consumed`);
        const targetEl = document.getElementById(`${macroKey}-target`);
        const fillEl = document.getElementById(`${macroKey}-bar-fill`);

        if (consumedEl) consumedEl.textContent = `${data.consumed}g`;
        if (targetEl) targetEl.textContent = `${data.target}g`;

        if (fillEl) {
            const pct = Math.min(100, Math.round((data.consumed / data.target) * 100)) || 0;
            fillEl.style.width = `${pct}%`;
            fillEl.className = `h-full rounded-full transition-all duration-500 ${barClass}`;
        }
    },

    renderWater(waterData) {
        const valEl = document.getElementById('water-consumed-val');
        const targetEl = document.getElementById('water-target-val');
        const barEl = document.getElementById('water-bar-fill');

        if (valEl) valEl.textContent = `${waterData.consumed} ml`;
        if (targetEl) targetEl.textContent = `${waterData.target} ml`;

        if (barEl) {
            const pct = Math.min(100, Math.round((waterData.consumed / waterData.target) * 100)) || 0;
            barEl.style.width = `${pct}%`;
        }
    },

    renderMeals(meals) {
        const container = document.getElementById('meals-container');
        if (!container) return;

        const mealConfigs = {
            'breakfast': { title: "Café da Manhã", icon: "☕", cardClass: "meal-card-breakfast", btnColor: "bg-amber-100 text-amber-800 hover:bg-amber-200" },
            'lunch': { title: "Almoço", icon: "🥗", cardClass: "meal-card-lunch", btnColor: "bg-emerald-100 text-emerald-800 hover:bg-emerald-200" },
            'snack': { title: "Lanche da Tarde", icon: "🍎", cardClass: "meal-card-snack", btnColor: "bg-orange-100 text-orange-800 hover:bg-orange-200" },
            'dinner': { title: "Jantar", icon: "🍲", cardClass: "meal-card-dinner", btnColor: "bg-purple-100 text-purple-800 hover:bg-purple-200" },
            'extra': { title: "Ceia / Snacks", icon: "🌙", cardClass: "meal-card-extra", btnColor: "bg-sky-100 text-sky-800 hover:bg-sky-200" }
        };

        const mealOrder = ['breakfast', 'lunch', 'snack', 'dinner', 'extra'];

        container.innerHTML = mealOrder.map(mKey => {
            const meal = meals[mKey];
            const cfg = mealConfigs[mKey];
            const hasItems = meal.items && meal.items.length > 0;

            return `
                <div class="${cfg.cardClass} rounded-3xl p-5 shadow-sm hover:shadow-md transition-all mb-4">
                    <div class="flex items-center justify-between pb-3 border-b border-black/5">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl p-2 bg-white rounded-2xl shadow-sm">${cfg.icon}</span>
                            <div>
                                <h3 class="font-extrabold text-slate-800 text-sm sm:text-base">${cfg.title}</h3>
                                <p class="text-xs font-semibold text-slate-400">
                                    <span class="text-emerald-600 font-bold">${Math.round(meal.calories)} kcal</span> • P: ${meal.protein.toFixed(1)}g • C: ${meal.carbs.toFixed(1)}g • G: ${meal.fat.toFixed(1)}g
                                </p>
                            </div>
                        </div>
                        <button onclick="Diary.openAddModal('${mKey}')" class="px-3.5 py-1.5 rounded-xl ${cfg.btnColor} text-xs font-extrabold flex items-center gap-1 shadow-sm transition-all hover:scale-105">
                            <span>+</span> Alimento
                        </button>
                    </div>

                    <div class="pt-2 divide-y divide-black/5">
                        ${hasItems ? meal.items.map(item => `
                            <div class="py-2.5 flex items-center justify-between group">
                                <div class="flex-1 pr-2">
                                    <div class="flex items-baseline gap-2">
                                        <span class="text-sm font-bold text-slate-800">${item.food_name}</span>
                                        <span class="text-xs text-slate-400 font-medium">(${Math.round(item.amount_grams)}g)</span>
                                    </div>
                                    <p class="text-xs text-slate-500 mt-0.5">
                                        <span class="font-semibold text-emerald-600">${Math.round(item.calories)} kcal</span> • P: ${item.protein.toFixed(1)}g • C: ${item.carbs.toFixed(1)}g • G: ${item.fat.toFixed(1)}g
                                    </p>
                                </div>
                                <button onclick="Diary.deleteEntry(${item.id})" class="text-slate-300 hover:text-rose-500 p-2 rounded-xl hover:bg-rose-50 transition-all" title="Remover item">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                </button>
                            </div>
                        `).join('') : `
                            <p class="text-xs text-slate-400 py-3 text-center italic">Nenhum alimento registrado ainda.</p>
                        `}
                    </div>
                </div>
            `;
        }).join('');
    },

    async addWater(ml) {
        const userId = Auth.getUserId();
        const payload = { user_id: userId, date: App.currentDate, amount_ml: ml };

        try {
            const res = await fetch('/api/water', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                App.showToast(`+${ml}ml de água registrados! 💧`, 'info');
                if (typeof App !== 'undefined' && App.playSound) App.playSound('water');
                this.load(App.currentDate);
                if (typeof Streak !== 'undefined') Streak.load();
                if (ml >= 500) App.triggerConfetti();
                return;
            }
        } catch (err) {
            console.warn("Offline: gravando água localmente...");
        }

        // Modo Offline: grava no diário local imediatamente
        if (this.data && this.data.water) {
            this.data.water.consumed_ml += ml;
            localStorage.setItem('vivaleve_diary_' + App.currentDate, JSON.stringify(this.data));
            const queue = JSON.parse(localStorage.getItem('vivaleve_offline_queue') || '[]');
            queue.push({ type: 'add_water', payload: payload, timestamp: Date.now() });
            localStorage.setItem('vivaleve_offline_queue', JSON.stringify(queue));

            App.showToast(`+${ml}ml registrados no aparelho! (Modo Offline 📴)`, 'info');
            if (typeof App !== 'undefined' && App.playSound) App.playSound('water');
            this.render();
            if (ml >= 500 && typeof App !== 'undefined' && App.triggerConfetti) App.triggerConfetti();
        }
    },

    async resetWater() {
        if (!confirm("Deseja zerar o registro de água de hoje?")) return;
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/water/reset?date=${App.currentDate}&user_id=${userId}`, { method: 'DELETE' });
            if (res.ok) {
                App.showToast("Água zerada para o dia de hoje.", "info");
                this.load(App.currentDate);
            }
        } catch (err) {
            console.error(err);
        }
    },

    async deleteEntry(entryId) {
        if (!confirm("Deseja remover este alimento do diário?")) return;
        try {
            const res = await fetch(`/api/diary/${entryId}`, { method: 'DELETE' });
            if (res.ok) {
                App.showToast("Alimento removido com sucesso.");
                this.load(App.currentDate);
            }
        } catch (err) {
            console.error(err);
        }
    },

    openAddModal(mealType) {
        this.currentMealType = mealType;
        this.selectedFood = null;

        const modal = document.getElementById('modal-add-food');
        const mealTitle = document.getElementById('modal-meal-name');
        const searchInput = document.getElementById('food-search-input');
        const resultsContainer = document.getElementById('food-search-results');
        const quantitySection = document.getElementById('food-quantity-section');

        const mealNames = {
            'breakfast': 'Café da Manhã',
            'lunch': 'Almoço',
            'snack': 'Lanche da Tarde',
            'dinner': 'Jantar',
            'extra': 'Ceia / Snacks'
        };

        if (mealTitle) mealTitle.textContent = mealNames[mealType] || 'Refeição';
        if (searchInput) {
            searchInput.value = '';
            setTimeout(() => searchInput.focus(), 150);
        }
        if (resultsContainer) resultsContainer.innerHTML = '';
        if (quantitySection) quantitySection.classList.add('hidden');

        this.searchFoods('');
        if (modal) modal.classList.remove('hidden');
    },

    closeAddModal() {
        const modal = document.getElementById('modal-add-food');
        if (modal) modal.classList.add('hidden');
    },

    async searchFoods(query) {
        const resultsContainer = document.getElementById('food-search-results');
        if (!resultsContainer) return;

        let foods = [];
        try {
            const res = await fetch(`/api/foods?q=${encodeURIComponent(query)}`);
            if (res.ok) {
                foods = await res.json();
            }
        } catch (err) {
            console.warn("Offline: buscando no catálogo de alimentos local...");
        }

        // Se offline ou sem retorno da rede, busca no cache local
        if (!Array.isArray(foods) || foods.length === 0) {
            try {
                const cached = JSON.parse(localStorage.getItem('vivaleve_foods_cache') || '[]');
                if (Array.isArray(cached) && cached.length > 0) {
                    const q = (query || '').trim().toLowerCase();
                    foods = q ? cached.filter(f => f.name.toLowerCase().includes(q)) : cached.slice(0, 15);
                }
            } catch (e) {}
        }

        if (!Array.isArray(foods) || foods.length === 0) {
            resultsContainer.innerHTML = `
                <div class="p-6 text-center text-slate-400 text-sm">
                    Nenhum alimento encontrado com "${query}".
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = foods.map(f => `
            <div onclick="Diary.selectFood(${JSON.stringify(f).replace(/"/g, '&quot;')})" 
                 class="p-3.5 rounded-2xl hover:bg-emerald-50 border border-slate-100 hover:border-emerald-200 cursor-pointer flex items-center justify-between transition-all mb-1">
                <div>
                    <h4 class="font-bold text-slate-800 text-sm">${f.name}</h4>
                    <p class="text-xs text-slate-400">
                        ${f.portion_name || '100g'} (${Math.round(f.calories)} kcal/100g)
                    </p>
                </div>
                <div class="text-right text-xs">
                    <span class="font-black text-emerald-600">${Math.round(f.calories)} kcal</span>
                    <div class="text-[10px] text-slate-400">P:${f.protein.toFixed(1)} C:${f.carbs.toFixed(1)} G:${f.fat.toFixed(1)}</div>
                </div>
            </div>
        `).join('');
    },

    selectFood(food) {
        this.selectedFood = food;

        const quantitySection = document.getElementById('food-quantity-section');
        const selectedName = document.getElementById('selected-food-name');
        const gramsInput = document.getElementById('food-grams-input');

        if (selectedName) selectedName.textContent = food.name;
        if (gramsInput) {
            gramsInput.value = food.portion_grams || 100;
            this.updateFoodPreviewCalculation();
        }

        if (quantitySection) {
            quantitySection.classList.remove('hidden');
            quantitySection.scrollIntoView({ behavior: 'smooth' });
        }
    },

    updateFoodPreviewCalculation() {
        if (!this.selectedFood) return;

        const gramsInput = document.getElementById('food-grams-input');
        const previewEl = document.getElementById('food-preview-calc');
        const grams = parseFloat(gramsInput?.value) || 0;

        const ratio = grams / 100.0;
        const cal = Math.round(this.selectedFood.calories * ratio);
        const p = (this.selectedFood.protein * ratio).toFixed(1);
        const c = (this.selectedFood.carbs * ratio).toFixed(1);
        const f = (this.selectedFood.fat * ratio).toFixed(1);

        if (previewEl) {
            previewEl.innerHTML = `
                <div class="grid grid-cols-4 gap-2 text-center p-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-2xl text-xs border border-emerald-100">
                    <div><span class="text-slate-500 font-semibold">Calorias</span><br><b class="text-emerald-700 text-sm font-black">${cal} kcal</b></div>
                    <div><span class="text-rose-500 font-semibold">Proteína</span><br><b class="text-rose-700 font-bold">${p}g</b></div>
                    <div><span class="text-amber-500 font-semibold">Carboidrato</span><br><b class="text-amber-700 font-bold">${c}g</b></div>
                    <div><span class="text-cyan-500 font-semibold">Gordura</span><br><b class="text-cyan-700 font-bold">${f}g</b></div>
                </div>
            `;
        }
    },

    async confirmAddFood() {
        if (!this.selectedFood) return;

        const gramsInput = document.getElementById('food-grams-input');
        const grams = parseFloat(gramsInput?.value);

        if (!grams || grams <= 0) {
            App.showToast("Informe uma quantidade válida em gramas.", "warning");
            return;
        }

        const ratio = grams / 100.0;
        const userId = Auth.getUserId();
        const payload = {
            user_id: userId,
            date: App.currentDate,
            meal_type: this.currentMealType,
            food_name: this.selectedFood.name,
            amount_grams: grams,
            calories: this.selectedFood.calories * ratio,
            protein: this.selectedFood.protein * ratio,
            carbs: this.selectedFood.carbs * ratio,
            fat: this.selectedFood.fat * ratio,
            fiber: (this.selectedFood.fiber || 0) * ratio,
            notes: ""
        };

        try {
            const res = await fetch('/api/diary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                App.showToast(`${this.selectedFood.name} adicionado ao diário!`);
                if (typeof App !== 'undefined' && App.playSound) App.playSound('success');
                this.closeAddModal();
                this.load(App.currentDate);
                if (typeof Streak !== 'undefined') Streak.load();
                App.triggerConfetti();
                return;
            }
        } catch (err) {
            console.warn("Offline: gravando refeição localmente...");
        }

        // Modo Offline: calcular e gravar no diário local imediatamente
        const cal = Math.round(payload.calories);
        const p = parseFloat(payload.protein.toFixed(1));
        const c = parseFloat(payload.carbs.toFixed(1));
        const f = parseFloat(payload.fat.toFixed(1));

        if (!this.data) await this.load(App.currentDate);

        if (!this.data.meals[this.currentMealType]) {
            this.data.meals[this.currentMealType] = { name: this.currentMealType, items: [], total_calories: 0 };
        }

        const newEntry = {
            id: 'off_' + Date.now(),
            food_name: payload.food_name,
            amount_grams: payload.amount_grams,
            calories: cal,
            protein: p,
            carbs: c,
            fat: f
        };

        this.data.meals[this.currentMealType].items.push(newEntry);
        this.data.meals[this.currentMealType].total_calories += cal;
        this.data.summary.consumed_calories += cal;
        this.data.summary.remaining_calories = this.data.summary.target_calories - this.data.summary.consumed_calories;
        this.data.summary.percentage = Math.round((this.data.summary.consumed_calories / this.data.summary.target_calories) * 100);
        this.data.summary.macros.protein.consumed += p;
        this.data.summary.macros.carbs.consumed += c;
        this.data.summary.macros.fat.consumed += f;

        localStorage.setItem('vivaleve_diary_' + App.currentDate, JSON.stringify(this.data));

        // Adicionar à fila de sincronização para quando reconectar
        const queue = JSON.parse(localStorage.getItem('vivaleve_offline_queue') || '[]');
        queue.push({ type: 'add_food', payload: payload, timestamp: Date.now() });
        localStorage.setItem('vivaleve_offline_queue', JSON.stringify(queue));

        App.showToast(`${this.selectedFood.name} salvo no aparelho! (Modo Offline 📴)`, "success");
        if (typeof App !== 'undefined' && App.playSound) App.playSound('success');
        this.closeAddModal();
        this.render();
        if (typeof App !== 'undefined' && App.triggerConfetti) App.triggerConfetti();
    }
};
