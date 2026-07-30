# Design 确认/审查顺序根因分析（2026-07-30）

## 结论

当前 ShitPM 流程允许"先确认 Design、后做 Review"，根因是：**系统把"人类确认"与"AI 自校验"解耦成两套互不相通的质量门禁，且下游（PRD/Prototype）的放行卡的是更弱的那套（哈希戳式人类确认），不是更强的那套（含综合审查的编排器技术接受）。**

正确顺序应为：AI 生成 → AI 自校验（结构门禁 + 综合审查，编排器已有）→ 把"已通过验证、可交你确认"的 Design 呈现给用户 → 用户确认。验证必须是"呈现确认"的前置。

## 证据（文件:行号）

### 两套独立门禁，彼此不连
1. **编排器技术接受**（`scripts/python/design-orchestrator.py`）
   - `accept_outputs` @806-813 调用：
     - `_validate_design_writer_upstream` @782-803：要求 a-baseline / b-baseline / c-baseline / design-brief 齐全；full-layered 还校验 `material_revision` 新鲜度。
     - `_validate_comprehensive_review` @760-779：要求 `design-check/v2` + `findings` 数组 + `coverage` 覆盖全部 6 项责任。
   - 这是 AI 自己的验证。
2. **人类确认**（`scripts/python/design-confirmation.py`）
   - 脚本头部自述"最小确认机制"：只记录确认对象、SHA-256 哈希、确认时间。
   - `check` 子命令仅重新计算 `design.md` 哈希并与确认文件比对，一致即 exit 0（start-action-matrix.md:42）。
   - **不查编排器接受状态，不查 review 结果。**

### 下游门禁接的是人类确认（哈希戳），不是编排器接受
- `skills/spm-prd/SKILL.md:30-41`：生成 PRD 前运行 `design-confirmation.py --project-root . check`，"Design 确认 有效"才继续；失败则停止（:157）。
- `skills/spm-prototype/SKILL.md` 同理以"已确认的 Design"为输入。
- 即：只要人类盖了哈希戳，PRD/Prototype 即解锁，无论 AI 是否验证过。

### Review 被显式降权为"非门禁、前后都可选"
- `skills/spm-design/SKILL.md:199`："`spm-design` 不自动执行独立 Review，不自动确认 Design…Review 是用户按需调用的第二意见。"
- `skills/spm-design/SKILL.md:229`："不自动执行 Review、确认或下游生成。"
- `skills/spm-design-review/SKILL.md`："Review 通过不等于 Design confirmation，不自动允许 PRD 或 Prototype"；执行流程第 1 步明确"confirmation 只作为上下文，不构成 Review 门禁"。
- `contracts/start-action-matrix.md:9-10`：review 在"未确认"与"已确认"两种状态均可用，不构成确认前置。

## 为什么这是错的
- 人类被推到"第一验证者"位置去审一份内部高度耦合的大文档；缺失字段、状态闭环断裂、跨层冲突、schema 违规恰恰是自动门禁擅长抓的。
- 确认可以发生在验证之前：用户能对一份从未被 AI 验证的 Design 盖章，随后下游基于未验证 Design 生成。
- 实际后果（本轮会话）：用户在迭代后"确认"，随后对抗性审查（Round 10）才抓出 P1/P2——说明确认的是一份有潜在缺陷、未经 AI 自校验的成品。

## Fix 建议
1. `spm-design`：在发出"请确认 Design"提示前，必须先跑通编排器 `design-editor` 接受（综合审查通过、基线齐全）。未过则呈现验证结果，不催确认。
2. `design-confirmation.py confirm` 增加前置：要求编排器 `design-editor` action 已 accept（或 `comprehensive.json` 存在且 `coverage` 全覆盖、0 P0/P1），否则拒绝盖章。
3. `spm-prd` / `spm-prototype` 的"已确认"判据改为"人类确认 AND 编排器接受/综合审查通过"，而非仅哈希戳。
4. `start-action-matrix.md` 把 review 从"前后都可选"改为"确认前置"。

## 问题 2（traceId JSON）说明
`{"traceId":..., "conversationRequestId":..., "conversationId":...}` 不在 ShitPM 仓库内（全仓 grep 零命中），属平台/基础设施层请求追踪 ID。裸信封（仅 ID、无错误消息/状态码）典型成因是上游服务返回追踪信封而非正常响应（网关/5xx/超时/鉴权/上游模型错误，错误文案被吞或未透传）。确切根因需用户补充：出现位置、触发动作、伴随错误文案/状态码。
