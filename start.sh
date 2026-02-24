#!/bin/bash
# HR简历筛选系统启动脚本

echo "================================"
echo "HR简历筛选系统 - 本地启动"
echo "================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要安装Python 3.11+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 需要安装Node.js 20+"
    exit 1
fi

# 安装后端依赖
echo "[1/4] 安装后端依赖..."
cd backend
pip install -r requirements.txt
cd ..

# 安装前端依赖
echo "[2/4] 安装前端依赖..."
cd frontend
npm install
cd ..

# 启动后端（后台运行）
echo "[3/4] 启动后端服务 (端口8000)..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端（后台运行）
echo "[4/4] 启动前端服务 (端口3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================"
echo "服务启动完成!"
echo "前端界面: http://localhost:3000"
echo "API文档: http://localhost:8000/docs"
echo "================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
