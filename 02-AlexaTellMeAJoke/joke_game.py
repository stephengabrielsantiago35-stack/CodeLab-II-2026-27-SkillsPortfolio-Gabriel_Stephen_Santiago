"""
=============================================================================
 JOKE.exe  -  "Alexa Tell Me a Joke"
 CodeLab II - Exercise 2

 A retro Pokemon Game Boy style joke-telling assistant built with Tkinter.

 The player enters a pixel-art room and talks to an NPC called JOKEBOT
 through classic Pokemon-style dialogue boxes.

 Required assignment functions:
     loadJokes()      - loads jokes from resources/randomJokes.txt
     randomJoke()     - randomly selects a joke (setup + punchline)
     displaySetup()   - shows the joke setup in the dialogue box
     showPunchline()  - reveals the punchline
     nextJoke()       - selects another joke and resets the dialogue state
     quitGame()       - closes the application

 Run with:  python joke_game.py
=============================================================================
"""

import os
import random
import tkinter as tk
from tkinter import font as tkfont

# ---------------------------------------------------------------------------
# Optional imports. The game must still run if these are unavailable.
# ---------------------------------------------------------------------------
try:
    import winsound  # built into Python on Windows - used for .wav sounds
except ImportError:
    winsound = None

try:
    from PIL import Image, ImageTk  # only needed for optional PNG assets
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pygame  # optional: better background music/SFX handling
    import pygame.mixer as pygame_mixer
    PYGAME_AVAILABLE = True
except ImportError:
    pygame_mixer = None
    PYGAME_AVAILABLE = False


# ---------------------------------------------------------------------------
# PATHS (relative to this file - no hardcoded computer-specific paths)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOKE_FILE = os.path.join(BASE_DIR, "resources", "randomJokes.txt")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUND_FILE = os.path.join(ASSETS_DIR, "backgrounds", "room.png")
IDLE_SPRITE = os.path.join(ASSETS_DIR, "characters", "jokebot_idle.png")
HAPPY_SPRITE = os.path.join(ASSETS_DIR, "characters", "jokebot_happy.png")
PIXEL_FONT_FILE = os.path.join(ASSETS_DIR, "fonts", "pixel_font.ttf")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
MUSIC_FILE = os.path.join(SOUNDS_DIR, "bgm.wav")

# ---------------------------------------------------------------------------
# GAME BOY COLOUR PALETTE
# ---------------------------------------------------------------------------
GB_LIGHT = "#9BBC0F"   # light green
GB_MED = "#8BAC0F"     # medium green
GB_DARK = "#306230"    # dark green
GB_BLACK = "#0F380F"   # very dark green (used like black)
CREAM = "#F8F8E8"      # dialogue box background

# ---------------------------------------------------------------------------
# LAYOUT / SCENE CONSTANTS
# ---------------------------------------------------------------------------
WINDOW_W = 700          # fixed window width
MIN_WINDOW_H = 560      # minimum window height (grows if text needs room)
SCENE_W = 680           # game scene canvas size
SCENE_H = 300
FLOOR_TOP = 110         # where the wall ends and the floor begins
NPC_X = 285             # top-left of the JOKEBOT sprite
NPC_Y = 210

# ---------------------------------------------------------------------------
# JOKEBOT PERSONALITY (random lines keep the NPC feeling alive)
# ---------------------------------------------------------------------------
GREETINGS = [
    "JOKEBOT: Oh! Hello there, trainer!",
    "JOKEBOT: Well hello, trainer! Fancy seeing you here!",
    "JOKEBOT: Psst! Over here, trainer!",
    "JOKEBOT: Beep boop! Welcome, trainer!",
]

SETUP_LINES = [
    "JOKEBOT: Let me check my joke Pokedex...",
    "JOKEBOT: Here's a good one!",
    "JOKEBOT: Ooh ooh! I know a great one!",
    "JOKEBOT: Loading joke... done! Here goes!",
    "JOKEBOT: This one always gets 'em!",
]

PUNCH_LINES = [
    "JOKEBOT: HAHA! Get it?",
    "JOKEBOT: Bwahaha! I crack myself up!",
    "JOKEBOT: Hehehe! ...Was that a good one?",
    "JOKEBOT: HAHA! Book it in the funny hall of fame!",
    "JOKEBOT: BEEP BOOP! Joke delivered successfully!",
]

