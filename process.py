import numpy
import numpy as np
import librosa
import time
from scipy.signal import lfilter, butter, filtfilt
import paho.mqtt.client as mqtt
import signal
import sys
import wave

HOST_NAME = "localhost"
TOPIC_SOUND = "raspberry/audio/sound"
TOPIC_RECORD = "raspberry/audio/record"
TOPIC_ZCR = "raspberry/audio/zcr"
TOPIC_MFCC = "raspberry/audio/mfcc"
TOPIC_TIME = "raspberry/audio/time"

elapsed_time = []
CHANNELS = 2
RATE = 44100
RECORD = False

n = 0
newwav = None

def signal_handler(sig, frame):
    global newwav
    print("SIGINT received !")
    newwav.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


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

def on_message_sound(client, userdata, message):
    global elapsed_time
    global CHANNELS
    global RATE
    global newwav
    global RECORD
    deserialized = numpy.frombuffer(message.payload, dtype=numpy.int16)
    s = deserialized.reshape(-1, CHANNELS)
    if RECORD == True:
        newwav.writeframesraw(s)
    zcr, mfcc = process_audio(s, 0, RATE, 10)
    client.publish(TOPIC_ZCR, zcr)
    client.publish(TOPIC_MFCC, mfcc)
    client.publish(TOPIC_TIME, elapsed_time[-1])

def on_message_record(client, userdata, message):
    global RECORD
    global n
    global newwav
    msg = message.payload.decode("utf-8")
    print("msg received = "+msg, flush=True)
    if(msg == "record"):
        RECORD = True
        n = n + 1
        newwav = wave.open("out"+str(n)+".wav", "wb")
        newwav.setnchannels(CHANNELS)
        newwav.setsampwidth(2) #to check
        newwav.setframerate(RATE)
    elif(msg == "stop record"):
        RECORD = False
        newwav.close()

client = mqtt.Client("process", clean_session=True)
client.connect(HOST_NAME, 1883, keepalive=1800 )
client.on_disconnect = on_disconnect
client.message_callback_add(TOPIC_SOUND, on_message_sound)
client.message_callback_add(TOPIC_RECORD, on_message_record)
print("Connected to MQQT", flush=True)
client.subscribe("raspberry/audio/#", qos=0)

# 
def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def Average(lst): 
    return sum(lst) / len(lst)

def process_audio(signal, channel, fs_rate, period=10, lpass_cutoff=6000, hpass_cutoff=0):
   
   global elapsed_time
   
   t0= time.process_time()

   total_samples = len(signal)
   window = total_samples//period
   
   zcr           = []
   mfcc          = []

   i = 0
   while((i+window-1) < total_samples):

      data = signal[:,channel] #

      #---------------------------
      # Signal treatment
      # -------------------------- 
      # Denoise
      n = 6 # the larger n is, the smoother curve will be
      b = [1.0 / n] * n
      a = 1  

      yy = lfilter(b,a,data[i:i+window-1])

      # Low pass filter
      yy = butter_lowpass_filter(yy, lpass_cutoff, fs_rate)

      # High pass filter
      if hpass_cutoff > 0:
         yy = butter_highpass_filter(yy, hpass_cutoff, fs_rate)       
 
      #---------------------------
      # Features extraction
      # -------------------------- 
      # Zero crossing rate
      max_zcr = np.max(librosa.feature.zero_crossing_rate(yy))

      # MFCC (Mel-Frequency Cepstral Coefficients)
      max_mfcc = np.max(librosa.feature.mfcc(y=yy, sr=fs_rate, n_mfcc=80))

      mfcc.append(max_mfcc)
      zcr.append(max_zcr)

      i = i + window

   elapsed_time.append(time.process_time() - t0)
   return Average(zcr), Average(mfcc)


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
client.loop_forever()