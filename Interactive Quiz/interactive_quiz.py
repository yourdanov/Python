import tkinter as tk
import random

# Sample questions for the quiz (total 103 questions)
questions = [
    {"question": "Какъв е резултатът от 3 + 5?", "options": ["5", "8", "10", "15"], "answer": "8"},
    {"question": "Коя е правилната синтаксиса за дефиниране на функция в Python?", "options": ["function myFunc()", "def myFunc()", "fn myFunc()", "lambda myFunc()"], "answer": "def myFunc()"},
    {"question": "Какъв тип данни е резултатът от 5 / 2 в Python 3?", "options": ["int", "float", "str", "bool"], "answer": "float"},
    {"question": "Кой от следните оператори е за сравнение?", "options": ["=", "==", "+", "*"], "answer": "=="},
    {"question": "Каква е стойността на 2 ** 3 в Python?", "options": ["5", "6", "8", "9"], "answer": "8"},
    {"question": "Какъв тип данни е 'Hello World'?", "options": ["int", "str", "bool", "list"], "answer": "str"},
    {"question": "Коя функция се използва за извеждане на резултат на екрана в Python?", "options": ["print()", "input()", "output()", "echo()"], "answer": "print()"},
    {"question": "Каква е стойността на 10 % 3?", "options": ["1", "2", "3", "0"], "answer": "1"},
    {"question": "Кой от следните е неизменяем тип данни?", "options": ["list", "dict", "tuple", "set"], "answer": "tuple"},
    {"question": "Как се нарича грешка, която се появява по време на изпълнение на програмата?", "options": ["SyntaxError", "RuntimeError", "IndexError", "ValueError"], "answer": "RuntimeError"},
    # Additional questions...
    {"question": "Коя библиотека в Python се използва за научни изчисления?", "options": ["numpy", "requests", "flask", "tkinter"], "answer": "numpy"},
    {"question": "Каква е стойността на 7 // 2 в Python?", "options": ["3.5", "3", "2", "4"], "answer": "3"},
    {"question": "Каква е функцията на 'len()' в Python?", "options": ["Изчислява дължината на обект", "Добавя елемент в списък", "Извежда резултат на екрана", "Прекратява програма"], "answer": "Изчислява дължината на обект"},
    {"question": "Как се дефинира празен речник в Python?", "options": ["[]", "{}", "()", "None"], "answer": "{}"},
    {"question": "Коя ключова дума се използва за цикъл в Python?", "options": ["for", "while", "loop", "repeat"], "answer": "for"},
    {"question": "Какво е 'lambda' в Python?", "options": ["Функция без име", "Масив", "Ключова дума за цикъл", "Тип данни"], "answer": "Функция без име"},
    {"question": "Какъв е резултатът от 'not True'?", "options": ["True", "False", "None", "0"], "answer": "False"},
    {"question": "Как се добавя елемент към списък?", "options": ["append()", "add()", "insert()", "push()"], "answer": "append()"},
    {"question": "Каква е целта на 'break' в Python?", "options": ["Прекратява цикъл", "Прекратява функция", "Добавя елемент", "Стартира програма"], "answer": "Прекратява цикъл"},
]

# Randomly select 10 questions for the quiz
questions = random.sample(questions, 10)

class ProgrammingQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Интерактивен Тест по Програмиране")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")

        self.question_index = 0
        self.score = 0

        # Question label
        self.question_label = tk.Label(root, text="", wraplength=500, font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#333")
        self.question_label.pack(pady=20)

        # Option buttons
        self.options_frame = tk.Frame(root, bg="#f0f0f0")
        self.options_frame.pack(pady=10)
        self.options = []
        for i in range(4):
            btn = tk.Button(self.options_frame, text="", width=50, font=("Arial", 12), command=lambda i=i: self.check_answer(i), relief="groove", bg="#ffffff", fg="#333", activebackground="#cce7ff")
            btn.pack(pady=5)
            self.options.append(btn)

        # Feedback label
        self.feedback_label = tk.Label(root, text="", font=("Arial", 14), bg="#f0f0f0", fg="#333")
        self.feedback_label.pack(pady=10)

        # Score label
        self.score_label = tk.Label(root, text="Резултат: 0", font=("Arial", 14, "bold"), bg="#f0f0f0", fg="#333")
        self.score_label.pack(pady=10)

        # Buttons for new test and exit
        self.buttons_frame = tk.Frame(root, bg="#f0f0f0")
        self.buttons_frame.pack(pady=20)
        self.new_test_button = tk.Button(self.buttons_frame, text="Нов Тест", command=self.start_new_test, font=("Arial", 12), bg="#4CAF50", fg="#fff", width=15)
        self.new_test_button.pack(side="left", padx=10)
        self.exit_button = tk.Button(self.buttons_frame, text="Изход", command=root.quit, font=("Arial", 12), bg="#f44336", fg="#fff", width=15)
        self.exit_button.pack(side="left", padx=10)
        self.new_test_button.pack_forget()
        self.exit_button.pack_forget()

        # Load first question
        self.load_question()

    def load_question(self):
        self.feedback_label.config(text="")
        if self.question_index < len(questions):
            question_data = questions[self.question_index]
            self.question_label.config(text=question_data["question"])
            for i, option in enumerate(question_data["options"]):
                self.options[i].config(text=option)
        else:
            self.feedback_label.config(text=f"Тестът приключи! Вашият резултат е: {self.score}/{len(questions)}", fg="blue")
            for btn in self.options:
                btn.config(state="disabled")
            self.new_test_button.pack(side="left", padx=10)
            self.exit_button.pack(side="left", padx=10)

    def check_answer(self, selected_index):
        question_data = questions[self.question_index]
        selected_option = question_data["options"][selected_index]
        if selected_option == question_data["answer"]:
            self.score += 1
            self.feedback_label.config(text="Правилен отговор!", fg="green")
        else:
            self.feedback_label.config(text=f"Грешен отговор! Правилният отговор е: {question_data['answer']}", fg="red")
        
        self.question_index += 1
        self.score_label.config(text=f"Резултат: {self.score}")
        self.root.after(2000, self.load_question)

    def start_new_test(self):
        global questions
        questions = random.sample(questions, 10)
        self.question_index = 0
        self.score = 0
        self.score_label.config(text="Резултат: 0")
        for btn in self.options:
            btn.config(state="normal")
        self.new_test_button.pack_forget()
        self.exit_button.pack_forget()
        self.load_question()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProgrammingQuizApp(root)
    root.mainloop()
