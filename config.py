"""
檔案標準 (Standard):
本檔案負責讀取和管理系統配置，包括從 .env 檔案載入 API 金鑰和系統設定。
輸入：.env 檔案中的環境變數
輸出：提供配置物件供其他模組使用

執行方式 (Execution):
- 被 main.py 和其他模組在啟動時匯入使用
- 獨立測試：python config.py (會顯示載入的配置，但不顯示敏感資訊)

相依性 (Dependencies):
- python-dotenv: 用於讀取 .env 檔案
- os: 系統環境變數存取
"""

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class Config:
    """系統配置類別
    
    根據 spec.md 和 echomemo.md 的硬體規格設定：
    - Raspberry Pi 5 (16GB RAM)
    - 0.96" OLED (SSD1306, I2C Address: 0x3C)
    - EC11 旋轉編碼器
    - 獨立錄音按鈕
    """
    
    # Google Gemini API
    GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # 語音克隆 API (aiclonevoicefree.com)
    VOICE_CLONE_API_KEY = os.getenv('MIX_VOICE_API_KEY', '')
    VOICE_CLONE_UPLOAD_URL = 'http://8.148.211.142:8080/api/upload/audio'
    VOICE_CLONE_SYNC_URL = 'https://aivoiceclonefree.com/api/instant/clone-sync'
    
    # 語音 ID (用於區分系統音和分身音)
    # 這些需要先上傳對應的語音樣本後獲得
    SYSTEM_VOICE_ID = os.getenv('SYSTEM_VOICE_ID', '')  # 官方導引音
    PERSONA_VOICE_ID = os.getenv('PERSONA_VOICE_ID', '')  # 數位分身音
    
    # ========== 硬體設定 (根據 spec.md 已驗證的接線) ==========
    
    # 是否啟用真實硬體
    HARDWARE_MODE = True
    
    # OLED 顯示器設定 (I2C)
    # Device: 0.96" OLED (SSD1306)
    # I2C Address: 0x3C (已驗證)
    OLED_I2C_ADDRESS = 0x3C
    OLED_WIDTH = 128
    OLED_HEIGHT = 64
    
    # OLED I2C 腳位 (硬體已固定)
    GPIO_SDA = 2  # SDA (GPIO 2)
    GPIO_SCL = 3  # SCL (GPIO 3)
    
    # ========== 旋轉編碼器 (EC11) - 用於模式切換 ==========
    # 根據 spec.md: 輸入 1 (導航)
    # 實體腳位對應：
    #   - Pin 11 -> BCM 17 (SW)
    #   - Pin 13 -> BCM 27 (DT)
    #   - Pin 15 -> BCM 22 (CLK)
    GPIO_ROTARY_CLK = 22  # CLK (Pin 15) - 時鐘信號
    GPIO_ROTARY_DT = 27   # DT (Pin 13) - 方向信號
    GPIO_ROTARY_SW = 17    # SW (Pin 11) - 按鈕 (Active Low, Pull-up required)
    
    # 為了向後相容，保留 PIN_* 命名
    PIN_CLK = GPIO_ROTARY_CLK
    PIN_DT = GPIO_ROTARY_DT
    PIN_SW = GPIO_ROTARY_SW
    
    # ========== 錄音按鈕 (獨立按鈕) ==========
    # 根據 spec.md: 輸入 2 (錄音)
    # 實體腳位：Pin 16 -> BCM 23
    # 邏輯：設為 Pull-Up，按下為 Low
    # 行為：按住 (Hold) = 錄音，放開 (Release) = 停止錄音
    GPIO_RECORD_BUTTON = 23  # Pin 16 (Active Low, Pull-up required)
    
    # ========== 音訊設定 ==========
    AUDIO_INPUT_CARD = 1  # USB Microphone (Alsa default card 1)
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_FORMAT = 'wav'
    
    # ========== 路徑設定 ==========
    # 資料庫路徑
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'memories.db')
    
    # 資源路徑
    ASSETS_SYSTEM_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'system')
    ASSETS_FONTS_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    
    # ========== 狀態機模式 ==========
    MODE_DAILY = 'daily'      # 每日訪談模式
    MODE_CHAT = 'chat'        # 聊天模式
    MODE_DIARY = 'diary'      # 日記回顧模式
    MODE_REMINDER = 'reminder'  # 提醒模式
    
    @classmethod
    def validate(cls):
        """驗證必要的配置是否存在"""
        errors = []
        if not cls.GEMINI_KEY:
            errors.append('GEMINI_KEY 未設定')
        if not cls.VOICE_CLONE_API_KEY:
            errors.append('VOICE_CLONE_API_KEY 未設定')
        return errors
    
    @classmethod
    def get_hardware_summary(cls):
        """取得硬體配置摘要（用於除錯）"""
        return {
            'OLED': {
                'I2C_Address': hex(cls.OLED_I2C_ADDRESS),
                'SDA': cls.GPIO_SDA,
                'SCL': cls.GPIO_SCL,
                'Resolution': f'{cls.OLED_WIDTH}x{cls.OLED_HEIGHT}'
            },
            'Rotary_Encoder': {
                'CLK': cls.GPIO_ROTARY_CLK,
                'DT': cls.GPIO_ROTARY_DT,
                'SW': cls.GPIO_ROTARY_SW
            },
            'Record_Button': {
                'GPIO': cls.GPIO_RECORD_BUTTON
            }
        }

if __name__ == '__main__':
    # 測試配置載入
    print("=" * 50)
    print("配置載入測試")
    print("=" * 50)
    
    print(f"\nAPI 金鑰狀態:")
    print(f"  GEMINI_KEY: {'已設定' if Config.GEMINI_KEY else '未設定'}")
    print(f"  VOICE_CLONE_API_KEY: {'已設定' if Config.VOICE_CLONE_API_KEY else '未設定'}")
    
    print(f"\n硬體配置摘要:")
    hw_summary = Config.get_hardware_summary()
    for component, pins in hw_summary.items():
        print(f"  {component}:")
        for key, value in pins.items():
            print(f"    {key}: {value}")
    
    print(f"\n路徑設定:")
    print(f"  DB_PATH: {Config.DB_PATH}")
    print(f"  ASSETS_SYSTEM_PATH: {Config.ASSETS_SYSTEM_PATH}")
    
    errors = Config.validate()
    if errors:
        print("\n⚠️  配置錯誤:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ 配置驗證通過！")
