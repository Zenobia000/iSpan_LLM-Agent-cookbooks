# Agent SDK 全景與 Harness Engineering 工程化分析

> 本文件由 Deep Research（104 個 subagent、22 來源、109 條主張 → 25 條對抗式驗證 → 22 條通過）整理而成。
> 研究日期：2026-06-23

---

## 研究誠實聲明（先讀這段）

本研究的對抗式驗證**只穩固確認了 CrewAI / LangGraph / AutoGen 三者**的設計理念與場景對應。其餘框架（OpenAI Agents SDK、Claude Agent SDK、LangChain、LlamaIndex、Google ADK、Pydantic AI、Mastra、Vercel AI SDK、Semantic Kernel、Strands Agents）**未取得各自經三票驗證的主張**——這是本研究最大的覆蓋缺口。

文中標記規則：

- `[已驗證]`：有引用來源、經三票對抗驗證通過。
- `[補充]`：基於既有工程知識補齊、**未經本次對抗驗證**，請當作待查證的工程判斷，而非事實斷言。

harness 組件與安全部分多數有 Anthropic / Claude API / Langfuse 一級來源支撐；框架橫向比較較弱（多為跨源 secondary/blog 共識）。

---

## 一、核心判斷：問題問錯了一半

業界已把這件事凝練成一條公式：

> **Agent = Model + Harness** — harness 是「包裹 LLM、使它能『行動』而非僅『回應』的軟體基礎設施」。`[已驗證, Databricks]`

Harness engineering 被定義為：

> 「設計 agent 外圍 scaffolding（context delivery、tool interfaces、planning artifacts、verification loops、memory、sandboxes）的工程學科，**明確區別於 model / SDK 本身**」，且強調「每個組件存在，都是因為模型單靠自己做不到」。`[已驗證, ai-boost repo + Databricks]`

**對選型問題的意義**：SDK 只是 harness 的一小塊（主要負責 agent loop 與 orchestration DSL）。「選哪套 SDK」和「怎麼做 harness engineering」是兩個不同層級的問題——選 SDK 決定不了生產可用性，真正的工程量在 SDK 外圍那七、八個組件。

---

## 二、Agent SDK / 框架全景與選型

### 2.1 經驗證的三大設計典範 `[已驗證, DataCamp + 官方論文/repo]`

| 框架 | 設計理念 | 核心機制 | 適用場景 |
|---|---|---|---|
| **CrewAI** | 角色導向組織模型（仿真實組織結構） | role / goal / task 映射到「員工」 | 任務能清楚拆成角色與職責的專案（內容生產線、研究團隊模擬） |
| **LangGraph** | 圖形化有狀態工作流 | 節點 + 邊 + typed State；**支援 cycles**，agent 可 loop / retry / reflect | 需循環、分支、retry 的複雜非線性決策管線 |
| **AutoGen / AG2** | 對話式協作模型 | multi-agent conversation | 人在迴路的腦力激盪式監督系統 |

**關鍵校正**（驗證階段特別標註）：**HITL 不是 AutoGen 獨有**。LangGraph 的 `interrupt_before/after` 提供更強的生產級 human-in-the-loop，CrewAI 也有人工檢查點。所謂「場景對應」是軟性啟發式（suits），不是排他規則。

LangGraph 官方定位另有獨立驗證：「不像只支援 DAG 的框架，LangGraph 支援 cycles，所以 agent 能 loop、retry、reflect」。`[已驗證, LangChain docs]`

### 2.2 其餘框架定位 `[補充，未經本次對抗驗證]`

依「抽象層級」與「誰持有控制流」分類：

**A. 廠商原生、貼近模型的「薄」SDK**

- **OpenAI Agents SDK**（前身 Swarm 的生產版）：輕量、handoffs + guardrails + sessions + 內建 tracing。理念是「少抽象、貼 API」，適合 OpenAI 生態、想要原生 tracing 又不想被重框架綁死。
- **Anthropic Claude Agent SDK**（前身 Claude Code SDK）：把 Claude Code 的 harness（context 自動 compaction、檔案系統、subagent、MCP、權限/hooks、sandbox）開放給開發者。**這是市面上「內建 harness 最完整」的一套**——它本身就是一個 harness，不只是 agent loop。適合 coding agent / 長時程自主任務。
- **Google ADK**：偏企業、與 Vertex/Gemini 整合，內建 evaluation 與 A2A。

