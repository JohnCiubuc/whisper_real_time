#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 22:55:23 2023

@author: John Ciubuc

This is adapted from https://github.com/davabase/whisper_real_time

"""


import io
import speech_recognition as sr
import whisper
import torch
import threading
import soundfile as sf
import pyloudnorm as pyln
import numpy as np
import recorder as Rec

import audioop

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform


class WhisperRT:
    _parent = ''
    _modelName = 'base.en'
    _nonEnglish = False
    _energyThreshold = 1000
    _recordTimeout = 1 # Below 1 results in freezing issues
    _phraseTimeout = 1
    _defaultMicrophone = 'pulse'
    _tempFile = ''
    # _ambientNoiseAdjustment = 10 # How many seconds to adjust for noise on start
    _activeRecording = False
    _activeTranscribing = False
    transcription = ['']
    
    _phraseTime = None      # The last time a recording was retreived from the queue.
    _lastSample = bytes()   # Current raw audio bytes.
    _Queue = ''         
    _Recorder = ''
    _Source = ''
    _Model = ''
    _stopListeningFunction = ''
    Recorder = ''
    
    ModelReady = False
    
    
    _ambience = 0
    
    def __init__(self, parent):
        self._parent = parent
        # self._setupRecognizer()
        self._Model = whisper.load_model(self._modelName)
        self._tempFile = NamedTemporaryFile().name;
        
        self.Recorder = Rec.Recorder()
        
        # Adjust microphone to ambient noise
        # with self._Source:
        #     self._Recorder.adjust_for_ambient_noise(self._Source, self._ambientNoiseAdjustment)

         # Cue the user that we're ready to go.
        print("\n\nModel loaded.\n\n")
        self.ModelReady = True
        
    def _setupRecognizer(self):
        # Thread safe Queue for passing data from the threaded recording callback.
        self._Queue = Queue()
        # We use SpeechRecognizer to record our audio because it has a nice feauture where it can detect when speech ends.
        self._Recorder = sr.Recognizer()
        self._Recorder.energy_threshold = self._energyThreshold
        # Definitely do this, dynamic energy compensation lowers the energy threshold dramtically to a point where the SpeechRecognizer never stops recording.
        self._Recorder.dynamic_energy_threshold = False
        
        # Important for linux users. 
        # Prevents permanent application hang and crash by using the wrong Microphone
        if 'linux' in platform:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    if self._defaultMicrophone in name:
                        self._Source = sr.Microphone(sample_rate=16000, device_index=index)
                        break
        else:
            self._Source = sr.Microphone(sample_rate=16000)
            
    def _record_callback(self, _, audio:sr.AudioData) -> None:
        """
        Threaded callback function to recieve audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        self._Queue.put(data)
        print('record callback into data')
        
    
    def _manualMicEnergyLevel(self):
        self.Recorder.startListen()
        time_start = datetime.utcnow()
        levels = []
        var_levels = []
        while self._activeRecording:
            # print(self.Recorder.getRMS())
            levels.append(self.Recorder.getRMS())
            # Average rms over past three recordings
            if len(levels) == 3:
                average_rms = np.mean(levels)
                print(average_rms)
                var_levels.append(average_rms)
                #  Get variance from at least 5 RMS's
                if len(var_levels) > 5:
                    var = np.var(var_levels)
                    print(f'Variance = {var}')
                    # If excessive variance, restart recording
                    if var > 30:
                        var_levels = []
                    # If consistent variance, save ambience
                    elif var < 15:
                        self._ambience = np.mean(var_levels)
                        print('Ambience variance acceptable')
                        print(f'Average ambience: {self._ambience}')
                        # self._recordThread()
                        return
                levels = []
            # if not self._Queue.empty():
            #     # Concat Queue
            #     databytes = bytes()
            #     while not self._Queue.empty():
            #         databytes = databytes + self._Queue.get()
                    
            #     # Use AudioData to convert the raw data to wav data.
            #     audio_data = sr.AudioData(databytes, 
            #                               self._Source.SAMPLE_RATE, 
            #                               self._Source.SAMPLE_WIDTH)
               
            #     data, rate =  sf.read(io.BytesIO(audio_data.get_wav_data()), dtype='float32') 
            #     # create BS.1770 meter
            #     meter = pyln.Meter(rate) 
            #     # measure loudness
            #     loudness = meter.integrated_loudness(data) 
            #     levels.append(loudness)
            #     print(f'{loudness} - {np.var(loudness)})')
            
            #     # if  datetime.utcnow() - time_start > timedelta(seconds=self._ambientNoiseAdjustment):
            #     #     print('Time exceeded')
            #     #     print(f'Average ambience: {np.mean(levels)}')
            #     #     self._energyThreshold = np.mean(levels)
            #     #     self._recordThread()
                    
            sleep(0.1)

    def _recordThread(self):
        bStartRecord =  False
        while self._activeRecording:
            try:
                # Pull raw recorded audio from the queue.
                if not self._Queue.empty():
                    # Concatenate our current audio data with the latest audio data.
                    databytes = bytes()
                    while not self._Queue.empty():
                        databytes = databytes + self._Queue.get()
           
                    # Use AudioData to convert the raw data to wav data.
                    audio_data = sr.AudioData(databytes, 
                                              self._Source.SAMPLE_RATE, 
                                              self._Source.SAMPLE_WIDTH)

                    data, rate =  sf.read(io.BytesIO(audio_data.get_wav_data()), dtype='float32')  # load audio (with shape (samples, channels))
                    meter = pyln.Meter(rate) # create BS.1770 meter
                    loudness = meter.integrated_loudness(data) # measure loudness
                    print(loudness)
                    
                    # Check if current audio is louder than ambience:
                    if loudness >= self._energyThreshold + 7:
                        bStartRecord = True
                        print('Actively Recording')
                        self._lastSample += databytes
                    # Previously recording, but now audio is back to ambience
                    elif loudness <= self._energyThreshold + 2 and bStartRecord:
                        self._lastSample += databytes
                        bStartRecord = False
                        # Read the transcription.
                        # Use AudioData to convert the raw data to wav data.
                        audio_data = sr.AudioData(self._lastSample, 
                                                  self._Source.SAMPLE_RATE, 
                                                  self._Source.SAMPLE_WIDTH)
                        
                        self._lastSample = bytes()
                        wav_data = io.BytesIO(audio_data.get_wav_data())
               
                        # Write wav data to the temporary file as bytes.
                        with open(self._tempFile, 'w+b') as f:
                            f.write(wav_data.read())
                            
                        result = self._Model.transcribe(self._tempFile, fp16=torch.cuda.is_available())
                        text = result['text'].strip()
               
                        # Send to parent (if exists) current transcription
                        try:
                            self._parent.getTranscription(text)
                        except:
                            print("Unable to send parent transcription. "
                                  "Likely WhisperRT uninitilized with parent or "
                                  "Parent does not have a 'getTranscription' function.")
                        print(text)
                    
            except :
                print('Main record thread failed. Something ugly happened')
                break
        
            
            sleep(0.1)
               
        print("Recording thread terminated")
    
    def startRecording(self):
        self._activeRecording = True
        self._activeTranscribing = False
        # Create a background thread that will pass us raw audio bytes.
        # We could do this manually but SpeechRecognizer provides a nice helper.
        # self._stopListeningFunction = self._Recorder.listen_in_background(self._Source, 
        #                                     self._record_callback, 
        #                                     phrase_time_limit=self._recordTimeout)
        
        
        # Reset energy threshold for manual detection
        # We will start transcription thread in the manual audio level fn
        self._energyThreshold = 0
        self.transcription = ['']
        recordThread = threading.Thread(target=self._manualMicEnergyLevel)
        recordThread.start()


    def stopRecording(self):
        self.Recorder.stopListen()
        self.Recorder.stopRecord()
        # self._stopListeningFunction(wait_for_stop=False)
        self._activeRecording = False
        self._activeTranscribing = False
   

   
