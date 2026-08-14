"""HI_AgriBot_v18_Adapt2Survive — frozen route + Adapt-2-Survive.

ROUTING: exact dual-seat tape (Yubo seat0 / Gbining seat1). Never rewritten.
  WEED repair only (DIG + replay planned action).

ADAPT-2-SURVIVE (per match, market/crops/animals only):
  * Classify opponent: buildA (melon12) | seb (4-quad) | straw_flood | mirror
  * Crops: strawberry→tomato under glut / anti-straw; optional melon seed top-up vs Build-A
  * Market: family-gated straw hold on extreme crash; behind-on-cash premium dump
  * Animals: skip late BUY_ANIMAL when already 12+ vs Build-A (save cash)
  * SELL slot ranking by price impact + Town demand
  * Terminal liquidation

NO water path overlays. NO plant-on-empty. NO MOVE rewrites.
"""


VERSION = "HI_AgriBot_v19_CompiledRoute"
import base64
import copy
import json
import math
import zlib


_SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
(
    'c%1EBO^+Pck^CzH&pLScA=!JQ$gxFuBnsqk1+O3o0&HV}h4-M{+rs~SNj9ge>Q!V$M82$^A>b36-P2v~BVT?*M&|'
    'qJ{~rD0*Wdo@Z~yz~-@f?ir$^tudUO5g=P$otufBQrmtUTL|LVKvH;=yj;?axOKfeFx3VibR+w1Ee-oJQy{_O4b^'
    '~(>R{P^wl^V|0?p6x#Q?)v8S_nS|Cc=P(@yBD|Huf6~D(cgdl?H_;p?ZeO?{qX$l+Ye)V^q;@}_h0|#!&^W9^UE*'
    'Rvm3wg>cyYm{jeSW^5vf%{doQM_B7e$)!jqZ-(IFDKk#l6<0HR+{pR-D)9<fdqKDr70)6P+*qz6G^X}En%U|CA|M'
    'uO7{U%Qs{@R?;&GQ%6%PP_(y!-PHTQ)rE{b%3bF7gvU^N$+|WRD#FdXSOlx7TlWk6PsA#dBc+Pk$7y+j(B+5ujxy'
    '&$xcR7X$RectV~)oWB^X)UrI=SvrD%pRt_Ne9b%wfX{mS`rUcES5sSFN?Q+q8VNF7Gi~e7V+ytdioyAD-qs^+v(l'
    'q*q0F5}kH}YSdFAc<+`>uw57!H>((e2ee)&!bY^C>lc(ZF&R(nx3E$3lUd0I`#l_xZxWx&gtRSn4AF&PYCvRsl7A'
    '>9raX_*Tap*shUPM~1WB%yur`sU{P#qBSDynb{0>gLsd>^DYKc|iEfrWg&XqSm#c!x2bBr)yW32t0t|MCf=vN#=2'
    'DnK>eL|6)QvmaXT%o;mx>SPOr~UwnT+uWvra*{f4_7dS^@I|!z~Y7C~M*mmc^&ct0P5KewNocPr^aT1GlslMIh8i'
    'pPly_FkKQG0kgQ%ZOpEY}AHRxxsH<V8dp#$83Y6Tu=*=)KX!D~xIv2UG@vwgHc*O_<AL4YxsCLiCe+B%t80gEc(;'
    '**%Lg8f&zMc)-f2Y;}N!wfd3zNLC@zaRaf<_SS%p2>R9Tlef2Tp8xpG^_w?;dH=sB7d7tVs{^h41r7dXZ2tw^fHT'
    '~%5)o&1VtkCD<XKO_G<ayRVDZBxne`=vh<wz>^0|S5dG2G#zb!=Wd!SugJY~l*vaW%Xs++iys^Ew9ZDx~5QaN2t?'
    '+zwz_8KM*A;~}5N`k@9d@algFCKy9RX{MddwAoRx<+TavLrBB{a$#?O0JOY(L~&X2~THtDE{T@JSbPkS1oqfKKI*'
    'L4c66a2#0(;H_zYvd)XwzMeQ(Vg2yro*O!u~EY3HFCr11$fw=eWve1+BX!RvoeI;1rIKAF<Hd;*avet_!RyWUb;?'
    'Z(+?CFdaBIrlY3d00;+1r7hUFbF6IVWcm^!3S^nSpO&+N25WJgvGxifyg1Bc;>1_jDfnzR<kGg&m*ikY9rwI-ghr'
    '8IJUbASQ5O|0pG;rjF9=hGZ1giLFS5+1Qi7Qp|~XM)51?=#>-T;_>1E+`}`MIe{@;)}Nm3!Cxo#LQNLBnDitxHzB'
    'Mn4|_fBo<N#(50JIn$qDvUgDe})XloYD_L->v@+1@p*JBBSBK*kD)*;$Ni|!mspc9S%yD%pkL#vr}s@dB>K^N!Z+'
    'k>!z197kE1<H2_Ch%r+FjkheeS?m3=3EPeel8LpW+Q%l{rcu?9iZVj>C_K<^xm+&+!>0OZ(jc(NFIYI7#i^S{E3M'
    'MEMEj7_IR8P<n;h3i!Q5*AB;i1pxgK;d@v)z9H7cG;ifd^3~QgT59QU#WHDzNMK>8LTs62XU!7dCi#cim!=MGOs2'
    'Wh~pnbS+cNDA1%SB&7eQ@==Od;&CLj#sOP2@><TJ&UQkL&6^Pknhw6fmw$?HlG!@EqU*4?*XZ=~}?T9HHJ3{<>HF'
    'LF1vU$XJkfnDp&TQ?wd6R@Um|Qt2D58df$6xaMUj{QP0~WKR^Q*OX*~gPjD6>aLiJ<qV@?P|{p{h=iXXQw2uo@J('
    'S77>GWU8050kph(%gTo0^HAInyc%SvNFedY2PMnWoiYXT>~o;$E`hajn>K&Rl^6f;s~#{<z1H1Wz=9_SJAHaYmPB'
    'If&ZmU2@+ynOlUPk|jjjGIiPlI&C)g9z{1k=$D&=9?V~D?Wgy7aD{z>2=F3S%+aqM4@+|?8C}oW$NVG@evbvRSRo'
    '`N2mz3Y6%hKsBYz%z$tgcePN4<cvu^gWCJ^;))ZAsbxhWn+J$8Wfxmf-1VOu)cx2e6JW7z#a68yWl{s0LC=~60fq'
    '<w|<XFl?CKSTj6bm;UwlYr93fVQ`DhnS55HT`w2sbVCJcqNP3L+`b!LtWDl+j`|!6Ugh#m`=Lt)onwcgW*Pzg`QO'
    'DVO1-g(NwB{<$VhsoPRadI7x%w+J5DUX8eOCWhzMH>DC?<VUh6szCc1TgjF<mjv?ERQJpl|8@iC>r<}l?z8V+-Te'
    '8{hpt8_p1SHv@C}o%hDn8Fbrc!k#;P>bA@Nd=3nGLS2W8_#0*@SO^hO`MaN8mOu&mq!F^yXihKNLiZsRLgxnPO@V'
    'W{f`Xk)u$k=r2?MAu@tuGpz@J&W?Vj(3)0arurVLfi$jZ{3a#Ho@3cpKd?}&L@n29m(esMX6~dW?TE7QOn;!%=?Z'
    'bSu>o2qk?Vsb;$a@!WnCV&7pB+tFSnu<6}`5%tzzZ$fNv1V$UvN**zzZLq$_-EJk*G_2~16WkEQb3pSKi!s9RXB&'
    '?{?$NpQn>40Ndta<O*n>esr5=tlj_Q!*8A5mT(cXYfF=MTG2HYv5Q`Diz-=ZmlMxb|+Wjd3j`Nw{$>D$^rWJQg|3'
    'Ggtj~bZj)j1hev<$_({1P-Yqk^RN=cS%AVgsWOrZM~!0gtf5SzC0nM4{7iuG#xm$e_X>X_Pcj?p)K2iE<SD#Y@Ln'
    '2ygWWv4ia8+vSUZs#6Kl7Z?2jjsEUvg&$uC7{2}cWGMs{$LhdRP_Xbv9=ya;UD$3?0Hr8L+JtGRYknxP=!uky%cm'
    '6!PB8lC)C<TUNCN!&Pii~lE;^z39XNY5%{UHTG9{9VmtuuWkpaFtxWTY`x6nQ3K*5pMZ!M5f4E!WBFiZi3@XSOU>'
    '8!?RSiigKVV(HGeN9MuxsKj^|NZ!V`JL&%baI8xa2%zwOG0RjQEur*a-&vocDLdw$4)5GLozKxuh(}wd}-af6ZsV'
    'ulB!CZOrg1Z@R%k90|I!MwLl2k!~#mi~948sy&X9y0+dAYLK(AyzrW$zbHNjnRWSU5sGRC>&N+&eE7MIs7T-H7)g'
    '-l*kUWb=DcHfp^_;x`b+6hrmsKAz}9os9t6P-XhXHC(%vo`X@}xO$|4&E(W=M4&H2&<??J`%%kys9m&utOqCHp&n'
    'XSrF#LxhA=h*;~QdVS|G@7LKPD<7k{fuKMW5jkQ%%^RQic**mS@x#8F=Q7G5`#ao}rEj&Qj`q+8fYTe-@jlN`y}K'
    'GHpoYo}x3pK!LI|AWRr-Q%RGfU%5ZjClU`NmG4&7LWjsit#51;T96g?2H}k7V9ufCP05U1AA#<=V-XJ^h6QC<n5h'
    '@p+QEAUVU#IBsj<k#t#i!T?mMVY7>kxrQ!=p9YLC{fL&Qt1G*+c2_xwVq2!TtdR!<BGNIFR3XSO44GT#!LF2Fx1k'
    '6T|kG0H_#)V3s2u&kJ`BcC3AP|P=XY;E|q%NFCgB2P?@p}$Yj2*p0hyrG{gKpg%yV#1#Ad|tLJq}Nd<eCQ^$ETvX'
    '0@Kb#0~*S0B6mZ%u4Q&cxM62@n40Q#@=z9fuk+By;YB_;IjvTg3--K~Ru-^Ngz=s~8ni%S(z5(UO*KHIkhG+d$#q'
    '%YLHAB(o9ajT;iRxl@FZk<S9-w?5>KblqCl5&yWq{!(@330;!@)uZLVRXTqc1V!U{10zcT<oY0X>Sz8mdFeElLn('
    'epcGoe9d@SOiModq4wmFgMe*2?U>IM$$actQZh4qY5&J)q1+D7|e)3yR%$#YKH?rMiCx5@;z@&Q28a}+r9qOcU)q'
    '*;ILx(1}1mv_EowDM(bNB`LYjJKCTAdjt?=#u_Tv=m+@(|E;<IxTA6w|l^BBd11_(T78N+Z!}6ZMg<X+ka`VL>HX'
    'pUHV1|XOqEPpOFnylwdtwyz{<tll8;#|`F;?^>zC|;&)Ee}Jrn2;hv#;Q)QOvR)J-Q82v2UqJXizCRO{{L|)SD;9'
    'Gw-610%z?5T?wsshCrjE##~Nr*H?&AEpYZ4jYmqtL81cjrRS5>b(znl3cVu5+%9em^StmpwNxb)AW4>q*0IDS$e!'
    'etQxHf{3i~gX1_dAmBirO0|F&jaQue`SjZAe>W+Z}KbB0h!g+fq6HVv0TSr5l?$!YHs#289H;jCVsB2}mpu*d5rp'
    'NhK#ouZ@%!>V{-G4A-RdMpc3OEZ>DDGx<v#7vB#a~uK!qr@JVNS|x>PQtxuFYquYv+sjz+)jyBST5t3$x9(?p(L1'
    'ThR3Ywi0KPcF+a2KDmOt5L1qpoZBRjoJ<PCmM%n&3MaglcJ*w-79CLdt<e!G3znWl{D?!*gg~^9WKp)4vwA10>Hz'
    'gpjYnCS)SYHa9haKNMq!V%8`pqg1n+=m#EFQ#@>6s+yGD6riLcG%A^J7R+BR8@@Mu)*;Ui2>JTYZSUl%b3+o?+mH'
    'T_XgChl1kVEaJn*x-lMe_H@FhY(Zs_IO04qe2kt(Cp%9w@zKz8OcXy&IH7K>%z<mK^E}vr<@D6zg2T~>IV;I<@?J'
    '|PkY!5@*aX?XKPk9}Qn>P&m7?rh_SH*KH1a@Rib8P1uu|oKA`>HHi$6D8<5eq4Xp5%+3hLn)NDz?6D$sA>h`w~$G'
    '7vF|PAL+czt-=^z?5ROMs}*ILrv~@quYpuA|tgkm?wZD&Iu#92To#RlVavs$R4d-A;V8trc`&U8c=qFzb*rl6h<@'
    '(Vceb^lVoB-kAc1iHZ5vSH9b45t|nZy^Eg@0NVjN6?hU~ptEj@m-crX3)rd7&<UyVCAs;$=Wc)OFu*Jf%rq}3-%b'
    'S+;s8EHHf6OO0)po^$)S$c|<JEBWvs|G_qeQpg4;l><|D0yhl&m8IgX<L4f09&ylxs#OK&Vd>1dUN=C`<t_TH02t'
    'Lpnx+6l_15>U=S*<K^yTV)rzK$?OKaK|>UtoyR1>ARYXU=3<2aWEg>q&4<zrPr-Met^cl_9g;Tp;3z@d2}hXl(YS'
    '(gF>RpH3((IcrrktBAvGG*uTA=i(C;5ZSXs}gOsH2=FdWV1QTp79z`an@MldqsrL2XFcXPdrT*sY%H^)_s%?0p51'
    '$@a{$B_eCNE-?r`H~-MZ?@s&;wH{E+F&&SRg&(!GY2CoaORh$V*-c^$2$#Fcv|Hkz#k1I=mmA&wVf<KAr}JTcUeG'
    'KfDqu8Vr&TZbx4V<5xU*gE2;sCD2K5Y(T9fQ=*<SfB{SB!cz9MsV+n1q(|i^!XD@B2poAi4L+h+Un(&$=Xyi6PtH'
    'E@Sz8liZ;c>pGihB%`7kc+&r}0eg1Ct=vA+eY`n7XCpLSxmbVLEHBI*nR40Wb_eS<Ra88yz!ZSM9na9#OER&xMkt'
    'jJwN6N@ayc`+okC?$wxyI+4IgtC<aYJXeLcyc*W?vm%RKqV}!@n>EuKF6=;|-^b%rNFAQZ9W}dlK*hj(0Zf*k<hZ'
    'sp>wqRstzrlxpt-tq))$MDq>)%iuAnQtl&0u`t0rmD6y3-=SLSsAlAncK(Mj4+IVrNT=y9qm+;E_f2<T}BmZi`zt'
    'O|EaC?A+>Vq)~AOmkOK#NNAqL3YqvGB|E^@dDZ?gfyVBOBb?UTU$^okzr<~eFT81XcM-4PGj#QWHH$FXa&W3-Ih*'
    'QFcd`g06H!#ULty!H-Q8pgVfnM$S26zx`u8yfrG070Ak2l7*^OiP=9z&J*9`fVtXr~voLOcybZOhtg8px1gGWVp`'
    'BNJzb$hvdYKTky(w#oq~0ZmFR&9vwU*$ulj1b{aQCzmHPkd4c3Mg{!C?}ckmhiPL0`g7J?GzFB6eipzIla`#0)qt'
    'l7ca$Ma1H~jKt>lm3<Q2owz>|+j*~LCSgML$}vh}m?9qKw8;6BR;wpX1Lz`~h`zi4B*ow#5-j2)#@GVxyq+l-E4D'
    'kF3dUjW0=<ZqnCxBH-6UmhHc5KvHyfexC*V*os>@U+gfQZ4$;94F93nwWdrh@ORe8uR<;h$<us0e6aqF!fr&B;h+'
    'muvDm#kMpQ9n+bHe9mHCZniDc97&hE;N#1g~*4L-vMQU<~VV-bmB*}xXjBEg3-N5@D0+Y0)b!_1`}sQQug&NVS+}'
    'vI7Ur?X9UCoY7C9_?AJ24)$LUIc4^e4&YDfo$mt<o{!~K@?;RH`cYL}m%_qPHzlzmPTGE&nStf;h-B=wP?Xz)yDh'
    '@Xs)l|p2ft!1OkQlz`G~%Ah%X`7~z{pfSQ)Kz&c^^)Lf;-JwP*{*(zWS5z!OfGW<kgHhG#ajuclIG`au5MWzJpb6'
    'Qm*@`qk#yQXTH=B01Yq@4EQXha&!h^nrZjqd7lOaOr1y8YB@C1(w;(A3O0ps5Tv-4^Ohpr+jTRQiVc;iRCZoyHKM'
    'cD(P~%-g(xVrPw=IJ{4wGMI>KFhne#pgIdJzMk(jY;@?`IAQ4kIFk+1qx#?n5Aq%euOGUAmF!M+ykLCfyaoOiWpJ'
    '^kT8#m?+jiPR@>DJc##<JV~^3ATB1;|pEtB2{A)YDsh>XD3-oC|_y=#9Jw*02&!9$Y$=cD5+ED(s*0X?AN>^ph__'
    '@h*j0*G4a_%@>A(RNC991&STMa=7)A)WLiG?#HT}m=q?F!0_5(woUyx!-P5#}oC&6O_0b<6dcPMG=I~z?3l+cH)T'
    '@s7r&o)*$J3dA+*$LXAug=pw|((CBeh};m<1je>QtBe;H$ROYAdfuTIgaVc-vX^Uf;a_{$omFw3@*8vF!as-x(X0'
    'A}*EMq`r$U%0uB=^8f-gDkNaK?-R)&FeL5V2kozuo-^?p2|>852X^_yJY|H>W8PtEruP?bkG7W`E)iFi%P4s%e7z'
    '4IrZS*67det!7@fY-)k%c4mdZ&A42f2814_||&ORy1&isqSd>2aIz;~gIIcla*rtDsw2IPc8usTb5cZSJ?BLzYlc'
    ')}Sn*;b`M)>wPr1rpj)oh#8|C4S-}Fuu6cNW8u#LKPX4%p4LoTpGAUc8S@35ELJe6BcsKa;W{F_NWPXy<HcjSg@!'
    'IIa=7UE8w$HtUFr}4wr(s08x=p3G`Ef3n(s=Njsc2rhXJr+kw<mRT0&ENz_og9i7mYchNJo^1Mn)r5bM|kax|YVU'
    'RjKZ_y$}hce^dD)amB*XZ=x^m9^-2=}{UpadjNjj9JO@RldM<q)5j<#(I6KSz!*-tD_j?wvC{KFjDOu<nbXUOLj;'
    'TtFDYcvtQCs#Z}P&4UtoSx$5R!&l=ujltmKZfC$VP#X?zCy<qTtG<qNesX+DV1~(5N*3=u<c0)!0|pX|l^oy5YT6'
    'ppy$+YxYY9t7J)#;It*M_Ba^|2S>*pXuC*nRfUVF`4JQ_!xB<R)6%U|A`!rONMpicGlWjY%0kUDSdxW;o{T;JKqk'
    'MEqhpOBe9xrxrzr2=n~H>i+utt9fC-dU3T5)&0p&pj;eaJfhf(_F?3Ydnx{g{~{oUMrY;E2X;nOjQfe1(5G+Tucm'
    '6GIEK8#a|Y&AEa^i3L%sgV(p{Okv1i^{pKm7DK@2!R)XMEsSHu9MlPTSTe&hhFe++Zxp0@s$__2Z9SkAjO65>R8<'
    'c7b7|d%^tQbob&~H#_eEgJFVF%UJii`<fB1uz7!YRW~E(3)SccHhNJ5=y6uxyCYQfLbZ2KQAA(`2wWMWQKUA03|z'
    'W)-=uTCN#GyCnSJaUCHW(DdP!r8_{9a3=wSGCi(aVB^8#nHRdk<i7i!=1g41X-IgfO*~pcr%_x0Hs1OAdb>2)K;e'
    'un*z3WG9tpEoG^bdbkX}sndws8<PBu%CDTL-wqtH@xHw2J4F5KB;O?eJENX#RlM<KG9xlKJHOjFN^PLPMb9@E4+`'
    '(2LKWY%jIP44C?R(TojzSWb{Lzc;&NKyqsCq2Z%#1#wto;KZRG^~@RXrQ-0bqHe3l3T{*q;BMRJUE^4OSk7$&XcC'
    '${qznwB&d}Fq78h6Dq_kM?Py*=+kiMN$MIs=Du}Ilgr_m#T4n_#rQib*rf+2bbHfYAOA0m0aKY6n$eub3i8@J@)^'
    'ZjW3_|C5&!?0K@e8Vc*G%KaGK>Vs3JXkSl{-EL)0CF{9lj|%eFEQ9_0sBH6{Xsijc-X=+s_CA_2cwD531cg!&S?x'
    '1AwcMCYRQC>rhtuvtNx0B2D0IzWOx$DkY8#i&ZbZWVO<yyH@^Q=9eGVeG^RW(B_*Cn{mFRzD#Jt!z}dTEOOtc8jq'
    'WOIfJ<t8*{=VA}}H)+7M+as5o~)hD#kii;|#{Iz;r$2F!DJRuNgG^Na(cMI|-VJfJxR<0m8}J(ZZAVqSV>z;1R6h'
    'puj)a?@H)u@uUk<`sh0GI1*=PP||*R=zGh$DBnFR)ELL5a3I*XQ*?|RnAzwr)Y$55KaJTbSZ5yDqa(^X@SPWQ6W-'
    'zs^x^iwh-=1M;W$fL-B*5;R;pPy2FO{zc_c8st}v@NQrQpXz7u%q6fF2j||FE?`i}_pDMNSv`lq4p$$jj*~JBIZY'
    '{a0s3iX8jJPs}M#<|@+E6mMOo5*3W%N*-p(@L1?<g}wiLFt-`$E$c(n<326qw}aC1dqffg?)$z#_{<fe_S^#|bCN'
    'I+<XDvbQW$GU7kMvhtT?yS8`IZ!5`zYH?5od@ub{8^+UvVqdHy>eV=exsIrEiFiild@^b#GhGdQ0pcggIy`5bK%>'
    'wIO!%dA1}&2~b_pIclNMk%$Cvn*6rGye8tdBYe0<*5cto0r!!#DaP#u?%N$Jt9prIoZF(@psA+nm;AFIXk!yKT8F'
    'P?kK_R*VX`RH_K0A465UcLegLuqXuD`c9Q4hKmPA}V}MfEOu*Fc*vjT@MI|zzcPG!6PFy5ij*qagWf*e{co`rITB'
    'o!G{91$*?69T*x$)JHL5kjj<#~TNm}qaY}QQ<CgORgd*cSYL86`jbKx``tXrtB7$8L`o5`+s}W2W7z(a8F|jF}t{'
    'dbpQ-Ez>g?OgWje=$$#e<d{=}b*B&>X)zo`%Y;EsPpRTq>5}GU{^A@}iy(2jY-oz8wArN2@hQp=ZtErksy>l&BX#'
    'S<DCCTGZ;P=Sq$dAmqM^p)-=BpkWLt-3nxPk>t7GybN1p+pD{r6j6V@o$#ld=K~z@R9yX;uvR}0hU(Mt$sUz-bjo'
    'y)Z`W5*B9)?7_eL~@2Zq7}Wb{XpN+aV`tGDg~FFUSk&)a@X5=Aqc*?dU>It0*FC6(xW&q0t=M4?o=r&+pY)u-c^r'
    'nBBd?Ltk>&~7*d^Qp8RckJ@pyEvmo&wj!-xD1~eCgiX)3v3mPXp^L<P9g6iQQ}jUcY)O%KMD}eDifbSiPfWkqLNt'
    '?iEZz3$0&hTWo#6al9q;Z5^CYu<nYUUs=#^!C92U}(_>~)rd0w{sD!wx7Y+~He5fu0D<n9LMaoW-nPTEidhE)c17'
    '*=P+_0Du$DpQT*-&Po>XK!%8zWikaP_>-Hf^#;Vg5+!5{87bt2!x^6a*LYRg_G&qy}`(oLa+BY2`qFn-)PD>|hT1'
    'jccr9d3>BDJ7e%bBCHnP=dx{(IP{HNe{}W+Pj7!F0AGF=OnR5aWkEpE^=|3ASSeOdu7tt1y~3m$ChPZNM6VS7Hmk'
    't4*?`BiXACB#0UWJ!B-x<jIyvT!V&N|H5D2g`XGgbrv;t`SJ<OQj%L(8G$ouac;EslnP9#UNf62!MznfGHx-4a=;'
    'j*k>Dy-V(m0C&WY%cNg^}AIXi(f-ckT!vrivouEL#Psv64&q#fd0)61<83p(ld8H9W>S>DVpJ8N@yU+1!>WruK?k'
    'jMaF@kG|WxXkqZ;9@I59ZR1(FSCg(C{M~6e<HqK-vpEcD){Hy%-602UR&#z*X_%1aDWdW=lZLj8QF)YpX-nul_FI'
    'Rb=mUy!JCDT1xN+B98Dpy?SW?;ptJ4w>*)6FxfyO>i$>$Nx#KMJ%2aS|hw#E5h$C{{jt1Q$zfxXk!K^2al3Wlz{;'
    'fe<xFe8xi3{QyT$$2Wy+C$ldU;FZ>7Qf1;N8y#7#mps{lTZwK-mO?904B9@}Te}|w_BuYRP*XitIP+@gj^Cj9+wq'
    'tKPf5KGf)_q9TH-Wdn%5m$4JujTB+cSX%&XwBGnSdrmrj756#qcoGgNfKa;Q7+IG(t8@j=B_$UFosPYweuqrkc{1'
    'wNRW0^x94k}hJ@TI2#rC9xinQ<4wp9_0&${I;4zfiR&Y3+N=V?!D2nDcuq)YijZ51pVjzwS6fCvZqC=pUzxWrGQn'
    'L!MIxPC=$h<O_!0-Y!2(L90b>HohKpJ;QMM6EroS!no*fL{wxr4nxLVGmI4VCW)qA`bANLUKA=i_2$T2+A1W`><U'
    '**NXVhn>S~0(y*w_UlNyNFgTs=BB-YVNdt6Nk9&FUYdAu@kh1nd-(!SHp{UKpu6+c`F%y1N7O>?)Sw;Xal1LAaML'
    'bPo^%Szb*SMTBiYG{)KE;C-q1)T}dwrqQEaQ1CLT^_#Ch;nAf`5%X`Q=<<ep_yc?+B!yg}xkTQtUgw!8@6HlBWT<'
    '9}Z$rqa?CB>6LPbER)l`7HW^XBI$^%^sf`H8M?nx37=@967lEDi6L1E3DVg&hWj5fDO2!uVn0gLVa4<;R8%vy6m7'
    'a`l)<8DGJOFi{mAs1jjI7D(JJWz@SBoj-?c8~GrIe0a(hy;$MJFJgRHco7u(26&dFdJlhShBM*M^EcFn!<6C7DPG'
    'jK535RL2}^SuJ<y?0}NZDhO7sCq9<Dx!<nJ!(4)S+%zSYm>{CGbRe~67TU>4YzIMc54*@xdfwJOqo2H}?sMY{c@3'
    'E9KWAj&Y7@H8zL<HVTj*aJx80)iXPx0`?#y67Q)08soU+G1ufu)dG?wSS+)=+9yE}hHd6m=zt$g!l5u;JYNte7_L'
    'df5AF@?Eq|j+C1YF7oOoaUIjqkr2k&YBQoD=~V0TIVsI5ZTeJ3J+K=>P@V63n!s+n`T;5!3r{3LyEI}JeF>29jAS'
    'H~jOnGuvk)dkAUD1ab=aPc+1d~Eif0#g?)cR<m7Qh$?ovxTc=j%!RlxJ;{Us<yuL!%xnfI3N{S;3T-gl5R^L^soc'
    '@Dd=>un&=3c2N8XxdlLq)JXUdi)Z5lK5{=PY}AAYXdGo!lC$O8+P!38Lqjh#e8u+JU91_e*Wjr{||K5Mdb'
))).decode("utf-8"))
_SEAT1_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
(
    'c%1EBO>bOBlKd+M&pw!vt+Dq;OFbiEXj7o56=ns&FfcP%U@?2}?rkyueMvRD-$zAeL}b-#k^`UA>Sp(=kIbyh$jG'
    'cu|9AF}Uw`|rzy0sozkT)T)7g(7{_@Mao9j0pUf-U5{ngpWx4Vn`7vFvU`m0Z8Z!d3lXV$CxpS$?^@~4Zd`(Jx~{'
    'qgRfbMVRgx4YfDyBFUcKYPF1y=g}<|Kz9L)%DL`KDqno?C-z+_K&~)c0Y-;cNg#9-#`BBKY#u2zy8ntTc7{=^;h$'
    'GuD@{k`p+NUEk`(g`P13Q-TT}9e5O~2hs?jdoW=ex<VPPSx_<c2*EhFs_fML=M2|oGg7Nsne4GdV_~G*E%`bQVzx'
    '{C7X6aeY_pDi7UA*2+Yium=;fwcMyL#x|XFuOgq7*;<j|*YcAKrX#AypT*yPM{rlZ3s#I4tk}J@Tx>p9iaYoa<~3'
    'c+nqTlE>{XTFF7rz_SE0q&@cd8^KCW%eS0+BRoBin~Xrds6cEUhFW>-`|A%!A%TlJ2~5Z2kWS3(Um~*wQ#1QHC_B'
    'gJ0(sF^5<V48XR)b`v}iLt{F<?z$5%*Jwp!Nd<4I)p`rP+0xSZ1~?Gb1Z55{Jp1n|v=mj&a67Hzg?{pa5)Me(>I_'
    '+fDA$`T00etvQ%i#Z9Pw1#Bk=6g5|VD)PKh=aendX()&q61hvxv#ITcCT-L`Qz^9_VViTKibvQ>^Ty!{h$gXM}w-'
    'IC)&{A2&AFYwJS^nYL7S(I-U*>px;HRyE_#l(0fGx{><KIwnj`1o1X9&?-X=*^#wMVX<3F*1fa&Nfxtl&y*KelPs'
    'A97`oT|!6F*;1oWzc!Ods$tx`!SgdY$1Go=%q$o`+2JfysWFv53gRxT^?vB3Q%@ySMh33!|Dx(&d5Z!Tm5{E{`?b'
    '25kw^Pqt`8!F2~~h=arvi!vH(w1)Ml);0%dShF7)5npdO5c}9(9^mVQz<Kk@``ep~k3a5iZvJxjzn3RH+}E!*Jmp'
    'V#;GgE~KY<%?#2{uO;>=Erk1;~p>nWHA9vUplUqnmN>q`g``Pv%y!CJYGq32I{<lf@`+TtlYj?sM$&Q#sRnN$Tot'
    'Zy@$M3Q<M<@7eV-(atyLkUS<)ix3t1fZ>jIpN78kh}^Vm+ctddQ786XS=c_FyZNlqAO&3G!d1e!_#roe!sgqr*(C'
    'F(_)A1eZP&(VBM^SaL5<Exw!fF@{tS|b;MyNcr3keeZ{+?alSb`G2)*I#G`MQg`ONot1rpyE5RbiJcvQMG2|#-^9'
    'G#Fvz&Oe93%F$#|jbjW6TQAer15S13kOYYd$z9$0O(uduOHxzKL0&Cb08u)eTb4)(R6;($3b?dExs){SFs)e7Zw^'
    '4RRRy#2U!3rAGuYffM^jDaAH*lzKNLquF+BMJmk3o&+aFpNL~mt9*n&YTHoEuZ3q$qk%D8Ha<N&27m3?3pH8jV$z'
    '+^T!*l-Jgi6XWKfZdv=Q&F*~t#})BssFoYA3KG}~vQ{>#fyAY6|n2#W9{pRGf*h!)*Blt3pM|Bu3)Yz(b-tW(QA3'
    '>0*6F1|eoE7%bC>RzCHhhPG)HwR;7S%+`XcFvr80->La#D|>`AFr>kj;8}WIQBO6evj@Bwl~c|@#g0GogjG(qF`v'
    'ii{mFY&ExQ~B4Uu&1E4HvpVnBxI-nQqSow(&hyZPv`IIz>42mrxr)c$CY<@`)nTExKP99v{HZ5PBEz$%LwFqFP*5'
    '_2O{fccBzk4w%8#!q(RPY}%1s5`zG0e7~$IDPz^yK6iSJZo+`tp>hUS9e-W|)oKIY0y+g3c4ujevzA;%Z+0*JG_8'
    'JUf&XnHjfn4k(hoxC(gnGRMA#I;~Xt)`uE4HVRngWgPr`VEAND6uZ}yWOsv|1dHmfn2XJ<M#G??zIYD_KUY%)7Rc'
    'Oob<bc@7l=NT803P}AV=A}+z!mNk7b|N%SvOqQ89^xJSL&*;)`0oJojJW4ndMgfgZuFDQ1|;jt8O>lsg{~wrjji4'
    '&JMXd8=nB*Yy77o6A21=lEt^V<MGgr-m_t@UCsir8Ppn-l4E!0;s+4Kq!+~mt2u~7`8<adibP`DpxC0C(EuMu?SD'
    '65h$_B5EclJP!TdUBt(#-x|wGJr#vF=3tL9S!&)3kHm*}@HBmjOw#fq1b75M+a*Hlkg5bHBcx2e6+)9wra68yWl?'
    'hpwC=~60fq<w|<V?!MBoxBhlnFPzH9MT56|!r*RaQL=AcpoQ<C`9Oo-5r@1(B57;Ms#6%4jZ{;E`OK;%860Hlpl1'
    '#f>rnbg^L=L1)HgrD-AQO`m^m2~#Sz6qBC7F2XH>Dm&I9HqONAx%Ew{L>IYAj)^MJzQ(8IkT{nF^7N=4Gh6)I12|'
    'mg-+Z2jPCs2<{rT*^OA(5v&PV0<R+F!WNePo)4|QIwOvik`X{bZur7<pu5LRrIjS~qua;Pyj`e?#!hs?vWavel7e'
    'v&XmBpUQE{&AJtmDnGKx}Jar)~H2(4w)dj7Q>B-od&LFQ6A^<&ZHKn??58NT`>DL+R?#BFm}~PG&Y8tLdAQW*pT>'
    'a?q_B_>!HGSH{8mX4(Hpb5ZgT&vYxGQ#+ne@t)+3X1QcDQDi%$_d^BE-Jfbfo@$B-G<~e!HDITlFVq{vZN19tK3&'
    'PY~V4<`U9#?5ha*7&w?5mX<1~{jPHSd<FiG#Q)d9>$Ve^G?Ti0HPXiMI6Z!?is>G@mRIYeIA0tjW9jYDB5H8{ncM'
    '^E_pi$GVVxLHKz|wU(?@ZlVXb8RDVMW6dvzLsLGMiH%EC5o1L*h?9+k95~05mVdFK9X?Css-`g@KM&;srN+qtNVE'
    'i^51Dlu98ivx!eW8<-q7<jnQ&K0A#kJYOqK|2$JQqY%qzx-18P>53~xN4Z)HrTHYYWchH=>-w%o4rDnwpf;74Tyt'
    '>D9&RO;r*#33m<5W@^T(SJ5}g%5t;tB2DQUF5j_M6U#D0BCXp5|;0*YBLh!Lxp4z#YefZI)k|NjGIx>IXirD%W)x'
    '+6MiwjCe1COg&{A`<mc`R;Xu=u4x_SF76k>5NchdlqN%t>5-JGv%GsT5lLl!J8<BUkV>*#P{c8-u2;vRr-N?5h4~'
    'nE)U|ZUFdNoz*_aJ53Z*Spr%O$tRf1@05qU+wZCI&xPm25@kVA6>Cb;=<@{lpW?v$8YOpUe(y!(`*QHQDcgF0RZM'
    '2|n(_swaiBKCY5VM02HEiajw;mYD?b@`>XQ;O%#Fm3h)j4BW#lL_5qNafQ9Hq85$p5iksere7QZ`=VDG(Wz}eIsg'
    'Y=;-OA~$MSt5Om61L1$f<}f767Sr>n+E%2`I*B&oAhpG2kIf$7K-&Q(XrT9tR7a7eO=m^sUGAyB=*C9~GbF~?ESV'
    'P!8!Ejz)1B^2@qby&F4D3AJeqH*1GU}0rF`M`)cT@CjIGA!(?lZJJ~F$~E1`XOMj%+S_T*caKZLd*4b+y#bOPh6Z'
    'vhZQbXe0xu%g$~3%h7^P!({bKV%uzEM2p!?b9o597+Xj5IkfMS?QLkcU>sv8oH1^dL365}d4UB_X7*(up0NhQe;?'
    'zs(Uk)iGA|4?-m^NHO=Os%$uVz*fy!?l=j_J-zwN`46T{LA;`x2@r0c7w8ED3Y(-|lwr&PYp%mWH-5KBA!_-*Z%C'
    '-7nllMKXTe%i#SrDuR%eg;>1^wFy0bDUnR8f;Q)aAO>g*2uW@rEFscwpmWCxDd^nU!MjbYT+f%Pr5SXmGw|$0MM@'
    'B$q2(Ryh+sQ<{JoVL4llOj3_yk91!0|pyHm3yuwqTbakNr(?PWK#Y~dO~<p@gyp+f;|S|Q|N&ZSdilJmE6s)JoJ!'
    '}XpTB+|)|iGL61KpHe)JEE7LwemrO9Wx$KoAVM%UO~Ba)LG_i=1@RJf(hLOs?otlx$Q4G-IU=wOOxbZ0}xKJ-bIA'
    'aAsO+p(*LvLbkIlZfR`&jGw>jU6N96;4`p8(Lyv94#8?pfH#?;Df^x%2(AAIPI+%Aga6e1eI~y7s*2wEnluIL0DZ'
    '>;1m_*8oFdUZVx<v#Je_p|;3Vl#~&z4PRSc_JtPTkpn#F$f)_E2%SE@VwEBEema`lv^%CGE%L9s_MVd1Iw5`9?{^'
    '`J_lj#yFo5vFI7miByNAi$($M;*b)~t)*LpG9%ATTgy=-A++Ek=K!c-y&`I$R5Mru3Noqj>Pqh8y?13f&u9!DC-j'
    ')0(=kG38$vD`Cv${w^rE>>+}(DE*g@u@h*z&_$wSY%J<L<DyVBH)cXcPyZq)U0o0LCLBDw1@RVi4fq6LV=iU*JYA'
    't!c(e+0I%>2OBBAzgtWkx#D|VQ`5el?otGC~y&UOwL$n+;JoXMwx-ZHPWP#>NiOV8X!rPTd(IL+3L^^`x<ozwmDw'
    '4f|`G{j6k0Zg78#Ph4rJJIC_xsa?%f3Rpx3T)NETCqlL70s3j60F*a69nI=7O1f3R5-x~0Wal>mrDxq&!Juhw1Vm'
    'e|y9mTHCg|N+P940XzG5~|AaKFWTfBbS2LRvmh6prcXkd!vlk22M+a8`6Ar9>?#d5OTS5sQi!C>SOvOQpMa6Hl!d'
    'U18}fIs%4p@+M@&*$juy!UY6O$){kd==cxn$!R@@2tiD8J$4?XFlFfMYEDH-P<1AP*-DLS6hHapb6%5kvzN+H8PX'
    'h!+5PC&shSn)Xr&%h6WOxOnu~H6zf)cD%5dqH4{e#@G|(_Hm=Ib<FBii=63(U;;4g%7GZ)(G0zu#%6Qv)s4@G4@?'
    'b5qheRqx&GJU|S_T4BUz_tJA3D%%JubMKU(@t+q*-S9%MP*PT!y>WRaazr`t6a=r#ANxmf|u7{8HNWG^(+);+EEQ'
    'Pp!O@8humd4x?!$+az?3_43Cg5GDAQ@&Br3xly#SudeYZ%PF>?Y5CpFMLZU+PQcv+_F8+0eDEf{-^}LEDb$m6*u-'
    'I)K%ZN(zO3{RowOi2p4C?3*p(6+e<=du7r54(8nH<UNm01mBG_OQ<g@RcmgGAlXw!|dWykcM5sRD&f4Qb|x<}r9%'
    'fxESI`~<H7aVNT!O|O??s2yAbX+=pOg{_U6L?9%-a3!09g75c(L2*=bs2s$Q&qzU3is>`INEmJeDQ3%wljv2_RH;'
    'u;<Q$4c`l+ZLG7(Oqg!$f6oT@@0wHS`V841Zo5g8T3SQ2s8-Aoh=Q!0oGRvR{Ab}GV%Em;y8zm4a*{91bLdIj29E'
    '#&F$<BK4mHPF)7*?#;-LwKeOUru%5o&o=;+$GvmXpJK+K8%@AaBz$7erMSD4!TncWeE%@<SLMEMEIqfhv{cXxn(V'
    '*Iu&(J{E-<{8lt#9{j!wAK#CQ7_z)klkZ*&hzrcMO6<{k!33uBBeP?b?KV?%!$!twd8tTM5D{@~dFjNknu{$@J90'
    'n+l%u5&(KMO{P*TM*Gr1Eo@lqhrr201gIal%xyNq0++Jw<+Ko_3~4snB3akCIH&JgSz01(~wj(4VBQ7tuuXL3-eH'
    'cNCAFzz9K3m9~9(@hVa8jt1a;ecQz4(n0_j!LuGO`0z@>sla-TK~(4@s7gA`qh#Zm`#~LaH(qZJ><Mo^S>cBHJpG'
    'JKM*Ez=<xu-RW!fnd=vbk;#`iBypK%8DW?$s)bydcllWB;zKwZ@`Z%~!~u&oA9(+$~U<~fmWfh;RZl2k)BvDA~U='
    '<Z0_DV|YX!of!{Y1!gxb*tkSX?aRCzgG4RpFAD`&@N5=c0GgvrKyK5`{%(omBv<K9csmSu?c+<Q_*F{J`Saixhtd'
    ')rF-my>3lLTKjm7ThQJqbeM+@+ZV{%=&qL4fuJ%(HY$|l#13G3ty3NHkL>``BUTZHnyy;^FsBuHPA*i4v*)n08w|'
    'bHbGE(>`3fREP(@;fPYe;KDd9Pq(JTa0$2t6==Ok0&|lvgi13S%XnILFm7Sdw?q(%=Lq=O@tQ<fs|_)>yrP3l*)Z'
    'BdO#zfRavmck|Ia88o#6C;%iDd~^AyMmYF3gmE?v!j|kCz&q%XpXj(){O89Hmsf9oxeHuwKOD3K-yFXI_5)*Td_t'
    'l4`tH5gyD8S$zehu)B#^GSc8Q@*bFqveF{fmR(xt2}qv;mvZ<WI(CFCtIhJ?SS;YyK>56Jv12iYh?Jh>%Sk`R8EH'
    'I;BpR`l+t-2Kab=n0XP^Yw!t;W9q{8_YQpICXtY8GcF&fsp0zt(T`TezyZNtw_X)AHVf%9mQ!%fqSkSEZn|FQYa~'
    'b?{T3jc!Uk%#<7EX0O!IgYO@NON<Gpz&M{DB35!nbsU98rBy;2j!)=q>JeSS+gbeVI@39yB#dz!b;tZ!5yKyNX`n'
    'qxNo*1MI=rR&iDU;$~uDoocUBC%(gQD|WD0hllB?0xM{Fniy%rF?BRfm~iYQ`fpU3E9WPM`-{0S`rzcw%}r;J9NY'
    'R+QT0buq}!uvj?jhyWobh-aYQp4H)9pUmc29Ru^NcQ>WNId<<vp!ql<E-IIcdwd`x0Vn5+vVE$HT+Ut9Z7@q6r5R'
    'NGuFxh+(I3LJn>}|1I|0)i<*g*jR9}@eTXD*1GICXJwoexzA{OL0bULGknW6O^s>@V>+I<aTk9+9xS%HSe<G1d|)'
    '|LqmCv4SW#S{vJ5}cN`rWLoOYAE>btI_3cA_QO)O+wcr@fA8sQ^mUz^VpvQwQ!oOx~gNM1*TTLj!kWU8+l(kk+_='
    'Q9pA=H016nad(3L%!yBV$?%^w@-KzvR<ZHxDn8JNME``wErjHXNXAVeHx^}S4Z6ay&{>*aq9)k>Q2`pP)EhbiX2n'
    '3!E<f3}TW+}nWT<#E%8`L)gdd}P~aSjbbK4P9lS&H*cZ1GZNQx?lT%SC1j8)jFBIxK1&vdK81alI(g@q%(f+$Y~p'
    '3<gD{ksQd0mttnk6cz*I*Xa-;^q>>L$}Oxao@ji)o#?Sb2J*nNYMT8>b~F~Ng3*Bk$D1ppzf1T^Ea#(0xDtS$vlj'
    '|?hIBQsAvJwvUS7_{AvNjJExjo_FI<<VEnt<_2_`6bu*6pD?P-_>H0>39bT?>t$PR_+%?aP_Dp6Ozj1Ri11asac1'
    '%%liQ5YHjL2ETTyMmByG;UTjfN>I0hz!)1ODb(jGaYr6$7*#?haJO<HNN{7t@j<vN~KWoqW|LZ8ypUvL&<|;P+AT'
    'p^fMrU3(4W12rtTgpkj9vFG-!9Xea8^C_>}Y-x16Ro*}w-ffj8r4(tNt0i)2oQnSaYh{VUdg+RoRb9m6|saGa=Xa'
    'bXXmb<I#pU=KrY;ZWgs+L1<&;$tvNkjGJw^?1701$MCk!dmzPBc#+`V--#V@g<RrQlU21TE_rgdXHFA`FhC5GO{k'
    'JYi90?$`jqq|GBMnQP1fH>P5JZ9{wIfq+WO4q{PHm!)XPjg%DTu3|>yg|STrG1?r{$MM`W4eBS*Yfu#Ln7~F(YS$'
    'PV{nLWDuO<fZZk@&;S4gOXrc-V=xl^H=Q(kWkVU>L>RouB5Ewr&I`*m!9#BxtmkL9=^a1VVjS;L^X3Cj;^c6b$1r'
    '_pk8$Jx{fh)y9eM{<IuH4*Vutn0Gp!+<>EEe*+Q%J*C4gcOTNOu<+6sw0jhLz~Z<zw2BXKLBPSZBOqDR+Lh|zkzc'
    'tB7>pH{m@mgvRZ!cBd(*FED0ffc0bdyYZ;_@A6ILS+5Ssl@td~Zd`4{{pgH3|0%A3Zx_pAR3Mq|v`KLz3XooY|-^'
    'P<Of`eltsq7Oe*s2{p=-DImSJ3-tpaYwCGE<z%ZQF(xnrH~MgsE3S%RQZA)`OHqBf#ja+y|l2w8$A8oozu}Wnn*Q'
    '>>#xUb9Q?*n}CGkb`N#(riBKt1Gn#i`0A8Q<f;q<g-ISz-Nf{srkhe5^2P<lQ)Ks%N2i#?z01)N;w5W^*~r<aMXd'
    '&k&#1AKcQ&$5Dhb=eZW~h?d!pk}n2z`v?oL5Smf&x*i0U|SC#{0a4Yr`gSTnk$m^^JYPN6!Xz*Ei13u+DV_kzJBj'
    'X);c%(*|vV#W)1rYqf1EgQ<uxG2<{79{*85_g6SYAGLNFyVO{RZm56EvvYg=5##oIDJ9|{nYd|_L2zrKf?xOz;<0'
    'wGuH3I2xgh2!tgAyt|nGKfHf5CjDf5(?wZa(NneVz*`#l)YjjA$%(`?cH?Q?}AI!#hHLKJmVSD9JsFr<$SHLRFG9'
    'g;4LXY0R`()u)`lu(*Xr39ZGNYL__-X9$7Ib9cbSA_+XT+yq97i+tnRqz>acVYkP7!1+6&Q!MyN$*WVz33&IZ<Yz'
    'L{P3U_h1WFu#DbR64hHae}GG>_pXL8M~_Ce8G~Yj2dFBg6g?2NN>t%^*+Q8uslrb8YY_E4AS`F%R_Y(&D~6PJ%3B'
    'HWi?>Lwu!SeOxmVPCHE!QxXmyN04X{&4K>(Ufnqv{MIsV`}HmM+vdIS&Ek*zlR`L;h$4@%{wqTzh-Dx)}<25pVi8'
    '++!l<<4NK<dPodFRSN+MHHt=NxkPsN(t|y{!uJ}Z3I&mK?#=Zrf*D|n_t{VVQGlE^oCE+8|VEQI{bAGn)tXY+6%R'
    'TX=salie;(E7Ha%Y#sC+Kz{jq{XV*NPpD#Xx$HmeBK0B)4lJs}#E4K&2RP4I!jrz96jaCsN2EIz_0m62%J<&)6?i'
    'FZ)If*e37E;V?Y}AqiL}-q*M?q2u7Ei8Yo|QhW6f(-$HFA$uX0wH0slP>QBM24(N7*>6vlsFBBhgw@l#1L4|IXC1'
    'kE7P(INnHbJ7~aXDzs>$EF~ta#1{#Hya4Xms&6a0QkCW=TsEOFk%eeyVb{PGWisbgGj(=t9lce6z#(>F8N^&j=U!'
    'HM<umLu>n6E*Ii^DNvR+X|ToScgCSakI8%fIEg^`;V&R(hBaU*nwAoA%h1e1Vk2V1BYEOLi^>a9f~mIRym9xFD=S'
    'gV=CykHq-q&#y(t(%|rA+0;8PL{kZXeUrtX{24NltF)OJIT;;A{ks5Bn)Z=4xznQvyp-<#R(v*WmPDWi9@QE7Of|'
    'WKt;+g71Q3f^&x3lRJ^g)1)A?UpQ`Vu>4Gt&?$XUlQFP{GUx$Y@*6M7g>g7*S%;gkws19i7ZI$q+aY2VtL$i`jk_'
    'RJ+1Qo>oW<Tg9%Xi6-JQ{%I-vYAm2|?_DrQ0)#<*VOI*=<OBU7a5NtX%)C)s`6!vrxjrfj5#z8ZrLi9bw_{oVGCf'
    '^hUV$2y39Ff$RbWgj&drp*A8#jkpl47jCsK-b&GE%S=mBVqIH<-RH4)=HgtN076#~Iq1o9zDFv*+SD88qcVKMzA)'
    'w1(H!HUaLpW})~L9StEOR)Y^rpdmd6WY%ibcf<0i{PYR#5+V@y=qVWTNfAkGQ$e`td%;E1R-fE7d4L<hp<5?LW(q'
    '&tz2p<|uCjIfU>nD&d*gd*&44U8iXi42$Ypjerg`v$=Qg+~SSq^C9?YC%>jwvK6JCoi}cG$C{j=+x9K135WBI>Mm'
    '&=cuMoZA^G^3LRRO|3DyA6F0}T<95^GQW39CX%nJb#wANIw2X%d(+XqZ%#1(+-g%Qf(K49LVcIViIiU<0erDKmVw'
    'whwlD&h^oh^T~T~;qOd_<1Q(FGeL1ei+7LsoW@xrxEnPGp<LQmk}<0^6hq1lO{MZld+H1uG`VF(qg%)RtVZQiqcJ'
    'ZNl~n@kWmBQ33bI+_NKWKYc*Ex0L{7KWm6KKJk!%lfRT8-xT|_Yx5}q5q;h}Bcnzi!Jc+ie$r8qOix^i;^`-FsZE'
    'F%Le^kKH1{-Ifh^NFxLS(zhvRq12T5EtBO@2c_a!al>!v6)ZIoES1bN~r6-Y_>tx+6NB{EmNX=Ruq!qwDoRb+{Jr'
    'ij|~h++ko24wa_-k?B{)Q*|MNPcjiEaSmcNRA;yW^0Av$E}0VpOWg70*p%;50AZzEH-%0sQzam*MQU<0%V=hu(o|'
    'd>j%03BlA_vs^pFuR4lJbCl`>engF<l*egMK2WHh(UU?V8pK)b{bB>_vV#KgfgO$9rkZpm3$E-Qfl{1)OrBIGsJ}'
    '@ze$DF{HHxvoOH~Qgl|ANd}{oA5t#3i7lH5}2PQjWfM36rv+UJ^b_h)LfPf3_#f)L;(?eV3E!?3&M%S{$DC6t&G7'
    'NgTy>nN&);*gh=U9^ZUcm?eGaGeRcoR9m@$z~;Clr-ljzz#Gir6rE5@Oj|NpwNJ#UyQAjr7X{^@`Ae&BOpEyCJ16'
    'a>YLeI(RZ}XOjihedE)Ree<9P{A!*4uOosO0_Xh+Jfw~&Cb8*h9d{IOky#I;y%Uyw)cP+#GfaUT+1G!~MBR#QfZ3'
    '+YY(BX?QTP%$i}&UuqG3m{Btt#efp(@Q=0SaZ=fG2uBFf-Dx;f7!>7S#$2GWoxw_I4akV1abqXD@6JuDzmaifz7i'
    '~KZbn!kX`aNO@m8WhT>zUq%!6$Go8Sy)jehvOeI%K!4{4T83-xdwC~jjqf<+31a5&-=NztpnkVUT6IrUGHMY>NCA'
    '}r=Zbq|r%Ps{%z})0{>^10Q47sYb9``Yv8ta=D3A4Ov-rq<vP6k!Ft+ye_H6C=eFp07l(mvy!MBBOwMUGn{rqDe;'
    '<0e#F%Cw*_t0`8$Eif#dI*$sZzG%!-g>2~qo>3=+tgfiQ8;yR%sh$#)-6o0}{7BB~a?wfeLIgq(HQAu<vOI2$e?D'
    '-vxdY2p_D|I)%_qIsNJnJ}mu+WRDOo2TdA(f&$u&|mTsbP!_>y(cj^Yj)u#dU>mA2XC7D;6pXxK$DV{Z4wW*+Hq1'
    'ctdgNG*ds;ohW;c4Hqf=RUbwX+VHu#9Xh?5PJPFd`u%}8FgNy(JIYoW)6DqD2bWUS=_8jPu>3B5$jOdJj^^g(2`Y'
    'vV`N!+N%4h4#398fw!t9U64s-9X@M#Wr1m$k@w^<Lu~aGDlyt68T6#z##pPuJ6jwE!@qP+col{lYApAU@t%fpjsv'
    'DRr6WR1fJ1>3WgdV20G99{4QJA0Npi{}Q#0#mvOFCdKRcLuZ`QoERaq(k!%+x_9`ow2M#~Y0IBn;p!2zRvOUGE@I'
    '!Ke#PIW>l}>JpyJec~((5VBoQ_!4oR<8o0Bo3-XPehiXgG0spZ+@WbemS$1k-GWC(AU3MpN<h#L9x=NBu~503w?{'
    '}l5|+c_Qe)V9sVYSpP^{Wt31N#ZS_%OjQrJ;o(wpIKbh)90vH>;-ds7CBjIuHs$Iv>2y!lrUUq>bly<gFq95~}KF'
    '{_MdUk=nD+FY0r1@Jhv)kIMsJv{kgPKC462WDtmByV<lKxjg*2D0KL;=IFBzw!<txpig1U&AH|mYML&oLk*g^2jE'
    '4q8J3KRN%P~yjnIrTQXIa;NOy|GQ760)qIDYBAAi5nk@978nC!vy|kDjGZGNwr^ahFw4g&{aMVj#*XaHFAc+NHN0'
    '5ME#@V#KoFr3T)~_LTzG_>`i9GUQvK*nit3)e`>CjQ38*g38yg7nRMMqyxGC36b9D-N>WWCje5lSAmZGF<na%3x#'
    '$%YZ84w_?BJJUrU$c2yyW@3`%!;P<BPDWV0)CgTfY|DZ8%!4)YP!7hxnX^8}-HT7E+xUd#9Jw@L!mO)bybK3NMod'
    'c+5AHC`fiJ1qy(N7xb9&q+m=$K#WrQY4GynLizn96pe?aT>YP}eT$pkibnyUcM!A2~op?mW&P5Wc&{rMl_={GqeD'
    'DBwp!5xO5Gq$E%4FzYZ)i<)XVfgT4!rCl_09veSfc66XgER@a@*=#(My|Ud1QsSy3pp9XKm7d9&;JisutnS'
))).decode("utf-8"))

