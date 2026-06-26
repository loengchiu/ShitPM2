# 原型写法参考

> 本文件是原型阶段的示例和对照说明。
> 硬规则在 `skills/spm-prototype/SKILL.md`。

## 失败模式速查表

| 场景 | 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|---|
| 原型只有一个 HTML 无法维护 | 页面过多全塞在一个文件 | 按模块拆分 HTML 文件 | 若文件超过 5000 行，必须拆分 |
| 原型重新定义业务规则 | HTML 中包含独立于 design 的业务规则 | 检查原型中的业务规则是否与 design 一致 | 若不一致，回退到 fix 流程 |
| 原型拆分不当 | 按技术层拆而不是按业务模块 | 一个子系统一个 HTML 文件，index.html 做入口 | 若模块间有共享组件，提取到公共 JS |
| 表现问题被当成语义问题 | UI 布局问题被误判为业务错误 | 先归类：表现问题 vs 语义问题 | 表现问题只改 prototype，语义问题才回写 design |
| 未归类就开始修改 | 读完 feedback 后直接改 | 必须先输出归类结果，再开始修改 | 若无法归类，停在澄清，不直接改 |
| 原型依赖 lib/ 缺失 | `lib/` 目录下 vue/tailwind/daisyui 缺失 | 提示用户运行 `python scripts/python/download-prototype-libs.py` | 停下，不凭记忆生成 |
| 状态表达不完整 | 只有默认状态，缺异常/空/加载状态 | 按 design 状态定义逐个补入原型 | 若状态过多，先补核心状态，其余标注 [TODO] |
| 页面渲染空白 | createShellApp 选项合并错误 / lib 缺失 | 1) 检查四件套 lib 引用 2) 按 references 第七章模板重写 shell | 回滚到上一可工作版本 |
| 页面无样式 | HTML 缺 Tailwind/daisyUI 引用 | 给全部 HTML 补齐本地 lib/ 四件套引用 | —— |

## 反例黑名单（不要做的事）

| # | 反模式 | 为什么不要做 | 替代做法 |
|---|---|---|---|
| 1 | **把所有页面塞进一个 HTML** | 无法维护，打开很慢 | 按模块拆分，用 index.html 做入口 |
| 2 | **原型独立定义业务规则** | 与 design 不一致，造成混乱 | 原型只做展示，业务规则以 design 为准 |
| 3 | **跳过归类直接修改** | 表现问题和语义问题的传播路径完全不同 | 必须先归类再修改 |
| 4 | **表现问题回写 design** | 表现层反馈不应改变 design 业务定义 | 表现问题只改 prototype |
| 5 | **使用外部 CDN** | file:// 协议下加载失败 | 使用本地 lib/ 目录四件套 |
| 6 | **使用 Element Plus 组件（`el-xxx`）** | 已废弃，改用 daisyUI | 用 daisyUI 组件类（`btn`/`table`/`card` 等） |
| 7 | **自造 createShellApp 框架** | 选项合并易出 bug（曾导致全部页面空白） | 复用 references 第七章模板 |
| 8 | **把页面 extraData 展开到 shell 的 data()** | Vue 选项被当响应式数据，挂载报错 | 页面用独立组件 + `<component :is>` |

---


## 一、原型定位

- 原型与 PRD 平级，均以 design 为基线
- 原型只做展示，不重新定义业务规则
- 第一版走最小原型，不追求重型系统

## 二、通用后台基座

新的原型默认复用统一后台壳层，不再每个项目从空白 HTML 开始搭页框。

固定壳层包括：

1. **顶栏**
   - 高度固定
   - 承载项目名、当前模块名、全局操作入口、用户区
   - 不承载页面级业务规则
2. **左侧导航**
   - 用于模块和页面切换
   - 可分组
   - 当前项高亮
3. **页签区**
   - 位于主体区顶部白色条带内
   - 用于同模块下的子页面或同页多视图切换
   - 页签直接展示页面名称
   - 活动页签默认带关闭按钮
   - 只表达当前工作上下文
4. **主体工作区**
   - 承载查询区、操作区、表格区、表单区、详情区、统计卡片等真正业务内容
   - 上述内容块按页面主任务按需出现，不是每页都全量出现

版式方向：

- 顶栏白底
- 左侧导航白底
- 主体区浅灰背景
- 页签条白底，紧贴主体区顶部
- 主体内容使用白色卡片承载
- 层级靠间距、卡片、标题和按钮优先级表达，不靠花哨装饰

