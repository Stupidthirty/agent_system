# agent_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class AgentCapabilities(BaseModel):
    """Agent能力定义"""
    name: str
    description: str
    required_resources: List[str] = []
    supported_tools: List[str] = []

class AgentResponse(BaseModel):
    """Agent响应"""
    agent_id: str
    task_id: str
    result: Dict[str, Any]
    status: str = "success"

class AgentBase(ABC):
    """Agent基类"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.skills = self._get_skills()
        self.tools = self._get_tools()
        self.resources = self._get_resources()

    def emit_task(self, task: Dict[str, Any]):
        """向 Router 发布任务，使其他 Agent 能订阅并处理"""
        from agent_system.router import router
        router.publish_task(task)

    def emit_event(self, event: str, payload: Dict[str, Any]):
        """向 Router 发布自定义事件，供其他 Agent 订阅"""
        from agent_system.router import router
        router.publish_event(event, payload)

    def create_task_context(self, task_id: str, initial: Dict[str, Any] = None):
        """创建/初始化任务上下文"""
        from agent_system.router import router
        router.create_task_context(task_id, initial)

    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """获取任务共享上下文"""
        from agent_system.router import router
        return router.get_task_context(task_id)

    def update_task_context(self, task_id: str, updates: Dict[str, Any]):
        """更新任务共享上下文"""
        from agent_system.router import router
        router.update_task_context(task_id, updates)
    
    @abstractmethod
    def _get_skills(self) -> Dict[str, Any]:
        """获取技能"""
        pass
    
    @abstractmethod
    def _get_tools(self) -> Dict[str, Any]:
        """获取工具"""
        pass
    
    @abstractmethod
    def _get_resources(self) -> Dict[str, Any]:
        """获取资源"""
        pass
    
    def execute(self, task: Dict[str, Any]) -> AgentResponse:
        """执行任务"""
        try:
            skill = task.get("skill")
            if skill not in self.skills:
                return AgentResponse(
                    agent_id=self.agent_id,
                    task_id=task.get("task_id"),
                    result={"error": f"Skill {skill} not supported"},
                    status="failed"
                )
            
            result = self.skills[skill](task)
            return AgentResponse(
                agent_id=self.agent_id,
                task_id=task.get("task_id"),
                result=result,
                status="success"
            )
        except Exception as e:
            return AgentResponse(
                agent_id=self.agent_id,
                task_id=task.get("task_id"),
                result={"error": str(e)},
                status="failed"
            )
    
    def register(self, redis_client):
        """注册到路由"""
        from agent_system.router import register_agent
        register_agent(self, redis_client)
    
    def unregister(self, redis_client):
        """从路由注销"""
        from agent_system.router import unregister_agent
        unregister_agent(self.agent_id, redis_client)
