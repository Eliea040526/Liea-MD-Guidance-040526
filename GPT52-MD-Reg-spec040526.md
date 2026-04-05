1. System Overview
1.1 Goals
讓使用者在同一個 Hugging Face Space（Streamlit）中完成：
指引/已發布文件（txt/md/pdf）匯入或貼上
內容解析與結構化
針對 FDA 相關資料（510(k) Summary、Guidance、Recognized Standards）做外部檢索與引用
產出具可追溯引用、可下載、可套版的綜合報告（2000–3000 words）
由報告與原始指引的結構，生成新的 agent skill 的 skill.md（指定語言輸出）
全系統所有 LLM 相關功能皆支援：
使用者於執行前調整 prompt
選擇模型（含 OpenAI / Gemini / Anthropic / Grok）
調整 max_tokens（預設 12000）
逐 agent 執行、可將前一個 agent 的輸出手動編輯後餵給下一個 agent
UI 視覺與互動達到“WOW”：
Light/Dark、English/繁體中文
20 種名畫家風格（Jackpot 隨機）
狀態指示牆、互動 Dashboard、可視化 token/成本/速度/品質指標
1.2 Target Users
法規/RA、QA、510(k) 研究員、TFDA 查驗登記撰寫者、醫材研發 PM、顧問公司審查人員。
1.3 Deployment & Runtime Constraints
Hosting: Hugging Face Spaces
Framework: Streamlit
Configuration: agents.yaml 可由 UI 上傳覆蓋 session 設定（不落地）
LLM Providers: Gemini API、OpenAI API、Anthropic API、Grok API
Document Parsing: PDF text extraction、TXT/MD 讀取（可擴充 docx）
No-code-change requirement: 本文件僅定義規格與介面/流程/資料契約，不提供或修改任何程式碼。
2. Existing Features (Must Remain Intact)
2.1 Global UI Settings (WOW UI v1)
Theme: Light / Dark
Language: English / 繁體中文
Painter Styles: 20 styles（Van Gogh/Monet/.../Escher）
Jackpot: 一鍵隨機選風格
Default Model, Default max_tokens, Temperature 設定
API Keys：若環境變數存在則顯示 “from environment” 但不得顯示 key 值；若不存在則允許在 sidebar 輸入（password 欄位）
2.2 Agent Runner (核心互動模式)
每個 agent 皆具：
Prompt 可編輯
Model 可選
max_tokens 可調（預設 12000）
Input Text/Markdown 可編輯
Output 可用 Markdown / Plain text 檢視且可編輯
允許使用者將 agent 輸出手動修訂後作為下一個 agent 的輸入
2.3 Tabs (既有)
Dashboard（含 token usage、runs by model/tab、heatmap、latest snapshot status wall）
TW Premarket Application（含匯入匯出、完整度指標、screen review agent、doc helper agent）
510(k) Intelligence
PDF → Markdown
510(k) Review Pipeline（submission structuring + checklist-driven report）
Note Keeper & Magics（筆記整理 + 5 個魔法功能）
Agents Config Studio（檢視/編輯 agents.yaml）
3. New Major Capability: “Published Guidance → FDA & International Regulatory Research → Report → Template Report → Skill.md”
3.1 New Tab: “Guidance Research & Report Studio”
新增一個主工作區（tab）用於以下流程。所有輸出皆可編輯、下載（txt/md；skill.md 下載）。

Step A — Input Acquisition (Paste or Upload)
User Inputs

Document input methods:
Paste text/markdown
Upload files: .txt, .md, .pdf
PDF 解析選項：
頁碼範圍（from/to）
解析品質提示（若文字抽取不足，提示使用者改用文字版或較乾淨 PDF）
Output Language

使用者選擇輸出語言：
繁體中文（default）
English
Content Type Metadata (optional but recommended)

Guidance jurisdiction hint（FDA/TFDA/EU/IMDRF/ISO/IEC/MDR…）
Device type / intended use keywords
Product code / regulation number（若已知）
規格要求：即便使用者不填也可運作，系統需以文件內容自動推斷。

