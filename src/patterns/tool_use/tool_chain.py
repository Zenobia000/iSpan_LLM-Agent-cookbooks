#!/usr/bin/env python3
"""
Tool Use Pattern: Tool Chain Orchestration
工具鏈編排 - 支援複雜工具組合、流水線處理和條件執行

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
from .robust_tool_wrapper import RobustToolWrapper, ToolResult


class ExecutionMode(Enum):
    """執行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"
    DAG = "dag"  # Directed Acyclic Graph


class NodeStatus(Enum):
    """節點狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class ChainContext:
    """鏈上下文"""
    variables: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, ToolResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取變數值"""
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any):
        """設定變數值"""
        self.variables[key] = value
    
    def get_result(self, node_id: str) -> Optional[ToolResult]:
        """獲取節點執行結果"""
        return self.results.get(node_id)


@dataclass
class ExecutionResult:
    """執行結果"""
    success: bool
    results: Dict[str, ToolResult]
    execution_time: float
    total_nodes: int
    successful_nodes: int
    failed_nodes: int
    skipped_nodes: int
    final_result: Any = None
    error_details: List[Dict[str, Any]] = field(default_factory=list)


class ChainNode(ABC):
    """鏈節點抽象基類"""
    
    def __init__(
        self,
        node_id: str,
        name: Optional[str] = None,
        retry_count: int = 0,
        timeout: Optional[float] = None
    ):
        self.node_id = node_id
        self.name = name or node_id
        self.retry_count = retry_count
        self.timeout = timeout
        self.status = NodeStatus.PENDING
        self.dependencies: List[str] = []
        self.result: Optional[ToolResult] = None
        self.execution_time: float = 0.0
        
    @abstractmethod
    async def execute(self, context: ChainContext) -> ToolResult:
        """執行節點"""
        pass
    
    def add_dependency(self, node_id: str):
        """添加依賴節點"""
        if node_id not in self.dependencies:
            self.dependencies.append(node_id)
    
    def can_execute(self, context: ChainContext) -> bool:
        """檢查是否可以執行"""
        if self.status != NodeStatus.PENDING:
            return False
        
        # 檢查依賴節點是否都已完成
        for dep_id in self.dependencies:
            dep_result = context.get_result(dep_id)
            if not dep_result or not dep_result.success:
                return False
        
        return True


class ToolNode(ChainNode):
    """工具節點"""
    
    def __init__(
        self,
        node_id: str,
        tool: Union[Callable, RobustToolWrapper],
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[str] = None,
        **kwargs
    ):
        super().__init__(node_id, **kwargs)
        self.tool = tool if isinstance(tool, RobustToolWrapper) else RobustToolWrapper(tool)
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping
        
    async def execute(self, context: ChainContext) -> ToolResult:
        """執行工具節點"""
        self.status = NodeStatus.RUNNING
        start_time = time.time()
        
        try:
            # 準備輸入參數
            kwargs = {}
            for param_name, context_key in self.input_mapping.items():
                if context_key.startswith("$"):
                    # 從其他節點結果獲取
                    node_id = context_key[1:]
                    node_result = context.get_result(node_id)
                    if node_result:
                        kwargs[param_name] = node_result.result
                else:
                    # 從上下文變數獲取
                    kwargs[param_name] = context.get(context_key)
            
            # 執行工具
            if self.timeout:
                result = await asyncio.wait_for(
                    self.tool.async_call(**kwargs),
                    timeout=self.timeout
                )
            else:
                result = await self.tool.async_call(**kwargs)
            
            # 保存結果到上下文
            if self.output_mapping and result.success:
                context.set(self.output_mapping, result.result)
            
            self.status = NodeStatus.COMPLETED if result.success else NodeStatus.FAILED
            self.result = result
            self.execution_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            self.execution_time = time.time() - start_time
            self.status = NodeStatus.FAILED
            error_result = ToolResult(
                success=False,
                error=e,
                execution_time=self.execution_time,
                tool_name=self.name
            )
            self.result = error_result
            return error_result


