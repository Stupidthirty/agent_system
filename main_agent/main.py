from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from agent_base import AgentCapabilities, AgentResponse
from config import settings
from agent_system.router import router

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
        worker = WorkerNode(worker_id=f"{agent_id}_worker", agent_manager=self)
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
        
        # 广播任务到路由
        self.router.broadcast_task(task)
        
        print("Task broadcasted:", task)
        return state
    
    def wait_for_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """等待结果节点"""
        # 在实际应用中，这里可以使用POLL机制或回调
        print("Waiting for results...")
        
        # 监听结果队列
        while True:
            result = self._poll_result()
            if result:
                state["results"].append(result)
                if len(state["results"]) >= state.get("expected_results", 1):
                    break
            
            time.sleep(1)
        
        return state
    
    def _poll_result(self):
        """轮询结果"""
        try:
            # 简化实现，实际应用中应该使用RabbitMQ的消费者
            # 这里返回示例结果
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
