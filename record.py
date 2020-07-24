import pyaudio
import numpy
import scipy.io.wavfile as wav


# MQTT 
import paho.mqtt.client as mqtt

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
	
TOPIC_SEND_AUDIO = "raspberry/audio"
client = mqtt.Client("record", clean_session=True)
client.connect(HOST_NAME, 1883, keepalive=1800 )
client.on_disconnect = on_disconnect
print("Connected to MQQT", flush=True)
# 

RATE=44100
RECORD_SECONDS = 1
CHUNKSIZE = 1024

# initialize portaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=2, rate=RATE, input=True, frames_per_buffer=CHUNKSIZE)
while True :
    frames = [] # A python-list of chunks(numpy.ndarray)
    for _ in range(0, int(RATE / CHUNKSIZE * RECORD_SECONDS)):
        data = stream.read(CHUNKSIZE)
        frames.append(numpy.frombuffer(data, dtype=numpy.int16))
    #Convert the list of numpy-arrays into a 1D array (column-wise)
    numpydata = numpy.hstack(frames)
    client.publish(TOPIC_SEND_AUDIO, numpydata.tobytes())