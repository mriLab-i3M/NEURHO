import numpy as np
import scipy.io as sp
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel,
                             QListWidget, QListWidgetItem, QPushButton, QApplication,
                             QFileDialog, QTabWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from matplotlib.backend_bases import MouseEvent
import qdarkstyle
from matplotlib import style
import sys
import nibabel as nib

import configs.hw_config as hw

# --- Clase para la Lupa (MagnifierWindow) ---
class MagnifierWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Lupa")
        self.setFixedSize(400, 400)
        self.move(0,0)
        layout = QVBoxLayout(self)

        self.canvas = FigureCanvas(plt.Figure(figsize=(2, 2)))
        self.canvas.setFixedSize(375, 300)
        layout.addWidget(self.canvas)

        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Amplificación:")
        zoom_layout.addWidget(zoom_label)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(300)
        self.zoom_slider.setMaximum(1000)
        self.zoom_slider.setValue(300)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(50)
        zoom_layout.addWidget(self.zoom_slider)
        layout.addLayout(zoom_layout)

        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

    def closeEvent(self, event):
        if self.parent():
            self.parent().on_magnifier_closed()
        event.accept()

    def update_view(self, img_crop, zoom_factor):
        self.canvas.figure.clf()
        ax = self.canvas.figure.add_subplot(111)
        ax.imshow(img_crop, cmap='gray', interpolation='nearest')
        center_row, center_col = img_crop.shape[0] / 2, img_crop.shape[1] / 2
        ax.axhline(y=center_row, color='r', linestyle='--')
        ax.axvline(x=center_col, color='r', linestyle='--')
        ax.axis('off')
        self.canvas.draw()

# --- Clases para el ListBox personalizado ---
class QListWidgetItemWithButton(QWidget):
    def __init__(self, text, parent_listwidget, icon_path, delete_callback):
        super().__init__()
        self.parent_listwidget = parent_listwidget
        self.delete_callback = delete_callback
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 0, 0, 0)

        self.item_text = QPushButton(text)
        self.item_text.setStyleSheet("text-align:left; background-color:transparent; border:none;")
        self.item_text.clicked.connect(self.select_item)

        self.button_delete = QPushButton()
        self.button_delete.setIcon(QIcon(icon_path))
        self.button_delete.setIconSize(QSize(16, 16))
        self.button_delete.setFixedSize(20, 20)
        self.button_delete.setStyleSheet("border: none;")
        self.button_delete.clicked.connect(self.delete_item)

        self.layout.addWidget(self.item_text)
        self.layout.addWidget(self.button_delete)
        self.setLayout(self.layout)

    def delete_item(self):
        self.delete_callback(self)

    def select_item(self):
        self.parent_listwidget.setCurrentItem(self.listwidgetitem)

class CustomListWidget(QListWidget):
    def __init__(self, icon_path, delete_callback):
        super().__init__()
        self.icon_path = icon_path
        self.delete_callback = delete_callback

    def add_item_with_button(self, text):
        item_widget = QListWidgetItemWithButton(text, self, self.icon_path, self.delete_callback)
        item = QListWidgetItem(self)
        item.setSizeHint(item_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, item_widget)
        item_widget.listwidgetitem = item
        return item

