from picamera2 import Picamera2, Preview
from libcamera import controls
import time
from PIL import Image, ImageDraw, ImageFont
import pyocr
import re

# for OLED
import board
import digitalio
import adafruit_ssd1306
import datetime


def format_timedelta(timedelta):
    total_sec = timedelta.total_seconds()
    # hours
    hours = total_sec // 3600
    # remaining seconds
    remain = total_sec - (hours * 3600)
    # minutes
    minutes = remain // 60
    # remaining seconds
    # seconds = remain - (minutes * 60)
    # total time
    # return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    return '{:02}:{:02}'.format(int(hours), int(minutes))


def main():
    # GPIOの初期設定
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    # GPIO18を入力端子設定
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # OLED
    # Setting some variables for our reset pin etc.
    RESET_PIN = digitalio.DigitalInOut(board.D4)
    i2c = board.I2C()  # uses board.SCL and board.SDA
    oled = adafruit_ssd1306.SSD1306_I2C(
        128, 64, i2c, addr=0x3C, reset=RESET_PIN)

    # Clear display.
    oled.fill(0)
    oled.show()

    # Load a font in 2 different sizes.
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    font2 = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    status = 'READY'

    while True:
        # get datetime
        dt_now = datetime.datetime.now()
        print(dt_now)
        nowtime = dt_now.strftime('%Y-%m-%d %H:%M:%S')

        # スイッチ状態取得
        sw_status = GPIO.input(18)

        # 画面出力
        if sw_status == 0:
            print('Switch ON!')
            break
        else:
            # Create blank image for drawing.
            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)

            # Draw the text
            draw.text((0, 0), status, font=font, fill=255)
            # draw.text((0, 30), datemsg, font=font2, fill=255)
            draw.text((0, 46), nowtime, font=font2, fill=255)

            # Display image
            oled.image(image)
            oled.show()

            time.sleep(0.5)

    # Capture
    picam2 = Picamera2()
    picam2.start(show_preview=False)
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    time.sleep(5)
    picam2.capture_file("test.jpg")

    # Open, resize, and convert image to Black and White
    image = (
        Image.open('test.jpg')
        .resize((oled.width, oled.height), Image.BICUBIC)
        .convert("1")
    )

    # Display the converted image
    oled.image(image)
    oled.show()

    time.sleep(1)

    # OCR
    tools = pyocr.get_available_tools()
    tool = tools[0]

    img = Image.open("test.jpg")

    builder = pyocr.builders.TextBuilder(tesseract_layout=6)
    text = tool.image_to_string(img, lang="jpn", builder=builder)

    print('---- READ OCR ---')
    print(text)

    # Get receipt date and time
    pattern = r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}'
    res = re.findall(pattern, text)
    # res = ['2023-02-20 22:40']

    if not res:
        print('ERROR')
        datemsg = 'NULL'
        status = 'ERROR'
    else:
        print(res)
        datemsg = res[0]+':00'
        datemsg2 = datemsg.replace('/', '-')
        dt_receipt = datetime.datetime.fromisoformat(datemsg2)
        td = dt_now - dt_receipt
        print(td)
        print(format_timedelta(td))
        status = format_timedelta(td)

    # for debug
    print('---- for debug ---')
    print(status)
    print(datemsg)
    print(nowtime)

    # Clear display.
    oled.fill(0)
    oled.show()

    # Create blank image for drawing.
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)

    # Draw the text
    draw.text((0, 0), status, font=font, fill=255)
    draw.text((0, 30), datemsg, font=font2, fill=255)
    draw.text((0, 46), nowtime, font=font2, fill=255)

    # Display image
    oled.image(image)
    oled.show()

    time.sleep(10)
    
    # Program end
    print('END')


if __name__ == "__main__":
    main()