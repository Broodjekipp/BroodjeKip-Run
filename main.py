"""
TODO:
-Json settings
-More commands
    -App search
        -App click in update_results()
    -Run command
    -Run system command
-Run with hotkey
"""

from urllib.parse import quote
from webbrowser import open as webopen
from pathlib import Path
import tkinter.font as tkfont
import tkinter as tk
import subprocess
import threading
import math
import json
import os
import re

CONFIG_PATH = Path.home() / ".config" / "broodjekip-run" / "settings.json"
json_default = {
    "dimensions": {
        "width": 500,
        "search_height": 40,
        "y_offset": -50,
        "max_results_height": 300,
    },
    "font": {"family": "JetBrains Mono", "height": 14},
    "colors": {"search_bar": "#2f2f2f", "results": "#141414", "text": "#d0d0d0"},
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

try:
    with open(CONFIG_PATH) as f:
        settings = json.load(f)
except FileNotFoundError:
    with open(CONFIG_PATH, "w") as f:
        json.dump(json_default, f)
    with open(CONFIG_PATH) as f:
        settings = json.load(f)

# Configurable constants
WIDTH = settings.get("dimensions", {}).get("width", 500)
SEARCH_HEIGHT = settings.get("dimensions", {}).get("search_height", 40)
HEIGHT_OFFSET = settings.get("dimensions", {}).get("y_offset", -50)
MAX_RESULTS_HEIGHT = settings.get("dimensions", {}).get("max_results_height", 300)
FONT_FAMILY = settings.get("font", {}).get("family", "DejaVu Sans Mono")
FONT_HEIGHT = settings.get("font", {}).get("height", 14)
SEARCH_BAR_COLOR = settings.get("colors", {}).get("search_bar", "#2f2f2f")
RESULTS_COLOR = settings.get("colors", {}).get("results", "#141414")
TEXT_COLOR = settings.get("colors", {}).get("text", "#d0d0d0")

CALCULATOR_CMD = settings.get("commands", {}).get("calculator", "=")
WEB_SEARCH_CMD = settings.get("commands", {}).get("web_search", "?")
FILE_SEARCH_CMD = settings.get("commands", {}).get("file_search", "f")
APP_SEARCH_CMD = settings.get("commands", {}).get("app_search", "a")
RUN_CMD_CMD = settings.get("commands", {}).get("run_command", ">")
SYS_CMD_CMD = settings.get("commands", {}).get("system_command", "<")

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
    "round": round,
    "pow": pow,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

root = tk.Tk()
root.title("BroodjeKip Run")
root.resizable(False, False)
root.bind("<Return>", lambda e: on_enter())
root.bind("<Escape>", lambda e: root.destroy())
root.bind("<FocusOut>", lambda e: root.destroy())

search_var = tk.StringVar()
search_bar = tk.Entry(root, textvariable=search_var, font=FONT)
search_bar.pack(fill="x")

result_frame = tk.Canvas(root)
cancel_event = threading.Event()  # For file_search


def main(*args):
    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == CALCULATOR_CMD:
        result = f"= {calculator(command_input)}"
        update_result(result)
    elif command == WEB_SEARCH_CMD:
        result = web_search()
        update_result(result)
    elif command == FILE_SEARCH_CMD:
        result = file_search(command_input)
    else:
        result = "Type the command..."
        update_result(result)


def calculator(input):
    try:
        result = eval(input, MATH_NAMESPACE)
        if callable(result):
            raise TypeError

    except (SyntaxError, NameError, ZeroDivisionError, TypeError):
        result = "Invalid expression"

    return result


def web_search():
    return "Press ENTER to search..."


def file_search(query):
    update_result("Searching...")
    cancel_event.set()

    def run_search():
        results = []
        if not query:
            return
        for dirpath, dirnames, filenames in os.walk(SEARCH_PATH):
            if cancel_event.is_set():
                return
            for filename in filenames:
                if query.lower() in filename.lower():
                    results.append(str(Path(dirpath) / filename))
        root.after(0, lambda: update_result(results, is_list=True, is_files=True))

    def delayed_start():
        cancel_event.clear()
        threading.Thread(target=run_search, daemon=True).start()

    root.after(10, delayed_start)


def parse_query(query):
    if not query:
        return "", "", {}

    command = query[0]
    query = query[1:].strip()

    if command != RUN_CMD_CMD:
        params = {}
        for match in re.finditer(r"-(\w+)\s+(\S+)", query):
            params[match.group(1)] = match.group(2)

        command_input = re.sub(r"-\w+\s+\S+\s*", "", query).strip()
    else:
        command_input = query
        params = {}

    return (command, command_input, params)


def update_result(results=None, is_list=False, is_files=False, is_apps=False):
    global result_frame
    result_frame.destroy()

    if results == None:
        root.geometry(f"{WIDTH}x{SEARCH_HEIGHT}")
        return

    if is_list:
        result_frame = tk.Frame(root)
        result_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(result_frame)
        scrollbar = tk.Scrollbar(result_frame, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas)

        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.configure(height=min(e.height, MAX_RESULTS_HEIGHT))

        inner_frame.bind("<Configure>", on_frame_configure)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for result in results[:MAX_RESULTS]:
            if is_files:
                item = tk.Button(
                    inner_frame,
                    text="",
                    font=FONT,
                    command=lambda path=result: open_file(path),
                    anchor="w",
                    justify="left",
                )
                item.configure(text=truncate_with_ellipsis(result, WIDTH - 10))
            elif is_apps:
                item = tk.Label(
                    inner_frame, text=result, font=FONT, anchor="w", justify="left"
                )
            else:
                item = tk.Label(
                    inner_frame, text=result, font=FONT, anchor="w", justify="left"
                )

            item.pack(fill="x")

    else:
        result_frame = tk.Frame(root)
        result_frame.pack()
        item = tk.Label(
            result_frame, text=str(results), font=FONT, anchor="w", justify="left"
        )
        item.pack()

    root.update_idletasks()
    root.geometry(f"{WIDTH}x{root.winfo_reqheight()}")


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
    while text and FONT_OBJ.measure(ellipsis_str + text) + 30 > max_width:
        text = text[1:]
    return ellipsis_str + text


def on_enter():
    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == CALCULATOR_CMD:
        result = calculator(command_input)
        root.clipboard_clear()
        root.clipboard_append(str(result))
        root.update()
        search_var.set("= ")
    elif command == WEB_SEARCH_CMD:
        engine = params.get("w", DEFAULT_ENGINE)
        url = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
        webopen(url + quote(command_input))
        root.withdraw()


def force_focus():
    root.focus_force()
    search_bar.focus_force()


def center_window():
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(  # Center the window to the screen
        f"{WIDTH}x{SEARCH_HEIGHT}+{(screen_w - WIDTH) // 2}+{(screen_h - SEARCH_HEIGHT) // 2 + HEIGHT_OFFSET}"
    )


center_window()
search_var.trace_add("write", main)
root.after(50, force_focus)
update_result("")
root.mainloop()
