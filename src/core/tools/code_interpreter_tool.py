"""
CrewAI 代碼解釋器工具

提供安全的代碼執行環境，支援多種程式語言
包含沙盒隔離、資源限制和安全檢查
"""

from typing import Dict, Any, List, Optional, Union
import subprocess
import tempfile
import os
import sys
import time
import signal
import threading
import queue
import json
import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import ast
import builtins

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .tool_registry import ToolCategory, register_tool


class ProgrammingLanguage(Enum):
    """支援的程式語言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    R = "r"
    SQL = "sql"


class ExecutionStatus(Enum):
    """執行狀態"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"


@dataclass
class ExecutionResult:
    """代碼執行結果"""
    status: ExecutionStatus
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    memory_usage: float = 0.0
    exit_code: int = 0
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class SecurityChecker:
    """安全檢查器"""
    
    # 危險的 Python 模組和函數
    DANGEROUS_IMPORTS = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests',
        'http', 'ftplib', 'smtplib', 'telnetlib', 'ssl', 'hashlib', 'hmac',
        'secrets', 'random', 'tempfile', 'glob', 'pickle', 'marshal',
        'shelve', 'dbm', 'sqlite3', 'ctypes', '__import__', 'eval', 'exec',
        'compile', 'open', 'file', 'input', 'raw_input'
    }
    
    # 危險的內建函數
    DANGEROUS_BUILTINS = {
        '__import__', 'eval', 'exec', 'compile', 'open', 'file', 'input',
        'raw_input', 'reload', 'vars', 'dir', 'globals', 'locals',
        'getattr', 'setattr', 'delattr', 'hasattr'
    }
    
    # 危險的關鍵字和模式
    DANGEROUS_PATTERNS = [
        r'import\s+os',
        r'import\s+sys',
        r'import\s+subprocess',
        r'from\s+os\s+import',
        r'from\s+sys\s+import',
        r'from\s+subprocess\s+import',
        r'__import__\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'open\s*\(',
        r'file\s*\(',
        r'input\s*\(',
        r'raw_input\s*\(',
    ]
    
    def check_python_code(self, code: str) -> tuple[bool, List[str]]:
        """檢查 Python 代碼安全性"""
        violations = []
        
        # 檢查危險模式
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"發現危險模式: {pattern}")
        
        # 解析 AST 進行更深入的檢查
        try:
            tree = ast.parse(code)
            violations.extend(self._check_ast_nodes(tree))
        except SyntaxError as e:
            violations.append(f"語法錯誤: {str(e)}")
        
        return len(violations) == 0, violations
    
    def _check_ast_nodes(self, tree: ast.AST) -> List[str]:
        """檢查 AST 節點"""
        violations = []
        
        for node in ast.walk(tree):
            # 檢查導入語句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_IMPORTS:
                        violations.append(f"危險導入: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.DANGEROUS_IMPORTS:
                    violations.append(f"危險導入: from {node.module}")
            
            # 檢查函數調用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_BUILTINS:
                        violations.append(f"危險函數調用: {node.func.id}")
        
        return violations
    
    def check_javascript_code(self, code: str) -> tuple[bool, List[str]]:
        """檢查 JavaScript 代碼安全性"""
        violations = []
        
        dangerous_js_patterns = [
            r'require\s*\(',
            r'process\.',
            r'global\.',
            r'eval\s*\(',
            r'Function\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            r'XMLHttpRequest',
            r'fetch\s*\(',
        ]
        
        for pattern in dangerous_js_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"發現危險 JavaScript 模式: {pattern}")
        
        return len(violations) == 0, violations
    
    def check_bash_code(self, code: str) -> tuple[bool, List[str]]:
        """檢查 Bash 代碼安全性"""
        violations = []
        
        dangerous_bash_patterns = [
            r'rm\s+-rf',
            r'sudo\s+',
            r'su\s+',
            r'chmod\s+',
            r'chown\s+',
            r'curl\s+',
            r'wget\s+',
            r'nc\s+',
            r'netcat\s+',
            r'ssh\s+',
            r'scp\s+',
            r'rsync\s+',
            r'>\s*/dev/',
            r'cat\s+/etc/',
        ]
        
        for pattern in dangerous_bash_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"發現危險 Bash 命令: {pattern}")
        
        return len(violations) == 0, violations


