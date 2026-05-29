# Filament Manager — 3D 打印耗材管理器

管理 3D 打印机耗材、料盘，通过 MQTT 实时监控打印机状态，自动扣减耗材余量，记录打印任务。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端框架 | Vue 3 (Composition API + `<script setup>`) |
| UI 组件库 | Element Plus |
| 构建工具 | Vite 6 |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| 后端框架 | Python FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite (WAL 模式) |
| MQTT 客户端 | paho-mqtt |
| 数据校验 | Pydantic v2 |
| 容器化 | Docker (多阶段构建) |

---

## 项目结构

```
consumable/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、生命周期、MQTT 端点、SPA 路由
│   │   ├── config.py             # Pydantic Settings（路径、数据库 URL）
│   │   ├── database.py           # SQLAlchemy 引擎、会话、init_db()
│   │   ├── models/
│   │   │   ├── common.py         # TimestampMixin（id, created_at, updated_at）
│   │   │   ├── manufacturer.py   # 厂商
│   │   │   ├── filament.py       # 耗材规格
│   │   │   ├── spool.py          # 料盘
│   │   │   ├── print_record.py   # 打印记录（主表）+ 打印明细（从表）
│   │   │   ├── printer.py        # 打印机配置
│   │   │   ├── mqtt_message.py   # MQTT 消息日志
│   │   │   └── operation_log.py  # 操作日志
│   │   ├── routers/
│   │   │   ├── manufacturers.py  # 厂商 CRUD
│   │   │   ├── filaments.py      # 耗材 CRUD
│   │   │   ├── spools.py         # 料盘 CRUD
│   │   │   ├── print_records.py  # 打印记录查询 + 手动扣减
│   │   │   ├── printer_config.py # 打印机配置 CRUD
│   │   │   ├── dashboard.py      # 仪表盘聚合数据
│   │   │   ├── mqtt_messages.py  # MQTT 消息查询/清空
│   │   │   └── operation_logs.py # 操作日志查询/清空
│   │   ├── schemas/
│   │   │   └── __init__.py       # 所有 Pydantic 请求/响应模型
│   │   └── services/
│   │       ├── mqtt_service.py   # MQTT 客户端、消息解析、自动扣减、打印生命周期
│   │       └── filament_calc.py  # 耗材重量/长度计算
│   ├── requirements.txt
│   └── data/                     # SQLite 数据库文件（运行时生成）
├── frontend/
│   ├── src/
│   │   ├── api/index.ts          # Axios 实例 + 所有 API 方法
│   │   ├── router/index.ts       # 路由配置
│   │   ├── components/
│   │   │   ├── Layout.vue        # 主布局（侧边栏 + 顶栏）
│   │   │   └── PrinterStatusBadge.vue
│   │   └── views/
│   │       ├── Dashboard.vue     # 仪表盘（概览卡片 + AMS 水位图 + 仓库 + 最近记录）
│   │       ├── Manufacturers.vue # 厂商管理
│   │       ├── Filaments.vue     # 耗材管理
│   │       ├── Spools.vue        # 料盘管理
│   │       ├── PrintRecords.vue  # 打印记录（主从表展开）
│   │       ├── PrinterConfig.vue # 打印机配置
│   │       ├── MqttMessages.vue  # MQTT 消息列表
│   │       └── OperationLogs.vue # 操作日志
│   ├── vite.config.ts
│   └── package.json
├── config/
│   └── config.yaml               # 应用配置
├── docker-compose.yml
├── Dockerfile
└── .dockerignore
```

---

## 数据库模型

### 实体关系

```
Manufacturer (厂商)
  └── Filament (耗材规格) — 多对一
        └── Spool (料盘) — 多对一
              └── PrintRecordDetail (打印明细) — 多对一
                    └── PrintRecord (打印记录主表) — 多对一
PrinterConfig (打印机配置) ──→ PrintRecord (一对多)
```

### 各模型字段

**Manufacturer** (`manufacturers`)
| 字段 | 类型 | 说明 |
|------|------|------|
| name | String(128) | 厂商名称（唯一） |
| short_name | String(32) | 简称 |
| description | Text | 描述 |
| website | String(256) | 网站 |

