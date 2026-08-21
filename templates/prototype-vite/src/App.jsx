import { useEffect, useMemo, useState } from 'react';
import { Avatar, Layout, Menu, Space, Tabs } from 'antd';
import { routes, groupIcons, moduleIcons } from './routes.jsx';
import { navigate, useHashRoute } from './shared/useHashRoute.js';

const { Header, Sider } = Layout;

// 主模块聚合（保持路由注册顺序；module 为 null 的不算主模块）
const moduleList = [];
routes.forEach((r) => {
  if (r.menu && r.module && !moduleList.some((m) => m.key === r.module)) {
    moduleList.push({ key: r.module, title: r.module, icon: moduleIcons[r.module] });
  }
});

const HOME_TAB = { key: '/', title: '首页' };

function buildMenuItems(module) {
  const items = [];
  routes
    .filter((r) => r.menu && r.module === module)
    .forEach((r) => {
      if (r.group) {
        let sub = items.find((i) => i.key === r.group);
        if (!sub) {
          sub = { key: r.group, label: r.group, icon: groupIcons[r.group], children: [] };
          items.push(sub);
        }
        sub.children.push({ key: r.path, label: r.title, icon: r.icon });
      } else {
        items.push({ key: r.path, label: r.title, icon: r.icon });
      }
    });
  return items;
}

export default function App() {
  const { path } = useHashRoute(routes);
  const [activeModule, setActiveModule] = useState(moduleList[0]);
  const [tabs, setTabs] = useState([HOME_TAB]);

  const activeRoute = useMemo(
    () => routes.find((r) => r.path === path) || routes.find((r) => r.path === '*'),
    [path],
  );

  useEffect(() => {
    if (activeRoute && !activeRoute.pinned && !tabs.some((t) => t.key === path)) {
      setTabs((prev) => [...prev, { key: path, title: activeRoute.title }]);
    }
  }, [path, activeRoute, tabs]);

  const switchModule = (m) => {
    setActiveModule(m.key);
    const first = routes.find((r) => r.menu && r.module === m.key);
    if (first) navigate(first.path);
  };

  const closeTab = (key) => {
    if (key === '/') return;
    setTabs((prev) => {
      const idx = prev.findIndex((t) => t.key === key);
      const next = prev.filter((t) => t.key !== key);
      if (key === path && next.length) {
        const neighbor = next[Math.max(0, idx - 1)];
        navigate(neighbor.key);
      }
      return next;
    });
  };

  const menuItems = buildMenuItems(activeModule);
  const Page = activeRoute.component;

  return (
    <>
      <Header className="app-header" style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100 }}>
        <div className="brand">
          <img src="/logo.png" alt="logo" className="brand-logo" />
          <span>{'原型系统'}</span>
        </div>
        <div className="module-tabs">
          {moduleList.map((m) => (
            <button
              key={m.key}
              type="button"
              className={`module-tab${m.key === activeModule ? ' active' : ''}`}
              onClick={() => switchModule(m)}
            >
              {m.icon}
              <span>{m.title}</span>
            </button>
          ))}
        </div>
        <Space className="user-info">
          <Avatar style={{ background: 'var(--avatar-bg)' }}>{'示'}</Avatar>
          <span>{'演示用户'}</span>
        </Space>
      </Header>
      <Sider
        width={220}
        style={{
          position: 'fixed',
          top: 56,
          left: 0,
          bottom: 0,
          overflow: 'hidden',
          background: 'var(--layout-bg)',
          borderRight: '1px solid var(--border)',
          zIndex: 90,
        }}
      >
        <Menu
          mode="inline"
          selectedKeys={[path]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderInlineEnd: 'none', background: 'transparent', height: '100%', overflow: 'hidden' }}
        />
      </Sider>
      <div className="page-tabs-bar" style={{ position: 'fixed', top: 56, left: 220, right: 0, zIndex: 95 }}>
        <Tabs
          type="editable-card"
          hideAdd
          size="small"
          activeKey={path}
          onChange={navigate}
          onEdit={(key, action) => {
            if (action === 'remove') closeTab(key);
          }}
          items={tabs.map((t) => ({ key: t.key, label: t.title, closable: t.key !== '/' }))}
        />
      </div>
      <main className="content-wrap">
        <div className="page-content">
          <Page {...(activeRoute.placeholder ? { placeholder: activeRoute.placeholder } : {})} />
        </div>
      </main>
    </>
  );
}
