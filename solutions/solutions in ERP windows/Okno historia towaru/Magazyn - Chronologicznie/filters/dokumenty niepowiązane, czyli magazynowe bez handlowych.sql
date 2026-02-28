MaN_TrNLp=127 and 
(    MaN_GIDNumer
    in
    (
    SELECT MaN_GIDNumer FROM CDN.MagNag mn
    left outer join CDN.TraNag tn on tn.TrN_GIDTyp=mn.MaN_ZrdTyp and tn.TrN_GIDNumer=mn.MaN_ZrdNumer
    WHERE tn.TrN_TrNNumer is null OR tn.TrN_TrNNumer=0
    )
    OR 
    MaN_ZrdTyp is null
    OR 
    MaN_ZrdTyp in (0, 960)
)