_PRICE_FLOOR = 1
_DEMAND_ALPHA = 0.25
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _regime(configuration):
    interval = int(_get(configuration, "townCenterSellInterval", 12) or 12)
    return "rebalance" if interval >= 24 else "legacy"


def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _seat(obs):
    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0


def _farm(obs, seat):
    farms = list(_get(obs, "farms", []) or [])
    return farms[seat] if seat < len(farms) else {}


def _align_hands(action, obs):
    action = _copy_action(action)
    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor_action(actions, step, actor):
    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, actions, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game["active"]

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - transaction["start"]
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(actions, step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return _align_hands(action, obs)


def _shed_access_tiles(board_size):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]

def _is_shed_adjacent(pos, board_size):
    try:
        return tuple(int(x) for x in pos) in set(_shed_access_tiles(board_size))
    except Exception:
        return False

def _v26_shed_access(position, board_size):
    return _is_shed_adjacent(position, board_size)

def _manhattan(a, b):
    try:
        return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))
    except Exception:
        return 999

def _step_towards(frm, to):
    try:
        fx, fy = int(frm[0]), int(frm[1])
        tx, ty = int(to[0]), int(to[1])
        if fx < tx:
            return ["EAST"]
        if fx > tx:
            return ["WEST"]
        if fy < ty:
            return ["SOUTH"]
        if fy > ty:
            return ["NORTH"]
    except Exception:
        pass
    return ["PASS"]

