"""
VOID GUI

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import threading
import webbrowser
from datetime import datetime
from math import sin, pi
from typing import Any, Dict, List, Optional

from .config import Config
from .core.backup import AutoBackup
from .core.chipsets.base import ChipsetActionResult
from .core.chipsets.dispatcher import (
    detect_chipset_for_device,
    enter_chipset_mode,
    list_chipsets,
    recover_chipset_device,
)
from .core.device import DeviceDetector
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .core.screen import ScreenCapture
from .plugins import PluginContext, PluginMetadata, PluginResult, discover_plugins, get_registry
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

        discover_plugins()
        self.plugin_registry = get_registry()

        self.theme = Config.GUI_THEME
        self.root = tk.Tk()
        self.root.title(Config.APP_NAME)
        self.root.geometry("980x640")
        self.root.configure(bg=self.theme["bg"])
        self.root.withdraw()

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
        self.chipset_detection_var = tk.StringVar(
            value="No chipset detection has been run yet."
        )
        self.chipset_status_var = tk.StringVar(
            value="Select a device to view chipset workflow status."
        )
        self.testpoint_notes_var = tk.StringVar(
            value="No model-specific test-point notes available."
        )
        self.target_mode_var = tk.StringVar(value="edl")
        self.chipset_override_var = tk.StringVar(value="Auto-detect")
        self.progress_var = tk.StringVar(value="")
        self.plugin_metadata: List[PluginMetadata] = []
        self._splash_window: Optional[tk.Toplevel] = None
        self._splash_canvas: Optional[tk.Canvas] = None
        self._splash_step = 0
        self._splash_total_frames = 48
        self._show_splash()

    def _show_splash(self) -> None:
        """Display the animated splash screen before loading the main UI."""
        self._splash_window = tk.Toplevel(self.root)
        self._splash_window.overrideredirect(True)
        self._splash_window.configure(bg=self.theme["bg"])
        width, height = 560, 340
        screen_w = self._splash_window.winfo_screenwidth()
        screen_h = self._splash_window.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self._splash_window.geometry(f"{width}x{height}+{x}+{y}")

        self._splash_canvas = tk.Canvas(
            self._splash_window,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
        )
        self._splash_canvas.pack(fill="both", expand=True)
        self._animate_splash()

    def _animate_splash(self) -> None:
        """Animate the splash screen (dragon flapping -> mask reveal)."""
        if not self._splash_canvas:
            return

        self._splash_canvas.delete("all")
        width = int(self._splash_canvas["width"])
        height = int(self._splash_canvas["height"])
        self._draw_gradient(
            self._splash_canvas,
            width,
            height,
            self.theme["splash_start"],
            self.theme["splash_end"],
            steps=24,
        )

        if self._splash_step < 28:
            wing_phase = sin(self._splash_step / 4 * pi)
            self._draw_dragon_frame(width, height, wing_phase)
            subtitle = "KALI DRAGON ONLINE"
        else:
            progress = (self._splash_step - 28) / (self._splash_total_frames - 28)
            self._draw_mask_frame(width, height, progress)
            subtitle = "ANONYMOUS MASK ENGAGED"

        self._splash_canvas.create_text(
            width / 2,
            height * 0.78,
            text="VOID",
            fill=self.theme["text"],
            font=("Consolas", 28, "bold"),
        )
        self._splash_canvas.create_text(
            width / 2,
            height * 0.86,
            text=subtitle,
            fill=self.theme["accent_soft"],
            font=("Consolas", 11, "bold"),
        )
        self._splash_canvas.create_text(
            width / 2,
            height * 0.92,
            text=Config.THEME_SLOGANS[0],
            fill=self.theme["muted"],
            font=("Consolas", 9),
        )

        self._splash_step += 1
        if self._splash_step <= self._splash_total_frames:
            self._splash_canvas.after(70, self._animate_splash)
        else:
            self._finish_startup()

    def _finish_startup(self) -> None:
        """Tear down splash and build the main interface."""
        if self._splash_window:
            self._splash_window.destroy()
        self._build_layout()
        self.root.deiconify()
        if not ensure_terms_acceptance_gui(messagebox):
            self.root.destroy()
            raise SystemExit(0)
        self.refresh_devices()
        self._load_plugins()

    def _draw_dragon_frame(self, width: int, height: int, wing_phase: float) -> None:
        """Draw a simplified Kali dragon with animated wings."""
        if not self._splash_canvas:
            return
        center_x = width / 2
        center_y = height / 2.7
        wing_span = 140 + wing_phase * 30
        wing_lift = 20 + wing_phase * 14
        body_color = self.theme["dragon"]

        # Wings
        left_wing = [
            center_x - 20,
            center_y,
            center_x - wing_span,
            center_y - wing_lift,
            center_x - wing_span + 40,
            center_y + wing_lift,
        ]
        right_wing = [
            center_x + 20,
            center_y,
            center_x + wing_span,
            center_y - wing_lift,
            center_x + wing_span - 40,
            center_y + wing_lift,
        ]
        self._splash_canvas.create_polygon(
            left_wing,
            fill=body_color,
            outline=self.theme["accent_soft"],
            width=2,
        )
        self._splash_canvas.create_polygon(
            right_wing,
            fill=body_color,
            outline=self.theme["accent_soft"],
            width=2,
        )

        # Body
        self._splash_canvas.create_oval(
            center_x - 40,
            center_y - 30,
            center_x + 40,
            center_y + 40,
            fill=body_color,
            outline=self.theme["accent_soft"],
            width=2,
        )
        self._splash_canvas.create_polygon(
            center_x + 10,
            center_y - 40,
            center_x + 70,
            center_y - 20,
            center_x + 20,
            center_y,
            fill=body_color,
            outline=self.theme["accent_soft"],
            width=2,
        )

    def _draw_mask_frame(self, width: int, height: int, progress: float) -> None:
        """Draw an anonymous mask reveal."""
        if not self._splash_canvas:
            return
        center_x = width / 2
        center_y = height / 2.6
        mask_color = self._blend_hex(self.theme["bg"], self.theme["mask"], progress)
        glow_color = self._blend_hex(self.theme["accent_alt"], self.theme["accent"], progress)

        self._splash_canvas.create_oval(
            center_x - 60,
            center_y - 70,
            center_x + 60,
            center_y + 70,
            fill=mask_color,
            outline=glow_color,
            width=3,
        )
        self._splash_canvas.create_oval(
            center_x - 35,
            center_y - 10,
            center_x - 5,
            center_y + 10,
            fill=self.theme["bg"],
            outline="",
        )
        self._splash_canvas.create_oval(
            center_x + 5,
            center_y - 10,
            center_x + 35,
            center_y + 10,
            fill=self.theme["bg"],
            outline="",
        )
        self._splash_canvas.create_arc(
            center_x - 30,
            center_y + 10,
            center_x + 30,
            center_y + 45,
            start=200,
            extent=140,
            style="arc",
            outline=self._blend_hex(self.theme["accent_soft"], self.theme["mask"], progress),
            width=3,
        )

    def _draw_gradient(
        self,
        canvas: tk.Canvas,
        width: int,
        height: int,
        start_color: str,
        end_color: str,
        steps: int = 20,
    ) -> None:
        """Draw a vertical gradient onto the given canvas."""
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)
        for step in range(steps):
            ratio = step / max(steps - 1, 1)
            color = self._rgb_to_hex(
                (
                    int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio),
                    int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio),
                    int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio),
                )
            )
            y0 = int(height * step / steps)
            y1 = int(height * (step + 1) / steps)
            canvas.create_rectangle(0, y0, width, y1, outline="", fill=color)

    @staticmethod
    def _hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _blend_hex(self, start: str, end: str, ratio: float) -> str:
        ratio = max(0.0, min(1.0, ratio))
        start_rgb = self._hex_to_rgb(start)
        end_rgb = self._hex_to_rgb(end)
        blended = (
            int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio),
            int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio),
            int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio),
        )
        return self._rgb_to_hex(blended)

    def _render_header(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.delete("all")
        self._draw_gradient(
            canvas,
            width,
            height,
            self.theme["gradient_start"],
            self.theme["gradient_end"],
            steps=30,
        )
        title_x = 26
        title_y = 32
        shadow_color = self.theme["shadow"]
        canvas.create_text(
            title_x + 2,
            title_y + 2,
            text="VOID",
            fill=shadow_color,
            anchor="w",
            font=("Consolas", 24, "bold"),
        )
        canvas.create_text(
            title_x,
            title_y,
            text="VOID",
            fill=self.theme["accent"],
            anchor="w",
            font=("Consolas", 24, "bold"),
        )
        canvas.create_text(
            title_x,
            title_y + 30,
            text=Config.THEME_TAGLINE,
            fill=self.theme["text"],
            anchor="w",
            font=("Consolas", 11),
        )
        canvas.create_text(
            width - 24,
            title_y + 8,
            text=Config.THEME_NAME,
            fill=self.theme["accent_soft"],
            anchor="e",
            font=("Consolas", 10, "bold"),
        )

    def _build_layout(self) -> None:
        """Build the themed layout."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Void.TFrame",
            background=self.theme["bg"]
        )
        style.configure(
            "Void.Card.TFrame",
            background=self.theme["panel"],
            relief="raised",
            borderwidth=1,
        )
        style.configure(
            "Void.TLabel",
            background=self.theme["bg"],
            foreground=self.theme["text"],
            font=("Consolas", 11)
        )
        style.configure(
            "Void.Title.TLabel",
            background=self.theme["bg"],
            foreground=self.theme["accent"],
            font=("Consolas", 20, "bold"),
        )
        style.configure(
            "Void.TButton",
            background=self.theme["button_bg"],
            foreground=self.theme["button_text"],
            font=("Consolas", 11, "bold"),
            borderwidth=1,
            relief="raised",
        )
        style.map(
            "Void.TButton",
            background=[("active", self.theme["button_active"])],
            foreground=[("active", self.theme["accent_soft"])],
            relief=[("pressed", "sunken")],
        )

        header = tk.Canvas(
            self.root,
            height=96,
            highlightthickness=0,
            bd=0,
            bg=self.theme["bg"],
        )
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.bind("<Configure>", lambda event: self._render_header(header, event.width, event.height))

        menu = tk.Menu(self.root, bg=self.theme["bg"], fg=self.theme["text"], tearoff=0)
        self.root.config(menu=menu)
        app_menu = tk.Menu(menu, tearoff=0, bg=self.theme["bg"], fg=self.theme["text"])
        app_menu.add_command(label="About", command=self._show_about)
        app_menu.add_command(label="Export Log", command=self._export_log)
        app_menu.add_separator()
        app_menu.add_command(label="Exit", command=self.root.quit)
        menu.add_cascade(label="Void", menu=app_menu)

        body = ttk.Frame(self.root, style="Void.TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        left = ttk.Frame(body, style="Void.Card.TFrame")
        left.pack(side="left", fill="y", padx=(0, 15))
        left.configure(padding=12)

        ttk.Label(left, text="Connected Devices", style="Void.TLabel").pack(anchor="w")
        self.device_list = tk.Listbox(
            left,
            width=36,
            height=18,
            bg=self.theme["panel_alt"],
            fg=self.theme["accent"],
            selectbackground=self.theme["button_active"],
            selectforeground=self.theme["text"],
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
        edl_recovery = ttk.Frame(notebook, style="Void.TFrame")
        help_panel = ttk.Frame(notebook, style="Void.TFrame")
        plugins_panel = ttk.Frame(notebook, style="Void.TFrame")
        notebook.add(dashboard, text="Dashboard")
        notebook.add(edl_recovery, text="EDL & Recovery")
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
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
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

        ttk.Label(edl_recovery, text="Mode Detection", style="Void.TLabel").pack(anchor="w")
        detection_panel = ttk.Frame(edl_recovery, style="Void.TFrame")
        detection_panel.pack(fill="x", pady=(6, 10))

        ttk.Label(
            detection_panel,
            textvariable=self.chipset_detection_var,
            style="Void.TLabel",
            wraplength=600,
        ).pack(anchor="w")

        detect_button = ttk.Button(
            detection_panel,
            text="Detect Chipset Mode",
            style="Void.TButton",
            command=self._detect_chipset,
        )
        detect_button.pack(anchor="w", pady=(6, 0))
        Tooltip(detect_button, "Run chipset detection for the selected device.")

        ttk.Label(edl_recovery, text="Tool Selection", style="Void.TLabel").pack(anchor="w", pady=(10, 0))
        tool_panel = ttk.Frame(edl_recovery, style="Void.TFrame")
        tool_panel.pack(fill="x", pady=(6, 10))

        ttk.Label(tool_panel, text="Chipset Override", style="Void.TLabel").pack(side="left")
        chipset_names = ["Auto-detect"]
        chipset_names.extend(sorted({chipset.name for chipset in list_chipsets()}))
        override_menu = ttk.Combobox(
            tool_panel,
            textvariable=self.chipset_override_var,
            values=chipset_names,
            state="readonly",
            width=18,
        )
        override_menu.pack(side="left", padx=(8, 12))
        Tooltip(override_menu, "Override auto-detection with a manual chipset selection.")

        ttk.Label(tool_panel, text="Target Mode", style="Void.TLabel").pack(side="left")
        mode_menu = ttk.Combobox(
            tool_panel,
            textvariable=self.target_mode_var,
            values=["edl", "preloader", "download", "bootrom"],
            state="readonly",
            width=12,
        )
        mode_menu.pack(side="left", padx=(8, 0))
        Tooltip(mode_menu, "Select the target mode for entry workflows.")

        ttk.Label(edl_recovery, text="Workflows", style="Void.TLabel").pack(anchor="w", pady=(10, 0))
        workflow_panel = ttk.Frame(edl_recovery, style="Void.TFrame")
        workflow_panel.pack(fill="x", pady=(6, 12))

        entry_button = ttk.Button(
            workflow_panel,
            text="Enter Mode",
            style="Void.TButton",
            command=self._enter_chipset_mode,
        )
        entry_button.pack(side="left", padx=(0, 8))
        Tooltip(entry_button, "Attempt to enter the selected chipset mode.")

        flash_button = ttk.Button(
            workflow_panel,
            text="Flash",
            style="Void.TButton",
            command=lambda: self._recover_chipset_device("Flash"),
        )
        flash_button.pack(side="left", padx=(0, 8))
        Tooltip(flash_button, "Check recovery tooling for flashing workflows.")

        dump_button = ttk.Button(
            workflow_panel,
            text="Dump",
            style="Void.TButton",
            command=lambda: self._recover_chipset_device("Dump"),
        )
        dump_button.pack(side="left")
        Tooltip(dump_button, "Check recovery tooling for dump workflows.")

        ttk.Label(edl_recovery, text="Test-Point Guidance", style="Void.TLabel").pack(anchor="w")
        testpoint_panel = ttk.Frame(edl_recovery, style="Void.TFrame")
        testpoint_panel.pack(fill="x", pady=(6, 0))

        warnings = (
            "Safety Warnings\n"
            "• Disconnect power sources before opening the device chassis.\n"
            "• Use ESD protection and insulated tools to avoid short circuits.\n"
            "• Confirm test-point locations with official board-level docs.\n"
            "• Proceed only if you are trained for hardware service."
        )
        ttk.Label(testpoint_panel, text=warnings, style="Void.TLabel", wraplength=600).pack(anchor="w")

        links_panel = ttk.Frame(testpoint_panel, style="Void.TFrame")
        links_panel.pack(anchor="w", pady=(6, 0))
        ttk.Label(links_panel, text="External Docs:", style="Void.TLabel").pack(side="left")

        doc_links = [
            ("Qualcomm EDL", "https://www.qualcomm.com/support"),
            ("MediaTek BootROM", "https://www.mediatek.com/support"),
            ("Samsung Download Mode", "https://www.samsung.com/support"),
        ]
        for label, url in doc_links:
            link_button = ttk.Button(
                links_panel,
                text=label,
                style="Void.TButton",
                command=lambda link=url: webbrowser.open(link),
            )
            link_button.pack(side="left", padx=(8, 0))

        ttk.Label(
            testpoint_panel,
            textvariable=self.testpoint_notes_var,
            style="Void.TLabel",
            wraplength=600,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Label(
            edl_recovery,
            textvariable=self.chipset_status_var,
            style="Void.TLabel",
            wraplength=600,
        ).pack(anchor="w", pady=(10, 0))

        ttk.Label(plugins_panel, text="Registered Plugins", style="Void.TLabel").pack(anchor="w")
        plugin_controls = ttk.Frame(plugins_panel, style="Void.TFrame")
        plugin_controls.pack(fill="both", expand=True, pady=(6, 0))

        self.plugin_list = tk.Listbox(
            plugin_controls,
            width=36,
            height=12,
            bg=self.theme["panel_alt"],
            fg=self.theme["accent"],
            selectbackground=self.theme["button_active"],
            selectforeground=self.theme["text"],
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
            self.chipset_status_var.set("Select a device to view chipset workflow status.")
            self.testpoint_notes_var.set("No model-specific test-point notes available.")
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
        chipset = info.get("chipset", "Unknown")
        chipset_vendor = info.get("chipset_vendor", "Unknown")
        chipset_mode = info.get("chipset_mode", "Unknown")
        chipset_confidence = info.get("chipset_confidence", "Unknown")
        chipset_notes = ", ".join(info.get("chipset_notes", [])) or "None"
        usb_id = info.get("usb_id") or info.get("usb") or "Unknown"
        usb_vid = info.get("usb_vid", "Unknown")
        usb_pid = info.get("usb_pid", "Unknown")
        status = info.get("status", "Unknown")
        reachable = "Yes" if info.get("reachable", False) else "No"
        self.selected_device_var.set(f"{device_id} • {manufacturer} {model}")
        self.details_var.set(
            "Device Overview\n"
            f"• Mode: {mode} | Reachable: {reachable}\n"
            f"• Status: {status}\n"
            f"• Brand: {brand} | Product: {product}\n"
            f"• Android: {android} (SDK {sdk})\n"
            f"• Build: {build_id} ({build_type})\n"
            f"• Hardware: {hardware} | ABI: {cpu_abi}\n"
            f"• Security Patch: {security}\n"
            f"• Chipset: {chipset} ({chipset_vendor}) | Mode: {chipset_mode}\n"
            f"• Chipset Confidence: {chipset_confidence} | Notes: {chipset_notes}\n"
            f"• USB ID: {usb_id} | VID: {usb_vid} PID: {usb_pid}\n"
            f"• Battery Level: {battery.get('level', 'Unknown')}\n"
            f"• Storage Free: {storage.get('available', 'Unknown')}\n"
            f"• Serial: {device_id}"
        )
        self.chipset_status_var.set(
            f"Active chipset: {chipset} ({chipset_vendor}) "
            f"mode={chipset_mode} confidence={chipset_confidence}."
        )

        testpoint_note = (
            info.get("testpoint_notes")
            or info.get("chipset_metadata", {}).get("testpoint_notes")
        )
        if testpoint_note:
            self.testpoint_notes_var.set(f"Model Notes: {testpoint_note}")
        else:
            self.testpoint_notes_var.set("No model-specific test-point notes available.")

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

    def _detect_chipset(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        context = self._get_device_context()
        if context is None:
            return
        detection = detect_chipset_for_device(context)
        if not detection:
            message = "No chipset detected for the selected device."
            self.chipset_detection_var.set(message)
            self.chipset_status_var.set(message)
            self._log(message, level="WARN")
            return
        details = (
            f"Detected {detection.chipset} ({detection.vendor}) "
            f"mode={detection.mode} confidence={detection.confidence:.2f}."
        )
        notes = " ".join(detection.notes) if detection.notes else "No detection notes."
        self.chipset_detection_var.set(f"{details}\n{notes}")
        self.chipset_status_var.set(details)
        self._log(details)

    def _enter_chipset_mode(self) -> None:
        context = self._get_device_context()
        if context is None:
            return
        target_mode = self.target_mode_var.get()
        override = self._get_chipset_override()
        self._run_task(
            "Enter Mode",
            enter_chipset_mode,
            context,
            target_mode,
            override,
        )

    def _recover_chipset_device(self, label: str) -> None:
        context = self._get_device_context()
        if context is None:
            return
        override = self._get_chipset_override()
        self._run_task(
            f"{label} Workflow",
            recover_chipset_device,
            context,
            override,
        )

    def _get_chipset_override(self) -> Optional[str]:
        override = self.chipset_override_var.get().strip()
        if not override or override.lower() == "auto-detect":
            return None
        return override

    def _get_device_context(self) -> Optional[Dict[str, str]]:
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_info):
            messagebox.showwarning("Void", "Select a device first.")
            return None
        info = self.device_info[selection[0]]
        return {k: str(v) for k, v in info.items() if v is not None}

    def run(self) -> None:
        """Start the GUI event loop."""
        self._log("Void GUI ready.")
        self.root.mainloop()

    def _summarize_result(self, label: str, result: Any) -> str:
        """Create a friendly summary of an operation result."""
        if isinstance(result, PluginResult):
            status = "complete" if result.success else "failed"
            return f"{label} {status}: {result.message}"
        if isinstance(result, ChipsetActionResult):
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
