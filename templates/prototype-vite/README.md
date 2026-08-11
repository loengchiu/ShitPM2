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
- Cloudflare：`cloudflare-project.txt` 只保存已确认的 Pages 项目名，账号与令牌不写入项目文件
