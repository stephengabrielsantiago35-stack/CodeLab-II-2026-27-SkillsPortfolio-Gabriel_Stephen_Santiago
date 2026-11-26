"""
The Academy Ledger
The records of every apprentice are in your hands.

A fantasy academy student records management system built with Python and Tkinter.
This application retains the existing Student Manager functionality and extends it
with sorting, adding, deleting, and updating student records.

All record changes are saved to resources/studentMarks.txt while preserving
the original file format.
"""

import csv
import os
import tkinter as tk
from tkinter import messagebox, ttk

# Optional Pillow support for fantasy imagery.
try:
    from PIL import Image, ImageTk  # type: ignore
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Optional audio support (fantasy background music).
try:
    import pygame  # type: ignore
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

try:
    import winsound
    WINSOUND_AVAILABLE = True
except Exception:
    WINSOUND_AVAILABLE = False


# =========================================================
# THEME CONSTANTS
# =========================================================
# Visual direction (defined before coding, guided by Anthropic frontend-design skill):
# A fantasy academy archive / enchanted ledger - midnight library atmosphere,
# parchment record panels, warm gold rules, muted sage archival accents.
# Signature element: a gold "ledger spine" with archival index marks along the left edge.
APP_TITLE = "THE ACADEMY LEDGER"
APP_SUBTITLE = "The records of every apprentice are in your hands."

# Palette (prompt-suggested, tuned for contrast and cohesion)
MIDNIGHT = "#101827"      # Midnight navy background
DEEP_NAVY = "#18263B"     # Deep blue panels
PARCHMENT = "#F0E4C8"     # Parchment record panels
PARCHMENT_DARK = "#DDD0B0"
GOLD = "#C9A45C"          # Warm gold accents/rules
GOLD_LIGHT = "#DEC48A"
SAGE = "#82927A"          # Muted sage secondary accent
INK = "#29271F"           # Dark ink text
MUTED = "#5E5648"
ERROR = "#8B3A3A"
SUCCESS = "#4F6A52"

# File paths (relative to this script for portability in VS Code).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FILE_PATH = os.path.join(RESOURCE_DIR, "studentMarks.txt")

# Optional asset paths (relative to this script; safe fallbacks if missing).
BACKGROUND_FALLBACK = os.path.join(ASSETS_DIR, "backgrounds", "archive.png")
ARCHIVIST_PATH = os.path.join(ASSETS_DIR, "characters", "archivist.png")
RECORDS_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "records.png")
CREST_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "academy_crest.png")
QUILL_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "quill.png")
BOOK_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "book.png")
MUSIC_PATH = os.path.join(ASSETS_DIR, "audio", "fantasy_theme.wav")


# =========================================================
# GLOBAL STATE
# =========================================================
students = []  # List of student record dictionaries.
root = None
content_frame = None
status_var = None
notice_var = None
table = None
current_records = []
current_view = "menu"
_images = {}
bg_canvas = None
bg_photo_ref = None
music_enabled = True
music_available = False


# =========================================================
# DATA CALCULATIONS
# =========================================================
def calculate_coursework_total(student):
    """Return total coursework marks out of 60."""
    return student["coursework1"] + student["coursework2"] + student["coursework3"]


def calculate_overall_total(student):
    """Return overall total out of 160 (coursework + exam)."""
    return calculate_coursework_total(student) + student["exam"]


def calculate_percentage(student):
    """Return overall percentage out of 160."""
    return (calculate_overall_total(student) / 160) * 100


def format_student_row(student):
    """Format a student record for display in the table."""
    return (
        student["code"],
        student["name"],
        student["coursework1"],
        student["coursework2"],
        student["coursework3"],
        student["exam"],
        calculate_overall_total(student),
    )


# =========================================================
# VALIDATION / NORMALISATION
# =========================================================
def normalise_student(record):
    """Validate and normalise a student record dictionary."""
    required = ["code", "name", "coursework1", "coursework2", "coursework3", "exam"]
    for key in required:
        if key not in record:
            raise ValueError(f"Missing field: {key}")

    code = str(record["code"]).strip()
    name = str(record["name"]).strip()

    if not (code.isdigit() and len(code) == 4):
        raise ValueError("Student code must be a 4-digit number (1000-9999).")
    if not (1000 <= int(code) <= 9999):
        raise ValueError("Student code must be between 1000 and 9999.")
    if not name:
        raise ValueError("Student name cannot be empty.")

    try:
        cw1 = int(record["coursework1"])
        cw2 = int(record["coursework2"])
        cw3 = int(record["coursework3"])
        exam = int(record["exam"])
    except (TypeError, ValueError):
        raise ValueError("Marks must be whole numbers.")

    for mark, label in ((cw1, "Coursework 1"), (cw2, "Coursework 2"), (cw3, "Coursework 3")):
        if not 0 <= mark <= 20:
            raise ValueError(f"{label} must be between 0 and 20.")
    if not 0 <= exam <= 100:
        raise ValueError("Exam mark must be between 0 and 100.")

    return {
        "code": code,
        "name": name,
        "coursework1": cw1,
        "coursework2": cw2,
        "coursework3": cw3,
        "exam": exam,
    }


def validate_student_input(code, name, cw1, cw2, cw3, exam, existing_code=None):
    """Validate user input for add/update. existing_code allows same record to keep its code."""
    student = normalise_student({
        "code": code,
        "name": name,
        "coursework1": cw1,
        "coursework2": cw2,
        "coursework3": cw3,
        "exam": exam,
    })
    for other in students:
        if other["code"] == student["code"] and other["code"] != existing_code:
            raise ValueError(f"Student code {student['code']} already exists.")
    return student


# =========================================================
# FILE HANDLING
# =========================================================
def ensure_resource_dir():
    """Ensure the resources directory exists."""
    os.makedirs(RESOURCE_DIR, exist_ok=True)


def load_students():
    """Load student records from resources/studentMarks.txt.

    Preserves the original file format:
    Line 1: number of students
    Remaining lines: code,name,coursework1,coursework2,coursework3,exam
    """
    global students
    students = []

    if not os.path.exists(FILE_PATH):
        show_notice("The archive could not locate studentMarks.txt in resources.", error=True)
        messagebox.showerror(
            "Archive File Missing",
            "studentMarks.txt was not found.\n\n"
            f"Expected location:\n{FILE_PATH}\n\n"
            "Please place the file in the resources folder."
        )
        return students

    try:
        with open(FILE_PATH, "r", newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))

        if not rows:
            raise ValueError("The studentMarks.txt file is empty.")

        try:
            expected_count = int(rows[0][0].strip())
        except Exception as exc:
            raise ValueError("The first line must contain the number of student records.") from exc

        loaded = []
        seen = set()
        for row_num, row in enumerate(rows[1:], start=2):
            if not row or all(not str(cell).strip() for cell in row):
                continue
            if len(row) != 6:
                raise ValueError(f"Row {row_num} is invalid: expected 6 values.")

            student = normalise_student({
                "code": row[0],
                "name": row[1],
                "coursework1": row[2],
                "coursework2": row[3],
                "coursework3": row[4],
                "exam": row[5],
            })
            if student["code"] in seen:
                raise ValueError(f"Duplicate student code found in file: {student['code']}")
            seen.add(student["code"])
            loaded.append(student)

        students = loaded
        if expected_count != len(students):
            messagebox.showwarning(
                "Archive Notice",
                f"The file header says {expected_count} records, but {len(students)} valid records were loaded."
            )
        show_notice("The Academy Ledger has been opened. Apprentice records are ready.", error=False)
        update_status()
        return students

    except (OSError, ValueError, IndexError) as exc:
        students = []
        show_notice("The archive could not read the student records.", error=True)
        messagebox.showerror("Archive Read Error", f"Could not load student records.\n\n{exc}")
        update_status()
        return students


