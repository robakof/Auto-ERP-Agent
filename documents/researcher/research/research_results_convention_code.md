# Research: Konwencje kodowania Python w projektach multi-tool CLI

Data: 2026-03-25

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana bezpośrednio

## TL;DR — 5 najważniejszych wniosków

1. **Dojrzałe CLI standaryzują przede wszystkim kontrakt interfejsu, nie „ładny output”.** Najczęstszy wzorzec to: wynik na `stdout`, błędy/prompt/logi na `stderr`, udokumentowane `exit codes`, jawny tryb machine-readable (`--json`, `--format=json`, itp.) oraz flaga wyłączająca interakcję (`--quiet`, `--ignore-stdin`, `--no-cli-pager`). — siła dowodów: **praktyczne**
2. **Spójność wielu narzędzi w jednym repo zwykle nie powstaje z samego style guide’a, tylko ze wspólnego scaffoldu.** Dojrzałe projekty centralizują helpery do parsowania flag, JSON-owego outputu, IO, błędów, helpa i testów kontraktowych. — siła dowodów: **praktyczne**
3. **Przy kodzie generowanym przez LLM największą wartość mają reguły redukujące niejednoznaczność i zwiększające weryfikowalność:** obowiązkowe type hints na granicach CLI, jawne importy, stała struktura modułu, jedna konfiguracja lint/type-check, testy kontraktu `stdout/stderr/exit code`. — siła dowodów: **praktyczne + empiryczne**
4. **Literatura o jakości kodu LLM nie daje jednej prostej tezy.** Są badania pokazujące mniej bugów niż w kodzie pisanym przez ludzi w części zadań, ale też prace pokazujące więcej code smells i problemy strukturalne przy wyższej złożoności. To wzmacnia argument za konwencją opartą na automatycznej weryfikacji, nie na samych promptach. — siła dowodów: **empiryczne**
5. **Pareto dla „minimum viable convention” to nie 50 zasad, tylko 5–7 twardych reguł:** jeden kontrakt `stdout/stderr`, jeden schemat JSON success/error, jeden enum exit codes, obowiązkowe typowanie granic, jeden szablon pliku narzędzia, jeden zestaw bramek (`ruff` + `mypy` + testy kontraktowe). — siła dowodów: **spekulacja** oparta na źródłach praktycznych i empirycznych

## Wyniki per pytanie

### 1) Python CLI conventions w projektach multi-tool

#### Wniosek 1.1 — `stdout` i `stderr` są traktowane jako osobne kanały kontraktu
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `gcloud` zaleca wypisywać właściwy wynik na `stdout`, a prompty, ostrzeżenia i błędy na `stderr`; dodatkowo ostrzega, żeby skrypty nie polegały na `stderr` jako źródle danych.
- `AWS CLI` dokumentuje strukturyzowany output błędów na `stderr` i osobno opisuje formaty danych wyjściowych.
- `gh` oddziela zwykły output komend od kodów wyjścia i ma osobną dokumentację formatowania (`--json`, `--jq`, `--template`).
- `HTTPie` w praktykach skryptowych podkreśla użycie flag ograniczających interaktywność i wymuszających przewidywalne zachowanie.

**Synteza:**
Dla repo z wieloma narzędziami generującymi JSON oznacza to bardzo mocną regułę: **na `stdout` powinien trafiać wyłącznie wynik machine-readable**, a wszystko, co jest komunikatem dla człowieka lub błędem operacyjnym, powinno trafiać na `stderr`.

**Trade-off / alternatywy:**
- Zysk: łatwiejsze potokowanie, prostsze testy kontraktowe, mniejsze ryzyko „zanieczyszczenia” JSON-a.
- Koszt: mniej wygodne „print-debugging” i większa dyscyplina przy logowaniu.

#### Wniosek 1.2 — Dojrzałe CLI mają jawny tryb machine-readable i jawny tryb nieinteraktywny
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `AWS CLI` wspiera wiele formatów outputu (`json`, `yaml`, `table`, `text`) i ma globalne opcje typu `--no-cli-pager` oraz konfigurowalny format błędów.
- `gcloud` ma `--format`, `--quiet`, kontrolę verbosity oraz możliwość wyłączenia outputu użytkowego.
- `gh` dla części komend oferuje `--json`, a potem dalsze formatowanie przez `--jq` lub Go templates.
- `HTTPie` zaleca `--ignore-stdin` w nieinteraktywnych skryptach; `--check-status` zamienia status HTTP na przewidywalne kody wyjścia.

