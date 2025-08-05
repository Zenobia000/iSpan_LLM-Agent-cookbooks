# CrewAI 執行日誌目錄

此目錄用於存儲 CrewAI hierarchical planning 的執行記錄，包含：

## 日誌文件類型

### 1. 主要執行日誌 (`crewai_execution_YYYYMMDD_HHMMSS.txt`)
- 包含完整的 console 輸出
- 格式化的執行過程記錄
- Agent 互動和決策過程
- 工具使用情況

### 2. 詳細技術日誌 (`crewai_detailed_YYYYMMDD_HHMMSS.log`)
- Python logging 模組產生的結構化日誌
- 包含時間戳、日誌級別、模組名稱
- 用於技術除錯和系統分析

### 3. 執行結果文件 (`result_YYYYMMDD_HHMMSS.txt`)
- 純文字格式的最終輸出結果
- 便於後續分析和處理

### 4. 統計分析文件 (`stats_YYYYMMDD_HHMMSS.txt`)
- 執行統計數據
- Agent、Task、Tool 使用頻率
- 錯誤和警告計數

## 文件命名規則

所有文件使用時間戳命名：`YYYYMMDD_HHMMSS`
- YYYY: 年份
- MM: 月份
- DD: 日期  
- HH: 小時
- MM: 分鐘
- SS: 秒數

## 使用方式

執行 `solution.py` 後會自動生成所有相關日誌文件，用於：
- 研究 AI 代理的思維過程
- 分析決策流程和工作模式
- 除錯和優化 CrewAI 配置
- 學習多代理協作模式

## 注意事項

- 日誌文件可能包含大量文字，建議使用文本編輯器的搜尋功能
- 定期清理舊的日誌文件以節省磁碟空間
- 分析日誌時注意 Agent 之間的互動模式和工具使用順序