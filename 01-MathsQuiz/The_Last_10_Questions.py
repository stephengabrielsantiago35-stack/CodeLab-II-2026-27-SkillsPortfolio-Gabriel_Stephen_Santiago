#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================
 THE LAST 10 QUESTIONS
 A horror-themed interactive maths quiz  (Python + Tkinter)
----------------------------------------------------------------
 Wake up trapped in an abandoned school. The lights flicker.
 A voice hisses from the speaker:

     "You want to leave? Then answer my questions."

 Solve 10 addition / subtraction questions, earn points and
 escape ... if the entity lets you.

 Run:   python The_Last_10_Questions.py
 Needs: Python 3.8+ (tkinter ships with Python)
        Optional: pygame  -> best quality audio
        (falls back to the Windows sound system, then silence)
================================================================
"""

import os
import random
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

# ------------------------------------------------------------------
#  Paths
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
UI_DIR = os.path.join(ASSETS_DIR, "ui")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")


def load_bundled_fonts():
    """Register bundled TTFs with GDI so Tk can use them (Windows).

    Uses AddFontResourceEx with FR_PRIVATE: the font is visible to
    this process only and vanishes when the game exits - nothing is
    installed on the user's system.  On other platforms the font
    must already be installed, or pick_font() falls back gracefully.
    """
    if os.name != "nt" or not os.path.isdir(FONTS_DIR):
        return
    try:
        import ctypes
        gdi32 = ctypes.windll.gdi32
        FR_PRIVATE = 0x10
        for name in sorted(os.listdir(FONTS_DIR)):
            if name.lower().endswith((".ttf", ".otf")):
                gdi32.AddFontResourceExW(
                    os.path.join(FONTS_DIR, name), FR_PRIVATE, 0)
    except Exception:
        pass


load_bundled_fonts()

# ------------------------------------------------------------------
#  Horror colour palette (from the design document)
# ------------------------------------------------------------------
COLOURS = {
    "bg":       "#08080a",   # background      - almost black
    "panel":    "#17171b",   # panels          - dark charcoal
    "panel_hi": "#1f1f25",   # lighter panel
    "text":     "#e9e4da",   # main text       - off-white
    "muted":    "#8d887e",   # secondary text
    "red":      "#8f1414",   # buttons         - blood red
    "red_hi":   "#b81c1c",   # hovered red
    "red_glow": "#ff3b30",   # glowing red
    "green":    "#3ecf6e",   # correct answers
    "wrong":    "#ff3838",   # warnings / wrong
    "gold":     "#c9a44c",   # rank / score highlights (dull gold)
    "gold_dim": "#8a7233",
    "line":     "#2a2a30",
}


# ==================================================================
#  Small helpers
# ==================================================================
def randomInt(minimum, maximum):
    """Required function: random integer inside the given range."""
    return random.randint(minimum, maximum)


def decideOperation():
    """Required function: randomly returns '+' or '-'."""
    return random.choice(["+", "-"])


def pick_font(candidates, fallback):
    """Return the first available font family from candidates."""
    try:
        families = set(tkfont.families())
    except Exception:
        families = set()
    for name in candidates:
        if name in families:
            return name
    return fallback


def round_rect(canvas, x1, y1, x2, y2, radius=14, **kwargs):
    """Draw a rounded rectangle on a canvas (smooth polygon)."""
    points = (
        x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius, x2, y1 + radius, x2, y2 - radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
        x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
        x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
    )
    return canvas.create_polygon(points, smooth=True, **kwargs)


def load_ui_image(path, size=None, threshold=None):
    """Load a Horror UI pack PNG, cropped to its visible artwork.

    The pack ships every asset on a fixed 1280x714 transparent canvas,
    so we crop to the alpha bounding box first.  ``threshold`` drops
    faint spatter/glow before cropping (useful for icons).
    Returns a PIL image, or None when Pillow / the file is missing.
    """
    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        if threshold:
            mask = img.split()[3].point(
                lambda a: 255 if a >= threshold else 0)
            bbox = mask.getbbox()
        else:
            bbox = img.split()[3].getbbox()
        if bbox:
            img = img.crop(bbox)
        if size:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            img = img.resize(size, resample)
        return img
    except Exception:
        return None


# ==================================================================
#  Audio engine  (pygame -> winsound/MCI -> silence)
# ==================================================================
class AudioEngine:
    """Plays ambient music and sound effects.

    Best quality comes from pygame.mixer.  On Windows without
    pygame the built-in winsound / MCI API is used so the game
    still has atmosphere.  If neither works the game stays
    completely silent but keeps running.
    """

    SFX_FILES = {
        "correct":   "correct.wav",
        "wrong":     "wrong.wav",
        "whisper":   "whisper.wav",
        "door":      "door_creak.wav",
        "unlock":    "unlock.wav",
        "sting":     "sting.wav",
        "heartbeat": "heartbeat.wav",
    }

    def __init__(self):
        self.backend = "none"
        self.music_enabled = True
        self._music_playing = False
        self._mci_opened = False
        self._sounds = {}
        self._pygame = None

        # prefer the generated .wav, accept an .mp3 too
        self.music_path = None
        for candidate in ("haunted_music.wav", "haunted_music.mp3"):
            path = os.path.join(MUSIC_DIR, candidate)
            if os.path.exists(path):
                self.music_path = path
                break

        # --- try pygame first -----------------------------------
        try:
            import pygame  # pyright: ignore[reportMissingImports]
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self._pygame = pygame
            self.backend = "pygame"
        except Exception:
            self._pygame = None

        # --- fall back to the Windows sound system ---------------
        if self.backend == "none":
            try:
                import winsound  # noqa: F401
                self.backend = "winsound"
            except Exception:
                self.backend = "none"

    # ---------------- sound effects -----------------------------
    def play_sfx(self, name):
        filename = self.SFX_FILES.get(name)
        if not filename:
            return
        path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(path):
            return
        try:
            if self.backend == "pygame":
                sound = self._sounds.get(name)
                if sound is None:
                    sound = self._pygame.mixer.Sound(path)
                    self._sounds[name] = sound
                sound.play()
            elif self.backend == "winsound":
                import winsound
                winsound.PlaySound(
                    path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

    # ---------------- background music --------------------------
    def _mci(self, cmd):
        import ctypes
        return ctypes.windll.winmm.mciSendStringW(cmd, None, 0, None)

    def start_music(self):
        if self.backend == "none" or not self.music_path:
            return
        if self._music_playing:
            return
        try:
            if self.backend == "pygame":
                self._pygame.mixer.music.load(self.music_path)
                self._pygame.mixer.music.set_volume(0.70)
                self._pygame.mixer.music.play(-1)
                self._music_playing = self._pygame.mixer.music.get_busy()
            else:
                err = self._mci('open "%s" alias tlq_bgm' % self.music_path)
                if err != 0:
                    err = self._mci(
                        'open "%s" type mpegvideo alias tlq_bgm'
                        % self.music_path)
                if err == 0:
                    self._mci("setaudio tlq_bgm volume to 700")
                    play_err = self._mci("play tlq_bgm repeat")
                    self._mci_opened = play_err == 0
                    self._music_playing = play_err == 0
        except Exception:
            self._music_playing = False

    def stop_music(self):
        if self.backend == "pygame" and self._pygame is not None:
            try:
                self._pygame.mixer.music.stop()
            except Exception:
                pass
        elif self.backend == "winsound" and self._mci_opened:
            try:
                self._mci("stop tlq_bgm")
                self._mci("close tlq_bgm")
            except Exception:
                pass
            self._mci_opened = False
        self._music_playing = False

    def toggle_music(self):
        """Flip the music state; returns True when music is ON."""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            self.start_music()
        else:
            self.stop_music()
        return self.music_enabled


# ==================================================================
#  Glowing horror button (canvas based, with pulse + hover)
# ==================================================================
class GlowButton:
    """A rounded, glowing button drawn on a small canvas."""

    def __init__(self, parent, text, command, *, width, height, font,
                 primary=True, pulse=False, bg=None, image_path=None):
        self.text = text
        self.font = font
        self.width = width
        self.height = height
        self.command = command
        self.primary = primary
        self.pulse = pulse
        self.enabled = True
        self.hovered = False
        self._pulse_on = False
        self._images = {}
        self._image_refs = []
        self._img_offset = (0, 0)

        self.cv = tk.Canvas(
            parent, width=width, height=height,
            bg=bg or COLOURS["panel"], highlightthickness=0,
            cursor="hand2")

        if image_path:
            self._prepare_images(image_path)
        self._draw()

        self.cv.bind("<Enter>", self._on_enter)
        self.cv.bind("<Leave>", self._on_leave)
        self.cv.bind("<Button-1>", self._on_click)

        if pulse:
            self._pulse_loop()

    # ---------- pack artwork ----------------------------------
    def _prepare_images(self, path):
        """Crop / fit a Horror UI pack button into normal/hover/off."""
        try:
            from PIL import Image, ImageEnhance, ImageTk
            base = load_ui_image(path)
            if base is None:
                return
            scale = min(self.width / float(base.width),
                        self.height / float(base.height))
            w = max(1, int(base.width * scale))
            h = max(1, int(base.height * scale))
            resample = getattr(Image, "Resampling", Image).LANCZOS
            fitted = base.resize((w, h), resample)
            self._img_offset = ((self.width - w) // 2,
                                (self.height - h) // 2)

            def photo(image):
                ref = ImageTk.PhotoImage(image)
                self._image_refs.append(ref)
                return ref

            self._images["normal"] = photo(fitted)
            self._images["hover"] = photo(
                ImageEnhance.Brightness(fitted).enhance(1.4))
            self._images["disabled"] = photo(
                ImageEnhance.Brightness(fitted).enhance(0.35))
        except Exception:
            self._images = {}

    # ---------- drawing ----------------------------------------
    def _draw(self):
        cv = self.cv
        cv.delete("all")
        w, h, r = self.width, self.height, 14

        # pack artwork buttons
        if self._images:
            if not self.enabled:
                key = "disabled"
            elif self.hovered or self._pulse_on:
                key = "hover"
            else:
                key = "normal"
            image = self._images.get(key) or self._images.get("normal")
            if image is not None:
                cv.create_image(self._img_offset[0], self._img_offset[1],
                                image=image, anchor="nw")
                return

        if not self.enabled:
            base, edge, text_fill = "#141418", "#24242a", "#55555d"
            shadow = "#000000"
        elif self.primary:
            if self._pulse_on or self.hovered:
                base = COLOURS["red_hi"]
                edge = COLOURS["red_glow"]
            else:
                base = COLOURS["red"]
                edge = "#c62222"
            text_fill = "#fdecec"
            shadow = "#4a0a0a"
        else:
            if self.hovered:
                base, edge = "#2a2a32", COLOURS["red"]
            else:
                base, edge = COLOURS["panel_hi"], "#3a3a42"
            text_fill = COLOURS["text"]
            shadow = "#000000"

        round_rect(cv, 1, 1, w - 1, h - 1, r,
                   fill=base, outline=edge, width=2)
        cx, cy = w / 2.0, h / 2.0
        cv.create_text(cx + 1, cy + 1, text=self.text,
                       font=self.font, fill=shadow)
        cv.create_text(cx, cy, text=self.text,
                       font=self.font, fill=text_fill)

    # ---------- interaction ------------------------------------
    def _on_enter(self, _event):
        self.hovered = True
        self._draw()

    def _on_leave(self, _event):
        self.hovered = False
        self._draw()

    def _on_click(self, _event):
        if self.enabled and self.command is not None:
            self.command()

    def set_enabled(self, flag):
        self.enabled = bool(flag)
        self._draw()

    # ---------- glow pulse -------------------------------------
    def _pulse_loop(self):
        try:
            if self.enabled and self.pulse and self.cv.winfo_ismapped():
                self._pulse_on = not self._pulse_on
                self._draw()
            self.cv.after(520, self._pulse_loop)
        except Exception:
            pass


# ==================================================================
#  The game
# ==================================================================
class Last10Questions:
    """Main game window: menu -> difficulty -> quiz -> results."""

    W = 980
    H = 660
    TOTAL_QUESTIONS = 10

    DIFFICULTIES = {
        "EASY":     (1, 9),        # single digit
        "MODERATE": (10, 99),      # double digit
        "ADVANCED": (1000, 9999),  # four digit
    }

    # minimum score -> (rank, ending message)
    RANKINGS = [
        (90, "A+", "You escaped the nightmare."),
        (80, "A",  "You escaped, but something followed you."),
        (70, "B",  "The entity reluctantly lets you go."),
        (50, "C",  "You remain trapped in the school."),
        (0,  "F",  "The entity caught you."),
    ]

    STORY = ("11:47 PM. Everyone else has gone home. You stayed behind "
             "to finish your work... Then you heard it - a knock from the "
             "empty classroom across the hall. When you stepped inside, "
             "the door slammed shut behind you. The lights began to "
             "flicker. A voice hissed from the speaker: \"You want to "
             "leave? Then answer my questions.\"")

    QUOTE = '"You want to leave? Then answer my questions."'

    def __init__(self, root):
        self.root = root
        root.title("The Last 10 Questions")
        root.geometry("%dx%d" % (self.W, self.H))
        root.resizable(False, False)
        root.configure(bg=COLOURS["bg"])
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ---------- fonts --------------------------------------
        # Creepster (bundled, spooky) for everything except the
        # maths itself - equations and typed answers stay mono.
        self.font_title = pick_font(
            ["Creepster", "Impact", "Segoe UI Black", "Arial Black"],
            "Helvetica")
        self.font_body = pick_font(
            ["Creepster", "Segoe UI", "Verdana"], "Helvetica")
        self.font_mono = pick_font(
            ["Consolas", "Courier New"], "Courier")

        # ---------- audio --------------------------------------
        self.audio = AudioEngine()

        # ---------- game state ---------------------------------
        self.level = None
        self.question_number = 1
        self.questions_done = 0
        self.score = 0
        self.attempt = 1
        self.num1 = 0
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0
        self.busy = False            # a question transition is running

        # ---------- bookkeeping --------------------------------
        self._afters = {}            # named after() handles
        self._img_refs = []          # keep PhotoImages alive
        self._dust_items = []

        self._build_ui()
        self.displayMenu()

    # ----------------------------------------------------------
    #  Scheduling helpers (named so we can cancel cleanly)
    # ----------------------------------------------------------
    def _sched(self, key, delay, func):
        self._cancel(key)
        self._afters[key] = self.root.after(delay, func)

    def _cancel(self, key):
        handle = self._afters.pop(key, None)
        if handle is not None:
            try:
                self.root.after_cancel(handle)
            except Exception:
                pass

    def _cancel_all(self):
        for key in list(self._afters.keys()):
            self._cancel(key)

    # ----------------------------------------------------------
    #  Screen switching
    # ----------------------------------------------------------
    def _show_screen(self, frame):
        for f in (self.menu_frame, self.quiz_frame, self.results_frame):
            f.place_forget()
        if frame is self.menu_frame:
            frame.place(x=140, y=50, width=700, height=560)
        elif frame is self.quiz_frame:
            frame.place(x=100, y=40, width=780, height=580)
        else:
            frame.place(x=140, y=50, width=700, height=560)

    # ----------------------------------------------------------
    #  Build every widget once
    # ----------------------------------------------------------
    def _build_ui(self):
        # background art canvas (full window, behind everything)
        self.bg = tk.Canvas(self.root, width=self.W, height=self.H,
                            highlightthickness=0, bg=COLOURS["bg"])
        self.bg.place(x=0, y=0)

        self.menu_frame = tk.Frame(
            self.root, bg=COLOURS["panel"],
            highlightthickness=1, highlightbackground="#3a1010")
        self.quiz_frame = tk.Frame(
            self.root, bg=COLOURS["panel"],
            highlightthickness=1, highlightbackground="#3a1010")
        self.results_frame = tk.Frame(
            self.root, bg=COLOURS["panel"],
            highlightthickness=1, highlightbackground="#3a1010")

        self._build_menu()
        self._build_quiz()
        self._build_results()

        # Horror UI pack: textured panel behind every screen
        self._apply_panel(self.menu_frame, "panel_menu.png", 700, 560)
        self._apply_panel(self.quiz_frame, "panel_quiz.png", 780, 580)
        self._apply_panel(self.results_frame, "panel_results.png",
                          700, 560)

        # menu + quiz + results text lives directly on the panel artwork
        self._draw_menu_text()
        self._build_quiz_text()
        self._build_results_text()

    # ------------------------- menu ----------------------------
    def _build_menu(self):
        """Buttons for the menu; text items are added after the
        panel artwork exists (see _draw_menu_text)."""
        f = self.menu_frame

        # ----- title stage: PLAY ------------------------------
        self.play_btn = GlowButton(
            f, "P L A Y", self._on_play,
            width=300, height=105,
            font=(self.font_title, 24), primary=True, pulse=True,
            bg=COLOURS["panel"],
            image_path=os.path.join(UI_DIR, "button_play.png"))

        # ----- difficulty stage -------------------------------
        labels = [
            ("EASY", "1 - 9", 60),
            ("MODERATE", "10 - 99", 255),
            ("ADVANCED", "1000 - 9999", 450),
        ]
        self._difficulty_controls = []
        for name, span, x in labels:
            btn = GlowButton(
                f, "%s\n%s" % (name, span),
                lambda lvl=name: self.startGame(lvl),
                width=190, height=76,
                font=(self.font_body, 14, "bold"),
                primary=True, bg=COLOURS["panel"])
            self._difficulty_controls.append((btn.cv, x, 280))

        self.back_btn = GlowButton(
            f, "<  BACK", self._on_back,
            width=150, height=42,
            font=(self.font_body, 12, "bold"),
            primary=False, bg=COLOURS["panel"])
        self._difficulty_controls.append((self.back_btn.cv, 275, 390))

        # ----- bottom controls --------------------------------
        self.menu_music_btn = GlowButton(
            f, "MUSIC: ON", self.toggle_music,
            width=160, height=38,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"])
        self.menu_music_btn.cv.place(x=30, y=506)

        self.menu_exit_btn = GlowButton(
            f, "EXIT", self._on_close,
            width=110, height=49,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"],
            image_path=os.path.join(UI_DIR, "button_exit.png"))
        self.menu_exit_btn.cv.place(x=560, y=504)

    def _menu_scrim(self):
        """Translucent dark scrim behind the story / quote text so it
        stays readable over the busy blood-spattered panel art."""
        cv = self.menu_panel
        cv.delete("scrim")
        try:
            from PIL import Image, ImageDraw, ImageTk
            w, h = 620, 200
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle(
                [0, 0, w - 1, h - 1], radius=16,
                fill=(8, 8, 10, 195))
            photo = ImageTk.PhotoImage(img)
            self._img_refs.append(photo)
            cv.create_image(40, 138, image=photo, anchor="nw",
                            tags="scrim")
        except Exception:
            cv.create_rectangle(
                40, 138, 660, 338, fill="#0a0a0c", outline="",
                tags="scrim")

    def _draw_menu_text(self):
        """Glowing title + story/quote text drawn straight onto the
        panel artwork (so no flat label rectangles cover the art)."""
        cv = self.menu_panel
        self._menu_scrim()
        self._draw_title()

        self.story_id = cv.create_text(
            50, 150, text="", anchor="nw", justify="left", width=600,
            font=(self.font_body, 13), fill=COLOURS["text"],
            state="hidden")
        self.hint_id = cv.create_text(
            350, 480,
            text="10 questions  -  2 attempts each  -  1 way out",
            font=(self.font_body, 12, "italic"), fill=COLOURS["muted"],
            state="hidden")
        self.quote_id = cv.create_text(
            350, 176, text=self.QUOTE, width=600, justify="center",
            font=(self.font_body, 15, "italic"), fill=COLOURS["gold"],
            state="hidden")
        self.diff_hint_id = cv.create_text(
            350, 462,
            text="The entity is patient. It is not kind.",
            font=(self.font_body, 12, "italic"), fill=COLOURS["muted"],
            state="hidden")

        self._show_stage("title")

    def _show_stage(self, stage):
        """Swap between the title stage and the difficulty stage."""
        cv = self.menu_panel
        if stage == "title":
            for widget, x, y in self._difficulty_controls:
                widget.place_forget()
            cv.itemconfigure(self.quote_id, state="hidden")
            cv.itemconfigure(self.diff_hint_id, state="hidden")
            cv.itemconfigure(self.story_id, state="normal")
            cv.itemconfigure(self.hint_id, state="normal")
            self.play_btn.cv.place(x=200, y=356)
        else:
            self.play_btn.cv.place_forget()
            cv.itemconfigure(self.story_id, state="hidden")
            cv.itemconfigure(self.hint_id, state="hidden")
            cv.itemconfigure(self.quote_id, state="normal")
            cv.itemconfigure(self.diff_hint_id, state="normal")
            for widget, x, y in self._difficulty_controls:
                widget.place(x=x, y=y)

    def _draw_title(self):
        cv = self.menu_panel
        cv.delete("title")

        # skull icon from the Horror UI pack (drawn fallback)
        skull = load_ui_image(os.path.join(UI_DIR, "icon_skull.png"),
                              threshold=60)
        if skull is not None:
            scale = min(84.0 / skull.width, 84.0 / skull.height)
            size = (max(1, int(skull.width * scale)),
                    max(1, int(skull.height * scale)))
            skull = load_ui_image(os.path.join(UI_DIR, "icon_skull.png"),
                                  size=size, threshold=60)
            photo = self._pil_photo(skull)
            if photo is not None:
                cv.create_image(34 + (84 - size[0]) // 2,
                                44 + (84 - size[1]) // 2,
                                image=photo, anchor="nw", tags="title")
        else:
            cv.create_oval(48, 52, 108, 106, fill="#d8d2c4",
                           outline="", tags="title")
            cv.create_rectangle(62, 96, 94, 114, fill="#d8d2c4",
                                outline="", tags="title")
            cv.create_oval(61, 66, 79, 84, fill="#08080a", outline="",
                           tags="title")
            cv.create_oval(81, 66, 99, 84, fill="#08080a", outline="",
                           tags="title")

        # glowing title text (red shadow layers)
        text = "THE LAST 10 QUESTIONS"
        font = (self.font_title, 44)
        cv.create_text(402, 78, text=text, font=font, fill="#4a0a0a",
                       tags="title")
        cv.create_text(401, 77, text=text, font=font, fill="#a01818",
                       tags="title")
        cv.create_text(400, 76, text=text, font=font,
                       fill=COLOURS["red_glow"], tags="title")
        cv.create_text(400, 76, text=text, font=font, fill="#f5e9e9",
                       tags="title")
        cv.create_text(400, 126,
                       text="S U R V I V E   T H E   N I G H T",
                       font=(self.font_body, 12, "bold"),
                       fill=COLOURS["gold_dim"], tags="title")

    # ------------------------- quiz ----------------------------
    def _build_quiz(self):
        f = self.quiz_frame

        # dynamic text (rendered as canvas items on the panel artwork,
        # see _build_quiz_text - keeps the StringVars requirement)
        self.var_counter = tk.StringVar(value="QUESTION 1 / 10")
        self.var_score = tk.StringVar(value="SCORE: 0 / 100")
        self.var_question = tk.StringVar(value="")
        self.var_attempt = tk.StringVar(value="ATTEMPT 1 OF 2")
        self.var_feedback = tk.StringVar(value="")

        self.answer_entry = tk.Entry(
            f, font=(self.font_mono, 30, "bold"), width=8,
            justify="center", bg="#0d0d10", fg=COLOURS["gold"],
            insertbackground=COLOURS["gold"], relief="flat",
            readonlybackground="#0d0d10", disabledbackground="#0d0d10",
            disabledforeground=COLOURS["gold"], highlightthickness=1,
            highlightbackground="#3a3a42")
        self.answer_entry.place(x=286, y=252, anchor="center",
                                width=230, height=58)
        self.answer_entry.bind("<Return>", lambda _e: self.submitAnswer())

        self.submit_btn = GlowButton(
            f, "SUBMIT", self.submitAnswer,
            width=220, height=54,
            font=(self.font_body, 17, "bold"),
            primary=True, pulse=True, bg=COLOURS["panel"])
        self.submit_btn.cv.place(x=176, y=330)

        # progress door + watching entity
        self.door_canvas = tk.Canvas(
            f, width=188, height=478, bg="#07070a",
            highlightthickness=1, highlightbackground="#2a2a30")
        self.door_canvas.place(x=566, y=16)

        self.quiz_music_btn = GlowButton(
            f, "MUSIC: ON", self.toggle_music,
            width=160, height=36,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"])
        self.quiz_music_btn.cv.place(x=80, y=520)

        self.quiz_exit_btn = GlowButton(
            f, "EXIT", self._on_close,
            width=110, height=49,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"],
            image_path=os.path.join(UI_DIR, "button_exit.png"))
        self.quiz_exit_btn.cv.place(x=366, y=515)

    def _build_quiz_text(self):
        """Quiz labels drawn straight onto the panel artwork.

        The StringVars still drive everything - each variable has a
        trace that pushes its value into the matching canvas item.
        """
        cv = self.quiz_panel

        self.counter_id = cv.create_text(
            26, 26, anchor="w", text=self.var_counter.get(),
            font=(self.font_body, 16, "bold"), fill=COLOURS["gold"])
        self.score_id = cv.create_text(
            546, 26, anchor="e", text=self.var_score.get(),
            font=(self.font_body, 16, "bold"), fill=COLOURS["gold"])
        cv.create_text(
            26, 50, anchor="w", text="ABANDONED CLASSROOM  -  11:47 PM",
            font=(self.font_body, 10), fill=COLOURS["muted"])
        cv.create_line(26, 68, 546, 68, fill=COLOURS["line"])
        self.question_id = cv.create_text(
            286, 140, text="",
            font=(self.font_mono, 40, "bold"), fill=COLOURS["text"])
        self.attempt_id = cv.create_text(
            286, 200, text=self.var_attempt.get(),
            font=(self.font_body, 11), fill=COLOURS["muted"])
        self.feedback_id = cv.create_text(
            286, 445, width=480, justify="center", text="",
            font=(self.font_body, 14), fill=COLOURS["muted"])

        # keep the canvas items in sync with the StringVars
        self.var_counter.trace_add(
            "write",
            lambda *_: cv.itemconfigure(self.counter_id,
                                        text=self.var_counter.get()))
        self.var_score.trace_add(
            "write",
            lambda *_: cv.itemconfigure(self.score_id,
                                        text=self.var_score.get()))
        self.var_question.trace_add(
            "write",
            lambda *_: cv.itemconfigure(self.question_id,
                                        text=self.var_question.get()))
        self.var_attempt.trace_add(
            "write",
            lambda *_: cv.itemconfigure(self.attempt_id,
                                        text=self.var_attempt.get()))
        self.var_feedback.trace_add(
            "write",
            lambda *_: cv.itemconfigure(self.feedback_id,
                                        text=self.var_feedback.get()))

    # ----------------------- results ---------------------------
    def _build_results(self):
        f = self.results_frame

        self.var_rank = tk.StringVar(value="")
        self.var_final_score = tk.StringVar(value="SCORE: 0 / 100")
        self.var_ending = tk.StringVar(value="")

        # rank / score / ending are canvas items on the panel artwork
        # (see _build_results_text) - the StringVars still drive them

        self.again_btn = GlowButton(
            f, "PLAY AGAIN", self._on_play_again,
            width=220, height=96,
            font=(self.font_body, 16, "bold"),
            primary=True, bg=COLOURS["panel"],
            image_path=os.path.join(UI_DIR, "button_newgame.png"))
        self.again_btn.cv.place(x=56, y=404)

        self.menu_btn = GlowButton(
            f, "MAIN MENU", self.displayMenu,
            width=240, height=54,
            font=(self.font_body, 16, "bold"),
            primary=False, bg=COLOURS["panel"])
        self.menu_btn.cv.place(x=350, y=425)

        self.results_music_btn = GlowButton(
            f, "MUSIC: ON", self.toggle_music,
            width=160, height=36,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"])
        self.results_music_btn.cv.place(x=40, y=506)

        self.results_exit_btn = GlowButton(
            f, "EXIT", self._on_close,
            width=110, height=49,
            font=(self.font_body, 11, "bold"),
            primary=False, bg=COLOURS["panel"],
            image_path=os.path.join(UI_DIR, "button_exit.png"))
        self.results_exit_btn.cv.place(x=548, y=502)


# ==================================================================
#  Horror UI pack: panels, icons  (appended to Last10Questions)
# ==================================================================
def _pil_photo(self, pil_image):
    """PIL image -> Tk PhotoImage (kept alive in _img_refs)."""
    if pil_image is None:
        return None
    try:
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(pil_image)
        self._img_refs.append(photo)
        return photo
    except Exception:
        return None


def _apply_panel(self, frame, filename, width, height):
    """Stretch a Horror UI pack panel behind a screen's widgets.

    The panel art is composited over the charcoal panel colour so it
    is fully opaque, then every flat widget background inside the
    frame is re-tinted to the panel's interior colour so labels
    blend into the artwork instead of showing as pale rectangles.
    """
    canvas = tk.Canvas(frame, width=width, height=height,
                       bg=COLOURS["panel"], highlightthickness=0)
    canvas.place(x=0, y=0, width=width, height=height)
    canvas.tk.call("lower", canvas._w)

    if frame is self.menu_frame:
        self.menu_panel = canvas
    elif frame is self.quiz_frame:
        self.quiz_panel = canvas
    else:
        self.results_panel = canvas

    pil = load_ui_image(os.path.join(UI_DIR, filename))
    if pil is None:
        return
    try:
        from PIL import Image
        base = Image.new("RGBA", pil.size, (23, 23, 27, 255))
        pil = Image.alpha_composite(base, pil)
        resample = getattr(Image, "Resampling", Image).LANCZOS
        pil = pil.resize((width, height), resample)
    except Exception:
        return

    photo = self._pil_photo(pil)
    if photo is None:
        return

    canvas.create_image(0, 0, image=photo, anchor="nw")

    # sample the interior colour (median of a central point grid)
    rgb = pil.convert("RGB")
    points = [(0.30, 0.35), (0.70, 0.35), (0.30, 0.70),
              (0.70, 0.70), (0.50, 0.50), (0.50, 0.30)]
    samples = [rgb.getpixel((int(width * fx), int(height * fy)))
               for fx, fy in points]
    interior = tuple(
        sorted(sample[i] for sample in samples)[len(samples) // 2]
        for i in range(3))
    self._tint(frame, "#%02x%02x%02x" % interior)


def _tint(self, widget, colour):
    """Re-colour every flat charcoal widget background in a frame."""
    for child in widget.winfo_children():
        try:
            if str(child.cget("bg")) == COLOURS["panel"]:
                child.configure(bg=colour)
        except Exception:
            pass
        self._tint(child, colour)


# ==================================================================
#  Background art + atmosphere  (appended to Last10Questions)
# ==================================================================
def _paint_background(self, scene):
    """Draw the full-window artwork for a scene (or use a PNG)."""
    self._cancel("flicker")
    self._cancel("dust")
    self.bg.delete("all")
    self._dust_items = []

    photo = None
    png = os.path.join(BACKGROUNDS_DIR, scene + ".png")
    if os.path.exists(png):
        photo = self._try_photo(png)
    if photo is not None:
        self.bg.create_image(0, 0, image=photo, anchor="nw")
    else:
        if scene == "hallway":
            self._art_hallway()
        elif scene == "classroom":
            self._art_classroom()
        else:
            self._art_corridor(self._results_good)

    self._vignette()
    self._create_dust()
    self.flicker_rect = self.bg.create_rectangle(
        0, 0, self.W, self.H, fill="", outline="")
    self._flicker_loop()


def _try_photo(self, path):
    """Load a PNG/JPG background when Pillow is available."""
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).resize((self.W, self.H))
        photo = ImageTk.PhotoImage(img)
        self._img_refs.append(photo)
        return photo
    except Exception:
        return None


def _vignette(self):
    """Darken the screen edges with dotted border bands."""
    w, h = self.W, self.H
    bands = [("gray75", 26), ("gray50", 20), ("gray25", 16)]
    offset = 0
    for stipple, width in bands:
        self.bg.create_rectangle(
            offset, offset, w - offset, h - offset,
            fill="", outline="#000000", width=width, stipple=stipple)
        offset += width


# ---------------- hallway (menu) --------------------------------
def _art_hallway(self):
    c = self.bg
    w, h = self.W, self.H
    vx, vy = w * 0.5, h * 0.46

    c.create_rectangle(0, 0, w, h, fill="#0a0a0d", outline="")
    # ceiling / floor / walls in perspective
    c.create_polygon(0, 0, w, 0, vx + 95, vy - 62, vx - 95, vy - 62,
                     fill="#0c0c10", outline="")
    c.create_polygon(0, h, w, h, vx + 95, vy + 74, vx - 95, vy + 74,
                     fill="#101014", outline="")
    c.create_polygon(0, 0, vx - 95, vy - 62, vx - 95, vy + 74, 0, h,
                     fill="#08080a", outline="")
    c.create_polygon(w, 0, vx + 95, vy - 62, vx + 95, vy + 74, w, h,
                     fill="#0d0d11", outline="")
    # converging floor / ceiling lines
    for i in range(1, 7):
        x = i * w / 7.0
        c.create_line(x, h, vx, vy + 74, fill="#17171c", width=1)
        c.create_line(x, 0, vx, vy - 62, fill="#141419", width=1)
    # far door at the end of the hall
    c.create_rectangle(vx - 46, vy - 60, vx + 46, vy + 72,
                       fill="#050506", outline="#241414", width=2)
    c.create_oval(vx + 24, vy + 2, vx + 32, vy + 10,
                  fill="#6b1414", outline="")
    # ceiling lights (one dead, one dying)
    for t, lit in ((0.06, True), (0.34, True), (0.62, False)):
        y = 26 + t * (vy - 100)
        half = 36 - t * 22
        if lit:
            c.create_oval(vx - half * 2, y - 16, vx + half * 2, y + 30,
                          fill="#28240f", outline="")
            c.create_rectangle(vx - half, y, vx + half, y + 13,
                               fill="#57501f", outline="#6d6428")
        else:
            c.create_rectangle(vx - half, y, vx + half, y + 13,
                               fill="#101012", outline="#1b1b1e")


# ---------------- classroom (quiz) ------------------------------
def _art_classroom(self):
    c = self.bg
    w, h = self.W, self.H

    c.create_rectangle(0, 0, w, h, fill="#0a0a0c", outline="")
    c.create_rectangle(0, 0, w, int(h * 0.66), fill="#0b0b0e", outline="")
    c.create_rectangle(0, int(h * 0.66), w, h, fill="#0f0f13", outline="")
    for y in range(int(h * 0.70), h, 26):
        c.create_line(0, y, w, y, fill="#131317", width=1)

    # chalkboard peeking in from the left edge
    c.create_rectangle(-10, 60, 130, 330, fill="#0d1712",
                       outline="#26221a", width=4)
    c.create_text(20, 100, text="DETENTION", anchor="nw",
                  font=(self.font_title, 20), fill="#39443c")
    c.create_text(20, 150, text="7 + 3 = ?", anchor="nw",
                  font=(self.font_mono, 16), fill="#313b34")
    c.create_text(20, 190, text="nobody left", anchor="nw",
                  font=(self.font_body, 13, "italic"), fill="#313b34")

    # moonlit window on the right edge
    c.create_rectangle(858, 60, 975, 330, fill="#0a1018",
                       outline="#1c1c22", width=4)
    c.create_oval(880, 90, 950, 160, fill="#1b2430", outline="")
    c.create_line(916, 60, 916, 330, fill="#1c1c22", width=3)
    c.create_line(858, 195, 975, 195, fill="#1c1c22", width=3)

    # dead ceiling light
    c.create_rectangle(430, 6, 550, 34, fill="#101012", outline="#1b1b1e")
    c.create_oval(400, 0, 580, 60, fill="#1a1810", outline="")

    # desk silhouettes along the bottom edge
    for x, y, dw in ((40, 596, 190), (330, 612, 210), (660, 596, 200)):
        c.create_rectangle(x, y, x + dw, y + 34, fill="#07070a",
                           outline="#101014", width=2)
        c.create_line(x + 12, y + 34, x + 12, y + 58, fill="#07070a",
                      width=5)
        c.create_line(x + dw - 12, y + 34, x + dw - 12, y + 58,
                      fill="#07070a", width=5)


# ---------------- corridor (results) ----------------------------
def _art_corridor(self, good):
    c = self.bg
    w, h = self.W, self.H

    c.create_rectangle(0, 0, w, h, fill="#0a0a0c", outline="")
    c.create_rectangle(0, int(h * 0.7), w, h, fill="#0e0e12", outline="")
    for i in range(1, 7):
        c.create_line(i * w / 7.0, h, w * 0.5, h * 0.66,
                      fill="#141418", width=1)

    # exit door in the right margin
    dx1, dy1, dx2, dy2 = 846, 120, 966, 600
    c.create_rectangle(dx1 - 10, dy1 - 12, dx2 + 10, dy2,
                       fill="#1a140d", outline="#2c241a", width=3)
    if good:
        # door standing open, light pouring out
        c.create_rectangle(dx1, dy1, dx2, dy2, fill="#6b5a2a", outline="")
        c.create_rectangle(dx1 + 16, dy1 + 16, dx2 - 16, dy2,
                           fill="#c9a44c", outline="")
        c.create_rectangle(dx1 + 34, dy1 + 34, dx2 - 34, dy2,
                           fill="#f2e2b0", outline="")
        c.create_polygon(dx1, dy2, dx2, dy2, dx2 + 70, h, dx1 - 60, h,
                         fill="#2a2412", outline="")
    else:
        # locked, red keyhole glowing
        c.create_rectangle(dx1, dy1, dx2, dy2, fill="#120e08",
                           outline="#000000", width=2)
        for y in range(dy1 + 40, dy2 - 20, 70):
            c.create_line(dx1 + 10, y, dx2 - 10, y, fill="#191309",
                          width=2)
        c.create_oval(dx2 - 40, 352, dx2 - 24, 376,
                      fill="#6b1414", outline="#a02222")
        c.create_oval(dx2 - 46, 346, dx2 - 18, 382,
                      outline="#4a0f0f", width=4)

    # the entity, watching from the left margin
    ex = 70
    c.create_polygon(ex, 640, ex - 44, 640, ex - 30, 330, ex - 44, 250,
                     ex, 196, ex + 44, 250, ex + 30, 330, ex + 44, 640,
                     fill="#040405", outline="#0d0d10", width=2)
    c.create_oval(ex - 30, 208, ex + 30, 276, fill="#0a0a0c", outline="")
    if good:
        # hollow eyes only, half hidden in shadow
        c.create_oval(ex - 17, 232, ex - 6, 246, fill="#c9c2b2",
                      outline="")
        c.create_oval(ex + 6, 232, ex + 17, 246, fill="#c9c2b2",
                      outline="")
    else:
        c.create_oval(ex - 20, 230, ex - 4, 248, fill="#e6e0d2",
                      outline="")
        c.create_oval(ex + 4, 230, ex + 20, 248, fill="#e6e0d2",
                      outline="")
        c.create_oval(ex - 14, 235, ex - 8, 244, fill="#08080a",
                      outline="")
        c.create_oval(ex + 8, 235, ex + 14, 244, fill="#08080a",
                      outline="")
        c.create_arc(ex - 14, 250, ex + 14, 272, start=200, extent=140,
                     style=tk.ARC, outline="#8f1414", width=3)


# ---------------- flickering lights -----------------------------
def _set_flicker(self, mode):
    if not hasattr(self, "flicker_rect"):
        return
    styles = {
        "none":   {"fill": ""},
        "dim":    {"fill": "#000000", "stipple": "gray25"},
        "hard":   {"fill": "#000000", "stipple": "gray50"},
        "black":  {"fill": "#000000", "stipple": ""},
    }
    self.bg.itemconfigure(self.flicker_rect, **styles[mode])


def _flicker_loop(self):
    self._sched("flicker", random.randint(1600, 4200), self._flicker_tick)


def _flicker_tick(self):
    roll = random.random()
    if roll < 0.55:
        self._set_flicker("dim")
        self._sched("flicker", random.randint(70, 170), self._flicker_clear)
    elif roll < 0.85:
        self._set_flicker("hard")
        self._sched("flicker", random.randint(45, 130), self._flicker_clear)
    else:
        self._set_flicker("black")
        self._sched("flicker", random.randint(140, 340), self._flicker_clear)


def _flicker_clear(self):
    self._set_flicker("none")
    self._flicker_loop()


def brownout(self):
    """A short full blackout - used when the entity stirs."""
    self._set_flicker("black")
    self._sched("flicker", random.randint(180, 320), self._flicker_clear)


# ---------------- floating dust ---------------------------------
def _create_dust(self):
    self._dust_items = []
    for _ in range(24):
        x = random.uniform(0, self.W)
        y = random.uniform(0, self.H)
        r = random.uniform(0.6, 1.8)
        item = self.bg.create_oval(x - r, y - r, x + r, y + r,
                                   fill="#2e2e35", outline="")
        self._dust_items.append(
            [item, random.uniform(-0.12, 0.12), random.uniform(0.03, 0.14)])
    self._dust_loop()


def _dust_loop(self):
    if not self._dust_items:
        return
    for rec in list(self._dust_items):
        item, dx, dy = rec
        coords = self.bg.coords(item)
        if not coords:
            continue
        nx = coords[0] + dx
        ny = coords[1] + dy
        if ny > self.H + 2:
            ny = -2
        if nx < -2:
            nx = self.W + 2
        elif nx > self.W + 2:
            nx = -2
        self.bg.coords(item, nx, ny,
                       nx + (coords[2] - coords[0]),
                       ny + (coords[3] - coords[1]))
    self._sched("dust", 90, self._dust_loop)


# ---------------- progress door (quiz panel) --------------------
def _draw_door(self):
    cv = self.door_canvas
    cv.delete("all")
    w, h = 188, 478

    cv.create_rectangle(0, 0, w, h, fill="#07070a", outline="")

    # the entity's face floating in the dark above the door
    self._face_id = cv.create_oval(56, 18, 132, 84, fill="#0c0c10",
                                   outline="")
    self._eye_ids = (
        cv.create_oval(68, 38, 82, 54, fill="#d8d2c4", outline=""),
        cv.create_oval(106, 38, 120, 54, fill="#d8d2c4", outline=""),
    )

    # door frame + slab
    fx1, fy1, fx2, fy2 = 40, 96, 148, 442
    cv.create_rectangle(fx1 - 8, fy1 - 8, fx2 + 8, fy2 + 8,
                        fill="#1a140d", outline="#2c241a", width=3)
    cv.create_rectangle(fx1, fy1, fx2, fy2, fill="#120e08",
                        outline="#000000", width=2)

    # 10 lock bolts: one disappears for every finished question
    remaining = self.TOTAL_QUESTIONS - self.questions_done
    span = (fy2 - fy1 - 60) / 9.0
    for i in range(self.TOTAL_QUESTIONS):
        y = fy1 + 30 + i * span
        if i < remaining:
            cv.create_rectangle(fx1 + 5, y - 5, fx2 - 5, y + 5,
                                fill="#6b1616", outline="#a02222")
            cv.create_rectangle(fx1 + 5, y - 5, fx1 + 13, y + 5,
                                fill="#4a0f0f", outline="")
            cv.create_rectangle(fx2 - 13, y - 5, fx2 - 5, y + 5,
                                fill="#4a0f0f", outline="")
        else:
            cv.create_rectangle(fx1 + 5, y - 2, fx2 - 5, y + 2,
                                fill="#20301f", outline="")

    # handle
    cv.create_oval(fx2 - 24, 262, fx2 - 10, 276,
                   fill=COLOURS["gold_dim"], outline="#5c4c22")

    cv.create_text(w / 2, 460, text="LOCKS: %d" % remaining,
                   font=(self.font_body, 13, "bold"),
                   fill=COLOURS["muted"])

    if remaining == 0:
        cv.create_text(w / 2, 90, text="OPEN",
                       font=(self.font_title, 16), fill=COLOURS["green"])

    self._blink_loop()


def _blink_loop(self):
    """The eyes above the door blink every few seconds."""
    if not hasattr(self, "_eye_ids") or not self._eye_ids:
        return
    delay = random.randint(2600, 5600)
    self._sched("blink", delay, self._eyes_closed)


def _eyes_closed(self):
    if not hasattr(self, "_eye_ids") or not self._eye_ids:
        return
    try:
        for item in self._eye_ids:
            x1, y1, x2, y2 = self.door_canvas.coords(item)
            self.door_canvas.coords(item, x1, y1 + 6, x2, y2 - 6)
    except Exception:
        return
    self._sched("blink", 150, self._eyes_open)


def _eyes_open(self):
    if hasattr(self, "_eye_ids") and self._eye_ids:
        try:
            for item in self._eye_ids:
                x1, y1, x2, y2 = self.door_canvas.coords(item)
                self.door_canvas.coords(item, x1, y1 - 6, x2, y2 + 6)
        except Exception:
            pass
    self._blink_loop()


def flash_entity(self):
    """The eyes turn red for a moment when the player is wrong."""
    if not hasattr(self, "_eye_ids") or not self._eye_ids:
        return
    try:
        for item in self._eye_ids:
            self.door_canvas.itemconfigure(item, fill=COLOURS["wrong"])
        if hasattr(self, "_face_id"):
            self.door_canvas.itemconfigure(self._face_id, fill="#1c0c0c")
    except Exception:
        return
    # brownout() (called right after in isCorrect) handles the
    # screen effect; keep the eyes red for a full 1.3 s.
    self._sched("entity", 1300, self._entity_calm)



def _entity_calm(self):
    try:
        for item in self._eye_ids:
            self.door_canvas.itemconfigure(item, fill="#d8d2c4")
        self.door_canvas.itemconfigure(self._face_id, fill="#0c0c10")
    except Exception:
        pass


# ==================================================================
#  Gameplay  (bound onto Last10Questions below)
# ==================================================================
def displayMenu(self):
    """Required function: title screen + difficulty menu."""
    self._cancel_all()
    self.busy = False
    self._results_good = True

    self._show_screen(self.menu_frame)
    self._show_stage("title")
    self._paint_background("hallway")
    self._type_text(self.story_id, self.STORY)

    if self.audio.music_enabled:
        self.audio.start_music()


def _on_play(self):
    """Show the difficulty selection stage of the menu."""
    self.audio.play_sfx("whisper")
    self._show_stage("difficulty")


def _on_back(self):
    """Return from difficulty selection to the title stage."""
    self._show_stage("title")
    self._type_text(self.story_id, self.STORY)


def _type_text(self, target, text):
    """Typewriter effect for the opening story.

    ``target`` is a canvas text item id (menu panel) or a Label.
    """
    self._cancel("type")
    is_canvas = isinstance(target, int)

    def set_text(value):
        if is_canvas:
            self.menu_panel.itemconfigure(target, text=value)
        else:
            target.configure(text=value)

    set_text("")
    state = {"i": 0}

    def step():
        state["i"] += 1
        set_text(text[:state["i"]])
        if state["i"] < len(text):
            self._sched("type", 18, step)

    self._sched("type", 200, step)


def startGame(self, level):
    """Required-extra function: reset everything and begin a round."""
    self._cancel_all()
    self.level = level
    self.question_number = 1
    self.questions_done = 0
    self.score = 0
    self.attempt = 1
    self.busy = False

    self._show_screen(self.quiz_frame)
    self._paint_background("classroom")
    self.audio.play_sfx("door")

    self._set_controls(True)
    self.var_feedback.set("")
    self.displayProblem()


def _set_controls(self, enabled):
    state = "normal" if enabled else "disabled"
    self.answer_entry.configure(state=state)
    self.submit_btn.set_enabled(enabled)


def updateStatus(self):
    """Required-extra function: refresh the question + score labels."""
    self.var_counter.set(
        "QUESTION %d / %d" % (self.question_number, self.TOTAL_QUESTIONS))
    self.var_score.set("SCORE: %d / 100" % self.score)


def displayProblem(self):
    """Required function: show the next arithmetic question."""
    self.attempt = 1
    self.busy = False

    minimum, maximum = self.DIFFICULTIES[self.level]
    num1 = randomInt(minimum, maximum)
    num2 = randomInt(minimum, maximum)
    operation = decideOperation()

    # keep subtraction answers in the positive numbers
    if operation == "-" and num2 > num1:
        num1, num2 = num2, num1

    self.num1 = num1
    self.num2 = num2
    self.operation = operation
    self.correct_answer = num1 + num2 if operation == "+" else num1 - num2

    self.var_question.set("%d %s %d = ?" % (num1, operation, num2))
    self.var_attempt.set("ATTEMPT 1 OF 2")
    self.var_feedback.set("")
    self.updateStatus()
    self._draw_door()

    self._set_controls(True)
    self.answer_entry.delete(0, tk.END)
    self.answer_entry.focus_set()

    # heartbeat on the tougher rounds
    if self.level == "ADVANCED":
        self.audio.play_sfx("heartbeat")


def submitAnswer(self):
    """Required-extra function: handle the Submit button / Enter key."""
    if self.busy:
        return

    raw = self.answer_entry.get().strip()
    if raw == "":
        self.showFeedback("Type an answer first.", "muted")
        return
    try:
        int(raw)
    except ValueError:
        self.showFeedback("Whole numbers only. The entity is watching.",
                          "muted")
        return

    self.isCorrect(raw)


def showFeedback(self, message, kind="muted"):
    """Required-extra function: coloured feedback text."""
    colours = {
        "correct": COLOURS["green"],
        "wrong":   COLOURS["wrong"],
        "reveal":  COLOURS["gold"],
        "muted":   COLOURS["muted"],
    }
    self.var_feedback.set(message)
    self.quiz_panel.itemconfigure(
        self.feedback_id, fill=colours.get(kind, COLOURS["muted"]))


def isCorrect(self, user_answer):
    """Required function: check the answer, manage score + retry."""
    try:
        value = int(str(user_answer).strip())
    except ValueError:
        return None

    if value == self.correct_answer:
        gained = 10 if self.attempt == 1 else 5
        self.score += gained
        self.updateStatus()
        self.showFeedback("Correct!  +%d points" % gained, "correct")
        self.audio.play_sfx("correct")
        self.busy = True
        self._set_controls(False)
        self._sched("transition", 1100, self.nextQuestion)
        return True

    # ---- wrong answer ----------------------------------------
    self.audio.play_sfx("wrong" if self.attempt == 1 else "whisper")
    self.flash_entity()
    self.brownout()

    if self.attempt == 1:
        self.attempt = 2
        self.var_attempt.set("ATTEMPT 2 OF 2")
        self.showFeedback("Wrong... one more chance.", "wrong")
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus_set()
        self.audio.play_sfx("heartbeat")
        return False

    # second attempt failed -> reveal the answer and move on
    self.showFeedback("The answer was %d." % self.correct_answer,
                      "reveal")
    self.busy = True
    self._set_controls(False)
    self._sched("transition", 2000, self.nextQuestion)
    return False


def nextQuestion(self):
    """Required-extra function: advance to the next question."""
    self.questions_done = self.question_number
    self._draw_door()

    if self.question_number >= self.TOTAL_QUESTIONS:
        self.displayResults()
        return

    self.question_number += 1
    self.displayProblem()


def displayResults(self):
    """Required function: final score, rank and ending message."""
    self._cancel_all()
    self.busy = True

    # rank lookup
    rank, ending = "F", self.RANKINGS[-1][2]
    for minimum_score, candidate_rank, candidate_text in self.RANKINGS:
        if self.score >= minimum_score:
            rank, ending = candidate_rank, candidate_text
            break

    self._results_good = rank in ("A+", "A", "B")

    self.var_rank.set(rank)
    self.var_final_score.set("SCORE: %d / 100" % self.score)
    self.var_ending.set(ending)
    self.results_panel.itemconfigure(
        self.rank_id,
        fill=COLOURS["gold"] if self._results_good else COLOURS["wrong"])

    self._show_screen(self.results_frame)
    self._paint_background("corridor")
    self._draw_result_icon(rank)

    # door unlocking, or a sting when the entity wins
    self.audio.play_sfx("unlock")
    if rank == "F":
        self._sched("sting", 700, lambda: self.audio.play_sfx("sting"))


def _build_results_text(self):
    """Rank / score / ending drawn straight onto the results panel."""
    cv = self.results_panel

    self.rank_id = cv.create_text(
        350, 214, text="", font=(self.font_title, 84),
        fill=COLOURS["gold"], tags="result")
    self.final_score_id = cv.create_text(
        350, 286, text=self.var_final_score.get(),
        font=(self.font_body, 26, "bold"), fill=COLOURS["gold"],
        tags="result")
    self.ending_id = cv.create_text(
        350, 365, width=560, justify="center", text="",
        font=(self.font_body, 15), fill=COLOURS["text"],
        tags="result")

    self.var_rank.trace_add(
        "write",
        lambda *_: cv.itemconfigure(self.rank_id,
                                    text=self.var_rank.get()))
    self.var_final_score.trace_add(
        "write",
        lambda *_: cv.itemconfigure(self.final_score_id,
                                    text=self.var_final_score.get()))
    self.var_ending.trace_add(
        "write",
        lambda *_: cv.itemconfigure(self.ending_id,
                                    text=self.var_ending.get()))


def _draw_result_icon(self, rank):
    cv = self.results_panel
    cv.delete("resulticon")
    cx, cy = 350, 96
    before = set(cv.find_all())

    # Horror UI pack icons first (drawn fallbacks stay below)
    pack = {
        "B": ("icon_key.png", "RELUCTANTLY FREED", COLOURS["gold_dim"]),
        "C": ("icon_skull.png", "TRAPPED", COLOURS["gold_dim"]),
        "F": ("icon_monster.png", "CAUGHT", COLOURS["wrong"]),
    }
    if rank in pack:
        filename, caption, colour = pack[rank]
        pil = load_ui_image(os.path.join(UI_DIR, filename), threshold=60)
        if pil is not None:
            scale = min(130.0 / pil.width, 112.0 / pil.height)
            size = (max(1, int(pil.width * scale)),
                    max(1, int(pil.height * scale)))
            pil = load_ui_image(os.path.join(UI_DIR, filename),
                                size=size, threshold=60)
            photo = self._pil_photo(pil)
            if photo is not None:
                cv.create_image(cx - size[0] // 2, cy - size[1] // 2,
                                image=photo)
                cv.create_text(cx, 164, text=caption,
                               font=(self.font_body, 11, "bold"),
                               fill=colour)
                _tag_result_icon(cv, before)
                return

    if rank in ("A+", "A"):
        # trophy
        cv.create_rectangle(cx - 30, cy - 44, cx + 30, cy - 26,
                            fill=COLOURS["gold"], outline="#8a7233")
        cv.create_arc(cx - 44, cy - 44, cx - 14, cy - 14,
                      start=90, extent=180, style=tk.ARC,
                      outline=COLOURS["gold"], width=5)
        cv.create_arc(cx + 14, cy - 44, cx + 44, cy - 14,
                      start=-90, extent=180, style=tk.ARC,
                      outline=COLOURS["gold"], width=5)
        cv.create_polygon(cx - 22, cy - 26, cx + 22, cy - 26,
                          cx + 12, cy + 4, cx - 12, cy + 4,
                          fill=COLOURS["gold"], outline="#8a7233")
        cv.create_rectangle(cx - 8, cy + 4, cx + 8, cy + 26,
                            fill=COLOURS["gold"], outline="")
        cv.create_rectangle(cx - 26, cy + 26, cx + 26, cy + 40,
                            fill=COLOURS["gold_dim"], outline="#5c4c22")
        cv.create_text(cx, cy - 58, text="ESCAPED",
                       font=(self.font_title, 15), fill=COLOURS["gold"])
    elif rank == "B":
        # key
        cv.create_oval(cx - 34, cy - 44, cx + 6, cy - 4,
                       outline=COLOURS["gold"], width=7)
        cv.create_oval(cx - 18, cy - 28, cx - 2, cy - 12,
                       fill=COLOURS["panel"], outline="")
        cv.create_rectangle(cx - 4, cy - 16, cx + 6, cy + 46,
                            fill=COLOURS["gold"], outline="")
        cv.create_rectangle(cx + 6, cy + 22, cx + 24, cy + 32,
                            fill=COLOURS["gold"], outline="")
        cv.create_rectangle(cx + 6, cy + 36, cx + 20, cy + 46,
                            fill=COLOURS["gold"], outline="")
        cv.create_text(cx, cy + 62, text="RELUCTANTLY FREED",
                       font=(self.font_body, 11, "bold"),
                       fill=COLOURS["gold_dim"])
    else:
        # skull
        cv.create_oval(cx - 36, cy - 46, cx + 36, cy + 14,
                       fill="#d8d2c4", outline="")
        cv.create_rectangle(cx - 22, cy + 4, cx + 22, cy + 34,
                            fill="#d8d2c4", outline="")
        cv.create_oval(cx - 24, cy - 26, cx - 4, cy - 6,
                       fill="#08080a", outline="")
        cv.create_oval(cx + 4, cy - 26, cx + 24, cy - 6,
                       fill="#08080a", outline="")
        cv.create_polygon(cx - 4, cy - 4, cx + 4, cy - 4, cx, cy + 8,
                          fill="#08080a", outline="")
        for x in (cx - 14, cx - 5, cx + 4, cx + 13):
            cv.create_line(x, cy + 10, x, cy + 32, fill="#08080a",
                           width=2)
        if rank == "F":
            cv.create_text(cx, cy + 56, text="CAUGHT",
                           font=(self.font_title, 16),
                           fill=COLOURS["wrong"])
        else:
            cv.create_text(cx, cy + 56, text="TRAPPED",
                           font=(self.font_title, 16),
                           fill=COLOURS["gold_dim"])

    _tag_result_icon(cv, before)


def _tag_result_icon(cv, before):
    """Tag every item drawn since ``before`` as a result icon."""
    for item in set(cv.find_all()) - before:
        cv.addtag("resulticon", "withtag", item)


def _on_play_again(self):
    """Jump straight back to the difficulty selection."""
    self.displayMenu()
    self._show_stage("difficulty")


def toggle_music(self):
    """Required-extra function: music ON/OFF button."""
    on = self.audio.toggle_music()
    text = "MUSIC: ON" if on else "MUSIC: OFF"
    for btn in (self.menu_music_btn, self.quiz_music_btn,
                self.results_music_btn):
        btn.text = text
        btn._draw()


def _on_close(self):
    if messagebox.askyesno("The Last 10 Questions",
                           "Leave the school... for good?"):
        self._cancel_all()
        self.audio.stop_music()
        self.root.destroy()


# ==================================================================
#  Bind the loose functions onto the class, then run
# ==================================================================
for _name in (
    "_pil_photo", "_apply_panel", "_tint",
    "_paint_background", "_try_photo", "_vignette",
    "_art_hallway", "_art_classroom", "_art_corridor",
    "_set_flicker", "_flicker_loop", "_flicker_tick", "_flicker_clear",
    "brownout", "_create_dust", "_dust_loop",
    "_draw_door", "_blink_loop", "_eyes_closed", "_eyes_open",
    "flash_entity", "_entity_calm",
    "displayMenu", "_on_play", "_on_back", "_type_text",
    "startGame", "_set_controls", "updateStatus", "displayProblem",
    "submitAnswer", "showFeedback", "isCorrect", "nextQuestion",
    "displayResults", "_build_results_text", "_draw_result_icon",
    "_on_play_again",
    "toggle_music", "_on_close",
):
    setattr(Last10Questions, _name, globals()[_name])

# the two pure helpers take no "self", so bind them as staticmethods -
# callable both as randomInt(...) and game.randomInt(...)
for _name in ("randomInt", "decideOperation"):
    setattr(Last10Questions, _name, staticmethod(globals()[_name]))


def main():
    root = tk.Tk()
    Last10Questions(root)
    root.mainloop()


if __name__ == "__main__":
    main()


