"""Genera un PDF con un codigo QR por pagina para probar el escaner de la app.

Se muestra en pantalla (pagina completa) y se escanea con el telefono. Cubre
cada camino de la app: veredicto verde, amarillo y rojo, redirecciones, enlace
sin esquema y contenidos que no son enlaces.

Ningun caso usa URLs de phishing reales: los rojos se arman con dominios
inventados que disparan las heuristicas L1 (punycode, TLD sospechoso, IP
literal). Por eso el PDF no apunta a nada peligroso aunque alguien abra un
enlace. El veredicto esperado asume las capas L1-L3; con la cache L2 llena o
con L4/L5 activas puede variar.

Uso (requiere `pip install "qrcode[pil]"`):
    python3 shared/qr-prueba/generar_pdf.py [salida.pdf]
"""

import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Homografo con la "a" cirilica (U+0430): se ve como "banco" y el motor lo
# recibe ya convertido a punycode.
_HOMOGRAPH = "b\u0430nco-prueba".encode("idna").decode()

CASES = [
    ("Sitio legítimo", "https://www.wikipedia.org", "Verde"),
    ("Enlace sin esquema", "www.wikipedia.org", "Verde: la app completa https://"),
    ("Redirección HTTP a HTTPS", "http://github.com", "Verde, ruta de 2 saltos"),
    ("Acortador", "https://bit.ly/", "Amarillo: acortador en la ruta"),
    (
        "TLD sospechoso",
        "https://premio-umbral-prueba.xyz/",
        "Amarillo: TLD .xyz, ruta sin resolver",
    ),
    (
        "Homógrafo punycode + TLD",
        f"https://{_HOMOGRAPH}.xyz/login",
        "Rojo: punycode + TLD sospechoso",
    ),
    (
        "IP literal + URL larga",
        "http://192.0.2.10/cuenta/verificar/" + "a" * 70,
        "Rojo: IP + longitud; el filtro anti-SSRF corta la ruta",
    ),
    (
        "Página de prueba de Safe Browsing",
        "https://testsafebrowsing.appspot.com/s/phishing.html",
        "Pendiente: la detecta L4, aún no implementada",
    ),
    ("Red WiFi", "WIFI:T:WPA;S:RedDePrueba;P:clave1234;;", "No es un enlace"),
    (
        "Contacto",
        "BEGIN:VCARD\nVERSION:3.0\nFN:Contacto de Prueba\nEND:VCARD",
        "No es un enlace",
    ),
    ("Texto plano", "Hola, esto es solo texto", "No es un enlace"),
]

# A4 a 150 dpi.
PAGE = (1240, 1754)


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size)


def _page(index: int, title: str, content: str, expected: str) -> Image.Image:
    page = Image.new("RGB", PAGE, "white")
    draw = ImageDraw.Draw(page)
    margin = 100

    draw.text((margin, 80), f"{index}. {title}", fill="black", font=_font(56))

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(content)
    side = PAGE[0] - 2 * margin
    img = qr.make_image().convert("RGB").resize((side, side), Image.NEAREST)
    page.paste(img, (margin, 200))

    y = 200 + side + 40
    draw.text((margin, y), f"Esperado: {expected}", fill="black", font=_font(36))
    # El contenido va en texto para comparar con lo que muestra la app.
    shown = content.replace("\n", " | ")
    for i in range(0, len(shown), 60):
        y += 46
        draw.text((margin, y), shown[i : i + 60], fill="#555555", font=_font(30))
    return page


def main() -> None:
    out = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name("qr-de-prueba.pdf")
    )
    pages = [_page(i, *case) for i, case in enumerate(CASES, start=1)]
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150)
    print(f"{len(pages)} paginas -> {out}")


if __name__ == "__main__":
    main()
