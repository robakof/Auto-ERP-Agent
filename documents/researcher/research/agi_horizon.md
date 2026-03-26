# Horyzont AGI i gotowość infrastrukturalna

_Status: wersja badawcza z dnia 2026-03-12._

## 1) Podsumowanie wykonawcze

### Najkrótsza odpowiedź

Nie ma dziś twardego konsensusu, że AGI pojawi się w ciągu ~2 lat. Najbardziej „krótkoterminowe” publiczne stanowiska pochodzą od osób związanych z Anthropic i części środowiska forecastingowego; bardziej ostrożne są stanowiska części akademików oraz niektórych liderów labów. Realistyczny obraz na marzec 2026 wygląda tak:

- **„AGI w 2 lata” jest możliwe, ale nie jest konsensusem.**
- **„Agentowa infrastruktura” dojrzewa szybciej niż konsensus na temat samego AGI.**
- **Najbardziej prawdopodobny punkt krytyczny dla małej firmy nie leży w modelu bazowym, tylko w integracji, orkiestracji, ewaluacji, bezpieczeństwie i odporności operacyjnej.**
- **Największe ryzyko geopolityczne dla AI to nie abstrakcyjne „WW3”, tylko konkretne zaburzenia: Tajwan/chipy, eksport, energia, priorytetyzacja obliczeń i presja regulacyjna.**

### Wniosek strategiczny dla Was

Jeżeli budujecie infrastrukturę agentową dla ERP/operacji, to **najbardziej trwałe aktywo nie brzmi „mamy najlepszy prompt”**, tylko:

1. **warstwa kontekstu i ontologii procesu**,
2. **warstwa narzędzi i integracji z systemami klienta**,
3. **warstwa orkiestracji agentów i kontroli stanu**,
4. **warstwa ewaluacji / trace / replay / audit**,
5. **warstwa bezpieczeństwa, uprawnień i human-in-the-loop**,
6. **przenośność między modelami i tryb degradacji przy awarii chmury/API**.

To są elementy, które mają wartość zarówno gdy AGI przyjdzie szybko, jak i gdy przyjdzie wolniej, będzie ograniczone regulacyjnie albo zmonopolizowane przez kilku dostawców.

---

## 2) Tabela scenariuszy

| Scenariusz | Horyzont AGI | Geopolityka / infrastruktura | Co to znaczy dla projektu |
|---|---|---|---|
| **Optymistyczny** | Do 2027–2028 pojawiają się systemy „AGI-adjacent”: bardzo mocne modele reasoning + długie workflow agentowe + dojrzałe narzędzia wykonawcze. Nie oznacza to jeszcze pełnej niezawodnej autonomii we wszystkich kontekstach. | Brak dużej wojny w Cieśninie Tajwańskiej; chmura i GPU drożeją, ale pozostają dostępne. Regulacje rosną, lecz nie blokują zastosowań biznesowych klasy „co-pilot + bounded autonomy”. | **Budować szybko.** Największa wartość jest w wdrożeniu agentów do realnych procesów klienta, a nie w gonieniu benchmarków. Rynek premiuje tych, którzy mają działający system operacyjny dla agentów. |
| **Bazowy** | „Weak AGI” / szeroka ogólność z ograniczeniami około 2028 jest zgodna z częścią rynków predykcyjnych; pełniejsze AGI częściej wychodzi później. W 2026–2028 dominują systemy bardzo silne, ale nadal poszarpane („jagged”) i wymagające nadzoru. | Brak pełnej wojny światowej, ale rosną: napięcia USA–Chiny, kontrola eksportu, presja energetyczna, lokalna suwerenność AI, fragmentacja regulacyjna. Okresowe niedobory / drogie okna dostępu do mocy obliczeniowej. | **Budować „model-agnostic control plane”.** Firma wygrywa, jeśli ma przenośną architekturę agentów, mocne evale, tryb awaryjny i głęboką integrację domenową z ERP. |
| **Pesymistyczny** | Albo AGI opóźnia się przez wąskie gardła (chipy, energia, dane, regulacje), albo zdolności rosną szybko, lecz dostęp do nich staje się ograniczony do kilku podmiotów / zastosowań uprzywilejowanych. | Blokada lub wojna wokół Tajwanu, twarde restrykcje eksportowe, militaryzacja łańcuchów dostaw, awarie chmury/API, priorytetyzacja wojska i państwa nad cywilami. Możliwe twardsze ograniczenia dla autonomicznych agentów. | **Przetrwa to, co działa lokalnie i audytowalnie.** Kluczowe stają się: open weights, lokalny fallback, kolejki zadań, cache procedur, możliwość przejścia z autonomii do assistive mode oraz własne dane/procedury klienta. |

---

## 3) Najważniejsze odpowiedzi na pytania badawcze

### 3.1. Trajektoria do AGI — stan obecny (marzec 2026)

#### Co dziś jest najuczciwszym opisem „konsensusu”?

Najuczciwsza odpowiedź brzmi: **konsensusu nie ma**.

W praktyce istnieją dziś co najmniej cztery warstwy prognoz:

1. **Liderzy labów frontier** — część z nich komunikuje bardzo krótkie horyzonty lub mówi, że przejście może być szybkie.
2. **Rynki predykcyjne** — zwykle są mniej skrajne i bardzo zależne od definicji pytania.
3. **Badacze/autorzy AI z ankiet eksperckich** — historycznie ich mediany są znacznie dalsze niż narracja „2 lata”, choć przesunęły się do przodu.
4. **Raporty bezpieczeństwa i governance** — podkreślają, że niepewność jest tak duża, że instytucje muszą przygotowywać się zarówno na bardzo szybki, jak i umiarkowany scenariusz.

