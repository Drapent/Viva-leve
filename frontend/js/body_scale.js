/**
 * VivaLeve - Módulo da Balança Digital (Bioimpedância via Bluetooth)
 *
 * Três caminhos, do mais automático ao mais manual:
 *   1. Web Bluetooth: lê a balança de verdade (Body Composition / Weight GATT
 *      services) e decodifica os campos conforme o padrão Bluetooth SIG.
 *   2. Manual: você digita o que a balança mostrou.
 *   3. Simulador: gera uma leitura realista para testar sem ter o aparelho.
 *
 * Tudo que chega aqui vira corpo 3D: a leitura é enviada para /api/body/scale/sync
 * e o backend devolve o modelo remodelado.
 */

const BodyScale = {
    state: {
        supported: false,
        connected: false,
        deviceName: '',
        device: null,
        characteristic: null,
        service: null,
        lastReading: null,
        history: [],
        busy: false,
    },

    // Serviços/características do padrão Bluetooth SIG
    // (Weight Scale = 0x181D/0x2A9D, Body Composition = 0x181B/0x2A9C)
    GATT: {
        BODY_COMPOSITION_SERVICE: 0x181B,
        BODY_COMPOSITION_MEASUREMENT: 0x2a9c,
        BODY_COMPOSITION_FEATURE: 0x2a9d,
        WEIGHT_SCALE_SERVICE: 0x181d,
        WEIGHT_MEASUREMENT: 0x2a9d,
        WEIGHT_SCALE_FEATURE: 0x2a9e,
    },

    // Conversão Bluetooth: 1 unidade = 0.01 kg (0x0101)
    UNIT_0_01_KG: 257,
    UNIT_0_1_KG: 10,
    UNIT_0_005_KG: 100 / 2,

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
            this.toast('Seu navegador não suporta Bluetooth. Use a leitura manual.', 'error');
            return;
        }
        if (this.state.busy) return;
        this.state.busy = true;
        this.setStatus('Procurando balanças próximas...');

        try {
            // Filtros padrão primeiro; sem filtro aceitamos qualquer aparelho
            // (várias balanças chinesas usam serviços proprietários).
            let device;
            try {
                device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { services: [this.GATT.BODY_COMPOSITION_SERVICE] },
                        { services: [this.GATT.WEIGHT_SCALE_SERVICE] },
                    ],
                    optionalServices: [
                        this.GATT.BODY_COMPOSITION_SERVICE,
                        this.GATT.BODY_COMPOSITION_MEASUREMENT,
                        this.GATT.BODY_COMPOSITION_FEATURE,
                        this.GATT.WEIGHT_SCALE_SERVICE,
                        this.GATT.WEIGHT_MEASUREMENT,
                        this.GATT.WEIGHT_SCALE_FEATURE,
                    ],
                });
            } catch (firstErr) {
                // Retry sem filtros (permite parear com balança de serviço customizado)
                device = await navigator.bluetooth.requestDevice({
                    acceptAllDevices: true,
                    optionalServices: ['generic_access', 'generic_attribute'],
                });
            }

            this.state.device = device;
            this.state.deviceName = device.name || 'Balança';
            this.setStatus(`Conectando em ${this.state.deviceName}...`);
            this.toast(`🔗 Pareado com ${this.state.deviceName}`, 'success');

            const server = await device.gatt.connect();
            device.addEventListener('gattserverdisconnected', () => this.onDisconnected());

            await this.subscribe(server);
            this.state.connected = true;
            this.render();
            this.setStatus('Conectado! Suba na balança e aguarde a leitura.');
        } catch (e) {
            if (e && e.name === 'NotFoundError') {
                this.setStatus('Nenhuma balança escolhida.');
            } else {
                console.error('Falha no Bluetooth da balança:', e);
                this.setStatus('Não foi possível conectar. Use a leitura manual.');
                this.toast('Falha ao conectar a balança. Tente a leitura manual.', 'error');
            }
        } finally {
            this.state.busy = false;
            this.render();
        }
    },

    async subscribe(server) {
        // Body Composition é o mais rico (gordura, músculo, água, ósseo, visceral)
        const bcService = await server.getPrimaryService(this.GATT.BODY_COMPOSITION_SERVICE)
            .catch(() => null);

        if (bcService) {
            this.state.service = this.GATT.BODY_COMPOSITION_SERVICE;
            const ch = await bcService.getCharacteristic(this.GATT.BODY_COMPOSITION_MEASUREMENT).catch(() => null);
            if (ch) {
                this.state.characteristic = ch;
                ch.addEventListener('characteristicvaluechanged', (e) => {
                    const reading = BodyScale.parseBodyComposition(e.target.value, this.state.deviceName);
                    if (reading) this.handleReading(reading, 'ble');
                });
                if (ch.startNotifications) await ch.startNotifications();
                this.setStatus('Conectado (Body Composition). Suba na balança!');
                return;
            }
        }

        // Fallback: Weight Scale (pelo menos o peso)
        const wService = await server.getPrimaryService(this.GATT.WEIGHT_SCALE_SERVICE).catch(() => null);
        if (wService) {
            this.state.service = this.GATT.WEIGHT_SCALE_SERVICE;
            const ch = await wService.getCharacteristic(this.GATT.WEIGHT_MEASUREMENT).catch(() => null);
            if (ch) {
                this.state.characteristic = ch;
                ch.addEventListener('characteristicvaluechanged', (e) => {
                    const reading = BodyScale.parseWeight(e.target.value, this.state.deviceName);
                    if (reading) this.handleReading(reading, 'ble');
                });
                if (ch.startNotifications) await ch.startNotifications();
                this.setStatus('Conectado (balança de peso). Suba e aguarde!');
                return;
            }
        }

        throw new Error('Serviço de medição não encontrado nesta balança.');
    },

    onDisconnected() {
        this.state.connected = false;
        this.state.characteristic = null;
        this.setStatus('Balança desconectada.');
        this.render();
        this.toast('Balança desconectada.', 'error');
    },

    disconnect() {
        try { if (this.state.device && this.state.device.gatt.connected) this.state.device.gatt.disconnect(); } catch (e) { /* já caiu */ }
        this.state.connected = false;
        this.state.characteristic = null;
        this.setStatus('Desconectado.');
        this.render();
    },

    // ---------------------------------------------------------------
    //  DECODIFICAÇÃO (Bluetooth SIG)
    // ---------------------------------------------------------------
    /**
     * Body Composition Measurement (0x2A9C), flags uint16 little-endian.
     * Ordem dos campos depende das flags — por isso a leitura é sequencial.
     */
    parseBodyComposition(dataView, deviceName) {
        const dv = toDataView(dataView);
        if (dv.byteLength < 2) return null;

        let off = 0;
        const flags = dv.getUint16(off, true); off += 2;
        const imperial = !!(flags & 0x0001);

        if (flags & 0x0002) off += 7;                 // Time Stamp
        if (flags & 0x0004) off += 2;                 // User ID
        if (flags & 0x0008) off += 2;                 // Basal Metabolism (kJ)
        if (flags & 0x0010) off += 2;                 // Muscle Percentage (%)
        if (flags & 0x0020) off += 2;                 // Muscle Mass
        if (flags & 0x0040) off += 2;                 // Fat Free Mass
        if (flags & 0x0080) off += 2;                 // Soft Lean Mass
        if (flags & 0x0100) off += 2;                 // Body Water Mass
        if (flags & 0x0200) off += 2;                 // Impedance
        if (flags & 0x0400) off += 2;                 // Weight
        if (flags & 0x0800) off += 2;                 // Height
        if (flags & 0x1000) off += 2;                 // Fat Mass %

        // Segunda passada: agora sim, lendo os valores.
        off = 2;
        const out = { device_name: deviceName || 'Balança digital', raw: { flags } };
        const unit = imperial ? 2.20462 : 1;         // lb -> kg

        const u = () => dv.getUint16(off, true);
        const u16val = (div) => { const v = u(); off += 2; return v / div; };

        if (flags & 0x0002) off += 7;
        if (flags & 0x0004) off += 2;
        if (flags & 0x0008) out.basal_metabolism = u16val(1) / 4.18;   // kJ -> kcal
        if (flags & 0x0010) out.muscle_pct = u16val(100);
        if (flags & 0x0020) out.muscle_mass = u16val(1) * unit;
        if (flags & 0x0040) out.fat_free_mass = u16val(1) * unit;
        if (flags & 0x0080) out.soft_lean_mass = u16val(1) * unit;
        if (flags & 0x0100) out.water_mass = u16val(1) * unit;
        if (flags & 0x0200) out.impedance = u16val(1);
        if (flags & 0x0400) out.weight = u16val(10) * unit;
        if (flags & 0x0800) out.height = u16val(1000);
        if (flags & 0x1000) out.body_fat = u16val(100);

        return finalizeReading(out);
    },

    /** Weight Measurement (0x2A9D), flags uint8. */
    parseWeight(dataView, deviceName) {
        const dv = toDataView(dataView);
        if (dv.byteLength < 4) return null;

        const flags = dv.getUint8(0);
        const imperial = !!(flags & 0x01);
        let off = 1;
        const raw = dv.getUint16(off, true); off += 2;

        // 0x01 => resolução 0.005 kg (ou 0.01 lb); 0x00 => 0.005 kg / 0.1 lb
        const div = imperial ? (flags & 0x02 ? 100 : 10) : (flags & 0x02 ? 200 : 100);
        const unit = imperial ? 0.45359237 : 1;

        if (flags & 0x04) off += 7;
        if (flags & 0x08) off += 2;

        return finalizeReading({
            weight: (raw / div) * unit,
            device_name: deviceName || 'Balança digital',
            raw: { flags, raw },
        });
    },

    // ---------------------------------------------------------------
    //  LEITURA -> BACKEND
    // ---------------------------------------------------------------
    async handleReading(reading, source) {
        this.state.lastReading = reading;
        this.renderReading(reading);
        this.toast(`📊 Leitura recebida: ${reading.weight ? reading.weight.toFixed(1) + ' kg' : 'sem peso'}`, 'success');
        if (typeof App !== 'undefined') App.playSound?.('success');
        await this.send(reading, source);
    },

    async send(reading, source) {
        try {
            const res = await fetch('/api/body/scale/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...reading, source, device_name: reading.device_name || 'Balança digital' }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Erro ao salvar');

            if (window.Avatar3D && window.Avatar && data.body_model) {
                Avatar.setBodyModel(data.body_model);
            }
            if (window.Avatar) Avatar.load?.();

            this.setStatus('✅ Leitura salva! Seu avatar foi remodelado.');
            this.toast('Avatar remodelado com a leitura da balança!', 'success');
            this.load();
        } catch (e) {
            console.error('Erro ao sincronizar balança:', e);
            this.toast('Não consegui salvar a leitura. Tente de novo.', 'error');
        }
    },

    /** Envio do formulário manual. */
    async submitManual() {
        const get = (id) => {
            const el = document.getElementById(id);
            if (!el) return null;
            const v = parseFloat(el.value);
            return isFinite(v) ? v : null;
        };
        const reading = {
            weight: get('scale-weight'),
            body_fat: get('scale-fat'),
            muscle_mass: get('scale-muscle'),
            water_pct: get('scale-water'),
            bone_mass: get('scale-bone'),
            visceral_fat: get('scale-visceral'),
            basal_metabolism: get('scale-bmr'),
            device_name: document.getElementById('scale-device-name')?.value || 'Manual',
        };
        if (!reading.weight && !reading.body_fat) {
            this.toast('Informe pelo menos o peso ou o % de gordura.', 'error');
            return;
        }
        await this.send(reading, 'manual');
        // limpa o formulário
        ['scale-weight', 'scale-fat', 'scale-muscle', 'scale-water', 'scale-bone', 'scale-visceral', 'scale-bmr']
            .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    },

    /** Leitura simulada (para testar o fluxo sem ter a balança). */
    simulate() {
        const cur = this.state.lastReading || {};
        const weight = cur.weight ? cur.weight : (App?.userProfile?.weight || 75);
        const fat = cur.body_fat ? cur.body_fat : 22 + Math.random() * 4;
        // Caminhada lenta e plausível, como uma balança de bioimpedância
        const wobble = () => (Math.random() - 0.5) * 0.25;
        this.handleReading({
            weight: +(weight + wobble()).toFixed(1),
            body_fat: +(fat + wobble()).toFixed(1),
            muscle_mass: +(cur.muscle_pct || 44 + wobble()).toFixed(1),
            water_pct: +(cur.water_pct || 57 + wobble()).toFixed(1),
            bone_mass: +(cur.bone_mass || 3.2).toFixed(2),
            visceral_fat: +(cur.visceral_fat || 7 + wobble() / 2).toFixed(1),
            basal_metabolism: Math.round(cur.basal_metabolism || 1680),
            device_name: 'Simulador',
        }, 'simulador');
    },

    // ---------------------------------------------------------------
    //  DADOS
    // ---------------------------------------------------------------
    async load() {
        try {
            const res = await fetch('/api/body/composition');
            const data = await res.json();
            if (data.latest) this.state.lastReading = data.latest;
            this.state.hasScale = data.has_scale;
            if (data.model && window.Avatar) Avatar.setBodyModel(data.model);
            this.render();
        } catch (e) {
            console.warn('Falha ao carregar composição corporal:', e);
            this.render();
        }
        try {
            const res = await fetch('/api/body/history?limit=30');
            const data = await res.json();
            this.state.history = data.history || [];
            this.renderHistory();
        } catch (e) { /* histórico é opcional */ }
    },

    // ---------------------------------------------------------------
    //  RENDER
    // ---------------------------------------------------------------
    renderSupport() {
        const el = document.getElementById('scale-ble-support');
        if (!el) return;
        if (this.state.supported) {
            el.innerHTML = '<span class="text-emerald-600 font-bold">📶 Bluetooth disponível neste aparelho</span>';
        } else {
            el.innerHTML = '<span class="text-amber-600 font-bold">⚠️ Bluetooth indisponível — use a leitura manual</span>';
        }
        const btn = document.getElementById('scale-connect-btn');
        if (btn) {
            btn.disabled = !this.state.supported;
            btn.classList.toggle('opacity-50', !this.state.supported);
            btn.classList.toggle('cursor-not-allowed', !this.state.supported);
        }
    },

    setStatus(msg) {
        const el = document.getElementById('scale-status');
        if (el) el.textContent = msg;
    },

    render() {
        this.renderSupport();
        const label = document.getElementById('scale-connect-label');
        if (label) label.textContent = this.state.connected ? 'Desconectar' : 'Conectar balança';
        const badge = document.getElementById('scale-connected-badge');
        if (badge) {
            badge.textContent = this.state.connected ? this.state.deviceName : 'Nenhuma balança';
            badge.className = 'px-2 py-1 rounded-lg text-[10px] font-black ' +
                (this.state.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500');
        }
        const source = document.getElementById('scale-source-badge');
        if (source) {
            const src = this.state.lastReading?.source;
            const map = { ble: 'Bluetooth', manual: 'Manual', simulador: 'Simulador', balanca: 'Balança' };
            source.textContent = this.state.lastReading ? (map[src] || src || '—') : 'sem leitura';
        }
        if (this.state.lastReading) this.renderReading(this.state.lastReading);
    },

    renderReading(r) {
        const set = (id, val, suffix) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val === null || val === undefined ? '—' : `${val}${suffix || ''}`;
        };
        set('scale-v-weight', r.weight ? r.weight.toFixed(1) : '—', ' kg');
        set('scale-v-fat', r.body_fat ? r.body_fat.toFixed(1) : '—', ' %');
        set('scale-v-muscle', r.muscle_mass ? r.muscle_mass.toFixed(1) : '—', ' %');
        set('scale-v-water', r.water_pct ? r.water_pct.toFixed(1) : '—', ' %');
        set('scale-v-bone', r.bone_mass ? r.bone_mass.toFixed(2) : '—', ' kg');
        set('scale-v-visceral', r.visceral_fat ? r.visceral_fat.toFixed(0) : '—', ' ');
        set('scale-v-bmr', r.basal_metabolism ? Math.round(r.basal_metabolism) : '—', ' kcal');
        set('scale-v-date', r.date ? new Date(r.date + 'T12:00:00').toLocaleDateString('pt-BR') : '—');
    },

    renderHistory() {
        const el = document.getElementById('scale-history');
        if (!el) return;
        const h = this.state.history;
        if (!h.length) {
            el.innerHTML = '<p class="text-[11px] text-slate-400 text-center py-3">Nenhuma leitura ainda. Conecte a balança ou envie os dados na mão.</p>';
            return;
        }
        el.innerHTML = h.slice().reverse().slice(0, 10).map(d => `
            <div class="flex items-center justify-between py-1.5 px-2 rounded-lg bg-slate-50 text-[11px]">
                <span class="font-bold text-slate-500">${new Date(d.date + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}</span>
                <span class="font-black text-slate-700">${d.weight ? d.weight.toFixed(1) + ' kg' : '—'}</span>
                <span class="font-bold text-rose-500">${d.body_fat ? d.body_fat.toFixed(1) + '%' : '—'}</span>
                <span class="font-bold text-emerald-600">${d.muscle_mass ? d.muscle_mass.toFixed(1) + '%' : '—'}</span>
            </div>
        `).join('');
    },

    toggleConnection() {
        if (this.state.connected) this.disconnect();
        else this.connect();
    },

    toast(msg, type) {
        if (typeof App !== 'undefined') App.showToast(msg, type);
        else console.log(msg);
    },
};

