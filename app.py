#wait for button release
#play message with beep at the end
#start recording right after the beep
#wait until the button is pressed
#stop recording
#save recording with timestamp
#goto beginning
import time
import signal
import sys
import RPi.GPIO as GPIO
from play_sounds import play_file
import pyaudio
import wave
from atomic import AtomicLong
import itertools
import numpy as NP
import datetime
import os
import flask

SAMPLE_RATE = 48000
CHUNK = 1024
sample_format = pyaudio.paInt16
channels = 1

p = pyaudio.PyAudio()

currentFrames = []

def saveRecordingAs(name):
    global currentFrames
    flatData = list(itertools.chain(currentFrames))
    print(len(flatData))
    arr = NP.array(flatData)
    with wave.open(name, 'wb') as wa:
        wa.setnchannels(1)
        wa.setsampwidth(2)
        wa.setframerate(SAMPLE_RATE)
        wa.writeframes(arr)

    currentFrames = []

def playSoundAsync(path):
    os.system("aplay message.wav &")

def stopRecording(stream):
    stream.stop_stream()
    stream.close()
    stream = None

def startRecording():
    global p
    playSoundAsync("message.wav")
    stream = p.open(input_device_index=1,format=sample_format, channels=channels, rate=SAMPLE_RATE, frames_per_buffer=CHUNK, input=True, stream_callback=audio_chunk_ready)
    stream.start_stream()
    return stream

taskScheduled = AtomicLong(0)
isDown = AtomicLong(0)

def onButtonChanged(channel):
    global isDown
    global taskScheduled
    global inInterrupt

    if isDown.value == 1:
        isDown.value = 0
    else:
        isDown.value = 1

    print(f"button changed on channel: {channel} state {GPIO.input(21)}")
    if isDown.value:
        onPiecePickedUp()
    else:
        onPiecePutDown()

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def audio_chunk_ready(in_data, frame_count, time_info, status):
    global currentFrames
    currentFrames.append(in_data)
#    print(f"status {status}, time {time_info}")
    return (in_data, pyaudio.paContinue)

PIN = 21

def onPiecePickedUp():
    global stream
    print("start recording")
    stream = startRecording()

def onPiecePutDown():
    print("stop recording")
    global stream
    stopRecording(stream)
    timestamp = int(datetime.datetime.utcnow().timestamp())

    saveRecordingAs(f"recording-{timestamp}.wav")
    print("saved recording")

def main():
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
            print(p.get_device_info_by_index(i))

    global stream

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN, GPIO.BOTH, callback=onButtonChanged, bouncetime=50)
    signal.signal(signal.SIGINT, signal_handler)

    from flask import Flask
    app = Flask("hurensohn")
    @app.route("/")
    def index():
        return "okay!"

    app.run(host='0.0.0.0', port=8080)

    signal.pause()

main()