#### Najbardziej użyteczne definicje AGI

W praktyce są dziś trzy rodziny definicji:

- **Poziomy sprawności / zakresu kompetencji** — np. DeepMind „Levels of AGI”.
- **Poziomy bezpieczeństwa i zdolności katastroficznych** — np. Anthropic Responsible Scaling Policy i AI Safety Levels / capability thresholds.
- **Definicje ekonomiczno-zadaniowe** — typu „system potrafi wykonać większość ekonomicznie wartościowej pracy umysłowej” albo „przebija człowieka w prawie wszystkich zadaniach poznawczych”.

Dla zastosowań biznesowych najpraktyczniejsze jest rozróżnienie:

- **AGI jako szeroka użyteczność zadaniowa**,
- **AGI jako niezawodna autonomia operacyjna**,
- **AGI jako system zdolny do samodzielnego przyspieszania badań AI i rozwoju oprogramowania**.

To nie są tożsame momenty.

#### Co wydaje się ważniejsze od sporów definicyjnych?

Dla Was najważniejsze pytanie nie brzmi „czy to już AGI?”, tylko:

> Czy system potrafi samodzielnie prowadzić długie, wieloetapowe workflow biznesowe z akceptowalnym poziomem błędów, audytowalnością i kontrolą ryzyka?

Jeżeli odpowiedź brzmi „coraz częściej tak, ale jeszcze nierówno”, to infrastruktura agentowa staje się aktywem już teraz — niezależnie od etykiety AGI.

---

### 3.2. Czynniki przyspieszające

#### A. Scaling laws: raczej nie „umarły”, ale zmieniły kształt

Najbardziej wiarygodny obraz na 2026 jest następujący:

- klasyczne skalowanie treningowe nadal działa,
- pojawił się nowy wymiar: **inference-time compute / test-time compute**,
- większym problemem stają się nie tylko algorytmy, lecz także energia, chipy, opóźnienia, dane i koszt wdrożenia.

W praktyce oznacza to, że postęp nie musi już zależeć wyłącznie od coraz większego treningu. Można „dokupić myślenie” na etapie inferencji.

#### B. Inference-time compute zmienia trajektorię

To prawdopodobnie najważniejsza zmiana jakościowa od końca 2024.

Modele reasoning (o1/o3/o4, Claude w trybach thinking, Gemini Deep Think i podobne) pokazują, że:

- coraz więcej zdolności można „wydobywać” po treningu,
- benchmarki matematyczne, programistyczne i badawcze reagują bardzo dobrze na dodatkowy budżet myślenia,
- granica między „modelem” a „systemem” zaciera się.

Dla AGI oznacza to, że **nawet bez jednego magicznego przełomu architektonicznego systemy mogą zacząć zachowywać się coraz bardziej „ogólnie” dzięki kombinacji: reasoning + narzędzia + pamięć + planowanie + wykonanie**.

#### C. Dojrzewanie frameworków agentowych

To bardzo mocny sygnał rynkowy.

W 2025–2026 przeskok nie polega już tylko na tym, że modele są lepsze, ale że ekosystem buduje warstwy potrzebne do użycia ich w pracy:

- trwałe workflow i grafy zadań,
- stan i pamięć,
- trace / observability / evals,
- HITL i approval gates,
- kontrola narzędzi i uprawnień,
- protokoły interoperacyjności agentów i narzędzi.

To właśnie wspiera tezę, że **wartość przesuwa się z „samego modelu” w stronę „infrastruktury wykonania”**.

#### D. Open models przyspieszają dyfuzję

Open weights i open-source reasoning models działają w dwóch kierunkach:

- obniżają koszt i skracają czas adaptacji,
- zmniejszają trwałość przewagi czysto modelowej zamkniętych vendorów,
- zwiększają odporność firm na vendor lock-in i scenariusze geopolityczne.

Z perspektywy małej firmy to dobra wiadomość: można budować architekturę, która ma fallback lokalny lub semi-lokalny.

#### E. Synthetic data / self-play

To nie jest jeszcze „darmowy nieskończony wzrost”, ale też nie wygląda na ślepą uliczkę.

Najbardziej realistyczny wniosek:

- synthetic data pomaga, zwłaszcza w reasoning, alignment i task-specific tuning,
- ale rośnie ryzyko dryfu, błędów, zawężenia rozkładu danych i powielania niepożądanych wzorców,
- więc synthetic data raczej **przyspiesza w pewnych reżimach**, niż zastępuje potrzebę dobrych danych i zewnętrznych sygnałów weryfikacji.

---

### 3.3. Czynniki spowalniające i ryzyka

#### A. Geopolityka i chipy

Najbardziej krytyczny punkt systemowy: **koncentracja zaawansowanej produkcji chipów w Tajwanie**.

Dla AI jest to ryzyko pierwszego rzędu, nie „tail risk”. Nawet częściowe zakłócenie:

- wydłuża cykle budowy nowych klastrów,
- podbija koszt HBM / zaawansowanego pakowania / logiki,
- ogranicza dostępność najbardziej zaawansowanych akceleratorów,
- wzmacnia znaczenie priorytetyzacji politycznej i wojskowej.

#### B. „WW3” trzeba rozbić na realistyczne mechanizmy

Najbardziej użyteczne dla planowania są nie metafory, tylko scenariusze mechaniczne:

1. **Blokada Tajwanu bez pełnej wojny globalnej**  
   Najbardziej niebezpieczna dla AI/chipów relacja ryzyko → prawdopodobieństwo.