class ConditionalNode(ChainNode):
    """條件節點"""
    
    def __init__(
        self,
        node_id: str,
        condition: Callable[[ChainContext], bool],
        true_branch: List[str],
        false_branch: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(node_id, **kwargs)
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch or []
        
    async def execute(self, context: ChainContext) -> ToolResult:
        """執行條件節點"""
        self.status = NodeStatus.RUNNING
        start_time = time.time()
        
        try:
            # 評估條件
            condition_result = self.condition(context)
            
            # 設定分支信息到上下文
            branch_info = {
                'condition_result': condition_result,
                'selected_branch': self.true_branch if condition_result else self.false_branch,
                'skipped_branch': self.false_branch if condition_result else self.true_branch
            }
            context.set(f"{self.node_id}_branch", branch_info)
            
            self.status = NodeStatus.COMPLETED
            self.execution_time = time.time() - start_time
            
            result = ToolResult(
                success=True,
                result=condition_result,
                execution_time=self.execution_time,
                tool_name=self.name
            )
            self.result = result
            return result
            
        except Exception as e:
            self.execution_time = time.time() - start_time
            self.status = NodeStatus.FAILED
            error_result = ToolResult(
                success=False,
                error=e,
                execution_time=self.execution_time,
                tool_name=self.name
            )
            self.result = error_result
            return error_result


class TransformNode(ChainNode):
    """轉換節點"""
    
    def __init__(
        self,
        node_id: str,
        transform_func: Callable[[ChainContext], Any],
        output_key: str,
        **kwargs
    ):
        super().__init__(node_id, **kwargs)
        self.transform_func = transform_func
        self.output_key = output_key
        
    async def execute(self, context: ChainContext) -> ToolResult:
        """執行轉換節點"""
        self.status = NodeStatus.RUNNING
        start_time = time.time()
        
        try:
            # 執行轉換
            result_value = self.transform_func(context)
            
            # 保存結果到上下文
            context.set(self.output_key, result_value)
            
            self.status = NodeStatus.COMPLETED
            self.execution_time = time.time() - start_time
            
            result = ToolResult(
                success=True,
                result=result_value,
                execution_time=self.execution_time,
                tool_name=self.name
            )
            self.result = result
            return result
            
        except Exception as e:
            self.execution_time = time.time() - start_time
            self.status = NodeStatus.FAILED
            error_result = ToolResult(
                success=False,
                error=e,
                execution_time=self.execution_time,
                tool_name=self.name
            )
            self.result = error_result
            return error_result


class ToolChain:
    """
    工具鏈編排器
    
    支援複雜的工具組合、流水線處理、條件分支和並行執行。
    """
    
    def __init__(
        self,
        name: str,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        max_parallel: int = 5,
        timeout: Optional[float] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化工具鏈
        
        Args:
            name: 鏈名稱
            execution_mode: 執行模式
            max_parallel: 最大並行數
            timeout: 總超時時間
            logger: 日誌記錄器
        """
        self.name = name
        self.execution_mode = execution_mode
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        self.nodes: Dict[str, ChainNode] = {}
        self.execution_order: List[str] = []
        self.context = ChainContext()
        
    def add_tool(
        self,
        node_id: str,
        tool: Union[Callable, RobustToolWrapper],
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> 'ToolChain':
        """
        添加工具節點
        
        Args:
            node_id: 節點ID
            tool: 工具函數或包裝器
            input_mapping: 輸入參數映射
            output_mapping: 輸出變數名
            dependencies: 依賴節點列表
            
        Returns:
            ToolChain: 鏈實例（支援鏈式調用）
        """
        node = ToolNode(
            node_id=node_id,
            tool=tool,
            input_mapping=input_mapping,
            output_mapping=output_mapping,
            **kwargs
        )
        
        if dependencies:
            for dep in dependencies:
                node.add_dependency(dep)
        
        self.nodes[node_id] = node
        return self
    
    def add_condition(
        self,
        node_id: str,
        condition: Callable[[ChainContext], bool],
        true_branch: List[str],
        false_branch: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> 'ToolChain':
        """添加條件節點"""
        node = ConditionalNode(
            node_id=node_id,
            condition=condition,
            true_branch=true_branch,
            false_branch=false_branch,
            **kwargs
        )
        
        if dependencies:
            for dep in dependencies:
                node.add_dependency(dep)
        
        self.nodes[node_id] = node
        return self
    
    def add_transform(
        self,
        node_id: str,
        transform_func: Callable[[ChainContext], Any],
        output_key: str,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> 'ToolChain':
        """添加轉換節點"""
        node = TransformNode(
            node_id=node_id,
            transform_func=transform_func,
            output_key=output_key,
            **kwargs
        )
        
        if dependencies:
            for dep in dependencies:
                node.add_dependency(dep)
        
        self.nodes[node_id] = node
        return self
    
    def set_variable(self, key: str, value: Any) -> 'ToolChain':
        """設定上下文變數"""
        self.context.set(key, value)
        return self
    
    async def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        執行工具鏈
        
        Args:
            initial_context: 初始上下文變數
            
        Returns:
            ExecutionResult: 執行結果
        """
        start_time = time.time()
        
        # 初始化上下文
        if initial_context:
            self.context.variables.update(initial_context)
        
        # 重置節點狀態
        for node in self.nodes.values():
            node.status = NodeStatus.PENDING
            node.result = None
        
        self.logger.info(f"開始執行工具鏈: {self.name}")
        
        try:
            if self.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential()
            elif self.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel()
            elif self.execution_mode == ExecutionMode.DAG:
                await self._execute_dag()
            else:
                await self._execute_sequential()  # 預設策略
                
        except Exception as e:
            self.logger.error(f"工具鏈執行錯誤: {e}")
        
        # 統計結果
        execution_time = time.time() - start_time
        total_nodes = len(self.nodes)
        successful_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.COMPLETED])
        failed_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.FAILED])
        skipped_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.SKIPPED])
        
        # 收集錯誤詳情
        error_details = []
        for node in self.nodes.values():
            if node.status == NodeStatus.FAILED and node.result and node.result.error:
                error_details.append({
                    'node_id': node.node_id,
                    'node_name': node.name,
                    'error': str(node.result.error),
                    'execution_time': node.execution_time
                })
        
        # 保存結果到上下文
        for node_id, node in self.nodes.items():
            if node.result:
                self.context.results[node_id] = node.result
        
        result = ExecutionResult(
            success=failed_nodes == 0,
            results=dict(self.context.results),
            execution_time=execution_time,
            total_nodes=total_nodes,
            successful_nodes=successful_nodes,
            failed_nodes=failed_nodes,
            skipped_nodes=skipped_nodes,
            error_details=error_details
        )
        
        self.logger.info(
            f"工具鏈執行完成: {self.name}, "
            f"成功: {successful_nodes}/{total_nodes}, "
            f"時間: {execution_time:.3f}s"
        )
        
        return result
    
    async def _execute_sequential(self):
        """順序執行"""
        # 建立執行順序（拓撲排序）
        execution_order = self._topological_sort()
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            if not node.can_execute(self.context):
                node.status = NodeStatus.SKIPPED
                continue
            
            self.logger.debug(f"執行節點: {node_id}")
            result = await node.execute(self.context)
            self.context.results[node_id] = result
            
            # 處理條件分支
            if isinstance(node, ConditionalNode):
                await self._handle_conditional_branch(node)
    
    async def _execute_parallel(self):
        """並行執行"""
        remaining_nodes = set(self.nodes.keys())
        
        while remaining_nodes:
            # 找到可以執行的節點
            ready_nodes = [
                node_id for node_id in remaining_nodes
                if self.nodes[node_id].can_execute(self.context)
            ]
            
            if not ready_nodes:
                # 沒有可執行的節點，可能有循環依賴
                self.logger.warning("檢測到循環依賴或無法執行的節點")
                break
            
            # 限制並行數量
            batch_nodes = ready_nodes[:self.max_parallel]
            
            # 並行執行
            tasks = []
            for node_id in batch_nodes:
                node = self.nodes[node_id]
                tasks.append(self._execute_node_with_context(node_id, node))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            for node_id, result in zip(batch_nodes, results):
                if isinstance(result, Exception):
                    self.logger.error(f"節點 {node_id} 執行錯誤: {result}")
                    self.nodes[node_id].status = NodeStatus.FAILED
                else:
                    self.context.results[node_id] = result
                
                remaining_nodes.remove(node_id)
    
    async def _execute_dag(self):
        """DAG 執行（支援複雜依賴關係）"""
        await self._execute_parallel()  # DAG 本質上是智能並行執行
    
    async def _execute_node_with_context(self, node_id: str, node: ChainNode) -> ToolResult:
        """在上下文中執行節點"""
        result = await node.execute(self.context)
        
        # 處理條件分支
        if isinstance(node, ConditionalNode):
            await self._handle_conditional_branch(node)
        
        return result
    
    async def _handle_conditional_branch(self, condition_node: ConditionalNode):
        """處理條件分支"""
        branch_info = self.context.get(f"{condition_node.node_id}_branch")
        if not branch_info:
            return
        
        # 標記跳過的分支節點
        skipped_nodes = branch_info.get('skipped_branch', [])
        for node_id in skipped_nodes:
            if node_id in self.nodes:
                self.nodes[node_id].status = NodeStatus.SKIPPED
    
    def _topological_sort(self) -> List[str]:
        """拓撲排序"""
        # 簡單的拓撲排序實現
        visited = set()
        temp_visited = set()
        result = []
        
        def dfs(node_id: str):
            if node_id in temp_visited:
                raise ValueError(f"檢測到循環依賴: {node_id}")
            if node_id in visited:
                return
            
            temp_visited.add(node_id)
            
            # 訪問依賴節點
            node = self.nodes[node_id]
            for dep in node.dependencies:
                if dep in self.nodes:
                    dfs(dep)
            
            temp_visited.remove(node_id)
            visited.add(node_id)
            result.append(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)
        
        return result
    
    def get_execution_graph(self) -> Dict[str, Any]:
        """獲取執行圖表示"""
        graph = {
            'nodes': [],
            'edges': []
        }
        
        for node_id, node in self.nodes.items():
            graph['nodes'].append({
                'id': node_id,
                'name': node.name,
                'type': type(node).__name__,
                'status': node.status.value,
                'execution_time': node.execution_time
            })
            
            for dep in node.dependencies:
                graph['edges'].append({
                    'from': dep,
                    'to': node_id
                })
        
        return graph


