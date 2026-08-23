# 启动导航报告

## 项目状态

- 当前阶段：
- status.json：存在 / 不存在
- Design 集合：存在（设计地图 + 设计集清单）/ 不存在
- Design 修改状态：无活动事务 / 活动事务（mode、phase）
- 下游受影响模块：无 / 列表

## 产物清单

| 阶段 | 人读 | Review |
|------|------|--------|
| Align | ✅ / ❌ / — | — |
| Design | ✅ / ❌ | ✅ / ❌ / — |
| PRD | ✅ / ❌ | ✅ / ❌ / — |
| Prototype | ✅ / ❌ | ✅ / ❌ / — |

## 最近 Review

无

## 可用动作

| 动作 | 可用 | 模型建议 | 原因 |
|------|------|----------|------|
| /spm-align | ✅ / ❌ |  |  |
| /spm-design | ✅ / ❌ |  |  |
| /spm-prd | ✅ / ❌ |  |  |
| /spm-prototype | ✅ / ❌ |  |  |
| /spm-design-review | ✅ / ❌ |  |  |
| /spm-prd-review | ✅ / ❌ |  |  |
| /spm-prototype-review | ✅ / ❌ |  |  |
| /spm-fix | ✅ / ❌ |  |  |
| /spm-prototype-mark | ✅ / ❌ | 轻量模型 |  |

## 建议

不提供唯一下一步；根据可用动作和模型建议选择。Design 存在活动事务时，先执行 design-set.py recover 再继续下游动作。
