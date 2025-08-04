#!/usr/bin/env python3
"""
Multi-Agent Pattern: Conflict Resolution
衝突解決機制 - 處理多代理系統中的資源競爭和任務衝突

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timedelta
import random
from collections import defaultdict, deque


class ConflictType(Enum):
    """衝突類型"""
    RESOURCE_COMPETITION = "resource_competition"
    TASK_PRIORITY = "task_priority"
    CAPABILITY_OVERLAP = "capability_overlap"
    DEADLINE_CONFLICT = "deadline_conflict"
    DEPENDENCY_CYCLE = "dependency_cycle"
    AUTHORITY_DISPUTE = "authority_dispute"


class ResolutionStrategy(Enum):
    """解決策略"""
    PRIORITY_BASED = "priority_based"
    FIRST_COME_FIRST_SERVE = "first_come_first_serve"
    ROUND_ROBIN = "round_robin"
    AUCTION = "auction"
    NEGOTIATION = "negotiation"
    VOTING = "voting"
    ARBITRATION = "arbitration"


class ConflictStatus(Enum):
    """衝突狀態"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class Resource:
    """資源定義"""
    resource_id: str
    resource_type: str
    capacity: int
    available: int
    properties: Dict[str, Any] = field(default_factory=dict)
    locked_by: Optional[str] = None
    lock_expires_at: Optional[datetime] = None
    
    def is_available(self, required_amount: int = 1) -> bool:
        """檢查資源是否可用"""
        if self.locked_by and self.lock_expires_at:
            if datetime.now() > self.lock_expires_at:
                self.unlock()
        
        return self.available >= required_amount and self.locked_by is None
    
    def reserve(self, amount: int, agent_id: str, duration: timedelta) -> bool:
        """預留資源"""
        if not self.is_available(amount):
            return False
        
        self.available -= amount
        self.locked_by = agent_id
        self.lock_expires_at = datetime.now() + duration
        return True
    
    def release(self, amount: int, agent_id: str) -> bool:
        """釋放資源"""
        if self.locked_by == agent_id:
            self.available = min(self.capacity, self.available + amount)
            self.unlock()
            return True
        return False
    
    def unlock(self):
        """解鎖資源"""
        self.locked_by = None
        self.lock_expires_at = None


@dataclass
class ConflictCase:
    """衝突案例"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.RESOURCE_COMPETITION
    involved_agents: List[str] = field(default_factory=list)
    conflicted_resources: List[str] = field(default_factory=list)
    description: str = ""
    priority: int = 5  # 1-10, 10 為最高
    status: ConflictStatus = ConflictStatus.DETECTED
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentBid:
    """代理競標"""
    agent_id: str
    resource_id: str
    bid_amount: float
    priority: int
    justification: str = ""
    valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))


@dataclass
class NegotiationProposal:
    """協商提案"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposer_id: str = ""
    target_agents: List[str] = field(default_factory=list)
    proposal_type: str = ""  # 'resource_sharing', 'task_swap', 'time_division'
    terms: Dict[str, Any] = field(default_factory=dict)
    benefits: Dict[str, float] = field(default_factory=dict)  # agent_id -> benefit_score
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=10))
    responses: Dict[str, bool] = field(default_factory=dict)  # agent_id -> accept/reject


class ConflictResolver(ABC):
    """衝突解決器抽象基類"""
    
    @abstractmethod
    async def can_resolve(self, conflict: ConflictCase) -> bool:
        """檢查是否能解決此衝突"""
        pass
    
    @abstractmethod
    async def resolve_conflict(self, conflict: ConflictCase) -> Dict[str, Any]:
        """解決衝突"""
        pass
    
    @abstractmethod
    def get_strategy(self) -> ResolutionStrategy:
        """獲取解決策略"""
        pass


