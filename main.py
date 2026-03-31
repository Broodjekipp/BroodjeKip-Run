"""
TODO:
 - App search
 - Calculator: unit converter
 - More search engines
 - Command history
 - Command params: <command> -<param name> <param> <input>
    - File search: Search paths    (-p)
    - Web search: Search engine    (-s)
    - Web search: Search website   (-w)
    - All commands: Help           (-h)
 - Subtext in update_results()
"""

from urllib.parse import quote as webquote
from webbrowser import open as webopen
from tkinter.font import Font
from pynput import keyboard
from pathlib import Path
import customtkinter as ctk
import subprocess
import threading
import json
import os

CONFIG_PATH = Path.home() / ".config" / "broodjekip-run" / "settings.json"
json_default = {
    "colors": {"bg": "#141414", "fg": "#2f2f2f", "text": "#d0d0d0"},
    "font": {"family": "JetBrains Mono", "size_primary": 20, "size_secondary": 16},
    "dimensions": {
        "width": 400,
        "search_height": 40,
        "result_height": 40,
        "scroll_height": 200,
    },
    "hotkey": "<cmd>+<space>",
    "search_engine": "duckduckgo",
    "search_path": "~",
}
try:
    with open(CONFIG_PATH) as f:
        settings = json.load(f)
except FileNotFoundError:
    with open(CONFIG_PATH, "w") as f:
        json.dump(json_default, f)
    with open(CONFIG_PATH) as f:
        settings = json.load(f)

BG_COLOR = settings.get("colors", {}).get("bg", "#141414")
FG_COLOR = settings.get("colors", {}).get("fg", "#2f2f2f")
TEXT_COLOR = settings.get("colors", {}).get("text", "#d0d0d0")
FONT = settings.get("font", {}).get("family", "DejaVu Sans Mono")
FULL_FONT_HEIGHT = settings.get("font", {}).get("size_primary", 20)
SECONDARY_FONT_HEIGHT = settings.get("font", {}).get("size_secondary", 16)
WIDGET_WIDTH = settings.get("dimensions", {}).get("width", 400)
SEARCH_HEIGHT = settings.get("dimensions", {}).get("search_height", 40)
RESULT_HEIGHT = settings.get("dimensions", {}).get("result_height", 40)
SCROLL_HEIGHT = settings.get("dimensions", {}).get("scroll_height", 200)

HOTKEY = settings.get("hotkey", "<cmd>+<space>")
SEARCH_PATH = Path(settings.get("search_path", "~")).expanduser()
ENGINE = settings.get("search_engine", "duckduckgo")
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

entered = False
search_cooldown = True
last_input = ""

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def calculator(expression, update_result=True):
    global entered
    try:
        result = eval(expression)
        if update_result:
            update_results(f"= {result}")
        if entered:
            root.clipboard_clear()
            root.clipboard_append(result)
            root.update()
            search_bar.delete(1, "end")
            entered = False

    except (SyntaxError, NameError, ZeroDivisionError):
        result = "Invalid expression"
        if update_result:
            update_results(result)


def web_search(query, update_result):
    global entered
    if entered:
        webopen(SEARCH_ENGINES[ENGINE] + webquote(query))
        entered = False
    elif update_result:
        update_results("Press ENTER to search...")


