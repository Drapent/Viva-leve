/**
 * VivaLeve - Gerenciador de Perfil, Metas e Gráficos de Evolução
 */

const ProfileCharts = {
    weightChart: null,
    caloricChart: null,

    async load() {
        await this.loadProfileData();
        await this.loadStats();
    },

    async loadProfileData() {
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/profile?user_id=${userId}`);
            if (!res.ok) throw new Error("Erro ao buscar dados do perfil");
            const profile = await res.json();

            // Preencher inputs
            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if (el && val !== undefined && val !== null) el.value = val;
            };

            setVal('profile-name', profile.name);
            setVal('profile-gender', profile.gender);
            setVal('profile-age', profile.age);
            setVal('profile-weight', profile.weight);
            setVal('profile-height', profile.height);
            setVal('profile-activity', profile.activity_level);
            setVal('profile-goal', profile.goal);

            setVal('profile-target-cal', Math.round(profile.target_calories));
            setVal('profile-target-p', Math.round(profile.target_protein));
            setVal('profile-target-c', Math.round(profile.target_carbs));
            setVal('profile-target-f', Math.round(profile.target_fat));
            setVal('profile-target-water', Math.round(profile.target_water));

            // Informações teóricas calculadas
            const bmrEl = document.getElementById('calc-bmr-display');
            const tdeeEl = document.getElementById('calc-tdee-display');
            if (bmrEl && profile.calculated) bmrEl.textContent = `${profile.calculated.bmr} kcal`;
            if (tdeeEl && profile.calculated) tdeeEl.textContent = `${profile.calculated.tdee} kcal`;

            // Status da IA Integrada e Chaves
            const apiKeyStatus = document.getElementById('gemini-key-status');
            const apiKeyInput = document.getElementById('profile-gemini-key');
            if (apiKeyStatus) {
                if (profile.has_gemini_key) {
                    apiKeyStatus.innerHTML = `
                        <span class="inline-flex items-center gap-1.5 text-xs text-emerald-700 font-black bg-emerald-100/90 border border-emerald-300 px-3 py-1 rounded-full shadow-xs">
                            <span>🔑</span> Chave Própria (${profile.gemini_api_key_masked})
                        </span>
                    `;
                } else {
                    apiKeyStatus.innerHTML = `
                        <span class="inline-flex items-center gap-1.5 text-xs text-emerald-700 font-black bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full shadow-xs animate-pulse">
                            <span class="w-2 h-2 rounded-full bg-emerald-500"></span> IA Integrada Ativa ⚡
                        </span>
                    `;
                }
            }
            if (apiKeyInput) {
                apiKeyInput.placeholder = profile.has_gemini_key 
                    ? "Chave configurada. Deixe vazio para voltar à IA integrada de fábrica." 
                    : "gsk_... ou AIzaSy... (Deixe vazio para usar a IA integrada)";
            }

        } catch (err) {
            console.error(err);
        }
    },

    async saveProfile(recalculate = false) {
        const getVal = (id) => {
            const el = document.getElementById(id);
            return el ? el.value : null;
        };

        const userId = Auth.getUserId();
        const payload = {
            user_id: userId,
            name: getVal('profile-name'),
            gender: getVal('profile-gender'),
            age: parseInt(getVal('profile-age')),
            weight: parseFloat(getVal('profile-weight')),
            height: parseFloat(getVal('profile-height')),
            activity_level: getVal('profile-activity'),
            goal: getVal('profile-goal'),
            target_calories: parseFloat(getVal('profile-target-cal')),
            target_protein: parseFloat(getVal('profile-target-p')),
            target_carbs: parseFloat(getVal('profile-target-c')),
            target_fat: parseFloat(getVal('profile-target-f')),
            target_water: parseFloat(getVal('profile-target-water')),
            recalculate: recalculate
        };

        try {
            const res = await fetch('/api/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                App.showToast(recalculate ? "Metas recalculadas com sucesso!" : "Perfil salvo com sucesso!");
                await App.loadProfile();
                await this.loadProfileData();
                Diary.load(App.currentDate);
            } else {
                App.showToast("Erro ao salvar perfil.", "error");
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro na comunicação com o servidor.", "error");
        }
    },

    async saveApiKey() {
        const input = document.getElementById('profile-gemini-key');
        const key = input ? input.value.trim() : '';

        const userId = Auth.getUserId();
        try {
            const res = await fetch('/api/settings/api-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, gemini_api_key: key })
            });

            if (res.ok) {
                const data = await res.json();
                if (key) {
                    App.showToast("Chave personalizada salva com sucesso!");
                } else {
                    App.showToast("IA Integrada padrão de fábrica reativada!");
                }
                if (input) input.value = '';
                this.loadProfileData();
            } else {
                App.showToast("Não foi possível atualizar a chave.", "error");
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro de conexão.", "error");
        }
    },

    async logWeight() {
        const input = document.getElementById('log-weight-input');
        const weight = parseFloat(input?.value);

        if (!weight || weight < 30 || weight > 300) {
            App.showToast("Informe um peso válido (ex: 75.5)", "warning");
            return;
        }

        const userId = Auth.getUserId();
        try {
            const res = await fetch('/api/stats/weight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, date: App.currentDate, weight: weight, notes: "" })
            });

            if (res.ok) {
                App.showToast(`Peso de ${weight} kg registrado com sucesso!`);
                if (input) input.value = '';
                this.loadStats();
                this.loadProfileData();
            }
        } catch (err) {
            console.error(err);
        }
    },

    async loadStats() {
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/stats/progress?user_id=${userId}`);
            if (!res.ok) return;
            const stats = await res.json();

            this.renderWeightChart(stats.weight_history || []);
            this.renderCaloricChart(stats.caloric_history || []);
        } catch (err) {
            console.error(err);
        }
    },

    renderWeightChart(history) {
        const ctx = document.getElementById('weight-chart');
        if (!ctx || typeof Chart === 'undefined') return;

        if (this.weightChart) {
            this.weightChart.destroy();
        }

        if (history.length === 0) {
            history = [{ date: App.currentDate, weight: App.userProfile?.weight || 75 }];
        }

        const labels = history.map(h => {
            const p = h.date.split('-');
            return `${p[2]}/${p[1]}`;
        });
        const data = history.map(h => h.weight);

        this.weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Peso Corporal (kg)',
                    data: data,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    },

    renderCaloricChart(history) {
        const ctx = document.getElementById('caloric-chart');
        if (!ctx || typeof Chart === 'undefined') return;

        if (this.caloricChart) {
            this.caloricChart.destroy();
        }

        const labels = history.map(h => {
            const p = h.date.split('-');
            return `${p[2]}/${p[1]}`;
        });
        const data = history.map(h => h.total_calories);

        this.caloricChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.length > 0 ? labels : ['Hoje'],
                datasets: [{
                    label: 'Calorias Consumidas',
                    data: data.length > 0 ? data : [0],
                    backgroundColor: '#059669',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        grid: { color: '#f1f5f9' },
                        suggestedMax: 2500
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
};
