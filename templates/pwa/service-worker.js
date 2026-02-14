const CACHE_NAME = 'egliseconnect-v3';
const OFFLINE_URL = '/offline/';
const BACKGROUND_SYNC_TAG = 'egliseconnect-sync';

// Core resources to precache on install
const PRECACHE_URLS = [
    '/',
    '/offline/',
    '/static/w3crm/css/style.css',
    '/static/w3crm/js/notifications.js',
    '/static/w3crm/js/search-autocomplete.js',
];

// Key app pages to cache when visited (network-first with cache fallback)
const KEY_PAGES = [
    '/onboarding/dashboard/',
    '/members/my-profile/',
    '/attendance/my-qr/',
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
    const url = new URL(event.request.url);

    // Skip API, admin, and external requests for caching
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin/')) return;
    if (url.origin !== self.location.origin) return;

    // For non-GET requests, try network and queue for background sync if offline
    if (event.request.method !== 'GET') {
        if (event.request.method === 'POST') {
            event.respondWith(
                fetch(event.request.clone()).catch(() => {
                    // Queue for background sync
                    return savePostForSync(event.request.clone()).then(() => {
                        return new Response(JSON.stringify({
                            queued: true,
                            message: 'Votre soumission sera envoyee quand vous serez en ligne.'
                        }), {
                            status: 202,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    });
                })
            );
        }
        return;
    }

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

// ─── Background Sync ─────────────────────────────────────────────────────────

// Store for offline form submissions
const SYNC_STORE_NAME = 'egliseconnect-sync-queue';

async function savePostForSync(request) {
    try {
        const body = await request.text();
        const syncData = {
            url: request.url,
            method: request.method,
            headers: Object.fromEntries(request.headers.entries()),
            body: body,
            timestamp: Date.now(),
        };

        // Use IndexedDB-like storage via Cache API
        const cache = await caches.open(SYNC_STORE_NAME);
        const key = new Request('/_sync/' + Date.now());
        await cache.put(key, new Response(JSON.stringify(syncData)));

        // Register for background sync
        if (self.registration && self.registration.sync) {
            await self.registration.sync.register(BACKGROUND_SYNC_TAG);
        }
    } catch (e) {
        // Silently fail
    }
}

self.addEventListener('sync', (event) => {
    if (event.tag === BACKGROUND_SYNC_TAG) {
        event.waitUntil(replayQueuedRequests());
    }
});

async function replayQueuedRequests() {
    try {
        const cache = await caches.open(SYNC_STORE_NAME);
        const keys = await cache.keys();

        for (const key of keys) {
            try {
                const response = await cache.match(key);
                const syncData = await response.json();

                await fetch(syncData.url, {
                    method: syncData.method,
                    headers: syncData.headers,
                    body: syncData.body,
                    credentials: 'same-origin',
                });

                await cache.delete(key);
            } catch (e) {
                // Keep in queue for next sync attempt
            }
        }
    } catch (e) {
        // Silently fail
    }
}

// ─── Push Notifications ──────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body || '',
        icon: '/static/w3crm/images/favicon.png',
        badge: '/static/w3crm/images/favicon.png',
        data: { url: data.url || '/' },
        vibrate: [200, 100, 200],
        tag: data.tag || 'egliseconnect-notification',
        renotify: true,
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
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            // Focus existing window if available
            for (const client of windowClients) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            return clients.openWindow(url);
        })
    );
});
