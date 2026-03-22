# Research: Wpływ języka na działanie modeli LLM

Data: 2026-03-22

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, case study, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5-7 najważniejszych wniosków

1. **Dla języków wysokozasobowych różnica jakości między angielskim a polskim bywa mała, ale nie jest gwarantowanie zerowa.** W oficjalnym raporcie GPT-4 wynik na przetłumaczonym MMLU wynosi **85.5% po angielsku vs 82.7% po polsku** (-2.8 pp). Jednocześnie w polskich egzaminach medycznych GPT-4 osiągnął **79.7% zarówno po polsku, jak i po angielsku**, a nowsze badanie na egzaminach medyczno-dentystycznych nie wykazało istotnych statystycznie różnic EN vs PL dla ChatGPT-4 i Claude. **Siła dowodów: empiryczne.**
2. **Największe spadki jakości w wielojęzyczności dotyczą raczej języków niższego zasobu niż samego „nie-angielskiego” jako takiego.** Publiczne ewaluacje Anthropic pokazują, że dla języków wysokozasobowych Claude jest zwykle bardzo blisko angielskiego, ale dla części języków niskozasobowych luki są dużo większe. **Siła dowodów: praktyczne + empiryczne.**
3. **Tokenizacja tworzy realny „podatek językowy” na koszcie, latencji i długości kontekstu.** OpenAI wprost podaje, że tekst nieangielski często ma wyższy stosunek tokenów do znaków, a prace o unfair tokenization pokazują, że to przekłada się na większy koszt i mniej miejsca w context window dla tej samej informacji. **Siła dowodów: praktyczne + empiryczne.**
4. **Nie da się uczciwie powiedzieć „chiński/japoński są zawsze tańsze” ani „zawsze droższe”.** To zależy od konkretnego tokenizera i modelu. Starsze/tokenizery anglocentryczne często nadmiernie fragmentują CJK; nowszy tokenizer OpenAI dla GPT-4o znacząco poprawił efektywność wielu języków, w tym chińskiego, japońskiego i koreańskiego, ale istnieją też prace pokazujące błędy rozumienia długich chińskich tokenów w GPT-4o. **Siła dowodów: praktyczne + empiryczne.**
5. **Nie ma jednej uniwersalnej reguły dla języka promptu.** Nowsze badania pokazują, że przewaga angielskich instrukcji po usunięciu efektu „translationese” nie jest przytłaczająca; zależy od zadania. W części zadań lepiej działa język docelowy, w części angielski, a w wielu scenariuszach najlepiej wypada „selective pre-translation” (np. instrukcja po angielsku, kontekst w języku źródłowym, wynik w języku żądanym). **Siła dowodów: empiryczne.**
6. **Praktyczny wzorzec produkcyjny to rozdzielenie warstw językowych.** Interfejs użytkownika i finalna odpowiedź zwykle pozostają w języku użytkownika, ale elementy techniczne (JSON, schematy narzędzi, nazwy pól, kod, część instrukcji systemowych) często pozostają po angielsku albo w języku kontrolnym. To jest dobrze wspierane przez dokumentację vendorów, ale rzadziej opisane w publicznych benchmarkach 1:1. **Siła dowodów: praktyczne + spekulacja.**
7. **Benchmarki wielojęzyczne trzeba czytać ostrożnie.** Wiele z nich to tłumaczenia angielskiego MMLU, co może zawyżać lub zniekształcać ocenę „prawdziwej” kompetencji w danym języku. Global-MMLU pokazuje, że część pytań jest kulturowo osadzona i ranking modeli może się zmieniać po odejściu od prostego tłumaczenia z angielskiego. **Siła dowodów: empiryczne.**

## Wyniki per obszar badawczy

### 1. Jakość odpowiedzi: polski vs angielski

#### Co da się potwierdzić ilościowo

