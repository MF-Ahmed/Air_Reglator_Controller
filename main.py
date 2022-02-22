# ------------------------------------------------- ----- 
# ---------------------- main.py ------------------- ---- 
# --------------------------------------------- ---------
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic import loadUi
from binascii import unhexlify
import pandas as pd
import time
import datetime
import traceback, sys, os
import logging
from logging.handlers import TimedRotatingFileHandler
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT  as  NavigationToolbar)
import serial
import serial.tools.list_ports
import numpy  as  np
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker2Signals(QObject):
    '''
    Defines the signals available from a running worker2 thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)



class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs['progress_callback'] = self.signals.progress

    #@pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Donez


class Worker2(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker2, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn2 = fn
        self.args2 = args
        self.kwargsz = kwargs
        self.signals = WorkerSignals()

        self.kwargs['progress_callback'] = self.signals.progress

    #@pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Donez




class MatplotlibWidget(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        loadUi("qt_designer.ui", self)

        self.setWindowTitle("Air Regulator Controller")

        #self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ######################## Logger #################################
        self.formatter = logging.Formatter("%(asctime)s , %(message)s",
                                           datefmt='%d-%b-%y,%H:%M:%S')

        '''
        'S'	Seconds
        'M'	Minutes
        'H'	Hours
        'D'	Days
        'W0'-'W6'	Weekday (0=Monday)
        'midnight'	Roll over at midnight        

        '''
        self.handler = TimedRotatingFileHandler('log/Plotdata.txt', when="midnight", interval=1, encoding='utf8')
        #self.handler = TimedRotatingFileHandler('log/Plotdata.txt', when="s", interval=60, encoding='utf8')
        #self.handler = TimedRotatingFileHandler('log/PlantMessages', when="s", interval=10,encoding='utf8')
        #for windows
        self.handler.suffix ="_%#d-%#m-%Y,%H-%M-%S"+".txt"
        # for Pi
        #self.handler.suffix="_%-d-%-m-%Y,%H-%M-%S"+".txt"

        self.handler.setFormatter(self.formatter)
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        ######################## Logger #################################

        #self.pushButton_generate_random_signal.clicked.connect(self.update_graph)

        self.index = self.SelBR.findText('9600')
        self.SelBR.setCurrentIndex(self.index)


        #self.index = self.SelPar.findText('None')
        #self.SelPar.setCurrentIndex(self.index)

        self.AddSerPorts();

        self.ConnectBtn.setCheckable(True)
        self.ConnectBtn.clicked[bool].connect(self.press)
        self.EXITBtn.clicked.connect(self.closeEvent)
        self.PlotLoggedData_btn.clicked.connect(self.PlotLogFile)

        self.arr1 = np.array([])
        self.arr2 = np.array([])
        self.arr3 = np.array([])
        self.arr4 = np.array([])
        self.result = ""
        self.curr_sec = 0
        self.prev_sec = 0
        self.i=0
        self.DataByte=[0]*10

        self.Setpoint="0"
        self.PercentOpening = "0"
        self.InletPress= "0"
        self.OutletPress= "0"

        self.PercentOpeningPlot = 0.0
        self.InletPressPlot = 0.0
        self.OutletPressPlot = 0.0
        self.LoggingEnabled=0

        self.PercentOpeningList = ["a","b"]
        self.InletPressList = ["a","b"]
        self.OutletPressList = ["a","b"]

        self.limitSwOpen=0
        self.limitSwClose = 0

        #########################################################################
        self.PercentageOpen_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.PercentageOpen_label.setStyleSheet(
            'border: 5px solid blue;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#0000ff;')
        ######################################################################
        self.InletPress_Lable.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.InletPress_Lable.setStyleSheet(
            'border: 5px solid red;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#aa0000;')
        ######################################################################
        self.OutletPress_Lable.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.OutletPress_Lable.setStyleSheet(
            'border: 5px solid green;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#005500;')

        ######################################################################
        self.SetPoint_Lable.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.SetPoint_Lable.setStyleSheet(
            'border: 5px solid black;background-color: rgb(85, 255, 255);font: 24pt "Comic Sans MS"; '
            'font-weight:600;color:#000000;')



        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.UP_Btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.DN_Btn.setContextMenuPolicy(Qt.CustomContextMenu)

        self.UP_Btn.clicked.connect(lambda: self.ChangeSP("Increase"))
        self.DN_Btn.clicked.connect(lambda: self.ChangeSP("Decrease"))


        self.UP_Btn.customContextMenuRequested.connect(lambda: self.handle_right_click("Increase"))
        self.DN_Btn.customContextMenuRequested.connect(lambda: self.handle_right_click("Decrease"))

        self.SetSpBtn.clicked.connect(self.SendSP)

        self.Log_checkBox.setChecked(False)
        self.Log_checkBox.toggled.connect(lambda: self.checkBox(self.Log_checkBox))

        #os.chdir("C:/Users/Uzair/Desktop/Air_RegUI/log")

        #self.file_name = 'Plotdata.txt'
        #self.default_path = os.path.dirname(os.path.abspath(self.file_name))

        self.default_path = os.path.dirname(os.path.abspath(__file__))
        self.default_path = self.default_path +"\log"


        self.lineEdit.setAlignment(Qt.AlignLeft)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setText(self.default_path)

        self.OpenFile_btn.clicked.connect(self._open_file_dialog)


        #self.timer = QTimer(self)
        #self.timer.setInterval(1000)
        #self.timer.timeout.connect(self.recurring_timer)

        #self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))


    def PlotLogFile(self):

        self.logger.handlers.clear()
        self.LoggingEnabled = 0



        try:
            time_list = []
            Date = []
            Time = []
            Data = []
            SetPoint =[]
            PerOpen = []
            InletPress = []
            OutletPress= []
            Dummytime = []
            CSVData = []
            i=0


            with open(self.default_path+"\Plotdata.txt","r") as f:
                for line in f.readlines():
                    i=i+1
                    time_list.append(line.split()[0])
                    Data.append(line.split()[2])
                    Dummytime.append(i)
                    CSVData.append(Data[0].split(","))



                for i in range(len(Data)):
                    test = Data[i].split(",")
                    OutletPress.append(float(test[3]))
                    InletPress.append(float(test[2]))
                    PerOpen.append(float(test[1]))
                    SetPoint.append(float(test[0]))
                    Time_int = (time_list[i].split(","))
                    Time.append(Time_int[1])

            f.close()
            #print(Time)
            #test_datetimestr = '2018-06-29 08:15:27.785758'
            #dt = datetime.datetime.strptime(test_datetimestr,"%#d-%#m-%Y,%H-%M-%S")
            #dt = datetime.datetime.strptime(test_datetimestr, '%Y-%m-%d %H%M%S.%f')
            #print(dt.time())

            SetPointNP_Array = np.array((SetPoint))
            PerOpenNP_Array = np.array((PerOpen))
            InletPressNP_Array = np.array((InletPress))
            OutletPressNP_Array = np.array((OutletPress))
            DummytimeNP_Array = np.array(Time)

            plt.ylim(0.0, 250.0)

            #plt.grid(color='b', linestyle='-', linewidth=0.5)
            plt.grid()
            #plt.figure(figsize=(10, 6))
            plt.xticks(rotation=90, ha='right')
            plt.tight_layout()
            plt.tick_params(axis='x', which='major', labelsize=8)
            plt.plot(DummytimeNP_Array, SetPointNP_Array,label='SetPoint',marker = 'o',linestyle='-')
            plt.plot(DummytimeNP_Array, InletPressNP_Array,label='InletPress',marker = '+',linestyle='-')

            plt.plot(DummytimeNP_Array, OutletPressNP_Array,label='OutletPress',marker = '.',linestyle='-')
            plt.plot(DummytimeNP_Array, PerOpenNP_Array,label='% Opening',marker = 'x',linestyle='-')
            plt.legend(loc="upper left")
            plt.title("Graph of Setpoint, % Opening,Inlet and Outlet Pressure",fontweight='bold')
            plt.xlabel('Time')
            plt.ylabel('Pressure (Bars)')

            plt.show()
            ############################ variables cleanup ###################
            Date = []
            Time = []
            Data = []
            SetPoint =[]
            PerOpen = []
            InletPress = []
            OutletPress= []
            Dummytime = []
            CSVData = []
            SetPointNP_Array = np.array([])
            PerOpenNP_Array = np.array([])
            InletPressNP_Array = np.array([])
            OutletPressNP_Array = np.array([])
            DummytimeNP_Array = np.array([])


            #values = np.loadtxt(self.default_path+"\Plotdata.txt", dtype=str)

            #values = np.array_split(values, 3, axis=1)
            #datetime = values[0]
            #print(datetime)
            #a,b = np.split(datetime, 2)
            #values =  values[2]
            #print(a)
            #print(b)



        except:
            print("file not found")

        #print(self.df)



    def _open_file_dialog(self): # a function to open the dialog window
        self.default_path = str(QFileDialog.getExistingDirectory())
        self.lineEdit.setText(self.default_path)


    def checkBox(self,chkbox):
        if chkbox.isChecked() == True:
            self.LoggingEnabled=1

        else:
            self.LoggingEnabled = 0
            self.Log_Time_label.setText("")
            #print(chkbox.text() + " is deselected")



    def handle_right_click(self,text):
        if text == "Increase":
            self.Setpoint = int(self.Setpoint)
            self.Setpoint = self.Setpoint + 10
            if self.Setpoint > 100:
                self.Setpoint = 100
            self.SetPoint_Lable.setText(str(self.Setpoint))

        elif text == "Decrease":
            self.Setpoint = int(self.Setpoint)
            self.Setpoint = self.Setpoint - 10
            if self.Setpoint < 0:
                self.Setpoint = 0
            self.SetPoint_Lable.setText(str(self.Setpoint))
        else:
            pass


    def SendSP(self):

        self.Sepoint_hexStr = hex(self.Setpoint)
        aloo = ""
        aloo_int = int(self.Sepoint_hexStr, 16)
        aloo = self.Sepoint_hexStr.strip('0x')

        if aloo_int <=16:
            if aloo_int < 16:
                aloo = "0"+aloo
            else:
                aloo = aloo+"0"

        if aloo_int == 32 or aloo_int == 48 or aloo_int == 64 or aloo_int == 80:
            aloo = aloo+"0"

        message_bytes = bytes.fromhex(aloo)
        self.ser.write(message_bytes)


    def closeEvent(self, event):

        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit? Any unsaved work will be lost.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
             sys.exit()

        else:
            pass

    def keyPressEvent(self, event):
        """Close application from escape key.

        results in QMessageBox dialog from closeEvent, good but how/why?
        """
        if event.key() == Qt.Key_Escape:
            sys.exit()

    def ChangeSP(self, text):
        if text == "Increase":
            self.Setpoint = int(self.Setpoint)
            self.Setpoint = self.Setpoint + 1
            if self.Setpoint>100:
                self.Setpoint=100
            self.SetPoint_Lable.setText(str(self.Setpoint))

        elif text == "Decrease":
            self.Setpoint = int(self.Setpoint)
            self.Setpoint = self.Setpoint - 1
            if self.Setpoint<0:
                self.Setpoint=0
            self.SetPoint_Lable.setText(str(self.Setpoint))
        else:
            pass

    def press(self):
        if self.ConnectBtn.isChecked():
            self.chosenport = self.SelPort.currentText()
            self.chosenBR = self.SelBR.currentText()
            self.ConnectBtn.setText("Connected")
            print("Connected to " + str(self.chosenport))

            worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
            worker.signals.result.connect(self.print_output)
            worker.signals.finished.connect(self.thread_complete)
            #worker.signals.progress.connect(self.progress_fn)

            # Execute
            self.threadpool.start(worker)

            worker2 = Worker(self.execute_this_fn2)  # Any other args, kwargs are passed to the run function
            worker2.signals.result.connect(self.print_output2)
            worker2.signals.finished.connect(self.thread_complete2)
            # worker.signals.progress.connect(self.progress_fn)

            # Execute
            self.threadpool.start(worker2)





        else:
             #self.threadpool.stop(worker)
             self.ConnectBtn.setText("Dis-Connected")
             self.logger.handlers.clear()
             self.LoggingEnabled = 0
             print("Dis Connected from " + str(self.chosenport))
             self.chosenport = 0

    def btnclicked(self):
        print("Connect clicked")

    def update_graph(self):

        #if self.PercentOpening != '0':

        self.PercentOpeningPlot = float(self.PercentOpening)
        self.arr2 = np.append(self.arr2, self.PercentOpeningPlot)

        self.InletPressPlot = float(self.InletPress)
        self.arr3 = np.append(self.arr3, self.InletPressPlot)

        self.OutletPressPlot = float(self.OutletPress)
        self.arr4 = np.append(self.arr4, self.OutletPressPlot)

        self.arr1 = np.append(self.arr1, self.i)
        self.i = self.i + 1


        if self.i==50:
            self.i=0
            self.arr1 = []
            self.arr2 = []
            self.arr3 = []
            self.arr4 = []


        self.MplWidget.canvas.axes.clear()

        self.MplWidget.canvas.axes.plot(self.arr1,self.arr2,marker='*', linestyle='-')
        self.MplWidget.canvas.axes.plot(self.arr1, self.arr3, marker='.', linestyle='-')
        self.MplWidget.canvas.axes.plot(self.arr1, self.arr4, marker='o', linestyle='-')

        self.MplWidget.canvas.axes.set_ylim(0, 250)
        self.MplWidget.canvas.axes.set_xlim(0, 50)
        self.MplWidget.canvas.axes.set_ylabel('Pressure (Bar)')
        #self.MplWidget.canvas.axes.set_ylabel('Pressure (Bar)')
        #self.MplWidget.canvas.axes.plot(self.arr1,self.arr2,color = 'deepskyblue', linewidth = 0.7)
        #self.MplWidget.canvas.axes.set_xticklabels(labels=self.arr1, rotation=90)
        #self.MplWidget.canvas.axes.plot(t, sinus_signal)
        #self.MplWidget.canvas.axes.legend(('cosinus', 'sinus'), loc='upper right')
        self.MplWidget.canvas.axes.legend(('Percent Open','Inlet Pressure','Outlet Pressure'), loc='upper right')
        self.MplWidget.canvas.axes.set_title(' Percent open, Inlet Pressure, Outlet Pressure')
        self.MplWidget.canvas.axes.grid(True, lw='.2', ls='--', c='.1')
        # Annotate on hover with grid line show------------
        mplcursors.cursor(hover=True)

        self.MplWidget.canvas.draw()

    def AddSerPorts(self):
        self.Ports = serial.tools.list_ports.comports()
        
        for x in range(len(self.Ports)):
            self.Port = self.Ports[x]
            print(self.Port)
            self.Portstr = str(self.Port)
            self.PortName = self.Portstr.split(" ")
            self.portnameA = self.PortName[0]
            self.SelPort.addItems([self.portnameA])





    def execute_this_fn2(self, progress_callback):
        try:
            self.arr1 = []
            self.arr2 = []
            self.arr3 = []
            self.arr4 = []
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()


            while (self.chosenport != 0):

                print("Thread 2 is running")
                self.update_graph()

        except Exception as e:

            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()
            print("Exception has occured")
            print(e)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setInformativeText(str(e))
            msg.exec()


    def execute_this_fn(self, progress_callback):

        try:
            self.ser = serial.Serial(self.chosenport, self.chosenBR, timeout=0.1)  # ,parity=serial.PARITY_EVEN, rtscts=1)
            time.sleep(0.25)

            print("I have opened "  +str(self.chosenport) + ", with Baud Rate "+str(self.chosenBR))
            print("Thread1 started")

            while (self.chosenport != 0):

                self.now = datetime.datetime.now()
                StartByte1 = self.ser.read().hex()
                StartByte2 = self.ser.read().hex()

                if (StartByte1 == "aa") and (StartByte2 == "55"):
                     for i in range(0,9):
                        self.DataByte[i]= self.ser.read().hex()

                else:
                    self.DataByte = self.DataByte

                #self.Setpoint = str(self.DataByte[0])
                #self.Setpoint = int(self.Setpoint, 16)

                #self.Setpoint= hex(self.Setpoint)

                separator = ""

                self.PercentOpeningList[0] = str(self.DataByte[1])
                self.PercentOpeningList[1] = str(self.DataByte[2])

                self.OutletPressList[0] = str(self.DataByte[3])
                self.OutletPressList[1] = str(self.DataByte[4])

                self.InletPressList[0] = str(self.DataByte[5])
                self.InletPressList[1] = str(self.DataByte[6])

                self.PercentOpening = separator.join(self.PercentOpeningList)

                self.PercentOpening = int(self.PercentOpening, 16)
                #print(str(self.PercentOpening))

                self.PercentOpening = (float(self.PercentOpening )) / 10
                self.PercentOpening = format(self.PercentOpening / 10, "10.1E")

                ##self.PercentOpening = hex(self.PercentOpening)

                self.OutletPress= separator.join(self.OutletPressList)

                self.OutletPress= int(self.OutletPress, 16)
                self.OutletPress= (float(self.OutletPress)) / 10


                self.InletPress = separator.join(self.InletPressList)
                self.InletPress = int(self.InletPress, 16)
                self.InletPress  = (float(self.InletPress )) / 10

                if self.LoggingEnabled == 1:
                    x= datetime.datetime.now()
                    print(x.second)
                    self.curr_sec = x.second

                    if self.curr_sec != self.prev_sec:
                        self.Log_Time_label.setText(
                            str(x.time().hour) + ":" + str(x.time().minute) + ":" + str(
                                x.time().second))
                        self.logger.info( str(self.Setpoint) +","+ str(float(self.PercentOpening))+
                                         ","+str(float(self.OutletPress))+","+str(float(self.InletPress))
                                         )

                    self.prev_sec = self.curr_sec

                self.update_lables()



                #print(self.now.strftime("%X") +" I got "+str(self.DataByte)  +" from Arduino")
                ##xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))

            print('Port closed')
            self.ser.close()
            ##self.MplWidget.canvas.axes.clear()
            ##self.MplWidget.canvas.draw()


        except Exception as e:
            print('Port closed')
            self.ser.close()
            self.MplWidget.canvas.axes.clear()
            self.MplWidget.canvas.draw()
            print("Exception has occured")
            print(e)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setInformativeText(str(e))
            msg.setText("Please Select a Serial Port!")
            msg.setWindowTitle("Error")
            msg.exec()

    def print_output(self, s):
        #pass
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")
        #self.UpdateLCD()

    def print_output2(self, s):
        #pass
        print(s)

    def thread_complete2(self):
        print("THREAD2 COMPLETE!")
        #self.UpdateLCD()



    def update_lables(self):

        self.PercentageOpen_label.setText("{:.2f} %".format(float(self.PercentOpening)))
        self.InletPress_Lable.setText("{:.2f}".format(float(self.InletPress)))
        self.OutletPress_Lable.setText("{:.2f}".format(float(self.OutletPress)))
        self.SetPoint_Lable.setText(str(self.Setpoint))




app = QApplication([])
app.setStyle("Fusion")
aloo = QStyleFactory.keys()
print(aloo)
window = MatplotlibWidget()
window.show()
app.exec_()
