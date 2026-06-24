# spm-prototype-mark SKILL.md Review 报告

**Review 日期：** 2026-06-24
**Review 对象：** `D:/work/ShitPM/skills/spm-prototype-mark/SKILL.md`
**对照基准：** `skills/spm-prototype/SKILL.md` + `templates/prototype.html` + `references/prototype-writing.md` 第七章

---

## 总体结论

**不通过。** SKILL.md 在多个关键点上对上游原型的真实实现做了错误假设，按现状执行必然失败。最严重的是组件库认知错误和 lib/ 路径断裂——这两条任一发生，标注原型打开就是白屏或没样式。

必须修复 P0 后再交付。

---

## P0 级问题（必挂，阻塞使用）

### P0-1 组件库认知完全错误——写 Element Plus，实际是 daisyUI

**位置：** 步骤 4「selector 生成规则」、步骤 4「元素识别策略」

**问题：**
SKILL.md 反复写：
- "DOM 中几乎无 id，class 全是 `el-button`/`el-form-item` 等重复值"
- "按钮类：`button`、`.btn`、`[role="button"]`、`el-button`"
- "表格类：`table`、`.table`、`el-table`"
- "状态标签：`.tag`、`.badge`、`el-tag`"

**事实：** `spm-prototype` SKILL.md 明确：
- "通用组件默认使用 **daisyUI 5**"
- 自检项 7："**无 el- 前缀组件残留**"——`el-table`/`el-button`/`el-form` 出现即不通过
- 实际组件类是 `btn`/`menu`/`card`/`table`/`form-control`/`input`/`select`/`textarea`/`badge`/`dropdown` 等

**后果：** AI 按 SKILL.md 去找 `el-button`/`el-form-item`，一个都找不到，selector 生成全空，标注系统空跑。

**修复：** 全文删除 `el-` 前缀组件引用，替换为 daisyUI 组件类清单。元素识别策略改为按 daisyUI 类名识别。

---

### P0-2 lib/ 相对路径在复制后断裂——标注原型必白屏

**位置：** 步骤 3「复制原型」

**问题：** `templates/prototype.html` 和 `references/prototype-writing.md` 第七章模板中，lib 引用全是相对路径：
```html
<link href="lib/daisyui-themes.css" rel="stylesheet" />
<link href="lib/daisyui.css" rel="stylesheet" />
<script src="lib/tailwind.js"></script>
<script src="lib/vue.global.prod.js"></script>
```

原型在 `output/prototype/index.html` 时，相对路径 `lib/` 指向项目根 `lib/`（因为 prototype 阶段约定 lib 在项目根）。

复制到 `output/prototypemark/index.html` 后，相对路径 `lib/` 指向 `output/prototypemark/lib/`（**不存在**），四件套全部 404，Vue 不加载、Tailwind 不加载、daisyUI 不加载——**标注原型直接白屏无样式**。

**后果：** 标注原型打开就是裸 HTML，悬浮栏能显示（内联 CSS），但原型本身完全没渲染。

**修复方案（三选一，推荐 A）：**
- **A. 改写 lib 路径为 `../../lib/`**：复制后用 Python 脚本把 `lib/` 替换为 `../../lib/`，指向项目根 lib/。最小侵入。
- B. 复制 lib/ 到 `output/prototypemark/lib/`：简单但增加磁盘占用（daisyui.css 946KB）。
- C. 用绝对 file:// 路径：跨机器不可移植，不推荐。

SKILL.md 步骤 3 必须明确写：复制后立即执行 lib 路径改写，并加入自检。

---

### P0-3 页面切换机制过度泛化——实际是固定模式

**位置：** 步骤 5.3「PanelManager 跳转执行逻辑」、章节「页面跳转实现策略」

**问题：** SKILL.md 列了 4 种切换机制（Vue 响应式变量 / 导航菜单点击 / 路由 hash / CSS display）+ 3 级 fallback + verify 校验，让 AI 现场识别。

**事实：** `references/prototype-writing.md` 第七章是**强制模板**，原型页面切换机制是固定的：
```javascript
const App = {
  data() {
    return {
      currentPage: 'PageList',       // 当前页 key
      pages: { 'PageList': {...}, 'PageEdit': {...} }
    };
  },
  computed: {
    currentPageComponent() { return this.pages[this.currentPage].component; }
  },
  methods: {
    go(pageKey) { this.currentPage = pageKey; }   // 唯一切换入口
  }
}
```
模板写死 `<component :is="currentPageComponent">`，没有 hash、没有 display 切换、没有 nav-click 单独路径。

**后果：** AI 浪费精力识别不存在的机制，pageNav fallback chain 全是死代码；更糟的是 AI 可能"识别"出错机制，跳转失败。

**修复：** 删除 4 种策略表，改为单一机制：**通过 Vue 实例的 `go(pageKey)` 方法切换页面**。具体实现：
```javascript
// 标注系统获取 Vue 实例
const app = document.querySelector('#app').__vue_app__;
const vm = app._instance.proxy;
vm.go(pageKey);   // 调用 shell 的 go 方法
```
pageNav 字段简化为 `{ type: "vue-go", pageKey: "PageList" }`，不需要 fallback。

