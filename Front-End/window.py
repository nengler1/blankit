import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from ctypes import windll
import shutil
import os

class ImageRedactorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BlankIt")
        self.iconbitmap('.\Front-End\Icons\Blankit.ico')
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width, height = screen_width // 2, screen_height // 2
        center_x, center_y = (screen_width // 2 - width // 2, screen_height // 2 - height // 2)
        self.geometry(f'{width}x{height}+{center_x}+{center_y}')
        self.image = None
        self.canvas_image = None
        message = tk.Label(self, text="Welcome to BlankIt! Upload an image to get started.", font=("Arial", 14))
        message.pack()
        # TODO: Display logo on startup
        # Display logo on app home page before image upload (Image at Front-End\Icons\Logo.png)

        self.create_widgets()
        self.create_menu()

    def create_widgets(self):
        # Upload Button
        self.upload_btn = ttk.Button(self, text="Upload Photo", command=self.upload_photo)
        self.upload_btn.pack(pady=10)

        # Canvas to display image
        self.canvas = tk.Canvas(self, bg="grey", width=400, height=400)
        self.canvas.pack(expand=True, fill='both')

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.upload_photo)
        file_menu.add_command(label="Save Image", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            img = Image.open(file_path)
            img = img.resize((min(400, img.width), min(400, img.height)), Image.Resampling.LANCZOS)            
            self.image = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas_image = self.canvas.create_image(200, 200, image=self.image)
            # TODO: Add image editing tools (blur, redact, etc.)
            # See: https://hackr.io/blog/how-to-create-a-python-image-editor-app

    def save_image(self):
        if self.image:
            # TODO: Save the current image after edits, remove metadata, etc.
            # See: https://www.geeksforgeeks.org/python/save-image-to-file-in-python-using-tkinter/
            messagebox.showinfo("Save", "Save feature to be implemented.")
        else:
            messagebox.showwarning("No image", "No image to save!")

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)

    finally:
        app = ImageRedactorApp()
        app.mainloop()
