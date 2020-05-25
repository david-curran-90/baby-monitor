import app
import ffmpeg_streaming
import os
import telebot
import time
import threading
import logging
import picamera
import psutil
import requests
import socket
from ffmpeg_streaming import Formats

log_level = logging.INFO
logging.basicConfig(filename='app.log',
                    filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=log_level)

api_key = os.getenv('TELE_APIKEY')
logging.info("Starting Baby monitor application")
tb = telebot.TeleBot(api_key)
port = "5000"
giturl = "https://github.com/schizoid90/baby-monitor"

# enable some modules
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

@tb.message_handler(func=lambda msg: '/help' in msg.text)
def help_handler(message):
    reply = """
    This bot can control your Raspberry Pi baby monitor.
    View %s for more details.
    /help - show this message
    /status - show stats about the Pi
    /picture - take a picture and send it through telegram
    /video - start a video stream
    /stopvideo - stop the video stream
    /room - information about the room taken from sensors
    """ % (giturl)
    tb.reply_to(message, reply)

@tb.message_handler(func=lambda msg: '/status' in msg.text)
def stats_handler(message):
    #temp = list(psutil.sensors_temperatures()['cpu-thermal'][0])[1]
    cpu = psutil.cpu_percent(interval=1)
    mem = round(psutil.virtual_memory()[1] / 1024 / 1024)
    disk = psutil.disk_usage('/').free / (( 1024.0 ** 3 ))
    status = "RUNNING"
    
    reply = "%s\nCPU Usage - %s\nFree RAM - %sMB\nFree Disk space %sGB" %(status, cpu, mem, disk)
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
        logging.info('Picture taken')
        try:
            with open(output, 'rb') as photo:
                tb.send_photo(message.chat.id, photo)
        except Exception as e:
            tb.reply_to(message, "couldn't send picture\n%s" %(e))
        os.remove(output)

@tb.message_handler(func=lambda msg: '/room' in msg.text)
def room_handler(message):
    # get details of room temperature and reply to user
    temp_sensor = get_temp_sensor_file()
    if temp_sensor == "error":
        tb.reply_to(message, "Could not find any temperature sensor")

    # read the temp_sensor file until it succeeds
    temp_read = 'NO'
    while temp_read != 'YES':
        time.sleep(0.2)
        temp_sensor_info = get_temp_info(temp_sensor)
        temp_read = temp_sensor_info[0].strip()[-3:]
    
    temp = get_temp(temp_sensor_info)
    tb.reply_to(message, "Room temperature is %sC" %(temp))
    
def get_temp_sensor_file():
    # try to get the location of the one pin file
    # should be in in /sys/bus/w1/devices/28-*/w1_slave
    w1dir = "/sys/bus/w1/devices"
    folders = os.listdir(w1dir)
    prefix = "28-"
    devices = [device for device in folders if device.startswith(prefix)]
    if devices:
        logging.info("Found %s one wire devices, using %s for temperature" %(len(devices), devices[0],))
        dev = "%s/%s/w1_slave" %(w1dir, devices[0],)
        return dev
    else:
        return "error"

def get_temp_info(file):
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(str(e))
    return lines

def get_temp(lines):
    temp_output = lines[1].find('t=')

    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    
@tb.message_handler(func=lambda msg: '/video' in msg.text)
def video_handler(message):
    host = get_ip()
    # start a video stream
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
    logging.info("Connecting to Telegram")
    while True:
        try:
            tb.polling()
        except KeyboardInterrupt:
            logging.info("EXIT")
            break
        except Exception:
            time.sleep(15)
