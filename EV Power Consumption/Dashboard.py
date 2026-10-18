import customtkinter as ctk
import serial
import serial.tools.list_ports
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

SERIAL_BAUD = 9600
MOCK_MODE = False


class DashboardApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("EV Power Monitoring Dashboard")
        self.geometry("1200x850")

        self.time_data = []
        self.power_data = []
        self.start_time = time.time()

        self.ser = None
        self.is_running = True

        self._init_ui()

        self.thread = threading.Thread(target=self._read_serial_data)
        self.thread.daemon = True
        self.thread.start()

    def _init_ui(self):

        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar,
            text="EV MONITOR",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        self.port_option = ctk.CTkOptionMenu(
            self.sidebar,
            values=self._get_ports()
        )
        self.port_option.pack(pady=10)

        self.connect_btn = ctk.CTkButton(
            self.sidebar,
            text="Connect",
            command=self._toggle_connection
        )
        self.connect_btn.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="Status: Disconnected",
            text_color="red"
        )
        self.status_label.pack(pady=10)

        self.main = ctk.CTkFrame(self)
        self.main.pack(
            side="right",
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        self.cards = ctk.CTkFrame(
            self.main,
            fg_color="transparent"
        )
        self.cards.pack(fill="x")

        self.card_voltage = self._create_card("Voltage (V)")
        self.card_current = self._create_card("Current (A)")
        self.card_power = self._create_card("Power (W)")
        self.card_temp = self._create_card("Temp (°C)")
        self.card_accel = self._create_card("Acceleration")
        self.card_lat = self._create_card("Latitude")
        self.card_lng = self._create_card("Longitude")

        self.graph_frame = ctk.CTkFrame(self.main)
        self.graph_frame.pack(
            fill="both",
            expand=True,
            pady=20
        )

        self.fig = Figure(figsize=(5, 4), dpi=100)

        self.ax = self.fig.add_subplot(111)

        self.ax.set_title("Power vs Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Power (W)")

        self.line, = self.ax.plot([], [])

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.graph_frame
        )

        self.canvas.draw()

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

    def _create_card(self, title):

        frame = ctk.CTkFrame(self.cards)

        frame.pack(
            side="left",
            expand=True,
            padx=5,
            pady=10
        )

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=12)
        ).pack()

        label = ctk.CTkLabel(
            frame,
            text="0",
            font=ctk.CTkFont(size=22, weight="bold")
        )

        label.pack(pady=10)

        return label

    def _get_ports(self):

        ports = [
            p.device
            for p in serial.tools.list_ports.comports()
        ]

        return ports if ports else ["No Ports"]

    def _toggle_connection(self):

        if self.ser and self.ser.is_open:

            self.ser.close()

            self.ser = None

            self.connect_btn.configure(text="Connect")

            self.status_label.configure(
                text="Status: Disconnected",
                text_color="red"
            )

        else:

            port = self.port_option.get()

            if port == "No Ports" and not MOCK_MODE:
                return

            try:

                if not MOCK_MODE:

                    self.ser = serial.Serial(
                        port,
                        SERIAL_BAUD,
                        timeout=1
                    )

                self.connect_btn.configure(
                    text="Disconnect"
                )

                self.status_label.configure(
                    text="Status: Connected",
                    text_color="green"
                )

            except Exception as e:

                self.status_label.configure(
                    text=f"Error: {e}",
                    text_color="red"
                )

    def _read_serial_data(self):

        while self.is_running:

            line = ""

            if MOCK_MODE:

                if "Connected" in self.status_label.cget("text"):

                    time.sleep(1)

                    v = 12 + random.uniform(-1, 1)

                    c = 400 + random.uniform(-100, 100)

                    line = (
                        f"V:{v:.2f},"
                        f"C:{c:.2f},"
                        f"P:0,"
                        f"T:30,"
                        f"A:0,"
                        f"La:0,"
                        f"Ln:0"
                    )

            else:

                if self.ser and self.ser.is_open:

                    try:

                        if self.ser.in_waiting:

                            line = (
                                self.ser.readline()
                                .decode()
                                .strip()
                            )

                    except:
                        pass

            if line:

                self.after(
                    0,
                    self._process_data,
                    line
                )

            time.sleep(0.1)

    def _process_data(self, line):

        try:

            parts = line.split(',')

            data = {}

            for part in parts:

                key, value = part.split(':')

                data[key] = float(value)

            voltage = 0
            current_A = 0

            if 'V' in data:

                voltage = data['V']

                self.card_voltage.configure(
                    text=f"{voltage:.2f}"
                )

            if 'C' in data:

                current_A = abs(data['C']) / 1000.0

                self.card_current.configure(
                    text=f"{current_A:.4f}"
                )

            power_W = abs(voltage * current_A)

            self.card_power.configure(
                text=f"{power_W:.4f}"
            )

            current_time = (
                time.time()
                - self.start_time
            )

            self.time_data.append(current_time)

            self.power_data.append(power_W)

            if len(self.time_data) > 60:

                self.time_data.pop(0)

                self.power_data.pop(0)

            self.line.set_data(
                self.time_data,
                self.power_data
            )

            self.ax.relim()

            self.ax.autoscale_view()

            self.canvas.draw()

            if 'T' in data:

                self.card_temp.configure(
                    text=f"{data['T']:.2f}"
                )

            if 'A' in data:

                self.card_accel.configure(
                    text=f"{data['A']:.2f}"
                )

            if 'La' in data:

                self.card_lat.configure(
                    text=f"{data['La']:.6f}"
                )

            if 'Ln' in data:

                self.card_lng.configure(
                    text=f"{data['Ln']:.6f}"
                )

        except:
            pass


if __name__ == "__main__":

    ctk.set_appearance_mode("Dark")

    app = DashboardApp()

    app.mainloop()