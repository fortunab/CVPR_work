// The anonymous website renderer and repository browser have different sandbox
// permissions. Open downloadable materials in the anonymous file browser.
(function () {
  'use strict';
  const match = window.location.pathname.match(/^\/w\/([^/]+)(?:\/|$)/);
  if (!match) return;
  const directory = document.documentElement.dataset.anonymousSourceDirectory || '';
  const base = '/r/' + encodeURIComponent(decodeURIComponent(match[1])) + '/' +
    (directory ? directory.replace(/^\/+|\/+$/g, '') + '/' : '');
  window.CBMP_ANONYMOUS_FILE_BASE = base;
  document.querySelectorAll('a[href^="downloads/"]').forEach(function (link) {
    link.setAttribute('href', base + link.getAttribute('href'));
    link.removeAttribute('download');
    link.removeAttribute('target');
  });
})();
