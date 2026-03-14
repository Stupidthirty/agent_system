import json
import threading
import time

from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from agent_base import AgentCapabilities, AgentResponse
from config import settings
from agent_system.router import router
from worker_node.worker import WorkerNode, worker_nodes

class AgentManager:
    """Agent管理器 - 管理所有Agent的生命周期"""
    
    def __init__(self):
        self.agents = {}  # agent_id -> Agent
        self.agents_lock = threading.Lock()
    
    def create_agent(self, agent_id: str, capabilities: AgentCapabilities, agent_class, **kwargs):
        """创建新Agent"""
        with self.agents_lock:
            if agent_id in self.agents:
                print(f"Agent {agent_id} already exists")
                return self.agents[agent_id]
            
            agent = agent_class(agent_id=agent_id, capabilities=capabilities, **kwargs)
            self.agents[agent_id] = agent
            
            # 注册到路由
            agent.register(router.redis_client)
            
            # 启动对应的Worker Node
            self._start_worker_node(agent_id, agent)
            
            return agent
    
    def get_agent(self, agent_id: str):
        """获取Agent"""
        return self.agents.get(agent_id)
    
    def delete_agent(self, agent_id: str):
        """删除Agent"""
        with self.agents_lock:
            agent = self.agents.pop(agent_id, None)
            if agent:
                agent.unregister(router.redis_client)
                # 停止Worker Node
                if agent_id in worker_nodes:
                    worker_nodes[agent_id].stop()
    
    def _start_worker_node(self, agent_id: str, agent):
        """启动Agent的Worker Node"""
        worker = WorkerNode(agent_id=agent_id, agent_manager=self)
        worker.start()
        worker_nodes[agent_id] = worker

class MainAgent:
    """主Agent - 使用LangGraph构建"""
    
    def __init__(self):
        self.manager = AgentManager()
        self.router = router
        
        # 构建状态图
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """构建LangGraph状态图"""
        workflow = StateGraph()
        
        # 定义节点
        workflow.add_node("接收任务", self.receive_task)
        workflow.add_node("任务分发", self.distribute_task)
        workflow.add_node("等待结果", self.wait_for_results)
        
        # 定义边
        workflow.set_entry_point("接收任务")
        workflow.add_edge("接收任务", "任务分发")
        workflow.add_edge("任务分发", "等待结果")
        workflow.add_edge("等待结果", END)
        
        return workflow.compile()
    
    def receive_task(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """接收任务节点"""
        print("Received task:", state.get("task"))
        return state
    
    def distribute_task(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """任务分发节点"""
        task = state.get("task")
        task_id = task.get("task_id")

        # 初始化任务上下文（供多 Agent 共享/协作）
        if task_id:
            self.router.create_task_context(task_id, {
                "skill": task.get("skill"),
                "status": "created",
                "data": json.dumps(task.get("data", {}))
            })

        # 广播任务到路由（使用 Pub/Sub 让所有订阅该技能的 Agent 平等接收）
        self.router.publish_task(task)
        
        print("Task published:", task)
        return state
    
    def wait_for_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """等待结果节点"""
        task = state.get("task", {})
        task_id = task.get("task_id")

        print("Waiting for results...")

        # 通过 Redis 列表获取结果（由 Worker 发布）
        while True:
            result = self.router.pop_task_result(task_id, timeout=1)
            if result:
                state["results"].append(result)
                if len(state["results"]) >= state.get("expected_results", 1):
                    break

        return state

    # 保留旧方法以便测试或兼容性
    def _poll_result(self):
        """轮询结果（备用）"""
        try:
            return {
                "agent_id": "weather_agent_1",
                "task_id": "task_123",
                "result": {"weather": "Sunny", "temperature": 25},
                "status": "success"
            }
        except:
            return None
    
    def add_agent(self, agent_id: str, capabilities: AgentCapabilities, agent_class, **kwargs):
        """添加Agent"""
        return self.manager.create_agent(agent_id, capabilities, agent_class, **kwargs)
    
    def remove_agent(self, agent_id: str):
        """移除Agent"""
        return self.manager.delete_agent(agent_id)
