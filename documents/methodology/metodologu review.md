# Recenzja obecnej metodologi od 4 agentów:

## 1

Czytam to jak system pracy, nie jak manifest. Najmocniejsze pytanie, które sprawdzam, brzmi: czy ta metodologia realnie zwiększa trafność decyzji i jakość wyników, czy tylko porządkuje narrację o pracy.

Thought for 33s

Ocena ogólna: to nie jest jeszcze mocna metodologia operacyjna, tylko dobrze ujęta filozofia pracy + model governance + zestaw sensownych heurystyk organizacyjnych. Dokument dobrze porządkuje role, ciągłość i obieg kontekstu, ale słabiej odpowiada na najważniejsze pytanie metodologiczne: skąd wiadomo, że wynik pracy z agentem jest trafny, a nie tylko spójnie opisany. Innymi słowy: dokument lepiej reguluje kto, kiedy i na jakim poziomie myśli o pracy, niż jak odróżniać prawdę od pozoru poprawności. 

METHODOLOGY

To, co tu naprawdę trzyma projekt, to trzy rzeczy. Po pierwsze, rozdzielenie poziomów Agent / Developer / Metodolog jest sensowne, bo ogranicza mieszanie wykonawstwa z projektowaniem zasad i z refleksją nad procesem. Po drugie, nacisk na zewnętrzną pamięć projektu — dokumenty, progress log, routing kontekstu — jest trafny; to jest realna odpowiedź na problem utraty ciągłości przez model. Po trzecie, zasada proporcjonalności dokumentacji do skali zadania jest praktyczna i zdrowa. To są elementy, które mają wartość nie dlatego, że brzmią mądrze, tylko dlatego, że rozwiązują realne problemy pracy z LLM. 

METHODOLOGY

Największa słabość: dokument myli częściowo metodologię poznawczą z architekturą procesu. Masz dużo o routingach, handoffach, chronionych warstwach, strukturze folderów, progresie i autokomprsji kontekstu, ale za mało o walidacji twierdzeń, kontroli błędu, kryteriach jakości, poziomach pewności i procedurach falsyfikacji. To powoduje, że system może być bardzo uporządkowany, a mimo to produkować błędne wnioski. Dobrze opisany proces nie jest jeszcze dobrym procesem. Tutaj governance jest mocniejsze niż epistemologia. 

METHODOLOGY

Druga poważna słabość: dokument jest miejscami przeteoretyzowany. Odwołania do cybernetyki drugiego rzędu, double-loop learning, rekurencji i fraktalności budują ramę interpretacyjną, ale nie zawsze przekładają się na ostre decyzje operacyjne. W metodologii liczy się nie tylko to, czy opis jest inteligentny, ale czy zmniejsza niejednoznaczność działania. Tu część języka robi wrażenie, ale nie redukuje ryzyka. „Fraktalność”, „genomiczność”, „obserwator obserwatora” — to są pojęcia inspirujące, lecz w obecnej postaci zbyt łatwo stają się ozdobnym metajęzykiem. Gdyby je wyciąć, rdzeń dokumentu nadal by działał. To znak, że są bardziej legitymizacją niż nośnikiem koniecznej treści. 

METHODOLOGY

Trzecia słabość to ukryte założenia, których dokument prawie nie ujawnia. Zakłada, że użytkownik jest stabilnym, kompetentnym gatekeeperem i potrafi zatwierdzać eskalacje mimo braku pełnego rozumienia technicznego. Zakłada, że stan projektu da się wystarczająco dobrze eksternalizować w dokumentach. Zakłada, że głównym problemem jest utrata ciągłości i pomieszanie poziomów, a nie np. błędna analiza domeny, halucynacje, złe priorytety lub fałszywe założenia wejściowe. Zakłada też, że praca jest przede wszystkim tekstowo-dokumentacyjna. To wszystko może być prawdą w części projektów, ale nie jest prawdą ogólną. Bez ujawnienia tych założeń metodologia wygląda na bardziej uniwersalną, niż jest. 

METHODOLOGY

Jest też napięcie logiczne w samej strukturze. Z jednej strony bronisz separacji poziomów i zakazu mieszania ról. Z drugiej strony centralnym źródłem poprawy ma być meta-obserwacja własnej pracy, czyli de facto przenikanie poziomów: wykonanie ma generować refleksję o zasadach, a refleksja ma zmieniać wykonanie. To napięcie jest twórcze, ale u ciebie nie jest rozstrzygnięte proceduralnie. Kiedy dokładnie kończy się „sygnał do wyższego poziomu”, a zaczyna nieuprawnione mieszanie poziomów? Jak odróżnić zwykłą poprawkę lokalną od obserwacji o randze metodologicznej? Dokument mówi: „zauważ i zapytaj”, ale nie daje kryteriów progu. To zostawia dużą dowolność. 

METHODOLOGY

Zasada eskalacji „wyłącznie w górę” jest elegancka, ale ma koszt. Chroni przed chaosem, lecz grozi wąskim gardłem decyzyjnym i sztucznym usztywnieniem systemu. W praktyce część problemów nie wymaga „wyższego poziomu”, tylko sprzężenia zwrotnego poziomego albo szybkiej lokalnej korekty. Jeżeli każdy insight architektoniczny ma przechodzić przez użytkownika jako mediatora, to system staje się bezpieczniejszy, ale wolniejszy i bardziej zależny od jakości decyzji jednej osoby. To jest świadomy trade-off, ale dokument traktuje go jak rozwiązanie, a nie jak koszt z konsekwencjami. 

METHODOLOGY

Słabe jest też to, że wiele kluczowych elementów pozostaje „organicznych”: format progress logu, kształt dokumentacji, sposób dojrzewania praktyk. To daje elastyczność, ale metodologicznie oznacza też niski poziom standaryzacji. Jeżeli forma ma się „wypracować sama”, to porównywalność sesji, projektów i błędów będzie słaba. A bez porównywalności trudno budować realne uczenie się procesu. Double-loop learning bez choćby minimalnej standaryzacji bardzo łatwo zamienia się w serię anegdot o tym, „co tym razem zadziałało”. 

METHODOLOGY

