import app
import ffmpeg_streaming
import os
import telebot
import time
import threading
import picamera
import psutil
import requests
import socket
from ffmpeg_streaming import Formats

api_key = os.getenv('TELE_APIKEY')
print("Starting Baby monitor application")
tb = telebot.TeleBot(api_key)
port = "5000"
giturl = "https://github.com/schizoid90/baby-monitor"

@tb.message_handler(func=lambda msg: '/help' in msg.text)
def help_handler(message):
    reply = """
    This bot can control your Raspberry Pi baby monitor.
    View %s for more details.
    /help - show this message
    /stats - show stats about the Pi
    /picture - take a picture and send it through telegram
    /video - start a video stream
    /stopvideo - stop the video stream
    /room - information about the room taken from sensors
    """ % (giturl)
    tb.reply_to(message, reply)

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
    host = get_ip()
    # start a video stream
    #tb.reply_to(message, "This will start a video stream and give the link")
    th = threading.Thread(target=app.run)
    th.start()
    
    tb.reply_to(message, "Starting video stream\nGO to http://%s:%s/video" %(host, port,))

@tb.message_handler(func=lambda msg: '/stopvideo' in msg.text)
def video_stop_handler(message):
    host = get_ip()
    requests.post("http://%s:%s/shutdown" %(host, port,))
    tb.reply_to(message, "Stopping video stream")
    
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    print("Connecting to Telegram")
    while True:
        try:
            tb.polling()
        except KeyboardInterrupt:
            print("EXIT")
            break
        except Exception:
            time.sleep(15)
