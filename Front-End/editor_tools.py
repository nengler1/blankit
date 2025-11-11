import tkinter as tk

HANDLE_SIZE = 8
HANDLE_TAG = "resize_handle"
REGION_TAG = "region_overlay"

class EditorTools:
    def __init__(self, layer_manager):
        self.layer_manager = layer_manager
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
            scale = 1 # You will need to provide display_scale or original_image size here
            box = (x0/scale, y0/scale, x1/scale, y1/scale)
            # Replace below with code to create and add Layer object properly
            new_region = self._create_layer(box)
            self.layer_manager.add_layer(new_region)
            self.selected_region = len(self.layer_manager.layers) - 1
            self._redraw(canvas)
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
        scale = 1  # Or get actual display_scale
        x1, y1, x2, y2 = [int(c * scale) for c in region.coords]
        handle_positions = {
            'nw': (x1, y1),
            'n':  ((x1 + x2)//2, y1),
            'ne': (x2, y1),
            'e':  (x2, (y1 + y2)//2),
            'se': (x2, y2),
            's':  ((x1 + x2)//2, y2),
            'sw': (x1, y2),
            'w':  (x1, (y1 + y2)//2),
        }
        self._handles.clear()
        for direction, (hx, hy) in handle_positions.items():
            handle_id = canvas.create_rectangle(
                hx - HANDLE_SIZE//2, hy - HANDLE_SIZE//2,
                hx + HANDLE_SIZE//2, hy + HANDLE_SIZE//2,
                fill='yellow', outline='black', tags=HANDLE_TAG)
            self._handles[handle_id] = direction

    def _redraw(self, canvas):
        # Code to redraw all layers and overlays on the canvas
        canvas.delete(REGION_TAG)
        for layer in self.layer_manager.layers:
            # Apply each layer’s effect on base image and render overlay
            pass  # Implement composite drawing logic here

    def _create_layer(self, box):
        # Creates a new Layer instance with default settings
        shape = 'rectangle'  # Or get from UI state
        return Layer(shape=shape, coords=box, method='blur', intensity=10, size=0)
