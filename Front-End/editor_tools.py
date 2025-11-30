import tkinter as tk
from layer_manager import Layer

HANDLE_SIZE = 8
HANDLE_TAG = "resize_handle"
REGION_TAG = "region_overlay"

class EditorTools:
    def __init__(self, layer_manager, app):
        self.layer_manager = layer_manager
        self.app = app
        self.selected_region = None
        self._dragging = False
        self._resizing = False
        self._resize_handle = None
        self._drag_start_pos = None
        self._orig_coords = None
        self._handles = {}
        self._creating = False
        self._creation_start = None
        self._temp_rect = None

    def clear_selection(self):
        self.selected_region = None

    def select_region(self, index):
        """Called from window when user selects a region in the list."""
        if 0 <= index < len(self.layer_manager.layers):
            self.selected_region = index
        else:
            self.selected_region = None

        # Redraw overlays on the app's canvas
        if hasattr(self.app, "canvas"):
            self._redraw(self.app.canvas)


    def on_mouse_down(self, event):
        canvas = event.widget
        x, y = event.x, event.y

        handle_id, handle_dir = self._get_handle_at_pos(canvas, x, y)
        if handle_id:
            self._resizing = True
            self._resize_handle = handle_dir
            self._drag_start_pos = (x, y)
            if self.selected_region is not None:
                self._orig_coords = list(self.layer_manager.layers[self.selected_region].coords)
            return

        idx = self._get_region_at_pos(x, y)
        if idx is not None:
            self.selected_region = idx
            self._dragging = True
            self._drag_start_pos = (x, y)
            self._orig_coords = list(self.layer_manager.layers[idx].coords)
            self._redraw(canvas)
            return

        # Start creating new region
        self._creating = True
        self._creation_start = (x, y)
        self._temp_rect = canvas.create_rectangle(x, y, x, y, outline='red')

    def on_mouse_move(self, event):
        canvas = event.widget
        x, y = event.x, event.y

        if self._creating:
            x0, y0 = self._creation_start
            canvas.coords(self._temp_rect, x0, y0, x, y)

        elif self._dragging and self.selected_region is not None:
            dx = x - self._drag_start_pos[0]
            dy = y - self._drag_start_pos[1]
            # Update region position
            layer = self.layer_manager.layers[self.selected_region]
            x1, y1, x2, y2 = self._orig_coords
            new_coords = (x1 + dx, y1 + dy, x2 + dx, y2 + dy)
            layer.coords = new_coords
            self._redraw(canvas)

        elif self._resizing and self.selected_region is not None:
            dx = x - self._drag_start_pos[0]
            dy = y - self._drag_start_pos[1]
            layer = self.layer_manager.layers[self.selected_region]
            x1, y1, x2, y2 = self._orig_coords
            dir = self._resize_handle
            nx1, ny1, nx2, ny2 = x1, y1, x2, y2
            if 'n' in dir:
                ny1 += dy
            if 's' in dir:
                ny2 += dy
            if 'w' in dir:
                nx1 += dx
            if 'e' in dir:
                nx2 += dx
            
            layer.coords = (nx1, ny1, nx2, ny2)
            self._redraw(canvas)

    def on_mouse_up(self, event):
        canvas = event.widget

        if self._creating:
            self._creating = False
            canvas.delete(self._temp_rect)
            self._temp_rect = None
            x0, y0 = self._creation_start
            x1, y1 = event.x, event.y
            x0, x1 = sorted([x0, x1])
            y0, y1 = sorted([y0, y1])
            if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
                return
            scale = getattr(self.app, "display_scale", 1.0) or 1.0
            box = (x0 / scale, y0 / scale, x1 / scale, y1 / scale)
            # Replace below with code to create and add Layer object properly
            new_region = self._create_layer(box)
            self.layer_manager.add_layer(new_region)
            self.selected_region = len(self.layer_manager.layers) - 1
            self._redraw(canvas)
            
            if hasattr(self.app, "_refresh_region_list"):
                self.app._refresh_region_list()
                
            return

        if self._dragging or self._resizing:
            self._dragging = False
            self._resizing = False
            self._resize_handle = None
            self._drag_start_pos = None
            self._orig_coords = None

    def _get_handle_at_pos(self, canvas, x, y):
        ids = canvas.find_overlapping(x, y, x, y)
        for id_ in ids:
            if id_ in self._handles:
                return id_, self._handles[id_]
        return None, None

    def _get_region_at_pos(self, x, y):
        # Return first region containing point (x,y) (using layer_manager)
        for i, layer in enumerate(self.layer_manager.layers):
            x1, y1, x2, y2 = layer.coords
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def _draw_resize_handles(self, canvas, region):
        if region is None:
            return

        scale = getattr(self.app, "display_scale", 1.0) or 1.0
        x1, y1, x2, y2 = region.coords
        x1, y1, x2, y2 = [int(c * scale) for c in (x1, y1, x2, y2)]

        handle_positions = {
            'nw': (x1, y1),
            'n':  ((x1 + x2) // 2, y1),
            'ne': (x2, y1),
            'e':  (x2, (y1 + y2) // 2),
            'se': (x2, y2),
            's':  ((x1 + x2) // 2, y2),
            'sw': (x1, y2),
            'w':  (x1, (y1 + y2) // 2),
        }

        self._handles.clear()
        for direction, (hx, hy) in handle_positions.items():
            handle_id = canvas.create_rectangle(
                hx - HANDLE_SIZE // 2, hy - HANDLE_SIZE // 2,
                hx + HANDLE_SIZE // 2, hy + HANDLE_SIZE // 2,
                fill='yellow', outline='black', tags=HANDLE_TAG,
            )
            self._handles[handle_id] = direction

    def _create_layer(self, box):
        # Default fallbacks if UI not yet available
        shape = 'rectangle'
        method = 'blur'
        intensity = 10
        size = 0

        # Pull values from window/editor panel if they exist
        if hasattr(self.app, "shape_var"):
            shape = self.app.shape_var.get()
        if hasattr(self.app, "method_var"):
            method = self.app.method_var.get()
        if hasattr(self.app, "intensity_var"):
            intensity = int(self.app.intensity_var.get())
        if hasattr(self.app, "size_var"):
            size = int(self.app.size_var.get())
        return Layer(shape=shape, coords=box, method=method, intensity=intensity, size=size)

    def _redraw(self, canvas):
        """Redraw all region overlays on the given canvas."""
        canvas.delete(REGION_TAG)
        canvas.delete(HANDLE_TAG)

        scale = getattr(self.app, "display_scale", 1.0) or 1.0

        for idx, layer in enumerate(self.layer_manager.layers):
            x1, y1, x2, y2 = layer.coords
            # convert from image coords to canvas coords
            cx1, cy1 = x1 * scale, y1 * scale
            cx2, cy2 = x2 * scale, y2 * scale

            if layer.shape in ("circle", "oval"):
                canvas.create_oval(
                    cx1, cy1, cx2, cy2,
                    outline="red",
                    width=2,
                    tags=REGION_TAG,
                )
            else:
                canvas.create_rectangle(
                    cx1, cy1, cx2, cy2,
                    outline="red",
                    width=2,
                    tags=REGION_TAG,
                )

        if (
            self.selected_region is not None
            and 0 <= self.selected_region < len(self.layer_manager.layers)
        ):
            self._draw_resize_handles(canvas, self.layer_manager.layers[self.selected_region])

    def copy_region(self, index):
        """Duplicate a region and add it as a new layer."""
        if 0 <= index < len(self.layer_manager.layers):
            src = self.layer_manager.layers[index]
            # Simple copy; you can offset coords if desired
            new_layer = Layer(
                shape=src.shape,
                coords=src.coords,
                method=src.method,
                intensity=src.intensity,
                size=src.size,
            )
            self.layer_manager.add_layer(new_layer)
            self.selected_region = len(self.layer_manager.layers) - 1

            if hasattr(self.app, "canvas"):
                self._redraw(self.app.canvas)
            if hasattr(self.app, "_refresh_region_list"):
                self.app._refresh_region_list()

    def delete_region(self, index=None):
        """Delete the given region or the currently selected one."""
        # If a specific index was passed (from the UI), use that
        if index is not None:
            target = index
        else:
            target = self.selected_region

        if target is None:
            return

        if 0 <= target < len(self.layer_manager.layers):
            self.layer_manager.remove_layer(target)

            # Fix up selected_region after deletion
            if self.selected_region is not None:
                if self.selected_region == target:
                    self.selected_region = None
                elif self.selected_region > target:
                    self.selected_region -= 1

            # Redraw overlays and refresh list
            if hasattr(self.app, "canvas"):
                self._redraw(self.app.canvas)
            if hasattr(self.app, "_refresh_region_list"):
                self.app._refresh_region_list()



    def circle_region(self):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.shape = 'circle' if layer.shape != 'circle' else 'rectangle'
            # This should handle drawing circles on the canvas to redact things within that circle. When drawn, it should be added to the layers and should be editable when selected.

    def rectangle_region(self):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.shape = 'rectangle' if layer.shape != 'rectangle' else 'circle'

    def set_blur_method(self):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.method = 'blur'

    def set_pixelate_method(self):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.method = 'pixelate'

    def set_redact_method(self):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.method = 'redact'

    def set_intensity(self, intensity):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.intensity = intensity

    def set_size(self, size):
        if self.selected_region is not None:
            layer = self.layer_manager.layers[self.selected_region]
            layer.size = size

    def clear_all_regions(self):
        self.layer_manager.clear_layers()
        self.selected_region = None
