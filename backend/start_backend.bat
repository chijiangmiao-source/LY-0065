@echo off
echo ========================================
echo 理发店管理系统 - 后端启动脚本
echo ========================================

echo.
echo [1/4] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo.
echo [2/4] 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

echo.
echo [3/4] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [4/4] 检查环境变量文件...
if not exist .env (
    copy .env.example .env
    echo 已创建 .env 文件，请根据需要修改配置
)

echo.
echo ========================================
echo 启动 FastAPI 服务...
echo ========================================
echo API 文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo.

uvicorn app.main:app --reload

pause
