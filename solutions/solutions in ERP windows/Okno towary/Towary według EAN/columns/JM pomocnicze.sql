SELECT
    CAST(jm_opak.TwJ_PrzeliczL    AS BIGINT) [opak.],
    CAST(jm_karton.TwJ_PrzeliczL  AS BIGINT) [karton],
    CAST(jm_warstwa.TwJ_PrzeliczL AS BIGINT) [warstwa],
    CAST(jm_paleta.TwJ_PrzeliczL  AS BIGINT) [paleta]
FROM cdn.TwrKarty
LEFT JOIN cdn.TwrJM jm_opak
    ON jm_opak.TwJ_TwrNumer = Twr_GIDNumer AND jm_opak.TwJ_TwrTyp = Twr_GIDTyp
    AND jm_opak.TwJ_JmZ = 'opak.'
LEFT JOIN cdn.TwrJM jm_karton
    ON jm_karton.TwJ_TwrNumer = Twr_GIDNumer AND jm_karton.TwJ_TwrTyp = Twr_GIDTyp
    AND jm_karton.TwJ_JmZ = 'karton'
LEFT JOIN cdn.TwrJM jm_warstwa
    ON jm_warstwa.TwJ_TwrNumer = Twr_GIDNumer AND jm_warstwa.TwJ_TwrTyp = Twr_GIDTyp
    AND jm_warstwa.TwJ_JmZ IN ('warstwa', 'warsta')
LEFT JOIN cdn.TwrJM jm_paleta
    ON jm_paleta.TwJ_TwrNumer = Twr_GIDNumer AND jm_paleta.TwJ_TwrTyp = Twr_GIDTyp
    AND jm_paleta.TwJ_JmZ = 'paleta'
WHERE {filtrsql}