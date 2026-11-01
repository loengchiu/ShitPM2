# Prototype Mark 主规格层迭代执行报告

> 日期：2026-10-20
> 状态：已完成（仓库改造与临时验收）
> 执行依据：`D:/work/ShitPM/docs/plans/2026-10-20-spm-prototype-mark-primary-spec-iteration-plan.md`
> 决策：用户于 2026-10-20 确认“仅进入测试的页面强制完成 Mark；复杂页面用深度推理，简单增量可用轻量模型；Design 权威，PRD 可选且不得混合”。

## 1. 执行结果

`spm-prototype-mark` 已从“原型标注副本生成”调整为“原型主规格层”：

- 只承载原型无法直接展示、且会影响研发实现或测试判断的内容；
- 已可见的字段、按钮、布局和普通交互不再重复写入 Mark；
- 页面完成判据改为“只打开带标注原型、不打开 PRD，也能完成实现和验收判断”；
- 标注内容按 section 组织，并显示具体来源和已确认/待确认状态；
- 无可承接位的规格必须报告，不得硬挂；
- 进入测试的页面强制完成 Mark；进入研发的页面可提前完成，早期探索原型不强制。

本轮没有新增检查脚本、Schema、metadata 或中间回执。

## 2. 实际修改

| 文件 | 修改 |
|---|---|
| `D:/work/ShitPM/skills/spm-prototype-mark/SKILL.md` | 重写内容门槛、不可见规格提取、可见事实阻断、无承接位、增量更新和最终自检 |
| `D:/work/ShitPM/references/prototype-mark-injection.md` | 标注数据改为 sections/source/status；增加分 section 展示、来源状态和空白点击关闭 |
| `D:/work/ShitPM/skills/spm-prototype/SKILL.md` | 删除 Prototype Skill 对 Mark 实现规则的重复维护，改为转交 `spm-prototype-mark` |
| `D:/work/ShitPM/USAGE.md` | 同步 Mark 的新定位、完成判据和强制范围 |
| `D:/work/ShitPM/contracts/start-action-matrix.md` | 模型建议改为按语义复杂度判断 |
| `D:/work/ShitPM/scripts/python/stage-context.py` | 同步动作模型建议和运行时动作说明 |
| `D:/work/ShitPM/docs/plans/2026-10-20-spm-prototype-mark-primary-spec-iteration-plan.md` | 记录确认后的执行决策和验收结论 |

## 3. 验证证据

### 3.1 规范层

- 搜索目标文件后，未再发现“按模块聚合全部 Design/PRD 内容”“内容来源：Design 文件”的旧泛称、默认浅层模型等冲突表述。
- `stage-context.py` 实际输出：

```text
model_tier: 根据语义复杂度判断（复杂页面用深度推理模型，简单增量可用轻量模型）
reasoning_depth: 首次或复杂页面需深；只做已确认事实的简单增量可浅。
```

- `python -m py_compile scripts/python/stage-context.py` 通过。

### 3.2 实现层

- 从 `references/prototype-mark-injection.md` 直接抽取 `annotations.js`、`MarkLayer.jsx`、`pm.css` 注入临时 Vite 工程。
- `npm ci` 成功，`npm run build` 成功，3698 个模块完成转换。
- Playwright 实际打开标注页面并点击角标，确认：
  - 多 section 正常显示；
  - 来源显示到文件和章节；
  - `confirmed` 显示为“已确认”；
  - `pending` 显示为“待确认”；
  - 点击页面空白处可关闭浮窗。

### 3.3 仓库回归

- `python scripts/python/test-shitpm-regression.py`：通过，4 个回归层用例、4 个直接测试脚本。
- `python -m pytest scripts/python/test-context-runtime.py scripts/python/test-context-loading.py -q`：2 passed。
- `git diff --check`：无空白错误；`USAGE.md` 保留原有 CRLF，其余目标文件保持 LF/UTF-8 无 BOM。

### 3.4 主规格试读

临时标注中的内容可以回答以下问题，且不需要打开 PRD：

- 合同在什么状态下可编辑：仅草稿状态。
- 删除合同的副作用：同步删除关联账单；删除失败整体回滚。
- 一线角色能否删除：不显示删除。
- 管理员删除范围：仅本服务区。
- 审批中合同能否编辑或删除：不能。
- 盘点超期后能否继续录入：不能，且页面显示该事实为待确认。

该试读验证了 Mark 能承载实现规则、权限、状态、异常和验收判断，但不是实际研发或测试人员试用。

## 4. 未验证内容

- 尚未在真实项目中让研发和测试按“只读带标注原型”的方式实际工作。
- 尚未评估存量项目 Mark 的迁移成本和内容质量。
- 尚未验证 `spm-start` 是否应在试点后主动推荐 Mark。
- 现有 Mark 的其他交互能力（拖拽、导航栏、复杂容器归属）不在本轮范围内。

## 5. 结论

仓库级规范、实现和临时产物验收已完成。Mark 现在以“原型不可见规格层”运行，下一阶段应在真实项目试点验证研发/测试是否能在不打开 PRD 的情况下稳定完成实现和验收。