**Synteza:**
Wzorzec jest spójny: **CLI mają wspierać dwa tryby pracy** — dla człowieka i dla automatyzacji — zamiast mieszać oba naraz.

**Trade-off / alternatywy:**
- Jeden stały JSON-only output upraszcza cały ekosystem.
- Dwutrybowość (`human` vs `machine`) bywa wygodniejsza dla użytkowników, ale zwiększa powierzchnię testowania.

#### Wniosek 1.3 — Exit codes są częścią publicznego interfejsu
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `AWS CLI` publikuje szczegółowe kody wyjścia (m.in. 0, 1, 2, 130, 252–255) i ich znaczenie.
- `gh` publikuje podstawowe kody (`0`, `1`, `2`, `4`) oraz w części komend dodatkowe kody specyficzne dla domeny.
- `HTTPie` dokumentuje kody wyjścia dla timeoutów, redirectów i klas statusów HTTP przy `--check-status`.
- `gcloud` zaleca opierać automatyzację na `exit status` zamiast parsowania komunikatów tekstowych.

**Synteza:**
Dla multi-tool repo najmocniejsza konwencja to: **z góry ustalić mały wspólny enum kodów wyjścia dla wszystkich narzędzi**, a wyjątki dopuszczać tylko wtedy, gdy są jawnie udokumentowane i testowane.

**Trade-off / alternatywy:**
- Wspólny mały enum zwiększa przewidywalność.
- Bogatsze, domenowe kody dają więcej informacji, ale są trudniejsze do zapamiętania i egzekwowania między narzędziami.

#### Wniosek 1.4 — Argument parsing jest zwykle ustandaryzowany bardziej niż sam kod biznesowy
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `argparse` ma mocne domyślne zachowania (`--help`, walidacja argumentów, standardowy `exit status 2` przy błędach składni).
- `gh` dokumentuje precyzyjne konwencje składni CLI: placeholdery, argumenty opcjonalne, wzajemnie wykluczające się warianty, argumenty powtarzalne.
- `CLIG` rekomenduje korzystanie z bibliotek do parsowania i odradza niejawne/niestabilne skróty komend.

**Synteza:**
W Pythonowym multi-tool repo warto standaryzować nie tylko nazwy flag, ale też **sam schemat parsera**: kolejność sekcji helpa, nazewnictwo flag, obsługę błędu parsera i sposób mapowania na JSON error.

**Trade-off / alternatywy:**
- Domyślny `argparse` jest tani i stabilny.
- Jeśli każde narzędzie ma zwracać JSON także przy błędzie argumentów, trzeba świadomie odejść od części domyślnych zachowań parsera i przejąć kontrolę nad błędem.

---

### 2) Coding conventions dla AI-generated code

#### Wniosek 2.1 — Najbardziej opłacalne są reguły, które zamieniają „styl” na coś sprawdzalnego automatycznie
**Siła dowodów:** empiryczne + praktyczne

**Wprost ze źródeł:**
- PEP 484 i dokumentacja `typing` traktują adnotacje typów jako kontrakt interfejsu przydatny dla analizy statycznej i refaktoryzacji.
- `mypy` oferuje twarde flagi typu `--disallow-untyped-defs`; tryb `--strict` scala zestaw bardziej rygorystycznych kontroli.
- W badaniu *Static Analysis as a Feedback Loop* iteracyjne sprzężenie LLM + analiza statyczna istotnie obniżało problemy bezpieczeństwa, czytelności i niezawodności.
- W badaniu *Automated Type Annotation in Python Using Large Language Models* pipeline generate-check-repair z `mypy` znacząco zwiększał spójność wygenerowanych adnotacji typów.

**Synteza:**
Dla kodu generowanego przez LLM nie wystarczy „pisz czytelnie”. Najbardziej wartościowe są reguły typu: **wszystkie funkcje CLI-facing muszą mieć type hints**, **schemat danych wyjściowych musi być typowany**, **kod ma przejść ten sam lint i type-check w całym repo**.

**Trade-off / alternatywy:**
- Zysk: mniejsza entropia między narzędziami, łatwiejsza naprawa przez kolejne agenty, wyraźniejsze granice interfejsu.
- Koszt: więcej adnotacji i konieczność utrzymywania konfiguracji `mypy`.