---

### P0-4 自检项 9 不可执行——Python 跑不了 querySelectorAll

**位置：** 步骤 6 自检表第 9 项

**问题：** "用 Python 解析 HTML 校验每个 selector 的 querySelectorAll 结果为 1"

**事实：**
1. Python BeautifulSoup **没有** `querySelectorAll` 方法
2. 原型是 Vue 模板，Python 解析时看到的是 `<div v-if="currentPage==='page-1'">` 原始模板，不是渲染后 DOM
3. Vue 组件 `<component :is="currentPageComponent">` 在 Python 解析时根本不存在，所有页面组件的 template 都是 JS 字符串

**后果：** 自检项 9 永远无法执行，要么 AI 跳过（自检失效），要么 AI 强行用 BeautifulSoup 找元素（全部找不到，误判失败）。

**修复：** 自检项 9 改为：
- 锚点注入后，用 Python 校验 `data-pm-mark=` 出现次数 = 标注项数
- selector 唯一性由 `data-pm-mark` 锚点天然保证（每个 id 全文唯一），不需要 querySelectorAll

---

### P0-5 锚点注入脚本只给伪代码——无可用脚本

**位置：** 步骤 5.0「注入 data-pm-mark 锚点属性」

**问题：** SKILL.md 写"必须用 Python 脚本（BeautifulSoup 或正则）完成"，但只给了一句伪代码：
```python
from bs4 import BeautifulSoup
# 或用正则按页面容器 + 元素序号定位，添加 data-pm-mark 属性
```

**事实：**
1. 项目约定所有脚本位于 `scripts/python/`（见 spm-prototype SKILL.md 开头"脚本路径"章节）
2. `scripts/python/` 下没有任何 mark 相关脚本
3. bs4 不是 Python 标准库，需要 `pip install beautifulsoup4`，项目未声明此依赖

**后果：** AI 要么现场写脚本（每次执行质量不稳定），要么用正则（Vue 模板用正则改 HTML 极易破坏），要么放弃锚点注入。

**修复：**
- 在 `scripts/python/` 下新增 `inject-prototype-marks.py`，接受 JSON 标注数据 + HTML 路径，完成锚点注入 + lib 路径改写 + 标注系统注入
- 用 Python 标准库 `html.parser` 或 `re`，不引入 bs4 依赖
- SKILL.md 步骤 5.0 改为"调用 `scripts/python/inject-prototype-marks.py`"

---

## P1 级问题（功能部分失效或 AI 执行偏离）

### P1-1 最小读取集合缺 `references/prototype-writing.md`

**位置：** 步骤「最小读取集合」

**问题：** 没有读 `references/prototype-writing.md` 第七章，AI 不知道 shell 真实结构，只能靠"分析 HTML"猜——这正是 P0-3 过度泛化的根源。

**修复：** 最小读取集合追加 `references/prototype-writing.md`，明确"用于理解 shell 的 currentPage/go/component:is 机制"。

---

### P1-2 pageNav.verify 字段未在数据格式中定义

**位置：** 步骤 4 标注数据格式 vs 步骤 5.3 PanelManager 逻辑

**问题：** 步骤 5.3 写"校验方法由 AI 在分析阶段确定并写入 `pageNav.verify` 字段"，但步骤 4 的数据格式 example 里没有 `pageNav` 字段，更没有 `verify`。

**修复：** P0-3 修复后，pageNav 字段简化为 `{ type: "vue-go", pageKey: "..." }`，verify 字段可删除（go 方法是同步的，调用后 DOM 自然更新，MutationObserver 会检测到）。如果保留 verify，必须在数据格式 example 里补上。

---

### P1-3 多页面拆分原型未处理

**位置：** 步骤 3「复制原型」

**问题：** `spm-prototype` SKILL.md 步骤 5 产出"主原型文件（或按页面拆分）"，`references/prototype-writing.md` 第七章给了多文件拆分版本：
```
output/prototype/
  index.html
  pages/
    page-list.js
    page-edit.js
```

mark 步骤 3 只复制 `index.html`，如果原型是拆分版，`pages/*.js` 没复制，标注原型直接挂掉。

**修复：** 步骤 3 改为"复制 `output/prototype/` 整个目录到 `output/prototypemark/`"，保留目录结构。自检项追加"如原型含 pages/ 子目录，确认已复制"。

---

### P1-4 过期校验逻辑跨章节分散

**位置：** 步骤 1 前置检查表 vs 章节末「与 spm-fix 的过期校验」

**问题：** 执行要求"步骤 1 前置检查中追加一项——对比 prototype 和 prototypemark 修改时间"，但实际写在文档末尾的"与其他 skill 的关系"章节。AI 执行步骤 1 时只看步骤 1 的表格，容易漏。

**修复：** 把过期校验直接加到步骤 1 的前置检查表里，作为独立一行。章节末只保留说明性文字。

---

### P1-5 备注 300 字上限与页面级示例自相矛盾

**位置：** 步骤 4「备注内容撰写规则」 vs 「页面级 fallback 规范」

