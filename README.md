# Sound Analysis

## Needed python packages

Proccessing script :

> numpy; librosa; scipy.signal; wave; paho-mqtt

Recording script :

> pyauido; numpy; paho-mqtt; wave; scipy


## MQTT Topics

    enact/actuators/microphone/record
Send either "record" or "stop record"	to record the currently playing sound in a wav file.
	
    enact/sensors/microphone/sound
The recoring script send the sound on this topic.

    enact/sensors/microphone/zcr
    enact/sensors/microphone/mfcc
    enact/sensors/microphone/time
 

   Send respectively zcr, mfcc and time as Numbers.
    
    enact/sensors/microphone/replay

 Enable the replay option when a valid filename is specified, if 'false' is sent the replay stop.








