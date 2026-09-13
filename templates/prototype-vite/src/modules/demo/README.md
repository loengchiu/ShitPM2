# 模板受检 Fixture（Demo Fixtures）

本目录为 ShitPM 模板工程内置的**受检 Fixture**，用于演示 Ant Design + Tabler 主题视觉规范、共享 UI 组件标准用法与数据锚点写法。

## 身份与边界定义

1. **受检 Fixture（Checked Fixture）**：
   - 纳入共享层规则守护：受 `scripts/python/prototype-shared-guard.py`（G1~G5）全量守护，严禁直接引用未经封装的第三方图标、外部 CSS 或重复版权（实测真实受检通过）；
   - 源码扫描与隔离登记：受 `scripts/python/prototype-consistency-check.py` 源码扫描覆盖，不再作为未解释路径静默跳过；脚本将其显式登记为 `fixture_files` 与 `fixture_routes`；
   - 业务事实比对隔离：本目录属于模板 fixture，其路由与锚点不参与具体用户项目业务 Design Index 的事实对账（避免在真实项目上产生假红或假缺失）；
   - 路由判定契约：`prototype-consistency-check.py` 依据组件是否解析到 fixture 文件判定 fixture 路由；凡是绑定或复用 fixture 组件（如 `Placeholder.jsx` 占位组件或样张组件）的路由项均作为 fixture 路由整体跳过 Design 页面对账，不产生假冲突或假遗漏。

2. **组件与锚点示范**：
   - `DetailDemo.jsx`：示范详情页 `data-page`、`data-block`、`data-state`、`data-operation` 锚点写法，以及角色字段可见性过滤；
   - `FormDemo.jsx`：示范表单页 `FormSection` 分区卡片、字段控件 `data-field`、步骤条 `Steps` 与底部 `ActionBar` 操作绑定；
   - `DesignGallery.jsx`：示范 Ant Design 原生控件与 Tabler 调色板视觉观感；
   - `Placeholder.jsx`：多模块路由占位壳层组件。

3. **项目生命周期**：
   - 新项目首次生成业务原型时，按 `skills/spm-prototype/SKILL.md` 指引清理 `src/modules/demo/` 下的样张页面及其路由登记（`Placeholder.jsx` 保留），替换为真实业务模块。
