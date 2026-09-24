#!/usr/bin/env python3
"""Seb (allegedly) tape opponent — local testing only.
seat0: top seat0 win; seat1: top seat1 win from 2026-08-09 pull.
"""
import base64, copy, json, zlib

_S0 = json.loads(zlib.decompress(base64.b85decode(
"""
c-rk<%Z^-Ea{QNG_hP!bNs8XJ$Qp|nN+kGjVJr}W0FPn77%yb+4F9`HvHRAon~@Qbc}_LOkyhQP*LmJ^
G9x1+fBfHzzyJKpfBx-%F8=Aq50@AJ{_`(?|JyGg|G#*B`}Xa{$5;O2=l}Y*|Nivm|6Q&=`s2lSFW&4w
zF++3+xLI{>Fs|1{NnQB`~AyTKU`d1Z(crpx4(UNae1}7fBp7{7vJB${P@nZSBHzs`10HD_WReL-Z<(0
x9?xPeE!qNLA-naYt!jCV$;{Bzx4XWv%kE5y>96EV?SOT_HW<)I<g;Ly?OWDum9c6-1?>Mr%pR@+T6?A
XZxkKleUh(M;qHVi$?tV&8z3{pS@en_vxVTIt&}%POa#~#{vCtY={m0{yVVMx3At?L%w~te?wc@-)@I?
-^0&4^4BKr*L<0sb-VHN%lh_boUHrZm_GjepFeHXlfE3^1EXLw-`xktb$E8WUH;=VEWOg}kv^$#r)?Hy
2N&jUz_kbOeqeB{;DL)Xe{6Qb%*Snd><!okota-I^ZsN-=UQB4GRtWDt4ExjpzS%f8(sbxoXWeW_tQ+m
v*p-ta(otNw)+UL1{Oy@WyaI#SQ@<B-i>+hj+#s^S%B@e(>utHLjvO_Gk(|loC#Q(j>iY+%;!({hP$)`
4v+hPjuR_e+M1%P27p!2X#t%5RujvIIxTGPvTM9QVq?)dnP;4zTH9BNDSYg4VpoqG`p;gye7S%2?x#QR
-@JSA^2NVy&#Kl{jxD;A3-C%Bm#}5;aRhU)JceKnR#q0Cjif7Y_b)#!-s;1jhvjtfu0N|DE{|_KDWAW2
_1f?@)Eul&-qno(*MZN8wJ19^;`r1Zx8?n09Q%<R&u|gc?Su}4*oot8EDJDjN5t`itr#a@b0XD;fA>r1
JOIt&2Vk=kTP|0)SIEtnUIV3z%eoM01J3-$cG)Gi?4*%_k$Wrqr}X<-CujY>|FeJm{vW^p$M1u4sbO?B
t;_E1Mxlm)2xvPK88qk~r^v<>^OD$ZY^<Vf8xsB!0}Pn&`OxrauQ1y^;1?Ex1kIc(Vl|EyMc8o}Dwt+~
BpD;ktv?Tq+t+<<)<S0t091<|1*V;kl*WZP{xGoSdYcX$U<~(&MjmuNO8dIjp2S&(M<nmgxP6aqa$NdO
17gOMLu7kSUH5`UN~ZW1#THx(1q^Ky?7i#jOvk3@u>J1+oi2!ZR#@{v4NqXtG(lDlF0D?jh=*oD-UpnQ
<9q5rlb0%sg_Z1NFn@CZ$fZdZ>L<ZjIRz!_3ouyZ8uVj!(gbEah^6lvAlZGG+A#iVd&boOyDNT5Kiq0&
z&fEdTzYfHMMUQiSvL}989x8Km2u2!cBI^W-2~C+0L#e3iMHo>qmIdhf^C({e~x+Bus43|O#-6Y{1)K~
@03w|?x9byC;w>i_tE0-##6}o#3c)G0JUDd)Z|l;eldvGBs{lltK1+i(X8iMbPP_Ec3l3Qrf=k6&fnd>
`Ip8-P+*^cwMSSw>04>Z8OXgJ7=!x8G5+P(;ao~i5d7BiVrl6W2TMcSr3E?m93p-US2Z4#9*z%ZGw!;H
lg^$uu<;u644jp9|7qw#d{ED|SY)y1w`|VpbhDrk@P?8Hfc2uy28)LNdM-fc7ME$mKdnV(VzV92t3LyG
mcr8yZZ8}zZ1f(72414y0xO3y;!aZAz_z%#w?SXt{_y<54or|f1D0m3tA9$m>c=mf_(`{SyAQ6n;e=D-
dFrp`Ob_HP8}aSCH@Amx_ix_(H9Rw62Rhk}clnk#IN$Q7fOA5#oO=-7SBg%{UAn|-qD~u#nKpp7Ve`D}
mpAfDRG*LkeeP?MkmCnWq%*M{MYBiA$d}`RJ68D1ng{M>B|$0?ZZak?$$4#1Jy?dR1o8bXrX3|aA`|BY
P3rNrjs4yYY~r!1wTrtlCe6lI*1tAN4ML<N`l%65hDA2XE839SCajr_gUrG_wc4lt0OuyQ#FI?POPvfa
noLPTF)2}LDBY(Jx1o+8dkH0D48&1V7vtp96+5C7RI!@Z#=>Bm@s)u9_Vm6WGlhFMTYI$JzvXO+R(*U0
(^ZOja<J!D%0olo1?S|D376&|v5=3aDK)pioAjEVKnQTWFmPn!O*i6uohi??;TFwuNRHoLqe*UyD#zHy
@Xc)A_Q0+14aP3>XJAI)MovNclttIIX&%dlfi6Lqo}SGKPQ2scCXc0o`CnXo87=`sruqCw<mc6^kAEH~
(AX}$M|RQxTX2GHcJHMCXHRFesdSJkC%}IO@{UQ839vK_7foDKwRHpND?yAwMmBNaDhA2UP27)`2gSK0
1lr1_CRZjB60o|1ulYe@1xYo}a^7plZyanPcVW(8{V>)DyC+_~C{~?kyw73ZjVFe<WVdtYxPOHW^@2mC
u*?H-zs{VQY{zz}CdX87qG)JSKaQgJ`2cqE8=V7~kJR)$z{ez1&DIVuj3^u&eF7d!DVga}po=w!{DmG!
4X$M!8)&TAP*4F;ZCG%RPgHfSB8aWrIiynQ1QUico&ggn3B0hT8G}r&BW#eXm7;tP&<DgmqvNbCs`O4#
=V&)!hvl*&Csf*urKp>XkMfb~C=^W=Mzg{jOoq|x8&h#LSCfx`VjBZ63V;CO)dZ(+i%F#O*omkeza7aP
8F;2Til)^Lx9v!{Ew}k39ukMJn93@54@?Y!+n2SZh$A2RX;?%i4*}O7@YFoyV&lMc?L;gq4YQ^jG#0P7
P9_!@1f9AR*}UY-P;m7whvSZP%9buI_OtX^dy!ZNABxuUOc;mw$t2mKgM)mfK6E2nXgX<eFcEpYk2{|G
^bk{ds0I^xD6E7qE>9i~YT{RsFF#kFjL8lG$5ut8;`8qD4oj}L4)-T?zI`4y>&Q=(JXC=SY=Dg^25`Ys
y@c^cPT6b*>i|#$^g-}GBf8ElcZ<+f<6AVT($==J4fGolj?E49U6b;|H!jmD)CyY7_y}@usN%Sxsb9j0
kcE;*a9I%A3s}~>Lzl=hJS84<7Rs4Izl!9|$UaC5M0CNf3fXmj*sHYb&fObU69n{vNRyu_6c}Hb63ZRz
!+@J}_XK|b;^klNXdr`bS$s~;+~1*Kt0TSB-Rsl4=IaFgHr(6oJ(Kn!F*u%N2Y#&z;<nBN6Q{EMU?Y%w
-L7{?i*wb&qRfx+nXTTb0F&7dd&gNq|3xFi)#x5C0>+xOxwQG9C>ig@-N-E05j4%lL=jU?Z|po=<_-wO
_{49FX3ru3#0-rhk24LBcagF@DwE_>Y;+%KRJ`&e?c|Y4gWAOuMX)N|PidqH1E|}N+cR!3maXWhl9-?n
l!)1EgxJl+jFoc-PkB7bYM3<mBFhy(GbV-=PGUc^xP1VLRybCyg(c^b=11!1C01c}gs{R+m*fTvqqjuS
*Bd3dHLbk@R*^=7n|uUNF$8QIpHUp2w=uqi%x2k^P&POSndXNa=nRz~DsF_1wvZFCeMkaWu#sWWwwTs?
W#a&<FL6zRLr1fXd1_YANp@8JeY}Osl6A1#Aryf>f(=stthvd))vGh-)R?VF4pCfV?dN7l?w1Xk*Hwic
kAVx8a-)C@;EUFm$Nh?2bO-lg^$c!|k*hQM>EJ?$VPZZ!loEOW(9C2Fu&x3R8@z{Z#4Lu{tpR)ep;0g>
PI*LZKz;3S`JElik)9l8NC5O9HQ!X2eP%&7BRAx-<VWyKV-EtL9EN?m8wv^GAX%i4BF(9el?_52?dTwG
fuUx3Gsts}-e~L_1<Wi>R+4?u@FhVPm7`iAmvao7{B!b@oPZ@}vJv>P&KbZE3)QUc@l)~_{kbV106Vt~
7&B_!q|2FkMxP@|b-98o|J0L58yG24M}*d3Tr6DjTQ3hd81Z#T{qY7AvJE+u;97dVvHp3K9;!#c-Rf&1
nc$6MnHW#-qF5%rPO$e`fh;Ql03z}6HOW<NEfEc=+8#Q8i{mo<^wH-hLy00WCD&)`5$k$2cnFI^>t0On
4FO21z44dzw+x4z;3B15{e-3Q2x}_uGJIt$;h$qBNG2%%!ucw^@u+2&&!KRj3BIS(Ge<XzEz0!LgCzHn
B3bd{)Jj&|j;1sZ%dY2<;5j)SKIxt$Ay~|O9@X!}3R3gfm1__g9pD(bKg9@cPt~BHOaeNiJj>TQRXT;k
3$PMO4JmKep}yA0IUGER5D!r+ZINhl*n;4yHC`a7q`UU5=alQE=`8|*wB*RqD#C(Pt;8Kp0uuuBM=fix
=aBE|O3-)jkvwRO`^bQ8@Tm~f_V<y5Qc%~aCoI<HxPjK2MIjdj=8=h%y9LkI&*)|VV3i7+6--@d%T#dz
r!JM3Q9WYNO?<}krkY@q3_|z<s!WiRSrh|+2YdR#Qv2n+<oeasV@hlb{`2T0AaawIp3EfV-pV4DRa3k%
Y>b2!czH84B6Yb(yf1R2z#2-^FG4^>!i}Yvff9r2K-i*12E6)oHTj>H<NE7?hM;gyg7o-%iB|wPse(v>
9uph#(k~kLGV{NpY72O<L13KNijz($Y7d~A#;ourC$50d(%E=6+{mUyT3yGx;O*&3GssaO)EY1V%6*DP
?;J0cxd+jfrCU8!t*mvqljo%_VG02fX%em`*`0Ih%Q4V+>FIhmknWE#vRDR7Vk#VM({O=<&^RFHoAchG
Mjo4$MFYhr-88076(wI-$CV;dPiPKE)~HUxiuCD1wAvmqzXwczkGaKg7p5r$5@G#9iXN__@|_AUGDC@|
h^>heHP{FR|CKU?qf5K0T^C+yojg<l5K@7|X=uscHsvAB?x_>7_Oed>ur!a{k_NU?RPsKc?HDD}2W3Lk
q3H9nP_NU9;*}M6T-OkZ&J)Y2vkH|rRYo154o5m<UT0U(!H5WHPl1HgCL)?753&jl*~igM@j4sR1dVlh
c!iZByo05+P%&Aqc_PTGqTXYV*Rt!VWU#Cjrbt3Fp}?FpdG=Pgm+=7}Qsk3`-7Q@ep7pTB4Z8Ii*xFlB
b&;FX_a>-_ir|nj5*G7BhGvzbYMchrp=eA;BiuRV3@qS!Z_ki!B-O-OxvV91HqTSJkb2;}k2SHN5xo+2
6j8+iH-UC8!I6-8SdhyqAhh+}Cy4>2(S&Q4P=&8yM&ja`Kz7m5LKaV)VeXQ<IZM4~FzGI#l7asF(S9Os
JcpmmaI6S4S=w=NouIIM>!B#3R<;T{i>TNO=tVtdM;8IKrVy5rBQ1dQc2GC&CI56FKB#&?X}#6%sQ|-1
emQd0d8^iGGb>F>?y$HJ&^IJtfTk3R^fZfX^Nm6zYba?PhJ$jD96ZUqk7$gSU0M1k%MENz`J;c(9IQ?*
kDo`yIX4XWm|Zr6bEz4z#sO+}XJlepv<)iWVGe4b*PiT4>@9ainW3VJ%k}1(YGs(La^w@m{naO>K(Cb1
$4ogqCf3yAq7=w9Y-@WtfjZIfd=N0<p3v~HlVsP#D3Pn8$S1XmqZDPSl&I?N9!gT;<@?OOSMnSg1`h~G
w8EhU4;TB#cqX<BX-$$@+-wqAX75s!*i#4aR|<YEjZ}+sv8H3@!OCM_+Ou<`TcT0>I`PXtUrNd=ZK0<1
imzwQJO>z?YO_Mkx@^27ru<fcp)|2}8-Lc(=a4uP-4Nq7-I%00>g?$@X{9L@)a2qlmOSMt$g}>CsAe4i
l$CV_o{d_!{l^_<e%BF`Gzd7yo)DR62A*iunM&^tN6}}!Y)I9IvBf|EDwi||HWKy&{$ZdLH*=vwQ<0fU
qdb=DLI4{n%vi-YSy~B9{plPs)L~^j0a!$XdSx@SM0o3zX~8Mz+3Zi}HIOJ6T@z23cp#&NUifsEfY@)E
0!zm<X|icP6NN^+dcJcAMSG*d1<j^m3fj)+r*CZ;dGjDKuI%KOZDJy)U}B+KiC1c@li|c*jq&Utmmk%c
SK{58j=xLNvB^bkR5~m;492nqdzS`Q&%UaK8k53z`Hog}D>dUMWb0woUZ#@~<DoI?pUjFd6WF9pijyIW
XznH(ORIE`M0h-=m7{n$DM#X*>YT~Unuz$>Iv&EV)hHUxUG?=_u;MdI^JhJ8CafBLW0WtgvW<)fDi!9W
q)=T8nhIvBQ&+^Q_$WRfpI3icou6wG!Op97#mEITq{?)yX=Wq8*_i(BdU!XU+%gZ$dgWZe2Jq#|ws#R9
?d~QS?$uSuNm>if@bYGlenVuKV#boAMS~Js$Jj7U;hCPb5=BAW*eRosv?^75xgg-YWe!bEICQqyu}QQ5
U84mZ!fZ^}I|fh$)p9GRmz;;A1M~vCJUdTMubCi1c~>ruNfDkI`<Mi$nYa`)`rW{0A4OA<%8X{^)LAD1
V4x#Afe$6hr!abv=Y(;D!Ybh8gxR&cigbu*ms22_bUcZZc{mw%8_;#9HkH&LWEoHKADR?IWA37M@}NSZ
f;SLvrb0Uc2e-3(>zPdz1+RGbPyv`!f|jx5H{WsVOjE|H#Vc@V8?|j+kO3;QYYm=94S>&>LmM6z$(c+(
S&l9>>J_Xn4%i6>&KPAndex4dLV9*46bpRl1y@#toIpZ4R@{myFH<a|1~~aZAFX>Ba)KC$Q-xww)ijX{
MY5Yt*Ega}tQOhncg^~5cTmGO0Zw`JAfhj416XW0MS9bPG@=H}#xA^3vDCqBFJxmW1JX`$iH}DQzyJ@e
Cr!c4P_JrCmxdsOcA4u+aR3?v>5KLfD9)1VF-jP7gl1Z%5wac#VM42Bb^%0B7W}}2eS1S^$o1^HDMh$L
`?N&5$w6s_UTMM;4XjcK)0AYHTE!hZ=Snw#NTZl~I36|Dmu;f6xSZW^O-y7_Inq)GCn5nSad<m{Oy(c$
>ngThoZBz7Tq6?@bZOd&9N|fDR6t^c8R^M}JeGCF<Yy0*&%v<TAtmXCQgp(9C^J7w$d(&-s7#cbfP%S7
ji*pfc7_%zHTAud3JtC<JDK5>`e5%VbblPrZ*@pEXe+8tDj3dFH5?#^(l|tGcn2lEP^yE&;@GLc7*MW`
poUdzjM7&&sDm-0Ji(@fcY*O8`-0poP!W}Xfn`YH(KZ#MNZyqeqOKJ6@FZnUSTz~M^CUoByRQ!PDOY@H
sKu1)ct2!P483buIuwIU&dBp97TRVR8=X#HcStoJK?&BWF*0Vxiy52bBO1D!tOrcgggBeWWPUk<rd^fg
eGQw#<*N9XCsxZfRcbtSrn+wJCY<oi2V0KdV6kHI`sz*dTHWM$5t$a2Rh`o>-_t04XUjq(?-tKpCF;(@
!<3Tcm28&D72_+tFA(!;EF{xg>U-VH@TZx_7^I=&9s-eky$`gZ1-u1`#XO3hpuU>}?Q&Qmh~l@AK}vHm
D8Hk3qqvN<1k<zik9^J6f)KVRe?`^)Db>3}kZ_~%J9`I3yPuDvSE~v@0$9j5jHCUG#0s-W7#owKu*4l^
9{Cf}#cc^2j)kVZ_ZqrSR8Ok6KeC0eU{tt917s;SKBhqFl$0<^ES}&dC%hU5`g`)#0WGY0HZHw1l(E#|
*mN$#>w4mnNJK(a3lR*XMPz2HRhlfDs!VaSNb`-4#6<XutqM4kjl7F?v0WN{jp4RJUC)C}oFCsC1bJhw
5!zfhFgfHnFt~<QR)K30EpJZMnVLctHim_CQqTm?cTenq2}Frh4oexqrzO~8Ktcxq_o?wgX@XG%pBZ;_
0h^krvbR*uN(xvA7DCBWtYwC=!bd$33o420xR6!kW;j}n$5B(!R*27D5`Ry#^|_G2bxTW);k;&*vv}Ck
uzi#mI2}b_j=}PgEC&V*ZoQa_*dbMUnU@O_pDP}Bq>M403XZK>L<M_jg=|vFTZa!;4#N&F1dl$@aD_4T
&F;~)jCY}NOH|26E-%M1KVxdok>%lF?+Jk7t{gb-jnO^vF#<C)&%eJ#8FcfS$&OxLt@=?x>nOtwnYD&^
QxuIrxn2%!=No&-H(w8$G@^3SMuN`E+@XFHlXvB3INO7;3e>}C%UI>REvUPX7cnp+qC+$khY*DGC?9)u
pUfD(TOFZ-2@u^4FY;toN=_}0If+dUjU}nkLPcOx@$zPXk{9;!%1+h6s}6U=oEJ|ZdTVWTbM3h76=OFw
;FcZ@X7A+mQF2xW!C(mE3}hW@%bQyn))DHWQ-{4#v>E~K(a6n%I$e<w&>T-v!&EF|AJ55~)98?L$XKRG
c1q0<&oL{R8TsuQdA9+Tz^wK4-iNEe@G4TBt4Loc*KbtvNldfPls1}Ej4hvH!FY_U6V5p-7Ge{`J!&?g
atA{M!^SZTTpOJ(=Bl{(h2GV%LSgD%OM=|)Zg$6+HMQ=xAC;)-^xtZp?+d%OR}-7Px~6KsQwukJsl24?
mg)?!UCu1)tF{>MkFfp8?uLV9x)yyw>0#r8-;JgaTXS+HYj{^Eeg)H*VZ;bm9o5aMGqgWcmWB}suW(;(
d>I_LrI}8(339~!K4P+aQ%pE52Ct;EZzJ=RiR3Ys3)`^GS+$@cO>9xpCY0(jaGJ?YVUo@`(6yJ?NfY!?
6c-2DpmBb2G`M=Q`ZS_yx9Wf!QU;Oswkn`Q-DGh&ZlasjWb@B#iYFkBCBmzC9vK~Ec~6)nG}(>%5jUO=
$6{%1#1y%b1>H+5kHD0S?v)?0^E!+{_kkwlt?M7d`yi@j49dNcaF@6=#1d{7y(yi>#P8xg0eUAFrAsqP
^3Ehi3ePsn-Bn(2vJf?ptpk~unWkp`Y{8<Z%yw~|h=W#~xCl|Kbu=<>{PTlEs}ra*S1%|fWl^ikCx9~V
H4U;FxA!h`PEJa1tx{t18)SV4eDl>6WpYEzU!wR@y@G>PNQLgeNyiF3v1nBhD+i*dI(y^S*d)a<$`RdG
p0hcpf>B`UbB^f`-}salC$Ecb1S&2%0%vIyz-Zbni8EOS1{zSx<I9zXRgzaPCz*y^C}GH^K=j;gnO3#;
@_0;boq4DrWAK*hm8#S(M-kw$f(R8d1Uxow2dk)~@-qh#(M`c**p)2sM()85F~5i%v-@~ceIgj)$>=6m
iesRBET4AlT~-=^+7}}gUGk(;;J?I2m_O=F8)v-W?0qhj0z+c;l5RORY8n<KS~=*I)enYr0b(ThYASIT
n5P;?shnIiat9~HXnZe}E3Sex>w-X^dax>8lAJ8+oRqbxCGur*T1ky3e~oy>mjZJmW}pxd+=&$1#kW+7
BuFr-@L^+L{hZ7w-y5$ZuxLCW<d(*M9ATL2$#OGoJO*^@OvubgA*aC?J6tVKPKFsJqMpKxYPT~;G#(MZ
;97bDK8L()5P@(!$wR~AJW~#qTSCap0Jb%A2UrU6z-K~-d<a5Nd7!Lwu#RZPm;(oJiO>msj@}(7gjE4l
r()7%o)CFNjru{J8v1~(sTdZFZ{unkS4d4l%9az?OJP--JJXSv=|NJgnhYdNsDP`=qc2rni5nY|Q3@rI
i@c~wSzraGksJH9t3b74sR#^$mU~mUwzN)^Dm6UyD<XJ+jmj#wdGM#3k!M!f6FE2xoKt5_#wMvqR#adB
S8|G?Mcr_p&2j4{>tsnSl?T?-+8M$3{47=7Tal?%R{b}-s8ykg)tEltT#r1VDx_RNsFj|UkV1h8XTAv7
o)qBi3^qdnBdimtrwo)U1Gpz6eBvNIkLD0=W+OdUV@MD1eIN$(=*t%K?kj?}5g~etKslJEl2i|>a0~M?
V9OQ3!U5>!>~qx>Rsy+1LzxW?(c6wC<TEZ1HQD9^L%3cRQ*Jkty3Oj7s=mjy|LC%0CQh<(g|)G4SW})V
;w@qcJT6)O#TJqq`Hl4w+HrazSf<5ldO2pc_^??lK81N|&V>qjq4IFO(h(RYV<nbawcG46-d3@CTbN*E
kFe_Y+Wq3_7()v>GS=N35Rtx`sui&6gbqOJxt<=XSb&3CwZOM4l(3H>t|cgn)Mm_8ue-`et>v`j0xN`t
l2S}-abuTdfgGQdOtu5(8PYJa=67~drfM6ds>nphd#3VJTQeG#Mb-!d<Hj*doTctiq8L?;$uw8&O4iBR
12~8k5Q|vKil6B#$k@FGC=PcgHwCqmdvx<#+NC(zKu?N-@(+&UoFB3&QA{A}lH(oyj4DKLYa$7;k{!Mp
!<%0I?<|=ajg{>ZTNJo0j6ef_))ktcT5=qC+bXE(F`EXuZaD-_wIGI*j3shi`<172C;%c1pkIde%j{`(
3rFSrW!nTl{|<>lhAdNw7Dju3N?kS!<X}@(QebLWnwdh?I6*_;R88Iw6`H5qBgJ5<dGbC3h)uAH!3&{*
3O}!9^pDsADvL1UlbiBHjvv~srDhdO<}#>Ui9(#GEyWe$4ce$M%Y3g09uI14`!oQjWFf<|sO|$Vbrln%
uKZF;etOrzty-0Z>O0kf><ky;>vthWpB=#?d*IBphjkJqjw5w+DRGThf%-AzAQCLb$blL{m**>j6v8Q_
&=SgEOHwe0$;liQT)GTP6~{sQ+QcSDu#msKbO+y~5wby9V?|og`dQF$8S@m8SA5?;G#$&E5k2!6Qco%R
v>x2!giG~x08eMj3Y#OkJen3pF>b07Z(SjCpd(PEfL0L*n8nB~I422(H$@C}&i^TJuGHR`!1akI660yj
*&84w7LY3nl6<N}Ul+l+wsXR)qTTEX7Qzk_(&7a#-4&E}$~K4JNmCPM(Uxp6JX%ZLbao3c2gRYSI(P&@
wWr^x?#80BS=KwP?PZCKb77J;k<e4yIpk!o=uC?^d5LM@OPHus8G9?V2q?5{y;1{(=upCSE0AVpWg`iT
se!Q32`Lf4cz;b@XZKjqE;J#Y)JykpA)jcdGPA_cyxD#5QD;pT#v(R?3}NaeHzkR>&Z#Aq65or%XDkkX
Xh1mj$^)SowdPohn_w4l0I`lyHvW2@c}lAZ?J_Qk!V3v|g`>Zv+^MM0uW&DGaMp*s@hEvBYnXR!nzW**
@KYPuX1mdWJu(Ki<VMY{q4mX~o$KF>;7`+mk064&-IWMRT`NxYk&8yus}^v?q2{3bFciJiDfy>Y8-RlP
#r&dLL36m3j!1pAjPK-hK%UMLQA27kVy9?EUY#TV1NtZf&Yq&`4Cy6D?y6H@K!>IU!$BWH(5JU!`Cch+
sxww89>pF`AE0sl_=2mfgkSZPdrH+b0oL@GMU|z`4#ABtQ9wf^@g^c&svw>!0p2ds(2~ROvs0YCU)?L7
)(=G~vWzsp(z%_qVSC3U38_F;1Sno2u{)#{MB-|sXo4a<gSd1Hg^SCZ3Fm}+>R^<F#Xa?rBFW+bOo-Z(
7_TY-xiD{XOj(EW3sjeB#*Eq12EUA8TGmimtr`VSfW=AQqaONG-$UPZK^N9XYTgs@Ap=|(R2*QEh!bY;
jf)6*-P+FVRTt+W18`8$;r_=x6d#`%31VNMAbLYgrl9RE1mDYvWRqlNJURe11!)ErQ~Wub!i-%>)-N6j
?DYZ35JsM1b-Pr5?X)pfC1;RHL$d=xCmGP<d8M;Zm9+_|s<<9<oTz4sdG)(nLsVs7A_9bPhuUzczMR^*
9qz8k^6-R3_rCPX?0hp(&P~vsp1=5K7Z`|OY>BI0DU(h$80kuEcjDxVSC$+UEsNO6;PWJ=sRX(%AcqrH
K5dU?X*pNe|9%S!MGtidh#KIT#N^|m>-Jc=FK#XOL$Mwl@Zp>XF?s=pvx_fUK;fr(Bt^Z8ZcifydLVdD
G2%WYz7EDgjpCRuWDVpT^UWMvCJxK`*)H=HdmL9fdLqQ5J&<G@kGQ}c*j>H<B(@ClWk~-kF8QMf-#kr*
bfbpE_G~Po7rP4>*9lrt+S>%Pad3?Y<Ypg!$X*e;7420(l%5)u5(@}(E#e}`PV~NQ+jsTTr_gk8(F-Qj
$lP(Ou@Lz^(~=zg-hU;lR~XUxR*!F?X{%S6m&)>~aew%KIn|9(
""".replace("\n",""))))
_S1 = json.loads(zlib.decompress(base64.b85decode(
"""
c-rk<O>bP+a{Mn`b0H2%S;~%<=0(DzEkPd{ycmLEATJ0IyeypTg8cW$B6Vlxc6C*CpED9=dp8`;%=tdI
ySlpir~f_s$1lJB=imS5?4N%6aDMjhzx?`-zyJF2_1Wv2w{OorzVjcy{MWzz_iz9Fzw?8S{&e=@<(uut
|94+}|Nd`3zuj)1pPirmu)Tft<JtM;>h0Z&?ajNh^NY>r_iuiD`NPfa$NxNgwL3fCd^qav_wQfcKL7b+
r{BH*)I!?t*g|aJ?ThX9b!g)C%V&Rm|9ap4zKx&GcH6h_K8@?gS8v|E`1I<20uSFxKXu&6qgJ24dG-42
sIC2%L1XKAfX&NBm!U2*VRrzH@%HA&cguWx9k{)Dwq4pkYW?%C-EEuBG~B$~zDc`rw-sK$dG-ALvv&vE
@OUqL{<Xs`u>aZ6L$((RtCCO3+gI<C(ZR_8J+#)yo1D*`f&F7!X5V+dM)t8>{&#rPv!RZhp7yT!%Wqdv
vTpPQ)z8%Z0N_Dh4GuQou8ubspEvVwtCq}2=+i+Dtkct8m1j4rg97#n=tBRV3$s8Ew6h&%tPwcK>l1Y;
S891xc<6zK*<M}V+0R;IEw(r7^C4Fj{wrU)&KlfrMf1wozs0UHITheYfO~s+u^(}D0lYbgH`g);tTXou
T6&tq>E7Q3p{b<-@Ps}7FuMX)hW61Uh9+f8^P7|}N-ZsOHr&t@ALQ7nxJWGi{bfh}3bl{#ckLJP8^94h
wv;YD{R}jaKKJ0+tJ~Y{vv)uLW&7sc%iEX#dVh$P6H(|6Gd{rB_xmyF18@4{4{UFLTh)Va?fty4OdETd
;=Ob4pB=pL4SM87eEu@IcEBw4@76fjW1Gah8&=(&^Q4QD%zA(~ioWsD_fRLG>C;{vX=nj2Aa84Rs~V@l
F!h3YMLMurp^}+ZYDhd1;7HHC4H%)8r7>b}OnEA1=je0|b)NXWmKsm|2i}l#9ZhNI)W+DK4gHZC8Z(%=
<<hi7A&OA4g<JmQy+4Q?N`^C_{{;iO>sIFgHE#LtNiiFSv|yHi=`h1T&h_$)19+as`sM%#2#B|){cfge
1CCIkiGuqB-q?tVH|hHh>H#+=7fc4)(`s@N+~!R$vizH<36F0qEiM+y-HYMI5H=jFp+;M)@0z~H@O&mN
oYRTrPPv~P!!Nk}AiA@dd5%$@^!@HPn!W(@Xh&VnQP*HjQ>Fb?Kze3c^1f^Pr#bpNw0j>uP^`_1CI-n7
uY-qA1ePb@fz3%cuqK*_ASHJYvp7ez=h&<Sg$DgQ?Fv}VQDFhP5b=KCU{Vgkw?~Nf1k!*)jn_7<va;!F
b(~1FF4Xcp9Um&L4D@>KunBMiyy<RDfB>%<JiiY>1A;<hl+4^mqokIT4gWhY>NeWdhp8R#jkM90e4FN^
Ejd9Q643b5O#HK<Z^^>`{Q}OgYqUqe+(t-Y$7-PMu5sJx6j;Z+PoCT_Zr=QhngeP#c&xfGQ>3}2OPt?9
2fNI;99s_fQb=D}L=E(J)oDDX`^ga@4H-;e{a!U>?<NQ$b{5x*YoO!g`hv*_V#9F8tz(lnPLXKgesxXX
*!SV-g^PLk^UH1m(CE>;F0DHgOY<bwfHuZn4;z;_KW%TZ;Awm7&(~U$w+(HZ1~e9P`2Ml;Sh^R7QwJK!
;wTQLAHBr*BThpNcXVDu(80L=G+ReAy-(1)z4`I^iYGui7>SdygVd`79dX<C9Z9q8&7*^fDS2cKF43us
aFm?+_T8JC-S^u!Z~k_6{xr$Z{L)xBH(ZOa+F1|~8%K2NG|tVkG)T7~WA{_8#ld1_qn31P`2l(HGmw@8
fBrCZCj>qlp*cAPd=#kjC8LUl(GM?0nisInc`0>)<qWCr<>_#%<!rbz(4^#BC3c6?YI>CLoDpSocJ(Vo
K!fDI$rZ?8<ldqrt$_aQ8%`+(JXbQd1E&NvlV|XC`T{%@@O#Vw?zGAPWzZ^UBC~*o8(qwpcB5tPK2(vo
_~0fR#9o1}d)DBLCY5Dzn)dhaII0RKYMTYu?VWO2-6@xLtb{lyGC{-<E&ztI8CL{0!Twc+2{$%(#dP8Q
e1=W8pT_Vn4Gxk=RQ@6djB?0-8jarfm0AG~v?~r_kDgmZ@WA{MyU-4qwCOF3+aKx5+AVoph*S|y9=6ai
srxgW@aom=A*2F$-Z|I;pm^6--zTpQ(e7m;?XqC1XCOQxk7bvr6740`O#qhm(=p;hGe*R~bbvk#%u8IV
7{dT<M>o0w52!SAfLA6@hZ)F#!~uxvg9Nzs?Mgv<3fF_TbR5fz2{<d@=NptzYhWdMfdE4Fj~!U<KQcff
y^&co^{zQ)sJ53a{HH_+k*V2VsUZh+FSRf6_&-TQe>irM3XEJldT@~u;ScN#7hpU_;^O4gbJ!SNYSY<y
U?M(ofE_kCN2!N!?!`@Jr^6y1R5dQ+VA^ppqAdv~0)a;BSKZVOwDM{AKr#dEq+mZ{Kr!A<6amaM!|HS1
Pmu@WOezf@4TP6ie>yRg-bQ3WQo6^1mA~%(fb%1Dx0ux5I=+S9=9#)3Ur6=@?d3M}FRmQ*&rsVWm3v_A
<ci4;fOF8ECc1Xfl|l?GbqQAdT;g+rrkQ8&lHrOPbQjFNR6Zi<IO9Bpm}vYu1xcI2VvCDK!7Q3ARu2o&
>;e)x*tf|-oZwUQ;@JlC|J)Ibo0Pc_V_vDyYNa<>^mmr;HZS}F2w0R1wqLBT$X7#=X6gmz|7=D|)--TG
Qj<c_qfsglKLvYPrJQ`3{uJ1JjYyh7B@-e0LLiUDg`zeTkF{x|reTXq`-hghAe5Y8HBy#|!01L1!I;3T
&?Nh%wFs*cpm#64Gc8SfZw9%V7NJ+@F6}>9Nz{*KK@h~ekX#;H_wr3h>m3Q&QwX!N&Uyk<N!NdPdHdJj
_WZe{IaE~iWt|2jyV-)m#7Sr{28odKDcT+k0oA(HAOw=O;~hAxVT-n_RgWd_B@sP;fO5!RQy}>vw>{gF
!Y<X?vLxl#ju4K7XqXm%OG>tB@0G#sB7DYeh{=ipxrGkvFs+MVA@6*DY8^F%n)@K~AC4S9oH6T8>VWtF
i+g2ErfwK>P$L)5kyf<gg_pRG=8^i!BE}%L7`J3AZ<}@nEFZ)`;s#vqk`gJniKg)d+mQ@(Fn3{C6Qk1b
d`6BQ{8$b?O&1#jJ&)TilDl{erypr|#GuW{AE2kEH77fL#gZ0rVnII&anng5WTZR+#1o+C1sKyh{xCBr
$)d|(lU5>bE8h4M(<}l*$jPI;#t~rPPYTN+Kmy&+dl!NJHzJI>cYqX~P?crq^>d>#y*g69+f-sNQtfey
3&B{KsN<6m&?!fu!c}2h6|U7n<r50sqGw)JWMvwY+aYVLrqJvnC!b81M?Z<#Dhyg6%Ww<HLW;e&oc(Bl
kWapLoV3NBwF<nWD!oZ`z)gj-*|LT8As8gdIslJ2zw<)@<m7<Lgb4;X0P}RY_-Mu+cnTK$R6nCBdM!~$
t1z*LUq0cZMM=I91OsUSQh4ArnPkAO5IBdsK!xnPjgk~cmMrjen14xmfW<N?PI+=cv7{=Va=JUj;(~;Z
Pq=82Q)#;GJ<5FeIK6woUY62qne0pql~8lg9fAuM`))X+5uC1n@dfCSTy9%C$=MBe+1GJ96zQC9B?XBj
djWZ1OHdj`F?gJEx4^o|b4tG>e4Ys&1v{>up3Vt8G}b8-RhsLRMVpU4`}k$S5>0%Ej4P((do=O~%^5XQ
b2@fM<g@^5LuqWOON6uO{6LE<RYQe=89fd8$rN##6aI?^GAJKH7=G2_jkW|Jp*@&#@eCEg5mfELk{&b0
0x)<SVol<MoD}vrIsQ@0`*@VeFD2>53H-nL(2%onOD2eFVL6eaSyEI47<pnIFpkg`UPTf%-s5TKM9)BK
(Ut_Nd0Z6@ObCFf@Fc5QgjPR7JTxy@M5x>37)X(D6E{;$C~V-6B&(@GZE9tCJSIkF;Zm^^Lh;ncXGIJB
9CQ%*nW$DZNc{1bM0uk1)I4@(hVlM2Qq39d0o-kT3)geR1-GERwULEh=7A};7ICB|F;FNv$sZ{I2gSi+
9FLuighN!AhmRxn&-AXGG9Dl}f;R;bw}ike8c39e6WRAc(6wE%Bl?mI*e4Qg5*)5@C*!Rx;U{0=4UO4{
o-2uyKou`eF3Qihi6w=UxrzzdR3(U>x52=JIqL=7ajZfPnIECa%LK{ON7po|K!AhUV*dOtouWL+N~)qr
Uz34F_gS<o8X|`NQDnw=Mb;!x#R`Im=UtdmjxL5nBi*|w9YDu*7ovHZ72vse(3lV+$1GCzLnsg7Y+&RB
{`;uNTI2g1#Ji)dUiG7B9&Hs|XUqSv!Nm}u;&r$23t%D|HPX=rMj!?2*aNkXSdbeK)c!_-&YGPEgExs$
KJMi+xn)LbijNQVT<sWysGqLBw_tcMA9ZN9!EUF@SaD~gt>jH^k#y5W1(@X*>F3~o6kx455%EM)j7RBi
`+ib`Og3TzD)ZGupi}&*TSGXD!rJpZ&~X~mi>%>;CvQu`i^J$OBOMG3NQC9M@|+L?RrT^uPqb|P>#7kK
WBe`aVu~NKE3OXaF-Ls?zw%vegCWgKFLSPtroi|D1hk+>9{qebc+YTDvUjWyqg4QGHu!7rA8q~$Ze3;0
&&N~IqxuEK#+Knn3PnyGY_dtcWTi;7hvJi~7y<9%82=JjMh@c-Y-&pjsW96SU?HL~JJS`X`XMtW{>sIV
qR2@kw~><2VB}7=6{q>q6sqsOIk>2Z3zfMwgKtu~l6|^S!@1;Y3M5?}04_!OkEtv~WaHAjYAcidOLp6n
1}KU67xmP=y<lYiyWVWmJie?`QsX-w7Df3W0~WnC)0A&SupJ61jEb62pOsYv=b^lUcm$oi2}hlOu`_)%
oXL+ESGGx!sT1<h&?|<%bC>5-l0csDZb$;$dzT8DpifCD-$2nI#`M#?k8Q5~0hL^eiA^k}h3|91tn7r)
JBTRls!?$ie=02}GUR=2?Cdvc=KzE>dIkzzT{&}ea)ec*;8Ky=vnb>UDuIqimTdVIh8qH%8Y;SE=Jq#=
Q>v*M*X$9*j@6vh21H7!QU#gjsO5faYF*edd?pf3Y+r&1a4c%|#hIWI11DqLJLWzSpA*z0Wy#PK>By3o
FKvh{!g#S;hb2%~_!9eY0kOIKN{G!~PHY&l$+N%eifu%2t%T2r@61iY=AC9j8e@Zm+Hg%2>e2^BI2|)S
+^IE`GZ;??Ls38qNdHqBQksU{nfCQHBY>aq0ysm=6O4ED-KRU|B(nlo--+!NhXo9Uc7=LRaFy+1i!|lg
Hr4>H3N)l`?pgx_ID&BTMfM2n%snd<=}0^aT3a-7xu{aflQ5OE(10XWWH8I)gdkJgJzlP+BaJpak&SK~
L|T)R9ruwelr>@cwXSMB-4qQhB+j%dv+*TR-kn*n&8^|)(y#CPphw~r3X5>b!PeWib@XUi-X5;DjG5oZ
4f|wCFyhr1TE(eJSvJhz^~q9B<f}HxDeinY4+>3j<8Unb(Ay@|KWSzB0ZxJq-0>(<li@{6O{pFo5UdUt
@c6HoWI^FD)2HvyzyMiCR_{aHguv#Z^E8tbrtB#uoCK=8G>gY!$7Ze`9(^GCRky_8e2@8Pbem*!*WUm&
NR>6_44u>Re@@2wi9iZLl34_SaAum+N$%x9{Q}|-a~?vce{5Pr#Gk&(DL%7<<ctx^$n6HBXEyVl&z-S%
nK{_$vOZcK$&0Q#q8+##uQs3t63GnEjAew|H$r=^9W;*-rD|-P*_xoh!G?ig>S5DN#Hpg>i1{KN5(1>z
iIq-9^pn(%y0ohZgWV9*@BL(cqgMQ!g~7$(3EcpD^yc~4&ckI{hI2O|E+QnD2X#CtQ?%M06v-GOMp>kH
JuZ^p1;W8wg3vOc2EeyJC|)I8_6}T_Lv&=qVX-&~Ih7#F)x>A7XFML_VaB%*3xbk(Rzad@WDqv5ixz{3
H$Hx%!8HJU%`PnN<AnYv@nr;$oFu3D(>)%`vXtiwKU8G*ZfkNy)ql$TlvRC(CkOb<kzDeVkl>!G0zC~i
9<Coyc2_a+OFU9ef$AtMr=fWR4m90K9IUCR5e=3#I=nx?6M_!aLY$gKx%pGy@N0!et3VuLy5%UHD*7*!
YT{)jtR1E~n}buLXb8GkAh?x2v+3|-2z83VSQ&L{IvapsJ}d=dXSs}POKCRd1Csk#pG^)>t(fq%JWzsU
ft@01z|DXetkNGUJ&8H^*k{S%tnnPdjvSH$uO;M*IdCC%s~Fr=7?UAhGF?IY;MhWvLq;b__DkZ1^aM$h
<T(Ys@Xc1ha7rrLG}i~5Ja8!<&o$Qr&q$xAaJ<zG!+5<`f_FleYB_s=R%6k6&~+sIa&hlBca5Kq>8SyD
y3`VQWfFJCGfB&jMXM_NvbPLWSsl{-Age9unW^iAg4rE~FTcvCZ3e><#_*c46xFDp(0G|fTG_!%B@^ZH
@&i%;ZMXu@;|DFg^H6CvqkxQx(^y0rvn;4X!g}0KE@!&W*zN+}3C&&UF#s;*Z6o##NjdR^`vzG#a^{(^
l9Tx3a+`+$C+Qlpph%=y?s#Z~nh$;9Ac8nCq7K|(w79vd)Gk@=FjB}m>w#k=XanYYj_QLavIH*{UlumS
`X;5|(!0)K7i2^W0y9*%2Q6S9Ev`mEpPo*2!QC*~P#6$7+T6A%ZgaBnk+Qi^G?2idr<S5Qp%B26hi8~a
V8BZBO2K#{JOXE-o2Dprc^EGpFZDuV1K7OE0b)wYvPH1r8Kd(Iz?WK4g=FfF0@Irin7($+6MkgDBR&Sn
jB^e2)@u%Ut72t%gm}EHLZHJ8BG^5ZHSG9ZF7lwW49RY1?c<v`fB8v5U7eI=9gnxgy7J0;>BwN)RIvrg
8Z=`c)1;o!(dB;~?xYNmx%lqeM`VWTmCr+A%s8=?I^qc%)9Z!nwdisb#e5NEim^PGTt|2k;eqy?TWD6*
qV@mgATBiLqok^9>Pa@$V|iS^S~5Fh$aE`aQ=8mL%%jUNR~;6{uQaX6&lDPTi0ReC82Cl6v3Qa$E5v((
Ra$aKG(}Du8ud^<+{&1$P3yT(BWBJ#Q)~xJ994V(pP!^QgN;2Ki(z#SIou6KnaWvoflQWQq>N6M^jV4c
kC&GA#aaA3D^_<>S@?QHkhF-S$$lbFA&)@dwqrL_MnquhA>8?Ocqc6_!B$!;L-3%QAfArw6VlpF_!uZ}
JZX7rNDXt^6fJ~xkh^M%y!3^3Vf|i99G_L5kFvW{v^E*d%H`OB``HW2IKlR(G9)TsL!RoU^s{@#{CIq<
`6NO7DIp>Rq-fCZvAdTZs5|)OXuU2r-!ON^Nn&!j5nt@h5!SyWx>BrC#glfX&{GJzgB2FFX*C^AS(8@7
Bl7WPrCiZzY?=$dFgchZFT}`@ig+Q-+1-pO#zVDzk97{17M&rl1dO7WMgM5vI#HSTq;x$|kx5iH%$m!E
WP0h?SQBSN*uWN=lxIf6$hKyK$jX@}%7ACbPpWqb7p`EB`)rI?S52^$Lx-nCiQwH9=Tjw$Vbc*FkD<ch
4baBW(dF?S!;id9SSy!(oUTD?;)If{$kdFSC$$lFmPnGH4C9hnu7H29SH#M@1uT@EO-S>`+~b<56f@{D
Kv1^|CRSGFJ5Nkks?2W73{~H2_W4J3n$_b1@?_&n-7*!rdgQiK?ZO<kf6XLYo8?eY&n@}A4z$dK5NNT^
0~L?}|5fWY_Ik{ho_p_B`5KPurK&g}6;7O#iw6xP^|P@aF#CtHYApJX6SkfUaeF0#Kv1_7YEJ_fvkP|-
F<w@M+f-nkD!)OwAH+taAXhFE*eSonpe?J+`PM0o$)xF~Z)uNs;K`3x%J2@V5ed;d4z+P65$}27vhWJ^
C{NUpysS|hSxI{?t7(CVVEayrHF7C#>hg;0KMqWsq!KqPxMfP2)#ld^i{xCdYI2w0;}3zc5vimR4GMO$
#0>`k8P?D&U}RE@neo!b3bq%j3dI@i7NlA)NvZFYehYR<!2|aE-qC9?6)%BuP5L=(Gn%}7kYZh}yrQ5-
x?+zmlharPB4S1fudSmiI@kw>!V_7!jB}_ndH14QLQEl&q%Zb2gmlor-K#~3n!Ft!EVLC9jyBzuUpq{m
7q)T0hKqbCqrXq7GER#0MI>jSR@GNgGgiy=fFPO+zk)M&r@0abG`Ah#b+RSPm5O0})1)R%0YSj@WB-IC
o-5qI0hlNCT}Ap>{;L3x-6~;r{h5n8`-j<7U>raqZMPjFT3tze6*>$~rEgX<9Pg{aV!<@&f>I2qgDu^*
0d5lKd{GrxB|hY055YnZ5i_s^NFjk&AS(1ZUQdqqY(_e~s?3l?t{~0%MNAk}%%dPxK^mAg)7F3$tW#OM
Mxe<0U19pqoPD1N7B4Ff%?!Exf_F%Gk#g^glMW%8W}>u#2-+~W@mubxZVSAT;#=}i*lH>^MZ_e8kg|F<
o=9dukX_e6giu!9WaV%^xGGguMMjqPlZHfij?1HD5Kn!V_d>~8ffEu(LQG~zi;3j5^b)hkbkmB33$7qd
ruK=Fz%1$khGZp~#!*~AO%zmW)Ou|7OR}<Bykv|=$l6sTryRMUi?CClB&+v3Pz!p1`psXaI65a-7>4!a
1UVk~jYFeSVVTOz<bpCxoX@NB<fu@$7*B-MK*&QSW)8_>o+Q-dbPzqo-2$TBnxdN#U1?EobXO!64Qy->
e)OsLA^C}dcuI4AYNc|&;P;M7u@H#dFN4~3$Ft%a3KIZ0rMB@>o_~)MoqNnXQx@4c%d4Y6<uuZg@B+dG
x48gXSq4wBST}N>*-2EC0hXDf#798}t!rD$C^BUm31uS1uqyGT1Z7fq@QS5F%Et@@nQF29LRRRS`4Tm{
+zn7V2$a;=b@-SDbT;CQi9QFf#BvarhEXG5s8J-c-HGg&AJAlFh<K1WxutSWaIK36D%qlnnOPOLwjP7M
UnFPp1bx5fT(Sp7L@XRY2fmkKFl25xw-AYE_&-pxb-;j@aR8Yhp#!7%SKS=2Ppftn$a)zz{^T3T0LwAc
hg>p!8Xt*y$tpeHya=4ii1US5nZ_~`auW=QUe60fv%wi>x=w!Ss3|=steu@vv%_?KNxIM+xgH|S%m6n*
vSX#M=9qcFD6;CfaSbY0TdtQHDSY0zxqU=}DLBqk?j<_6$dzlb9R|EkYD3!@>w=|FL|NujF#Nq?NyP7_
cHPY1;YAJN=7N_^2KLrep5@$EU=jr<RhT5~Kn;XQIdcwcY1fhK2@V^<Kz;5@LDkuh);n^eR|ym2%2byj
35P=ag<k+<hA5ic9IOOl8yRm*<wojaD{AP#!;#9<NM-^HQu$A@7HiHzyL{1pnR98g@W?RMk~HFpLzB%5
D)A2eyQ%(V-3uVD=m!I|m5WRBx;0J6kd6x`;-Oypa#CK|Be|}zmV2Q-3K-dw4|QaVvEmvs+B6}@VJIa<
7E{zKU|gTSdjK6h@C-T#Ze2de#5$X%<Q1Ri>2t0;_DE$W!^OmL4Pbp!7=M^mu<><|n5YyJj>xN4%b@(Q
rj2lCg+@8mmYahBF}MxPn^A;Hp@gj&znTTivaQo7D(mcgyWGZZYsm|H3QcKgnAsv(&eW<9u4&db6lIVe
NZqfdw@S7i)QpQEuB$XqwCM#@C>dKRfHMjIm~PQ7Oe=sHni{<|3LO??OY`*0F1Da?Dchw`@C213J5^<~
JWJ7F(Wz^d?c`y`M}>bQ`pKL<Iq`kjG;rxQX;X76AQ_Oc(u~|XbrmKmz0mrV^_pj%Je3K9a30cFHYe%=
(IoE9_?Si<Dz+5*$kVXPC6h^AwqX_yGaG2cn%y(NQuk4_r#9K<!nII%CC2*;3qb2$RjH~dmZRy#dc3dK
7g<s<mKO1*>}FmSY2!JlJjLyBJ+HIXd-P3nrT#diDC^GGVNpTwpUS{6i<mLksH8U9;*pGSc39ez`PlAG
{uF)`O*t%KW^>?!hzyX#&-jjVS{dv%O*;szHdzXj=A0vabE<1IJcQsjLL-Q#LCs;j0M1|Azur+Dm7NmC
F?{HpXu#x+D7sXlxm4<AD~DfAqEiz=6l3$1Q*6grCPcBcjoo%c63Fi3IFE)ZV6!A5TU_Buv;4B@!Zy(d
>5Q(-@EN6wMD4H<zK36}iE0t@&h%Jez+a&ry{QAq2Wm4QN-ka0W2p|wz6#w$m@4SJab57JFtm(yFY`)9
&&=F7+||s^6T7<aA{qvB%j2UJXz^gAdigaT#JQ7u+7!t+wtx~Fx8SN!IAt|Dr;y(A6&qW*w#O0=q7tlM
^(KQc8MM;x91X*-+Qf#whxs^LX=6`v%<`j<^NGgs*ycN3_X$T|60oY|^lj$BS0_|@IvtQj!Rumu-j*V2
r|6eeybR=x7&RUyD^UsZ3)9qMHyRb&7)Gmr*UP;vls8AKe)Ywu2w-JlgQT)HC;jy^%Od1JF+Z*^D@10X
c8|fd7~JM8aneu+$rEw&x2A!Gg5U>wCsUz>hIdE7ham<WA0tBVJfWmY9im0nJRjUvnG&eg#I&($#iJyK
l8ff<=4F49@OXh&gK1vlkZv`N3_?9}-Ih%#wOTNL8FHfxUC2rFA%l}~-qDq28SPTBi}sTiUX%%og$hw8
(&zH+a&VmKp=bJK9DE|~WHTl(MzxEN8a6fxN0jo1C{fF+*6C0*O8|E%WyL8^->7F+P3hu_@D$g){Lmi|
(LHA)h;9zWGVT@7FEDSrkdypa0kv_c@rk>Kq;j$Gi2D?W9LIM!j;lVF3H<2{Zak-eT>Nl%WX{TMet*E!
MJ2E1+vix>`hI!vqoV#gz&H^#dx+Y#6ipSiF@`Eo6Ym`Y4Fsc787df%m^A$kIV?^zQA+aD$h!=h5=qa~
fhW66i6srt3yJtK&vODG3dr>eXF%qpk5`wo3OqI7EjSG-F}<WN5`7vTAU6}cl)TxR+@LE$T19Goia-n;
`^XH<8*EaY?DR6<ytn0_8M(MH1d2C~6QGo$RHcfU527;Z5EH6WnRKjJDIN4_5*<B4TQQkh31&B)Yo-A<
pAkt(P%PL$y=u2QZmnWHy>$JQ_c#PfZuCb`C~D2vTqK{(>bgg4;!o5~T8nB5UkwC4qw5?o5|igtxfx2F
GjN%u^b)v8-T;o2rXNx8rq09)47Bc`vIXlAml)lv*fH#$TjU>td6mdYOl+O>yvkMTkr16VJ#}w~VW}?z
R87q56JeEu$%G858F<#0Q9>t*Fs2^g$_1TFhN-By!Z%6EofmYRRQ;?`8pxf4-ByQFr=lf@;cONk66)|=
Id~>_DdV8kc=-TP0Y{`=aAQurqd3AHlU|FM66M9Ia;l^ERwctua?UNG;R517bnqxKjB&->lt}Glx`+-G
*U3qghAV9IIVKkprnD2k^dVD-F^LJ|RRU=!X*7M4^M&gG?emxaToINti)a|0<KquKJ{+)zqYG=Mnq{WN
6cmE>m;npX7yy}l1=*QFmEes((CDGDaWXVH^-k%~uDj`f5jh|uure01y-EAONo9Tom=ZA*(*L->2n6J%
c)9pUghgVDv3n%LD;sYK9Rb-~p;rWQcRc=i_(E)!WjhkaPq(+6`g0vovr9E3r*9(z8BF$bde!KRoacK7
^`dvF)yVVWi9xTQg26P>DQdo-sQ=t3sUPP;(>s4MzG5$f|2Jnug^$+uO{KrV(wX$x!lB?Fowm)vtbF)?
qr-T=
""".replace("\n",""))))
while len(_S0)<720: _S0.append({"market":[],"farmer":["PASS"],"hands":[]})
while len(_S1)<720: _S1.append({"market":[],"farmer":["PASS"],"hands":[]})
_S0=_S0[:720]; _S1=_S1[:720]
_MEM={"repair":{},"ctr":{}}

