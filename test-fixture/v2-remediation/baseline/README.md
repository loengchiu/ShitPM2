# 批次 0 基准冻结记录

- 冻结日期：2026-07-28
- 仓库：`D:\work\ShitPM`
- 当前分支：`V2`
- 当前提交：`7e4198d`
- 工作区状态：执行冻结前 `git status --short` 为空；未发现用户未提交修改。
- 目标文件 `output/shitpm-v2-remediation-instructions.md` 在执行前无差异。

## 证据边界

仓库内没有 Park 的可执行运行器，也没有带来源证明的 Park 原始产物。因此：

1. `park/` 目录只保存合成基准和缺失证据说明，不声称来自真实 Park；
2. 批次 5 的真实 Park 对比在没有外部 Park 产物或独立评审者时不得写成“通过”；
3. ShitPM 原始产物和旧回归结果可由本仓库复现。

## 基线内容

- `calibration/`：允许在实现期间反复读取和调整的校准样例；
- `retained/`：实现冻结后才启用的保留样例；当前只保存输入哈希和封存说明，不在批次 0–4 读取其正文；
- `simple/`：简单模式短需求集；
- `known-failures/`：五类已知缺陷的合成失败夹具；
- `baseline/regression-2026-07-28.txt`：修改前 28 项回归输出；
- `baseline/manifest.json`：输入和产物哈希清单。