Największe ryzyko błędu jest takie: system zacznie nagradzać spójność dokumentacyjną zamiast trafności rozstrzygnięć. Agent może dobrze logować stan, poprawnie eskalować, nie naruszać warstwy chronionej, prowadzić plan i refleksję, a mimo to opierać się na błędnych przesłankach. Dokument nie ma prawie nic o tym, jak sprawdzać poprawność merytoryczną wyników: gdzie potrzebny jest test, gdzie niezależna weryfikacja, gdzie kontrargument, gdzie próg niepewności, gdzie obowiązkowe źródła, gdzie reprodukcja wyniku. To nie jest detal. To jest dziura centralna. 

METHODOLOGY

Czy z tego da się wyciągać sensowne wnioski? Tak, ale tylko określonego rodzaju. Ta metodologia nadaje się do poprawy ciągłości pracy, przejrzystości ról, kontroli zmian w zasadach i kumulowania praktycznych lekcji. Jest dobra jako system zarządzania współpracą człowiek–LLM. Nie jest wystarczająca jako metodologia, która sama z siebie gwarantuje, że wnioski końcowe są solidne. Dla projektów niskiego i średniego ryzyka to może wystarczyć. Dla projektów z większą stawką — technicznych, analitycznych, badawczych, produktowych — bez warstwy walidacyjnej będzie za słaba. 

METHODOLOGY

Co bym poprawił w pierwszej kolejności:

Dodaj warstwę epistemiczną.
Obok planu, implementacji i refleksji potrzebujesz jawnego kroku: weryfikacja. Nie jako ogólny postulat, tylko jako procedura: co w tym typie zadania liczy się jako dowód poprawności, jak sprawdzasz twierdzenia, jakie są źródła błędu, kto lub co pełni rolę niezależnego sprawdzenia. 

METHODOLOGY

Zdefiniuj kryteria jakości wyjścia.
Każdy tryb pracy powinien mieć minimalne kryteria akceptacji: kompletność, poprawność, testowalność, odwracalność zmian, ślad decyzji, jawność założeń, poziom pewności. Dziś dokument mówi, jak pracować; powinien też mówić, po czym poznajesz, że wynik jest wystarczająco dobry. 

METHODOLOGY

Ogranicz metafory, zwiększ operacyjność.
Zostaw 20% teorii, wyrzuć 80% ozdobników. Każde pojęcie ma przejść prosty test: czy zmienia decyzję operacyjną? Jeśli nie, jest balastem. W obecnej wersji teoria podnosi rangę tekstu, ale nieproporcjonalnie mało zwiększa jego sterowność. 

METHODOLOGY

Ujawń i skataloguj założenia brzegowe.
Napisz wprost: dla jakich projektów to działa, dla jakich nie; jaki poziom kompetencji użytkownika jest zakładany; kiedy użytkownik jako mediator staje się ryzykiem; kiedy dokumentacja przestaje być opłacalna; kiedy trzeba odejść od modelu „eskalacja tylko w górę”. 

METHODOLOGY

Wprowadź progi eskalacji.
Nie wystarczy „zauważam coś istotnego”. Potrzebne są warunki: np. powtarzalność błędu, wpływ na więcej niż jedno zadanie, konflikt zasad, koszt potencjalnej pomyłki, naruszenie architektury, nieodwracalność decyzji. Bez tego eskalacja pozostaje uznaniowa. 

METHODOLOGY

Ustandaryzuj minimum dla progress logu i refleksji.
Nie wszystko musi być sztywne, ale pewne pola powinny być obowiązkowe: stan, następny krok, otwarte ryzyka, decyzje i ich uzasadnienie, znane niepewności, sposób weryfikacji. Inaczej „organiczność” zamieni się w nierówną jakość pamięci projektu. 

METHODOLOGY

Najkrótszy uczciwy werdykt jest taki: to jest dobra rama zarządzania współpracą z LLM, ale jeszcze nie dość dobra metodologia dochodzenia do wiarygodnych wniosków. Ma zdrowy rdzeń organizacyjny. Ma słabą warstwę walidacyjną. Jeżeli ją uzupełnisz, dokument może stać się naprawdę mocny. Bez tego będzie dobrze porządkował pracę, ale nie da ci wystarczającej ochrony przed elegancko uporządkowanym błędem. 

METHODOLOGY

Jeśli chcesz, mogę teraz przejść krok dalej i zrobić red-team tej metodologii: wypisać konkretne scenariusze, w których ten system zawiedzie w praktyce.

## 2
Przeczytałem to jako dokument metodologiczny, nie jako manifest. Idę w to, co jest nośne, a co tylko brzmi mądrze.

Thought for 21s

Ta „metodologia” w obecnej formie nie jest jeszcze metodologią w sensie ścisłym. To jest miks: filozofia pracy, model ról, zasady governance, kilka sensownych heurystyk operacyjnych i sporo języka, który dodaje powagi, ale nie zwiększa sterowalności procesu. Najkrótsza trafna diagnoza: masz dobry szkielet zarządzania współpracą z agentem, ale słabo zoperacjonalizowaną metodę. 

METHODOLOGY

Co tu faktycznie działa

Rozdzielenie poziomów Agent / Developer / Metodolog ma sens. Chroni przed klasycznym błędem: agent wykonawczy zaczyna sam sobie przepisywać reguły gry. To jest realny problem i twoja separacja ról adresuje go sensownie. Podobnie sens ma „warstwa chroniona” dla wytycznych oraz traktowanie progress logu jako zewnętrznej pamięci stanu. To są elementy praktyczne, a nie dekoracyjne. 

METHODOLOGY

Działa też nacisk na ciągłość projektu niezależnie od konkretnej sesji modelu. To jest metodologicznie zdrowe, bo stan projektu faktycznie nie powinien siedzieć w pamięci jednej rozmowy. Dobre jest również rozpoznanie, że okno kontekstowe jest zasobem, którym trzeba zarządzać, a nie magiczną przestrzenią bez kosztu. 

METHODOLOGY

Pętla meta-obserwacji też ma wartość. Nie dlatego, że brzmi „cybernetycznie”, tylko dlatego, że wymusza uczenie się na błędach promptowania i organizacji pracy. To jest jedna z niewielu części dokumentu, która rzeczywiście zbliża się do czegoś, co można nazwać mechanizmem doskonalenia procesu. 

