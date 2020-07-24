import scipy.io.wavfile as wavfile
import numpy as np
import librosa
import time

from scipy.signal import lfilter
from scipy.signal import butter, filtfilt

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

elapsed_time = []

filename = "./hello.wav"
fs_rate, s = wavfile.read(filename)
print(s, flush = True)

# slice signal by fs_rate samples (1s duration)
samples = len(s)//fs_rate

for i in range(samples): 
   start = i*fs_rate
   stop  = start + fs_rate - 1 
   print(s[start:stop])
   zcr, mfcc = process_audio(s[start:stop], 0, fs_rate, 10)
   print(str(zcr) + "," + str(mfcc))

print("Mean processing time per chunk : " + str(np.mean(elapsed_time)))