class PriorityBasedResolver(ConflictResolver):
    """基於優先級的解決器"""
    
    def __init__(self, agent_priorities: Dict[str, int]):
        self.agent_priorities = agent_priorities
    
    async def can_resolve(self, conflict: ConflictCase) -> bool:
        return conflict.conflict_type in [
            ConflictType.RESOURCE_COMPETITION,
            ConflictType.TASK_PRIORITY
        ]
    
    async def resolve_conflict(self, conflict: ConflictCase) -> Dict[str, Any]:
        # 根據代理優先級排序
        sorted_agents = sorted(
            conflict.involved_agents,
            key=lambda agent_id: self.agent_priorities.get(agent_id, 0),
            reverse=True
        )
        
        return {
            'strategy': self.get_strategy().value,
            'winner': sorted_agents[0],
            'order': sorted_agents,
            'reasoning': f"Resolved by agent priority: {self.agent_priorities}"
        }
    
    def get_strategy(self) -> ResolutionStrategy:
        return ResolutionStrategy.PRIORITY_BASED


class AuctionBasedResolver(ConflictResolver):
    """基於拍賣的解決器"""
    
    def __init__(self):
        self.active_auctions: Dict[str, List[AgentBid]] = {}
    
    async def can_resolve(self, conflict: ConflictCase) -> bool:
        return conflict.conflict_type == ConflictType.RESOURCE_COMPETITION
    
    async def resolve_conflict(self, conflict: ConflictCase) -> Dict[str, Any]:
        # 收集競標
        auction_id = conflict.conflict_id
        bids = await self._collect_bids(conflict)
        
        if not bids:
            return {
                'strategy': self.get_strategy().value,
                'success': False,
                'reason': 'No bids received'
            }
        
        # 選擇最高競標者
        winning_bid = max(bids, key=lambda bid: bid.bid_amount)
        
        return {
            'strategy': self.get_strategy().value,
            'winner': winning_bid.agent_id,
            'winning_bid': winning_bid.bid_amount,
            'all_bids': [(bid.agent_id, bid.bid_amount) for bid in bids],
            'reasoning': f"Highest bid: {winning_bid.bid_amount} from {winning_bid.agent_id}"
        }
    
    async def _collect_bids(self, conflict: ConflictCase) -> List[AgentBid]:
        """收集競標（模擬實現）"""
        bids = []
        for agent_id in conflict.involved_agents:
            # 模擬競標
            bid = AgentBid(
                agent_id=agent_id,
                resource_id=conflict.conflicted_resources[0] if conflict.conflicted_resources else "",
                bid_amount=random.uniform(10, 100),
                priority=random.randint(1, 10)
            )
            bids.append(bid)
        
        return bids
    
    def get_strategy(self) -> ResolutionStrategy:
        return ResolutionStrategy.AUCTION


