@PAR ?@R(SELECT '(wszystkie)' AS KOD,0 AS ID UNION ALL SELECT KnG_Akronim AS KOD,KnG_GIDNumer AS ID FROM CDN.KntGrupy WHERE KnG_GIDTyp=-32 AND KnG_GrONumer>=0 ORDER BY 1)|Grupa|&Grupa:REG=0 @? PAR@
@PAR ?@R(SELECT '(wszyscy)' AS KOD,0 AS ID UNION ALL SELECT Knt_Akronim AS KOD,Knt_GIDNumer AS ID FROM CDN.KntKarty WHERE Knt_Akwizytor=1 ORDER BY 1)|Akwizytor|&Akwizytor:REG=0 @? PAR@
@PAR ?@S20|Platnik|&Płatnik:REG= @? PAR@
@PAR ?@R(SELECT '(wszystkie)' AS KOD,'all' AS ID UNION ALL SELECT 'Tak' AS KOD,'tak' AS ID UNION ALL SELECT 'Nie' AS KOD,'nie' AS ID)|Zgoda|&Zgoda na eFaktury:REG=all @? PAR@

(??Grupa=0 OR Knt_GIDNumer IN (SELECT KnG_GIDNumer FROM CDN.KntGrupy WHERE KnG_GIDTyp=32 AND KnG_GrONumer=??Grupa))
AND (??Akwizytor=0 OR Knt_AkwNumer=??Akwizytor)
AND (??Platnik='' OR Knt_GidNumer IN (SELECT kg.Knt_GIDNumer FROM cdn.KntKarty kg JOIN cdn.KntKarty p ON p.Knt_GIDNumer=kg.Knt_KnPNumer WHERE p.Knt_Akronim LIKE '%'+??Platnik+'%'))
AND (??_QZgoda='all' OR (??_QZgoda='tak' AND Knt_EFaVatAktywne=1) OR (??_QZgoda='nie' AND Knt_EFaVatAktywne=0))