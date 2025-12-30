"""
Help System - Context-sensitive help and tooltips for Void Suite

Provides comprehensive "What it does" descriptions and "How to" guides for every feature.

PROPRIETARY SOFTWARE
Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Unauthorized copying, modification, distribution, or disclosure is prohibited.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, List


class HelpContent:
    """Centralized help content for all features"""
    
    HELP_DATA = {
        # Device Management
        'devices_list': {
            'title': 'Device List',
            'what_it_does': 'Shows all Android devices connected to your computer via USB or WiFi.',
            'tooltip': 'View all connected Android devices',
            'how_to': [
                '1. Connect Android device via USB',
                '2. Enable USB Debugging on device',
                '3. Accept authorization prompt',
                '4. Device appears in list automatically'
            ],
            'icon': '📱',
            'category': 'Device Management'
        },
        
        'usb_debugging': {
            'title': 'USB Debugging',
            'what_it_does': 'Enables USB debugging using 9 different methods including standard settings, system properties, database modification, and more.',
            'tooltip': 'Enable USB debugging with multiple methods',
            'how_to': [
                '1. Select method from dropdown',
                '2. Choose force mode for advanced methods',
                '3. Click Enable USB Debugging',
                '4. Check device for prompts'
            ],
            'icon': '🔌',
            'category': 'System Tools'
        },
        
        'backup': {
            'title': 'Device Backup',
            'what_it_does': 'Creates comprehensive backup including apps, data, settings, contacts, SMS, and files.',
            'tooltip': 'Backup all device data',
            'how_to': [
                '1. Select device from list',
                '2. Click Backup Device button',
                '3. Wait for completion',
                '4. Backup saved to ~/.void/backups/'
            ],
            'icon': '💾',
            'category': 'Backup & Recovery'
        },
        
        'problem_solver': {
            'title': 'Problem Solver',
            'what_it_does': 'Auto-diagnoses and fixes 8 types of Android problems including bootloops, connectivity, and performance issues.',
            'tooltip': 'Diagnose and fix device problems',
            'how_to': [
                '1. Select device',
                '2. Click Diagnose Problems',
                '3. Review detected issues',
                '4. Click Auto-Fix to apply fixes'
            ],
            'icon': '🩺',
            'category': 'Diagnostics'
        },
    }
    
    @classmethod
    def get_help(cls, feature_id: str) -> Optional[Dict]:
        """Get help content for a feature"""
        return cls.HELP_DATA.get(feature_id)
    
    @classmethod
    def get_tooltip(cls, feature_id: str) -> str:
        """Get tooltip text for a feature"""
        data = cls.HELP_DATA.get(feature_id, {})
        return data.get('tooltip', '')


class HelpDialog:
    """Help dialog window"""
    
    def __init__(self, parent, feature_id: str):
        self.parent = parent
        self.feature_id = feature_id
        self.help_data = HelpContent.get_help(feature_id)
        
        if not self.help_data:
            return
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create help dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"How To: {self.help_data['title']}")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg="#070b12")
        
        # Header
        header = tk.Frame(self.dialog, bg="#0d1520", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title_label = tk.Label(
            header,
            text=f"{self.help_data.get('icon', '❓')} {self.help_data['title']}",
            font=("Segoe UI", 14, "bold"),
            bg="#0d1520",
            fg="#00f5d4"
        )
        title_label.pack(expand=True)
        
        # Content
        content = tk.Frame(self.dialog, bg="#070b12")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        scrollbar = tk.Scrollbar(content)
        scrollbar.pack(side="right", fill="y")
        
        text = tk.Text(
            content,
            wrap="word",
            bg="#0a0f1a",
            fg="#ffffff",
            font=("Consolas", 10),
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set,
            relief="flat"
        )
        text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text.yview)
        
        # Populate
        text.insert("end", "📖 WHAT IT DOES\n", "header")
        text.insert("end", "─" * 60 + "\n", "separator")
        text.insert("end", self.help_data['what_it_does'] + "\n\n\n", "body")
        
        text.insert("end", "📝 HOW TO USE\n", "header")
        text.insert("end", "─" * 60 + "\n", "separator")
        for line in self.help_data['how_to']:
            text.insert("end", line + "\n", "body")
        
        text.tag_config("header", foreground="#00f5d4", font=("Segoe UI", 11, "bold"))
        text.tag_config("separator", foreground="#333333")
        text.tag_config("body", foreground="#e0e0e0")
        text.config(state="disabled")
        
        # Close button
        btn_frame = tk.Frame(self.dialog, bg="#070b12")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        close_btn = tk.Button(
            btn_frame,
            text="Close",
            command=self.dialog.destroy,
            bg="#7c3aed",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8
        )
        close_btn.pack(side="right")


class Tooltip:
    """Simple tooltip widget"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Show tooltip"""
        if self.tooltip_window or not self.text:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#1a1f2e",
            foreground="#ffffff",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=4
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_context_menu(widget, feature_id: str, parent_window):
    """Add right-click context menu"""
    
    def show_context_menu(event):
        menu = tk.Menu(widget, tearoff=0, bg="#1a1f2e", fg="#ffffff")
        menu.add_command(
            label="❓ How to use this",
            command=lambda: HelpDialog(parent_window, feature_id)
        )
        
        help_data = HelpContent.get_help(feature_id)
        if help_data:
            menu.add_command(
                label="ℹ️ What does this do?",
                command=lambda: show_quick_info(help_data)
            )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def show_quick_info(data):
        import tkinter.messagebox as mb
        mb.showinfo(data['title'], f"{data.get('icon', '❓')} {data['what_it_does']}")
    
    widget.bind("<Button-3>", show_context_menu)
    if hasattr(widget, 'bind'):
        widget.bind("<Control-Button-1>", show_context_menu)
