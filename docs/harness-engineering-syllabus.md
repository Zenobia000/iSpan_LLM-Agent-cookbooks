# Harness Engineering 教學大綱

> 進階模組：從「會跑的 Agent」到「生產級 Agent Harness」
> 衍生自 [Agent SDK 全景與 Harness Engineering 工程化分析](./agent-sdk-and-harness-engineering.md)

---

## 模組概述

**核心命題**：`Agent = Model + Harness`

學員在前 16 週已學會用 CrewAI 寫出能跑的 Agent。本模組的目標是補上**模型之外的工程**——讓 Agent 從 demo 變成可上生產的系統。

| 項目 | 說明 |
|---|---|
| **定位** | 進階模組，接續主課程 Week 12（測試）～ Week 14（部署） |
| **時數** | 7 單元，建議 14–21 小時 |
| **先修** | 完成 Week 01–11，理解 Agent / Task / Tool / Flow |
| **目標對象** | 要把 Agent 推上生產的工程師 |
| **驗證基礎** | 多數內容有 Anthropic / Claude API / Langfuse 一級來源支撐 |

### 模組學習目標

1. 用 `Agent = Model + Harness` 框架，判斷一個 Agent 系統「還缺什麼」
2. 依「控制流形狀」與「團隊約束」選對 Agent SDK
3. 設計並實作 harness 六層架構（Sandbox → Observability）
4. 理解「環境層優先於模型層」的縱深防禦原則並落地
5. 建立 trajectory 評估與 OTEL observability 管線

### 與主課程的對應關係

| 主課程週次 | 本模組強化點 |
|---|---|
| Week 07–08 Tools | 單元 3：Tools + MCP / A2A 協定 |
| Week 12 Testing | 單元 5：trajectory 評估（取代「只看最終輸出」） |
| Week 13 Observability | 單元 6：OTEL → Langfuse 雙層遙測 |
| Week 14 Deployment | 單元 2：Sandbox 縱深防禦 |
| Week 15 Multi-Agent | 單元 4：Orchestration 與 lifecycle |

---

## 單元 1：Harness 思維與框架選型

**Agentic 定位**：心智模型建立

**學習目標**

- 用 `Agent = Model + Harness` 重新理解「SDK 只是 harness 的一小塊」
- 掌握三大設計典範與選型決策樹

**理論內容**

- 公式拆解：harness 是「包裹 LLM、使它能行動而非僅回應的軟體基礎設施」
- 三大設計典範對照：
  - CrewAI — 角色導向組織模型
  - LangGraph — 圖形化有狀態工作流（支援 cycles）
  - AutoGen / AG2 — 對話式協作模型
- 校正常見誤解：**HITL 不是 AutoGen 獨有**（LangGraph `interrupt_before/after` 更強）
- 其餘框架定位：OpenAI Agents SDK、Claude Agent SDK、Pydantic AI、LlamaIndex、Semantic Kernel 等

**實作練習**

- Lab 1-1：用選型決策樹，為三個情境（內容生產線 / 複雜決策管線 / 人在迴路審核）各選一套框架並寫出理由
- Lab 1-2：盤點本課程現有的 CrewAI Lab，標出「哪些是 model 的事、哪些是 harness 的事」

**評量方式**

- 能說清「為什麼選 SDK 不等於做好 Agent」
- 選型理由扣回「控制流形狀」與「團隊約束」兩個維度

---

## 單元 2：Sandbox 與縱深防禦（環境層優先）

**Agentic 定位**：安全基礎設施

**學習目標**

- 理解 Anthropic 圍堵三層架構
- 落地「先在環境層圍堵，再在模型層引導」原則

**理論內容**

- 圍堵三層：環境層（sandbox / VM / filesystem 邊界 / egress）、模型層（system prompt / classifier）、外部內容存取控制（MCP / plugin）
- 核心原則：模型層保護是機率性的，「確定性邊界是當所有機率性防護都沒擋住時被打到的那條」
- 隔離強度匹配監督能力：gVisor 容器 / OS sandbox（Seatbelt、bubblewrap）/ 密封 VM
- 核可疲勞：使用者核可約 93% 的提示 → OS sandbox 達 84% 提示減少
- sandbox 與 permission 是**互補**，不是替代

