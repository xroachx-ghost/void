"""
VOID GUI

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import csv
import json
import platform
import shutil
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from math import sin, pi
from typing import Any, Callable, Dict, List, Optional

from .config import Config
from .cli import CLI, CommandInfo
from .core.apps import AppManager
from .core.assets import add_firehose_source, collect_required_assets, perform_asset_action
from .core.backup import AutoBackup
from .core.chipsets.base import ChipsetActionResult
from .core.chipsets.dispatcher import (
    detect_chipset_for_device,
    enter_device_mode,
    list_chipsets,
    recover_chipset_device,
)
from .core.data_recovery import DataRecovery
from .core.database import db
from .core.device import DeviceDetector
from .core.display import DisplayAnalyzer
from .core.edl import edl_dump, edl_flash
from .core.files import FileManager
from .core.frp import FRPEngine
from .core.browser import BrowserAutomation
from .core.gemini import GeminiAgent
from .core.logcat import LogcatViewer
from .core.monitor import monitor
from .core.network import NetworkAnalyzer, NetworkTools
from .core.setup_wizard import SetupWizardDiagnostics
from .core.startup import StartupWizardAnalyzer
from .core.performance import PerformanceAnalyzer
from .core.report import ReportGenerator
from .core.screen import ScreenCapture
from .core.system import SystemTweaker
from .core.tools import check_android_tools, check_mediatek_tools, check_qualcomm_tools
from .core.tools.android import android_driver_hints, check_usb_debugging_status
from .core.utils import SafeSubprocess, ToolCheckResult, check_tools
from .core.workflows import RepairWorkflow
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
    
    # Constants
    MAX_SHELL_OUTPUT_LINES = 100
    ADB_TCPIP_WAIT_SECONDS = 2

    def __init__(self):
        if not GUI_AVAILABLE:
            raise RuntimeError("GUI dependencies missing. Install tkinter to use the GUI.")

        discover_plugins()
        self.plugin_registry = get_registry()
        self.cli_bridge = CLI(start_monitor=False)
        self.frp_engine = FRPEngine()
        self.logcat_viewer = LogcatViewer()
        self._logcat_thread: Optional[threading.Thread] = None
        self._logcat_running = False

        self.theme = Config.GUI_THEME
        self.root = tk.Tk()
        self.root.title(Config.APP_NAME)
        self.root.geometry("980x640")
        self.root.configure(bg=self.theme["bg"])
        self.root.withdraw()

        self.device_ids: List[str] = []
        self.device_info: List[Dict[str, Any]] = []
        self.all_device_info: List[Dict[str, Any]] = []
        self.detection_errors: List[Dict[str, Any]] = []
        self.selected_device_id: Optional[str] = None
        self.device_list: Optional[tk.Listbox] = None  # Initialize as None, will be created in advanced view
        self.status_var = tk.StringVar(value="Ready.")
        self.selected_device_var = tk.StringVar(value="No device selected.")
        self.device_section_texts: Dict[str, tk.Text] = {}
        self._device_summary_text = ""
        self.copy_device_id_button: Optional[ttk.Button] = None
        self.copy_device_summary_button: Optional[ttk.Button] = None
        self.device_search_var = tk.StringVar(value="")
        self.action_help_var = tk.StringVar(
            value="Select an action to see a description."
        )
        self.command_search_var = tk.StringVar(value="")
        self.command_line_var = tk.StringVar(value="")
        self.command_args_var = tk.StringVar(value="")
        self.command_detail_var = tk.StringVar(value="Select a command to see details.")
        self.plugin_description_var = tk.StringVar(
            value="Select a plugin to view details."
        )
        self.chipset_detection_var = tk.StringVar(
            value="No chipset detection has been run yet."
        )
        self.chipset_status_var = tk.StringVar(
            value="Select a device to view chipset workflow status."
        )
        self.edl_preflight_var = tk.StringVar(
            value="Run a readiness check before entering recovery workflows."
        )
        self.testpoint_notes_var = tk.StringVar(
            value="No model-specific test-point notes available."
        )
        self.target_mode_var = tk.StringVar(value="edl")
        self.chipset_override_var = tk.StringVar(value="Auto-detect")
        self.progress_var = tk.StringVar(value="")
        self.diagnostics_status_var: Optional[tk.StringVar] = None
        self.diagnostics_links_frame: Optional[ttk.Frame] = None
        self.download_status_var = tk.StringVar(value="")
        self.download_checklist_frame: Optional[ttk.Frame] = None
        self.download_item_vars: Dict[str, tk.BooleanVar] = {}
        self._download_items: List[Dict[str, Any]] = []
        self.edl_links_frame: Optional[ttk.Frame] = None
        self.plugin_metadata: List[PluginMetadata] = []
        self.command_catalog: List[CommandInfo] = list(self.cli_bridge.command_catalog.values())
        self.filtered_command_catalog: List[CommandInfo] = []
        self.command_list: Optional[tk.Listbox] = None
        self.assistant_panel: Optional[ttk.Frame] = None
        self.assistant_chat: Optional[scrolledtext.ScrolledText] = None
        self.assistant_input_var = tk.StringVar(value="")
        self.assistant_status_var = tk.StringVar(value="Gemini assistant idle.")
        self.assistant_task_list: Optional[tk.Listbox] = None
        self.assistant_tasks: List[Dict[str, str]] = []
        self.assistant_history: List[Dict[str, Any]] = []
        self.browser_panel: Optional[ttk.Frame] = None
        self.browser: Optional[BrowserAutomation] = None
        self.browser_url_var = tk.StringVar(value="https://")
        self.browser_x_var = tk.StringVar(value="0")
        self.browser_y_var = tk.StringVar(value="0")
        self.browser_text_var = tk.StringVar(value="")
        self.browser_status_var = tk.StringVar(value="Browser not launched.")
        self.browser_confirm_var = tk.BooleanVar(value=True)
        self.browser_log: Optional[scrolledtext.ScrolledText] = None
        self._app_config: Dict[str, Any] = self._load_app_config()
        self.gemini_api_key = str(self._app_config.get("gemini_api_key", "") or "")
        self.gemini_model_var = tk.StringVar(
            value=str(self._app_config.get("gemini_model", Config.GEMINI_MODEL))
        )
        self.gemini_api_base_var = tk.StringVar(
            value=str(self._app_config.get("gemini_api_base", Config.GEMINI_API_BASE))
        )
        self.gemini_system_instruction = str(
            self._app_config.get("gemini_system_instruction", "") or ""
        )
        self.gemini_extra_payload = str(self._app_config.get("gemini_extra_payload", "") or "")
        self.gemini_generation_config = str(
            self._app_config.get("gemini_generation_config", "") or ""
        )
        self._splash_window: Optional[tk.Toplevel] = None
        self._splash_canvas: Optional[tk.Canvas] = None
        self._splash_step = 0
        self._splash_total_frames = 48
        self._pending_troubleshooting_open = False
        self.output: Optional[scrolledtext.ScrolledText] = None
        self._pending_log_entries: List[str] = []
        self.notebook: Optional[ttk.Notebook] = None
        self.troubleshooting_panel: Optional[ttk.Frame] = None
        self.diagnostics_tab: Optional[ttk.Frame] = None
        self.diagnostics_notebook: Optional[ttk.Notebook] = None
        self.backup_button: Optional[ttk.Button] = None
        self.report_button: Optional[ttk.Button] = None
        self.analyze_button: Optional[ttk.Button] = None
        self.enable_backups_var = tk.BooleanVar(value=Config.ENABLE_AUTO_BACKUP)
        self.enable_reports_var = tk.BooleanVar(value=Config.ENABLE_REPORTS)
        self.enable_analytics_var = tk.BooleanVar(value=Config.ENABLE_ANALYTICS)
        self.exports_dir_var = tk.StringVar(value=str(Config.EXPORTS_DIR))
        self.reports_dir_var = tk.StringVar(value=str(Config.REPORTS_DIR))
        self.apps_filter_var = tk.StringVar(value="all")
        self.apps_package_var = tk.StringVar(value="")
        self.files_list_path_var = tk.StringVar(value="/sdcard")
        self.files_pull_remote_var = tk.StringVar(value="")
        self.files_pull_local_var = tk.StringVar(value="")
        self.files_push_local_var = tk.StringVar(value="")
        self.files_push_remote_var = tk.StringVar(value="")
        self.files_delete_remote_var = tk.StringVar(value="")
        self.tweak_type_var = tk.StringVar(value="dpi")
        self.tweak_value_var = tk.StringVar(value="")
        self.usb_force_var = tk.BooleanVar(value=False)
        self.logcat_filter_var = tk.StringVar(value="")
        self.monitor_status_var = tk.StringVar(value="Monitoring stopped.")
        self.edl_loader_var = tk.StringVar(value="")
        self.edl_image_var = tk.StringVar(value="")
        self.edl_partition_var = tk.StringVar(value="")
        self.recent_items_limit_var = tk.StringVar(value="10")
        self.db_limit_var = tk.StringVar(value="10")
        self.log_export_format_var = tk.StringVar(value="json")
        self.log_export_level_var = tk.StringVar(value="")
        self.log_export_category_var = tk.StringVar(value="")
        self.log_export_device_var = tk.StringVar(value="")
        self.log_export_method_var = tk.StringVar(value="")
        self.log_export_since_var = tk.StringVar(value="")
        self.log_export_until_var = tk.StringVar(value="")
        self.log_export_limit_var = tk.StringVar(value="500")
        
        # Simple/Advanced mode toggle
        self.is_advanced_mode = tk.BooleanVar(value=self._app_config.get("advanced_mode", False))
        self.mode_toggle_button: Optional[ttk.Button] = None
        self.simple_view_container: Optional[ttk.Frame] = None
        self.advanced_view_container: Optional[ttk.Frame] = None
        
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

    def _create_readonly_text(self, parent: tk.Widget, height: int = 4) -> scrolledtext.ScrolledText:
        text_widget = scrolledtext.ScrolledText(
            parent,
            height=height,
            wrap="word",
            font=("Consolas", 10),
            background=self.theme["bg"],
            foreground=self.theme["text"],
            insertbackground=self.theme["text"],
            relief="solid",
            borderwidth=1,
        )
        text_widget.configure(
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["accent_soft"],
        )
        text_widget.bind("<Key>", self._block_text_edit)
        text_widget.bind("<<Paste>>", lambda _event: "break")
        return text_widget

    def _block_text_edit(self, event: tk.Event) -> Optional[str]:
        if event.state & 0x4 and event.keysym.lower() in {"c", "a"}:
            return None
        if event.keysym in {
            "Left",
            "Right",
            "Up",
            "Down",
            "Home",
            "End",
            "Prior",
            "Next",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
        }:
            return None
        if not event.char:
            return None
        return "break"

    def _set_device_section(self, key: str, content: str) -> None:
        widget = self.device_section_texts.get(key)
        if not widget:
            return
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="normal")

    def _clear_device_sections(self) -> None:
        placeholders = {
            "device": "Select a device to view device details.",
            "build": "Select a device to view build details.",
            "connectivity": "Select a device to view connectivity details.",
            "chipset": "Select a device to view chipset details.",
            "categories": "Run a problem category to view targeted diagnostics.",
        }
        for key, text in placeholders.items():
            self._set_device_section(key, text)
        self._device_summary_text = ""
        if self.copy_device_id_button:
            self.copy_device_id_button.configure(state="disabled")
        if self.copy_device_summary_button:
            self.copy_device_summary_button.configure(state="disabled")

    def _copy_device_id(self) -> None:
        if not self.selected_device_id:
            messagebox.showwarning("Void", "Select a device first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.selected_device_id)
        self.status_var.set("Device ID copied to clipboard.")

    def _copy_device_summary(self) -> None:
        if not self._device_summary_text:
            messagebox.showwarning("Void", "Select a device first.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self._device_summary_text)
        self.status_var.set("Device summary copied to clipboard.")

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
        self.root.update_idletasks()
        if not ensure_terms_acceptance_gui(messagebox, parent=self.root):
            self.root.destroy()
            raise SystemExit(0)
        if not self._is_first_run_complete():
            self._show_onboarding()
            return
        self._show_main_window()

    def _show_main_window(self) -> None:
        self.root.deiconify()
        self.refresh_devices()
        self._load_plugins()
        if self._pending_troubleshooting_open:
            self.root.after(0, self._show_troubleshooting_panel)
            self._pending_troubleshooting_open = False

    def _show_troubleshooting_panel(self) -> None:
        if self.notebook and self.diagnostics_tab and self.diagnostics_notebook and self.troubleshooting_panel:
            # First select the Diagnostics main tab
            self.notebook.select(self.diagnostics_tab)
            # Then select the Troubleshooting sub-tab
            self.diagnostics_notebook.select(self.troubleshooting_panel)

    def _diagnostic_icon(self, status: str) -> str:
        return {
            "pass": "✅",
            "fail": "❌",
            "warn": "⚠️",
            "info": "ℹ️",
        }.get(status, "•")

    def _collect_diagnostics_items(self) -> List[Dict[str, Any]]:
        platform_tools_link = {
            "label": "Download Android platform tools",
            "url": "https://developer.android.com/tools/releases/platform-tools",
        }
        tools = check_android_tools()
        items: List[Dict[str, Any]] = []
        for tool in tools:
            label = "ADB" if tool.name == "adb" else tool.name.capitalize()
            status = "pass" if tool.available else "fail"
            detail = tool.version or tool.path or "Detected."
            if not tool.available:
                detail = tool.error.get("message") if tool.error else "Not found in PATH."
            elif tool.error:
                status = "warn"
                detail = tool.error.get("message") or detail
            items.append(
                {
                    "label": f"{label} detected",
                    "status": status,
                    "detail": detail,
                    "links": [platform_tools_link] if not tool.available else [],
                }
            )

        usb_status = check_usb_debugging_status(tools)
        items.append(
            {
                "label": "USB debugging status",
                "status": usb_status.get("status", "warn"),
                "detail": f"{usb_status.get('message') or ''} {usb_status.get('detail') or ''}".strip(),
                "links": usb_status.get("links", []),
            }
        )

        driver_status = android_driver_hints()
        items.append(
            {
                "label": "OS driver guidance",
                "status": driver_status.get("status", "info"),
                "detail": f"{driver_status.get('message') or ''} {driver_status.get('detail') or ''}".strip(),
                "links": driver_status.get("links", []),
            }
        )

        if self.selected_device_id:
            display = DisplayAnalyzer.analyze(self.selected_device_id)
            status = "pass"
            if display.get("surfaceflinger_ok") is False:
                status = "fail"
            elif display.get("black_frame_detected"):
                status = "warn"
            elif not display.get("screen_state"):
                status = "warn"

            detail_parts = [
                f"screen={display.get('screen_state') or 'unknown'}",
                f"power={display.get('display_power') or 'n/a'}",
                f"brightness={display.get('display_brightness') or 'n/a'}",
                f"refresh={display.get('refresh_rate') or 'n/a'}",
                f"black_frame={display.get('black_frame_detected')}",
            ]
            items.append(
                {
                    "label": "Display state / framebuffer",
                    "status": status,
                    "detail": ", ".join(detail_parts),
                    "links": [],
                }
            )
        else:
            items.append(
                {
                    "label": "Display state / framebuffer",
                    "status": "warn",
                    "detail": "Select a device to analyze display diagnostics.",
                    "links": [],
                }
            )
        return items

    def _update_diagnostics(self) -> None:
        items = self._collect_diagnostics_items()
        if self.diagnostics_status_var is not None:
            lines = []
            for item in items:
                icon = self._diagnostic_icon(str(item.get("status", "")))
                detail = item.get("detail") or ""
                lines.append(f"{icon} {item.get('label')}: {detail}".strip())
            self.diagnostics_status_var.set("\n".join(lines))
        if self.diagnostics_links_frame is not None:
            for child in self.diagnostics_links_frame.winfo_children():
                child.destroy()
            for item in items:
                links = item.get("links") or []
                if not links:
                    continue
                ttk.Label(
                    self.diagnostics_links_frame,
                    text=f"{item.get('label')} remediation:",
                    style="Void.TLabel",
                ).pack(anchor="w", pady=(4, 0))
                for link in links:
                    label = link.get("label", "Open link")
                    url = link.get("url")
                    if not url:
                        continue
                    ttk.Button(
                        self.diagnostics_links_frame,
                        text=label,
                        style="Void.TButton",
                        command=lambda target=url: webbrowser.open(target),
                    ).pack(anchor="w", pady=(2, 0))

    def _collect_download_items(self) -> List[Dict[str, Any]]:
        items = collect_required_assets()
        self._download_items = items
        return items

    def _refresh_download_checklist(self) -> None:
        if self.download_checklist_frame is None:
            return
        for child in self.download_checklist_frame.winfo_children():
            child.destroy()
        self.download_item_vars = {}
        items = self._collect_download_items()
        missing_items = 0
        for item in items:
            status = str(item.get("status", "info"))
            icon = self._diagnostic_icon(status)
            label = str(item.get("label", "Item"))
            detail = str(item.get("detail", ""))
            action = str(item.get("action", "manual"))
            selectable = action in {"download", "generate", "import"} and status != "pass"
            if status != "pass":
                missing_items += 1
            var = tk.BooleanVar(value=False)
            self.download_item_vars[str(item.get("key", label))] = var
            check = ttk.Checkbutton(
                self.download_checklist_frame,
                text=f"{icon} {label} — {detail}",
                variable=var,
                style="Void.TCheckbutton",
                state="normal" if selectable else "disabled",
            )
            check.pack(anchor="w", pady=(2, 0))
            links = item.get("links") or []
            if links:
                link_frame = ttk.Frame(self.download_checklist_frame, style="Void.TFrame")
                link_frame.pack(anchor="w", padx=(22, 0), pady=(0, 4))
                for link in links:
                    link_label = link.get("label", "Open link")
                    url = link.get("url")
                    if not url:
                        continue
                    ttk.Button(
                        link_frame,
                        text=link_label,
                        style="Void.TButton",
                        command=lambda target=url: webbrowser.open(target),
                    ).pack(side="left", padx=(0, 8))
        if missing_items:
            self.download_status_var.set(
                f"{missing_items} item(s) missing. Select to download or generate."
            )
        else:
            self.download_status_var.set("All required assets are available.")

    def _apply_download_actions(self) -> None:
        selected = [
            key for key, var in self.download_item_vars.items() if var.get()
        ]
        if not selected:
            self.download_status_var.set("Select at least one missing item to download or generate.")
            return

        self._run_task("Asset downloads", self._run_download_actions, selected)

    def _run_download_actions(self, selections: List[str]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        for key in selections:
            result = perform_asset_action(key)
            results.append(result)
            message = result.get("message", "Action complete.")
            detail = result.get("detail")
            if detail:
                message = f"{message} {detail}"
            self._log(message)

        success = all(result.get("success") for result in results)
        failures = [result for result in results if not result.get("success")]
        if failures:
            summary = failures[0].get("message", "One or more downloads failed.")
        else:
            summary = "Selected assets are ready."
        self.root.after(0, self._refresh_download_checklist)
        self.root.after(0, lambda: self.download_status_var.set(summary))
        return {"success": success, "message": summary}

    def _prompt_firehose_url(self) -> None:
        try:
            from tkinter import simpledialog
        except ImportError:
            messagebox.showwarning("Void", "Tkinter simpledialog is not available.")
            return
        url = simpledialog.askstring(
            "Add Firehose URL",
            "Paste a firehose download URL (http/https):",
            parent=self.root,
        )
        if not url:
            return
        result = add_firehose_source(url)
        if result.get("success"):
            self.download_status_var.set("Firehose URL added. Refreshing checklist.")
            self._refresh_download_checklist()
        else:
            messagebox.showwarning("Void", result.get("message", "Unable to add URL."))

    def _format_tool_checks(self, results: List[ToolCheckResult], label_prefix: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for tool in results:
            status = "pass" if tool.available else "fail"
            detail = tool.version or tool.path or "Detected."
            if not tool.available:
                detail = tool.error.get("message") if tool.error else "Not found in PATH."
            elif tool.error:
                status = "warn"
                detail = tool.error.get("message") or detail
            items.append(
                {
                    "label": f"{label_prefix} {tool.name}".strip(),
                    "status": status,
                    "detail": detail,
                    "links": [],
                }
            )
        return items

    def _collect_edl_preflight_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        context = self._get_device_context(show_warning=False)
        if context is None:
            items.append(
                {
                    "label": "Device selection",
                    "status": "warn",
                    "detail": "Select a device before running recovery workflows.",
                    "links": [],
                }
            )
            return items

        override = self._get_chipset_override()
        detection = detect_chipset_for_device(context)
        chipset_name = override or (detection.chipset if detection else "Unknown")
        mode = context.get("mode", "Unknown")

        items.append(
            {
                "label": "Device mode",
                "status": "pass" if mode.lower() in {"adb", "fastboot", "edl"} else "warn",
                "detail": f"Detected mode: {mode}.",
                "links": [],
            }
        )
        items.append(
            {
                "label": "Chipset detection",
                "status": "pass" if chipset_name != "Unknown" else "warn",
                "detail": f"Chipset: {chipset_name}.",
                "links": [],
            }
        )

        android_tools = check_android_tools()
        items.extend(self._format_tool_checks(android_tools, "Platform tool"))

        usb_status = check_usb_debugging_status(android_tools)
        items.append(
            {
                "label": "USB debugging status",
                "status": usb_status.get("status", "warn"),
                "detail": f"{usb_status.get('message') or ''} {usb_status.get('detail') or ''}".strip(),
                "links": usb_status.get("links", []),
            }
        )

        driver_status = android_driver_hints()
        items.append(
            {
                "label": "OS driver guidance",
                "status": driver_status.get("status", "info"),
                "detail": f"{driver_status.get('message') or ''} {driver_status.get('detail') or ''}".strip(),
                "links": driver_status.get("links", []),
            }
        )

        if chipset_name.lower() == "qualcomm":
            items.extend(self._format_tool_checks(check_qualcomm_tools(), "Qualcomm tool"))
        elif chipset_name.lower() == "mediatek":
            items.extend(self._format_tool_checks(check_mediatek_tools(), "MediaTek tool"))
        elif chipset_name.lower() == "samsung":
            items.append(
                {
                    "label": "Samsung tooling",
                    "status": "info",
                    "detail": "Use OEM download tooling (e.g., Odin) as required.",
                    "links": [],
                }
            )
        else:
            items.append(
                {
                    "label": "Chipset tooling",
                    "status": "info",
                    "detail": "No chipset-specific tooling detected; verify OEM guidance.",
                    "links": [],
                }
            )

        if self.target_mode_var.get().lower() == "edl" and mode.lower() != "adb":
            items.append(
                {
                    "label": "EDL entry prerequisites",
                    "status": "warn",
                    "detail": "EDL entry from GUI requires ADB; otherwise use test-point guidance.",
                    "links": [],
                }
            )
        return items

    def _update_edl_preflight(self) -> None:
        items = self._collect_edl_preflight_items()
        lines = []
        for item in items:
            icon = self._diagnostic_icon(str(item.get("status", "")))
            detail = item.get("detail") or ""
            lines.append(f"{icon} {item.get('label')}: {detail}".strip())
        self.edl_preflight_var.set("\n".join(lines))

        if self.edl_links_frame is not None:
            for child in self.edl_links_frame.winfo_children():
                child.destroy()
            for item in items:
                links = item.get("links") or []
                if not links:
                    continue
                ttk.Label(
                    self.edl_links_frame,
                    text=f"{item.get('label')} remediation:",
                    style="Void.TLabel",
                ).pack(anchor="w", pady=(4, 0))
                for link in links:
                    label = link.get("label", "Open link")
                    url = link.get("url")
                    if not url:
                        continue
                    ttk.Button(
                        self.edl_links_frame,
                        text=label,
                        style="Void.TButton",
                        command=lambda target=url: webbrowser.open(target),
                    ).pack(anchor="w", pady=(2, 0))

    def _config_path(self) -> Path:
        return Config.CONFIG_PATH

    def _load_app_config(self) -> Dict[str, Any]:
        data = Config.read_config()
        if not isinstance(data, dict):
            return {}
        return {key: value for key, value in data.items() if key != "settings"}

    def _save_app_config(self, data: Dict[str, Any]) -> None:
        existing = Config.read_config()
        merged = {**existing, **data}
        Config.write_config(merged)

    def _is_first_run_complete(self) -> bool:
        return bool(self._app_config.get("first_run_complete", False))

    def _mark_first_run_complete(self) -> None:
        self._app_config["first_run_complete"] = True
        self._save_app_config(self._app_config)

    def _collect_onboarding_status(self) -> Dict[str, Any]:
        tools = check_tools(
            [
                ("adb", ["version"]),
                ("fastboot", ["--version"]),
            ]
        )
        devices, _ = DeviceDetector.detect_all()
        return {
            "tools": tools,
            "device_count": len(devices),
        }

    def _format_tool_status(self, status: Dict[str, Any]) -> str:
        lines = []
        for tool in status["tools"]:
            if tool.available:
                detail = tool.version or tool.path or "Detected"
                lines.append(f"✅ {tool.name} detected ({detail})")
            else:
                lines.append(f"⚠️ {tool.name} not found in PATH")
        lines.append(f"🔌 Devices detected: {status['device_count']}")
        return "\n".join(lines)

    def _show_onboarding(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Welcome to Void")
        window.configure(bg=self.theme["bg"])
        window.geometry("620x520")
        window.transient(self.root)
        window.grab_set()
        window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._complete_onboarding(window, open_troubleshooting=False),
        )

        header = ttk.Frame(window, style="Void.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(
            header,
            text="First Run Check",
            style="Void.Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Verify tooling, USB debugging, and device connectivity before proceeding.",
            style="Void.TLabel",
            wraplength=560,
        ).pack(anchor="w", pady=(6, 0))

        status_frame = ttk.Frame(window, style="Void.Card.TFrame")
        status_frame.pack(fill="x", padx=20, pady=(10, 12))
        status_frame.configure(padding=12)
        ttk.Label(status_frame, text="ADB/Fastboot Status", style="Void.TLabel").pack(anchor="w")

        status_text = tk.StringVar(value="")
        status_label = ttk.Label(
            status_frame,
            textvariable=status_text,
            style="Void.TLabel",
            wraplength=560,
        )
        status_label.pack(anchor="w", pady=(6, 0))

        def update_status() -> None:
            status_text.set(self._format_tool_status(self._collect_onboarding_status()))

        update_status()

        reminders = (
            "USB Debugging Reminder\n"
            "• Enable Developer Options and USB Debugging on the device.\n"
            "• Accept the RSA prompt when first connecting to ADB.\n"
            "• Use a data-capable USB cable and a direct USB port.\n\n"
            "Driver & udev Guidance\n"
            "• Windows: install OEM USB drivers or the Google USB driver.\n"
            "• macOS: no drivers required; ensure Android platform tools are installed.\n"
            "• Linux: add udev rules (e.g., /etc/udev/rules.d/51-android.rules) and reload.\n"
        )
        ttk.Label(
            window,
            text=reminders,
            style="Void.TLabel",
            wraplength=560,
            justify="left",
        ).pack(fill="x", padx=20)

        actions = ttk.Frame(window, style="Void.TFrame")
        actions.pack(fill="x", padx=20, pady=(16, 8))

        recheck_button = ttk.Button(
            actions,
            text="Recheck",
            style="Void.TButton",
            command=update_status,
        )
        recheck_button.pack(side="left")

        troubleshooting_button = ttk.Button(
            actions,
            text="Open Troubleshooting",
            style="Void.TButton",
            command=lambda: self._complete_onboarding(window, open_troubleshooting=True),
        )
        troubleshooting_button.pack(side="left", padx=(10, 0))

        skip_button = ttk.Button(
            actions,
            text="Skip",
            style="Void.TButton",
            command=lambda: self._complete_onboarding(window, open_troubleshooting=False),
        )
        skip_button.pack(side="right")

    def _complete_onboarding(self, window: tk.Toplevel, open_troubleshooting: bool) -> None:
        self._mark_first_run_complete()
        self._pending_troubleshooting_open = open_troubleshooting
        window.grab_release()
        window.destroy()
        self._show_main_window()

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
        style.configure(
            "Void.TNotebook",
            background=self.theme["bg"],
            borderwidth=0,
            tabmargins=(1, 4, 1, 0),
        )
        style.configure(
            "Void.TNotebook.Tab",
            background=self.theme["panel_alt"],
            foreground=self.theme["muted"],
            padding=(10, 6),
            font=("Consolas", 10, "bold"),
        )
        style.configure(
            "Void.TCheckbutton",
            background=self.theme["panel"],
            foreground=self.theme["text"],
            font=("Consolas", 10),
        )
        style.map(
            "Void.TNotebook.Tab",
            background=[
                ("selected", self.theme["panel"]),
                ("active", self.theme["button_active"]),
            ],
            foreground=[
                ("selected", self.theme["accent"]),
                ("active", self.theme["accent_soft"]),
            ],
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
        
        # Add mode toggle button in top-right corner
        mode_toggle_container = ttk.Frame(self.root, style="Void.TFrame")
        mode_toggle_container.place(relx=1.0, y=35, anchor="ne", x=-30)
        
        self.mode_toggle_button = ttk.Button(
            mode_toggle_container,
            text="⚙ Advanced",
            style="Void.TButton",
            command=self._toggle_mode,
            width=12
        )
        self.mode_toggle_button.pack()
        Tooltip(self.mode_toggle_button, "Switch between Simple and Advanced modes")

        menu = tk.Menu(self.root, bg=self.theme["bg"], fg=self.theme["text"], tearoff=0)
        self.root.config(menu=menu)
        app_menu = tk.Menu(menu, tearoff=0, bg=self.theme["bg"], fg=self.theme["text"])
        app_menu.add_command(label="About", command=self._show_about)
        app_menu.add_command(label="Export Log", command=self._export_log)
        app_menu.add_separator()
        app_menu.add_command(label="Exit", command=self.root.quit)
        menu.add_cascade(label="Void", menu=app_menu)

        window_menu = tk.Menu(menu, tearoff=0, bg=self.theme["bg"], fg=self.theme["text"])
        window_menu.add_command(label="Gemini Assistant", command=self._open_assistant_panel)
        menu.add_cascade(label="Window", menu=window_menu)

        body = ttk.Frame(self.root, style="Void.TFrame")
        body.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create containers for both simple and advanced views
        self.simple_view_container = ttk.Frame(body, style="Void.TFrame")
        self.advanced_view_container = ttk.Frame(body, style="Void.TFrame")
        
        # Build Simple View
        self._build_simple_view()
        
        # Build Advanced View (original layout)
        self._build_advanced_view()
        
        # Show appropriate view based on saved preference
        self._switch_view()
        
    def _build_simple_view(self) -> None:
        """Build the simplified, user-friendly dashboard view."""
        if not self.simple_view_container:
            return
            
        # Main container with centered layout
        main = ttk.Frame(self.simple_view_container, style="Void.TFrame")
        main.pack(fill="both", expand=True)
        
        # Welcome section
        welcome_frame = ttk.Frame(main, style="Void.TFrame")
        welcome_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            welcome_frame,
            text="Welcome to Void",
            style="Void.Title.TLabel"
        ).pack(anchor="w")
        
        ttk.Label(
            welcome_frame,
            text="Android Device Toolkit - Simple Mode",
            style="Void.TLabel"
        ).pack(anchor="w", pady=(4, 0))
        
        # Device status card
        device_card = ttk.Frame(main, style="Void.Card.TFrame")
        device_card.pack(fill="x", pady=(0, 20))
        device_card.configure(padding=20)
        
        ttk.Label(
            device_card,
            text="📱 Connected Device",
            font=("Consolas", 14, "bold"),
            foreground=self.theme["accent"],
            background=self.theme["panel"]
        ).pack(anchor="w")
        
        ttk.Label(
            device_card,
            textvariable=self.selected_device_var,
            style="Void.TLabel",
            font=("Consolas", 12)
        ).pack(anchor="w", pady=(8, 12))
        
        ttk.Button(
            device_card,
            text="🔄 Refresh Devices",
            style="Void.TButton",
            command=self.refresh_devices,
            width=20
        ).pack(anchor="w")
        
        # Quick Actions grid
        ttk.Label(
            main,
            text="Quick Actions",
            font=("Consolas", 14, "bold"),
            foreground=self.theme["accent"],
            background=self.theme["bg"]
        ).pack(anchor="w", pady=(0, 12))
        
        actions_grid = ttk.Frame(main, style="Void.TFrame")
        actions_grid.pack(fill="x", pady=(0, 20))
        
        # Row 1 - Backup & Reports
        row1 = ttk.Frame(actions_grid, style="Void.TFrame")
        row1.pack(fill="x", pady=(0, 12))
        
        self._create_action_card(
            row1,
            "💾 Backup Device",
            "Create a safe backup of your device data",
            self._backup,
            side="left"
        )
        
        self._create_action_card(
            row1,
            "📊 Generate Report",
            "Create detailed device information report",
            self._report,
            side="left",
            padx=(12, 0)
        )
        
        # Row 2 - Diagnostics
        row2 = ttk.Frame(actions_grid, style="Void.TFrame")
        row2.pack(fill="x", pady=(0, 12))
        
        self._create_action_card(
            row2,
            "🔧 Repair Workflow",
            "Run guided diagnostics and repair",
            self._repair_flow,
            side="left"
        )
        
        self._create_action_card(
            row2,
            "📸 Screenshot",
            "Capture device screen",
            self._screenshot,
            side="left",
            padx=(12, 0)
        )
        
        # Row 3 - File & App Management
        row3 = ttk.Frame(actions_grid, style="Void.TFrame")
        row3.pack(fill="x", pady=(0, 12))
        
        self._create_action_card(
            row3,
            "📁 Browse Files",
            "Access device files and folders",
            lambda: self._switch_to_advanced_tab(1, 1) if self.notebook else None,  # Device Tools > Files
            side="left"
        )
        
        self._create_action_card(
            row3,
            "📱 Manage Apps",
            "View and manage installed apps",
            lambda: self._switch_to_advanced_tab(1, 0) if self.notebook else None,  # Device Tools > Apps
            side="left",
            padx=(12, 0)
        )
        
        # Row 4 - Performance & Logs
        row4 = ttk.Frame(actions_grid, style="Void.TFrame")
        row4.pack(fill="x", pady=(0, 12))
        
        self._create_action_card(
            row4,
            "🔍 Analyze Performance",
            "Check device health and performance",
            self._analyze,
            side="left"
        )
        
        self._create_action_card(
            row4,
            "📋 View Logs",
            "View device logs and diagnostics",
            lambda: self._switch_to_advanced_tab(3, 0) if self.notebook else None,  # Diagnostics > Logcat
            side="left",
            padx=(12, 0)
        )
        
        # Row 5 - Recovery & Network
        row5 = ttk.Frame(actions_grid, style="Void.TFrame")
        row5.pack(fill="x")
        
        self._create_action_card(
            row5,
            "🔄 Data Recovery",
            "Recover contacts and messages",
            lambda: self._switch_to_advanced_tab(2, 0) if self.notebook else None,  # Recovery > Data Recovery
            side="left"
        )
        
        self._create_action_card(
            row5,
            "🌐 Network Tools",
            "Network settings and diagnostics",
            lambda: self._switch_to_advanced_tab(1, 3) if self.notebook else None,  # Device Tools > Network
            side="left",
            padx=(12, 0)
        )
        
        # Help section
        help_card = ttk.Frame(main, style="Void.Card.TFrame")
        help_card.pack(fill="x", pady=(20, 0))
        help_card.configure(padding=16)
        
        ttk.Label(
            help_card,
            text="💡 Quick Tips",
            font=("Consolas", 12, "bold"),
            foreground=self.theme["accent"],
            background=self.theme["panel"]
        ).pack(anchor="w")
        
        tips_text = (
            "• Connect your device and enable USB debugging\n"
            "• Click 'Refresh Devices' to detect your device\n"
            "• Use Quick Actions for common tasks\n"
            "• Switch to Advanced mode for more options"
        )
        
        ttk.Label(
            help_card,
            text=tips_text,
            style="Void.TLabel",
            justify="left"
        ).pack(anchor="w", pady=(8, 0))
        
    def _create_action_card(
        self,
        parent: tk.Widget,
        title: str,
        description: str,
        command: Callable,
        side: str = "left",
        padx: tuple = (0, 0)
    ) -> None:
        """Create a card-style action button."""
        card = ttk.Frame(parent, style="Void.Card.TFrame")
        card.pack(side=side, fill="both", expand=True, padx=padx)
        card.configure(padding=16)
        
        btn = ttk.Button(
            card,
            text=title,
            style="Void.TButton",
            command=command
        )
        btn.pack(fill="x")
        
        ttk.Label(
            card,
            text=description,
            style="Void.TLabel",
            font=("Consolas", 9),
            wraplength=200
        ).pack(anchor="w", pady=(8, 0))
        
        # Add hover effect
        def on_enter(e):
            card.configure(relief="sunken")
        def on_leave(e):
            card.configure(relief="raised")
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
    def _build_advanced_view(self) -> None:
        """Build the advanced view with all tabs and features."""
        if not self.advanced_view_container:
            return
            
        body = self.advanced_view_container

        left = ttk.Frame(body, style="Void.Card.TFrame")
        left.pack(side="left", fill="y", padx=(0, 15))
        left.configure(padding=12)

        ttk.Label(left, text="Connected Devices", style="Void.TLabel").pack(anchor="w")
        ttk.Label(left, text="Search", style="Void.TLabel").pack(anchor="w", pady=(6, 0))
        search_entry = tk.Entry(
            left,
            textvariable=self.device_search_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        search_entry.pack(fill="x", pady=(4, 6))
        Tooltip(search_entry, "Filter devices by ID, manufacturer, model, mode, or status.")
        self.device_search_var.trace_add("write", lambda *_: self._apply_device_filter())
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

        notebook_frame = ttk.Frame(right, style="Void.TFrame")
        notebook_frame.pack(fill="both", expand=True)

        tab_controls = ttk.Frame(notebook_frame, style="Void.TFrame")
        tab_controls.pack(fill="x", pady=(0, 4))
        ttk.Button(
            tab_controls,
            text="◀",
            style="Void.TButton",
            command=lambda: self._scroll_tabs(-1),
        ).pack(side="left")
        ttk.Button(
            tab_controls,
            text="▶",
            style="Void.TButton",
            command=lambda: self._scroll_tabs(1),
        ).pack(side="right")

        self.notebook = ttk.Notebook(notebook_frame, style="Void.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        # Main tabs
        dashboard = ttk.Frame(self.notebook, style="Void.TFrame")
        
        # Device Tools - Combined Apps, Files, System, Network
        device_tools_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        device_tools_notebook = ttk.Notebook(device_tools_tab, style="Void.TNotebook")
        device_tools_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        apps_panel = ttk.Frame(device_tools_notebook, style="Void.TFrame")
        files_panel = ttk.Frame(device_tools_notebook, style="Void.TFrame")
        system_panel = ttk.Frame(device_tools_notebook, style="Void.TFrame")
        network_panel = ttk.Frame(device_tools_notebook, style="Void.TFrame")
        device_tools_notebook.add(apps_panel, text="Apps")
        device_tools_notebook.add(files_panel, text="Files")
        device_tools_notebook.add(system_panel, text="System")
        device_tools_notebook.add(network_panel, text="Network")
        
        # Advanced Recovery - Combined Recovery, EDL, and Data Recovery
        recovery_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        recovery_notebook = ttk.Notebook(recovery_tab, style="Void.TNotebook")
        recovery_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        recovery_panel = ttk.Frame(recovery_notebook, style="Void.TFrame")
        edl_recovery = ttk.Frame(recovery_notebook, style="Void.TFrame")
        edl_tools_panel = ttk.Frame(recovery_notebook, style="Void.TFrame")
        recovery_notebook.add(recovery_panel, text="Data Recovery")
        recovery_notebook.add(edl_recovery, text="EDL Mode")
        recovery_notebook.add(edl_tools_panel, text="Flash/Dump")
        
        # Make EDL recovery panel scrollable
        edl_recovery_scrollable = self._make_scrollable(edl_recovery)
        
        # Diagnostics - Combined Logcat, Monitoring, Troubleshooting
        self.diagnostics_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        self.diagnostics_notebook = ttk.Notebook(self.diagnostics_tab, style="Void.TNotebook")
        self.diagnostics_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        logcat_panel = ttk.Frame(self.diagnostics_notebook, style="Void.TFrame")
        monitor_panel = ttk.Frame(self.diagnostics_notebook, style="Void.TFrame")
        self.troubleshooting_panel = ttk.Frame(self.diagnostics_notebook, style="Void.TFrame")
        self.diagnostics_notebook.add(logcat_panel, text="Logcat")
        self.diagnostics_notebook.add(monitor_panel, text="Monitor")
        self.diagnostics_notebook.add(self.troubleshooting_panel, text="Troubleshoot")
        
        # Make troubleshooting panel scrollable
        self.troubleshooting_scrollable = self._make_scrollable(self.troubleshooting_panel)
        
        # Data Management - Combined exports and database tools
        data_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        data_notebook = ttk.Notebook(data_tab, style="Void.TNotebook")
        data_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        data_exports_panel = ttk.Frame(data_notebook, style="Void.TFrame")
        db_tools_panel = ttk.Frame(data_notebook, style="Void.TFrame")
        data_notebook.add(data_exports_panel, text="Exports")
        data_notebook.add(db_tools_panel, text="Database")
        
        # Automation - Combined Command Center, Plugins, Browser, Assistant
        automation_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        automation_notebook = ttk.Notebook(automation_tab, style="Void.TNotebook")
        automation_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        command_panel = ttk.Frame(automation_notebook, style="Void.TFrame")
        plugins_panel = ttk.Frame(automation_notebook, style="Void.TFrame")
        self.browser_panel = ttk.Frame(automation_notebook, style="Void.TFrame")
        self.assistant_panel = ttk.Frame(automation_notebook, style="Void.TFrame")
        automation_notebook.add(command_panel, text="Commands")
        automation_notebook.add(plugins_panel, text="Plugins")
        automation_notebook.add(self.browser_panel, text="Browser")
        automation_notebook.add(self.assistant_panel, text="AI Assistant")
        
        # Operations Log - Standalone
        logs = ttk.Frame(self.notebook, style="Void.TFrame")
        
        # Settings - Combined Settings and Help
        settings_tab = ttk.Frame(self.notebook, style="Void.TFrame")
        settings_notebook = ttk.Notebook(settings_tab, style="Void.TNotebook")
        settings_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        settings_panel = ttk.Frame(settings_notebook, style="Void.TFrame")
        help_panel = ttk.Frame(settings_notebook, style="Void.TFrame")
        settings_notebook.add(settings_panel, text="Configuration")
        settings_notebook.add(help_panel, text="Help")
        
        # Make help panel scrollable
        help_panel_scrollable = self._make_scrollable(help_panel)
        
        # Add main tabs to notebook (reduced from 20 to 8 tabs)
        self.notebook.add(dashboard, text="📊 Dashboard")
        self.notebook.add(device_tools_tab, text="🔧 Device Tools")
        self.notebook.add(recovery_tab, text="🔄 Recovery")
        self.notebook.add(self.diagnostics_tab, text="🔍 Diagnostics")
        self.notebook.add(data_tab, text="💾 Data")
        self.notebook.add(automation_tab, text="🤖 Automation")
        self.notebook.add(logs, text="📝 Logs")
        self.notebook.add(settings_tab, text="⚙️ Settings")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        self.notebook.bind("<MouseWheel>", self._on_tab_wheel)
        self.notebook.bind("<Button-4>", self._on_tab_wheel)
        self.notebook.bind("<Button-5>", self._on_tab_wheel)
        tab_controls.bind("<MouseWheel>", self._on_tab_wheel)
        tab_controls.bind("<Button-4>", self._on_tab_wheel)
        tab_controls.bind("<Button-5>", self._on_tab_wheel)

        ttk.Label(dashboard, text="Selected Device", style="Void.TLabel").pack(anchor="w")
        ttk.Label(dashboard, textvariable=self.selected_device_var, style="Void.TLabel").pack(
            anchor="w", pady=(2, 8)
        )

        details = ttk.Frame(dashboard, style="Void.TFrame")
        details.pack(fill="x", pady=(0, 10))

        details_header = ttk.Frame(details, style="Void.TFrame")
        details_header.pack(fill="x", pady=(0, 6))
        ttk.Label(details_header, text="Device Summary", style="Void.TLabel").pack(side="left")

        details_actions = ttk.Frame(details_header, style="Void.TFrame")
        details_actions.pack(side="right")
        self.copy_device_id_button = ttk.Button(
            details_actions,
            text="Copy Device ID",
            style="Void.TButton",
            command=self._copy_device_id,
            state="disabled",
        )
        self.copy_device_id_button.pack(side="left", padx=(0, 6))
        Tooltip(self.copy_device_id_button, "Copy the selected device ID to the clipboard.")

        self.copy_device_summary_button = ttk.Button(
            details_actions,
            text="Copy Device Summary",
            style="Void.TButton",
            command=self._copy_device_summary,
            state="disabled",
        )
        self.copy_device_summary_button.pack(side="left")
        Tooltip(self.copy_device_summary_button, "Copy the selected device summary to the clipboard.")

        sections = (
            ("Device", "device", 7),
            ("Build", "build", 4),
            ("Connectivity", "connectivity", 4),
            ("Chipset", "chipset", 4),
            ("Problem Categories", "categories", 4),
        )
        for label, key, height in sections:
            section_frame = ttk.Frame(details, style="Void.TFrame")
            section_frame.pack(fill="x", pady=(0, 6))
            ttk.Label(section_frame, text=label, style="Void.TLabel").pack(anchor="w")
            text_widget = self._create_readonly_text(section_frame, height=height)
            text_widget.pack(fill="x", pady=(2, 0))
            self.device_section_texts[key] = text_widget

        self._clear_device_sections()

        ttk.Label(dashboard, text="Actions", style="Void.TLabel").pack(anchor="w", pady=(6, 0))
        actions = ttk.Frame(dashboard, style="Void.TFrame")
        actions.pack(fill="x", pady=6)

        self.backup_button = ttk.Button(
            actions,
            text="Create Backup",
            style="Void.TButton",
            command=self._backup
        )
        self.backup_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(self.backup_button, "Creates a local backup snapshot of device data.")
        self.backup_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Create Backup: captures a local snapshot of device data using ADB."
            ),
        )

        self.analyze_button = ttk.Button(
            actions,
            text="Analyze",
            style="Void.TButton",
            command=self._analyze
        )
        self.analyze_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(self.analyze_button, "Collects performance metrics and device diagnostics.")
        self.analyze_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Analyze: gathers performance and system diagnostics from the device."
            ),
        )

        self.report_button = ttk.Button(
            actions,
            text="Generate Report",
            style="Void.TButton",
            command=self._report
        )
        self.report_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(self.report_button, "Builds an HTML device report with collected metadata.")
        self.report_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Generate Report: creates an HTML report with device information."
            ),
        )

        self.repair_flow_button = ttk.Button(
            actions,
            text="Repair Workflow",
            style="Void.TButton",
            command=self._repair_flow,
        )
        self.repair_flow_button.pack(
            side="left", padx=(0, 8)
        )
        Tooltip(self.repair_flow_button, "Run the guided repair workflow with remediation prompts.")
        self.repair_flow_button.bind(
            "<Enter>",
            lambda _event: self.action_help_var.set(
                "Repair Workflow: run diagnostics, clear blockers, and re-check device health."
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
            text="Problem Categories",
            style="Void.TLabel",
        ).pack(anchor="w", pady=(12, 0))
        category_card = ttk.Frame(dashboard, style="Void.Card.TFrame")
        category_card.pack(fill="x", pady=(6, 0))
        category_card.configure(padding=12)
        ttk.Label(
            category_card,
            text="Run focused diagnostics for common problem areas.",
            style="Void.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w")
        category_buttons = ttk.Frame(category_card, style="Void.TFrame")
        category_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(
            category_buttons,
            text="Startup Wizard",
            style="Void.TButton",
            command=lambda: self._run_problem_category("startup_wizard"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            category_buttons,
            text="Network",
            style="Void.TButton",
            command=lambda: self._run_problem_category("network"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            category_buttons,
            text="Display",
            style="Void.TButton",
            command=lambda: self._run_problem_category("display"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            category_buttons,
            text="Backup",
            style="Void.TButton",
            command=lambda: self._run_problem_category("backup"),
        ).pack(side="left")

        ttk.Label(
            dashboard,
            text="Action Descriptions",
            style="Void.TLabel"
        ).pack(anchor="w", pady=(10, 0))
        action_descriptions = (
            "Create Backup — Save a local snapshot of apps and data.\n"
            "Analyze — Collect performance and diagnostic stats.\n"
            "Generate Report — Build an HTML report with device metadata.\n"
            "Repair Workflow — Run diagnostics and guided remediation steps.\n"
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

        ttk.Label(dashboard, text="Repair Workflow", style="Void.TLabel").pack(anchor="w", pady=(12, 0))
        workflow_card = ttk.Frame(dashboard, style="Void.Card.TFrame")
        workflow_card.pack(fill="x", pady=(6, 0))
        workflow_card.configure(padding=12)
        ttk.Label(
            workflow_card,
            text="01 • Initialize",
            style="Void.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            workflow_card,
            text="Launch Void and select your target device or profile to analyze.",
            style="Void.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            workflow_card,
            text="02 • Scan",
            style="Void.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            workflow_card,
            text="Void identifies residual barriers and locks preventing access.",
            style="Void.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            workflow_card,
            text="03 • Clear",
            style="Void.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            workflow_card,
            text="Remove identified obstacles cleanly and efficiently.",
            style="Void.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            workflow_card,
            text="04 • Restore",
            style="Void.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            workflow_card,
            text="Device returns to a fresh, fully accessible state.",
            style="Void.TLabel",
            wraplength=520,
            justify="left",
        ).pack(anchor="w")

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
        if self._pending_log_entries:
            self.output.configure(state="normal")
            for entry in self._pending_log_entries:
                self.output.insert("end", entry)
            self.output.configure(state="disabled")
            self.output.see("end")
            self._pending_log_entries.clear()

        self._build_apps_panel(apps_panel)
        self._build_files_panel(files_panel)
        self._build_recovery_panel(recovery_panel)
        self._build_system_panel(system_panel)
        self._build_network_panel(network_panel)
        self._build_logcat_panel(logcat_panel)
        self._build_monitor_panel(monitor_panel)
        self._build_edl_tools_panel(edl_tools_panel)
        self._build_data_exports_panel(data_exports_panel)
        self._build_db_tools_panel(db_tools_panel)
        self._build_command_panel(command_panel)
        if self.browser_panel is not None:
            self._build_browser_panel(self.browser_panel)

        ttk.Label(help_panel_scrollable, text="Action Details", style="Void.TLabel").pack(anchor="w")
        ttk.Label(
            help_panel_scrollable,
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
        ttk.Label(help_panel_scrollable, text=guide, style="Void.TLabel", wraplength=600).pack(anchor="w")

        ttk.Label(
            self.troubleshooting_scrollable,
            text="Troubleshooting",
            style="Void.TLabel",
        ).pack(anchor="w")
        diagnostics_card = ttk.Frame(self.troubleshooting_scrollable, style="Void.Card.TFrame")
        diagnostics_card.pack(fill="x", pady=(6, 12))
        diagnostics_card.configure(padding=12)
        ttk.Label(
            diagnostics_card,
            text="Diagnostics Checklist",
            style="Void.TLabel",
        ).pack(anchor="w")
        self.diagnostics_status_var = tk.StringVar(value="")
        ttk.Label(
            diagnostics_card,
            textvariable=self.diagnostics_status_var,
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))
        self.diagnostics_links_frame = ttk.Frame(diagnostics_card, style="Void.TFrame")
        self.diagnostics_links_frame.pack(fill="x", pady=(8, 0))
        display_diagnostics_frame = ttk.Frame(diagnostics_card, style="Void.TFrame")
        display_diagnostics_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(
            display_diagnostics_frame,
            text="Run Display Diagnostics",
            style="Void.TButton",
            command=self._run_display_diagnostics,
        ).pack(anchor="w")
        ttk.Label(
            display_diagnostics_frame,
            text=(
                "Screenshot looks normal → display hardware likely at fault.\n"
                "Screenshot black → system rendering or power state issue."
            ),
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Button(
            diagnostics_card,
            text="Recheck Diagnostics",
            style="Void.TButton",
            command=self._update_diagnostics,
        ).pack(anchor="w", pady=(8, 0))

        # Device health diagnostics
        health_card = ttk.Frame(self.troubleshooting_scrollable, style="Void.Card.TFrame")
        health_card.pack(fill="x", pady=(0, 12))
        health_card.configure(padding=12)
        ttk.Label(health_card, text="Device Health Checks", style="Void.TLabel").pack(anchor="w")
        health_row = ttk.Frame(health_card, style="Void.TFrame")
        health_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            health_row,
            text="Battery Health",
            style="Void.TButton",
            command=self._check_battery_health,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            health_row,
            text="Storage Health",
            style="Void.TButton",
            command=self._check_storage_health,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            health_row,
            text="Temperature",
            style="Void.TButton",
            command=self._check_temperature,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            health_row,
            text="Full Diagnostics",
            style="Void.TButton",
            command=self._run_full_diagnostics,
        ).pack(side="left")


        downloads_card = ttk.Frame(self.troubleshooting_scrollable, style="Void.Card.TFrame")
        downloads_card.pack(fill="x", pady=(0, 12))
        downloads_card.configure(padding=12)
        ttk.Label(
            downloads_card,
            text="Required Files & Downloads",
            style="Void.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            downloads_card,
            text=(
                "Select missing assets to download or import. Firehose programmers must come from OEM sources."
            ),
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 6))
        self.download_checklist_frame = ttk.Frame(downloads_card, style="Void.TFrame")
        self.download_checklist_frame.pack(fill="x")
        ttk.Label(
            downloads_card,
            textvariable=self.download_status_var,
            style="Void.TLabel",
            wraplength=600,
        ).pack(anchor="w", pady=(6, 0))
        downloads_actions = ttk.Frame(downloads_card, style="Void.TFrame")
        downloads_actions.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            downloads_actions,
            text="Download/Import Selected",
            style="Void.TButton",
            command=self._apply_download_actions,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            downloads_actions,
            text="Refresh Checklist",
            style="Void.TButton",
            command=self._refresh_download_checklist,
        ).pack(side="left")
        ttk.Button(
            downloads_actions,
            text="Add Firehose URL",
            style="Void.TButton",
            command=self._prompt_firehose_url,
        ).pack(side="left", padx=(8, 0))

        self._build_settings_panel(settings_panel)
        if self.assistant_panel is not None:
            self._build_assistant_panel(self.assistant_panel)
        self._sync_action_buttons()

        self._update_diagnostics()
        self._refresh_download_checklist()
        troubleshoot_text = (
            "If no devices are detected:\n"
            "• Confirm adb/fastboot are installed and on PATH.\n"
            "• Enable Developer Options and USB Debugging on the device.\n"
            "• Accept the RSA prompt after connecting to the host.\n"
            "• Use a data-capable USB cable and a direct USB port.\n\n"
            "Platform notes:\n"
            "• Windows: install OEM or Google USB drivers and reboot after install.\n"
            "• macOS: install Android platform tools (Homebrew: brew install android-platform-tools).\n"
            "• Linux: add udev rules (e.g., /etc/udev/rules.d/51-android.rules) and reload.\n\n"
            "Black screen:\n"
            "• Check the power state and try waking the device.\n"
            "• Force reboot if the panel stays dark.\n"
            "• Verify brightness isn't set to minimum.\n"
            "• Confirm adb responds (adb devices, logcat).\n"
            "• Run Display Diagnostics to compare the screenshot with the panel.\n\n"
            "Still stuck? Visit the Android developer documentation for platform tooling."
        )
        ttk.Label(
            self.troubleshooting_scrollable,
            text=troubleshoot_text,
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(6, 12))
        ttk.Button(
            self.troubleshooting_scrollable,
            text="Open Android Platform Tools Docs",
            style="Void.TButton",
            command=lambda: webbrowser.open(
                "https://developer.android.com/tools/releases/platform-tools"
            ),
        ).pack(anchor="w")

        ttk.Label(edl_recovery_scrollable, text="Mode Detection", style="Void.TLabel").pack(anchor="w")
        detection_panel = ttk.Frame(edl_recovery_scrollable, style="Void.TFrame")
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

        ttk.Label(edl_recovery_scrollable, text="Readiness Check", style="Void.TLabel").pack(anchor="w")
        readiness_panel = ttk.Frame(edl_recovery_scrollable, style="Void.TFrame")
        readiness_panel.pack(fill="x", pady=(6, 10))

        ttk.Label(
            readiness_panel,
            textvariable=self.edl_preflight_var,
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w")

        self.edl_links_frame = ttk.Frame(readiness_panel, style="Void.TFrame")
        self.edl_links_frame.pack(fill="x", pady=(6, 0))

        ttk.Button(
            readiness_panel,
            text="Run Readiness Check",
            style="Void.TButton",
            command=self._update_edl_preflight,
        ).pack(anchor="w", pady=(6, 0))

        ttk.Label(edl_recovery_scrollable, text="Tool Selection", style="Void.TLabel").pack(anchor="w", pady=(10, 0))
        tool_panel = ttk.Frame(edl_recovery_scrollable, style="Void.TFrame")
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
            values=["edl", "preloader", "download", "bootrom", "fastboot", "bootloader", "recovery"],
            state="readonly",
            width=12,
        )
        mode_menu.pack(side="left", padx=(8, 0))
        Tooltip(mode_menu, "Select the target mode for entry workflows.")

        ttk.Label(edl_recovery_scrollable, text="Workflows", style="Void.TLabel").pack(anchor="w", pady=(10, 0))
        workflow_panel = ttk.Frame(edl_recovery_scrollable, style="Void.TFrame")
        workflow_panel.pack(fill="x", pady=(6, 12))

        entry_button = ttk.Button(
            workflow_panel,
            text="Enter Mode",
            style="Void.TButton",
            command=self._enter_chipset_mode,
        )
        entry_button.pack(side="left", padx=(0, 8))
        Tooltip(entry_button, "Guided mode entry with authorization checks and manual steps.")

        flash_button = ttk.Button(
            workflow_panel,
            text="Flash Readiness",
            style="Void.TButton",
            command=lambda: self._recover_chipset_device("Flash readiness"),
        )
        flash_button.pack(side="left", padx=(0, 8))
        Tooltip(flash_button, "Validate flashing tool availability for the selected chipset.")

        dump_button = ttk.Button(
            workflow_panel,
            text="Dump Readiness",
            style="Void.TButton",
            command=lambda: self._recover_chipset_device("Dump readiness"),
        )
        dump_button.pack(side="left")
        Tooltip(dump_button, "Validate dump tool availability for the selected chipset.")

        ttk.Label(edl_recovery_scrollable, text="Test-Point Guidance", style="Void.TLabel").pack(anchor="w")
        testpoint_panel = ttk.Frame(edl_recovery_scrollable, style="Void.TFrame")
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
            edl_recovery_scrollable,
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
        self._update_edl_preflight()

    def _log(self, message: str, level: str = "INFO") -> None:
        """Write a log line to the GUI console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}\n"

        if not self.output:
            self._pending_log_entries.append(entry)
            return

        def append():
            if not self.output:
                self._pending_log_entries.append(entry)
                return
            self.output.configure(state="normal")
            self.output.insert("end", entry)
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

    def _refresh_command_list(self) -> None:
        """Refresh the command list based on the search query."""
        if self.command_list is None:
            return
        query = self.command_search_var.get().strip().lower()
        self.command_list.delete(0, "end")
        if not query:
            filtered = self.command_catalog
        else:
            filtered = [
                command
                for command in self.command_catalog
                if query in command.name.lower()
                or query in command.summary.lower()
                or query in command.usage.lower()
                or query in command.category.lower()
                or any(query in alias.lower() for alias in command.aliases)
            ]
        self.filtered_command_catalog = filtered
        for command in filtered:
            self.command_list.insert("end", f"{command.name} ({command.category})")
        if not filtered:
            self.command_detail_var.set("No commands match the current search.")
        elif not self.command_list.curselection():
            self.command_detail_var.set("Select a command to see details.")

    def _on_command_select(self) -> None:
        if self.command_list is None:
            return
        selection = self.command_list.curselection()
        if not selection or selection[0] >= len(self.filtered_command_catalog):
            return
        command = self.filtered_command_catalog[selection[0]]
        aliases = ", ".join(command.aliases) if command.aliases else "None"
        examples = "\n".join(f"• {example}" for example in command.examples) if command.examples else "None"
        details = (
            f"{command.name}\n"
            f"Category: {command.category}\n"
            f"Summary: {command.summary}\n"
            f"Usage: {command.usage}\n"
            f"Aliases: {aliases}\n"
            f"Examples:\n{examples}"
        )
        self.command_detail_var.set(details)

    def _insert_selected_command(self) -> None:
        if self.command_list is None:
            return
        selection = self.command_list.curselection()
        if not selection or selection[0] >= len(self.filtered_command_catalog):
            messagebox.showwarning("Void", "Select a command first.")
            return
        command = self.filtered_command_catalog[selection[0]]
        args = self.command_args_var.get().strip()
        command_line = f"{command.name} {args}".strip()
        self.command_line_var.set(command_line)

    def _run_command_line(self) -> None:
        command_line = self.command_line_var.get().strip()
        if not command_line:
            if self.command_list is not None:
                selection = self.command_list.curselection()
                if selection and selection[0] < len(self.filtered_command_catalog):
                    command = self.filtered_command_catalog[selection[0]]
                    args = self.command_args_var.get().strip()
                    command_line = f"{command.name} {args}".strip()
                    self.command_line_var.set(command_line)
        if not command_line:
            messagebox.showwarning("Void", "Enter a command line to run.")
            return

        def runner() -> Dict[str, Any]:
            result = self.cli_bridge.execute_command_line(command_line)
            output = result.get("output") if isinstance(result, dict) else None
            if output:
                for line in output.splitlines():
                    self._log(line, level="DATA")
            return result

        self._run_task(f"Command: {command_line}", runner)

    def _execute_shell_command(self) -> None:
        from .core.shell import ShellController
        
        device_id = self._get_selected_device()
        if not device_id:
            return
        
        command = self.shell_command_var.get().strip()
        if not command:
            messagebox.showwarning("Void", "Enter a shell command to execute.")
            return

        def runner() -> Dict[str, Any]:
            result = ShellController.execute_command(device_id, command)
            if result.get('output'):
                lines = result['output'].strip().split('\n')
                for line in lines[:self.MAX_SHELL_OUTPUT_LINES]:
                    self._log(line, level="DATA")
                if len(lines) > self.MAX_SHELL_OUTPUT_LINES:
                    self._log(f"... and {len(lines) - self.MAX_SHELL_OUTPUT_LINES} more lines", level="DATA")
            if result.get('error'):
                self._log(f"Error: {result['error']}", level="ERROR")
            return result

        self._run_task(f"Shell: {command}", runner)

    def _run_task(
        self,
        label: str,
        func,
        *args,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Run a potentially slow task in a background thread."""
        def emit_progress(message: str) -> None:
            if message:
                self.root.after(0, lambda: self.progress_var.set(message))
            if progress_callback:
                progress_callback(message)

        def runner():
            try:
                self._log(f"{label} started...")
                self._start_progress()
                if progress_callback:
                    result = func(*args, progress_callback=emit_progress)
                else:
                    result = func(*args)
                summary = self._summarize_result(label, result)
                self._log(summary)
                self.root.after(0, lambda: self.status_var.set(summary))
                if self._is_failed_result(result):
                    self._show_task_error(label, result=result)
            except Exception as exc:
                self._log(f"{label} failed: {exc}", level="ERROR")
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        f"{label} failed. See log for details."
                    ),
                )
                self._show_task_error(label, exc=exc)
            finally:
                self._stop_progress()

        threading.Thread(target=runner, daemon=True).start()

    def _get_selected_device(self) -> Optional[str]:
        """Return the currently selected device."""
        # In simple mode, use the stored selected_device_id
        if not self.device_list:
            if not self.selected_device_id:
                messagebox.showwarning("Void", "Select a device first.")
                return None
            return self.selected_device_id
            
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_ids):
            messagebox.showwarning("Void", "Select a device first.")
            return None
        return self.device_ids[selection[0]]

    def _on_device_select(self) -> None:
        """Update dashboard detail view when a device is selected."""
        if not self.device_list:
            return
            
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_info):
            self.selected_device_id = None
            self.selected_device_var.set("No device selected.")
            self._clear_device_sections()
            self.chipset_status_var.set("Select a device to view chipset workflow status.")
            self.testpoint_notes_var.set("No model-specific test-point notes available.")
            self.edl_preflight_var.set(
                "Run a readiness check before entering recovery workflows."
            )
            if self.edl_links_frame is not None:
                for child in self.edl_links_frame.winfo_children():
                    child.destroy()
            return

        info = self.device_info[selection[0]]
        device_id = info.get("id", "unknown")
        self.selected_device_id = device_id
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
        modes = info.get("modes") or [mode]
        mode_label = ", ".join(modes) if isinstance(modes, list) else str(modes)
        chipset = info.get("chipset", "Unknown")
        chipset_vendor = info.get("chipset_vendor", "Unknown")
        chipset_mode = info.get("chipset_mode", "Unknown")
        chipset_confidence = info.get("chipset_confidence", "Unknown")
        chipset_notes = ", ".join(info.get("chipset_notes", [])) or "None"
        usb_id = info.get("usb_id") or info.get("usb") or "Unknown"
        usb_vid = info.get("usb_vid", "Unknown")
        usb_pid = info.get("usb_pid", "Unknown")
        status = info.get("status", "Unknown")
        statuses = info.get("statuses") or [status]
        status_label = ", ".join(statuses) if isinstance(statuses, list) else str(statuses)
        reachable = "Yes" if info.get("reachable", False) else "No"
        self.selected_device_var.set(f"{device_id} • {manufacturer} {model}")
        device_section = "\n".join([
            f"ID: {device_id}",
            f"Manufacturer: {manufacturer}",
            f"Model: {model}",
            f"Brand: {brand}",
            f"Product: {product}",
            f"Hardware: {hardware}",
            f"ABI: {cpu_abi}",
            f"Battery Level: {battery.get('level', 'Unknown')}",
            f"Storage Free: {storage.get('available', 'Unknown')}",
        ])
        build_section = "\n".join([
            f"Android: {android} (SDK {sdk})",
            f"Build ID: {build_id}",
            f"Build Type: {build_type}",
            f"Security Patch: {security}",
        ])
        connectivity_section = "\n".join([
            f"Mode: {mode} (Reachable: {reachable})",
            f"Modes: {mode_label}",
            f"Status: {status} (Statuses: {status_label})",
            f"USB: {usb_id} (VID: {usb_vid} PID: {usb_pid})",
        ])
        chipset_section = "\n".join([
            f"Chipset: {chipset} ({chipset_vendor})",
            f"Mode: {chipset_mode}",
            f"Confidence: {chipset_confidence}",
            f"Notes: {chipset_notes}",
        ])
        self._set_device_section("device", device_section)
        self._set_device_section("build", build_section)
        self._set_device_section("connectivity", connectivity_section)
        self._set_device_section("chipset", chipset_section)
        self._device_summary_text = (
            "Device\n"
            f"{device_section}\n\n"
            "Build\n"
            f"{build_section}\n\n"
            "Connectivity\n"
            f"{connectivity_section}\n\n"
            "Chipset\n"
            f"{chipset_section}"
        )
        if self.copy_device_id_button:
            self.copy_device_id_button.configure(state="normal")
        if self.copy_device_summary_button:
            self.copy_device_summary_button.configure(state="normal")
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
        self._update_edl_preflight()

    def refresh_devices(self) -> None:
        """Refresh the device list."""
        devices, errors = DeviceDetector.detect_all()
        self.all_device_info = devices
        self.detection_errors = errors
        self._apply_device_filter(log_refresh=True)
        if errors:
            summary = self._summarize_detection_errors(errors)
            base_status = self.status_var.get().strip()
            status = f"{base_status} {summary}".strip() if base_status else summary
            self.status_var.set(status)
            for error in errors:
                self._log(
                    f"Device detection error: {json.dumps(error, indent=2, sort_keys=True)}",
                    level="ERROR",
                )

    def _summarize_detection_errors(self, errors: List[Dict[str, Any]]) -> str:
        sources = sorted(
            {
                str(error.get("source", "")).upper()
                for error in errors
                if error.get("source")
            }
        )
        if sources:
            sources_label = ", ".join(sources)
            return (
                f"Diagnostics: {sources_label} detection issue(s). "
                "Open Troubleshooting → Diagnostics for help."
            )
        return "Diagnostics: Device detection issues detected. See Troubleshooting."

    def _apply_device_filter(self, log_refresh: bool = False) -> None:
        """Filter the device list based on the search query."""
        if not self.device_list:
            # Device list not created yet (simple mode), just update device_info
            self.device_ids = []
            self.device_info = []
            if self.all_device_info:
                for device in self.all_device_info:
                    self.device_ids.append(device.get("id", "unknown"))
                    self.device_info.append(device)
            return
            
        query = self.device_search_var.get().strip().lower()
        self.device_list.delete(0, tk.END)
        self.device_ids = []
        self.device_info = []

        if not self.all_device_info:
            self.device_list.insert(tk.END, "No devices detected")
            if log_refresh:
                self._log("No devices detected", level="WARN")
            self.selected_device_var.set("No device selected.")
            self._clear_device_sections()
            self.status_var.set("No devices detected.")
            self.selected_device_id = None
            return

        filtered = [
            device for device in self.all_device_info
            if self._matches_device_filter(device, query)
        ]

        if not filtered:
            self.device_list.insert(tk.END, "No devices match this filter")
            self.status_var.set("0 devices shown.")
            return

        for device in filtered:
            device_id = device.get("id", "unknown")
            label, color = self._format_device_label(device)
            index = self.device_list.size()
            self.device_list.insert(tk.END, label)
            self.device_list.itemconfig(index, fg=color)
            self.device_ids.append(device_id)
            self.device_info.append(device)

        total = len(self.all_device_info)
        shown = len(self.device_ids)
        if shown == total:
            self.status_var.set(f"{shown} device(s) ready.")
        else:
            self.status_var.set(f"{shown} device(s) shown (of {total}).")

        if self.selected_device_id and self.selected_device_id in self.device_ids:
            selected_index = self.device_ids.index(self.selected_device_id)
            self.device_list.selection_set(selected_index)
            self.device_list.activate(selected_index)
            self.device_list.see(selected_index)

        if log_refresh:
            self._log(f"Detected {len(self.all_device_info)} device(s).")

    def _matches_device_filter(self, device: Dict[str, Any], query: str) -> bool:
        """Return True if the device matches the current filter query."""
        if not query:
            return True
        modes = device.get("modes") or [device.get("mode", "")]
        statuses = device.get("statuses") or [device.get("status", "")]
        searchable = " ".join(
            str(value)
            for value in [
                device.get("id", ""),
                device.get("manufacturer", ""),
                device.get("model", ""),
                device.get("mode", ""),
                " ".join(mode for mode in modes if mode),
                " ".join(status for status in statuses if status),
            ]
            if value
        ).lower()
        return query in searchable

    def _format_device_label(self, device: Dict[str, Any]) -> tuple[str, str]:
        """Return list label and status color for a device."""
        device_id = device.get("id", "unknown")
        manufacturer = device.get("manufacturer", "Unknown")
        model = device.get("model", "Unknown")
        modes = device.get("modes") or [device.get("mode", "Unknown")]
        mode_label = ", ".join(m.title() for m in modes if m)
        status_label, status_color = self._device_status_badge(device)
        label = (
            f"{device_id} • {manufacturer} {model} • "
            f"{mode_label} [{status_label}]"
        ).strip()
        return label, status_color

    def _device_status_badge(self, device: Dict[str, Any]) -> tuple[str, str]:
        """Return status badge text and color for a device."""
        modes = [mode.lower() for mode in (device.get("modes") or []) if mode]
        mode = (device.get("mode") or "").lower()
        status = (device.get("status") or "").lower()
        statuses = [s.lower() for s in (device.get("statuses") or []) if s]
        status_set = set(statuses + ([status] if status else []))

        if "unauthorized" in status_set:
            return "Unauthorized", "#f59e0b"
        if "offline" in status_set:
            return "Offline", "#ef4444"
        if "fastboot" in modes or mode == "fastboot":
            return "Fastboot", self.theme["accent_alt"]
        if mode and mode not in {"adb", "fastboot"}:
            return mode.upper(), "#60a5fa"
        if "device" in status_set or device.get("reachable"):
            return "Online", "#22c55e"
        if "detected" in status_set:
            return "Detected", "#38bdf8"
        return "Unknown", self.theme["muted"]

    def _backup(self) -> None:
        if not Config.ENABLE_AUTO_BACKUP:
            messagebox.showwarning("Backups Disabled", "Enable backups in Settings to use this feature.")
            self.status_var.set("Backup disabled in settings.")
            return
        device_id = self._get_selected_device()
        if device_id:
            self._run_task(
                "Backup",
                AutoBackup.create_backup,
                device_id,
                progress_callback=self._log,
            )

    def _analyze(self) -> None:
        if not Config.ENABLE_ANALYTICS:
            messagebox.showwarning("Analytics Disabled", "Enable analytics in Settings to use Analyze.")
            self.status_var.set("Analyze disabled in settings.")
            return
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Analyze", PerformanceAnalyzer.analyze, device_id)

    def _report(self) -> None:
        if not Config.ENABLE_REPORTS:
            messagebox.showwarning("Reports Disabled", "Enable reports in Settings to generate reports.")
            self.status_var.set("Reports disabled in settings.")
            return
        device_id = self._get_selected_device()
        if device_id:
            self._run_task(
                "Report",
                ReportGenerator.generate_device_report,
                device_id,
                progress_callback=self._log,
            )

    def _repair_flow(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        save_report = False
        if Config.ENABLE_REPORTS:
            save_report = messagebox.askyesno(
                "Repair Workflow",
                "Save a full report after the workflow finishes?",
            )
        else:
            messagebox.showinfo(
                "Reports Disabled",
                "Reports are disabled in Settings; workflow will run without saving a report.",
            )

        def confirm(prompt: str) -> bool:
            return messagebox.askyesno("Confirm Remediation", prompt)

        def emit(message: str, level: str) -> None:
            self._log(message, level=level)

        def runner() -> Dict[str, Any]:
            workflow = RepairWorkflow(
                device_id,
                confirm_callback=confirm,
                emit_callback=emit,
                save_report=save_report,
            )
            return workflow.run(progress_callback=self._log)

        self._run_task("Repair Workflow", runner)

    def _screenshot(self) -> None:
        device_id = self._get_selected_device()
        if device_id:
            self._run_task("Screenshot", ScreenCapture.take_screenshot, device_id)

    def _run_display_diagnostics(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> None:
            try:
                self._log("Display diagnostics started...")
                self._start_progress()
                result = DisplayAnalyzer.analyze(device_id)
                summary, message = self._format_display_diagnostics_result(result)
                self._log(summary)
                self.status_var.set(summary)
                self.root.after(
                    0, lambda: messagebox.showinfo("Display Diagnostics", message)
                )
            except Exception as exc:
                self._log(f"Display diagnostics failed: {exc}", level="ERROR")
                self.status_var.set("Display diagnostics failed. See log for details.")
                self._show_task_error("Display diagnostics", exc=exc)
            finally:
                self._stop_progress()

        threading.Thread(target=runner, daemon=True).start()

    def _check_battery_health(self) -> None:
        from .core.diagnostics import DiagnosticsTools
        
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            battery = DiagnosticsTools.check_battery_health(device_id)
            self._log("Battery Health:")
            for key, value in battery.items():
                self._log(f"  {key}: {value}", level="DATA")
            return {"success": True, "message": "Battery health checked"}

        self._run_task("Battery Health", runner)

    def _check_storage_health(self) -> None:
        from .core.diagnostics import DiagnosticsTools
        
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            storage = DiagnosticsTools.check_storage_health(device_id)
            self._log("Storage Health:")
            for partition in storage.get('partitions', []):
                self._log(f"  {partition.get('mounted_on')}: {partition.get('used')}/{partition.get('size')} ({partition.get('use_percent')})", level="DATA")
            return {"success": True, "message": "Storage health checked"}

        self._run_task("Storage Health", runner)

    def _check_temperature(self) -> None:
        from .core.diagnostics import DiagnosticsTools
        
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            temps = DiagnosticsTools.get_device_temperature(device_id)
            self._log("Device Temperature:")
            if temps:
                for sensor, value in temps.items():
                    self._log(f"  {sensor}: {value}", level="DATA")
            else:
                self._log("  No temperature data available", level="DATA")
            return {"success": True, "message": "Temperature checked"}

        self._run_task("Temperature Check", runner)

    def _run_full_diagnostics(self) -> None:
        from .core.diagnostics import DiagnosticsTools
        
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            diagnostics = DiagnosticsTools.run_device_diagnostics(device_id)
            self._log("Full Device Diagnostics:")
            
            self._log("Battery:", level="DATA")
            for key, value in diagnostics.get('battery', {}).items():
                self._log(f"  {key}: {value}", level="DATA")
            
            self._log("Storage:", level="DATA")
            for partition in diagnostics.get('storage', {}).get('partitions', [])[:5]:
                self._log(f"  {partition.get('mounted_on')}: {partition.get('available')} available", level="DATA")
            
            if diagnostics.get('imei'):
                self._log(f"IMEI: {diagnostics['imei']}", level="DATA")
            
            if diagnostics.get('build_fingerprint'):
                self._log(f"Build: {diagnostics['build_fingerprint']}", level="DATA")
            
            return {"success": True, "message": "Full diagnostics complete"}

        self._run_task("Full Diagnostics", runner)

    def _format_display_diagnostics_result(self, result: Dict[str, Any]) -> tuple[str, str]:
        analysis = result.get("screenshot_analysis") or {}
        black_frame = result.get("black_frame_detected")
        if black_frame is True:
            headline = "Screenshot appears black."
            implication = "Screenshot black → system rendering or power state issue."
        elif black_frame is False:
            headline = "Screenshot looks normal."
            implication = "Screenshot looks normal → display hardware likely at fault."
        elif "error" in analysis:
            headline = f"Screenshot failed: {analysis.get('error')}"
            implication = "Check ADB connectivity and try again."
        elif "note" in analysis:
            headline = analysis.get("note", "Screenshot captured without pixel analysis.")
            implication = "Open the screenshot file to verify the panel state."
        else:
            headline = "Screenshot analysis unavailable."
            implication = "Retry after confirming ADB access and device unlock."

        detail_lines = [
            f"Screen state: {result.get('screen_state') or 'unknown'}",
            f"Display power: {result.get('display_power') or 'n/a'}",
            f"Brightness: {result.get('display_brightness') or 'n/a'}",
            f"Refresh rate: {result.get('refresh_rate') or 'n/a'}",
        ]
        if result.get("screenshot_path"):
            detail_lines.append(f"Screenshot saved: {result['screenshot_path']}")

        summary = f"Display diagnostics complete: {headline}"
        message = "\n".join([headline, "", implication, "", *detail_lines])
        return summary, message

    def _run_problem_category(self, category: str) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        category_labels = {
            "startup_wizard": "Startup Wizard",
            "network": "Network",
            "display": "Display",
            "backup": "Backup",
        }
        analyzers = {
            "startup_wizard": self._analyze_startup_wizard_category,
            "network": self._analyze_network_category,
            "display": self._analyze_display_category,
            "backup": self._analyze_backup_category,
        }
        label = category_labels.get(category, "Problem Category")
        analyzer = analyzers.get(category)
        if analyzer is None:
            self._log(f"{label} diagnostics unavailable.", level="ERROR")
            self.status_var.set(f"{label} diagnostics unavailable.")
            return

        def runner() -> Dict[str, Any]:
            result = analyzer(device_id)
            summary = result.get("summary", f"{label} diagnostics complete.")
            details = result.get("details", [])
            self.root.after(0, lambda: self._set_problem_category_summary(summary, details))
            for line in details:
                self._log(f"{label}: {line}", level="DATA")
            return {"success": result.get("success", True), "message": summary}

        self._run_task(f"{label} Diagnostics", runner)

    def _set_problem_category_summary(self, summary: str, details: List[str]) -> None:
        content_lines = [summary]
        if details:
            content_lines.extend(details)
        self._set_device_section("categories", "\n".join(content_lines))

    def _analyze_network_category(self, device_id: str) -> Dict[str, Any]:
        analysis = NetworkAnalyzer.analyze(device_id)
        interfaces = analysis.get("interfaces") or []
        wifi = analysis.get("wifi") or {}
        stats = analysis.get("network_stats") or []

        wifi_status = wifi.get("status") or "unknown"
        ssid = wifi.get("ssid")
        wifi_label = wifi_status if not ssid else f"{wifi_status} (SSID {ssid})"
        interface_count = len(interfaces)

        if not interfaces and not wifi and not stats:
            summary = "Network check returned no data from the device."
            details = ["Confirm the device is reachable over ADB and try again."]
            return {"success": False, "summary": summary, "details": details}

        summary = f"Wi-Fi {wifi_label}; {interface_count} interface(s) detected."
        details = [f"Wi-Fi status: {wifi_label}"]
        if interfaces:
            interface_detail = ", ".join(
                f"{iface.get('name', 'unknown')}"
                f"{' ' + iface.get('ip') if iface.get('ip') else ''}"
                for iface in interfaces
            )
            details.append(f"Interfaces: {interface_detail}")
        if stats:
            traffic_detail = ", ".join(
                f"{item.get('interface', 'iface')} rx={item.get('rx_bytes')} tx={item.get('tx_bytes')}"
                for item in stats[:3]
            )
            details.append(f"Traffic (sample): {traffic_detail}")

        return {"success": True, "summary": summary, "details": details}

    def _analyze_display_category(self, device_id: str) -> Dict[str, Any]:
        analysis = DisplayAnalyzer.analyze(device_id)
        summary, message = self._format_display_diagnostics_result(analysis)
        detail_lines = [line for line in message.splitlines() if line.strip()]
        return {"success": True, "summary": summary, "details": detail_lines}

    def _analyze_backup_category(self, device_id: str) -> Dict[str, Any]:
        details: List[str] = []
        if not Config.ENABLE_AUTO_BACKUP:
            details.append("Auto backups are disabled in Settings.")

        backups = AutoBackup.list_backups(device_id)
        backup_count = len(backups)
        latest_backup = backups[0].get("created") if backups else None
        if latest_backup:
            details.append(f"Latest backup: {latest_backup}")
        else:
            details.append("No backups found for the selected device.")

        Config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            usage = shutil.disk_usage(Config.BACKUP_DIR)
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            details.append(f"Storage free: {free_gb:.1f} GB of {total_gb:.1f} GB")
            summary = (
                f"{backup_count} backup(s) recorded; {free_gb:.1f} GB free in backup storage."
            )
        except OSError as exc:
            details.append(f"Storage availability check failed: {exc}")
            summary = f"{backup_count} backup(s) recorded; storage availability unknown."

        return {"success": True, "summary": summary, "details": details}

    def _analyze_startup_wizard_category(self, device_id: str) -> Dict[str, Any]:
        result = StartupWizardAnalyzer.analyze(device_id)
        diagnostics = SetupWizardDiagnostics.analyze(device_id)
        running = result.get("running")
        active_package = result.get("active_package")
        setup_complete = result.get("setup_complete")
        provisioned = result.get("device_provisioned")
        status = diagnostics.get("status")

        if status == "wizard loop suspected":
            summary = "Startup wizard loop suspected."
        elif status == "setup incomplete":
            summary = "Startup wizard not completed."
        elif status == "boot incomplete":
            summary = "Boot incomplete (startup wizard not ready)."
        elif running:
            summary = f"Startup wizard active ({active_package or 'unknown package'})."
        elif setup_complete is True:
            summary = "Startup wizard completed."
        elif setup_complete is False:
            summary = "Startup wizard not completed."
        else:
            summary = "Startup wizard status unknown."

        details = [
            f"Diagnostic status: {status or 'unknown'}",
            f"Active package: {active_package or 'none'}",
            f"Setup complete: {setup_complete if setup_complete is not None else 'unknown'}",
            f"Device provisioned: {provisioned if provisioned is not None else 'unknown'}",
            "Boot completed: "
            f"{diagnostics.get('boot_completed') if diagnostics.get('boot_completed') is not None else 'unknown'}",
            "User setup complete: "
            f"{diagnostics.get('user_setup_complete') if diagnostics.get('user_setup_complete') is not None else 'unknown'}",
        ]
        installed = result.get("installed_packages") or []
        if installed:
            details.append(f"Installed packages: {', '.join(installed)}")
        top_activity = result.get("top_activity")
        if top_activity:
            details.append(f"Top activity: {top_activity}")
        resumed_activity = diagnostics.get("resumed_activity")
        if resumed_activity:
            details.append(f"Resumed activity: {resumed_activity}")
        setup_packages = diagnostics.get("setup_packages") or []
        if setup_packages:
            details.append(f"Setup packages: {', '.join(setup_packages)}")

        return {"success": True, "summary": summary, "details": details}

    def _make_scrollable(self, parent: ttk.Frame) -> ttk.Frame:
        """
        Create a scrollable frame within the given parent frame.
        Returns the inner frame where content should be packed.
        """
        # Create canvas and scrollbar
        canvas = tk.Canvas(
            parent,
            bg=self.theme["bg"],
            highlightthickness=0,
            bd=0
        )
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        # Create inner frame to hold the actual content
        scrollable_frame = ttk.Frame(canvas, style="Void.TFrame")
        
        # Configure the canvas scrolling
        def _on_frame_configure(event):
            # Update scroll region to encompass the inner frame
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def _on_canvas_configure(event):
            # Make the canvas window width match the canvas width
            canvas.itemconfig(canvas_window, width=event.width)
        
        scrollable_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel events for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        # Bind to canvas for mouse wheel scrolling
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel_linux)
        canvas.bind("<Button-5>", _on_mousewheel_linux)
        
        # Also bind to scrollable_frame for when mouse is over content
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<Button-4>", _on_mousewheel_linux)
        scrollable_frame.bind("<Button-5>", _on_mousewheel_linux)
        
        # Bind enter/leave events to enable scrolling when mouse is over the panel
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        canvas.bind("<Enter>", _bind_to_mousewheel)
        canvas.bind("<Leave>", _unbind_from_mousewheel)
        
        return scrollable_frame

    def _build_apps_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Apps", style="Void.TLabel").pack(anchor="w")

        filters = ttk.Frame(scrollable, style="Void.Card.TFrame")
        filters.pack(fill="x", pady=(6, 12))
        filters.configure(padding=12)
        ttk.Label(filters, text="List Apps", style="Void.TLabel").pack(anchor="w")
        filter_row = ttk.Frame(filters, style="Void.TFrame")
        filter_row.pack(fill="x", pady=(6, 0))
        ttk.Label(filter_row, text="Filter", style="Void.TLabel").pack(side="left")
        filter_menu = ttk.Combobox(
            filter_row,
            textvariable=self.apps_filter_var,
            values=["all", "system", "user"],
            state="readonly",
            width=12,
        )
        filter_menu.pack(side="left", padx=(8, 12))
        ttk.Button(
            filter_row,
            text="List Apps",
            style="Void.TButton",
            command=self._list_apps,
        ).pack(side="left")

        actions = ttk.Frame(scrollable, style="Void.Card.TFrame")
        actions.pack(fill="x", pady=(0, 12))
        actions.configure(padding=12)
        ttk.Label(actions, text="Package Actions", style="Void.TLabel").pack(anchor="w")

        package_row = ttk.Frame(actions, style="Void.TFrame")
        package_row.pack(fill="x", pady=(6, 8))
        ttk.Label(package_row, text="Package", style="Void.TLabel").pack(side="left")
        package_entry = tk.Entry(
            package_row,
            textvariable=self.apps_package_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        package_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))

        button_row = ttk.Frame(actions, style="Void.TFrame")
        button_row.pack(anchor="w")
        ttk.Button(
            button_row,
            text="Disable",
            style="Void.TButton",
            command=lambda: self._run_app_action("Disable app", AppManager.disable_app),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row,
            text="Enable",
            style="Void.TButton",
            command=lambda: self._run_app_action("Enable app", AppManager.enable_app),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row,
            text="Clear Data",
            style="Void.TButton",
            command=lambda: self._run_app_action("Clear app data", AppManager.clear_app_data),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row,
            text="Uninstall",
            style="Void.TButton",
            command=lambda: self._run_app_action("Uninstall app", AppManager.uninstall_app),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row,
            text="Backup APK",
            style="Void.TButton",
            command=self._backup_app,
        ).pack(side="left")

        # New app actions row
        button_row2 = ttk.Frame(actions, style="Void.TFrame")
        button_row2.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            button_row2,
            text="Force Stop",
            style="Void.TButton",
            command=lambda: self._run_app_action("Force stop app", AppManager.force_stop_app),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row2,
            text="Launch",
            style="Void.TButton",
            command=lambda: self._run_app_action("Launch app", AppManager.launch_app),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row2,
            text="View Info",
            style="Void.TButton",
            command=self._view_app_info,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            button_row2,
            text="Export List",
            style="Void.TButton",
            command=self._export_app_list,
        ).pack(side="left")

        # Install APK section
        install_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        install_card.pack(fill="x", pady=(0, 12))
        install_card.configure(padding=12)
        ttk.Label(install_card, text="Install APK", style="Void.TLabel").pack(anchor="w")
        install_row = ttk.Frame(install_card, style="Void.TFrame")
        install_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            install_row,
            text="Select & Install APK",
            style="Void.TButton",
            command=self._install_apk,
        ).pack(side="left")


    def _build_files_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Files", style="Void.TLabel").pack(anchor="w")

        list_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        list_card.pack(fill="x", pady=(6, 12))
        list_card.configure(padding=12)
        ttk.Label(list_card, text="List Files", style="Void.TLabel").pack(anchor="w")
        list_row = ttk.Frame(list_card, style="Void.TFrame")
        list_row.pack(fill="x", pady=(6, 0))
        ttk.Label(list_row, text="Remote path", style="Void.TLabel").pack(side="left")
        list_entry = tk.Entry(
            list_row,
            textvariable=self.files_list_path_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        list_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            list_row,
            text="List",
            style="Void.TButton",
            command=self._list_files,
        ).pack(side="left")

        pull_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        pull_card.pack(fill="x", pady=(0, 12))
        pull_card.configure(padding=12)
        ttk.Label(pull_card, text="Pull File", style="Void.TLabel").pack(anchor="w")
        pull_row = ttk.Frame(pull_card, style="Void.TFrame")
        pull_row.pack(fill="x", pady=(6, 6))
        ttk.Label(pull_row, text="Remote path", style="Void.TLabel").pack(side="left")
        pull_remote = tk.Entry(
            pull_row,
            textvariable=self.files_pull_remote_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        pull_remote.pack(side="left", fill="x", expand=True, padx=(8, 6))
        pull_row2 = ttk.Frame(pull_card, style="Void.TFrame")
        pull_row2.pack(fill="x")
        ttk.Label(pull_row2, text="Local path", style="Void.TLabel").pack(side="left")
        pull_local = tk.Entry(
            pull_row2,
            textvariable=self.files_pull_local_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        pull_local.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            pull_row2,
            text="Browse",
            style="Void.TButton",
            command=lambda: self._browse_save_path(self.files_pull_local_var),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            pull_row2,
            text="Pull",
            style="Void.TButton",
            command=self._pull_file,
        ).pack(side="left")

        push_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        push_card.pack(fill="x", pady=(0, 12))
        push_card.configure(padding=12)
        ttk.Label(push_card, text="Push File", style="Void.TLabel").pack(anchor="w")
        push_row = ttk.Frame(push_card, style="Void.TFrame")
        push_row.pack(fill="x", pady=(6, 6))
        ttk.Label(push_row, text="Local path", style="Void.TLabel").pack(side="left")
        push_local = tk.Entry(
            push_row,
            textvariable=self.files_push_local_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        push_local.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            push_row,
            text="Browse",
            style="Void.TButton",
            command=lambda: self._browse_open_path(self.files_push_local_var),
        ).pack(side="left")
        push_row2 = ttk.Frame(push_card, style="Void.TFrame")
        push_row2.pack(fill="x")
        ttk.Label(push_row2, text="Remote path", style="Void.TLabel").pack(side="left")
        push_remote = tk.Entry(
            push_row2,
            textvariable=self.files_push_remote_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        push_remote.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            push_row2,
            text="Push",
            style="Void.TButton",
            command=self._push_file,
        ).pack(side="left")

        delete_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        delete_card.pack(fill="x")
        delete_card.configure(padding=12)
        ttk.Label(delete_card, text="Delete File", style="Void.TLabel").pack(anchor="w")
        delete_row = ttk.Frame(delete_card, style="Void.TFrame")
        delete_row.pack(fill="x", pady=(6, 0))
        ttk.Label(delete_row, text="Remote path", style="Void.TLabel").pack(side="left")
        delete_entry = tk.Entry(
            delete_row,
            textvariable=self.files_delete_remote_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        delete_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            delete_row,
            text="Delete",
            style="Void.TButton",
            command=self._delete_file,
        ).pack(side="left")

        # File operations
        ops_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        ops_card.pack(fill="x", pady=(12, 12))
        ops_card.configure(padding=12)
        ttk.Label(ops_card, text="File Operations", style="Void.TLabel").pack(anchor="w")
        
        # Create folder
        mkdir_row = ttk.Frame(ops_card, style="Void.TFrame")
        mkdir_row.pack(fill="x", pady=(6, 6))
        ttk.Label(mkdir_row, text="Create Folder", style="Void.TLabel").pack(side="left")
        self.files_mkdir_var = tk.StringVar()
        mkdir_entry = tk.Entry(
            mkdir_row,
            textvariable=self.files_mkdir_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        mkdir_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            mkdir_row,
            text="Create",
            style="Void.TButton",
            command=self._create_folder,
        ).pack(side="left")
        
        # Rename/Move
        rename_row = ttk.Frame(ops_card, style="Void.TFrame")
        rename_row.pack(fill="x", pady=(0, 6))
        ttk.Label(rename_row, text="Rename/Move", style="Void.TLabel").pack(side="left")
        self.files_rename_old_var = tk.StringVar()
        self.files_rename_new_var = tk.StringVar()
        rename_old = tk.Entry(
            rename_row,
            textvariable=self.files_rename_old_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=20,
        )
        rename_old.pack(side="left", padx=(8, 6))
        ttk.Label(rename_row, text="→", style="Void.TLabel").pack(side="left")
        rename_new = tk.Entry(
            rename_row,
            textvariable=self.files_rename_new_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=20,
        )
        rename_new.pack(side="left", padx=(6, 6))
        ttk.Button(
            rename_row,
            text="Rename",
            style="Void.TButton",
            command=self._rename_file,
        ).pack(side="left")
        
        # Copy
        copy_row = ttk.Frame(ops_card, style="Void.TFrame")
        copy_row.pack(fill="x")
        ttk.Label(copy_row, text="Copy", style="Void.TLabel").pack(side="left")
        self.files_copy_src_var = tk.StringVar()
        self.files_copy_dst_var = tk.StringVar()
        copy_src = tk.Entry(
            copy_row,
            textvariable=self.files_copy_src_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=20,
        )
        copy_src.pack(side="left", padx=(8, 6))
        ttk.Label(copy_row, text="→", style="Void.TLabel").pack(side="left")
        copy_dst = tk.Entry(
            copy_row,
            textvariable=self.files_copy_dst_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=20,
        )
        copy_dst.pack(side="left", padx=(6, 6))
        ttk.Button(
            copy_row,
            text="Copy",
            style="Void.TButton",
            command=self._copy_file,
        ).pack(side="left")


    def _build_recovery_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Recovery", style="Void.TLabel").pack(anchor="w")

        data_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        data_card.pack(fill="x", pady=(6, 12))
        data_card.configure(padding=12)
        ttk.Label(data_card, text="Data Recovery", style="Void.TLabel").pack(anchor="w")
        data_actions = ttk.Frame(data_card, style="Void.TFrame")
        data_actions.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            data_actions,
            text="Recover Contacts",
            style="Void.TButton",
            command=self._recover_contacts,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            data_actions,
            text="Recover SMS",
            style="Void.TButton",
            command=self._recover_sms,
        ).pack(side="left")

        # Partition Operations
        partition_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        partition_card.pack(fill="x", pady=(0, 12))
        partition_card.configure(padding=12)
        ttk.Label(partition_card, text="Partition Operations", style="Void.TLabel").pack(anchor="w")
        
        partition_list_row = ttk.Frame(partition_card, style="Void.TFrame")
        partition_list_row.pack(fill="x", pady=(6, 6))
        ttk.Button(
            partition_list_row,
            text="List Partitions",
            style="Void.TButton",
            command=self._list_partitions,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            partition_list_row,
            text="View Partition Table",
            style="Void.TButton",
            command=self._view_partition_table,
        ).pack(side="left")
        
        partition_backup_row = ttk.Frame(partition_card, style="Void.TFrame")
        partition_backup_row.pack(fill="x", pady=(0, 6))
        ttk.Label(partition_backup_row, text="Partition Name:", style="Void.TLabel").pack(side="left")
        self.partition_name_var = tk.StringVar(value="boot")
        partition_entry = tk.Entry(
            partition_backup_row,
            textvariable=self.partition_name_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=15,
        )
        partition_entry.pack(side="left", padx=(8, 12))
        ttk.Button(
            partition_backup_row,
            text="Backup Partition",
            style="Void.TButton",
            command=self._backup_partition,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            partition_backup_row,
            text="⚠️ Wipe Partition",
            style="Void.TButton",
            command=self._wipe_partition,
        ).pack(side="left")

        # Root & Recovery Management
        root_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        root_card.pack(fill="x", pady=(0, 12))
        root_card.configure(padding=12)
        ttk.Label(root_card, text="Root & Recovery", style="Void.TLabel").pack(anchor="w")
        
        root_row1 = ttk.Frame(root_card, style="Void.TFrame")
        root_row1.pack(fill="x", pady=(6, 6))
        ttk.Button(
            root_row1,
            text="Verify Root",
            style="Void.TButton",
            command=self._verify_root,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row1,
            text="Safety Check",
            style="Void.TButton",
            command=self._run_safety_check,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row1,
            text="Extract Boot Image",
            style="Void.TButton",
            command=self._extract_boot_image,
        ).pack(side="left")
        
        root_row2 = ttk.Frame(root_card, style="Void.TFrame")
        root_row2.pack(fill="x", pady=(0, 6))
        ttk.Button(
            root_row2,
            text="Stage Magisk Patch",
            style="Void.TButton",
            command=self._stage_magisk_patch,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row2,
            text="Pull Magisk Image",
            style="Void.TButton",
            command=self._pull_magisk_image,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row2,
            text="Verify TWRP",
            style="Void.TButton",
            command=self._verify_twrp,
        ).pack(side="left")
        
        root_row3 = ttk.Frame(root_card, style="Void.TFrame")
        root_row3.pack(fill="x")
        ttk.Button(
            root_row3,
            text="Flash TWRP",
            style="Void.TButton",
            command=self._flash_twrp,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row3,
            text="Boot TWRP",
            style="Void.TButton",
            command=self._boot_twrp,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            root_row3,
            text="Rollback Flash",
            style="Void.TButton",
            command=self._rollback_flash,
        ).pack(side="left")

        frp_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        frp_card.pack(fill="x")
        frp_card.configure(padding=12)
        ttk.Label(frp_card, text="FRP Bypass", style="Void.TLabel").pack(anchor="w")
        frp_row = ttk.Frame(frp_card, style="Void.TFrame")
        frp_row.pack(fill="x", pady=(6, 0))
        ttk.Label(frp_row, text="Method", style="Void.TLabel").pack(side="left")
        frp_methods = sorted(self.frp_engine.methods.keys())
        self.frp_method_var = tk.StringVar(value=frp_methods[0] if frp_methods else "")
        frp_menu = ttk.Combobox(
            frp_row,
            textvariable=self.frp_method_var,
            values=frp_methods,
            state="readonly",
            width=24,
        )
        frp_menu.pack(side="left", padx=(8, 12))
        ttk.Button(
            frp_row,
            text="Execute",
            style="Void.TButton",
            command=self._run_frp_method,
        ).pack(side="left")

    def _build_system_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="System Tweaks", style="Void.TLabel").pack(anchor="w")

        tweak_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        tweak_card.pack(fill="x", pady=(6, 12))
        tweak_card.configure(padding=12)
        ttk.Label(tweak_card, text="Apply Tweak", style="Void.TLabel").pack(anchor="w")
        tweak_row = ttk.Frame(tweak_card, style="Void.TFrame")
        tweak_row.pack(fill="x", pady=(6, 0))
        ttk.Label(tweak_row, text="Type", style="Void.TLabel").pack(side="left")
        tweak_menu = ttk.Combobox(
            tweak_row,
            textvariable=self.tweak_type_var,
            values=["dpi", "animation", "timeout"],
            state="readonly",
            width=12,
        )
        tweak_menu.pack(side="left", padx=(8, 12))
        ttk.Label(tweak_row, text="Value", style="Void.TLabel").pack(side="left")
        tweak_entry = tk.Entry(
            tweak_row,
            textvariable=self.tweak_value_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=12,
        )
        tweak_entry.pack(side="left", padx=(8, 12))
        ttk.Button(
            tweak_row,
            text="Apply",
            style="Void.TButton",
            command=self._apply_tweak,
        ).pack(side="left")

        usb_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        usb_card.pack(fill="x", pady=(0, 12))
        usb_card.configure(padding=12)
        ttk.Label(usb_card, text="USB Debugging", style="Void.TLabel").pack(anchor="w")
        usb_row = ttk.Frame(usb_card, style="Void.TFrame")
        usb_row.pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(
            usb_row,
            text="Force mode (engineering builds)",
            variable=self.usb_force_var,
            style="Void.TCheckbutton",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(
            usb_row,
            text="Enable USB Debugging",
            style="Void.TButton",
            command=self._enable_usb_debugging,
        ).pack(side="left")

        # Reboot options
        reboot_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        reboot_card.pack(fill="x", pady=(0, 12))
        reboot_card.configure(padding=12)
        ttk.Label(reboot_card, text="Reboot Options", style="Void.TLabel").pack(anchor="w")
        reboot_row = ttk.Frame(reboot_card, style="Void.TFrame")
        reboot_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            reboot_row,
            text="System",
            style="Void.TButton",
            command=lambda: self._reboot_device('system'),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            reboot_row,
            text="Recovery",
            style="Void.TButton",
            command=lambda: self._reboot_device('recovery'),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            reboot_row,
            text="Bootloader",
            style="Void.TButton",
            command=lambda: self._reboot_device('bootloader'),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            reboot_row,
            text="Shutdown",
            style="Void.TButton",
            command=self._shutdown_device,
        ).pack(side="left")

        # System toggles
        toggles_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        toggles_card.pack(fill="x", pady=(0, 12))
        toggles_card.configure(padding=12)
        ttk.Label(toggles_card, text="System Toggles", style="Void.TLabel").pack(anchor="w")
        toggle_row = ttk.Frame(toggles_card, style="Void.TFrame")
        toggle_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            toggle_row,
            text="Stay Awake ON",
            style="Void.TButton",
            command=lambda: self._toggle_system_setting('stay_awake', True),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="Stay Awake OFF",
            style="Void.TButton",
            command=lambda: self._toggle_system_setting('stay_awake', False),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="Battery Saver ON",
            style="Void.TButton",
            command=lambda: self._toggle_system_setting('battery_saver', True),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="Battery Saver OFF",
            style="Void.TButton",
            command=lambda: self._toggle_system_setting('battery_saver', False),
        ).pack(side="left")

        # ADB over TCP/IP
        adb_tcp_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        adb_tcp_card.pack(fill="x")
        adb_tcp_card.configure(padding=12)
        ttk.Label(adb_tcp_card, text="ADB over WiFi", style="Void.TLabel").pack(anchor="w")
        adb_tcp_row = ttk.Frame(adb_tcp_card, style="Void.TFrame")
        adb_tcp_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            adb_tcp_row,
            text="Enable (5555)",
            style="Void.TButton",
            command=self._enable_adb_tcpip,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            adb_tcp_row,
            text="Disable",
            style="Void.TButton",
            command=self._disable_adb_tcpip,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            adb_tcp_row,
            text="Check Status",
            style="Void.TButton",
            command=self._check_adb_tcpip_status,
        ).pack(side="left")


    def _build_network_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Network", style="Void.TLabel").pack(anchor="w")

        net_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        net_card.pack(fill="x", pady=(6, 12))
        net_card.configure(padding=12)
        ttk.Label(net_card, text="Connectivity Check", style="Void.TLabel").pack(anchor="w")
        ttk.Button(
            net_card,
            text="Check Internet",
            style="Void.TButton",
            command=self._check_internet,
        ).pack(anchor="w", pady=(6, 0))

        # Network toggles
        toggles_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        toggles_card.pack(fill="x", pady=(6, 12))
        toggles_card.configure(padding=12)
        ttk.Label(toggles_card, text="Network Toggles", style="Void.TLabel").pack(anchor="w")
        toggle_row = ttk.Frame(toggles_card, style="Void.TFrame")
        toggle_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            toggle_row,
            text="WiFi ON",
            style="Void.TButton",
            command=lambda: self._toggle_network('wifi', True),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="WiFi OFF",
            style="Void.TButton",
            command=lambda: self._toggle_network('wifi', False),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="Data ON",
            style="Void.TButton",
            command=lambda: self._toggle_network('data', True),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            toggle_row,
            text="Data OFF",
            style="Void.TButton",
            command=lambda: self._toggle_network('data', False),
        ).pack(side="left")

        # Network info
        info_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        info_card.pack(fill="x")
        info_card.configure(padding=12)
        ttk.Label(info_card, text="Network Information", style="Void.TLabel").pack(anchor="w")
        info_row = ttk.Frame(info_card, style="Void.TFrame")
        info_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            info_row,
            text="Show IP/MAC",
            style="Void.TButton",
            command=self._show_network_info,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            info_row,
            text="List WiFi Networks",
            style="Void.TButton",
            command=self._list_wifi_networks,
        ).pack(side="left")


    def _build_logcat_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Logcat", style="Void.TLabel").pack(anchor="w")

        logcat_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        logcat_card.pack(fill="x", pady=(6, 12))
        logcat_card.configure(padding=12)
        ttk.Label(logcat_card, text="Stream Logs", style="Void.TLabel").pack(anchor="w")
        logcat_row = ttk.Frame(logcat_card, style="Void.TFrame")
        logcat_row.pack(fill="x", pady=(6, 0))
        ttk.Label(logcat_row, text="Filter tag", style="Void.TLabel").pack(side="left")
        logcat_entry = tk.Entry(
            logcat_row,
            textvariable=self.logcat_filter_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        logcat_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            logcat_row,
            text="Start",
            style="Void.TButton",
            command=self._start_logcat,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            logcat_row,
            text="Stop",
            style="Void.TButton",
            command=self._stop_logcat,
        ).pack(side="left")

        # Log capture and management
        capture_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        capture_card.pack(fill="x", pady=(0, 12))
        capture_card.configure(padding=12)
        ttk.Label(capture_card, text="Log Management", style="Void.TLabel").pack(anchor="w")
        capture_row = ttk.Frame(capture_card, style="Void.TFrame")
        capture_row.pack(fill="x", pady=(6, 0))
        ttk.Button(
            capture_row,
            text="Export Logcat",
            style="Void.TButton",
            command=self._export_logcat,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            capture_row,
            text="Clear Buffer",
            style="Void.TButton",
            command=self._clear_logcat,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            capture_row,
            text="Kernel Log",
            style="Void.TButton",
            command=self._view_kernel_log,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            capture_row,
            text="Crash Logs",
            style="Void.TButton",
            command=self._view_crash_logs,
        ).pack(side="left")


    def _build_monitor_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Monitoring", style="Void.TLabel").pack(anchor="w")

        monitor_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        monitor_card.pack(fill="x", pady=(6, 12))
        monitor_card.configure(padding=12)
        ttk.Label(monitor_card, text="System Monitor", style="Void.TLabel").pack(anchor="w")
        ttk.Label(
            monitor_card,
            textvariable=self.monitor_status_var,
            style="Void.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        monitor_actions = ttk.Frame(monitor_card, style="Void.TFrame")
        monitor_actions.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            monitor_actions,
            text="Start Monitoring",
            style="Void.TButton",
            command=self._start_monitoring,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            monitor_actions,
            text="Stop Monitoring",
            style="Void.TButton",
            command=self._stop_monitoring,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            monitor_actions,
            text="Snapshot Stats",
            style="Void.TButton",
            command=self._snapshot_monitor,
        ).pack(side="left")

    def _build_edl_tools_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="EDL Flash/Dump", style="Void.TLabel").pack(anchor="w")

        flash_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        flash_card.pack(fill="x", pady=(6, 12))
        flash_card.configure(padding=12)
        ttk.Label(flash_card, text="EDL Flash", style="Void.TLabel").pack(anchor="w")
        loader_row = ttk.Frame(flash_card, style="Void.TFrame")
        loader_row.pack(fill="x", pady=(6, 6))
        ttk.Label(loader_row, text="Loader", style="Void.TLabel").pack(side="left")
        loader_entry = tk.Entry(
            loader_row,
            textvariable=self.edl_loader_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        loader_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            loader_row,
            text="Browse",
            style="Void.TButton",
            command=lambda: self._browse_open_path(self.edl_loader_var),
        ).pack(side="left")
        image_row = ttk.Frame(flash_card, style="Void.TFrame")
        image_row.pack(fill="x")
        ttk.Label(image_row, text="Image", style="Void.TLabel").pack(side="left")
        image_entry = tk.Entry(
            image_row,
            textvariable=self.edl_image_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        image_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            image_row,
            text="Browse",
            style="Void.TButton",
            command=lambda: self._browse_open_path(self.edl_image_var),
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            image_row,
            text="Flash",
            style="Void.TButton",
            command=self._edl_flash,
        ).pack(side="left")

        dump_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        dump_card.pack(fill="x", pady=(0, 12))
        dump_card.configure(padding=12)
        ttk.Label(dump_card, text="EDL Dump", style="Void.TLabel").pack(anchor="w")
        dump_row = ttk.Frame(dump_card, style="Void.TFrame")
        dump_row.pack(fill="x", pady=(6, 0))
        ttk.Label(dump_row, text="Partition", style="Void.TLabel").pack(side="left")
        dump_entry = tk.Entry(
            dump_row,
            textvariable=self.edl_partition_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        dump_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            dump_row,
            text="Dump",
            style="Void.TButton",
            command=self._edl_dump,
        ).pack(side="left")

        # EDL Tools
        edl_tools_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        edl_tools_card.pack(fill="x", pady=(0, 12))
        edl_tools_card.configure(padding=12)
        ttk.Label(edl_tools_card, text="EDL Tools", style="Void.TLabel").pack(anchor="w")
        edl_tools_row1 = ttk.Frame(edl_tools_card, style="Void.TFrame")
        edl_tools_row1.pack(fill="x", pady=(6, 6))
        ttk.Button(
            edl_tools_row1,
            text="List Programmers",
            style="Void.TButton",
            command=self._edl_list_programmers,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row1,
            text="Detect EDL Devices",
            style="Void.TButton",
            command=self._edl_detect_devices,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row1,
            text="Compatibility Matrix",
            style="Void.TButton",
            command=self._edl_compat_matrix,
        ).pack(side="left")
        
        edl_tools_row2 = ttk.Frame(edl_tools_card, style="Void.TFrame")
        edl_tools_row2.pack(fill="x", pady=(0, 6))
        ttk.Button(
            edl_tools_row2,
            text="Sparse to Raw",
            style="Void.TButton",
            command=self._edl_sparse_to_raw,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row2,
            text="Raw to Sparse",
            style="Void.TButton",
            command=self._edl_raw_to_sparse,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row2,
            text="Verify Image Hash",
            style="Void.TButton",
            command=self._edl_verify_hash,
        ).pack(side="left")
        
        edl_tools_row3 = ttk.Frame(edl_tools_card, style="Void.TFrame")
        edl_tools_row3.pack(fill="x")
        ttk.Button(
            edl_tools_row3,
            text="Unbrick Checklist",
            style="Void.TButton",
            command=self._edl_unbrick_checklist,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row3,
            text="Device Notes",
            style="Void.TButton",
            command=self._edl_device_notes,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            edl_tools_row3,
            text="Capture EDL Log",
            style="Void.TButton",
            command=self._edl_capture_log,
        ).pack(side="left")

    def _build_data_exports_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Data / Reports / Exports", style="Void.TLabel").pack(anchor="w")

        list_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        list_card.pack(fill="x", pady=(6, 12))
        list_card.configure(padding=12)
        ttk.Label(list_card, text="Recent Items", style="Void.TLabel").pack(anchor="w")
        limit_row = ttk.Frame(list_card, style="Void.TFrame")
        limit_row.pack(fill="x", pady=(6, 6))
        ttk.Label(limit_row, text="Limit", style="Void.TLabel").pack(side="left")
        limit_entry = tk.Entry(
            limit_row,
            textvariable=self.recent_items_limit_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=8,
        )
        limit_entry.pack(side="left", padx=(8, 12))
        ttk.Button(
            limit_row,
            text="List Backups",
            style="Void.TButton",
            command=self._list_backups,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            limit_row,
            text="List Reports",
            style="Void.TButton",
            command=self._list_reports,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            limit_row,
            text="List Exports",
            style="Void.TButton",
            command=self._list_exports,
        ).pack(side="left")

        export_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        export_card.pack(fill="x", pady=(0, 12))
        export_card.configure(padding=12)
        ttk.Label(export_card, text="Export Helpers", style="Void.TLabel").pack(anchor="w")
        export_row = ttk.Frame(export_card, style="Void.TFrame")
        export_row.pack(anchor="w", pady=(6, 0))
        ttk.Button(
            export_row,
            text="Devices JSON",
            style="Void.TButton",
            command=self._export_devices_json,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            export_row,
            text="Stats JSON",
            style="Void.TButton",
            command=self._export_stats_json,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            export_row,
            text="Logs JSON",
            style="Void.TButton",
            command=self._export_logs_json,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            export_row,
            text="Reports JSON",
            style="Void.TButton",
            command=self._export_reports_json,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            export_row,
            text="Backups JSON",
            style="Void.TButton",
            command=self._export_backups_json,
        ).pack(side="left")

        open_row = ttk.Frame(export_card, style="Void.TFrame")
        open_row.pack(anchor="w", pady=(8, 0))
        ttk.Button(
            open_row,
            text="Open Reports Folder",
            style="Void.TButton",
            command=self._open_reports_dir,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            open_row,
            text="Open Exports Folder",
            style="Void.TButton",
            command=self._open_exports_dir,
        ).pack(side="left")

    def _build_db_tools_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Database Tools", style="Void.TLabel").pack(anchor="w")

        health_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        health_card.pack(fill="x", pady=(6, 12))
        health_card.configure(padding=12)
        ttk.Label(health_card, text="Health & Stats", style="Void.TLabel").pack(anchor="w")
        ttk.Button(
            health_card,
            text="DB Health",
            style="Void.TButton",
            command=self._db_health,
        ).pack(anchor="w", pady=(6, 0))

        records_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        records_card.pack(fill="x", pady=(0, 12))
        records_card.configure(padding=12)
        ttk.Label(records_card, text="Recent Records", style="Void.TLabel").pack(anchor="w")
        records_row = ttk.Frame(records_card, style="Void.TFrame")
        records_row.pack(fill="x", pady=(6, 0))
        ttk.Label(records_row, text="Limit", style="Void.TLabel").pack(side="left")
        records_entry = tk.Entry(
            records_row,
            textvariable=self.db_limit_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=8,
        )
        records_entry.pack(side="left", padx=(8, 12))
        ttk.Button(
            records_row,
            text="Recent Logs",
            style="Void.TButton",
            command=self._show_recent_logs,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            records_row,
            text="Recent Backups",
            style="Void.TButton",
            command=self._show_recent_backups,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            records_row,
            text="Recent Reports",
            style="Void.TButton",
            command=self._show_recent_reports,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            records_row,
            text="Recent Devices",
            style="Void.TButton",
            command=self._show_recent_devices,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            records_row,
            text="Top Methods",
            style="Void.TButton",
            command=self._show_top_methods,
        ).pack(side="left")

        export_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        export_card.pack(fill="x")
        export_card.configure(padding=12)
        ttk.Label(export_card, text="Logs Export", style="Void.TLabel").pack(anchor="w")
        export_row = ttk.Frame(export_card, style="Void.TFrame")
        export_row.pack(fill="x", pady=(6, 6))
        ttk.Label(export_row, text="Format", style="Void.TLabel").pack(side="left")
        format_menu = ttk.Combobox(
            export_row,
            textvariable=self.log_export_format_var,
            values=["json", "csv"],
            state="readonly",
            width=8,
        )
        format_menu.pack(side="left", padx=(8, 12))
        ttk.Label(export_row, text="Limit", style="Void.TLabel").pack(side="left")
        limit_entry = tk.Entry(
            export_row,
            textvariable=self.log_export_limit_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=8,
        )
        limit_entry.pack(side="left", padx=(8, 12))
        ttk.Button(
            export_row,
            text="Export Logs",
            style="Void.TButton",
            command=self._export_filtered_logs,
        ).pack(side="left")

        filter_row = ttk.Frame(export_card, style="Void.TFrame")
        filter_row.pack(fill="x")
        for label, var in [
            ("Level", self.log_export_level_var),
            ("Category", self.log_export_category_var),
            ("Device", self.log_export_device_var),
            ("Method", self.log_export_method_var),
            ("Since", self.log_export_since_var),
            ("Until", self.log_export_until_var),
        ]:
            item = ttk.Frame(filter_row, style="Void.TFrame")
            item.pack(side="left", padx=(0, 8))
            ttk.Label(item, text=label, style="Void.TLabel").pack(anchor="w")
            entry = tk.Entry(
                item,
                textvariable=var,
                bg=self.theme["panel_alt"],
                fg=self.theme["text"],
                insertbackground=self.theme["accent"],
                relief="flat",
                font=("Consolas", 9),
                width=12,
            )
            entry.pack(anchor="w")

    def _build_command_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Command Center", style="Void.TLabel").pack(anchor="w")

        search_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        search_card.pack(fill="x", pady=(6, 12))
        search_card.configure(padding=12)
        ttk.Label(search_card, text="Search Commands", style="Void.TLabel").pack(anchor="w")
        search_row = ttk.Frame(search_card, style="Void.TFrame")
        search_row.pack(fill="x", pady=(6, 0))
        search_entry = tk.Entry(
            search_row,
            textvariable=self.command_search_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(
            search_row,
            text="Clear",
            style="Void.TButton",
            command=lambda: self.command_search_var.set(""),
        ).pack(side="left")
        Tooltip(search_entry, "Filter CLI commands by name, summary, category, or usage.")
        self.command_search_var.trace_add("write", lambda *_: self._refresh_command_list())

        list_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        list_card.pack(fill="both", expand=True, pady=(0, 12))
        list_card.configure(padding=12)
        ttk.Label(list_card, text="Available Commands", style="Void.TLabel").pack(anchor="w")
        list_row = ttk.Frame(list_card, style="Void.TFrame")
        list_row.pack(fill="both", expand=True, pady=(6, 0))
        self.command_list = tk.Listbox(
            list_row,
            height=10,
            bg=self.theme["panel_alt"],
            fg=self.theme["accent"],
            selectbackground=self.theme["button_active"],
            selectforeground=self.theme["text"],
            highlightthickness=0,
            font=("Consolas", 10),
        )
        self.command_list.pack(side="left", fill="both", expand=True)
        self.command_list.bind("<<ListboxSelect>>", lambda _: self._on_command_select())

        details_frame = ttk.Frame(list_row, style="Void.TFrame")
        details_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))
        ttk.Label(details_frame, text="Command Details", style="Void.TLabel").pack(anchor="w")
        ttk.Label(
            details_frame,
            textvariable=self.command_detail_var,
            style="Void.TLabel",
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        input_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        input_card.pack(fill="x")
        input_card.configure(padding=12)
        ttk.Label(input_card, text="Run Command", style="Void.TLabel").pack(anchor="w")

        args_row = ttk.Frame(input_card, style="Void.TFrame")
        args_row.pack(fill="x", pady=(6, 6))
        ttk.Label(args_row, text="Arguments", style="Void.TLabel").pack(side="left")
        args_entry = tk.Entry(
            args_row,
            textvariable=self.command_args_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        args_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            args_row,
            text="Use Selected",
            style="Void.TButton",
            command=self._insert_selected_command,
        ).pack(side="left")

        line_row = ttk.Frame(input_card, style="Void.TFrame")
        line_row.pack(fill="x")
        ttk.Label(line_row, text="Command Line", style="Void.TLabel").pack(side="left")
        line_entry = tk.Entry(
            line_row,
            textvariable=self.command_line_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        line_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            line_row,
            text="Run",
            style="Void.TButton",
            command=self._run_command_line,
        ).pack(side="left")

        # Shell command execution
        shell_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        shell_card.pack(fill="x", pady=(12, 0))
        shell_card.configure(padding=12)
        ttk.Label(shell_card, text="Shell Commands (ADB)", style="Void.TLabel").pack(anchor="w")
        shell_row = ttk.Frame(shell_card, style="Void.TFrame")
        shell_row.pack(fill="x", pady=(6, 0))
        ttk.Label(shell_row, text="Command", style="Void.TLabel").pack(side="left")
        self.shell_command_var = tk.StringVar()
        shell_entry = tk.Entry(
            shell_row,
            textvariable=self.shell_command_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        shell_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            shell_row,
            text="Execute",
            style="Void.TButton",
            command=self._execute_shell_command,
        ).pack(side="left")

        self._refresh_command_list()

    def _build_browser_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Browser Automation", style="Void.TLabel").pack(anchor="w")
        description = (
            "Launch a headed browser session and drive navigation, clicks, and typing. "
            "Automated actions require confirmation by default."
        )
        ttk.Label(
            scrollable,
            text=description,
            style="Void.TLabel",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))

        controls_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        controls_card.pack(fill="x", pady=(0, 12))
        controls_card.configure(padding=12)

        toolbar = ttk.Frame(controls_card, style="Void.TFrame")
        toolbar.pack(fill="x")
        ttk.Button(
            toolbar,
            text="Launch Browser",
            style="Void.TButton",
            command=self._launch_browser,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            toolbar,
            text="Close Browser",
            style="Void.TButton",
            command=self._close_browser,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            toolbar,
            text="Screenshot",
            style="Void.TButton",
            command=self._browser_screenshot,
        ).pack(side="left")
        ttk.Checkbutton(
            toolbar,
            text="Require confirmations",
            variable=self.browser_confirm_var,
            style="Void.TCheckbutton",
        ).pack(side="right")

        ttk.Label(
            controls_card,
            textvariable=self.browser_status_var,
            style="Void.TLabel",
        ).pack(anchor="w", pady=(8, 0))

        nav_row = ttk.Frame(controls_card, style="Void.TFrame")
        nav_row.pack(fill="x", pady=(10, 0))
        ttk.Label(nav_row, text="URL", style="Void.TLabel").pack(side="left")
        url_entry = tk.Entry(
            nav_row,
            textvariable=self.browser_url_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        url_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            nav_row,
            text="Open",
            style="Void.TButton",
            command=self._browser_open,
        ).pack(side="left")

        action_row = ttk.Frame(controls_card, style="Void.TFrame")
        action_row.pack(fill="x", pady=(10, 0))
        ttk.Label(action_row, text="Click", style="Void.TLabel").pack(side="left")
        x_entry = tk.Entry(
            action_row,
            textvariable=self.browser_x_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=8,
        )
        x_entry.pack(side="left", padx=(6, 4))
        y_entry = tk.Entry(
            action_row,
            textvariable=self.browser_y_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=8,
        )
        y_entry.pack(side="left", padx=(0, 8))
        ttk.Button(
            action_row,
            text="Click",
            style="Void.TButton",
            command=self._browser_click,
        ).pack(side="left")

        type_row = ttk.Frame(controls_card, style="Void.TFrame")
        type_row.pack(fill="x", pady=(10, 0))
        ttk.Label(type_row, text="Type", style="Void.TLabel").pack(side="left")
        type_entry = tk.Entry(
            type_row,
            textvariable=self.browser_text_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        type_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            type_row,
            text="Send",
            style="Void.TButton",
            command=self._browser_type,
        ).pack(side="left")

        log_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        log_card.pack(fill="both", expand=True)
        log_card.configure(padding=12)
        ttk.Label(log_card, text="Browser Action Log", style="Void.TLabel").pack(anchor="w")
        self.browser_log = scrolledtext.ScrolledText(
            log_card,
            height=12,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            font=("Consolas", 10),
            state="disabled",
            wrap="word",
        )
        self.browser_log.pack(fill="both", expand=True, pady=(6, 0))

    def _build_assistant_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Gemini Assistant", style="Void.TLabel").pack(anchor="w")

        description = (
            "Chat with Gemini to plan workflows. The assistant maintains a task list "
            "and updates it as you refine your goal."
        )
        ttk.Label(
            scrollable,
            text=description,
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))

        header = ttk.Frame(scrollable, style="Void.TFrame")
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Model", style="Void.TLabel").pack(side="left")
        model_entry = tk.Entry(
            header,
            textvariable=self.gemini_model_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=24,
        )
        model_entry.pack(side="left", padx=(8, 6))
        ttk.Button(
            header,
            text="Save Model",
            style="Void.TButton",
            command=self._save_gemini_model,
        ).pack(side="left")
        ttk.Button(
            header,
            text="Set API Key",
            style="Void.TButton",
            command=self._prompt_gemini_api_key,
        ).pack(side="left", padx=(8, 0))

        endpoint_row = ttk.Frame(scrollable, style="Void.TFrame")
        endpoint_row.pack(fill="x", pady=(0, 8))
        ttk.Label(endpoint_row, text="API Base", style="Void.TLabel").pack(side="left")
        api_entry = tk.Entry(
            endpoint_row,
            textvariable=self.gemini_api_base_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            width=48,
        )
        api_entry.pack(side="left", padx=(8, 6), fill="x", expand=True)
        ttk.Button(
            endpoint_row,
            text="Save API Base",
            style="Void.TButton",
            command=self._save_gemini_api_base,
        ).pack(side="left")

        advanced_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        advanced_card.pack(fill="x", pady=(0, 12))
        advanced_card.configure(padding=12)
        ttk.Label(advanced_card, text="Advanced Gemini Payload", style="Void.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            advanced_card,
            text="Paste JSON to pass through systemInstruction, tools, or other payload fields.",
            style="Void.TLabel",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))
        ttk.Label(advanced_card, text="System Instruction", style="Void.TLabel").pack(
            anchor="w"
        )
        self.gemini_system_text = scrolledtext.ScrolledText(
            advanced_card,
            height=4,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
        )
        self.gemini_system_text.pack(fill="x", expand=True, pady=(4, 8))
        self.gemini_system_text.insert("1.0", self.gemini_system_instruction)

        ttk.Label(advanced_card, text="Generation Config (JSON)", style="Void.TLabel").pack(
            anchor="w"
        )
        self.gemini_generation_text = scrolledtext.ScrolledText(
            advanced_card,
            height=4,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
        )
        self.gemini_generation_text.pack(fill="x", expand=True, pady=(4, 8))
        self.gemini_generation_text.insert("1.0", self.gemini_generation_config)

        ttk.Label(advanced_card, text="Extra Payload (JSON)", style="Void.TLabel").pack(
            anchor="w"
        )
        self.gemini_payload_text = scrolledtext.ScrolledText(
            advanced_card,
            height=6,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
        )
        self.gemini_payload_text.pack(fill="x", expand=True, pady=(4, 8))
        self.gemini_payload_text.insert("1.0", self.gemini_extra_payload)
        ttk.Button(
            advanced_card,
            text="Save Advanced Settings",
            style="Void.TButton",
            command=self._save_gemini_advanced,
        ).pack(anchor="w", pady=(4, 0))

        content_row = ttk.Frame(scrollable, style="Void.TFrame")
        content_row.pack(fill="both", expand=True)

        tasks_card = ttk.Frame(content_row, style="Void.Card.TFrame")
        tasks_card.pack(side="left", fill="y", padx=(0, 12))
        tasks_card.configure(padding=12)
        ttk.Label(tasks_card, text="Agent Tasks", style="Void.TLabel").pack(anchor="w")
        self.assistant_task_list = tk.Listbox(
            tasks_card,
            height=12,
            width=28,
            bg=self.theme["panel_alt"],
            fg=self.theme["accent"],
            selectbackground=self.theme["button_active"],
            selectforeground=self.theme["text"],
            highlightthickness=0,
            font=("Consolas", 10),
        )
        self.assistant_task_list.pack(fill="both", expand=True, pady=(6, 0))
        ttk.Button(
            tasks_card,
            text="Clear Tasks",
            style="Void.TButton",
            command=self._clear_assistant_tasks,
        ).pack(anchor="w", pady=(8, 0))

        chat_card = ttk.Frame(content_row, style="Void.Card.TFrame")
        chat_card.pack(side="left", fill="both", expand=True)
        chat_card.configure(padding=12)
        ttk.Label(chat_card, text="Chat", style="Void.TLabel").pack(anchor="w")
        self.assistant_chat = scrolledtext.ScrolledText(
            chat_card,
            height=12,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
        )
        self.assistant_chat.pack(fill="both", expand=True, pady=(6, 8))
        self.assistant_chat.configure(state="disabled")

        input_row = ttk.Frame(chat_card, style="Void.TFrame")
        input_row.pack(fill="x")
        input_entry = tk.Entry(
            input_row,
            textvariable=self.assistant_input_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        input_entry.bind("<Return>", lambda _event: self._send_gemini_message())
        ttk.Button(
            input_row,
            text="Send",
            style="Void.TButton",
            command=self._send_gemini_message,
        ).pack(side="left")
        ttk.Label(
            chat_card,
            textvariable=self.assistant_status_var,
            style="Void.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    def _build_settings_panel(self, panel: ttk.Frame) -> None:
        scrollable = self._make_scrollable(panel)
        
        ttk.Label(scrollable, text="Settings", style="Void.TLabel").pack(anchor="w")

        toggles = ttk.Frame(scrollable, style="Void.Card.TFrame")
        toggles.pack(fill="x", pady=(6, 12))
        toggles.configure(padding=12)
        ttk.Label(toggles, text="Feature Toggles", style="Void.TLabel").pack(anchor="w")

        ttk.Checkbutton(
            toggles,
            text="Enable backups",
            variable=self.enable_backups_var,
            style="Void.TCheckbutton",
        ).pack(anchor="w", pady=(6, 0))
        ttk.Checkbutton(
            toggles,
            text="Enable reports",
            variable=self.enable_reports_var,
            style="Void.TCheckbutton",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Checkbutton(
            toggles,
            text="Enable analytics",
            variable=self.enable_analytics_var,
            style="Void.TCheckbutton",
        ).pack(anchor="w", pady=(4, 0))

        export_card = ttk.Frame(scrollable, style="Void.Card.TFrame")
        export_card.pack(fill="x", pady=(0, 12))
        export_card.configure(padding=12)
        ttk.Label(export_card, text="Export Directories", style="Void.TLabel").pack(anchor="w")

        exports_row = ttk.Frame(export_card, style="Void.TFrame")
        exports_row.pack(fill="x", pady=(6, 0))
        ttk.Label(exports_row, text="Exports folder", style="Void.TLabel").pack(side="left")
        exports_entry = tk.Entry(
            exports_row,
            textvariable=self.exports_dir_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        exports_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            exports_row,
            text="Browse",
            style="Void.TButton",
            command=self._browse_exports_dir,
        ).pack(side="left")

        reports_row = ttk.Frame(export_card, style="Void.TFrame")
        reports_row.pack(fill="x", pady=(6, 0))
        ttk.Label(reports_row, text="Reports folder", style="Void.TLabel").pack(side="left")
        reports_entry = tk.Entry(
            reports_row,
            textvariable=self.reports_dir_var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            insertbackground=self.theme["accent"],
            relief="flat",
            font=("Consolas", 10),
        )
        reports_entry.pack(side="left", fill="x", expand=True, padx=(8, 6))
        ttk.Button(
            reports_row,
            text="Browse",
            style="Void.TButton",
            command=self._browse_reports_dir,
        ).pack(side="left")

        actions = ttk.Frame(scrollable, style="Void.TFrame")
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="Save Settings",
            style="Void.TButton",
            command=self._save_settings,
        ).pack(side="left")
        ttk.Label(
            actions,
            text="Settings apply immediately to GUI actions.",
            style="Void.TLabel",
        ).pack(side="left", padx=(12, 0))

    def _scroll_tabs(self, direction: int) -> None:
        if not self.notebook:
            return
        tabs = self.notebook.tabs()
        if not tabs:
            return
        current = self.notebook.select()
        try:
            index = tabs.index(current)
        except ValueError:
            index = 0
        next_index = min(max(index + direction, 0), len(tabs) - 1)
        if next_index == index:
            return
        target = tabs[next_index]
        self.notebook.select(target)
        self.notebook.see(target)

    def _on_tab_wheel(self, event) -> str:
        if event.num == 4:
            self._scroll_tabs(-1)
        elif event.num == 5:
            self._scroll_tabs(1)
        elif event.delta:
            direction = -1 if event.delta > 0 else 1
            self._scroll_tabs(direction)
        return "break"

    def _on_tab_change(self, _event=None) -> None:
        if not self.notebook or not self.assistant_panel:
            return
        selected = self.notebook.nametowidget(self.notebook.select())
        if selected == self.assistant_panel:
            self._ensure_gemini_api_key()

    def _open_assistant_panel(self) -> None:
        if not self.notebook or not self.assistant_panel:
            return
        self.notebook.select(self.assistant_panel)
        self._ensure_gemini_api_key()

    def _ensure_gemini_api_key(self) -> None:
        if self.gemini_api_key:
            return
        self._prompt_gemini_api_key()

    def _prompt_gemini_api_key(self) -> None:
        try:
            from tkinter import simpledialog
        except ImportError:
            messagebox.showwarning("Void", "Tkinter simpledialog is not available.")
            return
        key = simpledialog.askstring(
            "Gemini API Key",
            "Enter your Gemini API key:",
            parent=self.root,
            show="*",
        )
        if not key:
            return
        self.gemini_api_key = key.strip()
        self._app_config["gemini_api_key"] = self.gemini_api_key
        self._save_app_config(self._app_config)
        self.assistant_status_var.set("Gemini API key saved.")

    def _save_gemini_model(self) -> None:
        model = self.gemini_model_var.get().strip() or Config.GEMINI_MODEL
        self.gemini_model_var.set(model)
        self._app_config["gemini_model"] = model
        self._save_app_config(self._app_config)
        self.assistant_status_var.set(f"Gemini model saved: {model}")

    def _save_gemini_api_base(self) -> None:
        api_base = self.gemini_api_base_var.get().strip() or Config.GEMINI_API_BASE
        self.gemini_api_base_var.set(api_base)
        self._app_config["gemini_api_base"] = api_base
        self._save_app_config(self._app_config)
        self.assistant_status_var.set(f"Gemini API base saved: {api_base}")

    def _save_gemini_advanced(self) -> None:
        system_instruction = self.gemini_system_text.get("1.0", tk.END).strip()
        generation_config = self.gemini_generation_text.get("1.0", tk.END).strip()
        extra_payload = self.gemini_payload_text.get("1.0", tk.END).strip()

        parsed_generation = self._parse_gemini_json(
            generation_config, "Generation Config"
        )
        parsed_payload = self._parse_gemini_json(extra_payload, "Extra Payload")
        if parsed_generation is None or parsed_payload is None:
            return

        self.gemini_system_instruction = system_instruction
        self.gemini_generation_config = generation_config
        self.gemini_extra_payload = extra_payload
        self._app_config["gemini_system_instruction"] = system_instruction
        self._app_config["gemini_generation_config"] = generation_config
        self._app_config["gemini_extra_payload"] = extra_payload
        self._save_app_config(self._app_config)
        self.assistant_status_var.set("Gemini advanced settings saved.")

    def _parse_gemini_json(self, raw_value: str, label: str) -> Dict[str, Any] | None:
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            messagebox.showwarning("Void", f"{label} JSON is invalid: {exc}")
            return None
        if not isinstance(parsed, dict):
            messagebox.showwarning("Void", f"{label} must be a JSON object.")
            return None
        return parsed

    def _clear_assistant_tasks(self) -> None:
        self.assistant_tasks = []
        self.assistant_history = []
        if self.assistant_task_list:
            self.assistant_task_list.delete(0, tk.END)
        self.assistant_status_var.set("Task list cleared.")

    def _append_assistant_chat(self, speaker: str, message: str) -> None:
        if not self.assistant_chat:
            return
        self.assistant_chat.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        self.assistant_chat.insert(tk.END, f"[{timestamp}] {speaker}: {message}\n\n")
        self.assistant_chat.configure(state="disabled")
        self.assistant_chat.see(tk.END)

    def _update_assistant_tasks(self, tasks: List[Dict[str, str]]) -> None:
        self.assistant_tasks = tasks
        if not self.assistant_task_list:
            return
        self.assistant_task_list.delete(0, tk.END)
        for task in tasks:
            title = task.get("title", "Untitled")
            status = task.get("status", "todo")
            icon = {"todo": "⬜", "in_progress": "🔄", "done": "✅"}.get(status, "⬜")
            self.assistant_task_list.insert(tk.END, f"{icon} {title}")

    def _send_gemini_message(self) -> None:
        prompt = self.assistant_input_var.get().strip()
        if not prompt:
            messagebox.showwarning("Void", "Enter a message for the assistant.")
            return
        if not self.gemini_api_key:
            self._prompt_gemini_api_key()
            if not self.gemini_api_key:
                return
        generation_config = self._parse_gemini_json(
            self.gemini_generation_text.get("1.0", tk.END).strip(),
            "Generation Config",
        )
        extra_payload = self._parse_gemini_json(
            self.gemini_payload_text.get("1.0", tk.END).strip(),
            "Extra Payload",
        )
        if generation_config is None or extra_payload is None:
            return
        system_instruction = self.gemini_system_text.get("1.0", tk.END).strip()

        self.assistant_input_var.set("")
        self._append_assistant_chat("You", prompt)
        self._append_assistant_history("user", prompt)
        self.assistant_status_var.set("Contacting Gemini...")

        def runner() -> None:
            model = self.gemini_model_var.get().strip() or Config.GEMINI_MODEL
            api_base = self.gemini_api_base_var.get().strip() or Config.GEMINI_API_BASE
            agent = GeminiAgent(
                self.gemini_api_key,
                model=model,
                api_base=api_base,
                system_instruction=system_instruction or None,
                extra_payload=extra_payload,
                generation_config=generation_config,
            )
            result = agent.generate(
                prompt,
                self.assistant_tasks,
                history=self.assistant_history,
            )
            self.root.after(0, lambda: self._handle_gemini_result(result))

        threading.Thread(target=runner, daemon=True).start()

    def _handle_gemini_result(self, result) -> None:
        if not result.success:
            self.assistant_status_var.set(result.message)
            self._append_assistant_chat("Gemini", result.message)
            return
        if result.response:
            self._append_assistant_chat("Gemini", result.response)
            self._append_assistant_history("model", result.response)
        if result.tasks:
            self._update_assistant_tasks(result.tasks)
            self.assistant_status_var.set("Tasks updated.")
        else:
            self.assistant_status_var.set("Gemini responded without task updates.")
        structured = {}
        if isinstance(result.raw, dict):
            structured = result.raw.get("structured") or {}
        if isinstance(structured, dict):
            actions = structured.get("browser_actions") or []
            if structured.get("browser_action"):
                actions = [structured.get("browser_action")]
            if isinstance(actions, dict):
                actions = [actions]
            if actions:
                for action in actions:
                    if isinstance(action, dict):
                        self._dispatch_browser_command(action, source="Gemini")

    def _append_assistant_history(self, role: str, message: str) -> None:
        message = (message or "").strip()
        if not message:
            return
        self.assistant_history.append({"role": role, "parts": [{"text": message}]})

    def _browse_open_path(self, target: tk.StringVar) -> None:
        path = filedialog.askopenfilename()
        if path:
            target.set(path)

    def _log_browser(self, message: str) -> None:
        if not self.browser_log:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.browser_log.configure(state="normal")
        self.browser_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.browser_log.configure(state="disabled")
        self.browser_log.see(tk.END)

    def _confirm_browser_action(self, action: str, detail: str, source: str) -> bool:
        if not self.browser_confirm_var.get():
            return True
        prompt = (
            f"{source} requested to {action}.\n"
            f"Details: {detail}\n\n"
            "Proceed with this automated browser action?"
        )
        return messagebox.askyesno("Confirm Browser Action", prompt)

    def _ensure_browser(self) -> bool:
        if self.browser and self.browser.is_active:
            return True
        try:
            if not self.browser:
                self.browser = BrowserAutomation(headless=False)
            self.browser.launch()
        except RuntimeError as exc:
            messagebox.showwarning("Void", str(exc))
            self.browser_status_var.set("Browser unavailable.")
            return False
        except Exception as exc:
            messagebox.showwarning("Void", f"Unable to launch browser: {exc}")
            self.browser_status_var.set("Browser launch failed.")
            return False
        self.browser_status_var.set("Browser launched.")
        self._log_browser("Browser launched in headed mode.")
        return True

    def _launch_browser(self) -> None:
        if self._ensure_browser():
            self.browser_status_var.set("Browser ready.")

    def _close_browser(self) -> None:
        if not self.browser:
            self.browser_status_var.set("Browser not running.")
            return
        self.browser.close()
        self.browser_status_var.set("Browser closed.")
        self._log_browser("Browser session closed.")

    def _browser_open(self, url: Optional[str] = None, source: str = "User") -> None:
        target_url = (url or self.browser_url_var.get()).strip()
        if not target_url:
            messagebox.showwarning("Void", "Enter a URL to open.")
            return
        if not self._ensure_browser():
            return
        if not self._confirm_browser_action("open a URL", target_url, source):
            self._log_browser(f"{source} canceled navigation to {target_url}.")
            return
        self.browser.open(target_url)
        self.browser_status_var.set(f"Opened {target_url}")
        self._log_browser(f"Opened URL: {target_url}")

    def _browser_click(
        self,
        x_value: Optional[int] = None,
        y_value: Optional[int] = None,
        source: str = "User",
    ) -> None:
        if not self._ensure_browser():
            return
        try:
            x = int(x_value) if x_value is not None else int(self.browser_x_var.get().strip())
            y = int(y_value) if y_value is not None else int(self.browser_y_var.get().strip())
        except ValueError:
            messagebox.showwarning("Void", "Enter numeric X/Y coordinates for click.")
            return
        detail = f"x={x}, y={y}"
        if not self._confirm_browser_action("click", detail, source):
            self._log_browser(f"{source} canceled click at {detail}.")
            return
        self.browser.click(x, y)
        self.browser_status_var.set(f"Clicked at {x}, {y}")
        self._log_browser(f"Clicked at {x}, {y}")

    def _browser_type(self, text: Optional[str] = None, source: str = "User") -> None:
        if not self._ensure_browser():
            return
        payload = text if text is not None else self.browser_text_var.get()
        payload = payload or ""
        if not payload.strip():
            messagebox.showwarning("Void", "Enter text to type.")
            return
        detail = payload if len(payload) < 120 else f"{payload[:120]}..."
        if not self._confirm_browser_action("type text", detail, source):
            self._log_browser(f"{source} canceled typing.")
            return
        self.browser.type(payload)
        self.browser_status_var.set("Typed text into page.")
        self._log_browser(f"Typed text ({len(payload)} chars).")

    def _browser_screenshot(self, path: Optional[str] = None) -> None:
        if not self._ensure_browser():
            return
        if path is None:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG image", "*.png")],
            )
        if not path:
            return
        saved_path = self.browser.screenshot(path)
        self.browser_status_var.set(f"Screenshot saved: {saved_path}")
        self._log_browser(f"Saved screenshot to {saved_path}")

    def _dispatch_browser_command(
        self,
        command: Dict[str, Any],
        source: str = "Gemini",
    ) -> Dict[str, Any]:
        action = str(command.get("action") or command.get("command") or "").strip().lower()
        if action in {"open", "navigate"}:
            url = str(command.get("url") or command.get("target") or "").strip()
            self._browser_open(url=url, source=source)
            return {"success": True, "action": "open", "url": url}
        if action == "click":
            x = command.get("x")
            y = command.get("y")
            self._browser_click(x_value=x, y_value=y, source=source)
            return {"success": True, "action": "click", "x": x, "y": y}
        if action == "type":
            text = str(command.get("text") or "")
            self._browser_type(text=text, source=source)
            return {"success": True, "action": "type"}
        if action == "screenshot":
            path = command.get("path")
            self._browser_screenshot(path=path)
            return {"success": True, "action": "screenshot", "path": path}
        if action == "launch":
            self._launch_browser()
            return {"success": True, "action": "launch"}
        if action == "close":
            self._close_browser()
            return {"success": True, "action": "close"}
        self._log_browser(f"Unknown browser command: {command}")
        return {"success": False, "error": "Unknown action", "action": action}

    def _browse_save_path(self, target: tk.StringVar) -> None:
        path = filedialog.asksaveasfilename()
        if path:
            target.set(path)

    def _list_apps(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        filter_type = self.apps_filter_var.get().strip().lower() or "all"

        def runner() -> Dict[str, Any]:
            apps = AppManager.list_apps(device_id, filter_type)
            self._log(f"Apps ({filter_type}) found: {len(apps)}")
            for app in apps[:20]:
                self._log(f"• {app.get('package', 'unknown')}", level="DATA")
            if len(apps) > 20:
                self._log(f"... and {len(apps) - 20} more apps.", level="DATA")
            return {"success": True, "message": f"{len(apps)} apps listed."}

        self._run_task("Apps list", runner)

    def _run_app_action(self, label: str, action: Callable[[str, str], bool]) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        package = self.apps_package_var.get().strip()
        if not package:
            messagebox.showwarning("Void", "Enter a package name first.")
            return

        def runner() -> Dict[str, Any]:
            success = action(device_id, package)
            message = f"{label} {'succeeded' if success else 'failed'} for {package}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task(label, runner)

    def _backup_app(self) -> None:
        if not Config.ENABLE_AUTO_BACKUP:
            messagebox.showwarning("Backups Disabled", "Enable backups in Settings to use this feature.")
            self.status_var.set("Backup disabled in settings.")
            return
        device_id = self._get_selected_device()
        if not device_id:
            return
        package = self.apps_package_var.get().strip()
        if not package:
            messagebox.showwarning("Void", "Enter a package name first.")
            return

        def runner() -> Dict[str, Any]:
            result = AppManager.backup_app(device_id, package)
            if result.get("success"):
                self._log(f"APK backup created: {result.get('path')}")
                message = f"Backup saved: {result.get('path')}"
            else:
                message = "Backup failed."
            return {
                "success": bool(result.get("success")),
                "message": message,
            }

        self._run_task("Backup APK", runner)

    def _view_app_info(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        package = self.apps_package_var.get().strip()
        if not package:
            messagebox.showwarning("Void", "Enter a package name first.")
            return

        def runner() -> Dict[str, Any]:
            info = AppManager.get_app_info_detailed(device_id, package)
            self._log(f"App Info for {package}:")
            for key, value in info.items():
                if key != 'permissions':
                    self._log(f"  {key}: {value}", level="DATA")
            if 'permissions' in info:
                self._log(f"  Permissions: {len(info['permissions'])} granted", level="DATA")
            return {"success": True, "message": "App info retrieved."}

        self._run_task("View App Info", runner)

    def _export_app_list(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            result = AppManager.export_app_list(device_id, format='csv')
            if result.get("success"):
                self._log(f"App list exported: {result.get('path')} ({result.get('count')} apps)")
                message = f"Exported {result.get('count')} apps to {result.get('path')}"
            else:
                message = "Export failed."
            return {"success": bool(result.get("success")), "message": message}

        self._run_task("Export App List", runner)

    def _install_apk(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        apk_path = filedialog.askopenfilename(
            title="Select APK File",
            filetypes=[("APK Files", "*.apk"), ("All Files", "*.*")]
        )
        if not apk_path:
            return

        def runner() -> Dict[str, Any]:
            success = AppManager.install_apk(device_id, apk_path)
            message = f"APK installation {'succeeded' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Install APK", runner)

    def _list_files(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        path = self.files_list_path_var.get().strip() or "/sdcard"

        def runner() -> Dict[str, Any]:
            files = FileManager.list_files(device_id, path)
            self._log(f"Files in {path}: {len(files)}")
            for file in files[:20]:
                self._log(
                    f"{file.get('permissions', '')} {file.get('size', '')} {file.get('date', '')} "
                    f"{file.get('name', '')}",
                    level="DATA",
                )
            if len(files) > 20:
                self._log(f"... and {len(files) - 20} more files.", level="DATA")
            return {"success": True, "message": f"{len(files)} files listed."}

        self._run_task("Files list", runner)

    def _pull_file(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        remote_path = self.files_pull_remote_var.get().strip()
        if not remote_path:
            messagebox.showwarning("Void", "Enter a remote path to pull.")
            return
        local_path = self.files_pull_local_var.get().strip()

        def runner() -> Dict[str, Any]:
            result = FileManager.pull_file(
                device_id,
                remote_path,
                Path(local_path) if local_path else None,
            )
            message = (
                f"Pulled file to {result.get('path')}" if result.get("success") else "Pull failed."
            )
            if result.get("path"):
                self._log(message)
            return {"success": bool(result.get("success")), "message": message}

        self._run_task("Pull file", runner)

    def _push_file(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        local_path = self.files_push_local_var.get().strip()
        remote_path = self.files_push_remote_var.get().strip()
        if not local_path or not remote_path:
            messagebox.showwarning("Void", "Enter both local and remote paths.")
            return

        def runner() -> Dict[str, Any]:
            success = FileManager.push_file(device_id, Path(local_path), remote_path)
            message = "File pushed successfully." if success else "Push failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Push file", runner)

    def _delete_file(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        remote_path = self.files_delete_remote_var.get().strip()
        if not remote_path:
            messagebox.showwarning("Void", "Enter a remote path to delete.")
            return

        def runner() -> Dict[str, Any]:
            success = FileManager.delete_file(device_id, remote_path)
            message = "File deleted successfully." if success else "Delete failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Delete file", runner)

    def _create_folder(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        path = self.files_mkdir_var.get().strip()
        if not path:
            messagebox.showwarning("Void", "Enter a folder path to create.")
            return

        def runner() -> Dict[str, Any]:
            success = FileManager.create_folder(device_id, path)
            message = f"Folder created: {path}" if success else "Create folder failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Create folder", runner)

    def _rename_file(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        old_path = self.files_rename_old_var.get().strip()
        new_path = self.files_rename_new_var.get().strip()
        if not old_path or not new_path:
            messagebox.showwarning("Void", "Enter both old and new paths.")
            return

        def runner() -> Dict[str, Any]:
            success = FileManager.rename_file(device_id, old_path, new_path)
            message = f"Renamed {old_path} to {new_path}" if success else "Rename failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Rename file", runner)

    def _copy_file(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        src = self.files_copy_src_var.get().strip()
        dst = self.files_copy_dst_var.get().strip()
        if not src or not dst:
            messagebox.showwarning("Void", "Enter both source and destination paths.")
            return

        def runner() -> Dict[str, Any]:
            success = FileManager.copy_file(device_id, src, dst)
            message = f"Copied {src} to {dst}" if success else "Copy failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Copy file", runner)

    def _recover_contacts(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            result = DataRecovery.recover_contacts(device_id)
            if result.get("success"):
                self._log(f"Recovered {result.get('count', 0)} contacts.")
                self._log(f"Saved to: {result.get('json_path')}")
            return {
                "success": bool(result.get("success")),
                "message": (
                    f"Recovered {result.get('count', 0)} contacts."
                    if result.get("success")
                    else "Contacts recovery failed."
                ),
            }

        self._run_task("Recover contacts", runner)

    def _recover_sms(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            result = DataRecovery.recover_sms(device_id)
            if result.get("success"):
                self._log(f"Recovered {result.get('count', 0)} SMS messages.")
                self._log(f"Saved to: {result.get('path')}")
            return {
                "success": bool(result.get("success")),
                "message": (
                    f"Recovered {result.get('count', 0)} SMS messages."
                    if result.get("success")
                    else "SMS recovery failed."
                ),
            }

        self._run_task("Recover SMS", runner)

    def _run_frp_method(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        method_name = self.frp_method_var.get().strip()
        if not method_name:
            messagebox.showwarning("Void", "Select an FRP method first.")
            return
        method = self.frp_engine.methods.get(method_name)
        if not method:
            messagebox.showwarning("Void", "Invalid FRP method selection.")
            return

        def runner() -> Dict[str, Any]:
            result = method(device_id)
            message = result.get("message") or "FRP method complete."
            self._log(f"{method_name}: {message}")
            return {
                "success": bool(result.get("success")),
                "message": message,
            }

        self._run_task(f"FRP {method_name}", runner)

    def _list_partitions(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            result = list_partitions(device_id)
            if result.get("success") and result.get("partitions"):
                self._log(f"Found {len(result['partitions'])} partitions:")
                for p in result["partitions"]:
                    self._log(f"  {p.get('name', 'unknown')}: {p.get('size', 'unknown')} ({p.get('filesystem', 'unknown')})")
            return result

        self._run_task("List partitions", runner)

    def _view_partition_table(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import read_partition_table
            result = read_partition_table(device_id)
            if result.success and result.data:
                self._log("Partition table:")
                for line in str(result.data).split('\n'):
                    self._log(f"  {line}")
            return {"success": result.success, "message": result.message}

        self._run_task("Read partition table", runner)

    def _backup_partition(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        partition_name = self.partition_name_var.get().strip()
        if not partition_name:
            messagebox.showwarning("Void", "Enter a partition name (e.g., 'boot', 'recovery').")
            return

        def runner() -> Dict[str, Any]:
            result = backup_partition(device_id, partition_name)
            if result.get("success"):
                self._log(f"Partition backup saved to: {result.get('path')}")
            return result

        self._run_task(f"Backup {partition_name} partition", runner)

    def _wipe_partition(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        partition_name = self.partition_name_var.get().strip()
        if not partition_name:
            messagebox.showwarning("Void", "Enter a partition name to wipe.")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Partition Wipe",
            f"⚠️ WARNING: This will PERMANENTLY ERASE the '{partition_name}' partition!\n\n"
            f"This action CANNOT be undone. Are you absolutely sure?",
            icon="warning"
        )
        if not confirm:
            return

        def runner() -> Dict[str, Any]:
            result = wipe_partition(device_id, partition_name)
            return result

        self._run_task(f"Wipe {partition_name} partition", runner)

    def _verify_root(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import verify_root
            result = verify_root(device_id)
            if result.success:
                self._log("✅ Root access verified!")
                if result.data:
                    self._log(f"  Details: {result.data}")
            else:
                self._log("❌ No root access detected")
            return {"success": result.success, "message": result.message}

        self._run_task("Verify root", runner)

    def _run_safety_check(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import safety_check
            result = safety_check(device_id)
            if result.success and result.data:
                self._log("Safety checklist:")
                for check in result.data.get('checks', []):
                    status = "✅" if check.get('passed') else "❌"
                    self._log(f"  {status} {check.get('name')}: {check.get('message')}")
            return {"success": result.success, "message": result.message}

        self._run_task("Safety check", runner)

    def _extract_boot_image(self) -> None:
        from tkinter import filedialog
        boot_img_path = filedialog.askopenfilename(
            title="Select Boot Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not boot_img_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import extract_boot_image
            result = extract_boot_image(boot_img_path)
            if result.success:
                self._log(f"Boot image extracted successfully")
                if result.data:
                    self._log(f"  Output: {result.data}")
            return {"success": result.success, "message": result.message}

        self._run_task("Extract boot image", runner)

    def _stage_magisk_patch(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        from tkinter import filedialog
        boot_img_path = filedialog.askopenfilename(
            title="Select Boot Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not boot_img_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import stage_magisk_patch
            result = stage_magisk_patch(device_id, boot_img_path)
            if result.success:
                self._log("Boot image staged for Magisk patching")
                self._log("Next: Open Magisk Manager on device and patch the boot image")
            return {"success": result.success, "message": result.message}

        self._run_task("Stage Magisk patch", runner)

    def _pull_magisk_image(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import pull_magisk_patched
            result = pull_magisk_patched(device_id)
            if result.success and result.data:
                self._log(f"Pulled Magisk patched image to: {result.data}")
            return {"success": result.success, "message": result.message}

        self._run_task("Pull Magisk image", runner)

    def _verify_twrp(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        from tkinter import filedialog
        twrp_img_path = filedialog.askopenfilename(
            title="Select TWRP Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not twrp_img_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import verify_twrp_image
            result = verify_twrp_image(device_id, twrp_img_path)
            if result.success:
                self._log("✅ TWRP image verified successfully")
            return {"success": result.success, "message": result.message}

        self._run_task("Verify TWRP", runner)

    def _flash_twrp(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        from tkinter import filedialog
        twrp_img_path = filedialog.askopenfilename(
            title="Select TWRP Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not twrp_img_path:
            return

        confirm = messagebox.askyesno(
            "Confirm TWRP Flash",
            "This will permanently flash TWRP to the recovery partition.\n\nContinue?",
            icon="question"
        )
        if not confirm:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import flash_recovery
            result = flash_recovery(device_id, twrp_img_path, mode="flash")
            return {"success": result.success, "message": result.message}

        self._run_task("Flash TWRP", runner)

    def _boot_twrp(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        from tkinter import filedialog
        twrp_img_path = filedialog.askopenfilename(
            title="Select TWRP Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not twrp_img_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import flash_recovery
            result = flash_recovery(device_id, twrp_img_path, mode="boot")
            if result.success:
                self._log("Device will boot into TWRP temporarily")
            return {"success": result.success, "message": result.message}

        self._run_task("Boot TWRP", runner)

    def _rollback_flash(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        partition_name = self.partition_name_var.get().strip()
        if not partition_name:
            messagebox.showwarning("Void", "Enter a partition name to rollback (e.g., 'boot').")
            return
        from tkinter import filedialog
        backup_img_path = filedialog.askopenfilename(
            title="Select Backup Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not backup_img_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import rollback_flash
            result = rollback_flash(device_id, partition_name, backup_img_path)
            return {"success": result.success, "message": result.message}

        self._run_task(f"Rollback {partition_name}", runner)

    def _apply_tweak(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        tweak_type = self.tweak_type_var.get().strip().lower()
        value = self.tweak_value_var.get().strip()
        if not value:
            messagebox.showwarning("Void", "Enter a value for the tweak.")
            return

        def runner() -> Dict[str, Any]:
            success = False
            if tweak_type == "dpi":
                success = SystemTweaker.set_dpi(device_id, int(value))
            elif tweak_type == "animation":
                success = SystemTweaker.set_animation_scale(device_id, float(value))
            elif tweak_type == "timeout":
                success = SystemTweaker.set_screen_timeout(device_id, int(value))
            else:
                return {"success": False, "message": "Unknown tweak type."}
            message = f"{tweak_type.title()} updated." if success else f"{tweak_type.title()} update failed."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("System tweak", runner)

    def _enable_usb_debugging(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        force = bool(self.usb_force_var.get())

        def runner() -> Dict[str, Any]:
            if force:
                result = SystemTweaker.force_usb_debugging(device_id)
            else:
                result = {
                    "steps": [
                        {
                            "step": "enable_developer_options",
                            "success": SystemTweaker.enable_developer_options(device_id),
                            "detail": None,
                        },
                        {
                            "step": "enable_usb_debugging_setting",
                            "success": SystemTweaker.enable_usb_debugging(device_id),
                            "detail": None,
                        },
                    ]
                }
                result["success"] = all(step["success"] for step in result["steps"])
            status = "forced" if force else "enabled"
            self._log(f"USB debugging {status}: {'success' if result['success'] else 'failed'}.")
            for step in result.get("steps", []):
                icon = "✅" if step.get("success") else "❌"
                detail = f" ({step['detail']})" if step.get("detail") else ""
                self._log(f"{icon} {step.get('step')}{detail}", level="DATA")
            if result.get("usb_config"):
                self._log(f"USB config: {result['usb_config']}", level="DATA")
            return {
                "success": bool(result.get("success")),
                "message": f"USB debugging {status}.",
            }

        self._run_task("USB debugging", runner)

    def _reboot_device(self, mode: str) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        if not messagebox.askyesno("Confirm Reboot", f"Reboot device to {mode}?"):
            return

        def runner() -> Dict[str, Any]:
            success = SystemTweaker.reboot(device_id, mode)
            message = f"Reboot to {mode} {'succeeded' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task(f"Reboot to {mode}", runner)

    def _shutdown_device(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        if not messagebox.askyesno("Confirm Shutdown", "Shutdown the device?"):
            return

        def runner() -> Dict[str, Any]:
            success = SystemTweaker.shutdown(device_id)
            message = f"Shutdown {'succeeded' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Shutdown device", runner)

    def _toggle_system_setting(self, setting: str, enable: bool) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            if setting == 'stay_awake':
                success = SystemTweaker.toggle_stay_awake(device_id, enable)
                setting_name = "Stay Awake"
            elif setting == 'battery_saver':
                success = SystemTweaker.toggle_battery_saver(device_id, enable)
                setting_name = "Battery Saver"
            else:
                success = False
                setting_name = setting

            state = "enabled" if enable else "disabled"
            message = f"{setting_name} {state} {'successfully' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task(f"Toggle {setting}", runner)

    def _enable_adb_tcpip(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            success = SystemTweaker.enable_adb_tcpip(device_id)
            if success:
                import time
                time.sleep(self.ADB_TCPIP_WAIT_SECONDS)  # Wait for service to start
                status = SystemTweaker.get_adb_tcpip_status(device_id)
                if status.get('ip'):
                    message = f"ADB over WiFi enabled. Connect with: adb connect {status['ip']}:5555"
                    self._log(message)
                else:
                    message = "ADB over WiFi enabled on port 5555."
                    self._log(message)
            else:
                message = "Failed to enable ADB over WiFi."
            return {"success": success, "message": message}

        self._run_task("Enable ADB over WiFi", runner)

    def _disable_adb_tcpip(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            success = SystemTweaker.disable_adb_tcpip(device_id)
            message = f"ADB over WiFi disabled {'successfully' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Disable ADB over WiFi", runner)

    def _check_adb_tcpip_status(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            status = SystemTweaker.get_adb_tcpip_status(device_id)
            if status.get('enabled'):
                message = f"ADB over WiFi: ENABLED on port {status.get('port')}"
                if status.get('ip'):
                    message += f"\nDevice IP: {status['ip']}"
                    message += f"\nConnect with: adb connect {status['ip']}:{status['port']}"
            else:
                message = "ADB over WiFi: DISABLED (using USB)"
            self._log(message)
            return {"success": True, "message": message}

        self._run_task("Check ADB WiFi status", runner)

    def _check_internet(self) -> None:
        def runner() -> Dict[str, Any]:
            online = NetworkTools.check_internet()
            message = f"Internet status: {'Online' if online else 'Offline'}."
            self._log(message)
            return {"success": True, "message": message}

        self._run_task("Network check", runner)

    def _toggle_network(self, network_type: str, enable: bool) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            if network_type == 'wifi':
                success = NetworkAnalyzer.toggle_wifi(device_id, enable)
                name = "WiFi"
            elif network_type == 'data':
                success = NetworkAnalyzer.toggle_mobile_data(device_id, enable)
                name = "Mobile Data"
            else:
                success = False
                name = network_type

            state = "enabled" if enable else "disabled"
            message = f"{name} {state} {'successfully' if success else 'failed'}."
            self._log(message)
            return {"success": success, "message": message}

        self._run_task(f"Toggle {network_type}", runner)

    def _show_network_info(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            info = NetworkAnalyzer.get_network_info(device_id)
            self._log("Network Information:")
            if info.get('ip'):
                self._log(f"  IP Address: {info['ip']}", level="DATA")
            if info.get('mac'):
                self._log(f"  MAC Address: {info['mac']}", level="DATA")
            if info.get('gateway'):
                self._log(f"  Gateway: {info['gateway']}", level="DATA")
            if not info:
                self._log("  No network information available", level="DATA")
            return {"success": True, "message": "Network info retrieved."}

        self._run_task("Network info", runner)

    def _list_wifi_networks(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            networks = NetworkAnalyzer.list_wifi_networks(device_id)
            self._log(f"Saved WiFi Networks ({len(networks)}):")
            for network in networks:
                self._log(f"  {network}", level="DATA")
            if not networks:
                self._log("  No saved networks found", level="DATA")
            return {"success": True, "message": f"{len(networks)} networks listed."}

        self._run_task("List WiFi networks", runner)

    def _start_logcat(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return
        if self._logcat_running:
            messagebox.showinfo("Void", "Logcat is already running.")
            return
        filter_tag = self.logcat_filter_var.get().strip() or None

        def runner() -> Dict[str, Any]:
            self.logcat_viewer.start(device_id, filter_tag, progress_callback=self._log)
            self._logcat_running = True
            self._logcat_thread = threading.Thread(target=self._stream_logcat, daemon=True)
            self._logcat_thread.start()
            return {"success": True, "message": "Logcat streaming started."}

        self._run_task("Logcat start", runner)

    def _stream_logcat(self) -> None:
        while self._logcat_running and self.logcat_viewer.running:
            line = self.logcat_viewer.read_line()
            if line:
                self._log(line.strip(), level="LOGCAT")

    def _stop_logcat(self) -> None:
        if not self._logcat_running:
            messagebox.showinfo("Void", "Logcat is not running.")
            return

        def runner() -> Dict[str, Any]:
            self._logcat_running = False
            self.logcat_viewer.stop(progress_callback=self._log)
            return {"success": True, "message": "Logcat stopped."}

        self._run_task("Logcat stop", runner)

    def _export_logcat(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Logcat",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not output_path:
            return

        def runner() -> Dict[str, Any]:
            success = LogcatViewer.export_logcat(device_id, output_path)
            message = f"Logcat exported to {output_path}" if success else "Export failed"
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Export Logcat", runner)

    def _clear_logcat(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            success = LogcatViewer.clear_logcat(device_id)
            message = "Logcat buffer cleared" if success else "Clear failed"
            self._log(message)
            return {"success": success, "message": message}

        self._run_task("Clear Logcat", runner)

    def _view_kernel_log(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            output = LogcatViewer.get_kernel_log(device_id)
            lines = output.strip().split('\n')
            self._log(f"Kernel Log ({len(lines)} lines):")
            for line in lines[-50:]:  # Show last 50 lines
                self._log(line, level="DATA")
            return {"success": True, "message": "Kernel log retrieved"}

        self._run_task("Kernel Log", runner)

    def _view_crash_logs(self) -> None:
        device_id = self._get_selected_device()
        if not device_id:
            return

        def runner() -> Dict[str, Any]:
            logs = LogcatViewer.get_crash_logs(device_id)
            self._log(f"Crash Logs ({len(logs)} files):")
            for log in logs:
                self._log(f"  {log}", level="DATA")
            if not logs:
                self._log("  No crash logs found", level="DATA")
            return {"success": True, "message": f"{len(logs)} crash logs found"}

        self._run_task("Crash Logs", runner)

    def _start_monitoring(self) -> None:
        if not Config.ENABLE_MONITORING:
            messagebox.showwarning("Monitoring Disabled", "Enable monitoring in configuration to use this feature.")
            self.status_var.set("Monitoring disabled in settings.")
            return

        def runner() -> Dict[str, Any]:
            monitor.start()
            self.monitor_status_var.set("Monitoring active.")
            return {"success": True, "message": "Monitoring started."}

        self._run_task("Monitoring start", runner)

    def _stop_monitoring(self) -> None:
        def runner() -> Dict[str, Any]:
            monitor.stop()
            self.monitor_status_var.set("Monitoring stopped.")
            return {"success": True, "message": "Monitoring stopped."}

        self._run_task("Monitoring stop", runner)

    def _snapshot_monitor(self) -> None:
        def runner() -> Dict[str, Any]:
            stats = monitor.get_stats()
            if not stats:
                return {"success": False, "message": "Monitoring not available."}
            self._log(
                f"CPU: {stats.get('cpu_percent', 0):.1f}% | "
                f"Memory: {stats.get('memory_percent', 0):.1f}% | "
                f"Disk: {stats.get('disk_usage', 0):.1f}%"
            )
            return {"success": True, "message": "Monitoring snapshot captured."}

        self._run_task("Monitoring snapshot", runner)

    def _edl_flash(self) -> None:
        context = self._get_device_context()
        if context is None:
            return
        loader = self.edl_loader_var.get().strip()
        image = self.edl_image_var.get().strip()
        if not loader or not image:
            messagebox.showwarning("Void", "Select both loader and image paths.")
            return
        if not Path(loader).exists():
            messagebox.showwarning("Void", f"Loader not found: {loader}")
            return
        if not Path(image).exists():
            messagebox.showwarning("Void", f"Image not found: {image}")
            return

        def runner() -> ChipsetActionResult:
            result = edl_flash(context, loader, image)
            if result.data.get("command"):
                self._log(f"Command: {result.data['command']}", level="DATA")
            return result

        self._run_task("EDL flash", runner)

    def _edl_dump(self) -> None:
        context = self._get_device_context()
        if context is None:
            return
        partition = self.edl_partition_var.get().strip()
        if not partition:
            messagebox.showwarning("Void", "Enter a partition name.")
            return

        def runner() -> ChipsetActionResult:
            result = edl_dump(context, partition)
            if result.data.get("output"):
                self._log(f"Output: {result.data['output']}", level="DATA")
            if result.data.get("command"):
                self._log(f"Command: {result.data['command']}", level="DATA")
            return result

        self._run_task("EDL dump", runner)

    def _edl_list_programmers(self) -> None:
        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import list_firehose_programmers
            result = list_firehose_programmers()
            if result.success and result.data:
                self._log("Available Firehose Programmers:")
                for prog in result.data.get('programmers', []):
                    self._log(f"  • {prog.get('chipset')}: {prog.get('file')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("List EDL programmers", runner)

    def _edl_detect_devices(self) -> None:
        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import detect_edl_devices
            result = detect_edl_devices()
            if result.success and result.data:
                self._log(f"Detected {len(result.data.get('devices', []))} EDL device(s):")
                for dev in result.data.get('devices', []):
                    self._log(f"  • {dev.get('usb_id')}: {dev.get('chipset', 'Unknown')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("Detect EDL devices", runner)

    def _edl_compat_matrix(self) -> None:
        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import compatibility_matrix
            result = compatibility_matrix()
            if result.success and result.data:
                self._log("EDL Compatibility Matrix:")
                for entry in result.data.get('matrix', []):
                    self._log(f"  {entry.get('chipset')}: {entry.get('tools', 'N/A')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("Show compatibility matrix", runner)

    def _edl_sparse_to_raw(self) -> None:
        from tkinter import filedialog
        source_path = filedialog.askopenfilename(
            title="Select Sparse Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not source_path:
            return
        
        dest_path = filedialog.asksaveasfilename(
            title="Save Raw Image As",
            defaultextension=".img",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not dest_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import convert_sparse_image
            result = convert_sparse_image("to-raw", source_path, dest_path)
            return {"success": result.success, "message": result.message}

        self._run_task("Convert sparse to raw", runner)

    def _edl_raw_to_sparse(self) -> None:
        from tkinter import filedialog
        source_path = filedialog.askopenfilename(
            title="Select Raw Image",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not source_path:
            return
        
        dest_path = filedialog.asksaveasfilename(
            title="Save Sparse Image As",
            defaultextension=".img",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not dest_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import convert_sparse_image
            result = convert_sparse_image("to-sparse", source_path, dest_path)
            return {"success": result.success, "message": result.message}

        self._run_task("Convert raw to sparse", runner)

    def _edl_verify_hash(self) -> None:
        from tkinter import filedialog
        image_path = filedialog.askopenfilename(
            title="Select Image to Verify",
            filetypes=[("Image Files", "*.img"), ("All Files", "*.*")]
        )
        if not image_path:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import verify_hash
            result = verify_hash(image_path)
            if result.success and result.data:
                self._log(f"SHA256: {result.data.get('hash')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("Verify image hash", runner)

    def _edl_unbrick_checklist(self) -> None:
        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import edl_unbrick_plan
            result = edl_unbrick_plan()
            if result.success and result.data:
                self._log("Unbrick Checklist:")
                for step in result.data.get('steps', []):
                    self._log(f"  {step.get('number')}. {step.get('description')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("Show unbrick checklist", runner)

    def _edl_device_notes(self) -> None:
        from tkinter import simpledialog
        vendor = simpledialog.askstring("Device Notes", "Enter vendor name (e.g., 'qualcomm', 'mediatek'):")
        if not vendor:
            return

        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import device_notes
            result = device_notes(vendor)
            if result.success and result.data:
                self._log(f"Device Notes for {vendor}:")
                self._log(result.data.get('notes', 'No notes available'), level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task(f"Device notes: {vendor}", runner)

    def _edl_capture_log(self) -> None:
        def runner() -> Dict[str, Any]:
            from .core.edl_toolkit import capture_edl_log
            result = capture_edl_log()
            if result.success and result.data:
                self._log(f"EDL log captured to: {result.data.get('path')}", level="DATA")
            return {"success": result.success, "message": result.message}

        self._run_task("Capture EDL log", runner)

    def _parse_limit(self, value: str, fallback: int = 10) -> int:
        try:
            return max(1, int(value))
        except ValueError:
            return fallback

    def _list_backups(self) -> None:
        limit = self._parse_limit(self.recent_items_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            items = sorted(Config.BACKUP_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            self._log(f"Recent backups ({min(limit, len(items))} shown):")
            for item in items[:limit]:
                size = item.stat().st_size if item.is_file() else 0
                label = "dir" if item.is_dir() else "file"
                self._log(f"{item.name} ({label}, {size:,} bytes)", level="DATA")
            return {"success": True, "message": f"Listed {min(limit, len(items))} backups."}

        self._run_task("List backups", runner)

    def _list_reports(self) -> None:
        if not Config.ENABLE_REPORTS:
            messagebox.showwarning("Reports Disabled", "Enable reports in Settings to use this feature.")
            self.status_var.set("Reports disabled in settings.")
            return
        limit = self._parse_limit(self.recent_items_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            items = sorted(Config.REPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            self._log(f"Recent reports ({min(limit, len(items))} shown):")
            for item in items[:limit]:
                size = item.stat().st_size if item.is_file() else 0
                label = "dir" if item.is_dir() else "file"
                self._log(f"{item.name} ({label}, {size:,} bytes)", level="DATA")
            return {"success": True, "message": f"Listed {min(limit, len(items))} reports."}

        self._run_task("List reports", runner)

    def _list_exports(self) -> None:
        limit = self._parse_limit(self.recent_items_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            items = sorted(Config.EXPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            self._log(f"Recent exports ({min(limit, len(items))} shown):")
            for item in items[:limit]:
                size = item.stat().st_size if item.is_file() else 0
                label = "dir" if item.is_dir() else "file"
                self._log(f"{item.name} ({label}, {size:,} bytes)", level="DATA")
            return {"success": True, "message": f"Listed {min(limit, len(items))} exports."}

        self._run_task("List exports", runner)

    def _export_devices_json(self) -> None:
        def runner() -> Dict[str, Any]:
            devices, _ = DeviceDetector.detect_all()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"devices_{timestamp}.json"
            export_path.write_text(json.dumps(devices, indent=2))
            self._log(f"Devices exported: {export_path}")
            return {"success": True, "message": f"Devices exported: {export_path}"}

        self._run_task("Export devices", runner)

    def _export_stats_json(self) -> None:
        def runner() -> Dict[str, Any]:
            stats = db.get_statistics()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"stats_{timestamp}.json"
            export_path.write_text(json.dumps(stats, indent=2))
            self._log(f"Stats exported: {export_path}")
            return {"success": True, "message": f"Stats exported: {export_path}"}

        self._run_task("Export stats", runner)

    def _export_logs_json(self) -> None:
        def runner() -> Dict[str, Any]:
            rows = db.get_recent_logs(limit=200)
            if not rows:
                return {"success": False, "message": "No log entries found."}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"logs_{timestamp}.json"
            export_path.write_text(json.dumps(rows, indent=2))
            self._log(f"Logs exported: {export_path}")
            return {"success": True, "message": f"Logs exported: {export_path}"}

        self._run_task("Export logs", runner)

    def _export_reports_json(self) -> None:
        if not Config.ENABLE_REPORTS:
            messagebox.showwarning("Reports Disabled", "Enable reports in Settings to use this feature.")
            self.status_var.set("Reports disabled in settings.")
            return

        def runner() -> Dict[str, Any]:
            rows = db.get_recent_reports(limit=200)
            if not rows:
                return {"success": False, "message": "No report records found."}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"reports_{timestamp}.json"
            export_path.write_text(json.dumps(rows, indent=2))
            self._log(f"Reports exported: {export_path}")
            return {"success": True, "message": f"Reports exported: {export_path}"}

        self._run_task("Export reports", runner)

    def _export_backups_json(self) -> None:
        def runner() -> Dict[str, Any]:
            rows = db.get_recent_backups(limit=200)
            if not rows:
                return {"success": False, "message": "No backup records found."}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"backups_{timestamp}.json"
            export_path.write_text(json.dumps(rows, indent=2))
            self._log(f"Backups exported: {export_path}")
            return {"success": True, "message": f"Backups exported: {export_path}"}

        self._run_task("Export backups", runner)

    def _open_reports_dir(self) -> None:
        def runner() -> Dict[str, Any]:
            target = str(Config.REPORTS_DIR)
            if platform.system() == "Darwin":
                SafeSubprocess.run(["open", target])
            elif platform.system() == "Windows":
                SafeSubprocess.run(["explorer", target])
            else:
                SafeSubprocess.run(["xdg-open", target])
            return {"success": True, "message": f"Opened: {target}"}

        self._run_task("Open reports", runner)

    def _open_exports_dir(self) -> None:
        def runner() -> Dict[str, Any]:
            target = str(Config.EXPORTS_DIR)
            if platform.system() == "Darwin":
                SafeSubprocess.run(["open", target])
            elif platform.system() == "Windows":
                SafeSubprocess.run(["explorer", target])
            else:
                SafeSubprocess.run(["xdg-open", target])
            return {"success": True, "message": f"Opened: {target}"}

        self._run_task("Open exports", runner)

    def _db_health(self) -> None:
        def runner() -> Dict[str, Any]:
            stats = db.get_statistics()
            db_size = Config.DB_PATH.stat().st_size if Config.DB_PATH.exists() else 0
            self._log(f"DB Path: {Config.DB_PATH}")
            self._log(f"DB Size: {db_size:,} bytes")
            self._log(f"Devices: {stats.get('total_devices', 0)}", level="DATA")
            self._log(f"Logs: {stats.get('total_logs', 0)}", level="DATA")
            self._log(f"Backups: {stats.get('total_backups', 0)}", level="DATA")
            self._log(f"Methods: {stats.get('total_methods', 0)}", level="DATA")
            self._log(f"Reports: {stats.get('total_reports', 0)}", level="DATA")
            return {"success": True, "message": "Database health summarized."}

        self._run_task("DB health", runner)

    def _show_recent_logs(self) -> None:
        limit = self._parse_limit(self.db_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            rows = db.get_recent_logs(limit=limit)
            if not rows:
                return {"success": False, "message": "No log entries found."}
            self._log(f"Recent logs ({len(rows)}):")
            for row in rows:
                timestamp = row.get("timestamp", "")
                level = row.get("level", "").upper()
                category = row.get("category", "")
                message = row.get("message", "")
                self._log(f"[{timestamp}] {level} {category}: {message}", level="DATA")
            return {"success": True, "message": f"Listed {len(rows)} log entries."}

        self._run_task("Recent logs", runner)

    def _show_recent_backups(self) -> None:
        limit = self._parse_limit(self.db_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            rows = db.get_recent_backups(limit=limit)
            if not rows:
                return {"success": False, "message": "No backup records found."}
            self._log(f"Recent backups ({len(rows)}):")
            for row in rows:
                name = row.get("backup_name", "Unknown")
                device_id = row.get("device_id", "Unknown")
                created = row.get("created", "")
                size = row.get("backup_size", 0)
                backup_type = row.get("backup_type", "Unknown")
                self._log(
                    f"{name} ({backup_type}) - {device_id} - {created} - {size:,} bytes",
                    level="DATA",
                )
            return {"success": True, "message": f"Listed {len(rows)} backup records."}

        self._run_task("Recent backups", runner)

    def _show_recent_reports(self) -> None:
        if not Config.ENABLE_REPORTS:
            messagebox.showwarning("Reports Disabled", "Enable reports in Settings to use this feature.")
            self.status_var.set("Reports disabled in settings.")
            return
        limit = self._parse_limit(self.db_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            rows = db.get_recent_reports(limit=limit)
            if not rows:
                return {"success": False, "message": "No report records found."}
            self._log(f"Recent reports ({len(rows)}):")
            for row in rows:
                timestamp = row.get("timestamp", "")
                device_id = row.get("device_id", "Unknown")
                event_data = row.get("event_data", "{}")
                try:
                    payload = json.loads(event_data)
                except json.JSONDecodeError:
                    payload = {}
                report_name = payload.get("report_name", "Unknown")
                self._log(f"{report_name} - {device_id} - {timestamp}", level="DATA")
            return {"success": True, "message": f"Listed {len(rows)} report records."}

        self._run_task("Recent reports", runner)

    def _show_recent_devices(self) -> None:
        limit = self._parse_limit(self.db_limit_var.get(), 10)

        def runner() -> Dict[str, Any]:
            rows = db.get_recent_devices(limit=limit)
            if not rows:
                return {"success": False, "message": "No device records found."}
            self._log(f"Recent devices ({len(rows)}):")
            for row in rows:
                device_id = row.get("id", "Unknown")
                manufacturer = row.get("manufacturer", "Unknown")
                model = row.get("model", "Unknown")
                android = row.get("android_version", "Unknown")
                last_seen = row.get("last_seen", "")
                count = row.get("connection_count", 0)
                self._log(
                    f"{device_id} - {manufacturer} {model} (Android {android}) "
                    f"- last seen {last_seen} ({count}x)",
                    level="DATA",
                )
            return {"success": True, "message": f"Listed {len(rows)} device records."}

        self._run_task("Recent devices", runner)

    def _show_top_methods(self) -> None:
        limit = self._parse_limit(self.db_limit_var.get(), 5)

        def runner() -> Dict[str, Any]:
            rows = db.get_top_methods(limit=limit)
            if not rows:
                return {"success": False, "message": "No method records found."}
            self._log(f"Top methods ({len(rows)}):")
            for row in rows:
                name = row.get("name", "Unknown")
                success = row.get("success_count", 0)
                total = row.get("total_count", 0)
                avg = row.get("avg_duration", 0)
                last_success = row.get("last_success", "")
                rate = (success / total * 100) if total else 0
                self._log(
                    f"{name}: {rate:.1f}% ({success}/{total}) avg {avg:.2f}s last {last_success}",
                    level="DATA",
                )
            return {"success": True, "message": f"Listed {len(rows)} methods."}

        self._run_task("Top methods", runner)

    def _export_filtered_logs(self) -> None:
        export_format = self.log_export_format_var.get().strip().lower()
        if export_format not in {"json", "csv"}:
            messagebox.showwarning("Void", "Select a valid export format (json/csv).")
            return
        try:
            limit = max(1, int(self.log_export_limit_var.get() or "500"))
        except ValueError:
            messagebox.showwarning("Void", "Limit must be a number.")
            return
        filters = {
            "level": self.log_export_level_var.get().strip() or None,
            "category": self.log_export_category_var.get().strip() or None,
            "device_id": self.log_export_device_var.get().strip() or None,
            "method": self.log_export_method_var.get().strip() or None,
            "since": self.log_export_since_var.get().strip() or None,
            "until": self.log_export_until_var.get().strip() or None,
            "limit": limit,
        }

        def runner() -> Dict[str, Any]:
            rows = db.get_filtered_logs(
                level=filters["level"],
                category=filters["category"],
                device_id=filters["device_id"],
                method=filters["method"],
                since=filters["since"],
                until=filters["until"],
                limit=filters["limit"],
            )
            if not rows:
                return {"success": False, "message": "No log entries found."}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = Config.EXPORTS_DIR / f"logs_filtered_{timestamp}.{export_format}"
            if export_format == "json":
                export_path.write_text(json.dumps(rows, indent=2))
            else:
                fieldnames = ["timestamp", "level", "category", "message", "device_id", "method"]
                with export_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            self._log(f"Logs exported: {export_path}")
            return {"success": True, "message": f"Logs exported: {export_path}"}

        self._run_task("Export logs", runner)

    def _browse_exports_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.exports_dir_var.get() or str(Config.EXPORTS_DIR))
        if path:
            self.exports_dir_var.set(path)

    def _browse_reports_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.reports_dir_var.get() or str(Config.REPORTS_DIR))
        if path:
            self.reports_dir_var.set(path)

    def _save_settings(self) -> None:
        settings = {
            "enable_auto_backup": bool(self.enable_backups_var.get()),
            "enable_reports": bool(self.enable_reports_var.get()),
            "enable_analytics": bool(self.enable_analytics_var.get()),
            "exports_dir": self.exports_dir_var.get().strip(),
            "reports_dir": self.reports_dir_var.get().strip(),
        }
        normalized = Config.save_settings(settings)
        self.exports_dir_var.set(normalized["exports_dir"])
        self.reports_dir_var.set(normalized["reports_dir"])
        self._sync_action_buttons()
        self.status_var.set("Settings saved.")

    def _sync_action_buttons(self) -> None:
        if self.backup_button is not None:
            state = "normal" if Config.ENABLE_AUTO_BACKUP else "disabled"
            self.backup_button.configure(state=state)
        if self.report_button is not None:
            state = "normal" if Config.ENABLE_REPORTS else "disabled"
            self.report_button.configure(state=state)
        if self.analyze_button is not None:
            state = "normal" if Config.ENABLE_ANALYTICS else "disabled"
            self.analyze_button.configure(state=state)

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
        self._update_edl_preflight()
        target_mode = self.target_mode_var.get()
        mode = context.get("mode", "unknown")
        if target_mode.lower() == "edl" and mode.lower() != "adb":
            proceed = messagebox.askyesno(
                "EDL Entry Warning",
                "The selected device is not currently in ADB mode. "
                "EDL entry may require a manual test-point trigger.\n\n"
                "Continue with the workflow?",
            )
            if not proceed:
                return
        proceed = messagebox.askyesno(
            "Confirm Mode Entry",
            f"Attempt to enter {target_mode.upper()} mode for the selected device?",
        )
        if not proceed:
            return
        override = self._get_chipset_override()
        authorization_token = ""
        ownership_verification = ""
        if mode.lower() == "adb" and target_mode.lower() in {
            "edl",
            "fastboot",
            "bootloader",
            "recovery",
            "download",
            "odin",
        }:
            authorization_token, ownership_verification = self._prompt_recovery_authorization()
        self._run_task(
            "Enter Mode",
            enter_device_mode,
            context,
            target_mode,
            override,
            authorization_token,
            ownership_verification,
        )

    def _prompt_recovery_authorization(self) -> tuple[str, str]:
        try:
            from tkinter import simpledialog
        except ImportError:
            messagebox.showwarning("Void", "Tkinter simpledialog is not available.")
            return "", ""
        token = simpledialog.askstring(
            "Authorization Token",
            "Enter the legal authorization token (leave blank to skip):",
            parent=self.root,
        )
        ownership = simpledialog.askstring(
            "Ownership Verification",
            "Enter the device ownership verification (leave blank to skip):",
            parent=self.root,
        )
        return (token or ""), (ownership or "")

    def _recover_chipset_device(self, label: str) -> None:
        context = self._get_device_context()
        if context is None:
            return
        self._update_edl_preflight()
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

    def _get_device_context(self, show_warning: bool = True) -> Optional[Dict[str, str]]:
        # In simple mode, use stored selected_device_id
        if not self.device_list:
            if not self.selected_device_id:
                if show_warning:
                    messagebox.showwarning("Void", "Select a device first.")
                return None
            info = next((d for d in self.device_info if d.get("id") == self.selected_device_id), None)
            if not info:
                if show_warning:
                    messagebox.showwarning("Void", "Device information not available.")
                return None
            return {k: str(v) for k, v in info.items() if v is not None}
            
        selection = self.device_list.curselection()
        if not selection or selection[0] >= len(self.device_info):
            if show_warning:
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

    def _is_failed_result(self, result: Any) -> bool:
        if isinstance(result, PluginResult):
            return not result.success
        if isinstance(result, ChipsetActionResult):
            return not result.success
        if isinstance(result, dict):
            return result.get("success") is False
        return False

    def _show_task_error(self, label: str, result: Any | None = None, exc: Exception | None = None) -> None:
        summary, detail, steps = self._build_failure_dialog(label, result=result, exc=exc)
        if steps:
            next_steps = "\n".join(f"• {step}" for step in steps)
            message = f"{summary}\n\nDetails: {detail}\n\nNext steps:\n{next_steps}"
        else:
            message = f"{summary}\n\nDetails: {detail}\n\nNext steps:\n• Review the Operations Log for details."

        self.root.after(0, lambda: messagebox.showerror("Void", message))

    def _build_failure_dialog(
        self,
        label: str,
        result: Any | None = None,
        exc: Exception | None = None,
    ) -> tuple[str, str, List[str]]:
        detail = self._extract_failure_detail(result, exc)
        summary = f"{label} failed."
        if detail:
            summary = f"{label} failed: {detail}"
        steps = self._failure_guidance(detail, result)
        return summary, detail or "Unknown error.", steps

    def _extract_failure_detail(self, result: Any | None, exc: Exception | None) -> str:
        if exc is not None:
            return str(exc) or exc.__class__.__name__
        if isinstance(result, PluginResult):
            return result.message or "Operation failed."
        if isinstance(result, ChipsetActionResult):
            return result.message or "Operation failed."
        if isinstance(result, dict):
            return (
                result.get("error")
                or result.get("message")
                or result.get("reason")
                or "Operation failed."
            )
        return "Operation failed."

    def _failure_guidance(self, detail: str, result: Any | None) -> List[str]:
        detail_lower = (detail or "").lower()
        if isinstance(result, ChipsetActionResult):
            manual_steps = result.data.get("manual_steps") if isinstance(result.data, dict) else None
            if manual_steps:
                if isinstance(manual_steps, str):
                    steps = [step.strip() for step in manual_steps.splitlines() if step.strip()]
                elif isinstance(manual_steps, (list, tuple)):
                    steps = [str(step) for step in manual_steps if str(step).strip()]
                else:
                    steps = [str(manual_steps)]
                return steps
        if "adb" in detail_lower and (
            "not found" in detail_lower
            or "no such file or directory" in detail_lower
            or "tool_missing" in detail_lower
        ):
            return [
                "Install Android platform-tools (adb) for your OS.",
                "Ensure adb is on your PATH, then restart Void.",
                "Run Refresh Devices and retry the action.",
            ]
        if "device offline" in detail_lower or "offline" in detail_lower:
            return [
                "Reconnect the USB cable and unlock the device.",
                "Confirm USB Debugging is enabled and accept the RSA prompt.",
                "Run 'adb kill-server' then 'adb start-server' and retry.",
            ]
        if "adb_not_authorized" in detail_lower or "manual_authorization_required" in detail_lower:
            return [
                "Unlock the device and accept the USB debugging authorization prompt.",
                "Revoke USB debugging authorizations on the device, reconnect, and retry.",
                "Run Refresh Devices after reauthorizing.",
            ]
        return [
            "Confirm the device is connected and in the expected mode.",
            "Review the Operations Log for the full error details.",
            "Retry after addressing the issue.",
        ]

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
        if not self.output:
            messagebox.showwarning("Void", "The log is not available yet.")
            return
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
    
    def _toggle_mode(self) -> None:
        """Toggle between Simple and Advanced modes."""
        self.is_advanced_mode.set(not self.is_advanced_mode.get())
        
        # Save preference
        self._app_config["advanced_mode"] = self.is_advanced_mode.get()
        self._save_app_config(self._app_config)
        
        # Update button text
        if self.mode_toggle_button:
            if self.is_advanced_mode.get():
                self.mode_toggle_button.configure(text="🎯 Simple")
            else:
                self.mode_toggle_button.configure(text="⚙ Advanced")
        
        # Switch views with animation
        self._switch_view()
        
    def _switch_view(self) -> None:
        """Switch between simple and advanced view containers."""
        if not self.simple_view_container or not self.advanced_view_container:
            return
        
        # Hide both first
        self.simple_view_container.pack_forget()
        self.advanced_view_container.pack_forget()
        
        # Show the appropriate one
        if self.is_advanced_mode.get():
            self.advanced_view_container.pack(fill="both", expand=True)
            if self.mode_toggle_button:
                self.mode_toggle_button.configure(text="🎯 Simple")
        else:
            self.simple_view_container.pack(fill="both", expand=True)
            if self.mode_toggle_button:
                self.mode_toggle_button.configure(text="⚙ Advanced")
        
        # Refresh device info in simple mode
        if not self.is_advanced_mode.get():
            self.root.after(100, self._update_simple_device_info)
    
    def _switch_to_advanced_tab(self, main_tab_index: int, sub_tab_index: Optional[int] = None) -> None:
        """Switch to advanced mode and navigate to a specific tab."""
        # Switch to advanced mode if not already there
        if not self.is_advanced_mode.get():
            self.is_advanced_mode.set(True)
            self._switch_view()
        
        # Navigate to the specified tab
        if self.notebook and main_tab_index < len(self.notebook.tabs()):
            self.notebook.select(main_tab_index)
            
            # If sub-tab index is provided, navigate to it
            if sub_tab_index is not None:
                # Get the current tab widget
                current_tab = self.notebook.nametowidget(self.notebook.select())
                # Find notebooks within the tab
                for child in current_tab.winfo_children():
                    if isinstance(child, ttk.Notebook) and sub_tab_index < len(child.tabs()):
                        child.select(sub_tab_index)
                        break
    
    def _update_simple_device_info(self) -> None:
        """Update device info display in simple mode."""
        if self.selected_device_id:
            info = next((d for d in self.device_info if d.get("id") == self.selected_device_id), None)
            if info:
                device_str = f"{info.get('manufacturer', 'Unknown')} {info.get('model', 'Unknown')} ({info.get('id', 'N/A')})"
                self.selected_device_var.set(device_str)
            else:
                self.selected_device_var.set("No device selected - Click 'Refresh Devices'")
        else:
            self.selected_device_var.set("No device selected - Click 'Refresh Devices'")


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
