
import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os

# COLOURS
BG = "#F2F2F2"
WHITE = "#FFFFFF"
BLUE = "#2878D0"
TEXT = "#222222"
GREY = "#777777"

# FILE LOCATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_FILE = os.path.join(BASE_DIR, "resources", "studentMarks.txt")
SAME_FOLDER_FILE = os.path.join(BASE_DIR, "studentMarks.txt")
FILE_PATH = RESOURCE_FILE if os.path.exists(RESOURCE_FILE) else SAME_FOLDER_FILE

students = []

# CALCULATIONS
def calculateTotal(student):
    coursework = student["coursework1"] + student["coursework2"] + student["coursework3"]
    return coursework, coursework + student["exam"]

def calculatePercentage(student):
    return calculateTotal(student)[1] / 160 * 100

def calculateGrade(percentage):
    if percentage >= 70: return "A"
    if percentage >= 60: return "B"
    if percentage >= 50: return "C"
    if percentage >= 40: return "D"
    return "F"

def getStudentResults(student):
    cw, total = calculateTotal(student)
    pct = calculatePercentage(student)
    return cw, total, pct, calculateGrade(pct)

# LOAD / SAVE
def loadStudents():
    global students
    students = []

    if not os.path.exists(FILE_PATH):
        messagebox.showerror("Error", "studentMarks.txt could not be found.")
        return

    try:
        with open(FILE_PATH, "r", newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))

        if not rows:
            raise ValueError("The file is empty.")

        expected = int(rows[0][0])

        for n, row in enumerate(rows[1:], start=2):
            if not row:
                continue
            if len(row) != 6:
                raise ValueError(f"Row {n} must contain 6 values.")

            s = {
                "code": row[0].strip(),
                "name": row[1].strip(),
                "coursework1": int(row[2]),
                "coursework2": int(row[3]),
                "coursework3": int(row[4]),
                "exam": int(row[5])
            }

            if not s["code"].isdigit() or not 1000 <= int(s["code"]) <= 9999:
                raise ValueError(f"Invalid student code on row {n}.")
            if not s["name"]:
                raise ValueError(f"Missing name on row {n}.")
            if any(not 0 <= s[k] <= 20 for k in ("coursework1", "coursework2", "coursework3")):
                raise ValueError(f"Invalid coursework marks on row {n}.")
            if not 0 <= s["exam"] <= 100:
                raise ValueError(f"Invalid exam mark on row {n}.")
            if any(x["code"] == s["code"] for x in students):
                raise ValueError(f"Duplicate student code: {s['code']}.")

            students.append(s)

        if expected != len(students):
            messagebox.showwarning("Warning", f"Expected {expected} records, loaded {len(students)}.")

    except (ValueError, IndexError, OSError) as e:
        students = []
        messagebox.showerror("File Error", str(e))

def saveStudents():
    try:
        os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

        with open(FILE_PATH + ".tmp", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([len(students)])

            for s in students:
                writer.writerow([
                    s["code"], s["name"], s["coursework1"],
                    s["coursework2"], s["coursework3"], s["exam"]
                ])

        os.replace(FILE_PATH + ".tmp", FILE_PATH)
        return True

    except OSError as e:
        messagebox.showerror("Saving Error", str(e))
        return False

# MAIN WINDOW
root = tk.Tk()
root.title("Student Manager")
root.geometry("1100x720")
root.minsize(950, 600)
root.configure(bg=BG)

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", font=("Arial", 10), rowheight=30)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

# GUI HELPERS
def clearContent():
    for widget in content.winfo_children():
        widget.destroy()

def makeButton(parent, text, command, color=BLUE):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=WHITE, activebackground=color,
        activeforeground=WHITE, relief="flat",
        font=("Arial", 10), padx=12, pady=7,
        cursor="hand2"
    )

def makeHeading(title, subtitle=""):
    tk.Label(content, text=title, font=("Arial", 21, "bold"),
             bg=BG, fg=TEXT).pack(anchor="w", padx=25, pady=(22, 3))
    tk.Label(content, text=subtitle, font=("Arial", 10),
             bg=BG, fg=GREY).pack(anchor="w", padx=25, pady=(0, 18))

