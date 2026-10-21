# HR简历筛选系统

这是一个由大语言模型驱动的多 Agent 简历筛选系统。输入职位描述（JD）和候选人简历后，系统完成四件事：分析 JD、解析简历、计算匹配度、检测欺诈风险。

当前模型调用使用 MiniMax 的 `MiniMax-M2.5`（Anthropic 兼容接口 `https://api.minimaxi.com/anthropic`）。未配置密钥或某一步调用失败时，该步降级为仓库里的本地规则脚本。

Web 界面和 REST API 是提交材料、查看结果的运行方式，见下文「运行」。

## 筛选流程

协调器定义在 `.opencode/agents/orchestrator.md`。流程是：orchestrator 接收材料，先做 JD 分析，再解析简历，然后并行做匹配评分和欺诈检测，最后汇总报告。

```
┌──────────────────────────────────────────────────────────┐
│                 orchestrator（主 Agent）                  │
│              接收 JD 与简历，汇总评估报告                   │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    jd-analyzer      │
                 │    分析职位描述       │
                 └─────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   resume-parser     │
                 │      解析简历        │
                 └─────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
   ┌─────────────────────┐     ┌─────────────────────┐
   │       matcher       │     │   fraud-detector    │
   │     计算匹配度        │     │      检测异常        │
   └─────────────────────┘     └─────────────────────┘
              │                           │
              └─────────────┬─────────────┘
                            ▼
                      综合评估报告
```

1. orchestrator 接收 JD 和简历。
2. jd-analyzer 提取职位、技能、职责、经验和学历要求。
3. resume-parser 提取姓名、联系方式、教育、经历、技能和项目。
4. 协调器要求此时并行调用 matcher 与 fraud-detector：前者给出总分和分项匹配，后者给出风险等级和问题列表。Web 请求可以用 `enable_fraud_check` 关掉欺诈检测。
5. 汇总为评估报告。

Web 服务没有拉起 OpenCode 协调器，也不读取 `.opencode/agents/*.md`。`backend/opencode_service.py` 的 `screening()` 用各角色内嵌的系统提示词调用同一个模型，并且是按 jd-analyzer、resume-parser、matcher、fraud-detector 的顺序 `await`。欺诈检测由 `enable_fraud_check` 控制，默认开启。

## Agent

角色和模式以 `opencode.json` 为准。

| Agent | 职责 | 模式 |
|-------|------|------|
| orchestrator | 按上面的步骤协调并汇总报告 | primary |
| jd-analyzer | 分析 JD，提取关键要求 | subagent |
| resume-parser | 解析简历，提取结构化信息 | subagent |
| matcher | 根据 JD 分析与简历解析计算匹配度 | subagent |
| fraud-detector | 检测简历中的不合理之处、作弊行为和虚假信息 | subagent |

提示词里的知识库（`knowledge-base/`）和技能匹配命令（`skill_matcher.py`）只写在这些 Markdown 里。Web 服务的 MiniMax 系统提示词不会加载这些 JSON，也不会调用 `skill_matcher.py` 或 `vector_search.py`。

## 模型来源

每个角色单独选择来源。`_get_fallback_models()` 目前返回空列表，没有第二个在线模型。

| 来源 | `model_source` | 界面文案 | 何时使用 |
|------|----------------|----------|----------|
| MiniMax-M2.5 | `minimax` | MiniMax M2.5 (AI大模型) | 已设置 `MINIMAX_API_KEY` 且该步调用成功 |
| 本地规则脚本 | `local_script` | 本地脚本 (规则匹配) | 未配置密钥，或该步调用失败、返回空、JSON 无法解析 |

汇总字段 `model_source`：任一角色走了 MiniMax 则为 `minimax`，否则为 `local_script`。各角色的实际来源在 `model_sources`。界面在汇总来源为 `local_script` 时提示已使用本地脚本。

## 运行

### 环境

- Python 3.11+（后端镜像 `python:3.11-slim`；`start.sh` 只检查本机有 `python3`）
- Node.js 20+（前端镜像 `node:20-alpine`）
- 可选：`MINIMAX_API_KEY`。不配置时筛选仍可运行，各步使用本地规则脚本

```bash
# 当前终端
export MINIMAX_API_KEY="your-api-key-here"

# 或在 backend/.env（该文件被 git 忽略，需要自己创建）
# MINIMAX_API_KEY=your-api-key-here
```

`start.sh` 会在密钥为空时尝试 `source backend/.env`。手动在 `backend/` 下启动时，`main.py` 通过 `python-dotenv` 读取当前目录的 `.env`。

### 启动

```bash
# 推荐：创建虚拟环境、安装依赖，并启动前后端
./start.sh
```

等价的手动启动：

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8888

# 另一个终端
cd frontend
npm install
npm run dev
```

本地地址：

- Web 界面：http://localhost:3000
- API 文档（FastAPI Swagger）：http://localhost:8888/docs

端口以代码为准，不要和 Docker 混用：

- `start.sh` 把后端固定在 **8888**。直接运行 `main.py` 时默认也是 8888，可用环境变量 `PORT` 覆盖。
- 前端 Vite 固定 **3000**，并把浏览器的 `/api` 代理到 `http://localhost:8888`（见 `frontend/vite.config.ts`）。
- `docker-compose.yml` 把后端映射到宿主机 **8000**（镜像 `EXPOSE` 也是 8000），前端仍是 3000。前端代理目标仍是 8888，不会自动改到 compose 里的后端。

