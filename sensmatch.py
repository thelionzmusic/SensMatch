#!/usr/bin/env python3
"""
SensMatch - FPS sensitivity converter + Borderlands 2 / The Pre-Sequel
below-minimum sensitivity tool.

Borderlands' menu slider stops at 10, but the game's console command
`setsensitivity` accepts any value. Borderlands 2 ignores key binds in its ini
files, so SensMatch switches the console on once and then, when you press your
chosen key in game, types the command for you. The game's turn speed is measured
once (and can be shipped inside the exe by build.bat) so nothing is guessed.

Converter: any OS. Borderlands features: Windows only. No third-party packages.
"""
import base64
import json
import os
import re
import shutil
import stat
import sys
import threading
import time
import webbrowser
from datetime import datetime

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog

APP_NAME = "SensMatch"
VERSION = "3.0"
IS_WINDOWS = sys.platform == "win32"

# "Buy me a coffee" goes here. To hide your email, swap in a paypal.me link,
# e.g. "https://paypal.me/yourname"
DONATE_URL = "https://www.paypal.com/donate/?business=redetonation%40me.com&no_recurring=0"

ICON_PNG = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAACsElEQVR42u1bO47CMBBNRmnoCQ0U0FJxmByFY+xROMxWaaGABugp2WLllTfE9th54xgTS0gIHHvem68/KYoPbyW343yxeqYO5n49l3AC3gH4ECJKLvDleps88Mup9SaidIFHAr+c2uJ22Lz8XjdH+DxcEigW+JhNl3u+WD1tbky5gTfJbyKBOA/nTAJ1/8wFPJcE+vRCiHLWPscKollAN0f7/i/VqjFB2/pLW+N8sXrer+eSpID7gu8WSCFjJGEBXaF1YHVzZJOg+l5Orag1VDGAhzT1fN0c/8aWIIJSBG8aS8IlKiR4JHCbNSAtgVIB74oP+hxIS6jQZtrXdvsZq1jZ7X+/f389rHNxyBK3AI4WdvsZC3zfcy6QKCsoQ0phjumHAOduoOguEyKzvllCEqaPAK/AmSwBFXAJbfoo8BwSEK5AaO3HWM0hZYCuBdDa902T4gSMtWSVlOslCyBAuiJzdw5bf5Q8pixQSfiVKmi4qa1uWlE/t8lDsU21D9DtsBnNvaZN0YmAD2+VRL41BbTfqq4vCJoPRyXl8V4MqUA19ITXJw2i5oYshtQkfVrxSVfL9fbfZ0j5PfRofQqCyMFsOzlS+wLRCbC5gcR6wTYe4mYJ3AWQVZ0t8KFa0JYYR7g+7fjcEQoZXzwL+LjCEEtAg/cqhNDuUBQPVjET44AFHgNcVqAD4oDi9ENfqRscBLkkhBQ50uBhLqB2XBQJaBP2PQMYJQ3qZS1yA1NpXeqOADwIoqxBUuviWUAJrRPhAzoG8ChpUAfhqgkkAlxSq0EXuLHuKJIqCSUWMqk0G65pP0BfGORoBS48FGNNnyJ4pXDq+zEHErjyk4mZdybBJbeO0fnS1NhpSkLrTgJMJOTQum+REbdjjuCddUBOJJiwZPXucIgSvTX8LkTk6MIi7QejKrx0ioSYdwAAAABJRU5ErkJggg=="

# --------------------------------------------------------------------------
# Game data. "yaw" = degrees turned per mouse count at in-game sensitivity 1.0
# (hipfire). Override/extend with games.json in the data folder.
# --------------------------------------------------------------------------
DEFAULT_GAMES = {
    "Valorant": {"yaw": 0.07, "note": ""},
    "Counter-Strike 2": {"yaw": 0.022, "note": "Counter-Strike 2 assumes the default m_yaw of 0.022."},
    "Apex Legends": {"yaw": 0.022, "note": "Apex Legends is hipfire only; ADS multipliers are separate."},
    "Fortnite": {"yaw": 0.005555, "note": "Fortnite uses the in-game X sensitivity as a percentage, e.g. 6.4."},
    "Call of Duty": {"yaw": 0.0066, "note": "Call of Duty covers MW2019 onward and Warzone, hipfire."},
    "Overwatch 2": {"yaw": 0.0066, "note": ""},
    "Rainbow Six Siege": {"yaw": 0.00572958,
                          "note": "Rainbow Six Siege assumes the default multiplier of 0.02."},
    "Marvel Rivals": {"yaw": 0.0175, "note": ""},
    "Destiny 2": {"yaw": 0.0066, "note": "Destiny 2 is hipfire only."},
    "Team Fortress 2": {"yaw": 0.022, "note": "Team Fortress 2 assumes the default m_yaw of 0.022."},
}

BL_GAMES = {
    "Borderlands 2": r"My Games\Borderlands 2\WillowGame\Config\WillowInput.ini",
    "Borderlands: The Pre-Sequel":
        r"My Games\Borderlands The Pre-Sequel\WillowGame\Config\WillowInput.ini",
}
# Keys SensMatch listens for (name -> Windows virtual-key code)
APPLY_KEYS = {"Home": 0x24, "End": 0x23, "Insert": 0x2D, "PageUp": 0x21, "PageDown": 0x22,
              "Pause": 0x13}
# Unreal key names we can press to open the console
UE3_VK = {"Tilde": 0xC0, "Insert": 0x2D, "Home": 0x24, "End": 0x23, "PageUp": 0x21,
          "PageDown": 0x22, "Delete": 0x2E, "Backslash": 0xDC, "Quote": 0xDE,
          "Semicolon": 0xBA, "Tab": 0x09, **{f"F{i}": 0x6F + i for i in range(1, 13)}}
DEFAULT_CONSOLE_KEY = "Tilde"
SENS_CMD = "setsensitivity"
OLD_SENS_CMD = "set WillowPlayerInput MouseSensitivity"
CAL_VALUE = 10.0   # known test value set during the one-time measurement


def data_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def documents_candidates():
    """Every place a Documents folder commonly lives on Windows, including
    OneDrive redirection, so the ini is found on anyone's PC."""
    found = []
    if IS_WINDOWS:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:
            found.append(buf.value)
    home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    found.append(os.path.join(home, "Documents"))
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if os.environ.get(var):
            found.append(os.path.join(os.environ[var], "Documents"))
    found.append(os.path.join(home, "OneDrive", "Documents"))
    out, seen = [], set()
    for d in found:
        key = os.path.normcase(os.path.normpath(d))
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def find_ini(game):
    """Return (path, number_of_copies_found). If the game has run in more than
    one place, pick the copy the game wrote to most recently."""
    rel = BL_GAMES[game]
    hits = [os.path.join(d, rel) for d in documents_candidates()]
    hits = [p for p in hits if os.path.isfile(p)]
    if hits:
        return max(hits, key=os.path.getmtime), len(hits)
    return os.path.join(documents_candidates()[0], rel), 0


