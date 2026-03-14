import pika
import json
import threading
import time
from typing import Dict, Any
import redis
from config import settings
from agent_system.router import router

class WorkerNode:
    """Worker Node - Agent与路由之间的桥梁"""
    
    def __init__(self, agent_id: str, agent_manager):
        self.agent_id = agent_id
        self.worker_id = f"{agent_id}_worker"
        self.agent_manager = agent_manager  # Agent管理器（主Agent）
        self.connection = None
        self.channel = None
        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        self.pubsub = None
        self.is_running = False
    
    def start(self):
        """启动Worker Node"""
        self.is_running = True
        self._connect()
        self._setup_consuming()
        self._setup_pubsub()
        
        # 启动后台任务监听队列
        thread = threading.Thread(target=self._consume_tasks, daemon=True)
        thread.start()

        # 启动 Pub/Sub 监听
        pubsub_thread = threading.Thread(target=self._consume_pubsub, daemon=True)
        pubsub_thread.start()
    
    def stop(self):
        """停止Worker Node"""
        self.is_running = False
        if self.connection:
            self.connection.close()
    
    def _connect(self):
        """连接到RabbitMQ"""
        params = pika.URLParameters(settings.RABBITMQ_URL)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
    
    def _setup_consuming(self):
        """设置任务队列"""
        self.channel.queue_declare(queue=f"worker_{self.worker_id}_tasks", durable=True)
    
    def _setup_pubsub(self):
        """设置 Redis Pub/Sub 监听，用于支持 agent 之间的平等协作"""
        agent = self.agent_manager.get_agent(self.agent_id)
        if not agent:
            return

        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        for skill in agent.skills.keys():
            channel = f"skill:{skill}"
            self.pubsub.subscribe(channel)

    def _consume_tasks(self):
        """消费任务"""
        while self.is_running:
            try:
                method, properties, body = self.channel.basic_consume(
                    queue=f"worker_{self.worker_id}_tasks",
                    no_ack=True,
                    on_message_callback=self._on_message
                )
                self.channel.wait()
            except pika.exceptions.ConnectionClosed:
                if self.is_running:
                    time.sleep(1)
                    self._connect()
                    self._setup_consuming()
    
    def _consume_pubsub(self):
        """消费 Redis Pub/Sub 消息，用于 Agent 间互相发布/订阅任务"""
        if not self.pubsub:
            return

        for message in self.pubsub.listen():
            if not self.is_running:
                break
            try:
                task = json.loads(message.get("data", b"{}"))
            except Exception:
                continue

            # Pub/Sub 任务不一定包含 agent_id（由 skill 匹配）
            task.setdefault("agent_id", self.agent_id)
            agent = self.agent_manager.get_agent(self.agent_id)
            if agent:
                response = agent.execute(task)
                self._send_result(response)
    
    def _on_message(self, ch, method, properties, body):
        """处理收到的任务"""
        task = json.loads(body.decode())
        agent_id = task.get("agent_id")
        
        # 获取Agent并执行任务
        agent = self.agent_manager.get_agent(agent_id)
        if agent:
            response = agent.execute(task)
            # 发送结果回路由
            self._send_result(response)
        else:
            print(f"Agent {agent_id} not found")
    
    def _send_result(self, response: Dict[str, Any]):
        """发送结果到路由（同时写入 Redis 结果队列）"""
        task_id = getattr(response, "task_id", None) or response.get("task_id")

        # 发送到 RabbitMQ 结果队列（兼容旧逻辑）
        if not self.connection or not self.channel:
            self._connect()
        self.channel.basic_publish(
            exchange="",
            routing_key="agent_results",
            body=json.dumps(response),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.PERSISTENT
            )
        )

        # 写入 Redis 结果列表
        if task_id:
            router.push_task_result(task_id, response)

# 全局函数
worker_nodes = {}

def dispatch_task(agent_id: str, task: Dict[str, Any]):
    """分发任务到指定的Worker Node"""
    if agent_id not in worker_nodes:
        print(f"No worker found for agent {agent_id}")
        return
    
    worker = worker_nodes[agent_id]
    
    # 发送到对应Agent的Worker队列
    worker.channel.basic_publish(
        exchange="",
        routing_key=f"worker_{worker.worker_id}_tasks",
        body=json.dumps(task),
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.PERSISTENT
        )
    )
    print(f"Task dispatched to {agent_id} via worker {worker.worker_id}")