def _is_thirsty(tile):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("consecutive_unwatered") == 1 and not tile.get("watered_today")

def _dist_to_shed(pos, board_size):
    try:
        return min(_manhattan(pos, s) for s in _shed_access_tiles(board_size))
    except Exception:
        return 999

def _water_optimizer(obs, action):
    try:
        farm = _farm(obs, _seat(obs))
        tiles = _get(farm, "tiles", []) or []
        private = _get(obs, "private", {}) or {}
        inventories = list(_get(private, "inventories", []) or [])
        positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
        unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
        if len(unit_actions) < len(positions):
            unit_actions += [["PASS"]] * (len(positions) - len(unit_actions))
        elif len(unit_actions) > len(positions):
            unit_actions = unit_actions[:len(positions)]
        thirsty_set = set()
        for y,row in enumerate(tiles):
            for x,t in enumerate(row):
                if _is_thirsty(t):
                    thirsty_set.add((x,y))
        animal_needy = set()
        for y,row in enumerate(tiles):
            for x,t in enumerate(row):
                if isinstance(t,dict) and "animal" in t:
                    if not t.get("fed_today") or not t.get("cared_today") or t.get("fertilizer_available"):
                        animal_needy.add((x,y))
        from collections import defaultdict
        water_groups = defaultdict(list)
        for i,(pos,act) in enumerate(zip(positions, unit_actions)):
            if act and act[0]=="WATER":
                try:
                    pt=(int(pos[0]),int(pos[1]))
                except:
                    continue
                if pt in thirsty_set:
                    water_groups[pt].append(i)
        free=set()
        for i,(pos,act) in enumerate(zip(positions, unit_actions)):
            if act and act[0]=="WATER":
                try:
                    x,y=int(pos[0]),int(pos[1])
                    tile=tiles[y][x] if 0<=y<len(tiles) and 0<=x<len(tiles[y]) else None
                except:
                    tile=None
                is_plant=isinstance(tile,dict) and tile.get("kind")=="PLANT"
                if not is_plant:
                    free.add(i)
                elif tile.get("watered_today"):
                    free.add(i)
        for pt,idxs in water_groups.items():
            if len(idxs)>1:
                for dup in idxs[1:]:
                    free.add(dup)
        for i in free:
            unit_actions[i]=["PASS"]
        reserved=set(water_groups.keys())
        for i,(pos,act) in enumerate(zip(positions, unit_actions)):
            if not act:
                continue
            if act[0] not in ("NORTH","SOUTH","EAST","WEST","PASS"):
                continue
            try:
                pt=(int(pos[0]),int(pos[1]))
            except:
                continue
            if pt not in thirsty_set or pt in reserved or i in free:
                continue
            if animal_needy:
                d_animal = min(_manhattan(pt, a) for a in animal_needy)
                if d_animal <= 3:
                    continue
            inv = inventories[i] if i < len(inventories) and isinstance(inventories[i], dict) else {}
            if inv.get("WHEAT",0) > 0:
                continue
            unit_actions[i]=["WATER"]
            reserved.add(pt)
        action["farmer"]=unit_actions[0] if unit_actions else ["PASS"]
        action["hands"]=unit_actions[1:]
        return _align_hands(action, obs)
    except Exception:
        return action