2. **Ograniczony konflikt regionalny USA–Chiny z cyber / sankcjami / kontrolą eksportu**  
   Bardzo groźny dla dostępności chmury, dostępu do najnowszych GPU i reżimów compliance.

3. **Szersza sekwencja kryzysów (np. energia/logistyka/Middle East + Europa + Indo-Pacific)**  
   Mniej bezpośrednia dla leading-edge chips niż Tajwan, ale groźna dla energii, gazów technicznych, transportu i kosztów operacyjnych.

#### C. Regulacje

Regulacje najprawdopodobniej **nie zatrzymają AGI jako badań**, ale mogą realnie spowolnić lub zmienić deployment:

- **UE** — obowiązki dla GPAI i systemów o ryzyku systemowym, compliance, testy, dokumentacja, raportowanie, cyberbezpieczeństwo.
- **USA** — większy nacisk na konkurencyjność, standardy agentowe, bezpieczeństwo narodowe, walkę z fragmentacją regulacyjną stanów i politykę eksportową.
- **Chiny** — większy nacisk na bezpieczeństwo informacji, filingi i etykietowanie treści generowanych przez AI.

Czy to zabije autonomicznych agentów biznesowych? Raczej nie. Ale może wymusić:

- więcej audit trails,
- wyraźne granice autonomii,
- polityki override / approval,
- monitoring post-deployment,
- większe koszty zgodności dla sprzedaży enterprise / regulated sectors.

#### D. Alignment i safety

Na dziś bardziej realistyczny jest scenariusz:

- **więcej internal gating, preparedness frameworks i selektywnego ograniczania deploymentu**,
- niż globalne moratorium.

Moratorium w skali świata wydaje się mało prawdopodobne, ale lokalne wstrzymania wdrożeń, ograniczenia funkcji lub blokady dla konkretnych capability bands są jak najbardziej realne.

#### E. Energia

Energia jest już realnym ograniczeniem w horyzoncie 2 lat — niekoniecznie w sensie „koniec AI”, ale w sensie:

- opóźnień przyłączeń,
- kosztu operacyjnego,
- politycznej presji na data center,
- preferencji dla dużych graczy z zabezpieczoną mocą.

Dla małej firmy oznacza to, że lokalna lub prywatna infrastruktura inference będzie miała sens tylko tam, gdzie daje przewagę odporności lub kosztu całkowitego, a nie jako odruch ideologiczny.

---

### 3.4. Co oznacza „być gotowym” — AGI-ready infrastructure

#### Elementy trwałe (przetrwają zmianę modelu bazowego)

1. **Warstwa narzędzi i integracji**  
   ERP, CRM, DMS, BI, e-mail, kalendarz, pliki, API, bazy danych, systemy tickets/approval.

2. **Warstwa orkiestracji i stanu**  
   Graf zadań, delegacja ról, retry, kolejki, timeouts, checkpoints, pamięć operacyjna.

3. **Warstwa kontekstu / ontologii domenowej**  
   Słowniki pojęć klienta, mapy procesów, polityki, uprawnienia, słowniki wyjątków, reguły interpretacji danych.

4. **Warstwa ewaluacji**  
   Golden tasks, acceptance tests, trace, replay, cost/error budgets, regression suites.

5. **Warstwa bezpieczeństwa i governance**  
   Uprawnienia, segregacja obowiązków, approval gates, audyt decyzji, sandboxy narzędziowe.

6. **Warstwa przenośności modeli**  
   Możliwość wymiany modelu / dostawcy / trybu działania bez przepisywania całej logiki biznesowej.

7. **Human fallback mode**  
   System musi umieć przejść z pełniejszej autonomii do „assistant mode” bez załamania procesu.

#### Elementy tymczasowe (duże ryzyko przepisywania)

1. **Prompt-hacking jako główny mechanizm kontroli**
2. **Ręczne guardraile sklejone z jednym vendor API**
3. **Routing oparty o kruche heurystyki zamiast obserwowalnych polityk**
4. **Obejścia wynikające z małego kontekstu lub słabej pamięci modeli**
5. **Twarde rozdzielenie „chat” i „workflow”, jeśli modele staną się znacznie bardziej wykonawcze**

#### Jak wygląda AGI-ready architecture w praktyce?

Najpraktyczniejszy model dla małej firmy:

- **control plane** — polityki, routing, uprawnienia, observability, metryki, evale,
- **execution plane** — agenci wykonawczy, narzędzia, kolejki, stan workflow,
- **context plane** — wiedza klienta, ontologia, dokumenty, historia działań,
- **safety plane** — approval, risk scoring, audyt, sandbox,
- **portability plane** — multi-model, multi-runtime, open/closed fallback.

Nie budować „jednego agenta-geniusza”. Budować **system pracy agentów**.

---

### 3.5. Scenariusze dla branży ERP / wdrożeniowej

#### Co już się zmienia

Branża ERP w 2025–2026 przechodzi z etapu „copilot/QA” do etapu:

- asystentów osadzonych w ERP,
- agentów do konfiguracji, developmentu i transformacji cloud,
- automatyzacji procesów wdrożeniowych,
- agentów operujących na workflow i danych procesowych.

To jest ważne: **vendorzy nie czekają**. Oni już przesuwają produkty z „AI assistant” w stronę „AI agents”.

#### Co oferują duzi vendorzy

