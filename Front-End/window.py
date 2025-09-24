# New file to handle the main page.
# This file will handle accespting, processing, and editing the given image.

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

root = tk.Tk()

root.title("BlankIt")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

width = screen_width // 2
height = screen_height // 2

center_x = int(screen_width/2 - width / 2)
center_y = int(screen_height/2 - height / 2)

root.geometry(f'{width}x{height}+{center_x}+{center_y}')
def upload_photo():
    file_path = filedialog.askopenfilename()
    print(f"Selected File: {file_path}")
    # Add logic to process the image file here

window = tk.Tk()
window.title("Image Uploader")
window.lift()
window.geometry(f'{width//2}x{height//2}+{center_x*(3//2)}+{center_y*(3//2)}')
root.mainloop()
