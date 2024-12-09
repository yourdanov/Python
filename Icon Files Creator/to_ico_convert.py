from PIL import Image

# Load the image
img = Image.open("edb1caa8-0d38-4f11-8c2d-747932c05557.png")

# Save as .ico file
img.save("stocks.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
