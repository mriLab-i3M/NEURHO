import numpy as np
import scipy.io as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QHBoxLayout, QListWidget, QPushButton, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from matplotlib.backend_bases import MouseEvent
import qdarkstyle
from matplotlib import style
import sys
import configs.hw_config as hw


class ExploradorCortes3D(QWidget):
    def __init__(self, archivo):
        super().__init__()

        # Cargar el archivo .mat
        self.datos_mat = sp.loadmat(archivo)
        self.imagen = np.abs(self.datos_mat['image3D'])
        self.ejes = self.datos_mat['axesOrientation'][0]
        self.num_cortes = self.imagen.shape[0]

        # Fix image orientation
        if np.array_equal(self.ejes, [2, 1, 0]):
            self.imagen = self.imagen[:, ::-1, ::-1]
        elif np.array_equal(self.ejes, [1, 2, 0]):
            # TODO: fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [2, 1, 0]")
        elif np.array_equal(self.ejes, [0, 1, 2]):
            self.imagen = np.transpose(self.imagen, axes=(0, 2, 1))
            self.imagen = self.imagen[:, ::-1, ::-1]
        elif np.array_equal(self.ejes, [1, 0, 2]):
            # TODO: fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [0, 1, 2]")
        elif np.array_equal(self.ejes, [0, 2, 1]):
            self.imagen = np.transpose(self.imagen, axes=(0, 2, 1))
            self.imagen = self.imagen[::-1, ::-1, ::-1]
        elif np.array_equal(self.ejes, [2, 0, 1]):
            # TODO: fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [0, 2, 1]")

        # Inicialización de variables
        self.puntos = []
        self.puntos_real = []
        self.selected_point = None
        self.dragging = False

        # Configuración de la interfaz de usuario
        self.initUI()

        # Establecer el estilo Qt
        self.styleSheet = qdarkstyle.load_stylesheet_pyqt5()
        self.setStyleSheet(self.styleSheet)

        # Establecer el estilo de Matplotlib
        style.use('dark_background')  # Esto aplica un fondo oscuro y colores claros en los gráficos

    def pixel2coord(self, pixel, item=None):
        """
        Converts pixel coordinates to real-world coordinates based on resolution
        and axis orientation.

        Parameters:
        pixel (tuple or list): A 3-element iterable representing the pixel coordinates
                               (slice, px, py) in the image matrix.

        Returns:
        list: A 3-element list representing the real-world coordinates (x, y, z).

        Note:
        - `self.datos_mat['resolution']` should be a list or tuple containing the
          voxel size in readout, phase and slice directions.
        - `self.datos_mat['axesOrientation']` should define the mapping between
          pixel indices and coordinate system axes.

        Example:
        If resolution is [0.5, 0.5, 1.0] and axesOrientation is [2, 0, 1], then:
            pixel2coord([10, 20, 30]) -> [15.0, 10.0, 10.0]
        """
        resolution = self.datos_mat['resolution'][0]
        axes = self.datos_mat['axesOrientation'][0]
        mapping = {0: 'x', 1: 'y', 2: 'z'}
        axes_2 = [mapping[n] for n in axes]
        nsl, nph, nrd = self.imagen.shape
        coord = [0.0, 0.0, 0.0]
        if np.array_equal(axes, [2, 1, 0]):  # Transversal
            coord[axes[2]] = + (pixel[0] - nsl / 2) * resolution[2]  # x-axis
            coord[axes[0]] = - (pixel[1] - nrd / 2) * resolution[0]  # z-axis
            coord[axes[1]] = + (pixel[2] - nph / 2) * resolution[1]  # y-axis
        elif np.array_equal(axes, [1, 2, 0]):
            # TODO: Fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [2, 1, 0]")
        elif np.array_equal(axes, [0, 1, 2]):  # Sagittal
            coord[axes[2]] = + (pixel[0] - nsl / 2) * resolution[2]  # z-axis
            coord[axes[1]] = + (pixel[1] - nph / 2) * resolution[1]  # y-axis
            coord[axes[0]] = - (pixel[2] - nrd / 2) * resolution[0]  # x-axis
        elif np.array_equal(axes, [1, 0, 2]):
            # TODO: Fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [1, 0, 2]")
        elif np.array_equal(axes, [0, 2, 1]):  # Coronal
            coord[axes[2]] = + (pixel[0] - nsl / 2) * resolution[2]  # y-axis
            coord[axes[1]] = - (pixel[1] - nph / 2) * resolution[1]  # z-axis
            coord[axes[0]] = - (pixel[2] - nrd / 2) * resolution[0]  # x-axis
        elif np.array_equal(axes, [1, 0, 2]):
            # TODO: Fix image orientation
            print("WARNING: Image orientation may be wrong: please use image orientation [0, 2, 1]")

        if item == None:
            self.lista_coordenadas.addItem(f"Corte: {pixel[0]}, X: {pixel[1]}, Y: {pixel[2]} || " +
                "%s: %0.0f mm, %s: %0.0f mm, %s: %0.0f mm" % (axes_2[0], coord[0] * 1e3,
                                                              axes_2[1], coord[1] * 1e3,
                                                              axes_2[2], coord[2] * 1e3))
        else:
            item.setText(f"Corte: {pixel[0]}, X: {pixel[1]}, Y: {pixel[2]} || " +
                "%s: %0.0f mm, %s: %0.0f mm, %s: %0.0f mm" % (axes_2[0], coord[0] * 1e3,
                                                              axes_2[1], coord[1] * 1e3,
                                                              axes_2[2], coord[2] * 1e3))

        return coord

    def initUI(self):
        self.setWindowTitle('Explorador de Cortes 3D')
        self.setGeometry(100, 100, 1200, 600)

        layout = QHBoxLayout()

        # Layout para la imagen
        self.imagen_layout = QVBoxLayout()
        self.canvas = FigureCanvas(plt.Figure(figsize=(8, 8)))
        self.imagen_layout.addWidget(self.canvas)

        # Barra de desplazamiento
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.num_cortes - 1)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.actualizar_imagen)

        # Etiqueta del corte
        self.label = QLabel('Corte: 0')

        # Layout para slider y etiqueta
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.label)
        slider_layout.addWidget(self.slider)
        self.imagen_layout.addLayout(slider_layout)

        # Añadir la imagen al layout principal
        layout.addLayout(self.imagen_layout)

        # Contenedor para los botones de la lista
        listbox_layout = QVBoxLayout()

        # Layout para botones de ordenar
        botones_layout = QHBoxLayout()

        # Botón eliminar
        self.boton_eliminar = QPushButton()
        self.boton_eliminar.setIcon(QIcon("resources/icons/basura.png"))
        self.boton_eliminar.setText('')
        self.boton_eliminar.setFixedSize(80, 80)
        self.boton_eliminar.clicked.connect(self.eliminar_punto)
        botones_layout.addWidget(self.boton_eliminar)

        # Botón ordenar ascendente
        self.boton_ordenar_asc = QPushButton()
        self.boton_ordenar_asc.setIcon(QIcon("resources/icons/ord_asc.png"))
        self.boton_ordenar_asc.setText('')
        self.boton_ordenar_asc.setFixedSize(80, 80)
        self.boton_ordenar_asc.clicked.connect(self.ordenar_ascendente)
        botones_layout.addWidget(self.boton_ordenar_asc)

        # Botón ordenar descendente
        self.boton_ordenar_desc = QPushButton()
        self.boton_ordenar_desc.setIcon(QIcon("resources/icons/ord_dsc.png"))
        self.boton_ordenar_desc.setText('')
        self.boton_ordenar_desc.setFixedSize(80, 80)
        self.boton_ordenar_desc.clicked.connect(self.ordenar_descendente)
        botones_layout.addWidget(self.boton_ordenar_desc)

        listbox_layout.addLayout(botones_layout)

        # ListBox de coordenadas
        self.lista_coordenadas = QListWidget()
        self.lista_coordenadas.itemSelectionChanged.connect(self.mostrar_punto_seleccionado)
        listbox_layout.addWidget(self.lista_coordenadas)

        # Añadir layout de lista con botones al layout principal
        layout.addLayout(listbox_layout)

        # Mostrar la imagen inicial
        self.actualizar_imagen()

        # Establecer el layout principal
        self.setLayout(layout)

        # Conectar eventos de clic y arrastre
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)

    def actualizar_imagen(self):
        """Actualiza la imagen según el valor del slider."""
        indice_corte = self.slider.value()
        self.label.setText(f'Corte: {indice_corte}')
        imagen_corte = self.obtener_imagen(indice_corte)

        if imagen_corte is not None:
            self.canvas.figure.clf()  # Limpiar la figura
            ax = self.canvas.figure.add_subplot(111)

            # Mostrar la imagen con fondo negro
            ax.imshow(imagen_corte, cmap='gray', interpolation='none', aspect='auto')  # Sin interpolación y ajustada
            ax.set_facecolor('black')  # Fondo negro
            ax.set_title(f'Corte {indice_corte}', color='white')  # Título blanco
            ax.axis('off')  # Eliminar los ejes

            # Ajustar la imagen al tamaño del canvas
            self.canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

            # Dibujar los puntos
            for punto in self.puntos:
                corte, x, y, color = punto
                if corte == indice_corte:
                    ax.plot(x, y, color, markersize=10)

            self.canvas.draw()

    def obtener_imagen(self, indice_corte):
        """Devuelve una porción 2D de la imagen 3D para el índice especificado."""
        if indice_corte < 0 or indice_corte >= self.num_cortes:
            return None
        return self.imagen[indice_corte, :, :]

    def on_click(self, event: MouseEvent):
        """Maneja el evento de clic sobre la imagen."""
        if event.inaxes is not None:
            x, y = int(event.xdata), int(event.ydata)
            corte_actual = self.slider.value()
            clicked_point = self.get_clicked_point(corte_actual, x, y)

            if clicked_point:
                self.selected_point = clicked_point
                self.selected_point[3] = 'ro'
                self.seleccionar_punto_en_lista(self.selected_point)
            else:
                self.agregar_punto(corte_actual, x, y)

            self.actualizar_imagen()

    def seleccionar_punto_en_lista(self, punto):
        """Selecciona el item correspondiente al punto en la lista."""
        texto = f'Corte: {punto[0]}, X: {punto[1]}, Y: {punto[2]}'

        for index in range(self.lista_coordenadas.count()):
            item = self.lista_coordenadas.item(index)
            if item.text() == texto:
                self.lista_coordenadas.setCurrentItem(item)
                break

    def get_clicked_point(self, corte, x, y, tolerance=1):
        """Verifica si el clic fue sobre un punto cercano a las coordenadas dadas."""
        for punto in self.puntos:
            if punto[0] == corte and abs(punto[1] - x) <= tolerance and abs(punto[2] - y) <= tolerance:
                return punto
        return None

    def on_drag(self, event: MouseEvent):
        """Maneja el evento de arrastre del punto."""
        if self.selected_point and event.inaxes is not None and event.button == 1:
            new_x, new_y = int(event.xdata), int(event.ydata)
            self.selected_point[1] = new_x
            self.selected_point[2] = new_y
            self.selected_point[3] = 'r+'
            self.dragging = True
            self.actualizar_coordenadas()
            self.actualizar_imagen()

        elif self.dragging and not event.button == 1:
            if self.selected_point:
                is_selected_in_list = self.is_point_selected_in_list(self.selected_point)
                if is_selected_in_list:
                    self.selected_point[3] = 'ro'
                else:
                    self.selected_point[3] = 'yo'
            self.dragging = False
            self.actualizar_imagen()

    def is_point_selected_in_list(self, punto):
        """Verifica si el punto está seleccionado en la lista."""
        selected_item = self.lista_coordenadas.currentItem()
        if selected_item:
            texto = selected_item.text()
            original, _ = texto.split(" || ")
            partes = original.split(',')
            corte = int(partes[0].split(':')[1].strip())
            x = int(partes[1].split(':')[1].strip())
            y = int(partes[2].split(':')[1].strip())
            return punto[0] == corte and punto[1] == x and punto[2] == y
        return False

    def agregar_punto(self, corte, x, y):
        """Agrega un nuevo punto a la lista y lo dibuja en la imagen."""
        if len(self.puntos) < 3:
            self.puntos.append([corte, x, y, 'yo'])
            coordinates = self.pixel2coord([corte, x, y])
            self.puntos_real.append(coordinates)

    def actualizar_coordenadas(self):
        """Actualiza las coordenadas del punto movido en el ListBox."""
        for i, punto in enumerate(self.puntos):
            if punto == self.selected_point:
                item = self.lista_coordenadas.item(i)
                item.setText(f'Corte: {punto[0]}, X: {punto[1]}, Y: {punto[2]}')
                self.puntos[i][0:3] = punto[0:3]
                self.puntos_real[i] = self.pixel2coord([punto[0], punto[1], punto[2]], item=item)

    def mostrar_punto_seleccionado(self):
        """Muestra el punto seleccionado del ListBox en la imagen."""
        item = self.lista_coordenadas.currentItem()
        if item:
            texto = item.text()
            original, _ = texto.split(" || ")
            partes = original.split(',')
            corte = int(partes[0].split(':')[1].strip())
            x = int(partes[1].split(':')[1].strip())
            y = int(partes[2].split(':')[1].strip())

            self.slider.setValue(corte)
            self.actualizar_imagen()

            self.selected_point = self.get_clicked_point(corte, x, y)
            if self.selected_point:
                self.selected_point[3] = 'ro'

            for punto in self.puntos:
                if punto != self.selected_point:
                    punto[3] = 'yo'

            self.actualizar_imagen()

    def eliminar_punto(self):
        """Elimina el punto seleccionado en el ListBox y en la lista de puntos."""
        item = self.lista_coordenadas.currentItem()
        if item:
            texto = item.text()
            original, _ = texto.split(" || ")
            partes = original.split(',')
            corte = int(partes[0].split(':')[1].strip())
            x = int(partes[1].split(':')[1].strip())
            y = int(partes[2].split(':')[1].strip())

            punto_a_eliminar = None
            n = 0
            for punto in self.puntos:
                if punto[0] == corte and punto[1] == x and punto[2] == y:
                    punto_a_eliminar = punto
                    break
                n += 1

            if punto_a_eliminar:
                self.puntos.remove(punto_a_eliminar)
                self.puntos_real.remove(self.puntos_real[n])
                self.lista_coordenadas.takeItem(self.lista_coordenadas.row(item))
                self.actualizar_imagen()

    def ordenar_ascendente(self):
        """Ordena los puntos en orden ascendente y mantiene la selección del item."""
        selected_item = self.lista_coordenadas.currentItem()
        selected_text = selected_item.text() if selected_item else None
        self.puntos.sort(key=lambda p: (p[0], p[1], p[2]))
        self.actualizar_lista_coordenadas()
        if selected_text:
            self.reseleccionar_item(selected_text)

    def ordenar_descendente(self):
        """Ordena los puntos en orden descendente y mantiene la selección del item."""
        selected_item = self.lista_coordenadas.currentItem()
        selected_text = selected_item.text() if selected_item else None
        self.puntos.sort(key=lambda p: (p[0], p[1], p[2]), reverse=True)
        self.actualizar_lista_coordenadas()
        if selected_text:
            self.reseleccionar_item(selected_text)

    def reseleccionar_item(self, texto):
        """Vuelve a seleccionar un item de la lista por su texto."""
        for index in range(self.lista_coordenadas.count()):
            item = self.lista_coordenadas.item(index)
            if item.text() == texto:
                self.lista_coordenadas.setCurrentItem(item)
                break

    def actualizar_lista_coordenadas(self):
        """Actualiza el ListBox después de ordenar."""
        self.lista_coordenadas.clear()
        for punto in self.puntos:
            self.lista_coordenadas.addItem(f'Corte: {punto[0]}, X: {punto[1]}, Y: {punto[2]}')


if __name__=="__main__":
    app = QApplication(sys.argv)
    window = ExploradorCortes3D('RARE_TRA.mat')
    window.show()
    sys.exit(app.exec_())
