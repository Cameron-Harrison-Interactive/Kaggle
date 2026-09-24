import base64
import hashlib
import importlib.util
import tarfile
import zlib
from pathlib import Path

WORK = Path("/kaggle/working")
if not WORK.exists():
    WORK = Path.cwd()

MAIN_PATH = WORK / "main.py"
ARCHIVE_PATH = WORK / "submission.tar.gz"

# Exact c68 source from the frozen final gate, compressed so the notebook stays readable.
_AGENT_B64_PARTS = [
    "eNrNfWeXokzT8Pf5FTqGB3Tc24h6mbOYUDDvWREBFSUJmMNvfwkGdGZ297qf85zz7tkzo3R1dXV1dcVu5v39PQdF/rFI9FSi5TlN"
    "WdrlTiNfQC1ThmYpiySsFdoismvZQlCEqDAb9ZtEc8ya037TnPpI4H+8vRV1cIKnLCwxESQLQWoNsoUUONoylQTOosxpi6wQE5a+"
    "YpXnhKQOONnrTVViqT5cMhqON06aSYw85xlenlgUQfTIpCAx/MwiryccI8sa6h8WC7rmFUbFzwozhtTokWlpQ8s6PnE9YdWHXX/g"
    "TaVFkDysQBKsZUurQ0q0SDCSTi0v8CzD04SkdmdI2sNwogpuwQq1mkWQKFob9cNggIr1TaEljuFVPDqvSJYm+LVoESb6wJSF4fWx"
    "1fmqhNGSNhBL7DVSc8GQysENwZMqfTTLzBiVEW83VsoEq5G9FSzKWlK5ps5boQnKIkwtAk/rhCoSQS61FooWafUHr+jT2HPaJ4qe"
    "KPLHmyyo/OZlmlwbC8USPK9SZWAnCd4y0bjOTBX14ZZR5uoyWMg5wc801iqCos5rtSZU0pX9j7f39/c3lRuCpFgmhExDwds3UhD3"
    "t88LWeBvnzlCmd8+H1hm8vb2hmdybRhpYJaEDvmDFQhKBrTGHxStioa2ZDJgoP8xiYS0hxQN/A/pkZZxJDn0cWyVOo1xCszbHKUs"
    "spcnabw2DLgvjgUxdwHB6KqOYgtPzEspvsOwI19cKj4EjC3TydaoP2JHzoYYU5w4V4+mM6ely+cZlaKDEdSGq3hH3FfocN9/GvUn"
    "tgEYmXWX02yBmx5TpaJHGAd2jWKbZlDPBe2TieZWRtxOF0ueClwQPIqDY5rOsx5h6WcaXiZW74TdrD1wGPXFUnPghLvucLc06lZD"
    "RNknjH0U20VbAccmk2v4x2Ig0TwOCyGOPoFAJk3CwUE6m5wCGBUQ5nhvvprSsbm4SNf9Nnm7XUF8Zxkesd1pvz1ZnKFCeBQsx3is"
    "aS+Q/cisWE4t4Llv7Iv3L2L3xKLVLO5wlF3CpOpx23r8+GSvzE7+c9pdkEe4LXE6eQq7nTcfhHlflKcc1W5zK8QS0crIPsPs5W5x"
    "H8raU+N4MD93UmdI7Az7TSsNjluxppwdURNuU8p0UwlnECVXvZHTfqDlMbVlahw9CZf6+Lgt7bIb6zZ/uCDh404ChOY4fqAlsTZL"
    "ItIkAVcoIYyI22186Ld1oEtMOFu3qWoGmiHMJK24+X6kYueGK7sXmAYu814aTxV2dmbnxep7JlysAtn5ZNyMk7IAbZDhOA4lNv5L"
    "08VLUnhLz8OoMAqFqvMkRtmOSm00EobraOKcQAlXJOqczx2nxrCRd7Pb/WTv602Ok6m/iSzb/lrUrYQqwdYx6nVu2EybPTo9sxOQ"
    "s52XYSYfEk71SAWpVhQeLzWJIFyeXUaRVWW39YfS0GG+nfvOy2rEb6NmGSpFRPdJGQWapcy2HIFT5UF7P81W8DZwnjSwU3O+6To9"
    "kXDL5iGQ84FLDRbzAzBNkzRyKsoIfDqeVj6sXW22pmE63yiuh7Q/m61uAWocss/Ltm23BwT3oWm6ZnW4yEu438+MC3Mr2Zr313K7"
    "UEQGcj63s7t2ebGz2jlWFDqwsyCxcoxX2KzvLFmDG+vI76mFkQ6Tg1szhGxxPLlwblpnuTMY7LoTd8YpDw9QigjsU2exYyPSDaAE"
    "o83B4ohtrcnheeRedFr9Xet0rkMgMNp0IlBpHQ57YviRiJxdS6oAdUapZRLm23OrrTyOgKWS3RVNhvlSPu2R+udhC2llvOlRzTXy"
    "7KnKsSfxvA8sHQID0jrKO1AwnN+Mk11xfGiVgl6rXI/wuLNYASIlD3HZD8M05dkFrH1uLC3wVfLS8IQHWayZz0RWSnxwIoLBVrEN"
    "b+lQN1ifVIiY9eRNVapcdYJOt/aikIZyHF8h0ClPHoCCi01l2e3Iu5bma2IYuzjoFLmiT2EYxhezSyNGSHZ3N+xX4tNINjVy+Pxh"
    "LrmdAckgt52e7V3SChbnwV2q4oqurPFKYisHGm2kVgAHzVaqunR13dIqO3QSjswJtBbXq7UVbS0S/lTGBSaXMRe346OruGPOtcr+"
    "Tc659a/qNnhQXIRDrZTLWl3HXOV+IBatFgtbl8CkEw6HLZVoWeEU2IqUxO4KybHbdj7at02zMOal2HgzFRwGRCruBGznCpHdwPy4"
    "Y6XblRZxAZutCJ8A0u4UD4742a46hIQZnxCQVBax1RLRNBRI+3FbzyPECtxmCLSjjLCERRw+pmw2YL8eVhHMau3ssIY0X41bEuyJ"
    "STzY2M4KbGjRl3eVkcKV5oV1N4t6UpMiUPfZ2Xo6dxzZ+Eu/Ejs6opke4nK5OP9uNBxM1sswSE7RbLG3KyUcHbG+DHoauDsseP0K"
    "nGudeUd1WoAiojTlpmlwGz7W94LXQ/vWq3yi04WgEV5sdsVirEXDUDbTSgKjuadTTkOzeVIKRhfurdvlT8T6IQcXyzTcZ2yXE8bh"
    "Njy0hqehUtdT20jbAVRcLCYjpFA7nRtpOhNyOrHBgqp13IUJmncCGDuwd1AG3eUcazsvXgK2ATxI55sbW2mN132YbdVclapJWwRd"
    "iNhouVVQpj9vhdjxro2L8a7MuKKXMBG2hhsThWtkJ+7+0tlHu1BmcrT1nXV/F6+vXOjCtexwQNbpksFFQuWgw1/JM/1IAa5gyCa8"
    "29mTk5Eccs6xmkLN/QmqVm6F1xjNQqONHFeW+2P46BLpGlxfLNaZ0ZiG3FuxIYTb9fV6hadt23lQaK2aYnq54pKoFGouSxMrZq94"
    "XUlqIqz51lGpo/u0HTifU9YO3RvnV4fWaIZVmE2Y4yrVfnVxWs2x4WUjHGNlm7itnNJ5zAagXDm1RvqhyrTe3VqR0SYqnLxsy1td"
    "J9OxOIYonfk+E8BPjC3bT7HZgnPqOnoLbnukodStcQWQmi4nCwm+uD2UAIZyd9o+j1zcJptbeuF1KZa303wShwS2USaTgdACmg0G"
    "4xqYLg0HEu+nvBs7GBmkt8dKOh064+Vw31adTPhxo92vZTgkhhw7oSCav4wkTyKfBwYlW3MXQYqOZF6A8Q5eb9ozPrzVBpX0aRaA"
    "RaShUHggGFA6A1shOSxPgL1jVtm0qTB+cEPJ5VhI5uRkApxv8xH6lJOPqRESd1kPLrh56UPUiHEhGSJf30Wiqyhdv7DIojztLJsl"
    "Icv0pSU6PRyK6UBgSrOl/njFd/Mxd7GzcbdqtexlU8UP2RoZEthYtrOXQgV8Vz/H5n7/VkwtpQ5BUqlWW5pMwFyyRy9grlSIJlPl"
    "zDp+4RJWhPBJaURaLFOnYEG2dv0dpidM1ofYdJ/z8bWqENr4ed6V7BQ8ETK7JvOb8IJczT3FhJu3DxMb8VQvY7FLu1SCw9tuk/Qz"
    "m3bY1w978tNeqY2FMW89JI4U956rkJdE4sg34lPe2fYLYKbTyDaSzpl30Pb2p9n5aSnQ/TBUr9ijm2k7Kse5As1ZE0MmTbvRei99"
    "yZTaiW5UnLSKVN47RuENB+bs4UxtT5ZzWesip/53TJbcEh9lcQVCx/2lr5Q8lYFA2+OLTjMr+3FO7ju+uh8+xRN7MewrhBdLOheY"
    "Uaca3BzNiwu46YZxNDfhi0Nr+gAuZvVdvjJpKP5wyhkU8eZss2g7d+lKI8P0tqI1HOn1OCoAooe+ctwEjsMOSkZjqR1wkCoR/uJl"
    "6gkgx0jROeuYSvPahOEK8fa+OB1GHeGcL+9yZw4ysZnEgKRUtjtn0X7e3+uiAWqd3fnTWeTQjTkkeOtL1yFx7UyhvmosDQC1YCrP"
    "IBSp+oh+Z7/WcEHZXKYaOsyUYqgYqMqXwb5e9y/iqRzcPiRWXSBYKHY9Lfssu4vmfXA2XwdrNco6aA+Jsr3alGLHM8G1uiGiLs7B"
    "c9x5KEOU3cuecmzT4e5nwabV1q/3e4qLmbWd1VwyMC/YUdVOYKI7iU7ItrgXnXMQ207CDYwiGbx1YW31SGmE5mIXoMknQ9GEF6ku"
    "Vyu2MHUV/d1GBy+uD6FAwE9X/O3tZdJIoW17FpyD/U5cKSuyN1OwZQtlzN3Os1Y32m81Ctlsf9ypNTdszArjTtiDQ8sB6/CN/MPR"
    "rMBsyhGvv88RPmSHjzGpbiePnWBsSxzzqqknQs3kOd+Lw2AY23iOB9hKn5BEyO1Pu4FzP2310Y4KuCHDkiu3uXBhX5S02kjKfjn6"
    "ltvNqi4OT7ETF15UU2VwO80Rg3kadXdc81iMXTjj0GwV7ITzkKPEj0PbQGYUWqxSxZzbVZ6Fbbv6uHTkhxkl2+pHgrPT5Gxz1jpT"
    "ph+NIbAaUKRE4LI5p8JHmhi5knk3ngjMHLWMsLaGl8CgEBv4M+GxksLRTZcUCs3cMXWSxXEu5hCXremmvwsEsstzAi8IvD8cnHtO"
    "kDy2gz0o5M+c3aGFAjHOfca7DRdagn8ucN1qNTCY2SSr7ThtDeLDvSqx0epuXFiiHqC73xDFdHa73ATDNoDYWns2KbKPzYhcKdrl"
    "/Li7fnZ1dnnMfkxjdiFw6RDzhRVSfO7+3BOfAY7kdL9o+CJFx37dGjNxuZhyIfEm714nCmhk2V13+4qtHR23o77hXszvYdnnL1OO"
    "6YAkg015vkttwkeHXKFcIYxqMt0eVPMmtgM/wyfhU94d3e1YzguI7CBfyMTYjbsahVxYZkw5MJ4ZopuAwzPZ9aLp4VguUaFpzkZi"
    "ZHziCh22U3juXMbhyMoaypSdx9IF8LmVvieN1fw5rKNA6RFNdFAb7Ri7WhPPJUid9skkmJZ6vROUIFbDKh6VtpE4c/DBg2mhmJi1"
    "iw0p6J0xaWvngB0y0CWztCb5zDw0yk2L+9M86ohy45Tdm2gEof5R8DIoBEU9y8jBnkqsYvGs4yxH6Yk3Vl1AzgyZnUKjeUJUdQfV"
    "P029fgZO52NrcteS3aXAtNxmlAPAKkBNWFGRGHM4NQEnxhQj80lqSvRsNd5RQurBkVyQOnQ+sIjgSMduLWFnny0Sl2kMot0xuRPj"
    "cqVNo1RNiNzUzcoFX/8EORzNXsUahryerrPqBM8KWXTnoIjdd1pSDnd2iXZ6rhBL7OH5IOFDwucD5DlnmYjsF1mQkxvdTaPKtJLt"
    "fGSadU4Dbhq7gFDeGYiXVEVXhldHkMrZI8OU3bVOl9qgGla0eDIt5VOBSwgZ5FJlnx8R+7KblzzIJLKwZlz1uIdmNlE1WhWtUH57"
    "GMSXbKjlcy2JTquajJ0R1tEhowk/1a5CWHhFVzjbEqx1pUGnQ9iaMhwfDJWke7LPBtvnpDwvAZRju0ETOd57rDK0kz/TgMwgfTfQ"
    "RaodxZ4JRCJqkDty5IvsmCx5wcWuyBZi7DTP7Hfb+bQvVbf5AuaoFk75CxkbzNtZFJhXh04s6N71YuvjpnMIxRTXYNLbekeIgu44"
    "r7PQibcmcT4d6sfiF5o/TOkmmNi2s/UMNsrRmXxq1AQHFUGMF3etKHSsJnJwPzngkNLZvXG6pz7R3mRSvKNLZ5tHp3sbURXQeuBq"
    "rKqeWgyDHVA6N7KdyGE32jnlpnGxufO7C5UsDc+YhS1yWVX9bmK0dZOBg8M+R6GQN+ncyNFzrumQ0sPTDOMjcoabepvHBLO5IAG4"
    "XZ2HWhLm8w1qqwpQRy4bu2tPK4nKwrmNMp1MVuJOrvhA8lDCPsfHLik4KcX9yTAdmeei3gxNgKfcIks42+g0sKEH6cN6UEZ7cg9w"
    "cHE0mi06m8g8tAu6D9guuJjsC7DSF1FHuFIb7IcVh1gBcdpvt8VC55ST7SP9/AFRLdyyj3rng3J0mzvFF61kehGIdplKXrTjKdq+"
    "yhRh4FRM5qlstZpZ2AsrR9bN2xqArMp8IBKtr2xIz9UPCrWF13/ITT2Twolv23lwWMxMZpGw0hwAx84oXxh2U0vPgFy5GudKaXna"
    "2yuT4HacErZ2AVucRbAtjVora1Xe9LFL6AyGT0FeIKG+d7cpHU4xb8VzbBIjNbiKRdoXLFWKBZa1E14cVlpY/VgatJkBtaA7lKpP"
    "q+ISqMkLt8PGNDbuvX8yDlRWfGZxapXJASFNa6RsX2VzvVM10j7knMduMdJZpNxOcRdYnr1TV6FeK9KrXJkM9EZKBUBq7tI5VIoV"
    "WXZshSfO6rJWCYVVW5suSO6DY7ItnoRQZjgHN97C9HyCXG2pkeo7u2E1NBCLx6BXgAjGmbcvS/HmrhD3NeREIiXtUq5c2jUv0YFD"
    "Be7hsXEawKj4IRsaQh6wDh7GtUmdap6RRtaOLZSJe5mBjwXHzKV4XahyqtFL1xSO7FMS4a9Foc1xvjn7g4ksOYAUdj3io/ZDOUBV"
    "jwKe9TuFi3/BT7ubwDQZ9iKxhXuQGQDBaMNX2RRLRJNLS02wiJ5b8dlCiSxcExcI7+jOYTj1Ms38Llxid+fhWolNfT5FDFwS7q08"
    "VGb+bjkZbhOVys4bOexsrC83rx3c/pm7T7Qr51jAN1ziTSHuDu1LnWYg0CdnW6+49c+2QG46s9Hz9V7IY4GmN6O4K854AkVOIhKr"
    "l5cVqdiAFwEcqjkWMSRSpbc0OhytvGd4NBX8siMPoZdBI+2JRwIFJjnlCmBxV1jkYbxc6s2tc4F1t62TbaXHjQjyFJ/65w7GaU1m"
    "ljLugNnUAqK9sxlM8XmqWZ1QPEat5nEym+s01iFr3yUnkVynIDngHLFkUTmf8efUWEq2go5dtTegraUclAvZFXdkNYgu1svuNkVS"
    "6v4+DeehKcFNbAQ1Xx06qdHxAIDroWtrTUEXlLCXoGmx2OYDsxIONTdH1THdgASyToKbET2IFRvdM+QtKUMM5hw5YofmADi9nrCX"
    "wLghV5SdozhOZTflcRXcM0NlOCJadSgcgYaXWn/sg2Bg6XWJ7XRrIbhDo7iXdAj7TLE0wIqlWTPf5zxkB1o57AOHX+mV4MrGfljM"
    "TulBnh+AdhjuRRwtH4w0cvxoi4fHmXVlOkxE8kEqksuiE1ef88L9Qkic4oEOOLUdZ4FaIdLpbm1Qq9EL8a2tw7bdZGiYiV+WDht2"
    "qO4zyipDb2zblDDZeFb5uI0TqrWR1ZXJJ0YNCAMhebhC+4JDwGbrHJDaeM8B32HWHWIkGwkIGTDb7i8aq1hGjWlwIj2zBQfdpjwL"
    "q1IjD1m8pDpmyXJybN+CciowX1WW2QIjZkM+L1Mt2CfZnC13QOx27tQM+0fB6A4/pYZ9JQDnW2084vPNQt5RNjOtMaeKs46Knl4o"
    "tysnhovgPlZnC5193OuE9seImBhEd16kLTKIFya3rSG9yHpjjWVcdGHDWZqsM/nIaR93T8r5I1ITtkO8TO089RbVBOp8e8cj5KSd"
    "pXuYTew5opuj6GZURUqkrZVw5zK82HIbuFqPLo5820+yPetFisxTMlHL8Vg9fjiFMGjGR6QysdlHc/MDSA4uHT7RLw9hTpqEwboX"
    "taeaS9sW8pEiIMmRnpBNdRJZPnMezlgY3k2yJJw/hvshJc0vzmw+63dfVuFeIr/chfuzfbkKWLtULe8h8+Pj3FNe2HsTl9SbcsFO"
    "L0K7ye5unypHg6ltRY4LNBIbKntfKpeL5g5pqD+PRqgaIXiW1k415kRYgo/EF5e1QueL8QzGA9HQGl+5W8l4J9poFCYTO9uxIXzJ"
    "gZQavl66O8F26b6yITPuzVlVfPVcceV0djyyuvK56HIyGtoqiXB0u/FM2XQyXzqi0fFFPm5np7548bgS65MazzaaChesyrmLEq8L"
    "iygqoT1/ejQsTrdCtGsdJpeRQpdmuF7EGZp5132UKc/4WqIX2nlqQPw8c+eCHi+35TK8g4XQWLGNuNEQ0Mofg9GSF6MrESdj3yRi"
    "or0eSgfibYntF6NpOFJ356KU20fBMQZpdQnwYJu48AZqs3ei2UEDQPv0rosXp4dWBp/ERoFdWtw6NqXJIhhObqB02jNbSP22rSyl"
    "nQN/FXBAG8jXnW3wubp8G8beGLnb/HAejkba6zpDMZ38oBES+8VjPpQF9r0NkHaMkp6adQwC2012FoXhjU+dFlJzpAt8GeoMd4sq"
    "cQpBfirD5hWrH4NSQKI3c9nPC2vnlElLYCYGViSoi4PYsNkMHl3uU30yJpzAaDidzARfNgIAgfMxMsQm9WKHy0zG8ZYnPU6Tm6ZT"
    "wGk7hbRmJWC4JRvnVdancCTCdJ2+YrLRqckU4SAd5waSd22maCzRazmCTqzabbZQqha+9OnsgITwCrfZz/2YNYSgHdvCNycjmL1U"
    "Bx2+osOmOgbNgXs7ObvcG2gLipjzoPoTHbEWjyaj2DyqOYqMrVgvE6Vl2GnzXoZ9e1uujbseL0WkG6EKfyxHmm1rv2+b+0p23OGk"
    "2vZlq0yXUntCtLFbl7DDZ2UpmsWY9IKY0cRweWoMc419pp6J7/tsf9ZYFOtVH0jkQuvD8DSYr5SUA+e71tFwkVd1xgGuEliNO/B+"
    "78hXPp5gR5oN5XvkYdDrbvLtbXswckBNz6CFH/c+G1tLZ+yLc10C8yjaWfPlTmNSDmFVRg4H+4J7xe0Yd3u+I6sTbHKu98U9WFMG"
    "MNjYLEutljM4rzqLiT4wSzTSVKm4JdUQ0cvNsNI+kBo21ZApR8C1U78RDPZdUZCrF1yBvcMrzAobNos587ERNhJT/eOsUBoVXPte"
    "3JHr7kQH2gvYHSwLeA++zk7yLbw8X8o1hVqAJMeLdS9in6RWrcaw3DydixTUoI+VdXQbHM/O2UZxdfA6XY2i7xDGykwYsS2r1Rza"
    "GrrrLaYemzuBHMCilXFq1kGK2eK21qwFBRTOz6MxHprR3c6us3Jh9qCy8PYPtcnosBKmWQjYk7WYUJcmikjXfIkMsVz2F/Vup14q"
    "YdKqPx0CO9hNzvuJBlmF580OnHfUJ9NMk5PgS3A7cJRyOVKS6ot2NcekA3V6JbE5N9EYhN3+Op87OorpVKLbSSFMNUId3fvpcnRo"
    "2+hmx5lV/IFFaDE4dOIFvj/ON4bHQWWH5WwF56lwtDqOiOIqhytN5jTcc+l9ItDobHrLfMaWqxZA9aevE/XZAu0pnXVzkXan32g6"
    "JaAzD4/7rvwwxslNDhgrW24f2UvnUngBibPzSFCdaAwOpmGgH2dOSDvIR46uapEN9Dk6E+5MyOYwI/aZEKdk5PJsBkiEPZQbJ8u8"
    "tNtz7VyzBvkQwSGe0RptHYLUrjMvetB5uJc+BpINEZPRYnrL10tiOMhPMiuXl0fgfFRy+PZuZCs487VVGZ9G2uWi6Gw2lqIjnma4"
    "asdbCXnbdldaZCI0Xc2Nlg1GqeUOXmCSq/MLR4Ti9sduAyxv+gcxMYxY0y45gQQwbhHvYSVyOLlYrbFYqTRKRL3BYA6mNylPHmdd"
    "qz3jLaFQvCZD694kG+5gUHOtxOe9hALstv0ZGypXBG8NwBzb6QU+xeRaaINt5uc16V8vAllfr2hn2Gj2sqlgqRQgH0dcMOlvb1u7"
    "Pu+xFotJ/JDFFNs0sCYl2O4IAF5ihTdGQm5CzQmXK7vaFMMdTywLct1uw4F4/elhFBodt65lH0ofcTQNgBsftUtMcv5tJ7IfFJVW"
    "nWqvmXqj2tw5Y1K4FUMjsG2aUCCUxZJQemk/V/btMZ/z1QpkdRXxklDDNx5iwTqQZZdVybVMQaracsdQJddc+nsYEGNCDhANrHZB"
    "u3tHU+yiiUhceOiDpqzYg8jLyJG1KWl3APN3lk17d5merp2zRloiR/X+4TCspFr5Ut7Oz86NqC2Vwt1Jyr1Vg9aZAygqaL2zSi7J"
    "wcAZWDTmWy+ZAGaYnfUH43uS69k5tLEZblN2prwSPYvDkepsBwIglVMupjKvt1KqOlaS6UqGLsldb3CfaubDCwzNjY6BMd50rDG/"
    "GkV4E2XbalBIt4MdpsumiKaq7lowA4Bbx9S7K+ccx4HYOCAuzhs8UTO0eVnioyLZjFXW/kIIs4287rYzaC0hMJyplzK2NJJ2hfDh"
    "WSpwvWIh2BkDfYyxxuIBX6Ea7CSD60xy6lozi2y1p1xSBShYPkxrHAWI7HoIpSsOUvYlURFLlEAfJYMxINOUEHvVuoggvikpJrd5"
    "girb443qoj3ZIVk6vqiOE04AK3I1ic1Hieoy3TjMCaQVzO3kaSLlPcyTcZnx4YFINzGY2GuL2nq02C8Jb2RGEoqPRFOnfJ1OKxVf"
    "Gch215fUWTgyqQOwj1VxRSSjAMlQB9+uDwMROijXSu6Au7CFbTBe77nGrmNOmXOVuOJLyKuSrwaX63N3NgCt7ScrbePiOa/DD2fF"
    "jLjyUIctooRhZBJlVkhlM3Vv4qXmTDgvSkW51GPt8sKX4mkG4+0zGG4JjtUWkHKOiditZw/eWT7r7VZdVkhyBsU2i0F4vjI/uyGs"
    "XYrZ15H4KSV3hkRhJlOdGd8NFhS/mAm0g8B0nFXj5uQ53MfnwcIuUkrlJ416jxgopLvP+bsNvJiOD1FvcdtJ5QMNhqsRBTRSCaTZ"
    "9hZKU1IgEz4ycWun7AZ7y0h+WR+ckO5izeWTq7IVj+NMUqH3TlwpHnszewMauWbBeszj6w6APNzIt4HeFPK7x3IvtsIivR6Fen1y"
    "wBdKzCA2DaT7x07XVYvae+4gX+bVjRTpetvU0Xuq18f+oN0XHQd3XmFCimK1XOqjdAAeLRmFDM8CQCZSdcWX1L5pLac83WlvUQX4"
    "dH0CcLZq3b1RjbqYzCRIa8cPZerkGS/lK3usNWyknGyv3qoyHLpuE8WTOAMGB9gKOYrZeanP+ONMRRp0ersYFeTd+2BhVp7HfCm0"
    "E2xlOCB9PmCTtg2y5teNZXsN5iIp0hegW+CcGrBZEnGmzwsBCzOFVvJkH/BlfEjz0vwUT+8JwB/MkEDa4wRzdGfkG8azra1gXXRZ"
    "LjgHZoPSrDopLQqRVjrtz8IU145LsZGIu1ML+yIODTocRnRSuc1BVkLIBvdnURnfHZphpj05tSTCh0YSHhbphexbPqmgESLHnmpF"
    "u+28iBWVebEJIsfuvEbX16rRRbOtcnIEYWsIZ3L0Liu6UOxYRZL+TDwZG29SJUS0OaiJq9gDUykbtWJjp+JkUnOw2WW0UopN48wU"
    "AyuQk3cGbYAgHcT1unjBkn0hCqHAdjWq1/O57rbopgSkeXRF04vyZlOKeI+9KDOv4I4zUZKDcuY4jQyLxUO7zrr2rFPesTuUYGfb"
    "AXpObIJZBOJXtk2vi3P9MOWwdtotOLbKJlKRFlSFJ73GttNLgsHsahhn+Dx0YHqwPW8ty2JkDCbGyqrZD/hz69zhwkBs31XyuSPk"
    "Er90O6gt5bBXeXQcEuu7vH+5z4Vm27TkmVsjMU8SbR5F3lFBI4HGImVLrKbjRc/aEC6okE/Xq0Fgzy/Ywzw06qebA2SMNp3uQUtR"
    "IwpyOs5M5OoKBzvdoHCgWa8bikZgFlx73TMkg6bsHLyO705e1BHH0ERlJq+s6MTXbXS8LTfbPPf9aaIv7yVneVYtBU/YuVqphuP+"
    "c44azpaDEMqPY3SuAYxs/kE2hQbizIalMbstIsaoVp6OZCn3Yuw8oK7SwuFWenjHe8oOw+TgmGxEww0vFLMXkhfsJLtYLjAqDIjw"
    "wc+FEl2ayJAct/L3M2U81m0O/UiVcHhyAnrwJWtgy097+aUTodrz+Ca6bSdXRYVbqsrWs3ECZ+g0K3DIITDCoOViWbOhmXk77ZPH"
    "rn4/tACdQsU7na7yLJBM+xYldQ0SBDCi0HR4LZZqbtDbXJCFqa28x0fx0ILokHBwCKSGhV037+hPioEqvqu7ACc9s7NDoIFIy77i"
    "Lycqu/DlcEgesH1uelJ88pLog6tZgx5Od3OUn8dc2HlJAoN9Dhb8gKctWNlAK0APgVzJ0WAc5+Kkb0tm4n1hFh45lTqrhj7WbvJM"
    "lwMn2VHw1VUMmaWCpfPRLmDHh4Uk6alRPQIaXSrAtnDEsgFkvSCd7Hpa7xZXjUF0CEzlvLM839hY5HCiYIJdnSvpGMSV2FZKcqzW"
    "F97lGGMVoVFd0Swaghy85PELaTmz8zeLziMgFOFMBNyPhwpdz3Tl+qw59Awj3anVIViBGV+lyrHwtpj1bilu6fBYnR3ruHsqNIL1"
    "vLszaIOOeipULGetuzzscSqhGZS0Vclg7Cjzm4TyPyD443ow732tTD2RdxB8w/ENLWnnMHHckrBoh0jx68lRPJPPNNtwt/D+9oY3"
    "UThXwIs1BEFVMN8bni/UM408nqk1yxn1ifeHP/SG1zNotdDGmxk0U9fOCh7fLOq/9165kGm//2MB/KEPi8+r/vuwBLUf7/JKUt4/"
    "1N4R9QsrzPTPfvDD6JfLoCiidwyYOoa8ZlgzkvCtYxupZ9qI1hHy3jv69RGNQ6I6eNDcF7r1xdpoppctoOhA6+/zPxD4nkkOm7H5"
    "HgjqhRrSMGb76BvwfqZa/Rh4dCuUSlonc5+A/zPBn5hUh2tVnVLTVH3+J75A31DaQ5CaTqjXPMnQ14TeBywW0DZcg4cFVB/W+wcO"
    "m7+qKM5vOFZGmqpAIflOrm2SkmymWjCYrvPi4yY3t3Gb8HCY0TvrMPq8P+5r/Qk8i3YauTKONQ0Jesb58bTOty6DDNrAsTaCFvQe"
    "Ons+bo2a/OfQQqb+IMGE4sNyJ+iFanU/5DJFA+NVoO84sTqCtMtw4bco73zPoPUCil03mUHhbTI3xGZ2PE9Q43uhVstkawWV5cpa"
    "ZGngeb+quqAGt9TwOqMd9cURVDs9nrAAT3vxw3JjpEkMPm5Cf+fCp630xUJ9XAXw400duVco5FXWZ9oadUfvP5bjWRUr7df52ogW"
    "mrXMQIUpNDWhiWhyBBfbj076mFrPd5aQFVxWaFFlksenjqMfq37XsRmk+f4MdtaUXqFQb7bxQkNjW14dpC2t6cfzImoci1Yb/D+8"
    "j+f1TB/PZtq5stoQeHmeU/lUwPOwSnYjp9ENmdrhxlXRotoa6GrV+9xc7LQ7aAFvdTKNNtweqCDBB4CKE21r6tnvNT9EmtowEdOz"
    "MoLCQ51uo3cd7tS1pX4Vv+dFva4X+Pb2ZrMg+nF77VoAJ/Ae4yKAIIoCrx1jJ1XWysyUoaUfFkvzfs1AoNakoh9g5wVFO8M+Edaz"
    "ufppryLUz9s/7ip8WGRBe8ZIFo6QlrTiYfiNiluQ9haGJyWakGkLox2f18aRH2Prh+RVfMRUoSXtnoF24F7RDsYLa+1yAL1hhLWs"
    "g+nn8QmK0hop2rgSwMgKQ1oUYctbKIlg+B9vhh1UDV4x06m98M5o0tYVaTZNTdC9SV2zQrfQ0BWd/01dWHV1v5HztzeKnlrw62l/"
    "/HqnANAk9MPCKDQH/qMLLzO1aPwDvJZ4wqK1WuIWluaB2yF98Aqn/ZNo7SKCxftm+iKrSO8AHLEDVK3N8AqgX5P46f+legW31qkg"
    "GbcntBsR9wF+aoP++jGjFeDdWJx3UAWz/Pz16KkSqdGkdwYtSXUj6Nw2xvD+siRUZ0NTSO+mxz79sTZTHQ1444i2Gri+GldmyHNB"
    "lJ94ordqG+bGIZ0vDktQw+j952lCWm9tPjoWjW7AxDDt311SE5ZnY6VPWev2ofYBn/qoQ2rkaHhv3Z+RPqh0q5Jw488NFtTo9Flo"
    "VpVq38sc/K+TuKPxmZdVf3pjmSrztKrbCIUGhInKKg3VdZYyTSjazLTfWqMxDx1We/yQ0J8axK8nYjQ6NI5dpU6TGr2jIQsPhfqh"
    "KlSzGN6wH59Y8qqBnxvv+13XyC+NmkTINMvKXzXqC6sZSPC1gRQkWu8y/0fTrbo4zLU1kwh+RgOqEfhmS7stPvB1GFqjT8PmfWmY"
    "CxJzEHi15Wvd8QA/3z994rslYXDtaefqD65LfL2shN80H25sxc/rfVvZL2VCByHXkqTpzoSFYkgFwLXV1H/ocLc9/qFyWt/nms4y"
    "LY/puYHurmSv+Ewi8odeuCFlfxKsm0zeB9J0iKn/VS161B2lteAkq3IIp1Tdrt3b0oVe052/McwP0dUswed5POTv0zx0nuuq5eZn"
    "mfoZoqmrD0PzPOvamwq5GeVnFULRrEJcuXNdMh2r1kv1r3WM6k+PDnDjzRcQz4qLn9KSdn8vccXvflK4d64+a93rICrcn/DbLCjN"
    "CRtaN/C6af8fzfpytEcXafPdNtVZ6M0J7T4cpw4tWxjjrt4zNm0VVQdAvxhH71TjbpkQCjm3iGuWVfGoXNwSkn4bkTDdbLSIAsuQ"
    "+x9fT92T+Gx2TRPXZ/xJ2986xy2/89A+GwFSu1PIr5/npYvIz5tK+fVQ7mbpuOqVv9VXn4emdyJNKvpafz9fte91oK9mfp39HVPS"
    "bJieZsRwDEtIjLJXR1MdK+DGsI97Z9DyH8uUFVQzpHkhX7SDX2M2eHVV5r9+Xqk1mKYqdbdp7M8sUC3sP/8OrUfzw30hs2vzulyq"
    "f/PJ4XseZULLmn7VJvoy0IdlSe8TLMFNKMKi2iXgEyEqiGf+wowr0M3U/Loy+Xtx+NDHVgN6nRJNPkyG/6dJxRqWhxbNrQ+1rbVe"
    "dY8ZwNBrvx6h5YsJ0TTKiwFZ86xALlUJvOlE1X28eZE3L4ZWeUDhd2VrIDOuJP9bGycLrCb3R8PkPjm2BsInf9ZEzT//W5/2W32u"
    "kfTzBqazXX2gk3F7qOtU92+c9Cv7H+bohubGwtttb/wqKZ/cg6troeH+mnsGX26C9vGNTwPeF00D3xDsmtYF+0O1KlNizSqJhmqD"
    "HxEMI2t3o3VzfAXWTOznyEVv1EkwIzMmrz7VYryE9oFQFOmG6X2mr6A+4G08kmBZ7c46YHT6PJDx/ItRHu3mMZ7hrlPXblTjhjQB"
    "xq/rOMYXbeuoED8omha1D1cYs/NwHezhJ79PCYmjJdWXZFXDB5hF9dpiiOl7M4Nh779MHu/7XJVCzT39qfc0pN0M+hLdmVEbXW/b"
    "8ZcJ6XV/PGH9HaaX+PCK6h7s3oOQJ2H0GQb2SYNoF/BpPY9483MeEZP3hk5jyVV0VcRXpNpDzRnTCTZh1J8/6x0TDXrr1RXXNL4W"
    "NRlxtt4CGiMf7zMhWGbG4zrjgJuGekzsLgBfycjbi23Wg3ldgT7m8+AU+HFb2k+k649vM/1+Pd9MykxvUb3h+/iPjaE3/VB9LJqn"
    "gJ83sdHXGn/4IHe6PSZ84HUQg4af1/E13fR3wqjD//znhvvXL/PKGEjvEjRXTQhBktoLCGTmcFMxc4KdaqpQfWL5z38s/q93F6CD"
    "eTTrePuksld/an7yHfwzLPgi22psv9DJ12k02y6TYGoi8eUqX2MiZnO1bKadYDw0m9Mr8HW8p0BbVVT/mA2Irr+MHfQce+gazWhV"
    "V+ARCF6H0yoB6jSe4p0fmn8oA+DbI5a9eQpaTs685R5YTBCfJVgUZMZ44YgqKnpHjTkfdzWodlDn4VX1nMX1QH6F+bwrDLlZ84yC"
    "315kouL9Qol+mDToFfNv9KGOVWHYlzleydAbPk/NkFE982ISWW3P6B10WN81eNJjQZ6idx9m4rV1ofm1Sq9moc2zAp+cFL2n5p/o"
    "GaYbR/UBnppMK/ESLHyKUW5YVPLvCH/qyH6ZR9bykibLfgNVt4nGpQ/DOTRCXzNtmv7x/4EClRX7a+x76/ZTl4OnJ77nFCSg9QIN"
    "svjbCqiDP/Kn+6tSv66B5rjpz3fm5z/3v8A/ceiRnlZ33+823XebzbQaV86+7LKzeWZmsdCINn2/uaJ5VCsqvWQQdE7JOiOv9D5t"
    "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"
]
_AGENT_B64 = "".join(_AGENT_B64_PARTS)
EXPECTED_MAIN_SHA256 = "e5cbb6ed75e8582ed27dab18539f3b14e20f87d591181936c38cd1697ffbc248"
EXPECTED_MAIN_BYTES = 31149
BEST_LABEL = "c68_thunder_adaptive (refreshed field route + adaptive market horizon)"
BEST_PUBLIC_SCORE = "submission 55371099; rating is live and changes as games accumulate"

