"""
TODO:
-Json settings
-More commands
    -File search
    -App search
        -App click in update_results()
    -Web search
    -Run command
    -Run system command
-Run with hotkey
"""

from urllib.parse import quote
from webbrowser import open
from pathlib import Path
import tkinter.font as tkfont
import tkinter as tk
import subprocess
import math
import os
import re

# Configurable constants
WIDTH = 400
SEARCH_HEIGHT = 40
HEIGHT_OFFSET = -50
FONT_FAMILY = "JetBrains Mono"
FONT_HEIGHT = 12
HOTKEY = "<cmd>+<space>"
SEARCH_BAR_COLOR = "#2f2f2f"
RESULTS_COLOR = "#141414"
TEXT_COLOR = "#d0d0d0"

CALCULATOR_CMD = "="
WEB_SEARCH_CMD = "?"
FILE_SEARCH_CMD = "f"
APP_SEARCH_CMD = "a"
RUN_CMD_CMD = ">"
SYS_CMD_CMD = "<"

SEARCH_PATH = Path("~").expanduser()
DEFAULT_ENGINE = "duckduckgo"
SEARCH_ENGINES = {
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
}

# Non-configurable constants
FONT = (FONT_FAMILY, FONT_HEIGHT)
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


def main(*args):
    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == CALCULATOR_CMD:
        result = f"= {calculator(command_input)}"
        update_result(result)
    elif command == WEB_SEARCH_CMD:
        result = web_search(command_input, params)
        update_result(result)
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


def web_search(query, params):
    return "Press ENTER to search..."


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
        result_frame = tk.Canvas(root)
        result_frame.pack()
        scrollbar = tk.Scrollbar(root, orient="vertical", command=result_frame.yview)
        frame = tk.Frame(result_frame)
        frame.bind(
            "<Configure>",
            lambda e: result_frame.configure(scrollregion=result_frame.bbox("all")),  # type: ignore
        )
        result_frame.create_window((0, 0), window=frame, anchor="nw")
        result_frame.configure(yscrollcommand=scrollbar.set)
        result_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for result in results[:50]:
            if is_files:
                item = tk.Button(
                    result_frame,
                    text="",
                    font=FONT,
                    command=lambda path=result: open_file(path),
                    anchor="w",
                    justify="left",
                )
                item.configure(text=truncate_with_ellipsis(result, item, WIDTH - 10))
            elif is_apps:  # To be implemented
                item = tk.Label(
                    result_frame, text=result, font=FONT, anchor="w", justify="left"
                )
            else:
                item = tk.Label(
                    result_frame, text=result, font=FONT, anchor="w", justify="left"
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


def truncate_with_ellipsis(text, widget, max_width):
    font_info = widget.cget("font")
    f = tkfont.Font(family=font_info[0], size=font_info[1])

    if f.measure(text) <= max_width:
        return text

    ellipsis = "..."
    while text and f.measure(ellipsis + text) + 30 > max_width:
        text = text[1:]

    return ellipsis + text


def on_enter():
    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == CALCULATOR_CMD:
        result = calculator(command_input)
        root.clipboard_clear()
        root.clipboard_append(str(result))
        root.update()
        search_var.set("")
    elif command == WEB_SEARCH_CMD:
        engine = params.get("w", DEFAULT_ENGINE)
        url = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
        open(url + quote(command_input))
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
