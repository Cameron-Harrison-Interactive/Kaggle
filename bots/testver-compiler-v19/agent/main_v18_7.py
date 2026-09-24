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


VERSION = "HI_AgriBot_v18.7_WaterOpt"
import base64
import copy
import json
import math
import zlib


_SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
    (
    'c-rk<%Whm*a{L#rYav#VY{@&eR5MKsTNEhDg>ge@G%#ZrFvg3vcZUDn6d(1t85tRwd2UhC^sYoz-Fx0AGcq#rm;XKa_uqd1$KQWH'
    '`Ilc#K3snMc=CC1@*ltb*Wdp8{tx#b|MA=J|M~a-x&Qpj$xm0e>-+zuAAbDw*IzH+U;TV}eX=-'
    'td$T!NoSHv>{As=ZaI!di{*RCA^}G8&Z+==|-'
    'kmJYCx8BVeSPzO@6R7@Z{B@+d$<3C&;PeL=*89BzkK?z_x^2vemU8!Ki)kwbo=3{&wD@Hwr{`t-aDQearl<^H@9~`Jv?;x$-'
    'd|5r}RBf%~YTL<EN|Zcfa2M^X}7^2_X-jd{b}z_2t|3c97^0J$>`bEF3)l{y*N|ZD-bb&!6@e1$)im7Z2w8@@{?WJ^$@xFhGxAz~'
    'l1VgXfp-'
    'J@@HLY+NRr3_Whw^upBI7wjGfmc2fq_PN`q`2!+Pq<#Fyn@>*z4#p##K!2Qf3(pQmW&ZYB=Z`~c{<f!<9f!{RDFf1&KWSVl^Z5K*'
    'FdUB^s6B4C-ll)5J<ksBkk!Dt-'
    '&zgN4_RLhTm;H!3|<3|9}<s4c20O5ge&ds&Gq&A?cJ|`THoGXU0?m%Lo@AtlDhp1*A{99dBF26mue_@YuM0Wbdt?}-'
    'n%0wsIvL%2gV;i`Qs;F(N7M~#E<LiFRt6(PI>gmum@;-'
    'w2RLv|7mN5#3zq${#!q5Q9H_vKXf=Wu*0XHlV{DOAD!D_cPUmH3eJDncBO^>U4q*f|J)2yc*sB72ZM(R3_c#EN&~0%ergfyc};~^'
    '+W{^#VK>001@icUX>$fRY#{S23rDFLqQWz_BV>Q8ju3b#9-#7V@z3(x>Q#4e=N+P$r;|T_yt}>J{J6fo{p-'
    'nMRlE!*ABJCwqpru7xhT6==CgacH&fl7NUqod0F~t{RlhfE<Lt49N2KjmO|Re9JpueadJ&K4fPp=;BLpT9VV$ursaQz6<xzUxu3;'
    '|zJ;==TOb^WnvG&3Q6Kq|!_TX><sA3~0pj+qa`{N;F9@4W5S{^Ss6Q|+QKkoif?sBj3NsqADX5&8>T{Op${<3;6Z~wJ$fq}s!*F+'
    'g~NSHX_p&*b}agwJlw$z-b172IsFEI(a%e`%#)bZW7u?KFW-'
    '}x9`%XT2{`Sw;;CPeqhZ8%h(B`FkE>GSu0bw8inKRg)2H8<ZOH|gI0S&yz%_mrmB|1x77G$03LBg8IP?4HJ!Qs3ZsX$t{4m`5-'
    'd2szBR8{$*jBZQ3|Wq&2Aqa7c@9vdJUXSEO3R@mK_+bikuLvIsJA3FlpaZr&XAl(U9oW%q>uDFV#b*@F$&H9)saLJJ$(hAcU;?a?'
    '2;3YwYRUTAOjCJsuugf^tcSw$57ch4t^e25BVhD(mzyA{92L=H#Tw~P01J83f0Ma3ypx8#;4A3J;M;Q7|W!#w|ldwJPWAH)<AN20'
    '_=0mU!h<&y5ByVo6pH6CUg0G(4zx#{l-'
    'AQcQS+oJYnz*6Myc@c7xmru^pe}PqiZq%fk9GUx?ZTw*(l!C{e0J|M*xJOhNRYcdmk4C6Bv!d{-'
    '`c=a!JohhLSh`f1mQevyi>aKlsvT*%Cjs&DGxth;U%gCW8^T<ifr}MSMFXv8y!7TKaGNZcAum#&3HZfM%+SXnWS2{tiwwnF)sXS#'
    '!6JqpNK@U`=&kUD~o7)vg5uHfMkqC7p$Vg3jrM*(NY?K6f4GZbO$EZQz??S9R@f-'
    'X4FQEiVcq;banem8{wMHRLg$>>p9p_q0_3^0Dy00)-0G~YvM9<rZFWU!np{ea+6_exhW(d>+V}Hd;<tq_C%Z*eu#Poc>x-'
    '~P|K~#U*<M;8cqwtdhLTDOt@g1J)3iTuv^e$x9@y+^=Eh)_8@7)2t@X~F!r^OI$C6Y2zy*GJDA>?BG+zu>b%Uf{Sf!gNg3%9EwCF'
    'hGU&{mB?C(k<C#m06mb#X%9VVP-F0opsFQQ+yl(&a-VSWT+o<I4mR+}Ijv4mFtOYd-'
    '>K+2k)FMHaRc%oaR}ReqBs|T$IIP`nnq}M{f!8LnBCLZoHH!v?7k0OvGYXjmK84c?EMV6e&b=#`MaRlISkelw4w(7WWHn>&2Ib?$'
    '!vYwg?YNx`mT{VRA@r=Gb2eN=z@_s~1L#z{0!Foy%BM%hK9jPZs;3heeMA}=LFJs@(2IaE+cA-uOb-Ko8s;&M-VHXvea)e<FFK-'
    '$|MS)LU%sd*;ONIA&_4;PwL>B;i+<@CJlvvZ?m%SRSJ2GJUakc)1eSng4d=|`;oJfm&uCFsR#~$V-'
    '1^}~IDqt0Adf^oUwmL!I3|;2OAhZk=9=fE2*x}cmr*_kH5qpcy0BatIj>-8g#G~tYE;r=2{qiYI}*63-'
    '7+pEBwV!lwV?zGK%7QdsB{Mfd=@q+$g7AJrJ0$^wgJ{ZcaMWbY4}}9=^Go90<j1&D%-'
    '+qi9fl&UV93W=EMG@nL{)#s|v378Tj?&{S!5unbOA=fkMuFubn%{Fw2V=|LVdCFYHK<gPo4q24M(Y>`<!w4GAy&Fu<Jx=b`RS*^E'
    'L)w4r8gz)X7@jSf;C!9Lu?CLQ!i>)lKQSKLPO?7-BD4n>h`S3|-;Gp$GHC&@d8X0tEWx-yWQw~lhIV@OzIp*C?in%*ciD|vVfXo7'
    '3A#)66k-'
    '`1LX@%BLpPu7BUl7;LSOCWY?&B$?saLqxjd{Ss(Cg_~5?J7cpmNV)voy^H#RHUT61~~Z#*ioQMZBb0Kna(s7+VB`KsBiYyyT$aBO'
    '9My8$<tcL$skW=!v(gj&WLUGMyI(WAue+6sf0?|fME-O4LKNT8Ob~QT)}7nh0_H?pb5#NmlQ3K6O{bbA8}$MSR*um*!{lUAU-'
    '(ab$q%RW?8=^c<BujwL!DpEWu+K>L&7uQ3!)A^~V`ZO-'
    '<)0&e%F&uwgd?xK4vclA4D3r6}_?`Mu9dxlj<GjFqAiG$bCp`@iksK;VjOFX~GZwA5CLDt*ZHAt9LAX7=(A;rwK*7hUJ2#UNh1EI'
    '9bcP8gAcc}z4=!v_blAVgX-MC~YAqNa)trLI;{sV2OJZoLvf&`T2?#e8M1IxxH$d{GHi3%R5Nxfhxd*`Y}I6HhH!KAZ`S7lGV}W;'
    '#RtIq<NR!JC`A&8YUVE@^e7*+R7dL~fl*AV!fp4T2JUM!meZMO8bVQbNdUIR?jQ6&3O`@~{1DZ7J1FN<j@9hSs~yAprb1iXBvlH9'
    '-`kkH7YY4rnEEOrGGWoS!sE^sl<&hc~IV<mq6w7#!hs4p0Sx6(aGN1{;EBwHjhQOtU@~E5i=d@tGm>(AK|N=k$OmzXU}2SKpYsDz'
    'jLKY;|5WdL=lzAozv^B)R*0FkhJLvj3H3PVVE-C4T)`QNb)a6*<PuVDUlhFN9j!`9{tzX-'
    'H|g92UvA#z;R)PYLfOFa&g88oal*(omst-'
    '^w^3tVRvr{>S0&4I|*jCdw+<0^EoRT}X@?PF3zCc<6)(NEhA^r?txa@CDE9%9H8DG)5eGz_YPbOkfZmCBivVbK@|HA`C>M^O|RKl'
    '$Egjl?w*eEAO&UinbI6I?Tc#OPNQJw+kZ*JcEOJCT>;c6lQ=M_lo3wM{`NgNGZ-Mm>t)fOR~Du1C>%)$(;t;SxCkQAz3q(&YUOjG'
    '5e;{xKcGI3k@(SXB<gZb`xtCameM(vv=FY^Y104w?p3~%FaU=E*>z-'
    '*H`!rNgwwx2W9#BrJ#t>1*w*vobj7|nBt+=XM2C?h1=&Cya<w*qfk{}VZc)hO)CwI52Sw`QS+}OM6LxGNicVG9DHPWaY!*0a@*%*'
    '3EEO)$V!S<8O)k#u!7qHbtIbS+sl=fN>R^H79e7JCYG3O5Lz`-'
    '21Kt|2&ZQFr9^V+NG!Mu4AM>rt`_^YA6U9wz6{1PrBnf0QzXylFep^dSA*s3uw^v%h#?NlZnP-X2z$-'
    ';w%PL(>mO|SM=ABf`)#`iSF|gB7$M|V`!LuS`wE2!jwOk<AL-o>>Hr0Uvv0_gI;L-'
    'B&r{vE@?*96aPFvrBf$59^rJWw+N)wyQV1whtH+l_Hsd4_m1P)TlZ-'
    '1Ay(y;s^DgLBw1`VdBR5hMRWg`M8;NHJGe&`ypB=X?x20@6FH{y=G|M<I%X<m1X1&F^>x~~uXW8mQoq|l2ADN~qeM<TXYoC>@<?{'
    'L>WFuAgh#-'
    'udn@|}a<kW+}r*egPA7(7M6a#R8C&WtKbd&}O)1M02C0N+f`5)gyRD3T8jS^_WC&s6o3#KGMwh8dVD`l`*ds24{2**j&rvsmYBTO'
    'NYV9PM#@H~a+HHvmp%1@0g7RGeW<kOdeKIRxR;=aFe-'
    '1pbt2Pb<zs&yRqT$PfF9U68N5<P1YsT*m<jiSgjJQ{!mqpQry^yn<bJ3u{Vtc=SdrV6E7lTUAmaJyM;Ia0R9R#w}o?HnXtqc?Pa0'
    'R)R7znO?86pnmTrYJU<Mo9DJN(pfhtA1Tf|7i2biO?*!e=KGvOF4*n(i|mcWSE;QTu)~f9D}9xPFdn|X#`eOO5nSb6kB?ZVy-'
    'y>9U3c}4ipXL`_cHKnizWT{s3&bi@fX=W1m0TwFlv+i76$s(ybDc^)jh(NS*l{FM<?pijG(Ep;L~H=v2`FPDSpO)n>D=ClotNZcZ'
    'd-'
    '=UNdE+6!S>yHxkzkyqbuHKwXsZ~e}Ll)t6I$gL#~5A;Nb3fWU>`!V%>m#%JKgRBc()s_1{p$b0y)p@17a3_;W_sKJ=K;$lK3dv_;'
    'a|tG$;PQ8RF<($z6G75?#bc?BdTWK?d8jO^ds$jCFw3fok@T)6QzFzN=wDNFzZT3(u)(DSJQiB<{qt;zfLh8i6O&=PtQLB4onJrQ'
    'YgmG^Y)e-'
    '+;abuN3h1?+EN2>j4ag(H_74>JbsiUrl4|L~kw=|8{#g2M{HW9<MPl2+wM~~5&j~In6o83hWefn~Y%g()Q}#tH#*`l)Sz?1?EsQ7'
    'CT6(N^8dHaW%n{(Ng|VCS5gb4GN_Iz-En}o)=LD34G)4uAqQ?Pd(<*lfIdXy|>!QRSJ73kDdWK&Rk4u7nqzPjkWO8p|*~M_OhNKZ'
    'lOo}|+BWoQTEhVC;tS^_dAFzJr>&DQv!;tsa4zza$N>`qLi{&bhknqt0=m`I_?!$7_Z>ekWb+YI|Bugm~T;jxzPiqFql)~$6<>rx'
    '`heXjDl6q3FXP;PnoSl?_&I+2zfm%+ot;bhyASukaM?-'
    'L1mI|O#XOzT|8lt7)zZ5v$4BV7zy8Yn9?raHqg$32g)Pw#@qW7RVt<w`y!Dz8HKcUd>Lm}}h*z)+UqnRYsIUh~ylM>bv5J|M6;C$'
    'ghQnI*`q8bB;_pFFDmB3eayM3=9UI;xlDZ)XpHpw}XOqY}f9B_dOY^JD+u`WYjO<)sQABERSe%`)Qw|q^h9RY*m+fMxN3BE61TJR'
    'lQT0U=s){80~%VKsxWTR>Y+B&>yDaIn6j<k^^38JY6rYN}w#8pb<ZO91BqDhw!wvVC8<JtbYupN&Yr6Ro9eXG!m$a-'
    '@j86g(Yz_XY_9+q;?kr)Ugsv~2NPfAK_!82+C|1=}5i(&=LmEpv8UvXf*jPr;w65y3dvO=K_;dzN0$)eSoygaL6PqGcBHstx|O4&'
    '0g@93kPbZ;D^_M?18CPY4z<E&D5j*yQuZ;~kx$QRy7=~)^}*Tm|%&<CqqXVbkGVFozL+*<px?n)U>^Yh3?AE8lDuKP}4dC&n)vnX'
    'WXOB(XfjR&_I|D{w!Pxe7)3rLfss(5^l*v|0$e6dlUPuJh#Hfqb&q#rlMXHQChpbEv;iVtxL!Scl^1Q7qZ$SGCOL>@O^B&}~zk^B'
    '!6j8r%#aQO6Weu-+ok@$W|ZNf|n&oOHa_}Z3f98T)uT<nU3>Ln9Fd3W{aQ16XP4)p05(m1*ie8GK{Dy-WvsYU*!%1n}~W@PpX(gL'
    'j+%jd=gCDlloD?9Z`V4{}xp73T>3W?Ni(UsfCN*`(IN5(<n#oMXU#t6m#Bx63o+9;-cJRb-#p@NYWV4|dlOe9wkW!2c-'
    ')}A6l`igRlaClotQ^`fMb7`sS<|boWjs9e|4U;~hmVu%zoK4RNVElE5fxuyQJxIZy2+z6NJfulL5w(g6A+@ZY>YPYf#^TzM4*~F}'
    'FquG|9g578VWdt@fmJ5%g#7Vk5gnT9qi~(f=&?)<ftdy|N|#5)|H6I`RzNfT$G%_5x>7!%*&NBKTAfjV?AaYyev7#?qx5jj&W{A6'
    '6-uuVM5us_3BPLAX9?t09XFT!LMr4kr0hhd#<`X)%gIk1Nvl(WbyuDkkGu0t(F>t!w9z+b)x6nWi~a2S6l}pP2}w8=-'
    '?i)OoA+N(^a>Fyu){<e7z_%K&JGp7A)r#cMWG%fQzIzx98&W}AbTi8>Wf?yg+&5|l?p%WY{n9<xt%K&2HM%piWtM=x7i$@W+)({U'
    'Kk;;QE*XmPAhPua2JO%b{Z~ceg+Qo!p38L0&629u$5NG1!D+zTcb;OcQdsu&<jzBIVa~P^Qee|6Tv)N<-'
    'E7kpIfRNsjW<Hl=GkoFq6m_zv#g@1YzBvKhu_QjMD>@wH!7_sAru)j0G7&yF7XHSSy@P<}MAmVb_aT;Xz8B4Y08r6!YTAr9er+%='
    'BbMp^F`(*R8A$&us3<ZAw(SCKbr>bXZbYIwK?}>xbqgVvi|oPHQ6o1tl;Y@c|RS786on>MUgaP!LgKzXFVuM|)Z2YTFTrrPWw|2b'
    '8`8f$yzRZTW<+FtYibrGQR{cXSHqF0)iorXG_K8oYB^6#Ic@5^OQ2<H1YFgKkeXcGzg~-'
    'zdG6rN%LPs6{i3*dh{LiaH!Zn&|X)U(C%i1dSt^u|+Xi$3U1xX#?MOVMeS-'
    'RY`({xl{18S-LKQnrMD)HqpG9e98>uz}SBnzN_nZzuw<fcb`bDwn|!dy&PWPv=IfTJt*Mq`ss$*XLA7(?0PP$B-MpY<Ohf0DOz-G'
    'p5n&}lq`$#tXV;{h#K1{tqV+UK#jHsA7fovm+o+(^`^u>4(v9T<>jf=6<EZ;!6=ap?Qt;OwJc*llDp7UnPO@7yx?+hEQsQgoF5hv'
    '#udeYIF?E^)WaHUVJ$-+rX--iMMB}4)XISr4FZkEU>bl4Iz=OF0FXn2G>iQC5V8Qm!~djcQK3n+8wh|HLw42y4CT*(C!b6*244ek'
    'KzH*Q{lqU0PcMGASX_;o##+eg(sAHVN$~V!m|d{n@5C;aNAk&WqOt?M75Z?|Myyu*NR(ZEhG^xd;O}E=-'
    ')t?q`Rb&{3T0;k9z{iqN9bK^f@0x~sT5Bim93T*AET`tQaZa+t<A?@qCiWp{`XRVSu$y80py}mEe4f{&t!E95%|Esp;d({%b(uLd'
    '>IFY;J|;+vEr4wibbaCCZ%$pa3JWaCK^dv6`onCqq^)?0xVpIYD77SZOsip@pT!$98guAHH61BgzC>lt#&0vGsJPjtjGCaMxQoDg'
    '$`(-#kh-&(@dmMgtTmab2E5q%sgZ@$v3J9HXn}6xj@r*qY8%XY%uE~up|<cM0~lDiwvp85YltvlmN}-'
    '+nHLJTc?(>Drt2$M2dKo@T`3Q&pOGu8%-(+HN||!$l7-'
    'cZ<!CgnF0HVw683vo^4`nBx5vVC9ANXt{gbydz9Il72jBi34IdYvEuSu3OH^w+vEI%!5Ka@iH_-gkiYl_W>XV=UR5oXt)x3eqqr}'
    'qWjT#4nODjJUxVegV6O^#TcRxgK|HO^PEcUU<U-'
    '8LapmV%2`<Z&uMQF_RbvYR)CzGeN(yPCp^#Mpo6E=#6edX6*fQ#p%BdZo(<SM}1-'
    'z<u%7KEcvdN)%TT)+yBz#LpZ+|m_ajz(V1%zId=p<`@$=gvPp_HV-u-nYCMwy^hp~`z0$bcsh!aD2$loV~ND9ZzUY8?-'
    'hzWm6+q6<Jy<}SV4n0C7~vR+`Yrq>u!KB!1SzUmuE8l_ofN?jUreezRgvc_vA54dC)*kdRQBa=#~oE_m#D=tDBiOyROk-'
    '{p6V`;I*(y{|*i_w&_%ZK^lA!zA3i0RVu8=~VC(S1EOSDwcCJSdbJ?I36AE(1mqV7F;9Y(k04fVI_>V%v@!kx^4V1d?u^ZrjkRkx'
    '_1-NiF+Ebj~`>uVIv@L&VHh84ecwaUu7QB`rjja;#V@(a=+^OQm<D3qmTj&Z|aMDmAH2$>M-'
    'UDNRwX<X9;F7?*nS=686a0fh`wTr5sxOrTeG{p0Yj?9<|_(f?x3Iu$l2XB%kh9yx$9PKt~>mdiM^iBGJyIC1PoxUHe%4Kxg+pQMV'
    'Gjl-j1PAYRuGv(AJB!WqI7wf49GJ{eUI?(pwzRLmU{!A_fwam>38$Yy|@N_`o0H5$U6zbvp+^7%1sjFl?!2#xRK25*Tf-mr>mBcl'
    'JHKXaBSXdFPZ=k`3^U{1*IW7Ye=(re_kMhaoZdT#w;u^6Pg>{1KQe2FN;Imr2$#J8fVwZ%#m3Grmo|9rkkTQ&nz45$Lc`UMsb7Sc'
    'j+fcStiIS2>hx0>aB%Squ*LUVotHd3-5qb@h>KIIgkSpaDcGcwvYeGGhgha59mv;BVcPI>%hj-'
    '436tvSk+_TcFG8Mp{;e0YNA*j&Q6niYnFBh|wHu+qy;UyP|YD<|H=Ce}L_XQ*MZzQE$2_u15Tt@hQS)q4jvMcmtL_sq{*RvN4X@M'
    'wWB~}>Yu1wV$!2@AFWTYFVr8#&u&H&$DFO5L(UZ$QS3Y_$k(4?AHENKII{Tv~xtLvs{Qs|%x;WAowi>$czzE-zP;ur&6C|4cJLB)'
    'D`I+kK9XyP&GY+wvWW;#kF3DNHAW^k&t2O|55PD5ANM-<YRsL2%3jSI94xDtFm3ahlIt?CTd28xO4{3b`BT(^o;jpdN{5G|jWO-'
    'HKb5W))hlcyv-fJ8$I`AHNS)@)WaQcP%Dj_Co&j#TO%P8miiWhg*Tk{TxQeuM?lg?KJZ^af}pEiXK{?A7<0c9@Yg9xJj`s8&c}bt'
    '00zNiuy)ZZUan$eg5Ec@;)bE+<Jk?u|FxZ}faxO~l~Il^%?=LU~-3A@B33JL$ffD2{HX-3CCvDzPWkg<$Mp_y2_1E$KwrFmr--'
    'O)ImdjNPn26s;c=)=PZq^CT;35sG-wq!ndOh@cd35|o;yF$E^%6^NZ#4$zwl!{-'
    '^;){n$8ch|_nYBR@3DEOpiPCPXyG#^+Ye$XDJEDO78VxA+9e)uBYMbM;ILUnQ^FjIpGR5vc+hECRIJ^t(f6J-'
    'WRy_*uneHh)nty{;jq)Ia1<LKr$9~HKu=LD&k#Y_yFiMpk&fU(MHN(Cq-37r6hK+7N^_dl!K$S-G`-3IqOGnrui5Uocb)+CM-'
    '*UZEU=O6${>_V|CjwMIs$DKh@<b<-'
    '8QwZz$dhzxvd3%V>2^i?mpU@agdZ$Osj0DCNQ||n3j)db@OM}N<Bvin@?Mi%eWY4X%aulmLDUSa(5wY4N3S-'
    'F$LX@M_DTbGjprYwFTth1;Y&^I^6wKlmHEkj&Ldf)s?MzFirhF%qzNh2@4$|}jMwb*$Rbqd@caT%*a(1FzP`EBo#r&}hQ_dPcLL!'
    'w;(yAyekU<fua7U}dTDr-'
    '(wcCPf=;4706_av9rju$C`L5wtGXlp%tWReAX#6u}UJ=N}3a3da+d|>#!qjqzovIf?r>>>=Mp@Rv!69Xdb$93{uG<;gMb_yOa-'
    '@lB4AtniNt3{nrn{}mj>u*h?+kO43rV?&v>HpDrnh#fIx(vdWvi00_3M(AxhSk!*7k!?uS}_(l@RDo`L&2|FrpP@85>Rdyz6V*)$'
    'p_x&QG27@a7wmu4(($kq3p7sblKOvXrc(r~6b&2`JhcMd9sk7LP_e$!Q;V&AfhaRLVIX8HUHUot8r6nyn+mc7d@|OV=uv4oV6%<|'
    'dqrC1yY=Kz~MB1gy>nwS6@MB55wLIE|#n!8*Y?Mu}jh9&7aFmV;PpY#l~kSi+a(rF?`V(9Rk?3v}PTP*A<(_bMpMI;F5(tcXVQW)'
    'qw{Ee*a|s*TcABeAQ>Fhz1TiiBKPOtXNbu+1IrKIXb*<odw1L`tmhsF);kfgzyexIcG}`?ExNSV%SSoS~BcO(VQYrDs&-'
    'x>Oh~<>TZsC|b!H!&<>|UV=~#(}B4-'
    'm0^k>2D_zFW<HBM@?s2PE1;f?rVYV(Z#Acq1>qtS9Mkc_vajvd1YkVnZs{Wfr%BOjN@z`FPCi!iQjgbqhyhhF&yG?oyBTk-FomWH'
    'y{~gp0SfQA?S<CoN{-'
    '5>R0+AZh+1?wC#p+iADP*$PTqP*aH(C+IX92Rh#@?rLvN1EB#GBGuq?Lsbx?`9iIwsZiByT|WV;dM#$cjmS1KFH>!kv@@<!_8E!6'
    'xb?Rs*hVhGdu^VSu!9~d_vD5iK=XW=!A)JzhWGnwVqjbxsY{n=Dzl=R^OG}V(N^gMu5!53A!1p0==2@Yifv`mtT%H{dsSQuDZsS*'
    '!!wTnn9WSjN*{{h+evjY'
    )
)).decode("utf-8"))
_SEAT1_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
    (
    'c-rk<%WhlQ5&RdexfnjANZDy@CL=^+8L}K=VhDo)k|02kEGF3n`S-|{NM7EquCDHLE+si$4M!&LJ@3<xs_IYwIr-'
    '}^zy9Mdzn=W|)5-hG4<AnMXD5IA<)454*TWwkKK|pEU;qA>e?NTwbn^YjpMHLSd-L|=o4b?Q$>xXk<->nZ?`NM*ez>|_pQs-'
    '`Kj!k?)sL6g4^Me>vpJc~&7VK~uwK7EnXR_}@L|1vJ9_8f&p)oOZ{B_W^ZkEk2i>`P^M{Y`2XEPR?9<6+{o(FQb9Nt|IzRZ?uoaL'
    '0Ivf!1WlxPfeBHa7+q)mWJbnMkzVPX%+6$i=uD;~^k5|`ke}4GiyN^#35x!yk6S+Uvmv7d)@zX}{=_j9O>fl8W|M2c^H^<Hke>Yq'
    'n()&ig7%q&<yY;R2qBoc7*gbs{4%xO(<Mx7gvLPF7R`lF`XIj>QebfHAVEYti-'
    '@ah?SbwbYvu@w>;pXGhc!QzRXWO5P{kpXy)il|I_WDEAXR>!kr5&O!ldX(ZkI9yXtZCA>4*?@J>Qe2w`{nBXsrFzy1%1~L8<{?9X'
    '#2GF<rGUt8K|jN&getpxrg@KqXib;Q;!RkU2Qkl*XuWTKmTrhdv|qx^`|fGwHIB=ba`w>>OMuyAP?9cwyB1Kw}uT3Mkm?q?e^|DK'
    '~K-DT$F`H{p}~;e)58Ta(E_wSYLnkHwQb#^Jt;>dv>4l0(Uk*eDe4X3iK8$N15^A1b2UapFC^K<y*fU_P1lDq2T<7ZC6_8-'
    'zB(>@z2dLg@^psQ0P2NVDRxMRT?<<BvOlD;Hni~Z3no}g#7@U7RciZrp+1Puz}2-'
    'EgYpi>||mCt0M#+iU+94jQ@Z5ZS|@<xbqG}uk+ELKiu73ZoXgN-'
    'u`qlTNW?F(TDDrVz2A*c`nM<D|73x4rZ#gCz2~R1EJLNm8#zxwsH1Y!z0q{R*kRUrh5YTee@#k(E$^5&5jV5L=<3+eM!Ya+AojN^'
    'Y#sM1M{8COwaVtj1X%tC?UnVx#vcrij5q_<65r1Zx8u2L0B+r7c_ai<V+mrc)#8Kz1-'
    '!t#wR_(Vw;WsTy)VKNBZ;Xy}bQn;Q|ALNv?@<&>>;sfQNz<UByWryVz25o(_0zIX}lF=q~rJbyCOo-'
    '^L!e&BjMP7ku)}?jY{@?p9VNMEA&TT2-'
    'DUDJNFx^VffMZ%^*ud@+V=ZoY%a(!Kvx8~Up5DUGlHMaDR22st1dA$GxH_cXSY+6|89wh)kmc?5HT0NQ-JAwIP|>{{PZ_E(}h+VL'
    'Ump#h?CR{LOWh5dcGyOJJ1v~8mCV|#>koT$hVBHamBoaF>sTyZsu))V{EXH5GduqJ_VwLy`NGy~5WR9NPN3W~7~Uh}eygP}um47-'
    '528=*hx$051|QS$d+BK^QZKrF7&Yv6(B**yT#0y;stjk+12XONCC^qb1KGeag}d)UX|g%CdI?d{F`U>y+qYVS$j++07M)ZhePZr#'
    '6!i|6f0Y}?sr19~-aLl>1K^epW-Zr_zTQgmyT`=`6-'
    '?3SVaWa7^3A8P_;BXeQ&kcyuJh%$+#t6ZWsn^bTTFjGlPj+f#xUv|@+Zl@G=P6^#Cit&*zKVIUMsAX8>+|H8h-'
    'wSvDcFzc@pL&IJ_MfCLO?c(`hS^L;j-'
    '*<+sE3RI9WVT9#`05+p9mPS|E4|8D~rfdZcyJy(4&u)7ObMf`v9FA(NgLV{Z$O$=n71%r&4xqHw<us%&7Gk6`S%x5!2l(ZPsc$Q%'
    'ybzSkJ+Z3LR0!1OON+vu42@TeFo}GYwM`MlEMyrfoEAO|Az?vby^g3||Kjl|2zhb{~S1!Cb$F8Pxbv`ODnqLt}4&#Bc3`Vd!thHh'
    'Y$sd$3#3V|VX-d-Z#G8McL)4ayIh@50#E(&T87`Dy8X3F=^aC(1_0+|x+{!^5=o-bd-_5zVj{(le3FeI*lWAjUJ-IvM&(3)fd#=)'
    'RKVi|ns!J4P)$TIY4c<9j!-'
    '4c<nDlUsJ(8hK;b7qb@BB$4zmcuXx4WLeb~1##uj96%7$#EZk)?WS4A{SmNg64JpsSYxxOQ_5g}>p7#4A>}DJRbT<T&T#Hs!7Msf'
    '*1?iiuyVl6rzWczdpFS@FCLbZ2yMsRWH1(K;)T$&iq6?^5doLZKMkN$?TRGTPAVVr82e1hda9mIVDu3Xqz626d_&Iy6l{x$%p`nR'
    ';HSYn#u>TJCb+Lh)b~Y4H1U7Dy8gpwg#?`Zn15%j{&{moq{*URI0g^5=$ShZ8TXZFW@Ind5*b3~U$TaC=5cqt0L^DK!BLi3vk~0-'
    ';YHX1$Wj1=L_S}9U{`P>qh(7D?|RHNk24XBc{VP+d=6?d?iX}nxis)t!O{r*1CZ3HP+ke#+p#+maZkHtT$o3=Xq$Qo(lN?<?2()x'
    'Lx6mUXbGBm=tP0%&Ty~<4MHm^USl&*AoC#RV4I?|#CsgB&bnk9v<iohX6{cvUKCvR6CmWt`$u{<6A{2>fyT{rubn!jFv*J;*y_wl'
    'ChTF0on4H{24Mnh*c=O|UyvNbSqGoWFab$I!FR5}VasqgE=iyXSdj>w17U=~_MWtddPs|)HS}nu7yU~2I|aw91<PC@lN%F_Fc95('
    'WDPUlBHTAS=Uv(s!U(D!*KF&cZ|QOzMu^P=GUL>l@O#$g3Il^Q-'
    'dC`J)&@pr0`#{_LGLK&BBvJ6OhPICXiiO7e?PfBqU&@xbK5Kg)*%83pLIJ<PrXm2Y(O8u@nvPzfve%HNrrU{m!T_wjVpBcG#t1{o'
    '_I6Rfy04+2C>`6z8?*%Gp|rh1^;gGDx=;6BP0SX<r|$%v<G1F3q9~*)x?*%q76fOy1^6{!V2&H*a61~)zKK)mgG(zun}k|58O|?Z'
    '34RFF8VkO%2u$Q2odw@e-'
    'm^++#g^tHhO?X&_H%?Xri3xMeNy@+%56Px#Tk#UK(VTrmzk6*hU?*J3xz@a57uG^x^}}j}!4rJY36Kgg_+QkX6Vs!%<9XcPePXO0'
    '7%5QdFu3d14La50z<wc+E_SqE;|4|3K!h%dAkmbYt6(1YPLC&pc-EPzxt^4Cf64TO$5>_(vAM%2G;K4S~808#9|euSMVhQXy_Nzd'
    '{S@A<Irk*)VKi`yKoJ$OJD#fJu}Mm}`yT4d@5A1eW|jAT@YJccweIzwB`y_~S2>9>6?GR-UtsU)gcB#sQDIiYr)qd`^j%kz^j$AS'
    'QOkc#w{WdFVKZ<$VR8LTKT>5{wjbWRjyx0kdJ9H%nh&vGHPFfdM$s!>gAU*dA>{LQ#|_*fPZ0&WIvfAxPgd;oE~$=A<y8HWwoidt'
    'iP^fx-'
    '$N2f`K+t^_o&I}{^{IcXf1?!Mks!;<>&ItL=;<UT_2NAUdbUYQ@9N7EcYW*+Mi6PE2fCtImI(=Iw@89UR~5g*R$B7l;>AI(Ge`}|'
    '&!+idk=f!QM{@3aYdvfMR=0*euC(Yldc88vAi=86=+F`pzqP%<rKe(mQzLX<l2D(F=09(1^6CX+HU8#bm?V))0}PtIpbnZkVzs1o'
    '+sWW!KLnMN%d_POj2Lmaf<8hAF_sc0@w<YV+?&I<!-'
    'xKb<ah2lMU4Uu7@t5)=7OU(OF1_60M7)V0lHZ7bhddv9Bgt&DS29@M96UUO$DY%Fl7*)905~UC#^*fg6JvbwhQnF6svB0Bd&?$<O'
    'N~&$S%dEL=Dmw1a62n(=K-'
    '}p+oVyfjYOC3u3IY|5;K?BsVj%?Q_^?9f#D*>qR)^Au^j%1s%mS}+Y=bNpNpY;D);hzhF?oeJ7BG`C@U)uLeYV&)<!$wcSsamV^$'
    'bL&72q+QDq0F{*o7$qGjbSaih5tuAQoK5Caw5z1e}7@*p~oKc-fc)35(wueE`n>W^zxLdLVvIQH>5&E1r;*X@^bV)tJpuK%)0Y6l'
    'fTA%224Zn`9#)+99<TN!U3?QcEpk0Sp1gpL)Hhr;QFi-&+;tY;~V#S_vM&aM!GMOiTL+B*1R(!l*3-'
    'eG`s@%B^(_<Oe!UIRp)}nSuO%VCA-'
    '{l>py^dBd@}FJY+X_g&>A1V3deX$b`jaNsnT@&8k!0|X6_f_K>`DSmt*i)Yl(m{zCz026Si5iujGe?tfAwRxmpg^%h30sMc_g(Q?'
    'bgzqh2%>hn$Q;LV@>ohgGwY;GPMYct`s8f?~s||RA!!AoRBMxKH-'
    '=N9arW_#yqNLFgO6H=)Y3II(RC;4V(tzTJ>=rDm52PgEC)92P2T8nweZ<5Nk>f6pk#pP0AxdDMH*&U9CC`^CZSnjxrMRPB`8};T>'
    'XdX~!xIc3!%EP|(aFGXr^Cw#=BzFq!5`(<aJB4ND3rudJ(6@yZw*enIzr{u+yUapu!=ze@Ib7~Pmcpv5w+2!O08A!CqLcV+OS|nO'
    '7|X_X9+wmdpXmlTytXklQen)82Yi}Aj#%^m4iq~{ufS8{o*U*Ivkh4;1^F=mgE2&T0&hOpvX^XPzE68O#>Mrss_<r6relf0JmGxK'
    'g4A(>gJ<NF_7G6>(h0L3@KXuEH0tf50HeXDlOKwU&4V7sO8Q|sdKVZ^-`?$?$i|Wf!D;OtI)Iy+Mbg9JjV-XP#!XMAaFDYI0X75Q'
    'jIr86<Eg^ceI)4+0ulUrGAyD$V$WXrK^lV%$>Ek!&B2nD>au#HsD;i)F}6mmq(56<GuyqH0(a-'
    'h<Mb5oUSaz?x#>E#oBpK3x?zML)W{IT;TMs5z_bE@j#aMx^yoJ4f+TuKsfP~9BN9!fFhvBtr+pL#xM%s3Go&MXozCnL(?aRj@M-'
    'kQ<s?12s0?5j$j}txJRoa#KC<XK!5Il73M37Rv5ni+@csRp3V2~S{ek$2fEfruLK8Ht?~v-'
    '_g_{K9~u7Yl;UZfO6@IGL<so6kAXxW3MNaXi5bSXK?Y%wfM>U>C`A2uS?~)Xauh;|yGo7eyn<%?NlH&qImHk_(dyL2Zg^m~=v6z`'
    'c}{JDt|3LRQW6b;HYZEMH<3PQfQ!mAsGM;vfjUtkZ`8e_q9eKdh$GNTqf#p~BAsk1YnRbMY6^m^nHc6T;sPncDn1x%Ga**u^&KH~'
    'wzzytcrr67M?x!~>FQ0&0Uw+V8RQZnGqDX=6&|Ls3hhjf_gfCAMM?bVitwWuVkj$fdhrJH?W2lUXeXHQ^xNP$0f&&5lPw)gfucpz'
    '$ws{C;8egHhU6UW@B=6i0S9?JwSXMX;sxZKP?$wI*^3Gkr`|XAwmghTK|@)dRWB9~iPiP0PBP(4c+{>VccTvPnV$zb8i(~+UUO|='
    'G}C3^&#D_?=}AR(UJ=!B_({2&JA>+hXr)e)8Z}stQsKRkqB9|+N5ZWVkjA7!p%^caCTJ8!yolhD)juT-j_!dZ*NRLb<VqqiN_fa-'
    'CnH_Pnz{?9Ki@kPBrI47x~Ql3NfZJ52$Di-fsQp7MD1*%0k$!UOjpPU{?75>Xfa8xOps#2v2bW;RSOq0GzHWW?okv=lL!&uA*r>_'
    'O5i9t5V?YD!-'
    '%4NkSHL+<#UN@ZFlt7+pFJ)m1z~d&y>H0&(`7R?>}B$zy0~)mv<iz3aNUvh$z2Cf*)kechVsSjeGdZoAu5}7p!^{2k92saL-'
    '3SKZOcUn+A4S9#q)LH*zV6rx4$YRfP(rKjF$8y2UH3F4+yQbKruXGd_;nhy%FgtJfF_T4#6Y(Tj}m-%>LoLgy4y^ueVTnfkI7q-'
    '&0B3j88yRQul|W>Aotn<i{gtsa7$1Ob>-'
    'A>sEckP^~p^5$Wt!pO8D7M$tdM{k8=;d|^a2Cxy7K=E~p#21=`^jM(_x!4HtgODt00>@I9v6Xc|)siJZ=3OfiQV8TI;t~`OLWy9}'
    'UJ^x1<dE4sqsocbz2Hs83a@#^f|5>Vu>=bHGB1?Wr0R*cJD6@%10@$e>T;VX;cKS!lB$lv1G7TJDmfPf94Fi_6z;{Db)~yQJAu@Y'
    'jtIl6pE^lcpm5|^_lq*~;ZF<Ia1(S{B~h-'
    'VOk8|P5tzUV%?RNH3TK>FVuZa=;UfiTY@N4sao=aWN!grAxs*l?BB_9JMS{0;iIln3oxO079p{}@US4*<NR1q=ju$!dqdqCM7oVh'
    '+rgoi$LF;ADS}m-'
    '78QqxRQ5B*Vqf2OrP}**a@~=>{CawWveM^az7OC6um}Jj7vLcv7*CYid;4Vo=#8%meRQe^P6DwF5MTdn2lD0$9SkqOC;8Go%sHjd'
    '-Fr)LTtjOl(aOp%oM`8#@LJk$$K&8-'
    '+1Zkjr1Tcg><j1J!PIQU{S$yh2d%594ZkH*$5PGzWvQj0PlQI3lxspQs$VJj6a=3VcARo%?MSC0M;ASzGPpH0(&rdCJ5t~*3f}=%'
    '<fcfZi7L@ADsddSV%*dyMqOBigG1NM~JjO3~h5_WL$W)jd)Kr+@NtoIw(S{d7tt4ril#YfWQ{i`w7Dxgmz$k{;c9KsF21cr|bR$!'
    'aoZF1Z$rh%2Sf$}zP~-'
    '^F&3$l^wsJCTFIt{VGj+4kKS$@$w3<x@i>ujCA}gvkb+xk82TJ5?4G<1vf6J8u9lLnd+^<Hdr`72T3KeGgV5eb_DT*34Izt@I@0{'
    'anMbn2RBYT7x$c3M$g-'
    '24<ih$FkfdwVJxj)@VFaa1mnjQ`qm`c1;k244f)QTE(E}RlA2cmA<F*LYI>j4C08J<c{Esdg@B`cych)?b^qMpd-'
    '@OPBd5W1DvT3TP<y!)cEJL|Ql{qzbL0FsMIB4ju)kjXv7SUI8=kDTYVQr3DM$-'
    'CN_XES)_PT(S;j~*Q}0}nt$1yZ++?v|pmmmQZxT;U+v;@01ci(ZRfHuxFZ;zA#1{jtU5k`03u;DA#BVv;o#PBIk?6w_j2>-'
    'g7NROvv-QcK~IBt^1~5-P5dssK}w%1IA-s8JRUoMkeLLEUw8L9$*+M|*C#V*aX?-'
    'Ll0i`q&7P*lhs07vs?+fJuo*HNw3TBGWibn%ZNm5+BiA2aDOpVQe^JktvOc?626-'
    '4d#cb%u&V1Ty{9na$y83wz)axU0uaRATpYdD#Z$-'
    'b%W47k*soq3~91*B>l(g9@xOHCdTN(GMoDohEV4VinQE1ctC6GQEmTgL|7{0{CrGZBq2$EY&?)At*a*PD?taw@Ul28*@^2alZ*wr'
    'kphu?4k0fw986Sy0=*QW{GBRk*Fgs?M_&$UDw4#ePowC=uhEL?1u<Y+E<J}0iY7P_Bt&6w3nC1si7Vg4vLt<H5N6I(f?#UqDJRpG'
    '2yQ+C*TiC!WX}PQb2q;he{5ufS_)f_j4#v|Xq#fX_FC5&Bz`xu2pbrA)|BT0iE31ql}}eIM3mI+1JfKZ#;GhDyQF(e0IJxi_;x}#'
    'Gb)Av&$evovasGNHEzlx{3KCZ1udC#i@DvqAPm=g=f?%`0G-6}sI-}WUPUEmk-xF)TM!&!DG4dE9>|}?M^(V^<#jm~jPl@O;m2aF'
    'ZY;^?X%Yq`HV3eEhluj*PS-'
    ')NwS+p_Nx+r&XDwrsfN)Zlc#`5AOSv{)5Ok5)_O@+Yl&ekEopecI;VL`bLM0=;lJ0$KjiRj<vXI`Xjjo;9;M(%_7Nb0x{Jah~1Pj'
    'ZLKXrr*Mt2yycS{Yd00TYNY66DCjK1UG{s<(9l3la3prhgV^a##IWIzQ<$vq34X53;e$pw6)TEXa?c)F(IxZ%RBN7x4(9>X*kX;w'
    'G`Wvz?GQB;g97Z;=v8qW4Wb<15(Ssrg~K@+l2Pz_-tDTPm1SC?y7snri?9^Z>x)O<P<h-3;LY^oi{vr~{stn^9p*HG-rJk`h}^dg'
    's{5wplfQUE2?G?T&<Leh<nm>Z**hty=|3Qcj7s5u`>g=9-'
    'V4oom81_u%jP^UymOC8d<Swyv!uufvZ_=9Dx`Q7vHV&4z=%}QA$wHhB-'
    '34xJT*NI~xfSRIN!nv}|Q3#V#lhu*ys=*(`Xy*X(^L1;g^)9K$>f?1)TRRQpV*MX60IehJR=VV2oF|79+9+j}G7+CPzfndDDYe-Z'
    'N&IPT@hHkblKGN`8nr+p%Y9-'
    'AwaCZBoJuAlqA39mpF2W5RHisplc{$5OR)61I++KNNauTrq0S|$#0AU3QAzS)g93~#@x;T&87Ps$@Yt?djr83I&laCPDKZDr3t=u'
    'VDg2&Zq^!Ilt8GbTmL$}TdkVE^M6C-'
    'tlxlDfQhx;<ECV4c=tfERHi8m~I`<Hn;L(m6P75mP27*CkfMJsn9o0&Sww#A@kthKX$u>DUMT@6Otb!375=y#-'
    'aMY;iS#%okQ$<N}q_1gy|AuJ+h4*RYT^Wz=Fyz~?{Y0FfdVbhBmoVv}qH4KlVYEcxnNeJAu4$H&#L_@wzL#2)azuzj18@!tj|a3$'
    '7EEPU%^ro##6r@lj+!AwS<_#FRr9&Z&+_Yhf_SA|+m}U}X{p$@;-'
    'C_&i|HFN(A_iXxIF^mPC=#5@7#0@t^o1)gBKZ=^h*DJ)dWR>cnBXRG5reqI}w_&RB2SJ15jvfHzl`RDbb+oVMj9jO3pc<;=I=NmE'
    '<f)8Y*p~ww9b|39adc4oH-'
    '7itsUK+$5y(voX{#h^QUNwQvnE<#>L2qpA=~SjC+9kGT2i<`iQB;;Y<R2Dy&0YMcrh6sQJD#|$%v(*}EnmJ!sD%@n4PF`3>HF(*n'
    '!N{av}C1#BMpyU)f9S}a9d8tjVz3BKS>;mr`H8BLq)O;Ro@|DbGSODuihJgmF3sTg$uMRC&9_Qj7wnW-'
    'dFAg~SteyZj#3j=QRxXl?S~sUIO!QYo#FEfd#3>U^yIB)cKPSfTDlz8ehD9Z=0LrMXRa-lnAuzoF0rD;b-'
    'Y|QOCT8i$zb{m38lQFY!5+a}LLwxh<HKll?bK%yv}u4+Lz5S1z3_WW*EJ7nO9+zJ&_$OvY(k8oF3)8rMZqyr_$>%YY7%B-'
    '9#YLD$RNN_HQxcSO$#(XWZ|;y@u*7HODWA7MB80)<^?0q8SnF(T3Qna6kro8a%q(B;+@W=*jI*qnJpL5sqsqDSh9Ux5hV)c6#Di2'
    ')nY-'
    '|(VkwhwI<tuRb!kLg$3iQ*M!w1NkzI{JHM0!!gclIjaEYyW&Awjp+`(vETt(~ld5W4ESgx{PoNW8of%#XO+XOmG<um_D=FEkjJ#G'
    ')qP0}3Wqiten=X3E7Ouh`v!I`7N8=GjpCa^K6w6E?>;z_l$kI#}pb0DPH0W{jR{7OZ6dtY~txQyArTS##I!T3-!?{k+fy9-'
    'ihdjGaA{dYBcGgg{3`7&&AGGS~x{cyfAg2>omkuw_>!DB4QN%DpOk6V%V8<(hom4wuwX87DnhqP476O1YSJnyXdmXgp6}~7_vXX#'
    'Z;g>pq31xDy(k+HgbN{V-@l!?Vtq}&sL-fmLEq_byJx!2%7t60QLiLiXpKA4(dIX|6l{D?$;0X(vN~0|ib&sQ9R#m8nwW(Y@xlS*'
    'A=F+5VMGINu^Kso>n9=WBmUKHE31E(d;c)t!bO8kiU1RUknsz~K7=KaAeAA?Ey4)zY)d`QxlHEAdoAMrXd10DBu%HaKWh^s_!)_R'
    'KhUzFaln^cH)r&k?#m`auoGIdG4+=AF(se6gY4n{mn^Ig#F4Y`W?x2EZOl>tkg$&CmtMOZMESX1pR+Iu_TFF4-'
    'P?L=zAt>ws^gJ|ZoP!iD(s|kLDL=6m8_lfBtTiXlApkEn-'
    'R&kuOf=^pRR*<tg9zo5XkLf7P9|F@i=j}>d`3meZ!H#*tBG*XjFS!2A-'
    'Jk6iMh;l2eCh8;5@7SNCI%AID@~P#(MA>f^Uw=Df3#<pBn57eOpPQ{xyy(3yw~pwl{ats4EA#`pN@x6VXx&)d1AGnHoo+1CNtufC'
    '4kJ)XEG=GiHb72&ONh>LqEZ!k?w31X{Y4u4f6_!~_Y2h@4QbGwujW#shP-NTp?zFc#^IOVRi)5EYb+*qqddt%ZHWl2u~uBX>k|!<'
    'Q(-'
    'DeOO_3C|Vn3v_#mJ+pfYYeLGURZEMKiHuc?{%$1fU2TnOK;}pTh{jH0cn8Q<WChT8mdFQulv~9P4h=xbB<hsOthY~#uK2}Pa*d*?'
    'NnvX?(C>45SA@qgoRcK4t4uCngz<wlpj~Qkv(ogcAnuV|zB9}^OqufU3>i2gM+-'
    '+g^Q~DyQp)<GYZfYMRp2OLVF7kjN*;N!JOhh^2mq{<E8LY-cIqi#ojYW+)oT*IT0AFQr%$}Vy<R(Fa=4OCr$$w9H(JT?9A)hV6$j'
    'K5z+Xv8z)09N4+m-jz@)UGQhNHSHO>`5Xep;w(=ZJ~p`jTOfX<=-'
    'jkT=No(9n|jpbE~Sn60087GneXx7LO@SwM@6Gwj~MD{~bVxquQ#bY?ckA6`ZKAKeAqJ*B{S$HX^Msa;zV7){<6Z&@ed;x#WEp!rC'
    '*{stg<O!Xx$D-$2eN29Xl#NI^;QU4k?nJ)4)-6#LygD*5+ej<5Zg{YG0jYs%@37#;B-j@h88XU-'
    '^N5uUfn&j1*MF|Ysn|QHyja0q9&ZR1rvO@WXD+>ES(h_`ZYU8`(qu}<u_i5@9=1Ya97m?4i!IG6HHGzsut6Fms~XQVV#>+t$8P4a'
    'n8?YNI+qZE+1c9Yv!ZD*BqoZj<b2ks*~<uY$Ea14uVz=vs_7+KQvbe|-'
    'I`6?eh<GuoSrT;ZX(4%Bt0;eyqFjz>quHzt{_jt0I~e4;tz^bSn~rzVUrqwBq-m<QK(hy4pUQ-'
    'q1@hwqCiHmE}Ne@W0091g9ylVEICF6ozP2(1-'
    'f7|z=wwE`Pg!MY9u_Db{&X7x<F0QDvyr;O(deb)mWBZw=YWhLBg`P|KwMA7pH0Kr~RgDjx+TE%#|QwxlnV;w!w`$2Hwv}Ci4P}_<'
    'WKaV?H~3|3B8OfN='
    )
)).decode("utf-8"))
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
        # Water optimizer (v15-keep-gate-clean: PASS/MOVE->WATER on CU1 when safe;
        # empty/dupe WATER->PASS). Restored in v18.7 after the mirror-clone loss
        # where the rival's coverage beat ours (62 crops vs 52 at d12).
        action = _water_optimizer(obs, action)
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