### Web 界面

`frontend/src/App.vue` 提供两个页签：

- **简历筛选**：点击选择 JD 和简历（`.pdf`、`.txt`、`.md`），可勾选是否做欺诈检测，再提交到 `POST /api/v1/screening/file`。结果展示匹配分、技能/经验/学历匹配、风险等级、优势、不足、问题，以及模型来源。上传组件没有开启拖拽。
- **历史记录**：读取 `GET /api/v1/history`，点击一行再请求详情。

后端解析还接受 `.text`。界面上的「API文档」对话框仍写成 PDF/TXT，以实际上传组件和 `parse_uploaded_file()` 为准。

## API

基础路径前缀为 `/api/v1`。另有 `GET /` 与 `GET /api/v1/health` 做健康检查。

### 文本筛选

```bash
POST /api/v1/screening
Content-Type: application/json
```

```json
{
  "jd_content": "职位描述全文",
  "resume_content": "简历全文",
  "options": { "enable_fraud_check": true }
}
```

JD 和简历去掉空白后须至少 20 个字符。成功时 `data` 是 `screening()` 的结果，包含 `match_score`、`skill_match`、`experience_match`、`education_match`、`match_level`、`risk_level`、`advantages`、`disadvantages`、`recommendation`、`issues`、`model_source`、`model_source_display`、`model_sources`、`jd_analysis`、`resume_parsed`。

### 文件筛选

```bash
POST /api/v1/screening/file
Content-Type: multipart/form-data
```

| 字段 | 说明 |
|------|------|
| `jd_file` | 职位描述，PDF / TXT / MD / TEXT |
| `resume_file` | 简历，同上 |
| `enable_fraud_check` | 是否做欺诈检测，默认 `true` |

```json
{
  "success": true,
  "message": "筛选完成",
  "data": {
    "jd_file": "jd.pdf",
    "resume_file": "resume.pdf",
    "match_score": 85,
    "skill_match": "90%",
    "experience_match": "85%",
    "education_match": "80%",
    "match_level": "高度匹配",
    "risk_level": "低",
    "model_source": "minimax",
    "model_source_display": "MiniMax M2.5 (AI大模型)",
    "advantages": [],
    "disadvantages": [],
    "issues": [],
    "recommendation": ""
  }
}
```

文件接口的 `data` 还会带上 `model_sources`、`jd_analysis`、`resume_parsed`。PDF 文本优先用 pdfminer.six 提取，不可用时再用 PyMuPDF。

### 只解析文件

```bash
POST /api/v1/parse
```

表单字段 `file`。成功时 `data` 含 `filename`、`content_length`、`content_preview`（超过 1000 字会截断）和完整的 `full_content`。

### 历史列表

```bash
GET /api/v1/history?limit=20
```

`limit` 默认 20。`data.total` 是本次返回的条数，不是 `results/` 下的全部文件数。每条含 `id`、`timestamp`、`position`、`candidate`、`match_score`、`match_level`、`risk_level`、`model_source`、`model_source_display`。`id` 是结果文件名去掉 `.json`。

### 历史详情

```bash
GET /api/v1/history/{record_id}
```

返回保存文件的内容：`timestamp`、截断后的 `jd_content` 与 `resume_content`（各最多 500 字，更长时加 `...`）、以及 `result`。记录不存在时 `success` 为 `false`。

筛选结束会把结果写到 `results/`，文件名形如 `{时间}_{职位}_match{分数}.json`。

## 目录

```
├── backend/
│   ├── main.py                 # FastAPI 路由
│   ├── opencode_service.py     # 按角色调用模型，并含本地规则回退
│   ├── pdf_parser.py           # PDF 文本提取
│   ├── requirements.txt
│   └── Dockerfile              # 容器内端口 8000
├── frontend/
│   ├── src/App.vue
│   ├── src/main.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts          # 端口 3000，/api 代理到 8888
│   └── Dockerfile
├── .opencode/
│   ├── agents/                 # 五个 Agent 的提示词
│   └── tool/                   # 自定义 OpenCode 工具（与筛选 API 无关）
├── opencode.json               # Agent 名称、模式、提示词路径
├── knowledge-base/             # 技能映射、公司信息、评分标准、向量配置
├── skill_matcher.py            # 供 Agent 提示词引用的技能匹配命令
├── vector_search.py            # 独立的本地向量检索脚本
├── vector-store/               # 向量索引数据
├── requirements-vector.txt
├── samples/                    # jd.txt、resume.txt，以及一份 PDF 简历样例
├── results/                    # 筛选结果 JSON
├── docker-compose.yml          # 后端宿主机端口 8000，前端 3000
├── start.sh
├── ports.json                  # 空文件；服务端口不读取它
└── AGENTS.md
```

`backend/.env` 不在仓库里，需要本机创建。
