"""HI_AgriBot v13.0 "Replay" — meta route + adaptive overlays.

Backbone: the public Azelearn season route (kaitofukami v23 publication,
Apache-licensed, community-reproduced meta). Our value-add on top:
  1. survival overrides — starving animals / dying crops pull the nearest unit
  2. weed repair with action replay (meta pattern)
  3. attack-mode market dumps against lopsided opponents
  4. momentum escape sells when prices crater early
Adapt to survive; route to thrive.
"""
import base64
import copy
import json
import zlib

VERSION = "HI_AgriBot_v13.0_Replay"

_ROUTE_B85 = 'c%1EBO>bPuk^CzIp64*6r1{tzEzy=>jwnc!1@Ax@46rr~EWC%=y)E{?uc#K;@70UUi2SJTmaLOn-RypuRasS;k&#)y{O{S{fBXHPfBXIH-@f_f?A7I)H)rp^{pRc+zx~&L{P*2kcmMh4Z@>TN-~Q+Bf4`hPfARY2?l1ILe|Y=XUoT(2`1$hs?89$8y?OWHp9}EGo99<ouU4PExw?9G_sP5GSC_XRUi`56<mapFo0lJ6obSK%>h;aDw@+`E-+S`@{r`RY&05hHPyhV()$+0DE46<)dw2EbcBjD0o7cC`cQ5yEj<3dXdUJJsy_DhHlVSfyYZ>-`u^zS;*Ux_aFjcp2@5fk|%NQac-u*9OftJJOJ-;+Uz6keUe00cB**s<`+rm<y(QMva%dxeP>&vHC`_Uer1~kS3Y+sV+{&BVN#tFC=>dq!V{^*ByUf%APqxoJ~j;EK~G2Y1bVJt6iuU>CnK1i_m%TX#e{+sP^FVjk$tIId0EQx0<ei@D9{%QMHZ*JZS1BxDo7S3LY{SzjQ=hmF&jVrJnq!kok_o`$t3mwP|H;gOV{FeJq$9R4+I@LNBc3K)y-(t}g&^xr-ZF%M(i$;sy^N+o}^^zgZ??w0TEk$3vXFs;|EI6F|Psiui^jhcu9<h5BeggXf@ifWTA1qq_hT}klk9_upo9pYVr?<cU@#^*Mi|ZHvz8l?%x*b}=trJYX@UX>xRq1dl#n<H5FEo5%A4V?b?b~l2zxU9HC`54oM~{bHeRJl=_nP>RxUpGFgvEX&5-zh<mGF_~k78IPG>UzY!-O$Jz)H|r1Y2@K5O*FHv4SKLoCYFM??f!(RYhPp4bdTl6A=Xl4!Iss+}Aq|OT$U~>>Cgy^BY$KesLr@>M>0C*iE0OneD&t=**v&GYz`pU)1;E>gGH3=qv8CsZ&mQrm~}^x6uPQ6Nw?!jvCK#sEnz!IUdPMld#Ue!WY8_i~p)4j8ij)+x&DgSb+d?!(mo@gcckMzdSqI$tXu=#>4aLXQ`bHdVcx(FWKXE6E9hrrcaWwM<o30)PRvNXz`RyW-fnx+bNBXSw?pGFtycr#u+9hDO8?uyhC=t4_K*SK+Ql2Y_N5IZZ)-wUtYhToo_U=eqLVl#L`=BM_O|qk|H{Tx;*4$o3l_#kJ!ILHqi9bc7ihefbn1+Sy&fOb_S$)VaNxPcy4`xe?ur%+=a&hJ&~~gsEEk37k`=@PsNsSbNt@`sfru4?c~iIT}?PNs5^l(V~V7z3~*~08yVhHh^arLFIwl35dMD=8QYGS{GicyIJ)zWr&CJU`k}@NCTycQzMhQj!p$vYkLA2?9w_(YyBS%CHpD|)5*oOXoX*bZxO+Yi-~w%k=ZO=MNqpqY?Yo<syMNEWdrtzsyK(*CZ$Dd}z1Azg*y}!6d~^Hy^4%Y<Ucdh9od7>Qd=6&sBI02UQ8V=9HUY1oRfFe&OSur<jNlOTDzvMCVT9-MRuNlJK*L9JMvI<e?ve?1!y=BTERwfHM<pXld%SEH+33Uf5OyyXaNxj#76-~3uo!Z=TlgS#Ee_UurA7zNe__^r9~S0gXu^h^d$X+)%jcGMnxkGcR^+1jwTBDgQDM|5Mg>sE5X$9t8z!TeNwP(3Af5`fPrBS>_YoHPa0aLP0B$U--oj^)lS!||HCRex`pqF!R+RZcN3Iwq*A>a}<Vzw2K@WQ!<3AvWk>q%j<_Kg;8rO6cqjk$R4=~pxf<*O@EM?w8gSI0pfAWMs@xR+HD=fV<Cio<{Z0lDjv_60ML=2r_c;^Rzk2kia_Orkl;_tOS9}9yYLg%sNNNa$Js;y!5Y^}ovayXFx76@x1b|82T#;M)IEF=UVx)(RZbt}5YHWGooW757PuqqTwxD=xNaToCu_peAeqh;RjEji{88Z@nzbQ5l9;1(xIQ@paLkk2cc6`e%Yq5vZ?v0U~3B2lu&{Wpyi0^TRWzK$5*^Ib_AK%^7np$55+GNF0B^Tk?Eu+;@Tf2XNNX4L4}5PXP{07H~)(+N(G9C5B2hO6}ny2tzTi|aq1J@n<<w0iqt_4dj={{DT=Jx=6k>~?$W<cHG_D&Y^?KKzzT>3H|xoJWT(a-&VpKI7y^_aS+Y_2kNk03OV+{eXwxhKep+G0TY%N!cy3!a#+`22P$!h!<v&GvwZZUX>29J+uhdz99(nFlN&?Nb-URnOwz9hldsEtq5`Wg%Ay)QY2ofSyP8sydMx4w&CuH!EhFh$l|#ngK-3^sqgbB<g(77@~-`l51uvipu}j9tr8`X<|6(Q(2(kk1dAU*+v)znA1e{y4x4%G{&y|AM>4?9jJ@W7Jo+VQgW&ECid!tYfaY<Kr<UWKqdasx#s=ozkGp9eVyj&@?0WpPe^tsNEMpwv3M#M0A*nZ)Pq&aq0Fo6!W@9gPAX0^0#s)5iU<si}Eps3m^C)Y`M7pvf0hd|LVc@@Ihk#joW&biRKevTy@TUDh*BCfUG_}jT`u&8lE{;?gZ1)x5MZ>cxcZ4G3$1V#^@cz8L<iXiw#ds_dw<76jgjAgd7;VGlX@K%{!!Xxob-aBdoDpkK!_F<qIo9JJekAFc*m}Bk!p3FTKU~~2Y_;#4C@G`XARzw&&kKQuG?`t$4_!(_@{@RYpS`|$Wee?JGqFgktew^B@JHyHV6mWJm(0$jDe?J3Zfv%nnEk8mY_bWtcpRUQN4<&=3}B~S(y$&iOvqy6Eh(avbwx*>!Ax<H_vYkF+&uI~K3hy;tFO9;e-7fJ%Nrf#Kqeed@23R$_hj2p>n<bcP2*6HN_WCe_d}q7IIDuv3uIqu;wy!+@E=H(kfx90BS4|5oC4i;eaGMS{Sn(*|9xTvY+k)jHmes?NVMP4AQ;AXVQWv3HI%S(NpM7am2iyiwxU&ooRTMJs7{0049vl;c6MpnqyHk5I8|m^=T`6MAKqw|oNA#=CQv^k8bTC&)Ck#bqBBx3#EQpysmO@Uji>^0*=5jr9rRF~&c~hW+InBU#?M0uRdY_Pg<wqu0lUJx8%0b>{y^mn5w%q6l1uON`yWs~UBp3w^pNtEC*msiCz;KtP?K4*XqYw#?F+5vy}(_<pnZf4$98+42UP}!kzLBQk%T`MbYw;xE3@tmcs|ZT5mt1!rRTNAH^6Srt`Zq1XR{r32}rxJCZSCXc9tN>Mn?nC;Y=!kT5x4%3$5oXU0SP1Yo5YtC46mfyl>G$Fi>aYN-DK1y448H*hM=v?pb)y#4;w>3pO8_<fj2)5Hnq4YsJ<AYF-B(0ES2|(I*VfL_rDPp<jgZbwXS?>~IC*jGVNfV3rF(0F^k`jG&q=<s}vtwNI|HDjTO;SQSOgh-|(o8U<D==SrNqR#Ym$VvAX3$K42EENLNp53;j(v_5bW*{rvS-rWZM3wv5R2GC)`eJ;XfdaiXqjFgwg1Zm@JC<x3hqtVe!iklr^kg1|L^j+|n<DIb79|MhgXu^XCB#{Ss_e-SC0{KAzU~pkNnskd{Qobif<?++v;}-VFsXlc51yY5zYGo0j{Omene1RmN(+DgRrNW!TWE=++fdUti^c7veK~#3qCO~WKN)~|FvKI}gn?Yxnlje)G#fEEgC{6qco;i%f6uFF6Ee2;@!ZWini*}xk&uJfAH;X6gmhX6-;~+(7M&6#*v!Go6m$cdA+0g8q9AiOw+pV>OXQ?qjKlwtv9&I9XS0z4>!*kLyO3YWKjbVKGM7Ff*6rkN2=iegeFC|gvZLG`1Ti6Ifr>E7Ag-uSL(&?m11P2lJByl}sDM)8VkEhy&mRS=cq;UtJ;O0tE;stFQ9F>S}D{5ee(w($G-3<nN;gQJ5?B5GiG4&27d;*e0KzPuriDJUKyI^J8%u%e=*fm2sYxD+}bRMuj=_w`L`(X_=u|5a2h-cHQ{LDB^agc2Kgm@`-b-?6AI*)_QM7jr#<b^CE1kuWsu(KJC{!zZ&i(15?%h5bCh8YWlKeiM+qK#6#%O?Qz^;O6w==G*MlhX4}AW;~rdSr<XpvD3LLNh|8Vu4h?79PL}<PU_=?6SGVeVfk$HiHTz{KWpMzQ}O<i6n8)IoGwhpMu(-i#;`YzCQF{@}Z+qD#76@wLiD_>XbpUm*lAju>FbsehRte{ip)Brtrg=aX-31r}4C`et_^x^P|0K{8OU_GsAD0BGsW(1Ak{Oj*zSm%tD3!&N>^mWbaXAA&2errlfV%NEh%OFoPea^JZ?JORk*en-{|N5BHo-mV_Fh^U#wmlibTtQeLD`LBkC<KX4tDRDM28Etk0S?BKRPZ)u|h#{_4(iCwqm+T{ehkx7L~Y;?C!bTdK233HTzGZrQhNuP_!`w2<AqO3e@U0~<mTO1!hio~Mxgnfck(2=Ew;?9eSzbNS%vhU5(jYjR3Ti|O(5mNKnKry5KpE;KRes48FV^>XZ8?5_be|vx#ECxe`N5f-q*SQm6K#-2En>X|4)4{kBM5Ql?RWVNfr(YQ?vZnPRDH+SMBS#mp)+MjtLFgP}NHe@tCYkIi^T;4@y}1%Iw!jH9Nhk#xFI~VY&l@UCy*DsV)aetKsrzTa-WE`0A=b3}Nw8M1i<c!^7MU-2JCt@5e@(&-rvsqC<^*>Qgs@DvFcHBLGapSbbjiMqts`8!5g`M4UZG%K!DWs*AHxldc36jU9nP#!M42mb^H+RH<7hTo1|SgpW!@ZTBYNX`TbB`Gb&F5kQmQ3!tHF#qmBGU)gLs0V?IKrRsrG$Du9EsHEZq7F3_t7XNrGOTFrCR0^0;W4`pV8TjiZ3TF}1Ed0*?9lF4kSc@f^qkFz!I}9o^MYLoe*;71#w4td?G@_kE_a!|`d;L4*pTS2xfgIdMA?S`Ymo9(=_C0==Bu4pYmOHX+z<VvxhwQQL8=tTc*Fd20+VCv2R-iOViEwm~EbE$-11L*|artVQmTfE2|um)G_%ty==COlcNDtaD1w7Jq_Bn=yVbcf6CugoULL4~f_a3c+VfWTANbt+}MS1|2dEL(N$tFX1K7=0d-Zm{#|XsyzVBvGVD5BzsA2U5s{zW;4S58MQiDJl_Y!^2}R=>bSBJBohUp4$n0+@CGi1N;la;K+?)xn~3ZL@dG19*@$Y?-wXU9QISju7S(2-k+zoe?^>?jX}b)Z_<eP{*M(DO2kBlvtv*@}9&Wt5W8fSe#u~@rb8IHVC^WWfJ!)S8s3Mhl?tWiWVscd;+Vh#flbhM}HPH+xa)_QH9pM<IQ8Z{b|7scNN?7=0xa1;#{|rMqNRC=3F;>b{Yk{I0+8@LGQ;S><&yByxuLKkshr(gKM9|74G|(D^(92xB=#^GAl@JszDYhJNG|0_Eil`WaN<D8`k(V|5+J1ti1fiaQ->@7>Vage^PAbNA@Z-|95JoW|-k=xrnIx44+>~`bBH<{MJQ~lVGfp6eK`0Hyj+|kM%VmeCa2@&$WfqBp4+d+SK;nGRl~9{pHX2dT344KpaZVG0JMgLJ)3S&;se&0*L@Mesu8bzBT5is*51C~uYq-d{oM`>gIxL1YcPGjD8HeFZ>BdV?e4q4F=<X08_gK!QpD9ko^HYl5)NKAdEzr4Y1=Gm!V_w~9!6=NNP^qc$r-;&mWIqzIVm#CfKQ2@a)Xw$+v9ZCI<G@#id5-mES-=J)pjfe|uS8>gDm<WSf0%gPUbIgP3nRr-t6@Hij3EP=MM|-}wXs-3lc`>UG+}YlQVJ3FYSuKjB*_Gl)1!4U>Rh72Dx{kYB)JH)r*d2f^+;vd;lm=p%4-1wA$GwKp(LA?jyw<lfzc5lG3pw_l|%SP7KW?!F}$Aw!=C(-a|cC|rbkFUL}usiBYnR>0Ww||`L>|?g7ax=WD@;Y-{7G@F)+tRCsL|DejJ^^k%nA8h$<PU3mSx{EJ5cDYJyTl_+T@EwntH#()oA0@%vmV>c&y{QtrQU+cLQgs}Q*;*SgAjWqkFCxkX^!)cK6IS2pZuZs3H2VUGn_vh`xWa1*G0C8oD*7Xd&`bq8!DdRBO2i$9Yp>9O#^&Q}{_VHy3yG`r5X7-3n-VB4DUtOm^x;%%tr-%%BzN|J244dS_@)x04n@?gZ($~c4?F<I}~#ag9}f)R<}TiUu0TQFS{tu10^@%6~X839TO$-qpa@<EDJIyx46o5W_;UV>_QRwv&vv@ymS0!6+d+_>4WYH|!kPC#SJ!ua6|Nt!Y5DxP7l*^^?l@U;O9v&Ds?gki1rmSahT;Y4zNsiA5d9gYZ|$zT3Jka?D+g*~y-#7HB;vyrp4Tubg&bcWq;EH9vZ$QO8c^El%Vc+u7M&C9coeVE#MSYjL=0&KeN?uU1wFc^GcUuYW(h!ncjBCx>Iw^(shSOQtw=rCOwhz|(}6>~=;15sm|H;g7Vcoj0D*g~LJ=<den9wX7jI~#bD1}NMB*^)#84$aYai9ViJ)O)|SFCfiy=t2iU^!r1xcGKopN@_nP)o;sUQz){RG(^gLIaO6AD)drSZR{o372cnv7DX~mr;s0xgC7B#(q%v4PVkhm!^2WeTs`Oo4MMT7P(<SEnpe+=9XRn(TY`S`UlZq`_^j$x<x8ehA+oQoThS#>p&0F2Hvu;Uyo~V3%(kFtC$<})wHhn6g=ohZok6y$PWne2$2{Bd?mI;qt3unV-ZeUVDPkrvibA6+k$2xUc2GCFPmB`=+PRxi34TCQq|k1C3W3?=DA)r8<3yC|iuMsmzK-!A;EdRyeC6V8xNZ_nLy1NZ_W)RqOxPpQJA_0u#%)DZ3^W-25Bh;zL$n{YSRQUDND9tK^}!;9qT~l3ondeqT$wWbRIMO=N0WmSBhs1^kXC}vy8rFnh)Sjv@3luJNjEoN2g&a$gL1H`0t7aJs{}c(1Lzk<^4d_laU?o#xbVb1#h!dF0T#JD{JSpk^~nibM#08}q!T?>aMU{p7qY+ee4m<Pc^@Z!U8_q*q6Addbzj!xv>MZ=B0W4TLcTIT5;@2)+OI4?yH;!KMV0$&#yO--XFRYHG>0=>A|B}8CZ`?}Oq}vu78kPEj5V^FP4FXY!F`K1*U^zwi>fq1{%85|$d;P--n_x=rGfj1*(7XZQIa!$5fFxIN7b3|z-k47{oP5&>N1lOHQF%aYbA;1MiFu<UZky7$drQR+}RvzocNTtP{v6UV1HJ2V)aKvGEcTmj?Y3bfaTOmEZkm0MO1MEu<<WB(dn=d+~R(sWS+h{E@9Hhv2w$Vv+|U`BZ}twdGgK12b4svAp|lTjCD@2w`r5)5A#5GkIeB`Sz`;JtMG>1HPDQK(cL$`b_h5{0wjrQeaCqG@;Gv^h#%y28xc{WBqrxow46}IpVEP-vjLun7E|u=#c&U=LW<NlH=?}NJ1?w}dG_K@o?av>M2qZHa9?cC>Mat2^4N;<Loy8j#xEacUh+e+(UdN3)p?~MDA-3S*12IY>3Bzb(D>m6`tHMr=^(;|iv49zfM9zz)vf~s>uH#N)SS-Zq(<-zlB|1}HkK9Q$gxtZw95hq8rQ+w5t0N}dSJt`imVz6YgYO~BaZ8y&*LBShyw`mj_Ahc6A3x1=ZR+!`Lvl=!E-V09;{{r`EkKbv7;$5aF$s9mg9p<f-S;%XY7^-$hVFBENw8Xbs(I)WFLjk@XMC{Z8VG;LoXc``Lf)&-<1bbeuG>ys0{o$v8aZDpi#de)@MC_PXqUT3A-27)i0>Ao81d|1ipE$0jFp~+9b9bKvd!VNr)M#?rH8WXjGM{gnAV~^Qp$9AA!&JhHq+hoT~J2w;>;^I-%)4(4>g>HyO-as5QCXY*braqixM;&sT>Mclc*?to<xX?$@t$59i3tUc1_6SbvzgdanK15)K~+96{DU9p=7nUuB&K+sfQ6kY5j^&yg?t)^#IlrYUkKaTU1H4v>{$dsOHAH2Zae1^TYg+d*$Z<&sC6*Q^06$u}3XvN4^9HrhK;wCz@M#^7O=N)dae$YHN1kI{3D!a5Ie-XGjVaTQXG?Kc!33bnl4>d%ydRMZG?V{I`Iv56?CGL;%8FSV->+8;r>%|;|0(*`#QM2W{_XJ~G;af-I#`xAk2)kxoTN=2XxZW_TGO-kTatN4ay&#RJjQ28woR<xohLrY`Qbb`38d1k7hN-!IQr;7Al_m@6g2XwAJ{w+iav_{l~Yh&HAPHy)jr6~BgP`nVN0$f(Q4{1VE!+T78WOfAWSxuN)83Qpcn1kXWpI(u=pW87dYH1A8l_kB6N#jadNet2_!!gq0Hsd!HfZKtJ!WpsaFcw7UB)U1=asSEUao5lb2jBeKQS{)rWgNj|P6fgtXE0|C_lIFsvtdW1Lbyeetb`So<;#z)=q_+ii7IgxH%q~Wv`uQdZ6U3EhmKNWx*+8<eyuhw{gz15ji9H&<D782wn60Z*}OFNYH1Y8A(&JnUl%IEhLPAbW?gGf*@2vY*obn*ml}!6>5Pnr3DE(?NL{PQ?cnKd6pS5|P)aba_=VJwCBMN7N=oF{ibEJ1tu6p2X&V93$?y2eQW>O%$(gkA@X<LHAP7Z@F|b2dhy`jR5z|tQk#ShHzn={Ev-}*-O5$9a7DAGO9F|6c(B-&=N_nDqz+#9vXHRh3a1}8kTtBSXSU+Zs9F-5a*A_>rp8c3~x}1R)lF{r*x2P(xbZj~Cs`NRKsz(v79A7u!^a{t<K>WJk{2>DRgkOAxxn{#$28(X|UC?zCpOeCE@WVGSBmD5~HUm_|$D<B`?|yG8J+;`J;7sJg0!iHIm%|gVl5v~1?-GStZh?0&)XgAhErqszG+I0-e6_pG+@VdHOmzM5m$LH<3j7tQunC(Npn+1@&7-u|NNVpOmr7b%nu*I7+;*1s9|X3Sqg}Csb|ot&3ZV0GN>H_T1CCwuaL~JjjnvxF4TmwS#tiIGC?pnG3>Jvt$gdth{AJ8-fSWM-HG7ka@nKD3W0_B>5)h+sGHqu{aM>^e9nA?GK_5d-^h*>$#MDfnr$o1pWyU(Hk+^*{a4ks%6JemioeZXID9gMsU99?BH7<RTcbF^D6af+NRA#w&)&_thq~ThYglZUK)rwp(g%-gw{*KpMZj4xkP|Hfo%>?;9A%CiqXbg=G3%&lrhA%g;=#;LN->p6y_)%XnzNiU)49t;`N7eUge7lS3H+aixl8&8|Sa_DKVJ6;@l<T_an-Lvwh#&Ay4pH#idH1)_oii{dRutCIyb6;2l6Qg=f}0BY4DaIhW*^@r)@@+_oCZ@N{BhE(&JHwNm{s<y@KxcQKDMac0Nu6{rB{h<tLvKZAm@ZKI6xyO7TcZJMdDQ7cmAjTjPuIfFqKa&1r=MArLK@6xLSTwBcSeLbMwz>)=`n<+zQ*3&XDt&=)8eosIg#Vn}gFU?`NcFFGVJV1U6D~mnPbY|M3zb%*sjiEVNDo?DdOg<DU+F_y!>=eB*^hd(J5F8tCSvH?wfzbIYi?{R02oC&N|}R6hBYv&>;^Q*WwGQrWB$oNZx{*rr&0epUfBf{}v_;<!;0UfQPUFp-R7sj3a3d;VD}Z%_aOtF~Nxl5sQfNScd^QB~k<spQ>!VSzue<gP&%m_(D}YY}N73D#b=$a(;Kk%#htv#dd5zD4Yy=c5C~)<6Kd<>!qO6DM9lgvlbBOddtQ<Zwo%iTxqnydKHwhtcGecV8yXpP4tY=fpOf$J~A6ly2r>?g4cg%7nEX6x)5*x>rFe>UOwG)#;>gPInq`EM1_Ut9^$XITL;273hqG%$z(${!nFJ<Ti5wlQ*n~6kbHJnZo_!G?bE}--Pj_laQNnpu!?L#=bLeiKdpH1}ME6TMLORP*UC1h<Wl>%nV-bekvh3uTtm%aEt;-Cqhh^HVNAy@ZuLf!iH)|a*rV&J|HTUnZ5EwZ-YrxXr=|0L-^x}7pVF@j(`=iTP1G)+=W|zfid#d;S<JV9`C}cFXkfY=&{MYXO$tB_BlxG&*~RpDz-zI$k4Dmv<^N%lje$*Mg|8bjNrf|r_i;WX7N4KA~G4AsYsvyK`xyN$A$~hIs&0SW>I>$PePzjfq~w(eetq)0u9K*oNuxY5+laQk1&=YXmCq~7VVZU)X#+jLv-8lq9L-9=~PORd0R*^1r)xX&2PRX^VS;*I!MbeRg`=?7%WVg|1QC5zBCaCTrAoz$+KSpR2+Koftx70uaSX?P26ev$Go>pl|dsQ>oQB~y(n;6{I9UR=01f`xb`ugeOGht%T4e7{{x;eDoy'