Step B — Guidance Understanding & Structuring Agent
Purpose

將輸入指引/指南轉換為清晰結構化 Markdown：
章節樹
核心要求（shall/should/must）
測試與證據類型（biocompatibility, sterilization, mechanical, software, EMC…）
名詞與縮寫表（glossary）
Key Output Artifacts

guidance_structured.md（可編輯）
requirement_list.json（內部資料契約；前端可視化用，使用者不需看見原始 JSON）
Step C — FDA-focused External Research Agent (Grounded Search)
使用者選擇模型（僅 Gemini）：

gemini-2.5-flash
gemini-3-flash-preview 並可自行修改 prompt。
Scope of Research

FDA 510(k) Summary Intelligence
依文件推斷 device 類別、可能 product code、可能 predicate 方向
產出「可能相關的 510(k) summary 欄位/測試項目」清單（不虛構 K number）
FDA Guidance
搜尋 FDA Guidance database 中相關 guidance（含 final / draft 標示）
FDA Recognized Consensus Standards
搜尋 Recognized Standards（ISO/IEC/ASTM/AAMI 等）並提取關鍵適用範圍
Grounding / Citations Requirements

所有外部研究必須輸出 Evidence Table（Markdown 表格），每列至少包含：
Source Type（Guidance / Standard / 510(k) summary template / FDA database page…）
Title
Organization（FDA/ISO/IEC/ASTM…）
URL
Relevance（1–5）
Extracted key points（簡短）
報告正文需採用可追溯引用格式，例如：
[^FDA-G-001] 腳註樣式，並在文末列出 references
或 (Source: FDA Guidance “xxx”, URL…) 的括號式引用
若無法存取或取得內容，必須明示「未能取得原文，僅列出索引頁面」並降低 confidence。
Search Implementation Specification (non-code)

優先使用官方來源：
FDA guidance pages
FDA Recognized Consensus Standards database
openFDA（若適用）
以 http(s) 取得頁面後進行：
去噪（導覽列/頁尾）
抽取標題、發布日期、適用範圍、關鍵段落
建立快取（session scope）避免重複抓取
Step D — Comprehensive Research-Backed Report Agent (2000–3000 words)
使用者可修改 prompt、選模型（Gemini 兩款），輸出語言依使用者選擇（預設繁中）。

Report Objective

將「使用者提供的 published guidance」與「FDA + 國際法規/標準/官方指引的外部研究」綜整成一份2000–3000 words 的 Markdown 報告，並明確指出：
文件內容對應的合規要求（按章節/主題）
可能涉及的國際法規框架（示例：US FDA、EU MDR/IVDR、IMDRF、ISO 13485、ISO 14971、IEC 60601/62304/82304-1…依文件類型而定）
必要的測試/驗證/文件證據清單
風險與缺口（Gap analysis：文件要求 vs 常見法規期待）
以 FDA 脈絡提出 510(k) submission 可能的 evidence mapping（不承諾分類與路徑，提供推論與假設條件）
Mandatory Sections (default)

Title / Document metadata（文件名、版本、來源、解析範圍）
Executive Summary（重點、結論、建議）
Device/Topic Characterization（從文件推論 device 類型、使用情境、風險類別）
Key Requirements Extracted from Provided Guidance（以表格呈現）
FDA Landscape
Relevant FDA guidance list
Recognized standards mapping
510(k) considerations（測試、predicate strategy、labeling）
International Regulatory & Standards Landscape
EU MDR / GSPR 對應（或其他適用司法轄區）
ISO 13485 / ISO 14971 對應
Evidence & Testing Matrix（要求 → 證據 → 標準 → 文件輸出）
Gaps, Risks, and Open Questions（含 confidence）
Practical Submission Checklist（可直接用於審查/送件）
References / Evidence Table（完整列出）
Editing & Download

使用者可在 Markdown 或 text 視圖直接修改
下載格式：
.txt
.md
Step E — Report Template Stage (User Template or Default)
Template Input Options