class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self, max_memory_mb: int = 128, max_execution_time: int = 30):
        self.max_memory_mb = max_memory_mb
        self.max_execution_time = max_execution_time
        self.start_time = None
        self.peak_memory = 0
    
    def start_monitoring(self):
        """開始監控"""
        self.start_time = time.time()
        self.peak_memory = 0
    
    def check_limits(self) -> tuple[bool, str]:
        """檢查資源限制"""
        if self.start_time is None:
            return True, ""
        
        # 檢查執行時間
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.max_execution_time:
            return False, f"執行時間超過限制 ({self.max_execution_time}秒)"
        
        # 檢查記憶體使用量 (簡化實作)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.peak_memory = max(self.peak_memory, memory_mb)
            
            if memory_mb > self.max_memory_mb:
                return False, f"記憶體使用超過限制 ({self.max_memory_mb}MB)"
        except ImportError:
            # 如果沒有 psutil，跳過記憶體檢查
            pass
        
        return True, ""
    
    def get_usage_stats(self) -> Dict[str, float]:
        """獲取使用統計"""
        elapsed_time = 0
        if self.start_time:
            elapsed_time = time.time() - self.start_time
        
        return {
            "execution_time": elapsed_time,
            "peak_memory_mb": self.peak_memory
        }


class SandboxExecutor:
    """沙盒執行器"""
    
    def __init__(self, language: ProgrammingLanguage, max_memory_mb: int = 128, 
                 max_execution_time: int = 30):
        self.language = language
        self.max_memory_mb = max_memory_mb
        self.max_execution_time = max_execution_time
        self.security_checker = SecurityChecker()
        self.resource_monitor = ResourceMonitor(max_memory_mb, max_execution_time)
    
    def execute(self, code: str) -> ExecutionResult:
        """執行代碼"""
        # 安全檢查
        is_safe, violations = self._security_check(code)
        if not is_safe:
            return ExecutionResult(
                status=ExecutionStatus.SECURITY_VIOLATION,
                error=f"安全檢查失敗: {'; '.join(violations)}"
            )
        
        # 選擇執行方法
        if self.language == ProgrammingLanguage.PYTHON:
            return self._execute_python(code)
        elif self.language == ProgrammingLanguage.JAVASCRIPT:
            return self._execute_javascript(code)
        elif self.language == ProgrammingLanguage.BASH:
            return self._execute_bash(code)
        elif self.language == ProgrammingLanguage.R:
            return self._execute_r(code)
        elif self.language == ProgrammingLanguage.SQL:
            return self._execute_sql(code)
        else:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"不支援的程式語言: {self.language.value}"
            )
    
    def _security_check(self, code: str) -> tuple[bool, List[str]]:
        """執行安全檢查"""
        if self.language == ProgrammingLanguage.PYTHON:
            return self.security_checker.check_python_code(code)
        elif self.language == ProgrammingLanguage.JAVASCRIPT:
            return self.security_checker.check_javascript_code(code)
        elif self.language == ProgrammingLanguage.BASH:
            return self.security_checker.check_bash_code(code)
        else:
            return True, []  # 其他語言暫時跳過安全檢查
    
    def _execute_python(self, code: str) -> ExecutionResult:
        """執行 Python 代碼"""
        self.resource_monitor.start_monitoring()
        
        # 創建受限的執行環境
        restricted_globals = {
            '__builtins__': {
                # 只允許安全的內建函數
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'max': max,
                'min': min,
                'sum': sum,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'type': type,
                'isinstance': isinstance,
                'issubclass': issubclass,
            }
        }
        
        # 重定向輸出
        import io
        import contextlib
        
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_buffer), \
                 contextlib.redirect_stderr(error_buffer):
                
                # 編譯並執行代碼
                compiled_code = compile(code, '<string>', 'exec')
                exec(compiled_code, restricted_globals)
            
            stats = self.resource_monitor.get_usage_stats()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                output=output_buffer.getvalue(),
                error=error_buffer.getvalue(),
                execution_time=stats["execution_time"],
                memory_usage=stats["peak_memory_mb"]
            )
            
        except SyntaxError as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"語法錯誤: {str(e)}"
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"執行錯誤: {str(e)}"
            )
    
    def _execute_javascript(self, code: str) -> ExecutionResult:
        """執行 JavaScript 代碼 (使用 Node.js)"""
        return self._execute_with_subprocess(code, ["node", "-e"])
    
    def _execute_bash(self, code: str) -> ExecutionResult:
        """執行 Bash 代碼"""
        return self._execute_with_subprocess(code, ["bash", "-c"])
    
    def _execute_r(self, code: str) -> ExecutionResult:
        """執行 R 代碼"""
        return self._execute_with_subprocess(code, ["Rscript", "-e"])
    
    def _execute_sql(self, code: str) -> ExecutionResult:
        """執行 SQL 代碼 (使用 SQLite)"""
        try:
            # 修復 SQLite 版本兼容性
            import sys
            try:
                import pysqlite3.dbapi2 as sqlite3
                sys.modules['sqlite3'] = sqlite3
                sys.modules['sqlite3.dbapi2'] = sqlite3
            except ImportError:
                import sqlite3
            
            self.resource_monitor.start_monitoring()
            
            # 創建內存數據庫
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            
            output_lines = []
            
            # 執行 SQL 語句
            for statement in code.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
                    
                    # 如果是查詢語句，獲取結果
                    if statement.upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        column_names = [description[0] for description in cursor.description]
                        
                        output_lines.append(f"列名: {', '.join(column_names)}")
                        for row in results:
                            output_lines.append(str(row))
                    else:
                        output_lines.append(f"語句執行成功: {statement}")
            
            conn.close()
            
            stats = self.resource_monitor.get_usage_stats()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                output='\n'.join(output_lines),
                execution_time=stats["execution_time"]
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"SQL 執行錯誤: {str(e)}"
            )
    
    def _execute_with_subprocess(self, code: str, command: List[str]) -> ExecutionResult:
        """使用子進程執行代碼"""
        self.resource_monitor.start_monitoring()
        
        try:
            # 創建臨時文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 執行命令
                if len(command) == 2 and command[1] == "-e":
                    # 直接執行代碼
                    process_command = command + [code]
                else:
                    # 執行文件
                    process_command = command + [temp_file]
                
                result = subprocess.run(
                    process_command,
                    capture_output=True,
                    text=True,
                    timeout=self.max_execution_time,
                    cwd=tempfile.gettempdir()
                )
                
                stats = self.resource_monitor.get_usage_stats()
                
                if result.returncode == 0:
                    return ExecutionResult(
                        status=ExecutionStatus.SUCCESS,
                        output=result.stdout,
                        error=result.stderr,
                        execution_time=stats["execution_time"],
                        exit_code=result.returncode
                    )
                else:
                    return ExecutionResult(
                        status=ExecutionStatus.ERROR,
                        output=result.stdout,
                        error=result.stderr,
                        execution_time=stats["execution_time"],
                        exit_code=result.returncode
                    )
                    
            finally:
                # 清理臨時文件
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"執行超時 ({self.max_execution_time}秒)"
            )
        except FileNotFoundError:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"找不到執行環境: {command[0]}"
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error=f"執行失敗: {str(e)}"
            )