METHODOLOGY

Co jest metodologicznie słabe

Największy problem: dokument nie definiuje, po czym poznajesz, że metoda działa. Nie ma wskaźników, progów, kryteriów wejścia/wyjścia, kosztów ubocznych, jakościowych punktów kontrolnych, niczego. Mówisz, że metodologia „powstała empirycznie”, ale nie pokazujesz żadnego trybu zbierania obserwacji, żadnej struktury dowodu, żadnego sposobu odróżnienia poprawy od subiektywnego wrażenia poprawy. To jest na razie deklaracja empiryczności, nie empiryczność. 

METHODOLOGY

Drugi problem: mieszasz poziom opisu z poziomem uzasadnienia. Część dokumentu mówi, jak organizować pracę. Część mówi, dlaczego to ma sens. Część daje quasi-filozoficzne ramy interpretacyjne. To samo w sobie nie jest błędem, ale u ciebie skutkuje rozmyciem: nie wiadomo, które elementy są twardymi regułami, które heurystykami, które hipotezami, a które tylko językiem samoopisu projektu. W efekcie trudno tym zarządzać, bo nie wiadomo, co wolno naruszyć, co trzeba testować, a co jest tylko inspiracją. 

METHODOLOGY

Trzeci problem: operacjonalizacja jest słaba albo nie istnieje. Na przykład „zasada fraktalna” brzmi efektownie, ale metodologicznie jest prawie pusta. Nie podajesz warunków, kiedy ta sama struktura faktycznie ma być reużywana, a kiedy podobieństwo jest pozorne. „Fraktalność” jest tu metaforą, nie procedurą. To samo dotyczy „rekurencji”, „cybernetyki drugiego rzędu”, „nasłuchu”. One pełnią bardziej rolę legitymizującą niż projektową. 

METHODOLOGY

Czwarty problem: masz skłonność do ontologizowania własnych praktyk. Piszesz tak, jakby struktura trzech poziomów była naturalnym porządkiem pracy z agentem, a nie jedną z możliwych architektur koordynacji. To jest niebezpieczne, bo zamienia użyteczną konwencję w dogmat. Każdy element tej architektury powinien być przedstawiony jako rozwiązanie o określonych kosztach i zastosowaniach, a nie jako domyślna prawda o systemie. 

METHODOLOGY

Gdzie dokument udaje większą solidność niż ma

Odwołania do Argyrisa, Schöna, von Foerstera i język typu „genomiczny”, „fraktalny”, „rekurencyjny”, „cybernetyka drugiego rzędu” budują aurę głębi, ale nie przekładają się na lepszą kontrolę błędu. Innymi słowy: to nie wzmacnia metodologii, tylko jej styl. Można to zostawić jako warstwę interpretacyjną, ale nie wolno mylić tego z rygorem. W obecnym kształcie ta warstwa miejscami robi za intelektualny makijaż. 

METHODOLOGY

Szczególnie słabe jest zdanie, że metodologia „ma charakter genomiczny: może ewoluować szybko, a projekt jest zawsze jej odzwierciedleniem”. To brzmi nośnie, ale metodologicznie niczego nie wyjaśnia. Co dokładnie dziedziczy projekt z metody? Jak rozpoznajesz mutację korzystną od degradacji? Jakie są mechanizmy selekcji? Bez tego to jest metafora bez pracy poznawczej. 

METHODOLOGY

Podobnie z „hipotezą: nasłuch”. Dobrze, że oznaczasz ją jako nieprzetestowaną, ale nadal nie ma tu planu walidacji. Jakie miałbyś mierzyć skutki? Szybsze wykrywanie problemów? Mniej błędnych eskalacji? Mniejszy koszt poznawczy dla Agenta? Bez tego to jest pomysł produktowy, nie hipoteza metodologiczna. 

METHODOLOGY

Ukryte założenia, których dokument nie rozlicza

Zakładasz, że użytkownik jest dobrym mediatorem i gatekeeperem między instancjami. To jest duże i często fałszywe założenie. Użytkownik może nie mieć dość wiedzy, czasu ani dyscypliny, żeby sensownie filtrować eskalacje i przenosić handoffy. Wtedy twój model nie zwiększa jakości, tylko dokłada tarcie. Dokument tego kosztu nie rozlicza. 

METHODOLOGY

Zakładasz też, że separacja poziomów zmniejsza chaos bardziej, niż zwiększa koszt koordynacji. To bywa prawdą w dużych projektach, ale w małych i średnich zadaniach może być odwrotnie: sztuczny podział ról generuje ceremonialność bez zysku. Masz sekcję o skalowaniu dokumentacji, ale nie masz równie ostrej reguły skalowania samej architektury ról. To luka. 

METHODOLOGY

Kolejne założenie: że pełna lista „otwartych wątków” powinna wchodzić do każdego planu. To jest niebezpieczne. Bez mechanizmu priorytetyzacji i wygaszania wątków dostaniesz rosnącą listę zobowiązań, która imituje kontrolę, a faktycznie zatruwa focus. To jest typowy błąd systemów dokumentacyjnych: mylenie kompletności rejestru z jakością sterowania. 

METHODOLOGY

Granice wnioskowania i ryzyko nadinterpretacji

Z tego dokumentu nie wynika jeszcze, że ta metoda poprawia jakość wyników projektu. Wynika tylko, że porządkuje sposób myślenia o współpracy z LLM. To nie jest to samo. Porządek procesu może pomagać, ale może też produkować biurokrację i złudzenie kontroli. Bez porównania z alternatywami nie możesz twierdzić, że metoda działa lepiej niż prostsze podejścia. 

METHODOLOGY

Dokument przecenia też rolę dokumentacji jako nośnika ciągłości. Owszem, dokumentacja pomaga, ale zła dokumentacja też „utrwala stan” — tylko zły stan, zły model problemu i złe decyzje. Nie masz mechanizmu audytu jakości tej dokumentacji. To istotna dziura: zewnętrzna pamięć bez kontroli jakości jest równie zdolna konserwować błędy, jak wiedzę. 

METHODOLOGY

Najsłabsze miejsca konkretne

