import logging
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, scrolledtext
from typing import List

import cv2
import numpy as np
from PIL import Image, ImageTk
from qrcode.main import QRCode

from chroma_ai.auth.instance_token import token_manager
from chroma_ai.config.config import WEB_CLIENT_URL, ICON_PATH
from chroma_ai.services.app_manager import app_manager, ApplicationState
from chroma_ai.services.connection_manager import connection_manager
from chroma_ai.services.detection_service import detection_service

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ChromaAIGui:
    def __init__(self, connection_flag: bool = False):
        self.connection_flag = connection_flag

        self.qr_label = None
        self.url_entry = None
        self.url_var = None
        self.status_label = None
        self.connection_time_label = None
        self.reset_button = None
        self.loading_message = None
        self.progress_label = None
        self.spinner_label = None

        # Live camera feed components
        self.camera_feed_label = None
        self.event_log_text = None
        self.current_image = None
        self.speed_label = None

        self.loading_frame = None
        self.disconnected_frame = None
        self.connected_frame = None

        self.is_loading = True
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0

        # Event log storage
        self.event_log_entries: List[str] = []
        self.max_log_entries = 100

        self.root = tk.Tk()

        icon_image = tk.PhotoImage(file=ICON_PATH)
        self.root.iconphoto(True, icon_image)

        self.root.title("Chroma AI Client")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.server_thread = None

        self.token = token_manager.get_token()

        app_manager.add_observer(self.on_app_state_changed)
        
        detection_service.add_log_observer(self.on_detection_event)
        detection_service.add_image_observer(self.on_image_processed)
        detection_service.add_speed_observer(self.on_speed_update)

        self.setup_ui()

        self.update_ui_state(ApplicationState.INITIALIZING)
        self.update_connection_time(None)
        self.start_spinner_animation(None)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.pack(fill="x")

        title_label = ttk.Label(header_frame, text="Chroma AI Client",
                                font=("Arial", 20, "bold"))
        title_label.pack()

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        if not self.connection_flag:
            error_label = ttk.Label(
                main_frame,
                text="Неизвестная ошибка. Проверьте подключение к интернету",
                font=("Arial", 14, "bold"),
                foreground="red"
            )
            error_label.pack(pady=40)

        else:
            self.setup_loading_ui(main_frame)

            self.setup_disconnected_ui(main_frame)

            self.setup_connected_ui(main_frame)

        footer_frame = ttk.Frame(self.root, padding="10")
        footer_frame.pack(fill="x", side="bottom")

        footer_content = ttk.Frame(footer_frame)
        footer_content.pack(fill="x")

        footer_label = ttk.Label(footer_content, text="Chroma AI Windows Client",
                                 font=("Arial", 9), foreground="gray")
        footer_label.pack(side="left")

        quit_button = ttk.Button(
            footer_content,
            text="Quit",
            command=app_manager.shutdown,
            width=8
        )
        quit_button.pack(side="right")

    def setup_loading_ui(self, parent):
        """Setup UI for loading state"""
        self.loading_frame = ttk.Frame(parent)

        loading_section = ttk.Frame(self.loading_frame)
        loading_section.pack(expand=True, fill="both")

        loading_title = ttk.Label(
            loading_section,
            text="Подготовка подключения",
            font=("Arial", 16, "bold")
        )
        loading_title.pack(pady=(100, 20))

        self.spinner_label = ttk.Label(
            loading_section,
            text=self.spinner_chars[0],
            font=("Arial", 32),
            foreground="#0078D4"
        )
        self.spinner_label.pack(pady=(0, 20))

        self.loading_message = ttk.Label(
            loading_section,
            text="Подождите немного...",
            font=("Arial", 11),
            foreground="gray"
        )
        self.loading_message.pack(pady=(0, 20))

        self.progress_label = ttk.Label(loading_section, text="", font=("Arial", 10), foreground="#666")
        self.progress_label.pack()

    def setup_disconnected_ui(self, parent):
        """Setup UI for disconnected state"""
        self.disconnected_frame = ttk.Frame(parent)

        connection_frame = ttk.Frame(self.disconnected_frame, padding="10")
        connection_frame.pack(fill="x")

        qr_section = ttk.Frame(self.disconnected_frame)
        qr_section.pack(fill="both", expand=True)

        qr_title = ttk.Label(qr_section, text="Scan QR Code", font=("Arial", 14, "bold"))
        qr_title.pack(pady=(0, 20))

        qr_subtitle = ttk.Label(
            qr_section,
            text="Сканируйте QR код, чтобы привязать устройство",
            font=("Arial", 10), foreground="gray"
        )
        qr_subtitle.pack(pady=(0, 20))

        self.qr_label = ttk.Label(qr_section)
        self.qr_label.pack(expand=True)
        
        qr = QRCode(version=1, box_size=8, border=2)
        qr.add_data(f"{WEB_CLIENT_URL}/connect?token={self.token}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        # noinspection PyTypeChecker
        self.qr_label.config(image=photo)
        self.qr_label.image = photo

        token_label = ttk.Label(
            qr_section,
            text=f"Или введите токен вручную: {self.token}",
            font=("Arial", 12)
        )
        token_label.pack(pady=(20, 0))

    def setup_connected_ui(self, parent):
        self.connected_frame = ttk.Frame(parent)

        top_frame = ttk.Frame(self.connected_frame)
        top_frame.pack(fill="x", pady=(0, 10))

        camera_frame = ttk.LabelFrame(top_frame, text="Live Camera Feed", padding="10")
        camera_frame.pack(side="left", fill="y", padx=(0, 10))
        camera_frame.config(width=400, height=400)
        camera_frame.pack_propagate(False)

        self.camera_feed_label = ttk.Label(camera_frame, text="No camera feed", 
                                          font=("Arial", 12), foreground="gray")
        self.camera_feed_label.pack(expand=True)

        right_frame = ttk.Frame(top_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        status_frame = ttk.LabelFrame(right_frame, text="Status", padding="10")
        status_frame.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(
            status_frame,
            text="● Подключено",
            font=("Arial", 14, "bold"),
            foreground="green"
        )
        self.status_label.pack(pady=(0, 10))

        time_label = ttk.Label(status_frame, text="Время подключения:", font=("Arial", 10, "bold"))
        time_label.pack(anchor="w", pady=(10, 0))
        self.connection_time_label = ttk.Label(status_frame, text="00:00:00", font=("Arial", 12))
        self.connection_time_label.pack(anchor="w", pady=(5, 0))

        speed_label = ttk.Label(status_frame, text="Скорость:", font=("Arial", 10, "bold"))
        speed_label.pack(anchor="w", pady=(10, 0))
        self.speed_label = ttk.Label(status_frame, text="0.0 FPS", font=("Arial", 12))
        self.speed_label.pack(anchor="w", pady=(5, 0))

        log_frame = ttk.LabelFrame(right_frame, text="Event Log", padding="10")
        log_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.event_log_text = scrolledtext.ScrolledText(
            log_frame,
            height=4,
            width=40,
            font=("Courier", 10),
            state='disabled'
        )
        self.event_log_text.pack(fill="both", expand=True)

        self.add_event_log_entry("Connected")

    def start_spinner_animation(self, _):
        """Start spinner animation"""
        if self.is_loading and self.spinner_label:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            self.spinner_label.config(text=self.spinner_chars[self.spinner_index])

        self.root.after(100, self.start_spinner_animation, None)

    def on_app_state_changed(self, state: ApplicationState):
        self.root.after(0, self.update_ui_state, state)

    def update_ui_state(self, state: ApplicationState):
        if self.loading_frame:
            self.loading_frame.pack_forget()
        if self.disconnected_frame:
            self.disconnected_frame.pack_forget()
        if self.connected_frame:
            self.connected_frame.pack_forget()

        if state in [ApplicationState.INITIALIZING, ApplicationState.STARTING] and self.loading_frame:
            self.loading_frame.pack(fill="both", expand=True)
        elif state == ApplicationState.CONNECTED and self.connected_frame:
            self.connected_frame.pack(fill="both", expand=True)
        elif self.disconnected_frame:
            self.disconnected_frame.pack(fill="both", expand=True)

    def update_connection_time(self, _):
        """Update connection time display"""
        if connection_manager.is_connected() and connection_manager.get_connection_time():
            elapsed = time.time() - connection_manager.get_connection_time()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if self.connection_time_label:
                self.connection_time_label.config(text=time_str)

        self.root.after(1000, self.update_connection_time, None)

    def on_detection_event(self, log: str):
        """Handle detection event from DetectionService"""
        try:
            self.root.after(0, self.add_event_log_entry, log)
        except Exception as e:
            logger.error(f"Error handling detection event: {e}")

    def on_image_processed(self, image: np.ndarray):
        """Handle processed image with bounding boxes"""
        try:
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image

            height, width = image_rgb.shape[:2]
            max_size = 400
            
            if width > max_size or height > max_size:
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height))

            pil_image = Image.fromarray(image_rgb)
            photo = ImageTk.PhotoImage(pil_image)

            self.root.after(0, self.update_camera_feed, photo)
        except Exception as e:
            logger.error(f"Error processing image: {e}")

    def on_speed_update(self, fps: float):
        """Handle processing speed update"""
        try:
            self.root.after(0, self.update_speed_display, fps)
        except Exception as e:
            logger.error(f"Error handling speed update: {e}")

    def update_camera_feed(self, photo):
        """Update camera feed display"""
        try:
            if self.camera_feed_label:
                self.camera_feed_label.config(image=photo)
                self.camera_feed_label.image = photo
        except Exception as e:
            logger.error(f"Error updating camera feed: {e}")

    def update_speed_display(self, fps: float):
        """Update processing speed display"""
        try:
            if self.speed_label:
                self.speed_label.config(text=f"{fps:.1f} FPS")
        except Exception as e:
            logger.error(f"Error updating speed display: {e}")


    def add_event_log_entry(self, message: str):
        """Add entry to event log"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"• [{timestamp}] {message}"
            
            self.event_log_entries.append(log_entry)
            
            if len(self.event_log_entries) > self.max_log_entries:
                self.event_log_entries = self.event_log_entries[-self.max_log_entries:]
            
            if self.event_log_text:
                self.event_log_text.config(state='normal')
                self.event_log_text.delete(1.0, tk.END)
                self.event_log_text.insert(tk.END, '\n'.join(self.event_log_entries))
                self.event_log_text.config(state='disabled')
                self.event_log_text.see(tk.END)
        except Exception as e:
            logger.error(f"Error adding event log entry: {e}")

    def disconnect_connection(self):
        """Disconnect from current connection"""
        try:
            connection_manager.set_disconnected()
            self.add_event_log_entry("Disconnected")
            messagebox.showinfo("Success", "Disconnected successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disconnect: {str(e)}")

    @staticmethod
    def reset_connection():
        """Reset connection and return to disconnected state"""
        try:
            connection_manager.set_disconnected()
            messagebox.showinfo("Success", "Connection reset!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset connection: {str(e)}")

    def run(self):
        self.root.mainloop()

    def __del__(self):
        app_manager.remove_observer(self.on_app_state_changed)
        detection_service.remove_log_observer(self.on_detection_event)
        detection_service.remove_image_observer(self.on_image_processed)
        detection_service.remove_speed_observer(self.on_speed_update)