## 三、daisyUI 组件使用约定

通用组件默认使用 daisyUI 5（基于 Tailwind 的 CSS-only 组件库），不再使用 Element Plus。

daisyUI 5 是 CSS-only 库，无 JS 依赖。交互态（modal/dropdown 开关）通过 Vue 响应式变量或原生 `tabindex` + `:focus-within` 管理。

推荐映射（Element Plus → daisyUI）：

| 用途 | Element Plus（已废弃） | daisyUI 替代 |
|------|----------------------|-------------|
| 查询区 | `el-form` + `el-form-item` | `<form class="form-control">` + `<label class="label">` |
| 操作按钮 | `el-button` | `<button class="btn btn-primary">` |
| 下拉菜单 | `el-dropdown` | `<div class="dropdown">` + `tabindex` |
| 数据表格 | `el-table` | `<table class="table">`（原生 table + daisyUI 类） |
| 页签 | `el-tabs` | `<div role="tablist" class="tabs tabs-bordered">` |
| 统计卡片 | `el-card` + `el-statistic` | `<div class="card">` + `<div class="stat">` |
| 详情侧栏 | `el-drawer` | `<div class="drawer drawer-end">` + Vue 状态控制 |
| 确认弹窗 | `el-dialog` | `<dialog class="modal">` 或 `<div class="modal" :class="{'modal-open': visible}">` |
| 分页 | `el-pagination` | `<div class="join">` + 多个 `<button class="join-item btn">` |
| 状态标签 | `el-tag` | `<span class="badge badge-primary">` |
| 输入框 | `el-input` | `<input class="input input-bordered">` |
| 下拉选择 | `el-select` | `<select class="select select-bordered">` |
| 多选 | `el-checkbox` | `<input type="checkbox" class="checkbox">` |
| 单选 | `el-radio` | `<input type="radio" class="radio">` |
| 文本域 | `el-input type=textarea` | `<textarea class="textarea textarea-bordered">` |
| 警告提示 | `el-alert` | `<div role="alert" class="alert alert-warning">` |
| 折叠面板 | `el-collapse` | `<div class="collapse collapse-arrow">` |

约束：

1. 先用 daisyUI 现成组件类满足通用交互
2. 再通过 Tailwind utility class（`flex`/`gap-3`/`px-6`/`rounded-md` 等）做版式适配
3. 不要为了"更像设计稿"就把通用控件全部手写一遍
4. **禁止使用任何 `el-` 前缀的组件**——已废弃 Element Plus

## 四、页面落位方式

推荐顺序：

1. 先套统一页框
2. 再确定当前页面主任务
3. 再按需选择查询区 / 操作区 / 主表格 / 详情区 / 表单区等内容块
4. 最后补弹窗、抽屉、空状态、分页等辅助区域

坏例子：

- 每个页面重新发明一套导航
- 页签一页一套视觉语言
- 主体内容还没写清，先花大量时间做装饰

好例子：

- 页框统一
- 页签条直接承载“当前页面名 + 关闭按钮”
- 内容区差异清楚
- 有查询就放查询，没有查询就直接进入主内容，不为凑模板硬加一条工具栏
- 页面切换关系稳定

## 五、原型输入

1. 必须读取 design.md
2. 如 prd.md 已存在，还需读取：详细需求说明、状态机、权限汇总、数据字典

## 六、反馈处理

prototype-feedback.md 的反馈必须先归类：
- 表现问题：只改 prototype
- 语义问题：先回写 design，再同步

## 七、多页面 shell 写法模板（重要）

> 🔴 历史教训：曾经 AI 自造 `createShellApp`，把页面传入的 `extraData` 直接展开到 `data()` 返回对象里，导致 Vue 选项（data/methods/computed）被当作响应式数据属性，页面挂载时报 `Cannot read properties of undefined`，全部空白。
>
> 本节给出正确模板，AI 必须复用，不得自造 shell 框架。

### 核心原则

1. **shell 定义路由 + 渲染容器**，不持有页面业务数据
2. **每个页面是一个独立的 Vue 组件对象**（`{ template, data() {...}, methods: {...} }`）
3. 通过 `<component :is="currentPage">` 动态渲染当前页
4. **禁止**把页面传入的 Vue 选项展开到 shell 的 `data()` 里