// ---------- helpers puros ----------
function toDataView(dataView) {
    if (typeof dataView.getUint16 === 'function') return dataView;
    if (dataView instanceof ArrayBuffer) return new DataView(dataView);
    if (dataView && dataView.buffer) return new DataView(dataView.buffer, dataView.byteOffset || 0, dataView.byteLength);
    return new DataView(0);
}

/** Normaliza a leitura e calcula o que faltar a partir do que temos. */
function finalizeReading(out) {
    const hasWeight = typeof out.weight === 'number' && out.weight > 20;
    const hasFat = typeof out.body_fat === 'number' && out.body_fat > 0;
    if (!hasWeight && !hasFat) return null;

    // Balanças com bioimpedância mandam massa magra; dela sai o % de gordura
    if (!hasFat && typeof out.fat_free_mass === 'number' && hasWeight) {
        out.body_fat = clampPct(((hasWeight - out.fat_free_mass) / hasWeight) * 100);
    }
    // % de músculo esquelético (flag 0x10) -> massa muscular equivalente
    if (!out.muscle_mass && typeof out.muscle_pct === 'number') out.muscle_mass = out.muscle_pct;

    if (typeof out.water_pct !== 'number' && typeof out.water_mass === 'number' && hasWeight) {
        out.water_pct = clampPct((out.water_mass / hasWeight) * 100, 30, 75);
    }
    if (typeof out.bone_mass !== 'number' && hasWeight) {
        out.bone_mass = +(hasWeight * 0.0125).toFixed(2);
    }
    return out;
}

function clampPct(v, lo, hi) {
    const l = lo === undefined ? 3 : lo, h = hi === undefined ? 65 : hi;
    if (!isFinite(v)) return 0;
    return +Math.max(l, Math.min(h, v)).toFixed(1);
}

window.BodyScale = BodyScale;