THE ACADEMY LEDGER
==================
The records of every apprentice are in your hands.

Fantasy academy student records management system (Python + Tkinter).
Preserves the original Student Manager functionality and file format.

## Folder Structure

The_Academy_Ledger/   (this folder: AcademyLedger)
├── main.py
├── student_manager.py
├── README.txt
├── PORTFOLIO_DOCUMENTATION.txt
├── resources/
│   └── studentMarks.txt
└── assets/
    ├── backgrounds/
    │   ├── academy_library.jpg      (Main Menu)
    │   ├── library_records.jpg      (Student Records/Search/Sort/Highest/Lowest)
    │   ├── parchment_texture.jpg    (Add/Update forms)
    │   └── academy_night.jpg        (Delete screen)
    ├── icons/
    │   ├── academy_crest.png
    │   ├── book.png
    │   └── quill.png
    └── fonts/                       (optional)

## Placing studentMarks.txt

Place the existing data file at:
  resources/studentMarks.txt

Original format is preserved:
  Line 1: number of student records
  Following lines: code,name,coursework1,coursework2,coursework3,exam
Example:
  10
  1345,John Curry,8,15,7,45

The app uses a relative path based on the script location, so it works when you
open the AcademyLedger folder in VS Code.

## Running in VS Code (Windows)

1. Open VS Code.
2. File > Open Folder... > select the AcademyLedger folder.
3. Confirm resources/studentMarks.txt exists.
4. (Optional, for background images/icons) install Pillow:
     pip install pillow
5. Open Terminal (Ctrl+`) and run:
     python main.py
   or:
     python student_manager.py
   If needed:
     py main.py

## Features (all preserved + extended)

1. View all student records (table with calculated totals)
2. Search student by name or code
3. Show highest total student
4. Show lowest total student
5. Sort records ascending/descending by code, name, or overall total
6. Add student record (validated, saved)
7. Delete student record (confirmation, saved)
8. Update student record (validated, saved)

## Visual Design

- Theme: The Academy Ledger - enchanted academy archive / midnight library.
- Palette: Midnight navy #101827, Deep blue #18263B, Parchment #F0E4C8,
  Warm gold #C9A45C, Muted sage #82927A, Dark ink #29271F.
- Typography: Georgia (display/headings) + Segoe UI (body/controls).
- Signature element: gold ledger spine with archival index marks.
- Section backgrounds: fantasy library/parchment/archive/night imagery with dark
  overlays and readable parchment panels.
- Optional fantasy music: place a loopable audio file at
  assets/audio/fantasy_theme.wav (included). Toggle with the Music button in the
  status bar. Uses pygame.mixer if installed, otherwise winsound on Windows.
- Design guided by Anthropic Frontend Design skill principles (read from public
  GitHub SKILL.md; adapted to Tkinter desktop UI; not installed as a system skill).