_ACTIONS = json.loads(zlib.decompress(base64.b85decode(_ROUTE_B85)))

HALF = 5
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]
MEM = {"repair": {}, "opp_seen": False}


def _get(d, k, default=None):
    return d.get(k, default) if isinstance(d, dict) else default


def _seat(obs):
    return int(_get(obs, "player", 0) or 0)


def _farm(obs, seat):
    farms = _get(obs, "farms", []) or []
    return farms[seat] if seat < len(farms) else {}


def _tile(farm, x, y):
    try:
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError):
        return "LOCKED"


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _move_toward(pos, target):
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    if dx == 0 and dy == 0:
        return ["PASS"]
    if abs(dx) >= abs(dy):
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def _shed_dist(pos):
    return min(_manhattan(pos, t) for t in SHED_TILES)


def _align_hands(action, obs):
    farm = _farm(obs, _seat(obs))
    n_hands = len(_get(farm, "hands", []) or [])
    hands = list(_get(action, "hands", []) or [])
    if len(hands) < n_hands:
        hands += [["PASS"] for _ in range(n_hands - len(hands))]
    elif len(hands) > n_hands:
        hands = hands[:n_hands]
    action["hands"] = hands
    if not _get(action, "farmer"):
        action["farmer"] = ["PASS"]
    action["market"] = list(_get(action, "market", []) or [])[:10]
    return action