def _pasture_optimizer(obs, action):
    try:
        farm = _farm(obs, _seat(obs))
        tiles = _get(farm, "tiles", []) or []
        board_size = len(tiles) or 10
        private = _get(obs, "private", {}) or {}
        inventories = list(_get(private, "inventories", []) or [])
        positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
        unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
        if len(unit_actions) < len(positions):
            unit_actions += [["PASS"]] * (len(positions) - len(unit_actions))
        # precompute nearest empty build site near shed (dist <=3)
        build_candidates = []
        pasture_candidates = []
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                pt = (x, y)
                d = _dist_to_shed(pt, board_size)
                if t is None and d <= 3:
                    # check unlocked: None means unlocked empty
                    build_candidates.append((d, pt))
                if isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" not in t and d <= 3:
                    pasture_candidates.append((d, pt))
        build_candidates.sort()
        pasture_candidates.sort()
        best_build = build_candidates[0][1] if build_candidates else None
        best_pasture = pasture_candidates[0][1] if pasture_candidates else None
        for i, (pos, act) in enumerate(zip(positions, unit_actions)):
            if not act:
                continue
            op = act[0]
            # carry check
            inv = inventories[i] if i < len(inventories) and isinstance(inventories[i], dict) else {}
            has_animal = any(inv.get(k, 0) > 0 for k in ("COW", "SHEEP", "GOOSE"))
            if op == "BUILD_PASTURE":
                pass  # keep original build, don't redirect (avoids losing pasture slot)
            elif op == "PLACE" and len(act) >= 2 and act[1] in ("COW", "SHEEP", "GOOSE"):
                try:
                    dcur = _dist_to_shed(pos, board_size)
                except Exception:
                    dcur = 999
                if dcur > 3:
                    if best_pasture is not None and tuple(best_pasture) != tuple(int(x) for x in pos):
                        unit_actions[i] = _step_towards(pos, best_pasture)
                    elif best_build is not None:
                        unit_actions[i] = _step_towards(pos, best_build)
                    else:
                        pass
            elif has_animal and op in ("NORTH", "SOUTH", "EAST", "WEST"):
                # animal carrier drifting far: if moving away from shed and already far, redirect toward center pasture/build
                try:
                    dcur = _dist_to_shed(pos, board_size)
                    nx, ny = int(pos[0]), int(pos[1])
                    if op == "NORTH":
                        ny -= 1
                    elif op == "SOUTH":
                        ny += 1
                    elif op == "EAST":
                        nx += 1
                    elif op == "WEST":
                        nx -= 1
                    dnext = _dist_to_shed((nx, ny), board_size)
                except Exception:
                    dnext = dcur
                if dcur >= 2 and dnext > dcur:
                    target = best_pasture if best_pasture is not None else best_build
                    if target is not None:
                        unit_actions[i] = _step_towards(pos, target)
        action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
        action["hands"] = unit_actions[1:]
        return _align_hands(action, obs)
    except Exception:
        return action

