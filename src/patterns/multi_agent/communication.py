#!/usr/bin/env python3
"""
Multi-Agent Pattern: Agent Communication Protocol
代理間通訊協議 - 支援安全、可靠的多代理通訊機制

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timedelta
import hashlib
import hmac
from collections import defaultdict, deque


class MessageType(Enum):
    """訊息類型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    HANDSHAKE = "handshake"
    ERROR = "error"


class MessagePriority(Enum):
    """訊息優先級"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class DeliveryMode(Enum):
    """傳遞模式"""
    DIRECT = "direct"        # 直接傳遞
    RELIABLE = "reliable"    # 可靠傳遞（需要確認）
    BROADCAST = "broadcast"  # 廣播
    MULTICAST = "multicast"  # 群播


@dataclass
class Message:
    """通訊訊息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.NOTIFICATION
    priority: MessagePriority = MessagePriority.MEDIUM
    delivery_mode: DeliveryMode = DeliveryMode.DIRECT
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None  # 用於請求-回應配對
    signature: Optional[str] = None       # 數位簽章
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        data['delivery_mode'] = self.delivery_mode.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """從字典創建訊息"""
        # 轉換枚舉值
        data['message_type'] = MessageType(data.get('message_type', 'notification'))
        data['priority'] = MessagePriority(data.get('priority', 3))
        data['delivery_mode'] = DeliveryMode(data.get('delivery_mode', 'direct'))
        
        # 轉換時間戳
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'expires_at' in data and data['expires_at'] and isinstance(data['expires_at'], str):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """檢查訊息是否過期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class DeliveryReceipt:
    """傳遞回執"""
    message_id: str
    receiver_id: str
    status: str  # 'delivered', 'failed', 'expired'
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


class MessageHandler(ABC):
    """訊息處理器抽象基類"""
    
    @abstractmethod
    async def handle_message(self, message: Message) -> Optional[Message]:
        """處理訊息，可能返回回應訊息"""
        pass
    
    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        """檢查是否能處理此訊息"""
        pass


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
        self.trusted_agents: Set[str] = set()
        self.agent_keys: Dict[str, str] = {}
    
    def add_trusted_agent(self, agent_id: str, agent_key: Optional[str] = None):
        """添加受信任代理"""
        self.trusted_agents.add(agent_id)
        if agent_key:
            self.agent_keys[agent_id] = agent_key
    
    def remove_trusted_agent(self, agent_id: str):
        """移除受信任代理"""
        self.trusted_agents.discard(agent_id)
        self.agent_keys.pop(agent_id, None)
    
    def sign_message(self, message: Message) -> str:
        """為訊息簽名"""
        message_data = json.dumps(message.to_dict(), sort_keys=True)
        signature = hmac.new(
            self.secret_key,
            message_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_message(self, message: Message) -> bool:
        """驗證訊息簽名"""
        if not message.signature:
            return False
        
        if message.sender_id not in self.trusted_agents:
            return False
        
        # 暫時移除簽名進行驗證
        original_signature = message.signature
        message.signature = None
        
        try:
            expected_signature = self.sign_message(message)
            is_valid = hmac.compare_digest(original_signature, expected_signature)
        finally:
            # 恢復原始簽名
            message.signature = original_signature
        
        return is_valid
    
    def is_agent_trusted(self, agent_id: str) -> bool:
        """檢查代理是否受信任"""
        return agent_id in self.trusted_agents


class MessageRouter:
    """訊息路由器"""
    
    def __init__(self):
        self.routing_table: Dict[str, str] = {}  # agent_id -> address
        self.group_memberships: Dict[str, Set[str]] = defaultdict(set)  # group -> agents
        self.routing_policies: List[Callable[[Message], Optional[str]]] = []
    
    def register_agent(self, agent_id: str, address: str):
        """註冊代理地址"""
        self.routing_table[agent_id] = address
    
    def unregister_agent(self, agent_id: str):
        """註銷代理"""
        self.routing_table.pop(agent_id, None)
        # 從所有群組中移除
        for group_agents in self.group_memberships.values():
            group_agents.discard(agent_id)
    
    def add_to_group(self, agent_id: str, group_name: str):
        """將代理加入群組"""
        self.group_memberships[group_name].add(agent_id)
    
    def remove_from_group(self, agent_id: str, group_name: str):
        """從群組中移除代理"""
        self.group_memberships[group_name].discard(agent_id)
    
    def add_routing_policy(self, policy: Callable[[Message], Optional[str]]):
        """添加路由策略"""
        self.routing_policies.append(policy)
    
    def route_message(self, message: Message) -> List[str]:
        """路由訊息，返回目標地址列表"""
        targets = []
        
        if message.delivery_mode == DeliveryMode.DIRECT:
            # 直接傳遞
            if message.receiver_id in self.routing_table:
                targets.append(self.routing_table[message.receiver_id])
        
        elif message.delivery_mode == DeliveryMode.BROADCAST:
            # 廣播到所有代理
            targets.extend(self.routing_table.values())
        
        elif message.delivery_mode == DeliveryMode.MULTICAST:
            # 群播到指定群組
            group_name = message.metadata.get('target_group')
            if group_name and group_name in self.group_memberships:
                for agent_id in self.group_memberships[group_name]:
                    if agent_id in self.routing_table:
                        targets.append(self.routing_table[agent_id])
        
        # 應用自定義路由策略
        for policy in self.routing_policies:
            custom_target = policy(message)
            if custom_target:
                targets.append(custom_target)
        
        return list(set(targets))  # 去重


class MessageQueue:
    """訊息佇列"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[MessagePriority, deque] = {
            priority: deque() for priority in MessagePriority
        }
        self.total_size = 0
        self._lock = asyncio.Lock()
    
    async def enqueue(self, message: Message) -> bool:
        """將訊息加入佇列"""
        async with self._lock:
            if self.total_size >= self.max_size:
                # 佇列已滿，移除最低優先級的舊訊息
                await self._remove_oldest_low_priority()
            
            self.queues[message.priority].append(message)
            self.total_size += 1
            return True
    
    async def dequeue(self) -> Optional[Message]:
        """從佇列中取出訊息（按優先級順序）"""
        async with self._lock:
            # 按優先級順序檢查佇列
            for priority in MessagePriority:
                queue = self.queues[priority]
                if queue:
                    message = queue.popleft()
                    self.total_size -= 1
                    return message
            return None
    
    async def _remove_oldest_low_priority(self):
        """移除最舊的低優先級訊息"""
        for priority in reversed(list(MessagePriority)):
            queue = self.queues[priority]
            if queue:
                queue.popleft()
                self.total_size -= 1
                break
    
    def size(self) -> int:
        """獲取佇列大小"""
        return self.total_size
    
    def is_empty(self) -> bool:
        """檢查佇列是否為空"""
        return self.total_size == 0


