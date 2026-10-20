# 环境搭建指南（后端 + 前端）

> 全程在 `D:/Code/mine-simulation` 目录下操作。本文档只做环境搭建，不含业务逻辑。
> 已确认本机环境：Python 3.13.14、Node v22.22.2、npm 10.9.7
> 开发工具：VS Code + PowerShell

---

## 技术选型（已确认）

| 层 | 选型 | 说明 |
|---|---|---|
| 前端 | **Vue 3 + TypeScript + Vite + Three.js** | 对齐公司方案 |
| 后端 | **Python + FastAPI** | 需搭配 ASGI 服务器 uvicorn |
| 仿真引擎 | **SimPy** | **不是"后续集成"——阶段 1 竖线就要跑它** |
| 数据校验 | **Pydantic v2** | FastAPI 自带依赖，同时用于前后端契约 |
| 本地存储 | **SQLite** | 阶段 1 先用内存字典 + 抽象层，阶段 3 再落库 |
| 开发工具 | VS Code + PowerShell | 见下方 PowerShell 注意事项 |

**在原选型基础上补充的依赖**（都是必需品，别漏）：

| 包 | 端 | 用途 | 何时用 |
|---|---|---|---|
| `uvicorn[standard]` | 后 | ASGI 服务器 + WebSocket 支持 | 阶段 1 |
| `websockets` | 后 | WebSocket 推送 | 阶段 3 |
| `pytest` | 后 | 单测 | 阶段 1（可复现性测试） |
| `networkx` | 后 | 路网图 + 最短路 | 阶段 2 |
| `echarts` | 前 | 指标图表 | 阶段 4 |
| `pinia` | 前 | 状态管理 | 阶段 1 |
| `openapi-typescript` | 前（dev） | 从契约生成 TS 类型 | 阶段 1 |

**两个建议**：

1. **SimPy 不要往后放**。阶段 1 的竖线就是"前端提交 → SimPy 算 → 返回指标"。把它推到后面，前期就没有任何可跑的东西。
2. **SQLite 可以先不接，但要留好接口**。阶段 1 把任务存在内存字典里没问题（单进程），但要用一个 `TaskStore` 类包起来，阶段 3 换 SQLite 时只改这一个文件，业务代码零改动。这是你 Java 经验里的"面向接口编程"，在这里同样适用。

---

## 0. 目标目录结构

```
mine-simulation/
├── backend/                 ← 后端（Python）
│   ├── .venv/               虚拟环境（不提交 git）
│   ├── core/                仿真内核：engine.py / operators.py / network.py / dispatch.py / stats.py
│   ├── api/                 FastAPI：main.py（路由） / tasks.py（任务表） / schemas.py（Pydantic 模型）
│   ├── tests/               pytest
│   ├── data/                SQLite 数据库文件（不提交 git）
│   ├── requirements.txt
│   └── run.py               启动入口
├── frontend/                ← 前端（Vue3 + Vite）
│   ├── src/
│   │   ├── api/             接口封装（由 OpenAPI 生成的 types 放这里）
│   │   ├── components/      三维场景 / 看板 / 回放控制
│   │   └── views/
│   ├── vite.config.ts
│   └── package.json
├── docs/                    ADR / 压测报告 / 验证报告
├── PRD.md
└── 开发学习计划.md
```

---

## 1. 后端搭建

### 1.1 目录与骨架（已完成）

项目已按下列结构初始化，源码从零开始写，**不保留任何历史原型代码**：

```
backend/
├── main.py          FastAPI 入口（当前只有一个 /api/v1/health）
├── core/__init__.py 仿真内核（阶段 1 起填充）
├── api/__init__.py  接口层（阶段 1 起填充）
└── requirements.txt
```

> 后续所有启动命令都在 `backend/` 目录内执行。

### 1.2 创建虚拟环境

**PowerShell 用户（你用它，重点看这里）**：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

若报"禁止运行脚本"，先执行一次（只需一次，当前用户生效）：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

> 也可以用 VS Code 集成终端，它会自动识别 `.venv`：
> `Ctrl+Shift+P` → `Python: Select Interpreter` → 选 `.\.venv\Scripts\python.exe`

其他 shell：

```bash
source .venv/Scripts/activate        # Git Bash / WSL
.venv\Scripts\activate               # CMD
```

激活后命令行前面会出现 `(.venv)`。**后续所有 pip / python 命令都必须在这个状态下执行。**

### 1.3 安装依赖

> ⚠️ 本机直连 PyPI 会卡住，必须用国内镜像（已实测）

新建 `backend/requirements.txt`：

```txt
fastapi==0.146.0
uvicorn[standard]==0.38.0
pydantic==2.14.1
simpy==4.1.2
networkx==3.4.2
numpy==2.5.4
websockets==15.0.1
pytest==8.4.2
```

安装：

```bash
python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

**依赖说明**（心里有数，别乱装）：

| 包 | 用途 | 备注 |
|---|---|---|
| fastapi + pydantic | Web 框架与数据校验 | 自动生成 OpenAPI |
| uvicorn | ASGI 服务器 | `[standard]` 含 WebSocket 支持 |
| simpy | **离散事件仿真引擎（核心）** | 项目最关键的依赖 |
| networkx | 路网图 + 最短路 | W2 才用 |
| numpy | 统计聚合 | W3 才用 |
| pytest | 单测 | 从第一天就用 |

> **不要装 SQLAlchemy / ORM**。MVP 用 Python 标准库 `sqlite3` 就够，省一个学习负担。

### 1.4 验证后端

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

浏览器打开 **http://127.0.0.1:8000/docs** 能看到 `health` 接口、访问 **http://127.0.0.1:8000/api/v1/health** 返回 `{"status":"ok"}` 即为成功。

另开一个终端验证：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/v1/health
# 期望：{"status":"ok","version":"0.1.0","sim_engine":"simpy"}
```

