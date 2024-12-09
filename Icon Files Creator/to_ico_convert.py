from PIL import Image

# Load the image
img = Image.open("image.png")

# Save as .ico file
img.save("image.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
