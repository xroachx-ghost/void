"""
VOID GUI

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import Config
from .core.backup import AutoBackup
from .core.device import DeviceDetector
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .core.screen import ScreenCapture
from .terms import ensure_terms_acceptance_gui

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, filedialog
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class Tooltip:
    """Lightweight tooltip helper for Tk widgets."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 500):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: Optional[str] = None
        self._tip_window: Optional[tk.Toplevel] = None

        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event=None) -> None:
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self) -> None:
        if self._tip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + 24

        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        self._tip_window.configure(bg="#0b0f14")

        label = tk.Label(
            self._tip_window,
            text=self.text,
            background="#0b0f14",
            foreground="#e6f1ff",
            relief="solid",
            borderwidth=1,
            font=("Consolas", 9),
            padx=6,
            pady=4,
        )
        label.pack()

    def _hide(self, _event=None) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None


class VoidGUI:
    """User-friendly GUI with an anonymous hacktivist theme."""

    def __init__(self):
        if not GUI_AVAILABLE:
            raise RuntimeError("GUI dependencies missing. Install tkinter to use the GUI.")

        self.root = tk.Tk()
        self.root.title(Config.APP_NAME)
        self.root.geometry("980x640")
        self.root.configure(bg="#0b0f14")

        self.device_ids: List[str] = []
        self.device_info: List[Dict[str, Any]] = []
        self.status_var = tk.StringVar(value="Ready.")
        self.selected_device_var = tk.StringVar(value="No device selected.")
        self.details_var = tk.StringVar(value="Device details will appear here.")
        self.action_help_var = tk.StringVar(
            value="Select an action to see a description."
        )
        self.progress_var = tk.StringVar(value="")
        self._build_layout()
        if not ensure_terms_acceptance_gui(messagebox):
            self.root.destroy()
            raise SystemExit(0)
        self.refresh_devices()

    def _build_layout(self) -> None:
        """Build the themed layout."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Void.TFrame",
            background="#0b0f14"
        )
        style.configure(
            "Void.TLabel",
            background="#0b0f14",
            foreground="#e6f1ff",
            font=("Consolas", 11)
        )
        style.configure(
            "Void.Title.TLabel",
            background="#0b0f14",
            foreground="#00ff9c",
            font=("Consolas", 20, "bold")
        )
        style.configure(
            "Void.TButton",
            background="#111923",
            foreground="#00ff9c",
            font=("Consolas", 11, "bold"),
            borderwidth=1
        )
        style.map(
            "Void.TButton",
            background=[("active", "#1a2633")],
            foreground=[("active", "#7bffce")]
        )

        header = ttk.Frame(self.root, style="Void.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(header, text="VOID", style="Void.Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Anonymous Ops Console • Proprietary to Roach Labs",
            style="Void.TLabel"
        ).pack(anchor="w")

        menu = tk.Menu(self.root, bg="#0b0f14", fg="#e6f1ff", tearoff=0)
        self.root.config(menu=menu)
        app_menu = tk.Menu(menu, tearoff=0, bg="#0b0f14", fg="#e6f1ff")
        app_menu.add_command(label="About", command=self._show_about)
        app_menu.add_command(label="Export Log", command=self._export_log)
        app_menu.add_separator()
        app_menu.add_command(label="Exit", command=self.root.quit)
        menu.add_cascade(label="Void", menu=app_menu)

        body = ttk.Frame(self.root, style="Void.TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        left = ttk.Frame(body, style="Void.TFrame")
        left.pack(side="left", fill="y", padx=(0, 15))

        ttk.Label(left, text="Connected Devices", style="Void.TLabel").pack(anchor="w")
        self.device_list = tk.Listbox(
            left,
            width=36,
            height=18,
            bg="#0f141b",
            fg="#00ff9c",
            selectbackground="#1a2633",
            selectforeground="#e6f1ff",
            highlightthickness=0,
            font=("Consolas", 10)
        )
        self.device_list.pack(pady=(6, 10))
        self.device_list.bind("<<ListboxSelect>>", lambda _: self._on_device_select())
        Tooltip(self.device_list, "Displays connected devices detected via ADB or fastboot.")

        ttk.Button(
            left,
            text="Refresh Devices",
            style="Void.TButton",
            command=self.refresh_devices
        ).pack(fill="x")
        Tooltip(
            left.winfo_children()[-1],
            "Re-scan connected devices and refresh metadata."
        )

        right = ttk.Frame(body, style="Void.TFrame")
        right.pack(side="left", fill="both", expand=True)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        dashboard = ttk.Frame(notebook, style="Void.TFrame")
        logs = ttk.Frame(notebook, style="Void.TFrame")
        help_panel = ttk.Frame(notebook, style="Void.TFrame")
        notebook.add(dashboard, text="Dashboard")
        notebook.add(logs, text="Operations Log")
        notebook.add(help_panel, text="What Does This Do?")

        ttk.Label(dashboard, text="Selected Device", style="Void.TLabel").pack(anchor="w")
        ttk.Label(dashboard, textvariable=self.selected_device_var, style="Void.TLabel").pack(
            anchor="w", pady=(2, 8)
        )

        details = ttk.Frame(dashboard, style="Void.TFrame")
        details.pack(fill="x", pady=(0, 10))
        ttk.Label(details, textvariable=self.details_var, style="Void.TLabel", wraplength=520).pack(
            anchor="w"
        )

        ttk.Label(dashboard, text="Actions", style="Void.TLabel").pack(anchor="w", pady=(6, 0))
        actions = ttk.Frame(dashboard, style="Void.TFrame")
        actions.pack(fill="x", pady=6)

        backup_button = ttk.Button(
            actions,
            text="Create Backup",
            style="Void.TButton",
            command=self._backup
        )
        backup_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(backup_button, "Creates a local backup snapshot of device data.")
        backup_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Create Backup: captures a local snapshot of device data using ADB."
            ),
        )

        analyze_button = ttk.Button(
            actions,
            text="Analyze",
            style="Void.TButton",
            command=self._analyze
        )
        analyze_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(analyze_button, "Collects performance metrics and device diagnostics.")
        analyze_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Analyze: gathers performance and system diagnostics from the device."
            ),
        )

        report_button = ttk.Button(
            actions,
            text="Generate Report",
            style="Void.TButton",
            command=self._report
        )
        report_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(report_button, "Builds an HTML device report with collected metadata.")
        report_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Generate Report: creates an HTML report with device information."
            ),
        )

        screenshot_button = ttk.Button(
            actions,
            text="Screenshot",
            style="Void.TButton",
            command=self._screenshot
        )
        screenshot_button.pack(
            side="left"
        )
        Tooltip(screenshot_button, "Captures a screenshot from the connected device.")
        screenshot_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Screenshot: grabs a current screen capture from the device."
            ),
        )

        ttk.Label(
            dashboard,
            text="Action Descriptions",
            style="Void.TLabel"
        ).pack(anchor="w", pady=(10, 0))
        action_descriptions = (
            "Create Backup — Save a local snapshot of apps and data.\n"
            "Analyze — Collect performance and diagnostic stats.\n"
            "Generate Report — Build an HTML report with device metadata.\n"
            "Screenshot — Capture the current device screen."
        )
        ttk.Label(
            dashboard,
            text=action_descriptions,
            style="Void.TLabel",
            wraplength=520
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(dashboard, text="Quick Tips", style="Void.TLabel").pack(anchor="w", pady=(10, 0))
        tips = (
            "• Use Refresh Devices before each operation.\n"
            "• Reports are generated in HTML for easy sharing.\n"
            "• Operations run in the background; watch the log for progress."
        )
        ttk.Label(dashboard, text=tips, style="Void.TLabel", wraplength=520).pack(anchor="w")

        ttk.Label(logs, text="Operations Log", style="Void.TLabel").pack(anchor="w")
        self.output = scrolledtext.ScrolledText(
            logs,
            height=18,
            bg="#0f141b",
            fg="#e6f1ff",
            insertbackground="#00ff9c",
            font=("Consolas", 10),
            state="disabled"
        )
        self.output.pack(fill="both", expand=True, pady=(6, 0))

        ttk.Label(help_panel, text="Action Details", style="Void.TLabel").pack(anchor="w")
        ttk.Label(
            help_panel,
            textvariable=self.action_help_var,
            style="Void.TLabel",
            wraplength=600
        ).pack(anchor="w", pady=(6, 12))

        guide = (
            "Device List: Shows connected devices. Select one to view metadata.\n"
            "Dashboard: Overview of the selected device and quick actions.\n"
            "Operations Log: Live status output for running tasks.\n"
            "Status Bar: Displays the most recent operation summary."
        )
        ttk.Label(help_panel, text=guide, style="Void.TLabel", wraplength=600).pack(anchor="w")

        status = ttk.Frame(self.root, style="Void.TFrame")
        status.pack(fill="x", padx=20, pady=(0, 12))
        ttk.Label(status, textvariable=self.status_var, style="Void.TLabel").pack(anchor="w")
        ttk.Label(status, textvariable=self.progress_var, style="Void.TLabel").pack(anchor="w")
        self.progress = ttk.Progressbar(
            status,
            mode="indeterminate",
            length=260
        )
        self.progress.pack(anchor="w", pady=(6, 0))

    def _log(self, message: str, level: str = "INFO") -> None:
        """Write a log line to the GUI console."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        def append():
            self.output.configure(state="normal")
            self.output.insert("end", f"[{timestamp}] [{level}] {message}\n")
            self.output.configure(state="disabled")
            self.output.see("end")

        self.root.after(0, append)

    def _run_task(self, label: str, func, *args) -> None:
        """Run a potentially slow task in a background thread."""
        def runner():
            try:
                self._log(f"{label} started...")
                self._start_progress()
                result = func(*args)
                summary = self._summarize_result(label, result)
                self._log(summary)
                self.status_var.set(summary)
            except Exception as exc:
                self._log(f"{label} failed: {exc}", level="ERROR")
                self.status_var.set(f"{label} failed. See log for details.")
            finally:
                self._stop_progress()

        threading.Thread(target=runner, daemon=True).start()

    def _get_selected_device(self) -> Optional[str]:
        """Return the currently selected device."""
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_ids):
            messagebox.showwarning("Void", "Select a device first.")
            return None
        return self.device_ids[selection[0]]

    def _on_device_select(self) -> None:
        """Update dashboard detail view when a device is selected."""
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_info):
            self.selected_device_var.set("No device selected.")
            self.details_var.set("Device details will appear here.")
            return

        info = self.device_info[selection[0]]
        device_id = info.get("id", "unknown")
        manufacturer = info.get("manufacturer", "Unknown")
        model = info.get("model", "Unknown")
        brand = info.get("brand", "Unknown")
        product = info.get("product", "Unknown")
        android = info.get("android_version", "Unknown")
        sdk = info.get("sdk_version", "Unknown")
        security = info.get("security_patch", "Unknown")
        build_id = info.get("build_id", "Unknown")
        build_type = info.get("build_type", "Unknown")
        hardware = info.get("hardware", "Unknown")
        cpu_abi = info.get("cpu_abi", "Unknown")
        battery = info.get("battery", {})
        storage = info.get("storage", {})
        mode = info.get("mode", "Unknown")
        reachable = "Yes" if info.get("reachable", False) else "No"
        self.selected_device_var.set(f"{device_id} • {manufacturer} {model}")
        self.details_var.set(
            "Device Overview\n"
            f"• Mode: {mode} | Reachable: {reachable}\n"
            f"• Brand: {brand} | Product: {product}\n"
            f"• Android: {android} (SDK {sdk})\n"
            f"• Build: {build_id} ({build_type})\n"
            f"• Hardware: {hardware} | ABI: {cpu_abi}\n"
            f"• Security Patch: {security}\n"
            f"• Battery Level: {battery.get('level', 'Unknown')}\n"
            f"• Storage Free: {storage.get('available', 'Unknown')}\n"
            f"• Serial: {device_id}"
        )

    def refresh_devices(self) -> None:
        """Refresh the device list."""
        self.device_list.delete(0, tk.END)
        devices = DeviceDetector.detect_all()
        self.device_ids = []
        self.device_info = []

        if not devices:
            self.device_list.insert(tk.END, "No devices detected")
            self._log("No devices detected", level="WARN")
            self.selected_device_var.set("No device selected.")
            self.details_var.set("Device details will appear here.")
            return

        for device in devices:
            device_id = device.get("id", "unknown")
            reachable = "✓" if device.get("reachable") else "!"
            label = (
                f"{reachable} {device_id} • "
                f"{device.get('manufacturer', 'Unknown')} {device.get('model', '')}"
            )
            self.device_list.insert(tk.END, label.strip())
            self.device_ids.append(device_id)
            self.device_info.append(device)

        self._log(f"Detected {len(self.device_ids)} device(s).")
        self.status_var.set(f"{len(self.device_ids)} device(s) ready.")

    def _backup(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Backup", AutoBackup.create_backup, device_id)

    def _analyze(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Analyze", PerformanceAnalyzer.analyze, device_id)

    def _report(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Report", ReportGenerator.generate_device_report, device_id)

    def _screenshot(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Screenshot", ScreenCapture.take_screenshot, device_id)

    def run(self) -> None:
        """Start the GUI event loop."""
        self._log("Void GUI ready.")
        self.root.mainloop()

    def _summarize_result(self, label: str, result: Any) -> str:
        """Create a friendly summary of an operation result."""
        if isinstance(result, dict):
            success = result.get("success")
            if success is True:
                detail = result.get("message") or result.get("report_name") or "Completed successfully."
                return f"{label} complete: {detail}"
            if success is False:
                error = result.get("error") or result.get("message") or "Operation failed."
                return f"{label} failed: {error}"
        return f"{label} complete."

    def _show_about(self) -> None:
        """Display the About dialog."""
        messagebox.showinfo(
            "About Void",
            "Void\n"
            f"Version {Config.VERSION} ({Config.CODENAME})\n\n"
            "Proprietary Software\n"
            "© 2024 Roach Labs\n"
            "Made by James Michael Roach Jr."
        )

    def _export_log(self) -> None:
        """Export the operations log to a text file."""
        path = filedialog.asksaveasfilename(
            title="Export Log",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
        )
        if not path:
            return
        self.output.configure(state="normal")
        content = self.output.get("1.0", "end").strip()
        self.output.configure(state="disabled")
        with open(path, "w") as handle:
            handle.write(content)
        self.status_var.set(f"Log exported to {path}.")

    def _start_progress(self) -> None:
        self.root.after(0, lambda: self.progress_var.set("Working..."))
        self.root.after(0, lambda: self.progress.start(10))

    def _stop_progress(self) -> None:
        self.root.after(0, self.progress.stop)
        self.root.after(0, lambda: self.progress_var.set(""))


def run_gui() -> None:
    """Launch the graphical interface if available."""
    if not GUI_AVAILABLE:
        print(
            "GUI not available. Install tkinter (python3-tk on Linux) to use the GUI."
        )
        return

    Config.setup()

    gui = VoidGUI()
    gui.run()


__all__ = ["VoidGUI", "run_gui", "GUI_AVAILABLE"]
