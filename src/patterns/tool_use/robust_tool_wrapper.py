#!/usr/bin/env python3
"""
Tool Use Pattern: Robust Tool Wrapper
容錯工具包裝器 - 提供智能重試、錯誤處理和備用策略

作者: CrewAI × Agentic Design Patterns
版本: 1.0.0
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union, Type
from dataclasses import dataclass
from enum import Enum
import traceback
import inspect


class RetryStrategy(Enum):
    """重試策略"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI = "fibonacci"


class FailureAction(Enum):
    """失敗處理動作"""
    RAISE_EXCEPTION = "raise_exception"
    RETURN_DEFAULT = "return_default"
    USE_FALLBACK = "use_fallback"
    LOG_AND_CONTINUE = "log_and_continue"


@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    timeout: Optional[float] = None
    retry_on_exceptions: tuple = (Exception,)
    stop_on_exceptions: tuple = (KeyboardInterrupt, SystemExit)


@dataclass
class ToolResult:
    """工具執行結果"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    attempts: int = 1
    tool_name: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RobustToolWrapper:
    """
    容錯工具包裝器
    
    提供工具調用的智能重試、錯誤處理、超時控制和備用策略。
    支援同步和異步工具的統一包裝。
    """

    def __init__(
        self,
        tool_func: Callable,
        retry_config: Optional[RetryConfig] = None,
        fallback_func: Optional[Callable] = None,
        default_result: Any = None,
        failure_action: FailureAction = FailureAction.RAISE_EXCEPTION,
        tool_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化容錯工具包裝器

        Args:
            tool_func: 要包裝的工具函數
            retry_config: 重試配置
            fallback_func: 備用函數
            default_result: 預設返回值
            failure_action: 失敗處理動作
            tool_name: 工具名稱
            logger: 日誌記錄器
        """
        self.tool_func = tool_func
        self.retry_config = retry_config or RetryConfig()
        self.fallback_func = fallback_func
        self.default_result = default_result
        self.failure_action = failure_action
        self.tool_name = tool_name or getattr(tool_func, '__name__', 'unknown_tool')
        self.logger = logger or logging.getLogger(__name__)
        
        # 檢測是否為異步函數
        self.is_async = inspect.iscoroutinefunction(tool_func)
        
        # 執行統計
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_retries': 0,
            'avg_execution_time': 0.0
        }

    def __call__(self, *args, **kwargs) -> ToolResult:
        """
        執行工具調用
        
        Returns:
            ToolResult: 包含執行結果的對象
        """
        if self.is_async:
            return asyncio.run(self._execute_async(*args, **kwargs))
        else:
            return self._execute_sync(*args, **kwargs)

    async def async_call(self, *args, **kwargs) -> ToolResult:
        """
        異步執行工具調用
        
        Returns:
            ToolResult: 包含執行結果的對象
        """
        if self.is_async:
            return await self._execute_async(*args, **kwargs)
        else:
            # 在線程池中執行同步函數
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                self._execute_sync, 
                *args, 
                **kwargs
            )

    def _execute_sync(self, *args, **kwargs) -> ToolResult:
        """同步執行工具"""
        self.stats['total_calls'] += 1
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 超時控制
                if self.retry_config.timeout:
                    result = self._execute_with_timeout(
                        self.tool_func, 
                        self.retry_config.timeout,
                        *args, 
                        **kwargs
                    )
                else:
                    result = self.tool_func(*args, **kwargs)
                
                # 成功執行
                execution_time = time.time() - start_time
                self.stats['successful_calls'] += 1
                self.stats['total_retries'] += attempt
                self._update_avg_time(execution_time)
                
                return ToolResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    attempts=attempt + 1,
                    tool_name=self.tool_name
                )
                
            except self.retry_config.stop_on_exceptions as e:
                # 不重試的異常
                self.logger.error(f"Stop exception in {self.tool_name}: {e}")
                last_exception = e
                break
                
            except self.retry_config.retry_on_exceptions as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {self.tool_name}: {e}"
                )
                
                # 如果不是最後一次嘗試，等待重試
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    break
        
        # 所有重試都失敗了
        execution_time = time.time() - start_time
        self.stats['failed_calls'] += 1
        self.stats['total_retries'] += self.retry_config.max_retries
        self._update_avg_time(execution_time)
        
        return self._handle_failure(last_exception, execution_time, self.retry_config.max_retries + 1)

    async def _execute_async(self, *args, **kwargs) -> ToolResult:
        """異步執行工具"""
        self.stats['total_calls'] += 1
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 超時控制
                if self.retry_config.timeout:
                    result = await asyncio.wait_for(
                        self.tool_func(*args, **kwargs),
                        timeout=self.retry_config.timeout
                    )
                else:
                    result = await self.tool_func(*args, **kwargs)
                
                # 成功執行
                execution_time = time.time() - start_time
                self.stats['successful_calls'] += 1
                self.stats['total_retries'] += attempt
                self._update_avg_time(execution_time)
                
                return ToolResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    attempts=attempt + 1,
                    tool_name=self.tool_name
                )
                
            except self.retry_config.stop_on_exceptions as e:
                self.logger.error(f"Stop exception in {self.tool_name}: {e}")
                last_exception = e
                break
                
            except self.retry_config.retry_on_exceptions as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed for {self.tool_name}: {e}"
                )
                
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    break
        
        # 所有重試都失敗了
        execution_time = time.time() - start_time
        self.stats['failed_calls'] += 1
        self.stats['total_retries'] += self.retry_config.max_retries
        self._update_avg_time(execution_time)
        
        return self._handle_failure(last_exception, execution_time, self.retry_config.max_retries + 1)

    def _calculate_delay(self, attempt: int) -> float:
        """計算重試延遲時間"""
        if self.retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.retry_config.base_delay * (2 ** attempt)
        elif self.retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.retry_config.base_delay * (attempt + 1)
        elif self.retry_config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.retry_config.base_delay
        elif self.retry_config.strategy == RetryStrategy.FIBONACCI:
            fib_sequence = [1, 1]
            for i in range(2, attempt + 3):
                fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
            delay = self.retry_config.base_delay * fib_sequence[attempt + 1]
        else:
            delay = self.retry_config.base_delay
        
        return min(delay, self.retry_config.max_delay)

    def _execute_with_timeout(self, func: Callable, timeout: float, *args, **kwargs):
        """同步函數超時執行"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Tool {self.tool_name} execution timed out after {timeout} seconds")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)
            return result
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    def _handle_failure(self, exception: Exception, execution_time: float, attempts: int) -> ToolResult:
        """處理執行失敗"""
        if self.failure_action == FailureAction.USE_FALLBACK and self.fallback_func:
            try:
                self.logger.info(f"Using fallback for {self.tool_name}")
                if self.is_async:
                    fallback_result = asyncio.run(self.fallback_func())
                else:
                    fallback_result = self.fallback_func()
                
                return ToolResult(
                    success=True,
                    result=fallback_result,
                    execution_time=execution_time,
                    attempts=attempts,
                    tool_name=f"{self.tool_name}_fallback",
                    metadata={'used_fallback': True, 'original_error': str(exception)}
                )
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
                exception = fallback_error

        if self.failure_action == FailureAction.RETURN_DEFAULT:
            return ToolResult(
                success=False,
                result=self.default_result,
                error=exception,
                execution_time=execution_time,
                attempts=attempts,
                tool_name=self.tool_name,
                metadata={'used_default': True}
            )

        if self.failure_action == FailureAction.LOG_AND_CONTINUE:
            self.logger.error(f"Tool {self.tool_name} failed: {exception}")
            return ToolResult(
                success=False,
                result=None,
                error=exception,
                execution_time=execution_time,
                attempts=attempts,
                tool_name=self.tool_name
            )

        # FailureAction.RAISE_EXCEPTION
        return ToolResult(
            success=False,
            result=None,
            error=exception,
            execution_time=execution_time,
            attempts=attempts,
            tool_name=self.tool_name
        )

    def _update_avg_time(self, execution_time: float):
        """更新平均執行時間"""
        total_calls = self.stats['total_calls']
        current_avg = self.stats['avg_execution_time']
        self.stats['avg_execution_time'] = (
            (current_avg * (total_calls - 1) + execution_time) / total_calls
        )

    def get_stats(self) -> Dict[str, Any]:
        """獲取執行統計"""
        total_calls = self.stats['total_calls']
        if total_calls > 0:
            success_rate = self.stats['successful_calls'] / total_calls
            avg_retries = self.stats['total_retries'] / total_calls
        else:
            success_rate = 0.0
            avg_retries = 0.0
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'avg_retries_per_call': avg_retries,
            'tool_name': self.tool_name
        }

    def reset_stats(self):
        """重置統計"""
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_retries': 0,
            'avg_execution_time': 0.0
        }


def robust_tool(
    retry_config: Optional[RetryConfig] = None,
    fallback_func: Optional[Callable] = None,
    default_result: Any = None,
    failure_action: FailureAction = FailureAction.RAISE_EXCEPTION,
    tool_name: Optional[str] = None
):
    """
    裝飾器：將普通函數包裝為容錯工具
    
    Args:
        retry_config: 重試配置
        fallback_func: 備用函數
        default_result: 預設返回值
        failure_action: 失敗處理動作
        tool_name: 工具名稱
    
    Returns:
        包裝後的容錯工具函數
    """
    def decorator(func: Callable) -> RobustToolWrapper:
        return RobustToolWrapper(
            tool_func=func,
            retry_config=retry_config,
            fallback_func=fallback_func,
            default_result=default_result,
            failure_action=failure_action,
            tool_name=tool_name
        )
    
    return decorator


# 使用範例
if __name__ == "__main__":
    # 示例工具函數
    def unreliable_api_call(data: str) -> str:
        """模擬不穩定的 API 調用"""
        import random
        if random.random() < 0.7:  # 70% 失敗率
            raise ConnectionError("API 連接失敗")
        return f"處理結果: {data}"

    def fallback_local_processing(data: str) -> str:
        """備用本地處理"""
        return f"本地處理結果: {data}"

    # 使用裝飾器
    @robust_tool(
        retry_config=RetryConfig(max_retries=3, strategy=RetryStrategy.EXPONENTIAL_BACKOFF),
        fallback_func=lambda: fallback_local_processing("fallback_data"),
        failure_action=FailureAction.USE_FALLBACK,
        tool_name="unreliable_api"
    )
    def safe_api_call(data: str) -> str:
        return unreliable_api_call(data)

    # 測試
    print("測試容錯工具包裝器:")
    for i in range(3):
        result = safe_api_call(f"測試數據_{i}")
        print(f"結果 {i+1}: {result.result}, 成功: {result.success}, 嘗試次數: {result.attempts}")
    
    print(f"\n執行統計: {safe_api_call.get_stats()}") 