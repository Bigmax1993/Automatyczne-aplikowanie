"""
cv_finalizer.py
OCR (5 prób) → GPT dopasowanie (3 próby) → PDF → merge z oryginałem.
"""

import os
import time

import pytesseract
from loguru import logger
from openai import OpenAI
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------------
# 1. OCR PDF (5 prób)
# ---------------------------------------------------------
def ocr_pdf(path: str, max_attempts: int = 5) -> str:
    logger.info(f"OCR: Start OCR dla pliku {path}")

    for attempt in range(1, max_attempts + 1):
        logger.info(f"OCR: Próba {attempt}/{max_attempts}")

        try:
            pages = convert_from_path(path, dpi=300)
            text = ""

            for page in pages:
                page_text = pytesseract.image_to_string(page)
                text += page_text + "\n"

            cleaned = " ".join(text.split())
            logger.info("OCR: Sukces")
            return cleaned

        except Exception as e:
            logger.error(f"OCR: Błąd w próbie {attempt}: {e}")
            time.sleep(1)

    logger.error("OCR: Nie udało się odczytać PDF po 5 próbach")
    return ""


# ---------------------------------------------------------
# 2. GPT retry wrapper (3 próby)
# ---------------------------------------------------------
def gpt_call(messages, max_attempts=3, model="gpt-4o-mini", max_tokens=350, temperature=0.3):
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"GPT: Próba {attempt}/{max_attempts}")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"GPT: Błąd w próbie {attempt}: {e}")
            time.sleep(1)

    logger.error("GPT: Nie udało się uzyskać odpowiedzi po 3 próbach")
    return ""


# ---------------------------------------------------------
# 3. Generowanie dopasowania CV przez GPT
# ---------------------------------------------------------
def generate_match_section(cv_text: str, job_description: str) -> str:
    prompt = f"""
    Masz poniższe CV:

    {cv_text}

    Oraz treść ogłoszenia:

    {job_description}

    Twoje zadanie:
    - NIE zmieniaj struktury CV
    - NIE przepisuj CV
    - NIE generuj nowego CV
    - Stwórz tylko dodatkową sekcję:
      "Key Skills Match"
    - Wypisz w niej, jak CV spełnia wymagania z ogłoszenia
    - Użyj punktów (bullet points)
    """

    return gpt_call(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=350,
        temperature=0.3,
    )


# ---------------------------------------------------------
# 4. Generowanie PDF z dopasowaniem
# ---------------------------------------------------------
def generate_match_pdf(text: str, output_path: str):
    logger.info(f"PDF: Generuję stronę dopasowania → {output_path}")

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Key Skills Match")
    y -= 40

    c.setFont("Helvetica", 11)

    for line in text.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)

        c.drawString(50, y, line)
        y -= 18

    c.save()
    logger.info("PDF: Strona dopasowania wygenerowana")


# ---------------------------------------------------------
# 5. Merge: oryginalne CV + dopasowanie
# ---------------------------------------------------------
def merge_pdfs(original_pdf: str, match_pdf: str, output_pdf: str):
    logger.info("PDF: Łączenie oryginalnego CV z dopasowaniem")

    writer = PdfWriter()

    # Oryginalne CV (nienaruszone)
    original = PdfReader(original_pdf)
    for page in original.pages:
        writer.add_page(page)

    # Nowa strona dopasowania
    match = PdfReader(match_pdf)
    for page in match.pages:
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    logger.info(f"PDF: Finalny plik zapisany jako {output_pdf}")


# ---------------------------------------------------------
# 6. Główna funkcja: OCR → GPT → PDF → merge
# ---------------------------------------------------------
def build_final_cv(original_pdf: str, job_description: str, output_pdf: str):
    logger.info("=== FINAL CV BUILDER: Start ===")

    # 1. OCR
    cv_text = ocr_pdf(original_pdf)

    # 2. GPT dopasowanie
    match_section = generate_match_section(cv_text, job_description)

    # 3. Generowanie PDF dopasowania
    match_pdf = "match_section.pdf"
    generate_match_pdf(match_section, match_pdf)

    # 4. Merge
    merge_pdfs(original_pdf, match_pdf, output_pdf)

    # 5. Cleanup
    if os.path.exists(match_pdf):
        os.remove(match_pdf)

    logger.info("=== FINAL CV BUILDER: Gotowe ===")
