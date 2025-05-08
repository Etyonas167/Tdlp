from tkinter import *
from tkinter.font import Font
from tkinter import colorchooser
from tkinter import filedialog
import os
window = Tk()
window.title("To-Do List")
window.geometry("500x500")
window.config(bg='#0a9548')

myfont = Font(family="Brush Script MT",
              size=10,
              weight="bold")

frame = Frame(window,bg='light blue')
frame.pack(pady=10)

sbFr=Frame(window,
                height=1,
                bg='#0a9548')
sbFr.pack()
sbLa=Label(sbFr,
    text='search, your list item',)
sbLa.pack()
searchbox = Entry(sbFr,
                  font=('Helvetica',14),
                  text='search',
                  bg="orange",
                  width=14)
searchbox.bind("<Return>", 
    lambda event: search())
searchbox.pack(side=TOP,fill=BOTH, pady=25)
entryText=Label(sbFr,
    text='Enter the lists here')
entryText.pack()
entry = Entry(sbFr,font=("Helvetica",24),
    width=15,
    )
entry.pack(pady=25)

'''
search_button = Button(frame,
    text="Search",
    command=searchbox)
search_button.pack()
'''

listbox = Listbox(frame,
                  font=myfont,
                  width=32,
                  height=5,
                  bd=0,
                  bg='lightgreen',
                  fg="black",
                  highlightthickness=2,
                  selectbackground="gray",
                  activestyle="none",                  
                  relief=SOLID)
listbox.pack(side=LEFT,fill=BOTH)

scrollbar = Scrollbar(frame)
scrollbar.pack(side=RIGHT,fill=BOTH)

listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)


plan = ['wake up', 'wash','brush','school','task','sleep']
for item in plan:
    listbox.insert(END,item)


btframe = Frame(window,
                bg='#0a9548',
                height=3,
                width=7)
btframe.pack(pady=25)


def search():
        query = searchbox.get().lower()
        listbox.delete(0, END)
        for item in plan:
            if query in item.lower():
                listbox.insert(END, item)


def add_():
        text = entry.get().strip()
        if text:
            listbox.insert(END, text)  # Add to the end
            entry.delete(0, END)


def delete_():
    listbox.delete(ANCHOR)

def uncross_():
    listbox.itemconfig(
        listbox.curselection(),
        fg="#464646",)
    listbox.selection_clear(0,END)

def cross_off_():
    listbox.itemconfig(
        listbox.curselection(),
        fg="#dedede",)
    listbox.selection_clear(0,END)

def delete_crossed_():
    count = 0
    while count < listbox.size():
        if listbox.itemcget(count,"fg") == "#dedede":
            listbox.delete(listbox.index(count))
        else:
            count +=1
        
    from tkinter import filedialog

def save_list():
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        initialdir=".",
        title="Save your to-do list"
    )
    if filepath:
        with open(filepath, "w") as file:
            for item in listbox.get(0, END):
                file.write(item + "\n")


def open_list():
    listbox.delete(0, END)
    if os.path.exists("todo.txt"):
        with open("todo.txt", "r") as file:
            for line in file:
                listbox.insert(END, line.strip())
    else:
        print("No todo.txt file found. Save a list first.")


def clear_list():
    listbox.delete(0, END)

def edit():
    try:
        selected_index = listbox.curselection()[0]
        selected_text = listbox.get(selected_index)
        entry.delete(0, END)
        entry.insert(0, selected_text)
        listbox.delete(selected_index)
    except IndexError:
        pass  # No item selected

def click():
     window.config(bg=colorchooser.askcolor()[1])

mmenu = Menu(window)
window.config(menu=mmenu)

# File Menu
file_menu = Menu(mmenu, tearoff=False)
mmenu.add_cascade(label="File", menu=file_menu)

file_menu.add_command(label="Save List", command=save_list)
file_menu.add_command(label="Open List", command=open_list)
file_menu.add_separator()
file_menu.add_command(label="Clear List", command=clear_list)

# Help Menu
help_menu = Menu(mmenu, tearoff=False)
mmenu.add_cascade(label="Help", menu=help_menu)

help_menu.add_command(label="About", command=lambda: print("This is a to-do list app by YOU 😎"))

add = Button(btframe,
    text="add",
    fg='white',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=add_)
    
delete = Button(btframe,
    text="delete",
    fg='white',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=delete_)
    
cross_off = Button(btframe,
    text="cross_off",
    fg='white',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=cross_off_)
    
uncross = Button(btframe,
    text="uncross",
    fg='White',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=uncross_)
    
delete_crossed = Button(btframe,
    text="delete_cross",
    fg='white',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=delete_crossed_)
    
editbtn = Button(btframe,
    text="edit",
    fg='white',
    height=2,
    width=9,
    bg='#0d2818',
    font=("Helvetica",5,"bold"),
    command=edit)

editbtn.grid(row=1,column=2)
add.grid(row=0,column=0, pady=14)
delete.grid(row=1,column=0, pady=14, padx=10)
cross_off.grid(row=0,column=1,padx=10)
uncross.grid(row=1,column=1, padx=10)
delete_crossed.grid(row=0,column=2,padx=10)


window.mainloop()