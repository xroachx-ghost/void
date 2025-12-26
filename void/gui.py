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
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .core.backup import AutoBackup
from .core.device import DeviceDetector
from .core.partitions import PartitionManager
from .core.recovery import RecoveryWorkflow
from .core.rom_validation import RomValidator
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .core.screen import ScreenCapture
from .plugins import PluginContext, PluginMetadata, PluginResult, discover_plugins, get_registry
from .terms import ensure_terms_acceptance_gui

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
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

        discover_plugins()
        self.plugin_registry = get_registry()

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
        self.plugin_description_var = tk.StringVar(
            value="Select a plugin to view details."
        )
        self.progress_var = tk.StringVar(value="")
        self.plugin_metadata: List[PluginMetadata] = []
        self._build_layout()
        if not ensure_terms_acceptance_gui(messagebox):
            self.root.destroy()
            raise SystemExit(0)
        self.refresh_devices()
        self._load_plugins()

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
        plugins_panel = ttk.Frame(notebook, style="Void.TFrame")
        notebook.add(dashboard, text="Dashboard")
        notebook.add(logs, text="Operations Log")
        notebook.add(plugins_panel, text="Plugins")
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

        ttk.Label(dashboard, text="Security & Recovery", style="Void.TLabel").pack(
            anchor="w", pady=(10, 0)
        )
        advanced_row = ttk.Frame(dashboard, style="Void.TFrame")
        advanced_row.pack(fill="x", pady=6)

        bootstatus_button = ttk.Button(
            advanced_row,
            text="Boot Status",
            style="Void.TButton",
            command=self._bootloader_status,
        )
        bootstatus_button.pack(side="left", padx=(0, 8))
        Tooltip(bootstatus_button, "Query bootloader and OEM unlock state.")
        bootstatus_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Boot Status: checks verified boot and OEM unlock properties."
            ),
        )

        list_partitions_button = ttk.Button(
            advanced_row,
            text="List Partitions",
            style="Void.TButton",
            command=self._list_partitions,
        )
        list_partitions_button.pack(side="left", padx=(0, 8))
        Tooltip(list_partitions_button, "List device partitions via adb/fastboot.")
        list_partitions_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "List Partitions: displays known partition names for the device."
            ),
        )

        hash_partition_button = ttk.Button(
            advanced_row,
            text="Hash Partition",
            style="Void.TButton",
            command=self._hash_partition,
        )
        hash_partition_button.pack(side="left")
        Tooltip(hash_partition_button, "Compute SHA-256 for a partition.")
        hash_partition_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Hash Partition: calculates SHA-256 for a selected partition."
            ),
        )

        advanced_row2 = ttk.Frame(dashboard, style="Void.TFrame")
        advanced_row2.pack(fill="x", pady=6)

        dump_partition_button = ttk.Button(
            advanced_row2,
            text="Dump Partition",
            style="Void.TButton",
            command=self._dump_partition,
        )
        dump_partition_button.pack(side="left", padx=(0, 8))
        Tooltip(dump_partition_button, "Dump a partition image to disk.")
        dump_partition_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Dump Partition: exports a partition image to a chosen file."
            ),
        )

        validate_rom_button = ttk.Button(
            advanced_row2,
            text="Validate ROM",
            style="Void.TButton",
            command=self._validate_rom,
        )
        validate_rom_button.pack(side="left", padx=(0, 8))
        Tooltip(validate_rom_button, "Validate a ROM file checksum.")
        validate_rom_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Validate ROM: checks a ROM file against a checksum."
            ),
        )

        recovery_button = ttk.Button(
            advanced_row2,
            text="Reboot Recovery",
            style="Void.TButton",
            command=self._reboot_recovery,
        )
        recovery_button.pack(side="left")
        Tooltip(recovery_button, "Reboot the device into recovery mode.")
        recovery_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Reboot Recovery: safely reboot the device into recovery mode."
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
            "Screenshot — Capture the current device screen.\n"
            "Boot Status — Check verified boot and OEM unlock properties.\n"
            "List Partitions — Display partition names for browsing.\n"
            "Hash/Dump Partition — Verify or export partition images.\n"
            "Validate ROM — Confirm ROM checksums before flashing.\n"
            "Reboot Recovery — Safely switch into recovery mode."
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

        ttk.Label(plugins_panel, text="Registered Plugins", style="Void.TLabel").pack(anchor="w")
        plugin_controls = ttk.Frame(plugins_panel, style="Void.TFrame")
        plugin_controls.pack(fill="both", expand=True, pady=(6, 0))

        self.plugin_list = tk.Listbox(
            plugin_controls,
            width=36,
            height=12,
            bg="#0f141b",
            fg="#00ff9c",
            selectbackground="#1a2633",
            selectforeground="#e6f1ff",
            highlightthickness=0,
            font=("Consolas", 10),
        )
        self.plugin_list.pack(side="left", fill="y", padx=(0, 12))
        self.plugin_list.bind("<<ListboxSelect>>", lambda _: self._on_plugin_select())
        Tooltip(self.plugin_list, "Select a plugin to see details or run it.")

        plugin_details = ttk.Frame(plugin_controls, style="Void.TFrame")
        plugin_details.pack(side="left", fill="both", expand=True)

        ttk.Label(plugin_details, text="Details", style="Void.TLabel").pack(anchor="w")
        ttk.Label(
            plugin_details,
            textvariable=self.plugin_description_var,
            style="Void.TLabel",
            wraplength=420,
        ).pack(anchor="w", pady=(4, 10))

        plugin_actions = ttk.Frame(plugin_details, style="Void.TFrame")
        plugin_actions.pack(anchor="w")
        ttk.Button(
            plugin_actions,
            text="Refresh Plugins",
            style="Void.TButton",
            command=self._load_plugins,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            plugin_actions,
            text="Run Plugin",
            style="Void.TButton",
            command=self._run_selected_plugin,
        ).pack(side="left")

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

    def _load_plugins(self) -> None:
        """Load plugins into the list view."""
        plugins = self.plugin_registry.list_metadata()
        self.plugin_metadata = plugins
        self.plugin_list.delete(0, "end")

        for plugin in plugins:
            self.plugin_list.insert("end", f"{plugin.name} ({plugin.id})")

        if plugins:
            self.plugin_description_var.set("Select a plugin to view details.")
        else:
            self.plugin_description_var.set("No plugins registered.")

    def _on_plugin_select(self) -> None:
        """Update plugin details when selection changes."""
        selection = self.plugin_list.curselection()
        if not selection or selection[0] >= len(self.plugin_metadata):
            return

        plugin = self.plugin_metadata[selection[0]]
        tags = ", ".join(plugin.tags) if plugin.tags else "None"
        details = (
            f"{plugin.name} ({plugin.id})\n"
            f"Version: {plugin.version}\n"
            f"Author: {plugin.author}\n"
            f"Tags: {tags}\n\n"
            f"{plugin.description}"
        )
        self.plugin_description_var.set(details)

    def _run_selected_plugin(self) -> None:
        """Run the selected plugin."""
        selection = self.plugin_list.curselection()
        if not selection or selection[0] >= len(self.plugin_metadata):
            messagebox.showwarning("Void", "Select a plugin first.")
            return

        plugin = self.plugin_metadata[selection[0]]
        self._run_task(f"Plugin {plugin.name}", self._execute_plugin, plugin.id)

    def _execute_plugin(self, plugin_id: str) -> PluginResult:
        """Execute a plugin and return its result."""
        context = PluginContext(mode="gui", emit=lambda msg: self._log(msg, level="PLUGIN"))
        return self.plugin_registry.run(plugin_id, context, [])

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
        bootloader_status = info.get("bootloader_status", {})
        verified_boot = bootloader_status.get("verified_boot_state", "Unknown")
        lock_state = bootloader_status.get("bootloader_lock_state", bootloader_status.get("bootloader_locked", "Unknown"))
        self.selected_device_var.set(f"{device_id} • {manufacturer} {model}")
        self.details_var.set(
            "Device Overview\n"
            f"• Mode: {mode} | Reachable: {reachable}\n"
            f"• Brand: {brand} | Product: {product}\n"
            f"• Android: {android} (SDK {sdk})\n"
            f"• Build: {build_id} ({build_type})\n"
            f"• Hardware: {hardware} | ABI: {cpu_abi}\n"
            f"• Security Patch: {security}\n"
            f"• Verified Boot: {verified_boot} | Bootloader: {lock_state}\n"
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

    def _bootloader_status(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Boot Status", self._fetch_bootloader_status, device_id)

    def _fetch_bootloader_status(self, device_id: str) -> Dict[str, Any]:
        status = DeviceDetector.get_bootloader_status(device_id)
        if not status:
            return {"success": False, "message": "Unable to query bootloader status."}
        details = ", ".join(f"{key}={value}" for key, value in status.items())
        self._log(f"Bootloader status: {details}")
        return {"success": True, "message": "Bootloader status captured."}

    def _list_partitions(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("List Partitions", self._fetch_partitions, device_id)

    def _fetch_partitions(self, device_id: str) -> Dict[str, Any]:
        mode = PartitionManager.detect_device_mode(device_id)
        partitions = PartitionManager.list_partitions(device_id, mode=mode)
        if not partitions:
            return {"success": False, "message": "No partitions found."}
        self._log(f"Partitions ({mode}):")
        for part in partitions:
            details = part.get("name", "unknown")
            if part.get("size"):
                details += f" size={part.get('size')}"
            if part.get("type"):
                details += f" type={part.get('type')}"
            self._log(f"  {details}")
        return {"success": True, "message": f"{len(partitions)} partitions listed."}

    def _hash_partition(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        partition = simpledialog.askstring("Hash Partition", "Enter partition name:")
        if not partition:
            return
        self._run_task("Hash Partition", self._execute_hash_partition, device_id, partition)

    def _execute_hash_partition(self, device_id: str, partition: str) -> Dict[str, Any]:
        mode = PartitionManager.detect_device_mode(device_id)
        result = PartitionManager.hash_partition(device_id, partition, mode=mode)
        if result.get("success"):
            self._log(f"{partition} sha256: {result.get('hash')}")
            return {"success": True, "message": f"Hash complete for {partition}."}
        return {"success": False, "message": result.get("message", "Hash failed.")}

    def _dump_partition(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        partition = simpledialog.askstring("Dump Partition", "Enter partition name:")
        if not partition:
            return
        output_path = filedialog.asksaveasfilename(
            title="Save Partition Image",
            defaultextension=".img",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")],
        )
        if not output_path:
            return
        self._run_task(
            "Dump Partition",
            self._execute_dump_partition,
            device_id,
            partition,
            Path(output_path),
        )

    def _execute_dump_partition(
        self, device_id: str, partition: str, output_path: Path
    ) -> Dict[str, Any]:
        mode = PartitionManager.detect_device_mode(device_id)
        result = PartitionManager.dump_partition(device_id, partition, output_path, mode=mode)
        if result.get("success"):
            return {
                "success": True,
                "message": f"Partition dumped to {result.get('path')}",
            }
        return {"success": False, "message": result.get("message", "Dump failed.")}

    def _validate_rom(self) -> None:
        rom_path = filedialog.askopenfilename(
            title="Select ROM File",
            filetypes=[("ROM Images", "*.zip *.img *.bin"), ("All Files", "*.*")],
        )
        if not rom_path:
            return
        checksum_input = simpledialog.askstring(
            "Validate ROM",
            "Enter checksum or leave blank to select a checksum file:",
        )
        if not checksum_input:
            checksum_file = filedialog.askopenfilename(
                title="Select Checksum File",
                filetypes=[
                    ("Checksum Files", "*.sha256 *.sha1 *.md5 *.txt"),
                    ("All Files", "*.*"),
                ],
            )
            if not checksum_file:
                return
            checksum_input = checksum_file
        self._run_task(
            "Validate ROM",
            self._execute_validate_rom,
            Path(rom_path),
            checksum_input,
        )

    def _execute_validate_rom(self, rom_path: Path, checksum_input: str) -> Dict[str, Any]:
        result = RomValidator.validate_checksum(rom_path, checksum_input)
        if result.get("success"):
            self._log(f"ROM checksum verified ({result.get('algorithm')}).")
            return {"success": True, "message": "ROM checksum verified."}
        self._log("ROM checksum mismatch.")
        return {"success": False, "message": result.get("message", "Checksum mismatch.")}

    def _reboot_recovery(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Reboot Recovery", RecoveryWorkflow.reboot_to_recovery, device_id)

    def run(self) -> None:
        """Start the GUI event loop."""
        self._log("Void GUI ready.")
        self.root.mainloop()

    def _summarize_result(self, label: str, result: Any) -> str:
        """Create a friendly summary of an operation result."""
        if isinstance(result, PluginResult):
            status = "complete" if result.success else "failed"
            return f"{label} {status}: {result.message}"
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