NEXT_LINES = [
    "JOKEBOT: I've got another one!",
    "JOKEBOT: Wait wait, here's a better one!",
    "JOKEBOT: Round two! Ready, trainer?",
    "JOKEBOT: My joke buffer is full of gold!",
]

QUIT_LINE = "JOKEBOT: Logging off! Stay funny, trainer!"


# ===========================================================================
# REQUIRED ASSIGNMENT FUNCTIONS
# ===========================================================================
def loadJokes(file_path=JOKE_FILE):
    """
    Load jokes from randomJokes.txt into a list.

    Each line looks like:
        - Why did the chicken cross the road?To get to the other side.

    Returns a list of (setup, punchline) tuples.
    Returns an empty list if the file is missing, empty or unreadable
    (the game shows a friendly message instead of crashing).
    """
    jokes = []

    # Gracefully handle a missing joke file.
    if not os.path.isfile(file_path):
        print("[JOKE.exe] WARNING: joke file not found: " + file_path)
        return jokes

    try:
        with open(file_path, "r", encoding="utf-8-sig") as joke_file:
            for line in joke_file:
                # Remove the leading dash and any unnecessary spaces.
                cleaned = line.strip().lstrip("-").strip()
                if not cleaned:
                    continue

                # Split on the FIRST question mark only, so extra question
                # marks inside the punchline do not break the joke.
                setup, separator, punchline = cleaned.partition("?")

                # Skip malformed lines instead of crashing.
                if not separator or not punchline.strip():
                    print("[JOKE.exe] Skipping malformed line: " + line.strip())
                    continue

                setup = setup.strip() + "?"
                punchline = punchline.strip()
                jokes.append((setup, punchline))

    except (OSError, UnicodeDecodeError) as error:
        print("[JOKE.exe] Could not read joke file: " + str(error))
        return jokes

    if not jokes:
        print("[JOKE.exe] WARNING: joke file is empty or has no valid jokes.")
    return jokes


def randomJoke(jokes):
    """
    Randomly select a joke from the loaded joke list.
    Returns a (setup, punchline) tuple, or None if the list is empty.
    """
    if not jokes:
        return None
    setup, punchline = random.choice(jokes)
    return setup, punchline


def displaySetup(app, joke, npc_line=None):
    """
    Display the joke setup inside the Pokemon-style dialogue box,
    then enable the "Show Punchline" button.

    app:       the running JokeGame application
    joke:      (setup, punchline) tuple from randomJoke()
    npc_line:  optional NPC line to show above the setup
    """
    if joke is None:
        app.set_dialogue("JOKEBOT: My joke pokedex is empty! No jokes found...")
        return

    setup, punchline = joke

    # Reset dialogue state for the new joke.
    app.current_joke = (setup, punchline)
    app.punchline_shown = False
    app.joke_count += 1

    if npc_line is None:
        npc_line = random.choice(SETUP_LINES)

    # Show the NPC message first, then the joke setup underneath it.
    app.set_dialogue(npc_line + "\n\n" + setup)
    app.set_npc_mood("idle")
    app.update_joke_counter()

    # The player can now reveal the punchline, but not skip ahead.
    app.btn_punch.config(state="normal")
    app.btn_next.config(state="disabled")


def showPunchline(app):
    """
    Display the punchline below the setup in the dialogue box.
    Does nothing if no joke has been requested yet or if the
    punchline is already showing.
    """
    if app.current_joke is None or app.punchline_shown:
        return

    setup, punchline = app.current_joke
    app.punchline_shown = True

    reaction = random.choice(PUNCH_LINES)

    # Punchline appears below the setup, followed by the NPC reaction.
    app.set_dialogue(setup + "\n\n>> " + punchline + "\n\n" + reaction)
    app.set_npc_mood("happy")
    app.play_sound("punchline.wav")

    # Punchline is spent - the player needs the next joke instead.
    app.btn_punch.config(state="disabled")
    app.btn_next.config(state="normal")


def nextJoke(app):
    """Select another random joke and reset the dialogue state."""
    if not app.jokes:
        app.set_dialogue("JOKEBOT: My joke pokedex is empty! No jokes found...")
        return

    # Pick a fresh joke and show its setup (displaySetup resets state).
    joke = randomJoke(app.jokes)
    displaySetup(app, joke, npc_line=random.choice(NEXT_LINES))
    app.play_sound("button_click.wav")


