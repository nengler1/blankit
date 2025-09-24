# New file to handle the main page.
# This file will handle accespting, processing, and editing the given image.


# TODO: Complete the following:
#       Complete TODOs for each window
#       Add icons for app
#       Add menu bar for file, edit, view, help, etc.
#       Eventually look into mobile interfaces for IOS and Android

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
    # TODO: Add logic to process the image file after selected
    #       Display the image in the window
    #       Add functionality to edit images (blur, redact, crop, free color, paint bucket, etc.)
    #       Add functionality to save images
    #       Add functionality to remove metadata
    #       Add functionality to undo/redo changes

window = tk.Tk()
window.title("Image Uploader")
window.lift()
window.geometry(f'{width//2}x{height//2}+{center_x*3//2}+{center_y*3//2}')
# TODO:     Add image upload button of any filetype (png, jpeg, jpg, etc.)
#           Add image display and confirmation
#           Focus window until complete
#           Close window and prompt AI when complete

root.mainloop()


