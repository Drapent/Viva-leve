/**
 * VivaLeve - Módulo de Avatar Evolutivo 3D
 *
 * Orquestra as três peças:
 *   - Avatar3D  : o boneco 3D (three.js)
 *   - BodyScale  : a balança digital (Bluetooth + manual)
 *   - Wearable   : o relógio digital (Bluetooth + manual)
 *
 * A foto do usuário vira o rosto do boneco; a leitura da balança vira o corpo;
 * o nível/XP/coins e a loja de itens continuam como antes.
 */

const Avatar = {
    data: null,
    model: null,
    _3dReady: false,

    async load() {
        try {
            const res = await fetch('/api/avatar');
            this.data = await res.json();
            this.render();
            this.loadModel();
        } catch (e) {
            console.error('Erro ao carregar avatar:', e);
        }
    },

    /** Busca o pacote completo do modelo 3D (corpo + rosto + roupa). */
    async loadModel() {
        try {
            const res = await fetch('/api/avatar/model');
            this.model = await res.json();
            this.applyModel();
        } catch (e) {
            console.error('Erro ao carregar modelo 3D:', e);
        }
    },

    applyModel() {
        if (!this.model) return;
        if (window.Avatar3D && this._3dReady) Avatar3D.setModel(this.model);
        if (this.model.photo_url && window.Avatar3D && this._3dReady) {
            Avatar3D.setPhoto(this.model.photo_url);
        }
        this.renderEvolution();
    },

    /** Recebe um modelo de corpo novo (vindo da balança) e reposiciona o boneco. */
    setBodyModel(bodyModel) {
        if (!bodyModel) return;
        if (window.Avatar3D && this._3dReady) {
            // Mantém rosto/roupa atuais; troca só o corpo
            Avatar3D.setModel({
                body: bodyModel,
                appearance: this.model?.appearance,
                equipped: this.model?.equipped,
                outfit_catalog: this.model?.outfit_catalog,
            });
        }
        this.renderBodyStats(bodyModel);
        if (window.BodyScale) BodyScale.render();
    },

    // ---------------------------------------------------------------
    //  RENDER
    // ---------------------------------------------------------------
    render() {
        if (!this.data) return;
        const d = this.data;

        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

        set('avatar-level', d.level);
        set('avatar-xp-current', d.xp);
        set('avatar-xp-next', d.level * 200);
        set('avatar-coins', d.coins);
        set('avatar-shop-coins', d.coins);

        const bar = document.getElementById('avatar-xp-bar');
        if (bar) {
            const pct = Math.min(100, (d.xp / (d.level * 200)) * 100);
            bar.style.width = `${pct}%`;
        }

        if (d.body) this.renderBodyStats(d.body);

        const getEquipName = (id) => {
            const item = (d.shop_catalog || []).find(i => i.id === id);
            return item ? `${item.icon} ${item.name}` : (id || '—');
        };
        set('avatar-equipped-outfit', getEquipName(d.equipped_outfit));
        set('avatar-equipped-accessory', getEquipName(d.equipped_accessory));
        set('avatar-equipped-aura', getEquipName(d.equipped_aura));

        this.renderShop();
        this.loadMissions();
    },

    /** Card "de onde vem o corpo do boneco". */
    renderBodyStats(b) {
        if (!b) return;
        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        set('avatar-body-fat', `${b.body_fat}%`);
        set('avatar-muscle-mass', `${b.muscle_pct}%`);
        set('body-weight', `${b.weight} kg`);
        set('body-lean', `${b.lean_mass} kg`);
        set('body-fatmass', `${b.fat_mass} kg`);
        set('body-bmi', `${b.bmi}`);
        set('body-ffmi', `${b.ffmi}`);
        set('body-class', b.body_fat_class || '—');
        set('body-source', b.measured ? 'Balança digital' : 'Estimativa pelo perfil');

        const src = document.getElementById('body-source-badge');
        if (src) {
            src.textContent = b.measured ? '📡 Medido na balança' : '🧮 Estimado';
            src.className = 'px-2.5 py-1 rounded-full text-[10px] font-black ' +
                (b.measured ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700');
        }

        // barra gordo vs magro
        const fat = document.getElementById('body-fat-bar');
        if (fat) fat.style.width = `${Math.min(100, b.body_fat)}%`;
        const mus = document.getElementById('body-muscle-bar');
        if (mus) mus.style.width = `${Math.min(100, b.muscle_pct)}%`;

        const extra = document.getElementById('body-extra-metrics');
        if (extra && b.water_pct) {
            extra.innerHTML = `
                <span class="px-2 py-1 rounded-lg bg-sky-50 text-sky-700 text-[10px] font-black">💧 ${b.water_pct}% água</span>
                ${b.bone_mass ? `<span class="px-2 py-1 rounded-lg bg-stone-100 text-stone-700 text-[10px] font-black">🦴 ${b.bone_mass} kg ósseo</span>` : ''}
                ${b.visceral_fat ? `<span class="px-2 py-1 rounded-lg bg-orange-50 text-orange-700 text-[10px] font-black">🫀 ${b.visceral_fat} visceral</span>` : ''}
                ${b.bmr ? `<span class="px-2 py-1 rounded-lg bg-violet-50 text-violet-700 text-[10px] font-black">🔥 ${Math.round(b.bmr)} kcal basais</span>` : ''}
            `;
        }
    },

    renderShop() {
        const container = document.getElementById('avatar-shop-list');
        if (!container || !this.data) return;

        const catalog = this.data.shop_catalog || [];
        const owned = this.data.unlocked_items_json ? JSON.parse(this.data.unlocked_items_json) : ['regata_basica', 'shaker', 'nenhuma'];

        container.innerHTML = catalog.map(item => {
            const isOwned = owned.includes(item.id);
            const canAfford = this.data.coins >= item.price;
            const isEquipped = this.data.equipped_outfit === item.id
                || this.data.equipped_accessory === item.id
                || this.data.equipped_aura === item.id;

            let btnClass, btnText, btnAction;
            if (isEquipped) {
                btnClass = 'bg-emerald-100 text-emerald-700 border-emerald-200';
                btnText = 'Equipado';
                btnAction = '';
            } else if (isOwned) {
                btnClass = 'bg-violet-100 text-violet-700 border-violet-200 hover:bg-violet-200';
                btnText = 'Equipar';
                btnAction = `onclick="Avatar.equip('${item.id}', '${item.category}')"`;
            } else if (canAfford) {
                btnClass = 'bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200';
                btnText = `Comprar (${item.price})`;
                btnAction = `onclick="Avatar.buy('${item.id}')"`;
            } else {
                btnClass = 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed';
                btnText = `${item.price} moedas`;
                btnAction = '';
            }

            return `
                <div class="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col items-center gap-1.5 ${isEquipped ? 'ring-2 ring-emerald-400' : ''}" title="${item.desc || ''}">
                    <span class="text-2xl">${item.icon}</span>
                    <span class="text-[10px] font-black text-slate-700 text-center leading-tight">${item.name}</span>
                    <button ${btnAction} class="w-full py-1.5 px-2 rounded-xl text-[10px] font-black border transition ${btnClass}">
                        ${btnText}
                    </button>
                </div>
            `;
        }).join('');
    },

    async renderEvolution() {
        const el = document.getElementById('avatar-evolution');
        if (!el) return;
        try {
            const res = await fetch('/api/avatar/evolution?limit=60');
            const data = await res.json();
            const t = data.timeline || [];
            if (!t.length) { el.innerHTML = '<p class="text-[11px] text-slate-400 text-center py-3">Sem histórico ainda.</p>'; return; }

            const d = data.delta || {};
            const sign = (v) => (v > 0 ? '+' : '') + v;

            el.innerHTML = `
                <div class="grid grid-cols-4 gap-2 mb-3 text-center">
                    <div class="rounded-xl bg-slate-50 py-2">
                        <span class="text-[9px] font-black text-slate-400 uppercase block">Peso</span>
                        <b class="text-xs font-black ${d.weight <= 0 ? 'text-emerald-600' : 'text-rose-600'}">${sign(d.weight || 0)} kg</b>
                    </div>
                    <div class="rounded-xl bg-slate-50 py-2">
                        <span class="text-[9px] font-black text-slate-400 uppercase block">Gordura</span>
                        <b class="text-xs font-black ${d.body_fat <= 0 ? 'text-emerald-600' : 'text-rose-600'}">${sign(d.body_fat || 0)}%</b>
                    </div>
                    <div class="rounded-xl bg-slate-50 py-2">
                        <span class="text-[9px] font-black text-slate-400 uppercase block">Músculo</span>
                        <b class="text-xs font-black ${d.muscle >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${sign(d.muscle || 0)}%</b>
                    </div>
                    <div class="rounded-xl bg-slate-50 py-2">
                        <span class="text-[9px] font-black text-slate-400 uppercase block">Magra</span>
                        <b class="text-xs font-black ${d.lean_mass >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${sign(d.lean_mass || 0)} kg</b>
                    </div>
                </div>
                <canvas id="avatar-evolution-chart" class="w-full" height="120"></canvas>
            `;
            this.drawEvolutionChart(t);
        } catch (e) {
            console.warn('Histórico de evolução indisponível:', e);
        }
    },

    drawEvolutionChart(timeline) {
        const canvas = document.getElementById('avatar-evolution-chart');
        if (!canvas || typeof Chart === 'undefined') return;
        if (this._chart) { this._chart.destroy(); this._chart = null; }

        const labels = timeline.map(t => t.date.slice(5));
        this._chart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'Gordura %', data: timeline.map(t => t.body_fat), borderColor: '#f43f5e', backgroundColor: 'rgba(244,63,94,.12)', tension: .35, fill: true, pointRadius: 2 },
                    { label: 'Músculo %', data: timeline.map(t => t.muscle_mass), borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,.12)', tension: .35, fill: true, pointRadius: 2 },
                    { label: 'Peso kg', data: timeline.map(t => t.weight), borderColor: '#6366f1', borderDash: [4, 3], tension: .35, pointRadius: 0, yAxisID: 'y1' },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { boxWidth: 10, font: { size: 10 } } } },
                scales: {
                    y: { position: 'left', grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
                    y1: { position: 'right', grid: { display: false }, ticks: { font: { size: 9 } } },
                    x: { grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 6 } },
                },
            },
        });
    },

    // ---------------------------------------------------------------
    //  LOJA
    // ---------------------------------------------------------------
    async buy(itemId) {
        try {
            const res = await fetch('/api/avatar/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId }),
            });
            const data = await res.json();
            if (res.ok && data.success) {
                App?.showToast(data.message || 'Item comprado!', 'success');
                App?.playSound?.('success');
                this.load();
            } else {
                App?.showToast(data.detail || data.message || 'Erro ao comprar', 'error');
            }
        } catch (e) {
            console.error(e);
            App?.showToast('Erro ao conectar', 'error');
        }
    },

    async equip(itemId, category) {
        try {
            const res = await fetch('/api/avatar/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, category }),
            });
            const data = await res.json();
            if (res.ok && data.success) {
                App?.showToast(data.message || 'Item equipado!', 'success');
                this.load();
                this.loadModel();
            } else {
                App?.showToast(data.detail || data.message || 'Erro ao equipar', 'error');
            }
        } catch (e) {
            console.error(e);
            App?.showToast('Erro ao conectar', 'error');
        }
    },

    // ---------------------------------------------------------------
    //  FOTO -> AVATAR 3D (IA)
    // ---------------------------------------------------------------
    async uploadPhoto() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.capture = 'environment';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) this.processPhoto(file);
        };
        input.click();
    },

    async processPhoto(file) {
        if (file.size > 12 * 1024 * 1024) {
            App?.showToast('Foto muito grande. Escolha uma de até 12 MB.', 'error');
            return;
        }
        const toastEl = document.getElementById('avatar-ai-status');
        if (toastEl) {
            toastEl.classList.remove('hidden');
            toastEl.innerHTML = '<span class="inline-block animate-spin mr-2">🤖</span> A IA está analisando seu rosto e montando o avatar 3D...';
        }

        try {
            const fd = new FormData();
            fd.append('file', file);
            const res = await fetch('/api/avatar/photo/analyze', { method: 'POST', body: fd });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Erro ao analisar');

            this.model = data.model;
            if (window.Avatar3D && this._3dReady) {
                Avatar3D.setPhoto(data.photo_url);
                Avatar3D.setModel(data.model);
            }
            this.renderAppearance(data.appearance, data.engine);
            this.load();

            App?.showToast(data.message || '✨ Avatar 3D gerado!', 'success');
            App?.playSound?.('success');
            App?.triggerConfetti?.();
        } catch (e) {
            console.error('Erro ao gerar avatar 3D:', e);
            if (toastEl) {
                toastEl.innerHTML = '<span class="mr-2">❌</span> Não consegui gerar o avatar. Tente outra foto.';
            }
            App?.showToast(e.message || 'Erro ao gerar avatar', 'error');
        }
    },

    /** Mostra os traços que a IA identificou (editáveis). */
    renderAppearance(app, engine) {
        const box = document.getElementById('avatar-appearance');
        if (!box || !app) return;
        const st = document.getElementById('avatar-ai-status');
        if (st) {
            st.innerHTML = engine
                ? `✅ Gerado com ${engine} · <button onclick="Avatar.regenerate()" class="underline font-black">gerar de novo</button>`
                : '✅ Avatar gerado no modo local';
        }
        box.innerHTML = `
            <div class="flex items-center gap-2 flex-wrap">
                <span class="px-2 py-1 rounded-lg text-[10px] font-black" style="background:${app.skin_tone};color:#fff">Pele</span>
                <span class="px-2 py-1 rounded-lg text-[10px] font-black" style="background:${app.hair_color};color:#fff">Cabelo</span>
                <span class="px-2 py-1 rounded-lg bg-slate-100 text-slate-700 text-[10px] font-black">${app.hair_style}</span>
                <span class="px-2 py-1 rounded-lg bg-slate-100 text-slate-700 text-[10px] font-black">${app.face_shape}</span>
                ${app.facial_hair !== 'nenhum' ? `<span class="px-2 py-1 rounded-lg bg-slate-100 text-slate-700 text-[10px] font-black">${app.facial_hair}</span>` : ''}
                <span class="px-2 py-1 rounded-lg bg-slate-100 text-slate-700 text-[10px] font-black">ombros: ${app.shoulder_width}</span>
            </div>
            <div class="mt-2">
                <label class="text-[10px] font-black text-slate-400 uppercase">Cor da pele</label>
                <input type="color" value="${app.skin_tone}" onchange="Avatar.setTrait('skin_tone', this.value)" class="w-10 h-7 rounded-lg border border-slate-200 bg-white">
                <label class="text-[10px] font-black text-slate-400 uppercase ml-2">Cabelo</label>
                <input type="color" value="${app.hair_color}" onchange="Avatar.setTrait('hair_color', this.value)" class="w-10 h-7 rounded-lg border border-slate-200 bg-white">
            </div>
        `;
    },

    async setTrait(key, value) {
        if (!this.model?.appearance) return;
        const traits = { ...this.model.appearance, [key]: value };
        try {
            const res = await fetch('/api/avatar/appearance', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ traits }),
            });
            const data = await res.json();
            if (res.ok) {
                this.model.appearance = data.appearance;
                this.model.outfit_catalog = data.model.outfit_catalog;
                Avatar3D.setModel(this.model);
                App?.showToast('Avatar atualizado!', 'success');
            }
        } catch (e) { console.error(e); }
    },

    regenerate() {
        const stored = this.data?.photo_url;
        if (stored) {
            Avatar3D.setPhoto(stored);
            this.loadModel();
            App?.showToast('Avatar reconstruído a partir da foto.', 'success');
        } else {
            this.uploadPhoto();
        }
    },

    // ---------------------------------------------------------------
    //  3D: controles
    // ---------------------------------------------------------------
    init3D() {
        if (this._3dReady || !window.Avatar3D) return;
        const ok = Avatar3D.init('avatar-canvas');
        if (!ok) {
            const fb = document.getElementById('avatar-3d-fallback');
            if (fb) fb.classList.remove('hidden');
            return;
        }
        this._3dReady = true;
        if (this.model) this.applyModel();
        else this.loadModel();
    },

    avatarScreenshot() {
        if (!this._3dReady) return;
        const url = Avatar3D.screenshot();
        if (!url) { App?.showToast('Não consegui capturar o avatar.', 'error'); return; }
        const a = document.createElement('a');
        a.href = url;
        a.download = `meu-avatar-vivaleve-${Date.now()}.png`;
        a.click();
        App?.showToast('📸 Avatar salvo na galeria!', 'success');
    },

    // ---------------------------------------------------------------
    //  MISSÕES
    // ---------------------------------------------------------------
    async loadMissions() {
        try {
            const res = await fetch('/api/gamification/missions');
            this.renderMissions(await res.json());
        } catch (e) {
            console.warn('Missões indisponíveis:', e);
        }
    },

    renderMissions(missions) {
        const container = document.getElementById('avatar-missions-list');
        if (!container) return;
        if (!missions || !missions.length) {
            container.innerHTML = `<div class="text-center py-8 text-slate-400"><span class="text-3xl block mb-2">🎯</span><p class="text-sm font-bold">Nenhuma missão disponível hoje</p></div>`;
            return;
        }
        container.innerHTML = missions.map(m => `
            <div class="p-3 rounded-2xl ${m.completed ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-50 border border-slate-200'}">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex-1 min-w-0">
                        <h4 class="font-black text-slate-800 text-sm truncate">${m.title}</h4>
                        <p class="text-[11px] text-slate-500">${m.description}</p>
                    </div>
                    <div class="shrink-0">
                        ${m.completed
                            ? '<span class="text-emerald-600 font-black text-xs">✓ Concluída</span>'
                            : `<button onclick="Avatar.completeMission(${m.id})" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-black shadow-sm hover:scale-105 transition">+${m.points} pts</button>`}
                    </div>
                </div>
            </div>
        `).join('');
    },

    async completeMission(missionId) {
        try {
            const res = await fetch('/api/missions/claim', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mission_id: missionId }),
            });
            const data = await res.json();
            if (res.ok && data.success) {
                App?.showToast(data.message, 'success');
                App?.triggerConfetti?.();
                App?.playSound?.('success');
                this.load();
            } else {
                App?.showToast(data.detail || 'Erro ao completar missão', 'error');
            }
        } catch (e) {
            console.error(e);
            App?.showToast('Erro ao conectar', 'error');
        }
    },

    init() {
        this.load();
    },
};

window.Avatar = Avatar;