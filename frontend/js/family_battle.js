/**
 * VivaLeve - Batalha Familiar do Dia do Lixo & Gestão da Família Real
 */

const FamilyBattle = {
    battleData: null,
    missionsData: [],

    async load() {
        // 1. Render instantâneo de cache local
        try {
            const cachedBattle = localStorage.getItem('vivaleve_family_battle');
            const cachedMissions = localStorage.getItem('vivaleve_family_missions');
            if (cachedBattle) this.battleData = JSON.parse(cachedBattle);
            if (cachedMissions) this.missionsData = JSON.parse(cachedMissions);
            if (this.battleData || this.missionsData.length > 0) {
                this.renderAll();
            }
        } catch (e) {}

        // 2. Busca atualizada em segundo plano
        await Promise.all([
            this.fetchBattleData(),
            this.fetchMissions()
        ]);
        this.renderAll();
    },

    async fetchBattleData() {
        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const date = (typeof App !== 'undefined') ? (App.currentDate || new Date().toISOString().split('T')[0]) : new Date().toISOString().split('T')[0];
            const res = await fetch(`/api/gamification/family-battle?user_id=${userId}&date=${date}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.battleData = data;
                    localStorage.setItem('vivaleve_family_battle', JSON.stringify(data));
                }
            }
        } catch (err) {
            // Silencioso em offline
        }
    },

    async fetchMissions() {
        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const date = (typeof App !== 'undefined') ? (App.currentDate || new Date().toISOString().split('T')[0]) : new Date().toISOString().split('T')[0];
            const res = await fetch(`/api/gamification/missions?user_id=${userId}&date=${date}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.missionsData = data;
                    localStorage.setItem('vivaleve_family_missions', JSON.stringify(data));
                }
            }
        } catch (err) {
            // Silencioso em offline
        }
    },

    renderAll() {
        // Se o usuário ainda não participa de uma família real
        if (!this.battleData || this.battleData.in_family === false) {
            this.renderNoFamilyCard();
            this.renderMissions();
            return;
        }

        this.renderFamilyHeader();
        this.renderChampionBanner();
        this.renderPodium();
        this.renderFullRanking();
        this.renderMissions();
    },

    renderNoFamilyCard() {
        const headerEl = document.getElementById('battle-header-banner');
        if (headerEl) {
            headerEl.innerHTML = `
                <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 rounded-3xl p-6 text-white shadow-xl shadow-emerald-500/20">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div>
                            <span class="px-3 py-1 rounded-full bg-white/20 text-[10px] font-black uppercase tracking-wider">Novo Recurso</span>
                            <h2 class="text-xl sm:text-2xl font-black mt-2 leading-tight">Família VivaLeve & Batalha do Dia do Lixo</h2>
                            <p class="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl">
                                Crie o grupo da sua casa ou entre com o código de convite enviado por um parente. Juntos, vocês competem de forma divertida e quem vencer escolhe o cardápio do domingo!
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        const choiceContainer = document.getElementById('battle-champion-choice-container');
        if (choiceContainer) {
            choiceContainer.innerHTML = `
                <div class="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm text-center">
                    <div class="w-16 h-16 mx-auto rounded-3xl bg-amber-50 text-amber-500 flex items-center justify-center text-3xl mb-4 shadow-inner">
                        👨‍👩‍👧‍👦
                    </div>
                    <h3 class="text-lg font-black text-slate-800">Você ainda não está em um grupo de família</h3>
                    <p class="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-6">
                        Para participar da Batalha Familiar do Dia do Lixo, crie o grupo da sua família ou digite o código de convite recebido.
                    </p>

                    <div class="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
                        <button onclick="FamilyBattle.openCreateFamilyModal()" class="btn-primary-gradient w-full sm:w-auto px-6 py-3.5 rounded-2xl text-xs font-black shadow-md shadow-emerald-500/20 hover:scale-105 transition flex items-center justify-center gap-2">
                            <span>✨</span>
                            <span>Criar Minha Família (+50 pts)</span>
                        </button>
                        <button onclick="FamilyBattle.openJoinFamilyModal()" class="w-full sm:w-auto px-6 py-3.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-black transition flex items-center justify-center gap-2 border border-slate-200">
                            <span>🔑</span>
                            <span>Entrar com Código (+30 pts)</span>
                        </button>
                    </div>
                </div>
            `;
        }

        const podiumContainer = document.getElementById('battle-podium-container');
        if (podiumContainer) podiumContainer.innerHTML = '';

        const listEl = document.getElementById('battle-ranking-list');
        if (listEl) {
            listEl.innerHTML = `
                <div class="p-6 text-center text-slate-400 text-xs">
                    Crie ou entre em uma família para ver o ranking dos seus parentes aqui!
                </div>
            `;
        }
    },

    renderFamilyHeader() {
        const headerEl = document.getElementById('battle-header-banner');
        if (!headerEl || !this.battleData) return;

        const fam = this.battleData.family || {};
        const days = this.battleData.days_remaining;
        const daysText = days === 0 ? '🏁 Hoje é dia de apuração!' : `⏳ Faltam ${days} dias para o Domingo Livre`;

        headerEl.innerHTML = `
            <div class="bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-600 rounded-3xl p-5 sm:p-6 text-white shadow-xl shadow-emerald-500/20">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="text-2xl">🏆</span>
                            <span class="px-2.5 py-0.5 rounded-full bg-white/20 text-[10px] font-black uppercase tracking-wider">
                                ${fam.name || 'Família VivaLeve'}
                            </span>
                        </div>
                        <h2 class="text-lg sm:text-xl font-black tracking-tight leading-tight">Batalha Familiar do Dia do Lixo</h2>
                        <p class="text-xs text-emerald-100 mt-1 max-w-xl">
                            Quem pontuar mais na semana vira o <b>Rei/Rainha da Semana 👑</b> e ganha o poder de escolher a refeição livre de domingo!
                        </p>

                        <!-- Código de Convite com Cópia Rápida -->
                        <div class="mt-3 inline-flex items-center gap-2 bg-white/20 backdrop-blur-md px-3.5 py-1.5 rounded-2xl border border-white/30 text-xs font-bold">
                            <span>🔑 Código da Família: <b class="font-mono text-amber-200 select-all">${fam.invite_code || 'VIVA-0000'}</b></span>
                            <button onclick="FamilyBattle.copyInviteCode('${fam.invite_code}')" class="px-2 py-0.5 rounded-xl bg-white text-emerald-800 text-[10px] font-black hover:bg-emerald-50 transition active:scale-95" title="Copiar código de convite">
                                📋 Copiar
                            </button>
                        </div>
                    </div>

                    <div class="flex flex-col gap-2 shrink-0">
                        <div class="bg-white/15 backdrop-blur-md rounded-2xl p-3 border border-white/20 text-center">
                            <div class="text-xs font-black text-white">${this.battleData.week_display || 'Semana Atual'}</div>
                            <div class="text-[11px] text-emerald-100 font-bold mt-0.5">${daysText}</div>
                        </div>

                        <div class="flex items-center gap-2">
                            <button onclick="FamilyBattle.openAddMemberModal()" class="flex-1 py-2 px-3 rounded-2xl bg-white text-emerald-800 font-black text-xs hover:bg-emerald-50 transition shadow-sm text-center">
                                ➕ Adicionar Membro
                            </button>
                            <button onclick="FamilyBattle.leaveFamily()" class="py-2 px-2.5 rounded-2xl bg-white/20 hover:bg-rose-500/80 text-white font-bold text-xs transition" title="Sair da Família">
                                🚪
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    renderChampionBanner() {
        const container = document.getElementById('battle-champion-choice-container');
        if (!container || !this.battleData) return;

        const { leader, is_current_user_leader, cheat_choice } = this.battleData;

        if (cheat_choice) {
            container.innerHTML = `
                <div class="bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 rounded-3xl p-5 text-white shadow-xl shadow-orange-500/20 mb-6 relative overflow-hidden">
                    <div class="absolute -right-6 -bottom-6 text-8xl opacity-15 select-none pointer-events-none">🍕</div>
                    <div class="flex items-start gap-4">
                        <div class="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center text-3xl shadow-inner shrink-0">
                            👑
                        </div>
                        <div class="flex-1">
                            <span class="inline-block px-3 py-0.5 rounded-full bg-white/20 text-[10px] font-black tracking-wider uppercase mb-1">
                                Escolha do Campeão Oficializada!
                            </span>
                            <h3 class="text-base sm:text-lg font-black leading-tight">
                                ${cheat_choice.winner_name} escolheu para o Dia do Lixo da Família:
                            </h3>
                            <div class="mt-2 bg-white/10 backdrop-blur-sm rounded-2xl p-3 border border-white/20">
                                <div class="text-base sm:text-lg font-black text-amber-100 flex items-center gap-2">
                                    <span>🍽️</span> <span>${cheat_choice.chosen_dish}</span>
                                </div>
                                ${cheat_choice.restaurant_name ? `
                                    <div class="text-xs text-amber-200 mt-0.5 font-bold">
                                        📍 Restaurante: ${cheat_choice.restaurant_name}
                                    </div>
                                ` : ''}
                                ${cheat_choice.message ? `
                                    <p class="text-xs text-white/90 italic mt-2">
                                        "${cheat_choice.message}"
                                    </p>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (is_current_user_leader) {
            container.innerHTML = `
                <div class="bg-gradient-to-r from-amber-500 via-yellow-500 to-amber-600 rounded-3xl p-5 text-white shadow-xl shadow-amber-500/25 mb-6 relative">
                    <div class="flex items-start gap-3.5">
                        <div class="w-14 h-14 rounded-2xl bg-white text-amber-700 flex items-center justify-center text-3xl shadow-md shrink-0 animate-crown">
                            👑
                        </div>
                        <div class="flex-1">
                            <span class="inline-block px-3 py-0.5 rounded-full bg-black/20 text-[10px] font-black tracking-wider uppercase mb-1">
                                Poder do Campeão Desbloqueado!
                            </span>
                            <h3 class="text-base sm:text-lg font-black leading-tight text-white drop-shadow-sm">
                                Parabéns! Você é o líder da família nesta semana!
                            </h3>
                            <p class="text-xs text-amber-50 mt-1">
                                Como líder, você conquistou o direito oficial de decidir o que a família vai comer no Dia do Lixo!
                            </p>

                            <div class="mt-4 bg-white/95 text-slate-800 rounded-2xl p-4 shadow-lg space-y-3">
                                <div>
                                    <label class="text-[11px] font-black text-slate-600 uppercase">Qual é a sua escolha de refeição livre?</label>
                                    <input type="text" id="leader-chosen-dish" placeholder="Ex: Rodízio de Pizza, Sushi Especial, Hambúrguer Artesanal..." class="w-full mt-1 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800">
                                </div>
                                <div>
                                    <label class="text-[11px] font-black text-slate-600 uppercase">Nome do Restaurante (Opcional)</label>
                                    <input type="text" id="leader-chosen-restaurant" placeholder="Ex: Don Vincenzo Pizzaria, Feito em Casa..." class="w-full mt-1 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800">
                                </div>
                                <div>
                                    <label class="text-[11px] font-black text-slate-600 uppercase">Mensagem para os parentes (Opcional)</label>
                                    <input type="text" id="leader-chosen-message" placeholder="Ex: Preparem-se que esse domingo é por minha conta!" class="w-full mt-1 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800">
                                </div>
                                <button onclick="FamilyBattle.submitLeaderChoice()" class="btn-amber-gradient w-full py-3 rounded-xl text-xs font-black shadow-md transition hover:scale-105">
                                    👑 Decretar Escolha Oficial da Família
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            const leaderName = leader ? leader.name : "Um familiar";
            const leaderPts = leader ? leader.points : 0;
            container.innerHTML = `
                <div class="bg-gradient-to-r from-slate-800 to-slate-900 rounded-3xl p-5 text-white shadow-xl mb-6 flex items-center justify-between gap-4">
                    <div class="flex items-center gap-3.5">
                        <div class="w-12 h-12 rounded-2xl bg-amber-400 text-slate-900 flex items-center justify-center text-2xl font-black shadow-md shrink-0">
                            👑
                        </div>
                        <div>
                            <span class="text-[11px] font-bold text-amber-400 uppercase tracking-wide">Líder Atual da Batalha</span>
                            <h4 class="text-sm sm:text-base font-black text-white">${leaderName} (${leaderPts} pts)</h4>
                            <p class="text-xs text-slate-300">Quem terminar em 1º no domingo decide a refeição livre da casa!</p>
                        </div>
                    </div>
                    <button onclick="App.switchTab('diario')" class="hidden sm:inline-flex px-4 py-2 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-extrabold text-xs transition shrink-0">
                        Pontuar Agora 🚀
                    </button>
                </div>
            `;
        }
    },

    renderPodium() {
        const container = document.getElementById('battle-podium-container');
        if (!container || !this.battleData || !this.battleData.ranking) return;

        const ranking = this.battleData.ranking;
        if (ranking.length === 0) {
            container.innerHTML = '';
            return;
        }

        const top3 = ranking.slice(0, 3);
        const podiumCards = top3.map((m, idx) => {
            const isFirst = idx === 0;
            const podiumClass = isFirst ? 'podium-gold' : (idx === 1 ? 'podium-silver' : 'podium-bronze');
            const medal = isFirst ? '👑 1º Lugar' : (idx === 1 ? '🥈 2º Lugar' : '🥉 3º Lugar');

            return `
                <div class="${podiumClass} rounded-3xl p-4 sm:p-5 flex flex-col justify-between transition-all hover:scale-[1.02] text-center relative ${isFirst ? 'ring-2 ring-amber-400' : ''}">
                    ${m.is_me ? `<span class="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-emerald-600 text-white text-[9px] font-black uppercase">Você</span>` : ''}
                    <div>
                        <div class="text-xs font-black text-slate-700 mb-1">${medal}</div>
                        <div class="w-14 h-14 mx-auto rounded-full bg-slate-100 border-2 border-white shadow-md flex items-center justify-center text-xl font-black text-slate-700 mb-2">
                            ${m.name.charAt(0)}
                        </div>
                        <h4 class="font-black text-sm text-slate-900 truncate">${m.name}</h4>
                        <div class="text-lg font-black text-emerald-600 mt-1">${m.points} <span class="text-xs text-slate-400">pts</span></div>
                    </div>
                    <div class="mt-3 pt-3 border-t border-slate-200/60 flex items-center justify-around text-[11px] text-slate-600 font-bold">
                        <span title="Sequência de dias">🔥 ${m.streak}d</span>
                        <span title="Refeições registradas">🥗 ${m.meals_logged}</span>
                        <span title="Litros de água">💧 ${m.water_liters}L</span>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                ${podiumCards}
            </div>
        `;
    },

    renderFullRanking() {
        const listEl = document.getElementById('battle-ranking-list');
        if (!listEl || !this.battleData || !this.battleData.ranking) return;

        const ranking = this.battleData.ranking;
        listEl.innerHTML = ranking.map((m, idx) => `
            <div class="p-3.5 sm:p-4 rounded-2xl ${m.is_me ? 'bg-emerald-50/80 border-2 border-emerald-300' : 'bg-white border border-slate-100'} shadow-sm flex items-center justify-between gap-3 transition">
                <div class="flex items-center gap-3">
                    <span class="w-7 h-7 rounded-xl flex items-center justify-center text-xs font-black ${
                        idx === 0 ? 'bg-amber-400 text-slate-900 font-black' : 'bg-slate-100 text-slate-600'
                    }">
                        ${idx + 1}º
                    </span>
                    <div class="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-700">
                        ${m.name.charAt(0)}
                    </div>
                    <div>
                        <div class="flex items-center gap-1.5">
                            <span class="font-extrabold text-xs sm:text-sm text-slate-800">${m.name}</span>
                            ${m.is_me ? '<span class="text-[10px] font-black text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full">Você</span>' : ''}
                        </div>
                        <div class="flex items-center gap-2 text-[10px] text-slate-500 font-medium mt-0.5">
                            <span>🔥 ${m.streak} dias</span>
                            <span>•</span>
                            <span>🥗 ${m.meals_logged} refeições</span>
                            <span>•</span>
                            <span>💧 ${m.water_liters}L</span>
                        </div>
                    </div>
                </div>

                <div class="text-right">
                    <div class="font-black text-sm text-emerald-700">${m.points} pts</div>
                    ${m.badges && m.badges.length > 0 ? `<div class="text-[9px] text-slate-400">${m.badges[0]}</div>` : ''}
                </div>
            </div>
        `).join('');
    },

    renderMissions() {
        const container = document.getElementById('daily-missions-container');
        if (!container) return;

        if (!this.missionsData || this.missionsData.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-400">Nenhuma missão gerada para hoje.</p>`;
            return;
        }

        container.innerHTML = this.missionsData.map(m => `
            <div class="mission-card p-3.5 rounded-2xl ${m.completed ? 'bg-emerald-50/70 border border-emerald-200' : 'bg-white border border-slate-100'} shadow-sm flex items-center justify-between gap-3">
                <div class="flex items-start gap-3">
                    <button onclick="FamilyBattle.toggleMission(${m.id})" class="mt-0.5 w-6 h-6 rounded-lg flex items-center justify-center border-2 transition-all ${
                        m.completed ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-300 hover:border-emerald-400 bg-white'
                    }" title="${m.completed ? 'Missão concluída!' : 'Marcar como concluída'}">
                        ${m.completed ? '✓' : ''}
                    </button>
                    <div>
                        <h5 class="text-xs font-black ${m.completed ? 'text-emerald-900 line-through opacity-75' : 'text-slate-800'}">
                            ${m.title}
                        </h5>
                        <p class="text-[11px] text-slate-500 mt-0.5">${m.description}</p>
                    </div>
                </div>
                <div class="shrink-0 text-right">
                    <span class="inline-block px-2.5 py-1 rounded-xl ${m.completed ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'} text-xs font-black">
                        +${m.points} pts
                    </span>
                </div>
            </div>
        `).join('');
    },

    async toggleMission(missionId) {
        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch(`/api/gamification/missions/${missionId}/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });

            const data = await res.json();
            if (data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast(data.message, "success");
                    App.triggerConfetti();
                }
                await this.fetchMissions();
                await this.fetchBattleData();
                this.renderAll();
                if (typeof Streak !== 'undefined') Streak.load();
            }
        } catch (err) {
            console.error("Erro ao completar missão:", err);
        }
    },

    async submitLeaderChoice() {
        const dishInput = document.getElementById('leader-chosen-dish');
        const restInput = document.getElementById('leader-chosen-restaurant');
        const msgInput = document.getElementById('leader-chosen-message');

        const dish = dishInput ? dishInput.value.trim() : "";
        const rest = restInput ? restInput.value.trim() : "";
        const msg = msgInput ? msgInput.value.trim() : "";

        if (!dish) {
            if (typeof App !== 'undefined') App.showToast("Por favor digite o prato ou restaurante desejado!", "warning");
            return;
        }

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/gamification/family-battle/cheat-choice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    chosen_dish: dish,
                    restaurant_name: rest,
                    message: msg
                })
            });

            const data = await res.json();
            if (data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast("👑 Escolha oficializada com sucesso para a família toda!", "success");
                    App.triggerConfetti();
                }
                await this.fetchBattleData();
                this.renderChampionBanner();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao salvar escolha.", "error");
            }
        } catch (err) {
            console.error("Erro ao salvar escolha do campeão:", err);
            if (typeof App !== 'undefined') App.showToast("Falha na comunicação com o servidor.", "error");
        }
    },

    // ----------------- GESTÃO DA FAMÍLIA REAL -----------------

    openCreateFamilyModal() {
        const modal = document.getElementById('modal-create-family');
        if (modal) modal.classList.remove('hidden');
    },

    closeCreateFamilyModal() {
        const modal = document.getElementById('modal-create-family');
        if (modal) modal.classList.add('hidden');
    },

    async submitCreateFamily() {
        const nameInput = document.getElementById('create-family-name-input');
        const familyName = nameInput ? nameInput.value.trim() : "";

        if (!familyName) {
            if (typeof App !== 'undefined') App.showToast("Digite um nome para a sua família!", "warning");
            return;
        }

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/family/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, family_name: familyName })
            });

            const data = await res.json();
            if (data.success) {
                this.closeCreateFamilyModal();
                if (typeof App !== 'undefined') {
                    App.showToast(data.message || "Família criada com sucesso! (+50 pts)", "success");
                    App.triggerConfetti();
                }
                await this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao criar família.", "error");
            }
        } catch (err) {
            console.error("Erro ao criar família:", err);
            if (typeof App !== 'undefined') App.showToast("Falha na comunicação com o servidor.", "error");
        }
    },

    openJoinFamilyModal() {
        const modal = document.getElementById('modal-join-family');
        if (modal) modal.classList.remove('hidden');
    },

    closeJoinFamilyModal() {
        const modal = document.getElementById('modal-join-family');
        if (modal) modal.classList.add('hidden');
    },

    async submitJoinFamily() {
        const codeInput = document.getElementById('join-family-code-input');
        const inviteCode = codeInput ? codeInput.value.trim().toUpperCase() : "";

        if (!inviteCode) {
            if (typeof App !== 'undefined') App.showToast("Digite o código de convite da família!", "warning");
            return;
        }

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/family/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, invite_code: inviteCode })
            });

            const data = await res.json();
            if (data.success) {
                this.closeJoinFamilyModal();
                if (typeof App !== 'undefined') {
                    App.showToast(data.message || "Você entrou na família com sucesso! (+30 pts)", "success");
                    App.triggerConfetti();
                }
                await this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Código inválido ou inexistente.", "error");
            }
        } catch (err) {
            console.error("Erro ao entrar na família:", err);
            if (typeof App !== 'undefined') App.showToast("Falha na comunicação com o servidor.", "error");
        }
    },

    openAddMemberModal() {
        const modal = document.getElementById('modal-add-family-member');
        if (modal) modal.classList.remove('hidden');
    },

    closeAddMemberModal() {
        const modal = document.getElementById('modal-add-family-member');
        if (modal) modal.classList.add('hidden');
    },

    async submitAddMember() {
        const nameInput = document.getElementById('add-member-name-input');
        const emailInput = document.getElementById('add-member-email-input');
        const passInput = document.getElementById('add-member-pass-input');

        const name = nameInput ? nameInput.value.trim() : "";
        const email = emailInput ? emailInput.value.trim() : "";
        const password = passInput ? passInput.value.trim() : "123456";

        if (!name || !email) {
            if (typeof App !== 'undefined') App.showToast("Preencha o nome e e-mail do familiar.", "warning");
            return;
        }

        try {
            const adminUserId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/family/add-member', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    admin_user_id: adminUserId,
                    member_name: name,
                    member_email: email,
                    password: password
                })
            });

            const data = await res.json();
            if (data.success) {
                this.closeAddMemberModal();
                if (nameInput) nameInput.value = "";
                if (emailInput) emailInput.value = "";
                if (typeof App !== 'undefined') {
                    App.showToast(data.message || "Familiar adicionado com sucesso!", "success");
                    App.triggerConfetti();
                }
                await this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao adicionar membro.", "error");
            }
        } catch (err) {
            console.error("Erro ao cadastrar familiar:", err);
            if (typeof App !== 'undefined') App.showToast("Falha na comunicação com o servidor.", "error");
        }
    },

    copyInviteCode(code) {
        if (!code) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(code).then(() => {
                if (typeof App !== 'undefined') App.showToast(`📋 Código ${code} copiado! Envie pelo WhatsApp para sua família.`, "success");
            }).catch(() => {
                prompt("Copie o código de convite da sua família:", code);
            });
        } else {
            prompt("Copie o código de convite da sua família:", code);
        }
    },

    async leaveFamily() {
        const confirmMsg = "Tem certeza que deseja sair do grupo desta família?";
        if (!confirm(confirmMsg)) return;

        try {
            const userId = (typeof Auth !== 'undefined') ? Auth.getUserId() : 1;
            const res = await fetch('/api/family/leave', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });

            const data = await res.json();
            if (data.success) {
                if (typeof App !== 'undefined') App.showToast(data.message || "Você saiu da família.", "info");
                await this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.message || "Erro ao sair.", "error");
            }
        } catch (err) {
            console.error("Erro ao sair da família:", err);
        }
    }
};

// Auto-inicializar no escopo global
if (typeof window !== 'undefined') {
    window.FamilyBattle = FamilyBattle;
}
