---
name: spm-prototype-mark
disable-model-invocation: true
description: "为源码原型副本添加可点击的关键点标记和来源备注浮窗。"
---

## 路径与边界

从系统 prompt 的 ShitPM bundle root: 读取 $BUNDLE。规则资源使用 $BUNDLE/scripts/python/、references/、templates/、contracts/；项目文件使用当前项目根目录。

Mark 只处理 output/prototypemark/ 副本：

- 原始 output/prototype/、正式 Design 和 output/prd/prd.md 保持不变。
- 标注内容是 Design/PRD 的展示载体，不是产品事实源；浮窗必须标明来源。
- 高影响问题只形成结构化意见，交由 spm-fix 回写 Design；Mark 不进入 Review 链路。
- PRD 可选；没有 PRD 时使用对应 Design 文件，并显示“内容来源：Design 文件（PRD 未生成）”。

## 任务判定

用户明确说初始化标注或增量更新后执行对应流程；两者都未明确时先询问“需要初始化标注还是增量更新？”。流程开始输出模型建议：明确定位和展示可用轻量模型；主动发现产品或交互问题属于 Prototype Review，不在 Mark 内处理。

## 初始化标注

1. 检查 output/prototype/ 含 package.json、src/、Design 地图和 设计集清单.json；PRD 缺失可继续。运行 `python $BUNDLE/scripts/python/prototype-source-check.py --project-root .`。
   完成条件：源码检查和 Design 输入均可读；失败时停止，不复制、不标注。只有 dist/compiled.js 时报告源码工程缺失。
2. 将 output/prototype/ 复制到 output/prototypemark/，排除 node_modules/ 和旧 dist/，保留源码工程文件。在副本执行 npm ci、npm run build。
   完成条件：副本构建成功，且原始目录没有变化。
3. 按模块聚合 Design/PRD 需求：同一功能区域只用一个角标，保留原始描述、业务逻辑、前置条件和异常流程。
   完成条件：每个备注均有来源和对应模块。
4. 遍历副本 src/ 下业务 JSX，排除 shared/pm/ 和 dist/；在对应容器添加唯一的 data-pm-mark="N"，必要时使用 data-pm-mark-page="N"。表格标容器，按钮标操作组父容器，表单标 Form 或最外层容器；只插入 data 属性。
   完成条件：关键需求点全部有定位，且同一组件或模块没有重复角标。
5. 按 $BUNDLE/references/prototype-mark-injection.md 注入 annotations.js、MarkLayer.jsx、pm.css，并在 App.jsx 挂载 MarkLayer；content 用单引号包裹，英文单引号转义。
   完成条件：角标和浮窗均由副本源码生成。
6. 验证角标点击开合；X、再次点击同一角标、点击空白处可关闭；同一编号只开一个；弹窗或抽屉打开时主页角标隐藏；位置能避让。重新执行 npm run build。
   完成条件：副本构建通过，交互规则逐项可观察。

## 增量更新

1. 对比现有 Mark 副本与更新后的 Design、PRD 和原型，列出新增、修改、删除项。完成条件：每项差异都有编号和来源。
2. 新增项创建递增角标；修改项只更新 annotations.js 对应内容；删除项移除属性、角标和备注；保持现有标注视觉参数不变。完成条件：没有无关结构或样式变化。
3. 在副本运行 npm run build，并复验来源、角标、浮窗和原始目录保护。完成条件：副本可构建、可标注，原型和正式事实文件未被修改。

## 高影响意见

发现缺失模块、错误状态、权限漏洞等高影响问题时，在报告末尾输出六项：归属层、改什么、改成什么、影响范围、来源、建议处理。建议处理使用 spm-fix 回写 Design；不直接修改 Prototype、Design 或 PRD。

## 硬规则与最终自检

- 角标使用 position: fixed 并挂载到 document.body；不插入目标元素内部。
- 角标点击而非 hover 打开；浮窗与页面事件隔离；主页、Drawer、Modal 容器归属按注入参考处理。
- 标注内容始终标明“内容来源：Design 文件”或“内容来源：prd.md”，不宣称脱离源文件后仍权威。
- 副本 dist/ 只由 npm run build 生成；不使用外部 CDN、不引入 Python 标注脚本、不使用 Unix 专属复制命令或特定 Agent 协议。

最终完成条件：初始化或增量类型明确；副本排除旧构建依赖并构建通过；关键点与来源备注完整；交互和定位规则可观察；原始 Prototype、PRD、Design 未修改；高影响意见已按六项格式输出。