class CommunicationProtocol:
    """
    代理通訊協議
    
    提供完整的多代理通訊機制，包括訊息路由、安全認證、
    可靠傳遞和事件驅動通訊。
    """
    
    def __init__(
        self,
        agent_id: str,
        secret_key: str,
        max_queue_size: int = 10000,
        heartbeat_interval: float = 30.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化通訊協議
        
        Args:
            agent_id: 代理ID
            secret_key: 安全密鑰
            max_queue_size: 最大佇列大小
            heartbeat_interval: 心跳間隔（秒）
            logger: 日誌記錄器
        """
        self.agent_id = agent_id
        self.logger = logger or logging.getLogger(__name__)
        
        # 核心組件
        self.security_manager = SecurityManager(secret_key)
        self.message_router = MessageRouter()
        self.message_queue = MessageQueue(max_queue_size)
        
        # 訊息處理器
        self.message_handlers: List[MessageHandler] = []
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # 狀態管理
        self.is_running = False
        self.connected_agents: Set[str] = set()
        self.pending_requests: Dict[str, asyncio.Future] = {}  # correlation_id -> future
        self.delivery_receipts: Dict[str, DeliveryReceipt] = {}
        
        # 統計數據
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_failed': 0,
            'bytes_sent': 0,
            'bytes_received': 0
        }
        
        # 心跳機制
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_processor_task: Optional[asyncio.Task] = None
    
    def add_message_handler(self, handler: MessageHandler):
        """添加訊息處理器"""
        self.message_handlers.append(handler)
    
    def remove_message_handler(self, handler: MessageHandler):
        """移除訊息處理器"""
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)
    
    def subscribe_event(self, event_type: str, handler: Callable):
        """訂閱事件"""
        self.event_handlers[event_type].append(handler)
    
    def unsubscribe_event(self, event_type: str, handler: Callable):
        """取消訂閱事件"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    async def start(self):
        """啟動通訊協議"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 啟動心跳任務
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 啟動訊息處理任務
        self._message_processor_task = asyncio.create_task(self._message_processor_loop())
        
        self.logger.info(f"Communication protocol started for agent {self.agent_id}")
    
    async def stop(self):
        """停止通訊協議"""
        self.is_running = False
        
        # 取消任務
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._message_processor_task:
            self._message_processor_task.cancel()
        
        # 等待任務完成
        try:
            if self._heartbeat_task:
                await self._heartbeat_task
            if self._message_processor_task:
                await self._message_processor_task
        except asyncio.CancelledError:
            pass
        
        self.logger.info(f"Communication protocol stopped for agent {self.agent_id}")
    
    async def send_message(
        self,
        receiver_id: str,
        content: Dict[str, Any],
        message_type: MessageType = MessageType.NOTIFICATION,
        priority: MessagePriority = MessagePriority.MEDIUM,
        delivery_mode: DeliveryMode = DeliveryMode.DIRECT,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        發送訊息
        
        Args:
            receiver_id: 接收者ID
            content: 訊息內容
            message_type: 訊息類型
            priority: 優先級
            delivery_mode: 傳遞模式
            timeout: 超時時間（僅對REQUEST類型有效）
            
        Returns:
            對於REQUEST類型，返回回應訊息；否則返回None
        """
        # 創建訊息
        message = Message(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            priority=priority,
            delivery_mode=delivery_mode,
            content=content
        )
        
        # 設定過期時間
        if timeout:
            message.expires_at = datetime.now() + timedelta(seconds=timeout)
        
        # 為REQUEST類型設定correlation_id
        future = None
        if message_type == MessageType.REQUEST:
            message.correlation_id = str(uuid.uuid4())
            future = asyncio.Future()
            self.pending_requests[message.correlation_id] = future
        
        # 簽名訊息
        message.signature = self.security_manager.sign_message(message)
        
        # 發送訊息
        success = await self._send_message_internal(message)
        
        if not success:
            if message.correlation_id:
                self.pending_requests.pop(message.correlation_id, None)
            return None
        
        # 對於REQUEST類型，等待回應
        if message_type == MessageType.REQUEST and future:
            try:
                if timeout:
                    response = await asyncio.wait_for(future, timeout=timeout)
                else:
                    response = await future
                return response
            except asyncio.TimeoutError:
                self.pending_requests.pop(message.correlation_id, None)
                return None
            except Exception as e:
                self.logger.error(f"Error waiting for response: {e}")
                self.pending_requests.pop(message.correlation_id, None)
                return None
        
        return None
    
    async def send_notification(
        self,
        receiver_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """發送通知"""
        content = {
            'event_type': event_type,
            'data': data
        }
        await self.send_message(
            receiver_id=receiver_id,
            content=content,
            message_type=MessageType.NOTIFICATION
        )
    
    async def broadcast_message(
        self,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.MEDIUM
    ):
        """廣播訊息"""
        await self.send_message(
            receiver_id="*",
            content=content,
            message_type=MessageType.BROADCAST,
            priority=priority,
            delivery_mode=DeliveryMode.BROADCAST
        )
    
    async def receive_message(self, message_data: bytes):
        """接收訊息"""
        try:
            # 解析訊息
            message_dict = json.loads(message_data.decode('utf-8'))
            message = Message.from_dict(message_dict)
            
            # 更新統計
            self.stats['messages_received'] += 1
            self.stats['bytes_received'] += len(message_data)
            
            # 驗證訊息
            if not self.security_manager.verify_message(message):
                self.logger.warning(f"Message verification failed from {message.sender_id}")
                return
            
            # 檢查過期
            if message.is_expired():
                self.logger.debug(f"Received expired message {message.message_id}")
                return
            
            # 加入處理佇列
            await self.message_queue.enqueue(message)
            
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
            self.stats['messages_failed'] += 1
    
    async def _send_message_internal(self, message: Message) -> bool:
        """內部訊息發送實現"""
        try:
            # 路由訊息
            targets = self.message_router.route_message(message)
            
            if not targets:
                self.logger.warning(f"No route found for message to {message.receiver_id}")
                return False
            
            # 序列化訊息
            message_data = json.dumps(message.to_dict()).encode('utf-8')
            
            # 發送到目標（這裡是模擬實現）
            success_count = 0
            for target in targets:
                try:
                    # 在實際實現中，這裡會是真實的網路傳輸
                    await self._simulate_network_send(target, message_data)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send message to {target}: {e}")
            
            # 更新統計
            if success_count > 0:
                self.stats['messages_sent'] += 1
                self.stats['bytes_sent'] += len(message_data) * success_count
                return True
            else:
                self.stats['messages_failed'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            self.stats['messages_failed'] += 1
            return False
    
    async def _simulate_network_send(self, target: str, data: bytes):
        """模擬網路傳輸"""
        # 模擬網路延遲
        await asyncio.sleep(0.01)
        
        # 在實際實現中，這裡會使用 TCP/UDP/WebSocket 等協議
        # 進行真實的網路傳輸
        self.logger.debug(f"Simulated send to {target}: {len(data)} bytes")
    
    async def _message_processor_loop(self):
        """訊息處理循環"""
        while self.is_running:
            try:
                # 從佇列取出訊息
                message = await self.message_queue.dequeue()
                
                if message is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # 處理訊息
                await self._process_message(message)
                
            except Exception as e:
                self.logger.error(f"Error in message processor loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_message(self, message: Message):
        """處理訊息"""
        try:
            # 特殊訊息類型處理
            if message.message_type == MessageType.RESPONSE:
                await self._handle_response_message(message)
                return
            
            elif message.message_type == MessageType.HEARTBEAT:
                await self._handle_heartbeat_message(message)
                return
            
            # 使用註冊的處理器處理訊息
            response = None
            for handler in self.message_handlers:
                if handler.can_handle(message):
                    try:
                        handler_response = await handler.handle_message(message)
                        if handler_response:
                            response = handler_response
                            break
                    except Exception as e:
                        self.logger.error(f"Handler error: {e}")
            
            # 如果是REQUEST類型，發送回應
            if message.message_type == MessageType.REQUEST:
                if response is None:
                    # 創建預設回應
                    response = Message(
                        sender_id=self.agent_id,
                        receiver_id=message.sender_id,
                        message_type=MessageType.RESPONSE,
                        correlation_id=message.correlation_id,
                        content={'status': 'processed', 'message': 'Request processed successfully'}
                    )
                
                response.correlation_id = message.correlation_id
                response.signature = self.security_manager.sign_message(response)
                await self._send_message_internal(response)
            
            # 觸發事件
            if message.message_type == MessageType.NOTIFICATION:
                event_type = message.content.get('event_type')
                if event_type:
                    await self._emit_event(event_type, message.content.get('data', {}))
            
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {e}")
    
    async def _handle_response_message(self, message: Message):
        """處理回應訊息"""
        correlation_id = message.correlation_id
        if correlation_id and correlation_id in self.pending_requests:
            future = self.pending_requests.pop(correlation_id)
            if not future.done():
                future.set_result(message)
    
    async def _handle_heartbeat_message(self, message: Message):
        """處理心跳訊息"""
        sender_id = message.sender_id
        self.connected_agents.add(sender_id)
        
        # 回應心跳
        heartbeat_response = Message(
            sender_id=self.agent_id,
            receiver_id=sender_id,
            message_type=MessageType.HEARTBEAT,
            content={'status': 'alive', 'timestamp': datetime.now().isoformat()}
        )
        heartbeat_response.signature = self.security_manager.sign_message(heartbeat_response)
        await self._send_message_internal(heartbeat_response)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """觸發事件"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循環"""
        while self.is_running:
            try:
                # 發送心跳到所有已連接代理
                if self.connected_agents:
                    await self.broadcast_message(
                        content={'type': 'heartbeat', 'timestamp': datetime.now().isoformat()},
                        priority=MessagePriority.LOW
                    )
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計數據"""
        return {
            **self.stats,
            'connected_agents': len(self.connected_agents),
            'pending_requests': len(self.pending_requests),
            'queue_size': self.message_queue.size()
        }


# 使用範例
if __name__ == "__main__":
    class EchoHandler(MessageHandler):
        """回音處理器"""
        
        async def handle_message(self, message: Message) -> Optional[Message]:
            if message.content.get('action') == 'echo':
                return Message(
                    sender_id=message.receiver_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    content={'echo': message.content.get('text', '')}
                )
            return None
        
        def can_handle(self, message: Message) -> bool:
            return message.content.get('action') == 'echo'
    
    async def main():
        # 創建通訊協議實例
        protocol_a = CommunicationProtocol("agent_a", "secret_key_123")
        protocol_b = CommunicationProtocol("agent_b", "secret_key_123")
        
        # 添加處理器
        protocol_b.add_message_handler(EchoHandler())
        
        # 建立信任關係
        protocol_a.security_manager.add_trusted_agent("agent_b")
        protocol_b.security_manager.add_trusted_agent("agent_a")
        
        # 註冊路由
        protocol_a.message_router.register_agent("agent_b", "tcp://localhost:8001")
        protocol_b.message_router.register_agent("agent_a", "tcp://localhost:8000")
        
        # 啟動協議
        await protocol_a.start()
        await protocol_b.start()
        
        # 發送測試訊息
        response = await protocol_a.send_message(
            receiver_id="agent_b",
            content={'action': 'echo', 'text': 'Hello, Agent B!'},
            message_type=MessageType.REQUEST,
            timeout=5.0
        )
        
        if response:
            print(f"Received response: {response.content}")
        else:
            print("No response received")
        
        # 獲取統計
        stats_a = protocol_a.get_statistics()
        stats_b = protocol_b.get_statistics()
        
        print(f"Agent A stats: {stats_a}")
        print(f"Agent B stats: {stats_b}")
        
        # 停止協議
        await protocol_a.stop()
        await protocol_b.stop()
    
    asyncio.run(main()) 