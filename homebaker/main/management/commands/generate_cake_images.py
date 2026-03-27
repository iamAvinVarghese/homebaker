from PIL import Image, ImageDraw, ImageFont
import random
import os
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Generate unique placeholder images for cakes'

    def handle(self, *args, **kwargs):
        media_root = settings.MEDIA_ROOT
        cakes_dir = os.path.join(media_root, 'cakes')
        os.makedirs(cakes_dir, exist_ok=True)

        for i in range(1, 6):
            phone = f'{i:010d}'
            for j in range(1, 3):
                # Random color
                color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                
                # Create image
                img = Image.new('RGB', (800, 600), color=color)
                d = ImageDraw.Draw(img)
                
                # Add text
                text = f"Baker {i}\nCake {j}"
                # Try to load a font, otherwise use default
                try:
                    # Windows font path
                    font = ImageFont.truetype("arial.ttf", 60)
                except IOError:
                    font = ImageFont.load_default()

                # Position text
                # Simple centering estimation
                d.text((100, 200), text, fill=(0, 0, 0), font=font)
                
                filename = f"cake_{phone}_{j}.png"
                filepath = os.path.join(cakes_dir, filename)
                
                img.save(filepath)
                self.stdout.write(self.style.SUCCESS(f'Generated {filename}'))

        self.stdout.write(self.style.SUCCESS('Successfully generated 10 unique placeholder images.'))
