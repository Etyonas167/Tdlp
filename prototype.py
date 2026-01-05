import customtkinter as ctk
from datetime import datetime, timedelta

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class TodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tegbar List")
        self.geometry("1100x650")
        self.resizable(True, True)

        # ===== DATA =====
        self.selected_date = datetime.now().date()
        self.tasks_by_date = {}
        self.day_buttons = {}

        # ================= SIDEBAR =================
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=20)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(
            self.sidebar,
            text="☑ Tegbar\nList",
            font=("Arial", 22, "bold")
        ).pack(pady=30)

        for text, page in [("Tasks", "tasks"), ("Team", "team"), ("Tegbar AI", "ai"),
                           ("Settings", "settings"), ("History", "history")]:
            ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                command=lambda p=page: self.show_page(p)
            ).pack(fill="x", padx=20, pady=5)

        # ================= MAIN CONTAINER =================
        self.container = ctk.CTkFrame(self, corner_radius=20)
        self.container.pack(expand=True, fill="both", padx=10, pady=10)

        # ===== PAGES =====
        self.pages = {}
        self.pages["tasks"] = self.create_tasks_page()
        self.pages["team"] = self.create_team_page()
        self.pages["ai"] = self.create_simple_page("Tegbar AI", "AI assistant coming soon 🤖")
        self.pages["settings"] = self.create_simple_page("Settings", "Settings panel")
        self.pages["history"] = self.create_simple_page("History", "Completed tasks history")

        for page in self.pages.values():
            page.place(relwidth=1, relheight=1)

        self.show_page("tasks")

    # ================= SIDEBAR PAGE SWITCH =================
    def show_page(self, name):
        self.pages[name].tkraise()

    # ================= TASK PAGE =================
    def create_tasks_page(self):
        page = ctk.CTkFrame(self.container)

        ctk.CTkLabel(page, text="Tasks", font=("Arial", 26, "bold"))\
            .pack(anchor="w", padx=20, pady=10)

        # ===== DATE SELECTOR =====
        self.days_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.days_frame.pack(fill="x", padx=20)
        self.draw_days()

        # ===== TASK FRAME =====
        self.task_frame = ctk.CTkFrame(page, corner_radius=20)
        self.task_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.draw_tasks()

        # ===== ADD TASK BUTTON =====
        ctk.CTkButton(
            page, text="+", font=("Arial", 30),
            width=60, height=60, corner_radius=30,
            command=self.open_add_task
        ).place(relx=0.5, rely=0.93, anchor="center")

        return page

    # ================= DATE BUTTONS =================
    def draw_days(self):
        for w in self.days_frame.winfo_children():
            w.destroy()
        self.day_buttons.clear()
        today = datetime.now().date()

        for i in range(7):
            date = today + timedelta(days=i)
            btn = ctk.CTkButton(
                self.days_frame,
                text=f"{date.strftime('%a')}\n{date.strftime('%d')}",
                width=70, height=55, corner_radius=12,
                command=lambda d=date: self.select_date(d)
            )
            btn.pack(side="left", padx=5)
            self.day_buttons[date] = btn

        self.highlight_selected_day()

    def select_date(self, date):
        self.selected_date = date
        self.highlight_selected_day()
        self.draw_tasks()

    def highlight_selected_day(self):
        for d, btn in self.day_buttons.items():
            if d == self.selected_date:
                btn.configure(fg_color="#2563eb", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="black")

    # ================= TASK LIST =================
    def draw_tasks(self):
        for w in self.task_frame.winfo_children():
            w.destroy()

        tasks = self.tasks_by_date.get(self.selected_date, [])

        if not tasks:
            ctk.CTkLabel(
                self.task_frame,
                text="No tasks yet.\nClick + to add one.",
                text_color="gray",
                font=("Arial", 16)
            ).pack(expand=True)
            return

        for index, (text, time, done) in enumerate(tasks):
            task_btn = ctk.CTkButton(
                self.task_frame,
                text=f"{text}  ⏰ {time}",
                anchor="w",
                height=50,
                fg_color="#260a0a" if not done else "#038635",
                hover_color="#676262",
                command=lambda i=index: self.toggle_done(i)
            )
            task_btn.pack(fill="x", padx=15, pady=5, side="top")

            # Edit/Delete buttons
            btn_frame = ctk.CTkFrame(task_btn, fg_color="transparent")
            btn_frame.place(relx=1, rely=0.5, anchor="e")

            ctk.CTkButton(btn_frame, text="✏️", width=35,
                           command=lambda i=index: self.edit_task(i)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="🗑️", width=35,
                           command=lambda i=index: self.delete_task(i)).pack(side="left", padx=5)

    def toggle_done(self, index):
        text, time, done = self.tasks_by_date[self.selected_date][index]
        self.tasks_by_date[self.selected_date][index] = (text, time, not done)
        self.draw_tasks()

    # ================= ADD / EDIT / DELETE =================
    def open_add_task(self, edit_index=None):
        self.edit_index = edit_index

        self.popup = ctk.CTkToplevel(self)
        self.popup.geometry("350x200")
        self.popup.grab_set()

        ctk.CTkLabel(
            self.popup,
            text="Edit Task" if edit_index is not None else "New Task",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        self.task_input = ctk.CTkEntry(self.popup)
        self.task_input.pack(fill="x", padx=20, pady=10)

        if edit_index is not None:
            self.task_input.insert(
                0, self.tasks_by_date[self.selected_date][edit_index][0]
            )

        ctk.CTkButton(self.popup, text="Save", command=self.save_task).pack(pady=20)

    def save_task(self):
        text = self.task_input.get().strip()
        if not text:
            return

        if self.edit_index is None:
            self.tasks_by_date.setdefault(self.selected_date, []).append(
                (text, datetime.now().strftime("%I:%M %p"), False)
            )
        else:
            self.tasks_by_date[self.selected_date][self.edit_index] = (
                text,
                self.tasks_by_date[self.selected_date][self.edit_index][1],
                False
            )

        self.popup.destroy()
        self.draw_tasks()

    def edit_task(self, index):
        self.open_add_task(index)

    def delete_task(self, index):
        del self.tasks_by_date[self.selected_date][index]
        self.draw_tasks()

    # ================= OTHER PAGES =================
    def create_team_page(self):
        page = ctk.CTkFrame(self.container)
        ctk.CTkLabel(page, text="Team Chat", font=("Arial", 24, "bold")).pack(pady=20)
        return page

    def create_simple_page(self, title, text):
        page = ctk.CTkFrame(self.container)
        ctk.CTkLabel(page, text=title, font=("Arial", 26, "bold")).pack(pady=30)
        ctk.CTkLabel(page, text=text, font=("Arial", 16)).pack()
        return page


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