使用者上傳/貼上 “regulation report template”（txt/md）
選用系統內建 default template（例如使用者提供的範例：骨外固定器查驗登記審查指引與審查清單格式）
Template Engine Behavior

系統將模板解析為：
Section headings
Required tables
Checklist rows（若模板含審查清單表格）
Agent 依模板將 Step D 的 comprehensive report 重新排版並補足：
每一模板章節需對應到先前報告內容
若資訊不足：以「※待補」或「TBD」標示，不可杜撰
Output

templated_report.md（2000–3000 words 以模板為主，必要時允許更長但需可讀）
可編輯、可下載 .txt/.md
Step F — Skill Generator Stage (skill.md)
在使用者指定語言下，由 “skill creator” 格式生成完整 skill.md 內容（可下載），用於定義一個新 agent skill：

Skill Purpose

「輸入任一醫療器材 published guidance（pdf/txt/md 文字抽取後內容）→ 自動辨識該指引的結構與資訊密度 → 依其結構產出一份同等風格與深度的 comprehensive medical device guidance（含 checklist 與 evidence mapping），並可套用模板。」
Skill Output Requirements

必須包含 YAML frontmatter（name、description…）
技能描述需“pushy”以提高觸發率（在使用者提到 guidance、regulatory report、510(k)、standards mapping、checklist 等情境即應觸發）
全文使用使用者指定輸出語言（繁中或英文）
3 Additional WOW Features Inside This Skill (新增於 skill 本身)

Auto-Structure Mimicry
自動學習輸入 guidance 的章節結構與表格風格，輸出報告沿用相同「章節節奏」（例如：先 Review Guidance 再 Checklist）
Citation-Confidence Heat Labels
對每個主張標示 confidence（High/Med/Low）與原因（是否有官方來源 URL、是否為推論）
Checklist Autopilot + Gap Flags
從 guidance 內容自動生成審查清單，並在清單中加入“缺口旗標”（缺證據/缺標準/缺測試方法）
4. WOW UI v2 Enhancements (New + Existing Integrated)
4.1 Theme / Language / Painter Styles (Keep + Refine)
全站一致套用（Sidebar 一次設定，所有 tab 同步）
Painter styles 影響：
背景漸層
卡片陰影、按鈕形狀、badge
Jackpot 需同時觸發：
視覺切換動畫（spec：至少 200ms 過渡）
Dashboard “WOW moment” 提示（不打斷流程）
4.2 WOW Status Indicators (Cross-Tab)
新增更完整狀態體系（顯示於各 tab 頂部與 Dashboard）：

Agent lifecycle: pending / running / done / error
Evidence coverage gauge（外部來源數量、有效引用數量）
Report readiness score（完整度、模板對齊度、缺口數）
Token budget monitor（預估 token、上限、超限風險提示）
4.3 Awesome Interactive Dashboard (Expanded)
除既有 Runs/Model/Heatmap/Timeline 外，新增三類視覺：

Research Coverage Map
以類別顯示已抓取來源：FDA guidance / standards / others
Quality Signals Panel
citations count、low-confidence claims count、open questions count
Download Center
列出本 session 產生的 artifacts（報告、套版報告、skill.md、notes 等），一鍵下載
5. AI Note Keeper — Enhancements (Keep Original + Extend)
原有流程保留：貼上筆記→整理成結構化 Markdown→可編輯→AI Magics（至少 6 個；既有 5 個 + 新增 1 個或更多）。

5.1 New Requirement: Keywords in Coral Color (Already aligned)
預設 keyword 顏色：Coral（#FF7F50）
使用者可自訂顏色
支援手動 keywords 與 AI 建議 keywords（可作為新增 magic）
5.2 Additional AI Magics (Create/Extend)
在既有 Formatting / Keywords / Summary / Action Items / Glossary 之外，新增：

