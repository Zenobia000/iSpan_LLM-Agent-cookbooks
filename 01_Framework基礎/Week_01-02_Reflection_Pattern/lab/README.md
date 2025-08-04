# 實驗：第 1-2 週：反思模式

## 目標

本實驗旨在讓您親手體驗 **反思模式 (Reflection Pattern)**。您將建構並修改一個使用自我批判循環來改善其輸出的 CrewAI 系統。

## 指引

1.  導航至 `examples/self_critique_loop` 目錄。
2.  檢閱 `README.md` 和 `main.py` 檔案，以理解其基礎實現。
3.  遵循 `lab_1.md` 中的指引完成練習。

## 需重點關注的概念

-   `context` 如何在任務之間傳遞。
-   `Weather Reporter` 和 `Summary Reviewer` 代理之間「思考」過程的差異（請觀察 `verbose=2` 的輸出）。
-   最終輸出是如何綜合「生成」與「批判」的結果。
