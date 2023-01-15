#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 17:12:10 2020

@author: inathero
"""

from PyQt5 import QtGui, QtCore, QtWidgets,uic
from PyQt5.QtWidgets import *
import sys
import threading

import whisper_rt

class Ui(QtWidgets.QMainWindow):
    _bButtonActive = False
    Whisper = ''
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('qt/interface.ui', self) # Load the .ui file
        
        self.pushButton.clicked.connect(self.buttonClicked)
        tr = threading.Thread(target=self._initWhisper)
        tr.start()
        # tr.join()
        
    def _initWhisper(self):
        self.Whisper = whisper_rt.WhisperRT()
    def buttonClicked(self):
        self._bButtonActive = not self._bButtonActive
        if self._bButtonActive:
            self.pushButton.setText('End Transcription')
            self.Whisper.startRecording()
        else:
            self.pushButton.setText('Start Transcription')
            self.Whisper.stopRecording()
        
    def closeEvent(self, event):
      # do stuff
      self.Whisper.stopRecording()
      event.accept()
      
app = QtWidgets.QApplication(sys.argv) 
window = Ui() 
window.show()
ret = app.exec_()
sys.exit(ret)