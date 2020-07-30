import pyaudio
import numpy
import scipy.io.wavfile as wav
import paho.mqtt.client as mqtt
import wave
import scipy.io.wavfile as wavfile
import time

REPLAY = False
TOPIC_SOUND = "raspberry/audio/sound"
TOPIC_REPLAY = "raspberry/audio/replay"
TOPIC_REALTIME = "raspberry/audio/realtime"

def on_message_replay(client, userdata, message):
    global REPLAY
    REPLAY = True
    client2 = mqtt.Client("replay", clean_session=True)
    client2.connect(HOST_NAME, 1883, keepalive=1800 )
    print("REPLAYING", flush=True)
    client2.publish("raspberry/audio/record", "stop record", 0)
    filename = "./out.wav"
    fs_rate, s = wavfile.read(filename)
    # slice signal by fs_rate samples (1s duration)
    samples = len(s)//fs_rate
    client2.publish("raspberry/audio/record", "record", 0)
    for i in range(samples): 
        start = i*fs_rate
        stop  = start + fs_rate - 1 
        numpydata = numpy.hstack(s[start:stop])
        client2.publish(TOPIC_SOUND, numpydata.tobytes())
        time.sleep(1)
 
    print("REPLAYING OVER", flush=True)
    client2.publish("raspberry/audio/record", "stop record", 0)
    client2.publish("raspberry/audio/realtime", " ", 0)


def on_message_realtime(client, userdata, message):
    global REPLAY
    REPLAY = False
    print("Realtime", flush=True)


# MQTT
HOST_NAME = "localhost"
def on_disconnect(client, userdata, rc):
    print("Client Got Disconnected")
    if rc != 0:
        print('Unexpected MQTT disconnection. Will auto-reconnect')
    else:
        print('rc value:' + str(rc))
    try:
        print("Trying to Reconnect")
        client.connect(HOST_NAME, 1883)
        print("Reconnected")
    except:
        print("Error in Retrying to Connect with Broker")
	

client = mqtt.Client("record", clean_session=True)
client.connect(HOST_NAME, 1883, keepalive=1800 )
client.on_disconnect = on_disconnect
client.message_callback_add(TOPIC_REPLAY, on_message_replay)
client.message_callback_add(TOPIC_REALTIME, on_message_realtime)
print("Connected to MQQT", flush=True)
client.subscribe("raspberry/audio/#", qos=0)
# 
RATE=44100
RECORD_SECONDS = 1
CHUNKSIZE = 1024
CHANNELS = 2

# initialize portaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNKSIZE)
client.loop_start()
while True :
    print(REPLAY)
    if REPLAY == False:
        frames = [] # A python-list of chunks(numpy.ndarray)
        for _ in range(0, int(RATE / CHUNKSIZE * RECORD_SECONDS)):
            data = stream.read(CHUNKSIZE)
            frames.append(numpy.frombuffer(data, dtype=numpy.int16))
        #Convert the list of numpy-arrays into a 1D array (column-wise)
        numpydata = numpy.hstack(frames)
        client.publish(TOPIC_SOUND, numpydata.tobytes())