def _get(d,k,default=None):
    return d.get(k,default) if isinstance(d,dict) else default
def _seat(obs):
    return int(_get(obs,"player",0) or 0)
def _farm(obs,seat):
    farms=_get(obs,"farms",[]) or []
    return farms[seat] if seat < len(farms) else {}
def _align_hands(action,obs):
    farm=_farm(obs,_seat(obs))
    n=len(_get(farm,"hands",[]) or [])
    hands=list(_get(action,"hands",[]) or [])
    if len(hands)<n: hands+=[["PASS"] for _ in range(n-len(hands))]
    elif len(hands)>n: hands=hands[:n]
    action["hands"]=hands
    if not action.get("farmer"): action["farmer"]=["PASS"]
    action["market"]=list(action.get("market") or [])[:10]
    return action
def _tile_at(farm,pos):
    try:
        x,y=int(pos[0]),int(pos[1]); return farm["tiles"][y][x]
    except Exception:
        return None
def _weed_repair(obs,action,step):
    seat=_seat(obs)
    game=_MEM["repair"].setdefault(seat,{"active":{},"last":-1})
    if step==0 or step<game["last"]:
        game={"active":{},"last":step}; _MEM["repair"][seat]=game
    game["last"]=step
    farm=_farm(obs,seat)
    positions=[_get(farm,"farmer")]+list(_get(farm,"hands",[]) or [])
    unit_actions=[action.get("farmer",["PASS"])]+list(action.get("hands") or [])
    active=game["active"]
    for actor,txn in list(active.items()):
        idx=0 if actor=="farmer" else int(actor)+1
        if idx>=len(unit_actions):
            active.pop(actor,None); continue
        age=step-txn["start"]
        if age==1: unit_actions[idx]=list(txn["intended"])
        elif age>=2: active.pop(actor,None)
    for idx,pos in enumerate(positions):
        if idx>=len(unit_actions): break
        act=unit_actions[idx]
        if not act or act[0] not in ("PLANT","BUILD_PASTURE","BUILD_COOP"): continue
        tile=_tile_at(farm,pos)
        if isinstance(tile,dict) and tile.get("kind")=="WEED":
            actor="farmer" if idx==0 else str(idx-1)
            active[actor]={"start":step,"intended":list(act)}
            unit_actions[idx]=["DIG"]
    action["farmer"]=unit_actions[0] if unit_actions else ["PASS"]
    action["hands"]=unit_actions[1:]
    return action
def _step_of(obs):
    if _get(obs,"step",None) is not None:
        try: return int(obs["step"])
        except Exception: pass
    day=_get(obs,"day",None); hour=_get(obs,"hour",None)
    if day is not None and hour is not None:
        try: return int(day)*24+int(hour)
        except Exception: pass
    seat=_seat(obs); s=int(_MEM["ctr"].get(seat,0) or 0); _MEM["ctr"][seat]=s+1; return s
def agent(obs, configuration=None):
    try:
        seat=_seat(obs)
        step=min(max(0,_step_of(obs)),719)
        tape=_S0 if seat==0 else _S1
        action=copy.deepcopy(tape[step])
        action=_weed_repair(obs,action,step)
        return _align_hands(action,obs)
    except Exception:
        farm=_farm(obs,_seat(obs))
        return {"farmer":["PASS"],"hands":[["PASS"] for _ in (_get(farm,"hands",[]) or [])],"market":[]}