**實作練習**

- Lab 2-1：為一個會跑 shell 的 Agent，設計 filesystem 邊界 + egress 白名單
- Lab 2-2：用 dev container 包一個高風險 Agent（non-root、只掛 workspace、避開 host 憑證目錄）

**評量方式**

- 能畫出三層圍堵圖並標出自己 Agent 的對應防護
- dev container 設定通過「不掛 host 憑證」檢查

---

## 單元 3：Tools、MCP / A2A 與工具設計

**Agentic 定位**：能力擴展層（對應主課程 Week 07–08）

**學習目標**

- 用 MCP 整合外部工具
- 設計 prompt-cache 友善的工具定義

**理論內容**

- 工具定義：模型可呼叫、與外部系統互動的預建函式
- 協定標準：MCP（Anthropic）與 A2A（Google）
- MCP 安全：**URL 匹配 remote server、精確 command + arguments 匹配 local stdio**；只靠名稱 allowlist 脆弱（標籤由使用者控制）
- Prompt caching 與工具排序：
  - 在 `tools` 陣列最後一個 tool 放 `cache_control: {"type":"ephemeral"}`
  - 失效階層 `tools → system → messages`
  - 工程含意：穩定的放前面、易變的放後面

**實作練習**

- Lab 3-1：把一個既有 CrewAI 工具改寫成 MCP server，並用精確 command 匹配做 allowlist
- Lab 3-2：量測加上 `cache_control` 前後的 token 成本差異

**評量方式**

- MCP allowlist 不可僅用名稱匹配
- 能解釋「為什麼改工具定義會讓整個快取失效」

---

## 單元 4：Orchestration、Context 與 Memory

**Agentic 定位**：狀態與控制流（對應 Week 15）

**學習目標**

- 把 context window 當成一級工程資源管理
- 設計三個時間尺度的記憶

**理論內容**

- Context 是「邊際報酬遞減的有限資源」
- Auto-compaction：接近上限時自動摘要舊 context；實證閾值 80–95%（Claude Code）/ 70-80-85-90-99%（分級壓力）
- 三個記憶時間尺度：short-term / session-level / persistent
- Lifecycle：從單 agent 內部迴圈 → multi-agent → 完整 issue→PR 管線
- State persistence（checkpointer / durable execution）— 標記為 open question，需另查實作

**實作練習**

- Lab 4-1：為長對話 Agent 實作一個簡單的 compaction 觸發器（達 85% window 時摘要）
- Lab 4-2：設計 session-level vs persistent 記憶的存放策略

**評量方式**

- compaction 觸發器能在接近上限時正確壓縮
- 能說明三個記憶尺度各放什麼

---

## 單元 5：Evaluation 與 Trajectory 評估

**Agentic 定位**：品質保證（取代主課程 Week 12「只看最終輸出」）

**學習目標**

- 理解為什麼最終輸出評估不夠
- 建立 trajectory 評估

**理論內容**

- 反直覺核心：**正確的最終答案可能掩蓋破損的推理**；幻覺工具呼叫的 Agent 仍可能猜對答案
- Trajectory 評估：捕捉完整執行樹——每個被選工具、每份被檢索文件、每個推理步驟
- 評估三分工（待整合）：trajectory 評估 / LLM-as-judge / 離線 dataset / 線上 production 監控

**實作練習**

- Lab 5-1：為一個工具型 Agent，寫一組 trajectory assertion（驗證它「用對工具」而非只「答對」）
- Lab 5-2：刻意製造一個「答案對但路徑錯」的案例，證明最終輸出評估會放過它

**評量方式**

- 測試能抓出「路徑錯但答案對」的案例
- 能解釋 trajectory 評估為何依賴 tracing

---

## 單元 6：Observability（OTEL → Langfuse）