def _shape(name, value):
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(name)


def _market_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _MARKET_PARAMS[item]
    )
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(obs, order):
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(
        _get(prices, item, _market_price(item, current_inventory)) or 0
    )
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _demand_per_day(obs, configuration, item):
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)
    shop_interval = max(
        1, int(_get(configuration, "townShopSellInterval", 4) or 4)
    )
    demand = 0.0
    for shop in shops:
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += (turns_per_day / shop_interval) * (
                2 if len(products) == 1 else 1
            )
    regime = _regime(configuration)
    if item != "FERTILIZER":
        center_default = 24 if regime == "rebalance" else 12
        center_interval = max(
            1,
            int(
                _get(configuration, "townCenterSellInterval", center_default)
                or center_default
            ),
        )
        day = int(_get(obs, "day", int(_get(obs, "step", 0) or 0) // 24) or 0)
        multiplier = (
            1
            if regime == "rebalance"
            else (4 if day >= 20 else 2 if day >= 10 else 1)
        )
        demand += (turns_per_day / center_interval) * multiplier
    return demand


def _order_score(obs, configuration, order):
    score = _impact_score(obs, order)
    if _regime(configuration) != "rebalance" or score <= 0 or not _is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    demand = max(0.25, _demand_per_day(obs, configuration, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _DEMAND_ALPHA * urgency)


def _rank_sell_slots(obs, action, configuration):
    action = _copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_order_score(obs, configuration, order), -index, list(order))
        for index, order in enumerate(market)
        if _is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


# =============================================================================
# Adapt-2-Survive — crops / animals / buys / sells ONLY
# Routing (farmer + hands MOVE/WATER/PLANT positions) stays exact tape.
# =============================================================================
_MEM = {0: None, 1: None}

_CROP_PLAN_UNTIL = {
    "WHEAT": 22, "CARROT": 20, "TOMATO": 17, "STRAWBERRY": 16, "MELON": 13,
}


def _new_mem():
    return {
        "family": "unknown",  # buildA | seb | straw_flood | mirror | unknown
        "locked": False,
        "price_hist": {},
        "last_step": -1,
        "seb_score": 0,
        "builda_score": 0,
        "straw_score": 0,
        "opp_has_se": False,
        "opp_anim_peak": 0,
        "opp_straw_peak": 0,
        "opp_melon_peak": 0,
        "behind": False,
        "mode": "default",  # default | anti_straw | anti_buildA | anti_seb
    }


def _mem_for(obs):
    seat = _seat(obs)
    step = int(_get(obs, "step", 0) or 0)
    m = _MEM.get(seat)
    if m is None or step == 0 or step < int(m.get("last_step", -1) or -1):
        m = _new_mem()
        _MEM[seat] = m
    m["last_step"] = step
    return m


def _count_crop(farm, crop):
    n = 0
    for row in (farm.get("tiles") or []):
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == crop:
                n += 1
    return n


def _count_animal(farm, kind=None):
    n = 0
    for row in (farm.get("tiles") or []):
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                if kind is None or t.get("animal") == kind:
                    n += 1
    return n


def _opp_farm(obs):
    seat = _seat(obs)
    farms = obs.get("farms") or []
    opp = 1 - seat
    return farms[opp] if opp < len(farms) else {}


def _momentum(m, item, lookback=24):
    h = (m.get("price_hist") or {}).get(str(item)) or []
    if len(h) < lookback:
        return 0.0
    base = float(h[-lookback] or 0)
    if base <= 0:
        return 0.0
    return (float(h[-1] or 0) - base) / base


def _update_memory(obs):
    m = _mem_for(obs)
    try:
        day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        ph = m["price_hist"]
        for item, p in prices.items():
            h = ph.setdefault(str(item), [])
            h.append(float(p or 0))
            if len(h) > 48:
                ph[str(item)] = h[-48:]

        own = _farm(obs, _seat(obs))
        opp = _opp_farm(obs)
        o_sheep = _count_animal(opp, "SHEEP")
        o_cow = _count_animal(opp, "COW")
        o_anim = o_sheep + o_cow
        o_straw = _count_crop(opp, "STRAWBERRY")
        o_melon = _count_crop(opp, "MELON")
        o_wheat = _count_crop(opp, "WHEAT")
        o_quads = list(opp.get("unlocked_quadrants") or [])
        if "SE" in o_quads:
            m["opp_has_se"] = True
        m["opp_anim_peak"] = max(int(m.get("opp_anim_peak") or 0), o_anim)
        m["opp_straw_peak"] = max(int(m.get("opp_straw_peak") or 0), o_straw)
        m["opp_melon_peak"] = max(int(m.get("opp_melon_peak") or 0), o_melon)

        straw_px = float(prices.get("STRAWBERRY", 120) or 120)
        straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)

        if not m.get("locked"):
            seb = int(m.get("seb_score") or 0)
            ba = int(m.get("builda_score") or 0)
            st = int(m.get("straw_score") or 0)
            # Build-A / THUNDER / COLD / Roman: melon-12 open, cow-led 2+2
            if day <= 2 and o_melon >= 10 and o_cow >= 2 and o_sheep <= 3:
                ba += 4
            if day <= 3 and o_melon >= 8 and o_cow >= 2:
                ba += 2
            if 6 <= day <= 8 and "NE" in o_quads and "SW" not in o_quads and o_melon >= 8:
                ba += 1
            if 10 <= day <= 12 and "SW" in o_quads and o_anim >= 12 and o_melon >= 8:
                ba += 2
            # Seb: early multi-quad + wheat heavy + SE
            if day <= 5 and "NE" in o_quads:
                seb += 2
            if day <= 7 and "SW" in o_quads:
                seb += 2
            if day <= 12 and "SE" in o_quads:
                seb += 4
            if day <= 6 and o_wheat >= 10:
                seb += 2
            if day <= 15 and o_anim >= 16:
                seb += 2
            # Straw flood (Jonathan-like or late straw meta)
            if day <= 12 and o_straw >= 15:
                st += 3
            if day <= 15 and o_straw >= 25:
                st += 3
            if straw_inv > 10040 or straw_px < 100:
                st += 2
            if day >= 10 and o_straw >= 30:
                st += 2

            m["seb_score"] = seb
            m["builda_score"] = ba
            m["straw_score"] = st

            scores = {"seb": seb, "buildA": ba, "straw_flood": st}
            best = max(scores, key=scores.get)
            if scores[best] >= 4:
                m["family"] = best
            if day >= 6 and scores[best] >= 4:
                m["locked"] = True
            if scores[best] >= 6:
                m["locked"] = True
            if day >= 8 and m.get("family") == "unknown":
                m["family"] = "mirror"
                m["locked"] = True

        # Mode from family + market (sticky). Mirrors plant lots of straw too —
        # require price/inv stress for anti_straw so we don't nuke vs 14.5.
        fam = m.get("family") or "unknown"
        glut = straw_inv > 10045 or straw_px < 105
        if fam == "straw_flood" and glut:
            m["mode"] = "anti_straw"
        elif glut and int(m.get("opp_straw_peak") or 0) >= 28 and straw_px < 100:
            m["mode"] = "anti_straw"
        elif fam == "buildA":
            m["mode"] = "anti_buildA"
        elif fam == "seb":
            m["mode"] = "anti_seb"
        else:
            m["mode"] = "default"

        # Behind on cash late
        om = float(own.get("money") or 0)
        xm = float(opp.get("money") or 0)
        if day >= 18 and xm > om * 1.12 and (xm - om) > 4000:
            m["behind"] = True
        else:
            m["behind"] = False
    except Exception:
        pass
    return m


def _adapt_crops(obs, action):
    """Adapt-2-Survive crop layer: tomato hedge under market glut.
    Optional wider window only when mode==anti_straw (family+price locked).
    Never changes MOVE/WATER/positions. Never steals straw in healthy mirrors.
    """
    try:
        m = _update_memory(obs)
        day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
        mode = m.get("mode") or "default"
        market = obs.get("market") or {}
        inv = market.get("inventory") or {}
        prices = market.get("prices") or {}
        straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)
        straw_px = float(prices.get("STRAWBERRY", 120) or 120)
        private = obs.get("private") or {}
        seeds = dict(private.get("seeds") or {})
        farm = _farm(obs, _seat(obs))
        money = float(farm.get("money") or 0)

        lo, hi = 7, 13
        if mode == "anti_straw":
            lo, hi = 6, 14
        if not (lo <= day <= hi):
            return action
        surge = straw_inv > 10050 or straw_px < 100
        if mode == "anti_straw" and (straw_inv > 10040 or straw_px < 108):
            surge = True
        if not surge:
            return action

        mo = list(action.get("market") or [])
        if int(seeds.get("TOMATO", 0) or 0) == 0 and money > 200 and len(mo) < 10:
            if not any(x and x[0] == "BUY_SEED" and len(x) > 1 and x[1] == "TOMATO" for x in mo):
                mo.append(["BUY_SEED", "TOMATO", 5])
                action["market"] = mo[:10]
        seeds = dict((obs.get("private") or {}).get("seeds") or seeds)
        if int(seeds.get("TOMATO", 0) or 0) > 0:
            max_conv = 3 if (straw_px < 90 or straw_inv > 10070) else 2
            hands = list(action.get("hands") or [])
            conv = 0
            for i, h in enumerate(hands):
                if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY" and conv < max_conv:
                    hands[i] = ["PLANT", "TOMATO"]
                    conv += 1
            action["hands"] = hands
            fr = action.get("farmer")
            if (
                fr
                and fr[0] == "PLANT"
                and len(fr) > 1
                and fr[1] == "STRAWBERRY"
                and conv < max_conv
            ):
                action["farmer"] = ["PLANT", "TOMATO"]
    except Exception:
        pass
    return action


