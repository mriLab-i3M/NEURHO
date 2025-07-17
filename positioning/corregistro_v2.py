import sys
import os
import json
import numpy as np
import nibabel as nib
import nibabel.nifti1 as nifti1
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QGridLayout, QGroupBox, QFileDialog, QMessageBox, QSizePolicy
)

import pyqtgraph as pg
import scipy.ndimage
import qdarkstyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter


class Corregistro3D(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setWindowTitle("Corregistro Multiplanar 3D - v4")
        self.resize(1400, 900)

        self.img1 = None
        self.img2 = None
        self.img2_path = None
        self.idx_axial = 0
        self.idx_sagittal = 0
        self.idx_coronal = 0

        # Caché para velocidad
        self.last_params = None
        self.cached_vol2 = None
        self.primera_carga = True

        self.init_ui()
        self.init_connections()

        #self.spacing_mm = (1.0, 1.0, 1.0)  # valor por defecto hasta cargar imagen

    def init_ui(self):
        from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QPushButton, \
            QGroupBox

        layout = QVBoxLayout(self)

        # — Botones de carga y guardado —
        btn_layout = QHBoxLayout()
        self.btn_cargar_fija = QPushButton("Cargar imagen fija")
        self.btn_cargar_fija.setFixedHeight(40)
        self.btn_cargar_transformar = QPushButton("Cargar imagen a transformar")
        self.btn_cargar_transformar.setFixedHeight(40)
        self.btn_guardar = QPushButton("Guardar transformación")
        self.btn_guardar.setFixedHeight(40)
        btn_layout.addWidget(self.btn_cargar_fija)
        btn_layout.addWidget(self.btn_cargar_transformar)
        btn_layout.addWidget(self.btn_guardar)
        layout.addLayout(btn_layout)

        # — Vistas multiplanares —
        viewer_layout = QGridLayout()

        # Axial
        self.axial_view = pg.ImageView()
        self._hide_ui(self.axial_view)
        self.axial_view.ui.graphicsView.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.axial_view.ui.graphicsView.setRenderHint(QPainter.Antialiasing, True)
        self.axial_view.getImageItem().setOpts(autoDownsample=False)
        self.slider_axial = QSlider(Qt.Horizontal)
        self.slider_axial.valueChanged.connect(lambda v: self.set_slice_index('axial', v))
        viewer_layout.addWidget(QLabel("Axial"), 0, 0)
        viewer_layout.addWidget(self.axial_view, 1, 0)
        viewer_layout.addWidget(self.slider_axial, 2, 0)

        # Sagital
        self.sagittal_view = pg.ImageView()
        self._hide_ui(self.sagittal_view)
        self.sagittal_view.ui.graphicsView.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.sagittal_view.ui.graphicsView.setRenderHint(QPainter.Antialiasing, True)
        self.sagittal_view.getImageItem().setOpts(autoDownsample=False)
        self.slider_sagittal = QSlider(Qt.Horizontal)
        self.slider_sagittal.valueChanged.connect(lambda v: self.set_slice_index('sagittal', v))
        viewer_layout.addWidget(QLabel("Sagital"), 0, 1)
        viewer_layout.addWidget(self.sagittal_view, 1, 1)
        viewer_layout.addWidget(self.slider_sagittal, 2, 1)

        # Coronal
        self.coronal_view = pg.ImageView()
        self._hide_ui(self.coronal_view)
        self.coronal_view.ui.graphicsView.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.coronal_view.ui.graphicsView.setRenderHint(QPainter.Antialiasing, True)
        self.coronal_view.getImageItem().setOpts(autoDownsample=False)
        self.slider_coronal = QSlider(Qt.Horizontal)
        self.slider_coronal.valueChanged.connect(lambda v: self.set_slice_index('coronal', v))
        viewer_layout.addWidget(QLabel("Coronal"), 0, 2)
        viewer_layout.addWidget(self.coronal_view, 1, 2)
        viewer_layout.addWidget(self.slider_coronal, 2, 2)

        # Expandir vistas
        for view in (self.axial_view, self.sagittal_view, self.coronal_view):
            view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viewer_layout.setColumnStretch(0, 1)
        viewer_layout.setColumnStretch(1, 1)
        viewer_layout.setColumnStretch(2, 1)
        viewer_layout.setRowStretch(1, 1)

        layout.addLayout(viewer_layout)

        # — Sliders de brillo y contraste —
        sliders_layout = QHBoxLayout()

        self.bright1_slider = QSlider(Qt.Horizontal)
        self.bright1_slider.setRange(1, 40)
        self.bright1_slider.setValue(10)
        self.bright1_slider.valueChanged.connect(lambda v: self.bright1_label.setText(f"Brillo Image 1: {v}"))
        self.bright1_label = QLabel("Brillo Imagen 1: 10")

        self.contrast1_slider = QSlider(Qt.Horizontal)
        self.contrast1_slider.setRange(1, 40)
        self.contrast1_slider.setValue(10)
        self.contrast1_slider.valueChanged.connect(lambda v: self.contrast1_label.setText(f"Contraste Imagen 1: {v}"))
        self.contrast1_label = QLabel("Contraste Imagen 1: 10")

        self.bright2_slider = QSlider(Qt.Horizontal)
        self.bright2_slider.setRange(1, 40)
        self.bright2_slider.setValue(10)
        self.bright2_slider.valueChanged.connect(lambda v: self.bright2_label.setText(f"Brillo Imagen 2: {v}"))
        self.bright2_label = QLabel("Brillo Imagen 2: 10")

        self.contrast2_slider = QSlider(Qt.Horizontal)
        self.contrast2_slider.setRange(1, 40)
        self.contrast2_slider.setValue(10)
        self.contrast2_slider.valueChanged.connect(lambda v: self.contrast2_label.setText(f"Contraste Imagen 2: {v}"))
        self.contrast2_label = QLabel("Contraste Imagen 2: 10")


        for label, slider in [
            (self.bright1_label, self.bright1_slider),
            (self.contrast1_label, self.contrast1_slider),
            (self.bright2_label, self.bright2_slider),
            (self.contrast2_label, self.contrast2_slider)
        ]:
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            col = QVBoxLayout()
            col.addWidget(label)
            col.addWidget(slider)
            sliders_layout.addLayout(col)

        layout.addLayout(sliders_layout)

        # — Transformaciones —
        transform_box = QGroupBox("Transformaciones – Imagen 2")
        transform_layout = QGridLayout()
        self.slider_tx = QSlider(Qt.Horizontal)
        self.slider_ty = QSlider(Qt.Horizontal)
        self.slider_tz = QSlider(Qt.Horizontal)
        self.slider_rx = QSlider(Qt.Horizontal)
        self.slider_ry = QSlider(Qt.Horizontal)
        self.slider_rz = QSlider(Qt.Horizontal)

        # Definir etiquetas como atributos si necesitas reutilizarlas
        self.spacing_mm = (1.0, 1.0, 1.0)  # valor por defecto hasta cargar imagen

        self.tx_label = QLabel("Traslación Z: 0.0 mm")
        self.ty_label = QLabel("Traslación Y: 0.0 mm")
        self.tz_label = QLabel("Traslación X: 0.0 mm")
        self.rx_label = QLabel("Rotación Z: 0°")
        self.ry_label = QLabel("Rotación Y: 0°")
        self.rz_label = QLabel("Rotación X: 0°")
        self.tx_label.setFixedWidth(125)
        self.ty_label.setFixedWidth(125)
        self.tz_label.setFixedWidth(125)
        self.rx_label.setFixedWidth(125)
        self.ry_label.setFixedWidth(125)
        self.rz_label.setFixedWidth(125)

        for s, rng, lbl, row in [
            (self.slider_tx, (-50, 50), self.tx_label, 0),
            (self.slider_ty, (-50, 50), self.ty_label, 1),
            (self.slider_tz, (-50, 50), self.tz_label, 2),
            (self.slider_rx, (-180, 180), self.rx_label, 0),
            (self.slider_ry, (-180, 180), self.ry_label, 1),
            (self.slider_rz, (-180, 180), self.rz_label, 2)
        ]:
            s.setRange(*rng)
            s.setValue(0)

            if "Traslación" in lbl.text():
                s.valueChanged.connect(self.update_mm_labels)
            else:
                s.valueChanged.connect(self.update_deg_labels)

            col = 0 if "Traslación" in lbl.text() else 2
            transform_layout.addWidget(lbl, row, col)
            transform_layout.addWidget(s, row, col + 1)

        # Llamada inicial para mostrar "0.0 mm"
        self.update_mm_labels()

        transform_box.setLayout(transform_layout)
        layout.addWidget(transform_box)

        # — Conexiones —
        for s in (
                self.slider_axial, self.slider_sagittal, self.slider_coronal,
                self.bright1_slider, self.contrast1_slider,
                self.bright2_slider, self.contrast2_slider,
                self.slider_tx, self.slider_ty, self.slider_tz,
                self.slider_rx, self.slider_ry, self.slider_rz):
            s.valueChanged.connect(self.update_views)

        self.axial_view.ui.histogram.sigLevelChangeFinished.connect(
            self.sync_histogram_levels
        )

        for s in (
                self.slider_axial, self.slider_sagittal, self.slider_coronal,
                self.bright1_slider, self.bright2_slider,
                self.contrast1_slider, self.contrast2_slider,
                self.slider_tx, self.slider_ty, self.slider_tz,
                self.slider_rx, self.slider_ry, self.slider_rz):
            self.style_slider_handle(s)

    def clear_views(self):
        """Borra únicamente las imágenes de los tres ImageView."""
        for iv in (self.axial_view, self.sagittal_view, self.coronal_view):
            iv.clear()  # limpia la imagen y restaura el estado interno
        # y reseteamos caché / flags
        self.cached_vol2 = None
        self.last_params = None
        self.primera_carga = True

    def reset_sliders(self):
        # Reset de transformación
        self.slider_tx.setValue(0)
        self.slider_ty.setValue(0)
        self.slider_tz.setValue(0)
        self.slider_rx.setValue(0)
        self.slider_ry.setValue(0)
        self.slider_rz.setValue(0)

        # Reset de alpha, brillo y contraste
        # self.alpha1.setValue(50)  # si usas slider de alpha para la imagen 1
        self.bright1_slider.setValue(10)
        self.contrast1_slider.setValue(10)
        self.bright2_slider.setValue(10)
        self.contrast2_slider.setValue(10)

        # Reset de cortes (slices)
        self.slider_axial.setValue(0)
        self.slider_sagittal.setValue(0)
        self.slider_coronal.setValue(0)

    def update_mm_labels(self):
        tx = self.slider_tx.value() * self.spacing_mm[0]
        ty = - self.slider_ty.value() * self.spacing_mm[1]
        tz = self.slider_tz.value() * self.spacing_mm[2]
        self.tx_label.setText(f"Traslación LR: {tx:.1f} mm")
        self.ty_label.setText(f"Traslación PA: {ty:.1f} mm")
        self.tz_label.setText(f"Traslación IS: {tz:.1f} mm")

    def update_deg_labels(self):
        rx = - self.slider_rx.value()
        ry = self.slider_ry.value()
        rz = - self.slider_rz.value()

        self.rx_label.setText(f"Rotación Z: {rx}°")
        self.ry_label.setText(f"Rotación Y: {ry}°")
        self.rz_label.setText(f"Rotación Z: {rz}°")

    def style_slider_handle(self, slider, handle_size=30, groove_height=8):
        # Calcula el margen superior/ inferior para centrar el handle
        margin = -(handle_size // 2 - groove_height // 2)
        slider.setFixedHeight(handle_size)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 20px;               /* grosor de la barra */
                background: #ccc;
                border-radius: 10px;
            }
            QSlider::handle:horizontal {
                width: 60px;                /* ancho del selector */
                height: 10px;               /* alto del selector */
                margin: -10px 0;            /* centra verticalmente el handle */
                background: #888;
                border: 1px solid #666;
                border-radius: 5px;
            }
        """)

    def init_connections(self):
        self.btn_cargar_fija.clicked.connect(self.load_image_fija)
        self.btn_cargar_transformar.clicked.connect(self.load_image_transformar)
        self.btn_guardar.clicked.connect(self.guardar_imagen_transformada)

    # ——— Helpers UI ———
    def _hide_ui(self, iv: pg.ImageView):
        iv.ui.roiBtn.hide();
        iv.ui.menuBtn.hide();
        iv.ui.histogram.hide()
    def _make_slice_slider(self, axis):
        s = QSlider(Qt.Horizontal)
        s.valueChanged.connect(lambda v: self.set_slice_index(axis, v))
        return s

    def create_slider(self, mn, mx, iv, text, layout, row):
        lbl = QLabel(f"{text}: {iv}")
        s   = QSlider(Qt.Horizontal); s.setRange(mn, mx); s.setValue(iv)
        s.valueChanged.connect(lambda v: lbl.setText(f"{text}: {v}"))
        # agranda el thumb del slider

        s.setStyleSheet("""
                    QSlider::groove:horizontal {
                        height: 20px;               /* grosor de la barra */
                        background: #ccc;
                        border-radius: 10px;
                    }
                    QSlider::handle:horizontal {
                        width: 60px;                /* ancho del selector */
                        height: 10px;               /* alto del selector */
                        margin: -10px 0;            /* centra verticalmente el handle */
                        background: #888;
                        border: 1px solid #666;
                        border-radius: 5px;
                    }
                """)
        layout.addWidget(lbl, row, 0)
        layout.addWidget(s, row, 1)
        return s

    # ——— Corte de slices ———
    def set_slice_index(self, axis, v):
        if axis=='axial':
            self.idx_axial = v
        elif axis=='sagittal':
            self.idx_sagittal = v
        elif axis=='coronal':
            self.idx_coronal   = v
        self.update_views()

    def update_sliders(self):
        if self.img1 is None: return
        # centrar siempre en la mitad
        self.slider_axial.setMaximum(self.img1.shape[2]-1)
        self.slider_axial.setValue( self.img1.shape[2]//2 )
        self.slider_sagittal.setMaximum(self.img1.shape[0]-1)
        self.slider_sagittal.setValue( self.img1.shape[0]//2 )
        self.slider_coronal.setMaximum(self.img1.shape[1]-1)
        self.slider_coronal.setValue( self.img1.shape[1]//2 )

    def sync_histogram_levels(self):
        lv = self.axial_view.ui.histogram.getLevels()
        self.sagittal_view.setLevels(*lv)
        self.coronal_view. setLevels(*lv)

    # ——— Carga de imágenes ———
    # def load_image_fija(self):
    #     # — Si ya había imágenes cargadas, limpiamos todo —
    #     if self.img1 is not None or self.img2 is not None:
    #         self.clear_views()
    #         self.reset_sliders()
    #         self.img1 = None
    #         self.img2 = None
    #
    #     path, _ = QFileDialog.getOpenFileName(self, "Imagen fija", "", "NIfTI (*.nii *.nii.gz)")
    #     if not path:
    #         return
    #
    #     img = nib.load(path)
    #     self.img1 = img.get_fdata()
    #     self.spacing_mm_1 = img.header.get_zooms()[:3]
    #     self.affine_1 = img.affine
    #
    #     # Get voxel grid shape
    #     shape = self.img1.shape  # (X, Y, Z)
    #
    #     # Generate voxel indices grid
    #     i = np.arange(shape[0])
    #     j = np.arange(shape[1])
    #     k = np.arange(shape[2])
    #     I, J, K = np.meshgrid(i, j, k, indexing='ij')
    #
    #     # Flatten and stack as homogeneous coordinates (N, 4)
    #     ones = np.ones(I.size)
    #     ijk = np.vstack([I.ravel(), J.ravel(), K.ravel(), ones])  # shape (4, N)
    #
    #     # Apply affine to get world coordinates (4, N)
    #     self.xyz_world = self.affine_1 @ ijk  # shape (4, N)
    #
    #     # Reshape to (X, Y, Z, 3)
    #     self.mesh_coords = self.xyz_world[:3].T.reshape(shape + (3,))
    #
    #     # GUI updates
    #     self.update_sliders()
    #     self.reset_cache()
    #     self.update_views()
    def load_image_fija(self):
        # — Si ya había imágenes cargadas, reiniciar todo —
        if self.img1 is not None or self.img2 is not None:
            self.img1 = None
            self.img2 = None
            self.clear_views()  # vacía los 3 visores y resetea la caché
            self.reset_sliders()  # sliders a valores iniciales


        # — Pedir nueva imagen fija —
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar imagen fija",
            "",
            "NIfTI (*.nii *.nii.gz)"
        )
        if not path:
            return

        # — Cargar con nibabel —
        img = nib.load(path)
        self.img1 = img.get_fdata()
        self.affine_1 = img.affine
        self.spacing_mm_1 = img.header.get_zooms()[:3]

        # — Generar malla de coordenadas en espacio mundial —
        shape = self.img1.shape  # (X, Y, Z)
        i = np.arange(shape[0])
        j = np.arange(shape[1])
        k = np.arange(shape[2])
        I, J, K = np.meshgrid(i, j, k, indexing='ij')
        ones = np.ones(I.size)
        ijk = np.vstack([I.ravel(), J.ravel(), K.ravel(), ones])  # (4, N)
        self.xyz_world = self.affine_1 @ ijk
        self.mesh_coords = self.xyz_world[:3].T.reshape(shape + (3,))

        # — Actualizar sliders de corte al nuevo volumen —
        self.update_sliders()

        # — Reiniciar caché de transformación (por si queda algo) —
        self.reset_cache()

        # — Finalmente, pintar las vistas con la nueva imagen —
        self.update_views()

    def load_image_transformar(self):
        # — Si ya había una imagen a transformar, limpiamos sólo esa —
        if self.img2 is not None:
            # conservamos self.img1 para seguir viéndola
            self.img2 = None
            self.clear_views()  # borra los 3 visores y resetea la caché
            self.reset_sliders()  # sliders a valores iniciales


        path, _ = QFileDialog.getOpenFileName(self, "Imagen a transformar", "", "NIfTI (*.nii *.nii.gz)")
        if not path:
            return

        self.img2_path = path
        img = nib.load(path)
        self.img2 = img.get_fdata()
        self.affine_2 = img.affine
        self.spacing_mm = img.header.get_zooms()[:3]
        self.update_mm_labels()

        # Resample img2 to match img1's space
        if self.img1 is not None and self.img1.shape != self.img2.shape:
            # transform world coords into img2 voxel space
            affine2_inv = np.linalg.inv(self.affine_2)
            ijk2 = affine2_inv @ self.xyz_world  # (4, N)

            # interpolate img2 at those coordinates
            shape1 = self.img1.shape
            coords = [ijk2[axis, :].reshape(shape1) for axis in range(3)]
            self.img2 = scipy.ndimage.map_coordinates(self.img2, coords, order=1, mode='nearest')

            # Now both image 1 and 2 have the same affine matrix
            self.affine_2 = self.affine_1
            self.spacing_mm = self.spacing_mm_1

        # leer parámetros embebidos
        try:
            for ext in img.header.extensions:
                if ext.get_code()==40:
                    d = json.loads(ext.get_content())
                    for key, slider in (
                        ("tx",self.slider_tx),("ty",self.slider_ty),("tz",self.slider_tz),
                        ("rx",self.slider_rx),("ry",self.slider_ry),("rz",self.slider_rz)
                    ):
                        slider.setValue(d.get(key,0))
                    break
        except: pass

        #al cargar la segunda imagen, centramos también los sliders
        self.update_sliders()
        self.reset_cache()
        self.update_views()

    def reset_cache(self):
        self.last_params   = None
        self.cached_vol2   = None
        self.primera_carga = True

    # ——— Transformación 3D ———
    def get_current_affine(self):
        tx,ty,tz = [s.value() for s in (self.slider_tx,self.slider_ty,self.slider_tz)]
        rx,ry,rz = np.deg2rad([s.value() for s in (self.slider_rx,self.slider_ry,self.slider_rz)])
        cx,cy,cz = np.array(self.img1.shape)/2.0
        # matrices de rotación + traslación al centro/origen
        Rx = np.array([[1,0,0,0],[0,np.cos(rx),-np.sin(rx),0],[0,np.sin(rx),np.cos(rx),0],[0,0,0,1]])
        Ry = np.array([[np.cos(ry),0,np.sin(ry),0],[0,1,0,0],[-np.sin(ry),0,np.cos(ry),0],[0,0,0,1]])
        Rz = np.array([[np.cos(rz),-np.sin(rz),0,0],[np.sin(rz),np.cos(rz),0,0],[0,0,1,0],[0,0,0,1]])
        T1 = np.eye(4); T1[:3,3] = -np.array([cx,cy,cz])
        T2 = np.eye(4); T2[:3,3] =  np.array([cx+tx,cy+ty,cz+tz])
        return T2 @ (Rz @ (Ry @ (Rx @ T1)))

    def transform_volume(self):
        aff = self.get_current_affine()
        R   = aff[:3,:3]
        off = aff[:3,3]
        invR = np.linalg.inv(R)
        return scipy.ndimage.affine_transform(
            self.img2, invR, offset=-invR@off, order=1, mode='nearest'
        )

    def create_gray_overlay(self, slice1, slice2, alpha1, alpha2):
        # — normalización dinámica de cada slice al [0,1] —
        lo1, hi1 = slice1.min(), slice1.max()
        lo2, hi2 = slice2.min(), slice2.max()
        if hi1 > lo1:
            n1 = (slice1 - lo1) / (hi1 - lo1)
        else:
            n1 = np.zeros_like(slice1)
        if hi2 > lo2:
            n2 = (slice2 - lo2) / (hi2 - lo2)
        else:
            n2 = np.zeros_like(slice2)

        # mezcla directa con tus alphas
        gray = np.clip(n1 * alpha1 + n2 * alpha2, 0, 1)
        return (gray * 255).astype(np.uint8)


    # def update_views(self, orientation='None'):
    #     if self.img1 is None or self.img2 is None:
    #          return
    #     # if self.img1 is None:
    #     #     return
    #     #Recalcular el volumen transformado solo si cambian tx/ty/tz/rx/ry/rz
    #     params = tuple(s.value() for s in (
    #         self.slider_tx, self.slider_ty, self.slider_tz,
    #         self.slider_rx, self.slider_ry, self.slider_rz
    #     ))
    #     if params!=self.last_params:
    #         self.cached_vol2 = self.transform_volume()
    #         self.last_params = params
    #     vol2 = self.cached_vol2
    #
    #
    #     #Leer factores de brillo (1–20 → 0.1–2.0) y contraste (1–20 → 0.1–2.0)
    #     f1 = self.bright1_slider.value() / 5
    #     c1 = self.contrast1_slider.value() / 10.0
    #     f2 = self.bright2_slider.value() / 5
    #     c2 = self.contrast2_slider.value() / 10.0
    #
    #     # 3) Alphas fijos (50% / 50%)
    #     a1 = a2 = 0.5
    #
    #     # 4) Índices de corte actuales
    #     z, x, y = self.idx_axial, self.idx_sagittal, self.idx_coronal
    #
    #     #Preparamos un listado de (slice1, slice2, ImageView)
    #     cortes = [
    #         (self.img1[::-1, ::-1, z], vol2[::-1, ::-1, z], self.axial_view),
    #         (self.img1[x, ::-1, ::-1].T, vol2[x, ::-1, ::-1].T, self.sagittal_view),
    #         (self.img1[::-1, y, ::-1].T, vol2[::-1, y, ::-1].T, self.coronal_view),
    #     ]
    #
    #     #Renderizado
    #     auto = self.primera_carga
    #     for s1, s2, view in cortes:
    #         # 6.1) Aplicar brillo/contraste
    #         s1 = np.clip(s1 * f1, s1.min(), s1.max())
    #         s2 = np.clip(s2 * f2, s2.min(), s2.max())
    #         # 6.2) Aplicar contraste (centrado en la media)
    #         m1 = s1.mean()
    #         s1 = np.clip((s1 - m1) * c1 + m1, s1.min(), s1.max())
    #         m2 = s2.mean()
    #         s2 = np.clip((s2 - m2) * c2 + m2, s2.min(), s2.max())
    #
    #         #Si la imagen 2 es transparente, mostramos solo la fija
    #         if a2==0:
    #             view.setImage(s1, autoLevels=True)
    #         else:
    #             # 6.3) Mezcla en gris con alpha 0.5/0.5
    #             img = self.create_gray_overlay(s1, s2, a1, a2)
    #             view.setImage(img, autoLevels=False)
    #             view.setLevels(0, 255)
    #
    #     #Sincronizar histogramas solo la primera vez
    #     if auto:
    #         self.sync_histogram_levels()
    #         self.primera_carga = False
    def update_views(self, orientation='None'):
        # 1) Si no hay imagen fija, nada que dibujar
        if self.img1 is None:
            return

        # 2) Calculamos índices, clamp contra img1
        z = max(0, min(self.idx_axial, self.img1.shape[2] - 1))
        x = max(0, min(self.idx_sagittal, self.img1.shape[0] - 1))
        y = max(0, min(self.idx_coronal, self.img1.shape[1] - 1))

        # 3) Caso A: sólo imagen 1 → dibujamos cortes simples
        if self.img2 is None:
            self.axial_view.setImage(self.img1[::-1, ::-1, z], autoLevels=True)
            self.sagittal_view.setImage(self.img1[x, ::-1, ::-1].T, autoLevels=True)
            self.coronal_view.setImage(self.img1[::-1, y, ::-1].T, autoLevels=True)
            return

        # 4) Caso B: tenemos ambas → overlay
        #    Recalcular sólo si cambiaron sliders de tx/ty/tz/rx/ry/rz
        params = tuple(s.value() for s in (
            self.slider_tx, self.slider_ty, self.slider_tz,
            self.slider_rx, self.slider_ry, self.slider_rz
        ))
        if params!=self.last_params:
            self.cached_vol2 = self.transform_volume()
            self.last_params = params
            self.primera_carga = True

        vol2 = self.cached_vol2

        # 5) Factores brillo / contraste
        f1 = self.bright1_slider.value() / 5
        c1 = self.contrast1_slider.value() / 10.0
        f2 = self.bright2_slider.value() / 5
        c2 = self.contrast2_slider.value() / 10.0

        # 6) Álgebras de mezcla
        a1 = a2 = 0.5

        # 7) Preparar slices y vistas
        cortes = [
            (self.img1[::-1, ::-1, z], vol2[::-1, ::-1, z], self.axial_view),
            (self.img1[x, ::-1, ::-1].T, vol2[x, ::-1, ::-1].T, self.sagittal_view),
            (self.img1[::-1, y, ::-1].T, vol2[::-1, y, ::-1].T, self.coronal_view),
        ]

        # 8) Render
        for s1, s2, view in cortes:
            # brillo + contraste
            s1 = np.clip((s1 * f1 - s1.mean()) * c1 + s1.mean(), s1.min(), s1.max())
            s2 = np.clip((s2 * f2 - s2.mean()) * c2 + s2.mean(), s2.min(), s2.max())

            # mezcla gris
            img = self.create_gray_overlay(s1, s2, a1, a2)
            view.setImage(img, autoLevels=False)
            view.setLevels(0, 255)

        # 9) sincronizar histograma solo la primera vez
        if self.primera_carga:
            self.sync_histogram_levels()
            self.primera_carga = False


    # def guardar_imagen_transformada(self):
    #     if self.img2 is None: return
    #     # 1) Pedimos ruta al usuario
    #     path, _ = QFileDialog.getSaveFileName(
    #         self,
    #         "Guardar imagen transformada",
    #         "transformada_3D.nii.gz",
    #         "NIfTI (*.nii *.nii.gz)"
    #     )
    #     if not path:
    #         return
    #
    #     # 2) Parámetros de transformación
    #     params = {k: s.value() for k, s in zip(
    #         ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'),
    #         (self.slider_tx, self.slider_ty, self.slider_tz,
    #          self.slider_rx, self.slider_ry, self.slider_rz)
    #     )}
    #
    #     # 3) Cargamos la affine original
    #     try:
    #         img2_nib = nib.load(self.img2_path)
    #         affine_orig = img2_nib.affine
    #     except:
    #         affine_orig = np.eye(4)
    #
    #     # 4) Calculamos la affine acumulada
    #     affine_transform = self.get_current_affine()
    #     affine_new = affine_orig @ affine_transform
    #
    #     # 5) Creamos la imagen NIfTI con el volumen transformado
    #     out = nib.Nifti1Image(self.cached_vol2, affine_new)
    #
    #     # 6) (Opcional) guardamos los parámetros como extensión
    #     ext = nifti1.Nifti1Extension(
    #         40,
    #         json.dumps(params).encode('utf-8')
    #     )
    #     out.header.extensions.clear()
    #     out.header.extensions.append(ext)
    #
    #     # 7) Guardamos en disco
    #     nib.save(out, path)
    #     QMessageBox.information(
    #         self,
    #         "Guardado exitoso",
    #         f"Imagen transformada y nueva affine guardadas en:\n{path}"
    #     )

    def guardar_imagen_transformada(self):
        if self.img2 is None:
            return
        #Pedimos ruta al usuario
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar imagen transformada",
            "transformada_3D.nii.gz",
            "NIfTI (*.nii *.nii.gz)"
        )
        if not path:
            return

        #Parámetros de transformación
        params = {k: s.value() for k, s in zip(
            ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'),
            (self.slider_tx, self.slider_ty, self.slider_tz,
             self.slider_rx, self.slider_ry, self.slider_rz)
        )}

        #Cargamos la affine original
        try:
            img2_nib = nib.load(self.img2_path)
            affine_orig = img2_nib.affine
            spacing = img2_nib.header.get_zooms()[:3]
        except:
            affine_orig = np.eye(4)
            spacing = (1.0, 1.0, 1.0)

        #Calculamos la affine acumulada
        affine_transform = self.get_current_affine()
        affine_new = affine_orig @ affine_transform

        #Creamos la imagen NIfTI con el volumen transformado
        out = nib.Nifti1Image(self.cached_vol2, affine_new)

        #Guardamos los parámetros como extensión
        ext = nifti1.Nifti1Extension(
            40,
            json.dumps(params).encode('utf-8')
        )
        out.header.extensions.clear()
        out.header.extensions.append(ext)

        #Guardamos la imagen
        nib.save(out, path)

        #Guardar en CSV los parámetros en milímetros
        tx_mm = params['tx'] * spacing[0]
        ty_mm = params['ty'] * spacing[1]
        tz_mm = params['tz'] * spacing[2]

        csv_path = os.path.splitext(path)[0] + ".csv"
        with open(csv_path, 'w') as f:
            f.write("X(mm),Y(mm),Z(mm),RX(°),RY(°),RZ(°)\n")
            f.write(f"{tx_mm:.2f},{ty_mm:.2f},{tz_mm:.2f},{params['rx']},{params['ry']},{params['rz']}\n")
            f.write("\nAffine 4x4:\n")
            np.savetxt(f, affine_new, delimiter=',')

        #Notificar al usuario
        QMessageBox.information(
            self,
            "Guardado exitoso",
            f"Imagen transformada, nueva affine y CSV guardados en:\n{path}\n{csv_path}"
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Corregistro3D()
    win.show()
    sys.exit(app.exec_())