**B. 型別優先 / 工程師取向**

- **Pydantic AI**：以 Pydantic 型別系統做結構化輸出與依賴注入，理念是「FastAPI 式開發體驗」。適合重視型別安全、結構化輸出的 Python 後端團隊。
- **Vercel AI SDK** / **Mastra**：TypeScript 生態。AI SDK 偏前端/全端串流 UI；Mastra 是 TS 上較完整的 agent 框架（workflow、memory、eval）。適合 Node / Next.js 產品團隊。

**C. 重編排 / 企業整合**

- **LangChain**：最大的整合生態（model / vector / tool wrappers），但抽象層厚、版本動盪大。現在定位偏「元件庫」，編排交給 LangGraph。
- **LlamaIndex**：RAG 起家，data framework + 近年的 agent/workflow。適合「資料密集、檢索為核心」的 agent。
- **Semantic Kernel**：微軟、.NET / C# 與企業整合首選，plugin + planner 模型。
- **Strands Agents**（AWS）：model-driven、內建 trajectory evaluator，與 AWS 生態整合。

### 2.3 選型決策樹（實用主義）

```
你的控制流是什麼形狀？
├─ 線性 / 角色分工明確      → CrewAI
├─ 有環、有分支、需 retry   → LangGraph
├─ 對話式、人盯著監督        → AutoGen / AG2
└─ 長時程自主 coding / 任務  → Claude Agent SDK（harness 最完整）

你的約束是什麼？
├─ 重型別安全 (Python)      → Pydantic AI
├─ TS / 前端串流            → Vercel AI SDK / Mastra
├─ RAG 為核心              → LlamaIndex
├─ .NET / 企業             → Semantic Kernel
└─ 鎖定單一廠商最佳整合      → OpenAI Agents SDK / Google ADK / Strands
```

> **Linus 式提醒**：別為了「框架很潮」引入 LangChain 全家桶。多數專案一個薄 SDK + 自己寫 agent loop 就夠，重點工程量在下面的 harness 組件，不在框架選擇。

---

## 三、Harness Engineering 工程化組件清單

這是核心。組件**集合**有業界共識，但**切分數量沒有共識**——研究中「7 層 ETCLOVG」和「12 primitives」兩套分類法都在對抗驗證中被駁回（1-2），唯一穩固的是 Databricks 的「八組件」與 ai-boost 的 scaffolding 定義。

### 生產級 harness 的八大組件 `[已驗證, Databricks]`

> system prompts、tools/工具執行、sandboxes、filesystem/持久化儲存、memory & context 管理、回饋迴路/自我驗證、guardrails & 人在迴路控制、observability/logging。

以下整理成可落地的工程清單。

### 1. Context 管理（一級工程問題）`[已驗證]`

- 把有限 context window 當成「邊際報酬遞減的有限資源」。`[Anthropic]`
- **接近上限時自動 compaction / 摘要**舊 context。`[ai-boost + Anthropic]`
- 實證閾值：Claude Code 約在 **80–95%** window 觸發 auto-compaction；OpenDev 用 70/80/85/90/99% 分級壓力閾值。`[已驗證]`
- 治理三個時間尺度：short-term / session-level / persistent。`[LLM-Harness]`

### 2. Tools / 工具執行 + 協定整合 `[已驗證]`

- 工具 = 模型可呼叫、與外部系統互動的預建函式（搜尋、查 DB、寄信、跑 code、call API）。`[Databricks]`
- 規範「能力如何被描述、發現、呼叫」，**明確包含 MCP（Anthropic）與 A2A（Google）兩大協定標準**。`[LLM-Harness]`

### 3. Sandbox 執行環境（縱深防禦的第一道）`[已驗證, Anthropic 一級來源]`

研究中最紮實的一塊。Anthropic 的圍堵（containment）三層架構：

- **環境層**：process sandbox、VM、檔案系統邊界、egress 控制
- **模型層**：system prompt、classifier、probe、訓練
- **外部內容存取控制**：MCP server、第三方 plugin、web search

