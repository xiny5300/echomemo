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
    """系統配置類別"""
    
    # Google Gemini API
    GEMINI_KEY = os.getenv('GEMINI_KEY', '')
    
    # 語音克隆 API (aiclonevoicefree.com)
    VOICE_CLONE_API_KEY = os.getenv('VOICE_CLONE_API_KEY', '')
    VOICE_CLONE_UPLOAD_URL = 'http://8.148.211.142:8080/api/upload/audio'
    VOICE_CLONE_SYNC_URL = 'https://aivoiceclonefree.com/api/instant/clone-sync'
    
    # 語音 ID (用於區分系統音和分身音)
    # 這些需要先上傳對應的語音樣本後獲得
    SYSTEM_VOICE_ID = os.getenv('SYSTEM_VOICE_ID', '')  # 官方導引音
    PERSONA_VOICE_ID = os.getenv('PERSONA_VOICE_ID', '')  # 數位分身音
    
    # 硬體設定
    OLED_I2C_ADDRESS = 0x3C
    OLED_WIDTH = 128
    OLED_HEIGHT = 64
    
    # GPIO 腳位
    GPIO_SDA = 2
    GPIO_SCL = 3
    GPIO_ROTARY_CLK = 5
    GPIO_ROTARY_DT = 6
    GPIO_ROTARY_SW = 13
    GPIO_RECORD_BUTTON = 17
    
    # 音訊設定
    AUDIO_INPUT_CARD = 1  # USB Microphone (Alsa default card 1)
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_FORMAT = 'wav'
    
    # 資料庫路徑
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'memories.db')
    
    # 資源路徑
    ASSETS_SYSTEM_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'system')
    ASSETS_FONTS_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    
    # 狀態機模式
    MODE_DAILY = 'daily'
    MODE_CHAT = 'chat'
    MODE_DIARY = 'diary'
    MODE_REMINDER = 'reminder'
    
    @classmethod
    def validate(cls):
        """驗證必要的配置是否存在"""
        errors = []
        if not cls.GEMINI_KEY:
            errors.append('GEMINI_KEY 未設定')
        if not cls.VOICE_CLONE_API_KEY:
            errors.append('VOICE_CLONE_API_KEY 未設定')
        return errors

if __name__ == '__main__':
    # 測試配置載入
    print("配置載入測試:")
    print(f"GEMINI_KEY: {'已設定' if Config.GEMINI_KEY else '未設定'}")
    print(f"VOICE_CLONE_API_KEY: {'已設定' if Config.VOICE_CLONE_API_KEY else '未設定'}")
    print(f"DB_PATH: {Config.DB_PATH}")
    print(f"ASSETS_SYSTEM_PATH: {Config.ASSETS_SYSTEM_PATH}")
    
    errors = Config.validate()
    if errors:
        print("\n錯誤:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n配置驗證通過！")

