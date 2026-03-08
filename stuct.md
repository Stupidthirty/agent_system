agent_system/
├── main.py                 # 系统入口
├── requirements.txt        # 依赖
├── agent_base.py          # Agent 基类
├── agents/                # 具体Agent实现
│   ├── __init__.py
│   ├── weather_agent.py   # 天气查询Agent
│   ├── task_tracker.py    # 任务跟踪Agent
│   └── message_queue.py   # 消息队列Agent
├── router/                # Agent信息路由
│   ├── __init__.py
│   └── router.py
├── main_agent/            # 主Agent
│   ├── __init__.py
│   └── main.py
├── worker_node/           # Worker Node
│   ├── __init__.py
│   └── worker.py
├── api/                   # FastAPI接口
│   ├── __init__.py
│   └── main.py
└── config.py              # 配置
