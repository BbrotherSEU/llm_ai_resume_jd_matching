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

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 虚拟环境目录
VENV_DIR="$SCRIPT_DIR/venv"

# 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "[配置] 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败"
        exit 1
    fi
    echo "[配置] 虚拟环境创建成功"
fi

# 激活虚拟环境
echo "[配置] 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 验证激活成功
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo "警告: 虚拟环境激活失败，将尝试使用系统Python"
    PYTHON_CMD="python3"
    PIP_CMD="pip"
else
    echo "[配置] 虚拟环境已激活: $VIRTUAL_ENV"
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

# 清理已有进程
echo "[0/5] 清理已有进程..."

# Windows 下通过进程名查找并关闭
kill_by_name() {
    local name=$1
    # 使用 tasklist 查找进程
    local pids=$(tasklist 2>/dev/null | grep -i "$name" | awk '{print $2}')
    if [ -n "$pids" ]; then
        for pid in $pids; do
            if [ "$pid" != "0" ] && [ "$pid" != "" ]; then
                echo "  关闭进程 $name (PID: $pid)"
                taskkill //F //PID $pid 2>/dev/null
            fi
        done
    fi
}

# Unix/Linux 下通过进程名查找并关闭
kill_by_name_unix() {
    local name=$1
    local pids=$(pgrep -f "$name" 2>/dev/null)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "  关闭进程 $name (PID: $pid)"
            kill $pid 2>/dev/null
        done
    fi
}

# 根据操作系统选择清理方式
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    kill_by_name_unix "uvicorn"
    kill_by_name_unix "node"
else
    kill_by_name "uvicorn"
    kill_by_name "python.exe"
    kill_by_name "node.exe"
    kill_by_name "npm.exe"
fi

echo "  清理完成"

# 安装后端依赖
echo "[1/5] 安装后端依赖..."
cd "$SCRIPT_DIR/backend"
$PIP_CMD install -r requirements.txt
cd "$SCRIPT_DIR"

# 安装前端依赖
echo "[2/5] 安装前端依赖..."
cd "$SCRIPT_DIR/frontend"
npm install
cd "$SCRIPT_DIR"

# 启动后端（后台运行）
echo "[3/5] 启动后端服务 (端口8888)..."
cd "$SCRIPT_DIR/backend"
$PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port 8888 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# 等待后端启动
sleep 3

# 启动前端（后台运行）
echo "[4/5] 启动前端服务 (端口3000)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "================================"
echo "服务启动完成!"
echo "前端界面: http://localhost:3000"
echo "API文档: http://localhost:8888/docs"
echo "================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