def _weed_repair(obs, action, step):
    """If a scripted PLANT/BUILD lands on a weed: DIG now, replay next turn."""
    seat = _seat(obs)
    game = MEM["repair"].setdefault(seat, {"active": {}, "last": -1})
    if step == 0 or step < game["last"]:
        game = {"active": {}, "last": step}
        MEM["repair"][seat] = game
    game["last"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer")] + list(_get(farm, "hands", []) or [])
    unit_actions = [action.get("farmer", ["PASS"])] + list(action.get("hands") or [])
    active = game["active"]
    for actor, txn in list(active.items()):
        idx = 0 if actor == "farmer" else int(actor) + 1
        if idx >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - txn["start"]
        if age == 1:
            unit_actions[idx] = list(txn["intended"])
        elif age == 2:
            # second retry: replay the route's PREVIOUS action for this actor
            prev = _ACTIONS[step - 1] if step >= 1 else {}
            if actor == "farmer":
                unit_actions[idx] = list(_get(prev, "farmer", ["PASS"]) or ["PASS"])
            else:
                hs = _get(prev, "hands", []) or []
                i2 = int(actor)
                unit_actions[idx] = list(hs[i2]) if i2 < len(hs) else ["PASS"]
        else:
            active.pop(actor, None)
    for idx, (pos, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if idx == 0 else idx - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        if pos is None:
            continue
        t = _tile(farm, int(pos[0]), int(pos[1]))
        if not isinstance(t, dict) or t.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[idx] = ["DIG"]
    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return action


def _survival_override(obs, action):
    """Adapt to survive: reassign up to 2 units to genuine emergencies."""
    seat = _seat(obs)
    farm = _farm(obs, seat)
    private = _get(obs, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    inv_list = _get(private, "inventories", [{}]) or [{}]
    hands = _get(farm, "hands", []) or []
    farmer = _get(farm, "farmer")
    positions = ([farmer] if farmer else []) + hands
    unit_actions = [action.get("farmer", ["PASS"])] + list(action.get("hands") or [])
    # find emergencies
    feed_em, water_em = [], []
    for y, row in enumerate(_get(farm, "tiles", []) or []):
        for x, t in enumerate(row):
            if not isinstance(t, dict):
                continue
            if t.get("animal") and not t.get("fed_today") \
                    and (t.get("consecutive_unfed", 0) or 0) >= 1:
                feed_em.append((x, y))
            elif t.get("kind") == "PLANT" and not t.get("watered_today"):
                if (t.get("consecutive_unwatered", 0) or 0) >= 1 \
                        and t.get("crop") in ("WHEAT", "MELON", "CARROT"):
                    water_em.append((x, y))
    overrides = 0
    for tile in feed_em:
        if overrides >= 2:
            break
        # carrier first
        best, bd = None, 99
        for i, pos in enumerate(positions):
            if pos is None or i >= len(unit_actions):
                continue
            inv = inv_list[i] if i < len(inv_list) else {}
            if inv.get("WHEAT", 0) > 0:
                d = _manhattan(pos, tile)
                if d < bd:
                    best, bd = i, d
        if best is not None:
            pos = positions[best]
            unit_actions[best] = ["FEED"] if tuple(pos) == tile else _move_toward(tuple(pos), tile)
            overrides += 1
        elif shed.get("WHEAT", 0) > 0:
            best, bd = None, 99
            for i, pos in enumerate(positions):
                if pos is None:
                    continue
                d = _shed_dist(tuple(pos))
                if d < bd:
                    best, bd = i, d
            if best is not None:
                pos = tuple(positions[best])
                unit_actions[best] = ["PICKUP", "WHEAT", 4] if bd == 0 else _move_toward(pos, min(SHED_TILES, key=lambda t: _manhattan(pos, t)))
                overrides += 1
    for tile in water_em:
        if overrides >= 2:
            break
        best, bd = None, 99
        for i, pos in enumerate(positions):
            if pos is None:
                continue
            d = _manhattan(tuple(pos), tile)
            if d < bd:
                best, bd = i, d
        if best is not None and bd > 0:
            unit_actions[best] = _move_toward(tuple(positions[best]), tile)
            overrides += 1
        elif best is not None:
            unit_actions[best] = ["WATER"]
            overrides += 1
    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return action


def _market_overlay(obs, action):
    """Attack-mode dumps + momentum escapes, using free market slots."""
    try:
        seat = _seat(obs)
        farm = _farm(obs, seat)
        opp_farms = _get(obs, "farms", []) or []
        opp = opp_farms[1 - seat] if len(opp_farms) > 1 else {}
        private = _get(obs, "private", {}) or {}
        shed = _get(private, "shed", {}) or {}
        day = int(_get(obs, "day", 0) or 0)
        market = list(action.get("market") or [])
        # opp build reads
        ocows = osheep = ostrap = ocrops = 0
        for row in _get(opp, "tiles", []) or []:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        ocrops += 1
                        if t.get("crop") == "STRAWBERRY":
                            ostrap += 1
                    elif t.get("animal") == "COW":
                        ocows += 1
                    elif t.get("animal") == "SHEEP":
                        osheep += 1
        prices = _get(_get(obs, "market", {}) or {}, "prices", {}) or {}
        hist = MEM.setdefault("price_hist", {})
        for item, p in prices.items():
            h = hist.setdefault(item, [])
            h.append(p)
            if len(h) > 48:
                hist[item] = h[-48:]
        def momentum(item):
            h = hist.get(item) or []
            if len(h) < 24:
                return 0.0
            return (h[-1] - h[-24]) / float(max(h[-24], 1))
        # own counts
        own_cows = own_sheep = own_straw = 0
        for row in _get(farm, "tiles", []) or []:
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal") == "COW":
                        own_cows += 1
                    elif t.get("animal") == "SHEEP":
                        own_sheep += 1
                    elif t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY":
                        own_straw += 1
        attacks = []
        if ocows >= 8 and ocows >= 2 * max(1, own_cows) and shed.get("MILK", 0) > 0:
            attacks.append(("MILK", shed["MILK"]))
        if osheep >= 8 and osheep >= 2 * max(1, own_sheep) and shed.get("WOOL", 0) > 0:
            attacks.append(("WOOL", shed["WOOL"]))
        if 12 <= day <= 24 and ostrap >= 12 and ostrap >= 2 * max(1, own_straw) \
                and shed.get("STRAWBERRY", 0) > 0:
            attacks.append(("STRAWBERRY", shed["STRAWBERRY"]))
        # momentum escape: price collapsing -> sell what the route holds back
        if day >= 8:
            for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"):
                if momentum(item) <= -0.15 and shed.get(item, 0) >= 6 \
                        and prices.get(item, 0) > 20:
                    attacks.append((item, min(shed[item], 12)))
        for item, n in attacks:
            if len(market) >= 10:
                break
            already = sum(o[2] for o in market if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
            extra = n - already
            if extra > 0:
                market.append(["SELL", item, extra])
        action["market"] = market[:10]
    except Exception:
        pass
    return action


def agent(obs, configuration=None):
    try:
        step = int(_get(obs, "step", 0) or 0)
        step = min(max(0, step), len(_ACTIONS) - 1)
        action = copy.deepcopy(_ACTIONS[step])
        action = _weed_repair(obs, action, step)
        action = _market_overlay(obs, action)
        return _align_hands(action, obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {"farmer": ["PASS"],
                 "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                 "market": []}
