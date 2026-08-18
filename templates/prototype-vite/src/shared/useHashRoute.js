import { useEffect, useMemo, useState } from 'react';

function readLocation() {
  const hash = window.location.hash.replace(/^#/, '') || '/';
  const separator = hash.indexOf('?');
  const path = separator === -1 ? hash : hash.slice(0, separator);
  const search = separator === -1 ? '' : hash.slice(separator + 1);
  return { hash, path: path || '/', search };
}

// 极简 Hash 路由：本地预览与静态托管共用同一套可分享地址，不依赖服务端重写
export function useHashRoute(routes) {
  const [location, setLocation] = useState(readLocation);
  useEffect(() => {
    const onHashChange = () => setLocation(readLocation());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);
  const { path, search } = location;
  const query = useMemo(() => new URLSearchParams(search), [search]);
  const route =
    routes.find((item) => item.path === path) ||
    routes.find((item) => item.path === '*') || {
      path,
      title: '页面不存在',
      component: null,
    };
  return { path, query, route };
}

export function navigate(path) {
  const nextHash = path.startsWith('#') ? path : '#' + path;
  if (window.location.hash === nextHash) return;
  window.location.hash = nextHash;
}