**核心設計原則（逐字）**：「**先在環境層設計圍堵，再在模型層引導行為**」——因為模型層保護是機率性的，「當所有機率性防護都沒擋住時，被打到的是那條確定性邊界」。`[已驗證]`

隔離強度按使用者監督能力匹配：

- claude.ai → ephemeral gVisor 容器（per-session 檔案系統）
- Claude Code → 本地 OS sandbox（macOS Seatbelt / Linux bubblewrap）+ HITL 核可
- Cowork → 密封 VM（憑證留 host keychain，永不進 guest）

Claude Code 的 OS sandbox 達 **84% 權限提示減少**（解決使用者核可約 93% 提示的「核可疲勞」）。`[已驗證，但屬 Anthropic 自報內部指標，未經獨立稽核]`

對高風險 repo，**dev container / VM 比單純權限規則是更乾淨的邊界**，因其能聯合控制 filesystem / user / network / registry / credentials / runtime——sandbox 與 permission 是互補，不是替代。`[已驗證]`

### 4. 持久化 / State persistence `[組件已驗證；實作細節為 open question]`

- filesystem + 持久化儲存是八組件之一。`[Databricks]`
- 但 state checkpointing（LangGraph checkpointer、durable execution）與 HITL resume 的**具體實作沒取得獨立驗證主張**——需另查。

### 5. Memory `[已驗證為組件，與 context 管理同層]`

### 6. Orchestration / Agent Lifecycle `[已驗證]`

- 組織讀寫 state 的控制流，從單 agent 內部迴圈到 multi-agent 模式，到完整的 issue → PR 任務管線。`[LLM-Harness]`

### 7. 回饋迴路 / 自我驗證 + Evaluation `[已驗證]`

**最重要的反直覺結論**：

> 「只評估最終輸出不足以評估 agent——正確的最終答案可能掩蓋破損的推理；一個幻覺工具呼叫的 agent 仍可能產出正確結果。」`[已驗證, LangChain]`

因此需要 **trajectory（軌跡）評估**，而它依賴能捕捉**完整執行樹**的 tracing——每個被選工具、每份被檢索文件、每個推理步驟。`[已驗證，arXiv / NVIDIA / Anthropic / Strands 多源佐證]`

### 8. Guardrails + Human-in-the-loop（強制 vs 觀察的架構區別）`[已驗證]`

- 用 Claude Code hooks 實作：**PreToolUse hook 在權限提示前執行**，可 deny / force prompt / skip prompt。`[已驗證, 官方 docs]`
- **關鍵架構區別**：**同步 hook = 可阻擋 / enforce；async hook = 僅觀察 / log，無法阻擋**（agent 已往前走了）。要做強制型 guardrail 必須用同步。`[已驗證]`
- MCP 安全：**用 URL 匹配 remote server、用精確 command + arguments 匹配 local stdio server**；只靠名稱 allowlist 是脆弱的，因為標籤由使用者控制。`[已驗證, Anthropic docs + OWASP]`

### 9. Observability / Tracing `[已驗證, Langfuse 一級來源]`

- 可用 Langfuse 作為 **OpenTelemetry (OTLP) backend**（`/api/public/otel` 端點）接收 OTel trace 並映射其資料模型——**OTEL 正成為 LLM / agent observability 的標準傳輸**。
- 必抓兩層遙測：**trace 層**（userId、sessionId、metadata、tags）+ **observation 層**（span type、input/output、模型資訊、token 用量、成本）。token / cost 在 trace 層自動聚合。

### 10. Prompt Caching（成本 / 延遲層）`[已驗證, Claude API docs]`

- 在 `tools` 陣列**最後一個 tool** 放 `cache_control: {"type":"ephemeral"}`，可快取整段工具定義前綴。
- **前綴失效階層 `tools → system → messages`**：改工具定義 → 三層全失效；切 `tool_choice` / images / thinking → 僅 messages 層失效（tools + system 保留）。
- 工程含意：**把穩定的東西（工具、system）放前面，易變的放後面**，才吃得到快取。

---

## 四、建議的 Harness 分層架構

