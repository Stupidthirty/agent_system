import redis
import json
from typing import List, Dict
from agent_base import AgentCapabilities, AgentResponse

class Router:
    """Agent信息路由"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
        self.agents = {}  # 内存缓存
    
    def register_agent(self, agent):
        """注册Agent到路由"""
        capability = agent.capabilities.dict()
        capability["agent_id"] = agent.agent_id
        capability["skills"] = agent.skills
        capability["tools"] = agent.tools
        capability["resources"] = agent.resources
        
        # 存储到Redis
        self.redis_client.hset(
            f"agent:{agent.agent_id}",
            mapping=capability
        )
        
        # 添加到能力列表
        self.redis_client.sadd("all_agents", agent.agent_id)
        
        # 根据能力添加到特定列表
        for skill in agent.skills.keys():
            self.redis_client.sadd(f"skill:{skill}", agent.agent_id)
        
        self.agents[agent.agent_id] = capability
        print(f"Agent {agent.agent_id} registered")
    
    def unregister_agent(self, agent_id: str):
        """从路由注销Agent"""
        # 从Redis中删除
        self.redis_client.delete(f"agent:{agent_id}")
        self.redis_client.srem("all_agents", agent_id)
        
        # 从能力列表中移除
        capability = self.agents.get(agent_id, {})
        for skill in capability.get("skills", {}).keys():
            self.redis_client.srem(f"skill:{skill}", agent_id)
        
        # 从内存缓存中删除
        self.agents.pop(agent_id, None)
        print(f"Agent {agent_id} unregistered")
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """根据能力查找Agent"""
        return list(self.redis_client.smembers(f"skill:{capability}"))
    
    def get_all_agents(self) -> Dict[str, AgentCapabilities]:
        """获取所有Agent信息"""
        all_agent_ids = list(self.redis_client.smembers("all_agents"))
        agents = {}
        
        for agent_id in all_agent_ids:
            agent_data = self.redis_client.hgetall(f"agent:{agent_id.decode()}")
            if agent_data:
                agents[agent_id.decode()] = AgentCapabilities(**{
                    k.decode(): v.decode() for k, v in agent_data.items()
                })
        
        return agents
    
    def broadcast_task(self, task: Dict[str, Any]):
        """广播任务到所有匹配的Agent"""
        skill = task.get("skill")
        if not skill:
            print("No skill specified in task")
            return
        
        # 查找支持该技能的Agent
        agent_ids = self.find_agents_by_capability(skill)
        print(f"Found {len(agent_ids)} agents for skill {skill}")
        
        for agent_id in agent_ids:
            # 发送到消息队列
            from worker_node.worker import dispatch_task
            dispatch_task(agent_id, task)
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent信息"""
        return self.agents.get(agent_id)

# 全局函数
router = Router()

def register_agent(agent, redis_client=None):
    """全局注册函数"""
    r = redis_client or router.redis_client
    router.register_agent(agent)

def unregister_agent(agent_id: str, redis_client=None):
    """全局注销函数"""
    router.unregister_agent(agent_id)
