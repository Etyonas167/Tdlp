import sqlite3
import hashlib
import customtkinter as ctk
from tkinter import messagebox, Listbox, Frame, Button
from datetime import datetime
import threading
import time

# ---------------------- DB SETUP ----------------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Create tasks table for data persistence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'ongoing',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------- ANIMATED NOTIFICATION SYSTEM ----------------------
class AnimatedNotification:
    def __init__(self, parent):
        self.parent = parent
        self.notification = None
        self.animation_thread = None
        
    def show_notification(self, message, notification_type="success"):
        """Show animated notification"""
        # Destroy existing notification if any
        if self.notification:
            self.notification.destroy()
            
        # Create notification frame
        self.notification = ctk.CTkFrame(self.parent, fg_color="#2b2b2b", corner_radius=10)
        
        # Set colors based on type
        if notification_type == "success":
            border_color = "#4CAF50"
            icon_text = "✓"
        elif notification_type == "error":
            border_color = "#f44336"
            icon_text = "✗"
        elif notification_type == "info":
            border_color = "#2196F3"
            icon_text = "ℹ"
        else:
            border_color = "#FF9800"
            icon_text = "!"
            
        # Create notification content
        icon_label = ctk.CTkLabel(self.notification, text=icon_text, font=("Arial", 20, "bold"), 
                                 text_color=border_color, fg_color="transparent")
        icon_label.pack(side="left", padx=(15, 10))
        
        message_label = ctk.CTkLabel(self.notification, text=message, font=("Arial", 14), 
                                   text_color="white", fg_color="transparent")
        message_label.pack(side="left", padx=(0, 15), pady=15)
        
        # Position notification (top-right corner)
        self.notification.place(relx=1.0, rely=0.0, x=-143, y=20, anchor="center")
        
        # Start animation
        self.animate_in()
        
        # Auto-hide after 4 seconds
        self.parent.after(4000, self.animate_out)
        
    def animate_in(self):
        """Animate notification sliding in from top"""
        if not self.notification:
            return
    
        # Start position (above screen)
        self.notification.place(relx=0.2, rely=0.0, x=-143, y=-100, anchor="ne")
        
        # Animate to final position
        for i in range(20):
            if not self.notification:
                break
            y_pos = -100 + (i * 6)  # Smooth slide down
            self.notification.place(relx=1.0, rely=0.0, x=-143, y=y_pos, anchor="ne")
            self.parent.update()
            time.sleep(0.01)
            
    def animate_out(self):
        """Animate notification sliding out"""
        if not self.notification:
            return
            
        # Animate out
        for i in range(20):
            if not self.notification:
                break
            y_pos = 20 - (i * 6)  # Smooth slide up
            self.notification.place(relx=1.0, rely=0.0, x=-143, y=y_pos, anchor="ne")
            self.parent.update()
            time.sleep(0.01)
            
        # Destroy notification
        if self.notification:
            self.notification.destroy()
            self.notification = None