- **Comarch** — ChatERP jako wbudowany asystent AI w Enterprise Solutions; sygnał, że nawet vendor regionalny przesuwa UX ERP w stronę natural-language interface.
- **SAP** — Joule for Developers i Joule for Consultants; AI dla developmentu, interpretacji kodu, automatyzacji, konfiguracji i transformacji SAP; rośnie też warstwa agentowa Joule.
- **Oracle** — AI Agents for Fusion Applications + AI Agent Studio; wbudowane agenty, marketplace, observability/evaluation, możliwość modyfikacji i budowy własnych agentów.
- **Microsoft/Dynamics** — oficjalnie mówi już o „agentic ERP”, custom agents i AI w rdzeniu biznesowych workflow.

#### Czy duży vendor może zbudować to, co budujecie?

Tak — i częściowo już to robi. Ale to nie oznacza automatycznie, że Was wyprze.

Duży vendor z reguły wygrywa w:

- dostępie do platformy,
- dystrybucji,
- standardowych use-case’ach,
- zgodności i bezpieczeństwie enterprise,
- bazowych agentach osadzonych w produkcie.

Mała firma może wygrać w:

- szybkości iteracji,
- specjalizacji branżowej,
- jakości wdrożenia w konkretnym procesie klienta,
- warstwie cross-system orchestration (nie tylko „wewnątrz jednego ERP”),
- zaufaniu klienta i przełożeniu AI na realny proces operacyjny,
- lepszym połączeniu wiedzy metodologicznej z danymi klienta.

#### Gdzie jest moat dla małej firmy?

Najbardziej prawdopodobne fosy obronne:

1. **Ontologia procesu i danych klienta**  
   Nie „dane” w ogóle, tylko uporządkowane reprezentacje procesów, wyjątków, polityk i relacji między systemami.

2. **Metodologia wdrożeniowa zakodowana w systemie**  
   To, jak konfigurujecie, testujecie, odbieracie i utrzymujecie ERP, może stać się softwarem.

3. **Evale na realnych zadaniach ERP**  
   Własny zestaw testów wdrożeniowych i operacyjnych jest trudny do skopiowania i bardzo cenny.

4. **Integracja wielosystemowa**  
   Vendor ERP optymalizuje swój ekosystem; Wy możecie optymalizować realne środowisko klienta, które zwykle jest heterogeniczne.

5. **Szybkość uczenia się z wdrożeń**  
   Każdy projekt może dokładać nowe playbooki, reguły wyjątków, traces i acceptance patterns.

6. **Odporność i suwerenność operacyjna**  
   Jeżeli potraficie działać także przy zmianie modelu, regionu, API albo polityki dostawcy, zyskujecie przewagę tam, gdzie klienci boją się zależności.

---

### 3.6. Scenariusz pesymistyczny: disruption

#### Scenariusz A — AGI przychodzi szybciej niż 2 lata i Wasze narzędzia wydają się zbędne

**Co przetrwa:**
- integracje z systemami klienta,
- approval / audit / governance,
- ontologia procesu,
- evale i acceptance tests,
- warstwa wykonawcza i policy layer.

**Dlaczego:**
Nawet bardzo mocny model musi mieć gdzie działać, na czym działać i według jakich zasad działać. Im mocniejszy model, tym bardziej rośnie wartość warstwy kontroli, zgodności i integracji.

#### Scenariusz B — AGI powstaje, ale jest kontrolowane przez 3 firmy i trudno dostępne

**Co przetrwa:**
- przenośna architektura,
- fallback open-weight / private runtime,
- warstwa klientowskiego kontekstu,
- interfejsy narzędzi i workflow.

**Dlaczego:**
Jeśli capability staje się scentralizowane, przewagę daje to, kto najlepiej „opakowuje” ograniczony zasób w działający produkt biznesowy.

#### Scenariusz C — konflikt globalny / regionalny odcina API lub chmurę na tygodnie lub miesiące

**Co przetrwa:**
- lokalny tryb degradacji,
- kolejki i retry,
- cache procedur i dokumentacji,
- półautonomiczne workflow z człowiekiem,
- modele lokalne do prostszych kroków.

**Dlaczego:**
Największym problemem nie jest wtedy jakość modelu, tylko ciągłość działania.

#### Scenariusz D — regulacje ograniczają autonomiczne AI w biznesie

**Co przetrwa:**
- assistive mode,
- audytowalne rekomendacje,
- agent jako wykonawca w ograniczonym zakresie, z akceptacją człowieka,
- pełna rejestracja kroków decyzyjnych.

**Dlaczego:**
Wiele branż będzie mogło używać AI jako „decision support + bounded execution”, nawet jeśli zakazana lub utrudniona będzie pełna autonomia.

---

## 4) Rekomendacje praktyczne na 12–24 miesiące

### A. Budować to, co jest trwałe niezależnie od AGI

1. Ujednolicić **API/tool layer** dla ERP, dokumentów, raportowania i komunikacji.
2. Wdrożyć **workflow state + checkpoints + replay**.
3. Zbudować **eval harness** dla zadań ERP i wdrożeniowych.
4. Zdefiniować **risk tiers** działań agentów (read / suggest / prepare / execute / commit).
5. Przygotować **multi-model routing** i minimalny fallback open-weight.
6. Wprowadzić **audit-first design** od początku.

### B. Nie inwestować nadmiernie w kruche elementy

1. Nie uzależniać architektury od jednego modelu lub jednego prompt pattern.
2. Nie zakładać, że obecne ograniczenia kontekstu i reasoning pozostaną stałe.
3. Nie budować systemu, w którym bezpieczeństwo = „prompt z zakazami”.

### C. Ustawić firmę pod odporność geopolityczną

1. Mieć plan na **awarię chmury/API**.
2. Mieć plan na **wzrost kosztu inferencji**.
3. Mieć plan na **region-lock / export-control / residency requirements**.
4. Mieć plan na **switch z autonomy-first do human-in-the-loop-first**.

