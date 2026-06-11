from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "fonts/PlayfairDisplay-VariableFont_wght.ttf"
FOND_BEIGE = "fond_de_page_beige_avec_logo.png"
FOND_TERRA = "fond_de_page_terracota_avec_logo.png"

def wrap_text(texte, font, draw, max_width):
    mots = texte.split()
    lignes = []
    courante = ""
    for mot in mots:
        test = (courante + " " + mot).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            courante = test
        else:
            if courante:
                lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes

def generer_visuel(texte, fond="beige", output_path="test.png", taille=96):
    fond_fichier = FOND_BEIGE if fond == "beige" else FOND_TERRA
    couleur = (74, 56, 51) if fond == "beige" else (251, 248, 246)

    img = Image.open(fond_fichier).convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    W, H = img.size

    font = ImageFont.truetype(FONT_PATH, taille)
    max_width = W - 200

    lignes = wrap_text(texte, font, draw, max_width)
    line_height = int(taille * 1.5)
    total_h = len(lignes) * line_height
    y_start = (H - total_h) // 2 - 200

    for i, ligne in enumerate(lignes):
        bbox = draw.textbbox((0, 0), ligne, font=font)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        y = y_start + i * line_height
        draw.text((x, y), ligne, font=font, fill=couleur)

    img.save(output_path)
    print(f"Sauvegarde : {output_path}")

generer_visuel("Sans renoncer\na ton ambition.", "beige", "test_beige.png")
generer_visuel("Depuis longtemps.", "terracotta", "test_terra.png")
generer_visuel("Tu fonctionnes.\nMais a quel prix ?", "terracotta", "test_carrousel.png")
print("Termine !")