```
┌─────────────────────────────────────────────────────────┐
│  L6 Observability:  OTEL → Langfuse (trace + observation)   │ ← 橫切，貫穿全棧
├─────────────────────────────────────────────────────────┤
│  L5 Eval / Feedback:  trajectory eval + 自我驗證迴路          │
├─────────────────────────────────────────────────────────┤
│  L4 Guardrails:  同步 PreToolUse hook (enforce) + HITL       │
├─────────────────────────────────────────────────────────┤
│  L3 Orchestration (SDK):  agent loop / multi-agent / 圖      │ ← 框架選型在這層
├─────────────────────────────────────────────────────────┤
│  L2 Context + Memory:  auto-compaction(80-95%) + 三尺度記憶   │
│      Tools:  MCP / A2A + 工具定義(prompt-cache 友善排序)       │
├─────────────────────────────────────────────────────────┤
│  L1 Sandbox (確定性邊界):  OS sandbox / container / VM        │ ← 先做這層
│      filesystem 邊界 + egress 控制 + 憑證隔離                  │
└─────────────────────────────────────────────────────────┘
```

**落地順序**（依 Anthropic「環境層優先」原則）：**先 L1 sandbox → 再 L4 guardrails → 才 L3 框架**。

多數團隊順序做反了——先挑框架、最後才補安全，結果模型層 guardrail 擋不住就直接打到「沒有的那條確定性邊界」。

---

## 五、覆蓋缺口與待查證（誠實清單）

研究本身標記的限制：

1. **框架橫向比較不完整**——只有 CrewAI / LangGraph / AutoGen 經驗證，其餘 10 套是補充、需逐一獨立查證（本報告最大缺口）。
2. **「標準組件數量」無共識**——7 層、12 primitives 兩套分類法都被駁回，只有「組件集合」有共識。
3. **被駁回的主張**（0-3）：Claude Code 的四種權限模式（plan / default / acceptEdits / dontAsk）+ managed-overrides-user 分層模型——引用權限機制細節時請重新查官方 docs。
4. **state persistence / checkpointing 與 HITL resume 的具體實作**未取得驗證主張，是 open question。
5. 框架比較主要靠 secondary / blog（8+ 篇跨源共識），不如 Anthropic / Claude API 那幾條一級來源紮實。

### 後續可補的 Open Questions

- 那 10 套框架各自的設計理念、原生 harness 內建程度（內建 sandbox / memory / observability 與否）與優缺點——需逐框架做多源驗證。
- state persistence / checkpointing 與 HITL resume 的具體實作模式。
- evaluation 層除 trajectory 外，LLM-as-judge、離線 dataset 評估、線上 production 監控三者如何分工整合。
- MCP / A2A 之外，跨框架工具/agent 互操作標準是否會收斂為單一事實標準。

---

## 附錄：來源清單

### 一級來源（primary）

- Anthropic — How we contain Claude: <https://www.anthropic.com/engineering/how-we-contain-claude>
- Anthropic — Claude Code sandboxing: <https://www.anthropic.com/engineering/claude-code-sandboxing>
- Anthropic — Effective context engineering: <https://www.anthropic.com/engineering>
- Claude API — Tool use with prompt caching: <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-use-with-prompt-caching>
- Claude Code — Hooks: <https://code.claude.com/docs/en/hooks>
- Claude Code — Managed MCP: <https://code.claude.com/docs/en/managed-mcp>
- Langfuse — OpenTelemetry: <https://langfuse.com/integrations/native/opentelemetry>
- LangChain — LLM evaluation framework: <https://www.langchain.com/resources/llm-evaluation-framework>
- LangGraph docs: <https://docs.langchain.com/oss/python/langgraph>
- LLM-Harness taxonomy: <https://picrew.github.io/LLM-Harness/>

### 次級來源（secondary）

- Databricks — AI harness (Agent = Model + Harness): <https://www.databricks.com/blog/ai-harness>
- ai-boost — awesome-harness-engineering: <https://github.com/ai-boost/awesome-harness-engineering>
- DataCamp — CrewAI vs LangGraph vs AutoGen: <https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen>
- General Analysis — Claude Code security best practices: <https://generalanalysis.com/guides/anthropic-claude-code-security-best-practices>

（完整 22 來源見研究原始輸出。）
