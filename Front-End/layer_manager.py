from PIL import Image, ImageDraw, ImageFilter

class Layer:
    def __init__(self, shape, coords, method='blur', intensity=10, size=0):
        self.shape = shape
        self.coords = coords  # (x1, y1, x2, y2)
        self.method = method
        self.intensity = intensity
        self.size = size

    def apply(self, base_image):
        img = base_image.copy().convert("RGBA")
        x1, y1, x2, y2 = self.coords
        pad = self.size

        # Compute box and image coords and cast to int
        left   = int(max(0, x1 - pad))
        top    = int(max(0, y1 - pad))
        right  = int(min(x2 + pad, img.width))
        bottom = int(min(y2 + pad, img.height))

        box = (left, top, right, bottom)        
        region = img.crop(box)

        if self.method == 'blur':
            region = region.filter(ImageFilter.GaussianBlur(self.intensity))
        elif self.method == 'pixelate':
            small = region.resize((max(1, region.width // max(1, self.intensity // 2)),
                                   max(1, region.height // max(1, self.intensity // 2))),
                                    Image.NEAREST)
            region = small.resize(region.size, Image.NEAREST)
        elif self.method == 'redact':
            region = Image.new("RGBA", region.size, (0, 0, 0, 255))

        if self.shape in ['circle', 'oval']:
            mask = Image.new('L', img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse(box, fill=255)
            img.paste(region, box, mask.crop(box))
        else:
            img.paste(region, box)
        return img

class LayerManager:
    def __init__(self):
        self.layers = []

    def add_layer(self, layer):
        self.layers.append(layer)
        
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]

    def clear_layers(self):
        self.layers = []

    def merge_all(self, base_image):
        img = base_image.convert("RGBA").copy()
        for layer in self.layers:
            img = layer.apply(img)
        return img
    
    def create_preview(self, base_image, display_scale=1.0):
        """
        Create a scaled composite image applying all layers on scaled base image.
        """
        # Scale the base image to preview size
        preview_size = (
            int(base_image.width * display_scale),
            int(base_image.height * display_scale)
        )
        base_preview = base_image.resize(preview_size, Image.Resampling.LANCZOS).copy().convert("RGBA")

        img = base_preview

        for layer in self.layers:
            # Adjust layer coords to preview scale
            scaled_coords = tuple(c * display_scale for c in layer.coords)
            # Create a copy of layer with scaled coords to avoid modifying original
            scaled_layer = Layer(
                shape=layer.shape,
                coords=scaled_coords,
                method=layer.method,
                intensity=layer.intensity,
                size=layer.size
            )
            img = scaled_layer.apply(img)

        return img

