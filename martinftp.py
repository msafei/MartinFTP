import os
import tkinter as tk
from tkinter import ttk, messagebox
from ftplib import FTP
import configparser
import threading

# 1. Load konfigurasi FTP dan folder tujuan download
def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['FTP'], config['LOCAL']

# 2. Koneksi FTP dan daftar file
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

        # 2.1. Ambil daftar file dan folder
        def parse_line(line):
            parts = line.split()
            name = " ".join(parts[8:])
            if line.startswith('d'):
                dirs.append(name)
            else:
                files.append(name)

        ftp.retrlines('LIST', parse_line)
        ftp.quit()

        # 2.2. Bersihkan tampilan sebelumnya
        file_listbox.delete(0, tk.END)

        # 2.3. Jika dalam subdirektori, tambahkan tombol kembali
        if current_path:
            file_listbox.insert(tk.END, f" ../ {current_path}")

        # 2.4. Tampilkan folder dengan ikon 📁
        for folder in dirs:
            file_listbox.insert(tk.END, f"📁 {folder}")

        # 2.5. Tampilkan file dengan ikon 📃
        for file in files:
            file_listbox.insert(tk.END, f"📃 {file}")

    except Exception as e:
        messagebox.showerror("Error", f"Gagal terkoneksi: {e}")

# 3. Event double-click untuk membuka folder
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

# 4. Fungsi menampilkan jendela progress
def show_progress_window(files):
    global progress_window, progress_listbox
    progress_window = tk.Toplevel(root)
    progress_window.title("Download Progress")
    progress_window.geometry("400x300")

    tk.Label(progress_window, text="Proses Download", font=("Helvetica", 12, "bold")).pack(pady=10)
    progress_listbox = tk.Listbox(progress_window, font=("Segoe UI", 10))
    progress_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    # 4.1. Tambahkan semua file ke dalam progress window
    for file in files:
        progress_listbox.insert(tk.END, f"{file} - 0%")

    # 4.2. Mencegah interaksi dengan jendela utama
    progress_window.grab_set()

# 5. Fungsi update status di jendela utama
def update_status(filename, downloaded, total_size, percent):
    status_label.config(text=f"Status: {filename} ({downloaded} byte / {total_size} byte) {percent}%")
    root.update_idletasks()

# 6. Fungsi update progress di jendela progress
def update_progress(filename, percent):
    for i in range(progress_listbox.size()):
        if filename in progress_listbox.get(i):
            progress_listbox.delete(i)
            progress_listbox.insert(i, f"{filename} - {percent}%")
            break
    root.update_idletasks()

# 7. Fungsi untuk membuka folder setelah unduhan selesai
def open_download_folder():
    _, local_config = load_config()
    download_path = local_config['download_folder']
    if os.path.exists(download_path):
        try:
            os.startfile(download_path)  # Windows: Membuka folder yang benar
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuka folder: {e}")

# 8. Fungsi download file dari FTP ke lokal
def download_files():
    try:
        ftp_config, local_config = load_config()
        download_path = local_config['download_folder']

        # 8.1. Buat folder tujuan jika belum ada
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("Peringatan", "Pilih file untuk diunduh!")
            return

        # 8.2. Ambil nama file tanpa ikon
        file_names = [file[2:].strip() for file in selected_files if file.startswith("📃 ")]

        # 8.3. Tampilkan progress window
        show_progress_window(file_names)

        ftp = FTP()
        ftp.connect(ftp_config['host'], int(ftp_config['port']))
        ftp.login(ftp_config['username'], ftp_config['password'])

        if current_path:
            ftp.cwd(current_path)

        # 8.4. Fungsi download file tunggal
        def download_single_file(filename):
            local_file_path = os.path.join(download_path, filename)

            # 8.4.1. Ambil ukuran file
            file_size = ftp.size(filename)
            total_downloaded = 0
            last_percent = -1  # Untuk menghindari refresh yang tidak perlu

            # 8.4.2. Fungsi callback untuk tracking progress
            def progress_callback(data):
                nonlocal total_downloaded, last_percent
                total_downloaded += len(data)
                percent = int((total_downloaded / file_size) * 100)
                if percent != last_percent:  # Hanya update jika ada perubahan
                    update_status(filename, total_downloaded, file_size, percent)
                    update_progress(filename, percent)
                    last_percent = percent
                f.write(data)

            with open(local_file_path, "wb") as f:
                ftp.retrbinary(f"RETR {filename}", progress_callback)

            # 8.4.3. Hapus dari progress window setelah selesai
            for i in range(progress_listbox.size()):
                if filename in progress_listbox.get(i):
                    progress_listbox.delete(i)
                    break

        # 8.5. Mulai proses download
        for file in file_names:
            download_single_file(file)

        ftp.quit()

        # 8.6. Tutup progress window setelah semua file selesai
        progress_window.destroy()
        update_status("Semua unduhan selesai", 0, 0, 100)

        # 8.7. Menampilkan pesan sukses dan membuka folder setelah OK ditekan
        messagebox.showinfo("Sukses", f"File berhasil diunduh ke {download_path}")
        open_download_folder()

    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengunduh file: {e}")

# 9. GUI Utama
root = tk.Tk()
root.title("MartinFTP 📂")
root.geometry("650x600")

frame = ttk.Frame(root, padding=20)
frame.pack(expand=True, fill=tk.BOTH)

# 9.1. Judul aplikasi
title_label = ttk.Label(frame, text="MartinFTP 📂", font=("Helvetica", 20, "bold"))
title_label.pack(pady=(5,10))

# 9.2. Tombol download
btn_download = ttk.Button(frame, text="📥  FTP to Local", command=lambda: threading.Thread(target=download_files).start(), style="TButton")
btn_download.pack(pady=(5,15), ipadx=10, ipady=10)

# 9.3. Status label
status_label = ttk.Label(frame, text="Status: Menunggu perintah...", font=("Helvetica", 11))
status_label.pack(pady=(0,10))

# 9.4. Listbox file
file_listbox = tk.Listbox(frame, font=("Segoe UI", 11), selectmode=tk.EXTENDED, height=20)
file_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

file_listbox.bind("<Double-Button-1>", on_item_double_click)

# 10. Koneksi FTP awal
connect_ftp("")  

root.mainloop()
