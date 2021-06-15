#!/usr/bin/python3
import logging
import threading
import time
import pymumble_py3
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS
import pyaudio

import queue
import numpy as np


# Connection details for mumble server. Hardcoded for now, will have to be
# command line arguments eventually
pwd = ""  # password
server = "mumble.lug-saar.de"
nicks = ["luftbrueckeRaum1","luftbrueckeRaum2"]
rooms = ["Raum 1","Raum 2"]

chunkQueue = [
    {
        'user': {
            'session': int,
            'channel_id': int,
            'name': str,
        },
        'soundchunk': {
            'pcm': queue.Queue(),
            'time': queue.Queue(),
            'timestamp': queue.Queue()
        }
    }
]


# pyaudio set up
CHUNK = 1024
FORMAT = pyaudio.paInt16  # pymumble soundchunk.pcm is 16 bits
CHANNELS = 1
RATE = 48000  # pymumble soundchunk.pcm is 48000Hz

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=False,  # enable both talk
                output=True,  # and listen
                frames_per_buffer=CHUNK)

def sound_received_handler(user, soundchunk):
    """ play sound received from mumble server upon its arrival """
    # timestamp = float(time.time())
    # if( timestamp < soundchunk.time + 20):
    #     try: 
    #         sound_received_handler.chunkBuffer *= soundchunk.pcm; 
    #     except AttributeError: 
    #         sound_received_handler.chunkBuffer = 1
    # else if( timestamp >)
    index = None

    for _index in range(1,len(chunkQueue)):
        
        if(user['name'] == chunkQueue[_index]['user']['name']):
            chunkQueue[_index]['soundchunk']['pcm'].put(soundchunk.pcm)
            chunkQueue[_index]['soundchunk']['time'].put(soundchunk.time)
            chunkQueue[_index]['soundchunk']['timestamp'].put(soundchunk.timestamp)
            index = _index
            break
                        
    if(not index):
        new_item = {
            'user': {
                'session': user['session'],
                'channel_id': user['channel_id'],
                'name': user['name'],
            },
            'soundchunk': {
                'pcm': queue.Queue(),
                'time': queue.Queue(),
                'timestamp': queue.Queue()
            }
        }
        chunkQueue.append(new_item)



def mumble_thread_function(server, nick, password=pwd, room="LUGSaar (Treffen Do 18 Uhr 30)"):

    chunkBuffer = np.zeros(960,dtype=np.int16)

    mumble = pymumble_py3.Mumble(server, nick, password=pwd)

    # set up callback called when PCS event occurs
    mumble.callbacks.set_callback(PCS, sound_received_handler)
    mumble.set_receive_sound(1)  # Enable receiving sound from mumble server
    
    mumble.start()
    mumble.is_ready()

    LUGSaarTreffenCh = mumble.channels.find_by_name("LUGSaar (Treffen Do 18 Uhr 30)")

    if(len(LUGSaarTreffenCh) >= 0):
        LUGSaarTreffenCh.move_in()

        LUGSaarRoomCh = mumble.channels.find_by_name(room)

        if(len(LUGSaarRoomCh) >= 0):
            LUGSaarRoomCh.move_in()

            # soundChunkraw   = chunkQueue[0]['pcmQueue'].get()
            # soundChunkAudioData = np.frombuffer(soundChunkraw.pcm, dtype=np.int16)
            # timestamp = soundChunkraw.time
            
            
            # constant capturing sound and sending it to mumble server

            while True:

                # minTime = 0x7FFFFFFF
                # soundChunkAudioData = np.zeros(1920,dtype=np.int8)

                # for _index in range(1,len(chunkQueue)):
                #     if( not chunkQueue[_index]["soundchunk"]['time'].empty() and  (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= minTime)):
                #         minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]
                
                # for _index in range(1,len(chunkQueue)):
                #     if( not chunkQueue[_index]["soundchunk"]['time'].empty() and  (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.020))):
                #         pcmBuffer = chunkQueue[_index]["soundchunk"]['pcm'].get()
                #         timeBuffer = chunkQueue[_index]["soundchunk"]['time'].get()
                #         timestampBuffer = chunkQueue[_index]["soundchunk"]['timestamp'].get()

                #         pcmBuffer = np.frombuffer(pcmBuffer, dtype=np.int8)
                #         soundChunkAudioData = np.add(soundChunkAudioData, pcmBuffer)

                
                
                # if( soundChunkraw.time <= timestamp + 0.020 ):
                #     chunkBuffer = np.convolve(chunkBuffer, soundChunkAudioData)
                    

                #     # try: 
                #     #     mumble_thread_function.chunkBuffer *= soundChunkAudioData
                #     # except AttributeError: 
                #     #     mumble_thread_function.chunkBuffer = soundChunkAudioData

                # else:
                # #thread2threadQueue.put( stream.read(CHUNK, exception_on_overflow=False) )
                #     try:
                #         mumble.sound_output.add_sound(chunkBuffer.tobytes())
                #     except any:
                #         print("chunkBuffer is empty !!!! \n")

                #     timestamp = soundChunkraw.time

                # soundChunkraw   = chunkQueue[0]['pcmQueue'].get()
                # soundChunkAudioData = np.frombuffer(soundChunkraw.pcm, dtype=np.int16)
                

                # stream.write(soundChunkAudioData.tobytes())
                time.sleep(1)


    mumble.stop()


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    threads = list()

    for index in range(1):
        logging.info("Main    : create and start thread %d.", index)
        x = threading.Thread(target=mumble_thread_function, args=(server,nicks[index],pwd,rooms[index]))
        threads.append(x)
        x.start()


    time.sleep(0.5)

    while True:

        minTime = 0x7FFFFFFF
        soundChunkAudioData = np.zeros(1920,dtype=np.int8)

        for _index in range(1,len(chunkQueue)):
            if( not chunkQueue[_index]["soundchunk"]['time'].empty() and  (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= minTime)):
                minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]
        
        for _index in range(1,len(chunkQueue)):
            if( not chunkQueue[_index]["soundchunk"]['time'].empty() and  (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.020))):
                pcmBuffer = chunkQueue[_index]["soundchunk"]['pcm'].get()
                timeBuffer = chunkQueue[_index]["soundchunk"]['time'].get()
                timestampBuffer = chunkQueue[_index]["soundchunk"]['timestamp'].get()

                pcmBuffer = np.frombuffer(pcmBuffer, dtype=np.int8)
                soundChunkAudioData = np.add(soundChunkAudioData, pcmBuffer>>1)

        stream.write(soundChunkAudioData.tobytes())
        

    # for index, thread in enumerate(threads):
    #     logging.info("Main    : before joining thread %d.", index)
    #     thread.join()
    #     logging.info("Main    : thread %d done", index)

    # close the stream and pyaudio instance
    stream.stop_stream()
    stream.close()
    p.terminate()

