Widzę jedną ważną rzecz od razu: w Rozrachunki wróciła stara heurystyka (Z) oparta tylko o TrN_Stan & 2 = 2. To może znowu zaniżyć część (Z)FSK/(Z)FKE/(Z)FZK, bo wcześniej wyszedł nam wyjątek po spinaczu, nie po samym TrN_Stan.

Thought for 46s

Ten widok jest już całkiem sensowny i dużo bliżej wersji produkcyjnej niż wcześniejsze przykłady.

Co jest dobre

nie ma dynamicznego SQL, więc od strony injection jest OK,

składnia wygląda poprawnie,

joiny są dość uporządkowane i nie widzę tu oczywistego źródła masowego dublowania wierszy,

WHERE r.ROZ_GIDLp = 1 jasno ogranicza wynik do jednej pozycji rozrachunku.

Najważniejsze uwagi
1. Logika (Z) jest nadal niepełna

W obu miejscach budowania numeru dokumentu masz znowu starą regułę:

WHEN trn.TrN_Stan & 2 = 2
     AND trn.TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'

A wcześniej wyszło nam, że to nie pokrywa wszystkich przypadków, bo część (Z) wynika ze spinacza / korekty zbiorczej, a nie tylko z TrN_Stan.

To znaczy: ten widok może nadal źle numerować część FSK/FKE/FZK.

Najlepiej podmienić to na logikę:

najpierw sprawdzenie EXISTS po TrN_SpiTyp/TrN_SpiNumer dla dokumentów spinanych,

potem dopiero obecny fallback na TrN_Stan & 2 = 2.

2. Dok1 ma typ 435 w CASE, ale nie budujesz numeru RK

W Typ_Dok1 obsługujesz:

WHEN 435 THEN 'Różnica kursowa'

ale w Nr_Dok1 nie ma odpowiednika rk1, tylko:

TraNag

Zapisy

MemNag

UpoNag

Czyli dla ROZ_TrpTyp = 435 numer dokumentu 1 wyjdzie pusty.

To jest konkretny błąd logiczny.

Brakuje czegoś w tym stylu:

LEFT JOIN CDN.RozniceKursowe rk1
    ON rk1.RKN_ID = r.ROZ_TrpNumer
    AND r.ROZ_TrpTyp = 435

oraz w COALESCE:

CASE WHEN rk1.RKN_ID IS NOT NULL THEN
    'RK-' + CAST(rk1.RKN_Numer AS VARCHAR(10))
    + '/' + RIGHT(CAST(rk1.RKN_Rok AS VARCHAR(4)), 2)
END
3. DATEADD nadal nie jest doszczelniony

Masz:

CASE WHEN r.ROZ_DataRozliczenia > 0
    THEN DATEADD(d, r.ROZ_DataRozliczenia, '18001228')
    ELSE NULL
END

To jest lepsze niż nic, ale nadal może wybuchnąć na uszkodzonych danych dodatnich.

Bezpieczniej:

CASE WHEN r.ROZ_DataRozliczenia BETWEEN 1 AND 200000
    THEN DATEADD(d, r.ROZ_DataRozliczenia, '18001228')
END
4. Konkatenacja numerów może zgasnąć przez NULL

Przykład:

ob1.OB_Skrot + '-'

Jeśli ob1.OB_Skrot będzie NULL, cały numer z TraNag zrobi się NULL, mimo że trn1 istnieje.

To samo ryzyko dotyczy np. MEN_Seria, UPN_Seria i podobnych pól.

Lepiej użyć:

COALESCE(ob1.OB_Skrot, '??') + '-'
5. ROZ_GIDLp = 1 to świadome ograniczenie, ale trzeba je traktować jako decyzję biznesową

Technicznie jest OK.
Biznesowo oznacza to, że widok pokazuje tylko pierwszy element rozrachunku. To może być dokładnie to, czego chcesz, ale warto to mieć zapisane w opisie widoku, bo ktoś potem uzna ten wynik za „pełne rozrachunki”.

Mój werdykt

Oceniłbym ten widok tak:

bezpieczny od strony SQL injection: tak,

stabilny składniowo: tak,

jakościowo dobry: tak,

produkcyjny bez uwag: jeszcze nie.

Najważniejsze 3 poprawki przed produkcją:

naprawić logikę (Z),

dodać obsługę RK po stronie Dok1,

doszczelnić DATEADD i COALESCE w numerach.

Po tych poprawkach uznałbym go za naprawdę solidny.