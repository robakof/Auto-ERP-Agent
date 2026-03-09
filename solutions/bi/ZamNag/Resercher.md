Sprawdzę oficjalne materiały Comarch ERP XL i opisy schematu bazy, a potem zestawię to z obserwowanymi wartościami bitowymi z CDN.ZamNag.ZaN_DokZwiazane. Zależy mi na źródle, które wprost mapuje bity albo przynajmniej pozwala to wiarygodnie odtworzyć.

Mam na razie tylko słaby trop z oficjalnej bazy wiedzy: potwierdza ona samą tabelę CDN.ZamNag, ale nie pokazuje opisu tego pola. Szukam teraz bardziej „słownikowych” materiałów Comarcha: dokumentacji tabel, zmian technicznych i ewentualnych PDF/CHM ze schematem bazy.

Nie mam jeszcze oficjalnego źródła, które wprost rozpisuje maskę bitową ZaN_DokZwiazane. Mam za to kilka oficjalnych elementów układanki: jakie zakładki pokazuje „Historia związanych”, jakie typy dokumentów można wygenerować z ZamNag, oraz że powiązania DMS trafiają do cdn.DokZwiazane. Teraz składam to w możliwie wiarygodną mapę bitów i od razu zaznaczę, gdzie kończy się twarde źródło, a zaczyna wniosek.

Thought for 12m 42s

Przejrzałem oficjalną bazę wiedzy Comarch ERP XL/BPM i nie znalazłem publicznie dostępnego dokumentu, który wprost rozpisuje maskę bitową CDN.ZamNag.ZaN_DokZwiazane na konkretne wartości 0x10/0x20/.... Oficjalne materiały pokazują natomiast, że dla zamówień okno Historia związanych jest podzielone na kategorie: dokumenty związane, dokumenty magazynowe, korekty, księgowe oraz dokumenty w obiegu, a z ZamNag mogą powstawać zarówno dokumenty handlowe/związane, jak i magazynowe.

Dodatkowo oficjalna dokumentacja Comarch BPM/DMS potwierdza, że powiązania obiegowe są zapisywane w cdn.dokzwiazane, a w samym oknie Historia związanych występuje zakładka dotycząca obiegu dokumentów. To mocno sugeruje, że ZaN_DokZwiazane nie opisuje pojedynczych typów dokumentów w stylu „jest WZ” / „jest faktura”, tylko raczej obecność kategorii zakładek/powiązań w Historii związanych.

Najbezpieczniejszy wniosek jest więc taki:

to pole jest maską kategorii powiązań, a nie mapą 1 bit = 1 konkretny typ dokumentu;

pytanie w rodzaju „czy 0x10 = WZ, a 0x20 = faktura?” — raczej nie;

bardziej prawdopodobne jest „0x10/0x20/0x40/... = są wpisy na odpowiednich zakładkach Historii związanych”.

Najbardziej prawdopodobna rekonstrukcja maski dla ZaN_DokZwiazane jest taka, ale zaznaczam: to już jest wniosek z oficjalnych opisów + Twoich wartości, a nie cytat 1:1 z dokumentacji:

0x04 — Dokumenty w obiegu (BPM/DMS)

0x10 — Dokumenty związane

0x20 — Dokumenty magazynowe

0x40 — Korekty

0x80 — Księgowe

Taki układ dobrze pasuje do oficjalnych kategorii zakładek dla zamówień oraz do faktu, że w Twojej próbce pojawiają się kombinacje 36 = 32+4, 48 = 32+16, 96 = 32+64, czyli „bazowa kategoria + dodatkowa kategoria”.

Z Twoich danych wynikałoby wtedy orientacyjnie:

0 — brak powiązań

16 — tylko związane

32 — tylko magazynowe

36 — magazynowe + obieg

48 — związane + magazynowe

96 — magazynowe + korekty

To jest spójne logicznie, ale uczciwie: nie mam oficjalnego, publicznego źródła Comarch, które potwierdza dokładnie tę numerację bitów.

Gdybym miał wskazać jedyną realną niepewność, to jest nią para 0x10 vs 0x20: oficjalne materiały potwierdzają istnienie kategorii Związane i Magazynowe, ale nie znalazłem miejsca, gdzie Comarch przypisuje im jawnie konkretne wartości bitowe. Wszystko inne wskazuje jednak, że pole jest kategoriową maską Historii związanych, a nie słownikiem typu 0x10=WZ, 0x20=FS.

Jeżeli chcesz, przygotuję Ci jeszcze krótki SQL, który na Twojej bazie rozstrzygnie empirycznie 0x10 vs 0x20 na 100%.