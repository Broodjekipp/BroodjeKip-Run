"""
TODO:
 - App search
 - More search engines
 - Scrollable results list
 - Open with hotkey
 - Command history
 - Command params: <command> -<param name> <param> <input>
    - File search: Search paths    (-p)
    - Web search: Search engine    (-s)
    - All commands: Help           (-h)
 - Settings .json file
 - Subtext in update_results()
"""

import customtkinter as ctk
from threading import Thread
from webbrowser import open as webopen
from urllib.parse import quote
import subprocess
import os

BG = "#141414"
SURFACE = "#2f2f2f"
TEXT = "#d0d0d0"
HEIGHT = 40
WIDTH = 400
FONT = "JetBrains Mono"
FULL_FONT_HEIGHT = 20
SECONDARY_FONT_HEIGHT = 16
ENGINE = "duckduckgo"
SEARCH_PATH = "/home/george"
SEARCH_ENGINES = {
    "google": "https://google.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/?q=",
    "bing": "https://bing.com/search?q=",
}

entered = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk()
root.configure(fg_color=BG)
root.title("")
root.resizable(False, False)
root.attributes("-topmost", True)
root.bind("<Escape>", lambda e: root.destroy())
root.bind("<FocusOut>", lambda e: root.destroy())

content = ctk.CTkFrame(root, fg_color=BG)
content.pack(fill="both", expand=True)

search_bar = ctk.CTkEntry(
    content, placeholder_text="Search...", font=(FONT, FULL_FONT_HEIGHT), width=WIDTH
)
search_bar.pack(fill="both")

results_frame = ctk.CTkScrollableFrame(content, fg_color=BG, height=200)

_resize_job = None
last_input = ""
_search_job = None


def _do_resize():
    root.update_idletasks()
    root.geometry(f"{WIDTH}x{root.winfo_reqheight()}")


def update_results(lines, files=False, scrollable=False):
    global _resize_job, results_frame

    current_scrollable = isinstance(results_frame, ctk.CTkScrollableFrame)
    if current_scrollable != scrollable:
        results_frame.destroy()
        if scrollable:
            results_frame = ctk.CTkScrollableFrame(content, fg_color=BG, height=200)
        else:
            results_frame = ctk.CTkFrame(content, fg_color=BG)
    for widget in results_frame.winfo_children():
        widget.destroy()

    if not scrollable:
        lines = [lines]

    for line in lines[:50]:
        if files:
            btn = ctk.CTkButton(
                results_frame,
                text=line,
                font=(FONT, SECONDARY_FONT_HEIGHT),
                text_color=TEXT,
                anchor="w",
                command=lambda p=line: open_file(p),
            )
            btn.pack(fill="x", padx=8)
        else:
            lbl = ctk.CTkLabel(
                results_frame,
                text=line,
                font=(FONT, SECONDARY_FONT_HEIGHT),
                text_color=TEXT,
                anchor="w",
            )
            lbl.pack(fill="x", padx=8)

    if lines:
        results_frame.pack(fill="x")
    else:
        results_frame.pack_forget()

    if _resize_job:
        root.after_cancel(_resize_job)
    _resize_job = root.after(50, _do_resize)


def clear_results():
    global _resize_job
    for widget in results_frame.winfo_children():
        widget.destroy()
    results_frame.pack_forget()
    if _resize_job:
        root.after_cancel(_resize_job)
    _resize_job = root.after(50, lambda: root.geometry(f"{WIDTH}x{HEIGHT}"))
    for widget in results_frame.winfo_children():
        widget.destroy()
    root.geometry(f"{WIDTH}x{HEIGHT}")


def on_enter():
    global entered
    entered = True


def open_file(path):
    if os.path.isfile(path):
        subprocess.Popen(["xdg-open", os.path.dirname(path)], stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", path], stderr=subprocess.DEVNULL)


def calculator(expr):
    try:
        return eval(expr)
    except (SyntaxError, NameError, ZeroDivisionError):
        return "Invalid expression"


def web_search(query):
    webopen(SEARCH_ENGINES[ENGINE] + quote(query))


def file_search(filename):
    def _search():
        try:
            out = subprocess.check_output(
                ["locate", "-i", "--", filename], stderr=subprocess.DEVNULL, text=True
            )
            lines = out.strip().splitlines()
            files = [l for l in lines if os.path.isfile(l)]
            dirs = [l for l in lines if os.path.isdir(l)]

            if files:
                results = files
            elif dirs:
                results = ["[DIR]: " + d for d in dirs]
            else:
                results = ["[DIR]: Not found"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            results = ["[ERR]: File search not available"]

        root.after(0, lambda: update_results(results, files=True, scrollable=True))

    if filename:
        update_results("[DIR]: Searching...")
        Thread(target=_search, daemon=True).start()
    else:
        update_results("[DIR]: Type filename...")


def main_loop():
    global entered, last_input, _search_job
    user_input = search_bar.get().strip()

    try:
        command = user_input[0]
        command_input = user_input[1:].strip()
    except IndexError:
        command = ""
        command_input = ""

    input_changed = user_input != last_input
    if input_changed:
        last_input = user_input

    if command == "=":
        if input_changed:
            result = calculator(command_input)
            update_results(f"[CAL]: {result}")
        if entered:
            result = calculator(command_input)
            root.clipboard_clear()
            root.clipboard_append(str(result))
            root.update()
            entered = False

    elif command == "?":
        if entered:
            web_search(command_input)
            entered = False
        elif input_changed:
            update_results("[WEB]: Press ENTER to search")

    elif command == ">":
        if input_changed:
            if _search_job:
                root.after_cancel(_search_job)
            _search_job = root.after(300, lambda: file_search(command_input))

    elif input_changed:
        clear_results()

    root.after(10, main_loop)


root.geometry(
    f"{WIDTH}x{HEIGHT}+{(root.winfo_screenwidth() - WIDTH) // 2}+{(root.winfo_screenheight() - HEIGHT) // 2}"
)

root.bind("<Return>", lambda e: on_enter())


def force_focus():
    root.focus_force()
    search_bar.focus_force()


root.after(50, force_focus)
main_loop()
root.mainloop()
