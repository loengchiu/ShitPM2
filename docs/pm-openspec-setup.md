# PM 版 OpenSpec 改造手册

> 本手册指导你将 OpenSpec 改造成产品经理专用的需求交付工具。
> 改造后，OpenSpec 的产出物从"代码"变为"PRD + Prototype"。
> 整个过程不修改 OpenSpec 核心代码，仅通过注入自定义 schema + 配置完成。

---

## 前置条件

1. 已安装 Node.js 20.19.0 或更高版本
2. 已安装 OpenSpec：`npm install -g @fission-ai/openspec@latest`

---

## 第一步：创建自定义 Schema 目录

在你的项目 `openspec/schemas/` 下创建 `pm-workflow` 目录：

```
你的项目/
  openspec/
    schemas/
      pm-workflow/          ← 新建这个目录
        schema.yaml
        templates/
          proposal.md
          design.md
          prd.md
          prototype.html
          tasks.md
    config.yaml             ← 新建或编辑
```

---

## 第二步：创建 schema.yaml

**路径**：`openspec/schemas/pm-workflow/schema.yaml`

**作用**：定义 PM 工作流的 artifact 依赖关系

```yaml
name: pm-workflow
artifacts:
  - id: proposal
    generates: proposal.md
    applies-required: true
    requires: []
  - id: design
    generates: design.md
    applies-required: true
    requires: [proposal]
  - id: prd
    generates: prd.md
    applies-required: true
    requires: [design]
  - id: prototype
    generates: index.html
    applies-required: true
    requires: [design]
  - id: tasks
    generates: tasks.md
    applies-required: false
    requires: [prd, prototype]
```

**说明**：
- `proposal` 是根节点，不需要前置
- `design` 依赖 proposal（先对齐再做设计）
- `prd` 和 `prototype` 都依赖 design（设计确认后才能展开）
- `tasks` 依赖 prd 和 prototype（是它们的实现清单）
- `prd` 和 `prototype` 可以并行生成（都只需要 design）

---

## 第三步：创建 5 个模板文件

### 3.1 proposal.md

**路径**：`openspec/schemas/pm-workflow/templates/proposal.md`

```markdown
# 需求提案：{{变更名}}

## 一、需求概述

<!-- 一句话说明当前需求要做什么 -->

## 二、建设范围

### （一）本期范围

<!-- 本次迭代做什么 -->

### （二）后续范围（如有）

<!-- 二期/三期做什么，没有则删除本节 -->

### （三）明确不做

<!-- 本次明确排除的内容 -->

## 三、建设方式

<!-- iteration（在现有系统上扩展）/ new_build（全新建设）/ hybrid（部分复用部分新建），三选一 -->

## 四、涉及系统

<!-- 涉及哪些系统，各系统的边界和对接方式 -->

## 五、现有线索

### （一）已有系统或页面

### （二）已有资料

## 六、待确认问题

<!-- 如有阻塞性问题，逐条列出。无则写"无" -->
```

### 3.2 design.md

**路径**：`openspec/schemas/pm-workflow/templates/design.md`

```markdown
# 设计基线

## 一、文档概述

<!-- 可选：项目背景、设计目标 -->

## 二、范围与建设方式

<!-- 引用 proposal 结论 -->

## 三、角色定义

<!-- 核心：角色名称、职责、权限层级 -->

## 四、模块定义

<!-- 核心：模块名称、职责、包含页面 -->

## 五、核心业务流程

<!-- 可选：主流程、关键分支、异常 -->

## 六、页面清单

<!-- 核心：必须使用表格；至少包含 页面编号、页面名称、所属模块、主要功能 -->

## 七、字段定义

<!-- 核心：必须使用表格；字段完整属性（名称、类型、长度、必填、默认值、枚举值、格式、业务来源、说明） -->

## 八、页面与字段落点

<!-- 核心：按页面分小节；每页使用表格，至少包含"区域/动作""字段"两列；字段名必须直接引用上文字段定义中的标准字段名 -->

### 非页面落点字段

<!-- 可选：纯内部字段，使用表格，至少包含"字段""原因"两列 -->

## 九、规则与状态定义

<!-- 核心：业务规则、状态集合、状态迁移、触发条件 -->

## 十、权限定义

<!-- 核心：按"默认规则 + 例外"组织，不逐字段平铺 -->
```

