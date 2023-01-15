#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 22:55:23 2023

@author: John Ciubuc

This is adapted from https://github.com/davabase/whisper_real_time

"""


import io
import os
import speech_recognition as sr
import whisper
import torch
import threading

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform



class WhisperRT:
    _modelName = 'tiny.en'
    _nonEnglish = False
    _energyThreshold = 1000
    _recordTimeout = 2
    _phraseTimeout = 3
    _defaultMicrophone = 'pulse'
    _tempFile = ''
    _ambientNoiseAdjustment = 2 # How many seconds to adjust for noise on start
    _activeRecording = False
    transcription = ['']
    
    _phraseTime = None      # The last time a recording was retreived from the queue.
    _lastSample = bytes()   # Current raw audio bytes.
    _Queue = ''         
    _Recorder = ''
    _Source = ''
    _Model = ''
    
    def __init__(self):
        self._setupRecognizer()
        self._Model = whisper.load_model(self._modelName)
        self._tempFile = NamedTemporaryFile().name;
        
        # Adjust microphone to ambient noise
        with self._Source:
            self._Recorder.adjust_for_ambient_noise(self._Source, self._ambientNoiseAdjustment)
            
        # Create a background thread that will pass us raw audio bytes.
        # We could do this manually but SpeechRecognizer provides a nice helper.
        self._Recorder.listen_in_background(self._Source, 
                                            self.record_callback, 
                                            phrase_time_limit=self._recordTimeout)
         # Cue the user that we're ready to go.
        print("Model loaded. Listening in background\n")
            
        
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
            
    def record_callback(self, _, audio:sr.AudioData) -> None:
        """
        Threaded callback function to recieve audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        if self._activeRecording:
            data = audio.get_raw_data()
            self._Queue.put(data)
    
    def _recordThread(self):
        while self._activeRecording:
            try:
                now = datetime.utcnow()
                # Pull raw recorded audio from the queue.
                if not self._Queue.empty():
                    phrase_complete = False
                    # If enough time has passed between recordings, consider the phrase complete.
                    # Clear the current working audio buffer to start over with the new data.
                    if self._phraseTime and now - self._phraseTime > timedelta(seconds=self._phraseTimeout):
                        last_sample = bytes()
                        phrase_complete = True
                    # This is the last time we received new audio data from the queue.
                    self._phraseTime = now
           
                    # Concatenate our current audio data with the latest audio data.
                    while not self._Queue.empty():
                        data = self._Queue.get()
                        self._lastSample += data
           
                    # Use AudioData to convert the raw data to wav data.
                    audio_data = sr.AudioData(self._lastSample, 
                                              self._Source.SAMPLE_RATE, 
                                              self._Source.SAMPLE_WIDTH)
                    wav_data = io.BytesIO(audio_data.get_wav_data())
           
                    # Write wav data to the temporary file as bytes.
                    with open(self._tempFile, 'w+b') as f:
                        f.write(wav_data.read())
           
                    # Read the transcription.
                    result = self._Model.transcribe(self._tempFile, fp16=torch.cuda.is_available())
                    text = result['text'].strip()
           
                    # If we detected a pause between recordings, add a new item to our transcripion.
                    # Otherwise edit the existing one.
                    if phrase_complete:
                        self.transcription.append(text)
                    else:
                        self.transcription[-1] = text
           
                    # Clear the console to reprint the updated transcription.
                    os.system('cls' if os.name=='nt' else 'clear')
                    for line in self.transcription:
                        print(line)
                    # Flush stdout.
                    print('', end='', flush=True)
           
                    # Infinite loops are bad for processors, must sleep.
                    sleep(0.1)
            except KeyboardInterrupt:
                break
               
        print("Recording thread terminated")
    
    def startRecording(self):
        self._activeRecording = True
        recordThread = threading.Thread(target=self._recordThread)
        recordThread.start()

    def stopRecording(self):
        self._activeRecording = False
    
    # transcription = ['']
    


w = WhisperRT()
w.startRecording()


# For debug
while True:
    try:
        sleep(0.25)
    except KeyboardInterrupt:
        break
               
    

   

   
