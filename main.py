from decimal import Decimal, ROUND_HALF_UP
from webbrowser import open as webopen
from PIL import Image, ImageTk
from urllib.parse import quote
from pathlib import Path
import tkinter.font as tkfont
import tkinter as tk
import subprocess
import threading
import rapidfuzz
import cairosvg
import math
import json
import os
import re
import gi
import io

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # type: ignore

CONFIG_PATH = Path.home() / ".config" / "broodjekip-run" / "settings.json"
json_default = {
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
            return {**json_default, **json.load(f)}
    except Exception:
        return json_default


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
WEB_SEARCH_CMD = settings.get("commands", {}).get("web_search", "?")
FILE_SEARCH_CMD = settings.get("commands", {}).get("file_search", "f")
APP_SEARCH_CMD = settings.get("commands", {}).get("app_search", "@")
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

Examples:
  `{FILE_SEARCH_CMD} wallpaper`           search in {SEARCH_PATH}
  `{FILE_SEARCH_CMD} -e png wallpaper`    only .png files
  `{FILE_SEARCH_CMD} -p ~/docs report`    search in ~/docs""",
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

cancel_event = threading.Event()  # For file_search

selected_index = -1
result_items = []
previous_command = ""


def main(*args):
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
    elif command == FILE_SEARCH_CMD:
        file_search(command_input, params)
    elif command == APP_SEARCH_CMD:
        app_search(command_input)
    elif command == HELP_CMD:
        update_result(HELP_TEXT[command_input])

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
        search_var.set(f"= {result}")
    elif command == WEB_SEARCH_CMD:
        engine = params.get("w", DEFAULT_ENGINE)
        url = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
        webopen(url + quote(command_input))
        root.withdraw()
    elif command == RUN_CMD_CMD:
        subprocess.Popen([TERMINAL, "-e", "bash", "-c", f"{command_input}; exec bash"])
    elif command == SYS_CMD_CMD:
        if command_input in ("r", "restart"):
            os.system("systemctl reboot")
        elif command_input in ("s", "shutdown"):
            os.system("systemctl poweroff")
        elif command_input in ("l", "logout"):
            os.system("loginctl terminate-session $XDG_SESSION_ID")
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

    cancel_event.set()
    update_result("Searching...")

    if not query:
        update_result("Invalid search string...")
        return

    def run_search():
        scored_results = []
        for dirpath, dirnames, filenames in os.walk(path_to_search):
            if cancel_event.is_set():
                return
            for name in dirnames + filenames:
                if ext and not name.endswith(ext):
                    continue
                score = rapidfuzz.fuzz.ratio(query, name) / 100
                if (
                    score
                    >= 0.4  # Change this number for how many results to find. 0-1 and lower mens more results are valid
                ):
                    scored_results.append((str(Path(dirpath) / name), score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        results = [path for path, _ in scored_results[:MAX_RESULTS]]
        root.after(0, lambda: update_result(results, is_list=True, is_files=True))

    def delayed_start():
        cancel_event.clear()
        threading.Thread(target=run_search, daemon=True).start()

    root.after(100, delayed_start)


def app_search(query):
    found_apps = []
    for app in APPS:
        if query.lower() in app[0].lower():
            found_apps.append(app)
    if not found_apps:
        update_result("No apps found.")
        return
    max_items_without_scroll = MAX_RESULTS_HEIGHT // (FONT_HEIGHT + 16)
    if len(found_apps) > max_items_without_scroll:
        update_result(found_apps, is_list=True, is_apps=True)
    else:
        update_result(found_apps, is_apps=True)


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


def update_result(results=None, is_list=False, is_files=False, is_apps=False):
    global selected_index, result_frame, result_canvas
    result_items.clear()
    selected_index = -1
    result_frame.destroy()

    if results == None:
        root.geometry(f"{WIDTH}x{SEARCH_HEIGHT}")
        return

    if is_list:
        result_frame = tk.Frame(root, bg=RESULTS_COLOR)
        result_frame.pack(fill="both", expand=True)

        global canvas
        canvas = tk.Canvas(result_frame, bg=RESULTS_COLOR)
        result_canvas = canvas
        scrollbar = tk.Scrollbar(
            result_frame, orient="vertical", command=canvas.yview, bg=SEARCH_BAR_COLOR
        )
        inner_frame = tk.Frame(canvas, bg=RESULTS_COLOR)

        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.configure(height=min(e.height, MAX_RESULTS_HEIGHT))

        inner_frame.bind("<Configure>", on_frame_configure)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_canvas_configure(e):
            canvas.itemconfig(canvas.find_all()[0], width=e.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for result in results[:MAX_RESULTS]:
            if is_files:
                item = tk.Button(
                    inner_frame,
                    text=truncate_with_ellipsis(result, WIDTH),
                    font=FONT,
                    command=lambda path=result: open_file(path),
                    anchor="w",
                    justify="left",
                    fg=TEXT_COLOR,
                    bg=RESULTS_COLOR,
                )
                result_items.append(item)
            elif is_apps:
                name, executable, icon_name = result
                photo = load_icon(icon_name)
                item = tk.Button(
                    inner_frame,
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
            else:
                item = tk.Label(
                    inner_frame,
                    text=result,
                    font=FONT,
                    anchor="w",
                    justify="left",
                    fg=TEXT_COLOR,
                    bg=RESULTS_COLOR,
                )

            item.pack(fill="x")

    else:
        result_frame = tk.Frame(root)
        result_frame.pack(fill="x")
        if is_apps:
            for result in results[:MAX_RESULTS]:
                name, executable, icon_name = result
                photo = load_icon(icon_name)
                item = tk.Button(
                    result_frame,
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
                item.pack(fill="x")
        else:
            item = tk.Label(
                result_frame,
                text=wrap_text(str(results), WIDTH),
                font=FONT,
                anchor="w",
                justify="left",
                fg=TEXT_COLOR,
                bg=RESULTS_COLOR,
            )
            item.pack(fill="x")

    root.update_idletasks()
    center_window()

    if result_items and search_var.get().strip():
        selected_index = 0
        update_selection()


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
    if not icon_name:
        return None
    path = find_icon(icon_name, size)
    if not path:
        return None
    try:
        if path.endswith(".svg"):
            png_data = cairosvg.svg2png(url=path, output_width=size, output_height=size)
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
    if os.path.isfile(path):
        subprocess.Popen(["xdg-open", os.path.dirname(path)], stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", path], stderr=subprocess.DEVNULL)


def truncate_with_ellipsis(text, max_width):
    global FONT_OBJ
    if FONT_OBJ is None:
        FONT_OBJ = tkfont.Font(family=FONT_FAMILY, size=FONT_HEIGHT)
    if FONT_OBJ.measure(text) <= max_width:
        return text
    ellipsis_str = "..."
    while text and FONT_OBJ.measure(ellipsis_str + text) > max_width - 40:
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


update_result("Type h for help...")
root.update_idletasks()
APPS = load_apps()
search_var.trace_add("write", main)
root.after(50, force_focus)
center_window()
root.mainloop()
