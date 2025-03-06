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
        text_display.config(state=tk.NORMAL)
        text_display.delete('1.0', tk.END)

        # Jika dalam subdirektori, tambahkan tombol kembali
        if current_path:
            text_display.insert(tk.END, f"🔙 {current_path}\n\n", 'back')

        # Tampilkan folder dengan ikon 📁
        for folder in dirs:
            text_display.insert(tk.END, f"📁 {folder}\n", 'folder')

        # Tambahkan sedikit gap antara folder dan file
        if dirs and files:
            text_display.insert(tk.END, "\n")

        # Tampilkan file dengan ikon 📃
        for file in files:
            text_display.insert(tk.END, f"📃 {file}\n", 'file')

        text_display.config(state=tk.DISABLED)

    except Exception as e:
        messagebox.showerror("Error", f"Gagal terkoneksi: {e}")

# Event klik untuk menyorot teks
def on_text_click(event):
    try:
        text_display.config(state=tk.NORMAL)
        index = text_display.index(tk.CURRENT)
        selected_text = text_display.get(index + " linestart", index + " lineend").strip()

        # Hapus semua highlight sebelumnya
        text_display.tag_remove("selected", "1.0", tk.END)

        # Sorot baris yang dipilih
        text_display.tag_add("selected", index + " linestart", index + " lineend")

        if selected_text.startswith("📁 "):  # Jika folder, masuk ke dalamnya
            folder_name = selected_text[2:].strip()
            connect_ftp(current_path + "/" + folder_name if current_path else folder_name)
        elif selected_text.startswith("🔙 "):  # Jika tombol kembali, naik satu level
            parent_path = "/".join(current_path.split("/")[:-1]) if "/" in current_path else ""
            connect_ftp(parent_path)

        text_display.config(state=tk.DISABLED)
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

# Tagging untuk gaya tampilan
text_display.tag_configure('back', foreground="blue", underline=True)
text_display.tag_configure('folder', foreground="black")
text_display.tag_configure('selected', background="#d0eaff")  # Highlight warna biru muda

# Bind event double click
text_display.bind("<Double-1>", on_text_click)

# Jalankan GUI
root.mainloop()
