#!/usr/bin/python3
import logging
import threading
import time
import pymumble_py3
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS

import queue
import numpy as np
import scipy.interpolate as interp
from scipy import signal

from helpers import CustomLogger

# Connection details for mumble server. Hardcoded for now, will have to be
# command line arguments eventually later
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
            'duration': queue.Queue(),
            'pcm': queue.Queue(),
            'sequence': queue.Queue(),
            'size': queue.Queue(),
            'time': queue.Queue(),
            'timestamp': queue.Queue(),
            'type': queue.Queue()
        }
    }
]


def room1_sound_received_handler(user, soundchunk):
    """ callback function to store received sounds chunks from mumble server in a threadsafe queue """    
    
    index = None
    # search for a user entry in the dict and keep the index of it 
    # if the user cannot be found in the dict, der index retains the initial value = None
    for _index in range(1,len(chunkQueue)):
        
        if(user['name'] == chunkQueue[_index]['user']['name']):
            chunkQueue[_index]['soundchunk']['duration'].put(soundchunk.duration)
            chunkQueue[_index]['soundchunk']['pcm'].put(soundchunk.pcm)
            chunkQueue[_index]['soundchunk']['sequence'].put(soundchunk.sequence)
            chunkQueue[_index]['soundchunk']['size'].put(soundchunk.size)
            chunkQueue[_index]['soundchunk']['time'].put(soundchunk.time)
            chunkQueue[_index]['soundchunk']['timestamp'].put(soundchunk.timestamp)
            chunkQueue[_index]['soundchunk']['type'].put(soundchunk.type)
            index = _index
            break
    
    # the search for a user in dict was unsuccessful (index value = None), 
    # a new entry is added to the end for the current user            
    if(not index):
        new_item = {
            'user': {
                'session': user['session'],
                'channel_id': user['channel_id'],
                'name': user['name'],
            },
            'soundchunk': {
                'duration': queue.Queue(),
                'pcm': queue.Queue(),
                'sequence': queue.Queue(),
                'size': queue.Queue(),
                'time': queue.Queue(),
                'timestamp': queue.Queue(),
                'type': queue.Queue()
            }
        }
        chunkQueue.append(new_item)



def room1_thread_function(run_event, server=server, nick="luftbrueckeRaum1", password=pwd, room="Raum 1"):
    """ first thread function to run the mumble client for one channel at the time """

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
            
            ticker = threading.Event()
            while run_event.is_set() and not ticker.wait(0.06):
                pass 
            
    mumble.stop()