### D. Ustawić produkt pod moat, którego vendor ERP nie skopiuje szybko

1. Kodować **metodologię wdrożeń** w produkt.
2. Gromadzić **task traces i acceptance datasets** z realnych projektów.
3. Rozwijać **cross-ERP / cross-system orchestration**.
4. Budować **warstwę wiedzy klienta**, nie tylko interfejs do modelu.

---

## 5) Źródła / wzorce

### DeepMind — Levels of AGI

**Źródło:** paper  
**Data:** 2024  
**Kluczowy wniosek:** DeepMind proponuje praktyczną taksonomię AGI opartą na poziomach sprawności i zakresie zadań. „Competent AGI” jest traktowane jako dobry odpowiednik wielu wcześniejszych definicji AGI, a ówczesne frontier modele były jeszcze niżej, na poziomie „Emerging AGI”.  
**Implikacja dla nas:** Nie warto używać binarnego „AGI / nie-AGI” do decyzji produktowych. Lepiej mierzyć, które klasy zadań biznesowych są już wykonalne niezawodnie i jak rośnie poziom autonomii.  
**Link:** https://arxiv.org/abs/2311.02462

### Anthropic — Responsible Scaling Policy v3

**Źródło:** policy / framework  
**Data:** 2026-02-24  
**Kluczowy wniosek:** Anthropic utrzymuje publiczny framework progów bezpieczeństwa i zobowiązań ochronnych dla coraz bardziej niebezpiecznych capability bands. To nie jest dowód na moratorium, ale dowód, że safety gating staje się operacyjną częścią rozwoju frontier AI.  
**Implikacja dla nas:** Trzeba zakładać, że część capability może być dostępna z opóźnieniem, warunkowo lub w ograniczonych trybach. Architektura musi działać także przy nierównym dostępie do najmocniejszych modeli.  
**Link:** https://www.anthropic.com/news/responsible-scaling-policy-v3

### Anthropic / Dario Amodei — krótkie publiczne timeline’y

**Źródło:** esej / publiczna wypowiedź  
**Data:** 2024-10-11 (nadal istotne w 2026)  
**Kluczowy wniosek:** Dario Amodei argumentował, że systemy o sile „kraju geniuszy w data center” mogą pojawić się już w 2026–2027, niemal na pewno przed 2030. To jeden z najbardziej agresywnych publicznych horyzontów wśród liderów laboratoriów.  
**Implikacja dla nas:** Scenariusz „dużo szybszego niż historycznie zwykliśmy zakładać postępu” trzeba traktować serio operacyjnie, nawet jeśli nie jest konsensusem.  
**Link:** https://www.anthropic.com/research/machines-of-loving-grace

### OpenAI — Planning for AGI and beyond

**Źródło:** blog / stanowisko organizacji  
**Data:** 2024-02-24  
**Kluczowy wniosek:** OpenAI oficjalnie nie podaje twardej daty AGI; komunikat podkreśla, że AGI może nadejść zarówno względnie szybko, jak i dużo później, a tempo przejścia może być wolne albo szybkie.  
**Implikacja dla nas:** Nie wolno budować planu na pojedynczym „CEO quote”. Lepsze jest projektowanie pod niepewność i zmienność trajektorii.  
**Link:** https://openai.com/global-affairs/planning-for-agi-and-beyond/

### Demis Hassabis / Reuters — bardziej ostrożny horyzont

**Źródło:** wywiad prasowy  
**Data:** 2026-01  
**Kluczowy wniosek:** Demis Hassabis ocenił horyzont AGI raczej na 5–10 lat, wskazując, że droga staje się coraz jaśniejsza, ale wciąż brakuje pewnych składników.  
**Implikacja dla nas:** Nawet przy bardzo szybkim postępie modeli sensowne jest planowanie na świat, w którym przez kilka lat mamy „bardzo silne, lecz nierówne systemy”, a nie magiczny punkt przejścia.  
**Link:** https://www.reuters.com/

### Metaculus — weakly general AI

**Źródło:** prediction market  
**Data:** odczyt z marca 2026  
**Kluczowy wniosek:** Rynek Metaculus dla „first weakly general AI system” wskazuje okolice marca 2028 jako bieżący punkt centralny, podczas gdy pytanie o „first general AI system” jest wyraźnie późniejsze (około 2032).  
**Implikacja dla nas:** Rynek sygnalizuje, że „użyteczna szeroka ogólność” może przyjść wcześniej niż „pełniejsze AGI”. To wzmacnia tezę, że wartość najpierw przejmie infrastruktura i wdrożenie.  
**Link:** https://www.metaculus.com/questions/3479/date-weakly-general-ai-is-publicly-known/

### Manifold Markets — definicja bardzo zmienia wynik

**Źródło:** prediction markets  
**Data:** odczyt z marca 2026  
**Kluczowy wniosek:** Różne rynki Manifold dają wyraźnie różne prawdopodobieństwa AGI do 2028, zwykle od niskich do umiarkowanych wartości, zależnie od definicji.  
**Implikacja dla nas:** Nie należy traktować pojedynczego rynku jako „konsensusu”. Sensowniejsze jest projektowanie firmy pod kilka reżimów czasowych.  
**Link:** https://manifold.markets/

### AI Impacts — Thousands of AI Authors on the Future of AI