- **GPT-4 wypada trochę lepiej po angielsku niż po polsku na przetłumaczonym MMLU, ale różnica nie jest ogromna.** W raporcie technicznym GPT-4 opublikowano wyniki MMLU przetłumaczonego na 26 języków. Wynik dla angielskiego to 85.5%, a dla polskiego 82.7%.
  - Źródło: [GPT-4 Technical Report](https://arxiv.org/pdf/2303.08774.pdf) — oficjalny raport OpenAI z tabelą wyników multilingual MMLU.
  - Ocena: **empiryczne**, ale z ważnym caveatem: to benchmark tłumaczony z angielskiego.

- **OpenAI sam opisuje swoje modele jako „optimized for English”, choć zdolne do pracy wielojęzycznej.** To nie jest benchmark, ale istotna deklaracja projektowa dostawcy.
  - Źródło: [How can I use the OpenAI API with text in different languages?](https://help.openai.com/en/articles/6742369-how-can-i-use-the-openai-api-with-text-in-different-languages) — oficjalna notatka OpenAI.
  - Ocena: **praktyczne**.

- **Dane stricte dla polskiego nie pokazują prostego obrazu „polski zawsze gorszy”.**
  - W badaniu na Polskim Lekarskim Egzaminie Końcowym GPT-4 uzyskał **79.7% zarówno po polsku, jak i po angielsku**, podczas gdy GPT-3.5 miał **54.8% po polsku vs 60.3% po angielsku**.
  - Źródło: [Evaluation of the performance of GPT-3.5 and GPT-4 on the Polish Medical Final Examination](https://pubmed.ncbi.nlm.nih.gov/37993519/) — recenzowane badanie na polskim egzaminie medycznym.
  - Ocena: **empiryczne**.

- **W nowszym badaniu porównującym ChatGPT-4, Gemini i Claude na polskich egzaminach medycznych/dentystycznych nie stwierdzono istotnych statystycznie różnic EN vs PL dla ChatGPT-4 i Claude; Gemini był istotnie lepszy po angielsku.**
  - Źródło: [Comparing the performance of ChatGPT, Gemini, and Claude in English and Polish on medical examinations](https://www.nature.com/articles/s41598-025-17030-0) — recenzowane badanie porównawcze.
  - Ocena: **empiryczne**.

#### Gdzie różnica bywa największa

- **Dla języków wysokozasobowych spadki są zwykle małe; dla niskozasobowych rosną wyraźnie.** Anthropic publikuje dwa ważne zbiory danych:
  - w publicznej dokumentacji: wiele dużych języków (np. chiński, japoński, koreański) osiąga ok. **96–98% wyniku angielskiego**;
  - w system card Sonnet 4.6: średnia dla języków wysokozasobowych jest **-1.9 pp względem angielskiego**, dla średniozasobowych **-2.7 pp**, a dla niskozasobowych **-9.1 pp**.
  - Polski jest zaliczony do bucketu high-resource, ale Anthropic **nie publikuje publicznie osobnego wyniku dla polskiego** w tej tabeli.
  - Źródła:
    - [Anthropic Multilingual support docs](https://docs.anthropic.com/en/docs/build-with-claude/multilingual-support)
    - [Claude Sonnet 4.6 System Card](https://www-cdn.anthropic.com/6a5fa276ac68b9aeb0c8b6af5fa36326e0e166dd.pdf)
  - Ocena: **praktyczne** (dokumentacja/system card) z elementem **empirycznym** (publikowane wyniki benchmarków).

- **Rodzaj zadania ma znaczenie.** Badanie „A Fair Comparison without Translationese” pokazuje, że po usunięciu uprzedzeń wynikających z tłumaczenia:
  - instrukcje w języku docelowym lepiej działały w **lexical simplification**,
  - instrukcje po angielsku bywały lepsze w **reading comprehension**,
  - w klasyfikacji pomaga zgranie języka instrukcji z językiem etykiet.
  - Źródło: [A Fair Comparison without Translationese: English vs. Target-language Instructions for Multilingual LLMs](https://aclanthology.org/2025.naacl-short.55.pdf)
  - Ocena: **empiryczne**.

#### Czy prompt po polsku, a output po angielsku ma sens?

- **Tak, ale nie jako reguła uniwersalna.** Najmocniejszy sygnał z literatury jest taki, że opłaca się traktować język osobno dla: instrukcji, kontekstu, przykładów i oczekiwanego outputu.
- Badanie o selective pre-translation na 35 językach pokazuje, że **częściowe tłumaczenie promptu** regularnie wygrywa z dwoma skrajnościami: pełnym tłumaczeniem wszystkiego do angielskiego oraz pozostawieniem wszystkiego w języku źródłowym.
- W zadaniach ekstrakcyjnych (QA, NER) kontekst w języku źródłowym często pozostaje korzystny, szczególnie dla języków niższego zasobu.
  - Źródło: [The Impact of Prompt Translation Strategies in Cross-lingual Prompting for Low-Resource Languages](https://aclanthology.org/2025.loresmt-1.9.pdf)
  - Ocena: **empiryczne**.

#### Konflikty i interpretacja

- **Konflikt 1:** „angielski jest lepszy” vs „dla polskiego różnicy nie ma”.
  - Wyjaśnienie: te tezy nie muszą się wykluczać. Angielski często ma lekką przewagę na benchmarkach ogólnych i tłumaczonych, ale w konkretnych, wysokozasobowych i dobrze reprezentowanych domenach różnica może zniknąć.
- **Konflikt 2:** benchmark translacyjny vs benchmark natywny.
  - Global-MMLU pokazuje, że benchmarki zbudowane przez tłumaczenie angielskiego MMLU wprowadzają bias kulturowy i „translationese”, więc nie należy traktować ich jako ostatecznej miary jakości w danym języku.
  - Źródło: [Global MMLU: Understanding and Addressing Cultural and Linguistic Biases in Multilingual Evaluation](https://arxiv.org/pdf/2502.13509)
  - Ocena: **empiryczne**.

### 2. Tokenizacja i koszt

#### Co jest pewne

- **Dostawcy rozliczają użycie według tokenów, a nie według „ilości informacji”.** To oznacza, że różnice tokenizacji wprost przekładają się na koszt i dostępny kontekst.
  - Źródła:
    - [OpenAI API Pricing](https://openai.com/api/pricing/)
    - [Anthropic Token counting](https://docs.anthropic.com/en/docs/build-with-claude/token-counting)
  - Ocena: **praktyczne**.

- **OpenAI wprost zaznacza, że tekst nieangielski często ma wyższy stosunek tokenów do znaków niż angielski.**
  - Źródło: [What are tokens and how do I count them?](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-do-i-count-them)
  - Ocena: **praktyczne**.

- **Akademicka literatura potwierdza, że różne języki płacą różny „token tax”.**
  - Praca o tokenization unfairness pokazuje, że w tokenizerach z rodziny GPT niektóre języki potrzebują znacznie więcej tokenów niż angielski dla porównywalnej treści.
  - Praca „Do All Languages Cost the Same?” pokazuje, że wysoka fragmentacja zwiększa koszt, zmniejsza utility modelu i pogarsza few-shot prompting, bo do promptu mieści się mniej przykładów.
  - Źródła:
    - [Language Model Tokenizers Introduce Unfairness Between Languages](https://proceedings.neurips.cc/paper_files/paper/2023/file/21ed38c2b7e44b7c64d5d380bdf3f16b-Paper-Conference.pdf)
    - [Do All Languages Cost the Same? Tokenization in the Era of Commercial Language Models](https://aclanthology.org/2023.emnlp-main.785.pdf)
  - Ocena: **empiryczne**.

#### Co to znaczy dla polskiego

- **Nie udało się znaleźć publicznej, oficjalnej tabeli OpenAI/Anthropic typu „EN vs PL token count for identical text” dla aktualnych tokenizerów.** To jest luka.
- Dostępne przesłanki sugerują jednak, że:
  - polski jako język fleksyjny może tokenizować się gorzej niż angielski w części tokenizerów,
  - ale nie musi mieć tak dużego „podatku” jak część języków z innych skryptów lub bardzo słabą reprezentacją w danych treningowych,
  - publiczne prace pokazują, że języki używające skryptu łacińskiego i dzielące sporo subwordów z angielskim zwykle wypadają lepiej niż wiele języków pozałacińskich.
  - Źródła:
    - [Language Model Tokenizers Introduce Unfairness Between Languages](https://proceedings.neurips.cc/paper_files/paper/2023/file/21ed38c2b7e44b7c64d5d380bdf3f16b-Paper-Conference.pdf)
    - [Tokenization efficiency of current foundational large language models for the Ukrainian language](https://pmc.ncbi.nlm.nih.gov/articles/PMC12380774/)
  - Ocena: **empiryczne**, ale pośrednie dla polskiego.

#### Języki azjatyckie: czy są bardziej efektywne kosztowo?

- **Brak jednej odpowiedzi.** Są tu dwa przeciwne mechanizmy:
  1. **gęstość informacji** — pojedynczy znak/ciąg może nieść dużo treści;
  2. **fragmentacja tokenizera** — tokenizer może rozbijać tekst bardzo nieefektywnie.

- **Starsze lub anglocentryczne tokenizery często karały wiele języków pozaangielskich, w tym część CJK.** Literatura pokazuje, że CJK nie są automatycznie „tańsze”, bo skuteczność zależy od tego, jak tokenizer został wyuczony i jaki ma słownik.
  - Źródła:
    - [Language Model Tokenizers Introduce Unfairness Between Languages](https://proceedings.neurips.cc/paper_files/paper/2023/file/21ed38c2b7e44b7c64d5d380bdf3f16b-Paper-Conference.pdf)
    - [Excessively Dividing Texts Can Break Down Tokenizers in Large Language Models](https://aclanthology.org/2024.acl-long.328.pdf)
  - Ocena: **empiryczne**.

- **OpenAI poprawił tokenizację wielu języków w GPT-4o.** Oficjalna publikacja pokazuje spadek liczby tokenów względem poprzedniego tokenizera m.in. dla:
  - chińskiego: **1.4× mniej tokenów**,
  - japońskiego: **1.4× mniej**,
  - koreańskiego: **1.7× mniej**,
  - hindi: **2.9× mniej**,
  - gudżarati: **4.4× mniej**.
  - To jest poprawa **względem starszego tokenizera OpenAI**, a nie ogólna odpowiedź na pytanie „który język jest najtańszy absolutnie”.
  - Źródło: [Hello GPT-4o](https://openai.com/index/hello-gpt-4o/)
  - Ocena: **praktyczne**.

#### Konflikt źródeł

- **„CJK są bardziej efektywne, bo ideogramy”** — bywa prawdziwe w konkretnych systemach lub promptach.
- **„CJK są mniej efektywne, bo tokenizer je źle tnie”** — też bywa prawdziwe, szczególnie w starszych lub źle dopasowanych tokenizerach.
- **Rozjazd wynika z poziomu analizy:**
  - semantyczna gęstość języka ≠ efektywność tokenizera,
  - nowy tokenizer może odwrócić wnioski ze starego,
  - „ta sama informacja” jest trudna do ścisłego znormalizowania między językami.

### 3. Kontekst i długość okna

#### Czy polski „zjada” więcej context window?

- **Potencjalnie tak, jeśli wymaga większej liczby tokenów dla tej samej treści.** To nie jest osobny mechanizm — to skutek tokenizacji.
- OpenAI i Anthropic wprost zalecają liczenie tokenów przed wysłaniem promptu, bo to wpływa na koszt i długość promptu.
  - Źródła:
    - [What are tokens and how do I count them?](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-do-i-count-them)
    - [Anthropic Token counting](https://docs.anthropic.com/en/docs/build-with-claude/token-counting)
  - Ocena: **praktyczne**.

- **Badania akademickie pokazują, że nierówna tokenizacja zmniejsza realnie użyteczną długość kontekstu.**
  - W pracy o unfair tokenization autorzy zwracają uwagę, że część języków może zmieścić w tym samym limicie tokenów znacznie mniej tekstu.
  - W pracy „Do All Languages Cost the Same?” pokazano, że języki o wysokiej fragmentacji potrafią nie zmieścić nawet jednego kompletnego przykładu few-shot tam, gdzie angielski jeszcze się mieści.
  - Źródła:
    - [Language Model Tokenizers Introduce Unfairness Between Languages](https://proceedings.neurips.cc/paper_files/paper/2023/file/21ed38c2b7e44b7c64d5d380bdf3f16b-Paper-Conference.pdf)
    - [Do All Languages Cost the Same? Tokenization in the Era of Commercial Language Models](https://aclanthology.org/2023.emnlp-main.785.pdf)
  - Ocena: **empiryczne**.

#### Praktyczne implikacje dla długich promptów i dokumentacji

- **Im dłuższy i bardziej techniczny prompt, tym bardziej opłaca się patrzeć na język jako parametr budżetu tokenów.**
- **Długokontextowe benchmarki wielojęzyczne pokazują, że wraz ze wzrostem długości kontekstu rośnie luka między językami wysokiego i niskiego zasobu.**
  - ONERULER (26 języków) raportuje rosnącą lukę przy przejściu od 8K do 128K tokenów i w scenariuszach cross-lingual nawet do **20% wahań** zależnie od języka instrukcji.
  - mLongRR pokazuje spadek z ok. **96% accuracy w angielskim do ok. 36% w somalijskim** dla najlepszych modeli, a przy większej liczbie targetów spadek jest jeszcze mocniejszy.
  - MLRBench sugeruje, że w środowisku wielojęzycznym modele wykorzystują efektywnie **<30% deklarowanego context length**.
  - Źródła:
    - [One ruler to measure them all: Benchmarking multilingual long-context language models](https://arxiv.org/abs/2503.01996)
    - [Evaluating Multilingual Long-Context Models for Retrieval and Reasoning](https://arxiv.org/abs/2409.18006)
    - [Can LLMs reason over extended multilingual contexts? Towards long-context evaluation beyond retrieval and haystacks](https://arxiv.org/abs/2504.12845)
  - Ocena: **empiryczne**, ale część tych benchmarków jest syntetyczna i świeża.

#### Czy warto kompresować prompty przez angielski w częściach technicznych?

- **Często tak, ale głównie tam, gdzie informacja jest już z natury „angielska”:** nazwy pól JSON, kod, nazwy narzędzi, logi, endpointy, nazwy klas, komunikaty systemowe.
- **Nie ma mocnego dowodu, że pełne przejście na angielski zawsze zwiększa jakość.** Są natomiast dobre argumenty, że może zmniejszyć koszt i zużycie kontekstu w warstwie technicznej.
- **Najbezpieczniejsza interpretacja:** angielski bywa dobrym językiem „kompresji technicznej”, ale nie należy automatycznie tłumaczyć treści domenowej, jeśli ma znaczenie lokalny kontekst lub niuanse użytkownika.
- Ocena: **praktyczne + spekulacja**.

### 4. Wielojęzyczność w systemach agentowych

#### Co mówią oficjalne źródła

- **OpenAI:** dla najlepszych wyników warto trzymać cały prompt w jednym języku, kiedy to możliwe; model umie mieszać języki, ale spójność zwykle pomaga.
  - Źródło: [How can I use the OpenAI API with text in different languages?](https://help.openai.com/en/articles/6742369-how-can-i-use-the-openai-api-with-text-in-different-languages)
  - Ocena: **praktyczne**.

- **Anthropic:** warto explicite wskazać język wejścia/wyjścia, używać natywnego skryptu i uwzględniać kontekst kulturowy.
  - Źródło: [Anthropic Multilingual support docs](https://docs.anthropic.com/en/docs/build-with-claude/multilingual-support)
  - Ocena: **praktyczne**.

- **OpenAI Realtime guide:** gdy występuje niepożądane przełączanie języków, należy dodać wyraźną sekcję „Language”; dokumentacja pokazuje też wzorzec mieszany typu **„wyjaśnienia po angielsku, konwersacja po francusku”**.
  - Źródło: [Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide)
  - Ocena: **praktyczne**.

#### Jak production-grade systemy najpewniej to rozwiązują

Poniższe punkty są **syntezą** dokumentacji i badań, a nie jedną publicznie potwierdzoną architekturą „referencyjną”:

1. **Warstwa użytkownika** — język użytkownika.
2. **Warstwa sterowania** — możliwie stabilny język kontrolny (często angielski) dla system promptu, schematów narzędzi, nazw funkcji i formatów strukturalnych.
3. **Warstwa wiedzy / retrieval** — dokument najlepiej zostawiać w języku źródłowym jak najdłużej, a tłumaczyć dopiero to, co trzeba zsyntetyzować dla użytkownika.
4. **Komunikacja agent-agent** — najlepiej przez format ustrukturyzowany (JSON, tool calls, schema) albo przez jeden kontrolowany język pośredni; swobodne mieszanie języków między agentami zwiększa ryzyko dryfu instrukcji.

Ocena: **praktyczne + spekulacja**.

#### Czy są wzorce „prompt w języku X, output w języku Y”?

- **Tak.** Jest to już jawnie pokazywane w dokumentacji OpenAI dla voice/realtime i potwierdzane w badaniach selective pre-translation.
- **Najbardziej wiarygodny wzorzec z badań:**
  - instrukcja może być po angielsku,
  - kontekst pozostaje w języku źródłowym,
  - output ustawiasz w języku potrzebnym użytkownikowi lub downstream systemowi.
- Źródła:
  - [Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide)
  - [The Impact of Prompt Translation Strategies in Cross-lingual Prompting for Low-Resource Languages](https://aclanthology.org/2025.loresmt-1.9.pdf)
  - [LLM Prompting for Localization: English or Native Language in Multilingual Text Understanding](https://openreview.net/forum?id=27pOlHjUge)
- Ocena: **praktyczne + empiryczne**.

### 5. Języki azjatyckie — efektywność

#### Czy chiński/japoński faktycznie są bardziej efektywne tokenowo?

- **Nie udało się potwierdzić wersji absolutnej („tak, są”) ani absolutnego zaprzeczenia („nie, nie są”).**
- **Najuczciwszy wniosek:**
  - semantycznie gęste skrypty mogą być bardzo zwarte,
  - ale efektywność kosztowa zależy od konkretnego tokenizera,
  - ten sam język może wypaść inaczej między generacjami modeli.

#### Co wspierają źródła

- **OpenAI 4o poprawił tokenizację CJK względem starszego tokenizera.** To sugeruje, że wcześniejsze wersje miały realny margines poprawy i że CJK nie były idealnie obsłużone.
  - Źródło: [Hello GPT-4o](https://openai.com/index/hello-gpt-4o/)
  - Ocena: **praktyczne**.

- **Anthropic raportuje bardzo małą lukę jakościową wobec angielskiego dla chińskiego, japońskiego i koreańskiego w swoich publicznych evalach.**
  - Źródło: [Anthropic Multilingual support docs](https://docs.anthropic.com/en/docs/build-with-claude/multilingual-support)
  - Ocena: **praktyczne**.

- **Są też źródła pokazujące, że nowy tokenizer nie rozwiązuje wszystkiego.** Badanie o tokenizer bias wskazuje przypadki, gdzie GPT-4o kompresuje chiński mocniej niż GPT-4, ale jednocześnie ma problemy z interpretacją pewnych długich chińskich tokenów.
  - Źródło: [Problematic Tokens: Tokenizer Bias in Large Language Models](https://arxiv.org/html/2406.11214v3)
  - Ocena: **empiryczne**.

#### Trade-offy

- **Plusy używania natywnych języków azjatyckich:**
  - lepsze dopasowanie do użytkownika końcowego,
  - w części tokenizerów potencjalnie dobra gęstość informacji,
  - wysoka jakość dla dużych języków w modelach frontier.

- **Minusy / ryzyka:**
  - nieprzewidywalność tokenizacji między modelami,
  - potencjalne problemy interoperacyjności z kodem, dokumentacją techniczną i narzędziami opartymi na angielskich etykietach,
  - trudniej porównywać koszty bez realnego policzenia tokenów dla konkretnej treści,
  - w niektórych modelach/tokenizerach możliwe problemy na długich, rzadkich lub domenowych tokenach.

#### Case studies firm azjatyckich używających natywnych języków w produkcji

- **Nie udało się znaleźć mocnych, publicznych i porównywalnych case studies firm azjatyckich skoncentrowanych dokładnie na decyzji „native language vs English prompting” w systemach agentowych.** To jest realna luka.
- Da się znaleźć **pośrednie** case studies:
  - [ChatAndBuild customer story](https://www.anthropic.com/customers/chatandbuild?_=) — firma raportuje, że użytkownicy pracujący w „gęstych językach” jak japoński potrafili opisywać wymagania aplikacji w **40–60% mniejszej liczbie tokenów** niż po angielsku. To jednak **nie jest badanie naukowe** ani porównanie między modelami; to obserwacja produktowa konkretnej firmy.
  - [Lokalise improves translation quality with Claude](https://www.anthropic.com/customers/lokalise) — nie jest to firma azjatycka, ale opisuje produkcyjne użycie wielu języków, w tym pary **Japanese ↔ English**, z mierzalnym acceptance rate i oszczędnością kosztów.
- Ocena: **praktyczne**, ale o ograniczonej sile uogólnienia.

### 6. Rekomendacje praktyczne

Poniższe rekomendacje są **syntezą badań + dokumentacji**, nie gotowym „policy template” dla konkretnego projektu.

#### Kiedy używać polskiego

- **Gdy użytkownik końcowy komunikuje się po polsku** i liczy się jakość interakcji, ton, niuanse, zgodność z lokalnym kontekstem.
- **Gdy kontekst źródłowy jest po polsku** i zadanie jest ekstrakcyjne lub mocno osadzone lokalnie.
- **Gdy sprawdzasz jakość modelu na realnych danych użytkownika**, a nie tylko na benchmarku tłumaczonym.
- Ocena: **praktyczne**.

#### Kiedy używać angielskiego

- **Dla warstwy technicznej:** kod, JSON, tool schemas, nazwy pól, endpointy, logi, stack traces, dokumentacja frameworków.
- **Gdy prompt jest bardzo długi i techniczny** i chcesz oszczędzać budżet tokenów w warstwie kontrolnej.
- **Gdy task jest bliższy reading comprehension / reasoning na materiałach już po angielsku** albo gdy sam model/vendor sugeruje lepszą stabilność w angielskim.
- Ocena: **praktyczne**.

#### Czy mieszać języki w jednym prompcie?

- **Tak, ale selektywnie, nie chaotycznie.**
- Najlepsze uzasadnione wzorce to:
  - instrukcja systemowa / sterowanie: EN lub stały język kontrolny,
  - kontekst użytkownika / cytaty / retrieval: język źródłowy,
  - output: język użytkownika,
  - kod / JSON / nazwy narzędzi: zwykle EN.
- **Nie zaleca się przypadkowego code-switchingu w obrębie tej samej instrukcji**, bo oficjalna dokumentacja OpenAI podkreśla, że trzymanie promptu w jednym języku „when possible” poprawia spójność.
- Źródła:
  - [How can I use the OpenAI API with text in different languages?](https://help.openai.com/en/articles/6742369-how-can-i-use-the-openai-api-with-text-in-different-languages)
  - [The Impact of Prompt Translation Strategies in Cross-lingual Prompting for Low-Resource Languages](https://aclanthology.org/2025.loresmt-1.9.pdf)
  - [Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide)
- Ocena: **praktyczne + empiryczne**.

#### Best practices dla projektów wielojęzycznych

1. **Jawnie ustaw język wejścia i wyjścia.**
2. **Testuj język jako parametr ewaluacji**, nie jako detal implementacyjny.
3. **Oddziel warstwę UX od warstwy kontrolnej.**
4. **Licz tokeny na realnych promptach** dla każdego dostawcy i modelu przed decyzją o języku technicznym.
5. **Nie zakładaj, że benchmark tłumaczony oddaje realny use case.**
6. **W retrieval i ekstrakcji utrzymuj kontekst w języku źródłowym jak najdłużej.**
7. **Dla long-context i agentów wielokrokowych mierz nie tylko accuracy, ale też token budget, latencję i liczbę mieszczących się przykładów few-shot.**

Ocena: **praktyczne**.

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić publicznie jednej, aktualnej i oficjalnej tabeli tokenów dla „tej samej treści” w EN vs PL vs ZH/JA/KO dla aktualnych modeli OpenAI i Anthropic.** Dokumentacja mówi o kierunku zjawiska, ale nie daje kompletnego porównania dla polskiego.
- **Nie udało się znaleźć mocnej, publicznej i bezpośrednio porównywalnej serii case studies firm azjatyckich o decyzjach prompt-language w produkcyjnych systemach agentowych.** Dostępne są raczej customer stories vendorów i pojedyncze obserwacje produktowe.
- **Wiele benchmarków wielojęzycznych jest tłumaczeniami angielskiego MMLU**, co utrudnia wyciąganie wniosków o „natywnej” kompetencji w języku polskim lub azjatyckich językach.
- **Brakuje bezpośrednich, publicznych benchmarków porównujących GPT-4 / Claude konkretnie na polskim reasoning, coding, creative writing i factual QA w jednym spójnym setupie.** Dostępne dane są rozproszone po domenach.
- **Świeże benchmarki długiego kontekstu są obiecujące, ale część z nich jest syntetyczna i jeszcze nie stanowi stabilnego standardu branżowego.**
- **Wyniki dotyczące języków azjatyckich są sprzeczne, bo mieszają dwa poziomy: gęstość informacji w języku i efektywność konkretnego tokenizera.**

## Źródła / odniesienia

- [GPT-4 Technical Report](https://arxiv.org/pdf/2303.08774.pdf) — oficjalny raport OpenAI; zawiera tabelę multilingual MMLU, w tym wynik dla polskiego.
- [OpenAI: How can I use the API with text in different languages?](https://help.openai.com/en/articles/6742369-how-can-i-use-the-openai-api-with-text-in-different-languages) — oficjalna nota o wielojęzyczności; ważna dla praktycznych zaleceń dot. spójności promptu.
- [OpenAI: What are tokens and how do I count them?](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-do-i-count-them) — oficjalne wyjaśnienie tokenów i notatka, że języki nieangielskie często mają wyższy token/char ratio.
- [Hello GPT-4o](https://openai.com/index/hello-gpt-4o/) — oficjalny wpis o GPT-4o; zawiera przykłady poprawy tokenizacji wielu języków.
- [OpenAI API Pricing](https://openai.com/api/pricing/) — oficjalny cennik; potrzebny do powiązania tokenizacji z kosztem.
- [Realtime Prompting Guide](https://developers.openai.com/cookbook/examples/realtime_prompting_guide) — oficjalne wzorce sterowania językiem i mieszania ról językowych.
- [Anthropic Multilingual support docs](https://docs.anthropic.com/en/docs/build-with-claude/multilingual-support) — oficjalna dokumentacja Anthropic z wynikami relatywnymi do angielskiego i best practices.
- [Claude Sonnet 4.6 System Card](https://www-cdn.anthropic.com/6a5fa276ac68b9aeb0c8b6af5fa36326e0e166dd.pdf) — system card z GMMLU/MILU i rozbiciem na języki wysokiego/średniego/niskiego zasobu.
- [Anthropic Token counting](https://docs.anthropic.com/en/docs/build-with-claude/token-counting) — dokumentacja liczenia tokenów i ich roli w kosztach/promptach.
- [Evaluation of the performance of GPT-3.5 and GPT-4 on the Polish Medical Final Examination](https://pubmed.ncbi.nlm.nih.gov/37993519/) — recenzowane badanie na polskim egzaminie medycznym; rzadkie twarde dane PL vs EN.
- [Comparing the performance of ChatGPT, Gemini, and Claude in English and Polish on medical examinations](https://www.nature.com/articles/s41598-025-17030-0) — recenzowane porównanie EN vs PL dla kilku modeli na polskich egzaminach medycznych.
- [Language Model Tokenizers Introduce Unfairness Between Languages](https://proceedings.neurips.cc/paper_files/paper/2023/file/21ed38c2b7e44b7c64d5d380bdf3f16b-Paper-Conference.pdf) — jedna z kluczowych prac o nierównościach tokenizacji między językami.
- [Do All Languages Cost the Same? Tokenization in the Era of Commercial Language Models](https://aclanthology.org/2023.emnlp-main.785.pdf) — pokazuje związek tokenizacji z kosztem i użytecznością in-context learning.
- [Excessively Dividing Texts Can Break Down Tokenizers in Large Language Models](https://aclanthology.org/2024.acl-long.328.pdf) — praca o nadmiernej fragmentacji tokenizera, ważna dla CJK.
- [Tokenization efficiency of current foundational large language models for the Ukrainian language](https://pmc.ncbi.nlm.nih.gov/articles/PMC12380774/) — nowsza praca pokazująca, jak tokenizacja wpływa na koszt/szybkość i jak można porównywać języki względem angielskiego.
- [Problematic Tokens: Tokenizer Bias in Large Language Models](https://arxiv.org/html/2406.11214v3) — case study o problemach z chińskimi tokenami i różnicach GPT-4 vs GPT-4o.
- [Global MMLU: Understanding and Addressing Cultural and Linguistic Biases in Multilingual Evaluation](https://arxiv.org/pdf/2502.13509) — ważny caveat metodologiczny wobec benchmarków tłumaczonych z angielskiego.
- [A Fair Comparison without Translationese: English vs. Target-language Instructions for Multilingual LLMs](https://aclanthology.org/2025.naacl-short.55.pdf) — badanie o wpływie języka instrukcji po wyeliminowaniu translationese.
- [The Impact of Prompt Translation Strategies in Cross-lingual Prompting for Low-Resource Languages](https://aclanthology.org/2025.loresmt-1.9.pdf) — najmocniejsze źródło o selective pre-translation i cross-lingual prompting.
- [LLM Prompting for Localization: English or Native Language in Multilingual Text Understanding](https://openreview.net/forum?id=27pOlHjUge) — badanie sugerujące, że dla części zadań English prompts mogą być wystarczające.
- [Native vs Non-Native Language Prompting: A Comparative Analysis](https://arxiv.org/html/2409.07054v2) — porównanie native / mixed / non-native promptingu; przydatne jako kontrapunkt i źródło konfliktów.
- [One ruler to measure them all: Benchmarking multilingual long-context language models](https://arxiv.org/abs/2503.01996) — benchmark long-context w 26 językach; ważny dla cross-lingual i long-context drift.
- [Evaluating Multilingual Long-Context Models for Retrieval and Reasoning](https://arxiv.org/abs/2409.18006) — mLongRR; pokazuje silne spadki jakości wraz z długością kontekstu i niższym zasobem języka.
- [Can LLMs reason over extended multilingual contexts? Towards long-context evaluation beyond retrieval and haystacks](https://arxiv.org/abs/2504.12845) — MLRBench; ważne źródło o realnie użytecznej długości kontekstu w ustawieniach wielojęzycznych.
- [ChatAndBuild customer story](https://www.anthropic.com/customers/chatandbuild?_=) — case study vendorowe z obserwacją o niższym token usage dla japońskiego; użyte ostrożnie jako sygnał praktyczny, nie dowód ogólny.
- [Lokalise improves translation quality with Claude](https://www.anthropic.com/customers/lokalise) — case study produkcyjnego użycia wielojęzycznego, w tym par z japońskim.