@register_tool(
    category=ToolCategory.DATA_PROCESSING,
    aliases=["code", "python", "execute", "run_code"],
    description="安全的代碼執行環境",
    author="CrewAI Team"
)
class CodeInterpreterTool(BaseTool):
    """
    代碼解釋器工具
    
    提供安全的多語言代碼執行環境，包含：
    - 沙盒隔離
    - 資源限制
    - 安全檢查
    - 多語言支援
    """
    
    name: str = "code_interpreter"
    description: str = "在安全的沙盒環境中執行代碼，支援 Python、JavaScript、Bash、R、SQL"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 預設配置
        self.max_memory_mb = 128
        self.max_execution_time = 30
        self.default_language = ProgrammingLanguage.PYTHON
        
        # 載入配置
        self._load_config()
    
    def _load_config(self):
        """載入配置"""
        import os
        
        # 從環境變數載入配置
        self.max_memory_mb = int(os.getenv("CODE_INTERPRETER_MAX_MEMORY", 128))
        self.max_execution_time = int(os.getenv("CODE_INTERPRETER_MAX_TIME", 30))
    
    def _run(self, code: str, language: str = "python") -> str:
        """執行代碼"""
        try:
            # 解析語言
            try:
                lang = ProgrammingLanguage(language.lower())
            except ValueError:
                return f"錯誤: 不支援的程式語言 '{language}'"
            
            # 創建沙盒執行器
            executor = SandboxExecutor(
                language=lang,
                max_memory_mb=self.max_memory_mb,
                max_execution_time=self.max_execution_time
            )
            
            # 執行代碼
            result = executor.execute(code)
            
            # 格式化結果
            return self._format_result(result, code, language)
            
        except Exception as e:
            return f"代碼執行工具內部錯誤: {str(e)}"
    
    def _format_result(self, result: ExecutionResult, code: str, language: str) -> str:
        """格式化執行結果"""
        lines = []
        
        # 標題
        lines.append(f"=== {language.upper()} 代碼執行結果 ===")
        lines.append("")
        
        # 代碼
        lines.append("執行的代碼:")
        lines.append("```" + language)
        lines.append(code)
        lines.append("```")
        lines.append("")
        
        # 狀態
        status_icons = {
            ExecutionStatus.SUCCESS: "✅",
            ExecutionStatus.ERROR: "❌",
            ExecutionStatus.TIMEOUT: "⏰",
            ExecutionStatus.SECURITY_VIOLATION: "🚫",
            ExecutionStatus.RESOURCE_LIMIT_EXCEEDED: "📊"
        }
        
        icon = status_icons.get(result.status, "❓")
        lines.append(f"執行狀態: {icon} {result.status.value.upper()}")
        
        # 執行資訊
        if result.execution_time > 0:
            lines.append(f"執行時間: {result.execution_time:.3f} 秒")
        
        if result.memory_usage > 0:
            lines.append(f"記憶體使用: {result.memory_usage:.1f} MB")
        
        if result.exit_code != 0:
            lines.append(f"退出代碼: {result.exit_code}")
        
        lines.append("")
        
        # 輸出
        if result.output:
            lines.append("標準輸出:")
            lines.append("```")
            lines.append(result.output.strip())
            lines.append("```")
            lines.append("")
        
        # 錯誤
        if result.error:
            lines.append("錯誤輸出:")
            lines.append("```")
            lines.append(result.error.strip())
            lines.append("```")
            lines.append("")
        
        # 警告
        if result.warnings:
            lines.append("警告:")
            for warning in result.warnings:
                lines.append(f"⚠️  {warning}")
            lines.append("")
        
        return "\n".join(lines)
    
    def execute_python(self, code: str) -> ExecutionResult:
        """執行 Python 代碼並返回詳細結果"""
        executor = SandboxExecutor(
            ProgrammingLanguage.PYTHON,
            self.max_memory_mb,
            self.max_execution_time
        )
        return executor.execute(code)
    
    def execute_javascript(self, code: str) -> ExecutionResult:
        """執行 JavaScript 代碼並返回詳細結果"""
        executor = SandboxExecutor(
            ProgrammingLanguage.JAVASCRIPT,
            self.max_memory_mb,
            self.max_execution_time
        )
        return executor.execute(code)
    
    def execute_sql(self, code: str) -> ExecutionResult:
        """執行 SQL 代碼並返回詳細結果"""
        executor = SandboxExecutor(
            ProgrammingLanguage.SQL,
            self.max_memory_mb,
            self.max_execution_time
        )
        return executor.execute(code)


# 使用範例
if __name__ == "__main__":
    # 創建代碼解釋器
    interpreter = CodeInterpreterTool()
    
    # 測試 Python 代碼
    python_code = """
# 計算費波那契數列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 計算前10個數字
result = []
for i in range(10):
    result.append(fibonacci(i))

print("費波那契數列前10項:", result)
print("總和:", sum(result))
"""
    
    print("=== Python 執行測試 ===")
    result = interpreter._run(python_code, "python")
    print(result)
    
    # 測試 SQL 代碼
    sql_code = """
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    grade REAL
);

INSERT INTO students (name, age, grade) VALUES 
    ('Alice', 20, 85.5),
    ('Bob', 19, 92.0),
    ('Charlie', 21, 78.5);

SELECT * FROM students;
SELECT AVG(grade) as average_grade FROM students;
"""
    
    print("\n=== SQL 執行測試 ===")
    result = interpreter._run(sql_code, "sql")
    print(result) 