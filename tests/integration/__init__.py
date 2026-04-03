"""
Testy integracyjne (marker ``pytest.mark.integration``).

Domyślnie uruchamiane z ``pytest``; testy sieciowe / płatne są pomijane,
dopóki nie ustawisz odpowiednich zmiennych:

- ``RUN_DRIVE_INTEGRATION=1`` — ``cv_engine`` + ``CV_DRIVE_ID``
- ``RUN_SERP_INTEGRATION=1`` — ``serp_client`` + ``SERPAPI_API_KEY``
- ``RUN_OPENAI_INTEGRATION=1`` — ``mailer.generate_email`` + ``OPENAI_API_KEY``
- ``RUN_SMTP_INTEGRATION=1`` + ``INTEGRATION_SMTP_TO=...`` — jeden mail testowy
- ``RUN_SLOW_INTEGRATION=1`` — wolny test tenacity (``~4 s``)

Uruchomienie tylko integracji: ``pytest tests/integration -m integration``
Wykluczenie: ``pytest tests -m "not integration"``
"""
