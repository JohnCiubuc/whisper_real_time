#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 17:12:10 2020

@author: inathero
"""

from PyQt5 import QtGui, QtCore, QtWidgets,uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
import sys
import threading
import pyautogui
from multiprocessing import Pipe

from time import sleep
import whisper_rt

class Ui(QtWidgets.QMainWindow):
    _bButtonActive = False
    Whisper = ''
    _transcription = ''
    _fromTranscription = ''
    updateText = pyqtSignal()

    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('qt/interface.ui', self) # Load the .ui file
        
        self.pushButton.clicked.connect(self.buttonClicked)
        tr = threading.Thread(target=self._initWhisper)
        tr.start()
        self.updateText.connect(self._asyncUpdateGUI)
        
    def _initWhisper(self):
        self.Whisper = whisper_rt.WhisperRT(self)
        
    def getTran(self,texts):
        self._fromTranscription = texts
        # print()
    def _asyncUpdateGUI(self):
        self.plainTextEdit.setPlainText(self._transcription)
        pyautogui.write(self._transcription, interval=0.25)
    def _monitorTranscription(self):
        while self._bButtonActive:
            if self._fromTranscription != self._transcription:
                # print('new text')
                self._transcription = self._fromTranscription
                self.updateText.emit()
            sleep(0.2)
    def buttonClicked(self):
        if not self.Whisper.ModelReady:
            return
        self._bButtonActive = not self._bButtonActive
        if self._bButtonActive:
            self.pushButton.setText('End Transcription')
            tr = threading.Thread(target=self._monitorTranscription)
            tr.start()
            # self._monitorTranscription()
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