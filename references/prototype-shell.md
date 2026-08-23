# Prototype Vite SPA shell 写法

> 本文件只在生成多页面 Prototype、创建或替换共享 shell，或修复路由、导航激活、共享布局和空白页问题时读取。
> 单页面原型和普通局部样式修改不需要读取本文件。

## 目录

- [核心原则](#核心原则)
- [标准结构](#标准结构)
- [正确实现模板](#正确实现模板)
- [路由注册与菜单](#路由注册与菜单)
- [禁止的反模式](#禁止的反模式)

## 核心原则

1. **shell 定义路由 + 渲染容器**，不持有页面业务数据
2. **每个页面是一个独立的 React 函数组件**，放在 `src/modules/<模块>/`，与 Design 模块一一对应
3. 页面切换用 Hash 路由；`src/routes.jsx` 是唯一路由注册表，菜单从注册表派生
4. **禁止**把页面状态塞进 shell（如把列表数据、表单值放壳层组件里）
5. 只有 dist 没有 src、或路由/页面只能在构建产物中找到时，停止并报告源码工程缺失，不直接改 dist
6. 多角色项目角色切换统一放壳层 Header（Select，角色用全称如"被审单位对接人"），页内不放"演示角色切换"；角色不满足的操作不渲染，状态不允许的置灰禁用

## 标准结构

```text
output/prototype/src/
├─ main.jsx            挂载入口（ConfigProvider + App）
├─ App.jsx             壳层：Sider 菜单 + Header + Content 渲染当前路由组件
├─ routes.jsx          路由注册表（path → 组件，menu 决定是否进侧栏）
├─ shared/
│  ├─ useHashRoute.js  极简 Hash 路由（useState + hashchange）
│  └─ NotFound.jsx     `*` 兜底异常页
├─ modules/<模块>/     业务页面组件（按 Design 模块组织）
└─ styles/global.css   全局样式（壳层布局、page-head 等）
```

路由使用 Hash 模式（`/#/plan/list`）：本地开发预览与静态托管（Cloudflare Pages）共用同一套可分享地址，不依赖服务端重写规则。页面数量由路由和模块组件表达，不由 HTML 文件数量表达；默认只有一个 `index.html`。

## 正确实现模板

`src/routes.jsx`（路由注册表）：

```jsx
import Home from './modules/home/Home.jsx';
import NotFound from './shared/NotFound.jsx';

export const routes = [
  { path: '/', title: '首页', component: Home, menu: true },
  { path: '/plan/list', title: '年度计划', component: PlanList, menu: true },
  // menu: false 的页面不出现在侧栏，只能通过链接/按钮进入；对象 ID 放 query
  { path: '/plan/detail', title: '计划详情', component: PlanDetail, menu: false },
  { path: '*', title: '页面不存在', component: NotFound, menu: false },
];
```

`src/shared/useHashRoute.js`（极简 Hash 路由，不引入 react-router）：

```js
import { useEffect, useState } from 'react';

function readLocation() {
  const hash = window.location.hash.replace(/^#/, '');
  const separator = hash.indexOf('?');
  return {
    path: (separator === -1 ? hash : hash.slice(0, separator)) || '/',
    search: separator === -1 ? '' : hash.slice(separator + 1),
  };
}

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
```

`src/App.jsx`（壳层：只管路由 + 导航，不持有页面业务数据）：

```jsx
import { Avatar, Breadcrumb, Layout, Menu, Space } from 'antd';
import { routes } from './routes.jsx';
import { navigate, useHashRoute } from './shared/useHashRoute.js';

const { Header, Sider, Content } = Layout;

const menuItems = routes
  .filter((item) => item.menu)
  .map((item) => ({ key: item.path, label: item.title }));

export default function App() {
  const { path, route } = useHashRoute(routes);
  const Page = route.component;
  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Sider 独立滚动：菜单长时只在侧栏内部滚动，不随整页滚动 */}
      <Sider theme="dark" width={200} style={{ height: '100vh', overflow: 'auto', position: 'sticky', top: 0 }}>
        <div className="sider-logo">项目名</div>
        <Menu theme="dark" mode="inline" selectedKeys={[path]}
          items={menuItems} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header className="header-bar">
          <Breadcrumb items={[{ title: route.title }]} />
          <Space>
            {/* 多角色项目：角色切换 Select 统一放这里，页内不放 */}
            <Avatar style={{ background: 'var(--spm-color-primary)' }}>示</Avatar><span>演示用户</span>
          </Space>
        </Header>
        <Content className="content-wrap">
          <Page />
        </Content>
      </Layout>
    </Layout>
  );
}
```

页面组件只负责业务页面，不重复写壳层：

```jsx
export default function PlanList() {
  const columns = [
    { title: '计划名称', dataIndex: 'name' },
    { title: '状态', dataIndex: 'status', width: 120,
      render: (v) => <Tag color={v === '已通过' ? 'green' : 'orange'}>{v}</Tag> },
  ];
  const data = [{ key: 1, name: '2026 年度审计计划', status: '已通过' }];
  return (
    <Card>
      <Table columns={columns} dataSource={data} pagination={false} size="middle" />
    </Card>
  );
}
```

## 路由注册与菜单

1. 每个 Design 页面对应一个明确路由组件，在 `routes.jsx` 登记
2. 业务模块按 Design 模块组织目录：`src/modules/plan/`、`src/modules/project/` 等
3. 共享壳层、角色切换、异常页放在 `src/shared/`
4. 菜单从路由配置派生（`menu: true`）或与路由做显式映射，不在 App.jsx 里再写一份菜单数据
5. 带参数的详情页使用 query（如 `#/plan/detail?id=12`）；极简路由只做精确 path 匹配，不声称支持冒号形式的动态参数。页面通过 `URLSearchParams` 读取 query；同一路径 query 变化必须触发更新，`navigate()` 接受带 query 的 Hash 相对地址且不重复添加 `#`。

## 禁止的反模式

```jsx
// ❌ 错误 1：把页面状态塞进 shell（列表数据、表单值属于页面组件）
function App() {
  const [list, setList] = useState([]);      // 这是 PlanList 的数据
  const [form, setForm] = useState({});      // 这是 PlanEdit 的数据
  // shell 不应持有任何页面业务状态
}

// ❌ 错误 2：在 shell 里写死页面渲染逻辑而不是用路由注册表
function App() {
  // if (path === '/plan/list') return <PlanList />;
  // else return <PlanEdit />;   // 页面一多就无法维护
}

// ❌ 错误 3：自造 createShellApp 之类的框架函数封装上述反模式
// 任何 shell 都必须按本节模板的"独立函数组件 + routes.jsx 注册 + <Page />"方式实现

// ❌ 错误 4：用多个 HTML 文件做路由，或直接编辑 dist/ 里的构建产物
// 页面数量由路由表达；修改只发生在 src/，dist 由 npm run build 重建
```
