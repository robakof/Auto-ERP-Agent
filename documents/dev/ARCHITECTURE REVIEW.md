Rezenzja 1:
# Analiza Architektoniczna: Faza 2 — Warstwa BI + Bot Pytań

**Data:** 2026-03-03  
**Status:** Review (Architekt Systemowy)  
**Dotyczy:** Projektu automatyzacji konfiguracji i odczytu danych ERP  

---

## 1. OCENA OGÓLNA: 8.5 / 10

Architektura jest **wybitnie pragmatyczna** i doskonale dopasowana do realiów średniej wielkości przedsiębiorstwa korzystającego z systemu Comarch ERP XL. Wykorzystanie warstwy semantycznej (BI Schema) jako "bezpiecznika" i filtra dla LLM drastycznie zwiększa szanse na sukces produkcyjny. Wybór Cloudflare Tunnel to optymalne rozwiązanie problemów z infrastrukturą on-premise.

---

## 2. MOCNE STRONY

* **Warstwa Semantyczna (BI Schema):** Sprowadzenie złożonego schematu `CDN.*` do czytelnych widoków `BI.*` drastycznie ułatwia pracę generatorowi SQL i eliminuje halucynacje dotyczące nazw kolumn [cite: 1, 3].
* **Hybrydowy Pipeline (Report Matcher):** Priorytetyzacja gotowych raportów nad generowaniem ad-hoc zapewnia stabilność dla 80% typowych zapytań i redukuje koszty tokenów [cite: 1, 2, 3].
* **Izolacja Uprawnień:** Wykorzystanie dedykowanego konta `CEiM_BI` z uprawnieniami `SELECT-only` wyłącznie do schematu BI jest zgodne z najlepszymi praktykami Security [cite: 1, 2, 3].
* **Infrastruktura Connectivity:** Użycie Cloudflare Tunnel do obsługi webhooków WhatsApp bez otwierania portów na firewallu firmowym to bezpieczne i nowoczesne podejście [cite: 2, 3].
* **Uniwersalność Danych:** Ta sama warstwa BI służy botowi, Power BI oraz Excelowi, co zapewnia „single source of truth” [cite: 1, 2].

---

## 3. SŁABE STRONY I RYZYKA

* **Zagrożenie Wydajnościowe (SQL Injection / Heavy Queries):** Nawet przy dostępie read-only, LLM może wygenerować zapytanie (np. brak JOIN lub filtrów), które nadmiernie obciąży serwer produkcyjny [cite: 2].
* **Brak Zarządzania Stanem:** Obecna architektura sugeruje model stateless. Brak obsługi kontekstu (np. „A ile u nich zamówiliśmy?” po pytaniu o konkretnego klienta) obniża UX bota.
* **Ręczny Cykl Życia Widoków:** Brak wspomnienia o automatyzacji wdrażania zmian w schemacie `BI` (migracje SQL) może prowadzić do niespójności między `catalog.json` a bazą [cite: 3].
* **Vendor Lock-in (Claude API):** Cała inteligencja systemu zależy od zewnętrznego API. Awaria łącza lub serwisu Anthropic całkowicie paraliżuje bota [cite: 2].

---

## 4. ALTERNATYWNE PODEJŚCIA

| Problem | Propozycja alternatywna | Zaleta | Trade-off |
| :--- | :--- | :--- | :--- |
| **Wydajność SQL** | Implementacja `Resource Governor` na SQL Server dla konta `CEiM_BI`. | Fizyczne ograniczenie zasobów CPU/RAM dla zapytań bota. | Wymaga wersji Enterprise SQL Server. |
| **Brak kontekstu** | Dodanie bazy wektorowej (RAG) lub SQLite do logowania Thread ID. | Możliwość prowadzenia naturalnego dialogu z botem. | Większa złożoność promptu. |
| **Wdrożenia** | Skrypt CI/CD (np. GitHub Actions Runner) do `APPLY` widoków. | Gwarancja, że to co w Git, jest na produkcji. | Wymaga konfiguracji środowiska. |
| **Vendor Lock-in** | Fallback do lokalnego modelu (np. Llama 3 przez Ollama). | Odporność na brak internetu dla prostych zapytań. | Wymaga GPU na serwerze firmowym. |

---

## 5. PYTANIA KRYTYCZNE DO ZESPOŁU

