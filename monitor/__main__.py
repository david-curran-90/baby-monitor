from . import app
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

# set up some simple logging to ./app.log
log_level = logging.INFO
logging.basicConfig(filename='app.log',
                    filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s',
                    level=log_level)

# set up global variables 
api_key = os.getenv('TELE_APIKEY')
port = "5000"
giturl = "https://github.com/schizoid90/baby-monitor"

# 
logging.info("Starting Baby monitor application")
tb = telebot.TeleBot(api_key)


# enable some modules for one wire use
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# set up a /help route to let the users know how to interact with the bot
@tb.message_handler(func=lambda msg: '/help' in msg.text)
def help_handler(message):
    reply = """
    This bot can control your Raspberry Pi baby monitor.
    View %s for more details.
    /help - show this message
    /status - show stats about the Pi
    /picture - take a picture and send it through telegram
    /stream - start a the streaming server
    /stopstream - stop the streaming server
    /room - information about the room taken from sensors
    """ % (giturl)
    tb.reply_to(message, reply)

# function to give hardware status information
@tb.message_handler(func=lambda msg: '/status' in msg.text)
def stats_handler(message):
    #temp = list(psutil.sensors_temperatures()['cpu-thermal'][0])[1]
    cpu = psutil.cpu_percent(interval=1)
    mem = round(psutil.virtual_memory()[1] / 1024 / 1024)
    disk = psutil.disk_usage('/').free / (( 1024.0 ** 3 ))
    status = "RUNNING"
    
    reply = "%s\nCPU Usage - %s\nFree RAM - %sMB\nFree Disk space %sGB" %(status, cpu, mem, disk)
    tb.reply_to(message, reply)
    
# take a picture and send it as a reply
@tb.message_handler(func=lambda msg: '/picture' in msg.text)
def picture_handler(message):
    output = "bot_pic-%s.jpg" %(time.time())
    with picamera.PiCamera() as camera:
        # set picture details and take picture after warm up
        camera.resolution = (1024, 768)
        camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        camera.capture(output)
        logging.info('Picture taken')
        # try to send picture but send error message if it fails
        try:
            with open(output, 'rb') as photo:
                tb.send_photo(message.chat.id, photo)
        except Exception as e:
            tb.reply_to(message, "couldn't send picture\n%s" %(e))
        finally:
            os.remove(output)

# give information about the room the PI is placed in
@tb.message_handler(func=lambda msg: '/room' in msg.text)
def room_handler(message):
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
    # get lines from the temp sensor file
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(str(e))
    return lines

def get_temp(lines):
    # extract the temperature from the file
    temp_output = lines[1].find('t=')

    if temp_output != -1:
        temp_string = lines[1].strip()[temp_output+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    
# start a flask server serving video
@tb.message_handler(func=lambda msg: '/stream' in msg.text)
def video_handler(message):
    host = get_ip()
    # start a video stream
    th = threading.Thread(target=app.run)
    th.start()
    
    tb.reply_to(message, "Starting stream\nGO to http://%s:%s/video\nOR http://%s:%s/audio" %(host, port, host, port))

# send a POST connection to shutdown flask
@tb.message_handler(func=lambda msg: '/stopstream' in msg.text)
def video_stop_handler(message):
    requests.post("http://%s:%s/shutdown" %(get_ip(), port,))
    tb.reply_to(message, "Stopping stream")
    
# get the device IP
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
