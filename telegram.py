import app
import ffmpeg_streaming
import os
import telebot
import time
import threading
import picamera
import psutil
from ffmpeg_streaming import Formats

api_key = os.getenv('TELE_APIKEY')
print("Starting Baby monitor application")
tb = telebot.TeleBot(api_key)

@tb.message_handler(func=lambda msg: '/help' in msg.text)

@tb.message_handler(func=lambda msg: '/stats' in msg.text)
def stats_handler(message):
    temp = list(psutil.sensors_temperatures()['cpu-thermal'][0])[1]
    cpu = psutil.cpu_percent(interval=1)
    mem = round(psutil.virtual_memory()[1] / 1024 / 1024)
    disk = psutil.disk_usage('/').free / (( 1024.0 ** 3 ))
    
    reply = "CPU temp - %sC\nCPU Usage - %s\nFree RAM - %sMB\nFree Disk space %sGB" %(temp, cpu, mem, disk)
    tb.reply_to(message, reply)
    
@tb.message_handler(func=lambda msg: '/picture' in msg.text)
def picture_handler(message):
    output = "bot_pic-%s.jpg" %(time.time())
    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        camera.capture(output)
        print('Picture taken')
        try:
            with open(output, 'rb') as photo:
                tb.send_photo(message.chat.id, photo)
        except Exception as e:
            tb.reply_to(message, "couldn't send picture\n%s" %(e))
        os.remove(output)

@tb.message_handler(func=lambda msg: '/room' in msg.text)
def room_handler(message):
    # get details of room temperature and reply to user
    tb.reply_to(message, "This will give information about the room")
    
@tb.message_handler(func=lambda msg: '/video' in msg.text)
def video_handler(message):
    # start a video stream
    #tb.reply_to(message, "This will start a video stream and give the link")
    th = threading.Thread(target=app.run)
    th.start()
    
    tb.reply_to(message, "Starting video stream\nGO to https://192.168.0.150:5000/video")


if __name__ == '__main__':
    while True:
        try:
            tb.polling()
            print("Connected to Telegram")
        except KeyboardInterrupt:
            print("EXIT")
            break
        except Exception:
            time.sleep(15)
