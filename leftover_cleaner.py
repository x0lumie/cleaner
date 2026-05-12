import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import platform
import sys

# ---------- OS Check ----------
def ensure_windows():
    if platform.system() != "Windows":
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Unsupported OS",
                "This app only runs on Windows. The application will now exit."
            )
            root.destroy()
        except Exception:
            print("This app only runs on Windows. Exiting.")
        sys.exit(1)

ensure_windows()

# ---------- Helpers ----------
def format_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} PB"

def get_folder_size(path: Path) -> int:
    total = 0
    try:
        for root, dirs, files in os.walk(path, onerror=lambda e: None):
            for f in files:
                try:
                    fp = Path(root) / f
                    total += fp.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    return total

def build_start_menu_index():
    paths = [
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    index = {}
    for p in paths:
        if p.exists():
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = Path(f).stem.strip()
                        index.setdefault(name.lower(), []).append(name)
    return index

# ---------- GUI ----------
class CleanerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Windows Leftover Cleaner")
        self.geometry("1180x720")

        self.tree = ttk.Treeview(self, columns=("size", "note", "path"), show="headings")
        self.tree.heading("size", text="Size", command=lambda: self.sort_by("size", False))
        self.tree.heading("note", text="Start Menu Note")
        self.tree.heading("path", text="Folder Path", command=lambda: self.sort_by("path", False))
        self.tree.column("size", width=120, anchor="e")
        self.tree.column("note", width=260)
        self.tree.column("path", width=760)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Label(control_frame, text="Min size (MB):").pack(side=tk.LEFT, padx=(0, 5))
        self.min_size_var = tk.StringVar(value="0")
        self.min_size_entry = tk.Entry(control_frame, textvariable=self.min_size_var, width=10)
        self.min_size_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.search_var.trace_add("write", lambda *args: self.apply_filters())

        self.search_mode = tk.StringVar(value="Path")
        ttk.OptionMenu(control_frame, self.search_mode, "Path", "Path", "App Name").pack(side=tk.LEFT, padx=(0, 10))
        self.search_mode.trace_add("write", lambda *args: self.apply_filters())

        self.case_sensitive = tk.BooleanVar(value=False)
        tk.Checkbutton(control_frame, text="Case-sensitive", variable=self.case_sensitive,
                       command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 10))

        self.scan_btn = tk.Button(control_frame, text="Scan Folders", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(control_frame, text="Refresh List", command=self.start_scan)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.delete_btn = tk.Button(control_frame, text="Delete Selected Folder", command=self.delete_selected)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(self, text="Idle", anchor="w")
        self.status.pack(fill=tk.X, padx=10, pady=(0, 2))

        self.totals = tk.Label(self, text="Showing 0 folders • Total size: 0 B", anchor="w")
        self.totals.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.start_menu_index = build_start_menu_index()
        self.all_items = []

    def set_status(self, msg):
        self.status.config(text=msg)
        self.update_idletasks()

    def start_scan(self):
        self.scan_btn.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.all_items.clear()
        threading.Thread(target=self.scan_folders, daemon=True).start()

    def scan_folders(self):
        self.set_status("Scanning...")

        user = Path.home()
        scan_paths = [
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", str(user / "AppData" / "Local"))),
            Path(os.environ.get("APPDATA", str(user / "AppData" / "Roaming"))),
            user
        ]

        for base in scan_paths:
            if not base.exists():
                continue
            try:
                for entry in base.iterdir():
                    if entry.is_dir():
                        size = get_folder_size(entry)
                        name_lower = entry.name.lower()

                        matches = []
                        note = ""
                        if name_lower in self.start_menu_index:
                            matches = sorted(set(self.start_menu_index[name_lower]))
                            note = f"Shortcuts: {', '.join(matches)}"

                        app_names = [entry.name] + matches

                        self.all_items.append({
                            "size_bytes": size,
                            "size_str": format_size(size),
                            "note": note,
                            "path": str(entry),
                            "app_names": app_names
                        })
            except Exception:
                pass

        self.apply_filters()
        self.set_status("Scan complete.")
        self.scan_btn.config(state="normal")

    def apply_filters(self):
        try:
            min_mb = float(self.min_size_var.get())
        except ValueError:
            min_mb = 0
        min_bytes = min_mb * 1024 * 1024

        search = self.search_var.get()
        case_sensitive = self.case_sensitive.get()
        mode = self.search_mode.get()

        def match_text(text: str) -> bool:
            if not search:
                return True
            if case_sensitive:
                return search in text
            return search.lower() in text.lower()

        self.tree.delete(*self.tree.get_children())

        total_size = 0
        count = 0

        for item in self.all_items:
            if item["size_bytes"] < min_bytes:
                continue

            if mode == "Path":
                if not match_text(item["path"]):
                    continue
            else:  # App Name
                if not any(match_text(name) for name in item["app_names"]):
                    continue

            self.tree.insert("", tk.END, values=(item["size_str"], item["note"], item["path"]))
            total_size += item["size_bytes"]
            count += 1

        self.totals.config(text=f"Showing {count} folders • Total size: {format_size(total_size)}")

    def delete_selected(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("No selection", "Please select a folder to delete.")
            return

        path = self.tree.item(item[0], "values")[2]

        if not os.path.isdir(path):
            messagebox.showerror("Error", "Selected folder no longer exists.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete:\n\n{path}"
        )
        if not confirm:
            return

        try:
            shutil.rmtree(path)
            self.tree.delete(item[0])
            self.all_items = [i for i in self.all_items if i["path"] != path]
            self.apply_filters()
            messagebox.showinfo("Deleted", "Folder deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete folder:\n{e}")

    def sort_by(self, col, descending):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        if col == "size":
            def size_to_bytes(s):
                try:
                    num, unit = s.split()
                    num = float(num)
                    unit_map = {"B":1, "KB":1024, "MB":1024**2, "GB":1024**3, "TB":1024**4}
                    return num * unit_map.get(unit, 1)
                except Exception:
                    return 0
            data.sort(key=lambda t: size_to_bytes(t[0]), reverse=descending)
        else:
            data.sort(reverse=descending)

        for index, (val, k) in enumerate(data):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self.sort_by(col, not descending))

if __name__ == "__main__":
    app = CleanerApp()
    app.mainloop()