import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter
from layer_manager import LayerManager
from editor_tools import EditorTools

class ImageRedactorApp(customtkinter.CTk):
    def __init__(self):
        customtkinter.set_appearance_mode("System")
        super().__init__()
        self.title("BlankIt")
        self.geometry("900x600")
        
        # Initial state
        self.layer_manager = LayerManager()
        self.editor_tools = EditorTools(self.layer_manager)
        self.selected_layer = None
        
        self.image = None
        self.original_image = None
        self.display_image = None
        self.display_scale = 1.0
        self.canvas_image_id = None
        
        # Layout UI
        self.create_toolbar()
        self.create_main_widgets()
        self.apply_initial_appearance()

    def create_toolbar(self):
        toolbar = customtkinter.CTkFrame(self, fg_color="#545E56")
        toolbar.pack(side="top", fill="x")
        btn_fg = "#545E56"
        btn_hover = "#667761"
        btn_text = "#1B1B1E"
        
        btn_open = customtkinter.CTkButton(toolbar, text="Open", fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text, command=self.upload_photo)
        btn_open.pack(side="left", padx=5, pady=5)
        btn_save = customtkinter.CTkButton(toolbar, text="Save", fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text, command=self.save_image)
        btn_save.pack(side="left", padx=5, pady=5)
        btn_exit = customtkinter.CTkButton(toolbar, text="Exit", fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text, command=self.quit)
        btn_exit.pack(side="left", padx=5, pady=5)
        
        self.dark_switch = customtkinter.CTkSwitch(toolbar, text="Dark Mode", command=self.toggle_dark_mode)
        self.dark_switch.pack(side="right", padx=10, pady=5)

    def create_main_widgets(self):
        self.content_frame = customtkinter.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Left canvas and scrollbars
        self.canvas_container = customtkinter.CTkFrame(self.content_frame, fg_color="transparent")
        self.canvas_container.pack(side="left", fill="both", expand=True)
        
        self.v_scroll = tk.Scrollbar(self.canvas_container, orient="vertical")
        self.h_scroll = tk.Scrollbar(self.canvas_container, orient="horizontal")
        self.canvas = tk.Canvas(self.canvas_container, bg="#EAE1DF", bd=0, highlightthickness=0,
                                yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        
        # Right editor panel (scrollable with canvas + inner CTkFrame)
        self.editor_frame = customtkinter.CTkFrame(self.content_frame, width=280)
        self.editor_frame.pack(side="right", fill="y", padx=(8,0), pady=4)
        
        self.editor_canvas = tk.Canvas(self.editor_frame, bd=0, highlightthickness=0)
        self.editor_vscroll = tk.Scrollbar(self.editor_frame, orient="vertical", command=self.editor_canvas.yview)
        self.editor_canvas.configure(yscrollcommand=self.editor_vscroll.set)
        self.editor_vscroll.pack(side="right", fill="y")
        self.editor_canvas.pack(side="left", fill="both", expand=True)
        
        self.editor_inner = customtkinter.CTkFrame(self.editor_canvas, fg_color="#EAE1DF")
        self.editor_canvas.create_window((0,0), window=self.editor_inner, anchor='nw')
        
        self.editor_inner.bind("<Configure>", lambda e: self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all")))
        self.editor_canvas.bind("<Enter>", lambda e: self.editor_canvas.focus_set())
        self.editor_canvas.bind("<MouseWheel>", self._on_editor_mousewheel)
        
        # Add initial placeholder label
        self.editor_placeholder = customtkinter.CTkLabel(self.editor_inner, text="Upload an image to see editing options")
        self.editor_placeholder.pack(padx=12, pady=12)
        
        # Bind canvas events for editing
        self.canvas.bind("<Button-1>", self.editor_tools.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.editor_tools.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.editor_tools.on_mouse_up)

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_path:
            return
        pil = Image.open(file_path).convert('RGBA')
        self.original_image = pil.copy()
        
        max_dim = 800
        w, h = pil.size
        self.display_scale = min(max_dim / w, max_dim / h, 1.0)
        disp_w, disp_h = int(w * self.display_scale), int(h * self.display_scale)
        self.display_image = pil.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        
        self.canvas.delete("all")
        self.canvas.config(width=min(disp_w, self.winfo_width()//2), height=min(disp_h, self.winfo_height()//2))
        self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.configure(scrollregion=(0, 0, disp_w, disp_h))
        
        if disp_h > self.canvas.winfo_height():
            self.v_scroll.grid()
        else:
            self.v_scroll.grid_remove()
        if disp_w > self.canvas.winfo_width():
            self.h_scroll.grid()
        else:
            self.h_scroll.grid_remove()
        
        self.layer_manager.clear_layers()
        self.selected_layer = None
        self.editor_tools.clear_selection()
        self.show_editor_panel()
        
    def show_editor_panel(self):
        # Clear current editor_inner children, build UI controls synced with editor_tools & layer_manager
        for child in self.editor_inner.winfo_children():
            child.destroy()
        
        # Here you would build method/shape/intensity sliders and region list
        # (Refer to the old code or your latest implementation for full controls)
        # Implement syncing UI controls with editor_tools and current selection
        
        # Add placeholder for demo:
        label = customtkinter.CTkLabel(self.editor_inner, text="Editor controls here...")
        label.pack()
        
    def save_image(self):
        if not self.original_image:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                                    filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if not save_path:
            return
        composite = self.layer_manager.merge_all(self.original_image)
        composite.save(save_path)
        messagebox.showinfo("Saved", "Redacted image saved successfully.")

    def _on_editor_mousewheel(self, event):
        try:
            delta = int(event.delta / 120)
            self.editor_canvas.yview_scroll(-delta, "units")
        except Exception:
            pass

    def apply_initial_appearance(self):
        try:
            mode = None
            try:
                mode = customtkinter.get_appearance_mode()
            except Exception:
                mode = 'Light'

            if mode == 'Dark':
                self.config(bg='#1B1B1E')  # dark background
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg='#1B1B1E')
            else:
                self.config(bg='#EAE1DF')  # light background
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg='#EAE1DF')
        except Exception:
            pass

    def toggle_dark_mode(self):
        current = customtkinter.get_appearance_mode()
        new_mode = 'Light' if current == 'Dark' else 'Dark'
        customtkinter.set_appearance_mode(new_mode)
        # Reflect any UI updates needed on mode change (e.g., editor redraw)
        self.show_editor_panel()

if __name__ == "__main__":
    app = ImageRedactorApp()
    app.mainloop()