class NegotiationBasedResolver(ConflictResolver):
    """基於協商的解決器"""
    
    def __init__(self):
        self.active_negotiations: Dict[str, List[NegotiationProposal]] = {}
        self.negotiation_timeout = timedelta(minutes=5)
    
    async def can_resolve(self, conflict: ConflictCase) -> bool:
        return len(conflict.involved_agents) >= 2
    
    async def resolve_conflict(self, conflict: ConflictCase) -> Dict[str, Any]:
        # 生成協商提案
        proposals = await self._generate_proposals(conflict)
        
        # 執行協商過程
        successful_proposal = await self._conduct_negotiation(proposals)
        
        if successful_proposal:
            return {
                'strategy': self.get_strategy().value,
                'success': True,
                'agreement': successful_proposal.terms,
                'participants': successful_proposal.target_agents,
                'benefits': successful_proposal.benefits
            }
        else:
            return {
                'strategy': self.get_strategy().value,
                'success': False,
                'reason': 'No acceptable agreement reached'
            }
    
    async def _generate_proposals(self, conflict: ConflictCase) -> List[NegotiationProposal]:
        """生成協商提案"""
        proposals = []
        
        if conflict.conflict_type == ConflictType.RESOURCE_COMPETITION:
            # 資源分享提案
            for agent_id in conflict.involved_agents:
                proposal = NegotiationProposal(
                    proposer_id=agent_id,
                    target_agents=[a for a in conflict.involved_agents if a != agent_id],
                    proposal_type="resource_sharing",
                    terms={
                        'resource_id': conflict.conflicted_resources[0] if conflict.conflicted_resources else "",
                        'sharing_schedule': self._generate_sharing_schedule(conflict.involved_agents),
                        'duration': 'flexible'
                    }
                )
                proposals.append(proposal)
        
        elif conflict.conflict_type == ConflictType.TASK_PRIORITY:
            # 任務交換提案
            for agent_id in conflict.involved_agents:
                proposal = NegotiationProposal(
                    proposer_id=agent_id,
                    target_agents=[a for a in conflict.involved_agents if a != agent_id],
                    proposal_type="task_swap",
                    terms={
                        'swap_type': 'priority_adjustment',
                        'compensation': 'future_priority_boost'
                    }
                )
                proposals.append(proposal)
        
        return proposals
    
    def _generate_sharing_schedule(self, agents: List[str]) -> Dict[str, List[str]]:
        """生成資源分享時程表"""
        schedule = {}
        time_slots = ['09:00-12:00', '12:00-15:00', '15:00-18:00']
        
        for i, agent_id in enumerate(agents):
            if i < len(time_slots):
                schedule[time_slots[i]] = [agent_id]
        
        return schedule
    
    async def _conduct_negotiation(self, proposals: List[NegotiationProposal]) -> Optional[NegotiationProposal]:
        """執行協商過程"""
        for proposal in proposals:
            # 模擬協商回應
            accepted_count = 0
            for target_agent in proposal.target_agents:
                # 簡單的接受機率模型
                accept_probability = self._calculate_acceptance_probability(proposal, target_agent)
                if random.random() < accept_probability:
                    proposal.responses[target_agent] = True
                    accepted_count += 1
                else:
                    proposal.responses[target_agent] = False
            
            # 檢查是否達成共識
            if accepted_count == len(proposal.target_agents):
                return proposal
        
        return None
    
    def _calculate_acceptance_probability(self, proposal: NegotiationProposal, agent_id: str) -> float:
        """計算接受機率"""
        base_probability = 0.5
        
        # 根據提案類型調整機率
        if proposal.proposal_type == "resource_sharing":
            base_probability += 0.3
        elif proposal.proposal_type == "task_swap":
            base_probability += 0.2
        
        # 根據收益調整
        benefit = proposal.benefits.get(agent_id, 0)
        if benefit > 0:
            base_probability += min(0.3, benefit / 100)
        
        return min(1.0, base_probability)
    
    def get_strategy(self) -> ResolutionStrategy:
        return ResolutionStrategy.NEGOTIATION


class VotingBasedResolver(ConflictResolver):
    """基於投票的解決器"""
    
    def __init__(self):
        self.voting_timeout = timedelta(minutes=3)
    
    async def can_resolve(self, conflict: ConflictCase) -> bool:
        return len(conflict.involved_agents) >= 3
    
    async def resolve_conflict(self, conflict: ConflictCase) -> Dict[str, Any]:
        # 收集投票選項
        options = self._generate_voting_options(conflict)
        
        # 執行投票
        votes = await self._conduct_voting(conflict.involved_agents, options)
        
        # 統計結果
        winner = max(votes.keys(), key=lambda option: len(votes[option]))
        
        return {
            'strategy': self.get_strategy().value,
            'winner': winner,
            'votes': {option: len(voters) for option, voters in votes.items()},
            'detailed_votes': votes
        }
    
    def _generate_voting_options(self, conflict: ConflictCase) -> List[str]:
        """生成投票選項"""
        if conflict.conflict_type == ConflictType.RESOURCE_COMPETITION:
            return conflict.involved_agents
        elif conflict.conflict_type == ConflictType.TASK_PRIORITY:
            return ['priority_order_1', 'priority_order_2', 'equal_priority']
        else:
            return ['option_a', 'option_b', 'option_c']
    
    async def _conduct_voting(self, voters: List[str], options: List[str]) -> Dict[str, List[str]]:
        """執行投票"""
        votes = {option: [] for option in options}
        
        # 模擬投票過程
        for voter in voters:
            # 隨機選擇一個選項（在實際實現中會是真實的投票）
            chosen_option = random.choice(options)
            votes[chosen_option].append(voter)
        
        return votes
    
    def get_strategy(self) -> ResolutionStrategy:
        return ResolutionStrategy.VOTING


