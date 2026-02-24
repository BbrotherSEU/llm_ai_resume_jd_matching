# HR简历筛选系统

这是一个基于大模型的多Agent简历筛选系统，用于HR进行职位描述(JD)与简历的匹配度评估及欺诈检测。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (主Agent)                   │
│                    协调整个筛选流程                           │
└─────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
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

## 快速开始

### 方式一：本地启动（推荐）

```bash
# 1. 克隆项目后，进入目录
cd hr-screening-system

# 2. 运行启动脚本（Windows用户可直接双击或在Git Bash中运行）
./start.sh

# 或手动启动：
# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload

# 前端（新开终端）
cd frontend
npm install
npm run dev
```

启动后访问：
- Web界面: http://localhost:3000
- API文档: http://localhost:8000/docs

### 方式二：Docker部署

```bash
# 使用Docker Compose一键启动
docker-compose up -d
```

## 项目结构

```
hr-screening-system/
├── backend/                    # FastAPI后端服务
│   ├── main.py                 # 主程序入口
│   ├── pdf_parser.py           # PDF解析模块
│   ├── requirements.txt        # Python依赖
│   └── Dockerfile
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
└── samples/                   # 样本数据
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
