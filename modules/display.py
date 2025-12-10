"""
檔案標準 (Standard):
本檔案負責 OLED 顯示器的控制，提供文字顯示、清屏、多行顯示等功能。
支援中文字型顯示（需提供字型檔）。
輸入：文字內容、顯示模式
輸出：OLED 螢幕顯示

執行方式 (Execution):
- 被 main.py 呼叫以更新顯示內容
- 獨立測試：python -m modules.display (會顯示測試畫面)

相依性 (Dependencies):
- luma.oled: OLED 顯示器驅動
- luma.core: 核心顯示功能
- PIL (Pillow): 圖像處理
- config: 系統配置（OLED 設定）
"""

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import os
import config

class Display:
    """OLED 顯示器控制類別"""
    
    def __init__(self):
        """初始化 OLED 顯示器"""
        # I2C 介面
        serial = i2c(
            port=1,
            address=config.Config.OLED_I2C_ADDRESS
        )
        
        # SSD1306 裝置
        self.device = ssd1306(
            serial,
            width=config.Config.OLED_WIDTH,
            height=config.Config.OLED_HEIGHT
        )
        
        # 載入字型
        self._load_fonts()
    
    def _load_fonts(self):
        """載入字型檔"""
        # 預設字型
        try:
            self.font_default = ImageFont.load_default()
        except:
            self.font_default = None
        
        # 中文字型（如果存在）
        font_path = os.path.join(config.Config.ASSETS_FONTS_PATH, 'default.ttf')
        if os.path.exists(font_path):
            try:
                self.font_chinese = ImageFont.truetype(font_path, 12)
            except:
                self.font_chinese = self.font_default
        else:
            self.font_chinese = self.font_default
    
    def clear(self):
        """清空螢幕"""
        with canvas(self.device) as draw:
            draw.rectangle(
                (0, 0, config.Config.OLED_WIDTH, config.Config.OLED_HEIGHT),
                outline=0,
                fill=0
            )
    
    def show_text(self, text: str, x: int = 0, y: int = 0, font=None):
        """
        顯示文字
        
        Args:
            text: 要顯示的文字
            x: X 座標
            y: Y 座標
            font: 字型（預設使用中文字型）
        """
        if font is None:
            font = self.font_chinese or self.font_default
        
        with canvas(self.device) as draw:
            draw.text((x, y), text, font=font, fill=255)
    
    def show_multiline(self, lines: list, spacing: int = 12):
        """
        顯示多行文字
        
        Args:
            lines: 文字行列表
            spacing: 行間距
        """
        with canvas(self.device) as draw:
            y = 0
            for line in lines:
                if y >= config.Config.OLED_HEIGHT:
                    break
                draw.text((0, y), line, font=self.font_chinese or self.font_default, fill=255)
                y += spacing
    
    def show_centered(self, text: str, y: int = None):
        """
        顯示置中文字
        
        Args:
            text: 要顯示的文字
            y: Y 座標（預設垂直置中）
        """
        if y is None:
            y = (config.Config.OLED_HEIGHT - 12) // 2
        
        # 計算文字寬度（簡單估算）
        text_width = len(text) * 6  # 每個字元約 6 像素
        x = (config.Config.OLED_WIDTH - text_width) // 2
        
        self.show_text(text, max(0, x), y)
    
    def show_mode(self, mode: str, status: str = ""):
        """
        顯示模式與狀態
        
        Args:
            mode: 模式名稱
            status: 狀態文字
        """
        lines = [f"模式: {mode}"]
        if status:
            lines.append(status)
        self.show_multiline(lines)
    
    def show_progress(self, text: str, progress: float):
        """
        顯示進度（文字 + 進度條）
        
        Args:
            text: 說明文字
            progress: 進度 (0.0 - 1.0)
        """
        with canvas(self.device) as draw:
            # 顯示文字
            draw.text((0, 0), text, font=self.font_chinese or self.font_default, fill=255)
            
            # 進度條
            bar_width = config.Config.OLED_WIDTH - 4
            bar_height = 8
            bar_x = 2
            bar_y = config.Config.OLED_HEIGHT - bar_height - 2
            
            # 背景
            draw.rectangle(
                (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
                outline=255,
                fill=0
            )
            
            # 進度
            progress_width = int(bar_width * progress)
            if progress_width > 0:
                draw.rectangle(
                    (bar_x + 1, bar_y + 1, bar_x + progress_width - 1, bar_y + bar_height - 1),
                    fill=255
                )

if __name__ == '__main__':
    # 測試顯示功能
    print("OLED 顯示測試")
    
    try:
        display = Display()
        
        # 測試 1: 清屏
        print("測試 1: 清屏")
        display.clear()
        import time
        time.sleep(1)
        
        # 測試 2: 顯示文字
        print("測試 2: 顯示文字")
        display.show_text("Hello World", 0, 0)
        time.sleep(2)
        
        # 測試 3: 顯示置中文字
        print("測試 3: 顯示置中文字")
        display.show_centered("置中文字")
        time.sleep(2)
        
        # 測試 4: 多行顯示
        print("測試 4: 多行顯示")
        display.show_multiline(["第一行", "第二行", "第三行"])
        time.sleep(2)
        
        # 測試 5: 模式顯示
        print("測試 5: 模式顯示")
        display.show_mode("聊天模式", "等待錄音...")
        time.sleep(2)
        
        # 測試 6: 進度條
        print("測試 6: 進度條")
        for i in range(0, 101, 10):
            display.show_progress(f"進度: {i}%", i / 100.0)
            time.sleep(0.3)
        
        print("測試完成")
        
    except Exception as e:
        print(f"測試失敗: {e}")
        print("請確認 OLED 顯示器已正確連接")

