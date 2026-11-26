=============================================================================
 JOKE.exe - "Alexa Tell Me a Joke"
 CodeLab II - Exercise 2
 README
=============================================================================

A retro Pokemon Game Boy style joke-telling assistant built with Python
and Tkinter. The player talks to an NPC called JOKEBOT through classic
Pokemon-style dialogue boxes and discovers random jokes.

Tagline: "Press A to laugh!"


-----------------------------------------------------------------------------
 1. PROJECT FOLDER STRUCTURE
-----------------------------------------------------------------------------

JOKE.exe/
│
├── joke_game.py               <- the complete game (one file)
│
├── resources/
│   └── randomJokes.txt        <- required joke file
│
├── assets/                    <- OPTIONAL (the game runs fine without these)
│   ├── backgrounds/
│   │   └── room.png
│   ├── characters/
│   │   ├── jokebot_idle.png
│   │   └── jokebot_happy.png
│   ├── fonts/
│   │   └── pixel_font.ttf
│   └── sounds/
│       ├── button_click.wav
│       └── punchline.wav
│
└── README.txt                 <- this file


-----------------------------------------------------------------------------
 2. WHERE TO PLACE randomJokes.txt
-----------------------------------------------------------------------------

The joke file MUST be at:

    JOKE.exe/resources/randomJokes.txt

i.e. inside the "resources" folder that sits next to joke_game.py.
It has already been copied there for you.

The file has one joke per line, with the setup and punchline separated
by a question mark, for example:

    Why did the chicken cross the road?To get to the other side.
    What happens if you boil a clown?You get a laughing stock.

A leading dash on a line is allowed and will be removed automatically.
Only the FIRST question mark splits the joke, so punchlines that contain
extra question marks still work. Badly formatted lines are skipped
instead of crashing the program.


-----------------------------------------------------------------------------
 3. RUNNING THE APPLICATION IN VS CODE (Windows)
-----------------------------------------------------------------------------

1. Open the JOKE.exe folder in VS Code  (File > Open Folder...).

2. Open a terminal in VS Code  (Terminal > New Terminal).

3. Make sure Python is installed (python --version). Tkinter ships
   with the official Python installer on Windows - no extra install
   is needed for the base game.

4. Run the game:

       python joke_game.py

   or press F5 if you have a Python launch configuration.

5. Optional: install Pillow if you want to use the optional PNG
   backgrounds / sprites / pixel font:

       pip install pillow

   Pygame is NOT required. Sound effects use the built-in "winsound"
   module on Windows.

6. Interact with the game:
   - Click the four RPG menu buttons at the bottom, OR
   - Press A / Enter / Space: first press finishes the dialogue
     typing, the next press asks JOKEBOT for a joke ("Press A to
     laugh!").
   - Click the dialogue box to finish the typewriter text instantly.
   - The "SOUND: ON/OFF" button at the top toggles sound effects.
   - The "JOKE ##" counter at the top shows how many jokes you
     have heard.


-----------------------------------------------------------------------------
 4. REQUIRED FUNCTIONS - HOW THEY WORK
-----------------------------------------------------------------------------

loadJokes(file_path=JOKE_FILE)
    Opens resources/randomJokes.txt (UTF-8), strips each line, removes
    any leading dash and splits it on the FIRST question mark into a
    (setup, punchline) tuple. Returns a list of those tuples. A missing,
    empty or unreadable file simply returns an empty list - the game
    shows a friendly "joke pokedex is empty" message instead of
    crashing, and the joke buttons are disabled.

randomJoke(jokes)
    Picks one random (setup, punchline) tuple from the list with
    random.choice(). Returns None if the list is empty.

displaySetup(app, joke, npc_line=None)
    Puts a random JOKEBOT message plus the joke SETUP into the
    Pokemon-style dialogue box, increases the joke counter, switches
    JOKEBOT back to his idle face, enables the "Show Punchline"
    button and disables "Next Joke" (so the punchline cannot be
    skipped).

showPunchline(app)
    Does nothing until a joke has been requested. Otherwise it shows
    the SETUP again with the PUNCHLINE underneath it (">> ...") plus a
    funny NPC reaction, switches JOKEBOT to his happy face, plays the
    punchline sound, disables "Show Punchline" and enables "Next Joke".

nextJoke(app)
    Selects another random joke and resets the dialogue state by
    calling randomJoke() and then displaySetup() with a different
    NPC line ("I've got another one!").

quitGame(app)
    Destroys the Tkinter window and closes the application (also
    wired to the window's X button).

Helper functions keep the code organised: set_dialogue() /
finish_typing() run the typewriter effect, _draw_room() and
_draw_npc() paint the pixel-art scene, play_sound() plays optional
.wav effects, and update_joke_counter() updates the "JOKE ##" label.


-----------------------------------------------------------------------------
 5. OPTIONAL ASSETS AND EXPECTED FILENAMES
-----------------------------------------------------------------------------

All of these are OPTIONAL. If a file (or the Pillow library) is
missing, the game automatically falls back to drawn pixel art,
system fonts and silence - it never crashes.

    assets/backgrounds/room.png        Full-scene pixel-art room
                                       (replaces the drawn room).
    assets/characters/jokebot_idle.png  JOKEBOT sprite, idle face.
    assets/characters/jokebot_happy.png JOKEBOT happy face (shown
                                       after a punchline). If only
                                       one sprite exists it is used
                                       for both moods.
    assets/fonts/pixel_font.ttf         Any TrueType pixel font; it
                                       is registered at startup and
                                       used if available, otherwise
                                       Consolas / Courier New is used.
    assets/sounds/button_click.wav      Played when buttons are used.
    assets/sounds/punchline.wav         Played when a punchline is
                                       revealed.
    assets/sounds/bgm.wav               Retro chiptune background music
                                       (looped). A MUSIC: ON/OFF button
                                       toggles it in-game.

Recommended specs:
    - Sprites: small PNGs (around 32x48 pixels), transparent
      background, nearest-neighbour scaled to fit.
    - Background: 640x300 PNG (it is resized to fit the scene).
    - Font: any .ttf that suits a retro look.
    - Sounds: standard .wav files (played with winsound).


-----------------------------------------------------------------------------
 6. TROUBLESHOOTING
-----------------------------------------------------------------------------

- "joke file not found" warning in the terminal:
    Make sure randomJokes.txt is in the resources folder next to
    joke_game.py.

- No sound:
    Sound is optional. Check the file names are exactly
    button_click.wav / punchline.wav in assets/sounds, and that the
    SOUND: ON button at the top says ON.

- Optional images not showing:
    pip install pillow, and check the exact folder/file names above.
    The game works fine without them.

- Window looks too small/large on your screen:
    The window is fixed size and centred automatically; adjust
    SCENE_W / SCENE_H constants in joke_game.py if you change the
    background size.
