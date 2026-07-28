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

> 历史教训：曾经自造 `createShellApp`，把页面传入的 `extraData` 直接展开到 `data()` 返回对象里，导致 Vue 选项（data/methods/computed）被当作响应式数据属性，页面挂载时报 `Cannot read properties of undefined`，全部空白。
>
> 本节给出正确模板，必须复用，不得自造 shell 框架。

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

---
