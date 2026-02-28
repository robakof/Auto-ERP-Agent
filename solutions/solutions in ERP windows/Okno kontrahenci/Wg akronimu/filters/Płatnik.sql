@PAR ?@S20|Płatnik|&Płatnik:REG= @? PAR@

Knt_GidNumer IN (Select kg.Knt_gidnumer
from cdn.KntKarty kg
JOIN cdn.KntKarty p ON p.Knt_GIDNumer = kg.Knt_KnPNumer
Where p.Knt_akronim LIKE '%' + ??Płatnik + '%')