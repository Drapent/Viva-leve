/**
 * VivaLeve - Avatar 3D (renderizador WebGL / three.js)
 *
 * Constrói um boneco paramétrico a partir de dois pacotes do backend:
 *   - `body`       : leitura da balança digital (gordura, músculo, peso, altura)
 *   - `appearance` : traços do rosto extraídos da foto pela IA (pele, cabelo, barba)
 *
 * O corpo é montado com perfiles de revolução (LatheGeometry) e cápsulas, então
 * "engordar" e "emagrecer" muda a silhueta de verdade — e a mudança é animada
 * frame a frame (morph suave), não um salto.
 *
 * Não depende de nada externo além de `three.min.js` (vendorizado local).
 */
const Avatar3D = (() => {
    // ---- Estado interno -------------------------------------------------
    let renderer = null, scene = null, camera = null, root = null;
    let canvas = null, rafId = null, running = false, visible = true;
    let lights = {}, auraFx = null, faceTexture = null;
    let current = {}, target = {}, morphing = false;
    let disposed = false;

    // Estado da câmera (órbita simples, sem OrbitControls para reduzir peso)
    const cam = { theta: 0.35, phi: 1.42, radius: 3.2, targetY: 1.05 };
    const drag = { active: false, x: 0, y: 0, autoSpin: 0.00035, idleFrames: 0 };

    const _v3 = (x, y, z) => (window.THREE ? new THREE.Vector3(x, y, z) : null);

    // ---- Parâmetros padrão ----------------------------------------------
    const DEFAULT_PARAMS = {
        height_scale: 1.0, bulk: 0.0, definition: 0.0, muscle_scale: 1.0,
        shoulder_extra: 0.1, chest_extra: 0.3, waist_extra: 0.2, hip_extra: 0.2,
        arm_extra: 0.35, thigh_extra: 0.25, neck_extra: 0.15, face_fullness: 0.2,
        belly: 0.0,
    };
    const DEFAULT_LOOK = {
        skin_tone: '#dfae86', hair_color: '#2b1d16', eye_color: '#3b2412',
        face_shape: 'quadrado', hair_style: 'curto', facial_hair: 'nenhum',
        shoulder_width: 'medio', frame: 'medio',
        brow_thickness: 1.0, face_roundness: 1.0, jaw_width: 1.0,
    };

    let look = { ...DEFAULT_LOOK };
    let equipped = { outfit: 'regata_basica', accessory: 'shaker', aura: 'nenhuma' };
    let outfitCatalog = {};
    let bodyParts = {};   // referências para a animação/morph

    // =====================================================================
    //  BOOT
    // =====================================================================
    function init(canvasId) {
        canvas = typeof canvasId === 'string' ? document.getElementById(canvasId) : canvasId;
        if (!canvas) return fail('canvas do avatar nao encontrado');
        if (!window.THREE) return fail('three.js nao carregou');

        disposed = false;
        scene = new THREE.Scene();

        camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
        camera.position.set(0, 1.5, 3.2);

        try {
            renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
        } catch (e) {
            return fail('WebGL indisponivel neste aparelho');
        }
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.05;
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        setupLights();
        root = new THREE.Group();
        scene.add(root);

        // Estúdio: piso + fundo suave (dá "peso" e profundidade ao boneco)
        buildStudio();

        target = { ...DEFAULT_PARAMS };
        current = { ...DEFAULT_PARAMS };
        rebuildBody();
        applyLook(look, true);

        bindInteractions();
        resize();
        window.addEventListener('resize', onResize);
        document.addEventListener('visibilitychange', onVisibility);

        start();
        return true;
    }

    function fail(msg) {
        console.warn('[Avatar3D]', msg);
        if (canvas && canvas.parentElement) {
            const fb = canvas.parentElement.querySelector('[data-3d-fallback]');
            if (fb) fb.classList.remove('hidden');
        }
        return false;
    }

    // =====================================================================
    //  CENA
    // =====================================================================
    function setupLights() {
        const key = new THREE.DirectionalLight(0xffffff, 1.05);
        key.position.set(2.6, 4.2, 3.4);
        key.castShadow = true;
        key.shadow.mapSize.set(1024, 1024);
        key.shadow.camera.near = 0.5;
        key.shadow.camera.far = 14;
        const d = 2.4;
        key.shadow.camera.left = -d; key.shadow.camera.right = d;
        key.shadow.camera.top = d; key.shadow.camera.bottom = -d;
        scene.add(key);
        lights.key = key;

        const fill = new THREE.DirectionalLight(0xbcd8ff, 0.42);
        fill.position.set(-3.2, 2.0, 2.2);
        scene.add(fill);
        lights.fill = fill;

        const rim = new THREE.DirectionalLight(0xffd6a0, 0.62);
        rim.position.set(-1.4, 2.8, -3.4);
        scene.add(rim);
        lights.rim = rim;

        scene.add(new THREE.HemisphereLight(0xf2f6ff, 0x4b5563, 0.5));
    }

    function buildStudio() {
        const floorMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a, roughness: 0.86, metalness: 0.04,
        });
        const floor = new THREE.Mesh(new THREE.CircleGeometry(2.6, 48), floorMat);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = 0;
        floor.receiveShadow = true;
        scene.add(floor);

        // Anel luminoso sob o avatar (efeito "vitrine"/stage)
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x34d399, transparent: true, opacity: 0.55, side: THREE.DoubleSide,
        });
        const ring = new THREE.Mesh(new THREE.RingGeometry(0.92, 1.02, 64), ringMat);
        ring.rotation.x = -Math.PI / 2;
        ring.position.y = 0.006;
        scene.add(ring);
        bodyParts.stageRing = ring;

        // Luz de preenchimento vinda de baixo (boca/rosto não some na sombra)
        const under = new THREE.PointLight(0xffffff, 0.30, 6);
        under.position.set(0, 0.55, 1.5);
        scene.add(under);
    }

    // =====================================================================
    //  CORPO PARAMÉTRICO
    // =====================================================================
    function rebuildBody() {
        // Remove o corpo anterior e libera recursos
        while (root.children.length) {
            const child = root.children[0];
            root.remove(child);
            disposeObject(child);
        }
        // `stageRing` e `outfit` sao repostos aqui; `_lastOutfitKind` e
        // reescrito por quem chama, logo apos o rebuild terminar.
        const keptGear = [bodyParts._lastOutfitKind, bodyParts._lastAura, bodyParts._lastAccessory];
        bodyParts = { stageRing: bodyParts.stageRing, _lastOutfitKind: keptGear[0], _lastAura: keptGear[1], _lastAccessory: keptGear[2] };

        const P = current;
        const skinMat = new THREE.MeshStandardMaterial({
            color: new THREE.Color(look.skin_tone || DEFAULT_LOOK.skin_tone),
            roughness: 0.72, metalness: 0.02,
        });

        const hs = P.height_scale;
        const mus = P.muscle_scale;

        // ---- QUADRIL / TORAX ------------------------------------------
        // Perfil de revolução: quadril -> cintura -> caixa torácica -> ombros -> pescoço
        const torsoProfile = [
            new THREE.Vector2(0.001, 0.00),
            new THREE.Vector2(0.150 + P.hip_extra * 0.085, 0.02),
            new THREE.Vector2(0.148 + P.hip_extra * 0.075, 0.12),
            new THREE.Vector2(0.128 + P.waist_extra * 0.075, 0.22),   // cintura
            new THREE.Vector2(0.140 + P.chest_extra * 0.070, 0.32),
            new THREE.Vector2(0.152 + P.chest_extra * 0.085, 0.42),   // peito
            new THREE.Vector2(0.150 + P.shoulder_extra * 0.105, 0.50), // ombros
            new THREE.Vector2(0.075 + P.neck_extra * 0.055, 0.565),   // base do pescoço
            new THREE.Vector2(0.001, 0.575),
        ];
        const torso = new THREE.Mesh(new THREE.LatheGeometry(torsoProfile, 40), skinMat);
        torso.castShadow = true;
        torso.receiveShadow = true;
        // Ombros mais largos que a profundidade (silhueta humana real)
        const widthK = (look.shoulder_width === 'largo' ? 1.16 : look.shoulder_width === 'estreito' ? 0.88 : 1.0);
        torso.scale.set(widthK * (0.97 + mus * 0.10), hs * (1.0 + hs * 0.06), 0.74);
        torso.position.y = 0.80 * hs;
        root.add(torso);
        bodyParts.torso = torso;

        // Barriga: abaula a propria superficie do torso em vez de ser uma esfera
        // grudada na frente (que parecia uma bola solta na frente do corpo).
        // ---- BARRIGA -------------------------------------------------
        // Esfera ACHATADA que avanca da cintura. A escala e o RAIO em metros;
        // por isso o centro fica recuado para a traseira entrar no torso e
        // apenas a frente aflora (nunca uma bola solta na frente do corpo).
        if (P.belly > 0.01) {
            const waistR = 0.128 + P.waist_extra * 0.075;
            const belly = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 20), skinMat);
            belly.scale.set(
                waistR * 0.98,                                 // largura
                0.082 + P.belly * 0.018,                      // achatada na vertical
                waistR * (0.52 + P.belly * 0.12)               // profundidade
            );
            belly.position.set(0, (0.80 + 0.215) * hs, waistR * 0.20 + P.belly * 0.010);
            belly.castShadow = true;
            root.add(belly);
            bodyParts.belly = belly;
        } else {
            bodyParts.belly = null;
        }

        // ---- PESCOÇO ---------------------------------------------------
        const neckLen = 0.115 * hs;
        const neck = new THREE.Mesh(
            new THREE.CylinderGeometry(0.052 + P.neck_extra * 0.038, 0.060 + P.neck_extra * 0.042, neckLen, 20),
            skinMat
        );
        neck.position.y = (1.385) * hs;
        neck.castShadow = true;
        root.add(neck);
        bodyParts.neck = neck;

        // ---- CABEÇA ----------------------------------------------------
        buildHead(skinMat, hs);

        // ---- BRAÇOS ----------------------------------------------------
        const shoulderY = (1.30) * hs;
        const shoulderX = (0.176 + P.shoulder_extra * 0.105) * widthK;
        bodyParts.arms = [];
        for (const side of [-1, 1]) {
            const arm = new THREE.Group();
            arm.position.set(side * shoulderX, shoulderY, 0);

            const upperLen = (0.28) * hs;
            const upperR = (0.048 + P.arm_extra * 0.026) * mus;
            const upper = new THREE.Mesh(new THREE.CapsuleGeometry(upperR, upperLen, 6, 14), skinMat);
            upper.position.y = -upperLen / 2 - upperR * 0.5;
            upper.castShadow = true;
            arm.add(upper);

            const foreLen = (0.245) * hs;
            const foreR = (0.040 + P.arm_extra * 0.020) * mus;
            const fore = new THREE.Mesh(new THREE.CapsuleGeometry(foreR, foreLen, 6, 14), skinMat);
            fore.position.y = -upperLen - foreLen / 2 - upperR * 0.9;
            fore.castShadow = true;
            arm.add(fore);

            const hand = new THREE.Mesh(new THREE.SphereGeometry(foreR * 1.45, 16, 12), skinMat);
            hand.scale.set(0.85, 1.25, 0.62);
            hand.position.y = -upperLen - foreLen - foreR * 1.1;
            hand.castShadow = true;
            arm.add(hand);

            // Ombro (deltoide) — engrossa com massa muscular
            const deltR = 0.055 + P.arm_extra * 0.030;
            const delt = new THREE.Mesh(new THREE.SphereGeometry(deltR, 16, 12), skinMat);
            delt.position.y = 0.01;
            delt.scale.set(1, 0.92, 0.95);
            delt.castShadow = true;
            arm.add(delt);

            root.add(arm);
            // Guarda as dimensões de construção para o morph escalar em cima
            bodyParts.arms.push({ group: arm, side, built: { upperR, foreR, deltR, hs } });
        }

        // ---- PERNAS ----------------------------------------------------
        const hipY = (0.815) * hs;
        const hipX = (0.086 + P.hip_extra * 0.030);
        bodyParts.legs = [];
        for (const side of [-1, 1]) {
            const leg = new THREE.Group();
            leg.position.set(side * hipX, hipY, 0);

            const thighLen = (0.40) * hs;
            const thighR = (0.082 + P.thigh_extra * 0.042) * (0.75 + mus * 0.35);
            const thigh = new THREE.Mesh(new THREE.CapsuleGeometry(thighR, thighLen, 6, 14), skinMat);
            thigh.position.y = -thighLen / 2 - thighR * 0.3;
            thigh.castShadow = true;
            leg.add(thigh);

            const shinLen = (0.38) * hs;
            const shinR = (0.058 + P.thigh_extra * 0.020) * (0.8 + mus * 0.28);
            const shin = new THREE.Mesh(new THREE.CapsuleGeometry(shinR, shinLen, 6, 14), skinMat);
            shin.position.y = -thighLen - shinLen / 2 - thighR * 0.55;
            shin.castShadow = true;
            leg.add(shin);

            const foot = new THREE.Mesh(new THREE.BoxGeometry(0.095, 0.062, 0.215), skinMat);
            foot.position.set(0, -thighLen - shinLen - shinR * 0.5 - 0.03, 0.052);
            foot.castShadow = true;
            leg.add(foot);

            root.add(leg);
            bodyParts.legs.push({ group: leg, side, built: { thighR, shinR, hs } });
        }

        // ---- ROUPA / ACESSORIO / AURA ----------------------------------
        buildOutfit();
        buildAccessory();
        buildAura();
    }

    function buildHead(skinMat, hs) {
        const P = current;
        // Rebuild da cabeça (nova foto, novo estilo): remove a anterior para
        // não acumular duas cabeças na cena.
        if (bodyParts.headGroup) {
            root.remove(bodyParts.headGroup);
            disposeObject(bodyParts.headGroup);
        }
        const head = new THREE.Group();
        const headY = (1.44 + 0.115 * hs / 2) * hs;

        // Formato do rosto (IA) -> escala do elipsoide
        const round = look.face_roundness || 1.0;
        const jaw = look.jaw_width || 1.0;
        const shape = (look.face_shape || 'quadrado').toLowerCase();
        let rx = 0.098, ry = 0.128, rz = 0.108;
        if (shape === 'redondo') { rx = 0.104; ry = 0.120; rz = 0.110; }
        else if (shape === 'oval') { rx = 0.094; ry = 0.134; rz = 0.106; }
        else if (shape === 'triangular') { rx = 0.104; ry = 0.126; rz = 0.104; }
        else if (shape === 'losango') { rx = 0.100; ry = 0.130; rz = 0.108; }
        else if (shape === 'coracao') { rx = 0.102; ry = 0.128; rz = 0.107; }

        // GorduraCorporea preenche o rosto (bochechas, papo)
        const full = 1 + P.face_fullness * 0.16;

        // Eixos REAIS do cranio: o cabelo e a barba sao construidos a partir
        // deles, senao nascem menores que a cabeca e somem dentro dela.
        const skullX = rx * round * full * jaw;
        const skullY = ry * (0.94 + full * 0.10);
        const skullZ = rz * full;

        const skull = new THREE.Mesh(new THREE.SphereGeometry(1, 40, 32), skinMat);
        skull.scale.set(skullX, skullY, skullZ);
        skull.castShadow = true;
        skull.receiveShadow = true;
        head.add(skull);
        bodyParts.skull = skull;
        bodyParts.headGroup = head;

        // Mandíbula / queixo — dá o "maxilar" ao avatar
        const jawMesh = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 18), skinMat);
        jawMesh.scale.set(rx * 0.74 * jaw * full, ry * 0.42, rz * 0.80 * full);
        jawMesh.position.set(0, -ry * 0.50, rz * 0.10);
        jawMesh.castShadow = true;
        head.add(jawMesh);

        // Orelhas
        for (const side of [-1, 1]) {
            const ear = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), skinMat);
            ear.scale.set(0.016, 0.030, 0.022);
            ear.position.set(side * rx * full * 0.98, -ry * 0.05, 0);
            head.add(ear);
        }

        head.position.y = headY;
        root.add(head);

        // Nariz (pequeno, ajuda a leitura do rosto de frente)
        const nose = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 10), skinMat);
        nose.scale.set(0.016, 0.022, 0.020);
        nose.position.set(0, -ry * 0.06, rz * full * 0.94);
        head.add(nose);
        bodyParts.nose = nose;

        buildHair(head, skullX, skullY, skullZ);
        buildFaceTexture(head, rx, ry, rz, full, round, jaw);
        buildFacialHair(head, skullX, skullY, skullZ);
    }

    function buildHair(head, sx, sy, sz) {
        const style = (look.hair_style || 'curto').toLowerCase();
        if (style === 'careca') return;

        const mat = new THREE.MeshStandardMaterial({
            color: new THREE.Color(look.hair_color || DEFAULT_LOOK.hair_color),
            roughness: 0.92, metalness: 0.0,
        });

        // sx/sy/sz sao os EIXOS REAIS do cranio (ja com round/full/jaw).
        // O cabelo nasce desses valores com folga de 4%, senao ele fica
        // dentro da cabeca e so aparece um anel fininho no topo.
        const gap = 1.045;
        const cx = sx * gap, cy = sy * gap, cz = sz * gap;

        const cap = (k, drop = 0, theta = Math.PI * 0.62) => {
            const m = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 24, 0, Math.PI * 2, 0, theta), mat);
            m.scale.set(cx * k, cy * k, cz * k);
            m.position.y = drop;
            m.castShadow = true;
            head.add(m);
            return m;
        };

        if (style === 'longo') {
            cap(1.02, cy * 0.02, Math.PI * 0.46);
            const back = new THREE.Mesh(new THREE.CapsuleGeometry(cx * 0.88, cy * 1.5, 6, 14), mat);
            back.position.set(0, -cy * 0.95, -cz * 0.44);
            back.scale.set(1, 1, 0.80);
            back.castShadow = true;
            head.add(back);
        } else if (style === 'cacheado') {
            const geo = new THREE.SphereGeometry(1, 14, 10);
            for (let i = 0; i < 30; i++) {
                const ang = (i / 30) * Math.PI * 2;
                const t = i / 30;
                const blob = new THREE.Mesh(geo, mat);
                blob.scale.set(cx * 0.32, cx * 0.32, cx * 0.32);
                blob.position.set(
                    Math.cos(ang) * cx * 0.96,
                    cy * (0.70 - t * 0.14),
                    Math.sin(ang) * cz * 0.92
                );
                blob.castShadow = true;
                head.add(blob);
            }
            cap(0.99, cy * 0.02, Math.PI * 0.44);
        } else if (style === 'trancado') {
            cap(1.01, cy * 0.02, Math.PI * 0.45);
            const geo = new THREE.CapsuleGeometry(cx * 0.16, cy * 0.5, 5, 10);
            for (let i = 0; i < 12; i++) {
                const ang = Math.PI * 0.14 + (i / 11) * Math.PI * 0.72;
                const strand = new THREE.Mesh(geo, mat);
                strand.position.set(Math.cos(ang) * cx * 1.02, -cy * 0.30, -Math.abs(Math.sin(ang)) * cz * 0.60);
                strand.castShadow = true;
                head.add(strand);
            }
        } else if (style === 'moicano') {
            cap(1.01, 0, Math.PI * 0.40);
            const strip = new THREE.Mesh(new THREE.BoxGeometry(cx * 0.40, cy * 1.16, cz * 0.32), mat);
            strip.position.set(0, cy * 0.26, 0);
            strip.castShadow = true;
            head.add(strip);
        } else if (style === 'medio') {
            cap(1.01, cy * 0.02, Math.PI * 0.45);
            const back = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), mat);
            back.scale.set(cx * 1.0, cy * 0.80, cz * 0.82);
            back.position.set(0, -cy * 0.38, -cz * 0.34);
            back.castShadow = true;
            head.add(back);
        } else if (style === 'anco') {
            const bun = new THREE.Mesh(new THREE.SphereGeometry(cx * 0.42, 18, 14), mat);
            bun.position.set(0, cy * 1.00, -cz * 0.18);
            bun.castShadow = true;
            head.add(bun);
            cap(1.01, cy * 0.02, Math.PI * 0.40);
        } else { // curto
            cap(1.01, cy * 0.02, Math.PI * 0.42);
        }
    }

    function buildFacialHair(head, sx, sy, sz) {
        const kind = (look.facial_hair || 'nenhum').toLowerCase();
        if (kind === 'nenhum') return;

        const mat = new THREE.MeshStandardMaterial({
            color: new THREE.Color(look.hair_color || DEFAULT_LOOK.hair_color),
            roughness: 0.95, metalness: 0,
        });

        // sx/sy/sz: eixos reais do cranio (mesma base do cabelo)
        const k = 1.03;
        const X = sx * k, Y = sy * k, Z = sz * k;

        if (kind === 'bigode') {
            const m = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), mat);
            m.scale.set(X * 0.44, Y * 0.075, Z * 0.14);
            m.position.set(0, -Y * 0.17, Z * 0.86);
            head.add(m);
        } else if (kind === 'cavanhaque') {
            const m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), mat);
            m.scale.set(X * 0.72, Y * 0.46, Z * 0.34);
            m.position.set(0, -Y * 0.50, Z * 0.60);
            head.add(m);
        } else if (kind === 'barba_cheia') {
            const m = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 18), mat);
            m.scale.set(X * 1.02, Y * 0.86, Z * 1.0);
            m.position.set(0, -Y * 0.20, -Z * 0.04);
            m.castShadow = true;
            head.add(m);
            // Recorta a boca para a barba nao cobrir o rosto inteiro
            const skin = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({
                color: look.skin_tone, roughness: 0.75,
            }));
            skin.scale.set(X * 0.60, Y * 0.38, Z * 0.98);
            skin.position.set(0, -Y * 0.28, Z * 0.10);
            head.add(skin);
            const mustache = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), mat);
            mustache.scale.set(X * 0.42, Y * 0.07, Z * 0.13);
            mustache.position.set(0, -Y * 0.15, Z * 0.88);
            head.add(mustache);
        } else if (kind === 'por_make') {
            const m = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 12), mat);
            m.scale.set(X * 0.62, Y * 0.13, Z * 0.26);
            m.position.set(0, -Y * 0.56, Z * 0.78);
            head.add(m);
        }
    }

    /**
     * Textura do rosto: recorta um "patch" do elipsoide da cabeça e aplica a foto
     * do usuário, exatamente como o avatar 3D do WhatsApp faz.
     * Só a frente da cabeça recebe a foto; laterais e nuca ficam com a pele.
     */
    function buildFaceTexture(head, rx, ry, rz, full, round, jaw) {
        if (!faceTexture) return;

        // Recorte frontal da esfera (phi ~ 90° = frente)
        const phiLength = 2.05;
        const geo = new THREE.SphereGeometry(
            1.008, 40, 34,
            Math.PI / 2 - phiLength / 2, phiLength,
            0.42, 1.62
        );
        const mat = new THREE.MeshBasicMaterial({
            map: faceTexture,
            transparent: true,
            opacity: 0.999,
            depthWrite: false,
            side: THREE.FrontSide,
        });
        const patch = new THREE.Mesh(geo, mat);
        // Deve ser 1% MAIOR que o crânio em cada eixo, senão a foto fica
        // escondida dentro da cabeça (o jaw_width da IA pode até 1.4).
        patch.scale.set(rx * round * full * jaw * 1.02, ry * (0.94 + full * 0.10) * 1.02, rz * full * 1.02);
        patch.position.set(0, -ry * 0.02, 0);
        patch.renderOrder = 2;
        head.add(patch);
        bodyParts.facePatch = patch;
    }

    // =====================================================================
    //  ROUPA / ACESSÓRIO / AURA
    // =====================================================================
    function buildOutfit() {
        const style = outfitCatalog[equipped.outfit] || outfitCatalog['regata_basica'] || { kind: 'tank', color: '#f8fafc', accent: '#e2e8f0' };
        const P = current;
        const hs = P.height_scale;
        const color = new THREE.Color(style.color || '#f8fafc');
        const accent = new THREE.Color(style.accent || '#e2e8f0');
        const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.86, metalness: 0.02 });
        const matAccent = new THREE.MeshStandardMaterial({ color: accent, roughness: 0.72, metalness: 0.04 });

        const widthK = (look.shoulder_width === 'largo' ? 1.16 : look.shoulder_width === 'estreito' ? 0.88 : 1.0);
        const g = new THREE.Group();
        const kind = style.kind || 'tank';

        // Espessura da malha: 6mm por fora do corpo.
        const E = 0.006;
        // Recorte lateral. Regata/top deixam as costas e o ombro de fora.
        const openSide = (kind === 'tank' || kind === 'sportsbra');

        // Perfil: mesma silhueta do torso, deslocado 6mm para fora.
        // Topo em 0.505 (abaixo do ombro em 0.50) e base conforme a peça.
        const baseY = (kind === 'sportsbra') ? 0.30 : (kind === 'tee' || kind === 'hoodie') ? 0.16 : 0.235;
        const prof = [
            new THREE.Vector2(0.001, baseY),
            new THREE.Vector2(0.148 + P.hip_extra * 0.075 + E, baseY + 0.01),
            new THREE.Vector2(0.128 + P.waist_extra * 0.075 + E, 0.26),
            new THREE.Vector2(0.140 + P.chest_extra * 0.070 + E, 0.33),
            new THREE.Vector2(0.152 + P.chest_extra * 0.085 + E, 0.43),
            new THREE.Vector2(0.150 + P.shoulder_extra * 0.105 + E, 0.492),
            new THREE.Vector2(0.090 + P.neck_extra * 0.055 + E, 0.505),
            new THREE.Vector2(0.001, 0.508),
        ];
        const phiStart = openSide ? -0.62 * Math.PI : 0;
        const phiLen = openSide ? 1.24 * Math.PI : Math.PI * 2;
        const shell = new THREE.Mesh(new THREE.LatheGeometry(prof, openSide ? 30 : 44, phiStart, phiLen), mat);
        shell.scale.set(widthK * (0.97 + P.muscle_scale * 0.10), hs * (1.0 + hs * 0.06), 0.752);
        shell.position.y = 0.80 * hs;
        shell.castShadow = true;
        shell.receiveShadow = true;
        g.add(shell);

        // Alcas da regata: dois tubos finos do ombro ate a axila
        if (kind === 'tank' || kind === 'sportsbra') {
            // Sobre o ombro e na FRENTE do torso, senao some dentro do corpo.
            const strapR = 0.013;
            const topR = (0.150 + P.shoulder_extra * 0.105) * widthK * (0.97 + P.muscle_scale * 0.10);
            const strapTop = 1.335 * hs, strapBot = (0.80 + baseY + 0.005) * hs;
            for (const side of [-1, 1]) {
                const strap = new THREE.Mesh(
                    new THREE.CylinderGeometry(strapR, strapR, strapTop - strapBot, 10), mat
                );
                strap.position.set(side * topR * 0.58, (strapTop + strapBot) / 2, topR * 0.62);
                strap.rotation.z = side * 0.10;
                strap.castShadow = true;
                g.add(strap);
            }
        }

        // Gola (na altura do pescoco, nunca do queixo)
        const collar = new THREE.Mesh(new THREE.TorusGeometry(0.070 + P.neck_extra * 0.05, 0.014, 10, 26), matAccent);
        collar.rotation.x = Math.PI / 2;
        collar.position.y = 1.383 * hs;
        g.add(collar);

        // Faixa de cintura (destaque o shape)
        if (kind === 'sportsbra' || kind === 'tank') {
            const band = new THREE.Mesh(new THREE.TorusGeometry(0.134 + P.waist_extra * 0.075, 0.017, 10, 28), matAccent);
            band.rotation.x = Math.PI / 2;
            band.scale.set(1, 1, 0.75);
            band.position.y = (0.80 + baseY + 0.012) * hs;
            g.add(band);
        }

        if (kind === 'hoodie') {
            const hoodMat = new THREE.MeshStandardMaterial({ color, roughness: 0.92, side: THREE.DoubleSide });
            const hood = new THREE.Mesh(new THREE.SphereGeometry(0.128, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.74), hoodMat);
            hood.position.set(0, 1.40 * hs, -0.10);
            hood.scale.set(1.04, 1.0, 0.84);
            hood.castShadow = true;
            g.add(hood);
            const cordMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.8 });
            for (const s of [-1, 1]) {
                const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.16, 8), cordMat);
                cord.position.set(s * 0.032, 1.295 * hs, 0.085);
                cord.rotation.x = 0.15;
                g.add(cord);
            }
        }

        root.add(g);
        bodyParts.outfit = g;
    }

    function buildAccessory() {
        const id = equipped.accessory;
        if (!id || id === 'shaker' || id === 'nenhuma') return;
        const g = new THREE.Group();
        const P = current, hs = P.height_scale;

        if (id === 'galao_agua_2l') {
            const bottleMat = new THREE.MeshPhysicalMaterial({
                color: 0x22d3ee, transmission: 0.55, thickness: 0.4, roughness: 0.25,
                transparent: true, opacity: 0.75,
            });
            const bottle = new THREE.Mesh(new THREE.CylinderGeometry(0.058, 0.062, 0.24, 20), bottleMat);
            bottle.position.set(0.33, 0.30 * hs, 0.10);
            bottle.castShadow = true;
            g.add(bottle);
            const capMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.6 });
            const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.030, 0.034, 0.05, 14), capMat);
            cap.position.set(0.33, 0.44 * hs, 0.10);
            g.add(cap);
        } else if (id === 'cinto_lombar') {
            const beltMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.55 });
            const belt = new THREE.Mesh(new THREE.TorusGeometry(0.152 + P.waist_extra * 0.075, 0.026, 10, 30), beltMat);
            belt.rotation.x = Math.PI / 2;
            belt.scale.set(1, 1, 0.76);
            belt.position.y = (0.80 + 0.215) * hs;
            g.add(belt);
        } else if (id === 'tenis_dourado') {
            const shoeMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.35, metalness: 0.6 });
            bodyParts.legs.forEach(({ group, side }) => {
                const shoe = new THREE.Mesh(new THREE.BoxGeometry(0.105, 0.085, 0.235), shoeMat);
                const P2 = current, hs2 = P2.height_scale;
                const y = -(0.40 + 0.38) * hs2 - (0.058 + P2.thigh_extra * 0.020) * 0.5 - 0.028;
                shoe.position.set(0, y, 0.056);
                shoe.castShadow = true;
                group.add(shoe);
            });
        } else if (id === 'luvas_treino') {
            const gloveMat = new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.6 });
            bodyParts.arms.forEach(({ group }) => {
                const P2 = current, hs2 = P2.height_scale;
                const g2 = new THREE.Mesh(new THREE.SphereGeometry(0.052, 14, 10), gloveMat);
                g2.scale.set(0.95, 1.15, 0.85);
                g2.position.y = -(0.28 + 0.245) * hs2 - (0.040 + P2.arm_extra * 0.020) * 1.2;
                group.add(g2);
            });
        }

        if (g.children.length) root.add(g);
        bodyParts.accessory = g;
    }

    function buildAura() {
        if (auraFx) {
            root.remove(auraFx);
            disposeObject(auraFx);
            auraFx = null;
        }
        const kind = equipped.aura;
        if (!kind || kind === 'nenhuma') return;

        const colors = {
            aura_fogo: [0xff6b1a, 0xffd166],
            aura_raio: [0x38bdf8, 0xe0f2fe],
            aura_dourada: [0xfbbf24, 0xfef3c7],
        }[kind];
        if (!colors) return;

        const count = 70;
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(count * 3);
        const sizes = new Float32Array(count);
        for (let i = 0; i < count; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 1.5;
            pos[i * 3 + 1] = Math.random() * 2.0;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 1.5;
            sizes[i] = 0.05 + Math.random() * 0.07;
        }
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const sprite = makeGlowTexture(colors[0], colors[1]);
        const mat = new THREE.PointsMaterial({
            map: sprite, size: 0.14, transparent: true, opacity: 0.85,
            depthWrite: false, blending: THREE.AdditiveBlending,
        });
        const points = new THREE.Points(geo, mat);
        points.position.y = 0.05;
        root.add(points);
        auraFx = points;
    }

    function makeGlowTexture(inner, outer) {
        const c = document.createElement('canvas');
        c.width = c.height = 64;
        const ctx = c.getContext('2d');
        const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        g.addColorStop(0, '#' + new THREE.Color(inner).getHexString());
        g.addColorStop(0.45, '#' + new THREE.Color(outer).getHexString());
        g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, 64, 64);
        const tex = new THREE.CanvasTexture(c);
        return tex;
    }

    // =====================================================================
    //  API PÚBLICA — receber o modelo do backend
    // =====================================================================
    function setModel(payload) {
        if (!payload || disposed) return;
        const body = payload.body || {};
        const model = { ...DEFAULT_PARAMS, ...(body.model || {}) };

        // Altura real da leitura da balança manda sobre a do perfil
        const hs = body.height_cm ? clampNum(body.height_cm / 175.0, 0.86, 1.14) : (model.height_scale || 1);
        model.height_scale = hs;

        // (o alvo e definido dentro dos ramos abaixo)

        if (payload.equipped) equipped = { ...equipped, ...payload.equipped };
        if (payload.outfit_catalog) outfitCatalog = payload.outfit_catalog;

        // Compara o look NOVO com o ANTES. Atribuir `look` antes de comparar
        // daria sempre "iguais" e o rosto nunca seria reconstruido.
        const prevLook = look;
        const nextLook = { ...DEFAULT_LOOK, ...(look || {}), ...(payload.appearance || {}) };
        const lookChanged = JSON.stringify(nextLook) !== JSON.stringify(prevLook);
        look = nextLook;

        const bellyCrossed = (current.belly > 0.01) !== (model.belly > 0.01);
        const outfitChanged = (outfitCatalog[equipped.outfit]?.kind || 'tank') !== (bodyParts._lastOutfitKind || '');
        // Aura e acessório também mudam a geometria (partículas, garrafa, luva, tênis).
        // Sem isso, comprar uma aura na loja nao mudava NADA na cena.
        const auraChanged = equipped.aura !== (bodyParts._lastAura || '');
        const accessoryChanged = equipped.accessory !== (bodyParts._lastAccessory || '');
        if (!bodyParts.torso || lookChanged || outfitChanged || auraChanged || accessoryChanged || bellyCrossed) {
            // Geometria mudou de forma: reconstrói e ja aplica o novo estado.
            current = { ...model };
            target = model;
            morphing = false;
            rebuildBody();
            // Registra DEPOIS do rebuild: e o proprio rebuild que zera bodyParts.
            bodyParts._lastOutfitKind = outfitCatalog[equipped.outfit]?.kind || 'tank';
            bodyParts._lastAura = equipped.aura;
            bodyParts._lastAccessory = equipped.accessory;
            applyMorphImmediate();
        } else {
            // Mesmo rosto e mesma roupa: só interpola (barato e não pisca)
            target = model;
            morphing = true;
        }
        start();
    }

    function setPhoto(dataUrl) {
        if (!dataUrl || disposed) return;
        try {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => {
                faceTexture = new THREE.CanvasTexture(toSquareCanvas(img));
                faceTexture.encoding = THREE.sRGBEncoding;
                faceTexture.needsUpdate = true;
                // Recria a cabeça para aplicar a textura no patch do rosto
                const skin = bodyParts.torso && bodyParts.torso.material;
                if (skin) {
                    buildHead(skin, current.height_scale);
                }
            };
            img.onerror = () => console.warn('[Avatar3D] falha ao carregar a foto');
            img.src = dataUrl;
        } catch (e) {
            console.warn('[Avatar3D] setPhoto:', e);
        }
    }

    /** Recorta a foto em quadrado e aplica leve correção de contraste. */
    function toSquareCanvas(img) {
        const size = 512;
        const c = document.createElement('canvas');
        c.width = c.height = size;
        const ctx = c.getContext('2d');
        const side = Math.min(img.width, img.height);
        ctx.drawImage(
            img,
            (img.width - side) / 2, (img.height - side) / 2, side, side,
            0, 0, size, size
        );
        return c;
    }

    function applyLook(newLook, immediate) {
        look = { ...DEFAULT_LOOK, ...(look || {}), ...(newLook || {}) };
        if (!bodyParts.torso) return;
        bodyParts.torso.material.color.set(look.skin_tone);
        if (immediate) applyMorphImmediate();
    }

    // =====================================================================
    //  MORPH SUAVE (a "pança" que entra/sai)
    // =====================================================================
    function lerpParams(a, b, t) {
        const out = {};
        for (const k in b) {
            if (typeof b[k] === 'number' && typeof a[k] === 'number') {
                out[k] = a[k] + (b[k] - a[k]) * t;
            } else {
                out[k] = t > 0.5 ? b[k] : a[k];
            }
        }
        return out;
    }

    /** Aplica um conjunto de parâmetros reconstruindo só o que muda de forma. */
    function applyMorphImmediate() {
        const prev = current;
        current = { ...target };
        // Barriga liga/desliga -> exige reconstruir (geometria nova).
        // Todo o resto muda por escala contínua, que é barato.
        const hadBelly = prev.belly > 0.01, hasBelly = current.belly > 0.01;
        if (hadBelly !== hasBelly) {
            rebuildBody();
            bodyParts._lastOutfitKind = outfitCatalog[equipped.outfit]?.kind || 'tank';
            return;
        }
        scaleParts();
    }

    /** Escala as partes já construídas — barato, roda a cada frame do morph. */
    function scaleParts() {
        const P = current;
        const hs = P.height_scale;
        const mus = P.muscle_scale;
        // Bases geometricas: independem de hs. O `hs` ja foi aplicado na
        // CONSTRUCAO do corpo; reaplicar aqui dobrava a escala do boneco.
        const hipBaseY = 0.815, neckBaseY = 1.385, headBaseY = 1.4975;
        const torsoY = bodyParts.torso ? bodyParts.torso.scale.y : 1;
        const widthK = (look.shoulder_width === 'largo' ? 1.16 : look.shoulder_width === 'estreito' ? 0.88 : 1.0);

        if (bodyParts.torso) {
            bodyParts.torso.scale.set(widthK * (0.97 + mus * 0.10), torsoY, 0.74);
            bodyParts.torso.position.y = 0.80 * hs;
        }
        if (bodyParts.neck) {
            bodyParts.neck.position.y = neckBaseY;
            const nk = 1 + P.neck_extra * 0.9;
            bodyParts.neck.scale.set(nk, hs, nk);
        }
        // A barriga nasce escalada para o RAIO em metros. Reaplicar `bulk`
        // aqui a devolveria ao raio 1.0 da esfera unitária. Só reposiciona.
        // A barriga ja nasce com o raio correto em metros: aqui so se
        // reposiciona e reescala o volume conforme a gordura.
        if (bodyParts.belly) {
            const wR = 0.128 + P.waist_extra * 0.075;
            bodyParts.belly.scale.set(
                wR * 0.98,
                0.082 + P.belly * 0.018,
                wR * (0.52 + P.belly * 0.12)
            );
            bodyParts.belly.position.set(0, 1.015 * hs, wR * 0.20 + P.belly * 0.010);
        }
        if (bodyParts.headGroup) bodyParts.headGroup.position.y = headBaseY;

        // Braços/pernas: o raio da cápsula está "assado" na geometria, então
        // mudamos a espessura escalando só X/Z (o comprimento é no eixo Y).
        if (bodyParts.arms) {
            bodyParts.arms.forEach(({ group, side, built }) => {
                group.position.set(side * (0.176 + P.shoulder_extra * 0.105) * widthK, 1.30 * hs, 0);
                const kU = ((0.048 + P.arm_extra * 0.026) * mus) / built.upperR;
                const kF = ((0.040 + P.arm_extra * 0.020) * mus) / built.foreR;
                const kD = ((0.055 + P.arm_extra * 0.030)) / built.deltR;
                const upper = group.children[0], fore = group.children[1], hand = group.children[2], delt = group.children[3];
                upper.scale.set(kU, hs / built.hs, kU);
                fore.scale.set(kF, hs / built.hs, kF);
                hand.scale.set(0.85 * kF, 1.25 * kF, 0.62 * kF);
                hand.position.y = -(0.28 + 0.245) * hs - built.foreR * kF * 1.1;
                delt.scale.set(kD, 0.92 * kD, 0.95 * kD);
            });
        }

        if (bodyParts.legs) {
            bodyParts.legs.forEach(({ group, side, built }) => {
                group.position.set(side * (0.086 + P.hip_extra * 0.030), hipBaseY, 0);
                const kT = ((0.082 + P.thigh_extra * 0.042) * (0.75 + mus * 0.35)) / built.thighR;
                const kS = ((0.058 + P.thigh_extra * 0.020) * (0.8 + mus * 0.28)) / built.shinR;
                const kH = hs / built.hs;
                const thigh = group.children[0], shin = group.children[1], foot = group.children[2];
                thigh.scale.set(kT, kH, kT);
                shin.scale.set(kS, kH, kS);
                const footR = built.shinR * kS;
                foot.position.set(0, -(0.40 + 0.38) * hs - footR * 0.5 - 0.03, 0.052);
                foot.scale.set(kS, 1, kS);
            });
        }
    }

    // =====================================================================
    //  INTERAÇÃO (arrastar para girar, scroll para zoom)
    // =====================================================================
    function bindInteractions() {
        if (!canvas) return;

        const down = (x, y) => { drag.active = true; drag.x = x; drag.y = y; drag.idleFrames = 0; };
        const move = (x, y) => {
            if (!drag.active) return;
            const dx = x - drag.x, dy = y - drag.y;
            drag.x = x; drag.y = y;
            cam.theta -= dx * 0.009;
            cam.phi = clampNum(cam.phi - dy * 0.006, 0.55, 2.05);
            drag.idleFrames = 0;
        };
        const up = () => { drag.active = false; };

        canvas.addEventListener('mousedown', (e) => { down(e.clientX, e.clientY); e.preventDefault(); });
        window.addEventListener('mousemove', (e) => move(e.clientX, e.clientY));
        window.addEventListener('mouseup', up);

        canvas.addEventListener('touchstart', (e) => {
            const t = e.touches[0];
            down(t.clientX, t.clientY);
        }, { passive: true });
        canvas.addEventListener('touchmove', (e) => {
            const t = e.touches[0];
            move(t.clientX, t.clientY);
            e.preventDefault();
        }, { passive: false });
        window.addEventListener('touchend', up);

        canvas.addEventListener('wheel', (e) => {
            cam.radius = clampNum(cam.radius + e.deltaY * 0.0016, 1.9, 5.2);
            e.preventDefault();
        }, { passive: false });
    }

    // =====================================================================
    //  LOOP
    // =====================================================================
    function start() {
        if (running || disposed) return;
        running = true;
        rafId = requestAnimationFrame(loop);
    }

    function stop() {
        running = false;
        if (rafId) cancelAnimationFrame(rafId);
        rafId = null;
    }

    let last = performance.now();
    function loop(now) {
        if (!running || disposed) return;
        rafId = requestAnimationFrame(loop);
        const dt = Math.min(0.05, (now - last) / 1000);
        last = now;
        const t = now / 1000;

        // --- morph dos parâmetros corporais ---
        if (morphing) {
            current = lerpParams(current, target, Math.min(1, dt * 2.2));
            if (paramsClose(current, target)) { current = { ...target }; morphing = false; }
            applyMorphImmediate();
        }

        // --- respiração + balanço (deixa o boneco "vivo") ---
        if (bodyParts.torso) {
            const breathe = 1 + Math.sin(t * 1.9) * 0.012;
            bodyParts.torso.scale.z = 0.74 * breathe;
        }
        if (bodyParts.headGroup) {
            bodyParts.headGroup.rotation.y = Math.sin(t * 0.55) * 0.10;
            bodyParts.headGroup.rotation.x = Math.sin(t * 0.8) * 0.035;
            bodyParts.headGroup.position.y += Math.sin(t * 1.9) * 0.00018;
        }
        if (bodyParts.arms) {
            bodyParts.arms.forEach(({ group, side }, i) => {
                group.rotation.x = Math.sin(t * 1.1 + i) * 0.045;
                group.rotation.z = side * (0.10 + Math.sin(t * 0.9) * 0.02);
            });
        }

        // --- aura sobe continuously ---
        if (auraFx) {
            auraFx.rotation.y += dt * 0.35;
            const pos = auraFx.geometry.attributes.position;
            for (let i = 0; i < pos.count; i++) {
                let y = pos.getY(i) + dt * 0.30;
                if (y > 2.1) y = 0;
                pos.setY(i, y);
            }
            pos.needsUpdate = true;
            auraFx.material.opacity = 0.65 + Math.sin(t * 3) * 0.18;
        }

        // --- anel do palco pulsa ---
        if (bodyParts.stageRing) {
            bodyParts.stageRing.material.opacity = 0.40 + Math.sin(t * 2.1) * 0.14;
        }

        // --- câmera: rotação automática quando o usuário está parado ---
        if (!drag.active) {
            drag.idleFrames++;
            if (drag.idleFrames > 40) cam.theta += drag.autoSpin * 60 * dt;
        }
        updateCamera();
        renderer.render(scene, camera);
    }

    function updateCamera() {
        const sp = Math.sin(cam.phi), cp = Math.cos(cam.phi);
        camera.position.set(
            Math.sin(cam.theta) * sp * cam.radius,
            cp * cam.radius + cam.targetY,
            Math.cos(cam.theta) * sp * cam.radius
        );
        camera.lookAt(0, cam.targetY, 0);
    }

    function paramsClose(a, b) {
        for (const k in b) {
            if (typeof b[k] === 'number' && Math.abs(a[k] - b[k]) > 0.002) return false;
        }
        return true;
    }

    // =====================================================================
    //  UTILITÁRIOS
    // =====================================================================
    function resize() {
        if (!renderer || !canvas) return;
        const w = canvas.clientWidth || canvas.parentElement?.clientWidth || 300;
        const h = canvas.clientHeight || canvas.parentElement?.clientHeight || 420;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        // Em telas estreitas o boneco cabe sem cortar
        cam.radius = Math.max(cam.radius, (w < 380 ? 3.5 : 3.1));
        camera.updateProjectionMatrix();
    }

    function onResize() { resize(); }

    function onVisibility() {
        if (document.hidden) stop();
        else if (!disposed) start();
    }

    function clampNum(v, lo, hi, fb) {
        const n = Number(v);
        if (!isFinite(n)) return fb === undefined ? lo : fb;
        return Math.max(lo, Math.min(hi, n));
    }

    function disposeObject(obj) {
        obj.traverse?.((o) => {
            if (o.geometry) o.geometry.dispose?.();
            if (o.material) {
                const mats = Array.isArray(o.material) ? o.material : [o.material];
                mats.forEach((m) => { m.map?.dispose?.(); m.dispose?.(); });
            }
        });
    }

    function screenshot() {
        if (!renderer || !scene || !camera) return null;
        try {
            renderer.render(scene, camera);
            return renderer.domElement.toDataURL('image/png');
        } catch (e) {
            console.warn('[Avatar3D] screenshot:', e);
            return null;
        }
    }

    function setView(theta, phi, radius) {
        if (theta !== undefined && theta !== null) cam.theta = theta;
        if (phi !== undefined && phi !== null) cam.phi = clampNum(phi, 0.55, 2.05);
        if (radius !== undefined && radius !== null) cam.radius = clampNum(radius, 1.9, 5.2);
        updateCamera();
    }

    function rotateBy(dTheta) {
        cam.theta += dTheta;
        drag.idleFrames = 0;
        updateCamera();
    }

    function zoom(delta) {
        cam.radius = clampNum(cam.radius + delta, 1.9, 5.2);
        updateCamera();
    }

    function resetView() {
        cam.theta = 0.35; cam.phi = 1.42;
        frameModel();
        drag.idleFrames = 0;
        updateCamera();
    }

    /**
     * Calcula a distancia de camera para o boneco caber inteiro na tela,
     * seja ele magro ou obeso. Sem isso, um avatar gordo saía do quadro.
     */
    function frameModel() {
        if (!root) return;
        const box = new THREE.Box3().setFromObject(root);
        if (box.isEmpty()) return;
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const height = Math.max(0.4, size.y);
        const width = Math.max(0.3, size.x);

        cam.targetY = center.y;

        const distV = (height / 2) / Math.tan((camera.fov * Math.PI) / 360);
        const aspect = (camera.aspect || 1);
        // Margem lateral: o boneco ocupa ~70% da largura da tela
        const distH = (width / 2) / (Math.tan((camera.fov * Math.PI) / 360) * aspect * 0.70);
        cam.radius = clampNum(Math.max(distV, distH) * 1.16, 2.0, 6.5);
    }


    function dispose() {
        disposed = true;
        stop();
        window.removeEventListener('resize', onResize);
        document.removeEventListener('visibilitychange', onVisibility);
        if (faceTexture) faceTexture.dispose();
        disposeObject(root);
        if (renderer) renderer.dispose();
        renderer = null; scene = null; root = null; current = {}; target = {};
        bodyParts = {};
    }

    return {
        init, setModel, setPhoto, applyLook, start, stop,
        screenshot, setView, rotateBy, zoom, resetView, dispose,
        get isRunning() { return running; },
    };
})();

window.Avatar3D = Avatar3D;
