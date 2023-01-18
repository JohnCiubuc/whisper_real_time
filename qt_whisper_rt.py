#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  6 17:12:10 2020

@author: John Ciubuc
"""

from PyQt5 import QtWidgets,uic
from PyQt5.QtCore import pyqtSignal
import sys
import threading
import pyautogui

from time import sleep
import whisper_rt
import WhisperRTScriptEngine.whisper_script_engine as WhisperScriptEngine

class Ui(QtWidgets.QMainWindow):
    _bButtonActive = False
    Whisper = ''
    ScriptEngine = ''
    _transcription = ''
    _fromTranscription = ''
    updateText = pyqtSignal()
    updateTextEdit = pyqtSignal()
    variance = ''
    varianceText=''
    micLabel = ''

    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('qt/interface.ui', self) # Load the .ui file
        
        self.ScriptEngine = WhisperScriptEngine.WhisperRT_ScriptEngine()
        
        self.pushButton.clicked.connect(self.buttonClicked)
        self.pushButton_recalibrate.clicked.connect(self.buttonRecalibrate)
        self.doubleSpinBox_PT.valueChanged.connect(self.doubleSpinBox_PTChanged)
        tr = threading.Thread(target=self._initWhisper)
        tr.start()
        self.updateText.connect(self._asyncUpdateGUI)
        self.updateTextEdit.connect(self._asyncUpdateGUITextedit)
        
    def _initWhisper(self):
        self.Whisper = whisper_rt.WhisperRT(self)
      
    def doubleSpinBox_PTChanged(self,value):
        self.Whisper.varianceThreshold = value
              
    # Saves transcription. Called from WhisperRT
    # writes transcription into text
    # Saved transcription used in a GUI thread later
    def getTranscription(self,texts):
        self._transcription = texts+' '
        if self.checkBox_SK.isChecked():
            pyautogui.write(self._transcription, interval=0.01)
        self.ScriptEngine.processIntent(self._transcription)
        self.updateTextEdit.emit()
        
    # Updates GUI with transcription from thread    
    def _asyncUpdateGUITextedit(self):
        self.plainTextEdit.setPlainText(self.plainTextEdit.toPlainText() + self._transcription)
    
    def _asyncUpdateGUI(self):
        self.label_trans_val.setText(self.variance)
        self.label_trans.setText(self.varianceText)
        self.label_mic.setText(self.micLabel)
        
    def triggerGUIUpdate(self):
        self.updateText.emit()

    # Start/Stop Transcription
    def buttonClicked(self):
        try:
            if not self.Whisper.ModelReady:
                return
        except:
            print("Whisper class wasn't ready")
            return
        self._bButtonActive = not self._bButtonActive
        if self._bButtonActive:
            self.pushButton.setText('Pause Transcription')
            self.Whisper.startRecording()
            self.pushButton_recalibrate.setEnabled(True)
        else:
            self.variance = ''
            self.varianceText=''
            self.micLabel = ''
            self.pushButton.setText('Start Transcription')
            self.label_trans.setText('Start Transcription First')
            self.Whisper.pauseRecording()
            self.triggerGUIUpdate()
        
    def buttonRecalibrate(self):
        self.Whisper.resetAmbience()
    def closeEvent(self, event):
      self.Whisper.stopRecording()
      event.accept()
      
app = QtWidgets.QApplication(sys.argv) 
window = Ui() 
window.show()
ret = app.exec_()
sys.exit(ret)