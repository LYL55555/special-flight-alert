# Special Flight Alert（特殊航班观察）

通过 [Flightradar24](https://www.flightradar24.com/) 机场时刻表数据（社区 [FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI) SDK），扫描你关心的机场，找出**特殊涂装**、**稀有机型**等值得关注的航班。

本项目以**完全本地运行**为主：API 和网页都在你自己电脑上跑，走家庭宽带 IP 访问 FR24，**不要把 Token 等凭证提交到 Git**。

**English** → [README.md](README.md)

> **免责声明：** 仅供个人学习使用。请遵守 Flightradar24 [服务条款](https://www.flightradar24.com/terms-and-conditions)。商业用途请使用 [官方 FR24 API](https://fr24api.flightradar24.com/)。

---

## 界面预览

**搜索页** — 选择机场，扫描特殊航班。

![搜索界面](img/dash1-cn.png)

**结果列表** — 按航司筛选、按时间排序，查看特殊涂装与飞机照片。

![航班列表](img/dash2-cn.png)

---

## 功能概览

| 模块 | 说明 |
|------|------|
| **网页** (`web/`) | 输入机场码（PVD、JFK、LAX…）搜索，支持中英文界面 |
| **HTTP API** (`api/`) | FastAPI：`GET /api/scan?airport=PVD` |
| **告警引擎** (`alert_engine/`) | 命令行定时扫描、CSV/Excel 输出、可选 Telegram 推送 |
| **MCP** (`mcp_server/`) | 在 Cursor 里让 AI 直接查航班 |

---

## 快速开始（网页 Demo）

**环境要求：** Python 3.10+

```bash
git clone https://github.com/LYL55555/special-flight-alert.git
cd special-flight-alert

# 安装依赖（在仓库根目录执行，不要进 alert_engine 装）
pip install -r requirements.txt

# 可选：Cursor MCP
pip install -r mcp_server/requirements.txt

# 一键启动：API 8000 端口 + 网页 8080 端口
./scripts/run_demo.sh
```

浏览器打开 **http://127.0.0.1:8080**，搜索 **PVD**、**JFK** 或 **LAX**。

按 `Ctrl+C` 停止服务。

### 端口被占用？

```bash
./scripts/stop_demo.sh   # 释放 8000 / 8080，顺带停掉 Docker
./scripts/run_demo.sh
```

### 只启动 API（不要网页）

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

| 地址 | 用途 |
|------|------|
| http://127.0.0.1:8000/ | API 信息 |
| http://127.0.0.1:8000/health | 健康检查 |
| http://127.0.0.1:8000/docs | 接口文档 |
| http://127.0.0.1:8000/api/scan?airport=PVD | 扫描机场 |

---

## 配置说明

### 网页如何连 API

默认配置在 `web/config.js`：

```javascript
window.APP_CONFIG = {
  apiBaseUrl: "http://127.0.0.1:8000",
};
```

如果 API 跑在其他端口，可以复制本地覆盖文件（不会进 Git）：

```bash
cp web/config.local.js.example web/config.local.js
# 修改 apiBaseUrl
```

### 密钥与凭证（Telegram 等）

**切勿把真实 Token 提交到 GitHub。**

```bash
cp alert_engine/.env.example alert_engine/.env
# 编辑 alert_engine/.env，填入 TELEGRAM_BOT_TOKEN、TELEGRAM_CHAT_ID
```

- `.env` 已在 `.gitignore` 中
- 仓库里只有 `.env.example`（空占位符）
- GitHub Actions 如需 Telegram，请在仓库 **Settings → Secrets** 里配置，不要写在代码里

---

## Cursor MCP 用法

1. 安装：`pip install -r mcp_server/requirements.txt` 和 `pip install -r requirements.txt`
2. Cursor 会自动读取 `.cursor/mcp.json`
3. 在对话中说：「用 MCP 扫描 PVD 的特殊航班」

可用工具：`scan_airport`、`health_check`

---

## 告警引擎（命令行）

适合后台监控、导出 CSV/Excel、Telegram 摘要推送：

```bash
cd alert_engine
python main.py --airports PVD          # 单次扫描未来时刻表
python main.py --live --airports BOS   # 实时半径模式
python main.py --loop --poll-seconds 14400
python main.py --help
```

机场列表、评分阈值等在 `alert_engine/config.py` 里调整。  
特殊涂装数据库：`alert_engine/db/special_liveries.csv`。

---

## API 行为说明

- 扫描成功：返回 `count`、`flights` 等字段
- FR24 暂时不可用：返回 **HTTP 200** + `status: "degraded"`（不是 502），网页会提示「实时数据暂时不可用」
- **家庭网络**下数据最稳定；数据中心 IP（Render、GitHub Actions 等）常被 FR24/Cloudflare 拦截，因此项目默认**本地运行**

---

## 目录结构

```
special-flight-alert/
├── api/                 # FastAPI 后端
├── alert_engine/        # 命令行告警引擎
├── web/                 # 静态前端
├── python/              # 内置 FlightRadarAPI SDK
├── mcp_server/          # Cursor MCP
├── scripts/
│   ├── install_deps.sh  # 安装依赖
│   ├── run_demo.sh      # 本地一键 Demo
│   └── stop_demo.sh     # 释放端口
├── requirements.txt     # 根目录 pip install
└── tests/
```

---

## 开发

```bash
pip install -r requirements.txt
python3 -m pytest tests/test_api_routes.py -q
```

---

## 致谢

基于 **[FlightRadarAPI](https://github.com/JeanExtreme002/FlightRadarAPI)**（MIT），详见 `LICENSE`。
