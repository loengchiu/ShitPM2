# ShitPM 新辅助器使用说明

## 环境准备

- Python 3.10+
- 项目根目录为 `D:\work\ShitPM`（以下命令中的路径按实际位置替换）

## 启动

每次开始工作前，先检查当前状态：

```powershell
python scripts/python/stage-context.py .
```

输出中的 `current_stage` 是当前所处阶段，`next_recommended` 是下一步建议，`gate.can_proceed` 表示是否可以继续。

## 阶段总览

| 步骤 | 阶段 | 做什么 | 谁做 |
|------|------|--------|------|
| 0 | start | 识别当前项目、阶段、入口 | AI（`/spm-start`） |
| 1 | align | 需求对齐，产出对齐稿 | PM + AI（`/spm-align`） |
| 2 | design | 详细设计，产出设计基线 | AI（`/spm-design`） |
| 3 | design-review | 审查设计基线 | PM（`/spm-design-review`） |
| 4 | prd | 生成 PRD 正文 | AI（`/spm-prd`） |
| 5 | prd-review | 审查 PRD | PM（`/spm-prd-review`） |
| 6 | prototype | 生成 HTML 原型 | AI（`/spm-prototype`） |
| 7 | prototype-review | 审查原型 | PM（`/spm-prototype-review`） |

每个 AI 生成步骤完成后，需运行 `stage-prep.py` 同步机读元数据。

## 步骤 0：启动（start）

**AI 要做：** 调用 `/spm-start`，识别当前项目、当前阶段、当前可继续的入口。

新项目（无 status.json）时，AI 会扫描已有产物推断当前阶段。

---

## 步骤 1：需求对齐（align）

**PM 要做：** 使用 `/spm-align` 与 AI 多轮对话，确认需求理解、范围边界、角色场景。

**产出文件：**
- `output/align/align.md` — 对齐稿（人读）
- `.workflow/metadata/align/` — 机读元数据（自动生成）

**运行命令：**
```powershell
python scripts/python/stage-prep.py --stage align
```

**然后：** 运行 stage-context 确认 `next_recommended` 为 `design`，`gate.can_proceed` 为 `true`。

---

## 步骤 2：详细设计（design）

**AI 要做：** 调用 `/spm-design`，基于 align 对齐稿生成设计基线（模块、页面、字段、状态、权限、规则）。

**产出文件：**
- `output/design/design.md` — 设计基线（人读）
- `.workflow/metadata/design/` — 9 个机读 JSON（自动生成）

**运行命令：**
```powershell
python scripts/python/stage-prep.py --stage design
```

**然后：** 进入 design-review。

---

## 步骤 3：设计审查（design-review）

**PM 要做：** 调用 `/spm-design-review`，AI 会自动：
1. 运行 `review-precheck.py --stage design` 做确定性预检查
2. 读取 design.md 和 metadata/design 做质量审查
3. 输出审查结果（通过/有问题需修改/阻塞）

**产出文件：**
- `.workflow/reviews/design-review-1.json` — 机读审查结果
- `.workflow/reviews/design-review-1.md` — 人读审查摘要

**手动预检查（可选）：**
```powershell
python scripts/python/review-precheck.py --stage design
```

**如果不通过：** 先修复问题，重新生成 design，再审查。通过后进入 prd。

---

## 步骤 4：PRD 生成（prd）

**AI 要做：** 调用 `/spm-prd`，基于 design 基线生成 PRD 正文（详细需求说明、数据字典、权限汇总、状态机）。

**产出文件：**
- `output/prd/prd.md` — PRD 正文（人读）
- `.workflow/metadata/prd/` — 6 个机读 JSON（自动生成）

**运行命令：**
```powershell
python scripts/python/stage-prep.py --stage prd
```

**风格自检（可选）：**
```powershell
python scripts/python/prd-style-lint.py output/prd/prd.md --format json --output .workflow/runtime/prd/lint.json
```

**然后：** 进入 prd-review。

---

## 步骤 5：PRD 审查（prd-review）

