Zadanie: weryfikacja i fix widoku Rozrachunki — Stan & 2 na kontach walutowych

Zgłoszono błąd: Stan & 2 daje złe wyniki dla kont walutowych w widoku AIBI.Rozrachunki (solutions/bi/views/Rozrachunki.sql).

Zbadaj:
1. Jak wygląda obecna heurystyka Stan & 2 w Rozrachunki.sql
2. Czy konta walutowe faktycznie dają błędne wyniki — jaki jest błąd
3. Zaproponuj poprawkę

Jeśli potrzebujesz dostępu do schematu CDN.Rozrachunki — użyj docs_search lub sql_query.
Po zbadaniu: wyślij wyniki do developera przez agent_bus_cli.py send --from erp_specialist --to developer.
