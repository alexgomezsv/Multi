import sys
import os
import platform
import json
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit, QHBoxLayout)

# Definir las rutas predeterminadas según el sistema operativo
def get_default_paths():
    if platform.system() == "Windows":
        return {
            "urls_file": "C:/Users/Alex/Desktop/Multi/urls.json",
            "vlc_lib_path": "C:/Program Files/VideoLAN/VLC/libvlc.dll",
            "vlc_core_path": "C:/Program Files/VideoLAN/VLC/libvlccore.dll"
        }
    else:  # Para macOS
        return {
            "urls_file": "/Users/alex-mac/Desktop/Multi/urls.json",
            "vlc_lib_path": "/Applications/VLC.app/Contents/MacOS/lib/libvlc.dylib",
            "vlc_core_path": "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib"
        }

# Cargar la configuración guardada o usar la predeterminada
def load_config():
    try:
        with open("multiviewer_config.json", "r") as file:
            config = json.load(file)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return get_default_paths()

# Guardar la configuración en un archivo JSON
def save_config(config):
    with open("multiviewer_config.json", "w") as file:
        json.dump(config, file)

class AdminWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()

        # Crear el layout y los elementos visuales
        main_layout = QVBoxLayout()

        # Manejar las rutas actuales
        self.vlc_lib_path = self.config.get("vlc_lib_path")
        self.vlc_core_path = self.config.get("vlc_core_path")
        self.urls_file = self.config.get("urls_file")

        # Detección del sistema operativo para hacer recomendaciones de rutas
        self.os_type = platform.system()

        # Layout para la librería VLC
        vlc_lib_layout = QHBoxLayout()
        self.vlc_lib_input = QLineEdit(self.vlc_lib_path)
        self.vlc_lib_input.setPlaceholderText("Ingresar ruta de la librería VLC (libvlc.dll o libvlc.dylib)")
        vlc_lib_button = QPushButton("Seleccionar")
        vlc_lib_button.clicked.connect(self.select_vlc_lib_path)
        vlc_lib_layout.addWidget(self.vlc_lib_input)
        vlc_lib_layout.addWidget(vlc_lib_button)

        vlc_lib_recommendation = QLabel(self.get_vlc_lib_recommendation())
        vlc_lib_recommendation.setStyleSheet("font-size: 10px; color: grey;")

        # Layout para el core de VLC
        vlc_core_layout = QHBoxLayout()
        self.vlc_core_input = QLineEdit(self.vlc_core_path)
        self.vlc_core_input.setPlaceholderText("Ingresar ruta del core VLC (libvlccore.dll o libvlccore.dylib)")
        vlc_core_button = QPushButton("Seleccionar")
        vlc_core_button.clicked.connect(self.select_vlc_core_path)
        vlc_core_layout.addWidget(self.vlc_core_input)
        vlc_core_layout.addWidget(vlc_core_button)

        vlc_core_recommendation = QLabel(self.get_vlc_core_recommendation())
        vlc_core_recommendation.setStyleSheet("font-size: 10px; color: grey;")

        # Layout para el archivo de URLs
        urls_layout = QHBoxLayout()
        self.urls_input = QLineEdit(self.urls_file)
        self.urls_input.setPlaceholderText("Ingresar ruta del archivo URLs JSON")
        urls_button = QPushButton("Seleccionar")
        urls_button.clicked.connect(self.select_urls_file)
        urls_layout.addWidget(self.urls_input)
        urls_layout.addWidget(urls_button)

        urls_recommendation = QLabel(self.get_urls_recommendation())
        urls_recommendation.setStyleSheet("font-size: 10px; color: grey;")

        # Añadir las rutas actuales al layout principal
        main_layout.addLayout(vlc_lib_layout)
        main_layout.addWidget(vlc_lib_recommendation)

        main_layout.addLayout(vlc_core_layout)
        main_layout.addWidget(vlc_core_recommendation)

        main_layout.addLayout(urls_layout)
        main_layout.addWidget(urls_recommendation)

        # Botón para guardar la configuración
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self.save_configuration)
        main_layout.addWidget(save_button)

        # Botón para verificar si las rutas son válidas
        validate_button = QPushButton("Validar Rutas")
        validate_button.clicked.connect(self.validate_paths)
        main_layout.addWidget(validate_button)

        # Botón para abrir el MultiViewer
        open_multiviewer_button = QPushButton("Abrir MultiViewer")
        open_multiviewer_button.clicked.connect(self.open_multiviewer)
        main_layout.addWidget(open_multiviewer_button)

        self.setLayout(main_layout)
        self.setWindowTitle("Configuración Administrativa - MultiViewer")
        self.setGeometry(300, 100, 600, 400)

        # Intentar auto-detectar librerías en macOS después de inicializar todos los elementos del GUI
        if self.os_type == "Darwin":  # macOS
            self.auto_detect_vlc_paths()

    def auto_detect_vlc_paths(self):
        """Detectar automáticamente las librerías VLC en macOS."""
        possible_lib_path = "/Applications/VLC.app/Contents/MacOS/lib/libvlc.dylib"
        possible_core_path = "/Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib"

        if os.path.exists(possible_lib_path):
            self.vlc_lib_path = possible_lib_path
            self.vlc_lib_input.setText(self.vlc_lib_path)
        if os.path.exists(possible_core_path):
            self.vlc_core_path = possible_core_path
            self.vlc_core_input.setText(self.vlc_core_path)

    def get_vlc_lib_recommendation(self):
        """Retorna la recomendación de la ruta de la librería VLC en función del sistema operativo."""
        if self.os_type == "Windows":
            return "Recomendación: C:/Program Files/VideoLAN/VLC/libvlc.dll"
        elif self.os_type == "Darwin":  # macOS
            return "Recomendación: /Applications/VLC.app/Contents/MacOS/lib/libvlc.dylib"
        else:
            return "Ingrese la ruta de libvlc según su sistema operativo."

    def get_vlc_core_recommendation(self):
        """Retorna la recomendación de la ruta del core VLC en función del sistema operativo."""
        if self.os_type == "Windows":
            return "Recomendación: C:/Program Files/VideoLAN/VLC/libvlccore.dll"
        elif self.os_type == "Darwin":  # macOS
            return "Recomendación: /Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib"
        else:
            return "Ingrese la ruta de libvlccore según su sistema operativo."

    def get_urls_recommendation(self):
        """Retorna la recomendación de la ruta del archivo de URLs JSON."""
        if self.os_type == "Windows":
            return "Recomendación: C:/Users/Alex/Desktop/Multi/urls.json"
        elif self.os_type == "Darwin":  # macOS
            return "Recomendación: /Users/alex-mac/Desktop/Multi/urls.json"
        else:
            return "Ingrese la ruta del archivo JSON donde almacenar las URLs."

    def select_vlc_lib_path(self):
        """Seleccionar la ruta de libvlc.dll o libvlc.dylib"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar librería VLC", "", "Dynamic Library Files (*.dll *.dylib)")
        if file_path:
            self.vlc_lib_input.setText(file_path)

    def select_vlc_core_path(self):
        """Seleccionar la ruta de libvlccore.dll o libvlccore.dylib"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar core VLC", "", "Dynamic Library Files (*.dll *.dylib)")
        if file_path:
            self.vlc_core_input.setText(file_path)

    def select_urls_file(self):
        """Seleccionar o crear un archivo de configuración JSON para las URLs"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Seleccionar archivo JSON de URLs", "", "JSON Files (*.json)")
        if file_path:
            self.urls_input.setText(file_path)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as file:
                    json.dump({}, file)

    def validate_paths(self):
        """Verificar si las rutas ingresadas son válidas antes de guardar la configuración"""
        vlc_lib_path = self.vlc_lib_input.text()
        vlc_core_path = self.vlc_core_input.text()

        def is_valid_vlc_lib(path):
            return os.path.exists(path) and "libvlc" in os.path.basename(path)

        def is_valid_vlc_core(path):
            return os.path.exists(path) and "libvlccore" in os.path.basename(path)

        if is_valid_vlc_lib(vlc_lib_path) and (is_valid_vlc_core(vlc_core_path) or self.os_type != "Windows"):
            QMessageBox.information(self, "Validación Exitosa", "Las rutas ingresadas son válidas.")
        else:
            QMessageBox.warning(self, "Validación Fallida", "Algunas de las rutas ingresadas no son válidas. Verifique nuevamente.")

    def save_configuration(self):
        """Guardar las configuraciones ingresadas por el usuario"""
        self.config["vlc_lib_path"] = self.vlc_lib_input.text()
        self.config["vlc_core_path"] = self.vlc_core_input.text()
        self.config["urls_file"] = self.urls_input.text()

        # Validar antes de guardar
        vlc_lib_path = self.config["vlc_lib_path"]
        vlc_core_path = self.config["vlc_core_path"]

        def is_valid_vlc_lib(path):
            return os.path.exists(path) and "libvlc" in os.path.basename(path)

        def is_valid_vlc_core(path):
            return os.path.exists(path) and "libvlccore" in os.path.basename(path)

        if is_valid_vlc_lib(vlc_lib_path) and (is_valid_vlc_core(vlc_core_path) or self.os_type != "Windows"):
            save_config(self.config)
            QMessageBox.information(self, "Configuración Guardada", "Las configuraciones se han guardado correctamente.")
        else:
            QMessageBox.warning(self, "Error al Guardar", "Las rutas proporcionadas no son válidas. Por favor, verifique.")

    def open_multiviewer(self):
        """Abrir el archivo multiviewer.py una vez que las configuraciones estén guardadas"""
        self.save_configuration()  # Guardar la configuración antes de abrir
        try:
            subprocess.Popen(["python3", "multiviewer.py"])
            self.close()  # Cerrar la ventana actual de admin_multiviewer
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "No se pudo encontrar el archivo multiviewer.py para ejecutarlo. Verifique la ubicación.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminWindow()
    window.show()
    sys.exit(app.exec_())
