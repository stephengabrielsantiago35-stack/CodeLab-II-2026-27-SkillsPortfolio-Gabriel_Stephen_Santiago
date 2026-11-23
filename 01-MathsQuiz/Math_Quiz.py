
import tkinter as tk
from tkinter import messagebox
import random

# -----------------------------
# SETTINGS
# -----------------------------

BG = "#F4F4F4"
WHITE = "#FFFFFF"
BLUE = "#2878D0"
TEXT = "#222222"
GREY = "#777777"

score = 0
question_number = 1
first_attempt = True

min_value = 1
max_value = 9

correct_answer = 0
current_level = ""

# -----------------------------
# MAIN WINDOW
# -----------------------------

root = tk.Tk()
root.title("Maths Quiz")
root.geometry("600x500")
root.configure(bg=BG)
root.resizable(False, False)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def show_frame(frame):
    menu_frame.pack_forget()
    quiz_frame.pack_forget()
    result_frame.pack_forget()
    frame.pack(fill="both", expand=True)


def make_label(parent, text, size=14, bold=False, color=TEXT):
    return tk.Label(
        parent,
        text=text,
        font=("Arial", size, "bold" if bold else "normal"),
        bg=parent["bg"],
        fg=color
    )


def make_button(parent, text, command):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 12),
        bg=BLUE,
        fg=WHITE,
        activebackground="#1B65B0",
        activeforeground=WHITE,
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2"
    )


# -----------------------------
# MENU
# -----------------------------

menu_frame = tk.Frame(root, bg=BG)

make_label(
    menu_frame, "Maths Quiz", 28, True
).pack(pady=(65, 10))

make_label(
    menu_frame, "Choose your difficulty level", 14,
    color=GREY
).pack(pady=10)


def start_quiz(level):

    global score, question_number
    global min_value, max_value, current_level

    score = 0
    question_number = 1
    current_level = level

    if level == "Easy":
        min_value, max_value = 1, 9

    elif level == "Moderate":
        min_value, max_value = 10, 99

    else:
        min_value, max_value = 1000, 9999

    level_label.config(text=level)
    show_frame(quiz_frame)
    display_question()


for level in ["Easy", "Moderate", "Advanced"]:
    make_button(
        menu_frame,
        level,
        lambda l=level: start_quiz(l)
    ).pack(pady=8)


make_label(
    menu_frame,
    "10 Questions | Maximum Score: 100",
    11,
    color=GREY
).pack(pady=30)


# -----------------------------
# QUIZ SCREEN
# -----------------------------

quiz_frame = tk.Frame(root, bg=BG)

make_label(
    quiz_frame, "Maths Quiz", 24, True
).pack(pady=(35, 5))

level_label = make_label(
    quiz_frame, "", 12, color=GREY
)
level_label.pack()

progress_label = make_label(
    quiz_frame, "", 12
)
progress_label.pack(pady=(25, 5))

score_label = make_label(
    quiz_frame, "Score: 0", 12
)
score_label.pack(pady=5)

question_label = make_label(
    quiz_frame, "", 32, True
)
question_label.pack(pady=35)

answer_entry = tk.Entry(
    quiz_frame,
    font=("Arial", 16),
    justify="center",
    width=15
)
answer_entry.pack(pady=5)

feedback_label = make_label(
    quiz_frame, "Enter your answer", 12,
    color=GREY
)
feedback_label.pack(pady=15)


# -----------------------------
# DISPLAY QUESTION
# -----------------------------

def display_question():

    global num1, num2, operation
    global correct_answer, first_attempt

    num1 = random.randint(min_value, max_value)
    num2 = random.randint(min_value, max_value)

    operation = random.choice(["+", "-"])

    if operation == "+":
        correct_answer = num1 + num2
    else:
        correct_answer = num1 - num2

    first_attempt = True

    question_label.config(
        text=f"{num1} {operation} {num2} = ?"
    )

    progress_label.config(
        text=f"Question {question_number} of 10"
    )

    score_label.config(
        text=f"Score: {score}"
    )

    feedback_label.config(
        text="Enter your answer",
        fg=GREY
    )

    answer_entry.config(state="normal")
    answer_entry.delete(0, tk.END)

    submit_button.config(
        text="Submit",
        command=submit_answer,
        state="normal"
    )

    answer_entry.focus_set()


# -----------------------------
# CHECK ANSWER
# -----------------------------

def submit_answer():

    global score, first_attempt

    try:
        user_answer = int(answer_entry.get())

    except ValueError:
        feedback_label.config(
            text="Please enter a valid number.",
            fg="red"
        )
        return

    if user_answer == correct_answer:

        if first_attempt:
            score += 10
            feedback = "Correct! +10 points"
        else:
            score += 5
            feedback = "Correct! +5 points"

        feedback_label.config(
            text=feedback,
            fg="green"
        )

        answer_entry.config(state="disabled")

        submit_button.config(
            text="Next Question",
            command=next_question
        )

        score_label.config(
            text=f"Score: {score}"
        )

    else:

        if first_attempt:

            first_attempt = False

            feedback_label.config(
                text="Incorrect! Try again.",
                fg="red"
            )

            answer_entry.delete(0, tk.END)
            answer_entry.focus_set()

        else:

            feedback_label.config(
                text=f"Incorrect! Answer: {correct_answer}",
                fg="red"
            )

            answer_entry.config(state="disabled")

            submit_button.config(
                text="Next Question",
                command=next_question
            )


submit_button = make_button(
    quiz_frame, "Submit", submit_answer
)
submit_button.pack(pady=10)


# -----------------------------
# NEXT QUESTION
# -----------------------------

def next_question():

    global question_number

    if question_number < 10:
        question_number += 1
        display_question()

    else:
        display_results()


# -----------------------------
# RESULTS SCREEN
# -----------------------------

result_frame = tk.Frame(root, bg=BG)

make_label(
    result_frame, "Quiz Complete!", 27, True
).pack(pady=(65, 20))

result_score = make_label(
    result_frame, "", 24, True
)
result_score.pack(pady=10)

result_grade = make_label(
    result_frame, "", 18, True
)
result_grade.pack(pady=10)

result_message = make_label(
    result_frame, "", 13, color=GREY
)
result_message.pack(pady=10)


def display_results():

    if score > 90:
        grade, performance = "A+", "Outstanding performance!"

    elif score >= 80:
        grade, performance = "A", "Excellent work!"

    elif score >= 70:
        grade, performance = "B", "Great effort!"

    elif score >= 60:
        grade, performance = "C", "Good job!"

    elif score >= 50:
        grade, performance = "D", "Keep practising!"

    else:
        grade, performance = "F", "Keep learning!"

    result_score.config(
        text=f"Score: {score}/100"
    )

    result_grade.config(
        text=f"Grade: {grade}"
    )

    result_message.config(
        text=performance
    )

    show_frame(result_frame)


# -----------------------------
# RESTART AND EXIT
# -----------------------------

def play_again():
    show_frame(menu_frame)


def exit_quiz():
    root.destroy()


make_button(
    result_frame, "Play Again", play_again
).pack(pady=10)

make_button(
    result_frame, "Exit", exit_quiz
).pack(pady=5)


# -----------------------------
# KEYBOARD SUPPORT
# -----------------------------

root.bind(
    "<Return>",
    lambda event: submit_button.invoke()
)

# -----------------------------
# RUN APPLICATION
# -----------------------------

show_frame(menu_frame)

root.mainloop()
