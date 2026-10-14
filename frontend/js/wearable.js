/**
 * VivaLeve - Módulo do Relógio Digital / Smartwatch (Web Bluetooth)
 *
 * Conecta emoki pulseiras e monitores pelo perfil padrão "Heart Rate" (0x180D)
 * e monta a sessão do dia: calorias gastas, passos, distância, FC de repouso/
 * média/máxima, minutos ativos, sono e SpO2. Tudo isso volta pro saldo calórico
 * da dieta (ver backend/wearable_service.py).
 *
 * Se o aparelho não falar BLE (ou o usuário preferir), há entrada manual com
 * os mesmos campos e uma sessão automática a partir dos treinos já registrados.
 */

const Wearable = {
    state: {
        supported: false,
        connected: false,
        deviceName: '',
        device: null,
        characteristic: null,
        deviceId: null,
        live: { bpm: 0, samples: 0, min: 0, max: 0, sum: 0 },
        summary: null,
        health: null,
        devices: [],
        busy: false,
    },

    GATT: {
        HEART_RATE_SERVICE: 0x180d,
        HEART_RATE_MEASUREMENT: 0x2a37,
        BATTERY_SERVICE: 0x180f,
        BATTERY_LEVEL: 0x2a19,
    },

    // Perfil "Physical Activity" (0x1846) — passos e gasto calórico acumulado
    // Perfil "Cycling Speed and Cadence" (0x1816) — usada por pulseiras de passada
    GATT_EXTRA: {
        ACTIVITY_SERVICE: 0x1846,
        ACTIVITY_FEATURE: 0x2acc,
        ACTIVITY_DATA: 0x2acd,
        CSC_SERVICE: 0x1816,
        CSC_MEASUREMENT: 0x2a5b,
        CSC_FEATURE: 0x2a5c,
    },

    init() {
        this.state.supported = typeof navigator !== 'undefined' && !!navigator.bluetooth;
        this.renderSupport();
        this.load();
    },

    // ---------------------------------------------------------------
    //  BLUETOOTH
    // ---------------------------------------------------------------
    async connect() {
        if (!this.state.supported) {
            this.toast('Este navegador não suporta Bluetooth. Use o registro manual.', 'error');
            return;
        }
        if (this.state.busy) return;
        this.state.busy = true;
        this.setStatus('Procurando pulseiras e relógios...');

        try {
            let device;
            try {
                device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { services: [this.GATT.HEART_RATE_SERVICE] },
                        { services: [this.GATT_EXTRA.ACTIVITY_SERVICE] },
                    ],
                    optionalServices: [
                        this.GATT.HEART_RATE_SERVICE,
                        this.GATT.HEART_RATE_MEASUREMENT,
                        this.GATT.BATTERY_SERVICE,
                        this.GATT.BATTERY_LEVEL,
                        this.GATT_EXTRA.ACTIVITY_SERVICE,
                        this.GATT_EXTRA.ACTIVITY_FEATURE,
                        this.GATT_EXTRA.ACTIVITY_DATA,
                        this.GATT_EXTRA.CSC_SERVICE,
                        this.GATT_EXTRA.CSC_MEASUREMENT,
                        this.GATT_EXTRA.CSC_FEATURE,
                    ],
                });
            } catch (firstErr) {
                device = await navigator.bluetooth.requestDevice({ acceptAllDevices: true, optionalServices: ['generic_access', 'generic_attribute'] });
            }

            this.state.device = device;
            this.state.deviceName = device.name || 'Relógio';
            this.setStatus(`Conectando em ${this.state.deviceName}...`);

            const server = await device.gatt.connect();
            device.addEventListener('gattserverdisconnected', () => this.onDisconnected());

            let hrOk = await this.subscribeHeartRate(server);
            if (!hrOk) {
                // Alguns relógios expõem passos/calorias sem sensor de FC padrão
                await this.subscribeActivity(server);
            }

            this.state.connected = true;
            this.resetLive();
            await this.registerDevice();
            this.render();
            this.setStatus('Conectado! Batimento ao vivo ativado.');
            this.toast(`⌚ ${this.state.deviceName} conectado!`, 'success');
        } catch (e) {
            if (e && e.name === 'NotFoundError') {
                this.setStatus('Nenhum relógio escolhido.');
            } else {
                console.error('Falha no Bluetooth do relógio:', e);
                this.setStatus('Não foi possível conectar. Use o registro manual.');
                this.toast('Falha ao conectar o relógio.', 'error');
            }
        } finally {
            this.state.busy = false;
            this.render();
        }
    },

    async subscribeHeartRate(server) {
        const svc = await server.getPrimaryService(this.GATT.HEART_RATE_SERVICE).catch(() => null);
        if (!svc) return false;
        const ch = await svc.getCharacteristic(this.GATT.HEART_RATE_MEASUREMENT).catch(() => null);
        if (!ch) return false;

        this.state.characteristic = ch;
        ch.addEventListener('characteristicvaluechanged', (e) => this.onHeartRate(e.target.value));
        if (ch.startNotifications) await ch.startNotifications();
        return true;
    },

    /** Passos/calorias pelo perfil Physical Activity (0x1846). */
    async subscribeActivity(server) {
        const svc = await server.getPrimaryService(this.GATT_EXTRA.ACTIVITY_SERVICE).catch(() => null);
        if (!svc) return false;
        const ch = await svc.getCharacteristic(this.GATT_EXTRA.ACTIVITY_DATA).catch(() => null);
        if (!ch) return false;

        ch.addEventListener('characteristicvaluechanged', (e) => {
            const dv = toDataView(e.target.value);
            if (dv.byteLength < 10) return;
            // Instantaneous: total calories(uint32), distance(uint32),
            // steps(uint16), stride(uint16)...
            const calories = dv.getUint32(0, true);
            const distanceM = dv.getUint32(4, true);
            const steps = dv.getUint16(8, true);
            this.pendingSteps = steps;
            this.pendingDistanceKm = +(distanceM / 1000).toFixed(2);
            this.pendingCalories = calories;
        });
        if (ch.startNotifications) await ch.startNotifications();
        return true;
    },

    /** Heart Rate Measurement (0x2A37): 1 byte de flags + BPM (8 ou 16 bits). */
    onHeartRate(dataView) {
        const dv = toDataView(dataView);
        if (dv.byteLength < 2) return;
        const flags = dv.getUint8(0);
        // bit0 = formato do valor (0 = uint8, 1 = uint16)
        const bpm = (flags & 0x01) ? dv.getUint16(1, true) : dv.getUint8(1);
        if (!bpm || bpm < 25 || bpm > 240) return;

        this.onSample(bpm);

        // FC "de esforço" (< 100 bpm parado) indica repouso
        if (bpm < 95) {
            this.state.live.resting = this.state.live.resting
                ? Math.min(this.state.live.resting, bpm)
                : bpm;
        }
        this.renderLive();
    },

    onSample(bpm) {
        const L = this.state.live;
        L.bpm = bpm;
        L.samples++;
        L.sum += bpm;
        L.min = L.min ? Math.min(L.min, bpm) : bpm;
        L.max = Math.max(L.max, bpm);

        // heartbeats ao backend a cada ~15s (não spammar o servidor)
        clearTimeout(this._hbTimer);
        this._hbTimer = setTimeout(() => this.pushHeartbeat(bpm), 15000);
    },

    async pushHeartbeat(bpm) {
        try {
            await fetch('/api/wearables/heartbeat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bpm, device_id: this.state.deviceId }),
            });
        } catch (e) { /* offline: o resumo local ainda funciona */ }
    },

    onDisconnected() {
        this.state.connected = false;
        this.state.characteristic = null;
        this.setStatus('Relógio desconectado.');
        this.render();
        // Grava o que já foi medido antes de perder a conexão
        if (this.state.live.samples > 0) this.commitSession();
        this.toast('Relógio desconectado.', 'error');
    },

    disconnect() {
        if (this.state.live.samples > 0) this.commitSession();
        try { if (this.state.device && this.state.device.gatt.connected) this.state.device.gatt.disconnect(); } catch (e) { /* já caiu */ }
        this.state.connected = false;
        this.state.characteristic = null;
        this.setStatus('Desconectado.');
        this.render();
    },

    toggleConnection() {
        if (this.state.connected) this.disconnect();
        else this.connect();
    },

    // ---------------------------------------------------------------
    //  SESSÃO
    // ---------------------------------------------------------------
    async registerDevice() {
        try {
            const res = await fetch('/api/wearables/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: this.state.deviceName,
                    kind: 'watch',
                    device_id: this.state.device ? (this.state.device.id || this.state.deviceName) : '',
                }),
            });
            const data = await res.json();
            this.state.deviceId = data.device_id || null;
        } catch (e) { console.warn('Falha ao registrar relógio:', e); }
    },

    /** Envia a sessão acumulada (botão ou automático). */
    async commitSession() {
        const L = this.state.live;
        if (!L.samples) {
            this.toast('Nenhuma batida lida ainda. Conecte e aguarde alguns segundos.', 'error');
            return;
        }
        const payload = {
            device_id: this.state.deviceId,
            device_name: this.state.deviceName,
            avg_hr: Math.round(L.sum / L.samples),
            max_hr: L.max,
            resting_hr: L.resting || null,
            active_minutes: Math.max(1, Math.round(L.samples * 0.5)),
            calories_burned: Math.round((L.sum / L.samples) * L.samples * 0.11),
            steps: this.pendingSteps || 0,
            distance_km: this.pendingDistanceKm || 0,
            source: 'ble',
        };
        await this.send(payload);
        this.resetLive();
        this.renderLive();
    },

    /** Registro manual dos campos do relógio. */
    async submitManual() {
        const get = (id) => {
            const el = document.getElementById(id);
            if (!el) return null;
            const v = parseFloat(el.value);
            return isFinite(v) ? v : null;
        };
        const payload = {
            device_name: document.getElementById('wear-device-name')?.value || 'Relógio manual',
            calories_burned: get('wear-calories') || 0,
            steps: get('wear-steps') || 0,
            distance_km: get('wear-distance') || 0,
            active_minutes: get('wear-active-min') || 0,
            resting_hr: get('wear-hr-rest'),
            avg_hr: get('wear-hr-avg'),
            max_hr: get('wear-hr-max'),
            sleep_hours: get('wear-sleep') || 0,
            spo2: get('wear-spo2'),
            source: 'manual',
        };
        if (!payload.calories_burned && !payload.steps && !payload.sleep_hours) {
            this.toast('Informe calorias, passos ou sono.', 'error');
            return;
        }
        await this.send(payload);
        ['wear-calories', 'wear-steps', 'wear-distance', 'wear-active-min', 'wear-hr-rest', 'wear-hr-avg', 'wear-hr-max', 'wear-sleep', 'wear-spo2']
            .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    },

    /** Importa o que o relógio do celular já registrou no próprio app. */
    async importFromWorkouts() {
        try {
            const res = await fetch('/api/wearables/summary');
            const data = await res.json();
            const hist = (data.history || []).slice(-14);
            if (!hist.length) {
                this.toast('Ainda não há treinos registrados para importar.', 'error');
                return;
            }
            const totalCal = hist.reduce((s, d) => s + (d.calories_burned || 0), 0);
            const totalMin = hist.reduce((s, d) => s + (d.active_minutes || 0), 0);
            const totalSteps = hist.reduce((s, d) => s + (d.steps || 0), 0);
            const hrs = hist.map(d => d.avg_hr).filter(Boolean);
            await this.send({
                device_name: 'Relógio (importação de treinos)',
                calories_burned: Math.round(totalCal / hist.length),
                active_minutes: Math.round(totalMin / hist.length),
                steps: Math.round(totalSteps / hist.length),
                avg_hr: hrs.length ? Math.round(hrs.reduce((a, b) => a + b, 0) / hrs.length) : null,
                max_hr: Math.max(...hist.map(d => d.max_hr || 0)) || null,
                source: 'import',
            });
        } catch (e) {
            console.error(e);
            this.toast('Não consegui importar os treinos.', 'error');
        }
    },

    async send(payload) {
        try {
            const res = await fetch('/api/wearables/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Erro ao salvar');

            this.state.summary = data.summary;
            this.state.health = data.health;
            this.render();
            this.toast('⌚ Dados do relógio sincronizados!', 'success');
            if (typeof App !== 'undefined') App.playSound?.('success');
        } catch (e) {
            console.error('Erro ao salvar sessão do relógio:', e);
            this.toast('Não consegui sincronizar o relógio.', 'error');
        }
    },

    // ---------------------------------------------------------------
    //  DADOS
    // ---------------------------------------------------------------
    async load() {
        try {
            const res = await fetch('/api/wearables');
            const data = await res.json();
            this.state.summary = data.summary;
            this.state.health = data.health;
            this.state.devices = data.devices || [];
            this.render();
        } catch (e) {
            console.warn('Falha ao carregar o relógio:', e);
            this.render();
        }
    },

    resetLive() {
        this.state.live = { bpm: 0, samples: 0, min: 0, max: 0, sum: 0, resting: 0 };
        clearTimeout(this._hbTimer);
    },

    // ---------------------------------------------------------------
    //  RENDER
    // ---------------------------------------------------------------
    renderSupport() {
        const el = document.getElementById('wear-ble-support');
        if (!el) return;
        el.innerHTML = this.state.supported
            ? '<span class="text-emerald-600 font-bold">📶 Bluetooth disponível neste aparelho</span>'
            : '<span class="text-amber-600 font-bold">⚠️ Bluetooth indisponível — registre os dados na mão</span>';
        const btn = document.getElementById('wear-connect-btn');
        if (btn) {
            btn.disabled = !this.state.supported;
            btn.classList.toggle('opacity-50', !this.state.supported);
            btn.classList.toggle('cursor-not-allowed', !this.state.supported);
        }
    },

    setStatus(msg) {
        const el = document.getElementById('wear-status');
        if (el) el.textContent = msg;
    },

    renderLive() {
        const L = this.state.live;
        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
        set('wear-live-bpm', L.bpm || '—');
        set('wear-live-min', L.min || '—');
        set('wear-live-max', L.max || '—');
        set('wear-live-avg', L.samples ? Math.round(L.sum / L.samples) : '—');
        const ring = document.getElementById('wear-live-ring');
        if (ring) {
            const bpm = L.bpm || 0;
            const pct = Math.max(0, Math.min(100, ((bpm - 50) / 150) * 100));
            ring.style.background = `conic-gradient(#f43f5e ${pct}%, #e2e8f0 ${pct}%)`;
        }
    },

    render() {
        this.renderSupport();
        this.renderLive();

        const label = document.getElementById('wear-connect-label');
        if (label) label.textContent = this.state.connected ? 'Desconectar' : 'Conectar relógio';

        const badge = document.getElementById('wear-connected-badge');
        if (badge) {
            const s = this.state.summary;
            badge.textContent = this.state.connected
                ? this.state.deviceName
                : (s && s.device_name ? s.device_name : 'Nenhum relógio');
            badge.className = 'px-2 py-1 rounded-lg text-[10px] font-black ' +
                (this.state.connected || (s && s.connected)
                    ? 'bg-rose-100 text-rose-700'
                    : 'bg-slate-100 text-slate-500');
        }

        const s = this.state.summary;
        if (!s) return;
        const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

        set('wear-v-burned', (s.calories_burned || 0).toLocaleString('pt-BR'));
        set('wear-v-steps', (s.steps || 0).toLocaleString('pt-BR'));
        set('wear-v-distance', (s.distance_km || 0).toFixed(2));
        set('wear-v-active', s.active_minutes || 0);
        set('wear-v-sleep', (s.sleep_hours || 0).toFixed(1));
        set('wear-v-hr-rest', s.resting_hr ?? '—');
        set('wear-v-hr-avg', s.avg_hr ?? '—');
        set('wear-v-hr-max', s.max_hr ?? '—');
        set('wear-v-spo2', s.spo2 ?? '—');
        set('wear-v-balance', (s.diet_balance > 0 ? '+' : '') + (s.diet_balance || 0));
        set('wear-v-consumed', (s.calories_consumed || 0).toLocaleString('pt-BR'));
        set('wear-v-target', (s.target_calories || 0).toLocaleString('pt-BR'));

        const bal = document.getElementById('wear-balance-badge');
        if (bal) {
            const d = s.diet_balance || 0;
            bal.textContent = d > 0 ? `${d} kcal acima da meta` : `${Math.abs(d)} kcal de saldo`;
            bal.className = 'px-2.5 py-1 rounded-full text-[10px] font-black ' +
                (d > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700');
        }

        // barras de progresso
        const bar = (id, pct) => { const el = document.getElementById(id); if (el) el.style.width = `${pct || 0}%`; };
        bar('wear-bar-steps', s.progress?.steps);
        bar('wear-bar-active', s.progress?.active_minutes);
        bar('wear-bar-sleep', s.progress?.sleep_hours);
        bar('wear-bar-burned', s.progress?.calories_burned);
        set('wear-pct-steps', `${s.progress?.steps || 0}%`);
        set('wear-pct-active', `${s.progress?.active_minutes || 0}%`);
        set('wear-pct-sleep', `${s.progress?.sleep_hours || 0}%`);
        set('wear-pct-burned', `${s.progress?.calories_burned || 0}%`);

        // saúde cardiovascular
        const h = this.state.health;
        const hs = document.getElementById('wear-health-score');
        if (h && h.score !== null && h.score !== undefined) {
            if (hs) hs.textContent = `${h.score} · ${h.label}`;
            const notes = document.getElementById('wear-health-notes');
            if (notes) {
                notes.innerHTML = (h.notes && h.notes.length)
                    ? h.notes.map(n => `<li class="text-[10px] text-slate-500">• ${n}</li>`).join('')
                    : '<li class="text-[10px] text-emerald-600">• Tudo certo por hoje. 👏</li>';
            }
        } else if (hs) {
            hs.textContent = '—';
        }
    },

    toast(msg, type) {
        if (typeof App !== 'undefined') App.showToast(msg, type);
        else console.log(msg);
    },
};

function toDataView(dataView) {
    if (typeof dataView.getUint16 === 'function') return dataView;
    if (dataView instanceof ArrayBuffer) return new DataView(dataView);
    if (dataView && dataView.buffer) return new DataView(dataView.buffer, dataView.byteOffset || 0, dataView.byteLength);
    return new DataView(0);
}

window.Wearable = Wearable;