#### Wniosek 2.2 — Jawność wygrywa z „sprytem”: explicit imports, jawne nazwy, przewidywalny układ pliku
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- PEP 8 preferuje jawne importy, grupowanie importów, moduły i funkcje o przewidywalnych nazwach (`lowercase_with_underscores`) oraz przestrzega przed wildcard imports.
- PEP 257 zaleca docstringi opisujące zachowanie, argumenty, efekty uboczne i wyjątki.
- `ruff` ma reguły egzekwujące m.in. porządek importów i typowe błędy spójności bez rozbudowanej konfiguracji.

**Synteza:**
W kontekście LLM kluczowa jest nie „elegancja”, tylko **obniżanie liczby dopuszczalnych wariantów**. Reguły typu „zero wildcard imports”, „jeden standard nazewnictwa”, „stały układ sekcji pliku” są tanie, a mocno redukują dryf stylu między narzędziami.

**Trade-off / alternatywy:**
- Bardziej restrykcyjny szablon przyspiesza generację kolejnych narzędzi i review.
- Cena to mniejsza swoboda projektowa dla autorów ludzkich.

#### Wniosek 2.3 — Sam LLM nie daje stabilnej jakości; potrzebne są bramki QA
**Siła dowodów:** empiryczne

**Wprost ze źródeł:**
- *Is LLM-Generated Code More Maintainable & Reliable than Human-Written Code?* pokazuje mniej bugów i mniejszy effort napraw w części zadań, ale przy trudniejszych problemach pojawiają się problemy strukturalne nieobecne w rozwiązaniach ludzkich.
- *Investigating The Smells of LLM Generated Code* raportuje wyższą częstość code smells w kodzie generowanym przez LLM niż w kodzie referencyjnym.
- *Quality Assurance of LLM-generated Code* opisuje rozjazd między tym, co mierzy academia, a tym, co ceni praktyka: przemysł mocno akcentuje maintainability i readability oraz ryzyko technical debt.

**Synteza:**
Najbezpieczniejsza konwencja dla AI-generated code to taka, która **zakłada zmienną jakość pierwszego draftu** i wymusza sprawdzalność przez narzędzia. Innymi słowy: mniej „prosimy model, żeby pisał ładnie”, bardziej „kod musi przejść te same automatyczne bramki”.

**Konflikt źródeł:**
- Jedne badania sugerują mniej bugów niż w kodzie ludzkim w części zadań.
- Inne pokazują więcej code smells lub gorszą strukturę.
- Najbardziej prawdopodobne wyjaśnienie: badania mierzą różne rzeczy (bugi vs smells vs maintainability), na różnych zbiorach i poziomach trudności.

#### Wniosek 2.4 — Typowanie granic danych wyjściowych jest szczególnie ważne przy JSON CLI
**Siła dowodów:** praktyczne + spekulacja

**Wprost ze źródeł:**
- `TypedDict` w `typing` służy do modelowania słowników o stałym zestawie kluczy i typów wartości.
- Moduł `json` zachowuje porządek wejściowy; `sort_keys=True` może dodatkowo ustabilizować serializację pod testy.

**Synteza:**
Dla repo narzędzi zwracających JSON wysoki zwrot daje reguła: **output schema ma być jawnie opisana typem** (`TypedDict`, ewentualnie `dataclass`/model), a serializacja ma być deterministyczna na tyle, na ile to potrzebne testom i agentom modyfikującym kod.

**Uwaga:**
Nie udało się znaleźć bezpośredniego badania porównującego różne style modelowania JSON output specifically w repo multi-tool CLI; to wniosek inferencyjny.

---

### 3) Projekty multi-tool w jednym repo

#### Wniosek 3.1 — Spójność interfejsu jest zwykle scentralizowana w helperach, nie w kopiowaniu kodu
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `gh` w `AGENTS.md` opisuje wspólne helpery dla IO (`iostreams`), formatowania tabel, obsługi JSON flags, error helpers oraz wspólnego wzorca budowy komend.
- `gh` w `project-layout.md` pokazuje, że flag parsing, stdout/stderr i logika wyjścia są utrzymywane według wspólnego modelu, a pomoc i examples są osadzane przy komendzie.
- `AWS CLI` i `HTTPie` w guide’ach contributors naciskają na wspólne testy, lint i spójność kontrybucji w całym repo.