def quitGame(app):
    """Close the application."""
    try:
        app._stop_music()
        if getattr(app, "_pygame_ok", False) and pygame_mixer.get_init():
            pygame_mixer.quit()
    except Exception:
        pass
    app.root.destroy()


# ===========================================================================
# THE GAME APPLICATION
# ===========================================================================
class JokeGame:
    """Builds the retro Pokemon-style window and keeps track of game state."""

    def __init__(self, root):
        self.root = root
        root.title("JOKE.exe - Alexa Tell Me a Joke")
        root.configure(bg=GB_BLACK)
        root.resizable(False, False)          # fixed-size game window

        # --- game state ---
        self.jokes = loadJokes()
        self.current_joke = None              # (setup, punchline) or None
        self.punchline_shown = False
        self.joke_count = 0
        self.sound_on = True
        self.music_on = True
        self._music_started = False
        self.npc_mood = "idle"                # "idle" or "happy"
        self.anim_tick = 0

        # --- typewriter state ---
        self.full_text = ""
        self.shown_text = ""
        self._type_job = None
        self._arrow_job = None
        self._anim_job = None

        # --- optional image assets (None means use the drawn fallback) ---
        self.room_photo = None
        self.sprite_idle = None
        self.sprite_happy = None

        self.font_family = self._load_font()

        # --- build the interface ---
        self._build_topbar()
        self._build_scene()
        self._build_dialogue()
        self._build_buttons()
        self._bind_keys()

        root.protocol("WM_DELETE_WINDOW", lambda: quitGame(self))

        # Initialise audio and start retro background music (optional).
        self._init_audio()
        self._start_music()

        # Opening NPC dialogue (random greeting each run).
        opening = random.choice(GREETINGS) + "\n" + "JOKEBOT: Want to hear a joke?"
        if not self.jokes:
            opening += ("\n\nJOKEBOT: Oh no... my joke pokedex can't find "
                        "resources/randomJokes.txt!")
            self.btn_alexa.config(state="disabled")
        self.set_dialogue(opening)

        # Start the little NPC blink/bob animation loop.
        self._anim_job = self.root.after(800, self._animate_npc)

        self._center_window()

    # ------------------------------------------------------------------
    # Font: try the optional pixel font, otherwise use a monospace font.
    # ------------------------------------------------------------------
    def _load_font(self):
        # Try to register the optional pixel font file on Windows.
        if os.path.isfile(PIXEL_FONT_FILE):
            try:
                import ctypes
                ctypes.windll.gdi32.AddFontResourceW(PIXEL_FONT_FILE)
            except Exception:
                pass

        families = tkfont.families()
        for family in families:
            lowered = family.lower()
            if "pixel" in lowered or "press start" in lowered:
                return family
        for family in ("Consolas", "Courier New", "Lucida Console"):
            if family in families:
                return family
        return "Courier New"

    # ------------------------------------------------------------------
    # Top status bar: title, tagline, joke counter and sound toggle.
    # ------------------------------------------------------------------
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=GB_BLACK, height=42)
        bar.pack(fill="x", padx=8, pady=(8, 4))
        bar.pack_propagate(False)

        tk.Label(
            bar, text="JOKE.exe", bg=GB_BLACK, fg=GB_LIGHT,
            font=(self.font_family, 11, "bold"),
        ).pack(side="left", padx=6)

        tk.Label(
            bar, text="PRESS A TO LAUGH!", bg=GB_BLACK, fg=GB_MED,
            font=(self.font_family, 7, "bold"),
        ).pack(side="left", padx=10)

        self.counter_label = tk.Label(
            bar, text="JOKE 00", bg=GB_BLACK, fg=GB_LIGHT,
            font=(self.font_family, 8, "bold"),
        )
        self.counter_label.pack(side="right", padx=6)

        self.music_button = tk.Button(
            bar, text="MUSIC: ON", command=self.toggle_music,
            bg=GB_MED, fg=GB_BLACK, activebackground=GB_DARK,
            activeforeground=GB_LIGHT, relief="raised", bd=3,
            font=(self.font_family, 7, "bold"),
        )
        self.music_button.pack(side="right", padx=4)

        self.sound_button = tk.Button(
            bar, text="SOUND: ON", command=self.toggle_sound,
            bg=GB_MED, fg=GB_BLACK, activebackground=GB_DARK,
            activeforeground=GB_LIGHT, relief="raised", bd=3,
            font=(self.font_family, 7, "bold"),
        )
        self.sound_button.pack(side="right", padx=4)

    # ------------------------------------------------------------------
    # Game scene: pixel-art room + JOKEBOT NPC.
    # ------------------------------------------------------------------
    def _build_scene(self):
        frame = tk.Frame(self.root, bg=GB_BLACK, padx=4, pady=4)
        frame.pack()

        self.scene = tk.Canvas(
            frame, width=SCENE_W, height=SCENE_H, bg=GB_DARK,
            highlightthickness=0, bd=0,
        )
        self.scene.pack()

        self._load_optional_assets()

        # Use room.png when available, otherwise draw the room from shapes.
        if self.room_photo is not None:
            self.scene.create_image(0, 0, image=self.room_photo, anchor="nw")
        else:
            self._draw_room()

        self._draw_npc()
        self._draw_nameplate()

    # ------------------------------------------------------------------
    # Optional assets: room.png, jokebot_idle.png, jokebot_happy.png.
    # Missing files simply fall back to the drawn pixel art.
    # ------------------------------------------------------------------
    def _load_optional_assets(self):
        if not PIL_AVAILABLE:
            return
        try:
            if os.path.isfile(BACKGROUND_FILE):
                img = Image.open(BACKGROUND_FILE).convert("RGB")
                img = img.resize((SCENE_W, SCENE_H), self._nearest())
                self.room_photo = ImageTk.PhotoImage(img)

            for attr, path in (("sprite_idle", IDLE_SPRITE),
                               ("sprite_happy", HAPPY_SPRITE)):
                if os.path.isfile(path):
                    img = Image.open(path).convert("RGBA")
                    scale = min(40.0 / img.width, 50.0 / img.height, 1.0)
                    if scale < 1.0:
                        size = (max(1, int(img.width * scale)),
                                max(1, int(img.height * scale)))
                        img = img.resize(size, self._nearest())
                    setattr(self, attr, ImageTk.PhotoImage(img))

            # If only one expression sprite exists, reuse it for both.
            if self.sprite_happy is None:
                self.sprite_happy = self.sprite_idle
            if self.sprite_idle is None:
                self.sprite_idle = self.sprite_happy

        except Exception as error:
            print("[JOKE.exe] Could not load optional image: " + str(error))

    @staticmethod
    def _nearest():
        """Nearest-neighbour resampling keeps pixel art crisp."""
        if hasattr(Image, "Resampling"):
            return Image.Resampling.NEAREST
        return Image.NEAREST

    # ------------------------------------------------------------------
    # Procedural pixel-art room (used when room.png is missing).
    # ------------------------------------------------------------------
    def _draw_room(self):
        c = self.scene

        # --- back wall ---
        c.create_rectangle(0, 0, SCENE_W, FLOOR_TOP, fill=GB_DARK, outline=GB_DARK)
        c.create_rectangle(0, 0, SCENE_W, 6, fill=GB_BLACK, outline=GB_BLACK)
        # subtle wallpaper squares
        for x in range(24, SCENE_W - 24, 64):
            c.create_rectangle(x, 30, x + 16, 46, fill=GB_DARK, outline=GB_MED)
        # wainscot (lower wall panel with a black rail)
        c.create_rectangle(0, FLOOR_TOP - 26, SCENE_W, FLOOR_TOP,
                           fill=GB_MED, outline=GB_MED)
        c.create_rectangle(0, FLOOR_TOP - 26, SCENE_W, FLOOR_TOP - 23,
                           fill=GB_BLACK, outline=GB_BLACK)

        # --- checkerboard floor ---
        tile = 32
        row = 0
        for y in range(FLOOR_TOP, SCENE_H, tile):
            col = 0
            for x in range(0, SCENE_W, tile):
                color = GB_LIGHT if (row + col) % 2 == 0 else GB_MED
                c.create_rectangle(x, y, x + tile, y + tile,
                                   fill=color, outline=color)
                col += 1
            row += 1
        # baseboard along the floor edge
        c.create_rectangle(0, FLOOR_TOP, SCENE_W, FLOOR_TOP + 4,
                           fill=GB_BLACK, outline=GB_BLACK)

        # --- window on the wall ---
        c.create_rectangle(48, 16, 152, 78, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(54, 22, 146, 72, fill=GB_LIGHT, outline=GB_LIGHT)
        c.create_rectangle(96, 22, 100, 72, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(54, 44, 146, 48, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(44, 78, 156, 86, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(48, 80, 152, 84, fill=GB_MED, outline=GB_MED)

        # --- smiley poster ---
        c.create_rectangle(450, 14, 550, 82, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(454, 18, 546, 78, fill=CREAM, outline=CREAM)
        c.create_rectangle(470, 32, 480, 42, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(510, 32, 520, 42, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(472, 52, 476, 58, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(476, 58, 524, 62, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(520, 52, 524, 58, fill=GB_BLACK, outline=GB_BLACK)

        # --- bookshelf full of books ---
        c.create_rectangle(24, 150, 110, 246, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(28, 154, 106, 242, fill=GB_DARK, outline=GB_DARK)
        book_colors = [GB_LIGHT, GB_MED, GB_DARK]
        heights = [22, 18, 24, 20, 16, 24, 20, 18]
        for baseline in (184, 214, 242):
            book_x = 30
            i = 0
            while book_x < 102:
                h = heights[i % len(heights)]
                top = baseline - h
                c.create_rectangle(book_x, top, book_x + 6, baseline,
                                   fill=book_colors[i % 3], outline=GB_BLACK)
                book_x += 8
                i += 1
        # shelf bars
        c.create_rectangle(28, 184, 106, 188, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(28, 214, 106, 218, fill=GB_BLACK, outline=GB_BLACK)

        # --- rug ---
        c.create_rectangle(150, 196, 350, 270, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(154, 200, 346, 266, fill=GB_DARK, outline=GB_DARK)
        c.create_rectangle(166, 212, 334, 254, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(178, 224, 322, 242, fill=GB_DARK, outline=GB_DARK)

        # --- computer desk ---
        c.create_rectangle(418, 164, 618, 178, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(420, 167, 616, 175, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(426, 178, 610, 236, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(430, 182, 606, 232, fill=GB_DARK, outline=GB_DARK)
        c.create_rectangle(430, 198, 606, 201, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(430, 216, 606, 219, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(498, 188, 538, 192, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(498, 206, 538, 210, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(426, 236, 440, 248, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(596, 236, 610, 248, fill=GB_BLACK, outline=GB_BLACK)

        # --- computer monitor with "code" on screen ---
        c.create_rectangle(466, 96, 570, 146, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(470, 100, 566, 142, fill=GB_DARK, outline=GB_DARK)
        c.create_rectangle(476, 106, 530, 110, fill=GB_LIGHT, outline=GB_LIGHT)
        c.create_rectangle(476, 114, 550, 118, fill=GB_LIGHT, outline=GB_LIGHT)
        c.create_rectangle(476, 122, 520, 126, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(476, 130, 540, 134, fill=GB_LIGHT, outline=GB_LIGHT)
        c.create_rectangle(544, 130, 552, 134, fill=CREAM, outline=CREAM)
        c.create_rectangle(514, 146, 522, 158, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(496, 158, 540, 164, fill=GB_BLACK, outline=GB_BLACK)

        # --- keyboard ---
        c.create_rectangle(466, 166, 550, 176, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(468, 168, 548, 174, fill=GB_MED, outline=GB_MED)
        for i in range(5):
            c.create_rectangle(471 + i * 15, 169, 479 + i * 15, 173,
                               fill=GB_LIGHT, outline=GB_LIGHT)

        # --- potted plant ---
        c.create_rectangle(360, 214, 404, 222, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(363, 216, 401, 220, fill=GB_MED, outline=GB_MED)
        c.create_rectangle(365, 222, 399, 242, fill=GB_BLACK, outline=GB_BLACK)
        c.create_rectangle(368, 225, 396, 239, fill=GB_DARK, outline=GB_DARK)
        for leaf in ((378, 194, 384, 214), (366, 200, 372, 216),
                     (390, 200, 396, 216), (372, 188, 378, 208),
                     (384, 188, 390, 208), (378, 180, 384, 194)):
            c.create_rectangle(leaf[0], leaf[1], leaf[2], leaf[3],
                               fill=GB_LIGHT, outline=GB_BLACK)

    # ------------------------------------------------------------------
    # JOKEBOT sprite: drawn pixel by pixel (or from an optional PNG).
    # Redrawn every animation tick so it can blink, bob and change face.
    # ------------------------------------------------------------------
    def _draw_npc(self):
        c = self.scene
        c.delete("npc")

        x = NPC_X
        y = NPC_Y
        # Happy JOKEBOT bobs up and down.
        if self.npc_mood == "happy" and self.anim_tick % 2 == 0:
            y -= 3

        # Optional sprite images replace the drawn robot.
        sprite = self.sprite_happy if self.npc_mood == "happy" else self.sprite_idle
        if sprite is not None:
            c.create_image(x + 15, y + 40, image=sprite, anchor="s", tags="npc")
            return

        blinking = (self.anim_tick % 7 == 0)
        phase = self.anim_tick % 2

        def rect(rx, ry, rw, rh, fill):
            """Helper: draw one pixel-art block relative to the sprite."""
            c.create_rectangle(x + rx, y + ry, x + rx + rw, y + ry + rh,
                               fill=fill, outline=fill, tags="npc")

        # shadow on the floor
        c.create_oval(x - 6, y + 36, x + 36, y + 46,
                      fill=GB_DARK, outline=GB_DARK, tags="npc")

        # antenna
        rect(14, -6, 2, 6, GB_BLACK)
        rect(11, -11, 8, 6, GB_BLACK)
        rect(12, -10, 6, 4, GB_MED)

        # head
        rect(2, 0, 26, 18, GB_BLACK)
        rect(4, 2, 22, 14, GB_LIGHT)

        # eyes (blink / happy squint / normal with a glint)
        if blinking:
            rect(8, 8, 5, 1, GB_BLACK)
            rect(19, 8, 5, 1, GB_BLACK)
        elif self.npc_mood == "happy":
            rect(8, 7, 5, 3, GB_BLACK)
            rect(18, 7, 5, 3, GB_BLACK)
        else:
            rect(8, 6, 4, 5, GB_BLACK)
            rect(18, 6, 4, 5, GB_BLACK)
            rect(9, 7, 1, 1, CREAM)
            rect(19, 7, 1, 1, CREAM)

        # mouth (flat when idle, smiling when happy)
        if self.npc_mood == "happy":
            rect(9, 12, 2, 2, GB_BLACK)
            rect(11, 14, 8, 2, GB_BLACK)
            rect(19, 12, 2, 2, GB_BLACK)
        else:
            rect(11, 13, 8, 2, GB_BLACK)

        # body with blinking chest lights
        rect(0, 18, 30, 16, GB_BLACK)
        rect(2, 20, 26, 12, GB_LIGHT)
        rect(7, 22, 16, 8, GB_DARK)
        rect(9, 24, 3, 3, GB_LIGHT if phase else GB_MED)
        rect(15, 24, 3, 3, GB_MED if phase else GB_LIGHT)

        # arms and legs
        rect(-5, 20, 5, 10, GB_BLACK)
        rect(30, 20, 5, 10, GB_BLACK)
        rect(4, 34, 8, 6, GB_BLACK)
        rect(18, 34, 8, 6, GB_BLACK)

    def _draw_nameplate(self):
        """Name chip that floats above JOKEBOT's head."""
        c = self.scene
        c.create_rectangle(262, 166, 338, 186, fill=CREAM,
                           outline=GB_BLACK, width=3, tags="nameplate")
        c.create_text(300, 176, text="JOKEBOT", fill=GB_BLACK,
                      font=(self.font_family, 7, "bold"), tags="nameplate")
        c.create_polygon(296, 186, 304, 186, 300, 192,
                         fill=GB_BLACK, outline=GB_BLACK, tags="nameplate")

    def _animate_npc(self):
        """Simple animation loop: blinking eyes and happy bobbing."""
        self.anim_tick += 1
        self._draw_npc()
        delay = 350 if self.npc_mood == "happy" else 800
        self._anim_job = self.root.after(delay, self._animate_npc)

    def set_npc_mood(self, mood):
        self.npc_mood = mood
        self._draw_npc()

    # ------------------------------------------------------------------
    # Pokemon-style dialogue box with a blinking continuation arrow.
    # ------------------------------------------------------------------
    def _build_dialogue(self):
        # Thick pixel border: black frame -> dark green frame -> cream face.
        outer = tk.Frame(self.root, bg=GB_BLACK, padx=6, pady=6)
        outer.pack(fill="x", padx=8, pady=6)

        middle = tk.Frame(outer, bg=GB_DARK, padx=4, pady=4)
        middle.pack(fill="both", expand=True)

        face = tk.Frame(middle, bg=CREAM)
        face.pack(fill="both", expand=True)

        self.dialogue_label = tk.Label(
            face, text="", bg=CREAM, fg=GB_BLACK, justify="left", anchor="w",
            font=(self.font_family, 9), padx=14, pady=12,
            wraplength=580,
        )
        self.dialogue_label.pack(fill="both", expand=True)

        # Small triangular "more dialogue" arrow (blinks when text is ready).
        self.arrow = tk.Canvas(face, width=18, height=14, bg=CREAM,
                               highlightthickness=0, bd=0)
        self.arrow.place(relx=1.0, rely=1.0, x=-22, y=-18, anchor="se")
        self.arrow_id = self.arrow.create_polygon(
            1, 1, 15, 1, 8, 11, fill=GB_BLACK, outline=GB_BLACK, state="hidden")

        # Clicking the dialogue finishes the typewriter effect instantly.
        for widget in (face, self.dialogue_label, self.arrow):
            widget.bind("<Button-1>", lambda event: self.finish_typing())

    def set_dialogue(self, text):
        """Replace the dialogue text and start the typewriter effect."""
        self.full_text = text
        self.shown_text = ""
        self.dialogue_label.config(text="")
        self._hide_arrow()

        if self._type_job is not None:
            self.root.after_cancel(self._type_job)
            self._type_job = None

        self._type_step()

    def _type_step(self):
        """Reveal the text two characters at a time (buttons stay usable)."""
        if len(self.shown_text) >= len(self.full_text):
            self._type_job = None
            self._show_arrow()
            return
        self.shown_text = self.full_text[:len(self.shown_text) + 2]
        self.dialogue_label.config(text=self.shown_text)
        self._type_job = self.root.after(16, self._type_step)

    def finish_typing(self):
        """Instantly show the rest of the current dialogue text."""
        if self._type_job is not None:
            self.root.after_cancel(self._type_job)
            self._type_job = None
        self.shown_text = self.full_text
        self.dialogue_label.config(text=self.full_text)
        self._show_arrow()

    def _show_arrow(self):
        self._hide_arrow()
        self.arrow.itemconfigure(self.arrow_id, state="normal")
        self._blink_arrow()

    def _blink_arrow(self):
        current = self.arrow.itemcget(self.arrow_id, "state")
        self.arrow.itemconfigure(
            self.arrow_id, state="hidden" if current == "normal" else "normal")
        self._arrow_job = self.root.after(500, self._blink_arrow)

    def _hide_arrow(self):
        if self._arrow_job is not None:
            self.root.after_cancel(self._arrow_job)
            self._arrow_job = None
        self.arrow.itemconfigure(self.arrow_id, state="hidden")

    # ------------------------------------------------------------------
    # RPG-style menu buttons.
    # ------------------------------------------------------------------
    def _build_buttons(self):
        row = tk.Frame(self.root, bg=GB_BLACK)
        row.pack(fill="x", padx=8, pady=(2, 4))
        for col in range(4):
            row.grid_columnconfigure(col, weight=1)

        self.btn_alexa = self._make_button(
            row, "Alexa tell me a Joke", self.on_tell_joke,
            enabled=bool(self.jokes))
        self.btn_punch = self._make_button(
            row, "Show Punchline", self.on_show_punchline, enabled=False)
        self.btn_next = self._make_button(
            row, "Next Joke", self.on_next_joke, enabled=False)
        self.btn_quit = self._make_button(
            row, "Quit", self.on_quit, enabled=True)

        for col, button in enumerate(
                (self.btn_alexa, self.btn_punch, self.btn_next, self.btn_quit)):
            button.grid(row=0, column=col, sticky="nsew", padx=5, pady=6)

        tk.Label(
            self.root, text="TIP: Press A / Enter to talk to JOKEBOT!",
            bg=GB_BLACK, fg=GB_MED, font=(self.font_family, 6),
        ).pack(pady=(0, 8))

    def _make_button(self, parent, text, command, enabled=True):
        return tk.Button(
            parent, text=text, command=command,
            font=(self.font_family, 7, "bold"),
            bg=GB_MED, fg=GB_BLACK,
            activebackground=GB_DARK, activeforeground=GB_LIGHT,
            disabledforeground=GB_DARK,
            relief="raised", bd=4, padx=4, pady=5,
            state="normal" if enabled else "disabled",
        )

    def _bind_keys(self):
        """Press A / Enter / Space to talk (tagline: Press A to laugh!)."""
        self.root.bind("<Key>", self._on_key)

    def _on_key(self, event):
        key = (event.keysym or "").lower()
        if key in ("a", "return", "space"):
            if self.shown_text != self.full_text:
                self.finish_typing()      # first press skips the typewriter
            else:
                self.on_tell_joke()       # later presses ask for a joke

    # ------------------------------------------------------------------
    # Button handlers (each returns keyboard focus to the window).
    # ------------------------------------------------------------------
    def on_tell_joke(self):
        if not self.jokes:
            return
        joke = randomJoke(self.jokes)
        displaySetup(self, joke)
        self.play_sound("button_click.wav")
        self.root.focus_set()

    def on_show_punchline(self):
        showPunchline(self)
        self.root.focus_set()

    def on_next_joke(self):
        nextJoke(self)
        self.root.focus_set()

    def on_quit(self):
        quitGame(self)

    # ------------------------------------------------------------------
    # Small helpers.
    # ------------------------------------------------------------------
    def update_joke_counter(self):
        self.counter_label.config(text="JOKE %02d" % self.joke_count)

    # ------------------------------------------------------------------
    # Audio: background music + SFX (optional, never crashes if missing).
    # ------------------------------------------------------------------
    def _init_audio(self):
        """Initialise pygame mixer if available for better music/SFX."""
        self._pygame_ok = False
        if not PYGAME_AVAILABLE:
            return
        try:
            if not pygame_mixer.get_init():
                pygame_mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._pygame_ok = True
        except Exception as error:
            print("[JOKE.exe] Audio init failed: " + str(error))
            self._pygame_ok = False

    def _start_music(self):
        """Start looping retro background music if enabled and available."""
        if not self.music_on or self._music_started:
            return
        if not os.path.isfile(MUSIC_FILE):
            return
        try:
            if self._pygame_ok:
                pygame_mixer.music.load(MUSIC_FILE)
                pygame_mixer.music.set_volume(0.35)
                pygame_mixer.music.play(-1)  # loop forever
                self._music_started = True
            elif winsound is not None:
                winsound.PlaySound(
                    MUSIC_FILE,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP | winsound.SND_NODEFAULT)
                self._music_started = True
        except Exception as error:
            print("[JOKE.exe] Could not start music: " + str(error))

    def _stop_music(self):
        """Stop background music."""
        try:
            if self._pygame_ok and pygame_mixer.get_init():
                pygame_mixer.music.stop()
            elif winsound is not None:
                # Stop any async winsound playback (including looped music).
                winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self._music_started = False

    def toggle_music(self):
        self.music_on = not self.music_on
        self.music_button.config(text="MUSIC: ON" if self.music_on else "MUSIC: OFF")
        if self.music_on:
            self._start_music()
        else:
            self._stop_music()

    def play_sound(self, filename):
        """Play an optional .wav effect (silently skips missing files)."""
        if not self.sound_on:
            return
        path = os.path.join(SOUNDS_DIR, filename)
        if not os.path.isfile(path):
            return
        try:
            if self._pygame_ok:
                # pygame mixer handles SFX alongside music.
                sound = pygame_mixer.Sound(path)
                sound.set_volume(0.7)
                sound.play()
            elif winsound is not None:
                # winsound async SFX interrupts looped music; restart music after.
                flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                winsound.PlaySound(path, flags)
                if self.music_on and self._music_started:
                    # Restart music after the short SFX finishes.
                    self._music_started = False
                    self.root.after(350, self._start_music)
        except Exception:
            pass

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.sound_button.config(text="SOUND: ON" if self.sound_on else "SOUND: OFF")
        if self.sound_on:
            self.play_sound("button_click.wav")

    def _center_window(self):
        """Fix the window size and centre it on the screen."""
        self.root.update_idletasks()
        height = max(MIN_WINDOW_H, self.root.winfo_reqheight())
        x = (self.root.winfo_screenwidth() - WINDOW_W) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry("%dx%d+%d+%d" % (WINDOW_W, height, x, y))


# ===========================================================================
# ENTRY POINT
# ===========================================================================
def main():
    root = tk.Tk()
    JokeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()