1.  **Limity danych:** Jak bot zareaguje na pytanie generujące 10 000 wierszy? Czy prompt wymusza stosowanie `TOP 100` [cite: 3]?
2.  **Prywatność:** Czy firma jest świadoma, że dane wynikowe z bazy (po pobraniu przez backend) są wysyłane do Claude API w celu sformułowania odpowiedzi [cite: 3]?
3.  **Sanity Check:** Czy parametry w `solutions/bi/reports/` są walidowane przed wstrzyknięciem do SQL, aby zapobiec próbom manipulacji zapytaniem?
4.  **Skalowanie WhatsApp:** Czy backend FastAPI obsługuje asynchroniczne kolejkowanie, jeśli Meta wyśle 50 webhooków jednocześnie?

---
*Dokument wygenerowany na podstawie PRD, Techstack i Architektury Projektu Auto-ERP.*

Recenzja 2:
1. OCENA OGÓLNA (1-10)

7/10. Fundament jest sensowny: semantyczny schemat BI.*, separacja uprawnień oraz iteracyjne podejście „raporty gotowe → ad-hoc fallback” dobrze rokują na szybkie dowiezienie wartości. Największe ryzyka widzę w bezpieczeństwie/zgodności (zwłaszcza co dokładnie wysyłacie do Claude) oraz w kontroli kosztu i wydajności zapytań (LLM-SQL + DirectQuery). 

PRD

 

TECHSTACK

2. MOCNE STRONY

Semantyczna warstwa danych jako produkt: schema BI z czytelnymi nazwami i złączonymi encjami upraszcza zarówno raportowanie (Power BI/Excel), jak i pracę agenta oraz bota. To jest dobra inwestycja w „wspólny język danych”. 

PRD

Twarda separacja uprawnień: bot ma mieć read-only wyłącznie do BI.* i brak dostępu do CDN.* — to bardzo sensowny „blast radius limiter” w razie błędów lub nadużyć. 

PRD

 

ARCHITECTURE

Wersjonowanie definicji widoków i raportów w Git: trzymanie CREATE VIEW i gotowych raportów .sql w repo (plus katalog/metadane) ułatwia review, rollback i rozwój zespołowy. 

PRD

 

TECHSTACK

Architektura bota z wyraźnymi modułami: kanały (Telegram/WhatsApp), pipeline NLP, executor SQL, matcher raportów — to naturalne granice odpowiedzialności, które ułatwiają testowanie i wymianę komponentów. 

PRD

 

ARCHITECTURE

Pragmatyczny rollout: Telegram (polling, bez publicznego endpointu) jako etap testowy i dopiero potem WhatsApp (webhook) to rozsądna redukcja ryzyka wdrożeniowego. 

PRD

 

TECHSTACK

Bezpieczny sposób wystawienia webhooka: Cloudflare Tunnel ogranicza potrzebę otwierania portów/publicznego IP na serwerze firmowym. 

TECHSTACK

 

ARCHITECTURE

Mechanizm „uczenia się” produktu przez logi: logowanie pytań/odpowiedzi i budowanie biblioteki raportów na tej podstawie to właściwy loop do poprawy jakości i czasu odpowiedzi. 

PRD

 

ARCHITECTURE

3. SŁABE STRONY

Niespójność dot. prywatności danych vs użycie Claude do formatowania odpowiedzi
Wymaganie mówi, że do Claude ma trafiać tylko pytanie i schemat BI, a „zapytania SQL nie wychodzą poza sieć” 

PRD

, ale w opisie pipeline’u pojawia się krok Answer Formatter (Claude API): dane SQL + pytanie → odpowiedź 

TECHSTACK

. To kluczowe ryzyko zgodności (RODO/umowy/NDA) i wymaga jednoznacznej decyzji.

Generowanie SQL ad-hoc przez LLM bez opisanych guardrails
Sama izolacja do BI.* pomaga, ale nadal grożą: kosztowne full scan’y, niekontrolowane agregacje, długie czasy, błędna semantyka oraz podatność na prompt-injection (“wypisz wszystko…”).

Ryzyko wydajności: DirectQuery + „ciężkie” widoki + współdzielenie instancji SQL
DirectQuery w Power BI potrafi generować wiele zapytań, a jeśli widoki są złożone (JOINy, CASE, agregacje), SQL Server może dostać po głowie — zwłaszcza gdy bot też odpytuje w tym samym czasie. 

TECHSTACK

 

PRD