**Synteza:**
Najsilniejsza praktyka w repo multi-tool to **jedna warstwa współdzielona dla „boring parts”**: parser bootstrap, JSON emit, error mapowanie, help text, test harness.

**Trade-off / alternatywy:**
- Centralizacja zwiększa spójność i obniża koszt dodawania nowych narzędzi.
- Zbyt gruby shared layer może utrudnić nietypowe przypadki i prowadzić do „frameworka we frameworku”.

#### Wniosek 3.2 — Poszczególne narzędzia/komendy są cienkie, a ciężar spójności spoczywa na strukturze repo
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `gh` zaleca wzorzec: pakiet/plik komendy, obiekt opcji, fabryka komendy, lazy init w `RunE`, wspólne rejestrowanie w drzewie komend.
- Dokumentacja projektu `gh` trzyma help i examples blisko źródła komendy, a testy bazują na stubach i testach tabelarycznych.

**Synteza:**
W repo z wieloma Python CLI-tools najbardziej naturalny odpowiednik tego wzorca to: **cienki entrypoint per tool + współdzielony runtime/helper layer**, zamiast kopiowania pełnej obsługi CLI do każdego skryptu.

**Luka:**
Bezpośrednich, dobrze udokumentowanych przykładów repo z „50+ osobnych pythonowych skryptów CLI” jest mniej niż przykładów jednego CLI z wieloma subcommands. Dowód jest więc częściowo pośredni.

#### Wniosek 3.3 — Dokumentacja interfejsu bywa generowana z kodu źródłowego lub utrzymywana obok niego
**Siła dowodów:** praktyczne

**Wprost ze źródeł:**
- `gh` utrzymuje help/examples przy komendach i generuje z nich manuale.
- Dojrzałe CLI dokumentują publicznie globalne flagi, formaty outputu i exit codes jako część API dla użytkowników i automatyzacji.

**Synteza:**
To wzmacnia konwencję: **opis CLI nie powinien żyć w osobnym, łatwo rozjeżdżającym się dokumencie**, tylko możliwie blisko parsera/definicji komendy.

#### Wniosek 3.4 — Testy kontraktowe są ważniejsze niż stylistyczne dyskusje
**Siła dowodów:** praktyczne + empiryczne

**Wprost ze źródeł:**
- `AWS CLI` i `HTTPie` wymagają testów dla zmian/fixów.
- Badania o jakości kodu LLM pokazują, że sama poprawność funkcjonalna nie wystarcza; potrzebne są dodatkowe miary jakości i automatyczne sprzężenie zwrotne.

**Synteza:**
W repo multi-tool większą wartość niż rozbudowany style guide dają proste testy kontraktowe powtarzane dla każdego narzędzia: `--help`, success JSON, błąd parsera, błąd runtime, exit code.

---

### 4) Minimum viable code convention (Pareto)

Poniższa sekcja jest **syntezą**, nie bezpośrednim wynikiem pojedynczego badania. Nie udało się znaleźć pracy, która eksperymentalnie porównuje dokładnie taki zestaw reguł w repo Python multi-tool CLI. To propozycja „20% zasad dających 80% spójności”, oparta na powyższych źródłach.

#### Reguła A — Jeden kontrakt kanałów IO
**Treść:** `stdout` wyłącznie dla wyniku (JSON lub output przewidziany do pipe’owania), `stderr` dla błędów, ostrzeżeń, promptów i logów.  
**Wpływ:** bardzo wysoki  
**Koszt egzekwowania:** niski  
**Siła dowodów:** praktyczne

#### Reguła B — Jeden schemat JSON success/error dla wszystkich narzędzi
**Treść:** każde narzędzie emituje przewidywalną strukturę danych przy sukcesie i przewidywalną strukturę błędu przy porażce.  
**Wpływ:** bardzo wysoki  
**Koszt egzekwowania:** niski–średni  
**Siła dowodów:** spekulacja oparta na praktykach dojrzałych CLI i narzędziach typowania

#### Reguła C — Jeden mały wspólny enum exit codes
**Treść:** np. sukces, błąd użycia/argumentów, błąd runtime, przerwanie przez użytkownika, błąd autoryzacji/konfiguracji; odstępstwa tylko jawnie udokumentowane.  
**Wpływ:** bardzo wysoki  
**Koszt egzekwowania:** niski  
**Siła dowodów:** praktyczne