def _adapt_market(obs, action):
    """SELL quantity holds/dumps failed keep-gate (clogged cash engine vs mirrors).
    Timing edge = _rank_sell_slots only (notebook-legal permute existing SELLs).
    Memory still tracks family/mode for _adapt_crops.
    """
    return action


def _adapt_animals(obs, action):
    """Skip late BUY_ANIMAL only when anti_buildA locked and herd already full.
    Saves cash vs melon-meta without touching paths.
    """
    try:
        m = _mem_for(obs)
        day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
        farm = _farm(obs, _seat(obs))
        our_anim = _count_animal(farm)
        if (
            m.get("mode") == "anti_buildA"
            and m.get("locked")
            and day >= 14
            and our_anim >= 13
        ):
            mo = []
            for order in action.get("market") or []:
                if order and order[0] == "BUY_ANIMAL":
                    continue
                mo.append(order)
            action["market"] = mo[:10]
    except Exception:
        pass
    return action


def _base_agent(obs, configuration=None):
    """Adapt-2-Survive: exact route labor + adaptive crops/animals/market."""
    try:
        _update_memory(obs)
        actions = _SEAT1_ACTIONS if _seat(obs) == 1 else _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
        action = _weed_repair_action(
            obs, _copy_action(actions[step]), actions, step
        )
        # Adaptive layers — market/crop/animal only
        action = _adapt_animals(obs, action)
        action = _adapt_crops(obs, action)
        action = _adapt_market(obs, action)
        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }


def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)



def _v26_terminal_sweep(obs, action, configuration):
    action = _align_hands(_copy_action(action), obs)
    seat = _seat(obs)
    farm = _farm(obs, seat)
    private = _get(obs, "private", {}) or {}

    shed = dict(_get(private, "shed", {}) or {})
    inventories = list(
        _get(private, "inventories", []) or []
    )
    tiles = list(_get(farm, "tiles", []) or [])
    board_size = len(tiles) or 10

    capacity = int(
        _get(configuration, "shedCapacity", 100) or 100
    )
    room = max(
        0,
        capacity
        - sum(int(value or 0) for value in shed.values()),
    )

    positions = [
        _get(farm, "farmer", []),
        *list(_get(farm, "hands", []) or []),
    ]
    unit_actions = [
        action.get("farmer", ["PASS"]),
        *list(action.get("hands") or []),
    ]

    market = _get(obs, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}

    for index, position in enumerate(positions):
        if (
            index >= len(unit_actions)
            or index >= len(inventories)
            or room <= 0
        ):
            continue

        if not _v26_shed_access(position, board_size):
            continue

        carried = inventories[index] or {}
        choices = []

        for item in tuple(_MARKET_PARAMS):
            quantity = max(
                0,
                int(_get(carried, item, 0) or 0),
            )
            if quantity <= 0:
                continue

            price = float(
                _get(prices, item, 0) or 0
            )
            choices.append((price, quantity, item))

        if not choices:
            continue

        _, quantity, item = max(choices)
        quantity = min(quantity, room)

        if quantity <= 0:
            continue

        unit_actions[index] = [
            "PLACE", item, quantity
        ]
        shed[item] = int(
            shed.get(item, 0) or 0
        ) + quantity
        room -= quantity

    action["farmer"] = (
        unit_actions[0]
        if unit_actions
        else ["PASS"]
    )
    action["hands"] = unit_actions[1:]

    action["market"] = [
        ["SELL", item, int(shed.get(item, 0) or 0)]
        for item in tuple(_MARKET_PARAMS)
        if int(shed.get(item, 0) or 0) > 0
    ][:10]

    return _rank_sell_slots(
        obs, action, configuration
    )

def agent(obs, configuration=None):
    step = int(_get(obs, "step", 0) or 0)
    if step == 718:
        try:
            return _v26_terminal_sweep(
                obs, _base_agent(obs, configuration), configuration
            )
        except Exception:
            pass
    return _base_agent(obs, configuration)
