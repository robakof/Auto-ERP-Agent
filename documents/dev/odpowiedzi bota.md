Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja
      konfiguracji systemu" && python
      bot/pipeline/nlp_pipeline.py --question "Pokaż 5       
      ostatnich zamówień sprzedaży" --v…)
  ⎿  [SQL]
     SELECT TOP 5
         ID_Zamowienia,
     … +24 lines (ctrl+o to expand)
  ⎿  Shell cwd was reset to
     C:\Users\dcyprowski\Desktop\Automatyzacja
     konfiguracji systemu\bot

● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja
      konfiguracji systemu" && python
      bot/pipeline/nlp_pipeline.py --question "Jakie
      zamówienia ma kontrahent NELMA?" --…)
  ⎿  [SQL]   
     SELECT TOP 200
         ID_Zamowienia,
     … +24 lines (ctrl+o to expand)        
  ⎿  Shell cwd was reset to                         
     C:\Users\dcyprowski\Desktop\Automatyzacja 
     konfiguracji systemu\bot
                                     
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja
      konfiguracji systemu" && python      
      bot/pipeline/nlp_pipeline.py --question "Które
      zamówienia są w trakcie realizacji?…)
  ⎿  [SQL]        
     SELECT TOP 200                  
         ID_Zamowienia,
     … +20 lines (ctrl+o to expand)       
  ⎿  Shell cwd was reset to                                  
     C:\Users\dcyprowski\Desktop\Automatyzacja 
     konfiguracji systemu\bot
                                     
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python
      bot/pipeline/nlp_pipeline.py --question "Jakie         
      rezerwacje są aktywne na magazynie…)                   
  ⎿  [SQL]                                                   
     SELECT TOP 200                                          
         ID_Rezerwacji,                                      
     … +26 lines (ctrl+o to expand)                          
  ⎿  Shell cwd was reset to                                  
     C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot                                
                                                             
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python                        
      bot/pipeline/nlp_pipeline.py --question "Podaj NIP i   
      adres firmy MARCO" --verbose…)                         
  ⎿  [SQL]                                                   
     SELECT TOP 10                                           
         Akronim,                                            
     … +18 lines (ctrl+o to expand)                          
  ⎿  Shell cwd was reset to                                       C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot                                                                                             
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python                        
      bot/pipeline/nlp_pipeline.py --question "Którzy        
      kontrahenci mają blokadę transakcj…)                   
  ⎿  [SQL]                                                   
     SELECT TOP 200                                          
         ID_Kontrahenta,                                     
     … +16 lines (ctrl+o to expand)                          
  ⎿  Shell cwd was reset to                                  
     C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot     
                                                             
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python                        
      bot/pipeline/nlp_pipeline.py --question "Jakie         
      dokumenty są rozliczone z fakturą F…)                  
  ⎿  [SQL]                        
     SELECT TOP 200                                          
         ID_Rozliczenia,                                     
     … +25 lines (ctrl+o to expand)                          
  ⎿  Shell cwd was reset to                                  
     C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot     
                                                             
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python                        
      bot/pipeline/nlp_pipeline.py --question "Ile zamówień  
      złożono w marcu 2026?" --ver…)                         
  ⎿  [SQL]                                                   
     SELECT TOP 50 COUNT(*) AS Liczba_Zamowien               
     FROM AIBI.ZamNag                                        
     … +6 lines (ctrl+o to expand)                           
  ⎿  Shell cwd was reset to                                  
     C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot                                
                                                             