**Źródło:** survey / paper  
**Data:** 2024-01-05 (ankieta 2023)  
**Kluczowy wniosek:** W ankiecie 2,778 autorów AI 50% prognoza dla HLMI przesunęła się do 2047, a 10% do 2027; niepewność pozostała bardzo szeroka.  
**Implikacja dla nas:** „2 lata” nie jest stanowiskiem mediany badaczy AI, ale nie jest też scenariuszem marginalnym. To wzmacnia potrzebę strategii odpornej na szeroki rozkład wyników.  
**Link:** https://arxiv.org/abs/2401.02843

### Stanford HAI — brak AGI w 2026, rośnie suwerenność AI

**Źródło:** eksperckie przewidywania HAI  
**Data:** 2025-12-15  
**Kluczowy wniosek:** James Landay przewidywał brak AGI w 2026 i silniejszy trend „AI sovereignty”, czyli lokalnego/państwowego kontrolowania modeli, mocy obliczeniowej i danych.  
**Implikacja dla nas:** Nawet bez AGI świat może szybko wejść w fragmentację infrastrukturalną. Przenośność i suwerenność techniczna będą ważniejsze niż idealny benchmark.  
**Link:** https://hai.stanford.edu/news/stanford-ai-experts-predict-what-will-happen-in-2026

### OpenAI — o-series, deep research, operator, 1M context

**Źródło:** ogłoszenia produktowe / research  
**Data:** 2025–2026  
**Kluczowy wniosek:** OpenAI przesunęło front od samego generowania do reasoning, długich workflow badawczych, GUI/browser use i bardzo dużych okien kontekstu. To nie są tylko „lepsze odpowiedzi”, ale bardziej wykonawcze systemy.  
**Implikacja dla nas:** Warstwa agentowa nie jest już przedwczesna. Trzeba projektować systemy pod dłuższe zadania, narzędzia i pamięć operacyjną.  
**Link:** https://openai.com/

### Anthropic — Claude 4 / Claude Code / computer use

**Źródło:** ogłoszenia produktowe / docs  
**Data:** 2025–2026  
**Kluczowy wniosek:** Anthropic mocno pozycjonuje modele jako systemy do długich workflow coding/agentic, z terminalem, repozytorium i computer use.  
**Implikacja dla nas:** Wzrost wartości będzie w środowisku wykonania i kontroli pracy agentów, a nie tylko w samym „czacie”.  
**Link:** https://www.anthropic.com/

### Google DeepMind — Gemini Deep Think i inference-time scaling

**Źródło:** blog / research announcement  
**Data:** 2025-07-21 oraz 2026-02-11  
**Kluczowy wniosek:** DeepMind pokazało złoty medal IMO oraz dalsze dowody, że inference-time scaling nadal działa także poza poziom olimpijski.  
**Implikacja dla nas:** Postęp może przyspieszać bez jednego wielkiego skoku treningowego; to wzmacnia tezę, że AGI-like capability może rosnąć systemowo.  
**Link:** https://deepmind.google/blog/

### DeepSeek-R1 — reasoning open weights jako akcelerator dyfuzji

**Źródło:** paper / release note  
**Data:** 2025-01-20  
**Kluczowy wniosek:** DeepSeek-R1 został wypuszczony jako model reasoning o deklarowanej wydajności porównywalnej z czołówką closed models w wybranych zadaniach, z mocnym komponentem RL i wersjami open.  
**Implikacja dla nas:** Trzeba zakładać szybkie ściskanie przewagi capability i budować przewagę wyżej w stosie.  
**Link:** https://arxiv.org/abs/2501.12948

### LangGraph — workflows vs agents, persistence i deployment

**Źródło:** docs / framework  
**Data:** 2025–2026  
**Kluczowy wniosek:** LangGraph formalizuje różnicę między workflow a agentem i skupia się na trwałym wykonaniu, stanie, debugowaniu i deployment.  
**Implikacja dla nas:** To jest dokładnie warstwa, która ma sens jako trwała inwestycja.  
**Link:** https://langchain-ai.github.io/langgraph/

### Microsoft Agent Framework / AutoGen / Dynamics 365

**Źródło:** dokumentacja / oficjalne ogłoszenia  
**Data:** 2026  
**Kluczowy wniosek:** Microsoft scala ofertę agentową: od frameworków developerskich po „agentic ERP” w Dynamics 365.  
**Implikacja dla nas:** Rynek narzędzi przeszedł z eksperymentu do fazy standaryzacji i enterprise packaging.  
**Link:** https://learn.microsoft.com/ and https://www.microsoft.com/en-us/dynamics-365/

### NIST — AI Agent Standards Initiative

**Źródło:** oficjalna inicjatywa standardyzacyjna  
**Data:** 2026-02-17  
**Kluczowy wniosek:** NIST uruchomił AI Agent Standards Initiative, kładąc nacisk na interoperacyjność, bezpieczeństwo, identyfikację i zaufane wdrożenie agentów.  
**Implikacja dla nas:** Teza „wartość będzie w infrastrukturze organizacyjnej agentów” ma już odzwierciedlenie instytucjonalne. Standardy i interop mogą stać się ważniejsze niż pojedynczy model.  
**Link:** https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure

### Epoch AI — can AI scaling continue through 2030?

**Źródło:** analiza  
**Data:** 2024-08-20 (nadal wpływowa w 2026)  
**Kluczowy wniosek:** Epoch argumentuje, że przy odpowiednich inwestycjach skalowanie treningowe może iść dalej przez dekadę, ale ograniczeniami stają się energia, chipy, dane i opóźnienia.  
**Implikacja dla nas:** Trzeba jednocześnie wierzyć w dalszy postęp capability i przygotować się na wąskie gardła infrastrukturalne.  
**Link:** https://epoch.ai/blog/can-ai-scaling-continue-through-2030

### Epoch / AI Digest — how well did forecasters predict 2025 AI progress?

