#!/usr/bin/env python
#########################################################################
# PySerial-Ploter                                                       #
# Autor: Yosel de Jesus Balibrea Lastre                                 #
# Email: yosel.balibrea@reduc.edu.cu                                    #
#########################################################################
import sys
import os
import time
import serial
import serial.tools.list_ports as serialdevs

# Python Qt4 bindings for GUI objects
from PyQt4.QtGui import *
from PyQt4.QtCore import *

# Numpy functions for image creation
import numpy as np

# Matplotlib Figure object
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4agg \
    import FigureCanvasQTAgg as FigureCanvas

from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar


#Variables globales que podran ser modificadas en el menu de opciones
SPEED = 57600 #velocidad en el puerto
TIMEOUT = 0.1
XMIN = -1
XMAX = 10000
YMIN = -0.01
YMAX = 0.15

max_v = 0.12 # Maximo valor esperado a la entrada(REAL)

MR = 5.0 # Maximo valor posible en el ADC

gain = MR/max_v # ganancia del amplificador a la entrada

RES = 1024.0 #Resolucion del ADC (10bit)

# Ejes de coordenadas
y = []
x = []


def get_serial_ports():
    ports = []
    # obtener una lista de puertos disponibles
    for i in serialdevs.comports():
        ports.append([i[0], i[1]])
    # Devolver valores por defecto si no hay puertos disponibles
    if len(ports) == 0:
        if os.name == "nt":
            ports.append(["COM1", "Puerto Falso"])
        else:
            ports.append(["/dev/ttyS0", "Puerto Falso"])

    return ports


class Worker(QThread):
    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)
        self.okay = False
        self.s = serial.Serial()

    def run(self):
        global y
        global gain
        global MR
        global RES

        print "runing"
        v = 0
        while self.okay:
            try:
                time.sleep(0.1)
                #self.s.reset_input_buffer()
                v = (int(self.s.readline()) * MR / RES) / gain
                y.append(v)
            except:
                print "no valido"
            print "valor: ", v

    def rset(self):
        self.okay = True

    def stop(self):
        self.okay = False


class Qt4MplCanvas(FigureCanvas):
    # Class to represent the FigureCanvas widget
    def __init__(self, parent):
        # plot definition
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.axes.set_xlim(XMIN, XMAX)
        self.axes.set_ylim(YMIN, YMAX)
        self.y, self.t = [], []
        self.plt, = self.axes.plot(self.t, self.y)
        self.axes.grid(True)
        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)
        # set the parent widget
        self.setParent(parent)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)


