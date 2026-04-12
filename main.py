"""
TODO
-command history
"""

from decimal import Decimal, ROUND_HALF_UP
from webbrowser import open as webopen
from threading import Thread, Event
from PIL import Image, ImageTk
from gi import require_version
from urllib.parse import quote
from pint import UnitRegistry
from os import system, walk
from rapidfuzz import fuzz
from pathlib import Path
import tkinter.font as tkfont
import tkinter as tk
import subprocess
import math
import json
import re
import io

require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore

CONFIG_PATH = Path.home() / ".config" / "broodjekip-run" / "settings.json"
JSON_DEFAULT = {
    "dimensions": {
        "width": 500,
        "search_height": 40,
        "y_offset": 100,
        "max_results_height": 300,
    },
    "font": {"family": "JetBrains Mono", "height": 14},
    "colors": {
        "search_bar": "#2f2f2f",
        "results": "#141414",
        "text": "#d0d0d0",
        "highlight": "#444444",
    },
    "commands": {
        "calculator": "=",
        "converter": "c",
        "web_search": "?",
        "file_search": "f",
        "app_search": "a",
        "run_command": ">",
        "system_command": "<",
    },
    "search": {
        "default_search_path": "~",
        "default_search_engine": "duckduckgo",
        "search_engines": {
            "google": "https://google.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
            "bing": "https://bing.com/search?q=",
            "ecosia": "https://ecosia.org/search?q=",
            "brave": "https://search.brave.com/search?q=",
            "startpage": "https://startpage.com/search?q=",
            "perplexity": "https://perplexity.ai/search?q=",
            "youtube": "https://youtube.com/results?search_query=",
            "wikipedia": "https://en.wikipedia.org/w/index.php?search=",
            "reddit": "https://reddit.com/search/?q=",
            "github": "https://github.com/search?q=",
            "stackoverflow": "https://stackoverflow.com/search?q=",
        },
    },
    "max_results": 50,
}


def load_settings():
    try:
        with open(CONFIG_PATH) as f:
            return deep_update(JSON_DEFAULT.copy(), json.load(f))
    except Exception:
        with open(CONFIG_PATH, "w") as f:
            json.dump(JSON_DEFAULT, f, indent=2)
            return JSON_DEFAULT


settings = load_settings()

# Configurable constants
WIDTH = settings.get("dimensions", {}).get("width", 500)
SEARCH_HEIGHT = settings.get("dimensions", {}).get("search_height", 40)
HEIGHT_OFFSET = settings.get("dimensions", {}).get("y_offset", 100)
MAX_RESULTS_HEIGHT = settings.get("dimensions", {}).get("max_results_height", 300)
FONT_FAMILY = settings.get("font", {}).get("family", "DejaVu Sans Mono")
FONT_HEIGHT = settings.get("font", {}).get("height", 14)
SEARCH_BAR_COLOR = settings.get("colors", {}).get("search_bar", "#2f2f2f")
RESULTS_COLOR = settings.get("colors", {}).get("results", "#141414")
TEXT_COLOR = settings.get("colors", {}).get("text", "#d0d0d0")
HIGHLIGHT_COLOR = settings.get("colors", {}).get("highlight", "#444444")

CALCULATOR_CMD = settings.get("commands", {}).get("calculator", "=")
CONVERTER_CMD = settings.get("commands", {}).get("converter", "c")
WEB_SEARCH_CMD = settings.get("commands", {}).get("web_search", "?")
FILE_SEARCH_CMD = settings.get("commands", {}).get("file_search", "f")
APP_SEARCH_CMD = settings.get("commands", {}).get("app_search", "a")
RUN_CMD_CMD = settings.get("commands", {}).get("run_command", ">")
SYS_CMD_CMD = settings.get("commands", {}).get("system_command", "<")
HELP_CMD = settings.get("commands", {}).get("help", "h")