def makeSection(parent, title):
    section = tk.LabelFrame(parent, text=title, bg=WHITE,
                            font=("Arial", 11, "bold"), padx=12, pady=12)
    section.pack(fill="both", expand=True, padx=25, pady=(0, 20))
    return section

# STUDENT TABLE
def createStudentTable(parent, records=None, height=12):
    if records is None:
        records = students

    columns = ("name", "code", "coursework", "exam", "overall", "percentage", "grade")
    headings = ("Student Name", "Student Code", "Coursework", "Exam",
                "Overall", "Percentage", "Grade")

    frame = tk.Frame(parent, bg=WHITE)
    frame.pack(fill="both", expand=True)

    table = ttk.Treeview(frame, columns=columns, show="headings", height=height)

    for col, heading in zip(columns, headings):
        table.heading(col, text=heading,
                      command=lambda c=col: sortColumn(table, c, False))
        table.column(col, anchor="center", width=110)

    table.column("name", width=180, anchor="w")

    scroll = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)

    table.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    for s in records:
        cw, total, pct, grade = getStudentResults(s)
        table.insert("", "end", values=(
            s["name"], s["code"], f"{cw}/60",
            f"{s['exam']}/100", f"{total}/160",
            f"{pct:.2f}%", grade
        ))

    return table

def sortColumn(table, col, reverse):
    data = [(table.set(item, col), item) for item in table.get_children("")]

    try:
        data.sort(key=lambda x: float(
            x[0].replace("%", "").split("/")[0]
        ), reverse=reverse)
    except ValueError:
        data.sort(key=lambda x: x[0].lower(), reverse=reverse)

    for index, (_, item) in enumerate(data):
        table.move(item, "", index)

    table.heading(col, command=lambda: sortColumn(table, col, not reverse))

# DASHBOARD
def showDashboard():
    clearContent()
    makeHeading("Dashboard", "Student performance overview")

    total = len(students)
    avg = sum(calculatePercentage(s) for s in students) / total if total else 0
    highest = max((calculateTotal(s)[1] for s in students), default=0)
    lowest = min((calculateTotal(s)[1] for s in students), default=0)

    stats = tk.Frame(content, bg=BG)
    stats.pack(fill="x", padx=25, pady=(0, 20))

    for title, value in [
        ("Total Students", total),
        ("Class Average", f"{avg:.2f}%"),
        ("Highest Mark", highest),
        ("Lowest Mark", lowest)
    ]:
        box = tk.LabelFrame(stats, text=title, bg=WHITE,
                            font=("Arial", 10), padx=15, pady=12)
        box.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(box, text=value, bg=WHITE, fg=BLUE,
                 font=("Arial", 19, "bold")).pack()

    section = makeSection(content, "Recent Student Records")

    if students:
        createStudentTable(section, students[-8:], 8)
    else:
        tk.Label(section, text="No student records available.",
                 bg=WHITE, fg=GREY).pack(pady=30)

def displayAllStudents():
    clearContent()
    makeHeading("All Students", "View all student records")

    section = makeSection(content, "Student Records")

    if students:
        createStudentTable(section, students)
        avg = sum(calculatePercentage(s) for s in students) / len(students)
        tk.Label(section, text=f"Class Size: {len(students)}    |    Average: {avg:.2f}%",
                 bg=WHITE, font=("Arial", 10, "bold")).pack(anchor="w", pady=10)
    else:
        tk.Label(section, text="No student records found.", bg=WHITE).pack(pady=30)

# SEARCH
def searchStudent():
    clearContent()
    makeHeading("Search Student", "Search by student name or code")

    section = makeSection(content, "Search")
    entry = tk.Entry(section, font=("Arial", 12))
    entry.pack(fill="x", pady=10)

    results = tk.Frame(section, bg=WHITE)
    results.pack(fill="both", expand=True)

    def perform():
        q = entry.get().strip().lower()

        for widget in results.winfo_children():
            widget.destroy()

        if not q:
            messagebox.showwarning("Search", "Enter a name or code.")
            return

        matches = [
            s for s in students
            if q in s["name"].lower() or q == s["code"]
        ]

        if matches:
            createStudentTable(results, matches, 8)
        else:
            tk.Label(results, text="No matching student found.",
                     bg=WHITE, fg=GREY).pack(pady=25)

    makeButton(section, "Search", perform).pack(anchor="w", pady=8)
    entry.bind("<Return>", lambda e: perform())

