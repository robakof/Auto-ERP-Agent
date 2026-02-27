Twr_GIDNumer in (
	select t.Twr_GIDNumer
	from cdn.TwrKarty t with(nolock)
	JOIN cdn.TwrKody tk with(nolock)ON Twr_GIDNumer = TwK_TwrNumer AND TwK_Jm <> t.Twr_Jm
	LEFT JOIN cdn.TwrJM jm with(nolock)ON TwK_TwrNumer = TwJ_TwrNumer AND Twk_jm = TwJ_JmZ
	WHERE TwK_Kod IS NOT NULL AND TwJ_TwrTyp IS NULL
)