### 3.3 prd.md

**路径**：`openspec/schemas/pm-workflow/templates/prd.md`

```markdown
# PRD 正文

## 一、文档概述

<!-- 可选 -->

## 二、范围

<!-- 可选 -->

## 三、业务流程

<!-- 可选：写主流程、关键分支与异常、状态流转 -->
<!-- 这里只写业务流转，不写页面跳转、按钮点击、弹窗/抽屉开合等页面操作细节 -->

## 四、详细需求说明

<!-- 核心：按模块 → 页面 → 动作组织 -->
<!-- 推荐骨架：
### （一）模块名
模块职责与涉及页面，1-2 句

#### 1．页面名
页面区域组成与职责，1 段

（1）动作一
动作正文

（2）动作二
动作正文
-->
<!-- 列表/表单/详情中的字段描述只写当前动作需要理解的关键字段、展示方式和规则 -->
<!-- 如需交代页面区块，且区块较多或存在子分组时，优先用 `· 区块名：规则`；区块内子分组可用 `- 子分组：规则`。区块很少且内容很短时，直接自然句写 -->
<!-- 动作开头先写业务判断和关键结果，再补排序、分页、默认加载、空状态等通用展示规则 -->

## 五、权限汇总

<!-- 核心：页面级、按钮级权限；如存在字段权限例外，写入详细需求说明对应动作 -->

## 六、数据字典

<!-- 核心：按实体分组，默认使用 4 列（字段、类型、必填、说明）；长度、默认值、枚举值、格式、业务来源仅在确实影响实现时写入说明 -->

## 七、状态机

<!-- 核心：按核心业务对象组织，包含状态集合、迁移、触发动作和限制条件 -->
```

### 3.4 prototype.html