# HIGHEST / LOWEST
def showExtremeStudent(highest=True):
    clearContent()
    title = "Highest Mark" if highest else "Lowest Mark"
    makeHeading(title, "Student result")

    section = makeSection(content, "Student Details")

    if not students:
        tk.Label(section, text="No student records available.",
                 bg=WHITE).pack(pady=30)
        return

    student = (max if highest else min)(
        students, key=lambda s: calculateTotal(s)[1]
    )

    cw, total, pct, grade = getStudentResults(student)

    for label, value in [
        ("Name", student["name"]),
        ("Code", student["code"]),
        ("Coursework", f"{cw}/60"),
        ("Exam", f"{student['exam']}/100"),
        ("Overall", f"{total}/160"),
        ("Percentage", f"{pct:.2f}%"),
        ("Grade", grade)
    ]:
        tk.Label(section, text=f"{label}:  {value}",
                 bg=WHITE, font=("Arial", 11)).pack(anchor="w", pady=8)

# SORT
def sortStudents(descending=False):
    clearContent()
    makeHeading("Sorted Students", "Student records arranged by overall mark")

    section = makeSection(content, "Results")
    records = sorted(
        students,
        key=lambda s: calculateTotal(s)[1],
        reverse=descending
    )

    if records:
        createStudentTable(section, records)
    else:
        tk.Label(section, text="No student records available.",
                 bg=WHITE).pack(pady=30)

def showSortMenu():
    clearContent()
    makeHeading("Sort Students", "Choose sorting order")

    section = makeSection(content, "Options")
    makeButton(section, "Lowest to Highest",
               lambda: sortStudents(False)).pack(anchor="w", pady=8)
    makeButton(section, "Highest to Lowest",
               lambda: sortStudents(True)).pack(anchor="w", pady=8)

# ADD / UPDATE FORM
def createStudentForm(edit_student=None):
    editing = edit_student is not None

    win = tk.Toplevel(root)
    win.title("Update Student" if editing else "Add Student")
    win.geometry("420x570")
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="Student Details", bg=BG,
             font=("Arial", 18, "bold")).pack(pady=18)

    form = tk.Frame(win, bg=WHITE, padx=20, pady=15)
    form.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    fields = [
        ("Student Code", "code"),
        ("Student Name", "name"),
        ("Coursework 1 (0-20)", "coursework1"),
        ("Coursework 2 (0-20)", "coursework2"),
        ("Coursework 3 (0-20)", "coursework3"),
        ("Exam Mark (0-100)", "exam")
    ]

    entries = {}

    for label, key in fields:
        tk.Label(form, text=label, bg=WHITE,
                 font=("Arial", 10)).pack(anchor="w", pady=(7, 2))

        entry = tk.Entry(form, font=("Arial", 11))
        entry.pack(fill="x", ipady=4)
        entries[key] = entry

        if editing:
            entry.insert(0, str(edit_student[key]))
            if key == "code":
                entry.config(state="readonly")

    def submit():
        code = entries["code"].get().strip()
        name = entries["name"].get().strip()

        if not code.isdigit() or not 1000 <= int(code) <= 9999:
            messagebox.showerror("Error", "Code must be between 1000 and 9999.", parent=win)
            return

        if not name:
            messagebox.showerror("Error", "Enter a student name.", parent=win)
            return

        try:
            cw1 = int(entries["coursework1"].get())
            cw2 = int(entries["coursework2"].get())
            cw3 = int(entries["coursework3"].get())
            exam = int(entries["exam"].get())
        except ValueError:
            messagebox.showerror("Error", "Marks must be whole numbers.", parent=win)
            return

        if not all(0 <= m <= 20 for m in (cw1, cw2, cw3)):
            messagebox.showerror("Error", "Coursework marks must be 0-20.", parent=win)
            return

        if not 0 <= exam <= 100:
            messagebox.showerror("Error", "Exam mark must be 0-100.", parent=win)
            return

        if any(s["code"] == code and s is not edit_student for s in students):
            messagebox.showerror("Error", "Student code already exists.", parent=win)
            return

        new_student = {
            "code": code,
            "name": name,
            "coursework1": cw1,
            "coursework2": cw2,
            "coursework3": cw3,
            "exam": exam
        }

        if editing:
            original = edit_student.copy()
            edit_student.update(new_student)

            if not saveStudents():
                edit_student.update(original)
                return

        else:
            students.append(new_student)

            if not saveStudents():
                students.remove(new_student)
                return

        win.destroy()
        showDashboard()

    makeButton(form, "Save Student", submit).pack(fill="x", pady=18)

    if not editing:
        entries["code"].focus_set()

