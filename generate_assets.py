import os
from PIL import Image, ImageDraw

def create_icon(color, filename):
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    # Background circle
    dc.ellipse((4, 4, 60, 60), fill=color)
    # Mic symbol (simplified)
    dc.rectangle((24, 16, 40, 40), fill="white")
    dc.arc((20, 28, 44, 48), start=0, end=180, fill="white", width=4)
    dc.line((32, 48, 32, 56), fill="white", width=4)
    
    asset_dir = os.path.join(os.getcwd(), "assets")
    if not os.path.exists(asset_dir):
        os.makedirs(asset_dir)
        
    image.save(os.path.join(asset_dir, filename))
    print(f"Created {filename}")

if __name__ == "__main__":
    create_icon("grey", "icon_idle.png")
    create_icon("red", "icon_recording.png")
    create_icon("yellow", "icon_processing.png")
