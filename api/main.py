# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from main_agent.main import MainAgent
from agent_base import AgentCapabilities
import threading

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭逻辑"""
    # 初始化系统
    # 创建示例Agent
    weather_capabilities = AgentCapabilities(
        name="weather_agent",
        description="天气查询Agent",
        required_resources=["api_access"],
        supported_tools=["openweather_api"]
    )
    
    task_tracker_capabilities = AgentCapabilities(
        name="task_tracker",
        description="任务跟踪Agent",
        required_resources=["database"],
        supported_tools=["redis"]
    )
    
    main_agent.add_agent("weather_agent_1", weather_capabilities, WeatherAgent)
    main_agent.add_agent("task_tracker_1", task_tracker_capabilities, TaskTrackerAgent)
    
    print("System initialized")
    
    try:
        yield
    finally:
        # 清理资源
        main_agent.remove_agent("weather_agent_1")
        main_agent.remove_agent("task_tracker_1")
        print("System shutdown")


app = FastAPI(title="多Agent系统API", lifespan=lifespan)

import os

# 静态资源路径
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """前端主页"""
    index_path = os.path.join(static_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 初始化系统
main_agent = MainAgent()

class TaskRequest(BaseModel):
    """任务请求"""
    skill: str
    task_id: str
    data: Dict[str, Any] = {}

@app.post("/task")
async def submit_task(task_request: TaskRequest):
    """提交任务到主Agent"""
    try:
        # 启动异步任务
        thread = threading.Thread(
            target=run_task,
            args=(task_request,)
        )
        thread.start()
        
        return {"status": "accepted", "task_id": task_request.task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_task(task_request: TaskRequest):
    """在后台线程中运行任务"""
    task = {
        "skill": task_request.skill,
        "task_id": task_request.task_id,
        **task_request.data
    }
    
    # 使用LangGraph执行任务
    result = main_agent.graph.invoke({
        "task": task,
        "results": [],
        "expected_results": 1
    })
    
    print("Task completed:", result)

class AgentRequest(BaseModel):
    """Agent请求"""
    agent_id: str
    capabilities: AgentCapabilities
    agent_class: str

@app.post("/agents/create")
async def create_agent(request: AgentRequest):
    """创建新Agent"""
    try:
        # 动态导入Agent类
        module = __import__(f"agents.{request.agent_class.lower()}", fromlist=[request.agent_class])
        agent_class = getattr(module, request.agent_class)
        
        main_agent.add_agent(
            request.agent_id,
            request.capabilities,
            agent_class
        )
        
        return {"status": "created", "agent_id": request.agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/list")
async def list_agents():
    """列出所有Agent"""
    return {
        "agents": main_agent.manager.get_all_agents()
    }

class AgentDeleteRequest(BaseModel):
    """删除Agent请求"""
    agent_id: str

@app.delete("/agents/delete")
async def delete_agent(request: AgentDeleteRequest):
    """删除Agent"""
    main_agent.remove_agent(request.agent_id)
    return {"status": "deleted", "agent_id": request.agent_id}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "system": "multi_agent_system"}