**Filament** (`filaments`)
| 字段 | 类型 | 说明 |
|------|------|------|
| manufacturer_id | FK → manufacturers.id | 所属厂商 |
| name | String(128) | 耗材名称 |
| filament_type | String(32) | PLA / PETG / ABS / TPU / PA / PC / ASA / PET / PP / PVA / OTHER |
| color | String(7) | 十六进制颜色 #RRGGBB |
| color_name | String(64) | 颜色名称 |
| diameter | Float | 线径（默认 1.75mm） |
| density | Float | 密度 g/cm³ |

**Spool** (`spools`)
| 字段 | 类型 | 说明 |
|------|------|------|
| filament_id | FK → filaments.id | 关联耗材规格 |
| name | String(128) | 料盘名称 |
| label | String(64) | 自定义标签 |
| initial_weight | Float | 初始重量(g) |
| current_weight | Float | 当前余量(g) |
| is_active | Boolean | 活跃状态（活跃/闲置） |
| ams_tray | Integer | AMS 位置（0=不在AMS, 1-4=AMS槽位） |
| activated_at | DateTime | 激活时间 |

> **is_active 含义**: 活跃=挂在打印机上使用中（参与 MQTT 自动扣减），闲置=收在仓库里。结合 ams_tray 决定位置显示：`ams_tray>0→AMS`、`活跃+ams_tray=0→EXT`、`闲置→仓库`。

**PrintRecord** (`print_records`) — 主表
| 字段 | 类型 | 说明 |
|------|------|------|
| printer_id | FK → printer_configs.id | 打印机 |
| printer_name | String(64) | 打印机名称（冗余） |
| print_job_id | String(64) | 打印任务 ID（索引） |
| filename | String(256) | GCode 文件名 |
| start_time | DateTime | 打印开始时间 |
| end_time | DateTime | 打印结束时间 |
| status | String(16) | running / finished / failed |

**PrintRecordDetail** (`print_record_details`) — 从表
| 字段 | 类型 | 说明 |
|------|------|------|
| print_record_id | FK → print_records.id | 关联主记录 |
| tray | Integer | 使用的托盘（0=EXT, 1-4=AMS） |
| spool_id | FK → spools.id | 关联料盘 |
| filament_used_mm | Float | 使用长度(mm) |
| filament_used_weight | Float | 使用重量(g) |
| filament_diameter | Float | 线径 |
| deducted | Boolean | 是否已从料盘扣减 |
| remaining_percent_before/after | Float | 打印前后剩余百分比 |

**PrinterConfig** (`printer_configs`)
| 字段 | 类型 | 说明 |
|------|------|------|
| name | String(64) | 打印机名称 |
| serial | String(64) | 序列号（唯一） |
| ip_address | String(64) | IP 地址 |
| access_code | String(64) | MQTT 访问码 |
| port | Integer | MQTT 端口（默认 8883） |
| is_active | Boolean | 启用状态 |

**MqttMessage** (`mqtt_messages`)
| 字段 | 类型 | 说明 |
|------|------|------|
| printer_id | Integer | 打印机 ID |
| printer_name | String(64) | 打印机名称 |
| topic | String(256) | MQTT 主题 |
| payload | Text | 消息体(JSON) |
| received_at | DateTime | 接收时间 |

**OperationLog** (`operation_logs`)
| 字段 | 类型 | 说明 |
|------|------|------|
| action | String(64) | 操作类型（如 printer_connect） |
| target | String(128) | 操作对象 |
| message | String(512) | 详细信息 |
| level | String(16) | 级别: info / warning / error |

---

## API 路由总览

