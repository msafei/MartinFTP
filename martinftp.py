import tkinter as tk
from tkinter import ttk, messagebox
from ftplib import FTP
import configparser

# Load konfigurasi FTP
def load_ftp_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

# Koneksi FTP dan daftar file
def connect_ftp(path=""):
    try:
        global current_path
        current_path = path  # Simpan path saat ini
        
        ftp_config = load_ftp_config()
        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        if path:
            ftp.cwd(path)

        files = []
        dirs = []

        # Ambil daftar file dan folder
        def parse_line(line):
            parts = line.split()
            name = " ".join(parts[8:])
            if line.startswith('d'):
                dirs.append(name)
            else:
                files.append(name)

        ftp.retrlines('LIST', parse_line)
        ftp.quit()

        # Bersihkan tampilan sebelumnya
        file_listbox.delete(0, tk.END)

        # Jika dalam subdirektori, tambahkan tombol kembali
        if current_path:
            file_listbox.insert(tk.END, f" ../ {current_path}")

        # Tampilkan folder dengan ikon 📁
        for folder in dirs:
            file_listbox.insert(tk.END, f"📁 {folder}")

        # Tampilkan file dengan ikon 📃
        for file in files:
            file_listbox.insert(tk.END, f"📃 {file}")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal terkoneksi: {e}")

# Event double-click untuk membuka folder
def on_item_double_click(event):
    try:
        selected_indices = file_listbox.curselection()
        if not selected_indices:
            return

        selected_text = file_listbox.get(selected_indices[0])

        if selected_text.startswith("📁 "):  # Jika folder, masuk ke dalamnya dengan double click
            folder_name = selected_text[2:].strip()
            connect_ftp(current_path + "/" + folder_name if current_path else folder_name)
        elif selected_text.startswith(" ../"):  # Jika tombol kembali, naik satu level
            parent_path = "/".join(current_path.split("/")[:-1]) if "/" in current_path else ""
            connect_ftp(parent_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

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
btn_connect = ttk.Button(frame, text="🔗 Connect FTP", command=lambda: connect_ftp(""))
btn_connect.pack(pady=(0,10))

# Frame listbox
file_frame = ttk.Frame(frame)
file_frame.pack(expand=True, fill=tk.BOTH, pady=10)

# Scrollbar
scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Listbox untuk daftar file dan folder
file_listbox = tk.Listbox(
    file_frame,
    font=("Segoe UI", 10),
    selectmode=tk.EXTENDED,  # Multi-selection
    yscrollcommand=scrollbar.set
)
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar.config(command=file_listbox.yview)

# Bind event double-click untuk membuka folder
file_listbox.bind("<Double-Button-1>", on_item_double_click)

# Jalankan GUI
root.mainloop()