class ConflictDetector:
    """衝突檢測器"""
    
    def __init__(self):
        self.detection_rules: List[Callable] = []
        self.resource_usage_history: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)
        self.task_schedules: Dict[str, List[Tuple[str, datetime, datetime]]] = defaultdict(list)
    
    def add_detection_rule(self, rule: Callable):
        """添加檢測規則"""
        self.detection_rules.append(rule)
    
    def detect_conflicts(
        self,
        agents: List[str],
        resources: Dict[str, Resource],
        current_tasks: Dict[str, Any]
    ) -> List[ConflictCase]:
        """檢測衝突"""
        conflicts = []
        
        # 檢測資源競爭
        resource_conflicts = self._detect_resource_conflicts(agents, resources)
        conflicts.extend(resource_conflicts)
        
        # 檢測任務優先級衝突
        priority_conflicts = self._detect_priority_conflicts(current_tasks)
        conflicts.extend(priority_conflicts)
        
        # 檢測截止日期衝突
        deadline_conflicts = self._detect_deadline_conflicts(current_tasks)
        conflicts.extend(deadline_conflicts)
        
        # 應用自定義檢測規則
        for rule in self.detection_rules:
            try:
                rule_conflicts = rule(agents, resources, current_tasks)
                if rule_conflicts:
                    conflicts.extend(rule_conflicts)
            except Exception as e:
                logging.error(f"Error in detection rule: {e}")
        
        return conflicts
    
    def _detect_resource_conflicts(
        self,
        agents: List[str],
        resources: Dict[str, Resource]
    ) -> List[ConflictCase]:
        """檢測資源競爭衝突"""
        conflicts = []
        
        for resource_id, resource in resources.items():
            # 檢查是否有多個代理同時需要同一資源
            competing_agents = []
            
            # 模擬檢測邏輯（在實際實現中會基於實際的資源請求）
            for agent_id in agents:
                if self._agent_needs_resource(agent_id, resource_id):
                    competing_agents.append(agent_id)
            
            if len(competing_agents) > 1:
                conflict = ConflictCase(
                    conflict_type=ConflictType.RESOURCE_COMPETITION,
                    involved_agents=competing_agents,
                    conflicted_resources=[resource_id],
                    description=f"Multiple agents competing for resource {resource_id}",
                    priority=7
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_priority_conflicts(self, current_tasks: Dict[str, Any]) -> List[ConflictCase]:
        """檢測任務優先級衝突"""
        conflicts = []
        
        # 檢查是否有優先級相同的任務
        priority_groups = defaultdict(list)
        for task_id, task_info in current_tasks.items():
            priority = task_info.get('priority', 5)
            priority_groups[priority].append((task_id, task_info))
        
        for priority, tasks in priority_groups.items():
            if len(tasks) > 1 and priority >= 8:  # 高優先級任務衝突
                involved_agents = [task_info.get('assigned_agent') for _, task_info in tasks]
                involved_agents = [agent for agent in involved_agents if agent]
                
                if len(involved_agents) > 1:
                    conflict = ConflictCase(
                        conflict_type=ConflictType.TASK_PRIORITY,
                        involved_agents=involved_agents,
                        description=f"Multiple high-priority tasks with same priority level {priority}",
                        priority=priority
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_deadline_conflicts(self, current_tasks: Dict[str, Any]) -> List[ConflictCase]:
        """檢測截止日期衝突"""
        conflicts = []
        
        # 檢查是否有無法在截止日期前完成的任務
        current_time = datetime.now()
        
        for task_id, task_info in current_tasks.items():
            deadline = task_info.get('deadline')
            estimated_duration = task_info.get('estimated_duration')
            assigned_agent = task_info.get('assigned_agent')
            
            if deadline and estimated_duration and assigned_agent:
                if isinstance(deadline, str):
                    deadline = datetime.fromisoformat(deadline)
                
                if current_time + estimated_duration > deadline:
                    conflict = ConflictCase(
                        conflict_type=ConflictType.DEADLINE_CONFLICT,
                        involved_agents=[assigned_agent],
                        description=f"Task {task_id} cannot meet deadline",
                        priority=8
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _agent_needs_resource(self, agent_id: str, resource_id: str) -> bool:
        """檢查代理是否需要資源（模擬）"""
        # 在實際實現中，這會查詢代理的實際資源需求
        return random.random() < 0.3  # 30% 機率需要資源


class ConflictResolutionManager:
    """
    衝突解決管理器
    
    統一管理多代理系統中的各種衝突檢測和解決機制。
    """
    
    def __init__(
        self,
        default_timeout: timedelta = timedelta(minutes=5),
        max_resolution_attempts: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化衝突解決管理器
        
        Args:
            default_timeout: 預設解決超時時間
            max_resolution_attempts: 最大解決嘗試次數
            logger: 日誌記錄器
        """
        self.default_timeout = default_timeout
        self.max_resolution_attempts = max_resolution_attempts
        self.logger = logger or logging.getLogger(__name__)
        
        # 核心組件
        self.conflict_detector = ConflictDetector()
        self.resolvers: List[ConflictResolver] = []
        
        # 狀態管理
        self.active_conflicts: Dict[str, ConflictCase] = {}
        self.resolved_conflicts: Dict[str, ConflictCase] = {}
        self.resources: Dict[str, Resource] = {}
        
        # 統計數據
        self.stats = {
            'total_conflicts': 0,
            'resolved_conflicts': 0,
            'failed_resolutions': 0,
            'average_resolution_time': 0.0,
            'resolution_strategies': defaultdict(int)
        }
        
        # 預設解決器
        self._setup_default_resolvers()
    
    def _setup_default_resolvers(self):
        """設定預設解決器"""
        # 添加基本解決器
        self.resolvers.extend([
            PriorityBasedResolver({}),
            AuctionBasedResolver(),
            NegotiationBasedResolver(),
            VotingBasedResolver()
        ])
    
    def add_resolver(self, resolver: ConflictResolver):
        """添加解決器"""
        self.resolvers.append(resolver)
    
    def remove_resolver(self, resolver: ConflictResolver):
        """移除解決器"""
        if resolver in self.resolvers:
            self.resolvers.remove(resolver)
    
    def register_resource(self, resource: Resource):
        """註冊資源"""
        self.resources[resource.resource_id] = resource
    
    def unregister_resource(self, resource_id: str):
        """註銷資源"""
        self.resources.pop(resource_id, None)
    
    async def monitor_and_resolve(
        self,
        agents: List[str],
        current_tasks: Dict[str, Any]
    ):
        """監控並解決衝突"""
        # 檢測衝突
        detected_conflicts = self.conflict_detector.detect_conflicts(
            agents, self.resources, current_tasks
        )
        
        # 處理新衝突
        for conflict in detected_conflicts:
            if conflict.conflict_id not in self.active_conflicts:
                await self._handle_new_conflict(conflict)
        
        # 檢查活動衝突的解決進度
        await self._check_active_conflicts()
    
    async def _handle_new_conflict(self, conflict: ConflictCase):
        """處理新衝突"""
        self.active_conflicts[conflict.conflict_id] = conflict
        self.stats['total_conflicts'] += 1
        
        self.logger.info(f"New conflict detected: {conflict.conflict_type.value} involving {conflict.involved_agents}")
        
        # 嘗試解決衝突
        await self._attempt_resolution(conflict)
    
    async def _attempt_resolution(self, conflict: ConflictCase):
        """嘗試解決衝突"""
        conflict.status = ConflictStatus.ANALYZING
        
        # 選擇合適的解決器
        suitable_resolver = await self._select_resolver(conflict)
        
        if not suitable_resolver:
            conflict.status = ConflictStatus.FAILED
            self.logger.warning(f"No suitable resolver found for conflict {conflict.conflict_id}")
            return
        
        conflict.status = ConflictStatus.RESOLVING
        conflict.resolution_strategy = suitable_resolver.get_strategy()
        
        try:
            # 執行解決
            resolution_result = await asyncio.wait_for(
                suitable_resolver.resolve_conflict(conflict),
                timeout=self.default_timeout.total_seconds()
            )
            
            # 應用解決方案
            if await self._apply_resolution(conflict, resolution_result):
                conflict.status = ConflictStatus.RESOLVED
                conflict.resolved_at = datetime.now()
                conflict.resolution_result = resolution_result
                
                # 移動到已解決衝突
                self.resolved_conflicts[conflict.conflict_id] = conflict
                self.active_conflicts.pop(conflict.conflict_id, None)
                
                # 更新統計
                self.stats['resolved_conflicts'] += 1
                self.stats['resolution_strategies'][conflict.resolution_strategy.value] += 1
                
                self.logger.info(f"Conflict {conflict.conflict_id} resolved using {conflict.resolution_strategy.value}")
            else:
                conflict.status = ConflictStatus.FAILED
                self.stats['failed_resolutions'] += 1
        
        except asyncio.TimeoutError:
            conflict.status = ConflictStatus.ESCALATED
            self.logger.warning(f"Conflict {conflict.conflict_id} resolution timed out")
        
        except Exception as e:
            conflict.status = ConflictStatus.FAILED
            self.stats['failed_resolutions'] += 1
            self.logger.error(f"Error resolving conflict {conflict.conflict_id}: {e}")
    
    async def _select_resolver(self, conflict: ConflictCase) -> Optional[ConflictResolver]:
        """選擇合適的解決器"""
        suitable_resolvers = []
        
        for resolver in self.resolvers:
            try:
                if await resolver.can_resolve(conflict):
                    suitable_resolvers.append(resolver)
            except Exception as e:
                self.logger.error(f"Error checking resolver capability: {e}")
        
        if not suitable_resolvers:
            return None
        
        # 根據衝突類型和優先級選擇最佳解決器
        if conflict.priority >= 8:  # 高優先級衝突
            # 優先選擇快速解決策略
            for resolver in suitable_resolvers:
                if resolver.get_strategy() in [ResolutionStrategy.PRIORITY_BASED, ResolutionStrategy.FIRST_COME_FIRST_SERVE]:
                    return resolver
        
        # 預設選擇第一個合適的解決器
        return suitable_resolvers[0]
    
    async def _apply_resolution(self, conflict: ConflictCase, resolution_result: Dict[str, Any]) -> bool:
        """應用解決方案"""
        try:
            strategy = resolution_result.get('strategy')
            
            if strategy == ResolutionStrategy.PRIORITY_BASED.value:
                return await self._apply_priority_resolution(conflict, resolution_result)
            
            elif strategy == ResolutionStrategy.AUCTION.value:
                return await self._apply_auction_resolution(conflict, resolution_result)
            
            elif strategy == ResolutionStrategy.NEGOTIATION.value:
                return await self._apply_negotiation_resolution(conflict, resolution_result)
            
            elif strategy == ResolutionStrategy.VOTING.value:
                return await self._apply_voting_resolution(conflict, resolution_result)
            
            else:
                self.logger.warning(f"Unknown resolution strategy: {strategy}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error applying resolution: {e}")
            return False
    
    async def _apply_priority_resolution(self, conflict: ConflictCase, result: Dict[str, Any]) -> bool:
        """應用優先級解決方案"""
        winner = result.get('winner')
        if not winner:
            return False
        
        # 分配資源給獲勝者
        for resource_id in conflict.conflicted_resources:
            if resource_id in self.resources:
                resource = self.resources[resource_id]
                resource.reserve(1, winner, timedelta(hours=1))
        
        return True
    
    async def _apply_auction_resolution(self, conflict: ConflictCase, result: Dict[str, Any]) -> bool:
        """應用拍賣解決方案"""
        winner = result.get('winner')
        if not winner:
            return False
        
        # 分配資源給最高競標者
        for resource_id in conflict.conflicted_resources:
            if resource_id in self.resources:
                resource = self.resources[resource_id]
                resource.reserve(1, winner, timedelta(hours=1))
        
        return True
    
    async def _apply_negotiation_resolution(self, conflict: ConflictCase, result: Dict[str, Any]) -> bool:
        """應用協商解決方案"""
        if not result.get('success'):
            return False
        
        agreement = result.get('agreement', {})
        
        # 根據協商結果分配資源
        if 'sharing_schedule' in agreement:
            schedule = agreement['sharing_schedule']
            # 實施資源分享計劃
            for time_slot, agents in schedule.items():
                # 在實際實現中，這裡會設定時間基的資源分配
                pass
        
        return True
    
    async def _apply_voting_resolution(self, conflict: ConflictCase, result: Dict[str, Any]) -> bool:
        """應用投票解決方案"""
        winner = result.get('winner')
        if not winner:
            return False
        
        # 根據投票結果執行決定
        if winner in conflict.involved_agents:
            # 分配資源給獲勝代理
            for resource_id in conflict.conflicted_resources:
                if resource_id in self.resources:
                    resource = self.resources[resource_id]
                    resource.reserve(1, winner, timedelta(hours=1))
        
        return True
    
    async def _check_active_conflicts(self):
        """檢查活動衝突"""
        current_time = datetime.now()
        timeout_conflicts = []
        
        for conflict in self.active_conflicts.values():
            # 檢查是否超時
            if current_time - conflict.created_at > self.default_timeout:
                timeout_conflicts.append(conflict)
        
        # 處理超時衝突
        for conflict in timeout_conflicts:
            if conflict.status == ConflictStatus.RESOLVING:
                conflict.status = ConflictStatus.ESCALATED
                self.logger.warning(f"Conflict {conflict.conflict_id} escalated due to timeout")
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """獲取衝突統計"""
        return {
            **self.stats,
            'active_conflicts': len(self.active_conflicts),
            'total_resources': len(self.resources),
            'available_resolvers': len(self.resolvers)
        }
    
    def get_active_conflicts(self) -> List[ConflictCase]:
        """獲取活動衝突列表"""
        return list(self.active_conflicts.values())


# 使用範例
if __name__ == "__main__":
    async def main():
        # 創建衝突解決管理器
        manager = ConflictResolutionManager()
        
        # 註冊資源
        resource1 = Resource(
            resource_id="database_connection",
            resource_type="database",
            capacity=5,
            available=5
        )
        manager.register_resource(resource1)
        
        # 模擬衝突場景
        agents = ["agent_a", "agent_b", "agent_c"]
        current_tasks = {
            "task_1": {
                "assigned_agent": "agent_a",
                "priority": 9,
                "deadline": (datetime.now() + timedelta(hours=1)).isoformat(),
                "estimated_duration": timedelta(hours=2)
            },
            "task_2": {
                "assigned_agent": "agent_b", 
                "priority": 9,
                "deadline": (datetime.now() + timedelta(hours=1)).isoformat(),
                "estimated_duration": timedelta(hours=1.5)
            }
        }
        
        # 監控並解決衝突
        await manager.monitor_and_resolve(agents, current_tasks)
        
        # 獲取統計
        stats = manager.get_conflict_statistics()
        print(f"Conflict statistics: {stats}")
        
        # 獲取活動衝突
        active_conflicts = manager.get_active_conflicts()
        for conflict in active_conflicts:
            print(f"Active conflict: {conflict.conflict_type.value} - {conflict.status.value}")
    
    asyncio.run(main()) 