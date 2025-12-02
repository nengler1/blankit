import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter
from layer_manager import LayerManager
from editor_tools import EditorTools
import os



class ImageRedactorApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.theme_colors = {
            "dark_bg": "#1B1B1E",
            "light_bg": "#EAE1DF",
        }
        self.title("BlankIt")
        self.geometry("900x600")
        self.layer_manager = LayerManager()
        self.editor_tools = EditorTools(self.layer_manager, self)
        self.selected_layer = None
        self._handles = {}
        self._move_handle_id = None
        self._moving_group = False
        self.image = None
        self.original_image = None
        self.display_image = None
        self.display_scale = 1.0
        self.canvas_image_id = None
        self.live_composite_image = None
        self.live_tk_image = None
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
        
        btn_ai = customtkinter.CTkButton(
            toolbar, 
            text="AI Redact", 
            fg_color="#4A7C59", 
            hover_color="#5A8C69", 
            text_color=btn_text, 
            command=self.run_ai_redaction
        )
        btn_ai.pack(side="left", padx=5, pady=5)

        btn_exit = customtkinter.CTkButton(toolbar, text="Exit", fg_color=btn_fg, hover_color=btn_hover, text_color=btn_text, command=self.quit)
        btn_exit.pack(side="left", padx=5, pady=5)


        self.dark_mode_switch = customtkinter.CTkSwitch(toolbar, text="Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_switch.pack(side="right", padx=5, pady=5)

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
        # Clear previous widgets
        for child in self.editor_inner.winfo_children():
            child.destroy()

        mode = customtkinter.get_appearance_mode()  # Assume no errors here

        if mode == 'Dark':
            bg_color = self.theme_colors.get('dark_bg', '#1B1B1E')
            text_color = "#EAE1DF"
        else:
            bg_color = self.theme_colors.get('light_bg', '#EAE1DF')
            text_color = "#1B1B1E"

        self.editor_inner.configure(fg_color=bg_color)  # Background for editor panel

        # Helper to create labels with explicit color
        def make_label(text):
            return customtkinter.CTkLabel(self.editor_inner, text=text, text_color=text_color)

        # Helper to create radio buttons with explicit color
        def make_radiobutton(text, var, val):
            return customtkinter.CTkRadioButton(self.editor_inner, text=text, variable=var, value=val, text_color=text_color)

        #Selector for selection or drawing mode
        self.edit_mode_var = tk.StringVar(value="draw")  # default to draw

        mode_frame = customtkinter.CTkFrame(self.editor_inner, fg_color="transparent")
        mode_frame.pack(fill="x", padx=8, pady=(8, 4))

        mode_label = customtkinter.CTkLabel(
            mode_frame,
            text="Mode:",
            text_color=text_color
        )
        mode_label.pack(side="left", padx=(0, 8))

        self.mode_segmented = customtkinter.CTkSegmentedButton(
            mode_frame,
            values=["select", "draw"],
            command=self._on_mode_change
        )
        self.mode_segmented.pack(side="left", fill="x", expand=True)
        self.mode_segmented.set("draw")

        # Build UI controls
        make_label('Edit Regions').pack(pady=(8,4))

        make_label('Redaction method:').pack(anchor='w', padx=8)
        self.method_var = tk.StringVar(value='blur')
        methods = ['blur', 'redact', 'pixelate', 'none']
        for m in methods:
            rb = make_radiobutton(m.title(), self.method_var, m)
            rb.pack(anchor='w', padx=12, pady=2)

        make_label('Shape:').pack(anchor='w', padx=8, pady=(8,0))
        self.shape_var = tk.StringVar(value='rectangle')
        shapes = ['rectangle', 'circle', 'oval']
        for s in shapes:
            rb = make_radiobutton(s.capitalize(), self.shape_var, s)
            rb.pack(anchor='w', padx=12, pady=2)

        make_label('Intensity:').pack(anchor='w', padx=8, pady=(8,0))
        self.intensity_var = tk.IntVar(value=10)
        self.intensity_var.trace_add('write', lambda *args: self._on_layer_change())
        customtkinter.CTkSlider(self.editor_inner, from_=1, to=50, variable=self.intensity_var).pack(fill='x', padx=12)

        make_label('Size (px padding):').pack(anchor='w', padx=8, pady=(8,0))
        self.size_var = tk.IntVar(value=0)
        self.size_var.trace_add('write', lambda *args: self._on_layer_change())
        customtkinter.CTkSlider(self.editor_inner, from_=0, to=200, variable=self.size_var).pack(fill='x', padx=12)

        make_label('Regions:').pack(anchor='w', padx=8, pady=(8, 0))

        # container for region rows
        self.region_container = customtkinter.CTkScrollableFrame(
            self.editor_inner,
            fg_color=bg_color  # match background
        )
        self.region_container.pack(fill='both', expand=True, padx=8, pady=4)

        # build rows
        self._build_region_rows()

    def _build_region_rows(self):
        """Rebuild region rows with dropdown details."""
        # Clear existing children
        for child in self.region_container.winfo_children():
            child.destroy()

        scale = getattr(self, "display_scale", 1.0) or 1.0

        for idx, layer in enumerate(self.layer_manager.layers):
            row_frame = customtkinter.CTkFrame(
                self.region_container,
                fg_color="transparent"
            )
            row_frame.pack(fill="x", pady=2)

            # Header line: index + summary
            summary = f"{idx+1}: {layer.shape} - {layer.method}"

            # Determine if this index is selected
            is_selected = (
                hasattr(self.editor_tools, "selected_regions")
                and idx in self.editor_tools.selected_regions
            )

            if is_selected:
                row_fg = "#667761"   # highlighted background
                row_text = "#EAE1DF" # light text
            else:
                row_fg = "#545E56"
                row_text = "#1B1B1E"

            header_btn = customtkinter.CTkButton(
                row_frame,
                text=summary,
                fg_color=row_fg,
                hover_color="#667761",
                text_color=row_text,
                command=lambda i=idx: self.editor_tools.select_region(i),
            )
            header_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))


            # Toggle button to show/hide details
            toggle_btn = customtkinter.CTkButton(
                row_frame,
                text="⋯",
                width=32,
                fg_color="#545E56",
                hover_color="#667761"
            )
            toggle_btn.pack(side="right")

            # Details frame (start hidden)
            details = customtkinter.CTkFrame(
                self.region_container,
                fg_color=self.theme_colors.get(
                    'dark_bg' if customtkinter.get_appearance_mode() == 'Dark' else 'light_bg',
                    "#1B1B1E"
                )
            )

            # Coordinates (canvas units)
            x1, y1, x2, y2 = layer.coords
            cx1, cy1 = int(x1 * scale), int(y1 * scale)
            cx2, cy2 = int(x2 * scale), int(y2 * scale)
            coord_text = f"Coords: ({cx1}, {cy1}) → ({cx2}, {cy2})"

            coord_label = customtkinter.CTkLabel(
                details,
                text=coord_text
            )
            coord_label.pack(anchor="w", padx=8, pady=(4, 0))

            # Intensity only for blur/pixelate
            if layer.method in ("blur", "pixelate"):
                inten_label = customtkinter.CTkLabel(
                    details,
                    text=f"Intensity: {layer.intensity}"
                )
                inten_label.pack(anchor="w", padx=8, pady=(2, 0))

            # Buttons row
            btn_row = customtkinter.CTkFrame(details, fg_color="transparent")
            btn_row.pack(fill="x", padx=4, pady=4)

            copy_btn = customtkinter.CTkButton(
                btn_row,
                text="Copy",
                width=60,
                fg_color="#545E56",
                hover_color="#667761",
                command=lambda i=idx: self.editor_tools.copy_region(i)
            )
            copy_btn.pack(side="left", padx=4)

            delete_btn = customtkinter.CTkButton(
                btn_row,
                text="Delete",
                width=70,
                fg_color="#545E56",
                hover_color="#667761",
                command=lambda i=idx: self.editor_tools.delete_region(i)
            )
            delete_btn.pack(side="left", padx=4)

            # Toggle behavior
            def toggle_details(frame=details):
                if frame.winfo_ismapped():
                    frame.pack_forget()
                else:
                    frame.pack(fill="x", padx=12, pady=(0, 4))

            toggle_btn.configure(command=toggle_details)

    def _on_mode_change(self, value: str):
        """Update editor tools mode when segmented button changes."""
        if hasattr(self, "edit_mode_var"):
            self.edit_mode_var.set(value)
        if hasattr(self, "editor_tools"):
            self.editor_tools.set_mode(value)


    def _on_region_select(self, event):
        """Handle selection changes in the regions Listbox."""
        if not hasattr(self, "region_listbox"):
            return

        selection = self.region_listbox.curselection()
        if not selection:
            # Nothing selected
            self.selected_layer = None
            self.editor_tools.clear_selection()
            return

        idx = selection[0]
        self.selected_layer = idx

        # Inform editor tools about the selected region, if it has such a method
        if hasattr(self.editor_tools, "select_region"):
            self.editor_tools.select_region(idx)

    def _refresh_region_list(self):
        """Rebuild the regions panel from LayerManager.layers."""
        if hasattr(self, "region_container"):
            self._build_region_rows()

    
    def update_live_preview(self):
        """Create and display the live preview image on the canvas."""
        if self.original_image is None:
            return

        scale = getattr(self, "display_scale", 1.0) or 1.0

        # Create a preview composited image scaled to display size
        preview_img = self.layer_manager.create_preview(self.original_image, scale)

        # Keep a reference to prevent GC
        self.live_composite_image = preview_img
        self.live_tk_image = ImageTk.PhotoImage(preview_img)

        # Update or create image on canvas
        if hasattr(self, 'canvas_image_id') and self.canvas_image_id:
            self.canvas.itemconfig(self.canvas_image_id, image=self.live_tk_image)
        else:
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.live_tk_image)

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_layer_change(self):
        """Called when layers change to update live preview."""
        self.update_live_preview()


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

        ctrl = (event.state & 0x0004) != 0  # Check if Ctrl key pressed

        if ctrl:
            if delta > 0:
                self._zoom_canvas(1.1)
            else:
                self._zoom_canvas(0.9)
        else:
            # Vertical or horizontal scrolling
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

    def run_ai_redaction(self):
        """Run AI detection and automatically add detected regions as layers."""
        if self.original_image is None:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return
        
        try:
            from main import faces_boxes, plates_boxes  # Import backend functions
            
            # Save temp image path for AI processing
            temp_path = "temp_ai_input.jpg"
            self.original_image.save(temp_path)
            
            # Run face detection
            print("Running face detection...")
            faces_img_cv, face_coords = faces_boxes(temp_path)
            
            # Run plate detection on face-processed image
            print("Running license plate detection...")
            _, plate_coords = plates_boxes(faces_img_cv)
            
            # Combine all detected regions
            all_regions = face_coords + plate_coords
            
            if not all_regions:
                messagebox.showinfo("AI Detection", "No sensitive regions detected.")
                return
            
            # Clear existing layers
            self.layer_manager.clear_layers()
            self.editor_tools.clear_selection()
            
            # Add each detected region as a Layer
            default_method = self.method_var.get() if hasattr(self, 'method_var') else 'redact'
            default_shape = self.shape_var.get() if hasattr(self, 'shape_var') else 'rectangle'
            
            for coord_pair in all_regions:
                (left, top), (right, bottom) = coord_pair
                # Convert to (x1,y1,x2,y2) format for Layer
                coords = (left, top, right, bottom)
                
                new_layer = Layer(
                    shape=default_shape,
                    coords=coords,
                    method=default_method,
                    intensity=10,
                    size=0
                )
                self.layer_manager.add_layer(new_layer)
            
            print(f"AI added {len(all_regions)} detected regions as editable layers")
            messagebox.showinfo("AI Detection", f"Added {len(all_regions)} detected regions!")
            
            # Refresh UI and live preview
            self.show_editor_panel()
            self.update_live_preview()
            
        except ImportError:
            messagebox.showerror("Missing Backend", "main.py not found or missing dependencies (face_recognition, opencv-python)")
        except Exception as e:
            messagebox.showerror("AI Error", f"AI detection failed: {str(e)}")
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    app = ImageRedactorApp()
    app.mainloop()