raw = zlib.decompress(base64.b64decode(_AGENT_B64.encode("ascii")))
assert len(raw) == EXPECTED_MAIN_BYTES, (len(raw), EXPECTED_MAIN_BYTES)
digest = hashlib.sha256(raw).hexdigest()
assert digest == EXPECTED_MAIN_SHA256, (digest, EXPECTED_MAIN_SHA256)
assert b"def agent" in raw, "agent() missing from payload"

MAIN_PATH.write_bytes(raw)
compile(raw, str(MAIN_PATH), "exec")

with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    archive.add(MAIN_PATH, arcname="main.py")

with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
    members = archive.getnames()
assert members == ["main.py"], members

from kaggle_environments import make

spec = importlib.util.spec_from_file_location("embedded_c68_agent", MAIN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": 0},
    debug=False,
)
env.run([module.agent, "starter"])
status = [row["status"] for row in env.steps[-1]]
rewards = [row["reward"] for row in env.steps[-1]]

print(
    {
        "selected": BEST_LABEL,
        "ladder_publicScore_reference": BEST_PUBLIC_SCORE,
        "main_py": str(MAIN_PATH),
        "main_bytes": MAIN_PATH.stat().st_size,
        "main_sha256": digest,
        "submission": str(ARCHIVE_PATH),
        "submission_bytes": ARCHIVE_PATH.stat().st_size,
        "archive_members": members,
        "smoke_vs_starter_status": status,
        "smoke_vs_starter_rewards": rewards,
        "note": "This cell only builds files. It does not submit them.",
    }
)
