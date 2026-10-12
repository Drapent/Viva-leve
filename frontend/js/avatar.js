/**
 * VivaLeve - Módulo de Avatar Evolutivo
 * Avatar que evolui com base no progresso real do usuário
 */

const Avatar = {
    data: null,
    shopItems: [
        // Roupas
        { id: 'regata_basica', name: 'Regata Básica', category: 'roupa', price: 0, emoji: '👕', owned: true },
        { id: 'regata_growth', name: 'Regata Growth', category: 'roupa', price: 120, emoji: '👕' },
        { id: 'dryfit_neon', name: 'Dry-Fit Neon', category: 'roupa', price: 180, emoji: '👕' },
        { id: 'moletom_oversized', name: 'Moletom Oversized', category: 'roupa', price: 250, emoji: '🧥' },
        { id: 'top_power_pink', name: 'Top Power Pink', category: 'roupa', price: 150, emoji: '👚' },
        // Acessórios
        { id: 'shaker', name: 'Shaker', category: 'acessorio', price: 0, emoji: '🥤', owned: true },
        { id: 'luvas', name: 'Luvas', category: 'acessorio', price: 100, emoji: '🧤' },
        { id: 'galao_2l', name: 'Galão 2L', category: 'acessorio', price: 140, emoji: '🫗' },
        { id: 'cinto_lombar', name: 'Cinto Lombar', category: 'acessorio', price: 200, emoji: '🔧' },
        { id: 'tenis_dourado', name: 'Tênis Dourado', category: 'acessorio', price: 300, emoji: '👟' },
        // Auras
        { id: 'nenhuma', name: 'Nenhuma', category: 'aura', price: 0, emoji: '❌', owned: true },
        { id: 'aura_fogo', name: 'Aura Fogo', category: 'aura', price: 250, emoji: '🔥' },
        { id: 'aura_raio', name: 'Aura Raio', category: 'aura', price: 400, emoji: '⚡' },
        { id: 'aura_dourada', name: 'Aura Dourada', category: 'aura', price: 600, emoji: '✨' },
    ],

    async load() {
        try {
            const res = await fetch('/api/avatar');
            this.data = await res.json();
            this.render();
        } catch (e) {
            console.error('Erro ao carregar avatar:', e);
        }
    },

    render() {
        if (!this.data) return;

        // Nível e XP
        const levelEl = document.getElementById('avatar-level');
        const xpCurrentEl = document.getElementById('avatar-xp-current');
        const xpNextEl = document.getElementById('avatar-xp-next');
        const xpBarEl = document.getElementById('avatar-xp-bar');
        const coinsEl = document.getElementById('avatar-coins');
        const bodyFatEl = document.getElementById('avatar-body-fat');
        const muscleMassEl = document.getElementById('avatar-muscle-mass');
        const shopCoinsEl = document.getElementById('avatar-shop-coins');

        if (levelEl) levelEl.textContent = this.data.level;
        if (xpCurrentEl) xpCurrentEl.textContent = this.data.xp;
        if (xpNextEl) xpNextEl.textContent = (this.data.level) * 200;
        if (xpBarEl) {
            const xpForNext = this.data.level * 200;
            const xpProgress = this.data.xp;
            const pct = Math.min(100, (xpProgress / xpForNext) * 100);
            xpBarEl.style.width = `${pct}%`;
        }
        if (coinsEl) coinsEl.textContent = this.data.coins;
        if (shopCoinsEl) shopCoinsEl.textContent = this.data.coins;
        if (bodyFatEl) bodyFatEl.textContent = `${this.data.body_fat_visual}%`;
        if (muscleMassEl) muscleMassEl.textContent = `${this.data.muscle_mass_visual}%`;

        // Itens equipados
        const outfitEl = document.getElementById('avatar-equipped-outfit');
        const accessoryEl = document.getElementById('avatar-equipped-accessory');
        const auraEl = document.getElementById('avatar-equipped-aura');

        const getEquipName = (id) => {
            const item = this.shopItems.find(i => i.id === id);
            return item ? `${item.emoji} ${item.name}` : id;
        };

        if (outfitEl) outfitEl.textContent = getEquipName(this.data.equipped_outfit);
        if (accessoryEl) accessoryEl.textContent = getEquipName(this.data.equipped_accessory);
        if (auraEl) auraEl.textContent = getEquipName(this.data.equipped_aura);

        // Foto
        const photoImg = document.getElementById('avatar-photo-img');
        const photoPlaceholder = document.getElementById('avatar-photo-placeholder');
        if (this.data.photo_url) {
            if (photoImg) {
                photoImg.src = this.data.photo_url;
                photoImg.classList.remove('hidden');
            }
            if (photoPlaceholder) photoPlaceholder.classList.add('hidden');
        } else {
            if (photoImg) photoImg.classList.add('hidden');
            if (photoPlaceholder) photoPlaceholder.classList.remove('hidden');
        }

        // Loja
        this.renderShop();

        // Missões
        this.loadMissions();
    },

    renderShop() {
        const container = document.getElementById('avatar-shop-list');
        if (!container) return;

        const owned = this.data?.unlocked_items_json
            ? JSON.parse(this.data.unlocked_items_json)
            : ['regata_basica', 'shaker'];

        container.innerHTML = this.shopItems.map(item => {
            const isOwned = owned.includes(item.id);
            const canAfford = this.data && this.data.coins >= item.price;
            const isEquipped = this.data && (
                this.data.equipped_outfit === item.id ||
                this.data.equipped_accessory === item.id ||
                this.data.equipped_aura === item.id
            );

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
                <div class="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col items-center gap-1.5 ${isEquipped ? 'ring-2 ring-emerald-400' : ''}">
                    <span class="text-2xl">${item.emoji}</span>
                    <span class="text-[10px] font-black text-slate-700 text-center leading-tight">${item.name}</span>
                    <button ${btnAction} class="w-full py-1.5 px-2 rounded-xl text-[10px] font-black border transition ${btnClass}">
                        ${btnText}
                    </button>
                </div>
            `;
        }).join('');
    },

    async buy(itemId) {
        const item = this.shopItems.find(i => i.id === itemId);
        if (!item) return;

        try {
            const res = await fetch('/api/avatar/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast(`Você comprou: ${item.name}! 🎉`, 'success');
                    App.playSound('success');
                }
                this.load();
            } else {
                if (typeof App !== 'undefined') {
                    App.showToast(data.detail || 'Erro ao comprar item', 'error');
                }
            }
        } catch (e) {
            console.error('Erro ao comprar:', e);
            if (typeof App !== 'undefined') App.showToast('Erro ao conectar', 'error');
        }
    },

    async equip(itemId, category) {
        try {
            const res = await fetch('/api/avatar/equip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_id: itemId, category: category })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                if (typeof App !== 'undefined') App.showToast('Item equipado!', 'success');
                this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.detail || 'Erro ao equipar', 'error');
            }
        } catch (e) {
            console.error('Erro ao equipar:', e);
            if (typeof App !== 'undefined') App.showToast('Erro ao conectar', 'error');
        }
    },

    async uploadPhoto() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async (ev) => {
                const photoUrl = ev.target.result;
                try {
                    const res = await fetch('/api/avatar/photo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ photo_url: photoUrl })
                    });

                    const data = await res.json();
                    if (res.ok && data.success) {
                        if (typeof App !== 'undefined') {
                            App.showToast('Foto atualizada! 📸', 'success');
                        }
                        this.load();
                    } else {
                        if (typeof App !== 'undefined') App.showToast(data.detail || 'Erro ao atualizar foto', 'error');
                    }
                } catch (err) {
                    console.error('Erro ao enviar foto:', err);
                    if (typeof App !== 'undefined') App.showToast('Erro ao enviar foto', 'error');
                }
            };
            reader.readAsDataURL(file);
        };
        input.click();
    },

    async loadMissions() {
        try {
            const res = await fetch('/api/gamification/missions');
            const missions = await res.json();
            this.renderMissions(missions);
        } catch (e) {
            console.error('Erro ao carregar missões:', e);
        }
    },

    renderMissions(missions) {
        const container = document.getElementById('avatar-missions-list');
        if (!container) return;

        if (!missions || missions.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <span class="text-3xl block mb-2">🎯</span>
                    <p class="text-sm font-bold">Nenhuma missão disponível hoje</p>
                </div>
            `;
            return;
        }

        container.innerHTML = missions.map(m => `
            <div class="p-3 rounded-2xl ${m.completed ? 'bg-emerald-50 border border-emerald-200' : 'bg-slate-50 border border-slate-200'}">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <h4 class="font-black text-slate-800 text-sm">${m.title}</h4>
                        <p class="text-[11px] text-slate-500">${m.description}</p>
                    </div>
                    <div class="text-right ml-2">
                        ${m.completed
                            ? '<span class="text-emerald-600 font-black text-xs">✓ Concluída</span>'
                            : `<button onclick="Avatar.completeMission(${m.id})" class="px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-black shadow-sm hover:scale-105 transition">+${m.points} pts</button>`
                        }
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
                body: JSON.stringify({ mission_id: missionId })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                if (typeof App !== 'undefined') {
                    App.showToast(data.message, 'success');
                    App.triggerConfetti();
                    App.playSound('success');
                }
                this.load();
            } else {
                if (typeof App !== 'undefined') App.showToast(data.detail || 'Erro ao completar missão', 'error');
            }
        } catch (e) {
            console.error('Erro ao completar missão:', e);
            if (typeof App !== 'undefined') App.showToast('Erro ao conectar', 'error');
        }
    },

    init() {
        this.load();
    }
};

window.Avatar = Avatar;
