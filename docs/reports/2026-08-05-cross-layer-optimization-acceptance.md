# 跨层缺陷优化验收报告（A-01~A-12）

> 日期：2026-08-05
> 执行依据：`docs/plans/2026-08-04-skill-defect-cross-layer-optimization-execution-and-acceptance.md` §7 验收标准
> 背景：R17 审查确认 12 项缺陷在 Design/PRD 双链有规则落点（10 完整 + 2 部分），但方案 §4 阶段 4/5 的执行验收未做（R17 P2-1、R18 P2-3a）。本报告补执行证据。
> 验证方式（两层）：①隔离样本——`test-fixture`（完整 design + prd，54 页/401 字段/10 模块）跑 `prd-consistency-check.py`，验证检查器三类输出（A-05/A-12）；②真实项目模块样本——审计系统副本 `D:/ShitPM-tmp/audit_copy` 的 `module-draft-底稿作业.md`（按当前规则分片生成），逐项回读 A-01~A-11。

## 一、结论

**通过**。12 项缺陷的规则落点在隔离样本与真实项目模块样本上均可回读；检查器输出明确区分确定性冲突 / 语义判断项；权限不可评估有显式语义（A-12）；未修改用户正式项目，未执行 commit/push。

## 二、检查器三类输出实证（A-05、A-12）

`prd-consistency-check.py --project-root test-fixture` 输出（exit_reason=deterministic_conflict）：

| 输出类别 | 数据 | 对应验收 |
|---|---|---|
| `classification.deterministic_conflicts`（确定性冲突） | fields + field_enums，含 2 个 deterministic=true 的 enum 冲突（如"用户类型"多选枚举值差异） | A-05 第①类 |
| `fields.attribute_mismatch[].deterministic=false`（语义判断项） | 25 项（"计划版本""项目编号""审计单位"等 enum/长度差异，需人工判定） | A-05 第③类 + 结构适配差异 |
| `permission_evaluation.status=extracted` + "仍需人工对照 Design 权限矩阵核对" | 权限不可全自动评估有显式语义 | A-12 |
| `fields.missing=0 / hallucinated=0` | 无确定性遗漏/幻觉 | A-12 |

说明：spm-prd-review 已在本轮补充显式命名——检查器三类输出（确定性冲突 / 可能遗漏 / `needs_semantic_judgment` 含**结构适配差异**）由 Review 按业务语义判定，不因脚本无法确认而默认通过（R17 P2-4 修复）。

## 三、A-01~A-12 逐项核对（真实项目模块样本）

样本：`D:/ShitPM-tmp/audit_copy/output/prd/module-draft-底稿作业.md`（306 行，design.md 4565 行副本分片生成）。

| 验收 | 样本证据（行号） | 判定 |
|---|---|---|
| A-01 无权限/加载/空态/异常/超长/默认值/标签色值 | L127"加载中骨架屏；空状态'暂无底稿数据…'；超长截断 30 字符悬停全文；彩色标签；只读"；L209"无权限进入按权限规则处理；附件下载" | ✅ |
| A-02 页面区块/字段/操作/条件显隐可回读 | L128"编辑/删除仅状态=草稿时可用；删除置灰时提示不可删除原因"；页面含区块字段表 | ✅ |
| A-03 待办/编号/字典/文件/归档逐项判定 | 字典：L60/65"字典取值"；待办：反馈首页待办（design 定义，样本引用）；归档：本模块无归档场景（design 未定义，不补造） | ✅ |
| A-04 分页/导出/批量/首页/文件限制分开 | 批量：L20"批量初审/批量复核"+L128"按勾选数据状态控制可用性"；本模块 design 未定义分页/导出/文件限制 → PRD 不补造（符合"无事实不补"） | ✅ |
| A-05 三类输出区分 | 见 §二 | ✅ |
| A-06 审计侧/被审侧入口可回读 | L19/20 角色与数据范围；L209"被审单位反馈意见"；入口/菜单/路由在页面职责中 | ✅ |
| A-07 完成条件可定位 | L294"4.x.8 验收标准"章节存在，验收写业务结果/状态/权限 | ✅ |
| A-08 自动动作失败闭环 | L45/48"复核通过自动生成审计问题（状态=待定性）"；L33-35 复核驳回→正在征求（失败路径） | ✅ |
| A-09 枚举有来源 | L77"底稿状态：枚举，所有用户只读"；L60/65"字典取值"；无裸"枚举/字典"占位 | ✅ |
| A-10 删除传播 | L23"删除仅限草稿状态，软删除，二次确认'删除后不可恢复'"；L19/33 撤回路径 | ✅ |
| A-11 状态驱动展示 | L99/128"初审意见仅在'正在初审'且主审时可编辑；提交后按钮置灰；删除置灰提示原因"；L216"已审核后撤回按钮隐藏" | ✅ |
| A-12 三处交叉比较/引用/重验收/权限语义 | 检查器跑通（§二）；模块引用指向 design 事实；样本声明"未一次性全读 design.md" | ✅ |

## 四、测试

跨层优化涉及的测试套件全绿（本报告写于 R18 修复后）：test-prd-consistency-semantics / test-prd-style-lint / test-prd-simplification / test-design-simplification / test-design-index / test-context-loading 等 12/12。

## 五、边界说明

- 样本仅覆盖"底稿作业"一个模块（真实项目分片重生成仅此模块获得授权）；其余 8 个闭环的 PRD 重生成需用户另行决定（与 fragment-reading 遗留一致）。
- A-04 的分页/导出/文件限制在本模块无 design 事实，验证的是"不补造"而非"有落点"；此类规则已在 test-fixture 的完整 PRD 与规则文本（rules §8.1、Review 检查项）中体现。
- 未修改用户正式项目；未执行 commit/push。