Brak strategii deploymentu/migracji dla widoków BI (ryzyko driftu)
„Definicje w Git” to nie to samo co „stan na SQL Server”. Nie widzę mechanizmu: jak wdrażacie zmiany, jak wykrywacie różnice, jak robicie rollback i jak testujecie kompatybilność z Power BI.

Autoryzacja: whitelist użytkowników to za mało jak na ERP
Whitelist ID/numerów jest ok na POC, ale produkcyjnie zwykle potrzebujecie: mapowania na tożsamość firmową, ról oraz ograniczeń dostępu do wrażliwych danych (np. marże, rabaty, dane osobowe). 

PRD

 

ARCHITECTURE

Observability i operacje: logi lokalne bez monitoringu/alertów
JSONL na dysku jest dobry do analizy, ale brakuje mi: metryk (czas SQL/LLM), alertów (spike błędów), rotacji/retencji, backupu oraz korelacji requestów.

Bezpieczeństwo webhooka WhatsApp
Tunel rozwiązuje problem sieci, ale nadal macie publiczny endpoint: weryfikacja podpisów/tokenów, rate limiting, ochrona przed spamem, oraz procedury na incydenty.

4. ALTERNATYWNE PODEJŚCIA (dla każdej słabej strony)
(1) Prywatność danych vs Answer Formatter w Claude

Co zamiast tego?
a) Formatowanie odpowiedzi lokalnie (szablony + proste reguły + tabelaryczne odpowiedzi), albo
b) „Minimal disclosure”: do LLM wysyłacie tylko zagregowane wyniki (np. top-N z anonimizacją) / same nagłówki / statystyki, albo
c) Wrażliwe środowisko LLM (np. rozwiązanie, które spełnia Wasze wymagania compliance — jeśli polityka firmy dopuszcza).

Dlaczego lepsze?
Usuwa/ogranicza transfer danych biznesowych poza sieć firmową i eliminuje największą niewiadomą audytową (sprzeczność z NF-03). 

PRD

 

TECHSTACK

Trade-off
Gorsza „naturalność” odpowiedzi (a), większa złożoność logiki prezentacji (a/b), potencjalnie większy koszt/utrzymanie (c).

(2) LLM → SQL ad-hoc bez guardrails

Co zamiast tego?
a) „Constrained SQL”: LLM generuje strukturalny plan (JSON: view, kolumny, filtry, agregacje, limit), a Wy kompilujecie to do SQL, lub
b) Walidacja SQL parserem/AST: dopuszczacie tylko SELECT, tylko BI.*, obowiązkowy TOP/LIMIT, blokada CROSS JOIN, blokada wielkich IN, timeouty, maks. liczba joinów, itd.

Dlaczego lepsze?
Zamieniacie „dowolny T-SQL” na kontrolowany podzbiór → mniej awarii i mniej ryzyka „zapytanie zabiło serwer”.

Trade-off
Mniejsza elastyczność ad-hoc i więcej kodu platformowego (ale to kod, który zwraca się stabilnością).

(3) Wydajność: DirectQuery + widoki

Co zamiast tego?
a) Dla Power BI: Import/Incremental Refresh zamiast DirectQuery dla ciężkich obszarów, albo hybryda,
b) Materializacja: ETL do tabel faktów/wymiarów (mini-DWH) zamiast tylko widoków,
c) Oddzielenie obciążenia: replika/read-replica lub osobna instancja pod BI/bota.

Dlaczego lepsze?
Stabilizuje latencję i chroni ERP/SQL przed „bursts” z raportowania; spełnienie NF-01 robi się realniejsze. 

PRD

 

TECHSTACK

Trade-off
Mniej „zawsze aktualne” (a/b), więcej infrastruktury i procesów danych (b/c).

(4) Brak procesu migracji/deploymentu widoków

Co zamiast tego?
a) Wprowadzić migracje DB (np. podejście typu „schema-as-code”: skrypt wdrożeniowy + kontrola wersji + pipeline),
b) Automatyczne porównanie „repo vs DB” (drift detection) i testy (np. czy widoki się kompilują, czy kluczowe zapytania regresyjne działają).

Dlaczego lepsze?
Mniej „niespodzianek” na produkcji i mniej sytuacji, gdzie Power BI przestaje działać po zmianie widoku.

Trade-off
Koszt zbudowania CI/CD dla SQL i dyscyplina release’ów.

(5) Autoryzacja i kontrola dostępu

