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
import atomos.atomic
import atomos.atom as atom

SAMPLE_RATE = 44100
CHUNK = 1024
sample_format = pyaudio.paInt16
channels = 1

p = pyaudio.PyAudio()

currentFrames = []

def saveRecordingAs(recording, name):
    write(name, SAMPLE_RATE, recording)

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

taskScheduled = atom.Atom(False)

def updateState(state, newState):
    state = newState
    return state


def onButtonChanged(channel):
    global taskScheduled    
    taskScheduled.swap(updateState, True)
    print(f"button changed on channel: {channel} state {GPIO.input(21)}")

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


def audio_chunk_ready(in_data, frame_count, time_info, status):
    print(f"got audio chunk {frame_count}")
    global currentFrames
    #currentFrames.append(in_data)

PIN = 21

def main():
    global taskScheduled
    global stream

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN, GPIO.BOTH, callback=onButtonChanged, bouncetime=50)
    signal.signal(signal.SIGINT, signal_handler)    

    while (1):
        if taskScheduled == True:
            phonePiecePickedUp = not GPIO.input(PIN)
            if phonePiecePickedUp:
                #playSoundSync("message.wav")
                stream = startRecording()
            else:
                stopRecording(stream)
                timestamp = "fooo"
#                saveRecordingAs(f"recording-{timestamp}")
            taskScheduled = False


main()
