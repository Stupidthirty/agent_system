import pika
import json
import threading
import time
from typing import Dict
from config import settings

class WorkerNode:
    """Worker Node - Agent与路由之间的桥梁"""
    
    def __init__(self, worker_id: str, agent_manager):
        self.worker_id = worker_id
        self.agent_manager = agent_manager  # Agent管理器（主Agent）
        self.connection = None
        self.channel = None
        self.is_running = False
    
    def start(self):
        """启动Worker Node"""
        self.is_running = True
        self._connect()
        self._setup_consuming()
        
        # 启动后台任务监听队列
        thread = threading.Thread(target=self._consume_tasks, daemon=True)
        thread.start()
    
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
        """发送结果到路由"""
        if not self.connection or not self.channel:
            self._connect()
        
        # 发送到结果队列
        self.channel.basic_publish(
            exchange="",
            routing_key="agent_results",
            body=json.dumps(response),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.PERSISTENT
            )
        )

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
