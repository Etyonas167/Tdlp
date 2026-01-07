import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time
import customtkinter as ctk


import tkinter.messagebox as msg

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class TodoApp(ctk.CTk):
    STORAGE = Path.home() / ".tegbar_tasks.json"
    TEAM_STORAGE = Path.home() / ".tegbar_team.json"

    def __init__(self):
        super().__init__()
        self.title("Tegbar List — Premium")
        self.geometry("1100x650")
        self.minsize(900, 600)

        # data
        self.week_offset = 0  # offset in days from today for week display
        self.selected_date = datetime.now().date()
        self.tasks_by_date = {}  # { "YYYY-MM-DD": [ {text, time, priority, done, notes, created} ] }
        self.day_buttons = {}
        self.edit_index = None
        self.search_query = ctk.StringVar()

        self.load_tasks()
        # load team chat data
        self.load_team_messages()

        # layout
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=12)
        self.sidebar.pack(side="left", fill="y", padx=12, pady=12)

        ctk.CTkLabel(self.sidebar, text="☑ Tegbar\nList", font=("Arial", 20, "bold")).pack(pady=(18, 12))

        for text, page in [("Tasks", "tasks"), ("Team", "team"), ("Tegbar AI", "ai"),
                           ("Settings", "settings"), ("History", "history")]:
            btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", fg_color="transparent",
                                command=lambda p=page: self.show_page(p))
            btn.pack(fill="x", padx=12, pady=6)

        self.container = ctk.CTkFrame(self, corner_radius=12)
        self.container.pack(expand=True, fill="both", padx=12, pady=12)

        self.pages = {}
        self.pages["tasks"] = self.create_tasks_page()
        self.pages["team"] = self.create_team_page()
        self.pages["ai"] = self.create_ai_page()
        self.pages["settings"] = self.create_settings_page()
        self.pages["history"] = self.create_history_page()

        for page in self.pages.values():
            page.place(relwidth=1, relheight=1)

        self.show_page("tasks")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- persistence ----------
    def load_tasks(self):
        if self.STORAGE.exists():
            try:
                data = json.loads(self.STORAGE.read_text(encoding="utf-8"))
                # validate/normalize
                self.tasks_by_date = {}
                for date_str, tasks in data.items():
                    normalized = []
                    for t in tasks:
                        normalized.append({
                            "text": t.get("text", ""),
                            "time": t.get("time", ""),
                            "priority": t.get("priority", "Normal"),
                            "done": bool(t.get("done", False)),
                            "notes": t.get("notes", ""),
                            "created": t.get("created", datetime.now().isoformat())
                        })
                    self.tasks_by_date[date_str] = normalized
            except Exception:
                self.tasks_by_date = {}
        else:
            self.tasks_by_date = {}

    def save_tasks(self):
        try:
            self.STORAGE.write_text(json.dumps(self.tasks_by_date, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            msg.showerror("Save Error", f"Could not save tasks: {e}")

    def load_team_messages(self):
        try:
            if self.TEAM_STORAGE.exists():
                data = json.loads(self.TEAM_STORAGE.read_text(encoding="utf-8"))
                # ensure structure
                self.team_messages = {k: v if isinstance(v, list) else [] for k, v in data.items()}
            else:
                # seed example contacts
                self.team_messages = {
                    "Jonas": [{"sender":"Jonas","text":"Hello team!","time":"09:12"}],
                    "Neo": [], "Abraham": [], "Jessica": []
                }
        except Exception:
            self.team_messages = {}

    def save_team_messages(self):
        try:
            self.TEAM_STORAGE.write_text(json.dumps(self.team_messages, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    # ---------- UI navigation ----------
    def show_page(self, name):
        self.pages[name].tkraise()
        if name == "tasks":
            self.draw_days()
            self.draw_tasks()
        elif name == "history":
            # refresh history stats when showing the page
            self.draw_history()

    # ---------- tasks page ----------
    def create_tasks_page(self):
        page = ctk.CTkFrame(self.container)

        header = ctk.CTkFrame(page, fg_color="transparent", width=18)
        header.pack(fill="x", padx=18, pady=(12, 6))

        ctk.CTkLabel(header, text="Tasks", font=("Arial", 26, "bold")).pack(side="left", anchor="w")

        # search bar
        search_entry = ctk.CTkEntry(header, width=260, placeholder_text="Search tasks...", textvariable=self.search_query)
        search_entry.pack(side="right", padx=(6, 0))
        search_entry.bind("<KeyRelease>", lambda e: self.draw_tasks())

        # week navigation
        nav = ctk.CTkFrame(page, fg_color="transparent")
        nav.pack(fill="x", padx=15, pady=(1, 4))

        ctk.CTkButton(nav, text="◀", width=40, command=self.prev_week).pack(side="left", padx=4)
        ctk.CTkButton(nav, text="▶", width=40, command=self.next_week).pack(side="left", padx=370)

        self.days_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.days_frame.pack(fill="x", padx=18, pady=(6, 12))
        self.draw_days()

        # main task area
        body = ctk.CTkFrame(page, corner_radius=12, width=10)
        body.pack(expand=True, fill="both", padx=18, pady=12)

        # left: tasks list
        self.task_frame = ctk.CTkFrame(body, corner_radius=8)
        self.task_frame.pack(side="left", expand=True, fill="both", padx=(12, 8), pady=12)

        # right: details / quick actions
        right = ctk.CTkFrame(body, width=30, corner_radius=8)
        right.pack(side="right", fill="y", padx=(8, 12), pady=12)

        # quick add
        ctk.CTkLabel(right, text="Quick Add", font=("Arial", 14, "bold")).pack(pady=(12, 6))
        self.quick_text = ctk.CTkEntry(right, placeholder_text="Task title")
        self.quick_text.pack(fill="x", padx=12, pady=6)
        self.quick_time = ctk.CTkEntry(right, placeholder_text="Time (e.g. 02:30 PM)")
        self.quick_time.pack(fill="x", padx=12, pady=6)
        self.quick_priority = ctk.CTkOptionMenu(right, values=["Low", "Normal", "High"], width=120)
        self.quick_priority.set("Normal")
        self.quick_priority.pack(padx=12, pady=6, anchor="w")
        ctk.CTkButton(right, text="Add", command=self.quick_add).pack(padx=2, pady=(6, 12))

        # Export / import
        ctk.CTkLabel(right, text="Export / Import", font=("Arial", 12, "bold")).pack(pady=(6, 6))
        ctk.CTkButton(right, text="Export JSON", command=self.export_json).pack(padx=12, pady=6)
        ctk.CTkButton(right, text="Clear Completed", command=self.clear_completed).pack(padx=12, pady=6)

        # floating add button
        ctk.CTkButton(page, text="+", font=("Arial", 26), width=64, height=64, corner_radius=32,
                      command=lambda: self.open_add_task()).place(relx=0.4, rely=0.88, anchor="center")

        self.draw_tasks()
        return page

    def draw_days(self):
        for w in self.days_frame.winfo_children():
            w.destroy()
        self.day_buttons.clear()
        start = (datetime.now().date() + timedelta(days=self.week_offset))
        # show 7-day week starting from start
        for i in range(7):
            date = start + timedelta(days=i)
            text = f"{date.strftime('%a')}\n{date.strftime('%d %b')}"
            btn = ctk.CTkButton(self.days_frame, text=text, width=86, height=56, corner_radius=10,
                                command=lambda d=date: self.select_date(d))
            btn.pack(side="left", padx=6, pady=4)
            self.day_buttons[date] = btn
        self.highlight_selected_day()

    def prev_week(self):
        self.week_offset -= 7
        self.draw_days()

    def next_week(self):
        self.week_offset += 7
        self.draw_days()

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

    def draw_tasks(self):
        for w in self.task_frame.winfo_children():
            w.destroy()

        date_key = self.selected_date.isoformat()
        tasks = list(self.tasks_by_date.get(date_key, []))
        query = self.search_query.get().strip().lower()
        if query:
            tasks = [t for t in tasks if query in t["text"].lower() or query in t.get("notes", "").lower()]

        if not tasks:
            ctk.CTkLabel(self.task_frame, text="No tasks for this day.\nClick + to add one.",
                         text_color="gray", font=("Arial", 14)).pack(expand=True)
            return

        for index, task in enumerate(tasks):
            txt = task["text"]
            time = f" ⏰ {task['time']}" if task.get("time") else ""
            display = f"{txt}{time}"
            color = {"High": "#ff6363", "Normal": "#1f6feb", "Low": "#8ea28e"}.get(task.get("priority"), "#1f6feb")
            fg = "#065f46" if task.get("done") else color

            frame = ctk.CTkFrame(self.task_frame, corner_radius=8)
            frame.pack(fill="x", padx=12, pady=8)

            left = ctk.CTkFrame(frame, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
            title = ctk.CTkLabel(left, text=display, anchor="w", font=("Arial", 13, "bold"))
            title.pack(fill="x")
            notes = task.get("notes", "")
            if notes:
                ctk.CTkLabel(left, text=notes if len(notes) < 120 else notes[:117] + "...", anchor="w",
                             text_color="gray").pack(fill="x", pady=(4, 0))

            right = ctk.CTkFrame(frame, width=120, fg_color="transparent")
            right.pack(side="right", padx=8, pady=8)

            done_btn = ctk.CTkButton(right, text="✔" if task.get("done") else "○", width=36, command=lambda i=index: self.toggle_done_by_list(i, tasks))
            done_btn.pack(side="left", padx=6)

            ctk.CTkButton(right, text="✏️", width=36, command=lambda i=index: self.edit_task_by_list(i, tasks)).pack(side="left", padx=6)
            ctk.CTkButton(right, text="🗑️", width=36, command=lambda i=index: self.delete_task_by_list(i, tasks)).pack(side="left", padx=6)

            # priority badge
            ctk.CTkLabel(frame, text=task.get("priority", "Normal"), width=80, anchor="center",
                         fg_color=color, corner_radius=10, text_color="white").place(relx=0.6, rely=0.5, anchor="w")

    # helpers for list-based index (because filtered list is used)
    def toggle_done_by_list(self, list_index, visible_tasks):
        # map to actual date list index
        date_key = self.selected_date.isoformat()
        actual_tasks = self.tasks_by_date.get(date_key, [])
        task_to_toggle = visible_tasks[list_index]
        for idx, t in enumerate(actual_tasks):
            if t is task_to_toggle or (t["text"] == task_to_toggle["text"] and t["created"] == task_to_toggle["created"]):
                actual_tasks[idx]["done"] = not actual_tasks[idx].get("done", False)
                break
        self.save_tasks()
        self.draw_tasks()

    def edit_task_by_list(self, list_index, visible_tasks):
        task = visible_tasks[list_index]
        # find actual index
        date_key = self.selected_date.isoformat()
        actual_tasks = self.tasks_by_date.get(date_key, [])
        idx = next((i for i, t in enumerate(actual_tasks) if t["created"] == task["created"]), None)
        if idx is not None:
            self.open_add_task(edit_index=idx)

    def delete_task_by_list(self, list_index, visible_tasks):
        task = visible_tasks[list_index]
        date_key = self.selected_date.isoformat()
        actual_tasks = self.tasks_by_date.get(date_key, [])
        idx = next((i for i, t in enumerate(actual_tasks) if t["created"] == task["created"]), None)
        if idx is not None:
            self.delete_task(idx)

    # add / edit / delete
    def open_add_task(self, edit_index=None):
        self.edit_index = edit_index
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Edit Task" if edit_index is not None else "New Task")
        self.popup.geometry("420x490")
        self.popup.transient(self)
        self.popup.grab_set()

        ctk.CTkLabel(self.popup, text="Title", font=("Arial", 12)).pack(pady=(12, 4), anchor="w", padx=12)
        self.task_input = ctk.CTkEntry(self.popup)
        self.task_input.pack(fill="x", padx=12)

        ctk.CTkLabel(self.popup, text="Time", font=("Arial", 12)).pack(pady=(8, 4), anchor="w", padx=12)
        self.time_input = ctk.CTkEntry(self.popup, placeholder_text="e.g. 03:30 PM")
        self.time_input.pack(fill="x", padx=12)

        ctk.CTkLabel(self.popup, text="Priority", font=("Arial", 12)).pack(pady=(8, 4), anchor="w", padx=12)
        self.priority_input = ctk.CTkOptionMenu(self.popup, values=["Low", "Normal", "High"])
        self.priority_input.pack(padx=12, pady=(0, 8), anchor="w")
        self.priority_input.set("Normal")

        ctk.CTkLabel(self.popup, text="Notes", font=("Arial", 12)).pack(pady=(8, 4), anchor="w", padx=12)
        self.notes_input = ctk.CTkTextbox(self.popup, height=80)
        self.notes_input.pack(fill="both", padx=12, pady=(0, 8), expand=True)

        btn_frame = ctk.CTkFrame(self.popup, fg_color="transparent")
        btn_frame.pack(pady=18)
        ctk.CTkButton(btn_frame, text="Save", command=self.save_task).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.popup.destroy).pack(side="left", padx=8)

        # populate if editing
        if edit_index is not None:
            date_key = self.selected_date.isoformat()
            task = self.tasks_by_date.get(date_key, [])[edit_index]
            if task:
                self.task_input.insert(0, task.get("text", ""))
                self.time_input.insert(0, task.get("time", ""))
                self.priority_input.set(task.get("priority", "Normal"))
                self.notes_input.insert("0.0", task.get("notes", ""))

    def save_task(self):
        text = self.task_input.get().strip()
        time_txt = self.time_input.get().strip()
        priority = self.priority_input.get()
        notes = self.notes_input.get("0.0", "end").strip()
        if not text:
            msg.showwarning("Validation", "Task title cannot be empty.")
            return

        date_key = self.selected_date.isoformat()
        self.tasks_by_date.setdefault(date_key, [])
        if self.edit_index is None:
            self.tasks_by_date[date_key].append({
                "text": text,
                "time": time_txt,
                "priority": priority,
                "done": False,
                "notes": notes,
                "created": datetime.now().isoformat()
            })
        else:
            t = self.tasks_by_date[date_key][self.edit_index]
            t.update({
                "text": text,
                "time": time_txt,
                "priority": priority,
                "notes": notes,
            })
        self.save_tasks()
        self.popup.destroy()
        self.draw_tasks()

    def delete_task(self, index):
        date_key = self.selected_date.isoformat()
        if not (date_key in self.tasks_by_date and 0 <= index < len(self.tasks_by_date[date_key])):
            return
        if msg.askyesno("Delete", "Are you sure you want to delete this task?"):
            del self.tasks_by_date[date_key][index]
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
            self.save_tasks()
            self.draw_tasks()

    def quick_add(self):
        text = self.quick_text.get().strip()
        if not text:
            return
        time_txt = self.quick_time.get().strip()
        priority = self.quick_priority.get()
        date_key = self.selected_date.isoformat()
        self.tasks_by_date.setdefault(date_key, []).append({
            "text": text,
            "time": time_txt,
            "priority": priority,
            "done": False,
            "notes": "",
            "created": datetime.now().isoformat()
        })
        self.quick_text.delete(0, "end")
        self.quick_time.delete(0, "end")
        self.quick_priority.set("Normal")
        self.save_tasks()
        self.draw_tasks()

    def clear_completed(self):
        changed = False
        for date_key in list(self.tasks_by_date.keys()):
            before = len(self.tasks_by_date[date_key])
            self.tasks_by_date[date_key] = [t for t in self.tasks_by_date[date_key] if not t.get("done")]
            if not self.tasks_by_date[date_key]:
                del self.tasks_by_date[date_key]
            if len(self.tasks_by_date.get(date_key, [])) != before:
                changed = True
        if changed:
            self.save_tasks()
            self.draw_tasks()
            msg.showinfo("Cleared", "Completed tasks removed.")
        else:
            msg.showinfo("Nothing to clear", "No completed tasks found.")

    def export_json(self):
        try:
            dest = Path.cwd() / f"tegbar_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            dest.write_text(json.dumps(self.tasks_by_date, indent=2, ensure_ascii=False), encoding="utf-8")
            msg.showinfo("Exported", f"Exported tasks to {dest}")
        except Exception as e:
            msg.showerror("Export Error", str(e))

    # ---------- other pages ----------
    def create_team_page(self):
        page = ctk.CTkFrame(self.container)
        # left: contacts (avatar + name)
        left = ctk.CTkFrame(page, width=240, corner_radius=8)
        left.pack(side="left", fill="y", padx=12, pady=12)
        ctk.CTkLabel(left, text="Contacts", font=("Arial", 18, "bold")).pack(pady=(12,8))
        self.team_contacts = list(self.team_messages.keys())
        self.contact_buttons = {}
        for name in self.team_contacts:
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=6)
            initials = "".join([p[0] for p in name.split()])[:2].upper()
            avatar = ctk.CTkLabel(row, text=initials, width=36, height=36, corner_radius=18, fg_color="#ffffff", text_color="#000")
            avatar.pack(side="left", padx=(4,8))
            btn = ctk.CTkButton(row, text=name, anchor="w", fg_color="transparent",
                                command=lambda n=name: self.open_conversation(n))
            btn.pack(side="left", fill="x", expand=True)
            self.contact_buttons[name] = btn

        # right: chat column
        right = ctk.CTkFrame(page, corner_radius=8)
        right.pack(side="right", expand=True, fill="both", padx=12, pady=12)
        header_row = ctk.CTkFrame(right, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(8,4))
        self.chat_header = ctk.CTkLabel(header_row, text="Select a contact", font=("Arial", 16, "bold"))
        self.chat_header.pack(side="left")
        self.typing_label = ctk.CTkLabel(header_row, text="", text_color="#666666")
        self.typing_label.pack(side="right")

        self.chat_area = ctk.CTkScrollableFrame(right, corner_radius=6, fg_color="#F7FAFF")
        self.chat_area.pack(expand=True, fill="both", padx=12, pady=(0,8))

        # multiline input (Shift+Enter = newline, Enter = send)
        input_row = ctk.CTkFrame(right, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=8)
        self.team_entry = ctk.CTkTextbox(input_row, height=64)
        self.team_entry.grid(row=0, column=0, sticky="ew", padx=(0,8))
        # Shift+Enter -> newline
        self.team_entry.bind("<Shift-Return>", lambda e: (self.team_entry.insert("insert", "\n"), "break"))
        # Enter -> send
        self.team_entry.bind("<Return>", lambda e: (self.send_team_message(), "break"))
        send_btn = ctk.CTkButton(input_row, text="Send", width=90, command=self.send_team_message)
        send_btn.grid(row=0, column=1)

        # current conversation
        self.current_chat = None
        return page

    def open_conversation(self, name):
        self.current_chat = name
        self.chat_header.configure(text=name)
        self.render_team_messages()

    def render_team_messages(self):
        for w in self.chat_area.winfo_children():
            w.destroy()
        if not self.current_chat:
            ctk.CTkLabel(self.chat_area, text="Pick a contact to start chatting.", fg_color="transparent").pack(padx=12, pady=12)
            return
        msgs = self.team_messages.get(self.current_chat, [])
        for i, m in enumerate(msgs):
            is_me = (m.get("sender") == "You")
            bubble = ctk.CTkFrame(self.chat_area, corner_radius=12, fg_color="#D1F7E9" if is_me else "#E8F0FF")
            # show text and timestamp, name for incoming
            header_text = ("" if is_me else f"{m.get('sender')} • ") 
            lbl = ctk.CTkLabel(bubble, text=f"{header_text}{m['text']}\n{m['time']}", wraplength=800, anchor="w")
            lbl.pack(padx=12, pady=8)
            bubble.pack(anchor="e" if is_me else "w", pady=6, padx=12)
        try:
            self.chat_area.update_idletasks()
            self.chat_area.yview_moveto(1.0)
        except Exception:
            pass

    def send_team_message(self):
        # support Text widget get range
        try:
            text = self.team_entry.get("0.0", "end").strip()
        except Exception:
            text = self.team_entry.get().strip()
        if not text or not self.current_chat:
            return
        msg_obj = {"sender":"You", "text":text, "time": datetime.now().strftime("%H:%M")}
        self.team_messages.setdefault(self.current_chat, []).append(msg_obj)
        self.save_team_messages()
        # clear textbox
        try:
            self.team_entry.delete("0.0", "end")
        except Exception:
            self.team_entry.delete(0, "end")
        self.render_team_messages()
        # typing indicator + mock reply
        if self.current_chat != "Neo":
            self.typing_label.configure(text=f"{self.current_chat} is typing...")
            def worker():
                time.sleep(1.0)
                def do_reply():
                    reply = {"sender": self.current_chat, "text": "Acknowledged.", "time": datetime.now().strftime("%H:%M")}
                    self.team_messages.setdefault(self.current_chat, []).append(reply)
                    self.save_team_messages()
                    self.typing_label.configure(text="")
                    self.render_team_messages()
                self.chat_area.after(10, do_reply)
            threading.Thread(target=worker, daemon=True).start()

    def create_simple_page(self, title, text):
        page = ctk.CTkFrame(self.container)
        ctk.CTkLabel(page, text=title, font=("Arial", 26, "bold")).pack(pady=30)
        ctk.CTkLabel(page, text=text, font=("Arial", 16)).pack()
        return page

    def create_settings_page(self):
        page = ctk.CTkFrame(self.container)
        ctk.CTkLabel(page, text="Settings", font=("Arial", 24, "bold")).pack(pady=18)
        theme_frame = ctk.CTkFrame(page, fg_color="transparent")
        theme_frame.pack(pady=12, padx=12, anchor="w")
        ctk.CTkLabel(theme_frame, text="Appearance:").pack(side="left", padx=(0, 8))
        theme_opt = ctk.CTkOptionMenu(theme_frame, values=["Light", "Dark", "System"], command=self.set_appearance)
        theme_opt.pack(side="left")
        theme_opt.set("System")
        ctk.CTkLabel(page, text="Storage: (auto-saves to your home directory)", text_color="gray").pack(pady=(8, 0))
        return page

    def create_history_page(self):
        page = ctk.CTkFrame(self.container)
        ctk.CTkLabel(page, text="History", font=("Arial", 24, "bold")).pack(pady=(12,6), anchor="w", padx=12)

        stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=(6,4))
        self.history_done_label = ctk.CTkLabel(stats_frame, text="Done: 0", font=("Arial", 16))
        self.history_done_label.pack(side="left", padx=(0,18))
        self.history_undone_label = ctk.CTkLabel(stats_frame, text="Undone: 0", font=("Arial", 16))
        self.history_undone_label.pack(side="left")

        self.history_percent_label = ctk.CTkLabel(page, text="0% completed", font=("Arial", 16, "bold"))
        self.history_percent_label.pack(pady=(8,6))

        # progress bar (value 0.0 - 1.0)
        self.history_progress = ctk.CTkProgressBar(page, width=520)
        self.history_progress.pack(pady=(0,12))

        # recent tasks list
        self.history_list_frame = ctk.CTkFrame(page, corner_radius=6)
        self.history_list_frame.pack(expand=True, fill="both", padx=12, pady=12)

        # initial populate
        self.draw_history()
        return page

    def draw_history(self):
        # compute done / undone counts
        done = 0
        undone = 0
        for task_list in self.tasks_by_date.values():
            for t in task_list:
                if t.get("done"):
                    done += 1
                else:
                    undone += 1
        total = done + undone
        percent = int((done / total) * 100) if total else 0

        # update labels & progress
        try:
            self.history_done_label.configure(text=f"Done: {done}")
            self.history_undone_label.configure(text=f"Undone: {undone}")
            self.history_percent_label.configure(text=f"{percent}% completed")
            self.history_progress.set(percent / 100 if total else 0.0)
        except Exception:
            pass

        # render recent tasks list (most recent first)
        for w in self.history_list_frame.winfo_children():
            w.destroy()
        if total == 0:
            ctk.CTkLabel(self.history_list_frame, text="No tasks yet.", text_color="gray").pack(padx=12, pady=12)
            return
        # show up to 100 items for performance
        items = []
        for date_str in sorted(self.tasks_by_date.keys(), reverse=True):
            for t in self.tasks_by_date[date_str]:
                status = "✓" if t.get("done") else "○"
                items.append(f"{date_str} {status} {t.get('text')} [{t.get('priority')}]")
                if len(items) >= 100:
                    break
            if len(items) >= 100:
                break
        for it in items:
            ctk.CTkLabel(self.history_list_frame, text=it, anchor="w").pack(fill="x", padx=8, pady=2)

    def create_ai_page(self):
        page = ctk.CTkFrame(self.container)
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(12, 6))
        ctk.CTkLabel(header, text="Tegbar AI", font=("Arial", 26, "bold")).pack(side="left", anchor="w")
        ctk.CTkLabel(header, text="Ask the assistant about tasks or use commands.", text_color="gray").pack(side="left", padx=(12,0))

        self.ai_area = ctk.CTkScrollableFrame(page, corner_radius=6, fg_color="#F7FAFF")
        self.ai_area.pack(expand=True, fill="both", padx=12, pady=12)

        qa = ctk.CTkFrame(page, fg_color="transparent")
        qa.pack(fill="x", padx=12, pady=(0,6))
        ctk.CTkButton(qa, text="Summarize today's tasks", command=lambda: self.handle_ai_message("summarize today's tasks")).pack(side="left", padx=6)
        ctk.CTkButton(qa, text="Add sample task", command=lambda: self.handle_ai_message("add task: Sample task | 09:00 AM | Normal | Created via AI")).pack(side="left", padx=6)

        input_row = ctk.CTkFrame(page, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=(0,12))
        self.ai_entry = ctk.CTkTextbox(input_row, height=64)
        self.ai_entry.grid(row=0, column=0, sticky="ew", padx=(0,8))
        self.ai_entry.bind("<Shift-Return>", lambda e: (self.ai_entry.insert("insert", "\n"), "break"))
        self.ai_entry.bind("<Return>", lambda e: (self.handle_ai_message(), "break"))
        send_btn = ctk.CTkButton(input_row, text="Send", width=90, command=self.handle_ai_message)
        send_btn.grid(row=0, column=1)

        self.ai_messages = []
        self.ai_messages.append({"sender":"Tegbar AI", "text":"Hello — I can help with tasks. Try: add task: Buy milk | 05:00 PM | Normal | notes\nOr: summarize today's tasks", "time": datetime.now().strftime("%H:%M")})
        self.render_ai_messages()
        return page

    def render_ai_messages(self):
        for w in self.ai_area.winfo_children():
            w.destroy()
        for m in self.ai_messages:
            is_ai = (m.get("sender") != "You")
            bubble = ctk.CTkFrame(self.ai_area, corner_radius=12, fg_color="#E8F0FF" if is_ai else "#D1F7E9")
            lbl = ctk.CTkLabel(bubble, text=f"{m.get('sender')} • {m.get('text')}\n{m.get('time')}", wraplength=800, anchor="w", justify="left")
            lbl.pack(padx=12, pady=8)
            bubble.pack(anchor="w" if is_ai else "e", pady=6, padx=12)
        try:
            self.ai_area.update_idletasks()
            self.ai_area.yview_moveto(1.0)
        except Exception:
            pass

    def handle_ai_message(self, preset_text=None):
        if preset_text is None:
            try:
                text = self.ai_entry.get("0.0", "end").strip()
            except Exception:
                text = self.ai_entry.get().strip()
        else:
            text = preset_text
        if not text:
            return
        self.ai_messages.append({"sender":"You", "text":text, "time": datetime.now().strftime("%H:%M")})
        try:
            self.ai_entry.delete("0.0", "end")
        except Exception:
            self.ai_entry.delete(0, "end")
        self.render_ai_messages()

        def worker():
            time.sleep(0.6)
            reply_text = self.ai_generate_reply(text)
            self.ai_messages.append({"sender":"Tegbar AI", "text":reply_text, "time": datetime.now().strftime("%H:%M")})
            try:
                self.ai_area.after(10, self.render_ai_messages)
            except Exception:
                self.render_ai_messages()
        threading.Thread(target=worker, daemon=True).start()

    def ai_generate_reply(self, text):
        t = text.strip()
        lt = t.lower()
        if lt.startswith("add task:"):
            rest = t[len("add task:"):].strip()
            parts = [p.strip() for p in rest.split("|")]
            title = parts[0] if len(parts) >= 1 and parts[0] else "Untitled task"
            time_txt = parts[1] if len(parts) >= 2 else ""
            priority = (parts[2].capitalize() if len(parts) >= 3 and parts[2] else "Normal")
            notes = parts[3] if len(parts) >= 4 else ""
            date_key = self.selected_date.isoformat()
            self.tasks_by_date.setdefault(date_key, []).append({
                "text": title, "time": time_txt, "priority": priority, "done": False, "notes": notes, "created": datetime.now().isoformat()
            })
            try:
                self.save_tasks()
            except Exception:
                pass
            try:
                if self.pages.get("tasks"):
                    self.pages["tasks"].after(10, self.draw_tasks)
            except Exception:
                pass
            return f"Added task '{title}' for {self.selected_date.strftime('%Y-%m-%d')} (priority: {priority})."

        if "summarize" in lt or ("today" in lt and "task" in lt) or "summary" in lt:
            date_key = self.selected_date.isoformat()
            tasks = self.tasks_by_date.get(date_key, [])
            if not tasks:
                return f"No tasks for {self.selected_date.strftime('%Y-%m-%d')}."
            lines = []
            for i, task in enumerate(tasks, 1):
                mark = "✓" if task.get("done") else "○"
                time_txt = f" @ {task.get('time')}" if task.get("time") else ""
                lines.append(f"{i}. {mark} {task.get('text')}{time_txt} [{task.get('priority')}]")
            return "Tasks:\n" + "\n".join(lines)

        if "help" in lt or "how" in lt or "tips" in lt:
            return "I can add tasks with: add task: Title | 02:30 PM | High | notes\nOr summarize today's tasks with: summarize today's tasks"

        return "I can help with tasks. Try: 'add task: Buy milk | 05:00 PM | Normal | from store' or 'summarize today's tasks'."

    def set_appearance(self, choice):
        if choice == "Light":
            ctk.set_appearance_mode("light")
        elif choice == "Dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("system")

    def on_close(self):
        self.save_tasks()
        self.destroy()


if __name__ == "__main__":
    app = TodoApp()

    app.mainloop()