---

## 2. 前端搭建

### 2.1 创建 Vite + Vue3 项目

在 `mine-simulation/` 下执行（**不要 cd 进 backend**）：

```bash
cd D:/Code/mine-simulation
npm create vite@latest frontend -- --template vue-ts
```

若提示目录非空，选 `y` 继续（web 目前是空目录）。

> 如果 npm 慢，先切镜像：`npm config set registry https://registry.npmmirror.com`

### 2.2 安装依赖

```bash
cd frontend
npm install
npm install three echarts pinia
npm install -D @types/three
```

| 包 | 用途 |
|---|---|
| three | 三维场景渲染（W4 才用，先装好） |
| echarts | 指标图表 |
| pinia | 状态管理 |
| @types/three | TS 类型 |

**阶段 1（竖线）实际只用得上：axios（或原生 fetch）+ 一个页面**。Three.js 先装不必先学。

### 2.3 配置接口代理

编辑 `frontend/vite.config.ts`：

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // WebSocket 必须单独代理，且开启 ws
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})
```

> 这样前端写 `fetch('/api/v1/...')` 即可，不用关心跨域和端口。

### 2.4 验证前端

```bash
cd frontend
npm run dev
```

打开 **http://127.0.0.1:5173**，看到 Vite 欢迎页即为成功。

---

## 3. 联调验证（两个服务同时跑）

| 窗口 | 命令 | 地址 |
|---|---|---|
| 终端 1 | `cd backend && python -m uvicorn main:app --reload --port 8000` | :8000 |
| 终端 2 | `cd frontend && npm run dev` | :5173 |

验证链路：

```bash
# 从前端端口走代理，等价于浏览器请求
curl --noproxy '*' -X POST http://127.0.0.1:5173/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"测试矿区","description":"联调验证"}'
```

返回带 `id` 的工程对象 → **前后端链路打通**。

---

## 4. 从契约生成前端类型（强烈建议）

后端跑着的时候，一键生成 TS 类型，前端不手写接口类型：

```bash
cd frontend
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api/schema.d.ts
```

之后前端这样用：

```ts
import type { components } from './schema'
type SimResult = components['schemas']['SimResult']
```

**契约改了就重新生成一次**，前后端永远不会类型对不上。

---

## 5. .gitignore（根目录新建，别把环境提交上去）

```gitignore
# Python
backend/.venv/
backend/data/
__pycache__/
*.pyc
.pytest_cache/

# Node
frontend/node_modules/
frontend/dist/
frontend/.vite/

# 编辑器 / 系统
.vscode/
.idea/
.DS_Store
```

---

## 6. 常见问题（提前知道，省得踩坑）

| 现象 | 原因 | 解决 |
|---|---|---|
| `pip install` 卡住不动 | 直连 PyPI 超时 | 加 `-i https://mirrors.aliyun.com/pypi/simple/` |
| `npm install` 很慢 | 默认源在国外 | `npm config set registry https://registry.npmmirror.com` |
| curl 访问本地 8000 返回 000 | 系统代理拦截 | `curl --noproxy '*'`，或 unset 代理变量 |
| WebSocket 本地连不上（502） | 同上 | 前端浏览器不受影响；脚本测试需绕过代理 |
| `uvicorn` 命令找不到 | 没激活 venv | 先 `.\.venv\Scripts\Activate.ps1` |
| 前端接口 404 | 代理没配或后端没起 | 检查 `vite.config.ts` 的 proxy 与 8000 端口 |
| 改了 Python 代码没生效 | 没开 `--reload` | 启动时加 `--reload` |
| **PowerShell 里 `curl` 语法报错** | PowerShell 的 `curl` 是 `Invoke-WebRequest` 别名，参数完全不同 | 用 `curl.exe`（真 curl），或 `Invoke-RestMethod -Uri ... -Method Post -Body ... -ContentType 'application/json'` |
| **无法运行 Activate.ps1** | 执行策略限制 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`（只需一次） |
| VS Code 里 import 报红 / 找不到包 | 解释器没指向 venv | `Ctrl+Shift+P` → `Python: Select Interpreter` → 选 `.venv` |

---

## 7. 搭建完成后的检查清单

- [ ] `backend/.venv` 已创建，pip list 能看到 simpy / fastapi
- [ ] `python -m uvicorn main:app --reload` 能起，/health 返回 ok，/docs 可访问
- [ ] `frontend` 项目能 `npm run dev`，浏览器打开有页面
- [ ] 通过 5173 端口能代理调用到 8000 的接口（第 3 节验证通过）
- [ ] `src/api/schema.d.ts` 已生成
- [ ] `.gitignore` 已创建，`git status` 里看不到 `.venv` 和 `node_modules`
- [ ] VS Code 解释器已指向 `backend/.venv`

### VS Code 推荐插件

| 插件 | 用途 |
|---|---|
| Python + Pylance | Python 智能提示 |
| Ruff | Python 语法检查（比 flake8 快） |
| Vue - Official（Volar） | Vue3 支持 |
| REST Client | 在 .http 文件里直接调接口，替代 Postman |
| GitLens | 看提交历史 |

全部打勾后，进入 `开发学习计划.md` 的**阶段 1：打通竖线**。