**问题：**
- 规则 5："备注长度控制在 50-300 字"
- 页面级示例备注明显超 300 字："本页面用于查看当前用户提交的全部周报。主要功能：1)... 2)... 3)... 4)... 状态：... 权限：..."（实际约 150 字，但规则字数上限对页面级整体说明太紧）

**修复：** 区分元素级和页面级字数上限：
- 元素级备注：50-300 字
- 页面级备注：100-500 字

---

### P1-6 MutationObserver 监听容器假设不基于真实模板

**位置：** 步骤 5.3「PageObserver」

**问题：** 写"AI 在步骤 4 识别出主体工作区容器（通常是 `.main-content`/`.workspace`/`#app-main`）"。

**事实：** `templates/prototype.html` 真实结构是：
```html
<div id="app">
  <main class="flex-1 flex flex-col overflow-hidden">
    <div class="shell-tabbar-inner ...">...</div>   <!-- 页签栏 -->
    <div class="flex-1 overflow-y-auto p-6">        <!-- 工作区，页面组件渲染在这里 -->
      <component :is="currentPageComponent"></component>
    </div>
  </main>
</div>
```
没有 `.main-content`/`.workspace`/`#app-main`。真实工作区是 `<main>` 内的 `.flex-1.overflow-y-auto.p-6`。

**后果：** AI 按假设去找容器找不到，MutationObserver 监听范围错误，页面切换检测失效。

**修复：** 明确监听 `<main>` 元素（或 `#app`，subtree:true），删除猜测性类名。

---

## P2 级问题（一致性 / 体验）

### P2-1 缺「脚本路径」章节

`spm-prototype` SKILL.md 开头有明确的"脚本路径"章节（标红硬约束），mark SKILL.md 没有。应补充，明确 `inject-prototype-marks.py` 的绝对路径。

### P2-2 深色标注弹窗 vs 浅色原型的对比度说明不足

原型默认 `data-theme="light"`（浅色），标注弹窗深色 `#1e293b`——对比度其实 OK。但 SKILL.md 没说明"标注系统配色与 daisyUI 主题无关，固定深色以保证在任意主题下可见"。应补一句。

### P2-3 与 spm-prototype-review 的执行顺序未说明

mark 改的是 `output/prototypemark/`，review 审的是 `output/prototype/`，两者不冲突。但 SKILL.md 没说明：mark 可以在 review 之前/之后/独立做，不依赖 review 通过。应在「与其他 skill 的关系」表里明确。

### P2-4 spm-fix 传播矩阵未更新

SKILL.md 自己提到"spm-fix 传播矩阵当前不感知 mark 副本"，但没说要不要去更新 `skills/spm-fix/SKILL.md` 的传播矩阵。应明确：本次 review 不改 spm-fix，mark 自己启动时做过期校验即可（已写），后续再评估是否纳入 spm-fix 传播链。

---

## 修复优先级与建议执行顺序

| 顺序 | 问题 | 修复动作 | 工作量 |
|------|------|---------|--------|
| 1 | P0-1 组件库认知 | 全文替换 el- → daisyUI 类名 | 小 |
| 2 | P0-2 lib 路径断裂 | 步骤 3 加 lib 路径改写 + 自检 | 小 |
| 3 | P0-3 页面切换机制 | 删除 4 策略表，改为 vm.go(pageKey) 单一机制 | 中 |
| 4 | P0-5 锚点注入脚本 | 新增 scripts/python/inject-prototype-marks.py | 中 |
| 5 | P0-4 自检项 9 | 改为 data-pm-mark 计数校验 | 小 |
| 6 | P1-1 读 references | 最小读取集合追加 prototype-writing.md | 小 |
| 7 | P1-3 多页面拆分 | 步骤 3 改为复制整个目录 | 小 |
| 8 | P1-6 监听容器 | 改为监听 `<main>` 或 `#app` | 小 |
| 9 | P1-2/P1-4/P1-5 | 数据格式补字段 / 过期校验入表 / 字数分级 | 小 |
| 10 | P2 系列 | 补说明 | 小 |

---

## 建议的下一步

1. **先确认 P0 修复方案**——特别是 P0-2 的 lib 路径改写方案（A/B/C）和 P0-5 的脚本方案（独立脚本 vs 现场写）
2. **确认后再动手改 SKILL.md 和新增脚本**——避免改一半发现方案要换
3. **改完后用真实原型跑一遍**——找一个 spm-prototype 生成的真实原型，跑 mark，打开标注原型验证：原型正常渲染 + 悬浮栏显示 + 标记点定位准确 + 弹窗可拖拽可编辑

---

## 附：Review 中未发现问题的地方（确认 OK）

- 触发词、输入依赖、不修改原始原型的硬规则——OK
- 标注数据 annotationId 稳定派生规则（pageId + selectorHash）——OK，思路正确
- 弹窗拖拽/缩放/编辑/localStorage 持久化设计——OK
- "同时只允许打开一个弹窗"的设计理由——OK，合理
- 失败模式表覆盖度——基本 OK，但 P0-2 lib 路径断裂未列入，应补
- 不进入 review 链路、不写 metadata——OK，与 USAGE.md 一致