**PM 要做：** 调用 `/spm-prd-review`，AI 会自动执行预检查和正文质量审查（坏味道、三层覆盖、与 design 一致性）。

**产出文件：**
- `.workflow/reviews/prd-review-1.json` — 机读审查结果
- `.workflow/reviews/prd-review-1.md` — 人读审查摘要

**手动预检查（可选）：**
```powershell
python scripts/python/review-precheck.py --stage prd
```

**如果不通过：** 先修复问题（可能需回 design 同步修复），重新生成 prd，再审查。通过后进入 prototype。

---

## 步骤 6：原型生成（prototype）

**AI 要做：** 调用 `/spm-prototype`，基于 design 基线生成 HTML 业务原型。

**产出文件：**
- `output/prototype/index.html` — 原型页面（人读）
- `.workflow/metadata/prototype/` — 2 个机读 JSON（自动生成）

**运行命令：**
```powershell
python scripts/python/stage-prep.py --stage prototype
```

**然后：** 进入 prototype-review。

---

## 步骤 7：原型审查（prototype-review）

**PM 要做：** 调用 `/spm-prototype-review`，AI 自动检查页面覆盖、状态表达、交互主路径、权限表现。

**产出文件：**
- `.workflow/reviews/prototype-review-1.json` — 机读审查结果
- `.workflow/reviews/prototype-review-1.md` — 人读审查摘要

**手动预检查（可选）：**
```powershell
python scripts/python/review-precheck.py --stage prototype
```

**通过后：** 辅助器全链路完成。`stage-context.py` 的 `next_recommended` 显示 `done`。

---

## 同步修复（fix）

当 review 发现跨阶段问题时（如 design 缺字段 → prd 需同步），使用 fix 链路：

1. 调用 `/spm-fix`，描述要修改的内容和受影响范围
2. AI 按"事实源 → 下游"顺序依次修复各阶段产物
3. 每个阶段修复后运行对应的 `stage-prep.py`
4. 重新运行受影响的 review

```powershell
# 示例：design 加了新字段，同步到 prd 和 prototype
python scripts/python/stage-prep.py --stage design
python scripts/python/stage-prep.py --stage prd
python scripts/python/stage-prep.py --stage prototype
```

---

## 关键脚本速查

| 脚本 | 功能 |
|------|------|
| `stage-context.py .` | 查看当前阶段、门控状态、下一步建议 |
| `stage-prep.py --stage <阶段>` | 从人读产物生成/刷新机读元数据，同步 status.json |
| `review-precheck.py --stage <阶段>` | review 预检查（产物存在、章节完整、metadata 完整、ID 泄漏、lint） |
| `prd-style-lint.py <prd.md>` | PRD 风格检查（坏味道、流水账、模糊表述等 8 项规则） |

---

## 验收标准

全链路完成时应满足：

1. `stage-context.py .` 输出 `next_recommended: "done"`，`gate.can_proceed: true`
2. 三个 review（design / prd / prototype）的 verdict 均为"通过"
3. `review-precheck.py --stage design` / `--stage prd` / `--stage prototype` 均无阻塞项，`can_start_review: true`
4. `git status` 运行产物（metadata/runtime/reviews）不出现在未追踪文件列表中

---

## 常见问题

**Q: `stage-context.py` 报 `gate.can_proceed: false`？**
检查 `blocking_issues` 列表，通常是上游产物缺失或 align-notes 未确认可进入设计。

**Q: `review-precheck.py` 报 `can_start_review: false`？**
检查 `blocking_issues` 列表，通常是产物文件不存在、核心章节缺失或 metadata 文件不完整。

**Q: prd-style-lint 报 STYLE002 警告？**
检查 PRD 正文是否存在连续短步骤（动作流水账），应改写为自然段落，补充展示规则、状态流转和异常边界。

**Q: `stage-context.py` 和 `status.json` 的 `next_recommended` 不一致？**
以 `stage-context.py` 输出为准（它实时计算）。不一致的根因是 `status.json` 由 `stage-prep.py` 在上次运行时写入，可能已滞后于当前产物状态。如果仍不一致，检查 `status.json` 的 `current_stage` 是否正确。
