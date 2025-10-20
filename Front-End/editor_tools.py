from PIL import Image, ImageDraw, ImageFilter

def create_masked_shape(image, coords, shape='rectangle'):
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    if shape == 'rectangle':
        draw.rectangle(coords, fill=255)
    else:
        draw.ellipse(coords, fill=255)
    return mask

def blur_region(image, mask, intensity=8):
    blurred = image.filter(ImageFilter.GaussianBlur(intensity))
    return Image.composite(blurred, image, mask)

def pixelate_region(image, mask, block_size=12):
    region = image.filter(ImageFilter.GaussianBlur(0))
    cropped = region.resize((image.width // block_size, image.height // block_size), Image.NEAREST)
    pix = cropped.resize(image.size, Image.NEAREST)
    return Image.composite(pix, image, mask)

def blackout_region(image, mask):
    black = Image.new('RGBA', image.size, (0, 0, 0, 255))
    return Image.composite(black, image, mask)