import pyaudio
import numpy
import scipy.io.wavfile as wav
import paho.mqtt.client as mqtt
import wave
import scipy.io.wavfile as wavfile


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
	
TOPIC_SEND_AUDIO = "raspberry/audio/sound"
client = mqtt.Client("record", clean_session=True)
client.connect(HOST_NAME, 1883, keepalive=1800 )
client.on_disconnect = on_disconnect
print("Connected to MQQT", flush=True)
# 

RATE=44100
RECORD_SECONDS = 1
CHUNKSIZE = 1024
CHANNELS = 2

filename = "./out.wav"
fs_rate, s = wavfile.read(filename)
print(s, flush = True)

# slice signal by fs_rate samples (1s duration)
samples = len(s)//fs_rate
client.publish("raspberry/audio/record", "record")
for i in range(samples): 
   start = i*fs_rate
   stop  = start + fs_rate - 1 
   numpydata = numpy.hstack(s[start:stop])
   client.publish(TOPIC_SEND_AUDIO, numpydata.tobytes())
client.publish("raspberry/audio/record", "stop record")
