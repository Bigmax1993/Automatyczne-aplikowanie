"""
mailer.py
Generowanie treści maili (OpenAI) + wysyłanie maili z załączonym CV.
Zwraca DataFrame zamiast zapisywać CSV.
"""

import smtplib
from email.message import EmailMessage

import pandas as pd
from loguru import logger
from openai import OpenAI

from config import (
    CV_LOCAL_PATH,
    OPENAI_API_KEY,
    SMTP_PASS,
    SMTP_USER,
)
from cv_engine import download_cv

_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        key = OPENAI_API_KEY
        if not key or not str(key).strip():
            raise ValueError("OPENAI_API_KEY is missing or empty.")
        if not str(key).isascii():
            raise ValueError(
                "OPENAI_API_KEY must be ASCII-only (HTTP Authorization). "
                "Use a real sk-... key, not a Polish placeholder in .env."
            )
        _client = OpenAI(api_key=key)
    return _client


# ---------------------------------------------------------
# 1. GENEROWANIE TREŚCI MAILA
# ---------------------------------------------------------
def generate_email(company: str) -> str | None:
    """
    Generuje treść maila aplikacyjnego dla danej firmy.
    Zwraca tekst lub None w przypadku błędu.
    """
    prompt = f"""
Napisz profesjonalny mail aplikacyjny do firmy {company}.
Ton: uprzejmy, konkretny, bez lania wody.
"""

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content
        if not text or not text.strip():
            logger.error("generate_email: empty model output company={}", ascii(company))
            return None
        text = text.strip()
        logger.debug(
            "generate_email: company={} chars={} (body omitted)",
            ascii(company),
            len(text),
        )
        return text

    except Exception as e:
        # ascii() — bezpieczne przy pytest capture / stderr w ascii (Windows).
        logger.error(
            "generate_email failed company={} err={}",
            ascii(company),
            ascii(e),
        )
        return None


def run_mail_generation(df_emails: pd.DataFrame) -> pd.DataFrame:
    """
    Przyjmuje DataFrame z kolumnami:
    - company_name
    - emails

    Zwraca DataFrame:
    - company_name
    - emails
    - mail_text
    """
    logger.info("=== START: Generowanie maili ===")

    results = []

    for _, row in df_emails.iterrows():
        company = row["company_name"]
        emails = row["emails"]

        if pd.isna(emails) or not isinstance(emails, str) or not emails.strip():
            logger.warning(f"Brak e-maili dla firmy: {company}")
            continue

        mail_text = generate_email(str(company))

        results.append({
            "company_name": company,
            "emails": emails.strip(),
            "mail_text": mail_text,
        })

    df_out = pd.DataFrame(results)

    logger.info(f"Wygenerowano {len(df_out)} maili.")
    logger.info("=== KONIEC: Generowanie maili ===")

    return df_out


# ---------------------------------------------------------
# 2. WYSYŁANIE MAILI
# ---------------------------------------------------------
def _send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Wysyła pojedynczego maila z załączonym CV.
    Zwraca True/False.
    """
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with open(CV_LOCAL_PATH, "rb") as f:
            cv_bytes = f.read()
        if not cv_bytes:
            logger.error("Plik CV jest pusty — nie wysyłam.")
            return False
        msg.add_attachment(
            cv_bytes,
            maintype="application",
            subtype="pdf",
            filename="CV_Svinchak.pdf",
        )
    except OSError as e:
        logger.error(f"Nie udało się dołączyć CV: {e}")
        return False

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True

    except smtplib.SMTPException as e:
        logger.error(f"Błąd wysyłki do {to_email}: {e}")
        return False
    except OSError as e:
        logger.error(f"Błąd połączenia SMTP do {to_email}: {e}")
        return False


def run_mail_sending(df_to_send: pd.DataFrame) -> pd.DataFrame:
    """
    Przyjmuje DataFrame:
    - company_name
    - emails
    - mail_text

    Zwraca DataFrame logów:
    - company_name
    - email
    - status
    """
    logger.info("=== START: Wysyłanie maili ===")

    if not download_cv():
        logger.error("Nie udało się pobrać CV — przerwano wysyłkę.")
        return pd.DataFrame(columns=["company_name", "email", "status"])

    logs = []

    for _, row in df_to_send.iterrows():
        company = row["company_name"]
        raw_emails = row["emails"]
        body = row["mail_text"]

        if body is None or (isinstance(body, str) and not body.strip()):
            logger.warning(f"Pomijam {company}: brak treści maila (mail_text).")
            continue

        if pd.isna(raw_emails) or not isinstance(raw_emails, str):
            logger.warning(f"Pomijam {company}: nieprawidłowa kolumna emails.")
            continue

        body_str = body.strip() if isinstance(body, str) else str(body)

        for email in raw_emails.split(","):
            email = email.strip()
            if not email:
                continue
            ok = _send_email(email, f"Aplikacja — {company}", body_str)

            logs.append({
                "company_name": company,
                "email": email,
                "status": "OK" if ok else "ERROR",
            })

    df_log = pd.DataFrame(logs)

    logger.info(f"Wysłano {len(df_log)} maili.")
    logger.info("=== KONIEC: Wysyłanie maili ===")

    return df_log
