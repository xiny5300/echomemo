# EchoMemo - 自主建立 AI 數位人格機

數位分身

## 專案簡介

EchoMemo 是一個運行於 Raspberry Pi 5 的 AI 數位人格系統，透過每日對話搜集使用者的聲音與記憶，建立數位分身。

## 系統特性

- **雙重語音系統**：官方導引音 + 數位分身音
- **四種模式**：每日訪談、聊天、日記回顧、提醒
- **硬體互動**：OLED 顯示器、旋轉編碼器、按鈕控制
- **AI 整合**：使用 Google Gemini 1.5 Flash 進行語音識別和對話生成
- **語音克隆**：整合 aiclonevoicefree.com API 進行語音合成

## 硬體需求

- Raspberry Pi 5
- 0.96" OLED 顯示器 (SSD1306, I2C)
- 旋轉編碼器 (KY-040 / EC11)
- 按鈕 x2
- USB 麥克風
- 音訊輸出裝置

## GPIO 腳位配置 (根據 spec.md 已驗證的接線)

- **OLED (I2C)**: 
  - SDA: GPIO 2
  - SCL: GPIO 3
  - I2C Address: 0x3C
- **旋轉編碼器 (EC11)**: 
  - CLK: GPIO 22 (Pin 15)
  - DT: GPIO 27 (Pin 13)
  - SW: GPIO 17 (Pin 11) - 編碼器按鈕
- **錄音按鈕**: 
  - GPIO 23 (Pin 16) - 獨立按鈕

## 安裝步驟

1. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

2. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 檔案，填入您的 API 金鑰
```

3. **準備音效檔**
將系統音效檔放置在 `assets/system/` 目錄下：
- `thinking_filler.wav` - 思考音效
- `reminder_alert.wav` - 提醒音效

4. **初始化資料庫**
資料庫會在首次執行時自動建立。

## 使用說明

### 啟動系統
```bash
python main.py
```

### 模式操作

1. **每日訪談模式 (MODE_DAILY)**
   - 系統會自動生成問題並播放
   - 按住錄音按鈕開始錄音
   - 放開按鈕停止錄音並儲存

2. **聊天模式 (MODE_CHAT)**
   - 按住錄音按鈕錄音
   - 系統會使用 RAG 搜尋相關記憶
   - 以數位分身音回應

3. **日記回顧模式 (MODE_DIARY)**
   - 旋轉編碼器切換日期
   - 按下編碼器按鈕播放該日記錄

4. **提醒模式 (MODE_REMINDER)**
   - 按下按鈕啟動 10 秒倒數
   - 時間到後播放提醒音效

### 模式切換
- 旋轉編碼器：切換模式
- 按下編碼器按鈕：確認選擇

## API 設定

### Google Gemini API
1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 建立 API 金鑰
3. 將金鑰填入 `.env` 的 `GEMINI_KEY`

### 語音克隆 API
1. 前往 [aiclonevoicefree.com](https://aiclonevoicefree.com)
2. 註冊並取得 API 金鑰
3. 上傳語音樣本取得語音 ID
4. 將金鑰和語音 ID 填入 `.env`

## 檔案結構

```
echomemo/
├── main.py              # 主程式（狀態機）
├── config.py            # 配置管理
├── requirements.txt     # 依賴套件
├── .env                 # 環境變數（需自行建立）
├── data/
│   └── memories.db      # SQLite 資料庫
├── modules/
│   ├── hardware.py      # GPIO 硬體控制
│   ├── display.py       # OLED 顯示
│   ├── audio.py         # 音訊處理
│   ├── ai.py            # Gemini AI 整合
│   └── database.py      # 資料庫操作
└── assets/
    ├── system/          # 系統音效檔
    └── fonts/           # 字型檔
```

## 開發說明

每個模組檔案都包含詳細的註解說明：
- **檔案標準 (Standard)**: 職責和輸入輸出規範
- **執行方式 (Execution)**: 如何呼叫或測試
- **相依性 (Dependencies)**: 需要的硬體和函式庫

## 疑難排解

### 音訊問題
- 確認 USB 麥克風已正確連接
- 檢查 Alsa 音訊卡設定：`arecord -l`
- 確認 PulseAudio/PipeWire 正常運作

### GPIO 問題
- 確認硬體連接正確
- 檢查 GPIO 權限：`sudo usermod -a -G gpio $USER`
- 重新登入後再試

### OLED 顯示問題
- 確認 I2C 已啟用：`sudo raspi-config`
- 檢查 I2C 裝置：`i2cdetect -y 1`
- 確認 OLED 地址為 0x3C