| 前缀 | 方法 | 端点 | 说明 |
|------|------|------|------|
| `/api/manufacturers` | GET/POST | `/` | 厂商列表/创建 |
| | GET/PUT/DELETE | `/{id}` | 厂商详情/更新/删除 |
| `/api/filaments` | GET/POST | `/` | 耗材列表/创建 |
| | GET/PUT/DELETE | `/{id}` | 耗材详情/更新/删除 |
| `/api/spools` | GET/POST | `/` | 料盘列表/创建 |
| | GET/PUT/DELETE | `/{id}` | 料盘详情/更新/删除 |
| `/api/print-records` | GET | `/` | 打印记录列表（支持 ?print_job_id= & ?limit= & ?offset=） |
| | POST | `/details/{detail_id}/deduct` | 手动扣减料盘余量 |
| `/api/printers` | GET/POST | `/` | 打印机列表/创建 |
| | GET/PUT/DELETE | `/{id}` | 打印机详情/更新/删除 |
| `/api/printer/{id}/connect` | POST | | 连接打印机 MQTT（同步等待 5s） |
| `/api/printer/{id}/disconnect` | POST | | 断开打印机 |
| `/api/printer/{id}/status` | GET | | 获取打印机实时状态 |
| `/api/mqtt-messages` | GET | `/` | MQTT 消息列表（支持 ?search= & ?printer_id=） |
| | DELETE | `/` | 清空全部消息 |
| | DELETE | `/{id}` | 删除单条消息 |
| `/api/operation-logs` | GET | `/` | 操作日志列表（支持 ?search= & ?level=） |
| | DELETE | `/` | 清空日志 |
| `/api/dashboard/summary` | GET | `/` | 仪表盘聚合数据 |
| `/api/dashboard/locations` | GET | `/` | 料盘位置分组 |
| `/api/printer/{id}/check-consumption` | POST | | 检查耗材消耗（外部调用） |
| `/api/printer/{id}/print-finish` | GET | | 打印完成回调 |

---

## MQTT 数据流

本项目通过 MQTT 连接 Bambu Lab 系列打印机，实现实时监控和自动扣减。

### 连接流程

```
用户点击"连接"
  → POST /api/printer/{id}/connect
    → manager.get_or_create(p) → PrinterMqttClient.start()
      → connect_async() + loop_start()
    → 同步等待 5 秒（轮询 client.connected）
    → 成功: 返回 {"status": "connected"}, 记录操作日志
    → 失败: 返回 {"status": "failed"}, 记录错误日志
```

### 消息处理流程

```
MQTT Broker → _on_message()
  ├→ _save_message()        → 写入 mqtt_messages 表
  └→ _parse_report()
       ├→ 更新 PrinterStatus（温度、进度、gcode_state）
       ├→ gcode_state: IDLE → RUNNING → _on_print_start()
       │     ├→ 记录开始时间、初始 filament_mm
       │     └→ 重置 _tray_usage 字典
       ├→ gcode_state: RUNNING → _deduct_filament()
       │     ├→ 计算 delta filament_mm
       │     ├→ 归因到当前活跃 tray（记录到 _tray_usage）
       │     ├→ 从对应料盘实时扣减 current_weight
       │     └→ 更新 _last_tray（用于多色切换追踪）
       ├→ gcode_state: RUNNING → FINISH/FAILED → _on_print_end()
       │     ├→ 创建 PrintRecord 主表记录
       │     ├→ 为每个有耗材使用的 tray 创建 PrintRecordDetail
       │     └→ deducted=True（因为实时扣减已完成）
       └→ WebSocket 广播状态
```

### 多色打印支持

- 每次 `_deduct_filament()` 时，将 delta 归因到 `_last_tray`（即上一次 report 时的 tray）
- 当 `tray_now` 变化时，`_last_tray` 会在下一次 deduct 时更新
- 打印结束时，`_tray_usage` 字典中每个 tray 生成一条 PrintRecordDetail
- 同一次打印的多条明细通过 `print_job_id` 关联

---

## 前端视图说明

| 路由 | 组件 | 功能 |
|------|------|------|
| `/dashboard` | Dashboard.vue | 概览卡片、AMS 水位图、打印机实时状态、仓库库存、最近打印记录 |
| `/manufacturers` | Manufacturers.vue | 厂商 CRUD |
| `/filaments` | Filaments.vue | 耗材 CRUD（选择厂商、类型、颜色） |
| `/spools` | Spools.vue | 料盘 CRUD（关联耗材、重量、AMS 位置、状态） |
| `/print-records` | PrintRecords.vue | 打印记录主从表（展开查看每 tray 明细 + 手动扣减） |
| `/printers` | PrinterConfig.vue | 打印机配置 CRUD + 连接/断开 |
| `/mqtt-messages` | MqttMessages.vue | MQTT 原始消息列表（搜索、展开查看 JSON、删除） |
| `/operation-logs` | OperationLogs.vue | 操作日志（按级别筛选、清空） |

### Dashboard 特殊展示

- AMS 4 槽 + EXT 1 槽：以 **水位图** 展示每个料盘的剩余量百分比和颜色
- 仓库库存：进度条展示
- 10 秒自动轮询刷新（`setInterval(loadAll, 10000)`）
- 连接打印机时显示实时温度、进度