Co zamiast tego?
a) Mapowanie użytkownika bota do firmowej tożsamości (np. AD/SSO po stronie bota),
b) Role + Row Level Security (np. przez widoki per rola / predicate’y / filtr na jednostkę organizacyjną),
c) „Bezpieczne odpowiedzi”: bot odmawia/ogranicza wrażliwe pola.

Dlaczego lepsze?
Whitelist nie skaluje się organizacyjnie i nie chroni przed „zbyt szeroką” ekspozycją danych.

Trade-off
Większa złożoność (zarządzanie rolami, onboarding, support).

(6) Observability/operacje

Co zamiast tego?
a) Centralne logowanie + dashboardy + alerty (czas odpowiedzi, błędy SQL, błędy LLM, timeouts),
b) Metryki per etap pipeline’u i correlation-id per request,
c) Retencja/rotacja logów + backup + polityka danych w logach (maskowanie).

Dlaczego lepsze?
Bez tego „99% uptime w godzinach pracy” jest deklaracją bez możliwości egzekucji. 

PRD

Trade-off
Dodatkowe narzędzia i utrzymanie.

(7) Bezpieczeństwo webhooka WhatsApp

Co zamiast tego?
a) Weryfikacja podpisu i challenge (zgodnie z wymaganiami Meta),
b) Rate limiting + WAF rules po stronie Cloudflare,
c) Kolejka (np. buforowanie requestów) żeby nie zabić bota spike’iem.

Dlaczego lepsze?
Publiczny endpoint będzie „sondowany” — lepiej założyć to z góry.

Trade-off
Trochę więcej konfiguracji i elementów operacyjnych.

5. PYTANIA KRYTYCZNE (przed wdrożeniem)

Co dokładnie trafia do Claude w każdym kroku? Czy w jakimkolwiek miejscu wysyłacie rekordy/wiersze danych (np. w Answer Formatter), czy trzymacie się zasady „tylko pytanie + schemat”? 

PRD

 

TECHSTACK

Jakie są limity i bezpieczniki dla SQL? (obowiązkowy TOP, timeouty, max. liczba wierszy, blokady „ciężkich” operatorów, kontrola joinów) oraz jak obsłużycie „pytanie, które generuje zapytanie zabijające serwer”?

Jak będzie wyglądał proces publikacji zmian w BI.*? Kto zatwierdza, jak testujecie regresję, jak robicie rollback i jak unikacie driftu między repo a SQL Server?

Jakie dane bot nie może ujawniać i jak to egzekwujecie? (RODO, dane osobowe, rabaty, marże, dane płacowe, itd.) + czy potrzebujecie RLS.

Jaki jest spodziewany profil obciążenia? Ile równoczesnych użytkowników Power BI (DirectQuery) i bota, jakie SLA dla SQL Server, oraz czy macie plan separacji obciążeń, jeśli zacznie brakować zasobów?

Jeśli chcesz, mogę też dopisać krótką „listę kontrolną produkcyjną” (guardrails SQL, polityka danych w promptach, monitoring, RLS) dopasowaną do tego projektu.

Rezencja3:
Przeglad Architektury: Faza 2 - Warstwa Semantyczna BI + Bot Pytan
Recenzja architektoniczna | 2026-03-03

1. Ocena ogolna: 7/10
Solidna, pragmatyczna architektura na etapie MVP, dobrze dostosowana do realiow malego zespolu i istniejacej infrastruktury Windows/SQL Server. Szczegolnie dojrzale jest podejscie do bezpieczenstwa danych (separacja schematow, read-only, Claude API otrzymuje wylacznie metadane). Glowne ryzyka dotycza skalowalnosci NLP pipeline, braku warstwy testowej i nadmiernej zaleznosci od Claude API jako jedynego silnika decyzyjnego.

