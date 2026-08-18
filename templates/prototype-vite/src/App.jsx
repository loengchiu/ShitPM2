import { useState } from 'react';
import { Avatar, Button, Layout, Menu, Space } from 'antd';
import { IconMenu2, IconSearch, IconX } from '@tabler/icons-react';
import { routes } from './routes.jsx';
import { navigate, useHashRoute } from './shared/useHashRoute.js';

const { Header, Sider, Content } = Layout;

// 侧栏菜单从路由注册表派生；业务页面不在这里登记
const menuItems = routes
  .filter((item) => item.menu)
  .map((item) => ({ key: item.path, label: item.title }));

export default function App() {
  const { path, route } = useHashRoute(routes);
  const Page = route.component;
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 深色 Sider：只承载菜单，独立滚动；lg 断点以下自动折叠 */}
      <Sider
        className="app-sider"
        theme="dark"
        width={200}
        collapsedWidth={0}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        breakpoint="lg"
        style={{ height: '100vh', position: 'sticky', top: 0 }}
      >
        <div className="sider-menu-scroll">
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[path]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
          />
        </div>
      </Sider>
      <Layout>
        {/* 顶栏：LOGO + 搜索 + 用户区同一行（对齐 Tabler 顶栏） */}
        <Header className="header-bar">
          <div className="header-brand">
            <Button
              type="text"
              aria-label="展开或收起侧栏"
              icon={<IconMenu2 size={18} />}
              onClick={() => setCollapsed((v) => !v)}
            />
            <span className="header-logo">{'原型系统' /* 生成时替换为项目名 */}</span>
          </div>
          <div className="header-search">
            <IconSearch size={16} className="header-search-icon" />
            <input className="header-search-input" placeholder="搜索…" aria-label="搜索" />
          </div>
          <div className="header-user">
            <Space size={8}>
              <Avatar style={{ background: 'var(--spm-color-primary)' }}>{'示'}</Avatar>
              <span className="header-user-name">{'演示用户'}</span>
            </Space>
          </div>
        </Header>
        {/* 页签栏：不设页面大标题，用带关闭按钮的页签表达当前页面 */}
        <div className="tab-bar" role="tablist" aria-label="当前页面">
          <div className="tab tab-active" role="tab" aria-selected="true">
            <span className="tab-title">{route.title}</span>
            <button
              type="button"
              className="tab-close"
              aria-label="关闭页签"
              onClick={() => navigate('/')}
            >
              <IconX size={14} />
            </button>
          </div>
        </div>
        <Content className="content-wrap">
          <Page />
        </Content>
      </Layout>
    </Layout>
  );
}
