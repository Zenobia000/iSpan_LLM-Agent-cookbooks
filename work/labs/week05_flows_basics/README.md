# Week 05: Flows 事件驅動 (基礎)

## 學習目標

- 理解事件驅動架構的基本概念。
- 學習如何使用 `@flow` decorator 來定義一個簡單的事件驅動流程。
- 實作一個基本的天氣預警流程，當特定條件滿足時觸發。

## 實作步驟

1. **建立 `solution.py`:** 在 `work/labs/week05_flows_basics/` 資料夾中建立 `solution.py` 檔案。
2. **導入 `@flow`:** 從 `src.core.flows` 導入 `flow` decorator。
3. **定義天氣檢查函式:** 建立一個函式，例如 `check_weather_conditions`，用來模擬檢查天氣狀況。
4. **使用 `@flow`:** 在 `check_weather_conditions` 函式上加上 `@flow` decorator。
5. **觸發流程:** 在主程式區塊中，呼叫 `check_weather_conditions` 函式來觸發流程。
