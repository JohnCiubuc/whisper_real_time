#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 22:55:23 2023

@author: John Ciubuc

This is adapted from https://github.com/davabase/whisper_real_time

"""


import whisper
import torch
import threading
import numpy as np
import recorder as Rec

from tempfile import NamedTemporaryFile
from time import sleep


class WhisperRT:
    _parent = ''
    _modelName = 'base.en'
    _nonEnglish = False
    _defaultMicrophone = 'pulse'
    _tempFile = ''
    transcription = ['']
    
    _Model = ''
    _stopListeningFunction = ''
    Recorder = ''
    
    ModelReady = False
    
    
    _ambience = 0
    _variance = 0
    _activeRecord = False
    
    def __init__(self, parent):
        self._parent = parent
        self._Model = whisper.load_model(self._modelName)
        self._tempFile = NamedTemporaryFile().name;
        
        self.Recorder = Rec.Recorder()
        
         # Cue the user that we're ready to go.
        print("\n\nModel loaded.\n\n")
        self.ModelReady = True
        
    def _manualMicEnergyLevel(self):
        self.Recorder.startListen()
        levels = []
        var_levels = []
        levels_to_record = 3
        while self._activeRecording:
            # print(self.Recorder.getRMS())
            levels.append(self.Recorder.getRMS())
            # Average rms over past three recordings
            if len(levels) == levels_to_record:
                average_rms = np.mean(levels)
                print(average_rms)
                # Initial Run. Setup Variance.
                if self._ambience == 0:
                    var_levels.append(average_rms)
                    #  Get variance from at least 5 RMS's
                    if len(var_levels) > 5:
                        self._variance = np.var(var_levels)
                        print(f'Variance = {self._variance}')
                        # If excessive variance, restart recording
                        if self._variance > 40:
                            var_levels = []
                        # If consistent variance, save ambience, start recording
                        elif self._variance < 25:
                            self._ambience = np.mean(var_levels)
                            print('Ambience variance acceptable')
                            print(f'Average ambience: {self._ambience}')
                            levels_to_record = 5 # Half a second
                            
                #  Actual Recorder
                else:
                    # Start Recording
                    # This will record the last N levels (N * 0.1s) prior to speaking
                    # Allows for 'late' detection of speaking, but full
                    # understanding of intent
                    self.Recorder.startRecord()
                    
                    if average_rms > self._ambience + 2*self._variance:
                        self._activeRecord = True
                        levels_to_record = 2
                        print('Recording')
                    # Stop Recording:
                    elif self._activeRecord and average_rms < self._ambience + self._variance/2:
                        levels_to_record = 5
                        self._activeRecord = False
                        self.Recorder.stopRecord()
                        data = self.Recorder.getRecordData()
                        print('Stop Recording')
                        print(len(data))
                        self.Recorder.saveDataToFile(self._tempFile)
                            
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
                    elif not self._activeRecord:
                        self.Recorder.restartRecording()
                levels = []    
            sleep(0.1)

    
    def startRecording(self):
        self._activeRecording = True
        self._activeTranscribing = False
        # Reset energy threshold for manual detection
        # We will start transcription thread in the manual audio level fn
        self._energyThreshold = 0
        self.transcription = ['']
        recordThread = threading.Thread(target=self._manualMicEnergyLevel)
        recordThread.start()

    def stopRecording(self):
        self._ambience = 0
        self._variance = 0
        self.Recorder.stopListen()
        self.Recorder.stopRecord()
        # self._stopListeningFunction(wait_for_stop=False)
        self._activeRecording = False
        self._activeTranscribing = False