Magic 6 — AI Contradiction & Consistency Check
檢查筆記內部是否有矛盾（例如 SAL 要求、標準版本不一致、名詞混用），輸出修正建議與需確認問題清單
6. Three Additional WOW AI Features (System-Wide, New)
以下為額外新增（不取代既有功能），並需支援使用者修改 prompt / 選模型（全模型清單）。

6.1 WOW Feature #1 — Regulatory Delta Radar (Change Watch)
功能：使用者輸入「上次報告」與「本次報告/新 guidance」，系統輸出差異摘要：
新增/刪除要求
標準版本變更
測試項目增減
輸出：Markdown diff-like 摘要 + 影響評估
6.2 WOW Feature #2 — Evidence Traceability Graph (可視化追溯)
功能：將報告中的「主張 → 來源」關係形成可視化（至少表格；若可行則圖）
產出：
Claim ID
Claim text（摘要）
Source IDs（多對多）
Confidence
對審查與稽核（audit trail）友善
6.3 WOW Feature #3 — Smart Checklist Builder (From Any Report)
功能：從任一 Markdown 報告自動抽出 checklist（適用 TFDA/FDA/內部 QA）
支援輸出格式：
表格版（符合/不適用/待補）
任務清單版（To-do）
可選角色視角：Reviewer / Applicant / Auditor
7. Model & Prompt Control (Unified Requirements)
7.1 Supported Models (Global List)
OpenAI: gpt-4o-mini, gpt-4.1-mini
Gemini: gemini-2.5-flash, gemini-3-flash-preview, gemini-2.5-flash-lite, gemini-3-pro-preview
Anthropic: anthropic models（以 agents.yaml 定義為準）
Grok: grok-4-fast-reasoning, grok-3-mini
7.2 Per-Feature Constraints
Published Guidance external research + report + template + skill：模型限定 Gemini（flash 系列）以符合使用者要求
其他功能可用全模型
7.3 Token Defaults
全域 default max_tokens：12000
高篇幅報告（2000–3000 words）建議 UI 提示使用者調到更高上限（例如 16000–32000，依模型上限而定），但仍以使用者可控為準。
8. Agents & Data Contracts (Specification-Level)
8.1 Agents Catalog (Conceptual)
在 agents.yaml 中新增/擴充下列 agent 概念（實際 id 可調整，但需一致性）：

guidance_structuring_agent
fda_research_agent（search + evidence table）
comprehensive_reg_report_agent（2000–3000 words）
report_template_applier_agent
skill_md_generator_agent（skill creator format, specified language）
delta_radar_agent（WOW #1）
evidence_traceability_agent（WOW #2）
smart_checklist_builder_agent（WOW #3）
8.2 Artifact Naming (Session Scope)
input_guidance_raw
guidance_structured_md
evidence_table_md
comprehensive_report_md
templated_report_md
skill_md_output
traceability_table_md
delta_report_md
checklist_md
8.3 Quality & Safety Rules
禁止杜撰法規條文、標準編號、guidance 標題、URL
無法查證時：允許推論，但必須標註為推論並降低 confidence
報告必須包含：
“Assumptions & Limits”
“Open Questions”
“References/Evidence Table”
9. Example Output Expectations (Based on Provided Orthopedic External Fixators Template)
系統預設模板之一可包含：

