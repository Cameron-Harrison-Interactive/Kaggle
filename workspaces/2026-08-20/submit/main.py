"""HI_AgriBot_v30_AdaptiveVoter — v25 tape + adaptive enhancements.

Changes from v25 (ALL safe, no tape modifications):
  * Terminal sweep boost: d28+ sell ALL shed inventory
  * Wheat-arb opponent detection (Kawashigi-style classifier)
  * Extended animal-skip logic (anti wheat_arb mode)
  * Market: SAFE changes only (no new orders mid-game)
"""

VERSION = "HI_AgriBot_v30_AdaptiveVoter"



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
                # Wheat-arb detection (Kawashigi-style): lots of wheat + animals
                if o_wheat >= 20 and o_anim >= 8:
                    m["family"] = "wheat_arb"
                    m["locked"] = True
                else:
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
    """Adaptive market: terminal sweep boost + opponent-aware wheat front-run.
    
    SAFE changes only — never add new market orders mid-game (that clogs the
    cash engine). Only boost at d28+ where the tape is in terminal mode.
    """
    try:
        m = _mem_for(obs)
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        
        # === TERMINAL SWEEP BOOST (d28+) ===
        # At d28+, the tape is winding down. Boost any existing sells to 
        # clear the shed. This is pure upside — stranded inventory = $0.
        if day >= 28:
            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}) or {})
            mo = list(action.get("market") or [])
            
            for item in ["STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "CARROT", "TOMATO", "FERTILIZER"]:
                qty = int(shed.get(item, 0) or 0)
                if qty <= 0:
                    continue
                # Find and boost existing sell
                for i, order in enumerate(mo):
                    if order and order[0] == "SELL" and len(order) > 1 and order[1] == item:
                        old_qty = int(order[2]) if len(order) > 2 else 1
                        if qty > old_qty:
                            mo[i] = ["SELL", item, qty]
                        break
            
            action["market"] = mo[:10]
    except Exception:
        pass
    return action


def _adapt_animals(obs, action):
    """Skip late BUY_ANIMAL when herd is full + opponent-specific counters.
    Saves cash vs melon-meta, wheat-arb, and 4-quad opponents.
    """
    try:
        m = _mem_for(obs)
        day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
        farm = _farm(obs, _seat(obs))
        our_anim = _count_animal(farm)
        mode = m.get("mode", "default")
        locked = m.get("locked", False)
        family = m.get("family", "unknown")
        
        should_skip = False
        
        # anti_buildA: skip when herd full
        if mode == "anti_buildA" and locked and day >= 14 and our_anim >= 13:
            should_skip = True
        
        # wheat_arb: skip extra animal buys when already profitable
        if family == "wheat_arb" and locked and day >= 16 and our_anim >= 12:
            should_skip = True
        
        if should_skip:
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

# ---------------------------------------------------------------------------
# tuning constants (ported verbatim from rayk's public notebook)
# ---------------------------------------------------------------------------
_PREMIUM = ("STRAWBERRY", "MELON", "MILK", "WOOL")
_LIQUIDATION_ORDER = ("CARROT", "EGG", "FERTILIZER", "MELON", "MILK",
                      "STRAWBERRY", "TOMATO", "WHEAT", "WOOL")
_PREEMPT_ENABLED = True
_PREEMPT_FRACTION = 2.0
_PREEMPT_MAX_BATCH = 30
_PREEMPT_MAX_CLONE_DISTANCE = 6
_PREEMPT_MIN_PRICE_RATIO = 0.0
_PREEMPT_MIN_FUTURE_QUANTITY = 4
_PREEMPT_START = 120
_PREEMPT_STOP = 680
_PREEMPT_HORIZON = 4
_ADAPT_DEFAULT_HORIZON = 4
_ADAPT_MAX_OPP_HORIZON = 6
_ADAPT_MIN_EVENTS = 2
_RACE_STATE = {0: {}, 1: {}}
_SHIFT_STATE = {0: {}, 1: {}}


# ---------------------------------------------------------------------------
# helpers shared by the runtime layers
# ---------------------------------------------------------------------------
def _public_signature(farm):
    keys = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "COW", "SHEEP", "GOOSE", "PASTURE", "COOP", "WEED")
    counts = {key: 0 for key in keys}
    for row in (farm.get("tiles") or []) if isinstance(farm, dict) else []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (len(farm.get("hands") or []),
            len(farm.get("unlocked_quadrants") or []),
            tuple(counts[key] for key in sorted(counts)))


def _clone_distance(obs):
    farms = list(obs.get("farms") or [])
    if len(farms) < 2:
        return 10 ** 9
    left, right = _public_signature(farms[0]), _public_signature(farms[1])
    return (abs(left[0] - right[0]) + 3 * abs(left[1] - right[1])
            + sum(abs(a - b) for a, b in zip(left[2], right[2])))


def _race_state(obs, step):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    state = _RACE_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {
            "last_step": -1, "inventory": {}, "own_sells": {}, "shops": (),
            "scores": {h: 0.0 for h in range(1, _ADAPT_MAX_OPP_HORIZON + 1)},
            "events": 0, "horizon": _ADAPT_DEFAULT_HORIZON,
        }
        _RACE_STATE[seat] = state
    return state


def _shift_state(obs, step):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    state = _SHIFT_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "debts": {}}
        _SHIFT_STATE[seat] = state
    state["last_step"] = step
    return state


def _town_drain(step, shops, item):
    drain = 0
    if step % 4 == 0:
        for shop in shops or ():
            products = _SHOP_PRODUCTS.get(shop, ())
            if item in products:
                drain += 2 if len(products) == 1 else 1
    if step % 24 == 0:
        drain += 1
    return drain


def _planned_premium(tape, step, item):
    if not (0 <= step < len(tape)):
        return 0
    return sum(max(0, int(order[2]))
               for order in (tape[step].get("market") or [])
               if len(order) >= 3 and order[0] == "SELL" and order[1] == item)


def _future_sells(tape, step, horizon):
    future_step = step + horizon
    if future_step >= len(tape):
        return {}
    result = {}
    for raw in (tape[future_step].get("market") or []):
        if len(raw) >= 3 and raw[0] == "SELL" and raw[1] in _PREMIUM:
            result[raw[1]] = result.get(raw[1], 0) + max(0, int(raw[2]))
    return result


def _shed_access(board_size):
    half = board_size // 2
    return {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}


def _projected_shed(obs, action, mod):
    """Shed contents after the current step's labor (DROP/PLACE) is applied."""
    farm = obs["farms"][obs["player"]] if obs.get("player") is not None else {}
    private = obs.get("private") or {}
    projected = {key: max(0, int(value or 0))
                 for key, value in dict(private.get("shed") or {}).items()}
    inventories = list(private.get("inventories") or [])
    positions = [farm.get("farmer", [0, 0]), *list(farm.get("hands") or [])]
    unit_actions = [action.get("farmer", ["PASS"]),
                    *list(action.get("hands") or [])]
    tiles = list(farm.get("tiles") or [])
    access = _shed_access(len(tiles) or 10)
    for index, unit_action in enumerate(unit_actions):
        if index >= len(positions) or index >= len(inventories):
            continue
        position = positions[index]
        if not isinstance(position, (list, tuple)) or len(position) < 2:
            continue
        try:
            x, y = int(position[0]), int(position[1])
        except (TypeError, ValueError):
            continue
        if (x, y) not in access or not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
            continue
        inventory = {key: max(0, int(value or 0))
                     for key, value in dict(inventories[index] or {}).items()}
        if unit_action and unit_action[0] == "DROP":
            deposits = inventory.items()
        elif unit_action and unit_action[0] == "PLACE" and len(unit_action) >= 2:
            item = unit_action[1]
            tile = tiles[y][x]
            structure = {"COW": "PASTURE", "SHEEP": "PASTURE",
                         "GOOSE": "COOP"}.get(item)
            if structure and isinstance(tile, dict) and tile.get("kind") == structure \
                    and not tile.get("animal"):
                continue
            try:
                requested = int(unit_action[2]) if len(unit_action) >= 3 else 1
            except (TypeError, ValueError):
                continue
            deposits = ((item, min(max(0, requested), inventory.get(item, 0))),)
        else:
            continue
        for item, quantity in deposits:
            room = max(0, 100 - sum(projected.values()))
            amount = min(max(0, int(quantity)), room)
            projected[item] = projected.get(item, 0) + amount
    return projected


# ---------------------------------------------------------------------------
# the three runtime layers
# ---------------------------------------------------------------------------
def _repay_shift(obs, action, step):
    """Cancel tape SELLs whose units were already sold by a preemption."""
    state = _shift_state(obs, step)
    debts = state.setdefault("debts", {})
    due = {item: max(0, int(quantity))
           for item, quantity in dict(debts.pop(step, {}) or {}).items()}
    if not due:
        return action
    market = []
    for raw in action.get("market", []) or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and due.get(order[1], 0) > 0:
            item = order[1]
            requested = max(0, int(order[2]))
            reduction = min(requested, due[item])
            requested -= reduction
            due[item] -= reduction
            if requested <= 0:
                continue
            order[2] = requested
        market.append(order)
    action["market"] = market
    return action


def _preempt_shift(obs, action, step, tape, mod):
    """Clone-aware front-run: sell premium units ahead of the tape's plan."""
    if not _PREEMPT_ENABLED or not (_PREEMPT_START <= step < _PREEMPT_STOP):
        return action
    if _clone_distance(obs) > _PREEMPT_MAX_CLONE_DISTANCE:
        return action
    state = _race_state(obs, step)
    horizon = int(state.get("horizon", _ADAPT_DEFAULT_HORIZON))
    future = _future_sells(tape, step, horizon)
    if not future:
        return action
    market = list(action.get("market") or [])
    if len(market) >= 10:
        return action
    remaining = _projected_shed(obs, action, mod)
    for raw in market:
        if len(raw) >= 3 and raw[0] == "SELL":
            item = raw[1]
            remaining[item] = max(0, int(remaining.get(item, 0) or 0)
                                  - max(0, int(raw[2])))
    prices = (obs.get("market") or {}).get("prices") or {}
    shifted = {}
    for item in _PREMIUM:
        future_quantity = max(0, int(future.get(item, 0) or 0))
        if future_quantity < _PREEMPT_MIN_FUTURE_QUANTITY:
            continue
        base_price = float(_MARKET_PARAMS[item][0])
        if float(prices.get(item, 0) or 0) < base_price * _PREEMPT_MIN_PRICE_RATIO:
            continue
        target = min(max(0, int(remaining.get(item, 0) or 0)),
                     future_quantity, _PREEMPT_MAX_BATCH,
                     max(1, int(round(future_quantity * _PREEMPT_FRACTION))))
        if target <= 0 or len(market) >= 10:
            continue
        market.append(["SELL", item, target])
        remaining[item] = max(0, int(remaining.get(item, 0) or 0) - target)
        shifted[item] = target
    if shifted:
        action["market"] = market[:10]
        due_step = step + horizon
        debts = _shift_state(obs, step).setdefault("debts", {})
        due = debts.setdefault(due_step, {})
        for item, quantity in shifted.items():
            due[item] = due.get(item, 0) + quantity
    return action


def _observe_opponent_market(obs, step, tape, mod):
    """Learn the opponent's preemption horizon from inventory deltas."""
    state = _race_state(obs, step)
    current = dict((obs.get("market") or {}).get("inventory") or {})
    previous = dict(state.get("inventory") or {})
    prev_step = int(state.get("last_step", -1))
    if previous and prev_step == step - 1 \
            and _clone_distance(obs) <= _PREEMPT_MAX_CLONE_DISTANCE:
        own = dict(state.get("own_sells") or {})
        shops = tuple(state.get("shops", ()) or ())
        for item in _PREMIUM:
            delta = int(current.get(item, 0) or 0) - int(previous.get(item, 0) or 0)
            inferred = (delta + _town_drain(prev_step, shops, item)
                        - int(own.get(item, 0) or 0)
                        - _planned_premium(tape, prev_step, item))
            if inferred < _PREEMPT_MIN_FUTURE_QUANTITY:
                continue
            state["events"] += 1
            for horizon in range(1, _ADAPT_MAX_OPP_HORIZON + 1):
                expected = _planned_premium(tape, prev_step + horizon, item)
                if expected > 0:
                    similarity = min(inferred, expected) / float(max(inferred, expected))
                    state["scores"][horizon] += 1.0 + similarity
                else:
                    state["scores"][horizon] -= 0.15
        if state["events"] >= _ADAPT_MIN_EVENTS:
            best = max(state["scores"], key=lambda h: (state["scores"][h], -h))
            state["horizon"] = min(_ADAPT_MAX_OPP_HORIZON + 1, max(2, best + 1))
    state["last_step"] = step
    state["inventory"] = current
    state["shops"] = tuple((obs.get("town") or {}).get("unlocked_shops") or [])


