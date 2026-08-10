# Prototype 多页面 shell 写法

> 本文件只在生成多页面 Prototype、创建或替换共享 shell，或修复路由、导航激活、共享布局和空白页问题时读取。
> 单页面原型和普通局部样式修改不需要读取本文件。

## 目录

- [多页面 shell 写法模板](#多页面-shell-写法模板)
  - [核心原则](#核心原则)
  - [正确实现模板（单文件版本，多页可拆分）](#正确实现模板单文件版本多页可拆分)
  - [多文件拆分版本](#多文件拆分版本)
  - [禁止的反模式](#禁止的反模式)

## 多页面 shell 写法模板

> 历史教训：曾经自造 `createShellApp`，把页面传入的 `extraData` 直接展开到 `data()` 返回对象里，导致 Vue 选项被当作响应式数据属性，页面挂载时报错，全部空白。该框架已废弃。
>
> 当前架构为 **React 18 + Ant Design 6**（无构建、本地 UMD）。本节给出正确模板，必须复用，不得自造 shell 框架。

### 核心原则

1. **shell 定义路由 + 渲染容器**，不持有页面业务数据
2. **每个页面是一个独立的 React 函数组件**（`function PageXxx() { return (...) }`）
3. 页面切换用 `useState` 保存当前页 key，`PAGES` 对象做 key → 组件映射
4. **禁止**把页面状态塞进 shell（如把列表数据、表单值放壳层组件里）

### 正确实现模板（单文件版本，多页可拆分）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <link rel="stylesheet" href="lib/react-antd/reset.css" />
  <link rel="stylesheet" href="lib/react-antd/antd.css" />
</head>
<body>
  <div id="root"></div>
  <!-- 八件套引用顺序不可变：react → react-dom → dayjs → locale → antd → babel -->
  <script src="lib/react-antd/react.production.min.js"></script>
  <script src="lib/react-antd/react-dom.production.min.js"></script>
  <script src="lib/react-antd/dayjs.min.js"></script>
  <script src="lib/react-antd/locale-zh-cn.js"></script>
  <script src="lib/react-antd/antd-with-locales.min.js"></script>
  <script src="lib/react-antd/babel.min.js"></script>

  <script type="text/babel" data-presets="react">
    const { useState } = React;
    const { Layout, Menu, Table, Tag, Form, Input, Button, Space, Card, Divider } = window.antd;
    const { Sider, Header, Content } = Layout;

    // 1. 定义每个页面为独立函数组件
    function PageList() {
      const columns = [
        { title: '标题', dataIndex: 'title' },
        { title: '状态', dataIndex: 'status', width: 120,
          render: (v) => <Tag color={v === 'submitted' ? 'blue' : 'default'}>{v}</Tag> },
      ];
      const data = [{ key: 1, title: '第 1 周', status: 'submitted' }];
      return (
        <Card>
          <Table columns={columns} dataSource={data} pagination={false} size="middle" />
        </Card>
      );
    }

    function PageEdit() {
      return (
        <Card style={{ maxWidth: 720 }}>
          <Form layout="vertical">
            <Form.Item label="标题" name="title"><Input /></Form.Item>
            <Form.Item label="内容" name="content"><Input.TextArea rows={6} /></Form.Item>
            <Button type="primary" htmlType="submit">提交</Button>
          </Form>
        </Card>
      );
    }

    // 2. 页面注册表（key → 组件）
    const PAGES = {
      list: PageList,
      edit: PageEdit,
    };

    // 3. shell：只管当前页 + 导航
    function App() {
      const [current, setCurrent] = useState('list');
      const Page = PAGES[current] || PageList;
      const menuItems = Object.keys(PAGES).map((key) => ({
        key,
        label: key === 'list' ? '列表' : '编辑',
      }));
      return (
        <Layout style={{ height: '100%' }}>
          <Sider theme="dark" width={220}>
            <Menu theme="dark" mode="inline" selectedKeys={[current]}
              onClick={({ key }) => setCurrent(key)} items={menuItems} />
          </Sider>
          <Layout>
            <Content style={{ padding: 24, background: '#f5f5f5' }}>
              <Page />
            </Content>
          </Layout>
        </Layout>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
```

### 多文件拆分版本

页面较多时，把每个页面组件抽到独立 JS 文件：

```
output/prototype/
  index.html         # shell + 路由
  pages/
    page-list.js     # window.SPM_PAGES.PageList = function PageList() {...}
    page-edit.js
```

index.html 引入顺序：

```html
<script src="lib/react-antd/react.production.min.js"></script>
<script src="lib/react-antd/react-dom.production.min.js"></script>
<script src="lib/react-antd/dayjs.min.js"></script>
<script src="lib/react-antd/locale-zh-cn.js"></script>
<script src="lib/react-antd/antd-with-locales.min.js"></script>
<script src="lib/react-antd/babel.min.js"></script>
<script src="pages/page-list.js"></script>
<script src="pages/page-edit.js"></script>
<script type="text/babel" data-presets="react">
  const PAGES = {
    'PageList': window.SPM_PAGES.PageList,
    'PageEdit': window.SPM_PAGES.PageEdit,
  };
  // ... 其余同上
  ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
```

page-list.js 内容：

```javascript
window.SPM_PAGES = window.SPM_PAGES || {};
window.SPM_PAGES.PageList = function PageList() {
  return (/* JSX 或 React.createElement */);
};
```

注意：独立 JS 文件如果含 JSX，必须以 `.jsx` 或由主页面 `<script type="text/babel">` 再编译；最稳的做法是把页面组件全部写在 index.html 的 text/babel 块里，或给独立文件也用 babel 处理。业务简单时优先单文件。

### 禁止的反模式

```javascript
// ❌ 错误 1：把页面状态塞进 shell（列表数据、表单值属于页面组件）
function App() {
  const [list, setList] = useState([]);      // 这是 PageList 的数据
  const [form, setForm] = useState({});      // 这是 PageEdit 的数据
  // shell 不应持有任何页面业务状态
}

// ❌ 错误 2：在 shell 里写死页面渲染逻辑而不是用 PAGES 映射
function App() {
  // if (current === 'list') return <PageList />;
  // else return <PageEdit />;   // 页面一多就无法维护
}

// ❌ 错误 3：自造 createShellApp 之类的框架函数封装上述反模式
// 任何 shell 都必须按本节模板的"独立函数组件 + PAGES 映射 + <Page />"方式实现
```
