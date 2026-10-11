/**
 * VivaLeve - Gerenciamento de Autenticação (Login & Cadastro)
 */

const Auth = {
    currentUser: null,
    token: null,

    // Inicialização síncrona imediata para evitar race conditions
    _boot() {
        try {
            // Isolamento rigoroso por aparelho: se o dispositivo não tiver token autenticado, limpa contas legadas espúrias
            if (!localStorage.getItem('vivaleve_auth_clean_v3')) {
                if (!localStorage.getItem('vivaleve_token')) {
                    localStorage.removeItem('vivaleve_saved_accounts');
                }
                localStorage.setItem('vivaleve_auth_clean_v3', 'true');
            }

            const storedUser = localStorage.getItem('vivaleve_user');
            const storedToken = localStorage.getItem('vivaleve_token');
            if (storedUser && storedToken) {
                this.currentUser = JSON.parse(storedUser);
                this.token = storedToken;
            }
        } catch (e) {
            console.warn("Falha ao restaurar usuário do localStorage:", e);
        }
    },

    init() {
        this._boot();

        if (this.currentUser && this.token) {
            this.updateUI();
            this.renderSavedAccounts();
        } else {
            this.currentUser = null;
            this.token = null;
            const userNameEl = document.getElementById('header-user-name');
            if (userNameEl) userNameEl.textContent = "Convidado";
            const avatarEl = document.getElementById('header-user-avatar');
            if (avatarEl) avatarEl.textContent = "🌱";

            this.renderSavedAccounts();

            // Disparar portal de boas-vindas / login somente se não estiver logado
            setTimeout(() => {
                if (!this.isLoggedIn() && typeof Onboarding !== 'undefined') {
                    const saved = this.getSavedAccounts();
                    if (saved.length > 0) {
                        Onboarding.openLogin();
                    } else {
                        Onboarding.openWelcome();
                    }
                }
            }, 300);
        }
    },

    getUserId() {
        if (this.currentUser && this.currentUser.id) {
            return this.currentUser.id;
        }
        try {
            const stored = localStorage.getItem('vivaleve_user');
            if (stored) {
                const u = JSON.parse(stored);
                if (u && u.id) {
                    this.currentUser = u;
                    return u.id;
                }
            }
        } catch (e) {}
        return 1;
    },

    getUser() {
        return this.currentUser;
    },

    isLoggedIn() {
        return !!this.token;
    },

    updateUI() {
        const userNameEl = document.getElementById('header-user-name');
        const avatarEl = document.getElementById('header-user-avatar');
        const authStatusBtn = document.getElementById('btn-header-auth');

        if (this.currentUser) {
            if (userNameEl) userNameEl.textContent = this.currentUser.name;
            if (avatarEl) {
                // Iniciais coloridas
                const initials = this.currentUser.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
                avatarEl.textContent = initials || '👤';
            }
            if (authStatusBtn) {
                authStatusBtn.innerHTML = `<span>⚙️</span> <span class="hidden sm:inline">Conta</span>`;
                authStatusBtn.title = `Conectado como ${this.currentUser.name} (Clique para opções)`;
            }
        }
    },

    // ----------------- CONTAS SALVAS NESTE APARELHO -----------------

    getSavedAccounts() {
        try {
            return JSON.parse(localStorage.getItem('vivaleve_saved_accounts') || '[]');
        } catch (e) {
            return [];
        }
    },

    saveAccount(user) {
        if (!user || !user.email) return;
        let accounts = this.getSavedAccounts();
        accounts = accounts.filter(a => a.email.toLowerCase() !== user.email.toLowerCase());
        accounts.unshift({
            id: user.id,
            name: user.name,
            email: user.email,
            savedAt: Date.now()
        });
        localStorage.setItem('vivaleve_saved_accounts', JSON.stringify(accounts.slice(0, 5)));
        this.renderSavedAccounts();
    },

    removeSavedAccount(email) {
        let accounts = this.getSavedAccounts();
        accounts = accounts.filter(a => a.email.toLowerCase() !== email.toLowerCase());
        localStorage.setItem('vivaleve_saved_accounts', JSON.stringify(accounts));
        this.renderSavedAccounts();
    },

    selectSavedAccount(email) {
        const inputs = [
            document.getElementById('login-email'),
            document.getElementById('onboarding-login-email')
        ];
        inputs.forEach(inp => {
            if (inp) inp.value = email;
        });

        const pwdInputs = [
            document.getElementById('login-password'),
            document.getElementById('onboarding-login-password')
        ];
        const visiblePwd = pwdInputs.find(p => p && p.offsetParent !== null);
        if (visiblePwd) {
            visiblePwd.value = '';
            visiblePwd.focus();
            visiblePwd.placeholder = "Digite sua senha para entrar";
        }
        if (typeof App !== 'undefined' && App.showToast) {
            App.showToast(`Conta selecionada! Digite sua senha para entrar.`, "info");
        }
    },

    renderSavedAccounts() {
        const saved = this.getSavedAccounts();
        const containers = [
            document.getElementById('auth-saved-accounts-container'),
            document.getElementById('onboarding-saved-accounts-container')
        ];

        containers.forEach(container => {
            if (!container) return;
            if (saved.length === 0) {
                container.innerHTML = '';
                container.classList.add('hidden');
                return;
            }

            container.classList.remove('hidden');
            container.innerHTML = `
                <div class="mb-3 p-3 bg-emerald-50/70 rounded-2xl border border-emerald-100 text-left">
                    <span class="text-[10px] font-black text-emerald-800 uppercase tracking-wider block mb-1.5">
                        👤 Contas Salvas neste Aparelho:
                    </span>
                    <div class="space-y-1.5">
                        ${saved.map(acc => `
                            <div class="flex items-center justify-between p-2 bg-white rounded-xl border border-emerald-200/60 shadow-xs hover:border-emerald-400 transition cursor-pointer" onclick="Auth.selectSavedAccount('${acc.email}')">
                                <div class="flex items-center gap-2 overflow-hidden">
                                    <div class="w-7 h-7 rounded-lg bg-emerald-600 text-white text-[11px] font-black flex items-center justify-center shrink-0">
                                        ${acc.name ? acc.name[0].toUpperCase() : '👤'}
                                    </div>
                                    <div class="truncate">
                                        <div class="text-xs font-bold text-slate-800 truncate">${acc.name}</div>
                                        <div class="text-[10px] text-slate-500 font-mono truncate">${acc.email}</div>
                                    </div>
                                </div>
                                <div class="flex items-center gap-1.5 shrink-0 ml-2">
                                    <button type="button" onclick="event.stopPropagation(); Auth.selectSavedAccount('${acc.email}')" class="px-2.5 py-1 text-[10px] font-black text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-xs transition">
                                        Usar 🔑
                                    </button>
                                    <button type="button" onclick="event.stopPropagation(); Auth.removeSavedAccount('${acc.email}')" class="p-1 text-slate-300 hover:text-rose-500 rounded-lg text-xs" title="Remover desta lista">
                                        ✕
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });
    },

    openResetModal(prefillEmail = '') {
        const modal = document.getElementById('modal-reset-password');
        if (modal) {
            modal.classList.remove('hidden');
            const emailInp = document.getElementById('reset-email');
            if (emailInp && prefillEmail) emailInp.value = prefillEmail;
        }
    },

    closeResetModal() {
        const modal = document.getElementById('modal-reset-password');
        if (modal) modal.classList.add('hidden');
    },

    togglePassword(inputId, btnEl) {
        const input = document.getElementById(inputId);
        if (!input) return;
        if (input.type === 'password') {
            input.type = 'text';
            if (btnEl) btnEl.textContent = '🙈';
        } else {
            input.type = 'password';
            if (btnEl) btnEl.textContent = '👁️';
        }
    },

    openModal(defaultTab = 'login') {
        const modal = document.getElementById('modal-auth');
        if (modal) {
            modal.classList.remove('hidden');
            this.switchTab(defaultTab);
            this.renderSavedAccounts();
        }
    },

    closeModal() {
        const modal = document.getElementById('modal-auth');
        if (modal) modal.classList.add('hidden');
    },

    switchTab(tab) {
        const tabLogin = document.getElementById('auth-tab-btn-login');
        const tabRegister = document.getElementById('auth-tab-btn-register');
        const formLogin = document.getElementById('auth-form-login');
        const formRegister = document.getElementById('auth-form-register');

        if (tab === 'login') {
            if (tabLogin) tabLogin.className = "flex-1 py-2.5 text-xs font-bold rounded-2xl bg-white text-emerald-700 shadow-md shadow-emerald-500/15 transition-all";
            if (tabRegister) tabRegister.className = "flex-1 py-2.5 text-xs font-semibold rounded-2xl text-slate-500 hover:text-slate-700 transition-all";
            if (formLogin) formLogin.classList.remove('hidden');
            if (formRegister) formRegister.classList.add('hidden');
        } else {
            if (tabLogin) tabLogin.className = "flex-1 py-2.5 text-xs font-semibold rounded-2xl text-slate-500 hover:text-slate-700 transition-all";
            if (tabRegister) tabRegister.className = "flex-1 py-2.5 text-xs font-bold rounded-2xl bg-white text-emerald-700 shadow-md shadow-emerald-500/15 transition-all";
            if (formLogin) formLogin.classList.add('hidden');
            if (formRegister) formRegister.classList.remove('hidden');
        }
    },

    async doLogin(event) {
        if (event) event.preventDefault();

        // Extrai dados da form que disparou o evento com segurança
        const form = event?.target && event.target.tagName === 'FORM' ? event.target : document.getElementById('auth-form-login');
        
        let email = '';
        let password = '';
        let remember = true;

        if (form) {
            email = (form.querySelector('input[type="email"]') || form.querySelector('input[name="email"]') || form.querySelector('#login-email'))?.value?.trim();
            password = (form.querySelector('input[type="password"]') || form.querySelector('input[name="password"]') || form.querySelector('#login-password'))?.value;
            const remBox = form.querySelector('input[type="checkbox"][name="remember"]');
            if (remBox) remember = remBox.checked;
        }

        // Fallbacks caso não venha direto do form
        if (!email) email = document.getElementById('login-email')?.value?.trim() || document.getElementById('onboarding-login-email')?.value?.trim();
        if (!password) password = document.getElementById('login-password')?.value || document.getElementById('onboarding-login-password')?.value;

        if (!email || !password) {
            App.showToast("Informe seu e-mail e senha.", "warning");
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                this.currentUser = data.user;
                this.token = data.token;
                localStorage.setItem('vivaleve_user', JSON.stringify(data.user));
                localStorage.setItem('vivaleve_token', data.token);

                // Cookie de persistência longa para mobile/PWA
                document.cookie = `vivaleve_uid=${data.user.id}; path=/; max-age=31536000; SameSite=Lax`;

                if (remember) {
                    this.saveAccount(data.user);
                }

                this.updateUI();
                this.closeModal();
                if (typeof Onboarding !== 'undefined') Onboarding.close();
                if (typeof App !== 'undefined' && App.playSound) App.playSound('victory');
                App.showToast(`Bem-vindo de volta, ${data.user.name}! 🌟`);

                // Recarregar dados para o usuário autenticado
                App.loadProfile();
                Diary.load(App.currentDate);
                CheatDay.load();
                ProfileCharts.load();
                if (typeof Streak !== 'undefined') Streak.load();
                if (typeof FamilyBattle !== 'undefined') FamilyBattle.load();
                if (typeof MealAssistant !== 'undefined') MealAssistant.loadMenu();
            } else {
                App.showToast(data.detail || data.message || "E-mail ou senha incorretos.", "error");
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro ao conectar com o servidor.", "error");
        }
    },

    async doRegister(event) {
        if (event) event.preventDefault();

        const form = event?.target && event.target.tagName === 'FORM' ? event.target : document.getElementById('auth-form-register');
        let name = '';
        let email = '';
        let password = '';

        if (form) {
            name = (form.querySelector('input[name="name"]') || form.querySelector('#reg-name'))?.value?.trim();
            email = (form.querySelector('input[type="email"]') || form.querySelector('input[name="email"]') || form.querySelector('#reg-email'))?.value?.trim();
            password = (form.querySelector('input[type="password"]') || form.querySelector('input[name="password"]') || form.querySelector('#reg-password'))?.value;
        }

        if (!name || !email || !password) {
            App.showToast("Preencha todos os campos para se cadastrar.", "warning");
            return;
        }

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                this.currentUser = data.user;
                this.token = data.token;
                localStorage.setItem('vivaleve_user', JSON.stringify(data.user));
                localStorage.setItem('vivaleve_token', data.token);
                document.cookie = `vivaleve_uid=${data.user.id}; path=/; max-age=31536000; SameSite=Lax`;

                this.saveAccount(data.user);

                this.updateUI();
                this.closeModal();
                if (typeof Onboarding !== 'undefined') Onboarding.close();
                App.showToast(`Conta criada com sucesso! Olá, ${data.user.name}! 🎉`);

                App.loadProfile();
                Diary.load(App.currentDate);
                CheatDay.load();
                ProfileCharts.load();
                if (typeof Streak !== 'undefined') Streak.load();
            } else {
                App.showToast(data.detail || data.message || "Erro ao cadastrar.", "error");
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro ao conectar com o servidor.", "error");
        }
    },

    async doResetPassword(event) {
        if (event) event.preventDefault();

        const form = event?.target && event.target.tagName === 'FORM' ? event.target : document.getElementById('auth-form-reset');
        const email = form?.querySelector('input[type="email"]')?.value?.trim() || document.getElementById('reset-email')?.value?.trim();
        const newPassword = form?.querySelector('input[type="password"]')?.value || document.getElementById('reset-new-password')?.value;

        if (!email || !newPassword) {
            App.showToast("Informe seu e-mail e a nova senha desejada.", "warning");
            return;
        }

        try {
            const res = await fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, new_password: newPassword })
            });

            const data = await res.json();
            if (res.ok && data.success) {
                this.currentUser = data.user;
                this.token = data.token;
                localStorage.setItem('vivaleve_user', JSON.stringify(data.user));
                localStorage.setItem('vivaleve_token', data.token);
                document.cookie = `vivaleve_uid=${data.user.id}; path=/; max-age=31536000; SameSite=Lax`;

                this.saveAccount(data.user);

                this.updateUI();
                this.closeResetModal();
                this.closeModal();
                if (typeof Onboarding !== 'undefined') Onboarding.close();
                if (typeof App !== 'undefined' && App.playSound) App.playSound('victory');
                App.showToast(`🎉 Senha alterada! Bem-vindo de volta, ${data.user.name}!`);

                App.loadProfile();
                Diary.load(App.currentDate);
                CheatDay.load();
                ProfileCharts.load();
                if (typeof Streak !== 'undefined') Streak.load();
            } else {
                App.showToast(data.detail || data.message || "Erro ao redefinir senha.", "error");
            }
        } catch (err) {
            console.error(err);
            App.showToast("Erro ao conectar com o servidor.", "error");
        }
    },

    async doQuickLogin(userId) {
        const saved = this.getSavedAccounts().find(a => a.id === userId);
        if (saved && saved.email) {
            this.selectSavedAccount(saved.email);
        } else {
            if (typeof App !== 'undefined' && App.showToast) {
                App.showToast("Informe seu e-mail e senha para entrar.", "info");
            }
        }
    },

    logout() {
        if (!confirm("Deseja sair da sua conta?")) return;
        this.currentUser = null;
        this.token = null;
        localStorage.removeItem('vivaleve_user');
        localStorage.removeItem('vivaleve_token');
        document.cookie = "vivaleve_uid=; path=/; max-age=0";

        const userNameEl = document.getElementById('header-user-name');
        if (userNameEl) userNameEl.textContent = "Convidado";
        const avatarEl = document.getElementById('header-user-avatar');
        if (avatarEl) avatarEl.textContent = "🌱";

        this.closeModal();
        App.showToast("Você saiu da sua conta.", "info");

        if (typeof Onboarding !== 'undefined') {
            Onboarding.openLogin();
        }
    }
};

// Executar boot síncrono imediatamente
Auth._boot();

window.Auth = Auth;

window.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});
