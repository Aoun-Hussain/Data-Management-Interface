import sys
import random
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import serial
import time
import traceback
from datetime import datetime

'''
Altering tasks completed after sending and receiving was plotted on GUI:

##Set correct time format (plus 9 hours - present) - Done
##Convert flowmeter units to L/Minutes from Sarwan side - Done
##reset values of volume and accuracy upon reset - Done
##display signal strength on the GUI - Done
##receive, save in log file, and plot on graph. The lists shoulld be emptied - Done

##Write the unit of volume, average flow - Done
##Convert sender time stamp into readable form and then write - Done
##both the send and receive time stamp in the log file - Done

##display battery voltage as a box - Done
##Remove true flowrate - Done
##remove accuracy box and function - Done
##Window size - fit to screen and minimize option - Minimize not possible - it would have to be adjusted to fit the screen - Fit to the laptop Done
##change location of csq box - Done as made another box for monitoring parameters 

##graph scrolls for 20 values during display - Done
##plot graph with x axis time of sender time - Done
##show imei - Done
'''

ser = serial.Serial("COM6",9600)

class Fetcher(QRunnable):
    '''
    Fetches data from the serial port
    '''
    def __init__(self):
        super(Fetcher,self).__init__()
        self.time = []
        self.send_time = []
        self.inter = [0]
        self.IMEI = 0
        self.flow = []
        self.batt = [0]
        self.csq = 0
    @pyqtSlot()
    
    def run(self):
        while ser.inWaiting():                                                          ##Reads the string line
                reading = ser.readline().decode()
                csqVal = reading
                print ("csqVal Check: ", (csqVal.strip().split(",")[0]).split(":")[0])
                if ((csqVal.strip().split(",")[0]).split(":")[0] == "+CSQ"):            ##Updates signal quality value returned from the AT command
                        self.csq = (csqVal.strip().split(",")[0]).split(":")[1]
                if (len(reading) > 50): 
                    self.read = True
                    temp_split = reading.strip().split(",")
                    print("Signal Quality: ", self.csq)
                    print("Parsed Line: ", temp_split)
                    self.IMEI = str(temp_split[0])
                    self.flow = []
                    for i in range(1,len(temp_split)-1):
                        temp_list = str(temp_split[i]).strip().split(":")
                        self.flow.append(int(temp_list[0])/100)                         ##unit in liters/minutes
                        self.time.append(int(temp_list[1]))
                        ts = int(temp_list[1])
                        self.send_time.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
                        self.batt.append(float(temp_list[2])/100)                       ##unit in volts
                    for i in range(1,len(self.time)):
                        self.inter.append(self.time[i] - self.time[i-1])
                    self.time = [self.time[-1]]
                    print("Time Intervals: ", self.inter)
                reading = ""
                
        

