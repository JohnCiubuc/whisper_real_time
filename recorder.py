#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 18:16:09 2023

@author: inathero
"""

import pyaudio
import math
import struct
import wave
import time
import os
from sys import platform

Threshold = 10

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2

TIMEOUT_LENGTH = 5

f_name_directory = r'/tmp/'

class Recorder:

    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self, device_index):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=chunk,
                                  input_device_index=device_index)

    def record(self):
        print('Noise detected, recording beginning')
        rec = []
        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:

            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold: end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            rec.append(data)
        self.write(b''.join(rec))

    def write(self, recording):
        n_files = len(os.listdir(f_name_directory))

        filename = os.path.join(f_name_directory, '{}.wav'.format(n_files))

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(recording)
        wf.close()
        print('Written to file: {}'.format(filename))
        print('Returning to listening')



    def listen(self):
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            print(rms_val)
            # if rms_val > Threshold:
                # self.record()


p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
if 'linux' in platform:
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if self._defaultMicrophone in name:
                self._Source = sr.Microphone(sample_rate=16000, device_index=index)
                break
for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
a = Recorder()
a.listen()
