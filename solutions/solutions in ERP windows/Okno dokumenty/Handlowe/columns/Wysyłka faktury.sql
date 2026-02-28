select top 1 case 
		when WFP_DataZamkniecia=0 then 'Błąd wysyłki' 
		when WFZ_Akcja = '' then 'zamknięcie ręczne'
		else 'Wysłano' 
	end as [Status wysyłki wydruku]
from cdn.TraNag
join cdn.WF_Procesy on TrN_GIDTyp=WFP_OBITyp and TrN_GIDNumer=WFP_OBINumer
join cdn.WF_Zadania on WFZ_WFPID=WFP_ID
where wfz_status='Wysyłka dokumentu'  and {filtrSQL}