class window(QtWidgets.QMainWindow):
    '''
    Displays buttons and graphs, and calls the fetcher to manage received data
    '''
    def __init__(self):
        super(window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle('Water Flow Measurement System')
        self.resize(1048, 807)
        self.setMinimumSize(QtCore.QSize(10, 10))
        self.setMaximumSize(QtCore.QSize(1048, 650))

        self.flowrate = [0]
        self.timedata = [0]
        self.avgvaldata = [0]
        
        self.run = False
        self.clear = True
        
        self.datasize = 0
        self.volumeflown = 0
        self.avg = 0
        self.vol = 0
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.home()   

    def ParamBox(self):
        groupBox = QtWidgets.QGroupBox(self)
        groupBox.setGeometry(QtCore.QRect(15, 50, 100, 380))
        groupBox.setObjectName("groupBox")
        
        fontLabel = QtGui.QFont()
        fontLabel.setFamily("Open Sans")
        fontLabel.setPointSize(10)
        fontLabel.setBold(False)
        fontLabel.setWeight(50)
        
        fontLCD = QtGui.QFont()
        fontLCD.setFamily("Montserrat Light")
        fontLCD.setPointSize(16)

        self.csqDisplay(groupBox, fontLCD, fontLabel)
        self.battDisplay(groupBox, fontLCD, fontLabel)
        self.imeiDisplay(groupBox, fontLCD, fontLabel)
        
        groupBox.setTitle("Device Data")
        
    def DataBox(self):    
        groupBox = QtWidgets.QGroupBox(self)
        groupBox.setGeometry(QtCore.QRect(400, 440, 571, 200))
        groupBox.setObjectName("groupBox")
        
        fontLabel = QtGui.QFont()
        fontLabel.setFamily("Open Sans")
        fontLabel.setPointSize(10)
        fontLabel.setBold(False)
        fontLabel.setWeight(50)
        
        fontLCD = QtGui.QFont()
        fontLCD.setFamily("Montserrat Light")
        fontLCD.setPointSize(16)


        self.cFlowrateDisplay(groupBox, fontLCD, fontLabel)
        self.aFlowrateDisplay(groupBox, fontLCD, fontLabel)
        self.vFlowDisplay(groupBox, fontLCD, fontLabel)
        
        groupBox.setTitle("Receiver Data")
        
    def ControlBox(self):
        groupBox2 = QtWidgets.QGroupBox(self)
        groupBox2.setGeometry(QtCore.QRect(100, 440, 240, 200))
        groupBox2.setObjectName("groupBox")
        groupBox2.setTitle("Controls")
        
        fontLabel = QtGui.QFont()
        fontLabel.setFamily("Open Sans")
        fontLabel.setPointSize(10)
        fontLabel.setBold(False)
        fontLabel.setWeight(50)
        
        fontLCD = QtGui.QFont()
        fontLCD.setFamily("Montserrat Light")
        fontLCD.setPointSize(16)

        self.ButtonsDisplay(groupBox2) 

    def ButtonsDisplay(self, groupBox):
        StartButton = QtWidgets.QPushButton(groupBox)
        StartButton.setGeometry(QtCore.QRect(25, 25, 191, 51))
        StartButton.setObjectName("StartButton")
        StartButton.setText("Start")
        StartButton.pressed.connect(self.start)               
        
        StopButton = QtWidgets.QPushButton(groupBox)
        StopButton.setGeometry(QtCore.QRect(25, 85, 191, 51))
        StopButton.setObjectName("StopButton")   
        StopButton.setText("Stop")
        StopButton.pressed.connect(self.stop)

        ResetButton = QtWidgets.QPushButton(groupBox)
        ResetButton.setGeometry(QtCore.QRect(25, 145, 191, 51))
        ResetButton.setObjectName("ResetButton")   
        ResetButton.setText("Reset")
        ResetButton.pressed.connect(self.reset)      

    def cFlowrateDisplay(self, groupBox, fontLCD, fontLabel):
        self.CurrentFlowrateDisplay = QtWidgets.QLCDNumber(groupBox)
        self.CurrentFlowrateDisplay.setGeometry(QtCore.QRect(30, 50, 151, 91))
        self.CurrentFlowrateDisplay.setFont(fontLCD)
        self.CurrentFlowrateDisplay.setMouseTracking(False)
        self.CurrentFlowrateDisplay.setSmallDecimalPoint(False)
        self.CurrentFlowrateDisplay.setObjectName("CurrentFlowrateDisplay")
        self.CurrentFlowrateDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: skyblue;}")
        
        CurrentFlowRateLabel = QtWidgets.QLabel(groupBox)
        CurrentFlowRateLabel.setGeometry(QtCore.QRect(30, 140, 151, 41))
        CurrentFlowRateLabel.setFont(fontLabel)
        CurrentFlowRateLabel.setObjectName("CurrentFlowRateLabel")
        
        CurrentFlowRateLabel.setText("Curr. Flow Rate (L/Min)")
        
    def csqDisplay(self, groupBox, fontLCD, fontLabel):
        self.SignalQualityDisplay = QtWidgets.QLCDNumber(groupBox)
        self.SignalQualityDisplay.setGeometry(QtCore.QRect(18, 40, 60, 80))
        self.SignalQualityDisplay.setFont(fontLCD)
        self.SignalQualityDisplay.setMouseTracking(False)
        self.SignalQualityDisplay.setSmallDecimalPoint(False)
        self.SignalQualityDisplay.setObjectName("SignalQualityDisplay")
        self.SignalQualityDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: skyblue;}")
        
        SignalQualityLabel = QtWidgets.QLabel(groupBox)
        SignalQualityLabel.setGeometry(QtCore.QRect(18, 90, 60, 80))
        SignalQualityLabel.setFont(fontLabel)
        SignalQualityLabel.setObjectName("SignalQualityLabel")
        
        SignalQualityLabel.setText("Sig. Qual.")

    def battDisplay(self, groupBox, fontLCD, fontLabel):
        self.BatteryValueDisplay = QtWidgets.QLCDNumber(groupBox)
        self.BatteryValueDisplay.setGeometry(QtCore.QRect(18, 160, 60, 80))
        self.BatteryValueDisplay.setFont(fontLCD)
        self.BatteryValueDisplay.setMouseTracking(False)
        self.BatteryValueDisplay.setSmallDecimalPoint(False)
        self.BatteryValueDisplay.setObjectName("BatteryValueDisplay")
        self.BatteryValueDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: skyblue;}")
        
        BatteryValueLabel = QtWidgets.QLabel(groupBox)
        BatteryValueLabel.setGeometry(QtCore.QRect(18, 210, 60, 80))
        BatteryValueLabel.setFont(fontLabel)
        BatteryValueLabel.setObjectName("BatteryValueLabel")
        
        BatteryValueLabel.setText("Sen. Batt. (V)")

    def imeiDisplay(self, groupBox, fontLCD, fontLabel):
        self.ImeiValueDisplay = QtWidgets.QLCDNumber(groupBox)
        self.ImeiValueDisplay.setGeometry(QtCore.QRect(18, 280, 60, 80))
        self.ImeiValueDisplay.setFont(fontLCD)
        self.ImeiValueDisplay.setMouseTracking(False)
        self.ImeiValueDisplay.setSmallDecimalPoint(False)
        self.ImeiValueDisplay.setObjectName("ImeiValueDisplay")
        self.ImeiValueDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: skyblue;}")
        
        ImeiValueLabel = QtWidgets.QLabel(groupBox)
        ImeiValueLabel.setGeometry(QtCore.QRect(18, 330, 60, 80))
        ImeiValueLabel.setFont(fontLabel)
        ImeiValueLabel.setObjectName("ImeiValueLabel")
        
        ImeiValueLabel.setText("Sender")
        
    def aFlowrateDisplay(self, groupBox, fontLCD, fontLabel):
        self.AverageFlowRateDisplay = QtWidgets.QLCDNumber(groupBox)
        self.AverageFlowRateDisplay.setGeometry(QtCore.QRect(210, 50, 151, 91))
        self.AverageFlowRateDisplay.setFont(fontLCD)
        self.AverageFlowRateDisplay.setMouseTracking(False)
        self.AverageFlowRateDisplay.setSmallDecimalPoint(False)
        self.AverageFlowRateDisplay.setObjectName("AverageFlowRateDisplay")
        self.AverageFlowRateDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: darkblue;}")
        
        AverageFlowRateLabel = QtWidgets.QLabel(groupBox)
        AverageFlowRateLabel.setGeometry(QtCore.QRect(210, 150, 151, 21))
        AverageFlowRateLabel.setFont(fontLabel)
        AverageFlowRateLabel.setObjectName("AverageFlowRateLabel")
        
        AverageFlowRateLabel.setText("Avg. Flow Rate (L/Min)")

    def vFlowDisplay(self, groupBox, fontLCD, fontLabel):
        self.VolumeFlowedDisplay = QtWidgets.QLCDNumber(groupBox)
        self.VolumeFlowedDisplay.setGeometry(QtCore.QRect(380, 50, 151, 91))
        self.VolumeFlowedDisplay.setFont(fontLCD)
        self.VolumeFlowedDisplay.setMouseTracking(False)
        self.VolumeFlowedDisplay.setSmallDecimalPoint(False)
        self.VolumeFlowedDisplay.setObjectName("VolumeFlowedDisplay")
        self.VolumeFlowedDisplay.setStyleSheet("QLCDNumber {background-color: darkgrey; color: red;}")
        
        VolumeFlowedLabel = QtWidgets.QLabel(groupBox)
        VolumeFlowedLabel.setGeometry(QtCore.QRect(400, 150, 181, 21))
        VolumeFlowedLabel.setFont(fontLabel)
        VolumeFlowedLabel.setObjectName("VolumeFlowedLabel")
        
        VolumeFlowedLabel.setText("Volume Flown (L)")
        
    def livePlot(self):
        '''
        Plots and updates data every second
        '''
        self.Graph = pg.PlotWidget(self)
        self.Graph.setGeometry(QtCore.QRect(150, 30, 800, 401))
        self.Graph.setLabel('bottom', 'Time', 's')
        self.Graph.setLabel('left', 'Flowrate', 'L / min')
        self.Graph.setTitle('Incoming Flowrate Data')
        self.Graph.showGrid(True, True)
        self.Graph.addLegend()
        pen = pg.mkPen(width=2, color=(77,207,255))
        pen1 = pg.mkPen(width=1, color=(0, 0, 139))
        pen2 = pg.mkPen(width=1, color=(255,255,0))
        self.data_line = self.Graph.plot(self.timedata, self.flowrate, pen=pen, name = 'Current Flowrate')
        self.average_line = self.Graph.plot(self.timedata, self.avgvaldata, pen=pen1, name = 'Average Flowrate')

        self.fetch = Fetcher()
        self.fetch.setAutoDelete(False)
        
        self.timer = QTimer()
        self.timer.setInterval(1000)                  ##Plot updates every second
        self.timer.timeout.connect(self.updatePlot)
        self.timer.start()
    

    def home(self):
        self.DataBox()
        self.ParamBox()
        self.ControlBox()
        self.livePlot()
        self.show()

    def start(self):
        print('Starting!')
        self.run = True

    def stop(self):
        print('Stopping!')
        self.run = False

    def reset(self):
        print('Reseting')
        self.fetch.send_time = []
        self.fetch.flow = []
        self.fetch.time = []
        self.fetch.inter = [0]
        self.fetch.batt = [0]
        self.fetch.IMEI = 0
        self.flowrate = [0]
        self.timedata = [0]
        self.avgvaldata = [0]
        self.volumeflown = 0
        self.datasize = 0
        self.avg = 0
        self.vol = 0
        self.clear = True
        self.updatePlot()
    
    def updatePlot(self):
        '''
        Updates plot every second and fetches value. Assumes
        the first value to be read at t = 0
        '''
        self.logfile = open('datalog.txt', 'a')
        self.logfile.seek(0)
        if self.run or self.clear:
            if not self.clear:
                    print('Processing Data')
                    for i in range(len(self.fetch.flow)):
                        self.flowrate.append(self.fetch.flow[i])
                        print("Intervals: ", self.fetch.inter)
                        self.timedata.append(self.timedata[-1]+self.fetch.inter[i])   ##increasing by sent time interval
                        self.vol += self.flowrate[-1]/60
                        self.avg = ((((self.datasize) * self.avg) + (self.flowrate[-1]))/(self.datasize + 1))
                        print("Average: ", self.avg)
                        self.avgvaldata.append(self.avg)
                        self.datasize += 1
                        self.logfile.write("Send Time: " + self.fetch.send_time[i] + ", Receive Time: " + str(datetime.now()) + ', ' + "Flow: " + str(self.flowrate[-1]) + ", IMEI: " + str(self.fetch.IMEI) + ", Battery: " + str(self.fetch.batt[i]) + '\n')
                    print("Time Axis List: ", self.timedata)
                    
            self.data_line.setData(self.timedata, self.flowrate)
            self.average_line.setData(self.timedata, self.avgvaldata)

            self.VolumeFlowedDisplay.display(self.vol)
            self.AverageFlowRateDisplay.display(self.avgvaldata[-1])
            self.CurrentFlowrateDisplay.display(self.flowrate[-1])
            self.SignalQualityDisplay.display(self.fetch.csq)
            self.ImeiValueDisplay.display(self.fetch.IMEI)
            self.BatteryValueDisplay.display(self.fetch.batt[-1])
            
        self.clear = False
        self.logfile.close()
        self.threadpool.start(self.fetch)
        self.fetch.flow = []
        self.fetch.batt = [self.fetch.batt[-1]]
        self.fetch.send_time = []

        if self.datasize > 1:
            self.fetch.inter = []
        
        if (len(self.timedata) >= 15):     ##empties the lists after length exceeds criteria      
            self.timedata = [self.timedata[-1]]
            self.flowrate = [self.flowrate[-1]]
            self.avgvaldata = [self.avgvaldata[-1]]
        


if __name__ == "__main__":                 ##Multiple threads called under the main function
    def run():
        app = QtWidgets.QApplication(sys.argv)
        Gui = window()
        sys.exit(app.exec_())

run()
ser.close()
