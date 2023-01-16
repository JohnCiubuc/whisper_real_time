#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 18:16:09 2023

@author: John Ciubuc

Adapted from https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio
"""

import pyaudio
import math
import struct
import wave
import threading
from sys import platform

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class Recorder:

    last_rms = 0
    
    _listening = False
    _recording = False
    _data = []
    @staticmethod
    def rms(frame):
        count = len(frame) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        self.p = pyaudio.PyAudio()
        info = self.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        index = 0
        if 'linux' in platform:
            for i in range(0, numdevices):
                if (self.p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    if 'pulse' in  self.p.get_device_info_by_host_api_device_index(0, i).get('name'):
                        index = i
                        break
            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      output=True,
                                      frames_per_buffer=chunk,
                                      input_device_index=index)
        else:
            self.stream = self.p.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      output=True,
                                      frames_per_buffer=chunk)
    def _background_lister(self):
        while self._listening:
            input = self.stream.read(chunk)
            self.last_rms = self.rms(input)
            if self._recording:
                self._data.append(input)       
    def startListen(self):
        if not self._listening:
            self._listening=True
            threading.Thread(target=self._background_lister).start()  
    def stopListen(self):
        self._listening=False    
    def isListening(self):
        return self._listening
    def startRecord(self):
        if not self._recording:
            self._data=[]
            self._recording=True
    def stopRecord(self):
        self._recording=False
        self._full_data = b''.join(self._data)
    def isRecording(self):
        return self._recording
    def restartRecording(self):
        self._data = []
        self._full_data =[]
    def getRecordSnapshot(self):
        print('later') 
    def getRMS(self):
        return self.last_rms
    def getRecordData(self):
        return self._full_data
    
    def saveDataToFile(self, file):
        wf = wave.open(file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(self._full_data)
        wf.close()