from agent_base import AgentBase, AgentCapabilities, AgentResponse
import pika

class MessageQueueAgent(AgentBase):
    """消息队列Agent"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        super().__init__(agent_id, capabilities)
    
    def _get_skills(self):
        return {
            "send_message": self._send_message,
            "receive_messages": self._receive_messages
        }
    
    def _get_tools(self):
        return {}
    
    def _get_resources(self):
        return {}
    
    def _send_message(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息到消息队列"""
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        
        queue_name = task.get("queue_name", "default_queue")
        message = task.get("message")
        
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.PERSISTENT
            )
        )
        
        connection.close()
        
        return {"status": "sent", "queue": queue_name}
    
    def _receive_messages(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """从消息队列接收消息"""
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        
        queue_name = task.get("queue_name", "default_queue")
        
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        
        if method_frame:
            message = body.decode()
            channel.basic_ack(method_frame.delivery_tag)
            connection.close()
            
            return {"status": "received", "message": message}
        
        connection.close()
        
        return {"status": "no_messages"}