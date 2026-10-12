/**
 * VivaLeve - Onboarding Wizard & Motor de Déficit Calórico Personalizado
 * Sistema passo a passo interativo no estilo MyFitnessPal / Lifesum / Yazio
 */

const Onboarding = {
    step: 0,
    quizOnlyMode: false,
    data: {
        goal: 'emagrecer',
        gender: 'M',
        age: 28,
        weight: 75.0,
        height: 175.0,
        target_weight: 70.0,
        pace: 'moderado',
        activity_level: 'moderado',
        calculated: null
    },

    openWelcome() {
        this.quizOnlyMode = false;
        const modal = document.getElementById('modal-onboarding-wizard');
        if (!modal) return;
        modal.classList.remove('hidden');
        this.showView('welcome');
    },

    openLogin() {
        const modal = document.getElementById('modal-onboarding-wizard');
        if (!modal) return;
        modal.classList.remove('hidden');
        this.showView('login');
    },

    openQuizOnly() {
        this.quizOnlyMode = true;
        // Puxar valores atuais do perfil se existirem
        if (App.userProfile) {
            this.data.gender = App.userProfile.gender || 'M';
            this.data.age = App.userProfile.age || 28;
            this.data.weight = App.userProfile.weight || 75.0;
            this.data.height = App.userProfile.height || 175.0;
            this.data.goal = App.userProfile.goal || 'emagrecer';
            this.data.activity_level = App.userProfile.activity_level || 'moderado';
        }

        const modal = document.getElementById('modal-onboarding-wizard');
        if (!modal) return;
        modal.classList.remove('hidden');
        this.showView('wizard');
        this.setStep(1);
    },

    close() {
        const modal = document.getElementById('modal-onboarding-wizard');
        if (modal) modal.classList.add('hidden');
    },

    showView(viewName) {
        const views = ['welcome', 'login', 'wizard'];
        views.forEach(v => {
            const el = document.getElementById(`onboarding-view-${v}`);
            if (el) {
                if (v === viewName) {
                    el.classList.remove('hidden');
                    el.classList.add('fade-in');
                } else {
                    el.classList.add('hidden');
                }
            }
        });

        // Configurar botão de fechar modal (só visível se usuário já estiver logado ou em quizOnlyMode)
        const closeBtn = document.getElementById('onboarding-global-close');
        if (closeBtn) {
            if (Auth.isLoggedIn() || this.quizOnlyMode) {
                closeBtn.classList.remove('hidden');
            } else {
                closeBtn.classList.add('hidden');
            }
        }
    },

    startQuiz() {
        this.quizOnlyMode = false;
        this.showView('wizard');
        this.setStep(1);
        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
    },

    setStep(stepNumber) {
        this.step = stepNumber;

        // Atualizar barra de progresso
        const progressFill = document.getElementById('wizard-progress-fill');
        const stepCounter = document.getElementById('wizard-step-counter');
        const percent = Math.round((stepNumber / 6) * 100);

        if (progressFill) progressFill.style.width = `${percent}%`;
        if (stepCounter) stepCounter.textContent = `Etapa ${stepNumber} de 6`;

        // Alternar telas de passos
        for (let i = 1; i <= 6; i++) {
            const stepEl = document.getElementById(`wizard-step-${i}`);
            if (stepEl) {
                if (i === stepNumber) {
                    stepEl.classList.remove('hidden');
                    stepEl.classList.add('fade-in');
                } else {
                    stepEl.classList.add('hidden');
                }
            }
        }

        // Se for etapa 3, atualizar badge de IMC
        if (stepNumber === 3) {
            this.updateBmiPreview();
        }

        // Se for etapa 4, ajustar opções de ritmo de acordo com o objetivo
        if (stepNumber === 4) {
            this.adjustPaceOptionsForGoal();
        }

        // Se for etapa 6, disparar cálculo e renderizar plano
        if (stepNumber === 6) {
            this.calculateAndRenderPlan();
        }
    },

    prevStep() {
        if (this.step > 1) {
            this.setStep(this.step - 1);
            if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
        } else {
            if (!this.quizOnlyMode) {
                this.showView('welcome');
            } else {
                this.close();
            }
        }
    },

    nextStep() {
        // Validações por etapa
        if (this.step === 2) {
            const ageInput = document.getElementById('quiz-age');
            const ageVal = parseInt(ageInput?.value, 10);
            if (!ageVal || ageVal < 12 || ageVal > 110) {
                App.showToast("Por favor, informe uma idade válida (entre 12 e 110 anos).", "warning");
                return;
            }
            this.data.age = ageVal;
        } else if (this.step === 3) {
            const weightInput = document.getElementById('quiz-weight');
            const heightInput = document.getElementById('quiz-height');
            const wVal = parseFloat(weightInput?.value);
            const hVal = parseFloat(heightInput?.value);

            if (!wVal || wVal < 30 || wVal > 300) {
                App.showToast("Informe um peso válido (ex: 75.5 kg).", "warning");
                return;
            }
            if (!hVal || hVal < 100 || hVal > 250) {
                App.showToast("Informe uma altura válida em centímetros (ex: 175 cm).", "warning");
                return;
            }
            this.data.weight = wVal;
            this.data.height = hVal;
        } else if (this.step === 4) {
            const targetWeightInput = document.getElementById('quiz-target-weight');
            const twVal = parseFloat(targetWeightInput?.value);
            if (this.data.goal === 'manter') {
                this.data.target_weight = this.data.weight;
            } else if (twVal && twVal > 30 && twVal < 300) {
                if (this.data.goal === 'emagrecer' && twVal >= this.data.weight) {
                    App.showToast("Para emagrecer, o peso-meta precisa ser menor que o seu peso atual.", "warning");
                    return;
                }
                if (this.data.goal === 'hipertrofia' && twVal <= this.data.weight) {
                    App.showToast("Para ganhar massa, o peso-meta precisa ser maior que o seu peso atual.", "warning");
                    return;
                }
                this.data.target_weight = twVal;
            } else {
                this.data.target_weight = this.data.weight;
            }
        } else if (this.step === 5) {
            const mealsEl = document.getElementById('quiz-meals-per-day');
            const styleEl = document.getElementById('quiz-diet-style');
            this.data.meals_per_day = parseInt(mealsEl?.value, 10) || 4;
            this.data.diet_style = styleEl?.value || 'padrao';
        }

        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
        this.setStep(this.step + 1);
    },

    selectGoal(goal) {
        this.data.goal = goal;
        document.querySelectorAll('.quiz-goal-btn').forEach(btn => {
            const g = btn.getAttribute('data-goal');
            if (g === goal) {
                btn.className = "quiz-goal-btn quiz-card-selected flex items-center gap-4 p-4 rounded-3xl border-2 border-emerald-500 bg-emerald-50/80 shadow-md transition-all scale-[1.02]";
            } else {
                btn.className = "quiz-goal-btn flex items-center gap-4 p-4 rounded-3xl border-2 border-slate-100 hover:border-emerald-200 bg-white shadow-sm transition-all";
            }
        });
        // Se já estiver na etapa 4, atualizar as opções de ritmo imediatamente
        if (this.step === 4) {
            this.adjustPaceOptionsForGoal();
        }
        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
    },

    selectGender(gender) {
        this.data.gender = gender;
        const btnM = document.getElementById('quiz-gender-m');
        const btnF = document.getElementById('quiz-gender-f');

        if (gender === 'M') {
            if (btnM) btnM.className = "flex-1 p-4 rounded-3xl border-2 border-emerald-500 bg-emerald-50/80 text-emerald-900 font-black shadow-md transition scale-[1.02] flex flex-col items-center gap-1";
            if (btnF) btnF.className = "flex-1 p-4 rounded-3xl border-2 border-slate-100 hover:border-emerald-200 bg-white text-slate-600 font-bold shadow-sm transition flex flex-col items-center gap-1";
        } else {
            if (btnM) btnM.className = "flex-1 p-4 rounded-3xl border-2 border-slate-100 hover:border-emerald-200 bg-white text-slate-600 font-bold shadow-sm transition flex flex-col items-center gap-1";
            if (btnF) btnF.className = "flex-1 p-4 rounded-3xl border-2 border-pink-500 bg-pink-50/80 text-pink-900 font-black shadow-md transition scale-[1.02] flex flex-col items-center gap-1";
        }
        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
    },

    selectPace(pace) {
        this.data.pace = pace;
        document.querySelectorAll('.quiz-pace-btn').forEach(btn => {
            const p = btn.getAttribute('data-pace');
            if (p === pace) {
                btn.className = "quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 border-emerald-500 bg-emerald-50/80 shadow-md transition-all scale-[1.02]";
            } else {
                btn.className = "quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 border-slate-100 hover:border-emerald-200 bg-white shadow-sm transition-all";
            }
        });
        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
    },

    selectActivity(level) {
        this.data.activity_level = level;
        document.querySelectorAll('.quiz-activity-btn').forEach(btn => {
            const act = btn.getAttribute('data-activity');
            if (act === level) {
                btn.className = "quiz-activity-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 border-emerald-500 bg-emerald-50/80 shadow-md transition-all scale-[1.02]";
            } else {
                btn.className = "quiz-activity-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 border-slate-100 hover:border-emerald-200 bg-white shadow-sm transition-all";
            }
        });
        if (typeof App !== 'undefined' && App.playSound) App.playSound('click');
    },

    adjustPaceOptionsForGoal() {
        const paceTitle = document.getElementById('quiz-pace-title');
        const paceDesc = document.getElementById('quiz-pace-description');
        const targetWeightContainer = document.getElementById('quiz-target-weight-container');
        const container = document.getElementById('quiz-pace-cards-container');

        let cardsHtml = '';
        const currentPace = this.data.pace || 'moderado';

        if (this.data.goal === 'emagrecer') {
            if (paceTitle) paceTitle.textContent = "Ritmo do Déficit Calórico:";
            if (paceDesc) paceDesc.textContent = "Escolha a velocidade com que deseja perder gordura com saúde.";
            if (targetWeightContainer) targetWeightContainer.classList.remove('hidden');

            cardsHtml = `
                <div data-pace="suave" onclick="Onboarding.selectPace('suave')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'suave' ? 'border-emerald-500 bg-emerald-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-emerald-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-emerald-50 rounded-xl">🌱</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Suave & Sustentável</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">-300 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Perda de ~0.3 kg por semana. Muito fácil de manter sem passar fome.</p>
                    </div>
                </div>

                <div data-pace="moderado" onclick="Onboarding.selectPace('moderado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'moderado' ? 'border-emerald-500 bg-emerald-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-emerald-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-teal-50 rounded-xl">🎯</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Moderado (Recomendado)</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">-500 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Perda de ~0.5 kg por semana. O padrão ouro dos nutricionistas.</p>
                    </div>
                </div>

                <div data-pace="acelerado" onclick="Onboarding.selectPace('acelerado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'acelerado' ? 'border-emerald-500 bg-emerald-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-emerald-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-amber-50 rounded-xl">⚡</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Acelerado & Focado</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">-750 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Perda de ~0.75 kg por semana. Requer foco total e mais disciplina.</p>
                    </div>
                </div>
            `;
        } else if (this.data.goal === 'hipertrofia') {
            if (paceTitle) paceTitle.textContent = "Ritmo do Ganho de Massa Muscular (Bulking):";
            if (paceDesc) paceDesc.textContent = "Escolha o ritmo de superávit para construir músculos com o mínimo de gordura.";
            if (targetWeightContainer) targetWeightContainer.classList.remove('hidden');

            cardsHtml = `
                <div data-pace="moderado" onclick="Onboarding.selectPace('moderado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'moderado' ? 'border-purple-500 bg-purple-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-purple-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-purple-100 rounded-xl">🥩</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Bulking Limpo (Recomendado)</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">+450 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Ganho sólido de ~0.4 a 0.5 kg por semana com força e hipertrofia de qualidade.</p>
                    </div>
                </div>

                <div data-pace="suave" onclick="Onboarding.selectPace('suave')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'suave' ? 'border-purple-500 bg-purple-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-purple-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-emerald-50 rounded-xl">🌱</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Hipertrofia Gradual</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">+300 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Ganho seco de ~0.25 a 0.3 kg por semana com retenção quase nula de gordura.</p>
                    </div>
                </div>

                <div data-pace="acelerado" onclick="Onboarding.selectPace('acelerado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'acelerado' ? 'border-purple-500 bg-purple-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-purple-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-amber-50 rounded-xl">🚀</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Bulking Acelerado (Pesado)</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">+650 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Para quem tem metabolismo muito rápido (ectomorfo) e dificuldade de ganhar peso.</p>
                    </div>
                </div>
            `;
        } else {
            // MANUTENÇÃO - Nunca mostrar déficit calórico aqui!
            if (paceTitle) paceTitle.textContent = "Equilíbrio Metabólico & Manutenção:";
            if (paceDesc) paceDesc.textContent = "Seu plano manterá seu peso estável com máxima energia e saúde celular.";
            if (targetWeightContainer) targetWeightContainer.classList.add('hidden');

            cardsHtml = `
                <div data-pace="moderado" onclick="Onboarding.selectPace('moderado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'moderado' ? 'border-cyan-500 bg-cyan-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-cyan-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-cyan-100 rounded-xl">⚖️</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Manutenção Pura (Recomendado)</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800">0 kcal (Equilíbrio)</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Consumo igual ao gasto exato. Peso 100% estável, longevidade e equilíbrio hormonal.</p>
                    </div>
                </div>

                <div data-pace="suave" onclick="Onboarding.selectPace('suave')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'suave' ? 'border-cyan-500 bg-cyan-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-cyan-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-emerald-50 rounded-xl">🔥</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Recomposição Corporal Suave</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">-150 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Queima gordura residual aos poucos preservando 100% da sua musculatura.</p>
                    </div>
                </div>

                <div data-pace="acelerado" onclick="Onboarding.selectPace('acelerado')" class="quiz-pace-btn flex items-center gap-3.5 p-3.5 rounded-2xl border-2 ${currentPace === 'acelerado' ? 'border-cyan-500 bg-cyan-50/80 shadow-md scale-[1.02]' : 'border-slate-100 hover:border-cyan-200 bg-white shadow-sm'} transition-all cursor-pointer">
                    <span class="text-2xl p-2 bg-blue-50 rounded-xl">💪</span>
                    <div class="text-left flex-1">
                        <div class="flex items-center justify-between">
                            <h4 class="font-black text-slate-800 text-xs">Tônus & Densidade Muscular</h4>
                            <span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">+150 kcal/dia</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">Pequeno aporte energético para melhorar força nos treinos sem aumentar o peso.</p>
                    </div>
                </div>
            `;
        }

        if (container) container.innerHTML = cardsHtml;
    },

    updateBmiPreview() {
        const weightInput = document.getElementById('quiz-weight');
        const heightInput = document.getElementById('quiz-height');
        const bmiValEl = document.getElementById('quiz-bmi-val');
        const bmiStatusEl = document.getElementById('quiz-bmi-status');
        const bmiBadgeEl = document.getElementById('quiz-bmi-badge');

        const weight = parseFloat(weightInput?.value) || this.data.weight;
        const height = parseFloat(heightInput?.value) || this.data.height;

        if (weight > 30 && height > 100) {
            const hM = height / 100;
            const bmi = (weight / (hM * hM)).toFixed(1);

            let status = "Peso Saudável";
            let badgeClass = "bg-emerald-100 text-emerald-800 border-emerald-300";

            if (bmi < 18.5) {
                status = "Abaixo do peso";
                badgeClass = "bg-amber-100 text-amber-800 border-amber-300";
            } else if (bmi < 25.0) {
                status = "Peso Saudável / Ideal";
                badgeClass = "bg-emerald-100 text-emerald-800 border-emerald-300";
            } else if (bmi < 30.0) {
                status = "Sobrepeso Leve";
                badgeClass = "bg-amber-100 text-amber-800 border-amber-300";
            } else if (bmi < 35.0) {
                status = "Obesidade Grau I";
                badgeClass = "bg-rose-100 text-rose-800 border-rose-300";
            } else {
                status = "Obesidade Grau II/III";
                badgeClass = "bg-rose-100 text-rose-800 border-rose-300";
            }

            if (bmiValEl) bmiValEl.textContent = bmi;
            if (bmiStatusEl) bmiStatusEl.textContent = status;
            if (bmiBadgeEl) bmiBadgeEl.className = `p-3 rounded-2xl border flex items-center justify-between transition-all ${badgeClass}`;
        }
    },

    async calculateAndRenderPlan() {
        const loadingEl = document.getElementById('wizard-plan-loading');
        const contentEl = document.getElementById('wizard-plan-content');
        if (loadingEl) loadingEl.classList.remove('hidden');
        if (contentEl) contentEl.classList.add('hidden');

        let calc = null;
        try {
            const res = await fetch('/api/profile/calculate-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    weight: this.data.weight,
                    height: this.data.height,
                    age: this.data.age,
                    gender: this.data.gender,
                    activity_level: this.data.activity_level,
                    goal: this.data.goal,
                    pace: this.data.pace
                })
            });

            if (res.ok) {
                calc = await res.json();
            }
        } catch (e) {
            console.error("Erro na rota calculate-preview, calculando localmente:", e);
        }

        // Fallback local se o servidor não responder
        if (!calc) {
            const w = this.data.weight;
            const h = this.data.height;
            const a = this.data.age;
            const isF = this.data.gender === 'F';
            const bmr = isF ? (10 * w) + (6.25 * h) - (5 * a) - 161 : (10 * w) + (6.25 * h) - (5 * a) + 5;
            const mults = { sedentario: 1.2, leve: 1.375, moderado: 1.55, intenso: 1.725 };
            const tdee = Math.round(bmr * (mults[this.data.activity_level] || 1.55));
            const pace = this.data.pace || 'moderado';
            const tables = {
                emagrecer: { suave: -300, moderado: -500, acelerado: -750 },
                hipertrofia: { suave: 300, moderado: 450, acelerado: 650 },
                manter: { suave: -150, moderado: 0, acelerado: 150 }
            };
            const calDiff = (tables[this.data.goal] || tables.manter)[pace] ?? 0;
            const minCal = isF ? 1200 : 1400;
            const targetCal = Math.max(minCal, tdee + calDiff);
            const pMult = this.data.goal === 'emagrecer' ? 2.0 : (this.data.goal === 'hipertrofia' ? 2.2 : 1.8);
            const p = Math.round(w * pMult);
            const f = Math.round(w * 0.85);
            const c = Math.round(Math.max(200, targetCal - (p * 4 + f * 9)) / 4);
            const water = Math.round(w * 38);

            calc = {
                bmr: Math.round(bmr),
                tdee: tdee,
                activity_burn: Math.round(tdee - bmr),
                cal_diff: calDiff,
                target_calories: targetCal,
                target_protein: p,
                target_carbs: c,
                target_fat: f,
                target_water: water,
                bmi: (w / ((h / 100) ** 2)).toFixed(1),
                bmi_status: "Calculado"
            };
        }

        this.data.calculated = calc;

        // Preencher no DOM do resultado
        const bmrEl = document.getElementById('plan-bmr-val');
        const tdeeEl = document.getElementById('plan-tdee-val');
        const deficitEl = document.getElementById('plan-deficit-val');
        const targetCalEl = document.getElementById('plan-calories-val');
        const pEl = document.getElementById('plan-protein-val');
        const cEl = document.getElementById('plan-carbs-val');
        const fEl = document.getElementById('plan-fat-val');
        const waterEl = document.getElementById('plan-water-val');
        const breakdownEl = document.getElementById('plan-energy-breakdown');

        if (bmrEl) bmrEl.textContent = `${calc.bmr} kcal`;
        if (tdeeEl) tdeeEl.textContent = `${calc.tdee} kcal`;
        if (breakdownEl) {
            const actBurn = calc.activity_burn ?? (calc.tdee - calc.bmr);
            breakdownEl.innerHTML = `
                <p class="font-black text-slate-700 text-[11px] mb-1">🔬 Como chegamos no seu número</p>
                <p>🫀 <b>Gasto basal (TMB): ${calc.bmr} kcal</b> — o que seu corpo gasta parado 24h (respirar, coração, órgãos). Fórmula Mifflin-St Jeor.</p>
                <p>🏃 <b>Gasto com atividades: +${actBurn} kcal</b> — movimento do dia e treinos (fator de atividade).</p>
                <p>🎯 <b>Ajuste do objetivo: ${calc.cal_diff > 0 ? '+' : ''}${calc.cal_diff} kcal</b> → meta de <b>${calc.target_calories} kcal/dia</b>.</p>
                <p class="text-slate-400 mt-1">Treinos lançados na aba Treinos somam calorias extras ao seu dia.</p>
            `;
        }
        if (deficitEl) {
            if (calc.cal_diff < 0) {
                deficitEl.textContent = `${calc.cal_diff} kcal (Déficit)`;
                deficitEl.className = "font-black text-xs px-2 py-0.5 rounded-full bg-white/20";
            } else if (calc.cal_diff > 0) {
                deficitEl.textContent = `+${calc.cal_diff} kcal (Superávit)`;
                deficitEl.className = "font-black text-xs px-2 py-0.5 rounded-full bg-white/20";
            } else {
                deficitEl.textContent = `Equilíbrio (0 kcal)`;
                deficitEl.className = "font-black text-xs px-2 py-0.5 rounded-full bg-white/20";
            }
        }

        if (targetCalEl) targetCalEl.textContent = `${calc.target_calories} kcal/dia`;
        if (pEl) pEl.textContent = `${calc.target_protein}g`;
        if (cEl) cEl.textContent = `${calc.target_carbs}g`;
        if (fEl) fEl.textContent = `${calc.target_fat}g`;
        if (waterEl) waterEl.textContent = `${calc.target_water} ml`;

        // Se for quizOnlyMode, ocultar campos de conta e mostrar botão de salvar perfil
        const regSection = document.getElementById('plan-register-section');
        const quizOnlySection = document.getElementById('plan-quizonly-section');

        if (this.quizOnlyMode) {
            if (regSection) regSection.classList.add('hidden');
            if (quizOnlySection) quizOnlySection.classList.remove('hidden');
        } else {
            if (regSection) regSection.classList.remove('hidden');
            if (quizOnlySection) quizOnlySection.classList.add('hidden');
        }

        if (loadingEl) loadingEl.classList.add('hidden');
        if (contentEl) contentEl.classList.remove('hidden');

        if (typeof App !== 'undefined' && App.playSound) App.playSound('success');
    },

    async submitRegistration(event) {
        if (event) event.preventDefault();

        const nameInput = document.getElementById('quiz-reg-name');
        const emailInput = document.getElementById('quiz-reg-email');
        const pwdInput = document.getElementById('quiz-reg-password');

        const name = nameInput?.value.trim();
        const email = emailInput?.value.trim();
        const password = pwdInput?.value;

        if (!name || !email || !password) {
            App.showToast("Preencha seu nome, e-mail e senha para criar sua conta.", "warning");
            return;
        }

        const calc = this.data.calculated || {};

        const payload = {
            name: name,
            email: email,
            password: password,
            gender: this.data.gender,
            age: this.data.age,
            weight: this.data.weight,
            height: this.data.height,
            activity_level: this.data.activity_level,
            goal: this.data.goal,
            pace: this.data.pace,
            target_calories: calc.target_calories,
            target_protein: calc.target_protein,
            target_carbs: calc.target_carbs,
            target_fat: calc.target_fat,
            target_water: calc.target_water
        };

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok && data.success) {
                Auth.currentUser = data.user;
                Auth.token = data.token;
                localStorage.setItem('vivaleve_user', JSON.stringify(data.user));
                localStorage.setItem('vivaleve_token', data.token);
                document.cookie = `vivaleve_uid=${data.user.id}; path=/; max-age=31536000; SameSite=Lax`;
                if (Auth.saveAccount) Auth.saveAccount(data.user);

                Auth.updateUI();
                this.close();

                if (typeof App !== 'undefined') {
                    if (App.playSound) App.playSound('victory');
                    App.triggerConfetti();
                    App.showToast(`🎉 Parabéns, ${data.user.name}! Seu plano de dieta VivaLeve está pronto!`);
                    App.loadProfile();
                    Diary.load(App.currentDate);
                    CheatDay.load();
                    ProfileCharts.load();
                    if (typeof Streak !== 'undefined') Streak.load();
                    if (typeof FamilyBattle !== 'undefined') FamilyBattle.load();
                    if (typeof MealAssistant !== 'undefined') MealAssistant.loadMenu();
                }
            } else {
                App.showToast(data.detail || data.message || "Erro ao registrar sua conta.", "error");
            }
        } catch (err) {
            console.error("Erro no cadastro:", err);
            App.showToast("Erro ao conectar com o servidor.", "error");
        }
    },

    async submitQuizUpdate() {
        const calc = this.data.calculated;
        if (!calc) return;

        const userId = Auth.getUserId();
        const payload = {
            user_id: userId,
            gender: this.data.gender,
            age: this.data.age,
            weight: this.data.weight,
            height: this.data.height,
            activity_level: this.data.activity_level,
            goal: this.data.goal,
            target_calories: calc.target_calories,
            target_protein: calc.target_protein,
            target_carbs: calc.target_carbs,
            target_fat: calc.target_fat,
            target_water: calc.target_water
        };

        try {
            const res = await fetch('/api/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                this.close();
                if (typeof App !== 'undefined') {
                    if (App.playSound) App.playSound('victory');
                    App.triggerConfetti();
                    App.showToast("Suas metas nutricionais foram recalculadas e atualizadas com sucesso! 🎯");
                    App.loadProfile();
                    Diary.load(App.currentDate);
                    ProfileCharts.load();
                }
            } else {
                App.showToast("Erro ao salvar novas metas no perfil.", "error");
            }
        } catch (e) {
            console.error(e);
            App.showToast("Erro ao comunicar com o servidor.", "error");
        }
    }
};

window.Onboarding = Onboarding;