#### Reguła D — Obowiązkowe type hints na granicach CLI
**Treść:** typowane `main(...)`, typowane funkcje parsujące i typowany schema outputu (`TypedDict` lub równoważny model).  
**Wpływ:** wysoki  
**Koszt egzekwowania:** średni  
**Siła dowodów:** praktyczne + empiryczne

#### Reguła E — Jeden szablon pliku narzędzia
**Treść:** stały układ sekcji, np. `parse_args` → `run` → `emit_result` → `main`; jawne importy; jedno miejsce mapowania wyjątków na JSON + exit code.  
**Wpływ:** wysoki  
**Koszt egzekwowania:** niski  
**Siła dowodów:** spekulacja oparta na praktykach repo multi-tool

#### Reguła F — Jedna centralna konfiguracja `ruff` + `mypy`
**Treść:** repo-wide config w `pyproject.toml`/`ruff.toml`, jedna polityka lintowania i type-checkingu dla wszystkich tooli.  
**Wpływ:** wysoki  
**Koszt egzekwowania:** niski–średni  
**Siła dowodów:** praktyczne + empiryczne

#### Reguła G — Cztery obowiązkowe testy kontraktowe per narzędzie
**Treść:** test `--help`, test sukcesu, test błędu argumentów, test błędu runtime/obsługi wyjątku.  
**Wpływ:** wysoki  
**Koszt egzekwowania:** średni  
**Siła dowodów:** praktyczne + empiryczne

#### Dlaczego właśnie te reguły?
**Synteza:**
- Są blisko publicznego interfejsu narzędzia, więc redukują największą część chaosu między toolami.
- Są relatywnie tanie do automatycznego sprawdzenia.
- Dają zarówno korzyść ludziom, jak i agentom/LLM, które będą później dopisywać kolejne narzędzia.

#### Czego celowo tu nie ma?
**Synteza:**
- Drobnych preferencji formatowania, które formatter i tak rozwiąże automatycznie.
- Szerokich zasad architektonicznych zależnych od konkretnego projektu.
- Subiektywnych reguł „ładnego kodu”, których nie da się łatwo sprawdzić.

## Otwarte pytania / luki w wiedzy

- **Brak bezpośredniego benchmarku dla wzorca „50+ osobnych Python CLI skryptów w jednym repo”.** Najlepsze przykłady publiczne to zwykle jeden CLI z wieloma subcommands, więc część wniosków jest analogią strukturalną, nie 1:1.
- **Nie udało się potwierdzić jednym mocnym badaniem, które konkretne reguły stylu dają największy wzrost spójności w AI-generated code.** Dane wspierają typowanie, statyczną analizę i QA, ale nie wyznaczają jednego kanonicznego zestawu.
- **Źródła empiryczne o jakości kodu LLM są częściowo sprzeczne.** Jedne mierzą bugs/reliability, inne smells/maintainability; wyniki zależą od trudności zadań, języka, benchmarku i metryki.
- **Nie znaleziono mocnego źródła pierwotnego mówiącego wprost, że `allow_abbrev=False` powinno być standardem dla Python CLI.** To wniosek inferencyjny z praktyk stabilnych interfejsów i rekomendacji przeciw arbitralnym skrótom.
- **JSON error schema** jako wspólny kontrakt między wieloma narzędziami jest bardzo logiczny, ale źródła częściej dokumentują tę praktykę pośrednio (oddzielenie kanałów, exit codes, machine-readable modes) niż jako jednolity standard branżowy.

## Źródła / odniesienia

