# Rekomendacja: kolejne tabele dla bota

Data: 2026-03-20
Autor: Analityk

## Kontekst

Obecny zasób widoków:
- Kartoteki: KntKarty, TwrKarty, TwrGrupy(Dom), KntGrupy(Dom)
- Handel: TraNag, TraElem, ZamNag, ZamElem
- Operacyjne: Rezerwacje, Rozrachunki
- W trakcie: MagNag (Faza 1b), MagElem (backlog), TwrZasoby (backlog)

## Tier 1 — Wysoki priorytet (bot nie może odpowiedzieć na pytania codzienne)

### 1. TwrZasoby — stany magazynowe (backlog #36)
Już zaplanowane. Najczęstsze pytanie w każdej firmie handlowo-produkcyjnej:
"ile mamy towaru X na magazynie Y"
"które towary mają zerowy stan"
"gdzie jest ten towar fizycznie"
Bez tego bot nie zastąpi nawet podstawowego raportu.

### 2. Zlecenia produkcyjne (CDN.ProdZlecenia / ProdZleceniaElem)
Firma produkuje znicze — zlecenia produkcji to rdzeń operacyjny.
Pytania: "jakie ZP są otwarte", "kiedy będzie gotowy towar X", "na jakie zamówienie idzie ZP-X"
Uwaga: CDN.ProdZlecenia jest już referencjonowane w widoku Rezerwacje jako JOIN —
tabela istnieje i ma dane. Warto sprawdzić też CDN.ZlcNag (alias lub oddzielna tabela).

### 3. Cenniki (CDN.TCenkNag + CDN.TCenkElem lub analogiczne)
TraElem/ZamElem mają Nazwa_Cennika z JOIN, ale brak słownika cenników jako widoku.
Pytania: "ile kosztuje towar X w cenniku detalicznym", "jakie towary są w cenniku X"
Uwaga: prefiks TCN_ pojawia się w CTE CenBase w istniejących widokach — tabela jest znana.

## Tier 2 — Średni priorytet (rozszerzają istniejące o ważny kontekst)

### 4. Atrybuty towarów (CDN.DefAtryb + CDN.AtrybutyTwr)
Atrybuty to dodatkowe cechy produktów nieuchwycone w TwrKarty (np. kolor, zapach, seria).
Dla firmy zniczowej — kluczowe dla segmentacji asortymentu.
Pytania: "pokaż towary z atrybutem Kolor=Czerwony", "jakie atrybuty ma towar X"
Uwaga: atrybuty mogą być też na kontrahentach (CDN.AtrybutyKnt) — dwa oddzielne widoki.

### 5. Dostawy (CDN.Dostawy + CDN.DostawElem)
Śledzenie dostaw od dostawców. Rezerwacje już referencjonują CDN.Dostawy (JOIN).
Pytania: "kiedy dotrze dostawa X", "jakie dostawy są otwarte", "co jest w dostawie PZ-X"
Powiązanie z Rezerwacjami i MagNag — kompletuje obraz przepływu towaru.

### 6. Osoby kontaktowe kontrahenta (CDN.KntOsoby)
KntKarty ma dane firmy, ale nie osoby kontaktowe (handlowcy, kupcy).
Pytania: "kto jest osobą kontaktową w firmie X", "kontakty dla klienta Y"
Relatywnie prosta tabela, wysoka wartość dla sprzedaży.

## Tier 3 — Niski priorytet

### 7. Jednostki miary (CDN.Jm)
Mały słownik, wartości już widoczne jako kolumna Jednostka_Miary w TraElem/ZamElem.
Jako osobny widok ma małą wartość — ewentualnie gdy potrzebny przelicznik J.pom.

### 8. Operatorzy/Pracownicy (CDN.OpeKarty, CDN.PrcKarty)
Już używane jako JOINy w widokach (Akronim_Operatora). Małe tabele.
Samodzielny widok tylko gdy bot ma obsługiwać pytania "co robił operator X" lub listy.

### 9. Centra struktury (CDN.FrmStruktura)
Już w JOINach (Nazwa_Centrum). Przydatne do filtrowania "pokaż dokumenty centrum X".
Ale jako osobny widok słownikowy — niski priorytet (mała tabela, rzadkie pytania).

### 10. Załączniki
Trudne do zapytania NLP — bot nie wyświetli pliku. Ewentualnie "czy towar X ma załącznik"
ale to edge case. Najniższy priorytet.

## Sugerowana kolejność po MagNag/MagElem/TwrZasoby

1. ProdZlecenia (ZP) — krytyczne dla produkcji
2. Cenniki — częste pytania handlowe
3. Atrybuty towarów — segmentacja asortymentu
4. Dostawy — kompletuje przepływ towaru
5. Osoby kontaktowe — CRM
6. Reszta według zapotrzebowania