def addStudent():
    createStudentForm()

# DELETE
def deleteStudent():
    clearContent()
    makeHeading("Delete Student", "Remove a student record")

    section = makeSection(content, "Delete Record")

    tk.Label(section, text="Student Code:", bg=WHITE).pack(anchor="w")
    entry = tk.Entry(section, font=("Arial", 12))
    entry.pack(fill="x", pady=10)

    def remove():
        code = entry.get().strip()
        student = next((s for s in students if s["code"] == code), None)

        if student is None:
            messagebox.showerror("Error", "Student not found.")
            return

        if not messagebox.askyesno("Confirm", f"Delete {student['name']}?"):
            return

        position = students.index(student)
        students.remove(student)

        if saveStudents():
            showDashboard()
        else:
            students.insert(position, student)

    makeButton(section, "Delete Student", remove, "#C0392B").pack(anchor="w", pady=10)

# UPDATE
def updateStudent():
    clearContent()
    makeHeading("Update Student", "Find a student to edit")

    section = makeSection(content, "Find Student")

    entry = tk.Entry(section, font=("Arial", 12))
    entry.pack(fill="x", pady=10)

    def find():
        code = entry.get().strip()
        student = next((s for s in students if s["code"] == code), None)

        if student is None:
            messagebox.showerror("Error", "Student not found.")
        else:
            createStudentForm(student)

    makeButton(section, "Find Student", find).pack(anchor="w", pady=10)

# SIDEBAR
sidebar = tk.Frame(root, bg=WHITE, width=200)
sidebar.grid(row=0, column=0, sticky="ns")
sidebar.grid_propagate(False)

tk.Label(sidebar, text="Student Manager", bg=WHITE, fg=BLUE,
         font=("Arial", 16, "bold")).pack(pady=25)

def sidebarButton(text, command):
    tk.Button(
        sidebar, text=text, command=command,
        bg=WHITE, fg=TEXT, relief="flat",
        font=("Arial", 10), anchor="w",
        padx=20, pady=10, cursor="hand2"
    ).pack(fill="x", padx=8)

sidebarButton("Dashboard", showDashboard)
sidebarButton("View All Students", displayAllStudents)
sidebarButton("Search Student", searchStudent)
sidebarButton("Highest Mark", lambda: showExtremeStudent(True))
sidebarButton("Lowest Mark", lambda: showExtremeStudent(False))
sidebarButton("Sort Students", showSortMenu)

tk.Frame(sidebar, bg=BG, height=1).pack(fill="x", padx=15, pady=12)

sidebarButton("Add Student", addStudent)
sidebarButton("Update Student", updateStudent)
sidebarButton("Delete Student", deleteStudent)

# MAIN CONTENT
main_area = tk.Frame(root, bg=BG)
main_area.grid(row=0, column=1, sticky="nsew")
main_area.grid_columnconfigure(0, weight=1)
main_area.grid_rowconfigure(1, weight=1)

topbar = tk.Frame(main_area, bg=WHITE, height=50)
topbar.grid(row=0, column=0, sticky="ew")
topbar.grid_propagate(False)

tk.Label(topbar, text="Student Records System",
         bg=WHITE, font=("Arial", 11, "bold")).pack(side="left", padx=20)

makeButton(topbar, "Refresh", showDashboard).pack(side="right", padx=15, pady=7)

content = tk.Frame(main_area, bg=BG)
content.grid(row=1, column=0, sticky="nsew")

# START
loadStudents()
showDashboard()
root.mainloop()
