#!/usr/bin/env python3
"""Small Windows GUI for the DAoC spellcraft converter."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from sc_converter import (
    DEFAULT_SETTINGS,
    SETTINGS_PATH,
    WarningBag,
    blocking_warnings,
    canonical_realm,
    default_eden_dir,
    detect_and_parse,
    find_default_eden_ini,
    load_settings,
    parse_slot_order,
    planned_hotkey_count,
    hotkey_position,
    quickbar_hotkey_index,
    render_forge,
    render_zenk_report,
    save_settings,
    separator_macro_label,
    setup_bars,
)


DEFAULT_SLOT_ORDER = parse_slot_order("head,arms,hands,legs,feet,mainhand,offhand,twohanded,ranged")
APP_NAME = "Daoc Bar setup and craft tool"
APP_NOTICE = (
    "Daoc Bar setup and craft tool © 2026 Electronic87 - A non-commercial fan project. "
    "Not affiliated with EA, Broadsword, Mythic, Eden, DAoC Tools, Template Forge, or Zenkcraft. "
    "Built with AI-assisted coding support from OpenAI Codex."
)
MIN_WINDOW_WIDTH = 980
MIN_WINDOW_HEIGHT = 620
EXPORT_MIN_WINDOW_HEIGHT = 760
BAR_VISUAL_WIDTH = 650
BAR_VISUAL_HEIGHT = 86
BG = "#101418"
PANEL = "#172027"
PANEL_SOFT = "#1d2830"
FIELD = "#0d1116"
TEXT = "#f3efe7"
MUTED = "#aeb8c2"
ACCENT = "#c99a3f"
ACCENT_HOVER = "#e0b45a"
BORDER = "#34424d"
ALBION = "#b84a4a"
MIDGARD = "#3e78bd"
HIBERNIA = "#3f9b66"
SPELL_GLOW = "#ead7a1"
REALM_OPTIONS = ("Albion", "Midgard", "Hibernia")
REALM_COLORS = {
    "Albion": ALBION,
    "Midgard": MIDGARD,
    "Hibernia": HIBERNIA,
}
REALM_SYMBOLS = {
    "Albion": "cup",
    "Midgard": "hammer",
    "Hibernia": "tree",
}

CLASS_REALMS = {
    "armsman": "Albion",
    "cabalist": "Albion",
    "cleric": "Albion",
    "friar": "Albion",
    "heretic": "Albion",
    "infiltrator": "Albion",
    "mercenary": "Albion",
    "minstrel": "Albion",
    "necromancer": "Albion",
    "paladin": "Albion",
    "reaver": "Albion",
    "scout": "Albion",
    "sorcerer": "Albion",
    "theurgist": "Albion",
    "wizard": "Albion",
    "berserker": "Midgard",
    "zerk": "Midgard",
    "zerker": "Midgard",
    "bonedancer": "Midgard",
    "healer": "Midgard",
    "hunter": "Midgard",
    "runemaster": "Midgard",
    "rune master": "Midgard",
    "savage": "Midgard",
    "shadowblade": "Midgard",
    "shaman": "Midgard",
    "skald": "Midgard",
    "spiritmaster": "Midgard",
    "spirit master": "Midgard",
    "thane": "Midgard",
    "valkyrie": "Midgard",
    "warlock": "Midgard",
    "warrior": "Midgard",
    "animist": "Hibernia",
    "bainshee": "Hibernia",
    "bard": "Hibernia",
    "blademaster": "Hibernia",
    "blade master": "Hibernia",
    "champion": "Hibernia",
    "druid": "Hibernia",
    "eldritch": "Hibernia",
    "enchanter": "Hibernia",
    "hero": "Hibernia",
    "mentalist": "Hibernia",
    "nightshade": "Hibernia",
    "ranger": "Hibernia",
    "valewalker": "Hibernia",
    "vale walker": "Hibernia",
    "vampiir": "Hibernia",
    "warden": "Hibernia",
}


def default_chat_log_path() -> Path:
    return Path.home() / "Documents" / "Electronic Arts" / "Dark Age of Camelot" / "chat.log"


def path_from_field(value: str | Path, fallback: Path | None = None) -> Path:
    text = str(value).strip().strip('"') if value else ""
    if not text:
        return fallback or Path()
    username = os.environ.get("USERNAME") or Path.home().name
    text = re.sub(r"%username%", username, text, flags=re.IGNORECASE)
    return Path(os.path.expandvars(os.path.expanduser(text)))


def display_user_path(value: str | Path) -> str:
    if not value:
        return ""
    path = path_from_field(value)
    path_text = str(path)
    home = Path.home()
    home_text = str(home).rstrip("\\/")
    home_prefix = home_text + "\\"
    if path_text.lower() == home_text.lower():
        return str(home.parent / "%username%")
    if path_text.lower().startswith(home_prefix.lower()):
        return str(home.parent / "%username%") + "\\" + path_text[len(home_prefix) :]
    return str(value)


def display_chat_log_path() -> str:
    return display_user_path(default_chat_log_path())


def display_eden_dir() -> str:
    return display_user_path(default_eden_dir())


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / name


class CraftToolApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        icon_path = resource_path("daoc_craft_tool.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        usable_width = max(760, screen_width - 80)
        usable_height = max(560, screen_height - 140)
        self.base_min_width = min(MIN_WINDOW_WIDTH, usable_width)
        self.base_min_height = min(MIN_WINDOW_HEIGHT, usable_height)
        self.export_min_height = min(EXPORT_MIN_WINDOW_HEIGHT, max(self.base_min_height, usable_height))
        window_width = min(1220, max(self.base_min_width, screen_width - 160))
        window_height = min(960, max(self.base_min_height, screen_height - 160))
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(self.base_min_width, self.base_min_height)

        self.settings = load_settings()
        last_input_path = self.settings.get("last_input_path", "")
        last_input_dir = self.settings.get("last_input_dir", "")
        if not last_input_dir and last_input_path and path_from_field(last_input_path).parent.exists():
            last_input_dir = display_user_path(path_from_field(last_input_path).parent)
        self.last_input_dir = tk.StringVar(value=display_user_path(last_input_dir))
        self.input_path = tk.StringVar(value="")
        saved_chat_log = self.settings.get("last_chat_log_path", "") or display_chat_log_path()
        self.chat_log_path = tk.StringVar(value=display_user_path(saved_chat_log))
        source = self.settings.get("input_source", "paste")
        if source not in {"order", "chat", "paste"}:
            source = "paste"
        self.input_source = tk.StringVar(value=source)
        self.realm = tk.StringVar(value=canonical_realm(self.settings.get("realm", "Albion")))
        self.export_options_visible = tk.BooleanVar(value=False)
        saved_ini = self.settings.get("last_ini_path") or DEFAULT_SETTINGS["last_ini_path"]
        if not saved_ini:
            found_ini = find_default_eden_ini()
            saved_ini = str(found_ini) if found_ini else ""
        self.ini_path = tk.StringVar(value=display_user_path(saved_ini))
        self.eden_folder = tk.StringVar(value=display_user_path(self.settings.get("last_eden_dir") or default_eden_dir()))
        self.export_dir = tk.StringVar(value=display_user_path(self.settings.get("last_export_dir", "")))
        last_export = self.settings.get("last_action", "forge")
        if last_export not in {"forge", "zenk"}:
            last_export = "forge"
        self.action = tk.StringVar(value=last_export)
        self.template_name = tk.StringVar(value="")
        self.quickbar = tk.IntVar(value=int(self.settings.get("quickbar") or 1))
        self.page = tk.IntVar(value=int(self.settings.get("page") or 3))
        self.slot = tk.IntVar(value=int(self.settings.get("slot") or 1))
        self.include_separators = tk.BooleanVar(value=bool(self.settings.get("include_item_separators", True)))
        self.open_output_location = tk.BooleanVar(value=bool(self.settings.get("open_output_location", False)))
        self._bar_visual_items: list | None = None
        self._bar_visual_message = "Paste text, open an order file, or select chat.log."
        self._bar_visual_hitboxes: list[tuple[int, int, int, int, str, str]] = []
        self._bar_visual_page_controls: list[tuple[int, int, int, int, int]] = []
        self._preview_line_ranges: dict[str, tuple[str, str]] = {}
        self.bar_visual_page_offset = self._bar_visual_start_offset()
        self.gem_icon_images: dict[str, tk.PhotoImage] = {}
        self.realm_icon_images: dict[str, tk.PhotoImage] = {}
        self.app_logo_image: tk.PhotoImage | None = None
        self.realm_selector_hover_index: int | None = None
        if not self.export_dir.get().strip() and self.input_path.get():
            input_parent = path_from_field(self.input_path.get()).parent
            if input_parent.exists():
                self.export_dir.set(display_user_path(input_parent / "converted"))

        self.configure(bg=BG)
        self._load_daoc_gem_icons()
        self._build_ui()
        self._apply_window_minimum()
        self._refresh_preview()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        self.option_add("*Font", ("Segoe UI", 10))
        style.configure("Root.TFrame", background=BG)
        style.configure("Hero.TFrame", background=PANEL_SOFT, relief="solid", borderwidth=1)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL, relief="solid", borderwidth=1)
        style.configure("Inset.TFrame", background=PANEL_SOFT, relief="solid", borderwidth=1)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("HeroTitle.TLabel", background=PANEL_SOFT, foreground="#ffffff", font=("Segoe UI", 22, "bold"))
        style.configure("HeroSub.TLabel", background=PANEL_SOFT, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background=PANEL, foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.Panel.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Inset.TLabel", background=PANEL_SOFT, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.Inset.TLabel", background=PANEL_SOFT, foreground=MUTED, font=("Segoe UI", 8))
        style.configure("TRadiobutton", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.map("TRadiobutton", background=[("active", PANEL)], foreground=[("active", "#ffffff")])
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", PANEL)], foreground=[("active", "#ffffff")])
        style.configure("TEntry", fieldbackground="#f4f4f2", foreground="#111111", insertcolor="#111111")
        style.configure("TSpinbox", fieldbackground="#f4f4f2", foreground="#111111", arrowsize=12)
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7), background="#d8d8d8", foreground="#111111")
        style.map("TButton", background=[("active", "#eeeeee")], foreground=[("active", "#111111")])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8), background=ACCENT, foreground="#111111")
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)], foreground=[("active", "#111111")])

        self.scroll_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.scroll_canvas.yview,
            width=16,
            bg="#d8d8d8",
            activebackground=ACCENT,
            troughcolor="#25313a",
            relief=tk.FLAT,
            bd=0,
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        root = ttk.Frame(self.scroll_canvas, style="Root.TFrame", padding=(16, 14, 16, 14))
        self.scroll_frame = root
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=root, anchor=tk.NW)
        root.bind("<Configure>", self._scroll_frame_configured)
        self.scroll_canvas.bind("<Configure>", self._scroll_canvas_configured)
        self.bind_all("<MouseWheel>", self._main_mousewheel, add="+")
        self.bind_all("<Button-4>", self._main_mousewheel, add="+")
        self.bind_all("<Button-5>", self._main_mousewheel, add="+")

        hero = ttk.Frame(root, style="Hero.TFrame", padding=(14, 12, 14, 10))
        hero.pack(fill=tk.X, pady=(0, 12))
        hero.columnconfigure(1, weight=1)
        logo = tk.Canvas(hero, width=74, height=74, bg=PANEL_SOFT, highlightthickness=0)
        logo.grid(row=0, column=0, rowspan=3, sticky=tk.W, padx=(0, 14))
        self._draw_spellcraft_logo(logo, 74)
        ttk.Label(hero, text=APP_NAME, style="HeroTitle.TLabel").grid(row=0, column=1, sticky=tk.W)
        ttk.Label(
            hero,
            text="Paste an order, preview the gems, and set Eden quickbars safely.",
            style="HeroSub.TLabel",
        ).grid(row=1, column=1, sticky=tk.W, pady=(3, 0))
        realm_band = tk.Canvas(hero, height=9, bg=PANEL_SOFT, highlightthickness=0)
        realm_band.grid(row=2, column=1, sticky=tk.EW, pady=(12, 0))
        realm_band.bind("<Configure>", lambda event: self._draw_realm_band(realm_band, event.width, event.height))

        file_panel = ttk.Frame(root, style="Panel.TFrame", padding=10)
        file_panel.pack(fill=tk.X, pady=(0, 10))
        file_panel.columnconfigure(1, weight=1)
        self._section_mark(file_panel, ALBION).grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 8))
        ttk.Label(file_panel, text="Order", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=(14, 0), pady=(0, 8))
        ttk.Label(file_panel, text="Pick realm", style="Panel.TLabel").grid(row=0, column=2, sticky=tk.E, padx=(8, 6), pady=(0, 8))
        self.realm_selector = self._make_realm_selector(file_panel)
        self.realm_selector.grid(row=0, column=3, sticky=tk.E, pady=(0, 8))

        ttk.Radiobutton(
            file_panel,
            text="Pasted text",
            value="paste",
            variable=self.input_source,
            command=self._source_changed,
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Label(
            file_panel,
            text="Copy Discord/chat/order text first, then import it from your clipboard.",
            style="Muted.Panel.TLabel",
        ).grid(row=1, column=1, sticky=tk.W)
        ttk.Button(file_panel, text="Paste from Clipboard", style="Accent.TButton", command=self._paste_clipboard_text).grid(row=1, column=2, sticky=tk.W, padx=(8, 0))

        ttk.Radiobutton(
            file_panel,
            text="Order file",
            value="order",
            variable=self.input_source,
            command=self._source_changed,
        ).grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=(8, 0))
        ttk.Entry(file_panel, textvariable=self.input_path).grid(row=2, column=1, sticky=tk.EW, pady=(8, 0))
        ttk.Button(file_panel, text="Select File", command=self._choose_input).grid(row=2, column=2, padx=(8, 0), pady=(8, 0))

        ttk.Radiobutton(
            file_panel,
            text="Chat log",
            value="chat",
            variable=self.input_source,
            command=self._source_changed,
        ).grid(row=3, column=0, sticky=tk.W, padx=(0, 8), pady=(8, 0))
        ttk.Entry(file_panel, textvariable=self.chat_log_path).grid(row=3, column=1, sticky=tk.EW, pady=(8, 0))
        ttk.Button(file_panel, text="Select chat.log", command=self._choose_chat_log).grid(row=3, column=2, padx=(8, 0), pady=(8, 0))
        chat_actions = ttk.Frame(file_panel, style="Panel.TFrame")
        chat_actions.grid(row=3, column=3, sticky=tk.E, padx=(8, 0), pady=(8, 0))
        ttk.Button(chat_actions, text="Refresh", command=self._refresh_chat_log).pack(side=tk.LEFT)
        ttk.Button(chat_actions, text="Clear", command=self._clear_chat_log).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(
            file_panel,
            text=f"Common chat log path: {display_chat_log_path()}",
            style="Muted.Panel.TLabel",
            wraplength=900,
        ).grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=(4, 0))

        bar_panel = ttk.Frame(root, style="Panel.TFrame", padding=10)
        bar_panel.pack(fill=tk.X, pady=(0, 10))
        bar_panel.columnconfigure(1, weight=1)
        self._section_mark(bar_panel, HIBERNIA).grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Label(bar_panel, text="Gems to Quickbar", style="PanelTitle.TLabel").grid(row=0, column=0, sticky=tk.W, padx=(14, 8))
        ttk.Button(bar_panel, text="Set Hotbars", style="Accent.TButton", command=self._run_bars_action).grid(row=0, column=2, sticky=tk.E)
        ttk.Label(bar_panel, text="Eden folder", style="Panel.TLabel").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=(8, 0))
        ttk.Entry(bar_panel, textvariable=self.eden_folder).grid(row=1, column=1, sticky=tk.EW, pady=(8, 0))
        eden_buttons = ttk.Frame(bar_panel, style="Panel.TFrame")
        eden_buttons.grid(row=1, column=2, sticky=tk.E, padx=(8, 0), pady=(8, 0))
        ttk.Button(eden_buttons, text="Open Folder", command=self._open_eden_folder).pack(side=tk.LEFT)
        ttk.Button(eden_buttons, text="Find .ini", command=self._find_eden_ini).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(
            bar_panel,
            text=f"Default: {display_eden_dir()}  |  Find .ini picks the newest character INI, usually your last login.",
            style="Muted.Panel.TLabel",
            wraplength=900,
        ).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(4, 0))
        ttk.Label(bar_panel, text="Eden INI", style="Panel.TLabel").grid(row=3, column=0, sticky=tk.W, padx=(0, 8), pady=(8, 0))
        ttk.Entry(bar_panel, textvariable=self.ini_path).grid(row=3, column=1, sticky=tk.EW, pady=(8, 0))
        ttk.Button(bar_panel, text="Select .ini", command=self._choose_ini).grid(row=3, column=2, padx=(8, 0), pady=(8, 0))
        ttk.Checkbutton(
            bar_panel,
            text="Include item separators before each item (/craftqueue buy 1)",
            variable=self.include_separators,
            command=self._quickbar_options_changed,
        ).grid(row=4, column=1, sticky=tk.W, pady=(8, 0))

        positions = ttk.Frame(bar_panel, style="Inset.TFrame", padding=(8, 6))
        positions.grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
        for col, (label, var) in enumerate((("Quickbar", self.quickbar), ("Page", self.page), ("Slot", self.slot))):
            ttk.Label(positions, text=label, style="Inset.TLabel").grid(row=0, column=col, sticky=tk.W, padx=(0 if col == 0 else 18, 6))
            spin = ttk.Spinbox(positions, from_=1, to=10, width=5, textvariable=var, command=self._quickbar_options_changed)
            spin.grid(row=1, column=col, sticky=tk.W, padx=(0 if col == 0 else 18, 6))
            spin.bind("<FocusOut>", self._quickbar_options_changed)
            spin.bind("<Return>", self._quickbar_options_changed)

        visual_panel = ttk.Frame(bar_panel, style="Inset.TFrame", padding=(8, 6))
        visual_panel.grid(row=5, column=1, columnspan=2, sticky=tk.EW, padx=(12, 0), pady=(10, 0))
        visual_panel.columnconfigure(0, weight=1)
        ttk.Label(visual_panel, text="Bar Visual", style="Inset.TLabel").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(
            visual_panel,
            text="Hover slots to highlight the preview. Scroll or click the page arrows to switch pages.",
            style="Muted.Inset.TLabel",
        ).grid(row=1, column=0, sticky=tk.W, pady=(1, 0))
        self.bar_visual = tk.Canvas(
            visual_panel,
            width=BAR_VISUAL_WIDTH,
            height=BAR_VISUAL_HEIGHT,
            bg=FIELD,
            takefocus=1,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self.bar_visual.grid(row=2, column=0, sticky=tk.EW, pady=(4, 0))
        self.bar_visual.bind("<Configure>", lambda event: self._redraw_quickbar_visual())
        self.bar_visual.bind("<Enter>", lambda event: self.bar_visual.focus_set())
        self.bar_visual.bind("<Motion>", self._bar_visual_motion)
        self.bar_visual.bind("<Leave>", self._bar_visual_leave)
        self.bar_visual.bind("<MouseWheel>", self._bar_visual_wheel)
        self.bar_visual.bind("<Button-4>", self._bar_visual_wheel)
        self.bar_visual.bind("<Button-5>", self._bar_visual_wheel)
        self.bar_visual.bind("<Button-1>", self._bar_visual_click)

        content = ttk.Frame(root)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left = ttk.Frame(content, style="Panel.TFrame", padding=10)
        left.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5))
        self._section_mark(left, ACCENT, width=48, height=3).pack(anchor=tk.W, fill=tk.X, pady=(0, 7))
        ttk.Label(left, text="Quickbar Preview", style="PanelTitle.TLabel").pack(anchor=tk.W)
        self.preview = self._make_scrolled_text(left)

        right = ttk.Frame(content, style="Panel.TFrame", padding=10)
        right.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0))
        self._section_mark(right, ACCENT, width=48, height=3).pack(anchor=tk.W, fill=tk.X, pady=(0, 7))
        ttk.Label(right, text="Status", style="PanelTitle.TLabel").pack(anchor=tk.W)
        self.status = self._make_scrolled_text(right)

        export_shell = ttk.Frame(root, style="Root.TFrame")
        export_shell.pack(fill=tk.X, pady=(10, 0))
        self.export_toggle_button = ttk.Button(
            export_shell,
            text="Show Export File Options",
            command=self._toggle_export_options,
        )
        self.export_toggle_button.pack(anchor=tk.W)
        self.export_panel = ttk.Frame(export_shell, style="Panel.TFrame", padding=10)
        self.export_panel.columnconfigure(1, weight=1)
        self._section_mark(self.export_panel, MIDGARD).grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Label(self.export_panel, text="Export File", style="PanelTitle.TLabel").grid(row=0, column=0, sticky=tk.W, padx=(14, 0), pady=(0, 8))
        ttk.Button(self.export_panel, text="Create Export File", style="Accent.TButton", command=self._run_file_action).grid(row=0, column=3, sticky=tk.E, pady=(0, 8))
        ttk.Label(self.export_panel, text="Export name", style="Panel.TLabel").grid(row=1, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Entry(self.export_panel, textvariable=self.template_name).grid(row=1, column=1, columnspan=3, sticky=tk.EW)
        ttk.Label(self.export_panel, text="Save folder", style="Panel.TLabel").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=(8, 0))
        ttk.Entry(self.export_panel, textvariable=self.export_dir).grid(row=2, column=1, sticky=tk.EW, pady=(8, 0))
        ttk.Button(self.export_panel, text="Select Folder", command=self._choose_export_dir).grid(row=2, column=2, padx=(8, 0), pady=(8, 0))
        ttk.Checkbutton(
            self.export_panel,
            text="Open file location after export",
            variable=self.open_output_location,
            command=self._save_settings_from_fields,
        ).grid(row=2, column=3, sticky=tk.W, padx=(8, 0), pady=(8, 0))
        action_frame = ttk.Frame(self.export_panel, style="Panel.TFrame")
        action_frame.grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=(8, 0))
        export_actions = [
            ("Make Template Forge .forge", "forge"),
            ("Make Zenkcraft .txt", "zenk"),
        ]
        for index, (label, value) in enumerate(export_actions):
            ttk.Radiobutton(
                action_frame,
                text=label,
                value=value,
                variable=self.action,
                command=self._export_action_changed,
            ).grid(row=0, column=index, sticky=tk.W, padx=(0 if index == 0 else 14, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="Refresh Preview", command=self._refresh_preview).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Restore Backup", command=self._restore_backup).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(
            root,
            text=APP_NOTICE,
            style="HeroSub.TLabel",
            wraplength=1120,
        ).pack(anchor=tk.W, fill=tk.X, pady=(10, 0))

    def _make_realm_selector(self, parent: tk.Widget) -> tk.Canvas:
        canvas = tk.Canvas(
            parent,
            width=432,
            height=58,
            bg=PANEL,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        canvas.bind("<Button-1>", self._realm_selector_clicked)
        canvas.bind("<Motion>", self._realm_selector_motion)
        canvas.bind("<Leave>", self._realm_selector_leave)
        canvas.bind("<Configure>", lambda event: self._draw_realm_selector())
        self.after_idle(self._draw_realm_selector)
        return canvas

    def _make_scrolled_text(self, parent: tk.Widget) -> tk.Text:
        frame = ttk.Frame(parent, style="Inset.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        text = tk.Text(
            frame,
            height=12,
            wrap=tk.WORD,
            bg=FIELD,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            padx=8,
            pady=8,
            font=("Consolas", 9),
        )
        scrollbar = tk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=text.yview,
            width=16,
            bg="#d8d8d8",
            activebackground=ACCENT,
            troughcolor="#25313a",
            relief=tk.FLAT,
            bd=0,
        )
        text.configure(yscrollcommand=scrollbar.set)
        text.tag_configure("bar_hover", background="#3c3321", foreground="#fff2c8")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return text

    def _scroll_frame_configured(self, event: tk.Event | None = None) -> None:
        if not hasattr(self, "scroll_canvas"):
            return
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _scroll_canvas_configured(self, event: tk.Event) -> None:
        if not hasattr(self, "scroll_window"):
            return
        self.scroll_canvas.itemconfigure(self.scroll_window, width=event.width)
        requested_height = self.scroll_frame.winfo_reqheight() if hasattr(self, "scroll_frame") else event.height
        self.scroll_canvas.itemconfigure(self.scroll_window, height=max(event.height, requested_height))
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _widget_within(self, widget: tk.Widget, parent: tk.Widget) -> bool:
        current = widget
        while current is not None:
            if current == parent:
                return True
            current = getattr(current, "master", None)
        return False

    def _main_mousewheel(self, event: tk.Event) -> str | None:
        if not hasattr(self, "scroll_canvas"):
            return None
        widget = event.widget
        if hasattr(self, "bar_visual") and self._widget_within(widget, self.bar_visual):
            return None
        widget_class = widget.winfo_class()
        if widget_class in {"Text", "Entry", "TEntry", "Spinbox", "TSpinbox", "Scrollbar"}:
            return None
        if getattr(event, "num", None) == 4:
            units = -3
        elif getattr(event, "num", None) == 5:
            units = 3
        else:
            units = -3 if getattr(event, "delta", 0) > 0 else 3
        self.scroll_canvas.yview_scroll(units, "units")
        return "break"

    def _resize_window_height(self, delta: int) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        min_width, min_height = self.minsize()
        max_height = max(min_height, self.winfo_screenheight() - 100)
        next_height = max(min_height, min(max_height, height + delta))
        self.geometry(f"{max(width, min_width)}x{next_height}")

    def _apply_window_minimum(self) -> None:
        export_open = bool(hasattr(self, "export_panel") and self.export_panel.winfo_ismapped())
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        requested_width = self.winfo_reqwidth() + 24
        target_height = self.export_min_height if export_open else self.base_min_height
        min_width = min(max(self.base_min_width, requested_width), max(760, screen_width - 40))
        min_height = min(target_height, max(560, screen_height - 120))
        self.minsize(min_width, min_height)
        if self.winfo_width() < min_width or self.winfo_height() < min_height:
            self.geometry(f"{max(self.winfo_width(), min_width)}x{max(self.winfo_height(), min_height)}")

    def _toggle_export_options(self) -> None:
        if self.export_panel.winfo_ismapped():
            shrink_by = self.export_panel.winfo_height() + 10
            self.export_panel.pack_forget()
            self.export_toggle_button.configure(text="Show Export File Options")
            self._apply_window_minimum()
            self._resize_window_height(-shrink_by)
        else:
            self.export_panel.pack(fill=tk.X, pady=(8, 0))
            self.export_toggle_button.configure(text="Hide Export File Options")
            self.update_idletasks()
            self._apply_window_minimum()
            self._resize_window_height(self.export_panel.winfo_reqheight() + 10)

    def _section_mark(self, parent: tk.Widget, color: str, width: int = 6, height: int = 19) -> tk.Canvas:
        mark = tk.Canvas(parent, width=width, height=height, bg=PANEL, highlightthickness=0)
        mark.create_rectangle(0, 0, width, height, fill=color, outline=color)
        mark.create_rectangle(0, 0, width, 3, fill=SPELL_GLOW, outline=SPELL_GLOW)
        return mark

    def _load_daoc_gem_icons(self) -> None:
        icon_dir = resource_path("daoc_gem_icons")
        for key in ("red", "amber", "green", "cyan", "blue", "purple", "yellow", "white"):
            icon_path = icon_dir / f"{key}.png"
            if not icon_path.exists():
                continue
            try:
                self.gem_icon_images[key] = tk.PhotoImage(file=str(icon_path))
            except tk.TclError:
                continue
        realm_dir = resource_path("daoc_realm_icons")
        for realm in REALM_OPTIONS:
            icon_path = realm_dir / f"{realm}.png"
            if not icon_path.exists():
                continue
            try:
                self.realm_icon_images[realm] = tk.PhotoImage(file=str(icon_path))
            except tk.TclError:
                continue
        logo_path = resource_path("daoc_app_assets") / "daoc_craft_logo_74.png"
        if logo_path.exists():
            try:
                self.app_logo_image = tk.PhotoImage(file=str(logo_path))
            except tk.TclError:
                self.app_logo_image = None

    def _draw_spellcraft_logo(self, canvas: tk.Canvas, size: int) -> None:
        canvas.delete("all")
        if self.app_logo_image:
            canvas.create_image(size / 2, size / 2, image=self.app_logo_image)
            return
        center = size / 2
        canvas.create_oval(5, 5, size - 5, size - 5, fill="#0e141b", outline=BORDER, width=2)
        for radius, color in ((25, "#28333d"), (18, "#33404b")):
            canvas.create_oval(center - radius, center - radius, center + radius, center + radius, outline=color, width=1)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = center + math.cos(rad) * 13
            y1 = center + math.sin(rad) * 13
            x2 = center + math.cos(rad) * 27
            y2 = center + math.sin(rad) * 27
            canvas.create_line(x1, y1, x2, y2, fill="#40505c", width=1)
        self._draw_crystal(canvas, center, 9, 48, 26, ALBION)
        self._draw_crystal(canvas, 16, 42, 32, 66, MIDGARD)
        self._draw_crystal(canvas, 50, 42, 66, 66, HIBERNIA)
        self._draw_crystal(canvas, 20, 16, 54, 56, ACCENT, outline=SPELL_GLOW)
        canvas.create_oval(center - 4, center - 4, center + 4, center + 4, fill="#fff1b8", outline="#fff1b8")
        for x, y in ((13, 18), (59, 18), (18, 60), (56, 60)):
            canvas.create_line(x - 2, y, x + 2, y, fill=SPELL_GLOW)
            canvas.create_line(x, y - 2, x, y + 2, fill=SPELL_GLOW)

    def _draw_crystal(
        self,
        canvas: tk.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        fill: str,
        outline: str = "#d8d0bd",
    ) -> None:
        mx = (x1 + x2) / 2
        canvas.create_polygon(mx, y1, x2, (y1 + y2) / 2, mx, y2, x1, (y1 + y2) / 2, fill=fill, outline=outline, width=1)
        canvas.create_line(mx, y1, mx, y2, fill="#161b20", width=1)
        canvas.create_line(x1, (y1 + y2) / 2, x2, (y1 + y2) / 2, fill="#161b20", width=1)

    def _realm_selector_clicked(self, event: tk.Event) -> None:
        if not hasattr(self, "realm_selector"):
            return
        index = self._realm_selector_index_for_x(event.x)
        self.realm.set(REALM_OPTIONS[index])
        self._realm_changed()

    def _realm_selector_index_for_x(self, x: int) -> int:
        width = max(1, self.realm_selector.winfo_width())
        return min(len(REALM_OPTIONS) - 1, max(0, int(x / (width / len(REALM_OPTIONS)))))

    def _realm_selector_motion(self, event: tk.Event) -> None:
        index = self._realm_selector_index_for_x(event.x)
        if index == self.realm_selector_hover_index:
            return
        self.realm_selector_hover_index = index
        self._draw_realm_selector()

    def _realm_selector_leave(self, event: tk.Event | None = None) -> None:
        if self.realm_selector_hover_index is None:
            return
        self.realm_selector_hover_index = None
        self._draw_realm_selector()

    def _draw_realm_selector(self) -> None:
        if not hasattr(self, "realm_selector"):
            return
        canvas = self.realm_selector
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        segment = width / len(REALM_OPTIONS)
        selected = canonical_realm(self.realm.get())

        for index, realm in enumerate(REALM_OPTIONS):
            x1 = index * segment
            x2 = width if index == len(REALM_OPTIONS) - 1 else (index + 1) * segment
            color = REALM_COLORS[realm]
            is_selected = realm == selected
            is_hovered = index == self.realm_selector_hover_index
            fill = "#252d34" if is_selected else ("#1a242b" if is_hovered else FIELD)
            outline = ACCENT if is_selected else ("#75633f" if is_hovered else "#3b4650")
            canvas.create_rectangle(x1 + 1, 1, x2 - 1, height - 1, fill=fill, outline=outline, width=2 if is_selected else 1)
            canvas.create_rectangle(x1 + 7, 5, x2 - 7, 8, fill=color, outline=color)
            group_width = 112
            group_left = x1 + (segment - group_width) / 2
            crest_x = group_left + 24
            text_x = group_left + 56
            self._draw_realm_crest(canvas, REALM_SYMBOLS[realm], crest_x, height / 2 + 4, color, is_selected or is_hovered, realm)
            canvas.create_text(
                text_x,
                height / 2 + 4,
                text=realm,
                fill=color,
                anchor=tk.W,
                font=("Segoe UI", 10, "bold"),
            )

    def _draw_realm_crest(
        self,
        canvas: tk.Canvas,
        symbol: str,
        x: float,
        y: float,
        color: str,
        selected: bool,
        realm: str | None = None,
    ) -> None:
        stone = "#5b5d5a" if selected else "#3f4548"
        dark = "#12161a"
        edge = "#8b8778" if selected else "#666a68"
        points = (
            x - 22,
            y - 22,
            x + 22,
            y - 22,
            x + 18,
            y + 3,
            x,
            y + 24,
            x - 18,
            y + 3,
        )
        canvas.create_polygon(points, fill=stone, outline=edge, width=2)
        canvas.create_line(x - 18, y - 18, x + 17, y - 18, fill="#777b74", width=1)
        canvas.create_line(x - 15, y + 5, x, y + 21, x + 15, y + 5, fill="#333a3f", width=1)
        icon = self.realm_icon_images.get(realm or "")
        if icon:
            canvas.create_image(x, y, image=icon)
            return
        self._draw_realm_symbol(canvas, symbol, x, y + 1, color)

    def _draw_realm_symbol(self, canvas: tk.Canvas, symbol: str, x: float, y: float, color: str) -> None:
        if symbol == "cup":
            canvas.create_polygon(
                x - 11,
                y - 10,
                x + 11,
                y - 10,
                x + 8,
                y - 4,
                x + 4,
                y + 1,
                x - 4,
                y + 1,
                x - 8,
                y - 4,
                fill=color,
                outline=color,
            )
            canvas.create_rectangle(x - 2, y, x + 2, y + 9, fill=color, outline=color)
            canvas.create_polygon(x - 9, y + 9, x + 9, y + 9, x + 12, y + 13, x - 12, y + 13, fill=color, outline=color)
            canvas.create_line(x - 8, y - 8, x + 8, y - 8, fill="#f2a0a0", width=1)
            canvas.create_rectangle(x - 5, y - 5, x - 3, y - 3, fill="#7d2b2f", outline="#7d2b2f")
            canvas.create_rectangle(x + 3, y - 7, x + 5, y - 5, fill="#7d2b2f", outline="#7d2b2f")
        elif symbol == "hammer":
            canvas.create_polygon(
                x - 10,
                y - 13,
                x + 10,
                y - 13,
                x + 10,
                y - 7,
                x + 5,
                y - 7,
                x + 5,
                y - 4,
                x - 5,
                y - 4,
                x - 5,
                y - 7,
                x - 10,
                y - 7,
                fill=color,
                outline=color,
            )
            canvas.create_rectangle(x - 2, y - 4, x + 2, y + 12, fill=color, outline=color)
            canvas.create_polygon(x - 5, y + 12, x + 5, y + 12, x + 3, y + 15, x - 3, y + 15, fill=color, outline=color)
            canvas.create_rectangle(x - 7, y - 11, x - 5, y - 9, fill="#145070", outline="#145070")
            canvas.create_rectangle(x + 3, y - 12, x + 5, y - 10, fill="#145070", outline="#145070")
        else:
            canvas.create_rectangle(x - 2, y - 3, x + 2, y + 13, fill=color, outline=color)
            canvas.create_polygon(
                x,
                y - 14,
                x - 7,
                y - 10,
                x - 11,
                y - 3,
                x - 6,
                y + 0,
                x - 12,
                y + 5,
                x - 4,
                y + 6,
                x,
                y + 3,
                x + 4,
                y + 6,
                x + 12,
                y + 5,
                x + 6,
                y + 0,
                x + 11,
                y - 3,
                x + 7,
                y - 10,
                fill=color,
                outline=color,
            )
            canvas.create_line(x - 8, y + 13, x - 2, y + 8, fill=color, width=2)
            canvas.create_line(x + 8, y + 13, x + 2, y + 8, fill=color, width=2)
            canvas.create_rectangle(x - 6, y - 5, x - 4, y - 3, fill="#17694c", outline="#17694c")
            canvas.create_rectangle(x + 5, y - 2, x + 7, y + 0, fill="#17694c", outline="#17694c")

    def _draw_realm_band(self, canvas: tk.Canvas, width: int, height: int) -> None:
        canvas.delete("all")
        colors = (ALBION, MIDGARD, HIBERNIA)
        stripe_width = max(1, width // len(colors))
        for index, color in enumerate(colors):
            start = index * stripe_width
            end = width if index == len(colors) - 1 else (index + 1) * stripe_width
            canvas.create_rectangle(start, 2, end, height - 2, fill=color, outline=color)
        canvas.create_rectangle(0, 0, width, 1, fill="#2d3942", outline="#2d3942")
        canvas.create_rectangle(0, height - 1, width, height, fill="#2d3942", outline="#2d3942")

    def _export_suffix(self, action: str | None = None) -> str:
        action = action or self.action.get()
        return ".forge" if action == "forge" else "_SC-Report.txt"

    def _strip_export_suffix(self, name: str) -> str:
        clean = Path(name.strip()).name
        lowered = clean.lower()
        if lowered.endswith("_sc-report.txt"):
            return clean[: -len("_SC-Report.txt")]
        if lowered.endswith(".forge") or lowered.endswith(".txt"):
            return clean.rsplit(".", 1)[0]
        return clean

    def _default_export_name_for_path(self, path: Path) -> str:
        return f"{path.stem}{self._export_suffix()}"

    def _sync_export_name_with_path(self, path: Path, force: bool = False) -> None:
        if force or not self.template_name.get().strip():
            self.template_name.set(self._default_export_name_for_path(path))

    def _export_file_name(self, input_path: Path, action: str) -> str:
        raw_name = self.template_name.get().strip()
        if raw_name:
            stem = self._strip_export_suffix(raw_name)
        else:
            stem = input_path.stem or "Import"
        return f"{stem}{self._export_suffix(action)}"

    def _export_title(self, input_path: Path) -> str:
        raw_name = self.template_name.get().strip()
        if raw_name:
            title = self._strip_export_suffix(raw_name)
        else:
            title = input_path.stem or "Import"
        return title or "Import"

    def _export_action_changed(self) -> None:
        current = self.template_name.get().strip()
        if current:
            self.template_name.set(f"{self._strip_export_suffix(current)}{self._export_suffix()}")
        else:
            try:
                self._sync_export_name_with_path(self._active_input_path(), force=False)
            except Exception:
                pass
        self._save_settings_from_fields()

    def _realm_changed(self, event: object | None = None) -> None:
        self.realm.set(canonical_realm(self.realm.get()))
        self._draw_realm_selector()
        self.bar_visual_page_offset = self._bar_visual_start_offset()
        self._save_settings_from_fields()
        self._refresh_preview()

    def _source_changed(self) -> None:
        try:
            self._sync_export_name_with_path(self._active_input_path(), force=False)
        except Exception:
            pass
        self.bar_visual_page_offset = self._bar_visual_start_offset()
        self._save_settings_from_fields()
        self._refresh_preview()

    def _quickbar_options_changed(self, event: object | None = None) -> None:
        self.bar_visual_page_offset = self._bar_visual_start_offset()
        self._save_settings_from_fields()
        self._refresh_preview()

    def _redraw_quickbar_visual(self) -> None:
        self._draw_quickbar_visual(self._bar_visual_items, self._bar_visual_message, store=False)

    def _bar_visual_start_offset(self) -> int:
        try:
            page = int(self.page.get())
        except (tk.TclError, ValueError):
            page = 1
        return min(9, max(0, page - 1))

    def _planned_bar_visual_entries(self, items: list) -> list[dict]:
        hotkey_index = quickbar_hotkey_index(int(self.page.get()), int(self.slot.get()))
        entries: list[dict] = []
        for item in items:
            if self.include_separators.get():
                page, slot = hotkey_position(hotkey_index)
                entries.append(
                    {
                        "kind": "separator",
                        "page": page,
                        "slot": slot,
                        "item": item,
                        "label": f"{separator_macro_label(item)}\n/craftqueue buy 1",
                        "preview_key": f"{page}:{slot}",
                    }
                )
                hotkey_index += 1
            for gem in item.gems:
                page, slot = hotkey_position(hotkey_index)
                entries.append(
                    {
                        "kind": "gem",
                        "page": page,
                        "slot": slot,
                        "gem": gem,
                        "item": item,
                        "label": f"{gem.zenk_gem_name}\n{gem.zenk_display} +{gem.value}",
                        "preview_key": f"{page}:{slot}",
                    }
                )
                hotkey_index += 1
        return entries

    def _draw_quickbar_visual(self, items: list | None, message: str | None = None, store: bool = True) -> None:
        if store:
            self._bar_visual_items = items
            self._bar_visual_message = message or ""
        if not hasattr(self, "bar_visual"):
            return

        canvas = self.bar_visual
        canvas.delete("all")
        self._bar_visual_hitboxes = []
        self._bar_visual_page_controls = []
        width = max(BAR_VISUAL_WIDTH, canvas.winfo_width())
        height = max(BAR_VISUAL_HEIGHT, canvas.winfo_height())

        if message:
            canvas.create_text(
                width / 2,
                height / 2,
                text=message,
                fill=MUTED,
                font=("Segoe UI", 9),
                width=width - 28,
                justify=tk.CENTER,
            )
            return
        if not items:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Paste text, open an order file, or select chat.log.",
                fill=MUTED,
                font=("Segoe UI", 9),
                width=width - 28,
                justify=tk.CENTER,
            )
            return

        try:
            entries = self._planned_bar_visual_entries(items)
        except Exception as exc:
            canvas.create_text(
                width / 2,
                height / 2,
                text=str(exc),
                fill="#f1c27d",
                font=("Segoe UI", 9),
                width=width - 28,
                justify=tk.CENTER,
            )
            return
        if not entries:
            canvas.create_text(width / 2, height / 2, text="No quickbar slots needed.", fill=MUTED, font=("Segoe UI", 9))
            return

        by_position = {(entry["page"], entry["slot"]): entry for entry in entries}
        pages = list(range(1, 11))
        if self.bar_visual_page_offset >= len(pages):
            self.bar_visual_page_offset = max(0, len(pages) - 1)
        rail_width = 52
        left = 8
        top = 9
        gap = 1
        available_width = max(260, width - left - rail_width - 16)
        slot_size = max(28, min(38, int((available_width - (gap * 9)) / 10)))
        row_height = slot_size + 26
        visible_rows = max(1, min(2, int((height - top - 6) / row_height)))
        max_offset = max(0, len(pages) - visible_rows)
        self.bar_visual_page_offset = min(max(0, self.bar_visual_page_offset), max_offset)
        visible_pages = pages[self.bar_visual_page_offset : self.bar_visual_page_offset + visible_rows]
        has_page_controls = len(pages) > visible_rows
        up_enabled = True
        down_enabled = True
        for row, page in enumerate(visible_pages):
            y1 = top + (row * row_height) + 16
            y2 = y1 + slot_size
            bar_x1 = left + rail_width
            bar_x2 = bar_x1 + (slot_size * 10) + (gap * 9)
            canvas.create_rectangle(left, y1 - 13, bar_x2 + 6, y2 + 6, fill="#05070a", outline="#3d4650", width=1)
            canvas.create_rectangle(left + 1, y1 - 12, bar_x2 + 5, y2 + 5, fill="#101720", outline="#6f7880", width=1)
            canvas.create_rectangle(left + 3, y1 - 10, bar_x2 + 3, y2 + 3, fill="#020304", outline="#232d36", width=1)
            rail_x = left + 5
            rail_y = y1 - 8
            rail_h = slot_size + 9
            self._draw_daoc_bar_rail(
                canvas,
                rail_x,
                rail_y,
                rail_width - 9,
                rail_h,
                page,
                has_page_controls,
                up_enabled,
                down_enabled,
            )
            if has_page_controls:
                up_box, down_box = self._daoc_rail_control_boxes(rail_x, rail_y, rail_width - 9, rail_h)
                self._bar_visual_page_controls.append((*up_box, 1))
                self._bar_visual_page_controls.append((*down_box, -1))
            x_start = bar_x1
            for slot in range(1, 11):
                x1 = x_start + (slot - 1) * (slot_size + gap)
                x2 = x1 + slot_size
                self._draw_daoc_empty_slot(canvas, x1, y1, x2, y2)
                canvas.create_text(
                    (x1 + x2) / 2,
                    y1 - 7,
                    text=str(slot),
                    fill="#ece6d8",
                    anchor=tk.CENTER,
                    font=("Arial", 8, "bold"),
                )
                entry = by_position.get((page, slot))
                if entry:
                    label = str(entry["label"])
                    self._bar_visual_hitboxes.append((int(x1), int(y1), int(x2), int(y2), label, str(entry["preview_key"])))
                    if entry["kind"] == "separator":
                        self._draw_separator_slot(canvas, x1, y1, x2, y2, entry["item"].title)
                    else:
                        self._draw_gem_slot(canvas, x1, y1, x2, y2, entry["gem"])

    def _draw_daoc_bar_rail(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        page: int,
        has_page_controls: bool,
        up_enabled: bool,
        down_enabled: bool,
    ) -> None:
        canvas.create_rectangle(x, y, x + width, y + height, fill="#0a0d11", outline="#323a43", width=1)
        canvas.create_rectangle(x + 2, y + 2, x + width - 2, y + height - 2, fill="#111821", outline="#5a6670", width=1)
        canvas.create_text(x + 11, y + 15, text=str(page), fill="#f0eadb", font=("Arial", 10, "bold"))
        canvas.create_text(x + 11, y + 32, text="Pg", fill="#c4c9ca", font=("Arial", 7, "bold"))
        if has_page_controls:
            self._draw_daoc_rail_arrow_cluster(canvas, x + width - 8, y + 13, "up", up_enabled)
            self._draw_daoc_rail_arrow_cluster(canvas, x + width - 8, y + height - 13, "down", down_enabled)

    def _daoc_rail_control_boxes(self, x: float, y: float, width: float, height: float) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
        control_x = x + width - 8
        up_box = (int(control_x - 8), int(y + 4), int(control_x + 8), int(y + 22))
        down_box = (int(control_x - 8), int(y + height - 22), int(control_x + 8), int(y + height - 4))
        return up_box, down_box

    def _draw_daoc_rail_arrow_cluster(self, canvas: tk.Canvas, x: float, y: float, direction: str, enabled: bool) -> None:
        fill = "#e9e0c9" if enabled else "#59636b"
        shadow = "#090c10"
        offsets = (-5, 0, 5)
        for offset in offsets:
            cy = y + offset
            if direction == "up":
                points = (x - 4, cy + 2, x, cy - 3, x + 4, cy + 2)
            else:
                points = (x - 4, cy - 2, x, cy + 3, x + 4, cy - 2)
            canvas.create_line(points, fill=shadow, width=3, joinstyle=tk.MITER)
            canvas.create_line(points, fill=fill, width=1, joinstyle=tk.MITER)

    def _draw_daoc_empty_slot(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float) -> None:
        canvas.create_rectangle(x1, y1, x2, y2, fill="#05070a", outline="#879099", width=1)
        canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, fill="#10171f", outline="#1b222a", width=1)
        canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill="#141b22", outline="#030507", width=1)
        canvas.create_line(x1 + 2, y1 + 2, x2 - 2, y1 + 2, fill="#c2c8cb", width=1)
        canvas.create_line(x1 + 2, y1 + 2, x1 + 2, y2 - 2, fill="#6b747b", width=1)
        canvas.create_line(x1 + 2, y2 - 2, x2 - 2, y2 - 2, fill="#020304", width=1)
        canvas.create_line(x2 - 2, y1 + 2, x2 - 2, y2 - 2, fill="#020304", width=1)

    def _draw_separator_slot(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, title: str) -> None:
        canvas.create_rectangle(x1 + 4, y1 + 4, x2 - 4, y2 - 4, fill="#22272d", outline="#dad4c2")
        canvas.create_rectangle(x1 + 6, y1 + 6, x2 - 6, y2 - 6, fill="#171b20", outline="#3b4248")
        canvas.create_line(x1 + 8, y1 + 9, x2 - 8, y1 + 9, fill="#fff0b2", width=1)
        short_title = {
            "Helmet": "HELME",
            "Hands": "HANDS",
            "Arms": "ARMS",
            "Legs": "LEGS",
            "Feet": "FEET",
        }.get(title, title[:4].upper())
        canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 + 2,
            text=short_title,
            fill="#e6dfcb",
            font=("Small Fonts", 6, "bold"),
        )

    def _draw_gem_slot(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, gem: object) -> None:
        icon = self.gem_icon_images.get(self._gem_visual_icon_key(gem))
        if icon:
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill="#05070a", outline="#161b20")
            canvas.create_image(cx, cy, image=icon)
            return

        color = self._gem_visual_color(gem)
        shadow = self._shade_color(color, 0.52)
        mid = self._shade_color(color, 0.82)
        light = self._shade_color(color, 1.35)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        pad = max(4, (x2 - x1) * 0.12)
        canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill="#0d1014", outline="#181e24")
        canvas.create_oval(x1 + pad, y1 + pad, x2 - pad, y2 - pad, fill=shadow, outline="#eee6c2", width=1)
        canvas.create_polygon(
            cx,
            y1 + pad + 1,
            x2 - pad - 1,
            cy,
            cx,
            y2 - pad - 1,
            x1 + pad + 1,
            cy,
            fill=color,
            outline="#f6edc9",
            width=1,
        )
        canvas.create_polygon(
            cx,
            y1 + pad + 2,
            x2 - pad - 2,
            cy,
            cx + 1,
            cy - 1,
            fill=light,
            outline=light,
        )
        canvas.create_polygon(
            x1 + pad + 2,
            cy,
            cx,
            y2 - pad - 2,
            cx - 1,
            cy + 1,
            fill=mid,
            outline=mid,
        )
        canvas.create_line(cx, y1 + pad + 2, cx, y2 - pad - 2, fill="#ffffff", width=1)
        canvas.create_line(x1 + pad + 3, cy, x2 - pad - 3, cy, fill="#212121", width=1)
        canvas.create_oval(cx - 3, cy - 8, cx + 4, cy - 2, fill="#fff8d8", outline="")

    def _shade_color(self, color: str, factor: float) -> str:
        color = color.lstrip("#")
        red = min(255, max(0, int(int(color[0:2], 16) * factor)))
        green = min(255, max(0, int(int(color[2:4], 16) * factor)))
        blue = min(255, max(0, int(int(color[4:6], 16) * factor)))
        return f"#{red:02x}{green:02x}{blue:02x}"

    def _gem_slot_value(self, gem: object) -> str:
        value = getattr(gem, "value", "")
        category = getattr(gem, "category", "")
        if category == "resist":
            return f"{value}%"
        return f"+{value}"

    def _gem_visual_icon_key(self, gem: object) -> str:
        name = getattr(gem, "zenk_gem_name", "").lower()
        type_name = getattr(gem, "type", "").lower()
        if any(key in name or key in type_name for key in ("blood", "heated", "cinder", "steaming")):
            return "red"
        if "fiery" in name or "fiery" in type_name:
            return "amber"
        if any(key in name or key in type_name for key in ("earthen", "radiant")):
            return "green"
        if any(key in name or key in type_name for key in ("watery", "glacier")):
            return "blue"
        if "dusty" in name or "dusty" in type_name:
            return "purple"
        if any(key in name or key in type_name for key in ("airy", "light", "finesse", "salt")):
            return "white"
        if any(key in name or key in type_name for key in ("icy", "vapor", "mystic", "mystical", "magnetic", "ashen")):
            return "yellow"
        return "amber"

    def _gem_visual_color(self, gem: object) -> str:
        name = getattr(gem, "zenk_gem_name", "").lower()
        type_name = getattr(gem, "type", "").lower()
        palette = (
            ("fiery", "#cc4237"),
            ("heated", "#d35b32"),
            ("blood", "#b8242f"),
            ("watery", "#267ec8"),
            ("icy", "#8ecded"),
            ("vapor", "#d8dde5"),
            ("dusty", "#c9ad66"),
            ("earthen", "#8e6841"),
            ("airy", "#d5e4ef"),
            ("light", "#e1cb55"),
            ("finesse", "#d4c78a"),
            ("brilliant", "#53c5e4"),
            ("ashen", "#8f8496"),
            ("glacier", "#76c8db"),
            ("cinder", "#b64c2f"),
            ("magnetic", "#8560bd"),
            ("steaming", "#d18445"),
            ("radiant", "#e0d36f"),
            ("mystic", "#9b62d0"),
            ("mystical", "#9b62d0"),
            ("salt", "#c8c8bd"),
        )
        for key, color in palette:
            if key in name or key in type_name:
                return color
        category = getattr(gem, "category", "")
        return {
            "stat": "#d7bc6d",
            "hits": "#c84c54",
            "resist": "#5ba2d9",
            "skill": "#89c77c",
            "focus": "#9b62d0",
            "power": "#5fbfa8",
        }.get(category, ACCENT)

    def _bar_visual_motion(self, event: tk.Event) -> None:
        if not hasattr(self, "bar_visual"):
            return
        canvas = self.bar_visual
        canvas.delete("hover")
        canvas.configure(cursor="")
        self._clear_preview_hover()
        hit: tuple[int, int, int, int, str, str] | None = None
        for candidate in reversed(self._bar_visual_hitboxes):
            x1, y1, x2, y2, _label, _preview_key = candidate
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                hit = candidate
                break
        if not hit:
            for x1, y1, x2, y2, _direction in self._bar_visual_page_controls:
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    canvas.configure(cursor="hand2")
                    return
            return

        x1, y1, x2, y2, label, preview_key = hit
        canvas.configure(cursor="hand2")
        self._highlight_preview_line(preview_key)
        canvas.create_rectangle(x1 - 1, y1 - 1, x2 + 1, y2 + 1, outline=SPELL_GLOW, width=2, tags="hover")
        lines = [line[:46] for line in label.splitlines()[:3]]
        tooltip_width = 285
        tooltip_height = 13 + (len(lines) * 16)
        width = max(BAR_VISUAL_WIDTH, canvas.winfo_width())
        tx = min(event.x + 14, width - tooltip_width - 4)
        ty = max(4, event.y - tooltip_height - 8)
        canvas.create_rectangle(
            tx,
            ty,
            tx + tooltip_width,
            ty + tooltip_height,
            fill="#0a0d10",
            outline=SPELL_GLOW,
            width=1,
            tags="hover",
        )
        canvas.create_text(
            tx + 9,
            ty + 7,
            text="\n".join(lines),
            fill=TEXT,
            anchor=tk.NW,
            font=("Segoe UI", 9),
            tags="hover",
        )

    def _bar_visual_leave(self, event: tk.Event | None = None) -> None:
        if hasattr(self, "bar_visual"):
            self.bar_visual.delete("hover")
            self.bar_visual.configure(cursor="")
        self._clear_preview_hover()

    def _clear_preview_hover(self) -> None:
        if hasattr(self, "preview"):
            self.preview.tag_remove("bar_hover", "1.0", tk.END)

    def _highlight_preview_line(self, preview_key: str) -> None:
        if not hasattr(self, "preview"):
            return
        line_range = self._preview_line_ranges.get(preview_key)
        if not line_range:
            return
        start, end = line_range
        self.preview.tag_add("bar_hover", start, end)
        self.preview.see(start)

    def _bar_visual_wheel(self, event: tk.Event) -> None:
        if not self._bar_visual_items:
            return "break"
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self._scroll_bar_visual_pages(1)
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self._scroll_bar_visual_pages(-1)
        return "break"

    def _bar_visual_click(self, event: tk.Event) -> None:
        for x1, y1, x2, y2, direction in self._bar_visual_page_controls:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._scroll_bar_visual_pages(direction)
                return

    def _scroll_bar_visual_pages(self, direction: int) -> None:
        if not self._bar_visual_items:
            return
        try:
            entries = self._planned_bar_visual_entries(self._bar_visual_items)
        except Exception:
            return
        pages = list(range(1, 11))
        if not pages:
            return
        self.bar_visual_page_offset = (self.bar_visual_page_offset + direction) % len(pages)
        self._redraw_quickbar_visual()

    def _choose_input(self) -> None:
        start = path_from_field(self.last_input_dir.get(), Path.home()) if self.last_input_dir.get() else Path.home()
        path = filedialog.askopenfilename(
            title="Select spellcraft order",
            initialdir=str(start if start.exists() else Path.home()),
            filetypes=[("Spellcraft files", "*.txt *.forge *.log"), ("All files", "*.*")],
        )
        if path:
            self.input_path.set(display_user_path(path))
            self.last_input_dir.set(display_user_path(Path(path).parent))
            self.input_source.set("order")
            self._sync_export_name_with_path(Path(path), force=True)
            if not self.export_dir.get().strip():
                self.export_dir.set(display_user_path(Path(path).parent / "converted"))
            self._save_settings_from_fields()
            self._refresh_preview()

    def _choose_chat_log(self) -> None:
        current = path_from_field(self.chat_log_path.get(), default_chat_log_path()) if self.chat_log_path.get() else default_chat_log_path()
        start = current.parent if current.parent.exists() else Path.home()
        path = filedialog.askopenfilename(
            title="Select DAoC chat.log",
            initialdir=str(start),
            filetypes=[("Chat logs", "*.log"), ("All files", "*.*")],
        )
        if path:
            self.chat_log_path.set(display_user_path(path))
            self.input_source.set("chat")
            self._sync_export_name_with_path(Path(path), force=False)
            self._save_settings_from_fields()
            self._refresh_preview()

    def _refresh_chat_log(self) -> None:
        self.input_source.set("chat")
        self._save_settings_from_fields()
        self._refresh_preview()

    def _paste_clipboard_text(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showerror("Paste Text", "The clipboard does not contain text.")
            return
        if not text.strip():
            messagebox.showerror("Paste Text", "The clipboard text is empty.")
            return

        paste_path = SETTINGS_PATH.with_name("pasted_order.txt")
        paste_path.parent.mkdir(parents=True, exist_ok=True)
        paste_path.write_text(text, encoding="utf-8")
        self.input_source.set("paste")
        self._sync_export_name_with_path(paste_path, force=False)
        self._save_settings_from_fields()
        self._refresh_preview()

    def _clear_chat_log(self) -> None:
        raw_path = self.chat_log_path.get().strip()
        if not raw_path:
            messagebox.showerror("Clear Chat Log", "Select chat.log first.")
            return
        chat_path = path_from_field(raw_path)
        if chat_path.name.lower() != "chat.log":
            messagebox.showerror("Clear Chat Log", "This only clears a selected chat.log file.")
            return
        if not chat_path.exists():
            messagebox.showerror("Clear Chat Log", f"Chat log not found:\n{display_user_path(chat_path)}")
            return

        ok = messagebox.askyesno(
            "Clear Chat Log",
            "This will save a backup copy, then empty the selected chat.log.\n\n"
            f"{display_user_path(chat_path)}\n\nContinue?",
        )
        if not ok:
            return

        backup = chat_path.with_name(f"chat - DaocCraftToolBackup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        try:
            shutil.copy2(chat_path, backup)
            chat_path.write_text("", encoding="utf-8")
            self.preview.delete("1.0", tk.END)
            self.preview.insert(tk.END, "Chat log is empty.")
            self.status.delete("1.0", tk.END)
            self.status.insert(tk.END, f"Chat log cleared.\n\nBackup:\n{display_user_path(backup)}\n")
        except Exception as exc:
            self.status.delete("1.0", tk.END)
            self.status.insert(tk.END, str(exc))
            messagebox.showerror("Clear Chat Log", str(exc))

    def _choose_export_dir(self) -> None:
        current = path_from_field(self.export_dir.get()) if self.export_dir.get() else None
        if current and current.exists():
            start = current
        elif self.input_path.get() and path_from_field(self.input_path.get()).parent.exists():
            start = path_from_field(self.input_path.get()).parent
        else:
            start = Path.home()
        path = filedialog.askdirectory(title="Select export save folder", initialdir=str(start))
        if path:
            self.export_dir.set(display_user_path(path))
            self._save_settings_from_fields()

    def _choose_ini(self) -> None:
        current = path_from_field(self.ini_path.get()) if self.ini_path.get() else None
        eden_dir = path_from_field(self.eden_folder.get(), default_eden_dir()) if self.eden_folder.get() else default_eden_dir()
        if current and current.parent.exists():
            start = current.parent
        elif eden_dir.exists():
            start = eden_dir
        else:
            start = Path.home()
        path = filedialog.askopenfilename(
            title="Select Eden character INI",
            initialdir=str(start),
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
        )
        if path:
            self.ini_path.set(display_user_path(path))
            self._save_settings_from_fields()
            self._refresh_preview()

    def _open_eden_folder(self) -> None:
        folder = path_from_field(self.eden_folder.get(), default_eden_dir()) if self.eden_folder.get() else default_eden_dir()
        try:
            if not folder.exists():
                messagebox.showerror("Open Eden Folder", f"Eden folder was not found:\n{display_user_path(folder)}")
                return
            subprocess.Popen(["explorer", str(folder)])
        except Exception as exc:
            messagebox.showerror("Open Eden Folder", str(exc))

    def _find_eden_ini(self) -> None:
        folder = path_from_field(self.eden_folder.get(), default_eden_dir()) if self.eden_folder.get() else default_eden_dir()
        found = find_default_eden_ini(folder)
        if not found:
            messagebox.showerror("Find .ini", f"No Eden character .ini was found in:\n{display_user_path(folder)}")
            return
        self.eden_folder.set(display_user_path(found.parent))
        self.ini_path.set(display_user_path(found))
        self._save_settings_from_fields()
        self._refresh_preview()
        self.status.delete("1.0", tk.END)
        self.status.insert(tk.END, f"Selected Eden INI:\n{display_user_path(found)}\n")

    def _pasted_text_path(self) -> Path:
        return SETTINGS_PATH.with_name("pasted_order.txt")

    def _active_input_path(self) -> Path:
        source = self.input_source.get()
        if source == "chat":
            raw_path = self.chat_log_path.get().strip()
            if not raw_path:
                raise ValueError("Select chat.log first.")
            return path_from_field(raw_path)
        if source == "paste":
            paste_path = self._pasted_text_path()
            if not paste_path.exists() or not paste_path.read_text(encoding="utf-8", errors="ignore").strip():
                raise ValueError("Paste Discord or plain text first.")
            return paste_path

        raw_path = self.input_path.get().strip()
        if not raw_path:
            raise ValueError("Open an order file to preview it.")
        return path_from_field(raw_path)

    def _infer_realm_from_order_text(self, text: str) -> str | None:
        realm_match = re.search(r"\bRealm\s*[:=]\s*(Albion|Midgard|Hibernia)\b", text, flags=re.IGNORECASE)
        if realm_match:
            return canonical_realm(realm_match.group(1))

        class_names = sorted(CLASS_REALMS, key=len, reverse=True)
        class_pattern = "|".join(re.escape(name) for name in class_names)
        strong_patterns = (
            rf"\bClass\s*[:=]\s*({class_pattern})\b",
            rf"\bKlasse\s*[:=]\s*({class_pattern})\b",
            rf"\bCharacter Summary\b[^\n\r]*-\s*({class_pattern})\b",
            rf"\bSpellcraft Report\b[^\n\r]*-\s*({class_pattern})\b",
        )
        for pattern in strong_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                class_name = match.group(1).lower()
                if class_name == "mauler":
                    return None
                return CLASS_REALMS.get(class_name)

        for raw_line in text.splitlines()[:20]:
            line = raw_line.strip()
            if not line or line.lower().startswith(("name:", "jewel", "juwel", "gem ", "slot:", "source type:")):
                continue
            for class_name in class_names:
                if class_name == "hero":
                    continue
                if re.search(rf"\b{re.escape(class_name)}\b", line, flags=re.IGNORECASE):
                    return CLASS_REALMS[class_name]
        return None

    def _parse_items(self) -> tuple[list, WarningBag]:
        input_path = self._active_input_path()
        if input_path.is_dir():
            raise ValueError("Open an order file to preview it.")
        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {display_user_path(input_path)}")
        source_text = input_path.read_text(encoding="utf-8", errors="ignore")
        detected_realm = self._infer_realm_from_order_text(source_text)
        if detected_realm and detected_realm != canonical_realm(self.realm.get()):
            self.realm.set(detected_realm)
            self._draw_realm_selector()
            self._save_settings_from_fields()
        warnings = WarningBag()
        items = detect_and_parse(input_path, DEFAULT_SLOT_ORDER, warnings, self.realm.get())
        if not items:
            raise ValueError("No spellcrafted gems were found in the selected input.")
        fatal_warnings = blocking_warnings(warnings)
        if fatal_warnings:
            raise ValueError("Some gem text could not be imported safely:\n" + "\n".join(fatal_warnings))
        return items, warnings

    def _refresh_preview(self) -> None:
        self.preview.delete("1.0", tk.END)
        self._preview_line_ranges = {}
        try:
            items, warnings = self._parse_items()
        except Exception as exc:
            message = str(exc)
            self.preview.insert(tk.END, message)
            if message in {"Open an order file to preview it.", "Paste Discord or plain text first.", "Select chat.log first."}:
                self._draw_quickbar_visual(None, "Paste text, open an order file, or select chat.log.")
            else:
                self._draw_quickbar_visual(None, message)
            self.status.delete("1.0", tk.END)
            if message != "Open an order file to preview it.":
                self.status.insert(tk.END, f"Preview failed:\n{exc}\n")
            return

        quickbar_number = quickbar_hotkey_index(int(self.page.get()), int(self.slot.get()))
        for item in items:
            if self.include_separators.get():
                page, slot = hotkey_position(quickbar_number)
                preview_key = f"{page}:{slot}"
                start = self.preview.index(tk.INSERT)
                self.preview.insert(tk.END, f"Q{self.quickbar.get()} P{page} S{slot}: {separator_macro_label(item)}\n")
                self._preview_line_ranges[preview_key] = (start, self.preview.index(tk.INSERT))
                quickbar_number += 1
            else:
                self.preview.insert(tk.END, f"{item.title}\n")
            for gem in item.gems:
                page, slot = hotkey_position(quickbar_number)
                preview_key = f"{page}:{slot}"
                start = self.preview.index(tk.INSERT)
                self.preview.insert(tk.END, f"Q{self.quickbar.get()} P{page} S{slot}: {gem.zenk_gem_name} - {gem.zenk_display} +{gem.value}\n")
                self._preview_line_ranges[preview_key] = (start, self.preview.index(tk.INSERT))
                quickbar_number += 1
            self.preview.insert(tk.END, "\n")
        if warnings.messages:
            self.preview.insert(tk.END, "Warnings:\n")
            for warning in warnings.messages:
                self.preview.insert(tk.END, f"  {warning}\n")
        self._draw_quickbar_visual(items)
        self.status.delete("1.0", tk.END)
        self.status.insert(
            tk.END,
            "Preview refreshed. Nothing was written.\n\n"
            f"Realm: {self.realm.get()}\n"
            f"Spellcrafted items: {len(items)}\n"
            f"Gems: {sum(len(item.gems) for item in items)}\n",
        )

    def _save_settings_from_fields(self) -> None:
        last_input_dir = self.last_input_dir.get()
        typed_input = self.input_path.get().strip()
        if typed_input and path_from_field(typed_input).parent.exists():
            last_input_dir = display_user_path(path_from_field(typed_input).parent)
            self.last_input_dir.set(last_input_dir)
        settings = {
            "last_input_path": "",
            "last_input_dir": last_input_dir,
            "last_chat_log_path": display_user_path(self.chat_log_path.get()),
            "input_source": self.input_source.get(),
            "last_eden_dir": display_user_path(self.eden_folder.get()),
            "last_ini_path": display_user_path(self.ini_path.get()),
            "last_export_dir": display_user_path(self.export_dir.get()),
            "last_action": self.action.get(),
            "realm": self.realm.get(),
            "quickbar": self.quickbar.get(),
            "page": self.page.get(),
            "slot": self.slot.get(),
            "include_item_separators": self.include_separators.get(),
            "open_output_location": self.open_output_location.get(),
        }
        save_settings(settings)

    def _export_directory(self, input_path: Path) -> Path:
        folder = self.export_dir.get().strip()
        if folder:
            export_dir = path_from_field(folder)
        elif self.input_source.get() == "order":
            export_dir = input_path.parent / "converted"
        elif self.last_input_dir.get() and path_from_field(self.last_input_dir.get()).exists():
            export_dir = path_from_field(self.last_input_dir.get()) / "converted"
        else:
            export_dir = input_path.parent / "converted"
        self.export_dir.set(display_user_path(export_dir))
        return export_dir

    def _export_output_path(self, input_path: Path, action: str) -> Path:
        return self._export_directory(input_path) / self._export_file_name(input_path, action)

    def _open_file_location(self, path: Path) -> None:
        try:
            subprocess.Popen(["explorer", f"/select,{path}"])
        except Exception as exc:
            self.status.insert(tk.END, f"\nCould not open file location:\n{exc}\n")

    def _run_file_action(self) -> None:
        self._run()

    def _run_bars_action(self) -> None:
        self._run("bars")

    def _run(self, forced_action: str | None = None) -> None:
        self.status.delete("1.0", tk.END)
        try:
            items, warnings = self._parse_items()
            action = forced_action or self.action.get()
            input_path = self._active_input_path()
            if action == "bars":
                start = quickbar_hotkey_index(int(self.page.get()), int(self.slot.get()))
                count = planned_hotkey_count(items, bool(self.include_separators.get()))
                end = start + count - 1
                start_page, start_slot = hotkey_position(start)
                end_page, end_slot = hotkey_position(end)
                ok = messagebox.askyesno(
                    "Confirm bar setup",
                    "This will modify the selected Eden INI after saving a timestamped backup first.\n\n"
                    f"{display_user_path(self.ini_path.get())}\n\n"
                    f"Quickbar {self.quickbar.get()} range: Page {start_page} Slot {start_slot} "
                    f"through Page {end_page} Slot {end_slot}\n"
                    f"Other hotkeys, bars, and character settings are left as-is."
                    "\n\nContinue?",
                )
                if not ok:
                    return
            output_path: Path | None = None
            if action == "forge":
                forge_path = self._export_output_path(input_path, action)
                forge_path.parent.mkdir(parents=True, exist_ok=True)
                forge = render_forge(items, self._export_title(input_path), self.realm.get(), "Eden")
                forge_path.write_text(json.dumps(forge, indent=2), encoding="utf-8")
                self.status.insert(tk.END, f"Wrote:\n{display_user_path(forge_path)}\n")
                output_path = forge_path
            elif action == "zenk":
                zenk_path = self._export_output_path(input_path, action)
                zenk_path.parent.mkdir(parents=True, exist_ok=True)
                zenk_path.write_text(render_zenk_report(items, self._export_title(input_path)), encoding="utf-8")
                self.status.insert(tk.END, f"Wrote:\n{display_user_path(zenk_path)}\n")
                output_path = zenk_path
            elif action == "bars":
                result = setup_bars(
                    items=items,
                    ini_path=path_from_field(self.ini_path.get()),
                    quickbar=int(self.quickbar.get()),
                    page=int(self.page.get()),
                    slot=int(self.slot.get()),
                    realm=self.realm.get(),
                    include_item_separators=bool(self.include_separators.get()),
                )
                self.status.insert(
                    tk.END,
                    f"Updated:\n{display_user_path(result.ini_path)}\n\nBackup:\n{display_user_path(result.backup_path)}\n\n",
                )
                self.status.insert(
                    tk.END,
                    f"Wrote {result.hotkey_count} quickbar slot(s), {result.macro_count} item separator(s).\n",
                )
                if result.backup_cleanup_count:
                    self.status.insert(
                        tk.END,
                        f"Cleaned up {result.backup_cleanup_count} older backup file(s); newest 3 kept.\n",
                    )
            else:
                raise ValueError(f"Unknown action: {action}")

            if warnings.messages:
                self.status.insert(tk.END, "\nWarnings:\n")
                for warning in warnings.messages:
                    self.status.insert(tk.END, f"  {warning}\n")
            self._save_settings_from_fields()
            if output_path and self.open_output_location.get():
                self._open_file_location(output_path)
            messagebox.showinfo("Done", "Craft order action completed.")
        except Exception as exc:
            self.status.insert(tk.END, str(exc))
            messagebox.showerror(APP_NAME, str(exc))

    def _restore_backup(self) -> None:
        raw_target = self.ini_path.get().strip()
        if not raw_target:
            messagebox.showerror("Restore Backup", "Select the Eden INI to restore into first.")
            return
        target = path_from_field(raw_target)
        start = target.parent if target.parent.exists() else Path.home()
        backup = filedialog.askopenfilename(
            title="Select INI backup to restore",
            initialdir=str(start),
            filetypes=[("INI backups", "*.ini"), ("All files", "*.*")],
        )
        if not backup:
            return
        ok = messagebox.askyesno(
            "Restore Backup",
            "This will replace the selected Eden INI with the backup you choose.\n\n"
            f"Target:\n{display_user_path(target)}\n\nBackup:\n{display_user_path(backup)}\n\nContinue?",
        )
        if not ok:
            return
        try:
            shutil.copy2(backup, target)
            self.status.delete("1.0", tk.END)
            self.status.insert(tk.END, f"Restored backup:\n{display_user_path(backup)}\n\nTo:\n{display_user_path(target)}\n")
            messagebox.showinfo("Restore Backup", "Backup restored.")
        except Exception as exc:
            self.status.delete("1.0", tk.END)
            self.status.insert(tk.END, str(exc))
            messagebox.showerror("Restore Backup", str(exc))


if __name__ == "__main__":
    CraftToolApp().mainloop()
