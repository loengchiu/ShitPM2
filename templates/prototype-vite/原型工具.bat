@echo off
setlocal EnableExtensions
chcp 65001 >nul
title 原型工具
cd /d "%~dp0"

set "CF_PROJECT="

:menu
cls
echo.
echo  ============================================
echo   原型工具
echo   当前项目：%CD%
echo  ============================================
echo.
echo    1. 启动本地即时预览
echo    2. 构建并预览发布版本
echo    3. 重新构建部署包
echo    4. 上传到 Cloudflare
echo    5. 修复依赖并重新构建
echo    0. 退出
echo.
set "choice="
set /p "choice=请选择操作后按回车："
if "%choice%"=="1" goto dev
if "%choice%"=="2" goto buildpreview
if "%choice%"=="3" goto rebuild
if "%choice%"=="4" goto upload
if "%choice%"=="5" goto fixdeps
if "%choice%"=="0" exit /b 0
goto menu

:checkenv
where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Node.js，请先安装 Node.js 后重试。
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 npm，请检查 Node.js 安装。
  pause
  exit /b 1
)
if not exist "package.json" (
  echo [错误] 当前目录不是原型工程（缺少 package.json）。
  pause
  exit /b 1
)
if /i not "%CD%\"=="%~dp0" (
  echo [错误] 当前目录与脚本所在目录不一致，已停止。
  pause
  exit /b 1
)
exit /b 0

:ensure_deps
if exist "node_modules" exit /b 0
echo 首次运行，正在按锁文件安装依赖（npm ci）...
call npm ci
if errorlevel 1 (
  echo [错误] 依赖安装失败，请把上方错误信息转交给 AI。
  pause
  exit /b 1
)
exit /b 0

:dev
call :checkenv
if errorlevel 1 goto menu
call :ensure_deps
if errorlevel 1 goto menu
echo 正在启动本地即时预览：http://localhost:5173/
start "" "http://localhost:5173/"
call npm run dev
echo.
echo 本地预览已停止，按任意键返回菜单。
pause >nul
goto menu

:buildpreview
call :checkenv
if errorlevel 1 goto menu
echo 正在构建发布版本...
call npm run build
if errorlevel 1 (
  echo [错误] 构建失败，未启动预览；请把上方错误信息转交给 AI。
  pause
  goto menu
)
echo 正在启动构建预览：http://localhost:4173/
start "" "http://localhost:4173/"
call npm run preview
echo.
echo 构建预览已停止，按任意键返回菜单。
pause >nul
goto menu

:rebuild
call :checkenv
if errorlevel 1 goto menu
echo 将删除本项目的 dist 目录并重新构建（src、配置和其他文件不受影响）。
if exist "dist" rmdir /s /q "dist"
call npm run build
if errorlevel 1 (
  echo [错误] 构建失败；请把上方错误信息转交给 AI。
  pause
  goto menu
)
echo 构建完成，dist 目录：%CD%\dist
explorer "%CD%\dist"
pause
goto menu

:upload
call :checkenv
if errorlevel 1 goto menu
if not exist "wrangler.toml" (
  echo [提示] 尚未配置 Cloudflare 项目（缺少 wrangler.toml）。
  echo        请让 AI 完成配置后重试；本工具不会要求你手动输入部署命令。
  pause
  goto menu
)
REM 从 wrangler.toml 读取项目名用于展示（取 name = 这一行）
set "CF_PROJECT="
for /f "tokens=2 delims==" %%i in ('findstr /i /b "name" wrangler.toml') do set "CF_PROJECT=%%i"
set "CF_PROJECT=%CF_PROJECT:"=%"
set "CF_PROJECT=%CF_PROJECT: =%"
if "%CF_PROJECT%"=="" (
  echo [错误] wrangler.toml 未配置 name，请让 AI 重新配置。
  pause
  goto menu
)
echo 将先重新构建，然后上传 dist 到 Cloudflare Pages 项目：%CF_PROJECT%
set "confirm="
set /p "confirm=确认上传请输入 Y 后回车（其他任意键取消）："
if /i not "%confirm%"=="Y" (
  echo 已取消上传。
  pause
  goto menu
)
call npm run build
if errorlevel 1 (
  echo [错误] 构建失败，未上传任何内容；请把上方错误信息转交给 AI。
  pause
  goto menu
)
echo 正在上传：首次使用会自动打开浏览器完成 Cloudflare 授权，请在弹出的页面中允许后回到本窗口...
call npx --yes wrangler pages deploy "dist"
if errorlevel 1 (
  echo.
  echo [错误] 上传失败。常见原因与处理：
  echo   1) 未登录 Cloudflare：wrangler 会自动打开浏览器授权；若未弹出，请把上方错误信息转交 AI。
  echo   2) 网络无法访问 Cloudflare：确认公司网络能打开 https://dash.cloudflare.com
  echo   3) 项目名冲突：修改 wrangler.toml 里的 name 后重试。
  echo   上方错误信息也请一并转交给 AI。
  pause
  goto menu
)
echo.
echo 上传完成。Cloudflare Pages 控制台可查看部署地址与历史。
echo.
echo ── 访问/分享地址 ──────────────────────────────
echo   请用「生产域名」（固定、公司网络已放行）：
echo     https://%CF_PROJECT%.pages.dev
echo   部署日志末尾打印的 hash 子域每次部署都会变化，不要用作分享地址。
echo ───────────────────────────────────────────────
pause
goto menu

:fixdeps
call :checkenv
if errorlevel 1 goto menu
echo 正在按锁文件重新安装依赖（npm ci）...
call npm ci
if errorlevel 1 (
  echo [错误] 依赖安装失败，请把上方错误信息转交给 AI。
  pause
  goto menu
)
echo 正在清理 dist 并重新构建...
if exist "dist" rmdir /s /q "dist"
call npm run build
if errorlevel 1 (
  echo [错误] 构建失败；请把上方错误信息转交给 AI。
  pause
  goto menu
)
echo 修复完成。
pause
goto menu
