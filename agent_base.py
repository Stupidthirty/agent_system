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