# ---------------------- TODO APP ----------------------
def show_todo_app(user_id):
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("green")

    window = ctk.CTk()
    window.title("ተግባር List")
    window.geometry("400x600")
    window.minsize(400, 600)  # Set minimum size to prevent window from being too small
    window.resizable(True, True)  # Allow window resizing

    # Create notification system
    notification = AnimatedNotification(window)
    
    # Create main phone frame to contain all widgets
    phone_frame = ctk.CTkFrame(window, fg_color="transparent", corner_radius=15, width=480, height=500)
    phone_frame.pack(padx=10, pady=50)
    phone_frame.pack_propagate(False)  # Prevent frame from expanding
    
    title = ctk.CTkLabel(phone_frame, text="ተግባር LIST", font=("Arial Black", 24))
    title.pack(pady=(5, 10))

    tabview = ctk.CTkTabview(phone_frame, width=380, height=250)
    tabview.pack(pady=(10, 5))

    ongoing_tab = tabview.add("ON GOING")
    achieved_tab = tabview.add("ACHIEVED")

    # Replace Listbox with CTkScrollableFrame for ongoing tasks
    ongoing_scroll = ctk.CTkScrollableFrame(ongoing_tab, width=320, height=200, fg_color="#232323")
    ongoing_scroll.pack(padx=5, pady=5, fill="both", expand=True)

    # Replace Listbox with CTkScrollableFrame for achieved tasks
    achieved_scroll = ctk.CTkScrollableFrame(achieved_tab, width=320, height=200, fg_color="#232323")
    achieved_scroll.pack(padx=5, pady=5, fill="both", expand=True)

    # Global variables to store task data
    ongoing_tasks = []
    achieved_tasks = []
    selected_index = None
    selected_achieved_index = None

    # Helper to render tasks
    def render_ongoing_tasks(tasks):
        nonlocal ongoing_tasks
        ongoing_tasks = tasks
        
        # Clear existing widgets
        for widget in ongoing_scroll.winfo_children():
            widget.destroy()
            
        for idx, (task_text, timestamp) in enumerate(tasks):
            # Create main row frame
            row = ctk.CTkFrame(ongoing_scroll, fg_color="#313131", corner_radius=8)
            row.pack(fill="x", pady=3, padx=5)
            
            # Convert timestamp to readable format for display
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                display_timestamp = dt.strftime("%d %b %H:%M")
            except:
                display_timestamp = timestamp
            
            # Create inner frame to hold content
            content_frame = ctk.CTkFrame(row, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=8)
            
            # Task text (bold, left side)
            task_label = ctk.CTkLabel(content_frame, text=task_text, font=("Arial", 14, "bold"), 
                                     anchor="w", text_color="#fff", fg_color="transparent")
            task_label.pack(side="left", fill="x", expand=True)
            
            # Timestamp (faded, right side)
            timestamp_label = ctk.CTkLabel(content_frame, text=display_timestamp, font=("Consolas", 12), 
                                         anchor="e", text_color="#888888", fg_color="transparent")
            timestamp_label.pack(side="right", padx=(10, 0))
            
            # Hover effects
            def on_enter(e, r=row): 
                r.configure(fg_color="#444")
            def on_leave(e, r=row): 
                r.configure(fg_color="#313131")
            
            # Click handler - show popup with action buttons
            def on_click(e, i=idx): 
                print(f"Task {i} clicked!")  # Debug message
                print(f"Calling show_action_popup_for_index({i})")
                show_action_popup_for_index(i)
                print(f"Finished calling show_action_popup_for_index({i})")
            
            # Bind events to the entire row
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<Button-1>", on_click)
            
            # Bind events to content frame
            content_frame.bind("<Enter>", on_enter)
            content_frame.bind("<Leave>", on_leave)
            content_frame.bind("<Button-1>", on_click)
            
            # Bind events to labels
            task_label.bind("<Enter>", on_enter)
            task_label.bind("<Leave>", on_leave)
            task_label.bind("<Button-1>", on_click)
            
            timestamp_label.bind("<Enter>", on_enter)
            timestamp_label.bind("<Leave>", on_leave)
            timestamp_label.bind("<Button-1>", on_click)

    # Helper to render achieved tasks
    def render_achieved_tasks(tasks):
        nonlocal achieved_tasks
        achieved_tasks = tasks
        
        # Clear existing widgets
        for widget in achieved_scroll.winfo_children():
            widget.destroy()
            
        for idx, (task_text, timestamp) in enumerate(tasks):
            # Create main row frame
            row = ctk.CTkFrame(achieved_scroll, fg_color="#313131", corner_radius=8)
            row.pack(fill="x", pady=3, padx=5)
            
            # Convert timestamp to readable format for display
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                display_timestamp = dt.strftime("%d %b %H:%M")
            except:
                display_timestamp = timestamp
            
            # Create inner frame to hold content
            content_frame = ctk.CTkFrame(row, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=8)
            
            # Task text (bold, left side) with green color for achieved tasks
            task_label = ctk.CTkLabel(content_frame, text=f"{task_text} ✅", font=("Arial", 14, "bold"), 
                                     anchor="w", text_color="#4CAF50", fg_color="transparent")
            task_label.pack(side="left", fill="x", expand=True)
            
            # Timestamp (faded, right side)
            timestamp_label = ctk.CTkLabel(content_frame, text=display_timestamp, font=("Consolas", 12), 
                                         anchor="e", text_color="#888888", fg_color="transparent")
            timestamp_label.pack(side="right", padx=(10, 0))
            
            # Hover effects
            def on_enter(e, r=row): 
                r.configure(fg_color="#444")
            def on_leave(e, r=row): 
                r.configure(fg_color="#313131")
            
            # Click handler - show popup with action buttons for achieved tasks
            def on_click(e, i=idx): 
                print(f"Achieved task {i} clicked!")  # Debug message
                print(f"Calling show_achieved_action_popup_for_index({i})")
                show_achieved_action_popup_for_index(i)
                print(f"Finished calling show_achieved_action_popup_for_index({i})")
            
            # Bind events to the entire row
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<Button-1>", on_click)
            
            # Bind events to content frame
            content_frame.bind("<Enter>", on_enter)
            content_frame.bind("<Leave>", on_leave)
            content_frame.bind("<Button-1>", on_click)
            
            # Bind events to labels
            task_label.bind("<Enter>", on_enter)
            task_label.bind("<Leave>", on_leave)
            task_label.bind("<Button-1>", on_click)
            
            timestamp_label.bind("<Enter>", on_enter)
            timestamp_label.bind("<Leave>", on_leave)
            timestamp_label.bind("<Button-1>", on_click)

    # Safe auto-hide function to prevent Tkinter errors
    def safe_hide_popup(popup_widget):
        try:
            if popup_widget.winfo_exists():
                popup_widget.place_forget()
        except Exception as e:
            print(f"Error hiding popup: {e}")

    # Helper to show popup for a given index - SIMPLIFIED
    def show_action_popup_for_index(idx):
        nonlocal selected_index
        selected_index = idx
        try:
            print(f"Showing popup for task {idx}")
            
            # Simple fixed positioning - show popup in top-right area
            popup_x = 250  # Adjusted for mobile width (400px - 120px popup - 30px margin)
            popup_y = 150  # Fixed Y position
            
            # Show popup
            action_popup.place(x=popup_x, y=popup_y)
            action_popup.lift()
            action_popup.update()  # Force update
            print(f"Popup shown for task {idx} at position ({popup_x}, {popup_y})")
            
            # Auto-hide popup after 15 seconds with safe function
            window.after(15000, lambda: safe_hide_popup(action_popup))
            
        except Exception as e:
            print(f"Error showing popup: {e}")
            import traceback
            traceback.print_exc()

    # Helper to show popup for achieved tasks
    def show_achieved_action_popup_for_index(idx):
        nonlocal selected_achieved_index
        selected_achieved_index = idx
        try:
            print(f"Showing achieved popup for task {idx}")
            
            # Simple fixed positioning - show popup in top-right area
            popup_x = 250  # Adjusted for mobile width (400px - 120px popup - 30px margin)
            popup_y = 150  # Fixed Y position
            
            # Show popup
            achieved_action_popup.place(x=popup_x, y=popup_y)
            achieved_action_popup.lift()
            achieved_action_popup.update()  # Force update
            print(f"Achieved popup shown for task {idx} at position ({popup_x}, {popup_y})")
            
            # Auto-hide popup after 15 seconds with safe function
            window.after(15000, lambda: safe_hide_popup(achieved_action_popup))
            
        except Exception as e:
            print(f"Error showing achieved popup: {e}")
            import traceback
            traceback.print_exc()

    # Action functions for popup buttons
    def complete_selected():
        nonlocal selected_index, ongoing_tasks
        if selected_index is None:
            notification.show_notification("Please select a task to complete.", "error")
            return
        task_text, timestamp = ongoing_tasks[selected_index]
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET status='achieved' 
            WHERE user_id=? AND task_text=? AND timestamp=?
        """, (user_id, task_text, timestamp))
        conn.commit()
        conn.close()
        load_tasks()
        action_popup.place_forget()
        notification.show_notification("Task marked as completed!", "success")

    def delete_selected():
        nonlocal selected_index, ongoing_tasks
        if selected_index is None:
            notification.show_notification("Please select a task to delete.", "error")
            return
        
        try:
            task_text, timestamp = ongoing_tasks[selected_index]
            
            # Delete from database immediately
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tasks 
                WHERE user_id=? AND task_text=? AND timestamp=?
            """, (user_id, task_text, timestamp))
            conn.commit()
            conn.close()
            
            # Hide popup immediately
            action_popup.place_forget()
            
            # Refresh the list to remove from display
            load_tasks()
            
            # Show success notification
            notification.show_notification("Task deleted successfully!", "success")
            
        except Exception as e:
            notification.show_notification(f"Error deleting task: {str(e)}", "error")

    def edit_selected():
        nonlocal selected_index, ongoing_tasks
        if selected_index is None:
            notification.show_notification("Please select a task to edit.", "error")
            return
        task_text, timestamp = ongoing_tasks[selected_index]
        entry.delete(0, 'end')
        entry.insert(0, task_text)
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM tasks 
            WHERE user_id=? AND task_text=? AND timestamp=?
        """, (user_id, task_text, timestamp))
        conn.commit()
        conn.close()
        load_tasks()
        action_popup.place_forget()

    # Action functions for achieved task popup buttons
    def move_back_to_ongoing_selected():
        nonlocal selected_achieved_index, achieved_tasks
        if selected_achieved_index is None:
            notification.show_notification("Please select an achieved task to move back.", "error")
            return
        task_text, timestamp = achieved_tasks[selected_achieved_index]
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET status='ongoing' 
            WHERE user_id=? AND task_text=? AND timestamp=?
        """, (user_id, task_text, timestamp))
        conn.commit()
        conn.close()
        load_tasks()
        achieved_action_popup.place_forget()
        notification.show_notification("Task moved back to ongoing!", "success")

    def delete_achieved_selected():
        nonlocal selected_achieved_index, achieved_tasks
        if selected_achieved_index is None:
            notification.show_notification("Please select an achieved task to delete.", "error")
            return
        
        try:
            task_text, timestamp = achieved_tasks[selected_achieved_index]
            
            # Delete from database immediately
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tasks 
                WHERE user_id=? AND task_text=? AND timestamp=?
            """, (user_id, task_text, timestamp))
            conn.commit()
            conn.close()
            
            # Hide popup immediately
            achieved_action_popup.place_forget()
            
            # Refresh the list to remove from display
            load_tasks()
            
            # Show success notification
            notification.show_notification("Achieved task deleted successfully!", "success")
            
        except Exception as e:
            notification.show_notification(f"Error deleting achieved task: {str(e)}", "error")

    # Patch load_tasks to use the new renderer
    def load_tasks():
        nonlocal ongoing_tasks, selected_index, achieved_tasks, selected_achieved_index
        ongoing_tasks = []
        achieved_tasks = []
        selected_index = None
        selected_achieved_index = None
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT task_text, timestamp FROM tasks WHERE user_id=? AND status='ongoing' ORDER BY timestamp DESC", (user_id,))
        ongoing_tasks = cursor.fetchall()
        render_ongoing_tasks(ongoing_tasks)
        cursor.execute("SELECT task_text, timestamp FROM tasks WHERE user_id=? AND status='achieved' ORDER BY timestamp DESC", (user_id,))
        achieved_tasks = cursor.fetchall()
        render_achieved_tasks(achieved_tasks)
        conn.close()

    search_frame = ctk.CTkFrame(phone_frame, fg_color="transparent")
    search_frame.pack(pady=10)
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search task", width=300)
    search_entry.pack(side="left", padx=(0, 10))

    def search_tasks():
        """Search tasks in real-time"""
        query = search_entry.get().strip().lower()
        if query == "":
            load_tasks()
            return
            
        # Clear ongoing tasks
        for widget in ongoing_scroll.winfo_children():
            widget.destroy()
        for widget in achieved_scroll.winfo_children():
            widget.destroy()
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # Search in ongoing tasks
        cursor.execute("""
            SELECT task_text, timestamp FROM tasks 
            WHERE user_id=? AND status='ongoing' AND task_text LIKE ? 
            ORDER BY timestamp DESC
        """, (user_id, f"%{query}%"))
        ongoing_tasks = cursor.fetchall()
        render_ongoing_tasks(ongoing_tasks)
        
        # Search in achieved tasks
        cursor.execute("""
            SELECT task_text, timestamp FROM tasks 
            WHERE user_id=? AND status='achieved' AND task_text LIKE ? 
            ORDER BY timestamp DESC
        """, (user_id, f"%{query}%"))
        achieved_tasks = cursor.fetchall()
        render_achieved_tasks(achieved_tasks)
        
        conn.close()

    # Bind search to real-time updates
    search_entry.bind("<KeyRelease>", lambda e: search_tasks())

    search_button = ctk.CTkButton(search_frame, text="SEARCH", command=search_tasks, fg_color="green")
    search_button.pack(side="right")

    entry_frame = ctk.CTkFrame(phone_frame, fg_color="transparent")
    entry_frame.pack(pady=5, padx=10, fill="x")

    entry = ctk.CTkEntry(entry_frame, placeholder_text="Enter task", width=250, font=("Arial", 14))
    entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

    def add_task():
        """Add new task to database"""
        task = entry.get().strip()
        if task:
            # Use ISO format for proper sorting, but display in readable format
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (user_id, task_text, timestamp, status) 
                VALUES (?, ?, ?, 'ongoing')
            """, (user_id, task, timestamp))
            conn.commit()
            conn.close()
            
            entry.delete(0, 'end')
            load_tasks()

    add_button = ctk.CTkButton(entry_frame, text="ADD", command=add_task, fg_color="green", width=80)
    add_button.pack(side="right")

    def clear_all_achieved():
        # No confirmation dialog, just clear
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE user_id=? AND status='achieved'", (user_id,))
            conn.commit()
            conn.close()
            load_tasks()
            notification.show_notification("All achieved tasks cleared!", "success")
        except Exception as e:
            notification.show_notification(f"Error clearing achieved tasks: {str(e)}", "error")

    # Create popup frame for action buttons - SIMPLIFIED VERSION
    action_popup = ctk.CTkFrame(window, fg_color="#1b1e27", corner_radius=5, width=120, height=100)  # RED for visibility
    
    # Create buttons directly
    complete_btn = ctk.CTkButton(action_popup, text="Complete", command=complete_selected, 
                                fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    complete_btn.pack(pady=2, padx=5, fill="x")
    
    delete_btn = ctk.CTkButton(action_popup, text="Delete", command=delete_selected, 
                              fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    delete_btn.pack(pady=2, padx=5, fill="x")
    
    edit_btn = ctk.CTkButton(action_popup, text="Edit", command=edit_selected, 
                            fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    edit_btn.pack(pady=2, padx=5, fill="x")

    # Create popup frame for achieved task action buttons
    achieved_action_popup = ctk.CTkFrame(window, fg_color="#00ff00", corner_radius=5, width=120, height=120)  # GREEN for visibility
    action_popup_buttons = []
    # Create buttons for achieved tasks
    move_back_btn = ctk.CTkButton(achieved_action_popup, text="Move Back", command=move_back_to_ongoing_selected, 
                                 fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    move_back_btn.pack(pady=2, padx=5, fill="x")
    
    delete_achieved_btn = ctk.CTkButton(achieved_action_popup, text="Delete", command=delete_achieved_selected, 
                                       fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    delete_achieved_btn.pack(pady=2, padx=5, fill="x")
    
    clear_all_btn = ctk.CTkButton(achieved_action_popup, text="Clear All", command=clear_all_achieved, 
                                 fg_color="#1e1e1e", text_color="#ffffff", width=100, height=25)
    clear_all_btn.pack(pady=2, padx=5, fill="x")

    def hide_popup_on_click(event):
        widget = event.widget
        # Don't hide if clicking on either popup
        if str(widget).startswith(str(action_popup)) or str(widget).startswith(str(achieved_action_popup)):
            return
        # Add a small delay to prevent immediate hiding
        window.after(15000, action_popup.place_forget)
        window.after(15000, achieved_action_popup.place_forget)

    window.bind("<Button-1>", hide_popup_on_click)

    # Create frame for achieved task buttons
    achieved_buttons_frame = ctk.CTkFrame(window, fg_color="transparent")
    achieved_buttons_frame.pack(pady=5)

    # Bind Enter key to add task
    window.bind("<Return>", lambda e: add_task())

    # Load initial tasks
    load_tasks()

    window.mainloop()

# ---------------------- LOGIN PAGE ----------------------
def show_login_window():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    login_win = ctk.CTk()
    login_win.title("Login / Sign Up")
    login_win.geometry("600x300")
    #login_win.iconbitmap('output_icon.ico')
    # Create notification system for login window
    notification = AnimatedNotification(login_win)

    ctk.CTkLabel(login_win, text="Welcome to Tegbar List!", font=("Arial Black", 20)).pack(pady=20)

    username_entry = ctk.CTkEntry(login_win, placeholder_text="Username", width=400)
    username_entry.pack(pady=5)

    password_entry = ctk.CTkEntry(login_win, placeholder_text="Password", show="*", width=400)
    password_entry.pack(pady=5)

    password_entry.pack()

    def login():
        username = username_entry.get()
        password = hash_password(password_entry.get())

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            login_win.destroy()
            show_todo_app(user[0])  # Pass user_id to todo app
        else:
            notification.show_notification("Invalid username or password.", "error")

    def signup():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            notification.show_notification("Username and password required.", "error")
            return

        hashed = hash_password(password)
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            notification.show_notification("Sign up successful! Now log in.", "success")
        except sqlite3.IntegrityError:
            notification.show_notification("Username already exists.", "error")
    ctk.CTkButton(login_win, text="Login", command=login, width=200, fg_color="#4CAF50").pack(pady=10)
    ctk.CTkButton(login_win, text="Sign Up", command=signup, width=200, fg_color="#2196F3").pack()

    # Bind Enter key to login
    login_win.bind("<Return>", lambda e: login())

    login_win.mainloop()

# ---------------------- MAIN ENTRY ----------------------
if __name__ == "__main__":
    init_db()
show_login_window()
