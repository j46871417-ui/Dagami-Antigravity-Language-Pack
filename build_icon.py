"""Render the app's code-native A/Ya mark. Pillow is a build-only tool."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets'
SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 256 256">
<rect x="4" y="4" width="248" height="248" rx="54" fill="#005fb8"/>
<rect x="38" y="42" width="122" height="120" rx="19" fill="white"/>
<path d="M65 131 L97 70 L129 131 M76 110 H118" fill="none" stroke="#005fb8" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="103" y="105" width="118" height="111" rx="19" fill="#dcecff" stroke="#005fb8" stroke-width="6"/>
<path d="M182 188 V131 H161 C136 131 136 161 161 161 H182 M161 161 L142 188" fill="none" stroke="#005fb8" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

def main():
    OUT.mkdir(exist_ok=True)
    (OUT / 'app-icon.svg').write_text(SVG, 'utf-8')
    image = Image.new('RGBA', (1024, 1024))
    draw = ImageDraw.Draw(image)
    def rect(box, radius, fill, outline=None, width=1):
        draw.rounded_rectangle(tuple(round(n*4) for n in box),radius=radius*4,fill=fill,outline=outline,width=width*4)
    def line(points, width, color):
        scaled=[(x*4,y*4) for x,y in points]
        draw.line(scaled, fill=color, width=width*4, joint='curve')
        radius=width*2
        for x,y in (scaled[0],scaled[-1]):
            draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill=color)
    rect((4,4,252,252),54,'#005fb8')
    rect((38,42,160,162),19,'white')
    line([(65,131),(97,70),(129,131)],11,'#005fb8')
    line([(76,110),(118,110)],11,'#005fb8')
    rect((103,105,221,216),19,'#dcecff','#005fb8',6)
    line([(182,188),(182,131),(161,131)],10,'#005fb8')
    # Curved bowl, drawn as a half-ellipse and a horizontal return.
    draw.arc((144*4,131*4,176*4,161*4),90,270,fill='#005fb8',width=10*4)
    line([(160,161),(182,161)],10,'#005fb8')
    line([(161,161),(142,188)],10,'#005fb8')
    image.save(OUT / 'app-icon-1024.png')
    for size in (16,24,32,48,64,128,256,512):
        image.resize((size,size),Image.Resampling.LANCZOS).save(OUT / f'app-icon-{size}.png')
    image.save(OUT / 'app-icon.ico',sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
    image.save(OUT / 'app-icon.icns')
    print('Icon: SVG, PNG, ICO and ICNS saved in assets')

if __name__ == '__main__': main()