**Źródło:** analiza forecastingowa  
**Data:** 2026-01-16  
**Kluczowy wniosek:** Forecasterzy trafiali benchmarki lepiej niż realny wpływ gospodarczy; w badanej grupie dominowały raczej krótsze timeline’y i wyższe obawy o ryzyka.  
**Implikacja dla nas:** Warto oddzielić „capability forecast” od „adoption forecast”. Modele mogą rosnąć szybciej niż realna transformacja firm.  
**Link:** https://epoch.ai/gradient-updates/how-well-did-forecasters-predict-2025-ai-progress

### International AI Safety Report 2026

**Źródło:** raport międzynarodowy  
**Data:** 2026-02-03  
**Kluczowy wniosek:** Raport podkreśla szybki wzrost capability, znaczenie inference-time scaling, ale też „jaggedness”, evaluation gap i trudność stabilnej oceny ryzyk.  
**Implikacja dla nas:** Nawet przy bardzo silnych modelach potrzebne są evale, kontrola wdrożeń i architektura tolerująca nierówną niezawodność.  
**Link:** https://internationalaisafetyreport.org/publication/international-ai-safety-report-2026

### ITIF / USITC / SIA — koncentracja produkcji chipów w Tajwanie

**Źródło:** policy analysis  
**Data:** 2025  
**Kluczowy wniosek:** Tajwan odpowiada za dominującą część najbardziej zaawansowanej produkcji logicznej; zakłócenie miałoby bardzo duże konsekwencje cenowe i podażowe.  
**Implikacja dla nas:** To główny powód, dla którego odporność na vendor/region/compute shock nie jest luksusem, tylko wymogiem strategicznym.  
**Link:** https://itif.org/publications/2025/02/10/how-would-a-disruption-to-taiwans-semiconductor-production-affect-the-united-states/

### CSIS — Lights Out? Wargaming a Chinese Blockade of Taiwan

**Źródło:** think tank / wargaming report  
**Data:** 2025  
**Kluczowy wniosek:** Blokada Tajwanu jest realistycznym scenariuszem pośrednim między „pokój” a pełnoskalowa inwazja; skutki gospodarcze globalnie byłyby ogromne.  
**Implikacja dla nas:** W planowaniu ryzyka lepiej modelować blokadę/sankcje/przestoje niż jedynie totalną wojnę.  
**Link:** https://www.csis.org/analysis/lights-out-wargaming-chinese-blockade-taiwan

### RAND — Supply Chain Interdependence and Geopolitical Vulnerability: The Case of Taiwan and High-End Semiconductors

**Źródło:** RAND research  
**Data:** 2023, nadal relewantne  
**Kluczowy wniosek:** Geopolityka i high-end semiconductors są silnie splecione; nawet ograniczone scenariusze przymusu wobec Tajwanu mogą wstrząsnąć globalnym łańcuchem.  
**Implikacja dla nas:** Ryzyko chipowe trzeba traktować jako bazowe założenie strategiczne, a nie egzotyczny dodatek do roadmapy.  
**Link:** https://www.rand.org/pubs/research_reports/RRA1658-1.html

### U.S. BIS — AI diffusion / export controls

**Źródło:** regulacja / polityka eksportowa  
**Data:** 2025–2026  
**Kluczowy wniosek:** Polityka USA wobec eksportu zaawansowanych chipów i AI pozostaje aktywna, ale niestabilna i politycznie korygowana.  
**Implikacja dla nas:** Jeśli biznes będzie zależeć od określonych regionów, modeli lub hardware’u, trzeba liczyć się z nagłą zmianą zasad.  
**Link:** https://www.bis.gov/

### EU AI Act — GPAI/systemic risk obligations

**Źródło:** UE / AI Office  
**Data:** 2025–2026  
**Kluczowy wniosek:** Dla najbardziej zaawansowanych modeli ogólnego przeznaczenia i modeli o ryzyku systemowym wchodzą obowiązki dotyczące testów, dokumentacji, zarządzania ryzykiem i cyberbezpieczeństwa.  
**Implikacja dla nas:** Już teraz opłaca się budować produkt z myślą o śladzie audytowym, monitoringu i kontroli ryzyka.  
**Link:** https://digital-strategy.ec.europa.eu/

### Chiny — generative AI filing i labeling

**Źródło:** regulacje krajowe  
**Data:** 2023–2025, stan na 2026  
**Kluczowy wniosek:** Chiny rozwijają reżim filingów i etykietowania treści AI, łącząc rozwój i bezpieczeństwo informacyjne.  
**Implikacja dla nas:** Fragmentacja regulacyjna będzie rosnąć; „globalny produkt AI” będzie coraz częściej wymagał wariantów regionalnych.  
**Link:** https://www.cac.gov.cn/

### IEA / DOE / White House — energia jako constraint AI

**Źródło:** raporty i polityka publiczna  
**Data:** 2025–2026  
**Kluczowy wniosek:** Zapotrzebowanie energetyczne data center rośnie tak szybko, że staje się problemem infrastrukturalnym i politycznym; w USA temat trafił wprost do polityki energetycznej i AI.  
**Implikacja dla nas:** Dostępność i koszt inferencji mogą przestać być prostą funkcją „cena API spada co kwartał”.  
**Link:** https://www.iea.org/ and https://www.energy.gov/ and https://www.whitehouse.gov/

### Comarch — ChatERP