**路径**：`openspec/schemas/pm-workflow/templates/prototype.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>原型 - {{项目名称}}</title>
  <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css">
  <style>
    :root {
      --shell-bg: #f5f6f8;
      --shell-card: #ffffff;
      --shell-line: #ebeef5;
      --shell-text: #1f2329;
      --shell-text-secondary: #4e5969;
      --shell-primary: #2f7df6;
      --shell-header-height: 64px;
      --shell-sidebar-width: 248px;
      --shell-radius: 12px;
      --shell-shadow: 0 2px 10px rgba(31, 35, 41, 0.06);
    }
    * { box-sizing: border-box; }
    html, body, #app {
      margin: 0; min-height: 100vh;
      background: var(--shell-bg); color: var(--shell-text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    .shell-root { min-height: 100vh; background: var(--shell-bg); }
    .shell-header {
      height: var(--shell-header-height); display: flex; align-items: center;
      justify-content: space-between; padding: 0 28px; background: #fff;
      border-bottom: 1px solid #f0f0f0;
    }
    .shell-brand { display: flex; align-items: center; gap: 12px; min-width: 240px; }
    .shell-brand-mark {
      width: 30px; height: 30px; border-radius: 8px;
      display: inline-flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #1677ff 0%, #69b1ff 100%);
      color: #fff; font-weight: 700; font-size: 13px;
    }
    .shell-brand-text { display: flex; flex-direction: column; gap: 2px; }
    .shell-brand-title { font-size: 15px; font-weight: 700; line-height: 1.2; }
    .shell-brand-subtitle { font-size: 11px; color: var(--shell-text-secondary); line-height: 1.2; }
    .shell-header-center { flex: 1; display: flex; align-items: center; justify-content: center; padding: 0 24px; color: var(--shell-text-secondary); font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .shell-header-actions { display: flex; align-items: center; gap: 12px; }
    .shell-body { min-height: calc(100vh - var(--shell-header-height)); }
    .shell-sidebar {
      width: var(--shell-sidebar-width); background: #fff;
      border-right: 1px solid #f0f0f0; padding: 18px 14px; overflow: auto;
    }
    .shell-nav-group + .shell-nav-group { margin-top: 18px; }
    .shell-nav-group-title { padding: 0 14px 8px; font-size: 12px; color: #86909c; text-transform: uppercase; letter-spacing: 0.04em; }
    .shell-main { padding: 0; background: var(--shell-bg); }
    .shell-tabbar {
      min-height: 74px; display: flex; align-items: center; gap: 18px;
      padding: 0 26px; background: #fff; border-bottom: 1px solid #f0f0f0;
    }
    .shell-tabbar-toggle { width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; color: #4e5969; border-radius: 6px; flex: 0 0 auto; }
    .shell-tabbar-tabs { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; overflow: hidden; }
    .shell-tabbar-tab {
      display: inline-flex; align-items: center; gap: 8px;
      min-width: 148px; max-width: 260px; height: 42px; padding: 0 16px;
      border: 1px solid #e7ebf2; border-radius: 8px; background: #f7f8fa; color: #4e5969;
    }
    .shell-tabbar-tab.is-active { background: #fff; color: var(--shell-text); border-color: #d7e4ff; box-shadow: 0 2px 8px rgba(47, 125, 246, 0.08); }
    .shell-tabbar-label { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 14px; font-weight: 500; }
    .shell-tabbar-close { color: #a1a7b3; font-size: 12px; line-height: 1; }
    .shell-main-body { padding: 18px 22px 24px; }
    .shell-workbench { display: flex; flex-direction: column; gap: 16px; }
    .shell-block-card { border-radius: var(--shell-radius); box-shadow: var(--shell-shadow); border: 0; }
    .shell-content-demo { min-height: 96px; border-radius: 12px; border: 1px dashed #d7dce5; background: #ffffff; box-shadow: var(--shell-shadow); }
    .shell-placeholder {
      min-height: 520px; padding: 56px 24px; text-align: center;
      color: #a1a7b3; border: 1px dashed #d7dce5; border-radius: 12px; background: #fafcff;
    }
    @media (max-width: 960px) {
      .shell-tabbar { align-items: flex-start; flex-direction: column; padding-top: 14px; padding-bottom: 14px; }
      .shell-tabbar-tabs { width: 100%; }
    }
  </style>
</head>
<body>
  <div id="app">
    <el-container class="shell-root">
      <el-header class="shell-header">
        <div class="shell-brand">
          <span class="shell-brand-mark">PM</span>
          <div class="shell-brand-text">
            <div class="shell-brand-title">{{项目名称}}</div>
            <div class="shell-brand-subtitle">统一业务工作台</div>
          </div>
        </div>
        <div class="shell-header-center">当前模块 / 当前业务域</div>
        <div class="shell-header-actions">
          <el-button text>帮助</el-button>
          <el-avatar size="small">U</el-avatar>
        </div>
      </el-header>
      <el-container class="shell-body">
        <aside class="shell-sidebar">
          <div class="shell-nav-group">
            <div class="shell-nav-group-title">导航分组</div>
            <el-menu default-active="page-1">
              <el-menu-item index="page-1">首页</el-menu-item>
            </el-menu>
          </div>
        </aside>
        <el-main class="shell-main">
          <div class="shell-tabbar">
            <span class="shell-tabbar-toggle" aria-label="页签列表">
              <el-icon><Operation /></el-icon>
            </span>
            <div class="shell-tabbar-tabs">
              <div class="shell-tabbar-tab is-active">
                <span class="shell-tabbar-label">当前页面名称</span>
                <span class="shell-tabbar-close"><el-icon><Close /></el-icon></span>
              </div>
            </div>
          </div>
          <div class="shell-main-body">
            <div class="shell-workbench">
              <div class="shell-content-demo"></div>
              <div class="shell-placeholder">
                这里承载当前页面真正的业务内容。可按需放查询区、操作区、列表区、表单区、详情区。
              </div>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <script src="https://unpkg.com/element-plus/dist/index.full.min.js"></script>
  <script src="https://unpkg.com/@element-plus/icons-vue/dist/index.iife.min.js"></script>
  <script>
    const { Operation, Close } = ElementPlusIconsVue;
    const app = Vue.createApp({ data() { return {}; } });
    app.use(ElementPlus);
    app.component('Operation', Operation);
    app.component('Close', Close);
    app.mount('#app');
  </script>
</body>
</html>
```

