import pyaudio
import numpy
import paho.mqtt.client as mqtt
import wave
import scipy.io.wavfile as wavfile
import time

REPLAY = False
filename = None
TOPIC_SOUND = "audio/sound"
TOPIC_REPLAY = "audio/replay"
TOPIC_RECORD = "audio/record"

def on_message_replay(client, userdata, message):
    global REPLAY
    global filename
    msg = message.payload.decode("utf-8")
    if msg == "false":
        REPLAY = False
    else :
        REPLAY = True
        filename = msg
    print("REPLAYING", flush=True)

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
print("Connected to MQQT", flush=True)
client.subscribe(TOPIC_REPLAY, qos=0)
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
    # print(REPLAY)
    if REPLAY == False:
        frames = [] # A python-list of chunks(numpy.ndarray)
        for _ in range(0, int(RATE / CHUNKSIZE * RECORD_SECONDS)):
            data = stream.read(CHUNKSIZE)
            frames.append(numpy.frombuffer(data, dtype=numpy.int16))
        #Convert the list of numpy-arrays into a 1D array (column-wise)
        numpydata = numpy.hstack(frames)
        client.publish(TOPIC_SOUND, numpydata.tobytes())
    else :
        fs_rate, s = wavfile.read(filename)
        # slice signal by fs_rate samples (1s duration)
        samples = len(s)//fs_rate
        client.publish(TOPIC_RECORD, "record")
        for i in range(samples): 
            if REPLAY == False:
                break
            start = i*fs_rate
            stop  = start + fs_rate - 1 
            numpydata = numpy.hstack(s[start:stop])
            client.publish(TOPIC_SOUND, numpydata.tobytes())
            # time.sleep(1)
        client.publish(TOPIC_RECORD, "stop record")
        REPLAY = False
        print("REPLAYING OVER", flush=True)