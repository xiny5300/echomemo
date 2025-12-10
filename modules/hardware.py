"""
檔案標準 (Standard):
本檔案負責所有 GPIO 硬體控制，包括旋轉編碼器、按鈕的初始化與事件監聽。
提供非同步事件處理介面，供主程式狀態機使用。
輸入：GPIO 事件（按鈕按下、編碼器旋轉）
輸出：非同步事件回呼

執行方式 (Execution):
- 被 main.py 匯入並初始化
- 獨立測試：python -m modules.hardware (需要實際硬體連接)

相依性 (Dependencies):
- gpiozero: GPIO 控制函式庫
- asyncio: 非同步事件處理
- config: 系統配置（GPIO 腳位）
"""

import asyncio
from gpiozero import RotaryEncoder, Button
from typing import Callable, Optional
import config

class Hardware:
    """硬體控制類別"""
    
    def __init__(self):
        """初始化所有硬體元件"""
        # 旋轉編碼器（用於模式切換）
        self.rotary_encoder = RotaryEncoder(
            pin1=config.Config.GPIO_ROTARY_CLK,
            pin2=config.Config.GPIO_ROTARY_DT,
            pull_up=True
        )
        
        # 編碼器按鈕（旋轉編碼器上的按鈕）
        self.rotary_button = Button(
            config.Config.GPIO_ROTARY_SW,
            pull_up=True
        )
        
        # 錄音按鈕
        self.record_button = Button(
            config.Config.GPIO_RECORD_BUTTON,
            pull_up=True
        )
        
        # 事件回呼函式
        self.on_rotary_rotate: Optional[Callable[[int], None]] = None  # delta: -1 或 1
        self.on_rotary_press: Optional[Callable[[], None]] = None
        self.on_record_press: Optional[Callable[[], None]] = None
        self.on_record_release: Optional[Callable[[], None]] = None
        
        # 編碼器位置追蹤
        self.rotary_position = 0
        self._last_rotary_value = 0
        
        # 設定事件處理
        self._setup_events()
    
    def _setup_events(self):
        """設定硬體事件處理"""
        # 旋轉編碼器旋轉事件
        self.rotary_encoder.when_rotated = self._on_rotary_rotated
        
        # 編碼器按鈕事件
        self.rotary_button.when_pressed = self._on_rotary_button_pressed
        
        # 錄音按鈕事件（按住/放開）
        self.record_button.when_pressed = self._on_record_button_pressed
        self.record_button.when_released = self._on_record_button_released
    
    def _on_rotary_rotated(self):
        """處理旋轉編碼器旋轉"""
        current_value = self.rotary_encoder.value
        delta = int(current_value - self._last_rotary_value)
        self._last_rotary_value = current_value
        
        if delta != 0:
            self.rotary_position += delta
            if self.on_rotary_rotate:
                # 在事件循環中執行回呼
                asyncio.create_task(self._async_callback(
                    self.on_rotary_rotate, delta
                ))
    
    def _on_rotary_button_pressed(self):
        """處理編碼器按鈕按下"""
        if self.on_rotary_press:
            asyncio.create_task(self._async_callback(
                self.on_rotary_press
            ))
    
    def _on_record_button_pressed(self):
        """處理錄音按鈕按下（開始錄音）"""
        if self.on_record_press:
            asyncio.create_task(self._async_callback(
                self.on_record_press
            ))
    
    def _on_record_button_released(self):
        """處理錄音按鈕放開（停止錄音）"""
        if self.on_record_release:
            asyncio.create_task(self._async_callback(
                self.on_record_release
            ))
    
    async def _async_callback(self, callback: Callable, *args, **kwargs):
        """非同步執行回呼函式"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)
    
    def get_rotary_position(self) -> int:
        """取得旋轉編碼器當前位置"""
        return self.rotary_position
    
    def reset_rotary_position(self):
        """重置旋轉編碼器位置"""
        self.rotary_position = 0
        self._last_rotary_value = self.rotary_encoder.value
    
    def cleanup(self):
        """清理資源"""
        self.rotary_encoder.close()
        self.rotary_button.close()
        self.record_button.close()

if __name__ == '__main__':
    # 測試硬體（需要實際連接硬體）
    print("硬體測試模式")
    print("請確保硬體已正確連接")
    print("按 Ctrl+C 結束測試")
    
    hw = Hardware()
    
    # 設定測試回呼
    def on_rotate(delta):
        print(f"編碼器旋轉: {delta}, 位置: {hw.get_rotary_position()}")
    
    def on_rotary_press():
        print("編碼器按鈕按下")
    
    def on_record_press():
        print("錄音按鈕按下（開始錄音）")
    
    def on_record_release():
        print("錄音按鈕放開（停止錄音）")
    
    hw.on_rotary_rotate = on_rotate
    hw.on_rotary_press = on_rotary_press
    hw.on_record_press = on_record_press
    hw.on_record_release = on_record_release
    
    try:
        # 保持程式運行
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n結束測試")
        hw.cleanup()

