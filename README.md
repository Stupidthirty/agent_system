# Agent System - 多代理系统

## 概述

Agent System 是一个基于 Python 的多代理系统框架，支持分布式代理注册、任务分发和执行。该系统使用 Redis 作为代理注册中心，RabbitMQ 作为消息队列，FastAPI 作为 HTTP API 接口。

## 架构组件

### 核心组件
- **AgentBase**: 代理抽象基类，定义代理的基本接口
- **Router**: 代理注册和路由中心，使用 Redis 存储代理信息
- **MainAgent**: 主代理，负责任务编排和状态管理
- **WorkerNode**: 工作节点，执行具体任务
- **API**: FastAPI 接口，提供 HTTP 端点

### 目录结构
```
.
├── pyaudio_test.py        # 系统音频输出录制测试脚本
├── README.md              # 项目说明文档
└── agent_system/          # 多代理系统核心代码
    ├── agent_base.py          # 代理基类和数据模型
    ├── config.py              # 系统配置
    ├── main.py                # 系统入口点
    ├── requirements.txt       # 依赖包
    ├── agents/                # 具体代理实现
    │   ├── weather_agent.py   # 天气查询代理
    │   ├── task_tracker.py    # 任务跟踪代理
    │   └── message_queue.py   # 消息队列代理
    ├── router/                # 路由系统
    │   └── router.py          # 路由器实现
    ├── main_agent/            # 主代理
    │   └── main.py            # 主代理逻辑
    ├── worker_node/           # 工作节点
    │   └── worker.py          # 工作节点实现
    └── api/                   # API 接口
        └── main.py            # FastAPI 应用
```

## 工作流程

### 1. 系统启动
1. 加载配置文件 (`config.py`)
2. 初始化 Redis 和 RabbitMQ 连接
3. 启动 FastAPI 服务器
4. 在启动事件中创建示例代理

### 2. 代理注册
1. 创建代理实例 (继承自 `AgentBase`)
2. 代理调用 `register()` 方法
3. Router 将代理信息存储到 Redis 中
4. 为代理创建对应的 WorkerNode

### 3. 任务提交
1. 客户端通过 HTTP POST 请求提交任务到 `/task` 端点
2. API 层接收任务，传递给 MainAgent
3. MainAgent 使用 LangGraph StateGraph 处理任务

### 4. 任务分发
1. MainAgent 调用 Router 的 `broadcast_task()` 方法
2. Router 根据任务技能查找匹配的代理
3. 为每个匹配的代理调用 `dispatch_task()`
4. 任务被发布到对应代理的 RabbitMQ 队列

### 5. 任务执行
1. WorkerNode 监听自己的 RabbitMQ 队列
2. 收到任务后，从 AgentManager 获取代理实例
3. 调用代理的 `execute()` 方法
4. 执行结果发布到结果队列

### 6. 结果收集
1. MainAgent 轮询结果队列 (当前为简化实现)
2. 收集所有代理的执行结果
3. 返回聚合结果给客户端

## 安装和配置

### 环境要求
- Python 3.8+
- Redis 服务器
- RabbitMQ 服务器
- OpenAI API 密钥 (用于某些代理)

### 安装依赖
```bash
pip install -r requirements.txt
```

### 环境变量配置
创建 `.env` 文件：
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
OPENAI_API_KEY=your_openai_api_key
```

## 使用方法

### 启动系统
```bash
python agent_system/main.py
```

系统将在 http://localhost:8000 启动 FastAPI 服务器。

### 前端界面
服务器还提供一个简单的网页控制面板，访问根网址即可打开：

- **http://localhost:8000/**

该页面允许查看当前注册的代理，创建或删除代理，以及提交任务。

### API 接口

#### 提交任务
```bash
curl -X POST "http://localhost:8000/task" \
     -H "Content-Type: application/json" \
     -d '{
       "skill": "weather",
       "task_id": "task_001",
       "data": {"location": "Beijing"}
     }'
```

#### 管理代理

**创建代理**:
```bash
curl -X POST "http://localhost:8000/agents/create" \
     -H "Content-Type: application/json" \
     -d '{
       "agent_type": "weather_agent",
       "agent_id": "weather_agent_1"
     }'
```

**列出代理**:
```bash
curl "http://localhost:8000/agents/list"
```

**删除代理**:
```bash
curl -X DELETE "http://localhost:8000/agents/delete/weather_agent_1"
```

### 创建自定义代理

1. 创建新的代理类，继承自 `AgentBase`:
```python
from agent_system.agent_base import AgentBase, AgentCapabilities

class CustomAgent(AgentBase):
    def _get_skills(self):
        return ["custom_skill"]
    
    def _get_tools(self):
        return ["custom_tool"]
    
    def _get_resources(self):
        return ["custom_resource"]
    
    async def custom_skill_handler(self, task):
        # 实现自定义技能逻辑
        return {"result": "custom response"}
```

2. 在 `agents/__init__.py` 中注册代理:
```python
from .custom_agent import CustomAgent

__all__ = ['CustomAgent', 'WeatherAgent', ...]
```

3. 在 API 启动事件中创建代理实例:
```python
# 在 api/main.py 的 startup_event 中
custom_agent = agent_manager.create_agent("custom_agent", "custom_agent_1")
```

## 开发和扩展

### 添加新技能
在代理类中添加新的技能处理方法:
```python
async def new_skill_handler(self, task):
    # 技能实现逻辑
    pass
```

### 中间件支持
系统支持添加中间件来处理请求/响应:
```python
# 在 router 中添加中间件
router.add_middleware(AuthMiddleware)
```

### 错误处理
系统内置了基本的错误处理机制，包括:
- 任务执行超时
- 代理不可用
- 消息队列连接失败

## 监控和调试

### 日志
系统使用 Python 标准 logging 模块，日志级别可在配置中设置。

### 健康检查
访问 `/health` 端点检查系统状态。

### 调试模式
在配置中设置 `DEBUG=True` 启用详细日志输出。

## 性能考虑

- 使用 Redis 缓存代理注册信息
- RabbitMQ 提供异步任务处理
- 支持水平扩展工作节点
- 任务结果缓存机制

## 故障排除

### 常见问题

**Redis 连接失败**
- 检查 Redis 服务是否运行
- 验证连接配置

**RabbitMQ 连接失败**
- 检查 RabbitMQ 服务状态
- 确认队列权限

**代理注册失败**
- 检查代理类是否正确继承 AgentBase
- 验证技能定义

**任务执行超时**
- 增加超时配置
- 检查代理实现是否有阻塞操作

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送分支 (`git push origin feature/new-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

*最后更新: 2026年3月8日*