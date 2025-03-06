import tkinter as tk
from tkinter import ttk, messagebox
from ftplib import FTP
import configparser
from datetime import datetime

# Load konfigurasi FTP
def load_ftp_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

# Fungsi koneksi FTP
def connect_ftp():
    try:
        ftp_config = load_ftp_config()
        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        files = []
        dirs = []

        def parse_line(line):
            parts = line.split()
            name = " ".join(parts[8:])
            if line.startswith('d'):
                dirs.append(name)
            else:
                date_str = " ".join(parts[5:8])
                try:
                    mod_time = datetime.strptime(date_str, '%b %d %H:%M')
                except:
                    mod_time = datetime.now()
                files.append((name, mod_time))

        ftp.retrlines('LIST', parse_line)
        ftp.quit()

        # Urutkan file dari terbaru ke terlama
        files.sort(key=lambda x: x[1], reverse=True)

        # Bersihkan tampilan sebelumnya
        text_display.config(state=tk.NORMAL)
        text_display.delete('1.0', tk.END)

        # Menampilkan folder dengan ikon 📁
        for folder in dirs:
            text_display.insert(tk.END, f"📁 {folder}\n")

        # Tambahkan sedikit jarak antara folder dan file
        if dirs and files:
            text_display.insert(tk.END, "\n")

        # Menampilkan file dengan ikon 📃
        for file, _ in files:
            text_display.insert(tk.END, f"📃 {file}\n")

        text_display.config(state=tk.DISABLED)

        messagebox.showinfo("Berhasil", "File berhasil ditampilkan!")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal terkoneksi: {e}")

# GUI Utama
root = tk.Tk()
root.title("MartinFTP 📂")
root.geometry("600x500")

frame = ttk.Frame(root, padding=15)
frame.pack(expand=True, fill=tk.BOTH)

# Judul
title_label = ttk.Label(frame, text="MartinFTP 📂", font=("Helvetica", 18, "bold"))
title_label.pack(pady=(5,0))

title_desc = ttk.Label(frame, text="Daftar file di FTP Server", font=("Helvetica", 11))
title_desc.configure(foreground="#555")
title_desc.pack(pady=(0,10))

# Tombol koneksi FTP
btn_connect = ttk.Button(frame, text="🔗 Connect FTP", command=connect_ftp)
btn_connect.pack(pady=(0,10))

# Frame text display
text_frame = ttk.Frame(frame)
text_frame.pack(expand=True, fill=tk.BOTH, pady=10)

# Scrollbar
scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Widget Text untuk menampilkan daftar file dan folder
text_display = tk.Text(
    text_frame,
    font=("Segoe UI", 10),
    yscrollcommand=scrollbar.set,
    state=tk.DISABLED,
    relief=tk.FLAT,
    padx=10,
    pady=10
)
text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar.config(command=text_display.yview)

root.mainloop()
