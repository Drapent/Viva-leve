/**
 * VivaLeve - Gerenciador Central da Aplicação, Live-Update e Conexão Mobile
 */

const App = {
    currentDate: new Date().toISOString().split('T')[0],
    currentTab: 'diario',
    userProfile: null,
    serverInfo: null,
    appVersion: null,
    qrCodeInstance: null,

    init() {
        console.log("Inicializando VivaLeve Ultra-Rapido & Offline-First...");
        this.loadProfileSync();
        if (typeof Auth !== 'undefined' && Auth.init) {
            Auth.init();
        }
        this.setupNavigation();
        this.setupDateControls();
        this.setupNetworkStatus();
        this.loadInitialData();
        this.setupLiveUpdateChecker();
        this.registerServiceWorker();
    },

    loadProfileSync() {
        try {
            const cached = localStorage.getItem('vivaleve_profile');
            if (cached) {
                this.userProfile = JSON.parse(cached);
                this.updateHeaderProfile();
            }
        } catch (e) {}
    },

    setupNetworkStatus() {
        const updateStatus = () => {
            const isOnline = navigator.onLine;
            const banner = document.getElementById('offline-status-banner');
            const textEl = document.getElementById('offline-status-text');

            if (!isOnline) {
                if (banner) {
                    banner.className = "fixed top-0 left-0 right-0 z-50 bg-amber-500 text-white text-center py-1.5 px-4 text-xs font-bold shadow-md flex items-center justify-center gap-2 transition-all";
                    if (textEl) textEl.textContent = "📴 Modo Offline Ativo - Seus dados continuam disponíveis no aparelho!";
                }
            } else {
                if (banner && !banner.classList.contains('hidden')) {
                    banner.className = "fixed top-0 left-0 right-0 z-50 bg-emerald-600 text-white text-center py-1.5 px-4 text-xs font-bold shadow-md flex items-center justify-center gap-2 transition-all";
                    if (textEl) textEl.textContent = "🟢 Conexão restabelecida! Sincronizando dados...";
                    this.syncOfflineQueue();
                    setTimeout(() => {
                        banner.classList.add('hidden');
                    }, 2500);
                }
            }
        };

        window.addEventListener('online', updateStatus);
        window.addEventListener('offline', updateStatus);
        if (!navigator.onLine) {
            updateStatus();
        }
    },

    async syncOfflineQueue() {
        try {
            const rawQueue = localStorage.getItem('vivaleve_offline_queue');
            if (!rawQueue) return;
            const queue = JSON.parse(rawQueue);
            if (!Array.isArray(queue) || queue.length === 0) return;

            console.log(`Sincronizando ${queue.length} ações offline pendentes...`);
            const remaining = [];

            for (const item of queue) {
                try {
                    if (item.type === 'add_food') {
                        const res = await fetch('/api/diary', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(item.payload)
                        });
                        if (!res.ok) remaining.push(item);
                    } else if (item.type === 'add_water') {
                        const res = await fetch('/api/water', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(item.payload)
                        });
                        if (!res.ok) remaining.push(item);
                    }
                } catch (e) {
                    remaining.push(item);
                }
            }

            if (remaining.length > 0) {
                localStorage.setItem('vivaleve_offline_queue', JSON.stringify(remaining));
            } else {
                localStorage.removeItem('vivaleve_offline_queue');
                this.showToast("✨ Todos os registros salvos offline foram sincronizados!", "success");
                if (typeof Diary !== 'undefined') Diary.load(this.currentDate);
            }
        } catch (e) {
            console.warn("Falha na sincronização offline:", e);
        }
    },

    async loadInitialData() {
        this.cacheFoodsCatalog();

        try {
            await Promise.allSettled([
                this.loadProfile(),
                (typeof Diary !== 'undefined' && Diary.load) ? Diary.load(this.currentDate) : null,
                (typeof CheatDay !== 'undefined' && CheatDay.load) ? CheatDay.load() : null,
                (typeof Streak !== 'undefined' && Streak.load) ? Streak.load() : null,
                (typeof FamilyBattle !== 'undefined' && FamilyBattle.load) ? FamilyBattle.load() : null,
                (typeof MealAssistant !== 'undefined' && MealAssistant.loadMenu) ? MealAssistant.loadMenu() : null,
                (typeof Workout !== 'undefined' && Workout.loadWorkouts) ? Workout.loadWorkouts() : null,
                (typeof Avatar !== 'undefined' && Avatar.load) ? Avatar.load() : null,
                this.loadServerInfo()
            ]);
        } catch (error) {
            console.warn("Inicialização parcial offline:", error);
        }

        if (navigator.onLine) {
            this.syncOfflineQueue();
        }
    },

    async cacheFoodsCatalog() {
        try {
            const res = await fetch('/api/foods');
            if (res.ok) {
                const foods = await res.json();
                if (Array.isArray(foods) && foods.length > 0) {
                    localStorage.setItem('vivaleve_foods_cache', JSON.stringify(foods));
                }
            }
        } catch (e) {
            // Em offline, usará os alimentos gravados
        }
    },

    async loadProfile() {
        try {
            const userId = Auth.getUserId();
            const res = await fetch(`/api/profile?user_id=${userId}`);
            if (res.ok) {
                const data = await res.json();
                if (!data.offline) {
                    this.userProfile = data;
                    localStorage.setItem('vivaleve_profile', JSON.stringify(data));
                }
            }
        } catch (err) {
            console.warn("Offline: buscando perfil no cache local...");
        }

        if (!this.userProfile) {
            try {
                const cached = localStorage.getItem('vivaleve_profile');
                if (cached) this.userProfile = JSON.parse(cached);
            } catch (e) {}
        }
        this.updateHeaderProfile();
    },

    updateHeaderProfile() {
        if (!this.userProfile) return;
        const nameEl = document.getElementById('header-user-name');
        if (nameEl) nameEl.textContent = this.userProfile.name || 'Usuário';

        const goalLabels = {
            'emagrecer': '🔥 Emagrecimento',
            'hipertrofia': '💪 Ganho Muscular',
            'manter': '⚖️ Manutenção'
        };
        const goalEl = document.getElementById('header-user-goal');
        if (goalEl) goalEl.textContent = goalLabels[this.userProfile.goal] || 'Saúde';
    },

    setupNavigation() {
        const navButtons = document.querySelectorAll('[data-tab-target]');
        navButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetTab = btn.getAttribute('data-tab-target');
                this.switchTab(targetTab);
            });
        });
    },

    switchTab(tabId) {
        this.currentTab = tabId;

        document.querySelectorAll('.tab-content').forEach(section => {
            section.classList.add('hidden');
        });

        const targetSection = document.getElementById(`tab-${tabId}`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            targetSection.classList.add('fade-in');
        }

        document.querySelectorAll('[data-tab-target]').forEach(btn => {
            const isCurrent = btn.getAttribute('data-tab-target') === tabId;
            if (isCurrent) {
                btn.classList.add('text-emerald-600', 'font-black');
                btn.classList.remove('text-slate-400', 'font-medium');
                const indicator = btn.querySelector('.nav-indicator');
                if (indicator) indicator.classList.remove('opacity-0');
            } else {
                btn.classList.remove('text-emerald-600', 'font-black');
                btn.classList.add('text-slate-400', 'font-medium');
                const indicator = btn.querySelector('.nav-indicator');
                if (indicator) indicator.classList.add('opacity-0');
            }
        });

        if (tabId === 'diario') {
            Diary.load(this.currentDate);
        } else if (tabId === 'cardapio') {
            if (typeof MealAssistant !== 'undefined') MealAssistant.loadMenu();
        } else if (tabId === 'dia-lixo') {
            CheatDay.load();
        } else if (tabId === 'familia') {
            if (typeof FamilyBattle !== 'undefined') FamilyBattle.load();
        } else if (tabId === 'restaurantes') {
            Restaurants.load();
        } else if (tabId === 'treinos') {
            if (typeof Workout !== 'undefined') Workout.loadWorkouts();
        } else if (tabId === 'avatar') {
            if (typeof Avatar !== 'undefined') Avatar.load();
        } else if (tabId === 'progresso') {
            ProfileCharts.load();
        }

        if (typeof Streak !== 'undefined') Streak.load();

        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    setupDateControls() {
        const prevBtn = document.getElementById('btn-prev-day');
        const nextBtn = document.getElementById('btn-next-day');
        const todayBtn = document.getElementById('btn-today');
        const dateInput = document.getElementById('current-date-input');

        if (dateInput) {
            dateInput.value = this.currentDate;
            dateInput.addEventListener('change', (e) => {
                this.currentDate = e.target.value;
                this.updateDateDisplay();
                Diary.load(this.currentDate);
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.offsetDay(-1));
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.offsetDay(1));
        }

        if (todayBtn) {
            todayBtn.addEventListener('click', () => {
                this.currentDate = new Date().toISOString().split('T')[0];
                this.updateDateDisplay();
                Diary.load(this.currentDate);
            });
        }

        this.updateDateDisplay();
    },

    offsetDay(delta) {
        const d = new Date(this.currentDate + 'T12:00:00');
        d.setDate(d.getDate() + delta);
        this.currentDate = d.toISOString().split('T')[0];
        this.updateDateDisplay();
        Diary.load(this.currentDate);
    },

    updateDateDisplay() {
        const dateInput = document.getElementById('current-date-input');
        if (dateInput) dateInput.value = this.currentDate;

        const dateLabel = document.getElementById('current-date-label');
        if (!dateLabel) return;

        const todayStr = new Date().toISOString().split('T')[0];
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];

        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        if (this.currentDate === todayStr) {
            dateLabel.textContent = 'Hoje';
        } else if (this.currentDate === yesterdayStr) {
            dateLabel.textContent = 'Ontem';
        } else if (this.currentDate === tomorrowStr) {
            dateLabel.textContent = 'Amanhã';
        } else {
            const parts = this.currentDate.split('-');
            dateLabel.textContent = `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
    },

    // ----------------- SERVIÇO DE LIVE-UPDATE & AUTO-SYNC NO CELULAR -----------------
    async loadServerInfo() {
        try {
            const res = await fetch('/api/server-info');
            if (res.ok) {
                this.serverInfo = await res.json();
                this.appVersion = this.serverInfo.timestamp;
            }
        } catch (e) {
            console.warn("Falha ao obter dados do servidor:", e);
        }
    },

    setupLiveUpdateChecker() {
        // Checa alterações no servidor a cada 60 segundos com baixíssimo consumo no 4G/5G
        setInterval(async () => {
            if (document.hidden) return; // Economiza bateria e dados quando celular está com tela apagada

            try {
                const res = await fetch('/api/version');
                if (res.ok) {
                    const data = await res.json();
                    if (!this.appVersion && data.timestamp) {
                        this.appVersion = data.timestamp;
                        return;
                    }
                    if (this.appVersion && data.timestamp && data.timestamp !== this.appVersion) {
                        const isTyping = document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
                        if (isTyping) return; // Não atrapalha o usuário se ele estiver digitando

                        this.appVersion = data.timestamp;
                        this.showToast("🚀 Nova versão do VivaLeve sincronizada!", "info");
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    }
                }
            } catch (err) {
                // Silencioso em caso de oscilação transitória do sinal do celular
            }
        }, 60000);
    },

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            // Tenta registrar na raiz /sw.js com escopo completo /, com fallback para /static/sw.js
            navigator.serviceWorker.register('/sw.js', { scope: '/' })
                .catch(() => navigator.serviceWorker.register('/static/sw.js'))
                .then((reg) => {
                    console.log("Service Worker ativo!");
                    if (reg) {
                        reg.onupdatefound = () => {
                            const installingWorker = reg.installing;
                            if (installingWorker) {
                                installingWorker.onstatechange = () => {
                                    if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                        App.showToast("✨ Nova versão do VivaLeve pronta!", "info");
                                    }
                                };
                            }
                        };
                    }
                })
                .catch(err => console.warn("SW não registrado:", err));
        }
    },

    // ----------------- MODAL DE INSTALAÇÃO NO CELULAR / APK -----------------
    openMobileModal() {
        const modal = document.getElementById('modal-mobile-app');
        if (!modal) return;
        modal.classList.remove('hidden');

        const qrContainer = document.getElementById('qrcode-container');
        const urlDisplay = document.getElementById('mobile-url-display');

        // Se estiver acessando via HTTPS (Cloudflare), usa a origem atual, senão usa a URL pública do servidor se existir
        const currentOrigin = window.location.origin;
        let mobileUrl = currentOrigin;
        if (currentOrigin.includes('localhost') || currentOrigin.includes('127.0.0.1')) {
            if (this.serverInfo && this.serverInfo.public_url) {
                mobileUrl = this.serverInfo.public_url;
            } else if (this.serverInfo && this.serverInfo.mobile_url) {
                mobileUrl = this.serverInfo.mobile_url;
            }
        }

        if (urlDisplay) urlDisplay.textContent = mobileUrl;

        if (qrContainer && typeof QRCode !== 'undefined') {
            qrContainer.innerHTML = '';
            this.qrCodeInstance = new QRCode(qrContainer, {
                text: mobileUrl,
                width: 180,
                height: 180,
                colorDark: "#065f46",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.M
            });
        }
    },

    copyMobileUrl() {
        const urlDisplay = document.getElementById('mobile-url-display');
        const url = urlDisplay ? urlDisplay.textContent.trim() : '';
        if (url && url !== 'Carregando...') {
            navigator.clipboard.writeText(url).then(() => {
                this.showToast("Link copiado com sucesso! Abra no celular.");
            }).catch(() => {
                this.showToast("Link: " + url);
            });
        }
    },

    closeMobileModal() {
        const modal = document.getElementById('modal-mobile-app');
        if (modal) modal.classList.add('hidden');
    },

    switchMobileModalTab(tab) {
        ['android', 'ios', 'wifi'].forEach(t => {
            const el = document.getElementById(`mobile-tab-content-${t}`);
            const btn = document.getElementById(`mobile-tab-btn-${t}`);
            if (el) {
                if (t === tab) el.classList.remove('hidden');
                else el.classList.add('hidden');
            }
            if (btn) {
                if (t === tab) {
                    btn.classList.add('bg-white', 'text-slate-800', 'shadow-sm');
                    btn.classList.remove('text-slate-500', 'hover:text-slate-700');
                } else {
                    btn.classList.remove('bg-white', 'text-slate-800', 'shadow-sm');
                    btn.classList.add('text-slate-500', 'hover:text-slate-700');
                }
            }
        });
    },

    playSound(type = 'success') {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();

            if (type === 'success' || type === 'victory') {
                // Arpeggio alegre (C5, E5, G5, C6)
                const notes = [523.25, 659.25, 783.99, 1046.50];
                notes.forEach((freq, idx) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08);
                    gain.gain.setValueAtTime(0.12, ctx.currentTime + idx * 0.08);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.08 + 0.22);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + idx * 0.08);
                    osc.stop(ctx.currentTime + idx * 0.08 + 0.25);
                });
            } else if (type === 'water') {
                // Efeito sonoro de gota d'água refrescante
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(600, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(1300, ctx.currentTime + 0.1);
                gain.gain.setValueAtTime(0.18, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.14);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.16);
            } else if (type === 'click') {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(800, ctx.currentTime);
                gain.gain.setValueAtTime(0.06, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.06);
            } else if (type === 'streak' || type === 'flame') {
                // Sequência estilo Duolingo
                const notes = [440, 554.37, 659.25, 880];
                notes.forEach((freq, idx) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.06);
                    gain.gain.setValueAtTime(0.1, ctx.currentTime + idx * 0.06);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + idx * 0.06 + 0.15);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + idx * 0.06);
                    osc.stop(ctx.currentTime + idx * 0.06 + 0.18);
                });
            }
        } catch (e) {
            // Suprime silenciosamente em browsers com restrição de autoplay
        }
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        const bgColors = {
            success: 'bg-emerald-500 text-white shadow-emerald-500/30',
            error: 'bg-rose-500 text-white shadow-rose-500/30',
            warning: 'bg-amber-500 text-white shadow-amber-500/30',
            info: 'bg-cyan-600 text-white shadow-cyan-600/30'
        };
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.className = `flex items-center gap-2 px-4 py-3 rounded-2xl shadow-lg text-xs font-bold fade-in ${bgColors[type] || bgColors.success}`;
        toast.innerHTML = `<span class="text-sm">${icons[type] || '•'}</span> <span>${message}</span>`;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    triggerConfetti() {
        const canvas = document.getElementById('confetti-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const pieces = [];
        const colors = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#facc15'];

        for (let i = 0; i < 70; i++) {
            pieces.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height * 0.3,
                r: Math.random() * 6 + 4,
                d: Math.random() * 10 + 10,
                color: colors[Math.floor(Math.random() * colors.length)],
                tilt: Math.floor(Math.random() * 10) - 10,
                tiltAngleIncremental: (Math.random() * 0.07) + 0.05,
                tiltAngle: 0
            });
        }

        let count = 0;
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < pieces.length; i++) {
                const p = pieces[i];
                ctx.beginPath();
                ctx.lineWidth = p.r;
                ctx.strokeStyle = p.color;
                ctx.moveTo(p.x + p.tilt + (p.r / 2), p.y);
                ctx.lineTo(p.x + p.tilt, p.y + p.tilt + (p.r / 2));
                ctx.stroke();

                p.tiltAngle += p.tiltAngleIncremental;
                p.y += (Math.cos(p.d) + 3 + p.r / 2) / 2;
                p.tilt = Math.sin(p.tiltAngle - (i / 3)) * 15;
            }

            count++;
            if (count < 110) {
                requestAnimationFrame(draw);
            } else {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
        draw();
    },

    clickMascot() {
        const phrases = [
            "Você está arrasando hoje! Cada refeição saudável te deixa mais perto da meta! 🌱",
            "Não esquece de beber água para manter o foguinho aceso! 💧🔥",
            "Sabia que quem lidera a Batalha Familiar escolhe o que comer no Dia do Lixo? 👑🍕",
            "Fotografa seu prato no Scanner de Foto! A IA analisa tudo em segundos! 📸⚡",
            "Viva leve, viva bem! Uma dieta feliz é aquela que cabe na sua rotina! ✨"
        ];
        const bubble = document.getElementById('vivi-mascot-speech');
        if (bubble) {
            const random = phrases[Math.floor(Math.random() * phrases.length)];
            bubble.textContent = random;
            bubble.classList.remove('hidden');
            this.triggerConfetti();
            setTimeout(() => {
                bubble.classList.add('hidden');
            }, 6000);
        }
    }
};

window.addEventListener('DOMContentLoaded', () => {
    App.init();
});
