# 理发店预约排班与耗材领用系统

基于 Python + FastAPI + Beanie + MongoDB + React + TypeScript + Ant Design 的全栈管理系统。

## 功能特性

- 🔐 用户登录认证（JWT）
- 👥 员工管理
- 💇 服务项目管理
- 📅 预约登记管理
- ⏰ 排班管理
- 📦 耗材台账管理
- 📋 领用登记
- 📊 统计看板

## 业务约束

- ✅ 预约编号不能重复
- ✅ 同一员工同一时段不能重复排班
- ✅ 取消状态预约不能办理服务
- ✅ 领用数量不能超过耗材库存
- ✅ 预约时间不能早于当前日期时间

## 技术栈

### 后端
- Python 3.9+
- FastAPI
- Beanie (MongoDB ODM)
- MongoDB
- JWT 认证

### 前端
- React 18
- TypeScript
- Ant Design 5
- Vite
- Recharts (图表)

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- MongoDB 4.4+

### 方式一：使用启动脚本（推荐）

#### Windows
```bash
# 后端启动
cd backend
start_backend.bat

# 前端启动（新开终端）
cd frontend
start_frontend.bat
```

### 方式二：手动启动

#### 1. 启动 MongoDB

确保 MongoDB 服务已启动，默认端口 `27017`

#### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
copy .env.example .env

# 初始化默认用户
# 启动服务后访问 POST /api/auth/init
# 或者在浏览器访问 http://localhost:8000/docs 执行

# 启动服务
uvicorn app.main:app --reload
```

后端 API 文档: http://localhost:8000/docs

#### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务
npm run dev
```

前端访问: http://localhost:3000

### 默认账号

- 用户名: `admin`
- 密码: `admin123`

## 项目结构

```
cj65/
├── backend/                 # 后端项目
│   ├── app/
│   │   ├── models/          # 数据模型
│   │   ├── routes/          # API 路由
│   │   ├── utils/           # 工具函数
│   │   ├── config.py        # 配置文件
│   │   ├── database.py      # 数据库初始化
│   │   └── main.py          # 应用入口
│   ├── requirements.txt     # Python 依赖
│   ├── .env.example         # 环境变量示例
│   └── start_backend.bat    # Windows 启动脚本
├── frontend/                # 前端项目
│   ├── src/
│   │   ├── components/      # 公共组件
│   │   ├── pages/           # 页面组件
│   │   ├── utils/           # 工具函数
│   │   ├── App.tsx          # 应用入口
│   │   └── main.tsx         # 渲染入口
│   ├── package.json         # Node 依赖
│   ├── vite.config.ts       # Vite 配置
│   └── start_frontend.bat   # Windows 启动脚本
└── README.md                # 项目说明
```

## API 接口

### 认证
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户
- `POST /api/auth/init` - 初始化默认用户

### 员工管理
- `GET /api/employees` - 获取员工列表
- `POST /api/employees` - 新增员工
- `GET /api/employees/{id}` - 获取员工详情
- `PUT /api/employees/{id}` - 更新员工
- `DELETE /api/employees/{id}` - 删除员工

### 服务项目管理
- `GET /api/services` - 获取服务列表
- `POST /api/services` - 新增服务
- `PUT /api/services/{id}` - 更新服务
- `DELETE /api/services/{id}` - 删除服务

### 预约管理
- `GET /api/appointments` - 获取预约列表
- `POST /api/appointments` - 新增预约
- `PUT /api/appointments/{no}` - 更新预约
- `DELETE /api/appointments/{no}` - 删除预约
- `POST /api/appointments/{no}/complete` - 完成预约
- `POST /api/appointments/{no}/cancel` - 取消预约

### 排班管理
- `GET /api/schedules` - 获取排班列表
- `POST /api/schedules` - 新增排班
- `PUT /api/schedules/{id}` - 更新排班
- `DELETE /api/schedules/{id}` - 删除排班

### 耗材管理
- `GET /api/consumables` - 获取耗材列表（返回包含 stock_status 库存状态字段）
- `POST /api/consumables` - 新增耗材
- `PUT /api/consumables/{no}` - 更新耗材
- `DELETE /api/consumables/{no}` - 删除耗材
- `POST /api/consumables/{no}/stock/add` - 耗材入库

> 耗材状态说明：
> - `status` 业务状态：正常/停用（存储在数据库）
> - `stock_status` 库存状态：正常/库存不足/缺货（根据 stock_quantity 动态计算，≤0 缺货，<10 库存不足，否则正常）

### 领用登记
- `GET /api/usages` - 获取领用记录
- `POST /api/usages` - 新增领用
- `DELETE /api/usages/{no}` - 删除领用（退还库存）

### 统计看板
- `GET /api/dashboard/summary` - 汇总数据
- `GET /api/dashboard/appointments/count` - 预约统计
- `GET /api/dashboard/schedules/distribution` - 排班分布
- `GET /api/dashboard/consumables/ranking` - 耗材消耗排行
