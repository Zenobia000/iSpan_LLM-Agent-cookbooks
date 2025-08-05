# 📋 Task 核心模組 Fundamentals

> **基於任務分解和執行控制的 CrewAI Task 設計指南**

## 📋 概述

Task 是 CrewAI 系統中最小的可執行工作單元，承載著將複雜目標分解為具體行動的關鍵職責。

### 知識框架對照

| 框架維度 | Task 設計應用 | 核心優勢 | 適用性限制 |
|---------|-------------|----------|-----------|
| **First Principles** | 任務的原子性：每個 Task 應該是不可再分的最小工作單元 | 確保任務邊界清晰，易於管理 | 可能過度分解，增加協調成本 |
| **Fundamentals** | 描述、輸出、執行者、依賴四要素 | 結構標準化，易於實作 | 靜態定義難以適應動態需求 |
| **Body of Knowledge** | 對照項目管理的 WBS、敏捷開發的 User Story | 理論基礎成熟，實踐經驗豐富 | 軟體任務與 AI 任務特性存在差異 |

---

## 🎯 First Principles: 任務的本質特性

### 1. 原子性 (Atomicity)
**定理**: 任務應該是不可再分的最小工作單元

```python
# ✅ 良好的原子性設計
good_task = Task(
    description="分析競爭對手 A 公司的產品定價策略",
    expected_output="包含價格分析、策略評估的結構化報告"
)

# ❌ 違反原子性的設計
bad_task = Task(
    description="研究市場、分析競爭對手、制定策略、撰寫報告",
    expected_output="完整的市場研究報告"  # 太複雜，應該拆分
)
```

### 2. 冪等性 (Idempotency)
**定理**: 相同輸入的任務應該產生相同結果

```python
class IdempotentTask(BaseTask):
    def execute_with_idempotency(self, inputs: Dict[str, Any]) -> Any:
        # 生成輸入指紋
        input_hash = self._generate_input_hash(inputs)
        
        # 檢查是否已有結果
        cached_result = self.result_cache.get(input_hash)
        if cached_result:
            return cached_result
        
        # 執行任務並快取結果
        result = self.execute(inputs)
        self.result_cache.set(input_hash, result)
        return result
```

### 3. 可觀測性 (Observability)
**定理**: 任務執行過程和結果應該是可監控和可追蹤的

```python
class ObservableTask(BaseTask):
    def execute_with_observability(self, inputs: Dict[str, Any]) -> Any:
        # 記錄開始
        self.emit_event("task_started", {"inputs": inputs})
        
        try:
            result = self.execute(inputs)
            # 記錄成功
            self.emit_event("task_completed", {"result": result})
            return result
        except Exception as e:
            # 記錄失敗
            self.emit_event("task_failed", {"error": str(e)})
            raise
```

---

## 🏗️ Fundamentals: 任務的四大要素

### 1. 任務描述 (Description)

**SMART 原則應用**:
```python
class TaskDescriptionValidator:
    def validate_smart_description(self, description: str) -> Dict[str, bool]:
        return {
            "specific": self._has_clear_action_verb(description),
            "measurable": self._has_quantifiable_output(description),
            "achievable": self._within_agent_capability(description),
            "relevant": self._aligns_with_goals(description),
            "timebound": self._has_time_constraint(description)
        }
```

**最佳實踐**:
- ✅ "分析過去6個月的銷售數據，計算每月增長率"
- ❌ "看看銷售情況"

### 2. 期望輸出 (Expected Output)

**輸出規格化**:
```python
class OutputSpecification:
    def __init__(self):
        self.format: str = "structured_json"
        self.schema: Dict[str, Any] = {}
        self.quality_criteria: List[str] = []
        self.validation_rules: List[Callable] = []
    
    def validate_output(self, output: Any) -> ValidationResult:
        """驗證輸出是否符合規格"""
        for rule in self.validation_rules:
            if not rule(output):
                return ValidationResult(valid=False, message="輸出不符合規格")
        return ValidationResult(valid=True)
```

### 3. 依賴管理 (Dependency Management)

**依賴類型**:
```python
class DependencyType(Enum):
    DATA_DEPENDENCY = "data"        # 需要前置任務的數據
    RESOURCE_DEPENDENCY = "resource" # 需要共享資源
    SEQUENTIAL_DEPENDENCY = "sequence" # 必須按順序執行
    CONDITIONAL_DEPENDENCY = "condition" # 條件性依賴
```

**依賴解析**:
```python
class DependencyResolver:
    def resolve_execution_order(self, tasks: List[BaseTask]) -> List[str]:
        """使用拓撲排序解析執行順序"""
        graph = self._build_dependency_graph(tasks)
        return self._topological_sort(graph)
    
    def check_circular_dependency(self, tasks: List[BaseTask]) -> bool:
        """檢查是否存在循環依賴"""
        graph = self._build_dependency_graph(tasks)
        return self._has_cycle(graph)
```

### 4. 執行控制 (Execution Control)

