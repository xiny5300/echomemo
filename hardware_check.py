"""
硬體檢查腳本：用於測試所有硬體元件是否正常運作

執行方式：
python hardware_check.py

功能：
- 測試 OLED 顯示器
- 測試旋轉編碼器（旋轉和按鈕）
- 測試錄音按鈕
- 在 OLED 上顯示測試狀態
"""

import board
import busio
import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import config

# --- 從 config.py 讀取 GPIO 腳位設定 ---
# 根據 spec.md: 已驗證的硬體接線
PIN_SW = config.Config.GPIO_ROTARY_SW      # GPIO 17 (Pin 11) - 編碼器按鈕
PIN_DT = config.Config.GPIO_ROTARY_DT      # GPIO 27 (Pin 13) - 編碼器方向
PIN_CLK = config.Config.GPIO_ROTARY_CLK    # GPIO 22 (Pin 15) - 編碼器時鐘
PIN_RECORD = config.Config.GPIO_RECORD_BUTTON  # GPIO 23 (Pin 16) - 獨立錄音按鈕

# --- 初始化 GPIO ---
GPIO.setmode(GPIO.BCM)
# 設定所有按鈕為輸入，並開啟上拉電阻 (平時為 1，按下接地變 0)
# 根據 spec.md: Active Low, Pull-up required
GPIO.setup(PIN_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_RECORD, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- 初始化 OLED ---
# 根據 spec.md: 0.96" OLED (SSD1306, I2C Address: 0x3C)
i2c = board.I2C()
# 嘗試連接螢幕
try:
    oled = adafruit_ssd1306.SSD1306_I2C(
        config.Config.OLED_WIDTH, 
        config.Config.OLED_HEIGHT, 
        i2c, 
        addr=config.Config.OLED_I2C_ADDRESS
    )
    oled.fill(0)
    oled.show()
    oled_ok = True
    print(f"✓ OLED 已連接 (I2C Address: {hex(config.Config.OLED_I2C_ADDRESS)})")
except Exception as e:
    print(f"⚠️ 警告：找不到 OLED 螢幕，請檢查 I2C 接線！")
    print(f"   錯誤: {e}")
    oled_ok = False

# 準備繪圖工具
if oled_ok:
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()

def update_display(status_text):
    """更新 OLED 畫面"""
    if not oled_ok: 
        return
    
    # 清空畫布 (畫黑色矩形蓋掉舊的)
    draw.rectangle((0, 0, config.Config.OLED_WIDTH, config.Config.OLED_HEIGHT), outline=0, fill=0)
    
    # 寫字
    draw.text((5, 5), "Hardware Check", font=font, fill=255)
    draw.text((5, 25), status_text, font=font, fill=255)
    
    # 顯示
    oled.image(image)
    oled.show()

# --- 主迴圈 ---
print("=" * 50)
print("全硬體測試模式")
print("=" * 50)
print("\n硬體配置:")
print(f"  旋轉編碼器 (EC11):")
print(f"    CLK: GPIO {PIN_CLK} (Pin 15)")
print(f"    DT:  GPIO {PIN_DT} (Pin 13)")
print(f"    SW:  GPIO {PIN_SW} (Pin 11)")
print(f"  錄音按鈕:")
print(f"    GPIO {PIN_RECORD} (Pin 16)")
print(f"  OLED:")
print(f"    I2C Address: {hex(config.Config.OLED_I2C_ADDRESS)}")
print("\n測試項目:")
print("1. 旋轉編碼器（左右旋轉）")
print("2. 按下編碼器按鈕 (SW)")
print("3. 按下錄音按鈕 (GPIO 23)")
print("\n(按 Ctrl+C 離開)\n")

update_display("Ready...")

last_clk = GPIO.input(PIN_CLK)
rotation_count = 0

try:
    while True:
        # 讀取狀態
        clk_state = GPIO.input(PIN_CLK)
        dt_state = GPIO.input(PIN_DT)
        sw_state = GPIO.input(PIN_SW)      # 編碼器按鈕
        rec_state = GPIO.input(PIN_RECORD) # 錄音按鈕

        # 檢測旋轉（根據 spec.md: EC11 旋轉編碼器）
        if clk_state != last_clk and clk_state == 0:
            if dt_state != clk_state:
                rotation_count += 1
                msg = f"Right (CW) -> {rotation_count}"
                print(msg)
                update_display(msg)
            else:
                rotation_count -= 1
                msg = f"<- Left (CCW) {rotation_count}"
                print(msg)
                update_display(msg)
        
        # 檢測編碼器按鈕 (SW) - 根據 spec.md: Active Low
        if sw_state == 0:
            msg = "Encoder Click!"
            print(msg)
            update_display(msg)
            time.sleep(0.2)  # 防連點

        # 檢測錄音按鈕 (Record) - 根據 spec.md: Active Low
        if rec_state == 0:
            msg = "REC Button ON!"
            print(msg)
            update_display(msg)
            time.sleep(0.2)

        last_clk = clk_state
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n測試結束")
    GPIO.cleanup()
    if oled_ok:
        oled.fill(0)
        oled.show()
    print("硬體資源已清理")
