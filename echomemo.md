# Role
你是資深的 Python 嵌入式系統架構師，專精於 Raspberry Pi 5、Asyncio 非同步架構以及 Google Gemini 多模態 AI 整合。

# 🔴 CRITICAL INSTRUCTION (最高指令)
請你依照本 MD 檔裡面的安排，生出這個系統所有需要的檔案。
在架構整個系統的時候，請**完全以本 MD 檔為標準**。
**變更通知：** 本專案 **不使用 OpenAI**。STT (聽) 與 LLM (腦) 全部統一使用 **Google Gemini 1.5 Flash**。

**必須執行：** 在產生每一個程式碼檔案 (`.py`) 時，必須在檔案的最開頭以註解形式 (`""" ... """`) 詳細註記：
1. **檔案標準 (Standard):** 該檔案的職責、輸入輸出規範。
2. **執行方式 (Execution):** 該檔案是被誰呼叫，或是如何獨立測試。
3. **相依性 (Dependencies):** 需要哪些硬體或 Library。

---

# Project: echomemo (自主建立 AI 數位人格機)
**核心價值：** 透過每日對話搜集使用者的聲音與記憶，建立數位分身。
**系統特性：** 運行於 Raspberry Pi 5，具備實體滾輪與按鈕互動，擁有「官方系統音」與「數位分身音」雙重語音系統。

# 1. Hardware Specification (Pinout Standards)
請嚴格遵守以下腳位設定，並使用 `gpiozero` 函式庫實作：

* **Display (I2C):**
    * Device: 0.96" OLED (SSD1306) | Resolution: 128x64
    * Pins: **SDA (GPIO 2), SCL (GPIO 3)**
    * Library: `luma.oled`, `luma.core`
* **Rotary Encoder (KY-040 / EC11) - 用於模式切換:**
    * CLK: **GPIO 5**
    * DT: **GPIO 6**
    * SW (Button): **GPIO 13** (Active Low, Pull-up required)
    * Library: `gpiozero.RotaryEncoder`
* **Record Button (Push Button):**
    * Pin: **GPIO 17** (Active Low, Pull-up required)
    * Logic: 按住 (Hold) = 錄音，放開 (Release) = 停止錄音。
* **Audio Hardware:**
    * Input: USB Microphone (Alsa default card 1).
    * Output: System Default (PulseAudio/PipeWire).

# 2. Dual-Voice System Architecture (音訊標準)
系統必須在 `modules/audio.py` 中區分：
1.  **System Voice (官方導引音):**
    * 用途：介面提示、每日訪談提問。
    * 實作：
        * 優先使用 `assets/system/` 下的預錄 `.wav`。
        * 若需即時生成 (如訪談問題)，呼叫 Mix Voice API (`SYSTEM_VOICE_ID`)。
2.  **Persona Voice (數位分身音):**
    * 用途：模仿使用者的語氣說話。
    * 實作：呼叫 Mix Voice API (`PERSONA_VOICE_ID`)。

# 3. AI Tech Stack (Google Gemini Only)
* **All-in-One Model:** Google Gemini 1.5 Flash (`google-generativeai`).
* **STT (語音轉文字):** 不使用 OpenAI。請使用 Gemini 的 `genai.upload_file` 上傳音檔，並 Prompt 它：「請逐字聽寫這段錄音的內容」。
* **LLM (對話生成):** 使用同一個 Gemini Client，但在 Chat Session 中設定 System Prompt 切換人格。
* **Storage:** SQLite (`data/memories.db`)。

# 4. Software Architecture (State Machine)
系統必須是 **Asyncio 非同步架構**。
請在 `main.py` 實作以下狀態機：

* **MODE_DAILY (每日訪談):**
    * Entry: 螢幕顯示 "構思問題...", 播放 "thinking_filler.wav", 同步呼叫 Gemini 生成問題 -> Mix Voice 轉語音 -> 播放。
    * Loop: 等待按鈕 -> 錄音 -> **Gemini STT** -> 存檔 -> 系統回饋 "已記錄"。
* **MODE_CHAT (聊天模式):**
    * Loop: 等待按鈕 -> 錄音 -> **Gemini STT** -> RAG(搜尋資料庫) -> Gemini(Persona Echo) -> Mix Voice TTS -> 播放。
* **MODE_DIARY (日記回顧):**
    * Loop: 監聽編碼器旋轉 -> 更新螢幕日期 -> 按下播放。
* **MODE_REMINDER (提醒模式 - Demo):**
    * Action: 按下按鈕 -> 啟動 10 秒非阻塞倒數 (Async Sleep)。
    * Trigger: 時間到 -> 檢查是否錄音中 (避開衝突) -> 播放 `reminder_alert.wav`。

# 5. File Structure & Implementation Plan
請依照此結構建立檔案：

```text
echomemo/
├── main.py              # [Entry] 主程式
├── config.py            # [Config] 讀取 .env (GEMINI_KEY, MIX_VOICE_KEY)
├── data/
│   └── memories.db      # SQLite
├── modules/
│   ├── hardware.py      # [HW] GPIO 控制
│   ├── display.py       # [UI] OLED 顯示
│   ├── audio.py         # [Audio] 錄音、Mix Voice API
│   ├── ai.py            # [Brain] 封裝 Gemini (包含 STT 與 Chat 功能)
│   └── database.py      # [DB]
├── assets/
│   ├── system/          # 音效檔
│   └── fonts/           # 字型檔
└── .env                 # API Keys