def _terminal_liquidation(obs, action, step, mod):
    """Sell unplanned shed leftovers at 716+ (ahead of the 718 sweep)."""
    if step < 716:
        return action
    action = _copy_action(action)
    shed = (obs.get("private") or {}).get("shed") or {}
    planned = {}
    for order in action.get("market", []):
        if _is_sell(order):
            planned[str(order[1])] = planned.get(str(order[1]), 0) \
                + max(0, int(order[2]))
    for item in _LIQUIDATION_ORDER:
        available = max(0, int(shed.get(item, 0) or 0))
        extra = available if step >= 718 else max(0, available - planned.get(item, 0))
        if extra and len(action["market"]) < 10:
            action["market"] = action["market"] + [["SELL", item, extra]]
    return action


def _record_own_sells(obs, action, step):
    state = _race_state(obs, step)
    sold = {}
    for order in action.get("market") or []:
        if len(order) >= 3 and order[0] == "SELL" and order[1] in _PREMIUM:
            sold[order[1]] = sold.get(order[1], 0) + max(0, int(order[2]))
    state["own_sells"] = sold


# ---------------------------------------------------------------------------
# fertilizer crash-hold (small isolated layer)
# ---------------------------------------------------------------------------
def _fert_crash_hold(obs, action, mod):
    """Hold FERTILIZER sells while its price is crashed AND cash is healthy."""
    try:
        day = int(obs.get("day", 0) or 0)
        if day < 5:
            return action
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        px = float(prices.get("FERTILIZER", 100) or 100)
        base = float(mod._MARKET_PARAMS["FERTILIZER"][0])
        inv_n = int(inv.get("FERTILIZER", 10000) or 10000)
        if px < base * 0.92 and money > 2500 and inv_n > 10060:
            action = _copy_action(action)
            action["market"] = [o for o in (action.get("market") or [])
                                if not (o and o[0] == "SELL"
                                        and o[1] == "FERTILIZER")]
        return action
    except Exception:
        return action


# ---------------------------------------------------------------------------
# tetsu tomato overlay (isolate-only; the v18 three-fer rejected it)
# ---------------------------------------------------------------------------
def _tetsu_tomato_hedge(obs, action, mod):
    try:
        day = int(obs.get("day", 0) or 0)
        if not (6 <= day <= 15):
            return action
        farms = obs.get("farms") or []
        opp = farms[1 - obs["player"]] if len(farms) > 1 else {}
        straw = 0
        melon = 0
        for row in (opp.get("tiles") or []):
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    if t.get("crop") == "STRAWBERRY":
                        straw += 1
                    elif t.get("crop") == "MELON":
                        melon += 1
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inv = market.get("inventory") or {}
        straw_px = float(prices.get("STRAWBERRY", 120) or 120)
        straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)
        if not (straw >= 15 or straw_inv > 10045 or straw_px < 105):
            return action
        private = obs.get("private") or {}
        seeds = dict(private.get("seeds") or {})
        mo = list(action.get("market") or [])
        if int(seeds.get("TOMATO", 0) or 0) == 0 and len(mo) < 10:
            mo.append(["BUY_SEED", "TOMATO", 3])
            action["market"] = mo[:10]
        if int(seeds.get("TOMATO", 0) or 0) > 0:
            max_conv = 2
            hands = list(action.get("hands") or [])
            conv = 0
            for i, h in enumerate(hands):
                if h and h[0] == "PLANT" and len(h) > 1 \
                        and h[1] == "STRAWBERRY" and conv < max_conv:
                    hands[i] = ["PLANT", "TOMATO"]
                    conv += 1
            action["hands"] = hands
    except Exception:
        pass
    return action


# ---------------------------------------------------------------------------
# melon4 (direct tape patch: 4 LATE strawberries -> melons, rayk-style)
# ---------------------------------------------------------------------------
def apply_melon4(tape):
    """Swap 4 strawberry PLANTs (planted day>=5) to melons + seed buys + sells.
    Rayk plants 23 melons / 36 straw vs our 19 / 37 and outsells us by ~18
    melon units.  Swapping the OPENING strawberries collapses the economy
    (early straw cash is load-bearing), so only day>=5 plants are swapped.
    Labor (WATER/HARVEST/MOVE) is untouched — harvest on a melon tile just
    harvests melons; the tape's straw SELLs fail harmlessly when short, and
    the extra melon units are added to existing MELON sell steps (d13+)."""
    out = copy.deepcopy(tape)
    swaps = []
    for s, e in enumerate(out):
        day = s // 24
        if day < 5 or day > 11:
            continue
        for k in ("farmer", "hands"):
            unit = e.get(k)
            if k == "hands":
                for h in unit or []:
                    if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY":
                        swaps.append((s, k, e, h))
                        if len(swaps) >= 4:
                            break
            else:
                if unit and unit[0] == "PLANT" and len(unit) > 1 and unit[1] == "STRAWBERRY":
                    swaps.append((s, k, e, unit))
            if len(swaps) >= 4:
                break
        if len(swaps) >= 4:
            break
    for s, k, e, unit in swaps:
        unit[1] = "MELON"
    # seed compensation: convert exactly 4 strawberry SEED UNITS to melon
    # (1 seed per swapped plant; split the last order if it overshoots)
    converted = 0
    for e in out:
        if converted >= 4:
            break
        for o in (e.get("market") or []):
            if converted >= 4:
                break
            if o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY" and len(o) > 2:
                qty = int(o[2])
                take = min(qty, 4 - converted)
                if take >= qty:
                    o[1] = "MELON"
                    converted += qty
                else:
                    o[2] = qty - take
                    converted += take
                    # add a fresh melon buy next to it (room-permitting)
                    if len(e.get("market") or []) < 10:
                        e["market"] = (e.get("market") or []) + \
                            [["BUY_SEED", "MELON", take]]
                    else:
                        o[2] = qty  # no room: skip this order's conversion
                        converted -= take
    # sells: +4 melon across existing melon sell steps after d13
    added = 0
    for s, e in enumerate(out):
        if added >= 4:
            break
        day = s // 24
        if day < 13:
            continue
        for o in (e.get("market") or []):
            if added >= 4:
                break
            if o and o[0] == "SELL" and o[1] == "MELON" and len(o) >= 3:
                o[2] = int(o[2]) + 1
                added += 1
    return out


# ---------------------------------------------------------------------------
# seat1 opening splice (market-only offline patches on the Gbining seat1 tape)
# ---------------------------------------------------------------------------
def apply_seat1_splice(tape1, tape0, mode="s1sp"):
    """Market-level patches to the seat1 tape, labor untouched.

    s1sp  : d0h0 market = seat0's (4 hires instead of 5, sell/buy order),
            the 5th worker never exists (hands truncated by _align_hands).
    s1sp_w: s1sp + trim ~20 BUY_PRODUCT WHEAT units across d2-10 (seat1 buys
            23 more wheat than seat0 over the game; most of the seat1 gap).
    """
    out = copy.deepcopy(tape1)
    if mode in ("s1sp", "s1sp_w"):
        out[0]["market"] = [list(o) for o in (tape0[0].get("market") or [])]
    if mode == "s1sp_w":
        trim = 20
        for s, e in enumerate(out):
            if trim <= 0:
                break
            day = s // 24
            if not (2 <= day <= 10):
                continue
            for o in (e.get("market") or []):
                if trim <= 0:
                    break
                if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" and len(o) > 2 \
                        and int(o[2]) > 1:
                    o[2] = int(o[2]) - 1
                    trim -= 1
    return out




_ADAPTIVE_SPEC = {'seat1': 'seat0', 'race': False, 'hold': False, 'th': False, 'melon4': False, 's1splice': None}

def _v20_agent(obs, configuration=None):
    seat = _seat(obs)
    tape = _SEAT0_ACTIONS if (seat == 1 and _ADAPTIVE_SPEC.get("seat1") == "seat0") else (_SEAT1_ACTIONS if seat == 1 else _SEAT0_ACTIONS)
    step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
    _update_memory(obs)
    action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)
    action = _adapt_animals(obs, action)
    action = _adapt_crops(obs, action)
    action = _adapt_market(obs, action)
    if _ADAPTIVE_SPEC.get("th"):
        action = _tetsu_tomato_hedge(obs, action, None)
    if _ADAPTIVE_SPEC.get("race"):
        _observe_opponent_market(obs, step, tape, None)
        action = _repay_shift(obs, action, step)
    action = _align_hands(_rank_sell_slots(obs, action, configuration), obs)
    if _ADAPTIVE_SPEC.get("race"):
        action = _preempt_shift(obs, action, step, tape, None)
        _record_own_sells(obs, action, step)
        action = _terminal_liquidation(obs, action, step, None)
    if _ADAPTIVE_SPEC.get("hold"):
        action = _fert_crash_hold(obs, action, None)
    if step == 718:
        try:
            action = _v26_terminal_sweep(obs, action, configuration)
        except Exception:
            pass
    return _align_hands(action, obs)

def agent(obs, configuration=None):
    try:
        return _v20_agent(obs, configuration)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {"farmer": ["PASS"],
                "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                "market": []}

def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)