Najsłabsze zdanie funkcjonalnie: że ARCHITECTURE.md „zawsze istnieje jako jądro”. To jest dogmat organizacyjny, nie wniosek metodologiczny. Dla części zadań sensowniejszym jądrem może być spec przepływu pracy, test plan albo decision log. Upieranie się przy jednym centralnym artefakcie grozi forsowaniem formy niezależnie od natury zadania. 

METHODOLOGY

Drugie słabe miejsce: „każda taka obserwacja powinna zostać zapisana możliwie szybko”. Intuicyjnie słuszne, ale bez filtra jakości kończy się zalewem mikro-reguł i lokalnych wyjątków. Brakuje kryterium: które obserwacje zasługują na utrwalenie, które są tylko jednorazowym szumem, a które powinny poczekać na replikację. 

METHODOLOGY

Trzecie słabe miejsce: „projekt jest odzwierciedleniem metody”. To zdanie jest zbyt mocne i niemal tautologiczne. Każdy projekt częściowo odzwierciedla swoją metodę, ale też domenę, zespół, ograniczenia czasu, budżet, jakość decyzji i przypadek. U ciebie metoda dostaje status czynnika dominującego bez uzasadnienia. 

METHODOLOGY

Co bym zostawił, a co wyrzucił

Zostawiłbym:
rozdzielenie ról, warstwę chronioną, progress log jako pamięć zewnętrzną, aktywne zarządzanie kontekstem, pętlę meta-obserwacji. To są rzeczy praktyczne. 

METHODOLOGY

Wyrzuciłbym albo brutalnie skrócił:
większość metaforyki („genomiczny”, „fraktalny”, część „cybernetyki drugiego rzędu”), bo obecnie bardziej pudruje brak procedur, niż coś wyjaśnia. Zostawiłbym najwyżej jedno krótkie uzasadnienie teoretyczne, jeśli naprawdę chcesz mieć warstwę filozoficzną. 

METHODOLOGY

Przepisałbym od zera:
sekcje, które dziś są opisem intuicji, na format decyzji operacyjnych: kiedy stosować, kiedy nie stosować, koszt, ryzyko, warunki wyjątku, artefakt wejściowy, artefakt wyjściowy. Tego tu najbardziej brakuje. 

METHODOLOGY

Co trzeba naprawić, żeby to zaczęło być metodologią, a nie tylko narracją

Po pierwsze, dodaj kryteria skuteczności. Na przykład: liczba błędnych zmian w wytycznych, liczba utraconych wątków między sesjami, czas dojścia nowej sesji do produktywności, odsetek handoffów kończących się realną poprawą, koszt dokumentacji względem złożoności zadania. Bez tego nie mierzysz niczego. 

METHODOLOGY

Po drugie, rozdziel dokument na trzy warstwy:

założenia,

reguły operacyjne,

hipotezy do testu.
Teraz to wszystko siedzi razem i rozmywa odpowiedzialność poznawczą. 

METHODOLOGY

Po trzecie, każdej regule dopisz:
zakres stosowania, sygnał uruchamiający, spodziewaną korzyść, koszt, ryzyko nadużycia, warunek odstępstwa. Wtedy przestajesz mieć „mądrze brzmiący system”, a zaczynasz mieć instrukcję działania. 

METHODOLOGY

Po czwarte, wprowadź rejestr zmian metodologii z minimalnym standardem dowodu. Nie „wydaje mi się, że pomogło”, tylko: problem, interwencja, obserwowana zmiana, kontekst, decyzja: utrwalamy / testujemy dalej / odrzucamy. 

METHODOLOGY

Ostateczny werdykt

To nie jest zły dokument. Ale jest bardziej inteligentnie napisany niż metodologicznie domknięty. Najmocniejsze fragmenty są tam, gdzie schodzisz do praktyki organizacji pracy. Najsłabsze tam, gdzie próbujesz podnieść rangę dokumentu metaforą i teorią bez przekucia ich w procedury. 

METHODOLOGY

W obecnej formie oceniłbym to tak:
jako rama refleksyjno-organizacyjna — sensowne; jako metodologia z rygorem — niedorobione; jako dokument łatwo wpadający w pozór solidności — niestety tak. 

METHODOLOGY

Mogę też zrobić drugą rundę w trybie jeszcze bardziej bezlitosnym: akapit po akapicie, z oznaczeniem „trafne / puste / ryzykowne / niefalsyfikowalne / do przepisania”.

## 3
Przejrzę to jak metodolog, nie jak redaktor. Skupię się na tym, co w tej konstrukcji rzeczywiście kontroluje jakość wnioskowania, a co tylko daje poczucie porządku.

Thought for 29s

To nie jest zła metodologia. Ale w obecnej formie jest bardziej filozofią pracy z LLM niż metodologią w ścisłym sensie. Daje porządek, język i rytuały. Dużo słabiej daje kryteria trafności, reguły decyzji i mechanizmy kontroli błędu. To podstawowy problem. 

METHODOLOGY

Gdzie to naprawdę działa

Najmocniejszy element to nacisk na zewnętrzną pamięć projektu: dokumentację, progress log, jawne handoffy, ochronę wytycznych, rozdzielenie poziomu wykonawczego od poziomu refleksji. To jest sensowne, bo największym praktycznym problemem pracy z LLM zwykle nie jest pojedyncza odpowiedź, tylko utrata ciągłości, rozmycie decyzji i niejawne zmiany zasad działania. Tu trafiasz w realny punkt bólu. 

METHODOLOGY

Dobra jest też intuicja, że trzeba odróżnić trzy rzeczy: wykonanie zadania, kształtowanie instrukcji i ocenę samej metody. To może ograniczać chaos i samozmieniające się reguły. Krótko: separacja ról ma sens. 

METHODOLOGY

Sensowna jest również pętla meta-obserwacji: pytania o to, co agent zrobił źle, co trzeba było doprecyzować i czy problem wynika z brakującej reguły. To jest praktycznie użyteczne, bo zamienia pojedyncze potknięcia w materiał do poprawy procesu. 

METHODOLOGY

Co tu jest słabe w sensie metodologicznym

Najważniejsze: ten dokument prawie w ogóle nie definiuje, po czym poznajesz, że metoda działa. Masz strukturę, role, eskalację, dokumenty, ochronę warstw i rytm pracy, ale nie masz operacyjnych miar jakości. Nie ma odpowiedzi na pytania:

jakie błędy metoda ma redukować,

jak je liczysz,

po czym odróżniasz poprawę od tylko większej ilości papieru,

kiedy dokumentacja pomaga, a kiedy jest już kosztem netto,

jak oceniasz jakość decyzji po sesji,

jak wykrywasz, że pętla refleksji produkuje pozorną mądrość zamiast lepszych wyników.

Bez tego to nie jest jeszcze pełna metodologia kontroli jakości. To jest dobrze ułożony system pracy. Różnica jest zasadnicza. 

METHODOLOGY

Drugi problem: dokument myli architekturę procesu z epistemologią procesu. Bardzo dużo mówi o tym, kto ma co czytać, kiedy eskalować, jak przekazywać kontekst, jakie pliki istnieją i jak nie zgubić stanu. Prawie nic nie mówi o tym, jak odróżniać trafne wnioski od elegancko zapisanych błędów. To znaczy: dobrze zarządzasz pamięcią, słabo zarządzasz prawdą. 

METHODOLOGY

Trzeci problem: metodologia jest mocno obudowana językiem wysokiego poziomu — „rekurencja”, „fraktalność”, „cybernetyka drugiego rzędu”, „genomiczny charakter”, „obserwator wchodzi w zakres obserwacji”. Część z tego coś wnosi, ale część pełni funkcję estetyczną, nie operacyjną. Innymi słowy: dokument chwilami brzmi mądrzej, niż jest precyzyjny. To ryzyko, bo przy metodologii ozdobny aparat pojęciowy często maskuje brak warunków decyzyjnych. 

METHODOLOGY

Ukryte założenia, które trzymają tę konstrukcję — i mogą ją rozwalić

Pierwsze ukryte założenie: że rozdzielenie Agent / Developer / Metodolog realnie daje różne jakości myślenia. W praktyce to często będą trzy sesje tego samego typu modelu, z podobnymi uprzedzeniami, podobnym stylem halucynacji i podobnymi ślepymi punktami. Zmieniasz kontekst, ale niekoniecznie zmieniasz aparat poznawczy. To znaczy, że ta „hierarchia instancji” może dawać pozór niezależnej kontroli, choć faktycznie to nadal ten sam rodzaj błędu, tylko inaczej opakowany. 

METHODOLOGY

Drugie założenie: że użytkownik jako mediator i gatekeeper wystarczy do kontroli eskalacji. Nie wystarczy, jeśli użytkownik nie rozumie, dlaczego coś jest sygnałem architektonicznym albo metodologicznym. Wtedy kontrola jest formalnie po stronie człowieka, ale poznawczo nadal po stronie modelu. To jest słaby punkt, bo mechanizm zatwierdzania może być pustą procedurą. 

METHODOLOGY

Trzecie założenie: że ochrona wytycznych przed samodzielną edycją przez agenta zwiększa bezpieczeństwo procesu. Zwykle tak, ale tylko do pewnego momentu. Gdy każdy sensowny update wymaga osobnej zgody, system zaczyna być stabilny kosztem adaptacyjności. To dobra zasada ochronna, ale bez wyjątków i progów istotności może robić z procesu wąskie gardło. 

METHODOLOGY

Czwarte założenie: że „zasada otwartych wątków” zapobiega gubieniu spraw. Owszem, ale równie dobrze może powodować chroniczne puchnięcie backlogu i zamianę każdego planu w magazyn nieskończonych zobowiązań. Tu brakuje reguły wygaszania, priorytetyzacji i kasowania wątków, które straciły sens. Sama zasada pamiętania wszystkiego nie jest jeszcze zasadą zarządzania zakresem. 

METHODOLOGY

Piąte założenie: że organiczny, projektowo-specyficzny format progress logu jest zaletą. Bywa. Ale koszt jest oczywisty: spada porównywalność, przenaszalność i szybkość wejścia nowej instancji. Zbyt organiczny format łatwo staje się prywatnym dialektem projektu. 

METHODOLOGY

Największe ryzyka błędu

Największe ryzyko to meta-spirala bez walidacji. Dokument bardzo promuje refleksję nad procesem i szybkie zapisywanie obserwacji o tym, co poprawić w metodzie lub wytycznych. To może być świetne. Ale bez twardego etapu sprawdzenia, czy dana poprawka faktycznie zwiększyła jakość wyników, kończysz z metodologią, która świetnie obserwuje samą siebie, a słabo bada skutki własnych zmian. To klasyczne ryzyko systemów autoreferencyjnych. 

METHODOLOGY

Drugie ryzyko to nadprodukcja dokumentacji. Sam dokument ostrzega przed nadmiarem dokumentów przy małych zadaniach, co jest trafne. Problem w tym, że reszta metodologii naturalnie pcha w stronę dokładania kolejnych warstw: routing, role, handoffy, progress logi, chronione wytyczne, architektura, PRD, TECHSTACK, refleksja. Bez bardzo twardych progów użycia ten system będzie miał własną tendencję do biurokratyzacji. 

METHODOLOGY

Trzecie ryzyko to fetyszyzacja spójności procesu kosztem celu projektu. Dokument kilka razy sugeruje, że projekt jest odzwierciedleniem metody. To brzmi atrakcyjnie, ale bywa zdradliwe. Projekt ma przede wszystkim rozwiązywać problem. Jeśli metoda staje się głównym obiektem troski, łatwo zacząć optymalizować proces dla niego samego. 

METHODOLOGY

Czwarte ryzyko to brak mechanizmu rozstrzygania konfliktów między poziomami. Jest hierarchia eskalacji, ale nie ma reguł, co zrobić, gdy np. Developer chce jednej rzeczy, Metodolog innej, a Agent widzi koszt wykonawczy jeszcze inny. Kto wygrywa i według jakiego kryterium? Dokument zakłada uporządkowany przepływ w górę, ale nie opisuje powrotu decyzji w dół ani arbitrażu konfliktu. 

METHODOLOGY

Co jest logicznie niespójne albo niedomknięte

