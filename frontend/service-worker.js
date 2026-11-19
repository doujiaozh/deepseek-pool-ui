const CACHE_NAME = 'ds-pool-v1';
const urlsToCache = [
  '/',
  '/index.html'
];
// ... 后续安装、激活、fetch事件的代码可以后续再完善
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});