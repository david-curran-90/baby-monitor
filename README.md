[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/schizoid90/baby-monitor) 

# Baby Monitor

A baby monitor written in Python that is controlled via telegram. 

Features:
* telegram commands
* take a picture and send it to a chat
* stream video

Requirements:
* Raspberry Pi (Developed on a [Pi 4 Model B](https://thepihut.com/collections/raspberry-pi/products/raspberry-pi-4-model-b))
* Pi Camera (Developed with a Pi [Zero camera](https://thepihut.com/products/zerocam-camera-for-raspberry-pi-zero) with [relevent adapter](https://thepihut.com/products/raspberry-pi-zero-camera-adapter))
* Temperature sensor (Developed with [DS18B20+ One Wire Digital Temperature Sensor](https://thepihut.com/products/ds18b20-one-wire-digital-temperature-sensor))
* Jump cables

## Dependencies

```
python3 -m pip install -r requirements.txt
sudo apt install libatlas-base-dev libjasper-dev libqtgui4 libqt4-test python3-pyqt5 python3-opencv
```

## Usage

* start

```shell
export TELE_APIKEY={{your_API_KEY}}
python3 telegram.py
```

This will start a connection to your telegram bot and start listening for commands

type `/help` in your chat screen to see a list of commands

## Video

Video streaming is served via flask and shows a stream of *jpg* images on port 5000

Start by sending `/video` and stop with `/stopvideo`. It is also possible to send a POST request to the flask server running on port *5000*

```shell
curl -X POST http://192.168.0.150:5000/shutdown
```

## Picture

Yuo can instruct the Pi to take a pciture and send it to that chat with `/picture`. This will also delete the picture sending so there's no need to worry about storage.