Mówisz, że metodologia nie jest zbiorem reguł technicznych, ale potem dokument zawiera sporo bardzo konkretnych reguł operacyjnych: co ma czytać agent, co jest warstwą chronioną, jak ma wyglądać routing, kiedy istnieje ARCHITECTURE, jak ma działać handoff, że każdy plan ma zawierać wszystkie otwarte wątki. To nie jest wada sama w sobie. Problem jest taki, że dokument deklaruje wyższy poziom abstrakcji, a realnie miesza poziom filozofii i procedury. To osłabia precyzję, bo nie wiadomo, co jest zasadą konstytutywną, a co tylko obecną praktyką. 

METHODOLOGY

Druga niespójność: podkreślasz rozdział poziomów i zakaz ich mieszania, ale jednocześnie cały sens metodologii polega na przenikaniu obserwacji między poziomami przez handoffy i meta-obserwację. W praktyce poziomy są więc nie tyle rozdzielone, co silnie sprzężone i proceduralnie filtrowane. To trzeba nazwać uczciwiej. Dziś dokument obiecuje separację, a opisuje kontrolowane przenikanie. 

METHODOLOGY

Trzecia rzecz: „fraktalność” jest tu bardziej metaforą niż zasadą. Żeby to była realna zasada metodologiczna, musiałbyś pokazać, które dokładnie elementy mapują się 1:1 między skalami i jakie są warunki wyjątku. Obecnie to jest intuicja o samopodobieństwie procesu, nie ścisła reguła. 

METHODOLOGY

Czy da się z tego wyciągać sensowne wnioski?

Tak, ale trzeba uczciwie powiedzieć: da się wyciągać sensowne wnioski o organizacji pracy z LLM, dużo słabiej o jakości poznawczej samych rezultatów. Ta metodologia może dobrze odpowiedzieć na pytania:

jak nie gubić stanu projektu,

jak rozdzielić wykonanie od poprawiania instrukcji,

jak zamieniać błędy sesji w ulepszenia procesu,

jak chronić zasady działania przed przypadkowym dryfem.

Znacznie gorzej odpowiada na pytania:

czy wynik jest prawdziwy,

czy rozwiązanie jest lepsze od alternatyw,

czy poprawka do promptu realnie zmniejszyła błąd,

czy dokumentacja zwiększyła skuteczność, a nie tylko poczucie kontroli.

Czyli: do zarządzania współpracą człowiek–LLM to już jest coś. Do oceny trafności i niezawodności pracy — jeszcze nie. 

METHODOLOGY

Co bym poprawił, żeby to stało się mocniejsze

Po pierwsze, dodaj warstwę walidacyjną, nie tylko refleksyjną. Każda zmiana w metodzie albo wytycznych powinna mieć minimalny test skuteczności. Nie filozoficzny komentarz, tylko prosty zapis: jaki problem miała rozwiązać, po czym poznamy poprawę, po ilu próbach oceniamy, czy działa. Bez tego meta-obserwacja będzie produkować anegdoty, nie wiedzę.

Po drugie, wprowadź metryki procesu. Proste, ale twarde. Na przykład:
liczba korekt promptu do uzyskania akceptowalnego wyniku, odsetek zadań wracających do poprawy, liczba błędów wykrytych po wdrożeniu, czas wejścia nowej sesji w stan projektu, odsetek otwartych wątków starszych niż określony próg. Wtedy wreszcie będziesz widział, czy metoda realnie działa.

Po trzecie, rozdziel dokument na trzy warstwy:

zasady konstytutywne,

procedury domyślne,

heurystyki i metafory.
Teraz to jest przemieszane. Po rozdzieleniu będzie jasne, co jest nienegocjowalne, co tylko praktyczne, a co służy orientacji myślowej.

Po czwarte, zdefiniuj progi użycia. Kiedy naprawdę uruchamiasz poziom Developera, kiedy Metodologa, kiedy wystarcza zwykły progress log, kiedy trzeba PRD, a kiedy nie. Dziś skala jest opisana dość miękko. To zostawia zbyt dużo uznaniowości.

Po piąte, dodaj regułę zamykania otwartych wątków. Nie tylko ich przenoszenia. Każdy otwarty wątek powinien mieć status, właściciela decyzji i warunek zamknięcia albo porzucenia. Inaczej system będzie kumulował pozorną odpowiedzialność.

Po szóste, dopisz mechanizm kontr-opinii. Jeśli „Metodolog” to nadal ten sam typ modelu, potrzebujesz przynajmniej jednej procedury, która wprowadza kontrolowany opór: alternatywną hipotezę, próbę falsyfikacji, checklistę „jak ta rekomendacja może być błędna?”. Bez tego hierarchia ról może być tylko teatrem niezależności.

Po siódme, ogranicz język wzniosły tam, gdzie niczego nie operacjonalizuje. Zostaw go tam, gdzie naprawdę porządkuje myślenie. Resztę zamień na definicje, warunki i przykłady decyzji. Dokument od razu stanie się mocniejszy.

Najkrótszy uczciwy werdykt

To jest dobra metodologia utrzymywania ciągłości i dyscypliny pracy z LLM.
To jest średnia metodologia uczenia się na błędach.
To jest słaba metodologia kontroli trafności i jakości wniosków, bo nie ma jeszcze porządnej walidacji, miar i kryteriów rozstrzygania. 

METHODOLOGY

Rdzeń, który trzyma ten projekt, to: zewnętrzna pamięć, separacja ról, jawne handoffy, ochrona wytycznych.
Rdzeń, który go dziś rozwala, to: brak metryk, brak testów skuteczności zmian metodologii, za dużo języka autorefleksyjnego względem ilości reguł decyzyjnych. 

METHODOLOGY

Jeśli chcesz, mogę w następnym kroku zrobić drugą warstwę: przerobić ten dokument na ostrzejszą wersję metodologiczną, punkt po punkcie, bez zmiany jego ducha.

## 4
Przejrzę to jak protokół metodologiczny, nie manifest. Interesuje mnie tu przede wszystkim: co to realnie stabilizuje, czego nie mierzy, jakie ma ukryte koszty i jakie wnioski wolno z tego wyciągnąć.

Thought for 1m 15s