# --- wheat16+nocow tapes (override) ---
_SEAT0_ACTIONS = json.loads('[{"market": [["BUY_PRODUCT", "WHEAT", 16], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 1], ["BUY_ANIMAL", "SHEEP", 4], ["BUY_SEED", "MELON", 5], ["BUY_SEED", "WHEAT", 5]], "farmer": ["PASS"], "hands": []}, {"market": [["SELL", "WHEAT", 11], ["BUY_SEED", "MELON", 3], ["BUY_SEED", "WHEAT", 1]], "farmer": ["PICKUP", "COW", 1], "hands": [["WEST"], ["WEST"], ["PASS"], ["PICKUP", "SHEEP", 4]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["NORTH"], ["NORTH"], ["PASS"], ["PICKUP", "WHEAT", 4]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["NORTH"], ["PASS"], ["BUILD_PASTURE"]]}, {"market": [], "farmer": ["BUILD_PASTURE"], "hands": [["NORTH"], ["NORTH"], ["PASS"], ["PLACE", "SHEEP"]]}, {"market": [], "farmer": ["PLACE", "COW"], "hands": [["PLANT", "MELON"], ["NORTH"], ["PASS"], ["FEED", "WHEAT"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["WATER"], ["NORTH"], ["WEST"], ["CARE"]]}, {"market": [], "farmer": ["CARE"], "hands": [["NORTH"], ["PLANT", "WHEAT"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["EAST"], "hands": [["PLANT", "WHEAT"], ["WATER"], ["NORTH"], ["BUILD_PASTURE"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["WEST"], ["NORTH"], ["PLACE", "SHEEP"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["PLANT", "WHEAT"], ["NORTH"], ["FEED", "WHEAT"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["CARE"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["PLANT", "MELON"], ["WEST"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["PLANT", "WHEAT"], ["WEST"], ["BUILD_PASTURE"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["WATER"], ["WATER"], ["PLACE", "SHEEP"]]}, {"market": [], "farmer": ["WEST"], "hands": [["PLANT", "MELON"], ["WEST"], ["WEST"], ["FEED", "WHEAT"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["PLANT", "WHEAT"], ["WEST"], ["CARE"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["SOUTH"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["PLANT", "MELON"], ["PASS"], ["BUILD_PASTURE"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WEST"], ["WATER"], ["SOUTH"], ["PLACE", "SHEEP"]]}, {"market": [], "farmer": ["WATER"], "hands": [["PASS"], ["EAST"], ["PASS"], ["FEED", "WHEAT"]]}, {"market": [], "farmer": ["PASS"], "hands": [["PASS"], ["PLANT", "MELON"], ["PASS"], ["CARE"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WEST"], ["WATER"], ["EAST"], ["WEST"]]}, {"market": [["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [], "farmer": ["CARE"], "hands": [["WEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["CARE"]]}, {"market": [], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"]]}, {"market": [], "farmer": ["CARE"], "hands": [["CARE"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"]]}, {"market": [], "farmer": ["PASS"], "hands": [["PASS"]]}, {"market": [], "farmer": ["PASS"], "hands": [["PASS"]]}, {"market": [], "farmer": ["PASS"], "hands": [["PASS"]]}, {"market": [], "farmer": ["PASS"], "hands": [["PASS"]]}, {"market": [["SELL", "FERTILIZER", 5], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 6]], "farmer": ["PASS"], "hands": []}, {"market": [], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["CARE"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["FEED", "WHEAT"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["CARE"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["FEED", "WHEAT"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["CARE"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["FEED", "WHEAT"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["CARE"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["COLLECT_FERTILIZER"], ["EAST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["EAST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 5], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "WHEAT", 1], ["BUY_SEED", "STRAWBERRY", 3]], "farmer": ["PASS"], "hands": []}, {"market": [], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["CARE"], ["PLANT", "STRAWBERRY"], ["NORTH"]]}, {"market": [], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["PLANT", "STRAWBERRY"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["PLANT", "STRAWBERRY"], ["WEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["SOUTH"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["SOUTH"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["NORTH"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["SOUTH"], ["SOUTH"]]}, {"market": [["SELL", "FERTILIZER", 5], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["BUY_SEED", "WHEAT", 5]], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["WEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["CARE"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["CARE"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["SOUTH"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["CARE"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WATER"], "hands": [["COLLECT_FERTILIZER"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["SOUTH"], ["PLANT", "WHEAT"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["CARE"], ["EAST"], ["HARVEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["COLLECT_FERTILIZER"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["EAST"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 17], ["SELL", "FERTILIZER", 5], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 1], ["BUY_SEED", "WHEAT", 1], ["BUY_SEED", "STRAWBERRY", 4]], "farmer": ["PASS"], "hands": []}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PICKUP", "COW", 1], "hands": [["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["PLANT", "STRAWBERRY"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["BUILD_PASTURE"], "hands": [["FEED", "WHEAT"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PLACE", "COW"], "hands": [["CARE"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["PLANT", "WHEAT"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["PLANT", "STRAWBERRY"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["SOUTH"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["FEED", "WHEAT"], ["PLANT", "STRAWBERRY"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WEST"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["SOUTH"], ["EAST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["PLANT", "STRAWBERRY"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 5], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["WEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["PICKUP", "WHEAT", 3], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["HARVEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["CARE"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["HARVEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["SOUTH"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["HARVEST"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "WOOL", 5], ["SELL", "FERTILIZER", 3], ["BUY_LAND"]], "farmer": ["DROP"], "hands": [["FEED", "WHEAT"], ["EAST"], ["EAST"]]}, {"market": [["HIRE"], ["BUY_ANIMAL", "COW", 2], ["BUY_SEED", "WHEAT", 1], ["BUY_SEED", "STRAWBERRY", 2], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["EAST"], "hands": [["CARE"], ["EAST"], ["EAST"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["PICKUP", "COW", 2], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["NORTH"], ["WEST"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["BUILD_PASTURE"], "hands": [["WATER"], ["WATER"], ["PLANT", "STRAWBERRY"], ["BUILD_PASTURE"]]}, {"market": [], "farmer": ["PLACE", "COW"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["WATER"], ["NORTH"], ["EAST"], ["NORTH"]]}, {"market": [], "farmer": ["CARE"], "hands": [["EAST"], ["WATER"], ["PLANT", "STRAWBERRY"], ["NORTH"]]}, {"market": [["SELL", "WOOL", 15], ["SELL", "FERTILIZER", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 2]], "farmer": ["PASS"], "hands": []}, {"market": [["BUY_SEED", "WHEAT", 3], ["BUY_SEED", "STRAWBERRY", 10], ["BUY_PRODUCT", "WHEAT", 4]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "COW", 3], ["WEST"], ["EAST"], ["PICKUP", "WHEAT", 4], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["NORTH"], ["NORTH"], ["CARE"], ["PLANT", "STRAWBERRY"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["PLANT", "STRAWBERRY"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["BUILD_PASTURE"], ["WATER"], ["WATER"], ["FEED", "WHEAT"], ["SOUTH"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["PLACE", "COW"], ["WEST"], ["EAST"], ["CARE"], ["PLANT", "STRAWBERRY"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WATER"], ["PLANT", "STRAWBERRY"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["CARE"], ["SOUTH"], ["WATER"], ["WEST"], ["EAST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["EAST"], ["SOUTH"], ["PLANT", "STRAWBERRY"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["BUILD_PASTURE"], ["WEST"], ["PLANT", "STRAWBERRY"], ["FEED", "WHEAT"], ["WATER"], ["WEST"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["PLACE", "COW"], ["WATER"], ["WATER"], ["CARE"], ["EAST"], ["WATER"], ["EAST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["CARE"], ["WATER"], ["PLANT", "STRAWBERRY"], ["WEST"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["CARE"], "hands": [["EAST"], ["EAST"], ["WATER"], ["SOUTH"], ["WEST"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["SOUTH"], ["NORTH"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["PLANT", "WHEAT"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["SOUTH"], ["NORTH"], ["PLANT", "STRAWBERRY"], ["WEST"], ["NORTH"], ["WATER"], ["EAST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["PLACE", "COW"], ["NORTH"], ["WATER"], ["NORTH"], ["DIG"], ["NORTH"], ["EAST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["SOUTH"], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["CARE"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["PLANT", "STRAWBERRY"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["EAST"], ["WATER"], ["WATER"], ["WEST"], ["SOUTH"], ["SOUTH"]]}, {"market": [["SELL", "FERTILIZER", 7], ["SELL", "WHEAT", 2], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 2], ["BUY_SEED", "WHEAT", 3]], "farmer": ["PASS"], "hands": []}, {"market": [["BUY_SEED", "WHEAT", 5], ["BUY_SEED", "STRAWBERRY", 2], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 4], ["NORTH"], ["EAST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "COW", 2], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["WEST"], ["PICKUP", "WHEAT", 2], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["NORTH"], ["NORTH"], ["HARVEST"], ["EAST"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["NORTH"], ["WATER"], ["NORTH"], ["CARE"], ["BUILD_PASTURE"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["PLACE", "COW"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["WATER"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["HARVEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["EAST"], ["FEED", "WHEAT"], ["CARE"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WATER"], ["EAST"], ["CARE"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["CARE"], ["WATER"], ["SOUTH"], ["EAST"], ["PASS"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["SOUTH"], ["NORTH"], ["PLACE", "COW"], ["HARVEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WATER"], ["SOUTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["NORTH"], ["PLANT", "STRAWBERRY"], ["CARE"], ["CARE"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["FEED", "WHEAT"], ["HARVEST"], ["EAST"], ["WEST"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["CARE"], ["PLANT", "WHEAT"], ["PLANT", "STRAWBERRY"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["SOUTH"], ["EAST"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["EAST"], ["NORTH"], ["SOUTH"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["PLANT", "WHEAT"], ["FEED", "WHEAT"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["HARVEST"], ["WATER"], ["NORTH"], ["WATER"], ["EAST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["NORTH"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 10], ["SELL", "MILK", 6], ["SELL", "WHEAT", 13], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WEST"], ["NORTH"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["NORTH"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["HARVEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["NORTH"], ["NORTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["NORTH"], ["CARE"], ["CARE"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WATER"], ["WATER"], ["HARVEST"], ["FEED", "WHEAT"], ["WATER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["EAST"], ["FEED", "WHEAT"], ["CARE"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WATER"], ["SOUTH"], ["CARE"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["NORTH"], ["SOUTH"], ["WATER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["WATER"], ["EAST"], ["WATER"], ["HARVEST"], ["FEED", "WHEAT"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["EAST"], ["SOUTH"], ["PASS"], ["FEED", "WHEAT"], ["CARE"], ["WATER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["WEST"], "hands": [["WATER"], ["SOUTH"], ["EAST"], ["CARE"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"], ["WATER"], ["EAST"], ["COLLECT_FERTILIZER"], ["EAST"], ["SOUTH"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["EAST"], ["WEST"], ["SOUTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["SOUTH"], ["FEED", "WHEAT"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["CARE"], ["PLANT", "WHEAT"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["NORTH"], ["WEST"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["WATER"], ["CARE"], ["EAST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["NORTH"], ["WEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["NORTH"], ["EAST"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["NORTH"], ["SOUTH"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [["SELL", "WOOL", 16], ["SELL", "WHEAT", 2], ["BUY_LAND"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "MELON", 9], ["BUY_SEED", "STRAWBERRY", 7]], "farmer": ["PASS"], "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "MELON", 1]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["SOUTH"], ["WEST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["WEST"], ["NORTH"], ["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["PLANT", "STRAWBERRY"], ["WEST"], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"], ["NORTH"], ["EAST"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["CARE"], ["WATER"], ["WEST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["SOUTH"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["WEST"], ["CARE"], ["CARE"], ["SOUTH"], ["WEST"], ["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["PLANT", "STRAWBERRY"], ["WEST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["PLANT", "STRAWBERRY"], ["NORTH"], ["HARVEST"], ["EAST"], ["NORTH"], ["WEST"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WATER"], ["SOUTH"], ["NORTH"], ["NORTH"], ["WATER"], ["NORTH"], ["PLANT", "MELON"], ["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["EAST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["WATER"], ["EAST"], ["HARVEST"], ["NORTH"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["PLANT", "STRAWBERRY"], ["PLANT", "STRAWBERRY"], ["CARE"], ["CARE"], ["PLANT", "STRAWBERRY"], ["NORTH"], ["SOUTH"], ["WATER"], ["PLANT", "MELON"], ["NORTH"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["SOUTH"], ["SOUTH"], ["WATER"], ["NORTH"], ["WATER"], ["EAST"], ["PLANT", "MELON"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WEST"], ["SOUTH"], ["WATER"], ["WEST"], ["EAST"], ["EAST"], ["HARVEST"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "MELON", 6], ["BUY_SEED", "MELON", 4], ["BUY_SEED", "STRAWBERRY", 9], ["BUY_PRODUCT", "WHEAT", 4]], "farmer": ["PLANT", "MELON"], "hands": [["SOUTH"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["PLANT", "MELON"], ["DROP"], ["WEST"], ["SOUTH"], ["HARVEST"], ["WATER"], ["WEST"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 4]], "farmer": ["WATER"], "hands": [["PLANT", "MELON"], ["WATER"], ["PLANT", "STRAWBERRY"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["PLANT", "STRAWBERRY"], ["WATER"], ["EAST"], ["WATER"], ["SOUTH"], ["PLANT", "MELON"], ["WEST"], ["SOUTH"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["WEST"], "hands": [["WATER"], ["EAST"], ["WATER"], ["CARE"], ["CARE"], ["WATER"], ["EAST"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"], ["SOUTH"], ["SOUTH"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["PLANT", "MELON"], "hands": [["WEST"], ["PLANT", "STRAWBERRY"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["NORTH"], ["EAST"], ["DROP"], ["EAST"], ["SOUTH"], ["SOUTH"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["PLANT", "MELON"], ["WATER"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["EAST"], ["PLANT", "STRAWBERRY"], ["EAST"], ["NORTH"], ["WATER"], ["WEST"], ["EAST"], ["SOUTH"], ["SOUTH"], ["SOUTH"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["WEST"], "hands": [["WATER"], ["SOUTH"], ["WATER"], ["HARVEST"], ["SOUTH"], ["WATER"], ["SOUTH"], ["NORTH"], ["NORTH"], ["CARE"], ["EAST"], ["WATER"], ["CARE"], ["DROP"]]}, {"market": [], "farmer": ["PLANT", "MELON"], "hands": [["SOUTH"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["EAST"], ["SOUTH"], ["NORTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["COLLECT_FERTILIZER"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["PLANT", "MELON"], ["WATER"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["NORTH"], ["PLANT", "STRAWBERRY"], ["SOUTH"], ["WATER"], ["WATER"], ["SOUTH"], ["SOUTH"], ["NORTH"], ["NORTH"], ["WATER"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["DROP"], ["WATER"], ["WEST"], ["WEST"], ["SOUTH"], ["WATER"], ["NORTH"], ["SOUTH"]]}, {"market": [], "farmer": ["PLANT", "MELON"], "hands": [["WATER"], ["NORTH"], ["WEST"], ["WEST"], ["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "MELON", 6], ["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["SOUTH"], ["WATER"], ["PLANT", "STRAWBERRY"], ["WEST"], ["WEST"], ["NORTH"], ["SOUTH"], ["WATER"], ["NORTH"], ["WEST"], ["DROP"], ["WATER"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["WEST"], ["WATER"], ["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "MILK", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 3]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WEST"], ["EAST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["NORTH"], ["WEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["SOUTH"], ["NORTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["PLANT", "MELON"], ["NORTH"], ["CARE"], ["CARE"], ["WEST"], ["NORTH"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["NORTH"], ["WEST"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["EAST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["PLANT", "MELON"], ["NORTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["NORTH"], ["HARVEST"], ["WEST"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["CARE"], ["CARE"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["WATER"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["PASS"], ["HARVEST"], ["WEST"], ["EAST"], ["PLANT", "WHEAT"], ["EAST"], ["NORTH"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["EAST"], ["PLANT", "WHEAT"], ["SOUTH"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["NORTH"], ["WATER"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["PASS"], "hands": [["WATER"], ["NORTH"], ["EAST"], ["CARE"], ["CARE"], ["NORTH"], ["SOUTH"], ["PASS"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"], ["PASS"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WATER"], ["NORTH"], ["HARVEST"], ["WEST"], ["EAST"], ["EAST"], ["WATER"], ["EAST"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["SOUTH"], ["WATER"], ["PLANT", "WHEAT"], ["SOUTH"], ["SOUTH"], ["WATER"], ["EAST"], ["EAST"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["SOUTH"], ["NORTH"], ["WATER"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["NORTH"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["SOUTH"], ["CARE"], ["WATER"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["EAST"], ["EAST"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["WEST"], ["EAST"], ["EAST"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WEST"], ["WEST"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["EAST"], ["WEST"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["WATER"], ["WATER"], ["WEST"], ["WEST"], ["WATER"], ["NORTH"], ["SOUTH"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 12], ["SELL", "WHEAT", 10], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["BUY_ANIMAL", "COW", 1], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 8]], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["EAST"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 4], ["PICKUP", "FERTILIZER", 1], ["WEST"], ["PICKUP", "FERTILIZER", 2], ["EAST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["EAST"], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WATER"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["NORTH"], ["WEST"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_SEED", "STRAWBERRY", 1], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["CARE"], ["NORTH"], ["WEST"], ["NORTH"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WATER"], ["WATER"], ["CARE"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WEST"], ["WATER"], ["EAST"], ["EAST"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["EAST"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WEST"], ["WATER"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["CARE"], ["SOUTH"], ["PLANT", "WHEAT"], ["NORTH"], ["FEED", "WHEAT"], ["WATER"], ["SOUTH"], ["WATER"], ["WEST"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["HARVEST"], ["CARE"], ["WEST"], ["WATER"], ["WEST"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WEST"], ["EAST"], ["EAST"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["WEST"], ["SOUTH"], ["WATER"], ["WEST"], ["EAST"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["WATER"], ["WATER"], ["CARE"], ["EAST"], ["NORTH"], ["WATER"], ["WEST"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["WEST"], ["SOUTH"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["NORTH"], ["EAST"], ["WATER"], ["NORTH"], ["SOUTH"], ["WEST"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["WEST"], ["WATER"], ["PLANT", "WHEAT"], ["WEST"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WEST"], ["SOUTH"], ["WATER"], ["SOUTH"], ["CARE"], ["HARVEST"], ["SOUTH"], ["WATER"], ["NORTH"], ["WEST"], ["HARVEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["WATER"], ["EAST"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["PLANT", "WHEAT"], ["WATER"], ["EAST"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"], ["SOUTH"], ["WATER"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["WEST"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["HARVEST"], ["CARE"], ["SOUTH"], ["WEST"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["SOUTH"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["WEST"], ["PLANT", "WHEAT"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["PASS"], ["CARE"], ["HARVEST"], ["WATER"], ["EAST"], ["WEST"], ["WEST"], ["HARVEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["WATER"], ["EAST"], ["COLLECT_FERTILIZER"], ["PLANT", "WHEAT"], ["EAST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["NORTH"], ["NORTH"], ["SOUTH"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "WOOL", 12]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"], ["DROP"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["NORTH"], ["WEST"], ["SOUTH"], ["EAST"], ["EAST"], ["NORTH"], ["NORTH"], ["NORTH"], ["SOUTH"], ["EAST"]]}, {"market": [["SELL", "WOOL", 4], ["SELL", "WHEAT", 25], ["SELL", "FERTILIZER", 9], ["SELL", "MILK", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WEST"], ["NORTH"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["EAST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["SOUTH"], ["NORTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["CARE"], ["CARE"], ["NORTH"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["WEST"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["WEST"], ["WATER"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["HARVEST"], ["EAST"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["EAST"], ["CARE"], ["CARE"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["EAST"], ["NORTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["EAST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["NORTH"], ["SOUTH"], ["WEST"], ["EAST"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["EAST"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["WATER"], ["EAST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["EAST"], "hands": [["EAST"], ["EAST"], ["EAST"], ["CARE"], ["CARE"], ["SOUTH"], ["EAST"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["EAST"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["SOUTH"], ["WATER"], ["WEST"], ["EAST"], ["CARE"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["SOUTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["CARE"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["NORTH"], ["HARVEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WEST"], ["WATER"], ["WEST"], ["EAST"], ["EAST"], ["WEST"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["WATER"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["NORTH"], ["WEST"], ["WATER"], ["WEST"], ["NORTH"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["NORTH"], ["WATER"], ["WEST"], ["NORTH"]]}, {"market": [["SELL", "FERTILIZER", 12], ["SELL", "MILK", 6], ["SELL", "STRAWBERRY", 6], ["SELL", "WHEAT", 4], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["PICKUP", "FERTILIZER", 2], ["WEST"], ["PICKUP", "FERTILIZER", 2], ["EAST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["WEST"], ["NORTH"], ["HARVEST"], ["WEST"], ["WEST"], ["NORTH"], ["EAST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WEST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["WEST"], ["CARE"], ["CARE"], ["WEST"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WEST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["NORTH"], ["WATER"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["EAST"], ["WATER"], ["NORTH"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["NORTH"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["SOUTH"], ["SOUTH"], ["SOUTH"], ["FEED", "WHEAT"], ["NORTH"], ["WATER"], ["NORTH"], ["WATER"], ["EAST"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WATER"], ["CARE"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["EAST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["CARE"], ["FERTILIZE", "FERTILIZER"], ["WEST"], ["SOUTH"], ["SOUTH"], ["EAST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["SOUTH"], ["EAST"], ["SOUTH"], ["EAST"], ["NORTH"], ["WEST"], ["SOUTH"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["NORTH"], ["SOUTH"], ["SOUTH"], ["CARE"], ["FEED", "WHEAT"], ["WATER"], ["WEST"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["CARE"], ["NORTH"], ["WATER"], ["SOUTH"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["SOUTH"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"], ["HARVEST"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["SOUTH"], ["WEST"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["EAST"], ["WATER"], ["WATER"], ["CARE"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["WEST"], ["EAST"], ["COLLECT_FERTILIZER"], ["CARE"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["EAST"], ["WATER"], ["WATER"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["EAST"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WATER"], ["EAST"], ["EAST"], ["WATER"], ["SOUTH"], ["SOUTH"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["WATER"], ["EAST"], ["NORTH"], ["WEST"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"]]}, {"market": [["SELL", "MILK", 9], ["SELL", "FERTILIZER", 8], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 4]], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 2], ["WEST"], ["NORTH"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 4], ["WEST"], ["NORTH"], ["WEST"], ["PICKUP", "FERTILIZER", 1]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["SOUTH"], ["NORTH"], ["NORTH"], ["HARVEST"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["HARVEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WEST"], ["WATER"], ["FEED", "WHEAT"], ["CARE"], ["NORTH"], ["NORTH"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["EAST"], ["WATER"], ["EAST"], ["CARE"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["FEED", "WHEAT"], ["EAST"], ["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["HARVEST"], ["HARVEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["EAST"], ["EAST"], ["WEST"], ["HARVEST"], ["NORTH"], ["PLANT", "WHEAT"], ["WEST"], ["FERTILIZE", "FERTILIZER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["SOUTH"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["NORTH"], ["NORTH"], ["EAST"], ["HARVEST"], ["CARE"], ["HARVEST"], ["EAST"], ["HARVEST"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["NORTH"], ["WATER"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["PLANT", "WHEAT"], ["EAST"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["NORTH"], ["EAST"], ["CARE"], ["PASS"], ["WATER"], ["SOUTH"], ["NORTH"], ["HARVEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["NORTH"], ["WATER"], ["COLLECT_FERTILIZER"], ["PASS"], ["EAST"], ["SOUTH"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WATER"], ["NORTH"], ["NORTH"], ["WEST"], ["SOUTH"], ["HARVEST"], ["SOUTH"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["EAST"], ["WATER"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "MILK", 12], ["SELL", "FERTILIZER", 1]], "farmer": ["WEST"], "hands": [["WATER"], ["WATER"], ["WATER"], ["HARVEST"], ["DROP"], ["HARVEST"], ["EAST"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WEST"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["PICKUP", "WHEAT", 2], ["WATER"], ["WATER"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WEST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["EAST"], ["NORTH"], ["EAST"], ["EAST"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WEST"], ["WATER"], ["WEST"], ["WEST"], ["NORTH"], ["WATER"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["EAST"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["WATER"], ["WEST"], ["HARVEST"], ["CARE"], ["WATER"], ["WATER"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["HARVEST"], ["SOUTH"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["WEST"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "WOOL", 16], ["SELL", "STRAWBERRY", 12], ["SELL", "MILK", 9], ["SELL", "FERTILIZER", 9], ["SELL", "WHEAT", 10], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "WHEAT", 3]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 5], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["NORTH"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["EAST"], ["PICKUP", "FERTILIZER", 3], ["PICKUP", "FERTILIZER", 4], ["WEST"], ["WEST"], ["NORTH"], ["PICKUP", "FERTILIZER", 5], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["PICKUP", "FERTILIZER", 1], ["NORTH"], ["HARVEST"], ["WEST"], ["EAST"], ["WEST"], ["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["EAST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["NORTH"], ["CARE"], ["CARE"], ["WATER"], ["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"], ["WATER"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["EAST"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["EAST"], ["SOUTH"], ["HARVEST"], ["WATER"], ["EAST"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["WATER"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["SOUTH"], ["PLANT", "WHEAT"], ["WEST"], ["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["EAST"], ["HARVEST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["CARE"], ["WATER"], ["EAST"], ["CARE"], ["CARE"], ["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["SOUTH"], ["NORTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["EAST"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["EAST"], ["WEST"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["WATER"], ["SOUTH"], ["WEST"], ["NORTH"], ["WATER"], ["NORTH"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["HARVEST"], ["SOUTH"], ["EAST"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["SOUTH"], ["WATER"], ["SOUTH"], ["HARVEST"], ["SOUTH"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["WATER"], ["HARVEST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["SOUTH"], ["WATER"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["SOUTH"], ["SOUTH"], ["PLANT", "WHEAT"], ["CARE"], ["CARE"], ["WEST"], ["HARVEST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WEST"], ["WATER"], ["SOUTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["WATER"], ["WATER"], ["WEST"], ["WATER"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["SOUTH"], ["SOUTH"], ["EAST"], ["SOUTH"], ["EAST"], ["WATER"], ["EAST"], ["WEST"], ["NORTH"], ["WATER"], ["HARVEST"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["HARVEST"], ["SOUTH"], ["NORTH"], ["SOUTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["SOUTH"], ["PLANT", "WHEAT"], ["SOUTH"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["SOUTH"], ["WEST"], ["HARVEST"], ["FEED", "WHEAT"], ["HARVEST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["WATER"], ["PLANT", "WHEAT"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["EAST"], ["WEST"], ["EAST"], ["WEST"], ["WATER"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["NORTH"], ["CARE"], ["WATER"], ["WEST"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["HARVEST"], ["WATER"], ["WEST"], ["WEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["EAST"], ["WATER"], ["WEST"], ["WATER"], ["EAST"], ["NORTH"], ["PLANT", "WHEAT"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["NORTH"], ["WATER"], ["WEST"], ["WATER"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WEST"]]}, {"market": [["SELL", "MILK", 18], ["SELL", "WHEAT", 25], ["SELL", "STRAWBERRY", 4], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["NORTH"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["EAST"], ["PICKUP", "FERTILIZER", 2], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["EAST"], ["NORTH"], ["FEED", "WHEAT"], ["HARVEST"], ["SOUTH"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["NORTH"], ["CARE"], ["FEED", "WHEAT"], ["WATER"], ["WEST"], ["HARVEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["EAST"], ["NORTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["CARE"], ["WEST"], ["WEST"], ["EAST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["HARVEST"], ["WATER"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["EAST"], ["EAST"], ["CARE"], ["HARVEST"], ["WATER"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["EAST"], ["WATER"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["CARE"], ["WATER"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["NORTH"], ["WATER"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"], ["WATER"], ["EAST"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["EAST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["HARVEST"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["EAST"], ["SOUTH"], ["SOUTH"], ["WEST"], ["FEED", "WHEAT"], ["EAST"], ["EAST"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["HARVEST"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["CARE"], ["NORTH"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["EAST"], ["SOUTH"], ["SOUTH"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["HARVEST"], "hands": [["HARVEST"], ["SOUTH"], ["FERTILIZE", "FERTILIZER"], ["WEST"], ["EAST"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["CARE"], ["WATER"], ["WEST"], ["SOUTH"], ["WATER"], ["EAST"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["HARVEST"], ["COLLECT_FERTILIZER"], ["EAST"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["EAST"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["HARVEST"], ["NORTH"], ["WATER"], ["EAST"], ["WATER"], ["WATER"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["HARVEST"], ["WATER"], ["WATER"], ["NORTH"], ["EAST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 28], ["SELL", "MILK", 9], ["SELL", "FERTILIZER", 9], ["SELL", "WHEAT", 4], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["EAST"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 4], ["SOUTH"], ["WEST"], ["PICKUP", "FERTILIZER", 4], ["NORTH"], ["WEST"], ["EAST"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["HARVEST"], ["WATER"], ["NORTH"], ["WEST"], ["NORTH"], ["WEST"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["WEST"], ["NORTH"], ["SOUTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["CARE"], "hands": [["CARE"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["CARE"], ["WATER"], ["NORTH"], ["NORTH"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["CARE"], ["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["WATER"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WEST"], ["WATER"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["WEST"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["FEED", "WHEAT"], ["WATER"], ["EAST"], ["NORTH"], ["FEED", "WHEAT"], ["SOUTH"], ["WEST"], ["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WEST"], ["WATER"], ["HARVEST"], ["CARE"], ["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["WEST"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["EAST"], ["WEST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["EAST"], ["WATER"], ["CARE"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["EAST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 5]], "farmer": ["WEST"], "hands": [["NORTH"], ["SOUTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["SOUTH"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 5]], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["WEST"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["WATER"], ["EAST"], ["EAST"], ["WATER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["WATER"], ["EAST"], ["NORTH"], ["SOUTH"], ["CARE"], ["WEST"], ["WEST"], ["WEST"], ["WATER"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["EAST"], ["WATER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["WEST"], "hands": [["WEST"], ["EAST"], ["HARVEST"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 1], ["SELL", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["WEST"], ["WATER"], ["SOUTH"], ["CARE"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["WEST"], ["WATER"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["WATER"], ["WATER"], ["EAST"], ["HARVEST"], ["WATER"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["WATER"], ["EAST"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["WATER"], ["WEST"], ["WEST"], ["HARVEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["CARE"], ["WATER"], ["WATER"], ["NORTH"], ["HARVEST"], ["WATER"], ["WATER"], ["SOUTH"]]}, {"market": [["SELL", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["EAST"], ["SOUTH"], ["WATER"], ["NORTH"], ["WEST"], ["WEST"], ["EAST"], ["WATER"], ["WEST"], ["WEST"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["WEST"], ["WATER"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "MILK", 9], ["SELL", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["EAST"], ["SOUTH"], ["WATER"], ["WEST"], ["DROP"], ["WEST"], ["EAST"], ["WATER"], ["EAST"], ["WATER"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "WOOL", 16], ["SELL", "STRAWBERRY", 12], ["SELL", "FERTILIZER", 8], ["SELL", "MILK", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 4]], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["NORTH"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["PICKUP", "FERTILIZER", 6], ["NORTH"], ["WEST"], ["PICKUP", "FERTILIZER", 1], ["PICKUP", "FERTILIZER", 5], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["PICKUP", "FERTILIZER", 5], ["NORTH"], ["NORTH"], ["SOUTH"], ["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["WATER"], ["WEST"], ["FEED", "WHEAT"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["NORTH"], ["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["WEST"], ["CARE"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["HARVEST"], ["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["HARVEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["EAST"], ["WATER"], ["WEST"], ["COLLECT_FERTILIZER"], ["CARE"], ["SOUTH"], ["NORTH"], ["DIG"], ["WATER"], ["WEST"], ["WEST"], ["HARVEST"], ["EAST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["WEST"], ["WEST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["PLANT", "WHEAT"], ["EAST"], ["SOUTH"], ["NORTH"], ["DIG"], ["HARVEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["SOUTH"], ["FEED", "WHEAT"], ["NORTH"], ["WATER"], ["HARVEST"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"], ["PLANT", "WHEAT"], ["EAST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["SOUTH"], ["CARE"], ["HARVEST"], ["WEST"], ["PLANT", "WHEAT"], ["WEST"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["SOUTH"], ["WEST"], ["WATER"], ["NORTH"], ["WEST"], ["EAST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["SOUTH"], ["SOUTH"], ["WEST"], ["CARE"], ["WATER"], ["EAST"], ["HARVEST"], ["WEST"], ["SOUTH"], ["NORTH"], ["HARVEST"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["WEST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["DIG"], ["SOUTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["EAST"], ["EAST"], ["WATER"], ["FEED", "WHEAT"], ["EAST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["EAST"], ["PLANT", "WHEAT"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["EAST"], ["EAST"], ["CARE"], ["SOUTH"], ["WATER"], ["HARVEST"], ["HARVEST"], ["NORTH"], ["EAST"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["EAST"], ["PLANT", "WHEAT"], ["WEST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["WEST"], ["HARVEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["EAST"], ["WATER"], ["WEST"], ["CARE"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["NORTH"], ["WATER"], ["SOUTH"], ["EAST"], ["HARVEST"], ["HARVEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["HARVEST"], ["SOUTH"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["SOUTH"], ["SOUTH"], ["WATER"], ["NORTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["SOUTH"], ["WATER"], ["FEED", "WHEAT"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["NORTH"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["PASS"]]}, {"market": [], "farmer": ["WEST"], "hands": [["HARVEST"], ["SOUTH"], ["SOUTH"], ["CARE"], ["WEST"], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"], ["WATER"], ["WEST"], ["WATER"], ["EAST"], ["PASS"]]}, {"market": [["SELL", "MILK", 11]], "farmer": ["WATER"], "hands": [["NORTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["COLLECT_FERTILIZER"], ["DROP"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["SOUTH"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["HARVEST"], ["WATER"], ["WATER"], ["WEST"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["NORTH"], ["HARVEST"], ["SOUTH"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["CARE"], ["WATER"], ["SOUTH"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"]]}, {"market": [["SELL", "STRAWBERRY", 34], ["SELL", "MILK", 3], ["SELL", "WHEAT", 12], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "WHEAT", 45], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["PASS"], "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 2], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["WEST"], ["WEST"], ["WEST"], ["PICKUP", "FERTILIZER", 5], ["WEST"], ["WEST"], ["NORTH"], ["PICKUP", "FERTILIZER", 5], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["HARVEST"], ["WEST"], ["NORTH"], ["HARVEST"], ["WATER"], ["WEST"], ["WEST"], ["NORTH"], ["WEST"], ["WEST"], ["NORTH"], ["EAST"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["PLANT", "WHEAT"], ["WEST"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["HARVEST"], ["WEST"], ["NORTH"], ["NORTH"], ["WATER"], ["NORTH"], ["NORTH"], ["EAST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WATER"], ["WEST"], ["CARE"], ["CARE"], ["PLANT", "WHEAT"], ["WEST"], ["WATER"], ["NORTH"], ["HARVEST"], ["NORTH"], ["WATER"], ["NORTH"], ["HARVEST"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["DROP"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["WEST"], ["WEST"], ["FERTILIZE", "FERTILIZER"], ["PLANT", "WHEAT"], ["NORTH"], ["HARVEST"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WEST"], ["HARVEST"], ["NORTH"], ["EAST"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["NORTH"], ["PLANT", "WHEAT"], ["NORTH"], ["WATER"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["PLANT", "WHEAT"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["DROP"], ["HARVEST"], ["SOUTH"], ["EAST"], ["EAST"], ["WATER"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["EAST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 4]], "farmer": ["CARE"], "hands": [["CARE"], ["NORTH"], ["WATER"], ["CARE"], ["CARE"], ["WEST"], ["PLANT", "WHEAT"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["HARVEST"], ["SOUTH"], ["WATER"], ["NORTH"]]}, {"market": [["SELL", "MELON", 12]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["WEST"], ["WATER"], ["DROP"], ["PLANT", "WHEAT"], ["SOUTH"], ["EAST"], ["DROP"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"], ["WEST"], ["EAST"], ["WATER"], ["SOUTH"], ["WEST"], ["WATER"], ["SOUTH"], ["FERTILIZE", "FERTILIZER"], ["EAST"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["NORTH"], "hands": [["WEST"], ["NORTH"], ["EAST"], ["SOUTH"], ["HARVEST"], ["WEST"], ["EAST"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WEST"], ["EAST"], ["DROP"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["DROP"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["SOUTH"], ["EAST"], ["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["NORTH"], ["EAST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["NORTH"], "hands": [["WEST"], ["HARVEST"], ["SOUTH"], ["CARE"], ["CARE"], ["WATER"], ["EAST"], ["NORTH"], ["EAST"], ["WATER"], ["SOUTH"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["NORTH"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["WATER"], "hands": [["WEST"], ["PLANT", "WHEAT"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["DROP"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WEST"], ["SOUTH"], ["NORTH"], ["WATER"], ["NORTH"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["HARVEST"], "hands": [["NORTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["EAST"], ["PLANT", "WHEAT"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["DROP"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [], "farmer": ["PLANT", "WHEAT"], "hands": [["WATER"], ["EAST"], ["HARVEST"], ["HARVEST"], ["SOUTH"], ["WATER"], ["EAST"], ["HARVEST"], ["EAST"], ["SOUTH"], ["WEST"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["NORTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["HARVEST"], ["EAST"], ["WEST"], ["FEED", "WHEAT"], ["HARVEST"], ["EAST"], ["EAST"], ["PLANT", "WHEAT"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["NORTH"], ["HARVEST"], ["WATER"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["PLANT", "WHEAT"], ["SOUTH"], ["HARVEST"], ["CARE"], ["WEST"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["PLANT", "WHEAT"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["SOUTH"], ["WEST"], ["COLLECT_FERTILIZER"], ["WEST"], ["EAST"], ["NORTH"], ["EAST"], ["EAST"], ["HARVEST"], ["NORTH"], ["WATER"], ["SOUTH"], ["WEST"]]}, {"market": [["SELL", "MILK", 9], ["SELL", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["SOUTH"], ["HARVEST"], ["SOUTH"], ["DROP"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["WEST"]]}, {"market": [["SELL", "MELON", 6]], "farmer": ["EAST"], "hands": [["NORTH"], ["DROP"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["HARVEST"], ["HARVEST"], ["SOUTH"], ["HARVEST"], ["WATER"], ["SOUTH"], ["WATER"], ["WEST"]]}, {"market": [["SELL", "MELON", 6], ["BUY_SEED", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["WATER"], ["SOUTH"], ["WEST"], ["WEST"], ["SOUTH"], ["DROP"], ["PLANT", "WHEAT"], ["EAST"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "MELON", 12], ["SELL", "STRAWBERRY", 16], ["SELL", "WHEAT", 20], ["SELL", "MILK", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "WHEAT", 2], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "COW", 1], ["PICKUP", "FERTILIZER", 1], ["NORTH"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 4], ["SOUTH"], ["WEST"], ["PICKUP", "COW", 1], ["PICKUP", "FERTILIZER", 2], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["PICKUP", "WHEAT", 3], ["SOUTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 1], ["EAST"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["NORTH"], ["HARVEST"], ["SOUTH"], ["WEST"], ["WEST"], ["EAST"], ["SOUTH"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["SOUTH"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["WATER"], ["SOUTH"], ["NORTH"], ["EAST"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["CARE"], ["WEST"], ["SOUTH"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_SEED", "WHEAT", 2], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["EAST"], ["HARVEST"], ["WATER"], ["CARE"], ["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["EAST"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WEST"], ["WATER"], ["NORTH"], ["HARVEST"], ["WATER"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WATER"], ["WATER"], ["WEST"], ["HARVEST"], ["WATER"], ["HARVEST"], ["BUILD_PASTURE"], ["NORTH"], ["NORTH"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["HARVEST"], ["EAST"], ["SOUTH"], ["FEED", "WHEAT"], ["WEST"], ["WEST"], ["PLACE", "COW"], ["DIG"], ["NORTH"], ["DIG"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["SOUTH"], ["WATER"], ["HARVEST"], ["CARE"], ["WATER"], ["WATER"], ["FEED", "WHEAT"], ["PLANT", "WHEAT"], ["NORTH"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["NORTH"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["WEST"], ["HARVEST"], ["CARE"], ["WATER"], ["HARVEST"], ["WATER"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["DIG"], ["WATER"], ["WATER"], ["CARE"], ["PASS"], ["WATER"], ["WEST"], ["EAST"], ["EAST"], ["DIG"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["BUILD_PASTURE"], ["EAST"], ["EAST"], ["COLLECT_FERTILIZER"], ["PASS"], ["EAST"], ["WATER"], ["EAST"], ["SOUTH"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["PLACE", "COW"], ["WATER"], ["HARVEST"], ["WEST"], ["SOUTH"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["HARVEST"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "MILK", 6]], "farmer": ["WEST"], "hands": [["CARE"], ["WATER"], ["HARVEST"], ["HARVEST"], ["DROP"], ["HARVEST"], ["HARVEST"], ["EAST"], ["HARVEST"], ["SOUTH"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["CARE"], "hands": [["WEST"], ["PASS"], ["WEST"], ["EAST"], ["PICKUP", "WHEAT", 2], ["PLANT", "WHEAT"], ["EAST"], ["HARVEST"], ["NORTH"], ["HARVEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["NORTH"], ["HARVEST"], ["EAST"], ["EAST"], ["WATER"], ["WATER"], ["EAST"], ["DIG"], ["EAST"], ["SOUTH"], ["DIG"]]}, {"market": [["SELL", "WOOL", 8], ["SELL", "MILK", 3]], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["NORTH"], ["WATER"], ["DROP"], ["NORTH"], ["WATER"], ["HARVEST"], ["HARVEST"], ["PLANT", "WHEAT"], ["EAST"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["NORTH"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["SOUTH"], ["EAST"], ["SOUTH"], ["WATER"], ["EAST"], ["EAST"], ["WATER"]]}, {"market": [["SELL", "MELON", 6], ["SELL", "STRAWBERRY", 4]], "farmer": ["NORTH"], "hands": [["WATER"], ["NORTH"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["DROP"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 6]], "farmer": ["NORTH"], "hands": [["NORTH"], ["DROP"], ["WEST"], ["WATER"], ["NORTH"], ["EAST"], ["HARVEST"], ["WATER"], ["NORTH"], ["WEST"], ["EAST"], ["NORTH"]]}, {"market": [["SELL", "STRAWBERRY", 30], ["SELL", "MELON", 6], ["SELL", "FERTILIZER", 5], ["SELL", "WOOL", 8], ["SELL", "WHEAT", 1], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["EAST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["SOUTH"], ["EAST"], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["NORTH"], ["WEST"], ["HARVEST"], ["HARVEST"], ["EAST"], ["NORTH"], ["NORTH"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["EAST"], ["NORTH"], ["NORTH"], ["SOUTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["CARE"], ["HARVEST"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["CARE"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["HARVEST"], ["WEST"], ["EAST"], ["HARVEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["WEST"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["NORTH"], ["HARVEST"], ["EAST"], ["SOUTH"], ["WATER"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["SOUTH"], ["WATER"], ["EAST"], ["NORTH"], ["NORTH"], ["SOUTH"], ["HARVEST"], ["WATER"], ["EAST"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["HARVEST"], ["WEST"], ["WEST"], ["SOUTH"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 3]], "farmer": ["WEST"], "hands": [["CARE"], ["WATER"], ["WATER"], ["CARE"], ["CARE"], ["WEST"], ["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["SOUTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WEST"], ["WEST"], ["WEST"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["EAST"], ["WATER"], ["WATER"], ["EAST"], ["EAST"], ["NORTH"], ["WEST"], ["WATER"], ["NORTH"], ["HARVEST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["EAST"], ["EAST"], ["NORTH"], ["SOUTH"], ["NORTH"], ["NORTH"], ["WEST"], ["NORTH"], ["EAST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["EAST"], ["WATER"], ["FEED", "WHEAT"], ["HARVEST"], ["WATER"], ["NORTH"], ["WATER"], ["HARVEST"], ["HARVEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["NORTH"], ["EAST"], ["NORTH"], ["CARE"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["EAST"], ["DIG"], ["EAST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["WATER"], ["SOUTH"], ["WATER"], ["COLLECT_FERTILIZER"], ["CARE"], ["HARVEST"], ["NORTH"], ["SOUTH"], ["PLANT", "WHEAT"], ["HARVEST"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["SOUTH"], ["SOUTH"], ["WEST"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["HARVEST"], ["SOUTH"], ["NORTH"], ["EAST"], ["NORTH"], ["WEST"], ["DIG"], ["EAST"], ["HARVEST"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["SOUTH"], ["HARVEST"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["WEST"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 10], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["HARVEST"], ["HARVEST"], ["WATER"], ["FEED", "WHEAT"], ["CARE"], ["DROP"], ["CARE"], ["WATER"], ["EAST"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["WEST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["EAST"]]}, {"market": [["SELL", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["WEST"], ["WEST"], ["WATER"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["HARVEST"], ["WEST"], ["SOUTH"], ["WEST"], ["SOUTH"], ["SOUTH"], ["WATER"], ["SOUTH"], ["WATER"], ["SOUTH"]]}, {"market": [["SELL", "STRAWBERRY", 33], ["SELL", "FERTILIZER", 13], ["SELL", "MILK", 9], ["SELL", "WHEAT", 1], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 3], ["PICKUP", "FERTILIZER", 5], ["WEST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 3], ["PICKUP", "FERTILIZER", 6], ["EAST"], ["WEST"], ["EAST"], ["PICKUP", "FERTILIZER", 4], ["EAST"], ["WEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"], ["SOUTH"], ["EAST"], ["WEST"], ["EAST"], ["WEST"], ["EAST"], ["NORTH"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["WEST"], ["WEST"], ["FEED", "WHEAT"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["NORTH"], ["EAST"], ["SOUTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["SOUTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["NORTH"], ["CARE"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"], ["WATER"], ["HARVEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["EAST"], ["SOUTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["CARE"], ["SOUTH"], ["NORTH"], ["WEST"], ["NORTH"], ["SOUTH"], ["NORTH"], ["HARVEST"], ["DIG"], ["WEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["FERTILIZE", "FERTILIZER"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WATER"], ["FEED", "WHEAT"], ["NORTH"], ["WATER"], ["HARVEST"], ["WEST"], ["EAST"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["HARVEST"], ["CARE"], ["HARVEST"], ["WEST"], ["DIG"], ["WATER"], ["WATER"], ["WEST"], ["WATER"], ["NORTH"], ["EAST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["FERTILIZE", "FERTILIZER"], ["PLANT", "WHEAT"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["FERTILIZE", "FERTILIZER"], ["PLANT", "WHEAT"], ["EAST"], ["SOUTH"], ["WEST"], ["HARVEST"], ["WATER"], ["SOUTH"], ["WEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["WATER"], ["WATER"], ["WEST"], ["CARE"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["FERTILIZE", "FERTILIZER"], ["PLANT", "WHEAT"], ["WEST"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["DIG"], ["SOUTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["FEED", "WHEAT"], ["EAST"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["NORTH"], ["NORTH"], ["WEST"], ["EAST"], ["EAST"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["HARVEST"], ["CARE"], ["SOUTH"], ["WATER"], ["DIG"], ["WATER"], ["NORTH"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["EAST"], ["WATER"], ["EAST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["WEST"], ["EAST"], ["PLANT", "WHEAT"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["PLANT", "WHEAT"], ["EAST"], ["NORTH"], ["WATER"], ["HARVEST"], ["WATER"], ["EAST"], ["EAST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["WEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["NORTH"], ["HARVEST"], ["FERTILIZE", "FERTILIZER"], ["WATER"], ["WATER"], ["HARVEST"], ["HARVEST"], ["PLANT", "WHEAT"], ["NORTH"], ["HARVEST"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["WATER"], ["EAST"], ["WEST"], ["DIG"], ["NORTH"], ["WATER"], ["WATER"], ["DIG"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["SOUTH"], ["WATER"], ["NORTH"], ["CARE"], ["SOUTH"], ["SOUTH"], ["WEST"], ["PLANT", "WHEAT"], ["FERTILIZE", "FERTILIZER"], ["EAST"], ["EAST"], ["PLANT", "WHEAT"], ["EAST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WEST"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["FEED", "WHEAT"], ["COLLECT_FERTILIZER"], ["FERTILIZE", "FERTILIZER"], ["HARVEST"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"], ["PLANT", "WHEAT"], ["CARE"], ["PASS"], ["WATER"], ["DIG"], ["EAST"], ["WEST"], ["NORTH"], ["HARVEST"], ["HARVEST"], ["WEST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["PLANT", "WHEAT"], ["SOUTH"], ["SOUTH"], ["FERTILIZE", "FERTILIZER"], ["DIG"], ["PLANT", "WHEAT"], ["NORTH"], ["WEST"]]}, {"market": [["SELL", "MILK", 11]], "farmer": ["EAST"], "hands": [["SOUTH"], ["NORTH"], ["NORTH"], ["EAST"], ["DROP"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["DIG"], ["WATER"], ["WATER"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WEST"]]}, {"market": [["SELL", "STRAWBERRY", 22], ["SELL", "WHEAT", 20], ["SELL", "FERTILIZER", 2], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["SELL", "FERTILIZER", 2], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 4], ["SOUTH"], ["EAST"], ["PICKUP", "WHEAT", 3], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["HARVEST"], ["NORTH"], ["NORTH"], ["HARVEST"], ["HARVEST"], ["NORTH"], ["HARVEST"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["PLANT", "WHEAT"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["CARE"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["CARE"], ["HARVEST"], ["NORTH"], ["CARE"], ["WEST"], ["HARVEST"], ["NORTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"], ["CARE"], ["COLLECT_FERTILIZER"], ["WEST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["HARVEST"], ["NORTH"], ["WEST"], ["NORTH"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["SOUTH"], ["HARVEST"], ["HARVEST"], ["NORTH"], ["NORTH"], ["WEST"], ["WATER"], ["HARVEST"], ["NORTH"], ["WEST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 2]], "farmer": ["SOUTH"], "hands": [["FEED", "WHEAT"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["HARVEST"], ["FEED", "WHEAT"], ["HARVEST"], ["EAST"], ["FEED", "WHEAT"], ["NORTH"], ["WATER"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["CARE"], ["WATER"], ["WATER"], ["FEED", "WHEAT"], ["CARE"], ["EAST"], ["EAST"], ["CARE"], ["WATER"], ["HARVEST"], ["PLANT", "WHEAT"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["WEST"], ["CARE"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["PLANT", "WHEAT"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["HARVEST"], "hands": [["WEST"], ["WATER"], ["WEST"], ["COLLECT_FERTILIZER"], ["PASS"], ["HARVEST"], ["SOUTH"], ["EAST"], ["PLANT", "WHEAT"], ["WATER"], ["WEST"]]}, {"market": [["SELL", "WOOL", 4], ["SELL", "MILK", 3], ["SELL", "FERTILIZER", 2]], "farmer": ["WEST"], "hands": [["WEST"], ["HARVEST"], ["NORTH"], ["WEST"], ["PASS"], ["EAST"], ["SOUTH"], ["DROP"], ["WATER"], ["WEST"], ["SOUTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["HARVEST"], "hands": [["WEST"], ["PLANT", "WHEAT"], ["WATER"], ["SOUTH"], ["SOUTH"], ["HARVEST"], ["SOUTH"], ["PICKUP", "WHEAT", 1], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WEST"], ["EAST"], ["WEST"], ["HARVEST"], ["SOUTH"], ["SOUTH"], ["HARVEST"], ["WEST"], ["WATER"], ["HARVEST"], ["HARVEST"]]}, {"market": [["SELL", "MILK", 3], ["SELL", "FERTILIZER", 2], ["BUY_SEED", "WHEAT", 2]], "farmer": ["HARVEST"], "hands": [["SOUTH"], ["NORTH"], ["WATER"], ["FEED", "WHEAT"], ["DROP"], ["HARVEST"], ["DIG"], ["NORTH"], ["HARVEST"], ["EAST"], ["PLANT", "WHEAT"]]}, {"market": [["SELL", "FERTILIZER", 1], ["BUY_SEED", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["SOUTH"], ["DROP"], ["SOUTH"], ["CARE"], ["PICKUP", "WHEAT", 2], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"], ["PLANT", "WHEAT"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["WATER"], ["WEST"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["NORTH"], ["WATER"], ["NORTH"], ["WATER"], ["EAST"], ["WEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WEST"], ["SOUTH"], ["SOUTH"], ["WEST"], ["NORTH"], ["NORTH"], ["EAST"], ["NORTH"], ["NORTH"], ["EAST"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 12]], "farmer": ["HARVEST"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WATER"], ["HARVEST"], ["NORTH"], ["HARVEST"], ["FEED", "WHEAT"], ["WATER"], ["DROP"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["WEST"], ["WATER"], ["WEST"], ["NORTH"], ["DIG"], ["CARE"], ["HARVEST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 14], ["SELL", "FERTILIZER", 1], ["BUY_SEED", "WHEAT", 1]], "farmer": ["HARVEST"], "hands": [["SOUTH"], ["EAST"], ["WATER"], ["NORTH"], ["SOUTH"], ["DROP"], ["PLANT", "WHEAT"], ["COLLECT_FERTILIZER"], ["PLANT", "WHEAT"], ["SOUTH"], ["NORTH"]]}, {"market": [["SELL", "MILK", 3], ["SELL", "WHEAT", 2]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WATER"], ["DROP"], ["WEST"], ["WATER"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 16], ["SELL", "FERTILIZER", 7], ["SELL", "WOOL", 12], ["SELL", "WHEAT", 28], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 4], "hands": [["PICKUP", "WHEAT", 3], ["PICKUP", "FERTILIZER", 1], ["WEST"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 3], ["SOUTH"], ["EAST"], ["WEST"], ["NORTH"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["FEED", "WHEAT"], ["WEST"], ["WEST"], ["NORTH"], ["NORTH"], ["WATER"], ["EAST"], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["CARE"], ["WEST"], ["WEST"], ["NORTH"], ["HARVEST"], ["SOUTH"], ["EAST"], ["NORTH"], ["NORTH"], ["SOUTH"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["NORTH"], "hands": [["EAST"], ["WEST"], ["SOUTH"], ["CARE"], ["CARE"], ["WEST"], ["NORTH"], ["WEST"], ["NORTH"], ["HARVEST"], ["WEST"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 2]], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["SOUTH"], ["WATER"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["DIG"], ["WEST"], ["WEST"], ["NORTH"], ["SOUTH"], ["HARVEST"], ["WEST"], ["EAST"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["PLANT", "WHEAT"], ["WATER"], ["NORTH"], ["HARVEST"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["EAST"], ["WEST"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["WEST"], ["NORTH"], ["FEED", "WHEAT"], ["EAST"], ["WATER"], ["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["SOUTH"], ["WATER"], ["FEED", "WHEAT"], ["CARE"], ["WATER"], ["EAST"], ["WATER"], ["SOUTH"], ["HARVEST"], ["PLANT", "WHEAT"], ["HARVEST"]]}, {"market": [["BUY_SEED", "WHEAT", 2]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["SOUTH"], ["SOUTH"], ["CARE"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["SOUTH"], ["WATER"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["HARVEST"], ["NORTH"], ["EAST"], ["WATER"], ["EAST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["SOUTH"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["EAST"], ["WEST"], ["SOUTH"], ["WEST"], ["PLANT", "WHEAT"], ["NORTH"], ["WATER"], ["WEST"], ["EAST"], ["SOUTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["WEST"], ["HARVEST"], ["WATER"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["NORTH"], ["EAST"], ["EAST"], ["SOUTH"], ["HARVEST"], ["WEST"], ["NORTH"], ["HARVEST"], ["SOUTH"], ["PLANT", "WHEAT"], ["NORTH"], ["WEST"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["NORTH"], ["EAST"], ["WATER"], ["SOUTH"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["NORTH"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["WEST"], "hands": [["DIG"], ["EAST"], ["WEST"], ["SOUTH"], ["CARE"], ["WEST"], ["NORTH"], ["WATER"], ["WEST"], ["WATER"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["CARE"], "hands": [["PLANT", "WHEAT"], ["FERTILIZE", "FERTILIZER"], ["SOUTH"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["EAST"], ["HARVEST"], ["WATER"]]}, {"market": [["BUY_SEED", "WHEAT", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["WATER"], ["HARVEST"], ["HARVEST"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["NORTH"], ["WEST"], ["NORTH"], ["WATER"], ["PLANT", "WHEAT"], ["EAST"]]}, {"market": [["SELL", "MILK", 9], ["SELL", "FERTILIZER", 2]], "farmer": ["WEST"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["DROP"], ["NORTH"], ["WATER"], ["WATER"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["NORTH"], ["NORTH"], ["WATER"], ["NORTH"], ["NORTH"], ["NORTH"], ["WEST"], ["SOUTH"], ["WATER"], ["NORTH"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["NORTH"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["PLANT", "WHEAT"], ["NORTH"]]}, {"market": [["SELL", "FERTILIZER", 10], ["SELL", "MILK", 5], ["SELL", "STRAWBERRY", 6], ["SELL", "WHEAT", 26], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_SEED", "WHEAT", 1], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [["BUY_SEED", "WHEAT", 2]], "farmer": ["PICKUP", "WHEAT", 3], "hands": [["PICKUP", "WHEAT", 2], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 4], ["PICKUP", "WHEAT", 4], ["SOUTH"], ["WEST"], ["NORTH"], ["EAST"], ["WEST"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["WEST"], ["WEST"], ["HARVEST"], ["HARVEST"], ["WEST"], ["NORTH"], ["EAST"], ["SOUTH"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WEST"], ["HARVEST"], ["FEED", "WHEAT"], ["DIG"], ["WEST"], ["NORTH"], ["EAST"], ["SOUTH"], ["WEST"], ["WEST"], ["NORTH"]]}, {"market": [["SELL", "FERTILIZER", 1], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["CARE"], ["WEST"], ["SOUTH"], ["FEED", "WHEAT"], ["CARE"], ["PLANT", "WHEAT"], ["WEST"], ["WATER"], ["WATER"], ["HARVEST"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"], ["CARE"], ["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"], ["NORTH"], ["EAST"], ["DIG"], ["WEST"], ["HARVEST"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["EAST"], ["WEST"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"], ["SOUTH"], ["PLANT", "WHEAT"], ["SOUTH"]]}, {"market": [], "farmer": ["CARE"], "hands": [["SOUTH"], ["WATER"], ["DIG"], ["NORTH"], ["NORTH"], ["HARVEST"], ["HARVEST"], ["WEST"], ["WEST"], ["WATER"], ["SOUTH"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["EAST"], ["PLANT", "WHEAT"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["DIG"], ["DIG"], ["SOUTH"], ["WEST"], ["SOUTH"], ["HARVEST"], ["EAST"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 2]], "farmer": ["WEST"], "hands": [["CARE"], ["EAST"], ["WATER"], ["CARE"], ["CARE"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["WATER"], ["WEST"], ["HARVEST"], ["DIG"], ["NORTH"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["DIG"], ["PLANT", "WHEAT"], ["NORTH"], ["DIG"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["SOUTH"], "hands": [["WEST"], ["WATER"], ["HARVEST"], ["EAST"], ["EAST"], ["SOUTH"], ["SOUTH"], ["WEST"], ["NORTH"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["PLANT", "WHEAT"]]}, {"market": [], "farmer": ["FEED", "WHEAT"], "hands": [["NORTH"], ["WEST"], ["DIG"], ["NORTH"], ["SOUTH"], ["HARVEST"], ["HARVEST"], ["WATER"], ["NORTH"], ["WATER"], ["SOUTH"], ["EAST"], ["WATER"]]}, {"market": [["SELL", "FERTILIZER", 1], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["CARE"], "hands": [["NORTH"], ["WEST"], ["PLANT", "WHEAT"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["DIG"], ["DIG"], ["WEST"], ["NORTH"], ["EAST"], ["HARVEST"], ["WATER"], ["WEST"]]}, {"market": [["SELL", "FERTILIZER", 2], ["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["NORTH"], ["WEST"], ["WATER"], ["CARE"], ["CARE"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["WATER"], ["WATER"], ["SOUTH"], ["DIG"], ["WEST"], ["SOUTH"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["WEST"], "hands": [["NORTH"], ["SOUTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"], ["NORTH"], ["HARVEST"], ["HARVEST"], ["PLANT", "WHEAT"], ["NORTH"], ["CARE"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["SOUTH"], ["SOUTH"], ["WEST"], ["EAST"], ["WATER"], ["EAST"], ["WATER"], ["PLANT", "WHEAT"], ["DIG"], ["WATER"], ["DIG"], ["COLLECT_FERTILIZER"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["NORTH"], "hands": [["EAST"], ["SOUTH"], ["HARVEST"], ["NORTH"], ["FEED", "WHEAT"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["WATER"], ["PLANT", "WHEAT"], ["EAST"], ["PLANT", "WHEAT"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["HARVEST"], ["DIG"], ["NORTH"], ["NORTH"], ["WATER"], ["HARVEST"], ["SOUTH"], ["EAST"], ["WATER"], ["SOUTH"], ["WATER"], ["NORTH"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["DIG"], ["PLANT", "WHEAT"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["DIG"], ["WATER"], ["EAST"], ["WATER"], ["HARVEST"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "FERTILIZER", 2]], "farmer": ["NORTH"], "hands": [["EAST"], ["PLANT", "WHEAT"], ["WATER"], ["CARE"], ["EAST"], ["WATER"], ["PLANT", "WHEAT"], ["WATER"], ["EAST"], ["WEST"], ["DIG"], ["NORTH"], ["EAST"]]}, {"market": [["SELL", "FERTILIZER", 1]], "farmer": ["WATER"], "hands": [["WATER"], ["WATER"], ["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["WEST"], ["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["PLANT", "WHEAT"], ["WATER"], ["EAST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["WATER"], ["NORTH"], ["EAST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WATER"]]}, {"market": [["SELL", "STRAWBERRY", 32], ["SELL", "FERTILIZER", 13], ["SELL", "MILK", 6], ["SELL", "WHEAT", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["PICKUP", "WHEAT", 1], "hands": [["PICKUP", "WHEAT", 3], ["WEST"], ["EAST"], ["PICKUP", "WHEAT", 3], ["PICKUP", "WHEAT", 3], ["WEST"], ["EAST"], ["PICKUP", "WHEAT", 3], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["FEED", "WHEAT"], ["WEST"], ["NORTH"], ["HARVEST"], ["NORTH"], ["WEST"], ["EAST"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["FEED", "WHEAT"], "hands": [["COLLECT_FERTILIZER"], ["SOUTH"], ["NORTH"], ["FEED", "WHEAT"], ["HARVEST"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 2]], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["FEED", "WHEAT"], ["NORTH"], ["NORTH"], ["HARVEST"], ["WATER"], ["NORTH"]]}, {"market": [["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["EAST"], "hands": [["NORTH"], ["WEST"], ["NORTH"], ["NORTH"], ["CARE"], ["WATER"], ["NORTH"], ["FEED", "WHEAT"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["FEED", "WHEAT"], ["WATER"], ["WATER"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["COLLECT_FERTILIZER"], ["NORTH"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["EAST"], ["FEED", "WHEAT"], ["NORTH"], ["WATER"], ["HARVEST"], ["WEST"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["EAST"], ["WATER"], ["EAST"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["WEST"], ["NORTH"], ["SOUTH"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["FEED", "WHEAT"], ["NORTH"], ["EAST"], ["WEST"], ["FEED", "WHEAT"], ["WATER"], ["WATER"], ["HARVEST"], ["EAST"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["CARE"], ["WATER"], ["SOUTH"], ["NORTH"], ["CARE"], ["SOUTH"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["WATER"], ["HARVEST"], ["NORTH"], ["EAST"], ["EAST"], ["WATER"], ["WEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["EAST"], ["SOUTH"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["HARVEST"], ["SOUTH"], ["HARVEST"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["SOUTH"], ["WATER"], ["WATER"], ["CARE"], ["SOUTH"], ["NORTH"], ["EAST"], ["HARVEST"], ["EAST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["EAST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["NORTH"], ["WATER"], ["FEED", "WHEAT"], ["EAST"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["NORTH"], ["EAST"], ["WEST"], ["NORTH"], ["HARVEST"], ["CARE"], ["EAST"], ["NORTH"]]}, {"market": [["SELL", "MILK", 9], ["SELL", "FERTILIZER", 2]], "farmer": ["WATER"], "hands": [["WEST"], ["EAST"], ["NORTH"], ["WATER"], ["DROP"], ["WATER"], ["SOUTH"], ["EAST"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["CARE"], ["WATER"], ["WATER"], ["SOUTH"], ["PICKUP", "WHEAT", 1], ["SOUTH"], ["WATER"], ["EAST"], ["SOUTH"], ["NORTH"]]}, {"market": [["SELL", "WOOL", 8], ["SELL", "MILK", 3], ["SELL", "FERTILIZER", 2]], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["HARVEST"], ["WATER"], ["EAST"], ["WATER"], ["HARVEST"], ["DROP"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["SOUTH"], ["WATER"], ["WEST"], ["FEED", "WHEAT"], ["WATER"], ["EAST"], ["WEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["WATER"], ["SOUTH"], ["WATER"], ["NORTH"], ["EAST"], ["WATER"], ["WEST"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"], ["WATER"], ["HARVEST"], ["COLLECT_FERTILIZER"], ["WATER"], ["WATER"]]}, {"market": [["SELL", "WHEAT", 51], ["SELL", "FERTILIZER", 9], ["SELL", "WOOL", 8], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["PASS"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"], ["BUY_PRODUCT", "WHEAT", 1]], "farmer": ["PASS"], "hands": [["PASS"], ["WATER"], ["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["PICKUP", "WHEAT", 1], ["WATER"], ["WEST"], ["PICKUP", "WHEAT", 2], ["PICKUP", "WHEAT", 3], ["SOUTH"], ["EAST"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["HARVEST"], ["HARVEST"], ["WEST"], ["WEST"], ["NORTH"], ["WATER"], ["NORTH"], ["WEST"], ["NORTH"], ["WEST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["WEST"], ["HARVEST"], ["FEED", "WHEAT"], ["SOUTH"], ["NORTH"], ["WEST"], ["NORTH"], ["SOUTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["EAST"], ["WATER"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["WATER"], ["NORTH"], ["WATER"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["FEED", "WHEAT"], ["HARVEST"], ["SOUTH"], ["WEST"], ["NORTH"], ["WEST"], ["NORTH"], ["EAST"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["FEED", "WHEAT"], ["FEED", "WHEAT"], ["WATER"], ["NORTH"], ["NORTH"], ["HARVEST"], ["WEST"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"], ["WEST"], ["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"], ["NORTH"], ["NORTH"], ["NORTH"]]}, {"market": [["SELL", "MILK", 3], ["SELL", "FERTILIZER", 2]], "farmer": ["WEST"], "hands": [["DROP"], ["HARVEST"], ["WATER"], ["EAST"], ["EAST"], ["WATER"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WEST"], ["WEST"], ["EAST"], ["SOUTH"], ["EAST"], ["EAST"], ["WATER"], ["HARVEST"], ["EAST"]]}, {"market": [], "farmer": ["WEST"], "hands": [["NORTH"], ["WATER"], ["WATER"], ["NORTH"], ["HARVEST"], ["WATER"], ["SOUTH"], ["WEST"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["NORTH"], ["HARVEST"], ["SOUTH"], ["NORTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["SOUTH"], ["WATER"], ["SOUTH"], ["SOUTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["NORTH"], ["EAST"], ["WATER"], ["COLLECT_FERTILIZER"], ["EAST"], ["WATER"], ["WATER"], ["HARVEST"], ["WATER"], ["SOUTH"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["WATER"], ["EAST"], ["EAST"], ["WEST"], ["FEED", "WHEAT"], ["WEST"], ["SOUTH"], ["WEST"], ["HARVEST"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["EAST"], ["SOUTH"], ["EAST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["WATER"], ["SOUTH"], ["WATER"], ["WEST"], ["SOUTH"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["EAST"], ["WATER"], ["WATER"], ["NORTH"], ["WEST"], ["WEST"], ["WATER"], ["HARVEST"], ["NORTH"], ["WATER"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["HARVEST"], ["WATER"], ["FEED", "WHEAT"], ["WEST"], ["WATER"], ["HARVEST"], ["NORTH"], ["WATER"], ["WEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["WEST"], ["NORTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["WATER"], ["EAST"], ["WATER"], ["WEST"], ["NORTH"]]}, {"market": [["SELL", "MILK", 5], ["SELL", "FERTILIZER", 4]], "farmer": ["WATER"], "hands": [["WATER"], ["WEST"], ["WATER"], ["EAST"], ["DROP"], ["WEST"], ["WATER"], ["HARVEST"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["EAST"], ["WATER"], ["WEST"], ["WATER"], ["EAST"], ["WATER"], ["HARVEST"], ["EAST"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["EAST"], ["NORTH"], ["WATER"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WATER"], ["NORTH"], ["WEST"], ["WATER"], ["EAST"], ["WATER"], ["WEST"], ["WATER"], ["SOUTH"], ["WATER"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WATER"], ["WATER"], ["WEST"], ["WATER"], ["EAST"], ["NORTH"], ["EAST"], ["WATER"], ["NORTH"]]}, {"market": [["SELL", "WHEAT", 61], ["SELL", "FERTILIZER", 7], ["SELL", "MILK", 3], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["EAST"], "hands": []}, {"market": [["HIRE"], ["HIRE"], ["HIRE"]], "farmer": ["NORTH"], "hands": [["EAST"], ["WEST"], ["NORTH"], ["WEST"], ["EAST"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["EAST"], ["NORTH"], ["NORTH"], ["WEST"], ["HARVEST"], ["WATER"], ["WEST"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["NORTH"], ["NORTH"], ["HARVEST"], ["EAST"], ["HARVEST"], ["WEST"], ["WEST"], ["WEST"], ["WEST"]]}, {"market": [], "farmer": ["EAST"], "hands": [["NORTH"], ["NORTH"], ["HARVEST"], ["NORTH"], ["EAST"], ["SOUTH"], ["SOUTH"], ["WEST"], ["SOUTH"], ["WEST"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["NORTH"], ["NORTH"], ["EAST"], ["WATER"], ["NORTH"], ["WATER"], ["WATER"], ["WATER"], ["SOUTH"], ["NORTH"]]}, {"market": [], "farmer": ["EAST"], "hands": [["WATER"], ["NORTH"], ["NORTH"], ["HARVEST"], ["WATER"], ["HARVEST"], ["HARVEST"], ["HARVEST"], ["WATER"], ["WATER"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["HARVEST"], ["HARVEST"], ["NORTH"], ["WEST"], ["EAST"], ["SOUTH"], ["WEST"], ["WEST"], ["HARVEST"], ["HARVEST"]]}, {"market": [], "farmer": ["NORTH"], "hands": [["WEST"], ["WEST"], ["WATER"], ["WEST"], ["WATER"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["NORTH"]]}, {"market": [], "farmer": ["WATER"], "hands": [["WEST"], ["WATER"], ["HARVEST"], ["WATER"], ["HARVEST"], ["HARVEST"], ["HARVEST"], ["HARVEST"], ["WATER"], ["NORTH"]]}, {"market": [], "farmer": ["HARVEST"], "hands": [["WEST"], ["HARVEST"], ["WEST"], ["HARVEST"], ["WEST"], ["WEST"], ["WEST"], ["SOUTH"], ["HARVEST"], ["NORTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WEST"], ["EAST"], ["SOUTH"], ["EAST"], ["WEST"], ["WATER"], ["WATER"], ["WATER"], ["WEST"], ["WATER"]]}, {"market": [], "farmer": ["WEST"], "hands": [["WATER"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["HARVEST"], ["HARVEST"], ["WATER"], ["HARVEST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["HARVEST"], ["EAST"], ["COLLECT_FERTILIZER"], ["EAST"], ["WEST"], ["WEST"], ["SOUTH"], ["EAST"], ["HARVEST"], ["EAST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["EAST"], ["SOUTH"], ["WEST"], ["COLLECT_FERTILIZER"], ["WEST"], ["WATER"], ["WATER"], ["EAST"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["COLLECT_FERTILIZER"], ["HARVEST"], ["HARVEST"], ["NORTH"], ["EAST"], ["EAST"]]}, {"market": [], "farmer": ["COLLECT_FERTILIZER"], "hands": [["SOUTH"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["SOUTH"], ["EAST"], ["EAST"], ["COLLECT_FERTILIZER"], ["EAST"], ["SOUTH"]]}, {"market": [], "farmer": ["WEST"], "hands": [["SOUTH"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["COLLECT_FERTILIZER"], ["EAST"], ["EAST"], ["EAST"], ["NORTH"], ["SOUTH"]]}, {"market": [["SELL", "MILK", 18], ["SELL", "FERTILIZER", 9], ["SELL", "WHEAT", 22]], "farmer": ["DROP"], "hands": [["COLLECT_FERTILIZER"], ["COLLECT_FERTILIZER"], ["DROP"], ["DROP"], ["DROP"], ["NORTH"], ["EAST"], ["EAST"], ["NORTH"], ["SOUTH"]]}, {"market": [["SELL", "FERTILIZER", 14], ["SELL", "WHEAT", 24], ["SELL", "MILK", 6], ["SELL", "FERTILIZER", 3]], "farmer": ["WEST"], "hands": [["EAST"], ["DROP"], ["SOUTH"], ["SOUTH"], ["WEST"], ["NORTH"], ["EAST"], ["DROP"], ["DROP"], ["SOUTH"]]}, {"market": [["SELL", "FERTILIZER", 1], ["SELL", "WHEAT", 15]], "farmer": ["SOUTH"], "hands": [["DROP"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["SOUTH"], ["NORTH"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["DROP"]]}, {"market": [["SELL", "WHEAT", 15]], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["SOUTH"], ["WATER"], ["SOUTH"], ["SOUTH"], ["DROP"], ["NORTH"], ["SOUTH"], ["SOUTH"], ["WEST"]]}, {"market": [["SELL", "WHEAT", 15]], "farmer": ["SOUTH"], "hands": [["SOUTH"], ["SOUTH"], ["SOUTH"], ["WATER"], ["WEST"], ["WEST"], ["PLACE", "WHEAT", 15], ["WEST"], ["WEST"], ["WEST"]]}]')
_SEAT1_ACTIONS = _SEAT0_ACTIONS


