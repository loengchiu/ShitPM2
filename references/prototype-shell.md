# Prototype Vite SPA shell 写法

> 本文件只在生成多页面 Prototype、创建或替换共享 shell，或修复路由、导航激活、共享布局和空白页问题时读取。
> 单页面原型和普通局部样式修改不需要读取本文件。

## 目录

- [核心原则](#核心原则)
- [标准结构](#标准结构)
- [路由注册与菜单](#路由注册与菜单)
- [正确实现模板](#正确实现模板)
- [禁止的反模式](#禁止的反模式)

## 核心原则

1. **shell 定义路由 + 渲染容器**，不持有页面业务数据
2. **每个页面是一个独立的 React 函数组件**，放在 `src/modules/<模块>/`，与 Design 模块一一对应
3. 页面切换用 Hash 路由；`src/routes.jsx` 是唯一路由注册表，菜单从注册表派生（module/group/icon 字段）
4. **禁止**把页面状态塞进 shell（如把列表数据、表单值放壳层组件里）
5. 只有 dist 没有 src、或路由/页面只能在构建产物中找到时，停止并报告源码工程缺失，不直接改 dist
6. **三栏布局（项目组约定）**：顶栏通栏 = 品牌区 + 主模块 Tab + 用户区；侧栏 = 当前主模块一二级菜单；内容区上方 = 可关闭页面标签条（替代面包屑/标题）。三栏全部 fixed 钉住，只有内容区随 body 滚动
7. 多角色项目角色切换统一放顶栏用户区（Select，角色用全称如"被审单位对接人"），页内不放"演示角色切换"；角色不满足的操作不渲染，状态不允许的置灰禁用

## 标准结构

```text
output/prototype/src/
├─ main.jsx            挂载入口（ConfigProvider + Claude 主题 + App）
├─ App.jsx             壳层：顶栏 + 侧栏 + 标签页栏 + Content（详见下方模板）
├─ routes.jsx          路由注册表（path → 组件，module/group/icon/menu）
├─ theme/claudeTheme.ts  Claude 主题 token（颜色/圆角/组件级）
├─ shared/
│  ├─ useHashRoute.js  极简 Hash 路由（useState + hashchange）
│  ├─ ui/DetailList.jsx  详情列表（17:33 列宽封装）
│  ├─ ui/PageFooter.jsx  内页底部版权
│  └─ NotFound.jsx     `*` 兜底异常页
├─ modules/<模块>/     业务页面组件（按 Design 模块组织）
└─ styles/global.css   全局样式（三栏布局、操作栏、标签栏等）
```

路由使用 Hash 模式（`/#/plan/list`）：本地开发预览与静态托管共用同一套可分享地址，不依赖服务端重写规则。页面数量由路由和模块组件表达，不由 HTML 文件数量表达；默认只有一个 `index.html`。

## 路由注册与菜单

1. 每个 Design 页面对应一个明确路由组件，在 `routes.jsx` 登记
2. 路由字段：`path`（Hash 路径）、`title`（页面标题/标签/菜单名）、`component`、`menu`（是否进侧栏）、`module`（所属主模块，顶栏 Tab 聚合源；`null` 表示不属任何模块，如首页）、`group`（侧栏二级分组，可选）、`icon`（侧栏菜单图标，antd icon 组件）、`placeholder`（占位页文案，可选）
3. 业务模块按 Design 模块组织目录：`src/modules/plan/`、`src/modules/project/` 等
4. 共享壳层、异常页放在 `src/shared/`；共享 UI 组件放 `src/shared/ui/`
5. 带参数的详情页路径（如 `/plan/detail/12`）由页面组件自行解析 hash，或拆成不带参数的页面状态切换；模板不引入路由参数解析库
6. **标签页栏**：App.jsx 维护 `tabs` 状态（初始含首页，首页常驻不可关）；hash 变化时新页面加入标签条；关闭激活标签时激活左邻

## 正确实现模板

`src/routes.jsx`（路由注册表，含主模块/分组/图标）：

```jsx
import { MoneyCollectOutlined, ScheduleOutlined } from '@ant-design/icons';
import Home from './modules/home/Home.jsx';
import PlanList from './modules/plan/PlanList.jsx';
import PlanDetail from './modules/plan/PlanDetail.jsx';
import NotFound from './shared/NotFound.jsx';

export const routes = [
  { path: '/', title: '首页', component: Home, menu: true, module: null, pinned: true },
  { path: '/plan/list', title: '年度计划', component: PlanList, menu: true, module: '计划管理', icon: <MoneyCollectOutlined /> },
  { path: '/plan/exec', title: '计划执行', component: PlanExec, menu: true, module: '计划管理', group: '执行管理', icon: <ScheduleOutlined /> },
  // menu: false 的页面不出现在侧栏，只能通过链接/按钮进入（内页）
  { path: '/plan/detail', title: '计划详情', component: PlanDetail, menu: false },
  { path: '*', title: '页面不存在', component: NotFound, menu: false },
];
```

`src/App.jsx`（壳层：顶栏三段式 + 侧栏子菜单 + 标签页栏 + 内容区；三栏 fixed 钉住，body 自然滚动）：

```jsx
import { useEffect, useMemo, useState } from 'react';
import { Avatar, Layout, Menu, Space, Tabs } from 'antd';
import { routes, groupIcons, moduleIcons } from './routes.jsx';
import { navigate, useHashRoute } from './shared/useHashRoute.js';

const { Header, Sider } = Layout;

// 主模块聚合（module 为 null 的不算主模块）
const moduleList = [];
routes.forEach((r) => {
  if (r.menu && r.module && !moduleList.some((m) => m.key === r.module)) {
    moduleList.push({ key: r.module, title: r.module, icon: moduleIcons[r.module] });
  }
});
const HOME_TAB = { key: '/', title: '首页' };

// 侧栏菜单：按 group 聚合为两级；无 group 的平铺
function buildMenuItems(module) {
  const items = [];
  routes.filter((r) => r.menu && r.module === module).forEach((r) => {
    if (r.group) {
      let sub = items.find((i) => i.key === r.group);
      if (!sub) { sub = { key: r.group, label: r.group, icon: groupIcons[r.group], children: [] }; items.push(sub); }
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
      if (key === path && next.length) navigate(next[Math.max(0, idx - 1)].key);
      return next;
    });
  };
  const menuItems = buildMenuItems(activeModule);
  const Page = activeRoute.component;
  return (
    <>
      {/* 顶栏通栏：fixed */}
      <Header className="app-header" style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100 }}>
        <div className="brand"><img src="/logo.png" alt="logo" className="brand-logo" /><span>{'系统名'}</span></div>
        <div className="module-tabs">
          {moduleList.map((m) => (
            <button key={m.key} type="button"
              className={`module-tab${m.key === activeModule ? ' active' : ''}`}
              onClick={() => switchModule(m)}>{m.icon}<span>{m.title}</span></button>
          ))}
        </div>
        <Space><Avatar style={{ background: '#cc785c' }}>示</Avatar><span>演示用户</span></Space>
      </Header>
      {/* 侧栏：fixed，当前主模块一二级菜单 */}
      <Sider width={220} style={{ position: 'fixed', top: 56, left: 0, bottom: 0, overflow: 'hidden',
        background: '#faf9f5', borderRight: '1px solid #e6dfd8', zIndex: 90 }}>
        <Menu mode="inline" selectedKeys={[path]} items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderInlineEnd: 'none', background: 'transparent', height: '100%', overflow: 'hidden' }} />
      </Sider>
      {/* 标签页栏：fixed */}
      <div className="page-tabs-bar" style={{ position: 'fixed', top: 56, left: 220, right: 0, zIndex: 95 }}>
        <Tabs type="editable-card" hideAdd size="small" activeKey={path} onChange={navigate}
          onEdit={(key, action) => { if (action === 'remove') closeTab(key); }}
          items={tabs.map((t) => ({ key: t.key, label: t.title, closable: t.key !== '/' }))} />
      </div>
      {/* 内容区：body 自然滚动；page-action-bar sticky 贴视口底 */}
      <main className="content-wrap">
        <div className="page-content"><Page /></div>
      </main>
    </>
  );
}
```

页面组件只负责业务页面，不重复写壳层；内页（详情/表单）加显式标题 + 右上返回 + 底部操作栏 + 版权（`PageFooter`），默认页不加标题（标签条替代）：

```jsx
export default function PlanDetail() {
  return (
    <div>
      {/* 内页标题 + 返回（右上角） */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>计划详情</Typography.Title>
        <Button icon={<ArrowLeftOutlined />}>返回</Button>
      </div>
      {/* 详情列表（一行两对 17:33） */}
      <DetailList title="基本信息" items={[...]} variant="pair" />
      {/* 版权（内容最底部一行，操作栏之前） */}
      <PageFooter />
      {/* 页面级操作栏：底部通栏贴底 */}
      <div className="page-action-bar">
        <Button icon={<EditOutlined />}>编辑</Button>
        <Button type="primary" icon={<SendOutlined />}>提交</Button>
      </div>
    </div>
  );
}
```

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

// ❌ 错误 5：侧栏/顶栏用 antd Layout 的嵌套滚动容器（overflow auto + sticky 混合）
// 三栏必须 fixed 钉住，只有 body 滚动；否则操作栏 sticky 会被内层滚动容器困住，滚到底向上跳

// ❌ 错误 6：内容区设 padding-bottom 或用 labelStyle/contentStyle 调详情列宽
// padding-bottom 会让操作栏滚动到底上跳；列宽用 CSS table-layout:fixed + td 17%/33%（见 prototype-writing.md）
```