To jest sensowna metodologia operacyjna, ale nie jest jeszcze mocną metodologią poznawczą. Jako sposób organizacji pracy z LLM-em ma realną wartość. Jako podstawa do mocniejszych twierdzeń o „tym, co działa”, „dlaczego działa” i „jakie zasady są ogólnie lepsze” — na razie jest zbyt słaba. Dokument jest dobrze przemyślany na poziomie architektury procesu, ale słabo domknięty na poziomie dowodu, pomiaru i falsyfikacji. 

METHODOLOGY

Najpierw sedno: to nie jest metodologia badawcza sensu stricto, tylko normatywny protokół pracy z elementami autorefleksji. To ważne rozróżnienie. Dokument mówi głównie, jak powinno się pracować, a dużo mniej o tym, jak sprawdzać, czy ten sposób pracy rzeczywiście daje lepsze wyniki. Gdy piszesz, że metodologia „powstała empirycznie — przez obserwację własnej pracy i systematyczne wyciąganie z niej wniosków”, to brzmi dobrze, ale metodologicznie oznacza głównie introspekcję praktyka, nie jeszcze solidne rozpoznanie empiryczne. Nie ma tu jednostki analizy, procedury zbierania danych, kryteriów porównania ani progów sukcesu/porażki. 

METHODOLOGY

Najmocniejsza część tego dokumentu dotyczy ciągłości pracy i kontroli stanu projektu. Zewnętrzna pamięć w postaci dokumentacji, progress logu, handoffów i rozdzielenia poziomów działania to bardzo sensowna odpowiedź na realny problem pracy z LLM-ami: utratę kontekstu, nieciągłość sesji, dryf instrukcji i mieszanie ról. To jest praktycznie trafne. Gdy piszesz, że „tożsamość projektu siedzi w strukturze”, a agent jest tylko nośnikiem chwilowego wykonania, to jest to jedno z najmocniejszych zdań całego dokumentu. Ono dobrze rozpoznaje naturę pracy z modelami językowymi. 

METHODOLOGY

Druga mocna rzecz to separacja ról: Agent–Developer–Metodolog. To nie jest ozdobnik, tylko mechanizm ograniczania konfuzji między wykonywaniem, projektowaniem reguł i oceną samej metody. W praktyce to może zmniejszać ryzyko, że model jednocześnie wykonuje zadanie, przepisuje sobie reguły i sam siebie uzasadnia. Z punktu widzenia kontroli procesu to dobry ruch. Tak samo sensowna jest „warstwa chroniona” dla wytycznych oraz wymóg jawnej zgody użytkownika na ich zmianę. To wzmacnia nadzór i ogranicza samowolną rekonfigurację systemu przez model. 

METHODOLOGY

Trzecia mocna rzecz to pętla meta-obserwacji. Sam pomysł, by błędy pierwszego podejścia, poprawki promptu i powtarzalne symptomy traktować jako materiał do ulepszania reguł, jest metodologicznie wartościowy. To jest realny mechanizm uczenia procesu, a nie tylko wykonywania zadań. Problem w tym, że ta pętla jest obecnie zbyt autoreferencyjna: opiera się niemal wyłącznie na obserwacji samego procesu przez uczestnika procesu. To daje materiał do ulepszania praktyki, ale jeszcze nie daje mocnej podstawy do twierdzeń o skuteczności tej praktyki. 

METHODOLOGY

I tu zaczynają się zasadnicze słabości.

Najpoważniejsza wada: brak operacjonalizacji sukcesu. Dokument bardzo dobrze opisuje strukturę, ale prawie wcale nie definiuje mierzalnych rezultatów. Nie wiadomo, po czym poznasz, że metodologia zadziałała lepiej niż alternatywa. Mniej błędów? Mniej reworku? Krótszy czas rekonstrukcji stanu po resecie sesji? Lepsza trafność implementacji względem wymagań? Mniej halucynacji? Mniej zmian wytycznych w czasie? Bez tego nie masz metodologii, którą można oceniać porównawczo; masz raczej rozsądny system roboczy. 

METHODOLOGY

Druga poważna wada: nadmiar języka wysokiego poziomu przy niedoborze procedur niskiego poziomu. „Cybernetyka drugiego rzędu”, „adaptacja refleksyjna”, „fraktalność”, „rekurencja”, „projekt jako odzwierciedlenie metody” — to wszystko tworzy ramę interpretacyjną, ale miejscami bardziej podnosi rangę dokumentu, niż zwiększa jego testowalność. Krótko mówiąc: masz sporo języka teoretyzującego i za mało instrukcji typu „w tej sytuacji rób X, uznaj Y za sygnał, zmierz Z, odrzuć W”. To grozi pseudo-precyzją: dokument brzmi dojrzale, ale nie wszędzie daje się rygorystycznie sprawdzić. 

METHODOLOGY

Trzecia wada: mieszanie trzech porządków w jednym tekście. Ten dokument jest jednocześnie:

esejem o naturze współpracy człowiek–LLM,

instrukcją dla agenta,

procedurą zarządzania projektem.
To da się czytać, ale trudno audytować. Metodologicznie lepiej byłoby rozdzielić: osobno „uzasadnienie”, osobno „protokół”, osobno „instrukcja wykonawcza”. Teraz część tez ma status filozoficzny, część normatywny, a część proceduralny — i nie zawsze wiadomo, co jest założeniem, co regułą, a co tylko interpretacją. 

METHODOLOGY

Czwarta wada: hierarchia eskalacji jest elegancka, ale może być zbyt sztywna. Założenie, że sygnał idzie tylko w górę, a role nie powinny być mieszane, porządkuje system, ale w praktyce grozi kosztami koordynacyjnymi. W realnej pracy wiele problemów jest hybrydowych: częściowo wykonawczych, częściowo architektonicznych, częściowo metodologicznych. Jeśli będziesz zbyt konsekwentnie pilnował czystości poziomów, możesz zwiększyć tarcie, opóźniać decyzje i produkować nadmiar handoffów. To dobry mechanizm dla złożonych projektów, ale dla średnich i szybkich zadań może być przerostem formalizmu nad zyskiem. 

METHODOLOGY

Piąta wada: użytkownik jako gatekeeper jest założeniem politycznie sensownym, ale epistemicznie słabym. Piszesz wprost, że użytkownik „nie musi rozumieć technicznego uzasadnienia”, a model komunikuje się sam ze sobą, użytkownik tylko zatwierdza kierunek. To buduje kontrolę formalną, ale nie gwarantuje kontroli merytorycznej. Innymi słowy: możesz mieć zgodę człowieka bez realnej walidacji sensowności. To jest ryzyko pozornej kontroli. Użytkownik podpisuje decyzję, której nie ma narzędzi naprawdę ocenić. 