class ApplicationWindow(QMainWindow):
    # Example main window
    def __init__(self):
        # initialization of Qt MainWindow widget
        QMainWindow.__init__(self)
        # set window title
        self.setWindowTitle("PySerial-Ploter")
        self.setWindowIcon(QIcon("./icono.png"))

        # Objeto serial
        self.s = 0

        #escalas posibles
        self.scala = [0.001, 0.1, 1, 10, 60]
        self.scal_index = 1

        # Menus y barra de menu
        self.f_menu = QMenu("&Archivo", self)
        self.f_menu.addAction("&Configurar", self.configurep, Qt.CTRL + Qt.Key_C)
        self.f_menu.addAction('&Cerrar', self.fileQuit, Qt.CTRL + Qt.Key_Q)
        self.menuBar().addMenu(self.f_menu)
        self.h_menu = QMenu('&Ayuda', self)
        self.menuBar().addMenu(self.h_menu)
        self.menuBar().addSeparator()
        self.h_menu.addAction('&Acerca de PyQt', self.about_prog)
        self.h_menu.addAction('&Acerca de', self.about, Qt.CTRL + Qt.Key_H)

        # instantiate a widget, it will be the main one
        self.main_widget = QWidget(self)
        # Crear Layouts
        main_l = QHBoxLayout(self.main_widget)
        fig_l = QVBoxLayout()
        butt_l = QVBoxLayout()

        # Botones y otros controles
        self.bOpc = QPushButton(text="OPCIONES")
        self.bini = QPushButton(text="INICIAR")
        self.bsave = QPushButton(text="GUARDAR EN CSV")
        self.bload = QPushButton(text = "CARGAR CSV")
        self.bclear = QPushButton(text = "LIMPIAR GRAFICA")
        self.bscale = QPushButton(text = "ESCALA: 0.1s")
        self.bdist = QPushButton(text = "AREA Y DISTANCIA")

        # Combo Box
        self.cbport = QComboBox()
        self.available = get_serial_ports()
        for (i, desc) in self.available:
            self.cbport.addItem("%s (%s)" % (i, desc))

        # Labels
        self.l_status = QLabel("Estado: Parado")
        self.l_dist = QLabel("")
        self.l_area = QLabel("")

        # instantiate our Matplotlib canvas widget
        self.graf = Qt4MplCanvas(self.main_widget)

        # instantiate the navigation toolbar
        self.ntb = NavigationToolbar(self.graf, self.main_widget)

        # Empaquetar los widgets en sus layouts
        fig_l.addWidget(self.graf)
        fig_l.addWidget(self.ntb)

        butt_l.addWidget(self.bOpc)
        butt_l.addWidget(self.bini)
        butt_l.addWidget(self.bclear)
        butt_l.addWidget(self.bsave)
        butt_l.addWidget(self.bload)
        butt_l.addWidget(self.bscale)
        butt_l.addWidget(self.bdist)
        butt_l.addWidget(self.cbport)
        butt_l.addWidget(self.l_status)
        butt_l.addWidget(self.l_dist)
        butt_l.addStretch()

        main_l.addLayout(butt_l)
        main_l.addLayout(fig_l)


        # set the focus on the main widget
        self.main_widget.setFocus()

        # set the central widget of MainWindow to main_widget
        self.setCentralWidget(self.main_widget)

        # Run status
        self.is_run = False

        # Eventos
        self.bini.clicked.connect(self.start) #inicializar o parar

        self.cbport.highlighted.connect(self.scan_ports) #escanear y seleccionar un puerto
        self.cbport.activated.connect(self.scan_ports)

        self.bsave.clicked.connect(self.save_data) #guardar datos en csv

        self.bscale.clicked.connect(self.scalar) #cambiar de escala

        self.bclear.clicked.connect(self.clear_graf) #Limpiar la grafica


        # thread
        self.worker = Worker(self)

        self.timer = QBasicTimer()  # basic timer

        # Centrar la ventana
        self.centre()

    def scalar(self):
        # AUN FALTAN COSAS ######################################################
        self.scal_index += 1
        if self.scal_index > len(self.scala) - 1:
            self.scal_index = 0
        self.bscale.setText("ESCALA: "+str(self.scala[self.scal_index]) + "s")

    def clear_graf(self):
        global x
        global y
        #preguntar al usuario si quiere salvar los datos
        #existentes en la grafica
        reply = QMessageBox.question(self, "QMessageBox.question()",
                                           """Desea guardar los datos existentes en la grafica.\nSi seleciona "NO" estos se perderan""",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.save_data()
            x = []
            y = []
            self.graf.plt.set_data(x, y)
            self.graf.fig.canvas.draw()
        elif reply == QMessageBox.No:
            x = []
            y = []
            self.graf.plt.set_data(x, y)
            self.graf.fig.canvas.draw()
        else:
            return

    def centre(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

    def scan_ports(self):
        if self.available != get_serial_ports():
            self.available = get_serial_ports()
        else:
            return
        for (i, desc) in self.available:
            self.cbport.clear()
            self.cbport.addItem("%s (%s)" % (i, desc))

    def start(self):
        global s
        if self.is_run:
            self.bini.setText("INICIAR")
            self.l_status.setText("Estado: Parado")
            self.is_run = False
            self.worker.s.close()
            self.worker.stop()
            self.worker.wait()
            self.timer.stop()
        else:
            self.bini.setText("PARAR")
            self.l_status.setText("Estado: Corriendo")
            self.is_run = True
            self.worker.s = serial.Serial(self.available[self.cbport.currentIndex()][0],
                                          SPEED, timeout=TIMEOUT)
            self.worker.rset()
            self.worker.start()
            self.timer.start(200, self)

    def save_data(self):
        global y
        #guardar los valores contenidos en y como una variable temporal
        #ya que esta cambia constantemente
        yt = y
        file = QFileDialog.getSaveFileName(self,"Guardar datos en csv","datos",
                                           "Archivo CSV (*.csv);;Todos Los Archivos (*)")
        if not file:
            return

        f = open(file, 'w')
        f.write("Valor(Volts); Tiempo(*0.1s)\n")
        for i in range(len(yt)):
            f.write(str(yt[i])+";"+str(i)+"\n")
        f.close()

    def timerEvent(self, event):
        global x
        global y
        try:
            self.graf.plt.set_data(np.arange(len(y)), y)
            self.graf.fig.canvas.draw()
            #print "data: " ,y
        except:
            print "no graf\n"

    def configurep(self):
        pass

    def fileQuit(self):
        self.close()

    def about_prog(self):
        QMessageBox.aboutQt(self,"Acerca de PyQt4")

    def about(self):
        QMessageBox.about(self, "Acerca de", """GUI para plotear datos desde el puerto serie\n 
        Autor: Yosel de Jesus Balibrea Lastre""")


qApp = QApplication(sys.argv)
aw = ApplicationWindow()
aw.show()
sys.exit(qApp.exec_())
