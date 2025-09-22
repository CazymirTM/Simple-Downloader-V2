import sys, os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests

# ---------- YOUR PROGRAM LIST ----------
PROGRAMS = {
    "WinRAR": "https://www.win-rar.com/fileadmin/winrar-versions/winrar/winrar-x64-713.exe",
    "CPU-Z": "https://download.cpuid.com/cpu-z/cpu-z_2.16-en.exe",
    "Automatic Driver Installer": "https://www.glenn.delahoy.com/downloads/sdio/SDIO_1.15.5.816.zip",
    "DirectX All In One": "https://download.microsoft.com/download/1/7/1/1718ccc4-6315-4d8e-9543-8e28a4e18c4c/dxwebsetup.exe",
    "Bundle of usefull apps": "https://github.com/CazymirTM/simpledownloaderneeds/raw/refs/heads/main/Ninite%20Chrome%20Java%20AdoptOpenJDK%208%20Installer.exe",
    "GIMP": "https://download.gimp.org/mirror/pub/gimp/v2.10/windows/gimp-2.10.38-setup-1.exe"
}


# ---------- Helpers ----------
def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.2f} {units[i]}"


# ---------- GUI App ----------
class DownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Simple Downloader V2 by CeZeY")

        # Program selection
        tk.Label(master, text="Select programs to download:").pack(anchor="w", padx=5, pady=(5, 0))
        self.program_vars = {}
        for name in PROGRAMS.keys():
            var = tk.BooleanVar()
            cb = tk.Checkbutton(master, text=name, variable=var)
            cb.pack(anchor="w", padx=15)
            self.program_vars[name] = var

        # Output folder
        self.outdir = tk.StringVar(value=str(Path.cwd() / "downloads"))
        tk.Label(master, text="Download folder:").pack(anchor="w", padx=5, pady=(8, 0))
        dir_frame = tk.Frame(master)
        dir_frame.pack(fill="x", padx=5)
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.outdir, width=45)
        self.dir_entry.pack(side="left", fill="x", expand=True)
        tk.Button(dir_frame, text="Browse", command=self.choose_dir).pack(side="right")

        # Start button
        tk.Button(master, text="Download Selected", command=self.start_downloads).pack(pady=8)

        # Progress area
        self.progress_frame = tk.Frame(master)
        self.progress_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.progress_bars = {}   # {program: (label, progressbar)}

        # Credit label
        credit = tk.Label(master, text="by CeZeY", font=("Segoe UI", 12, "bold italic"), fg="blue")
        credit.pack(side="bottom", pady=(0, 5))

    def choose_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.outdir.set(folder)

    def start_downloads(self):
        # Reset old progress bars
        for widget in self.progress_frame.winfo_children():
            widget.destroy()
        self.progress_bars.clear()

        # Collect selected programs
        selected = [name for name, var in self.program_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("No selection", "Please select at least one program to download.")
            return

        outdir = Path(self.outdir.get())
        outdir.mkdir(parents=True, exist_ok=True)

        # Create progress bars for selected
        for name in selected:
            row = tk.Frame(self.progress_frame)
            row.pack(fill="x", pady=2)
            label = tk.Label(row, text=name, width=20, anchor="w")
            label.pack(side="left")
            bar = ttk.Progressbar(row, length=300)
            bar.pack(side="left", fill="x", expand=True, padx=5)
            self.progress_bars[name] = (label, bar)

        # Start downloads in background thread
        thread = threading.Thread(target=self.download_all, args=(selected, outdir), daemon=True)
        thread.start()

    def update_progress(self, name, value, maximum):
        label, bar = self.progress_bars[name]
        bar["maximum"] = maximum
        bar["value"] = value
        if value >= maximum:
            label.configure(text=f"{name} (Done ✔)")
        self.master.update_idletasks()

    def download_all(self, selected, outdir: Path):
        session = requests.Session()
        for name in selected:
            url = PROGRAMS[name]
            try:
                r = session.head(url, allow_redirects=True, timeout=15)
                size = r.headers.get("Content-Length")
                total_size = int(size) if size and size.isdigit() else None
                filename = os.path.basename(url.split("?")[0])
                target = outdir / filename

                with session.get(url, stream=True, timeout=30) as resp:
                    resp.raise_for_status()
                    with open(target, "wb") as f:
                        downloaded = 0
                        for chunk in resp.iter_content(chunk_size=1024 * 128):
                            if not chunk:
                                continue
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                self.update_progress(name, downloaded, total_size)

                if not total_size:
                    self.update_progress(name, 1, 1)

            except Exception as e:
                label, bar = self.progress_bars[name]
                label.configure(text=f"{name} (Failed ❌)")
                print(f"Failed {name}: {e}")


# ---------- Run ----------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    root = tk.Tk()

    
    icon_path = resource_path("icon.ico")
    root.iconbitmap(icon_path)

    app = DownloaderApp(root)
    root.mainloop()