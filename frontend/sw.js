// Service Worker VivaLeve v5.0 - Ultra-Rapido (0ms Instant Load) & 100% Offline-First
const CACHE_NAME = 'vivaleve-cache-v5.0';

const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/vendor/tailwind.js',
    '/static/vendor/chart.min.js',
    '/static/vendor/qrcode.min.js',
    '/static/js/onboarding.js',
    '/static/js/auth.js',
    '/static/js/streak.js',
    '/static/js/family_battle.js',
    '/static/js/meal_assistant.js',
    '/static/js/app.js',
    '/static/js/diary.js',
    '/static/js/scanner.js',
    '/static/js/cheat_day.js',
    '/static/js/restaurants.js',
    '/static/js/profile_charts.js',
    '/static/manifest.json',
    '/static/icon.svg'
];

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('Pre-cache de assets finalizado com avisos:', err);
            });
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((k) => {
                    if (k !== CACHE_NAME) {
                        console.log('Removendo cache antigo:', k);
                        return caches.delete(k);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const req = event.request;
    const url = new URL(req.url);

    // 1. APIs de Leitura (GET /api/...): Network-First com Fallback Automatico para Cache
    if (req.method === 'GET' && url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(req)
                .then((networkRes) => {
                    if (networkRes && networkRes.status === 200) {
                        const clone = networkRes.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
                        return networkRes;
                    }
                    // Se o servidor retornar erro transitorio (500, 502, 503, 530), tenta o cache local
                    return caches.match(req).then((cached) => cached || networkRes);
                })
                .catch(() => {
                    // Sem sinal / offline: entrega a versao salva em cache
                    return caches.match(req).then((cachedRes) => {
                        if (cachedRes) return cachedRes;
                        return new Response(JSON.stringify({ offline: true, detail: "Dados offline em memoria local" }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    });
                })
        );
        return;
    }

    // Nao interceptar requisicoes que nao sejam GET (POST, PUT, DELETE vao para a rede/fila)
    if (req.method !== 'GET') {
        return;
    }

    // 2. Navegacao HTML (pagina principal): Instant Load (0ms) com Stale-While-Revalidate
    if (req.mode === 'navigate' || url.pathname === '/') {
        event.respondWith(
            caches.match('/').then((cached) => {
                // Background revalidation: busca versao atualizada sem travar o usuario
                const networkFetch = fetch(req)
                    .then((networkRes) => {
                        if (networkRes && networkRes.status === 200) {
                            const clone = networkRes.clone();
                            caches.open(CACHE_NAME).then((c) => c.put('/', clone));
                            return networkRes;
                        }
                        // Se for erro da Cloudflare (530/502/503), mantem a tela do cache
                        return cached || networkRes;
                    })
                    .catch(() => cached || new Response('Offline', { status: 503 }));

                // Se ja estiver no cache, abre INSTANTANEAMENTE (0ms)!
                // Se for a primeira visita do aparelho, aguarda o download inicial.
                return cached || networkFetch;
            })
        );
        return;
    }

    // 3. Assets estaticos (JS, CSS, Imagens, Fontes, Icones): Cache-First Imediato
    event.respondWith(
        caches.match(req).then((cachedRes) => {
            if (cachedRes) {
                // Revalidacao assincrona silenciosa em segundo plano
                fetch(req).then((networkRes) => {
                    if (networkRes && networkRes.status === 200) {
                        const clone = networkRes.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
                    }
                }).catch(() => {});
                return cachedRes;
            }

            return fetch(req).then((networkRes) => {
                if (networkRes && networkRes.status === 200) {
                    const clone = networkRes.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
                }
                return networkRes;
            }).catch(() => cachedRes);
        })
    );
});