---

## 开发环境搭建

### 前置条件

- Python 3.11+
- Node.js 20+
- 一个 Bambu Lab 打印机（用于 MQTT 功能）

### 1. 后端

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端（开发模式）

```bash
cd frontend
npm install
npm run dev
# 启动在 http://localhost:5173，自动代理 /api → localhost:8000
```

### 3. 构建前端

```bash
cd frontend
npm run build
# 产物在 frontend/dist/
# 需要部署时复制到 backend/static/
```

---

## Docker 部署

### 构建并运行

```bash
# 构建镜像
docker-compose build

# 或者直接构建
docker build -t consumable-filament-manager .

# 启动
docker-compose up -d

# 查看日志
docker compose logs -f

# 停止
docker-compose down
```

### 导出为 tar（群晖等离线环境）

```bash
docker save consumable-filament-manager:latest -o filament-manager-docker.tar
```

在目标机器上：
```bash
docker load -i filament-manager-docker.tar
docker run -d \
  --name filament-manager \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  consumable-filament-manager:latest
```

### 多阶段构建说明

`Dockerfile` 分为两个阶段：
1. **frontend-builder**: 基于 node:20-alpine，安装前端依赖并执行 `vite build`
2. **runtime**: 基于 python:3.11-slim，安装 Python 依赖，复制后端代码和构建好的前端静态文件

最终镜像约 300MB（仅 Python 运行时 + 静态文件，不含 Node.js）。

---

## 配置

### 方法一：环境变量（优先）

所有配置通过环境变量覆盖，前缀 `FM_`：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FM_DATABASE_URL` | 数据库连接串 | `sqlite:///{data_dir}/filament.db` |
| `FM_DEBUG` | 调试模式 | `false` |
| `FM_MQTT_PORT` | MQTT 默认端口 | `8883` |
| `FM_DATA_DIR` | 数据目录 | Docker: `/app/data` / 本地: `./data/` |
| `FM_CONFIG_DIR` | 配置目录 | Docker: `/app/config` / 本地: `../config/` |

### 方法二：config.yaml

参考 `config/config.yaml`，当前仅作为参考，核心配置仍由环境变量控制。

### 数据库

- SQLite 文件存储在 `data/filament.db`
- 启动时自动建表（`Base.metadata.create_all`）
- 新增字段通过 `ALTER TABLE` 迁移（`_migrate_add_column`）
- 多线程：启用 WAL 模式 + `check_same_thread=False`

---

## 关键业务逻辑

### 耗材扣减机制

1. **实时自动扣减**（MQTT 运行中）
   - 每次 MQTT report 计算 `delta_filament_mm`
   - 从当前活跃 tray 对应的料盘 `current_weight` 中扣除
   - 更新 `_last_filament_mm` 追踪值

2. **打印结束记录**
   - 不会再次扣减（避免双倍扣减）
   - 创建 PrintRecord + PrintRecordDetail，标记 `deducted=True`

3. **手动扣减**（用户触发）
   - 调用 `POST /api/print-records/details/{detail_id}/deduct`
   - 计算 `filament_used_mm → weight` 并从料盘扣减
   - 仅对 `deducted=False` 的记录可用
   - 用于自动扣减异常的补救场景

### 料盘位置与状态

```
is_active=true, ams_tray>0  → "AMS"      （在 AMS 中）
is_active=true, ams_tray=0  → "EXT"      （外置挂架）
is_active=false, ams_tray=0 → "仓库"     （闲置存储）
```

自动扣减只查找 `is_active=True` 的料盘。

---

## 常见问题

### 连接打印机失败

1. 检查打印机 IP 是否正确
2. 确认访问码（打印机屏幕上查看）
3. 查看"操作日志"页面获取具体错误原因
4. 常见错误码：rc=4 用户名或密码错误（访问码不对）, rc=3 服务器不可用（IP/端口不对）

### 手动扣减按钮灰色

- 必须满足两个条件：`deducted=False` 且有关联料盘（`spool_name` 不为空）
- 如果实时扣减正常，按钮会自动变灰不可用

### 多色打印记录

- 一次多色打印会在打印记录中产生一条主记录 + 多条明细（每个 tray 一条）
- 展开主记录行即可查看每个托盘的使用情况
