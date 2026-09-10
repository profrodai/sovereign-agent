---
jupyter:
  authors:
  - name: Prof Rod
    website: https://profrod.ai
  course:
    book_url: https://profrod.ai/book
    community_url: https://profrod.ai/community
    distribution_version: '2026-09-10'
    edition: nineteen-chapter-v1
    instructor: true
    lesson_id: agent-loop
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch03-a-bounded-agent-loop-solution
    self_contained_runtime: true
    source_basis: 444c5f6
    source_unit: ch03-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch03-a
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3.14
    language: python
    name: python3
  language_info:
    name: python
    version: '3.14'
---

<!-- #region -->
# Chapter 3, Unit A: Build a bounded model and tool loop

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Instructor worked edition · 90 minutes of dedicated work · 2026-09-09**

This is one of two practical units for Chapter 3. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. Implement next-call admission under call-count and cost-exposure limits; trace actual tool observations through the bounded loop.
3. Solve **admit a variable-cost next model attempt** using changed inputs and an independent expectation.
4. Retain your implementation, failed/corrected observations, causal explanation and limits.

| Minutes | Dedicated activity | Evidence you produce |
|---|---|---|
| 0–5 | State the problem and make a prediction | Initial prediction in your own words |
| 5–25 | Foundations and library examples | Values, explanations, revised predictions |
| 25–35 | Trace setup and the main interface | Input → learner function → observation |
| 35–60 | Construct and connect | Source, visible checks and runtime evidence |
| 60–80 | Implement and challenge the transfer task | Function and a new counterexample |
| 80–90 | Retrieve, explain and save | Exit ticket and retained submission |

Installation is preparation time. These are planning estimates, not measured completion times.
Use the reference primers when a term is unfamiliar; in Unit B retrieve an explanation before
re-reading it. Run All checks that the artifact executes. Unfinished student functions deliberately
produce NEEDS_WORK. Keep your first attempt before opening answers.


This notebook belongs to the nineteen-chapter edition. Its supplied teaching runtime is embedded, so it can run without the textbook or another notebook. Where code uses `REFERENCE_LESSON`, that is the frozen runtime exercise identifier; the reader-facing chapter and saved unit identifiers use the current edition. Building against a supplied runtime is not proof that you have constructed all of its dependencies.

<!-- #endregion -->

## Run the self-contained setup

Use a **Python 3.14** Jupyter kernel and **Pydantic 2**. If needed, run
`%pip install "pydantic==2.13.4"` once in a separate cell and restart the kernel.
Package installation needs internet; the lesson itself needs no repository download, API key
or prior notebook. The complete source runtime uses Python 3.14, so this edition does not claim
compatibility with a hosted notebook service's default interpreter.

The collapsed cell contains 102 frozen teaching files. Base85 represents compressed bytes
as text; `zlib` decompresses them; SHA-256 checks that the decoded files match this edition.
These are supplied packaging operations, not learner algorithms. `tempfile` creates an isolated
working copy; `Path` handles file locations; `sys.path` tells Python where the supplied modules
live. The code is available for inspection below and performs no package installation itself.
The subsequent lesson teaches the libraries used by the mechanisms you will implement.

Run setup on every fresh kernel. It writes scratch runtime files separately from your retained
`practical-work/ch03-a` folder. Rerunning setup restores the frozen support files and keeps
your saved work. Restarting a kernel clears variables, not saved submission files. Source basis:
Sovereign Agent `444c5f6`. Some tasks use reviewed local subprocesses; they are not an OS sandbox.

<details><summary>Supplied offline setup and teaching files</summary>


```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import base64
import hashlib
import json
import os
import sys
import tempfile
import zlib
from pathlib import Path

minimum_python = (3, 14)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError("Use a Python 3.14 kernel for this complete-book practical course.")
try:
    import pydantic
except ImportError as error:
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.') from error
if pydantic.__version__.split(".")[0] != "2":
    raise RuntimeError("Use Pydantic 2; the tested version is 2.13.4.")

# Frozen, reviewed course files: data until explicitly loaded by the lesson.
COURSE_ARCHIVE = (
    "c-ri}3v=5>)*$*<@Oi4P$%LXwJuP}Udlgxk_{OokmXhq0q+)>tC}B(y3_)7fxb)xed3B?^(EveN_SjRJZ#Nc"
    "!Mn6xV_v6!(VVb^w7EW%$+iZ|dpN+2K(fe7NOcxpa-RZVxw@-Rc&guUSufo|Po(J7tkWS+u{y3W?qht|Wr%^"
    "l!=J8+4I9s%Wn`Chngwr4$k0%MVo5$HKon~<`PChP{^SI5uolnoF$@MIqFM@D>ISc1mtRIZh*{%L@6=qkHWT"
    "=1tD@)<i@jSf_mh%a`Y0J=oH2CH8^zFMiO6Kus@k=<3Ch@!#yi?N~E|W<#NN4dhp5q)&emQ;{^n*|5(*XW={"
    "$#Yw7U?y-d(wknua~3S^CzwR<$NAb@e#iK$4_sKce8mKEk}zC-<|P8{NJbZC)xWYe{k~a?;C#{ym|Hd^#Obc"
    "52oRD%&-0kr^#dz^5b+mxPpn}n@#*ZkJEV+&j)lc`1JW*t9*pRUycutUmu(vxnmq&rK5BbF5<!{UH>q<Rl}T"
    "|zB~Byr=xf8{^^c$vY3ZA!+1WwEe_-zXGe{50sr3Nshm%vcpO~ESr%T#StGkjXU!hBna2P{Q+tc`pL`VabRt"
    "v9ZnH&vtxqX$GD@e5m`6W<^5;BR#6cLqFmr_G`81hc1^@@6_rY+Uz)Z&JJV01z2MD=#SHA;nr_;%8u(*nYY&"
    "nB#5l8a%I0T4j2XA0+0tFz!FrK70*gBa9vKIm0IbZiL(_oq|g4uFDf~x@2oZc?3aDFhQ(IiZ+p{H;`H;#IWK"
    "PDOUWUbjb$9#X58A5u?-VnTD?Pz&D<Be|x8EnhoeSDksPv^_HsZT3EsabeCNyA9m6GrHtKl$q>o^G8#aZb)S"
    "uJb3<6bGe0TGlH$eR^v_g4HZr%;WGH8~q$kve<eDXFrSQA)*~@(6RduKMoe@`*=ztZ0_t@Z=qAz2H598JciR"
    "3NSOlW(>rTGDzuIU1S*Xv9WAe6C)KKxF`ZwMCDUvXPDinB(F&quq}$OBg$bPSAK_#fAI<0Kyn*L(J)6XfB%K"
    "EF^aDW7EDo*#M*$SknGgR3Xb$$6I~iT2$tcbMp{YUIm+=C-;TO7LaaPiz6-)qrnh0H!c&eT@ga7FR;;)=35("
    "Q(nh?M~cN6y?}YSQOf=c0NpvOfgq^gz}!PNqqAHQ*D1?s0Ai2k8tBsqSV*NkpS^XYl9zI-E>y^=t*=^mJuxd"
    "5m}F(_QIaN-JXl@<e)Br0HZZg7NS`im&JKc$tNh{N|J_Ck$qQ0H$i!0qZcfx(PER&j1+4_9tU^6v6_sdtsI("
    "IQhk@Ez}LIvxcsU2fm0uE@1!cQ8k_^-8}pZaL!^*JA*IrNgEy{v&M=Y!TWhVTinV<6s9C72s_L#FQMuIq3RW"
    "srZGDcDtOTf@NZ4p;5XotMu#6e6z(F}a9TH;d8bHQW&s={qS=^n=$Xk+K;M9T`;+i`7{QVEf_xUu0wyL7PEe"
    "8Tq_HF*JU}A)yrcA^Azi?5!%2LNsN>AUgXwhwBnt_aObDI@KhhMK;$QeyQdmOX2oBudi{O9x_YB^e!>H*pxJ"
    "-E|dii?zt2q)$cn{D3w_^mC!l27@CX!6@<h7!l@=)k(WZyoVweFgR?%9M|?O!{b0dE=M=qX$kcor<DI656}0"
    "6+#8rYD<7J=&nD`Z2(B8qQ!t7lS17fv51t?d&Q98rE1vyxYLP0;z2@o9(OkW0U|<T_6mo(TG2`#!=%VDg?&7"
    "9mVks|KLUrX@8<xBfYd{E`K+1lZR<UJhWyT)Juz`en{dQfn=N&(o0P_nG;_O%!wvE`^A|#iwneW=0tp7mS7W"
    "X0v9TrULr%60CFN&Qt}3(SsL(#eiQ~{kaw;a{kVwG$0U?<Mt}_$%Z%BMH%CV=PX<399G?Du@Otp>=#N)Ne_9"
    "OQ`IBfKj%m~B(wlF_lkk%IDWV2zFC4B)<3u`114a5il5+!oG|NEN0`e6r5iDzX1TwYpe9-)AAe-38;>oy$Ti"
    "Oc70Kf>YfL*i8R&WJ77|(%6nZ`FD{H-`XHD*BcG>%>b@LxJXAVTBh61c($n5u{{PQY!215iLXNj}6xs2d2fY"
    "P`P%2XL)M@8iWrO8h0#z(sN$r%TvW#7|+cNEhJ*Kx8u67)?+VxLk&FAe(XA4wNLlrMiRh2~`5;hSPhGq99@p"
    "5TvFV3AH%?V8}8CfX))cIG9=hbQM@U1w;&keI@KR%mckzEM~oD&tNLy<SNY;y>54VYx~)UF39=e;#p42GYhb"
    "ya1r(moI=~6afs1Sj;0SN;E+lD#_8=$#EcM;?}+y48OiTYlnfykfRqNNXx?yv2=EoYX=puz?00{w(+uDuDm8"
    "-z5;t_~_(dD9Ut@P?u(P$7^B&0KLc3=0_kdpQR)dsQX2c&yaU2P88S!~O1$1x=g5)Ftn(49}w1<f7G8&IT?D"
    "*%OU%z^D1ULHR?eUwFBTEsXIQCwptm`ntJ<SOhL|)Ch_S{}vso7u#TfUZ-@GP1Oq(i}GuviW=qTHEQ0??aou"
    "OQlTU&9pDMe}$qshB_2`V1a{2X6)8Fom0eT#MBWNZ~0H`V88CzyafFz&t>^uuxNCzSCTWsha@CTXUnNzCylA"
    "sj}J!^GibTZ|O}Vin9^0uXq9ag8^Xw!Juh=+76>=5Xv_IXB!)cd5|MvhM`ZVI*$hnpy3*{%Dxq$x`pU9Tuv5"
    "-D9#^3Yh?7~d-?}^$P_b3R1F$1Gk_{G^#ZQHJV!Fibo?TJccvx!3*L>a&A*ur&TozDrDz~DbkHnbO!^j|2Qf"
    "(XfqPSoTS|NaUGyr3!B_;|-Ps~IKA~IPGH$prJK3A~V`Ab_{9m_lvwkBDD9%3^hsgxsDL7e#fVGd|VqAyJ$u"
    "8k7aiZ~r1T)rnyzppzh)z>mt#XC07E7Ro@DL?y*vK55i4Vz$4ghePfUH^jgaG69t3Qr{-;Q4%y$<v?KJo1J`"
    "4ib~-7NU|)&D*H{oPRxdDJEE_?c!tE^@r8UkUedVQ#I==g*K8ZPeri>B^SjL>;J--FgVfh3*7_!bpPw3J8Ni"
    "&__9TFu;pB7-%t;@9FvUNo$3!d()@u-UNOMs8~c2O@Ly1765jc^GTvsFPUy!$JZ&Kxl;YMrOsycwfvYbr}&D"
    "L*|Ttge7w?PzlERYO3^*LjQ|@bBlYqp5E}^STEQW)GB1-6!1&KeJc;y28BR1#E~f+L5(wS~M2w`HQ&`U-KyA"
    "qfq@{?G3}!aEQs2Ck->6hS`WTOv3*=O=CqtV~>uSS)2e_&R(1Hf8r!g3e;d%h>Ya_v@gCpG(85#h%noT%j?1"
    "PZX+jp-Hk4}gt+NyKZ)^%D%b$2h=>geaDei}a5+p&1mH>twVSwrupLg&0w%p}6_`4%^TYo3RIPC?WhCJ{m=s"
    "wGAXmaWVI-m>hQk7A6dC9C&KWUY~K(9t!n0d#>Qxm;ZJyQEOizd9YO_m_C#^1j`{)Bt}i5o{K>J>)R;D3^;q"
    "?9wF0UOTSnHy|Ll1VF90hLf15H(L47bL2sI*CZhv{_tx7?kv7by&x47J}7>$g2RuN%vWmVdXPjhtys8tC1a5"
    "M(im9X6|_6VU;Xd{%%1ES#NUzfnH4*{bdPF>Ul_`rJG)QZl0i%F3Tt`PBHPIVr2U4e5W28tE{cl=B56k>L3k"
    "U^La9VlpN?vRH}2Q?R&CpI`hJ?;==K_``$bU^2-)_dhAhxPHBV*=C(F_82FV&e+e@hxEpM}&CJVTM*<t`p|A"
    "_cfMh9nV1{XGmmhTu5qr!IK?)UW$<-O!B_`p$Nx$b!v4@F%(glz8DdnOhz>u;iDJVq{+kTNSAKsG}*pV%er&"
    "pNWdmgxc&)f!X^xCa*6S1WF=JnSESpdJfnq9&-}Ks_k5B;hwdIeSZf;0d334*8-8R)!Yj<-3EQPi?!FI(Meb"
    "mg>?bP7SwXv~mmxEqI{s9f*pw^Fq^!gNtI|2(D4wLP{*qBCAT`tSCbm7~gqA<C=_GtM<I}d*+{Ys9+qVQLXg"
    "E>EmW2>op=3CfvG!HoZ7)7kb>eOQ-jnK3&d%(zm*Aff*SsNumq+8na?RgATBSz#uMC*?r)FV`RpZ&en4VHlc"
    "K0(h#0?Tv(EO&haz|%s?iapawYV!v+0!JO$RAUbK;&A!LugaFeNdvsofEDws9Nt|6tc0lCl3+R5}o`aW(bj;"
    ")bIeNoaO6M`f69heT3NSO6M-8C(~{j6b<afRs=!Mm`DICckbKOm}tmkQfmrfKBPF5gLeo+2LTdD=i=PPEEd!"
    "bCs2%Jych%g|Hd^a{FfCB%lcXAVstbly0PRa1vCeKUVxac9dX?ril4>j7^7sBMyh$V2xJ=}&k|8cC%9%g{C#"
    "lHeW?ooA-GhI7xl0?_NDgLiL^-qn&SV0P)`L)>VhP6JQota}kWLu?;|tQpVM!co+Ko>5N+*BN`H#r6Xk4B(w"
    "#()Gw6s+J_4pjummF#3n+xYdVl;dGNXr;h07DWIB`hCZts{od(Di*HXZl<YM)JwASYVttKFHDebZ?C9j=;2$"
    "Jb39+=S4wbGmj^^)|crqie7=YmzH{4-V=(=QWkUHksg4H8AhO(7<=TClyy^BMTGZiOKkSA33?*Z^*)PZpYxk"
    "dajM6EqL!Kka|b}l|NOj5KsV~)@dI_=<Od3_zulYg_3fUr0~)N%rCEt2W<eh>f=8j|K>lwQNqBen=cDO?jAm"
    "+lYH-O)UTH`7b%o+q=ony1UlD?MOg=Cp^TAcc9)(kz^i`J;sFDYa$EnToql>50CrI7enj#rPA*8J;YVSmVxw"
    "*XeS)aHeu$n}raI5HR<Yk{kc;V7a(T(G-*8mIc}|aAq*|U<}0e1#S><#;N!NWXkO@ibqL?Rtp33C_!K_NRYu"
    "Ch(QU7xg`?d<2F5o;|DPe=sPtr`%tbG(ueXxY6Zdy{Lsn`KPa!mAG75`{EE!MY~829UQFYUZ1QTW(NzP{Q=T"
    "l+*{g+^nY>~|j!#Szh2mY~k5}O`V^<J9#5d^0q?r;ltDv6~4c{nte$Z&BL7pppA2YJit;deEnkLVf_iV3D#w"
    "qIl^~l9nB!y|FW8;I@ghAq-kEZ*Z-itx;^wn&A&Qh{3yA;=-(_GDVoz*l;Bm(1f1)cSR4`MXh6`PG=E!w6>F"
    "T{Ylx!dV5)<rBsN^gbs;KnzLo`}2&@ds1{jp7F5@1`H&gwyPX1a0KmuaZn%nHOTiy+lhSOafh<!zm;67#ZPk"
    "k<K;3Q74e));k5fKz>n6h?+9~HC|51o&(Ry9B7o|Suz#k)7FlVRy!hx(5T$AtQDLoZe27|=@1CO2O@W8hSN;"
    ">khZ=_o}MX^a>2f1IHu(`M#~56olHSw&`(K%fRPPLXx^bFLyk6uK9aSi?-7F~OjD69_9Iks1GPG#)1glC0rf"
    "@=5|(+0pSG@0&m%3u{Ao&tL}a&8Tde(n3iqZ#9U0=6`kmi6<DsQWF`nm2G;_xcxk7eB)QxIdv`*8b&3E~?TS"
    "2$Wnsn06nYX!7KzzH<ddJiH;=jaLTJ|A1XV64f4ZX_T%B)O3(DFiqJ*ad0sm~;8@KX(khD*PZ)?7g6xp;tv+"
    "g#@W0MxMFiTy=`5h4VZzDV}rxwVYWLH-e;qQ$-sS)Zk+M$<7D5^iCYUQ44IHnt$j($8`%=IembwmzLKBZTHh"
    "{I&&@udr&vbnflJ$qAc5r7N+4{(SK2wdtiwyPuzV!JcVI@D37f0b)h7M1Qks-^~tNN{wA%EOdDM+uPSir$;Y"
    "gUSvBqCf2R131HUngrvA5v|{rmtfL#)_UQ(;dq9Wh=oo@~hi+MO^vnUEZ_y-ykN}1i@djiu_L~Emx+E@?5d6"
    "o*y3s#AZGrqk=YACYYuHcc@i<0o83Ss+1lHr<M9Z@_-PJZ(JJol`9JX`<QnLv68Ayl&G-$9Z?H~vI61yq=mo"
    "*Cc#941p@`3WV8OSaLdMl>vsK=YzLP1+rLYL(_z8;oOL-%@<&fn`UF=V6_#M8f)@e+=a{fA1rK<}?1IlYSUS"
    "AN&FFy|T&Ll8U`T4aiX9(nEBG|6gtP2ozztwg^YqoQG;t{pT|f=+E|?uYj`9y^<_^CY9*9Uj3y4cknrUKH&x"
    "`2yQ|rsZ>dB(F8eE9rR@wrHQm2%6#i_9b~1rt{kd-m2tdU(A;5&ar{KW|+};)ZFq7f)4wHVjB8=lN6175wgD"
    "~35MAj&Q3%4KwX~(cF;6|S1?Q?8d^}n_ZyzJ#HPw5%di2V`YC(QT)f1s!G6Peso*>O>X`u1v#w<~jE3#eB!%"
    "fTYt9qE6d;YLt$~ON)5|B&)G<DEPC&&F8A>n60jD6#ksv`d%$;k|W$0jxq-Y)szazdux<AE|-+vQB9AKKF_O"
    "5&zH?3{7=a!R2nq2*TT66ki3|Lz5-;1kx90$YY1TaSCneUc0UqSuSV>*d87NlFY`&X*K(D7v_8Ruq77=~zx^"
    "g~E*11Sw|sTtlv1cqACci8yl@f(RwCG~Nbz0XQ^ziszLWU%5WtxF|-c6~)g3*S|#JKKbH3Wh$@dM@w`m)-+3"
    "$|pljgHJdYb3NTS$5`)c1${rm)}#w~Epj$|Y;#^cUbA<u6(bebi)bUAP8rDCG1+_3jqBv-_0i!e47Y>{{m=}"
    "4es}y^U^5|bK<#l1yc1B)1_C|a`)+YD$I7c-l<M<H-*Q@pcw6})dK%wULUdi_wgpX!?XY+kN4PH+-w;XJ;iP"
    ">POX>*krkH2HVK-QZJ2g?ag_1zVNl~0w-xW{U$4sJN%8?EaY?CaD>ETP~C{e5{sOE`AE)gM7GuE|1Fu#ZSux"
    ")wdUA~%y3(HKmd?UIIe?(Owdeg#RWxW}yK7kt>BO)An@L?^1+QTEt?PK<^$c!SoVRp9;Uh(x(14C6Iy7ju$V"
    "!Lr5wgiuQ2}_7~h>2`^PELv<{7<is4}V1|S}PVT)q#m|4n^>qqYYBRI<8qhDdHRT(MwC6&|5>Fuu`XRKfOX3"
    "SNDzU8+Ls9h8=W`r66iixyLL8eBi&(qlpqPDE|Xt3DHbCilcgoM!pB_LUr%5H)xrVAr22tP!TtR9ZEocj|a5"
    "bS-y>5Tx%gHUmeyU!+17P3M-9<(t|N~+fx3}&~TuFHPu4|0^LXRD`_eo#p-%mYl;cQ=!bq_Q2GYPs`u{65_y"
    "oM%@28bp<+N`eVL!YEBlsZ{`<>&EM%*>=X{^zBE?$(6aaq+GTk8DvGJkXUZmF(b8Q;EAV-+rP?|Om=#!8~6t"
    "p^wVKH%#qb{PH6aZi$0Nfdvo$auUmo*dnrLom2^8t6!ELaBVj`uYVY*@hCV$9QLBm-;9;;c`2^sKk#n%86s%"
    "D%@xn_f$#i-YsVRem8h-t-s{VULRs^;qPFTG`+Os`1mQr;Xa4KF!zDKm}zDc#m?qczpik6F#HS?|L18BQ{cV"
    "#)Nz`TV7+O;qKy%#;e6Id3mN!=TCA#BS&&Mz&k(tWHE&r$mL8Zb;G-(pMO6=Ua9GdHbutE00xhkoA*!Ksjq>"
    "|P`GD&g@Sl1u%0uMW=rU6YxJC(8G6)f-a83XP+)W~Iq`u7RN(opXNz+2u3ILC!1*T?DkARJrw96EyEol=^+L"
    "RLmrFQf5@?jD#G|g(>HL-eiv=vLx^?W52=`>N1a5;*#wVY6r10u>73Jz$%gMb@viqsGR)1Y0Ei263Xs(o-wW"
    "L``@L5Y3eHbxNLel&9)vNLM1<hJ<ns1f6D9w;R`z&#^6txnMV(^(g*RAO8exj@FB%YMowLZN0YI5qXPfp$K1"
    "t4vbb3E)25^lq;2)mtef~+N3#&PO8ai-Ft1WN#$IjT1ox9bY6Y4#|;{x`_4eq%l3&Vg2SiSeGbV5HPSW%M9-"
    "q4^5Zu|HHip2U~)@Opq=AJcfEBh2M_O94CFsu<``Iw3jxEugZur$PUrT+egaeK|weX>d637{k>9q8R<|=2lf"
    "cO8$;~0(*h+wI?y9Cy@$>X)sfM@r3)JQ4t{~*<i?NvB*L3t{4`36)yarE_5Ot!7zFL95dJD#|4MU;+}eve_H"
    "YHa*=;Z6_yW2L}2JF7N`UTbXDn2&pTCgsF&x^k^JSnPsd|mpfbY+RlmwuiC%b)G+}^#@&kkp)HR5Yr{URwF4"
    "W4aV{wJSUkLO~*MSvZF=4oj7r)B{pZL5uWS&aS!`?9Jm!1}#F8?O(c!=cV5AhWC6Jx9=afG?U@MF3GL$qtfu"
    "mm{l3C8xvnW!(LSOv2q_4i5;=JtAa&YWqp=)dA@qHoEi`&<k;IOU)RofUF~vKz&4T&J|a;gaKCZee{{Nr<_+"
    "NpjuxJDuQ1)&r<DnF-+#`jT*x{9B|L<vCO)-*_}El5El|()7M1jY*{rpdkNO%Koe5el7D$eo2-pin@z(Z9&7"
    "s71Y<KxEg^6RWaE9meJ5iF9^&*ZmrW4)^a+lC(o8hThe7)Sit;2ZQ-jZ`#ARKmQVC<73DzV5$6Dusq~ea*5)"
    "%BmL#GlZtkn%JP_^bUW)99y|<la%ZYq_FeSj35%M0?+Nkn-(l@G!5rxHfNZT9MRA39=Ri(iuL}?(=)v9dcrV"
    "c6pXU;V=&V<A2cD592wZFgLRD1zE@0ve0o94aetcfX!y@pN&c(Xf`az$i+NCl2y3a$LhqJjbm2Yf;i4x2s|m"
    "yjqWrAa2iT<wM*TN-+n-Iya{KDMV=qaMuF#O{{fUSIioYI`LRZfM4GEtMX$DADS@)ah~HclbWn?`4>sOs~6a"
    "hdnwiXpu8;z^QdwLASGg;hve3R0s15bS{cXaU{h+iQ>bP@lRACN#t`b3jX}%=-pAkSHJ)C-O<6ze?AS4-@QC"
    "~7yR^34!(t(2ZJKJQL2VE!?7rE+4ky~p@v2Kb+il_p$}_^WfnJ$yYc#HWHGEf8sy8bK3Mb$j!BWACRONw{Nd"
    "<f`6RoZN#<RPXS3Hw0<Qmv8mY@cvmi*)9W*PJSA=C79}2O{H=Opa<?(weuE5X^d6kWh4ys(|$g^JW+<jXr{Z"
    "u*U*o);4ysPzU^bU32cb1ds95!vN?P2OsTkLTlBq&unsUF*wwao6t55-PSc**zd<#TY|!4eqm5Hs^28#0a79"
    "NM5ExM?JNID|x+d}3@?1A!@YrS*J%kH|Y5r=Upq{mrj$j{kh)Ns@DN^rnynDJMgtIGHUf)X7sXMzxj8D8ND="
    "j8ESu)2RPc&$=y~25r$(6OXP`K))kTPE4i<=cA`8KHU7{8`O(yuXVMv{h;frpvys6sjt71SBase+SpJ`iv=u"
    "Rj}I%4^JLbiOcB8?NTsNkAQmFxtP98o;^IkCK?|6{P>BjjcUOC&^E4$E3H4lkWJ_CW8am=^;Z6j}eEcFejp2"
    "1X)eBy80+pUPEpt!MFOU^Bs1g;oU~}w%Z}sX4d>c+Yq7h-sk79ED?l-PEND}0-2FSy#@wTcH%7PpqVM8&<UV"
    "HkfoMKt-cDX?nm9U7(Jh>(UUCOY@71IKg9kGe9<q6iZXK!4Ve7>Opat0hKa8<eeG1CX^aGJH_>4#(vD2k)iP"
    "mccp^!e%^Zw3ed0E|621$6a~cL%=>PLF>*dc*90eoP~ghE{fS{PyVG!Rhh46Wv2QgT2G1Ew`u&&rOP`pg2y$"
    "w394KF5!zN-DE_9^c-`bcQ_0Ke<ESyX*Emt&CN|0FX#jjNdUV|91`3V61vkYAs2%wK=B-?w4%Z}Ccyy-<;Vu"
    "O$F5UQBbTVITZ7gpul!=Au|VJA3@xG|9Otl8Di+rfPZf=M6W=I(Po><cs^LVLCtva#%zKyjqtGsyuEII|LPl"
    "^oR|$rOfQ*sa;tca(22@mskv3T(wnAepx)dl^1DsqCM%T$=!9@o!r(lA`RnWCI%P78A^@hpjF+s9&>LT)tgg"
    "Q9AGP5J&EEJP395GIk0yo+!TP^$@)nHxf34+3?^#6Bo@aCl}7TQ^s{6b>z`qgi*PJ_*kMIal7Hh|&-kY5zi*"
    "U}m;W;*cBS<1Z3$-E&9B(L1WyIQ(HiO3P3{ow{IpyU?of{>#Av~2^bGk-j5F^h)^g!y)3U#bO4N7L(inrM5^"
    "r}HOF$t^QrP}CXrWW>8K>)J0uL=w9oG$7d)W9=K89TQb+v7^6A4zeb$Kl4Mx5Ki-bVGzuJs?1OFeX{`Nvcq;"
    "#-ZL`}@?u@NrAo9CG>}C7|BZJ+a$fSGUbLDk1Q$WNx{+~KPR3|&Ee&33?)s8>3u&aw#W4Li;N&d18%@5c-mk"
    "Jzs_elE$HR_g!1u8V2>|{D?01F*;0Vd;#QG@zr$S{3UsTq;Ab=1sEZS5w;q(eT#wK+v@M<VTn9hxLn(`J)7j"
    "j$$4L!a0z)fFE#vYLKbT8S6oX>RZq<3n{(MXp6#r=);eEvpzxxWz?7W!AJORnJ0c$Q=-x(6~XQ+agpLfl*>R"
    "E{jfIMIm8o;-}RQMMckZ;(H_%{;zH>H+ZdU)C|HUJtsKq2V!<BAnIvnrmXAzAK@}s*`LKPFukZTI1Go_Q^2t"
    "Y&nTBqu>abvgK4g`HC?wDo@maHHvw%ir$w@boOu=&ctD;G{0Hh#Af|Gu^HX1he;u}ehRdzG-#d_X!Y}y<(s7"
    "l_vhp#YkHH8asSQ#gzif;I``6h86?wH^_Zd(Hp_7-h#Scys-^q-F0-QCgzw`j>oUp8h4`q4@%Z2MgrpB`Z~t"
    "6$Co6uX;Qn2RF&s!85xPKf*~b4gn!!e}wQnfN^MsE12R~X(6cO<T;!DmLJ5_?Qt?W!l7hm_^*MH${SRm&*8L"
    ";Up>vuce)ex`&tC(D0$5DbV0R%`nqhFLeiwghW-@ZIJJqm2UUCa=Ca&!uCjwKTNc7_|#-6K6Exo4W*^zBTD#"
    "XyBdF{-D+`ap&?+;m3(L8i=`?Lu!}N#X{vN#JVmAmn&)1nANi?D5sMwqtFrXi5k=eY@*5t;t8t+=x=|XviRC"
    ")6H6^RPI6`m1k?%yI|Yfl3*lyT2Mom8JD~%2EqwYG_3rVkfj<hAS(fBeBuD4g*WetuN7|8mH`V_z`jsnR?&N"
    ";RBwJ*)OJXp`3Glttrg*Z*w3l(iOV5cT}X2LGws@$DaOcg38~6E>Usp0rW`dJ`ogDFLag%m9AigvcDv!=#+n"
    "EP@Gef?g<TQ^q)SPAyfH~{-0U>g3Y$eA6qG9L7&_x#Q6uA4smAVHNOKU?gbi+dZ@AE(SHML1$zGH>C|E*n*;"
    "zg$PE4kF?@)z}xKOG-^`9$mqxZ}HQ)3NJec)1d9AAE#-F2q99_0(?Flm?UxiaypgikA+KMYGyQ1Fp>AK&&^$"
    "SHc3!Mj$j%rT5=Qf;lkvB3w}@)H8n=`V66|9NtH^xM1R<5T{9`rF%=uii=CvV%AOkiQNG2d`hBKe_WdWK<YX"
    "jm3#qzlUJC=07UmN&lq;`)sy$8@+!08#nB`6<9s{{x{00&H=Pa)Ih{$Snx8=w*t>}MJZJ_yC(&ZQT8#qyk4R"
    "&Q35zX70Xl>RMJ&4bWo>oH3G8ra#@a8r(ZLJd&%n5H`Gk+w^R(;UesB3n+cqvdJGR|<61Jr*}4!(g_i$GsEh"
    "y1-4ReQ!M~esSu!}ezHxem;$9Kfr8Xz~>g`dnQ9PfoXoQwMs{d2?IGisA)A(i}Zg_5^Qva#df>ALaK@^7(N-"
    "RncxlX6)0tBHEV5=X4#(u|>oBDaP-~p=Bv6|0WBU$M7f8~R+$2M;f*;<<=hKYQby3C+sN^D7DYB3!7EDF9l)"
    "Z7cB*>s*<Ce!{?u7#liy=Tz<-sV$ZFD9BSzQwdnu(VwDos(onT6sc6?S+2V^Uu{W;OKM5Gsq@!JZp5?olR#F"
    "$_Wa!>bX0kcR~h_&<cFnE3l3#l?s(riTgZa9E}-FCmIh>J7E`R#Ze4N0a3o~mupfAe7lYlvIR6svFN}`uA~w"
    "2i_00HAu4xA7B}RQG96<5AiZMCS2o01&4u^4N|m`K%-0?;Uwb<i^JO3YnX+ujL3{S+sYJtP08kjH);m9+ZUl"
    "t_zI#&m<9ylagj?Oc_D+Wid_e0{)GYQ2Z=O~{gJKeY&lPgwe!GHIw4`oLqgZ6%z*70rnNOh;KNGc%aB6`T*B"
    "+tEu#(5BMkfW=d;Fj6+UnWR6|Ad2%s}><;GMRu<MjH)ojTWW>@+Wm&y{n{oHPFOEHxXiFd^G8p+(VNuv*-1t"
    "?G?cP;yq-XSJxdvcFsjZg%PkKJ$N$p=*=y7QUAB5uU*6^|poMu2xTd)po4ckAE8+thu76yNdT!?>uJuio0D<"
    "HBZAyAtD&#+v@UNsv#H1B|+BVWD8tn&MCKq8RqiL)DM=?TTTh5G^D&*f5+)k(nT2@w2DdoI75%%ifK|zZS#T"
    "W<C9-iWQugd*0B*{NJKTj9u?oH(R~ScPEL>CzNI)uD$I(LEviZWq!1PDmp7Wk;dFBAYL0Ec^e^hg@Z9Ic@Vv"
    "*B8-s8LdjOI;9OV21$PbwcPiu*A08C7ZK`uc^WxKEpFwi6l<A%#tbYZYO7FfX9dI(1aiS0Ff739fvI0Za6e^"
    "`G89lT!86+wyR^7V=QK7{{(h`Y)QLCBx_7_Gs8R^O&T)o)vJLYRk@sdP&!QO0Nz!|J*JiTWe>fB&z00BB-XT"
    "QQJxW(i(r{0Jjhk>qmJ!Z1CiFckGf_2Oi8tfh)@q!C9c;X1NyTzf)%>YcXd!;KBKWrdfh&7jyR&quhqp58j%"
    "5!7xKyQepnQr`Hxs1|v7^v9duU%$57I9d_Ajq<s-<C-h=6Q)6u5eipig_**!0DxxV2mc^Sh;k`fJiG0Iz12M"
    "50qYChsMH!G!I=7vk3(1m=7M8AkR^!RCh;V4u0Ql~wOGu0&z^NR_u4S6c9$KOc`o?h0c9;{Hu-Ak;CF{BsHE"
    "~m3a^^qgg`EQRC7%VUPZl2$I|H@;xQUA8|*QmOR!s$=69-VncZ7lEGgOCoRmUB^Jq#wz5}Axsy*dKAt`P-#b"
    "_2Ru`s#KE2(IrM#rdTo5#Ia=!@(HegubhgNAz5G8!3~QXWPfSdzH5ScgFX_j%9jWKfpzNlSQ+q7X@l?eMPp-"
    "=Jc4PL_QZHc=ZFPMDEHibY>?$b--F1lQ>@MieE;pB=v!w^qVdm2oIaK)6{nQdO#=>C;E5yd(Ee0C4|)0oZkI"
    "){|&8Yv=+T5m*P#_8rpinW3EklaBJP*$ND2u>L01g4Dh8jMckNr&F!Qp@EAtsX4A+ujBCoIHclqk=kUz4n40"
    "vPN5F}dFd1?%q3Mw`BVW%Koa5aW}fn;;OrTO{|&9VKNJ2dCTy7XO)sDygWXPjQLj};b>`V6@=sFSwk+_A?@{"
    "?ny?GVi%cYc-&5EXK*Oe<?c}x2|%G;G4RO_Kms(k;v`&O}EHTKDYN{=+n+oEr}uMhRkXT@4$%W7s?UYEF4L;"
    "t%N?U9jzASv<=bKllO7z*qa!q16Mjs|j)Z9!Rc1tk0}IAjMc<OIosG)SiZ5~l&Ox3YA7IY;ky-sMR6Uk(KTM"
    "hOD|Y$Cg+KSG&LLJ46jIGG7CLx%+c?P!3^@1)-;P&l<?&6T#0@)H%lQg-FbouP)9=J$A^OYz+OF6-Zd1E~cI"
    "GSt;=mY_$q6j~QALX5RWpHp;-n*w`@>MexfEWC~hTrSy5;>$qmLwL|I$nXkkahrRU+@^KtlV}Z_wq_r-F&i~"
    "BQB5|o<dT&er<Fh45?J^K%(Tf?!6)yI{y3IgXx-1Xlc^OcXISR<3RW>;7+2Va#P-#xWlVgBCrS}@@gxrMY_&"
    "3yCzDsNaGY|j#32tr4JvysuCN}%RmyA$B$vFc$z!cVH+5O7HQ1`={jsfHv|6A1Zaxry{w>etTey+vcu+aZbi"
    "sKz%aCiqmAEE;tq>BI*UL#rSu0R4P3!q;qGE*@w6L>$mfcTmR!0D;yrAEd{KNV$Ht8t9Y}l$U<N!Dav4{F=y"
    "ov8uIUSU^8hEIOPJX5|v_f4aC5EW@{w;~GynYdqT?#7{7081|24&Qtgg8)-Mc1r@!^5MulnvGU-95&~er31<"
    "M+D3Vm;NQ7twvuDeA@H$hN8_%PCM6`F-8Hd)OYS-QQ2%b-s2dC-#z}syn+lSvT@#z4gWOtQTL*02U}tvdrtO"
    "+a6<BDUs$dOayGINc?&V!Vii(f$A{6sfqF5(GIqrE%yH$;6YwfjpL;rDI?9Bc&@;-oE>4!@SVpdWhR4<mbY5"
    "l(G83<$cBvbfdyhG5s_z<W5GZ9JB{YPBGH_RenT|pELDs+06T?(@cq3`o4CPcNcNNYVsdhcnHlr;N6q~8rG;"
    "1e5;3?K{5ZL!Q2<!u$#2ihMw3m*87aCGVd4$<nI?ZB9Vim;*nejBw)K_#3c=QJNg5Ch1;RWz;)_(&I25K9M9"
    "ss88U$s(ZZK)k#k{Ms~|1!q_o2-6C4*@+p0HO`@#M@98+v?!ali>3`2}~rZaYU3v)ZH*1rPpyFNB58}1r}`m"
    "H~JPRo(K)%3eD6CMEMN<D_7lhb+XX{`z7XQW)(5yqMnCAITHPLy$trtybRtc?*hdiuHjm+uk(Go0fT0GzR&h"
    "8@UX_8*(Y*j`5YZ?l1<+CP${qDkznM^Yt{^z|6Kcjr(pkAiWb~OGl?HB<lf3O7Z^D8h*x$uM_o&Nmrje~yUq"
    "*lmpJ4*O8!{vqC`xY7sM2jPfWb_jcQ`L#VTCLbdmK)Wl5tNTyqs_sLV>~%@jJlN@jfVaVj9MWEeD@xOUOM1>"
    "#f<WE=$$QUlH=;V34TC3Ip60b|WVEbgV#8h1MemTiAI3wD+6=-%-6aO$HvQz+FSsX9LQwSRqCWF^-}RaJorj"
    "*>|da^AC+Zx35CuW#les-l0NbrVbPxAb1Pr{<b7Tie2=MBuZMcr;@xwBpG2{Q5dd6wM-h8%mUJ$EQT;c6tg^"
    "0fs{67F8*T`C5nxr@@$bObo%F$O}sDj50~KfaXDnG2IWBClZ8vAWmOEAM+nkw0vg%$nQ-}lNX+qz~X!9ZSdl"
    "uD8-&W4FY3T`X=i?*R}U5WpQaPH+NMM0pm)l42(2v!<MS)UC&#3(@8Vp7tTxkzjYpV(GeNheyJn4c*}+5{tc"
    "ILz>){C0E*G~SG=rd5<J2U^lsEKS}Z1gwE&eAiXgzPTBO0X?<xaic4iKKu4MHflF=%8rH*t`La`o3+AyVz+^"
    "F<GLWaCvy?oWsUt`F(dYz@w)Ne9ium-QaxSlCCPd9Gg%mKbwyK~>{*fXy8no>el_|a(kvtz5xq{ez@eN9!Wc"
    "KjCr$lE55sMjs?N8T@FPqDfD>1N9=%Zi<Emyq9ve}{=|>bsg_#fA}^My^L2DJB<fioP$$mtCdw8e%SJ@;*~x"
    "`WTIT&9$Jc64z!5(Vlin5R`7*)lVuLE+!h+5XD**ovRk#!E=n$TrOsa$L^X|vFs7oD3e`Rqg5LAxIgnlyUSe"
    "7op<Q*s>-ionb^^?QU{~Skm~13AQ06Ekv&v-qk2_3D?5IuRt%AGaw-ikPQl4J?p5v<=!_f#F>%>)Gy+xzB?$"
    "~128?2KTPQy8Nj@GBsR}Xc`9NG*aF1nzhyurxWp>p!oZVcunyZVyN#Ddb?^M3jo>8V-D%MG<?jJC@0{rvC`y"
    "2er+}@H!nsPTKnNk%h#OWD;6t$zuotUJuc~li#1;e+9HO_Un>7sr89+-7?lv<t=lhb{2*gjV|Y|nB4Rv}zEI"
    "kO$$rK$;kQPpdSqSexH+8Wn;DO&#)9AlC%oh(dy{?ZfDz))s>6%8)FGh~&(16@wT4`DJvg--jwDL))<#_H5&"
    "o@518=0jy~b6^rESULeD-}DpQjhrv^cSn#|@@c8@(Y!%zl{e05bMe)4sFmk%tF%iL?8hE*?r3Oos-73hwrqx"
    "&>K?(sFbFEvyG%J}e&3R>eMu@di;AXnZYR<$n(Rs}67XeSKgG5%h*^_cn0%H`Nvm{2hDfqV(~UTsPi`f%eKA"
    "oSUO}u&@6lk<;?X5%!0Lqt|I<Es^^adc%xIQ<;@hvSX1OklKC)AIY}i8;vwingbZ47@U9Iym^JFR+J@KHoF9"
    "2midn$V$rEw<4U}DP=l*VDU*Z>>{6gA><g{1#(uY^id0{Oc>P0a&e022Yi?oL7bY?N7|l(IF0S!^D`D*_NN)"
    "3=CzC3ev=WO;DQJte(X9e+07in3&QVm6Q_-fQG!d(~yW)>eKSat&+y{MvADmc4qh9x^%B!EUw!_mK3molbHN"
    "Gbkn$6VHZ{i(dQU;QvYms71OQT{Q@I4$}AipF_B%by5M9<BXm4a7IUUTKvk|90Nu3WSVDHY<js8-s}}~B|fo"
    "hNZ2A;%aX4yzN*zPR~?l);(9WP>l0TP%TOC!_`(G*D!}@C@uw{@eSB6lM_JB26I?z&w#q1ct`m?KNI?;!H;Z"
    "WX)yvmM?zV}#)~j_Ik@FiWEZ7i&X|$NDP$@{s<S_^fwPW%=#HKzF4VD7A87J!WDzQ`!PCz-NFL7}~4PBKWTb"
    "H*g)r1YGII{g^Zi4idlv9^jUAkV-^*78xnHpiT2XDJ7eS&`K{S@;WbFC_=^3)4D<$AZ$<aIteQOZ90{J!dA{"
    "FS!Fhc0zwN@{u4>=j?+XnjS)yxQJp*OsQ_nLJfv?+yEg(V)ex^^JEk?cA?y5sPOPMq0CQQEs3u)CEO$#nBuQ"
    "d!cX%>yTJA)(U(r=}PE^%y`(vCZGJu7FwRPvfOg0flLDfMeIv{;glMFjqz%%3)KDSkTs52kgmEH)f`3B>Di5"
    "oNTxv?j;`Qxr4y<JgBX@W8#w8*2d`XMNtac5Mo+cmYsozV7(f*@MqM7(d!!+<<+U25fG{ctQBaxJ194I)7OJ"
    "v3)mR_caNqSB?z_F<Dn)vP3MyUNGi&Lp&c7YL<*fWEVGSzp3I9QzA&kr}NB6ec=a%+|G_Jo%71kpI#@Dm7#~"
    "*=*8DP1-++Ge_H%vda^!D-VwXEa!jb5l(osqKdoWg@va0+uf1lTV5Hsi(663h*n-7c=uX~{=ay%2NnVtpF*)"
    "sa>x;*faAzZ{>OzIuH$czJyI`)@~YPV<^+20|DvCn!KndpZb<%d`O5og~+kX(V`cIYo^wY9v(U;ivLCYwOJV"
    "=TClzEwj-Ern(z0Z?U=#2Y2a=50hIgGoEBz10DWV`eTIssb!Kl1R)2u0R!@AV|!{m{J)>m`3N(OLa)T6!+`4"
    "cVb3puYhX?>Uqw6}V^dWlV<Bh?@C3of$aIw{v3cYro(bao)(^8HFjAgtu48Fdu%x<`{)&|sc5%+ESm#awR3n"
    "LiQUbrRRB}5awZ4J4&3B4R$oik|T$PC3Bd|;1B)v2`lqZAh(X4h?o<a!Nxr*TP^62jTr4XktA4)z2sd?Ee`X"
    "`tHnLUI+Hw$yquQ`UpK~ig;BYLDz5i~rKrr*y*-+6A;=YP%$U4dX*;E#-t^W5jkf*D74NoYb9qPr7Y3lJGLo"
    "{@f$ibc1z;fycQyBIKDws=Q*x(&15V1R<rU?3o#r7(JIE)k!%`7s(h=#Ovaj)>aH>~GcSc;pB^FTY~Iz8sw9"
    "+_)Qzrw93S8#H;hFfn<)i+9bn(q9x7U@rD-gE&E}{_NKhV}xH3$Iq`=&y<-~7_F+PsclSkYMb86t}6amwnbH"
    "FP0z%&wrMqFRet6YTx&@6IrMMS@rE03=fm!98yYmkyrqN~FzmTFy7QIE;n{E4$Pf%Lv%dk+`Ba{%PM>vo(MW"
    "i)iOYc8`4R3aJ4C?-;W7jT3xvTn_8V%W02SFBBUjKH%?3i?SOP4e3NFgB2efkn<V6^Yfg47J`?YNYpHZ_Wi~"
    "sUc(gu0lR2WGv90yEVyjcX>Mn5?sw>GR6GOuNeDKzI<v2d;GWuGY+q)%NiG+8V<cw1#J9d?}#^F{JlGC(oe|"
    "EIYw#LcITyCEap;e0-MSQUJ5_{;I(@#}-rqx_MX8RxES>6;hQYf6rEq@KVIVsyOWt4b0BP|5-2K|~e7U9tSY"
    "FTyv^90r7hc0Jaa?)bu2DOGlKaWzkumsc#=g21a>XtgFoHl$hHzlW_a<EXX$1!g+M7+q2{<Rq@=kNP-1F~#;"
    "?@aFh5c=!987Xj7)Hc6!9KbVqAAS6}MESX{&>ExR5M9n;zdGQB5U;G{*IQN8s6LQN6o*cY+`P1?L9lZJtep{"
    "Cg5C=(-qDHIL%gN!pgVV!bYzT;_m+bRxxa4rvd$*gHSmx~A0I#J@cUcxjr(XW6L2GNNIksesuUaj%ySY^>ji"
    "AjID7{)QXABkdxFLoAwCfdVZP1lUjK-E6Zf}s{!V6r1p%iMR+4=btQ=9ZPQfrW3($i<jbhcbPL-hvvyF6_+&"
    "$!^-(+l{<wa5T>TW~j&=DjI-x1BweZF*{;I!fMC><dfA!D#Q7PcQoRJ~mrVmr3-r$4<pdbSl0Byzu0{%z`cJ"
    "G(@CnSzLjnJuLDA0)&0}x9KnOPBNI|iz8G^S03`z9)_>Z7)@Vrx&eM*P#K5j9UlMo_VtkyvscVRRP0B&^m4U"
    "c@)9Lz0zr6l3juG*X0Y9zovm#TEjSclWMz=T=A<$~|9DnCiT9Aka)e8ve`DpMLz44iX{i9c90h{hR}X{)bgF"
    "dtkx#DZPKcq;=)v(UV_eZ!IKzPsbcdY}kZbQVGI2i_=j={<$Il0<3{t$V;)$KU`t4}&`qgi*PQ`B|Z%OrhmN"
    "VUSq_QBHhpP_Y)f64ADP1K?>_|6@gSNc=e`TWTBUWFpN>O*ytA^j~1u<R-jO)dbDOLv)Wn^UIf$0XrNkYMz="
    "^_(1xLCZlWY=rx;em-j1-oA_UkrOouP4;{A(ivT<1vOxom{1}-?(0I9mP8D4LQqmH-`r&M<*@4X|;MuuE|;Z"
    "+Kj^sKg3EOvPvbdoU)Z>AI)pEmF&Nqp1%E!5t3Kmp6kAT2DCU`{0Y1QW)ZQCM{Bya7u9t~XxCa?q4q7w(54-"
    "?gP)eS$VB2pR}c3mmJVR-I=XGRN7ua9tY}W?h&+qujb>Ya=zdbM4*b~`5l08U00Tfeb*h<362)?!A~t9R+#V"
    "HY@;4J4Af)f(X;xhE0oCLDcGl~78v9p|E)s#W1^e_r^QkL58(ZUfVeOMmVhn&y=ffldFcnUwS3})ev0qB0nc"
    "g-^r0}BtwXT-i){l<W#0?dx1auTl2P^d8Sle7lX~A_E#ceAV<V&kJRfYB{#b(*JsxSqf7-sl~um8G<r&}vOR"
    "BW5!8qx}`;>nD3&&Xx5s31TfWQvonCx(+mZPhEyl&nl%B-yg@RjUA*(hU~2T5_=CnIa$!;TF-g004!^3-Atb"
    "><n#WenW_(DO^}_tO!u-9F6NkH!XY-X_bmzwi>uu_*{R=i3mgTit(`6?~eXI;DD$!W1X(mQ`Usg+O$fD_>zo"
    "AnWh5`y;|T_%pLD_E1)_u8zb3W;z9Hc+L-eWtAzWR6f@4}tHTG8i|K2^-7pZYZ}+X`(8t#P;v{@%4!1<LwwJ"
    "9X9&gVpxBrh<M}H399sQr*U%kua99<F<*MiC;R7cU0Smqz4a|Cs^-O$dg98X1rDIwYku)%^>Q*y0gmmlOs;4"
    "}Jx;&Xy0g$KOxq1#42PA42BKg2$BFT$r#DjM=TV}?(81Jl@6#D=~=bZ>3hUi<fJR)_CYpOjN_z2?gKauAOJc"
    "o5f2(XaYR(^hKHH-yxz07Vb?Xh=MA8w}u*iMDvz09o{JtBDht#UY^fO^xF+uBm|jKCBgYZZWID^+i=s<+>CR"
    "^G-n%e8K3rxhuR7&vNG|w<D*g0}UGDm$eE**mp&@N0Son*?@u#<ia~{Ou2+);w0Jy6HVx@u1TQI2Ar!l2D+e"
    "b)jE6ilXMrTZZ^1^K)Ua(+^aQhak&_=0hcr#SDEByM9p+k07Fn<UqU8+7zpE->(o&d#afZR+SygOxwA_}GWm"
    "85Zx=BTxn}z+{wP`1NfW|<SLssnKIDeF0KyrMe4ta5;!i@3WTjgqD+hT2Lq;NB@d<TLc`JHlsfncmp`jX><x"
    "ZqZ^2W|Q^ph@q_bZ6yTc%k47Fj^7M-~xY3@(@OFVYs^S`==HblP=bxg^U5r{<nahT-UaQ5yeVg>R48%yo7KS"
    "%nB(DmT+dgKQekva6ILU&0k#t?A*0NxB!>0gt2I2lQ}#mpEI_L331gsKBCBKID@>0DhXYjAE?#NF@Og28q48"
    "LhbOCj)Mv8=@Mqd40-U^63Fu6b{$8rdq|<>A6xfa>;7X@ASmVr9dl90ZZpHB`V#(9n;_SBa(P$*f0eh&LLYQ"
    "NR5MC@+RTx`_k2EU)-+ML#nP<nY?5EqD%xhcqUVI`{;~axxHG%dH9g7!R{<|w_Xd_Zp_Cc6(=iF*YR^$Ff!|"
    "2(UD{$L%O0OU`GgJcHa<zWcNWX*P*1#fL^f4ibFpuK?inL;gmneQS3jBwYMcZcc^mlhd@562-HkLX@5$W4)!"
    "mt`%lkxej?x9K?9VtY^-<A}#OS#Y2kMwKL_RU70$I8YmZ8F&>Wc+5@c+8?sf=_qZJJ73GEGILb!<MBm#tCY+"
    "~Y;IDF;kdb2<6^3w3L%KGIyvfZ0s^+F?A)Ki4N9G!c(@fQJnvBc>>_Mzj2Di+`=0<T#EaWReD^hn7&rXNbw3"
    "4d+Qb-so1=3u1^v4w=6HHI8ROnJ8ui=mc?O*WvqE(to5GYQD1=3CjpIQ`1pG6*?+M$wq*;d5mN6DBmFXi~zf"
    "4Dv5G9d6CD-bLB@eyz0u^<-^>q_OTRFC2W$Je;(24`4e(xGwz~!&Am3Zh8u*Ib94=}f^d$7k>t`aE+eEQp3D"
    "lKwELHwuBWg5IB*Qa&EjG<s~4kC$qJUl=y(`L6k1(tjhoeLEbJt7UZtojw6_^xblXJtt<HtI-rPagV`nXRPF"
    "~K@Jp({mNhrl~Vb1Id?w2IK#DT^&Ee}4fm~5-^Ah+rrB;DK<H`M6;GELVw&aE|%6MOfiBldu<_Rk9W6g2K7D"
    "c9}DWSF?1ZvSDfT}um{eMdr9x*!_P1Ej~VUmv|3{B&^mt8ZCH;hfxXMZ$#%%b~MEs?ezi0JiJiWU>~Bwi6f5"
    "QGXwS^Ph?^YC9L1XireT;zA9quB<xzifaTKUb0f@PjkA!ObDN0cwI_V&s02~xT1T*Jq(xiP?c!=?BQtkxV{O"
    "|F^##CY0F?eKXoZ<4s%0rDXFSi8r|=u7*cl4+Ud`t7xieziZXwSXs$NBT97q~>)%WQaCe6*unToxyoo2L2d`"
    "D`7S%*+!8{I6=!|o@lq?oJRUN*XYdJZ9)g7@osk27L+-Q&~yv}AXx`kd6aN)_2(I`b;E;rcl0gBnkSTozXGA"
    "=zHG=QElYE>9WR#>b|bE8CD?d_)g8!wuc-qkB6Iy^IUS5VL9zTd)WU#u*_2fb8UnK<=Z!OUcv((YC>2BLFS9"
    "0htg7FmOPx>+fWhT~@C=L8CBV8fM1E{Rt2PZBCYOAp(ZlXM8*{h(5pHk($j%yHMv*k7_H(G;@B?E7RI^`Djr"
    "d`~TwwJbY{RaJ$i*AI3){DOWjW^yGD1*E>2YNL<t$fa6E7dF3J8!DU#)32e;xeroMBYj=ekekYghaFj1F<Z_"
    "*z|%~2!Dqlwv$nHpJYdZIwrN#3;OuH6O)MyVPdFc43ED^JRn93pLI{{la;t)h#y65*6%7n!QTG4&boZ{N{K3"
    "NVQNsxUIIAC{52MGImMfv)idR$AUa7jnGUG#FSCFXktd$C$dQiHXzm}=~TTQD)LE-Bpz^4Om6%yf#kEfA#;@"
    "-LNDa}m7Og^jVBWCynKIp^Qrs55(tgQO=mRvnteBs+|^{p62-S;~e&GoX%b8GR+3zLO9g@*5FOzIy_r*K<Fe"
    "&&09##@+fiiy=-dsuC|K`C>Mo5wkOv*mc4d<68>R>klvy))bB1C)g4aa4%8;V_P9bqT>@DM6Y-NkKnj)rEfl"
    "9#B2nQa+u{ud4o?BvK{~ndHWk6q2JD@UnkJ#i9q@5=B^Dp1v4@fy}%GP))OVP(T0E0%-GW3YlA)C0VLJxA;q"
    "rtiGl>rzE6U?A-<0E@l6Gp`-T-9L?S@TN0_$(uInMU(17@@=#F>U91xiiu1WdWigouhwxvvCZbH?a3I}Q0RL"
    "~Nn2xj2?UcWQ=bJ6e+)#YCjo-j)-*=lG=yS8fUs|t=POSpTL~#g=g=RG{+N%(!$*b-2KPB0AbJ+;@gt)T&Nu"
    "Hckh2}Jjo%1mH2ja)WGgSH4ZrQDm7%(%V8J-B!y#Z&Z#-osUP-4`2ZfN%~M$-`4I7aBQO6k|k9wfh>LJEcAb"
    ")h6Wwd3FTF&7r4LF}mbw{xtxCMDg7Nh9M#v97mUN=8@N*y^~I{OH)AU7Z8m?p9TWRNRPI$>!v$DFd|hl=|uq"
    ";4Lzk7i#l}osi_Sd-an$ev$D+%~O`5)@fZ#mu<~#O)H-)!vC_?0d1C9yNcW4Z|C2m)m9;?`|t;b()mh0D9^@"
    "P38PCYAt-Gj;^TBY)}_)5;4f^U(3b{ZS5)w}h5Q%3(5#~88>?c8kxadqf1h&j_ks__r<8%e6?~|ZdtW90ez@"
    "%WP6A2MTdXeMU6G5wRzCjw<m4CIF(T1YD`iz;ej6=Sbbvt8ta#5L;cMYbC@RVITV;8bSLE!ko!q}F!GA5>RL"
    "ZIEtYp;7WQElXe6jwwO838#iFdGo>d8z}+H6)@4m@SjU=!FxAX*Qm*{U!&iN0mZ{c4$DwZUSY?8-JXTAI+je"
    "sRy0YQuuD<K6FX-n>H8vXTOrrUj)3A=2!sT-Y~wMV69pW;2B*fA&U}EwFqSi<icq_?>y)oM82YH;kaQTwx99"
    "3hiStgv_IdG_wgC>}<&`<t7II)hyF8nA!wYzsM_g`|fv*wDamSC-J<`5GSIGVG9wly1XDr{T*46i|63?(_fC"
    "?y*mBp;N<l9Z5fJLZSh<e?!Oo!seK3ZJvcmgb9jWt{xz(pUtv>Lr-FBrL{++Kkw9&3U+ZD^uk$VK*+U`G^?|"
    "4inO5vYo@vQ2XsFBunbyQA>j&T9UImIQkzMYQk;}$U5;;~h6|WdeB34M@A-TL*kwT_FRl>d4$kMG~TT~9!8w"
    "(Hpl2SMgmXfxO)237qU?<Q0W~INQA&sV)nS_74%zv@o#8vp%iV(E2ZcP2H&jwJg$6dKS3RHR}<sMcnR6{v2v"
    "~<j@?V|jG1P`qJBW)9I=L-oy%y|T^k<-!>aMh{a@&l!eeg%`S8v9BStiuabE7Q1~Q{-ltB+Z$%IKMKhm?lZ7"
    "n(8QIx=lk9Wvk*k?XEvZk||(xcRW6Hp9_8-AiG=TmAk&~`~kR(N}^ECO?dRdM+^kPa!SITR2-1daHEsjP&Hg"
    "em+|7kfXb&Gb{^IQH@_md@2Y{Fb_NRUyJb+kD#4O8PbrmlbZc)b)FRHB><5`Y^1>?D>4qCnyZ|^zp;)&t_l}"
    "L4{pBW+t?w_tVrH>bdmT=(ue!_dTwh}dV-<=(Yp065@C|}GtigQpqgi6mSF_Q(5k~j+hSaLsn>$eD3mBo9nQ"
    "6x&$k~B_@?~o0A%}yiU*Ol*BM;{D6H;cu@6;~%HBycdo3^g2nt>czK90<tN)#rOTb2Ehvo`jhB9bh1T`Q*iq"
    "Z6aqvbhiKotwK9V41&paH3VVx#o(D-S~S4jydpc$=^FwRR(>utXq{f@AKCcPT~w$2Fxj8ETGxyG=H>S`WAz&"
    "0v{uK{$%yZ|BvVB>+DCTlAa#}!pyEhB<Vxo9;pEKh)$1_DH4Cnl_21f64SfeG6jl2WQk@)j$6YSj&Hfjl<%a"
    "z)kbIdE?K~-U>J22j}nSd2#f?oW8gmse<SXp)I;OsBW3BBjFuCra#rF>S<fL*e5+J72IcgGE;C(Tk8*?Rs&t"
    "BMYGI3YZGXZYZ}PyMo+?=sgy>#~aDm8slEMlD<)aydmm!8<$j+E~)?rH!d#;(XfJ&3+9)(=4@k@IZGPn&?i6"
    "+N~PkDgCMRH2CN==G^bfEn8xEsS=?_r!8Tda)FQ;$AK@gc|OPiHuAs1dpe30<oB9mxmq70IBh+!palCL`@=h"
    ";GZv8Rq>8Czvq>?kp~*1x$akAjR&Ns#|0yPefNMry81By`F_yoq>&WG4y4h+I6b+ni2VKzib!9Eo|t*<AGhU"
    "w0D1hEGg}XvW(4n7g^8}*Ddy>OoYEKUJ~L{)y#G6^rkOrX~y0#k{zl=Tv?!M*LZ`LOj!&etZj;RsvDof4KmL"
    "0G|8^S-Pxn8xB?D6?>LtnRJW_71HHw%B&>!B@%*Rmco=7~z!d>Xj~9L3*)|Wbxb<|e(+J(G%By_sWj$T7UN6"
    "L__Fbv&m8DA(#BxWPe7{tRBuYJ)&inZ}N+E3irxi$jZ$~8VZgy%J=fvw%okL!F*MU$KX3)}!$@>~&QRO(F>a"
    "YSwmfv*~5h$|R7Zk^`oVu*imG8QmUk{LiLKjXnk$PR8{;7^rfiW-Dq2E8~XQ0DJ<Sy`~oP>BP0pjeNIr{!l#"
    "o8dR@agw2)BAvWt40(4A>ldre}Ych+1v9dh0BdA0=w!?nIU@`8d`z{9q4TO;(ZT~-g=@9T@NN6RD7CgP(9T7"
    "6QEcLaw!`JlAE*qg1EUY5S?L8?d-}~i85rccBI6W8q@hBx?0S`n_)aBSHt`ogkyL+O;uKZw{%A<*lvEtrWeM"
    "3@J)9&M@BSvCcI$>??4?v(f2GTs-E~?+gp<i+kw0_U=`jJG(gDwR9(qj-%#v~Tp)2Ye?%g2SQLMW3Q;MZirT"
    "DVq=9_mP(??dR^r{@M>f<IcRP^yrH0x=gQm%8`0-G+rt2Z_5CHjx9D-3kBNuseGLABg^zeG1?tR9Y#~;%7O1"
    "*WTVMN|xj>Zvw2o}_xTn8(uasnXY=KY@u9-1vO<tD!As4yp?F$?|#pAAq(oN#er??Bjyk_L!+j}3<w;imEtt"
    "Q3^XPy}e{MpsA=xz>{Dq-}rjw?KQc&#rE>1jT5pLKJeRSgIGr24t$!F)11Z@}gWJ+4j!FT#(<N)mbG~Gt<lL"
    "1<#cq-TVWWI`7=I$~rL$HM!k%H`nOLBoT#<R`zq}-3Y<XNt~7LgpgAjF{gJu!g)NZh}3LYGfD29*WFW*r9zL"
    "o6qVCuu_OOtSVE=DKYBTGt!ON5ec!QkVupRa)499zMX?+4MmSbkE+#EytcYE&gYHE$VxbD?2WQ?ne-iu<>~6"
    "1zJHDo?y4DU6XC2(cl%})9ZT%k9HIFGP+of7Uk$)np^AfyZT9GLy#*x=03U0y@MEen8R|VU?W{RZvokC!|89"
    "JJ17~S0MbgFMdIkWhgyLD!*spM!%sCqI&s#i&Jlc?plo@=68=0~DY6mXzNuU}#Pu$SILF_90JOM3J3t9QS7+"
    "B!SR%J9CcQ$$#811SMU!L!+RsRJpfq!Z#`s)d1mXjM9>v!7>@96G1GC>qNXsf4T_P2)JC%hWWJL(||!87N=Y"
    "01m7JBGp0Fzpo%95T5O_chCLbUDQE;qSB$I0EmnU<!x=Yf-=5`bDpYv4aE$Ig8q(Az7+05^SoB*$Fmgu>(eD"
    "X%&S=Y#3<X%f+WKYg+5(B3#FF}tHa<b9A?({Mz07&yN@bOEFA+~lj2@R)Y|&AqW+>*vYFNDA?(@GF?mvBibY"
    "24Qp46qqq2G)Uz4lawA6DC->;H_Duj|vZ|t_8uAzO6g<r+pdCAoTZKUeh2f(T^rLOoyapeQDhYfOq*DYyI3B"
    ")Gw!ROOPZYKm{U~%w%;;sn9AV;LVVB6bx3=6v&u-{-W*M9h#x?o?;60kCFu$&4%RkFJVmGXNhCgWVoQXPDhD"
    "-wKVL{~=D=T=f6kMm-+3?2F=$(h9@$cY^q&ezY#I@@{Po|T1J`G-5Nu-$4L=^BnWFTw1#O$7%jVa8%!JtIP#"
    "PB&VBUNgS{?&5;;4XFeJx++i4Q^wLTu+f@z<EF>f#^0kE5WdvbKm$X|wmr+{A2{hN(u0^1dKX?v2x;~V0O(m"
    "8#ODvshRO7qwi0fT^-S-xT?+%fr=aioqMuGTq$UohET`FV5gEx_ak5BfC-JDi-^p9pWh+jUWk6|_UgT-QbE7"
    "6H4V9;RBqcnQXS#vw+@cuAK(a9))Kp)Q2Z2r71@YPamLW%HjA?$=Uz3Y~vKu4yS4s?kx*QYQxx)-6c`s(Y@V"
    "70XRn^Yffp^S)V6L!_WS2$H4rc>R#CxH=s`H9fg@yhh<{;QjM8U8+Lpd(i-;z}pu(x-8UexVhp)swW5r=E9S"
    "WmYmk~haafAT_@8PZO1t{C<+Q%Js~$098#IR~zz5d~O(G`F~Ax^6T`*X&J$)_9CXHV~sOe)fRLw06DDFS|V~"
    "RE^U81ZRkDEx=^LMZ9HXXsYS-9YP4eJ%v97TgBPumd`X2ZaJPYfSy1kD07tgZ_Li6?m8#Ka{XA=P0;l!&o05"
    "9+_m}<h@D;zRFyP2C+B&s&Pd=v+zQx;G{EYlM&Yy-+@L^SuO9`0s)(rkJ|uawuD_0|sKUj=%YAIVu7?o*7bp"
    "Q-KKcAL7W>T}#{Fl3M?Vj*2gs97u@)bHCi-3gubA{j<PG%p`1Py9f7WyF>27YJcTX!YLbCc>n2P6odicw$*D"
    "nW0Z~n+t)9>TkUcfqwsZKEw-?sQ!RiX(@E)m~;W_k${!~c2u%kdlT0eJAcoGC`5C$Q~{WWp?DOIL_~p4Tq5b"
    "JW<`2&B32k`%=3iQ`v&*hM>O#D>2TXGsu1M^#@d^D2<6hltD#`wMkK6_TBDwLgc*Ul0zvU%_0OhUjP-Xs7uX"
    "uu?D-lUEp!!tJav-=uHin|G?L-DeD2SUpJ|<YP<jIG8T<dYLV>ucx4!5deASZUmQ7_$gIYxy15E*^^*5H>B2"
    "rT~}x@z#`s*0nON)Af>ij&M<c~70tYGUS;f9hR==lqw-NzC|X=$!d|@dPN`RZ#jL?)y!f35(aeFPIWQ;UnM0"
    "e4eKcsCLYW`9c2c2ez~$u0Rabr6H13f!YglnHfMu128mq?ltomi2OwNoaD1&&jqUf2hX=v&S_UX0QjJOXP6|"
    "a7h4TkALOYe7uZ2o{97yeJNL@VnFfWP}da#rzkA|=p>7Ms6R4e#7+lI&%fyF8j3ra4B9de(4zEc5GQ=w;T83"
    "ePSk{mp7OKc!;h9t#mnz!%SeKF2w=D5?@o7eK@F%_iQ4=cfvn#5hE;VK7PZ38!iTMSbY+Z+?Aq{O22`c_a_I"
    "+Zs-UT2CiFclQei^eQ(o?>?d=qtX*W!Um<KX)ms4y3i=MEJ>UA3DFxa2ceDsYH@um@#}-f#!lO2FTF3?DOU}"
    "qN`-kRXJwQ!=+I`TnhHrsB8U~JPN(`rXzUmHfrVy#FvBFt*@EI7-%rz<DH05z0<l#IdNfJo+Wer+E)Fs=auE"
    "UNY#i*Flluu4xN*%)fx|C}7nJ%lABw)&zzJ|}cuDDGik3vk-AqR#5VwF}3^;3t`_`8mNnZjpXb}@OX|5_4JJ"
    "sgE<(AE{RbXm^w2nz}z-y?__H*@_AropBXj_Hm4rDlZ>%fACbMV$d;C%&EpXce#bB5b+9bXT{;A$FjR1IhTb"
    ";M=#RFh{MJ1T{hKCf$Cs*gIBGRTQ1v76vR)%{FMQCY<ZO*XnI3nC*;8q(1pFWr=k8?L()k(mqtCt6Noud&Ii"
    "DbF2>eQ#yXzE@?YG*9DkGS2{zmvKMx8aPmc3ykq(pn3h>?SdV`bx)R+MvB5N65!nnfMoc4=`YCi)YTdk{Uw="
    "i9TV7?_;EM)uEC{a%>0C;#6Am)4R6@<W=Zx^?!QPle|mj<_-oOPG)KKupPmhzx)0H@HQf+xI$?JWMSJFFEks"
    "7CXA&KfQ+m$gyXF#jZ!+seh*9iqx6-KF`T`%4zZps6T(xU)CGPmlSMTrdudvn|5J|}{@GORSqJ~Tl+&M4?O^"
    ";KguSUXs@U`ipSUn5ht*CI2c^D9@uBuZCS0%19xq@ZII+5*sb1Fq_@PrT$Nwo4D1r?HbzvT4GZY)O8;m{XYL"
    "|Qi?5A-)@@TC}?oM6DuDy$Yx5qYuKD%)A)kr$uAqz6>loN7RAHhb%)&eJDcl^m)fIgbY@${Q>Gr0>K+db7fq"
    "VoF83S`b+BeT{NYRp{FTqh=i#k5_?Nd52t)O#d953?>P<=&^ekv}pQM$co3(3jeVmO8v&_xXXQlx%9+gic1+"
    "H4Uk*XQd7|DRjS3iQa?e*f4I9-;+s%(?d^7Jy7-}jhiB|kt#=1MBO)+1FP}NFYgr-N-?!qjQj9lJxiI=w8K%"
    "9rHYe*v1Kv6bX12S&D^-$ZX4iMl{)_5q$QgE2gB5I~A-8<te8wW^mc1-Wzoi9zSG-qC+K_x)r76h-D$3`pgz"
    "WW`DPR0Y^BI?k=_N2wpWEyJaH8b>v4thOpGlBu@Ci}K(<FL&aVLMXlN<c@hWsK@k!}RH#M9+9*?t=<vCQYOl"
    "bc_R9l(KYOG3ld9kxh1o~IM|VsgusK5G)xnptqokXhNsLby#)Y~~t4-(ouRja*TDzl`SCMXnzz>qHvpu=y49"
    "DeXwMU#JC{4=yVD5*L$|ot5?TU11s0;Ff8fS+VOtW^M|dgxA9;>~SC3pAUEd0bfsk^s>kdvxAoU+?ObE(;sa"
    "b*(s2@!}1Ks-wIFE_1$_D?V<rYw>0>l_Q|V%{0fMo>22@Zr>$mb+$wxw=at^D2U&UECR_A(eFA5><>7+zL3V"
    "b^PTO>1;gDXf`el?{(}$fEbFK=hi0+H>noR*pV(6*&+Dfp$1*e!2iM2-oYC|$kl7wo;+!}_oEe?UTo5nY}C8"
    "k}l%Fb^G;W~*eH1LHV!eoLdf4~-$8a67uQpHWLlelsffb{ihzBo7#l5GhN<)p*Jb9!$`w^JG>#veJ!*Hyo(O"
    "40HxYEGH!IraVDm!wLTA?ec<8IpZ%Y9vT5PrjhZo*0aERH(c+(=m_(Q1wmwY6Gb&U7>?wubi4%xoWTbV#v|w"
    "5*&Upz;eR`*EZd$4$aBUy^8xZ=~ABA(XbJhM&yLW)W%BBl4trs6ld6&nUl{KP^Ma8jR&22wSwcGQIePs(7#p"
    "1LeeS~5zgfY&wKK^H<NgmNC_m#P%x&m3AK{*;N{%ybXG8Ml40F-zbv&n>9pb6U0m`g8*!5od2U2q!jrq|?lN"
    "%(EKi%R3Ur&X*`={P%ELcz+9{8-9S~Z}2G`^;x-zWBH+`ACatUV?Vdt6WSVQzW)eTCbI5Q`PGjk(2vts;a#v"
    "r10lVeE#W8s_b_9(JAAX<`XFZW2cqU(a?G@?+0zGEF^l7@*{kj#0<BwI58M!O@SBDymUD8aX#!poAbwp9><o"
    "%O8hTa{d?EQ3TgO4;SB6!RV!Uh@%b()=2e>MW8`FkEKI6yuYCsJ%c6hLx);-RE0DS<?LTCyLuV6(`<+>U-c8"
    "w}CbVNXmlQ6}j+&Ff`F2tLUX1EN93HaaQQI7w7w<<HF@+K@LM_Wz({~I!i@u9dsUOr@hj)%c*3T`8Rrvu51p"
    "h*My>k#M>bd7l}Bk`bZsvX4Zj=&niBUqf&CylbXr^zn_c|6p3mxgH|-__putSqMH>URi63)WNz|HEXai=D4B"
    "0>Ptbzjbt9ZExx~!C@E76$T>R7t$@TATK_``m>-u;TBY?LW>E||RUO{{DapBa5Ryd(q_N77(%I~ej6Hhg3ky"
    "3Svstc-Tb$(v-(&5M;H8MGV_AzG0+swD=uROsx00hG0wFn#nDUiVspzw@%_C+sBQX=P<RI%WJMCY@b1O3HuG"
    "b)VU{vcK)c`8^FjnzD#mX^Pol_fc96y005euvmSD{FX|ZR*tYS{Y$WaZo6$s+g$ufp`?Yr8kWz=F5Zu^MgT@"
    "j^I9+pSHs&8YnNshNYVg&^5XLHcz}(_C>CWt<m+$M#AK*YDNBzzFDFdKdQ?4L;43lHRC<-XPeh)g%6|awDGR"
    "R4RdvZekXs@R0|I6UoQ4}|BJ*vs}12THTpE3wy)nqx0Ecs-%0ndVh&F`V<mDxQyQf2`{V#`ChZPy8)ip(-34"
    "D#@us%3Yph$C9c2BAitK7aPDyspR6aLGGLDvTv(x#rIqJ5q<BdE-JKOlsCFK94_k<WkWC^e0>+lbBRAwJ*PJ"
    "v*%SBv#ty`fCHhk!(w1fM_I-;9P^(e~DEG}_%C?(FVw$MI;m6-Hq^jGk}q?RCaG`<pu*-GwnFgCEm8D@83}F"
    "sGep0UfUwS3IP%=m}unX*>rg>ueIJ8Xx5p{QSvQ_jxzk-0SS`?e2{CL-=#p+1ws=##_%vJL7PFXSlT&KHuEm"
    "+VAcTpYM&HKi}$h_n*f*yIZ5qP8?eubDazB*udQcb4m^m{-+<XxYV=0B^77kQvzYTA(zL3bJ?{vVxA6VWFzv"
    "l#lFui4YnM3(9#j66;Yz=2IZ|ERGNp7uFNP-x?cHA^3k-U9PG+(MLVRzDXl=imMCSQH!(Ite;Eib!}KFM1lP"
    "Fj=W^fa1U4u?!3I8TVowV$cukjFx^3e%#+SBBAvXo=dhU1?s;(?&Zl=GKNRHh?&TT8~Ig%p<a{XPMhZ<j~z^"
    "-#c)kqet-Z{h5<s=<~h(#n)<7I5lPXIuXFaW2+4GH_3{`*F{pmTxDo^pexLDin+zuqZ{RxQ^w4A}*LRF{f7F"
    "g~#Ih?~i|nNa#ubMrr{i&bg3&(}`5eO?Hjag7kdEJ#LeoUa)q<zzmyw$93ahLUha7_0H28_SA%^QJfd_K&+A"
    "wKEcVl1~lU|MTf}F~9<cSb>h^&~(<2>ofXj32e_`k*1Rje_k~B@yRd8Z|S$rWya5Sc7JM%Nz4#N=jrrvLu)<"
    "H^NeQjXEX;iE4r(5C#@MiKySZuB&ojZg#R`B?d@T3(fO2R87p#052aHIp0ljU2^Qc-N*C#Zd&LzG_@&v9yC+"
    "Pcd2fxK;7JVf>5QIP1OjO(>IVjSF~y!8edx>$UXPK^s3v#b&gQW3(;8hZjD&k;PppAJ0`(feFc3>ghR)&fhj"
    "_ZNSPlc~Ex5Ugr@Figy1qfHEcw_DPOf4sY(+W5nK?(yl)+ON6xh&UaTPAOleW7hlW?lT#^7*?%fX23Bw|&6w"
    "!o+@UI-SLp`eLN7=dQjCX=YG0MitmI5rf?&`3&=(=?Ck@VyvLwW@5soWw!y%JPEr=pRs}mn`Ih;f8egb~+ne"
    "!HE{rB7_@irI)=p(v*!A^KeKBnexdkQjl6da22x!ZY(m%?cgm)=gA27IvHIBlkk=VXiNr^u~9dfB8wax1aOl"
    "lI8Uq$gIQ~F%g{A{Dh#o?KHdphR2<o}<lN%M5n!bt6}|oTc5#)OQEeD02Zx%3lNUMn9Gv{0*FX`ef+6hPGzG"
    "pT(UI5lK*jx|{~~D(MKJ&;!<qsu+AFy9GniXzGMHOc3})N~j&f@|8jpcv9EZcby>R?|Z!_NRJRis1Fpi(^cA"
    "|I`#rwc`?rwE}9UblilR55ehMnizol*u9U^>lEW%^@ZT&~+b7tS&!)BL>SXD~On9~sO?2J?}@d}J{HqYP$$E"
    "%tKDU@y&-9}0qsc{e!ihLLr{O}oL|CI!<_z&G=o2BfofMe($KZjbZDR5#q3C(&rO_$B4(%^BS)?$_5e=ZK|0"
    "u_JMlmPFw2D@n0KJ^CxgR&cR^RA<1Mq6Zprrt>zdfm$@EQJ$M$nguB}V{10ZAJBU@!#Owdl{)-lys#(9`i`B"
    "3!>)_owO*S0L$vX?<CjOT2R|RYvPvJX!%=%C)cK+lav1a6-!HH1D!E~hQAJ~i1nq_kBwv^?AWNlKIXso*i5Y"
    "a1z7NLpI9|bvBWEpLi6LgL`Aw|9D@lf+mD(EMiqlz!tnI(!d5XMwLS~e_Y+0b#8)2Q1o&S(xO**#KP&EeN(J"
    "3hdV8sMwi6NVl$kmZoNStH^v;A&44Q|urJit^ARDSoC(1ftYH!1I-^aLA49C*l{lpFXg$k9q0de8+a#h#A$M"
    "Hz`HC)Z7kQcA`fm3_A?_O_SB&gP?M4x9C?kkYJ**?zwLJl+XM;dp;*cXx#UZ@jy|AMHk)d;6WRyS2L=jyv7%"
    "*4A!k|M|{%Z*zCN{d^qmZf@>$pO3cpOPOuNOm@oW{~a8>d5Oma!d1UZ)biZ1vr5xevsK1~d%9hxCxy`VJCBU"
    "|BcuMvs6R65|4BxD#pP4^cyt0#P7l*Ee48>-3Fm2JtR<3CRh4Q}4@_V(_~2*VT*JIhcX`=6x5G`{VS1DGo#Z"
    "oS$K|{<re4lJ9PloRYB-$UHs-{xbE+ET*86>Dh3rdA-hS*$b<RmjlK6vkbN1<dZ+`Zky^h~=<^*_-ct)>C4?"
    "w@zc1sh#v-`jJVk~#rMtqJQx}wjT3Tg4H%X04^CXmA=vx!p#UP*eyg|aEylGs#ypDi)F7aDdAh+e_^9_n;Qk"
    "||s?&&*bs*_+`+h(E-`#$?Wz<q_x+^2*8L1zfv1apyeI8}c~kaGfZP*}sUjvK%2AqV5++SAZo!E|*CZ7Ut?`"
    "m3gAPP=F@WAu+@h&+~}3i`2}^j8eXENRzNG?cf!oi(64S!#=|JfX%UWlBE+04<^+!v8*8#8~;AJ+nw)>yG0{"
    "PjO+s}vaL)m&32N(e&P!eVw$BM3(x_Y6-pcx_IDrI(?|C7kv)B6Pro1b6w`&q1Hy<cmhv%Qul!aS)q&IN({*"
    "^p&I5=(7wI)QB;ZTapZckGLcrt)0%7p~&!->Q*N)zG^;6&lfN`Ni&FIx3*;XYp?*xdWYN-%*|BOM7rz#%q$V"
    "gJFr*h5Js_^(`_{?6MVrPv>w)DhW$a^fIZJ*;~1Nx-*$+@gOqy={^nHTDsfeGk4M{KlbMpJ3I`YNBMk7NG{G"
    "sp$P%?ep^do~K!>CXKeIS{Bxa+zR+v0{P-RF7r4&~6~KME#nO3Lq3USxPSn&uGs4)rF}WSAYVYsZYKbTV1u9"
    "&ta`s^jnj?2GoVF4aA;BXfq-GE8M>&Y)r76>R@loBO4AAASnr|Jb{J04sW%3d2*|HaJ;E-een}YGg(8+%%G0"
    "!HhU^uVcAdM?yz+-N*2&NRtiy-eFa9_!4Yi$&gnL1sEMfM<)VA+6hZzFw2=x;<X>>HENYV1Xk-;J0&NuoeiS"
    "9leUH*vLLvrG7Sw>#l_q_23WADS;q+4Jn&ox}a#>k3jk@+*<y=GlPq{~knsvtPHlP}nM*cFv3N{?%|DAH?yR"
    "|uUx0*y1W4^n$7w>FtZtw5xZ*KwHy}h~fe6+bAZpWjo(N1@3zcYkKJNv_UINpyohuiVaR{XrP9e2Y0t^Igh%"
    "9tbcW4`t_+#Vw7l%gFO3GxEZ(LE7^66PE`p(?0;Cy%X1=KPU4e`L-dne%UsIWH^dLp6MSbxf>6CbURuGf&fN"
    "Vabb?N2KtG)Ey~Q1UaK6=jA$(lk0Z6rf!&?F;6?^f%undjTrV^7v{i6sxrs9RO2Z7L}7bkL@(#*lAKBSL(Ny"
    "ZZ1LS4!a@>deU-1y%mdvjWB@7Uj%mOFyg@%!8VaL%p<~uO0~1HNdDM08t%P+unUsx|=>pmi{lyq%dtn9t3Tt"
    "8b_C8E=VT^9&7~Rzz^!fR6v(w!NmYAqt7@=Dauyq23%%p`mrzC9L6-D3^ldyrnCbu1{O;46loYi2PX)TzFEu"
    "Mf_Nc!<%EUY2cJjsHL;(Y_ft^}`M0#E%HJ1{8auJ~H;Oc1h}2S=?ow9|3_JQ#Mc%$68z3#e-h%)krQJ+o3-d"
    "t95P`vCDR82FUGH2cBe8~|88#6}V;^fJLZ95p<tF_mJ#msfaddO}VbOZ>f{z}bjVD=cR@Wi>Y02r}l{kwZpV"
    "7}@vR7nqCZigozxc0P<%wa)LBv);Rh&YQ%x3ch-{wX+{@ZN>XLak#y=Gu+<a+~3+6?`?05qP=K0-r3*W+5~?"
    "3`A%nVG}<0^_Mdll!(n%4Z*y;FGcH$nqb+B^H6JKf&w2icMEKyx0JY(>8Eo^9LAM$Fpxe2%6j;Mj!g|*jr+&"
    "W*mu>ELA6fQCmi>`se`MLeVST!JaaCm)L_(;Qo$4|=qT_YlILdXtd8r#rL0>3r)1_Inb7cPv`Bf=C)0(C?{q"
    "EL&v+3q!-fmu$vcQyOcSd>b*ulHUUAOd0`u#=N-<C@)R*#^`jWfc((qZ;B8Ekvo-26&iE3r+d>R0~5E^KXVe"
    "Hrt-ia}pzj+MXa&2hV$!9NIyMZN)PAsEeL@`cbI)tmx~isvB53w&!B1?iZaqq)@8g5Q#5DqCKoCx|67Xtx#R"
    "(Y=D}{|Wh1u}fv7*IqC$K9_{AALR~iciO?RVuv#v1wBGwZX)0?8s|&HKG`ZHG9101q?a$4l~=ASlwXI6aj`S"
    "W1ebW7VDhjasnn0ZB|j48@d(RMRa6iaU=`?e0(@^6eZZxoy1N}5rq@<!B3-vRh-V<MM66Ord1`{M6`~<2<d!"
    "^KSS-Q4hfSH&o@03D_v@4W{2m;<q&=<R;X9-5=y|leAMR`qk!z2)cb@O=JRgt7;m&Tj6~fc*PPDoCe0y&@9z"
    "x4#ySp8254*$t;pT9^(rJY&QE-&Z46}#nC=%qXjkit)Mrja6a^!yp7@IaKoLj0|=J`1GAKCIpw)~MTe`L%5l"
    "We(6q4vOqaiI@}V{0+^m@144NKy+0<wkKR+=lH|;nO_FJtgUaC!B#cc#8=Y$U~H3pn7&&Qk1jPb$=xQ*hs!*"
    "Py`n!bbeolCoT_zr0EO<Bv?t$&su)+(nGb5@bC_4qF3E7$9%hURjwZvb6QME>{S1<r+r^7xMwa4JDss_Do)1"
    "FdQ&M&FOntK%L$x%oGvrD(^w4d<_fkPaS}iu`W*u_0z-z%a=H+;Ipve&qb`brN$V99(tfHum17JMMBj;<VLV"
    "62a%>1Z1=UfL@Wng>TJA3*Kpw=vio(nYm$ic<dWzi0RfueHM$w1N?clnRp{9_`C}pn`#MS7dodws+1-rj6XH"
    "EAYqy4UoawI_{_x+AP0`Aj$NnAEaB?t*L8{Pr-6T!48Q|0%fbCS>(${k#}tPB1IUYSk-K7pPvvB)J!HAsQKS"
    "I&C>`{JxsR@8o8xQJ$B63s&4#B-x`B1NV*%lPTi?w89XYU6*l8<Yrl?Libi+<FX%d}PHRS@B0!{F~O0+m}za"
    "5y4rdK&R~dHL{-=nRK72)Vz4~Vpl9CR~N7FDc5qbhU3ddS!;DwmzHF3r{XROo*zQaumQ8rcUE9e(*|w;Q0W&"
    "cC>;qpzbiNdAR(AG07Wmv?t&FZoYwYS)oQV-H7Wq~7QHcd#VmPaWI`rCB)7)Rd3ANQqMlwY71RGF5$lu*E#)"
    "XkZNu3{_d>ab9vmJXy*)j8DPBTTw<2=ipsp*gv|Vs#)upbw(<TZl=P%TF7Q(yVDHQkap-#jvEKbr9TBPJeSX"
    "PuDEDu^`5)2Cx{l!gWx)|LHoVZBHMpJ7&Urv<t&9val<gC{<rJO(c{mrj$j{kh)RFyCQ^hucwrE(wcYxyZ#)"
    "#k&jN<Y8vqNdBqq)xnYh(h0OE|ytUVS>dCX1n3sIpl6c3(`4zB*RXy1bjTl$m1G*U=r4V&R&>K2g3$}kYu-4"
    "FG=9Uj6cg+K*@D5(@t_p_ME()7R(v>qcIRACDiJimcehF2~#@Zl7AsdlT=G)If<CLTA<%%z?FejO$Y3JNj_*"
    "K=jMb?3}CoH8?Rm>wE=Rw04j7Vk<g=sk#{H58Hhl}#T;RQq~kI6qe@af7<2L>boQbcjEH#RiHcvL=<bMJ#*A"
    "V)$~?!?u0GIw-%wyy81Y3eY#YvR7_l$XHq900eRBnp_An!jLIT8{V%k-ph`AB$gQioh{&M{KWeriABTx(pdl"
    "CXLUB#TVNkxwc*!^;P`Ziy$`hr###Ivgyi!)E~=x1mc47l#kDM!_-J>vLy5!pqE<NzT~2W6M1gxw%3rmjB38"
    "Bn$8&q4*700}|HQLvnm3V=%u2~-l}$VG8#%KF{T_v8pC6>i({EFE28YI?CJ59mRe1P@=aX4WfwZ$H|>9)<5m"
    ";rmhe{$AYEr0z2srE(ad^puDM`2wwWO~d(MuYC;@ij#LBf_m+<-H0kyA-}f42$!Q&NYH_UPOh)xD8Z^sP0sn"
    "J&RxNE2_*df_T|CpQD6tR&(le8a&#K-@FJ(tk5-efeH+nj8wVd`%Q0L>>a49JTv-q@V%q6z$1*6Jsl{+QU>G"
    "|OWYN>o+h{~j_aswNV2yg$%wu~f(R@8CqHeA1h-FDm!%55(Z$PW#luYt5N82Eq$EDz?=ILiS{N<f}O{cu#D!"
    "rCLccu3>{rQF~82>z@bys=Hi4lh5T`<;S&J`yWz%Yc9d<3`)g$G>*bCKG9amstHR{S_87{z-uVW+$WiU<Fa{"
    "7r1*%2?Lo8Nl`CFnMM*L>R+}8D#U*n<=7Ez)L2V59gav?e#cn2M1GBL4XWJrRp@U&|_g~0_2+k>tPg5sO2QA"
    "Lyl23Avw?CXtF09aYN<ZLCQ30O_|}|$&^Ebq|&A^>rsr@p=P{{v8n_YmXfSDhV8gwE1Yc^q;F(H2s4AIhO1%"
    "m8@tf*1SOL|BWNz<Aji&?NR{CfrgcN{NVg)4W@vrH^s&hDeXnN3Znu8)I_6ncIR+|?h@0`|^ZjVNJ=z-Ycel"
    "pf(Re@XV$!JHy-|c=>d&`#!f<D2b8Dx&yWQE}i+A_No1MLJybbNQtK9P_d973`q<z5kBbTZ8G!*39lEtGcx0"
    "KnDKgZP0-lNR%D04i@9FH=`w-?23qGF9Hbo!T;`17E*JQlPn>xL5w@vz)SUjAxrZ1W~nwOKR1PSgI`g<K>F("
    "QW9`Sk2riFP^rUrJ}<}e9q2r&c1vy6H%Fop-l6KkwTKr0f*PS($6=jab|B&!=L4<#aAbc)B*zYZW{}3$@}Jo"
    "CxKKmuS(X>XQRrFsU26f#(>(5cmrBGyO(EXMv<|qczg9Fa0}4{4HLR<0>&}n<~LiuYGGfvSeSoW_Z16Ddt1T"
    "wzm-G9Y8V01UE=RKtUHw4L|Ab;kdA>}&1T4yk*x$}TE%zIw5*8Y0A(LtRW0lw;FBf}Ccwz?3{X2gBYvC`KVg"
    "_aaG9ox@l(~bu2R&mlfE3S9LRffR(}ltroeAKcT6=4P^W4JSh4d-rnvV5G<6tXQE$xmyV2xgML~;#a{a5~;7"
    "{k2|H|qe0bAnURq-zk&tx!1F-s=wOv>ca6Dlc|+bd`-$_j;L#uS6ClE2DYuvBVhaQ~cfS9V>hmw&hX{AMXXU"
    "xLe@5iWlwY54FoD_HyS-f*Wo+#PL>I$N8&<K5kGXKNgf!@d2uv$r$sZf<XG?hJ>W;q&d$^Jr&(bMJYy2mjsP"
    "dOq43?d_Jb_6=el7FQ_Ep{iy>VyJ%9F4(2Me<h##-T3w%z4#uP`bVbzk*WXBGxgP%KF7!E5*{9$9G$>`k}vf"
    "hxZ`*{Mm%@|{0@}}!mxI@MtzLEZH$QWju1p?B!u4)-MfC@3P{muP?@jAp8IN24R?qZCu(irKdlNzRk4bLYhs"
    "V3wik8I$xuV_d%Do+QHk0crOuol1}f#|fHik+9#w(q1X|J;>yMcCkoS#|-xADY^p!vTa=Q4!4*GQCB}?};l{"
    "r^rV_n6U`({)$4%}->rHN-f4ozW{&M<S+I0TUfctA1@AZIMoLo*m^k`WgHmly%BIzcwhU@b9+t4iR?(1e^bi"
    "mIq-UdijfQx$pD9TMhdIFG~knK(9yPJX<cvhtrb`>GlsGm7~xDPJq8Fd+dyzyRH3q`y{Yqo+%v0g@o#<VBN?"
    "dvGg}^RgAg7^ev&GD2IyTNE$U5L|3nYN&-d`#cApIlif(#8=s^XczHzp)jJ<_(p(F5MHB^i!*<PlhIOV`Vtj"
    "9Od2IJTVW4!g4hSpGND#ag-J5D>rkd!no4BsGRZjbT_yq%N@CwH_rLWWR*9fw*x59k0rX;qZY1yMHl%>EN{d"
    "fM*pd<vdyl1tA6flJR{xRJ|8FS~VPi_{8&*WNPgRu5t+2o>sESJ0VK#8vq{c)8KmU<ja#WFtrqQZcY~tyU2I"
    "o#U^~a~{RGj!7FylXddh4q+Vbqk6C>*P<1O{Wsy+&6A_OjsmLe1Pc$5(g4+J&mh6Ax5%!nIlyI<&o;?o})!-"
    "-7$h?hCp+0mmIBl-XFVD=NA^aV@d|!VgP&XBivu5u({QqsSF>FTS)RlW*=`nZ=raF^nSzI5S}5{vJ;y^D4+k"
    "E2gDD%8f3mKV3(<QnRs(aB#!{dQs&n3<`sYVwAmx<Tj5!eJR#U*9De6mIQCa2=d6}&~J{OC(h!E6pO2Qy1cx"
    "SJh|w#l$Yr^c>Btz|E%{GnQaz-)FlH6;|**jS2_sTB$fr7;VXivV}dR~<H;yTNU$k#;W%Hg_7Y3Sxd?|PKUP"
    "(M4vmRP*03qfh3=qCrpIw4`8HoJ|9|%0g{_SwOB4PpIqrELOI3*q;X7`1FNJY6Q#LSwtF}Lzl@loi+19O<k}"
    ">V&zklZ%w~UkowtISJ-LqRpQe<SriHH;D`X1C@N!4R-4d|u@!0a+-)HjyFs9=3IEAS8}FAGLBBM;UC%2uS*2"
    "u2`Q!jX$il2?LIujho)Kzt!LAyyMYlg8H4^?zTz>fs%|Dt&~YUg=fI2hW}Xe|-A%(Rsi3Fnj!Pv-jXh@8QGq"
    "r(1&ugJ+xPS@!5z{;dD>>Eo>T;Ms$R4|-3w9&YtE`%kmSpy$-8R|E>u0qJUtSHyMeVnKe!ACqUz<fosK_GX="
    "GB@YJARUfhF2;X(B@4D7^UF*B9^)K#Lu?$%c;Xd;?T#X5NRU}l0J|YFALG9jV=GbYsm$)~OpE`jxZ{6?CBm&"
    "3KpwiI)Nf5x$g4|Vua`;H~SFePei2~aEW)d~cu95-mPK6R115_?|e0L28(l@u4z4_4{UR+Z<11mLPW-f0ajv"
    "wNLRoWT0jvA$)t`>54l3rd6vBRR&4B9?Otob;Rdl*Gfu10}4WCi9FV@P^F7B>Ke`pa-Q*ySJjY$9S2&5>h<P"
    "+GfSM}QUO%)FpK<9?urG>9J#H@b7AZd;0yYA+uSZNh<@S3n|LDHyjpa4tFrw4q3P9I@ErS49%FQ%r_Uwl+8E"
    "MKDmMiAwx(TIpw^Kr1;>R|P_Zk1`gGF~vc>0y7jk6>RsvuaJ6|64A&YieA1<I(@eJto?NJ;gbiw!Go=K)_!)"
    "rIe55ve*WaaqYMPl_Ot$ZZ?KtVPo88C9`-?2ZExj+r~Uq*_XHYjwri!+b<@hyDFQL~J8gTFwU-sAyKTRl%lc"
    "L3_Vnp@3HQ5%`(48QF5&(QdlQ74>*+%?*<zZawFvn^nq21DkeE%7l+0XtgWIo{maL}P4nKrF*|OFAU2vvk6x"
    "324CV`omFb|Cky&N&K(1@8@p;|iZcWvWs{?n<Yfm<16MVetZTl5P7MshQ%9f5@_p%$F;hX?hWNyy>wV;0@|I"
    "eba=<;a_>HtwabUavs2Q!9dBnCQZzFf;?HjTnv?C^5`qX2Ds=@TkbH)646U@ogw@<`P5n&+{DZlxTY`hGCVn"
    "sOgx6Id>R%lE}x!c1pr&F?TKpx|0pl$Z|xnR<bV$xlF)hFw8DAk++nJ6LcC{$sy*QE3EA-|2Pq3AqB{xcp5@"
    "FB3hH_Jn7Hi-MR_kSuD&k5L_e!ZnP}oMk-O@oDe{VgI@SlBEs*b(i~}<3BVA`3|>%;X8MAN4nNWYu-Lkw@_+"
    ")pM7aTor%SFrBnNRRi?YM8I(NbU0eKq6Ig+$t#{Cg-T4uxg292H4f}OSMtMq{DMMX|Xiva;#_#|@1^T}jR-("
    "gNgDz(8sP|h!qd(O2+P%>Xr2!DJ>OR)emjV~n2XK8I{jJJ85J<6VJ_1c5Y{Jj12{Cw+KyFcjnA3u8h@X13sc"
    "D=1<4<7U$KWaZ|KYn<gKN)Op!T<8j^XyTrL{6c1xZs_nK>*pQ4ZlYS!1)3MhX!3{Wo<mZ(@AZK=x5(6M1Pm2"
    "zf05KrRjfldvVB?4ZctCy{T}~{1#X{T3mvx7k+VrPW$1rXF)W6I5;_WaVeS+E19RqBjMfB799B=e}+xWm~41"
    "4%So7)_ls;!8&GEg65EB8_cgv|>XuixOtc>g6=IjP84<^;;4<0w#tLREn?t02(>D|KBlL>O+;Q4{K?r{Q#T7"
    "N9_Py)I*_+ZBTp+nz%sAYgFFj0UMH~3VC7H#i8WCZ_;Z0=>DnEgvnND+()ai(#2+sRuEg>IeNDNwE5SF9vGz"
    "tZGAV4uFMC5X|hRbL<E+P-(|KVZ)4LI1NbkHfbMTW=rca~F8BF5BJ!Ud(`(k$~^L>bhk1PT;JHFn@T9Xy?Wc"
    "CAB0;>gei606_EA{xN%fKQC3&yi*1sQ6<H4$991;JhV=qMTpD<!*sOuYl$oT!@aMzn5qeCs)}NsR8O(f8k-T"
    "a-_bZ5b-${xY0tZo=CvR6x|4_trh$@@Vr^CkPPNAk&W<=Y)WrMiSXi2kThj4A7`^-LYzclO0k881ofnhd1X="
    "ll@0y)&)K^%{Ch7Aq1p5P0_ZfE{RHwcE`4{HotNE@ZO|C*ZQpxG|F=7tUh_toV|7JX6KxF?=#%0@@U*;*_{L"
    "-9hjKq?mm%P+1L4#Ht~aLbjcMaU*lD1b!r6pdG-J)rL_J}4NN+*7St^fGR`=|@m=mFxp3ozPIuTG4XORG@d6"
    "{%)l$gd1;~)09Tq3N}oGFIyIXrQbw{d_xeHf@*)2Qo$a$r8=<!3%jO7mxVxq!22KY}ctIUmis+pn(e-zsS@Q"
    "ApsWBvpwx-R)xgZnxP2Ml%_L<kV~-(;3g-jdyoWcU~R-0!<w(^#(ot6WVTg88>WgpK=4%o+fq=`^)+quiI?C"
    "<@-Tep(SmM|3_<wCFQZ7SK0ZtNRJ?tce`+Y=iP1tQIuelOt3z^Xt&L62V)&UmJl!)MoGzov&j`LG5$*lgggh"
    "3y{X2E)sP8EUV98XoGfNNqjKQOn=obbuD7aCp9RkuQ0R`^k4p;s0E|fXM2j`*hSx<47z3OSARZQrVeu7&w}0"
    "z+!%$uPY}-eKpJlLRli%>7p#a(j#q!aqlesZdauSlJ#TX?Yd!Foyp-AUX)N-1&)VqObcfHHcLh<d*t^UnM51"
    "7M7wRa@A(f7R9iP~qH(@N*)@ck&U=N=iz+z~{XlBJ=x#Kh{xAbZWmxPewRr1($2!)CBdeArt^hB*j5!RYaS-"
    "Uif}rqy<qZcCd1HvwIuBk$!;SX}@w{Sr1ww>!P=0h<PnKuYDkAApww1)D)%mHj~KpKf~@$LjOK5|aNE98ukZ"
    "UHYBuPq7ExoB;1#Y{faNY%93)XMKz&d`k>Sc@3Y4E{gKADR<>A6w1-14w5J8o@jXMu$WUL_jr?88J-$tpBkH"
    "~M++9r&ytPgf%AZ9h6IuN?q2I}upJw4Zax>uk4gImq-lD^+v4m7ln~tag{|d5FH5O<E28O8OHf653>aex>Vz"
    "|4%J%H?v@6r4B#_$K+IDQMOGS?L*^*lF&isjsY3|Hpf+X`Xm?%F+Os<V$3Jpa$o-)SOobG3w9!x%;TG)3FvL"
    "DVH3eZe|=R&4T031PviSRongtOsj*y62ec(h29woh&rVDu)l4jz~4EH9kQ7p|~bN_Yxl_0MxJm<2Zg0pDaGx"
    "b<!6I}m{`SOgIP<hIKSy3ge#T+isjk@>15V>XDk4QF(?^JYz4L2Tpv(1Py^&|7tJW!?FmyzZ-)_Xsql0%L#1"
    "7{W8gf)CeG+APKe=t^4HK`C?V#pTg?D_33O#aPyNiXM?P`5`r_ziJkAY<nMz*@R(!I<A(C|NF3=eDuG;>3m3"
    "&k9gcCWlNrJ!C*%o$B|{ha^BGCy`!Dezc3F!`RmE)-s|JT!&Clz`uga_{xSdkYUkh=`D?ek^Xe5sm6;xIqGN"
    "{raP-&HzZ@R$8_saA%z1lT9!~eJGq^t_2MFg%MGte*08zRDCNjT5=NSP>m&HGfc%mDcHCvoHm0iGsn=SwPr|"
    "YV305@?2tr^->!|SZ(@|}(7>g8^lZh5282-Og{EkMK;s~EzxA+a`oMxvQ%(~Z+S^QsV$a@KJq_SO-my##l>y"
    "d}6^dsqFAnN9E;tVG9Ijo{aE-k&V6zLb6I{?T5wQ9hfkXoP2gva%`<1Gnss^Q$f>MU-eak(4Q{%ye%$DT`0O"
    "(Bm*6%r%RQH<cl=!I?&cgn<K$dUylnR-6@@Q3LArbLSbpLh(yy<8nfoGuKn@ZIA4<{a`$Q5Ce?pfJW<A&F>O"
    "KVv6wt#qVM^Sxj5Wubk$S^XD||4_P27mXw!5suej|GqRTSH!vWR^mlb)D(suFz*LTSjNsc<VGo+22s*uJ=+v"
    "i0KNXd-C51l%isqEXUg=6ZpuE857cAkU_zF_JFX!~2d06|+$Ndi8WxnpjZwrQM9)zFlgK2{5Ne53c|K#-Km>"
    "nv^sP0z3wWAgDSoM1IL_#cD)~xKuhP~3#WPjYxKhfVIk3yUghc1LVf-cb*5j!?kSg-QFdqF#cM}J6f-mEq^a"
    "1~D2NwpP%L^{2-;Pz~M$gjyU%f?N*v-0ayJ{Dusv))_HD1%@Ty?QIcHphDv?O}YuhCd4*#RhSfie`4h9jH~m"
    "+6ylu{w$j>(g604G{8+3HgL#-tz4RiO_d_pPXCU)kP7%QO61PT2|6GKx)JcO!uKzC_FrM0vFgLD*r@YAqL0-"
    "*qP~NO+EVw34GV~wHC&MsZ~rndY*c!sD|JPutOc&q=S^G{RJ>RI7%-T)0cSmZM2syevL34Df#&nFK+}i{IvN"
    "twXGaCACL463YYZ@=DDs$HAr$L<<syc{eJ2UjskC%ii%9RbQ8)?B8Ta<z!QpB5<jv2o_fM&;-Ax@A<@XU+2o"
    "3}Z{-2!(8FI72(ComZ7jGvMpIK^LP)1eP4{zm4KeEHu=*O8=7x)|n>UlQowfo5XUE-1666611Y$1<bV;B*he"
    "vYuhl}9~~RZ9A2Q}3@j-YlD935z;8J$|!$`sR4A``gZ|{TJQSy`9~^>>YQH_kP>o`yKxI&o}$WxOs33^5U;#"
    "VrJyTknFy$G{g$8;(bF`14wO@e~i4c6jeH-bPH$h&l3|QBy}dxtuUqvF})%v%T9d6o;P;PhW3-dU}=4|F$an"
    "|7qGJJ)=vl;3b#(F9+D09er@<Zm3;|tLp@hoaODW&tzeL<-h5%L9nxpYu0q$fCBR&*iqFFHQLN`%xO?={Ed!"
    ";-65Oy(a1k4y4KeYwl5<zuZQEkI#^!H+lmk!`X5<GM=@Is$j5w%fBre_Qwf6-@mg%M%A@d9hBG;IoX~U3ZRN"
    "slv(H(k0tDomn{G%}frgrj|!y{`9#b#_G?ZXBt6;tpYFpx`<pHQ6_wCVu`%b<xL`#E2L2Gm95<I?a*`UJmA%"
    "Leu?FCs8$e$qg>>tm=S(4z`H?r7Z#Kz@(71F|LtAHPSDs2mxD-#W14aP&Vcg#S3vTg25gP>B$CZ)9xpkGQC3"
    "IQ<Veb2$10ut1?8Z)pg~n2|nS(jK{v+D{&B##$;n<VwZ&UL5bdJXJ#+ip4r2a#uV~lcy=YG)*?sWTTB^e&X9"
    "IWSGGfSwlaMj@7R@zN>?A@%;*~)&E5a9&dVwRnWh0B3%ZzS5sFe(11%R&=}rQYi;gl&z^b9?@(z8P3^v<Bm7"
    "OaWzCdjSH`xkGe|vxpWXRyCvVSgnmQvp2eO$ulNc7|T+megIoy!%R(H33TZerp&WL<vxo$Mk6-wg^ccyd^mD"
    "y^{+rCOHt$fP`%i%jjCxsCLZmK19^F%AJCs}_~%t;S3yxzoI#Uj-l@K3@}YOcQ8AAY~u|L0!qx5HJFk15^-A"
    "c?0=p^y?)wNXAg2Uarn&biZu!*}nE^D9wc^c?D=(tu2g%xwBOW|PdW<x_Sg5<is`HZxoI`SC<G1~$jvx`R>C"
    "9~T#wbN)2HEM~QRpjQoO8tX-V+CbAPe?#!CYm5fdI5K%VFrL|5zh2BpyOie<zqS*hywlU`{TB!Ozx;*VDx>U"
    "EF<Oi|ZJ$G<I~Kd5rE0Uh03Z2YQohQPf~8B)jFnc?PAFD+P3=&d^ztnuf}jGpWQ`(R@Ycsfyp6Kim+y#Jof@"
    "9FR?gI$r+Vw*jrLIk>FK2?VtwRL5NE5~P3!MIe-{Cvkn(0*Xs6yqhcA%Drq^sD5J21WpjYh1OLmd&8~L|tDU"
    "M!yRoigHa9?u;F2)*62pavYK+vvlc=bK{e)WC7`goQhim15?9e_=}_@?Al*749!j0-A!Z|b`1?Y6%!0<8@jb"
    "^$@}wdu1D1$ytz!Tx`~+3WuDX8*;`!R{V4u~?w!H^}<k3{@ch^PDq*?|WP!zz9vIwSs!=h2}@$WVL+r9CM%J"
    "O!Kod(!>t+rjD65qnMv|D438O*0LQ0svuF+`CP>@MH{knDh=mIUAtl}YN-F{jau~oD`~rup0^v+KX<YHQ$<?"
    "fZBEsKGUsOnd#zTVti9Jqr+-zW@9VvT)05zE-QparxlR2c{;O@(I7#lh3F;R6>tEuJzhC12k6q$(M5mi&qpq"
    "fk$Rwu|dq;El{?C)SYpm>1NMF+Nu8en%KP(d6znCJrY*`7=LQjhP1|7;@VP9m`;(kW?{BqJy2{)k`cWJtPy1"
    "pF#s!^oLhl0XJq?99_Jjxk;+I~VA2y^_)?Y+(~#$9#`I%!44T{X%}gf0jY<?QdcEd1j=?t+GaETJg7=M&;jW"
    "Co2HQYp`2?mdoQ5O29=FB#4={wS$DWVbX>E1~`OCgu}6r>K3{4-R{N>pv%Ce)=$U`0Edwbw4~Hb$v0-XB1{t"
    "4N2FATe@J+o;|B;)0UNdw&}eudXtlCJ(26^9Me!7whvnY_@}F1%TqOp&zkl;84Te0Fzs2+TDP~Dl@l~&_$ki"
    "#mZy)tf_AP}rRB47jZ5pzilcddXomBmjQ7}Vw#>$H&iPwirN_+_x371O=*BvWnVeV5=Ifi1wP0wyA^D%Q7ry"
    "P{e0^!+$#-eu|5=lO3qgV)nEeIAsq{YREu!BVQP}96zF_R!O$k}DyZuGp+1lJpIYAQ+XO}J1W#@^1An|q7{d"
    "jWKX~Q)UVRgv%y>?p<9x+dB*Y|~OZqGI`ZxII{p3J{Z5I#0`G9PX&A1k8St{f~i`X`JQ-Xn~v4voU$wLRyBO"
    "OZ1bi8Exj{(9VPivK#S^67sUR;gb=Z{PXmH{hGg;g<yU#^5mBniUf=P^zdy%8ES@qI;J`zn_mQeE0<hK$w|T"
    "k%sOG!jQHQn4QitlpV&{sUqw=-qZ|`EQ(E3iL`Jqn+#%;4&;1E7bmC3JHP+DcYOR;?B!uiFIIi*Pf&IAfP@r"
    "tsFMCAN3a$gDbN#d36w-INvRuA65u4+aR^kB|3c56Mi$E8vkbo&=#Yw%(gZk=Q*f3lk09uhtZMM1PqZK#rHZ"
    "AL{Fpr6^s|d(877UaS^2YSj$Og~eK4Mo-UhrUdeJ@F+*}e91EYdnc86X62qY9=f2owmy0a4Fpx^+X7z`&@wQ"
    "9_N4GocM{{`bfR<nF9GjqU!#my$v&o^2m>RykVmM{BuKHK)@cLnW#xS)ZPA@gl+WC}@dR(5)4;UQH-s9Q-9K"
    "eL--Z7D+D;auG45}OPq0l*BDdp8~u{7tGABBQkt9mbgBVTfo7IKP3x`q9S(WF2pC2{ZcAw?_I;O|Hf{UVbK)"
    "slKV!jh>7<_(jWpMhpn!Qrcdfq9_1}JgHmI1_pU93v^QrMXBd#UlNZ(bd-ABXhs8WSG85%QDdW%MrGFHw~fT"
    "zXM}!55*Zg8h4b8{9FR}&j+Pml-F_D6haawjDaiMW@vs<wXhd(3FWAJ2hs<xWtM%3I9{)wv+efD9_>Gk|Uw%"
    "><rLJ;bzv-6vR;qlv{ryt?AAYIcf-VP>9SyQya@}$%C<ct>=S(Wi63;C(>Gq3qig|5@uJRetY4!|~1@>mlt_"
    "Z^sA|qke#4w*VK>02G9JhR|xwCMkbE{aADx4JFeuPN=#JCD^knlEtC=Hbky2wnK9~{eH4#83#mY->)q~Qz)*"
    "K91&D?#60mV?JwEU_AIaiC}M;0rgcf{ctl-suP9p!K3qa^$O0+7ef4JehZ;ccU8Lc*Eh9sn{^r8s+C;+Bd<l"
    "gCJyY2JXTw9hb8MWQcSdthK(s&kA<3#}=4E1j`)6N8oMQkkCkKbwQUN^!~dNL{`Ypc0nZ!Z#W|gbTt-8W2c("
    "y5XT-ZDv-<XtUXxN#<4Vgy-BA6-_@muI`pED5FxU`hiFmerTIxQD&VTi#7G|qw$6FhuN-DhR$G0JL1MTb!__"
    "!1dg%HA9>fQ2jL<_HIb8Hsh~N^1$o0SQ9Kqm%d_w6NkCVp+{L?SOdDn~|dX?~Vcf1<5=!hRKm&I54_L8qIxO"
    "~q`{w}x}x*QG$h>~z}Ihnpj>16F*oZ8^h)h+?0DN=cAA~H>Q8SNYo8v-A(w}{DNgm3a8At{mhyNUnb)v|-f`"
    "WJcRDQK|w;+H-A`xzzU!hhQjo;1@H-I>y+(Jl}6e#bxC?KF9mV)bs@r~UOQd=UhUGO}4o&^bhiYC^D5u7SUk"
    "0D@_p^r@wIGM+?6RPPu%H^Q|{`Ar?_B6U$93}<5$d&5M|eCGd$<OPiAJZG3@hHSTxLL_LERIk2=hZ~gWtT)U"
    "VwY-E)0gn(*V5|l{{fx@cQr8g{iH9l33h?JR;a}{(e7SeLcR<Nm?MLLqX+MQkZ5!%)O(<Hd>2q>JVSW*NlEV"
    "j|G<~^jHF>$Wlu~OwN;+B1U!RRX_|C?^C*s5tap<3}mLiMh;~+mG%sI}i>w%zB^d&ylre3;sCMVUPK~Me&4J"
    "F&aVJ$T&2P|`n#0QT$yPqJS;j8;=r1rqd{_^utebzyUWgN*qup+yXjYg1?-if8ZBC)`=*$U!eO}GcnNwBF1+"
    "GDyj(cm&-pl!PAB#ahU>hlem+w>6=G3<ZYzFBTlHWLpPUQ;Io=B@1TKil&0pODK~j14-jBVbgFl&X$+`<yB~"
    "wn^`8c<YRnA=u{FC<Dj6l0i1SCBe2&QD(|9b4bv}7(_gx*Ad)~>|2?8*%<H9l7~_u=34=w#2rVQElS-pQU8Q"
    "sXMQ$M-G*91%{#q4&aS>yx=i~!+{6F$t9E+bM*x?ePUbgM<uh}TJSXaM8ul^K#?y<WZhXo`<6Xwi1?JOazBp"
    "(0-oPsKD9vIidj8`{nrz`8TbuGn``I%rQ_tT~#rmdyV~HJv-bS~c41i1Gg%MReh7SJ|)e*2iL`+(oD+&^gSI"
    "T3`j}<s2YV$*4!arhN#-NqD|M}+dbWbr8Y|BaSgQJ>-;<crw=J0QAwiSp8uH^uNsd^>ef=01h(A_Lw?J86cH"
    "jT{s(pLxFVyzSp&Nje4ibd8CPAj?A6tzd9(2yec9fI7ixY^?9f>fOa_%EE3o>Yl}K|N60b4_rtc{$gk!%=nq"
    "Tt5;x1P*hDcUE-1+Z}_gHfeFy?fmRf`)fEWIleFIsNDQkx7T;XhX46Egr*wRTIyp>F?TMMZi>49GlP!(a3ND"
    "fyOY=&@J^yTfg%R9F(pbvU}5R29#+`iAYEI5Wy`%Tq@?v)@g(so98QJ$#FnTJFGjagz1FD@U<}<5DyHRziKN"
    "oV-Acc=95zBCOU0MU2yaVV<ZS%6B{RB&@RpWgxhpHtDRyy}UfM2It=s0?>Zg1u+q&S>#XQucmM`PCV)Ku`r<"
    "Q#8@!Yz&@V{)Xikzib!Qr<~(OrUQjn$$J&f7N$S}ndf<7A!U+T*X2I}#Pzt2rZHzKEMEQpp6V%>t1OkaaR6T"
    "sPc`<PhWM7q?fm6m?Blg>iJ<dfzDMdQA^Osb@hFZU?yrUz#Vmv`BY*v+aN+u1lQTQpC}<4ff4lDsFrAw%uym"
    "0Vd$r=$&ydmSu_-V-6q9dTg-q=K0UaZmnT&{~V!#aVR(DS^2?KdIceYg2oVj|1uwC<W5NC8>cXUz+lTSQUsJ"
    "SfqAT-Z2@FcqIEmja_S-v7UP~RitNFWy9J|*xrP>>UQe-v69S`G+x;CCc+=ZXLO9Myz6>2Zy~R)p<!}|@Da@"
    "P;&^TRSa2g3l+{dnd^sDw!sH5N^Z^LH$8+yMj46zt66h)#y6xgDi4Dq+jR4PPsR$?7=!1`cW<!df3A$6)~qF"
    "g_Dlzqr$S_X4G|2v6j>_bS#AS<+zBjFGU<7OpCYTMMvBren-?f~fcm!FR)#U4)C24_}fpcPz>Fz%`qQV5TZ("
    "uc~KC%jQmAi-h`sVNb@F<VgSZu(kg)x$zkgT>HYlUB0J-6qZ+fQb{?v5=e-(v{%3NY1b6w_V;>$%AA#nN0nW"
    "!hyXQPv9uZei-WvE$w>Q7}OjY{sznSG)jt6N6}@2*o@!tWuejR=!_&(*$??O4@!|kQYs~}z&e%K4XisN_!E|"
    "YDplEmM<8!AOG2T+ve5HOU}izACD8E#o|%c1x1^@}>FgRenv|glcN)x@3oOEB&4!bU)Nb9rvuC+16sw&|uvT"
    ")+R>G^xqIby^%&}rHtuQJNS?|&x*svHCLac*{-P2`Gm8pu-6kRWK!D=^U%F|_B<Y6rrae!ItxX6pe42hbI^3"
    "h~=y_AQ*Y-fB^aODvuDy<-*CP@8tamFuWB|qcFPAV|1EG63;!x?=mImw53CaBaLm8X;Pe7rP0s*sFz?Mkk&4"
    "twAOX>l6`2wCH@paxgCUbqK`*)-)ku?ej&?ACF9Md`j~(_+U{Wga9Kj<L|#5*BbQpv<X~ig&(LT*$FLqLi+G"
    "o^W`jQj3e3jj>SA+|@SA>k_oEM8LE-;8cz~QG4krKU&P`RPh2`IWWD9D3bIic_}qaM=(7a%q+v&X;>En)aT@"
    "40i3ZiY5&k?SoRP2670s}AF!UVZP2}gpg)9EQp%o@V%D(I&|yk}QnOJp#-ra$oKq(37|XsgXz;S*y~~77=2r"
    "!F%J9!rO%vFVP<2js5Uv7wM$OJ)C0DtsLmhOz;>Ce98BY>+8pG%%$4#of&8P}bsY_UU)?d<?Xe9;<RCUavOB"
    "FgG5Pl1y4>HMQG7vLgiSGm<W=^}W=u>@BI+W{jhDWuWA$Cd~uJ9WNo*>5z%Y27?;TPE=THmn;beZF)X?9)=$"
    "(**1P+<-N$ZVr?46h?*zy~`Y78eC_DIN_;2*9Na4?12>8MA;5Q};+Em3{(T12=Xn*&D-3_Ly^_l@4y&K5iQ;"
    "Q#<Ef&7E1luZKwm4B+!-NtUpM6AZhte2PV%;iQM>`vX_koJ|%Nm;PP2bF@#l<Jj;8B@yjg><<6H`kGjJQ$uQ"
    "4AhXn8B?kzFsi<Wix8Eqc*3PhqC-&yfnRR}%*x7Jc#~U!W#c*a244#{Au|JS{hPHk+FpK92Ck9lORPPD1qOy"
    "+9Ih8-5ii><PNHJaP|36L+58TCF&O}6X!-eV-T6!uY-yrc|Lk24O8_*aNHsFO*WMPOVKqJLDx!>__Z6!NMUg"
    "(FfO$vX<9n8WFf=U>9jzaS>&b5}C?9ox6rR8_B`9!xC@-^tG_W|_432_(N$qC}o%LR=xGH;A^SjgjA7ScsXx"
    "-RDb_UqWl5u;4X{Y7f^68U0~jbL6GOGH2nb3Ku$pK$@&#3EPLa+Q5N@gzr5U345F;pZiecDrrv8D;~r$rz0f"
    "7%*m+A$^BA#c}giqfKVk2wBQvl#O*rdQEdtXS-i{IzJ&Kqa$9x+l-dPIi(`+W_`LL_0*Mc32+hmzKCjY!hj%"
    "47|t6pSpz2?^2BxJ=mji-Xy43D%sx7w%%7{QLYq^q#A5atX1MQ?#h8=<6!dYLOS#N0?nfkq2yeMAFj2BJE2~"
    "lt%n$1aD^=yXu46O%j?_epr3{+_FFAOR*V&QhL59jdWxcskgAg_}MTYJ(;jS1;lgoTKMZu1QLcAPHe&c0vaf"
    "xE1pd9i-;SX1rlVKhsPQZFth8A4eR8df68xoBf%##33S@9Jz4fFBE{1UkfYu&mQ!e#L28$LziowK1Z{GRV=%"
    "EYf@HWK44JC0ci9Lc;OIqFnEbSb$VN!w%oGe)rmEvt#v!B~^mJgMb1grHZ$WKI}SZ#j2)T~JBcE0_ifR-pYY"
    "K)mfuK(Z@)`D$f_cCA47&1(1vdA~5dZ$cD6qZL;j9^<hERz1uv;Ab}0A;cVF$|-A62E;~lkwW@-6VA|zpiIH"
    "Q(~(>_Mm!rjm!yfpeKVa>v3LduELZRdoe-<p1sYo}GK?`+7U60oykB^L$^Hu%I1HcMRy@g%csIiSolQ!VMyA"
    "}FY;fgrA%v!erwvZ!gm)VaU)W8FeS<zSa+gq9A~1I{kk>GWU9qd62njkrK2GP-P{=r1=*^QJi#e!Dkm#jkhm"
    "k39r^7|*4O6vtRwJCPvFzNxq12I#Y-M@EuEfENpF{X5J3df|aP~vQ$jQ!2Hb^lqW)kCTH)tJj2}xB(g$y}7Z"
    "*S5(P?{zKal+F@39(m^51q4rib}S*f-$8Lbn+bU;n`w5COK?^j1TQOx+awO!qd6}zOw<^Z|_4Q3$zXgcv{N="
    "#5GgL1or5q+=%>Fb&TL-g!$Cs9O}_<dpXK)z#2znf<r|(FDm?`R&&vpqT)tCVZ5y5A9A<@+qRLplV=C5Vva~"
    "H)&_K*p;~}W(C60r0F=mQ#1TN;2ZbglVVZwqnS>O4wuWXSyh@(K#%3)CZglieqZT_9K~-!|eS>E%6JEwJj@Y"
    "xuLIu;$csp_Xk34Q+ToXJ@vC}1>6DYOJEu|A76<)SB8%e1N-05<6xxNXY2%GelOCBWHd!h$fs+dFx=<*ZPK1"
    "Q%?DA!@w#<lS%;nqfX(7cYh{EAjg+)WnTg_S&_De0api6bX>94F67Ctb{0r)1j*`Tb`FzH)AwkWPXlV5VaRM"
    "xV^HY8u9kjhY!R<x-m{N-VTZH|W4iMgiMpfEF7*WLj#gc(c<}OzH44K|A#Lk*;tnIUr4k01PtTH)`~(<vOU5"
    ">J9<^qqm}=uzD<v^%SnYyqM0{<S*^bdIm!-sIGxyiSwD?S^dQeR|<U9>oetI_ObYg`+&4-xE4{jzQpZ3MAqp"
    "99M$s~G%~x67t)(W3C}bhXB+Q`VsI^vHHo*NYxxt*9B&l6M;X#4H9O3c@X5W;P*7#cDvYD93*%=o+X91=jKj"
    ">viTCcqX(H*7SX)M{u7`VUD2|RLz7*oo=fW2p>j-TkhF{=VDY~TvW{O3396H+MhiC%Kr)smI%h{W%EXs1(#A"
    "<Oub4trFilKvPr6v(Lr9FyHBLk{NM$xdAT1wcf#y--S$aT6@;#SMXBn8osQns`D&NyB@voK;P0%pm<1V)=Bs"
    "u6P{rjpHimm9i5wA+Ap&zHJYnD+tS%F9cBZH6})tPH8BOn>6zqycl<4bniaKRcEXfeAOEup5L?LU$PQYKv>c"
    "UM80RSTfA!7^*a1F3PaMZIC;rN;t*Do5uE-h&9h#28tG`N~LVI5nl^yv7B}-%V8ftt$!CyZ|p1OD)x1p=GgI"
    "tsZDumQl?hxHU>>cBB`i1lsG3JK&aE>XUrbT{w*{`Do2uVFFczaS>ZTs0WW{_j435)^5pcx4Jzyj{RaY>LH*"
    "zfPG;Ga>!W2g3nd|xxCnA$ncT9^k`Mb#sDg^h>%>ePXDYr>nT`$uM=5G8-RdOuAc6mevI*zCq0zPC0H`pM51"
    "_1#)jB&Cx9T~{cG<_Q7}Bw!s~lF46n9iyX2N!A^&2|F>~$(Hi>WbISAE;5W7Xw_q9lA5fkxfyz~>WGNx3gFb"
    "2w|FtR7C%1lJfA0v04GVewXJJhas0#3DLyny7eu6qW>+rJs_McubL&v>(aTq`&xsmNU$by^^*N52=<PxNF{*"
    "W1<J=@C4<)aXu%h92qk3LL}vL{XoWBbVlP-vwVaaGfE^z>k>aaA_L5d+i;2{;UJQ#U#tF@jK(E=;uMXc3`#("
    "fwF>|2m=oDj%Ve(^2jWJ)B5#B>D=%s1>5$dukDvzIWMP|LUY7+j<54ko#aenb!aDYbi@qv0><8`V19bP4spF"
    "q<<4Q#G{y4#Xq>ku{Z^GjXFH!3=k^zp+usY3H<_k0gI^ZixgeT@(dEeqdNPGa{JWN>mGNfQRSq_@;npg-!z&"
    "!R*PeE4cDpO<?XDkU6hCwy!1HA}nBA?k;GPo|^$K+VP5IM|ppcxj7t>Z8+VRN9PQ$i<DGBI;Ee2ae*e=3RuA"
    "o@HvK`l8&;-CSHj1Wq4OQ`4StH1-EcnBXz!>RG#N^tcWY$k~6V4d8I4Yv_8pT147!lglDZlJL4B<N3sIc^YK"
    "iQI{_*(jrt{S2A#0=x}K@AIZWhiw3~s@HnRPDXYbtQ>}xIT#<PgRr#tQ7`q`1Z@lhVDIO}90RhGAxKIKv<5@"
    "}^GlG@$1KvW#cv+eD??s}e;wD^WpNd)3P1`p1dKw}Db$JPd1)Y|F0+!E`JlL1i1?ymG^?c+$Kiz(5$7EYWW-"
    "@Y?0wrdx1Ox`L_$F*!ar5G7L!4p;M06v>Nb~fjDiCsoUy71YLm%vTg)dTWNys6*n`20a-Ne&B$y6MIMbf8AI"
    "x3=2FLyclCT^TNJ`dqgGOUr%NpfCu4TBJv<C~n;CYpu>6!eM<&uo<Rqc?tNk2#F{G1h^bC6m|A93kbZ=;>E2"
    "h-=1a0=mer|aCVj)){m^YMjsD)SMi5G}@Mc<!yBNum;pxCR;Rw!F%wq%b;O>s7I3s=mm6qJUYAJ0Z`~WK3Wh"
    ")%|5+7+5>9I(y~-AvoLI31!3yvCsskcA`6rxK1sL(Thq~%}H<JSBvub9D9fTghxh9E$48A=V-4&Nnyy5Ru?m"
    "gqRBBbg+qkaVmkHFYMc;W!)tyPjlvojmhhRqA-W?p1$s<3{naGlob8p2B?wJI4=vrkG(LNY$>masT9U+C(06"
    "di3C1zgeZ81ofz+M)erMS5L$(lE<0oURjO_+tyDnX?6pl0zy<M)UrOFRQnK=<<JPDFN+~83ms~Bw2AV3Bd&!"
    "!v7TvEq@+8BE*4{s?4c?q}Z475&;)Jbq%XEdymEF9vs#MN49FcEd#UgY8mbEs@Mz8*+R>P2b46|<=m>r1;Gj"
    "+R})DZ2i`QB_$2q81=v!4rDP*5;-`Hn4%HI$S##&83s=laz2~Fz|5?b^%JfSC`l5q(@_@9U`n0jO!oyY~l#L"
    "<q|o=t}|~c_2mj@DP?z|1JkJFr4u2(?kTU2JkxaAnsa`rDFBLiFelM>sriFVY$Rr}*VPzn%Ed@+ckAgiYOmw"
    "yGe@bzt7J|wXdIkpOs=$njPaktr!o60XBk;cWMcaQ-3xSjGz=1MKC0{}i_#%gyEg?GEzmSJU7Qa=o#Nvg*l$"
    "G(nO<|aMAgJujA278VGTdy%?+|F=_BM5w9aRy0gE$aTEm@7wnf(%3!7w=8DsR$(Y~=h;DaO_xm*lS=D3FuKD"
    "c&2(c&QE=@nIZD2!yy*p5iyJZP~plSJnVrSSF&N_`xNL6q|f%$+~S!noLaF=i8a9cMX`b>nkNuA7V!Au0b6q"
    ")QMopPLAfK;Wy|p?R&I6Q>cMI&UAlY9`jiCgMDIoL(X;$42dQo?}*wrF+aw&PiQHuZ%8f8tAQ*GeNd~4go;n"
    "oZQL8`+*0jbRz+&s1KnclXH~b5EVx`cPg3;CC>W8ve<X>9MAIe$%Gup#`@}db)3C|3rFgOTvx`Ls}jt*T&X^"
    "ot&#~^!=84Gr);U31Ba?C7bG?C9f>0HCCZ(~+>JiR_3bQXe45lo3<}-Nq%-SI-*yc$up`+=AeB1AXUhp>shV"
    "3BrADV}w2pN*&##~B`!uU;#5vA*<C8_RbllV!^MgAGj$iJXf%~{Oml<PrIT%U2gvtpyj($Px$2gQV|82wpQ|"
    "!u61Fr}<GG<qJAwvukbV2qS5nFlYMTwCnWX6#cywxV%my=n~EHD{+*j<LpT$-s^XE3~^hume{yIv~SNDwQot"
    "?Th7UPEbX6h%+mZyx%I<<1m)np|EI7|R=AgN1z_v>ReT+dw@@Xhl%DPPc+Jn<H^o`j?Fn#>BR<hGraUjs)v^"
    "ovnjQoSCxqg#->H9uL_>b)VuMQUiX!i@_)*N2|D&wpzCIiZ}`$LNqtSBB|BIbq}e@G+XqGIaXpX5Y-iUE%K*"
    "9LEMZA56vcUJn^z8dr(zJ!hg=*jc?XTN$gTeV%JA4IEHCa|FERS2&p`c?kxeEoeZqA!wGQ_0D~4Lm><LVax}"
    "d&SG5yB13%eeTgl1dTpXsjxvg@DxeIuWl(0DGlTXm!se7p%^J`vZ=P2=%s7$Ie+#1ozcrRsDHh9hwI)TG8I1"
    "0q_x?N79=yna<C;IZ(Ugw}KWC*bl!okFl7=RGdYX_I%)BI|dO_xJ4P)@nP8Nh(xLhN=CGo+jhKjw{Qi+!m;S"
    "UdX;zo-TO?P9MD;6)AWM;a64K@K_r#t127MR%B;%fi3AM^H?*M@r>A-8uR7#0R&cPN}z8LTi9+f?e8dRYLH8"
    "H>UMZPUz`Vc(`F-ssJRi2Swh=tOuH{Y`PCq<uAAuI7>ksHW+=y*@YljUE~g0hQd^KyJ!mSb{i<Vfgm%%d_5V"
    "fS5sgC`~hfg+WRft;se7$OPw<vZ4ms9#DX6&N(k|@*f#?I!g*p^gM`UgUPi8<B=_p;Q2eHP?>>?We(irl*t2"
    "-hP}VHxt*dPKp@DzE#y~&}9F{3M)C{UuqEJh*UBF!$*h@-%yp#oakq??gXHo_zb^!)!X8P6@gU;gR4+d0!nP"
    "x*!IPEAjjD?nIIFbzAqXhK8QX*Rp1`>Qd<Zw?rf`EFs4)|IRQ;o*1k92uPc6LF#f*n(cricIU2X5G#47(h!Z"
    "JVRn5m(Ejb_=8e5dH9{2701%EVk`b>9FI0Jv`Dky}Q@?+oTvb=()G_M*MR;Nj8#pvdv?FuDbl~S+g=|4b|%i"
    "evv&C@|&CqKH%<QfYqXc3U*I$8}ivV$+L+GXY^eQ-T2c+bM<-x)21jfd(2Hf0XpW!MP>PD>*56LK32}!0)dd"
    "QXL;~VZ}0&$AMQNvs&zi;U-SM83c}6889NWa&Z(Y<%JcpMd`kYU6WM7FvftW7Gl7So=ngY7z=lK&Dhrta6Cj"
    "@<8t>#fBI;5S2=%*n1m)r!0H4PG7H4QaZx?^bF(;Xcf|W5leO&x~k$cnQ#D;$5q-mu<Zy>2l4MYHS0l0KuNs"
    "rA6BggT$=-V|7-Q%`4dHpkq!C76@i$N}-83ac%c#q(cttN2cgs!}SQwG|1;BqvvG&lsckjO|px{FlR@rV<}X"
    "5%hXG2qAps6)YJAuwq7&QkAdYU*7eIB8}wyubLtbvG8x^=F$MNX8}-EYy2q)9vj|(hFuB-vu%(-EZD(af^9S"
    "+2Z>Zb~{A_Xa|(l!-Ipp-P64nJ|G*t5QN+F+<TuxC;AcSR7K9FRv`2>=pCtvCg`}2>z7>{4RYoUSG6!5FTQT"
    "|2uX_Nww`EMKS<E<j&}}DUhW+ezPpY!0=eRjuFO6fN@fhKh^G4Btnil}8t%X0t$MU`aspR421wuWG-YF>9D2"
    "|j#_Wb&nKW85{!8Q&2n*iU>Q8zLVbGsLO#cuk#{JDPMY+OgrJYLu3@eDuL!d#AcXA+BfHYX?)aM*#42F;^9#"
    "}CL)6JTraWr!5(yY4o{aNKP7jx&g{geHlU+r~qXW&_M8sFGId3VEqn(m%=fP!=}QJk91yC3pvmhsYrFVD`F!"
    "}q-njrx|ep_|*$9pb2F&RF6HtttU&M=fAu4ZFK)B%z?S*>6oF&s4OY_>)TKCLg|#)T<s3H!yW``#ro$(hJ@i"
    "?(il{y{iUWv(JO)suR#|-d5jywrW0W$dAH!Y=j#^g(9S=21{vhK5#9&&~f2r=~%0bUR$#{fOxkxL^YzCxIF0"
    "?4MH`%YUdL3)la?4%`Mlo^}^^BWnyGZN^3M2M_bRG@XAu6Fx5aQ@2nzlqPuLV5r}L)J&b5#Gg>P<@7a1@Lkf"
    "12R*@3p<|}D}ImPD3*Bn}MG@E?7M&vHrhHN9;XlHzF3|%1x|IcvgOQEG*3afchAi&H^EFhJ}5c*I4a(GlVJG"
    "~26fedZa2?qS*N{FoqHVQs(Y(huJ`@4H5bm93};oHg9qfJG5-2Kbp?%}H)1gzgq9&B#L&>!J}Cy#EpR}*~){"
    "jyc1{IGy`Zqrh=5GD%$AS83w6oW%!d5Ru~CvIHRl~Zi9VaTRCm8;HjWD?feGPG;}H=bo3trAW;6a~7g%5PtA"
    "#4omQao(u!fthS$2k;JBqsFKhcR6Rf)5g@APv+C+rq}xm^vv77!<Xp`6o?9aK6CSyi+N`geLUE!c1xF4QO>*"
    "M@@aH~L+e<mKL7B;3=_VvNF#=9;&Q=Av4Q}v&n#z5MA|SYoNdStz&Vj)AwO|$UxJZNb=mNO&HD{qwiY3Gm<#"
    "aCVK?Fj^eXcf825Nlwt%o&HBx)36n^<Nzg9jfekyJ2fI~{n8V696cHg#njaS)L$Hc-1!QPU&+!H+D&gBH+YX"
    "Qf>>P+763p7&pCa@TSk-44l*?OyQJ+ozUl^ztU!HA|FNw~6sQo;7Xze?0?=k_b;6Wl<={aZ)+tkB!LxlH?hF"
    "&Lns*Mv;@5#rdFSq_d%>e!{PoG~m^pfhaNF5(YAP){DsbwFlq^$V|+SLGmRnEb#4d>dK7Gk=@ZphBAU{9opp"
    "5DZvlFMRlYoI4>jD!;@`RQTjfD9ZdZ-<ousZMu2h8qO!%L2@{@%}w_9E!;Pt%Hw~fCZ(HLu?<Q#m9Z8OP)Cy"
    "^DYRngs4j*O7Oy)Zh_!fCBzxB#AM{|0r5UY-GDl*q9MYJ^&Uevg418H>9x=3(BIPJ7bY<G1GIQfA9{7KZ*=T"
    "J4VV!7ayI8ht3xYeqmnMY1A2~a%N?~cIHwN5I;{$M*nR%&`Q_E)&_$xwTPQ`JVR&Kr2JW=-^XQB=Z<Cj`!hK"
    "%{!b3sPZP%{c+3ogUdWrcQ*p5w|CSN@7uKe5C9n)mq@UA*48T}uccH4+`o9U#&Fd7EwgV`t<4+uV58-8lR4-"
    "z`+GJ?4ni_ZE8BBkYI}Cc|mF)}toLUO$+E&_UJg1BzV6A#w~77c}U!A9o)-eONIo>6Q=W+{S18rNxwBu-FOX"
    "xRSVzPu(;t?k3wMsgC#+e_E|Knar}1eNL2OSFuBjqolp{H2GtvGD-Zd-Q9fnwEO7E<8|z`9J)DYWKs&)BIq#"
    "*F9@|VLvQ-z5*<AzvBd~FsEoHdg(|-;>lilG1#c;LGqo^Nvq~bj*+nsu8_`kfX1Y^5^9|%wNt}0GSQ38DcZ}"
    "0FYUPx>MU^nUCF23H!H+^Mw3!No?iec7F|<ZuebI94zYAS;rHgm>Zk85~)T4;51EgViZD<fO&&SD^t#X&O3u"
    "vt~k67{b3L#s58YSmkg!{3^y1K>~*xF{|47+MsT|v|6;I^yRc4eqU<G^UcK%KHUBL6fDQG&*r&)RXTu~HAhA"
    "-m&j+@Yyfz3|APqyuaFN&XZ+u94}iLs97hCet0FU&EthtP`#GMw7rV=#QHvbz#y3dA9tiN>mya;DlDiD4#6m"
    "^6Bv8t{asO97mMWY*gWKpsyQ<aPBBPw>B2w^A%%(vuxO>xn-)2o6D7*TB!5uz*-#W-f{i=Tj=1mdN`#w`8v4"
    "K!*$eLFV59DYgBRUEP7L}p^7h49_m%{Td3vhsOGm-&yBdRq$0_*LMm3#kvgGz{xwwewbk^msj5?e2j#73S<S"
    "U{_4-x*;RoujvKZ^=?Q7}o)cq>meU<+1Ex3b9;DvZqG_Ca&ytqn7O<k399bL|7a=c7yXmYfUOJDO<6*zs<nP"
    "<kaT1&&y*Qh5>nQ)_0c*=x*rn$=B@ZgsIh6i8S-!P&;(s%@_Ed;jQ$M9~9msM94uT^&bz}q6X)4Q>%%P54K{"
    "@ybD41OPkg_1(e>_fsr>4P5_x`W}sKv7KI<-9ZsP2iealx#Ld@lGRE9LlY<kJ0;2VYh4>lhqv7M73=0hkn3J"
    "I8Zs^e$L<OWYVP7YGL73b;dDL2u%6|>@2mUZ@O$<;8r8blT;Q40SAGK42l?6FW@sGqq81={(Msn58~lg3i@e"
    "1VGxt31(%I|TNNN9HZyVKlK?>qNYPL0TCHKDtFzS^%bd~1aORHcvF!@fz9!VXiM-^d`qe;`J)`3>F}!wXm1~"
    "CS$J>f49(3&fp^=oGhA|fv{f<;t-e}|M;Y>Oq12-e@e7@o0y7+$v__<T5_e1d<W_xfwhtOqUH_5wuf60f_<Q"
    "0f9CWX+yiHUudt>h)mhiGC)*h*aAyaV2$vMJ{fv(WLUWRul#*QUlTG^lEhz{9rSiQoAPc0+R>sqy5wZ-A48i"
    "36iihH0dX;b=`HrGGC4z3*Ut<vHc@^d=*ix}ZNfH7hvyoN#G1^o<AOCMnWY5ssW_NLdUDxrwMw)yu0Usmxzf"
    "tOBrXMUR%OBg<Qw>o03~LK!+p8BTHvhH|zRpL~U;r_wikGDl<{_mqFJoJD_VKh{c%FpEBXJs3_h{NeGY!*M^"
    "UDl1Pt*y=uc{B#LVZFe`f9_l+$Sc|rL*xh_4@5h9?5eh~$JQmm-25qOs`2KzaDmmv`KBp-3Ip$AKo8c62JiS"
    "5m4Qua~cxmKkOTpN$9<gE#JTk=luTU$k9i>Z)G+KxpwT1C@1Nl80H=3H~gp>n*!8VgW0+EU9^2fpyj9SM8>!"
    ";k$vLPEnZFF7C6pJEJt0)-&N5Up~3pP#EpL{{1yTvdBRHv`NEp@{nqR@+Cn=d3(ZNub`>x^!UafcU~PbU_Zv"
    "{Qee>m2&YWO_`@)hWEXC|xHZ0Vp|N=+(7N*GQaQL|H}MS+AU4qi)I1YU4ps6)TlBoR_9fF^trVjhqy`g~TgC"
    "z|veAb2Nc9nT(5GDyZ&w6;3<DY;@kww$*v5yH+-0NB@9zWKO99p@TEo2@Fd*94%C;_@*5m4#kIax4Kb%x6^_"
    "{`iYF@1JVutppthBs;a$dD&3CBFiwGEmY3mXE-xFrvZ*X+2j$*~X~}Mg;DOYcXzGqIbq1Kq_);@GGZF?Ab7%"
    "HPox8hxd^y)HPc`d=$19V2ckkr%@Thyd_n&X}PB_ro>q+VTr;b^L75$y=zuxP<+JC)&>bqmuGlJD-&Aw}?yQ"
    "J!ta^%>zF8$<*v!-YJ6?*vh<?><f9v+<T{qNJrNLl4XIj4iTc@62@zZdkCkvk*Vki~2U;nv!1jHiY~Jp6U<A"
    "TqY772oV=b10&`@=yM@@h<aPGr1Yj>%$j&ue!U3Coz&q6<rxcXW20Phum%bV<pa(M$nP^Ynsf{sE*ZV9(KDl"
    "BPx$<pvW(CwzPK)x7pC$A8Cw^25;3nW_^R!Rj-p(>~Ce>50>KP&i<=!cwY6A#>W2M4{vAua}zgpwJCmU=(1u"
    "Q`v<@6yxM=!eRHz&%bvgKxvw8%Z*T_OC#6u-Z%>b<$B0c<(=Cg><C1_I06&Wulw+M<TUL*LS}}>^y`#MyV58"
    "mLoma2A`<3N!uB0FB>;GiA$)w89<NV?9RgB5vm^u53dUhFy9*Pzh|Kf#JlS{KIC0e4z#}YY*4s(5d^lFc;lT"
    "<olJ&oMh?iVKED@Qap)4|^Bqtm~_t#tJ2uN6kq^n)I&i(KW9%kINl-id3Uvs;`sEA!PbLSq4Q?oRRbM|`o>w"
    "Z4TB%WB&=q9vv&vsb(8*}WW1-MQR(W>vTEYGaijml)ntc>FA(tx=T{>92_cFNxQI9?NRn4Sox201D2m!A)Fg"
    "(cDkmhn1*p^pD&yY4!H-;xsCEyv%WIvfT9T!Nqa{`+I*b7#>l*$gwGtms^a(QjskGbeSy>;|=pj$X=pZ(X2;"
    "csWJraq1QL+W1GnW=&Yc%1o~qVyI^&xjioTYnaF-fW}S_XwL4UdioP=?-qbNQ8aHSVe4hqRvd1xVYHZi8Kb7"
    "*^PQ}d(2xs$fo!PiaHSxt2b00=OjEmtgOCA#tBn9DQSLgX`cAY$=ubvB7)7In7O}0v+6|M#Q&BecSd{_1a|K"
    ";@b$UVR8(KsCEf~j%{FQ%&Cyt$v7Dv;=9BdBQf;xJCxYA_6vJ%RRrzskoCkZ^*7NZN6QMTln2>6=pDpriV>e"
    "DRHVhB|#Z-rIfQ!!(M=8qtX_5kwqo?{*2lx^+39PrJ^O;z;x75*tQk1k>yqlk;M!oJ1kxx?y@%+6ZwdNJ9x#"
    "^-fQQ)Pf0Ebve)SY-B@ZD(?Uqi(JW}AWN-*@Vb0NkV%vSzMX7V^Gov#?mFa|`Cvd`XLuaP6AxeByV_#hU)Xf"
    "V(zg+duEwR>{^=(=28jE%-EKd8@bIUPZ7PWQlWaCZ?}@PwG<bEKt6A2|YTA)!E<yGI0U4RiF5mAPr^dgPO*v"
    "o(F$ftE=Vpo8r5nAL=@>nl$<bmn3(D?Wo0~D=t9s+H(GNL@DL<kiQI!z2kNFV6)x5M)^KQb(2rjeBNzucz%V"
    "1d@(*+^e&~KE^?|e-yy=?wCvWV##4Tq$hpz0vsMpON3=8wUgwuB8mA2-q32@!q|y~qQHaSWQK#anYoV{<ZXS"
    "XArs(LgV&#5H{;pWu{lC)W>qL->f?v!=ar-7?=2w`AfDmKk})2ZVQ~%UPMa1-tD8FLuY3CU4K0tJcnR6|A25"
    "9@W1GTkB0jQT}ig8(fWJHnUZvBWs8wMaF@?`8x?(7`676ecNZt#1m=ffE>M5fA!f)S;aYG(S95k_gRb$HRFD"
    "4?2E%ygw{)Wizq0SB{zyoZF`g<Xp74?8aGWktv()Tdt!|y7JwYWFlTcCRgX|)l|oLzFN>vPOG-8ybt;COXj^"
    "O9G1i>QofwdG-Q&n%{7Nu*m+-=7RP%8{33P(&2dr9JMHLcDTIxmI+A!OFI7XkUakxA4`K&kxF)?a}tGiF)5j"
    "Rd9C3DBblq#0$6}M0n;--_1R{9bXPFxS<wtk8pJKs)XYd&k4C?iot?I~;VJrP_C+D8X|;;)v!(sx(Lw{O+@A"
    "V4H+fY`2{x?;R=?8q8=?l2MCp*g%k949>_bHku%a~9Cc7gxW<zvZ%eTpjAfzR)*|oHY>zE>PWq?m3d8!$W#&"
    "V#tHzuOzNF=`^S#6Ra)qe{Wq)&-v1e<8;2ap}S|zWd;|CY}R4XJRK82Bc^mdOp|t-bJZy(*k$F7io*RET0e@"
    "kK8r;hQVovsC$Ug$P^vv5G0rEW;l1s9f?h}H!z7MV1JwMaNC^Gd#xD#O63(X*RO*L-ddmvqDlAM_sUdRE<&l"
    "9XA59phG$`OSEAj!AZ0$QCMr=lDC1Ge0kb&UzrQQM}=wQOzHUm_ca(axPTKYAo46ZBJ3Z(i0V|oF>5ler3qA"
    "mz27_oV>F#+G##V}Fq5(P578^apXOKd1pP4LnsR=D-vS1`OjRRW@bBwUNH5Rvqf<jv&#8vCOP1Beq#g_bNf5"
    "j}jrG~;HJZhJ-~f(i%6?<s(7GBB$#SS0&c9Y^A>P{J%VUN@C`OK$X$B8mw^qe8L<f)zG+IqUs2!>Z)?dLZ{j"
    "HZK0b;Hy8Wk;09wJ<56?kl8X2dTY&|2&_EX--#Lm(5wjKM6gWSH6L;iRA4pUEw(n>4--o0OxT;4CP#v$0Uh@"
    "d&Xpi-?+7gG#qpMZAA&gdV9j{ls42r@+4B=G<a14Pu6L-7k459CY0EX)bvneNyYyx40|JVzqbJ~+uISt~521"
    "@o+K=-qxL`opocFrp$yLn*B%hdPPT&Wefgj!yAZ-Mg8qutH8{FUH^jIT6QWU)R?HaK(yIFa;H@1ckYtb7?p("
    "}(|CK&gWk)}(S334+jE<H}@jV(1tVTZ_0GKDaw$GNLg>ly=tp@Q?oJX;B3DeG5-h(zyC-n?$`OL$Jr_lRAE9"
    "T2WIQkyd3N;>yip+$d2Bzm|@^7-&uLSm5T(L7qo2^Ng!z(@(6dTt{k8TMIXmdv!?W61Lbl}LoOf6rL`z}b<b"
    "OdLi;FFwa2^<34BYab{CG;(W+P_mUki+QrKk-SHI?XFe?$jkQ$F)=Sjby$o)V5eNumP&mRzCMTaV2crz4<O7"
    "WK@{|FJ8E>5VFtj6OTM<;b=TQS61WW2Sp;Xhu?@j#XP{vIFKb|m>q@v63g8m?Ew-a$?YtF;zKPrYFN}80XY*"
    "?(H@EES0&!eqvhgRveb|n}|G87fIJdfUyFW%YGnri<(LOScAO8ePK9ff~mI=JCoNTBdhOC6Ey3s%1He8d&?^"
    "uyF@VTR$gi@1Osyp4=apJspKvo_l^E|`v0?K#VTbP}1*+}Q1$?+#)qkrCVu=+i3F8pL623unAZ-ge<{ezRe<"
    "J08uI6?RF&hB2ae{gzeBoiF90ZdGO+j;e7?<8sbIZgiDtXNGIUx(7=T(72n-|ZrBK)2g$#zREEXvBpsd?SR3"
    "BNZUkHBZe_r~V4Zr)mD*s`-L64@>pHo49p4IZbcA$@Ga=0RcdEE*p3ix(B9qYLQ8S&I4U-h-QF$vc1{eM8(6"
    "Om>Mj%ts3#}UhUjm834`==?*AIwMt1fO_Lg8t$AlsNwoO22}ce@S<L^GampQotkNwbi$$GD?&ms&D7$l_m2e"
    "PLnxytxD|s*5={?<X@4cP$o-eX|wt)+BjdzJ&g2h;`2Dq-M(iU1t;5F}&5MAm1J=|Br$raq!7%6I|z=ATCm;"
    ")(hm}dgELKS_a`r`dEaN-Fqx0Mam^S?N=`vZvr1dQ8mCq`~gMvLLR*gzU-Il9IL3IMFnEvTf~Unavo{=3!OP"
    "Vkof1C?H%Q%Sr&)oB0*30+{ECn_Ms(I`0fYV56yGjSw0_9Wv?XuPdN*s9U@db0^j!_u4ATx&#OKU*8fa$#|Y"
    "dD4)qyE56_Xm84%k!XO_R+>wtf~_q>`>~+DXboZU&w&ul=QO6>!<R4j_WX*O<vg2d!b+CB*oPL!dk3ewC^|#"
    ";CvW&9bdf>_bVTyqw*_WPEir%2MKIB@kDV#1EN$ZP0?T$|NuwV0*V7Uq;}?4`ciy}@?e6ZJ?z}quMRVBP!)5"
    "c>RJOFgHQX#++H9S#fA=};Md;Oen7Sf^vyD4iXI7tDbF@L0gBd$7rZfCs^YL|t1y2TpJdaIbs~t??@uSUn+<"
    ";D|y;(b($Ifh;z9^!MLx%1OCg@_LTVd&P21^ewKzW8A5VCMvkGq~=fy*ob<!XTuq7|Ni$A0;lcSM;L2R{uD0"
    "Ui}od~tGR^n#s!pR+GAM1!ZAtM0+ne5=euyl4N&wzRx28V?rC8s;1CW#hi*Ql(f-h!C5Hs8Jv$__bUdTI9pj"
    "G(&Z0p3A_*!lAs><u*@vI#h2LjxnZ(<r~;=0~&I5G_1$mOqn^bKN6S`mp8#=2)3nDNlWZzgd@}nc!*NIm~%l"
    "MDn(bIZHKC5iLMdcJ_Rc(vaay>!QSt(x=L}r*_fT`M7Xb~IA)zqQBH<ztpW{bR(wJg%B&P#&Uz(NEhDRO;@y"
    "Zj?in$1hcM>0$r3IW2pWXmX{h62sx9(A{50iTyct#IHp=<+P|N-3y<zky9=(?QVkH~*0w#})xiB3KRd{hxT5"
    "H@DT+F)UcKW!%vhg)b0Yu#Jw&W6GL*u?I^>#PMVcU}cf&+nZMP$){KdxW|rof@bX&f!k|Hi<_WhxcBTul^q6"
    "#PQ63mP_2egWz|=cQ32fOnHofjA(vEEd)w;-Vj_BWHL6n@btBT)Bw6^Tiya%mc;OL%1Op)&$LOYdI`RW_Ac#"
    "Q_Cd`$avR)!IOELwsgx8K54ML(Lq9!F`Rh=!x(9NzG<VT@zb&~4qWUO90*x#lwp3x=Woo|Rw;S05rz(xHPni"
    ")t_zYXQ6Z?OL-@Z&b;F2T`io~%uP1&>U6EC*sNcUzrDg4OWbrneOP}?p5N{dPUMoYqY2GeE^42O~<c<IH6=k"
    "t^ade7Df#^ARWI!Hu7qys%FZ`+9EA?TUMN|z9)Fkz>VcZk+UN0y$+?*YOkimOlZ1oDSYNXmaabR4E5KZuU^`"
    "Bl!0Z|Z2d_T}7?UND~>tz4M9t#npQQj}8dZc{=I|z}OV-sXe!$O%0UpORp9jVaB`<>GEB^jH!FlU|vImtz4u"
    "yI6M<Db#{KaX5Y%9zdA8qI`^xVkSZP)uuV*^|9jd%LGAxli))`0%x}7{62HJ-o0w$)9l}5~p?plv{&*-oq-X"
    "L2e=8axJN2B5s~2e|;mMT5yH6qWlhv*3QvqBq}Kn*p9pIDLXOB430M<)q_BA#3EB^=g-u5GHX+~m(3O36SfP"
    "5_f%I!?ey8KAk#;+fh5Vxq7Tv>mqzw0*2nOmqCdVV(S2_6%#C|_84;|xqJu}hQ9<@fHk|Ku>s3NU3>E%ld%P"
    "PxuP_UVfRC^qx2+ya=Meba#l&&?#OZKqg>>~X^W(rbM+F8oV$j*uWj@O_f{QtlU($MQx*z9mEW$Est1+jZ)+"
    "P?6x<Xy8fu+5yUKzU9iawQ)L|>>}PkufeG4`Mpd>Ls3E%+J;maph{OfSLYKY*svaZYbb%w-iSv66t8H`y?+{"
    "<=7)vSzTJovJWYqM{8%gQu^!#x2JhhNSyr$D^1JYbWV-IM%_WG61KLZ%6#em0)jiOn2E&9U12zSj~T?N*Nmc"
    "&Wj;kzpPo3EmMDGr10}x-LYY3uwNG@dOZ1%Uz4+yg2mZad-&=FH_EY)5NTSXgN0o=E3}Qu#?AI;*=09)buf("
    "1gtWg&Pr{!#Od2kUF*-)W9`Sayrb@nC$*aj%IeT4gVR;f2^e6;fvA83g{bc9$9?q3@)%O*7?tRiAGkFs)d8<"
    "^~-WUvlnQ#e8KUF60=M?u$_3B7wz@Np|E33iQB)>0Ld$wlq(k|ioHQ{_9e=YjY@q4a(H^Xp*fM7@*^h&dcf)"
    "&nzP}xk(HyMAABHAoxh(4NvmW8fNGaKN1xFon88zLYL2E`{eIPf@SrUkmBKjdZDm)Nn?6>T5FU1jY-3~WsX7"
    "Q0C*M?lQf(;;Hk$?~yd11HaBI4pWo^z(q;b}M%VOExTgR%UeLonx0VM#QdrZ;oE<obEXy)XCnd!?OPz5vhz&"
    "79dNmuZetJ^+OoGmFtrqDl&bIGm=!?clZ9z*>3uLt?v#tzq5kOp(=-Qo2#_yw&5d32ZOflmD?R_f*TkNmD;l"
    "G6tq^9y<$pm1FkC$*urG6aSlhs$oq1V_`Hq91g8;AYH&h<pq0G0yXn2;-<QdogZ=+}v*-5J7!?<S)6;IUq^5"
    ">#JYjQ;2c)==V(#o;;32v3>M0XL4W)<J;8%RsacX#gdf5!u-I%(4ChPWL_-&e;FDO1|alw7f@{1W3L#HT}^Q"
    "=eVCz+fhibzARqT3hCSuB)E+*oU$fPY}s$tIPMfCQ7j)Bs0imu^37FUMB^vGLTTh{n>pRC6)Lb#L@As;3VNI"
    "g{Fkv@*bk+@7dPJLVoH7mEy3x_Rz0fLop@v3k;BvMYU?qr^R6wzhQEa{H057@Gr+5*6iWtmWwrZCBM4JUA#V"
    "b8ad_`&?t8(o-D!IXKqQHbxTNPU;OxuBf?PBY;L93xqKO#`V97J|-NEv*($)MW?SUpNL?VuD&)(5UK5i{ZZ1"
    "X%aAJ(J*a`cH4%AdK^6K;RnYR%@fGwZ1k%d;uk?=9EW08|=9X(p5Nz>PRxM*5sJk`TEa1)u`16as<K*YR;ya"
    "LF;y`3`046#KZH$XBm~W85ATZtm<hH!sPYslvg1`8Rio7ZwxNqJZ(Hc?pn9ro=qHg!Ogz4Bl>waDHB-`ou9W"
    "-u}T*vmiG*OKO6^{C@5#Lf34A88is5>7P9q%1<q+>1NF#9d(bjMnTu4nJ5;Kz6mUNoQoy!TV}>1N$wlf`!M^"
    "-=umib7U%++YRHw(oW{P+*H1$5gf>1RhTttUD5l<KQCxhlk)SU?bubWFl8*hmkdI{j{~GwR^bpYVTxsuThD>"
    "O_R-LvU4KgwiN~tOwTa@%Jl3urXIAg^U8oLF@zimimAsJe@8JTW8g**N-ju&1Q8Bnyk``M%(&Wk|L>gqibS="
    "}d)sh;DJ(2L6ysL1KR4nNsHdj9$F>NH6t~Q7c}{oH^hVIj-ec-D76PF$zfZCY6anY1i&uQ}#zPAoiSHg!80P"
    "4G);M9Dz&V8(OUVD6q$e&w&v^3q7oN6M0-*VZ;Du`?yAuS^onR^(I_)(e%ocLsqnAn;v(iJ%h_Ff=XzXS#a1"
    "7WqyEgLi2&V&cS8F&(ki`Ygl!JewF~)w3tmiM_P4Rl?e|L}fPEHSZf9-+*eTsECA8p!0&_&}}E>@8mM+BV&_"
    "}AMqFX#yg%|=7%Aj7nnOya6hnkNT^9%?*4)8V3I!qV2YTWHL_hJ-SHEaA}9pNU|bybm?N_h?5!9fC)~wyV<C"
    "BOLcBc?18Z8bAXYET!t$ak8f#L-w?Ti09yzXaB1@1FC$03Ehd7qYNuiI#MGAdHW6ozVo8iPOleNs9d9)8fmj"
    "))myW(z!K=ACnM+VDRy|2qc>A8(^Kmfd+90-qN(GZ>zdR8#J$K(gqh<kGK$%*`7Vuw*QaV8m2*mm$yQ@?Zcf"
    "R90_MTCF58z$bYP_$<Ai8X%sexMLM5nE4iFjUA2Y{qhlh(>6J!9Yo;}Ji2F^*vrI6LIf*a&#n5aeOxJm(3P0"
    "LGFlur&{@3})&n1a3p6loJLa7C+3im{OqLN(wvN5d<K6_;XE90+_l4<F59WF&;se+9#vX(p}kpV^E|*fR72%"
    "~j*SNpdmf5e@M=DuI>r%LbSeizWiKa|&OjIA8II!iGTdnMf>08J^{sEMjPVycpxvM-gnSW(<cI;T!jd8v5$;"
    "^2NZ+PXo{rNi`><;(0#5LabLVC6P;E5DK-zES`8Y4p|_*eHn(j#Qi?(tC79KdE9u7o1R*cnmDl87UN8l(EGw"
    "uHHYVFGK0NynfdYn%nFvGPfpuvk0v8*gEGRB8fOpac8hU%Y-snHlU%w-rxi0kuHp4HOg?Lg5(T21eI+cZ^L>"
    "f6nFx3lWe4=)z?aUa0D&KG1=|(gQU7tce}KKfj!h2XuNFCivKD-W&-2BR@wb2WX4LRjJXI!Gy-jLe%FDLKfZ"
    "~9a%%8n?-B?fthk3-7c8^v<!q;pn*ZDOuHJ21@!Gs@R8&cldIRB!(g3ee9Q=n*uY+T(mCbBOZN4JXeKtzkSz"
    "xpMT?b#6}5`{0!-6yyJ2Xyjlt;6TwmG|k5_nS9NQS-(aHGiMXKB!lSSCoNo@K}p~To;YRsme+Jq9u}~=io#~"
    "ytqwUXQ`Jf7WX<Q*vRY*!$ikV`Y82ixdb)RS#Y$Loh%vB*F0UqKBem#CTz1M)jOy|8RmmIem42Lw8C(yRd)J"
    "q`ER~4tFYiWn~hnYcz6*D6r!K9fkztX2+ri#7>VQEJ;pC_tu)fM+I0Q3;J_!Q9$FK^1>u~0IBPn@`~24XXE)"
    "K+5i}KNjjG3K9KEJ)eS|(4EB}I2WfTu_m1<5<hQU9#JU@JHG7cN!QxiQZ$Q7{>qlzp&H9QQbcB@th1+Ma;oM"
    "s64p*M`Ph3GMF1F0!YB@ID-xy3Q0kvI$f_P$O6RyP@D6o_sF8OkbVHn@xj?wALxNr6M}FkGG-WXzuFhs*3Eh"
    "n%l<JehXUC@keFbl*`k#;~yCpJMIKxyVUK?3#TdBFvq3iaZ<HE24uM@o4Eb>F2#+Hp>GpA`izlfoNd_lru0h"
    "AZ62LN5e0sV>~V918@&j<8Hw>tfD5ih2*pJa>GtSG78C1$Vi1rAD{KDH+9UN`=pq*k!p)JO(E>?3wQ_~0W`$"
    "1nTKBso4js>zM=B7znI&J^#yo~+@u;{hBt7#I>ym-D!-bV$!aI;BBpiTUsG4tdQRJ+Y1B)lqR3nLPv}U(&^0"
    "_spz$H5o#_pOTp4J&5t#5(fn%}XG@amDw3)KH2`Vii_YqcJHoGQ6>WnqZ<meg>>zLtKEbHOYFlgUSwRTJ2L~"
    "D$>f|i&o#Zrs8EecyBku8(Shh#A|z_Kw_(oC{0Hgm<1U<z~I2}R|Zem+;aHhM&T%x3**U`<mr5bN2-sSdMZR"
    "DRLDDzg9rn&G1sp=m4a=%I*G?@vj^KKlj4gh9l}h=6jKSA(RWJw**GFOG7Xp9QbcG2T1&?NN3ulggQ&Q8E<>"
    "oXEzgBEXmN9z$qcS)goW&}5J)qZGGz4!6Ih49rv2Hft!n)JV(A%|)JXEBrfQ+RlPv998rP#3Hsc^Y+zBGqc8"
    "|W!B{<*H6*vpC|W$Bj6dM1S^zDlsxyBo(>$pKx>h`OlzRV!oMxq8Y=?9WVPC>t?2$r)kM^n&h>u_$?#wj_%="
    "v0Sh-jljhyxWwkXNOqre6NJ%e0KW1)y_U&N`xkoy|_*>grq{Ierf$!dF2)!T@NS~WKIY<8S3f2i_4v2RNHD8"
    "KVo0YzWS(Hfp#$FVBA!fZ|M=}$W9^>>RdI}!tgK<ej)I3{_hK1+u;nz(6$Z(_@T8oClSkRC*{65UyhXoR<&N"
    "pS@&BL7O4UO6JGc1;R{F9Vt_Ai|Fo-a^?e@IBTFXDdasqs95K=(*^nm-!Gh8_qr|Z9p?S3_?${I-^TH7I@L2"
    "T=_g<&_bj#rfFlqP?iXevq@18)WM8Yc*m2-WT};0Js+c`g5#O;h8qPBs3l#EdrE_|qG(WoyJ|w(i%;<1WG*R"
    "^b}S*KmOG}jscp7=E-6LH;lZAl9j3DI9!3YKIs-frv!eSsA};0}mPKS$pAGypnoj13_{p+eYU9f79!PD}7yC"
    "`%=^$+_OWyyy_sjl4vj6(^-i!U6)4lh&X)oxdP6nCrwv;XMtz|PRpRO>RC0@k2J5}VnIC<;Fp)?N{U_evqN%"
    ";;PM1Ce5>>!G$pk%jcR*F+h+*T;a<Gbira-1SQmWI+?k$roTv>(b;u57gm6Xm7Lu<sBSIMRC#zYUC^ltN-$o"
    "Xz)yi^CFm`QFQnz@c&CgNgYyY|Hrccm<yuSD@papBE^^IA{tPUbzJCh;h23Ji|nIIMnAe%G2(9PDz8Xf_|(%"
    "3Y1vvr>f)l#S3neG04!(l&yZTPU@g{iD_jCx}=1BbtdR!=imjA-Fy)0SA0M<z94eMyUy5qmS>>gQVA7{3Qne"
    "UpG;YlwMbr~YZCb32S={ZXW_<G*hsMkm_v<8MOg0$%>o$BbQ2cr_(Ni?X)pJWPfk<U|4Mv*NCH<`ag&-LI?w"
    "ysiTM6|bsqkJaDKnx-G^P*@%<X6?<3)_P8VBCbP^ZX@_Y*Y>&HlDMP!Fn#Jd$+s+z0g0!JR~{jzhq|J&ZS#_"
    "59aQdT3VfRmjst_=$C9f<HP(ma;n2Gqw$<Nr2jm#j|mk2hFS6D_Rf!inw5_-iXMRf3B=eQMP+64PGY7^@zvs"
    "1@7JNm})A5cRqp9M}5CZ{k1Q0W<;qRVHh5Iage3mwLxlGAHP;dTz8X!kVZ@^ZviLH0$y{d_s_y;m5pxznR1U"
    "G{oEMo8#ln8a9)3jVcyvCeg=Y=WeUquX|(FmT<bwM!(hOzV(JyWPAUKI^N)g_^pcMyLIBmt&dY^^7ro6ig#z"
    "tT#@RlZYrs}YY3;DK1qpJ7FUAA&agL<Ldk7PX;z*{;UZ?RdNPr_2_0r6u^02O!`TD_qbc=EfYVqMe)+2zR8("
    "*c`&o=PU?};FljtN(&B)WnVerLwp@^V-4KAT+ss}1%BzsE1PLnuHk6rs344ymOs74fm5yw*`Drpk6^*uwOIN"
    "olJOE6M`tfr+&R&N#M1k{;PHgD8U;+9A0_Sili0lXA9UFLXk8-w}ol&`7DTEryxpfU~Im$ZDi;jCXDeSp-m8"
    "AGZFfm+ss7y9PP))y#Rcg1_DKyUjh7T*T9(5}|3wt(q!ezk@7@2BLNOg2VI&C@M<`aK#6%BgtdaF@YFRo=D4"
    "LN>dYW;3LNmRYzirHg4czr+d-^1~5)G~F*9p+4bdKBbZ9@|vOrewqjOb?AI&jd@7M22A1Ow#}pREpR~=63rD"
    "ubadXW9jPpKM8BX|bkU*ma`p2wDkJyS%KE^zr5j+S8ymC9gf=Ud+Ug+PFim%mErxUY1Z}XksbcXh&S5-GSMU"
    "XYDjR)-+Muwj5lJJdDfFhfNzwy7$WOUZTQ$EMxzIF$;g@z4^bby{B;raNpae8=7Xp7RTR2-M_z1s}0dwgi9n"
    "H22KZ~N)z|BACe2!!vz$;t*^X84Gq??Dm{nh#GC)!0Hl{3ESrP^`J)-q>Vh>%yGi~_H#<ki*Zk(#M|Mn-cVU"
    "V~v#3XIEN$|wB6OqG7{h5<jDnc7*>LC2D|Xto1ZK<lC0$E*lDUrw&ec|O|vRLmQ6tbh@;aP{A|x6g2|uEp7;"
    "=n$cfq8ZxdaK|~J9%bxr$Ecw4ax!HPj=)nV1MIo4wTsYCz^p4Qox_MVawzY}`apR{{uZw`GqW5KA!p2o#iG#"
    "SEO5HXaK}IFjIYz=Bp(jUIHpnwM_atad_5^BtcI+~Y(19RV(*glbTHX5^$^#2SZh`pR&E>`C-TcK{HL~54c^"
    "LFUQlX2*>W-{0Rah)Cc~n4{grC&EUBYoOF*CCCfLO-(r{>@qK*so4(FTb-nhs+n`tu4JMB%vENn)KU@U7aWj"
    "%t`Yv5<#(317vwADVOQfHT6!0ggg{lI<Vi*Qo2SpdQQ#GiE{F|08U0@ge@y}T}q9)U06F>ymz@JKF#Dwa;U5"
    "tqC#@?n9e_t2iQ7@a9zmuQDoO!Pb1i0lnhf@0N35acfAmz}LUk&|*HyUwv+gP1%zj6KBhHRM~x3c}Q_X`|U("
    "hq}^JpXovgxr_sDx_h3;VW>3XTF<MAPIV=JL1>T|t*P>2{U%jVgA$k(sgYA&gSz&cP50Hu!mW?s?v1_NxMaK"
    "ebke)@mlniCSgbLu+W&c*Z45Ryo}GPuuyynAR<>Yfe#@sEOtS4{0OGeZkvUF;QmVVfcmS8%xI?uWRSGfSNsi"
    "~$vWzne>&)xqHj8ZiGfgkXt$KkA<UL{6&CQLUj0eR9TtX<$F^g@45cPd2JfRuFJ}=gFrw@ot=l$By$D4P`u>"
    "B!1$x_VNb&%cjf_AYgbaRjZ@_C0%hCG%Q<~@+HuDLuXs#?~lW)7)tk&a~l^n_Dkv25IM@;&|SB{r-O+o+qy5"
    "6zXcHBuW#uxy?!N8Bbm7Gn7`_z(y&*drw|pyt6rg67gS(^-4mQ_j^4MomckSP*s9SdTCay+m)ib3cg0MWD7}"
    "tQ)n)spyb}E_TS{!30gwya80m>p3#6d?yP=@koP-<_{PGr0&<UoYBa&psKOy-LGnF@GV<|#c)WlTF|e{PjKJ"
    "L!~Szr1(`-rErQ%!zWQ3bScTM4KF?6fF;iJ}X6=6Wsn+4~h|)IBrm(f<HDrHxPi5_&v}Fw`^=DJenp1d!ink"
    "tdf=4u|OVWVeo-J!^7aQB^rzH>QHo)fmcg-SHw>8$RED(s0x2q{5K>0tT>HNC>5Z)#<p;~zRE=-4I=gR2~kT"
    "_?_*JBKhbu236R0+x`XCy$1s4payTyO@1#N1NZ`yr#a9hlkSakBr*!QrvslrOuEtic=pFNO^m+)V*PszENR_"
    "pq&hQ^quYr(D7e(K=ykw~6Zz&N<#@o1A^Oa@=b!T*$d4VWy7&og|bNC5w2Wk)S7vp9(I#!&uG>C6-TUbj<rI"
    "$Pw0)4{fqk3{jF&-|5n=Y?7NgZGTtS-4$x5rQ%Qbd<NCffpY?%CrS|0k)Qnw0w#e5&=xWZSagIHMZ2Ao3)gI"
    "6m~nTWf0{RFG5xOBXJZBrQfOjsYa0q#n3LEKSI}k!Ir5P%r&x-+va4e8j%p+14YVCxTJrM`sgvQzfsbMWCEb"
    "5Jumz;*%V5g-Y6I?@v=SM)Gd5UrCWTRa8T^hG*3(2Kv0Q_s+SVY*qOyP{VuyYzsRUa-4TdeP^<aH-DO($@Cu"
    "i%hoNQ0|$`hnH0Z%$sg={q$4O{6Kg8^O#Hr3MX(VClpEO|-wts=fS)G~t1fNRk^tQy6t&Sz&L+m-&vOC;7kD"
    "x-mGrdWtJlZ6s)y1L}_rZvP+x1BH8gu|!`m;OtuQl_*G#`edgeJ3GQXjc^;Yv>;nA5{zuM(&{lpuxOeJX}Nm"
    "yagGT2#Wp?mp!$Pyc=j6I-!)DO8&J#SGxR;xQA#<S!=;`95p8H3U@CNrv?ZFlW^S#3WzW^3$j#Djn6D4zT2#"
    "bo)QCvO^C{$m5~;T2C42>!G;vi&P}DK_<P@a{hfvC-1;hAyuWH!@pj}N&-3w;<_04{?;s$>&hGBs5uuCV+>i"
    "JE19&`sx>+S>M-MKF7^WtcZUz~ECr+!ezUA3UU7FfOVUohyy6!>UP3Qw`ETvraCiED9WF<SSJ1`6y{_A0kEo"
    "0tpyWmW7e3<i10EMPZXWN_vzqesF2H6Y_9YMrwhXHGA4gNM0kRTmvwp4(&N*l*nxE+h5WBp*8j-QV|mqx(kB"
    "9WJl!*R7^GYl0p0J@COS`RYJld)#hy4eJKjpn5$b$?=FOXv973R^KVbGcsxG<QI+v?rLHp7!vrnviSfr75{h"
    "ZY&s{TZrl-y4CL}TF<hpE^gNC<otS`>n3J=Jy+7cy$JqaE@7(*EHlLWa_jL{xBc)TvOn>^w#v(F>(OJ|s&$!"
    "v5<E@1g@hDKZ&&p<TN984))Y@1{PeNN5rh@r!o;?b9QakobA$x^mLbs1APqzUsjDk>-XGSo+0^9lV#7dZ#WA"
    "!(2KI&OYxPa*tFS~rQ_@9Cb0@yt*;0E}5KhkBH7Q;1F5x<`7RAD=L^nt1vm)8N2&3xgtG9BK@Fo=M3t}o8>x"
    "5>;_OPbK#_U*C^Gw<@0#rE!TnwW=+s{s54e>Wj_+Zh*$Q2rwmim{NPRy!@H<k`WI1xu80=f!ln}}RN#dz>P4"
    "Xo}&k2?1sws`P(b904UEO8xfM2BL{vLi*`jF~M}G1+Q5aa)H}Autn3ne%n%zo~G(4*wIX{+;?`R@I6=S1-Dm"
    "y{~kfZ(Y$v>CS+n1jh3jlkxB=F6iK1b*%!#nX=JbdBfS&M1h{>U~g$P%hL;&FO3#cR#)k@zerS|k-j$L=i<E"
    "ag_^QYq+E=gm6`eCD||Bf?J%z&BEQ>gfGNugXMSl|pJa?y9EOCh77y;=C8!9`vCZQT<n9NlUbzq{&RZ#1NL&"
    "jw1}p3Fi=c5y;Lj|4x+3K5<VWcACJ4rmJ!qP+=8x~=3ekbiT3vI2qSw%7d~%(oUPBu*S~($xY$(h_4IQH!n+"
    "m}Z-iT07N;Pa7Sc^62_(QF?=*HjPd|M2Nkx9Swa%B$Tlnth%p%a=#Y%kU1E5XJmlVoT))VnH{p&E@!a=p&Qx"
    "Hnw%9qFLfIahDbaOdRYhD9nnz{TO@5!5Nmli3_g-jp4_Cd+)9u>{;{pdpg3(`_58>;BIe{GA?yjDhvYWXPZ$"
    "`PNn~u{NBbTMjD>L?~rk95snqyN3ra_m5u_G^)q$qB%q__FjQ7alB@0YYEx*K7~0)wDY94gn^)pBt$#TnnnN"
    "sT4$tjy*TR;U4;q~;4)N_N}xYz2$MxQyrvYV;i5!TFa`SbXnxmY?P|;6NF7#_h=gyOJH+Ft-=ZHSU*x>F{d#"
    "ac5xbky)&$T+8~Y7Kakpo}(dF-UC}JW<-C}8dQwc~6{m~pt3O6Yxm?5mrqUg8qKaT=p(GLeZulG)lc6Rr=Z;"
    "oF%g7b#nn!pZ{A6F<~q{H61yqDcBIATm9W50V^=A=TTSn72;PbFn6<#Uj-u8=C_s>!PF?zvv{<bF7_`|16Cj"
    "=Ke&FrT@8emw;D;lcYa4iEO|kCVNF)BCYH;Z>uIy9V)8$+gKGdEAkoYKquWr@0fAr89c&1U0zW;au-T{9Oen"
    "A1<afsd-#tFIh0~SfomBJp91F(9K=GT{+cGBN2ik*8jU_MOOm6F+G}hRp<Wk-fxG$?!CAV`|IQ6L*DPS(`<^"
    "CSy)Y2uwvNRTq7;Ivm`0nk!e<BMOP%Csyn1c5HfdbCyB}e!F4+BP5KrbRdNwc)cjq=hUiMhmi(5>7-t?TLe@"
    "Qnj0KM)rrMdgv1ub^>;}VOSQ=cG{_e%+=>IkA*SsD{z**lVjaKlJU?G>Z2&|A*_d9SQnD)Cd@gwQ4+2TJMP0"
    "w1n<TXm*iiYd_P*rW0bhw=58Lh4oOmGXFhTDoKwOWNB#CMX$a``cC%#X->q_Z!3j&O+^o+L}K#m*e4zEMQn("
    "L#2P$lP3-34A-im}R{7&#6q7{<;;nUCC)1A|*t$A`Hv5OScl8V;v%X6@FG59_XZ4RQS%f<2g~0cS(D;Fy59W"
    "EPEiZ3*GH3;~h%*j4auq_s6r&)Lfun0TzjNHIE+ttdpcrmhXg+EcgFilc7lP{CATo1s|Ih-K1{s(^Oj~fs;S"
    "l>S8N?UJk%?XW_ooj3M2_ZJ637&gbwTLGJTvfA_S3Xb&$A6QL_ovntl>Q2E~IY^G#vl~4I6GQ0F!&X;Mm4}u"
    "$(M@E=cT^VP~X_A^=oi8JrfH)Qzk%gaROK@}j(&gh7e3aBWS7P1WIoREM^$KOy9)_O`hr~xO^064_JNC~X+Y"
    "wrTK$g!s2X9`zO4)Q;(g)pVe4FhbBn=RbcV7Gz^rquC2M7BHzrbHVzdGDSak=T?qkh>8wL%6?Qq{Z8{Wk}{9"
    "vuFDa6hskc%VjyrlB6~9lYQnp2%Of8RF9GtNyN985myemvP+?R;FO9E50F{jdBhKc8h8w1dLVaIFPE$u1kY|"
    "$OQq&k;@r$2za8EiOIu6T3yTSbQjBcGgund5GT!!`a%bHMjE5_EtB7qV+BB0%*#s}M!A@|AbFy;msR5&8`}f"
    "8+vTREdgv#4O~vGt6~k);_yMjWE#s`WH_3*1*~=T_#c)^*8s`Q4Grs7m)#3jArdl8>$qjS{m&qma;J<aMR)_"
    "F0XNhkr?h@loaKkj3=pj)muQvMgevnlo#Ar;97bCvR+H~h_xqfynP|L2z=BJ;Mr;i_+BusP3%6d?=S#)eP1Q"
    "n*;36VIhbayjDX%l1iW02|D*=#ny1huGM)WY3kh63|<v4=?5O6)-K=Wik^^BzV<fCT8$ozr205k-Ei6DLTU;"
    "^vlOR>gwnIOXNKtDYc`ue}}HVb~g&TAgq~OV*-sq`ai9V0F^OBhl?-i7GYz1~MQKW1N2i+AQG0&OSBtgRY9J"
    "AU4170;&eC<Lf2hq8h{=2my}oJB;x=ORFmC-9>}AoaM)gtf4T(qemp_BlSWg(q#GMoJFXamWLzdkE4HH4Mo&"
    "h=>S?YHEmX=@i}g0Ma&6AmaEZDqH&RHnqh-jnQbN65__-hJsMD17a6*g>QV4CF@|mX5!`VIJu4{FyQX=~xLo"
    "J3nFzBbRIn?SnVa+r<SmUg!;{Cc28LA?u4r`2_#jH0PnS@rh9K)=U1j}`C^Yp!X&+5oIGDq6PQ`9Bgu$B(25"
    "{?wG}p_=*{nc>_<YtYN)f!0viOu}Psu39?6#sD-5&adJ*qHuJd@hy&FOAxzT`6tOE}Ngz`?3Or7Y%?kq2D$J"
    "BF~o$Z;;n|JkD2we3<YO@w^Arbk?M;Oqe+$_VZg_&rq$b}5DyRsj!!JW|^staLH<21$U8M$m(PE-;XD*1d$A"
    "vZkA&Z%|qoM6j-1IT?EI+Sf0Z!p4kXw_tFbqVeGMiUWi1&k;`kj=*8j$L5pC&`jnOKBV;DT@D6uB7I?@bQ3l"
    "Z^=g|oL$tj6u_ot{@7`q;&#_WupD=p}e-;Uen%X&Pr1=o>m_f?CEc$RAdbJO#_**SZfNnVWTVu|@l&##@+T4"
    "1aCePC35$x)JVCsDb_PWM4X)!=_i9i?0Pgp0=RtOAQwMHNM#f&k>yOR%Yf&nY}&`q$kZX#6yss#Z|b@5$gr("
    "rtwd_LoRPA&=Dcx4Ax>mT_TMgGrDY!fia3}v-<_io%r;bf5jkqrs$DtLPT;I};x3y%NVJw5z&?;v=VbUWZtv"
    "=jUXDM;3dZZgkl?5Nq_Xp=^6+4|e07!#-$TGCp0DdaaD{s0>f-Pbqo?y)ZmzH{QQr7T9HX#jFGAgSZ-NQbU("
    "{R;*gHL7Fg==!WLs6ayyHijh$iFirCSMYZ;ysV@z*qR^}hrRK)(jS7FE$hv%17lK=G4onV8R>TocbwQIi|*~"
    "<QS!{0e)#+vJ=&>+Y+qo$Y}h_D__Ns>Q{8g&xNznGEFOQb5Dy_6Z@AIdh$ol&JyD?*<N?DjW9F8f$D0Nhw1e"
    "B5qF3$Isnk%Hc+R{72iqg!c+wqUT7E}wkLvrK-R%v;em~4c=lv|{Qh3(3e^WJ#T)=C5nP<cKC9S@nmh#j)NZ"
    "KWi3MZ`>RV5P!CWMo+XGyc(=n4u*FW=hSQZkVY>H4F1C_F<B1@IAKHoRGX&GRXjGeD@83tatij+I5-k;5|}Q"
    "_c8^U8->coW2+iGX=;Gn;X%LpV`*{WWQuo^*P+G{K#+e0*v^E`{;6>%ope7vVqZ5Mi`$o)0%uRn{!y)(aHg8"
    "9bOEj9+zka!<(i|KEi@?rKH+{9`j@Pg@mL#tzA!nFP=2?DA;99{e?4m6h?|!wvnA~s#}ht+A)Hgp%1o`ih8("
    "fqB~`so|`4EtbpdOXm?HYIc}+M&@-I+_kqf5oj@9k(8BC`yzRPK%Kx6bJD&tF#LWr6QCZ&+)XW>SJ3V8`d~U"
    "f;dvo=(=jPeuM=K6Dw2LicY$6^-2sMuU7+v-C#w1m2*6whvf$DTwbTpkAin6FlRJKP_z%>)b_$*4)Kqx~R`s"
    "kwxq|<1(fPrte3^B|bmh9ljOWkyr-OEW2#R<o(4eE=Z6Hmvr7=j+&5p{l>!fCxm&M-G|m@w90pV9!(gW3`4I"
    "&y=(yZ6y22g50GF<E%~aM7b1;qMDHuf#}W*2jA{UD#bx_`H~a0rMP!SJPX%^V$AQ7xj&E!*@R0zi&MIGj;`+"
    "5COv5E<je$FK>cSe>tY{QOS>>`c4+JUfy{kha3AwE+M}+D`O}Zqfv%r?tI3?2a*BdIf^rI1whk5Fe>)^FlYv"
    "bps;M|a_O*Co{>kllh5Ywn~HJBE<v?ysFfF>50NxlY)rTzb(Jj89MnC<vR$0?msV`OhM?7VxLPQ}6!x;2sHC"
    "5{#-j7p&BmWT^O5$xja5A5W3{b!8n2FSby%J<9}y;N=d*qZa$`%s?aCx$1^FxpasU?GLw`}jH@@()t!p76CD"
    "gHuyn<tOAC<y6W{r)p$WxDH7uHlM=t2x8WNk{5MXA-RK`<S{&DFoiXLkk0Wgy%*#%(RS?ax`6zvjX068PbZ0"
    "u4Ka*jQ^Wxg|I(o7RZJ^1y4ggV3u_;TP52hr=b>eis<R6vbWhV)=|gg?nU!L%sc!U`^kRcXv*AULF2o*#bs*"
    "|N3U*x1EFiSFd(FVGciRrO8wH?<2!=rTy+-4tEb<?VRqZlquXEKepi^P}U!8h7X;b9`F4A^WO3CU-_w%`7FD"
    "FYlc;^HYxX8Pafe@9;l~-<JmBaqq3U#PH3TET6V=i;DP>uw*z-NF9>qnM-&J^c<nnPxS{2TMF0a^j1>kJ2JV"
    "2uwgW`c7qe_Iw|)Ds((W~CCV)AeE6i!v;+&%Srp!UZ$1BUjwIb_{QyqZM%swN_!M&19$mKiBf$xzYm>q_MQ6"
    "aSn6qB0LHS;+E-Fuds+oX}1@EpABQtle7FQRjKGNkB~lJp(fl-pm??Wbjl8#I7e#jaZw7g?*q$Fgc%T2F|E^"
    "X?w0>F|*$6D<tH<>JsOP?#bE@b#n3&HtahZ*gnm$nyPHdYs)4$!W>pBu++-W|m-*u))9rP9_&~n?`D&$3m@9"
    "OD3#`|NYi^)vK#pEo|@IZ|~hljQUYsk5i}4^LIX7fvS(1V#|&ada2_h%}WfD1NL55O>MKW0t_}?r6+4GoEd-"
    "Uev+UkZ~QH*#MP%RY(NV=F8H~jSfASDo54YM+>zO}+xT^~=6QZO%`Mb<tB;8adhb(R!l#0UXO5DAfv*N&1d4"
    "3wBm<i@<11LZ!Ubw@P+h4`foJQ3=Mi17HhiQ_RTn3MB*&sWxsHU(O%NRXX;YvM7U?v`lz`BSv3z)}s16r>9c"
    "sSuFS_p6Mz;noGb-4{6>h$vX{e>p9pZ@4fnQTosc%PfZ66&SAN~q)V>(7E)?rrhhK>kU-HoX>w)#BjiQ(owX"
    "qB7?)A{RgV*_>uc5es~e*(IKS8DdJ)QpmXT=m=YJeaBG6`zm*B*j?O$%xnmipn6Ap!)I6SSNN_Q~+=EBEMpq"
    "QpM$2L8@^cV@>kBw)Y}LgIRfM_K*hBh7uzKPyDFII*~MFt~&(6Gu9{p!ob{C+Q#ir8~B6-gFvxda8Wb$1LL1"
    "SnNxB*x9Ea4tY2n{-9t!1axi<5u2DxuVps5cY$>GZmyD`R=~hFi6Mp@3UKHZ1AYJt^Q8iR5osJgWW&eI9{b3"
    "MQDlyTdK<49F;QT+Yv`Od^qkHP!Pd^+v{d%y;YYZYM)0QiKHq#afe?tt$>2$oDZ;S8S@_4svGOaneeK^!J(~"
    "YTgkxRe$87mJKpB4s+lnhVUyLoja9FAGb(Inbt>gR+k*bL2~c&d_y-)E6ijSH(AI7I%BWwEd!A3d=h1dyQ~<"
    "4W3k`V`x%EUAf=AGmW+dD4nHt~?w)rS7&#yKy5aUL9}$cp4@nQqP@}+Epey)u?NskHCgG)~+z{9*qhp;4Qe!"
    "z{Xqy0WG^(OoZo1m5R&EqnedyQKWarbSthJx?2p(aD~dC_KV_Ow46n$^b0wr00F2`!E$INNA1`MSEbr}m$<x"
    "}8tvs#-N$Vq=Tv0`JLvmU1EAf5%AKBd-aUmZ2bv(vboQeIfK1U<<IC!}T;Ai|#7_nWb?%s-j0oC6l8nW{ZMn"
    "AL2HI1RP|&lJPl<xNmKaP^LH4W;yLC#gw#LSna|wXp%4=R61lUO<uyUvsEtjK_dg*F8;mMOg$?_#fX;0JnT&"
    "JoduGn17?`@_i+)=5~#qS1GgAv<+Z}6|H<#fb&JZGXodeRY(3WhHObRU4Gth)>>igqN7`h=7COmgvA&!hp{b"
    "wUvP`wX==^`CQ)wLUx;e`cT;t^mVV;Sek!_yJK5#7T$w`!FTgIrFIQB;y6pI}UwU4G4>T>HwrViGS9SY(B%@"
    "JQtC`O%>x=E8clPtSdi{xGqqp&9rp}jtO<uSxQuIP5E@vE7g1WB!8VC4P)n;IZwPB&hgP*17(#J?HXv)EeKW"
    "zvoxH7@b{J=$odGv(z7sjFh8j|k7}u=9h!>9R(Q6)4>Vy<i4muml2D>r3vq|`y-ib-bo8!_1ZU4W!PLir|5M"
    "+*)Q@BES&f$9-hdE6W+yyCjLyL8j5H(cwvViFlHOz0IlDcOcbG{DPckRy$uDnSnnMa?{i_M+<m3e6+6ZEEw;"
    "a>Z+?iTt*y|miG!6C~beZ`@MJO_89boP!;o`|Fmv;{IKG4R)>enz00duB1^exHrv)62rUS<<F>m8d@M+W!}("
    "sGpNPN^l`u|9eJA?&FaeZY1e2GIxU#sm7*<LK>jb2I(w1C!gcXF&W9efj;b@N=;FeEa|l-`7iyJCU)&_)!>X"
    "qIWq++B7IZf$Cb5X7%k9S{g_<s9oI)`dQZrUJ%C-hs`^N>qGL(oZJ*MG`Ks5;WkLnDD{AIicdT&Av?<8w2$e"
    ";<NDdfl^WFadI_fjAXv_Uy<j4q$eVkBgF?Y~it;(E0i>D%xnxCnq|H&@sO5)q1!3+W(9A2Nh;3p{6^I4K_Jv"
    "~Eq<}I<pwE-WdzJqIz9hVdn+FtxpHEMZXjpxF+_st}c@{Q8cs9ARWSSZ&!+L_9#C5ly+K=Y9nbOp`gqZ!6^p"
    "8Z{m@OB{qIjnW9K8tQBL|5_yOahtqd0_el`bk6)~<v(faJ20u)N`4C`bxkxq@a4$j8nKTcqgO1%pc`CvR{Zp"
    "*J|2D&Y^JLAAt%`r@s1_G1P-#RYXuby+(F$?2nF8}`BN9@!*+*pkN?c5ZMU{3=Nt=atkf`-6jEp=&*(oX6A="
    "S6v6g33TWiNHRlDIf|shZaMt$;AXUNsE+-84A<H6)6>z}Ysn!4AEtmbdGC#&v>^f~Of6M)sT$4n=)$fCHRdZ"
    "m4|^Z-huXY#o{c7@M2BCQIjZ-oXiJQ3e~6o&w^i=28L<BCs(rBj*?{4&Rl{OYtQo|^YH$k;E~8QP%pOFt=!U"
    "T=eA8zyVEX*B+EFEFwVB5%_5ziG3}NC0HyHl6yJ9Z}9Rj!&W|L*9>sq?T9}K4{Nj%cdq?a{j@M#gHV@l^uCz"
    "hy&DssOe{}UfY?p0X35Lc>*yz>j{6r;{z@9-*@q9#}ICkW>p70byO-<iz;;D?fe@%@)_*y1Hro->ed%f2I~Y"
    "LN|s!N*eHS&2pJZ|(Xxe?XImI+fwFrF6g@{3Ajs8%I4xzYY%Jydo>w-9L6#3*Q(Bh)qC*k*f!VF-@qGX`Io3"
    "+QqTx+%zke<rM9Rw<xG90Rci=B8<ZrV5vj_H^lxsK`d%l^dJwPB#+Nh<GHS|^Qf3i$VRV3$4edI0<0W5YqE$"
    "^l=(7KuDAqse`V;*8kL?sV~}HxiG3esIN-%}&dwyu{(v%sp0_RbGP>)MoZ!C+3WVJDK7{F)l*$CxKYuOgw(&"
    "s}k@V?9g2+0?^Hz`j53@M%X0^Wq;(et!fWH|16W4|*F#px(9Nd34!udr5IHYexwVEMV2IKp=6F0!>K-8KIG?"
    "|~BoyYhvXs;AxJ<xB}yF_TC{+MH64AyqPyUC^u6s@BL4IUe!o!fYuuny>ODE#y%G<<&yYCJbVPBex-8~)WeU"
    "j^=r;+`-?sh^KM+<2?ZAD%<#{)Mv$8~2=!W@0OVI+yBW?_9unt;z*lbXCI`6mgJcB}o^0P{qk&hXp=@aymc8"
    "s2x>D5gelYjM!ez!Mwy-O8TP-%Pv@IIsnQz58(tOHTopXupte>K$To**GfgbMH^>}=QNoAD)goyTTJ}=7*Ji"
    "a38={dm2W_&V{jQ8OyWy~`flo&Oh17S)`T?$AkqE+kapjvU9&=8M0-=L8Zp9Bw(0ftJiA7(hoGP+l`DPErB("
    "$eUY9_JQ>q_sxk|_4W?a)h&Vd_ETb#krqK-=-HNJ8Oi3MbB?iW{o;@A)l!ldvJ`oR$*Z=XC=H&PP^2ylV=eN"
    ")*pGCdHek0^-VHn1ulIP_RSj&4a7XmeF;I-lf>#+yQ*^MZg+N7)?yf-)9p4guyeBEx@l#M)4lFJ6Y)g$%1y3"
    "4t(*Y)-W<|IQ%L*U<dseRM?!3Yb*x`ay6xi>f$a>c7uHAsb_eaQ7YtHWQfmm7|ul=12BO9)loWtuq1Ur4X)<"
    "x0%ADb+-^D2f*pWcvzHCCG#Ngj2fwnZkuj!o)sVsYmLe>fFBFuGo8N0axp4yeM5LS>dChVA7Tp#+`o~JNj<|"
    "Kv_9%W%ope^)LL2JcMAE-Y9GD>-@op5VjIuDbfT*Z45DXzCfZ%&zv=i=znvarlRzJcwAyhir&B?rfOtT7zSX"
    "u@JG+>?hfKQC*a-kJtJJZp{Tidd;U%&TNA}Y`76JCffB;1bq{;BtdbsLMb^{&rWuRr0P`{wm$FWs0*vLToh9"
    "<%Q5A@gVIGbj7lv)ZVb6x!f1>ZH-kaIGJVGo0Q1mG4VmT2*R+;lNF)PM%U&r!BNT#y|Nuq^m8hRfhz4=(%x1"
    "jE;BJE(sRSm|;V5QNklSWyCMpq8Gpo^s>9+d_p3zK6Nx<$#sfaMNomMsgU<l}1TK5YV?UVl`ne2E_%q8fF~z"
    "`+f8pb{mx~8Ul2K{!m<xM$@rC9^lk*DF^*aUVS87AZS3t<A2>jaAQo>9MT8+oLQ-))UD0f8R*dd;UXklad>1"
    "!uL(od?7iCG)kTb4VdxQIlusXVq}4}Jg1Kjo%)@~UEN*X8m=@%UXkt*ZkyQ~dO2_GJ0ixIx!+%oRD!nqBaKb"
    "o5;{;9<NIsrs;BM)oOQwWqBZy5<FJ8~nTL2kH&V?hOx&ZEz&#HcoimDmWX-V;w`79^DP>bS#tHNb<k-!nnkP"
    "hn6S(_Db<r(x{EwVEpwTTy<+w>3oWB9zv>B0YlZ=&PpE1VMi4YiE$AQoO+Ig1~mkk%@r^vSLB#@o;9Zj;JcU"
    "5L8YT4<S~VKOz5*h)@`1~pSS>M#&S*Pvmpljig&Wazd4u#C!@zE5-H*a_++4Rs0}q)Ki?fLvF+1i1x@k4PE>"
    "D+?>t(t4O`LZA~u>b6(#EdgSiVORm^biq)iBr0RDA6nQ!N<-oKirmwR5A@V=H&@Fz9fOkP4IAal7W+(NG&OH"
    "DHbVDx*1X6ueGNmUC&6qSaiw9&j%ooMZyJtFWtuXD=|BpFgHodHD4)B{Sf7W+s%8_bWVIS8J=`$P)`Nl4H-s"
    "pw*lP(Q_Rol7nU7F~Ah2NQF2UPU;W92#@%X`#V7y|mBwyf@R0OZp*mg+fCfQla`Mgwzzj{W=9lEq&sdi^RnV"
    "{zopEKr&M-PisfOf|MJ?jiCu4mhgb{A&`YLW0Q#Sj&hK1hGMQfOs<tm!FN%};=ffYv>DOgBXUQYw$^XTsD)m"
    "u(#JM$ws@b?s<{iAE!co4iI*SnmrAWR<2QmIY5)YL-jom9~15IfEfUAFV%YNv>Nhtx|9TQ9u7Q+(3K7Mzp{8"
    "dQY`b&56{KZrmbaNcSAJjn>Vrx_e<ax_HGb&D1kR#<pfPwEpgTL0%B_S4qUw8E`}5qnr-srF*UHtqvf?xMuv"
    "E1gaU){)jwQ6lCf+t)>MWqLA^DU0q3L8G}lzdowKzd*(_|rKO=qq#JpfNNAh^^C;k1F(8^AG?aV*ZWi8*ZfK"
    "T7=l0OFZ^dZ2QAt(+5@y@jSg74rG9*W7aEH$*jN`mUa14YO>m|ZmrdxFA+PO>~s0N0)R1%p?gqAMWG^`#5^r"
    ";3Nfr(!yym{$Lf|y(ZKyEcr#36^RlYG}Ocx$!TF3c6^RFG|W^huOa7q9f8uAj}hg6k)P)h2~i9G$f<Hm4HS<"
    "%?B(vbFC>I>zc^G{%8BXywv;@Y$Lba*PIb3}CwA6q49Y1|oDtyY@65?A1Jy^ZIYp8<iUqvDzhMnWv68ObcC-"
    "M&%Kf@RE%$4Y^mXa<H`iE!pNP_iHzRy`<*dO4G7u%VcZO)blU@Xf`Iqm91Ahc=ps@TnU<wqo-E8AyNwVEc$1"
    "(DzD6Hwjpg@!jBzpE9#Tr=vDP6%T%;_?gB=NL8I_Uj4a^;q~q{g`nE58)+4&t8joybcNs8z_*U(Vaga=FS*I"
    "_Y);(ux;OM8#rFzbWW%A$+uW(+yF~dqGkp=ckD4KeDHP((5RrVh0X=-(DU0}_*$d)C+@_SC!GT>k`0xJZ)c~"
    "fv}c|n}L>0Q%v;(O!3;LdjUI8=%+8#45z##n7V3LmNsq%EQFp|~{G-v@pYZdk^T{euE~iCKzu-<D@g$&c{H;"
    "$gD0!m9WI8IW}5x2em@9*e$>8NslpQpymm7Kg8o_IIiBwLd1z0I93TZD*>6<IpXN<qua=Qy-n88i*;c%ao;o"
    "I>)b9(jbtZjKhXNhwA56Wsmw<qQD$JeujeCvsNw(E^uwqEPa9(wDDk<1d`S&YrP8Qs$cAI@8L#mmm#ytHy-#"
    "V)>mQ>2~@jk%Y@5Q;k+1ru;V{PxikiB<}cBv_PR6SbXOM(x6Fnoqhf}JKs(kQSj>!Vy-@v&tlbn=QAt1#8k1"
    "IAk91H=jRC2Zies6UOnV=Ds{3}R+6OUA8y+hONDB8*H>^FFAra^)sGT-0fVTk&+@z6TQh<+Ztk4UqKSPLm&<"
    "x)z=8R)a@gTg^FoTd~V}H@fv*S=CGT^oCoV6+|Elca45K4MVT1PZL+B9g)fI%O3vlg$$YI+&ih!O=f^upll&"
    "*iEa&<kd*6B$}rL}bG~eabzHYsvh<@#wD|RP!kUYgTq{WnktP(Y6~nsgWrmz2R=IRCe@rS-K@)t>AVrJIgY-"
    "R^m>>bJJ3#sj1A}%<SGi*_J9(5dp7{O|F&L@KSb)lsfW(qF2hBd{))z?GU*(v94j`|H<k0e%Si|uqvL#IxOm"
    "5=8hRlW*i-!_?>IB8kLm@tU~<?K!*Bd0lDU5E0*ml%_sIU(1FSUm^k~y{S^J^Q1HopKLn!u=t<HsXzbI<Rz#"
    "wG^0XQ+obA(R%plm4j-zIuLK$6VO4!BBa!5~4-(_OOQuBcNCx;SI#4A_2bHQgDLcoB{RpY&M!90xXvI_mI8_"
    "9LNyL0&K?(y%*Z`*sPbs=4!%4f84bN~0?Z(a~ROQxk^ZkqoAmWM8G3nlJ?Fj)WH*;}jBQ79*LO-?DVLL4}{d"
    "zeNBsQq*B!_jH?l8T1R<&4A4fW|#6-HYJziXn+s`*B$4{Nol&zx`j%9`%9OU4->Da!W1vx3-z1#O(?0GNCh|"
    "{2!1c>VU|9W-NIDirJgO#=rj*u<7v5HJB$#4+%Yk$0ynFxr2j_xQ8B|aZbG%NVis<R;L-nh0Y0FWCrjj%S$*"
    "GxO4$AF(n@8P0MgGf^b7;mKf-q^Qv8p?|Lw)JUkmIwW{~jBBTb~%*!cNi`L`gPir?a0+73KX;kdHd*-2&pX;"
    "w9SQp;2vAW<Kpw<B4tGQeG6dm=tY+RX9F>8F^z$q;+LF?4BLbRha=s$M}49QC!m{$C<_I%p6sU`afy5c+}bd"
    "xB$QTy-`9^cw@9)TXhWdx0KZn)lC9LZA}p7UI@vo-+enf%9_L#)f-J_V)d4VH%+=5L9me10_uq;OJA2`rqi_"
    "*>4CFvsfPgX9kvxyY({EqncINh%0fyX6^~-OJ_pI$OB+wlECXD`M#y2!Rse?Ca+x$Vk9FxOX<*5Sa$;T-NXP"
    "D1dgWS+35@Nd4CM!gzHyh@SN@{QR!kTxd>e+YLSJBH~H2_B5{Uru{VI{cTn&rv-MisA5JsqKpf0ZHq-yZ)$R"
    "&jj=pEZ9NlwlK>aeDIse_X;XMCgbjsC6t9zELG&MYYh%qkv75il%(wzdNVk0~Ot8EA23`AMo!V6~S=&!}8GO"
    "gP|E@;qngRKhrdgp9&HmJIl8joly2RsdOC<7al3yc=92N$m>D5&6(xDlYY~i3>&daQd*o-<C6HPZ5w%9&qao"
    "m3z-?1;=AG_&N8I7ZVKioU;Y343a_u=p$x>K6OaNL*BdZMgxpT?XpiTNemncmh3a~!mBlE}kUd0Y)M9CKqmC"
    "OmNEgBCwa(1p43ji85f)k`)%sy>Xso*m{Uv1Z`0&28f#uZ$f|*R4$xa^v-ga3!Ld&_Krd6>2e{f!vb#jHGfs"
    "z0Eu%P)krzr&q@sCX<VsBrv+kCu7bo5(TE8WQzE+rBBqBd%FS<tx0)+t_P+z|1ppp()sA7;USr5FHXQ5m2rq"
    "KI+<a0Pc)<uF`r1%F>{p=mIScYp&3MFk6q>{TuPP3q5iOU130O}U-jj%fv|mT8LTK1WH23G{a7=JSW|Lko5f"
    "YG6QpnV*f*tj^#2BG&>+FZvi2Xbox*eF#2Qh_MiWS6SygoA7nbj(-hezS{Q`PY9mNt#@W(^dU`r2Zk(V;dT9"
    "neF+zx(ztR<KdAc3X?4m2&qg@I;CDxiCdxWr=JL>u&@i)t|-MEi3Lj+~%abLSsi?y06uD}7K6v5_img-*U1y"
    "g8$DPLpg+=^Mq`oT@dP?Y43J=HP%z)=27F7jpwT<GzsH_XuL4KBOffsI6TgTATd@PEZTjq8V$Ub#h;uq&|%m"
    "u@PInkHg>sCX#Jv{`_()COhG9<CPJQgfKzPro%`#-`}XgE^vg~K&c*5_2U(V#M*9N?jdhpF|pD&9zy8DJ8YG"
    "(5r{tr_O4g5>c0kp*97yFXT7cSFdqJ3ZOltXq+O8=Q6J@qaXKhZ_qG~yJ2`YmEJq2x)A)vo>#2rMK?<51LKU"
    "x3=x$XBCJRrLJ}{*43#l6e*)Is!qhz<2z{YhYL<zEv?vN+nQkEKFrhF1W2@@r6S77@L?m2zX88cxWs8gM9<?"
    "!eT^v4IsA?JvojqbRL9A*uEX#V^Za0}YL@G<B~_L1mCq^trE(nHW4X=RR;xuKDBc9zi?bZc65V0BjwbI-AsN"
    "S+f}Osv3ieh+99IBX*5-FQ^q7D~Y`runGjJ*FP0Q?X4;45?9VE9!aQV<;6HXFJG<A*bWq0bS>;udJhaNeffI"
    "fDFnjz+lB{+0IBo9D>xjl7KOcM#oJ#>YNn&XfjMVp!J+tg6~!N7eyY*L>NH(n(PR#!s5#0lvZ3EBw(I>O0+k"
    "0xlvmFO^c_76H{C}aVV29Yp4il-KrJ?`cNIogI6ye2@vgzVUqW~`T#GWtw*@|TvLc5ZcEH`p-=S7p2wq!)W#"
    "Kw&Mm<Ah-iI7Fy4)`HPSIiH~~gm-j|E)wjst-AL0W$naTK=h(ZV@*<G%FLr(SY#nPAn35So%LR>EICBmQt^g"
    "!*#2-Dv~Fbl;RAeAGC-H}*4)NkNCobtd3M%9m5D)Z1Hs+MLm6AVB6I&hoW@bEUDc3wcaOCiFL;1tr=?Jl*q%"
    "TecTP2X;3g{iJp8iylite?aYOwVxITr)Xi^)xk)vM%|>=~L^}m(@8cK5wc7`GS0x9Pj?eo86O8r0-);ahld_"
    "MfTZRfI4e{>0pHA@Zin<ek`Cu@FQBG3fF=T)aW29MCj%Kr5Q}sxC&IUBHSC1Qs9JlD~MEzhbV0mUKW|GCb|)"
    "0K!(*ysnj_#y1`$8!j^dO4yqq@E2)(xc)rpG?LiZ3?1ax(o^F)`ptz6>SUvi|>Ze?fBZmpYtxdSbEY*Hgq}_"
    "*ViB0oxKn`Z<BVdRh<z+5qy^jfv76QN|?u!ABs9+HWq-gvDDLJSPrxMlJ<@9=<Qbmf&hm6pcEP;=}2XWFutn"
    "LvR`QyHA5Wcf>*K}plW`|n61Q2$$)jQT~ZS65Tx;CSr>lRJ5Gc;gdIw=~wm+Mn8zKC|n1p;DAj_~qJh^9*`7"
    "!PV1Q42(*tIVo2XO|}o<e_+L7Ffb75bka1Ol=S$^|K9#P65PEj8XwQ{NP5#JaE)j7!l_R<5ryZ?Ajm^RxKO!"
    "pI<%n6)#}Riw0d?4UWqEr~&|lxV$nbtyqt9DTM-YPHGa>{i__S^&td`iBIhY`Qqxd>viRnN7_<BCA3^2flLi"
    "z;lw@RFWVR5bTXJLvMkp~7Fm`x*&>xbw2X1~ja3bKA{a%^u-ceGif)?JOBX@IRAZ7z^OSh;!Is_K33N8F^4T"
    "9Z>9W+e!nI<XfuvWNySCq){(N}6clvt*Ld8c$E#DS)yz(oT@8nqZCc_fWN|A%7%RzLTPM3tzW^xu|lr@f)YW"
    "HDnzY9=O_4^lU8Q`RbGK_!}ivRR_kSstMGU`(>b8nz<@;BgPEJySFQf=S2({!Y^kZJ_WaHI>g#xCZ|jQnmnU"
    "4T>}rLGOcP*MV|^!^g%Q`k)fL{Vdm6@ssG`UgX6K-ns^A8{QYI3&}Ftbw|54H2_Y#YeKmV5BF9zrj7rK&M8P"
    "P9qH$ijZnnE0FJ#!v~L!504H{c25+YN_3QBQONq#V@LOjq^97R-2<uiL=Dht#0=+4MeT~}zeE@0g3Z&B`tmI"
    "x=$XQxFfeCLQNvR57oF*FAFuSVFPaI0EP-o2wi;5y1H47xQWUB4KF{t5C|~_i!Xq%VM~dx^@|mI#wRDQ&F&6"
    "!xP!bG8gHNN=pSMq`7UNy|4r0d_;K7NOv%cEpH_KbV<X=wVI*`Z(`F)eJxVwmfuE0=Fzi=TgXbCP5AP|NQ(P"
    "oN)j24so7-08Fa$;GEf_E>~^rX{!>Jc<Z*jTjkNWMsje~!84*L$U#Awkc8zAdt5dcy9)&`-8s@6yl~H}hh7j"
    "gkCs6@gEeU`oC4gRil@3#Hh>HpojTV5s;;ihBdwQ&a|nv?52QI8O3~!|*N+t!>Rta_%Saf(tHY08CM>2+Vj7"
    ">?7d5Ah}ZjeN|hjY;AkepIKA>OwTrE>r<G&n%}omCHgHVSwH%rfI|}agwji)t5h{djcTT=OsY-X(SYM8YNOA"
    "%oDOafwaEJBg*p=__X+Qh3)(R09Dt|f5j@53pAii{BZ`B(yL{S(mHe2L3CdMS7l08W&mUp_M4L<nd4pxHV;a"
    "Mei@4*APa<4_rV{2)u>>;1;gkSd6aP?#x<t2C(ge{1RzKlh;q?T_At7=IXC`1pIC<wdyHbk7q$w#uKfA3d_J"
    "lG@kBdp&SL`0k`!-eAyoQ64=gsac5F+F4^yHT}lwtqNo8IZ}Hc<h2?HKk<<~@PtO(Hn_lfbeMaJ6Hd%z$nNZ"
    "yl=%a6p+t%j(z@h^0PFADkY{cy7~)lBjP%OqiO&wfdaMOJcYS2!Ow)a2m`!u;h+@v<G3$YUh^kP&`j{>FK`I"
    "*Nw(SM&Z2xU#U(hL^h&cLd<zI%hl0?+~$`zATAYvSBa+7k?M##X7kYvyVmIJxC4OBzk^*56PHlrP^?>zM=S_"
    "10w7Ev8Uq^+3Pb7D*0o^stoiTfWpb5ITsfPJ=S+%~*cWF8@8%%aBgi4N*$*a*mg)l#y$8oNyWL>QrZh!3w#s"
    "`Drf2oDYHm2rdWs;i1;e_7>7=eOI!o`tHSQ%{STh2wI6(|4jJi`~G<^GHxwz_mr$kLRix6A*_mjheR~f|Tp|"
    "A;7yUde1n<n(in^Ci{FiVuE0iRGhBR2aGp5qE-Kr9pp<^>}E?ujUWnPCkSArb?2@rWh(G5^Eaij*(DdRgdD!"
    "_f%qH9$DLJ`C}~Y-FtY2o}LK4q75;b;wRZhZ|)b-4yr)7u`oLf_ygmpxgV?Tvy=4?W#fQ)lbEDqv;axY(t9!"
    "Ei?G19IjOIj%7C+GBn4yBH{v%SdpL8_nEsSJQCq^*XojCUxCfS>X65Rp}zYN!71hCp`I8oR6|Q{oq16#h`)P"
    "jBkC|x3+)J1kS~HSbj{J*QP1_Yj%siu;4%wOe6eGP5iKwd;+HI&QQ6fjjsBj_$@1Z$q$wQ;T!0B0e})xKcR2"
    "0cVBvDr1Tb1mvPv%to?}P7A#q8^v#7_b0eLzteH`n8=q@S^0<2S^^i1)77sc3KZaOB0XZ|O&_L8KKqMl%H6R"
    "&=7g=|32Np$bZz!Oe4$$pYx6t(-X?Rz3u0H(2#uF^xr!+Bodj?}T}`jKIc)p?P>2OAKtG8;W^Q$=<2-l))d3"
    "QRJnS|Bit7UY<OVmNo>=y@D{ty3YHbvTlsP+XO3ET>>@7B8|?wMP}0{6R`zD9W-*7j_3RWznKub-|)JYn0Xm"
    "0d^4-0Dp~I0|WqwyV*xHBGI2`;R7pLV5YDq9HWFlPV65Z?H+HR9v<5se>k8M3{mqYIkxRYr=abD+JqJ&^%8Z"
    "AIdnf#hv6heyP)D`w^^zbH{x_?xgpB6+e2;T^yj@3)|f#=1w&%4HkDHJZ%Cn;(sQVk+<-EBgT}lP#I4KBZtr"
    "TTWG8jbL23<HbJ3EG;>JXcD!R+EcYWLbL&-1+vFPNT(!Ylu!RraIs8eff9rgceo~`OjY^|WRrVIQK(65*;%;"
    "W}%I@lO6SaY#sov`^>)7ckM@GR?#;e&)ukq@o&#5HCEH;$gEzV)?M@b(E_09_paw7w6MtO!#nM{4EVw|a`Q<"
    "xP?jQTKb|OsPHrhiz2{+|=EGj;A-hhF*=FiHak=IjlMR6_woR$Gzi|(*X+AY<fYPw32X*-DU~`jP?}VVr=8`"
    "Ql0)ib&%XbMt<MW2`SI|q;h!~+s7*lPXq=Xun0#@?;N&O=waGmUh5Uk>z?uO9@#ue+%+$IN4jT{sXy3FF>ka"
    "RloQBDR`RfCsf3u41sLhJcTV?y-5tQ}dNwF%&9OtNlh-wjC>`%ku?AcY$Ntnu@@KP7Wgl6!mppS#WUMuoWhr"
    "9AlBQC~-v$nac35LpiU~{@q&hkU$fOBeP;~`ExY&9?EuEnKLbX?18FY_MNxqBd+pbsC`2Pz`|6gGGe@<Z1Q4"
    "+4@2|gP8)-|bX%2wN9bOu=DXt2RQ5S<ebAH*n!(ZC;lnglqshC_2MoI697M#29@f1YigOPmO%6X?V#{~0w^`"
    "M5SZ*_kCJ<dM0J=jR4=Ir%ioFz6gMf*q6~wT5JBMDkaM)t>n5u=1F5OFx}4yo-6MQb(d9s)Xef^==nV+iCHS"
    "bP%2F|G2ri1(tX)XUBAEkeNHWN^f)Vu|RmSIl&2=PR+Y#0PX8&opux5lgYLEE)HzTfl+hpfBB(8q5rQ7PoGH"
    "4N&YX0Ijuan91Y;%PVHHKx^k3FmC94FPamB7Q7K**697daWaN-!Y#Y-w%;piywGtUnpkelhrH+VEf?0XYM;T"
    "kH=a>0n4i=@U8sS{c!6cntFCp}3dX*~4RVhPLu<k|sP&pU9Xy7tJ_x(LNV^bjY@+Bc+QEHd~@le{%EK4!I{q"
    "fEoMu89GWz7vhmf~YGFh_gvS)T$iD>k>9+)gWCwblU6^5C66H2_wn^ntv8@-ClDD1cU7{WS1d0W>VQLTbXl>"
    "51)7u7H36Qnukvs>_7|{i2(P&nc+WY5o3!q>kCmeTg;dH~?LumE^aQ&NDT+kT4AfS%y7=5~LJcG}R#6QZ|?V"
    "i-{{Jc{=|&r!u-ajSEYyhTn7^rD%1NR%Sx+T@jVy@ri^Py^jqgcxpuuzD0Fq%D#BezEDJmj088U#>vvabt5Q"
    "DBK{suT_s=jLc<<kW<bLdt2o`+hJXltNWrQ&X<CJvJqQLtbHrFRJSk>u`-nP9g!>i#Py*p*9DS$$_-3;kLk!"
    "pnT;9UV->A#qe$(w*&%dx9`dXYPB9>DZo+!CnuW0kvzjMA0O?SPvgj5XLd1Gr|xvj~auhdVkVa1mg_Xz`LQM"
    ">c(dM+3R(3NU;rgkYF#;UN|u<tvKnH$ih*U<boILUuj|9$=q&FKzY-o*b?!}v;x>D}Oq*3)0<M{4_dQ$TG%5"
    "FgOG-@cat^5}*hdEs71_n^R6PQjO0ruUHHdp$+{SOB28;2#!d)GDI{2|^SKAC}otX%%js%iAZXAm`Bm3SUSe"
    "hIcWi@Ucj?EqY|C3MTDd#az@jH4YOQ0-4&b@_DH?b^ZtKOZ7Cn;sAYBeaM(4RIe9zMRW&ti*yWPfCOx0(x4j"
    "XC>z7s3qe=JP)TxtUNVGKHdix)TVDMr&_$e^Pl;)dY4<;~dEsxdn`|;B(UR!?)KJr=MPvu&^4E&|{w$mOfHr"
    "hoPw*3{S~h1?G_D^L`taY7Fu#qXZ$a0zKK(mV3(}OPZ}Y|$(3e>Y%U~taRtMH%fE`0C6=pzs?EJiHx5_~nnx"
    "moPda5{S3iHYyKf_zm@|~q{90EiIlr2K1z6()E@~35T=%5QtF9k-dLr~h6`i%1c6YzQO7<3N61V|G`+9!_ZK"
    "+sdbn>jzfH*eB|=N3>0N4$1y1i35p2;6(g(RlQqdx_Ra`EqLRAX+3Br^kawB5FW38IXt){gXiPhjxwvKA_uS"
    "QO2%v&svw-&>GrqE4Itr4_JVzG+&>=Dr!D%UK^8*KLme%12>>f?1z!5TQ!o|FCP#P3GU<16_9OXgdZBoCozQ"
    "tq9F>!N)(qfF^jWokyGS;1<8#@3pwiahw2We#A%BlSB)P=AJEi6(ii^8Sp>!GzBA6U83}BTv4j@lK~E42O<L"
    "4rrH57w78xs6KLGO-Mw7t_f_R|V07c6{h|OgdS&`RPCOtkDuF)x-I>U!>kU%W-D>zP_!+w=tFXy_lCs3Ro;u"
    "*Cg)$VXc3dk)nlhD;bq$Oukn=(6PrYU3KL7?b0MUxan=60COx}lUX(TMt|83^7=(|d)Hmug#fW=b2$|9}E7%"
    "h7$$sFFP>i=z&Yu{=2lrJq20GfVv)(0w}k@h+Mhh^zcViRf9d?B!$YxVPeKTBbL=ZBP$=u~upLDmIh=!XkSn"
    "W2gh%)Lez#Fm|hi*#`iB%@>rG!w{|m8r4I$+t6C~vyD<)y0NpxGyzk6tY_abdFxqds%lT4r~q8Govo(jfBWP"
    "EnAz5!rz^r+#GQ@Ok-N_uXy^-d$W6zX@)K!|T8UL930nPVm-m-asu)`z<LWVlkXaisozJ#{M&&2Q+rdJd%ui"
    "#^rj7|gEv7C#W(BuetYGtPo4=~5!)~tihKy;gmnul6EnfG^6E?M`iw~|UGq?&*r-6hW@QG@Du)rHuF-*JkrP"
    "5gSaRBl%vQfYIrD;1*0aN4mIoKiw+Cd%PSBkwYK^aM=WvA&?RHC4Zj&R=iF%5Up34g7EdIDm}vuG>X+}xD^5"
    "2Wv}fTyVB+($!K6z&8o3i+TB1QTH+Lzw!FZpp?#bJ--FmBBum4A&Z9Dv(3M^hUV^jRo;Ou0mj-xEn<VS+Y@u"
    "QS-+Ls5;#7^(zk!T0msE(Z9hD=x1GM(C{DyV8#IF@XR3+de<tt$Jb3o>TamyIY)sH>j6W=K{dAWw`(%jSCz%"
    "iGs-k1`PLF*Ko_XgV0E+v8hy?5fJ5~WZ6d1@J8ZYUFzuYQB&wBl-x)QNh+PBG*4-x6Qo~j{H*v*8S2@CoYDR"
    "dg??*n3svOtrOM6r{>fyA&a>)s0k*w~W4Gs60nws|Zy=_%h(+1=V*VSBi%!1mVOw!AYfCMP3p-)-J4a0}Rq|"
    "4`<>FA$t-(I4v@UQ9*`0?iC75_CZCX;lIH-Ou@*a+~Iy_yb(FN1R5&?9u>5u;R7iue*{AahLa{wMl1{y77BF"
    "aP?_x694V^sAb#b-RzCAYJMl;R@EkC2+6_@O17x?S_jE)-H1$!nwyuHfsl<#eiGfS!E*b5)0sh`H&}&tmIoO"
    "S<yp48Yu1>D%m%HKv~cn1fj7)Y){AOY(c{_MG?CFBmsVtB=M^Ei7gEvWhq@O<|4G{F2rbQ>8@;No~4SZ0LWB"
    "!b;arEl{Tvnt#1AyZki}q8w4VTHCmxzKv2OXU+Bm2SL5@>OvBmr{HwW36xxjF$mpVPde{KH0LP{m`iMkVb{Z"
    "`N1jv$@Y<1`KZ=MB%o`R=mhh<H)<*%elgWDoZ-@+nkdfOHs^~>gB<GT*>tM$5by|IN5MvB!?=yr2^%nvj*$%"
    "W=|T$=JQ#P1s)cfoX4>_FmX4uB3_TDf;Ccs#3KXaMV3{VwD(5WIqguY+Ys#RoW+z>}AdVmDcim0AMP1!~Ivv"
    "CK=}kdNjWi@7=yFf7NWV$sZ+-fV}J)Nm|x!w5i-o+mn`#-##=0JzPDNu2xe+1-ZXONy7=rqI>rj-%D&U<8QD"
    "ugLi8-tKRRR<?JH;8zu>9aHb568b6tNzm3A?w3hAWi$_pb0AmXatf=CCoKVp@byc;E>w#GKs_A3R7JH@w40?"
    "AurScv6y#P6k0_>p7i6d6io>S3h_DwxHCtXz@)7l}8i1@OUCaI&YyqYaQjH;QjXlNyC<UM3pbaj^iGu=rp&5"
    "vqbNApZkls*;;8TWI$?U&!dCOE{n8o>-^+=UyYJk9M_y2l(wrsm;-C>v60*tDq1u@395%)3ElWnrL5*!ViY{"
    "^CBI(4v@V!)*eI1;F*`s&6AOwfKy!41(&hj}R~xyeg}13@p{j41)}&9z5fbuIS+!9e%Vd0suE%!d&CtB7N(?"
    "WPz{DR5@3jHXcY2<)5i!l$-)dc1Ch0X`i0&K282B>yhEH>9q9)Nw-l`|2^c8-(K3yCXPF&VC3!;h4fg4|oDg"
    "@R_hkQV+}PZkUm%YA}4aW?nsbAeObFy#n{$a#^;E)xCq<zQTosR*lQG!Z<7vrKiHw*+7}L2X`H!bSH~g3Gs~"
    "`vZ`U(V#xMUYCb}fi4`n1%$}U`VrhuT(%|z9I%>!c7um-g#86G5X_k#kLEFL8q95%S5ZDN-&fpVPam#AKK)q"
    "xM9a$W~J@CR9yvPOwuXiF_Ft>+LVt{y_Sx)Hpia|pZ@S>2D6Dp4Z!VhPYz(bO@9tv;yaP{`d2iTk&(DcUn!+"
    "?I7Z>VchiK0%T!C{?g(mrpCt%Z>{XaOtj(CpK@!m2SIDVBc;BZ3T}l97=$xDDveW83kPmK-_5z!Z-PcrKTh7"
    "{~>|#&YSttdCJ{6`TASOZ&zx!<E;K8y?M)(ImIN`FiJQ2QRdaG+t3$w^V!NviJjuz(K0PWY={n^43@3Jx2P}"
    "lNGGSi(c2Z1$kd2Uw!v=w^jJ`35`!em2MHm*o07z<}ic-QwXXRkhV8ZAd-{1;{-w(<|48TZJ$tejp(WBHLM_"
    "otPYT~!050VM#M8ekS_WkGGTY_%nENJ8Opeaz(Q<&?d{agJG_!=wVh-T1?Jz0O3_3X5CP8AK4h~dbO;oV-mO"
    "IRHf<f~8|v`$Fh+MBUOq+pJ_G^6r|<K5fvGja4-b_Rdk{^7!w410<8oVgzn@RvD|w@1eJ_qaJap|TBqkX&Ot"
    "!0F0PQAf5^5{fr(=nvL5-_)(r71m@TrB7b$p4EGl|_84j*jSW>F!hCpJ|tI9VZNdK<Y^#i>#0{JI?Y``o83&"
    "V=KpsyT4R%M8ay(1EX4sxlT`JP7d@%4s@NucMumO99y)EX$!d{P56S1>y?b#5d2#!E@fO>LS+zfMMT)jKDG0"
    "z^^J1VT)jt8B?j@$2BH#nEpNouGAULpYYfRdMH%4LrDuY?;x`r@^ba@SIv{mM)kA&yXI+&!|FGzYpdbQ89vG"
    "g3H?*5ezi+ADQcHT9+L%9(i&JE<|4P5O3J3X1*M({@BcLHfEF_m{Mj%=SWa~$D<e-Z>b9*PigvDt(yu9|hWv"
    "$g7QkWAsGj9hrEEO|ip0D~N)VVsTrh|7tNy*LX>nR85q*J~wN@#rGR%lP))0qi9iCXpi+D@m{I`^Hm3#u(51"
    "4^zNx6ptBx2yRNQ*O}Kd~*vrwBgE;kAGSGr3GhkCt#7Q~C-c_Ck@WwKDiVeOjKG5B*7uNw4Tvv7VntCf!K}J"
    "_YE-v>u6O=AT5SMl1o7+-M<MKPGt(&cHH7$OFm|*4Q4BQxnuSDL$XE8y9mqP~h$U?YnV4=hDg);1N?{;iP!S"
    "KcP#*&Ei`PF2EVooHpI@%bP`CLQ*tkKFdBz0ZqvcE#VD_0J=(`dfvsi-a^u<u^LFVD{=!AAgmW<ACliXlozd"
    "j9VR=+yW6Kqp2Z)#f7{uYzkfSEJlOv|jy8)Iy6-4*s=HTXY{s;WpwX8cjICxVOK<JKb-d6ASmmsvM$@g_x|%"
    "G@8$03*K2qLKM;&<pfE9~Q*JUj<4$qnbAFvH3mXQI&SczimYwYRNP5#a19Q#u1oDt4Lw@A&+C8^2p5RT>PA@"
    ";}7PGeFsy=-P=?Dc6NbHwLrUC@qWXZ&ynvifqB1Qgx=iuF}_!nn8{+RWryQ-wRUkhCdor@nqoFe?Z|W0}U;8"
    "^Nap;xOw&!OpU9;0tJ~?Q#bMjL;@LL{HHcO%8J`ni9m<+Ayg5WabmbIo=3(VPN`TpC@SU87(@D5gBj%3mP9c"
    "x;)2q5Ai(XbNhR*_f*fS<!s$0X{-ppBI8A7&j9-X!ejP6FP0_3KJr*2Z6xhl*-wfFPb|}?TWgSvXja&kTP84"
    ";Nc5q1^qAmb4XUCuzMOr_XV%a@z{(-D8q3ZcO2&%aB*aYOV+ntHfwt!J$ghQ?AGh`_J!fBVAJv9gdeF=<`6l"
    "&@vv<-aaC5*wL@sbYm>v7bGwevtysiVrJFGLrb`5+f76%?iM)?P`sE$nmqbN?<gG3*4iV$UGOJY#Es3rxO!g"
    "^Bu#JFA!mymhV=G8${F$Pym3D@DOUaWCP)w`X9!lVdS(hwM<VffGlJd~fIRyo{)L8vt8H!8vQ^c_NZ=;Vj(o"
    "nOMlgQ#TNr*0jYR+S~JubiB2L&4PABIJXb>g--^!OLKYA)9mBrApRtGq&+9HaQfHtEozR!52)e5=2?9{l4)B"
    "(Pj-drg#59FJJIM!w8Z}O%>0NS&N11Mpx9g(t1*AS7F8M+mi@Tz&-|W<KzL<8RU&au);#u!V<t43X#w-Hq7{"
    "x;2|2kF5Tn#z>v=EgKnDLSqi8KA7&jY$@v!Q45eIXF!kFkEtiO>fus%vP8i&#M^FA^sSZaQ$hfWF$k=jig&L"
    "5`r`Krcl5(qHutd)S6$pde+~VC!HT&aYxe%iTBG4}irQRZnK>wpEB2>IZp9G9%XIrh);ZH{Dhq9F&l!YzP5<"
    "mrWHKqTFXBmpuEd6KK#Uf{9HS0PaTq*kSlom7ZNaaVcv8y@Cr~S(%0AC<lDklD*>jP5!FJX?lZVh3`DF#I)`"
    "b$JEl3;;$7rT|ta~sRuQKfFP#Z56rkUM;q!`$hzW5vXZ@$~QztwT^Rd&Fd8%}gc3#GN%WRbJUmMJxH#j;W_e"
    "GGD#+y(m`q{9?3LZ%rS3@fienckD_tPbt>w!$a5LtRn&cswGlt_xa}YZ+e?AdRyN)z>3}sIOI`H9MB0;!4s+"
    "S>4Ep%IP8#^rI-0cXRmyq&<y(f;URpq;Evy$UKRX?uwl-icHmv!+uc#>!b5%Bi;_RC94df0w^s*y_6!X872;"
    "{08$G16M}(4_(S<N)0%4?VxUdQ(a;=R;mX2<?o-jIGjPFKg757)Pj+WXJ9h<l^s1^M3)QtimFIVQIQn7$+t|"
    "{UnUL8U|&dCXS<h*Jd7S@R}eOQ?n=Tl9mmX%a@ah0MV4ypZq$1VLKOc#-p@P=Ece!Dl*tX0+dF;r{T9pTHGi"
    "HaT>*qQfdA2{odB2G5XV{0qGm96s!JNAT6#`EqPYZ~M(d5J1P9sN8wjDMyMl?-R_3G{tF8!_MOZ_;YyEJoT3"
    "3D>$0fkMLp3z7XD2*RbVozo}56bjAvzIy&*^Eu{xP!KeA;*AxU3yFDCszRbMp&s1$u==l3@94Aqx2eMdUK-b"
    "YOYbS!01clK27waNRU~;WME^+w0!)%<eoFF8OYx7b3Davf0k}e-SImtt+j@jLDjp?W4VFvpKq@3AKmnH|N9H"
    "FH11<bRFh9UgdHc=jPOLBf*8>-RG=iXs>oE~2?y_`jJ9NF>)+!7Ig44-=?B@^=%$6^R)aLMP3NqDEyW=#+vI"
    "Xh@TXHmUc>^nZmAgPr#^CAOhqVF5vWY6P#5{x42SEv03NuE)Wc3MweD0>GfJ7z+KoC$lheT4t;Xm4=k>0Dzu"
    "%+}<&z?o!y)gLAA+zn1A9jD*JJ28SD<v%{AK|j<1`amHR$qS4vx|#|T2}(!0=G;}@}E~r6{fvfMY*XDten^7"
    "Bx0jK9Us0qihlS#5}iI=la}%qKY16p*_NGP(j7+ajqjr(ohXSe>p=80*coB!55z{bcMx?pb`B4I+&g}~`)VW"
    "Jc(uE~_p4f(R~y}c3H}sbrR<GpcVD%&8SNgt>c*Su*sMI<;>+7dN5_Z1;)hRELwg55slVPF{Bm&k+rgS02t2"
    "$p12tTH`V#7`E!LW34LC`8W91AW9)o4L;T9Ibv^T)29vN^PY#AJ$fX3GamczZ}qo0hI1Y$*Z9Dm}P0ZDE!5^"
    "<@Xjy+l@Ajws*R|O)4f{<*?R7f(Oj2VX>xummUu;%*XH;EPfkCg4)48`o%(7%!$I-E6<NPKt;GNto~%d4mNf"
    "x_w?bvbT!O(ElEN~@rOAO}-&Zy;xarQueo-+K1)am-wf>k<U{Y&iOc#%c3}<K697zbiIy{N~_*7y=iC-ssk}"
    "ad`Y{_ZXNbBe};)N+ti^^Ua3R=I8bX8_~Y{{4<3Wu+5ASFN-zIIzgPKlSBzSc^NCQL~YA)&A`KFNxMmkUhSU"
    "jtUps~Yvh3Ao~>~d*3SpGc3*ou63;0ci3cJVrrAUd<d@xOV*y3Om8LuR*9~*3%6A&Z=&@U@W4|5?X^=6fqgZ"
    "uoLt5WJUp0}zaO2hC!R|)gNuY(It9%MYwk&pObx=GY9j7`aX0bTY)g+h=e5V%0V{s(l6Ri9P&P?rcg(HS#I&"
    "xG}*^``M>#Ya^%$Oiu)vD*d*=_tJI7;EgGrirFf{v31h%lY9ivs)Q1gp`!1e{y&|AAd9pGQ(rUiV_D*zz3Ye"
    "Jn!(+k!j9Vg_|6`qI70k_X+?!_jT6?7x2U!JrvSDFiiuc?RmKX)n;-L?{(@m)>eMeXl&QqW`+__5;zcJitJx"
    "a=GqetDzwr2OUEllwJ(hA6lYFRw2RGEiof+uAtNtIp?VK4_m%i*Q1IuEH*2VC%v9$nM157ESx<@D4NaYPx)0"
    "g@oYzkdh$b&+yQ8TQ#tQnGHI%==({jBFsD+1I)n;*5^y?ld`2LtJF$$?TaIr}l)fZIdzhF7`k;%$A6S@7tA;"
    "Tc50vOv764S8y7_Zfs%>TDJ1mS*G`}dQFLArZqA9^TXla*{?EvUYFAa-E{eVRD+L}&$lk>Uxv#Qr18TFOK3!"
    "ux{oRhLqD@d2)e1V|Z02aqppKGc?fl+j+Qze&vsw4~tZsD+;X=Y7gz+-i%jmI2J+@{oVQ54XFi+iG4H_BEh7"
    ";u0Vt(u$;c%4Mz1bzdL%jT)ix2_AL_dLxY7$s)FbRjSsNpYJm7!Tt%{R0#fke8XiYDAN$NA5jrrt2*RO<W@L"
    "&cAD)@jvO#40k{uMkR7hgq@|d;3p_)lAV=>P5Pk^E!|!IYPXJz<V;Wgu`Cu@nfS15c++`<l#HcVTPuX3SgX<"
    "m?%VI;F~*bBY-W$Bbf!Nszs)MDf>Coc0n)Qu)n|PjM-q!2?&|2LXi1V=^+~&i1w)hOm+|t$Kj2UHAP?U@*<X"
    "(CH%enli~>0d>YzL1In*_@&NeI-iW#eR)l`Y*V9w}n6~FBhkpOf`K_t6>fYm-ekTU=5S+upe`OxQ|{|dhbo6"
    "o(9t*XIo$SlL+sT#^1s99Jn?KEy$KcQRKSL#1-NQ|4$cbpYVJhDtfu#+C#e2Oc>+o(#xU7F*>Ynj7s%(6K_W"
    "5KRO3>d2066MJ6*zxv{r!}22f}k&vsj0FAHopVEf#j*Tv3gYV5fat;Yb=jC_eFjUcW4AF2$|K+J3HG4JG&5&"
    "7M_k{9f_iK6XG;Z7v<iAhd|-|+_6n51AWs%E@$1=KN&3P2+`1ow!@7=Qqkph9!J>}LUxk09ObzUx2`vASg2A"
    "%?L{9bR5GFjaz>~IZ9wTD2v!|QYB^Cf+%gt2Uz*T)>8c?l8hBjxj8o)8+J%IDYSkq011GP@XfzOzK%9Y8ic3"
    "}uI9DR#5L~O?nu|iQd>~6^%ZhreBq`y^`hhJPi64z60aXZF&Bf_;8DOyU<)bWApgwSE*Qk)>oItk{sb1*SaE"
    "e$u#ps;Lp>+jCP9k3g=F@O>SNJ#A2dyXvKA^-wEp1!MuT+NhrPb=3X<<@W1XBPzW?0z-&y0?P3y=k<*hF8oU"
    "4L@K1c(am-m4P)t(d10V}?tSON@8!gCvM3;!Ja8O4Nk!N}=L0NZi0PEy3$SOkSiQvHo0PR_0W6WIWuA6L^tj"
    "eZEfFc=SC;z(EusM1LXiwC@!x)CVd#@F}DlGj(VRaByxECZFT&9K5r9QaD~+tcVR4dx)TH>h?yRH&8=tYb&-"
    "Y_Rg0R_~&OeRQPwRi^ch%f?f#}QmXllE<6wC#Rj?V$oL)`_4k4*mqL+J)gylF?Q}LtN0`z#AR>jD>d^Nd>@k"
    "Qui^c`2)|28|{h$mFa2iKnZT7(1hfk|^U{ny?ak<PV3#^7)%mDRjL<NQc{{%bUxe!<CMI2q&LB|(eE++VPO0"
    "~oQi_}aisJVK&D#He!C6r?)w39^<y_*(yZ>Q;{nkbyMA5_1_C1+;pQii%krOcrVo%|5s0@YP_D1|en0wH4_s"
    "?#+n9g1b)0Zb(-p^}rD<~V|!(s`^eOzwLG3QEygBSl7?GRvxUnj<N|{5AGhiC+AgB+I}7w@@5ma<2&iR`2Z;"
    "sy#3TU<n~uS&nzzxj~@LXzMvYko}R(M>!?{(3p_`sP5_8DW3K+1t}tv6eU3w$csIcL)HF*L^lk8Rr7qPgzWK"
    "hjx`-qsCSqy)b50X<{q|Wq=c8~!VN;dh+I$g+v!$6+NOF|J%pc#mAIi~IBfI+=fAu_hSa&uuh~4f^`Z;wK;@"
    "_4z`}hyDkjU@DWj~Z*_n=2@5h+CYi$l#0X4!=KBE9&)95!*I>7?q*czxlmlJhfv+PUNw*g}`zg%+p%;&1_Q;"
    "w!5nTdMbXVCNuN<_lR+8aYT70lnFQkb~jSBic05R(rqNmolKsS3u&9}Z7{j?`0X7B8qE!-YB*(-DfMZ>Ln|D"
    "}`(|t~16l2!fjf)5C!xh%GkBuWuI71sRYpBB&iTWgCZTO|2Mabc3g>oa8eAbK-K@h*)FImsCwB76WIB<}b{4"
    "ut2g@HdkxM^(1(10hzAEh40Do_VJ%2SJTC4dOO=E2&o10zV~YP_0i$!?!jqvynD32{W~P-0V;wl=E?T!U05+"
    "`C0g7;B^OBj%>furEv?Ye25yF<<Gt70$G=Cv?EX%b+X<m7qG^Dppr>Vo85-~fr9GUS@@?KwK#*+xQ%42x5XI"
    "qgy~GJEF|<YDsTcNw@b^?3v42hIMNJN;HeuI=)l;<iqHqQgb<)XQdS9wjBQSx`hvVHJ-<<3n{1j~;sO12l_U"
    "+TXANF^nqrLsZ(?J9^t}&8D&tWkdEoV703PoV$1QL}}XzJD8k3TBKOs$4I%UyH(E2}Q6Al1}!#OoHca`L{G("
    "Zw;5KF$(VJ_8SfwFJNYe5kr>@eXLF<1-iT3I=|t$GQOfj;}k61bLs@$WUQXHJKCpfTDItS6G3T0IBfvm`al`"
    "zy!EJ4x%_bgiOM7xOkK73Y^30-uUtLYN_neSFP}xK2cUT0=Ub=yaJyp13Vw=r@_302XqVQp(9wPW0Vk`P^)c"
    "6lu}E}D=nuFZY2z1!X?us4kO4hw8G-hSIu;5V;T{=PSS;Q5z4)*v)_G|UdNcNN#@=XNgd+`vAVW(v%(xGso2"
    "D#CD4D`J{=bn$>}jhrB&x?%~WD(GPcGZJ422uBaH(C^ipfkAxV3U9g&)&3?nzXprgB>ON6eQjm$J#RqT~^Mv"
    "@yT8-xWw<wicpXa6*R2x+F<aynzdMWrqmllO>K2grGU<dn^9kzJ?_-pi4xss79sA^YRYXoHHnMNdhOp()!4v"
    ";{FSv_?c4B&QKmO4Z951Q7C&+`hQVj72fle94<bNbX{|JiY{}zOfz9BV=MdYc5uvHiYCnZ!UXp_{3J}k-6o)"
    "StUyA-Re#6?aH<!ya=s3YQze&1oe;w0w>^X*tmwB#0~r;Ze%EeDNx5PPgrfkrol<3q`0dLEqW|?vK$Xa3Z<{"
    "X1Mo^;SR`&NP~bp3jYvH0s)IRG!mcj?pd!Sw9f<%?;Z_m;)XGE!oysUjkv^#mvqIa+#X?El<umwiA__Ig1U?"
    "7lfyC_nRJ%&;#-40>WC|>BU|2QC)To(2`I{-BKV=bQm{?{O_^9G}lO^bN>I_?gw7a+~dR8p17Me%*AdFinX_"
    "p1p$p(43my=;ymtckqBSQMImWdPHka6=N*$IZlu3PsojEvQ~#)em_5Lr{F&4E!@aihA0Lq|z0;X<nAZbMt9c"
    "wFTCUwsX^hFT(eSWWd(?iyTO9txY8jaA>YCZqn*z$|@iN4xF8!sr<5?@brk^<3>843GrM%L19`d|vZfmv5hN"
    "<!H<s#uvIZb+Yg<uipA1Isx5N3lPF&`0#}&drlS`rBf(ZrndPU<jiVAq`)D*F0czSuWDOHPx1F0?J-vXqA6h"
    "Np@y)AHz}UL_JCE0Fqg8fgBpVL`R=9&56vc(XFfqZ3&>f-OF~Ui8pcg#OC@BTGMrk{R#BS+$tKv4VfLbzmH_"
    "v&z>@=|h_blN#I?FXnCtxzUINQWLr<tRqHH%vJT)6t+Uwi11{HxFc_R3#qF4R4Kh4lWMYdSkN?>jNGz@Iiz%"
    "FZ|{~BS|6KwIscVt+-Em+2-vqBCY%U;)<*0ybE7Rk8eC_FL^qWmDz1BwAnH9lQAFQi8hE?lE75lEd>f-qX~D"
    "#VWPLzDZLkvfF4`5nxr7`W3_U9}|$I@%(DADH9L#t1~{FnP9U0#;4sr<4BOcHe;c(UbU5xRZ6sSp+HO`85hX"
    "yz4j06>~uFP3y9x=6M*Yll;1v-w%yOL6it-IaiasA-$IIBPoHf4&YPvqm3~6$z>ngq}3^9$~6zu6`QwM{IHe"
    "U&wR?-UHcSg?RG`37sg_l0yDd+I?P8u)YP&125^717c<w6mzPyT9ywHkebQDtHq51$#rv$rJcp*fX%T9sn9p"
    "uf2m@pVfsRMtbQfLT;}*ZdO)vUT1vXZ|uGXL^&*Z{U+t&KAsif4FlC98w4QF1s9i!KQ3h1||&jac32rMXJK_"
    "U8nIR#JJ^e>^Ww>hND0i}BbCsb8IY^V@=2nUWfMJtAX4|zA-=@hsygr&XI7V{>p!yJQ-^^h&UAnufr_+C;tI"
    "vUzilGD_PLkOaqaV(U%JS}>~4Dw-{M!5d@VAIM*L(6YU5^Q<4=y~=KGWW#;17e&wG6F1H*>qgr-wGe+rA+7}"
    "!S`GS?tul=Lr>Mhfbplrs}}s`hi282lG|5kd%l5c&_<&R*{23=b-b{FYS3Qqb8T>g7CPWV7`BX0Bi`V?sdXJ"
    "wVqlUj<6(UVJ)2>0;wx6dhItOy1skWeY6-MK6)aPry&csjt2yJQ1cGCh(-9%SrDqU{g-ip_*L(41dIxNbEPL"
    "wJL20t}Kkm4x9xkHs1r5WNW!^nS2tlY_#Ec!J;)Km$oCz~7@Fqvs7>Z`ha*9H;9*Mb%`Cd=axQO9Xm)QhN0P"
    "_r^g~07UgRq6ATJX#KdP#7YisxC=OyL-iz(J8%Ye(LIhk3S~&j6pHQwi_@U-y&LkF<diQME8Ii7IJkqNJM=y"
    "_OV&+$Fh)v=}=shXY*zA&2rFZnDYytP~wZ!f7a6!HRkD$I!?5zj%vhJ}x6VH>vTHU*449P@|BoS&?JG76v4f"
    "<w5vPMF!;}o4-_N2?vr;dpF={EvVpn8eRORmhmSw<_n709WAU_5tzR_45?X&KmGB3RKl`o13@9}Aju>=)+Q_"
    "o?a@3WLOEGr<j-*dfifpZhBdD{0YuV>b*<(#Tp@WLX7Ck9RloqhpwI;{k=YC3tPs%XZ90Wg&x*Mf;4oMJfKk"
    "2c#AEcKIieVytL+xku>A#Ca05ni0jY=A(~D;pP;P;KKorsiG>7=wDHo$E7&tz<gBX)oYCoCYmlz*WP$xM2Sk"
    "0^I*wOy>!NKlvvb}S9c%1CL!oa=T6vo;c70Y>v_+!5v9{=J$Bp<aNGu|9HUNBMxc49{@(7;)dnEA?p7Z&-ty"
    "#yf!|D!RW0Zmi+D`GrK^kT$Au1MhU2<>>;CV;^!It~<ryT*EgHLUN#Kw%N2_V|Lk&8`=)K1Px#t(w_+a|{aJ"
    "{_jNe2>#)0@~ESj6hbj(kn?_rTt!?G%TmW(;^N_#B>JO-(W+5iNI((+$546{AdahpReN$MvmRvon-s))CdJD"
    "vo0>Rj(86*^c_%2UbcV5hyMI$_tOlTw>JU41SC}_UG99JqLPj2Nx<Gjr?0z4>p}~L$mLP93m0FF$Jw8VWJM<"
    "*1fdi|?XQhG9E8i_a593#<8;ZqTnXjt{SZ8<m4^X1g0J`DE(F9H9EC@!7#>s?|QGgA97U0<R%(5SQEOZ8S{4"
    "iY=KGrBkum>H52nkiz;sW3`RC6!Ss^R_cJ!eSRs0*TqLI&M2Fw+`z3NCZ%DbFXvi@{7%B$oXMAwlB<Hn;8*w"
    "NQ?jXCjdiNQ5&rXd)3Hq*<Qn0wHYGFVcTz^8$!ROC8MKwAFGsK~_umQ^>BkEzm6i%+l0N;Tbn-y>#Gg^IRgf"
    "U3tysQI>RW8XB5EZQ&cjJBOgaBLmi_z}U@O;K&-Lun$b&xtHIA$>(q^_79JCkGB;|wng{}q|ncyCq8SBT?`("
    "2$m8s>i^Yim&Y4p4)&4@9cf<}c9oGG73)F?IDbX9uDe`B>yXtgt$o*8zv&<K|uv8BslcQ{=^qjF04bVcBP1S"
    "Z7smn^VqS<~dTGuU>CvniaJ{RJa2Q9$w?oAhp$o3)38*P<wlw{L?EHfyxp|RtY=ulhJ<iEcBNEP|(4hCKy$w"
    "BhYRi4eA7!In|>s)%bw0}wj2m?i!!Vs7dqN!2wmVAbF*7O6WRD=zWi^`w1kMYbXAy6A~yE@3nVhRgW>;~@QC"
    "AH-9eAdB>z_;)sg4}LyT3HwBF5bZ;RWsyR1`25W%XSqA1hv^5O~&LTMUFWjAM3Tr=GFP}F6DH10%J2(-CAVx"
    "+F%Gy@L9Wjgcb#&Jo@*;y#wiW8O@?Y^{cO@WthW%1zQQPP@xU=mu>yGHR~4GLwfowfNQkM>X{>hxAf2l6kdC"
    "*7G9Lc`ovB^$1NAU;L4`ME&P>_{}ciZf+?`JP#u2I>glkpA&kZ(^Mh=crvxp`SPRja4yk~#7P!jOmeZn+CR%"
    "T6-*i{uBtgCwcWO|nnHMmJ%EMS>y(A!p5EiKYoJdD2p5qO+@;SZ#s!yU6)UkO*90m4m%hG=p#$ogVb+Cgg7u"
    "~ybc%t7EkC-Rn;)B)*m}J962-ooAyg7QceY)F387I4^W`o2j079sZ;?PS?gpy4}%>g<A{L?V)G)eV!2txjd8"
    "UPdJfBrIb50$z|hrp6+kY_i4DPk;G2+~(#ak+pG`1`-CEPP8iD968BJMa#`W-(#&j*5k}4Q1D0MVSaS{@-wD"
    "TJ4D&+(lKhy@)cPM<|l>g2p`w#+NMCJVqY}y|vzs*=)yIiMuLw5sBEn4q90Qigc9(+2!d|7ZR5?7LC$rr&6X"
    "^y*7xhl<vB4@$<3la(=tK)y2d%H%(n)t8yI$ep;}q#JcWW{EDeWv>BwLn|@wGz?zzLbr)qkfUxfHce`Sh&oS"
    "o~|J;hcA4<RAPk?1;6z8aY#($+<i3S}I;Y8Gfd8x{A8RzF3JHVQx_E~^lgJm6b4@DTZ&Y<aM5E+c@q!IG+aR"
    "7)7%_@Vo6@Ftaq3I7gVnFK(!20!`wd|j%9Iy~(1MWjRSwTzcHmRx&u$-pv)10b&21Eq^yJSxh_=O5W*JqO!f"
    "-*wXu~!m}JT2mh!X-akHApv#->sF10&S3Ai4m#omdp*9w=Zq}TOW_b5X)jWsF_4F+i`8c2^m~;hXx-^-!^hU"
    "4;XwfJ$$GSbFjBglcX(iF7piIh*Qr#hA=XeXk>MSHzQyfP+3|V7Ny@1b%I7qgxMkR&aysG1FZF{$JQwI`wus"
    "W{+cZ{vYwik_{>PsF;_OTb8c2g%=z}G1{wxi>`ppMA@f7YNrdAIpIsmczKkXrI3Un$&h|RmlKsyp@6ev#j16"
    "5X-Fk(R&@m6kQH48nn@iC>F6PE6`{s_Kul)_{MdDb})u1|t`T!RpC-<e5ROYg#fyKdUU#LOhTM;^=$&(}>@g"
    "G1V)q@ADar|HxbSDuOt6#fR%I`bJw$JaiwPZ60m2JV^Q-T|G4w;Vz4Wo+il(HnISzuukrF->s=@6)bIM4COX"
    "Y_~3y?UgWVHoDmr>947?&>-okXoM;!q;U+kQk7tfx0=Plo8YhF~LVW{FNM{I58NHL)9$i=6VV6S&M4IwPQ)I"
    "mJq*LEM|SG<0KvVLG>NRdra}wKdXtGfDQ-OPVmXc6c)$p%lQOKDC3B90`+`Ss+C&kshQo6Q}D*y{XvkYINCu"
    "Br&l?kar_9`EVbF<FfJ+^fo<sdqKYf1{BTY-<3)G$XGAt-^m6>9I?c_uJ6I7{iHwShE@5}0iCW#T@wvou4)x"
    "ujr=8n;nyBq@y|@`}p%$fo>53BnSf*$i65Wbkyk017s&*DUxT#@o^M!?*UjIU3-jN;Qc54O!qw}d6&Hu)lU1"
    "-Vw7cEpuLSXGn>h%5>txwXF3SQsN1bqON^hPOZCZ)rn77Zw5Nn){Yz`y};m@#_p$q509DG+k8T!?ZyjJ}Emv"
    "DEQ4r~|JU-N?kS1;;lNP*sjORpk&u?8ryEO*R60t&cde>^KLS^M##aE>GU5)k3g0c8q^``(*3+xBX4^zgvV>"
    "H5l+8xCZdNQyR!^PHBpBtin`tAL?Y@fwQ^hKElw{-MpHo*XUoYZCvTRW*pS(XHIWhSSLz#G)xddT{COTE#UH"
    "ASrbRw0UGHiax3QFOd(K_neX)H<S@cMb~Oz(EpJDo;BuYrdDaJ*;ahU7JvmEzSDU>*pMUu3`2*^U^mw;hnKC"
    "q9ATipei^^m8MD%^Mxz-d)DJeaH(rqv*BXq7mUHkw~7JYRX>8p6b-kN*|kxu>XX>X#%joE(B_$5bxdTRX*=W"
    "uhKMmy5gY~;`*^>vIiO1nd>R_Cm)KD#1xR_B^281&G7DP#q#3ftXasWLu{Ji?=8VZv1kC)U~aYALAM8wxHg{"
    "BUh*7L+91?5ftFK3OGP`X);Oa&8zbI=4eb=X$5QdRz(=M&&!7p%4<TBl)-9i5$hfZJFtTOM9!{+eISeqP!NJ"
    "s^Rh<_IPP;HB=u)MV+?%5L@FPu^%CWvTAa9zsSnrR<il^cgZ*3zKH8;ugFsNx#osC1D<bg1_|ZxMDsj<qXPI"
    ";K_Kw+2#63fb<=#}dHZyYKs%^NdT?2c@2iDjEKfSU9pgUv7`7r`^t#4?f>e->Zu}b;kGwamM5r2<R6@zCQAR"
    "FTZ)lH~(KLr5L0yBI>DRU=p1BqM<Km`xNdFsxO@@1nf=!5R8rHyKjnph@Q@S?5?%ZHaivU)fS-Kl*P=r;)f@"
    "kaF*qh?Egnao7XHqxc#PVdiYT2GV@IQz3eR}qW<)CYMTV;wV2GM1B!(sIGX1Jtuwbt^-aZAbY|8K__0sJ+eE"
    "mreG;08*heYc!-LQJ65ws!a#au&0N?e9>m?RvbXS&Y(?9Qw9tw7W(v)qp;ramCrm)@pLuiwTAa<~1aY9vQ(2"
    "bbk~ey)d@1>UM(QoQY5j!Inu;b{)@_j_;|(pa^<XOvbu}gfcfvqoHm})Ld~(18Zn%o`Kn~(u+Xk91!v*csqk"
    "%CpT!b7gW!;v3-F-OVGhCGxdLqJBV7xfL}r!nsR2UiBN#)29plPCcYcz^A7ze$?i?L>`C#?wvIRzKqW_<FM@"
    "U9rm4o}(ed_AueYPW7fXPcPQXqx{B3*R*esec;&zUA!Hj*n4G@ugKSl?Kr_t`;_D)Vu7=+nSc67S?w^JL8GI"
    "jysG@HcdprL~|`};A|t$VfWK{h|Wmwc9V6d&3<INkke_t?S9-1&KT=NIsKZgsux>d+&%yChRfQ|t6s!c7j3q"
    "rIOF4v%*QSb(HO10e9%c#{wW!1UOM|9su)_HVL3;_gRJ$6U;&Fd>x%TYGS{OFNpOl1+=Ppq;RB)IK?g8!ed6"
    "hb&HPj8m<3`}AZtAS78`QV)r&`%TwQIi^G9I^k;5%<?JwR7_^+{95rM#n0=y0+u51Bq8WK9kUQDFwc-$pxjd"
    "qz-T(030N&a(5esj{my{9@SeK?k{5B^puS(%oq2la)<bZW*uYGc;QkQ?*n!7tpCZAp;|qClP{?cF%060h*$~"
    "`8bolhH+wF#BUw*&z2NQNC<6C!-0NjT}qYRr4dJcb>7w@v^Q9jE!aD7LU&~c_{sLq`z1hB1RUq)!T#S|uqQp"
    "8lIa#3KyDVGtcEWc))jtW&3WOPCb>Is&TGB^4_$5vO6dEiV~hl3{)U<+qk=WsYu<5teD+fU)3x|g+rk4Z>w3"
    "f$4b;KXe>Cz+UFUD!@=3?H!gi)apzG_-jR#F>d&0GGDTAN&Ea%RR9NhUW4~cAbvyU3mgW3>PXvIN**SItq*5"
    "Pkn^&V@%4Nm=x525W~XXOk#Lk(Fm(U(8Ok?4e=XNQ<Oo3V>r_jc24Pa0k^Oj$S{(Z^weVjPlx7CTYydA?sOd"
    "a-@%ZYZXk%!UZru7{Iq-OoeQw@ro}%Le?0hZ^LaItM~EK2U|TQiSOu|QrCY_`LU!xWhT4A9vWJFodobh)&n}"
    "M~>+pK44u8G*=NQPJU^PhXX45m8W)q#Z_|UD3yQmJv$_88?(niEM$_}LZ96Gek$cR+-b!&683D?HTB@DRCp^"
    "KcqviVU{r6hT!>m-Y!NG9sw&(@zU>pS5WfwIDPKGfr7J$>rZVj~ooUH+^lbjCc)i-d*E&b)-n&GW9GrdbzG@"
    "esF)Knu;9p#)}U<`n!)%(E4vHug-y60EQ|WQ_V5LdkV`+MkAQt=aWx(Lka#?cC6e)*rajwKgjqy?Qw~`q0=d"
    "Dq+`kr?bykt8}I@Lr~^$Cg^K_f)txfu0YbF8L6BRM~5e$=8zDlR$vLkvL^fwMJ1^D7fZcIrd64j&gL3E!^Z-"
    "KXmiuwgWd4YF9!A7x*-Ekw7qI*b|u277~i{QL0T3Rr9r6eP=6YF-f4oPb?k`nF}5PszXN+r%^?~kVRPBi9!#"
    "T*t>X6g8i5Afz5FMi8928a8w(8N%<jrLC19>>V}-M!+HOsg-Sy}~EV8EInszZxzZO*5O%DUi@HHfc3Ny0Q0B"
    "xP{gP;Qw-7v|`@OX~p9y%Ykxwguok|<ABUoeFQhBL(fe!1l;G|eAyq<ot;<%n6oe~m9xbD+%hTWL$(x&>fga"
    "`Q(TZU?g0>ZSzODVTB=I&fUQu(JOh6%qdk9kpyGFx#h%sJZE%UcBKFi&=egK`DGXeZrF|zp_1<?BlYtiCP_1"
    "P3(vx4MRIbTaAZ0`jC_Qb(T0BTAilVsT^WX3}Q$Pp)Y_*EyO{{yf$_%Z_-gfA5~h#yX?O7OOUput9CRcA8b!"
    "kO<E`E@6_W*OR+7K&rc=7>goQhvMkA|EvyHgkh^7sT*bCP&=i{SMcy#o2Ie>bn*8u+HB2UL7zMrhRyfw6Hq5"
    "~F>LAjktV!rWa%Iz4j(7iEts&GpC)X!}QZe-G_Rh}k5#ICN`0mfuBFZC?o|%T6%-ya>K(d^%Q;V1;wYxe$3s"
    "W1#zZvQ{-y<V-0(D9q@3kMz&@U%hHtPhPo7GQ;Jh>sTWCWEHx91I}X-dB$jQA(aFh#|fcRZVA>AdXM>=oNXb"
    "F*BGi@Rxu!tnbiKfgImj$i$D++F=HLaKFIQn|lLWr0ME<WT;h6|LXtc#+0nB2wpt_^#|1`zCny8&jkT-QTtg"
    "Uj4S$kz!TweflTCPXw#I*v}<Uhyr@ZPhJ78`=svac~Y6F&@4(s0ANaXd?ypeFT?amUPXVK6FracPG_8zqj`?"
    "?j)zGyE=EbxwO{S0<8dO%p=x4#J;^D7nT1&2AqF03_0&Ev>zcqqyz)9Z%(AO=Iav(9`}W0)6)#gwPy6GmI;{"
    "3ek4lo7aK1PqY|f#e1TR30c(S4?*qyqOo(>G)zF_==8O!F1#`IQPXE4NQSM?u!pdfQoBlr(AqdjnT^oTsKah"
    "ziBI;@r*%UoqWLwdh@Blb2CJ&1o=w}L#69u3}#?G3?mNRR8E&WACjk-v=44-N)!4(S+>S&$@TO-d5jN=c&aN"
    "VKzbo|cz-^GuRC?941}*^IWY5f=*U&A|bNaAUwlE{ozFT5JDTHZOX+x3fucpJfhgC1qyqVJ?p@Q!`6P@6?9@"
    "F$Wyq5MdvIbX?w-i|jU*{4d0Jon{Nn%|*~1uJgNQUe-q!o3v_2PP4m2XJR#jvTg&6Xe?-dafGR}unP{aeuK2"
    "W$0D=7RST=$fizWEZ?)W8{jd9*G$To(*fCx{6Oc*lhn8dBK5<&JE>l0PD>5nOia!K%$Lf-Gm1hesoHr035vx"
    "sn+W?*vU0lrW7dKFmp)yYw7d~2@KarzJ9%+EO9OsRczZ0ag-9Pe0hqguiz91x6r(=X{n_cJX1chwFbSx00X6"
    "Gt;o&sxC(m-^2_<H}bz<P_~7LxCpa`$QmkGn}1YE^P!0&T^SkpR{qVL(oVPrcgxar@2wDM25e7#jQFMl6wZJ"
    ")7s#Q9es2Jw)7f1ZgngOfv5|?+GZBo&x|fJ{4+%>zPA5^FVdw30BR@l0p+Q>4e#gZME0)6#Z>*g@GhgN1))i"
    "PT3WoQgB2b#&6Ad=&8oRki6n$D_6$@z?3`+L^7tob1ch(XrkDEvRWi+9GE=RY9tjP;+nC@bDv@~aAZ=Ki3ow"
    "Kb9n(;hiQU1zom?eM66chQSHnX8C|a$k39Ej#{<A#+1=XY1n|TFCA6y3@?2x5#~D?Ygc?MnRXwjvHQ>r7Qj5"
    "Ut{<#I~L{cH=*LJ)poC34oB@o91$6&f;D#rtKVT(2<uvYl#a+L=Q5fkZzzh*@UM|5dW{kR*STS1sI>JO%98O"
    "GS*lwrl%{Xupu{RFsuLLImIW3ZHvUCIn#me){tI9p{f@D?l3VK-2JSM;bv;N{|~_nonPG6uPaU7Vs*9E;qM{"
    "ZwW#R?pc6vo9jOy_8}%$w&8KGG)ka0JujE2qEPXxQ(X)99FSg{OAixs+RKBG&>PurNJ4I&hL}4Qkq5#{TN|P"
    "URL(i)RY7}KDl@L1;yI9)<i5-ZV+XdYsSy$J+3EwfdlRL`&udKUf9hc+%#giM~HE|07zqs3Z&9A(tGJS)___"
    "Rg=HZiwECg%I>glsh9M2rLNuU6Xtd!DJx5#lyc>iyq)p5%nmrwASMTE?P#ZKZRA4qZ5<=)pK0WXk{mTJN#fs"
    "%7^cDtdq+YE{w59#enZ|A~^@e3c#@N7LE&w*~(OMZ3{+mGRv|n{(j;@lP+INbuk&d4!!ks*`fu-<0hyx}t<*"
    "T{U0tp&<3WY)*D|wEJ*?kzlA^`Tx((h!#g_HZ~rAC4PFfW9>qNjj$VRW`7oyw(pAd1$g%C9M?I*u580{_{is"
    "!zctU_Lc?nMQxMP^jU5|4nzXqZ;|oY$^sKiZe&tpVCF3P@^sd$lyD+sllh58(S~Ll;LHcyx7zs?r=;{{+GP<"
    ")$`=r7vE_#_Sq6*$KGXA(`>T&{A>B<BAq0`r@l@$|IFW4;$wb`b&jEXE<DAiJuIp&<34~;n>H-O3?MET8=@|"
    "pUNI5Ov8V9rz~_C)z}g2P{eE?t(iDu2*D2MRBl&qkW72~U2d6k4txiI)o7KluC%0C2QbV?TJ>;4`b^WViFml"
    "v8+1*!vmys2LlOULUeW(t0EJLv*lp|`<ejK=MHb5NCoiMZ>dcdLLaQhWvuT7Q&40Bvq#v!+s(ZL{>5x2@S<W"
    "<9oq(v)hSIwJ0CAoKM+z$1#x_V}<90=d+*n09?EkMgf2*?xP57)%cfci~1#S`SaI`K`mk4Cmx#kN%&$C#2hk"
    "Qy-H8pIqNmcggx9b@k>7o_7wJ%i#tpEl=V&L8CZb!@xBh+Ui@qk@3$2BYs-A06;<$6Q#SUIXhSiyKGaC0WwU"
    "4)|mXCOwWO#pvBYAMa;p=P?~$=K>*nTc{lcRnYkjl3FtR9sPN1ISeO)ifY1f0^SGf-va#tyj3vstzRl{K#u^"
    "3yqWh7WM06)Ch6_vI32h-o)tnOnd_G<n?+Ozq?C%TvNkWp+sqZ6u_zh4)}gR1)q7X!&m}yqb9PR-;?WUVMQ_"
    "L($Xh@uJGUiPUc)p{ioNVd+w;qO0csj1cVTUx>2=AD!YNlTRRq~%%-RWJ`&?=hJQZ={FD`CCCI$6vks(+ORa"
    "8@C$_1YCMIRlu6FA4{_)5p=Y$0ja@40I4JOk4!G;pVe-a~34#C&KhP#=jm`%wN+Oq!^(qg|G2yQ1X=gE(gQ{"
    "jpjA_@g64-xV<>9ZzyxeEe>w8-2;m3ZHb*#Fi-N&`#DrVCw>2(I1NMD1q9DN@bQo;&w*R${06gr6$52h6A^}"
    "=~(<Gws{T1VTEbS(ksk8Zc18-t;vY(QN-3DVje@Rhv4*))ft|;Hi>``pT%3;iy@<{o#3L_VG5?#efRUaXLmR"
    "GBy-l~ds#V~{W_hpc6GJD1I;8a$lE6;r-w($@$P@T**(G753iC1Q_Ek5nub=ice?j_H^F2R7u5+(Vn9BIS@-"
    "#(SDXP-O|0OKGkazEjdPP}2?;4YAFl4u+|8ZC14zOR^wjLrA<8J+xO=|KCj)1H)MGO9VFskx@2jxJl}SAOW%"
    "nS^w`#;8tdVnE1cF-Z`++zsy`MEp2x=XFammh6jA|>y>k+*^e6_ou>>QqirraPgm=i42q`BRx1oz1phE0R;B"
    "v5NpeL1XvCPV*+^iW@teS#$(>^*LXHDt75@(tV(XcWz<d$RWe4+AWtLvuq-UG<VD$3GhTKpdUYNBI{6nyesA"
    "TF4)__x3*{w-6l^9(H$L2v{HSC903YRXr~&`muNL>-PTMtK`ke_D{R+mZP@541K|_Ta1QlptOEICLDVdaHjM"
    "cGU@XQn^Ui0iUs@)XD0mal2)Bf`=DOUOR_NGtrdef-aP{Nfmg}S_WpjdS6LqGIRDao{x61?71h%u%$*MRLo6"
    "QpyqrN~Ft%*j3+ZUXnGg_wZdIi>GZpSYVDnl0{PofPE=4bLLlkF?(V+GPU6u<?wYq`b*GH$ntAp@p|Mv=S>U"
    "tFlDl1!M%1uY`n#XYK&9%k``xHlqO->c=siAnR<DN?(z>EdKu{&$vSQ}p<bfXrKoo>?!Ku$>BqHzO2_9CMM1"
    "}DOl0GLo-Pp0XV>XHX*y9a5f<~)RrYF4MtTyBbNOmZh)=@uvvf-o@IdpW;KM}!)U1xl9)T$*EXSMW3SK%EJf"
    "`{{oc;OC+=NY7jnSAO1`Tclxui+U9d^jc8PVe_{hj#IcqNsX~}i2{-BD~u*$U%IOgXfpl{`5Y;3pQaRJ)dv7"
    "kw6^)b&hnp4z+88mZ~+2cn31o?2ow$>tXM*4R@k)~N%QUyPK%C9JxCQl2d@~aN4aJqZAxKs>H@gp5m{3EVZa"
    "N$gqorf1Kqw&dx;OPu7F9N+!QmO9CbpC6M#i*-=HkF!RA)|8!44c%@NQ87^ey?S+-~qQMn=Y-Gm&SsHwdy{)"
    "n}Unr^plvQpqc+)PxHD#ju~F;&|%#fJ;v&aj0#6lAF`bo*SRSXez=T#c4R3ioic_*SEMk1ti@LdPBa*fWTLK"
    "sqEOEqxy8Rq2c``H}?TfKWw-OpuN&fdOj10-wV_)KOe0d4KvopDRvAj?I(9Uw4mp_kKD^lt6cInn)4c6UMFv"
    "B6!m66O=X_A5TzFfc6~7C5|K*R=7j|WJdO&BYeUx^DCW?*%^hZ2Zgd)7h>?r7D_|ON7SVKoVjJ`E#0aCRCUZ"
    "J^Ny*Oj7_0kN=?<uDWW3@{>w$1q1w=UH!=H`KdL#7cV@5r$o~H8<cIB(-Q>;jJ}m{{kq@3d(`e#@t*x)W`uf"
    ">>$lHt`(K-%;n*PUKHvQ_6&1@g-CBN+cuCWbbU%pAzNvD<{3LmS@HgusR?FH~3rKuH%eUGCwd{hpUPJ{1PJv"
    "<tzbVzR)h{6`je)8t%Xn$|_*h6v9Z8(mv0CUFbS79)EgEgxKJw~bFft6W0AKfHWXxe>>w!w(ve~mZJmk1$H@"
    "LfgxlPV&W%V<FeTvr09T942jfGF?jgQ$8xpO!PFqV+;x;u`w{4!GbG4{l9K8$s7I0<-DYdOl#^Am$Oe69@d+"
    "^mO&Q(}9u>CkNeED4Xvk6u4+7#ORm!Y+IL2oNOPw`r+_z$=++!$HRLN53kluo$ROsVCQFnKhtLt_Z8yM)@Bs"
    "14tJm~`p<_ar*8LTW2#Ao#ak?uu-$QwcicC(qnTPHbtV+oyc*_0EYmpTf4f?jK<hY&xtK@jWcckJ?49my@9+"
    "IDQiVZNDi#9Oi--J!4!5Hu=gLll<>i~h>JIQs&B7*H<EN%kprV52V0n%ISnHGCaDO;_bHD>#0F)37RjTfo^4"
    "Csgy1viXct(`)t4B^K{MF4J+RrxZ{znMD{INt=Ip7Cu?3G8&I4FbY9DCHvd(=>wl0l8)?+u5GB+^%7iVzzL="
    "@ocXiC7l1)HS4kn(OXj(4-M#DYyZ0_NQv(^Gl4+EP?p5^fp-75Hg_YHf5?mfAKuo`udx0&9Hb;!X><{0jh>$"
    "&d|yg6IiS@<e&+`CQn?7G3ad=6~7(<@_Sac&E6Ci{vH)TYH}Lfdei#M;{SNF`zDY(Z0dPQ(`}2NndJ=J<PJl"
    "TbDB}C*n16W0i1(Ie}@b-Vm;&hH!--&p=K_Sq1j-!+ht<EjJ^sYjIDVp2P%%WIG}wae^sEU(2B@fJzkEFBp7"
    "cISqIrs!-HG{J2u0&pMHX`iOvlhTgK&nEkL~Tpx0J~^hm=2RnVXf-IDo0D?MyG4vo6vuQBzLhe3+2+uSJD+G"
    "nk9$5BRMIs4%Xp1_arlTZ+0E(MzgSiztIaLfXo6u>rJ4X&bn8q5B+3u%X0!$Za5PaA`JpFr4r-C-h2Uc+{If"
    "gB!cnDNkXWfG@{^beRZv@vFgvRXUFTiHY2dMLg9oiS#R;}6SMho-P*XrF0VwL=2qP>%}>*OHx0P53NPQ;1sb"
    "2w|%-CYwy^XinE&=ltMGA$G|NmeQ!JXw;_0-#`o4JNSu&Ij0_`N5ZD&rRiE7e_c-NX3$iIw};rGqp$W(07v{"
    ")priIwy?uhlIIs`MRs?pxNEK@u>rEFp5HL2$>8kEY#n{D9*Kru`3ZI{7L%vt??bRcNo;o50_xTvJ&Fc4_JhO"
    "_=JG6XT%%^^ioPJ0MG;oW8X0Zt=MobAf*qm3E_;Q|SSJm3VlzTs3@@cPsYJtSM(jbxe#}4?8RrlP)e7Wj99N"
    "cXc+?wFli&yQv29fb(=jYv5Z}x*yBRT6@Es|1j)C~M5SSPUAH>W#+XQ0ZllD!nS<*$#5bdr^$EM$)fZ0|O-X"
    "P)}l-TwFD@{{dzN-AAX;$zGk^(}f|Br*TGEownlvqsC&Pr#{n2B~v@EL=22_K0rQ?RA-(M)t&hIe=K3C>1bp"
    "!a}yyBD*aS{aUiO4R0PT05-}~_AE5s@nwHKc&vOJb7&%WmtfW%LNWNvBc*bJI{s?+WQQS|pKto6V5@iMf#DI"
    "0{x2LKE3{M%T}I0m)N!J&<p2%_zW%X4dWLukK~TSa^0Bj0wci-CF6At%F1h9!$%70ZP_;%7-L5CER?ba+@RR"
    "7gwlN`amkwG)F9>7{IwE8Uba4g+O^2?EOS6JQFegbUtgRxEHs(K|$wm=getVmZb1(^@jpkE9id720<CX)2P$"
    "Jdg#_{g<tKT=`^nIFRz<ZKjsdI6-8Kg^Ulz{D|fgkq4@cU|`;f3vkSCH@7;cWwbNb<V<U_e*9wV^DQeJk!Z<"
    "A4XuWC4i|gK;V%oJB^pX1MSfMjNEBNC2?1V8`L7+R4xCc<#w7mLlOA_ykI<or$k%-h1&)^37M@RwIs~UP<(q"
    "2yeewZBrE-KZvT##%1*4>*$yKhp@>yF!$tTZzH0HxIsN9u+b3Jfc*M<XdxduK0@yiK}2Ai760<T-z3y~WqWE"
    "EPq&s17LZi$um2j{f<Z9b<63@Vej&U9c5?(=z-Jo49p1FNyM1+7leK-N7>QjabVr#8hIf2(u=Dfw!B3VUrZV"
    "}Q*3uy1(i7`Tw>#ShJG=Y)O&_0Ux7qEbxB2T82|yqbbd5?dS6>>du@?ml5AU-3*ps)>Ue=Rv4l;Fg!c<=$Fj"
    "_ZUC4-T-Dm2$J40@<j-{lrl|Ks8DPlu<cy9f1C4+YGZv$}~lx6y}K6~5^{_R@F6bh`}<A2f}c36Q4wsc_rt>"
    "YGQ~Z%%^BCPi5A2BI%=?Hp6;T`dQcvY+S(u$)ZPRC08h-KkeJnnJ&oQklUx9^t>?_bdasZfTun)Vm;?-dZ7Z"
    "W%@n~Xm$|91(t4tFMOXlXPVGz`7WO*A(4yk_^KE-Khz!VNLnGAIPv9jNX>(xZ>BVWQfv+Q!?SW$T1TjHcs=2"
    "sEO2T;E0X@ZmEfTe0vw?rAeeERzyLGNh&DsFTM-@MxnLnI>6%<RuZEr=TvtjZFzm6I%jai?kk13u%NjmzPpm"
    "vvjeEICpMUcL-Eh9xP)D6Oi#_$(YnMRrdYA&>S(^PdHmqwBI^F(BY#@N{h@*lA`|v9!XeeR(bb~L{`tWHSNE"
    "#YJjIKfIC-APdJ@|p0Lx(L5KInh4ANV-Ij|c4CayOI@^Bp8<-@+HzbACHCVZ$n&n7Iu3(-I{%Ws@NV6rvxEu"
    "9Kj$+S8^~3G%f?SNR_hm+pL~)?7@7NLw2c|J!M~7BH!yfTZ%i>>JR~ZXe`VL@I?^wz_l@M#6@|3du`33<b!w"
    "9J04v7sU)BkR-^yzx&?H<p66?nP0<p=}?${|77o{y@S&@GCxmuk6-(FEPR*#fmdUu!sux-zz_E^5!lbBQr%e"
    "@S#_$^=AVwYUniIf8K^LIiSf%4y57NtDc1)-(G+OthuXpaOqaLWJRdpn#$e7Qa3h=}68a$6SVt$*>=*NXUMj"
    "wtFZ`?~=p+`fg09FXR3o5p@=u-rrCaT`K!lKS8~H?9ZwP$0*Ia2b%Q?oTSx^*|YmAi&VDa)Y!Sx%oDSKg}U7"
    "fkEsY&rE!T{C?Kv)6P|2cZJB1pmOQB7?ph;FY9U07*N{9GXo4i7MSZbOS`)|-3s9MpfrO2l&H1(+X4G_t~t;"
    "2!f9y3~E>0$#_mys0TZ(nK7=?c&S>j2#NjcD8ET04XV-hCaMh3o-{k4y4Pqw8uL(c?z(5+HJHh(kw-L2T^C^"
    "&A~4Rhrb<c#2Y8O2e0-He%k0ZRE5Oy9Kj+$il%hu2aPn`v{Rgv8ZS;z2R(%8thvgRn?Dr#A0+yU31tU(=<mt"
    "F?(VA-D?a{VEt>fv+McS}VOyUSaf#3+1Yz}#{KdlhH-J^3lcJ_YI7`R`BUyhXej-)Ur4ly!(cxU3@ql~+zBR"
    "CkruWfJHW~M8i^s_kwTkO|Mm>`7)yuJ*Jk3k7PV+YVY*9+9k@q<~u*Gw$93|_zK0^QFM(ecr##%hqb?bP6Kr"
    "P;3P#g@$8m=g8T0{N~1;&WtJ`ruf7H>&Ymui!|3*TNDyyYS|_<>xZ1A8^`u0F8i#yM(5r0Wo8TcTW_7~2wIx"
    "B%L^{K-mTZ9_(1MEk`xK;;5x$7P0oIx_vKx1j0^0IlB62!2WOW=Hc3BgN85sOk<$GoM3d3G}~SGGV+AM)ioB"
    "3!hod0OpPU`6VD%f74xekZ_2esuT3LZOClL?283}C!>{08gCq%k*A<PFE-=o`O~NJChB>*k9dY}wK6Up9vxX"
    "Oh{_lw%RisO@(!PysxVMn)Xn7I@&sym7mKU1RT!@DdW!uI@k<apfcm{@;oM<`g>2pdEHbPCQ(}$}2tTQ!xIt"
    "YxpxW|5rXegzLw|Q1oOCin#F3=;p3%1ySt_w%HhlZ!a+y!YI3AKxvS@!fx>u4)08@Zla}#JoC2{N?jGUqz<i"
    "RWQQKtG*&9%!z33h8`0GgzUfFae1k*~IBM|f85dJ&+ZG(ZZttQu!^Xj!1qhMPj$wHDzu(i|l?CNwFwV?J;n9"
    "k!M0;!6y?Ab!5eE%Av}lQ7u>73v*%k^YPGHcd8ZKFZd}Gc_)s>MORrz2>fE#ST9ZG{c_9t9RrR3g1?oU<zg&"
    "wehiZqwqh=_*PfrihYyrTaI^h6)S)`S=J8pmMvI0%dSU7{0e72LPMRJ%gF>4tP)~#$(@&udm!0HBQ|kF-ltZ"
    "L^4-!M;mI#=dcSTT?CtMwubd*vNeb6c`+8O3G098v3zzY@(@V8amuiSqy7$fLPGs4u%*(CUf`uJ#J;5aom-w"
    "p$hZW5W_%a%jnO&85WFRl3RDi5p^I!mKkobO&63ypXaR$k35$(MqJFT_~M|Stxd|rJNYd5V!_wTa%HQ&%Kth"
    "L@^mrR&?wpP5HazU(hK1iOzbzkD>f7RWqwFihHRcpRwO1P}`nnX2L$^kml`qhigRofB~J$f_gLbZ+Oo5|+NR"
    "y5v6Q%kEFk?8)KB8@M;UfB(*w>VyUOlB2NG^gxZD@S=>$c`Ud+K~WC9{29;Xx8IY`^PrHiTOP(a6PIOof-On"
    "*n1PUHm+<@^siJq_g*AhQou>v32w!QfSl$8gBx%sxwfAuqyluTfmTT-v=9INt#MDat5m|cPrvVb=^?0wU3;&"
    "+_L_$_W`=$a29V*P&8ebQ<7`!9LO_M3{79S2k9bViZugY(FQQVs-lLEzX&QyGe9MVcfEis%AM{E32mev5j`F"
    "_9>a#zv>&*ys-0?V_q*f2fvjt`#JWs-5sPzw*W4;(=<6#NchxhyPM&6K;(_Q{|ttxF258+g5>*-Xljf;snBr"
    "()PI09OUDG;V*B^L5axq(IZs?&Cr=2z5KZ&jH#cr{*z&2P+Cul31&>a|_p4grQEGvrTco=N$xT`E4a2MTs8c"
    "}d$heVB@B8M?$x*(@$b*r$uEopbg46AIlh^J)6+Pq>>_*O_F43}0PRYtC7$z|xb0g=_D?zyK|QO>4pc9*i{W"
    "0y+JE-lpw;zQ_ODZ2!=2zyGw^diKrT|1tzc(5CwRo%a8Qw>$XyR_ocf&g&>4&zHQ5{uq<dv_H<Kmy4_JR*TB"
    "b%CGOYet2r^AnbXTy82T2o8Q-tVizQLaMvMkoULa~*YF|1n#1#LvsHKma<jUY1yqY$Rmk7@Y&jqBkDvq{pOh"
    "nQ`^PPXvf?>>F8)#Np`N3M1+9$()*ePVRl4lBrP=*%78GXysL?RtnH;PnfuuY|H!?sX0O-C~$ogB;pvHMj-i"
    "O=YZ9OgA#ZTcqYDyEn$@9V6PxZEIH;n`qND+MpK18O-Y%oQYzE~t=od9i3VXG6JZQPr<#L%_r(oykm@?s_En"
    "nMA*)Jfdzi`&hLU7JBEX~_l9SyHi804y7zaTZ*8IQcZ6-Mrm=?<P{|J9n#tH)J|4j0fp;3TSzokS{MAJ_qp3"
    "vBey2C7VU48S#{iE%DysWl$`{x4W>zFn58~W)zUP?CuK>jC3vD8Emke=af)YV_y4*C%xm-WdHE=C_Xv!K{`%"
    "+n)ooZBtxuOh`@jM=<hoRZ+a(5<3&sUQ%tF;Jg6-<tF{@>Z$)D+2K~`$JHQ<lfCX5l)I8wukX6xs-0PH9-?6"
    "Lj2m%C6Iq{!Q28AdJQrBW5CN);ljgb%MdRLaYOV;h;%9L1}kn|d)Iy6j+EHp>X>>$5RlO>|;kHL63%#zs{ed"
    "d!%I>+`P#J5@2(H>!@M+nn+Dy`)-RLH+(t09a!_bfoz`7?jclwC5aK?%g5LXN3}>ETzX&@<XF$818GT_mZn3"
    "TZ&gofy+Gbw<}_A48HZnY0&sdaOe$YaF4y9@e~Gmo~0>r0;u@fvL}^41nye`Iug5Cibju#g6jPVX}L4`0`+X"
    "_tf&Ty`w}Z8qzKutE+!J*(yKoWvAIatmrc=IgyC^GZ3!Ga#QON-Z@f^OW3qXYWW!g1e@Qwy-`}pW0IgoljTG"
    "k(LLRiemo?B`Ta_?C#%F>Y+*Hgc^&@*u2xSFK>Pj(&DIgdj|WM*z0iC+16aug9NdOhRy9tu*-h@JCr46~*Gx"
    "-xQ<6(LMAg|SBHRi|qCQ%=9c+0;2mu%3Gwj-#56F2zeU?D(V1WJ~0%(JuU~GDyJb~FIl!3(8#a#cs8H2g+sR"
    "Tj}fWYxUul$gKG|oY~aA7-XwEda161hMvN}J8M+k!OjU3onnN+5gC64>p$!es9ln<rtt3X4yd%W(=q&1ejw_"
    "v@pR{oj&{ae9fNPZvwT!u)nJ9!)<mGkCfG@+d(!a30Fv*WCZFFON5xb<vqW&w4lKGT>B-*v*roQ01fk@!rwl"
    "!SBg`C&2qaznV8@IiB^S{^8Nfql1H^U-5u$Hlq(5QsN&!ppBc{2wILkxaLH3_!=d)a)JuYp&8^t!Xp<$ddR*"
    ">+`cjsR$3Ab`5PCg=r<%U7S}(Wd9ll0)K<Faob>lkj(a~hbd*jG^c{F1HLGwh=A(aNtC+24{cpbiHd=4*0k)"
    "<*yO+MJ@d|zf1VSbY!XKiEz3C857`3LuVoAo`R*T8R1t`Rn0UB6yHP5r#8K6C$BaX;1YnH=I4Ttq0`Uy8KGY"
    "QTmnJ%<VIRPy=!&>ZBa(n1`DLe<1W<)(b{I=fMLwJ~p>e_Ugw-RT{odKxjI2xQ9_fQy73S385)F}jHpUr9_4"
    "YB+~#9b^XBn^es-AOz0GL1ZP??lM@eZe$nVmw4e@lRcySq=4&HbFkd(knoU(@CE5o`WPh&2AFoNV=D}c66NV"
    "|9p4^00{&)23CW4sw5l9>|1J#2(+x`8t`i=C|YWk>~MM-9UH7h$DXIC_N6>c^Q`0`gt>?IED-)v{au!g_)kL"
    "cR?_KojG!d;qA5Fx6O13oHQ(`a2}dAe3t7xaE4TTWnrY~9tD^A3^?)Bn`l;Ba%2S|njV(sQvPPLKW0EC<O>^"
    "U?V4+TDHg_w%-P4Mw42Br7VS0g*$kX@DP>gbfY7L0+^6ETN7?@dGMayZ>2~<Ng+<ure#rG|zB_OrOeBbg+p;"
    "*~7M}w$IAtI}&j{C<osq>te%A$SPl9P}%_{g?Fq8jM|4?zc$hFC>}+=<<=K<Th!8*U1hA=YMG0W7L{AJQ`Md"
    "2rG91YJdwYchmg&c#laFGsOv)m6;O;?JhmoYJGI+{sH-MjFkn@SHs|OQT3V|DIckJ9iVCX>1Fj5=Mv&foE3<"
    "p?LHV!bAlIYV-r3qg9hdp9JoUWRbC<bwrL0VIP)b6i&HFd;a!;fSoVTQ5}($lDvnVq@`Unn@`Z6;Wv?%$2oB"
    "_Z!}j(=XM3~FB%f#CDEvECgdUn&Fx<H=dY+$tKgjg16ScNSOqe`Znj+Hqao*LkYPzuEr&C=q~=$qc^Tj@wwl"
    "#8>rR^f6gfqrZmISSj(Ria9^``$9lyYL6g&T9)7YaT#OrL1CGOyBrqDX`E)g)Laf6RN!zG14*_o~sC5qN$At"
    "@0<vSVi=iqiZ{yLItPTlb-4Ro0(keM{FC#D`gV&QQ!iq1DyNP&X0}qB!B~wjPbUGSNovTOKFo&KgD|4po;Qk"
    "EL4~1`Y=diS!GpD6O_6)>UfTlYsN18Oa%ltV;dOZ@=$<_vdHT$9*&<I;|^{n%CAZiS_zWU@BTs*5!YnF9<aw"
    "r4MRy96irKJ{fb=W!kiKRkkS1W*`uB)^CgV0i;$Ac4sQ0f@?*CyhxdavPa8mFVtzK$1k`p=T&d@ZPAKA<SdR"
    "A7dlJ7z*ymYK#X8?xmaVvDU%U$P1+}{4Fmi1$%Vf)G?MN1F?`|9#bnnUOev3QLFPlOwDM|%fke0Kh<>ACi^r"
    "&{KpC@iYN4vVqr;wG+K$WFX@6y7bJr584XtvgcfwDGu7F_hU^30tW;616S<U`Qa(Hx_9KJa?h}Y3<k;lp{9{"
    "H_@{?_TCK82Pi;yONISMk7PpgbEkWJlZ+TX9-H#R`NuSd!+_NicRmEk-Jaj)rmUM7tIFr0k=N16Vv}`@5~DW"
    "iO#K49nsYZ0*bX8(w}2Bt8B%+Slfs(-X-PEHXHdUPyx8j`Ej);A>|$g01TnGom6q|5%4?(R1&s`iPqs-QM9o"
    "3k&O8$lz#z(wF&(uaf^fIXVQknodxDLV1w5Vm5`T1G~94!dTu(_Dly<(s5YqBcmrK>JDcekNrDVf?~}x)ATg"
    "I&9PHmB<;dd+;@+DpDig?j#74#NjgQ-5zYey%j-_^1}jKYBSMPYrdVxmy#*5WBwLIIorsU*m>ohWJ%Sj*Vcx"
    "_SiIt<ZN|}zypfk__V9W?mgK;{VpzVaxN+Msm0SW#Za33f?d<jK-5XM1-COLLKA$@?tg*(YEx2KK8_T-oXNy"
    "j#ed}B7oZ^MXqvbhZ^hHue2NU5-vp6z!ajiL9&K`2EJul+{L-9Bf-mO01AdOO5NRNr}DBeYNoNP3ZlAiuOVc"
    "q!4i=9acghux7zg)Q1ETWr8oG|Mh7U?KSzi7lK^%-@Q>u82q!W0%?9m3pZxV6c_Ep3eYfXXDZ+z<}jxj3T05"
    "OF}rbxADIwj_^Ossv0bjYb2lq7<wHgw}V!gp%gE!B->EZdWA9IT$+5vT1@JLn;JlYT1LMQ2(;*9ie0~txP1{"
    "uZ@4}oxZSa3aIoPpwri)$&Wyrl?cseSzniNK;`T#iex2nbR%``a3DAKtm)noGuL@YQooW<1?xX`3n$vE+{C#"
    "uRS*XJbYcxpHQCWW@Lo?NkxEL+i6oCWls%f!Kkg9fN)YG9K91Sx-OY%UFT~YV`Kah05Nw~GBpk31}7686&qp"
    "`f=B|O_eqU}4BIpDp8kBw(DtQCn*wX~YN=&ynC6NLgXkjf}J1_3)dM9V~RZU-Yp1~+rl_zZkAi>ld3Kem-}<"
    "R6wMNFyac(Sah3n=9<vxDCvIYfI9U=++2Jqe>Gl>M-GPF>xFEfCO%=h}<v-1oJ^I=YT5eVKw7?Rt%?4IUDvF"
    "hLeBxsH6h2K{Q}t9m3glv1MF|0ZUVLho%A&@)`h(N(Pj3tfBGYspoDW+{1+hFZaTqy0nk=CSthja0IM!F41U"
    "s6q&JrD7Jy3hV+YRx;+tQLr_smT$qoH+Js^_D^2o-iQM|I)KIMt%T}}0->4s|-4t*+{V<)~O!dXU@JEgwr<k"
    "-ng|>~i`0fa^9DrR6kl}%v;LU}Q8gGXPP2<+1`D!B4?d3l9x=I`<gfs6@tOP8kY@z{TS&)|XK;V7-JCcK~tC"
    "ftJZTfyO1J}053{HMgN~g0kxaCKG{^@mTQ&`eehPoLnc<N$X6x!4OklkuqZi#XPR@vpI)+lgpV{214@G9=dY"
    "cTDiNF$YY<@1$3J=TZNZ<@1@VZ@#%)F~*&GD8W~?hr_xbQz_y%PA%tb&?$_+i_0y1>8|NInO8pw%T0^ScQs="
    "Ie#sV!k5c)IPZ8ufzMG+RkFX=Dd}ltI-z~npg#|HUiD61@9a{CYNlw|f#wMV68_DrCqQ^uU*BW9wXzEU9eAf"
    "3RWlxOQ0SIM8l<y40O2vEjS{7tQdEMm(Xeucnmz>@=j1AKGL4+W1+UDO`C5S(whs#T38~o$M2$hxFF`C*i2Q"
    "v@rx`3P`fvO%Z2P#;j74wAz7e;M1Z))J{?Vxw7Wlkz3$;i&St*#tM@#Cc@ed4D-9LV%<!kqP2m4rx5$lZvhC"
    "hPlDw(jrhN2c2NvBZ4$f_KRi|2S=xcJy}3KucQXi6;$@DiJzN{g3AroCMV5)0v^IT8SZ<DHjM|7GX(>*J%p6"
    "ENc4JtDR7B4bmLQ#;lJHwrNt1xFUM{w%FH{h#d@_Ox!5x9s5Q^8rA^-HN^)wdWt1yPPM#ZNcA<u;G9<<1y|s"
    "Lt<Q`VzaVmONEy#<|(7ubd2#uU1g>ri2GqKSTarrR8ZOP!*^FYsRxL2(#A>Qdq8<xLVsF@*!WG4#NOOuo>?m"
    "mr6f$s?Kx<Omhjz{iIg#t`(u_pyv}c;bu=q8I_!6x=ozm&Q6y}}zT`&A@T6j~GnDS<-ry2t+kt7rM#OLeAy="
    "{pEEcS$VoD)aOOm@PV{IEnw-7_a8F@D{YCOco5s{}9SL60QA{)nzAN&Cqe4Wiq)5y3u+iJy3ZFA_zhnJK{tK"
    "HK2KQE*_Bt<x1ph+fc2(X%}7~&NFq98<}8ZSIaD9gX*G-v`m0x5u4+87o*OmE$(aM@!a>b#%U^i%j!QF$^oI"
    "s{H+)IbNoJ=IUP7_TFWJboy7tIDdx(-Nd9*p28eP&}=vLGc{&qwLw*9JQ5{i6wWXg9}UWRJUf`z!F6u<M)`L"
    "e}h6H$D_*;DgnOG@9AoN#R!h1@~bJ5K)+VNFXw0#Gd&zPr`cj%y-@dn?UimdKK@oqT8#;6H9=)(N7Iqa;!8B"
    "Yqxhwe3~d)h6sQtD@3_Wzz_67-6;QwwqAf#Kvhd179cwo%9jK!QLquwwI`gFa;8#T2u}%vrHzoqCarhX7L^u"
    "#GlCQwb+!g{Z7j==+S;H$vZp%W9^p^an<S%YjuZIzVHq0wAG%|`14-wKW{1-(V$}3P?w~8rSQQ<_^>sYeOa_"
    "A%msM^j|AjC%Cc7^HqF_e^B2^F%Jhujr8=|(mzdXh+m5ISmVFgit>6<LO|+j?ko%#vA*Z)IoE`X?pEu=5Ysh"
    "*P7yAJE5h#z|abSc_PZFsIAh@wE%SX_odQ)#UWI#=Pn5CJEEUEnA<!50;bVI4yIsP=fkrC!yEZwVnjJR?<+&"
    "wC<g;T0?!>-8t#uhY!8V=~^$nWooF$g#T0Lwc_300gSw%{CgvTA#MBA^V{x=pqVOMC=O!Ua*{CFec`jZ;2cX"
    "oN0AmudU$hs^lImHf0tXZSkfo`R<vyd!rKZ)brNXT$aZHfQ5PG_b2kd3-<n;;DAUe}3yIF=(ua~0;w%fqtNJ"
    "5Ie78xB(ht-1`-J)r1yx!dr$oI8Rg8Z_A)2!Z{-;IgAbmhXk5n>^nm1iqy+3VVfWUdR_*%UgOgT720qe@3$b"
    "j|l6FNv-3sS`&F^*9=s7WWB*cxW1`<iSX(%iJt)b!=eO!biAVQICoY_&?Lc6WnV{YDv)wzDUyEHoP^awR==m"
    "v)bu0!;S|qPHq2oln)=dICi?DoA>BD3H|jFOMQEJ?HvnwSdO%4}6eX-7UG*9iD0U9%X7%7p#1FaWVP>zSeQQ"
    "wv@Tsrx5q1CQ9;1RLayR1f?!o`Y2Hmwj~xCII4&yWqof=-~<5^OU8{u@=qD^6l)~GW_6+p48#S<A<#q1TGDl"
    "`p|Sc>8tKNB#7)El<{tyNT*IEDoH_o&kc_&cIU4#J?nFr~=ugvWm&|j~Gw`Rb4MmlYysuS+$|2F*WjQc3AQ@"
    "*pY9z6APD+}$JSE{x$A+@AyW4wxs)m!}-hTq(hmMJ=NzImv!E9oZpRjq&c$rfnN-r}mqQ95Bh{~s8*W?ZOC("
    "l2xtWzqel9%2*TO;K-1UQ|+6fv8tC2F9sE<R{<Em@rdsit2tr*i1n%_*^P)De-$0C$s$fHVZP2t!B64UM^5^"
    "0=8fH`pZKdJMkI@(rqlr#c#dUxQn|XvxRQCH97gCoDb6R7E(qh|)^D_66J;Jtna?@3(+;M3j~vvhOInUFYv7"
    "rJ_thgh_%6MNn)8%PUbt%J{GJom#<yZ3~GAp4@rgHz{0<^On8v`Ds){l@(NtwOP)WiQ#&9O@Tc6#=jqmis}S"
    "gsXvH8Xs(_a2mY3u6Al?zdg>kt|DW&rD%qyMG3LYtnly8+TkT$}?>;NXf}rdr76U~s(P2|bNbNOFKb<D&d5-"
    "o{j?y%Nn@VrkV>Fth<T^;tv5Nk9Mz*j~ZX+?1bm1vl*iQvZx?!-Y#Bh$&TZ-zVl$E@boKls|IgFl%4bc=%65"
    "zwRwQ!v>2qG2M{zb~R_~>+Y9jxqn-Dqm%O}$Q4J2yAgs_ylR5!h41n0m#F%*N^PoUSnyVMv)b=3snQglDCP="
    "HJ+K5b>_ro5mr5H|0FmGlvqbSaRlf7y!zUw=NZ59;Ks?<4q|v@iT?ONQa{eN*9Fe>om64jq8Y+1&XYc<BX!F"
    "iPB`%7{4uhHn8rMJ!ZQBY+K4v_ON2awxC1lg9USABt7)Ym|Mte=o?#h_I}@Jr61D~)h6ku7qGM4%_P>pQ-kR"
    "Y*L5w~RFw>)gEn?|4tIM82k>{Z%C_V>P0Ls7WwBd+>#uqpIj9)&L1x%EYh2A4chmroxw%jhvkDYtILh_*c?Q"
    "Y@(%4%}I>|>|70gv842Lw)D8}hHxW&<kHmjF%n1bXw7u^brm@`MyTnd;3&=#cGoCJv^hFYalPZKUf=2W5RBr"
    "ll-3}rIU)l&rv#F*DKAzm(AHo_{`EGhHAlHIC;GPPB{^9+k_<Xns?2n)8_o-govi}qw*qn&#EqTuSTF+0N)h"
    "E$3rjWZDSeiUOR9@L8P`8s-C{k+&7T;&o6jFJZA=&8lfPkBp(ut-*eEAblzi#N07>2O7+Si3o*j30Co^x}RU"
    "gIuUOl6T)oQ<^A!SInm?MqB*r=J93pMtS6aT2!=^y60X9%NLJVAg|MUl?$bqLcW|d*ycfn5Y~&EcR9TAFt=i"
    "EYp(`WS)=b_oSOiyEOw|OqTw$Dlkzv#h>q|F;rNI(A|jfFNeF(tH7yd+5${+gLoIUU0P2`GrbKg83$I2b!Ih"
    "&q?)&1~)Fs@GP&0n1RHCaNHNq#}91`Q?VYiI&%u>OvDLI1%qflMah}LzEj=obJ0Z7t`3CQbi5-rh?>pD88ex"
    "@qNu5JjRz~-M?$`eGjVF?`MuNCLA7%^;^ilpW?%LDl23ChhYJf$;fdr{JV=@wpJA7zY)ge9H<KFcxH|Iadmz"
    "zOzkndeud>lInu7U5%Vh5H4|+A(9{vU+?Yw1c7z!~?oXuyR0m|C2?=2JXaaV;-Yf@AXQzMV$G{D5`kw{feit"
    "r9cfNRR;IVZ0bldbVBW=Vp$nq;EV{HoG<QvqaXo09?E7>nO#S^tR-2lBXX@Lc0F)xhe``c)R17&C2lt;36qF"
    "h4DKP?-nsUC>b?=RFGO4`QXgiWsIJwfg=0?RCX=LTJEdjUFP5N^Yj@1&)?&yGEh_S$%}5qh67qk{rfnNu1V("
    "LhLmEo0NHZ~I2XxhTWSqrkS*T0$ZB-zUXpl8yS^R3OD=fm;-f;+<fs}7HzqN5D>Q)>{MQAo6F@9>jj?c=hEo"
    "dbI-;rte!cyIRP3z^Eo_dEEqN#321`>OuYSsKt#SnsA&7cR`%WN|pjyEt_<iabOb=2a(B2pGax<tbqb<-~B<"
    "^RS`4le}6GX~X7-*Jj)nXDyKW_Ja?nlcNOEY!ZSydI`fLalbBpFLE_ie}S3w%+W@zn{c{p&4DelqSyAit#rl"
    "h|60WE%SOasH_pDJjgQMy44}x+rlyx*QwCN`;ve_*iL~(2jIn_Xt04>tAlgQ`OqY9DT3nC9$fA{b4G$p5r>%"
    "6>7?chLP7&t8iQR1wACHf9wvr=!%%{n(Wws>)UMsYB0=rb`+CAWs=MugJL;la<uLQBpOoxWP|~rqAHydv@~4"
    "CpyU$dwc+I&5wA@V?zN=AG4|~>6Qn#qytI?&zGHm^@4YE%<2lYc*h~j#&L9aHtZy8mL>yyp1$!w8Dit3&0{<"
    "ZgNN7{MerQPEmBJk<XPY1n-n9|Td6g;B6pL@s2>*M`bJIB8#zw~}jV6fd^0E@A7bF-CDsBCiD`|Z?JN7Wb-m"
    "W6Z-Q#*C9_j2dW!6_>I&FAl?acUrQ!L%{@f}1dwVCCX@<0|{3!Sz<o$FuXs*0U!3^SpF*WCXEGqZvEvY5_|c"
    "U4o43EhTw#xc|2|JyWqYzEG;B7~E2Ws6U*pUEQfXfK@Uppw(iF1Py31Y7!Vnr=g{2@scwSaoO{0Sbu$*jmu_"
    "5zP=3`U^Kc$Gg;Zw8!anBl|1rV)wHRzGy8{oz2AbJ>9hECbQoN3NG%s#UBw354vf0ZdG?Pe3ZoHo{}6_G)jK"
    "?GspBwM!*TB=kdMP%z`0;bBU5>^V&huL1W*R+o_fQ2fCyLcU!b&AqG%io;|Qp&mKSLK9QV1RQC>taInUv9Ki"
    "U|_Db`*dF0&A`vMB}vRGjcF#mrh*R|DZHq32d#ttMf?{#TuCYQ7tQo10C9$DQlF$Hpi*n9?Sp9D3ernGhAuj"
    "$O2^DC!-eSX*0ey6IJ+M`~UUS}9xKsDO#Iv<NP1H<%b$q7YjNl}&lu+0R0=h1Fo=BK2zC^Z@2Gp;`w-A_G>P"
    "-uu%Tqy7ZIl2Ee{gk1Nk<fO}8=X_UlDo$f+C60een2B$7c3F{Ftt+{i+DnBo#m-3OaW~$cwZs+2M^_}-rnip"
    "c^s8Kh<2hU@=adOuOdI>sz`EhlN?$&?xBwNi@Esi6%6cm8^`CC87WjtgXnbp#Wt6uJ)7vsYiHw%7KCC7wq6("
    "PY)&e7lYK(}HEfd5Tr$A!m=q|lbItXiP*4i8p#B<A4Dz?Z-XfB&{M7035cMeWrx+SD!XKydrJvw;v>QKT2OZ"
    "lg%__$FzCP}}}h-<>H_P9ZOpugyQjAxyg4=_1Za4LsVR5;%M8J`KZrLS>Vebc$=-Sns4ODugMc7dap$?7^@v"
    "ZEg7k+NVg+|T=mi5U2fclJ+ujh&y4j)6*Uh}lfbp12L9Hk!{deYAucY&q1R9<a1vZJ8`q1u9y+3}6A36yT)a"
    "D2V-)K%klGt8oyN@eK5Epl-=!9PTA-$Km2|aV@0Va4JBiWb~{MlxymMLi|<>-Vdzl)sm@v;PzQ+QZxv}(r_m"
    "l@|cQTvcztM#N`+aWgGQ`7B(|3Wbt_;G0X7~#Y9y#s;TVbpo1xpS0Zki`;Ne6hD#SQt`IxFPuD)bRQtMQKd~"
    "BieO_@60x<|${pf*Mha%vVs>lJ}Zv|fq@P_8LiZ;;F(Ih5g`K@e=R3biGP>ItImGfnbQA@=MX?$~!3G=7cqh"
    "(U0+$Ce4g0T|)LmeYUU8ty^$Z4-L#4t;T)af$NbREgAPXc(EMCnK+@Nk)!F7bKQQhYsW(wF`Ucwk{%$?grWR"
    "}i)o60O40Td_5^+!X}~<nD6?9@(naCeD8i@!*@4<b`zwPcnnq$9L26q0MsPtT-SFqN@j7V?^ng1#D(=J<b+Y"
    "ww4N+K>{ZF*qC{Q@%{}rwK5_&Xu*e24<Ji<IE706LrX^V=SzFa9gDm7+3RsS?Uz^tqBAnK1<Y5P_v7<J8xBK"
    "n9d`BYYUQ)gnk}Y>dJ8lK#8;i?`r3foRqmc@0UiEutSYV%K6@XAp$#m}-0L6p?^Yi5qW<Xz1D6Q^8nXq!VoQ"
    "_%7KMiEGp!9R^aX#KpyG{Y8A3f<jZpIpyC1D*`;G9;wG4AH(;2qU9^S?+!7-t{)bMS%YCRu|Z&IuDxCp5FYC"
    "`i6P;ROv$~t*4psn0vr>`k96vqw1qNPKbg|>9eCTww7x8Ecru<NR|@hhTyMj>6cAsc_Mv(c;={oS;p1*Ma)K"
    "#eC`(aglwhUPVGREi2bow`<mO5jAdqf#U0XRKX-0`bN4zOL-63z<^>%Fauq5L)H4sHRiJtHa)}oqK>&mc&^8"
    "z(|Eds>c|o2k+WhS`5Q$HL=W(NWd3$0z8OL0)Lr_0HEuE8$;*wD*?A-AmRCn5BGuLPXV<^PkO)YpPZg3;Vf$"
    "wqV(0ovpB&i^3Ejv1Bqkxo0_M|+afucZg8)&9K4E~-Mz<-y_-HbhW$?>7UB{<P@bx-Sl2Zy!R{4LwKh5$o)a"
    "RZxe=#P1|1PS?u!)ix9(n@6}yMdU$hLSWG^o9kmKEvcZL}!L|2Q1Dvzv=^U3BPM}y4oo+-)MSF>E2<P4LOza"
    "3zURxBR5;P#)-6BF@klbT>q1RTfL+_!n=EH{77ZEwu{A7hxoH}?1P9AvmbmfNTETl@DSn_ORv#@Wh7n^=l(J"
    "UZ7Yy{6`z@&1~nT{X*lVrne@RhEtySH*&a(a?FSFp~RyySR%wcL~{gA8kjoDr?<~&NWm4l&{9)W;9Ri=i{R{"
    "ud$W1Mz0k@-6T91yT(%gtlEk5n4PF`Gf6#3NaB(<j^7*}a^9wL5tFwW&Do5F<7qucZm3ZRW$b*BKzavyUZ5T"
    "~9NLy`_d@~+u;R4f@E3e?lgfBA(7m1<NYFODSkj~|5BlFUWgbk&m+kfNrwnntAa8g3ta_yhGF9oeC6l#=^#_"
    "}<PwZ6<I@tfEmuxK1z%@@N+y6UOEEOdHL)q`YMkizEJRM*O06$g7DV4BI<cSCe{$Xn=JI{2e0anf_D(>}B-p"
    "_9*<I(g(qgY$%C6LM<y=V$7(OkSj4VsC-Uof%N?nl_p*qMA7j^+*ip_Mb~t^VwTHu&Xw#l1hY1Q(G5{LCc%0"
    "Mu_dTT*cmG%uk{a<QcLew>YCS|cU13tMo?Oou}4W>`jamSalLwBgLLg%^+dBxfZ5%|Cj-?H=ggzaAeQ9{k=)"
    "HfPT^H)Wo1gUWg}?BLN%JIdD)PNlf%ew(s)@@aaVU(LdD20k_mD(JJtS`d22AyBW6cYc1gBRx*h5j?oc1|JG"
    "^h?68{AELd&Vx_hi6U?v)4Vzq~Tqm#@=I}Y_K(K%JXnv06Msev2*yKs@Spe=uemfmB_-+T;_H@>0`q_g&!C~"
    "mppMKht`?=+m(3_Gwrk4S(nbmo0!Fk=Qgolz%a1c2v%sGQj#xsjLuaPxy2@{UX8rp<AZr+LIcd_H(6*XGVTl"
    "nx4Xw&sAHgZR}VofvMS}mpXOO{=8{Wy$ov(m<NHq5r=IH0J4kDxpwX~Q|joet@H7PBNzACEKE_!(wsY2hvoH"
    "`r7Z51oFYqjI01fE+w-izr&WjE8A$b9sCt$I?6>a%^HLGMb?sCf;T-^GlCUQWPIY<FQ8Yh+&*#$H%uSZ{j++"
    "HXoI{qZ&6--Dk9j7r*0;(~4X`8M|FmgxOxyE-(BrP)o$aMsrn0pA-bn64Q84&r4Z8Uq~M=-aYyhPO+2b{pEb"
    "rXx_a*KTUT&!we0$!WdmbM!pPLh%8$Uhz3fI5F6(6<+We8K*AnLl4beT6;~rO6;`bgo5ZO(6QMuR^aJEOezh"
    "3$nLp9CrrfHeua_Im`s*<ni{`NL=k*)U6P^c_D4;`oF`5T$cfU$r&k-duDH5z%krNEKmQ1oCV9IiSPRbP%3X"
    "=Ug0VP!(rgMrFaOUa!c5j4jNoVuh1_sZL{^-7YWOR|Xe5)<AcA+nYNsBa-E|IZ@d8nCuo!BJK4&!Jj^ROSrX"
    "%PEuBWU_sisbZFn%6ahXBc5V1|@|1>7&i!qk3!oj+QE^qn1t!>b_{POz$>><gO}oztvpXq4M))WQ+zj(xz+w"
    "e6rP|;Jq#x-X&y@f5a-CxcNqr(*LSGC0gnqm8!7Ne{9^yioZ&ZfVJ3EpFuk14y#&382#aks`4J4I$*5X?I36"
    "nvsp-t^+pH&0*t5;d1T!}1nbq8aIr6nb&(lO()kA}ieIC1K&%{?m6p3Q7LR~|<PEt%k@MKmxx-zqDYK~rIL?"
    "SF;r&r1;F;si@*Rp9S)=R=&Vv`A8C*3=o>?I^29L^=8_v{Q0*fjvF$$R@nj6(+&-CX8*=ag+8U~?xbpn!^Te"
    "p`B1)H<s2|pXTjw$YNr#`S|&Ec8JF!4K;X5mUKTasdD&li;kvC=FxYo}fk^BIT>MEF}$eG<hzz4Dkcva)nOx"
    "bho~lCTS4-qsq4_)+^lRdEHPZG;#1roF05%x`nxIzvj?1!|T~iPz6DZ;%)xtbD<>0Q0L1q`H4BXDC*6tQ5Rh"
    "q8ylxE!d>%80(KD0S~>+N#`hZz^^L>A!iCxG0J?9lA&+!<e+1VOH6MYtZR0#Oa(PrXw2U|`ugoo`~Rlxe{Qy"
    "a=y$$uzkh;!0$|g?uQr<`;Lrp>!fAw%YF0~=fqg-2voxG-jhdcQ<=xD9(x`FbEXl7)GUwt%0@T4(iqSSfN8h"
    "G(Eobxo#W=kr4|dXS>-M+#9#`7ei&|-4hsvfONkpcX^`Q=2jlag0Qo8LaU>7W`zkLH(`u^Q?PZVtAfd|XM?F"
    "On2H|cHOhV?A4(Hcojmy}MlLxo<a*#hSa4`5tVM~YMe^1nS{2*R+Zx7S%WAE8e1Zi-$H7{v%v-A}ktAXN5Xr"
    "%up>-Th=Y?T){eQ0fH&37$>(jZY2?@%8D)(R@acPH0b&VZZ*Qkb*~!Gcu8PXVW(7&r39L%e9ki(B0aEsdDA0"
    "lf~>BFZ}?Q-n>fl58chpKmYmN^l)~V-MpTUKEi;PAP6kx*drV-0Ir`-uFVC|ng)v#I&596T7rSD$Do7#isTn"
    "hd~VhapxWmX1fcpA*i<(B>9z~BBVCRc7NAb>1JV`2&j#0C)jBetL1LoDaMWpT^A3>h1)Qx3YbmhN%Rf9tCDy"
    "@1&W}eNjD&xHLvXS11laK0(4|Q_g$<tv{eJOXTRTgJ<XReP9dD7T(%f3nJ4Flv3Pt&b`6}^aT&k7t2@TB|?Z"
    "}Jq(-ypCAJ&M<#g(W4ovRtyiBbITP!){JuLTreBV1touW2?RG^psFS*^2JK=%SmfH4|tQi)={Zn$jqa-wu_0"
    "ih3CNWSQ!qMZDnWOD}RWVOo2-Us3*e2Q^2J-!JMHWGGd)Xis`n-N`40~xvjk9ASsVtiNsaI1&l4y<W3)ygyY"
    "sxkH=B8x$z&^annI<>^;Yb($gv=qCI>FeniKOt!p2?~EwzUDk(-E^J#a@xR>AcS0lg`A#to3V__&!pL8hKei"
    "}QK70BWU3HYNJ+i!)6M&i&!PKz9UGWG;*8T(Ujkvm$9w0TZ{K5A)<c&%_KOR$JkH2m_AxV6pIzGL?c93%GRp"
    "4>ID;fBO|xGTQA}@u;3M|y)t>_~+pL)HX@T<Y4%u%`(0tQ6S)S7$ekBf&F3IZ+GrERJ(G=ZQ2!9l>nfbS3t#"
    "mw3rm~G~LC?T(Hd?S}QRLHBye0|52WaRJKC30pyk`NUQFk3?&f`2CytqbT5z<YZXoJ1woOB4uGr$7_T5UFLY"
    "udk76+y9&2r@c5(di~Bjn~M!GbufPzkma*kz{^MC;(t}{6Sef0ou+7W2{b?>sQUCe@Vze^l>WLV<zO*@nL!H"
    "Kg=8(@cuuusUA<d#*GM6AR7`wc_Gox6;3sAE?7&}Htw>xA8_xShsYY>j>|b$bVcK9Mfn_O_9|uzsYuE*-6uR"
    "cz*v1Ij+Ra~gQf>2#fy9o6j)<B2bg#$cnXwx+7*m!k+9V4dXxj=cS4!CpH2U<%$92WbBspDBD!lURcdY+=IX"
    "dTj$Ej=3Siax57>$E0tn#358<`Yp-ehcWXObTxj=1|f;;HeByw}#0LYi$TjjeWw}RxU;8TH#!LMbDvL6G<Yv"
    ")Mb8coFtt~0ollzF$YY@^)Hh<Y`eSiEuTS^t~wzb!n;-=*q~-)$D|%IBr{V__D4@nP7oX5kU1{gG?}nG=drH"
    "d%;2VycOEo07_`aw1@Nv~sVIuZ$P$hqr_kPOmADU;y8(sb(p}yWs9JF0pQM&wd(CED-O6lq!?_wyM4v`tj|m"
    "63O}y@_#|4LWwWu8OfuodPGiP<um3eRz9Wasg)zm##!Y9Va}rWEXks__6o1gB<MQP|0cJ%#hH-dX|5rnY9gT"
    "qg3mJwqe6R`)jC9f2$jDA@gX_E1(n~U()Rm^&a1#9NWNiAm1$zn%z1_@4m2K-!BC=dzE3THnqgyMfn$fGB9W"
    "oMmrP6%S<I(HL#nQUJv1iiAM{6ei(Im!K-&9SoE$;rxUbm@5?<vB1?H;I04$r)#dRV<O1}O&`Tp6rCeUTYG1"
    "X}M<7EHmLrftED<xu{n^(lbt(e%PqifKOYh1XkDm6BsF1gS$A1(7{SO%8z?j#tEzbn<6;p0L|V)Jo5;|!^Ve"
    "yk~Rd@2dlpKC>=WjI5>ZD`o0sv;7S3;Od+!yc+;p(C!BO{+28LgS&6d;(yR2EsoA#Q;X(^tWc)&3Bt*l2Ne0"
    "V^24o4#YALyDCCaBIGua11jedl&N%p<RkmzDqUi!=I4$a$KCCXlx9tMZfEJZ^V+1V)!k3?La?8O<iTKXJ)A4"
    "$U-iymaQZlq)O`+%6h>3QTM~R5NmcO@J6f{GEv5fN{{4>xyr30k5jKleQ;Yv;2K|2hkcF}mpt3gqqRzv=D(e"
    "nAMBD^d6dr|kO#+?JNn=@!hv%j%F`U#wy;CfUP7TPo<`eqvP{)0)9azmFBHBQWLWt=sW`J7r*-a<*F$_ivzT"
    "=+r5Js|{!7^!c{oXdg=7w<LEhb)dVb272B5oBUp2M>0yn^k|D{{+J9zE(xrMmjZlNXA?c~}2<@}j&|P?Sf6^"
    "?d_|;1g6+orM`nX?a+;N4@C?=qZnp4!rkN6(1K=#^k>_YP{>>&4VkDfmXLpWQDew@Ig|<k_RRTZsa^6>5U&?"
    "|G5OCc<!7A%o-uupU)8Q-R)=v&=2EJiwd)&SQ>f0pjZ|g@EUnPri02rF?E-lA!tHai9Q_cqNym?b&!oj1Zmm"
    "mrM6YKhYJ1lM$C5n_2RA9Rm8hQna_gap5}wms8Qp=Az<C2>_Mas9%wep`%2Z)zq#)v+mopirqfaLdX|qUqVQ"
    "Az;G}SS`nmDqO3~(Z+kUS_c*u2zg<5@!Ran}U41}LYjN*aWJqlcWbGmCjnPVttjv6Rs7-)7Rx=@fHda)uYh4"
    "hYRm)M77J_-AfEN-u}LY3O4b`=>-X^#q3Z2yvM#mz(pRx7Z8A5XCQEfOr&C3W{X*cY(Gn9&Qy8J}ceyi2irm"
    "O~q;v@FvFoi|+yJEG9Vf|W{B)wn<{#>Ti+^3{qEEjnK$Q);J(lC#gV{MGC_{$I0mW67}P*sL~Rgm#>^w+dA5"
    "0Xx1F(xfSuw5o}fqlT<B=tPR=D=BfZ{k@E#=NM=q(Vym#3u@)-#N~yu*+X=2z?BzeKGco^wJ1EMEv+ye$+(V"
    "4kx@lwMT>}n`K>SqOFm<^xn^9L0IH^xy|VRFoM2+~QNrFcpe}<Cx$%c!(Wiw`PJljgzvdA(rGW<vi5?!cTob"
    "z+57Wep@SeiGrF7qBz0Mb`nrmwk|2p<5S=F`9BOS}>2M`{ohTnQj7$FyI)8kgTxQ=<AqsekY{1VFtZ*I~yV)"
    "H5tpwif>DYfjWA=7$VS<!2O#FMz3d^con_~#b3^ppGeC)UHN8382_!NAGfrWI=4<!<u!{l9NFELKzAzV|Y<K"
    "eKt2L#Iu#Nm59a82zOiQ(=#e_j<>eu5D-*0QX@3)&6M`(PB}P(f#sB2(LFCk6rHR<n7@40w@&wTNkWuC5qfi"
    "h0aXi-6H_YHsuj*jD{QU@8oY??8f^)&F`W;_cVRJ!o}l1R_5g?w;K8Hm%4!b$11!)7QF&fX&5R}lAR$rlc60"
    "own<`%p&4m$37Akx2*1|>C~Rj58`QBwP&-SwL=hu2Jb6j(n)TBsq7SYj@;U=IuY#$(GmBQqEFzbYD2%4dpc$"
    "}Grw#+8ylZ>@VFXVMDf0rzDo}HvedKv*3se+=(SwwHt)L2I0KbEn*ZQJc94C2_H1xwylC36?n9^Y%n8oTWx-"
    "VL0BMR)+5GWThnx$gjiq=!n_ETXCD#T48LBlAOh$3stDbL_{%2S1ribx2o@8S(Tg+~a+Sf)?;s};6B6C$&o6"
    ">qT^>+Npx!=}}jxnARJI=+p@ZV2-$f1o0`BakTrb)2GyWUikjnQ+8cX>djS4#30Q*#xy4exrQy&9hbVi7I=v"
    "Pas<XUqn6ovzl}|&f)s4yeSE>zQj_ai=w>t)>c9(5p4X1_UpEQyy?UPI&QSIQU`HLtnG~#-Hi=&E#F{?rWeh"
    "UiW@hbppgGx<o$?#_X0={4X7T`t!CMy^em5WQYFdF+QbnW&Q(pI<cB36^Dj7IcrZGNEpK4oha0Pe)@(LctVq"
    "kEm1+8tAUV^}8Lc(dMc9@AcIM4b3z)P_Q4^h&Q<g0<!Lk{#D~oJuGAI1IqYjrF{i|$p{B&#&_?GO$k5RlalC"
    "i;rWUqI!+k&6s21QJ~G2-%8QCyB#oQuw~N?+y5n{lzyCCjat-P@t-wFh1G*7~DHREWyvt#!za(|ACI9JdcTi"
    "aA@K=Q%W)*CA%LoK)-=l7IceBwxSq1)2a=?5omtg*17XEN~uQ;%Tk!vKh+Q6hBQI$;j9$pagP@-!k6m7GI2J"
    "+I1umUq|85Vs}b)scId{0Z!o7AxIUZQDIZW152k;7APlrRv|{tvAmSFk&g!KlF@6M;Z<&*2~BEi3Om&@!hNN"
    "J;-N%`%A!2vMeBxWq<J5$OMyM)>HAm}Bmrh$%SBM73H@5LDtq0{lkuwm9G!#;Y-uZJQ;bm3<^jmdsgW5l>W("
    "7hEvYH`P6d9R^B^KJ`S-m=OXii2yx#M4knO|n+hwkZNYiz!buh`)oJFA`WJn(-=eJsX#0aW2#J6(iffJ{OWR"
    "F=d(?$B*C77l0YXR#vOq*-0@-de29Ldm+%3#V82Db$zND#QAVJmVqMrY_oDP<}$J9<7ILPNJAq5;1W4MgCSm"
    "@pb47MN$_>7tCZ3`-=xk@XmcIpIpayap*T8~RQ`vjTR@+Zggtjln(+>u3YRj_Eyd-Lc)X!jMg;sYFav{m-NQ"
    "LQVQ>toeG4YQwN&n}sm44vp*^VbzK!wWJrfd4=|$*K1@v<Hez10{SJ=cmDyi<cPLavU3&~?!NI76K6b!q0P="
    "IQ9bY`czjFRzitN!*CE?lN3Shqqx|WI@Zs4ex~3wsb7W;rL9Ai3e9H@mp3=ZN!{y{UZ^&q^Bpr`uH~nck?Q)"
    "uWiL;GsWXEhdKIEASnus2Zu#_Ja?w(>$1LnlDu4c17u(CF1eTYiQKa5scJ0X36SU63`?BL5ep|SbkC_(FOKC"
    "JluLZVh3QJv}}1r~!9@_VE%6^F#e^dt(BE#7F<koF?B<|j!5E8{-fY$Z>V$B(H@ZUIl9HJc6w5Ro=pE|Hhb$"
    "duwdv5pQB)~PInvj*x3pN5E?)lpW=F?91#wWD^ZyaXV)iyuO!hxhSzA8Cyq&Y^v-q?IYJ)UT2vgQ=~9N)$=L"
    ";>qH2Z(p}`zFmi#ntJZ}aw45`o2|{Vdc0);uZB0eRqi)-UcWv*`g?D0qcU=#jA?qMj_-4<P5)dj@a6Wr?fO6"
    "4FT#p#(!??zN_3yeL~D(elviWZnSowQIuyrDQd)lP??-6;3k$FXrRQJN-v?*0SLyU}buvv|%ZSsc!3Z7ziL#"
    "P)#T5%_-q>}|78;rWz{BUo!<2J5P_?(4(pe*}^}11t(*Ziys2*M$$&0ZdUtx_?md7xQ_$vLFB})G&W0=}WCW"
    "|!xklb8hRS~M43V#h{eF*8i<BmwdHxyaJ&uQq*Ji}5Ow$LknbtAW3u#)p-4gzSNYleOi8J>J5Hq_Yqy8F`QW"
    "+0rgWQJuU{QCA~Uu}pf2@K1KarlsLvHGA5msEK$>O?oFVNhyE=fP^?-sd47DkZ$J+ZEo@xCzlJ51tXxe*LcL"
    "6+}j=+qXRfSIfHEO^_)yhxV=~<}x=u&ZxwhX-<fm&@9KmG+Z79;NoeJUU3^anLwxk@pzUmIxygZOC5ilVL_W"
    "gdL0em^`{#~IQe&zza*P0Q>3Sak8Uh3LC*|TbR<4hxK^#W;Q^LtF3zDcJM;^R|A2{?6ev_*0t!=;qK(6=tyr"
    "I95zr2<U733{+1gn83WW-4T3Xh%wp2%!xm2<!VmPZ0gCJu7hzDu969$ktT}BZcKXyxQa(m4}Jc<}ggX8xnZ<"
    "JWu(z1cfR>hEoT}r{Xesn+OHA4+Q(JU>eUuoE3sz8PYq{%k3wNTCVzQH-}t|Jq7z}|KKezLVv>?}PZ_YTzlt"
    "W<J2Z*J;#Fp+g579QUxgS>1SWroD4r>%HUB$&`Nvn?PT$7HUD%rdBHXzLBytZSAepwvU$&r9emMb(Ic5raZE"
    "cJaxJWQ}xBAB3j#MOk|1XWO#YUq+mhh4YqUTVlZ!Q1r>(7dF0dQoV|WdOoLJQdM}h_@-f?Hz(LNuD54vKv9H"
    "s?PgOVi`OW;P?4PP1Vl@DU}<T<6-QXKfA=Vily1gWbo%D_uy0<`)Lzng*I1Sb*eMJCiD^MM=qjNID-#qHc<V"
    "GY%LPiLibUX_Dg_T)rzM<-ZPF4^^zPA}3oV{@6ka>O?(Cn!>;2wur@iCDodZXBFMNt@F8m?2#N6Xc{Hpzud1"
    "8O>pjXvePl|wJFQj6XyX7=pETrEe3Bjg&2>GP1K>k~tXP8nm9VXZ{Jsr1)^AYMfua_YFe_n+<dSx&Jt&cmwb"
    "kg&IzPF22BB?oS-70pN%|^~=d!K%D{Y4<vi}XuZwHpo1?55cbdW4eYV$dfI>D~0z&TsvbQ=qc_pMF0DxuI(^"
    "{dP^okgi$y+qb?qjACeh#dPAmY%mgW{@wI-dW$tDy%*^nOuK23n)bd{Nj-1qZIdROap*1oHjX-57Z1sE=(wx"
    "(y&Z#?$Lx1<+eABGm@lV&De)KT=iF`ywDGZDm(LjBDVVNrk3e~FvwcQC76dt0r3PQ~9=NY@h8)g4U2I#_jKx"
    "P!(m(oAdpp+zs&86RCtF$4t~&%?Tjf}j6kI&i-m6;EUDI|8el{|SvQxrK$*kA;&hw)hfR`jfM$!%`OrK%eQl"
    "PiI6;$UyCicJ0I&L-(DPqx+;S3|niHiuhRYDIM&1Pqm&#;0xmWz(Osq2fi->?g=_MRDY8GL?NRmY<g{Y@>S?"
    "ZgnN5bIxiGxf3pN)exsyMzQt#K5pm83PixVBqG44%HS-RE@GoXGB#PhQ%y@x10BjcKIc{<#Xl@7nGS{C5cn%"
    "{NM{=>mg*|)b8z{U@P7|YZ+T+3?T(_2YHf3Dklqv(a+|zj4nJN|3${CHIKui)BfI@o|(oq7TKAh<Cg;#5Eb%"
    "<s&#@geR12rH!T_mPIW7OrlBKgq#dQi4|QA)gwPjB)TADG^F{wdcB}QtMShvh^KJu=IEh_Y+Rm;Vv+iYVFYP"
    "{H&($>4*7%}{P*`9F1bOQjF!bd7c9Ge{QQ89DDc-UtRw8K#>F82Xj?z>sAAbxGh(Cwz4(oRcTEipfD~ZlAA}"
    "5T$&3K|bVvQG)SPv)biJ?bKN~wJ<Zt;=rYbj_wQW}u$Bzg{7tFx-BjzItA{&A11UMUc@!q(2Nb4FQsK`KV#A"
    "V)}=yOCa<>+D{=J&QA41VtX-5@Nmq3>k4vq*lvBMo7K_+-#QYaE$$0&r^&OmvCbX&ywWSRqWc@wtQqLdDNUT"
    "U35v`Cre0IaP$iM<UOpZ!5IvX+x-sKgPkWYSlYBnMSRYJxM?^-sDbbQ?M;trTZ4#+GO%`YrOu34+|;d@z50k"
    "A_g)|D{LVpVtRi&ZJ;LnNe2nfl379c?3-Ok${`nMnry)34z>hW7yh@y|D^izW1RZWCSOWHY<K@mi#Y*s83Md"
    "js2MhR?9K97d{27zx35#6YA4vR>|NBX@)hZz~B2A$lY=U44FQXOPQ+VQIQ7p_R$H3^gHVCE)V1W!-4y<y_<&"
    "8qTRYbG9@SxgQEwnj#v%A~t?O{kzL132o#T^~@oI`~`5u(Os^?q0(!I#8K3m``J!mQqIN3+z@MjbzL*UEN!l"
    "}T^vd3HI<k(?kgqIgy;)jUY3>Lx9l_LLqb!yIhvO*YS|Yu=6wGQ!5=`2>UhUf(W2CrK`rQ|<vn!8u6Na&2q5"
    "NNpci?kdG2zQbba=DSIHj)6SVbZ9*6B)hbV1pCE~XBb_UEUz(lBgLW4O)VuU6*PlkVMI{QX4nWi1A>aj>haC"
    "hXmIt|S)S<@N3)<^;j((vK8<9j%WQ$olTl+Gz(;sZW0?M&pm2IKlcs#wkDXf%QvWrYm0KQdl3tDm>3AF8+QO"
    "dC27K5rg-d+niZ3X3egQ&Fis2i1CpqITd{{3xMZ0w$!1FQd&oi>n_OEBana&7l7}n<TPO^WIaOKotGD!0)YN"
    "X9gv$*#)u00u#Ktx<V-Q4<?md`63QNLn%oCePRz*%9bg293pIhj!nE35#H;Z}=mYWwN{WS-g;G9u?@ao88z$"
    "S28T_~c`l#Bg+prCw(or@{y#Q|~0FG7WiXjC+y}kd={34K@s8R%qe|X%d_XAQ*-+(^Z*GI^~UnjiDtDgZ`Ab"
    "n?PSLM}Uy{3@$_u3QkXUOK=<(1IU{Lo-xh<G_!P$`S;l7l>nbjsf~9=H4fncIA%-gV*Kx5rN*jR*?9Qn8>`>"
    "}9at+kZDe1BmwL@raQi%qj3sA$ex)j52{CIiF{5C^<u%R%mr4lf_zPG8g)jB}1}@71wnK8Q&WgdInHj|c1Zh"
    "JW1NQL~*gg>-YdZGnJ_DiHyrs-|Ob~eKTjL$~BU#oRD7|<3tyl^Ia&qXm{IIk>OS={zD)0Sj6l+?yfUyDH8@"
    "5brGXCX|EH-|bnW>ZU!_u&F`1?K<uP{kE)(}c2N3ndy#$hhL_uD$@0{o}#)xzV>D#LfYTjs?(XRnY@_XpUB$"
    "lEB|o{{NMx8`Q-9_<|TPIh~ZlQ*v<`kTK2GW2FM**Ss3vq;ChCo}`NIUi+48!v8vR%kYhqY>DeW)>p{oev9p"
    "JG|r7Dm_Pm3tc>f%m8}7?d+Z&{GQw}#UJHD+;yyu9_5`Rzrq&9hP`~GZf}Be?d$O}Z{up)yn2x>P*j;MFRzF"
    "lB8LMqEYmn6*qHvr`58TPhQX8>hBHqnJ@q5~KUH%)V<s>H(Gh6i5<VhLrV!DX+`x$B1ZT<RTEqH*CoZvEEeA"
    "n5<MRl{#3MkMseZ^3Uy`Rc5=u=B)dK_2pIZ#PCZP$d<hI-FO9dccz$g=IHK<elSAfC=VEk1lInI!HV*L3ud3"
    "~IG_4Hc<Zr&aZy{3t5<e2}OI0!(J5{m;e9jc<B>yY;p#{hOe{SN4RcyfCDX7_ae=x`h50%F|g@*T2In1frhA"
    "%RQ3Nu_@Ys-uO%nvzt8^U=iu?;}Ic7uhxQ25%6%C|5w>V00|*f#rmGAMh|?;!K)ck1+=KO!NnXXJ@ik(umoL"
    "C>pZvY`Tovak1VzZ$9g6e8NI%e4voj=-;T2>S@61`nMadTtlp^Vijc!`PZZ4gT3S>oX~9%A?MV$6>uK_m`&+"
    "qalF6DI7{ZE%c})?RbD9AUy1yioC#URQeZ-I&st=0);njN<m5V?&k=w$ZA4B|AQ+>ZbCDp>GCHwlD26B{B8U"
    "QzAwE(|voT-armYgj&mZl6FZHc?9QeuSEE`|ovbpsW%hM`*A}P6?XW5j(tx;YS%^6#R=FXge7!T81!CZO`H4"
    "eZvIj4A$<abJ>IL}DWAwk|^7=|eGfTF^V(<v#QB!pr!A%+hxb}?IGeMu&!*w!_IfQnlQx3pb}JWe1ImNpD!5"
    "JIO_%)CO%!X929mRwkDc~`8~VbL=zkg8|Izw8$A3O^rQu3~GJqlJc+i+7I>XO6&wD@LvF6VAWmnF_Skk2xP2"
    "=V(O~QyI^ZLww0Jgi$Mb{CJM_EZ;qH3O#JwuiSZrCJw*|@a!y2IA$p4w2C|GTv{KT7tRv8pX>sXhMrC?dnvy"
    "*-rqUYL+<HMxaoTdVDOK*FRPkYoNMr&*)uP{(i0Fqmx2yw!Yi+rbKoL*#_|G6XIQ%fL^8S?5fBU|J;gIkW*R"
    ">^jEQKPP&bw7;5GpwwCE&fC?a+`ohEMQ=9!^1*Vm)*t(6Io-RYFX(8Eb;N&5%*hcG)I{XtE9bJFXxw3GZ5nE"
    "_9jpLS#*RM=_yWR}VPLBbLm9)NAM8~*@u`j}e+V{m8F7)*fpaYCG8uLFsep}+z#G59P-87bv7@f__T7yx)lU"
    "9BUOPeitE^44NW!L6*ytXHGaiKnY)do=N&96&|#xO|=!qz@oUq7BqrXU6~mYr{zyuRQxlq|BWYg7`jM9Sbx#"
    "XZ~w6)tlHUkmQof3{8+kRGJvn34gu!+`#;T+vprQA!)&Rl!^xcaOhPbbXirB?d0wI!d<I3;RC)J<<gFIScQy"
    "gk8{DG8{-<zifb^A*f-oEnuV1f&Vut!mN$7lNiVUx*CNVLuIDo#lM~noQv}<o9Br8`-3=oBoChNqvK?j<tcC"
    "8bM%ohEP}D_>#(w(tTY+GqWbHjFtSNxBV(kTwE#%`9e{VxRhinB+q1>%ImWUFR#LfP=)=qJ4YLKM!{|DA}dX"
    "E)o-K&P!DO#J53u3z@QcD^dlOPw2J{=N}MxtT(j{mgLqXi0|90+eG5uj7=>uc!)xoy_j;?~<sGz)CYgzx;Vk"
    "X8JtYhHSQ9r+}mYFUVX(!cJCZ8H%7Lf9-Dpp{YUPnYn8_a9)gNHi@!3Rt<BYz_KZLOVUW8Iiu~QO-KDVKuds"
    "wj%@|SCk9LWNi{zAdc@IJ%|5w{tJY&hJJ{WL-hxHbYM?DQO{zPEAOlzgOF<6em%mNP4l&wlvi%>`D}p?$Xgo"
    "FccVQ65?Xmj5r(t%UU;?w&i(lRfVfgiLLoVqvq;~n*5qW52uZJyO}<L@xswX)EQ`JWg_2;(#+&VAaWm6t8%q"
    "$0h3wWn$BrJ_epg47F1+lOq(iJPIjGx-sAQ`TEXRDo4a8GjypQTUTY8zSabeRibkAFugk-D9{(Jj?q2*0!)M"
    "sxIZ$c|^vsvs^B)gz<EEZ;~M>ooklSe|(`x1pmO{H?hhsspVPu@1%#gwf^-n6=WNHC6jKkuKM9{=u=Z*k^0B"
    ")q0gWxI~uuBAg3=;n5)pqfXkK(k#z@L&LPUwmb}^uG5#`IxIs+TH<@j1IL<^3x2C+XVA{04R9Qu$C?x?Y`oC"
    "1tuZrPF-Z<adJCb(g>!Chx+-^);M3H;fly<AIWKd_piO(UofeKU5YtiwC+X_iB3}th<D(saN9Rl((@iuOYuf"
    "h_`#3|>m+Za!wrhi7(Rn!O~8XeHp%Y6(MfO5dN8Jm_QbIP1EjXI5-x23Q>w1NjrL=O2kEvZ_#x%tOo+vFc0R"
    "*cGc44^-qR~~bbxxCO{q`>`B6eu_yYZp3PPd~3M6aFgJ(+Jat~sb`{Y!!-PUcnE9glDWev{q8xNQppY*GD8+"
    "L1CJ212d3qa)5o~fuz`GI({zKbcFHhE4fqwkQBOlSW{x09a^dYhYDNt;{%9%8W7g6*`_`{&;crn?eZF+xYtC"
    "$1Ahkzt*FAHya3{kv@te(};>2*|RqrST|?S;`l~@#wrw^a14uK>apWk`&>Z=-z!Z|I+#8bvj26nq1(2!S_0o"
    "Y>{GQg1L1)P8S%4YA)ord38L-3HC82hZ;R~oi46mWW9@Zf6L-5^qGDiE>q@lzbwK6p=;thj<btp4q8|ISxON"
    "%&mJ+oXeGz9aasJvY<`(eNB?C1oxbN>D|t=J&6satw&?y|@A#zT1**0Bag<{#NPYuIGoBWt(DtSm*?>+<5P="
    "m!jUk5WjDVGtBx6U9ZE?RlvGM%#9C_(=I`{xfIh-wCVqc6xIcCj|<)S$<bvHY(KcCGO4LmjZb&3Un6g4}CdX"
    "3hDShMZPR#ZRQyx75Uuu?QxcN?Bheue=ljehCaHp<|dBKrEX4?y$*%@rm9^@|zxxc{b=Y<;W7rQ2bO{$$+=c"
    "KU?d1Dc0CXOngGMfy%*m_K!60AqC<MODy36pfM{IyJmPCm9GI145NZh~hTVJ3Yr8S)@)71iVihN55>4=4jSW"
    "s^i9CueW!SeAC(b_Q}Rwe0-if(7SLQ-mrGTJn*ailM_rm2nWS653>cAjFN`GK`kQt;OXoGh&bEH$_HQTx!kt"
    ")1?>HjA{o#_i*mg=ubt5X6lgD=caUDAj;W91VLvYv1BPd8Cz8NeqEWQ2Gbi~(uPDesou3zal)7UNv1Zf|&}*"
    "Khc_A6ae&q>$=6RyeZ_9^*_wQVFG#l6ZinEUOhR@3&^6rt?6cg6F*;D7*5f}5+vB$a)0dQsM1m4{ao1MWsYL"
    "~)tqVia14x>S^GTtPs9)X{UzD~vZkeu}MY#dD!3dS-ow9N}E1}2|*-9hQ$=zuv$5$Cf%R=|oM@&@3_{JiT)<"
    "I_ef*<i~Pz1zHNavm1%lw@JKTj<aXphbA{w!a4oK^SoNiATS43yxb-L=AK;1=$V<#bR)nN1_h0*~JCPNmyiT"
    "G+2(8lTLDgVc3>EqX}b1qG>wr_=zXXTsA!)kC{v4+lR2^Z6(zj5{?v;f{!sK7Fqh4;r#8?A=zj4<H7Ophle-"
    "i1K~InGLfTCGfTAY|1iUiBo`;>CD-WqB~j52WZUwjicuXVY#Aj8NPr8jNYtS*0(RaEImSLbG)l*#f1>0JgAm"
    ")k3#Yc}OpT&RsmsJ?POxll7hK_&x^d%c9r^(@88c0N7GRd~iJs|z8ujkoLVjS$Hs_}zTjk<JckNHJn=iCF)s"
    "DNgG^xcP7v26AMvhvH7GvOw_QEjBN0cjIFR{YtUeS&==7Q>0Q_mZR;FFJcj0PQn3&<+dF9i_Z;n7FT?Q|9(J"
    "2CPWN?WNx%;e^Cpa>VD5R4C%4`$b*ba+zhIBOQZ=s}H62@*K^ApFlljsfajiU1SH!WV+2HM0t2_=2-Om|F~_"
    "?giZIsp*he7?QFZ&BcZjw-A7Vj-`7S*o*U<IZf4J<b12OK*e9K29?xf;{G);ENPZc38+4L@z$D?wCcVBbR}+"
    "hEj4)4v81D<6lMwn@060|7qcW?4o6fDb!T_C_xiNA$2pnSD2MkYTvG{3enoLIj^s_BJCpuMXUX|!nqmsc9E&"
    "j}Cx1Jzc`XS%4+Lb9&e4}Y9y)0xFvcxSEW-*^!cHl3%CsN=8A765P*wh*fiT=M-Xv-a#v=+9!11sKGfou42P"
    "L_RdX-;glCOkaJ6!Fa^k$qG-dfC;m`K54N$4lUs;!tGM9DjF{d_k2@En5_DS0YoGj3a|BC%(j%r_D9V*Rsbo"
    "l|l!JcpI9@feG_r|yXFqGok8jGtRKrNM^cpr5DMut<VoyGg;XcJxaj3zRGE6jK$Fc1cnKD(Drd2Z6}TBI?1>"
    "ubxM)Ab^FoKM-Dd6+m4mMh=#WZKspcK)i5W7k1Xg$h?|ic#%LC-g$I(*vbYJ<lj|cb_EXT&Qsw5C$J(Cmtyv"
    "r+9Ud50sPS?^};k9t>BYBzu`W<@xHnJBPa@q)8ad3hxkOF<wv{8c{)z1*ku46bt2yPP@rd~mFyn9IXrDVrYw"
    "@F=K}uu_~^}RgbTTF43zL!>^MYMKcyvqW0s6B7Z(jDg6VMW)#w`BU?XP?HwM{=jAANf18Scd!Jy!SzV(V|8h"
    "2SL>@oMXzmYrJUnFx@^5)SL6w<ZWAc8|`0w73M@aSNCmQs*6N2Pxmmt_q7p-VKs#idZStof2ELvya}TFc`%S"
    "MrVyrguiARGTO0iuznkp;BH;udji%f;=;e2=_d#N^unQ*U`o87m`T1#X&ACl0RkCopq#rI!!bfMP2Z)QDl&="
    "3dXUPeA;-ub8@o5u~u|X(kaFEiEhsgWFLH!(;tgyLeXO5aU&QbI<Y1Xz2)i6XtV!9VE!sOoF(nHNpoelEL;I"
    "$6K%}dyp!zMgk?@$LO}@xDU-j%aXi~PVwzwPUrrxiP|hl%8Cf^bNeTM&>_WZ4=b7;q8n3OBAT7#B0D&62Zg$"
    "lO!k_H0&ii*h)y*hUW<Z3-d0xTOhX?XF-8T^YWCp3$QH)RM9y-D4RoE{DGXSqK>;@#}yk)w{O#mT*9<mky*R"
    "Rs~u>FDCu5b%rqZ*vG+b~{smQdM>G(juwILt|g|FIb_`vbSL-PRnvYfR(e_HBxSB<SahWSL_vfL|qJ3{#az*"
    "2W2A%0H*q&*s_X934-sBp+wlwF${N&lWf6*T*lz0?;r<O`3pNv06g)z2-}HPd9cK^KpAO`8qk-|9SuL6iYsR"
    "$W0a<Xh=CWUx9fK(j_Kt4FF=;1DTL<oLx{z@?egkj}%XpV&j@YcAjDc1RRyC(Ga#-dnsg-nI5ohUKKmLFVKM"
    "7k{?JG0Ks!UF9<f(e_A$|k{=b@Ae|LV$4W6yA~`xqP^=sQA|`vd4^vQC%;AHHw{NpW`+PYX%QDa8@w24CUSt"
    "@eJ%%rg^$TCKD*N?vDi;v4BkVJSDt0z(+L_UZ&aSaMEsXbO3fj>RlBZ~@+rp71OH9_j!D14V4ATZj`J|ONW9"
    "oj6LA1em8A(<nznIp?g{i{c<e63@oelD@nG@w-Kiz!#tiAbt`{@sDj4%G7O>=6G^0v;Sjia>f$?8mCA?>!Nm"
    "W^`N-&6;5y|x7LmS(AOx+G6g3W0EmUNIq2?OsH3tQm(lY2lZgetCc0PzZ(ZG;YBAsKO1hu0sN`i-~J!!^z!)"
    "l<<abCpjk2qPv+_h8gwV$v5l6TV}tx>bOl>9x8eo6cGHet2t{$c7C+5`HPxZ!|gZVP6P0Pw(Alp))cQYPBc4"
    "~YRQgLkOk8t+;AQX(Ivt2fpun!g%&6ti86VIQpcHrkc;6TX`MkMV2((+s6ssaon!Lha;!g{qZ)}o!j&5C(02"
    "_L==}l`*r8qQ6PPtd1F!cH`gGYDsSvY(?>f;3j1v7B#c!;Sh%`($7>H3Zn3Kam(b>w<48G33*X@<6_$Pd>!$"
    "4=ji!Tt3x(n6rCkb)fe0I~7=g2g9=U5!&h8H|~$9^s64eQ-%M!(SDQADh3I`8wP==-7kL9p9SC=yekB1Qh1c"
    "UtbR<=rNr!A*t-#%E^e!ARZC3lV|B6c@h-5jbX5a>lgI9D^}dCPz^fhXo#v+2eS~Uh|rG_9(~sWMGf$hiprB"
    "IGs3C^_&1hTyQj`<IB5zw#}a=j+Whk+@S2jdk=48S`3I4fczMgss(^{4)*`vBc6?k>@@5+Yf}-Ov&1hbd~&*"
    "T(1Ve0XH4rGR9=ZA2Xg@Xm>Vi^Y0z|W)oj7a`#<$|PEXL%h#`ntp@RZR-DQYiw8?}BBodkz7f1kr%_w~G1|x"
    "EZvr7tMT;@*hGm#psvjvnCB(%l&wv3L1r{C6=7Ybl5^tHGotN0dC)~5=i3)c_ArNtf3vX(guKdn?F)efy%i?"
    "!>GrgsY#2p*+_zTieP;^MXKQag$j)U|<NuT4|8EJATAcnA)e<!m|k7%g82k2OJBQ$gW)%dnLqzu}4beU9joC"
    "1uP^O@|**Eg4!ao7;*EHVg&>V>kk*vnCtT5A=s1;kqnEZ@ioOwgP*nh&tr}!O_<<1+AWXIOBXYS&oTzP9r$H"
    "fKO%%4%DLe0b3-Vh#x?MncOx5J&JhukMOvk(Z^{VkQeAx^A<@cjx@}g4_rgxBpSIO2#ek(;lpOIYVSP0VGpc"
    "Tfw}r8-i<6kZH4yX(pZXO*a68_ecHQugZ9j9<<9(ai7S3hH?=DP7j@~DJ=REvcreG;(w5tOtAqDac^oF*ZX+"
    "zXFe&k!?z=}A^_<ZAurN0Ql&PxgPvJ>dOvMG&>=FhH0yn(4;9<r(Fg8|s_vip!VF~*0)IO^vFIbXA&aZZZHm"
    "aD?H^dLx<`$KC_bspgeapAj(JYHVkw7#A1edgg`8e0)&n}R%|BX3km(4u+<OJ(lLY6Pj`5P27XTN5zH(=EWb"
    "y2RUxTA#dX(cqH&Ml}|s(qJ+x(*@z?vVyUwu;NwjpYz?H%^FLj}&}1{Wt<%%Xx?%xOm)7o?+WGLYKUO{+)3)"
    "?@D~BnJ&h`)S4_lSUpvelq}EgEM}9j$?zY~u#yoQ(SqsX$R(4-TV|?hHDDj5E1@Y4Y97h@BG`Nm!{P}c(8c$"
    "jpR2$CY63aRIfvMc>dzAI$0q5$UIGpqU1We_-5+IOktZqv1D`_NDtKwshRCo{2S^+``s@n$h&o`0D}o4Q;|d"
    "7L03kIXuZ)>^$wTe7#0UAL6itmXn+>marR18R^4wWHHb0F+PvLqF13z}Z^R{LV+51)Bq3|Vt1<2tBqw93szF"
    "GqGSI^aClenXt{PL!K+S@6-9mhr|9L%62hR0OkBHpe<M2&TFV>c+CVu&#nC+Pof+AoF6vL^4!$6)ms-sG=+h"
    "h;mawescjTh{B)W=mDpRMlQFJjO}+qjOw~8}%N2(U36v<|GAzFmDe)LeDe*_4u~nEwdjO%~`%3)L5WuH)z3Z"
    "E}UZDcmhZ2h3~@{;X2szQ1wJ~r3#~Pt<m=-4yz8V@clTb;EsWmQS8cq#Sc`%EBk|M%(<8gIGac(lcxKn8n`P"
    "D#^=sA9X?L1t#3rVIvkx|sa#QhMLv3=S}mzlY>Om1EF<9Q?sQ7IJ3ZvA0o^#|J3#j<r;Dr+Ne5vUka9Khh>O"
    "TZY~x7b4yYGBc&cpfaL+kr;@>VmX=94!ub8`pI;5safP=u?k(rpV_^jhRSe{(Lf~8n?*BRKKEk97fgZY6Ffa"
    ";{T?S`U{ArsaWR!y)L(I{hlr9-fzw!N6~I4s!NAOW8uxnXv}$Ym7836U`9!JhqEhms$yMiijwzHy&k!n&9=P"
    "wyb|cr}Pk{J|*9`Ex}=D?`K~!#5pao|5$HfP^1iAvVxxj?jP{du|Hb-v&_O=W9SE{@_}eC_|J<^mx-Mk7!#d"
    "ry_WJC2FXP8cUF1t$QR)`5*(4bTo62crq(U&}1jV@dsD4(ICrFVikkY`-=D23giRBF(moJ+3VhrCAuoyvJBe"
    "#G3#KBlaE@%(18CC3=6TIwscn*ccAeG$OcW!fhQ*Bk=B9@sv;!0FX&}^PDc0*aj9)2Z;d-UxtdYE-d1E7&y)"
    "Qg?RgvIg@O0Uf?DFWR^M=OK=N6)N*va(SC5L-Lz>~n1eoFM2755QoiG*~_OxMj2=Bg+(y>5|AUed0+h|b~0D"
    "4<y7wXJ(D}MwNFOjj#0|pDN3!)AZS~tXJ<KRlyRnkz`mAK=?*MnDz+pQRg<!e(MC_x`oGMRB<MyWfCu}#!+`"
    "HI|J*{})^%wi+@mXV#~yKZG5&pl>6W8(5K^sDS!9?CiHF%SM&1EFi{urLu~%JswMW)TIobLx49Av|o(N_BQr"
    "4JgMb7IwKcD5OT0+zfH93P|LH@#*MbJaWKub2UQ?JHC!oy<v)a0(j2h+N2o)P#m?*eXF{YYrPIu)03Zv(f5q"
    "RP?K^5p}7~eT9>S+h?p@BF#!RgG4w)<HtYf4cpe#ZgUQxLN#KQ{rdMfRbub8C4@w(7p?NKu$-8W-(~vK=Vb{"
    "jJH_+=gL;3YlY#}9Phb22PwCl5R+SS1*`}kUD#Vf_x!xoOEY_1!vLRG;20D5+j0i(bxi`k4r(qM`c%mNt$0V"
    "PeuTdAE;$#U%j%?gLLZCnor*?8=zUrjbQ%A@>lSU9!B59GTQ`KI+qfmS<h07`w_HbqRhXsFjYH*hZ+e;Q^Uc"
    "rL9D{ed`|)2LO2bkLt>9f$&zqOVR$aY(_FSX(=G&2d4RNX#iG6mxZ&4)qU|Gj~_wO{B6h7m1d(VIO(FkD%)J"
    "jaQSqv!2`n*e5+W0u2IXv!db+Ba&P7=9q&^i4)6hBna23(_Tws>!gM}Q}~2>u#t?;U0?587e|uU9<1Hazow="
    "A$r3hjKKdtFse%UdizUdkpeF1xJojOHko|Q!9qeU~xLvOsk$qjAvDrVU(~A~h9J>warB<MGMY>mTM<JLdd1&"
    "py<Cvem<W7V&CE=>u6x)8S<$WnQmsBNj%(V(fQ!4mG=*jJfmpR)y*(OUQg?}PFd-v#$9Qw0``9NhOV)~92+v"
    "cKLND$>+jQnX+h2ugi_d0E60n$?S_Fk<@!;Uzwc7AKXklY9d+c8oqkUc@V30l$8LcgL#rFo{<ZqX@9{C4wwG"
    "}ms;uJw_*Mzlg_P6$HA8iO!?)7-k<=~s<u`lGwOTg#grV#RV>NS`TPA0buRB0f9{s&**>0KR4Z4qCy3z_vgG"
    "GRUbzI=Qf&PlJ2hh|Aui6NM*s+pDu$yA4wjM(bf)P~6=CWDMns^;CiDk#VE;gcn!T38_yLXRzK%0whzwzGX<"
    "hEke6!mo2~<IoX4Qm>lfC+CK#bTXR)TRqw%ap3mlXe%*wMYtv$}FO~fgwcMi8r+QP~q1xJ9D;Oa}p>B=MmK&"
    "CujYpRw(~Bd2>*7zcjU8MY?xhwLZ^b7uL)S&9=6mCOq1a#)Ivm&sM}1T*x;koUVq-Q1VIQq94V_)FP7)_3^5"
    "T;p1z6m>hEo>FmH1v*LY(*)6%YIeWj|l2<p{$0qP+g2@Hr9Ps4WuqgE1B9S>Wg#&u+qk^SWeN=v(^G_Itl+v"
    "o~gBk(T$x7a9}-ItQBgAuJtV6J~{)Le9*zwh;W?^nn43CK1KK0!P+p*d$^Po4r|i*M!V4e!F0Fr{nG6@_H!Y"
    "6PAoN<e0R~dsxQ7smmpWf#luFZI|Pibj?_A+gtBDMElG8&p%94YL{z92v|kyd6(10h~mBYr*t<*0k%PbUpNs"
    "UIML6w6uLFoYO&k79;|&>^d<T$NK`9reI5Z$$DLE`zDH;4bVzrQBIt2051`2H)?7!AOJ6=6lL?BF@#9trpO3"
    "S6;qa^^IOmQPg#VxE{~IxV!>dbKO-M(-7%jCV)H!#;XIW7x5k-t4l?uZb<`aJ7?Y4`{?}aN<4o$7s+aAvA`y"
    "bd#>Y{r?C8~h8l?YBPI;hPeuO`OsDQ<iayrv};!1ss};tY&Q(8AtQ{F7EsUmRzpTJ4>_pyE$Jk3NtGmRYh32"
    "Iu6)vA|bf7~!NIKaSagk#D=>baFmSDdlM!BvZ<q!huN^;XEj^1vD$IL!7BgN7peCy;_bJqc(c+^vtOtQo9qP"
    "l+;##4mP{SbmasKu7d);zG0|_iANvF$o*sQ({EsB@c%Fmtf(AmI(;}hCSX2T=jk=-B0E+k$C|X#7IeaZ-$iH"
    "bc2q5ubB>*Syep&WAe~Po@!8mp*!!D<AhB)0=5j%{<@Ry7C=+zQLmUtmVn^~#x3C?HvE~se8+^7Ye9)n*GAY"
    "!prWlDow?YV7P0Xe?G$+X!H?Z-PiE{Nij<_NmuM|_Sr-LjfIgMQCeG5Wg7HdXaFh_^jUiRg|{_ZJ^&`kD@5^"
    "3Oi(mO4T$71VvIn0Kg@LthAB3q#z{k*~qV$2?hMtwn`bqych*8Ap;DkKm_62k;FdPI<%0Z$rifDs|e=#%T=N"
    "gZ1tQNC_czf(<NKS{3f5vkZ`O!u))b1|Bd2qg#=g?R^Qj@^HJ47f=Vhk$Ya#egheR9HC!SQ;n`^c8xUT05R&"
    "NmJ@6!J#9b?*a?Iask2maC*#uQ8eR7lrjsbFS6BuQE0j43HlewV9Yn(@_M=180L}bufhu@z_#N=;r*k6+nIU"
    "^<S#G;^kc@yl*%wnFR5nWC;i5TOwKJ*6%cy>+ZL4|mW@$tA+r-oMs~i=TLp>8c^zd58Ule3hi*L}mLu#67+R"
    "by2ciptCtXd=yNAWwN6Qt)ZbO8f&#z(>qOq@F7xpV5+mLT|4X-ehD30h%%RXN@*X|lDXf-5O^Cm~eb@@R3u^"
    "s+)fpG#?RSb^L*0%SlmQ;4CCDat9msPB49hUPipr%}HbRC-dFXDqdv30m%oE9m?E6^U7c@}P#5i)O9g|{l{s"
    "eRqO@#QFD^?>zcg4IllZHeQI2<-q{(viNCa`6C1OfX8L2bSjN(`EDd`w?e8?7mI4I8a?LW#Ksa7}F|ZfSo}d"
    "52jVks1$-K*?nvv1-f*U#+iqVq9zTY=x=F{#)TYQEiiEDKfFq1=A{;b$o@HVZ>c4rPf?1kM5|<YD`-(PW1nr"
    "o)f>6hN;Zyrr^ml<C<}HOuJh%P;}%EtX4dt7J=xNkcFos{19)q&Jhyad4qG<YirDBu&l}4{F~NrzBd*n6*|t"
    "`8*UePEu*X8^otYVm@6NVaW{Y(~wxq(X`%#u#ZH-T+QPN7q#Hpy^$BUm5dyT&?Az3Ve^JqbXHXhsSm$@&A*#"
    "U<`aXH}1-1WfraR5krgJWFQG`o=^Iz|hlf;6LrZA&klj;9F<0+U>StN|SC%h~*vLV%rFFp#jcxAm`<SO(P|="
    "2`_${&p~0_@&OJxMcF{&OwXn1Y+9dhwL_|UpJUsK=GNA(dAq!f!s4@46EU;7eKbZkknOuiY%~Bi!`}1NvA0$"
    "_gA!0i&zwQrnjZWL>oPcF`bjtbZp!GYwy(#ih!^7e?Hzh-9I|)Z~btuLHbWO{c)ad-gBI-V4SUcj`K7a=jlD"
    "i`6d|Wn|qG)Z7|Na_Z;WDV4UynInJ|SoM(tW4jxd0CO#Ukk9U3sJdyL%$Mb|WpbnqEo9-U>kTsp|{B+Pu_Fq"
    "!fuikI_C#NR~f3|Orno7yq@eDX|@8{le^7?rH)z0zn$uGU%g${5YAqqsvY45jF8ujqa!2w7H)!&qa+J*^MjC"
    "~~8d2@QSe+a|8>K&fSCxIDwpGw{w?*HvgPwrA>Z|}Z_P)SSZ*gY%Ot+@(Q0H)#3tq3SdXjyOg96h@$hqg(4("
    "Z$8SEVo`B9ryNsKE$yaPQQ!fxc3tH@8NFGuCPHRqgTvVYI=SlXmAaaFEzN6!nX1YQfM#+QcbD;oUP#Dy=_2D"
    "z%7V8ZAziL&oiuQZJP1**8%M4n!0w>UEFH0Ut`WzI{s4IYU($y9Nw!c`EUz_m$K3I;>(>0Q@N!Prv?x7A=sw"
    "ja^O(x56cG~-!>^({Q+s-VK_!%pQO2cct6?ez1(?oaGGqIC*5W#rNiB0IbJ)C)wt)j^LWT<NX6ULGXN!Vd7Y"
    "uaP{mx!=U`=XM^JGDlXg4Vp?C(C>a!_`C<DsnrJT+jb1_j%G2V2lKtpkC5+W(BhOW|cEUbqEYVC1&4=osHqI"
    "|PtaYm}t*&ZmJaLs7~a>iBesa!wRrdRMC@BfTokBKS$>8#JeZttc)^^o|grhjxOkKm1;_Yb8MDXY52JNqZS#"
    "?DVi$EU4iLraLvGs&hPP;5&SohptS2+iK%-t*cM1C2OyCMGL>fQj+Ik%<xXdrDa~t%7z870VmU0|L#HvvE7g"
    "?rglAO!)&Kon?Q((F8%0J3FO3+W8Vr%24aZ|K|xzUyuz;tUBeX(kb?g2QqOELy@rIlvIU*T+s!~w4MUwcJ}s"
    "?-J^pyuMU&_6UDtD);eOvbQ^m@rRQ_3CxI0uVHho{FruR30s?%)MN-Di2?+Cm(r}Ma6z0L7<pXIrkTZ*rMwi"
    "H2&sUG6T`huBtAuW2qsAE8xuTq0J|~#$jV>`mnYwCWO<QcSHJV;87t(o)yRK*Humd_SV;|=VQ+oZB3-2zd8X"
    "b*CC3zQmk^pg>syq3NZNrr84LdN&(tL>q;@L-O2u6w1+@O|=yw`v`J>DPkIw~M0CvX37ulHMtK+zZc<8wu)j"
    "c+vEE*82yWhC+&pG2MkCNDwd`iKdzqsvQBzo@`yn!N5Ew|9>Y58?E}dvLVU%Sp=kN2Ot}v-#pyw}$mOJ`Y&v"
    "&8G~P%XCgD=W|Z(<}}#F430h!OtHNl9RpInKG@mqoh36qqSm~}`%S9fKw7YKV}luG%;WaoqW5b_ErZj9OGKH"
    "@bG-Ri*?5dy0Y+1_QSyV@WbR@%9?x#@+U`|)jrg-g%^j$t9it7FVFpy-PP#Z?swjta9|ro!Y3pd6WK-jE%F*"
    "3J0*n9$fXndUUVGD-fOZ=R7$19T)*xWHxtirf6w)!ZeB?^en7lgUNjN<2YBnB9cZi+C-=*JOC+Rt?51oG#tQ"
    "svv3$&|WP0Byd0I~y1`gQLt>Hqbwy+eJkA;f>nYl-E!)DC;Ua$}(TG7OndjAIzwcd`H5KtRA&xEJFQHt@)i&"
    "?}{(Z5_`pHLw6~!C9MJ&lc1}7lfAWWN|Z-{xmrf8)hoV=qd4=PX)Xu1r4$hu^&!S<>Y93m>L6+Oo%4}n}bkG"
    "L>S8mCRZtiSDZ`TJV5h2y+u^TXj(k0f*D#r0?XD`YA6>M7y?VCnubQe-j>N}U%<Q(-<$9Jy&<Q!Iixui3dD8"
    "tCF0lT<JozOYekW@Q$;puw}7z5>k9!WKAvE8TqbZhSQ{VY=Ge)cN=M_aVwnTnRoWn;`hci*%YaOD1brw9e4e"
    "%8UOUeg+CLNbp7{jU2pEtwLRW?JAYNcgn}C5By*OkbWt;=16|&pd7;I3dik37|?N=P<xV$F|Ft42SPHi1Mj6"
    "N_)rDz22Q}ge^LW*d>LH=Ld6m6r~;@PWt!JT3^DSOv>DtOZiPpp33KDtqkjL$+sF$Zo-E{}A<w4O+}NQ{I}?"
    "B<xx&S!8Iafewv!AeYC?<-+#+A0;89JTJ^4^Uy}6lfW<ODY`$Pf>v>4PnN{Li|!^g&}}P{2b%bN=qMp0`%ER"
    "Bb1h+``1~h)-^50<SqeU|J<~TOGrnctL_(ARy|g;3uz}<89{_r^h<KF0wA(n*ZUj<`I&UK6*(2DJL)4Sl!kP"
    "{Sah5NS~MO#U;UEQ->i^B<EP=z{%LR-2nba}fJ+Zi5|x=LWzJz{9JSNMnqDMlU=4ezc!fQBh~tQu=X7vxp%J"
    "FpNlq5?<zPYL_ds+x>7s=cca|f)#xnp%9PKC*tYo8PUR)Z$BUvvb{b@FkDbXqQwD3|6nLmUHuatdCao`7It#"
    "X^KCk=06EooCKpNyJx-RFI~t~FEJV<SY-t%=A)@TZ;A-M^w3Wt1T{<FP7>vI|y|5iyHvIs2v+tSTn77WEyHe"
    "6T1JtQqw%Gc1Y0DC=<PVymyC{7fU3zJ(N(ieGb&LME;xA|vZYaob8;Ii6$S?A7?<!r}AXC##Vvy}X=fmt~rz"
    "L83g*hU*yj>S5SJ(^(IA0k!q+1vGcH^6kDIvwZlY7tJ5aKtFTHI8FWDr>Q3(M<RjRz(yWiNehbu!V%b3*5bF"
    "J(gJ48GjN<14b(@0BVY9WhdDlli+Ty>OLZ-hO-amHa+#Qf&W=)3)4mfmQK_{<^6`)}TvIGR1H<Ht<s|DQ`wL"
    "^b$|%k12FS3kjR#zUB0i*Zj?Mc>as4<-St-T?IM1;3+bs&<rZ=IiwIk*;VVbM}Q`K_A%^a=(vm@=0Y&*2tdB"
    ")A#xQRP1HayqLHTxf*-p_wh`wYi;vE17IYj5|L#HY#0Uw#A*EvLy1S94}e=|3v(1{}bYvUYTA_i-b)<2?3Xh"
    "74qbB=$7F>@R`C11p8S0}?R?Dm1v=2okT&SQ-jP6DQh%b^x6*EM)Ka=yd@35-|oh1kTvbE7++c_u)zjPTmEg"
    "V%Nh`9N!7}Ug=@|!9T2M;$j&g!Jr~#MugBT*%MlyXJS{vGb%a%#@H-8o)4{Wa@O9T^6F@@&E_vIv@0EGF6Zg"
    ">m1+Hv`sxMWoPb6u0?^5upZ*iKypc|CNyjyD1nK#Vjv+kr%NuQ|BLYy926HUuI-HSeL9sz$PldIYzmP1(2aG"
    "^NrgJ%I9=#S3>s~f$^}EOz82sqG94LSaXw(4hQ;LynjdI@JKcS<z!Y0dK4!D(E_3W`V5o~L-8pD8iu`oMg>!"
    "71n%tV%=+8HAhhKE3i4?sudwwE-XA@1Co7GHo(8>M3&es;}4ash!Q;%Z2%p{I(nhKeSJwiW~>g;X7S`tK)Au"
    "aMNfw6J|YiOc6A&JtV}0y}tkl$<g8cRC%yds*EX$Q@(0S^%b{^YI9dzeZ+VrPPQ~m@3l)8BXv-xGabXND0$1"
    "hyb~IKNGT>lMXnXvjc$T1m+~1Hopi=B!=OrF%{XywV3vj89YT;$ff4zvs=#nc7s2ejxoFDM1ZMhIp^3=(O0>"
    "BCYAJNKb1A#zr<Yo!FZOF=a6b2Z{t{&DbjJ6la-z6;3!us`Nt8~&&*sTlD^j<T4A*~jfTU7`*AL&%4v>$1h5"
    "w*8Of9VSFd_|`*6Ta@2v!g2ivLnU@p?hHP%Q`-T*w~61zm(v&v10*}}xS4y-w)bcl1bBTvzzLW9{k(OwH#xR"
    "!tir)fKzJy`a`F+t5^XVE{Fqiiw0Ws^2HMc_7>02zwDK-m){O3>~<aKG-3FW^`T(ij!x8t<^R3|DmycFQ@%M"
    "fqp_;o_o>h)pi(Cz+`hD{`eHS*|Y}*^3b#>WfD9(SIrb+6oP(o^8OliDA2z(Soyf;ah%BcdyR^;d6!&)0y-p"
    "qSl9_!Dzt_@Hr*3Q5yomc6P}))PoH{fN?Y$RoX_BJJ0ZhOPd9vOF+=b$V84EPT$F>w@fabXDN>eh{`0Ll0T3"
    "JTuxa{WD10{VD!dUsPOmvd<45czYPQ+-)7(%=^Sfp#M-&0G7Ya46=^Z12D|xHa*B({#pg&xet6?Z9wjP)u95"
    "|MtWZvsA075;!hc`AIVE(!u}*eg_D+8nhw&2qEDQNQOS7Wyp&K~i${s)quy7csBuI1K3C1aZK#R^-Lb#DJ;m"
    "!&9Ab;6yGMw>V<7i0R73kKBMoyl2i_}<h*L@{qkof@Y&R2MCpYf9F{x0BufB^>pS#^95M>$oby|vYgfm9B~D"
    "+PM{?4o@RER(d|uY}@GvJ`_+_^Hu?+tcqH?t!#Dy1wRDQH!?37LBY!_FnN+#mCnc;_f`kT$WwR7eJS<I7x0S"
    "a5TQ_{KM#)c`c5&yoUF&s<}y?koBLbYD8fGnEP^0<@I0$PO;xk&aRh>KG1)V9!LMghNPzUZmNnE%mD{u=PYw"
    "o+!d>X0ei?@r--toIaS$53vtfSq$7o68T$Z+`bgUWatUIUZj}XKV`tM5c0trmKSC8W3P`NUv^Su0U81p}apt"
    "xx?qDTw)aLrKmb0dT4Od9-UysJK1&2wDfoMd4q?QYK1dIA@E4d@AqmtnZ+&ZK-7yyvX+epaHMgUB)$TX1SyM"
    "gKSH4>#r;QA`T(1tmzbgN0S7)n&LjNR22qlNwW29U3tDH~SW668VoB*>C*pvKuJ!qYp)!+%DZG1w3@Ib$#VS"
    "xX2T4a|srMcyeK19#zLO3^j5izeBD259ub@;D2g07spDEiqoQof=9d2xHND>zUbQ65VK4?L5867Pkp&t^{Ko"
    "{fsuGkI-X@9EY-oAU?a2|9R#uQow<v`St7G;a>mf@Zk485$Ka`DS}4nh*<m#E5B$bWeIoC<RrMjywkbjkzD7"
    "xSQXuO#dhgjqDt?5tkB<A?^#~B&4QhG9Ra}?+=Mf!rHrDk3G->t7TWAH__x<5`c$poY?0&rqEsnjZ62vpTbk"
    "1xS`y+e^jc+riGzQoL67px>R1tZ@S(yUow=39J%0Y&N+TcZ&aFH$$4sswG)L!kpV*wzHPs8w`6_v34?QJj0r"
    "5Kd>pq;vy%yDOC!E7SI>{j%<jZVI#MZEE#MFz?JYQ(0XF@fq9P<QnaEa0q>jydMFC^s4vCR>IW*gX9{Ma<ls"
    "4oK0P!<`LPZML3JH*UzDCCT@1y6;_(4*@MIiav~NoKNiPl>EF!{Crd$)YBvg=>ZL_)iut$>f5Z3^cNj6zsJx"
    "i=Si@;7KT8a2XlndX?gB2)yJq#>-BTjZT&ek<C)<voyhu4b*xgV?#Qndh+5Vrp?U@e7Zp#Rh&`Q>-+8zR||X"
    "hh{9dOC8hheGffKX$Aufou6zeTz>&O7?yn%?*2_1iZvcOtv@(42xmA>(BD=+cHL#9hhGXL+q<64YBG*NXXhk"
    "5LO<5^EBd3ZP8P?nvNcKm0pO<;o@l>Lxm5jvU7!hXS@d=MbGy}!!Y5(M}J5RskfR(}dci(>h&G|RqW#48OfB"
    "t^>=Vx2re7`ju{E%*?gCD-#9DMh~`FDT*_TtZf-g-9J`t#uXZ_h7&IDa<y{)caVc$$8fh0&s0ZbW@`jG$<gm"
    "2vB`;??1PV%UAC$aOon^3e6qp4<IMxHGqk;7XlbRdl7y>t5lNWoxP+;nmCX_0TG$@G*boRDHGife@rH+fp=n"
    "*xB9>WeT$`N1R}~73ky7^gc+mVy*W^C5^+XLL#M=D<`Qg{RcuEXKtk^^Z9eTADTFGD@PDBxeC<KdEEyoO4oF"
    "6bTH`<)frO4E^9=VOWeqVWl7oTRpd#1{`Bt2Zk*{=1@r6tD#Q6@YWEB1FI(5TA^lrHM$4Ni2)W;HYh9W47zE"
    "?7mIOwV6Lvr6i*87NgWmggBj*S~>Qg1YDmK`(Wk76x@<BWm^46c>t^9U605xJdTcRtJ#%OZ5ILN%qi6(im=1"
    "k+DEKOmv<U_ZOSJlx%CM-0(Qe_;L%ZJGa(k#%UOQGheMg_O5r`^;)Ud%pZWJ^T*2Y&i$Gz6%tPl==GZD@R&?"
    "CzX!AUBEq;_Q(a_awbc(IUe^KfLF#%q5u)jn7*8;Y|P#3$(;(J1%ze`4c0x0*#EOo-zDAPj7fMwAXa}atvgI"
    "NI~cZJqo+-qKO(n5C6|ea~R@D#-vN~);P(2{CTdHPA~nx)V&LP+sKhN`d6@;lVj2$X~}cRgcByKk>weEktMG"
    "r&urGxM?xehAtnI^AT2A7{`;wGUw{Tl*`7VSd3MJlE{(oaS5?>LEv~N)^Izm;X_iF5qRYxDOjeCDo|q~sBOx"
    "pKZTvnVXCOHw?RBx*=`_;Gieo8coM^Kpk1F~$-;<4641;$?4DV2uBgZO24^tqgWPLayqo+|9Of({QXj{aKMn"
    "C(8#10(LX~qsvL*H!g*EtqcAT*UqJPSv#G49<Gcc@r&dB<RBw=AJ^I)~X;QZAG%ty!{TBRA1ppTZF{OElYU7"
    "T@<|hmTC=4CP$O_7ow~f)5Kr#8YO>76x8@>|mLqp3~;tDs>&n!;S6}m}yw6Ri+qooWNo;x6s8Tp*0LtPD93s"
    "H;I<zga3>pX7BJ2TJ$y}RSda$vM#wFlV1<FP~<J-#LIMfA6#%D^r25bH3$kWmDv<VQOP5z$D(2>+N}akw}PI"
    "ilcCs!*e~t7B6`utiMr?sc@9m0&5+leTNp(xs^Q$`5|6?r3M}fJqG9L0gG5U1@j8jK|B-Tyh-&O-fr)Yb(0C"
    "?^G!hu#vl%jI$#Wb#U_tMYn~q>`PN3TeqrKSu;nZL)Rj%9<epFjxEof7fW;eyle2#t;iejUf3p56$%O(5g*T"
    "v48i8I)0Um);jZGOrB7(!kX)A<>}_UrukwaNBl9c`{~?ZH6kBSrCG1P|7&p3ydujf0$5rsfBb`Ux3GDLw_Z6"
    "um+Y;k5+H1XL1d^=VQmQnGwazuLX%j5GcuQpN@>b1g+ATJfo(H_z!W#qsG5(oAvEgjlL@L?dZSlCwu)Fp^ir"
    "5(%p|A~UCF<LD+OjX}OJkMAYg2K|<_t1AwE7vIOttgA5?ZBmkWsM%L>I=jw4L>5N$S&=M@`)3o(T7)a8-eCX"
    "e)Xg9POxX;I5DV-cPaIX9z_2Bpte4$4-*or-Mo4yPZz&#XSCTDZ;l{VBDT=^kRWV`jTY(xFO<;?ho1m4TcxH"
    "8my3%&b!<WDZm)&t%j8|kY=eC4`1eUc!!4xD5Ok(n;M8)8?Zayr06FMw(qSru1peUf<m;j~FDE#^?`s!<#C$"
    "msp<6hAEBC}i+i<aZK{JIU4Sl%TCMcV_NL>E6Fog4j!1pr;bv?*5z@M3v_;Bp74_FZz%R_IE!QmU~Tarq7la"
    "tp1R*nRyZ)t{F*WTJCaw$x|N%a8JCHtR(fcX{;U=p}Ka3l@D29V@isIR+c?iyUY}>bS57d?GE#=WFK96{1|1"
    "Wrb057`TJsHe~`k8RedI8B?TJSxjb08F_Y3i8__2G&ucn*eS=L2zU4qc;&etChMpGX3*3Y(>n=doF{^|mni3"
    "X&h8JsqYSWPa0z4rRhh%nlT(x1A^w>J<HFN(3Pr&4E;ha7fE)Tcqk2$FoXO3Jo}@L}2*eW!<YlL}3Yoq?C92"
    "m_d<o27i&!V`X$}YAQ;~#rDrbiK(TH;Cn5&G8IsnbhqFIiC6?$4LB{Boo6{cw-L6?o5EfYQr{eZnHM>47qLD"
    "^u;swB&gzNhdFy;B>=Nj2L>svddnF_I5_q;lar?GZq;zpT3qmNH&p@;|M56(I(GvF_H!6M8MY)!Fmk<D?eu8"
    "tgjLyg=G3kR5V#2K0?iu@ede>W4HYI_Z$`ObwY(TXgtDwN}PLL$m=lR$SjC*$T#tv8^z+jxV(H6`y1%enzpj"
    "tKx`7wqj^w`KX$}zGok(SW57Koph;VNDSD^c&U*_5tl+L(WNV~8LKgSJPoy?4A4U#rzL1`Dt!&Np0GO&@8L)"
    "_in$pJA>kw^cR&<l9%D;QKeB%VBSks7$QLWhoWkvXlS@h<l2KbCcaT@0v4CS$$vmYTz%D%YvzqBpUtTwl*B;"
    "!4kCbKK24vYE`_XHR4UwQ<6FN<)8fPrqp6@>YuDknv_xT^YD|qLRU5X~@re#;+Etwa0(E`)8i{2r85o(~1u1"
    "2;5(2m8Wilf`r9B7bp*Q8I1)I^Yb*Ib{>i5X_g7O815hTHP$rr9(pkXAMQi|NZQGDhcRt9aIxL2?i%^L6*Bg"
    "X1Ga_{rHP(F+_5#X7~HW#Yoef{+~Vm>|GQJX^)05XLsXjQI=)o@sziPxAq|)giY^D!wSAmpjPsY>*np_n5$F"
    "@=(`01qy%*T}D!rMKC97_^4&E$bAJhVcV-<m4J#ah|Dr7#I_U*gw1v3sX)u6C$pVE_P$yrU^BB-QSg{}_-+a"
    "wS73`Lr44l_V+LF8h#9RvO@`v2wgEKo7a)i*=LOd?YMqlkAx)5&XiVW-lXSwN?pqtmgkAG^dru<~PdI;g`~3"
    "9RXHN7ahH>!r>q#ySg$z?Bw0D$7gCma?13PdUEvaz}z>F@USEuI}k?OK3@B~Z@!eDD`5tmr6xtaR3Ni;U^Ug"
    "Q7Ee1>@exmj?cDn6M{LD?vEm(PhlA})LtVfMi`lprB*TjW^NgTuNZ)8ZX46L}&pcr<2KyiO`1igf6PZ~J89A"
    "sU9jHbNBXgIfeFB=vW~*+UyroFq-iDL(2>-M~zfkKvEe%e5Jk)H%9YnFqP$)YUjWYyKp?yzLit4jaBIx7!9q"
    "euGKHqcbOh-n;Hb&?BM0cB3KtYz(RHH!3+EIU-B#!6`=@q28~NPmEm2Ql}o7>PGZxAT60CJB;mR4JL`F{<6k"
    "RN^T&0v+j=(#f;M&$gu2axX;_0V8cQ?Wv$mX81%Z)l^7HeU&x!=G=xUa?r%ASPxJUT4WZfl8y>?NPjImNpW+"
    "qXZXP~4bim)*n<-J_tGDd8%BC+$drogR5Z#yR?dOo0)7wq-WxBhOu(YS2PEn0xT}MiUIEx$;6(K$Ch%<!vBp"
    "#mdY?yrDjI_$BM3{NUBxd3PosTCyI0>BOd{XPyBm$`Xe%h5FV2~1qf@I2PEBYGRc0dT=xih0vH=XfBLcmdVQ"
    "nocvS$yEm5gkUxZ~@8E=4qJWsN|=vp{W8(9l05yWLB<PP1M#UlkvXnx`+`N-;IY6vgJv7tN=DixWO`!00(q^"
    "FMAcuC*`!*X-eVD<Y{$XrH+m)29l|m`6Tb~2gxENJJUatA}6~IFDXiAzYUrfQZ6W0mhA~_@z+^`51V<)Ggs}"
    "b1QFl~*P5v8Eb>z42sc?KZ4YeWW`z}T7)NV->vjz7A}J-UxtX%Qih>4WuRE->)KXrZ3S*ZUZzA4MPZoJ`Gvv"
    "VypG5!q7b&H%??iK~DA4{*-N`Xr;?3;Zku`uM?uj})(AP!j`|0fT&FkpLzu6~#-v8z3<frK1^v%gd>uDPch?"
    "-1ygExY0h-s+%=RXtXpBdegj;SKndXnXLly=KS3E{P7Gs|}YGs~X%PblA}OF<*n^c%IR+cElCEGK(yO{}JHf"
    "-aTMc0+fx^IaEJLz33`h!0#xa@hz*M9jjf_f>U1M`8QcLdce=@TG*qgBE?_Lwee`<|56iQVK@<HX)xXzOK-o"
    "+;*a=*r!ZBx0W1!3~;b-nrJr%Yw*eqMJLFMcf!<yN`iF74d~c#oTN-CJ@=TQHW?Ifg`3Y%$mnt7-86crseMq"
    "ofpImWN!Zvtj4fE8T>8WioP8(Bu!JvTw1R<4$b@X&Fa^qM)EEY~DWFxoD^Le{#)!lRr>|bauE5!JtVuLE;!l"
    "KjWtn6WsVxjMYDpZ_UR$6M^z7fU{wA{yPt1y9!7Ow^8vd*7ewMyVg0#@9S$~u&C_hpKf)*+u3kD-rt+TA53#"
    "vxFVsAs_ScQt7r3*}R!8j(yv;Lc+-I34C5E=`2a-s@M1dA!+0>&&tM)OvgBs|HSc`B^O+kzQL1Wto28SPr|u"
    "?=nv;g^%4MrPE;dJrpWZ;UT8nXjf^h72VXR3=sheZ*nb{#ILK0pZcK^m!B8vtA9Qm)7g{oFlnebz~0lrL=j|"
    "v1T>?GduQ)io5C98jW3gwoX;&PO(@wYs{LuvxJ{IwhfB9N1hCW?y7|ppv9q;>cO6+Q}Gh0xub6pL=E$FN!lZ"
    "3v$0}_6LvfnsbDNrz0corz33;j+9VSz{9H5|#LPo{$6`Xkq9Wqq1dwD@9UW8GmbV>O=u^~Lj@D>lzgXUlR1Q"
    "ZO;HWbV4RGu~gt}82o)iLk=s2^IW9Z3plljM8leHVteQ+~{cuS3*xzFF5)t)x)&@b52=29nNEwlo``!lTE5|"
    "$5yfx<$gpEu(uX4D}|mK(SFU~h2`$|sEF=*L57^zis^S`<TLFC=(Yr~uJFFs4vy*z{e$oqmD!Tp;6LPtX3^F"
    "#+?j?aML+9Z=~>AgxJI!sr=g(nP5shS(}Yty!IiafymCI*;Mhc)3&N^Mt`#9i;o{HEA*9M7`_R$t@f}^9|kv"
    "Gc861#2>>=E~QUa$Xu+c)I>jotgsvtU?xyel8g^p0UKGLo(tmC<qj6yg|(z)+i8lZ%ozU?-)PYRjnomaj!nD"
    "QPSD!DYaiRZADlV=LPFK=WaGB|Ql0!X0qb|NS;)G*Tq9_m4zjRS!ev=2zuKQS(nlxZRM2eqC+`u}1>_qlxMU"
    "78fl-9mQzjbwgsC)!hncDgDi_5gNtKJ~2~p0c6!B7uUTbRvxpj+wz##ldoXj!Ego2I==27nxid?frl`yyk^z"
    "g|Fk)sgVEM<No`7*##QVFC+flQ$U9&d?P%Y42W{TbDCXdDhDtlkF-Ad%kOsy+8-M}f|g56dA%dRGslsESO;M"
    "mStsHsa&MleN%@QIg?YuPJA@r$N;mdL^Z`*Hpg)X8u8|!LO<N^mU-VoSj@8_4)~Ro~@lQTt}&0FUL_jStWrv"
    "m7vq=<u#$+RJNS%bef&720PO2aYy<PDxpcyVB;cPEQi(lnOZozW>@g4+}f)Jq74Qm86z6h$f|J=&g8djFX+3"
    "WF-R5bAw_PFH}99`feB>CFgQSs&X~^;0c`8RX!MRV4(BtW@l;BwuN#U+*@g250&Q1nvNtTX_YLmO8oKxU>yU"
    "n$jpHI?Lt&j>KE3ZIe(*B}&{^L*Q-KqUsBF2`fi5G67wTlStQB)3%y9VW1_rn;EyQH4a1b1`3smBUmVX5LIR"
    "|mJsl;c~K1N6w2BD*`NyY87Os~^fJ#9vcf)hF$^x*gt)ZTMenl0-p6_71O{FNfbnyI``3D>wtIAzwxL0~MW%"
    "~0Y*64q20ZI09wa*1G``42WC-eA(9TZ@(Vy2=~isaD&KYRYclaZ$6v8div9Z`ORHpibG)RZ&T6D(`R7)tder"
    "?rMO`ubb7t<7>Mb5+a{Es|{Ukn$_Q=t4*^S)U*wl5dW9Z?aF0wRYj<4?R8v$Cgt<3=kDd_=JMC><*&`<Z`{k"
    "@n9JX~m%lZazjH5tXD<K2z5EAr`Fr>B_vZ2+-OGP8m-lwP@$A|g{y^<W_q?I**|F|<gWa>E-SdXKXUDte4S3"
    "Ivc+VU1o*na^H|RY(>OF7Rdv@G=-oW?l$e(*7e{M(q+#C6GXN~<uwj+P;jr_SC`EzgN&+W*cdn12tNB-O!`E"
    "we%i#S*=K%xu{mO$BJ=3?On5t$MZv93JO!E<~K%^FVD$TF7@dV50TR9*ZSzG}*Rn(~>xL*F7AU?}Z~8%tX45"
    "y#hBv@oj#qidzYDz5Vh$|wpPpz|5!XeIM>oX^nfWYbj?JJ=3?Bw6(t8rAN|3Kl!vvbh>4*E&vtQpvw#7K145"
    "z#4k)ggM3cXj1xiVu2aFy%O8jYC5IDdiE8xgOgDhM#^i`qcy{8WeX4G*q6aYu}a!~8;O}tIaUFl>LJ|1qScP"
    "1rQS>~^cX||XR39%)9qgFxGm@ur`am8SEYx)A4Kf`b-vd;tu215+PXs`%xL8~?Qq+FJTN)%RsR*|3tP4>_?P"
    "x+-W=rck6x(DK~+rHF+&XR84g?Mw(C%8c0YQJ3EH?@PJoV`KH%LRCTwTR-u&GpEn578*Q>*^FT?yDFQ3zQEL"
    "w~&!)WoJ${ky87vnL^wA00wB#Sq^&@1x0;gphD?wyy<@;m#=vbe9V6gE<>7N}=}CMhs|Wy|?a@&O@&qeJ=!0"
    "SW^xINczJb*r+%MVyvNbJvw2T<*L++yCj+KH+erHyIbW8-U;^)V-}=|2t@#=y{%F&AUPL>;AF#{#OR>+|*uH"
    "99r1>p>oKqA(W=tLE+9SG<S6I^XZ!lO-EUV>o0dK6f}C0Vg{GCib(GfBdiyVu1^zrl_?b+kDCs3BKpt%NL&P"
    "24}MB=1%vBP5AeI*y22K1{6d9Bl0`m7if<g2_cZfXQRnzo6TZaXA?)OQX5tYCd&)QTf9>8hS&k9Hyw!fYd*$"
    "DR!_GV6H)c2XkW~&#U?b@VnB<<IMlA2W2@P){N?kyi#Lf1wAU3q|0bWJ>sA($j8s!z}{T>~cS~TFwM`a7X1o"
    "AngpgKyz3^WL9BE7(Piy^AMARhj0z|+{!1KOO?FY#=ZP`l81(<z;+Nm>$Aw}@Xg+~OE1N9=@hS6pTaTSj<kh"
    "<|=%7}SAfc^Gb(ViGu=8Y$w%$azpKKxh+^!2NiZ^rBOO@3HO8@;j;Rxmc1soFk^_UCh|9j37gmV56T7xIpxn"
    "(vxrF6-8jolG1ICz=@DaNX4l9j-tt2obt%2{ETVyl8x_dV~?HRBufnL67h1mV{anBD9(?+xty29u~wPGW^&x"
    "bj)k6d37V)0XUSdE8kaDuTP90930*mjuy*u|JZdJ2oo84u{&2on-g5w{<Je>!)8MF+9F6X={G+37$qcpDOQJ"
    "2fi+FT+B8Kz0MEYQ^f+1joCmb1T8C&^;vRsz;3%E&reX@@A_;+9#d7qd^E0eA&OR{udB}ecY=Ba~Gj9ng5wd"
    "1f=xnuEc=C#h>{0Pg}f-k)#B;1my@~TbyhGG*aJi2^v$swRNY$k{^u1~YdP!-QK@>qhp*<kd8B*7RgecJZon"
    "I`dzwQOqyq51BE%_2>|J}@tJqmMd$IAr;|6Af|X_U!-Q(VsNa59m5BJDpzcn1miKmXMUD3wD9}(Z`aevnBW1"
    "51#aqg_0h-3!%cfiP`c@?Zb=r(L#U%9E9dH;{q<d=%tgk|AUzECeRbgAGgOn{NEwMO_)ZWfJXh|IC}aNj&o0"
    "+lEqJ_lj>zeH@Tjqa)JTi&~4k?s8U*KL?B(UK^8#KKv6l06fPCODcDwpk)yJ5<Pk%e-^Hb=s>XGlu&<PcPmu"
    "taH_tg)=B(fim2fS*5)+0rk(Bi~%c2Jkwdh{8NaP2nuU;KpII@L4N8l0;G>>e6l<RV6;Ce-0<Y*<AG0bKR;K"
    "KVwD=cFIIM86(_s;Q*YA9J0vBo)O6X$q<y!aMVDzf+SES=z_S-^IFfjzN^4PvTXl?aN5BciM~ORil+vq(7w8"
    "P}0xofFQ__i3|n7q35>cw3d{-`}s5tqFTp$uc!NDJ(xLr(*`WO5Uf4E?MWrX^Dl!(5phYmh0tG<zWmP@T5Ys"
    "TyGWumF-hgTXnXq$pa>!$wt&}P!yX!ZyIPnqRYWAT<*Bp6g3&vGK;O;Jzln>ssOf){jz`j=I}gf{Uwliu+s^"
    "@Wxml4Jn)zS?(oj9EyafO^!hf>PLGd&+&}nhaDgkQY(4{K2qCw{H|kWW^sc<{-^G|dk24HvvhpXL&yz{&NuV"
    "RFj01Z3+q#-x*9rC&lh0v@T-cDp)KQwua$s|BUZZYva^Z33n&eQJAQPH`b@C?Mg0NX+!FDGQ$92xTxq>xFhf"
    "7V2BF`AAv5WxI;R{ky578;c0vN#94d!r2(O%JuL_js1VN&ori>4=~)>tNp2?UEWattS94bMaqU3E3Hq4Sxbh"
    "H{1&b8|iN1$1PytX6BGQc0{pIL-ec_(cR2sxrx@XVnyB$Bgy~EcLPMw87~0No@3<!ul%jZ`*i)9|$k_5ww>k"
    "e(>1E{Y3sz;T>VV@dbH?Gk`~Pjrxjy!n!cYeukk_DZRngX@?32e>wEqf=?aJ<D$P13dSh|HA%-yu2iz0-Csr"
    "js%rCi9NX5EHZ_MsNoxz#8u|!5d4LxGf@X*ob*AGCDSVuj!wA;a>|y*`DQ8Fi3>_VTa4Dk}v5>0fp~Y(1@^`"
    "eufSp-#KZp$v(@FS7zcOtdcUghf`r&C6W+6|94gDOS$0e<Mlhu3yW0eSCVb}v)I*%Q*t~@}GhSmkX-06S1xu"
    "Ry0W(CQqIjnW$+mWO6{3WdBw9I6h`l?lB$K4h)e?XY4`CAM|@K)SnvEe~&H7;89w`Tg`8W1He4c%a><j1QIe"
    "af6L{_$@yD+XElzi)w^G~wEazM>!_O+O8|O8Tt1S?y}NLI`7t6Dq5%k%~s(&Bo&@xwc+8MJim2;DmH6ru>C!"
    "OXjSM8s9P+HKM$Zq-Fp@1`6I=wXH=?cIUQ(t*h8AS|^pmd&~GeVWv)UEfnfEq}W}fjSzSvD(n4sLTh9E*lJs"
    "Xg{hE{PKY+u7VAZ$)061n^yKC75%7C-RlhiuAfHjSEe_5R@IorvDU;3!zcChN9WPgeKAqoXrIc<%lS{R!brW"
    "5)!!T@Qyi}ObwAP$vsvy`7RsGVLTilN%v1$TZ>6ok-XrCZ```$N<2yF?DYu7zjxM;*k!EU&EuY%s)`|RD!Ti"
    "64Ia!>#SQM-}L;r<SuZZCJ7rN$sqyVTM7;YDOp`az|EU6o9F`ps}_2HV?tquM+7o=W)*tjF+I{yOnib4}a-M"
    "2>4>>V5;Bt8FXSO&2NU7OL2%z29Mg<RMTbW;KQ<mLIWkyB!}bIke(->BIBe;KMVszV1FNXgnO8_wch?BYj;<"
    "JydF8VHqJAhktVTD;z4edC8f#N4;UEam&}dxemXxmg36flWA+(NL-?P|0WXMQ?Q)^(ShSfMW5D2?J*?iLwJq"
    "0F{-G-7{eAwlb|pZiIfUdGAw+_RX1zi8t3Go;|XZc|2Cj9j9d@9w$%fUYk%C7(U@>i8isQ7%2P|L?doAdmHn"
    "pfZAS);6rf*rNT3D@!vX7c?(f+&8yQ7_S~~vL@IHrIqrR_KQuq??x}@fj8GD!4`<>1h-&j2`)<<6oQZ3b<Hb"
    "~vB#~xk%={Wl7phiB8QAazSow67|D+#U`Lx_NpXUk_4(O-fRvD4p?>dN<s%T4i$2tq+xNygQd6LNq65ea@OU"
    "csC%GIPZU`eOovDfnSHoURZjW;m3H{fO*^8q#Q^&d&I2En{M6_fb*F@_)bq_2m1#@7=({eGdS{fEY4Txk45p"
    "HkG<`N-ls?mQMd_!EKGFZq4Yep0Dq2@2i(28?bsglR#^nqUyb;&floJ-Q)!~8}SaOc`<YxA|_gK?IgTqGLZc"
    "zpu2Dr{#&^&eTIATSLMFjd3ebES*1GZK0Kv=I!_>2bF1Am^9_RFqjvQn`Uo9+h>mprK1yF6deI4d5H7giW%q"
    "9rK~qw=OVDnH^ED!4WAZXr>7Zz-E}Xy^gOWmbA4$S;75SpPq8=4}L4V8b<vrDBlbie5z4=yUC_P(!jGujB{J"
    "Fu$(@CjMW(jMxaC{$T7?Kx!0iytC=AA<v{~0T=CR$pm9MjyiCf9w_hYl6us>(>;mPFL*H0#Av!&)Z=*M5`w&"
    "<9uu8knDyCgZS}>%`WC^NuT2Us)DYOGKBII`1O0oGyT98Svy_ndA4QFwsZ`3`8a)85rSUQ;7yLnI?{Qa=l*G"
    "`G*}QFA{Cur#zIiXp;~V0oJn;vd67CMmW>3YlSn9+pnRO8m4g`FIz^CwKWy)A24qX160c?J|yK92|3LHL1dG"
    "u?Q7c$J9MWA8qxK-^1_qlWuj5o_>21%pUnp!<)uExz_l>_@xcl2XCxtyRBcedLkMa%ml&eWYiS4FiPkQnHz%"
    "iOFAmQTEY2BcJ={o!>`aVHvQ<_49|IebM9p4RHC`ZczRjmd|0Yp8-^M@d59l7K*|6nC;DgRCQEu0pQm}<m7`"
    "I@bt29!HU2r0+3~e;>dxj=+IsS`;O&o|NIcA$i*^%<;TpYxf2o=DPPv!f!ad|sSuS0SGp>@Pj+KaEp+77ZgE"
    "}B74VU#U2pm$$W?E7!U;k9<^Wp+S@o`LDj+qYMpsFJyLWw#a2-B2i?Wf*==F!LPQw$xBbA!nJIUU?fo|Mt7q"
    "1`dVhpJGXY?VKCXgRVmNfj9MTlMmd1mbcSMm8aEh1)#{)on*z7QNc_i3gsi9UNK3Cod9hV%M_CZN=|X`-65B"
    "mh%}x@Gu&xIatngiX?qMmqrZBL0qUi1U^|+)0S&dx!zyqL%??Z#9OmFlwuyhN_hx3`pQ-FqRuH<Ox-@A6`Pc"
    "Iw$<z(ZU+x#B_d^`k0RQ9M<kcKhsOqC~q`q)h7>Krv7wu;#N|<#}xUOoUJK&Jq_GO$<sVykn#9-8X>vEVM(G"
    "*P?!q)~Q$d>Z}r4=ItDdDTUO=dHq=r7A+<VRkbKg(O_=FI*yU9*?&%k6a3$1o*6LF%J&lKX8K7*$B_@IPk>U"
    "h2RH$!O4t&egMWI{h^--ZeCc<z8UHZHM7pKh%qx-s!p8_>o!fv*aHupyQ5n=^Rck4y#&aLp;y4@IU>^V;zE0"
    "%vW&AnZh=}lh}8=y<O(1W(|7>l4CY`%@^DZ#kjb69}S2F(I<L%q3!S>xXtY6=Kb5<D>f7_?w7Y1%-nbPtlUR"
    "R>DkmqVLusu<Rkg#bGV(oPm4Tz3%{>OXu}^Uv@sWF|Kex1k^Fr6>X83B-aq+C{yG@$A7kPX_Dx>0?LC-}^;q"
    "HK5y5X6kRRlrk>PftV6rPJ6Ar7Yu-r`s)Gqu{xdmSu!2efYKru6T8PCe3dM94cE`}9ctd^YSR*6}Jvup4=ul"
    "qp$t=whCQT?Kd0!dV`!@l4~4yCRymI|t5FGzHgm|Fag=}CM5izn1h-J77(xmUBJ!D)SfhM3zGN7eER4aOG>w"
    "NY<K&iSYSv~)eH%B6esAE4O`C_t;Rm2)~Yx&YL9p{<&pb&L2en&mfTy#s2gfQDrmyhkL9ho;h-`O|Z<tbU1k"
    "Hsz-Y1P$kpvQ)#fjuS;6Y=427TxFKmb&1zuur$?N1a6_T$mQ&m7p$E^D+3uSWX)VEZ={NKj&pGcdoP*gi^MG"
    "z-51tx;Jo`)cCV#!;7`IQX7x=g?$FjWmn!P2NOY>4C#Zi+HCeJ+7V*qt2|84UDL`yFXaD!X@sVeI&`}`AbdQ"
    "m$;Gpl%oB5to_xb&vH*w+<#MeGnt==iMM)!L)C)ec;;wjk&@K@~-C#6rHGnbr)AG{8kFot11B?N4I8P-M4>!"
    "{|p@K2x#Qdc}>^m4~6Q*ca0o-e6AAZ7DpyVh|<LFVavk<-?pDAZhl1##iYcEouAX}QQta-W!1eQNf{$W#;T;"
    "RJXrB@}Bn`Pq6O3(`{jr=n-(Mz20OvM8$i2VS*@h^Dt4A8_?$d#l|zaPAu?lVYvH&<t=0I^J@$F<E`=){q})"
    "g{DLcSxb&zKMMMwf8>y4RQl8GrXwrr%o`c@$%VyEHXn1Azu#-{Kffsx#Xi#Heb7a(F%~+Z;slbI(Tjwx$kS?"
    "bQl0X&vv~ZD%m-PM|5Ru9!8>?3=V4_QwKK3~lg2+c6fYUga!Y>nRSgcG#9I~jB7e1-Vn+>ZwSk!lyFIPmWZ+"
    "gf7Ytgs!$|Mz`;9mzpWovu5v)vRJZU^^T67(9tIFM@jl;K7MP7+@bJ+IZ5iA1pN!hhLNjxR>7dTa!(~I42AZ"
    "{TXT!A=YK3B_W_j}`A<ufq(Z9H>{`+Acpge=0%J(Q*}!O`g#I$pSm2b%LWeY2)m)0OJd@HR0k)F`vVg4y$U$"
    "u;3n?j>8}pl?sEp+MET0Z70zRO$<z`1AqKoO%7Pnp2AL@>9$y8p$&Vh-XzY<evTvJTX*Ux+0kloUwY(tZ>Q("
    "A6-6fCvD)=hyaFFwTG~}G6@??EJz$s2QRiKG7Ze8DuMb(;2Bxjf&A-!Uh7McvFPoUZ>ecu0%rRMsnrrHDy8p"
    "|Ax-per&I=)Oo{N5XqBz8#=hamS!qv?|E7OKmXX*D&zYlVQDUF3-5CRc)l(GwqVlBRs#m|X<)H^oid>JKvxO"
    "w535yfMF(W2i77^>Uv&H4kp~6w~VaZX!wSuqo@}I1ZbL-+Wq|)K5tV!Q9q!3b__vuSi8jE^QCr<7s9giwA?B"
    "G?bJ0Y2;hE?CbL-1y_1J69w@_9vDdFUc0ltjdU8kl$Sv1^l>AmB*uv%UB|>`RJ#+IAVuk#&`smqTmz67EH|K"
    "+8PkT2b~8S%%&UA4LNX9$|{@Y{r#;j*p0^p*~09Ggx?b&HP)AX@?M60_XhJd_s-c9$8|Xw!@a>Fd%#d&d~0%"
    "aBKFU>`ZdaqF7k~^NE4|nE!;>p!lDvTaRLj21eJcs(&1RjcBFwWDwwFF4#uH%O&iK>-<ASrm?vZ6_^jeU})?"
    "3Y^0&J%2R{&Zv}cB8by7j+n$aAOJzi$hu=Ezt+<9vCc$^&yPEFk8lzNq{3<%5nD%MDqQcV&LWM@HgFOV8SW$"
    "!(md`*{R7zR7VcGD;>BY~7XWACCK6;v%l`UVDOwo|Tu~u+u8ujd616mmYyVN%PxbMY%zh8;{?nfhcB%^30b`"
    "api;&d_nVH@2w;!2J-gMp1SyPxnCv=KP9gIK>V{qlecBa0cKbO&R2aQVvn`7F)ealxciYOQEnG&QZHchmC+f"
    "ztL*pc^xy4)pWSqqb8Ff|C5PqOCX4r6eU_bz3+DlEI7$uaNJD3%Ni?C}jd>eaQu0V1{Nrv-rt8#}r(yMXnG8"
    "Q=qt8scL9aO)+-K<mhs#3C$6(xdDVoD8K@?fW70R!V2;Ra0cXJ3pVtv$@BQiGk<ZC$z)Y%yed~<6lWN$_=@U"
    "7Rj2_g!f;!XLIG<qU1ejTS8U@t&)*@6A0aa2i`9%_jh5WyI|c;HwHcWgihQJr(Uql%Whuj3;})^QiRQB0WP{"
    "LBX<G!@kbGF6U}_^QB6-Yu#e4~i3zVGUic$G5p&}qLP(Faj2qg*E&XT2AfP~7kdxm66QO~i&se!-K9P^eb7e"
    "*Vm`(%8Jrbm2CN(EqdV7aOO4U-6?e&GBIkpi~@)xea-F$+kmqKO~;HayKGw_wDT%`8wRtRZWyFK$T}4QB;OX"
    "Jok9NGo_LC5bImXha(@!|W2Iw_26$<r){#K#l8_*|8PsLSQNEC6Wl%8l+OxWQ`?u=g=A@ilf{wEj=14=GaxB"
    "0{Ns&!wd+MYprovQbKG_CS`SG1X|~n!z^Hb5(W?F9*xN<@uch-<qLY>OUt1Q-go=MEv7t`9+c97mo-R$I!xA"
    "0ZU#AN+XD>~F_OMd95HgZ*EWC<#7{VOIL|Ot9g86vG2u3aC$S|(f=|;A^;DpsNbq>D+t}&Zi=z_+|9*Ld^%9"
    "nW1?6fny5p#3>~#SobL+MfUjwN)$VagIcvegUc0(p9EsRuF&1YVRfIPGk1&q+=04?ZJd&G;VVwa^rB?%np@+"
    "4pGztB&TD`<qCNisj?(C!#(Tot%g1oegy4DMnNOig!?8_-M()w20!>@q6lNaJ;)vJSBH$gaqWNep9D&D<W@!"
    "s)h|alFF1frJWI<V%dS94WjUyKzQ(sP0I<8zbL%BeCbQm;12RFCq-~E0?o-D)I|k8W|`~<0Kl%`9k(HLgIP="
    "c%WXT({$Wnuv`#-H<{S&74?WVU5x0oz;VYi0uQB5N8FLkj<X3GC_3<;l(q!f0#ot|0+NGeqcC?5JZ~P)Fn|p"
    "e3s{H5t*z_sf7B9ecg)A#mN>lsnxKrZV&iyB8?6_e(WG$IB$KOI-Vx9RMx9e7XK#L}%CD@NFnUt+bh*v+Lf0"
    "lU;_vIohDe3%*>(;28#vviSxAzDAk^KqSjZ4<JSojN3qvGen<v1_$>mogr)BOpg7$ixU(pb79eUdxN~g}LRN"
    "Nf2Z$F~n1NZa46%Sf)Im|CYN6`wGGL{BX0UTD-LZOC*vzKit-<Otw)D+e2kj7Y`i^`|!4=!>UPeF=cVFAt|r"
    "aD6Pw(ye-%9Z6=*LEcX>TX-*$nq{MX&Pv!s{HUI2l<+lgc1i@8qYx4>UjH9Y#UaNQoa$FGIh34y)9yX^1Vmc"
    "YFLrxV%AiCY02pzG!3FR7m4y`oFK>By3Skxb38P2EFm6b=?~frs&d=S(x?d<b5dN7lS~01YU{_d$}@7mPB1Q"
    "G`C(Zx?(<=_$M*wo!TwwO7Th<%h7`bTgBdL=97NP93CEFS;y&v2vueDgTUP}Lz%hh4XL5dQ#a4ftLVz%d=st"
    "g_!-9LmbkV`xDW?&57O}X%VlkA<fRFo$b^LfUqNwDDNPuSDso3aQ)Bk-8U-shyI2WQ4gIRyvgktL(>vL1ZEv"
    "zeOUo)51zNl+#-_t7%uRSzeU+Xjs;E1)W_{5e3?cYEbmBG}2g8WVgfPwTDCUeuXlrfe}8ryO#{6Vx~m*^du;"
    "v<lA@81U7G*}%x&Rz)J$lYkwX8q@Bw`qhOKT4OXJVU4+iF;Pz8sf9<{T&YC+(g-qejn*|Ggl>pig3cD+SDk*"
    "KzyuCVG-`L{eb_&=Q8ZgM^mG^sVarwyzII_3l%q2<8#1ImiaiJ0e8lPI9OS`G`PIZ_Rn$~gw|8Au%Qwgvm&J"
    "5mZ3kO6<pjJoj5e)+bvP#FgIlX*O;K)2hlDy;r3Nk4w-m7NTRUxcxD|zN<1EeK%56*VZyAc8{IZ-LAC?F<#x"
    "R$0xg`Zy`<RIu)gFmcYy;trMlXYL7^FP`^iL${e>b!Dl}kw1(WYWd{hrsp*X<C?g)zLP@Qh!S8Nw-%%7`g)D"
    "|6B$!@>dGfSTaedeD@kq<Gd#{F>pqpo6&PXlq2wLsS4W9|D7CI*K3XZFOVE|~|1B?gVo*LTb9)f}y!6Zed^E"
    "LLL-#+?XH@w>EfC(=>T*@?L0a5rumg3)Ot=#ldDopwlFQZ6Xou%Q*ITaI^<vJnW!jTRHmX`ZfT_FK%zA3x{{"
    "r>ST^;boIy$g7_`3Vz+f*!#WbkiPXiYi;-Hdu*%Tt@Tm=Zw(%C{%(#TSye(a>R}|Iuo3#B9x}rJtP2;ZURV="
    "0Qu+PchL3b)xf|1hEc}v53VN-XKx9E(-gh)Y5MdrP?@%2mU4_8XhA>=(@VCC9B_Y>2MXpkaJ)#^WSd$GQSf5"
    "VF4K`jr6&N&eIZPBEf^?NR%-41P!IX)GRwt`*V!)@c`MWgB5a9d>Gp@_L<H31%*wROhaX(fWbuH`D&P7XV^i"
    "+IHPpL$vR(W}f1}W(srUWCzRfd)6(G^KP)A%OFbAAVo=i?aN_k4$3Bzz0)2J<8)(<gE&LGb2`CSVQ;6}*U~v"
    "b#(jf`w%{!wtMoOSH-4WK%+Wz-87NAsYCzVg={FoATN7-RIwRcfaq#e_@neX}t^Yc6n>fCnF%H#+N1pT^rB3"
    "EBN|1U0q6et4-@k2<f0Kt!4>3aO0&3_ctTp+0V*5%t|6ZV?^G6OalX=ncc<r2o`ghQLVlr>B4Zk2<4{pBmg2"
    "}@Me#1T8`5N9hXN%GK=qf6u{bQI~L#-5hc4m$g(x*BG7qP0&QbTaJ<a+dePITzmj8CyFQQaX|-j2|1&C5v_)"
    "q5-Cv$QjYf*)#w?7ee-u5VT?U;&#^~R%P-*UUn84@u)4E&m(`=mNZaOy0zoGqGB_Rc<LvQ%2YtZH3>o5W7^g"
    "eJCy6`o3K`>AR2TtapBgMgKqZfH;97Tk!gN4RS2XN3@RaM!;h`rbB)hu99^EqXf>x#TSdeOuGaAC$GLF*Z{C"
    "N|%Ef%_D9MR{LBhkxM8ZL`Fz6VV$-bd=%{Cd}wWivlE)E#zkIkO2=i4V8jHdmj-L^aJ!7hKEzSi=(G7E*_!%"
    "WD=d8OF<c4975+u=tFELTg|Tt=l(L|$Szu%GG!&2PAJeOIXKZH83S#gJEQL>Dr*qv)d;q<qC<}Y*@is{%ow%"
    "N5J>~?(x71qF&SKIIglqYLW{lFc*_|Uf2RuXnBhzn7v3e&n0+fT7m+8Q2|7Ou4iY%nKgT)%hz3X_eEReya|B"
    "~{&Tw)hOr{5WWuJmX*o{D$p3y8P&L^ux*-TiW%{tz7Ct#HxcPCJ#9$Yxs`|q&l;@fA3Qn}0*CHgj;XaKU!<I"
    "DIIqftdf>cYp!(TOfSbkD;8V$g2yl7ed^OwuW7Y|Fm5QmFx%PvGe}!7oa{HCnZqG^O{jRYk?hfxS9FfW2na#"
    "127;M-{Q=Z2HSg0O*+O$4&qa$WIF3ckIxv=cLM6Sy+hgj|;OHfk!+FogLU<FFFTy&GO;>9*KePyH@z9MCe{-"
    "n68clkHSHG1qoq*Mw(~Qa|^3JDnnRMq0R5r3e7!_03kr68Hx@{N+%<jFKx&e=JZui8<z2x0<!s18O4{`0fE~"
    "O8kh$@v43!JdNw>h+&@1YUR)f*vt~FgASx_hGWZrW#KZqQJa|JDMfWc*4qv^#XncC_TPJ@Z#P?gl{Ih))1S("
    "S!qeWWBlFc;dGU*2H|HMj+epO;LNelA&dCXnCjC49vsDXT{4^_VoZ{+wyl5s6Cqz!aV@o!@)<J87mP_5g<-#"
    "A#L7mbiezZpq{MTT_+7(>=b0w=Hqbnzr!QbnExZk2SL1Zs_n20x_(`FQvdztE%4v?y`nL2DNOyCLot5Y<1EO"
    "tWn`LXIq5$BC_isVk&Q!@Pu8HY(B8nX&p2S$s*6G!<bz>_zf`Pl^~+26mKkJ$t%WViDK~53%sYc@C?ByfmV6"
    "?m92!ZCvmYa~2}Y48}LX-*u^xN^pa2Ntwnok-8X{Ra(AC9f4IvNXqgyT|`8MQaPgi169j;m*hl!Q`0LEu%fx"
    "nIsQ$_n=`iH_;EunQ97$gO(WJ+CM+o`1O&p4MGJi%%@)!*K~*M~ICF6daTGC9p%N$hUxV(w@0dO6-0~KTP(r"
    "j7&0}-2Qk)4OK+ftN(r#++Y(bNUx{~|6ke@-B82Cqo>9{~;W`5+LQw|3hoxM3ZIXd}i#K2pmqV?AU1Dg^fk|"
    "L2MrhpTMm~s4@F;^H2L8G<T3Y~D=oR&Z4V6A3-UBmtj{mRLx+N@(2C@YZ<wKIg!rl-A_Oa{i9cADezi0PCxI"
    "1@?fqJ)$}tXj5>b>5g_DQ(}VYO&!N&ar4%;UCv&Hjz__c21Vhu|2qhMimq5y2h-s3V61lP%BNN`ncxMq_ix>"
    "PhtspBc)3snr^WiU98&>p}_U5;r7db2nq@lO&jlPj(=59E-@>h@nfDKifUTUOE&~ZrY(uz%d>L=*LGqAQ90-"
    "21A&T6FltZ2tElT($1}(<JXTT9+xfCwrD3T*m-DbGPI_R9p(AtV_M6fD^Z<tckm>^OG(q_>aF<Y^NT-_Y>Zq"
    "hPt8GYKF#tt&OmZge>b@RLu6wq)QhVg>a1F836B&n}$Yh#eCmgw9K$0}Hw7Ep3E#0F)aj<E*s9b)NAl(Ht5U"
    "f3%7hB=Ux!8cN)Ne8LQ4=U&1rAUi#-#xrry0<X_tZc-*aMNWgr!oaupVLQA;;6`sZ|I%$Kc#fR&w2LQ=uboR"
    "}l4B?aD9V!sT1G2I6}vwU6zW6@kzJZD$-pgV^5o0Qj8BEmD%D?)s3i*CxXbq7^XNGuWLA<nEc<J)R&BS1<c7"
    "d7Qw3|EmCbdysk#msk(V=R8<x!g7=KEw}*WUISL$S>J$t&S}7*vw%ghr68ORwFMY)XALKodkVq3T+aITJck}"
    "{|7@r^%MLrVnLnDe*>HBah^d|?R|=rI>SEr>jM;po{T`74gUt?>G5QvYjsd%HY_@&NAURr9Ibp>F+>6dRx~1"
    "eQ!*KYbf<zo8d5^7&eZu71!2Ktsk+INmJj$s=Co7qTU5`nwi&aw%Nrtl^*G-)Kj(DA|a+a4W`1zyu6hLQNKf"
    "ap<Npt}!0vr)ZwPLCPaf14l)sGyBQWYdWs2KHJB&GFIn3{Bc{X7G$PWt3LAR01aZ^EfX7o&>dUI!R2N%@}}m"
    ">~?@m)ISP4I@&Z9ooGVrg9hk9!cDR$Wvjp1!B9@(D1k|7SyQjE9AMAS`K`v9_s0^9e%{??_W9&^T6MM7V7Mt"
    "YEV1v{E0<C1q41&(7Q5>Kx7(?C2$=k)|I<~Cv1N<Jh-_jBgr27as%*2I#rDTHaKZ#6gu?STI!FfUFwpMmCW@"
    "O@QJ9irkJTiNG=h%1k_wlWKF%(=7`8O%kT(_+C*8~lf|Pc?Qu<SQSf!!c&JU`{7zUuV+MTGxyCsDv~<pw<&r"
    "I5amL~BbgES}yv9|%+&RsJvD+glOBd_a)Rh02%uJ}XtZA>Bw(hu|yIq8`iVzMF{?5s0+Styoak?~)0a2{=_@"
    "2wsvSzT73Rm_+&6|TV4#sSugJE5xn=#|qg62WFcm>XR^fsA=Ya7*3^5}&LA2<Rh1bZ%MdnXWit?3BDw_OO}i"
    "Zl7kDTVd3_kW|dc=!Q>IcUM8o(xVs55E_^7S)4ISDuR1H||r{m~XALbo#Z{TnU{Z%ZfFoa_SDAhT*=Z+^GdF"
    "&TgzyN_!aYx26{Gflxg;kC+U#lpKz2=N9SEXbXPp1mMM$>&2W|*jm4u98R=ca)sfVznc;~R2}5GfQNV!VK!$"
    "D+8PX?AoG+!GDC|+v05yj!Ks9L06k`V)^=LlIyLJt8s3*s$G(&b6;kWyMoqJ;YgY|Is3vQot%d(*DKDF(4M>"
    "^;w&wce0y4~#J)Q^7B%&f6h50BZCGl2VnEh&Y-Va_8#~XCAOQvYz2%|7`9flW}qZbwVOK|7Lw8v<Viwxm4vf"
    "GeM&+#m2>hI?ZG8}VP)G_DSCN2Q<bEnygV%<V-H%J`}h^Rf^{_hnt+>;H0rXph+#7offOTqy2r#vz66KXW8g"
    "-3dlA*n_KL#wX!fZPx4X5i+S+oen2%sNpYKo-NWF?u+o9KZD*9w*97q$t)eB@+WpQot*Nb>t-#5IFX2UM#z)"
    "tWC^zY8fYrDI<!wKA5OFQgruD#b*^Q9OzsNr_-iwWn~{aG+lQH0X#+w$xul8YDvHgqly3@nTRQwL<c*A1L85"
    "N1?5RseL3!UobA(L_y`!1@6=@21qp=|PfW?7Q|+is=L;&@svD|Q1Or6zRp_VLEP9{D)>lJm4z&n7n0pXw@uG"
    "w7<Z(iI0J>$IjYKg3tW?D1(g`r{x<OhCLSAIOLfC4vm1>s0OSD2PY3T~j#YD}ak$uJr;mlaacuywTY4qbMaG"
    "g;-dJcJC)t%11HKRz#E){LUdYV0>lP)SnURkb15k#su>3oZz;3rz5JQWEXLnsRtq<i$@=;ccgswWrDmIc|@t"
    "<N`;A!^Q8OrRhMa7HYM40AMJ2JMC2b5eR%dN2uSD8H4;@#66K5LAwBjPA`UL|p;dQmObHT|u~dKv&qSTbM%|"
    "=zp218O!udQj8|q;Hnp5q6nNmLCXkKf;SM6IHE+8XmOpqC2uQarexz5%P%r(&fjp|*nzm<ct(%1D3(|vidaO"
    "eGH^Te;1PR}j7;fVz;GS3Sv%(H!~cAJbawcHSO9WPb5xK-6pHSnFeciQ4O~J_4s32P;@8d^%b6Bqb!km(vc?"
    "m*j}riHA^=Qep;;Z9@oX&m+^(onoakPZqRPN9F&b?aFJMC|auuD)kQ)So2=F*L>adT&1ZD78bFwes%%A>xVu"
    "Bs5%yFVdq6-gkN5V7iZjEf2>2z7HO1%cHXKJQCEght;0H5#RL$oJBu-d4kju5P7=yK3e`v;aYcPXFvL<cePM"
    "{c;WJy8~z;IF_Ig&b<JaE8OoUGtJrsEF>BF!kVT!>h?)Meq=mq|7?I*$)>Cc2EkeM2Aon^K`-|UsS5DljR*L"
    "_oSx86LVUp>3AmliCbeFGCI+-r1i@R(B{lJHrF&d7i=2(Sn8a_V}Xq8^AwTGg_Mn!`MPd5XIcr9$B3v^R+>p"
    "rz^JGxg~7FXQQ3Qjjc{N{3`Zo*ed>CJ$S5%(v=a&ulo9?ALLXC3$xF{bLliLs^8@-1%`z?toTV1P3xs)+GJt"
    "C%HR0#;JnN3lGK(6-S`qP}47TYwk<c2#-U<c_6pT=?<>@6g4)<D0xrV#drS70EkZSJjCW&XtHC?Yit?Sn-CV"
    "P-_1NeXOObzJ2P0~5!;obDvQ2T-4gxZOu8lq4O=;10~m595~idIPCo&+q^dV}6cPcgdO`9G&eCr-DJL!82e="
    "Gb^l_m6u(o_;%`n)OU9gcCX9=N%fK`{##7XrG2CMThV%`uJs8zJe1Iwx)oEBF^UNO~LzY@0%!|OcI0GG+WIv"
    "{*=%_fCAw3k}jx*#a9Hm$D9sZ<On##I^%PoBHJ<Jk<_<RAt_JZ93QKefo*BxR%6JU1|-3u4&l_4XA|b%4IbB"
    "SDZvffqU#uzCs<&@@|4x}qVAsK$WHzN?2@sgR+z2DRsn3s4GI#LwEyM;DC6Ml@D)lViKgNVO_JivXpgu7=}R"
    "0v{S|Z(V~I)|`-FBNN~cR^IxGfy!uSO24)TpkrjHqz>Kne!4r0fFFw@iFxQIy;B%9hzJQhU=SmE&Gbm*$QKO"
    "UXDI6C<WsI=?o<Uva6Yqmr049F_9QTqm2XXwl!rt&*sIe`ef%N@T0X|-KHzc*Z9)6ead5Bep=uR8y8BZeAgX"
    "3(nE8d|n0)7uu5LvPAmDMi`u4eRa*h5umzOp?be#a5;G`&Dy*QeD<GpB?MPDnIQ|xjtlc)5$ZK*s|66b8Sfa"
    "k16?9LSaCdkek_9YScgFBsB8oWYp0!0`c%`H#Xf5ZdSxi|B$v-{4|j0+2Mb@;e#QZCncG%Z-bgKH&P~gV{CK"
    "492>RXr}3Ht@UuWlY=^&1?rr}NFAS=3l&>NK(_SM;Lq>zG*=!ZLrOSuNat6DU5~%+WVdm=fEG_XpJb+r<*Wn"
    "@u=_-adV_Z|<PCos$O}sy+>Z&s!&H}k8bgG{5G143r5J6e(QKbp`Mk{~~{O*U_b5Af5-A$HG))Jhj=qzW_s!"
    "mT1-J|yoTON!Db(<#a>m3_IkFg0hVV#YdIJUsqSdZB?(|*UMR`;N17q=!a#&@n#USpRMBT}1O@A*>QT~Llt7"
    "|NVywnWzX{;R{a!PP9<WpbCrs${_Gd@egAGr-GqT%-hN3H8@$Q9E~hlQZ@RnWU}%ic;PA5K7#`Im))Io>UNm"
    "1M3;L_X}Jf2CYSaB%9AXOU#LuUBx_IVkV{#aNZ1ca_U7ADKd8RCs;39NUCJ%INCUcfh!)+nhLSdahBcHrQJ5"
    "}36b2;s8Y&Obuj<GxEI9JF?lCwTc8biN$5~+CV<%GIZnlQ@KEO$g7D0WamTeGnG6*?t#_(n_QJK+#oBWwMgG"
    "2)M?)yMnm{C&VwO>N*4rjK>>H&?(`fs)jat>@B3K<V16IDws<=5S>pHYX_2ZMwqC9bQP6vZgTN!4CI>L-YTB"
    "qd0k!1Z<CZOPGC-V&Z+LrGvBI%&^CZQS$(RJOdnj>tJS#TDTTgt_#j1nzov-BpFZ2fBnxJ<d^Cb36`*%TpaY"
    "Z#7~24Y~f%s~gjZ8N+7@*%4%Z~36Sg@Zv($`u=e6Vb3`ynmDD!1D~$j=8qO)+|%$q8(4oacoppssgZVnMXq!"
    "H`-*H4<WVo+_pSDHTrWkrlKiKf;pixxW~sxc(D*Ba>18nzEzw^C5W+R=0rH>$Hv)sXo^+X56OR2IEX7;Ct)e"
    "f>?#~q!6HEoyQLAyzNg*Knxo|CP-8A%7G4sN*d$9T(mLFp%5abRIoHYxZ?=tBWp%j0fCP7hcPCopz-g|@>jK"
    "=VL?BFJ-T#fTBd&^Hf$;re@gvrfw>^VeXNChURc#h%vP|Nh!@uCB^Q-O(W&Y+_{f-Y`UPNRK+-x?K=++al1P"
    "<1Abd6<jjdie@bv9ZFw`4E-R<M2azU{Faa_v2eC7_|L#uBEcn#Wog=myFbBS7%s1JVwwl6tb4UhR+txNaTA+"
    "GQnbGL|h*I=D6r;A}(U%!Asy4UPnJe~pYGP)=?73op4jYRAUcT365;7QqB~hb072!cvcK7-MTYLIK}lj!BMT"
    "I?sr=)~eK~*Uem~ENh@k6Q#!v*>Jm5U<gjQi~}S}?=`4)2?Ltno1Fdh%g|^r&fLizpQdoezO@d^jl^5yF5y7"
    "&_BP2(rmavylVz<KX{-2(aMctn-74*AGpBd+RqBklg{<9YkZavkbtYZWaU0d2PSlv&!b{u^G~SfyvL@vvut6"
    "O$7P#4fS-C}i%x7d;HBZxTnw15d>fqw&m%}<ihr^N|5x(undW_y)=id8^i0npz?Wi5z@&tNmTV3ZOt+wMu(E"
    "28~x)V_DTLXC$X2(WfY{wx*>zu8{$`WXHI-N!%`}oMBZPY+MDvZww%1Dh}XG#c2V<XdpFeO+Zsban`Mp}e#g"
    "d;W|usb#m8i57qP;qej>NSSdy?FNH@#(=|;a@JELy(Yuazs4Qszo#P&T+^~Ux3aOM9w|P1X#RvUu#9dtXe`<"
    "Bmflzk}yQ6|BBCJq!Dpu6mwbwVtkwND5GUcXPN~@kdEvoqaaiP1|o%QPL+2`7Q*7AV9EN_Gi$Zhfj3fFs5X^"
    "rXMrX*X?yyZB;%Aku{x4ULX?&LS$>^^#(@zdG=9cptzk?(&hOv6rEA)L<Nn^-Rj<(;zJ-DjW=KJ7><wBI&?;"
    "fJPCfX&$+P8{evD`Kz+BsEM|XU1658O-F@mT60OM<&ZHc3r$HhC>*7}6jPLO+6Wz`z$m^aDL?SqE+TihaojL"
    "CtYr5c%x)vQoQ3sm1i^L+@GTcAXIzlotyN+xH+pFTO}^0sMd3whdkX00&Rz%Nymd30*q%NL0sT<8oID<9GX5"
    "rZ6E?z}iX0r57nQHRP=){Kd3u;SZihX<#>0PVhjCfx1p?84i)m~`I}?2*DC2I8UC?<f(PfrBv0PE$p|7nBr="
    "?2%x7dkIK&v{8h%AJfmr2zLrc35D)BgIKE^tm7BXxB|!;azq&h)LdUOhke1cS7&f4e_QniU-=o0MBS`N8Rg-"
    "Qa6^N55`F>&qJ;uI&gk?ndwSnv-sNq6S7NRV1@(w)01suOW;{_hL&j8TWf|JSfPLvs8=2=1>`Jlw6uA+z40<"
    "(jq>oodjZjw?3wW9WaEu3l{5f;NxHXN!_MI>CC3{blrDJl*cDDHfr{I4{Od8xVJN5~a#S;c^@Jwbk{DxLlv9"
    "Cx&;F}d`_%<Am#>IHaf=Uy2Ro@aGQo-XkgAL6OZ3EY`NqQ36n?*MQ+SfWI2BFqTBqE3BcuB53vlR{%Z_$aQk"
    "0Xg=uyL}IQN-B1iuJ~3WlBI&zbkpZk`K#<fPIurooE*SGew<Nky0qp$Aa@RIIgc!6Iu-$<D3e>oD}B3wS)f1"
    "*v2v0r<b<~l6$XF|1n|J<<|_p^4n~TW@xE8X$B~=i6EsVTT!h-f>qa9L#?qO^wgsQ%04Tw>~jLlzF=h67mM)"
    "vB2ZNUGeEnZQd%|_lR)flx0J*_9UG(nbAEdA?Bev*@v~Q;>P}D>6VyshU57*DeT4U=7*5gqL<DInxTQbx()@"
    "{>6FVo(Vea27z1Fr~V<AMov%II>EI0PEdnY!I#xkUix3Gmiy+}aJai4L+!#e-3q=aLFV;rrr^dBo^V%IbB97"
    "@MJ(X_nJ#vSBZa1tNoWe@l#rlgKWJ(n*~`53OT*xOu-UQ<4?ekv(Z%lTqR<zWZr)6fh8DKA=!BAKQi2Gh%(-"
    "beZjK1i-hU~E&o1$UqUyZ|2_I9*YAzWD+g##w3UhxCqzy+fw~7~*t-`hCmk-{sET_2mvZ<N0dEAkP=Md|L}A"
    "z8$<jovq5-R^=Xk5GT2%4`G$syyX`1veS+O=+JD-Z90+7+)=<2TJc)T^w@b<s^O|FR9VcW8L4yV)`<jSyQ<P"
    "pjpjOTeMT*oNcf=Ha`3!UtxTwKfCDr*^{9whLId`@M<veO?%@S%rCQ%1d^XfH_7T|UeAap&&sIqv2dG`8kWL"
    "_#-5`eeA)Xyc;HPt{*hQ>C3c`-xVG$T%ACpx<0hgmROP7_Mf;oPrA_j9GIyBvG(IqOk*=KDBx^d-*HCkc<T9"
    "y0D)nb;|wW>ZF7e#zOY<h$BDSWN^9&bCU--HtYVw>m434#Uz3u}rQWXT-GEDffIzx-06^<k$3kzO6OKRlJsE"
    "%S|PZ9A%ARcjT8B-P8YUtE^hd*<!#RrAN)`P!xnWfEwF)=%HY_zs@UhmX+E16Exn3LGNYQjgjXo|C0Ev$A}Z"
    "h#B`IRR3|!eWw#|sTWu4pSRnDXO$Pf-PB3S4D(2>Qg)A`xp*-2{H93@jA!kbWKdU|-`YGf(JH(OoK)<`Es{%"
    "ZB3bhVr+{P+LD&~9tkx+__!&HQ>1o4w&za<m%0tAaDqJbZNzioP?gz$#k&RqCkDk<ec~h!2ypA`uFw8xg0!x"
    "QUs<({g6L}nK+Mqod>eX9hEjWIZu{_h&t>Mv*Gh@+}sbyD=;{^eg*v=S%iBk*zqYqr_|90&CCzm@<I?)rp{K"
    "VHQr*QM5v<^G;Nu!3z@qbh`!cj9%;pB>k!A^93`YZfbN?b8AyHPpeK=601A@W)JWwQ?1P~C%T+Gxv;2<<rfL"
    "B|os4ee09Qqz!(x)YtzaAEKW^o~}I)9J5y@y-Jn!^(I$ztEC@`?iG=&uuKDDvhv8Vzm@fbA4;T8MUr~xH84j"
    "uSXX@pT4;;g?Sv<mR~5o+a$Op;^Bd_O)_SK0m^p75=rJ***^O9mI9OUGm14Y&B}S2t!0TxlI<9DeRt6p_aiE"
    "-w#?NsEs6xWQ_vKaIp=e&!d{|P4g(($_y-LPrW$;S3gnV-EEX}D{3uWzzN<*|#)7<{d|z_fQ1!)VKawbSad#"
    "yXw4Puv52mfH;KVv3vps^jmrnk>WRV#22)WP#_5<p9zqW8F5?xb)kb+by?l)Ke)(5#{E<Vx1KjBEgueP_;Lf"
    "r@~RT}x)gDn|A)&)lZUhaGqebgSnS$>v0c;+-5cE@|ZOJMgS^HMr_7}cMl$_VabbRqO4L0-8}(uJWKCMvH~`"
    "UBnnDteKWL?ZNwbx-RTCj7#X%QviVe1D99m9g>jmg_$7^eqkPBRvTdNqnDOu|VDW`Pei$<R-5+^Z{9K(`T=o"
    "we2zBL5q7a`dFgj31%>A(Vx5o?S90+#&AN^K9+1`LS}V^&eFHoK!!g1ovXI{g}Q1(+u<!bdG=qtI_%9S<SML"
    "d9%Yp(E8lhNwNjH)3|qP@pXo4UCt>4_dkG)??e>w1RP3G=0m28348UMkJ?%YS9yFLZ1XTgpG^1h(=j{RU7lf"
    "3><&1x@f&1vLM=|?8@y>3O6rn7*2rh-)Vo`M~`+**wS>{#JPrK9Y!l40z?K5PY3`#*BY&&q8^3J-pN6(yQ+w"
    "}=%-NTz-zSI{vU7bM3Lf}U8HVs;I8~TNMIsbM@PruhpVu7-<WC8fh&(9~-?Qi#%zX9F`BPqX<35uLX8-o9Wm"
    "!XNLPya(oj`p8EHSK5_(#N;<0_)XQTARqV$G5gG^nQ=cjkG=81@}$TWUHnnpMRPAZS!T&^tW&Gs-DK&Zq&zb"
    "L1|iEC-Kr%$A8v~eVYtM!LJ$N1yO>TU!pfEL4(3SrI;fy8qyZ`Bl7{pb9FK8DNVGmnx~7uFF9;l4+uYgnW<Z"
    "p(;hlDD8Ur=qY6gYT^qS{a(cm^7W|~_p1OC5C4@maD+wrIsS4xk)r`@B@M>Pz8*ZK$YHu*E+4A;2x?DZqMYI"
    "U4Amm`l*(zZuD@%(8#PxXZa%cK<@=(WBpg>H}q#9ZnSW_;k0&X`l3nPi2T=yw0C^~|LCVRG)oWF--=Vzi3Ra"
    "q}bpe9dl1XGq_KJlk1d}Q*oaE^YEm}gpca)_CQA-FjSD3;_#I5|7(m>OUyU^Vl&#8kp~g3)gjC_GQ3C@A$h0"
    "nQ_U!c@+b^lq*LdmFz`scv1@IPh>(W~~^k6g_zuO$W_UG}nrb?1uL6IG>UG1Vh87j1FB})w`G~gB@L*A0EG?"
    "Lk1PUp{a;kqiS^X0zc2m;gqxd$F?9*nFL`I+J?sml&>s=C`JjRYp8ij62wn*A}us1G=&aETuhi>Mgm$bDRAh"
    "H(1Ee6?K`x$#{yjCj^zo>zE)kL?L!sC@wD?7m<>FE-5~Cf&Gp2GL3f)k2+kF&KvTIk1R~0(5m&Z?NyJ*KW7+"
    "0(ev<l+=a|--$;zV_mY}al8JxIv!!>u&WeJAH$g2vAZ~F2B&ENiy=Z7Z;ht!Y2>rC-f8#(72I44S~&^ew?R&"
    "MBGp%M6#1kLYvxCeN@OG46kg;`Zo9;VA-dYt<V3xy{$DaI`LU0m6ff>Gy0N}o_k^>fRhHkvTj6(|k9;4?h2S"
    "UA@RN2d>(Ay+*v&H7{M@Dk%b2`q=hzObS%Q!Q8R#%~o!%L_@-hN*gS_;UZv@x}1`V*mJXxc~Cv@N9T~cyN01"
    ";vBTdKkn{sRiMzY$a9Y6t3ncD$tlam@IhPuk9lpRi<>U_<X<dZdlTUn@Dt==iK4GCHv5=Dv!j2Z`yK}%f1jK"
    "Ve>~j3I9J6OKR?8;YS5v;IaTkvh10x8%6wIfllrT$XhWInKHDJu*Km1;gd}SpBg|h>*b}zTw$M6JF`sIZ4Z?"
    "@%+zbZZ;HqgiYPHlS`nWZ%DnL<I3<Bq7tfNeEqjV(5n?CGLO)adHo^WO$oEb|T1#O?z_QH8Zq)^ndZ$Vol5~"
    "6W@tTY9xAF~X;!D~f%MEERz{-K_Sfm(QV0R7(X^ntJm+^5?c)<cLeyckot4+nD`*#qXm%SP4i)@kISY`Yzhr"
    "s`8dByU>ADjaAOT+=KU2DjY0o<CxBKvrPx;8=|TaBgh?5kMS|1iXBCTbV9vK*h#}h5}o_-TEFo>v%g0XLCGD"
    "(UTpjk-U&H?KQ1f%4nLZf~kdB+((3J7>gwJP<6sMptaFfSuJq$lZ{$nMYUj{L<GPkJj;SaWOY#B8(A}F%i?@"
    "R?L|VcWrA@qpxP$0P`r}Ruba`tnv<Jx53|;rT=$$9Uhlvyw;!3=bZeE`mh?gwqq+WIIDe@2x`?=NO~QJ3jJ$"
    "8@#`JB-VS+7%2d`641A~PLT_e~e%6y&BIztVNW8v-+Wjsh`e_w&t!Zv1`w{7-xubwTi&GMMwvo$NhVQF^R{J"
    "_fS^z6mqS@h%I+&5kvo*#4!jp488_~_NqMYN|cKOXU~GHDeW6UI1jrBsDnT)sWPZ#3SIm!bPSGod>UCl9_@r"
    "<FnATAfU(N0d;wHa5&oyfv(1&;<xHvmv6cw$|<~K?9xXS9SW0WO1|`#G-|E{xk>;K^>){{&*X!d98Gv<X>mZ"
    "-tzFkbbor0fZj66m|W;IUL}D}qaPLUJ7=-rZy$B-5$m+Z$g*56hQu_<cjU&`MVO61Z2ISmi`P`k7?1lAhh@?"
    "EMEvOE*=hnJ@5RY^2lw8D%F|-m4a^q8m{!g+xgbavTialKn}UERBw>cHUQW>KiC^nQ2Sq}`mGKPD&P85gn%X"
    "4II$HBSE^gj;qFH`Za_IoXU`Pq6K{`rS>R$BMbT-oxi6Azy=Yml`M$;n#OI}lqJ7x1O(IPpEk|{#_n!FMAS1"
    "3{jg7A}Nq<Ek53G>q&zNnCV_f0sya854YdaxnJmd7*u(^Sp2m+tM~s{+P;-IJnI{zaLk?T>X0;fs8<8J^^43"
    "7ZgF{s(%voO<tPijFH(Fthr@w}$e(v;R;<Lj>-BNPO3HA%CDtf|2{8d3hrVQbKt02uLL8hf__uY8tmG_^0QG"
    "I6*Dc>$ooha6KUnW1E8=4Y9;va=((asYi`FLE<=F&CeaNcDI5?=tO|ZsR^@TEaNuAw(eL8HVZwATsdDY^$<3"
    "Q_I5j3SL#DLU(JW~9aRpVfA@U2_sus7W>_1gz~&&Wf)0ZzfgrEt8*R;p+>QRE-$mxU_k36H?BQ?k!}P##_nY"
    "sB-~Qpd+B*G$F(JBC1a$~Il30^rMXcfiE6d2>%8}7VPn4L(CimILswN04f_`iGr&GO!tAh7V1jL{HK&6A@$-"
    "BFE{oOa>LL;9JTKLJIR%=n#5gSz&inaY7Y7fd};)C*M?Gc$&e8ihy=fMZhQG*dsNv1)cHsUh+^S0~ZiU@Pa!"
    "jDGRs0&(UJ;~muMb5cDUcdm_tNI)p<j1G6ON;}a(1~33qz(0}`9Mw>feep*yxc)N9gZ0~|J(V+;j6RL(+l~1"
    "empz?Er0m(2=xK)(u<?B%bf==ZorQ)X0bJJm@k5}Rozg)hed~F8|LLscg|m`TC;o+Tu&uPv&CvTsIE;-Z<_!"
    "m44gi_K6-sve+XoO`_PNSUof+-@|@7sAWUB{`vYecD|gAEKX{1|Y0Wjsa0Yv<e-SSaA){EfOtfVth+veRUCp"
    "W-vL)TvI8SAZKf?1;j|;TSti>;T;I+=~l?`hiLQYPPC_pHS0#oUZihMdVe8F>g$Qe_$O{BNop&E83X;wd|${"
    "}uLwGgkecNyaK??`b;Yf_SK*d5x5{+iq$R;rCw=Q+(7=dm*1JoL&}OpN0k4tOn+52*o7^Y=@+NXGus;NBo@u"
    "6MlxO{?gkn$=QH^M|%iEw^zQFPBA&bsyS6aK1p=ETB^r+Clhq)LSXPzHqcXL6aoYhfZ)WdVP9+^q)+R1)2LW"
    "3ai?p^<znpL|0OL8B%-}7ZibtS}<Oa!0{L{WA8}v_bS_v2GZkyWLUlPqo4MV&t7#R`+NA}<#9Xws!o8ueROg"
    "33Xbk)hx^AJn(()dpty1xAwf0JM_7zqc>zK<Ire@~(Gz=THT6u__N_?DD&NA!2ipip*<vIhD{Y7<9LRT!kh}"
    "`>mU<axvJF*+a=n7(9%6b3OrWc|w%a{Q8marTbzVA#H`XS(lI9eVpNCbEK%6ukjRxik-T~645#LwQ@1wmyD7"
    "1)cYy(Af?X`ZmX05Qk=k>cL(bV)ucwttlUhJMINV6y2(NxM<)5c}6{1&b?T(TA*PE^43I7cn}XxVY!w4>a&U"
    ")Qc^E{t~d5Qqfd^;n~Dy-tuvcA|^>MN(szX8Pz52fUB6kl>g{7VaUj!r{;uxtYD5-(v>U;fHkD5?<MS7*8i&"
    "hTA!C---jY%c1gUdZyDc26>j&6^H@blem~fut-IW5CWfeG%b@cjJC<4_vYfD<9YR16o_$_duTI!supT4-xiH"
    "V{NV6!@V{5DUc9*Y`R7-!&d>jA_(A?x$+=M%i7_vstq8h8q54z20wU~pfBW71caw|X{rtOEzdQdgqa#>9gXS"
    "6x#peP4@>qM6jXAtcKD55UOb$CP$1e3}^Yze>&}4pxbu6G)cFBBeCqG#mLo-Q~`HTU89m05-uZr$s7E{iG+>"
    "aP~yh94`MEr#uQQ#K+=+2V&$;`!8CezGIjOZgu#iR3*eg0!>f)Ph#o?{J+0;2_{<ZfR^8UR&-FpU|P55p$4x"
    "X4^$hcMIt12gb36NaH(r_5)`=(d=}9N<C0FxQDKx%`7$7tz64<x(Hhgiu6ae@7*B`8xmbsh;j}4qAjncgNRb"
    "eH4LGa8qt?IN3HM6a^7dN28yd_^0`dAO~(`pm>e6;u-LXdK~kJ>o%^zZ#!2fs3ECcWs5H#=_0=-^6WbyvqWw"
    "~3<oUXC`;*V9MjnA^)SX&4|YP2Lxh<{2QqyHG$2i?GZ*v)OSi<Jw|WOwHOHJ~BJpirfG?!mK5wmE21RO!RMB"
    "D!m(7kO7K4Ad$4ww(I%q(vlokszI-k9-VvEMveMN6^UgStu`({LG_1+aYGMg79^R}#~e^Kxzg-*<-z3M7DDp"
    "}aiYd+xH_<BROw*mjQO;TzwX#M7$cEdypdB|KMk%VLq;~rp?6+w6n=)qpWSzebrJ<KLT3Mi`P1p5ve70}`ke"
    "#^^nqEUHt`w*TH+kE4cNHaJe*iyqRSeloKU~@`%A{;XbeXO=&!hJP(_kmv8Ca|NDogL~ZZkR`OF>~n6-Et(4"
    "yg~Ro`0*pa_kw*#n0Qp&WU~tN14*U65eIMIUUA-D#qvr+6Xs@_F!Q*6y?{}USSj8oY5^tQ-Bx>31cdX|Rwzb"
    "S{RiO)-oulZr)LL<TZJp)^imvZZ%+1q**`ko|MB>+p#=?-q$=;w<A%qycI0)!l_MriU(9k=1zZuo7I$)+N$}"
    "Xt`gsW67B)KRQd9&{A|^OA#Z-U9(_4^*wjYSaw#xQrkIC|lPZ*F}Chif#@mL;=1^<Py{J>!!v}6edHd7e$9k"
    "l$}!*rC?Pa7)h%hyHzj;bSVJ=QAIgyG`9G+Z)Pqf(0}J`)_v8v19Cm>ArrjTJh4-$fXZE)BG)N42qfytVzH+"
    "EOR7kGRYkp5ULG0AcyZzvKBn9b?>eKCygPS+iAD5iI2T@5$K1k6@*_X4VV?Ytso3+j}6VE?4vYD6L{N9EazU"
    "_pgrX4D%ZkHkmnd$r+6DsxVlJb2beXq3xEc+j8+(oRoMLYPTA|Z3{Wsuhm||u(`>^>%P?f(#j^04we@>qGY@"
    "rA?3(nPJlQQfqbYn@8DOPKJc2v{<dvCz0SvrAv@ju$O84=vH2BE!FlxR;I%mDLCB_A#yPFP>z6qk#iHlC&%f"
    ">Ne%Iamo(`<XIaM-RV3tB&bb()?P?(Tco_uF;jO+n*kTJUxonn4W2kSp9C>nrj5?_~N(BmX&8>7UfMx-<n-4"
    "t=Ql(Y})$|0sE)bj)Nx|%op=?BjZP($z;N)&rcJOJBh^tfqHsTWut>N+03LsQo_E`Av40WFW?ydMtH={p=&o"
    "%Sx&^L!p-Z5{)I;%1Awp)Sl)sz)ieQla%ZRlVKLQ#Bv=x1Hty0MIb<lCX%Pe?uD{=0borp&n}Ke1j|dyWODQ"
    "%5#enfp_eF6w1<uIY@^0g0@_9TN_=~a9#SP&krm&R%5jPT8U<F<Uj+pftp+Fet{bmb1dD|bQ#an`8r@Am(kR"
    "njcK;oA^GLJmh1hJR04L0Hp&v3fDOlauR%A08{Dnmq~X|zZs)Q$<3LV8y2EP(*TY=RdK(5CsuPiyw7vby@TE"
    "0x*PS1@IW?%f2>NeW`rvaZ9Ycevz{jvVfzA%ZoPWXCD^Bvi+_8*0*qCT-@glxXXYkpCEc~@N2j@{@I!D<wrw"
    "3VK<4;wjW_O7xc3c?*?!I?>wRgD_`ou#sI-TO6z})n15}3I9aNEo^+z}(MFe;j!UTquMrl|mx>Y>u5fHx<=X"
    ";zsega9i+p(LZH#34oyBlB%!K6hV3+2I3mS;tdkBA^uCVlkFw?(On4i`qsPVY~)?qkLw`Y7(A(GJ(%?cq`A+"
    "F@f!bLk?;nM_h2KO4>Z{&qRNRnXE6Tyecb-7@h~KqRa!H<c4`x8q;7xVb>VruAF?8E#ez=4<~Fghh8pglg(C"
    ")L8U`NIQ4$FLIoU_E=mu*Dkwbx2WCMoLsrkDKSy6b4?a`3A~t-@0sjg=FEX?8iq1Q2;Wi2H4euk=m%eZne$="
    "(R@dVZ$Yk$(7(trruPqdIsS)pw+NlSt#Cfnjizt{B+KGf;boTE%b#9i#7ZP(?=iVyCI?KGWEEA?N<2l``NCW"
    "rK=UzN}difWZtp$_Szu6>L-23yDAOC|8)D)wN<gj|ST7E;C<rLKFlyYr*><a-^~f#4vXap;i+t^l5L?ICzM6"
    "AsN$h}(C=ufP9hvoeP>x=o0ii90a*dQVaj&*cJ_gw)&hsi(`p*KY6(Sp<}bj??zxFNY@=!(Y#iE)FY8#rWPZ"
    "%6>400QZ;q82{0l#~)g|cDbT%jY+rLP2mNhfF_(XE)-xQB?22BpIB18BT#`D6l1O8gbNqi4oDsF-?!3U|H`9"
    "N%rZ{jCqk+riu9>=Gi`dR-*39)C=+XIj)*hCC0B~~%;&7^|Nl!0COCH;HH>dp**m5M4vSf<27j~r$M4#WgQB"
    "+9_R_|`VF&eqHX~3i#?6v016?HXJlJFRF!lQZf3z`d$9WjJ&v)Mrzy12VwOtHwA?ed5HiQe;shstkU%e8f#j"
    ">U3(($5=gtz*kd)Q#Ta;hWc4M!&3fb-Vriim!rM5^+PdgNx_>xyDK`s{r&g9B+L7L?o|@>Q1ssGg{z3iVd8D"
    "<a6nybMC-Hu41ja1G18=Y-kmrWu5kT=)E5^+yHN??%--CAHh@hp&<IUwDlNh}Zb92fML@M_^Q0hJ<VsXE#Y}"
    "@4M<&x74A2G-j^aYF&l39b^1GejiWNJQ8JAszU@AL!N=Iyh<=A^G8v(y(5RBKS}bS?q(#;Vx{nmTd3A(DQo$"
    "3i#=?&)yS8+7`l$iD(}4I=dX~&z2ynMbh*PBI_|uDlD_IHC>$kCj(*)PidK&Y!Z|@6OlsWBL{j^sH!;Aq*{f"
    "`Sey|ytck|W`eMieS@!f306u2ZIOc5yJHl{+plGCF+0ZUZAOR5fO&?k$V6&3M#98U<jt;IYSNh*Wy(l*+DkO"
    "jU*8$DU8-0|s4_cr>8Ox3LJ8_cH=R}7w)$Lxo5Z7ZB}ak*or0WX>#58f2=DZzj<RJ8i92n0tqA_lJC##~qQo"
    "n`<QN%ljO2+jq28WQ8?hLPo~1&*w@&e8>{0!Do=DmJqPWeJ;r>c1WxAJ>mT5|4JA=kHdF!$278f?~Nsw$a{Q"
    "4B}Hmg1-%bAb1*V=#1s7xU~~kpdGYsuWtwyB-4^>t;g!x#c*gBt7_D*kV@t459@9H?@~1MBkz3c9W6B^!g*B"
    "ikiEz1Pc79)(f8dI{*xi9^N+7h-YJHFbt7))RJjGX8N$V~x99%40OrKcQhDt(d5^`tP}}E71j5FI9i7mgguP"
    "iLU!=%{mjqfQzaavT0V$Igw2aSYz#aqCV-iB{5Ui`^qx`Ekr|(6<Vsu=AwGy%k)_?&4_%`nTbGQ4)tKTC#BJ"
    "h8Su5!WuhvU3NIG9;7U25PU9pN~t22O|R&28uob%lQSy|g!M$QWDb<@WkyHv|m3=kj_?7RmfNnPBoq8O>Kz-"
    "59Ge|6>JoGJ$!|N?PU}8#<U%`bduIIHgaP|0qB&UCmn`qNmXZ(!M?rKsk1;4cFE_#eMc;o!xCJZ*Va1hfai*"
    "@S=aF3mUo17un)4+nv*yqGw(=F@wYTNwGM)y<M+X+J;EbS2R^Wr)KgePFN{wc7C8KZ6i6GYjL0tSU}UeRwi>"
    "0eCgP`NN8f?d+!>PEACY9@_SHS*c$GBS{faCH5YBx?i`o9kO}sxUP&@7jntHGtdFpg;#=ti!5S=9*RynNJSe"
    "s9qcg9ku1!OJ0iq8k0$UV@8kCcLu*z3`Rhj*xG$t2iMIEIBr^}Sq>pj%6Ll(!Y441?Dpb7gxk34rJ^4pe_Yw"
    "DvaF0{9Pr^^16j&_`82~y4JBL#7gBI@JHtihCdJe~}7hx|O%r>J7K>84pwzsI(_KKjh|6|T1`Y;EYb6F!2~o"
    "vZji$0}>O-$tS_zr0XJVj%$l5`RMkZaR}tzu9ttU0{7p>PCA_1?yT&lEGy{snod3NeG0tvqG)9_vqo_qxUHl"
    "snK+N-R&@-O}my`HyqasH<dFRW#3c#_{a0z_4|k?L!KuQcb&lhE$<K{ZI5>C^IfxXc(kMlkTSK5X#k=c(A{>"
    "2%FwxMB&<o}z5PNr&R7BxU-b*G0L~}Yw9`E*_3Ru@HHe-tpL!CVp7}Q_B^am5s6HCpU3j3m5My(hJDM^(cNh"
    "^bKsv&Ecdp!AH<6JM>oU$dME@^0g@PRoyL+A56aSJY+Aadln3WWo^Oj==l#+2u(9{iqMXFrqo!;_-Sy;Z-5$"
    "sg8t8AB!bcDW8xmSyimOlF`N<9bN%oGSx3G0wv!FH%d_Nd{>N9LKt_a!NCA1cFu&r-=1Cj9PW5Rqz#N3dSsf"
    "A`I9cpReXAd&|>*V>DIZ#(uZ`g+$LvK4g$Rw3m3_J*G+ObQsO8DD=3dqd~z_j<w17hc)JE7}`#!D-qwdrKiH"
    "W;<8&i4A>|{j8315Fr2RGuZDcTo!k}`lO7YQ#CfxFsdjFO=8FP$#R51w=Q>9CaV20B#e<A@%uRCq_drHz>;N"
    "}rrOmlvPy2K<8N$s?<AAY<*)2&vY)1|i-Utc(2o8j66`W_P2<yOJ})R7pdUTz>yB)b2b@EtX+NdV7h=oa{x@"
    "dr%Djj%j^`xc+kp|x;({A&2#!#`MSlOiE5onCPh(UOKj^G>_)#JOoKt$?`BeiO*Si50-Vgy%ohfY0{O&k|4q"
    "IYdyS+cq4(Cd2J!TeNnDFO#*=b3iNGENV3hpq%w~!B88tPy*vH_5XANxpaqomERhN&NcGTtZtBhqCSVbYyyw"
    "ieTCv!#g29bhwFX(-sPbSJ_)KlrHg6N>8@FF83o#!B9>TMmwoB*NR)iT;ANqEE*1>Yx>rg4;|t7WWh8@A4Gd"
    ">R#b!JJCU&P1Bnfh=~`yM9|Jg!;+6}6B%2UV2@p9uZ$bXx2e04#}|1%!#t~&>4KiZcwNTS9caS#tCf6!uMRG"
    "EV4bf~l=$Wi&jJB2(jZ#%G#kQhx>?>1U|#`Y>aXX!DoKrpVDn3RyStRyiI8%G;&SKzqH$}#`(L}=KMuQBzyE"
    ")Xw%q7y*v_niQ*dE3AY3~GSE1Qa#d<a~iMBeWwPahaqQa$#4G`F_YX=s`kYhux`RmwE(~s=peuN`LK9jIbBz"
    ";ni*o$dIxwtar_e0$X&O-<}tlqLOV@OYMiJZ5O2xMhPDuI0mPrZ_OgOTzy0<8tMCc@P|;sveJH-g?3=lo0$n"
    "Vaok;A$XaCuh8Jo7PE_(Nut=;!|@1{gI+t$`4$uzHvSW;_*&T6&HXIho0Sp0KE8oPMB`G{j@QZ-~9^gvO1x<"
    "?f|<hkicuB<74d^mm#1ZZ68G$b2!o^rTrT2^~~g=pl=lzH0F~`6UtIqkxMV;hbgPX;p#3-AbsBZmO8ReLAdQ"
    "7b#ab?)hq0#R1!Iz&Ek0+#f+pdqvRI>BeFH_v&kZdd3eVBa8(#^1(PO&mBl8#NC9t31xEtXxkK2H7;$imq^R"
    "c6M+68>01liu9i7E@#?^eCPf}6;664Hyb9T&75t){bK;E=SDUlkQV=x0LOA$|~IEM9S(%A_}8S`||{D+v)Bx"
    "%`^SOJNCOhO7;aE6MtNDLBXRR7sCnp8?3-`o4<>u;XD-}81iecrzGkGmxM+It{gq*zbOWxNe^4F^8h>sZq{n"
    "ZnF3UBrCf{u6R-k(?DAo<&?(rwv@Aa2{99q6a37<|MH`GJgLwT<wxNsXtO@D6$(%q2XV%{7wVEC+SKs?QYYX"
    "Te%v4xZHWz9MI#&tDCQ*s!ydCYq>AA4i0L4_6F3dx^QtGKux_(tOx!huf2=_{wfXdU&Wv;uOoH%Ipp$;+=ml"
    "hvF<)Pl2Ji#x=-iArkm3uzL|U0_V)H+Q@nW+;Sk>RVwSZxI|JPmVves2-kCkKWq1nrp8uf-C$8Qe|LphowxR"
    "?9xAVJLYG6Ha!SgynC>=|5+nhC1jzxlPh&fI2gvD!kMlt8|sO(oSlHq@$d|OBL&FHK(B6ITEcI!7O9ID!>=3"
    "pocgsMIr{mJzKZ9%$Jmk3b-m@vqYP=>SPOvQUw;jCh!Vk<_+WE!YFBdg1ybNqKbRae45`%x9-(txkZkOhC$p"
    "NBf0YcePCyeddR+^vJO%HoEAEo9_xP38z{zLgvZ)t+lC)G<3XHd|w|^o3x1j*U+MY)S7wV0FHGVYFulT;Lg("
    "4Gie|Buj%}fY2+cb|=+-s7q7Oq)2y>(jNH!gX<Wp2Mw9PxIxsM9p^C{s#*PPd>f;ZMZAI?`vC==&<`D*UZ%9"
    "&1mNnT9m>BA8B@*3to7);3Z5T2Tj4O<7?<ZL$5Yudj0XC#($GUKL{ESvT^E7ALfCwp0tfN^O<{vh_q2Cr4b>"
    "@y#mFcfzShI>ZJv(N#I#b21AJ2A8|5C!2j?<9`Dy7`=4<N{vg9!eKiLaD6>j(K?p0&@RsE%v6Oz4cWT`jVxi"
    "NL|_en9}dF0s+GiE#O(IB!tZ;B-5CuHt55O#CSsULFw80yhaZzdi>Ep~c`^0d4iG7rRHcB>VY%UpCy*Cg@qN"
    "mQL?s*`XeuZ5+rbgmk%D<}<*+)LEFRHI`PT|E+)uG5*q|E4?GPW1L_i%?-{O7@6u33HwE6t^3J=3a_D7W&d9"
    "TS#0K@%<X&#QqxpX8lXX^w?m@pA00`uUh%T;|!oR>vPsDbY&9+8{RV(pn=0xgY7tmq^po%X@{*vY5+GgzE+%"
    "wU9Pt9#(vlMJf4MV2gwx=2e=kQ#9B1zj05H|=0hrSje@n2$V^BLg(9jhTUTJ|mMW^d+tHkVxYEI4NJA6jk}v"
    "!@pdPC{K!SV>;mfg!@_=mdlVl<ab5kh2IY8JMqEC0EkM%I=4T!l%u>C%)LC;;=ed{4`^A!YP9j!?Q^WDWDU+"
    "1jxfOKC-o#5B%(vXs}z333#1YCHGtySzVm?T;6Q_EvEMBdWvBwNk(*7>qHgrDo6S3b!PbAIsi;j8`OFNbI6N"
    "2ezdsTI}+c}`vsHt~LjJ4Ic|XfcR~f;FJ-0>20D*QE$N)qQWt1n9?KpPjx28hb(fLVu_NzkhIX^vfX^e4;<~"
    "27Kh`<=>7@exiHkmwoTx@b!f>sz3DRkH@D6f0cXkx88cWe{?K&_)ooYuzzxJc&zu#FW=C6p5FzB_~LB;<psS"
    "+e`%YT#`!n8On;fapPwK7bfSHiALgAmCnq{;`P(-4%hBPl(jNY~)npv}ynpi3;ra0F@IT%hp6gS!tDib|c5?"
    "QO<1;u%2QUZb>-_f?V?H>2_4@eGyr;i5E@#6q9CrbWx?opNWR_3t6dxS#AHC9E@ZWmt#pwwXF#cgK!h-Wf_{"
    "0D5Sw0Kwk)xA?qu2Y#93xzSdYCRy&*R&#_F;+6=-xcWG-ADR`ugx}|KgNysW(7xp1<BdJJWeB7oahb1=iVLN"
    "75+lb3z>VJ1U#H<*=5THwC8;D?(DW%)FRQBCNBGI=~%bY%#p_ZGK0kt+9d#=qARoF%p2Y5z6a3t$I$6G1K1v"
    "@$}6_<kV6=|LdEM7U#rjlw5NiF(wfiOo~+8+JYJ|AL!ax-o{vH5g9RqP?A%Js_xo^GGymiFK`@VCGXfeSD}H"
    "s+gt$F*ij=LH`lltGf%(`md=(;6V!om2F9^;j%=V(cZ_1Tu&|;j?7k@S$qJg~2pm?|5e*HdvqU3VGG8q3gFX"
    "^3=zf_lXNiaHT%wXpVejsB7j(~aDck-Hc{LoEFIxx;nsWKR_?hprq!@akvdy9Cz5s)Z$URP{zas4K8me0%{1"
    "FfxLQ-ONZ;a1?r6g5A>nblPR}!=iL@CAM9sCUCep>?6^TUt}!woUhX%v+hW_Nd+2<-rIo}d28XGuiwyGbm$8"
    "v>VAIl+n~lrA(&Zm^UG?hkyMJYYh}F(L=OM|kxcCOs;2$4KdvN++GQ(duZyo#!+Vd^4j$tkPPU<B62O0Wky?"
    "+q1bUs00@2^@<WC#Ve@ASK*s5lPKeX#){R9HxpNNT?zeB*ArMFLc+PmelRK?4ZKP%_)4Y#<3O$-fDQ=tT`KN"
    "MOOwqcEF0J-p>hl?&iNf$y@1b6qpP#wO&-tcwCs>i;3hOMMA&-gyBy+^Btr~+=o3Ttc7>`5+Y$cR3Xuy#^zI"
    "E_@%X)cJx)vil1UN`Z9%fnCMBFq+)1r4g-zYvC(w&cy{*m+Ce)>qqzHAjHs`pnL0$p(VR%c+pwOnCV*!jIJG"
    "x;TIAtU>r-vTJypH!tlZvu&0A+qxnY{XZ!k~a5BXp*7(RSW%kEgk!ByBh4qN{A~GXj+s-Ub0RBCX_KIZWTJV"
    "d%WHnB6Olgm#h)#nqr>9J4r`4@m+vzRb^X0jzROo)SO(RrCgV{rCN74ssKi_Y_MF3x}nbVs4Q%2;h7z#tFz-"
    "MF5Heda+iBuMj9Sp=gPsyUL^tmmHnjJ?kfIKSQ{KA^g2040vLw3-~q~0!&5hub9K}$(m8ZP@Z##Se+2f3a{s"
    "L3{?hp*zIy^bs4?vzWJuR_oUS3(7=aXDYfX!41+{5e^Z4(kz~moiGd~X^GQPGOt0@jYP^$TsM;2{g!TezU<~"
    "RXDHtF(QFMxQONrt0ta41oED`QJO+X3FZrF~&N5H@eVdCulkcxCTQDs{(5`uP(XB)}dMpXJ+O1S<cy-CVtMJ"
    "$l1WO#jF;g%D7F*F#Dp|UCtTguUzH;w5KnH-v@)@UzMwH?<X6Kz+OlxxhoDOOoWhzXQtlAWnmpSPNe6_BG&G"
    "@@4UZ&F7_-i(b%l}3WPPBTeTx=rp;%VE9MmoFr!<MJJ;t|ahTxs?xgv<w<wH9AKx`jtu4DB*L|a}t>lSWzUj"
    "zvDiNsZ0pR$`M$q)gL5mX_?GsOshhQWP-tY<B~ZW)rTgMF&cu#Emc8mwU$)69GYUZ8qK*(r!m#Dod(o|DiMY"
    "$C7{~)v7EAw^*iN?fQkE5ivWXE(MK%}UQ_VYq#9;wLRlrCY&azuc0X|3Ma0Y9E#!Sv&xO7+VIFaG7zBw~ESt"
    "&x*ITL}@93zLbkeI)Dq>|KwF}%e%2NCZ2beKvu@3zUu`z}-nfXYAre1K^1#vZ4zy|8F>V4u(@N_jZ?WA~uz<"
    "qd~%yP^DHz?dX2tHG48R<`<%gVVcq+?VSC%vSAw?+XGmR5OcRR!(?lHQg!iZBVIo)Nn4<yF(h<$%heLXJ0bU"
    "VYHu3^qKc{G`4MEiwM$oa&n?5`+AW4-R-PGUPbZ-TA~GR>UA-NN+#7MvR?~fP&8mc6~uL$<LsB$sO@oA{Oku"
    "XJbew!DEwyHCk{JVp3uKg1#rBn%^R*a|8>_bx7x8-;oB$+lLXNJREcOi%Mj@cqp4EFxtR-s{Vp*mBa;{7YfV"
    "7X}8@X++B)4SzLj-2-@xhtLA*#sjjAJH_7|PwRc%({Z4#yQzSPPKBtwV(Hg`|b<5KlP173rp1Cyxct;~KiKp"
    "W4h+0H7l12W*0ozd4k1F(O>5b$>tuLM!%Ld!r^ePM5n;0EqNDoMn@iH;05C)v!+M`IfHa1!80{gcjrL@GjU&"
    "mUuELM!gOKTpx`&;;JPArw|AzN_1+A0TWLHiXty)Kdh^DCX3^`&+<+hd3)aFVV`#%+(sx~oGp5*)OO4_{qf-"
    "(mAkqdAR>&~DPLD+*DWuZnTNL|8fFmUzhWu{Bf)2}lKrkgCrm2$9tyF~QX}E5jLC#5OAxL=R#=D<cFG>P7pL"
    "_h|_dN7%I38e+5wSS1={<O1;^#mXt#v$+Z!d6@%KL3?A#YP9%E&U?{|go_1ZI@nmO`1kOYOb!}q6jpP#ZZs4"
    "%_!&n5iTI203>kchOdz<Qd<zGQZ_Pux-1)yPm1dKF5zsvR%ih(tO-Tw5t?_UtyL+g*uS<uG8iW%URhi#MzHK"
    "T{KJq<S@T6?gR9~+^Z$2&3n{<tCK*(l<EC@OYoP#KSTg=NPvdv{qu9ysgfPnO<Q9jJjQ3d(zU+luMg%2y8{D"
    "17d3v(Msb_V)aCep1E;5&e9Z*D4qgKW4IWHU>X3Q5^<Nh)AS49ST=0E+=cF$(|t?epqB{g?qr$=)REY|0{ln"
    "Vz2R)8~D@^AEkR|FQS&KlNbQ|Eafx+j>>qt4jcHT$eq#yH}e-u|n#F&TuoVB$lKBX*vVS3KSh8&K>bP+rrGK"
    "Bv*A#PGy>7Z-FmNPz3C4I66Kf6RU5mR&b|)tGCzVI}D*hhnYFS+u{55nDxO$SEY0X6dx~;4k;~08v?9@oE+1"
    "12!PE1af40*DI?}Q%x=NUUO+p}&CT42tDK=8(MgWINX_foRfSs__I?L-1K)Za@wlz}M(Qlw7VnKXU^&rtA@1"
    "t9{IF%b?XCnfzzO;aQiNKUe`!3nZ5-aFREH&r&2wr<$5^bciaDq1deyV)du)0($SCt5&rbjS5D=pcPr52sbY"
    "8AtR6<%a)cBv$nDtAP&eqq)NSmb^=Iq=8wk_vl*Y>YE=OZkmMdoFzc~MHzS2=-ebIwM?-7H#U_VDS1VLFYJA"
    "*TCffZ-ZC)TXZm!nM~@Z8sf<#v4S_<#k3qVa$};bd$Bg`7Q$dq~(*<Bl$OGd%j^L_H)WO9Z|5*Bpci3j6u@g"
    "EZ4dJyHP~ZC(BAHI$H(L$9yY&4h5n$7e<E{CT@~nQqS!+yn#AH{1SYW#@1;kU#w6RZHND(p5M8H0ZiUN8Ck)"
    "~ISn|MFJMdfZ_8_=FEEh6--;iVKXRynKXK66|D^9$GM>L-|CId%R)&07%;Y|j)BHh#c=FK?PxH6h)zGp*+@&"
    "p`u;~YkurIvVk#CKZ$|Lb~Q{0WgJ#4{+&a3GdqOs$Go$0w386DdgTifK=QDpbg2=}pk*>I1c(&EmYyz|A!4E"
    "yVuZ^!s?m-`@G<!*yd4R_g)TCjpYAD{gB^wr+}X#DE<@L>O7bebzex>((v&WmMzy^wu}=H}yb{>`owMWpOA_"
    "<N`T9{=aUQc%r9>HE80wu};csZMGXG$(mzTSBMMO|cbo*w{HlKt-{Dy{2u|4&3%!H&5!X7dNx0``7f`+#&3~"
    "<KNo1_ZlS)zVKxH^gPkJj09K&phEaqeb7Y6I>UDL_!ppGIziV7-=`b*Pzf(F%-?AHb=bfJvyOF_rLIOR-s32"
    "j1<N){b~e$wHpwKr7*t$Ps^Ajl;CXg_r-w7svDo7|`@_)VW`6*abOQ;%sN1-ap4E^fqsKB<)^t{i<HuX`?1+"
    "@%?A5`G0sMy&qgEv*^q=23|1}LoIbc|Ei`{40B_x&sI&%OS;0BzHmr$BLThtU!to1lfyt4SA5GdHvkT`Nq)1"
    "56A?~QHt9>TEaEAtk;IruKk%7u#s32jrcT+D0G8}zf&vXnrh(IL&!7?A?GC)33R6n9!JKSV>e0@aXSO3pff<"
    "bTEE8TKHBL)p22wCLbOCXO-XGnmtO^L|>bI^08@+RSB0isQw5jXxrtPegs|G@ea$gS*Iyb2)`1At2}bL33ys"
    "lJtPj7}2@}+z?GS8G?oypjnM~hrM*nul*J*PAO@yyaTQ$*3qYKyq#1n43E0ptOZ*Xt5<|8$zPNh4TXFi_;W}"
    "N85|0!!vJtvY=_3qL-y!(Mau~pWkKjCh$LoS{XPb6H$!;+)G@n;6Rflk6p3>$Xfab=+KYT-dVJwzl76~<E*a"
    "9V=kJZK$Nsc_L#yFE+6Ydow;ZzqNJy9iWd77mH`6XQ_F*<tsIge9Vn>R9UgA+3fbi-4-^kj$^P7c0cxK$V(7"
    "7LS%T-EM+g8}CL>|)v^v&L61O3ch*oOto>4^HZCR#7+$RE19C1X13$Mc(oS6QWxy3(_%rwV+iP#`L{_Ui(Gw"
    "!ew$p5?R+vNzZnuJMe8SY4Olxqg=}nf6#~s2k)w`$WsG%WZr{uK88CMneU%VI++Q#qN?ZF;VSo=;HZAwi%l_"
    "*vVpJOWIm!55s@M_eMIym5Mg+w;rs5!0Z&L0y>Mtd})SOaM{SY1`7;Rl67z4&|9p2bJ=CN211V#nKh^an}~z"
    "fqk;psA5rS$#mCbuK{dCp?;TXhJ|Ef?`aq?f4#~dmplpZY<e*9pmTZXs4Sw;~ZRmXp;VWrPhWu~vYn0(Vq<`"
    "Y(y5=$3#O_N4PjIE5_dUdqVc&7<T^w3$;56*zBTuZ;lXBSuJP7jlqt30IQm2RY`9)aD)3I~U(?UM*!#Hy*cl"
    "lIaMXhKBOjW*SP<<%Y($Xe~B&M{5oya~RA+}LI1O^)Doe&!2ZQUH>i~AJD9)@m^j`w@+xp(?hBG!#sYZV`&`"
    "}Kaw(oIvHa}rBEX4VFgg2lY82fDyd4-jiHddUDR+|Oaxz)?0^IuAB0F~W{n?+w^AV+v1jXoS-n{j4(0Is>=Y"
    "K*MWGqzvV8olV@TO(a+kVJHZ9W_yQN0@pi!H9Au3*4LO;ShEQ=GhnmIXf$2$&P*_k0fL;6aD%osHK0Up!Nm$"
    "*kC{0D&476hKRP!WF(Ujyaw<4JX0+K79a^=Klx`>}@R}GdQ{4bG7M#KEBvWiD>%8o}{wGM}%`U5tT`!LUx(a"
    "KUAuvP1N=H;IEDc)R+*AmTg<T0j|L*lD(c`*Ua?TC(^8l>T;(e)QC<UW9x#SLLpul2zToHhEgHh2f0=tl5#8"
    "lATH5tPU>b}2&9Y}h+?NZbZ*L$83O1fEg;E+ZNLmAEz>b0Fk!mprKhYOH#$7scwE3yXy0O|-XPGO;O6+9Q4a"
    "7YlJ1@TCpvEcIYE?|oZ2TG^-Zw*U&Zq~!5!ctw=Gus8ywqihc3H|D=(30FFnE3!fUkP<0<{g~6S+Tl;O;;1b"
    ";u{aL$5q6Xl%Y;<l68a-T?~xfGu67AU86wK9quGN_A4`XLkLjz8&qaBD>F4f$c4&`<Ap=_XN>K=EQk2tJjSI"
    "6x!o}JWgbFgak<YBVCz3FG11s{P=nX4-&aeUW)q_|=(3<8A|`?FxlbxXbg`5P8Kpvk7vx1D{KNvC&k)V#oG?"
    "tIv$=XulNRdsUX{^swV0Jj<xJufeJnkGw92)6!;|Ba>}2%naBqJ^y-&=h*Bzy1Vcdw4+`C!OuO!i?#N3Wb8v"
    "LtAfX_~08^f}9x($<WQrKXOl(I(8y!ZUWpP!_mNBeew*ovGvq0%piCf+__e=72|bK*&8QB+hAc&P{DL=(fqN"
    "}H*HRi*_DnPbffi!?4fp>Z*PVx`ePo>FokV^>oy38XU7b(xV`W!7Pw&T@rNEkM+IfCdF364yLL?aEju_~S$m"
    "h6yQLPe@Xi>n-<w9QiWDNU!piNFD)E=tcTb$J+GtA^?+iT8|t2=uw&4U2;jzIVJ7Qd!hzD&uCwtH60B+9+tN"
    "*!BYq@R{FrW=jlE;-R)j7>g*Pn^5)xSW%qAJrQOHHFa!swx!B~A)E<oTT+K?t9|B*~fHe|UdIH^3DA%ws%s!"
    "@*z{;{w8YaG(G08=(L49=|D>3~Br5Kc}aIlQ(BWEfM1Fl-kuX5Uq(LBfpkNPT4jnAReX_D^++^8;DJtei40$"
    "a(@O{lLl8~6|qR(4e&@lYQjqp!(Eiw}9?ST!mlmYx&eCq%F&>eL<E^^`^e9wxtSKH0P?p~E3*f~T1PV4h9yW"
    "I>51hZZi}GYC)6!wf|zy65M_W@0hJAA4}Fd^1r-gMeX3?2unCM2Al0+v_`$BM6PmGPfTRAu!O;3jr+9exKVU"
    "kUm<ke+%jou75&V!r!sfm%qXf_gksTZZ=bt%D&t}H~O&iw)kZH1(=9O@`_`?MO)97zXjXR7b)}!kJ4_(ERIu"
    "Qf^JYHLBT2O>u7b@(1dnAg^HLCj`j~<zW{6*G5F~qt&DWUf>t9P%->j{0!k%?25-z?#`wk360MbzHafTUMtG"
    "Z9S*H(r0#%vlPL?Slb&V|_*Hj9FMtQsQCLvYz-mfbo?or)FrwkxvzkMR0`EGTjz=~iuAg4%buspZaWwnCfXL"
    "hwIptUz}Gv0=0k>^B`q_1E|V<H0cb0d8rF342mI}aRbwYm@ZGV4H~H}PBuu$<*~*F<&6SK?RznhK}O2ikaOI"
    "2)8tNEW|=^0~%vwmm8}*6pF*BgqCF+hz|BmTEmRuKlVqhr*VsXpbeT6|Ir&i_L09c#8@ya=S$%?GL%$9D5*w"
    "@ZtW4)s)*CTA9-2{)OgUJKZ;_x1gay!$!frn%hK5yz`7}L_!13B-m%{R>b2VIY!?lz{=D;dcdm2_X2acPef2"
    "kn{F&&Vt&LBhlXCkWqi8;zEtROrVFFn8>Tgb{po-)kKI;6hQMc&ozH-f3*{bqAnNPKV3AYu{z3}+Vl!i}B(S"
    "xMYdVpa#Y$kTh#{zvu$;2%@~v#e=7kt0{4AHFh0g--c;Nng3K?j=jV#0@u(rO2L!o!2_e2{)SKL4FFkS-i0T"
    "4SplBaMl9P?b9^H4{aK0e2DaGHWwVa-J#D50>(#TKPr7gMfSsxyT_o3_I*5D^Sh@5(8)LE+GOwnv~AZ99-2b"
    "IZQaW~5)xCc1DJF{<@yxcKLyB5W)4AoGUWr{;vUNiAGtJ&?*;xlEHbY%ve{L0v^1ax%4U>B1~SjknY6G%o6^"
    "*lA44-jF#{7`x^mbA#pOV0rNVlsTtCdfZHI>%>IR$r@y-_Zh(OZ`0fQz~0!7B52~`E3>=TH2w4&sQ!8~aep*"
    "*!RH!8YN(VOIhaZ!4`=LqnI)CR-sc7Q@!Qx;+NSq6Yy4X+sHfSPEhtC5okFE9bZP^n92u>zA%F(TkX5JkXrY"
    "=864z0S?Mj7_I4He$c#r)CvrcL4twx>4cIb_rxfK|8npl#G?&Hk8^sahN9K*9)Okq{F!hX-B_2vpwGZj|=al"
    "lHdtKw{`O^u9zm7|nxZMD7D+KrBIuck7OiYN1+N-|Hhx>p_FQFrxR@T|nr<Dx#@!s=jT@5n0!*Kd=Bg|VrQD"
    "ZII^xKe$oYl$QIrn()60a3SLe3kkpzMMrNT}dC}i@f#bYrXH{Tf#lzyTY&I8~v^0+x#!%o0M#PK-X-aT`OP8"
    "tx<vSIBBY|=L#%<ag7KFK9`)|MMvt@!kG8xtE#*-3Z5uc&}SCRXsgbH0pJcBls*(#rSC>N#NK^e;i?!Rr$x`"
    "pHR`Vi&yNQZ%(|wYscYy;uf^*Jh6OM}v6>e~6TK+p2p5@A4>#4k#B`61F<Q9cZl^FyT-4Xb;GOo=U^dkSf%N"
    "`~4H;NxxY*o0g_u1)0dqYt(}XKg=H*9anczwj+lCqoaOKdeT^UWYMu<D~^|ZMCu}d>HCIGFp^X=DByQqipA&"
    "(c`PK^{c#$x94nMGfClKIm+62w;0syv&1`YhDu3E96L9~=doXt`(@<M;?38J;Keel%0!VCL_TUX$#MS(<-k9"
    "!2_+49;hA4XvSc>ril9hTVz!^{gzHov-^}e;dm_VvkWk(HYRqaYY@;OP<{Lcdxd-Ar1HoM=k@MD-Ru9UnHox"
    "D!DU)dA`)5zj^a6$57_G=0=j#`ZsbHt6E!cgrrtsRI|k#04h}~fp(G-`^ZthsM+KBhpxu~PZ+y$(jg^FJ)XI"
    "GcLKTz`&*|7`;FmQ^gHWyFw1S2%Pr<3xO6RXOe4}K`cViUYZB6p$}te1GAXi9p9j%f4YP^422?i&Sa-Ef-&2"
    "`;)f{v5xWKLMyVr#^otQ5ruWRD=5nu7DGW6<jzxWLok{ba&15&o<P*FF(!d|S<x1s|9R!+k+>t=oyKB9=md~"
    "5auII*|llKscPQ{F~>^%dnSLf~Pwq8{vDeTB9Fa4Yu|@lhJ7VW|QZ(km83$I)}^*mK519VTAVXBJ?}k&SEut"
    "9-|nH1Lc^37Wvdj9D#da}Q3`#8m{qzz;@`=6oLB&NE#|Nsj|S9)Q$=xie6=u@lQF&o~edlV>Pe$@JA>cN-&#"
    "riM5@6z(Syr<d&jPUnYeia0FE=zB5idfA$}j;iJw1av~hHGkQta(V{noM*QyXwVs~FZMgW#J8V>fwf8B=umo"
    "@SV3{^fjPU>OyLgAKTMPa?<=mkByM&DcJ7%@`XqSLOo-DQ62!wdt0LJ91IW9$xb`zujkbdRN44g%$mU2=8YS"
    "gdalS0iqRYxoNcJkjHcYGq?qxT8_zf>xJ^UK|GQ+QtzZGBzaUX$@$^)8-WIr;D$?Kzoe}6rKjbvBk1-OybnP"
    "-1;kD-Rq)r><7vPoJuo-mZ<d=XN)XtZ2wPQK77EvX?RUw;vWShHA8EP<_NpFAXgkZS=ag^;p~)zUCjGvcx|>"
    "i!%Zs<~t;dv$aRV+~Xn)NB;3Sn>3;#%!KL^pIH;lX?SjzPm7u7@kXO<rtY(e~C5{qVIeIZfUcIrI&_7C36mP"
    "i4|u@&QyH1qR^k&6bvSj&<ZpLLn0rlLU`Zu4#IbnF_vZnzh;W4C&>9Lg3m89bJ)yod6hMrIUwmyS(OJ;tuV#"
    "d@S%ejqtweu!W~R*?X8!MAM!daR~1A<kjOgJWPm+;#reV>XD^mp-_0+sSBv>#Q^Vn_QyJk<`v=Z?!+z#h7!W"
    "34DFBu%E=%2W7tpKCgEn&sy?BD`W%ZG&;7ckUfE@_KqR%H@lpj7@&k!6}k0nxgH&M{=T=CcEVc^_waDv~~3P"
    "VE>U7r>y127M+R<KCiHQn}r3lh+wX5T0;>+6-#3zoA@ZFyJE@-}kR<qRPyGSq)bzuLjv1aeb5$v6cpB~F!fw"
    "|#v8oYK%5bY}s-p?NI=l!Kk7q&h`7D!I-~8^Fq`Uo@n>Lf{PKenE8zT!6r5OmgtNBEhIKK&9a=kSHfe0N3RV"
    "MuKd%1@jwq9;%w;joFmVe7)FQT$cpINm&6>*uZqd?OU(|2WG^1g%J|XpH|cFta^qT?j=Mc0ONs@g+Y--m<vt"
    "nTB*!Q&qTd4&se856FWZIALVlJaif=IQ&yrDk;Lf|#Kec4v?g7}vhr>NOg1WP0WM`W5BjW-0Qiep&+77yStI"
    "GW3QnNx8$t2*2_wTndmmm|)Oro$HyQ?%uXafSa&iR|QB=s{6?Om(DBM&(iNwJ%5{^@ZfI+Ehpq_nalUfLL*H"
    "bCr0@#3S07R80MmJ^+>tI%x6oZhvfUHY<&seNC3v^po*wWh!TtftMf_BkFTMPi~1;!~;oPHaCyu`e19G45Dj"
    "GU&Oiz|lmW~)J%hWU%wMAt50RK~ROEFfsp3XrizE>l8JHsOHqWZ)Y*-dh=+gBI3G3Q-~L?#U`6lIJ`tsTm>S"
    "A;+aP@FYyVxAG2W!;51iHh@wZzQ?&SkmPTuMS;yzqjn<(KU#aUtc{*At7<s?;v%%V?`Ga3xJ_}>VV9Mu?wY-"
    "_;4XY6ir&S-JK_6_IfYmODXOM!6M(2{-^`pXI&y;sWwP0kg4zXZm5fkRRMfDO&KnXgfHCqM)?T>J`9M=v44~"
    ";D;3>lpla}mXq>cle4)&8${T00>Zu09_;FLQ$gX%M6E?`F3q<_TI>3aSk3NhiCuPsxabMMb`McM<&SC;Csf5"
    "5S|^nsQ7j<9QBD#-Aw8ErNA1D@4EZ5LTG5Nn4s>4t*C$TnSBp(o*z@W8JT7}FBfnyM{kwyBuWU`lP*8#UQ*C"
    "}?h)V~<hxOPBOSV1Rh+tzdBdG$AOXG?BS7(7HKKN4NzS<UyNJ6phAkfm&YoG_SZ1JhO&9F=$Yb?E*UR2Ma7@"
    "UDdo+N|Qz=CO-F0lf^=uCv?@Q=_sF#AvvdA;DOiD>9YEm^I$#OkwrrkX;wgqKJF|+Co%YO$~+%DK-A3ztMRY"
    "qEe>zr@9Szg%=ccF+#LPhHfccH3Ul)V0P1*Q-6%OU1q15Gg>>(srmG(ndc|(^qMK+3GZkb4B#iwziPiHIx~2"
    "t^>pNWP2~3FHB)l{G$3Omfa7Ow;YA9P8I;U=VzScu%v>>pH)y)hLvB<BsN)KjE4*4KghElPP6bXgX)%uMNbb"
    "nPz_qrRj)hM(CIGT!)eCD4DLC~F?bP+@jLSK3=-t*ix%4sTMiVB(9@-?ig=S5{6GMzbOcr+I`B^p|D*5AlFr"
    "9dl9v@K@pefxwYqtOinL}|V1;0?rr-aav`;V+vqb-^J0x`9K=KhCOmi<kd8PYm{ul9#PzFI!7r+R9&AN?`m5"
    "Nz=WLtmJL4l0m$(of@M*BJclk*(Ek2)R111h@(T!T{~D%J7ACsT6%u;#^d-Y{WXmfrvMDRplaK_;mM|Qk>Ir"
    "NFo4S>7(~3G{r20jSGUr3agZSqW^|=*z2A-8m`(%1Peq(xSQ0drrN(JD&HOw}$Z5#r*;e5iSGnTA&$N_i7Zl"
    "AKW|y>OQ+K0N^|I|WvXzK-p%~Wiv=nQ&a*J?#n!R%P5R3{zE{VOD&>%YW3y_!g8nw5`Q~MNkAM}o2E@o3~ij"
    "1zYJj03!#128XyDASw#}uWmR~}#}f#7ypf>PEih~7NTu2T*bFOg6@qTcI3TeiB}52{8IseqWO=w~}5uTgxx@"
    "zMv>Rr<AGegvFUcps3~S=(WNo8rG~FD`Gra%92!%g=$94jZ?m(1?eZ$iUcaYinmpO$*p<K2j^wiS@#St~1ud"
    "|1|pk;3zxz@yF4NgT1p+92S1c1Owp<a9-CHfX0#;<y#kK#LW^=73S-V0;1=ebqH+BZ*(E<*!Q5}6|_d=%#*&"
    "u<S7VS8Tph?F#Y1dD`t>T;i#T*e5WPEmTbrfLx>hOzYfSX6I^I$%URVI)pBM`-)=uk<d;D=WHhZ~C}0(mgEp"
    "aVH|~Ig2+(k}e)t;TUR?XrszRp)R-;glYH+l{vz(u!X;NMyh;}#R%A<(xL{0JJNKCvOgh*!yp+n#{Q%m;leH"
    "Xryqw?l+xtY!S+VfXYt18jW8j=G8EyT|NwSzRIf$mb^;zf~hulZPh3ZMOVt9y75wGV74P~o7M*?B286clIkK"
    "G$oMC=CT7Bh{28!9bwJIKD5!QggvnLrDw!#kAcUa1u$;(A3i~8fHLF8LXBaP0|?+Onokig8ef*V0u-qcdeJ9"
    "<iuWYLFnBGQ~YZ0?1zTiPcW*EfJ-*3G5sj%TsREXVjBr>E2<Hy8b_)4YsO19KkBsJZt7;w{OF{_le;1uIZOi"
    "Xb~UvpE+D)xUk>{9Js?t2b4!X)mWO&F^3>hASjDPzd^7i6jIes6W<AaI4~=FUj^~Y(tYDIU3%ce6ozdIsTix"
    "Y}QdcASsdvbfs<Lu%Rqh@Aa`pq%RF_1{F0d%>vmRa9(}NZBJ9M7)Bs^Kq7FIHbozy9Id3R%E(|d+l)nj3MUU"
    "aQ-!2qih<Y~RYRE(mAD)j<G(j{_CfXNcx<gsbiQ@H5$h6V>;8iCils3Rm50>-!7uX-JnmVhLq7tFnQrELvi8"
    "^U8il$a;IMVQF(RFKv<oukeeEeRUPOubTd^(1OqB>qKj2QumeXO;)24Q*|ky2ngN*|6w(p#FNe`-t`r-IpmW"
    "Dy-kKURY~bSVJkN7@${WCr>C>#M8kFP?hdjj`*e=M^9cHynH!286BPJN-f!XJr*WP(q57xfr>o8s#4iyuDJG"
    "4>H{tBQ1SEjz&zTf;4$@-b?(LS`0L)xEXxesdb3SkeE^W{t754Kn?UBua|X44ZZW+6!N`NMC!-i)*JA+Z=_I"
    "49880{DDK=C`BrFWqaZG@-GAeGLfW6xXwqCS%y&%Owcky9m8V;DFbcn;aCGMf0ZE6dZ5h@PTu;7GI>+Qbxj%"
    "_W6CXfPCQkV&YhpN>CcYv=vOfk$y(8dN*r5D&F{7LRp3W=#bvyt-v=*;1u!3l<rbXH5Di!Eg07V1JqN7PkZt"
    "c<;Y@!(l?iM1kKDryDJQ6ucVB3n2UUI8^vfZnUptEg5CTy8B3>dF8amjF*psslw=XIO+@{-@bb%)6(JY`%>V"
    "hNE%w*GDtMa6H&nJ%r|p%n%{v)0_iH!n>M7cY};&32^anJVU_sW_1a3K+B#pi6&8-ok=eF59nfmRzR34stqe"
    "fzr$n$=)c0@8_WyxXRD0};5L^?EkJbfEAJow`08*3*aDbS7nvRssV9Dq`JAv6u#MqR1U0{*uJjpJ#!JaR=6a"
    "xxypi&6a@bIzj4^<6KdD9}Q-P@<?po5W=WJsx-oGzP>@H`qQ$?Wm6A=ZZ+(-%FAV%CiDOD1(#qeR{M_NZX66"
    "9xnYM6wvfclL-Krp8Ge#$PArZ8pA0Y#=ouPaTnJJJ^Lt4u?V%|Bzxd<N(487%HI4=lEMP@pe_?xE~z=>1_h{"
    "-U}lYnQifDOABdwhYOn>wrQqb()vL!6mS#W7;y5gVt?aWyjc>x3w<0v*#fD^eoSw^`Rw}F{J?;vJ(?fx7)I-"
    "%9Pp=xr{@qNZ#9RsNIh`Uq$V!AYTOkR2sQ1{f}4!3v7Zc0!{6TF^KFYs9XzjtEDtdR`Wwfk0OrbJ3zT{(jdT"
    "n;LIpvnw4|F2a4v$+%#gQ#A`39h5To6RcIAuG^QCq6FEx($F$`(OYC$RM9P_s&dPu@+axaX2ClDHi_H}_vlk"
    "vc@HGL}TkWffU(L(WFy~@cN{Be4u3G?}ivF8$EKus`)brf%P0hL>ii^_rQMogGd$WWb7k>G0G|UG8?p|XmUn"
    "V$EQ}&IUNf~``y}<`&xO|be!}GF2TBlHg(hs^H=Hbs~kZE3`u1;)T3F~mY1}mybThKZ}B-mp6snux0BweStM"
    "_LOII;1A`P<fuRYRN{bus6(+L=zNGRzDo&45e~$DUJqIR_D~I_yTcp#IS`lOS=tNM4_{K#Tn^(H}#-h#Z;{b"
    "GGW}jK{j!0<vB2v=acAI5=c2X-}S|lE<5<#%x+OPSg#7`pc5?<`dO(F7px-!n8Ewf%5Xt}`32gp;X$7`bt*k"
    "4aTvP``&B*W*+A|dVi5s*qBpjeg~K6f3-(TdiSH%37{yv}i&rz8J^A{Jh#2VUsM}mX8}d~@`?;9Cm&7ggQrT"
    "t+%g}*%KtfqEuQuC27C<+fSV=IkwKw`p*&~9TYNG|VndInANsn}I2X1-E2Ck^$Ic8q4%jc!L&?Wuqqb{CMr1"
    ">VIV1Rk=_&o#H@pWNdE<hHzyri^<D6>nduVu+W|LeG(m)Td2K)4fJH=QhF2N){p+mHlvZkFynfn$l7X4tR9g"
    "8R$d`fQJe8=kF~LhfssWu!a1`?r)#@1`IB?DS$dNm$PTHBi|n@YmXhbvZC#IYzsV?2eL?m$=N(zjEb9QD?11"
    "Wpp$y<c5bHLc%a0QFSEXTNUIjqCY3<hU8;grPVwha!@V`DR4@K(+(PieDip1;{U8ccLxo<Md{`Q=tA2;#5v<"
    "rFC3<AyxKn&m4Ha2`g2>D*M_R0M{D?RpB&6T7_z9KFebZ(IzV9Y0f_=Tz0vZudBUtJV9}!Gc1ro)#Wt`stE>"
    "a+q`2KSASJ=l`mGTwtfr$r9XQ3aljGwvq)^OrpaOwVvBkT=33y=iDX8DEiPNa1DS_WJpC|b?`O<Te<@oj4tJ"
    "i1Q{tpL-FTjgMbr7KBfV=Z6bP<2mt{uy1M}=-<8<VigfRkrC<EDi4=&HWSquDJ1LKVEQ3o6|1domcbDMI}~n"
    "?j8Y3Y;!^lb2<UAP}6!%rHb7u9w&}RN@$^9m*If6k8nlJc!jQDrtr{@jUd5gjiBPdf9CVht3M{^-3#K%b}>{"
    "j(JS(I8{<CTgC;>*VWv6UGqYgS0!C<P?t#lN8M=zD~QP=11|^n60Wz|UzO3dAb*flM|epv)WNGu{2OacZBOe"
    "7;qzj>Zymd!WED92WUWBJpTWLywQZYXl|6xkiKxNC_?9W7uHe!e>;1gNBG7eJLymrA0-SK{hz#`Y5hQK<gk$"
    "mDn$(?=xPt){ju+ZPcKsR+AALx}(GaE}NXrtvwqh;Z)?4`uI~)q2fy~+C$QJmPm_K&8Y=dhr{lH+hh)%X%D$"
    "e)GSX&h5R9!}PTg;(hed*OP7KSzrCiWQd1|cnssLZ$l)*xaT@kaVamXxWSV8Q$4VncnNpw&*++5hJG{<mE&h"
    "EEyg%tSH1c3FLlA0IKLxn+3~xsLV@H3x+9io(7gRwzM%HEJ?WRm07SHgTf*4^4=*puE_uh36}EzFq|OLd*@J"
    "ET4)Ti#djWsAO0e*&2|u*Gg%_2ux(mT^8r7ilmw1VnA}2@QUIV5-zc3FmNBH)}@O<&Eol;H}{-~w250f)*nf"
    "3WK}+g0rky-N|<+o{_5lhrh}<f?`S+yEMs!Oj7TxJ7vaf9*%@<LbTG^6y4qsq8_Ll0a<TXvZg1H=VSN=?#Ab"
    "Dl<%B&+yGVpF)|i4(E0G3_Sg0I*UiD`60n59vNKCe?NqQ{A_2*<oKk5s%+(2fA6AQi*w}-t^W6KQh+hzkk*e"
    ">Jg;BJyphF?6|BIEJ!FgMvwR#|DaqIT9>Jj<$i#MtIaSXT44;KKI9=+H!zHqjEG0XZ2c8O=I|RVtbXe4M(`G"
    "GLoQXwAO4M@6WzHILY24x*mx>(0N9g%{a%U)Fk~r5HPx&QA6l3vEMGN@$P1>5|6pYbb1+`QG4Ik(&3EZ<2dz"
    "LXHF~O=iy^PXHYLTCN|Tyf`@8JNYFX?d8GY2tBWn8N=o2c8Z-)4w%zl$6i`FAXI5)M{zS|`2;o9_4URm4*k{"
    "5dR4|AUzfba=a5+7<Y=+pdm+P(plA&+v1o%AW>B*P=4lBBa&B9OQVTamKgViJ1+61;+YDBIT$;y#_oP_IngW"
    "c3{${5RS91mf1`j^uYT$+}E-p4JSU|*iM-Co|ELS$|?*swzFeUSN6inx^`*)EvwMkn2<=tRF8a$<fK-s*@eM"
    "1)lC`uDy1ie*p8!sGpHh}j9`HkC$ue3r8u8iN^!OawRYV)EK0nz9UY3UHfPH!kmD8meDi0c$rb5JoaDE&Rs*"
    "(mdgMPsgz@m$6`G`>LR=Mo_)=440Vo$+|0&mv&c3@Ti#p<@VQR$WwJlj@9o5QJDBZuH-a$d0mQo71wsSXJk^"
    "kC480ae<rB&%Q@QJ;93*?vqTY&^FYhnK?}c%Btc<ol)QdUx}4?*UocRy)V&#0n@AlkYWhniux}DVIYoDq=Ik"
    "eh^trB*8&j>c}2ylLJJ;1_{$Z1G^7W!CJs@=QAC-Du~q=3X;t1V2=oBwz&!)Gn1ohJl2qy<VwdE4!0K(pvGC"
    "v!0osJsc)*r1zo5F&W0EVq<inuS;s)OBswA5)Pz8+=Vf8x7gzI!|^|;gbK<WL}bv@OzHRi@`%3mZBB;hrb<`"
    "^i%=9}v-Ds1g)jAOjW+c8D(MlugTJ6vvN=;~M_de-a?WLZm{-^?g0M4d1XVo$!1oEt{awLyPerRMQS)&S;BD"
    "4^N|&{h|+rzeZ1Rp%N$t3Y@CDsK&GAYr0S%94bko+|DlLjEMhr_k1EQ=akppQDkT_y?30+9_q9uY*DFW4oKe"
    ">d<Srg9;W_D(Kwzuz!G5NbcN4@Ac8q!O{0k2|fMoc5RenW1Z=j#^Sh+n~iY}?tt5Zc?DyJVaDQOm7$BMA5$}"
    "KTkR~Ts!nNw3Gp2<0Foi|JLdwjCb&`2*({4yD84AWB6W9#Nku;&oc(b8`V0h}VGo`sOngb~B#KRSs1_~7p9l"
    "bHXl8Ys5=%gA?4s9NDf--ErxL8tl+e<60^%597)B0qlR)lrFE>yijA)4V0uM*@GH9n#ps%v<j_f`;Po|&Xyo"
    "#CG(wnLVU#B6bNe?Vo^DQhWddJNME+Aze7*stZ{4LU?qw$chK?a!0i?GRwR9SUbt`*#fw0e(ys)Qfuo2#&XH"
    "Nlh3%iHdEq<Q*miuq9FZokax+d?RT-X%L<EsE((n%g5S0thFp1wsaaVxG!lAUq|`=k*l<^10f)N+Zn{t8)Q;"
    "!(*JxY$YNU_c~}>cx-dRYRQx5L<5+)sF1DKlS2Ul!JH^4e7AKgR)B!R1AHwl-YU$FK*xjhe8aj?YNlbe9>T("
    ";I<@$C-eBZ`%)Jh35ad;5)kJil0ZVqzpAc#3JGmDcoCuNcGWIC|sGdc^TO+HzU|6U9Z&0_`{}$#SrI9?%P<*"
    "Y*D?^lsp<|YwC_VCQv&!sTiBUwSa~7NRoIC3)C1H9PVgWX#AzHc4u(2?U2`%14pad7d7#&3yNf)`wiCDSFFD"
    "|s_w%5u8Rdq#E%arETqIl_%sG%5~+sJ)<m)YPT0#jodePYh=W~gdfe@Egyr7azlEca!htR^lsOT@=kT+D*;C"
    "L=N8GX;IeF!4fe@Fa)TU!j$f1f-VcD15ALiUhpWQ{KdsA4ezfLzy8+1+b<$?oA9U!HDLB{0v7vl=5bJP`<sO"
    "IxJYy;x_UaBsAK7x5-g0%a{W9(a#nmB;_S<*NjkBMXC`Z_W$ERs$8bopGGf_PY4*46)^?Yo|BW5(|sB;R#&{"
    "W7D&In)Q!WbT(%RPeB}u062P6O>bm+Q+y|_DlhQH`+bhS*bzl@w1qakDAu=j5@|u89;4&GWF$PyvlBRx#Mbp"
    "5IITd8@@buUgBy}{dTnI{U^D#p_i&RrwXD{Qr)&X9o%1OZ`n|LK)Xs=2OfuIfymyZgc;>8p685VL-ns*7lsy"
    "gu66d(AK8$@<?IR|leIVYRc(w-4La1c3yg+<CGU4eJh%n+VPPRaLiSV^!|ae7j1=|P~PaZDwx49|y>&3Xb;("
    "i%3!mIFQi)8X;{pUuB7_YMw6FUT>54^31rCF1|0q@CY2<=~67M!~^_!<1{Xs8e|u6)g&eQ&pWE!=bYaQ5_gi"
    "^O1gnVoRaGE)p?mb&xF&4S<YRgvE>4y$EDeP4F9Y_B&hrenS)qvQf1!jIVhMqjPs84|0W%t}DBXI7Y&CW2^9"
    "jUVGb$@^W43*JsiiCrGQ?)JMx2wPEi^=AEfB{Mx7_=@N5>2J>19N;PGO2W1|-;>Kr5Oh|NR8Q!@8B-lTh_j5"
    "pZ4Y-b&=E^a!v0%vliN83V7t8v3v2MFL4PW>)J1fkBYQf^_KG0jken%UBBPFg8yb<m$YYmZ%Id+(f;g~tA4f"
    "xa4Fx@pu^VE3chz+`ngZnXisocWUBO4?G7`qhS=v2u8Q7Z!t1}mER#2Z?>W|tJ1)OX#14V|!=o*E3nuM3vJa"
    "DI<ZQJ28Lx#h)RprcZ9RgyKrb7)w<Wr2}C1o#D%5Y7*o_+Sc?R8CWBL<IEKiA^dW3d}9Ti^^(A?Fl##l#8H9"
    "jTdk%YGGywT@;dz2z|rt>Ix+yOFOUyQzIIQX9WVcx+eX+pY0bLSOQKcp&dr-eCYZMh`~wBPpoecGR93rtZ9H"
    "~<<t=c`3|kN%(f8hZfZDLAT(+`m;eu4i=$(6Ehidw7-x{c9t{pSIPv&okL9P1O~lWgyP=zcF~v#ek~BHYbX2"
    "U<=J-??h@6W=8f<{vG4%NPu85vuN4Ma4%6bn;9*t>d#{6~r)SG{#S4sblGwItPR0DLQ1q^MxK$w2R1ue_B8z"
    "7<G%b2|@iDG`oc|IOd^|#*vOliTiHS*py`p7TeKKZo1Tb8^P{qYzgn&a{PAp3-0-8bI)zhZxUWuRq`o@Re8@"
    "6H!Sd>z2btv1Y|PVWrMy%~K3bO`gTqvJET=cupWwTYjyz5uJ7eDL-AYPl3CCfpp9SrV|MuOqs@Gb_^k*h&jx"
    "@04{Z0)t(Ij?XIJ43+Sw2CWMWt{@&2A{_u@y;_xZZHwHDj$zaUFj1k4Mow+9YFwYBphP7(s!NpwTWsg<s?`l"
    "o1QmkazO!k9oj*-IWp7TtHP|rh_ENh=fjBhEWRWODF9INt8t!D&JJ~xp9laRnE_-AkKxhs7s-SGQPnDeLhTY"
    "PY4$2tCKr(4;x4gcr{X($v8uBXMn}?=G?3^Ba|L23l!>+1-zaYU*jaZ;2gM1yXQ4~zJ;&QztQCW}>9+Wi)vC"
    "^j{^<ViP!`o=-|MnOguPnB22k<jLSCoInoM>Z4^+9zUugj0?j^Q*5#D{+SWV62P{bOWgJ<VP~;>1)Trz$j&8"
    "ZidR;R8`}+UE>IR_N+ZB`~|h6?C=2v00;iME+{SlBVUlRIZ=p3NaG#^D^bAEVC=1XRK={aHE0s>qsclw!=}C"
    "7LD~nsL9$$6?czYP+OgPy;v?WVz(`W|9i1}@HiG=OrCQQJC)r{cw;Cpi8Xow`U_gE*tnIAt2*ox3Z&RFUqWJ"
    "W?9T<*n&SW>F~BoeEU9g}VdWF1x=9xp5NEkjm<O!QC=w<%GSs<)+2#z2$a+JAmvGwTw%Bok5r|6LbIN!V&-("
    "068=3g7*a;*Zs_+DZ2E;ipvAra*O!AC#f?$bxcWDe7H5ymwI{HST%Xkc{a)$ADOc`3IsBc2?Qdx0~GGucjUZ"
    "~<A@{f7KC>el-zNm&4WW}l9hr-5DNg^;*r0XQ#*apLd{v2hX5sxl!Sj5~@MB;!7*@UyZ9yOq_&JX5;woeltK"
    "RHH_wGj^Vp<2wi&tR9NE(HZKzDq;{?18e#A&kN;=YY+Cr5VFBS+bWxgBx^?-oV5PNFjrCa_&=hTg^i=GwlYl"
    "h9~uX`3$?$j$}nfgGhy>H#d4<`R2ily6G{@K?+UgMi6M1s1{*kwp*-1qL5}TtJ0*D$8Vp0l9{;3%rsc7Uk&R"
    "@)+iiPZ!VzOkD;H=g33H3+=$iB&~YfGG+A#8HHDNJIN-V^G?Rtw-$PdD9kCVbrt!FWG9Iv7A2`dg8&XIuf2@"
    "<{hm)DiIWVar<UN$bOU8!-&1o8q+BvJm7V4Pv`+eDB<Xq=Q3|v6(oHeM-O-BAxE`m*)L`8O4-XeFbv93GDnh"
    "eKcfyt#|6Rb}bp-6xpxY>1Ww3!w+pAE6tSO}$X!vxN&c_FQn#XcxY3XE2D%I8I+G2!QeqlTr^JR5|mtUaX1X"
    ";l}-{wib4yC5LK3$4kHVEnV6*%A~#uWVa0u`tC_vrH@EiRBYIaqS13c*w>T!~-^P`vF;1l`)D@R=|enO<!(S"
    "%Q)_%3?J3~8#8}7#f^1QF-5EdsM9u?#SKKm)KY`$ObeMzW}5G<yI%P$+s+y9Ebber1U5v+l%lbW;>yr8o3d~"
    "qHP;JZS*au%O;@C(Qgmw2Ha*#YNjwIN2<=&yMb$7NnaX&+zz9%FOA2FnDX6O@;-Y1rxKxv@{=Wm`t9b-$pN0"
    "H>tMsuFNI#U?G@}OuMrnFfx2Y-5BMjQDM(r+!?SmY53e&FVAJp$uaLJ<EpO>l;bKByZ?dyE<w)?(oOlCBteR"
    "=KM)c$Yxt@GY$U_ac*-oBw<-eBI*n)fYwf1QG~U)^lZ>oVWkZcZn+Jd*%9#uamE%g5$PY3nN){bSJNwR-*P1"
    "@y2`YC(bRs8Gy7Jr(K!oK}*^bV<4xQE4fm0WM1s2tK>i8JCwMX$^~I8mv!JD!?`Zn}jn5$m1wsb<*P`F+f6I"
    "HfbR3vcz1yb?sEddUGz0F>J6Q7`~l?B}n73f124I9|BV#2_3F;>+z}41Lo87#YfD-FYPt`<y|)&Ju46uz-Fg"
    "O`OQSr`Gn=8le_DN)__Zd<#R={)M$h>9rGKzEm5fw1;F-C7&OH*fBs=~G6HK3UiyY{4F0QJVOv3?k4=z9rxW"
    "&7VzySE7Os-)Muf`+AI`4=acXd@OQNmku)QkRNx~7I=0t~o7v!PF<{I|6Fl5G>vO#8dt&3<j@YS6m$$7?E{;"
    "<ca60BDnGb9yS1R8kS8yhIT^g^_o?Bxn_0L%+e-`FH6GG3hPu#Kj69ceA8Fsg7QsF^U2sEQe29(OG7tRZhv_"
    "$cI`XiDrRtu<A`?P&&pq4xHPczd7$S(=}U{yA<+NwIqSw)+>i<5aCiSfHUxHby@kjDAkM7uIaGzu7r;JAV9o"
    "aYojce=8n1`C4`P*y&Q@*q5IzjoaFn&}J+7lT3C&Ok68-O7uV3tRUxX_>c~DEKW7x`|0RRVk|>w0M{r>L9uv"
    "!c-T^bMeG*)>isd>J9^PN)*m0!XAVwsf4aF@*1G!XW-%>iWB9rQe;P%JwJ7L<gu3Vux{-W=UUAZ2wpsVvE$~"
    "8e2lfs(v2VnY(UGAW$}syT$*B-^2=8j^Yr3V>k`-&!Zupb;=1^scErdWa*-f*WOq;&$l?Ph0oTMeG|Kv02Z?"
    "PoKJmtvCsPuD?#b48c<iKT>Hq+Ljdlb@=T+}Ed5d)>DeNazjvgWx`(pCi~)v^eoH15r|QDNEHyoP*G)r-l=$"
    "7f3Mk%QYlDt2BfpkPV0D<L<{w%rJuIgt$6a?`=Q2C#u3qYUQF+26>}zB391L&igLU$HS3Lb0aY;Pz>$ddi5g"
    "jDdU`?@oq5F%dP9@~XSX205;Z4Vd?RaeOpN8f8jh>0l=*)KIu_CH~vUxl$tK^V`s>*Ptxp);_dPQk_?UD3}N"
    "ak(Ar90V{M^<d|cg{bgg+Y79SOh{G>lGSoM%F4hCCD4vTeWuA1BvK!r^(|8H4*X3;L8XpBYt7)^2(*J>qp-$"
    "(b<kDt1(nST1%}Ed#K))h6&XXw^V85cpS~#aBPa4G(c>XbhMv0XO1xWF%)NoY5V;(4){~+VqNL?EM7f`s$U6"
    "5AI**K&MILZfhjvK=$-#%gRA@}<VG3%1EBOEu@_2Jf4sSy#13ohlinK$({T#|HMK-I?r_P_sY9}5R;YPXi_l"
    "poiy`B8n0`BrXF26t^MUAK~s;t1{zi`CY4pU@B77lyi&>$6=_K+mMa0Db(y3+crpyXal(GlYy&kFmeCxpP~l"
    "u*I*tb#9#N0aKe9$=V6$$G>-frTM*i*G@~*Y0KR3*X~YxwB<QmXWsZE{{1&!g&hP_x|=Wv>Bf%2jA`ukS+uG"
    "zbVWvwkt;-xd}dMMopl%F85_dTH#{RV6V+BMvlU<`o4#ZdaZ;H|DoqV1lPeTkKwjq2Extt$ObLKIPk_8qViJ"
    "^)*y3k=wII=7Pz79pbX@nWN)130XX6?~z0EqLvAN!Q+u}jCY8m24L;mOt)2o7t|J4fPi>lHwfsc!-w^`oCB*"
    "r|5ftBbkYQj}~+EfVYoT!*KYF-o-BBw84)Xe$QY2#y9O-_@!g>JwFS#oq28iz&^VDr#oI|psaqgqRfehUnh%"
    "usL0w9DQ^uEb-l1QS&fxJotmp0HV3v6YE?PGru|r$SsQT+-6-O9<8u|0&i6+uG1bWJR^2G}F*%0-rYe{i!Mp"
    "e6I^Ew=1WN-9crn5~QT97-$%Qrertn3WYIFsth;U?<|UPM#YS}4@5(^uDG~4krdI0%#;k9b7R<4tGi3shFRQ"
    "7?}V(Vso7mvBdm>u3v*zDqn}16zYrU=n7F#+GRh&NSa>d_VRyE=q!Ye<E+Bjj$gmQ9qO)LWttYewZIZh=SL2"
    "(xQ!1X#Z%H<~5ikh`!9(^km6S2DC+X~hdd$JmWUD6vp(gqySBW9{+$hV$tT0b?wJ9ZAZh!CaFgras8^x%>0u"
    "XP`Jw7cWr99jkT?!lJ%g)WQ26qK@purT-64$v>*?1>=M+25|6VLmUz=4*I^<MR~>eEFnbihjl0XV|Em#m^V$"
    "#7c<9j2dCI0n-S1f4XdwU@n<Z+qWhIhBA9Lp}CDH;Rzvd<#ovP1uKsT|llHpaErambOA4d^~4oht%gCSPVh1"
    "#z-pUN8$uX4oG7EL6<*TeylL<ANe#gsYETcB&^QLE3@i1;9w?~%ffHgsU&g($bf1y%kX)W_ri1SLzs`eDPi$"
    "Dz@H@=QsQQ#z`)gDQRk}TMT@ZcpV&7vF*EL?iidLkzP7p4MhZfrH&&aj@SNI$&}!WsNCYmmYQ`At89M6KCHH"
    "nhNHd8$<F=6EB5}n(9iRP>Jmt;-DK*gO9H&e=L<z?DbLIA#@qjR}8w)9Z+1de5&KJGK(&}7}2YDNu0J6XBiI"
    "7xq1X!0HN`z=z+bY7pWC^%xI*yRD9YOQHl`i8s|5C2JzT+qOrIJ)e-kbknosLCEU}~lTobG6=pD>+H(&I_B?"
    "Y~u%JX&NE=(q*Qn(%nQ9A6oxZdmX@atY~2$eXw+6^Mii!BlEQ=jerm0uCdS8eB-$n;jH9<pc$Z#3X*NOPy69"
    "L1ymg3~U#rqW2zW$e<9?_q@Vh#S4E(oPhu^uH{<j|7$^kf-n`AMOTsl0c?w`0i^B;Avytu%>{a?-n$$%*-x)"
    "KFmZsoxb5@SR<1uT)K=N4@+=it4`o!l(N2$l=3KVP)M!Uz;5!r1{v0Ygox&x$P@p7@6+(C;KlL4eu2uy&Dk)"
    "=fak06f_B_awaRd)wiAd3XmKXM$)hn{@>T3z3q1c$|7@gtHUe{kOz@Z9OIDFx`q(kh$2ry6)DqrWm8JmBbEn"
    "&`{v}XWpE^b5Wh6pis%-84DbPNv~(*hN<jvmE3)m=@iPqSlD@%LY!py)aW7TnKHp=1ov)lexhtQa~oVVuOgK"
    "BO<NF}pIX31>YKQaS3y+=5eqKS_84Oc=gp&dl~BwfDl<mPZgzZKevE)AS-!uV*-BO*ld%j2iJsn`NQV&+nMi"
    "`4De+@Irbt@DbbY+=u~7JJsitO~ne>1{aX7q|Ha^jjIPV?8(ruVW)ax3^NJbHNu{RFV)$d!n>&#*24&a>F<E"
    "V(u7%E`ZqV5HO`de2iW`#r5rXtDDg0Px4#?8HW*s>F7OeH%yo7Wk4MA(Nx$wV?{U@i-W7>K5)wg$177|on&F"
    "n-&2VK^2Th5nl#P4Uky6A|kIs42T$`i*3y1e?U!MFTh{Fh(XXZ>ktJ@|P#u@RY?^<raHR8%PcZ#;5v9^;{f~"
    "2<X*xM&Y1MtQ{5H(o4^b9D#O*6K#Cl);k8CRwE0Aipdm6u$4SU3U133MWzBtq6SwFm6N+b1U*pKCF=p7fYVF"
    "M*b0fHpa_G19F`EN`Ejjt)orXBn!M;vzt$W6Zk7%ah|DogP5hC?1oc)Rbseo#2e+I*X%g6jUQ!jP{|Cex~I`"
    "RTHa$NDZhm;P#Ff2)3A+N^Up>0cz~gQPy~emTY|JhP?T~0#wuCyo4i;8E+pTy(Pl?g%oA_Cy&7DSaJ`2L7s="
    "2J_}umJ`I%^4z6|LS}v}KvEUDG3ie|dE`7k#c{9z5UDm@lfYo8><_(3W-w{SP$aW*sfSyA4zwFXb{)lX#J<("
    "Ga(sAYIAC3=4q*3IyeZ{N*J}7pdErVSrfVYfBjJcau)5idJKLV1nWa}?MadibDaQka8WA1)7F4jYfKc$J)V{"
    "nd0eJUM19w&Nle}DAq%u9L0bVE0Wk%9K={U7#@z8{^APe%X#dUR@T`-~??V|hwpbIST45$4&2-*7I=(dp>qE"
    "IT+lI~FUk!^s<{q^g4ypPk(9K;FQ+C0Y`kif;DP-l2KRtn<e_3;(~HWXPSSngC?Pje+ANv(Veq$SER@(Rf9}"
    ";R~kdQeiM(x6_oa*Um6fIe6VP1$=&1&X&}J=ClKRY+qF6<bK-p8=06h>jr990ZE^i7k<$6c7EqB#qGIoUYAG"
    "Na9~#4853?k?O4~3riRS7=iCeApyg_vHTxtJzxS=yhs9($aKVpJt|L-ph_%G-BgO~y-A53<ezOlo(g`Nyy^B"
    "0aBVrq5@=ND0hPixse1iQFkM@2Xy<m0EHM0plFH$UkwcX_TXZRcPAP9hIA5dnbh;r}MfssFp_d#nVf}%z-1d"
    "f?yg;ricivNuTDJK(>>_+M?houG@Nzz(RaBq!<Gxwzei1K1iwgbQnz;c6!ti{8z)&Jn~?@&p5g#E@zvU;EgY"
    "V#pg0@}!Yp%%hfm}^%1@0xUJ&xoriBeIr203>)qPz83GH422?*;O%bNy8+?T-in1tq&S{yHZXki1vwu(^xay"
    ";Osd$sLoLCZGq>)O%CZFcP&!+e6}7||7rLY>f}OvJ09i}#(WA7GM*tS4W<(SdLir`{@x>GW)<#t<4$PW69Uj"
    "j?~~`6=}|9f9B{xbM=);$%V*e_^jb|&;sS^8I2JNTNI&Em<PM;2Pzz}syMYV?CbgF1DXZ!`Ak|v8Iw0jb=YZ"
    "VIDQ&Ly*tsw!VFbd^lgyl8y3vVc70YA#f)v7^Mkfa^e}R;dq^T1rmci3R!Ay_YZ3K}GhJn|W5s4!RaIB(hMj"
    "acvxzRUzQGqVOAbw*P&q-DMNau}iB+Ey>#%2IKvTKyUJMd1=B({dFNeQq?db6zQWz0I5mc6k2Fog~UFo7`|U"
    "NrT0N(PAyW9}m>X1px!W{YAPFx^in{^h6v^p{rs6ZNRE)svboijpuj%ShfK#5>5|G-gN3>Z6v`cUxp8McxVe"
    "!MZA-=Mk(0f2}OQ`vzAa7`JML<Euh@_daO}2ENyy(#)4#3;~5SyAc{Urp*oE7gM)vgKzk2S_}<hUiW(V#%)5"
    "hbm2mUR`$?-5&AgLe=`K{kKM{>^zMU=^xxKS)q6_jYf6NBd(&jFM(zn-q1-0^xtH%YjL~A-KGeKzr`DKi8_{"
    "2&vQ6Ng;DCaxefeiZ#{fU2OHwC%E0XC(*MJJ?Hp?0U1}(Y6TNsf?stvz?)9Q2ldKWADQKq-s=YCZ$z|Jey$v"
    "d~0<8YYN`OYoA$UOV6YT5CQz8tt5m;Pc+oyQW97V88aW+VQyfr5Yysi*G(w7A2j?ZPKR4mPBhbCRTiu80ZA)"
    "goRR=E1eta&=2>cI1|n2do>Nk@A1g*=fhwL-L%_sfTYOqXygpsD)6-Aq&QP*LZ@e^%(l24!@>?ZoMjW2EJ+9"
    "RqoQw&gG^j@N%>&GCS6TDCI&Fhn-gKQOZ%EC@Gy}7s^qOWSUX8ZXu&U71>rFs|^qrchDAP11+_S*_Hyd2g%Y"
    "{o(jY0B*dnOK`mjmZrB(BO+~aG<``}io?D8lt@+wYMmumlZ?Ij3%1#2>nMk`Fm2a9j!Pnb|-+|rju6XP~j-T"
    "m67S|w!9$Dw$XrpJAR*in<`4{0dJDFl!#^tXa+_BqoicfnxYk2#FlpvhV=BD#aq_ZQ52z7KDhgmPy#SF`t%6"
    "X?j-A@%5rM%K?#6@mt>(@@ZzaHtH<_rl+WdgS*wqdkB80&T{QvOZPleGt4CqthV)xaXIq4TIuasnih@=;6$M"
    "CVfvo;odW7MT5~%-8c0T9>;Di{eJm=pktcdU#R#)YZo9O<7|Da9)L)dtA+Ct?6{Q)Ps1Hz>)DTa(fvOGQTrF"
    "VR5V<6sak=jK>fx0ZfHc{;ENgKeUtQx*y-_dx2bn)SbG=BZh=r3*HB`<3z>_{T>B#QjeB5wQk3bmTT$Buphq"
    "dS=;^a?3K$tx##_F_Qx0VNBQBm@(i^xUzU3u&zt<w+K2tDjvUfQnD*y}dx6bhFSz}g<woXC&zj8k_*-(YYZP"
    "_g39cR5(sO6}ork^d0JFGmhH^BqjzXNH%Bx=85at&*Tei8Es-<s`d`VF`i#884R}LNM$za$ULT^LfNGqe-5^"
    "m9_4Q>t3oTCf5(vQ}pXaXs~I}ZOHroPcU&mI)4;ND-fjs56NUHtDs$zBX_f|*^O8;jGs+`C!Op-{(u`-EeK*"
    "}*9x7#*L8rZmi+J?om!FGeTXpMHT^nlE3BPWQ9JgC7shvTx#CF|{R$G%>S|o%kI86nk4f6tijyswOJOl+;8o"
    "i-}F3otPz4sMY}si1KE`xb}m#`DTH6o)<RjPwqK>X)~37vpuzY^T&tn46B`grCot+@p}EG&!65Hk$cP|EtZM"
    "s`G2J|_rL7)w5w*xQ)K>4ZjKaBr4$l<aIz7)i%~I}mrl7*V)7NV-T?8lELW&Ei#koY+1U8p{o2n?QA&y04A4"
    "%xPq~|rZrbar1E?92m;$qsV%tHQN*>1oQB0NyzzPy}j%^mOYY2myJAfB>2UHih0s6J?DL*P!KrUwfZ=cZYv8"
    "3S%D0222i-y3zy(dujl6y=?&5q3Wnwfp4F2M>~4C})$ZIbwNvXS+H(RE$Bu(OA-u^<OINPdk?5k$)aZ)F`Fk"
    "^WVQ*>700^`r|KqK(j%eRJA2$r^H2UxKXM=m67Ft27Yim7eRYg;_S9zr?v?mCq@tii09F!s@*(PH|(Nl<NYz"
    "a&YGXF4^^!AJigyR4HT+1XRlzD*lc%Td$l7k1-vNs|Bj1D=hY%v~i$G3yms!6l;;{k`wPzhH3Y6i(~q!;+WR"
    "z7TRok$yPGJ!i4I418mIUuhngYP_7{dyeStCWt87BMp`gAGawe59vu{_(YHV~nENNh_3B9mwV9;rR&&GaR?-"
    "=qM#ls7Yw(#D2d8HTNBd_%k8~<|U`Xtgcz&n|4tNZ2-6wa(gJg<03IAU2F->g@5h5f}x6i!I-f%nY^v`4xf}"
    "v(ic+d+JY4dJF5ZZ{kp47NGq#7zT2i!xo=_Bd}PGYU98K`ni?Wp{AQryxUO}v`MqKZH@91kSz53xL)ixLSU$"
    "QY4kCz-p7@W8f+X7w+74DO@ShbU1A1uU#HG-1Xj5mRnzeoZ~Sby6wxx4@QWQ0oQVz^S*z9eUTWf($xHLJAj@"
    "WCNmNKRdex--?+GG#1hIkyPbRo@#6n0ugX}OR}4JDex!g>#&j2Cl3xfRv`8|G1@EFwy@$B<z%I!qtDBD1(s)"
    "7ye_k!E-ok(Z&5g)K67!t;Cg52pH}b#`BlEtE!T3LLOYc<l=VWDPca)YOu^8S#T69K17>(JFoQQWEXAsg%J%"
    "Pvi0}b8AAlnOHC=+jQ@8;KP|Xb6Ym_uBjm8_)>{jQMnb7Kvc*zBVA`*BA$}H995u{&vgD^$dqH2-NH#g_lI$"
    "r6DcvRL{;m%2qT&9HcGCSai1k0H%q?4P9@_yjkA!tsG9kj84a6yeVE##0<-HUUm{Wp4S>F?un>ZVse|Mu%||"
    "DpHwKlaRj>%Yv*s6Ae}9w0N&%Js}(Jz2Q^&Gc7gyuia!{MKj4#B#Ha9~SIx<Fi7zL(OX8i47b!aJKU8gCvj-"
    "|ESFaIUP{pE36h*XB{e-_}10D;R%Mx%}dNS89p>YiI;c(`1R3Q=c{hEcbZ*D1s`h9>Et0=bDWhpd_c`La>Y>"
    "M#k#}s`8<2}|M<nZ&$^AE(;aBi2}9oZE$@d-^zM(+Sdu0y?@2XZckJ4joxH$p{Fm(Ogx;ig1EBaiFq2pW>&v"
    "u+4a@W&t~~v07>!k!z+4j;jNDi#CkH<n`wREw?1xcyIC}B@=)}jsAk>liz1JMjj43m71BQ?m8onX{MbHdy(S"
    "~Z#Qi8y_te;4|-6_Cx{~#73RBdzWIGZ7|4WY%$j{25`0gV{}J38LD;Ojf8+`%{X6tOX~V%0#XRsA}liy~4vT"
    "olw#()OWePmDuds27_RcnXxxg>8@PsO$xb&_ANEo^5XCwFMG!@Yer!dVGX}a(#<kl#Cu?X3EYeEyM`b0b1OF"
    "1`m^QFmO0JIypdXnO187H(|}In8Do;FV=V?5-3o8;S7txjz}(B9%*^%bi@DxWizKMQMQuWBt@7Upm;wAA~y3"
    "mFBxmgsB^`f`b4i6i&?uw`waJ9l(@p}A&^j|p+<{@3yg|D+--I3v4`$)Rri-zb}tRGFoDpT0H6HHn%|yv!0X"
    "n1cHb1u+fzns)U_NTy`XoUhlEoBbljIL*C|`E3p@rPZNd1A?&J~m7oKm7uq#@Oyoc`)PY+tINk^7@+f1;gb*"
    "|O~Mez}#BDR1xynS+(<O25aQ<g4{kJi$hu>q?(W9Ii|HmvNe9=2y{&H0phi!D$4VyldWgrEFJ-sfty`2zFwX"
    "Y}i{clUo2i{94LXNT23yViiEaulT-5<ezf_@?*&*=8HCi(LA@f&iqCOYY(0#D<IYeEyogtUh|}7^zp#L)Y1+"
    "D&R{8)qYedX82QO<^^J~b|IEQhJI#v!13kJsBSv<qSZu_kumbv*jha`K9M6rqKNm#4r<I{i|H67I2j4iBdZQ"
    "NaDwAjY+z|t#e<=j&-VLZCBwsAo?^no)uyViDZIh6!yG;I6dJ}%u=%`pl)XnvuH+<pjnbCpF6brM&;D&Qy+X"
    "gl=Hi-*dby#Tb9e*jl{Mw5bMJZ3dmf<Vo}*VkGXtZCN}7gOYt_M(;JR}>?1baKS+-~-D%d0?e(tM|-3PxSaJ"
    "jKpqn`kpA@(gDo0WM^1%);KnS|;$$H%{`XT}XZ=bA`JNA7F793+rI)E%&58MU2b=t~QlB>L1jVZ&A2S|-8*2"
    "7p<S(o?P-0i4lEzyEw<7T^jOj-Y6Z^V+Db0D=mrxj@q~cq2B`R1L?=`T{~;0VEQy@U#NFvIY377D<p?&`-^?"
    "5%UZ-98`Fx1S2c21KeKn38WCmk%C;uj7!j<i}~FxL46{mEH$?6ht*c*ZHI^!I{wc^h50XL_PO4Q*w}`pfIIt"
    "@vEIz1I^D-(Z%O?(%27FY08e0_e~%|uST<)MWo?a(0C&qvTdD~AiSSNADr-uk)0emQAbR`6-m1kBFq0OTEzm"
    "e<L7VeklX4c=T}7z#WgSkq5os%FdnyRe6^MYn`CS`Yr?NNUchB6^CL9}^R>N^tWj~FzXhD`9s6GQHF{U5L05"
    "&WQFA2zr0U7%mjKhI+gljKXC(vUAF++XXe1Diiol3O!?6Npsj4!5jQ+maBpK+dOkwGV7#FBO!;1fNu6~yjWQ"
    "b-@HK+z4y=MXuzP{?iAZ@VCsFe++8GAFBnelq8tWz#X(Ek#mLO{p$@fCI_?Fza%5@_Lk=9DM)7S(Lu%26woF"
    "<kT-PixgJgn#SN=gIE;FqiXHkeHz3-`~Ad?x0Li35^EUBq2OIVJ1{33!m=QI26}Ga^g&&n8X~7$(UiwAXL0S"
    "J?JAJn@7!?T_B9TlWX+RrM)YrW`5*e($*4E_kJ0|?v(YKv;loE*zT`JPb7TCydL*iCQ{T&(8Z@U!5jn8}uxX"
    "9_g0flxGGbKAc9~a``2W--DC+G`1ZrRr=z3~2j8#RtB!{~R-PfCg>P=$wjt=>`7-S7kCG0}iBeK(Vxy=3`Dl"
    "i;mq>>vz>0i}-Tf)h~(_#ZoJZAlfO<x4lkoq)A1%ejS#e7}*3S9kOgb1exU*S0>kLAt6?|ZPgRN7GAOc?rN)"
    "C*Lt3EJMvn#9Z~cXDou_o0uQdSzVNhQrcL004{YHWiyWfDhE6_(CgChg@fYI_QgsgLFIqH~2Tj4E7ho^ZncT"
    "rM&!6K&_4ws&>Kx1(w0~QzAdJ$^9s6F3v~P64?uIU3>uGB|~D?ko+Rn|2|evBJJ74QnDzwmnT$EN_5vrgZ>F"
    "bpch^-%h`SKdLr(Wu|eTr8soFk->QVvRu2A!JSWgR(LzJ-vR-ovfu}KA9=tMA9>bym%VHG6p;31rxcTCIF}="
    "ei0&e(6M0Z|NF~t=7k2DSBa#Nr4fK3bbg60YA6+r(f-!z<XatSpk^(o`%RE#HY6SXWBkGRcdh?aH?ir+1)Wv"
    "cMwDR(!7cZDAAC6$O|*JUwVU*EB5w^jil=uA((5VX7?saLUT5%R;Zrcx?a2U#n$Pk;@SfJxX1@5kMyLYIVi4"
    "kgmS1&PsKa0K+i2VLOT=o?$_rtWlwcKvc%pSIoT4|l2Vlb;HP!0eK>=XR)W%0c$&S)M)Xqd&ksse9kf4a{yj"
    "$gPypi;Z=Rx+@^Bh3!?4PCTGSJQNYc4xV&i6c+45D#lu&mBlg3&PGI3rW=%IK?=*(Gjk%LJUD*N{q$;dLf*r"
    "21_)x%tgg7YR(>O03aXuAj4S4+#)>DLmIQk)Op-~yy7TB$*OJZHnmvNBr|K)zp(tG)I>ewHpe7EGj>XwwTK9"
    "bl%Bgvb?Z*UxU~Dz$)o!gyd`jtO%TZe=hH|s+6f`4I`0gJcot+%~={2N6XD67Rq;FP<O2P#(Mafpi)jbe@_#"
    "FYPt1?{BX!T&2RgdP6t*gT=7vT27^CVI3p*t^7^SoMn>vF!3?t=~RaomeWvMSvI*oH`cX8>}O_p_h5dKd1>g"
    "967e@!#+jvj@O5FIEtN*W*#)0AS36PK|ysL|ZmmHP||;s+e8cmlb->jm82(n6fGK3md8b=hrrwfbA6N_bnNn"
    "sI{Q0l9LNj<-%ZZwf0DUWEBZBh&w=Lfey}2v*VwS$av*r>bv6c;l9L?^+y@jvqtVK&?Od|+8FBCYtyB)qKvA"
    "IT~Q<6ed!+{RmZ`tDN=<O=73Gh0FFO|1PrvbUnPCq!{_`$PTJ<8;5I)G?W*UMbqAibZG?NglWf~B>NIME=-l"
    "c!a$tmEK2IvV5>l{x#TTQ)gP%qx&|lQWy}(<xFh~0(1|h;>s`&?VNUJL;1ui|e^}#8%CW5mt2*d+=6p~Q~=n"
    "Qsesgzs>(rT{Yz$(gQ_A2yKE0GQ}f>>)>69z2j8>eHHrQVQ|LWz3wbv55aZvsuADpk&~SWzxhzu%vr^I=LQv"
    "jiG;!Ogo6?%?d?7(mU>!Xd$=1;T`0+a6O^hZ-{!&13Kh&LM7FSVrA4$=jOU6w@-i)-bk<jbT5wmnO#-*arj3"
    ")WWM|7T70iRktMiKV}!GzJea{ct$aDX+d@p_fD`Gw(+TH2KSA@7c(v=zXQwEyr|V{&BxuDY@%}Fp`>uLlUUT"
    "ar#b%P1POFBy)B`S-eTsWkR;wkdV+f#&lD*Q&BHqN5(o;zbreA+xgDwqNK%DNzIoWn<v4&Z?2Gc!7Yo<6Z5="
    "K$MgXR(#gd!aa2rL|VcH{C%sic1OipUsLCMnv#F6dyaf&JwpL&gT&KaQqTdP6ng6r#Tt69&f81<N1So4;(UU"
    "que7EF*~N7k#-5lIgs*6KIGvdd^2Rv{5mr9bIW8Vo{XC2$&UIlJ=|e6}u(6rH5-2_~S_LmkTbosXu#R#i>D8"
    "$F_jte~1YqYt=ftQC=_t%1dW?(8XP*lqVt!Gk^BSy_Vo+lMr~O6p3{AkBj5@oLkWbR7#Y-xkBxPB!pwqB`l+"
    "E(jYhE|VbI&5XeXIeeh%FW)Ij%-h{GEVK5~6Y{Zz4U!h(qQHp=Z-~dt*|+rMwgL!MR1EgpE?thKxLDd;jDt="
    "Z4FwKCg1YY`msR?*x;*npZk8*4HE+7Dl2+9Ua1I@6mntB`+}A5BC|c;$HfYq1C>im@F%H6Iz}OUfA-<%b`vL"
    "U!!u5)j9-PjO*nOqCq4%SO$-^Find^%-cy-IOJtwVY-{cfKF9SFnM8>BGOm`w%j((ZIu|k!17gS*>G(lb>Y<"
    "sK9dl>;A*FWv+T@zR&ly1_y8qs4rU^usnVdxl}B9oq7Y^_}klfXMop`|a<a!%p$Xot@34BaTk%nb!HNz@nMz"
    "Tasl23PVeEF4stDJ4Oo63(VC;vTiV|J*F8>3OMLHLmMsYw{{wG=6k(;Fo9e!r-@qtbAr=xAp7W6?ja%laD0_"
    "<97~uCIWUvsxh<SALy>IDy^*~`x0TiMvhvhHHEJ4Sf>q4`_-|tJ?YO02rah%JvV3swx+?$1Y9d}{#I)~__2+"
    "Fb-wmw1G~eers62E>mWwL*9ZOMpTckThW!J+7hNt-xDZzsprV1SLhlu31e)s-8nCU9NTk8NL(CGL5cOyk<dY"
    "iZUXxl?yKdkd7%gVj<Gv;5lQZ9fR1lyRF_wVFYjiQHFBYo@HA<yp0-0FbGzXxiS7!Gws%0TH_B$#ERz+fxjA"
    "*r=y(nkKlp+%lO*$%#(<9k!bh$->v@dL2lfS16T3Yt(Um|N2xZ(rs8RvKssrqgzP@@(3Zi<9q&VVlLLYI^`D"
    "kz{Mv&IJ&wySb|T`j}YOeUk;4J@o5W+#z2P(byc!WNNDs5-$>dz^V<u|sxgmzwC1+Q=F2y^f}z1FNLF-Xy`X"
    "Q&1@KIy=hMU5%#%?rG9+YLvB~w)HN(ha{R5X*^0l++qM((!61lrQX44fT#(N3NCqqA6bL$&V?dzM#i&xXSI="
    "3I1a&+K0zL+N<cwFj?gfsC-aibL2zN5*9tD>nx6EiwoC?_@=?m4Z#{Cn(QgI~Oe8&^bwXF`ob`4Z)f=(c(oF"
    "inHFTt>HSt{Z=QbhCw(3LYca(lI$N(wj4Q4AN%Ix0!?j1l&e7fHixJ-uX*X4RzUKX3#y5kOyYo73~n`dv{b^"
    "8S7!YV|RDLKXN4h#j&Fc%sEdgr{FV3rqPFoJ{u{${5PsA`UFy?K{*oVa@*ue2O3{8Zr}^Z3~(na2II?QziHW"
    "<hUpDYiy}Q7dxj?Y)_QQ3qYrNSqs<+c?BdE<3YY5Qc>QX@;^Cg{h5VU=FUjm4+CkNq+M#xm7gmXGEa%9_dZ7"
    "Rij*e*|wxFG3!a?+54MQfE90Mc_UT=^yjSVdW)az!5bxMNgHFKt!9Xi#1BSZB^gTTw4}tAJ#93PlC2C?aVVA"
    "9c{<latSGm1U<fs|NTdN@m8+hMcZqTcL9n^m(F+Rx1gTT(hC&N4U~QOVG-RrZ2+nT=?jdu;iz#C@G^h(s0Ur"
    ";~s)~`^%sFVDL!$j${1qP?oZO&cW;>jmt*1vyMRX~|E}0*J9z&%7jJE+1467KSV~m{{ZP_1>I!m4(OCzO-2X"
    "|XWNa8e6{ZW!00$QL&^GHGK)j|n8mp8Tplh+%?e@dEp;*@?3-ihg4#jM;G2B0)AaT1e;NtB`$S<WpHe@b%{K"
    "q7{~e#upi3Z7w6z^=dniJAXjRytBare9u?Dl6KF<$6kyXih)|xK(d@-@LQ-iKk3`PES>-2k0i@b%v_Mtn=_@"
    "llFzq?}o~a)7nkaTZE?ZntL}Y?6Ze;Zls3uDpTGrt4{ykwfX$x`avF_WGACnhkN@YYGvhi!n1HmLi*jN8X7a"
    "|+f<EI)c$Ep8^F)#gXF91jeU-uM4gOmLm^E$8FaXH?kSI0?%N!~;Po>0<XTh?4=@yzfdO`pM36&nDGd*4z%P"
    "uN-U~oNuJb)_>$s>?$G==*>1s2R4nu$0Kpr21Y`EBk)R;=Om?}G^YR&O_p%B6_4|<@_G<YKYvNSc+mbx@^x#"
    "}K0E4`95f`o*UZTur{T5Ed~n=9iAX?fqF{1N;v3ox`%oPad#YuM&=`pxo)ka@9&?$5AAE-=O+RfSIz1iQU~>"
    "}N6|2HC_ui})w9ApUb#4&)tKThJnd_ub36!)G6M-;GI~e$<ps-z4g$ISJp9cQrp>d=yMO-ld@5&5y>~GeTG6"
    "AKEhPSz&h44uS6>qj*RLHgeqzvxv_MkZrtY?v5g;apmF3TR;N?%`ce41Az__ews+fd(0F1+5tOME9gdl=V3>"
    "*c1Ob%XKh2TaiO8{2<l$TT_Q(4S^ykX+&(%we{4(ZAjq(pV*nZi@RVYO^;%FfG6(&Y>w-+{nv=r9ZP-i4p6V"
    "d$-!X6D!*DcrxCnM~%Tf|8x@Dx%9=U{=0rcp_@(Nbtm1(EYc!d;PQ7b;C>y@x&sXWL}w_-lB>=&awH?4=SDB"
    "Vi|&s_=6J#Rbh6(7p<Ssn=e=9uo?2>ta}*0<Br4rZK3%4MJQNbasN@XaSJ`Y0G4>UwUJ#2R{sIDw(|YpkIhc"
    "$Gc)W!FsxR%>R9%eSu=T$+F<aBJ3btOtsSf6FBe7=v>7_)Uc$Y!CiMJLXOJ-e2>S?UEMV!CJN$J&j-#c{8em"
    "H!FY)dgQbSgyYrbd{$kUrxiC`w8&7_4%r@Ji?gC;>^$<wAp(gll#kxkg+9Rzg_#Eng-^r4Z4{xL)Ei?seyD0"
    "=EG_RQ&uR}Ac7dTBgiupRDgw8?m=<@KrcqvDEQFteu*J(&^}z!!zAk4=n@?BGd-PJ&WB?z)eGZ`1w-z+S6$U"
    "1_fXIhtR_|ItzW9wGH<@`~6|3nCIy57a3#4(%lvmZ&72t|gZH=2+IcTK5qr4lh%a7}w+YRl6hw^Zo5o5q$=<"
    "p3BAUTGAZ#$kc^K+lq)p}Om8yz|rqz|~%^C^JXXD*fcljEQKH{dtk0|sRP%aQ8SV;1cRRovqv%r#H)C-v&$x"
    "%FR;(SP}TxiDwq&QRl%!4o+q5W5rmm|%xs8oiqW`k=61gbJfAINRGfdg909%MJ9~8IOTZ2>aA1GL&XxuL|bS"
    "FIOulx#K%nKWexZd7!;EXnEy3F7xaJ9TEa;0?$8weYSu6<7j+#vUhZPaCUHfbjlHL|4zW#*WXYGoL1U%j=nl"
    "Mesz30dNIg81y0kmgP%r$Cv|`CXn%BgIC>#|sKhM;ok!&T{?q8>;N>p|N8jfS7yRk)c>m9%7fnCE+&egI{?*"
    "QnFGx<&PN8|0;w{b_f5(M+)Exa6OwN!mdDwR3sY$@_m<werlmxv9RS~VoCru|7Q0K+T-peyHBm2e4Xz#@@jx"
    "f~&z5DPoec#^c>B09$FkkzXEXmfv<X&$cuaAy^o*pqA-|D~BPY0u)A2k@>>Ak5?k-KRBhdn5@9iNQ;{q^YdY"
    "?pDPTT+W@_xa@ba5Ua~efGog$-&t#yv@Wyr1gf{UHHMA{)40agI9Zpa2}o*31#@B2pF=;1fUE4z5*1parqI`"
    "B0zC-&Qh5=j{4)Cnd=D-xttYz9qDUqgU;9G)e7}&0+~d|DEr@n!H!>zPWH}@X*dx2bPwtRV++A6bD0YW4G#="
    "lHW={q)!xYovj8<9Lm@W36LO9NeyjL7*g4s`?d_htos;SpI-J4PJYfD#>UvW71Dq>TTeu$C-{UthjOW{HvCy"
    "R^W(cU50Nd~h?!M2U!1@O9YCh4k5@p1<*LOx+-?Kv1=vhb%)c%Y7<`@pYqht_Rh!r&q0}R_#qA#~VA3i9hcy"
    "3gUF_cmosXhekp2ear37;J9xxI#uFdb+*Hrq@~h76_`^C!`D`x8bJIj%Vf#IbpmrFp>A|6aQQ@eAG$K}H^C3"
    "877iTJ)Hl+8%Z7mdkTw(|M#v?6dd+Ie8p%Bq`<K6F>VN^zcvez{Z`IaZr&WKaSDjZjI*LLu^mt3AWi7gHl7x"
    "xU3(t^$qER!M4AKJ<q_9m?>p0LuA|;7F3XzKiqDmV#*uGGyv`myZ=r|y1ke0$ZyFXqCF3U?r*f;2ps>JdyQ="
    "Yc%!+no?+&xeJC@r|H6bY>Sg$)H<;972*22Zrkt{TQBYWH{7o&e6Z?k;58LjoSdMLow?2pVa3mXRLU!6h${O"
    "L)BS`It0cF7~rL^akDiGSqqXim*J$b)@q#y@1AuOJ}_Q@0xZQ0ob_8x(b*e!pqTLJc`=i7EYmIL^HQY#BtDC"
    "dBRCnY3cMlOrhDs|NDsdj$uo8r!B7;^%I9fYP=VqYoOgwN!ss5`OIZc&K~e_+k>{t?Glxz8)?!G+c{ALwM-E"
    "3;=fpB%HLbArs5isI*(dav+@0k8v#V&@+g?^ET8pL=?3Xk-qg=3WUWR&StMGCQ9wFathHZELagS*@s_kH^)#"
    "T93z`)h|lNs=P9q!|JY|?Qd4~VnxZS7*Jq0QZX%-*kk~^fWk@IpA|+|K=R!;_W8%qE$}%8znymf9D#S}o&zH"
    "!XS3=G)J2*4)&VYPnmhzediR^*#q7QCVfR~kA^BeXwDZk?n_5&r9!tXrFb9;zIW|A+9qilhcODUP;80)Xflm"
    "3e8{qBy)yeTs2QNk^r@9^>wdl$sGW5<Pfqyw1)h0l^eM0*H7x{ajFM$QdEA&e13vd<j3U58tC5zdtxGCV0rl"
    "rD*m7QUfjIpd!2Rep0k(GLP=1^8&A7*yhP+x%&JS~MTi-Uu^^0(J>>NjVH`UH<?wl_qtKS!V^5P9}^V?z{%&"
    "V=vLua?cLi}&!uLztRTTGy}>+jUMMk31s^$g#}sW1i7wqKZPBwnZ0VGTqAPutlw6a(WYcb`b@ppr7p#XRFQR"
    "0mufBm+EVC$MB3mbRXvH<Zm%XBOeyE{Sy$?_|N)!v#w_D<L2B<4vQP;QP6G|d2eZ%ru{0Xt`B@AIQM7Oxm@+"
    "ieB@u&cT3ECXUFOMF3$`duNN1K*+cm>{O@1w1Ulx{|0?IWMrNl-Mwp?`%aLCI$HXwm)|=(5B$m?e_t_m@eyo"
    "6Arsm95hN}J>&j|fguct;u!n2qSGZ#KE-<ui6-{Z9DYZ}J<N~6*5{|f4Cxmw@3z=Dk^BmxLbci`uzxByP){_"
    "Wej{cN6i|Mp2A%#Ky3yXy)e`Ry0W;=Gy}6U<f<6(5RfhGi?+`C`G1h#1r;ep^uJjCO`A2bY^4Uji(>{`GQJT"
    "qPHT3sp-jt4-Zc8b|Xl;~nlE*Jj(#7avnsnA<lOaEu^96A+4%7d7ASnn<BXD|N{Rvc}r)wWzhJ%goB38{;SS"
    "lP&RNn)b+^sN38isa{iX+D-9Ii(0laqR_3Bb6^xtN+dradu|ZC&VbK7N57VEcHB4QP{N1HCXsh7K}hgi|DrZ"
    "}petg6h)3CJ*X_m4yDyjQKm~GXBQ?ZhwNizM4|5e(YKejSSsQw4WUMfO)zt@8^~fyrcB;3soPW^z8COT5Jm_"
    "%c<@gd+fV&}F_At&g`ry)|Yz76tJT>Xo4~IHYUdZBBU3yc@$O2C-;u;Fw=3rST4m~wfv^S<WSNqbd!|&#4Xn"
    "dzdlC6o=zK+OENf5D`qDV4G110_)9x{ks(<@VYhH!Y*4jfpB6Gcfe0gOf8bH1r&({W|VNE&o8dx$v(tF#{3g"
    "@Z1ORb8qik{qMeP9yfngqPk9Li+S<v3Nh;EIYx9h>Vq+JoS!rp+063s2i0};<~6&pmjiKvzy5ZI2;?+)E{+K"
    "_Up1(nITt3j(7g}&wuyk?c3YlyY46R3pL*Bz!=^8&L8C`h)uvFx>Bs>4m7$($jdl3hp<{LC^_jXAcfjZ#6Oz"
    "@u}t89`-|mW#?Ig6th%TmM?^V*t$O;QSYZR|+7;)Ut)a>?rv*sgaiYaV-REh&fiK=+&H%PRtmgPH*3!xs?rL"
    "QVnI!=R9qwJ8ePuXP?U6x~rU#<W-OhKiESv%9p{F+{5@$2XRSA=c-q(A2N6ZcWH+M?q5N^*&Gc?wSdzQ<ywC"
    "ShDI`STbjTMGUEAN9F%(r&l@J#t7-{px85<_He;V-nzW0KRzh=VJD1e4!aH>J62_|4a0aRQnw;lsMZoX{!QI"
    "X)f1TIBk*&S=EZ$0dNQb^&UQROv6X>`<nLe|3F>&L2$m;|PXzzqs+as|Ae&->9odPnS#RlmD}sjr!Sq;-9;5"
    "=n>0FW!KH7nG=v=&AH?DY0k?Re8vA_nfIJn7k|Z;w*E@n((--6;Y!d1%ewCjh~0b)VA}9Z?uFSwfg(Zx#l8U"
    "LE!;mmpl}xCFs-0=+Z`?LfoW8!_eKV10u6SNjA=c}uMnN3b$JD19ML&QJKN0dVx)Wu)urrJKcUbO<Pd_a(KU"
    "e<{D{>>w0A&SDMWh#B%fRE#lZeui0`K=hoKRvx(hw~<f=F?9j4;6GV%<;SDL&y(XasFARQ13?L?=}eTz$)Sr"
    "W@ZtvZ`~D|QqleK?HZ?7=0$eu2>swg>p@I^lXd(<CPfcVFnbD#$)&<AV*K<Y@LH9?X9B$D+4MjzB;0?erm<2"
    "OBsnK$<4vn?Y_u{`bM)WDuo?q~By9`sCkk4ID}c#bJU%g<#OYyoyCw-EY3ce>m#n$(iFXJa7EFY1Y;(d(h17"
    "UG1|^T_zK`_jvaBLh*gSZXXpZQMvN0bBn1SIbjkQ&W-qbbP#l#Cc4Zr9lDxEeP`KK>gfaj(KY&qAhCv0KvTD"
    "LAHlmgkVeP~_9WX;?*^oP*7qsS1sEvV#f)+Q3URdFQ1=L<)32sI1YO(A8Sx6xsEkHlW1O-y?0#Kc)Vs2@-K2"
    "z@dK1qQHGqsEaOIA{3hL}&3R(YFwOo>-Ywqde=T6s?*>X*+XE{68S4!FbHiN>H`tWz%kzssI4=?z))8nHTC9"
    "LnLQK55h(23hbn8mV&e6$5To8hOoPe574;t!rnSa7{6Zin()@RJ=sRCfKvs%q3sKvm@D=4fVhf4!IbP|P;Sv"
    "-rC&_)^#_gZee|;9PgMzFR^KH4wl51Khzs7!g(6TC*kj()gNG`5`Z4S4~fQm#{GfZFD?^<Gv8115HqlbwAT8"
    "aYm((V7o$lm#o)=>ICw0{1p<&)A3}cjwW^8ca`v$E&9K=3AvZsr2PfCH7DSm`IEReaxs+AJkG`O=JBCC^x%T"
    "T0OLUWu>2sa@>!vnkYH@+yGs1n;KTAfypY{g0;^^WMEA1b4bTF8@96A@ljBzh`{TV=2jf4Fe({c=_xtO!AI4"
    "|Le;yqLm+T+zy?!wo?;o5094D^oKGd=16>^GWg4*La??h8|r+@zRxE*VQkXhdK5XsTlz}cB461Pk6P!Q(59$"
    ")Mg%EDpV?QXczyH#PAcD#AyYSeDngwk9M(zVk8%>}g_{G(FHhk(;&zUx~%9iTD4?&i2`sn(O)!}fq>jZ0{Qg"
    "-+mz$RvmIN8*|wP&1@S5}Uy^Nuw1#^IKZ>S=s2`qjv(65$C=CDp!j()J5r3GW6+yofV=i^y{U0VJzh7ggXxc"
    "*WB**tB)dBRjEn*&p&^3fO^ZYMz~V`Rr`RPFAeGpOS8gAS@@9MN0RGP!#Ry7U9r3a9XJ|Dc+Gg7hy3rGuir6"
    "n8}0+YQLGGDb91N`R1t0RdbmhkA7O~F)j4chCNg1rpg<I`Txc1HjoYKzPdIn(w(#hHVcIyn*tgwyV!rj+I08"
    "(eS6^J0kY*DO6Ig`9#A$7$4~u`;BbR`@I;Av@rT`>u!|mP@1V=62eF)_?z7YQ&zf2p~=zj4~jPijR>(usTM*"
    ")_=;qiQv`p!IQ9EU0@nRi1c?Hf~nIDt+?Nqff60XYyett4_T5(Y7Bg8)ejN+$h;u1yKXKNMMkr|y}scE72l("
    "jBWNv|fG{b){>6fMCMd1k8F)Q70xFminmBMm3GzzPfbH>m^F2$1ZBTu*#bzJnd1)6+C(A5=RRRt#xoo@Bw(1"
    "aXlK_N{Cyaya7m0%9@vD#pw|;XgQTL&u+fI@{&Hxtq^Pi1o~sx$54YyIIS8bOG0+U-gYfS68Bq9n0vTB8t0_"
    "lNf=NNyrmR6ze)1=Jml~1y2<A?`RSD}cH6T>^5t!Vz6<uq;#9j^ZkFp<L-BceC!Wd>{u6HK?Q|#u+l35e(A?"
    "ab3OW;FTchFCZIV@wituamfvmceZ_M91x{_H-MlIu@mfNO=BvpRADCP5_yZN)bU>9GC?=taoNbptkeeNgk4s"
    "=dO7qeqqT{nlbH-kc-vD^|+1NIbnU*2^G8Tyz|4w=t6e<a-Bt5Q3OmH!Jb!i<*geWZJ<>)5l-$t{t}t&!c;?"
    "_%VeY17IMIVLjmRDGMK<E7p3By4_9z}(b5!IE#zWw-Eo7UbJ{#UZyN*x#xiqiGf+p@@UkrV_<`o2lmQ6CUE>"
    "UPN@SrJaZ3Ym5DbM8oE<DB4deHk3c|hNT<Yzrrgl)eaSH`xN1R$mz6O+bfSy*{{lBNXZYZH^D4#&u@se6u+g"
    "%Fp)vcJ^p@oDn8DssOvH!pCVOnq+N>ow=dvPd;;FT|4=@}zXhisT(isF@QF05g!_-9^$!}xX-*IID7q=<-jg"
    "5UUwkw8_TBG3#^1!ph`WZ|cc^wS@G<gs@@0B+qYM9M`0x^ACcJU>-JP>5b_}tP&3kD_l17L5nq60Nawzz37c"
    "4p4I58W2&(`@!8c56SHi;y1|An^(>(F>(=<s{+0NajDcw`c1)87X<ODuJef+fd_m5S&fC0k-NY%g$}#OaUy*"
    "r6}-ujVprx1$G<_S~2{W%Y4ocB|5l$MuYmec~+&oOR8fIZjH%tZ3R~^14A{B6f_aVLU4OUoOF`MBsV+9Ak7a"
    "XKfq4iG*5iv92Y&bwM3U;yk<Nr#{T7ltATAZ6O`M^agUN&9AY2Ja*d>|7`dMDvCUUb*`3PznA3JLDM)O`TuJ"
    ">$j6zjl}^g>7&-cVftEa>sXLhQCkP^Ob;#|v-}P%oF36~84qUjMe_-&!TB?r@UF^<p)1Kh%-e4kCR?<^HS*<"
    "<wV=wIlR?c1!Xbn@{Vsp^Q?SA7l&xw4tR%^(0GH8!eSl@llnkPKF;a$J`g8vqL!Ru?lvrD;x?JvK3f-&|6sh"
    "(zEz#?7FO6u8@@pojbzI}3^b`m>hayWwa7^k#o^K<xoc~<Tmxc7tDNBe)(!RrXt-)H;%Z{prX^bXIzOMo|fS"
    "jXeJc}EBtRLxn3BP<eW>nPQa+(mR%O|Qz|6GVRlU#^Fs6FGAkX(#E;#U=Zq-rUzGr^hFMWA5DFb2xv`;ru;^"
    "^Y<LiFPFoaC}?XOLxDi=?9vT}z*fr5uH@7?{+r0Cq)O%v>qABp>b5v3=;8<ZCqhl@(Qb+_l?dqG^?zD2VC(t"
    "@?mqVte~nbYNc4yKe#sQSkga@nx*j_@^Z}1aCIy$Y#g*fs&SMYj(A&}dJ@@Z-f6wo^f4}Gc{hs^xzdZLZf-l"
    "y7BEseEX>4PKx8@+QI>(3#3-INP*w#gqvDfoi^}ZAUd&Z5i&(5iL1+X2XE4?QG+<ErH+1aaX^8CX$&o8cv^>"
    "g+=g8OLlc5ayb(intBtt=3HYL@Y%QPWtd86aA1F~7^=m!NCk&O09t4}Z+F!ymKL^=4Wva=w;BmEFEkq`(7)N"
    "aIDFO(ukXJDFtX<wdcfHVrU~w{xBbH--b7)I4#1SzXC|a6wMWVp>~W$=t8~D;7v>0GIa6<4%u%8l8*|zCRl8"
    "eLp%n8=L8l|Fm~H8oxd{G?RF{`S$B?{$3tnuD@QdmxJfeaZ1+<qkMn!&ENmw@6A$9CjI6Se>{FMN)Gpz+j9N"
    "~^Fznn-tUh`|1sKseRh0eZ!lz6)ZLbm*-PZcUSMM#vuo#Nu_{;JW#_YE{vKJY-c4MqLm(aMkS8RQ<Khw&GA`"
    "m*-1wmW3MgkX*#iae1iRu)Cf~u;Z|54N-|&r|v`~e<cUf^&z`@fE0nbY_9Z-kw40+D45az0aE)erC3@}{Z)e"
    "lDnZgio--jA_c2wrNFXsM%wq26-<QA2+VezjZwHn*Ptd%Ur+ixo91Ajr|tPX{N*M?V?@jbM(Q3IKgZnh%~e5"
    "Ym_7;n;GGf0DLbtgG+Mi@X@U+<Sd^W~YPlvGL#oxyl{*FuWWOHvBaHY47mh#rX7W@9gy{Vm>_yB1YWEfIg_m"
    "(fIV2)3ec!<5wrgKfXHCYxm1ygNZ#wb}F>O_Ah`s7hs`L^NkFy<o<l<$@nh2Gv5$k7M(gcq9XQ<fryp_CarM"
    "q40HV|1H^T>9oRJ_4`IXD<D<i00K?0i9>ehgU&WZC(83ae8Ng7;356p+TdWZ2Ji7$3X5<o%z>PMsA(k|T7-Z"
    "f8{kK}5|8~ohXU}+G1UkdcEKsVuHkXb!b1a@3WdDp^!l;eZd^4N<OP;CArTx|*d-KoWqMTp-3lOOu+N?uKBh"
    "}Z)Pw2Aye)bYOQ$b2fIj`z#YQ4)t1EZ8D^PIB3YyiDyeJ6uMJhfOGZMR(38C_Cfe~aQAJO$<j%&m(Rh<=pD-"
    "%&Tz7DkJ`u07bkdNKP@j!8y#(4<l4F%8LiLP}o;IL&yon&l)4@~l`^V^Gyy`jG<aR1CsH<V1coRN$Jdv2Hp0"
    "S$F`u{T2C;-#&S6Z48o8o>8&WgP0*GRT;eDyWAP_6n_Yh2Uze8rAfnT*!A4$fsQZX_IMGiriKn->`GcdBx6@"
    "gBY?qAvMqR}Fo|2ESAhU{eBA1((Z&s%S_9J=Fb*R0j=8I|%L0V$93c5F5l_nSq{8U2<YNN$kX)DMJn8WirXR"
    "qD8V-c*e$7$c%vUtP43tGuezQ9ON5-}<6xpFZfU1eFx0_>1`u5J-ujcbdKr(plefF=}Cz!|mqcgqJKL*$biH"
    "kz7cnt0It9h??_A|Xnxi^L4(|KSw4L>}fH%)Q`?cpPzWj9Y{Zfn<Cn2h#+z-1=wOVS=Q5nN+1N;^)1Fz7Opy"
    "tGs!X(YcGbKdMr%~<h1;<S<H3==%aE@um13PFR5^TqUz6f=ATh<iTP<{KUwzvRE2ml?jLzz)ds@&=VJb8_JO"
    "ui341ZR}BS;o}4L7YJ+GJ3}WAs5+30%{%a%eAf4_ZzsQ{j+NqIZ)_t?QU%^VK|J@jPyU29U-pUbymy@4m@IP"
    "?#(|BZ4i4}Y<R+0<00a<}4-PT^e7d<=)*V>2u90D&)pfeLOl`>j+EpL&zn(;-dIFqMpA<g`t$+LV*Abp9gEV"
    "(|bI5feCYNY~zMO@_rZ55RgK)-X=`OAp)dg(nyEk9Idt>()K7;CsJ4ES}mLkiK*dB*ymXurvy&k}vLl*#xd|"
    "0fET3Dis4X*EBRv1nA1c5^OX2oCK+t;AJaYox54zu1j=r1+{{PU2$jaKL<aD)1bv_d5vUd5Q+7{k}<xqT3x!"
    "vH}M=JbXhKfveyzu7nMTHps^garCv`^;{On)97f)6!gGs@cM#Tp59b+C4dc2Yf5;KoxSFq_-ISr|1d~-h_Yd"
    "RG`NrpCH#@cXvce{@IK`qxm3|aO4?p+^tK~;8us<7#2CZ8I$(W(Va|k-Nhu&z6#l#+178q{ks1(u8ndsc<TO"
    "M{T_9B(peCzm-cDB(8i3qJxA3Gg+ACEhT6Hwgi@l+>e|>wtWnJ~BY@%bP9}7ICljk(DcgYqnK$pJ6$CV(uB9"
    "e512R+U^?31KdUizW7_+}drOe;A`oaitj-05IzyYo|WSW-P0CI7OK|^8{c%RF=ZUGz3vp<)2{FkMJ#0=<>sW"
    "~!RGS_J7=;@+C03KH&(28hTf^QRQ67;8D%veIzceQzYvOz3&9Av(C;y&Lp%BC(?(HMTeN?e5j_LPFZpu3d$f"
    "5jotA=!6bwVPBUJ_zYJzh!z!rp}Y|pn-44ETTBpXM;8Du}~M2OCh{4@;G?50ebU>`iyl#g&dxPy#w52Fc_xh"
    "R?Rct)5JMI+Se4C2r0M8&}Xyh_Xr#<-EP$D0h;Sh$3}`&&{w85y7&`g0GO3stnT_ZW-{-ZW<zU~Dr^Mt+PUb"
    "WEBgXom@a*nELT*loi58!IqWvnD(d--3v<v{V|2uf*$Fd79>xS*)YoI^k2=3F?5p;&4F3Q2zJ<AsBT4hG^vD"
    "+{Km$OMZFxP=V7#;l&u~X3wInsZJxK>NfhO525Y0scqPaT$_scII_2>r($=cc7hzmzpAkbZ1U6qyZ{IUsgjd"
    "c~MQKL82w`Tv+s3S4kV5QaX)YU9K*WLN-Hc`_LtNv#A?8%dNtqm?*e+w^fJR=J6vhgr>2h`&@j(ZEM9wy%XE"
    "xlMptyDi0yi%r<-9zF^)S*YOg&?JWhO89-UtU|^Rb^uGn4_~SMYJk-z(R^Mv^x3=FWm(CD<66i_H)|u(brw*"
    "XvD20V`;NK?|<(OY4`v~&rQ$pFZ}RhmD-0gJMSy>?W7;vJ#2b<lLKj`Q3BHru1LG<RGMVP4WLXh@(s00M&Ty"
    "CpV;~U_r7^L<lI3{ys;bwJ`?!HCJ^f(&_D3tk`!oKJO1>PN1-?5AG*n(lBYfoF@BFH@(OhMWCB0cWFpb-$pm"
    "jSnb3M!8!f1jCoF)*zvk->zj1e$psPzy3SzDMnK-uS_48SBp8pD4jr$uTFW)<yep{Q%_HfgG_jpiC)W<xM)p"
    "oa4Po!^+`z3slpX*utLe9AV?_m2oIoLea{MYcS{r&x6B4cbF?zIJ548Bjar$VvkonT$Pzv+(HV97}SEySv++"
    "f>cAm)-K8WpUl3iaU*^Qm!W|41JcCQ8Kgx=2a2sw4BgZ_#`Fyt7K0jxqC0QT5QQUt6(N{NC&2bWu`wNK&S?Z"
    "=6Iy5C?ryxH|J-FjlbeV8hi^qj4V(%++6#;RWYaMhND3vUeRqtkJ*YYqUrJFF3SUSOvY7$xXU0c?Pyf{zUwt"
    "yqQ=2*)7FE5TU2vVHoe3$T_Hr(|NqM8Cn}#|O3rUoN1Hj~e_gF~vxu9pzrq*9tW#2b5Q?Bn(*=8xBMtQ?eV-"
    "*4bfWPS?HO%8umCSGJlwjXtJ0kJ(C}=XFK6rIDg$51%PTp2({gj2tv=*ZojN5!!DrJ3!LeLzNZwq$U3RAPVp"
    "cwuKg-8oKl%E*{*&+fU;m+x1NnzOzePVU`(;Lqgl5&p6Z*jeuI5v?OQ$FPD|(Iho$gdKPJ{$XNlK*iut8$KC"
    "ZnVa=)me<#077caz*9d${P)mQ+gXx+mX(~{z^^#TNRs&%OoWox>#iwD?~l`AsGXh@SDS7iL@;wTOh;5UQDxS"
    "V9j!xivIp~=`P?FcGsw+(AlLNDlRrFy4;veE<+HRT=Om+Ewjo7Uqfx~OkrK|>Q3msY}!rc1pr?pIVQP5o=Ci"
    "9Cr7`$U7Cj6<Nl>9QMlhOpCTU4$S%V4(*+p$ZU3A*RVk_6Tw<kW>9Sbn$O#M^-XR?&Ur5XK>5Jp>-syOMiZ^"
    "9P@ru}K|Au&1aYOfmiv1`vdJ?~~WEOG1uQTFa%Yp~f9-BO`guTTyA%1!P_^DQ6(t>@>f&F<h->le1kf}@H;5"
    "J*+FzI5$tx=KGDu-pB&2q%Zdr7gFbA%{gl^E=sLE?PfOa!3Y>qU-J<WAYmWyZ3L=>mKQYlf`EZ|UxJafO#eT"
    "xF5wS2~ovx;<D*F|ZDjlS@0*3szUe2Oob);}>!-R`~^OA|1T<pogO%%V!{iDShC?PmvD#Y{2@tX8y7|2EtIW"
    "jETgf#H)-GiFHnSI?L<^Z^h4<bE~oRJfm;8OoW#{MEO~Mhkap=nI=(>KTVK$yTpm~t16kkpeyO=$l0kh{Nd3"
    "ls{+H29V9sS^8y^TpI$5rJ|>;i=r*UFP5oj^80S)Z9d?a((6W>8%O2{f6%N`@kSQ<EI{E8sA@bymG|n5#wCc"
    "qN4-}v*mqrI5E3u?>J-Z}bkA?#-EBjritL&WKgO2Vb%+D$xmzV|dT)Mj?D?pyDy+9w*d!B7b+d_O$ADEW)b5"
    "37^CP@6tOZ8DIm!H$B@M{&EWeu)GL`~=TtYn|I1Z}&Ykx<K5&5DKAF_BO{o7tr==po!iv=va+ebtlh;(F!zh"
    "D1|Qcqa!m(L7yz5wL=a`^2BM;PVOWiC%JCK;WD(EwzjmW!UMM;Yr%5ef%#({QF9zQM~OJ<K_N%fS6Im0Pe#_"
    "N+=y55wy)2r|g3dxyIx#($y-@RHql>zmH?k5zpp4l4nf@t6&_AX>B<VMS=4CV46apzx-wIH0f}Aa%WrOc;Fr"
    "AJF$T54^BiayU&wp!@SZ(v2<gr8A%WL3(cjII*!{5jwEU#h((tqYG)=Bx`S|yZJl&dz&r9i=q1J!^rSD))Ej"
    "i6F0MriZ(w{A=34#EdOuFG^K&{X6I8(rgO2X590>n`9{!9~9Jw>}=1sU~MwIV*5$)($?{*?OmMRCNlSUK=r9"
    ")N;>`<13dA~9vKB|T2gbmz0T2UFNvY>1g%bSxCXj0_=3R>GOe=Ofi|3`dDCz(H~S~5{xOb07&Z1n0fvc2F)b"
    "H}ULjnH}_>0)G+%g>|4UUav0j$A8To@UAJZW~<6J9EO0)_hFP`9R!`_-f}&`bU^#*=l|3eM`EO-m%#@e%+hI"
    "m(@`%IOU6H>ToSAtjQ23@-&xZ${81%rBkvds(y8dK@KC1$a7;8P-!@#zcDMJu?{C%^|FX{HYjy9y-kMNvl}^"
    "QT1f}648$*|%1>yhi49dw>0sZ0e+ds_{Yd!>n+MECQalCh)6IbNTH$an_D)2Tlfo1;QoPQ@uo!x~93puVTc)"
    "McN@xZ^S5S?&U!0$Fp_5>5%0Pc6{d$NWb*Z@)WlcP1vzRAY&I;)YJ%3|`({yd~y`{@i<i4bfFG$hGd#>bkr+"
    "xuV*X8k-to-0inv0(mNI-@{EhM^;(rWfEu{O@Ik3H`Qnr&7LIhsm78Z?Oy`ev-JFoVcyIu4|bgSKQj1N{*D$"
    "#C~4<Co(Xr|jm^Lrt&F_5uiP&_WPm;=tk%`z8=&L@Ty$Vm+Ask@`Z<!dr$sX-*~1QF@SUuAOnXu>6U$+hjU%"
    "I<lRQsj8IrPOSQ{E}=zfVlJMc)%oH07a59o#P%ObS1iv&P~E^+LZ@#qKO2yNxfBIWYvi-2ucRzrf_iZF$q_Z"
    "{r=O0Ges-2rnS^25w+~*9e>zS6>FD4vX*yHM%{)0er2h{@_)eTSfd6)o&nu(-@|W@P7?;y82Petl>z6N+qvQ"
    "SYaq{E8U~0up?m|J`!FfiCHOa<K?37WSqRunt;baFIjqnDZExZ_<!c6Hn_kfqC<$4!zvf4gv<72{T<;hwo;Z"
    "@0ZP5f;aYHYE#O^m`C`OW6GQYPEnpJZ>t#zF(?<h@u$>zmB_Zm-3^!o{8?X~a0h2!C-~-m;XJHo2cmYQA6xb"
    "=4K&<a^F0tKM?5_wzVdis!gjeL*}Jm_Z3w$~@r=0ILUeoKqJ)6bJ07!Nr?p{%@OXi*Wc4IAVGp<cl8h;eqHg"
    "{4vs9$WRULOUnzrsd9q09@Z~*PJ@BO4?$e7zz8(!Xk-~d4s^p1{tdBnbbmS!P=U(JH?j#1erZBh#}=oTJp3Q"
    "5q+}1fG|)pm9S<ubd^%I{cUQui_i~$PkHK{6v0b~8_rBp0&q}sD$J0b*gb>FpW_R*K$n<po+0jIEsk6LZMWw"
    "gI_&8E2X9P~2DLmE#$8M&IY_S%r7M?@Z@8~FA<y;yD3-1En52wt%ED9B=X98zaB0*ppQot1X6C{_H$uzXb;q"
    "QH@?>P<Zu5v<4F_BYBmrWf@*p#MSIMq{Oveo*PH(_5ezX^&e;Y(&#VDTzC5%As|9gagiO9M1h*`*0qX4<6%<"
    "pTR)U9_6=3|1F>&|GzNm8Gg_${rbcE=2xc=GV{{6hsM(H(wGzDp4p8$A;*dksraFT?TO1pDj3J3<-@`(xd~G"
    "s}zm~{>93fyB)b^SDSLJ+F$~h`6dSWsr)flm4g?gOysaD=ETF8nySZo?{Gh63$ANBxPs9wbA}(Hz-q_+*t3("
    "Ptbk~`Q?C_}6DMbtvnp|>JSJKQ=;n_W<n_ckX_}7K1>2rx`rA<(Dv#l#hGg{mAzNj}5vJ^{K1*ls8@(qIGdV"
    "asIoKcjAO#ya*F?9WQPBCR|N0O8r$i;^`LA7^39>lYwaD5yL@_I&PULcpoTYZpHE1Mh-zdlJMRDHsY9sz<fi"
    "z83%?M%|s!Gt&x8i?RD}ouajmB_N0l~>8VP;riTf=U+J#n(Uf8_mJA{iPrYu@`!>cJY$5-S&32FL&|b6ymM`"
    "%KeCl)YHwv)kxB)Iq??rL*7R8hE3rquhMe^i5S7LM?IGqQQpM3H%U4X_|<tg~+(&i}>{$Fz!k1F+J1b6y391"
    "og2@i#U~KXq#}2aYuzA<g4x7yN!8n%Vc4SAt>^r>Wo~KI;8&up?}2))TH6|k`)Gt@UFVLB7@A4}Vf)VICJ)}"
    "F?LoB*0&((uxd{-4oZn(pKO)hJx(jz$O22Rcv4pGPUp#PPE6g2io;nOsedb>!AwL=_Gph0;B&PI?zt#AkX#$"
    "$da<i;)y<U=EU1jr}t@aw|NbV#&$B@IpzyWjSO1xz}8%{l8hrw0Bhcdk=k`6OFi|+sm2h6b>j|E4|W%?nrj3"
    "3i`z+!7`kp9_lcr2ZXcO)DOJl^wQaPbs#bv_t0b_ue7Q2JtAnf))}Sk7csH!yo&*e!u@Di>Rb@5u7#Va!QBk"
    "+bJ?>EYJ!LV~A;#fA2BmBQXbLKo~xCokVVU=@hY%~i&`5mjoh6@x~2ABUuALWoT+CG+WubSNxQ^+M>K*pVQ+"
    "D9%bVIMKyg6`2}UHL#1S88zC*J1Wd;RQbE<jt!Td*r@s^uo4?C_Cbx29qNJqu4!}xJp8p1nrTRpEEd64_^aU"
    "}9~|+Q`tMpAq*ShVU$x|ER%0r`q#Ay09K^JzkwzIiRc#Hfj0@2Q9KUQwq|_`!4MM_!nN^YrcjciP{Rns{r#)"
    "h{?)^MddvGn*|K$aumkX>QErEj~-Z1vNS6Cj&0A?9DyqAa>e+kh@+D)Tsqs{pi>))a`4O;Z3Zfsiws%6IqWy"
    ")?CVW~Y%_4oTM^<Ee&3nw#-BH%i)AzK<+_}&~RJl-rT5r$CzJXbcX9+>Az0p<S&d2pIF>uqWkMxk3hU-r)z`"
    "Nid09qWkyK+>GuLh?XFy+(@Z_lyoie>z{m^!WAR;lbgbr+BzL388Y$2;;Szi=H6DP>q+Wlhb0|3t*bTKDVSO"
    "9X@<l35;A6E``h^?!r-_;RwX=`im^(`q+8md=Gv2Ev|@N=$mK~7B82jpK+22-DSaLJWm~~XPFC;;*RXOzO)8"
    "~1hM2pk<Uw#tji5ziJO%ZpX_f~8J}9R=6nU6M+<I6yx%x)4U2uJa2S-Z3eV|_qn}^B9K##kOQt`*JbLk0{)l"
    "m>KkXg7gqxcEB?fY-c}=o87n=-;A?m3W7)t@Mw7nBY;S!Of0wJbZWIx6Jif7#hcLcITy)R8DYc#56eGGJu8%"
    "jW0IHGqSRB`63LF+1~Qk$w$D&gn2?KhtPK+4c-&s};7ON_#x6{(+#V`k36Xgb18sMk&F_q+P~>6!l$>t{Iuf"
    "47D6O98!up(B-ApR*!Kc87A2rUj~$_oqu$8Y{_k(LCeQge^)#Z4v#l#i~NxP-pogWs!jbQI|cHy=mH)An?y{"
    ")+!}6MY?gnYI{WsGpK!0-<9_KX!t#Eqe4AR7f9#x71+oe+2#v$Y~;)VNx)?8i|iF--pySZ0~waz_Md)%5<aM"
    "qY@+$xwoH(t@c((XSf{P|Yser8i}UvN?=O(<rk+%L3szeuiWS{>1B8WMz08D^$Y7W(i<_Mi>VB5upPqeSrod"
    "p2<GqtHa7}DAI&`o$D4clujQ0BHz5g{i9-kf`jDdRiO`!82GBDvioUG~SEj#nGp<AI!(SXv!D!p+nC;1+qfW"
    "Xm%tAaKYCmrVYlFoQCHC5vJcFJ)8r&CD8){=M;ur&$z%faD^OaE|Te0%QU_!ol!N_-y3nsi;PABt(1O<%L3%"
    "f#7(r4Ofofad4R*<v#{gPbvW@%Vq;lxu5aRI(XM5534ZiYD(0>^n}LxZvZdPFD;pziX&P9UQq;xZ$r4sBDE-"
    "IiHizC>TQmE7mV=$ZG3vmNsEmibm(F!|yI>=rR;?by<CafEnt=_9pDH(OuzO6IojTO}f}@v6#D9ci<S{1>k1"
    "}^9w!8NL*R4IvK1pASqQ(zFEprH>d~Fw25f%{$K^|`}p`YIXFB$lHr6f%MRO^#uX>&x|{rM@8xTv=*~msNJ7"
    "XDd&v)RUyF{Ou}*i8mxW}}bh<tuVGePu+DPX*SfsSo9Ky6rwrsW5iz1hI1#X6~2+WESrc8LMdi+(kQgdNNHu"
    "ZJR)`Hj);&afyfRp6IfqLxqJlX*m+4sRZl9?|I253L!McfNTo<EX*LRn!`8M#m4UFI8+e}i8z$r1k7i!1c9Q"
    "OKtTbZEnpJGYS|w>|NOuzVqc3GCBO=-Q^At~Wqv@HLSRe~iVlefHH}9WD}n`#`I<!nO(l^QP?z@WuwE=xo4H"
    "$>#z1nDZp)THz=6$6c%g7_OBki<>OF7J@A+<Uva@3?y7kAPr?*uH-9Dh5<9V6<f{xrP}E3YNI{vq#WS6+5tG"
    "y;?XoV%Zw?Cp4gr^XKtqph034lP^*$0j;-fi`<%SmC$-jrx+N#$Q?*V<$wML=I?^JectUvh*Dqi8l4^S>OF+"
    "^(*GZY7;IERs(6bTgn_y7-0)uuN29-dmo6n1vdj~%w^8rCo89^9#Nwf@Tupb)6z_pzpg4`>=t%#X+6B5s_kJ"
    "<js>neF?2}ei3y8PY2$0#+SmTw_k0W}}zxnSUxY{7SGVb@A7LnX_>kAVw<5v!d}+7Fa08l8aa_+0tHDyJuSi"
    "a$a5l30G_=&*2)GAQ_PC>wH6aPir5Iv5t#M(9R)NIS>a!_+=U&O$)ZhBNU9NgW)L1XGeU+N#Jen^ZN1-jGi7"
    "bHwvLJ4ufhr?R;EK7psJw%W0P(l|OikgSf8%2mQTR)vf~YhYRp5{Ax2;AuJUm)W|f24Ony0~S-dDm$eSDwL="
    "-oTRFl*HdL8gTWxFoLDUGRP-Cpt4P^tZN{N5FhVL?vPUybR}0X$wQ%FW5;IQIzqL>V3-^jK7J7jbX;pBgRf1"
    "fBp_W4$?Esga%Mxis$V2&)ZxMG6|4lkyP6uc1lKyU)70<OUTy!k?@zEnOvcMscWHNa4h!;rG$H?6E8fL<{+5"
    "K6*nr$#WRjSp+L>8wLc;>!|#JAEW&oVyA%9TffKaQy)mVKN^DX!<u(na;OrUV$lTy%q7a{45(<<jew$z?isT"
    "CD2ImVbi?*4pfaF#krcQ~w~%7a293X%pWj4lwPq>pKL{(}Ij(PD6>ZrOBgt&Pn9U^&>SaB*4hh^pfG+5vap)"
    "la3lG1F-0}E^;8ghYGf+*9)Yp{%TjXRRVw4pQF-kl`gm>_}jkOSSbAU37Q}Zaafwph;?G}Wf%aqxtxPkv|HW"
    "`l2o)^;tGDqt{OUng*L~PvG~VtA95nb%}@-$h{AZ8xNg(-R;d>U_Yo-lkuqdYqmPKZ9wpuu>PWOQFiF@9gnK"
    "gAvTK$^2>M!rM@Tc8ugf-^Gmzr<#W}T}zeu!)UZpn7i8s&AHtW7k>YS5(%qdM;f8k73<0sq+M(t8ZCPF1xPP"
    "3rQfyka`#dAc~XTJ6Z^-XGuHH=HlJ0$@#KKV=KJ!oN&@uoc*-P$nUTVxy-kVR4YORpspTGhX6x-Zj1gl>MB4"
    "ofdLHJFV~clvlbM=xjkYYk8h_2&yS!Sp%0o?FWT=faLsiP9U9sRFPTs_&u-gt8_;sZDPh!fo4H0KR>o9L&=9"
    ">J9SH*iRf=C40~%x}Z*idD(P>^U-LBA67&fu6xZ5bBL2H+<1*04{LT@MR)^g(655AUawC4Zsd9HZtHT%%2_s"
    "N_;S1V&e9`Awx(`g-t$MK@Uiy%yZRd4T%y_Fo>ntUd;taTn=@Up(u1bVGw6xJ_Z*snbj;Y&oU*zHvcORG?rT"
    "-~g5Qo=6B{$!NYTCF){R<n&ZScp-IfHayORhFtj<<h>b7*-#ew{)xg_qr<4*~@9r^w0zVN_c^<tFoV?mkxK4"
    "G8Zr(1>QW@&OgM#(x{Eos<8QOzrHNJfbp=PEm4<kFlVy5Sk@a2Z9!>|{tN5X!^5m5i0*oc|Ifl66zfVWCwOu"
    "bti)j(4_7m!y2~+TSEzXV9b~mNl}WbXxGH>ZZ%3iwkq$Xh7ABv6D=p@L5*H2l%|`e3G#hB-l7N+i$hG%?_#B"
    "-9Pl|7B7EWw|G@HO>Dn^*v($w@}bF;cLr0_=rs%fhi+i@`&aP4M3d&PTm1o?ODT3-C$cnP+;={~ThOgH;ce<"
    "dZYE#@XsR18@)6W8<hSbmeaH5Kyy3^HTcaJjwbJQTT(orNIm7@7`1F%I1Dk4~oRjwkr?;(NFAEM+64aC(5{s"
    "350y&!St(VfrB#J%^?t|Lfs!Ax?rTJP~$FX9|<KGUp_U{c{F!5Cl4jGAXR-K$019j4fesSbdJ>~e3KioAy^y"
    "xF&wVYk`!PwzpQ}><=Q&m63dBK?N(Yp)-4Et8s#?R^My~S8ECu)=ZqeBuQw6pp7tp#Qz-vk^x(%C(*g3q&QQ"
    "3MR3LFv_KFkjyeH6zH$9QOAHc_>%uJX5H+tPiuT|GkUiO8QK5$j8+oBV(lR9XRbqDNV3%*I$#>B#IntQs-%a"
    "Lqsnjv4i$)TvxNqobn}35J`k3;X92sX6j;B$K!u~eQ-P`{`)?=C1Ypahs@;ce{0K$7oHI#AW_Puk!Jm<qHFf"
    "H8lms=YcqnxWaf2ckI|WC%85ZFi5<G15ad?{SL@7NlVDA<Io~XFJAv{e6r0UGG>*vNhvp$v?}Xw6n#mqw0$T"
    "09I_=zsdp${_c-aa(wG0YHZ1r9J`<%!V&B|Tymd9KRa;6s0vo{0LK`{uIXn*U<P}Zbin6`t0C<8xCIy#yzj!"
    "Qxlf?tq1TiPLF2p{g4hUWq$2j%2!d|Jh9up@p81k6wlUO?w4J0&x3Msvy#s|7k)$<2LPk>a2R0v$`nATmdR*"
    "~_AQS<+vmcnK8!oHtx>1S~a-)4-xAsr2}viK=x69>Ezeb3VN|jkiHErjnM@zXZSMg(Tip4d;6;#a($Q-tXgG"
    "-KY#%&!?M}sML{GuPRNKTyp1FvbQOl%<7+&A<Y`(Y}55^X1AEH3|i4-#C?jb^2PLNNQ8%<AF$%vcTz<w>N<Z"
    "HYvKndl@dKxI74ag<$HAJf2cYZJ0kq)5QPd970XTNK_C63f4918Q?b|!0iMrfL5G)(Gbv*zjDf3pR!JPGuD1"
    ";6qZbwH%rOZ(#j_&#`j#AA9kh)2Lc2TB+ezt08ad#E4a0+%I<6>AJ&2v=A)WcFXa+GC`V#6W3Q!#Qo-rm(dz"
    "twc;$D~y1I&oDFMz#M(IF@N<~wV(u^x+eYf)k=5yjuGgPOh>dP5sk&Y?Z5RgFC6TwB-PkY<!4FN$gG8XK2$N"
    "8|nR-hPsvBk3qe=yH1F-=J^i>LO9836Kd}oQf9ZHP2APP=|G(X6Tkei{RQy=a!!5<t)DjJ~lTC4_w4UBVa?C"
    "=wD@5wAXGfQ!UoAGB78Zm7-9Z%I<O1B%~hNgT|1|<oT^h(}NZx2b%Llq*P3>da9};^FDQ0cTWEKWzMDAXhz!"
    "y%wm#pRm%F79;bQ<v0`EkYk`Vc`Y48_0jb80nEq4(6RcnLD;9xr8E)m}AZ^5}q}`iJTPi7Di_6e}1jj^Qx_b"
    "7W1Q^1M_EM4oJ)AY8cn~3c$cqgCh$Jv+1#*(I%1SYSO_Hm8-siNknX;SIu!FoO*s!8hY7w`*xx8hSrufk4>3"
    "3x4+(3=g*x=lz6EP8K^2d<chjmwLc<t{=^0Yc*lWI0n{mM#~N#smzb)>dkSoMI#S83tBXI>i8avd1}OT6Q|f"
    "HQ0vIbczKe68R&On7M|cyGp3&rB<nOZ_KmR6l%K&!khse%M9H+C`yi^@MH7k#C{Id#`GC($)3)U}+qV!j{3K"
    "*K8_5R1Apr5gMI-6`t_-bo!lpuir;MM^YXIC8d}{fQqrGZaoo5DyN!NEtWkvVtqMcp&SxkDplxhN*8AYH;72"
    "*W)OsH*y@Z24aHE<Nj|hrsi=7i1Z9GyF6Vym3o+|#42yo2KFB#qkv=HB3)W43$}g-0N_KE-il!40;g7-BZRw"
    "gVRT3q=7!r;Fq#G7XFj7TM%xc}gMv#i@<G7CzKmavY$Tb69C44_{EH1gDg942Fwt@-$qbS|SRpvgH8Nh^#mH"
    "$yO5Zs@eGqo|?SIAH}&li3W<fXblHk*9Dt<jSBmu|1w7*Jf`<t=9YRdNcf5~Ax@2m8rWZF0ftg}i}uNlEqs8"
    "|yV)36+NHE(GC3S|NNTJ|R*{iR8ubkW&c-^*Mu};aho<79OotS$6xunHlAK)F(_{937tS9UP92CkKZIrv^&;"
    "z^!f%-4lAc7TQ&oJ`Y^^199NrOZ(5Dp#s{a%r5f<E-%W#IjY>d+~`2R9VOOxmwqm@HPG@&Fu$=rEBb9d?|k>"
    "{**D)t-)`#PLbiV3=lc#%z2r^xi?<K@2V&~<f0Tb8=Sy0AH1WDvrB_7b((2`gW|`Gr^p9vxr}I7sNXsQi-?e"
    "I_iQJ_5`kLm)ui3*lzZ@R@W$*CM-U($l227nUn_%lYPjG<_Bg4|!<Da<avGrlZ@`-GFYFYi5Dx<`7o(!JgTQ"
    "}y@udz`6tOdw5d`>$CgbUOF2@|M!L?+%4RIGnL>RDF}HuwC6C8^fL616dq-dxO3bdLkykkD;6a_wyC+s8h$4"
    "50Ma{Axprfp#3qIi2+Bcav|v|F)+^#f|NcHDJM#Q`6TJYu;S9oX&^_C-Z#8JmU5_lJq(C7NB=<$Z?>oxXxMG"
    "_t}{H{7$qkB*VmB;iX6z*IyihM<>$lIwe^^_k?JiT!ZVf%Fu1fMx^uj9tj}}l6-~WaY;j4<W{ZDa+0*GTj8C"
    "anoGvaS7YQzdbZ@q>02we!S)6AoSuGZdkVjOHZPkiT#0hHf!go5MOsnjBnz#5@rv{%G9=k>3^b3`+Xrvb{=e"
    "__|M!#rAKv+ogU7>3|J|d1EHBfqpM5u^AI@>X$M3$q!};UoYsk&0w{m`UbaL>&#6)Dr)gqte>sSWqW~40e1-"
    "BvWZ{3M{?a=x8qmduN)89M^PNTf))33kBFEJ_No9~`Yo_+IObUnJg$N_Tg$+__h6YNeem@nBolc>m*v`OE$R"
    "Yt9tG1%drc;Y9^bg39hZU*kvF*_Xqvy%C5pN>sKjtWXkf#!a83mh2CEST7bd{qcpaliRjd#8Va_5rRezp1ZD"
    "eqf$R3<yHB>-)}!>>^T!u@k|M19mQyu*GP|%`*RW`1tW-noXmM9KF&Sc`NLe(06lSz$wrm(uJMx6925Dmbt-"
    "OzIpp#ABE}1lfN9DoRYXej-Q{PJKbm8W6Y@;sNfAqkVcW4)bqv%K|V_ImpdLTt@>i^$Q2(y4i4sbcX3;(S$f"
    "U7laOh(cOM!y)xMLK#iM7v=siclyT*k|x%NFAi1rA2su7VkfJNut@KDkb(Z$V{7jUI*maf&|^Pte&)gX5x$#"
    "Q=SIqAbadQ$wulPBG36G*4t8wvD@q5Ym!x&i+8ZKpf9%zh2beA5L7r-&DW{qCEz=#XA^p8q<6`B5zTjI5HcM"
    "mke=2{_3Tk}?hwlmu=W<*w**pDq3|v~jq{TMq@&f)^-v57IM|5AY#$cc6D8bDf#gJX-Ff2m@L)k{A8rTDk@a"
    "+%&Z2koNW2vIVxv&z@E4Ww2UU@t*4&PQ!Pq-hv0AqSZ^PEVJfacmNis&BuDi1RE~XhN?1ZMW<~XzPf(AI3wG"
    "o$L@9NS7{40u)?yTcelH2c1dg1c~X4)?YCjKZb{Gt4qw&(;`l)=c(z$KeB1A@t{T7QY1gtt)2poMTCv(jONl"
    "7dFIW^8efB-C+OOdP7ARYdzY=4j5sK^4-piM*7o_v~=wy6KX3u?>{JG^4lI0uPm|GAtO_kp4rhiQnr+t+8M*"
    "SAj)5|_fv(YzSH(nvmiqUu9Hm~&TdQ*;`HvY6xDOvkzS%9=?$l-V2Hs4v&T0a>+Y5Z|bY^mvG9@7uQ)lF|%f"
    "S1xgC9$<$ng4q>`o4MYSK=k8{BllQ?e;nwox#meu4bc;HO_O_o0sd6*iAibee2HC!C2jLYk*NphgK1AwL1@*"
    "hWoMUwZ(c1Pk$X7S+%_I^uLSxJaVKllGU#O>({9QKJm$|Jzx$Q8s2;GYFxi4Tdl&2PEPlaUZ2)4%a`F*`{Tc"
    "H1!#O(vy2W3l2_{qilR#zg4lXP8{YuY1jXL=IC+;quN94V#A;u<TBWyPk)<_ufrNFqJ)sOUuSB!QKzC&uY93"
    "2s=gArDi%0%MzYy=c{XA@dq0^s8UAX|x>#7sKXfGIh{I~Jp>Ew94x8H4mlw)TAmT}mOLZ)h}d!T&ikmb;M(("
    "~)kudPE(j5px!@dBS7{5+n#Jox$Gw8<0d3e@R1zHk0{cDY%;7Z(N2Y-K41Eba;vhJO3x58rjSz9tVf{H$51t"
    "BaITpat+i?azYMq79bGXsLJvc3U<&W3OJHe%8Xl4z`ghB;N4wI`Mk8G1sQQyxwr^bWHPR0vSAcdJm1Xu24k-"
    "-<5#uR=n8LufH|qoztVEmlHwRYFaCW7Yf+Zsl3Km(nyA_TYe7}pXXd1IjpU}J?FYW{cj5d;r7)haz}TG>kCK"
    "l*9@p9*m@@ifBx&i%a`5OmwhES0X}|nJ#K(t^cr7TR-3gqZ1}To^F?|JxwN%Yxu(^GY%wKSD>R#N#zrNSzju"
    "wT%&WqyS>iOyu=Z=4EX&=bSLNNmN~TbAr<_aZn{Ir7hlgYFoH%<R7Be~#0+&gvs;?fF><%APp;*!A5pICdCo"
    "k=FX-i84>sC2mtmOhyp0LuR|ML<5-2IPWA41#xkbW$y=KF4D{5Es`i!VNdf9hfdCco6P+xJSjfD5|rG)c3nT"
    "fnT+*&<7qn`;dnYPJih1n2qcDsTX3pz33YK_Fgm_AzM_!0=aDIs7Unn*9A{7z>bh-NBq&w+oaRI&U-b7!FJ~"
    "8c$s_!<w>6yDip}w7agEM{3qjt}GshM>JVV$mQh4kc)yv(2MTc19V|yVi%q}<$zJt5g3^9Lx*2xnSYXl+S7v"
    "8)x6KGcyKEcZd_wk{}fBVM`H@poP8#+R<9|<m4=q>GVZbppyWid>bd25|4IM5zV(Yh{(Mi$t)C4!rO~$s@+~"
    "c9=?18tj6;BO+~oy#nN&1SoBJ?GBGh{|`N7hmX)a`?lQcXH8$aizL0ZZ<vNqORjU^@OkF!kQ;=@y}OaDITN!"
    "@?D)F^M?tt7pfYk3I&x$lu7UC5AA#%*l0w>ElMOTYjPo)dmL_KCB~B_$rsy`+Pze(P~0WE<Wtn^Ni*+5Cdry"
    "9KG-%iAC_FAWS`TW5*GO4%t>4`kh1%W@>YjVb!MeHB%2Alc85Z?!3krfVAbD9&%G$m0UQClKt5^xtz-Ip7wQ"
    "wrT{D162y(t<5ML?3%)tPb9&XpTmudzaAtffI@L(e-)=-bF&MSe;<y2nbK5Ng?6yI4Zut~mNn>`qJytXau^Z"
    "JR1gIPt)=Vx!SE*9%UoLpl^krv+~`WP=wl(4sHu^(@u~xHBJEb+29&Ow%Y%vr=h}snDDrsh^7=N2m1iIybAx"
    "nNO;eCI+=`lw<lCuiLx5PTEp51`o(N*VywX}I@@dZ{Su#{25;?FPS`$K)Ah9`4@??nIb2)ZMF;PNACq<e<d7"
    "Wyn8U<-hrH8h($UY1XrX(5$yejVOg~58RE(9U?R3IybsI(J?HeJ-PfJ2q`_`gWmSXd<ogIz2U^aGA<KGSgAN"
    "d|p-Y*8xoZDbI1@#n_<mWhk-nb)Rn>x|p*aGvJ6;9Qo?5?d_CCOmsIlUqY5<`p9`lP}&b{rLdWj6(X;gr6f_"
    "6<|ajRYp&t622Tf0U<&-1f?B{oUw!o6Bha0_!a}&zj6MYQ2>~Rv#_VH7K0&`qGYizKXXH7t49_*zaSZusX;q"
    "ig3uhav-EbvTZWBe=l~N>F2mM}A-=NabGoJl!2#edjmF;>+4)+QonPZKdRaH6s8mu<gpuvu&bk>g)2>(M_ul"
    "{%)N?Vt$06lTlvy!+Q%|<tzWa|s7~S5oTb|rYPKq0a9{tR|-Ho>?AG3v<e?X^;N!dDc7A$soi0RdGz2lmR%Z"
    "rk{$bg-4R+5%uRoTDj7OD?1*OPNd+!m-l45;5rI7~;Qu$;U>c^Icz+ew;}ibY02mR_OFqX{GMUDjCWn3ik&E"
    "5``~L5=FNVABH#?NwT%k$Jb^5=^iQWFlq;`l2izkv_{PTmEu%jOgskqZ3JI3Iv&)<kN!}f1Mm0o{o?Iw)b*!"
    "GJbJ%xDUYCuLn<d>c)I*OwLozu&rCPelHBC+Rj^u-hH{lqfeZ4Yv>=vo!%Ma75vb!)tSr9bJDwCtrWCXQdM5"
    "OJb11yVEvNzq^$JcR-GZ#sa)G>&b`^G;k2UB(aS~<rk^>I6EXoJwi~Kpb9U~E9YR*xi^mhLl)lW+MPle$2)y"
    "8?5)L|L3u@(YR%UC}F-<Kq;4w=orDMR*Y0V0$ucO|kc=Ay;?US+JoI=ZTU7$Cuvmp1ek*p=P^SA<L#gkRN%j"
    ">_~Fo>td2lCQ2wAUrG^4hpB4{Cf8;!_)VJ5OG}qC<Faa&*k?e`+P!UX@u3Z7*&W)JM3)W+`xET<IY_TC}!}_"
    "tvUJq<@gJ{CKIF@S3zgUllfycexYw(7;NCc<dE;#u^)7QmC<u3P4mq&0#%OG}>>0i8?2f+ABpLqj8ZOPJ)ON"
    "6S+plI|1rpH-U*!X+BZrCfGC#{02N|?g$)P4aho$o?0(G2nr#&qb}DNEmf&t^V00r@>2Xo%=Z_CKu@8y?)~^"
    "x<~FKbc(D9HoG<6@F=C<eqa;TImaQ~VyL6r^A;J1HgFJ6=+7+PhS*2<!&{b+{ZOy81STV_wmQV#*_B~lDS&;"
    "?f7r$$!wG!Q110s`Qej|0k8vH0DeG)zGEkkYHdV(Sodgh?TXzc&Kn@p=2WZue3OlSj_sN{^qSbH;`?Xu==&`"
    "Z2Q1XiVwcp5~cG&Q8T-|gV!&tcem#SkIH7WdYmDS+HSguPX1#ZeI?UrkjbodioADRI+nUJZx8!H@;)hm!0b{"
    "#(2Z%X2^jO95%|A)m9!Z|U5Z#f>-t(v@#9<U<7#i!cZSwtz1RwDj|6lsx{5Qw_BX4HR|jAiiL-&P#`($PNLl"
    "pZY$vj1p|owGHGMrMk@X2z}%20}_OS;CaSSe!4LS9_yq6T`{zsVUWe>@TsFljBYjC1)o!m=Shw6Pn`ozkflS"
    "wj;Ow~44S)}mCmLGTMo{RXPQ@C!c6IS7uRKYw6sf6u?!uB(x)&WfHvzM<NV^xB{R%Qr|Yof+53qs1#LJTypB"
    "{mmFgKXcu3S64PCLRHnq2Y_EK#cdMSEVdTacMGn}nUlTFObBzZMJO-Qx7mGhrj2P1P+r4`qiU8#OLHXE%3Um"
    "q+E7XgAxZb{!$KU|}pq{n*L&TlG>W?ciJWpe*Ecck63vb+)hKMXAe<T|RWVs^8RHfU0xKA{y+y_J&$Cihg$R"
    "`2K1tg6WGg=4IiYCsCrq12zpdMX-beaO@`n~PK5pkV2^tkRiQfm>NYbugBmtQcM3Vgwrm%$5v-4ee(?rv9z%"
    ">?Wc#c-6zLZLn~m;^5IERcDTxF0cd`nR}(8K7^edR!D#DwzgkFbH}ZXniODT<Vc_y_|16#2(QK0bgFlB2Tnk"
    "MUMjzWoZY>p<x$i$1{=aMve0L9)KHY_uG_%=8-2WMO6`(X5`HGypfX+8vc%?cDeXsn9MX|cjL1L?^(4Tm_zg"
    "TNEtjgzI%+OP9oH0zkM;t9LFvSpC+@eXR`RafSOiL=dj-JX+FUAp=RCnuYhnIiIihW_C62w>5%(bmIasPkc)"
    "$|0lr$^G{n9-6_Sj^5%`k5<s0F@5qNj57=3R4=U+7!K!EAK8cJz<nJ}-W>16e`yM6&w8>D;7wJeK_Al0OEA("
    "%l_FyMC4YBJGbkSe&E%a#8dIhN9ZJP-pZ|BSJY4E1Ytt$srRh;g~3v2-ihTA5R68dHVPTDe(v~eWSdXWX%dV"
    "X^E5@r_t1=`b17QhpIu=4kFDCIn1vJ)<QyAF640=4i%`of?+598D*e!?W4c{DyVCsHac1fhcb~Y+6*n5B5AB"
    "m&my`ZO#)2}nPx)y<|aJgT8R=VlM>Aie#*;9d3&|Um+x!&8<8Wv<8J9Cb!w@1MXX6uO)U#C5?G;x1hIQm=)9"
    "36kL>M(ceQNQytMAno!SW8oUR+oFdI5>w0F$0Umv0Cz5Y7k@JN7rhzyLo^|azZs4X{;9zG-hRylE=f6rLT$s"
    ")2DZls4eMtCl(O=ow8m587vLKh6sB|Hp7FKJclwf#&B->M^WZ5ii>#;W+1rocgcTUzyv+>6xF(k6JDw&1RD5"
    "~-;d@V%*0JHR%`fqq$NMuzBe1v@$6nuYrCuyp){;hlY`<6+q}n7}Kqvwpfltpj9eWLb416NHsXRxq2!ayqB9"
    "Awg`Ni!C|rQCJN#X8sv9tJ*iDabD+%#Rmm6+KHW>e~yH0B?K*D?8bLA^UZq`T-(uLUmH^CYAS7_`3REGCSBK"
    "R^xE-ftJVNBpb;nr;}=JNqhqiil}iP>bHK)ww*{amHU0Y&4m7-Xm6M!=C$jmx1t&`<SUEfmdi{2~--5jBIbS"
    "1;M(`x_yfjYQAzf5<BFqA;%AUKw!=xQCw#>SvpLt}&)L*OhHWxqSd$w_^2JD~kp8LRV^!ADcfDzh_08UYCUv"
    "o{;oG@wnli|O<N6PyPtKyy2(u|ZQIJzf#U2uJbv%eSmbe7z!{d{fMYsPaUe-&HeJ|k&RRTkr*`qXlQ#5a>II"
    "sG~aqp6nlSX?!+y2uW7_5b}tl9dRQ@S%8aDRkn#tUHjxahiNdksE0ttvnmONWtq#y5A_UZ8>UCGme8QDsi1D"
    "lxm>;n@{cBP>+582D6vfR$@DGRk5MYQCsLx5tZR%Ye&xIK#qCkfH%0Rnn38cxEg|3{wNd&KAJ!B%3SN2sDuX"
    "`GjTxz>`~{FqW~NO*qS47yjgM_7`VouATkTM3wo3+jA{mk>tR3<hC}2CU2!cSO5PP{PCRuQk0b~mEUCc4JBN"
    "wKb#L$lhB*d}KES9NT~gWXiCcsAO=DGa3EW8A!!tBg%Q(D~)wK^+qUkM1@%n{*MH{juM*L;3f!M<-j@-AtdO"
    "rYtX(FmeJx=NwCTB%K3L1yCNJsIoER7j6jct<=_JI!^cs|Q{n2q`3<w3#~p$V6STF0~EBA@lp@o59-m5b|i6"
    "?A=@Vp^O5GsWD4Hh3}pGDlMoF4~6Da*a!}|5ecv*8);p%y1^TL2Bw%x?bhKa=Yf9BH1Ekli@BHqX{{OdJKH?"
    "JNiYk`jSifZXwPq?_O9pCE(MGs)!hbZ^xh=Q$Agofjw$!yD)VyB~F#6x1~!t-7~RN3Fijj`&Jt%>F=Bz{F(M"
    "Gd7QjhuNM6mjI}!bYj%59q^tRXT{@M>?%eu#NlX-G?R)9bRdD15%c|-3lJEsqZc!D9c(93VeX3#MNY^pv;vn"
    "ur6akO{9`V|ucyWmV9g7S|Jr-5DOabn>vhHPQ2{&5{pjbYi(~<}zj}r7S_K=4G8URsQ$Obf&GW;n!X5f2czf"
    "7@Mgocz>07U7(t^-?B4zLg(*ASpergU&MXul{~(wq&PbWld%;sH@gFz{N7W&ffe;^;PnV0br13Db@p7S0l2a"
    "?B<rx+1PSpwZ10!zcCVElCR*YFYpv-b!?zo+vmd7(Hxp%+JCpeCt{z2->PX4!VMt)X6^`UtmYn*Q-p+AgiLP"
    "Jq1G>Ims7D%gHq|*CujFNB)T;In2JQg<i~&16&`e<K;?SdZo(c0f3gByt<L!a9>OL=(g9{;g#aaYc*o+*bdu"
    "nsFzf3-Ja@phG{1a^BmU1T$P&mra<<cley*(IF@9Xd_;Y(4A`gvbnoKM_MNiQ{0La;!5B>vlg0=#-tQZsQJm"
    "5cO-b!EmW|Z)VNPd9pwsM@L5Cs!0G5ho66zu!UA9c5iryt17eMh>IDPc4mjr1NUG_?})QzpPMFt#}2_Tf0Sq"
    "<FrRDbu}S}z>B`V5+O`krBUw9FyBI?FFML`DwT`-=cPuI>k9tidk!P`SG<X2qf{eV!K<2IiU#3%hrcE&pwkZ"
    "L%+vPXDPX@|WxN^@MFuzQe5m%?Zd-_)qeHe=OD=dqwlwr!)3Ex@2OL38<3lNWT+gQx?_=NZ|cq6g|mPT;2|m"
    "G8;b72x1t>nhB|2>&ZmN)^<XchgOj-iX9Na#{o1BXmGzDdce3z|K0E55SLaA_k$c6Y?>oj59OCw-E9~UfcE7"
    "Okpoa}_oJ?&{W>U#x{)w9#H^ln-#mHuo7Xm46}gQUCr6#@1G2PVUn2of^Ycm~8b$Mc`{3^W6(KcwbA8P{&#T"
    "8cXOH<d$c<G-l(#GqFHx#%bVGtp%i-h4>2*FZR)TVf$7jWwp|!$w{yl(N_*;3`2JaD;Yg7TY^Eh@5H(YWdK{"
    "@(}t`ZEv)IYtw&ZK~rvv+3vx{oDFaJQvS`kQAvltIg?3>4|}ccbL%Cr@@Lc6RGO&t`ykn73?%E<M~l3h)QS>"
    "9XS<d{)eF>+@ow@s2VXp~qy`l`?I7p&6gWdwQh#Us}LS8p!F>UP0X%cr3SI$A`$hr>cxDQ7?E_5BiOM!d^DP"
    "Eqs;iy*fx<AHOUef|+YmFwjgyl1GxfhzCLa=gZN?q?qSfIcPdS4Lhdfugxl+TTfQ!s7FIGwhRL7P%JR>b%DT"
    "lIuvL2OiYxP9rtONNRdaGt>2J5eOKk2y2tK%?$@-u?Es^x!^)D|Q6Qui)}QZ>z=u6|f9BrmD(``zbkdychHO"
    "O^t5X2D%p3V$F}kL`B!hIssma6)hLBXfWcv$OOC;LYtLytd04;UI-a`{i;4t(^<KRIjb2!M_vHo_1^cT0)PK"
    "f>|<Co(Xr^%z_r{kla6R&CLyv<vt-O%LA5rQ^JNB`=DzQO?mjuTaMVxvc91RCT|Z!8t2M7-%wV$tA#on|@u3"
    "I;AGB-!S>lKq0)$DxEvOzE>?ZR$mI=yzC)gTs^Y@o7SK#!>4^xVM%*0Qwf)<ZpW~Uyo0c&JR8Muc<H8(P8r9"
    "=<uhP2QN--jBc`jqz&gdLdHXmxWm>wn-8KV_^;i<RiOoKW-?AMTvQ^rZ=W>a_*d;(=815GFSyUaoNG$XqGQo"
    "Z;^%bR%(zb>*iQ&6?vDX&^l9YEQGZ$8m~^98i27riN$HnDHK|W!8$EB1NT~y!sEThROL2)4w02w9#2wz^{2W"
    "zJElZ-~?QnwYr&mWF>7+=b^!Wo46HzOEBWfT3*odvMsu@l+QWX6Uq!P&!7$Ai|L5);A!eR3C$rJpo>JPs8n!"
    "ivOkIBZy90LBvIs`m;cUJ?0t*9S*V~-cVYpBTjEu$evI@2!7yxg3e!CdfI&Ma=vbENS5EaOk?&a#s1;oX_})"
    "6YL0{8>57pMLlx9uu*bHaWncZ1PGwGJ0k3l09w>zeC1;nO|H&`xzOv_QQrl&@6OoNVU)%9^R*(%5|!q?xuXU"
    "5rp_KYx<}BDuHJCth%rJp>_*Rla(oVMOC5lWBxID@@ccSC1QGA-`1Y}RkB}5W_DiAfOLawn{>4x$|h6k>I@?"
    "IT)HeX(hD+B84a0>YlLA`N2JMLZ!~rsf^10mL-Ha~#Hn488l&4W0RW^<|LXbGsJx2r*cq+6;~qWVhO?bO^y="
    "S6AvTj15-Fu~p>NP76Xp7xrdiG|IRF-4jW2h6CwX3AlU07lP`~Yk^^L?uw{ClH3+c<%`W_AE0mx#t_r;e@C#"
    "OM|s8}ZXa@`PKM_xkBFloLH?_{%J1HUV9jDYs#%&O+wcpAaI{HEJyRK42uq;9@k06)XUEGO*!=r&&;>^YXRn"
    "#vMQo_;q(wdN}zSotd7Y~YWhsM|mr&b5RJ5r#oM{M!c~RruTuKf1Gh*9`xdb61HSb5A4LN#t4)p6qiKktwrL"
    "<w^eNHN1AS^z+ptrW2rEMV+{vHbhRJ->1*3tORd6H>i-U3IuYXsRLVBD7|5}4O2YVTyS2;HY8cE+gJjN|LRK"
    "`ULrlb;l)xuvba9i-r|u0gG+VMR;35>#ne=jI=@ezcDt?Bw80{U{Yg3IFad#lo*Tk9soB*J@hLjzO3I=>-+7"
    "=JvW<$S1zbiCUyTp<4-WtQuxay-_s7S{kN<+>$RMoA(}sS2?GBaRPRb~^S8qgW)!mERLt0#*xM6>xf>V&WG0"
    "4j~olP|OV?nX*)UWB9+uU#LZ^^2yuQdqTukHT$@L;_E&}G^x&ysm@8e^}!)s?I(0DBuFg<JGhvZomomX!#wE"
    "G{wSf>evG^`xT@FI)1L)6-YdI!}t#U2oDIS;UU-ePT4V+lx24K~%4hTj0%(yuyn1jEi6>e)ET#cU|wtKW~QL"
    "eE)=uX2ccVzFodijKcM5vqZk?{JHbprl{v%t+|+pgR$@8#6oqrd+Rz5ws4<4s0EsL+d_nFO|ynH<oVsj2coj"
    "-+kE!bx)D)hA}_vg&TI;e+A6hsofkg5<sG|*+uL9?D4c9MA}dAd!4>RBaW!j!2L5$;>eB<;y#2$*dtV>^_3-"
    "GIL%aP`_^W6y^G|BIdJp0M(9>5P{Sc6Th2h%a*rhe9ylF!$DhPdjj5lo9vX6IN$w!f;^XtB~<7s$ccWp-s^3"
    "t_+#Vx}YwpQ6bmo!tI<nWUc^0y@8^X3gKhoQ_GI$CT^$2as|Ss45^X<D726^pcCbhm83S|{c&cVBFKf@3Yi2"
    "C>+B-!4S6d)~f5AxVuzYZggSEGF~3yk@UN2tZ7HYtCIiJ&4GV-5i=8QzqKGY_lc~Z5VpjIB#=+Pb@za62Sd!"
    "DI|Q$49+g*2WVq5v-@5U#~0Ald!ZP8nu-7M=aiEdU#*H?Z#ne5r30vR4ZWSG0M@kMekA4eXH>N@TLk2fIp|t"
    "*R-_0{bYL0el$IDTvJ-gR*!2#?ZA0HBD*&aV)t`~!DI4bT>sA*VLs_GDedFe?GF<b<hHg>cyg|l;<UObd9&v"
    "0E%N!|{Oyi~m#*%dItCUkJ+M7H!1B1&sSi3X;hmcSQ1M)u&o0x;(xZ_98V`%7|q#c|5V!4Zh?;7txi>)gpFP"
    "H8Xx4OE)pxucsL^b&#Jg;|Qg3i7k!)(=*q7x^%giYXRA4<jXi0LEb7LS6@8Yc)%C<I!9D+C2)!gYcnNf@ybT"
    "|hv+YitQB0CK-hgo8<&ty=$2=2Q(?M!cN-N@yKlIia18+=f^Po_Q135#j^#2yoY3x2BW&A-l-?U^SKh+M(ef"
    "hQ{McLFG6DL~l-KAa1XAUg<U&y*m4KCQrWoe)8-ezS}(=iXW{CZbQ>XpY0@@*^|G*jYBPu{TO~<8K5@b`YY6"
    "rcj?bJ6JC7C8&3Hf-Z?uGyl>KL&UUZle5YWu1~k>H5{@yfFUqfQRq)DD8W-fv`%DwLU<wQ!XWh<)*22bu=R!"
    "@#2ux@3Hp^tiHfDdVU1nx%IKO5c>!alH425yR@=)lpVIuT4p`j)^#M=jV+j6}e+u>X{THh)ka!7PMQTHo*zG"
    "y*AxKvVmD#EOm!BhF22LrS#3eqg82e>nSdhmFb*^HK;mc6sXs_2oJxbdQ8(QO$-;z^%aJrP^o8e8WeKnkktt"
    "ZyeigJ$avHBN5WSg)2z)ARa_t=g`!KURD>?{mcn<x*uM5Eb(sx0Kx~=1fDAS{|X^rMC8_L6h33hi)UAX^NHX"
    "un#%}z071mFOfy--!zD{7Jd6bDz@nh{&3es^e&CfC9j1UZIu`-U8T*F<S(_5KljiZkk8##RlN*V^dC{5WlFl"
    "!%m>L&`Et&sPV$S?y<DtP9K>t)5-9j#q`UR!D(I`-6z?|pZ`UVVZ#l3pUTJl$%QhjaZeFr$$tNe9(lU&#oeU"
    "KYs7If}8>Bt0IYZfE0Ru4Bl{DqrLF4{ZJ^Ouj%hPSbMegkO$bH*NeXc5aGTtfI_hCT$ah)zEoQ<tomig|~mn"
    "MpOlnBmpk!~w4w&j9*t&(-g#&RRpj7BQlSq|0|vbv9u?{cabwoJbHV)~e+E{hVW)up0d@RvR8(rA%hoz2q(T"
    "E>w7FY>+{Y87^>bW!L*=u5+U%IcV@wa<8Usv8&ThR_1}7FGwJ-2bZH)Rx=qeXWG>DT}zLPog)!Ntfb5(=)>p"
    "4vUh~<$DMECj`ZXWxT^7;-BS+IPJ_YX=Um(%N4}SH_0R3Po2X5bjQ|6quK>eZv6eI{jT7Iwch-7%VXa@0M6C"
    "F7P%<<13Q<sW_<a%4AvOC$7)#=ufvzg$>`SBbN~YD)aa_y$G>l$kio<sp1!NC#W|PR8l5_;X5v+2dBU3^6T-"
    "WCjhUmn4v*F21(BP&(I3g5gqR$S|0CQ(`Ao9<J=vR2N2Vj1v{mX4tBjgSKVXv{Okm)~Vaf?eq4o-E=20z@&m"
    "&z0($9l_F7oqib~{^SLqi&{xf+CnK*$T20?LkOf?|D!)k?KX)*fS#d#HuZ)T5-KJ#G2;k0B!3pB_)Uf{PANh"
    "t#9cq7&7+Sa35f?gNHaO6$@Z*3cZR7sHRNxEW#u*PGgm7&9z=yM#Yfux6Ll{yo|9L$*K-s`UVJ&<j@83ja3O"
    ">t_NMc^Wi@5F~fp<{lX$wZpgxI%BY6FW8m_xIt1qovnL1&~&d6G-Ap@&WlXY;{(K9!GEWbfgsnDqHGySvYZ("
    "07sY8y$;MB$wpMV6ftS-slK?S}WkT0_?z~;%+;i*!)w(z7g2ChIGo#F7H&6<}U2K2@r(M!kS!Q)2IfK>ZNQH"
    "!@CyN%;Kra@w2Dm<5WdS@0YSo9>x1fOsD&GCp2rRSq954BHuJtLU`x+Vop-utQOcNAq^xiJ9!RUJL%b^Vx7b"
    "BlD$~NBe7P)3~GQ1qxKKCPqOO~X|;`Z}<;asNW<sv`x?QkwP+^1+)w=1@j?zf*`(Vwk)VM_xW-|hr(%QuCn@"
    "mnYl7|)k<4hPAenn1SyYwi~J6_iD;4M9sI-hi;98iPEe-upb2Vsb-BP7QF$Arx?r`LDF3JrNyCLG-JwqE;Io"
    "t0R$$2w#O%I){^$^XoFg0X-GDaKb&<|D%nYR_K<_)VWA+Q3}s}5j5ElhvZ@jlsYxeG2RWRhOE|%5v#eU7I$%"
    "K!EXV_82|k0=y>n=Unctp$Kw~LN5}u76&sCsFR#YOCkH2|<3s7%at&~?a?Mc>>FILvYVXB(^6Kd2!Ha`2`n5"
    "O*WaneUv&iOhBi?m|296al*}8xMyq6hSnGFrJfq@&Xzu7#$Kp+`AKTB73V0pu|3|3Gi(q({_PV%zn7^^nX_J"
    "<f`RqDeyn6wn=HQ`;3wFLZ$Q&=tqy^WE)t;HfkVxVz?a8`^orSF1D<EcZ$=(K=k_7X$O>?IYrOm6R^kQUv6A"
    "faOUNIN=TWhwzU0}3FWIq|-dmxS~#SQLq3^eB2IMhoQv+OsNvDG|%$)$#abeEhfZ{^aOzLR*MtD6o1QPU1jH"
    "`FctG&4Bpk*U!FVMK&0O$RHjl#4YV};(O5Xg*g9&wLLKOA+s1D`an_nka@Ea-$!UC{{%@fwF{?opwLDTgG_s"
    "Z>LjQkw?PvVIe?^`61!*n*|1J9`d~64+bf&rA10Hj95Y6jNY6-Z+N_CY07=@vWCs=V`I6DW5dl)z0rW6s8Lz"
    "F?fY0HvN@b=ZBEjSY0%}Hz-5G;Ze8?5NV>%cBdE`PHcSsvJVF!H@3g`K+D%2IhR<JBq#pdGDkgia!rX6AOU%"
    "^Z=1V0!~N}9}&yet+tflS}BZtmb<KhUC-{$?+v2VYS-7W(tQLjva9*9K|ZoD?gkj2|Mx+So2nUCRkdLyvb?q"
    "8oa7OUy@vkC3olBun6SZ7<lHfDriQ&e0<atIC@Og1AUm^98_wxoafLVI>HAGoFDact<Tlo%rUiPK>K4VX8p&"
    "64|dq6<mtT5XA870l1N|S%@GmNISX0k`aBC;>_WZLPBE-K@TAVyje@Hg8)#h@5qVorcuta3ss$z;+V6r`m_}"
    "3tBD<#$YENCy?hqTaz%OJo$^Yi!lMyOgeirMxY1q?`mXYR=riayE*ScnJJGO{ITX^iq0qbZuqZ{KZEp<K6Jo"
    "EpQg(fL&b5)xmbEL%4pE}Rw$>?cAB?ZA*M{KR&>y8~&E*Kgu8*mpJ^&I`v83JFz$c_VqC|kfW-^{bH2&7^C%"
    "6D$1%Lrf7fszyXr;i^IyPn(V8cdXo$l_9WiSdLFJu_>mJ$9bZ7O11=FeEbv&_A=LJZj{pyN|dq~r`d?z86kx"
    "t`pJf;|)91{d{#h>V#WQ<)2Nax2g<gd$LU=}Df)tq&9sduiP;^6)sc6U9Jh9@iRanv{T2vpI!Vm5!tOiV-6A"
    "ZzL4syc2%EQ4&wg4!JS<QPNQ`a!**5i{n^|yLDhUOx8swdT2LFSo6L#2-vLRn*Yxw)(WN7?9pChe=QI>UyoN"
    "3V9Rw2QAEq~pFtC1wM&d6^v}C(47~e*BAzgvN4nc1;L>mgdYGqx--42J{xhz$=RGm7^oBUJwKTy4hruY7b|-"
    "S2U07Pk`C?I=kvjVbiJNsFFSA=>j~KdEuw92TW?SvH!w({1W9jzTUiUd)%BZAuu@ZM)`B6XL|1f@C^JHSkI7"
    "^IwmOc3@`9(Cv>5u9eI$5UI<s}rm$No!6*`0c)4tpR0%*K{4F-tWV6h@1|N};V55Y+0S3T62M4GPK1CKfsUk"
    "i)|WN3}xho$*jtc`5kUP@KH62KvqBjRY+1nlG{?*-8u2$!-c&BcxraDVUM7iy0F;X1LiB8HsqkeEA_SbJ#}f"
    "LQ}h;fQn&<(F8mS%2;ImJC~cHC8Fj0TDvy!C9hUUeJ8Q~4J{0tr9o5rf9QKg;@q5rtNF0KQH^>pb@d%&>m%o"
    "joj>wD2-dFat0bv=A|%4wtl*boajL6d!iS7`hrZEp@dop=N7JO^^;2588|@cycI!PaP<OObf=)ev?G*v;I(4"
    "|NUAkYe=3P4-9*vVqScxlc!WWZbG21u(<_z{ZR*kITJ#W;}uV_n#Z4C5JHuJsLsEJMx&|mReqRE3I3<@|PyK"
    "q8<S}Yg%jNP?j_|f%HX3yP3NM-%;==I?~ydftqj$Vz~`VF7XtbHQe1u$suPNMCZ2zs#D$M=LAtH(StkN3=fB"
    "5?46uRMFN7M5Eas8SI%1|r0o%rWjGzizO`)i=i)@#@XxoHeX@&-Wl>I$Ey;gR#*$KI2yJp`UvY5wGjjS0Ulx"
    "EXY|q`RA9QE5&6-OV$P&SFlU%zZ_C|&wPP8<w~1$acY;|fT<mA8s}og1KoEx*z~OSAFBli!ozNEZRZTCG7Jk"
    "fhllHV96gXXRuaN&5oIZ@@0}hrWVWk0c0!vrjfs4!T>*5F5MPj9@pJK!h!-~vB#Nn(tJSSp_^^f8G4A=S_N*"
    "4&%X;gQ!LTR_jtivgiiv0#sv!I_!~jFWfeW2oE93TIGsx8-F)q%otg9m4`6+3q^1QH(u`cJtRv9RilTb-=8!"
    "TV&V_VL%-728qlP3LK2_o{#hNu*AXBl_G-6+-a3HQjxo<o&GM>^FP8mWH+b@YpkR$gAUjdmB|X|xawE$7F(x"
    "?&mXy*44I@{Sr5J7vTpi^izil(o45_jlvGDzXBBjwDxym3=xrOw8`_mXyt)+r@n4(nv$BQdLKX8^vV1qpWFb"
    "eJ<g`c_ef_6LaXvXeh7q@Xa!%wLO-Yqm4Opp$|~<_s6H>7pLQW;SqpJMOc+1L!?fn2K1R+(PyOFdF*2+=pI3"
    "U!&A({Y5K^`biP@M3Xz934?T5F8J4QXh9&x!&c#Q6$$g=cqm%xEW<**5iSD!FSJzZDMUu<x690yyIkyG32M@"
    "iW@(sgLI6qs|Ar&CZjB~x1`|(K2g;VjY5RVy48_nWm#C&^a@N%$P>A>KcnM(kK&z1ItZDi|?ZBG%hbR2Dp$;"
    "~%2Bm|YZ@OAZHW9MbiP}SBSx)t~JbSk-+8d=seBU)9hQbJ?@M&=4CkLQY=!b`cEF~Othg75$6+}uI1SK*{rU"
    "NdT)oL3c8-icmXTfLgyz#_416j^@ZB<IVJ)-G6!iSyA^&zR3!f0N)^+pkO%99SWS5zjd&=??e0W4%?YyhQtW"
    ")PIQNS;RAJ`|Irr)L^glW#ou+<mCxivCM10;yd}DG8y@+mMWx|8ZW(O&%y6TdQbFq%|+G?mb{vm7CbZQM-%e"
    "x38YVH<;H04{c!GfqY(v{$rg)_<FPB9N?~!-dAE_}Yaav~XJj9GwhJTuw<iOR`2Rf{bmRvQ`e(N_1ToFVl8r"
    "2Icjgm})G}ee_te7u9GUkgQJOfWoOUw<kdE)SA_vHcjbn|jI!~@yg*SY+Hr*vI*bwxds-4XNG9=vFVU-MlZW"
    "y1wH_YlfBL)hy8V&xv)Vo;?bT@^mjm01^M>3CtPF~lSJ~AAL-X*T=Ueg7beOy`DGhK2OgtC?CNt;GqVp>C=5"
    "-^Rr8oLh9Vr-F|L|neeB?daXEQ(UwMCTG}LK7WXh0W4JK8)_kKuCz`MM)5vW6_%J!A-ftpddU&8UvN^lH}@0"
    "`n-hp&j47ES!>=ihGt@13-;r%Ad@_q!RiV&s&R7H3t?yv>nGEC52CY7j2D{)z4-C?r`IRr{U9DGryn$H+=eM"
    "G<sub@6=&iN$1kIlqcdsg5GcK_K_?RaIfqz!Xm}fPhupa5e(E-y_+&)MLaa-h(J>7&D<*TcT<7ZzTYL$>wOE"
    "Adx-uo{?6%Y_m{K$_iCkMa7JHPfMF4BANV>3L{Ht($9ZzCv!=gdLLyN5hZB<)y6(BZL@j?4E(T~W%q9uL56a"
    ")=TM^i2^ka&Z3gHMyGh99QRppe!Wl6gdb^o#2t<;+6B@HR;})-?||AFQK+&62Z?qy-8hN||!R9Q=Wij|N71d"
    "yc{$NpBZXeI7AYV1sVxjQ5!UqO7*f5;xIKK{K`|O9q7e)aer6xVg+{mk}EjVpc`TwdFW3P+Y<pPC8VML=5Po"
    "Ym|Acd)&DL-d|z}m4oFUgHT<m4dRI|vS=_zkT}4O0GNsp4kE=>YdEItUt9(N#Nj*AK3{AY>#Y*k$N7f;fq7m"
    "DM@eTIcIg=e`x7SkbbFOd0_eoo=>=y@xCUpTN64M1NTk_;5UBvRpuP@CbaGxQ2-me#B6*s*N=tTzxZ|SC)wT"
    "*`LuXN`M^>ykvaY;V3*zc&U%Q9lUN3QyLbtY#{Zan?-RiD6`lgo!-gj>rIjNwLcaE$1biaD!Ey$G1a^_eM_2"
    "50kiadOuW!DcuF)V4Z?l>$>F}%1!jig#WgCgG)!gH@&bzYoH{Em|`&WFjzhrQ&Xq`9j?SYPmN_ik$-ZzIb*s"
    "iq{h<O5ivxKWUuS9fk{S$Gg0`z@`E8wb7ruI=RYOBBaVKE~^gs4w$r9l43ps>z7Vb4n+QLWUCujhnL)YVK|m"
    "z@<hzLbj#MN3xr+koEDr^1$pxcngwpoR(0Pk&Z#v2lMh#8L@HQ?P8MU<0sPi+Xn|r5*O>7S>PoJ(|Yf27K})"
    "Ea_^|R5RuC2R-4UAQ^YN#@AfAkeo4D(%5YFyz=Ix`A!&lsjL(2FiAB?<b*k}VzGGlj&CRKkHn3bq=dCq4^4{"
    "=oICtp+Rh!F}CgRAtZ4}_Wn)I%U?Wo<mjKy&O@*~n0S^pGs2Qpp*T6Kb#*kL@BqdLdR*TrUbIjGjO;{8l12?"
    "{?K;mh+bRco6<HKW6qM)#N1s-dPw`3{k?1#g!R?*1Rgu_Dv"
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if (
    hashlib.sha256(course_bytes).hexdigest()
    != "db253698e725997ddd940a5a35996b8db0d3d7a8318f82569d9997b06484840e"
):
    raise ValueError("Embedded course files failed their integrity check")
course_files = json.loads(course_bytes)
if "COURSE_START_DIRECTORY" not in globals():
    COURSE_START_DIRECTORY = Path.cwd().resolve()
if "COURSE_RUNTIME_DIRECTORY" not in globals():
    COURSE_RUNTIME_DIRECTORY = tempfile.TemporaryDirectory(prefix="lucy-practical-runtime-")
COURSE_ROOT = Path(COURSE_RUNTIME_DIRECTORY.name)
for course_relative, course_content in course_files.items():
    course_target = COURSE_ROOT / course_relative
    if not course_target.resolve().is_relative_to(COURSE_ROOT.resolve()):
        raise ValueError("Invalid embedded relative path")
    course_target.parent.mkdir(parents=True, exist_ok=True)
    course_target.write_text(course_content, encoding="utf-8")
for course_import_path in (COURSE_ROOT, COURSE_ROOT / "src"):
    if str(course_import_path) not in sys.path:
        sys.path.insert(0, str(course_import_path))
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch03-a"
COURSE_WORK.mkdir(parents=True, exist_ok=True)
os.chdir(COURSE_WORK)
ROOT = COURSE_ROOT
print("Python", sys.version.split()[0], "Pydantic", pydantic.__version__)
print("Offline teaching files ready:", len(course_files))
print("Save your work here:", COURSE_WORK)
```

</details>



## Commit to a prediction before the examples


```python tags=["prediction", "learner-notes"]
prediction_notes = {
    "prediction": "Write the expected behavior before running the worked example.",
    "reason": "Name the input and rule behind that prediction.",
    "falsifier": "Name an observation that would prove the explanation wrong.",
    "revision": "After execution, explain what changed in your understanding.",
}
```

### Reading the Python vocabulary used in this notebook

You need basic assignments, `if`, loops, functions, lists and dictionaries. The less familiar
features used by the supplied code are introduced here. A **library** is reusable code that
Python can import. The **standard library** ships with Python; Pydantic is an additional package.
An import makes a name available, but does not mean that you have completed the exercise.

**JSON** is text for exchanging structured values. A Python dictionary is an in-memory object;
the JSON representation is a string. Use `json.dumps` to encode and `json.loads` to decode.
Decoding proves that text has valid JSON syntax, not that its fields match our business contract.
Predict which of the following two decoded objects could describe a stock count.

```python tags=["foundation", "worked-example"]
import json

intro_data = {"sku": "MANGO", "count": 3}
intro_text = json.dumps(intro_data, sort_keys=True)
print(type(intro_data).__name__, type(intro_text).__name__, intro_text)
print(json.loads(intro_text))
print("Also valid JSON:", json.loads('["not", "a", "stock", "record"]'))
assert json.loads(intro_text) == intro_data
```

The first result is a dictionary; the second is a list. Before indexing a decoded object,
check the shape that your function promises to accept. An **exception** interrupts the normal
path. `raise ValueError(...)` refuses an invalid value; `try`/`except` lets a caller inspect that
expected refusal. Catch the expected class, rather than turning every programming error into
apparent success. `finally` runs cleanup even when an earlier operation raises.

An **annotation**, such as `count: int`, documents the expected type. It does not by itself
enforce the type at runtime. A **class** defines a kind of object; an instance holds one object's
data. `@dataclass` asks Python to generate routine construction and comparison methods from
annotated fields. `frozen=True` prevents ordinary reassignment of the instance's fields; it does
not make every object nested inside those fields immutable. A **method** is a function attached
to a class; `self` refers to the instance receiving the call.

```python tags=["foundation", "worked-example"]
from dataclasses import dataclass


@dataclass(frozen=True)
class IntroObservation:
    operation: str
    count: int


intro_observation = IntroObservation("count-mango", 3)
print(intro_observation.operation, intro_observation.count)
assert intro_observation == IntroObservation("count-mango", 3)
```

A **callback** is a function passed to another function. This is how the classroom harness
invokes *your* implementation. The argument `candidate` below is a function object; parentheses
perform the call. Predict the two answers before execution, then trace the result to the callback.

```python tags=["foundation", "worked-example"]
def intro_apply(candidate, value):
    return {"input": value, "observed": candidate(value)}


def intro_double(value):
    return value * 2


print(intro_apply(intro_double, 3))
print(intro_apply(lambda value: value + 2, 3))
assert intro_apply(intro_double, 3)["observed"] == 6
```

`lambda value: value + 2` is a small anonymous function. A **closure** is a function that retains
access to values from its surrounding scope. It can bind a tool to a shop snapshot. A shallow
copy duplicates only the outer container; `copy.deepcopy` also copies nested containers used
in these fixtures. A **set** stores distinct values; `required <= allowed` asks whether every
required item is allowed. `frozenset` is the corresponding immutable set. A tuple groups ordered
values; `(value,)` is a one-item tuple, including the comma.

**Paths and cleanup.** `Path` represents a filesystem location. `path / "file.json"` constructs
a child path; `read_text` and `write_text` read and write text. A context manager, used with
`with`, manages entry and exit. A temporary-directory context removes its contents on exit.
Save your submission outside temporary runtime directories. Reopening a file is different from
reusing a Python variable: the former tests retained bytes, while the latter only tests this kernel.

```python tags=["foundation", "worked-example"]
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as intro_folder:
    intro_path = Path(intro_folder) / "observation.json"
    intro_path.write_text(json.dumps(intro_data), encoding="utf-8")
    intro_reopened = json.loads(intro_path.read_text(encoding="utf-8"))
    assert intro_reopened == intro_data
    print("Read from a file:", intro_reopened)
```

**Retrieval check:** explain JSON versus a dictionary, annotation versus validation, class versus
instance, and defining a callback versus invoking it. Change the callback above so an incorrect
implementation visibly changes the observed output. This distinction will matter when grading
your connected work. Reference: Python's [JSON](https://docs.python.org/3.14/library/json.html),
[dataclasses](https://docs.python.org/3.14/library/dataclasses.html), and
[pathlib](https://docs.python.org/3.14/library/pathlib.html) documentation.


### Pydantic: turn an input dictionary into a checked object

Pydantic is an additional Python library for validating data. Its **model** is a class describing
fields, not a neural network. Inherit from `BaseModel`, declare annotated fields, then call
`model_validate` on incoming data. A field without a default is required. A field with a default
can be omitted. The result is an instance whose values you read with dot notation.

```python tags=["foundation", "worked-example"]
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class IntroCourseRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=1000)
    note: str = ""


intro_request = IntroCourseRequest.model_validate({"name": "mango", "quantity": 4})
print(intro_request.name, intro_request.quantity, repr(intro_request.note))
assert intro_request.note == ""
```

The annotation says the field's type. `Field` supplies constraints: `gt=0` means greater than
zero, `le=1000` means at most 1000, and `min_length=1` excludes an empty name. `ConfigDict` sets
model-wide behavior. `strict=True` rejects conversions for this integer field, including `"4"`,
`4.0` and `True`; `extra="forbid"` rejects undeclared keys. Pydantic can otherwise convert some
compatible inputs, so choose this boundary deliberately rather than assuming every accepted
input arrived in the expected type.

Predict which rule refuses each payload. `ValidationError` reports a failed contract. Its
`errors()` entries contain `loc`, the field location, and `type`, the failure category. Catching
that expected exception lets the notebook inspect the failure and continue.

```python tags=["foundation", "worked-example"]
intro_bad_requests = [
    {"name": "mango", "quantity": "4"},
    {"name": "mango", "quantity": True},
    {"name": "", "quantity": 4},
    {"name": "mango", "quantity": 0},
    {"name": "mango", "quantity": 4, "approved": True},
    {"quantity": 4},
]
for intro_bad_request in intro_bad_requests:
    try:
        IntroCourseRequest.model_validate(intro_bad_request)
    except ValidationError as intro_error:
        print([(item["loc"], item["type"]) for item in intro_error.errors(include_input=False)])
    else:
        raise AssertionError("An invalid input crossed the declared contract")
```

Use `model_dump()` for a Python dictionary, `model_dump_json()` for JSON text, and
`model_validate_json()` to parse and validate JSON. `model_json_schema()` describes the contract;
it is neither an instance's current values nor an invocation of the business handler.

```python tags=["foundation", "worked-example"]
intro_serialized = intro_request.model_dump_json()
intro_schema = IntroCourseRequest.model_json_schema()
assert IntroCourseRequest.model_validate_json(intro_serialized) == intro_request
print("Actual values:", intro_request.model_dump())
print("Quantity contract:", intro_schema["properties"]["quantity"])
assert intro_schema["properties"]["quantity"]["exclusiveMinimum"] == 0
```

Four is valid input to this schema even if the shop needs six. Pydantic checks the declared
shape and constraints; the handler still needs authoritative stock, price and permission.
Ordinary assignments to an existing instance are not automatically revalidated unless configured
for assignment validation. This lesson validates new input at the boundary and uses the resulting
values. Explain these limits before relying on a model object in a transaction or tool call.

Chapter 2's full introduction expands this pattern with a separate data-repair checkpoint.
This notebook contains the required pattern here so prior Pydantic experience is not needed.
References: [models](https://docs.pydantic.dev/latest/concepts/models/),
[fields](https://docs.pydantic.dev/latest/concepts/fields/), and
[strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/).


## A loop is a repeated decision with a stopping argument

One tool call cannot answer every request. Lucy's agent may first inspect stock, then ask for
prices, then prepare drafts, and finally explain what it found. An **agent loop** repeatedly
obtains a model turn, executes admitted tool requests, appends their observations and decides
whether another turn is allowed. It is ordinary control flow surrounding a model interface.

A **transcript** is the ordered sequence of messages. A tool request carries a call identifier;
the tool observation repeats it so a later reader can connect the result to the request. A
**state machine** is a description of allowed states and transitions. Our loop starts running
and eventually reaches a terminal reason such as completed, call limit or model failure.
Terminal means this episode stops; it does not mean every requested business action succeeded.

### Work one iteration by hand

The following replay has two tool requests and a final answer. `iter` creates an iterator;
`next` consumes its next item. A real provider could return different turns, but the program's
responsibility to retain observations and enforce limits is unchanged. Predict the role sequence.

```python tags=["foundation", "worked-example"]
intro_turns = [
    {"call_id": "stock-1", "tool": "stock"},
    {"call_id": "price-1", "tool": "price"},
    {"answer": "A draft is ready for review."},
]
intro_transcript = []
intro_tool_values = {"stock": 6, "price": 250}
for intro_turn in intro_turns:
    intro_transcript.append({"role": "assistant", "content": intro_turn})
    if "answer" in intro_turn:
        break
    intro_transcript.append(
        {
            "role": "tool",
            "tool_call_id": intro_turn["call_id"],
            "value": intro_tool_values[intro_turn["tool"]],
        }
    )
print([item["role"] for item in intro_transcript])
assert [item["role"] for item in intro_transcript] == [
    "assistant",
    "tool",
    "assistant",
    "tool",
    "assistant",
]
```

An assistant message requesting a tool is different from the tool observation. Do not replace
the observation with an assistant's claim that a tool succeeded. The real exercise connects
its admission function to the Chapter 2 dispatcher and retains actual handler results.

### Bound the next attempt, not just the previous result

Suppose each model attempt has a configured exposure of two pence and the budget is six.
With four already charged, one more is admitted; with five already charged, it is refused.
Equality at the boundary is allowed. Exposure is an estimate used for admission, not an invoice.
A failed admitted attempt still consumes one call and its configured exposure. Otherwise a
repeatedly failing provider appears free and can evade the bound.

```python tags=["foundation", "worked-example"]
intro_spent = 0
intro_attempts = 0
intro_events = []
while intro_attempts < 3 and intro_spent + 2 <= 6:
    intro_attempts += 1
    intro_spent += 2
    try:
        raise RuntimeError("authored provider failure")
    except RuntimeError:
        intro_events.append((intro_attempts, intro_spent, "failed"))
print(intro_events)
assert intro_events == [(1, 2, "failed"), (2, 4, "failed"), (3, 6, "failed")]
```

Move charging after the raised error in a copy of this example and predict the consequence
before trying it with a fixed three-iteration outer bound. Keep that outer bound so the
experiment cannot become an accidental infinite loop. This is the failure investigated in
Unit B: accounting belongs at admission, before the provider attempt can fail.

### Multiple limits and deterministic precedence

A call-count limit bounds the number of provider attempts. A cost-exposure limit bounds their
configured cumulative estimate. A tool-call limit bounds a different operation and must not
be confused with model turns: one model turn may request multiple tools. If two refusal reasons
apply, the implementation needs a declared precedence so the same input yields an explainable
result. This lesson checks call count before cost exposure.

The dataclass `ModelTurn` packages a content string and a tuple of calls. `ReplayModel.complete`
returns the next authored turn. These are test doubles implementing the same small interface
that the loop expects from a provider. They are not trained models. `Limits` supplies configured
bounds. Your function decides admission; the surrounding loop records counters and invokes it.

Before coding, draw a trace with columns for attempt number, exposure before, next cost,
admission decision, provider outcome and exposure after. Include zero budget, exact fit and
first-attempt failure. Then explain why a terminal status without counters is insufficient
evidence for a bounded loop. The transfer changes costs and call identifiers, so memorizing
the first transcript will not solve it.


## Understand the supplied execution interface

The course runtime is provided so your implementation can be connected to real callers and
storage. `SourceTask(ROOT, chapter)` makes a private copy. `install(source)` replaces only the
declared function; `visible()` invokes the real chapter probe; `save(path, result)` retains a
successful implementation and its evidence. `load(path)` checks the saved identities and hashes.
`inject_failure()` changes the declared boundary; `repair(fragment)` replaces that broken fragment.
`close()` removes the scratch copy after you retain evidence. These methods are supplied harness
operations, not additional packages you must discover or install.

`RuntimeLab` provides the same copied-source failure experiment without the complete-function
construction layer. Its `run` method records exit status, observations and the compared expectation.
A subprocess log from an unfinished learner implementation is feedback about that implementation;
it is not a successful connection. A syntax error in the notebook cell itself is a separate issue
to fix. The task below names which interface it uses.

For direct-function units, the visible driver calls your callback without installing a source
string. In either case, trace where your code is invoked. Supplied fixtures, database wrappers and
replay models are labelled infrastructure; your own implementation and changed-case explanation
are the evidence of learning.


<!-- #region -->
## Main practical: construct, connect and challenge



Lucy asks what needs ordering. One model turn requests stock, another requests two drafts, and a final turn explains the results. You will implement the admission decision that governs every model call, connect it to a real Chapter 2 tool dispatcher, and retain the transcript for Unit B.

The setup above supplies the required source; use Python 3.14. It uses authored model turns and makes no network call or purchase.

## 1. Locate the cumulative code
<!-- #endregion -->

```python tags=["setup"]
import copy
import json
import os
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path

assert sys.version_info >= (3, 14)

ROOT = COURSE_ROOT


def run_book(relative):
    previous = Path.cwd()
    try:
        os.chdir(ROOT)
        return runpy.run_path(str(ROOT / relative))
    finally:
        os.chdir(previous)


chapter2 = run_book("book/always_on/learner/ch02.py")
ToolCall = chapter2["ToolCall"]
dispatcher = chapter2["build_tools"](chapter2["SHOP"])
print("tools", [schema["function"]["name"] for schema in dispatcher.schemas()])
```

Predict the transcript roles for stock lookup, two draft calls and a final answer. A tool observation must retain the request's call identifier.

## 2. Represent authored model turns

```python tags=["setup"]
class ModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelTurn:
    content: str = ""
    calls: tuple = ()

    def message(self):
        message = {"role": "assistant", "content": self.content}
        if self.calls:
            message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments, sort_keys=True),
                    },
                }
                for call in self.calls
            ]
        return message


class ReplayModel:
    def __init__(self, turns):
        self.turns = iter(turns)

    def complete(self, messages, tools):
        try:
            return next(self.turns)
        except StopIteration:
            raise ModelError("fixture exhausted") from None


OPENING_TURNS = [
    ModelTurn(calls=(ToolCall(id="stock-1", name="list_stock", arguments={}),)),
    ModelTurn(
        calls=(
            ToolCall(
                id="draft-v", name="draft_order", arguments={"sku": "SKU-VANILLA", "quantity": 6}
            ),
            ToolCall(
                id="draft-s", name="draft_order", arguments={"sku": "SKU-STRAWBERRY", "quantity": 4}
            ),
        )
    ),
    ModelTurn("Drafts total 2600 pence GBP. No purchase was made."),
]
```

## 3. Construct model-call admission

The starter always admits another call. Repair it so call count and configured estimated exposure both stop the loop before another provider attempt. Check the call limit first. Inputs are already validated nonnegative integers.

```python tags=["exercise", "learner-owned", "ch03-admission"]
def decide_admission(case):
    if case["used_calls"] >= case["max_calls"]:
        return "MODEL_CALL_LIMIT"
    if case["spent"] + case["next_cost"] > case["budget"]:
        return "MODEL_COST_LIMIT"
    return "CALL"
```

<details><summary>Hint 1 — the decision</summary>

Admission asks whether the *next* call may begin. Used attempts never disappear because the previous provider failed.

</details>

<details><summary>Hint 2 — the evidence</summary>

Inspect `used_calls`, `max_calls`, `spent`, `next_cost`, and `budget`. Equality at the money boundary is allowed; exceeding it is not.

</details>

<details><summary>Hint 3 — the structure</summary>

Return `MODEL_CALL_LIMIT` when `used_calls >= max_calls`; otherwise return `MODEL_COST_LIMIT` when `spent + next_cost > budget`; otherwise return `CALL`.

</details>

```python tags=["assessment", "visible"]
VISIBLE_CASES = [
    ({"used_calls": 0, "max_calls": 3, "spent": 0, "next_cost": 2, "budget": 6}, "CALL"),
    (
        {"used_calls": 3, "max_calls": 3, "spent": 0, "next_cost": 0, "budget": 6},
        "MODEL_CALL_LIMIT",
    ),
    (
        {"used_calls": 1, "max_calls": 3, "spent": 5, "next_cost": 2, "budget": 6},
        "MODEL_COST_LIMIT",
    ),
    ({"used_calls": 1, "max_calls": 3, "spent": 4, "next_cost": 2, "budget": 6}, "CALL"),
]


def grade_admission(candidate, cases):
    rows = []
    for number, (case, expected) in enumerate(cases, 1):
        supplied = copy.deepcopy(case)
        try:
            observed = candidate(supplied)
        except Exception as error:
            observed = type(error).__name__
        rows.append(
            {
                "case": number,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if observed == expected and supplied == case else "FAIL",
            }
        )
    return rows


visible_results = grade_admission(decide_admission, VISIBLE_CASES)
VISIBLE_PASSED = all(row["status"] == "PASS" for row in visible_results)
print(json.dumps(visible_results, indent=2))
print("VISIBLE_CONTRACT", "PASSED" if VISIBLE_PASSED else "NEEDS_WORK")
```

## 4. Connect admission to the loop

The loop calls your decision before every model attempt. It increments calls and estimated exposure before invoking the provider, preserves assistant tool requests, invokes the real Chapter 2 dispatcher, and appends identified observations.

```python tags=["integration", "learner-path"]
def run_loop(
    model, tool_dispatcher, initial_messages, admission, *, max_calls=4, call_cost=2, budget=8
):
    transcript = copy.deepcopy(initial_messages)
    model_calls = 0
    tool_calls = 0
    spent = 0
    seen = set()
    while True:
        decision = admission(
            {
                "used_calls": model_calls,
                "max_calls": max_calls,
                "spent": spent,
                "next_cost": call_cost,
                "budget": budget,
            }
        )
        if decision != "CALL":
            return {
                "status": decision,
                "messages": transcript,
                "model_calls": model_calls,
                "tool_calls": tool_calls,
                "estimated_pence": spent,
            }
        model_calls += 1
        spent += call_cost
        try:
            turn = model.complete(copy.deepcopy(transcript), tool_dispatcher.schemas())
        except ModelError:
            return {
                "status": "MODEL_FAILED",
                "messages": transcript,
                "model_calls": model_calls,
                "tool_calls": tool_calls,
                "estimated_pence": spent,
            }
        identifiers = [call.id for call in turn.calls]
        if len(identifiers) != len(set(identifiers)) or seen.intersection(identifiers):
            return {
                "status": "REPEATED_CALL_ID",
                "messages": transcript,
                "model_calls": model_calls,
                "tool_calls": tool_calls,
                "estimated_pence": spent,
            }
        seen.update(identifiers)
        transcript.append(turn.message())
        if not turn.calls:
            return {
                "status": "COMPLETED" if turn.content.strip() else "EMPTY_REPLY",
                "messages": transcript,
                "model_calls": model_calls,
                "tool_calls": tool_calls,
                "estimated_pence": spent,
                "answer": turn.content,
            }
        for call in turn.calls:
            tool_calls += 1
            result = tool_dispatcher.invoke(call)
            transcript.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, sort_keys=True),
                }
            )


INITIAL_MESSAGES = [
    {"role": "system", "content": "Use stock tools to prepare drafts. Never purchase."},
    {"role": "user", "content": "What needs ordering?"},
]
connected = None
if VISIBLE_PASSED:
    connected = run_loop(
        ReplayModel(OPENING_TURNS),
        dispatcher,
        INITIAL_MESSAGES,
        decide_admission,
    )
    print(connected["status"], connected["model_calls"], connected["tool_calls"])
    print([message["role"] for message in connected["messages"]])
    assert connected["status"] == "COMPLETED"
    assert (connected["model_calls"], connected["tool_calls"]) == (3, 3)
else:
    print("CONNECTION_NOT_READY — repair decide_admission, then run again.")
```

Trace one `tool_call_id` from assistant request to tool observation. Final prose alone does not prove the two draft tools returned valid results.

## 5. Save the bounded transcript

```python tags=["handoff"]
ARTIFACT_PATH = Path("ch03-unit-a-handoff-v1.json")
artifact_status = "NOT_WRITTEN"
if connected is not None:
    encoded = json.dumps(connected, indent=2, sort_keys=True) + "\n"
    ARTIFACT_PATH.write_text(encoded, encoding="utf-8")
    artifact_status = "WRITTEN"
    print(ARTIFACT_PATH)
else:
    print("HANDOFF_NOT_WRITTEN")
```

## Exit ticket

Explain why failed provider attempts count, why call-limit precedence matters when two limits are exhausted, and which transcript observation proves each draft tool actually ran.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch03-a",
    "attempted": 1,
    "completed": int(VISIBLE_PASSED),
    "failed": int(not VISIBLE_PASSED),
    "skipped": 0,
    "connection": "PASSED" if connected else "NOT_READY",
    "handoff": artifact_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: Admit a variable-cost next model attempt

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

Implement transfer_check(state). Fields calls, max_calls, spent, next_cost and budget are validated nonnegative integers. Return CALL_LIMIT first when calls >= max_calls, otherwise COST_LIMIT when spent + next_cost > budget, otherwise CALL. Equality at the money boundary is allowed. The next-cost estimate can differ on every attempt.

Write your expected values before running the table. Keep one accepted case and one refusal.
Your function is passed directly into the driver below. The driver copies inputs and checks
they remain unchanged; it does not replace your implementation with the reference answer.

<details><summary>Hint 1 — identify the authoritative inputs</summary>
Name the source field for each output value. Which input changes while the rule remains the same?
</details>
<details><summary>Hint 2 — choose the boundary cases</summary>
Start with exact empty, exact equality and one value on each side of the boundary where valid.
Do not add a special case for a visible product name or operation identity.
</details>


```python tags=["exercise", "transfer-owned"]
def transfer_check(state):
    if state["calls"] >= state["max_calls"]:
        return "CALL_LIMIT"
    if state["spent"] + state["next_cost"] > state["budget"]:
        return "COST_LIMIT"
    return "CALL"
```

```python tags=["assessment", "transfer-invocation"]
import json

TRANSFER_CASES = [
    ("exact fit", [{"calls": 1, "max_calls": 3, "spent": 4, "next_cost": 3, "budget": 7}], "CALL"),
    (
        "next attempt too costly",
        [{"calls": 1, "max_calls": 3, "spent": 4, "next_cost": 4, "budget": 7}],
        "COST_LIMIT",
    ),
    (
        "two exhausted limits",
        [{"calls": 3, "max_calls": 3, "spent": 7, "next_cost": 1, "budget": 7}],
        "CALL_LIMIT",
    ),
    (
        "zero allowed attempts",
        [{"calls": 0, "max_calls": 0, "spent": 0, "next_cost": 0, "budget": 0}],
        "CALL_LIMIT",
    ),
]


def same_transfer_value(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            same_transfer_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            same_transfer_value(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


def run_transfer(candidate, cases):
    observations = []
    for label, arguments, expected in cases:
        supplied = copy.deepcopy(arguments)
        before = copy.deepcopy(supplied)
        raised = None
        try:
            actual = candidate(*supplied)
        except NotImplementedError:
            raised = "NotImplementedError"
            actual = {"unfinished": True}
        except Exception as error:
            raised = type(error).__name__
            actual = {"raises": raised}
        expects_error = isinstance(expected, dict) and set(expected) == {"raises"}
        correct = (
            raised == expected["raises"]
            if expects_error
            else (raised is None and same_transfer_value(actual, expected))
        )
        passed = correct and same_transfer_value(supplied, before)
        observations.append(
            {"case": label, "expected": expected, "observed": actual, "passed": passed}
        )
        print("PASS" if passed else "NEEDS_WORK", label, "expected", expected, "observed", actual)
    return observations


transfer_observations = run_transfer(transfer_check, TRANSFER_CASES)
TRANSFER_PASSED = all(row["passed"] for row in transfer_observations)
print("TRANSFER_STATUS", "PASS" if TRANSFER_PASSED else "NEEDS_WORK")
```

### Design a counterexample and retrieve the mechanism

Add one new case with an independently calculated expected outcome to `TRANSFER_CASES` and rerun
the driver. Change one condition at a time. Then deliberately replace your candidate with a
constant answer in a temporary copy and show a case that rejects it. Restore your implementation.
Explain why that counterexample is stronger than repeating the original example with a new name.

Without viewing the worked example, write the invariant in words and trace one observed value
back to its input. Identify which part is a local fixture result and which claim would need a
live provider, host or external-system observation. Keep a first attempt even if you used a hint.



## Instructor explanation and additional transfer cases

Admission concerns the next exposure, not only what was already spent. A failed admitted attempt is still charged by the caller. Keep the decision and the accounting event distinct in the trace.

Ask for the learner's first prediction and attempt before revealing this version. Passing these
cases verifies behavior on these inputs; it does not establish independent student mastery.
The original core holdouts also run against the connected implementation below.


```python tags=["instructor-check"]
INSTRUCTOR_TRANSFER_CASES = [
    (
        "free but counted attempt",
        [{"calls": 2, "max_calls": 3, "spent": 7, "next_cost": 0, "budget": 7}],
        "CALL",
    ),
    (
        "new estimate",
        [{"calls": 0, "max_calls": 8, "spent": 0, "next_cost": 11, "budget": 10}],
        "COST_LIMIT",
    ),
]
instructor_transfer = run_transfer(transfer_check, INSTRUCTOR_TRANSFER_CASES)
assert TRANSFER_PASSED and all(row["passed"] for row in instructor_transfer)
```

```python tags=["instructor-check", "core-holdout"]
# Instructor-held checks appended after a submitted Chapter 3 Unit A notebook.

# ruff: noqa: F821 - executed inside the submitted notebook namespace

import json

assert (
    decide_admission({"used_calls": 4, "max_calls": 4, "spent": 9, "next_cost": 3, "budget": 10})
    == "MODEL_CALL_LIMIT"
)
assert (
    decide_admission({"used_calls": 2, "max_calls": 4, "spent": 9, "next_cost": 3, "budget": 10})
    == "MODEL_COST_LIMIT"
)
assert (
    decide_admission({"used_calls": 2, "max_calls": 4, "spent": 7, "next_cost": 3, "budget": 10})
    == "CALL"
)


class HiddenFailedModel:
    def complete(self, messages, tools):
        raise ModelError("hidden fixture failure")


failed_hidden = run_loop(
    HiddenFailedModel(),
    dispatcher,
    INITIAL_MESSAGES,
    decide_admission,
    max_calls=5,
    call_cost=7,
    budget=20,
)
assert failed_hidden["status"] == "MODEL_FAILED"
assert failed_hidden["model_calls"] == 1
assert failed_hidden["estimated_pence"] == 7
handoff_connected = run_loop(
    ReplayModel(OPENING_TURNS), dispatcher, INITIAL_MESSAGES, decide_admission
)
assert handoff_connected["status"] == "COMPLETED"
Path("ch03-unit-a-handoff-v1.json").write_text(
    json.dumps(handoff_connected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print("HOLDOUT_RESULT=" + json.dumps({"unit": "ch03-a", "status": "PASSED"}, sort_keys=True))
```

## Save your evidence and explain the result

Fill the prediction notes and your explanation before saving. Include the exact observed value,
the input or retained row that caused it, your code's invocation point, one failed hypothesis,
and the strongest claim the evidence still cannot support. A completed code cell alone does not
earn explanation credit. Do not label reference-start behavior as your own Unit A construction.

Keep this edited notebook, the Markdown if used for notes, saved handoff files, and the JSON record
below. Your work folder survives scratch cleanup and can be reopened in a new kernel. An instructor
can ask for an unseen case after the visible checks; keep your implementation general.


```python tags=["course-report", "retained-evidence"]
explanation_notes = {
    "causal_trace": "Explain the input, learner invocation and observed result.",
    "failed_hypothesis": "Describe a prediction the evidence changed.",
    "remaining_limit": "Name the guarantee not established by this experiment.",
}
course_submission = {
    "unit": "ch03-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch03-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch03-a",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "instructor",
        },
        sort_keys=True,
    )
)
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.

<!-- #endregion -->