def room2_thread_function(run_event,server=server, nick="luftbrueckeRaum2", password=pwd, room="Raum 2"):
    """ second thread function to run the mumble client for one channel at the time """

    mumble = pymumble_py3.Mumble(server, nick, password=pwd)
    
    mumble.start()
    mumble.is_ready()

    LUGSaarTreffenCh = mumble.channels.find_by_name("LUGSaar (Treffen Do 18 Uhr 30)")

    if(len(LUGSaarTreffenCh) >= 0):
        LUGSaarTreffenCh.move_in()

        LUGSaarRoomCh = mumble.channels.find_by_name(room)

        if(len(LUGSaarRoomCh) >= 0):
            LUGSaarRoomCh.move_in()

            ticker = threading.Event()
            while run_event.is_set() and not ticker.wait(0.06):

    
                soundChunkAudioData = np.zeros(5760, dtype=np.int8)
                                     

                for _index in range(1,len(chunkQueue)):
                    if( not chunkQueue[_index]["soundchunk"]['time'].empty() and (_index == 1)):
                        minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]

                    if( not chunkQueue[_index]["soundchunk"]['time'].empty() and (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= minTime)):
                        minTime = chunkQueue[_index]["soundchunk"]['time'].queue[0]
                

                for _index in range(1,len(chunkQueue)):

                    durBuffer = []
                    pcmBuffer = []
                    seqBuffer = []
                    sizeBuffer = []
                    timeBuffer = []
                    timestampBuffer = []
                    typeBuffer = []

                    pcmNPBuffer = np.array([],dtype=np.int8)

                    # opus supports frames with: 2.5, 5, 10, 20, 40 or 60 ms of audio data.
                    # so we have to assume the worst case and take one from the queue in the case of a 60ms frame. 
                    if((not chunkQueue[_index]["soundchunk"]['pcm'].empty()) and 
                       (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.0600)) and 
                       (chunkQueue[_index]["soundchunk"]['duration'].queue[0] == 0.06)):
                        
                      
                        durBuffer.append(chunkQueue[_index]["soundchunk"]['duration'].get())
                        pcmBuffer.append(chunkQueue[_index]["soundchunk"]['pcm'].get())
                        seqBuffer.append(chunkQueue[_index]["soundchunk"]['sequence'].get())
                        sizeBuffer.append(chunkQueue[_index]["soundchunk"]['size'].get())
                        timeBuffer.append(chunkQueue[_index]["soundchunk"]['time'].get())
                        timestampBuffer.append(chunkQueue[_index]["soundchunk"]['timestamp'].get())
                        typeBuffer.append(chunkQueue[_index]["soundchunk"]['type'].get())
                       
                        pcmNPBuffer =  np.append(pcmNPBuffer, np.frombuffer( pcmBuffer[0], dtype=np.int8))

                        ####################################################################################################################################
                        ####### historically, if the individual sound chunks have a different sampling rate, they must be resampled to a common rate #######

                        # pcmNPBuffer = np.reshape(pcmNPBuffer, (-1,2))

                        # if( len(pcmNPBuffer) < len(soundChunkAudioData)/2 ):
                        #     upsampling_factor   = len(soundChunkAudioData)/(2*len(pcmNPBuffer))
                        #     downsampling_factor = len(pcmNPBuffer)
                        #     pcmResampleBuffer = signal.resample_poly(pcmNPBuffer, upsampling_factor, downsampling_factor, axis=1) 
                        # elif( len(pcmNPBuffer) > len(soundChunkAudioData)/2  ):
                        #     upsampling_factor   = len(pcmNPBuffer)
                        #     downsampling_factor = len(soundChunkAudioData)/(2)
                        #     pcmResampleBuffer = signal.resample_poly(pcmNPBuffer, upsampling_factor, downsampling_factor, axis=1) 


                        # pcmNPBuffer = np.reshape(pcmNPBuffer, (-1,1))
                        # pcmNPBuffer = pcmNPBuffer.flatten()


                        soundChunkAudioData = np.add(soundChunkAudioData, pcmNPBuffer)


                    elif((not chunkQueue[_index]["soundchunk"]['pcm'].empty()) and 
                         (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.0600)) and 
                         (chunkQueue[_index]["soundchunk"]['duration'].queue[0] == 0.02) and
                         (chunkQueue[_index]["soundchunk"]['pcm'].qsize() >= 3)):

                        for nmbOfValues2Get in range(3):
                            if(chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.0600)):
                                durBuffer.append(chunkQueue[_index]["soundchunk"]['duration'].get())
                                pcmBuffer.append(chunkQueue[_index]["soundchunk"]['pcm'].get())
                                seqBuffer.append(chunkQueue[_index]["soundchunk"]['sequence'].get())
                                sizeBuffer.append(chunkQueue[_index]["soundchunk"]['size'].get())
                                timeBuffer.append(chunkQueue[_index]["soundchunk"]['time'].get())
                                timestampBuffer.append(chunkQueue[_index]["soundchunk"]['timestamp'].get())
                                typeBuffer.append(chunkQueue[_index]["soundchunk"]['type'].get())

                        for nmbOfValues2Get in range(len(pcmBuffer)):
                            pcmNPBuffer =  np.append(pcmNPBuffer, np.frombuffer( pcmBuffer[nmbOfValues2Get], dtype=np.int8))
                        
                        if pcmNPBuffer.size < soundChunkAudioData.size:
                            difference = soundChunkAudioData.size - pcmNPBuffer.size
                            pcmNPBuffer = np.pad(pcmNPBuffer, (0,difference), 'constant')

                        soundChunkAudioData = np.add(soundChunkAudioData, pcmNPBuffer)
                  

                    elif((not chunkQueue[_index]["soundchunk"]['pcm'].empty()) and 
                        (chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.0600)) and 
                        (chunkQueue[_index]["soundchunk"]['duration'].queue[0] == 0.01) and
                        (chunkQueue[_index]["soundchunk"]['pcm'].qsize() >= 6)):

                        for nmbOfValues2Get in range(6):
                            if(chunkQueue[_index]["soundchunk"]['time'].queue[0] <= (minTime + 0.0600)):
                                durBuffer.append(chunkQueue[_index]["soundchunk"]['duration'].get())
                                pcmBuffer.append(chunkQueue[_index]["soundchunk"]['pcm'].get())
                                seqBuffer.append(chunkQueue[_index]["soundchunk"]['sequence'].get())
                                sizeBuffer.append(chunkQueue[_index]["soundchunk"]['size'].get())
                                timeBuffer.append(chunkQueue[_index]["soundchunk"]['time'].get())
                                timestampBuffer.append(chunkQueue[_index]["soundchunk"]['timestamp'].get())
                                typeBuffer.append(chunkQueue[_index]["soundchunk"]['type'].get())

                        for nmbOfValues2Get in range(len(pcmBuffer)):
                            pcmNPBuffer =  np.append(pcmNPBuffer, np.frombuffer( pcmBuffer[nmbOfValues2Get], dtype=np.int8))

                        if pcmNPBuffer.size < soundChunkAudioData.size:
                            difference = soundChunkAudioData.size - pcmNPBuffer.size
                            pcmNPBuffer = np.pad(pcmNPBuffer, (0,difference), 'constant')

                        soundChunkAudioData = np.add(soundChunkAudioData, pcmNPBuffer)
                
                if np.count_nonzero( soundChunkAudioData ) != 0:
                    mumble.sound_output.add_sound( soundChunkAudioData.tobytes() )
              



    mumble.stop()


if __name__ == "__main__":

    logger = CustomLogger()

    logger.info("Test Info Message !!!!")
    logger.debug("Test Debug Message !!!!")
    logger.warning("Test Waring Message !!!!")
    logger.error("Test Error Message !!!!")

    # create a common thread event to control them with each other
    run_event = threading.Event()
    run_event.set()
  
  
    thread1 = threading.Thread(target=room1_thread_function, args=(run_event,))
    thread2 = threading.Thread(target=room2_thread_function, args=(run_event,))
    logger.debug("create and start thread to receive sounds in room1")
    logger.debug("create and start thread to send sounds back to server in room2")
    thread1.start()
    thread2.start()

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        logger.debug("attempting to close threads")
        run_event.clear()
        thread1.join()
        thread2.join()
        logger.debug("threads successfully closed")

    
