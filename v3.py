import tkinter as tk
import tkinter.font as tkfont
import subprocess
import math
import os
import re

# Configurable constants
WIDTH = 400
SEARCH_HEIGHT = 40
HEIGHT_OFFSET = -50
FONT = ("JetBrains Mono", 12)

# Non-configurable constants
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
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
root.geometry(  # Center the window to the screen
    f"{WIDTH}x{SEARCH_HEIGHT}+{(screen_w - WIDTH) // 2}+{(screen_h - SEARCH_HEIGHT) // 2 + HEIGHT_OFFSET}"
)
root.resizable(False, False)

search_var = tk.StringVar()
search_bar = tk.Entry(root, textvariable=search_var, font=FONT)
search_bar.pack(fill="x")

result_frame = tk.Canvas(root)


def main(*args):
    query = search_var.get()
    command, command_input, params = parse_query(query)

    if command == "=":
        result = calculator(command_input)
        update_result(result)
    else:
        result = "Type the command..."
        update_result(result)


def calculator(input):
    try:
        result = eval(input, MATH_NAMESPACE)
        if callable(result):
            raise TypeError
        if update_result:
            return f"= {result}"
        if entered:
            root.clipboard_clear()
            root.clipboard_append(result)
            root.update()
            search_bar.delete(1, "end")
            entered = False

    except (SyntaxError, NameError, ZeroDivisionError, TypeError):
        result = "Invalid expression"
        if update_result:
            return result


def parse_query(query):
    if not query:
        return "", "", {}

    command = query[0]
    query = query[1:].strip()

    params = {}
    for match in re.finditer(r"-(\w+)\s+(\S+)", query):
        params[match.group(1)] = match.group(2)

    command_input = re.sub(r"-\w+\s+\S+\s*", "", query).strip()

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


search_var.trace_add("write", main)
root.mainloop()
