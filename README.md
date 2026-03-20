# FlowTrace 🚀

**FlowTrace** 是一个轻量级、实时、可私有化部署的 API 请求追踪与回放工具。它旨在帮助开发者在复杂的分布式系统或微服务开发中，轻松捕获、观察并重放 HTTP 请求，彻底告别盲目调试。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-green.svg)

---

## ✨ 核心特性

- **无侵入追踪**：通过轻量级中间件或 API 节点捕获完整的 HTTP 流。
- **实时控制台**：基于 WebSocket 的前端界面，无需刷新即可实时看到请求流入。
- **请求回放 (Replay)**：支持一键重放历史请求，快速复现 Bug。
- **安全合规**：所有数据存储在您的本地数据库中，确保数据隐私。
- **轻量易用**：基于 Flask 与 Vanilla JS 构建，部署极简。

## 🛠️ 技术栈

- **后端**: Python 3.12+, Flask, PyMySQL
- **前端**: 原生 JavaScript (ES6+), CSS3, HTML5
- **数据库**: MySQL / MariaDB
- **包管理**: [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone [https://github.com/your-username/FlowTrace.git](https://github.com/your-username/FlowTrace.git)
cd FlowTrace
```

### 2. 环境配置
复制环境变量模板并根据实际情况修改数据库连接信息：
```bash
cp backend/.env.example backend/.env
```
编辑 `backend/.env`，填写您的 MySQL 配置。

### 3. 安装依赖
推荐使用 uv 进行快速安装：

```bash
cd backend
uv sync
```

### 4. 运行应用
```bash
# 启动后端服务
python app.py
```

默认情况下，后端运行在 `http://127.0.0.1:5000`。
您可以直接打开 `frontend/index.html` 访问管理控制台。

### 📂 项目结构
```plaintext
FlowTrace/
├── backend/
│   ├── src/flowtrace/      # 核心逻辑 (路由、重放、数据库)
│   ├── app.py              # 程序入口
│   └── pyproject.toml      # 依赖管理
├── frontend/
│   ├── index.html          # 主界面
│   ├── main.js             # WebSocket 与交互逻辑
│   └── style.css           # 样式
└── README.md
```

### 🔒 安全性说明
**数据隐私**：`FlowTrace` 默认不上传任何数据到外部服务器。

**敏感信息屏蔽**：建议在 `validation.py` 中配置敏感 Header（如 Authorization）的过滤规则。

### 🗺️ 路线图 (Roadmap)
- [ ] 支持请求参数的“编辑后重放”

- [ ] 导出请求为 cURL 命令或 Postman Collection

- [ ] 多用户协作与团队工作区 (Team Workspace)

- [ ] 智能请求异常分析 (AI Insights)

### 📄 许可证
本项目采用 `MIT License` 开源。

### 🤝 贡献与反馈
如果您有任何问题或建议，欢迎提交 `Issue` 或 `Pull Request`。
提示：如果您在企业环境中使用并需要高级支持（如私有化集群部署、自动化测试集成），请通过邮件联系：`lhawzed@gmail.com`