● Bash(cd "C:\Users\dcyprowski\Desktop\Automatyzacja         
      konfiguracji systemu" && python                        
      bot/pipeline/nlp_pipeline.py --question "Pokaż         
      kontrahentów z grupy 01.KLIENCI" --…)                  
  ⎿  [SQL]                                                   
     SELECT TOP 200                                          
         ID_Kontrahenta,                                     
     … +28 lines (ctrl+o to expand)                          
  ⎿  Shell cwd was reset to                                       C:\Users\dcyprowski\Desktop\Automatyzacja               
     konfiguracji systemu\bot                                                                                             
● ---                                                        
  1. Pokaż 5 ostatnich zamówień sprzedaży                    
                                                               ┌─────┬───────────┬───────┬─────────┬────────┬───────┐     
  │     │  Numer    │ Kontr │         │ Data   │ Data  │     
  │ ID  │ dokumentu │ ahent │  Stan   │ wystaw │ reali │     
  │     │           │       │         │ ienia  │ zacji │     
  ├─────┼───────────┼───────┼─────────┼────────┼───────┤
  │ 143 │ ZS-13/03/ │ -     │ Zrealiz │ 2026-0 │ 2026- │     
  │ 47  │ 26/OTO    │       │ owane   │ 3-10   │ 03-10 │     
  ├─────┼───────────┼───────┼─────────┼────────┼───────┤
  │     │           │ NELMA │         │        │       │
  │ 143 │ ZS-31/03/ │  Sp.  │ Zrealiz │ 2026-0 │ 2026- │     
  │ 48  │ 26/PH_2   │ z     │ owane   │ 3-10   │ 03-13 │     
  │     │           │ o.o.  │         │        │       │     
  ├─────┼───────────┼───────┼─────────┼────────┼───────┤     
  │     │           │ REMIL │         │        │       │     
  │ 143 │ ZS-15/03/ │ A Sp. │ Potwier │ 2026-0 │ 2026- │     
  │ 49  │ 26/PH_3   │  z    │ dzone   │ 3-10   │ 03-12 │     
  │     │           │ o.o.  │         │        │       │     
  ├─────┼───────────┼───────┼─────────┼────────┼───────┤     
  │     │           │ COVAR │         │        │       │     
  │ 143 │ ZS-12/03/ │ DIA   │ Potwier │ 2026-0 │ 2026- │     
  │ 50  │ 26/PH_5   │ Sp. z │ dzone   │ 3-10   │ 03-10 │     
  │     │           │  o.o. │         │        │       │     
  ├─────┼───────────┼───────┼─────────┼────────┼───────┤     
  │ 143 │ ZS-32/03/ │ MARCO │ Potwier │ 2026-0 │ 2026- │     
  │ 51  │ 26/PH_2   │       │ dzone   │ 3-10   │ 03-13 │     
  └─────┴───────────┴───────┴─────────┴────────┴───────┘     

  Podsumowanie: 2 zrealizowane, 3 potwierdzone. Wszystkie    
  wystawione 10 marca 2026. Waluta: PLN.

  ---
  2. Jakie zamówienia ma kontrahent NELMA?

  Kontrahent NELMA ma 58 zamówień (typ ZS).

  - Zrealizowane: 30
  - Zamknięte w realizacji: 20
  - W realizacji: 1 (ZS-9/02/26/PH_2 z 2026-02-08)

  Główne magazyny: Buszewo (WMS), Piaskowo, Otorowo. Waluta: 
  PLN. Okres: czerwiec 2023 – marzec 2026.

  ---
  3. Które zamówienia są w trakcie realizacji?

  Nie znaleziono zamówień o statusie "W realizacji".

  ---
  4. Jakie rezerwacje są aktywne na magazynie głównym?       

  Na magazynie Buszewo (WMS) aktywnych jest 200 rezerwacji   
  (próbka z zapytania).

  Główne kategorie towarów: świece i wkłady LED, wkłady      
  zniczowe, figurki wielkanocne, zapałki, produkty zapachowe.  Główni odbiorcy: MARABELLA, VENTRUS, REMILA, MARCO, HARDY, 
  COVARDIA i inne.
  Data rezerwacji: 9–10 marca 2026.

  ---
  5. Podaj NIP i adres firmy MARCO

  - NIP: 5561871628
  - Adres: ul. Przypadek 9, 88-100 Inowrocław

  ---
  6. Którzy kontrahenci mają blokadę transakcji?

  Nie znaleziono kontrahentów z aktywną blokadą transakcji.  

  ---
  7. Jakie dokumenty są rozliczone z fakturą FS-1/06/23/FRA? 

  Faktura FS-1/06/23/FRA jest rozliczona z zapisem
  kasowym/bankowym:

  - Kwota rozliczenia: 28,80 PLN
  - Data rozliczenia: 2023-06-01
  - Rozliczenie wykonane przez system synchronizacji POS     
  Franowo.

  ---
  8. Ile zamówień złożono w marcu 2026?

  W marcu 2026 złożono 109 zamówień.

  ---
  9. Pokaż kontrahentów z grupy 01.KLIENCI

  W systemie jest 200+ kontrahentów z grupy 01.KLIENCI,      
  podzielonych na podgrupy:

  - 01.DETAL, 02.DETAL+, 03.HURT, 04.CENTRALA
  - 05.BRICO, 06.CHATA POLSKA, 07.INTER, 08.PSB, 09.FRANOWO  

  Największa podgrupa: 09.FRANOWO. Kontrahenci aktywni i     
  zarchiwizowani z całej Polski.

  ---
  10. Jaka jest pogoda w Warszawie?

  To pytanie wykracza poza zakres danych do których mam      
  dostęp.