- [gcloud CLI overview](https://cloud.google.com/sdk/gcloud) — oficjalny opis globalnych zachowań CLI; użyte dla `stdout/stderr`, `--format`, `--quiet`, verbosity i modelu automatyzacji.
- [Scripting gcloud CLI commands](https://cloud.google.com/sdk/docs/scripting-gcloud) — oficjalne zalecenia do skryptów; użyte dla roli `exit status` i ostrzeżenia przed parsowaniem `stderr`.
- [GitHub CLI: exit codes](https://cli.github.com/manual/gh_help_exit-codes) — oficjalna dokumentacja kodów wyjścia `gh`.
- [GitHub CLI: formatting output](https://cli.github.com/manual/gh_help_formatting) — oficjalna dokumentacja `--json`, `--jq`, `--template`.
- [GitHub CLI: command-line syntax](https://cli.github.com/manual/gh_help_reference) — oficjalne konwencje składni komend, placeholderów i argumentów.
- [GitHub CLI AGENTS.md](https://github.com/cli/cli/blob/trunk/AGENTS.md) — opis wewnętrznych wzorców implementacyjnych repo; użyte dla shared helpers, error helpers, JSON flags, IO abstractions i testów.
- [GitHub CLI project-layout.md](https://github.com/cli/cli/blob/trunk/docs/project-layout.md) — jak repo utrzymuje spójność komend, helpa i testów.
- [AWS CLI return codes](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-returncodes.html) — oficjalna tabela kodów wyjścia; użyte dla wniosku o exit codes jako części interfejsu.
- [AWS CLI output format](https://docs.aws.amazon.com/cli/v1/userguide/cli-usage-output-format.html) — oficjalny opis trybów outputu; użyte dla wzorca jawnego machine-readable mode.
- [AWS CLI environment variables / global behavior](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) — użyte dla `AWS_PAGER`, `--no-cli-pager` i globalnych zachowań automatyzacyjnych.
- [AWS CLI global options reference](https://docs.aws.amazon.com/cli/latest/reference/) — użyte do potwierdzenia aktualnych globalnych flag (`--debug`, `--no-paginate`, `--cli-error-format`, itd.).
- [HTTPie CLI docs](https://httpie.io/docs/cli) — oficjalna dokumentacja; użyta dla `--check-status`, `--ignore-stdin` i praktyk skryptowych.
- [CLIG.dev](https://clig.dev/) — wtórny, ale wpływowy przewodnik po projektowaniu CLI; użyty pomocniczo dla zaleceń o parserach, `stdout/stderr` i stabilności interfejsu.
- [argparse — Python docs](https://docs.python.org/3/library/argparse.html) — źródło dla domyślnych zachowań parsera, `--help`, błędów argumentów i opcji parsera.
- [json — Python docs](https://docs.python.org/3/library/json.html) — źródło dla deterministycznej serializacji, porządku i opcji `sort_keys`.
- [PEP 8](https://peps.python.org/pep-0008/) — źródło dla jawnych importów, nazewnictwa i zasady spójności w obrębie projektu.
- [PEP 257](https://peps.python.org/pep-0257/) — źródło dla docstringów opisujących zachowanie, argumenty i wyjątki.
- [PEP 484](https://peps.python.org/pep-0484/) — podstawowe źródło dla type hints jako kontraktu i wsparcia statycznej analizy.
- [typing — Python docs](https://docs.python.org/3/library/typing.html) — użyte dla roli typowania w dokumentowaniu interfejsów i narzędziowej weryfikacji.
- [mypy command line docs](https://mypy.readthedocs.io/en/stable/command_line.html) — użyte dla `--strict`, `--disallow-untyped-defs` i podejścia do enforcementu.
- [Ruff rules](https://docs.astral.sh/ruff/rules/) — użyte dla taniego egzekwowania spójności i wykrywania typowych błędów.
- [Ruff settings](https://docs.astral.sh/ruff/settings/) — użyte dla centralnej konfiguracji repo-wide.
- [Static Analysis as a Feedback Loop: Enhancing LLM-Generated Code Beyond Correctness](https://arxiv.org/abs/2508.14419) — badanie empiryczne o iteracyjnym feedbacku z Bandit/Pylint; użyte dla tezy, że analiza statyczna znacząco poprawia jakość kodu LLM.
- [Automated Type Annotation in Python Using Large Language Models](https://arxiv.org/abs/2508.00422) — badanie empiryczne o generate-check-repair z `mypy`; użyte dla argumentu o typowaniu i weryfikacji.
- [Is LLM-Generated Code More Maintainable & Reliable than Human-Written Code?](https://arxiv.org/abs/2508.00700) — badanie porównawcze; użyte do pokazania, że wyniki jakościowe są mieszane i zależne od trudności zadania.
- [Investigating The Smells of LLM Generated Code](https://arxiv.org/abs/2510.03029) — badanie o code smells; użyte dla kontr-tezy wobec narracji „LLM po prostu pisze lepszy kod”.
- [Quality Assurance of LLM-generated Code: Addressing Non-Functional Quality Characteristics](https://arxiv.org/abs/2511.10271) — użyte dla rozróżnienia między priorytetami praktyki i akademii oraz dla nacisku na maintainability/readability.
