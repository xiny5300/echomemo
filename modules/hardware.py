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
- gpiozero: GPIO 控制函式庫 (Raspberry Pi 5 相容)
- asyncio: 非同步事件處理
- config: 系統配置（GPIO 腳位）

硬體規格 (根據 spec.md):
- 旋轉編碼器 (EC11):
  - CLK: GPIO 22 (Pin 15)
  - DT: GPIO 27 (Pin 13)
  - SW: GPIO 17 (Pin 11) - Active Low, Pull-up
- 錄音按鈕:
  - GPIO 23 (Pin 16) - Active Low, Pull-up
"""

import asyncio
from gpiozero import RotaryEncoder, Button
from typing import Callable, Optional
import threading
import queue
import config

class Hardware:
    """硬體控制類別
    
    管理所有 GPIO 硬體元件：
    - EC11 旋轉編碼器（模式切換）
    - 獨立錄音按鈕
    """
    
    def __init__(self):
        """初始化所有硬體元件
        
        根據 config.py 中的 GPIO 腳位設定初始化：
        - 旋轉編碼器：CLK (GPIO 22), DT (GPIO 27), SW (GPIO 17)
        - 錄音按鈕：GPIO 23
        """
        # 旋轉編碼器（用於模式切換）
        # 根據 spec.md: EC11 旋轉編碼器
        # CLK: GPIO 22 (Pin 15), DT: GPIO 27 (Pin 13)
        # gpiozero.RotaryEncoder 使用參數 a 和 b，不是 pin1 和 pin2
        self.rotary_encoder = RotaryEncoder(
            a=config.Config.GPIO_ROTARY_CLK,  # GPIO 22 (CLK)
            b=config.Config.GPIO_ROTARY_DT,   # GPIO 27 (DT)
            bounce_time=0.01  # 防彈跳時間（毫秒）
        )
        
        # 編碼器按鈕（旋轉編碼器上的按鈕）
        # SW: GPIO 17 (Pin 11) - Active Low, Pull-up required
        self.rotary_button = Button(
            config.Config.GPIO_ROTARY_SW,  # GPIO 17
            pull_up=True
        )
        
        # 錄音按鈕（獨立按鈕）
        # GPIO 23 (Pin 16) - Active Low, Pull-up required
        # 邏輯：按住 = 錄音，放開 = 停止錄音
        self.record_button = Button(
            config.Config.GPIO_RECORD_BUTTON,  # GPIO 23
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
        
        # 事件佇列（用於執行緒安全的事件處理）
        self._event_queue = queue.Queue()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 設定事件處理
        self._setup_events()
    
    def _setup_events(self):
        """設定硬體事件處理
        
        將硬體事件綁定到對應的處理函式，並透過 asyncio 執行回呼。
        """
        # 旋轉編碼器旋轉事件
        self.rotary_encoder.when_rotated = self._on_rotary_rotated
        
        # 編碼器按鈕事件（按下）
        self.rotary_button.when_pressed = self._on_rotary_button_pressed
        
        # 錄音按鈕事件（按住/放開）
        # 根據 spec.md: 按住 = 錄音，放開 = 停止錄音
        self.record_button.when_pressed = self._on_record_button_pressed
        self.record_button.when_released = self._on_record_button_released
    
    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """設定事件循環（由主程式呼叫）
        
        Args:
            loop: asyncio 事件循環
        """
        self._event_loop = loop
    
    def _on_rotary_rotated(self):
        """處理旋轉編碼器旋轉事件
        
        計算旋轉增量（delta），更新位置，並觸發回呼。
        delta > 0: 順時針旋轉
        delta < 0: 逆時針旋轉
        
        注意：此方法在背景執行緒中執行，需要透過佇列傳遞事件。
        """
        current_value = self.rotary_encoder.value
        delta = int(current_value - self._last_rotary_value)
        self._last_rotary_value = current_value
        
        if delta != 0:
            self.rotary_position += delta
            if self.on_rotary_rotate:
                # 將事件放入佇列（執行緒安全）
                self._event_queue.put(('rotate', self.on_rotary_rotate, delta))
    
    def _on_rotary_button_pressed(self):
        """處理編碼器按鈕按下事件
        
        當旋轉編碼器上的按鈕被按下時觸發（用於確認選擇）。
        注意：此方法在背景執行緒中執行。
        """
        if self.on_rotary_press:
            self._event_queue.put(('press', self.on_rotary_press, None))
    
    def _on_record_button_pressed(self):
        """處理錄音按鈕按下事件（開始錄音）
        
        根據 spec.md: 按住按鈕 = 開始錄音
        注意：此方法在背景執行緒中執行。
        """
        if self.on_record_press:
            self._event_queue.put(('record_press', self.on_record_press, None))
    
    def _on_record_button_released(self):
        """處理錄音按鈕放開事件（停止錄音）
        
        根據 spec.md: 放開按鈕 = 停止錄音
        注意：此方法在背景執行緒中執行。
        """
        if self.on_record_release:
            self._event_queue.put(('record_release', self.on_record_release, None))
    
    async def process_events(self):
        """處理事件佇列中的事件（應在主事件循環中定期呼叫）
        
        此方法會從佇列中取出事件並執行回呼。
        """
        while not self._event_queue.empty():
            try:
                event_type, callback, arg = self._event_queue.get_nowait()
                
                if event_type == 'rotate':
                    # 旋轉事件，傳遞 delta 參數
                    if asyncio.iscoroutinefunction(callback):
                        await callback(arg)
                    else:
                        callback(arg)
                else:
                    # 按鈕事件，無參數
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
            except queue.Empty:
                break
            except Exception as e:
                print(f"處理事件時發生錯誤: {e}")
    
    def get_rotary_position(self) -> int:
        """取得旋轉編碼器當前位置
        
        Returns:
            當前位置（整數，可為負數）
        """
        return self.rotary_position
    
    def reset_rotary_position(self):
        """重置旋轉編碼器位置
        
        將位置計數器歸零，用於模式切換後的初始化。
        """
        self.rotary_position = 0
        self._last_rotary_value = self.rotary_encoder.value
    
    def cleanup(self):
        """清理資源
        
        關閉所有 GPIO 資源，應在程式結束時呼叫。
        """
        try:
            self.rotary_encoder.close()
        except:
            pass
        try:
            self.rotary_button.close()
        except:
            pass
        try:
            self.record_button.close()
        except:
            pass

if __name__ == '__main__':
    # 測試硬體（需要實際連接硬體）
    print("=" * 50)
    print("硬體測試模式")
    print("=" * 50)
    print("\n硬體配置:")
    print(f"  旋轉編碼器:")
    print(f"    CLK: GPIO {config.Config.GPIO_ROTARY_CLK} (Pin 15)")
    print(f"    DT:  GPIO {config.Config.GPIO_ROTARY_DT} (Pin 13)")
    print(f"    SW:  GPIO {config.Config.GPIO_ROTARY_SW} (Pin 11)")
    print(f"  錄音按鈕:")
    print(f"    GPIO {config.Config.GPIO_RECORD_BUTTON} (Pin 16)")
    print("\n請確保硬體已正確連接")
    print("按 Ctrl+C 結束測試\n")
    
    async def test_main():
        hw = Hardware()
        
        # 設定事件循環
        hw.set_event_loop(asyncio.get_event_loop())
        
        # 設定測試回呼
        def on_rotate(delta):
            direction = "順時針" if delta > 0 else "逆時針"
            print(f"編碼器旋轉: {direction} (delta={delta}), 位置: {hw.get_rotary_position()}")
        
        def on_rotary_press():
            print("編碼器按鈕按下 (確認選擇)")
        
        def on_record_press():
            print("錄音按鈕按下 (開始錄音)")
        
        def on_record_release():
            print("錄音按鈕放開 (停止錄音)")
        
        hw.on_rotary_rotate = on_rotate
        hw.on_rotary_press = on_rotary_press
        hw.on_record_press = on_record_press
        hw.on_record_release = on_record_release
        
        try:
            # 主循環：處理事件
            while True:
                await hw.process_events()
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n結束測試")
            hw.cleanup()
            print("硬體資源已清理")
    
    try:
        asyncio.run(test_main())
    except KeyboardInterrupt:
        print("\n測試結束")