第一部分：Review Guidance（產品規格、生物相容性、滅菌、機械測試、特殊風險如 MRI）
第二部分：Review Checklist（表格：審查項目、重點、結果、備註）
系統需能把 Step D 的研究報告內容映射進上述章節，並在 checklist 的每列加入：
建議證據文件（例如測試報告/標準符合聲明/風險評估）
對應的外部來源（FDA guidance / recognized standards）
10. Non-Functional Requirements
10.1 Performance
解析與研究流程需顯示 running 狀態與階段性完成（避免使用者誤以為卡住）
外部抓取需 session 快取，避免重複呼叫
10.2 Security & Privacy
API key handling：
若從環境變數取得：UI 僅顯示 “from environment”，不得回顯 key
若使用者輸入：使用 password 欄位；不寫入檔案、不輸出到報告
文件內容屬可能機敏：明示僅在 session 記憶體中處理（Hugging Face Spaces 的日誌策略需在 UI 提示避免貼敏感個資）
10.3 Auditability
Dashboard 保存每次 agent run 的 metadata（tab、agent、model、tokens_est、timestamp）
研究報告提供 evidence table 與 traceability table（可稽核）
11. UX Flow Summary (End-to-End)
使用者選擇 Theme/Language/Painter style（可 Jackpot）
進入 Guidance Research & Report Studio
上傳/貼上 guidance（txt/md/pdf），選輸出語言（預設繁中）
執行：
Guidance Structuring → 可編輯輸出
FDA External Research → evidence table → 可編輯
Comprehensive Report (2000–3000 words) → 可編輯/下載
選擇/提供報告模板 → Template Report → 可編輯/下載
生成 skill.md（指定語言 + 3 個 skill 內 WOW 功能）→ 可編輯/下載
可選啟用 WOW AI：
Delta Radar
Traceability Graph/Table
Smart Checklist Builder
Dashboard 自動更新狀態牆與品質指標
12. Exactly 20 Comprehensive Follow-up Questions (for next iteration)
你希望「外部搜尋 FDA 資訊」的允許範圍到哪裡：僅限 FDA 官方網站（Guidance/Standards/openFDA），還是可包含 NCBI、PubMed、IMDRF、EU 官網等？
是否需要支援輸入多份 guidance（多檔案合併）並產出一份整合報告？若需要，合併策略是依時間/優先層級/司法管轄？
對 PDF 抽取失敗（掃描影像）的處理，你希望加入 OCR（例如 Tesseract）規格嗎？Hugging Face Space 的資源限制是否可接受？
2000–3000 words 的計算基準要用英文 words、中文以字數換算、還是段落/頁數近似？
報告的引用格式偏好：腳註（[^id]）或括號式（Source: …），是否需要可切換？
Evidence Table 的最低欄位是否還要加上：發布日期、適用 device 類別、標準版次、取用時間（retrieved on）？
對 “510(k) summary” 的研究，你希望系統僅提供「可能需要的段落與常見 testing」還是要嘗試定位真實 predicate/真實 K number（可能需要更強搜尋）？
是否要加入 “Product Code/Regulation Number 推斷器”，並在報告中輸出推斷依據與不確定性？
報告模板套版時，若模板要求的章節在前一份報告沒有對應內容，你希望：插入 TBD、或強制重新研究補足、或提示使用者手動補？
你希望提供多少個內建 default report templates（除了骨外固定器範例），以及要涵蓋哪些器材類別？
“Smart Checklist Builder” 的輸出是否需要支援 CSV/Excel 下載（即使主體仍是 Streamlit）？
Dashboard 的 token/cost 顯示是否需要按 provider 套用不同單價模型，還是只做 token 估算即可？
是否要在每個 agent output 加入 “變更追蹤”（例如保留前次輸出快照，支援 compare）？
對 Note Keeper 的 keyword coral 標示，你希望是 HTML 渲染（span）還是純 Markdown（例如加粗/背景碼）以提升相容性？
你希望 “Citation-Confidence Heat Labels” 的評分規則是固定規則（rule-based）還是由 LLM 判斷再輸出理由？
skill.md 生成時，skill 的觸發描述你希望更偏向「醫材法規報告」還是更泛用「任何 guidance 轉報告」？
是否需要在 skill 中明確規範輸出章節必須包含的最小集合（例如一定要有風險、標準、測試矩陣、checklist）？
外部搜尋若遇到 rate limit 或連線失敗，你希望系統自動降級（只用已取得資料）還是直接中止並要求重試？
對已產出的報告，你是否希望加入 “合規聲明草稿/cover letter 草稿” 的一鍵生成（作為額外可選輸出）？
是否要把這條 “Guidance→Research→Report→Template→Skill” 流程也做成可在 Agents Config Studio 中可視化編排的 pipeline（類似拖拉式/順序清單式）？