**Źródło:** produkt vendorowy  
**Data:** stan na 2026  
**Kluczowy wniosek:** Comarch ma już wbudowanego asystenta AI pozwalającego komunikować się z ERP w języku naturalnym.  
**Implikacja dla nas:** Nawet vendor regionalny już internalizuje interfejs konwersacyjny i AI layer; przewaga nie może polegać tylko na „chat do ERP”.  
**Link:** https://www.comarch.pl/erp/asystent-ai/

### SAP — Joule for Developers

**Źródło:** produkt vendorowy  
**Data:** stan na 2026  
**Kluczowy wniosek:** SAP używa AI do generowania aplikacji, logiki, testów, automatyzacji procesów i migracji kodu, w tym do transformacji z klasycznego ERP do S/4HANA Cloud.  
**Implikacja dla nas:** Część pracy developerskiej i konfiguracyjnej będzie coraz bardziej skompresowana przez vendor tooling; wartość przesunie się w jakość procesu, integracji i orkiestracji.  
**Link:** https://www.sap.com/products/artificial-intelligence/joule-for-developers.html

### SAP — Joule for Consultants

**Źródło:** produkt vendorowy  
**Data:** stan na 2026  
**Kluczowy wniosek:** SAP tworzy osobną ofertę AI dla konsultantów wdrożeniowych: konfiguracja, interpretacja ABAP, najlepsze praktyki, wskazówki projektowe i przyspieszenie transformacji cloud.  
**Implikacja dla nas:** SAP bezpośrednio wchodzi w obszar, który wcześniej był „know-how partnerów wdrożeniowych”. To zwiększa presję na posiadanie własnej metody i własnych evali.  
**Link:** https://www.sap.com/poland/products/artificial-intelligence/ai-assistant/sap-consulting-capability.html

### SAP — Joule + agenci dla core functions

**Źródło:** produkt vendorowy  
**Data:** stan na 2026  
**Kluczowy wniosek:** SAP komunikuje Joule jako warstwę agentową dla wszystkich głównych funkcji biznesowych i dla systemów SAP oraz non-SAP.  
**Implikacja dla nas:** Cross-system orchestration jest bardzo ważne — duzi gracze też chcą przejąć tę warstwę.  
**Link:** https://www.sap.com/products/artificial-intelligence/ai-assistant.html

### Oracle — AI Agents for Fusion Applications

**Źródło:** produkt vendorowy  
**Data:** stan na 2026  
**Kluczowy wniosek:** Oracle oferuje wbudowane agenty dla procesów enterprise, AI Agent Studio do modyfikacji i budowy własnych agentów oraz framework observability/evaluation.  
**Implikacja dla nas:** Oracle pokazuje, że duzi vendorzy rozumieją już potrzebę nie tylko agentów, ale i warstwy pomiaru jakości. To potwierdza, że eval/trace to trwały element stacku.  
**Link:** https://www.oracle.com/applications/fusion-ai/ai-agents/

### Deloitte — State of AI in the Enterprise 2026

**Źródło:** raport rynkowy  
**Data:** 2026  
**Kluczowy wniosek:** Dostęp pracowników do AI wzrósł w 2025 o 50%, a liczba firm z dużym odsetkiem projektów w produkcji ma się szybko podwoić; jednocześnie pełna „reimagination” biznesu jest rzadsza niż zwykłe podnoszenie produktywności.  
**Implikacja dla nas:** Adoption rośnie, ale nie jest automatyczne. Kto dostarcza AI wpinane w realne procesy i mierzalny efekt, ma przewagę nad tym, kto sprzedaje „inteligencję” bez wdrożenia.  
**Link:** https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/content/state-of-ai-in-the-enterprise.html

---

## 6) Pytania, na które nadal nie ma dobrej odpowiedzi

1. **Jak dokładnie zdefiniować punkt, w którym agent „prowadzi biznes” zamiast tylko wspierać ludzi?**  
   Mamy definicje capability, ale słabsze definicje autonomii organizacyjnej.

2. **Jak szybko duzi vendorzy ERP przejdą od agentów wspierających do agentów konfigurujących i commitujących zmiany end-to-end?**  
   Kierunek jest jasny, ale tempo wdrożeń produkcyjnych pozostaje niepewne.

3. **Jak trwałe okażą się obecne przewagi reasoning models po wzroście kosztów inferencji?**  
   Może się okazać, że capability rośnie szybciej niż ekonomika użycia w produkcji.

4. **Na ile synthetic data i self-play pozwolą ominąć wąskie gardło danych bez utraty jakości i stabilności?**

5. **Czy do 2028 dojdzie do realnej priorytetyzacji mocy obliczeniowej na potrzeby bezpieczeństwa narodowego kosztem klientów komercyjnych?**

6. **Jak głęboko UE i inne jurysdykcje będą ograniczać pełną autonomię agentów w procesach biznesowych wysokiego ryzyka?**

7. **Czy najbardziej opłacalny moat w ERP-agentic space będzie leżał w danych, evalach, integracji, czy w relacjach wdrożeniowych?**  
   Najpewniej w kombinacji, ale proporcje pozostają otwarte.

8. **Czy open-weight reasoning models utrzymają tempo doganiania closed frontier, czy natrafią na twarde ograniczenia compute/data/safety?**

---

## 7) Konkluzja końcowa

Jeżeli miałbym zredukować całe badanie do jednego zdania, brzmiałoby ono tak:

> **Nie trzeba wierzyć w pewne AGI za 2 lata, żeby uznać, że inwestycja w infrastrukturę agentową jest dziś racjonalna — pod warunkiem, że buduje się warstwę trwałą: integrację, orkiestrację, evale, governance i odporność na zmianę modelu oraz szoki geopolityczne.**

To jest teza, która pozostaje sensowna w niemal wszystkich badanych scenariuszach.
