import tkinter as tk
from tkinter import ttk, filedialog, messagebox, BooleanVar
from PIL import Image, ImageTk
from ctypes import windll
from layer_manager import Layer, LayerManager
import customtkinter
import shutil
import os
import json

class ImageRedactorApp(customtkinter.CTk):
    def __init__(self):
        # Initialize the main window
        # Configure customtkinter appearance and load a custom theme file if available.
        # Use 'System' as default so we don't forcibly override a user's desired start mode.
        customtkinter.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
        # Build an absolute, OS-safe path to the theme file (avoid backslash-escape issues)
        theme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "themes", "BlankIt_theme.json"))
        self.theme_path = theme_path
        if os.path.isfile(theme_path):
            try:
                customtkinter.set_default_color_theme(theme_path)
            except Exception as e:
                # If loading the theme fails, fall back to the default theme and print a warning.
                print(f"Warning: failed to load custom theme {theme_path}: {e}")
        else:
            print(f"Warning: theme file not found at {theme_path}, using default theme")

        # Default colors (used for non-CTk widgets like Canvas).
        # These can be overridden by values present in the theme JSON if available.
        self.theme_colors = {
            'light_bg': '#EAE1DF',
            'dark_bg': '#1B1B1E',
            'widget': '#667761',
            'text': '#917C78'
        }
        # Try to load color overrides from the theme JSON if it exists.
        if os.path.isfile(self.theme_path):
            try:
                with open(self.theme_path, 'r', encoding='utf-8') as f:
                    theme_json = json.load(f)
                # Look for common keys in theme JSON to override defaults.
                # customtkinter theme files vary; we attempt a few heuristic keys.
                colors = theme_json.get('colors') if isinstance(theme_json, dict) else None
                if isinstance(colors, dict):
                    # Possible keys: 'background', 'bg_color', 'dark_bg', 'light_bg'
                    for key in ('background', 'bg_color', 'light_bg', 'dark_bg'):
                        if key in colors and isinstance(colors[key], str) and colors[key].startswith('#'):
                            # Map 'background' or 'bg_color' to light_bg if present
                            if key in ('background', 'bg_color'):
                                self.theme_colors['light_bg'] = colors[key]
                            else:
                                self.theme_colors[key] = colors[key]
            except Exception:
                # Non-fatal: fall back to defaults already set above
                pass
        super().__init__()
        self.title("BlankIt")
        # iconbitmap expects an absolute or relative path; keep the same relative path
        try:
            self.iconbitmap(os.path.join(os.path.dirname(__file__), "Icons", "Blankit.ico"))
        except Exception:
            # ignore if icon can't be loaded
            pass
        # Start smaller and centered (allow user to resize). Use a sensible default but keep it on-screen.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        default_w = 900
        default_h = 600
        width = min(default_w, max(400, screen_width - 200))
        height = min(default_h, max(300, screen_height - 200))
        center_x = max(0, screen_width // 2 - width // 2)
        center_y = max(0, screen_height // 2 - height // 2)
        # Set initial geometry once at startup
        try:
            self.geometry(f'{width}x{height}+{center_x}+{center_y}')
        except Exception:
            pass
        self.image = None
        self.canvas_image = None
        # Create toolbar first so it is always at the top
        self.create_toolbar()

        # Init LayerManager
        self.layer_manager = LayerManager()
        self.selected_layer = None  # track currently selected layer index
        self.region_clipboard = None  # for copy/paste of settings


        # Initial message (use customtkinter label so the theme applies)
        # Colors: light mode welcome(#BDB6B5), dark mode welcome(#43434A)
        self.welcome_colors = ("#BDB6B5", "#43434A")
        self.header_label = customtkinter.CTkLabel(self, text="Welcome to BlankIt! Upload an image to get started.", font=("Arial", 14), fg_color=self.welcome_colors)
        self.header_label.pack(pady=8, padx=12, fill='x')
        # TODO: Display logo on startup (This should be done while starting the back end & ML model in the background)
        # Display logo on app home page before image upload (Image at Front-End\Icons\Logo.png)
        # Style lightmode and dark mode using these colors: #667761 (widget), #917C78(Text/widget), #545E56(Text/widget), #1B1B1E (Dark mode background), #EAE1DF (light mode background)

        self.create_widgets()
        # Apply the current appearance to non-CTk widgets and header so start-up matches dark/light mode
        try:
            self.apply_initial_appearance()
        except Exception:
            pass

    def create_widgets(self):
        # Upload Button (use CTkButton so theme affects widget)
        self.upload_btn = customtkinter.CTkButton(self, text="Upload Photo", command=self.upload_photo)
        self.upload_btn.pack(pady=10)

        # Content frame holds canvas and editor panel side-by-side
        self.content_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill='both', padx=8, pady=8)

        # Canvas to display image with scrollbars (container)
        self.canvas_container = customtkinter.CTkFrame(self.content_frame, fg_color='transparent')
        self.canvas_container.pack(side='left', expand=True, fill='both')

        # Horizontal and vertical scrollbars
        self.v_scroll = tk.Scrollbar(self.canvas_container, orient='vertical')
        self.h_scroll = tk.Scrollbar(self.canvas_container, orient='horizontal')
        self.canvas = tk.Canvas(self.canvas_container, bg=self.theme_colors.get('light_bg', 'grey'), width=400, height=400, bd=0, highlightthickness=0,
                     yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        # layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        # hide scrollbars until an image is loaded and content overflows
        try:
            self.v_scroll.grid_remove()
            self.h_scroll.grid_remove()
        except Exception:
            pass
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        # Mouse wheel scroll bindings (Windows standard). Bind to canvas only so other widgets receive wheel events.
        self.canvas.bind('<Enter>', lambda e: self.canvas.focus_set())
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)

        # Editor panel (created as empty for now; populated after upload)
        self.editor_frame = customtkinter.CTkFrame(self.content_frame, width=280)
        self.editor_frame.pack(side='right', fill='y', padx=(8,0), pady=4)
        # Make the editor panel scrollable: prefer CTkScrollableFrame if available, else canvas+frame fallback
        try:
            self.editor_scroll = customtkinter.CTkScrollableFrame(self.editor_frame, width=260)
            self.editor_scroll.pack(fill='both', expand=True, padx=6, pady=6)
            self.editor_inner = self.editor_scroll
        except Exception:
            self.editor_canvas = tk.Canvas(self.editor_frame, bd=0, highlightthickness=0)
            self.editor_vscroll = tk.Scrollbar(self.editor_frame, orient='vertical', command=self.editor_canvas.yview)
            self.editor_canvas.configure(yscrollcommand=self.editor_vscroll.set)
            self.editor_vscroll.pack(side='right', fill='y')
            self.editor_canvas.pack(side='left', fill='both', expand=True)
            self.editor_inner = customtkinter.CTkFrame(self.editor_canvas, fg_color='transparent')
            self.editor_canvas.create_window((0,0), window=self.editor_inner, anchor='nw')
            def _on_editor_config(e):
                try:
                    self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox('all'))
                except Exception:
                    pass
            self.editor_inner.bind('<Configure>', _on_editor_config)
        # bind mousewheel for editor scrolling (works for both CTkScrollableFrame and fallback)
        try:
            # If using CTkScrollableFrame, bind its inner frame
            if hasattr(self, 'editor_inner'):
                self.editor_inner.bind('<Enter>', lambda e: self.editor_inner.focus_set())
                self.editor_inner.bind('<MouseWheel>', self._on_editor_mousewheel)
        except Exception:
            pass

        # Initially hidden: show a label prompting to upload
        self.editor_placeholder = customtkinter.CTkLabel(self.editor_inner, text='Upload an image to see editing options')
        self.editor_placeholder.pack(padx=12, pady=12)

        # Region data
        self.regions = []  # list of dicts: {'coords':(x1,y1,x2,y2), 'method':..., 'intensity':..., 'size':...}
        self.selected_region_index = None
        self.selection_mode = False
        self.region_clipboard = None

    def create_toolbar(self):
        """Create a CTk-styled toolbar that replaces the native menu for consistent theming."""
        # Toolbar frame (use navbar main color)
        try:
            toolbar_color = ("#545E56", "#545E56")
            btn_fg = ("#545E56", "#545E56")
            btn_hover = ("#667761", "#667761")
            btn_text = ("#1B1B1E", "#1B1B1E")
            self.toolbar = customtkinter.CTkFrame(self, fg_color=toolbar_color)
            self.toolbar.pack(side="top", fill="x", padx=0, pady=0)

            # Open button
            open_btn = customtkinter.CTkButton(self.toolbar, text="Open", command=self.upload_photo,
                                                fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text)
            open_btn.pack(side="left", padx=(8, 4), pady=6)

            # Save button
            save_btn = customtkinter.CTkButton(self.toolbar, text="Save", command=self.save_image,
                                                fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text)
            save_btn.pack(side="left", padx=4, pady=6)

            # Exit button
            exit_btn = customtkinter.CTkButton(self.toolbar, text="Exit", command=self.quit,
                                                fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text)
            exit_btn.pack(side="left", padx=4, pady=6)

            # Spacer
            spacer = customtkinter.CTkLabel(self.toolbar, text="", fg_color="transparent")
            spacer.pack(side="left", expand=True)

            # Dark mode switch (right-aligned)
            self.dark_switch = customtkinter.CTkSwitch(self.toolbar, text="Dark Mode", command=self.darkMode)
            # initialize switch state based on current appearance
            try:
                self.dark_switch.select() if customtkinter.get_appearance_mode() == 'Dark' else self.dark_switch.deselect()
            except Exception:
                pass
            self.dark_switch.pack(side="right", padx=10, pady=6)

        except Exception as e:
            # If custom toolbar can't be created, fall back to native menu to avoid losing functionality
            print(f"Warning: failed to create CTk toolbar: {e}")
            self._create_native_menu_fallback()

    def _create_native_menu_fallback(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.upload_photo)
        file_menu.add_command(label="Save Image", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        # fallback boolean
        self.darkmode = BooleanVar()
        view_menu.add_checkbutton(label="Dark Mode", onvalue=1, offvalue=0, variable=self.darkmode, command=self.darkMode)
        menubar.add_cascade(label="View", menu=view_menu)
        self.config(menu=menubar)

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            # Load full PIL image and keep original for edits
            pil = Image.open(file_path).convert('RGBA')
            self.original_image = pil.copy()
            # fit image into canvas viewport while preserving aspect
            max_dim = 800
            w, h = pil.size
            scale = min(max_dim / w, max_dim / h, 1.0)
            disp_w, disp_h = int(w * scale), int(h * scale)
            self.display_scale = scale
            self.display_image = pil.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(self.display_image)
            self.canvas.delete("all")
            # configure canvas virtual size and display image at origin
            self.canvas.config(width=min(disp_w, self.winfo_width()//2), height=min(disp_h, self.winfo_height()//2))
            self.canvas_image = self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)
            # Update scrollregion so scrollbars work and show scrollbars if content overflows
            try:
                self.canvas.configure(scrollregion=(0, 0, disp_w, disp_h))
                # show scrollbars if image is larger than canvas viewport
                if disp_h > self.canvas.winfo_height():
                    self.v_scroll.grid()
                else:
                    try:
                        self.v_scroll.grid_remove()
                    except Exception:
                        pass
                if disp_w > self.canvas.winfo_width():
                    self.h_scroll.grid()
                else:
                    try:
                        self.h_scroll.grid_remove()
                    except Exception:
                        pass
            except Exception:
                pass
            # clear regions and show editor
            self.regions = []
            self.selected_region_index = None
            self.show_editor_panel()
            # Bind drag to allow user to add manual regions
            self.canvas.bind('<ButtonPress-1>', self._on_canvas_press)
            self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
            self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
            # TODO: Add image editing tools (blur, redact, etc.)
            # See: https://hackr.io/blog/how-to-create-a-python-image-editor-app

    def save_image(self):
        if not hasattr(self, 'image') or self.image is None:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        export_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if export_path:
            composite_img = self.layer_manager.merge_all(self.image)
            composite_img.save(export_path)
            messagebox.showinfo("Saved", "Image saved successfully.")


    # ------- Editor and region handling -------
    def show_editor_panel(self):
        # Remove placeholder
        for child in self.editor_frame.winfo_children():
            child.destroy()

        # Controls: method, intensity, size, add/remove, listbox of regions, copy/paste
        customtkinter.CTkLabel(self.editor_frame, text='Edit Regions').pack(pady=(8,4))

        customtkinter.CTkLabel(self.editor_frame, text='Redaction method:').pack(anchor='w', padx=8)
        self.method_var = tk.StringVar(value='blur')
        methods = ['blur', 'redact', 'pixelate', 'none']
        # create radio buttons and store them so we can update text color on appearance changes
        self.method_rbs = []
        mode = None
        try:
            mode = customtkinter.get_appearance_mode()
        except Exception:
            mode = 'Light'
        rb_text_color = '#BDB6B5' if mode == 'Dark' else None
        for m in methods:
            rb = customtkinter.CTkRadioButton(self.editor_frame, text=m.title(), variable=self.method_var, value=m, text_color=rb_text_color)
            rb.pack(anchor='w', padx=12, pady=2)
            self.method_rbs.append(rb)

        customtkinter.CTkLabel(self.editor_frame, text='Shape:').pack(anchor='w', padx=8, pady=(8,0))
        self.shape_var = tk.StringVar(value='rectangle')
        shapes = ['rectangle', 'circle', 'oval']
        mode = None
        try:
            mode = customtkinter.get_appearance_mode()
        except Exception:
            mode = 'Light'
        rb_text_color = '#BDB6B5' if mode == 'Dark' else None
        for s in shapes:
            rb = customtkinter.CTkRadioButton(self.editor_frame, text=s.capitalize(), variable=self.shape_var, value=s, text_color=rb_text_color)
            rb.pack(anchor='w', padx=12, pady=2)


        customtkinter.CTkLabel(self.editor_frame, text='Intensity:').pack(anchor='w', padx=8, pady=(8,0))
        self.intensity_var = tk.IntVar(value=10)
        customtkinter.CTkSlider(self.editor_frame, from_=1, to=50, variable=self.intensity_var).pack(fill='x', padx=12)

        customtkinter.CTkLabel(self.editor_frame, text='Size (px padding):').pack(anchor='w', padx=8, pady=(8,0))
        self.size_var = tk.IntVar(value=0)
        customtkinter.CTkSlider(self.editor_frame, from_=0, to=200, variable=self.size_var).pack(fill='x', padx=12)

        # Region list
        customtkinter.CTkLabel(self.editor_frame, text='Regions:').pack(anchor='w', padx=8, pady=(8,0))
        self.region_listbox = tk.Listbox(self.editor_frame, height=6)
        self.region_listbox.pack(fill='both', padx=8, pady=4)
        self.region_listbox.bind('<<ListboxSelect>>', self._on_region_select)

        # removed 'Add from AI' and 'Delete' buttons per user request

        cp_frame = customtkinter.CTkFrame(self.editor_frame, fg_color='transparent')
        cp_frame.pack(fill='x', padx=8, pady=6)
        customtkinter.CTkButton(cp_frame, text='Copy Settings', command=self._copy_region_settings).pack(side='left', padx=4)
        customtkinter.CTkButton(cp_frame, text='Paste to Selected', command=self._paste_region_settings).pack(side='left', padx=4)
        customtkinter.CTkButton(cp_frame, text='Paste to All', command=self._paste_to_all).pack(side='left', padx=4)
        customtkinter.CTkButton(self.editor_frame, text='Remove Metadata', command=self._remove_metadata).pack(pady=6)

        customtkinter.CTkButton(self.editor_frame, text='Delete Selected', command=self._delete_selected_layer).pack(pady=6)
 
        # draw existing regions if any
        self._refresh_region_list()

    def _on_editor_mousewheel(self, event):
        """Scroll the editor_inner when the mousewheel is used over the settings area."""
        try:
            delta = int(event.delta)
        except Exception:
            try:
                delta = 120 if event.delta > 0 else -120
            except Exception:
                delta = 0
        # Scroll up for positive delta
        try:
            if delta > 0:
                if hasattr(self, 'editor_canvas'):
                    self.editor_canvas.yview_scroll(-1, 'units')
                else:
                    # CTkScrollableFrame will respond to yview_scroll as well
                    try:
                        self.editor_inner.yview_scroll(-1, 'units')
                    except Exception:
                        pass
            else:
                if hasattr(self, 'editor_canvas'):
                    self.editor_canvas.yview_scroll(1, 'units')
                else:
                    try:
                        self.editor_inner.yview_scroll(1, 'units')
                    except Exception:
                        pass
        except Exception:
            pass

    def _add_ai_regions(self):
        # Placeholder for backend-provided regions; here we add a sample region in center
        if not hasattr(self, 'display_image'):
            return
        w, h = self.display_image.size
        box = (w//4, h//4, w*3//4, h*3//4)
        self.regions.append({'coords': box, 'method': 'blur', 'intensity': 10, 'size': 0})
        self._refresh_region_list()
        self._draw_regions()

    # Canvas mouse handlers for manual region selection
    def _on_canvas_press(self, event):
        self._drag_start = (event.x, event.y)
        # create temporary rectangle
        self._temp_rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red')

    def _on_canvas_drag(self, event):
        if hasattr(self, '_temp_rect'):
            x0, y0 = self._drag_start
            self.canvas.coords(self._temp_rect, x0, y0, event.x, event.y)

    def _on_canvas_release(self, event):
        if hasattr(self, '_temp_rect'):
            x0, y0 = self._drag_start
            x1, y1 = event.x, event.y
            self.canvas.delete(self._temp_rect)
            self._temp_rect = None
            x0, x1 = sorted((max(x0, 0), max(x1, 0)))
            y0, y1 = sorted((max(y0, 0), max(y1, 0)))
            if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
                return
            scale = getattr(self, 'display_scale', 1.0)
            box = (int(x0 / scale), int(y0 / scale), int(x1 / scale), int(y1 / scale))
            shape = getattr(self, 'shape_var', tk.StringVar(value='rectangle')).get()
            region = Layer(shape=shape, coords=box,
                        method=self.method_var.get(),
                        intensity=self.intensity_var.get(),
                        size=self.size_var.get())
            self.layer_manager.add_layer(region)
            self._refresh_region_list()
            self._draw_regions()


    def _refresh_region_list(self):
        self.region_listbox.delete(0, 'end')
        for i, l in enumerate(self.layer_manager.layers):
            self.region_listbox.insert('end', f"{i + 1}. {l.method} {l.shape} {l.coords}")


    def _on_region_select(self, event):
        sel = self.region_listbox.curselection()
        if not sel:
            self.selected_layer = None
            return
        self.selected_layer = sel[0]
        layer = self.layer_manager.layers[self.selected_layer]
        try:
            self.method_var.set(layer.method)
            self.intensity_var.set(layer.intensity)
            self.size_var.set(layer.size)
            self.shape_var.set(layer.shape)
        except Exception:
            pass
        self._draw_regions()


        def _delete_selected_region(self):
            if self.selected_region_index is None:
                return
            del self.regions[self.selected_region_index]
            self.selected_region_index = None
            self._refresh_region_list()
            self._draw_regions()

    def _copy_region_settings(self):
        if self.selected_layer is None:
            return
        self.region_clipboard = dict(vars(self.layer_manager.layers[self.selected_layer]))

    def _paste_region_settings(self):
        if self.selected_layer is None or not hasattr(self, 'region_clipboard') or self.region_clipboard is None:
            return
        layer = self.layer_manager.layers[self.selected_layer]
        for k in ('method', 'intensity', 'size'):
            if k in self.region_clipboard:
                setattr(layer, k, self.region_clipboard[k])
        self._refresh_region_list()
        self._draw_regions()


    def _paste_to_all(self):
        if self.region_clipboard is None:
            return
        for r in self.regions:
            for k in ('method','intensity','size'):
                if k in self.region_clipboard:
                    r[k] = self.region_clipboard[k]
        self._refresh_region_list()

    def _apply_to_selected(self):
        if self.selected_layer is None or not hasattr(self, 'image') or self.image is None:
            messagebox.showwarning("No selection", "Select a region first!")
            return
        layer = self.layer_manager.layers[self.selected_layer]
        self.image = layer.apply(self.image)
        self._update_display_image()


    def _draw_regions(self):
        # Start with displayed image base
        base = self.display_image.copy()
        # Composite all but selected onto base
        for i, layer in enumerate(self.layer_manager.layers):
            if i == self.selected_layer:
                continue
            base = layer.apply(base)
        # Update canvas image with composite
        self.tk_image = ImageTk.PhotoImage(base)
        self.canvas.itemconfig(self.canvas_image, image=self.tk_image)
        # Draw outline of selected with yellow highlight
        self.canvas.delete('region_overlay')
        if self.selected_layer is not None and 0 <= self.selected_layer < len(self.layer_manager.layers):
            layer = self.layer_manager.layers[self.selected_layer]
            scale = getattr(self, 'display_scale', 1.0)
            x1, y1, x2, y2 = [int(v * scale) for v in layer.coords]
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='yellow', width=3, tags='region_overlay')


    def _delete_selected_layer(self):
        if self.selected_layer is None:
            return
        self.layer_manager.remove_layer(self.selected_layer)
        self.selected_layer = None
        self._refresh_region_list()
        self._draw_regions()


    def _apply_redaction_to_image(self, region):
        # Work on the original image then later update display
        pil = getattr(self, 'original_image', None)
        if pil is None:
            return
        x1,y1,x2,y2 = region['coords']
        pad = int(region.get('size',0))
        x1 = max(0, x1-pad); y1 = max(0, y1-pad); x2 = min(pil.width, x2+pad); y2 = min(pil.height, y2+pad)
        box = (x1,y1,x2,y2)
        roi = pil.crop(box)
        method = region.get('method','blur')
        intensity = int(region.get('intensity',10))
        if method == 'blur':
            from PIL import ImageFilter
            blurred = roi.filter(ImageFilter.GaussianBlur(radius=intensity))
            pil.paste(blurred, box)
        elif method == 'redact':
            fill = (0,0,0,255)
            red = Image.new('RGBA', roi.size, fill)
            pil.paste(red, box)
        elif method == 'pixelate':
            # downscale/upscale
            small = roi.resize((max(1, roi.width//intensity), max(1, roi.height//intensity)), Image.NEAREST)
            pixel = small.resize(roi.size, Image.NEAREST)
            pil.paste(pixel, box)
        elif method == 'none':
            pass
        # update original_image
        self.original_image = pil

    def _update_display_image(self):
        pil = getattr(self, 'original_image', None)
        if pil is None:
            return
        scale = getattr(self, 'display_scale', 1.0)
        disp_w = int(pil.width*scale)
        disp_h = int(pil.height*scale)
        disp = pil.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.display_image = disp
        self.tk_image = ImageTk.PhotoImage(disp)
        self.canvas.itemconfigure(self.canvas_image, image=self.tk_image)
        # update scrollregion after resizing
        try:
            self.canvas.configure(scrollregion=(0, 0, disp_w, disp_h))
        except Exception:
            pass
        self._draw_regions()

    def _on_mousewheel(self, event):
        try:
            focused = self.focus_get()
            if focused != self.canvas:
                return
        except Exception:
            pass

        delta = 0
        try:
            delta = int(event.delta)
        except Exception:
            try:
                delta = 120 if event.delta > 0 else -120
            except Exception:
                delta = 0

        ctrl = (event.state & 0x0004) != 0

        if ctrl:
            if delta > 0:
                self._zoom_canvas(1.1)
            else:
                self._zoom_canvas(0.9)
        else:
            # Vertical scrolling
            try:
                if event.state & 0x0001:  # Shift pressed for horizontal scroll
                    if delta > 0:
                        self.canvas.xview_scroll(-1, 'units')
                    else:
                        self.canvas.xview_scroll(1, 'units')
                else:
                    if delta > 0:
                        self.canvas.yview_scroll(-1, 'units')
                    else:
                        self.canvas.yview_scroll(1, 'units')
            except Exception:
                pass

    def _zoom_canvas(self, factor: float):
        """Zoom the displayed image by adjusting display_scale and updating the display.
        Factor >1 to zoom in, <1 to zoom out.
        """
        try:
            old_scale = getattr(self, 'display_scale', 1.0)
            new_scale = max(0.05, min(5.0, old_scale * factor))
            # Avoid unnecessary work
            if abs(new_scale - old_scale) < 1e-6:
                return
            self.display_scale = new_scale
            # update the canvas image based on new scale
            self._update_display_image()
        except Exception:
            pass

    def _remove_metadata(self):
        pil = getattr(self, 'original_image', None)
        if pil is None:
            return
        data = list(pil.getdata())
        clean = Image.new(pil.mode, pil.size)
        clean.putdata(data)
        self.original_image = clean
        self._update_display_image()

    def darkMode(self):
        # Robust handler: support CTkSwitch (self.dark_switch) or BooleanVar (self.darkmode)
        try:
            # Save current geometry so we can restore it after appearance changes
            try:
                _saved_geo = self.geometry()
            except Exception:
                _saved_geo = None
            val = None
            # Priority: CTkSwitch from toolbar
            if hasattr(self, 'dark_switch') and self.dark_switch is not None:
                try:
                    val = self.dark_switch.get()
                except Exception:
                    # CTkSwitch may not expose get(); infer from appearance
                    try:
                        val = 1 if customtkinter.get_appearance_mode() == 'Dark' else 0
                    except Exception:
                        val = None
            # Fallback: BooleanVar (native menu fallback)
            if val is None and hasattr(self, 'darkmode'):
                try:
                    val = self.darkmode.get()
                except Exception:
                    val = None

            # If still unknown, toggle current appearance
            if val is None:
                current = None
                try:
                    current = customtkinter.get_appearance_mode()
                except Exception:
                    pass
                if current == 'Dark':
                    customtkinter.set_appearance_mode('Light')
                    val = 0
                else:
                    customtkinter.set_appearance_mode('Dark')
                    val = 1
            else:
                # Apply based on val
                if val:
                    customtkinter.set_appearance_mode('Dark')
                else:
                    customtkinter.set_appearance_mode('Light')

            # Update non-CTk widgets and header color based on resulting appearance
            if customtkinter.get_appearance_mode() == 'Dark':
                self.config(bg=self.theme_colors.get('dark_bg', '#1B1B1E'))
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg=self.theme_colors.get('dark_bg', '#1B1B1E'))
                try:
                    self.header_label.configure(fg_color=(self.welcome_colors[1]))
                except Exception:
                    pass
            else:
                self.config(bg=self.theme_colors.get('light_bg', '#EAE1DF'))
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg=self.theme_colors.get('light_bg', '#EAE1DF'))
                try:
                    self.header_label.configure(fg_color=(self.welcome_colors[0]))
                except Exception:
                    pass

            # Sync widget states so UI reflects mode
            if hasattr(self, 'dark_switch'):
                try:
                    if customtkinter.get_appearance_mode() == 'Dark':
                        self.dark_switch.select()
                    else:
                        self.dark_switch.deselect()
                except Exception:
                    pass
            if hasattr(self, 'darkmode'):
                try:
                    self.darkmode.set(1 if customtkinter.get_appearance_mode() == 'Dark' else 0)
                except Exception:
                    pass
            # Restore previous geometry (prevent theme toggle from recentring/resizing the window)
            try:
                if _saved_geo:
                    # reapply saved geometry
                    self.geometry(_saved_geo)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Error', f"An error occurred while toggling dark mode:\n{e}")

    def apply_initial_appearance(self):
        """Apply appearance colors to non-CTk widgets and header at startup so the UI matches the current mode."""
        try:
            mode = None
            try:
                mode = customtkinter.get_appearance_mode()
            except Exception:
                mode = 'Light'

            if mode == 'Dark':
                self.config(bg=self.theme_colors.get('dark_bg', '#1B1B1E'))
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg=self.theme_colors.get('dark_bg', '#1B1B1E'))
                try:
                    self.header_label.configure(fg_color=(self.welcome_colors[1]))
                except Exception:
                    pass
            else:
                self.config(bg=self.theme_colors.get('light_bg', '#EAE1DF'))
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.config(bg=self.theme_colors.get('light_bg', '#EAE1DF'))
                try:
                    self.header_label.configure(fg_color=(self.welcome_colors[0]))
                except Exception:
                    pass
        except Exception:
            pass
if __name__ == "__main__":
    # The try, finnally block is used to provide DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)

    finally:
        app = ImageRedactorApp()
        app.mainloop()
