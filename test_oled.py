import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# 1. 設定螢幕參數 (128x64像素)
WIDTH = 128
HEIGHT = 64
BORDER = 5

# 2. 設定 I2C 連線 (這就是你接的那兩條線 SDA/SCL)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)

# 3. 清除螢幕 (變全黑)
oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# 5. 畫一個白色的矩形框框
draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=0)

# 6. 載入預設字體並寫字
# 若沒有字體檔，會使用非常簡陋的預設點陣字
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except IOError:
    font = ImageFont.load_default()
    font_big = ImageFont.load_default()

# 寫上文字 (座標 x, y)
draw.text((10, 10), "Hello!", font=font_big, fill=255)
draw.text((10, 35), "Echomemo OK", font=font, fill=255)

# 7. 將畫布推送到螢幕顯示
oled.image(image)
oled.show()

print("螢幕應該亮起來了！")
