import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import os
import re
import spacy
from langdetect import detect


nlp_en = spacy.load('en_core_web_sm')
nlp_de = spacy.load('de_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')


def preprocess_image(image):
    """Preprocess the image to enhance OCR results."""
    if image.mode == 'P' and 'transparency' in image.info:
        image = image.convert('RGBA')
    else:
        image = image.convert('L')  # Convert to grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Enhance contrast
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2)  # Enhance sharpness
    return image



def extract_invoice_number(text, lang='en'):
    """Extract invoice numbers based on language-specific patterns."""
    if lang == 'en':
        pattern = r'\b(?:Invoice|Proforma Invoice|Receipt|Bill)\s*(?:No\.?|Number|Num|ID|#|/|:|[-])?\s*([A-Za-z0-9\-]+)\b'
    elif lang == 'de':
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


def extract_iban(text):
    """Extract IBANs based on standard patterns."""
    pattern = r'\b[A-Z]{2}[0-9]{2}[ ]?([A-Z0-9]{4}[ ]?){1,7}[A-Z0-9]{1,4}\b'
    matches = re.findall(pattern, text)
    return matches if matches else None


def extract_names(text, lang='en'):
    """Extract names based on language-specific patterns and spaCy NER."""
    nlp = nlp_en if lang == 'en' else nlp_de if lang == 'de' else nlp_es
    doc = nlp(text)
    ner_names = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
    
    patterns = {
        'en': r'\b(?:Client Name|Name|Bill to)\s*:\s*([A-Za-z\s]+)\b',
        'de': r'\b(?:Kunde|Name|Rechnung an)\s*:\s*([A-Za-z\s]+)\b',
        'es': r'\b(?:Nombre|Nombre de Cliente)\s*:\s*([A-Za-z\s]+)\b'
    }
    pattern = patterns.get(lang, patterns['en'])
    regex_names = re.findall(pattern, text, re.IGNORECASE)
    
    return ner_names + regex_names



def extract_amounts(text, lang='en'):
    """Extract amounts based on language-specific patterns."""
    patterns = {
        'en': r'\b(?:Total Amount|Amount Due|Net Amount|Pay|Payment|Total)\s*[:]?[\s]*([€$£]?[0-9,.]+)\b',
        'de': r'\b(?:Gesamtbetrag|Betrag|Zu Bezahlen|Zahlen|Zahlung)\s*[:]?[\s]*([€$£]?[0-9,.]+)\b',
        'es': r'\b(?:Monto Total|Cantidad|Neto|Pagar|Pago|Total)\s*[:]?[\s]*([€$£]?[0-9,.]+)\b'
    }
    pattern = patterns.get(lang, patterns['en'])
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches if matches else None




def detect_language(text):
    """Detect the language of the given text."""
    try:
        return detect(text)
    except:
        return 'en'  



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

    for i, image in enumerate(images[:2]):  
        processed_image = preprocess_image(image)
        text = pytesseract.image_to_string(processed_image, lang='eng+spa+deu')
        all_text += text

        # Detectar el idioma del texto
        lang = detect_language(text)
        print(f"Idioma detectado: {lang}")

        # Extraer el número de factura
        invoice_number = extract_invoice_number(text, lang)
        if invoice_number:
            print(f"Número de factura encontrado: {invoice_number}")
        else:
            print(f"Número de factura no encontrado")

        # Extraer fechas
        dates = extract_dates(text, lang)
        if dates:
            print(f"Fechas encontradas: {dates}")
        else:
            print(f"Fechas no encontradas")
        

        # Extraer IBANs
        ibans = extract_iban(text)
        if ibans:
            print(f"IBANs encontrados: {ibans}")
        else:
            print(f"IBANs no encontrados")
        

        # Extraer nombres
        names = extract_names(text, lang)
        if names:
            print(f"Nombres encontrados: {names}")
        else:
            print(f"Nombres no encontrados")


        # Extraer montos
        amounts = extract_amounts(text, lang)
        if amounts:
            print(f"Montos encontrados: {amounts}")
        else:
            print(f"Montos no encontrados")



        if invoice_number or dates or ibans or names or amounts:
            break



    # Guardar todo el texto extraído en un archivo
    with open('output_text.txt', 'w', encoding='utf-8') as f:
        f.write(all_text)

#####Alemán
# file_path = 'img1_de.png'
# file_path = 'img2_de.png'
file_path = 'img3_de.png'

# file_path = 'doc1_de.pdf'  

######Inglés
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
# file_path = 'doc8_es.pdf'

process_document(file_path)
