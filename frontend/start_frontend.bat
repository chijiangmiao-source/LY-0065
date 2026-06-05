@echo off
echo ========================================
echo 理发店管理系统 - 前端启动脚本
echo ========================================

echo.
echo [1/3] 检查 Node.js 环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js 16+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖...
if not exist node_modules (
    call npm install
) else (
    echo 依赖已安装
)

echo.
echo ========================================
echo 启动开发服务...
echo ========================================
echo 前端地址: http://localhost:3000
echo 按 Ctrl+C 停止服务
echo.

call npm run dev

pause
