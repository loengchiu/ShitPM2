# 原型系统（Prototype）

## 用户操作

请双击 `原型工具.bat`，按数字选择操作：

1. 启动本地即时预览
2. 构建并预览发布版本
3. 重新构建部署包
4. 上传到 Cloudflare（需先由 AI 配置项目）
5. 修复依赖并重新构建
0. 退出

全程无需使用 PowerShell，也无需手动输入命令。

## 面向 AI 与研发（附录，不作为用户操作步骤）

- `npm ci`：按锁文件安装依赖
- `npm run dev`：本地开发预览（固定端口 5173）
- `npm run build`：构建 `dist/`
- `npm run preview`：构建产物预览（固定端口 4173）
- 唯一编辑源：`src/`；`dist/` 是可重建产物，禁止直接修改
- Cloudflare：`wrangler.toml` 保存已确认的 Pages 项目名（`name = "..."`）与构建目录（`pages_build_output_dir = "dist"`），账号与令牌不写入项目文件；未配置时上传选项会停止并提示
- 配置示例（由 AI 在用户确认项目名后生成，模板不预置）：
  `name = "pages-project-name"` + `pages_build_output_dir = "dist"`
