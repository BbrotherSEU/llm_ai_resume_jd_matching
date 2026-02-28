# HR简历筛选系统

这是一个基于大模型的多Agent简历筛选系统，用于HR进行职位描述(JD)与简历的匹配度评估及欺诈检测。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (主Agent)                   │
│                    协调整个筛选流程                           │
└─────────────────────────────────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  JD Analyzer  │    │Resume Parser  │    │ Fraud Detector│
│  分析职位描述  │    │   解析简历    │    │   检测异常    │
└───────────────┘    └───────────────┘    └───────────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                               ▼
                      ┌───────────────┐
                      │    Matcher    │
                      │   计算匹配度   │
                      └───────────────┘
```

## 功能特性

- **PDF解析支持** - 支持上传PDF、TXT格式的JD和简历文件
- **智能匹配** - 基于大模型分析JD与简历的匹配度
- **欺诈检测** - 检测简历中的异常信息和虚假内容
- **Web界面** - 友好的Web UI界面，支持文件拖拽上传
- **REST API** - 提供完整的API接口，支持二次开发
- **模型来源显示** - 清晰展示结果来自AI大模型还是本地脚本
- **筛选历史** - 支持查看历史筛选记录

## 快速开始

### 前置要求

1. **Python 3.11+**
2. **Node.js 20+**
3. **MiniMax API Key** - 用于调用大模型（可选，不配置则使用本地脚本）

### 配置大模型API Key

```bash
# 方式一：设置环境变量（临时）
export MINIMAX_API_KEY="your-api-key-here"

# 方式二：创建 .env 文件（推荐）
# 在 backend/ 目录下创建 .env 文件，内容如下：
# MINIMAX_API_KEY=your-api-key-here

# Windows PowerShell:
# $env:MINIMAX_API_KEY="your-api-key-here"
```

### 启动服务

```bash
# 方式一：使用启动脚本（推荐）
./start.sh

# 方式二：手动启动
# 后端
cd backend
pip install -r requirements.txt
# 创建 .env 文件并设置 MINIMAX_API_KEY
python -m uvicorn main:app --reload --port 8888

# 前端（新开终端）
cd frontend
npm install
npm run dev
```

启动后访问：
- Web界面: http://localhost:3000
- API文档: http://localhost:8888/docs

## 模型说明

系统支持两种模型来源：

| 来源 | 说明 | 配置方式 |
|------|------|----------|
| MiniMax M2.5 | AI大模型，匹配更精准 | 设置 `MINIMAX_API_KEY` 环境变量 |
| 本地脚本 | 规则匹配，无API费用 | 无需配置，失败时自动降级 |

当大模型调用失败时，系统会自动降级到本地脚本，并在界面上显示提示。

## 项目结构

```
hr-screening-system/
├── backend/                    # FastAPI后端服务
│   ├── main.py                 # 主程序入口
│   ├── pdf_parser.py           # PDF解析模块
│   ├── opencode_service.py     # 核心筛选服务
│   ├── requirements.txt        # Python依赖
│   └── .env                    # 环境变量（需创建）
│
├── frontend/                   # Vue3前端界面
│   ├── src/
│   │   ├── App.vue            # 主组件
│   │   └── main.ts            # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml         # Docker部署配置
├── start.sh                   # 启动脚本
│
├── .opencode/                 # Agent配置
│   └── agents/                # 各Agent定义
│
├── knowledge-base/             # 知识库
├── samples/                   # 样本数据
└── results/                   # 筛选结果存储
```

## API接口

### 筛选简历（文件上传）

```bash
POST /api/v1/screening/file

参数:
- jd_file: 职位描述文件 (PDF/TXT)
- resume_file: 简历文件 (PDF/TXT)
- enable_fraud_check: 是否启用欺诈检测 (默认true)

响应:
{
  "success": true,
  "data": {
    "match_score": 85,
    "skill_match": "90%",
    "experience_match": "85%",
    "education_match": "80%",
    "risk_level": "低",
    "model_source": "minimax",
    "model_source_display": "MiniMax M2.5 (AI大模型)",
    "advantages": [...],
    "disadvantages": [...],
    "issues": [...]
  }
}
```

### 解析文档

```bash
POST /api/v1/parse

参数:
- file: 要解析的文件 (PDF/TXT)

响应:
{
  "success": true,
  "data": {
    "filename": "resume.pdf",
    "content_length": 5000,
    "content_preview": "..."
  }
}
```

### 获取筛选历史

```bash
GET /api/v1/history?limit=20

响应:
{
  "success": true,
  "data": {
    "total": 5,
    "items": [
      {
        "id": "20260228_115222_大数据开发工程师_match82",
        "timestamp": "2026-02-28T11:52:22.500756",
        "position": "大数据开发工程师",
        "candidate": "范彬",
        "match_score": 82,
        "match_level": "高度匹配",
        "risk_level": "中",
        "model_source": "minimax"
      }
    ]
  }
}
```

### 获取历史详情

```bash
GET /api/v1/history/{record_id}

响应:
{
  "success": true,
  "data": {
    "timestamp": "...",
    "jd_content": "...",
    "resume_content": "...",
    "result": { ... }
  }
}
```

## Agent 说明

| Agent | 职责 | 模式 |
|-------|------|------|
| orchestrator | 协调整个工作流程 | primary |
| jd-analyzer | 分析JD，提取关键要求 | subagent |
| resume-parser | 解析简历，提取信息 | subagent |
| matcher | 计算匹配度评分 | subagent |
| fraud-detector | 检测简历异常/欺诈 | subagent |

## 配置文件

- `opencode.json` - Agent配置
- `.opencode/agents/` - 各Agent的Prompt定义
- `knowledge-base/` - 知识库配置
- `backend/.env` - 环境变量（API Key）

## 样本数据

- `samples/jd.txt` - 示例职位描述
- `samples/resume.txt` - 示例简历

## 依赖要求

### 后端
- Python 3.11+
- FastAPI
- pdfminer.six / PyMuPDF

### 前端
- Node.js 20+
- Vue 3
- Element Plus
- Vite

## License

MIT
