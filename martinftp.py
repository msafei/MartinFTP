import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from ftplib import FTP
import configparser
import threading

# Load konfigurasi FTP, OwnCloud, dan lokasi download
def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['FTP'], config['LOCAL'], config['OWNCLOUD']

# Koneksi FTP dan daftar file
def connect_ftp(path=""):
    try:
        global current_path
        current_path = path  # Simpan path saat ini

        ftp_config, _, _ = load_config()
        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        if path:
            ftp.cwd(path)

        files = []
        dirs = []

        def parse_line(line):
            parts = line.split()
            name = " ".join(parts[8:])
            if line.startswith('d'):
                dirs.append(name)
            else:
                files.append(name)

        ftp.retrlines('LIST', parse_line)
        ftp.quit()

        file_listbox.delete(0, tk.END)

        if current_path:
            file_listbox.insert(tk.END, f"../ {current_path}")

        for folder in dirs:
            file_listbox.insert(tk.END, f"📁 {folder}")

        for file in files:
            file_listbox.insert(tk.END, f"📃 {file}")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal terkoneksi ke FTP: {e}")

# Fungsi menampilkan jendela progress
def show_progress_window():
    global progress_window, progress_listbox
    progress_window = tk.Toplevel(root)
    progress_window.title("Transfer Progress")
    progress_window.geometry("400x300")

    tk.Label(progress_window, text="Proses Transfer", font=("Helvetica", 12, "bold")).pack(pady=10)
    progress_listbox = tk.Listbox(progress_window, font=("Segoe UI", 10))
    progress_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    progress_window.grab_set()

# Fungsi update progress
def update_progress(filename, percent):
    for i in range(progress_listbox.size()):
        if filename in progress_listbox.get(i):
            progress_listbox.delete(i)
            progress_listbox.insert(i, f"{filename} - {percent}%")
            break
    root.update_idletasks()

# Fungsi update status di jendela utama
def update_status(filename, downloaded, total_size, percent):
    status_label.config(text=f"Status: {filename} ({downloaded} byte / {total_size} byte) {percent}%")
    root.update_idletasks()

# Fungsi untuk membuka folder setelah unduhan selesai
def open_download_folder():
    _, local_config, _ = load_config()
    download_path = local_config['download_folder']
    if os.path.exists(download_path):
        try:
            os.startfile(download_path)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuka folder: {e}")

# Fungsi download file dari FTP ke lokal
def download_files():
    try:
        ftp_config, local_config, _ = load_config()
        download_path = local_config['download_folder']

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("Peringatan", "Pilih file untuk diunduh!")
            return

        file_names = [file[2:].strip() for file in selected_files if file.startswith("📃 ")]

        show_progress_window()

        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        if current_path:
            ftp.cwd(current_path)

        def download_single_file(filename):
            local_file_path = os.path.join(download_path, filename)
            file_size = ftp.size(filename)
            total_downloaded = 0
            last_percent = -1

            def progress_callback(data):
                nonlocal total_downloaded, last_percent
                total_downloaded += len(data)
                percent = int((total_downloaded / file_size) * 100)
                if percent != last_percent:
                    update_status(filename, total_downloaded, file_size, percent)
                    update_progress(filename, percent)
                    last_percent = percent
                f.write(data)

            with open(local_file_path, "wb") as f:
                ftp.retrbinary(f"RETR {filename}", progress_callback)

            for i in range(progress_listbox.size()):
                if filename in progress_listbox.get(i):
                    progress_listbox.delete(i)
                    break

        for file in file_names:
            download_single_file(file)

        ftp.quit()
        progress_window.destroy()
        messagebox.showinfo("Sukses", f"File berhasil diunduh ke {download_path}")
        open_download_folder()

    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengunduh file: {e}")

# Fungsi upload file ke OwnCloud
def upload_to_owncloud():
    try:
        _, local_config, owncloud_config = load_config()
        download_path = local_config['download_folder']

        selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("Peringatan", "Pilih file untuk diunggah!")
            return

        file_names = [file[2:].strip() for file in selected_files if file.startswith("📃 ")]

        show_progress_window()

        for file_name in file_names:
            local_file_path = os.path.join(download_path, file_name)
            cloud_url = f"{owncloud_config['cloud_url']}/{file_name}"
            auth = (owncloud_config['cloud_username'], owncloud_config['cloud_password'])

            with open(local_file_path, "rb") as f:
                response = requests.put(cloud_url, auth=auth, data=f)

            if response.status_code in [201, 204]:
                update_progress(file_name, 100)
            else:
                messagebox.showerror("Error", f"Gagal mengunggah {file_name} ke OwnCloud: {response.text}")

        progress_window.destroy()
        messagebox.showinfo("Sukses", "File berhasil diunggah ke OwnCloud!")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengunggah file: {e}")

# GUI Utama
root = tk.Tk()
root.title("MartinFTP 📂")
root.geometry("600x620")

frame = ttk.Frame(root, padding=15)
frame.pack(expand=True, fill=tk.BOTH)

title_label = ttk.Label(frame, text="MartinFTP 📂", font=("Helvetica", 18, "bold"))
title_label.pack(pady=(5,0))

title_desc = ttk.Label(frame, text="Daftar file di FTP Server", font=("Helvetica", 11))
title_desc.configure(foreground="#555")
title_desc.pack(pady=(0,10))

btn_download = ttk.Button(frame, text="📥 FTP to Local", command=lambda: threading.Thread(target=download_files).start())
btn_download.pack(pady=(0,5))

btn_upload = ttk.Button(frame, text="☁️ Upload to OwnCloud", command=lambda: threading.Thread(target=upload_to_owncloud).start())
btn_upload.pack(pady=(0,10))

status_label = ttk.Label(frame, text="Status: Menunggu perintah...", font=("Helvetica", 10))
status_label.pack(pady=(0,5))

file_listbox = tk.Listbox(frame, font=("Segoe UI", 10), selectmode=tk.EXTENDED)
file_listbox.pack(expand=True, fill=tk.BOTH)

file_listbox.bind("<Double-Button-1>", lambda e: connect_ftp(current_path))

connect_ftp("")
root.mainloop()
