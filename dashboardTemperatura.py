import tkinter as tk
import sys
from tkinter import messagebox
import serial
import threading
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl
from openpyxl.chart import LineChart, Reference

# --- CONFIGURACIÓN ---
PUERTO_SERIE = '/dev/ttyUSB0'  # Cambia esto al puerto de tu Arduino
BAUD_RATE = 115200
SIMULACION = False # para probar el dashboard sin el arduino conectado

class DashboardTermocuplas:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Temperatura - Piña")
        self.root.geometry("800x700")
        
        # Variables de datos
        self.tiempo_inicio = time.time()
        self.tiempos = []
        self.temp_s1 = []  # Interior
        self.temp_s2 = []  # Agua
        self.temp_s3 = []  # Superficie
        
        self.leyendo = False
        self.hilo_serial = None
        self.conexion_serial = None
        
        self.crear_interfaz()
        self.iniciar_conexion()
        
        # Configurar el evento de cerrar la ventana (la X roja)
        self.root.protocol("WM_DELETE_WINDOW", self.guardar_y_salir)

    def crear_interfaz(self):
        # --- PANEL DE ETIQUETAS (Temperaturas Actuales) ---
        frame_top = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        frame_top.pack(fill=tk.X)
        
        estilo_label = {"font": ("Arial", 14, "bold"), "bg": "#f0f0f0", "padx": 10}
        
        self.lbl_s1 = tk.Label(frame_top, text="Sensor 1 (Centro): -- °C", fg="red", **estilo_label)
        self.lbl_s1.pack(side=tk.LEFT, expand=True)
        
        self.lbl_s2 = tk.Label(frame_top, text="Sensor 2 (Agua): -- °C", fg="blue", **estilo_label)
        self.lbl_s2.pack(side=tk.LEFT, expand=True)
        
        self.lbl_s3 = tk.Label(frame_top, text="Sensor 3 (Superficie): -- °C", fg="green", **estilo_label)
        self.lbl_s3.pack(side=tk.LEFT, expand=True)
        
        # --- PANEL DE LA GRÁFICA (Matplotlib) ---
        frame_grafica = tk.Frame(self.root)
        frame_grafica.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_grafica)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.configurar_grafica()
        
        # --- PANEL DE BOTONES ---
        frame_botones = tk.Frame(self.root, pady=10)
        frame_botones.pack(fill=tk.X)
        
        btn_guardar = tk.Button(frame_botones, text="Guardar Datos y Salir", font=("Arial", 12, "bold"), 
                                bg="#4CAF50", fg="white", command=self.guardar_y_salir)
        btn_guardar.pack(pady=10, ipadx=20, ipady=5)

    def configurar_grafica(self):
        self.ax.clear()
        self.ax.set_title("Evolución de Temperaturas en Tiempo Real")
        self.ax.set_xlabel("Tiempo (segundos)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax.grid(True, linestyle="--", alpha=0.6)
        
        # Dibujar líneas vacías iniciales
        self.linea_s1, = self.ax.plot([], [], 'r-', label="Sensor 1 (Centro)")
        self.linea_s2, = self.ax.plot([], [], 'b-', label="Sensor 2 (Agua)")
        self.linea_s3, = self.ax.plot([], [], 'g-', label="Sensor 3 (Superficie)")
        self.ax.legend(loc="upper left")

    def iniciar_conexion(self):
        if not SIMULACION:
            try:
                self.conexion_serial = serial.Serial(PUERTO_SERIE, BAUD_RATE, timeout=1)
                time.sleep(2)  # Dar tiempo al Arduino para reiniciar
            except Exception as e:
                messagebox.showerror("Error de Conexión", f"No se pudo abrir el puerto {PUERTO_SERIE}.\n{e}")
                self.root.destroy()
                return

        self.leyendo = True
        self.tiempo_inicio = time.time()
        self.hilo_serial = threading.Thread(target=self.leer_datos, daemon=True)
        self.hilo_serial.start()
        
        # Iniciar ciclo de actualización de la GUI (cada 500 ms)
        self.actualizar_interfaz()

    def leer_datos(self):
        import random # Solo para simulación
        while self.leyendo:
            t_actual = round(time.time() - self.tiempo_inicio, 1)
            
            if SIMULACION:
                # Generar datos falsos si no hay Arduino
                v1, v2, v3 = 25 + t_actual*0.1, 24 + t_actual*0.05, 23 + random.uniform(-0.5, 0.5)
                time.sleep(1)
            else:
                if self.conexion_serial.in_waiting > 0:
                    try:
                        linea = self.conexion_serial.readline().decode('utf-8').strip()
                        datos = linea.split(',')
                        if len(datos) == 3:
                            v1, v2, v3 = float(datos[0]), float(datos[1]), float(datos[2])
                        else:
                            continue
                    except Exception:
                        continue
                else:
                    continue

            # Guardar en las listas
            self.tiempos.append(t_actual)
            self.temp_s1.append(v1)
            self.temp_s2.append(v2)
            self.temp_s3.append(v3)

    def actualizar_interfaz(self):
        if len(self.tiempos) > 0:
            # Actualizar etiquetas
            self.lbl_s1.config(text=f"Sensor 1 (Centro): {self.temp_s1[-1]:.1f} °C")
            self.lbl_s2.config(text=f"Sensor 2 (Agua): {self.temp_s2[-1]:.1f} °C")
            self.lbl_s3.config(text=f"Sensor 3 (Superficie): {self.temp_s3[-1]:.1f} °C")
            
            # Actualizar gráfica
            self.linea_s1.set_data(self.tiempos, self.temp_s1)
            self.linea_s2.set_data(self.tiempos, self.temp_s2)
            self.linea_s3.set_data(self.tiempos, self.temp_s3)
            
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
            
        # Repetir este método cada 500 ms
        if self.leyendo:
            self.root.after(500, self.actualizar_interfaz)

    def guardar_y_salir(self):
        self.leyendo = False
        if self.conexion_serial:
            self.conexion_serial.close()
            
        if len(self.tiempos) == 0:
            self.root.destroy()
            return
            
        # Generar sufijo de fecha para no sobreescribir archivos
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_filename = f"grafica_pina_{fecha_str}.png"
        excel_filename = f"datos_experimento_{fecha_str}.xlsx"
        
        # 1. Guardar la imagen de la gráfica
        self.fig.savefig(img_filename, dpi=300, bbox_inches='tight')
        
        # 2. Guardar a Excel usando Pandas
        df = pd.DataFrame({
            "Tiempo (s)": self.tiempos,
            "Sensor 1 (Centro)": self.temp_s1,
            "Sensor 2 (Agua)": self.temp_s2,
            "Sensor 3 (Superficie)": self.temp_s3
        })
        
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        
        # 3. Insertar la gráfica nativa de Excel dentro del archivo
        wb = openpyxl.load_workbook(excel_filename)
        ws = wb.active
        
        # Configurar el gráfico de Excel (LineChart sin etiquetas en los puntos)
        chart = LineChart()
        chart.title = "Temperatura vs Tiempo"
        chart.x_axis.title = "Tiempo (s)"
        chart.y_axis.title = "Temperatura (°C)"
        chart.style = 13 # Estilo visual nativo
        
        # Referencias de datos: Columnas B, C, D (2, 3, 4). Filas desde la 1 a len(df)+1
        datos_ref = Reference(ws, min_col=2, min_row=1, max_col=4, max_row=len(df)+1)
        # Referencia de categorías (Eje X): Columna A (1). Filas desde 2 a len(df)+1
        cats_ref = Reference(ws, min_col=1, min_row=2, max_row=len(df)+1)
        
        chart.add_data(datos_ref, titles_from_data=True)
        chart.set_categories(cats_ref)
        
        # Insertar el gráfico en la celda F2
        ws.add_chart(chart, "F2")
        wb.save(excel_filename)
        
        messagebox.showinfo("Éxito", f"Experimento guardado con éxito:\n\nImagen: {img_filename}\nDatos: {excel_filename}")
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardTermocuplas(root)
    root.mainloop()