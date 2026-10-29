// يخزّن غلاف الصفحة وقائمة الكلمات ليفتح بسرعة وبدون اتصال. بيانات GitHub (الحفظ والمزامنة) لا تمرّ من هنا أبداً.
const CACHE = 'gate-shell-v2';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png', 'data/words.json'];
self.addEventListener('install', e => {
  // نحمّل كل ملف على حدة حتى لا يفشل التثبيت كله إن غاب ملف واحد
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin) return;
  // الشبكة أولاً حتى تصل التحديثات فوراً، والنسخة المخزّنة عند انقطاع الاتصال
  e.respondWith(fetch(r).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(r, copy)); }
    return res;
  }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match('index.html'))));
});
