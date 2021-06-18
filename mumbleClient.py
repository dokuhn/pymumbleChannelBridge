#!/usr/bin/python3
import logging
import threading
import time
import pymumble_py3
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS
import pyaudio

import queue
import numpy as np
import scipy.interpolate as interp


# Connection details for mumble server. Hardcoded for now, will have to be
# command line arguments eventually
pwd = ""  # password
server = "mumble.lug-saar.de"

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

def room1_sound_received_handler(user, soundchunk):
    """ stores sounds received from mumble server in a threadsafe queue """    
    
    index = None
    # search for an existing dict in chunkQeue object
    for _index in range(1,len(chunkQueue)):
        
        if(user['name'] == chunkQueue[_index]['user']['name']):
            chunkQueue[_index]['soundchunk']['pcm'].put(soundchunk.pcm)
            chunkQueue[_index]['soundchunk']['time'].put(soundchunk.time)
            chunkQueue[_index]['soundchunk']['timestamp'].put(soundchunk.timestamp)
            index = _index
            break
    
    # if there is no exsisting dict in chunkQeue add one for the user                
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


def room1_thread_function(run_event, server=server, nick="luftbrueckeRaum1", password=pwd, room="Raum 1"):

    mumble = pymumble_py3.Mumble(server, nick, password=pwd)

    # set up callback called when PCS event occurs
    mumble.callbacks.set_callback(PCS, room1_sound_received_handler)
    mumble.set_receive_sound(1)  # Enable receiving sound from mumble server
    
    mumble.start()
    mumble.is_ready()

    LUGSaarTreffenCh = mumble.channels.find_by_name("LUGSaar (Treffen Do 18 Uhr 30)")

    if(len(LUGSaarTreffenCh) >= 0):
        LUGSaarTreffenCh.move_in()

        LUGSaarRoomCh = mumble.channels.find_by_name(room)

        if(len(LUGSaarRoomCh) >= 0):
            LUGSaarRoomCh.move_in()

            while run_event.is_set():
           
                time.sleep(60)


    mumble.stop()


def room2_thread_function(run_event, server=server, nick="luftbrueckeRaum2", password=pwd, room="Raum 2"):

    mumble = pymumble_py3.Mumble(server, nick, password=pwd)

    # set up callback called when PCS event occurs
    # mumble.callbacks.set_callback(PCS, room1_sound_received_handler)
    # mumble.set_receive_sound(1)  # Enable receiving sound from mumble server
    
    mumble.start()
    mumble.is_ready()

    LUGSaarTreffenCh = mumble.channels.find_by_name("LUGSaar (Treffen Do 18 Uhr 30)")

    if(len(LUGSaarTreffenCh) >= 0):
        LUGSaarTreffenCh.move_in()

        LUGSaarRoomCh = mumble.channels.find_by_name(room)

        if(len(LUGSaarRoomCh) >= 0):
            LUGSaarRoomCh.move_in()

            while run_event.is_set():

                minTime = 0x7FFFFFFF
                soundChunkAudioData = np.zeros(1920,dtype=np.int8)

                for _index in range(1,len(chunkQueue)):
                    if( not chunkQueue[_index]["soundchunk"]['time'].empty() and (_index == 1)):
                        minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]

                    if( not chunkQueue[_index]["soundchunk"]['time'].empty() and (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= minTime)):
                        minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]
                
                for _index in range(1,len(chunkQueue)):

                    if( not chunkQueue[_index]["soundchunk"]['time'].empty() and (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.010)) ):
                        pcmBuffer0 = chunkQueue[_index]["soundchunk"]['pcm'].get()
                        timeBuffer0 = chunkQueue[_index]["soundchunk"]['time'].get()
                        timestampBuffer0 = chunkQueue[_index]["soundchunk"]['timestamp'].get()

                        pcmBuffer1 = chunkQueue[_index]["soundchunk"]['pcm'].get()
                        timeBuffer1 = chunkQueue[_index]["soundchunk"]['time'].get()
                        timestampBuffer1 = chunkQueue[_index]["soundchunk"]['timestamp'].get()
                     
                        pcmBuffer0 = np.frombuffer(pcmBuffer0, dtype=np.int8)
                        pcmBuffer1 = np.frombuffer(pcmBuffer1, dtype=np.int8)

                        pcmBuffer = np.concatenate( [pcmBuffer0, pcmBuffer1] )

                        pcmBuffer_L = pcmBuffer[0::2].copy()
                        pcmBuffer_R = pcmBuffer[1::2].copy()


                        pcmBuffer_interp_L = interp.interp1d(np.arange(pcmBuffer_L.size),pcmBuffer_L)
                        arr1_compress_L = pcmBuffer_interp_L(np.linspace(0,pcmBuffer_L.size-1,soundChunkAudioData.size/2))

                        pcmBuffer_interp_R = interp.interp1d(np.arange(pcmBuffer_R.size),pcmBuffer_R)
                        arr1_compress_R = pcmBuffer_interp_R(np.linspace(0,pcmBuffer_R.size-1,soundChunkAudioData.size/2))


                        pcmBuffer[0::2] = np.int8(arr1_compress_L)  # np.concatenate((arr1_compress_L[0::1],arr1_compress_R[1::1]),None)
                        pcmBuffer[1::2] = np.int8(arr1_compress_R)
                        # pcmBuffer = np.append(pcmBuffer, pcmBuffer[0])
                        # pcmBuffer = np.ravel(np.vstack((pcmBuffer_interp_L, pcmBuffer_interp_R)), order='F')

                        # pcmBuffer_interp = interp.interp1d(np.arange(pcmBuffer.size),pcmBuffer)
                        # pcmBuffer_stretch = pcmBuffer_interp(np.linspace(0,pcmBuffer.size-1, soundChunkAudioData.size))

                        # pcmBuffer_stretch = np.frombuffer(pcmBuffer_stretch, dtype=np.int8)
                        soundChunkAudioData = np.add(soundChunkAudioData, pcmBuffer)
                    

                    elif( not chunkQueue[_index]["soundchunk"]['time'].empty() and (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.020))):
                        pcmBuffer = chunkQueue[_index]["soundchunk"]['pcm'].get()
                        timeBuffer = chunkQueue[_index]["soundchunk"]['time'].get()
                        timestampBuffer = chunkQueue[_index]["soundchunk"]['timestamp'].get()

                        pcmBuffer = np.frombuffer(pcmBuffer, dtype=np.int8)
                        soundChunkAudioData = np.add(soundChunkAudioData, pcmBuffer)

                    

                        
                # stream.write(soundChunkAudioData.tobytes())
                mumble.sound_output.add_sound( soundChunkAudioData.tobytes() )
                time.sleep(0.021)



    mumble.stop()


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    run_event = threading.Event()
    run_event.set()

    # for index in range(1):
    logging.info("Main    : create and start thread to receive sounds in room1")
    thread1 = threading.Thread(target=room1_thread_function, args=(run_event,))
    thread1.start()

    time.sleep(0.5)

    logging.info("Main    : create and start thread to send sounds back to server in room2")
    thread2 = threading.Thread(target=room2_thread_function, args=(run_event,))
    thread2.start()


    

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        logging.info("attempting to close threads")
        run_event.clear()
        thread1.join()
        thread2.join()
        logging.info("threads successfully closed")    

    # for index, thread in enumerate(threads):
    #     logging.info("Main    : before joining thread %d.", index)
    #     thread.join()
    #     logging.info("Main    : thread %d done", index)

    # close the stream and pyaudio instance
    logging.info("close the stream and pyaudio instance")
    stream.stop_stream()
    stream.close()
    p.terminate()

    
