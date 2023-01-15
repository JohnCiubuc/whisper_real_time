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
        self.doubleSpinBox_PT.valueChanged.connect(self.doubleSpinBox_PTChanged)
        tr = threading.Thread(target=self._initWhisper)
        tr.start()
        self.updateText.connect(self._asyncUpdateGUI)
        
    def _initWhisper(self):
        self.Whisper = whisper_rt.WhisperRT(self)
       
    def doubleSpinBox_PTChanged(self,value):
        print(value)
        self.Whisper._phraseTimeout =   value
              
    # Saves transcription. Called from WhisperRT
    # writes transcription into text
    # Saved transcription used in a GUI thread later
    def getTranscription(self,texts):
        self._fromTranscription = texts+' '
        if self.checkBox_SK.isChecked():
            pyautogui.write(self._fromTranscription, interval=0.01)
        
    # Updates GUI with transcription from thread    
    def _asyncUpdateGUI(self):
        self.plainTextEdit.setPlainText(self.plainTextEdit.toPlainText() + self._transcription)
    
    # Thread to detect if we have new transcription text that's different
    # If so, update main thread with new text
    def _monitorTranscription(self):
        while self._bButtonActive:
            if self._fromTranscription != self._transcription:
                # print('new text')
                self._transcription = self._fromTranscription
                self.updateText.emit()
            sleep(0.2)
        
    # Start/Stop Transcription
    def buttonClicked(self):
        if not self.Whisper.ModelReady:
            return
        self._bButtonActive = not self._bButtonActive
        if self._bButtonActive:
            self.pushButton.setText('End Transcription')
            tr = threading.Thread(target=self._monitorTranscription)
            tr.start()
            self.Whisper.startRecording()
        else:
            self.pushButton.setText('Start Transcription')
            self.Whisper.stopRecording()
        
    def closeEvent(self, event):
      self.Whisper.stopRecording()
      event.accept()
      
app = QtWidgets.QApplication(sys.argv) 
window = Ui() 
window.show()
ret = app.exec_()
sys.exit(ret)