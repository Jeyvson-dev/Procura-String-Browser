import time
import threading
import tkinter as tk
from tkinter import scrolledtext
import pygame
import unicodedata
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from datetime import datetime

# ---------------- Configurações ----------------
TEMPO_ESPERA = 20
# ------------------------------------------------

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # quando rodar no .exe
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Carregar som
SOM_ALERTA = resource_path("alert.wav")

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
try:
    alert_sound = pygame.mixer.Sound(SOM_ALERTA)
except Exception:
    alert_sound = None
    print("⚠️ Arquivo alert.wav não encontrado. O som não será reproduzido.")

def toca_som():
    if alert_sound:
        alert_sound.play()

def url_valida(url):
    try:
        resultado = urlparse(url.strip())
        return all([resultado.scheme in ['http', 'https'], resultado.netloc])
    except:
        return False

def remover_acentos(txt):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', txt)
        if not unicodedata.combining(c)
    )

def log(msg, log_widget):
    timestamp = datetime.now().strftime("[%H:%M:%S]")
    log_widget.insert(tk.END, f"{timestamp} {msg}\n")
    log_widget.see(tk.END)

def monitorar(url, string_busca, intervalo, stop_event, log_widget):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    string_busca_norm = remover_acentos(string_busca.strip().lower())

    try:
        while not stop_event.is_set():
            try:
                corpo = WebDriverWait(driver, TEMPO_ESPERA).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                texto = corpo.text.strip().lower()
                texto_norm = remover_acentos(texto)

                if string_busca_norm in texto_norm:
                    log(f"✅ String '{string_busca}' encontrada!", log_widget)
                    toca_som()
                else:
                    log(f"❌ String '{string_busca}' não encontrada.", log_widget)
            except Exception as e:
                log(f"⚠️ Erro ao carregar página: {e}", log_widget)

            time.sleep(intervalo)
            driver.refresh()
    finally:
        driver.quit()
        log("🔴 Monitoramento encerrado.", log_widget)

def iniciar_monitoramento():
    url = entry_url.get().strip()
    string_busca = entry_string.get().strip()
    intervalo = entry_intervalo.get().strip()

    if not url_valida(url):
        status_label.config(text="❌ URL inválida!", fg="red")
        return
    if not intervalo.isdigit() or int(intervalo) <= 0:
        status_label.config(text="❌ Intervalo inválido!", fg="red")
        return

    intervalo_int = int(intervalo)

    start_button.config(state="disabled")
    stop_button.config(state="normal")
    status_label.config(text="🟢 Monitoramento iniciado...", fg="green")

    global stop_event
    stop_event = threading.Event()
    global monitor_thread
    monitor_thread = threading.Thread(
        target=monitorar,
        args=(url, string_busca, intervalo_int, stop_event, log_text),
        daemon=True
    )
    monitor_thread.start()

def parar_monitoramento():
    if stop_event:
        stop_event.set()
        stop_button.config(state="disabled")
        start_button.config(state="normal")
        status_label.config(text="🔴 Monitoramento parado.", fg="red")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("🔍 Monitor de Página")
root.configure(bg="#f5f5f5")

FONT_PADRAO = ("Segoe UI", 11)

largura = 750
altura = 600
x = (root.winfo_screenwidth() // 2) - (largura // 2)
y = (root.winfo_screenheight() // 2) - (altura // 2)
root.geometry(f"{largura}x{altura}+{x}+{y}")

container = tk.Frame(root, bg="#f5f5f5")
container.pack(padx=20, pady=20)

tk.Label(container, text="URL:", font=FONT_PADRAO, bg="#f5f5f5").grid(row=0, column=0, sticky="e", pady=5)
entry_url = tk.Entry(container, width=50, font=FONT_PADRAO)
entry_url.grid(row=0, column=1, pady=5)

tk.Label(container, text="String a buscar:", font=FONT_PADRAO, bg="#f5f5f5").grid(row=1, column=0, sticky="e", pady=5)
entry_string = tk.Entry(container, width=50, font=FONT_PADRAO)
entry_string.grid(row=1, column=1, pady=5)

tk.Label(container, text="Intervalo (segundos):", font=FONT_PADRAO, bg="#f5f5f5").grid(row=2, column=0, sticky="e", pady=5)
entry_intervalo = tk.Entry(container, width=10, font=FONT_PADRAO)
entry_intervalo.grid(row=2, column=1, sticky="w", pady=5)

button_frame = tk.Frame(container, bg="#f5f5f5")
button_frame.grid(row=3, column=0, columnspan=2, pady=15)

start_button = tk.Button(
    button_frame, text="▶ Iniciar Monitoramento", command=iniciar_monitoramento,
    bg="#4CAF50", fg="white", font=FONT_PADRAO, width=22
)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(
    button_frame, text="⏹ Parar", command=parar_monitoramento,
    bg="#f44336", fg="white", font=FONT_PADRAO, width=12, state="disabled"
)
stop_button.grid(row=0, column=1, padx=10)

status_label = tk.Label(container, text="", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
status_label.grid(row=4, column=0, columnspan=2, pady=5)

log_text = scrolledtext.ScrolledText(container, width=90, height=20, font=("Consolas", 10))
log_text.grid(row=5, column=0, columnspan=2, padx=5, pady=10)

root.mainloop()