def save_students():
    """Save all student records to studentMarks.txt in the original format."""
    ensure_resource_dir()
    temp_path = FILE_PATH + ".tmp"
    try:
        with open(temp_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([len(students)])
            for student in students:
                writer.writerow([
                    student["code"],
                    student["name"],
                    student["coursework1"],
                    student["coursework2"],
                    student["coursework3"],
                    student["exam"],
                ])
        os.replace(temp_path, FILE_PATH)
        update_status()
        return True
    except OSError as exc:
        show_notice("The archive could not inscribe the changes.", error=True)
        messagebox.showerror("Archive Save Error", f"Could not save student records.\n\n{exc}")
        return False


# =========================================================
# HELPERS
# =========================================================
def show_notice(message, error=False):
    """Display an academy notification in the status notice bar."""
    if notice_var is not None:
        marker = "⚠ " if error else "✦ "
        notice_var.set(marker + message)


def update_status():
    """Update record count status."""
    if status_var is not None:
        status_var.set(f"Apprentice Records: {len(students)}  |  Archive: resources/studentMarks.txt")


def find_students_by_query(query):
    """Find students by exact/partial name or exact code (case-insensitive)."""
    q = str(query).strip().lower()
    if not q:
        return []
    matches = []
    for student in students:
        if q == student["code"].lower() or q in student["name"].lower():
            matches.append(student)
    return matches


def get_student_by_code(code):
    """Return student by exact code, or None."""
    code = str(code).strip()
    for student in students:
        if student["code"] == code:
            return student
    return None


def academy_confirm(title, message):
    """Show a fantasy-themed confirmation dialog."""
    return messagebox.askyesno(title, message)


def academy_info(title, message):
    """Show a fantasy-themed information dialog."""
    messagebox.showinfo(title, message)


def academy_error(title, message):
    """Show a fantasy-themed error dialog."""
    messagebox.showerror(title, message)


# =========================================================
# AUDIO (optional fantasy background music)
# =========================================================
def init_music():
    """Initialize background music if an audio file and backend are available."""
    global music_available
    music_available = False
    if not os.path.exists(MUSIC_PATH):
        return False
    # Prefer pygame for mp3/wav/ogg; fall back to winsound for wav on Windows.
    if PYGAME_AVAILABLE:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(MUSIC_PATH)
            music_available = True
            return True
        except Exception:
            music_available = False
    if WINSOUND_AVAILABLE and MUSIC_PATH.lower().endswith(".wav"):
        try:
            music_available = True
            return True
        except Exception:
            music_available = False
    return False


def play_music():
    """Play fantasy background music in a loop if enabled."""
    global music_available
    if not music_enabled or not music_available or not os.path.exists(MUSIC_PATH):
        return
    try:
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            pygame.mixer.music.play(-1)  # loop forever
            return
    except Exception:
        pass
    try:
        if WINSOUND_AVAILABLE and MUSIC_PATH.lower().endswith(".wav"):
            winsound.PlaySound(MUSIC_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    except Exception:
        pass


def stop_music():
    """Stop background music."""
    try:
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
    try:
        if WINSOUND_AVAILABLE:
            winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass


def toggle_music():
    """Toggle fantasy background music on/off."""
    global music_enabled
    music_enabled = not music_enabled
    if music_enabled:
        play_music()
        show_notice("Fantasy music enabled.", error=False)
    else:
        stop_music()
        show_notice("Fantasy music muted.", error=False)
    update_music_button()


def update_music_button():
    """Update music button label if it exists."""
    btn = getattr(root, "_music_btn", None)
    if btn is not None:
        try:
            btn.config(text="Music: ON" if music_enabled else "Music: OFF")
        except Exception:
            pass


# =========================================================
# GUI STYLING
# =========================================================
def get_font(size=11, bold=False, family="Segoe UI"):
    """Return a readable body/UI font with fallback."""
    weight = "bold" if bold else "normal"
    return (family, size, weight)


def get_display_font(size=20, bold=True):
    """Return an elegant display font for titles and headings."""
    return ("Georgia", size, "bold" if bold else "normal")


def configure_styles():
    """Configure ttk styles for the fantasy academy theme."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Ledger.Treeview",
        background=PARCHMENT,
        fieldbackground=PARCHMENT,
        foreground=INK,
        rowheight=30,
        font=get_font(10, False),
        bordercolor=GOLD,
        borderwidth=1,
    )
    style.configure(
        "Ledger.Treeview.Heading",
        background=DEEP_NAVY,
        foreground=GOLD_LIGHT,
        font=("Georgia", 10, "bold"),
        relief="flat",
        padding=6,
    )
    style.map(
        "Ledger.Treeview",
        background=[("selected", PARCHMENT_DARK)],
        foreground=[("selected", INK)],
    )
    style.configure(
        "Gold.Vertical.TScrollbar",
        troughcolor=PARCHMENT_DARK,
        background=GOLD,
        bordercolor=GOLD,
        arrowcolor=INK,
    )


def load_image(path, size=None, darken=0.0):
    """Load an image using Pillow if available. darken=0..1 adds a dark overlay for readability."""
    if not PIL_AVAILABLE or not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.LANCZOS)
        if darken > 0:
            overlay = Image.new("RGBA", img.size, (16, 24, 39, int(255 * darken)))
            img = Image.alpha_composite(img, overlay)
        photo = ImageTk.PhotoImage(img)
        key = path + str(size) + str(darken)
        _images[key] = photo
        return photo
    except Exception:
        return None


def get_background_path():
    """Return the best available fallback background image path."""
    for p in [os.path.join(ASSETS_DIR, "backgrounds", "academy_library.jpg"), BACKGROUND_FALLBACK]:
        if os.path.exists(p):
            return p
    return None


# Per-screen backgrounds (all relative to project; missing files fall back gracefully).
SECTION_BACKGROUNDS = {
    "menu": os.path.join(ASSETS_DIR, "backgrounds", "academy_library.jpg"),
    "view": os.path.join(ASSETS_DIR, "backgrounds", "library_records.jpg"),
    "search": os.path.join(ASSETS_DIR, "backgrounds", "library_records.jpg"),
    "highest": os.path.join(ASSETS_DIR, "backgrounds", "library_records.jpg"),
    "lowest": os.path.join(ASSETS_DIR, "backgrounds", "library_records.jpg"),
    "sort": os.path.join(ASSETS_DIR, "backgrounds", "library_records.jpg"),
    "add": os.path.join(ASSETS_DIR, "backgrounds", "parchment_texture.jpg"),
    "delete": os.path.join(ASSETS_DIR, "backgrounds", "academy_night.jpg"),
    "update": os.path.join(ASSETS_DIR, "backgrounds", "parchment_texture.jpg"),
}


def set_section_background(section="menu"):
    """Update the content-area background image for the current section."""
    global bg_photo_ref
    if bg_canvas is None:
        return
    path = SECTION_BACKGROUNDS.get(section, get_background_path())
    if not path or not os.path.exists(path):
        path = get_background_path()
    # Use canvas size; fall back to a sensible default.
    w = max(bg_canvas.winfo_width(), 1200)
    h = max(bg_canvas.winfo_height(), 700)
    # Stronger darken for readability behind panels
    darken = 0.55 if section in ("menu", "delete") else 0.45
    photo = load_image(path, size=(w, h), darken=darken) if path else None
    bg_canvas.delete("bg")
    if photo:
        bg_canvas.create_image(0, 0, image=photo, anchor="nw", tags="bg")
        bg_photo_ref = photo
    else:
        bg_canvas.create_rectangle(0, 0, w, h, fill=MIDNIGHT, outline="", tags="bg")
        bg_photo_ref = None
    bg_canvas.tag_lower("bg")


def make_button(parent, text, command, width=24, primary=True):
    """Create a styled fantasy-themed button."""
    bg = GOLD if primary else DEEP_NAVY
    fg = INK if primary else GOLD_LIGHT
    active_bg = GOLD_LIGHT if primary else MIDNIGHT
    active_fg = INK if primary else GOLD_LIGHT
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=get_font(10, True),
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=active_fg,
        relief="flat",
        bd=0,
        padx=12,
        pady=8,
        width=width,
        cursor="hand2",
        highlightthickness=2,
        highlightbackground=GOLD,
        highlightcolor=GOLD_LIGHT,
    )

    def on_enter(_e):
        btn.config(bg=active_bg, fg=active_fg)

    def on_leave(_e):
        btn.config(bg=bg, fg=fg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


def clear_content():
    """Clear the main content area."""
    global table
    for widget in content_frame.winfo_children():
        widget.destroy()
    table = None


# =========================================================
# LAYOUT BUILDERS
# =========================================================
def build_header(parent):
    """Build the fantasy academy header with a dramatic archive background."""
    header = tk.Frame(parent, bg=MIDNIGHT, highlightbackground=GOLD, highlightthickness=2)
    header.pack(fill="x", padx=14, pady=(14, 8))

    # Decorative hero strip with background image.
    strip = tk.Canvas(header, height=170, bg=DEEP_NAVY, highlightthickness=0)
    strip.pack(fill="x")
    bg_path = get_background_path()
    bg_img = load_image(bg_path, size=(1400, 170), darken=0.45) if bg_path else None
    if bg_img:
        strip.create_image(0, 0, image=bg_img, anchor="nw")
    else:
        # Fallback gradient-like bands
        for i in range(170):
            r = int(16 + (24 - 16) * i / 170)
            g = int(24 + (38 - 24) * i / 170)
            b = int(39 + (59 - 39) * i / 170)
            strip.create_line(0, i, 1400, i, fill=f"#{r:02x}{g:02x}{b:02x}")

    # Gold frame and ornamental lines
    strip.create_rectangle(12, 12, 1388, 158, outline=GOLD, width=2)
    strip.create_line(28, 108, 520, 108, fill=GOLD_LIGHT, width=1)
    strip.create_text(32, 34, anchor="nw", text=APP_TITLE, fill=GOLD_LIGHT, font=get_display_font(30, True))
    strip.create_text(34, 76, anchor="nw", text=APP_SUBTITLE, fill=PARCHMENT, font=get_font(12, False, "Georgia"))
    strip.create_text(34, 122, anchor="nw", text="Enchanted Archive  •  Apprentice Records  •  Archivist Console",
                      fill=SAGE, font=get_font(9, True))

    icon = load_image(CREST_ICON_PATH, size=(64, 64)) or load_image(RECORDS_ICON_PATH, size=(56, 56))
    if icon:
        strip.create_image(1325, 85, image=icon)

    # Notice bar
    notice_bar = tk.Frame(header, bg=DEEP_NAVY, highlightbackground=GOLD, highlightthickness=1)
    notice_bar.pack(fill="x")
    tk.Label(
        notice_bar,
        textvariable=notice_var,
        bg=DEEP_NAVY,
        fg=GOLD_LIGHT,
        font=get_font(10, False),
        anchor="w",
        padx=12,
        pady=8,
    ).pack(fill="x")


def build_status_bar(parent):
    """Build bottom status bar."""
    bar = tk.Frame(parent, bg=DEEP_NAVY, highlightbackground=GOLD, highlightthickness=1)
    bar.pack(fill="x", padx=14, pady=(8, 14))
    tk.Label(
        bar,
        textvariable=status_var,
        bg=DEEP_NAVY,
        fg=PARCHMENT,
        font=get_font(9, True),
        anchor="w",
        padx=12,
        pady=8,
    ).pack(side="left", fill="x", expand=True)
    root._music_btn = make_button(bar, "Music: ON" if music_enabled else "Music: OFF", toggle_music, width=12, primary=False)
    root._music_btn.pack(side="right", padx=6, pady=6)
    make_button(bar, "Return to Ledger", show_main_menu, width=16, primary=False).pack(side="right", padx=6, pady=6)
    make_button(bar, "Close Ledger", exit_app, width=14, primary=True).pack(side="right", padx=6, pady=6)


def build_nav_bar(parent, active=None):
    """Create a navigation bar connecting every page/screen."""
    set_section_background(active or current_view or "menu")
    nav = tk.Frame(parent, bg=DEEP_NAVY, highlightbackground=GOLD, highlightthickness=1)
    nav.pack(fill="x", padx=16, pady=(8, 0))
    items = [
        ("Menu", show_main_menu, "menu"),
        ("All Records", display_all_records, "view"),
        ("Search", search_student, "search"),
        ("Highest", show_highest_total, "highest"),
        ("Lowest", show_lowest_total, "lowest"),
        ("Sort", sort_student_records, "sort"),
        ("Add", add_student_record, "add"),
        ("Delete", delete_student_record, "delete"),
        ("Update", update_student_record, "update"),
    ]
    for label, cmd, key in items:
        is_active = (active == key)
        bg = GOLD if is_active else DEEP_NAVY
        fg = INK if is_active else GOLD_LIGHT
        btn = tk.Button(
            nav, text=label, command=cmd, font=get_font(9, True),
            bg=bg, fg=fg, activebackground=GOLD_LIGHT, activeforeground=INK,
            relief="flat", bd=0, padx=8, pady=6, cursor="hand2"
        )
        btn.pack(side="left", padx=2, pady=4)
        def mk_hover(b=btn, a=is_active, nbg=bg, nfg=fg):
            b.bind("<Enter>", lambda _e: b.config(bg=GOLD_LIGHT, fg=INK))
            b.bind("<Leave>", lambda _e: b.config(bg=GOLD if a else nbg, fg=INK if a else nfg))
        mk_hover()
    return nav


def parchment_panel(parent, title="Academy Ledger"):
    """Create a parchment-inspired panel with a gold frame and depth."""
    shadow = tk.Frame(parent, bg="#0B1422")
    shadow.pack(fill="both", expand=True, padx=16, pady=10)
    outer = tk.Frame(shadow, bg=GOLD, padx=2, pady=2)
    outer.pack(fill="both", expand=True, padx=(0, 2), pady=(0, 2))
    inner = tk.Frame(outer, bg=PARCHMENT, highlightbackground=GOLD, highlightthickness=1)
    inner.pack(fill="both", expand=True)
    heading = tk.Frame(inner, bg=DEEP_NAVY)
    heading.pack(fill="x")
    # Gold accent line under heading
    tk.Label(
        heading,
        text=title,
        bg=DEEP_NAVY,
        fg=GOLD_LIGHT,
        font=get_display_font(13, True),
        pady=9,
        padx=12,
        anchor="w",
    ).pack(fill="x")
    tk.Frame(inner, bg=GOLD, height=2).pack(fill="x")
    body = tk.Frame(inner, bg=PARCHMENT)
    body.pack(fill="both", expand=True, padx=16, pady=14)
    return body


# =========================================================
# TABLE / RECORD DISPLAY
# =========================================================
def refresh_table(records=None):
    """Refresh the student record table."""
    global current_records
    if table is None:
        return
    if records is not None:
        current_records = list(records)

    for item in table.get_children():
        table.delete(item)

    for i, student in enumerate(current_records):
        tag = "even" if i % 2 == 0 else "odd"
        table.insert("", "end", values=format_student_row(student), tags=(tag,))

    table.tag_configure("even", background=PARCHMENT)
    table.tag_configure("odd", background=PARCHMENT_DARK)
    update_status()


def create_records_table(parent, records, title="Apprentice Records"):
    """Create a clear table with headings and calculated totals."""
    global table, current_records
    current_records = list(records)

    body = parchment_panel(parent, title)
    table_frame = tk.Frame(body, bg=PARCHMENT)
    table_frame.pack(fill="both", expand=True)

    columns = ("code", "name", "cw1", "cw2", "cw3", "exam", "total")
    headings = {
        "code": "Student Code",
        "name": "Student Name",
        "cw1": "Coursework 1",
        "cw2": "Coursework 2",
        "cw3": "Coursework 3",
        "exam": "Exam Mark",
        "total": "Total",
    }
    widths = {"code": 110, "name": 240, "cw1": 110, "cw2": 110, "cw3": 110, "exam": 100, "total": 90}

    table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Ledger.Treeview", height=12)
    for col in columns:
        table.heading(col, text=headings[col])
        anchor = "w" if col == "name" else "center"
        table.column(col, width=widths[col], anchor=anchor, stretch=True)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview, style="Gold.Vertical.TScrollbar")
    table.configure(yscrollcommand=vsb.set)
    table.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    refresh_table(current_records)
    return body


def show_info_panel(parent, student, panel_title="Apprentice Profile"):
    """Display a parchment-inspired student information panel."""
    shadow = tk.Frame(parent, bg="#0B1422")
    shadow.pack(fill="x", padx=16, pady=(0, 10))
    panel_outer = tk.Frame(shadow, bg=GOLD, padx=2, pady=2)
    panel_outer.pack(fill="x", padx=(0, 2), pady=(0, 2))
    panel = tk.Frame(panel_outer, bg=PARCHMENT, highlightbackground=GOLD, highlightthickness=1)
    panel.pack(fill="x")
    tk.Label(panel, text=panel_title, bg=DEEP_NAVY, fg=GOLD_LIGHT, font=get_display_font(12, True), pady=8, padx=12, anchor="w").pack(fill="x")
    tk.Frame(panel, bg=GOLD, height=2).pack(fill="x")

    details = tk.Frame(panel, bg=PARCHMENT)
    details.pack(fill="x", padx=16, pady=12)
    total = calculate_overall_total(student)
    pct = calculate_percentage(student)
    rows = [
        ("Student Code", student["code"]),
        ("Student Name", student["name"]),
        ("Coursework 1", f"{student['coursework1']} / 20"),
        ("Coursework 2", f"{student['coursework2']} / 20"),
        ("Coursework 3", f"{student['coursework3']} / 20"),
        ("Coursework Total", f"{calculate_coursework_total(student)} / 60"),
        ("Exam Mark", f"{student['exam']} / 100"),
        ("Overall Total", f"{total} / 160"),
        ("Percentage", f"{pct:.2f}%"),
    ]
    for label, value in rows:
        row = tk.Frame(details, bg=PARCHMENT)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label + ":", width=18, anchor="w", bg=PARCHMENT, fg=MUTED, font=get_font(10, True)).pack(side="left")
        tk.Label(row, text=str(value), anchor="w", bg=PARCHMENT, fg=INK, font=get_font(10, False)).pack(side="left")



# =========================================================
# MENU / NAVIGATION
# =========================================================
def show_main_menu():
    """Display the main Academy Ledger navigation menu."""
    global current_view
    current_view = "menu"
    clear_content()
    build_nav_bar(content_frame, active="menu")
    show_notice("Select an action from the Academy Ledger.", error=False)

    body = parchment_panel(content_frame, "Academy Ledger — Main Menu")
    intro = tk.Label(
        body,
        text="Welcome, Archivist. Choose a ledger action below.",
        bg=PARCHMENT,
        fg=INK,
        font=get_font(11, False),
        pady=6,
    )
    intro.pack(anchor="w")

    btn_frame = tk.Frame(body, bg=PARCHMENT)
    btn_frame.pack(pady=12)

    menu_items = [
        ("1. View Academy Ledger (Display All Records)", display_all_records),
        ("2. Search the Archive (Search for a Student)", search_student),
        ("3. Highest Total (Top Apprentice)", show_highest_total),
        ("4. Lowest Total (Needs Guidance)", show_lowest_total),
        ("5. Sort Student Records", sort_student_records),
        ("6. Enroll Apprentice (Add Student Record)", add_student_record),
        ("7. Remove Academy Record (Delete Student)", delete_student_record),
        ("8. Revise Apprentice Profile (Update Student)", update_student_record),
    ]

    for text, cmd in menu_items:
        make_button(btn_frame, text, cmd, width=44, primary=True).pack(pady=4)

    tk.Label(
        body,
        text="Tip: Press keys 1-8 on the main menu for quick access.",
        bg=PARCHMENT,
        fg=MUTED,
        font=get_font(9, False),
        pady=8,
    ).pack()


# =========================================================
# OPTION 1 - DISPLAY ALL RECORDS
# =========================================================
def display_all_records(records=None, title="Academy Ledger — All Apprentice Records"):
    """Menu option 1: display all student records in a clear table."""
    global current_view
    current_view = "view"
    clear_content()
    build_nav_bar(content_frame, active="view")
    display_records = list(students) if records is None else list(records)

    if not display_records:
        body = parchment_panel(content_frame, title)
        tk.Label(body, text="No apprentice records are currently in the archive.", bg=PARCHMENT, fg=INK,
                 font=get_font(11, False), pady=30).pack()
        make_button(body, "Return to Ledger", show_main_menu, width=20).pack(pady=10)
        return

    create_records_table(content_frame, display_records, title=title)

    # Summary panel
    avg = sum(calculate_overall_total(s) for s in display_records) / len(display_records)
    summary_shadow = tk.Frame(content_frame, bg="#0B1422")
    summary_shadow.pack(fill="x", padx=16, pady=(0, 10))
    summary_outer = tk.Frame(summary_shadow, bg=GOLD, padx=1, pady=1)
    summary_outer.pack(fill="x", padx=(0, 2), pady=(0, 2))
    summary = tk.Frame(summary_outer, bg=DEEP_NAVY)
    summary.pack(fill="x")
    tk.Label(
        summary,
        text=f"Records shown: {len(display_records)}    |    Class Average Total: {avg:.2f} / 160",
        bg=DEEP_NAVY, fg=GOLD_LIGHT, font=get_font(10, True), pady=9
    ).pack()
    make_button(content_frame, "Return to Ledger", show_main_menu, width=20).pack(pady=(0, 8))
    show_notice("Displaying apprentice records from the Academy Ledger.", error=False)


# =========================================================
# OPTION 2 - SEARCH
# =========================================================
def search_student():
    """Menu option 2: search for a student by name or student code."""
    global current_view
    current_view = "search"
    clear_content()
    build_nav_bar(content_frame, active="search")
    show_notice("Search the archive by apprentice name or student code.", error=False)

    body = parchment_panel(content_frame, "Search the Archive")
    book = load_image(BOOK_ICON_PATH, size=(40, 40)) or load_image(QUILL_ICON_PATH, size=(40, 40))
    if book:
        bl = tk.Label(body, image=book, bg=PARCHMENT)
        bl.image = book
        bl.place(relx=1.0, x=-12, y=8, anchor="ne")
    tk.Label(body, text="Enter student name or student code:", bg=PARCHMENT, fg=INK, font=get_font(10, True)).pack(anchor="w")
    query_var = tk.StringVar()
    entry = tk.Entry(body, textvariable=query_var, font=get_font(11, False), bg="#FFFDF5", fg=INK,
                     insertbackground=INK, relief="solid", bd=1)
    entry.pack(fill="x", pady=8, ipady=6)
    entry.focus_set()

    result_area = tk.Frame(content_frame, bg=MIDNIGHT)
    result_area.pack(fill="both", expand=True)

    def do_search():
        for w in result_area.winfo_children():
            w.destroy()
        query = query_var.get().strip()
        if not query:
            show_notice("Please enter a name or student code to search the archive.", error=True)
            academy_error("Archive Search", "Please enter a student name or student code.")
            return
        matches = find_students_by_query(query)
        if not matches:
            show_notice("No matching apprentice record was found in the archive.", error=True)
            body2 = parchment_panel(result_area, "Search Results")
            tk.Label(body2, text="No matching student record found.", bg=PARCHMENT, fg=ERROR,
                     font=get_font(11, True), pady=20).pack()
            return
        show_notice(f"Found {len(matches)} matching apprentice record(s).", error=False)
        create_records_table(result_area, matches, title="Search the Archive — Matching Records")
        if len(matches) == 1:
            show_info_panel(result_area, matches[0], panel_title="Apprentice Profile")

    btn_row = tk.Frame(body, bg=PARCHMENT)
    btn_row.pack(fill="x", pady=4)
    make_button(btn_row, "Search Archive", do_search, width=16).pack(side="left", padx=(0, 8))
    make_button(btn_row, "Return to Ledger", show_main_menu, width=16, primary=False).pack(side="left")
    entry.bind("<Return>", lambda _e: do_search())


# =========================================================
# OPTION 3 & 4 - HIGHEST / LOWEST
# =========================================================
def show_highest_total():
    """Menu option 3: find the student with the highest total."""
    clear_content()
    build_nav_bar(content_frame, active="highest")
    if not students:
        show_notice("No apprentice records available.", error=True)
        display_all_records([])
        return
    student = max(students, key=lambda s: calculate_overall_total(s))
    show_notice(f"Top apprentice identified: {student['name']} ({calculate_overall_total(student)}/160).", error=False)
    show_extreme_student(student, "Highest Total — Top Apprentice")


def show_lowest_total():
    """Menu option 4: find the student with the lowest total."""
    clear_content()
    build_nav_bar(content_frame, active="lowest")
    if not students:
        show_notice("No apprentice records available.", error=True)
        display_all_records([])
        return
    student = min(students, key=lambda s: calculate_overall_total(s))
    show_notice(f"Apprentice needing guidance: {student['name']} ({calculate_overall_total(student)}/160).", error=False)
    show_extreme_student(student, "Lowest Total — Apprentice Needs Guidance")


def show_extreme_student(student, title):
    """Display a highlighted student record for highest/lowest total."""
    create_records_table(content_frame, [student], title=title)
    show_info_panel(content_frame, student, panel_title="Parchment Apprentice Profile")
    make_button(content_frame, "Return to Ledger", show_main_menu, width=20).pack(pady=(0, 8))


# =========================================================
# OPTION 5 - SORT
# =========================================================
def sort_student_records():
    """Menu option 5: sort records in ascending or descending order."""
    clear_content()
    build_nav_bar(content_frame, active="sort")
    show_notice("Arrange the apprentice records by your chosen order.", error=False)

    body = parchment_panel(content_frame, "Sort Student Records")
    controls = tk.Frame(body, bg=PARCHMENT)
    controls.pack(fill="x", pady=4)

    tk.Label(controls, text="Sort by:", bg=PARCHMENT, fg=INK, font=get_font(10, True)).grid(row=0, column=0, sticky="w", pady=4)
    field_var = tk.StringVar(value="Overall Total")
    field_box = ttk.Combobox(controls, textvariable=field_var, state="readonly", width=28,
                             values=["Student Code", "Student Name", "Overall Total"])
    field_box.grid(row=0, column=1, padx=8, pady=4, sticky="w")

    tk.Label(controls, text="Order:", bg=PARCHMENT, fg=INK, font=get_font(10, True)).grid(row=1, column=0, sticky="w", pady=4)
    order_var = tk.StringVar(value="Ascending")
    order_box = ttk.Combobox(controls, textvariable=order_var, state="readonly", width=28,
                             values=["Ascending", "Descending"])
    order_box.grid(row=1, column=1, padx=8, pady=4, sticky="w")

    result_area = tk.Frame(content_frame, bg=MIDNIGHT)
    result_area.pack(fill="both", expand=True)

    def do_sort():
        for w in result_area.winfo_children():
            w.destroy()
        if not students:
            show_notice("There are no records to sort.", error=True)
            academy_error("Sort Records", "No student records available to sort.")
            return

        field = field_var.get()
        descending = order_var.get() == "Descending"
        if field == "Student Code":
            key_fn = lambda s: int(s["code"])
        elif field == "Student Name":
            key_fn = lambda s: s["name"].lower()
        else:
            key_fn = lambda s: calculate_overall_total(s)

        sorted_records = sorted(students, key=key_fn, reverse=descending)
        show_notice(f"Records arranged by {field.lower()} ({order_var.get().lower()}).", error=False)
        create_records_table(result_area, sorted_records, title=f"Sorted Records — {field} ({order_var.get()})")

        # Optional save: only if user explicitly chooses.
        action_row = tk.Frame(result_area, bg=MIDNIGHT)
        action_row.pack(fill="x", padx=14, pady=(0, 8))

        def save_sorted():
            if academy_confirm("Archive Confirmation", "Save this sorted order to studentMarks.txt?"):
                code_order = [s["code"] for s in sorted_records]
                by_code = {s["code"]: s for s in students}
                reordered = [by_code[c] for c in code_order if c in by_code]
                for s in students:
                    if s["code"] not in code_order:
                        reordered.append(s)
                students[:] = reordered
                if save_students():
                    show_notice("Sorted order has been inscribed into the archive.", error=False)
                    academy_info("Archive Updated", "The sorted order was saved to studentMarks.txt.")

        make_button(action_row, "Save Sorted Order", save_sorted, width=18).pack(side="left", padx=4)
        make_button(action_row, "Return to Ledger", show_main_menu, width=18, primary=False).pack(side="left", padx=4)

    btn_row = tk.Frame(controls, bg=PARCHMENT)
    btn_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
    make_button(btn_row, "Sort Records", do_sort, width=16).pack(side="left", padx=(0, 8))
    make_button(btn_row, "Return to Ledger", show_main_menu, width=16, primary=False).pack(side="left")




# =========================================================
# OPTION 6 - ADD
# =========================================================
def add_student_record():
    """Menu option 6: add a new student record (Enroll Apprentice)."""
    clear_content()
    build_nav_bar(content_frame, active="add")
    show_notice("Enroll a new apprentice into the Academy Ledger.", error=False)

    body = parchment_panel(content_frame, "Enroll Apprentice — Add Student Record")
    quill = load_image(QUILL_ICON_PATH, size=(48, 48))
    if quill:
        ql = tk.Label(body, image=quill, bg=PARCHMENT)
        ql.image = quill
        ql.place(relx=1.0, x=-12, y=8, anchor="ne")
    form = tk.Frame(body, bg=PARCHMENT)
    form.pack(fill="x", pady=8)

    fields = [
        ("Student Code (1000-9999)", "code"),
        ("Student Name", "name"),
        ("Coursework 1 (0-20)", "cw1"),
        ("Coursework 2 (0-20)", "cw2"),
        ("Coursework 3 (0-20)", "cw3"),
        ("Exam Mark (0-100)", "exam"),
    ]
    vars_map = {}
    for i, (label, key) in enumerate(fields):
        tk.Label(form, text=label + ":", bg=PARCHMENT, fg=INK, font=get_font(10, True), anchor="w").grid(
            row=i, column=0, sticky="w", padx=(0, 12), pady=5
        )
        var = tk.StringVar()
        vars_map[key] = var
        entry = tk.Entry(form, textvariable=var, font=get_font(10, False), bg="#FFFDF5", fg=INK,
                         insertbackground=INK, relief="solid", bd=1, width=32)
        entry.grid(row=i, column=1, sticky="w", pady=5, ipady=4)
        if i == 0:
            entry.focus_set()

    def submit():
        try:
            student = validate_student_input(
                vars_map["code"].get(),
                vars_map["name"].get(),
                vars_map["cw1"].get(),
                vars_map["cw2"].get(),
                vars_map["cw3"].get(),
                vars_map["exam"].get(),
            )
        except ValueError as exc:
            show_notice(str(exc), error=True)
            academy_error("Enrollment Failed", str(exc))
            return

        students.append(student)
        if save_students():
            show_notice(f"Apprentice {student['name']} has been enrolled in the archive.", error=False)
            academy_info(
                "Apprentice Enrolled",
                f"{student['name']} ({student['code']}) has been added to the Academy Ledger."
            )
            display_all_records()
        else:
            students.remove(student)  # Roll back if save failed.

    btn_row = tk.Frame(body, bg=PARCHMENT)
    btn_row.pack(fill="x", pady=12)
    make_button(btn_row, "Enroll Apprentice", submit, width=18).pack(side="left", padx=(0, 8))
    make_button(btn_row, "Return to Ledger", show_main_menu, width=18, primary=False).pack(side="left")


# =========================================================
# OPTION 7 - DELETE
# =========================================================
def delete_student_record():
    """Menu option 7: delete a student record (Remove Academy Record)."""
    clear_content()
    build_nav_bar(content_frame, active="delete")
    show_notice("Search the archive for the apprentice record to remove.", error=False)

    body = parchment_panel(content_frame, "Remove Academy Record — Delete Student")
    tk.Label(body, text="Identify student by name or student code:", bg=PARCHMENT, fg=INK, font=get_font(10, True)).pack(anchor="w")
    query_var = tk.StringVar()
    entry = tk.Entry(body, textvariable=query_var, font=get_font(11, False), bg="#FFFDF5", fg=INK,
                     insertbackground=INK, relief="solid", bd=1)
    entry.pack(fill="x", pady=8, ipady=6)
    entry.focus_set()

    result_area = tk.Frame(content_frame, bg=MIDNIGHT)
    result_area.pack(fill="both", expand=True)

    def do_find():
        for w in result_area.winfo_children():
            w.destroy()
        query = query_var.get().strip()
        if not query:
            show_notice("Please enter a name or student code.", error=True)
            academy_error("Remove Record", "Please enter a student name or student code.")
            return
        matches = find_students_by_query(query)
        if not matches:
            show_notice("No matching apprentice record found. Nothing was removed.", error=True)
            academy_error("Record Not Found", "No matching student record was found.")
            return

        show_notice(f"Found {len(matches)} matching record(s). Select one to remove.", error=False)
        panel_body = parchment_panel(result_area, "Select Record to Remove")
        table_frame = tk.Frame(panel_body, bg=PARCHMENT)
        table_frame.pack(fill="both", expand=True)

        columns = ("code", "name", "cw1", "cw2", "cw3", "exam", "total")
        local_table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Ledger.Treeview", height=min(8, len(matches) + 1))
        headings = {"code": "Student Code", "name": "Student Name", "cw1": "CW1", "cw2": "CW2", "cw3": "CW3", "exam": "Exam", "total": "Total"}
        widths = {"code": 100, "name": 220, "cw1": 70, "cw2": 70, "cw3": 70, "exam": 80, "total": 80}
        for col in columns:
            local_table.heading(col, text=headings[col])
            local_table.column(col, width=widths[col], anchor="w" if col == "name" else "center")
        local_table.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=local_table.yview, style="Gold.Vertical.TScrollbar")
        local_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        iid_to_code = {}
        for i, s in enumerate(matches):
            iid = local_table.insert("", "end", values=format_student_row(s), tags=("even" if i % 2 == 0 else "odd",))
            iid_to_code[iid] = s["code"]
        local_table.tag_configure("even", background=PARCHMENT)
        local_table.tag_configure("odd", background=PARCHMENT_DARK)

        def confirm_delete():
            sel = local_table.selection()
            if not sel:
                show_notice("Select a record to remove.", error=True)
                academy_error("Remove Record", "Please select a student record to delete.")
                return
            student = get_student_by_code(iid_to_code.get(sel[0]))
            if not student:
                academy_error("Record Not Found", "The selected student could not be found.")
                return

            # Confirmation before deleting (academy notification style).
            confirmed = academy_confirm(
                "Academy Confirmation — Remove Record",
                f"Are you sure you want to remove this apprentice from the Academy Ledger?\n\n"
                f"Student Code: {student['code']}\n"
                f"Student Name: {student['name']}\n\n"
                "This action will update studentMarks.txt."
            )
            if not confirmed:
                show_notice("Removal cancelled. The apprentice record remains in the archive.", error=False)
                return

            idx = students.index(student)
            removed = students.pop(idx)
            if save_students():
                show_notice(f"{removed['name']} has been removed from the Academy Ledger.", error=False)
                academy_info("Record Removed", f"{removed['name']} ({removed['code']}) was removed from the archive.")
                display_all_records()
            else:
                students.insert(idx, removed)  # Roll back on save failure.

        action_row = tk.Frame(panel_body, bg=PARCHMENT)
        action_row.pack(fill="x", pady=10)
        make_button(action_row, "Remove Selected Record", confirm_delete, width=20).pack(side="left", padx=(0, 8))
        make_button(action_row, "Cancel", show_main_menu, width=12, primary=False).pack(side="left")

    btn_row = tk.Frame(body, bg=PARCHMENT)
    btn_row.pack(fill="x", pady=4)
    make_button(btn_row, "Find Record", do_find, width=16).pack(side="left", padx=(0, 8))
    make_button(btn_row, "Return to Ledger", show_main_menu, width=16, primary=False).pack(side="left")
    entry.bind("<Return>", lambda _e: do_find())




# =========================================================
# OPTION 8 - UPDATE
# =========================================================
def update_student_record():
    """Menu option 8: update a student record (Revise Apprentice Profile)."""
    clear_content()
    build_nav_bar(content_frame, active="update")
    show_notice("Search the archive for the apprentice record to revise.", error=False)

    body = parchment_panel(content_frame, "Revise Apprentice Profile — Update Student Record")
    tk.Label(body, text="Identify student by name or student code:", bg=PARCHMENT, fg=INK, font=get_font(10, True)).pack(anchor="w")
    query_var = tk.StringVar()
    entry = tk.Entry(body, textvariable=query_var, font=get_font(11, False), bg="#FFFDF5", fg=INK,
                     insertbackground=INK, relief="solid", bd=1)
    entry.pack(fill="x", pady=8, ipady=6)
    entry.focus_set()

    result_area = tk.Frame(content_frame, bg=MIDNIGHT)
    result_area.pack(fill="both", expand=True)

    def open_edit_form(student):
        """Open an edit form for the selected student."""
        for w in result_area.winfo_children():
            w.destroy()
        show_notice(f"Revising apprentice profile: {student['name']} ({student['code']}).", error=False)

        edit_body = parchment_panel(result_area, f"Revise Apprentice Profile — {student['name']}")
        quill = load_image(QUILL_ICON_PATH, size=(48, 48))
        if quill:
            ql = tk.Label(edit_body, image=quill, bg=PARCHMENT)
            ql.image = quill
            ql.place(relx=1.0, x=-12, y=8, anchor="ne")
        form = tk.Frame(edit_body, bg=PARCHMENT)
        form.pack(fill="x", pady=8)

        # Editable fields: name and marks. Code is kept as identity but shown read-only.
        tk.Label(form, text="Student Code (identity):", bg=PARCHMENT, fg=INK, font=get_font(10, True)).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=5)
        code_var = tk.StringVar(value=student["code"])
        code_entry = tk.Entry(form, textvariable=code_var, font=get_font(10, False), bg=PARCHMENT_DARK, fg=INK,
                              relief="solid", bd=1, width=32, state="readonly")
        code_entry.grid(row=0, column=1, sticky="w", pady=5, ipady=4)

        fields = [
            ("Student Name", "name", student["name"]),
            ("Coursework 1 (0-20)", "cw1", str(student["coursework1"])),
            ("Coursework 2 (0-20)", "cw2", str(student["coursework2"])),
            ("Coursework 3 (0-20)", "cw3", str(student["coursework3"])),
            ("Exam Mark (0-100)", "exam", str(student["exam"])),
        ]
        vars_map = {}
        for i, (label, key, value) in enumerate(fields, start=1):
            tk.Label(form, text=label + ":", bg=PARCHMENT, fg=INK, font=get_font(10, True)).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=5)
            var = tk.StringVar(value=value)
            vars_map[key] = var
            ent = tk.Entry(form, textvariable=var, font=get_font(10, False), bg="#FFFDF5", fg=INK,
                           insertbackground=INK, relief="solid", bd=1, width=32)
            ent.grid(row=i, column=1, sticky="w", pady=5, ipady=4)

        def apply_changes():
            try:
                updated = validate_student_input(
                    student["code"],  # Code unchanged
                    vars_map["name"].get(),
                    vars_map["cw1"].get(),
                    vars_map["cw2"].get(),
                    vars_map["cw3"].get(),
                    vars_map["exam"].get(),
                    existing_code=student["code"],
                )
            except ValueError as exc:
                show_notice(str(exc), error=True)
                academy_error("Revision Failed", str(exc))
                return

            confirmed = academy_confirm(
                "Academy Confirmation — Revise Record",
                f"Save changes to apprentice {student['name']} ({student['code']})?"
            )
            if not confirmed:
                show_notice("Revision cancelled. No changes were inscribed.", error=False)
                return

            old = dict(student)
            student.update(updated)
            if save_students():
                show_notice(f"Apprentice profile for {student['name']} has been revised.", error=False)
                academy_info("Record Revised", "The student record was updated and saved to studentMarks.txt.")
                display_all_records([student], title="Revised Apprentice Record")
            else:
                student.update(old)  # Roll back on save failure.

        btn_row = tk.Frame(edit_body, bg=PARCHMENT)
        btn_row.pack(fill="x", pady=12)
        make_button(btn_row, "Inscribe Changes", apply_changes, width=18).pack(side="left", padx=(0, 8))
        make_button(btn_row, "Cancel", show_main_menu, width=18, primary=False).pack(side="left")

    def do_find():
        for w in result_area.winfo_children():
            w.destroy()
        query = query_var.get().strip()
        if not query:
            show_notice("Please enter a name or student code.", error=True)
            academy_error("Revise Record", "Please enter a student name or student code.")
            return
        matches = find_students_by_query(query)
        if not matches:
            show_notice("No matching apprentice record found.", error=True)
            academy_error("Record Not Found", "No matching student record was found.")
            return
        if len(matches) == 1:
            open_edit_form(matches[0])
            return

        # Multiple matches - let user choose.
        panel_body = parchment_panel(result_area, "Multiple Matches — Select Apprentice")
        table_frame = tk.Frame(panel_body, bg=PARCHMENT)
        table_frame.pack(fill="both", expand=True)
        columns = ("code", "name", "cw1", "cw2", "cw3", "exam", "total")
        local_table = ttk.Treeview(table_frame, columns=columns, show="headings", style="Ledger.Treeview", height=min(8, len(matches) + 1))
        headings = {"code": "Student Code", "name": "Student Name", "cw1": "CW1", "cw2": "CW2", "cw3": "CW3", "exam": "Exam", "total": "Total"}
        widths = {"code": 100, "name": 220, "cw1": 70, "cw2": 70, "cw3": 70, "exam": 80, "total": 80}
        for col in columns:
            local_table.heading(col, text=headings[col])
            local_table.column(col, width=widths[col], anchor="w" if col == "name" else "center")
        local_table.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=local_table.yview, style="Gold.Vertical.TScrollbar")
        local_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        iid_to_code = {}
        for i, s in enumerate(matches):
            iid = local_table.insert("", "end", values=format_student_row(s), tags=("even" if i % 2 == 0 else "odd",))
            iid_to_code[iid] = s["code"]
        local_table.tag_configure("even", background=PARCHMENT)
        local_table.tag_configure("odd", background=PARCHMENT_DARK)

        def select_one():
            sel = local_table.selection()
            if not sel:
                academy_error("Selection Needed", "Please select a student record to revise.")
                return
            student = get_student_by_code(iid_to_code.get(sel[0]))
            if student:
                open_edit_form(student)

        action_row = tk.Frame(panel_body, bg=PARCHMENT)
        action_row.pack(fill="x", pady=10)
        make_button(action_row, "Revise Selected", select_one, width=16).pack(side="left", padx=(0, 8))
        make_button(action_row, "Cancel", show_main_menu, width=12, primary=False).pack(side="left")

    btn_row = tk.Frame(body, bg=PARCHMENT)
    btn_row.pack(fill="x", pady=4)
    make_button(btn_row, "Find Apprentice", do_find, width=16).pack(side="left", padx=(0, 8))
    make_button(btn_row, "Return to Ledger", show_main_menu, width=16, primary=False).pack(side="left")
    entry.bind("<Return>", lambda _e: do_find())


# =========================================================
# EXIT / APP BUILD
# =========================================================
def exit_app():
    """Close the Academy Ledger with confirmation."""
    if academy_confirm("Close the Academy Ledger", "Are you sure you want to close the Academy Ledger?"):
        show_notice("The Academy Ledger has been closed. Farewell, Archivist.", error=False)
        stop_music()
        root.destroy()
    else:
        show_notice("The archive remains open.", error=False)


def handle_keypress(event):
    """Keyboard shortcuts for main menu."""
    if current_view != "menu":
        return
    mapping = {
        "1": display_all_records,
        "2": search_student,
        "3": show_highest_total,
        "4": show_lowest_total,
        "5": sort_student_records,
        "6": add_student_record,
        "7": delete_student_record,
        "8": update_student_record,
    }
    action = mapping.get(event.char)
    if action:
        action()


def build_app():
    """Build and initialize the Tkinter application."""
    global root, content_frame, status_var, notice_var, bg_canvas

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("1180x780")
    root.minsize(1020, 700)
    root.configure(bg=MIDNIGHT)

    configure_styles()

    status_var = tk.StringVar(value="Apprentice Records: 0  |  Archive: resources/studentMarks.txt")
    notice_var = tk.StringVar(value="✦ Welcome to the Academy Ledger.")

    # Outer border frame
    outer = tk.Frame(root, bg=GOLD, padx=2, pady=2)
    outer.pack(fill="both", expand=True, padx=10, pady=10)
    shell = tk.Frame(outer, bg=MIDNIGHT)
    shell.pack(fill="both", expand=True)

    # Signature visual element: gold ledger spine with archival index marks.
    spine = tk.Canvas(shell, width=34, bg=MIDNIGHT, highlightthickness=0)
    spine.pack(side="left", fill="y")
    spine.create_line(20, 0, 20, 2000, fill=GOLD, width=2)
    for y in range(30, 2000, 46):
        spine.create_line(12, y, 28, y, fill=GOLD_LIGHT, width=1)
        spine.create_text(16, y - 10, text="§", fill=SAGE, font=("Georgia", 9, "bold"), anchor="w")

    main = tk.Frame(shell, bg=MIDNIGHT)
    main.pack(side="left", fill="both", expand=True)

    build_header(main)

    # Content area with section background image.
    content_container = tk.Frame(main, bg=MIDNIGHT)
    content_container.pack(fill="both", expand=True)
    bg_canvas = tk.Canvas(content_container, bg=MIDNIGHT, highlightthickness=0)
    bg_canvas.pack(fill="both", expand=True)

    # Embed content frame inside canvas so background shows around margins.
    content_frame = tk.Frame(bg_canvas, bg=MIDNIGHT)
    content_window = bg_canvas.create_window((0, 0), window=content_frame, anchor="nw")

    def _resize_content(event=None):
        w = bg_canvas.winfo_width()
        h = bg_canvas.winfo_height()
        if w > 1 and h > 1:
            pad = 28
            bg_canvas.coords(content_window, pad, pad)
            bg_canvas.itemconfigure(content_window, width=max(100, w - pad * 2), height=max(100, h - pad * 2))
            set_section_background(current_view)
            bg_canvas.delete("frame")
            bg_canvas.create_rectangle(pad-2, pad-2, w-pad+2, h-pad+2, outline=GOLD, width=2, tags="frame")
            bg_canvas.tag_raise("frame")

    bg_canvas.bind("<Configure>", _resize_content)

    build_status_bar(main)

    # Load records and show menu
    load_students()
    show_main_menu()
    if students:
        show_notice("The Academy Ledger is open. The records of every apprentice are in your hands.", error=False)

    # Start optional fantasy background music.
    if init_music():
        play_music()
        update_music_button()
    else:
        global music_enabled
        music_enabled = False
        update_music_button()
        show_notice("Fantasy music file not found. Add assets/audio/fantasy_theme.wav to enable music.", error=False)

    root.bind("<Key>", handle_keypress)
    root.protocol("WM_DELETE_WINDOW", exit_app)
    return root


def main():
    """Application entry point."""
    app = build_app()
    app.mainloop()


if __name__ == "__main__":
    main()