# ---------------------------------------------------------------------------
# LaborRepair — tile-local, PASS steps only
# ---------------------------------------------------------------------------
def _labor_repair(obs, action, mod=None):
    """Replace PASS with DIG/WATER/HARVEST when the unit stands on an
    actionable tile.  No movement => no desync.  Strictly >= PASS.
    mod=None means 'embedded in the agent file' (module-level helpers)."""
    try:
        if mod is not None:
            action = mod._copy_action(action)
            seat = mod._seat(obs)
            farm = mod._farm(obs, seat)
        else:
            action = _copy_action(action)
            seat = _seat(obs)
            farm = _farm(obs, seat)
        tiles = farm.get("tiles") or []
        day = int(obs.get("day", 0) or 0)
        positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
        units = [action.get("farmer", ["PASS"]),
                 *list(action.get("hands") or [])]
        board = len(tiles)
        for i, (pos, act) in enumerate(zip(positions, units)):
            if not act or act[0] != "PASS":
                continue
            if not (isinstance(pos, (list, tuple)) and len(pos) >= 2):
                continue
            try:
                x, y = int(pos[0]), int(pos[1])
            except (TypeError, ValueError):
                continue
            if not (0 <= y < board and 0 <= x < len(tiles[y])):
                continue
            tile = tiles[y][x]
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "WEED":
                units[i] = ["DIG"]
            elif kind == "PLANT":
                cu = int(tile.get("consecutive_unwatered", 0) or 0)
                watered = bool(tile.get("watered_today"))
                if cu >= 1 and not watered:
                    units[i] = ["WATER"]
                elif day >= 28 and tile.get("crop") in ("WHEAT", "CARROT") \
                        and int(tile.get("yield_units", 0) or 0) >= 2:
                    units[i] = ["HARVEST"]
        action["farmer"] = units[0] if units else ["PASS"]
        action["hands"] = units[1:]
        return action
    except Exception:
        return action



