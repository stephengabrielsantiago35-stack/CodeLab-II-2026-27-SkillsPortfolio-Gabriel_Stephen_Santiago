
import tkinter as tk
from tkinter import messagebox
import random
import os

# -----------------------------
# VARIABLES
# -----------------------------

jokes = []
current_joke = None

BG = "#F4F4F4"
BLUE = "#2878D0"
TEXT = "#222222"
GREY = "#777777"


# -----------------------------
# MAIN WINDOW
# -----------------------------

root = tk.Tk()
root.title("Alexa - Joke Assistant")
root.configure(bg=BG)
root.geometry("600x600")
root.resizable(False, False)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def make_label(parent, text, size=14, color=TEXT, bold=False):
    return tk.Label(
        parent,
        text=text,
        font=("Arial", size, "bold" if bold else "normal"),
        bg=parent["bg"],
        fg=color,
        wraplength=480,
        justify="center"
    )


def make_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 11),
        bg=BLUE,
        fg="white",
        activebackground="#1B65B0",
        activeforeground="white",
        relief="flat",
        padx=15,
        pady=8,
        cursor="hand2",
        width=22
    )


# -----------------------------
# LOAD JOKES
# -----------------------------

def load_jokes():

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "resources",
        "randomJokes.txt"
    )

    try:
        with open(file_path, "r", encoding="utf-8") as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("- "):
                    line = line[2:]

                setup, separator, punchline = line.partition("?")

                if separator and setup.strip() and punchline.strip():
                    jokes.append((
                        setup.strip() + "?",
                        punchline.strip()
                    ))

        return len(jokes)

    except FileNotFoundError:
        messagebox.showerror(
            "Error",
            "Could not find randomJokes.txt.\n"
            "Check your resources folder."
        )
        return 0

    except OSError as error:
        messagebox.showerror("File Error", str(error))
        return 0


# -----------------------------
# RANDOM JOKE
# -----------------------------

def random_joke():

    global current_joke

    if not jokes:
        return None

    available = [
        joke for joke in jokes
        if joke != current_joke
    ]

    if not available:
        available = jokes

    current_joke = random.choice(available)

    return current_joke


# -----------------------------
# TELL JOKE
# -----------------------------

def tell_joke():

    joke = random_joke()

    if joke is None:
        messagebox.showwarning(
            "No Jokes",
            "Please check your jokes text file."
        )
        return

    setup, punchline = joke

    setup_label.config(text=setup)
    punchline_label.config(text="")

    instruction_label.config(
        text="Click Show Punchline to reveal the answer."
    )

    punchline_button.config(state="normal")


# -----------------------------
# SHOW PUNCHLINE
# -----------------------------

def show_punchline():

    if current_joke is None:
        return

    setup, punchline = current_joke

    punchline_label.config(text=punchline)

    instruction_label.config(
        text="Hope that made you laugh!"
    )


# -----------------------------
# NEXT JOKE
# -----------------------------

def next_joke():
    tell_joke()


# -----------------------------
# QUIT
# -----------------------------

def quit_app():

    answer = messagebox.askyesno(
        "Quit",
        "Are you sure you want to quit?"
    )

    if answer:
        root.destroy()


# -----------------------------
# INTERFACE
# -----------------------------

make_label(
    root,
    "Alexa Joke Assistant",
    26,
    TEXT,
    True
).pack(pady=(45, 5))

make_label(
    root,
    "Need a laugh? Let me tell you a joke.",
    13,
    GREY
).pack(pady=5)


# Joke display

joke_frame = tk.Frame(root, bg="white")
joke_frame.pack(fill="x", padx=45, pady=15)

make_label(
    joke_frame,
    "YOUR JOKE",
    11,
    BLUE,
    True
).pack(pady=(25, 15))

setup_label = make_label(
    joke_frame,
    "Click the button below to get a joke!",
    20,
    TEXT,
    True
)
setup_label.pack(padx=20, pady=15)

punchline_label = make_label(
    joke_frame,
    "",
    16,
    BLUE,
    True
)
punchline_label.pack(padx=20, pady=10)

instruction_label = make_label(
    joke_frame,
    "Ready for a laugh?",
    11,
    GREY
)
instruction_label.pack(pady=(10, 25))


# Buttons

button_frame = tk.Frame(root, bg=BG)
button_frame.pack(pady=5)

make_button(
    button_frame,
    "Alexa, Tell Me a Joke",
    tell_joke
).pack(pady=3)

punchline_button = make_button(
    button_frame,
    "Show Punchline",
    show_punchline
)
punchline_button.config(state="disabled")
punchline_button.pack(pady=3)

make_button(
    button_frame,
    "Next Joke",
    next_joke
).pack(pady=3)

make_button(
    button_frame,
    "Quit",
    quit_app
).pack(pady=3)

# -----------------------------
# START APPLICATION
# -----------------------------

total_jokes = load_jokes()

if total_jokes > 0:
    instruction_label.config(
        text=f"{total_jokes} jokes loaded. Ready for a laugh?"
    )
else:
    instruction_label.config(
        text="No jokes loaded. Check your text file."
    )

root.mainloop()