### 正确实现模板（单文件版本，多页可拆分）

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <link href="lib/daisyui-themes.css" rel="stylesheet" />
  <link href="lib/daisyui.css" rel="stylesheet" />
  <script src="lib/tailwind.js"></script>
  <script src="lib/vue.global.prod.js"></script>
</head>
<body>
  <div id="app">
    <!-- 顶栏 / 导航省略，参考 templates/prototype.html -->

    <!-- 主体区：动态渲染当前页组件 -->
    <main>
      <component :is="currentPageComponent"></component>
    </main>
  </div>

  <script>
    // 1. 定义每个页面为独立组件对象
    const PageList = {
      template: `
        <div class="p-6">
          <h2 class="text-lg font-medium mb-4">周报列表</h2>
          <table class="table">
            <thead><tr><th>标题</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="item in list" :key="item.id">
                <td>{{ item.title }}</td>
                <td><span class="badge" :class="item.status === 'submitted' ? 'badge-primary' : 'badge-ghost'">{{ item.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      `,
      data() {
        return { list: [{ id: 1, title: '第 1 周', status: 'submitted' }] };
      }
    };

    const PageEdit = {
      template: `
        <div class="p-6">
          <h2 class="text-lg font-medium mb-4">填写周报</h2>
          <form class="form-control gap-3 max-w-xl">
            <label class="label"><span class="label-text">标题</span></label>
            <input class="input input-bordered" v-model="form.title" />
            <label class="label"><span class="label-text">内容</span></label>
            <textarea class="textarea textarea-bordered" rows="6" v-model="form.content"></textarea>
            <button class="btn btn-primary" @click="submit">提交</button>
          </form>
        </div>
      `,
      data() {
        return { form: { title: '', content: '' } };
      },
      methods: {
        submit() { alert('提交: ' + this.form.title); }
      }
    };

    // 2. shell 只管路由 + 当前页
    const App = {
      data() {
        return {
          currentPage: 'PageList',
          pages: {
            'PageList': { label: '周报列表', component: PageList },
            'PageEdit': { label: '填写周报', component: PageEdit }
          }
        };
      },
      computed: {
        currentPageComponent() {
          return this.pages[this.currentPage].component;
        }
      },
      methods: {
        go(pageKey) {
          this.currentPage = pageKey;
        }
      },
      template: `
        <div>
          <aside>
            <ul>
              <li v-for="(p, key) in pages" :key="key" @click="go(key)">{{ p.label }}</li>
            </ul>
          </aside>
          <main><component :is="currentPageComponent"></component></main>
        </div>
      `
    };

    Vue.createApp(App).mount('#app');
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
    page-list.js     # window.SPM_PAGES.PageList = { template, data, methods }
    page-edit.js
```

index.html 引入顺序：

```html
<script src="lib/vue.global.prod.js"></script>
<script src="pages/page-list.js"></script>
<script src="pages/page-edit.js"></script>
<script>
  const App = {
    data() {
      return {
        currentPage: 'PageList',
        pages: {
          'PageList': { label: '周报列表', component: window.SPM_PAGES.PageList },
          'PageEdit': { label: '填写周报', component: window.SPM_PAGES.PageEdit }
        }
      };
    },
    // ... 其余同上
  };
  Vue.createApp(App).mount('#app');
</script>
```

page-list.js 内容：

```javascript
window.SPM_PAGES = window.SPM_PAGES || {};
window.SPM_PAGES.PageList = {
  template: `...`,
  data() { return { ... }; },
  methods: { ... }
};
```

### 禁止的反模式

```javascript
// ❌ 错误 1：把页面 extraData 展开到 shell 的 data() 里
function createShellApp(pages) {
  const mergedData = {};
  pages.forEach(p => Object.assign(mergedData, p.extraData)); // extraData 含 data/methods 会被当响应式属性
  Vue.createApp({ data() { return mergedData; } }).mount('#app');
}

// ❌ 错误 2：在 shell 中混用页面级 data 和方法
const App = {
  data() {
    return {
      currentPage: 'list',
      // 下面这些是 PageList 的数据，错误地塞到 shell 里
      list: [],
      searchKeyword: ''
    };
  },
  methods: {
    // 下面这些是 PageList 的方法
    fetchList() { ... },
    handleSearch() { ... }
  }
};

// ❌ 错误 3：自造 createShellApp 函数封装上述反模式
// 任何叫 createShellApp 的函数都必须按本节模板的"独立组件 + <component :is>"方式实现
```