### 3.5 tasks.md

**路径**：`openspec/schemas/pm-workflow/templates/tasks.md`

```markdown
# 任务清单：{{变更名}}

## 1. PRD 撰写

<!-- 以下由 AI 从 design 和 PRD 中自动拆解，每条对应 PRD 中的一个具体章节或动作 -->
<!-- 示例格式：
- [ ] 1.1 撰写文档概述
- [ ] 1.2 撰写业务流程
- [ ] 1.3 撰写 XX 模块 - XX 页面 - XX 操作
-->

## 2. Prototype 制作

<!-- 以下由 AI 从 design 页面清单中自动拆解，每条对应 prototype 中的一个页面或组件 -->
<!-- 示例格式：
- [ ] 2.1 搭建后台基座（顶栏、导航、页签）
- [ ] 2.2 实现 P01 XX 页面
- [ ] 2.3 实现 P02 XX 页面
-->
```

---

## 第四步：创建 config.yaml

**路径**：`openspec/config.yaml`

**作用**：注入 PM 写作规则、风格指南、强制约束

```yaml
schema: pm-workflow

context: |
  你是产品经理助手，负责产出 PRD 文档和 HTML 原型。以下是必须遵守的写作规则：

  === Design 写作规则 ===
  - 字段定义必须使用 9 列表格：字段、类型、长度、必填、默认值、枚举值、格式、业务来源、说明
  - 页面清单必须使用结构化表格（页面编号、页面名称、所属模块、主要功能），不用散文或纯标题平铺
  - 页面与字段落点必须按"页面 > 区域/动作 > 字段"组织，使用结构化表格
  - 每个字段必须满足二选一：要么出现在页面与字段落点，要么出现在"非页面落点字段"例外表并写明原因
  - 权限定义按"默认规则 + 例外"组织，不逐字段平铺
  - design 是字段、权限、状态的唯一事实源
  - 不写研发级页面正文（那是 PRD 的职责）
  - 不新增 proposal 未确认的范围
  - Design 正文不得出现稳定 ID（如 MODULE-xxx、FIELD-xxx）

  === PRD 写作规则 ===
  - 按模块 → 页面 → 动作三级组织。模块顺序与 design 模块定义一致，页面顺序与 design 页面清单一致
  - 每个页面正文必须覆盖三层：①界面元素与展示规则 ②交互逻辑与状态流转 ③异常处理与边界场景
  - 动作开头先写业务判断和关键结果，再补排序、分页、默认加载、空状态等通用规则
  - 列表/表单/详情中的字段描述只写当前动作需要的关键字段，不把数据字典完整搬入正文
  - 动作下如需交代页面区块，且区块较多或存在子分组时，优先用 `·` 列一级区块、`-` 列区块内子分组；区块很少且内容很短时，直接自然句写
  - 具体数值写死（"每页 20 条""小数 2 位"），禁止占位
  - UI 文案用双引号嵌入正文（如点击"提交"按钮）
  - 超长文本必须交代处理方式（截断/换行/滚动/悬停）
  - 少用加粗，层级通过标题、编号、段落和列表表达
  - 禁用模板腔（"用于承载""需支持""按规范处理""同常规"）
  - 禁用模糊表述（"按配置""待补充""详见原型"）
  - 禁用标签式正文（**页面目标：**XX / **关键动作：**XX）
  - 禁用动作流水账（1.点击 2.填写 3.提交）
  - Markdown 标题最多 3 级：## 章、### 节、#### 小节。中文编号推荐：章 一、 节 （一） 小节 1．
  - 数据字典默认使用 4 列表格：字段、类型、必填、说明
  - 长度、默认值、枚举值、格式、业务来源仅在确实影响实现时写入说明，不固定铺满
  - PRD 不得独立新增 design 中不存在的字段、权限、状态定义
  - 写完每个动作后自检：数据展示、按钮反馈、表单校验、列表加载、弹窗行为、异常降级、数值边界

  === Proposal 对齐纪律 ===
  - 一次只追问一个阻塞性问题，不一问多个
  - 能从已有材料中推断的不问
  - 4 轮以上生成轮次摘要，6 轮以上冻结状态再决定是否继续
  - 最终收敛为：目标、范围、边界、建设方式、建设类型判断

  === Prototype 制作规则 ===
  - 默认复用统一后台基座（顶栏、左侧导航、页签区、主体工作区）
  - 通用组件使用 Element Plus（el-form、el-table、el-button、el-dialog、el-drawer、el-pagination、el-tag）
  - 不重写 Element Plus 基础交互语义，只做版式、间距、信息层级适配
  - 多个页面必须共用同一套顶栏、导航和页签语言
  - 页面名称默认放在页签条中表达，不再另起大页头重复写标题
```