SEARCH_PATH = Path(
    settings.get("search", {}).get("default_search_path", "~")
).expanduser()
DEFAULT_ENGINE = settings.get("search", {}).get("default_search_engine", "duckduckgo")
SEARCH_ENGINES = settings.get("search", {}).get(
    "search_engines",
    {
        "google": "https://google.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
        "bing": "https://bing.com/search?q=",
        "ecosia": "https://ecosia.org/search?q=",
        "brave": "https://search.brave.com/search?q=",
        "startpage": "https://startpage.com/search?q=",
        "perplexity": "https://perplexity.ai/search?q=",
        "youtube": "https://youtube.com/results?search_query=",
        "wikipedia": "https://en.wikipedia.org/w/index.php?search=",
        "reddit": "https://reddit.com/search/?q=",
        "github": "https://github.com/search?q=",
        "stackoverflow": "https://stackoverflow.com/search?q=",
    },
)
MAX_RESULTS = settings.get("max_results", 50)
TERMINAL = settings.get("terminal", "default")

# Non-configurable constants
FONT = (FONT_FAMILY, FONT_HEIGHT)
FONT_OBJ = None
MATH_NAMESPACE = {
    "__builtins__": {},
    "sqrt": math.sqrt,
    "factorial": lambda n: math.factorial(int(n)),
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "ceil": math.ceil,
    "floor": math.floor,
    "abs": abs,
    "round": lambda n: int(
        Decimal(str(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    ),
    "pow": math.pow,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}
UNIT_ALIASES = {
    "c": "degC",
    "f": "degF",
    "k": "kelvin",
    "km": "kilometer",
    "m": "meter",
    "cm": "centimeter",
    "mm": "millimeter",
    "mi": "mile",
    "nmi": "nautical_mile",
    "au": "astronomical_unit",
    "ly": "light_year",
    "in": "inch",
    "ft": "foot",
    "yd": "yard",
    "kg": "kilogram",
    "g": "gram",
    "mg": "milligram",
    "t": "metric_ton",
    "ton": "imperial_ton",
    "oz": "ounce",
    "lb": "pound",
    "floz": "fluid_ounce",
    "l": "liter",
    "ml": "milliliter",
    "pt": "pint",
    "qt": "quart",
    "gal": "gallon",
    "s": "second",
    "min": "minute",
    "h": "hour",
    "d": "day",
    "wk": "week",
    "sqm": "meter**2",
    "sqkm": "kilometer**2",
    "sqmi": "mile**2",
    "sqmm": "millimeter**2",
    "sqcm": "centimeter**2",
    "ha": "hectare",
    "acre": "acre",
    "cm3": "centimeter**3",
    "m3": "meter**3",
}
HELP_TEXT = {
    "": f"""Commands:
  {HELP_CMD}          Help
  {WEB_SEARCH_CMD}          Web search
  {FILE_SEARCH_CMD}          File search
  {APP_SEARCH_CMD}          App search
  {CALCULATOR_CMD}          Calculator
  {RUN_CMD_CMD}          Run command (in terminal)
  {SYS_CMD_CMD}          System command

Type `{HELP_CMD} <command>` for detailed info.""",
    HELP_CMD: f"""Help [{HELP_CMD}]
  Display usage info for a command.

Usage:
  {HELP_CMD} <command>

Example:
  `{HELP_CMD} {WEB_SEARCH_CMD}`  web search help
  `{HELP_CMD} {FILE_SEARCH_CMD}`  file search help""",
    WEB_SEARCH_CMD: f"""Web search [{WEB_SEARCH_CMD}]
  Search the web using your default browser.

Usage:
  {WEB_SEARCH_CMD} <query>
  {WEB_SEARCH_CMD} -w <engine> <query>

Examples:
  `{WEB_SEARCH_CMD} tkinter`           uses {DEFAULT_ENGINE}
  `{WEB_SEARCH_CMD} -w youtube cats`   searches YouTube

Engines: {", ".join(SEARCH_ENGINES.keys())}""",
    FILE_SEARCH_CMD: f"""File search [{FILE_SEARCH_CMD}]
  Fuzzy search for files and directories.

Usage:
  {FILE_SEARCH_CMD} <query>
  {FILE_SEARCH_CMD} -e <ext> <query>
  {FILE_SEARCH_CMD} -p <path> <query>
  {FILE_SEARCH_CMD} -d <depth> <query>

Examples:
  `{FILE_SEARCH_CMD} wallpaper`           search in {SEARCH_PATH}
  `{FILE_SEARCH_CMD} -e png wallpaper`    only .png files
  `{FILE_SEARCH_CMD} -p ~/docs -d 3 report`    search in ~/docs with a depth of 3""",
    APP_SEARCH_CMD: f"""App search [{APP_SEARCH_CMD}]
  Search installed applications.

Usage:
  {APP_SEARCH_CMD} <query>

Example:
  `{APP_SEARCH_CMD} fire`  matches Firefox, etc.""",
    CALCULATOR_CMD: f"""Calculator [{CALCULATOR_CMD}]
  Evaluate math expressions.
  Press ENTER to copy the result.

Usage:
  {CALCULATOR_CMD} <expression>

Examples:
  `{CALCULATOR_CMD} 2 + 2`
  `{CALCULATOR_CMD} sqrt(144)`
  `{CALCULATOR_CMD} sin(pi / 2)`

Functions: sqrt, log, log2, log10, sin, cos, tan,
           asin, acos, atan, ceil, floor, abs,
           round, pow, factorial
Constants: pi, e, tau""",
    CONVERTER_CMD: f"""Unit converter [{CONVERTER_CMD}]
  Convert a unit to another.

Usage:
  {CONVERTER_CMD} <value> <from unit> <to unit>

Example:
  `{CONVERTER_CMD} 40 c f`

Allowed units:
  {", ".join(UNIT_ALIASES.keys())}""",
    RUN_CMD_CMD: f"""Run command [{RUN_CMD_CMD}]
  Run a shell command in a terminal window.

Usage:
  {RUN_CMD_CMD} <command>

Example:
  `{RUN_CMD_CMD} python3 script.py`""",
    SYS_CMD_CMD: f"""System command [{SYS_CMD_CMD}]
  Perform a system action.

Usage:
  {SYS_CMD_CMD} <action>

Actions:
  r / restart    Reboot
  s / shutdown   Power off
  l / logout     Log out""",
}
ureg = UnitRegistry()

root = tk.Tk()
root.title("BroodjeKip Run")
root.resizable(False, False)
root.configure(bg=RESULTS_COLOR)
root.bind("<Return>", lambda e: on_enter())
root.bind("<Escape>", lambda e: root.destroy())
root.bind("<FocusOut>", lambda e: root.destroy())
root.bind("<Down>", lambda e: move_selection(1))
root.bind("<Up>", lambda e: move_selection(-1))

search_var = tk.StringVar()
search_bar = tk.Entry(
    root, textvariable=search_var, font=FONT, fg=TEXT_COLOR, bg=SEARCH_BAR_COLOR
)
search_bar.pack(fill="x")

result_frame = tk.Canvas(root, bg=RESULTS_COLOR)
result_canvas = None

cancel_event = Event()  # For file_search
_cairosvg = None

selected_index = -1
result_items = []
previous_command = ""


def on_update(*args):
    global previous_command
    query = search_var.get()
    command, command_input, params = parse_query(query)

    result_map = {
        RUN_CMD_CMD: "Press ENTER to run command...",
        SYS_CMD_CMD: "Press ENTER to run system command...",
        WEB_SEARCH_CMD: "Press ENTER to search...",
    }

    if command == CALCULATOR_CMD:
        update_result(f"= {calculator(command_input)}")
    elif command == CONVERTER_CMD:
        update_result(unit_convert(command_input))
    elif command == FILE_SEARCH_CMD:
        file_search(command_input, params)
    elif command == APP_SEARCH_CMD:
        app_search(command_input)
    elif command == HELP_CMD:
        update_result(HELP_TEXT.get(command_input, "Invalid command name."))

    elif command in result_map:
        if command != previous_command:
            update_result(result_map[command])
    elif command == "":
        update_result("Type the command...")
    else:
        update_result("Invalid command...")
    previous_command = command


def on_enter():
    global selected_index

    if 0 <= selected_index < len(result_items):
        result_items[selected_index].invoke()
        return

    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == CALCULATOR_CMD:
        result = calculator(command_input)
        root.clipboard_clear()
        root.clipboard_append(str(result))
        root.update()
        search_var.set(f"{CALCULATOR_CMD} {result}")
    elif command == CONVERTER_CMD:
        result = unit_convert(command_input)
        root.clipboard_clear()
        root.clipboard_append(str(result))
        root.update()
        search_var.set(f"{CONVERTER_CMD} {result}")
    elif command == WEB_SEARCH_CMD:
        engine = params.get("w", DEFAULT_ENGINE)
        url = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
        webopen(url + quote(command_input))
        root.withdraw()
    elif command == RUN_CMD_CMD:
        subprocess.Popen([TERMINAL, "-e", "bash", "-c", f"{command_input}; exec bash"])
    elif command == SYS_CMD_CMD:
        if command_input in ("r", "restart"):
            system("systemctl reboot")
        elif command_input in ("s", "shutdown"):
            system("systemctl poweroff")
        elif command_input in ("l", "logout"):
            system("loginctl terminate-session $XDG_SESSION_ID")
        else:
            update_result("Command not found.")


def calculator(input):
    try:
        result = eval(input, MATH_NAMESPACE)
        if callable(result):
            raise TypeError

    except (SyntaxError, NameError, ZeroDivisionError, TypeError):
        result = "Invalid expression"

    return result


def unit_convert(query):
    parts = query.split()

    if len(parts) == 2:
        match = re.match(r"([\d.]+)(.*)", parts[0])
        if not match:
            return "Invalid value."

        value = match.group(1)
        from_alias = match.group(2).strip()
        to_alias = parts[1].strip()
    elif len(parts) == 3:
        value = parts[0].strip()
        from_alias = parts[1].strip()
        to_alias = parts[2].strip()
    else:
        return "Invalid format. Use: <value><unit> <unit>"

    from_unit = UNIT_ALIASES.get(from_alias.lower(), from_alias)
    to_unit = UNIT_ALIASES.get(to_alias.lower(), to_alias)

    try:
        result = ureg.Quantity(float(value), from_unit).to(to_unit)
        num = result.magnitude
        formatted = int(num) if num == int(num) else round(num, 8)
        return f"{formatted} {to_unit}"
    except Exception:
        return "Incompatible units"


def file_search(query, params=None):
    if params is None:
        params = {}
    ext = params.get("e")
    if ext is True:
        ext = None
    p = params.get("p")
    path_to_search = Path(p if isinstance(p, str) else SEARCH_PATH).expanduser()
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    max_depth = params.get("d")
    if max_depth is not None:
        try:
            max_depth = int(max_depth)
        except ValueError:
            max_depth = None

    local_cancel = Event()
    cancel_event = local_cancel
    update_result("Searching...")

    if not query:
        update_result("Invalid search string...")
        return

    def run_search():
        scored_results = []
        base_depth = len(path_to_search.parts)

        for dirpath, dirnames, filenames in walk(path_to_search):
            if cancel_event is not local_cancel:
                return

            current_path = Path(dirpath)
            current_depth = len(current_path.parts) - base_depth

            if max_depth is not None and current_depth >= max_depth:
                dirnames[:] = []

            for name in dirnames + filenames:
                if ext and not name.endswith(ext):
                    continue

                score = fuzz.partial_ratio(query, name) / 100
                if score >= 0.4:
                    scored_results.append((str(current_path / name), score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        results = [path for path, _ in scored_results[:MAX_RESULTS]]
        if results:
            root.after(
                0,
                lambda: update_result(
                    results, is_scrollable=True, is_list=True, is_files=True
                ),
            )
        else:
            root.after(0, lambda: update_result("No files found"))

    def delayed_start():
        cancel_event.clear()
        Thread(target=run_search, daemon=True).start()

    root.after(100, delayed_start)


def app_search(query):
    found_apps = []
    for app in APPS:
        if query.lower() in app[0].lower():
            found_apps.append(app)
    if not found_apps:
        update_result("No apps found.")
        return
    max_items_without_scroll = MAX_RESULTS_HEIGHT // RESULT_ITEM_HEIGHT
    if len(found_apps) > max_items_without_scroll:
        update_result(found_apps, is_scrollable=True, is_list=True, is_apps=True)
    else:
        update_result(found_apps, is_list=True, is_apps=True)


def parse_query(query):
    if not query:
        return "", "", {}

    command = query[0]
    query = query[1:].strip()

    params = {}
    if command != RUN_CMD_CMD:
        for match in re.finditer(r"-(\w+)\s+(\S+)", query):
            params[match.group(1)] = match.group(2)
        for match in re.finditer(r"-(\w+)(?!\s+\S)", query):
            if match.group(1) not in params:
                params[match.group(1)] = True

        command_input = re.sub(r"-\w+(?:\s+\S+)?\s*", "", query).strip()
    else:
        command_input = query

    return (command, command_input, params)


def update_result(
    results=None, is_scrollable=False, is_list=False, is_files=False, is_apps=False
):
    global selected_index, result_frame, result_canvas

    result_items.clear()
    selected_index = -1
    result_frame.destroy()
    result_frame = tk.Frame(root, bg=RESULTS_COLOR)
    result_frame.pack(fill="both", expand=True)

    if results is None:
        root.geometry(f"{WIDTH}x{SEARCH_HEIGHT}")
        return

    if is_scrollable:
        inner_frame, result_canvas = make_scrollable_frame(result_frame)
        container = inner_frame
    else:
        container = result_frame
        result_canvas = result_frame

    if is_list:
        for result in results[:MAX_RESULTS]:
            item = make_result_item(container, result, is_files, is_apps)
            item.pack(fill="x")
    else:
        item = make_result_item(container, results, is_files, is_apps)
        item.pack(fill="x")
        item.update_idletasks()

    root.update_idletasks()
    center_window()

    if result_items and search_var.get().strip():
        selected_index = 0
        update_selection()


def make_result_item(parent, result, is_files, is_apps):
    if is_files:
        item = tk.Button(
            parent,
            text=truncate_with_ellipsis(result, WIDTH),
            font=FONT,
            command=lambda path=result: open_file(path),
            anchor="w",
            justify="left",
            fg=TEXT_COLOR,
            bg=RESULTS_COLOR,
        )
        result_items.append(item)
        return item
    elif is_apps:
        name, executable, icon_name = result
        photo = load_icon(icon_name)
        item = tk.Button(
            parent,
            text=truncate_with_ellipsis(name, WIDTH),
            font=FONT,
            command=lambda e=executable: launch_app(e),
            anchor="w",
            justify="left",
            fg=TEXT_COLOR,
            bg=RESULTS_COLOR,
            **({"image": photo, "compound": "left"} if photo else {}),
        )
        item.image = photo  # type: ignore
        result_items.append(item)
        return item
    else:
        return tk.Label(
            parent,
            text=wrap_text(str(result), WIDTH),
            font=FONT,
            anchor="w",
            justify="left",
            fg=TEXT_COLOR,
            bg=RESULTS_COLOR,
        )


def make_scrollable_frame(parent):
    cv = tk.Canvas(parent, bg=RESULTS_COLOR)
    scrollbar = tk.Scrollbar(
        parent, orient="vertical", command=cv.yview, bg=SEARCH_BAR_COLOR
    )
    inner_frame = tk.Frame(cv, bg=RESULTS_COLOR)

    def on_frame_configure(e):
        cv.configure(scrollregion=cv.bbox("all"))
        cv.configure(height=min(e.height, MAX_RESULTS_HEIGHT))

    def on_canvas_configure(e):
        cv.itemconfig(cv.find_all()[0], width=e.width)

    inner_frame.bind("<Configure>", on_frame_configure)
    cv.create_window((0, 0), window=inner_frame, anchor="nw")
    cv.bind("<Configure>", on_canvas_configure)
    cv.configure(yscrollcommand=scrollbar.set)
    cv.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return inner_frame, cv


def update_selection():
    for i, item in enumerate(result_items):
        if i == selected_index:
            item.config(bg=HIGHLIGHT_COLOR)
        else:
            item.config(bg=RESULTS_COLOR)


def move_selection(direction):
    global selected_index

    if not result_items:
        return

    selected_index += direction
    selected_index %= len(result_items)

    update_selection()

    if result_canvas:
        scroll_to_selected(result_canvas)


def scroll_to_selected(canvas):
    if 0 <= selected_index < len(result_items):
        item = result_items[selected_index]
        canvas.update_idletasks()
        total_height = canvas.bbox("all")[3]
        if total_height > 0:
            canvas.yview_moveto(item.winfo_y() / total_height)


def find_icon(name, size=32):
    theme = Gtk.IconTheme.get_default()
    info = theme.lookup_icon(name, size, 0)
    return info.get_filename() if info else None


def load_apps():
    apps = []
    dirs = [Path("/usr/share/applications"), Path.home() / ".local/share/applications"]
    for d in dirs:
        for f in d.glob("*.desktop"):
            name = None
            icon = None
            try:
                with open(f) as file:
                    for line in file:
                        if line.startswith("Name=") and not name:
                            name = line.strip().split("=", 1)[1]
                        elif line.startswith("Icon=") and not icon:
                            icon = line.strip().split("=", 1)[1]
            except (OSError, UnicodeDecodeError):
                pass
            if name:
                apps.append((name, f.stem, icon))
    apps.sort(key=lambda x: x[0].lower())  # Sort results alphabetically
    return apps


def load_icon(icon_name, size=16):
    global _cairosvg
    if not icon_name:
        return None
    path = find_icon(icon_name, size)
    if not path:
        return None
    try:
        if path.endswith(".svg"):
            from cairosvg import svg2png as _svg2png

            _cairosvg = _svg2png
            png_data = _cairosvg(url=path, output_width=size, output_height=size)
            assert png_data
            img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        else:
            img = Image.open(path).resize((size, size)).convert("RGBA")
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"failed to load {path}: {e}")
        return None


def launch_app(desktop_file):
    subprocess.Popen(["gtk-launch", desktop_file], stderr=subprocess.DEVNULL)


def open_file(path):
    p = Path(path)
    if p.is_file():
        subprocess.Popen(["xdg-open", str(p.parent)], stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", str(p)], stderr=subprocess.DEVNULL)


def truncate_with_ellipsis(text, max_width):
    global FONT_OBJ
    if FONT_OBJ is None:
        FONT_OBJ = tkfont.Font(family=FONT_FAMILY, size=FONT_HEIGHT)
    if FONT_OBJ.measure(text) <= max_width:
        return text
    ellipsis_str = "..."
    while (
        text and FONT_OBJ.measure(ellipsis_str + text) > max_width - 40
    ):  # -40 to give the text some extra breathing room
        text = text[1:]
    return ellipsis_str + text


def wrap_text(text, max_width):
    global FONT_OBJ
    if FONT_OBJ is None:
        FONT_OBJ = tkfont.Font(family=FONT_FAMILY, size=FONT_HEIGHT)

    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        current = ""
        for word in words:
            test = current + (" " if current else "") + word
            if FONT_OBJ.measure(test) > max_width - 40:
                if current:
                    lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)

    return "\n".join(lines)


def get_item_height():
    item = make_result_item(
        root, "[GETTING ITEM HEIGHT]", is_apps=False, is_files=False
    )
    item.pack(fill="x")
    item.update_idletasks()
    height = item.winfo_height()
    item.destroy()
    return height


def deep_update(default, custom):
    for k, v in custom.items():
        if isinstance(v, dict) and k in default:
            deep_update(default[k], v)
        else:
            default[k] = v
    return default


def force_focus():
    root.focus_force()
    search_bar.focus_force()


def center_window():
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    height = root.winfo_reqheight()

    x = (screen_w - WIDTH) // 2
    y = (screen_h - SEARCH_HEIGHT) // 2 - HEIGHT_OFFSET

    root.geometry(f"{WIDTH}x{height}+{x}+{y}")


RESULT_ITEM_HEIGHT = get_item_height()

update_result("Type h for help...")
root.update_idletasks()
APPS = load_apps()

search_var.trace_add("write", on_update)
root.after(50, force_focus)
center_window()

root.mainloop()
