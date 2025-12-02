import tkinter as tk
from layer_manager import Layer

HANDLE_SIZE = 10
HANDLE_TAG = "resize_handle"
REGION_TAG = "region_overlay"
MOVE_HANDLE_TAG = "move_handle"

class EditorTools:
    def __init__(self, layer_manager, app):
        self.layer_manager = layer_manager
        self.app = app
        self.selected_region = None
        self.selected_region = None         
        self.selected_regions = []
        self._mode = "draw" # can be changed to "edit" as needed
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
        self.selected_regions = []
        if hasattr(self.app, "canvas"):
            self.notify_layer_change()


    def select_region(self, index):
        if 0 <= index < len(self.layer_manager.layers):
            self.selected_region = index
            self.selected_regions = [index]
        else:
            self.selected_region = None
            self.selected_regions = []

        if hasattr(self.app, "canvas"):
            self.notify_layer_change()
        if hasattr(self.app, "_refresh_region_list"):
            self.app._refresh_region_list()


            # Redraw overlays on the app's canvas
            if hasattr(self.app, "canvas"):
                self.notify_layer_change()

    def set_mode(self, mode: str):
        """Set interaction mode: 'select' or 'draw'."""
        if mode in ("select", "draw"):
            self._mode = mode


    def on_mouse_down(self, event):
        canvas = event.widget
        x, y = event.x, event.y

        # ---------- COMMON: check resize handles first ----------
        handle_id, handle_dir = self._get_handle_at_pos(canvas, x, y)
        if handle_id:
            # Start resizing the currently selected region
            self._resizing = True
            self._resize_handle = handle_dir
            self._drag_start_pos = (x, y)
            if self.selected_region is not None:
                self._orig_coords = list(
                    self.layer_manager.layers[self.selected_region].coords
                )
            return

        # ---------- DRAW MODE ----------
        if self._mode == "draw":
            # If clicked inside an existing region, drag that single region
            idx = self._get_region_at_pos(x, y)
            if idx is not None:
                self.selected_region = idx
                self.selected_regions = [idx]
                self._dragging = True
                self._drag_start_pos = (x, y)
                self._orig_coords = list(self.layer_manager.layers[idx].coords)
                self.notify_layer_change()
                return

            # Otherwise start creating a new region
            self._creating = True
            self._creation_start = (x, y)
            self._temp_rect = canvas.create_rectangle(x, y, x, y, outline="red")
            return

        # ---------- SELECT MODE ----------
        # 1) Click inside an existing region: start dragging that selection/group
        idx = self._get_region_at_pos(x, y)
        if idx is not None:
            if idx not in self.selected_regions:
                self.selected_regions = [idx]
                self.selected_region = idx

            self._dragging = True
            self._drag_start_pos = (x, y)
            self._orig_coords = {
                i: list(self.layer_manager.layers[i].coords)
                for i in self.selected_regions
            }

            self.notify_layer_change()
            if hasattr(self.app, "_refresh_region_list"):
                self.app._refresh_region_list()
            return

        # 2) No region and no handle: start box-select
        self._creating = True
        self._creation_start = (x, y)
        self._temp_rect = canvas.create_rectangle(
            x, y, x, y,
            outline="yellow",
            dash=(3, 3),
        )


    def on_mouse_move(self, event):
        canvas = event.widget
        x, y = event.x, event.y

        if self._mode == "select":
            # Drag selection box
            if self._creating and self._temp_rect is not None:
                x0, y0 = self._creation_start
                canvas.coords(self._temp_rect, x0, y0, x, y)

            # Move selected region(s)
            elif self._dragging and self.selected_regions:
                dx = x - self._drag_start_pos[0]
                dy = y - self._drag_start_pos[1]

                for i in self.selected_regions:
                    if i in self._orig_coords:
                        x1, y1, x2, y2 = self._orig_coords[i]
                        self.layer_manager.layers[i].coords = (
                            x1 + dx, y1 + dy, x2 + dx, y2 + dy
                        )

                self.notify_layer_change()

            return

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
            self.notify_layer_change()

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
            self.notify_layer_change()

    def on_mouse_up(self, event):
        canvas = event.widget

        # -------- SELECT MODE --------
        if self._mode == "select":
            # Finish box-select or end drag
            if self._creating and self._temp_rect is not None:
                # End box selection
                canvas.delete(self._temp_rect)
                self._temp_rect = None
                self._creating = False

                x0, y0 = self._creation_start
                x1, y1 = event.x, event.y
                x0, x1 = sorted([x0, x1])
                y0, y1 = sorted([y0, y1])

                # If the box is tiny, treat as no selection
                if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
                    return

                # Multi-select: find regions whose canvas-space boxes intersect
                hits = []
                scale = getattr(self.app, "display_scale", 1.0) or 1.0
                for i, layer in enumerate(self.layer_manager.layers):
                    lx1, ly1, lx2, ly2 = layer.coords
                    cx1, cy1 = lx1 * scale, ly1 * scale
                    cx2, cy2 = lx2 * scale, ly2 * scale
                    # simple AABB intersection test
                    if not (cx2 < x0 or cx1 > x1 or cy2 < y0 or cy1 > y1):
                        hits.append(i)

                if hits:
                    self.selected_regions = hits
                    self.selected_region = hits[0]
                    self.notify_layer_change()
                    if hasattr(self.app, "_refresh_region_list"):
                        self.app._refresh_region_list()


            else:
                # Finish drag / resize in select mode
                if self._dragging or self._resizing:
                    self._dragging = False
                    self._resizing = False
                    self._resize_handle = None
                    self._drag_start_pos = None
                    self._orig_coords = None

            return  # done for select mode

            # -------- DRAW MODE (existing behavior) --------
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

            # convert to image coords first
            ix0, iy0 = x0 / scale, y0 / scale
            ix1, iy1 = x1 / scale, y1 / scale

            # If the current shape is circle, normalize to a square
            shape = "rectangle"
            if hasattr(self.app, "shape_var"):
                shape = self.app.shape_var.get()

            if shape == "circle":
                # make a square that fits inside the drawn box
                w = ix1 - ix0
                h = iy1 - iy0
                side = min(abs(w), abs(h))

                # keep top-left anchored and grow down/right
                if w >= 0:
                    sx0 = ix0
                    sx1 = ix0 + side
                else:
                    sx0 = ix0 - side
                    sx1 = ix0

                if h >= 0:
                    sy0 = iy0
                    sy1 = iy0 + side
                else:
                    sy0 = iy0 - side
                    sy1 = iy0

                box = (sx0, sy0, sx1, sy1)
            else:
                box = (ix0, iy0, ix1, iy1)

            new_region = self._create_layer(box)
            self.layer_manager.add_layer(new_region)
            self.selected_region = len(self.layer_manager.layers) - 1
            self.notify_layer_change()

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

        #Move handle
        cx = (x1 + x2) // 2
        top_y = y1 - 15  # above the top edge

        self._move_handle_id = canvas.create_rectangle(
            cx - HANDLE_SIZE, top_y - HANDLE_SIZE // 2,
            cx + HANDLE_SIZE, top_y + HANDLE_SIZE // 2,
            fill='orange', outline='black', tags=MOVE_HANDLE_TAG,
        )

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
        canvas.delete(MOVE_HANDLE_TAG)

        scale = getattr(self.app, "display_scale", 1.0) or 1.0

        for idx, layer in enumerate(self.layer_manager.layers):
            x1, y1, x2, y2 = layer.coords
            # convert from image coords to canvas coords
            cx1, cy1 = x1 * scale, y1 * scale
            cx2, cy2 = x2 * scale, y2 * scale

            # Style: different color for selected regions
            if idx in getattr(self, "selected_regions", []):
                outline_color = "cyan"     # selected
                width = 3
            else:
                outline_color = "red"      # normal
                width = 2

            if layer.shape in ("circle", "oval"):
                canvas.create_oval(
                    cx1, cy1, cx2, cy2,
                    outline=outline_color,
                    width=width,
                    tags=REGION_TAG,
                )
            else:
                canvas.create_rectangle(
                    cx1, cy1, cx2, cy2,
                    outline=outline_color,
                    width=width,
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
                self.notify_layer_change()
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
                self.notify_layer_change()
            if hasattr(self.app, "_refresh_region_list"):
                self.app._refresh_region_list()

    def notify_layer_change(self):
        """Call this after any layer modification to update live preview."""
        if hasattr(self.app, "_on_layer_change"):
            self.app._on_layer_change()


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
