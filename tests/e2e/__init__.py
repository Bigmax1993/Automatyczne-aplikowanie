"""
Testy E2E (marker ``pytest.mark.e2e``).

Scenariusze od wejścia do wyjścia (np. pipeline → Excel). Sieć zastąpiona mockami,
żeby testy były deterministyczne i szybkie.

Uruchomienie: ``pytest tests/e2e -m e2e``
Pominięcie: ``pytest tests -m "not e2e"``
"""
