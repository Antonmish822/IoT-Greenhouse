/**
 * Глобальная конфигурация API для фронтенда Умной теплицы.
 * Хосты можно переопределить до загрузки этого файла, например:
 * window.SG_API = { hosts: { backend: 'https://api.example.com' } };
 */
window.SG_API = window.SG_API || {};
window.SG_API.hosts = window.SG_API.hosts || {};
window.SG_API.hosts.backend = window.SG_API.hosts.backend || 'http://127.0.0.1:8001';
window.SG_API.baseUrl = window.SG_API.baseUrl || window.SG_API.hosts.backend;

window.SG_API.buildUrl = window.SG_API.buildUrl || function (path = '') {
  const base = (window.SG_API.hosts?.backend || window.SG_API.baseUrl || '').replace(/\/+$/, '');

  if (!path) {
    return base;
  }

  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
};

window.SG_API.fetch = window.SG_API.fetch || function(path = '', options = {}) {
  const url = window.SG_API.buildUrl(path);
  return fetch(url, options);
};
