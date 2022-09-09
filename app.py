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
from playsound import playsound
import pyaudio
import wave
from atomic import AtomicLong
import itertools
import numpy as NP
import datetime

SAMPLE_RATE = 44100
CHUNK = 1024
sample_format = pyaudio.paInt16
channels = 1

p = pyaudio.PyAudio()

currentFrames = []

def saveRecordingAs(name):
    global currentFrames
    flatData = list(itertools.chain(currentFrames))
    arr = NP.array(flatData)
    with wave.open(name, 'wb') as wa:
        wa.setnchannels(1)
        wa.setsampwidth(2)
        wa.setframerate(SAMPLE_RATE)
        wa.writeframes(arr)

    currentFrames = []

def playSoundSync(path): 
    playsound(path)

def stopRecording(stream):
    stream.stop_stream()
    stream.close()
    stream = None

def startRecording():
    global p
    stream = p.open(format=sample_format, channels=channels, rate=SAMPLE_RATE, frames_per_buffer=CHUNK, input=True, stream_callback=audio_chunk_ready)
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
    global taskScheduled
    global inInterrupt
    global stream

    taskScheduled = AtomicLong(0)
    inInterrupt = AtomicLong(0)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN, GPIO.BOTH, callback=onButtonChanged, bouncetime=50)
    signal.signal(signal.SIGINT, signal_handler)    
    signal.pause()

main()
