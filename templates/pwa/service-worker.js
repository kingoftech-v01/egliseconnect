const CACHE_NAME = 'egliseconnect-v2';
const OFFLINE_URL = '/offline/';

// Core resources to precache on install
const PRECACHE_URLS = [
    '/',
    '/offline/',
    '/static/w3crm/css/style.css',
];

// Key app pages to cache when visited (network-first with cache fallback)
const KEY_PAGES = [
    '/members/',
    '/events/',
    '/donations/',
    '/volunteers/',
    '/attendance/',
    '/reports/',
    '/communication/',
    '/help-requests/',
    '/onboarding/',
];

// Static assets to cache aggressively (cache-first strategy)
const STATIC_EXTENSIONS = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf'];

// Install - precache essential resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        }).catch(() => {
            // Ignore cache failures during install
        })
    );
    self.skipWaiting();
});

// Activate - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Helper: check if URL is a static asset
function isStaticAsset(url) {
    return STATIC_EXTENSIONS.some((ext) => url.pathname.endsWith(ext)) ||
           url.pathname.startsWith('/static/');
}

// Helper: check if URL is a key app page
function isKeyPage(url) {
    return KEY_PAGES.some((page) => url.pathname.startsWith(page));
}

// Fetch handler with strategy selection
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    const url = new URL(event.request.url);

    // Skip API, admin, and external requests
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) return;
    if (url.origin !== self.location.origin) return;

    // Strategy 1: Cache-first for static assets
    if (isStaticAsset(url)) {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                if (cached) return cached;
                return fetch(event.request).then((response) => {
                    if (response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, clone);
                        });
                    }
                    return response;
                }).catch(() => {
                    return new Response('', { status: 408 });
                });
            })
        );
        return;
    }

    // Strategy 2: Network-first for key pages and navigation
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Cache successful HTML responses for key pages
                if (response.status === 200) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, clone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Try cache, then offline page for navigation requests
                return caches.match(event.request).then((cached) => {
                    if (cached) return cached;
                    // Only show offline page for navigation requests (HTML pages)
                    if (event.request.mode === 'navigate') {
                        return caches.match(OFFLINE_URL);
                    }
                    return new Response('', { status: 408 });
                });
            })
    );
});

// Push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body || '',
        icon: '/static/w3crm/images/favicon.png',
        badge: '/static/w3crm/images/favicon.png',
        data: { url: data.url || '/' },
        vibrate: [200, 100, 200],
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'EgliseConnect', options)
    );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data.url || '/';
    event.waitUntil(
        clients.openWindow(url)
    );
});