2. Mocne strony
2.1 Przemyslana separacja bezpieczenstwa danych
Architektura konsekwentnie realizuje zasade least privilege: konto CEiM_BI nie widzi CDN.*, Claude API otrzymuje wylacznie schemat BI (nazwy kolumn i opisy), a zadne dane rekordowe nie opuszczaja sieci firmowej jako prompt. To dojrzale podejscie minimalizujace ryzyko wycieku danych w kontekscie GDPR i wrazliwosci danych ERP.
2.2 Warstwa semantyczna jako single source of truth
Schemat BI.* jako jedyny interfejs danych dla bota, Power BI, Excela i agenta ERP to architektonicznie czyste rozwiazanie. Eliminuje duplikacje logiki JOINow, centralizuje definicje biznesowe i sprawia ze zmiana w widoku automatycznie propaguje sie do wszystkich konsumentow. Wersjonowanie w Git dodaje audytowalnosc.
2.3 Progresywne kanaly komunikacji
Strategia Telegram najpierw, WhatsApp potem to rozsadna decyzja. Telegram z long pollingiem nie wymaga publicznego endpointu - pozwala przetestowac caly pipeline NLP bez konfiguracji tuneli i weryfikacji Meta Business. Minimalizuje ryzyko wdrozeniowe.
2.4 Biblioteka raportow jako mechanizm uczenia sie
Pipeline gotowy raport -> ad-hoc fallback z logowaniem tworzy naturalna petle doskonalenia: logi ujawniaja powtarzajace sie pytania, te staja sie gotowymi raportami, co skraca czas odpowiedzi i zwieksza niezawodnosc.
2.5 Spojnosc technologiczna z Faza 1
Te same narzedzia (Python, pyodbc, SQLite FTS5, model repozytorium) minimalizuja koszt kontekstu. Wspolne zaleznosci ulatwiaja deployment i utrzymanie.
2.6 Architektura kanal to warstwa transportowa
Oddzielenie logiki biznesowej od warstwy transportowej jest prawidlowe. Dodanie nowego kanalu (Teams, wewnetrzny czat) wymaga wylacznie nowego adaptera.

3. Slabe strony
3.1 Potrojne wywolanie Claude API na jedno pytanie
W sciezce ad-hoc bot wykonuje do trzech wywolan Claude API: (1) Report Matcher, (2) SQL Generator, (3) Answer Formatter. Przy SLA < 30 sekund, kazde wywolanie to ~3-8 sekund - margines jest bardzo waski. Koszt per-pytanie trojkrotnie wyzszy niz moglby byc.
3.2 Brak walidacji generowanego SQL
Nie ma warstwy walidacji miedzy wygenerowanym SQL a jego wykonaniem. Ryzyka: kosztowne zapytania (pelne skanowanie bez WHERE), SQL injection przez sprytne pytanie, komunikaty bledow SQL wyciekajace do odpowiedzi.
3.3 NSSM jako jedyny mechanizm niezawodnosci
Brakuje: health checkow, alertow, graceful shutdown, monitoringu zasobow. NSSM pomoze przy crashu, ale nie przy deadlocku, wycieku pamieci czy utraconym polaczeniu SQL.
3.4 Brak strategii wspolbieznosci
Architektura nie adresuje: puli polaczen SQL, wspolbieznych wywolan Claude API, kolejkowania przy piku. Przy 5+ uzytkownikach pytajacych rownoczenie grozi to timeoutami.
3.5 Brak testow automatycznych i CI/CD
Dla systemu generujacego i wykonujacego SQL dynamicznie brak testow regresyjnych to znaczace ryzyko. Zmiana widoku BI moze zepsuc odpowiedzi bota.
3.6 Pliki .sql jako baza raportow - ograniczona przeszukiwalnosc
Dopasowanie pytania do raportu przez Claude API na bazie pelnej listy nazw. Przy 50+ raportach rosnie prompt, koszt i spada jakosc dopasowania.
3.7 Brak obslugi konwersacji wieloturowych
Bot traktuje kazde pytanie niezaleznie. Brak kontekstu konwersacji, doprecyzowania, korekty wynikow - istotne ograniczenie UX na WhatsApp/Telegram.