**超時機制**:
```python
class TimeoutControl:
    def execute_with_timeout(self, task: BaseTask, timeout_seconds: int) -> Any:
        def timeout_handler(signum, frame):
            raise TimeoutError(f"任務執行超時 ({timeout_seconds}秒)")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            result = task.execute()
            signal.alarm(0)  # 取消超時
            return result
        except TimeoutError:
            task.cancel()
            raise
```

**重試策略**:
```python
class RetryStrategy:
    def execute_with_retry(self, task: BaseTask, max_retries: int = 3) -> Any:
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return task.execute()
            except RetryableError as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # 指數退避
                    time.sleep(wait_time)
                    continue
            except NonRetryableError:
                break
        
        raise last_error
```

---

## 📚 Body of Knowledge: 項目管理理論對照

### 1. WBS (Work Breakdown Structure) 對照

```python
class WorkBreakdownStructure:
    def decompose_complex_goal(self, goal: str) -> List[BaseTask]:
        """將複雜目標分解為任務階層"""
        # 1. 識別主要可交付成果
        deliverables = self._identify_deliverables(goal)
        
        # 2. 分解為工作包
        work_packages = []
        for deliverable in deliverables:
            packages = self._decompose_deliverable(deliverable)
            work_packages.extend(packages)
        
        # 3. 創建具體任務
        tasks = []
        for package in work_packages:
            task_list = self._create_tasks_from_package(package)
            tasks.extend(task_list)
        
        return tasks
```

### 2. 敏捷開發 User Story 對照

```python
class UserStoryTask(BaseTask):
    def __init__(self, story: str, acceptance_criteria: List[str]):
        # 解析 User Story 格式："As a [role], I want [goal] so that [benefit]"
        parsed = self._parse_user_story(story)
        
        super().__init__(TaskConfig(
            description=f"為 {parsed.role} 實現 {parsed.goal}",
            expected_output=f"滿足以下條件的功能：{acceptance_criteria}",
            validation_required=True
        ))
        
        self.acceptance_criteria = acceptance_criteria
    
    def validate_output(self, output: Any) -> bool:
        """基於驗收條件驗證輸出"""
        for criterion in self.acceptance_criteria:
            if not self._check_criterion(output, criterion):
                return False
        return True
```

---

## ⚠️ 潛在盲區與適用性分析

### 1. 任務粒度盲區

```python
# ❌ 過度細分的任務
micro_tasks = [
    "打開文件",
    "讀取第一行", 
    "解析數據",
    "寫入結果"
]

# ✅ 適當粒度的任務
balanced_task = Task(
    description="處理CSV文件並提取銷售數據摘要",
    expected_output="包含總銷售額、平均值、趨勢分析的JSON報告"
)
```

### 2. 適用性矩陣

| 任務類型 | 標準化程度 | 創新要求 | 推薦模式 | 注意事項 |
|---------|-----------|----------|----------|----------|
| **數據處理** | 🟢 高 | 🔴 低 | 嚴格規格化 | 重視準確性和效率 |
| **內容創作** | 🟡 中 | 🟢 高 | 靈活描述 | 平衡創意和質量 |
| **分析研究** | 🟡 中 | 🟡 中 | 結構化方法 | 確保邏輯完整性 |
| **決策支持** | 🔴 低 | 🟢 高 | 開放式探索 | 提供多種視角 |

### 3. 性能考量

```python
class TaskPerformanceOptimizer:
    def optimize_task_execution(self, tasks: List[BaseTask]) -> ExecutionPlan:
        # 並行化分析
        parallel_groups = self._identify_parallel_tasks(tasks)
        
        # 資源分配
        resource_allocation = self._allocate_resources(tasks)
        
        # 關鍵路徑分析
        critical_path = self._find_critical_path(tasks)
        
        return ExecutionPlan(
            parallel_groups=parallel_groups,
            resource_allocation=resource_allocation,
            critical_path=critical_path
        )
```

---

## 🛠️ 實務整合指南

### 1. 任務設計檢查清單

#### 設計階段
- [ ] 任務描述是否符合 SMART 原則？
- [ ] 期望輸出是否明確具體？
- [ ] 是否正確識別了所有依賴關係？
- [ ] 任務粒度是否適當？

#### 實作階段
- [ ] 是否實作了適當的錯誤處理？
- [ ] 是否設置了合理的超時時間？
- [ ] 是否實作了必要的驗證邏輯？
- [ ] 是否考慮了並發執行的安全性？

### 2. 故障排除指南

```python
class TaskDiagnostics:
    def diagnose_task_failure(self, task: BaseTask) -> DiagnosisReport:
        """任務失敗診斷"""
        return DiagnosisReport(
            dependency_check=self._check_dependencies(task),
            resource_availability=self._check_resources(task),
            input_validation=self._validate_inputs(task),
            agent_capability=self._assess_agent_match(task),
            performance_metrics=self._analyze_performance(task)
        )
```

---

## 📖 延伸學習資源

### 項目管理理論
1. **《項目管理知識體系指南》** - PMI (2021)
2. **《敏捷軟體開發》** - Robert C. Martin (2002)

### 任務分解方法
1. **《系統分析與設計》** - Alan Dennis (2019)
2. **《軟體工程》** - Ian Sommerville (2020)

---

*本文檔基於項目管理最佳實踐，最後更新：2025年1月* 