# 使用範例
if __name__ == "__main__":
    # 示例工具函數
    async def fetch_data(source: str) -> str:
        """模擬數據獲取"""
        await asyncio.sleep(0.1)
        return f"數據來自 {source}"
    
    async def process_data(data: str) -> str:
        """模擬數據處理"""
        await asyncio.sleep(0.2)
        return f"處理後的 {data}"
    
    async def save_result(result: str) -> str:
        """模擬結果保存"""
        await asyncio.sleep(0.1)
        return f"已保存: {result}"
    
    def check_quality(context: ChainContext) -> bool:
        """品質檢查條件"""
        data = context.get("processed_data")
        return data and "處理後" in data
    
    # 創建工具鏈
    chain = ToolChain("數據處理鏈", execution_mode=ExecutionMode.SEQUENTIAL)
    
    # 添加節點
    chain.add_tool(
        "fetch", 
        fetch_data, 
        input_mapping={"source": "data_source"},
        output_mapping="raw_data"
    ).add_tool(
        "process",
        process_data,
        input_mapping={"data": "raw_data"},
        output_mapping="processed_data",
        dependencies=["fetch"]
    ).add_condition(
        "quality_check",
        condition=check_quality,
        true_branch=["save"],
        false_branch=["retry_process"],
        dependencies=["process"]
    ).add_tool(
        "save",
        save_result,
        input_mapping={"result": "processed_data"},
        output_mapping="final_result",
        dependencies=["quality_check"]
    )
    
    # 執行鏈
    async def main():
        result = await chain.set_variable("data_source", "API").execute()
        print(f"執行結果: {result.success}")
        print(f"執行時間: {result.execution_time:.3f}秒")
        print(f"成功節點: {result.successful_nodes}/{result.total_nodes}")
        
        if result.results.get("final_result"):
            print(f"最終結果: {result.results['final_result'].result}")
    
    asyncio.run(main()) 