def file_search(file_input, input_changed):
    def _search():
        try:
            results = (
                subprocess.check_output(
                    ["locate", "-i", "--regex", f"{SEARCH_PATH}/.*{file_input}"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                .strip()
                .splitlines()
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            results = None
        if file_input != parse_input(search_bar.get())[1]:
            return
        root.after(0, lambda: update_results(results, files=True, scroll=True))

    if input_changed:
        if file_input:
            update_results("Searching...")
            results = []
            threading.Thread(target=_search, daemon=True).start()
        else:
            update_results("Type the filename...")


def run_command(command, update_result):
    global entered
    if entered:
        subprocess.Popen(["kitty", "--", "bash", "-c", f"{command}; exec bash"])
        entered = False
    if update_result:
        update_results("Type ENTER to run...")


def system_command(command):
    global entered
    if entered:
        if command in ("r", "restart"):
            os.system("systemctl reboot")
        elif command in ("s", "shutdown"):
            os.system("systemctl poweroff")
        elif command in ("l", "logout"):
            os.system("loginctl terminate-session $XDG_SESSION_ID")
        else:
            update_results("Command not found.")
        entered = False


def main():
    global last_input, entered
    user_input = search_bar.get()
    command, command_input = parse_input(user_input)

    input_changed = last_input != user_input
    if input_changed:
        last_input = user_input

    if command == "=":
        calculator(command_input, input_changed)
    elif command == "?":
        web_search(command_input, input_changed)
    elif command == "f":
        file_search(command_input, input_changed)
    elif command == ">":
        run_command(command_input, input_changed)
    elif command == "<":
        system_command(command_input)

    root.after(50, main)


def update_results(results, scroll=False, files=False):
    global results_frame

    for widget in results_frame.winfo_children():
        widget.destroy()
    root.geometry(f"{WIDGET_WIDTH}x{SEARCH_HEIGHT}")

    if results is None:
        return

    if isinstance(results, list) and len(results) == 0:
        results = ["No files found."]

    results_frame.destroy()
    if scroll:
        results_frame = ctk.CTkScrollableFrame(
            result_frame_frame,
            fg_color=BG_COLOR,
            height=SCROLL_HEIGHT,
        )
        results_frame.pack(fill="both", expand=True)
        root.geometry(f"{WIDGET_WIDTH}x{SEARCH_HEIGHT+SCROLL_HEIGHT}")
        for result in results[:50]:
            if files:
                item = ctk.CTkButton(
                    results_frame,
                    text="",
                    font=(FONT, SECONDARY_FONT_HEIGHT),
                    hover_color=FG_COLOR,
                    command=lambda path=result: open_file(path),
                    anchor="w",
                    width=WIDGET_WIDTH,
                )
                item.configure(
                    text=truncate_with_ellipsis(result, item, WIDGET_WIDTH - 10)
                )
            else:
                item = ctk.CTkLabel(
                    results_frame,
                    text=result,
                    font=(FONT, SECONDARY_FONT_HEIGHT),
                    anchor="w",
                )
            item.pack(fill="x")
    else:
        results_frame = ctk.CTkFrame(result_frame_frame, fg_color=BG_COLOR)
        results_frame.pack(fill="both", expand=True)
        root.geometry(f"{WIDGET_WIDTH}x{SEARCH_HEIGHT+RESULT_HEIGHT}")
        item = ctk.CTkLabel(
            results_frame,
            text=str(results),
            font=(FONT, SECONDARY_FONT_HEIGHT),
            anchor="w",
        )
        item.pack(fill="x")


def open_file(path):
    if os.path.isfile(path):
        subprocess.Popen(["xdg-open", os.path.dirname(path)], stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", path], stderr=subprocess.DEVNULL)


def parse_input(input):
    try:
        command = input[0]
        command_input = input[1:].strip()
    except IndexError:
        command = ""
        command_input = ""

    return command, command_input


def truncate_with_ellipsis(text, widget, max_width):
    f = Font(font=widget.cget("font"))

    if f.measure(text) <= max_width:
        return text

    ellipsis = "..."
    while text and f.measure(ellipsis + text) + 30 > max_width:
        text = text[1:]

    return ellipsis + text


def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def on_enter():
    global entered
    entered = True


def force_focus():
    root.focus_force()
    search_bar.focus_force()


root = ctk.CTk()
root.configure(fg_color=BG_COLOR)
root.resizable(False, False)
root.geometry(f"{WIDGET_WIDTH}x{SEARCH_HEIGHT}")
root.title("BroodjeKip Run")
root.attributes("-topmost", True)
center_window(root)
root.bind("<Escape>", lambda e: root.withdraw())
root.bind("<Return>", lambda e: on_enter())
root.bind("<FocusOut>", lambda e: root.withdraw())
root.after(50, force_focus)

content_frame = ctk.CTkFrame(root, fg_color=BG_COLOR)
content_frame.pack(fill="both", expand=True)

search_bar = ctk.CTkEntry(
    content_frame,
    placeholder_text="Type...",
    font=(FONT, FULL_FONT_HEIGHT),
    height=SEARCH_HEIGHT,
    width=WIDGET_WIDTH,
)
search_bar.pack(fill="x", expand=True)
result_frame_frame = ctk.CTkFrame(content_frame, fg_color=BG_COLOR)
result_frame_frame.pack(fill="both", expand=True, anchor="w")
results_frame = ctk.CTkFrame(result_frame_frame, fg_color=BG_COLOR)
results_frame.pack(fill="both", expand=True, anchor="w")

root.after(50, main)

combo = {keyboard.Key.cmd, keyboard.KeyCode.from_char(" ")}
current = set()


def hide_window():
    root.unbind("<Return>")
    root.withdraw()


def on_press(key):
    print("DEBUG: show window")
    current.add(key)
    if all(k in current for k in combo):
        root.after(0, show_window)


def on_release(key):
    current.discard(key)


def show_window():
    root.unbind("<FocusOut>")
    root.deiconify()
    center_window(root)
    search_bar.delete(0, "end")
    update_results(None)
    force_focus()
    root.bind("<FocusOut>", lambda e: root.withdraw())


def for_canonical(f):
    return lambda k: f(listener.canonical(k))


hotkey = keyboard.HotKey(
    keyboard.HotKey.parse(HOTKEY), lambda: root.after(0, show_window)
)
listener = keyboard.Listener(
    on_press=for_canonical(hotkey.press), on_release=for_canonical(hotkey.release)
)
listener.daemon = True
listener.start()

root.mainloop()
