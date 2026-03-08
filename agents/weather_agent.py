import requests
from agent_base import AgentBase, AgentCapabilities, AgentResponse
from config import settings

class WeatherAgent(AgentBase):
    """天气查询Agent"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        super().__init__(agent_id, capabilities)
    
    def _get_skills(self):
        return {
            "get_weather": self._get_weather
        }
    
    def _get_tools(self):
        return {
            "api": requests.Session()
        }
    
    def _get_resources(self):
        return {
            "cache": True,
            "timeout": 5
        }
    
    def _get_weather(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取天气信息"""
        city = task.get("city", "Beijing")
        response = self.tools["api"].get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": settings.OPENAI_API_KEY,  # 使用API key
                "units": "metric"
            },
            timeout=self.resources.get("timeout")
        )
        data = response.json()
        
        return {
            "city": city,
            "weather": data["weather"][0]["description"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"]
        }

# agents/task_tracker.py
from agent_base import AgentBase, AgentCapabilities, AgentResponse
import uuid
import redis

class TaskTrackerAgent(AgentBase):
    """任务跟踪Agent"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        super().__init__(agent_id, capabilities)
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)
    
    def _get_skills(self):
        return {
            "create_task": self._create_task,
            "get_task_status": self._get_task_status,
            "update_task_status": self._update_task_status
        }
    
    def _get_tools(self):
        return {}
    
    def _get_resources(self):
        return {}
    
    def _create_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        task_info = {
            "task_id": task_id,
            "description": task.get("description"),
            "status": "pending",
            "created_at": time.time(),
            "assigned_agents": []
        }
        
        self.redis.hset(f"task:{task_id}", mapping=task_info)
        self.redis.lpush("pending_tasks", task_id)
        
        return {"task_id": task_id}
    
    def _get_task_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取任务状态"""
        task_id = task.get("task_id")
        task_info = self.redis.hgetall(f"task:{task_id}")
        
        return {
            "task_id": task_id,
            "status": task_info.get("status", "unknown"),
            "created_at": task_info.get("created_at")
        }
    
    def _update_task_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务状态"""
        task_id = task.get("task_id")
        status = task.get("status")
        
        self.redis.hset(f"task:{task_id}", "status", status)
        
        return {"task_id": task_id, "status": status}