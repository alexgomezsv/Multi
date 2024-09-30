import sys
import vlc
import random
import json
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QLineEdit, QLabel, QGridLayout, QHBoxLayout, QScrollArea, 
                             QMessageBox, QProgressBar, QInputDialog, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import subprocess

# Cargar la configuración guardada o usar la predeterminada
def load_config():
    try:
        with open("multiviewer_config.json", "r") as file:
            config = json.load(file)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        # Configuración predeterminada
        return {
            "urls_file": "/Users/alex-mac/Desktop/Multi/urls.json",
            "vlc_lib_path": "/Applications/VLC.app/Contents/MacOS/libvlc.dylib",
        }

config = load_config()
URLS_FILE = config["urls_file"]
DEFAULT_VLC_PATH = config["vlc_lib_path"]

def load_urls():
    """Cargar todas las URLs desde el archivo JSON."""
    try:
        with open(URLS_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Clases FullScreenWindow y VideoWidget siguen iguales como has proporcionado anteriormente.
class FullScreenWindow(QMainWindow):
    """Ventana de Pantalla Completa"""
    def __init__(self, video_widget):
        super().__init__()
        self.video_widget = video_widget
        self.setWindowTitle("Pantalla Completa")
        self.setStyleSheet("background-color: black;")

        # Botón para volver al modo normal
        self.back_button = QPushButton('Atrás')
        self.back_button.clicked.connect(self.restore_normal_view)
        self.back_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #555;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)

        # Widget de video separado para la ventana de pantalla completa
        self.fullscreen_video_frame = QLabel()
        self.fullscreen_video_frame.setFixedSize(720, 480)
        self.fullscreen_video_frame.setStyleSheet("background-color: black;")

        # Layout para organizar el video y botón
        layout = QVBoxLayout()
        layout.addWidget(self.fullscreen_video_frame, alignment=Qt.AlignCenter)
        layout.addWidget(self.back_button, alignment=Qt.AlignCenter)

        # Configurar el widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Crear un reproductor VLC independiente para la pantalla completa
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def start_fullscreen_video(self, media):
        """Inicia la reproducción en pantalla completa."""
        self.player.set_media(media)

        # Configurar el área de video de la ventana de pantalla completa
        if sys.platform.startswith('linux') or sys.platform == "darwin":
            self.player.set_nsobject(int(self.fullscreen_video_frame.winId()))
        elif sys.platform == "win32":
            self.player.set_hwnd(int(self.fullscreen_video_frame.winId()))

        self.player.play()

    def restore_normal_view(self):
        """Restaurar la vista normal sin cerrar la aplicación."""
        self.player.stop()
        self.hide()
        self.video_widget.is_fullscreen = False
        self.video_widget.fullscreen_button.show()

    def closeEvent(self, event):
        """Cerrar el reproductor VLC al cerrar la ventana completa."""
        if self.player is not None:
            self.player.stop()
            self.player.release()
        event.accept()


class VideoWidget(QWidget):
    """Widget de video independiente para cada canal."""
    def __init__(self, instance, index, window_number, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.instance = instance
        self.index = index
        self.window_number = window_number
        self.setStyleSheet("background-color: #222; border-radius: 8px;")
        self.player = self.instance.media_player_new()

        # Layout horizontal para combinar video y monitoreo de audio
        self.main_layout = QHBoxLayout(self)

        # Monitoreo de audio vertical
        self.audio_monitor_layout = QVBoxLayout()
        self.audio_monitor = QProgressBar(self)
        self.audio_monitor.setOrientation(Qt.Vertical)
        self.audio_monitor.setRange(0, 100)
        self.audio_monitor.setFixedWidth(15)
        self.audio_monitor.setStyleSheet("QProgressBar::chunk {background-color: green;} QProgressBar {border: 1px solid #555; border-radius: 5px; background-color: #333;}")
        self.audio_monitor_layout.addWidget(self.audio_monitor)

        # Botón para activar/desactivar audio
        self.toggle_audio_button = QPushButton('🔊')
        self.toggle_audio_button.setCheckable(True)
        self.toggle_audio_button.clicked.connect(self.toggle_audio)
        self.toggle_audio_button.setStyleSheet("margin: 5px; border-radius: 5px; background-color: #333; color: white;")
        self.audio_monitor_layout.addWidget(self.toggle_audio_button)

        self.main_layout.addLayout(self.audio_monitor_layout)

        # Layout vertical para la pantalla de video y controles
        self.video_layout = QVBoxLayout()

        # Campo de texto para la URL del canal
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ingrese URL del canal...")
        self.url_input.setStyleSheet("margin-bottom: 10px; padding: 5px; border: 1px solid #555; border-radius: 5px; background-color: #333; color: white;")
        self.url_input.textChanged.connect(self.save_url)
        self.video_layout.addWidget(self.url_input)

        # Campo de texto para el nombre del canal
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ingrese nombre del canal...")
        self.name_input.setStyleSheet("margin-bottom: 10px; padding: 5px; border: 1px solid #555; border-radius: 5px; background-color: #333; color: white;")
        self.name_input.textChanged.connect(self.save_name)
        self.video_layout.addWidget(self.name_input)

        # Área de video
        self.video_frame = QLabel()
        self.video_frame.setFixedSize(280, 180)
        self.video_frame.setStyleSheet("background-color: black; border-radius: 8px;")
        self.video_layout.addWidget(self.video_frame, alignment=Qt.AlignCenter)

        # Añadir el gráfico de espectro de audio
        self.spectrum_plot = pg.PlotWidget()
        self.spectrum_plot.setYRange(0, 100)
        self.spectrum_plot.setBackground('#333')
        self.spectrum_plot.hideAxis('bottom')
        self.spectrum_plot.hideAxis('left')
        self.spectrum_curve = self.spectrum_plot.plot(pen=pg.mkPen(color='g', width=2))
        self.video_layout.addWidget(self.spectrum_plot)

        # Botones de control
        button_style = """
            QPushButton {
                background-color: #333;
                color: white;
                padding: 8px;
                border: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """
        
        play_button = QPushButton('Play')
        play_button.setStyleSheet(button_style)
        play_button.clicked.connect(self.play)
        self.video_layout.addWidget(play_button)

        pause_button = QPushButton('Pause')
        pause_button.setStyleSheet(button_style)
        pause_button.clicked.connect(self.pause)
        self.video_layout.addWidget(pause_button)

        stop_button = QPushButton('Stop')
        stop_button.setStyleSheet(button_style)
        stop_button.clicked.connect(self.stop)
        self.video_layout.addWidget(stop_button)

        # Botón de pantalla completa
        self.fullscreen_button = QPushButton('Pantalla Completa')
        self.fullscreen_button.setStyleSheet(button_style)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.video_layout.addWidget(self.fullscreen_button)

        # Añadir el layout de video al layout principal
        self.main_layout.addLayout(self.video_layout)

        # Configurar un temporizador para actualizar el monitoreo de audio
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_audio_monitor)

        # Temporizador para verificar el estado del video
        self.check_black_screen_timer = QTimer(self)
        self.check_black_screen_timer.timeout.connect(self.check_black_screen)

        # Bandera para estado de pantalla completa
        self.is_fullscreen = False
        self.fullscreen_window = None

        # Bandera para evitar notificaciones repetitivas
        self.black_screen_notified = False

        # Referencia al layout padre
        self.parent_layout = parent

        # Cargar URL guardada si existe
        self.load_url()
        # Cargar nombre guardado si existe
        self.load_name()

    def toggle_audio(self):
        """Alternar entre activar y desactivar el audio."""
        if self.toggle_audio_button.isChecked():
            self.player.audio_set_volume(100)
            self.toggle_audio_button.setText('🔇')
        else:
            self.player.audio_set_volume(0)
            self.toggle_audio_button.setText('🔊')

    def set_video_window(self):
        """Configura la ventana donde se renderiza el video."""
        if sys.platform.startswith('linux') or sys.platform == "darwin":
            self.player.set_nsobject(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.player.set_hwnd(int(self.video_frame.winId()))

    def play(self):
        """Reproducir el video."""
        stream_url = self.url_input.text()
        if stream_url:
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.set_video_window()
            self.player.play()
            self.player.audio_set_volume(0)  # Establecer el volumen a 0 al cargar el stream
            self.timer.start(100)
            self.check_black_screen_timer.start(5000)
        else:
            print("Por favor, ingrese una URL válida.")

    def pause(self):
        """Pausar el video."""
        self.player.pause()
        self.timer.stop()
        self.check_black_screen_timer.stop()

    def stop(self):
        """Detener el video."""
        self.player.stop()
        self.timer.stop()
        self.check_black_screen_timer.stop()
        self.audio_monitor.setValue(0)
        self.black_screen_notified = False

    def toggle_fullscreen(self):
        """Alternar entre pantalla completa y tamaño normal."""
        if not self.is_fullscreen:
            if not self.fullscreen_window:
                self.fullscreen_window = FullScreenWindow(self)
            media = self.player.get_media()
            if media:
                self.fullscreen_window.start_fullscreen_video(media)
            self.fullscreen_window.show()
            self.is_fullscreen = True
            self.fullscreen_button.hide()
        else:
            self.fullscreen_window.restore_normal_view()

    def update_audio_monitor(self):
        """Actualizar el monitoreo de audio de manera dinámica simulada."""
        audio_level = random.randint(0, 100)
        spectrum_data = np.random.normal(size=100) * audio_level
        self.spectrum_curve.setData(spectrum_data)

        if audio_level > 95:
            self.audio_monitor.setStyleSheet("QProgressBar::chunk {background-color: red;}")
        else:
            self.audio_monitor.setStyleSheet("QProgressBar::chunk {background-color: green;}")

        self.audio_monitor.setValue(audio_level)

    def check_black_screen(self):
        """Verifica si la pantalla de video se pone negra después de 5 segundos."""
        try:
            video_frame = self.player.video_get_size(0)
            if video_frame == (0, 0) and not self.black_screen_notified:
                self.notify_black_screen()
        except Exception as e:
            print(f"Error al verificar pantalla negra: {e}")

    def notify_black_screen(self):
        """Mostrar una notificación cuando la pantalla se pone negra y permitir edición."""
        self.black_screen_notified = True
        QMessageBox.warning(self, "Pantalla Negra Detectada", f"La pantalla de video {self.index + 1} se ha puesto negra. Verifique el stream.")
        self.url_input.setFocus()

    def save_url(self):
        """Guardar la URL actual en el archivo JSON."""
        state = load_urls()
        window_key = f'window_{self.window_number}'
        
        if window_key not in state:
            state[window_key] = {}
        if 'urls' not in state[window_key]:
            state[window_key]['urls'] = {}

        state[window_key]['urls'][str(self.index)] = self.url_input.text()

        with open(URLS_FILE, 'w') as file:
            json.dump(state, file)

    def save_name(self):
        """Guardar el nombre del canal en el archivo JSON."""
        state = load_urls()
        window_key = f'window_{self.window_number}'

        if window_key not in state:
            state[window_key] = {}
        if 'names' not in state[window_key]:
            state[window_key]['names'] = {}

        state[window_key]['names'][str(self.index)] = self.name_input.text()

        with open(URLS_FILE, 'w') as file:
            json.dump(state, file)

    def load_url(self):
        """Cargar la URL guardada desde el archivo JSON."""
        state = load_urls()
        window_key = f'window_{self.window_number}'
        if window_key in state and 'urls' in state[window_key] and str(self.index) in state[window_key]['urls']:
            self.url_input.setText(state[window_key]['urls'][str(self.index)])

    def load_name(self):
        """Cargar el nombre guardado desde el archivo JSON."""
        state = load_urls()
        window_key = f'window_{self.window_number}'
        if window_key in state and 'names' in state[window_key] and str(self.index) in state[window_key]['names']:
            self.name_input.setText(state[window_key]['names'][str(self.index)])

    def closeEvent(self, event):
        """Detener el reproductor VLC al cerrar la ventana del widget."""
        if self.player is not None:
            self.stop()
            self.player.release()
        event.accept()


class MainWindow(QMainWindow):
    ventana_count = 1  # Contador de ventanas abiertas
    ventanas_abiertas = []  # Lista para guardar las ventanas abiertas

    def __init__(self, num_widgets=8):
        super().__init__()

        # Configuración de la ventana
        self.setWindowTitle(f'ZETA MultiViewers 1.0 - Ventana {MainWindow.ventana_count}')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #333; color: white;")
        self.window_number = MainWindow.ventana_count
        MainWindow.ventana_count += 1

        # Crear el widget central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout_container = QVBoxLayout(central_widget)

        # Layout para los botones y las pantallas de video
        button_layout = QHBoxLayout()
        add_screen_button = QPushButton('Agregar Pantalla')
        add_screen_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        add_screen_button.clicked.connect(self.add_video_widget)
        button_layout.addWidget(add_screen_button)

        add_window_button = QPushButton('Agregar Ventana')
        add_window_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        add_window_button.clicked.connect(self.add_new_window)
        button_layout.addWidget(add_window_button)

        # Botón para el modo de configuración administrativa
        admin_button = QPushButton('Modo Admin')
        admin_button.setStyleSheet("""
            QPushButton {
                background-color: #888;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #AAA;
            }
        """)
        admin_button.clicked.connect(self.activate_admin_mode)
        button_layout.addWidget(admin_button)

        main_layout_container.addLayout(button_layout)

        # Área de scroll para las pantallas de video
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout_container.addWidget(scroll_area)

        # Widget contenedor dentro del área de scroll
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        # Crear layout de cuadrícula para las pantallas de video
        self.main_layout = QGridLayout(scroll_content)
        self.main_layout.setSpacing(20)

        # Crear un reproductor VLC
        self.instance = vlc.Instance()

        # Añadir widgets de video iniciales
        self.video_widgets = []
        self.max_widgets = 15
        self.add_initial_widgets(num_widgets)

    def add_initial_widgets(self, num_widgets):
        """Agregar pantallas de video iniciales según el número indicado."""
        for i in range(num_widgets):
            self.add_video_widget(i)

    def add_video_widget(self, index=None):
        """Agregar una nueva pantalla de video a la cuadrícula, si no se ha alcanzado el máximo."""
        if len(self.video_widgets) < self.max_widgets:
            index = index if index is not None else len(self.video_widgets)
            video_widget = VideoWidget(self.instance, index, self.window_number, parent=self)
            self.video_widgets.append(video_widget)

            row = (len(self.video_widgets) - 1) // 4
            col = (len(self.video_widgets) - 1) % 4

            self.main_layout.addWidget(video_widget, row, col, alignment=Qt.AlignCenter)
            self.save_layout_state()
        else:
            QMessageBox.information(self, "Límite Alcanzado", "Se ha alcanzado el número máximo de viewers (15) en esta ventana.")

    def add_new_window(self):
        """Abrir una nueva ventana para agregar más pantallas de video."""
        if len(MainWindow.ventanas_abiertas) < 5:
            new_window = MainWindow(8)
            new_window.show()
            MainWindow.ventanas_abiertas.append(new_window)
        else:
            QMessageBox.warning(self, "Límite de Ventanas Alcanzado", "Se ha alcanzado el número máximo de ventanas permitidas (5).")

    def activate_admin_mode(self):
        """Activar modo de configuración administrativa."""
        password, ok = QInputDialog.getText(self, 'Contraseña de Administrador', 'Ingrese la contraseña:')
        if ok and password == 'admin':
            QMessageBox.information(self, "Modo Admin", "Modo de configuración administrativa activado.")
            # Abrir admin_multiviewer.py y cerrar multiviewer.py
            subprocess.Popen(["python3", "admin_multiviewer.py"])
            self.close()  # Cerrar la ventana actual de multiviewer

    def save_layout_state(self):
        """Guardar el estado actual del número de pantallas en el archivo JSON."""
        state = load_urls()
        window_key = f'window_{self.window_number}'
        state[window_key] = {'num_widgets': len(self.video_widgets), 'urls': state.get(window_key, {}).get('urls', {}), 'names': state.get(window_key, {}).get('names', {})}
        with open(URLS_FILE, 'w') as file:
            json.dump(state, file)

    def load_layout_state(self):
        """Cargar el estado guardado del archivo JSON y ajustar el número de pantallas en consecuencia."""
        try:
            with open(URLS_FILE, 'r') as file:
                state = json.load(file)
                window_key = f'window_{self.window_number}'
                return state.get(window_key, {}).get('num_widgets', 8)
        except (FileNotFoundError, json.JSONDecodeError):
            return 8

    def closeEvent(self, event):
        """Eliminar la ventana de la lista al cerrarla y detener todos los reproductores."""
        for video_widget in self.video_widgets:
            video_widget.close()
        if self in MainWindow.ventanas_abiertas:
            MainWindow.ventanas_abiertas.remove(self)
        MainWindow.ventana_count -= 1
        event.accept()

# Función principal para ejecutar la aplicación
if __name__ == '__main__':
    app = QApplication(sys.argv)
    initial_widgets = MainWindow().load_layout_state()
    window = MainWindow(initial_widgets)
    window.show()
    sys.exit(app.exec_())