**Agentic 定位**：可觀測性（對應主課程 Week 13）

**學習目標**

- 建立 OTEL 標準遙測管線
- 捕捉雙層遙測屬性

**理論內容**

- Langfuse 作為 **OpenTelemetry (OTLP) backend**（`/api/public/otel`）接收並映射 OTel trace
- OTEL 正成為 LLM / agent observability 的標準傳輸
- 雙層遙測：
  - **trace 層**：userId、sessionId、metadata、tags
  - **observation 層**：span type、input/output、模型資訊、token 用量、成本
- token / cost 在 trace 層自動聚合

**實作練習**

- Lab 6-1：把 Lab 5 的 Agent 接上 Langfuse，產生完整執行樹 trace
- Lab 6-2：在 trace 上掛 userId / sessionId，並讀出單次 session 的 token 成本

**評量方式**

- trace 能完整還原 Agent 的工具呼叫序列
- 能在 Langfuse 上定位「哪一步最花 token」

---

## 單元 7：Guardrails、HITL 與整合架構

**Agentic 定位**：控制平面與總整合

**學習目標**

- 用同步 hook 實作強制型 guardrail
- 組裝 harness 六層架構

**理論內容**

- **同步 vs 非同步 hook 的架構區別**：
  - 同步 PreToolUse hook = 可阻擋 / enforce（在權限提示前執行，可 deny / force prompt / skip）
  - async hook = 僅觀察 / log，無法阻擋（Agent 已往前走）
- Human-in-the-loop：interrupt → 人工核可 → resume
- 六層架構總覽與**落地順序**：先 L1 Sandbox → 再 L4 Guardrails → 才 L3 框架

```
L6 Observability   OTEL → Langfuse          ← 橫切全棧
L5 Eval/Feedback   trajectory eval + 自我驗證
L4 Guardrails      同步 PreToolUse hook + HITL
L3 Orchestration   agent loop / multi-agent  ← 框架選型在這
L2 Context+Memory  auto-compaction + Tools(MCP/A2A)
L1 Sandbox         OS sandbox / container / VM ← 先做這層
```

**實作練習**

- Lab 7-1：寫一個同步 PreToolUse hook，攔截危險指令（如 `rm -rf`）並 deny
- Lab 7-2（綜合）：把單元 2–6 的成果組裝成一個有 sandbox + guardrail + eval + observability 的完整 Agent

**評量方式**

- 同步 hook 能真正阻擋危險工具呼叫（驗證 async 做不到）
- 綜合 Lab 通過六層架構檢查表

---

## 模組總評量：Capstone 加值

在主課程 Week 16 Capstone 的基礎上，加一份 **Harness 成熟度自評**：

| 層級 | 檢查項 | 通過標準 |
|---|---|---|
| L1 Sandbox | 有 filesystem / egress 邊界 | 危險操作被環境層擋下 |
| L2 Context | 有 compaction 策略 | 長任務不爆 context |
| L2 Tools | MCP allowlist 非僅名稱 | 通過安全檢查 |
| L3 Orchestration | 控制流形狀說得清 | 選型理由成立 |
| L4 Guardrails | 同步 hook enforce | 危險呼叫被阻擋 |
| L5 Eval | 有 trajectory 評估 | 抓得到路徑錯 |
| L6 Observability | OTEL trace 完整 | 可定位成本熱點 |

---

## 教學注意事項（誠實聲明）

1. 框架橫向比較中，**只有 CrewAI / LangGraph / AutoGen 經對抗驗證**；其餘框架定位為補充知識，授課時應標明「待學員自行查證」。
2. harness 的「組件數量」業界無共識（7 層、12 primitives 兩套分類法均被駁回），本大綱採「組件集合」共識，切分為六層僅為教學便利。
3. 84% 權限提示減少為 Anthropic 自報內部指標，非外部 benchmark，授課時須如實說明。
4. 引用 Claude Code 權限模式細節前，請重新查官方 docs（研究中相關主張被駁回）。
