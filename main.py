import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QFileDialog, QHBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from Hyperspectral_image import SpectralImage, wavelength_to_rgb, extract_filename
import numpy as np
from variables import wavelengths

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Visualización hiperespectral'
        self.left = 100
        self.top = 100
        self.width = 1750
        self.height = 580

        self.mouse_pressed = False

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        mainLayout = QHBoxLayout(self.central_widget)

        self.canvas_left = PlotCanvas(self, width=5, height=4)
        self.canvas_right = PlotCanvas(self, width=5, height=4)

        self.canvas_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        mainLayout.addWidget(self.canvas_left)

        self.buttonLayout = QVBoxLayout()

        self.button1 = QPushButton('Seleccionar\n.bil')
        self.button1.clicked.connect(self.load_bil)
        self.buttonLayout.addWidget(self.button1)

        self.button2 = QPushButton('Seleccionar\n.bil.hdr')
        self.button2.clicked.connect(self.load_hdr)
        self.buttonLayout.addWidget(self.button2)

        self.button3 = QPushButton('Representación\nBGR')
        self.button3.clicked.connect(self.show_bgr)
        self.buttonLayout.addWidget(self.button3)

        self.button4 = QPushButton('Seleccionar\npixel')
        self.button4.setCheckable(True)
        self.buttonLayout.addWidget(self.button4)

        self.button5 = QPushButton('Seleccionar\nárea')
        self.button5.setCheckable(True)
        self.button5.clicked.connect(self.reset_selection)
        self.buttonLayout.addWidget(self.button5)

        self.button4.clicked.connect(lambda: self.button5.setChecked(False))

        self.button6 = QPushButton('Limpiar')
        self.button6.clicked.connect(self.deselect_all_buttons)
        self.buttonLayout.addWidget(self.button6)

        mainLayout.addLayout(self.buttonLayout)
        mainLayout.addWidget(self.canvas_right)

        self.bilPath = ''
        self.hdrPath = ''
        self.img_instance = None
        self.img_section = dict()
        self.section_processed = False
        self.mouse_moved_while_pressed = False
        self.img = None
        self.imgMask = None

        self.canvas_left.mpl_connect('button_press_event', self.on_click)
        self.canvas_left.mpl_connect('button_press_event', self.mouse_press)
        self.canvas_left.mpl_connect('button_release_event', self.mouse_release)
        self.canvas_left.mpl_connect('motion_notify_event', self.mouse_move)

    def load_bil(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', filter="Image files (*.bil)")
        if fname[0]:
            self.bilPath = fname[0]
            self.button1.setText("Archivo\n"+extract_filename(fname[0])+"\nseleccionado")
            print(self.bilPath)

    def load_hdr(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', filter="Header files (*.hdr)")
        if fname[0]:
            self.hdrPath = fname[0]
            self.button2.setText("Archivo\n"+extract_filename(fname[0])+"\nseleccionado")

    def show_bgr(self):
        if self.bilPath and self.hdrPath:
            self.img_instance = SpectralImage(self.bilPath, self.hdrPath)
            self.img = self.img_instance.BGR()
            self.imgMask = self.img.copy()
            self.canvas_left.plot_image(self.img)

    def mouse_press(self, event):
        self.mouse_pressed = True
        self.mouse_moved_while_pressed = False

    def reset_selection(self):
        self.img_section = dict()
        self.section_processed = False
        self.button4.setChecked(False)

    def mouse_release(self, event):
        self.mouse_pressed = False
        cont=0
        if self.button5.isChecked() and self.mouse_moved_while_pressed and not self.section_processed:
            all_values = []
            for i in self.img_section:
                row = range(self.img_section[i][0], self.img_section[i][1])
                for j in row:
                    all_values.append(self.img_instance.values[int(i),int(j),:])
                    cont+=1
            all_values = np.transpose(all_values)
            self.canvas_right.plotAreaHyper(all_values)
            self.img_section = dict()
            self.section_processed = True
            self.canvas_left.plot_image(self.imgMask)

    def mouse_move(self, event):
        if self.button5.isChecked():
            if self.mouse_pressed:
                self.mouse_moved_while_pressed = True
                try:
                    x = int(event.xdata)
                    y = int(event.ydata)
                    if x not in self.img_section: self.img_section[x] = [y, y]
                    self.img_section[x].append(y)
                    self.img_section[x].sort()
                    self.img_section[x] = [self.img_section[x][0], self.img_section[x][-1]]
                    radius = 2
                    for i in range(max(0, x - radius), min(self.imgMask.shape[1], x + radius + 1)):
                        for j in range(max(0, y - radius), min(self.imgMask.shape[0], y + radius + 1)):
                            self.imgMask[j, i, :] = (1, 1, 1)
                except:
                    print("Atención: Selecciona un pixel dentro de la imágen")

    def on_click(self, event):
        if self.button4.isChecked():
            try:
                x = int(event.xdata)
                y = int(event.ydata)
                self.canvas_right.plotHyper(self.img_instance.values, x, y)
            except:
                self.canvas_right.blank_plot()

    def deselect_all_buttons(self):
        self.canvas_right.blank_plot()
        self.button1.setChecked(False)
        self.button2.setChecked(False)
        self.button3.setChecked(False)
        self.button4.setChecked(False)
        self.button5.setChecked(False)
        self.canvas_left.plot_image(self.img)
        self.imgMask = self.img.copy()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        fig.tight_layout()

        super(PlotCanvas, self).__init__(fig)
        self.setParent(parent)

    def blank_plot(self):
        self.axes.clear()
        self.draw()

    def plot_image(self, img):
        self.axes.clear()
        self.axes.imshow(img)
        self.axes.axis('off')
        self.draw()

    def random_plot(self):
        x = np.random.rand(50) * 100
        y = np.random.rand(50) * 100
        colors = np.random.rand(50)
        area = (30 * np.random.rand(50))**2
        
        self.axes.clear()
        self.axes.scatter(x, y, s=area, c=colors, alpha=0.5)
        self.draw()
    
    def plotHyper(self, values, x_coor, y_coor):
        x = wavelengths
        y = values[x_coor, y_coor]
        self.axes.clear()
        for i in range(1, len(x)):
            self.axes.plot(x[i-1:i+1], y[i-1:i+1], color=wavelength_to_rgb(x[i]), alpha=0.5)
            self.axes.fill_between(x[i-1:i+1], 0, y[i-1:i+1], color=wavelength_to_rgb(x[i]), alpha=0.3)
        self.axes.set_xlabel("Longitud de onda")
        self.axes.set_ylabel("Valor del pixel")
        self.draw()

    def plotAreaHyper(self, values):
        x = wavelengths
        minVals = []
        maxVals = []
        meanVals = []
        for i in range(len(x)):
            minVals.append(values[i].min())
            maxVals.append(values[i].max())
            meanVals.append(values[i].mean())
        self.axes.clear()
        for i in range(1, len(x)):
            self.axes.plot(x[i-1:i+1], minVals[i-1:i+1], color=wavelength_to_rgb(x[i]), linestyle='--', alpha=0.5)
            self.axes.plot(x[i-1:i+1], maxVals[i-1:i+1], color=wavelength_to_rgb(x[i]), linestyle='--', alpha=0.5)
            self.axes.plot(x[i-1:i+1], meanVals[i-1:i+1], color=wavelength_to_rgb(x[i]), linewidth=2.5, alpha=0.5)
            self.axes.fill_between(x[i-1:i+1], minVals[i-1:i+1], maxVals[i-1:i+1], color=wavelength_to_rgb(x[i]), alpha=0.1)
        self.axes.set_xlabel("Longitud de onda")
        self.axes.set_ylabel("Valores de\nlos pixeles")
        self.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())