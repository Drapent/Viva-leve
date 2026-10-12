/**
 * VivaLeve - Módulo de Treinos
 * Estilo Growth Suplements - Cálculo de gasto calórico com MET + EPOC
 */

const Workout = {
    templates: [],

    async loadWorkouts() {
        try {
            const res = await fetch('/api/workouts/today');
            const workouts = await res.json();
            this.renderWorkoutsToday(workouts);
        } catch (e) {
            console.error('Erro ao carregar treinos:', e);
        }

        try {
            const res = await fetch('/api/workouts/templates');
            this.templates = await res.json();
            this.renderTemplates();
        } catch (e) {
            console.error('Erro ao carregar templates:', e);
        }

        this.loadHistory();
    },

    renderWorkoutsToday(workouts) {
        const container = document.getElementById('workouts-today-list');
        if (!container) return;

        if (!workouts || workouts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <span class="text-3xl block mb-2">🏋️</span>
                    <p class="text-sm font-bold">Nenhum treino registrado hoje</p>
                    <p class="text-xs mt-1">Registre seu primeiro treino abaixo!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = workouts.map(w => `
            <div class="p-3 rounded-2xl bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-100">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-black text-slate-800 text-sm">${w.name}</h4>
                        <p class="text-[11px] text-slate-500">${w.category} • ${w.duration_minutes}min • ${w.intensity}</p>
                    </div>
                    <div class="text-right">
                        <span class="text-lg font-black text-violet-600">${w.calories_burned}</span>
                        <span class="text-[10px] text-slate-400 block">kcal queimadas</span>
                    </div>
                </div>
            </div>
        `).join('');
    },

    renderTemplates() {
        const container = document.getElementById('workouts-templates-list');
        const countEl = document.getElementById('workout-templates-count');
        if (!container) return;

        if (countEl) countEl.textContent = `${this.templates.length} treinos`;

        if (this.templates.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <span class="text-3xl block mb-2">📋</span>
                    <p class="text-sm font-bold">Nenhuma ficha disponível</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.templates.map(t => `
            <div class="p-3 rounded-2xl bg-slate-50 border border-slate-200 hover:border-violet-200 transition cursor-pointer" onclick="Workout.useTemplate(${t.id})">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-black text-slate-800 text-sm">${t.name}</h4>
                        <p class="text-[11px] text-slate-500">${t.focus_area} • ${t.exercises.length} exercícios</p>
                    </div>
                    <span class="text-xs font-bold text-violet-600 bg-violet-50 px-2 py-1 rounded-lg">Usar</span>
                </div>
            </div>
        `).join('');
    },

    async useTemplate(id) {
        const template = this.templates.find(t => t.id === id);
        if (!template) return;

        const nameInput = document.getElementById('workout-name');
        const categorySelect = document.getElementById('workout-category');

        if (nameInput) nameInput.value = template.name;

        // Tentar encontrar categoria correspondente
        const focusArea = template.focus_area.toLowerCase();
        if (categorySelect) {
            const options = Array.from(categorySelect.options);
            const match = options.find(o => focusArea.includes(o.value));
            if (match) categorySelect.value = match.value;
        }

        if (typeof App !== 'undefined') {
            App.showToast(`Treino "${template.name}" carregado! Ajuste e registre.`, 'success');
        }

        // Scroll para o formulário
        const formSection = document.getElementById('workout-name')?.closest('.bg-white');
        if (formSection) formSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },

    async logWorkout() {
        const nameInput = document.getElementById('workout-name');
        const categorySelect = document.getElementById('workout-category');
        const intensitySelect = document.getElementById('workout-intensity');
        const durationInput = document.getElementById('workout-duration');

        const name = nameInput?.value.trim();
        const category = categorySelect?.value || 'musculacao';
        const intensity = intensitySelect?.value || 'moderado';
        const duration = parseInt(durationInput?.value) || 45;

        if (!name) {
            if (typeof App !== 'undefined') App.showToast('Informe o nome do treino', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/workouts/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    category: category,
                    duration_minutes: duration,
                    intensity: intensity,
                    exercises: []
                })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast(`Treino registrado! +${data.calories_burned} kcal queimadas 🔥`, 'success');
                    App.triggerConfetti();
                    App.playSound('success');
                }

                // Limpar formulário
                if (nameInput) nameInput.value = '';

                // Recarregar
                this.loadWorkouts();
                if (typeof Avatar !== 'undefined') Avatar.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.detail || 'Erro ao registrar treino', 'error');
            }
        } catch (e) {
            console.error('Erro ao registrar treino:', e);
            if (typeof App !== 'undefined') App.showToast('Erro ao conectar com o servidor', 'error');
        }
    },

    async loadHistory() {
        try {
            const res = await fetch('/api/workouts/today');
            const workouts = await res.json();
            this.renderHistory(workouts);
        } catch (e) {
            console.error('Erro ao carregar histórico:', e);
        }
    },

    renderHistory(workouts) {
        const container = document.getElementById('workout-history-list');
        if (!container) return;

        if (!workouts || workouts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <span class="text-3xl block mb-2">📊</span>
                    <p class="text-sm font-bold">Nenhum treino registrado ainda</p>
                    <p class="text-xs mt-1">Complete treinos para ver seu histórico aqui!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = workouts.slice(0, 5).map(w => `
            <div class="p-3 rounded-2xl bg-slate-50 border border-slate-200">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-black text-slate-800 text-sm">${w.name}</h4>
                        <p class="text-[11px] text-slate-500">${w.date} • ${w.duration_minutes}min</p>
                    </div>
                    <div class="text-right">
                        <span class="text-sm font-black text-violet-600">${w.calories_burned}</span>
                        <span class="text-[10px] text-slate-400 block">kcal</span>
                    </div>
                </div>
            </div>
        `).join('');
    },

    init() {
        // Atualizar preview de calorias quando mudar duração ou intensidade
        const durationInput = document.getElementById('workout-duration');
        const intensitySelect = document.getElementById('workout-intensity');
        const categorySelect = document.getElementById('workout-category');

        const updatePreview = () => {
            const duration = parseInt(durationInput?.value) || 45;
            const intensity = intensitySelect?.value || 'moderado';
            const category = categorySelect?.value || 'musculacao';

            // Usar peso do perfil se disponível
            const weight = App?.userProfile?.weight || 75;

            // Calcular MET baseado na categoria
            let met = 5.5; // Padrão musculação moderada
            if (category === 'corrida') met = intensity === 'leve' ? 6.0 : intensity === 'intenso' ? 11.0 : 8.3;
            else if (category === 'bike') met = intensity === 'leve' ? 4.0 : intensity === 'intenso' ? 10.0 : 6.8;
            else if (category === 'natacao') met = intensity === 'leve' ? 4.8 : intensity === 'intenso' ? 10.0 : 7.0;
            else if (category === 'hiit') met = intensity === 'leve' ? 6.0 : intensity === 'intenso' ? 12.0 : 8.0;
            else if (category === 'yoga') met = intensity === 'leve' ? 2.5 : intensity === 'intenso' ? 5.0 : 3.5;
            else if (category === 'crossfit') met = intensity === 'leve' ? 5.0 : intensity === 'intenso' ? 12.0 : 8.0;
            else if (category === 'funcional') met = intensity === 'leve' ? 3.0 : intensity === 'intenso' ? 7.0 : 5.0;
            else if (category === 'calistenia') met = intensity === 'leve' ? 3.0 : intensity === 'intenso' ? 7.0 : 5.0;
            else if (category === 'luta') met = intensity === 'leve' ? 6.0 : intensity === 'intenso' ? 12.0 : 9.0;
            else if (category === 'esporte') met = intensity === 'leve' ? 4.5 : intensity === 'intenso' ? 10.0 : 6.5;

            // Fator EPOC
            const epoc = intensity === 'leve' ? 1.05 : intensity === 'intenso' ? 1.20 : 1.12;

            const calories = Math.round(((met * 3.5 * weight) / 200) * duration * epoc);
            const valEl = document.getElementById('workout-calories-val');
            if (valEl) valEl.textContent = calories;
        };

        if (durationInput) durationInput.addEventListener('input', updatePreview);
        if (intensitySelect) intensitySelect.addEventListener('change', updatePreview);
        if (categorySelect) categorySelect.addEventListener('change', updatePreview);

        // Carregar treinos
        this.loadWorkouts();
    }
};

window.Workout = Workout;
