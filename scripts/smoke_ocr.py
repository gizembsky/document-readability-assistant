"""First-run model download and actual OCR smoke check (CPU)."""
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
image = Image.new('RGB', (1000, 180), 'white')
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 48)
ImageDraw.Draw(image).text((30, 50), 'Türkçe belge okuma testi', font=font, fill='black')
reader = easyocr.Reader(['tr', 'en'], gpu=False, model_storage_directory='.easyocr', user_network_directory='.easyocr/user_network')
result = ' '.join(reader.readtext(np.array(image), detail=0))
print(result)
assert 'belge' in result.lower() and 'testi' in result.lower(), result
