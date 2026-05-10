# ShitPM 新辅助器使用说明

## 简介

新辅助器是一套 AI 辅助的项目规范化工具链，用于将自然语言需求通过四个阶段（align → design → prd → prototype）逐步转化为结构化产物。

## 快速开始

### 1. 创建对齐文档

在 `output/align/align.md` 中写出原始需求，然后运行：

```bash
python scripts/python/stage-prep.py --stage align
```

### 2. 运行完整链路

按顺序生成每个阶段的产物，每个阶段完成后运行对应的 `stage-prep.py`：

| 阶段 | 产物路径 | 机读元数据路径 |
|------|---------|--------------|
| align | `output/align/align.md` | `.workflow/metadata/align/` |
| design | `output/design/design.md` | `.workflow/metadata/design/` |
| prd | `output/prd/prd.md` | `.workflow/metadata/prd/` |
| prototype | `output/prototype/index.html` | `.workflow/metadata/prototype/` |

每个阶段完成后执行：

```bash
python scripts/python/stage-prep.py --stage <阶段名>
```

### 3. 检查状态

```bash
# 查看当前工作流状态和门控检查
python scripts/python/stage-context.py .

# 检查 PRD 文案风格
python scripts/python/prd-style-lint.py output/prd/prd.md
```

## 关键脚本

| 脚本 | 功能 |
|------|------|
| `stage-prep.py` | 从人读产物生成机读元数据（index、entities、relations、anchors 等） |
| `stage-context.py` | 读取 `status.json`，进行门控检查，判断下一阶段是否可以进入 |
| `prd-style-lint.py` | PRD 风格检查（8 项规则：禁止标签式文案、禁止流水账叙事、禁止空占位等） |

## 目录结构

```
ShitPM/
├── output/                     # 人读产物（design.md / prd.md / index.html）
├── .workflow/
│   ├── status.json             # 工作流状态中枢（当前阶段、产物路径、审查记录）
│   ├── metadata/               # 机读元数据（由 stage-prep.py 自动生成）
│   │   ├── align/
│   │   ├── design/
│   │   ├── prd/
│   │   └── prototype/
│   └── reviews/                # 人读审查结果（design-review-1.json 等）
├── scripts/python/             # 工具脚本
├── schemas/                    # JSON Schema（output.schema.json、review-result.schema.json 等）
├── templates/                  # 产物模板
└── .archive/                   # 旧项目归档
```

## 常用流程

**完整走一遍：**

```bash
# 1. 写好 output/align/align.md 后
python scripts/python/stage-prep.py --stage align

# 2. 基于 align 写 design
python scripts/python/stage-prep.py --stage design

# 3. 基于 design 写 prd
python scripts/python/stage-prep.py --stage prd
# 检查风格
python scripts/python/prd-style-lint.py output/prd/prd.md

# 4. 基于 prd 做 prototype
python scripts/python/stage-prep.py --stage prototype

# 5. 最终一致性检查
python scripts/python/stage-context.py .
```

## 归档旧项目

```bash
# 将当前 output 归档到 .archive/
mkdir -p .archive/项目名-日期
cp -r output/* .archive/项目名-日期/
# 清空 output 开始新项目
```