METHODOLOGY

Szósta wada: „zasada otwartych wątków” może degenerować się w chroniczne przeciążenie planu. Wymóg, by każdy plan zawierał wszystkie otwarte wątki z poprzednich sesji, brzmi jak ochrona przed gubieniem stanu, ale bez reguł priorytetyzacji szybko zamieni się w listę długu, która obciąża uwagę bardziej, niż pomaga. W praktyce potrzebujesz nie tylko „pełności”, ale też mechanizmu odcinania, archiwizacji i hierarchizacji. Inaczej dokumentacja zacznie konserwować chaos zamiast mu zapobiegać. 

METHODOLOGY

Siódma wada: brak warstwy walidacji zewnętrznej. Cała metodologia skupia się na dokumentacji, ciągłości, handoffach i autorefleksji, ale prawie nie mówi o tym, jak sprawdzać wynik wobec rzeczywistości zewnętrznej: testów, benchmarków, review przez drugiego człowieka, porównania z baseline’em, miar jakości. To fundamentalne. Bo LLM może być świetnie „zarządzany”, a mimo to produkować rozwiązania przeciętne lub błędne. Dobra metodyka pracy nie zastępuje walidacji rezultatu. 

METHODOLOGY

Ósma wada: zbyt szerokie roszczenie „fraktalności”. To atrakcyjna metafora, ale metodologicznie podejrzana, jeśli nie pokażesz granic jej stosowalności. Nie każda struktura skaluje się sensownie od całego projektu do pojedynczego zadania. To, co działa jako rama dla wielosesyjnego projektu software’owego, niekoniecznie działa dla incydentalnego bugfixu, analizy tekstu czy eksploracji badawczej. Tu potrzebujesz nie tylko zasady skalowania, ale też zasady wyjątków. 

METHODOLOGY

Dziewiąta wada: brak kosztorysu metodologii. Dokument zakłada, że dokumentacja, routing, handoffy i refleksja są warte swojej ceny, ale nigdzie nie próbujesz oszacować kosztu tej warstwy. To błąd. Każda metodologia ma koszt poznawczy, czasowy i kontekstowy. Jeżeli go nie liczysz, łatwo wpaść w pułapkę: proces staje się coraz bardziej uporządkowany, ale niekoniecznie bardziej produktywny. Dokument sam zauważa koszt nadmiarowej dokumentacji, ale nie daje narzędzi, by ten koszt monitorować. 

METHODOLOGY

Dziesiąta wada: brak precyzyjnych progów decyzyjnych. Masz sformułowania typu „gdy zadanie rośnie”, „większe zadania”, „coś istotnego dla Developera/Metodologa”, „okolice ~10 sesji”. To za mało, jeśli chcesz, żeby metodologia była egzekwowalna i porównywalna. Potrzebujesz progów albo przynajmniej przykładów granicznych. Inaczej działasz na intuicji, tylko ubranej w formalny język. 

METHODOLOGY

Teraz najważniejsze pytanie: jakie wnioski ta metodologia uniesie, a jakich nie uniesie?

Uniesie wnioski skromne i lokalne. Na przykład:

że zewnętrzna dokumentacja poprawia ciągłość pracy między sesjami,

że rozdzielenie ról zmniejsza mieszanie wykonania z regułami,

że progress log i handoffy ułatwiają restart pracy po utracie kontekstu,

że jawna refleksja nad błędami pomaga udoskonalać instrukcje operacyjne.
To są wnioski wiarygodne jako hipotezy praktyczne dla Twojego sposobu pracy. 

METHODOLOGY

Nie uniesie natomiast — w obecnej formie — wniosków mocniejszych. Nie możesz uczciwie twierdzić, że:

to jest ogólnie lepsza metoda pracy z LLM niż inne podejścia,

że druga-rzędowo-cybernetyczna rama jest przyczyną poprawy wyników,

że trzy poziomy działania są optymalne,

że ta metodologia zwiększa jakość produktu, a nie tylko porządkuje proces,

że obserwacje z niej mają większą wartość niż dobrze prowadzona praktyka projektowa bez tej warstwy pojęciowej.
Do takich twierdzeń brakuje porównań, wskaźników i procedury walidacyjnej. 

METHODOLOGY

Mój twardy werdykt jest taki:

Jako metodologia zarządzania współpracą z LLM-em: dobra, miejscami bardzo dobra.
Jako metodologia poznawcza zdolna generować mocniejsze, obronione wnioski: niedomknięta i zbyt introspektywna.

Największa wartość dokumentu nie leży w jego warstwie teoretycznej, tylko w tym, że trafnie rozpoznaje operacyjne problemy pracy z modelami: nieciągłość, dryf, mieszanie ról, potrzebę zewnętrznej pamięci i potrzebę kontrolowanej aktualizacji wytycznych. Największa słabość polega na tym, że próbujesz ubrać praktykę projektową w mocniejszy kostium metodologiczny, niż obecnie wytrzymuje jej aparat dowodowy. 

METHODOLOGY

Gdybym miał to oceniać brutalnie proporcjonalnie:
wartość operacyjna: wysoka,
wartość heurystyczna: średnio-wysoka,
wartość dowodowa: niska do średniej,
ryzyko samoutwierdzania się metody: wysokie,
ryzyko biurokratyzacji procesu: realne,
ryzyko przecenienia własnej refleksji nad obiektywną walidacją: wysokie.

Żeby to naprawdę dojrzało metodologicznie, musisz dobudować cztery rzeczy: minimalne metryki sukcesu, porównanie z baseline’em, reguły wyjątków oraz niezależną walidację efektów. Bez tego masz inteligentny system pracy. Z tym — zaczniesz mieć metodologię, którą da się już nie tylko stosować, ale i bronić.

Jeśli chcesz, w następnym kroku mogę zrobić drugą warstwę recenzji: przerobić ten dokument na wersję metodologicznie twardszą, punkt po punkcie, bez zmiany jego ducha.