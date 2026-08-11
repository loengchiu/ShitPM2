import { Avatar, Breadcrumb, Layout, Menu, Space } from 'antd';
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
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={220}>
        <div className="sider-logo">{'原型系统' /* 生成时替换为项目名 */}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[path]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="header-bar">
          <Breadcrumb items={[{ title: route.title }]} />
          <Space>
            <Avatar style={{ background: '#1677ff' }}>{'示'}</Avatar>
            <span>{'演示用户'}</span>
          </Space>
        </Header>
        <Content className="content-wrap">
          <Page />
        </Content>
      </Layout>
    </Layout>
  );
}
