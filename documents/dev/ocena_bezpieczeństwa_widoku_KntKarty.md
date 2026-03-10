Przejrzałem to pod trzema kątami: bezpieczeństwo, stabilność wykonania i ryzyko błędnych danych. Największe ryzyka nie są „hak erskie”, tylko operacyjne: rekurencja i możliwe duplikowanie wierszy.

Mam werdykt: od strony SQL injection ten widok jest w porządku, ale nie nazwałbym go w pełni bezpiecznym produkcyjnie bez kilku poprawek. Najgroźniejsze są: możliwe zapętlenie/awaria CTE, duplikowanie kontrahentów przez grupy oraz bardzo szeroka ekspozycja danych wrażliwych.

Thought for 1m 27s

Nie w pełni.

Od strony SQL injection / wykonywania obcego kodu ten widok jest zasadniczo bezpieczny, bo:

nie ma dynamicznego SQL,

nie przyjmuje parametrów od użytkownika,

to statyczny VIEW.

Ale od strony bezpieczeństwa danych i stabilności produkcyjnej widzę kilka istotnych ryzyk.

Co jest OK

Najważniejsze: nie widzę tu klasycznej luki typu injection.

Co jest ryzykowne
1. Ekspozycja danych wrażliwych

Widok wystawia bardzo dużo danych, w tym:

PESEL

NIP

Nr_Rachunku, NRB

Email

Dokument_Tozsamosci

Numer_Karty_Platniczej

To jest największe ryzyko. Jeżeli ten widok ma być dostępny szerzej w BI, to nie jest bezpieczny w sensie kontroli dostępu. Lepiej zrobić:

widok “publiczny” bez danych wrażliwych,

osobny widok “wrażliwy” tylko dla wybranych ról.

2. Rekurencyjny CTE może się wysypać

Sciezka_Grup jest rekurencyjny. Jeśli w CDN.KntGrupyDom pojawi się:

cykl w drzewie,

albo głębokość > 100,

to zapytanie może zakończyć się błędem. W widoku nie ustawisz OPTION (MAXRECURSION ...), więc to nie jest w pełni odporne operacyjnie.

To jest realne ryzyko.

3. Możesz duplikować kontrahentów

Ten join:

LEFT JOIN CDN.KntGrupyDom kgd
    ON kgd.KGD_GIDNumer = k.Knt_GIDNumer
    AND kgd.KGD_GIDTyp = 32

wygląda jak relacja potencjalnie 1:N. Jeśli kontrahent należy do wielu grup, dostaniesz wiele wierszy dla jednego Knt_GIDNumer.

Jeśli oczekujesz 1 wiersza na kontrahenta, to ten widok nie jest bezpieczny biznesowo, bo może psuć agregacje w BI.

4. Część joinów może być zbyt słaba

W Comarch często logiczny klucz to nie samo GIDNumer, tylko para typu (GIDTyp, GIDNumer).

Na przykład tu:

LEFT JOIN CDN.KntAdresy a
    ON a.KnA_GIDNumer = k.Knt_KnANumer

jeśli KnA_GIDNumer nie jest globalnie unikalny, możesz połączyć z nie tym rekordem. To trzeba zweryfikować w modelu danych. Ta sama uwaga dotyczy każdego miejsca, gdzie łączysz tylko po numerze, a nie po pełnym kluczu logicznym.

5. Cicha utrata danych w ścieżce grup

Tu:

CAST(... AS NVARCHAR(2000)) AS Sciezka

ścieżka może zostać obcięta, jeśli będzie dłuższa niż 2000 znaków. To nie jest luka bezpieczeństwa, ale jest ryzykiem jakości danych.

6. Możliwe błędy na DATEADD

Masz sporo konstrukcji typu:

CASE WHEN k.Knt_VatDataRejestracji > 0
     THEN DATEADD(d, k.Knt_VatDataRejestracji, '18001228') END

Jeśli dane źródłowe będą uszkodzone albo sentinel wyjdzie poza sensowny zakres, DATEADD może rzucić błędem. Dla Knt_EFaVatDataDo to uwzględniłeś, ale dla innych pól już nie.

Mój werdykt

Jeśli pytanie brzmi: czy ten kod jest bezpieczny przed SQL injection — tak.

Jeśli pytanie brzmi: czy bezpiecznie puściłbym go na produkcję i dał do BI — jeszcze nie.

Co bym poprawił przed produkcją

Najpierw:

usunąć albo zamaskować pola wrażliwe,

potwierdzić, czy widok ma zwracać 1 wiersz na kontrahenta,

zweryfikować joiny po pełnym kluczu logicznym,

zabezpieczyć logikę rekurencji,

dodać WITH SCHEMABINDING, jeśli architektura na to pozwala.

Najbardziej krytyczne są punkty 1, 2 i 4.

Mogę Ci od razu przerobić ten widok na wersję „bezpieczniejszą produkcyjnie” z komentarzami, co i dlaczego zmieniłem.