rules:
  proposal:
    - 明确建设类型（iteration / new_build / hybrid）并说明判断依据
    - 只写目标、范围、边界、建设方式，不展开页面和字段细节
    - 有阻塞性缺口时逐条追问，一次只问一个问题
    - 最后一行收口为唯一待确认问题

  design:
    - 核心章节必须全部存在：角色定义、模块定义、页面清单、字段定义、页面与字段落点、规则与状态定义、权限定义
    - 页面清单使用结构化表格，不用散文或纯标题平铺
    - 字段定义使用 9 列表格
    - 页面与字段落点按"页面 > 区域/动作 > 字段"组织
    - 权限定义按"默认规则 + 例外"组织
    - 每个字段必须出现在页面落点或例外表中
    - 不写研发级页面正文，不做高保真视觉表达
    - 不新增 proposal 未确认的范围

  prd:
    - 核心章节必须全部存在：详细需求说明、权限汇总、数据字典、状态机
    - 按模块 → 页面 → 动作组织
    - 每个页面覆盖三层：展示规则、交互逻辑、异常边界
    - 禁止标签式正文、动作流水账、纯表格正文
    - 禁止模糊表述和模板腔
    - 数据字典使用轻量格式，按实体分组
    - 不得引入 design 中不存在的新字段、新权限、新状态

  tasks:
    - 每个 task 对应 PRD 中的一个三级小节（如"XX 模块 - 列表页 - 查询操作"）或 prototype 中的一个页面
    - 单个 task 不超过 200 行输出
    - PRD 任务和 Prototype 任务分两个章节

---

## 第五步：启用 PM Schema

### 方法一：命令行设置

```bash
openspec config set default-schema pm-workflow
```

### 方法二：在项目中指定

在任意 `/opsx:` 命令中加参数：

```
/opsx:new my-change --schema pm-workflow
```

### 方法三：在 config.yaml 中指定（推荐）

上一步创建的 `config.yaml` 中已设置 `schema: pm-workflow`，OpenSpec 会自动读取。

---

## 第六步：刷新 AI 指令

```bash
openspec update
```

重启 AI 编辑器（Claude Code / Cursor / Trae），使新 schema 和 rules 生效。

---

## 验证安装

运行以下命令检查：

```bash
# 检查 schema 是否存在
openspec schemas

# 应显示 pm-workflow 在列表中

# 检查项目配置
cat openspec/config.yaml

# 应显示 schema: pm-workflow 和 rules 配置
```

如果一切正常，你就可以开始使用了。