# --- Clase principal del Explorador de Cortes 3D ---
class ExploradorCortes3D(QWidget):
    def __init__(self):
        super().__init__()

        # Variables de imagen y configuración inicial
        self.load_button = None
        self.canvas = None
        self.label = None
        self.slider = None

        # Se crean tres volúmenes con las transposiciones indicadas
        # Axial: (2,1,0); Sagital: (1,0,2); Coronal: (2,0,1)
        self.image_axial = None
        self.image_sagital = None
        self.image_coronal = None
        # Se usa la vista axial para cálculos de coordenadas
        self.imagen = None
        self.num_cortes = 0
        self.resolution = np.array([1.0, 1.0, 1.0])

        # Gestión de puntos: cada punto es [corte, x, y, estilo]
        self.puntos = []
        self.puntos_real = []
        self.selected_point = None
        self.dragging = False
        # Bandera para saber si se acaba de agregar un nuevo punto
        self.new_point_flag = False

        # Canvases para vistas adicionales (sagital y coronal)
        self.canvas_sagital = None
        self.canvas_coronal = None

        # Ventana de lupa
        self.magnifier_window = None

        self.initUI()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        style.use('dark_background')

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select Image File", "",
            "Image Files (*.nii *.nii.gz);;All Files (*)", options=options)
        if file_path:
            nifti_img = nib.load(file_path)
            image_data = nifti_img.get_fdata()
            # Se crean los tres volúmenes con las transposiciones indicadas
            self.image_axial = np.transpose(image_data, axes=(2, 1, 0))
            self.image_sagital = np.transpose(image_data, (1, 0, 2))
            self.image_coronal = np.transpose(image_data, (2, 0, 1))
            # Para cálculos de coordenadas se usa la vista axial
            self.imagen = self.image_axial
            self.resolution = np.abs(nifti_img.header.get_zooms())
            self.resolution = self.resolution[[2, 1, 0]]
            self.num_cortes = self.image_axial.shape[0]
            self.slider.setMaximum(self.num_cortes - 1)
            self.slider.setValue(int(self.num_cortes // 2))
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()

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
        resolution = self.resolution
        axes = ['x', 'y', 'z']
        nx, ny, nz = self.imagen.shape
        coord = [0.0, 0.0, 0.0]
        coord[0] = (pixel[0] - nx/2) * resolution[0]
        coord[1] = (pixel[2] - ny/2) * resolution[1]
        coord[2] = - (pixel[1] - nz/2) * resolution[2]
        if item is not None:
            item.setText(
                f"Corte: {pixel[0]}, X: {pixel[1]}, Y: {pixel[2]} || "
                f"{axes[0]}: {coord[0]:0.1f} mm, {axes[1]}: {coord[1]:0.1f} mm, {axes[2]}: {coord[2]:0.1f} mm"
            )
        return coord

    def agregar_item_lista(self, corte, x, y, coordinates):
        texto = (f'Corte: {corte}, X: {x}, Y: {y} || '
                 f'x: {coordinates[0]:.1f} mm, y: {coordinates[1]:.1f} mm, z: {coordinates[2]:.1f} mm')
        self.lista_coordenadas.add_item_with_button(texto)

    def initUI(self):
        self.setWindowTitle('Explorador de Cortes 3D')
        self.setGeometry(100, 100, 1420, 940)

        main_layout = QHBoxLayout()

        # Panel Izquierdo: Vista Axial
        axial_widget = QWidget()
        axial_layout = QVBoxLayout(axial_widget)

        self.load_button = QPushButton("Load image")
        axial_layout.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_file)

        self.canvas = FigureCanvas(plt.Figure(figsize=(8,8)))
        axial_layout.addWidget(self.canvas)

        slider_layout = QHBoxLayout()
        self.label = QLabel('Corte: 0')
        slider_layout.addWidget(self.label)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.num_cortes - 1)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.actualizar_imagen)
        slider_layout.addWidget(self.slider)
        axial_layout.addLayout(slider_layout)

        self.lista_coordenadas = CustomListWidget("resources/icons/basura.png", self.eliminar_punto_item)
        self.lista_coordenadas.itemSelectionChanged.connect(self.on_coordinates_selection_changed)
        row_height = self.lista_coordenadas.sizeHintForRow(0) if self.lista_coordenadas.count() > 0 else 30
        self.lista_coordenadas.setFixedHeight(row_height * 4 + 2 * self.lista_coordenadas.frameWidth())
        axial_layout.addWidget(self.lista_coordenadas)

        main_layout.addWidget(axial_widget, 1)

        # Panel Derecho: Vistas Sagital y Coronal en Tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        tab_widget = QTabWidget()
        #tab_widget.setFixedHeight(self.canvas.sizeHint().height())
        tab_widget.setFixedSize(700, 750)
        sagital_tab = QWidget()
        sagital_layout = QVBoxLayout(sagital_tab)
        self.canvas_sagital = FigureCanvas(plt.Figure(figsize=(4,4)))
        sagital_layout.addWidget(self.canvas_sagital)
        tab_widget.addTab(sagital_tab, "Sagital")

        coronal_tab = QWidget()
        coronal_layout = QVBoxLayout(coronal_tab)
        self.canvas_coronal = FigureCanvas(plt.Figure(figsize=(4,4)))
        coronal_layout.addWidget(self.canvas_coronal)
        tab_widget.addTab(coronal_tab, "Coronal")

        right_layout.addWidget(tab_widget)

        brightness_layout = QHBoxLayout()
        brightness_label = QLabel("Brillo:")
        brightness_layout.addWidget(brightness_label)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(50)
        self.brightness_slider.setTickPosition(QSlider.TicksBelow)
        self.brightness_slider.setTickInterval(10)
        self.brightness_slider.valueChanged.connect(self.on_brightness_change)
        brightness_layout.addWidget(self.brightness_slider)
        right_layout.addLayout(brightness_layout)

        contrast_layout = QHBoxLayout()
        contrast_label = QLabel("Contraste:")
        contrast_layout.addWidget(contrast_label)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(50)
        self.contrast_slider.setTickPosition(QSlider.TicksBelow)
        self.contrast_slider.setTickInterval(10)
        self.contrast_slider.valueChanged.connect(self.on_contrast_change)
        contrast_layout.addWidget(self.contrast_slider)
        right_layout.addLayout(contrast_layout)

        self.info_box = CustomListWidget("resources/icons/basura.jpg", lambda widget: None)
        row_height_info = self.info_box.sizeHintForRow(0) if self.info_box.count() > 0 else 30
        self.info_box.setFixedHeight(row_height_info * 2 + 2 * self.info_box.frameWidth())
        right_layout.addWidget(self.info_box)

        main_layout.addWidget(right_widget, 1)
        self.setLayout(main_layout)

        self.actualizar_imagen()
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)



    def apply_brightness_contrast(self, img):
        brillo = self.brightness_slider.value() / 50.0
        contraste = self.contrast_slider.value() / 50.0
        mean_val = np.mean(img)
        adjusted = (img - mean_val) * contraste + mean_val
        adjusted *= brillo
        return adjusted

    def on_contrast_change(self):
        self.actualizar_imagen()
        self.actualizar_imagen_sagital()
        self.actualizar_imagen_coronal()

    def on_brightness_change(self):
        self.actualizar_imagen()
        self.actualizar_imagen_sagital()
        self.actualizar_imagen_coronal()

    def actualizar_imagen(self):
        indice_corte = self.slider.value()
        self.label.setText(f'Corte: {indice_corte}')
        imagen_corte = self.obtener_imagen(indice_corte)
        if imagen_corte is not None:
            self.canvas.figure.clf()
            ax = self.canvas.figure.add_subplot(111)
            imagen_ajustada = self.apply_brightness_contrast(imagen_corte)
            vmin = np.min(imagen_corte)
            vmax = np.max(imagen_corte)
            ax.imshow(imagen_ajustada, cmap='gray', interpolation='bilinear',
                      aspect='auto', vmin=vmin, vmax=vmax)
            ax.set_facecolor('black')
            ax.set_title(f'Corte {indice_corte}', color='white')
            ax.axis('off')
            self.canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            for corte, x, y, color in self.puntos:
                if corte == indice_corte:
                    roi = patches.Circle((x, y), radius=hw.v_radio, color=color[0], fill=False, linewidth=2)
                    ax.plot(x, y, color, markersize=10)
                    ax.add_patch(roi)
            self.canvas.draw()
        self.actualizar_imagen_sagital()
        self.actualizar_imagen_coronal()

    def obtener_imagen(self, indice_corte):
        if 0 <= indice_corte < self.num_cortes:
            return self.image_axial[indice_corte, :, :]
        return None

    def actualizar_imagen_sagital(self):
        if self.image_sagital is not None:
            self.canvas_sagital.figure.clf()
            ax = self.canvas_sagital.figure.add_subplot(111)
            if self.selected_point is not None:
                # En vista sagital, se utiliza la coordenada X del punto (axial)
                x_index = int(round(self.selected_point[1]))
            else:
                x_index = self.image_sagital.shape[1] // 2
            image_sagital = self.image_sagital[:, x_index, :]
            imagen_ajustada = self.apply_brightness_contrast(image_sagital)
            vmin = np.min(image_sagital)
            vmax = np.max(image_sagital)
            ax.imshow(imagen_ajustada, cmap='gray', interpolation='bilinear',
                      aspect='auto', vmin=vmin, vmax=vmax)
            ax.set_facecolor('black')
            ax.set_title(f"Sagital (Columna = {x_index})", color='white')
            ax.axis('off')
            self.canvas_sagital.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            if self.selected_point is not None and int(round(self.selected_point[1])) == x_index:
                # Se dibuja el punto convertido para vista sagital: (axial_slice, axial_y)
                ax.plot(self.selected_point[0], self.selected_point[2], 'ro', markersize=10)
            self.canvas_sagital.draw()

    def actualizar_imagen_coronal(self):
        if self.image_coronal is not None:
            self.canvas_coronal.figure.clf()
            ax = self.canvas_coronal.figure.add_subplot(111)
            if self.selected_point is not None:
                # En vista coronal, se utiliza la coordenada Y del punto (axial)
                y_index = int(round(self.selected_point[2]))
            else:
                y_index = self.image_coronal.shape[2] // 2
            image_coronal = self.image_coronal[:, :, y_index]
            imagen_ajustada = self.apply_brightness_contrast(image_coronal)
            vmin = np.min(image_coronal)
            vmax = np.max(image_coronal)
            ax.imshow(imagen_ajustada, cmap='gray', interpolation='bilinear',
                      aspect='auto', vmin=vmin, vmax=vmax)
            ax.set_facecolor('black')
            ax.set_title(f"Coronal (Fila = {y_index})", color='white')
            ax.axis('off')
            self.canvas_coronal.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            if self.selected_point is not None and int(round(self.selected_point[2])) == y_index:
                # Para la vista coronal se invierten los ejes: se dibuja (axial_x, axial_slice)
                ax.plot(self.selected_point[1], self.selected_point[0], 'ro', markersize=10)
            self.canvas_coronal.draw()

    def on_click(self, event: MouseEvent):
        if event.inaxes is not None:
            x, y = round(event.xdata, 1), round(event.ydata, 1)
            corte_actual = self.slider.value()
            clicked_point = self.get_clicked_point(corte_actual, x, y)
            if clicked_point:
                self.selected_point = clicked_point
                self.selected_point[3] = 'ro'
                self.seleccionar_punto_en_lista(self.selected_point)
            else:
                self.agregar_punto(corte_actual, x, y)
                self.selected_point = self.puntos[-1]
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()
            self.update_magnifier()  # Mostrar o actualizar la lupa al seleccionar un punto
    def seleccionar_punto_en_lista(self, punto):
        texto_buscar = f'Corte: {punto[0]}, X: {punto[1]}, Y: {punto[2]}'
        for index in range(self.lista_coordenadas.count()):
            item = self.lista_coordenadas.item(index)
            widget = self.lista_coordenadas.itemWidget(item)
            if widget.item_text.text().startswith(texto_buscar):
                self.lista_coordenadas.setCurrentItem(item)
                break
    def on_coordinates_selection_changed(self):
        item = self.lista_coordenadas.currentItem()
        if item:
            widget = self.lista_coordenadas.itemWidget(item)
            texto = widget.item_text.text()
            original, _ = texto.split(" || ")
            partes = original.split(',')
            corte = float(partes[0].split(':')[1].strip())
            x = float(partes[1].split(':')[1].strip())
            y = float(partes[2].split(':')[1].strip())
            self.slider.setValue(int(corte))
            self.actualizar_imagen()
            self.selected_point = self.get_clicked_point(corte, x, y)
            if self.selected_point:
                self.selected_point[3] = 'ro'
            for p in self.puntos:
                if p!=self.selected_point:
                    p[3] = 'yo'
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()


    def get_clicked_point(self, corte, x, y, tolerance=1):
        for punto in self.puntos:
            if punto[0] == corte and abs(punto[1] - x) <= tolerance and abs(punto[2] - y) <= tolerance:
                return punto
        return None

    def on_drag(self, event: MouseEvent):
        if self.selected_point and event.inaxes is not None and event.button==1:
            new_x, new_y = round(event.xdata, 1), round(event.ydata, 1)
            self.selected_point[1] = new_x
            self.selected_point[2] = new_y
            self.selected_point[3] = 'r+'
            self.dragging = True
            self.actualizar_coordenadas()
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()
            self.update_magnifier()  # Actualizar la lupa durante el arrastre
        elif self.dragging and event.button!=1:
            if self.selected_point:
                if self.is_point_selected_in_list(self.selected_point):
                    self.selected_point[3] = 'ro'
                else:
                    self.selected_point[3] = 'yo'
            self.dragging = False
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()

    def is_point_selected_in_list(self, punto):
        selected_item = self.lista_coordenadas.currentItem()
        if selected_item:
            widget = self.lista_coordenadas.itemWidget(selected_item)
            texto = widget.item_text.text()
            original, _ = texto.split(" || ")
            partes = original.split(',')
            corte = float(partes[0].split(':')[1].strip())
            x = float(partes[1].split(':')[1].strip())
            y = float(partes[2].split(':')[1].strip())
            return punto[0] == corte and punto[1] == x and punto[2] == y
        return False
    def agregar_punto(self, corte, x, y):
        # Solo se pueden marcar tres puntos
        if len(self.puntos) < 3:
            self.puntos.append([corte, x, y, 'yo'])
            coordinates = self.pixel2coord([corte, x, y])
            self.puntos_real.append(coordinates)
            self.agregar_item_lista(corte, x, y, coordinates)
            # Se activa la bandera al agregar un nuevo punto
            self.new_point_flag = True
        else:
            # Si ya hay tres puntos, no se agrega ninguno y se desactiva la bandera
            self.new_point_flag = False

    def actualizar_coordenadas(self):
        for i, punto in enumerate(self.puntos):
            if punto == self.selected_point:
                item = self.lista_coordenadas.item(i)
                widget = self.lista_coordenadas.itemWidget(item)
                nx, ny, nz = self.imagen.shape
                corte, x, y = punto[0], punto[1], punto[2]
                coord_x = (corte - nx/2) * self.resolution[0]
                coord_y = (y - ny/2) * self.resolution[1]
                coord_z = - (x - nz/2) * self.resolution[2]
                texto = f'Corte: {corte}, X: {x}, Y: {y} || x: {coord_x:.1f} mm, y: {coord_y:.1f} mm, z: {coord_z:.1f} mm'
                if widget is not None:
                    widget.item_text.setText(texto)
                self.puntos[i][0:3] = punto[0:3]
                self.puntos_real[i] = [coord_x, coord_y, coord_z]

    def mostrar_punto_seleccionado(self):
        self.on_coordinates_selection_changed()

    def eliminar_punto_item(self, item_widget):
        texto = item_widget.item_text.text()
        partes = texto.split(" || ")[0].split(',')
        corte = int(partes[0].split(':')[1].strip())
        x = float(partes[1].split(':')[1].strip())
        y = float(partes[2].split(':')[1].strip())
        punto_a_eliminar = None
        index_to_remove = None
        tolerance = 0.1  # Tolerancia para la comparación de coordenadas
        for i, punto in enumerate(self.puntos):
            if punto[0]==corte and abs(punto[1] - x) < tolerance and abs(punto[2] - y) < tolerance:
                punto_a_eliminar = punto
                index_to_remove = i
                break
        if punto_a_eliminar is not None:
            if self.selected_point==punto_a_eliminar:
                self.selected_point = None
            self.puntos.remove(punto_a_eliminar)
            if index_to_remove is not None and index_to_remove < len(self.puntos_real):
                self.puntos_real.pop(index_to_remove)
            row = self.lista_coordenadas.row(item_widget.listwidgetitem)
            self.lista_coordenadas.takeItem(row)
            self.actualizar_imagen()
            self.actualizar_imagen_sagital()
            self.actualizar_imagen_coronal()


    # --- Actualización de la ventana de lupa ---
    def update_magnifier(self):
        indice_corte = self.slider.value()
        img_slice = self.obtener_imagen(indice_corte)
        if img_slice is None or self.selected_point is None:
            return
        px = int(round(self.selected_point[1]))
        py = int(round(self.selected_point[2]))
        crop_size = 100
        half_crop = crop_size // 2
        rows, cols = img_slice.shape
        r0 = max(py - half_crop, 0)
        r1 = min(py + half_crop, rows)
        c0 = max(px - half_crop, 0)
        c1 = min(px + half_crop, cols)
        img_crop = img_slice[r0:r1, c0:c1]

        from scipy.ndimage import zoom
        factor = self.magnifier_window.zoom_slider.value() / 100.0 if self.magnifier_window else 3.0
        img_zoomed = zoom(img_crop, (factor, factor), order=1)

        offset_y = py - r0
        offset_x = px - c0
        zoomed_y = offset_y * factor
        zoomed_x = offset_x * factor

        final_size = 200
        half_final = final_size // 2
        crop_start_row = int(round(zoomed_y - half_final))
        crop_start_col = int(round(zoomed_x - half_final))

        zoomed_rows, zoomed_cols = img_zoomed.shape
        if crop_start_row < 0:
            crop_start_row = 0
        if crop_start_col < 0:
            crop_start_col = 0
        if crop_start_row + final_size > zoomed_rows:
            crop_start_row = zoomed_rows - final_size
        if crop_start_col + final_size > zoomed_cols:
            crop_start_col = zoomed_cols - final_size

        img_final = img_zoomed[crop_start_row:crop_start_row+final_size,
                               crop_start_col:crop_start_col+final_size]

        if self.magnifier_window is None:
            self.magnifier_window = MagnifierWindow(self)
            #pos = self.canvas_sagital.mapToGlobal(self.canvas_sagital.rect().topLeft())
            #self.magnifier_window.move(pos.x() + 20, pos.y() + 20)
            self.magnifier_window.show()
            self.magnifier_window.move(20,315)
            self.magnifier_window.close_button.clicked.connect(self.on_magnifier_closed)
            self.magnifier_window.zoom_slider.valueChanged.connect(self.update_magnifier)

        self.magnifier_window.update_view(img_final, factor)

    def on_magnifier_closed(self):
        if self.magnifier_window:
            self.magnifier_window.close()
            self.magnifier_window = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExploradorCortes3D()
    window.show()
    sys.exit(app.exec_())
