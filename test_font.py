# test_font.py
from PIL import ImageFont

try:
    font = ImageFont.truetype("/home/hernansote/dbs/sys-donaciones/fuentes/PlayfairDisplay.ttf", 60)
    print("✅ Fuente encontrada!")
    print(f"  - Nombre: {font.getname()}")
    print(f"  - Tamaño: {font.size}")
except Exception as e:
    print(f"❌ Error: {e}")