# ---------------------------------------------------------------------------
# CashRank — sell-first re-ranker when buys would fail (missing-crop fix)
# ---------------------------------------------------------------------------
_SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100,
              "MELON": 80}
_ANIMAL_COST = {"COW": 400, "SHEEP": 500, "GOOSE": 300}


def _order_cost(obs, o):
    """Cost of a buy order in the current market state."""
    if not o or len(o) < 3:
        return 0
    try:
        qty = max(0, int(o[2]))
    except (TypeError, ValueError):
        return 0
    if o[0] == "BUY_SEED":
        return _SEED_COST.get(o[1], 99) * qty
    if o[0] == "BUY_ANIMAL":
        return _ANIMAL_COST.get(o[1], 999) * qty
    if o[0] == "BUY_PRODUCT":
        px = float(((obs.get("market") or {}).get("prices") or {}).get(o[1], 0) or 0)
        return px * qty
    return 0


def _cash_rank(obs, action, mod=None):
    """When the tape's buy orders would fail for lack of cash this turn,
    move our SELLs to the front of the queue so they fund the buys in the
    same step (the engine resolves our queue in order).  Fixes the live
    cascade: cash pressure -> failed BUY_SEED -> skipped PLANT waves
    (the visible 'missing crops') and failed feed-wheat buys (escapes)."""
    try:
        farm = obs["farms"][obs["player"]]
        money = float(farm.get("money") or 0)
        market = list(action.get("market") or [])
        if not market:
            return action
        total_cost = sum(_order_cost(obs, o) for o in market)
        if money >= total_cost:
            return action  # no reorder needed — preserve reference behavior
        sells = [o for o in market if o and o[0] == "SELL"]
        if not sells:
            return action
        others = [o for o in market if not (o and o[0] == "SELL")]
        action = dict(action)
        action["market"] = sells + others
        return action
    except Exception:
        return action




_BRAIN = {"labor": True, "cashrank": True}

def agent(obs, configuration=None):
    try:
        seat = _seat(obs)
        tape = _SEAT0_ACTIONS
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(tape) - 1)
        _update_memory(obs)
        action = _weed_repair_action(obs, _copy_action(tape[step]), tape, step)
        action = _adapt_animals(obs, action)
        action = _adapt_crops(obs, action)
        action = _adapt_market(obs, action)
        if _BRAIN.get("cashrank"):
            action = _cash_rank(obs, action)
        if _BRAIN.get("labor"):
            action = _labor_repair(obs, action)
        action = _align_hands(_rank_sell_slots(obs, action, configuration), obs)
        if step == 718:
            try:
                action = _v26_terminal_sweep(obs, action, configuration)
            except Exception:
                pass
        return _align_hands(action, obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {"farmer": ["PASS"],
                "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                "market": []}

def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)

_v25_agent = agent
