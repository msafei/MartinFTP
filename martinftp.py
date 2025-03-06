import os
import tkinter as tk
from tkinter import ttk, messagebox
from ftplib import FTP
import configparser
import threading

# Load konfigurasi FTP dan folder tujuan download
def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['FTP'], config['LOCAL']

# Koneksi FTP dan daftar file
def connect_ftp(path=""):
    try:
        global current_path
        current_path = path  # Simpan path saat ini
        
        ftp_config, _ = load_config()
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
            file_listbox.insert(tk.END, f"../ {current_path}")

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
        elif selected_text.startswith("../"):  # Jika tombol kembali, naik satu level
            parent_path = "/".join(current_path.split("/")[:-1]) if "/" in current_path else ""
            connect_ftp(parent_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Fungsi menampilkan jendela progress
def show_progress_window():
    global progress_window, progress_listbox
    progress_window = tk.Toplevel(root)
    progress_window.title("Download Progress")
    progress_window.geometry("400x250")

    tk.Label(progress_window, text="Proses Download", font=("Helvetica", 12, "bold")).pack(pady=10)
    progress_listbox = tk.Listbox(progress_window, font=("Segoe UI", 10))
    progress_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

# Fungsi update progress
def update_progress(filename, percent):
    for i in range(progress_listbox.size()):
        if filename in progress_listbox.get(i):
            progress_listbox.delete(i)
            progress_listbox.insert(i, f"{filename} - {percent}%")
            break
    root.update_idletasks()

# Fungsi download file dari FTP ke lokal
def download_files():
    try:
        ftp_config, local_config = load_config()
        download_path = local_config['download_folder']

        # Buat folder tujuan jika belum ada
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("Peringatan", "Pilih file untuk diunduh!")
            return

        # Tampilkan progress window jika belum ada
        show_progress_window()

        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        if current_path:
            ftp.cwd(current_path)

        for file in selected_files:
            if file.startswith("📃 "):  # Pastikan hanya file, bukan folder
                filename = file[2:].strip()
                local_file_path = os.path.join(download_path, filename)

                # Tambahkan ke progress window
                progress_listbox.insert(tk.END, f"{filename} - 0%")

                # Ambil ukuran file
                file_size = ftp.size(filename)
                total_downloaded = 0

                # Fungsi callback untuk tracking progress
                def progress_callback(data):
                    nonlocal total_downloaded
                    total_downloaded += len(data)
                    percent = int((total_downloaded / file_size) * 100)
                    update_progress(filename, percent)
                    f.write(data)

                with open(local_file_path, "wb") as f:
                    ftp.retrbinary(f"RETR " + filename, progress_callback)

                # Hapus dari progress window setelah selesai
                for i in range(progress_listbox.size()):
                    if filename in progress_listbox.get(i):
                        progress_listbox.delete(i)
                        break

        ftp.quit()
        messagebox.showinfo("Sukses", f"File berhasil diunduh ke {download_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengunduh file: {e}")

# GUI Utama
root = tk.Tk()
root.title("MartinFTP 📂")
root.geometry("600x550")

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
btn_connect.pack(pady=(0,5))

# Tombol download file
btn_download = ttk.Button(frame, text="📥 FTP to Local", command=lambda: threading.Thread(target=download_files).start())
btn_download.pack(pady=(0,10))

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
