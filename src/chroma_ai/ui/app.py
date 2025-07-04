import time
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk
from qrcode.main import QRCode

from src.chroma_ai.auth.instance_token import token_manager
from src.chroma_ai.services.app_manager import app_manager, ApplicationState
from src.chroma_ai.services.connection_manager import connection_manager


class ChromaAIGui:
    def __init__(self):
        self.qr_label = None
        self.url_entry = None
        self.url_var = None
        self.status_label = None
        self.connection_time_label = None
        self.reset_button = None
        self.loading_message = None
        self.progress_label = None
        self.spinner_label = None

        self.loading_frame = None
        self.disconnected_frame = None
        self.connected_frame = None

        self.is_loading = True
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0

        self.root = tk.Tk()
        self.root.title("Chroma AI Client")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        self.server_thread = None

        self.token = token_manager.get_token()

        self.setup_ui()

        connection_manager.add_observer(self.on_connection_state_changed)

        self.update_ui_state(None)
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
            text="Запускается сервер и создается туннель...",
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
        connection_frame.pack(fill="x", pady=(0, 20))

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

    def setup_connected_ui(self, parent):
        """Setup UI for connected state"""
        self.connected_frame = ttk.Frame(parent)

        status_section = ttk.Frame(self.connected_frame, padding="20")
        status_section.pack(fill="x", pady=(0, 20))

        status_frame = ttk.Frame(status_section)
        status_frame.pack(fill="x", pady=(0, 20))

        self.status_label = ttk.Label(
            status_frame,
            text="🟢 Connected",
            font=("Arial", 18, "bold"),
            foreground="green"
        )
        self.status_label.pack()

        time_frame = ttk.Frame(status_section)
        time_frame.pack(fill="x", pady=(0, 20))

        ttk.Label(time_frame, text="Connection Time:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.connection_time_label = ttk.Label(time_frame, text="00:00:00", font=("Arial", 14))
        self.connection_time_label.pack(anchor="w", pady=(5, 0))

        url_section = ttk.Frame(status_section)
        url_section.pack(fill="x", pady=(0, 20))

        ttk.Label(url_section, text="Tunnel URL:", font=("Arial", 12, "bold")).pack(anchor="w")

        url_frame = ttk.Frame(url_section)
        url_frame.pack(fill="x", pady=(5, 0))

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(
            url_frame,
            textvariable=self.url_var,
            state="readonly",
            font=("Arial", 10)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=3)

        control_frame = ttk.Frame(self.connected_frame)
        control_frame.pack(fill="x", pady=(20, 0))

        self.reset_button = ttk.Button(
            control_frame,
            text="🔄 Reset Connection",
            command=self.reset_connection
        )
        self.reset_button.pack(fill="x", ipady=8)

    def start_spinner_animation(self, _):
        """Start spinner animation"""
        if self.is_loading and hasattr(self, 'spinner_label'):
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            self.spinner_label.config(text=self.spinner_chars[self.spinner_index])

        self.root.after(100, self.start_spinner_animation, None)

    def update_loading_progress(self, message):
        """Update loading progress message"""
        if hasattr(self, 'progress_label'):
            self.root.after(0, self.progress_label.config, message)

    def on_connection_state_changed(self, _):
        """Handle connection state changes"""
        self.root.after(0, self.update_ui_state, None)

    def update_ui_state(self, _):
        """Update UI based on connection and application state"""
        is_connected = connection_manager.is_connected()
        app_state = app_manager.get_state()

        if hasattr(self, 'loading_frame'):
            self.loading_frame.pack_forget()
        if hasattr(self, 'disconnected_frame'):
            self.disconnected_frame.pack_forget()
        if hasattr(self, 'connected_frame'):
            self.connected_frame.pack_forget()

        if app_state in [ApplicationState.INITIALIZING, ApplicationState.STARTING]:
            if hasattr(self, 'loading_frame'):
                self.loading_frame.pack(fill="both", expand=True)
                self.update_loading_message_for_state(app_state)
        elif is_connected:
            if hasattr(self, 'connected_frame'):
                self.connected_frame.pack(fill="both", expand=True)
        else:
            if hasattr(self, 'disconnected_frame'):
                self.disconnected_frame.pack(fill="both", expand=True)
                self.generate_qr_code()

    def update_loading_message_for_state(self, app_state: ApplicationState):
        """Update loading message based on application state"""
        if app_state == ApplicationState.INITIALIZING:
            self.update_loading_progress("Инициализация...")
        elif app_state == ApplicationState.STARTING:
            self.update_loading_progress("Запуск сервисов...")

    def update_connection_time(self, _):
        """Update connection time display"""
        if connection_manager.is_connected() and connection_manager.get_connection_time():
            elapsed = time.time() - connection_manager.get_connection_time()
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if hasattr(self, 'connection_time_label') and self.connection_time_label:
                self.connection_time_label.config(text=time_str)

        self.root.after(1000, self.update_connection_time, None)

    def generate_qr_code(self):
        if self.qr_label:
            qr = QRCode(version=1, box_size=8, border=2)
            qr.add_data(self.token)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((300, 300), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            self.qr_label.config(image=photo)
            self.qr_label.image = photo

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
        connection_manager.remove_observer(self.on_connection_state_changed)
