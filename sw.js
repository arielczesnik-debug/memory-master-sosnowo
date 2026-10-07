const CACHE = 'mm22-sosnowo-v1';
const ASSETS = ['./','./index.html','./manifest.webmanifest','./sw.js','./assets/logo-szkoly.png','./assets/mini-me.png','./INSTRUKCJA_GITHUB_PAGES.txt'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS))));
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
    const copy = resp.clone();
    caches.open(CACHE).then(c => c.put(e.request, copy)).catch(()=>{});
    return resp;
  }).catch(() => caches.match('./index.html'))));
});
