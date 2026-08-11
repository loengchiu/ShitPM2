import { useEffect, useState } from 'react';

function readPath() {
  const hash = window.location.hash.replace(/^#/, '');
  return hash || '/';
}

// 极简 Hash 路由：本地预览与静态托管共用同一套可分享地址，不依赖服务端重写
export function useHashRoute(routes) {
  const [path, setPath] = useState(readPath);
  useEffect(() => {
    const onHashChange = () => setPath(readPath());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);
  const route =
    routes.find((item) => item.path === path) ||
    routes.find((item) => item.path === '*') || {
      path,
      title: '页面不存在',
      component: null,
    };
  return { path, route };
}

export function navigate(path) {
  if (window.location.hash === `#${path}`) return;
  window.location.hash = path;
}