def load_games():
    games = {k: dict(v) for k, v in DEFAULT_GAMES.items()}
    path = os.path.join(data_dir(), "games.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                for name, info in json.load(f).items():
                    if float(info.get("yaw", 0)) > 0:
                        games[name] = {"yaw": float(info["yaw"]), "note": info.get("note", "")}
        except (OSError, ValueError, AttributeError):
            pass
    return games


def load_config():
    try:
        with open(os.path.join(data_dir(), "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    cfg.setdefault("calibrations", {})
    if cfg.get("version", 0) < 3:
        # Measurements from before v3 relied on key binds, which Borderlands 2
        # ignores, so they were taken at the wrong sensitivity. Start fresh.
        cfg["calibrations"] = {}
        cfg["version"] = 3
        try:
            save_config(cfg)
        except OSError:
            pass
    return cfg


def baked_path():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "baked.json")


def load_baked():
    """Turn rates measured by whoever built the exe, so users don't have to."""
    try:
        with open(baked_path(), encoding="utf-8") as f:
            return {k: v for k, v in json.load(f).items() if float(v.get("yaw", 0)) > 0}
    except (OSError, ValueError, AttributeError):
        return {}


def save_config(cfg):
    with open(os.path.join(data_dir(), "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def cm_per_360(deg_count, dpi):
    return 360.0 / (deg_count * dpi) * 2.54


def convert(src_yaw, src_sens, src_dpi, dst_yaw, dst_dpi):
    return src_yaw * src_sens * src_dpi / (dst_yaw * dst_dpi)


def fmt(x):
    return f"{x:.6g}"


# ---- UE3 ini editing ------------------------------------------------------
_SECTION = re.compile(r"^\s*\[(.+?)\]\s*$")


def _section_bounds(lines, section):
    start, end = None, len(lines)
    for i, line in enumerate(lines):
        m = _SECTION.match(line)
        if m:
            if start is not None:
                end = i
                break
            if m.group(1).strip().lower() == section.lower():
                start = i
    return start, end


def _insert_in_section(lines, section, new_line):
    start, end = _section_bounds(lines, section)
    if start is None:
        lines += ["", f"[{section}]", new_line]
        return
    ins = end
    while ins > start + 1 and not lines[ins - 1].strip():
        ins -= 1
    lines.insert(ins, new_line)


def ini_set(text, section, key, value):
    lines = text.splitlines()
    start, end = _section_bounds(lines, section)
    if start is not None:
        for i in range(start + 1, end):
            if lines[i].split("=", 1)[0].strip().lower() == key.lower():
                lines[i] = f"{key}={value}"
                return "\n".join(lines) + "\n"
    _insert_in_section(lines, section, f"{key}={value}")
    return "\n".join(lines) + "\n"


def ini_get(text, section, key):
    lines = text.splitlines()
    start, end = _section_bounds(lines, section)
    if start is None:
        return None
    for i in range(start + 1, end):
        k, _, v = lines[i].partition("=")
        if k.strip().lower() == key.lower():
            return v.strip()
    return None


def ini_remove_old_binds(text):
    """Remove key binds written by older SensMatch versions (they don't work in BL2)."""
    lines = [l for l in text.splitlines()
             if not (l.strip().lower().startswith("bindings=") and
                     OLD_SENS_CMD.lower() in l.lower())]
    return "\n".join(lines) + "\n"


def find_console_key(text):
    """Return (value, section) of the ConsoleKey setting, searching every section
    (preferring [Engine.Console]); value is '' if the line is there but empty."""
    best = None
    section = None
    for line in text.splitlines():
        m = _SECTION.match(line)
        if m:
            section = m.group(1).strip()
            continue
        k, sep, v = line.partition("=")
        if sep and k.strip().lower() == "consolekey":
            hit = (v.strip(), section)
            if section and section.lower() == "engine.console":
                return hit
            best = best or hit
    return best or (None, None)


def ini_status(path):
    """What SensMatch can see about a WillowInput.ini, for the setup screen."""
    info = {"path": path, "exists": os.path.exists(path), "readonly": False,
            "console": None, "raw": None, "section": None, "error": None}
    if not info["exists"]:
        return info
    info["readonly"] = not os.access(path, os.W_OK)
    try:
        _, text, _, _ = read_ini(path)
        raw, sec = find_console_key(text)
        info["raw"], info["section"] = raw, sec
        if raw:
            name = next((k for k in UE3_VK if k.lower() == raw.lower()), None)
            info["console"] = name
    except OSError as e:
        info["error"] = getattr(e, "strerror", None) or str(e)
    return info


def ini_enable_console(text, key):
    """Set ConsoleKey wherever the file already has it; otherwise add it to [Engine.Console]."""
    lines = text.splitlines()
    done = False
    for i, line in enumerate(lines):
        k, sep, _ = line.partition("=")
        if sep and k.strip().lower() == "consolekey":
            lines[i] = f"ConsoleKey={key}"
            done = True
    text = "\n".join(lines) + "\n"
    return text if done else ini_set(text, "Engine.Console", "ConsoleKey", key)


def read_ini(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        enc = "utf-16"
    elif raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        enc = "latin-1"
    text = raw.decode(enc)
    nl = "\r\n" if "\r\n" in text else "\n"
    return raw, text.replace("\r\n", "\n"), enc, nl


def backup_ini(path, raw):
    """Back up to SensMatch's own folder, so nothing new is created in Documents."""
    folder = os.path.join(data_dir(), "backups")
    os.makedirs(folder, exist_ok=True)
    parts = os.path.normpath(path).split(os.sep)
    game = re.sub(r"[^A-Za-z0-9]+", "-", parts[-4] if len(parts) >= 4 else "game").strip("-")
    backup = os.path.join(folder, f"WillowInput-{game}-{datetime.now():%Y%m%d-%H%M%S}.ini")
    with open(backup, "wb") as f:
        f.write(raw)
    return backup


def write_ini(path, text, enc, nl):
    """Rewrite the existing file in place (no delete/rename/new files)."""
    was_ro = not os.access(path, os.W_OK)
    if was_ro:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    try:
        with open(path, "r+b") as f:
            f.write(text.replace("\n", nl).encode(enc))
            f.truncate()
    finally:
        if was_ro:
            os.chmod(path, stat.S_IREAD)


# ---- Windows input ----------------------------------------------------------
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    winmm = ctypes.WinDLL("winmm")

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.c_size_t)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    def send_mouse_dx(dx):
        inp = INPUT(type=0, u=_INPUTUNION(mi=MOUSEINPUT(dx, 0, 0, 0x0001, 0, 0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def key_down(vk):
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)

    _EXTENDED = {0x21, 0x22, 0x23, 0x24, 0x2D, 0x2E}

    def send_key(vk, up=False):
        flags = (0x0002 if up else 0) | (0x0001 if vk in _EXTENDED else 0)
        scan = user32.MapVirtualKeyW(vk, 0)
        inp = INPUT(type=1, u=_INPUTUNION(ki=KEYBDINPUT(vk, scan, flags, 0, 0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def tap(vk, shift=False):
        if shift:
            send_key(0x10)
        send_key(vk)
        time.sleep(0.012)
        send_key(vk, up=True)
        if shift:
            send_key(0x10, up=True)
        time.sleep(0.012)

    def type_console_command(console_vk, text):
        """Open the game console, type a command, press Enter."""
        tap(console_vk)
        time.sleep(0.15)
        for ch in text:
            r = user32.VkKeyScanW(ord(ch))
            if r == -1 or r == 0xFFFF:
                continue
            tap(r & 0xFF, shift=bool((r >> 8) & 1))
        tap(0x0D)

    def foreground_bl_game():
        hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        t = buf.value.lower()
        if "pre-sequel" in t:
            return "Borderlands: The Pre-Sequel"
        if "borderlands 2" in t:
            return "Borderlands 2"
        return None


class HotkeyWorker(threading.Thread):
    """Background helper.
    Always: when Borderlands is focused and the apply key is pressed, types
            'setsensitivity <value>' into the game console.
    mode "measure": F6 fast turn, F7 slow turn, F8 back one count, F9 reset, F10 done.
    mode "verify":  F11 turns exactly verify_target counts."""
    VK = {"F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A}
    FAST, VERIFY_CHUNK = 20, 10

    def __init__(self):
        super().__init__(daemon=True)
        self.mode = "off"
        self.running = True
        self.counts = 0
        self.finished = None
        self.verify_target = 0
        self.verify_total = 0
        self.verify_sent = 0
        self.pending = 0
        self.apply_vk = APPLY_KEYS["Home"]
        self.commands = {}      # game -> (console_vk, value or None)
        self.override = None    # test value used while measuring
        self.type_now = False
        self.typed = None       # (game, value, time) of the last command typed
        self._prev = {}
        self._slow = 0

    def _pressed(self, vk):
        d = key_down(vk)
        was = self._prev.get(vk, False)
        self._prev[vk] = d
        return d and not was

    def run(self):
        winmm.timeBeginPeriod(1)
        try:
            while self.running:
                if self.pending > 0:
                    n = min(self.VERIFY_CHUNK, self.pending)
                    send_mouse_dx(n)
                    self.pending -= n
                    self.verify_sent += n
                else:
                    if self.mode == "measure":
                        self._measure()
                    elif self.mode == "verify" and self._pressed(self.VK["F11"]) \
                            and self.verify_target > 0:
                        self.verify_total = self.pending = self.verify_target
                        self.verify_sent = 0
                    if self._pressed(self.apply_vk) or self.type_now:
                        self.type_now = False
                        self._apply()
                time.sleep(0.001)
        finally:
            winmm.timeEndPeriod(1)

    def _apply(self):
        game = foreground_bl_game()
        if not game or game not in self.commands:
            return
        console_vk, value = self.commands[game]
        value = self.override if self.override is not None else value
        if value is None or not console_vk:
            return
        t0 = time.time()
        while key_down(self.apply_vk) and time.time() - t0 < 2:
            time.sleep(0.01)
        time.sleep(0.05)
        type_console_command(console_vk, f"{SENS_CMD} {fmt(value)}")
        self.typed = (game, value, time.time())

    def _measure(self):
        if self._pressed(self.VK["F9"]):
            self.counts = 0
        if self._pressed(self.VK["F10"]):
            self.finished = self.counts
        if self._pressed(self.VK["F8"]):
            send_mouse_dx(-1)
            self.counts -= 1
        if key_down(self.VK["F6"]):
            send_mouse_dx(self.FAST)
            self.counts += self.FAST
        elif key_down(self.VK["F7"]):
            self._slow += 1
            if self._slow % 3 == 0:
                send_mouse_dx(1)
                self.counts += 1


# ==========================================================================
# Look: cel-shaded. Thick ink outlines, hard offset shadows, loot-yellow.
# ==========================================================================
INK = "#14161c"
BG = "#252b38"
PANEL = "#2f3646"
FIELD = "#3a4256"
TEXT = "#f2ead8"
MUTED = "#a3abbd"
YELLOW = "#ffc23d"
YELLOW_HI = "#ffd773"
ORANGE = "#ff7a45"
FIELD_HI = "#465069"

S = 1.0          # UI scale, set at startup from the screen DPI
F = {}           # font families, set at startup


def px(n):
    return max(1, round(n * S))


def pick_family(root, *names):
    fams = set(tkfont.families(root))
    for n in names:
        if n in fams:
            return n
    return "TkDefaultFont"


def label(parent, text="", size=10, color=TEXT, family="body", bold=False, **kw):
    bg = kw.pop("bg", parent.cget("bg"))
    font = (F[family], size, "bold") if bold else (F[family], size)
    return tk.Label(parent, text=text, fg=color, bg=bg, font=font, **kw)


class CelButton(tk.Canvas):
    """Chunky button with an ink outline and a hard drop shadow that it
    presses down into."""
    STYLES = {
        "primary": (YELLOW, YELLOW_HI, INK),
        "secondary": (FIELD, FIELD_HI, TEXT),
        "danger": (ORANGE, "#ff9a6e", INK),
    }

    def __init__(self, parent, text, command=None, kind="primary", size=11, width=None, pad=(16, 7)):
        self.off = px(4)
        self.font = tkfont.Font(family=F["display"], size=size)
        self.command = command
        self.kind = kind
        w = width or self.font.measure(text) + px(pad[0]) * 2
        h = self.font.metrics("linespace") + px(pad[1]) * 2
        self.w, self.h = w, h
        super().__init__(parent, width=w + self.off, height=h + self.off, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        lw = px(2)
        self.create_rectangle(self.off, self.off, w + self.off - 1, h + self.off - 1,
                              fill=INK, outline=INK)
        self.face = self.create_rectangle(lw // 2, lw // 2, w - lw // 2 - 1, h - lw // 2 - 1,
                                          outline=INK, width=lw)
        self.txt = self.create_text(w // 2, h // 2, text=text, font=self.font)
        self._down = False
        self._paint(False)
        self.bind("<Enter>", lambda e: self._paint(True))
        self.bind("<Leave>", lambda e: self._leave())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _paint(self, hover):
        face, hi, fg = self.STYLES[self.kind]
        self.itemconfigure(self.face, fill=hi if hover else face)
        self.itemconfigure(self.txt, fill=fg)

    def _leave(self):
        if self._down:
            self._shift(-1)
            self._down = False
        self._paint(False)

    def _shift(self, sign):
        self.move(self.face, sign * self.off, sign * self.off)
        self.move(self.txt, sign * self.off, sign * self.off)

    def _press(self, _):
        self._down = True
        self._shift(1)

    def _release(self, e):
        if not self._down:
            return
        self._down = False
        self._shift(-1)
        if 0 <= e.x <= self.w + self.off and 0 <= e.y <= self.h + self.off and self.command:
            self.command()

    def configure_button(self, text=None, kind=None):
        if text is not None:
            self.itemconfigure(self.txt, text=text)
        if kind is not None:
            self.kind = kind
        self._paint(False)


class Card(tk.Frame):
    """Panel with an ink outline and a hard offset shadow. Put content in .body."""

    def __init__(self, parent, title=None, step=None, pad=16):
        super().__init__(parent, bg=parent.cget("bg"))
        off = px(5)
        shadow = tk.Frame(self, bg=INK)
        shadow.grid(row=0, column=0, sticky="nsew", padx=(off, 0), pady=(off, 0))
        self.body = tk.Frame(self, bg=PANEL, highlightthickness=px(3),
                             highlightbackground=INK, highlightcolor=INK,
                             padx=px(pad), pady=px(pad - 2))
        self.body.grid(row=0, column=0, sticky="nsew", padx=(0, off), pady=(0, off))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        if title:
            head = tk.Frame(self.body, bg=PANEL)
            head.pack(fill="x", pady=(0, px(8)))
            if step is not None:
                d = px(26)
                c = tk.Canvas(head, width=d + px(3), height=d + px(3), bg=PANEL,
                              highlightthickness=0)
                c.create_oval(px(3), px(3), d + px(2), d + px(2), fill=INK, outline=INK)
                c.create_oval(1, 1, d, d, fill=YELLOW, outline=INK, width=px(2))
                c.create_text(d // 2 + 1, d // 2 + 1, text=str(step), fill=INK,
                              font=(F["display"], 11))
                c.pack(side="left", padx=(0, px(10)))
            label(head, title, 15, family="display").pack(side="left")


def entry(parent, var, width=10, mono=False, readonly=False, size=12):
    e = tk.Entry(parent, textvariable=var, width=width, relief="flat",
                 bg=FIELD, fg=TEXT, insertbackground=YELLOW,
                 disabledbackground=FIELD, readonlybackground=FIELD,
                 selectbackground=YELLOW, selectforeground=INK,
                 highlightthickness=px(2), highlightbackground=INK, highlightcolor=YELLOW,
                 font=(F["mono" if mono else "body"], size))
    if readonly:
        e.configure(state="readonly")
    return e


def combo(parent, var, values, width=24):
    return ttk.Combobox(parent, textvariable=var, values=values, state="readonly",
                        width=width, style="Cel.TCombobox", font=(F["body"], 11))


class Dial(tk.Canvas):
    """The 360° ring: shows counts turned against the target turn."""

    def __init__(self, parent, size=230):
        self.sz = px(size)
        super().__init__(parent, width=self.sz, height=self.sz, bg=PANEL, highlightthickness=0)
        c, w = self.sz / 2, px(20)
        r = c - w / 2 - px(10)
        self.c, self.r, self.w = c, r, w
        self.create_oval(c - r - w / 2 - px(2), c - r - w / 2 - px(2),
                         c + r + w / 2 + px(2), c + r + w / 2 + px(2), outline=INK, width=px(3))
        self.create_oval(c - r, c - r, c + r, c + r, outline=FIELD, width=w)
        self.arc = self.create_arc(c - r, c - r, c + r, c + r, start=90, extent=0,
                                   style="arc", outline=YELLOW, width=w)
        self.create_oval(c - r + w / 2 + px(1), c - r + w / 2 + px(1),
                         c + r - w / 2 - px(1), c + r - w / 2 - px(1), outline=INK, width=px(3))
        import math
        for deg in range(0, 360, 30):
            a = math.radians(deg)
            r1, r2 = r - w / 2 + px(2), r + w / 2 - px(2)
            self.create_line(c + r1 * math.cos(a), c + r1 * math.sin(a),
                             c + r2 * math.cos(a), c + r2 * math.sin(a), fill=INK, width=px(2))
        self.value = self.create_text(c, c - px(10), text="0", fill=TEXT,
                                      font=(F["display"], 30))
        self.caption = self.create_text(c, c + px(24), text="counts", fill=MUTED,
                                        font=(F["body"], 10))

    def set(self, value, frac, caption, color=YELLOW):
        frac = max(0.0, min(frac, 0.9999))
        self.itemconfigure(self.arc, extent=-360 * frac, outline=color)
        self.itemconfigure(self.value, text=f"{value:,}")
        self.itemconfigure(self.caption, text=caption)


class ScrollArea(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                 style="Cel.Vertical.TScrollbar")
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", self._wheel))
        self.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120), "units")


def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Cel.TCombobox", fieldbackground=FIELD, background=FIELD_HI,
                    foreground=TEXT, arrowcolor=YELLOW, bordercolor=INK,
                    lightcolor=FIELD, darkcolor=FIELD, padding=px(5), arrowsize=px(14))
    style.map("Cel.TCombobox",
              fieldbackground=[("readonly", FIELD)], foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", TEXT)],
              background=[("active", YELLOW), ("readonly", FIELD_HI)],
              arrowcolor=[("active", INK)], bordercolor=[("focus", YELLOW)])
    style.configure("Cel.Vertical.TScrollbar", background=FIELD, troughcolor=BG,
                    bordercolor=BG, arrowcolor=YELLOW, lightcolor=FIELD, darkcolor=FIELD)
    root.option_add("*TCombobox*Listbox.background", FIELD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", YELLOW)
    root.option_add("*TCombobox*Listbox.selectForeground", INK)
    root.option_add("*TCombobox*Listbox.font", (F["body"], 11))
    root.option_add("*TCombobox*Listbox.borderWidth", 0)


def dark_titlebar(root):
    if not IS_WINDOWS:
        return
    try:
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        on = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(on), 4)
        r, g, b = int(BG[1:3], 16), int(BG[3:5], 16), int(BG[5:7], 16)
        col = ctypes.c_int(r | (g << 8) | (b << 16))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(col), 4)
    except Exception:
        pass


class ManualFixDialog(tk.Toplevel):
    """Shown when Windows refuses the write: explains why and offers a Notepad fallback."""

    def __init__(self, app, path, step, err, steps):
        super().__init__(app)
        self.app, self.path = app, path
        self.title("Couldn't change WillowInput.ini")
        self.configure(bg=BG)
        self.transient(app)
        self.resizable(False, False)
        card = Card(self, "Windows blocked the change", pad=18)
        card.pack(padx=px(18), pady=px(18))
        b = card.body
        reason = getattr(err, "strerror", None) or str(err)
        label(b, f"SensMatch couldn't {step} the file: {reason}.", 10, ORANGE, justify="left",
              wraplength=px(560)).pack(anchor="w")
        label(b, "This is usually Controlled folder access in Windows Security, which stops "
              "unknown apps from changing files in Documents. OneDrive syncing the Documents "
              "folder can cause it too. You have two ways round it.", 10, justify="left",
              wraplength=px(560)).pack(anchor="w", pady=(px(8), px(10)))

        label(b, "Option 1: allow SensMatch", 13, family="display").pack(anchor="w")
        label(b, "Windows Security > Virus & threat protection > Manage ransomware protection > "
              "Allow an app through Controlled folder access > Add an allowed app. Pick "
              "SensMatch.exe (or python.exe if you run the .py), then try again.", 10, MUTED,
              justify="left", wraplength=px(560)).pack(anchor="w", pady=(px(2), px(12)))

        label(b, "Option 2: make the change in Notepad", 13, family="display").pack(anchor="w")
        label(b, "Close the game, open the file, make these changes, and save.", 10, MUTED
              ).pack(anchor="w", pady=(px(2), px(6)))
        for i, (what, line) in enumerate(steps):
            label(b, what, 10, justify="left", wraplength=px(560)).pack(anchor="w", pady=(px(4), px(2)))
            r = tk.Frame(b, bg=PANEL)
            r.pack(fill="x")
            v = tk.StringVar(value=line)
            entry(r, v, 52, mono=True, readonly=True, size=10).pack(side="left", fill="x", expand=True)
            CelButton(r, "Copy", lambda l=line: self.app.copy(l, "the line"), kind="secondary",
                      size=10).pack(side="left", padx=(px(8), 0))

        btns = tk.Frame(b, bg=PANEL)
        btns.pack(fill="x", pady=(px(16), 0))
        CelButton(btns, "Open in Notepad", self._notepad).pack(side="left")
        CelButton(btns, "Close", self.destroy, kind="secondary").pack(side="left", padx=px(12))
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_width()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        dark_titlebar(self)
        self.grab_set()

    def _notepad(self):
        try:
            if IS_WINDOWS:
                import subprocess
                subprocess.Popen(["notepad.exe", self.path])
            else:
                self.app.toast(self.path)
        except OSError as e:
            self.app.toast(f"Couldn't open Notepad: {e}", error=True)


class ConsoleKeyDialog(tk.Toplevel):
    """Skip the ini: tell SensMatch which key already opens the console."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Your console key")
        self.configure(bg=BG)
        self.transient(app)
        self.resizable(False, False)
        card = Card(self, "Which key opens your console?", pad=20)
        card.pack(padx=px(18), pady=px(18))
        b = card.body
        label(b, "Start Borderlands and try the key below. If a text bar appears at the bottom of "
              "the screen, that's your console key. Pick it here and SensMatch will skip the "
              "file step.", 10, justify="left", wraplength=px(440)).pack(anchor="w")
        label(b, "On UK keyboards, Tilde is usually the @ key (next to Enter). On US keyboards "
              "it's the key under Esc.", 10, MUTED, justify="left", wraplength=px(440)
              ).pack(anchor="w", pady=(px(8), 0))
        self.var = tk.StringVar(value=DEFAULT_CONSOLE_KEY)
        app.field(b, "Console key", lambda f: combo(f, self.var, list(UE3_VK), 12)
                  ).pack(anchor="w", pady=(px(12), 0))
        r = tk.Frame(b, bg=PANEL)
        r.pack(anchor="w", pady=(px(16), 0))
        CelButton(r, "Use this key", self._save).pack(side="left")
        CelButton(r, "Cancel", self.destroy, kind="secondary").pack(side="left", padx=px(10))
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_width()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        dark_titlebar(self)
        self.grab_set()

    def _save(self):
        self.app.cfg["console_override"] = {g: self.var.get() for g in BL_GAMES}
        save_config(self.app.cfg)
        self.app._update_bl()
        self.destroy()


class CalibrationWizard(tk.Toplevel):
    """One-time, guided measurement of Borderlands' turn speed."""

    def __init__(self, app, game, needs_console=False):
        super().__init__(app)
        self.app, self.game = app, game
        self.first = 0 if needs_console else 1
        self.step = self.first
        self.counts = 0
        self.title("Measure turn speed")
        self.configure(bg=BG)
        self.transient(app)
        self.resizable(False, False)
        card = Card(self, pad=22)
        card.pack(padx=px(18), pady=px(18))
        self.body = card.body
        self.progress = label(self.body, "", 10, MUTED)
        self.progress.pack(anchor="w")
        self.heading = label(self.body, "", 20, family="display", justify="left")
        self.heading.pack(anchor="w", pady=(px(2), px(8)))
        self.text = label(self.body, "", 11, justify="left", wraplength=px(500))
        self.text.pack(anchor="w")
        self.extra = tk.Frame(self.body, bg=PANEL)
        self.btns = tk.Frame(self.body, bg=PANEL)
        self.btns.pack(fill="x", pady=(px(18), 0))
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._go(self.step)
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_width()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_height()) // 4
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        dark_titlebar(self)
        self.grab_set()
        self._tick()

    def _clear(self):
        for f in (self.extra, self.btns):
            for w in f.winfo_children():
                w.destroy()
        self.extra.pack_forget()

    def _button(self, text, cmd, kind="primary"):
        CelButton(self.btns, text, cmd, kind=kind, size=12).pack(side="left", padx=(0, px(10)))

    def _go(self, step):
        self.step = step
        w = self.app.worker
        w.mode = "measure" if step == 2 else "off"
        w.override = CAL_VALUE if step in (1, 2) else None
        if step == 1:
            self._typed_before = w.typed
        if step == 2:
            w.counts, w.finished = 0, None
        self._show()

    def _show(self):
        self._clear()
        key = self.app.b_key.get()
        s = self.step
        total = 4 - self.first
        self.progress.configure(text=f"Step {s - self.first + 1} of {total}")
        if s == 0:
            self.heading.configure(text="Close Borderlands")
            self.text.configure(text="SensMatch needs to switch on Borderlands' console, which it "
                                "uses to set your sensitivity. Close the game if it's running, "
                                "then click Next.")
            self._button("Next", self._enable_console)
            self._button("Cancel", self._cancel, "secondary")
        elif s == 1:
            self.heading.configure(text=f"Start Borderlands and press {key}")
            self.text.configure(text=f"Load into your character, then press {key}. You'll see the "
                                "console flash at the bottom of the screen as SensMatch sets a "
                                "test sensitivity.\n\nThis window moves on by itself.")
            self._button("Cancel", self._cancel, "secondary")
        elif s == 2:
            self.heading.configure(text="Spin exactly once")
            self.text.configure(text="Aim at something with a sharp edge, like a door frame. Hold "
                                "F6 to spin right and let go just before you get back round. Hold "
                                "F7 to creep forward, tap F8 to step back. When you're exactly on "
                                "the edge again, press F10.\n\nDidn't see the console flash in the game? Click "
                                "Back and press the key again.")
            self.extra.pack(fill="x", pady=(px(14), 0), before=self.btns)
            self.dial = Dial(self.extra, size=190)
            self.dial.pack(side="left")
            keys = tk.Frame(self.extra, bg=PANEL)
            keys.pack(side="left", padx=px(20))
            for k, what in (("F6", "Spin fast"), ("F7", "Creep"), ("F8", "Step back"),
                            ("F9", "Start over"), ("F10", "Done")):
                r = tk.Frame(keys, bg=PANEL)
                r.pack(anchor="w", pady=px(2))
                tk.Label(r, text=k, width=4, bg=TEXT, fg=INK, font=(F["display"], 11),
                         highlightthickness=px(2), highlightbackground=INK).pack(side="left")
                label(r, what, 10).pack(side="left", padx=px(8))
            self._button("Back", lambda: self._go(1), "secondary")
        else:
            value = self.app._bl_state()[0][self.game]["value"]
            self.heading.configure(text="All done")
            self.text.configure(text=f"Measured {self.counts:,} counts for one full turn in "
                                f"{self.game}. It covers both games. Your sensitivity "
                                "is now set to "
                                f"{fmt(value) if value else '—'}.\n\nFrom now on, just press "
                                f"{key} after you load in, with SensMatch open.")
            self._button("Close", self.destroy)
            self._button("Measure again", lambda: self._go(2), "secondary")

    def _enable_console(self):
        if self.app.enable_console():
            self._go(1)

    def _tick(self):
        if not self.winfo_exists():
            return
        w = self.app.worker
        if self.step == 1 and w.typed and w.typed is not self._typed_before:
            self.game = w.typed[0]
            self._go(2)
        elif self.step == 2:
            self.dial.set(w.counts, (w.counts % 20000) / 20000 if w.counts > 0 else 0,
                          "counts turned")
            if w.finished is not None:
                n, w.finished = w.finished, None
                if n < 200:
                    self.app.toast("That turn was too short. Press F9 and spin a full circle.",
                                   error=True)
                else:
                    self._finish(n)
        self.after(40, self._tick)

    def _finish(self, n):
        self.counts = n
        # Same engine and input code, so one measurement covers both games
        for game in BL_GAMES:
            self.app.cfg["calibrations"][game] = {
                "yaw": 360.0 / (n * CAL_VALUE), "measured_counts": n, "at_value": CAL_VALUE,
                "date": datetime.now().isoformat(timespec="seconds"), "measured_in": self.game}
        save_config(self.app.cfg)
        self.app._refresh_games()
        w = self.app.worker
        w.mode, w.override = "off", None
        w.type_now = True          # the game is focused right now: set the real value
        self.app.bell()
        self._go(3)

    def _cancel(self):
        w = self.app.worker
        w.mode, w.override = "off", None
        self.destroy()


# ==========================================================================
# App
# ==========================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global S
        S = max(1.0, self.winfo_fpixels("1i") / 96.0)
        F["display"] = pick_family(self, "Bahnschrift SemiBold Condensed", "Bahnschrift",
                                   "Segoe UI Black", "DejaVu Sans Condensed")
        F["body"] = pick_family(self, "Segoe UI", "DejaVu Sans")
        F["mono"] = pick_family(self, "Cascadia Mono", "Consolas", "DejaVu Sans Mono")
        apply_theme(self)

        self.title(f"{APP_NAME}")
        self.configure(bg=BG)
        self.geometry(f"{px(1100)}x{px(780)}")
        self.minsize(px(960), px(640))
        try:
            self._icon = tk.PhotoImage(data=base64.b64decode(ICON_PNG))
            self.iconphoto(True, self._icon)
        except tk.TclError:
            pass

        self.games = load_games()
        self.cfg = load_config()
        self.baked = load_baked()
        self.game_boxes = []
        self.worker = None
        if IS_WINDOWS:
            self.worker = HotkeyWorker()
            self.worker.start()
        self._toast = None

        self._build_header()
        self.pages = tk.Frame(self, bg=BG)
        self.pages.pack(fill="both", expand=True, padx=px(22), pady=(px(6), px(18)))
        self.pages.columnconfigure(0, weight=1)
        self.pages.rowconfigure(0, weight=1)
        self.page = {}
        self.page["convert"] = self._build_converter()
        self.page["borderlands"] = self._build_borderlands()
        self.page["data"] = self._build_data()
        self.show("convert")

        self.protocol("WM_DELETE_WINDOW", self._close)
        dark_titlebar(self)
        self.after(40, self._poll)

    # ---- frame ----------------------------------------------------------
    def _build_header(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=px(22), pady=(px(18), px(10)))
        logo = tk.Canvas(bar, width=px(40), height=px(40), bg=BG, highlightthickness=0)
        c, r = px(19), px(12)
        logo.create_oval(c - r, c - r, c + r, c + r, outline=INK, width=px(8))
        logo.create_oval(c - r, c - r, c + r, c + r, outline=YELLOW, width=px(4))
        for a, b, x, y in ((c, px(1), c, px(10)), (c, px(28), c, px(38)),
                           (px(1), c, px(10), c), (px(28), c, px(38), c)):
            logo.create_line(a, b, x, y, fill=INK, width=px(7))
            logo.create_line(a, b, x, y, fill=YELLOW, width=px(3))
        logo.pack(side="left")
        label(bar, "SensMatch", 24, family="display").pack(side="left", padx=(px(10), px(30)))
        self.tabs = {}
        for key, text in (("convert", "Converter"), ("borderlands", "Borderlands"),
                          ("data", "Game data")):
            b = CelButton(bar, text, lambda k=key: self.show(k), kind="secondary", size=12)
            b.pack(side="left", padx=(0, px(10)))
            self.tabs[key] = b
        CelButton(bar, "Buy me a coffee", self._donate, kind="danger", size=12
                  ).pack(side="right")
        label(bar, f"v{VERSION}", 9, MUTED).pack(side="right", padx=(0, px(14)))

    def _donate(self):
        webbrowser.open(DONATE_URL)
        self.toast("Opening PayPal in your browser. Thank you!")

    def show(self, key):
        for k, b in self.tabs.items():
            b.configure_button(kind="primary" if k == key else "secondary")
        self.page[key].tkraise()

    def toast(self, text, error=False):
        if self._toast is not None:
            self._toast.destroy()
        t = Card(self, pad=12)
        stripe = tk.Frame(t.body, bg=ORANGE if error else YELLOW, width=px(6))
        stripe.pack(side="left", fill="y", padx=(0, px(12)))
        label(t.body, text, 10, justify="left", wraplength=px(420)).pack(side="left")
        t.place(relx=1.0, rely=1.0, x=-px(22), y=-px(18), anchor="se")
        self._toast = t
        self.after(5200 if not error else 7000, lambda: t.destroy() if t.winfo_exists() else None)

    # ---- shared helpers ---------------------------------------------------
    def game_names(self):
        return list(self.games) + [f"{g} (your calibration)" for g in self.cfg["calibrations"]]

    def get_yaw(self, name):
        if name in self.games:
            return self.games[name]["yaw"]
        for g, c in self.cfg["calibrations"].items():
            if name == f"{g} (your calibration)":
                return c["yaw"]
        raise KeyError(name)

    def _combo(self, parent, var, width=26):
        cb = combo(parent, var, self.game_names(), width)
        self.game_boxes.append(cb)
        return cb

    def _refresh_games(self):
        for cb in self.game_boxes:
            cb["values"] = self.game_names()
        self._update_converter()
        self._fill_data()
        self._update_bl()

    @staticmethod
    def _num(var):
        v = float(var.get().replace(",", ".").strip().rstrip("%"))
        if v <= 0:
            raise ValueError
        return v

    def copy(self, text, what=None):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.toast(f"Copied {what or text}")

    @staticmethod
    def field(parent, caption, widget_factory):
        box = tk.Frame(parent, bg=PANEL)
        label(box, caption, 10, MUTED).pack(anchor="w", pady=(0, px(3)))
        w = widget_factory(box)
        w.pack(anchor="w", fill="x")
        return box

    # ---- converter ------------------------------------------------------
    def _build_converter(self):
        p = tk.Frame(self.pages, bg=BG)
        p.grid(row=0, column=0, sticky="nsew")
        p.columnconfigure(0, weight=1, uniform="c")
        p.columnconfigure(2, weight=1, uniform="c")

        self.c_from, self.c_sens = tk.StringVar(value="Valorant"), tk.StringVar(value="0.26")
        self.c_fdpi = tk.StringVar(value="800")
        self.c_to, self.c_tdpi = tk.StringVar(value="Counter-Strike 2"), tk.StringVar(value="800")
        self.c_out = tk.StringVar(value="—")

        src = Card(p, "Your current game")
        src.grid(row=0, column=0, sticky="nsew")
        self.field(src.body, "Game", lambda b: self._combo(b, self.c_from)).pack(fill="x")
        row = tk.Frame(src.body, bg=PANEL)
        row.pack(fill="x", pady=(px(12), 0))
        self.field(row, "Sensitivity", lambda b: entry(b, self.c_sens, 10)).pack(side="left")
        self.field(row, "DPI", lambda b: entry(b, self.c_fdpi, 8)).pack(side="left", padx=px(14))

        mid = tk.Frame(p, bg=BG)
        mid.grid(row=0, column=1, padx=px(14))
        CelButton(mid, "⇄", self._swap, kind="secondary", size=16, pad=(12, 6)).pack()

        dst = Card(p, "Convert to")
        dst.grid(row=0, column=2, sticky="nsew")
        self.field(dst.body, "Game", lambda b: self._combo(b, self.c_to)).pack(fill="x")
        row = tk.Frame(dst.body, bg=PANEL)
        row.pack(fill="x", pady=(px(12), 0))
        self.field(row, "DPI", lambda b: entry(b, self.c_tdpi, 8)).pack(side="left")

        res = Card(p, pad=18)
        res.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(px(16), 0))
        left = tk.Frame(res.body, bg=PANEL)
        left.pack(side="left")
        self.c_to_label = label(left, "", 11, MUTED)
        self.c_to_label.pack(anchor="w")
        valrow = tk.Frame(left, bg=PANEL)
        valrow.pack(anchor="w")
        tk.Label(valrow, textvariable=self.c_out, fg=YELLOW, bg=PANEL,
                 font=(F["display"], 46)).pack(side="left")
        CelButton(valrow, "Copy", lambda: self.copy(self.c_out.get()), size=11
                  ).pack(side="left", padx=px(16), pady=(px(10), 0))
        stats = tk.Frame(res.body, bg=PANEL)
        stats.pack(side="right", padx=(px(20), 0))
        self.c_stats = []
        for cap in ("cm per 360°", "inches per 360°", "counts per 360°"):
            box = tk.Frame(stats, bg=FIELD, highlightthickness=px(2), highlightbackground=INK,
                           padx=px(14), pady=px(8))
            box.pack(side="left", padx=(px(10), 0))
            v = label(box, "—", 22, family="display", bg=FIELD)
            v.pack(anchor="w")
            label(box, cap, 9, MUTED, bg=FIELD).pack(anchor="w")
            self.c_stats.append(v)
        self.c_note = label(p, "", 10, MUTED, justify="left", anchor="w")
        self.c_note.grid(row=2, column=0, columnspan=3, sticky="w", pady=(px(6), 0))

        everywhere = Card(p, "The same feel in every game")
        everywhere.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(px(10), 0))
        label(everywhere.body, "At your target DPI. Click a game to copy its value.", 10, MUTED
              ).pack(anchor="w", pady=(0, px(8)))
        self.c_grid = tk.Frame(everywhere.body, bg=PANEL)
        self.c_grid.pack(fill="both", expand=True)
        self.c_grid.columnconfigure(0, weight=1, uniform="g")
        self.c_grid.columnconfigure(1, weight=1, uniform="g")
        p.rowconfigure(3, weight=1)

        for v in (self.c_from, self.c_sens, self.c_fdpi, self.c_to, self.c_tdpi):
            v.trace_add("write", lambda *_: self._update_converter())
        self._update_converter()
        return p

    def _swap(self):
        f, t = self.c_from.get(), self.c_to.get()
        out = self.c_out.get()
        fd, td = self.c_fdpi.get(), self.c_tdpi.get()
        self.c_from.set(t)
        self.c_to.set(f)
        self.c_fdpi.set(td)
        self.c_tdpi.set(fd)
        if out not in ("—", ""):
            self.c_sens.set(out)

    def _update_converter(self):
        if not hasattr(self, "c_grid"):
            return
        for w in self.c_grid.winfo_children():
            w.destroy()
        self.c_to_label.configure(text=f"{self.c_to.get()} sensitivity")
        try:
            sy, ty = self.get_yaw(self.c_from.get()), self.get_yaw(self.c_to.get())
            s, fd, td = self._num(self.c_sens), self._num(self.c_fdpi), self._num(self.c_tdpi)
        except (ValueError, KeyError):
            self.c_out.set("—")
            for v in self.c_stats:
                v.configure(text="—")
            self.c_note.configure(text="Enter a sensitivity and DPI above zero.")
            return
        result = convert(sy, s, fd, ty, td)
        d = sy * s
        cm = cm_per_360(d, fd)
        self.c_out.set(fmt(result))
        self.c_stats[0].configure(text=f"{cm:.2f}")
        self.c_stats[1].configure(text=f"{cm / 2.54:.2f}")
        self.c_stats[2].configure(text=f"{round(360 / (ty * result)):,}")
        notes = {self.games.get(n, {}).get("note", "") for n in (self.c_from.get(), self.c_to.get())}
        self.c_note.configure(text="  ".join(sorted(n for n in notes if n)))

        names = [n for n in self.game_names() if n != self.c_from.get()]
        half = (len(names) + 1) // 2
        for i, name in enumerate(names):
            val = fmt(convert(sy, s, fd, self.get_yaw(name), td))
            row = tk.Frame(self.c_grid, bg=PANEL, cursor="hand2")
            row.grid(row=i % half, column=i // half, sticky="ew", padx=(0, px(18)))
            a = label(row, name, 11, bg=PANEL)
            a.pack(side="left", pady=px(3))
            b = label(row, val, 13, YELLOW, family="display", bg=PANEL)
            b.pack(side="right")
            for w in (row, a, b):
                w.bind("<Button-1>", lambda e, v=val, n=name: self.copy(v, f"{n}: {v}"))
                w.bind("<Enter>", lambda e, r=row, ws=(a, b): [x.configure(bg=FIELD) for x in (r, *ws)])
                w.bind("<Leave>", lambda e, r=row, ws=(a, b): [x.configure(bg=PANEL) for x in (r, *ws)])

    # ---- borderlands ------------------------------------------------------
    def _build_borderlands(self):
        p = tk.Frame(self.pages, bg=BG)
        p.grid(row=0, column=0, sticky="nsew")
        p.columnconfigure(0, weight=3)
        p.columnconfigure(1, weight=2)

        self.a_game, self.a_sens = tk.StringVar(value="Valorant"), tk.StringVar(value="0.26")
        self.a_dpi, self.b_dpi = tk.StringVar(value="800"), tk.StringVar(value="")
        key = self.cfg.get("apply_key", "Home")
        self.b_key = tk.StringVar(value=key if key in APPLY_KEYS else "Home")
        self._ini_override = {}
        self._check_until = 0
        self._last_typed = None

        left = tk.Frame(p, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, px(14)))
        right = tk.Frame(p, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        c = Card(left, "Your aim")
        c.pack(fill="x")
        r = tk.Frame(c.body, bg=PANEL)
        r.pack(fill="x")
        self.field(r, "Game you're coming from", lambda b: self._combo(b, self.a_game, 24)
                   ).pack(side="left")
        self.field(r, "Sensitivity", lambda b: entry(b, self.a_sens, 8)).pack(side="left", padx=px(12))
        self.field(r, "Mouse DPI", lambda b: entry(b, self.a_dpi, 7)).pack(side="left")

        c = Card(left, "Borderlands")
        c.pack(fill="x", pady=(px(16), 0))
        self.b_rows = {}
        for g in BL_GAMES:
            r = tk.Frame(c.body, bg=PANEL)
            r.pack(fill="x", pady=px(4))
            label(r, g, 12).pack(side="left")
            val = label(r, "", 20, YELLOW, family="display")
            val.pack(side="right")
            status = label(r, "", 9, MUTED)
            status.pack(side="right", padx=px(12))
            self.b_rows[g] = (status, val)
        self.b_cm = label(c.body, "", 10, MUTED, justify="left", anchor="w")
        self.b_cm.pack(fill="x", pady=(px(6), 0))

        # what to do next: changes with the situation
        self.next_card = Card(left)
        self.next_card.pack(fill="x", pady=(px(16), 0))
        nb = self.next_card.body
        self.next_title = label(nb, "", 15, family="display")
        self.next_title.pack(anchor="w", pady=(0, px(8)))
        self.next_row = tk.Frame(nb, bg=PANEL)
        self.next_row.pack(fill="x")
        self.keycap = tk.Label(self.next_row, text="Home", bg=TEXT, fg=INK,
                               font=(F["display"], 20), padx=px(14), pady=px(4),
                               highlightthickness=px(3), highlightbackground=INK)
        self.next_text = label(self.next_row, "", 11, justify="left", wraplength=px(430))
        self.next_text.pack(side="left")
        self.next_btn = None
        self.next_detail = label(nb, "", 9, MUTED, justify="left", wraplength=px(560))
        self.next_tools = tk.Frame(nb, bg=PANEL)
        CelButton(self.next_tools, "Check again", self._update_bl, kind="secondary", size=9
                  ).pack(side="left")
        CelButton(self.next_tools, "Open file", self._open_ini, kind="secondary", size=9
                  ).pack(side="left", padx=px(8))
        CelButton(self.next_tools, "My console already works", self._console_works,
                  kind="secondary", size=9).pack(side="left")
        self.last_label = label(nb, "", 10, MUTED)
        self.last_label.pack(anchor="w", pady=(px(10), 0))

        o = Card(right, "Options")
        o.pack(fill="x")
        self.field(o.body, "Key to press in game",
                   lambda b: combo(b, self.b_key, list(APPLY_KEYS), 12)).pack(anchor="w")
        self.field(o.body, "Different DPI in Borderlands? (leave blank if not)",
                   lambda b: entry(b, self.b_dpi, 8)).pack(anchor="w", pady=(px(12), 0))
        r = tk.Frame(o.body, bg=PANEL)
        r.pack(anchor="w", pady=(px(14), 0))
        CelButton(r, "Find BL2 ini…", lambda: self._browse_ini("Borderlands 2"), kind="secondary",
                  size=9).pack(side="left")
        CelButton(r, "Find TPS ini…", lambda: self._browse_ini("Borderlands: The Pre-Sequel"),
                  kind="secondary", size=9).pack(side="left", padx=px(8))
        CelButton(o.body, "Measure turn speed again", self._open_wizard, kind="secondary", size=9
                  ).pack(anchor="w", pady=(px(10), 0))

        k = Card(right, "Check it (optional)")
        k.pack(fill="x", pady=(px(16), 0))
        label(k.body, "Click the button, go back to the game and press F11. You should spin "
              "exactly once and land where you started.", 10, MUTED, justify="left",
              wraplength=px(330)).pack(anchor="w")
        self.check_btn = CelButton(k.body, "Start check", self._start_check, kind="secondary",
                                   size=11)
        self.check_btn.pack(anchor="w", pady=(px(10), 0))
        if not self.worker:
            label(k.body, "Needs Windows.", 9, ORANGE).pack(anchor="w", pady=(px(6), 0))

        for v in (self.a_game, self.a_sens, self.a_dpi, self.b_dpi, self.b_key):
            v.trace_add("write", lambda *_: self._update_bl())
        self._update_bl()
        return p

    # turn speed: own measurement > built in > the other BL game's measurement
    def bl_yaw(self, game):
        cal, baked = self.cfg["calibrations"], self.baked
        if game in cal:
            return cal[game]["yaw"], "measured on this PC"
        if game in baked:
            return baked[game]["yaw"], "built in"
        for other in BL_GAMES:
            if other != game and (other in cal or other in baked):
                return cal.get(other, baked.get(other))["yaw"], f"using {other}'s measurement"
        return None, ""

    def _bl_dpi(self):
        return self._num(self.b_dpi) if self.b_dpi.get().strip() else self._num(self.a_dpi)

    def _target_deg(self):
        return self.get_yaw(self.a_game.get()) * self._num(self.a_sens) * self._num(self.a_dpi) \
            / self._bl_dpi()

    def _ini_for(self, game):
        if game in self._ini_override:
            return self._ini_override[game]
        return find_ini(game)[0]

    def _bl_state(self):
        """Per game: found, console key, value; plus target degrees per count."""
        try:
            deg = self._target_deg()
        except (ValueError, KeyError, ZeroDivisionError):
            deg = None
        state = {}
        for g in BL_GAMES:
            path = self._ini_for(g)
            found = os.path.exists(path)
            yaw, src = self.bl_yaw(g)
            ini = ini_status(path) if found else {"console": None}
            override = self.cfg.get("console_override", {}).get(g)
            state[g] = {"found": found, "path": path, "src": src, "ini": ini,
                        "console": override or ini["console"],
                        "value": (deg / yaw) if (deg and yaw) else None}
        return state, deg

    def _update_bl(self):
        if not hasattr(self, "b_rows"):
            return
        state, deg = self._bl_state()
        found = [g for g in BL_GAMES if state[g]["found"]]
        for g, (status, val) in self.b_rows.items():
            s = state[g]
            if not s["found"]:
                status.configure(text="Not installed, or not launched yet", fg=MUTED)
            elif not s["console"]:
                status.configure(text="Console off", fg=ORANGE)
            else:
                status.configure(text="Ready", fg=MUTED)
            val.configure(text=fmt(s["value"]) if s["value"] is not None else "—")
        if deg:
            cm = cm_per_360(deg, self._bl_dpi())
            self.b_cm.configure(text=f"That's {cm:.1f} cm of mouse movement for a full turn.",
                                fg=MUTED)
        else:
            self.b_cm.configure(text="Enter a sensitivity and DPI above zero.", fg=ORANGE)

        key = self.b_key.get()
        if self.cfg.get("apply_key") != key:
            self.cfg["apply_key"] = key
            save_config(self.cfg)
        self.keycap.configure(text=key)
        # BL2 and TPS are treated as one: either being ready is enough to carry on
        ready = [g for g in found if state[g]["console"]]
        not_ready = [g for g in found if not state[g]["console"]]
        needs_console = not_ready if not ready else []
        needs_measure = [g for g in ready if state[g]["value"] is None] if deg else []
        if not found:
            self._set_next("Launch Borderlands once",
                           "SensMatch looks for Borderlands' settings, which the game creates "
                           "the first time it runs. Launch it, then come back here.", None)
        elif needs_console:
            ini = state[needs_console[0]]["ini"]
            seen = ("ConsoleKey line is empty" if ini.get("raw") == "" else
                    f"ConsoleKey is set to {ini['raw']!r}, which SensMatch can't press"
                    if ini.get("raw") else "no ConsoleKey line found")
            ro = "\nThe file is marked read-only." if ini.get("readonly") else ""
            err = f"\nCouldn't read it: {ini['error']}" if ini.get("error") else ""
            self._set_next("One-time setup",
                           "SensMatch needs the console switched on. Close the game, then click "
                           "Set up. It does Borderlands 2 and The Pre-Sequel together.",
                           ("Set up", self._setup),
                           detail=f"Reading: {ini.get('path')}\nIt says: {seen}.{ro}{err}")
        elif needs_measure:
            self._set_next("Measure Borderlands once",
                           "Borderlands' turn speed hasn't been measured on this PC yet. It "
                           "takes about two minutes, once.", ("Measure now", self._open_wizard))
        else:
            extra = (f"\n\n{' and '.join(not_ready)} still has its console off. Close the game "
                     "and click Set up to switch it on too.") if not_ready else ""
            self._set_next("You're all set",
                           f"Keep SensMatch open (minimised is fine). In Borderlands, press {key} "
                           "after you load in and SensMatch sets your sensitivity. Press it again "
                           "if your aim ever feels fast after a loading screen." + extra,
                           ("Set up", self._setup) if not_ready else None, keycap=True)
        if self.worker:
            self.worker.apply_vk = APPLY_KEYS.get(key, 0x24)
            self.worker.commands = {g: (UE3_VK.get(state[g]["console"]), state[g]["value"])
                                    for g in found if state[g]["console"]}
            if deg:
                self.worker.verify_target = round(360 / deg)

    def _set_next(self, title, text, button, keycap=False, detail=None):
        self.next_title.configure(text=title, fg=YELLOW if keycap else TEXT)
        self.next_text.configure(text=text)
        if detail:
            self.next_detail.configure(text=detail)
            self.next_detail.pack(anchor="w", pady=(px(10), 0), before=self.last_label)
            self.next_tools.pack(anchor="w", pady=(px(8), 0), before=self.last_label)
        else:
            self.next_detail.pack_forget()
            self.next_tools.pack_forget()
        if keycap:
            self.keycap.pack(side="left", padx=(0, px(16)), before=self.next_text)
        else:
            self.keycap.pack_forget()
        if self.next_btn is not None:
            self.next_btn.destroy()
            self.next_btn = None
        if button:
            self.next_btn = CelButton(self.next_card.body, button[0], button[1], size=14,
                                      pad=(22, 8))
            self.next_btn.pack(anchor="w", pady=(px(12), 0),
                               before=self.next_detail if detail else self.last_label)

    def _browse_ini(self, game):
        path = filedialog.askopenfilename(title=f"Find WillowInput.ini for {game}",
                                          filetypes=[("ini files", "*.ini"), ("All files", "*.*")])
        if path:
            self._ini_override[game] = path
            self._update_bl()

    def enable_console(self):
        """Switch the console on in every found game that needs it. True if all worked."""
        state, _ = self._bl_state()
        ok = True
        for g in BL_GAMES:
            s = state[g]
            if not s["found"] or s["console"]:
                continue
            path = s["path"]
            steps = [("Find the line that starts with ConsoleKey= and change it to this. If there "
                      "isn't one, add it on the line under [Engine.Console]:",
                      f"ConsoleKey={DEFAULT_CONSOLE_KEY}")]
            step = "read"
            try:
                raw, text, enc, nl = read_ini(path)
                step = "back up"
                backup_ini(path, raw)
                text = ini_remove_old_binds(text)
                text = ini_enable_console(text, DEFAULT_CONSOLE_KEY)
                step = "save"
                write_ini(path, text, enc, nl)
            except OSError as e:
                ManualFixDialog(self, path, step, e, steps)
                ok = False
        self._update_bl()
        return ok

    def _setup(self):
        if self.enable_console():
            state, _ = self._bl_state()
            if not any(state[g]["found"] and state[g]["console"] for g in BL_GAMES):
                self.toast("Windows said the file saved, but the change isn't there when "
                           "SensMatch reads it back. Try Open file, or My console already "
                           "works.", error=True)
            else:
                self.toast("Console switched on. Start Borderlands and press "
                           f"{self.b_key.get()} once you've loaded in.")

    def _open_ini(self):
        state, _ = self._bl_state()
        g = next((g for g in BL_GAMES if state[g]["found"] and not state[g]["console"]),
                 next((g for g in BL_GAMES if state[g]["found"]), None))
        if not g:
            return
        if IS_WINDOWS:
            import subprocess
            subprocess.Popen(["notepad.exe", state[g]["path"]])
        else:
            self.toast(state[g]["path"])

    def _console_works(self):
        ConsoleKeyDialog(self)

    def _start_check(self):
        if not self.worker:
            return
        self._update_bl()
        self.worker.mode = "verify"
        self._check_until = time.time() + 90

    def _open_wizard(self):
        state, _ = self._bl_state()
        found = [g for g in BL_GAMES if state[g]["found"]]
        if not found:
            self.toast("Launch Borderlands once first so its settings file exists.", error=True)
            return
        if not self.worker:
            self.toast("Measuring needs Windows.", error=True)
            return
        ready = [g for g in found if state[g]["console"]]
        CalibrationWizard(self, (ready or found)[0], needs_console=not ready)

    # ---- game data ------------------------------------------------------
    def _build_data(self):
        p = tk.Frame(self.pages, bg=BG)
        p.grid(row=0, column=0, sticky="nsew")
        c = Card(p, "Turn rates")
        c.pack(fill="both", expand=True)
        label(c.body, "Degrees turned per mouse count at sensitivity 1. Add or correct games with "
              "a games.json file in the data folder.", 10, MUTED, justify="left",
              wraplength=px(800)).pack(anchor="w", pady=(0, px(10)))
        self.d_table = tk.Frame(c.body, bg=PANEL)
        self.d_table.pack(fill="both", expand=True)
        CelButton(c.body, "Open data folder", self._open_data, kind="secondary", size=10
                  ).pack(anchor="w", pady=(px(10), 0))
        self._fill_data()
        return p

    def _fill_data(self):
        if not hasattr(self, "d_table"):
            return
        for w in self.d_table.winfo_children():
            w.destroy()
        rows = [(n, g["yaw"], g.get("note", "")) for n, g in self.games.items()]
        rows += [(f"{g} (your calibration)", c["yaw"],
                  f"Measured {c['measured_counts']:,} counts at {c['at_value']} on {c['date'][:10]}")
                 for g, c in self.cfg["calibrations"].items()]
        rows += [(f"{g} (built in)", c["yaw"], "Measured by whoever built this copy")
                 for g, c in self.baked.items() if g not in self.cfg["calibrations"]]
        for i, (n, y, note) in enumerate(rows):
            bg = PANEL if i % 2 else FIELD
            r = tk.Frame(self.d_table, bg=bg)
            r.pack(fill="x")
            label(r, n, 11, bg=bg, width=30, anchor="w").pack(side="left", padx=px(8), pady=px(4))
            label(r, f"{y:.8g}", 12, YELLOW, family="display", bg=bg, width=12, anchor="w"
                  ).pack(side="left")
            label(r, note, 9, MUTED, bg=bg, anchor="w").pack(side="left", fill="x")

    def _open_data(self):
        if IS_WINDOWS:
            os.startfile(data_dir())
        else:
            self.toast(data_dir())

    # ---- loop -------------------------------------------------------------
    def _poll(self):
        w = self.worker
        if w and w.mode == "verify":
            left = int(self._check_until - time.time())
            if left <= 0 and w.pending == 0:
                w.mode = "off"
                self.check_btn.configure_button("Start check", "secondary")
            elif w.pending > 0:
                self.check_btn.configure_button(f"Spinning… {w.verify_sent:,}", "primary")
            else:
                self.check_btn.configure_button(f"Press F11 in game ({max(left, 0)}s)", "primary")
        if w and w.typed and w.typed is not self._last_typed:
            self._last_typed = w.typed
            game, value, t = w.typed
            self.last_label.configure(text=f"Last set: {fmt(value)} in {game} at "
                                      f"{datetime.fromtimestamp(t):%H:%M}")
        self.after(100, self._poll)

    def _close(self):
        if self.worker:
            self.worker.running = False
        self.destroy()


def bake():
    """Used by build.bat: ship this PC's measurements inside the exe."""
    cal = load_config()["calibrations"]
    out = {k: {"yaw": v["yaw"]} for k, v in cal.items()}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "baked.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("Built-in turn speeds:", ", ".join(out) if out else "none (users will measure once)")


def main():
    if "--bake" in sys.argv:
        bake()
        return
    if IS_WINDOWS:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    App().mainloop()


if __name__ == "__main__":
    main()