4. Alternatywne podejscia
4.1 Redukcja wywolan Claude API (do 3.1)
Co zamias tego: Polaczyc Report Matcher i SQL Generator w jedno wywolanie. Drugie wywolanie (po SQL) formatuje odpowiedz. Sciezka raportowa: 2->1, ad-hoc: 3->2.
Dlaczego lepsze: Latencja i koszt spadaja o ~30-50%. Miesci sie w SLA z bezpiecznym marginesem.
Trade-off: Dluzszy prompt systemowy; trudniejsze debugowanie; koniecznosc parsowania strukturalnej odpowiedzi.
4.2 Walidacja generowanego SQL (do 3.2)
Co zamiast tego: Warstwa walidacji: (a) sqlparse - whitelist operacji (SELECT, TOP, WHERE; blokada EXEC, xp_, INSERT, UPDATE, DELETE), (b) timeout pyodbc (30s), (c) sanitacja komunikatow bledow.
Dlaczego lepsze: Eliminuje klasy atakow i awarii przy ~100 liniach kodu.
Trade-off: +50-100ms; wymaga utrzymania whitelist; zbyt agresywne reguly moga blokowac prawidlowe zapytania.
4.3 Health check + alerty (do 3.3)
Co zamiast tego: Endpoint /health (FastAPI - i tak bedzie dla WhatsApp) + watchdog (Task Scheduler co 5min): ping /health, SELECT 1, przy awarii restart + alert Telegram.
Dlaczego lepsze: Wykrywa problemy ktorych restart nie rozwiaze; daje widocznosc na stan systemu.
Trade-off: Dodatkowy skrypt; false-positive wymagaja kalibracji.
4.4 Connection pooling (do 3.4)
Co zamiast tego: pyodbc pooling=True lub aioodbc + asyncio. Semaphore limitujacy rownoczene wywolania Claude API (max 3).
Dlaczego lepsze: Eliminuje overhead polaczen; zapobiega wyczerpaniu przy piku.
Trade-off: Async wymaga refaktoru synchronicznego kodu.
4.5 SQLite FTS5 jako magazyn raportow (do 3.6)
Co zamiast tego: Metadane w SQLite z FTS5 (spojnosc z docs.db). Report Matcher przeszukuje FTS5, do Claude API trafia top-5 kandydatow zamiast pelnej listy.
Dlaczego lepsze: Skaluje sie; mniejszy prompt = nizszy koszt i lepsza precyzja.
Trade-off: SQLite wymaga toolingu CRUD; wersjonowanie mniej naturalne (ale SQL templates moga zostac w plikach, indeks FTS budowany automatycznie).
4.6 Minimalna historia konwersacji (do 3.7)
Co zamiast tego: Dict per user_id z ostatnimi 3 turami, dolaczany do promptu. Czyszczenie po 15 minutach nieaktywnosci.
Dlaczego lepsze: Naturalne doprecyzowanie dramatycznie poprawia UX na WhatsApp.
Trade-off: Wiekszy prompt = wyzszy koszt; stan w pamieci (reset przy restarcie).

5. Pytania krytyczne
Pytanie 1: Jak zachowa sie system przy aktualizacji ERP zmieniajacej schemat CDN?
Widoki BI zaleza od tabel CDN.*. Aktualizacja Comarch ERP XL moze zmienic schemat - czy istnieje mechanizm wykrywania zmian? Broken view nie rzuci bledu do momentu odpytania. Rozwazyc smoke test (SELECT TOP 1 z kazdego widoku) po kazdej aktualizacji.
Pytanie 2: Jaki jest plan B, gdy Claude API jest niedostepne?
Bot jest w 100% zalezny od Claude API. Przy awarii jest kompletnie niefunkcjonalny. Czy istnieje fallback - np. keyword matching dla Report Matchera (bez LLM) + surowe dane tabelaryczne?
Pytanie 3: Jak beda zarzadzane uprawnienia danych na poziomie uzytkownika?
Kazdy uzytkownik na whitelist widzi wszystkie dane w BI.*. Handlowiec widzi marze wszystkich kontrahentow, magazynier dane finansowe. Czy to akceptowalne? Architektura nie przewiduje row-level security.
Pytanie 4: Co sie stanie z logami zawierajacymi dane osobowe?
Pytanie o zamowienia Jana Kowalskiego generuje log z danymi osobowymi. Czy logi podlegaja GDPR? Plan retencji i anonimizacji? Lokalnosc to decyzja infrastrukturalna, nie prawna.
Pytanie 5: Jak wyglada rollback przy wadliwym widoku BI?
Developer tworzy widok z bledem logicznym. Bot zwraca zle dane. Ile czasu minie zanim ktos zauwazy? Czy istnieje walidacja przed deploymentem i szybki rollback?

Podsumowanie
Architektura Fazy 2 jest dobrze dopasowana do skali projektu. Kluczowe ryzyka: brak walidacji SQL, zaleznosc od Claude API bez fallbacku, brak testow. Rekomendowane priorytety:

Warstwa walidacji SQL - niski koszt, eliminuje krytyczne ryzyka
Health check + alerty - widocznosc na stan systemu
Minimalna historia konwersacji - kluczowa poprawa UX