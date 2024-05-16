
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import os
import re
import spacy
from langdetect import detect

# Cargar modelos de spaCy para diferentes idiomas
nlp_en = spacy.load('en_core_web_sm')
nlp_de = spacy.load('de_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')

def preprocess_image(image):
    """Preprocess the image to enhance OCR results."""
    image = image.convert('L')  # Convert to grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Enhance contrast
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2)  # Enhance sharpness
    return image

def extract_invoice_number(text, lang='en'):
    """Extract invoice numbers based on language-specific patterns."""
    if lang == 'en':
        # pattern = r'Invoice\s*(?:No\.|Number|#|Nr|):?\s*([A-Za-z0-9\-]+)'
        pattern = r'\b(?:Invoice|Proforma Invoice|Receipt|Bill)\s*(?:No\.?|Number|Num|ID|#|/|:|[-])?\s*([A-Za-z0-9\-]+)\b'
    elif lang == 'de':
        # pattern = r'Rechnungsnummer\s*(?:Nr\.|No|Nummer|#|):?\s*([A-Za-z0-9\-]+)|\b[Rr]-\d{7}\b'
        pattern = r'Rechnungsnummer\s*(?:Nr\.|No|Nummer|ID|Code|Ref|#|[-/])?:?\s*([A-Za-z0-9\-]+)|\b[Rr]-\d{7}\b'
 
    elif lang == 'es':
        pattern = r'Factura\s*(?:No\.|Número|#|Num|):?\s*([A-Za-z0-9\-]+)'
    else:
        pattern = r'Invoice\s*(?:No\.|Number|#|Nr|):?\s*([A-Za-z0-9\-]+)'  

    matches = re.findall(pattern, text, re.IGNORECASE)
    valid_matches = [match for match in matches if len(match) > 2]  
    return valid_matches[0] if valid_matches else None

def extract_dates(text, lang='en'):
    """Extract dates based on language-specific patterns."""
    if lang == 'en':
        pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b)'
    elif lang == 'de':
        pattern = r'(\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b)'
    elif lang == 'es':
        pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b)'
    else:
        pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b)'  

    matches = re.findall(pattern, text)
    return matches if matches else None



def detect_language(text):
    """Detect the language of the given text."""
    try:
        return detect(text)
    except:
        return 'en'  # Default to English if detection fails



# Comentario: Extracción de información de balance
# def extract_balance_info(text):
#     pattern = r'.*Balance.*'
#     balance_lines = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
#     return balance_lines

# Comentario: Extracción de información total
# def extract_total_info(text):
#     pattern = r'.*Total.*'
#     total_lines = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
#     return total_lines

# Comentario: Extracción de nombres de personas utilizando spaCy
# def extract_person_names(text, lang='en'):
#     nlp = nlp_en if lang == 'en' else nlp_de
#     doc = nlp(text)
#     names = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
#     return names

def process_document(path):
    """Process the document to extract invoice number."""
    _, ext = os.path.splitext(path)
    images = []
    if ext.lower() == '.pdf':
        images = convert_from_path(path, dpi=400)
    elif ext.lower() in ['.jpg', '.jpeg', '.png']:
        images = [Image.open(path)]
    else:
        print("Formato de archivo no soportado.")
        return

    all_text = ""
    for i, image in enumerate(images):
        processed_image = preprocess_image(image)
        text = pytesseract.image_to_string(processed_image, lang='eng+spa+deu')
        all_text += text

        # Detectar el idioma del texto
        lang = detect_language(text)
        print(f"Idioma detectado en la página {i+1}: {lang}")

        # Extraer el número de factura
        invoice_number = extract_invoice_number(text, lang)
        if invoice_number:
            print(f"Número de factura encontrado en la página {i+1}: {invoice_number}")
        else:
            print(f"Número de factura no encontrado en la página {i+1}")

        # Extraer fechas
        dates = extract_dates(text, lang)
        if dates:
            print(f"Fechas encontradas en la página {i+1}: {dates}")
        else:
            print(f"Fechas no encontradas en la página {i+1}")

        # Comentario: Extracción de información de 'Balance'
        # balance_info = extract_balance_info(text)
        # print("Información de 'Balance' encontrada:", balance_info)

        # Comentario: Extracción de información de 'Total'
        # total_info = extract_total_info(text)
        # print("Información de 'Total' encontrada:", total_info)

        # Comentario: Extracción de nombres de personas
        # person_names = extract_person_names(text, lang)
        # print("Nombres de personas:", person_names)

    # Guardar todo el texto extraído en un archivo
    with open('output_text.txt', 'w', encoding='utf-8') as f:
        f.write(all_text)

#####Aleman
# file_path = 'img1_de.png'
# file_path = 'img2_de.png'
# file_path = 'img3_de.png'

# file_path = 'doc1_de.pdf'  

######Ingles
# file_path = 'img1_en.jpg'  
# file_path = 'doc1_en.pdf'  

# file_path = 'doc2_en.pdf'
# file_path = 'doc3_en.pdf'
# file_path = 'doc4_en.pdf'

######Español
# file_path = 'doc1_es.pdf'
# file_path = 'doc2_es.pdf'
# file_path = 'doc3_es.pdf'
# file_path = 'doc4_es.pdf'
# file_path = 'doc5_es.pdf'
# file_path = 'doc6_es.pdf'
# file_path = 'doc7_es.pdf'
file_path = 'doc8_es.pdf'

process_document(file_path)
