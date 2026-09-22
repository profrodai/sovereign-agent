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
    instructor: false
    lesson_id: skills
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch06-a-versioned-skills-exercise
    self_contained_runtime: true
    source_basis: 444c5f6
    source_unit: ch05-a
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch06-a
  jupytext:
    notebook_metadata_filter: all
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.5
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
  language_info:
    name: python
    version: '3.12'
---

<!-- #region -->
# Chapter 6, Unit A: Construct versioned skills

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-09**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch06/profrod-sovereign-agent-ch06-a-versioned-skills-exercise.ipynb) Runs on Google Colab as it ships today, or on any local Python 3.12+ kernel.

This is one of two practical units for Chapter 6. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. Construct context assembly from active eligible skills, explicit preferences and revision-matching completed history. Enforce the byte budget and retain provenance before adding the current user request.
3. Solve **admit only complete skill requirements** using changed inputs and an independent expectation.
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

Open this notebook in **Google Colab** with the badge above, or use a local
**Python 3.12+** Jupyter kernel, with **Pydantic 2**. If needed, run
`%pip install "pydantic==2.13.4"` once in a separate cell and restart the kernel.
Package installation needs internet; the lesson itself needs no repository download, API key
or prior notebook. The closing extension can use an OpenAI key from Colab's Secrets pane to put a
live model behind the same tools; without a key it replays a recorded transcript and says so.

The collapsed cell contains 90 frozen teaching files. Base85 represents compressed bytes
as text; `zlib` decompresses them; SHA-256 checks that the decoded files match this edition.
These are supplied packaging operations, not learner algorithms. `tempfile` creates an isolated
working copy; `Path` handles file locations; `sys.path` tells Python where the supplied modules
live; a `.pth` file, the mechanism an editable install uses, tells reviewed local subprocesses the same. The code is available for inspection below and performs no package installation itself.
The subsequent lesson teaches the libraries used by the mechanisms you will implement.

Run setup on every fresh kernel. It writes scratch runtime files separately from your retained
`practical-work/ch06-a` folder. Rerunning setup restores the frozen support files and keeps
your saved work. Restarting a kernel clears variables, not saved submission files. Source basis:
Sovereign Agent `444c5f6`. Some tasks use reviewed local subprocesses; they are not an OS sandbox.

<details><summary>Supplied offline setup and teaching files</summary>


```python jupyter={"source_hidden": true} tags=["setup", "embedded-runtime"]
import base64
import hashlib
import json
import os
import site
import sys
import sysconfig
import tempfile
import zlib
from pathlib import Path

minimum_python = (3, 12)
if sys.version_info[:2] < minimum_python:
    raise RuntimeError(
        "This edition needs Python 3.12 or newer, which is what Google Colab runs today."
    )
try:
    import pydantic
except ImportError as error:
    raise RuntimeError('Run %pip install "pydantic==2.13.4", then restart the kernel.') from error
if pydantic.__version__.split(".")[0] != "2":
    raise RuntimeError("Use Pydantic 2; the tested version is 2.13.4.")

# Frozen, reviewed course files: data until explicitly loaded by the lesson.
COURSE_ARCHIVE = (
    "c-ri}3v=5>)*$*<@Oi4P$%LXw>P;_auOcfG-#C_6Qj(pLR4kAHC5$P8AxO&_m;U=buWocV8Xzgl9(zjj?ZzU|=;!"
    "J4etdd1NYnQ(!trf*m-W-hi{W)Vd_PT-$vlI<TkYob?pZf@c0vDlcpXmX@hoU}gLD!H@yF>n87A}KCXM28FpK|M#"
    "M!(N+$QtuAe;p0Xf#fs-7L<g=_HGTQSx!Vn8i)*?P78<Np7a;Y#xNOt7$mPV*Oy4PVe-O>oB_>Cj<TaUs(#Dj%Mj"
    "iu$YbEO;d&rq`@y|XYWqpD4E5>`7hxl8ppFnaH6I+SR~`9pHAaRJi|Gh{&M^-=mnoHCIS5K;@NPK&C?rr2MfP=_G"
    "U4>yLi^fU(ROn1RvqcfBf{$csHG;(PB8y@ZC8-#Q%M|c$U3i@CT>A{=V_Y!Q0nw-W<S(@L&?&#Qf@yaFUG2AwNzh"
    "{cD&wzUkoaS)9(Ic-E(r!KZuojq(u=e>pxpesgek<c@K8oetA+IFAdXwEe^ER1I@_c5?9NPe&&w|8&PWozKGCK|G"
    "t?6$kQ;v#rLtgn#exR4yh_JPK~&EDNvVtd?D;(|VWN%wm9|iM_@8Pd<uSI+m$qciB9?(WjI*8K#qY%%fjC`*W7e;"
    "~)%Rm>I(JY?4f_0)T_z`(Q9jU?!t<79cD%1B6_=tKR{()5-WQm|w?1wwS`Th$H!W6aqvvgSW6ZfdY_V5RcPaY@N&"
    "k*^7WLov-^>X)sCW!E`Yj!c~B2PVVN{I6s)ua2zH#&{H_48%I6GACnAvvexXJW4=F&3?aQ?ZwTJ7X0*7O^2RrU47"
    "R2JKEBI(XR}3I*Qb@A)HJ*sr(q=R2_y6_p8a(jPc|=}IVWcv*Tpkxii6T04eOPhKE1Ud!D^PxXK{FgjeZWtS!}(7"
    "v!BMZ5YY}cXxaUTAN%w4eLSHNI@>$eTj&(F0rt5ckKptLQYL`;^v)WP3az6)fl4h(hl?B7Nww-^MCX@e$t0VHlVP"
    "k|G=eA@>UOk4VFD-oM>t-@N3&TvtKqraOvmv&Nhd)(`2dhJje{G&Q2<4B=7WC$nu9&&PKMWMGK@1oXljt=RXoRT_"
    "=Rp*oRzd_1Y>}oIzrbto~Wnw;D366_$z0MM8TLXVr9U=kux`#n)G?zx~!gy><<AtJ&?7Gl1Y+X_xXgNdz>4>K{|y"
    ")T6Hs{B%)EdGx&3M6OPAsdbR>_db%>UJjOfo>ArL?rIoP&c_O{c({$V)!gzQf#n-cVw8+A7esfBe69!X2028(AfO"
    "QyK-G&*GX8;Ui`;(D73Sj}+y)erXocw&*7V3u9SwmOF1E0qq=dgeFs2b0dZXSLHIA=bioxzv*qzMm_X>G}l;QhRr"
    "&hKO+3R4mkgdOIWmr!+|Q1uc@Q=6U(6})T&__ro)@Eh<+t;LTW3U?W7IIZjTyi=qt(*TYU(QM2(^xWhppl?9Fy>W"
    "Omh~UV(K|YIm0TUAoC#Xnv(pVA@9v~4t-ckBdlP+Mm!8pD_)NyX&!Sp5pl7$3ICIrudA886q@h^QVDJ&sx1P5;KM"
    "ex7;dj@aKVbpXPTqe8}y?j0V^$dw5ya#B2+cAVoVbJ9n6G<j{@>)?&c_?%?vTq;GT6axDcWpwg_OBUEfwzos^c1c"
    "NJPQ^R9Gwm~03d@4)0Iu69&ON6{TSdm38%23^L`Tfz*G3+W_BF{4XZ69-c8_Nfz;OO_2zZ_F-m}_&JhOGXv7~|<E"
    "Zfw6#`@4jN*8Te{ds*v_Dg=kzQIem%r<{$%8Z^9$K>v>ZL_eKP2(3Kr+q>>7}Ne%!$wY=0p>o{rudV#U<i5b0WSk"
    "ORxzxfeRH*u8^Ti067sXDR~3YEDiWlKMI2p$UE1Jeq2Q8V-m_aBfy69MaFE$+oPjbr~RJ~4$po+c+)>Q`s4M{pB9"
    "66@hqB!BieMj^yZt<IJ}~Mim1Wb3x})HIFU}$K#{(W<lKNC%`%X+fPBSD1j}k3flO^YA2h$}%O=*ccsy$0mNtSB0"
    "5F0pVAt%b5nRI##xvkiCh;u@e@l)}jTsO<jiZ+V{FhD;h|nmx0<JIurYa(g6L4GM02C08lMgWw>KcNq8t-qx0bHx"
    "$`*^;Q5`T#_aGu=6=>j$t@lzPg(|I@s5E+j*hGP^3t`^}8$YvZj10_jss_tNXLY2U|;q>04D2SK?1gS|zLM_fe7_"
    "f{1ptArm4yG0WT?H0T0TIJsPYJs<^FXiX^J(|R3z$kczD~1wx82^_+<Nh$4T63+e~}aO%mS<^oQFLFr_eTN9AY$-"
    "qv-((IAjvPadtNqF(X9eJEVPjLGt@EB}2#sAf<sRn%7()0(^yUYFf`A``z1Y)dRSQO3h$_#4X)Ae$mA1SKHa{Z*T"
    "7Aya)2Q(5@c*J)l=R)gYyn8S%$q97jT2hJ2pS0Ug|dAURHeX1Xi~?I9w&jK*USJO26SH?Q9w!HqtBcl`GB$WlZoj"
    "=ftc>pIMES98Jzkyo>>UAGrkYBrd`hOeb1Jd5T6=}^!K=8Hi_lsnT(0D9Bz7DQX_YmlP4Xcn&}74xTBpTQ&W;Ef<"
    "0q;NBkYq7ckDLiFDpF#T%IAA;pm<MPU7HUe&_nONvbrZmNYi^X(SIAc>RaWz0c0~yO9lfbVaW(|@6)!-q-v{j9@7"
    "K*wn_(37L-_{aY-0m44{{{TF!bnDXK{ZHG+cvL*|#E8HxRvsi}BnL#rZ>Mjf|drPyb*KnPLWsszC#022e$&UcmL2"
    "=SXImj$h{Q&b35;$-9v?`8U(S*`0B{6b*!i4w}V_N#El0AO@*EaBqrnONmdQi(bVr7>mHWJDmr$<5RlU4daTN6h("
    "F?{+O7U6#v&Q+^ye82Z}2QMqx4rhzd^UA>i#}xEePh^Rf$gOT1`2Cee&_9xpvQAEMOMRx4fMtN8+`Av{Fc8n!YAX"
    "yQaNq67e*CMav>J|WO}^ZJjY;J4#fM{feXk<UE4eeq28TQ>`Se*J&Xem^<NVUN1xJwMm%$7POL^()~&F3qi#`TQB"
    "Os*RewByHIu9IGQ$(pwinxzL@UP#CG-M-idl4|*uc_WO7>`+Y6Q@=d*%KqpJ|-5syKy8}EGP_l@mngB)jEC38M<F"
    "iD~UNYIZiEmOsb)`CPOQp>!Z22);Oz;&cw5Q=5d3mMDeg{7<l(Ktz7Xe02hU(={AUY7(HG)H8XI>>kfb*Y|cpT}E"
    "GMs3fTuu7SDG<c<i6BWgXRw|_fZLJ}NK+9d8O&^Wt-g6BzfrM%^f4YT=E$vJPliUF*42dn_Hk7;pa(TvPp#h{!36"
    ">Q*F>UEM@RZ8vNiyC)$4G`*asn&cPFn8k4}j$+Uj%E*tHr(m3KGTZ0YBwjv7AL-M0ADx2eL?SxxVz!T`Ke%qYU}`"
    "4-oJbDo8OQbF7tBoV?UswReWmaohK-m(0fk7A6drK|S~WUrBU(9zXy0C<5bxtd@1+N4y_zgjJ;_g8r3^1j`{)Bt}"
    "i5NzgmUF0(LC|C0y?9w>KUR$pC*C!yigg~vlhLf13w^{+wb!0+#S0_On{_tx8?k(O+y&yFdJ}7>$gv*Z>%v)*&dy"
    "qsitynmDC1;QfQ|nvZ6*N4=WBu?0%${r-#N&|ynw2}ebdP$6Ul<CWd%I8El72()3Tt}QBAdw^B>tMI6uPu#F3O7<"
    "qG?AfL6{rPLa9YmpN@KhH}2Q?PHo#_@_v%u>h>D1`^8Za3fcanhAdD)HBV*?$BW_J2FV*f`%9@MEpM}!By+fd*}M"
    ";o|B!f7MhE9=2A4LMmhTvmqr!IK?)UT#<-O!B_`p$Vx$b!v4@F%(glz8DdnOhz>u;iDG(t|5kTNSBKt4lOpI9dB&"
    "pNWd7U>+7)f!X^xCa*6Q!B17J?tNTpdJfnq9&-}Ks_k5Bmp=-IeSZf;0d354*9YOR)!|z)ycunXSQuiojX%zOMPh"
    "*r<&U_S~~iK7Cg{*0^%a=ywG&w;i4Egf*TaMkP-{D$f}Y!E6NcD#&_P(xF)OCSb5(0J@d~xR4@(_saAaA^l`J1`5"
    "KZM6K-8Vn_ir@3q9`KrPGH^pDt%#>0I5nz>EwRB-Mp{jafOMK?j&ZU=io3>^^Y8F*0LHZ|gY&n@~D0X$a3cE-mRj"
    "=Xh!aW+0c1Q41XP;DY`;o&a-BFPg~C5VFT#xXIMKUM~?G70jAs*N{}$h}`35&1CW+eIM5p$5u<Co+#>&3Bi$j4on"
    "A1EX;bJ?&}ukeqJ-lxWaUb;9c589J_<J9}rc+ONH&O(ll~sm+z!KPZ1FGJZ&H_CtBq&VWOWMWq-5QW$3DKdIkNr5"
    "@f@bXAVstb>29QWmAVSeKUV-foIbz@N9Mo?*VrJ$Zed0&_g#6DNuMvdP$`Q%g{m>lK37FrDwKz1s9)nMW8oF2Pbc"
    "jPF9jDV0P*FLtLw)W&_XWynPwGKztvAycy5b%2C*Wo>5x|7aDt{#r6Uj3?QCg(gn#Ms+J_6pmJNpF#3lmxz&em;d"
    "GNXr;h0786ca6hCizt{od(D3vkaamGsp=J3fAMYJH7tHRBf^?CA9L;2$Jd3Awav50wryj{fhLcswQF7=Yp!H{4-W"
    "=)z=8kUM7CoK++_j<QvI7tel%y^BMTG!-vTkSBEZ?*VXR)PZpcxkdajMBP2R!l=vUb}pVYOjNW$V~)@ZTFu~eadQ"
    "*Sl7F+Qfbcj#)M5;6Eu!i4eh>f|8j$v4nBKtBBen}fDO?jAm+lWx-r+2UH<K&so+mTEo~4VcYdv6L=Cp^TCWU!V("
    "<~g55u}9hDdlC!nTpd->50CpI7enk#RL?{8J^COT;tA!H|b(BccyY_8;1~!5HNR@svH0BU@^Z=(IAuKmN{B8aAq*"
    "|U<Bm$C2kP##;JG(WXkz4iib&twhIIEC{du_Pmsmzi&+WDxg`|f<0d_Y;|D<uC_FVW`%n%R(ueX!Y6QXz{LskFKP"
    "a)oAJfHLyo=1iYz?TvU`*nVZ1`%b(NzP{R-Vq&>Fc=|o4kTVj!#TOh2mc0kJsTMV}}qv#JA|nq}dWQuAsLQ4PPsF"
    "fzW8EM*b^3A3L(qUX3AX)J?82@7Z3Rj8n7#=#h)BNDk9%$HoV*A%g@yA654^eGrS{>8sxOoTX%6b}6n`r@5M~RaR"
    "3kkqL~`6?E1OK8WdPM=Upn&1j1ry%aNQXQ$O-tczHN6yFN%!HusM{SkQ+;t!|_8pbuo-*rF22`AYtiQ34uUniNmG"
    "B3rFdxiE$m;^dJhZ9EXF|xwpJe_HTqfQ{pZFmZJf&8ML5OrnzYqXe<RR^AxxzQ;1vt%N~r>Wf`t#(8Xp;5ViStB@"
    "C{JQ9*(g6^F4@B<H4cD3SA#IJ5JUv$=<&r(fa7@d2jFu1BJDGscpr4Wq0V5ms(7Z!Uh8%qgeI#p3-y;S~n5H6Q>_"
    "@2N3~F^kr$e3O1L}?HCoJ_4M{Ql9u18*k`O}mPnaFOXwpe=u74A)qIx++>^*g_D#zRY)Vm!~)Xy%R?l7;MsC>+(a"
    "Xq~2CoA2^(HG+1Vb?Ky^GjDUPfcSQx^|q(=<$sCEwCqE2(V&Sg8+w`1m06iypyh=c`%&jsRG(qg;HPR14VQi+t-F"
    "BEbMXMpx4G5<0H|iY6AO$6BSZ)+eUa?Lb88r#gZv{xMT0#cvK~uMwYp<6B;3MEy@p0LY;Hl6rJv<k%+~><ZGAdfM"
    "hMN1_-!jFUt!gT>D;@6(^EEuN>^eB{rTYa8`D>nc0WJ!f=$zq;T<H}0K|%hiC(8}-^~_VOO0J&EOdDM+q*YMXGgD"
    "KUSvNuCe~h67r?CHDM@ihXvyYFxRQ2Y%c~vO>H;O6p@RtS9=d1E&_f5nzCqIjQUW+u1RRjY*nbYF>Vo)CLh&Ex>q"
    "Y_j^ab(@o%~VsU%`eti$^iy%NUUR6)+$FCTgBF>9#h>;;Ftn=J2Ickefxk&p<}(qfvuhYWq3pm)K6}zpPWpC(fFK"
    "k`I*MO<#5?&|5KKhdtih28!CU61pxo@y(!o8oJlpboO3%iJ>EnAfEiSh!=2->_=461$u!E$oW+a!18-#D|4;`F+{"
    ";*p+=@K=#kiNOtY+(*c7%j+)MPk5vm&c>f%8oCF-m!&;9WJ)?;h)b)IC@yTc{;r(v5))r+DnCSPDv&$N7wPXu;F0"
    "!x}6g)N$AF@k0|yL&|*hUx6ChPNvD*b~zwyL4<Iw;5*i9W}Q+grLJ7p_rO}Unf-~Uxe(haf0D?hSSpkK2X=Eh8@&"
    "R;1vv0iv|`{@co9T4Y8{-(K75nsDR4eGaoPUYp~yNUMdI=zj`4+^rCIq4x>SHI8I?Y^%ds{U<!~%^wvN`h3VxJsO"
    "wlCIwzoGhzz9{<bhL==17zvD(23$=s0vRLQ*t~h2s$qA>E&1${)UoAr3G}QGZvyjU8(n?YZS-ktVnLKCL<Z5e6>J"
    "`S1DlERKW0Vhk7~^UQbCny;XK=`kHg8*|bw+x;tLVCeX?lazBiAq+#bMEW75w}F%fx6}-CAp%3K=sRru>iDfhsge"
    "RY%-&}uyWh0?A~INUl-8vZZ@Zo%qlNFP6rN4OIt62&X+alwhD+}O8s(Rvrokti3%Z_eoMT+=YXyBj!`7s8crB7Pd"
    "~9=GU0$<yt`#E{*NbQ)olF?Wn=#pZ(Ut4;=*`jL84S083H?wHem*(=EwGsoIH2Yz2HpuMXAOZK?|r+tm}BK#FKYE"
    "!q;EMbLp-kh5Iu=+D<OJS^|l2~itVs?7e~A=7vK;{*<qzU6;tYn@1~$<zhQS+hdVV<w}p~G%1Ke6Sl=B_S;$PHU`"
    "mn>4{Vbxi|OG@=crMvE2!p)W-bvTQ8(7MK`_6E`LIoS<Xyg+g$v6}w|pbI4Sz&sA^Oz9UuC@+%07V`8zUkddhp>&"
    "BDIG{l-tMbVUZa{bi?fKDtN`$%L*8(3em0Cr54<c1F>az)J#}nyhBW6({plC6ykq+bA0$K%F$Z2U?~qwjB_Z0*9@"
    "(Y65esc@<|cjsE=M*3We?(8il1=g@<Vt%DB33UE{Fr)i`XUgDizpi`qSAIp72Tg?>$xf<gHp2vdlr(qSB}mU85K&"
    "@WW?E_;L42^r$>;1rc{L)f7NB>1>byPf6R_{H@Wg7np4^)rlY6UDI7X((M7^S2G<6%7shDr{3dL?F<8)W4Fh;z_V"
    "xO><4rp%??v3k+Ic<EZuS1DPTZnzT70FE>;SEnHpdC-BO?WvTz+5+94%YVJAb=eSAn761*vAA(Fb2zP9JXgBBS&D"
    "dO<MlZ+{<~Nk4%>(*m<ROKx4q{kL9OS5rXeWgMSO@@j24-iwE#qa)#D-~XwaS6OUDONKLAv8TjRR{I@HQCp^ccy&"
    "+Ojz75gtA7Zn`EmnS!$M@z1)~8tLNTym6Iph>bTrMnu@-;zK<aIiprK_<)N1bmD2Fwx>t)^)yhyS$*E4TrwVAJo|"
    "*tX!QGT3*d+i)toya-^_;BU}?C#<eu?ezi?E_F?qSBPZ!T}KqGf@Ily~A17)#=8p!2LD2c<#(a*o1BDYj`g_|PlW"
    "dMUm(9Qd&?bO#mW+?nKzCuyF5m?WeO|xb6wRL*V%?v#XHt(H;DJU>{kfiv?A}a8FH`95!fY&Y)MBx0B3MCQu>(c~"
    "%vR$0+y_zB3x~m18F^M!vSmIHaYju80fW-oqR^2*wON4teUI4ejC*zY)JaTyTx{8wZO3TSTP_l<9xR!riA}=e<U8"
    "^sZoVBdEis-YJIQlq(paiG)9;#X6?+d!M;xykWmr<G_fA(1dX(?(Y9>w4@yRK`|{lkP;*-1PpwQD_i^YtXv9j~Oi"
    "(+xo0Bo}$uBP891Z4vf6<78P2vX0~AbrMabM+p`HI5Sjn&hOS0Thr`Gg8grhVEqPr#-4qx?h*q&Yr;seg$n6@?nv"
    "_$<YRxxcs!1;X5mdAJwGP#SVx-6^M(R;xK=Sxpma=<_B%jk@6LkWV>zJb()(hHuv6o(;1Pzc1w=D??apRZZc6@+J"
    "OjId@wF#Or6;Kh2x>4>e({X^pivPeCRu;LDYD2-@xB-ydmYaGpU!ns9l<bpE*&%P<;OXP%i^AT5`kKA@N$uVN)?_"
    "DheTrNEas>P1$0&ERL?tAbgP%=(2@M*yiZ3XV4*U@5mmp+Sdm_Mj#QzK-tv8f4%9Y?r>EiFfsWM5vtxdZL0|~<b="
    "Qp*UomO8is!$}1fTglIb@zn(!<^``j?&-T`&J8PI-vr;}7u!_7h{R$8m&t#PDOf0Ryyc#jpf8>@mjp$C)TFqgVyC"
    "BmMWv5a#xJcFvq>z39W@Y@%<;rTbhAJUHXf2c02uh|(KHa@?e}z`=r}U+!RiSxKn5x=C`~_FJvsN7e+WHJQob5c-"
    "mEocvql809@wCgFH=ERuNAE7WwqC7ns77NDR3sFePfN&Z^umt2!9R}{4u<@$n}hbvfJqvGlW9#zR;dtF8YBh?@<2"
    "f4*gQ&`LKY&D6tMBb7vo5BL-4^|exiqel`lWzEg??zD)G#+t2K$%KUDQay#qh`q>dgA83D$WDZuI{DCj@WzKsyCb"
    "n*hf<Xd>JwCQ7w)t*C&0Wni#QIe228fVNDgb@Lg3pY(kU<5?!v$Hg4*Ga)IVtL+xBRtafWtu~z&0`*p<^!1K2Gqf"
    "<BUJ!eo%N$@qaD!`lFo0Kae3q&e#1XF0_UlvsqNI2jVigW1rlw3lhl$0h}1#`t4er)OJS$1QNi22yAVvV{mR};Hi"
    "ntOfaS5w?8fp9}JmTM{XphbyZ@0CuI1HZ%fxrQ&pJY{;_WjpNAYC(&ffdfvh)d<?HtxNaJoa8!~XP|XiOpYU|21-"
    ";Pp6q|33`ruNgHiD3FGnXw0bl*z^OK{4SO0t-9G|>8IthOICx_s|&4WRa-6&N=n?YF=zHEDTOi{<8eLEV4jL?I%!"
    "!nDT#@%@RG_n|09`*C(S05~T2FIjGP?IWjKt6HwuzZqj&m{A%#k<+-Cjr-gNR8Cxpji+k=?>}@%PYdNjSq#`<r_|"
    "W*YNm06<1*BhrH@WM+;T1b>vyEckaF|m42!mbnM0Q2j10sb$W+72RzHkbPgRGYkQb_)E9f42nkA+PO8h+Wi7LN@k"
    "6nbQ(p1|d-)t(cd!74JH!k<$c9X!HHS862yPn59u6UqCZ8Cat$@H3y3%?+zgOfvj#E%1{QmaWx5t0J^(4zVJ$hTn"
    "hLn?`VVq3o6$<5v7o*zhWfWkc55}kOlS$Nju4mm8PJ_1Sxrs-Ys-REEn-h~N!ujZ_iXS)s_y#rO+H+m)Y%gfLO6Y"
    "PBRtoH|<X2*7sWvtg(_#UO*XP5^={%nHC|^Wy2U02OC5VNHIQIhbfw*{*RL}-yFjS&K(%r2*(OH@ji-dZv9<rqkH"
    "4PngHg_k2WIleG8^`cEp6LazIe|)FoQAn4=o`oi8&rvkYp^+Xz_)t&1ilS79?^)f?ME@Weg_=aAS9`BSp(!@)_7a"
    "h31vYJkg%Z`YOj6$RBo{>cfH)8>PlG9WR~0zfi7j(<cetl%8uJa*zyEy*|Rq;OFrMw067B=6}YNA|CsLsb~w$N@#"
    "I4?0~EzE>!-(m0Q!9WkGK7Ue*nhrp8>l1$H~EO{j=j=kKQu-pC8juq@ktV9KSm{IXF8$In_NhGuS(9+Hec3@Z6-J"
    "3X0=2Of$)%<O;s1(@jPsNY61JdW%Cb@Fx;Bo>skd-`pH^@tjT&kp!^Y#38{=A)!0X5^^$_02I%FN-HXyV-g&YP>y"
    "VXd+a(LHFAmSy47fn^2#q(8VmF-&d?$n!f_5erDE|a;;EuBZ{u5~@2QkKRb`wg^JGqbi}~;JeiYgz(^WWwU&sh9W"
    "-86l0FW_KTbyAY(142SFw!PV#8zmIMW+JgY=Dys!ssTM&$$2r<`zt_&<Z-&W*No!s@^d1JSIw3Ze2v4kx&O`*JhS"
    "voP}cYg(JpEQt(DoWvzw3qZL?})dWFdRC@nAIC%TY6$|ZLOMW3Sc=P(V*JnYeWf91lp$(uI0pu5j^fk1Gi<u6*bC"
    "xnMbMkKp1Ia5l@vfFGP$F`~XMe~63n;nCx*(*eKW*E9>dYV0TFm94f?>Yh_?K#d($Vy~z9!n<^XcLlQ*z4;7!-Ae"
    "T^aHI%ewcA5Rt?#2=z&}#d!N#r)8pQEq3&l$wAh{^=E#F7{F=1FARctP?h;fzONUcTz1$_&U<dgLSC*bw^WH%f(D"
    "YP_rLKjNbXBM)XPSFiQpngS2r@w%E=t<t*gOH&7EH|Z&8hOF(0HK`<$XBccjTT)%#U8OqD%Y;dt1w4ER1)ApyX@g"
    "#FI27#ty4onjy5|5T_f;fu-|7z7XkhDDo-CY)Y@$JnHn1zt6U2-BIdPE+1u=|YaHprNPt9=Pdg$=CyOp6(?lk@K0"
    "3pY%>mxf;pxzr4rMuGiyeH}^Q=GDH7LbpaOq8BdceMHfM)W-6mDUWwc5go=}e7%du65tPSqH_8?R;STagcbUf<Nj"
    "(6r{>!>1t=5CCY-solr3h)Oe9aZIP~(-*W7SDE3@44?7VU9sx%*@oezq9Lm|1WLY}sO>o_xi)7nLun&pO3CWkvT("
    "COmt*OlRUURGQ~()dXj~Ji!^=t;b0vwtgzKs&r_cRA{T`E6X=ak?zmQPgeIPALIV({|W7v=yV>W`7(&6tL!m_C2W"
    "@CQV=+jakP^5>$}X2avQ#ntL)1pEf->>9>?o{#}k-7us!~B;hpUGm7@E1A;@qzbwua_$z>D&Q>zCX!REf9CeIT)<"
    "{$iMHBm&w8;&oTW9)<p#<sFMAzggke^38~w_%RF>$uOxtE|^<c~?Wg2Fzk|a}!4iIt36Q<*a^D@+_+Se}DJt;Or="
    "{J$Erv@afSRz&RF7?Adv4M0=0)lq8=?dfT%zA{K)cYQ@N&3i|_@)^O7u5d@hsZ_W$7c_rx^#43TS!Gn<F#Sx%OU%"
    "<y#+uD}3wW2E_==ANb*SIDh)pIk-YDYsRDVuJtbV}t;1X71~1&bGKdsEVkM9&L~=rZ$?H_<>i28xDN;1aS`0|sO@"
    "AdOEPfVA*tU-7lVjoLI|;TqT%D$^>OkCdv<4~qH@=`;V}Jg>SU+z)#?6+Uq}M5_x)l7Ft9J2S-?IZh!}`A1!!z|z"
    "#CW<y^Hl}d|M9;0LINX~B89Nf4fLIJ#slXqd41Oe$%(jRY((_1%3jkUsh(F+Bo3OkO@xL4H3xK*mLI~UR&L@UAuH"
    "-0c&=+7%)qWokp%Ul#JA-C)-9}_1g6TEk*#70~w^`Cls%HQbyqW9cb!*d_FlpV*HpJscVX|6~4!Wm53C3~(+ye#e"
    "0688_o78De`B;Ln&T^4eRzGd*Pk*jkIvzpXhD{yS^0k-^vz;yPDT*-f)o*n&ma(sNozt4Vq_v-bDWG_2-`w#i+uz"
    "&F8&Be2OuS-US3DsDf`1N}TmTLf{Ql9i*O0>_0Yq!yxH@|Vio?DOAv+sYS-0B=et3(Y%Y=#Xl<D4t-OxKoDMYOw8"
    "4jE-1qsyBGdJ`pp160{eWkV%xB|`^w3Rfc_YcH4Qh;<S+Gr*VZPCY}-)O<&!q3uPTXLp&vDXPcta5iovPn@j_k%V"
    "aZpM<*j&)gva1rz+c?iMJ6lj|9$S19upVU=ogvajDA6&uB~*^)+R+oMWAg^$D8yg!L=`{Ib_HY)X?S}qtBa}q>x7"
    "@@?X1d*F`lFmU88UnWZF{tggJUOcO>IENAos`vl&Kk)=xBn|2lzp~&i^$qqFELHz!>q~-I>y9?B&ZhCk<X^!t4ht"
    "iFq%zg$yGAxJ?EMj8qm82-S2ju`+70aWbrK~Z-S-e%I};cGt$b_Dr!IU`>ubkjtNJfJDx!{j^k;q)ogW~Nhmic)T"
    "`$Xjot|vJVGPzWw5}Cs#G*oRwWMfh;cM#Fx_Z8K<xxxoEJwiBn3qIwr8$MDe&z&ZpaqUD8-@!E4h+J$S*FZkEW>H"
    "Az2)eOUiYK{e$$14PW^XXEm4J<0@6=mM~wtz<lj)Tg;bz_~**DB?s-<pXU-0p8-H&s9N{pVzLnwO8M?e0g#JDs}*"
    "jxcbnTSD)a%Z&rq}2ExdVN2@Q%#{5@C5i39EuR?(8WHH~7CfkR8>OJ_cXPW(*NI>M<1T3myKF2hnDs~VjYobT~}w"
    "sWgzLzl3w{y+oSYl3&$wwBZD7kBGi!?n}AC_ZP-HS^B+&$HBUyu^rX!-N(^yTNjCyRob{Rzb;GVV~8a+S2}VCAit"
    "CC;ZI+IR>wd!#ns|Qb>40tJm8Wj=Wkv^<~?!UO)bAaIof*p6)B&SH1HX>MQPcLDf77$Ay?+jBs0(?@|r9R4xg!4k"
    "ugSDsxV`A<QrrYNmd$oZezWIHe|K)_U7cmy$Bd;Gk7h^2aIq1XoOxqH61pJRhI@s$x^58@7%O5kn%X0rsf)Mvd-E"
    "!gG3d{O%n^GE#|FoNQ4|@+SqUXwSUiI1VS{J6CgTd!~O`KZZT8AH!akYd8ks6m|h*bvVk|2aq5#6{6M<@c`JE6a!"
    "s?kP3KVNnoH#6v_?Pt?0yH`7E%Av-udV3KHLIcq_=0n{Wb{ZuYny4LX2*HD?4Rn9J9v^7|0}148aHKLjCw>SMGA1"
    "7dxb0$smr$O&OKR;JSpsYw~5Q4A~T{wL~?;Q#%<?g5~YS#3pM&Y5L+o%JJ(U`3MAQH#U$m_kw16V;28+i@jjgd>k"
    "QY6;hwZR5rh=Cj&qdp_LQP+L}biTVtRpYnW!o9pSV<sCuoR<V0}W2xnhzl(~IS4V%m{r$}wyN#n4vD+xWdpowdQb"
    "S>yBpIP_ZC02m918$wCcf~GqJ}7!qs6=19@tyg^8}b*=tia27z)PJcYGAWDlj7)Yl19M<SvQFk#qf_kL&q-+I{h&"
    "-Pvuzw3=;pUgo*rfBTfVpkC*zp#$I@zMzuM7iqj|ej5V8@X^gRX?PX=E*(p!e27PA#;mc=gf7Q!O`6}Su4Q)baIv"
    "Ijb2C#45zQki`S=cqUaR($ABE(&#RMZ-u++l%F0ZJfi5eZFnr$BYVxcdx82Aw!S`KRJRl{gxWJ`G*g<whg+G0Hh0"
    "o=W=*Ug|T>ywu8991Eb5Zmcp^}j)7?VN1;EN-GcE*vu}hZKvx<gf>y?Fp{aRg5S~kUu+r&+n|Xtt#tKlz@0MucfM"
    "FMct>7RJlhUpaS6j{UWgI-mE9lsIQ<6aD-qTJlk_fzh{Pa8caIM`+6fV+`)PsstT!l<r%AYtyZgAkwXI)XR_kBe$"
    "9@@58#lB)J1BO1v_-T8aahJ{O6_9s4$mQA?H&i905s$zuQ^Lmx42B7#=vZ=H68Jub8l5)-(NpehhY6s|$OLRg`C*"
    "T_O)9#cj(1zxW=Nzto#o@x5G1X<4sms&-vD<CV9x&!fCu*+DfP>!ix}&%19G`?bP8IZ)}5r+HiSP51So-udiUYi!"
    "wy`IgruZq?9#5~D>jG7uz1-(d#a)ewdPdxh|G;*+C+oMc;2R$l@Me+v%TMGHAW@*xe9$-l&HfGn;oU0==6znynE6"
    "8@Ki0f14$5CEIVuIZ6b=9N%F*a~iDLd?)*K|nj|BlA1%wF(qY?O1)OHKhDRg|C!d`EqBdA*TL4Ug%Oh_pr<Qx8Oi"
    "(!h#HSeU~NZQ!ORe#g7o<t<mcg-Qp&|UZR2vVK@tKVgi>d_LKNB(E1oYGz>Dlf|a<<-AZoLI`nb0hE-d$kJ_A#8k"
    "%TDHnQZBm7AxPN8AEf_!`W#&UV3PCr5uAOFp#r=UU3tij+Gn^Lqumm@te>tV3e`YOQ2WJi!yCsJeI@hj_MH8Of8$"
    "YgjmLxmNO!N1z6kJr`HF8pBn}YzZWnyj_vUT8eH~Wv$j=tLhKOwtCTOee%2hNc{P?JeP0bMxyIM<t)=V=i)3wt_5"
    "e}74d6@khr*6j6=#?fqH3L&sP%_E5x9=o$0geeqys#1fa?b`c26{tp8$@jsnb@t?EJ!fb$T0sK3UW_<ot&L5Z`0h"
    "kED)Xi7sX)K$`Ah>GvulKjf+86g>_uuf5dJZNN4Mjc9s1NB&R&N?_eJbFhNQN7<iV0`RXhAVJHz<h8CU;^4|^!3Q"
    "6JxgyX-mK)bbDbGu6yQpI=N=Z7&4%kej$wG-<4?>j$Y3HH=l$65P*WeZFY9)=CHArFWMBx#B!BjV<$5G{BO8%75Y"
    "x?<A@y~<82uZl7XvI~OPtRfXYM=+uR`^?uOp_UOvnvAqpa)VW=XDP<lJZYY`sMHWu_og@e68}I)b_Pm@}vPuCWGz"
    "QU+3jLntf*cQu&mD3l*${Y!l@Om&AhmUhixPGxde0iBU**EMZ3+5$n*nYvAV<>UuE#Z_Dc_Ps6w`#>o%Q<J3brNi"
    "K*hLl$xp>~>1vRG1CMKQu=JjwI*6`cc~`~kk8Kfq`B0X&}l-++U@+J>SJfNA|#t(0L~DhQZ_#@GD6%r(F!tY6VbK"
    "+g_<XoI}*Hq^zoI(YIW_<Uai6G>_u5hW3IH;9MnO&rM4J*HEE1zZ1(-UW&)LX)^cGb;t7d<F-WEAQGm<!FHc69Y6"
    "eix_sXnvX#_68(1l4ED?X3{I4Pf#ML?a4y)_S-;(&K{H9;XL}cTnB&jv6M3?Hjt)P`M(+nGmDlk}Ff!-WR}7o~Tn"
    "~U&!2>|4T5uQ5RDQgW2dmRuVBqv4Ug_N&bu9s2IxPzDIy<;u=8*3w1!S>{5<z8F5L8G)G4a|rs*7nCYjGjdMfM|="
    "DUB*|%~ZIdGAyOH6X^6hnexTQser_iVc>A$T1NjCh+{R7aTGvE5jY)(!<d|w(2Xesj5Q6h#FtKP+-@0Iw)y33*j3"
    "u22gBdvDUeo~La7c(Rr7hM1?<ZrE4e<ZwhByen2eK<bDuSQd)Sb9eKQwPmHzvzn^=0krT4-;HP@Wk`W7xI0-u${q"
    "#0YGRY$h(*Vj>_XcplcQKPh5UNuU))m69(a1^q)s7yiJ*Fao22}Z<aVj%ulUQm)}luEKWG!H_I?0&p#ks#g!dHMn"
    "xng58Y<ukKLes7AJya26)7e7dIgI5oQDfafM5ge-$I9YE`*Wjy^#-+L3-DRl+j7zEVFw(F!Tdt;eU2h3aC)tQ!JT"
    "LJ9*ZJ5*OJrpIrH<g@E#{UBI9$d)%O1o8C|2KJ`Ldc#@Q63iyHU?*J|Fkg0#s@!f&jOAkp|bEs}7LanYsA6qSd3w"
    "M$06YRpgTrn)NvHhAC&{hNVXmGvxL1<*SDNT0_3o>s*bdhLZt<b$HGB%~UaZx^eS%2JprDorh-0o^svSl+vogk6P"
    "WIC0lJKHP$=pYpPPV<G%nv-Zpt$y>6L5@_r$Eip}LuH*0oTcI<q+g#6b0J4|F#-_;x|){OWxazENgF~w+IG=4e0Y"
    "%8_b05d|92bv1j$C%_Bt_fw8x;7JucC}-IpmgJ|eo{GcG2ys|DAud!jJ5a<o@1=$Vm?JYc3-!OW)Hbmne4h6t<t#"
    "1{h1%yUFM4JyhD#?RelxA1doQ5Kp4%2R7Y2Wfv8r9?4imY)veN6*)c>b#Ss}Nr;_pF6r9}SUiEH)&d4zk6PGQ9Lt"
    "tf4mcZ~~z$iwyg(3u><l{b(st~iE_r;wB_gE%~C~!1hWY;~z;mu{Nxytz4^lf~5qOzuTjdI;mxlT%U|9~kL;GZAf"
    "-{N29_LeNtl)Nd`l&VxAj?Vz3s2^1>#Uz)_qN)HZ7`{QQajv~h=gph<z^<#K)Do2#ogR|Oc28xpJ<kDHg>mT=&32"
    "HNsw(_Nm9HhLR!hfe>s%kCYW-VqjH$kK$}sKyOHW7#LmB#2M7a3RkX-@~bTJ7(gvl6HI?ey4EOERU%M+Y=QWjJh5"
    "S7Kvfk~iX=@^iF-A`~ga=y^t9YJErr={jc^9D6l_Bf}_<yX(7R-VbN(lSx7AbZHUqoc{GdR{QwvKnH-djtc+B&b;"
    "LGWDGKeM7$XrK;!@RZZ#4PN!Qm+LhQO;LE&@ifv;M!zQ;d`7EEBR%wR}kz}5x8*w-r-${P^V!AlIf>@v4qr;-bqg"
    "zg&)eANLr+NDNAHRZ_Q7`+%w_ls}a%~oUWGC|2u!kz<{O&I4&Nc$Odgo*2$y7>u;z93T0?LH;Llm&1G|t2vOl&!V"
    "(kRU48-U}0qDEY{kTl@UrBG=~Ab;1Vsd?Z_U?M=+-7e^#jdDwrSa!vL7Mn-#iU7pR^em!ZiCwe|Ssvi>KuNE$icc"
    "GFMOjKbF&sz}?=^CAzUp#cYpcHvxrViUetoz%*WPOJ9x^%B!gd;gdq{fOPA55s85GlsiEl&6MPK>i;QvYmsCl{=U"
    "e^eB_S5&hpF_B%t0V*}#~It};f$8*wD^^^IR=X6$<)uQ*z|HWyxA*eOnhcnlCVXzh9zHJepS0)t~x4p#`WYA*C(z"
    "pmZ3Jd^o0ywR)F>Q;!|5<{P?Vhj<U>qCb)cle3elEU8f;0kb)vcuNTqk>sN1%+-(zetyk+bB=<K|Sg;`klW8$mp%"
    "Rgj$)g_@D#+x0h*iBW8Y~5JQ%=|ERbr`3oPcsjU*h6~6?9dCY+c@}R1?;xBFXlbxe?M^T25VJb?Lf6+utw;Wom>8"
    "AH40V^a=W@_fyPn%oVGo)>AiVmFwL~Q`q_FL@E2|^ZZ&J<1e)?K6b$)Q&P*TXD|68N9#)(=2iDTyT&x7(B!EadvD"
    "k`j0O#Et#7=WZRcUdi&#9XFw>gli*gffp*|?GD~{%f*b9YASck-_u}0u)NmoKQWX8iTI{EBZw$SpVmF1Sh4P+V^E"
    "Mi~sOQ+=U8;n_FU7+qqhplncf^^lstmY`{PS0*^L^28DaCi-uD;-ls7{ss~-oUAsJ$U8PO1-SgG<vEg-$?!uzyPY"
    "aG3xTL?jsG6EpF5x1%y#Kh=R(zDu|Ovu~41Wsml7;ru(+vbl>g<*C|pYR8i?7pIJlKcmD109cSlH32#uLPxudN4P"
    "k6{J9@C)KDV_$rg{Bss_-6}FutCxJ^lz>Odrek<rZ_;x<UG}p|_7;uVo*9XavKGRT?P=&lx;u1ZOa}LxAp*Z!=yD"
    "Ey3KN>D~M~os@h;RSYo)FV?A1Uma<cA`Xd%{LAs_+3Pn){a43_zyEgh_AIZRW}t+@VvHihq^m=*xLgYm-f?n6`9^"
    "}*R}<9fqE159Abu{dv!>3lfAQ>h*fJY&V8Xk>;ts3qaEO=A`!K%4g5ycX)zINzr9np6pIAnTLlARd8!#-7HnywA!"
    "~gp^oeeSHDD+BfIt-|8ANKq*xB>PQvsT2D5jIt|GUkG)08<cr3{7X5601jE?3p0WZ~riB10(IZ;d+*4B}=Mb>91U"
    "QX&33tiuLXkK-H26XeDqQ3njTDTI(68+kB_^gsk`J-c^d&Jp#iNj?*inLwVA_8BSO3%2N;lJ6CahUM}68zZB&3Wk"
    "t!SAhj>MMGpltEVGLc=w@TC`*p`~I7n>Gb3~sMDu#wfQulkB=sVA?di>9Mp(_w=3mlU1ah?NR*)ZeCE)GqoLbP{c"
    "Z2=;~<}=bTQrYOHHl6V$I*9?}W%Cot*KHW~`h66Q`h5ZMEQQfybBXx8$&b<8L4SNRcSICVW`E00$0JGbdHGcX_T}"
    "Jo=f>S&Jl)Tq+n~w2g$c^@UA(Wal?0=(0CTbD8^jA*b!fkqAS3*WIDdY{x~9yw!e~{+O>J|kQ{(hOmR0e{vTdqDY"
    "q}<`wT-JGEAum#;95hf&!K;tj@R6nJ0Es;+t8pPW-legfWgnj(VeeM4$pqWW`>}T8U783&ZqK1b^4;si$=nWO<V@"
    "#-j8sXSt1Hn2$vx!*dPq9u~$<Y1*pj87`c+(aM~9F$1-3ERd7+3J)oT#ATP#H4Bjwm-LGvO_>9^$S^SrmlGe!Qro"
    "v2e>9}Ch;>}{%Hu}jCxwT;{A@h~2F@@$lD;BR+-RyG(gY>Bjh9-+e2X8CwrNg$<VZKNnO9m(={r@!61-bdOaW`b7"
    "dz{ZF537O?4u3g5JbrU<c9cId^W)r?ExmIoy{6<!M+yq;AV$|4zN#cK0Hy3xHbhhs+!xCb{33kw)L}qKY}aF*>y9"
    "sd6;owL=hw4zadpj-EeO2IiB{_}WJBu3{d?RxGmc{0UudRPjMF7mLr&tl{>YExQ&Vj325*ngf|K9hz6`Jyut_2%2"
    "f~C@0wF1jrpW}8NhddiCsxdsnHPc3^TqE0f^%OOI3c&Z;OW8JS3e#9-~Q|0;J0<@0CA8MDT=g}dO1BjIXFA~#fE@"
    "*a>ZWXhEvW}OzJ16n^#!w?4*y^(x$sC3!_^v|5c;4HPjp%GR9Y}8rtq`u9QsBW($;Nt(!B3ih10S0)X22inKQ9Oe"
    "JPxOAfa;NO9o>uE0<VHPY<jVuA@ydK#(K$TR8ri)1og%wM2-gFIfI*X!q8`0n{7eB;_=fV(X?97^-<g#6pipUXBq"
    "H&7j=@G16%rQ=|<_lxJ3J$oPPjpvIbdfsKX;sv@D-veHF_E2WQmUU_((ljitK$0I8`2hjKp8Q+)mwG1|%<;w%s--"
    "Isd1?^DSLckTFFEA^KQO3_L-P)ge|z`l$cfu4W+N*0qnvuVYA^YT5;TDz+}T9HTd*N)XM1~d%R>te1sGWwq_8=uO"
    "wdD~RZrqSq_G^~Qt01Ux#*DOyjWT)KrhFEAotY;ApzYg9e(7KE4mY6=rMY5e9IVD^c2o;paUIZXMN<_dyGun&&55"
    "v)!g>;fhvy_ud8@sXRm)d>c4sY+v_v&9LZZ!U7y8NHyx^6Nao?H19&|_S8GaI$r3x#&ElX9Z~tGJsQQT2SFBdl?)"
    "Vk)oo*20mB8p;9Gl{GFkMDQb{?2;Fc>EkvYE~^afOS;b4&Jp1x-A#5vXGKYvzlgZ|TjLT0f?G{&+OPaH-Slbov`t"
    "4qipI&U-@+^W4qh!RgUyLvPwjy(Bl}uzh33;)Ne#r4d=Clvj?~O1F<Dww2ZFznq=D`;AeOSL2>*zkUY9IGO(m+yd"
    "qju?<LTy0;e<c1LL2nqQ;-Ey>WX9XErY7I(--;zL&x_a~MRVEj6~tGP#4f6%OGPUwt0jc2ubQ-A1wQn3#F*%Tp12"
    "fqLdKw5RGo=GyrVwNI4Xaw9IRcG=ylN=zW@8d~UT=4-_=KOZn>v$XcSC4KIfwKks^gr{dD?S@r<9T82lTBm{fK6w"
    "EBmyuMUZ%T(!nI<*lu$FdtCh&%MGfq#dTv`oI#Lril%x{WQ8XSb(S&1_b0wz*H(?Yvt$2_xt>9F(+N)HXW#6g-6?"
    "kHp=^wuS>o%TjF8xq3ZiahEBe;&oQ_?;opT)w00D+JxPQIQPjuI;?UumXfXYwM+hK;Wp1;~_cu)x)V10K&60jUYU"
    "i0%adC`4X>dw^qSXd?q0LL5!u(u!q8fMN$}Tpzk>;fqKsRrIpe!1coC`cqCv7?Nj<hsi!U`u~6jq9To}bgiDUE`-"
    "*ml|sarWIW0w?Q7`OBDZ4ic&{4))sxv6%I*>mqHoZ~jCWWi-p{10aXw!iLWo>UPZRE%fpC4hZ!L#Dw)Ph%;X`w{C"
    "91W(Y%TM6dtSQzf4n~Wvww2*e|~>`l1n<eI3}(I)kmn1q9w7^KTKx`>TJEComo1biV9O=v=d~5g{>y!Uc+ub$cw;"
    "d^aBOx1WyVNc;iF6iF}++J4n8WJ?377Poab~<a@>ppYjN%v8|{LeSzrS+S0xD@z<;l->Dv{r{sFglmliz9s%$mu9"
    "={3^|QLI)}n6+saZja9`4bQdE_=2z$FuH@Uj82=-);iCo+vgK<yok<1((TfIdI07k6$kE5h|fRZ!)+6%q4JffIbe"
    "=(xEnybv#P2PwBBr>6rA8seL^3`5v=MYl(z67E@_0uJQDJFZN*jAY^@+65C$=&o)^q|W-Bvo;30pl;PVd-aoa7pQ"
    "JFxSK$_?=Ib|HLY>E7_kADG#ynL<)%c<bYcKQP+)&TCVm(U;~4DJQ56MSk-nPQb=cY7p<<bQy9Rgj7>HcGc^!Y0?"
    "CPWo;lHc2DS01qLtOyjyhlFJDa!GuAxE>)Es~XkyntaNk*^4ax~IGq-Le$LQi;$|4oq`LQYCw1XCC@Vm%jZq1oKT"
    "xFn@<kAXX-e2r~v(3-}kQ3-B!pyF@wxJ1||6YlD+?kH>>>_`WEQf3M=VM{wqfJN>Le2riYJ>7#x&38&e0O7Sn@lC"
    "IYDa>I1pbM1u3G4FkPxV~GQE$N_1DmzqQQ7R$w$sYhm&DlmVVtlAlfe4Glo?W4K`btN^81{4lGh&uJ_-g@#d49K!"
    "v)2RU(DIM1o38c$F{%(0dxP$|C}uaA<x+hKhpEkw>pQwUu86<PV`Z)nx*)6>MLuoz$l!cFpE;|WNZev-)^#|^uWA"
    ")_Gab@%()I8Ne@5MzUG$nB<$$Yzm#%va3!YHo4BPRT#BjCeD4D=-B=|0Mv65zwE}nhDhW8tvq}zLo>2>HQ-a8_kD"
    "!RGYw?6}o5kJD(g5s+m%``PmnvJ{-e0edEsV?tE8kYBDZsGFo%+}?7qCiJUgO>JZoR<2i=u2YsT!;pB%o-x07*v6"
    "*T?W%oVN&%)1RD5%-AYwPQko`Br78KQqSA^spUMl^C~)rbBAb*6rmDG|eEx;HHB}#JuBFe6CVuU(p5>qG6A+q+N8"
    "HE529gm|ELp8y{<X!yR!(vh#}P6~ebY-zDB}ynWG@D@Bpz+FD=P;v#37GN-~SrNQ=v>0IRbQoII^4YeJn{p(hPOq"
    "S&W2bh`OoCFriu<m7`=sz}q~=v3Qkl5PU{}T{D$TIUK*tqvg2<BpF|I4es(`?w9*n3aJt{$;?BK==9<lIkXvf(Y)"
    "qfJ6p{SMawz5npsOY$HGW*X&9FgQZi3wg;3i4OK#V**MA&1M&f#LF`eqgC{(h9B{4c4gb@W;ue8Qa^%@I137uD|>"
    "I&^`1{hs8(S@sZsjfG7(Dv9`3*M7gGj!1akX8~(v2d6(yMhZQi7#=WaZSU6k1HnIs65Ec)ee$w?vfj7^nR75YaHk"
    "1n#YN~`_dA7Kv(-{g?tJc_mZ6Jc4RV4Tw1sHIM=SBh0dNMqbqF?4d(&U<2P@PUiE)EIQ-SOtfO#7uDBxM!i43}St"
    "V8I)B^xptKMX?7l^(S7tXPNAA$3qh%jn97@25KP`~0r4Xm#0I{b>O1sa~RQu9x9y1+~bpJ8}jN@UMOyq>tWd(Axz"
    "m-SFJX?yJDX!f|i5z#S@xsz$iU|m0TDQgaMLvSgnuUQ)7@1+=0fX&+J&!QKr(T*hr{}j<&ZhW;MYaFkBGYP=m9j?"
    "GG)P3<Lo}L}NQ5jrR6RijHI6a|5&ecM4S@2YK5NodI<S<ru#NwpRYZ-H+L8kCJ8@}ikdP%^gCr?JL6nVMaV9f_8W"
    "+P+GZ0X9l2zgKgdd8?#VIWyyu|mzQ5^=T1oAPnItXrB_ubAlY%+OsyL7V%33#Wa#v=|@sQfX)61aJjIlWk19U(Oh"
    "a)>Uy7=;>Hw4Ib!fr8F9jtCgP<C@6vrXCApETG2mFs2D9hY+jAi0ets^N?=;ATfH*Jy=vzEk~N8@kiBN#CzGi6yi"
    "DMGZn3OoIZCYRDm1-bu<hX&^m{RsD|sj&_02?^eRM}I)hfEN`CZ#k;Y65z4Q<Xtkb)ZN>!OC-SVlbT(87w@V)g-^"
    "X0i)D6NZ|#om=BEBk#8?yTSoySsQ9{L1}!#+3;ErKf17TZrLHiz<8Y76;w>Vkp!z~VknEX|IeqrcXj2D7MzbdP5{"
    "B_>XG^|dVFQM6AHF?Jwg4IszEF>J_LpZ$turUDdDLHrM>xUk?OzIv>Fr|zD^>1I`BpzA-?!|8tEq<oD-kY&D6{!w"
    "2DGvrcdC6KAd+HcVJ~_)vq_@^5NnO-)^aI#W?D|-@dG`mtCG)i)UV#%+)E>d`Dx_|8O#a+cNaC-|Ms9!gf<+tnS*"
    "wY}*Y=*=yW9&fS|WMx*2-Ah4z?i)U$`*-jszEIf;&LgWnxb41IF2^NbA(iBQc`x&b)^!xXKYSWf->TH5lmGC5?GU"
    ">=9N1mjT9L9i|{VOUKKWLYz!dB(#i-8!(&RYOgH_Hh1@;@zrHqWMz!KGf3t@?Azz~sp4YZ`P)0*l4sU7+q#0MHje"
    "`k?U9?ERu4@j4A%vWPggJoG6K7{vg_RiZ+1K3AwNCL`eh{>%16lqwt^q}>SM|7{o3a@N|d@>lS@)4==<#dlly4ZQ"
    "Y!*J(kYofdy-y)HVo3M3Q7Autx2Rl}ICLbN8Yw#WaJWZliBBis|>%kn3Al2R3*Q!{qX!{#4|FAvX9<zc&H*FIvw%"
    "*<wZB24%CoTVC%LZU*6RqMI|-h&v8LuBO`qT4E^VKaM>JbMZ$6w26zlJL}yg5$?rVw484W8>e=u=bi1cOxc^%oD{"
    "L-)>16U2S8t<<|70V}o|99N<>Fsy?LRM#N4wBX><1prNPKQ-1(&k-@xBpGWM3B%$41J;~!28BY{FWvObN*2T2h*3"
    "8zl^T{IoFIPICPMN){xE=m>{ykc57n1r9e_%kJuk?fRZd@sGbV)@7r7uK$oQ_7iXnFzsg)J2NQse82D&D4$|H2oV"
    "RrGvgRW31-su%O{Q!f5)@S*sWGVwQp53A(hS4qGhFAKkuNK!Nx%L{o|<m6u|FaJYw^NaNuk!Y!%vMNEpjg~4pKp?"
    "4Cyl0T`weTetl_dL(vi!<Ra`&&C<i9G>|4O*2lvCec%BYvg3d<SzVkK~u_J1i8?_dGdlbNivUazzrc*>>0Ca{q}v"
    ">r^eRf%vCeaqDQ)iS|ylf^n&mThLVG_m>WWj>cG4h!avli%OIeT}GPDFrZ%3rY_{q}f%uuz&E9TqWPkW(rOI?2Rm"
    "2VEHZ<FO5F|JoCIc!RiWc7(r{f!Wz&O+Q*^@nMV_8W)(Kr*^*nzO$`34UZ!O*wF#<@kyq^Y-R~9B&#TXz1oS>roQ"
    "N)lHAKYf^1>ji@5qvjJO{s@{c?Qr`s|<m)3f7uWhiF3&2wG2|6+(_<vXD7!QsK%!y`2JuVFv^3Y)S#CA^y|s?u4D"
    "1Zs2p8jrJot#4`19t(-C4@70iv|=yvd`pHwLuD_>v?f+rKllcBD^O&K?DBxTTsD4^=&_=)c*$52wL%IH$>_z36f*"
    "v)V(!I8mTm>xqH<`pvGCBZD3MctA<5e~c}fKVcJkeKDm@+zX*A8uWc*uY9*nC^T!oM=2}3LE#?;^XYyjnY+@;&2K"
    "&4w!_F>6FHIx%WOUKOGF3K`U@W9$X(l+6CzLX%uoJZhVISoAlSDorDLr}`-S1|div9Bb-I=n!&GL6eRMQ)x+(wtd"
    "~^DDE8$&!?+X%&S`yKZQrY*k#V+4g5jG6jtGw#SR^bHUF8WcSPba@W_LKLVFgNfgSt36DPbh=CwjOh~ws$^#M}Zg"
    "jFTR1Fr<RXl$*pz>*lorf!en_m&!bJf63I|Bvw+;S*hm0(G-r<6)Ox;3~JY7uu$_JqtId1007b;AuPUH}}VP_$c^"
    "d&fr29&_W!*7uiRF|+8Zy$+}7*Q(3#Twh}dV-<=(Yp06501kpWtigQpqgiUuSG&=>5k~j+hOAV*H+P}R7cfLKGt-"
    "WFkh22;WzE#?Lk<VEdZAxmk35*qQ%IQwzf-&5*GN1@Y}&fcY6fy>_&73mDp8n>?^F&*&fVC1j!3f9d99fEk4}tc%"
    "jQ0`cXoCt#4>;L=tQe*bIlbQyYcrH9CP5?lE1gAstx*RS-UEE-si6?9LE{3447BKSU|nes{d%c^eqNk1wKaf;@R?"
    "({~yoMud*MlN_u__2s675k)#iRd!$0xLpnW9sYv`S*MopdN=)xg!xSh2ktOOCnQjedIKJg7U%rz7R~wz-yJQZhf`"
    "QagJWMD?Auy5<je!3k{EfJW(hrT2kCdrnJY0;W+F6M+<!Ua0;#;L^GAO4fbeU=MdXyVfTP0OwQwv+HSNAB~_NNfs"
    "?yBNNL5L292pNdJ$0@8aP=1<0cokv@hU|@*Zyh!T@#mUp3#dqW?o-Hx8^5$)Ap=}r6>D<5_>>nYTqUPitJJ3GO9#"
    "qhkGnA(_8!NrvBB#2JO$~a6d`iF{&bcDhaRD$kWi)-zat3&z9K1fnd2f}%4Dcr4bgRZF~#g(;TZF#z^%o_G=S|-="
    "A_#FQuT}M6pH9<<<vzp>)5kctMjmNK8Bv`Q*)KNy=GLt+b>&2aSLm@1bJYWF6}<tBTI@rqBLXk-bE&~#CeN-DHGw"
    "ai<g8rRW);6MZNBeT$-{!jO2)F5MLIk8aCd*B~uzh2y2?co$AKta)YdMJV~-^ad`HqE3Sb@&pXa#2i5H|`9N>6E)"
    "J_<LcIT}J08YaEbv8u)Z=-Ncecp`%<nwi>tsR?s`n~idznvHu-6OmDSnqKd}Zm93bEXkCf_fWD2Wmfrn6ptj#3hv"
    "|7iqL>Dv*C+nv@*<~i~EROgTv;dLNXg&H(;g7Th*SX4UBCOWjhk>+>YWCV(A_5{VTG^Z}BbmhCQ=GT3spwNXAQKV"
    "j%CxKeUt-zR<>d@~Y^fS=mBXSt{Qf@*#l>l+}?F_yDsCI3T*ZTB(nCX2$%~h=q|B(0`{69e}ZSC%Q)WYTF6@guKr"
    "_8WD4Gj&!f(~@neKEg>NAEllhprD34=P^GG^ifx;u%n^1i6%r1If@?enH&)7KqL;w{~{ztVEeISU*zYOpR&%5nat"
    "^;q4%vk+Wfb4Z;z;oun$ezgxni5p2~zW77*`Kl-M-n<FEdI}_fri+7-opy+*;6ID+Pu<fr&rtLu98n6m)3OXQUey"
    "Xlyu5l=KMoy48nm;O$I4p|6M3tzNQAK@LG1fpnaj2rBQ7iFp@FN@Qio5Mg1XE4zp+VE+H2ip|TG#a$cnE-eLk__x"
    "qmhd|Iw40HMtXcrQ2Qa{%;FE}d!^ud$S@-BFh}DEKLiWvPOgKMR9OKKa`XPr1rJT<nQ|2GI7-ZMXv~5?!DoGx5yx"
    "C+*gFt5qQn8B;A7LFMYySq1giz*G86$?y3w`LL$0}Gx@p@V{4LPF?9=PJEI~2asuYFXDHiQTu>qOtbVRBKfxIYJN"
    "jAMRF&E_bXmwUeRn7D=yTP9Fq?>)<qUWvqMp-9D!6vtxc4v)#OcGJ(XlXz9-i;9KoWxn_P6#=r5p#OiC7j2jib&0"
    "-HIwAtdmTO%St|6XOHw&q7CZ7Uh9y+W{-c*8*NVo{_V;Z|D`r^OTdn(hUnIK`afD-)<zv!P#*+B;RnWa?Ml4hT{o"
    "u@77tewpf}O4PaL3nlR@d4g;;e()m{N6?IIcf{y5>=3WxKSJP~@M8>bwLmn092!i*e+2ih`T40MUL(*j2%{ubCn#"
    "ezy=9Z;Gxa8b&)itycAIC}$QwbGOc|HI*Dq2~|&qNcAd7ZW1;8_H#{i%REUmiUJPw=*?@aBlgOBC?@j3vPo}$etq"
    "(rr>(Q2tPbzFIz@!lCXf<f6g-=47d(){N;)YHrd#OihgQ9VRrd2-QbgyJ7e!-vA{CMKqe&b`beZaAif9_#C<o=s9"
    "KfM<K%`oz{Pz`x1j4gb_HNJr-Q_CiPgFXz6abMCp}fsbBPip0IPa;-*-*@aDCqC_^h@DBG|+2>emqUl!#-WW!@Qc"
    "cPmHo1El4ulQ0UY3v`~7vusRT~!ewTCfAoq_w1=qD#M05%l_?%%MqOE-R@7gtlyGLbdI)>AbWEP~m|~GpyHvCF(W"
    "tDR#W&=vHYxSp!}rUipbDX+<Bi_-(>1iPvGA+7J1@B!qm@)0dmmUerqmUmD6YIu_OO0V@Y*HKDT&w^KKOjv$nAtc"
    "^eqnFPuvxO=;w&E8*F(Sk6>ZfefAve=GqTmQy1*3Sprt(^%oQ2r%HC$pi+MS#AK9fS*pX2az%o#oaoZH`rJ$k<Z)"
    "K4nW2N<Btf&71Ua=s&H4HT*=JjO&1qSnm4CR43gfNDk*?v0GZRejnpAj@QfAC&)iWZ*>2#w7=ruD8;4aQN=a5P<p"
    "lkDVJ>@J70~@VbH?DhZZTvl&0pUw+4Ky&cY}<=$_JI?>B0Y#HsdwR(1d(Ph0DxXJL45x3VvtN;Xe;3cS<m!7+Z8d"
    ";e+v4Z&3ox&Ln`BN+H#s5my(gp6{qubdKwRV`>ni%UA*E{Sq79=>1CcOJU42R(op%jM^eZ``KBAV&Ml2`3?v&vLQ"
    "VA*`4HH&T@at$Zy9oQ#+c++{SCPYD7!IIf2G6#sLL^-oj=TQllNlQOMlw}T2<|w9XMh31M`J_B)cs7b~qboBHl~w"
    "SDn|bDlGI5F$ckJA_|7p8Om|7{+6t=fW5uz^P+D53XN&~j5u8T#d^9mk-RzX#j}^f%#e19v&FEdnL_d<Jr-#}$vJ"
    "Q}jVQo6q`Ac{)Agf4x@LbGw8mpJvVj<N3AD#dsI}vFf7$6`$!e7E$2doHYymbCuHqe|LsL<wZxO-(?kfB#_$tmmw"
    "~VHdbj$IL0R#m?L7A(}e`AI&b=x^1mg~u~Zj!Fod4>u0=3c2Ef!WDbUsX$!b8?=q)ES99h+P36kq%g$)G(Yhf?E{"
    "HSL;VXpeiORzYj^`T-9So)m7m#;^kg8U)M(n{|mGLE}wk<2Fw0tkK+I|$D^NxH+|$vCs>n@KNF2FfLBZ!Bk~7&cl"
    "_q{;XhY%@M(88(Z8n=7-3nxO-#pgF**F@^_y4yqql$L%IWv<T{mE@#YCr>i0>NwtSZ?ACYXrtJ~PDx3F7}e`{np8"
    "_W)e@ea;r6*%KJ|c`{}uvY~55@8va2?L0MhMgnOr+$04udt&)jA9nFh8nNcD$XOBy&{9>{%KQo>^C2R0!vaH{P^D"
    "z2Z0*k>au|fe9#%M)rXgCI8d_@p1<Vu-#RL`xq>wvn%(v;=`1VAVxBHA?3#%vDgZymCAqSI&-Yl}Y_VyHXGXx;d+"
    ">PLZ3O}W)I+xh~D1#F0=7v;Uu&WF8`&iDq-=`Uy6QuNZiz#MsrsA2G&Z~@F%ka6eepElIIz{tqOxufh-YNOYub4T"
    "wis!%cAeudJbO+`{JacGr$&VV1Qz-TW*G}pb^|`P-x$CNL>&88jW;H7|2C%HsQDgo1u2skElgXR$1Z5C!W)wXWHV"
    "#c((LTKqs}c7>qvF+1vi=~QYx(`YkkcQq<J|u#mTF~90dRO9NYW~PPNW1H(PHzLs^PtxQIh>EbEijh!!*yRQO_EV"
    "k7b^H486>{Q32ZdxYwz6^ixVU?y(TX1f1~{=yRM?i=r~obOJPd-)!P-_<pL8NsL7lD+ZG!pLnV!P}GS2{`S|m$A7"
    "+6x<~S%yIaAHP;2VM>+WG8fnN0{X5UAYWYl{iNZ6p%G|l<VR2LlOmL;hZKOuU<<sh{2Uk$F3C7ylo*w|^?@TK=fy"
    "XC6ERKYOs<gBbx1|90Os;Q8KC4yLi3U#Vdgyw#cA6RV02UARyoXsib@%<#dogl#gDiB*0p@-u{uFVhH@Zum7BOei"
    "P&c?x>JNchrfg3l>6gd2n_(7>Z^P%XQ4V(aHh?lfZrf^Aw+|7101aS)pMxQfxxNm*=k@O`n0~axAljf>&!BcGxTy"
    "EJMTM4E%NNbrC2fT&?Z9i9_88V@Eg0_`t?m&i%w+=0MJQr^r2;Ngr^?APDJZHEKH}TCtOs=LWN7ZuXUq@U_Pc?bL"
    "@uN~+>GQhQ1^cLDDTkbRlDi2mRNYUt6qQwsP-nB7vLQ0kq#+#*^1@BaxZyfX5t+#VaH7RH_L`f#y7Jtm*!NcE?0Z"
    "#aO!G7zC9@0wc@g&_uZaV7xWE{X`<mC^*(z8fTnA-YX{0FZJOSRl07!<%m;Qo`Pi?J1(O;4Q*D->Ph#z<J?;2b>#"
    "?6mOO6;+)So4NHcS<sta{oob`O}-@!(WSzq&e!PI`wSg)P0DSt?q_t(+Rt4C|Wc>YaueqYDUokxuxeUzH2an_a?J"
    "mgc!x%wkyrLjW6&ad7P0n&b7Pd*W!@ReD(hR{t|n=0g;sO0?%TACu+#_z?}nQQ1`e+`YI(n1Yes@iq*65-HHkqna"
    "2UK>e@P`a8=?wlPg%3tP|PJw`Wqy22Th9kwh!cQBXOF_X|$J>_%f0T@HPrMWl5T@<4xc7GH|e$q5Ghtio#H1d$i}"
    "t+J&>9(nN@OuA1M&Z!bqr`}yReV#tyssvFL33@z0QQlbbCp{+`(wiB^6jLhNtptH3->*>gsS162VAQMz<MAsn>+g"
    "^=lIfv?lfgs*mtA%cgBEpv8d>pKTH-<WL#gN3Dh_j>U@l#8nc{+mNCV`SG}ILIdX;MNzSL9D@gQz*mv|=>oqOBu6"
    "`lN0!NW6lsn*HC&xi<&&C6#_>{?dH`1h?itrR1UR6dMeRhDV*t<A}L(S)~7l9{cx?@E<qn%VK4v;U%c8giB$)nEx"
    "5X~->KIH$1)x@9km(r;;5-zD$Wk~SnKS7}-@fr|3^Dj|FQgvyuy(VWI*VtNS-tj=w=060<d{@B36-7h4}H28!l<a"
    "rW3zr2^f+06}pdxL%vsYo}1TjI&$hHSsJrC8?k*vZZpV+U|x+mcXob%za-j%Vo@z8K$ez0Va1>WZ0g&7fJ?$3nnO"
    "QEcWqLEmCZ^Nn0l{IIO%*hQ`%D(gfV=)n0U^C|5}wqK|PnGY^2`VuFTrJa@a^Ic&X(%_b9omsK#KxS?V9fvoADC}"
    "|{+M^G600Cc5j`XtF46}oV`rMZ+vEz?7jqEhY++leZ<Zp#1YWr?Iigr<-om*=BPxJKkKYj&7QTMj@?bBwxG;$Tbu"
    "yadq*n=!RZ<8(hyFP*Q-12ZqIU!ryWv6XAv2akYR{b(cUeSx46?3i%sfg~2@|sNnN}}kg_m!1ke+$kqEfQ;w0@Q|"
    "NoG1y^jJY)oX<HluYd48+b4yIKV3nQS^}}^iTWH`5KZMB`QGTB-C@a{g^hy;sy-xDVWdPFCtNG&KKuESBIFu6)6V"
    "K_rA?;RapcsGTBw$zlE-OgOvsiJ;T+^xN|Gp$$vJ6R|F3FPYYqLU<<nr_jn(T?eSjUCRdov*eIRI7Pw68Xhy3!Ro"
    "DE7)(Q7c#NcV7%T`dos;FZx(?nBdx`JJrECxw%(ypC(<(vpX6#;?kI$u$bOh=~?nzKZxQC8#8nA`2xyRE3EOLQ?F"
    "KVJTOiYa{~Ies#s21B_qPQ{NQ;{e)nb~?-D72BpC|FbT(n7^gMVucUr9_44h<Hcik^btxh_1xONzqT*^k|q{N;Za"
    "hLGqzPh_ioB_*Ir>ipEW^{IGbdU1!&zrW&BW?SH*0TN$IgBn1tnp1>X0M#W8AaH+<~iCBy-sz5k~q%HiQ>%M7|yI"
    "1!I?3LsNLi!(*IZhr@K9hEcS_(WZKU?lC5aFU^$5>*r4ZF2brW{Y8E7O-Z9D641m#WNwA3Sj6+KBZL9FIq^m6zhG"
    "6GCtNK=@S1QXPkquLJ`6|V{2Zq;t1e-Lw!L&N_WEcz<Su(*0B_L`qk%D3M>Pq+dMo^YG|KgeAHqXR~H=r6HxW!GN"
    "O#za!V0uk1ydVsXb<iq$DF=%wvO=60y6MIF{`k0XF`kpd(0SRkY_HBzQCo+d2ij?`wC!RdIcENiUZYE!1M4-WI3e"
    "+N2*gDqj;cOV$Do;Y;Nr8259Fwn-1KZkWq{vL#t4f<wV6RH>Z|v$9Ic|86(CifdLLwN@=Gkpg(WDNZ*N!7g5Px`o"
    "GiG^OyBSq;t*W?)CtP<?`=URl?UwlcoQRpw;Ji^HfUZ!bN+Ge)QDC%p<ec-LJ!LCt;7>gHEWPkb%Lr3s%dp`QS{Q"
    "`*dR4BIezvqX2#phx9P7v!8iZ}!s9gv90Dnl!4RPEjCl4%FH6!Q=a*Em;DN;Fvzi0_#c?w#jNbk*RwQ{UToaAeJf"
    "DV^zv`7`IaVmVw{8s&v3pk5@i5!0QrBx~j4j1Mp{%N6qM8TdQTUGD)S{R#6Nb$9`%yZC`(S?B45O&8ybx=aZZ<&I"
    "<lehH^;+2%xhi&ru9r3vCTCeI@^|#j6216QRn8yMKlrH`?}0y?yiO~C7+t50cMWcss}uA)`IDwvaA^N>(a-x|B>G"
    "ux2ydy;r}4CT^B%gTgz3Fjx{FnFc-k2&kpr4iKYiaL2Y54acX(GbJJRbe_>zh@wVhvM-Qw&Z>sM4|R}*r|vU{fT*"
    "-?^lw1BIf&R)z=xpfn7<Wbt$#)mdxe+-)>77>}k>-Z-816`Hb%bL?5*bdfWzgKT4o9-c?5hlVH&-OdfU^Cj<+=+%"
    "e`-APB{jE424mQImj0e$PXLq+X+TQPMw{#cAoD7akbFCD&fZ?2WvITU#o?r8j&Z@_NdnfS>;H=dlU^PC<Y52vn?N"
    "MiU5bx~An|s?^gJIkm?YDMDoxNyhCm!vE;nvn(d$8AzTH*HgaC>*OJJ{W6?+&A3)Y{pNqsZ!*t6gx%2KFYXQ<8Y_"
    "KfQnjrmpoZDLD(D5)j)BxkwhA%Z{}XvveRM8?mPi_I_??z~#_`hK@0<h!b5mEN}g=(maTCX;yL4_R43Hlcpg>VV8"
    "a@`XLoiX@&YVL@fioiMbj2%Rqb?q#w~Gc!m3ZAvc~*V1sfLY~aH>_B7|R*L2OL+a_LQd}%usa#O&s7mi<{>dJEGW"
    "(rKn<k&If!nVU+AVE?f*W1y#sPTmg?Yc0Ojbzj6UNAgejne@LSwti?X2$0H1OOCC1MoWBknq3h!EdAtx)8|hDo1D"
    "<RP9;*>qN=4YPqIq$S(V%x>Wpu@qv{~+)U8Tq|%?BoBvT=EK9|Gv3A<+i$eH}YlaYZL9%M&e9bT^C;OSTbyfy6l!"
    "Yq-S&a|fXjasm*S$Hof81%Qosrm+d}=5FTug3?Ar?5q5_BwwrZb1!oYO}OV0`-XG#zL7^RmW|Pk%XnN56GGGk&f!"
    "{8L*@WQH(0OD9(wTJL$0XElRAqZy!C(Oz9Rsm<^K`uklVQT1IX{IA(>cNfEpE+#C^Sg}ibD4kaDf~8GPvH(9)x=5"
    "GYE3UZDFU^MBJz)yXeQWFlPhyZzr}WGs5J*c=L(tDlDt7JoLuYRAdW3XFHM#e8HiM0ytkBimNV;eC#5xEhP;USX1"
    "F@B4=pG(_h$kEK#UP;Gg4^qOqKmws^Bc6vl8?>c^g71!R+LAa*>l8989aqSfe{Vn*WsKyX}Vi74ktQr3=WsL9E{0"
    "MB3AZibBx>Kg<zQ(3Y)ls5omTzGK$(NFip{kXG5V3&7>4NP4l=3-;3!~E6Zk!aUA5%EH6ou{sEPG$y_cNZb*A~yS"
    "2e}oM<r(Lb#z;d)bR4UD-%64~LYLDWBXt1-bPD*D{;q#v+^C4Bml!o(yrXli_tR4(~{W#)L2#n{|^3GReU~05^Gz"
    "^Tg^fn7J0W44v~Q!V;V7<DH;I#gRQr&M$5p0oDsr@!Rk2=GUni*M_ljaHvT*ewp*n!Rh~b0~C?!7{cC7Qs7$>9eX"
    "_sROCN;Fp}O-R0D7_tSivMy@E?WgSojTgSlD7U~cY>cH^DFaM*6|w|3j%XnS*S*xBFR-3v!stuT&S9ppVbaVv_p!"
    "qKSJYDb%+&gSNB+}hpQAC)qg0MluPO4A>E;&k2gIdPUTndav$KZDuXdSWo27|bUI^NGRyk209Owb;u|gS|A9ekce"
    "kX5Qe$8%Ev@H}M8@n-oq%A>Yhz8j#NR6~)u`xINAnlihG@o<yzQ;FpxEH)nLKxL;q>oFkV0#FE5K8WMxUuO!J1_2"
    "{n~TfxNwQk?>4iauz>na-N525QitMv-oQX_lqbjIG%qe?afuEa%+FSMczQ@xq=&>)UoB4!b&f+j?p457EZoj$a+U"
    ">HmE2+A4s&4oB^oQ0t3M$YIQLkH5UWt7L~kMitE+61E%8k$hpwfGm}g<?vJzC}z-6`aT%V;&=%!j-0i0C8n5}<~O"
    "klucR4*R%&a2D^8~wvbO(@XDRaL2^muI(q(~SZ-jM5cK$<(b?MkzLlqf-N2jz5fE5#zB?fFzB4<ZlA#suw%=XD*6"
    "5OSWS%AqLs0i;Jp$TD)Z&Thw=?ON9IPj2tDL3$0kfW6*^q|X9ibWmoi!u{aR<7F^rId^}D*J9(>@6>goy~?X95(A"
    "kA*opvv%R;q7jK8daJ0X<vopm1H`>|Xk9MNY?tUw5Z|(qx-D<ZtH+Ne5d)uSk&dz9SZxrryI@|5N;nsdBvyGU^PW"
    "$}7gM+uP@R&fj>a~elUO1LkY1*ha%9wCZx9jwz5ZZq0iBW%I)SnpjCr150$*3>6d@3W4P65gZVj6~bQ${M`JaLS*"
    "L{h4%a&78?2}}kb{Gy#}nAhnpFMa2B*wG!Pw^`3gKVx=W&P!wZ<^01w@1m%N!^vH3M(jE#t3htP*K=0L-o)hZ$KF"
    "&IoTem+KS(#{pWb(8=kM9?_&w)Nfai#3^osNV^own`H1T`8|I07Na+hty=jfp;`dm>VEuM8*?jOVia<E`Fae}}rX"
    "^*&AHpN>Kn~LwV1?Klc!>$3*OIY7So$yGqg^T8y*$Oj*Gn@$Vhj`eS&>8bQ0zE=rIhntNYd0hAoF{rqKIa^;6Qwb"
    "G7_nBCV?;yL{Q~I<uq?>cB8kGnTpg`4Pm~u5&}6zKhM4Ag7SVQ*nt72?(iaYD64s>|yk>N9Cn{&yM;ITlIkrx+bW"
    "8!lq<SWnHKc;$-zRsw{he{QXheyTeSk$amC2>vOfuL{d?7+iz0_j?IzY2RiKD{)&J%n3#GXE}r%&wZ_rsoI!qB)+"
    "7_q@pK4$Ed-zuj%aC$wu4lmew0MX|>y&;DLd}(@AKi5tOnEpT@4F3Pc<OBQK(Yv;O3cLU?E_A3Fy*eb@s^sP!194"
    "O>6~gYFGsy8&#m5~PNow_6uDMzj9^Vw7*^5)`tTD-ko>&8Uj|H^tafEC@pL9Ptm$i$u;JzXALR~X30X^r4jrPoFD"
    "lJz}Wz_U>>_1@+xj?vCAxm!0M)5k`xt}8k0yR#q5{xlcOi-U{vP|aM4TP4cUlURRgrX)(2`1qg&6&TtG<D+&P@ps"
    "Q$rod*t5)+lto4$9S7fgNb)jnmv1bw5Oi2F<_iq6k6D%e=+#55=hJyr1N`fj+U?Fe9JFQ+G-)SBkZz^10{DcxsuA"
    "pURP)Bx~Jr%C8^e1q4*g6>|bLbswg{bPj0;A2~h&BM{beA*KMAY(<(Oq_mAb$wjNQEZyFSuY9HOcEVvWggiwu%8i"
    "iW26&hv_sS5d$a-YQX7AlfF3xK}D@_a;0?5a=Qb$tgM+vUHhGKt|9-Y+#^KII%9SlP>o6?f0bYr8xHgTPC4_Pl{s"
    "^_o<tR6-fr*g#=FD4t^LhtchuP$Z0>FDM6GtX+1cA}@9YmdVJB{H4mW{Q2PP_RZS6*TyTBLk?REB}_OO&ON9f0l?"
    "M=8nMA9iqJ2DdF2cDyQA_gVQId(#oQ2kCGn@`O76LbE=oIf$=-yCyZR?>&6`1mTBSfxy8k<@0ErZ>Wp7i*75=@F?"
    "sQm6@XPD{=Ub|5F$ZnaI_Fg;_QcE$toFVz|`?1e7Pfsa&ejti;BQTB<#_QZ%@&C&%qlkkU{uXNes`+J0iB+7a!W1"
    "X1^x>3jhQpz3EfPHv_eylVU#`8kQta%0|j<WNp>)c%m>vlRR8!giXv?2P7G0OJB3jP(=!tm`wnC8M5?aDFQ%Q@(a"
    "i$$l^-UpVLs9zYNTMw{x0)@<^g*m4rY}_@);1iRufxsrW9V<?c7g3z8z&6ubFd17s2C<Oz<AYdOL#%p|1sO&B28v"
    "w?UcUmK`Y(21P|98Lwcwc`WHS$rT5V{jBma3Y>|l{CFx(bU*9e$_m#lkcrLy+8HjDQG;+r$@DSv79gTXlfuzZM(G"
    "*;+kf|WQ{@TA6MiUD6<;i>5fIcY5L_nbm!BSx*ToW+FI*kmKfm}^H48D(K)-|t>xHlAzN;j`QMAXXJSzgy0F_W?R"
    "@65A^H>cQsre!RIE?{CN9*6#LTYrnI<xjow5+8jo^(N4U*-`VU$ox$FAYj-%@8npKJT07yOy}jGn-R{KY3U9RK^t"
    "tK-W$U@fACU+j{1~7%d^&|~{xN9RgCBG|x0(WLSV~y$6~<Y;Uxmv$JMAZy{fT9NV%eWq_HS69ZeCnf8wQaOYGo(7"
    "kdEkhT{n($oo`<329wYiO53z)*6bYFJ4b$1%Fi?=>20sQxnHllS(&%$m!&K)<=LH5W;=H9?sC@+{gQrv5%#y?Qj6"
    "syXmaC>@UL``eN6`2-ZnSGQrk*x)2jNF|FDZ&8(Uw-JTGI=*O_DGuhr(bRn6cZ1jHiWg0v6}XEFIgXpd@60!8I>k"
    "mCiuHH?CEM9$G%>}t+$$ugBKZqO6N5*f7Hit^}Q!u9`z{HfTbGSX|$nHQf)%GZx_2e(?y;8?N48IFP;Auu-)a2Sp"
    "ArD30J6%rW^-;dL)m(0p5*A>dJL*=;GnPiMhyh$*9Sddie$KR133G;Y_WvDJHhzhU@bUFdPH;g{u(ox;r3=Y#9t2"
    "mLa+#JMH5LhBssiQnK#@7nbkQ8!99xg1F;NHWg%xKRsyz~3@$=-Va2QP_FD|q;5(B6-BHuu8a?O|syinha@L8r6X"
    ">THc#yL)?s{Z0r>e%#(2wW6J9u(Q7xZ@1&!sJ+?V+1ZUdRZc5hi-MzMrkFoWN0A_BZM=1IFiL|kk|X~+z}Tc#;oM"
    "TyGSA1c|HPI*vE@%}`4e0IpJdBr3M&s>7#I3rIJOppkEzC}fF!k0P;Qim!fn`U6h6(f+*6t^c)~eogLjxvfjmSh2"
    "C8efB}F+qUH6s(fQ{rE21RgzLTC7Oc;fOfNSaPxK!TO@{H)<8FI`mY2oLX&CVJKWa?H0oSLOO)F{j0(#7_M$d)g1"
    "xf_vsNw-XxsrsCxMTx}|4=|!^SW-*3SkJCjacN)vV-Co0%BTfS7L%(ByMqtQLSxy&XWls4t`KZg{VA^^Gg|we4Q{"
    "@Ol1krcmb`a0du^bx$PeGN`Bz!T?fR_7<2#^Ocu%a+C!e!0ih@K)havdUDoKf^4b33?hWT+`5GfLU(1aUR`XlKFA"
    "V$SX_%vsYt$Y{SSqZ~;P$$h`$kAVC1UJ{oLQVBu=&4zb?{X{Tr%0&6S=$s_<g>na1F6)B7fmfzefKQ+&Oe}ImQVm"
    "kz@0GLO|GqeDl^3;_moB2&m_)NsI`P6No=B1D^)i0CwEM*(iJJJIts14mU3(CP4>z9zBA;0CCszE475}C+<o4y0Z"
    "A5TZNzf@j{|ebpj9j`eRB~QCda)}O)2oYD_=KyuSi|vUqrA1cu1iC5xKnu-1<#KmXV`$*<2x&`r)dK>0I2i}6_kz"
    "yo!=E40+0|)8-Su0Vt2ucBTj33p{li5^%@lbdduFJyJ8l-F>)c3ACg<;=Ayd3T2W80mWm00lZbW7gqCs?q_*LFqk"
    "XAdLk|uQkKUafy%H~>iCYu7XHeIrSK2PQv+Pn=-DwkrmGc*BJPYAH>=cT7_gE+57Z%6q5G_)2A}lM)50(e5LJ5Wi"
    "iT>gyGF^=B1x{QfWTUCIo-Zd#`es`2WpdW*no=&F{r>jXx5t0Jb?QnO0Q#)VhEll?54HT1t*Y}ltJ2ROx~R!wJYF"
    "SUIYgoFE*HzJx-h}~7PH-O?i_MAq6O)kJ(6K3SO7krVdU`&eqa*TfX-f+P6xvVf{<jl*RM$6#Ed_SX+X(!Fw;(QM"
    "fRM$q87{<`J)jKB_-7AoR-0FoC#Ap;i7*bNt0AfW-*SKxtgQjX27+9RaFP<d_g{FB<JRYP7GkUK^w1MA+-T=I|nL"
    "sCy~&@xsi7#)ES6C#>E_Afu!Rx_M=KtJ{WQGB6Rkm7>tN`;<1Wfq3G_2UB--ZIm$f8(yl(xeBV%DRv7VRE^HglZy"
    "2#J(l*T%=6!n&lJ+1YjY0y%onqQmpoqB<?1QFLt^RWS=G6+KHb<Zs681O*V7iVuX_JZ`5wQE^?Cf2>UiAg7EQqJq"
    "F_vc@<IzviFc@&<pEHiCS9`?q@glN|5Xk{ToDRw^Pzk$1R!m)gh%=yS(VvA1GyxKVjH6&NB^3Y{8xp7_#*xe7tSI"
    "ZZTi=r-oYc5&#?y3ojj8Fyp4_JgWfDAm#hO{K@V)h92YV8}pM>ux;rn}WPm{{eXq3ufgwj(Y666cC+%*m7gT3}NO"
    "ejv?fe7lg$95yCS%v)C1|wXKQXxSH4m!EHiK7JTGSxZfpE`F1*Cmkf`@2^MXGeh@+&)Xk!RgUiz{882Mn4*LzV=N"
    "-w@n<ppDjjk9jUXXj&Nl`$cSmDuN}*vY^D~&>40JEJdj0COK+nQJ>8W|Nr5%$eLauup+xhmSrK(>Wk)PaavF|frg"
    "(i?9j9cHk2%@~**q==M^#Th%i%BY>}xvZ6<6uC47w|Qu<6e?T*3I~8Lhp{Q%;O99Pfg$7Bj9nsQ`u{oa7_GT_`;0"
    "LYVW^_KQ>Ab1TJ<bAnO4M`L!%o1=K}FUjA;Hm;0iEuH~fZw`}ZRzrj_jF>?-KfRqG8U?&$a`|w+8C748qh@e0K@|"
    "kZP*ki=;|e_%mL@>H8L%Ek;e=XF!b;>ARTGl)9F8V?!Vx!A;2oq)quP`i?ww3HG)QV~3bP)?h#gjpmoZkA;KEXp^"
    "+vEA*KCEeEraxpYzSdy5Y=!sEPi7bTArX}5@-a?g&gGAxfZE1oWitjDIV!ggwYJGkC;9dS-$VpjM#3k9=(ovmQ{{"
    "{D#>El8gzC#VS6;%iQ1dnt$2HHu)n`G*c*+uwxX~dc7}VcRyf+(Z%12EC*JAoY(_hq`&)ZEdwctvtt$6CN?t3q3T"
    "Yp3{m5l1J`Dx=reyJ`$}MGf<j*m+z566{JjonSGRKq5@$E&io2Xc03Z4F?A^tq*Esq7Q%DUl%LOd+@k(a+(8{521"
    "Rdv>kuhXP=ekm78LUe1oG*&%#%8MsWW~u1#5udX&oU<>V%tTaXVkp!6VWg0xbHL&CuJrN^s-4>#RP$%KYVg$wBej"
    "6QyxYct8}hz>=}90}&#RL4^4X}eV`|4$tudf>L*9Uf&hF)znNeh{D&Agw3EV<7M#F@zn}BglxcT*luUgm_E*9pW)"
    "<eaD(%zP^{qN*Zu^L8zbeH&h4(kpjHxbsH4y0pXSF<THWn?QsnO5=LQ!Oi^I6&D)msJZp2>7Ilg9$KlJOk8D&xjw"
    "V#7`I|5L~6HV*FG!t?Lx^>!dG7D+lu4oYf!0zbWur&mB|E0@SIR0aomMk}2-}08JgnSJWHx{cbe5SW(cTpj`i|IQ"
    "X*}<-f9eN5Gc2cUAmL!!sGoQOuGFJCicG^n^-^<@O3%i?TvtnK8v+tK_e;7A%#T8Qec-+?8FI`sLp(Ki?_k=Sy(;"
    "3&Q0uBn=;)W(8|M+8u1S2Rp;gu(jFQ8SU(Z+nb|!6z=ZFt=;WGyR+5lY!3#l!QR$zFWTPk?CwRo@ZYV?z2W9?cc+"
    "xKuMzVwzeZ^eRW%zDL-nI}!7lavEBVy##<%<A#rMS2KQZ-BO#OeJsjt5DIX+gG@bKXD=oAK&e5nt>9mk^);=xnkc"
    "c?@VhPA^r>S63{ZAg@Nh#*QMA^Z;M-t~G`K#ER-%6u*M+*6aPxkEHKQELtVX;d((idF325PK}Oy{L0eh8l|B)1^+"
    "2O4Qycb>{TYS1C99thsaZs0vIc(2~Abf5g0pyl;&BmS7&Eul(tk)5RBd(5D+OS-P*O%()^P>oUIFH>09);6YO=O+"
    "4#yXbPirikX{6A&4}<1CnU~Ib)d~n!!+$jJOE6#0YrRF|u(6Yl%5rRRULrCghw^R7FkmQeOW=RpeE7NSK?!EDqmi"
    ";@BiQ`O#v+%751Et7?GEDCWDQe66IygarHm19Y2_{#u=lo-T<7NP>Wq7fm|u!JS0T%T^3xoF<US2yF%LP`pq>aIs"
    ";jp%&)s^9*?A_;v*)zRGSzyNI_7g%PF3Hv)Wu@CJ=socSvp4;MPqm#E-j(kPMH3VV<f#6EzQ3AK7EOp>u(hceyLR"
    "3c-SNydTiG7*SS68nC+|IP2PN(3dt&L-g$pcgZABY8)+AqA9GT6{9XmXwIteJVBl#Ogn>`cJI>e@lr78&hK6up+X"
    "3s-j$Og#~6oRaCkTvw_<tH708K`H$q1ql!$_jaJ2C6VHD%ICr|KKR#cl;>7QO8UOLqJ71*<qo#yJ;aGJgFc?GbHM"
    "%0Omj%}ss^`u*zPc0EE>u;Xc%-TmuGON@q3zxDpkf*M7CdBjU(n?VIPNH+%*JY6QPK5@YmxO4epu2w&)A5M5Y4_B"
    "MXsQI`K2A1d~^58EY|#sVH`QYnE@LQ_joFqS3y2nGA#vCZgk1&({-dPH5<DK2S*&B7gesppfHFiM%imXZu98Vmtw"
    "tiU0~T`N$^IDAdgHA{pRR-;w-L6F~6Rri>qtNlZ#$Ud6|xbcdw25&w6i>*=F%aT{4g`-ojRLrGtP?Vp+f$z9N|V|"
    "IgmLaJO+}X@Y+xTUC1m$VrHlWZ8xauAwQ)=2#**B<-47iUTEq1eqng8VN{ZY53pwKI4^<36PR^d-k}xk4ylOkr6i"
    "{Zrta05ugj$crmaH35X&Gj`4y`l-O)!RX8m9v91Di<_t_w!=^MAI)gHpF6WV0GGDDwe<f9qy)~el8UVBFoKfFc2B"
    "U)Y*`mNhoV+R+)r>q?PbpiGQX?3FSP4fiGD%(uLcLxPN(1qQ+=N)o2u&JWOV|JB>Q&F~=~Wpb1oc|4N<RAG2jGw2"
    "fB)^}aPTa9{%m{j^t-{cXP4hU89g2Suzi^!>cS7h@4tVZ4W9n+^x4zFcTb)@8Eg-~&z^&xQ>$JPC`b>at0`U)H=U"
    "~$`5C`SerP9;A16E8b*hy-7(7>f#G)hoscZeIYyGKf{i$pH7k8^zhOCG1fO#CQ#*Dlw5~@QVkpj}7c5gFt?CtC{x"
    "HpiWI)OFk?spdwfn#V;Y3TnX2w-SI?yEsLe5CrTS3=H20d4<b5;e`Pk^${bg%TSBR4#XX_YDWqH}5pP`P+NExTba"
    "nR%*b^T;4z&Kg0>Ev@>iSHA+EUFXZkfgS;4HhefFwv_p_s^JyaYFp8jDjRJAV3d||Sko0^iZU74Pm*H@*%fIu*Ov"
    "ECZBgYJ(w06ag04vIwc|m{1{Xh?C5I-DlbmvIjwiG4RK|UVagabFPfJC-ZFm83=Tyzd-Ly`12VzI}sizM1fF&Q>_"
    "vb{|&f`KYcRN|M@N<R|?I?1WJDi9)klCfxvDGurtSfJ3UV7ve43aR%g5seI@801aT=?~jK?0mod?7OFf(bFe8+0G"
    "A_+oNaOmzUo?{Wb#ubmxcR<zTd(W#4_5J$*I=S#{@0KKgz*91XsM2HQKe(&?sYW$7G&n1{U`dzI}p6{ovvzuQgyD"
    "s%h(`#&YzKPB8hCEPzH-2cMf1mWg-`p`_anx|+jLVl1Y*LgN3W)mbOGgsc?_M4?8t7*2!4`ENXY&CxuoGBRvwUmc"
    "RU}h%FLnA{kN6f4=Vy0H8mJWw~+qlbrI<+)#E2FGPGwf%pVIjasZbr2uuy7^Rf^+`xp#EVJaya~$MYnzqUs8QJ^5"
    "&|IyYbbV6=-&9Meqv~U3e6R79h0|!w~}|hIuS3I13pb71?!ueN!^N4F%3zV~GA`o}---ZLh^Rta27L9kVd!4g*gT"
    "`MB6lNjNR$&gDRNvSAuojwsei4g?{W37Cw=*_9^pmQrzoPD3X-!n|{ZwO!;NW`ZoF067#-Lr6zNYcicD!v(xsHz7"
    "QWg*iroi)6r!nj&tb5(Ul)0dzR%g-<0S{9Y@~k+zut46)4M1=VP#FNo;yBP{@ntt%=ID9}rk8-RGa<my9m5SOwjI"
    "}EFHAN(JXr(v8ENgHO|9}%ZzHmq;Z*eNa8S*xK+54c`b<b<>s5Ws~`B4@mu&6e~X=2WCo8~i=x`~ta`Tx$d+^9_a"
    "Y=l8S}3oz64O0s;KB=YANZ}U9+Hv8_$U}v<QU+#Q=dHLjro#ALWeE#k8XWu=8V>fv6!_%jO=ilypxAXkjW&Yi0`w"
    "9Fn-@eSgt(C|r^bQxim$V2VJGJ5W2m!cUf#A@h%dD)8$9FoZEfM|0pB1A2l&1fbrvH?t|Et@JL$+-2eS+^zg^Ttd"
    "fwiN>CCGZ=7dPnbJp18?AR0d$oE*Ej6wQd0%+uqM@NQ`fj(m?l!zN}-HoRKoBuvZuMK-4ms51eH?Mlk~8ecPY%d1"
    "-^+7E>au}j*Fh~rgone2OG1v8rF5UJnvhl%<TdPQaKIPJb51V8@bikeaT-c94|O=%1+kX)`79PZAS9;ULQ4gBhw%"
    ";Iy6h%n*srZNVVpTN<~=Q&C0bVN}E=l!ygkdHDX2Cc6M%Tae4g@QW}pcoV)ayeVWWwaa@k%#gBa4~=e9PCj#=oH%"
    "`!(;n9%c&?4W9lm5f>Lp5miaBB3~EyX1q!2@I`Ewip3X44(V-!6Wat8kHSA*%4PbY`Cnob3$TD(N{4oXx<>wJ_-j"
    "YL6E^pv+w?LsEf#zFWh>oJa8?=ejkJ%il0qWRr<zcUKq`smM@i`W_(L$@9NWjP(-3Y3!75q5xyv3l94CX13jqs0b"
    "N^eDp@ZwL9H02<lW{YA*oJ3(tv4w^N4Wx{DWl{bs8~X7-7jLKVU$`klZ1#M(0z%Cek3m4jweOF!%d-Dr2UG?a`Gd"
    "Fge|xj}4R4ht)>nj8(dIydA*ntDP|F*M?>tt2DEou<8A8rFAWj|NdsEurm^eO$y#|^ooKCn$GuHh~+!N-93|54kr"
    "4lLSbuTW9C6S6L3O!=56G1g`9tjYe7fSa=iHY1W{_&6tCc-)`nP&K&qf<A18wbeKhk?pPjoL1#2j(+gf9AuiG=G-"
    "YD>$9@BS_<!^U<ul{p!a4t+IB5N&+t>xk?1;ejnTS`|S>}n%Nj+r*;R~&UE>9y0?3_`}*i-XzHM;x9I7|XuaWO+_"
    "Keu$}L!Yn%D#EFB@{iZo7TXH-xl8TiO)=kJb*0%40vTv&*i?k06%!`*4Dn{eBB^lwgz0utL4)x9zTjvW_rI2pJ5c"
    "r1ZhX>?18P{+Ch+c@7|bQ<W8~BNLXq_84|JTP+4g>A;t_Van!R=c-a)1kV{*=$_k;OA7k{j7auGhjr?f*F^_d1Dp"
    ">a9+rz?0T#r!|LA$cP;LC8>tn(%GT5@o?|9Wv2yKg^`RLTi+?XvnDM|BUin5PAPj<ynsPiXkdCf)&-bnPj!S!dMc"
    "z65B@OEne%wenAI}+SzeBSFs@iWb7rE_%oevs&Mj|^n+2;xl1)=*nyVtr$fz7|v5K<gS(1gPI(J6I+@>>VV-62zW"
    "h^!Pt-1L{oEYCB7}#%91xK%3~vd-)UA7r<-3giX@#&u<36rhy}nTKV7+Fms?_JLs#jA4mbzZ7<_ke_mKd@}Ghus#"
    "~y6zmo+j_Mn>;;Ju6OI2V;|1-JfUi1CEy#DJ97@QLW7Fu#~{SMEZgBwgwtd7|!#hPRH3B{g!7HyM`UsY&*!wVisj"
    "VA1>{*-D-|4~T9^AgOO3bp8d~u?6SmbCG<L?A(GpO|LjFE^a{$!F^xYY992ml<K!4o({DHWt7K&QI?=kI1{FP&pu"
    "DPGF?goshzED$M(8ZBw3#=sV(oqpST$3E<7ekQXj*K@?*s0c2H2Ep(w{w#<-r-{e;tl$>(zm{O*DF!+ApynhEei$"
    "dn0$BM31Oe#eAxHXIFG{536)7HP8MlbZz?y~(VL$E7;U3#ZGKD{ht&pn_=q%iIfR!3{vrHyMa-LtFd~M4&4cK|}z"
    "#>#~COb3F^!GrDkOz$(d{4Z>~986EDtMH^QT+c-aT;QInJS6y6LcYY_Y`}*ZQ23@JZ=$|PD@l3Jg!%dVnt7!q+l9"
    "qN*%G`Nzd34^&RhM`*mGzyYPb5tqr6&1T4TFw#??bVeG0;!X)syjm@4Lwd{~Mgn`!xB0$9-0I<mnC!cH(gySr#nl"
    "4V^wX-aY$;dHCr+PtW$>oE#mU@#nKQ$1e{~`0v-dhd;|-d;Q(luMw=w^mrQ`Gwg@sf1dqvbjWYGz`e5M?QMBD-Mh"
    "}<{*oLbpevO<%t;4C=?0j{@*}#>2uivv{%yn)-O#Mt;>@Y=0+!tD_}4#OS3?82i6iJN(5f0<XEm4aVnSChchhzY9"
    "8D&uhQMtBBDUDY5U34_we=Gc%}kqaoc4uRhltd(o+Gh$jxq5ixZ~w5!Sy=$IP96(1i!&b^qkcQel3^7*$OL6*|#1"
    "X?^he;i^ZBocm^mhtMV{#%l<U~*axMEQtf7vG=;U99?WND@yQo@943U>W|8rxG9)%R(}<8TaDY)0Z=u|ZvqD2^K)"
    "qq^Ji}Kge(7vnPAPNddd9u&lcjbTjOQ<6f)O3i=>4ksU4uwWQGTHKT`gv-c_;am6Mb_2oQC}&3nayoGE+#kA~$PB"
    "_LAWihGdckuWn2Qels?h$`OwdyjvCapc#sw^Q)FleO?SxQ7Jo8`XiudPI>H=uCxQn3~YbF5`G(BL8|!WoE|g~Yrp"
    "w)*u%Tb*PZxn!BEYE@RNNoO;A1Q;VI^yoSq!BLuDA%-Rie?v|=8sUT>aAh-J&#mHpVVS6Z4JOo#a=`a9%Nh&1BRg"
    ">XmEDH<bU&qfRDRX%htXlL-~5g9Do)#e7U!U;U7wnCUlr?(E=o~`%!4Y_97yh(Rfev`__VrqKUd#fE~5G<lsZ$;S"
    "Vc(0;Gj4#;mXW^sRAkI?J&~CT`wHj7?;bp|1W%ETE!2Xd2xXHo>4q333OY^X)QUu%S-;ozm2|vb(+&w)-7sN<60v"
    "=ZQ{?+cmYpgU@eV7#+b^k~7vARdpdk|4u>K?Iy0Wq_ND{|uPUj~MaO0RUKuIZGuz)kwRjjMu+_{tvx1`{{nY^INh"
    "u|-AJBh@_6fL<188c{(<gJOp4s$kV*i%xWn0Y(%>9<wWiV#Tjq#89~JB!xPamM&`%>D@L8C!ty6-u^p0I_sbQ_S2"
    "h#Gb(I%TgOHDeZ&=l13`lSXXil%-K;P)J22_R+sVXd8jTCesOtLRtz79xcK8PUIJ4>lpQBJc&xXBmANjCPJkncY{"
    "2z=h<gptJBf`@!5m>nLsOPgvN&jr?{Z+@CWm7b;sME8P-}cUaJK695zWe&%W&dn{ckh?|lm5y6?+5$;fdBlD-wsZ"
    "2^WYZb#b3+B%*cr$*?nDUh&5it|AwvxklH8%8F^(Xs&qyP7tY*YBqmHqDovnUVM;Y(21QVqo%o17Z|s^4?I(f3(t"
    "2y7E)?}HJm#Ibwam)*#*B_$6e2fH4pT;KI+0KImnXZg&Sap*#O<cu$AiRNj8@Hjk)muX5O@0sbX)okIS^}<#y4{m"
    "kP)-E+D;2nXeN;fB+Lwy7O^Jw(P${4*M$k>(@;YB=-WgHAb3P^9XDOrqFA!TR8Ax(>=2)kLc2v?rUrL7Gj<?~<<w"
    "YAQrr=5jKAiiD_Q_e)CT9tv@{$h$uX(k6kfrMC&Vse=Q1jbAaf<hH$!YaFi69E3~bWU&p#b=LR7xkVh?o&D#!ICh"
    "le^Lg)nNv54H4ji&Eo)-NKwAlXAqf8ladyT8-T`=_GsHZQ|?!L`XBG8!dc!LP4j3-L}X3DtSt!4*ii1i|lF&7oXO"
    "-nd%HJ?Wp9Z4u4C)n5PQ+jDcxe<ns1AzAmORe*|>FGCL@C@}Nv{Wjd%Uv;tx`1e%b~aq(|b@p>bA0tUS5l8~!Z78"
    "(J4^8m<R(4ZGtr07ZncG_I>;Z8$v3Nl~8X3fSkEUKwncj)X{7P=Y!K?#PHJxNw({AmL%t<c=a0Xsp=<D?K`9nS2Y"
    "rV^w?0(EMae5}e1LrtI6auJJyU&}>at`<ntWRg$d1UK>!!T-Z^LVSH-;r!6^r)h-@WYok;e!`7yeCk-Lwm|F(sk&"
    "r>ot)8Q?%o*B1S#@dhLw#UyflP&LRN#4{nxMu-V?Uq7ThKI6huC3@DbMw_ux32r)-5!XnkR~PV<i#3THPh*F_cPL"
    "1Asvtbz#cv4E2tsCbD6XdxBv{9J;Y(E22y0a#}hQU8@%tSU<BRYEu%ERmIg$_zIdEKW&r)`-)u$DOF%c*>7g%ca("
    "QrGRlmPbp_=0#LAK^@m)F)}m&L@-aeaU#);MRwnHq`V5UKz?U%j_1~0knqwAqnJ?K<U&@{lS0SwQ6eF&E;1uVS2|"
    "GrkdiJT9tR~F??nG#=NSxw3&<%#R%J=z=P<2UnP;MY5b>~RXj&N0nI%wM=(8~`w1&JeA3JT8XV<@hsqEjzO#wm3P"
    "YtQ;C8WXL=XvImiiuJ|RrwEChuqW}qvyp_fm-tT5G%4~QE$*h6@1~sL+gi>LJEaa+_?>ZDkYk2U)Q~UyEL%jaX9J"
    ")MmC~ALmjxo+Y$jBgg8;(f<Pr`!GXp-@`54qU<Wf8uk`RDP7fWZ=N;zfB0=A4)sglZ2k{5t+?{j$tMm)X26oS<dw"
    "~dWKbk4iUkQfg2FsXn6eBLZc16w#n05i*{SoGoGmMTb*xeIrX4@_wU<_k(9h5^EQY+7%5>Ewr#KxV1GP7V+XThyi"
    "rg_%)jXd=bl+&N3Ak}ftUL_~Q5)k{&%41&Q6)2)fyGTuR87B94*Ubv)sPnZ>zb%Y0oaL5v}XYs`#t_tk`zn>l*x{"
    "JF>mJA`y4Y#l>0o}{DNIck*fpU!(<af&gW`4u<K9&rxJES?e-|=ph0u<1XVDFM226iwDHy8<G<T;9e92aFhH`%A7"
    "KugQ-l*D`oo=M7I3}>1(^g$AuLg1-QSjh8Q7Sf;3#^XK~)*IHb5iP93_m>YjR+TSC*#sj3St7zJD|$VVsGqTUUn}"
    "r5ag_r+@eDeEUS}L3MwyQjTK0@1ugyKfY(O^IYEEBWQavS8GclE|Mw`s65weukB%7L|Kypn>IH=jLJe|h_3=g&91"
    "-#8@No>jzc{dx<4XLND#Be!s@ef5*gA)b>X<#_NmAM5xqlp`sV|;-`CraM}DyIABa<+V-vI=cZlLV)D4pPR2lmSX"
    "6TZV#ez-9JuKT=gn7T$7QV4`GcR#v4PnBR<m<fJMOU)ObP=D?AfxWJ__Y)<D(?K(U1{3QZoXM?3tgO;F7r&O@VW5"
    "Rt&1WB&*@f-y^5(@EhEcuPs#T6o8z@<Gxfyb7_`FK4W=P}|$A+fUoIpQTjBGqk3G^Vh-W%3@O*+}sfG9l*p@*24d"
    "Yu&mQ7UA3SDH89T4TWx7zNf3zNgZY*ApWxBn3ceh%nOpE&JaQeBtHW4=5S)#V^b7cFf#=9IP#svro866T3!Qvzpr"
    "C5r|36cjhng4n}Q7XA7L6OSb_G(rA$GxD+l>{WrcPvzlZ{UV|=8T&R2Lnz|=`_Tgj;bIpT6G$)WHw2aXS6Q~hgpS"
    "t@H$2E<uDB83d`CS0HuL74(7T77($<ihFfqnu09MB%=f&vS{7g<+Lzc!W-f)$9U|EmxR@x>Oe7Y9+j1hFU@u1`fj"
    "~7b;Kk0~Kw`28$WN!_T=jIZDcAA%v!erwvZ!jCUIiU)W8FeJ?l%)hwa1L}2ce=~KfT_6%%%4k{l#PUq54DAiOidh"
    "=``=#5&HO34l*Q{v9YtI`{$2}LJ0!r2;4=N`$=90(Va^BG4AevV@0&G@o}W<Q>xedMxagB0^(CNYI>&^q7}mJZB~"
    "Y;V#$D9V)L@Oio@Ar30?p>y^rzS~^E2q+0Uc~0@*t0@KdUlVW-+H-VGmSj+&X}M_yyg-|9fbVNLfMzz<FoAt~spf"
    "GsFoM$wmRXYww*d`zkfZzttZ}lEKvuzB+DvmXN!^&7JvGZpJ}`$naIyq4cS=!1tC%BFi?so>{WN9#g|$8aCGrJF>"
    "93Zc(Bvdc^KUGZkb=+FP|n48p+)4lXtX3fi=ZmDr=i|EI^iaUam=ZRl66A#Gx?^t{U;u`FsWQlJ%<uaW`<hkmePr"
    "k3NKrmjil6sqcQM&IY-MTvo}i~3~lO)9%QMK!V(;QTf*%)MPtDjy^J?D83`eX=Ya>pWiG#>6%%)ptq#sg9?_I^Pn"
    "N`ylRHU(FGwd{Em^0Os6osYSQN8`uKhrD5*z_D9WyZcWS&*iFm7zr%y=mqZK5c#&^Fzo124eNY?lFAh}jzrWh0Q#"
    "QtKm?G)^|9W0_4(+VuF5O{U_AGpcJS*-AE~riSb6PVIRrN^>h33Y)BwARlPcto-eI216NBeL0kMeC8jl{^Es;Y`I"
    "aNDOZaR1(kczXf)KV39@30tkX=YiO-x^Kn1HeixSR5W+5bB6r&r3q2N4hjwg|XGP_49VwG%^yu&;RpK_EL7YmLzs"
    "W6VZE{vbWY*l4M#$jgTz$y;mG;vuSWNj38<srm1`BI2SUkYCcA)HCDr`#I3r6n+wMR%%2&v|I?;ee{mhAwAssv0H"
    "LD4SR<PH0YXUq&%>Ytf5I1WxGy^9!eBKvhHv8djsFguQBvO|}rZPM1pDYFKg}q#znn%63-Y8ON(<7Dfz3z$`f{+G"
    "w*xHBLoDrjjiN*IT+mwA(UF#b{z7%=;u_n_ipYO$IANDyrrIju-=+EvQ5T&CoVuQD_mKD{n$!H$aLU-C-+&4}{lK"
    "#U}PLvHZu9A*N4E=F4VLh7E3`+%Z+cDJI@DwZ}xPdFC=8;ha<}Rw~_C>J3@WPA$t}A3&{tmkZO+#u_6~$7xO+Uzo"
    "v)F$n(absJMZTGHUDH<UPMh^wN<&zL=w{o7KlsT@g09d~VZWQAimQoQ^LiCid2lNW&a)l}Hiznvnx*bkoIWRZPze"
    "YC7*p(KP7SB?=rO>)ZtOFrx~$>A+SmDh=xIL=gjp)wsE1ddYFTDsLq>Olhki?P))A_I-C6$e0tk-VQGPLNn<r?#3"
    "d%>6@FjOp0WRbG^=xTE5-5VljR-_RLmuTyzl%#E?S>f25ot1d4T1#iQKz%4&TLxH;2fzJnc@$Q-^tLOZ<Aua?gNP"
    "@xR>ogu(YI0%`9k~3jczm2fzu7P)C-JoK>;CF5{-EUyvtzHMEyP2r<p=JX54B#iO(ey%2?hMIIi)Z30~v488I4ax"
    ">Y&NlccRDcQ?fS*2Qh#GHR_Ln{%_zDXOx1I4ba<5aXBLVvt!OJNVj<$h?}FmQ2Z0xd8U+{`26?abC)b^2E%JoOkJ"
    "^-UY%NSSyF7+4?4^-8VEU!_0PC*B_er$nBhKh@NFCT!YkDJjAXFKb>EoPY263DK*LIwd_{@yWa`+Nz+I;_9~@^=z"
    "HEU(l9T12c^TJ@%;Ny{6k9e>@-i5mie>=9FsNojpjTO-D6p`v{J22Ffh}{v;6)w>S`=5;wMxz_*c|BSl+X#3Ow8O"
    "3-{RlIpDN{-UpO`UFcL>G91O`Vp<bx30uMNO?K_5?K*PE5-%8=X4cJT&)xkQs85?dRuA(9Ph&@ec%ncOQ-30xKFv"
    "l$_R48{MZ8ic9XFo$GyZ~<l()+wA&|w<^t?IQNvXgNP+?0?56wIJp6<m?T2Y@r_^J9>dR%i`|{+HJvrB7L;y>pSk"
    "KpFB%5!G>>Jr-BdssN-wL%<|dokE=mt15~>ASf1I*%uQ=vtDX(99{&8$Id$#$b`d$*!$Ksx1Ox`OhQ4ZMiNIM43<"
    "uf70r9H`jLcV6d!^THAVzARaa<REN2sBZev>&M;PTYCy^*x0>$G@`^tXc8Y?l;j{FHEVL2v{l&tHQIYTlyu4RpKA"
    "lEY7P1=Lj%L%;7&h#`cYK<hLd({-+L2jZoeKsxW<JxHF?7{T;B%DIH-RU~Ft0N+b(tLVloyvT~DMX8leZKHk&>%e"
    "uMO=f7c3XbT=A<w>Uh8$SWvaf&e&VV;5_dwLrP(x3qx;LmFtB!Hb@t4uYvycoCzO#&>5$L_r*@`0Yfu4$bXkloxX"
    "P<m8f1+`>j2Sd4iMVW)N%<&c!~BZloZAsX?3-bC>pJ7be{@3KGWg43pKpvC($UZfuVuV?2id*ND$$tbklzX*_sLh"
    "tYs`=O(!4L-<FW&%cT;vB*62a@8FOX>%UA^^N%2Pr@r4AHvE_^MArC8QQoAK$_8P(E?ut_jx-a!T|?8Glpl&Rb0W"
    "%k5+r}P!J|S}G1#I(fDA02O*fRe1b>a%Sa4AqULyy21-IxTK@_2qO}WE-LBlG^!XaKuT&=YR6H(XgMJ}!|hsuWI>"
    "w&bSrn*@2t(ID_vA&$f4BN=8AYuK4qpGb<u=AaiCfJsZm^y)|I$S##&@|~pYu$np&I|@Vx-hI<&%qfYLSaOTI@HS"
    "<cAa@ssV`SJODVex9hgQXFP#YS`;;K?Pq|pc>dyI*Le@EeuFbC96EU%on8jXKW2`Ax6SduKrqigsj-$^Ur4Fx>CB"
    ">j|aGo)_a_tONK{$LmRfJ(<A`{yeCL=7!Fo;npq_U?328;nNV)v#1qZOLQ=Bvvws8deCY-_(2Eo6Sf;SyC7XEB8h"
    "(ZCvh!kc?FXMKcxg4X%WG+=RtOl!Dv$+qYkV_}m_GGmO!YI+qgVV8^fm|u@+aggy0imE&mMzUsXN2G8bv{;!*`ne"
    "(mXF&#0&MPo?{t}Zyu=Pq{#_KrCv8)@P(=tR7E+!ykzAzCWfxuU_L-Sg_AWq}M6`NHvu_hJ+@`dB{5?MJm>Y!L4E"
    "5;7Cb580qdSxu|yRWxW&IH-|IRpTOb8;sW?*|^B(v1Y9qCSL*OwLhyV^kdF+^J|XmN@J8O|kFfIcCUZd`kuOF2sj"
    "JlNhQOa$Ol~uECAF2PU)6l`1fvHSB5Ec*+{p90&W5??@DpuTkza=5F*kZf<8W<5LJgVo>OACY@P#dN%@Acq7MJeY"
    "T8Hn5wyj5xjBvHCo5Io0m5)^nETeq}=#q(JUP|HOBnl4#GSz&kQ`oz1d`p+2dfO0FE(L^hWwY9LkCpI^lpRc4er6"
    "SA-lHvn#xiA;y5y4Q)YAnt4%TqzRdE1W<InN%z%kF)#~E#vXQ;;W8U|M#mWpFBu?rsUQvpa*czx;d;C|?;G>hD2k"
    "rA-!k+Q%bh9qGy~YjvLkH(Df-ESc0&vp$Xz^1gc&Jvoo)qdHYZr}b^c{zgfX#gtf3i)nj^uwUT5pz5@)7^GD+)cy"
    "j?tG6V-i&d&tAXWR%R6mls;gmR?t|I>qYZx`)(cN{F4Hfy1swD-+z&uwzFBaWf0xMo48`NH)}wnsFV2q{KcYC5FI"
    "`2$(2XXj{e%sa%b2F1iLwuB|2R4kyS(-~$QF@x;emv{RrwXtcz3l2e1=k-L@0LVU*#LPI*&nnf2xnWuEIGp!k&%="
    "eO`y=4-!F?hm*awMkL?{gYOzpuE8<jrG?odfuomCMb*9|>OGfpGk^{J6;GUkAd`nSGC6)Pa8~kGh5EHQ0|dCfJ?^"
    "NKZ^IJ~uFeuMs5+cF@`G>941C2$8Xz)(AAD%~$nsAy4V)GkCaVU#gk5vIj-t$*d2W?QFUaQ{^yJ#%?L~8wM1rQc8"
    "Xyh*np5$FB07At+bCA%Nzlz27p(3|9Ay!Je#uQI+p&uq>I@8zWhw08U_cexmf$gU3-6CH$78&2riKn2q1J@DJD+l"
    "HhF64%$_~DF<R?N{Fub=qp)(m-(nobS8B`QESXh&s{<2B2x96-hh~PG@DH!!i+3KHz{KilAI{W>k@uF=73K-f`EF"
    "s4)|IGnD<vnAL;Xq?CgSe1-qsYrw9N45jPyn#(j?1u0a_zAfOJA4Emx$uqp|YDcn^GZbolX^gsp-q&MQ9(^;~W>?"
    "B<t19a8rZ!0*7Hds#)aqOXx-xOtnj%Wl~!r2qt#)pIxSPg+2Sihc>^}lqFxydL%*W9$IEFW!MoPgcO%2_)g66OdK"
    "#Dn)yKLQ{M+<Dwp=W;f@;r$n20xiNBI}gClsh)?*^Zo;TN)%?q+iCSkqV+^Gp@*RAjtR@WLc{=G#3JeS%ylF?xsH"
    "ei*zX$!uuR<p5J6TkTbv;Py<Pkz$DE`l3RlMbbV301rpKub!^%lhv_Eek70^EiC(-OH>2W=(U`<2!xNS^c|4d?dR"
    "v$HEkV`6n6iRXX9-tAP>-7XKoZyw;;FN*>9XK6LGz|_xZ6q=hA8An`mH%G@78NE_g%({uZ<^~*K6)q%76xe3B;4D"
    "ZWRP!yEomTyHh~Tm@2`t3*#mX;=<slVk3e`T$Rl?}#ua-%qav+<+cAEn0k3o)j}(}=Xa@*Hq=)Hv2^Mkf2uX_Nww"
    "`EMKS<E=PIeDZU+oi$r5WpIgaRt1k{n)>x8CT=?1P~sMQ=udk@(AV3$Sv5o5rATVTklSPg6EE>Y)d|VGM6xp=Cue"
    "#n>kh7QC%BoDEiS_|Pg+jE9nDjZv;JT7^mz>Ax9%s~M`i(y7lm%oq$I*F3OhFs7RgM-u?GnN|0`zi7l``~Beb;HT"
    "I7ecTxVbddvb#k(8+X}f#gseYr2iQ?2^i8xLy<E05-p1mgy-}g2&>RZl+b~m!KLmbu28B6@2RV5(pNCC8DchyKjL"
    "2I+$ENogu>xn<9bZ+zE3rW51@o)oEH+SE|>m<G4t>F%Dv(&q8ur>QUc&<7D?dH7t=8JXn*+702#$#jLVB`d|r{Pi"
    ">o{v>H%tFV7o5rzL8NIe<bAW@<jyhv2s)@^!j?o}g!y}e1v0ptNTyH<|j9V{_R#7HyMM<nEAqxDH7fy&}DUq0Jq?"
    "EUIDrG>>W!7j0BCF2;qng-|*2yjhYW=~y1dJ_`R_KNzQ%P<r^O>)t3FZ}>AK!3z$?;<L=?2leY#XwUaHHMnjWKo2"
    "6{|{q`w6ania|^fBx+P#y(|!9<`n{`rMP({)|Yk=_Hz2m(Q(!A)Kq@~mqM&fuvPGRV--3+IoR7jr7O>?(}zH2-)<"
    "AoHGI4G%hBG^>)o?`{Ql{-`Ti6nhJXCDe{%9qdf>ZnZ@E_!fd~DvU8Q`#!h#yKR2_th!avX!({_z9I5d{1=y9yt<"
    "r=RJXS*7n-ZEs<y-L3FK1V0Pdo3+nz>gOhNO<s~%VH=P)9`~T{q_aN{9^kS=Z*Rvm<a-vq7Y4M)S492KId)sb}+r"
    ">llip0?e+c=z4Ny3@MZb}1*1a0&(gf*YT4UHKM(e*-O_bcl*>N3eOmqC*g7_<&yOB0FzM^<0}k87<&q)_ygrMZtB"
    "KKu;W`TZ1Mtpk!hpSK-})Hg{ZyB&q>^GSUA6#?_QGK};tOnn0B`17VC>^n*#W|8{YLG{;it??f6Z@{lZvlO+Zrxe"
    "MO2jC*EO&4%A@I+Sp1-hDr7MCL=U)iIf?j20CIjh4t`&unQ}0L#o&^2(2UR4xxQ89o?A-~ir3)Mj2=mlu02Bq+XM"
    "e9k+;3Oub@wG0~7ZjJ?XPTZ}09h?JH$&{3vnk%Pa@SCiU#nSI!ug3Dp_4YZvj+BkIYcxemyzt*N2uwsHzeRvIRcc"
    "!1}T1-$ULNewcjS<nAwt_i7bsqBRhzmIh%ghut3n2Cy?oDD_Uf96}0lGCM|=iG2U*$$G&(KR>O`8nJ-pv>dHrWB="
    "3uILhYDKZwW|L5p(B!^aP9d#I`I2tC1wRu%!d)FoZxr%`f3<*tes<%+~NUW7Z8q?VMF8YjtFe}X?hL#<^E>KwL%d"
    "|sv<~D>VeLH2`Mq~Z=*R<ts7t59z2$sCS7W~qL(GMeM2i=+OU6(pcp5LKE4F}*bGxJg>ua?gu@K=PxoQv}^t=xL4"
    "d7|z;Zgok^!uX{Yo<T~TzYugJ4L74uw%{^MT~=u4=((=&)wspK=GD)|c{jYzpKNQX1aodT5&}q(L}zmkNc6wXv#o"
    "#cZvEfeTR-%-F24DzVU*4>N3_0k=v|MnBSM%gr~0yPlJNB?)$FTOtbct{m8o(H50T@L80NdT^SuA``)5_qUD@)Xo"
    "ZI@0zjT-q3>Z6OELRfO@u}N(#o=VTB;^sm;!o=}CzD-Pve)S{k6EI{RkHKs`{ZxE$|Ui-o&NT-@B80=_k0seEr)L"
    "|8J(1Zwg`SqLJUH^%+Q-YxkN{wNo+BK4l3iVPNB-L%Q}XAPAjC`jXjc-ou{iLa+_TgBe@YB(PN?&U}W?czKI-T9A"
    "(#```4>@#dnO;H|ph-zZI05!}vZ<izSmEg<EJd6$sri)WWLI-Xou<TMZczWswTh5cJ=NuKLo2hqGR-NMVj5IuDSB"
    ";kBWG$UGk>XST{+obnWbE_aW4$cF5jH+mBhLU#OAO3u3o_hXHHb%Qamz0JfL_SLq!hNjWMb!%$wxkDuy2WA@v>y*"
    "V2`KM)w5>{W4oK`W~v3-zw5DwX&X44)`wd#jQ4kaB}>re7y{J2J@vk66|3z$rQjGhgTlCe(Mkooq3VBB|^9=FZ)P"
    ">^ZMpQ=T{)o)VDwUyNI;ZH}W(E=(PA32UIrTM7J;{af{5a--cdG2g3z~?LG0%zf{Pjk;y8@HR)om#;2o4{fmXy0)"
    "S{EyJWYc+97a;nyZ@whh$gPzt|ql{x`(Yta3WxTP(L9J4L2gQ67<@~M+dZi`-$)*)jv67C|2^I9Op`>rDsDDjmUC"
    "KR?OPTk_M%sG)DnEKe-BlK26U}`i?VY+`r@gP!;JpQRunD{{uZpg<xr!H8>Zqx!bZ(-}8C{N-X#-u3*0J$5UsZ+E"
    "H(hv!9ILmqEPaiF(qn^32?C-~Dm-<<KGR<7b9j1JpTpCy>~ok<IB7f%wU}(?XLvis>#DEH*E(B&;Bt}s>FrciW)#"
    "Ftf9DKCgWm_ip`=tZ1959D`Qf3v7!(W?#Ux(NPon?@F1b!gXLA(sG+xD_+*%tMz5fjMOV^mKmarzOY1`VXlo1DNC"
    "*08axlSfcI-L#{&QzBiBZk1F-^1QgYx=g!*adbqqCk<ZM_v&GEHY?fT*ZJ-iHy$r{rU54HAsku8_H1ligOW^s0Ek"
    "(Jg*9o5xbc<^SL$~Dj~%%t!uS`ovzMaXRLEZBg2_H>POcVs(o#!eH(enZS|{>D11iGV`6yiE+Un>kbb<axbi{I?j"
    "IUS*=re-QGrDZiQ#VT;OgN_dLaupBkz5_ZKrKHLk0l4SE>6$Q5|M`a9xMcZD2Ra+Xuho<9YHL1R0Y`=-<V}K+8_@"
    "isnN!u_Npxu7}<M@lffMbBS5(_%YdLmE5(faSIKtS|R|kEqvm4{*s;1oKI@JdF~tFBw_l%WRhVzDPuWWGfC;+OhN"
    "Cvm}hxOIXzfcFrNwvlvBHcL(mDIRs-O8FmAFUT^8ZUiH4NRpwOF$?o_?LYLd(RHN|QGO)Glbu#PNoY0kf_;VEV6A"
    "Z0k&DHzJdMtt%$nx9JF_{kiRdEEE>i{&i(!_IT@VN%Us_<A&+W%$GMZHME2Qgv3IditdQ-Sh7oc<N4n`^htXCyHy"
    ")R?qs|Kgjzrv2KE*5e<(;HitpmX)(^f-(Y8Z+s`PNquA$|Ks|kiQ^CtfIXu$fE%DOG&z6F*Up->Q8hB)g_g|q_T0"
    "2UY7V%2Js4q-!TFCF&z|q!xC!`$k3$~m54Twx!*VGYJDs5nf^;7Q`*_e%?HpVVyjzy8EQ<MyZBf*or1=}X}Prjhh"
    "-C-C4t}|2sm%3pPQRqdn%@-1?wqf$OO-47x=)<ebrxOcH+NnR#O%DBRHa{Wes(}ck&$y040#b6m(5tIU*GQaQL|H"
    "}MS+AU4qj1U3YUM#u6)TptoR_9fQH<1#jT{xcg~T&K0Mk86W1GxiO=i<#kP5mxUWN1CIGbD!v#vTYb=S&9?CBq{j"
    "?5`lAaw91dx2?5htpQZA~>f#9u7r`bGN!teb>{91N(`L<^$3V{-Dx#h=yaB8^PtFah$@(EHA^&Tw)R#u52m`%5|E"
    "n#wEKUf(KG(qNzK=)EQtZ<4eu(%t#nm%$?cabnfo%@#S2*JgpjYp-c|zSsooz)yn--4!8DtQhNW`Gpn$szq5lk`~"
    "BAkZw}6UmkfJHfX;T`b<|~2bxk>P?72%ndE%n&*?)x|{(adz%)O(-v;F^h78xn4oG9n?5I?Uao%{EKzA|!WBwMnW"
    "?I7q{yN&VGkcdaW?jJ_R7PaJ?9c>Oplvn=fZyWD2uQipM5xqHjx&OMqcXS#f8C$t^6uqWl_z$_;`kP9$EsdZjb=W"
    "ker&S%R&phmQX-8BZ*+7wBw0^tcHe0&;BaPA7;H`SktZ&ddQW)K8_IES!2aBQgWdEQOtJgF(_IH1HKjWX<xUH*A@"
    "moWgHRCuq<chk#o$mg;?{9nV>zmjcoB<C>EffXZ(`4x}VwBai%VOxbCEyOg&msur(~etUkA7M+iIe@~{as+B{k`4"
    "Sulom;<#8^hZ|v)TwESdN<>+w^ar8RIW^v4%g+)EPtV555mINoFsL`cel@l$|;$w-NM2Ee;IexuQ7fLD}v8G1OZ1"
    ")S3_(fHcO$YmLj?exH_tNp}e^yvc+Yf!LE^?JeHr<GKycIV-XLmSjR_d!^g~kTv+@9j`k9cIOYkdbZmesd$L=DC%"
    "vse3@S-u=y-MQX*W>x3!dUKT@ofzI!c>FA(tyz^4>TiezH$?3~k7YIb2ET<h02OD^;wE0PY`vkl4=YpK7$CW0((3"
    ");MQc=Ud70zXWV`9xgRA8f_V>Y3&^)4=kz-XRU$>Ztr8Zgq={j2>+8gGRki|r^qgj){qGbr-L$7buM>vxW&{;ui3"
    "-re%mci;$8(U#~Gm!<63_DvNYImrZ6@7<Fys2YsG_KGf1V0TNWzS;<)!44xd@AK1I~6xSAe_y!O=jaJ*TffB41O2"
    "`F)ha9EO}0lkQ9oOeZ0&Ui<{&bef2_Mo1Q%1-e$Wb+Tl8|-&`a-$A4u{@Goa)$L{%MpT^NN7i^Uycrn!n=gs}X)P"
    "qD%8-YfnABPdk)`Mb@^a-^8&yV@^DH2W)5lKI;un5tuIgL{)9rRS=mM{Jwo}q4^p7(ZN_%My)5l3|5ON0~0D!hF{"
    "vhG|jm-D{!q`1=jxx|K18Noce!6dy{N+(gsIB%F<l{P{g3e-?SRXx<RF|}X<R^85vJe$}snaVqW#v)g8I7p*C5MG"
    "y02t0{$!Mn+JHP1B9;I2cSnU6*UdxpnxI`fd`y{j$8{e?~UEPY$C7;9Xr?&HUF3=jdXyR-A`>9fZlcBnMwW7%wk;"
    "uB*ZX!7bgSF@~_)wLtfT!ZWb0x~k2J-*+!&WwjEn{&_(q7gDO&TWI@r5nAL=@?C#$<bj$3(D?Kwzp%#SM|nYvmbI"
    "0Q;0;vqAG!EAM!E6ta<6B=G}yq5nN{1vtoc}mtnJdrVB!{q2DO2-}#zadRhH(gb~v<nhr@hLDfONji&t9%pXHKZ7"
    "~~qK5nG76CxZRdXWbb<Cru}i*s{GV{<ZXSXArt(Lg_|#5R2<ui%_-C)X2uOGt^_v!=gt1vB3k*D!Gh)r|b&BSJpY"
    "<*ZEI!ru0R7rWz1lk<!Ay0tT11*>PiNA>UNlg*}~cz-yGEw0P4SlD{fku}7TBI7{s{JjJ%j9fcs@AgHLcp~i_u%m"
    "PJSYND_Rh%Oh?Z<I)U&Po@JMPKGzBpt>Xx+$LL_w)6xlvqd+oKFYTU@@;=xNev_3=R46MHnV0OSycIhzZpdW0gY6"
    "mklFSu8DEQnT5pQ!(U3+gi(xvF23n#DJum9!C!5SAxO2gcr7>nvWAqpc7<IVAa;DRyMJvrHLDNYlCeM;2eFbM&s@"
    "-my6;O<ixlkuI@&ON8LCzmCP*@Q>$36R}4c@iQ7(ETItJ7ICVXeUHue2c)q2?)_>NLQAVbUT2waTd?LCS+>ajo#9"
    "uYP(sx<Nx94hq5J(a>L3FF<u9&VITe60rJ8Z;uXpV0X%}Ec*+%R<7oCfst#T9Vzak<PMSBE;WFZ2x~7j49Y3zWB@"
    "dyb~)@sQ3<EP22Hl*IK$ofdUuLbfFe@Z8n)oG-m-PUm|Yz<bedGPy{6vkr^q=@<c8F}3qqn(XXw&N@W~yUe^*QMs"
    "Q(>u)2iFQRdWRFI>5EJlhg%DG2S#^r1>#vnvNvLh^F63M9rYJXBPgnrz?FAOdc&ZrVx>W6}Q3kxGFEM!-yfpXC0u"
    ">mZf%owyZDCe{&@(~qq9Xf$VY)a`QVSo`3g245q`U0ZqVCq|!!75B~Jw{V4{R&hD<&`T3QZ<1oy@0@pr9VDXSA-j"
    "kI6c{vVDRfAnJ9vZ!kOMqVHN2mHlV2{gy|aV-FojU7;K;F0#R5JuEke~OL|2zXL5Oi{ZYLEM2)4gOBSby9)4JwaW"
    "iJOJtY!Hg@fbw6u>wcq}3QLk^`)jBhgnVWtJMZn@aU1HwH=3#e}6%Sy=<eid(!~3?47ANIAYA=zWz<i+?i`>tnT4"
    "crmue+2B1gTn0w(Y}yy0m&bcNRf7PU7h$Xjo=H3BeGUQ(tjOEdlkJ^n38i-?>{m>aV?ow{o`(qUN)WgA1e*0Cddv"
    "SDgIM=;!^qvJNyDPs^Aj)Sb4_!ufT)d6MDwU=%T?NSI>e~^^kwY>0+X$yCm@@?=-xFCp{q;UPxFs(&4ALm9Q3ENk"
    "2MdFlwzJag&%MRexOT$yAdF4M04bAp#OlAWsM+75%J!)8${LYW##q$)EYpnWp5&-uMldPfZbEZo-Sb~$kC+S^faM"
    "2cGN6|9U@D~6x5s^=dMbvbPP;}O3)Jn?Ieh;tX~x(7`;3F?M;hc!gFfBLo6%ofRMJ4+LRwx(%ILVE&4NJ)5Cp|FU"
    "L0$9D{t1=Fv$`v4lK_NJ<#h3mY5BFwhdcWTy2FgP*UcXd<lrJ4WvZ?v7k#<}f3A@g<h6=Q?j(4M8EHkz-4&lC2F|"
    "ER(IR<Q*bz_q9eqUcO6+k$KUo<6`<AJLM|3RQ!_=_c^!+TTG~+0AVNz!k~ZSQKOF;<^oK(2yDk)cb%=Igv(H!MR2"
    "wo+Y+311{mglvnHlEuY`i3a4wPGVmmt4&Rc=#o4DP7!?@RcvAl6Ib<4gk5JyNRTR##CL^lox=uR0U-s;Zn!4%odY"
    ";ki;`^Y$e{1Ys>O&;x7F7Uo`GNXcMvJ$TA*6^}xxF(I?u_kK>bWb@6r75v&cecOlM11dp#5_rsd4}Hwl<)04!CZa"
    "IMtaXo#y<%h!^@6?-tT#J;U^0@*b&2jD>Tg>9G>o<oFzvm3A&kg_x6*6!?PnJo#3bqfMW9d?(5(7Pm|W))8y~%iu"
    "F{{b|`hu^=|6-{XW77^!x30JXrLLMqKE^w?f!BQUp?6^VBSL>aTEon&$u4%@<^PSgNPq#I5tmX?pvIOrLla5CG)o"
    "vV~Wndthp(7MT=iKG4;cXa~3_ceeZ6sDAhpQ^RG~suFJ>)XvS70pQ$_{(y2+r<AnQG^ruhhIb|vNsC{baO6Oo#av"
    "Jsr`$2fD&4}eSmv2zf39qZ@;j$o2?s&NNvg4Rl6SJ5-q9WR&f7`v_#(>}Teu)Mc$erUSWNY5fa{8CZ=tOOUh@tK("
    "U<Pu!F@HJeT4fOV@AysSXjoQb0Ecx^Gu*usK$@fV|-W!&OD)ISJ_ZK|BExbzmO<EK)E|Ri4mNW$!feTwva|zpssa"
    "=0s!lDD=KpK%WOQv|2}DV6TD^rLdDpZR3vXmbsK;|LKhhEiAo4@GzydbIQ3S>nK+Ugdy?@cG~P}kY}M#|gT;)cVd"
    ">3lu2rM3pC?<$a$#}DdD4>nyE56{+S!&pBT)gVtv#1YO<P--_CrB^(Hg?yUjiZ8FKA4AN3UM(@B1}0%VoCE)RioG"
    "c>pa=_7Bf=QFMmxPu}oJ=pv;K=!oQdXiLtPT6F%B%VMH|A3IZ&S=z+Y6&CWwB1Z%0Z=gj(rZ4wj?f&-qtiQK=w)^"
    "_%XU%4F50}koQ`yq~)^am;X|wgd{@v%W7ok`0S?Y=m&Nl98<yn1d!_fx$4rc7Un9lHj&8IgR7C;$|@;o+$Cp*Cuo"
    "`1U?j~~#<>}=Q0=D9PQwl9h(<B*}df(g3X=vHW4&S2@`1t`z(140&V>v7jpEP0tFpj@pmR<yzs@Ypw>c}J94bMVv"
    "f5a3ZU<rrrljb5-j9C98;hUoBAh1ETnnt7FZ2>9$L=}OCoqVZq}t#Q8fPB!j4E?$b|g$TiUj2Z=Egx|=;p+!GTl`"
    "~X_mbnZ}tQ^WqU2gLoPlqb-!ZF4~v3v^~Zb3t?mxdLZ+bJ^#_DcdY;&LaL7Qq&EDsqY4OmKu+6Aw|#S4%F?L&fO|"
    "wC_;;EYUTB+oxbfMb;G_KivO^tgcd=Z#HJ9IuY*cdmOXQrYL7)wpf7%v?xBI3T0LbFK4}ysk)KXIPq@8eD{nPxkD"
    "Ip+hhrs4+ITD?=;l$FzFWgAAXwiE#8hQb6e%|W~}9Z^xiOf6pvnufU%N|djZo(rd+CyhAO<cD6K{ABV5e7<aYYF!"
    "LsQMO94dO@V4ZlVq@dREcJFb$D!*<0KtL4_#(1sz#kuB1g7Mn#%mm}&=1Ez$Ym-uyj)Ebb`<<VvI`nFQGNmHz2K!"
    "$BY=04QOP(Uv@90ZCE_9=sv~E31Di`3wOqM~yz|8zqs#-v*TcIZ7S;yM?@2R6N@jKlT2#vh24uW!z~ITmO<TI-2%"
    "j`q-sm8q$rvuYfnlsPKHs*{)A*@rj3XDv1qVVF8)cZE@%dXbwslHgY=og(WdpV1tLuWKN>m8y=@9;}QQa`&p8n$5"
    ")a!|Vq^`)SRn-4qrBYKn9a+51cH^`D6yhzT+G}Nqx9z({O5RxojJ)yx|BABMyEsb4qd@eWJ2D`Tx{q2+%NPFC?v?"
    "r=&LXOY25OS}*f8!1dT&;gByP@*z{%jfFtvJxS4UE9oj5QqPKYLWz536trKBhbCB84{n)XQvi*<VNa-W5W$s`{ZR"
    "8P{rft`d%%&7^sreUGXg)bbF%Z^lN<o!;u`;v^!T&gqAft=(fGdMXSt?|zo1F(!-Ov;$e*jnv`jJUclE3ix(Y}wQ"
    "O*ZX^CYq?MI>g4E+vl#!NN_==>^^(8iMkG${1}b+(`Er1DQ-dr+!su$KYa(u*D1ZG;0Jh)?>qPk-ma$!;&q!2K9<"
    "UvE-BWgAlp`E(M5+hD;fO`1($1f$@n+U0b2rTu-4nJ81^ZN2MeX$2tRT}zwSgqb>tYDf92ZOWYuLxIp`t(jR-y~t"
    "WSkopa}yD)xuS<hy;VW^O17Nub?a3EMhq2xv_0OBo*ywAi6D@$Lbt6aOXm>y-PO!-`o!sQW`%V1GxOuXHzx%KH)8"
    "PF$LoBNYa|zQB)`b@#&kc)-FSp1YO67)p4KKBrMg0Wt%;?*tX~<r)`}sOltf>sTu**p95MEw6?_?K1TFX)2$ruH_"
    "DnCq<llp)(sNF4N6cjvDzTD)=r`Foul~Baq%vo)p1rCtRHC8{M1!Y4a@AXoISfhnx1L8aAL35Z>~O53S!DoDY2Tj"
    "slPf{r;+XEUpE@$mzp$GBgDPcc^t&v^bp5hsNw!S=m2tx_b9Kjtoxy%xnJDt)eSSmERtg$tU+vNBm)t1F!a}5Ji4"
    "GQa<*ZN_m5tl(XW3=9cy%zK&WyCb*+7DzI9wVoi77fp!yfT=wWdnGT*<4+S2=rKZK-(@74#?sU9q?$oc(n7%|6bR"
    "b=7wjdG1}(A~Sg#FL|p}+TIuzfthd#N<Y;qALbPQO!ezXX274t)+?*Q)+E0#S9`W*@X{{f<qaWzAb%}}FYtS=gtx"
    "$Ogn(d39P~=Fh=MiGfl%2(%r_Z-k0RP4XShC^f)<LdOfwtde7H!s9UEdHjYh>MH8}7%Wu^tXq~GUd*q7L`)D>+X!"
    "d+$UK@4+E1{S+XDn~%f)blZ-*U9p+V*@A8W;iT?Qw;Nf-gYbZMhzPlJ}Wc2_0F-&7$aiWgWrx{?w;*CBGl>rnZvU"
    "G9ucXGP!^y}Zmx-ZUG+m4zLo2fM-`dA#u-T}?%N0d$ysmue68;eHovoi%%LiWvCCCkb=&Zfqk}=)_M_V!Yl2%C43"
    "*kK?G(6Hl!IbUzyq!;4%otMv~>wb#K`+{lK8w$#RR7jO=@sLfuNJTv%Be?<l&deZ-)o}<F|dcuhyiv62zXJHcM)1"
    "*v1pK#F#*e3n`Y){skVA8?T-+G1O27h!p;j&pJ*G56~c6;JO=Ax6fqVJ`BH2lgkyw=d7-{uSI^fz~bl>rE-}KDEu"
    "Uob3_qo=v8$4VmXV2GKm}O91sK$tUB4G5)zPL^4A*VsO-}1hwbI~3LrL~niO$a2G?pX#^~;?0Y>!<VIdb%>yTCk*"
    "pS;3Rc*%{#N=v~fl9Z`T?TN+6D3wpI!tz@?{bv52h7@*&N^;C@)e_W;8CIy9j%Q#-J$KOnu-SprDM)bWoVykEL3`"
    "mV?PJSI@-oaqTQt4pyZ00-5LQj`dA>05lF88RrE38Xq-jQ%q=>7W%)z|vvl>9Qi6DGC+v@sPhEywiReKM^xQ<`T?"
    "AF>GgU#$YsXhGoDp0r@4wPJR*UQ-!83PUQ-a`(ud`|y^FZCL!Daz>KER(}?w=$-{S)7T1QQ1$n*%W6NoZqSgu#4+"
    "JO+XE4&b-t?S6`&>=gXPS5)Lx@$h}~=7`pas>gC6Jr{Mm&m~OH?pgQinkU&#$M2wVn<P87-=&FaEU0kQca2Dws$h"
    "U-6~*6qzv_AKpd%e?35VHlNvAv3GITwAPX#~5d+?(9{O7%&s!zA;4x22tgSC(1Utbimn&Sp5aM8Wr(LjMMY8+G9j"
    "*xgfZLsc0D4v6h{vRHKi-3)YQ;>;VogGHjxYg7)p4Q&c?(6;2z5P}t0yj;z+sW>!gxgjaKrlVW04US5+n9RLLeFa"
    "huEY>>EO@3KU;GD(DH%gJf>3fr3M7bd7~{R5KxD?)#`}Nw^j9RRb>7>CBg|uA@u8S@l7poYpFlk|#Xh<sC{o-qyX"
    "86OMbjKXFMEe6*jN^X#{4eHu22MAx-MSv%^MFbbR@oeL}OT@_gUkFaRQeVW-KB9OOl?rAU$Kt<6n5%QVD?O8-f?E"
    "lkCk9N_U0{ZRoVufG}IsfsbA)Va!SoF(bk%aiFoAy1+4D^X$gR#}k|m%w4VFAVC&aI8zS(iN+ZFF|wY&fH%dP-T&"
    "D?**`ry+WWN+0`wVH>HK!v9)dm^&vLPf)HovOB*1^YE%TC|kkD*2l#Vh?jmadg8l`!1Q0Sq?^D`f>N+v9AUAu**>"
    "}yCU>&FrfP5qe&w#mCt1AK>e6x1PjBy77XZFR!wkdim>Z>k71qQO$SjvXg^>M>+bJBWA=?s)dUsxzR<2bj>kXmQH"
    "0E~O(iQjoXrK;SzsYVGuTafQkax~Y*iD^|S?I}0p<K8`YS&VizcM>%>s_3}Nnj<J`n(juBV-nqU>EkOK>+(ei;&L"
    "X3j?V0b=NO*m!=21DPbeL>yHs|J)JSbouZ0oXpnM4Oxx-m|O2F1)XLr_!#J>>wAasDB5{C0S_xHUlspz1lGOk?1j"
    "RB8%Y4J)`oeujx!WR9y8K-ILoRz>;r=*_-6RD~-TN<fh|@d8)0=A;-K87ou+ZgVuef>?1aM#Yf;ne*_`EJj8`IQ<"
    "`Ccni&^75=kWkO^CcUZA;Z`Y%Z_#yp}iUPmRca(>weGh@+2pmt8-s}$!e9#Pm3NInyZ<tW389Fs*1txr}{y!t4Dj"
    "n$0t7$bb+{!l|-U0%KznE7b{S|TauWK_J&mmd-Jm5WN`QY3^ztuTux9*sj5NN-<;p)PU15Bq9l?{GFZUgM^xPNY5"
    "#Y_`=j(_HkS@Knv=`8Zp^-nq_vc>rbwOEDy;ZM8>}5w=AcVM&d%2XwpDG(0x6`^-r$-J{cq86P+B`Whymbwr5*QO"
    ">>+mel#a#5zp`!HTj2dU4=O=Tm^ikGF#D3h$`@espk%y}*u5j^M8jIfAkde1*^R#gXy1fA?n8@>V=mCRn{qYF)}r"
    "TVq6Vz)I%N-n(usID^AHVoSSED<R=)HkIr0hM1a53btUv53mg>Z*7`?(OyAkEQKjhG($G6ZW<HWmrbKv#d#p2McZ"
    "Hfg30#mh!Tmy7iRDiXn+Gg`L)*JbMVTC^u~wnTc)UaV~m>rm@VF`SBO`X0dVkGi+@}fjl`+SN&liHlEmlWL`S^1Z"
    "Ci6`kSi+pCMVd)><q_5$4~kw^=P>SHPTsdw3<$q4C!m0E@7Y2bqy1?*^=rV)S-;?(GowK{9RgMxYQ~;{jU5s-&#~"
    "yaGcG?tWP|=hy@B!P}#sE4Riz-a%_ym@%90un7CFNX<Kc&`C4$`6H^bZ3E_fpUOt>P9pXcN>%)uN=;{cjinB)5<1"
    "~$4Q+GZ>pNy4%MXEB2hqy{LCn&?<pF5r(J~tVM4e_ao9u?$@*od)38cz)m!>Qz|^+JKGyf5b&!hYxt<7^>%%-cX}"
    "3R6i#@L%q53~40Jf}cOsNx<qR<BS5)jUYo=#mokqc;K#iz?u{|^bW)2$w9{KnSQv=K5)qSM#qzB7mdPFu0r=6HDe"
    "qLJN`Kq@?46Xgv74dCnCb!Yp2Mwk-Z{1s1c7Ex5+RcjI%`^a1nVpwh2TFBe<NAnE@%AHai-AF&*P+F&}_?s2X<%z"
    "F`$Lu`MK@rI%ZF5|U9!hC)UvO#1k&Z@sN!?%XHEv`ti7v}p=qhhM-$@CcwGj?Fy$TG-@uBlHcGpZ&$`Ce|0=EpnT"
    "xff?Sw?dlju+o=L;Dk!U+u#ec*`EWyBT`N0vL({02N=1>k@K5MS!q7E5Nuco|ww>t>gIpPKxfPi3Q-Nf$-?W|JTC"
    "|z6x(O;RA@~tyUbeU)L+XMx%jEb54(pU5SuE?}A~9&+PPK~5&_ruYxt5lgE5%Zaxh)D^Batn$+52QQHvqFSRnknd"
    "E;e(`kzfjQ-U&tJnSMT3x;A=5eavS4X<$uLG!X0A#;K08Vp4w5y(+T+0-E8Y7NKb?JJCZCrQVN8#XkE5#Dqb_$cV"
    "slm{)_OpglzmD=&_6o1X-?(J|gT_U%b_Ba_ORpHVUu2%N~qs4~Ep@g75HTv?!OWYA=gDWep(cn){Jr3}<l)i!G=+"
    "-Rib<>rFVcNPAfFl}c+F^(#F1Y!}}nR)wqrI}e{(lP7u*!5F%hL_1h;0SoeD8UM45+%>W#?yi07kDkQmuWTBSopU"
    "kTWd`qn5@>$dMmoWQZ*6vrE~q?K{7m?1-=c^4Aw4|Mk8m#f2~R~@hGr?K+hl-(^x1X+ZS=FFyy{QfA*Zw694Q-Rk"
    "GTiRCONlP^-qqp3R=q<)bR^6Z@v5kMcY36j1cF9IfH`bsVd*E6mp9o_^F(Z@yb}*^w9^1X4e@#4*W3^;tT+)x=F3"
    "d=p##v(S~Of%G7nmFUi5L?gWIOo}UL5&2iT^vVfYwQEusd>PPe0TF(z@D|E$f$y<aI9n^49j`9O#lXcdz0Sv=*>L"
    "tzX#<+sVGw$n)frvtvA~NC<;oWc0~aEdF-;o-hO$KPoK1>)pbloF!aJTsCQGg4>iHNg6&%l$H{2+AKrQKN+*2By6"
    "-9#z+*LEuUVMW8E^|qdv{MNwwcIhKO>MK~b4e*mjt=*|>@byu_c1y^)fwQ4m=!(D5p^-=uq-00`fT8*$$Yj%+)tM"
    "6QX5xp_dsf+zSwU9PX}phS@Q0u{htpGlY=*J_Fo?Cp6$QGO?yQzbu!3|x25cmZ!KF;DRqV7Eb$`F-Kiqq#mQSY4y"
    "Adx00Wv*Ps(@bAo4TeU<Xk|1tq)9vr?R5;<iFT9^Xa3lH(Ndu{4zCBiXlS$<8yG%12wZ!bExLG8{OB1&;KN!*2uQ"
    "C#8@W7iaq&;o`7FUcU1(BXDS(_+Vmw4cjt4Jzl{V#ueyz=a&TvF%FtShF31ZJ7S#fB+oDr9uD>8g7UP7o>S5wte_"
    "ujhyo=R{i*6Wei4JaWDGKdGi9q^ZIU|ZU1C~cf-Wf`U!4g$**$zoWH%p#`V}8gjW38C@vbxWf#n$}xKu*LqJont;"
    "wMuUWi67I=$Zr`J#yp<eHLz9g^d(zfH~BdRD^Yp&@6z_Ot)d-j=v<<n)d48<n%0c{jbF5$0Tr-6*s8~qVv43y@>C"
    "BQ0L(f2<P`3-hJ409pA5E`aUB5`gF04L?>~9HRn_4U*AMBD<V6rBHpdpQq^1?7dY~8|L5JagWvbN8m9}wOIeMe0#"
    "0_hx-m$=_aMR_k>=5W8&Dr3jsM%CU9vvOKi;6BHd<KKg%jJA@z+*lsstB#`qa8-B&NN(G1fg;Q7gL6Nm}=C5cS#("
    "j%)qnxAC9u0h)mRDwDO@%oR7<rQUIs%n3TIo*S)?uqNu!eE8RnW?epnPYCid{*VtJwv!luhIo5@b9}s6%Vv^pP|a"
    "e)B>GtF++CIXO>eB)Qcic-=y%%Ocizy7Z|^@*#~Zv5zjcv(cTU{6^KlAI{@&eM@$PJxD^h*cZ6$Sg1L2g@Cn@pD;"
    "!2R%8TLj}D7j53&B_xgT*M4kPiAsAp~H+M_F@@!xR_yJG^KtCa2kukuYNUyiVCh_Kdb2$3?*N15}l-}8F|_`48Hg"
    "-6cLoK!3LV9dZ1E9v!@j7G>OCX*tM_0;JL?*YD6IzaXdw$k|t4G=Q9+F<Lx%M1S6%$YFe6P^-fXFK%JRn%U10q?s"
    "$~$j_u<Sz)Nw{WsVoQF_`a88Jn7{MND$XKl~ypw0yYXtY05}fO%~xn-HjFGkBptT-o{pMeDwJFBRx*U&Z3v;11f="
    "ru7yuUoNP(@b2B5oRi7cB&m74Lyx~hGeJ2QpB(NpxT?zg7Foy^SMzLvl+Z#8H>Gqj&z9F%!$E#HhL5KE#u4fhUhY"
    "#Gi7&4yTi_>pa9>Bxch;PTbZo&CK6Gs+m2ZO!@{nk*7^I`~?(9m9v19rL1*5AT6`HG`pHUjQw@x+$#x30dGu_%+%"
    "x1J*vFKJ0>4u5Aqii)^(kEzxRZbO+Z*>Xdak_#p_*2;$BG?86UQI|INlnQ&%}$aY=s|wUjoYgE-AIO}2@JoqqoDu"
    "blu9D5v;j&$6L%r-*Rq4Nb;6JED;Y4CK+@54T>x4XwnlCSLho}V{{UXu8D6$;JvH4t?Cr1KXFt_0`ly`pZ7<o5TX"
    "ve<Wg$jheL4!fu98_-pGj(_@)=ppLwF4aMkzEde<`2v2QyXr!5aqrY-Va_Ne3N^+oItPSOKkvvLCY|?0z}DDVO<V"
    "|5LGS(Xj$X(81L|-|1f9UfqnhN$nv59z{#E$Ky_NLO#ma=Z=v<<@IdNUL1j_PDa@EP-_^WuYj3XSVD(UYvfqollg"
    "%Hj~p&uab{t8BErs?535z71zO;Ilktv!*qz>_$!R_wnQ_de8jiMjg*kgtTv&}+v&CjiwZk4J>FIE`Yic8I^03yfG"
    "R)jKHBRN1J@}`#Tn*mLSZYveKiQHpC<Ortj%VXyaPyVw?ljcWvE`soaTDy}7HK)OP;tkFdxsNFbZ=edz3ns^=e?b"
    "6!Yyn^3Sl%gmeL-<>b3AQ@My{WZ`+C=Qnj<sFJOjgDu3WU@x?f)-z=bDKk{dtNDObxgMl><&aZFEVn6^)cud^z6+"
    "DxxprWNya>OO?%Y0nm@jbGqEJkOF*(KUxB@_KlHX?h(l%QBa5`?*{<#q4Ly~s&<l6~jcZ$L~Q9mXHx_*(L<;ss&)"
    "*1XkjZ$e$^X~=Y;q+G@VH{HER<S<kkaoy+jM5hXqKO;OyjMh|xv3`>(ut5pTid4xtuR&e=?Y8^s6JgiKaQntyZrr"
    "l{d_Ego`%4RgA}rPvR_%YCXIrD~tsgEvKYeohS1VmGGr!|g4lY?Y8G#7yOk{}@p|t9LF&)A6HtkWBMwLShfRf{Vw"
    "JhVpLOb(1xy>S5|3XuYajRb80(no^b#wFMXVXz}1(y&Cbj)H~Ax!;Hice^ku+NKi-RT43(|NzP^zrt+vTPqECSi&"
    "hyAHB{S<o(4rEUo_K)&p;*^tN5!Q2Nj*tMJUqN=5hYUYsY7U@X_&_Fm97S6^EC*RZGUUI`4!Hv3UJ!-F=t&!U}ie"
    ">wv8Fia%S%~M)07M|fV2_l@fVu|<3YtsTOlRY9&pBT+7&W2sV`<cNV?D-D^b$Sl&ix<~7XjOb@ov-_r=mj^y4WF4"
    "M>8}>^9E2UZ{SF|@|`Rg#UzbpnnPd+kh)*Xaz>-qf(pl`cfZ21!MN;<R^u^2YeBy*Kf!$~5BtwiMPwR5wIFi4dG)"
    "o9u?ne^e3_w?W2Un1%-a3#Q?1A25w&fa&0%XTYsmigfePD?wPg({^=DJqn$viK+P5BYf=4v5OHzT(FPa+L#m2V!s"
    "o??L2H2ecu33cYw#LGh1%eUsb~U90C<kaVU*6Oo!n=egREu!mhv~5FTsge~8s{SUdW^xbkVS=@DnS|Pj08v#^@XI"
    "856*y)m|rS;KV%el12j82Ne+HKJUS7q@}}#^8olBFV)%f;-4rmS8uYSyFWcrfWlZOHN+v82u@koT4sjjAI>*~=n="
    "|m%j(fv}3puwW%?uHwlZ4WuWDzek6AVQ0Q^AFI7|VH~#PSKvj`>gpIl_DL;Y}LF5G5(~oi=V|li<|b@ppCIU7@yG"
    "DggDsXHYF2I4ALWq69G=`Psi9U=nBo?I5FoMMr2+wA?xQaP1C;8uyp^r)7&4)9-q7HfAs(g(l{<w&9S4If=t?1#M"
    "=KBOmE<imkXWyDAp*s8&MWK;7WdlAj-?PL?AFKZ+5QbpLK(3rN+U!IbsY2HZDkB|36<YVhVv8l(6#_#GXrsfkKrx"
    "dBPFtwE7RWdV)E4*gV83ATJ13|m_3!TQ6cY;CleoUOxhGCt)iPmty$Jn2{!vh`#%Y-L!CMtB|AbW5{GYi<Iv<R#U"
    "&iumGC%Lp<fu1fE)Y80z_pPh+xEB%qDNUVEQN(0wS@epk`3nkt3b;;>X8;GH9J72H~hfx(S{g+myOlcd8?QhA>y@"
    "XJqT~&Cjp?^$#R53IdxrY#dCi8mna0B`C4rFW)6#XGKJ++Cv8)zFkp_JT8{<T0?y8MpVhiFULXu)(GH74!~cP|mE"
    "1_%U`a2*K>iZC?`(kQ6LXO<G*ZC6B3iG#u>MCH%QNDD=TR2Qt^LyB+bw$fAlz2{zk7oj@0xk?xBui90-9r?)feA>"
    "|5;3ViB1f<yA+uJ`Tgb|$k$^L%_9*>`H*U8z@gNq`Dsf(qXK?dN7(`u~mc(ziPrgl-7q_DQGgHU%9dI4LFl&ju^9"
    "s`ifWQTPJhC#!BJ)E&7=Iyo%&NRn}Io||uXv%cD<|O#Njk77pW^m{TCZ-z(t!*^;yG%d=b*$M^LE0*99Cu+i7E8z"
    "aL6?r7k3pA40OcalmyXMEy=yZJ7c?NcjM7>UG|ZE+X4Jab1bdC<r6zTMVq#0@7~2Y4F*9?yUj#UJM6a|bnB1QB@U"
    "EMXYv-jYxlL{@Af8){>H|8~?<ra@vX6b-tli}DW|`|IW{f>o(!RS0{{Ojzttzn05bw(;&!6;no;^eMC;rz?d7VA^"
    "_PK4<xz0ZcrY7A&LW;)QRUOXO1Z2TA#S;fVeJFASV#T*Gv282|e%13FApyT-7<4m81Cv1N>RO%m(MC3#nmk@?80f"
    "4xhEB-9zEFLwzG-t6mgr~7x@dXs#J4+JYA*`H%DKNLrR&`%YzNk&Sa_8P=Lmh)B%BvvWF38VE;k8pLZQB(rn0e4X"
    "l85=8(M74j#V|!q%I>!l|#VQIO?<g?1a`3f5W5?7EO#?p|NSHe~IbDta^BB=|F@NaU>$3tAMtR=oM6u2mfhdg(rH"
    "{x&N@m)92gUYvf{y>u@7F6mOOtDf(v2ZmEjNR?~^wI;0YTnMlf<uSfr;!ufjqpHTJh)gQB}R`j`g(JkzKrQ<wzMH"
    "i(zgNhO$&u2`?!>72YgL~C=3J_<?R(tIYXIB#idYXg1rPVA?FKk{KEvT%n(i?w~s7NDyZN|?9dgBW<XP-#9nm8-7"
    "@Wog7WOCeLUXLQb+l+uY%L*5Md03xhj946og{~J5?%^e<2+y(2;}7Ki2dQ4U5Gl@EDOgBc3pEBS>+uVraarKcEPT"
    "2m<lW>)==3%S#*jT|ny}`N@8c@bfzDc8bAhAR@Me5+lcnB38#7utp@wWJ)I$v&qZ^xw!4c+&P*2J=bPcq{26TK>>"
    "n*zVw>RGwBVuIIFTGruLpWuF>uBhNW)a&<H33WT@yR3^S`PKDie;%rqmo>&b1@x^S3^fSsCCZO+cVrbIr(9c>JD&"
    "mIJpFM%JOWn#IiSKkFUuxpJyxq_gZL(r0cY6qjlZ?8H2ymV~{nl8JP?jv?Jfzs%6&3Gjz*gm4OJQjEkctIcx9e@Y"
    "TV|8-hpm*j+S_=;i)v5GGDGY;7$eUGGzvcSJi+>Pr|H%1BbQ<E&`~AfR<d8rO@n8PQd!AOS8zC8-4ZgN86$mE#*q"
    "a~iKoL<Uo^PmkvJJ=U(a9FEjsHHk?0wz)$*j{7Z!QSwF3i`%aU*%Pt5Ic-e<U9_>^P!xB2CLCS<eup9^a?~xB);N"
    "`b#Lyqjv7~U5Vv-p`>#T}l2mkptAQt^_xcg@R^mun~zyI6GYe#V2(pwYQLGsNS1&nmqdzbjK+XY9AiDc||Ps^NCh"
    "!o4c&X=jAjir1JQq~nxrCc>(_3Z=Ki=I3TXZA3Cc))SDpcCc`*Uztq;2}Kt@a56rKK*gJe|YvVRx7+}lyTP}o-Vm"
    "DnIn%o@>5MATk14-qOx>GFPxwT7eAb9o`}Dz-~`0gye2)5%j_j91|N%5%8iE~_!qjl%e$3R?KBc0C}RD;e`a(gz#"
    "CJfc~|uwp6vgA^y~i1hp@js%--k2-cFj$(J~9G2@6(?d)phNM)w*LqaB%MO=fgO0;;-0Y6Ky3xAu~#ED&6$)4^<L"
    "0a7I&(L~MPS8Rx`WNgXrxQub;p(146Q^;8GIAXe;nH!rnQpRsE9EPRArWANDK1ctrUBBk_XadgqHZ)qpPlAPPXc1"
    "T;tL}H;LNM*OQ{qR`U%SJ9wA!Avvf(vK;EIOp{7_YG8#-)ec}A<N1QXl=tKqKVNv&2PDDl0d)hs{8jrkFIk978?="
    "Lnm)<w>#xUF^((Y8*wx9W7?(h|KNAY~Z_r#x(KTzo#-;`s+^Ib}grEiIfo0iZCqKF5Oy$j!lU8RrpzLc%YMFQQ<p"
    "(9M6f0ybbNy!gyDf(DXoH7rNhB#ygZU8d<VK?~iAlskuPE0yGlsY92lOStm)MEZ+-ZSswmXlc7lP{HsZof{$&Ba8"
    "kGTX{sHQ!pR?Pg|Rh1H-j+UTevSZV@UV#4oqzu=W}$JAoqEFuy@u%#D|whiO?0PSrzMbsC;kqwo@{;%BTDjnO%k*"
    "=gYL(2SE<YBNNQ4u8gzeG)Yab&X*BQKpcyV%EC{wCAhtL`SR%+K1ynxE3xkF9`5bGevLBg0K-qlW8$M%`BaSaJ^S"
    "Z3I}uudK$b6hhrhjkowDh)qz}5!_%=H@Oj;lu@4oye=uIcT9UdMW{tSQp^!jKI#pSk#k@{sb)G8S`NmcK94}UxS_"
    "3-E)hYuqgf(L4JXd3GA{^3g=;;H;~mmxM@U-fs@+Q9H?zl`mM&@u&EUGWXsVv=((uv=IgVPLF6$AMI3c2gP*L@o+"
    "Ij$F>5L(mhgPD~yq(&{>Hr+Zk^n*r0XjyP#{)E7FqGtwBXZ<+j_94i32VqRX;Fv``!1<Dh(y{sDN*w`LG-Zq<->f"
    "xW{H5HRnR*Y{D<OjHlw2ZUf!7Ll+<sffOSL1OpYF!rapXpU!tqu<#w$%brNp7Gs*d&+8ga6U1S{=g2oF%@kxJ!&T"
    "!41=BqlZMPyx!=~`$1NXP@^$HUX1uMYtx;#<%Zdfz%9ETo5zon@1H+2Ntou6mGz)#v*_4p2r5jw6C!b1>F#ER(k9"
    "02#~{<Qx7}`k335@rsD-=73<c)z;t!FqmDqve&wq%h%zGFa0TQ53cTSH9Milv`PMjcZikn-CSrrSO<CK@1zIuW{z"
    "V>!(kD+T|YIVW|Em?=gk@Avug4IbAk3@HqC92f;7s!A_jA{M}XtRO~JNwkq54tL@g4q7T3#b~nj<1)1i)s*iAOtw"
    "R?=Z&iBCV>Z_ZJP~a+V(}vVp=7j~<bzkJJm1NR#HtIg3y;Ee}h|AII>r8j7g1(gAc9YTB$!<8$21ikK6KE?1+SMB"
    "^eiG{Xk5GF>HEgT2@G9u26hiwtd~dK5rSjA30rf;$eQX9Z<?*F3Kom+Krh6JfT53U<XZbDMsFyrr>bc=9;bz_6;q"
    "6^-r~A4G}sX#<672(mHWRW|&9QqvH$_Q}ixggKh#RPr`MFud7l1otk;bAx=EEegbm&liKD6wxawi%*Gml}vKXZ!5"
    "~l-N9ejrwWtDQ>kr!JKIammwakr5trEpSXdRXl+|)J@xZJ8fkEsqbDRs_0Blq3+jc1yC_>I%(<3fC@b&-`Wdb(}{"
    "GKWW`xHeB%Ya8g9;xjR*1DK_gCy8SBkDmvR~X8<=wHKKS<_81G&n5`C0N(4oQ=JA9q1R0z%dipE*KuCcszK);=th"
    "hO9Yj_CwN%&vE^(wHj_Dn4=Me-$KfDOtS>B-Zo(EKUv+6SM2oziXnG!b?_E~$0_#N%3AKk%XpxYpt6ic_nvW5c8R"
    "X3CVh9(aR{^1l!PUVO=$3=QHRTLU*~+aa+fSaS$q#ArE$r%lWAc3u_PRzlX-PnIia;01W2_cv>jVa^I+ORqV!_Dc"
    "{n>jr#emg(=q6ZNH<hXY<$^$_`uMK0*D@V@UY}{cB&P&!ys`(Y_3wO&LjPwcx(V21hSJ*G2e<B{aI#2*$i{?t6+C"
    "@#`1?Kx1}FdQpB??We;7PV+8r<{+6n%H6ejD$H<{-&derQ1v`Qnt?EGt1ObOTvZD}367V_I3e}IjL4(!{v57?Up-"
    "#HQ3QXHezHV`=)lGJl|q(j$p|BAszt?HOLzCIfYF3=dnjd4k0B3={l75v=}uPf;bwkF8MVQ>7c^oPJ^O}+WmU`#S"
    "H=3YxdBmJ)BjuX3N;e97~lzelhA3ncElXmJM+ZUKGTec4k|7>@rRK46hE}S`ljK?1=$V14+TW<U{V#=j{PgHINdB"
    "C{O$hl?j`L;m^?cw&O_*FY~Dmc_9p0n)1!S;wao%KhUnBUXeqxyblcY6b|-;cA&<uFV76rk1hZ>pA&40w&N^K87l"
    "rq%ZoQ@-~Ol6Hxs!b$5zRmp{c3E`ydS<<{Wx`G1I%eOYWl#C=}y8b943eS*30epm*4R6+8^L)-l4G^s53Ri!cV|`"
    "I~<nRngRSSM%k1Cx2r!U6iOkwiF=0-T<XAU$3*)JSbeGa!PKk~c00As%4KDu5e%hhGsG%%XV1S6CdTA2@Ka|w$(S"
    "vx?j#*4w!(-I9~c+-^02Uu{fmsC5@6MhW8kf3y@wd*VJ#gmpE1-q=Nzi=j#!bmYq8`<fmy5%UY9b>o|{Ggju6vRC"
    "f-zn?#!YpxR1vGm_yKAG@@ril|J=3XwAE><63#73KEzGXR+peFb{NGD==aT@2$T{IRD(yRhnt6kEr)Ml#E-lyD*<"
    "SzbrFk~_#)`u&?c#|sHxZ8_j2cINjIR1-W0G1n8+W+TKy|t-I-1T5MOoA&D%&F|0GkQpd=@2YAe18weGJhE(rfK>"
    "fPrs!3^B|b8g_8xrEbE@-t}yN;)G+^2KB|yil^gRj6oCci9+9{fLgDSGt6xqCX6-Mr!)Zcq4q?&j@)2xAAIo1!GK"
    "C!QWoAmUJd9*_|Fv@SYo6x>*KwfF6=%jd|p(*h<OeHtm!S?`)vQFi~82N;d`I$-?yFx8oPo^h+yGu7a%L>m$yN%z"
    "Z}!}sN_dberK!2An$!Aha3AwE+N0SD`O~ElSzhT?tRA82a*BdIf^uJ1whk5Fe>)_Fl+_}p|EV}a_O*Oo{>kp$!GK"
    "TZN)rfm!Mia)XEFche#S7HYePYx=J=^4(py{@h(pLODoo1L(u9wTrCuV3J2LjRMO8}Y0>%WcI(H_e5Ac^V|7pYSa"
    "tPI<JHlv4$D*K6GCO}ebz5QZtUo{eVJseET08J4giA(=rL;f<`-VJjcp{Pg}Szp*Kn{NqFT7b%&{pJdm6Cx!n!I2"
    "UWmzrEKX^%Dz%C=h^Aw>yM|Z!;=bUx42B!WxvfRG{V6N+H$0d<0ziCOplOFt8*2?FcLa!K^BU1u9(bdc5PJ0){G!"
    "_Xc-)}x_kktMQQ$Q%md_YixKDOC)ZEVq+Vt&oZ})8X_0i9kF<_MUufJ{mzI%A^`t`0S&f$kAY4Sb%`>o-+(thukq"
    "rIcoyJ!0<X9~Z^k2~-XsOwL+!-r1KPImwC)BefHKl!QC<s$nC7Y!?8JEYz}`R-eM$^-UvusmC4aa39p{|PM=Ov|n"
    "qh&<3gaChKOmjwZj`=|l|5U+hl1Us~RzY3sWi>X4v!oVG1*qs2C^yMNOEp6ZatF(KKoC%;#mkM>-w^*lWz$tUk@$"
    "u5~u&u~`<5UUYGjqV`a&WUGGjjVba^QUA3udPw;Z#VC0>!1Kl+AoeaQB|=<}RsZCPW8syOg`eDvao0o{cF&r6i3<"
    "Hf8rKy8g60af=2JtK4;`A|o4B`e>@krFDg9IBy@2q7EOKGSLD-Ts96J1BEFy0AGK*z5VqHReceO9ZO2=p;m}DuW?"
    "8o<a=FJwe7}AFw}K*KRIjRQT(?3RRW)a`EOV)u0DO?A@;B(g+Ctx>w`nS9i4Q`pP5_3O&%wEUf`QE+yd@fb4^qbd"
    ">@%oJ{3efdzEx8gf)UAaCA$n-*s6tJwg>Me6R)&*_Epm1lB%mPY8pxAtakrck!Y~3M$T1m}t1d2EyT=?hZ5oBdx}"
    "`5)^wWo{z2-81SrP!p$H4)ztrb*sg)hOlIQdig(}8HC9w;_h?4s#ILEX)Nv!ac8`xwj(*43F%u`1noz6sp@|BH;i"
    "g<88(z<vV!ZnRUZs%9wEo_E_z+J94X=k$e+s-p-_)F6tsSL>x$2MSMKoJ2C_$k?NWfU(W+eOq*ku?_P<{D!YLdI0"
    "U4Tz)C1K?>P{y^bqSbiKM3=m%9leUtXjq=wGi1QDvCv325I^eiPBax+>JOptOqEJ-V^Dr8ALGrC8{~#WlfZ1Xl;U"
    "RafnuOgoddaDdh~%C?p|(597ME*^kNR8U6Yp1#I59a-;zkluQ^wnGQGx-C&D`DvM9_~QM%fqWYt*7biP{5ki*|AD"
    "G=SHQjv*?g4vJfk^BFm(kCNK3~qRMKmT;>jqBFkUPBZ)WpDZ7XY<}-;jc#lIjvTZ_wDd~R~~P-ZML-}xc7R7GVPQ"
    "L82S5`UgPA#Qfp<Pw3D%gdz#lr!_l0L9L=I_4j;#C!xnfB;He-Df5;QBDi>8a@HY8>u4YRY_AwCKQ2^<gIj-GXj~"
    "-Efl_j<D@?D<>m6lHAaiwwch=;pL>Wv>w@$zK%)meNSv3l;^)V?y=szzSx{)ily6XOg+|IuKEg}fD;8QGX`AmC-U"
    "i%Ae28K}6zJgS+A&W;RzvBOHMrtS@<Ww}CSQm<#T_sMFWWI8V5m<k2}v%=*tN)DXZgjS_GdVg~TKN`fBdkvqCh2B"
    "$@8SIhw4<^8;hm<=*bvZpVT@ErqSaNofLxfE+)#J<RynNmh{7A2iOzOfjKv@yAMO!je7q{cw#vjO{N*jfIJH?cDa"
    "N7}snG|f%YKdc~l$vW|e7VpN2&umoL_(mYG(jr|tZ2C!4B(;BYAnRlV9D}@L~2j7#lobk6Smj_=sU?_hkGhDIr;s"
    "dYBXb801o*yT1^Ln$#bq6WFQ^MtZ@1|LB9cZ<@_q(qGU&+$WOe9&ov)k^h}<xTPuX{zt2f~gMThi*7|&FJ(`hG_y"
    "UZ4i<jUG!ygFwK;3kd!;d7P!P%x}kb)V&&v^U0YCu>PQx7E7Oa61NWcwQN=lQ4ve!7@YZT3C@V_o}t!gj%8ZMLs-"
    "bWOmw-cpi!Ys;v!UJ1`pOL;rP8m8WN_C5)I@UD;c9gtQ<(XN3v-NAr$G)&_yh=1=Wifo7?tRsu#2TM!Cd7!77ewY"
    "-Ey$H4b7U{wzi4~`0Cy_*TC)6E2_wJq=XM^`;qF8&*4F)eq{?B6z(mzhnYc*J*g9C#Eg`LO@DL#X~7ql5=w;f`Q<"
    "Lrhi&$<1fydz9Xd6K<BPk;UGg}tOu)*p>gCucX1)JIU8yW^V1?#^ME@vOJPt!eS+aLB?hDngM(>_Brr3l|Sw`n<D"
    "i&Vex=R^LXc2$VP7;&*ATpSxz`>@pwwneWscTp8#$$jU)cc;%MNz&h;v$H1qp<TLei+f6>}FmB1So+fWs+uPaG&$"
    "8VfKgP{}+tJVe7k=z+KN;TQ!gtJ)(@7NkFlmZ2?VD4Mk~U9Dk)YZR(VVfJVNYEh2KQ@5!5`}eAq(QU;;4JiaDBvn"
    "nbYgpoDA;XWw?tHG)X<^o{}4nO34m#yzNuI@uZISYy^{<Uajy}KorXbvKLCmQ+e|Mu~0bt4tBl-HlS3~Wv8qPk9;"
    "`FYgm4~R|x73L(PIxiqt3NRiRj5ZC@mojb~Wu2=#f^ct^!2^d-@6ba+rf_~q>En5Wfo=k2Olnrq>rgy-XtBh%DK8"
    "BPmv6W9Ix$Zc9oa?sSJjF|hD>{B0pn6H-o<?KCdaPlIkmmDP;<5KFnjN%AOR{F?bRKF5wfC*+L<9XwMu`DTi<z`G"
    "V+&*q**fJyEE*e}~1^a{3g#5wz6ofyF2Q?BG>5CKR?x!qxjtpws8nbR1k~c<R8}7yJU)d~wxRS>?4X%3;eJe{G7n"
    "SrZ_l4bP!D~ZN$z^J(tFA=>1t$0nC7E8J93@(3x9oks^|M+eSjT-o1?=pEDeC0zb>xt42vxwEeDFk6+E9TLNz0X8"
    "szx(2ySVEC<~)-7aO-n%TbsKs)M!#lOaPXpQN3TqSYllJL)z5dRk`D4!1|}F_QCqL5yRm|9jisLW)ipS0WJ){j6v"
    "43XOOl<JC08gnm)H8rq6Gx0|h~A6FOG$7q}E;3>PnY!06xhnzI;n2+&cOk5{FsZRs0-D4?cf@yIxnUeuVur?Vs*a"
    "!PMDc0@H&kvk1JpwyJO*UUMEv{JJqxWBMkG3gxc39oV~?s6S}!hp`fY&9OzGxG(4{BUA0J^w;4Tl$KW=N#qRvg3)"
    "VMr6Zq@S#?D2C)eKHm;A0TQYgTt&CqgN(cTze<UPj)2xT&*P$s~RAfbW_$S_K(Gy(-vWbW=`t9M&nkL|88s<Eq4I"
    "^1hf|?u6az>WK35n_;B4BV!LXj9<DwwDchcp8(j0Mic7G~qK?D2<Gdaf()JeZBgY^4X`@zTV&AT!6o+DxL1q`ur1"
    "EiO^vUmHAghkDO}Imk1}q@kBG9`a%b=jM~;pRgEV;BQNVyzaV0C;YchBBAvC8bkF<PG`dJ|M-f~n??w6Ow!j63S#"
    "@1(5=1#08+6VP_?s%0)C}LK)4v4Q{RfIVE@&29{RtS;lk1Z64p21ip>}<Loxm`h-+kaC~VEUW}Ba%U!>F+^;ZtG?"
    "wY6Sog#ctUlkM@LlxdXUguMRi#8F17L|=K&t23_TnBPF%)%5XGJSsucD!`KZZrWv>;2ujUlsI>BcCWusZ$IC^mwP"
    "(AKgUc0LI&hIuG2Amar9AolAJxdmnb*D02}fUDY&(r5towS=Pl7RME1;WkF3yQkQ0e-BEQF;Wa94)cSIP1}4c=GB"
    "53m^g;!vBhZYC7+Nsx#&8P@ct}GyP$eVUw^Q+G$;!DwI|J#z4#TM@Hj}VQ2G-bYf@|`i<r^^S1Y*X8l=y}Kzncc8"
    "<Yx%Nn!u(AFxn@CY7f2IH7oR&<X}p*BL-B^HoLl7<X7bPP%IQsy0Q;aa8=RbO(Ar=r8@DRtNU0Tjd%2rOXx<^5f@"
    "0bq~&jr8gIFW$AZ$fj7w@jNpy&WVRC>7e~=iFw-0Ws2dRkzM7Tixxv88PB@YJc6Bc4{44k?L-hQm$M{l?-$m$Agx"
    ")>LN$(v!Y^OE6D2l)d3!eSO=5JBcLVAFqcEc#GVEMLU>#Vo4~gg~4{zTk?N{}L$ZEA0OACK>UCf<~2(ohZbdv#TU"
    "z>c7rKp$DT!p!We1wrnu<EGHZ8wJ^3va~Tx(>MjJZ55>@Zg2NP_t$&0#K>%+bLB-;%Dy4&hG#b1v{@D&ga;*?=*y"
    "vP_3H(HHpZWHkt(Jq?Bs7J`<DNpB@DcSu@cj>qAuDL~f!7DVNaYK@3yogZ3Ee{BvbvXVH}tUkgV?3}FB_X01Ks4Y"
    "+==ec<Zr&d;IlV^d>k1AZ>`O^l{cuUSwMXtLT@<saI$CP5136?T1x@qW|by-wNqmjIJzX(;mLl+%cAhU6cPYifi)"
    "R<+ZL^QljXofeOZ7R5bBql{y22%23r}({9ra=ga?M}c9Ku?kDOkLMsrgGh6LX`uA$^*_ToMU{|cZZ$Sl#}|8(e5>"
    "8Jq{MA~u2KYpPn8o^oUVG5X`zixd91Pq6-*LFz%>Wb3kD<A}{*LC6qV4{wmayRA1e|7^ED*7DdmzP~pUgKTgSuxV"
    "fXaO1}Z-R)vMKP;=@ndjgfUjYuNvG2xzhS#k+2SeSF!&GPdOVw!1N4Bmj=yur!xU6Wq6NYZ3`qX77C{_Sx@M1G(2"
    "?v)kWzQHQ*WX@_k)j;Fp>btie3{3tT}l3df${X@`a&$1X4b_$CXweM~UX11u+i~IB+(ZWJng`iezE{*~qDjmt@0i"
    "zC=-MN&!F_AC;{#A4}3W#^Xe86HGv!=IC(gkW;3_cq5EXfCsM@*#x1+iF45mxH^E}@^RJEQBgG$zAZVzvX~d_8QP"
    "#k;JScWQz~%46f$8wCUdg_u{_7I!y<bVf<wG)O|nn)NAF3M)1wE7o+Q`LQz8j{#)?LC5i2jQ+{O1$NNbf*e&x<Z<"
    "Ihj(erA=kx)61}ZJ=eUhAF#=#a4DpG^m-%QG1a<x&{sNE{RU}!iU}z23D|HvkzH89J^0CNkg>)53f=>Q8?E%4`Fr"
    "z@DWXf5M^PlT3QcQ%{X+rk=mOp_>KUvD`2b$ce)h7QWljd+>b2mD5a6`JYokm@PRG3?iR3&(;+HZ!L&)f+~AxUoT"
    "lc3CPwIv$(&a?remO}3=!<XQD+(z?x>c*3CM74>(i7Ol7n_AUX&Vd$2r}b%=JlZu0Tzym9^1KxpBihH=Ya@z+qfj"
    "V6P>L*uM~#WicQXf+2%(xD0a3<;$d0#r-GCg7KQkvV1`;xfI?;bK7H?n`LJ$>hl6Fe`o`8hbb^v!s#r=WAYtRJ8O"
    "=(_q13A*z8*1w%)|jdbZtYckw7ti-+$hhNP%;Q2I0VLM!xf$WyMPPlSu0*4@3&FjW8ol}FDrBkPjWHcjN9nB2{}e"
    "vHDzvr*hlS)(Mb_eCbMPE%6LLZB=)%cc6rrh1dTgE2&(tUq^>Tz59KO5qK}<NS}_L$WtKOkN+nIe;FjS&>H4O*cp"
    "xG9$-hV{~(;`d-|Tu3j-mGYw3UsjFG_oWI*am=}iqRZ=lc4qT7<s3gP%314eRYeGmVvYB3|p=wsNKW2{=hnad#tL"
    "Y3cQOtSCM<dNG6KHApZEl3&z+8!{w03llgrh(ciOn-&9z{$m0Yx*D#=;NC&EkjA56;r~+$}QgJ5gGGT#^%lMEN!@"
    "B5Hdh8B*djWWeVf$Z=64I7R}D%@R>I(}WzlZZ=Z@t3iP-l~g7hqh(4q^{STvzp6n;kj-yW-hzZB#Z9ijAa6t{=8("
    "OO(|qq>@HT3(Tb?U2s3_YA_9yR*x`?IEb>nQ#7QA~pSZ!KZ#nD;&U~@8IUB+0&CtLfBCS<HHNn;(D-HlwDw;@||f"
    "{w|cP9aPqNg_%8bRb4pbSqHP#a_)Mxu}0fy-~R_6>GDUEZgc>0=38`X;mI&2`|L>(vW?%Q5Kfbzct@{?RjlS@Rxw"
    "@PNJ4eEt{{!q?b?O)oe|OYkRK_@cfaxxEeN}CXbwcV_PXYvgCg!>oUunZW|KUH2~S;wyHiUmR?nVa!f_*X%{h4bQ"
    "^_7W@LT2Kw2KZ<#&g|XFaZat?|gkch?Eyizje0hS6<W%Q{2hw62}4gkxIUuj)A)70bgXg7SIw#tbK&L>D+Lq-d+^"
    ")mS^$)Y`kP-&5<e>mq9|rM4UiR-W_nmJth6P*^eOEg-?f@q&0~Gx*NXB=p9i!Cma`X{;b$-V^vsgR{EvEJC<8l(u"
    "w-_td3v_j3@Y;l^eBG`uKil$57f_ik-t3xC89mP}Ke6;9m`%z@-Pf0OF0;<4zss1X8vss#<nYH{@D`1L;5zYga_I"
    "Usdax!qjVcqF>BW97xw<kWj7sYas8>vCmzqTclz6gG%tDATkt(4qReb@`)Vo+vVhFQ-s6f7Z!np#`o@o8?!?f;L|"
    "4nnJR%%3802`RbQA+_&hUZk8jn&Nm);CskPz7zt9lYKw(yt9WLNG;D>fIGe`8&HR{b8?U=;oc8*X;f~qxbTFHfA<"
    "&I>M;0>|TQAlCV{12uRa8>YqsFB5)*}<tQe!~cNX2nXOSZo+z12fIRBb~F)5c~cLrKvYYR9z)J0%7_MYYpK1_%xy"
    "!<#hnOAheyjTL5L&1)D_54(}yW(&cx=6DcUYNR0M*|=}?GVLT3i4Az04$fJXwU(v3-w+@@^*4@azPD-6ngOFe?q)"
    "3>=4wY7Ifxns)C<Dk>+j{N888TD{eRed7xuP|WKH<5V4Sm`$ONP%$8j=rI5UdGIGV_kjwC0OV{0LZgd~h9l0%SIG"
    "#>r;uj|$~G(b?6XU}tX=j_HJE{(oaS65e8y>FGt(8wbq6Yk3|xn^;tnBO}m`fCT(JVs#6%F3+_%={wSb^|9hHYKD"
    "t+|JdO9nZR~y(OTn;B+uE%W}Au;!eYT({M{u!OvZ<?A|@u7Ots?z}H76+e&<RDIbayI`V;{SBmR=R^HRwA#zP(UB"
    "k}*lhf_}u=oFdRXmHeSX8~t6>Aw+W*i-!;2#dceuMESjYVJ_s>cAb)GwxxZ$7f3*)G$3Y!3u2sT_id{ZIN&NstZ("
    "AK!IDP|6SPCLM*wr&`&HShPn^tnmWc9zSOW0iSdvHJ>UJ(M6`rUCb_r6!r9dCVni{54Z#6U?PfnWyU)ffVL(G3=~"
    "~C;!6|fVPuy@_p@#+*YRNI@Rz~yZ^^IQd#6=FU5|BYv~qg?_t0=&7(Lsjg;8%>0|K6hCb<QwyC4+Se|H7fEPWJMg"
    "|6sa%4dp$!|o2Ik^y@E9M0ls#d}HQA#+*ha5|ua4@rCxWL~Kx+1Y*?B0B%LK?=D4!x^ML{JM*?zD9nj1p?PJdzAD"
    "&fnFxG3KahX5=9*-`Ol0fFK{t?6PWsUj{%+z?_7b4qVVw0GkAQQ^`ALt=!kykp&I8@o1Ro_)p~WBL2T%pAVy{Yg0"
    "j4Tg@FkSNR252K~Gu+jS-w1TD8PU=d4)G;(XTwOXcR-c&X*RPbE%j;HY^yA>L@+KK`^mN=6uR7c`A%zuRv;jPf)6"
    "b%gA~dp2ShtOQgV;C$6rE1%$Dy{3;VGNQG{_YJ7h@&b0Ax>rbc)GqpuZGuGd(g!A`vst@8?b}q6{RCZc9um1pl-#"
    "I!cma=ZZ90!Y4dF6EM>#j#6I^V`m()Dxx%va!0IX;7pKlJ4oxyzyNa+otha2i|8K%5|)tIEPQcValoUiy(&a*K`Y"
    "T<(f5EsA5V!xKT{#+6Z0v>O9Mtb*RIl9Ug?!7Gx1@_1+T_+((BCLJgyZ|c+v<KJDMjayepq<b9y>11_ZaLG{c^Re"
    "OYF`+&&W6&n9)_Ram5U4YNoBdAhh1DeDc0`B)z!40X4JpUGJ{%RHp^zrm`9X#0ms|o)zp)k4$($PR8LdS1mGl~g>"
    "+iT8j;!*A`78IA+q9ivMfmc<921dnP+(OmsuH?pb6==kBAArci*XNKdjTcN^WcWDKCrfc<@)%O4k+0uhjJlkv02W"
    "!-+C#)T)w?+YRx^vvGcfSaL`YMBS^U;-w=qXxYL-xtteS8MhgCT`V;1VCZ7=xW!TT%lMYh<NdaqDizTv`s?A|fiE"
    "++0rrQ(gXmW6CHkYTgx8Z~jk?t4ghk9Jb7y&5C)Bam<e)?zCJu7d%y8U|^_b|ul@D6_EWu;Um2U)3Iaj@8>!b3+2"
    "=CcqZ4zq*9^2YB4(iI-(RA&~R3SHJj|5kunh6nPlwaa526iAfWIm&)Tup8=4-eEbRMhI#vYN@_;wB0Vuk-PUGmK;"
    "d(@ioZ{MphMYU_x*1QV@AxrfIOEN%W{U^%4o;dRYJ($QY5fLSWzkY04M!>XRBNh4xCk)$KmDj_@xP_2E_h|(Op$k"
    "DhIw#L5xuy+GAsiR-@<*<veIl~O{$^;cmi$_1!N+Q;hT$*NaS?dJl+g<hz0gwK_022)gTr6Y%3DYUuS5CYUQ8$`k"
    "BFn9!v%iqWmuds{tketSNmUeyl;Ds1vdfkp&?YZsmo*^NqWlhiexxm!0$_nA1Q0Zt$}t8yCW%P*2GNPdzlmPx2UB"
    "Y?C`9vh43?arS##?zT<)r-Rx7<w^|6q$Y=u_78N4~8bxw<H1p$syZ4P%0XS{73zd1M{;u=X`Yh!*uYt$97`yPQT)"
    "Q7Ys1RUEXp|#adU<I|nE$Z<W8YlQQN$k^j5gV~p`#20RV4~Uj=FhLTV)7IAH+GGAB!UUsY+8(T@!gFI`~t_g4G{L"
    "wRzF@rC)RZGat(R%ij$STaUa4U-eIqVjYIr75O_V}s(%j<uL<ZW-gdUm!l?MYwUI9wmv%)$M0KPi#_FIw-Px+m@8"
    "s|u@f;=iPVE~ewx=9I1!-t*7*)Im-Q6l8CJR-RKG3HS3}KIf3>bv$QMTJlP~(~pQ39=_Thz%nl&MCzDUSjwVIt*i"
    "9=6YLK&KZv<0h;EcB(pEIXpUo{o}oJB<Gl*wFhz~JIrc)-~9O)kPF(s@F@sN_LAsDrK|!G(oN76Y2=QTzM+<LhL+"
    "he=+gAofw#M=nR|}6L~@<TV`2rD^LrqhpkWii@W!R`W~w&W(@8#Td5@_Fs<zmsB!<-}mlbuq?=hT;jkX<B#E{o<="
    "0LA==2zCzx}<@tUw{VX6;QC^wQT03APqs=xq`qk%#MzWa<+3q`BCSXaG>isy9D1W>o1Bvl#Vd4_7xct9?#;+1eHc"
    "w94uh&eM+`Ba=B4h=bM&J4JW6#e&SFzV^+fpXx%DP0(~sE<lf_rM*&3tVp!z;bA5mq(B31Qe6A}*3Abfty6`9ZW$"
    "(nJPSi#vi_WFtdqBj#5g6~r+ci=$$T$H-Tig|k?4~BpQ!nB@JE6&(F_DB2QnEW--I~1W-=<6B0wgRxCWp9K-bsu>"
    "0SJQn7$Yoy_rXjQtARvH5W6k0bf{mzSvc*1QH;tTv$o8AOQ;&U%}hXi|9RjxtKt4lK54xG(n}G-kl_^CuiI5>?w6"
    "y=+dF-`oE5IRMyVW*ow0r*M=(XhDRa#Pjn&;$-^!{47^hB+(_dESsrb676zB`~U2;75&o_gUP_*wuka6n9Y()mzT"
    "A(^>0P0|rW&hyK{(daLLhvJ6u@$Za9;n!ZtT3VLLzHIFRiiRk#fp$`L`#7c-sKS~QHZGBCcG>*Sw(y!#(?z8e5q7"
    "9a=O7^0eVYZczflKx_oMd37{{PL37Z=8#^KNrKcO^0Vpjb4OWkSwCX9><H%9MaBCB;u}ZZc6>ImtOtfhp4%oqLeF"
    "Plw!@S6a-20diX(0ei;=UO4h-iy2AVp&!2=Sm=oC@5=E+<#>lz1shA2LQ;vIIQ>AH+@zsk#Sb<&V0yL-^LtU(@`g"
    "^#^Lz7C`u@t@>ci-mN`kMptGPv|Z{{J4*xRrIV(?bGbSl<BMpAjzGX{$q{0H3DI<E3Fkp|Bklqb?JBeQ=4_I}KrV"
    "_mW`QBR1moVe&eQ}EQGdGu(J6rXiBT#bhacUjn0t=e3Zvp&V%&;Tp3M*vA$M7?`|R?*t8@W-UNrFPYJgPMM<oy-#"
    "O9So>5cU$7eW+>b5fnC?qBA}*@rMFCPK9x)QhWAuh+Fx9_UMjEunQ363Esd6;9d{{<6<PoJt1sMV7@H2_ws*B4ea"
    "fhlWwkzO$+(R|Mn88Cn~&Nb#5^^-@OAF;$x=Qr{(Bgs|mzcS4;Fw0!pab-FCHuW+sCW)SIB?yl`Or#~GY@16dZfK"
    "l<OamzPTCt`Wm)jT<J-(*PTthRFSc+rb)(#evr+DztRjMm1{Qq4c)_&bMfs($}m4Fs&!K*tDpq4-ay0|^6^C!;<E"
    "efI_kl)r&f#$q_nFVqBnH%W(T5~)Ivj3Zs3KXx%+W_0qF(*;NvQX96OxJn9;md>A|d;;@n3USmJWrYyzoC3lC8$e"
    "%$9wcV-fn_os%P6QDR}eD`Tt1RB1}!}~{1xt5E;`k!bP{RMPy|-9N`b7O96oq-e0X$tGB{C^D)CWDNulynj~(49p"
    "_;(i>>k*)C#r!~A*MNBDS20N{}moWF4#dGsW0CEj-DY1g@!p}ihC?&fzhfC_wh;x>!Q^lSQ9wrBdZ|QJV0FpJw>r"
    "PAM)&$;PTZU1v~;hd!!WaFrO(2QA4L>9;49@rpktac<@Pd`qTC)aWdYf?;(180cSYTa@JMz{Car<$o$I*Tn7<3r<"
    "32LnBJbpAXnh3r(ZY_=QIT82onfRhj=rkLWYa+T@2v+WIM4nMd7;_s(aGO9n}a5B!ny)c@$q1#6QN&{q;fZ&QPFd"
    "Am5f)vpivSq3I{vuLsn$#r1r;yuw)icS^t~OK_&1`{CDE-nrV^!8FJVATm^%BgMIa<tZtHMq05W6Kp4)hC}nt53P"
    "C4$K+g3&<5vBX#i?bjR^F32RtNjfI*h0!1}7PQkmLzr$4p2{HgA3%-N?vf7QS5Cd&9*j<as`!xWZD&=YEB3RNZU9"
    "M!6sW}8%#xTRsoPt-)8F{utt5H-m9=DAuG$9D<Ok8_$Z=^Wsv<PluQ@1BwjJ|&5R?7Mu@hLQY~qzTGaNEd(<BF`U"
    "T21S!x1$l$5u48J$k&C<Iv`=DOL8cPcPqBnD!}64XT9Xr^40jXlMrjiy56FSSwZiKOh(ki+5YA0NW;l80IJ;C^hj"
    "Cq6f_`>eOY8~dl^##WRbR1dEbrS=UGW+=N}e~fbBaJ2?<OZdzo9()pWk#&2iqhCbZ*DsXVUKp6mQbO;hzMCy@#V6"
    ">vRS@Xz<3doCF7wDYC4VJpo$kQuo2?!HVZ59V?sq1`LIXA+Xi!L|%}>T|fx@6$R8_?tx`_bfY~8Y*sV3c#j5pswt"
    "?u!m}HVrWpnJ0*Iwrr4ZkUY6(&2(JWU>4{DpA-+;k11=LD(rVdp_)H0h7ulaC|){a|%>HIr*_Aqq`jSi){b$i5z0"
    "4)H)1fenD;jm>WJdRxpJkRR?ZeApp`Pj9z$$ieESc-medhm7*mOVlpLYduQ!f2sB0P%aUT=T&jblHTu2-{YA4+8b"
    "9dX^my$5}@SB$i-QcQB>YHAiRZ9UP8(X%|+HfGSQ9Nebiclo<8jJy|X;JKrf|)6FEr68?H}c(9v6gdUok;J3>>yR"
    ")uCFTEZ$0}H)GsT%MJwQIy;@56muk_?E30@Hko_`iE%%wJ^4gd##>ATJ&;1V84#J5!Oe##avuEo#^rQN0EZhsTG3"
    "URaHcv>rh+Omjp_0<9L=3GCvASxXlMr-F<20|!Aq8-3K}{b8<|IB~jasCxBN>D_3u1XSD5;6TX?0V<0t5#O=xW&?"
    "-j7+FMG-~l7@Q~DuuhlE=qdhSYHGU_WZS$IR_sbJuF?;}K|yxi9v;{|JI%dIt^P8X!#y~Gi<7^#7Fj4H?&!57+Q>"
    "20a!x_Xyt&?Mk88&7<(Wd{;1FcRYDESnMiYL-TSPv_+O@UYU<9taKr6LkOdOPcO*(z!+gb5#T=T1>M_FQ(kb&i01"
    "PB^}YC9xsRF>D2U5tclTGY#M}FC&Khh>3$c>*dA_LCi-vvPw3rCl0uq#g0)RN9^sPMz&<C@wJQQoIMpN%N`i6J?!"
    ")%!6CDO%A{*^hI=Jz0o)^#~wJf?P$uP!hy~sa+7l=oh-5xiolDc_kIMta7EHb#YKzJB!$gv2;u<pjuvp9OLlOb7k"
    "IF_JDTv=-@C*W|Fb7Wz+$1O0O2&w(Tv?$7QVOJ277A@&j7c7~xT4{9<AQ%A=_-ouXKnQ>wIQzIpWcqV2eB_N5I4b"
    "N8$2cLd6T62;gX8Vf!(;o*9~S5YgVelEj%`oTDeU%O+k`$M^%7N#HFP&pi{Us$&!Ey~H(9DSZlvkZcSDkEmxsHR)"
    "1UTEc*hJTD!3AJHL27_|C%;56M7CeCD*W-y+(Il0p`|4W|w!lRJM~^=ODQT{JH4MMss7VS{2=9+54{T0itx6gj96"
    "$UhTj8p1|u4u%uJ(*jnoUtA4gPnAlrEV@((MA&_5jUzpAf3U#nBP_X7=%UWUck(RSBqTpKA6~_k|onjwa>xt{m25"
    "lTYRdws?UBSC2cmej}_^0)K=wv0BYICGU&V8$+BwOAjD-rj8Pn<5*D`3Cr)&VDVJFv&olU@U`Move?k)9k@pZ$WH"
    "+~~)><CD`K8rAH2L9ev3aE;$)0tSpeE4abv#^r@t{X1$Qxq+Pgu8|YkJnNOp)n)7<FAY2i7*xO#9M!#Zm{y^OX@Y"
    "sBmo%@t#>0E$^(1rGyzDLMo=c{BVK<cC=r<_FkddtHVb4<uQ6&p-(rxdY?)@_8LGOA#C@9VGL#dV5b&RMz-mOv%I"
    "2?}usf*&zZk^IRvKW{=cTHrxHI`>7V#kt}Qpn&24TXMK<5r3ZQW&f{S_R0Z30hE91%tTQdq5?fp#MUZH@!3nAFYB"
    ";FQRYT9<}lRGnoFL!SsKf!KC9PT+b7HH1@q~!fwi5+kW&G5XsSDgMT1KCoVpSR1U3yKf2TjuxR!BW?eXQnk<FF2^"
    "jtPcJoXkMKGa2r%w6LsIJOKmGQ|=FDWCB+-=-H*RYq9PooWk$HT_310qtZNrowszuGU?#8-!<$DCXG>5Kth%u6LU"
    "iIS-jwo}x*ZCGt5(|@GB=w$!L&CM<F#DhCKrd5O7+|gxvlgk+k1Q?qYoDk|%zk3eQu8!Af*3lj5T&wPKge_Sxs*n"
    "9I-<Krx|90c)k<6Ur|A3j(><pI!0(|VLJ?o^d7-kc->6!AmJ{<5zg`B&XASenWqa#Viw=rcye;z?^E29BT8diWvc"
    "|@ub9LpnK%-B~wzsMJJ@F`7H8|SJQ#_8m03E@YR%T(E}YCALm|6a5Y47zxZ28Tv?gnviJu_*|9@sd!nC_PNTcqny"
    "emZccu{_x`-MuQJyX3Y&qmeOQ1a7cR)T91L66`Nai2Tv=YwblU7@?f4H8w9IFfgtanywAsD3Zhk49|uA!fQSWGXr"
    "u5K-LWmo7Z6B5$~fFfHEkHkFCO&pN(FqK*6%OK?wDQQ706Y`LFf{(B)^q?o~h1-q-k);GV~Epky3ooM1yS$eJ=eM"
    "lULC8bpCTjbh<i~3n^E_Z#s`s#JWi>GvWBIkxDW7B*Kj0$F34ww;~APB7T{oD`#k5D4|0|f|FHaWohubArO?vi4U"
    "i*(rNWV!yjK{Aj1-`IN8~TkO;j@!KgT?T2s|~5DtP4iIFOJJe{%kBWful?ict&nS`5h^qu<So6U9%abPEKc?&Opq"
    "b`5@O}lM9|H69cxg4K}VNO+eqAYJcqV-?@&iOhN-S)~7Q8B3JwWWRSmL_+;RzJOhm0nuhB@CKH<<7IKx!@E)Rm#<"
    "w*pxhsS7DW5-**Z#H=s(dq4;mGlmDpx`|KO)(;c|HiT_VE<7;K8w}UTQPk*f+sjTPq6gUFGfI$C#^I8VPqaAwWg?"
    "k+j2nED)0;h>ZdIwp)R}<VJ3lKCD{~<x6-ZV;}AjF~YVwo+~zQWCQdH3WLEInF4;R`9m@h;{RLKexi#WR`m7L#VL"
    "QZ8zmnj;fw0y*0*^Le2rb^bfeOZ7A##sLPa`jBx<s9G;>r_n8VF47U00TQy2Nr9@N!)yd=FN9r@LM6)qYRNEC*<A"
    "GuPI>iXiigCx`II>KSa$!J&8PkpyUxZVGA>E(PmMHfT0(YUE<ab|_eYuB2Q;DMYJndEd)b_k(U?aj^x?muV164%-"
    "@<Ow`t)xoEhtl3zReq3AYW!IESHs7TP+xi9##zfRG0<nsq?e4=PCzdXpXLqtBKO2DfBC!`5E1czV9rB<q%*hfW8Q"
    "i^<9`kvOq1TLkkbl^iW{bI)tTtrPnwQGy$LYmO*C$Oh7cDrCri^4ir6wyqWd$d-EnecxHihaMWwdMv=S3Gl4rVK^"
    "m9-GcVa1C0|y}9Yl;|l6qWtB&G&zlOCBU(Z2{Bzi;O$-~+lGHf3zKd){}c39aGnwql#^zQ+bssrc$FR@vy|<h60x"
    "_(SmLH*f>^Vm}TIf7MWWzqm(GB)E@1SHQN75Q1nZpTsm0h=-UeRid<<iCUaxi=3kOOK5J?TF6tUKU8%%El&FcnLW"
    "NAeMDymSzq`kXA(?jcdb#D&B$PL+$A&+_qv0iX;PwYD?PNLv8Y&)1pypX7*7T(2x5X_0TeF-K{gjzWJO<F+4T5Wn"
    "5$DN^%ft(MuM==uV6cM9{Xi}wVZ2)Pmnm>#J5zAu-;*hOd-F-bV6H$krtdyZRmE2OiM=3gF(?_icTqr&26!mwL@u"
    "PvLouAW?*=$o!&0SUaD!?nyKAL{yPx8EQfa;vz6=sJ&syDM)G7Yl!5{&&TRF!VDHn?kGIj`Kw9M=%0$nC^p_9ib8"
    "n>Av`uexTdx}aVl9gJGCq`m!lHU6cc=s2RL{n46uU)b_7MPJ^97~mFpO)DT6N!U*Ob=&Y^~J3ZmjHdl7O>5*1hjI"
    "y>&0tvD?!pN+4HFd#i5v-#z&Vj<)st>5?!Pab}}+<j(UN8Tvvka+49J{X}|4t<0)|46SZ7;Q6ICRgAEYk@Xlv$f}"
    "K$&Sx7zv*jnn+d@K4)~7LNRL6v(7E_fTGJ;zTMzH?2tzT8wVKvu!L)x^~OC>bZ2CsWGg>|KA62et<gR3xgYDCxpp"
    "eXZ%1>UeoF>MM=wPV%G0oco^Mtu@YQ+9v}Q)Bo!_#y`0K`q~xO1&*%Gm=b-R^6+(iGnIR#(C|>G~`Ju{IwGD3792"
    "Mqpf6fb5s6*AccPgL`5m@KI*%sa4X0x<O4?#RD_KVVR#%}>c&8E**KjQ!8)2O*9vedutUP~M%e_l#CV^^6c`|Rqu"
    "3zJHYzD<{uqH(hbz8517WWLOqLt}8~lKN)`bTRH&Q@m40sOr9HODOE%H6SZkVatA?kCE1MgRZhR6}s$jafa$X;JX"
    "kDX_fZAkX5WyHW<pv1-M>=LN;72N|zst+g=Rh9T*+tmcMbJ`^lXVzV7ST7<r7oxp)8<#1Et(0!kiizer!j7s(d8@"
    "8RK8ea2*Q-l&WHzedWQw%O3FVQjuAL1J_YiJPd-~oqV%M}m`NI5~>$X{t`;&2ckr9{x<u!CE6S=1OKv24TwwVt9_"
    "3qsT`U?N7{(v8EPImdP(R4gc=Xe9Oor{kEU)iguaQHH8?rUm<hj^qYRhJ^hglWhe6TJV0=NkW-fxH)g{@1(Z=4Se"
    "JMb+Bv2S|{nJV(faHLwXBd;(mZTVJ-r<b##NT!nJ(X_C##252+j24_~0$Z?4Ua>07YGe}nIt(B_iK41+@Z)+IsYk"
    ";6Ecn*TmSYfuOqja{Q<{4syb~i~t-y})A>U~m6JxE$g7mK+VExHOZdRp2m%b91XQYrv6m0ezPN_wfx@<XeOzmMxW"
    "3dRP(h+&LY>@Xm#V4N@X<M^xgdE=(x414}nUnL4|MucQMqOW_{fW3gmrWd-1Mpv|IJp=^Gl9-HjXZ5e|1%sf1t7n"
    "UCP4wljluCo$B1+%FBdL4aHXrrN=3?!;4*IM0x^um@gb+@ORZ!@5eR-@8v^2?u`gU9xiWt)OwU4`iIxA)%X)^~zh"
    "c2z0yCqDXRWH;4_N;yvvKa_s!NS-<I#M|U97*8GOGvUCFGp%y0?`Gk%l@&<3!ab<))|YrS`siU$ChH*nbp173@@o"
    ">S!jn*fFMCn_LLf%3KRlhHyb5!=0j+=YY3Q>F1bmes?VH*R+EJh5GtRS@t3{9uZUQ-cZ>j7CAb~Kc~S~~6_6w->n"
    "+ZgaXMi{4~lc3qrl|^MjcmL0ukZs7l2==1_i)+IDDy$Y^P*5ODSNXr?n~Atr#9Lo%~(Uou-!@HpOJZUI5i>c`?q1"
    "RJ(Ervg&kg`)jxb=t4*~hR8KOF$Pd6_yh-SFexWC3jBqpA#T>)y)!_1LLrJz5gsKo|BB@eONmhyXK$@X%0g2C239"
    "%$*PF9N(@E<#yT}&cR4pu+G4_qPkC~cmled*1Y1m~;M?~(S4%Si}xWs}ZfqJU0Zj8Vf{kIg{5Y2R$my(j}yg)z@J"
    "f)klBp}AQK9N^d%Y9HV*!$<)ubxxpV+aCP%(2yeQ;et-NV7&xQ{X)U|0cZf*d9+$*R62ChhyKFwJjv_@3T82>gq?"
    "8CbYk=9)r6<I9@$Fg5BiIhu{;AD=hSYXRrjH37aI<(7f)18Ol}-n(y-FRRahjwH3`3xbISC*+;DI9n|(EEhMsPj$"
    "BKM!xB+?DlDBfl4+mdt|OFgXOSu)y|F`HH6$;Fd>^&VM|d*vg2hJJ)1kb08Y1#E_&S4@8uG(M_A&=CRO4upWurpy"
    "c5t=mM*C9;Y=lu~_z8>PvP>GNhb*Bbi(|NZUKoQH*?<7{PGk#a_Yh7D2+vdN5c-2s&=3W@n99lt>|=oO!}%oekR+"
    "~$!dpIGzI*Z!Cg%ney>WKmqhID5>YA`oR9Q6GthZXU&l=-vVdxFIzzQcg`}B5dag9ex>0dybAWNuVd}Ix91H0#ue"
    "e{wR96Q6{6b}k{E|wP<$_3%Za_O$9j#6$Eo%|UIe&dD#%j-rC4`<16oLk>~y>qmK7aGSJub|j1)GWD}{*F@Mpw(c"
    ")>pHx=)m*&CD51Kuf}Ff~?%I@=_eJvcchB360;o@@eG;s6gILBUh<Z4OCiGZBaAN_fd-DWhIjK5MD3nnzV$IO}32"
    "|&hU#eQe2vX2$4|NN)4mmL*?)jcn(f^PMymNb2v=doT=70!%#Mal|P3+vmOW~|-CA}!n|4v+r7P5d5@K()3c5Fh0"
    "V9U|Dk(l1PsRMPxUHm+Z)Ln&|Pw~F@L74E#hkQQ8^qT(1`x4O}#M59iLR5K7x`p?<`Q(GLI9k^C;^^aj+wMZrl0n"
    "yGGadsdH&LBX$y}d~B$fvET!oWLJI19?4UCNAOSGNI@Wz1nV7a!63LSf5QPrlC6-1_|kt<c49+l3oik?5uec9q{I"
    "4-K32WQTiVfhFi;p>qqwMA11AqGP+NoVSH^pr9okbQ<_9Vzxd-nUmlxk5GZ&9`*KbJmP|ky!zt**9P%aFjLZt5Qt"
    "ZA{b}JQfl;Zg;N~5zssR3Rc`Yq-1eSs3bA)6d!gbTRF-`nt}gznc#_qqewKe%JZ))M{f2dIHHbMwNEsucdrBNw17"
    "fDA93FX021wa!;Cq;h<!1Pl4aWr~pNQ^%9Cbj0nFtDPSRpJYI+m5uCm4I%-XY5VTsNg#L8*rNg=Q8&Vo|G}<`cEu"
    "dI}PWxsjA2Fo(!s4(3<&ds$K9WU7qx1!mV;gj7XX5qYX14#_$^u~HZDl)(OPYUe5g1ri`I4b!%B4+T!dfN0T9&V>"
    "KOwk4k;1SyBu0v^oxA{{>1#;r~3n;OFx$g0-L;(PqmJkuZglNgs?+GEAKe;$~4Cwcf3q!-h8BwC$6idBt>0w%%HL"
    "biTL0w1h`MT)=&lqswcJ|wRuxZ|W4eMWFx%w<V|x4Sp*NBNv7mMO?1CW7H)`ksG6mHM00Z#BdK=TUR=bjznXi@t)"
    "?Xv%+<nUn&ik{w>cQxIWvl}Yuijc>h!#8u-t5Y{U?3YdbqJ}tVC0N0}IX!Ywb**P9;pDK$Me+>S%voC-DdVF}W|6"
    "3ewPG9J{qtU7EUXHLBQ#OJ}UvNOS>ZL5bv4hv~LKnc5vzBU2yL9VvyezKms5AITaW@&Z<N<(JoVMDoa-nv39u@e2"
    "?KH6*4H(Kw5?jr+r_(q2H@kG~OO5kJI2+v(H8-E6BF95CmbVkJKaRc{la}daG^1*-P6e4GN>^iIJC2|6LmtTU%WM"
    "f~y!{z@R=LBN<PQC2a;=W(4!tBzNbc0vuLx`f;b<)PIG;%HDuHOsdQq@5EgTR7>S~+zfZ!3Dgox-a+M>>3jYVC8C"
    "|er_eV<%?qButzfs+{MKA7hTdVGe979&N*8~=e0$c;Alan(cI&-mQ_-s?S8vofu%J0!Kt@GG)jr1uQG58ymzAM)w"
    "4K=4OyYor~eZ7Tyx$>53Q{&YD9$&qG-Zn<=Uu|%Wyy`{$l5Nl`^o%Q9+TVAvJ_5xP)snl3zW?!;a>>?p<5+6(W(+"
    "l)BpG7_=j(*&lv-F&O!F^OaXX!!H$8<iadz?=wZ2>n63`FIE_JiKBmpr46WX)?kki7jWXKdSmm?BAVKQh~YaE<Et"
    "6mX1Um)%PQBBu#aX0{{;rHgW6kRjL;78G;*YP5v(lXkK8>PQ(}GbPN&RlZnpBvpO%BoZcMTuDuEj0WRFH*jBmhDz"
    "m-3x=Z7qF=iWw!7~TXrhxJws(FG3lCzGZJ)Y)GL0A}tgoD$ZUb>@B^i0If~DQ#7`zBl4cVI0rYu?GsIkfUV%?#lI"
    "c_S;UhoCOS%O&0mESjKLNr;!h3VPf)58~h&?thW#I53;WmY2Mx)B!Dr8Mr8%28O+`*tS+Ah3@FT-$j7cm}!S5U{Y"
    "&oLB-nLtzpc%7zu6GCX7tuPJ=Ib1;;1d!d_Tx7G$!j1Myor38Hod4|$1G^F}XmKIAy)j&}PniB@N>Clt^SgOU*hB"
    "Iz_c4XYS&XyVw%O_Xp>=NQta9ZN&0#SuQhVJzJOV$6Q>2e{C3q+z{Ow|S#u>`uG#EeinF?tk8nw@PmQirdM-46to"
    "EwqL$;}XCHbJeN;#MKN9Y_|WitLY+Vgf;6rE?p^}<f(nkyd@lv;AdBTlux=BOMt&X)KpCW!Q&4|^uK^UYP)R0kXZ"
    "~{mFQ0q9g_s9+FcA+TG4GxcV{zolP#{NBLus{XF1rNE<2t~<c_C@`{*G8=IkNMjny-yJQKIqOjmgXoJv;mi5*!_@"
    "nrr6+doOMs^`<vTD3KG@C|4%-QBjUy?IIzS0C@&25%h&_!n)HQn}AIpMBHWe9_tZ&H-5TdcYBna{7QylM1d$rBC;"
    "~@5bRniCKD)k97{qM+(rOzwhtEiwjQqy~*X2-w;L2dDITb%LltUYQu0}9sQy#kV{7jpwI2m!J0h<Cw@tI>ib4F>F"
    "omo%1!G+$TNXpQg&Tfl!?r_vB=WlH8Tt2p^G`c(YeLl6{VxM_C!Z0t_*F3vw5n<6rnFyW~LHpKsMJBaUZV^q#xyU"
    "5PIaiYP%NJi8Z}nnH}d#O{-FslxJ~Sq97Wn`FzJI{V^;Tk(2g@Q>c2n*UPNM@B9#{HRFyTX7xfvkM!*P`?nuC_m1"
    "LDHqT;fD!`SkvwJ%Ng;&P2_8Mav)Gm2}n}RC&xpx%*Of4!I_TUq!`+PQJz1Q8O(a715v<DKdweJIz!vP<W{T&F!r"
    "K+9LC&3vC#dp4b_G0rHW`0m8G*#k_6`l*}c@ttI(a2EuZj@N{SE+XNS^nGbvA{`<>%gV=lx={nPYH!U3+XbF>=u&"
    "$Bmn~^NwhvCd#0%Y$PR_c6?*|ZGti@TBkZ;g;g8C>l4gcw@*PNt#6&32lXRT<D2AYgg9t7N_$hC{Io*l%#eYA5;U"
    "^;rn&=)Am*S2~%l1WA`))0YC@`H){&PQvz+m=%LBuwPX;ZMNj@})mIT9GCC2Yx2#l<y@>}Bo(IvJ;@?<3Yu7|SoJ"
    "1QYWOQXdQ@<Son?36r-_2<US=!7WH+A^`*om2*iXMI8R4Pc_mzbr~j=e(LGd=(`sN$vNb@ee%QL)!u>rfX|t<q`Z"
    "WS@?mhWF!ucNd!BDx&Z#vk_!b<^R3rg<ysFUcWk%(?I`9U)DmM`eeRX{J<|z8%w@CK&VSZZ5V|?@~aIp<5!J^xbn"
    "mgc!({!wCx~v6J)ZlA`u0Iez)!sqW+SoZf_;K&}^<Z}+-q;=N@BN~NW_P0<aKoR%tCYnN4fa)8o6+E4w;gY)g|qZ"
    "<gD-C%9UUM3f*(Fn1??TYQh&WU`1#=Q*Ml`H5O{cHCTf_7`U05O7Hf5~2A-t+v0?^Lk3mXqxP^3>_5@f}BLk9yCB"
    "va7pz^gr<#26z@h1l+fmzWV=S*?Uup~DmiL_KlM<A^emgH`+SA`>mLXm9jR7f@+j~J02wWKp)kbnK*lf=pbK*@G)"
    "hGO?C<X_niEzTZEBu>16n9_R0RO{(ofMmU;F30u9Q>eIE(n_cxsKJ!w8_1ntd$>^wxbD4t6tk9NhJv7;4aeY6J8h"
    "kCJlNj-O{sz7HwOo#5SSo(qg_$P;qmU^7?dYty2r{+r8B-~n>94&XZ8de(!BcoJ%w!8rpHK^#Tsy(pia|qqKuuqh"
    "?QBQrsb%j;o-HUStmuigOi>0drD1>91z{JHI~Ba{@~K?DwjvnIYq7TK=i^S8>@!=Jcu?HKp?L6y1oCkVOCZ7PE8v"
    "<b&H(#>#2|$8-pr}{97AR`Uaj?lNj_jb`K8*8&xZTHi|Cu3D9j>>e8y9oPx9*o=VJSabm2=FzfjTTNIPU@qkZ|0}"
    "u{0^|31~F>KS(VI>iu<P2YLMG;`$1npKWZuiZ0?I+=|6kdF*r@PvsW9I=fOsi<4!G1ADUYeJHcME5L;F-$jk+93_"
    "S}c`Xo`b!QgcL9>xI%1ZP=%te+?#B9&`sSOUDnF_>nHCGs<DtFs0Pe4*r1y70@Y1KQek%Ksa8?<(gQ2%uM2P95dF"
    "$MG=w<Jbrl;m4PiNG8ET>RVle;E7e%%T8MZFjjJ&x*Qcq-^BN8C?eeqt8xMkRERwhq+HP13fSkYK``wSszHtRp-^"
    "KIhVj!^Y<7DaXkpaxE4y?@D~sj8yyLfgQhN>p_S8Tce{@W?S5f#mMQa!YSH=X<j0OH%ZRiCdrxdvW*!Da!QLFb3y"
    "=GX07v09L1N9-WnPTWa|Z8)FpHFB{aCI9+4eDZw~sYnPJl0Psr>4Vy;YfJOA$>P~!<^Sb%7s@7l`b(O^n;LF*Zle"
    "2MGkS<600>QHZG>-Y7D|n&6ExObxlS@Bk5}E_Iuvtzw^G>42ZFRei+Z;^brWA77DBvkB&WSREl)a%~-~k%6a*{gW"
    "c9Mt_2o5|hlczfGx+<97J8cHTC@~GD3xVE9rZ@S5aWQVv-(iCS_A={NjcgKi=ztH4X?ue~9hXSI^Y6-M{7<?)!xh"
    "krQGr?$;b$p5_z7B?<Y{GNlYZz$OIMe_+O85KS<{n$ET@aCNPKuUyy?6_n~bISTT6nXRIAzv+%=!YBaA7jn9QC~>"
    "5P9;ew$@<1+&f30!Ytpm7n$ZIFexOXjf-{ik>97Rh_(RR4^22ewmYg_y<muJ?O)CPxhC?yN$xQ5~Dz-f?DVfxeqm"
    ")*4qtBg<|Ha&7Ud}9jqDMsp6M?A{Ky7EQn<G_mK7DBW>oNK8?0EH}AXr^MApw-sUrpyHypq4f$nAqpBg@L7GLy(o"
    "Ex`^%J^ueWm&Xhorc9eaBw0%p=P+1T*R0&8oOGx{cThZqpn)UfUdQVV2Jc3JX>xV&G6+mTZpviXCtNcv?{@V+i^d"
    "nd&ObVDl^RD_EX-8mmXO9wAemzsB~cb6@P&aD|32f{<bDytA`?urq+5v~YJE>sS=MHz7^qR8j8Tdq@=C&mG&9($h"
    "CB1asco`YVHF9U&@u-#&7quv9#BJBy=i0%1EzS`72thF#YaHf&U>rgox_6fPN2A~_>f!)`$BK@hY$k`!~2Xt-rOW"
    "WF__^V3y9C^Yc6%o&I5L&}B3eJa%?@`ENX*=W=dut1!KlxQYP4xCFdaR|0mPtC<tseBMiR?A9ytW+t{$@+mUYKb3"
    "_B|%jPU(Gc2nh+TLeEBd7QPl@74a^pj4kz$fiMC#Ns^QRCI<$07=g_#qMoyw%1@6;mb=UYe*L#g52R@+8L2YeYn_"
    "uCG^{v%%pJ`)KR0K-^AI$J(6HaDyEL=b=V2e%iRax~XM=XH2!QI;};KUVkRbtF?ndTDbo%>)3Vv0E3T<Q|l;RB&8"
    "9)ZOTI@2<|?#1Or8zkO8mz0%R6&)K7C*v4iWLuxFQ%)Xz50Y>Y4G2+S$UN<O)P;IMr6YU_>&9#y>H=(>8;Qy5c*7"
    "&!Sw5b+=eo#_4OcserEEBSqt+W>6WiK~E%x5|at#0cq#6tVZncr754iLSkdZ?5aCGjSah`9`;T^f(W3vH1Cl*s6E"
    "LBzF$KFk5<8+9beLWIW;8%yrcVL!5^jS2T;^ulhy;46Y&jXH)qpvqRaNdVct8$=K5a4mK%*P94#+}Xp|7u8N!+?Z"
    ">6>pu(Vd{Ato!g<u=WV7Hd^aIhF+e3Xy$Ty$-Cd<-!>J`uvlH&gVj8`lOmE*!(hJp5*lj<kdW{Os(A1=cx<s{|!$"
    "WjBiGV{;&A&sboGDR-jJT;z)qqA6DdGWEB`Sc^Np*7^L2l_h))&Ti9fAj?2(6(Kq*jq-WzObE$e5pFeU<UWuSv=b"
    "EO85^6UKL15McD)O@Q}-B>>5UU}QP!b>|u(JEN^<{6O}5HXr7g20(2_0U!?4cN1Lir3+F-D47-nSs*WV&=OTM4AR"
    "{&3|95?p)#{a%Q><;roeodF4X*lrREMMWu(lP=-drOKabqA>UWc^ZnRCzRvm<)h?T*itT-(69Q(gGN0rpN$*<T!x"
    "b>n9<3L1Iuw>!P9Ztu~n+fBssot54RP9HY!)r|r7y;G7VLqcUU{mNfQ94F4a4ZcrKNn-QVzc#2Ox%DrnqMrLNb{M"
    "h`-Efa$!ek+cNsqYoYIl7v-U<ntb$owM2d;yeW?^!2hsV!mvp%VdR1^g{&0BuQ>30!y?9R44CiWPOowQkzMBx?R|"
    "+|6%s9qT2!fyk-NT_Gh%z?LudWx-Ik}L}BVdu5u$M!XrbY}iyWy;>80Ry9bz<slM6R*=OBmEi#lWhf^$V*VBuf^S"
    "b2WC%EWv#X7<B~>d`E`2i~l6K>Mq9B+u1%ra4qQfz1_j<qr=m|!D)0nINIO-4N~<09YF^3Wc&31ModbH7Pr9Z0tv"
    "u5K*Xt`6*=0#$#8VM_j>#Ix9I1=Z^YtGSX~iy0~7@{Eh5a*fG?>1!^tV%<_QG?$^JjJSbz>u8ZOsEoX`+MSrnprZ"
    "Vw25Pn8k-*F;`a=Wv1(R$Wv*MT{?|P9vgLI=)Ts3bkqkIuPn`Joxd=$=<=MX!}472SB!OpYHvzKZuU@_76{c5%67"
    "OEQ{{L>2SE5<)|o>fE8m%S4yF%-Mt@wR9iDO8uBbx&8@GDx{QJ_tLKQ^Ex6@${#r!m$0YjLOT>W&XAIU5{QA?Os;"
    ";FwpqQ4gT(~M2`k@|c0{}d}?kEz}eQF{D*P<#iC-njJb|_cKMN80B_<2mI$rs=RT%ZO~8Xm$X;W-?<adrvE!|LAX"
    ";mox}fb?}E+@?p$?M5hfd6-AwvGTz4k$xH+Ot?TdfFL@8VLC<|(FwNNc1$TXv^>(X`ruT;ASN6#O?DVTrlA!Who{"
    "vnw>GvBsp}+NI2VEXU9J7@v-CPfZH+Vcme}eTJBUo%*3FV~pwwa$jg~<DY5KHWa3rV37?)P=r!^CbrO4Q7d+anhF"
    "10icG|)@1!6QkUYkU-`HA+8n;|p543Ysi*-JE2W+49z2?a#<^qwNME0ub@YNBQg@=J%n!>9(xSNWG{w%+v7)M6Cl"
    "1z29@nX|}{JR0hxG$ndK_wN1$G=px!6dbj9H+R0FtZ3N1Ks2Ca}5)HD`NGYZ2<qSdyxk+wa-0h4dF;;)cn|(;}V&"
    "FW!1PQ;f9nvFWVm)gvmYz0(<UDUKdvEx{R;rP?<-J)JO6%S7P4Df}v?SCBy?fNS6=n#kfeQpwz?radg*u6A^hsQ+"
    "Py|_^N?V@rwhfDhV=`sMU1sRhW5bi}cyLpw{Te&~uXII4;>3at9GIsOnWt^FFlWlx^(_G02(fKPCIE2VD#4#v`KY"
    "j`GMl4FuT(}^q4(r`p{(xWDf~B)9W~elz6Rxn#C-m#W|f+a9hvf|6xiUvz-q9mac2TVI1@sF$|A@zu^cV%QKj?7O"
    "W4<`HEapi?&5aZv7&Lc(LB5ZW86whyO=U#HrUIZoLtkIj2SKr3Gv4oCQf!k#m$RkD;OBNE(2m1A*(UlhDTb6s;Sj"
    "v!KmWiC{N+gQW8tRkSe)dQ<kBTi=6*g%_djFDx#ZJ$DDFobJ*pfv6<dj^-ZfYsviyX(x+Cm-5fNGma*>MWRYFX)!"
    "e}lNszoOkdMymHIH@i?g?{9WA-q<(5_(2!o|FN>x<|F_MX~+5GBKlFT~k%!q_mK0CAa`=5w$!%LUN}4v}_2U66xS"
    "`!YI8zvt+WxdbpxfmII`glyil@dUL8szQvpl=nKgLy$V(UQfeKvqj~pFAz@yb{6T9P*IeKah=&#33;cCrk2!I+|7"
    "Yy6D-Imd)b#30Q$4Ql>@DaVtSLw;pzsVuXjVJ32Z0zJ)_o`vhASoR7_MUuWR=ja05H`MDSH5uljAjo1uh~ZLzYHz"
    "}WnuADF0tSym_i6~?S**y4)s*syw9u#HP=g)BUlzpg&DZQIB!igCelc;p&H`$4P+Gz03`K3zL6w2vTkxZ1r$AbnC"
    "9!sx{-2|I!ijqhGYY7x%nx6qs7;7(Un)wUpLX^Q}aV2(2zV-TUjbhbquu&OH`&-!=EeFN@C&*DepPR1o?6J$Eiuh"
    "8h>S-(-N=mP?AT3032_rp-F<X6-AUEk~|ND?72=W?9aq}Vc!Bqb460e#ARw2>ws-S)9vTCGC5T<b8+-Mq!-hrOx&"
    "%&V+jwZ~X%w@Y@tC>F~VnA!a5&>!7UQOD{Vp#9Zc%v?WSUX&eqbf6NfllI!NV=ldze#k1^bLi@uOhd&?=d<e+0s("
    "o0K+B`=x{EIEaEf2zq?i3r2|iXJuhx(#&*j2#+t&E8tEAALlC98u4d-6C6{FWd3h1}Dp9j(57FdwNf<^TGasnr5l"
    "Rt&N-ei$73zV)6tWf0*Vhva5AuKrB6|EHh9c12crBl$t5SaE-d(7*09cCGHyoc=h1#_o}<m@GdrK6@SWjRfZIfP)"
    "k8An5z%adtmI)jYZx)!d#KG?FdQB(4pf(%>kEqb0$2wD5$f&o!Z92)_it!y%?u5U??^H3)Ak>Go-0`~v|ssX4f!N"
    "B;_a;g^m=EwT2CndPA*zNfas$P>FUC2MxYr4k^JE(fi_kFGpuGe4>cpnBY<JE{KxbJFR$CVi9WXpM2T|v)h80`3x"
    "m$0Uv1Af8UZY_HPZD0k<6=+XK^~rM9xS>LD+;Tc11hn)FVzE$Z;QD$er<vXY8>7mec#J4@zW#?TH|51ec6>p{u;r"
    "O|R}n%HY8W$PN2$1hGZ<;YsteAOqbm$YGmbeWqgjUxU8R1nCg@(o5UPu83{HS~h7m(>@IQmVg{2zui~MRyu$W5gS"
    "shIQ8IZ(5(O7H8-oP32Y&o9+MnkI<;sK}KPf|bD23kbSVc-;1_RLt>HwB(sQXq1hEF;>-*pWFL>H;`9l>2a<jXz|"
    "C>{2A4h5{C>s29HtT^xY(cev`~K;rQx6@K#bn*xs1C~Rvs&5^o=Vaa585XMspLb1r^FV$+op(Iq^H5|20iF`ec&V"
    "N<I_)4|;oT7Gz3oBX#`tKHlY8G;${_vAj!n0@sLm}m$$Rym>Iy?z|rg=z$a<ahKpW`Wn%ABAWR=n<n5J@4{wTjnp"
    "gyebX!Cj84fChd+!3*Fdvj@T%A&}9VbON-`O1(|t$XxvcZuPbkk<o?XNMdxpwo9vFpBNzZ2DIcH(hsjD=TFapc!7"
    "RE9MU-yhdA3Q6H`qYKt8&KD3e%tpiJ!xjF6a8B{&3G^{cAb(f;<q!QeRA-Z?!yPWE;&c<&~KwswZo<-9-?vR@C6f"
    "A$}ek6MqJ^Bh=UFjfU-VoMEB&l!=J^-7Ni7B#y)1R)jwqj8~uOcNCrDIR5fG4dgE6F53TAH8f7(BLI42ui_SA-7<"
    "K>N_`pSOl#-I_GNh;S2a5BT1H4#q7K}hArOyZzS{x0OCyYsHKz?LNaEM_kN37MGhsFg^s<%!NV^}{6_(;RjoXikR"
    "$?+p%f`V9#>1NKFgu(da&-VQ!wmV6fd%DVq&FXAC^PfI{{LqGmQ2d{7sFqYJkS8Lk!h{C~xRwT1?Z0v^;R^0z@rX"
    "{Vsq+g9{IQL0)I7jWwG0_#C0^(33C*4!9bxmIg$xc)x_57{5x@P%7rqd|f@jyLLzafF!CtKs#JGI-!Z!g22S6oh&"
    "FBh1l?C0hV3&ET3eLM9zTI4^vj*W3`3^pP{1}A>qo}U;xa9a{lGpa)>{C&uJ1C>Ov`^nL&39+_Z+Cg3FwK%Kgb8W"
    "6+Zni)BATh|u_et*yHxEtDtbIZ31i66H(<npgw~YnEr)AP8I4gY?gAJ_X^?RtKv$?YCTxQPtA@6f!Jsrg$&`%F-~"
    "XaF3gfy;R`s=9xroyB3?Rqb&Q}6x26=+U7R|c=llnj|y0?0wXtffn#e}!alNq=U$EvCZNNz*gZTN9B(U?Y#Z@oNT"
    "Z)aO?=fJyEr`bkf+&W7m*WzoHMo2SMv+;-Vr~<R9M%mF<ckwrbN#$m+;SydDThdkO8XHXOS;7$y5iTlcQ{=_BtbF"
    "9H5sfo2UsfRF{=;Mg9Fy%&r?GDseEoJ{Rtm2Qa|z?oAd-%=RJF8~v4Wlw^~CEHfb7&?xfCc&KDI`S%l%l<~iAq2b"
    "lh9Axoa=Gokd;~?%{=hFM7{Zpbq7%sw4L||TsmPe&s@)>fj=?4sHgbkC68$fF&<El|Wur_3PwNR7A6dI-!4&22{Y"
    "RKpLtc4drbKyk<yWQNhaxc_fyo0H#rpd816ma>M&A12zzu7EK#_c4O#~hT8+-)*_b(Xv<IW6wM*mPC9663rwAcE6"
    ";)+UnB#z2%ue?8ngkXjefEIL%bx~g0HIs8`;mhcKuZm7TP699X6-2j0|cb^4yjh<QEbL8}v8v4M(Yq!-xjq-G#_z"
    "GyjW$FuNIqh%ZuYB}}5Off9fi;DyP=r=@hwTwzOeX0cRJ+_I=w(J;M5jB13u7&al`k81i&~s$ysdfDUWJwfSzBDG"
    "UWq?1;1ZRGk#fBtIED}=sQsMSM=PG=3AXY%J^#v2q8-$-bwwNn=50e7z>?xHI|H?}!*MPi@zUanXP>ylJP8vKS}k"
    "Ca4HFWsahCJuXm|T`P$wBDgHtm>;uK&Z)I@RQr6Nkn7NYtfod6DMSa#~{`YIeDzeP2$iSoZc_1#6KD%v41<QnYR&"
    "0&fd6BYvXm0?^g-~;~rFG>U75ERNe<E?CX3&68juz5zsBHBi>D-fehlp6nEI6SR##SPA)vg=+<8Q4iEk@Et_JqyO"
    "SEY@5`9|pj+-i+C7rddh5stqFwv3ni%Wi@EhWfA0KPhYxFxU{=ym`++H%3}3eFS=B_*M*Ctj}*-L&GJUmifwKhj$"
    "(_$j)Ffea8*)Ww=RmsM55XZUeR?oFCb`5b-KEXHXcA(xA?nl@yzF#d5eE;Mc?<OUhpS?Gt`=MR6e7?(yT<64w!Ia"
    ">OsGh?YNAybd4uqO;P(SaIZmn2VFxkhOISd@)=A9V>@Y_ynGaZV?)PEuPNJatSvPCLB|Ye%m%Dq?^whBnW%w9Fl*"
    "2sn%N54Qny7_O@QSj{gCFw_Zct|{O^)SML-xzI9;F3S_s+*QOh1lbn`TbDGF16xZ5CID1NunA_|m2CrgY=ZI@(jK"
    ")-!u>)+~_ECyN@zd=POn%<5pgHFidqAS$<XzI3+1BO8Fqp9J2b*O_qb?Pi_iFKK07)zXb9x?=zp=2YgB0L!Z(SQh"
    "QZE%!sP2>r>EfH*oAUuoeU=8rsuWnnd)$c!CWBO~gRI7R_Ug9+)Nk`0aX6N0kj+*oRPc<?O-q@XVmO}Q2vXcnS7e"
    "2c{5queqGdO}k$2t4!Xi9cJqrF3Oels?5srJ?@HVG~Ba2%DiL%W`o?qP8^76F{wimpC!ST7pKvaWjNHdF_>h&Z_~"
    "t&}oXHT5hFR{25&7T=2S87-b<`N#<Z6jEMzz#GR8wqfri#$x$v7i#nS-tq49dyReBj78=6u=kYd2Gv9Lqrt<7AD$"
    "AI#5oH}Y^-))9ZezvjEM6b7k$Qn7~iQ!rZWu2{OR=c2v%Or=m81#IU#*rWCV->=^D5@XS6Z`+#ogh;6s09i6~tR?"
    "&A=v#oSyk07h$3PP=w|>18_c>&0T$B}ONy$PcRS(B5N;vi?bR+!%IoaP0)2d<e-nUSH0~K&Ol?(rMK5aiK<Pp}S^"
    "wH%j3|-mVXVJ;l)uVma;RfXVSA<g`@gj6=JKJ_5_o{YBg>xc%YGY{rdl>CcFD$|&aeNwuDvZ?}*gR~d~;iY{P&qm"
    "x?QuyMM?cMeQ%P}9~;K1tLBxmsNJw{Rb&e`#ike=JjU4$1C{Uc6c;eX8abJh-XhZu5nOpI-e!V&0J%;Z|z~VWabj"
    "YR&&f_Ad10|A#g!B`vV>CAEJ4hu%?AmkMs*&KOStN=c4FZYDJ1z)AyKvLvw-I3VEwM9c_J@97u<wx%G+)8#_8r~T"
    ";bSddGd^9Hr#O^4UgG3>+f9R<YBF(-Bo5yX~!v|Z;Vpx3&HC(DQDAalOCGo8zm*J`v7^o<Y4KfZgi_3Yd3rux4vL"
    "aplc_zxTdc-|oia*I=Y#X0gZRon;8%v(5cuDFk2G*ve*=jj!mF;*6?cD<$@RO_csZ5#L}3bi<l5lLMuYwKXZ)x9z"
    "%&VC1Eq?^dCn18c`06R0^>CWlM2<zC^GE_IbEsciDoZa)R3vk0XbhP&5ZQ8lq?ELZU<JZsbamPrHx7(#IL-z#=qw"
    "TyXJ%&$2-$$Ekb)k?-=?;`?gIgIPbp7t)2e`B7tNln{#S8Y-<U5FX>Q7I55-qOH^n1!LIVRMX*59xW*E2TS@vdef"
    "haRcsGty}7j<8ylv#R>^l2BTmYlb-JzWGqd2v}^}?I39xFGil=(Xg=Ksx2pSZhM>xs`vVW4+}qBubKrZ2{+rSG+-"
    "(#1x;UPDL~KlgY<JdL_gO#)jV=3NEi`$K1CxW%qaP{&WS9=oo(sqo-2E+-W#A0GC{8;r>eR9huvP9TQy9?xK*bq-"
    "^bGUN9;$*ptYJ@+%2-Azm;r0|1SCF+ZS;a2a614m$^688t`m$GbkvBCtBzE6BQt+rUV8*k3a}9UpLLi-g%#93$z1"
    "^qy`t$(OsD!#yU%<w_}_qpQ2Xei(b_jSdggc=*C}|M)J<65|L^gQVA$8M;f_Wy{0@KMpGP`1XTrUrC(W|oXxGMAJ"
    "d%TBK;Qxoeb9)4V#eKG^&Bk8sRQ!LSh?GcW%I@B>*edEM1K?B*G%I;NJQ)^`^8fAz(hmp47$HsXXbfO0_2s{LfK+"
    "kFVa47`jromAaVX5M71W??=x!!{pLs*5yyrmXhcH-%c?C2y8xEtk#F14U|dyemQG}lt80t?dUVqEM^MZ-=TQh^>j"
    "_W8KpZp^lejUdkt3Az<xmEi}NvCqt4}XOmIxFt|4Re$QVwr_eTTL3uGIqY9|QMnTW&?c$v_%>xi~=bVnryP0;J<c"
    "%(~6D1WmsJJd~yo15NH!)l6}XW;lN)gll(2ZFo_=bgc?(?MwcIjHV$<NE@KmSBWkWa|GdZXt3VgMJBjXu|oaCPo3"
    "e8(caVo%nu~&s+4PAkQ~tv?tT|ws*u~0+md0z6joh>pHH@qvP#YueYPWPnQ5Soq(UF|LgX?@mbU(#qAsqz>$5r4M"
    "355KSl?Kr_tbVdnczS4909EJ31Zw?bL>(j9pkbttRm~DCpqL{(j7I>t1bp(9I98C9fqdrHA$oP6w|B#|~=d&QF7#"
    "pW)PVtL;@+2OqiBC7W7`TBp7eaB_GY?Y%lUJRS(V09lI$M&Qr!CgBKx>#+;}dERPwue0Cd_9u78T->J6A*BIZyKy"
    "v2TUw!#Pm8^vt*~>{UO7k`Em+ToJWlM4Q>C@L^kh3=Bw1Bb4~eb&P1{a9rbXo{Vcuz0`ILhyF0*ugrF4<f=T%h!P"
    "Z69YA^1Bjvk)#Y&rn)`_9+K=G#$_csuqA~)rY%&W#GW@j;jHd7irz#e!r?Z^Yqr`MQ}H<fu1Vh07w*I3m&U{iVVM"
    "&Z{)>6Bd>WW`{>DKM{o;K;?vu9yB)TD`TfFgO!zn%-@1h~;4UN^Wmt6Z?6CF2eEL3{9Obi&W7l`I3>{}mhz3;%8X"
    "^MQI{sydzFSOWl1N2NXet&{Ogm*lk&*yt)#+@a%BGA?OTnFjwN06u9YM?9u%P<DzOa@D&nUnW-fo@2@<@eSxw~#X"
    "MThEIR+>I0F}W^yM+bzHzTw<tQiD~YJHa-5L>d^`J3#8t<{5}*CL05|v~_mxH;9kj6T4yPFdt`E>G00AD6qwFp%j"
    "P%NAi7V%i`BlFCzRH3p1xD1@}ORW#LaJaXqdmgf~P`#Ac}sIXk4HD31u+@K$%&870{Tj)qM``jNb(yB>phTGV&i2"
    "W*0OC!@&!4u;jV1A&b8D2=ActHG(aGQiB6O#h)Y<iU5F&&uIEBJ}VD+kaW5EJz8f-Bs)jWV;G=sOdK?k7yXb2g9C"
    "l_435A3b)6q@bk?-#vuL#uR$Acc0QwXHqpt8_wB0Ki*jSEoWS*=ZN!kH96@60(BW;yN+bf<t<B9kd>bpHFmP-RRp"
    "cC&%}?qoWy`DGPO_Lzld)R*v-Nw+`cC*okgV{XkJY$YUw-MzVl5<?O@vkvK4Tu{K|+eNw_e)i=2_cM)~pJtxQ`n}"
    "p@n+QNCK-fvkHDD<=IG48;>So3YJtHDn|Vbq2;<d?GJsIb#^^jG|*^uGdI+u)eG)qt;tGDuO1GLKs26<Qs{Nn>g+"
    "4lvYct`5VSd*4tnl)kW!P$C0JV2Bc(Os=<wum7701l3JhV`+Jyg6T!QL<@zr}`TDE#=ZLZKWyewdtHW&Rpcn<&gq"
    "E|hwYqIcUzgG^=E=3tlM|ZAckcI_~X)tPARG*rfx9VVN9Zw>BjQxn!@4y^WeTZ&Jm|V8C2i+)bD;@lMg+KxBT>gW"
    "v44m7wg#{Y&)~?DKC1I{CW5sbpx!j5(+v~}N_+(AN73E^AekHiHn<56-;cHk7C1qr71GIm_4}=bMbWJDM!{j->d#"
    "HTa>)I%fN+LaZ`+{jK(40R0_p2>;LsS0&$I7>5Q<j+Z>sR|iIS<Nozm>Ywt{MP7O|Jh)&Fw%2TUD3fI0e(rLJN+&"
    "FD%V}XN!n`gqB)%6qxDL#MIpMS1+D$iKVO_-B1dzPLH@U<(KwZCZBTI8AXkjsycPVv4)`;qW#8w9e>D){W?<|7Oh"
    "s@=#&;QCkipN4WTc9Q!S)H$iX&peQ#1xKp|DTiuc)F;ggXzm8)hlB_C`qQ+2ye+P_ncA8f@o*nB>g39GyNv)Zy`r"
    "#A2&ct-A)F>;mK0z*?|#y5GxavSL50C@8KgSTPQY5gd8u5Sfo^(q4m+;bg7yp%BsJxGVy)RyDHU)2}_>p2~MA~Y3"
    "4&~ESS436-ge~|C~Ty3H}5b>F1$jRPqdjcfG89S`R)T!;&Ia-+BC?}kuit{~kV<*5^>YQKu@eJK!oMp3C@OZQQ>C"
    "jnj2s9a?<>cV=8dEi;UJ=Ip6LOf6V$40B&9Zb}bSvhHeMWP=T#Tl-lNJTycTawLbDA9Q{(9VA{VoElwHivfKS^bP"
    "WE;uB{Cz84zt!?$jlo5v)(bhkvR~|)@Y!z+Srs0D+lTP#w>^#&t%C2<KM8&!$ogVGmjEFJ)R3RN1bp{#)zkB&)Kj"
    "5el$ZcOmTdXQOc=oo-6NS5-EB_xJi<GzQC1A+IWiyjlVmg<CP~|VwVRGci6n@sj_q_Ls|0!$qJ8@qdZ4$b_JUbe1"
    "XA+K>vUw6U8c+NqW|5uFJ7#8nYcaekFTn*nkyZmCN%+laYP86eL)LefEn>*MNu$2bs-%c8o+hI2nf@b%@u{|skly"
    "KNYSpUKb(Ss%}s^iKTwQ5gR|pD<av$d6nocUwCrf+vg+y6`{f(4H;L#${L{J>)Oqx1@K$V32<}6AT>o@FjA@PhWr"
    "Tlluz+(&$bj5}Bq487lE73-675H#nPqadyzHB&lF#8}XKCMNw0(u>P{=$7OBjNVfgZV-PT!-y_P?_Ev@^Jwji+~6"
    "=D=4{cGe!|^Jv1FSvq{Lz6`iIaQF>T_7T{}#a*$;Zeqy+L!8%1w!jQsgx+Ds-!*fyKACpXVv(F=w~5Zist0G?1~}"
    "1JQ2*ix6KG)`9A5qk$$bw+Xnm)KR=oqssxabez_+^3yPMP_Num@oUVbZJlUNUJ$-H~wlxAI~dRkYcQ_K~=3FeMfC"
    "F?5p7F;;16F-tyNBp({L@7EypWQ94ft{h$Q|ISCYMtMe!*L#Ipt>A;jy8ZNC})G;^F@oMM$OzHP*}HWgmRl*<!T*"
    ";tiyC9aHMAbDw&>uf>ky_bb9!D|Dh0ji|Gv{;nn5vRWu)Gl%{P})?or=#gVZC))8YsQG`$J4u0Hzvwuo3h$lwQKD"
    "v=hWMj|f`DB>S(s2jTcO7#Y96966d(L|TXw!25L&m2<WiY!r#5MO+Rh}S+R+db)Fw@R3o3Y3CYM$b$8(d*X2~`oG"
    "AJ@sda<UX`k%#wN(H?rLwlQS2czMg^_5esFw*pa(>F*p#S`b+j>rcLmM70Bxh#Iw|1WH`d7J2S5S_2CwRhfhkG&_"
    "?G&^SyI#QZI!U1VrAYL6;suEgkSReR*Q$88Tld}X(5ixWT<1E|odO3QP#l^$ipGYO1D!&Nmebv0njCc;eMR{zWbc"
    "p}@7^K4sQEY1}3;3XW#gvempWhzSqRAGxICg@i9>1vgG3mX&VguiA*3P*IQSN^ygr(43BGMgYw)iR2)#i_$ewfl{"
    "1Te}p{_6b$os*gccLUk!UfZ1Ms(c$cy!2n$3qr+<8E?&u_GK80l%g%Sk|H*jd9*%K}N8?C&M_yFv#aKOOyUo6c^z"
    ">5OyKz3e1IH=DcLUfxYCs4rmjG^D4Pdc~T`Ht6D7jk5uBmq-L`{P=BAwqQBeiuJG6-aZv3Xh1Rb5jM1o`;RsTWYU"
    "G4n($oHvL#%nb4~dXL$K&#|H1ZdY$j+UIt02tAE>?h&HhE&$$`q63MDMrtoLM@Fc{bZYqt2)VxRA0Xmr27{6MY9M"
    "OxA~f=Fi=LyYeAW&E9MUA_63v_rm8<7*AEXTm7b!3k90eitC0`!+i~i*Rx?;(H6M73nHd2rI5<P1FbGoq|Ou=Czk"
    "<m8rmkWl?bF|vZg#RXxLtWw^nd6a3N6kDX+9=6SmFSM2+8|T-B18leu=3?x?FI=Zc>=T{54Amq)7f1Z$sz#!%=Yh"
    "i%tXrF^g?4o0I(OrU(r*byf9ANvQOnwH6%r2gyq*1UL8jaLxKMchy^NG1oWo{GSf)V79utL-(PeUTdI(MW)pD~QN"
    "%f702MA4g=%#nkOtqeZw)@>+}L^{E)6da<;A8Bc87(6GQs4nub(B~zW7dKv(J_gL-szKm|~O7XV2xEi*%d>pL(8b"
    "{*k}049NTjd5@ubE>Oj$-7MmoaUVd~O&cI$24EMA5>XXcuha-;+f$%*;PXCwVC935h`%~vX#&p2tCV=>$bueIn{?"
    "yDK`Kr~%bgIcX8AEy$*t9u)bQ<I4VmGms(xiWMvi|c|NH9iGRh)o5(Jj74%xwqWoVd$vPCV~j{~>O1c<{~6h_uV4"
    ">(dBF25w~m1&cJXO08QnB>+lI(X#L;zk*VJZjjHG-yTTsCoUTZ1+~h@k4d5uI^bY8^U)#HtzgJ1JG~~0v5&h{WXy"
    "^fXxZJc#L{ir@+bd(HJ+Y)V3<)7?Trw!UzLLgqV%PR`{g2WfUIPg0#G-XVBp1)#fa$`GZ=&N^O@Ev5OdFHX*QkgV"
    "wjKkM?-EV=b&#ub#D%#kDQ)(k-cHd%Us*(;tW9>F|9|FYj;Pp2f6$oe7-m%~Z`OU`6LQ$ZE;#cl776<S?)ZZdDVG"
    "7w|q<{TA#n;M59wzVS=NHS8n+E^p?&0~r|5uyJ~GF-m)Gwr5F@$maSv%VrVLf)v8=Dr56fPMw+I87a#6h#iP-iT_"
    "<~fG*%^ox5|&{6|OR8NH@cL7oC?yK_?@4;v<gQVeD{+MZwJ3)rY(nin$tOs)z(Fq|-(sS?Nz<JXQ6<>x{>;)&9Yz"
    "qq&tn-n&1iwt3Fh+j>KDbqdWi!L7Aj$s|6<trVfvxOvJe_$5hc?RxRDBxB#y@S$3==o4sfGvq9dtd%gN}8mzrH?M"
    "vbVc6{26N2rx+66J@JCC8zAa`-IvVFV`1svcJNk-?6+P+ViY?L5p_#0Iz|;lgqTiL?Q3ka!m5MBb6z+^*mN9<HN>"
    "YS53=3{?-LmveZ0i~Z#tO@pwX-nyxF{(lwmKuWTM=80h`9~1Zh})s-q3K@HAxACI4z#yUMv}1Z3PF#4p%U>?z*4X"
    "HM_me$C)!O-^<9^>es21HLJ^H57d)9An%@>oE{z}$AkZTGdRH*5RcV@rR7h3Eki5HJKcLdNHFQd#dkud7>JKi)?L"
    "2n5j8-{i52AW)*e}Y<ILn-LShQ{hr4&EujbC-0i@#wYHH?bA8iya++E-0lYzBA>advkfCEzO_hpFVQYRk%JU9r{t"
    "sHp>W8^Fsf#4SVejwgT&u6U?g1e4Cxnk#Rj4B!9b&Fmf?hf{oox_t*mm5q5vx0?+G`Cx&AU|nCzpfFU1!_&Iulgk"
    "bWvG9j9_mWcPmu1xp5sPXLv9-u-@qLKNzt0RBXckCFaR_<GS}DARc(1nBCc@|#L+2zm47j|$tsOOL;2(O-u`FQ7q"
    "Sb5huygsg4su`iSnaxRrkz_dh8wivc12zo4h&Mel>6>9hLP}=nFQJF*>h7*1GwKQ0>vgnb2#frq4=>PQ8Z77VtN$"
    "n((_#`|51cg$>rcARiOnTG5E(!4W_a>?S+g`}@gWX?Uy!{VVhNKN)Q{Ew3kG{dBk=Qu0ve<qTqkv1H3<NQ)cxga8"
    "7x%bR-BQ{f5(rk|zJUmxucD2|Z}qKIpZ3$-t3k}h=D>H-F@k4}G6OX1P}Zzb*2_V@})BU@I>b&K$t3vuJgwZ;T{j"
    "K#wir;`5Eusqg+&x8ojV?n6w)*7hR=DZN9Q3=mZw`mQagGipDaSdGdBBN9WC)Sj}n9yQRCh3Hj%7bk0LD{KT5n-a"
    "5(W!Kq8_tb!?nW-%fGk2N1}1(l=a=b_Fr<;PbcrygInuqtX;TNbG-3Lm?q`94o)!l8nMrcx=bgDlyDT`UUIhxh7O"
    "->J1+JUp5Sb{;F}5yIP_li6u|@1lx7DFd=8!`^N1M0Dp=K<f13*NreFRYD{m;hWvb#x`kU$eP^7R;D!y%j%DRpL3"
    "o4b*A-z`FI(J`tAsnY0hHilcIT&s~L)R>&c00;7jGpWyF;4FFxETa++-MmbDhz~C>K~0`qPiNdYYK<Bt0Fv0eKpA"
    "d>)UE0_RNFGuM<5U2pqgsyvO$T6(G6+vCh+J)b?wFU_gEiP)9uDZmIx2zsEIhLVk8ZUiG9=15l=xs!xU;!z@@s-?"
    "lNn!D0{fL8as<N-Tlq!w;I!XbfF3tId0*{o<bZ1$|2!u=@m(jN^5k%mn0Mi%qntbf_-F}48Q>kdJg|ki}6(1{F4v"
    ")Txl{o-aI+{WpF&$dv%Z~lkVU&5n9|6MzRJWc+&0?ur@3pPta6=@*Dsrjwk4sv_tn~Mn0h<e8MLFmCDC_Acflx3T"
    "w44#Beq{RlAgYNJZMunOoN0rCoM{s*3qy-ZK2jSQPrER9CI+B3hK-zf9u{>_Z>iB<&misMa{%s=e|f`}?nxAGS{h"
    "$(!SS8VW!s?>&90vBi5^ThG6K{`3RnaK;ZP9h*T#|Km2BeEq;;wvYCbp9jBboP*f6a8k9>so@7IWHs6PF0iCM0RE"
    "%YwQ_9V;aCkHp#$yH;QQrM9*tYtr#B2>VS`~md2@8Mzc)Dc5FK<G&f!-;IU^fZ7@FQ7&uUYT5o@?%MV8Ko*9lQiy"
    "HC+H7*Zs#Ig#^iLI@XpUorrNRitzoy$FHp$^=#85xN6_<sH2cmG9@1Vx~4}oe;FR#sPr^F8IW~%Q0!=>3WV}cK=$"
    ">2Yei)JVJNkz?n8ZUB2#AprFOc!TJ@+=6eZ+FWSj5`Xyf5)>RWH+XuTp9R4lYdyPBt@EpX&t8q~$J8A*g`ANXg^q"
    "RzVg=n<36~*r14lt$vba-;=R!=6T>QorK#ZnpDEq8gxd2=(IsX<a}!t{zq!(51^8~glkTkj^&Lk?yx<`g>FetQRd"
    "r+eG`d;dk7Vc0887XsXii~PL~x}${W(oBQl<(vKT4Dj5|q9z)nsiskYUqNfIyy6U5?<l?I{&4u_fE&61SRrbvknk"
    "8fY$r=y-{))GBg**IEhkL=^5hQ9XB&k76AWMeSfV)(_yHS-<v~3Tn?XDvdr;4N(opJ>Ud7hmYYvkp(pO`O6YGoUO"
    ">wCbvn*z-t55&b^YCKmq%mVDzyb32C#vQ13yjh%K=`xtCP;J$+0b;Gveuuyc$REE|E68hEFP3FrI*z}RdCGNTDej"
    "Ji?x~@bRyW|i9<1heH+HcuP1=~o|SjAH-Uk_!wn!6ISEd^Np+U-f4&*K3FHwQelIDyDH)m>&cIEsFp!>8k0OKb6("
    "k36J{tWUa?yzYjC0|{=`M?!xj?RFgXC`0#(ouj9Yh;jb5#y7kTqDKeMf)UpeV_T*jgPPj!zUAZxDG8vZI;@83%TJ"
    "hVMargs;h-8z#22%l%qFc;!K_tdi)_4hOb^26^a)+y{Eo!`|ait4n7#hEKU4l<2C-jb^RA*6MPc%_t0KH_Ye>`Up"
    "P>^ayjIZ|WhRK?&}d4LTvjHdPIdqP-f+{I-d;!>ZxF<nyPALA6gHc)n^eks+^8yF5US4mHZSZ?rO*(|!5}+!)#!("
    "??sanc^+YA#Xg?zWu#%X3*gu(piVPu%c<7sacgx0_RYNiH0l1&Xy*8mZT{pEw_ZWRcezhCRH-0x!5^ZxJ1k@Il@A"
    "fx=KcEY5Wy-0ec6p$e45ZF+CAB9GIqRRr+-~sp>()6mK`NK}C1>P5@PWH&9W#tKL09XB_wkWGaHXU!+Pkjr61oEC"
    "?8%<WyDHq~z@4r>is!SB2M4^da9V`}XpIMo*QH!V&ribIz*go;<Tk&pWbwGo4TTOga6K2x#CI1<qm-LQYI+I9QxV"
    "Q+zScv&%A<Fy-Nomb}{QpV}a?uGCm0{;~t7$Etd6lD=H^9uCg75{6B1>cy+(UX96kvh&km_sxFLYNX@3MuVg_II0"
    "K!3El}T_RZ-|;2B^&R<@VYw*2+sG#zKfFbnx(0@J&R?3t%Nb+-R~dhuxUoKj2Iv-lYQMtzIk7fZ~)Zkt+=+pLju^"
    "b@e^y@dq2-xn^jBA<zFR?T(kn_Bh6=W+nIHdb4}zzPdFSBvbXKqPF*;WoN?xBv(#Z?k71^NudM>p^AZqnN`Jxw-_"
    "o?g)y(Y96XBCv3-e2PZoW*ZgeLcLiIuI}0?ARP?{GeY~M1c64bidr(J-x|Rb_7@YQx{MIwvQwWaw-IGu4m9qcFxO"
    "FLWSyjn(*GM*Gc!8>Pg6MKRd$qJ~@`I1E=e3;)fxEQOB8EXAXV5VrLja63pf~NiTU_cDY=T)yLZNLXi?lWe0$nyr"
    "@ba6RY?Omb0DUx%1us@2gvTidXrUyk{f*<n_U>;Rarz<6G3Y%>FV(u(-wetn6-pp?Qos-U;P~C$sCi-gU>CAJTRd"
    "%`4oO}$9}EC%yE2%?@^8iMdQ9+un=D|_VK`37gtNq`(hV10!)StZl?VWC7R)&OR5SaT51u>ninWn&9ee^S*389Mc"
    "JICTCi&*;Z_81~z+MvlDZ<+?R{K;1(+?smvr!Sfcpm+n{}6Ur2l}2)*_)WCA#G5t32bCU)gYgZ4?X04=Zw&ML~s$"
    "<XT`t#@7Edi9*Iwd;%QgP!2(k2{qbKzTQDGIbBxPJ))%5HU^Yjf1$?CuoZ)q|yWLfbHF?`tnvqylLVA>rV5rA82R"
    "lD)AH1?0F{RGu)Rr0xm!4SPy4~46*ct5a*L{4R-DEcx-sG>|NB|CrU~H6vxw=wVg}*4^czB=P#h$&5{<4mQbC9c}"
    "6_)zykkP8<DjSSWt3rJ(&7g-`)m3iL^*<gSzdAfU9UN45J<ypiXH^|<ZsQqZ+4!dWSWEvPrroYl_^{Kc=m062p9+"
    "_~?tb%V`^`ykvq=#aJb~zo%%fw7-_>vcvHe&_faT<(CIZq)cB@{|m<ruSo5~E@@qqIie$R4{>yp+fM!gHR>5UaKS"
    "EL`Zz|IbWxWLm*P=+5eXH64XE#Bv2Wh62YkG~be;`_RyElDk87bm`4^r?7o^v%=`pb%dJ{_wn<rP2|099~bjCJXF"
    "Z*cD0rU0!$~MSvv~3<T3|6BuB+88K(*b|ax9R2L-0lB&t2vvTMOf_9}uhhewHTt0hi1o<o=y}ZN6>4_|4<+zvY^w"
    "~Er@EFcF8>*xed$FTFd*uo!UJpwEJWIX5#)NfULZ{oW#0LUMkJu_GunWIp0*Df|PdE5N<rzM;14TpQh|x7j{{-E&"
    "_6dGq=FnnGjSrqb*$;f0;l~a3Zn+c6hx`tTwC~{y%sIat>ac!UPE22h&eIZQHf7^J1r*{r8eJztW%Ws$+Dgz_TXd"
    "QK4sq$uXDZ#rw1_nIA@RShhGPMp8VX1%?uxE~4{dkBenr$$V7ApXN*D<n3M-^j%6=$7u3?kC>AINCAOcB(?7M>xU"
    "N#4KgNpnLrb~;$^t&f}ul5d3<H-Cx9UQ;*Gg<g9{R6MYEQQgRNe@5V#bjVVpGs9{Wn|T<+BUyB-hQ26I%I%t>H_1"
    "JC3L-o1yi;UexfeW&=0kP|4o)R**qUQ@y6iJB#0yIBQp9R*jPs=Q}0jb-MmnGHDCC7O;AZBvx2I~CsZM@;pCq>15"
    "B6NZh#6Q?Kbv_lwK3~Y>&Cx$t>p>n`XgLP`)v;7Qo=;MS|nkYeIoxqFtT7uHdJ5j4*&T0uWY!_J58Vtq4-^YE;4V"
    "1kvr4p$jX$iJvQ^!O;OG)2(j_&3b)LCkNFZu~M-ddja~#F^#NnBe=)9g)X)4+kn}zEUqhvNa}<mI9;56fVKnqY-_"
    "8c46u^&N$A5%H6U|1$AN^ohW>cRCr<%(U$$$#i_}Ze-a*vbcysXc!Qrn58}Y`;;9z&};MGREh9MHEI)a2iN~Uz>d"
    "$lrLH&dLH8ZS;z2R(%4te$bo%^wQ=4~4$uLfHWw`de}^80?-{@$vU-$;=ng_C)m#`}(YiON1{W7_0YmUM#AA15^b"
    "bQdE=(YYDkvB<ruhPo&DaRK`X(I-ILD9?(zVYz=&(>0NZ4jYr)|A~{*2R%w0DsYe#RdO4Prr+z5bDc)9}4QRD$b)"
    "TaH8$7q_pk&>nkI?_zXq^V%SWCyc$2wjhP=j|E7ze|#`YT9IE5yHsY>XuCkz@;|cte@GP?O|+`1Z=+Ef>YX59A6h"
    "*sFzi^@1JO_E94tT}L>Z3g!C3*i;C^WN7Q^Co6@ui5Ptm?N6@&Fc*M3E;2l)BiEmL3m9MkZuMqH5KNLcJDg`2DVB"
    "~y3_N7bd=8r>Q2%PnL@+-X*(0_#5TU-a3IgOC{qrk8u>PjKZZlySJymPyuiKE_j`<f008vIil@wmvI%82meO_$F("
    "X%hVls9pwr|XET_*NtL(&5pObqG;vgJk;W6BywBGs6)BOrvf#|CVP`%ezRm%6?(E!XqjkK*TUX`~a%=riFHgObgk"
    "(1&CzG2vcB|512oxlDS?LIZ!2;kSPcWYUuBlgO^T@h&Yl2-?#KFC78-^nDyU1xmf1o5w?fylq}j`4)2t$5<nH;(%"
    "cl<5J8SzgP}vvL1%c=e3+@al(X&fP>S7JIe;c@BH&7OqU6gZ+A*G`yIu@vC=rlCF3av&9b6VDwC1MBcBM~vjYLNY"
    "j|p{(eKa4qk4Ltp>vEbHctKA3O1I=xtel3)XHcQq(K*t;IdjwGljg&0jZ9N>=u>{h_PAHvwfxxO2ZD~+vv~E4d_n"
    "=-N)t@Lk)tL)5;=<gv)pf0j8}X*>AvNhkFHV$z?x;vKyTQBJX$t873nMN`3PNgsxQZ5++r0Fol6IL>8Jy?Z8T&jN"
    "928KRV&{w-4>qw{HF8E_QBr%{`Sf)qO7DaquTRTG-Q&Q<kOgOyVDCbPnW8RMCAMCbSJVrR_5i#W5MQ*H=b}P4wv|"
    "=1c?>Rr|@NTC9}FJaLGVjNXY<MvF5@6(jXE3o+O&j^VS(`vqiMGOP*To7mn=eHTk^yDDpV1BlqvKyEWg?hgfU9#f"
    "LIs>DgNGa?0db>wJ*T3fFy!<NsB4FV}7$234*3mZ5T4>otjMERh2`-TL*5%~jJ9F+DmnsY1DoXPe39%2G7qM_oy)"
    "3X%B!3d+V8&sSE1*cV4jPsyy(iDs2uYvd^N3)S&Mi5>}}<YDjL3}+oqwtr|5oSNU!2G@g1(Yc`=$PN7z2|(9Dhmu"
    "9>%Gs)y1WyYy07-`cNSsC24EF>xFoIUR+{2(MCXa$>zU2*Lz~ooVihh&+PJfi~QO?RsefB%B-{gzva6C?LQnL>!v"
    "IXQIyo~%}kOGK6nJ@EfJgQjr)%yv*QM4F%x=;T$Lu%uY2pg?!AeEizV<uW7aY>DMO#n|Z2E)Y0X2G*5JGkgUSZ&v"
    "7ag79ftDxG{t6?ZMm!hv31<FG(+h%to)rq+-@`tp@7{Y4@0cdvB7CVl9!~vW<4ysxP$Ko0~iy#RTyh!_VLeW3L@C"
    "{v`wo8LTyjp#$k}Y(8^>Jf!L52kYP!1Qi#{+@`1PUA51VKCyZPr%`^?$!jJO4a`|7>>tm~_rQZpJUZzW)!cQdn&2"
    "-{0>1mwLMkuW!XKo?EYjjXYn{D7t0b<dbBaO|BN#{jC^bXZhE6TYr3}Jt1`Z%=r3@08Z}<x7a0G9>hQ7l(Y4sZM!"
    "}=U~_cQ(?bPQpwO+0O-IE<S;2o7)8%|fKRg&Znkk1u07%qAS$Q75<TFy?R4?F^1w4*J+CSt4;$3!ah<2CN0%Hx7X"
    "tZ>QCIu{UFez2hjt<}`0KD%2T0hrBHP&PNzPkO**0a)G_!QhjavJ|lst??LCbw<>Um&=E!St>EK{bVrg9&Wv%RnL"
    "P1ZhheTayTFeZ&b(^p7`fJ<4aC)L0I@rf|SMGK=eRv3afNc+-QF=6nFDB|@&MjwL5F)PnGbqmT3H?c2>WJDEz}xn"
    "CW?!PT+*c$m&oC6;#)p66wwm#TZ_KsE<MNsbYuCZ3?XCCoKm)r+MVcf0Q()SdfkGuV;P?EasfZp3S0j<Df!USLvH"
    "gL>^9oD7anqrHRE!*J#F2XQ*lY@*2!bCy`U6ovop$uHacZw4n(>(4R&UpcL&cB001W^Fs1;|lIv2>ip=cGc>zP*M"
    "O;rTPJD4OtcON35sV`mSkxmj%G1=Y;=#)FOnDkkS?tH7W6ucAUIl*ZZpMUG#64TPDg{hov`A)xK+*ZJ{}=%$D#=H"
    "OV5%ejkpPqb!<^;oSV@CY=LK2(H^?>j+nv<_aMlkMLR+u|n~b{D!L3x#I%@4$$HyX?D)4R@*=bETp(PRXz9$!aai"
    "*b4*T@>1CAiQo&TT#L1YBkttnBKSpR@l4>t=d#s}?8%&|y0U%$ms~gvx(hr@<YEhpe6abH|{+L{8M`o^Wg{Jc1L9"
    "}yt@Z<j8&Z$|;b`K-gXrQ~KtiJs5)mHU%ubR#FWQB9XiWv!_KUKyR`feIc!h6fgu@##DrB=@&C1CSAn<FKTzC;Tu"
    "zggZ0A>Ff0=H)>P%;hZ+c2<tR*aA#^ejWZ)t6DQd06hFTIIaT=KTITMeZl&6hpHu)YT~v8T~!~OO>YY~MLCe3yk="
    "^$ot9j=Le$NTvcRpdB$|tr&1Fk1f*!DYd<y)X#So7#kZ(!Z9n_)!A9iSqo*-#Di@s8|i!cj`uCv4btR3oe_pDMWa"
    "@7$~p4wNw&y+Pzfx7BKFKTt%n#2)bK(f+y`)!Yf=FGO&(-8-=d*r}20}H9WV<1ri%nBn<SIcp#jGBC`Oz)$^lfA!"
    "1m*eyb!k;deN(zg+n{hsQPm95idp{mVa1dPh_V<i<026+^)ov=z^m*EMQ$7P!r7Yc4DGXOWOpbRC5B7hH{uQaUPw"
    "lVft!V*s{V+K={PA#q|L|9spquUB0|%J=M-K>rlO07%@dq<XMps|M<W@>j!8)|Pd`R`k<p>`#Z{liSn+?m<L?imf"
    "C2aItoEr=6pG=+jWhZhgU35>9y_4g?tCp0~EtGy&Yavor*cXfZpFkP2^&<KDyXQg7y+;_D>I`4}u0$+w6a)uBK+k"
    "0GN4=mxG2p^zR2?!)GGbjVClr@@A+#C5f+b(`BD<R^v4?p?Q8~KJJeiStSSF&IbYm|j-n>NDg%Flwr+IT&0AD%32"
    "cKu~Ii+cGWcF|gzJX16l=0TJZIQU*%2ZedAo(~roLUdqFoG4h&R$Wf;HiCbtFbji_75s|_Mo6O<ZE{;^~lLKa@4&"
    "QCF}BoN!Y}A1RKRa^rdDEwud+f{4ug#RZme$$x9k@Wr<F*+ejZJJ;+=;JdXBW9UQ6-@eDWWtQM`QoN&aokHs0`?X"
    "ucy^j|Dp5sO>0ODSqNZ2*yu&Ypt1FIm$h*NP{CpMPlP0?I#P@RDsrf1-fLQMcRGh7$XWCUi_3K?Fe|IgeLMH3b5`"
    "ki`^t<t8UnvJIWps%-oaCh+4}KQ+TtI}60FF@Q8=YgE}XI$_cqG&_PyHPm8gvxm|dJwZjKZU`wG(idQfJUeUqW|U"
    "=AOGt#1Tj!`k&&?W_J*OTcs03-)yqH+Uv)G~rM4HUA*l~pdx@Q3nQJqGFUQsFc_Ze>IDLIu)d!L#Uh1L5=PYY3l6"
    "oJRkgHemUBCPJ%Z&=cFz}yCdLQup)$>sG${n`h*jL$p>_&tKdqMI2y!mj4*Co7hDh_t$Hu`=?rDY#QIHDz^j(v?9"
    "+6D6KCM!IPjtLNUc(YOmcxf#ngJyfv}!h%4xtL>q1{1Ehs7z{}Eqq+`TjUIh8xG$qcMvm4T4>oxDFe^rBmb10z4x"
    "cixi{%AuN4TYE?*XGU(?*l~1kN*DGHHICk|&E+dxdpwTA=>HA|YZDoa(wlwm@Lr9^`-i0x4Tr?zl6c71jbPoviw9"
    "x?B|bi1IYhvBc??qp1z6`Gux1Q}PRxvqHCSrRq;$rHJHMs&fma-p+}OeE7cWf_w+1^A9GKJ!nE4WpjYJQ(x0y>$G"
    ";Ufyv|zuJnwS7zAZ%y3&*=dy`qE1RTkhp9wWe`xE`v<u7eLM3dEdf65q_wl9b#v#dEIb_4ldS1U_hTRb4*D6>788"
    "uwME4c|9w9J@OkIE^S=oqv4EoMjL?>@7&RzhG2p@g>n-rLjLrt^D9dvI;`4QnLB{yX2d1U(`?ce1dvfTE@87=3Ej"
    "m`@mo-dr{V1|32LiY6svC8m>4ppOyL~$&n+|w$ZCRM1E90c0qT2a=iD-YNc>@(jsEG*3jeypcbkgt-@buLa9eD*h"
    "kK*-bxH`g=cb>%L*Hvm0uvKus*;}FuYvG*|4B8{8baj3GiXmIDNGH-#8l4cl)LK!o4lYwmTTp9>s%9lUQ`+bq=9K"
    "ck7sb`6#9`>QE>{o=yR)+C4lNxbSuaX(v3(+UG7Xsx3jflRN$={i6V{aIZ4$c(Wb&Jhx`=Bsw@ejSk-I?}xE8V?4"
    "340VJP0;%^Q;<V+!UOkC?s*xq<RLQs*7T0A25jIEiiA44EvmXxFgvk8VKsF6sK(0mk@PVigdnUr~yWB>qUdf#k4t"
    "9l6z!vGo=`_{ZHztzjnlu8f34gR$`W%UGd1<MPZvR=@F?giHuPvHx@8}_YzDyB_E_57DoWQ@<9)$xhz7i|u4cM0<"
    "`F1T=TK*`JW#23+DPYw^%vYOt2{RH+Pu8P@2Rb4GNGi{6&-Dp?ypyD2f%szB_LbC2?+I5zH%S%wkJ=4^u#a#hxb%"
    "DeSqjBFo`E9zyXgN&UiEh#fxQ?J6%CMYuqc?yejbwxvyN%J>M8Bmh>YHql54(Xgl4Cj$0_#zkAr$D1>mn}Y;H{EH"
    "M`zLL-cX$}#f}<|)BFZ}Czx0g_{y!a;AcwqmF8Dp0ux^u<I03aJ9d79`vD9X?nXOAQX7ixDIg6Jr)?Ja#&itdRwc"
    "sBCMr}2-@<m_rowo7dhe7q2B$BUK#6!b6dbWVeAa+13yP3+Mu?`UymQthxR6mK-Pl59!E_{iDU#UcScucr_%K~zj"
    "H6{B2Q;o(c6q6qQhb)^!W)eGTfy!MqJ&X)nPIS$OI0C*adb4FDxsZ@E8_sYMNgs>LHJ@0;t-DGe@`UgUv#TlWRpu"
    "QAcq(_yplbS5YxBg`7p`QN}6+F2s&q~uMp9sJh&+#6tK@o5+y*31k&u11f=`YkKeFQh1Bh?0mA{>VW4ft%T|qi(s"
    "utoDB#W2E^+fAbihuFoVK>yU6IlRV*=d|lUR9+vZ-pYckD`ghiDe<eD(YKuGLU$F>FASCZ*C24qeTN9C4X1$Qc0z"
    "ORKT5R+y@AGs^6c59Xsxi6x#vpl4CW{x6_9)J(WDq9EL9MhcX?^}t<T^AgN$rKHU}m_6XU1&@uVQ$UP_r((gB=N+"
    "u){sgmtU8G!!l!2WcEF#u%oIS6kK;gP>5}^TaX2Fd%=#QRgj^h1NhiRnPQ8=M+&rLYHCUOIE;5wW*#k*_hOTC#!S"
    "(IY@>7pYy<N*%dSP{FSCkW((T+NlJ$Qi3H=aZs1UCr4t&rm<Pa}R+PU?Bt-7N8MMXJz8J3Ky27>y9)I609|<Tf{c"
    "NykiND_h&tEf)JAnnO^pVKlE`Nn^i=wuA^Knm2-|qgQ-Xhi!#PGz}R5cn6}M~FdeB)YQ-Vu6TNW)L!7ov{DzL*dc"
    "Txlt@q2gU3uatA8JeuxSYJ7Om8RhqUZX<qaF)Vnx6vi##?wdheQXpTnu5sQyT@RE-2J++ZSjox0%itCy@*<vDr&2"
    "p&-AXX@o*Ru#mP1E{J8xUX}>~_vP<E9=5cWvub+y{c;wrA<Fb-e%VgPxih?@M_>JLR7nksdzFz42AQ7H*cgL*lK0"
    "u2kaKgKqgpEaL~RWwXAcNY?a-_6NnVR|7seWiz004kJ=LQf5uBVBbjpy^*%Rz4Fv>Cm3)PH}vOMuJSZ7xgNIL39+"
    "X&uqffxgJsg$6nw*m(9E>%(mTNyq7Vv57(%X2l~VTP)84)dy_z1?mFvz6vU`=*6|9&EoJoE&ZMAWt=EG~l86iaJv"
    "LORdL_aHPKZneEm}E&!bH7AI9Z9CJ|OOv62-)jZXO$Cx^bnsS113EE3T+cVhfW2kX~hecMdku|y0E7N7MRw#yHLm"
    "{@1hI}C64r0~>_DzBCCzwz(Tp01+_zxg|+-Qg5H+bA|wGM=Alq3J)Sj&g`ytUz47*v*F(`afjni~CpVAZ|j*8*a@"
    "JJ{a?Kt{kE@mzn{o2zWX(lQkE!Ei!_C`Q`Kk-2yQ^MxSDUShzAo<<WSE`Uqqe5!;n4^+EX3KR4DNwOqV7aVW@$QU"
    "r&M@PqpzhGyCIX(gid4aMK>eQ6=$aEokM?ta0w0~woPWNZ$&t|r6RTFnm^=Sft>uv>mN8|bj>dy1YB`^5p5NHR4l"
    "1CqyX%%C;72CDUEj8z4p|diqO;@{L<giTBg4iD>(2{XFL|A2)jqkp)QjZYnB=kxCdrI@htbbyyY+ULi_BhA1W;RM"
    "hsR)#^nFqDf;&nIHu`=3n|B`GEhyRUt9qrnj4)Yx=e#YS_3IxuWm+V*>s#GX?1{4158w6C=^IRJyCWcZ73C+UuSk"
    "N{Vk_rJaiSLSy)zcf@QWOp4<lS<q;UF8!M4n(|jm>_9K8{;A{6k%E_iVbF+Qx<2)^E(jHwQ=g>LpRq;<+>@pqC61"
    "i80QX;F8H&+*xhe7(x}lmo5aO8ZLYlVWxk>YG4JZ1l#}uz_DuZD7~|*Lg2@&)M-48>!<Xk^5#k7bZ|eRQv;3w9=Q"
    "D^pYb}T$d`|0Z`FB~s9G#ECBG5gRT@ulH87%se^fo&ctwq)DzoIivT$A!oUL2CX=sTEkUsgiffEi4h8*WtIcx%4q"
    "u<%9B_a_NOXXrJqCvk_$S-ASm2*9;gU<h-y*FWR+sG0{{|ef9_lZnMMsjw!nOsGd6HRQ%Ey<J4wf#{L2}u}}gqk4"
    "js6GDg@2s_<0D`jI)A##cW|9`M6sk_0I{RX_SXVF9Jz#saTaAyu)UsAnf?7*Z+1b%_B)9kq&F?6FDI`PNMHK~_gw"
    "GFLX*^)qN}wtzV9L?fAuCyU<)MMK8`cgqP=g^NwN9OR(p~T?BJEhG1(h5V0oJ&D3_>Ct2p7p$U}kR10oRMVNa?KM"
    "6=Sz$Ax3&jepK=ox2m_ph(H_Wl^7ZsMTq+d>K6Wsq77vhsI6PYl%1$>BI|W5*>zcT5(U(3=c*85BXGOIbo>}f(ya"
    "sw*~=5|jhqZ48x}oDq(TTCHFX%B(#?u26WMJ&v?b=rET^}!vuOR3GGo~PhwH?tQQi;f<2mCbZZNP#tVo#EW$yUe1"
    ">ZDF`;qE$`dee(bas=3>FSnkPT<F@*=m~BIaw%0{iD;++v{3i1iDtzQONY}oU__OecInUJ-`nidG*t^YI@I9QjZD"
    "$XU=QYy9ZBU<SpgjTL}zlo2Xvg4u1+-s=|fpAf`Dd36sO0d{!5nW9jNB(jrL@FV2pi?VTO&b0Zc@`lRcMHjhAfTf"
    "wMJ3hf5@?yM#1Vq=-^Mq%_Dw5u3pni_F2(PAOpC^;q0vOv75KZ4YEo7N~@F<rk;sQ*w{rPXn2)SFPn_%{@yIiKKv"
    "T7(V~2sHReCDW*R)1}pi^Zq3WoY%`Q)tkYTgF_UsvJ8q0SOq_!gT(b9Rs0d-7?p&Y4Z?|SV0OBz$>u)IO>0d}pWe"
    "*W4jJy3RvXJ!uZC(5w}{nm)e&hsd!ouhvw<Qv(o=V7cc?1Bbk87quYuC}RL!j@P*tOXv^R$WNoD`~IMUj4u5UIAX"
    "zc#L2dUxRiW}bHnTGFCt~T|;Dp!}6`JeE$f$O!U+}#lcxpy^Hl1HL)ramF4b<xsCiHfi-vC_s-MKmexduswG2$)z"
    "lZW@w*%8{p7BMCQa6IEa!E<g@}9$MCtp=%9|RhZIPH?AgbA|5aU8NlTl_8jHR@fU_<)E&*y&^K@=N^-$yp3aA4o{"
    "OG=zYJ|Ks(j>it1?s$iRNC*fuRA(IO|clMAJD*Y2Nabgm)bq%HIC|!SgdUoSYo|2Oxgvm}r_*v09FcnMr@b7B<sW"
    "NyR9=+_;GTUhg8RpNd_RH{f49|GctJsiI0=dh=|Hq~j3abOuwzY_6E7p~AZOpxw3Pb&jQ?e$AZfp<_3v#=_A?L?Q"
    "#+yHo_E38+OFIznz}%-)j6&CI#YCi&K5@MV^7P$fLo(GdI=-14WMe5_t#?|68^(xXgOgma51y~Jx_zzx!45_|V<3"
    ")n<N>G?tXj<P#+{{Es?l&Od?NpPVGitS)|HHt_b|CR1jYgn*tBN4%q58n4p5*OpVWiNbwIt@`}6;)$nmh)+1xb9z"
    "5AdkNB?}wtII>FZJ4`L8nsAtB3zvbqHLk5<fx<|tQ$Gg62wkdFoIdOp|(VS~nyVu&g&+4%tD13?KKv7F{*i;fydy"
    "Ujj=Sg}|qP>)(G)>^9(i`>|<qMQt$LR%D(w`P&3(HFziJ7EJPtn4jDp=GFgH<JlbDG{#R39a+l!N4q>TE7x^fGLV"
    "rf`w~AI`3Y>y$$fsj>DiQntlMr?VSiZP%MlS8H$Tb*kIBy{%StuV;+Fo|?wAD_>+bPKW1&jkyRz%DgcP<D()x8$C"
    "4t#-@Xacg@~34hg&|=dqnRlxW3@bHBp?P=>s9srd3J9eo^cPN9h(DHKM!95qn7AY@;svAbzpN6aixWu+Wv6g5rMr"
    "mM#IZQZkhb+7I*+Yw;bQjWTZ6(e>99cmw}m>VMrqMydxLS94P*s}NdkF8$%HqEIz$tb;qogHo`u`Zq(OlP>RYssd"
    "%WEdT^wZC_?fAI7v{M~J`ExAt9`qg@Q?3Um9tKLKos)l@!88*%u*K@`_H2`F8E|kQq0!5kRrQW{CKzTqKdy7dYWz"
    "KcMTxG&=NE3}>oQ~sL9F1tRdMPI<NUjUft+0$ab2QDRfJp#tL7L5JkVs;vVLJ6S;X-6i9g0Engjv8uCi6%=Rj@#e"
    "c})}I<-%nnta8JmGWRUmtt%<hTIIXQu<S<3<(Pu7V5{x<0<X7dPv$k+smCuWuI?7IGfZJZ#aPlf15xisHCEzYtq3"
    "2lqqo)1t4+dHE^)vpX+VyiS`Gb_w?qhwWHq=FzfrJwGkcy6S7nMDv`CaM1pNfP$X~}K7b=hB-#7A<CQE;)X4F;VE"
    "&g@$_%xcMJn}y+EZS<_3onS}lSeF&-)Xbzg;G$VT+KRc^`K%1n?=sMJl^=2dojngR|l%D;deFCO#oLHJ=74>@K=I"
    "K{Tmy^NBDzqgv16h5#7op1V3JyMv3T(cWjfP9=Ub^b<G=NqB*LSS0l3E+R+>be)VnY7H&sq8NpO5)3uKq;S+BTiE"
    ";C=W5)Pqsp!_6+(F|!RG2iTb(5o`?=;5%l6+!9@`l?)OEl=Zjn=83Y09!|8w4n@`KOli1YvDb0|)tQ&AF_`3>&5*"
    "$+_M75I%W=vhylW=}h`wob+FZmDe{%86zZNnP-5{YDzr-vdkcGg1uW7<#m3uCa>Efe9W<Mw{TfIW-MS<k8gx_P`r"
    "WoK(`524(RTFvdG-P{a9_(V>Iu*UHP_%J6{<^6VJU{0X4Q2sEMS><bIXS9Z7~xsJ&DzE#r%v5pk0<#@%mJWMIcf*"
    "{!Oxo5+_fWy?*3uFV9mdyel=c_E1!6D-2SZ3i`>5^<}+9faEtu1%kMa71kk5%-EziP<EwYrT2lgj2c6ENPlgY4P>"
    "T6{zLfCG(NB8nRQ13O#5`k|h;}{2#Mx+qM^hVcXo0wo+?SO-$(lU9}w<XYo;1>YAKe6$vCFWW#tCzb5M%t1z~CoW"
    "N!v?JE|yHr7O4i@DT=W<wI=r`GKFsO;K`ULx?#P16^a>+Wh^ug~_>JH!%AjXN@u*dx`d@_#DE5aeqHJ<w)mTk3Gk"
    "fypEnZqaR{7zb97x<Jwu8t161c11J)H+FP*VIZDCsBH?5Q%cKZE}3GxYw*>ST4-dV_KnreB$YyHt)u<yp+Z(v%tz"
    "RQb147&MJyni(Pc=f;#{*Be`AukytUOcuXls$8e!UlEaRnHA>y?yF4J(GicP$(2?~Vm6j%%ZUL1}F8@RJRK*yX9P"
    "4t#RC@$^6<=!!GB*+$Vh)J7%YQ88WG@z$(*mXc#-)HT9;`p}=C1@F;dT)X4+7m1i*gn6jH_W5DyAHUcZn||&Grs~"
    "#%}xb{9c#NXy!WDiYDlsBO!JC2oLfN4-K60UZA$B5^ZHrpmDYQfUr9v6&JVjF{iF*}L8O%^t{5BjYRmhcQOCGS*&"
    ">@2%Pdk_?{xpygJ*lv)(bD~pBx|xpY8qp^dKUrbTk|V59z@#2Pet%lf!3wCx0Zr9sH5NVEexT9%BjTZZDyL+2rit"
    "?`Nh;sz#EqG^Asg8mf;Ep6tDNdWK4W_tC3)oF2$rFnNr=;HHfwSiyMFxz7IVaMhKIX>rln`L+xHJgQwC8A9yRXvW"
    "UEdcc(OE0A)%r6ezo4*&Mzz*KIHFO;e(2Dj8G>JO)DSEniuU=_^<X!Y1CK?9n+ngqttX=q7WyyVP79QXVh)?uG#)"
    "4Exa$8XDq8Ra)<Dyw^Xt7nC%nn#|iqBeJS=J4q8!QX?O8L<F%d=y;oNJST2UBd?3PK>(EW%iFK3Zo(O@Cb%^c5rm"
    "oQ}<!8hLeLQKtPW60q24#<)#8>!^ZWJ8K4Z-KlO(701>X>zd&tkMA0}F#t~3kE-%pnIvsIcqq2%%a-PHIezcK}bF"
    "9HUS!E$+WpfM%XgJ|JikYpjt_8w1LeH(j+DyWN{ck$k)Py$xH#eOKk2}|WkBw1tFr{5WJ@mZQG9jv*9lK~-SJXR1"
    "vG%syeABB&kJP*#v{Jsl(*P4`Z4q47t}rpML?N~oD%<k5v!9iw3+utg#p>0>=>g1XMzsluL<(#=y?3WGMga<dB>`"
    "t42)X)I%}JNL&iQWURGiGzOB^4SFcaVM?6M-UTsLwvwV4WIik*?h<8C}Y8;L89pRP)>O^+SN@z=Np$9uR|&Z!f+m"
    "^O~2k#)zTmA-s(c?n8p<vTdGmGxBG8$H}!FYry$e0pn{Wt6u}(%U*fiHugRKddG-q6wJX-U8!@T8xPCEi=Rzr%Yn"
    "w=q|lbItXj)w%QyJ#7oOn8n(ztXfB&{M7035_nw}?bZbb--s8u~{_)cn&yFNmu$F(Cx{q76W0LgijJP5ET8|q<3H"
    "pn^!+6$_c@L9Q1*dT+MTL{YU+|e=TSgj<H8LHXUd?|#c!C8m#4>RFBw1h0OLo-bJW?DChWq94C=nCi$=>1VL1*vh"
    ";}f8gTVgoV;wNq+sjcoKOd_qJ20IQlXa_7UTU#fKHGzs2F9TRWB^5a7H!5O(BM@k&`f3~mbvy%o9H?7zF^4+|+i|"
    "!!TwKfPcAPqpDVaSR1m%`Gpb)?Hg7-aZdaYzCAGjlyniLHJu{7L?jy$F!mn?DEAaOY+L)k_>p_R>y3t4>LNX&A4L"
    "@`lS&1x$9IOt%?<kg5<=Ds6vnc>o9j4Q;>@57DHFIB*<*-xyA-JVxmfItj_)+l-)HlYYOr6zKK_j|$D0=%KQt)mU"
    "JbTo;{Sbj^}DwT-O7F6Q&P2+soV$@S{LK@)QVZ!{W&1jjFDtF14r(mo_|4_$BQ5UM}Cvw``3^B>l33a>-G+jrs8<"
    "7BBCs8_52|QdUrb~=ovlQP>n)Ic=3LaP(H?n)f>lK7Og+#Bi^j>U@J$FR`0=fI#fJe5rwTbrMKs@+rEqP&G!IR8j"
    "_VL}cd}zB~II9kbg6R4IHyBYmX91g;-AuD(ldYveW{{AH5jJSfG3vkLCRj!U2QB*$>H%aa52w(me`w)|(PCv!xnp"
    "tnK6^7w=c5{nKy*gNwt!hni&1=jXv1OXZNjd;Uax#sTC~OVP;Y^zjQG0q++G`SyUX2CEuh06j@869!e{ToFtm}Sn"
    "S1-A{>|E>Ue!PSfZ#d-K%=$*SZrzX-=gqveWtgi<-Xug6Ii^}twX49*CW&-!yZVR*?uE@b0foC%yforv?sT5OK?m"
    "muQhxduG-GW;+xbOJuU*Ok($sv1eBX<iLy=}3~8(P*y(G^48?JSu;}SfW}!VDvkO}sR_`}S3GBM+ZT*fYpHWbkZO"
    "q2s8*FtOMt?PLXhrEHEl>l>UNk?kx24%lTaBUuPp7R_pb<FH?P%19`59{$pkRD4y>BY}>O$s}!?O1TDTLPgtg7i$"
    "_v+~2_rV>&DNAB3zh|VvA=P7y(}Q>IEG>rNwU$`s$0Xp3IsqO;CxO4rL;%q3z>VSa<+Xs@F_7?l#fN*(@TZVkq$d"
    "Y|KRi7<Rl-@<GDPXCiD+@cQ{<gl`X>^{<~KE4lea}OGu`lBXE}HkH+y)89eXvucMSWVL@dN5e4svITd{6vSc2Uvo"
    "@#4!G(0CnNOL1jqYOGCdfXK$<Zs=*HY;`yoxf-qOvzqc;vvVoBkxQyPK$092~{3x5$TgH-sa;h=%Oh}+Sf%X&2lE"
    "m>EE7WvsNr3x#UKmj}jC0Yg3zGR0JJI*xa>=W>K0y7q&-c`Hv~g;4AxkbpcY`I4kYb<*ogDnayr4^J%uW;U<>ko8"
    "}ifrRUV7Gu~&jw!3D1Z%mEHzs}O>^151>Fd9Bjl}1Xxe;4;t=WZc8ucK{g)@84I5xRyhfcn+>yc^9H`{m^L#dB;b"
    "tr2XMa5o7N#{RL?N2_%LJ?1EC<V?~|7Lv%Mt&<l=N1VN>e8gmLMl&~KA$eMtksE7N!WjpjB$(cTo)@ggjfZw++x@"
    "UW0<5?#H~<Ep+@^Bg40NwI2a>dHFP=2%%Y*(mO}Pit`DJ%A{Ha46FVNfFKC579l1x+5ZOvq@Y5m?N?2~&{gq|M$c"
    "93i>(Zsb#XS@F^Rx}l507KjFzD6f&=OP_rDF8oR$0?bxOXP_N2mWDeDm%{%s1a7lX)5mZyd0IcvuQqm)2Y^2dIF^"
    "KfL=6(mS`?s!3NDn;4hf?YWE{-X&lVnO!7sCe`p0wdTUg?(MG>qxA@>sEyYFT06#NJ-vITS6e}t+f(9m(N-kH_=8"
    "rRSOpBzXxU_|*%ycN&uE27lMTu!a^Nuse9$q{ik))CQH~%>J`~Fk?`}dRMqo;rLlI`N#?QNMS+@SJa9Xoh5-;Q#2"
    "gi|SQy5FV@o^qbvl-EUA)WFAPK?QxbS`$L=I0WkX$=)x|_N3P-x`M~o+4xO`4soJH@g~|cELL)hF~JO*(6Gs6%Jl"
    "-fVIH4@4g~vG4;B|#b`+PsgiW3Wp9SDvmbde9hwl!MZO@BN*UusR84kk%{pqJZxu09j3B4)7V}2FjnpvI47M$0;i"
    "g+m51P77h!kjbc<UO;f^Bh?NmonkVtcgv!<0hV1h8H^zUQ^5UvWE}Pfi~UTVoP^~E7msCt<{n`zh&7C*O9{rH!E$"
    "-i%GUC#{oqZd<5kgNgggS@^nJqvzR5>`gokN*3TqETMKt{c!$kJ@zCiP1}gUn3dq6Z_K2d#%XpaDwvflSN-WXyro"
    "?8JBBL4FVIpppg<pbvmZJEWPp2BgBc^eV9-rQ-you}N8hupuj%wXVm7jbWFM`J#r<J*YG7g8P7_+^o-Cp=%pq7Y-"
    "o$k7<J}C^GC8hzPo|n3uzK}j#zIyOJoZ=uYN2^8N>3;YLJvGBcfms@Gg)zE@jC>lh5Lvby5Dk^g5gQhZ)s0`hKms"
    "30l4beT6;~rO6;`b=o5ZO(8DTWj1O((ee$5#3nZMAsrrfe*q?bG0_UkcOi{`NL=k*(p5}pSZDxgDqnJ<F&yPqY`7"
    "l;y>6bshO$Qg!QOE%dAFlDv4Amxe)1<8JcfRd^XGdROKIE!>~`#8t;q{ZU4gW<FJpTk!Vj4slbZ}o-NF7>4_agk;"
    "+Br?`94|S6-6Pw66U>pr)9`?jIjbgv<1kGP-k(|Ct^SWX1Od`z3poDNgeY9JBRBvtG*-|BS)YEA}!=HLA)4NR}xw"
    "{J8?{(L9s{FVa8MA?nwHew!zu4(f_}-9A?-I1fKVtPx+?=CG3jo!g5-s_UN>y0!KQ?Y;#h)d|z*=mw&p4fPr&TQ`"
    "j2`i2Q<0BB8!)!)dJr^<*{&qVdZPn>0Y=n`JhEvqg3YQ-xY!rPy2y-X>EaC)$8XU=AXXO4O3OnTi$}mv@{U}f*m>"
    ";iJm7BEl-pDT9A`w8@cwKP@XYaM`3}X5tW);|=fO+R46Zvh&#aLegGXh`9cSu2fkhLR7=_Fc&5i2v*!1ZJ*=b%lj"
    "f2p@Is?hft>4Q9gU#9SgrBWa#}tRSQzuyS=J3p9nEahe({Lr0JxQ{&=ZlJjSZS7;wo^}uMFHXh5&oW3p+s>{uY68"
    "9Sy{RmU;7P5N!SH2?`o|?{HT4Os<{HuHo}X0(_YmjmbWEvoe8Dw0yRtL#OoKBIY^8VR=(t#faP@tQr$mR1&UPzD+"
    "MoCC<mrf3pVLK#`+^kz!PtC(gg|~@atMZ$l1bFl(HPBWaxW*`gC9mOw4aPtZNRiR0TC#=qz46`10jm|No@@e{T1G"
    "7!AJczy1RG1i+?)U+s2Dz@Z6%gwqKj)oqq01N(v)XK6UwA~n6B3cQ)|rBMULA}Mc3GUpOS0@U$!it#o<XWy=ME@z"
    "9;<utt_A9m93>-P8g9#`Dgi&}AChsx$}NkpcX^`QY=jlag0Qo8LaV3#bczkC5$`uf%Uu_)Nc1D~$Ow_B(>yi0G(K"
    "CEYn4cAC&x}t=lJu3J*&z3k}cmN}t22!jNkpJZ=LlA~NyS>SVWsW+<t2z2TU=$-v4d3HNflzq>J9UaC?BRR6X&?A"
    "&2_;`3kl@*b-+1r95MQ6a%@+m5I-xy9hW+xrLJA%^$;d=LEarXGpI2z$mTRZkc(}6-Q|0<mr_167FZ}?QUOY?7H^"
    "c4i@4kCAKPry0ch493TNv;P1cBuOdxhf#!1c4)jky3?(|CDGhi!<JOEA>+1az?9k^JI`FU`6EREK<m093yNo606X"
    "-wuIxq^s%D0@MkAK)NFM+2I<jT1)05NKDiijylb4IRLV~gtIkcEd@4u^{1z(#5#G%`SFN@k?^155L`4o0XDoabZM"
    "5(VZ#?e-(P&!R?w0mxt@kv$9rU|G`H6DP!WTGLQ%e9zDoQUmulsELPK*#2l8V4v;}Y3hc%{hc`Yiy;JP3?F^c~Ks"
    ")TX%rGVl~gbR%SCCw&;29@43t92F&=w4w7Fh*xXDp9T54VSH6PLvKVAoM{CDVHNul#~BA*)HImtXKKi`#}7JPce?"
    "B$2TFuM#2t_y8Z3;c0||HP=;Z^V_np@7(diM+zKMN0~;DmwfYRcYK*;z$YRi_bdZV^P^~fg+A1^#EyZqQ`g{5XP)"
    "Hg@g2JDauQ^XxH{D>dns=})2qD*aDW|93XDp)<G-);~P?5z#DpVPROceqPDXceqxP900Ie1^MV<YnioO8PFOCU`6"
    "c<-F^-8<~cX6Vw!esM{b$AZjdZ!=T<*`<Bn&TY0Yd3i^`86;V2n*EfBVtNDwAF*F={v3$eX2pC@3zZM|$bNH*=9}"
    "K>>Vp38t8svINnUT5(G5(Brs%dr__KP=%)b|FspEMvm2K<_dIpZOe94|gkxzT^x+DxAprI4^td=?Ro&}6X-F1>Vk"
    "Mnf!;wHsKNI7xi4IZx+q(w-s0UjC9YqLpTQ~$NH2nv2glF{9XZZ}D5yg}xjNfG+Hg&bg|B=ciNApq+m5b7cd(0V?"
    "eVvWL5ziKZ1OM(ufk5l0uGa<K{4@-3a+sv^8@BcHK>j9-}+>$^=vI(J-7Z&YY;dB${g0*Gs;x3B=0{6~&i0lFGxS"
    "V%IS2V^})X!;VuVTiK3Z*>LL&Bq{7_ZOdv08Id+aH)TFY-Q6aE<LDU}B=+DNyHWS1`6kLQ}Jwyad!Agi`S+oBv~#"
    "t<?PIn2n50bl=vi)ci2a*KxZYxlrv@z^XMMuqWdskiexM#%rNN*>tAVkO|pxf!eDDchI*<B<GO<kT1da>UT$O1qo"
    "Earvf8`U(*()KL(Q5*pd7-nvNA*XK*Po^KN7DM!B64{pxhFgyYV)qp!aIy7DA{muftIvt79>pO+Glm09>jh+)IJl"
    "}DULNU{lJP^eDXWFr2E=_cN7N-VSLiGbbF%e{iWGG4GB-V)Zhz2-oI0erWnrlk<?io?q|#fHfpJ8L-6K)e%DuuO8"
    "?nmTCc$9J1bCF?^d0SGEp3Vk`xNG@H|BXSBGpD{<V@hMGFZ5*kXW{nSod5hk&B#qkoE4(_Br0Zk=nEc`%XG4akxr"
    "LCb$%GmVzQ`z$3N2<<?+^_lRR1c(hvWnoRDQQg+xa6puL_SK35PLNritA%7a6WN(0N1(Lz&9?J~adChAoB#jsuR1"
    "M1}%iGEqfjGoMcksk#C7(3z!w(jUVea?0j`y!WNJIfD9eU$P%0yvkJy%vGTQSUO{f>qLT-eEDVa{kLD6P?t5wR3q"
    "+BlEYt)FpVIrmx#G;ULgy&Zeo{?u0c1hbKy3v)aZb=<U&h*^vs)KF<8pIlW;WtuGDOXj|(Y@&ByhPGo+UKv93h&s"
    "U*;Tt_`u4;SBu-qG7|ThFC~0?9Vd|yQ!Lm=3F(KR%7~x#)BvM1i&H<gntBz0gS@wbj{YAZ??%OqhNu@9&S6mh-Dy"
    "lR)nHN$ZaAARL&)+Q|TDVNA~A+y266Zj~qFU``jBT%^LCC9@BC6wMkiPyPxKTU_UDfgu&i=I9JQR+MUDT^l>Pu`y"
    "3W3jHZM4B>Xm#uHq$k^kk2FO8<%c`yUB-K`+cC>{e^1R{yUXbpG{&7U~Lt%G&&kIuHM<tUK%!@h-Tc@TfFy66l0("
    "8p~=tJU9J`;iOioo?>xyYDLC%pU``UI_@Lw#cB=_(FST5LQH2_0BS9YcZ1l+FdQxTj(g5S7|C`9%cRZqd)x$@8^V"
    "RRn0VEtJrmrMxL1vN4vVYv3U)uP)Gbqa^r<VA8tNZk{G=FM4)u>OeyVR76y*_NmEV9N_ypBdXkms@TO`))R&RO(d"
    "dg#@7w;Wa#m_4$WAfh|H$HUn=H3;^K&#s%wnE!Y_#mlb$vqPUH+G(o^qn7K|FHz4dhVQ7%o-y)S`>))?soJ7=!X%"
    "gRfXA6ER8&0Q7o&ic#XUt(?MmRn7Yd?5i}{RMjsA#(NvWiI><&Mf;4aR(%YKbM1`JuBW61ud-2!nD&pOu%x6JyPs"
    "?$hcUn9+0jyirJ&4r71I>1Qf2mgbH+R5fi!$}Zbb4#v6lG2^g=Yc)Cym?F&y62f3O8@s0DL3DL(VfS*6LfV!t$<U"
    "ApAID6c5clpwPt^XZz-pB?fbrsDV<Bfo4de69oyP7cG)fQ17(3!fqssS=fzad3%#pD%Eziw@5yxJ*rf){cExlHxn"
    "6Ht-%6*Ji!XMNU&I!)ZOQBU%(P$Mz0uWe3F3?FV!wu4sD?FvP>6r-gGJKi$WJGRw_+a<07>f9pl!@S1Ura^n8^}s"
    "huK9&OXla*Rucke-#(Tl3`1-S#7=w?Ko}kRjAxO_I;_ON>e^*Q!^_^4Owf@iImV+QsQL%dpSdoFw{cgKg}bT)YR9"
    "B%nN0+`{?6<E3e9Ys2v4rQFu&yT4g$tbsdo+ql(U&MiCYBTV)QGe8y~Z-MBCTR81*+V*{u-!NmBZguQ1#UB+)p;}"
    "5~YPfMem0Da`n%{jKFfd?z89v-#a5W73~)5?qRo&vt5eBXAv{uiv8Yl9O1I(92r*S*do9jo~p5FY1--+D|KAs1}Z"
    "=e>Gy9Wy=i*=k1o5=#hgZ__qn3o8tv(&(u<HSTF4(|TH2)oX#olenCGH)L-3=MJ{^ll%B5*2HQV10@i_(8<y!7Ha"
    "L~Ve<0zzi&@0R#RTS_Hwm9vW1mHr%l00Qb?5;{dE{qVUJH9ADm#qwxL-7+^2`n4$qQ^7K@sU?w3bGc)jU#>T*vfa"
    "|hQKK%v^{x?**!QRLPtbY=pt9spQ&DU)a`pKQJUAb;y(w_g8c@gdrIPZQ`HTs;0`bzYu&tC9bHtqaJ1ticOp(JL^"
    "OhQT5=`5BTm8QM`}n<SPPnvoWmfC<$E@q2xM!nT&MK?6GkwY7vx6f;7@lb7T}w|xRd^ucvRUT5HDRxp)!X3?veMd"
    "UIPg?zpWngR=T8ZbcW`?r^Ga(H4wxfeiIftmyDBhO1;prQzj9;D<;1yvve_<h8@_7}tIILQ}DM?d^UveN|;Q#<TE"
    "vsj(Q@TZ>Hhzh$k1j<E>Zmrn2rU6y7302sL3UO0N&?HJFqR85F3N-lr@>F4@G7<vo5An91!XpG@EYqh9)&^Uj36a"
    "^%inm-&_4Y9NVcY7<T(hy5Pj92K8^ZkRA7}{f2xQ7Y9jE9and?VMCLHlq8(a~;1Mo0+wn6QN-zcAa_3b+OM3p_-C"
    "y=dxFQT6PQLQ>1=WzR$-js&eUSes{OHp2XX=|a>2sVCW`%N1`z8k~?I^Jn{r2*oUSlc^44Y#(?wfqjtH2u`Ask!l"
    "P5ES$OtGpl4?|uT(Lj$Tubf;VQC_T&Ln`B9HvvzTWj&oI0DEVQ@$owl#7#@sHV#gcU_u<B>p>@06H7nB6Xmy&tq("
    "~MTI-~Wbh6vjlz!u*8w1i2|lr_;=Ii=Ym6RevNyRyipCUe5S2kLNnr+?K=j-QV00pF5+_%Vt%Mlv>-kUTy(-S5Fq"
    "af2czzBA(TPE}lvSe&cQvPNI!+M98)(k08inBCi<>#YY}_txg4MpTH#7Ori`jnjNUg&emZI*K_vALltVxz{0P^_*"
    "nvpCkkOCzF2tlP}N&sA6B0)+?mR!(@T;_!3WVeXq?>#-;#j;z&luRskiDTm07XPS^NqG}FE#iTFASj~2UAt4lTOP"
    "!4bcw+=z7B8>{0A|6;fmAXJV(X%Qsa*pMtwwZi1V3&+uy9}>-`%Gw3+fdkPmJ#kM6;ux;I#ibRAun1vL?g{dXk7~"
    "IArD{2>L3X)M_Mp~YE9_Zx=s1(Zl;V^|L6ELRA6fxI-7EYk~j}QUd@fnfKhi8A#X`d)psiJ^PC3}k;%XBEn0G~eB"
    "||>r-N)CcHgdZMMPS!W3_`>rsgaP6(K|VB)PcN@*_r2Z6UtZI}e;VH6(k?dYLZL-!8$djb95`w_(~`XO)k!jOR#("
    "epCiimN2+2C_;k3%_qIc)fk<j8?}_F%IxU*cnA&MiiigMN;D9Gb7I11gjisnji-w;(mE`W3`f>u80Lg4<?05c#BA"
    "a_1<eZBEpKDULp26_Ic%a0Oa`X^#Ld8V&<aB~oyHO|QT0EL4=Z))Z?Nv`4XO>3fo&MV$T~5yZ-iAVp0tu)+y)lfg"
    "<h|b@r)OTf(huCNZ<Vj%#tJ8R?W^?V7U9nOH7>c9EMh0P^x<1P4M`Zw1C|WQm#X`wTWI^%SQRr_u<2{jdV>_War4"
    "rnu1uvZvB>54n3uT4JNDEP1%vrdPzE+7Vk#$bUx%n^%`dz*U66Aa(u`$6*Lh&7-1<t8r(hApa#r}XI;%^ePDHM&i"
    "W9Ql7ASjvUN)O60vZePT9d%a!O<O-cf?q+r3}${U?c9bwqWlloVJD*2wRX%2XT@8`G00NVa;T(?Z&d*qXmcI#?U`"
    "+wETRF!}s*DwJEn({H<72Lp&mn=O~f%Wh;!ah}*l2MH@xR>D~W^@LAD#Lns{E9MxwnW)-TJ5*i*5PXOqLZ*jz@pd"
    "0;l^)KbeWaw7DX&zpk}`v-t%OPxNy6gE;&NwSw{*YVgqxb0?&WGG-E+IW?YfG*bpfx2H@cPXxAvYtKRN!-gU4Hqk"
    "qdQ9(<^p-mt$>u=yHiKx9{!H|Jna3tl1`wEaRa>cbQDI+E`72H8!0Y==G#aam*y81=#-c7_EO{3AUj8{7>!o!CCB"
    "eI=@<<Ow-mf;xub8f(JmNu4r9##X_35_T96Eh9&^;<Wco7m0S>1?d_&`R?gL4w`y@ZK<5_q!&@VHH5TMEta8fo7-"
    "kV)r*E@F=^tebQ%lKYnU-&och^`~gsP{)UlUm$Lb@EdBU11UMb_|h8hW$Hu-Jwz^@?BJDs3mM<YHBV09uxsqhCda"
    "FFq0*T5NsWeHn5?5YAXK!?F>6bNjNdHpG+!hGoP!e8jg{ebA;$syrBVVi*)LsI{Z>U@dX)<B$)P65iO|25)KHglL"
    "rq&xmNh{-NuYL`JGRvV8;B%evZ8kSR5X_HHKTGB-WRsK}XVP>7mPQDR^kE{_6m@ia)kxUG^*Ak>6-T9nHH47lWC$"
    "8QTPX){i5q5-`Abi)WI|8DZvWP5Fj^qla~jm0JCnW3tV#QO@@Y85v;#v;wtIW%U6enRmdF!724h1yF%VQNyed3du"
    "G>tiee+QoG!bB`ul8%tlMP(e#e%cj<r=EyRaN>)V-XZ2waWDEfDAWe6|01~IuD1zh1Va-i$u~~^n5o2j^{QlyN5^"
    "G&rH;~z?7_zWSDfrfp?x(zlsNpBNwFUJX4LeK~$k2c^*=Dv@>bc%EILF;}Wa19khtA($?5q_#YmdmC1GPUYm0Zr7"
    "o4OrLWYdU+&+n2!UN?<8Lt@m^Ry`;ZOlTU~RuGP3GB-nJ8Pqhj^#<*>HA@mu+9B@8C3M!JYDB?^L17rX_{C4j2I-"
    "zY2u<mWy7bPEwq<R;j5sF?=Pk#!#)2uJ7?Hg%Y<=ORdQ}Vcd`!cnrtoU<O~XJhPO)>`!DCwkiXyCAx0@1KyhY)Kh"
    "U9!FAX*9pOH%``IKra+s|R7EbT_u5vlk~vBlC);_L9!K!Lm%iPF?U%ObdF4t`dr{GC@Isw@yQ|T%bg%NCf_=TJW%"
    "STEdCgCM^*~uO57Gp~cgV!fWsMy~8tjeRS~mvxAePy{C@wUilQ+T=+w3iMhj<_*MHQ^Tgrfrw5Jg^`s6swnK{4xm"
    "(TC<x;vXk{E0{h>%zM8YIBwMTSW=^GSle)6;2xvdB@>dA<Vi|Kn=h(JSKu^giweGe|GS`rbZPili2?ZR^-!J{!58"
    "?S1;qH5h?dFVjz5*Djx!+0C<e=o3m-%khYGq*wE2dw(CDo&lX5{rtxnNDf1j>$h)eh78TZU%vGHVH8F4J0=uA&c?"
    "Y2^sna6(_5@N>AgtrVB$@W6t&l_it2eo@0vu}jDv6aw{g|k%6LeiL)Tra@9i1PJYmn1+br7o!eTWaNs+%$L+6%Dp"
    "pQ@e%6!HIPvLYUdj{&mo9#3Du^`O3DLMFt_rQIPbL4RD>2lYiW-LN_mi{@C`rD<ZP<_>ly4mW|cHJTH+B(;oB;n$"
    "r_FmPx?wYt;@wAayl-&|uQf9mEcb+HJ0K6s@GLm>mf%**7o&vq+t)MvzGO_>PZR2S3kRld88O|`Gp16pBTP5_M)9"
    "nuOvcM|hSTZ{Drmip6g2OJj*?(pXX7Kq*QzegD^f%Rvb`wLSLacx8&D6^as6~82?ivyxF$0qk<qSyVf`OYGJk(k^"
    "QANrkoe@@H7#6hr-R|Bo-sQLKmd}|tTu^9+)g(@)^TRKMv4@a>Q~UVv6dUqBwzjcV#t>2<50EEWq;m3b82xNkOMd"
    "AA`L8lot9cw9pN$^BI55+=!7@7qx_&ui0a2mssA4B5GZM%BYtyE2?9{j7XF58P#@bO*{6xp)PzZgIgiY#$w^)weW"
    "Vc$QT;!KxQ4TwJ#7XeN;&yiBn0GH@dx`e}dv2zow#pYxgaQLIAjmu40z*$OZkL%&9i=Vco#HL~!b&6^Ass_1%Tb$"
    "b<>QY50`cdt<zf47K^yqwd^OQIM&yR^w;4~AN38Ke66@n+eKGWiNh-Ck#ce*aeLV%OM@j>-okY(;Z+%{M(-9awIX"
    "pSwx>pKBt+BPY@0?K<UXY5BILI-Q=5C~4=O(+?ZqMRO7eP_Rw}hB)07FJx6RXuTu@RE705`ieI~-%b*7p?S#5LU5"
    "!m}nlbsf95)-4|yY92MGOc!0#`^gg0H5|RcLU{*!YH$X_<94@$b#Ld%3zs&nQW2lCAaWXx5bEHEe|vF2)vZCqL>X"
    "8+x>9#WEN|-8%wB&)PY#|x-TQ;X&R9hlzIuT9spS+Ma1t_OG8f`)S^e`V@=ix^u!0{Ota+U{-BzTo!3a9sPPhc@_"
    "tulWLyDH*xl~Xjjt&;^Jvn-7aQGu8%@Y>6b~Kg<B>(pp$xg3^%!o9FdawzDsl1GKY)|2dk44ci+Z+X><JvHoCV&M"
    "pWIeFzF_$+A@m3Md?!vulW3ABU^u_-E!NFq;3aSXqGQYU1<BoG^5GX>_*lykrD<t@mcx?&9$X=M$+wJJq+uEq@N9"
    "ozw&aN}*P`${m@)8LOk|T;~#d6K#geq^+!f99OVKU9Z*1pRYCH2nRlR<K9KVHr-@bCHU610-!ay92pFchGJRISwJ"
    "mdn(3bLHMrJmM=Xm~OtCq!$>>Bdv#~lR>gi%Sf<m?6klLvt)IH`5P$?bz$l$Nx7f`hJ_J9Ju9#sbOt0957y`JuJi"
    "Hr=g#s>&p4U|?F*OIqb6!3JzZr>Y@v)g>li-5YnsCJ7X*c~cZIa(!>;Vyc#yiV(X8AOX|wbyAE(n@d}{|gKO692*"
    "Ay=EjVr#S`1vJ>H7SO0l!N4)d+}k-+!SrsBLL6aY_!P8N;|qKfH$2J+Ayrm<AdbzGU4i}lVqHh*VIm%TW4_xY+QR"
    "X%|S?9J>1^;nwHNi%&BWJJWc~=f8wmLT)}wBi<}iy#|o=}W60Gqo7?U>0GWq&g^bFjSsZr9HWEtmIehYSn8YN%!g"
    "8+#$Eq-b$kYePnM^|-n&O_MV`OIJR)Y=0xD}eXL7D_-0tklT%yd;|lg@eLU}I>Blb}l_?j}&!s~iv#pTULbLBZ+C"
    "ZV8UVVgPwdz%#}ffM%91Fb5x-y%ONFIW_ansLmlg0LN@ay^Q}I?9^B}E1OO}eRCB&pkr$Xr;Qwm_|mSy3T~fgld<"
    "HC&#zP_tRZGSCT0|HxVphv;8F=89ghL4pzx)U-^67##->QF-B~d>G&G}tfFSKid%zKX0-Gq}V_nBWJz^kK8@SY&j"
    "|l=#e0#j(f+X9z1Etqa&lO8SKvE8Umv2_qZ)w*8MCG+#kzzyp7O*y;dy}4tPsYC-lEvmPGc$EGzF8S&4u9Xp<`pJ"
    "N$J#>4<S3rcSUJqa*M4&+U4Z|zy;^zPS!MW+cgwu^!PzS$)T1#rBl0$iwkJ28>Nebr{o}o-2dDc7ozoZ3Bm$hj0a"
    "EmKH`zOd!?R4MyeBjRxVgwPqmNfNK&v#H#nA|CPcw^=gU*MA{T<%%>eZg3z>O|GLS_I5f8X0bd-_N6jwya#3USx5"
    "26~kDlJXiG6&v>QmU_Mk%JpxitFn))?epqIwm?y(SY2HcJ46l#WLTzgPOvduipz6)<{SemGYn~-QHttY`Y%;<JZC"
    "15gYXD6a0MTcMpKArOm1LAa)h(wa-*UBz!O(kvX%oOo$+}DW8@Ja6sjSz$d{DqI|-*IhU$R<=+7+%Uz5;;m2&%i_"
    "ND?5FldyCwVKqa1}s3~5-|RHkep;lJTV4+o;*KEK707J0XJ`thF{Y}wo1%_O&kOuNr}Y)nGRJ_&~?ariemt~pZ@^"
    "#Jvu!*d9i<Xczm>rase@Jbox%%E6f3|*@VEQ-=y-t1l4@0u%<+n$s)g8;(cW3<ubcr-rx;l7v%~F9FUF$KCq-P?*"
    "kqtOrA-Tn<>WOo{I)y@a$anO4>175k<q+olTcf2QJoo=gnuGo%dKwjSm!(8vPqpQaufLUH^7NmRpFGO{}7hA^(1S"
    "^7L`?1WxF#h>#2F-U_%60L<oevN-17WSu38{OWp%ewCjT?9W90P0ocZV>vJ(x#vByIqRMCL2`PNE*1ztnl>UQDG-"
    "cN&bdesXc?VYGZaIVk`Y7!$Pgc?t=W{X@6uKY<L8eKzn2=<JP!QibCyjnaoODdiREdPJ&}}LEwXG*A=fA`itdaJL"
    "Q7{(K#V8ptza&_h8hRpnw(R-Nb)-+Q(R=E=a3+8F$}|$c|cKOr|FzjPZC10p%BA|7rQK0SYwijDK>YFAfVz_!i{a"
    "$B99Y{gyjuG8HCVj9W!r`vapZWn-v!qTYacj?6Bw=7D?4J;$L<Pd4-=3E;q3?%h5tp%jK&FM};Hs;EGY}dyn%Uc*"
    "X*4_hZh7#yVON#Z<?0<Pcvn4Pn$vKL31yH7#E~aEd+b+OK@@2u&P-5#ZTbnvl#;&goTm)VZ`dI4_+g4By)YBpp4S"
    "T>4UeZN2{BP!GAMKjEhDCxF4<mcFcNUU9C$duGqP97|6?_*e=$DTG(vtQNpU%8ca&l+Lhz2Z&^JHzFVyN_vK8n#?"
    "qQf*2FgG@*_v^YLv0L})ok&QU}h3<h1?&h2wUX>M-v>8+IsklpE&#L&ZuYDxbG_=hmN%>SfTz9s4PSvp95MP|Sg="
    "BFJQ2o-jkKAB~*e~_?*h6i99{mwstoPN%Yfib|dYYZkp{5UC2vDbk_&ro0im>7JPc}7Y(O}s>V2nGROQE%%A<r9%"
    "@n7p)DQgJM+GV9f8bYkk-SszVID2GsyJT9MS1?dfll4u3>);Tah!1{1f%B#%&5h-=&gdx5TSH}Vk&YAzp=Xw*n1("
    "IBHm7x)mh)Nd&JK?X_o+FrFaNC_DCnPPnj8gFc01myXgfFW~vYWhoUAb%ZCVaqGqg>jt39FD%?QyP{bYon@S#b--"
    "5&MQaM7Ofiqarx(WO<X<lk^HZd@Z94<z`U;nVi8!m_pc2^=Qj%>246~=R6p}kliq&U?X&QHPW8YhN>=FHTToEUkU"
    "^(Woz$HWlaI3RckMKY#|@-`FmUPIb<tn3gw>Nv1F8>EN=GajdqLcQ<Ef}|39#{(`&3k>s~d)PSM%~T@c$Pky=vGm"
    ";||C^y!d*G!hTPcl@V~9xYIK??8Ari2$8CVBbhD$X&C}9yj1#p;=&8Cj7zQ3R%TphUTSv*pc`0sh)-Sd;RM}wRI)"
    "}KnR;<1GF+~|LGFG@cuna7Kx_iM*%B0lWjpiYiOrOHzU$lJIdKcHf*Mr(t3p8<BD<tnQToWE5z~DgGcc1;J-jP>*"
    "$9lK~#URM+f%gJ@qYCx$=V*WDruF+b?sB+B9E_NqO}KpN|&!fV`yveK*=OAfc6a6k#}H?<dbz!1*8l7l<pZBovZ!"
    "Ig|9IYE4cCiIDUL+2ph2kh`hC&a&A1UnmKtY`ob`mhTFkwy^|}Sjdju3+(ElEqHZA>BP%kNjk*(l7qT~h)TBpz;e"
    "_V+(10l#rvqvv!$2G8W%PWLkGQuNl3Q3?7_DW7+T(yW_|V+@g}qqce~YYMY0Pz$7*r5c66iuIC&%ly)RLCv{WkBe"
    "5g*<eD7_;hnTX}DZ5se4++M}!7qoWXD5HS<XfCM4he5*Q`v1}x9jPU6}q__DyZhsCeZ9Q5Ih)w+!vo2FTL-*Pu`Y"
    "lleTw&B%?!Zko;W0ahqYr4*&(v8P?NfqupnmvA`q*-KooLI!$hi6^&pjd8nTsZH<c+8m@?(j*y&=_J2Lt{|(bx*r"
    "iwkM(b__vFJ3#fOrS43b%!0BRxN0YAN1G3O|_eV1wj^bh$wh8UtvMtO<B9%qH1?dVG5D*m^MLiT1^@0RyDAvl1??"
    "08^^4zl-)`g$L=jCio%c;Y^6dytpVZ+6;>|vG??v9UY(^XLBkRL4K4_6~09Oqk@nqgaXN$^5B_Tx7@v$<=#6LZFh"
    "BBK2-Fiin0c0`Gp6}t@rxX4_kI?WIHgp2a7<I)S{`XO!=XBvcAhXn>Kk)Yvb>bk<5#Kq`S$_PY<@YcalE206fHCs"
    "|DL>ssGQv8%*~lvLZ)E(R;2HLa||k(FnsOMxzhAApGK`4<R6H1DB?GC2FZ$PNw-qpC|-M5P<xBtS2erHBr91X8)y"
    "&tDAIzJ~X+&{{!C}%(7*Qu?gnZ%`{zND5|+o-j>Y~8K>CIm|SY~)J?j)hLQCyR{yPww9scpBe+cY$D_I!3xuzU@H"
    "ojXS0(6O@n<Pf+&p{C6r-1%6w|s0j$(0@&hvk=2T$K~uGPGzMQ6;nFlY4e@xjSy%?ng<^=)2aLr8uDh%=rSq|x@K"
    "7u$etOAvw;LY)Z)>*T;pYErVJ2e-Q4gV=cfiH^MVJRQG*r5qK@C)gdMQj}S<WVv*XOx?{894(4s*}-#D-lSL-NKt"
    "ceq}OOYh&8*ObVXI9&5HvZ2kS+XeYfLz<qHf+>5OW}ws8hG6w@~<-T>JLG*_4a)GrI_bpKT^+4)+{OSh90J<7Th?"
    "Dh$_2Xqg4&L-^Wi}an!Fn<}w0LBV83ag-pC>kYubZU5oPC^hq2Ba#HAjMszczTWpvPhjEh<NX}j(^)C-O;R{l*g^"
    "3gM-JX$ybA&ufN#(5Fei>4-_w4hc~QUFc19f@bnbZ55hrl%%g0{g`=eHZ%~oQK6qBV0U>8MS^MB~J(s)I!hjuMQX"
    "~U<Xi>5^=XH=TL522WddKMvYMJ^t9`=h$Nnm)!_9F?*B^pWVx^t5E^ooKE6#7M_Q>i=l1S>~P0KFDjT2>NL>{q^^"
    "&pb->`Ca)?@csu^A<d@kzT&K7v*F7+h`f3rR>g!hZ}!!>mc->Ebu6+jL;ze_I)it2!<J|8j#{R$sHi*^8pLQ2tdB"
    "R#nn&PgqOViQJ|rijGMh$Ig@Uon3w`s#nt{n{-gZ!WI67bnQp82^=Nee?L*4*fpPzR<>Ac_SC0lHJqIbI=x}1x}J"
    "0+P|?iM;U185PRyxs4CLJ$Ugc+aDMaLbNcQbcWZEd|*P2gQ<bm`kEAvf}cR<RmOLmXBA{)ohSF#XxM!p3#U=kZ_t"
    "#2Y&JiGnZ}8%VXve`SuYkc~?ob28AQVr0`>miba-wZa9BGbx8KP{djOZ{NdqE`9L@h1x=Lb)yxvD{y)iZBgx4Ln#"
    "m2ieo0jHL)msbsUmN~ge{{40SR!y6^RBkM!?RyA;&m`hw^lq{}W|r7=+mNhj41!&eSNLlzL5k<OJ*HcFA>qsV6tS"
    "HlQCslQG-WX8~pz@9CKVC{nLpE#(ImZgYMrvNbMFwAax*d-sV}r~2`bmL~NW<f7Z<!pKp}d^rWKXfI5%GN)_-dx="
    "#>_lowlF&9+3ntT2@1fP6-V07pRTtHTte=30R4(D$%ztdTO>_qM@l(tgCn90%SKoKrPAs8R392YmDba+zhH0xHr="
    "s}H62@*K^ApC0~#{l&%MSuxp;S<5q8d?Q1e8E{C%q<2|_X6(q-1Nz;3`rS|=3>W*TnNBG$I`tE?8W)boTlk8a?aI"
    "8pyDq#gG#D0aTl8ymUQc<1XLgWcpJ@08g^d;x)L|MkxIPjR1#8B3N!_QcTNfO%OXivlbnj8?(Od%JU=^l%z2sCEQ"
    "j|cU{eW7c}<Zrj^s_BJC`m==gCDrPceyPfhC!e)4x5nnJo!C4+LbHF3_7loj8dkFvcxSEW<if!cHl7$}}PX8A9S*"
    "P*r}Tp)lMy-lS@br#S@+;CNVx87GPXgpyuG9m}sX$ymbP9j<mydNWQ8Z!H%qOr_w!B=i(w?N-bXqVyfOeo+)}9$}"
    "awrB9`7$n8sIB=(Jy`6gmuY=73QdrA(5=d$uO9%D22)E)6&w5*Ya5p<g-HP~Pr^z>BQ7D+hlFsXRfj(@9Uf^xN;Y"
    "O+GouSrWl1-&8pAP{+3M16YvyXTXu2w<W04}@1<1yC1?l7ppU^Xa5E6fa!YrJZ#(Hm_wMUL@3ocOKmxwz>g@`43f"
    "?U4sL<^HhAm39X1krkH)ECW(Gv0Dtt0c7Ym>R`6b*-*O+{dfnaq5fp{QY4jblL%gTY@}tA#BAupG@-l#qx)JYsD9"
    "|_4OZJan9G!JOr#zCm=LG)c<oLyNgbO)w43zL!>^MYMKc^*sWtNODR~HQ@g6VMU)#w`Ba3g07HwxK^jAANf1L}y{"
    "!Jy!S-t~rf8h2SL>@oMXzmYrJUnFxj^5%RF3h72{5WyjJ0T3i>cyus6ODV{kqtd^O%QA-k&?TDR;#6o_)?!8Vp*h"
    "=jqvi3NYk9{26Fj3*s?8L1MSU))&?v8^H#fjqL7pih!aYx`Q5*&RHNU+5L=q`CIw*xj@~4ctvx&4%r-=rmxC<UOi"
    "VV_Q!MN6v_gl~RPEWTu+KTQ;LZ#R~(eb&3?1OJ|0%R3UC|+zj?F3^)C)VYmcRalrZT6oC%%3GkMbht^L|1mq!W9r"
    "U(Z-xD2FadHS?1&=6qG=aG8s%9$+N2?rU{nv<plC2WvwEbk#z&zl%P)+m+B9`$c(?x_-&mOX;DT32(;LBv#UlBes"
    "70$-v8iJ-Hc*o#zbhG=M_97c%Y2aeFMSwW{_qb#rTBopc9;3hh0-J2k-_1Z$M%$d#0z{3=k6NA!`9}{W@Jt`fs@T"
    "3O52as=;}`594L$36-u$6SU$^!>nZZm(6(DpSYd<zGms&U?LAUaZ?l|LBCuks}idL{4P0Tn5;yyHcl9m{yD+ESY%"
    "fVbUgKva++l~CMf43TfRfjK7JV%fQB(@)db9n)e@@lwOFx(y0gDrO#A!Em&xhjFNa5GSoY~nY4YemLn^Ta3(R|*t"
    "}u0L3=qRk$b^j3?2>|##|sR8q=>2%+t-Y<ixguZ;HX^Z6WC_$sF2MHJz%@MDt32Yq5-!jKaeZ{f|q<=5NxXd^lUa"
    "IKPt9CIxCovm13ksa(tSgSeXMNCXaC+=Ag2e!v_=Z-)77H#VVi5GSB7l^Q6OGWEi49g)dC?3tzG-`{imb7Z9>JcA"
    "G&JJDYUv%;-bsH&~(;#(Oab?dS)|R5TTC;YgDuChNb$auTx)69@Bh)=Qi*bw8&d+F-<tq^pr%Ol#!ARAFz*Oe>NW"
    "<MK=9MCF$cw;z7n-~PV;@P|G|82`|xIra0huk+~RD1Cdf1~XVlzpu$<d8zuF>VU4-mLT5KJT*?3<S9xi5H8azCM2"
    "rgi%5=j<M1Xe{E8DW@2(pPq41r?9e5vAxN$agNFeqyaSd%axjT>&-q78o#1vX|H}lFcr`|jHW_@_e>^IjQw`t20M"
    "NfkQf<JaO=e@|z=S!QxsHrvFgaht$03T?(u8?BQ@ham)cVMZO>?j3UFg?Nz=dlo75<DMRYqnZyfg+M9mv<tyoEZq"
    "E82*vg88iash?I-!#KYeurXQ}R`qMe8kr*Ugso@SI*HD4pFCc*f+QkupSz|Qt`Us&<mz|L+F$?&v6MeuaF)Ap2V{"
    "=5LVTQp#jEcdW90rQcR+eV)b@sjPu2sd~<8uQBItyNWfoRl+Q0@LAA&y%X?}qXmnI=Ct7Du_^g^zw<zn1fc^=@^e"
    "U+C~CBGz@C_xV!v{ZRfO*zG11iz!f%LVw*4TJo>w-6o*HO@;?XXlCfaNZtMm5rM)K7{3D%IAK+?U|MI6!4#{Lqo|"
    "6*0uRUhaXe(tc}+Zfl;eCd@R%!z>`Hz(oj6nZoB%^yFrU!z<y}7C<xdkw%ie+9pzOkX4{u{)42Ttg{1}$1C4lyx9"
    "{%S6@oY?Gr(vgApUUW*Cw@`k)3d#&2Qcz&!L+_Z1(rB=umrGAxvc`12ThmP-5#ub^z*^q*(q8YF$hs>bWkX%y9^P"
    "GwwVxtL_+i85(xmXf&wVtVNC9%xS}w|Rq13u6RE*kTR=%cLR(I6>*z>$`fYuAp#bK>NDEA|if<8RbE=SEx_%HYFY"
    "b7jwbWVoX{8#e_G#66tV3@!y<4$B@F)ZH1$Vj;7q4xaI#8^j-VFqMZJoMf5sH(+LvY9}i`Bwow0t2v)&yxy28H7-"
    "!#0Zih9{PHIif3;lrc9ooxDZ0WMa8&X=^grFc=Js;Ru|;hHOYbFq(jb>#`KR@oMhd3hbRK>eK@SN8ij8w0`R0jLU"
    "qsniB1tM{sxvpUjpVs73Dswn#h?KY#`^xork|5b^FG<8eQykJC6HFVL&zEs{_iX_z%1xQ4<>G;%=@7QIcvhs|Kk-"
    "g$h(9$2daa|KYm8(Dzb3hl$Su@u#?1Cp&qw0DaR?U~uiy~WiESNxoAYG(p2>oTl+tdmagU`}tOIk)@P0Pm&pI840"
    "XM_6!iQsO(qR}V1mIidGqVQvH{Q&rcW!jo>8iVLdZ3I+@UH@wK;Nya)bwpV%e;3>Mo67=7xeO8NJuq2C|U+o5cR5"
    "7J@h#$7ijVjCGOJ4u$o^P$ASyq7}foKQ_E^7(%ajwaqLm*}U3$xCyx@Gd-3D&iQtXy62Hz;P#e$8I*z^W1IqFhmd"
    "M+xE6T4+X{TT;PP`z{T26GHmc0}X`iRhO?D%R%ODoDjJlDfn#uHV0nInTQ^^c-%pmVe>RXm$HNYooTihN_?rAF2="
    "#Mnk+upJXMmEEYBV+i`mrV_)iP0WyD6bV7fSR&1CVGnQGb$*azuaXo`cHN3y;MHlM?=ctQwt@xABg8ZdxbLFOfA5"
    "t~u{S>pZJB)!*bz+t0{3{b55qYf<cL?d9}Q;1s?FOAv|88+$wi9<)9T>~Fc2kdZF5P@vm03jJ5qz2@bF%z$OsNa|"
    "PAfJ??sZnOL<yEhgY!g(T2kXb?r*Y^xTrXkZ&)x65Y?(#&dfj&@e92z{a=3ARlTQ2BD}es`xte?uca+oLUi8ln_9"
    "}13vC#<!Gw6unF%7tgw;K^rW1ZaC4T`6jU`)j+`oFvOOX0Gt$-D6}SUrX}`D@=}*^X(geEH&*^*XfKQk^wbwbu-f"
    "aZ>*19M|GTy+>a(B+R}!OMxIP`eTsL%gld0zAbpm><313)^7(j7iiiIS}>an=h!`-z>#|4`!Ghh4z@frJrP~0!YE"
    "v8^nHoLY6B~LKMpFmV<2S|yE<U;1C8*?{^TliF6IKxCeqEM>wc*P?#hGlx${kjj}vPf8BwndN2gaBS5#h;k6x%&P"
    "bwALGKmh$2za_Xom%cr4>@Z<H%|Qy(EY~gB5Op_LD&VPT#Y>9BC-+NI8wL+>O~Kps+&99bB>w#x9d;Zl%n|?<}RT"
    "Qsc978ATal3CMGOC>o^aVC)coGDVIHT2KHym4>a&#ejo&(I_Yi8q3C1Cgmr~Y6Kq8^>KI?`5bUV!FAE-r1v?ug;8"
    "P?w%q|$Yj-ogr5(Yikv)}4a@}td&0yNz>?$b+H8I$Je9Yh|l1+j@g7=<~1u1aWSh&W{UrX$Q#l3p8-@S|(Q1{%!~"
    "8jxczOlkYu04n@^3#h~&+z1n8h&qWLZ(8LMZ7cOu1aGfJ4Rujt5fZF+kA$flXCRX1g@eSiq9Q?)oe0MtUl;i}D^X"
    "$<gVF1T_t*;L1H&;S`NP@k-jFrAD%`RR+WIluV2zWH+QQI){}2o-v7WYgR~UDo@dn5SP0WEOCYF)*f*q<OB)Ko>W"
    "qU+M_$_g%Z6z;_J3F~9sA6v~GK}ZRevS6LE%L&^`(#0_@mi~IxH=&Dta~*MYuKv?)%qdbaAN|@aCU<|nBGnpiw%3"
    ")us(!$-$&_KphgfK;>B(BC<*|*EybleGu_%B!NhB1Ec1ZDLhFKPgM`)%@zFTA)^(M1)O989IPvx1mFjjY24Vr*6b"
    "DMs2bIhUF3l*FXEC;k8ZTdyn=6|%;elCfMBg&9b9~pW4CJ}TtY=JI9)^C^eak~R$35o3AFCh?Z6y{aLQJ`S*xs(9"
    "pmtBa$S{P5%~`3=j_LuG7{$Uaw+@BW=#sl3&NTsvoG?Be9Zz!yJnyaxw6NprNYy*0tS5ly0<O)v5dg(e+uXORJGs"
    "`|U^PAYaTtBaNDMV8M-ZC(QLA;ydWwh{;}A0t5IPetv}ns7@U2IYF}Ij(ZPf%`7;1W*mQ4qP;B~LG(G!|CqM5wQr"
    "ale%Vmo$i+<gPRZUxG(4`K_cF*~f-iJ_gJjnl3TM%l+VLMvV=&K|aKDur|1Xcejh_9xJ@%M2I=URf3ehor$2XP5;"
    "t1p-Q%h__NZp_=8|2f7UoYumma4zlssQOBBWVU$Pt-LY`$i66*!EAmb2kpiuD-T{<)yK9P=aM@6=dv4%fH2yTqJn"
    "&pv1NsATw4_m+O6j0K%{mYTDpg;dl;V(rC$ZLc?3&|}G?AE7PAKO3Gz01(C}-|NjW?0X##|;^+=hMRqY;8?G%{XI"
    "?$COA3t*oez!B&WD7#HHZy1xjx;G~rUP`=J?juRKNu3s38eJ!K<eA1N)QOFxbng9n*UC7OzIJadhyFE<?N3**g^T"
    ">3WTy(+&@WdY)q<k1&+t5i4MGMu7!0tZJz{sejzso#b;oA^pl&Z(gmLP&rI&hv&K2ok!Ci%5n&hLkM~|a^Mv^@d)"
    "|G^-Zfk7&wVwB-;AB#z#3|P+%;!|}i4c^V60b_OcCuBLhzkEiiuUTk2Xg5bOY?!ocEt1@Ex65vwU8vryBPb^rz*#"
    "lhVE^e%>tyQ^6i}(mWEw%p6&g;14D8%9Bj%+$w2l5=_Y7ZOAGymMwRB7YSTrhF!9Un*U@ad4SUx|<{HrpojD;08E"
    "Xu}_^or>_NZSsrs<OIc5tn4d5BfZZ83eObR&dRZKL?`D5&D41OPaf`8#L`4<g$VO~@drPUz&qc0LU5aWgJ^k4_Yx"
    "*j=yIYU@@^RTyoCZ9#!|2aqw8tJYKnzDMSb))QV{Q#Yg$O`O4cD=Cmn0Y{c0`PK;SrCqlGXXNBD9K_`5;j_atV6i"
    "P%<y7__uNGyou=5)xRA8GHi@mArm#FO)l|R*+@($J4=6b;hAqsZuZ1>#2)NGnx<)$A;`O?LoWEcCmcHB!nD&UGwV"
    "veqhP~F$Y{X)^fD0Voo4~}|XExeldG_^6CgSd}&n2ye_S}BQB6M6B;j{+?2U&Bd@<V<`mEFn((tEvb7gVLWb)^ZH"
    "tVp(4UQuv$*Z`2wId%~Ei^ek`;PKtM7(Rp36Ec7LPX!o_>y4f2uvPjGO;tLH*0bKx1d=r+BZwa$XRUv0)T3rbK?)"
    "t!hMU#l)V1XlRbZi>2ht1xsylX;c7{6UGy3_IYaCI}0018V+J912V<~=Or;8f<4(m?WV<F?CjOonExm;IgB1ET%)"
    "UFh$pHMPq%BLu9W0lmxVVnp#y{8M_IqX65X&@Y?_5S-}edJ5eZY_;0+To2YEEcyyP79^_GHb9R6XW-5$cHg73ZTh"
    "4;ND*{8mj_VfcI&RA&t)W^j>!a7$@ueL4WEy*c;WD@Bsk}e6@>qv>HixseZ#A3SxrbsKN&5xB-A-~!e?1gsS!ntD"
    "V2)DSLPFb<K?c4%ddqiQx;9D*ZUsM>-%rmPwJw3M<uF&x77$vJvyk}Dz7HS?kR435WL1E4Z!z^65<SuNzlUnQv8!"
    "vPhXs7wOZ{5eL=;afF8XeA1t$E7YxqHjbnkYzA(Z`O@17+2P5AOr|Ilsl2X#sE=Z=7JB0(2EW(*kWDDpv+lM$=m("
    "H$hBzm@*F7rNm^7PcHF;aUJqMX!MpANRX#+2m*%dUe8zPV|rg^@=e$;bs{@6&H!Xz*W{2Ub;%w4OdHP6(X$)_;0~"
    "+Q^Pw$+0J`wFaFs;P=sCyBk$Z<)mXjAMZ*&AE%4CBtIML5qp435G8gE*jzry_S_K;7iEL)cZdhVLhMMs`4+ZgIn`"
    "VuWrW{u3nz3at4s>Dt2svFFRU1Xb`!Iy9nDK}#tp1Ib;4Y`z9X&>$1BD3>-jh<Nm3&>`pAONm&UpgH_Y)7Hkp0$^"
    "l<+SM(8Gwj}vL*dU|kH8IJ|m>1vWq2I0M`g+#VOz4~Q?A;cIy5RFEHK%1IAysh^Q9!*FftR#jBYW9dAIRl<_*Z?C"
    "!l+h<Q!;?1FK%#uZq<z1d%6^h$<0DeF+nDZSn-*g<B@s&yDhl%f(j2@0_!#h$Dh>hb{;L65z^br%1~4^H7w9YWGB"
    "tR-z_O;)S%SkyJpTn2f8`>A?cww}14hw|qfzQ?puW)70!E?jmM7?6B$F}Uc**PKmSdPproSpL)BxL#6NUGW3T|iW"
    "HITo=FwnOdA5$vDFu$U@f$#MjTQWJfP*p(e0c<-|hFCU6v4spzC>z=NI&W2EBIk9KCTIu*LL9p7fLM>PYhY+`wjP"
    "Ks2)-C<dfpvu-acBcF?Smx?0kM5qY#~a4ZE;k3E75xb7**lnM8F&XIl38#<>nRU_t94v7R?MQm)Gf+K=t<w@Zu_x"
    "Nc%_e71JIPxYj_Q!AmSD!r^@RhzJ!e*rb+ildv*)PE5l<cV#<4db*(DPD#4xXiP1vyPB?v#Pw+NKftS?u}1J5t|2"
    "WCljn^Qfy6}W<+Sm*qDy=os<g*IAVfP8a=RdKb|g|&)<zW^I`X`s?~wo`Y9{N$;X&p6$9)H+W0W7YDVP{RLLG;8!"
    "6DGqcqMuWE3@N3q^lRlQb^o;A(+^Q~&-|Dl;#&5JdLRnR`zy2_uSB>?K+$!&^a*A{s|*4Q}4ZonEqaa&UI?$Ck2S"
    "m*F~J4moahRBvWO@7EVQI@6)~T6F+#4VLHDF3n-f=2{gSJ?MF3xhN+15M#uxnk?G}%kH|F%2)PS2)#2iL-F0&cI&"
    "LMPS}=IxphCva;vTL$uvsZshCI=HT-xnRAR63*Ciy2C2$@sXw$}HdtEaRB{@6ba40SZT$wu`*j^3*X>V|h%$jHKq"
    ">zr$!l)=szO>Ehh12mgK|x@W>yI^tgMC#jZYd1dnFRw0%X?c7Yn^RS4Pu^M@bqs_^QB+#TuMwPzwbTmQMEu!zI>D"
    "2mh|f#rWjC^<}ANjNIj4{#*JZ3+|7c>4wsU^s!x#>)@hU`S7zxv#T5UBW@-_e;@<qW)|_Z#C^52gmYTk8`@bGM+e"
    "0Dn+2JoIduNBoN28q|?lj2g;kG}{!|gkcvlEQ7bH{NW2ID-u<2YXh<9v0;alQ`5`TCCId=rfG%^k=2HW=qyL>~ta"
    "s7(_ejprwOzW|=dc^ct)!b(s_k6z99PY#edo$dYn^dLEWLbbmR{(g9RcAD^KNA{?xoUDD%fEOS9a&VG7KRJB1ck)"
    "N_+rb|~2{@Y&MWW>F;O}QN>d}j*PeC?l{-&hWc1*xx>?6tEi?idyBN*n{!O@v~64-(FspQ4c;on{y$X%-M?cLWfD"
    "rpTJyJrQv4Od~xz;yh%RRJYwEt?HrqIY-g&^DDXy13Yv<<^tqlY_%wj&Q7w)Ab@bId}pb_-OyYuCPOequ0z=Dtmq"
    "+XmBNyPc^uc$hP(iQf@E?QcbM>n62R9y=_2Dz%7V8Z3?2h&oiuAZJP1-w*hQ^L%loNE^a;8Z!mK!oqnoqHC3F~4)"
    "4{LyuSs)OId!i{B&o+)Nkp;slh#c2)1dm8aovG&FWsqx2;One?VGz7>-fdCuwpY-cKGMJlT8k^eovnPr5BrYKObS"
    "a=fM->v7L*>T#dbkh-_)X8>yA>Lx>hp^3TH&%w&(j-cWQCjEZ0M==d7)n{`MQO1<fOPQS|W@MtCV*Ke;hlXO=Bur"
    "8o4qc}gSY8hY)C%PA9@;R@Mg3;U;+&MJ^T(ie!ZoKA$T`=#r=tB-p<cmva`+2^Jtn4%=EaBu-d@drK0xBDy8iKzJ"
    "c2iVIXserq^#_o>>ZvSboPEeJ~`_pTUtnDkx51cfnrx8=~Q*xLTDZwJ$}@BVxSXe&ctNJ_b@RYI5IJU{((|fO|76"
    "EL)G#f<^qB4$vL@$WWSiMW^?`kNN3rfa5O>C<o-@6k9M(wlQPlj@&9oO(-&mJLaR=Zs&tOM<AF?Ez)&P?IE7VVAX"
    "jw3Vy$NYxxL4all|kTFP<GGho_2r6Rdc|is>$PhDt9MSXBb+O2RN&S|O*>;sOGE!$nfY%^3*ufYNY}Q55FEpXCE-"
    "IFK`okVe<YTaVU{q`fVIQ>%n-YpcZ=+P|WnTs|V0JkGB$PnmjaVP#uvw3W|qR!ix>#ogDlbTR-Pm$8pChAGK@&gF"
    "NPRFjUzqr$vPJxPE#PVJqtVCyiYe8UdRvb0>GiMV(xZNVsgn%mTJsrMFer^iPVUPlAO<m4S5JwEt*jX*IH{Nr;)r"
    ";TrP++G&CJ#{4VE1yK3117IP<$8;0u=&*$s9#iOG)<l#ob>mPkB;E<!h3ME(yLj@_(ug|Z?eVmR=0-rIX(|q?#-t"
    "RSF3bEiRTMW@#bXMWdTPY2&PzHk52$8pFiE(KR8bcKBCsZ$NNpH-&h*4b9;k=^5${-Z_)p?qQ=2#!iAzt|2f|L>u"
    "fs3-T?U=t(5$rwwk*vrqkjbUfaJ;ZxDZWsKo>IwPUowV$6UF+)oz=Ocmvj?!!QDIe8uJlWc5U%{jt*LVywA0B{)|"
    "+;MMS2xxbafbp@XmJI@ych^NpL?NA0<43L+jVY`JPr~7G*Tr-qJtFpw{*bPBgXF+redzw1VeM!sU7)@FT2lT+29O"
    "<F(yx1GN&oM^9vta=9U=ZZUSllBsdjYmJGTeAE5nfa#5jh*eHZ(`4g>^jh<iEBv5iNGgkC8PZR@nS($E691!rw`Q"
    "!J^IE(k5V$?{zxU1~}sHq2Cz(Np?2p9*+S${J)ju^&!U<rHapnA!u7Oo%4}TZB+!L>S8mCf6wiSX@Z;JV5g@y+u^"
    "Th*~_Wf*D#x0*lu+YABbN7zRtGnvO=n-qy)!pTN8k-<xmzy&<=^Iiw|(3&eHuCF0i?)8eAX6{E=7sUn*+T|ijl^`"
    "!t5A5XAGE)zH$td9?Ji|k}U1*CCTvDg9bDs2!^eLz&ZWk4ndf<6=pzR3D;uU}?M?V^c$&wK(a1&m1=p{v4q5HGN?"
    "O~62mUK}!zI?e&p3fXOJ3^u7#T}v9N^(&5hT;7ufm{(2@&TKV3j6X1mrDy~nQ48?#Qc7vSLH>WZHQH9U$Fo=Sf;+"
    "`wQunU&RPd%3pxFGneRQiH8NUq)#R9l3IX%)P(|RJ^A~6y^v7=*NToiB?afewv!Fo(y2P|Q2+AtNE95wLb4^VmM6"
    "lfW<ODZ4(Pf?jE4PwUjLj2NTjUj+X{21fXT1y{(0`%ENBa{}T``1~hHZ?8A<Sqf<=)yFOOGrnctL_(ARy|R(3uz}"
    "<A3=mx^h|QW0wA(n-TMLr`9k{Jikynn9rY0uN<+F}EIQ5sts0LWt$#_Xa5l)H@zd~~e;Ql{0z%aU;BtT{iOS5Jvg"
    "a^6j+*LXWiOI5u#&yhy~0jC#BoH-bNV><&<N8VB&W;8YP=-zdn~$~^wL6#Ta-wz@eIHbM?1<4>)9xo7ncU`NY)EU"
    "e=5c@B|4>^7GBFC%lk0l)v`}15qxi~Rc^EOq~lGjC(TOblTnkd`@C=0wPtF2Y=kJfl@XZ;{=9d#|0{}7Mj2u=9;>"
    "n_yI@Tj5wp0Wvu|3#+G0X$QQslS2TL=-no$ok!;%<`vJMw8w)#5C&opA~TS!r<1U7dnWa3I9GO}(Ix2?2Q;yDJ+-"
    "i$9U96sKCvL30@tE)wJRi{}RBr3~nvWao89fsXEo%MhhP+RX_Ky%kC-|pKn%ZERD)%>9h^dpCi)70;MntBRyBoe4"
    "CZ0EuCw6H`V9D!YBEq*g9En~(!1IOvnKqC}5%H_y^m?KoUw3lGM)Yu}~l*Eh`mx@W~>?k!gO*~N(m3liQA5S>THN"
    "_G%Fig2z&9XsqxHP7#j1sNh0U6e{@qjB(#3yvlv4tNgu5a^{m0~=Aiwq0E-J$?)Iuy!U2Vy=GrpXF0)h;*O%;5?!"
    "JJJrxwnM93WZc4yTe;(6!*i`%bM*G%-TWu5&v1+v%dP!i5B7gce43p6^+({)a+=(LHD|_@0HpG6zyVA_Ye&a+A2)"
    "J4&g1Y&$UwG8Vo%Gf(F!;`uu|ANAQ4lbLgU-5Ao<#irNMACaiSe)2hbVALLQ$SKMx>ZBgWu{z!}?n20L}^KHMn5$"
    "-6*Q?0Q&=<2wQ0t39kg_=gouTr49b7*wRph!C13dqV4rOzcW{MkVjx7@LL1^P%-k&e{P~Ud@-gZ2sbMyV8f|YLVV"
    "tn+71MuU_!Y8EB*;0G+=0`9E;WJL&wEbX*fhkX{sY4B?sIUT9k#5rDchm}5ED;fz!ZiVX^TDy%*Ejbt%CU<4X6oy"
    "$q{=(UJgcd}8d-$lm2@JHw6Kmk-hqXuZ7QjBD4l=JrCDILW%Hd+31z^&w}XOC@(U_0B*7zV_Ph1r~~gN|BJh%80*"
    "GjbG$CqRgwf{x0~FKIkO+_^z5z5tt+r&AujxZxnVfWQ)QHKf(hQ$<-rMH53?D}s_jstrB;_migANNS&2*uI;@<#Q"
    "2d2`&qP9XvWt&Kdm&g8|{atnM7-jwxF$0MpXNG>7A_ky+O%wPO^f%Je{n6Fd<v3t|FN!gLBEK&jr(gzV;|15Os~0"
    "AM+RISHrEF9Q>aVK{0`MYeGxroE(qrw9wV;QXSv<?L@a_><`vvujQTn0uCUjtv!km78c%VQ=<RS@Zo9%(ov;i;_H"
    "tQ~`Mx$FfY3j>Cei>`VvqQmy1~bF8A7xkx14uR*lJig6kZhe`L-QcRWe61xdtM@TY~Cx_3T9XvjS17<pKB|tpbPR"
    "$2%na*yoPKxpd;2BrgE83n_ZcWS<Cf0Re%_${BT%a9!jvf^n%+87STFAnU1Uxvc+u7{FvLB8KY92d_{;|rl<@A<K"
    "+T0p}n`HuIDEb0rPmm}<yMM!7y9d62V<|`{ugW#vVe1*L>KyEzbBe3-&*sC$MI8~FT+&Z6Q!7^FN=LF>UpTTCBRt"
    "d>jqIcUQvS6Q8caRgfNvASrY-rB^LF7|erI>D+XCTph7r@5bSR<*i1|2QvIBfU>1@=DK(L)%G7j}%Ll9sbjYjph5"
    "#=s2JmJ!8f#?ztG%_-gV}}!XGU_l>O8;5PBm$x`OXuVdqyblRRuh>5;Vc-v@f9lny|~C>_ZPQ;0OZ>YTqB)hjg44"
    "4H&mwKwW=a5#?)XpKTFPV5vBMXsn8E^9Lb|ZCD2u}M2{89sq$mMUQPJ_XD`kO9dNAEy(b4}e~80)g?^T$e4nLR(f"
    "7~|oN#dupaobwjFS?iMehvbl;5C5=QAPP$e3{FgnW>{>^7Mcyw^Ay(sl*9^`eoJXVD`ymfUrp2^nNQ0K4-UUOQyG"
    "r0Ty*_!ltXDL_^o-;=zgs<gMZhB1)JiFl<zZ!a$U7r-(}+x<)^?kr0&7=@q8m)xX&@8~f|+xg86zlvJ4CAMf}ov`"
    "<crz$?az7TikQRcGjQoaPbe9dWcQ-P!LU6*h28|Jk*-s%S4$J*v5dqUQKuBs7*0busa1(n!?5je?yH#xsqEk{8AL"
    "3+&piET+u{oPa*E0_Zg#?D#hs<<mw2Ltv{x=s;gNeimAj~3#Rp-D#y$1?T-4E2%b1LP9KTHPuOz{VEy9D5;ZzaOC"
    "r8U-ZQWZE0hxvtRI&^dP-7Z0!=IBIhvS<89Xz=rFjk8bj5vE(p`DG-eakkoPkk6>ZHT_tyfbyPTfiCc%%1_J=HMI"
    "Q;-c@Dr7i%bVOz8jcMUn5b91g_5#3~gAzN_V;>i=jkSWbCfK%$N4#TR^_v&DpThmmm+yCqb5k19i^d6P|u>JpAXB"
    "8G~&xlXLdcpZA2Y(ZGz@*W{hTF>n{&rW9RMTz1J0G)AKj7RXuh1UTyKONsH4?bJ{zK^TkHJKvgJCee*%)i2Y_Y<Z"
    "io=1MTe(a&i^MhHEY$Z;rZ2;#FV8KCFhA_W{snx8*EIC?xfK6?7chzRuQt`tI}ghVWWhP7X`pR$BIXnGP{VBYCm@"
    "kp+7U95`kyJEX^E>XSr5!UG+srRg`+-AYfyN-b13vSAp)Kf-L*M#|WXbWxr8T_x;E&5EY-)xcN{i0MUVr?F&Q(Kz"
    "TB3e@7F7;YtfQf^DwLy>a%=%andGNl%9-X<>#yx)g+-f5q+s>^%GRI7=Av8zlb(h$j+BLNc&iO2PW)D3jW&!a!{q"
    "+#e<KrIHZzr6?KL*JW9OSEPPQ=!*Y{b;dd{Hhn*E69iRgQTAIk-e=iS>h=^p_Iy<=EzkK(h_(JbrAt=hPhmXef(}"
    "%BP7j$sJ;5I23ZmV#!mXQuOHhLQW{`T#}hA-BThfEipLcQSzvXY2jMoJpPk~OES42Cj*V_Ed_fW%Hn6)40sX>7+g"
    "rkxL&1z8v-wRj`6Z{WTUgyQe?9fyDiPIZv!>p$k>oh$)3D8iD`550v~P>M-^w3_4>Yg!1cmjJ)m$GaY^aE?ah<Q`"
    "f=e#va8<#5O5@Kle;X4xb@`4*$cp5C#?+Md}I~nhsbWRWDTrilHu6+2<aVcl_+%)IjsnUvpFlp=j2o|Bg2|U0?AQ"
    "cj(C~p15YJ-*vLp6juBxN9-r`7L^n{p9*$0b-Fx^A2ds=QzWMt5uP(m&Ci^<O{O<e7ci--O_5IFd{6o5vj(_-id;"
    "HB07vFsM_2qZp?R-1l`ELCE*B6&RTzotJ{)exAc$j{Zh0&rrZbW@^jG$<gjdAO;;`QNvV%WW}$aOon`q1@{p4;6>"
    "xHGqg;7XlbQ*@=w>rUa7b!%!M;mynP_0T4y@G*bwRDHGio)Dxm+gdca-`U;`Wh%3+N1R}~4d~;~^e#xWX03NdC5^"
    "*sLL#M=YbU8L{d+<jXKuA9^YL@L8=5$Ct49zsxdznGdEEsmYS(mUbTH`<%^6a{E?Y#FOWer4Wl7oTHRMTs{Pga~Z"
    "k*{g1@r6t8pHWzYIh6huUprqA^kf+M$3yi2)W<yYGs-J6a?d`76nF=6ZSyoi*87Nhu-^otK<kl>Q*JbDmK{kWk76"
    "z@<u!r^453oR(U%ggBmd}R_F?)F}fTs4l?g*rb%9`Iny{OOH<e^`Ot0qRduwG2@4IcR2zro@=5ZBGz;|TQmA>VQN"
    "cayX*U&+m&KcmY>8<9z)xT26M(w<lsJmshQ_DK{@y7Ea+BCE&K`+zPtvOtEixSR!+Q?PT#@O}_^hQX-V6Y-L`$5u"
    "<YFhEKQU4((8y>i8pGd<^c|0e_L_lTj)9C2DG1%5M`7<>G*JWS;lG?ThasM1Ou8a(jg#!hpXZ9{^b&Vj2ly|FvNT"
    "&F<)X_#3zJ==j3>s5U?pTFzfRv~<P0Q-q`fXyI|U<YRvb$q>qMI^c~sH2`Ic<dVi<h4NZ}pIa^zS=m|+g+lr@JVa"
    "{V-#f{8}t3AL?wQR`=4lh}a^I-auw)ZjPU`xVAg7YI$I63@aBY+U(ni6>Mnx_n}=z1ut^J)OhsgOm$JOKX<w*~m>"
    "a*XN*O&NIz+o2It|IpOCfbB1!R<ai1b>A;7DAflF;vW0<nA17GmDCczfv`TkJ@^GX31RxE2wVG>{IZj})nOo>$lF"
    "%A1RZdIBh&PFrWyOEW5wq`530(}<SE?9s4`tnQKPJB#ZlSfekP<KR<!yAs1<^-7{!~g(aKp^HFp40Lq#BEg4QX2i"
    "oVF@GQAI<s3$b6?cSQ`6b0_LzAm}+V0X8Gva~|P5=};%<E;o7<GO@tc&N&)(ZhMHN<Q}i0IQt(d*NCvjein!rcM("
    "mel1L+g0X~@_gO)tUu>-d39a7VCSez5+c8<|r?EY{%v6jkLZmE7$S7I&bP?hF1rORT5eiVvgqnHac2Ib2o`{$ct="
    "MCUYb+vm4{AtWD`L{vjhM3Ne2)1wX<5z&~$2!_v;mU)N&_{~m!3ZAgUOlB_A_oU4uYl$eaQ%!7q!gb5M~Yq{hj1f"
    ";G6I!ES$&*TjFc>2Gq3I-IpK^yiIlMc%iK>9kyd=F=*@HHOL2U9f;3Z{Bq8Q19MMS9lH}}B7>wjqF-OAAjY!Pt*)"
    "+MzNn(&M%+gzlwn4uoo$A2B@7DKmGwUh@Mu(In9vb#pnolo^KNDL>^vgxIT-<&+!K_8Ng5nL%kF;(s62O?vMG;ad"
    "yvKl}z7rU>gur^zfAMvHXV);vKAkPCh}xHAOW3&awMvS@Fj-X0*!#9X35)>PA?GGYCCHvxoS~_7-6ruR(7|PYoG-"
    ">JvX}E%f<aQ4wMW4e#0yMf^14LD=&`O>7QT)t3%%qypb-cP=r^W<QfL%@ev*9l6~M`CRNuH4w8O}>5W%A3I4-~H0"
    "w$L4vIRxk1D+&jzaE|%`G*+*UBa{}mkID@d5qxI1H{@l*)3b4gJ`8(V>8n74YuVLTs5)#`bp|SFLB6(=O}Ec&z!d"
    "(`O$PbNY36B$>YN(M3K&z^*MN~#T`#E*oa@`KpPUrg+$;J`GS1D26iqJ<<2ZCjGDv19SpZAGdRh}_hibLBE6cYWR"
    "{eb&u=MFCx}V|?T^DwIR-_j!_Pn~PyH}iM+7j7rm+~`i6JALsJOjEInN4qfAAe8fIU-}Kme%19BNNaXKn}irxJ_{"
    "PtPb60rg!RddUGd^mVT4K_hV{Hz#_M)Mz6Rk0g+no!ZJ|c72ejTubpK0KX2APCnBd4!~NGgmx-rhWp7m<<c=#IXB"
    "_}3^z@t1qN2AwpL1H2JS0>X(B<FwVo{#J`D4KvnnbX^@yNsFeX)!<wxJs@(qJy8^}q0+s;)y^4w#@A6TVw%XwNAK"
    "(oKBy9~B6U19P+?Rr=t27a;Z)<q4y65i^Z`R@^^3wIB;9WdV@?k$iUa&!jFjkMSa1p@8HBqq{yh<WA)O=v7qK2fZ"
    "dwa^l6fQ@C>SJ`|8YsT1CSX<9$+Qo`B8H%6LYTF?@VwSB{w6TR$g<;>a4^%8As9<M(niwJj&N5wUq*21nkV<svN^"
    "Hhz%pOmJt;hpZ>EpBn4Nj%6;n5Rvr{O&usYWq3V?iVYa`q08V$5sosOd+}Z)By&M{kOo6=hE0ala}gB@of5E0H@$"
    "E6`ZLv8rUAQVL)<9_JZmI#jpU&EvI-+h{{x_DzJB{ji%n$Jh`F`Zb}`l&W#UyzSxk!*BcB-}fK>&|kqjKlCY@q@S"
    "04iMM20+(!#c-)?%3>Wk0-yXb0UO8}i%+^RIWUd;dpId@Iwq?MYe<lY7MD05<l*|J4qT8iPeyu11QGFu?7YWf%Bm"
    ")&HH&YQ2&X<rt}L7+_6-KX}S9%6-`f_)N$h+-(#DK1(jE_`eX$?=XE7I;agt5gKS)W(-Fo#DVU4bT~AJ^+t8;!#P"
    "&7h&|(1EhC0NDbqAOkgy5s4J5K0l+O?MqHFxFehsGRm)Q0`&!h5ZLd<R1VnVH$t<hF+LmI0u(_@b3bb5$JlhFm-&"
    "Lyw9A>sEN<AiCzMF!_J=oGoX+zz~n88*%B1X;HWGoJ<O+f>H1ELk?yx>}{TIXa>$PmOPYE$?cl1@0(y|tlC$ThEb"
    "@OdKa3E_vgPmh29(utnLFb+O`1IfjqkYUP%_Ec#!IPz*SumizpQH@6cVsw@~J3c*2RF=(wCSYO^23zBZxW#(S&D5"
    "tuqOp0m8vkDwQ_Kq}%!U(Iv1Wb=!bYj5d`9?@aO<lCvk%%}f`q)a$g!peM^!_nt#`mgWJ_M~aLnv@6;)yw>EI3D_"
    "R+?xXc#ND5yMEoxJAT5Qhg_$J+vmpNz#Oz2Ba?Nh6YT26@QFgu0Tvu=jdht2f5{R);K<?|0KQK_KOO`ny<?3uBju"
    "x#-!rmnG-?pU3Vks5z(K!(U7}r3<=L0wH;3!mZkRKoTH6U?$^jCu3X7nry7~+M)YbREtw^IT-(bUOfpaWWr>@F+("
    "`Il)gL2*8K*grVcC&zA9mN34U3(WMz3u&=yk0tG0GzD$(viZgj&z;r(D9_Jic{HsQ3QH*U;bzj!yqBUg36dxO3=$"
    "f3(+QqQ+OZoVW6(d&NCxwrh~?zGnL|Xy(jz9e$bVu0<@J>D@7^cCAgQL=|U|Vxl0V+KxCwh)$yNgt}q&CugJuT8R"
    "+zo=MC^1)bHC0cZk81#4>k3P%8u-%q=e3K%4WAtSkD-HN`3wjE#ssCUju>n0sfI0UGwld`LU%HjieRCHJwmkY?2H"
    "c!JWM>#)D4NVo;?8wasC9`s9HBnoa0OM`hcPmC<d^aj1WXqHESSi>f;Ref00vyowy&MFRPtIwvmpO$qlc&{nl{zx"
    "A7)UO~%qMw=k0gtb>`ed676sXDcuSEx`(qGXNVuR}S+*yz#b2QWA2x6*=C0To1QDQyYfV%ZioDeYmYXcIu2*c~YK"
    "1*<xQ^EN+MO8MMRH17b2DXq5d{sz-gH=IsieF*J;q+m`4I7e+PWzgS0i5BXe;^e|0ban&Yeh(fdK8_)RUaTB|glq"
    "9a#fN(t(J>Lw#L@zF$s`Up!BK{=+`;>)wAJ9{rN+AHO&{>wMnD7NRE8-P9YwF~l^~|M5qv`Da$Q)iZs>I$QJN9i`"
    "oJTS9oP-pulC#LTiI{u9c#=~K{%HT@=?@Hi&FisfXdtBKVVPSB?Y+HUBMPQLF})sUn$R`G%ANG=<d5fQVn%6*~C="
    "Ll@y*b=fO3Vb=$;X#W&(IM6Lt+`0EsuY9KzD<=+wZ5+4p4@h#so1AXKDUl2Kc;Z7Z<^@V2W#-ojYK9W7H@>8MTG>"
    "JiW|_eMxCTgDb;(-QtJ!~xWn~26cTzocvrO^Y8oGeZXjH>)g)|e9>x~jAYZy;2+p39WLUzNF<QZtOPCAVx?u{G*Q"
    "hZJY*Rq1dS6N%6mzafynp=cIh+cFrejSa;D|pF#+7XnAktVEX4H{5sGY8qMo`_qXZ=lPAGXYnV#6$SK^pq2<bImJ"
    "$)dP0s91j#D=0rw8G<${APWXptZK5Xp$n>ly<%^}%CTB1dYa#0nhVA;aXsrlwAvl{%nYJ2b0;UNl!;(AMO46;MaX"
    "F0DYJ}$%$cV`db}ez2adpLkR?~UmipMHZVc5gCqs=u)W&)cDeA6`FEW|0reB6EB^FdBRt0^;A=ds;Yp{UuYC8J7i"
    "S20?L+Pbv*`9MG*Ncu!A?{0>HxsKD<3Dm@cNE;s#2O@anOT#l&XZ!cZuXcZb!Q9jy0$ffx`&=z2Hh14DL{)uE7gN"
    "N%`e4EpyrNUTS3$iPZy;<WHtvYbtqxaBavE+g}V3oM{bb(f>xVsVws;?jRtGxVSUHNgn~td#e)Wr&8a^+rmiiodo"
    "I(bsIvmC(L#Q)y&H)fjxfMcXBryd*ng<%PHAXTtjI&pfl7g)C(Cu_A9qh052X9xdJOTl8a;C#e>TIJ)}GLNoN0Zl"
    "leiQbl;Hgpc5VsV2h2drLZhE|&QZ)LLzc`puJyse%`FI@u$IH04`9%Pr+;Wu42`{z;90=}tp0&9h0?=j*Y(@!7g)"
    "{(H2(eg<hPy)m{09omO03PiceC~niwUlo~ulnC>5+Bwwj~Vtj@!<M8O!H$DlR7dQcX#jEl88mF|=0B*ly~^{!uJ*"
    "PwtFYrF{tEJg&xAER|Hr8^5`Zmp@@L_fr=upAR$0H{@xj1O81HnKcDlZsQX9$?E|*h@;bz09#HGseH9SK4$yBXy)"
    "$$GX#N0n~VQ?PKfDg9Gz>VygZmYme=HP4aFG)}LfOlXYj=z-XNbGP700WnL@4x*xaFjgxSKYPNfmw^-E$_!|niWD"
    "YWcQB<*~%ry21Q)vthGhGvuFN#N!dKc3ZBAj1R#7il1t?d!yb}oK|LHLt2n_-X%1syGzM!n4_a?LhX!r&H=!zU}O"
    "9EFw5a;7JeF9Recmq2P{$P`N8(Ux?zEN1JgKckoqgM(7S;(eq663NY-%5y(D0`xrlb2*|&?@$><QDj0k!ck+}i1#"
    "118cQQ4*&Jcr(9Uj0gQ_|7N}6jobiV^){-^eXZ|M8<RiwY11um|-8Nkl76%E66l-m7r9Ho<07J;b*oraeiLcOVRI"
    "o;{iJ6}!hNO#6PnM16FCPjmd7x~R{6!y>5*4Y)ig4gBNUR_|d!6+x=iUt+5s$GNw{EnRkeK)oS>0&*i$nEj^^HRS"
    "sDcLcKE>NR0W;3h+)_O4-z2mII`Alp*K{NHHrD&90JbxfEcF>i*W~;q#@N^pR-k-07`uTjEF6L|~tm4bv=WgN$KV"
    "kvB=GmDJoY+LA<z7doj77XqCaYwvm>Y3|!%x=`z^1eileNM@a7->xh#Oh@5t-)<*x9-kpLORLOTuswI{KP)+|JAV"
    "BA-^%W~3=NRcC`4JiUY1d&)wyC0(T!WXrMs$|A>}seDeUuJIz{lvx`Gfw7!6Lx~efSW@9?b0nsaO9b=GAK8d_Q<D"
    "zeS}eR*McxQawbE`<5q2Ywi<lLcuwo>8z2uujWy+eVibz@!c|XZiEAnrAsu3#R1l7pnjZ=*=k-I{*W~y~i{UlSZg"
    "KAXLHpPVazf|3>TrOUR73w-WJ-0xU()rFq_wqw?`78JGSLX89?&Yt|<!{`}-<Zqax|hE-m%no_e`hX#?_U1iT>in"
    "m{DZl?v+b>C+uraOYFE1BEp^APb;n!mj$Q4Jx7;1O-W_kjJ9fo8-ja9hns>ZK@7PuEc+1|g>)!DezGGMZ&|CRKyY"
    "h$L${#v=>~FGN`9p8z5ADhydMkfuSN_mj`9r(%hu+E`(#qY6gXIlyl#!_=P<EKO*m8qdnG!2vz4nR@p5kk0)^M^$"
    "mW71STMdy@b@5~Ps%i6S+GqL>eOu80Lut=>u&mQP=lEJ%EzAnR=voO##YHhe9z}rzq@PiaRyNDW#T30xHeE$)2ix"
    "VJOIH0HjcV`63YI$4vbh?_*LqHaQpvw#5`$IRfiw(UfH}?g2q?Q2us{r6z82fo>hh8r>)BV(4o*g4SSjz#fc6Zpl"
    "^s;daW2EN#VYIW+DOd&l4BL%sR5Q-xao8g8EG(;3j;2qfRO6EdeHB`df<+rAkOEj%wCllelbkg|Lc6O9;_XHD;(W"
    "H5hk?qoKCpwKOO-NeAR!&`9jOlrT(RTnhys#{FBG(a`^wadl&vTjw4_6tIX0jSAYUQlw*4xI7pVJD4Qn~sU>N9vm"
    "y^L1P0_p00x->L@```_gl|?O%Djl^4_y2zg>%%M^8VhtE%hqFI6#N#|$yNXE<!3+pa^Y+5O}#CTQbsIR-j*`ha(P"
    "n6SNA_2%y<dD-G0yj~rSeHj+-dHI~aW6@%K8Agl$1b1w`U5v*t(@qy#k}TfvLa!`thf_*sxpQ7VEpF{AtMV>fDQu"
    ")#FHz3~O;TX`s+RMe>?1-1CkONo0u)ACaJoSb>sGMBWtvx6bJvw2T<p9(-TUFq9^r80*9$IiHvqv;sC!$#{&&ze("
    "epgVns<Zbm%StJ{VxpMxv9OZIJB_$W95)pL#Rx(gVLQ<XzuX*$CIDVH63LYufN=}P|)Z}N*P?*Dk8lnjIdrbx;{<"
    "hRi;#QJZ?JBiReH3BXJRAJ@_ff6^yPwJ;3jJ>k3=6@e2WsWXocV6yG>3?`h_(qR#QFCVYv%L)gj1%)}!OUMk<v|F"
    "wJ5Y&Av*^H%%a?xlYd4m<CO-<aLlLsmJgfQ{rIVUl}-8nL?bCN#c<D0Km45;xn!g4oc;M|c(Oqo%3IYm`@@_j`0)"
    "YSDm$kIEK&4din`L3Nab8EFvKM0$bo7DH5hK|K7+fTyvc2edhppVQeoqjsV5rc*jsle{9RZV|s~xWzG2j@U8fuDH"
    "w;wv6!782|jjFsOaY@-W;m$0Tq%HB!Wjk@KKffY2r+fxGc6>m?@y-(%aG6}M8`bGagUI7dv;+mx|k89|0B!6rZKb"
    "AjkFr6=E{Yl^^_WtH0;ffFH<kcv^oEk%>LIOT~``5DvZB^%$_#vVJr&Q=)QCF12`$KFJMQJf!tb2%@IV=b7&W^#O"
    "t9Sc3_5;Rd0&XT*RH7;RRx5`#{61sF6VeRN=dDKi4JI}CS{K0&=y5j&+$Fa#eromAsIhx#I`A0|Fk{N1kmPA`{7x"
    "C!uL=5L?h4jH(1w+6F&p0yHGPdd&Wx1^GmT;5$`fL;H@$bMg@;)(-29vHTOSW=fB}ecE=Ba~Gj9ng5*m2mZ+_7{v"
    "^IGR`-ox^>;7jia3AZAuylm6Hq1XfpkFFkEa)_u6j}ycx*QZ%8P!(Tj<go;Gv%%;)NrEw0`n2uEGfm<bYuVNaLi6"
    "1RkBc<@`oO%@P40F2aLDp^CmG_%?b-jqqd#e;AJKJOb~?S-F$q0fEFr5*7wiJ{llzLMvnBW151#aqg_0h-3!%cfi"
    "P`c@?ZJz8$x?s<9E9e4!3A7;$!jNV|2r|`O`s=~KW>kE_`d^$n=p+$1C9FCQS$sb9Os@tCySp>C)LYHt_wX$6$As"
    "oq1(2(QBYcGL?B(MK^8#KKv6l06fPCODcDwpk)yJ5<Pk%e-=>wRs>XGlu&<PcPmutaH_tg)=B(fim2fS*5)+0rk("
    "Bi~%c2Jkwdh{8NaXt`Z{8f9JF<m7N8l0;G>>e6oa=IE;Ci4ha<r1m7-lmDaN+%;6_zmp9B8oWd*^sYHIyuhRO1{M"
    "6X$q<y!ZxFDi$BoSw6u@vw-dV0()W+8^lz(st^<pM?_g~mR!4tW|4CWGOi=XI%k}p@6%@EF5Y}J@wO_@zrSCDtqF"
    "Tp$uc)PDK0;Q(=mfwWgl`xm#p*Ryu!j_=v5(H%gu5rco@S5JgLwu*PBH^uzhN3tIn1+dB6lT*@)T=iel5}O#|&Gb"
    "UFHkiyb$cq9(&yX0esKr>k}n3SisV&wEEd9h@btzeExbb~^F5%s1MR2c9y(9p3r1rFi5#y}8ZPlcS^W_xAr9UEtu"
    "9&1b*`Ldb3LjXG5-y(=&LH!-Hq(**`KS^1OC=h-CpB+wyN#sNM2U0uzu>jZm>$>%UcE^J6)>L^WS1+clF-lA@EeC"
    "~1Qn&eQJAQPH`b@C?Mg0NX+!FDGQ$92xTg@QFmhbv8tBF`AAv5WxI;R{ky578;c0vN#94d!r2(O$``Oh7f9VN&or"
    "i>7Cl)>tNp2?UEWattS91J6VgUAUTyq4SxjhH{D+b8|iNMRa7dtX6BGQc0{pIL&`2_(cR2sxrx@XVnyB$Bgy~EcL"
    "1Ew87~0No@3v!uo>uw{1Ma4}=$d586u;KX~fmej@(}ct@OXd`6z(4B*LJqrRe_ur5rpzrxU|l-^+Lv_pl1za08)!"
    "KV)AanWB01>=-~n&jgZS1Q?C++8OB6>9T%9NX5EHZ_MsNo$ML8oGy`JV1+oK{G^)I@5866hF?&VFYVy_Aq{}lCvX"
    "!hK`OvxRg<gSV*CHXt`ds{2lEuU}u)x4`Rc^d=kIW52mf-E-TPlKR&I(Ead69p`YXPxTJM&vYszttP%k%410h}=d"
    "okfl?Uk2(7M1EJN-{LSJX_>tROixhqaD;J8_hrzr@v?mYGabUo}*A+-))Q2ZXtrzr|n#Z^bPZ8z0nG<Dyl6XQm&n"
    "0a4=8&<&<aems2WQ|5&6kAI6<G04jQeGBZQ3D-vS1qB&t`f0>f(r3-hYFE=WLKsV&P!+aDDjI<|8;`5x+Ir;_sc<"
    "cV6VkDm@)yFE%vl*VzEv`6M0p)a%>aZ96uh^vtz|)W=eC2btJp1CCzZo{tMmh5rcMei6zVsm*j=MXA@D|2*8A^-*"
    "2eg;VOxTQsgRLQh&I(0>m{R;<7EHj`1R2t@OyMszdDg1pHbKr2j>WQA(icvNoR!L6pONsS8GC_E^Zf<lx{<lOW4$"
    "=iLTjU7&bCpDNJZyYfdv&5NwC4e(B6D??#eXH36-3OjZoEPmsQS=Nm?Zwgktu>z*rIG-9M+H(b3Jpm+Cv^={@Z?1"
    "4f#C;)<}-N@x|e@9QZ7dy^UV-Trb>g4R;JTWQ#pwhsu$|gPiX1q0n?d`k~_RhVhQvMOvWB4n7op`IcrtN<s$2Bo^"
    "zX8wHww3GV%baoxRqWH=?=V2}5GWF}8sihokJz}~j*pfcTXDPe@%e4=;h9<Abe|P89uCfX{8_D$zNw`iDz&h%jF6"
    "1OKR);c4i($H<jmWX-mufS<!jzt$KTmVaaH!ov^8xcE>XUJ6N&CA*iM1y$nhi4r?pXg42k*>-lA=cDylHXum#d2C"
    "=5j+r2>@<3tw^7&6>ByIXUQfA{z9+45$nv*Tb%D^@!uzA2($*W?Ynpq1?Rk)Y57@JWQyv-_*VB$e@t|^vezj)F5F"
    "vV7<=$J)34Dqli#T$KM*>=WuJ(_w`x|U&39N)I2g{@A789(<$Q{s|UvV=qo|0rP|X5soV9~qpLq3CqL}h$fq&t2)"
    "evemE#u`;T2;H5peRw>IH@LSD;1g^phQ_uY8Bd+!V2hFchShEV$lsMlKK_BSBEbE12~~hOQK0e@tjFg+C03(={T+"
    "42Kf4pOD2+gBoqz*(ramWsD5%KB_8<;vaBCJ^uFPw{B?Ro(BP9U<?_nTtSNvol2cL6_>!NDyM(7@V3Ttx90SQC+y"
    "psyYQ0a1BRCu5^9Z86yAI8{Egb%by0G&3GZ>57emQ0a-ucYPQqIz2iboDx(heqzrl6sGu)HEg8Odg;UV{DNO#hGc"
    "uN0to<O+fR=a2B8$`jqcJ(2-hmJiYhdO`v(wB!`att4Y3+{K>0o+K^lo#%iw43F8h3MFrz|568C}OG$r!dB$r10G"
    "*60uxG-YBoAS4CgY-*S6(M>X2y=HBAYd@C4B&sHGgXI~kgZuIedQt6Y6j5S+0!Vec1mKS{iBLQdTodX>IDJ!uiVp"
    "=L4)7-QsSAElm4i)1H<)m*<B6@Y2^<t`FwX>4zze$bgeJlnI3{c9GacIm{X6wRvM;5BFEQ_gSqN||RyT~o43m{$w"
    "JULkE_yZ|TG?D>>k;zB~MnKqfqJd1NiKU%fZI*ZbfrrV9#GCgi59us<Opu8X>scw;<JKHQoN3s##F@wK*U(Z8(>P"
    "C8EhEg@nhy65n74)js`V5fl9G#rp5_1{vf0%3we5u-x>E#==z3jxA<FVH(I{;F<z0)<=YxBBsgH4RElh!Ya6<eUO"
    "~@lv8`$p<f||}Hj_C2Vw1e&>8yC@=latd|2d4-a=Zv!+awJ1`CdMV%P~HB=z=kDJvzMXP3q;Ph`6TJzBx>i|_-Fk"
    "A-2*i{w%mw((Ag!*?RrxRxKIk?7VL9DBSHLv6J2F!qnYC~KAFe!UuA6QKt#zgTQ;hW6jA3AA+}Jcz=nJ(=f6p-n^"
    "}GplLQE`Bks~(dNtN|kkN7J40;M<ZJ`0Z`<5c$e=8oZ6;v-4`(*AJnBKg5ciBmT{H;s7v3Tx=LIW+s@(Ti+=lHgj"
    "222V;%hdF$oAk@CziB<fqtFOct|+{nGX#3jRp>r&r`}EWkvq`x_Btu_w7RVbAh|k~te`S#m`O*WtOV38CK)jlpp9"
    "~sW6D6qi4ML~<YFO0jpxw}ciNERg3xu^9)r;6uO1_TdPyAEj;3!wLoM^LiX20;1JebEJ@~S1;veq4nHl&eEBllcg"
    ">JwuP1->I^}I+jbp!L4`$g&f5QjCu|2Q{!H3tDz-78P(3x9=yXv=ufeuiR&Sr3Klsv5cjj!AA`$_bU)vciolMy<F"
    "WkNF-=(v&HDWx#@LSr1TMF;b8czp9&THY1w;yi7)Z6qWh2x`BSq>`&7*d+Dy)PEUObTjGPHJ}T$A--d-zrQ{C(bD"
    "H6$4t$V|2c6_hJuD~FUyAa5LxWiM1(w`)7|!=Yz4+KWJy#<?H0ynu{bLQ3+;J|Q!5PM3R_nzOPc<$4Pd|99Ly(Ha"
    "8qPXX*a&zY`)0Sd%Usp0VQ*h@%_eX8f}5$Bme(JW0Wl%^L=P{t9WDg7nE_pYc(;4W2IJ-3>IQ?F`|hrl`$#E0o8l"
    "-8Xn`NOCqI1ww-+DsvRJ%>-<Kq~;SUttn3J=2{v+E;emr?|z<(X>9seMI?GN{kFaZhsCNJ6c9?Zvjtn~4S;I|CO4"
    "|dQ9aXV2k*@4=G!wQv_+sT01g+GE@@TCF#fA|6ln!)RIR%PLxbV<7yR&cpqak^U&y9g)P=yhKAf&3fXWyTSHQH6m"
    "dEZAY6b0Y^*-xo^;1z8Ld<s=3d|6_U{AHd=XwNv*d=zQ+g>}hajAD}trX3f#H{6d2X#zJn?8<NvLssJrrk5IvM4F"
    "Cf)p8*AERkmtQ2S*o(x+t|()3a`w-X^o+x~g|T?G@0lEQ9xmWb@EedNY4=Mi$o3G0&z9HG!ew{86@QeAaQI=!5Og"
    "Fq7+r<#k=+br>{FwHJX~=qz$sJLLr%r_jnkh78#-m&zNda-HL39KznqX2mjdOGfvF^&434e#q{%WDfjEIK`~MY2_"
    "W-n&wiVu!=;d3VMS6$5gY()~hm|SxiBP$}km(E$HkA-#<F^3=ldB<e2VJQdJ!E0eUmvbLu~Tc<D`?_y+N{`_THGQ"
    ")_g;S95k<>>#d^eE@&e9&u9p^f`0MdHBKWkO^lP7E?mP#+PAT<jjtWehdEunjm$>Q%5g$%rZsCR2IdG+5=KHPqu3"
    "vS2Sdv&Q}F(9g0RR1Yi&sp6o}Q50F>Oq9QknY1OA@e~e5u(H>5K$5LXkc9Wm2_pu}`#eXV!VQ%#5lOv0w+JEF#dy"
    "Hs$+wld5FWXz~#({I+IH?qC7RF|PL(%b;qm9YxW4DI<Kr1#STF_c@{rXAN7yUhlCZpP)FRnYXqRzaLd7oTa>}>O~"
    "XZicR20!#qRi+q7n#2#f=oQ99XH=v>5;S^=&=q-HZEmVlrgoN&-;)7h(d0+f*?sVi9?pqanMLgsY}uso(+$O2Mzh"
    "?KAAMDW<7e?!;AZ5nhN*Vcz*ZZWnXuc_@FoMe!nt73!W~9>U*B)UG5h=;SBc<d7RIB-!=^>oA-6*Ao;*5yJ5}VH*"
    "ffW2{~f_3FrSoN%ag=YQh$L{mO0JX{RZL}!qF9o6XtWhns&c6URFK@llR6mn7FSu8AHe_+}uNH3KJcjexdt?n|Po"
    "(-_SQ}jx}8gmxi~AS)oRm9T&`=-%G9uhjK63S_gf5a*YM7)=fYHqM=e>=)|WFc;?jWe`ruC$E!~<sAxpbAR?Ys$&"
    "h>cGxEex@#)HJI&jA7J+sCs8{E5m+)moSsTBbXE3}BPx-yBIODtF%PzNuzCo&D(rYeE@N8}k<*@67)eqQTLkh$pH"
    "rEjZgU;<|QN2%2kDk`P#vms6NZ>Lm7mrRN9lW3LgvBtjP$XRJmkN>8BLza=)49}UPXHkNmuiY5~fz?wK1S5D-@YT"
    "aFZF%T{lOoq;=d2;gZNehOaLh;vpGCxa?QC(ebD*%)d{}Z+aINGkz5FMu<J`LV4XK3qdeNls8B&O;&U^GFDv?FKr"
    "xPdlla5Eh3_G|Ln@&jPsbT2hcL?5$cHo((T0XC6D-T_!gqDa{Py_QWK6YhN6a*y6eYTf=fPG03P}?q}IkK)7=H=L"
    "$y@q><Ez~m4xn`6-L{_o4;z!ZQgNK-EJDYI@prb?LX{gUp7!4Mn-7x=_W7;9amcTi`HJ?yZwntVNukElUISdG2fi"
    "twbEZmwsC_9r}vnU1&U_LRhAM>9O8x;Q&y7nlxXkc{BQ2paLY(y=cXM+eQb3r#6UanwYTooS!na1WuRA4>=gQ2bC"
    "vyq0@f~N+X--`4&Hj4U6w>=#Lmdc1g565-jTX7AUOrr0kw>90-HAboK_(gI`vF+1hO$DekgbYnu`!5k_Voh;YSVj"
    "X?Q7LKVhG)YYC+9yNoN8Ol`sit5R<?{)Hbp}YM_j?FY1FfO4QOQq>{8qC<G+`8{eBPw-cLsENJhz8>>$92#qDDH!"
    "#27r#FrdB4hlBXEPujT&_>|Y4r2YP^2-D&oGfOB(jAQB!R4#&=Cge9o(m`CQgcPyqN!<Rz3ZMo2$Z&e0^OLAb)cV"
    "r9<`mK5R~kXm2JI=t|U1DtK7mNkPK#2fQ5WNT+jtNLa7rl>nkqw0y8x0nZ?iM1*YP1O>%`Im;%M!NOeP#a*FXwCR"
    "dkBPH3)x%@H7ELID`Ch3p+46;_frz%w8hTd<*TOuok#p81QDO(yG7<5sy6qj<w$#n)6PDxe0e48v_nDg~^;biEi0"
    "y<!_zMe!cd{0Nz$SgvObZ?xhr-!d>*q0Pv=Py{4RjIJzAEK3>Q8aId`PBgbDOjZajm9|CD4cW&f3Z^!~Ba+9gSI$"
    "?kxIoDZTrnyGCR79@2FeEz8KEWN+F7y`3y@Ix;*O!2a@2DyacThYw7~pj%8Aj&?LHabpy?4Glac}09awIvgTo}k="
    "pQ)$LZra0Ks7KWa?AqKs%QcTzYR}w=`9#>u$cwYgf(QX`Nb{iqT#F{>5L3F8)+pkr6jS13XNz3W|&=q_ExL1y<Fo"
    "$8me)%Haj+;E(DmuULuKL%|R+jP1aaqcMh#l!Z^zP%F?5uVvb-1Dv(dgG|Yf7x#k*|Cne<OY*K|IBk($}EM^J&ld"
    "yO=2Wd=BiDy;MC|}U~US17l@V?_8ZZYMl^q|xZysTjY)M2u2ax=(D+a7qBh>`q5=7^Dlmu&+KLHvYch>Hb=tYc9`"
    "BPQIY@FcdPi12Ctv7QnX6$u^>b{ji6eRX(@AmFbLv2MaDvY=cwMt2<5j=d^@WNzGc(kmbp2LTCoAJ2+uz;4Jar-h"
    "LUtHsRg5Rivfq<|6n9H0eVYL9pkRqV192$I2pE{}`V-Yfkixq?RMnI!XL0qu^l)>VmHMbK{;$>28iK-F{yxna$;P"
    "%WEx#xA2ujx=5;f^~qUM|MS4Okx<LFoSz!3#i*>#_1aC2NF75S*$SHa-=YG?8X`Cp}He^Z;XKBjl`bIUhlzLze+I"
    "RuUgISsMs%TX=I={jgw>~=L^}-2#xCj;emRUPxEnyL32U;T`$CLujog#=~6_g1&%wG5qM~II^vFOcAQPnK+%E!tg"
    "@xZmYAAX5}+I`8wI<2AbRt3hCytoSim}DZjD`c|D%>*yJJ4?w!~rnR|IK<l^e%n+GxGxlqQ9%Cz+hh>Xra6F!r1("
    "I(zd&)qZ8wgwd0lr^{`o7rHi?5r5xAHbg39&$esG-@xgv%tDeJ1flM>#X^Q?<5^|SSr{S#+dKnaPA<P1Ijsu65wz"
    "Fi{ECKv>(JZoP&#!^rQ+tGeS43758TiHQa)(m<v72H9Yq5!Wh@P(0ywOug+dJrXs_B*#xJiTDJrVlA&s#>7nM)dA"
    "6(=roq`m>0t1{&O!b87ZQ&;woNG}my0$9|pzgL+jx6uO(x#DiLgj}iIm*|ZWRx`0(s%~SR>#|?V%xBCl=6<aq^Yx"
    "o>TMD8lkYvjR>O)k7qzA`Oe;<bp=l7kxy+P5;{-Y0)=lODnB$?DV+rvfOMld65Xx;gSED9q%t>)GUNQxMsI4E*Dl"
    "f?WI>ES%)yGv}+~>n;kMBp`g8jGgEx2#O4JnA(hBI1LI7p~d5{@HD#eLN4XJN#oTVDkTz%hh4XL5dQ%~pS#Mu2dM"
    "=stg_!-IRnbWy_HDW?&57O}L%qA`@ufRFnLcKmoVvZ&;UNQh?Lso3aQ)BoMaFZ*!;oDUI1Vb&iv;n@1d<{VXV3+o"
    "En*UY7jFX|fG_w-7`YYz?AH#!X?cw+4kr`VF9{Tt{a7)%W?$nSInAV_avQa3$Id1Kk6u`S2KA4MH@iQb_pJ_0%S{"
    "$;RDgW=$D_F^bU?nVon^`EERrV)1hC|wG9hEP2c_blKV;<N4j9S-8$MAc4ypXhZnR~3VcaN?xe)F{G0e5_4j5$?1"
    "7i2uXqGVIMqQ=_`6f`V{fj$NdMz)jWo9PpD>F)n7noiQyAR@N>JF0Zrw7ljQ%>nUj1P>GFM5z=qV&>zqWE^duZ92"
    ")ZNmMC(V8?ygvOc3vbWS5$7`>HC3OgtVWQCNCBvyLPs9*;pJ&Vw*9VOG_RZkx7X+Y#S#yIvcC7Eab)Qf+IPU-Fo{"
    "z>%F2u6AP3XolQ=HqoMgvB;2s25hfj@?EHp@L&~-18nS$potFE=@x&*cEQH{xq3!z(Seoh_M1Jk^l8v%{+X4<5Tk"
    "0`57$5HD%SWk5I0#1WF78n-+wSMFw{S@Cm!pPd2m=^(CB<~x7=RM(ds#I&uFW1J;q?%iSQJ^OONhEIx0Fl5qBK!#"
    ">a+WbQ%eIq<np+9a5K+3yL>vXoc#Q<DKMe1j2En#e_4Pr|X&h7Bljv4?5s9f%X$$HW`Mz`pKi<*DajA-+K<}+sv~"
    "zcCWt2w(8wRANBv#;1TEV<`|N75SmdBBZ-BL&>!`X5&maWxJY<mL)b|0`?n1r>Bw?7Ck9y@CYu)YR&#;KhPt}zXp"
    "A5NK4|Wtx=^|bhNUfGzzQL8eMO5x&U1=gr67AmJIJs)8-lSupO7PLym~HxXySC3C{hGzD|48!tKy?67z?dV*5k~;"
    "P+{}8`C@@k=ZBbgT@@V<*t^5FK5C5nv0hNu7Jb^gXiH6=i+AZc70c9mFVE2=CB4JMU<A8bV2yfoMv~Vwy-x9@-+="
    "@AI7J6O-ytUn-$Kj5JWI*=iM&d%yg8={*h5C8FA}NoE>nlFVT*!c2R`H#T4f5dDxpQ-V$m8QF8GUb4JW|s>cyA4U"
    "w+fw{k9ALg;92;^)9^I<;^vpjDVaPUz!kzZ940&;p<;@bt&PkHmxUNrGvV(o@MO9O;;x1-;97~e^K3HUJ`j46Y~F"
    "KA{Y?O>^8ka*qDn2RqZRYE)2Jepl&)(0wp3QZ}$1-)i__$fq7JBv-GY<A*`*oV*_3jQL^)cY+I8qLY{Xe)HbCg$B"
    "V_wUh@3;FXWoluFumuT5Vb1|47Olt&xl3_Ak$$CnH65V<tw_KT2NEK7-C6YxM6}&@}ftOyHOH)4E&m(`=sPZaP-W"
    "zo7+OWg&&ALvQ%28*t{}>o5WN^e%D}y6^|?f?%NtBAm=aN6LiLMlXxXxQYm62TP8b4&b1*zN)f^5&N&%uUW#P7IV"
    "rk*A;nt_^OBh;S!ByhW0aRO{~7f689<Yit4U{4u8ir+-8|sC!#lw>8QjdOz6>>mIufrU&zhfArl^K8Y&8d7C#~=="
    "m%&v3>2qymnP3)Ts%Vi$t*cJlhQK0IE2%WAc)w`Vm-ei#QTc{$9B=uR5`2BbVh+T$;F92$rNY<9U6T<Sy{tCFGsM"
    "Y6(@QW$v5mtXvV0Grbrrimj(?}hza3Z)q#A83EJ$%%3IB_3_R6($1G>6z3@Iu#_U~5xtu(CP0;;Wa+tvW-WgT|Kw"
    "Ll?;q&LOnIjm(^8zPF0%dxzSN14OgdGW#>zT|7;(W47l+T2<+N|qccLLVyad!gM?7@YDz5gD2F5Z21DOIatS)q5s"
    "i3cF-Jid%iF)md?q%M4nT%G9DLkB$!AO-#QHY>SG!X%%P&bI1{GnE>U`2?O`5D=q;T%%o^NmF_cTUC^-0@$kq3D|"
    "4KPwWt=coK*;XVYIS1d5Kie(Hqafc&Hoe#a8+`c6X5%ECgte_W!)2t49Z=<dJ<d&wEFYnBfmUXmF2wrhotN`&sk0"
    "#nwJ;88e;w;&@l&_pvWdTxo;C*=qWKD7D0UZcV12|xshH$(A3S>@ye^QA{}hB<*1)P`01x!`O*S5EQ8VxM5{2Mx>"
    "vpV-?!KRF#99qgSQ4A0Mx;8`=A77!H{G8udgI^w~99PIx@wMF;N&kx?bJ#T#a<=0LILyYgYq8Vs=EC^JlWJZg$t|"
    "gmm&IQvA@c*%u82wOUG)W8c`+3Y={fu-zQ@DX*st<)<hc^m*B3p1(Fr*E1Pw{VKEaT+H8&Iy>#NRkvq?e44NWU6M"
    "jKu;g3^1Ckkpxa?3uxn6x}w@VOWZ2?IEz#r6&-#`NAmIT9>36|&$K9Y;z6qy|C=H177*1xvxVl{aEu(;x{fki4^v"
    "l2mxg%>v20YL!<n)A5!rl6ku<eoJrqXrflta5R0ejHa%FqES7ABW1dp-s#d!g%g1j`L!tOdR)lFLR5_29R%M8Xi!"
    "QXYMkxO`kZb_NOQ<1tDnN?Z7NF9MyMR3aMCSN8*g;GPJ{T<cKd7l+TeN)pb5wN1U&N%{3$(wVw;P`P(PEk6mNOdF"
    "DR3<Db0s;bI$D)NkkA@5BoZu^yQ=GXt1v!cs38=)0|JSg4?>lCXI=8$9Bcu>*MKjr)ycA~w2%0mzL)uO4oh@kcKv"
    "!~)7xGt7CWihIVLDDwnVIi7?34onMyEd=A0Hn7Fk<*EQqlUGA%ab@5lNC*WTuo82AOdLoH1A!EJ35S*Gisn<eU~l"
    "=5VcMeO&|p4gJc=C~VfT3{*kvL+uP9wCQOtCYOOxr=8}wP+~qM4bH?;x;P<~5UUn&W1TmpXiD2Rs$Xn)hI1?$2K?"
    "hHUrgjwqMeiFb8HXppi#xd3a=@vtOBDgc+^VMs6K8uG$}1h8I)8)-bm?^n5G*nOqc35L{M-&Yq<R~V1k0gMAOFmn"
    "j>HpnoG<IX#ALGh^LxY^U4jvk!j1)5Ay7sV78qoK~&B;{XifiGmP7l04wS`R`iTA43AaRGj~2OS7})4U(0#e7$-e"
    "2Wzms2bNkI0e|iAJe@JzKcbWkG7`{s=P^42$c6C%zo7Fa?u1J6)J0=B_cDS!cldGOBv(z4WJ6wb8^hCx1C^DHQ+z"
    "Cf+7?7k5t!y??WsCSITpVm#E-zPHXGnJu4FszY7v)x{axOxkEA?9pf7ApG7=QxG!?-k{<21wi@tzt;2YVn=R<Km+"
    "7S<yyJ>>WrJ+%s<=NP8j$xE)=Z2~&-b_G$7)vo+vE?mfEYdF5=QU%$5S#by*_;yAkG}!HJ4~EaF;UdLZ>dp@tdu="
    "l8AX*WlJwx8PknWzr-Qx-JaCq5&$>RhL2w(u|?E&jKTw*gcpYveQgykliTX3Psy#}nhv$+BLoYR0qXAz5HOQAR&Y"
    "Kt)9&IV2__Y{hEwVL(qc@BNv{@GBomK}CzbAL2#v*GM;o>FB^t{FfT*2TQDFlO_S_IpGI3^qGh#^_rpItK2-vDx-"
    "5gXDNs<%EF=xR;!9d`rdkhT-r<rHMFB@(x=U`-I83f&0%YBV(cCc$8C#PF6AvydINW7ptZkk_=}-uA4a-9_c1q<*"
    "cYw@bgFQDS*zleuOs*lH?pz1UMp+YQ<Co;so_8s~<TMB@`szsTlQKB$f42nCf(XB|QVOPWt3LA{rLN-h@+&E=IM("
    "y$&#9lJY+{G(#A;FR?oo9Y&-;JGOf%P~|rHJ(9Qslc&OJ3+#5Orr~j0EUgjlE9ALBRR_LQ5B7A}4nN}c_b(lXdEo"
    "Cz3w3r+)u^3z{=_06fP;^e_6~*-iA|%iM6Sccx^g%2gze8G4?f<Mkz`MOxdD13pQ=Ux8=SN=3LbiDRrRM-F?C7EO"
    "6K|s_(as%P}bBTB$tR>0&1=-vZ3;6b4=uhWq1NbJw{pElf{!M?P*PKQTlb;h^WT``klajMh&>vxyDHTymHQ$)ru`"
    "&>4F2|=~SzDc#W%iv2(Hz#%_<KEM2TuQ<MHvGBcslvZ1{&aouq}ce@B?l^`G@{9TaIw6UFE(tKqc1EN^#@x73xWz"
    "AqMwXW=knl}gK9E{mQ2gABTH{*h13z`SzA{IF3(VJ`*uX0q!$)gu0eBg+j5bU|2?VUj6wWcEo-*#bu184H*Qwr;6"
    "@Bc<^@!%r{bI^iGWf`1$9)2%*E2;;Zt~?d1Z``M@G2dEg>GW%@xe_`-mKAGE<>Vba4a0p+x>E~Wy12GVDeYmn-<n"
    "#;2g3E_Oky(BQhGSHU0AF`qb>NY6NDGnuorV?X{-KfdN|Q?#kGcO{%%U~P<4>!0v_T`g!!BWXlpQllFU;A%M2}+<"
    "$Ae#0jCn`0rZ&dS=(uGo7AkQXn3DP9s67=R7|a-8#T?Yu3a?<p_;5owif=sN_lxq+JL0lXKSucE+E4^+2eWOOe!k"
    "UQJjxrS`u%?rP;4$=Y8jubG$|;yX1;yjxdUY*I{^pIeJmKzYKS7N_&j<xX2J*BfAaB^qkJJrvCnVL55@QiaO>T+r"
    "$Nce(rp+rdYSw+YM3&10rhAxBq*^4EN*_K@-TB2JsTL{E{%h3@T3y{D2zGdg+m#<VdQ~z|g8|Js|f3yBWAS=63nY"
    "H?vOE2e3$C*cd;&pe(=59v&ykOr$7QG9?oOO;W@wgB9f^84x)3O;N78sH{!Qc4`?XiYX|H$Uc~=I#Pu9PT;djmJW"
    "EX1=MNNwz9Gh9h$B?gdiRh24yHEfwdy&g;5~DM<!xQCecC9;E;HXYC(C@RbP%f9%uV>7(fDs<U2JPctJuT#S>F;="
    "u|tY^7)d=x9Wzf6vF^<d=>m@HcLL_srA)RqC+jh4(1-jTDt6@J9(T@CV*}kXCqMz04o(~wQ@qtyKa!ylCT$9uMoD"
    "{Y^9pz?=!6xOIo@DbTLtLXk?$!LO3_pG2W9&cA9*D0$gWQkDf!`7rN8gw`LRx*`=aQSWmNObkaqo$ScdWD1t~8C!"
    "KE*6#PU>l&3O-V+iHJf^<(_9lm}ILiPCE*|H$}y7l>HGDOW8%L$Yu0ZxepkztPJ%iz7RdrpebN)ILx4du5|IbIzc"
    "9e~QQjnTbXg{UhaTPhX5MpqE79?=zE)-BAj4fH?E)Qsi&COJlvJmRVsVxkC~K7q>!Sb{eYkvO76lW1|BycKUNWTs"
    "@}7RxU(YtG<s-Pn=1;B-chvM82VB8pf<t1@sq^xzSDkep2ET*Po4wOKpn>VyAydw6>AidX=0PIFX{R1}KtqcA4gl"
    "MP%#P7Z8tFyhzF8q1j$qjhO@Y_i4^ypIzAZXy6oWT9CdoAYce`rNLlQk?2uR-($lFfkf!mM&pKDs~l}$&edFf(Y<"
    "9IqI;F!31USSPQZ*;LM-=a%_Sft;}(vMv`+6b4S86Zf}findx*{u1dWIt!HYcKCc|Ct_Yv+;6t=0L9p7Wq>d1*=I"
    "C<JQTscVGq*XP_(TUW@kegBu{}|inBuR{7Ns0&v2=#R%w6-6QK*RSl`!?-Ys0I_U_}5Cl%~u&yV(!t40lioutbM&"
    "6^nerCtp;muCmoFDfgtNq!V*mr|Ebh`-xj)Br-bDv!wM43()2)I5yWbIu~>r`dIFq#8Ux{>+=+m%Y~GUmifAFH)m"
    "Q2mB)yv^`bJ9ppa2XQwoD?^C}Tgk%1!|AQHn7NpqjNULi6{ObG9ULIh=m-^K99lvDE3Gt>}8%)tDB{zJ2jO9E%9C"
    "GY}ao}>)m+DLWy`Mg+k$7Y#D4Pvc`c+dj2={S?n8baTS1`CvoQLyFdB{vTDT2i@&yVa%cpe~SV?(HUtXG%6*Z9c8"
    "**8`J1NVx(0zj&qw^xr1w9P{u#_Ssnbk>G^di6jhBs0H+JrLQ33?pH-CWNA+V7HYjg@1&;~UF`g?lfz@DTgV|!;6"
    "ih3JSP07Js?lN9Z}7CCKkep9Pu*`jnDnphel|hhA2gc@GkoJWm&#}6BD+kkcA@7=J|EW`|RacNjjNi2D53lo@4we"
    ";eh}J!09DlQWc9Y2y~A*9k$33aENxs=Rn1_W5y$?Z<T^l9{+T7q*?~HrHNaOA#WOx1cy2VR8yW!sDIaZT)UwJH*A"
    "ZpV_2S`feFh~R@Y0qFC9mA_77l}j2^YdY%R75U^{M5kg%k^pU#0Y_D>JqphS{rD$da)DZWZx5;q`yiKC~#fG%PzQ"
    "DtMF&<;fDblFUY#ZXTepMc##z7b^ln1QLj;p^-mb{r5hJspnAlr%xIsa>aIQG|dM4v$ZUuFCuU;qj}(;~#)ZyN*s"
    "CrKG-QJM>P0tYRCrZ?JWS&KzPgzY~@diLkra@#~O=?fMzM@iLo!cCUQUFD`!B`9C*es9|OXt+3kAsufIcTW}7&DR"
    "-q5<-a$qyCW3-4+~(DOlB#$DrMj=n*)^UvZnd$ST9)lX@|<qA)}9-Jfn#%Tb(~QhNOR=lW!#!280Q@3mZ#~`lp<P"
    "M&6u^I(kMR9)9J<ru)Ioin-|@(zc491`<6z`1haqU<l_)Nha*upk~aCl!<;cwmD*sO<EuFbi)DoMI<G*!`~+Nwtt"
    "8h1{ECTLu_E$YXoY@c(65_tzx%y`4CynV3$$?^}i;Vxq3CrD|`<RpceUcxGX@ris8)|*A%*wPk(I_@6V~a>I_I1k"
    "z5oyRnPbsX^skrp{(|($^?C*6~G35_v7ukCm4zDCQB!43C>e=mNRKpC&vfw(R+t255|MKO%wL@j*X$m*aVxf&PGi"
    "fTjXr4$LyMEzhhIYd(gA<8<Q8~J69>Mu}g^&xlOM3e5vj(s75FZWzHA2NY>fjn}dzP)hya&a#!WLV#w-ZE<0plpq"
    "J^mND0mo>aWwHcJB1LVDu3(Nn8IFrMmMWl(>g;lx<l(sU!>s)-!JImbg9)TZ<4$HlKNxnG-F$ig~)kOiUr*ycz1`"
    ")Jr5%WbEcouwJy3RLRP5v~dap*F2y#6=I>|EW4{KyKUSPBDtYarIe-WVE%u3Czz*W@=nmUKpXIi@S)sH0I|z+oQm"
    "(@q0TP_<CzuXj%!0Q87g>M?}TCY!nHQV+H)pF@u8MSLpZpaKqRPQmQi;$+a^2g8>LCpX#2K}TGiwtSRFD0247}X+"
    "#Hp49a^LM@kwS;o;W<CgTbh+40C}x!i+;&r{u$tWc~F*V8PK&<{9?2E#F&2(n0M_LNyYi>$+JrN7yE_;4EY}l#3C"
    "J5-n!4{5qFx{VRsJ%(>_$u}22l6d`J>7>-v4Vqm>0KnKEYGrRlzA*(EJ`JlXogF#NpfepclXxK8|zsYmpc?N37T-"
    "#x5mI=CO$5V408<myn0IXW((U``KHksx_NUc4$El*EP{v5_sG=)hpCv*n)^cV>*7Q#d>__EBmiW8|sQP#|y2<N<S"
    "oQ;R3ScScq{6~d@xWZKym%_}h;$amm64bC;8IkOJ+Wo9KN{)^-=JI9XB@u~DvLuk!@%B`Pd(_XlR#tekZ9J6K@dh"
    "Ij+!5ZLWLW^GxgxI%aHk5PFo|{lH^z>*Dt-Xs``O}0tR-)I2DQly2U@DyEYM_`r9Fp#!A<8^-4)9G&9nL)9lSnI$"
    "Qt;#*-)ZekHr!=*x1nxmcb3y!DiOkXeHc|z3f@RcJF=LV>jg5dlE}PLtBj{OiewHjX=;1lr2Vp=)?P@9fp#6@;JT"
    "PAq#ZfCW^JoO4MX5Tb^`qZ5Y7WhQyf%wRamF3FiI=8AGs~+Vp2$a&y#9jjy$?pf@an3Gj|f2%?0Q9^Wv=)^>yfzT"
    "+H|9K&>;5pS(ksZp<+xlUQuKvyP8j~%k{cB#Y=oNyTjNR-|yQ0+2?G`}-B`}yag(P*5xlRG}m;f#G_9hQ$0Z;iXe"
    "1I63hBr}<|VhK%_wPK{LA}qpHQ?hicw5P{8y_>I6XS^+B?LLFt=%%VO=|IPARDU{2V{QvCaXZp@Q>M#?l$Xc`b;M"
    "ZYW&>*F7Wpy1BGamQnts!)EZ|i8=Z8NZ)CoEsmi&b9ZAaE)^!6tA-d{vyHwtV=?eLZ-(o5UwCKqYgju%1eo80P7K"
    ")G)X<V~0zkNRRe4k=paY%NxnV6*e-G#S~)M;2|P2J#UwJ|`$6H+G#VAs~&7Opn5pV2Px_d|`~V2;T@tY(8LjY#cN"
    "K3(%or|K!bE46A$f;`^hM{lCJ$Tt0^&A^qftbfR^OX6l{eke9vyohgW%dyt8+c<a8_nu3e4h^j~cDhVWEh*AL-pT"
    "|fe;>;-Kv<k%dX2GLORymz%mKZ@gvYU*8Pz4x>6tX$h-l<p!i;sdO>vPYn)!GE!NQI%=RIr@|n%Jc6>0^?ObMnOM"
    "NP>hYEBhD4RRJ0YMvTz-8I!e!G4(XRfAf~EY5R@)duvy{MsxTU3PzYA1+lR=XiY$?gxNav;P)oamSg%cp4okKZL1"
    "yK@xe)GgFD9vp8kD|uXVO1j%uEk?_FE#Gg>=A?par%HPkV0lA+rN4e__QMFbg>1AmcgWHQ#XLLDtqe+$j`F<@?i6"
    "7l^ehDIrwoDF~a<d_TG=9MkwY3G@>!c+slR8{8Dsco-VW`1y?Ggz#BNE1X1a&)ot>f{*2+sH;8Do5EcCa%JYZ=W9"
    "QpZpB8`wE(Hx3jYgZ_;woeNV7Q3WFGlhuXZOL}*41!YDgU9RXiZQYf-Vg7xhsFxAPUBDDRKem+IGQ#eX2bjKOQM&"
    ")1=zi`GCLDrBX$}pnl`jR>B3#Pp~gH!pt&>MW|XEYLZvm#}bhg-r8jp9l82^5GH3iLRm)4%NLJ&$=;H^ps*xiS>g"
    "Bd!5Fl#QD4MBNM-Q>T?>XbS`Or8{k8p5L)6#qLw&M$9tk)y$DTULiF?U0p8WX$rtG9su&^%n9SxGz!~yzARSkJyD"
    "j9$tBy_=1ZJ{{~<AHaL4S}XG|8)7`(wVnbq(cTA^YeNJHS8fi!#<k4NKjyktS8iMy<C2@k2@X`8`@=Et^yYuO|{3"
    "GL0I8v*TWr4oZs>m(A9!*jeM*Phu52a31oMAD~;#4*@7S;;73Y+l8BW3w_PAgSM#JYU(zRYSl&%BD^-OaGapPOC^"
    "Ml;~r@c^MqnSE&iDhK+Gf4PZ_RbKu%Re`IXql<d>18wAO{)2RQHu<D8{24DGYHbyhFRGl;<6xl?O(vq#I7LZ`*I%"
    "}vl7KNUAQb5_S3M~6I0cM{uvg@-&czqVAs)!k&T~8^kHk6Y<@NTb|#2y_SlmB&ga{S`_<jv8GH=yiJP#Y86N={yf"
    "W8__e_oX0C+51EcX)3y<KZ?ryiM$hgC(U8@-z>k<w%%efM831Sqx~#5_7-<ebR3OkNF8rs3w?T#pqSG>BZtSe{$E"
    "H9#}vmjSugT`tdWgf&B%8s9qT01>TWUaAm4(s_^7CQz(Fx7bu{X^oPkQnaGk~8<Mrq@=@V<Hk{Y#|FNahjc3?gY%"
    "^;NWvb8L;Y5s9Az1Zp9(`WEOa$W*!o8m3F0}bE>`0&8#iURb_m(VcIN=rYacRchRIuF1QrxVohTTcHjc5bgOcE}y"
    "iR|AtgU*r;QEu8pv^!{|Vu5MbvJ^Ua}a!Vh=O0`AHE#_sX9S6{%*_PXMCY!mVfG4!-wU+9!^R86Gm0PH~m`gKK>("
    "H$g3B-08(oc=%I&O_dEtp6Mp^Mev%T8FGP$K~cXmaXNA+wAI?01jKoVne@3)W7xxkLDDtZD2cFwps|^&y?Dvpx<`"
    "yGlWwKq|XY6!8N*J(9@J=Tx<eSc4RW9lysiFv312>ykn)NBJUO1v>?^{3^u^=00?2y4}J{RC2S=`VMsC(h+R5#00"
    "e}_gCxXEVFABKAV<hdN*u(gEcCAEqsr+9o2Bc2>`*(bL50UgNTJS#T>G1j)Im3)5BkWxzPHsa{@^ZN9_+!C3MStB"
    "dl*nb*yTw;*g|*IrfW76MN6R+r4c5xI16lbfL;3jnMk(+Zf@&v-xlj4LxAxRieNlk}dV9{ouJ-YBMX#7sSlCAE6q"
    "M8}2)uct^ds-2A-VCOoUW`0b`nQf`<>YC-8eis$0N(DRQ?T4X#M$0UQgeEhA)M<#lOSA~<x{kVm4sZAtnzTgy*>>"
    "&*MvV|2pr3pWW$1Xi>81Ffgo)J7mY%1VNQBH!!`*uGv7L0A=`g!!E*36qyz2Qx~sfB^=$rM;ROj5mNETPEb*w6;;"
    "$yl%6A#1_$qm1R54!4F!JI;(Hm!_UwHBOfVRbo411SU=`{Et3xq5s>l_n%$tJnJOS`0_Jfvz)@sdubhZ=(A=WlS2"
    "ThaD=O9p1|o94}_iM?Bo~tuavoBbatb3!lB^rT1VtpX_(DgWJ84yu4|($J3_SMXb2rg95=K>RZC4nGU`rpO2dW0B"
    "iK7yHcqC$6y<vlWDM)$75qX={_WcqDm=TflnNSQrNrtfr0Dt<fm3Q-gK=ewlV1+ce?0l=+!W_=pj&>X7;ls0mWh`"
    "K&NtbZjRq*)5l<wWV}1MNmm3OB#?L6;yfiCkYPOhVCQ-Iy5cb_gU*3(VxZ0{v>$Ip6<WfO%*upuZYc2K)Epr(BfZ"
    "#u9WH2@1D^wv@gk`Zz$?QkL>hN7fqc>LMCFT5*<A!Q5CVPoQx{J#zo1g^+19~uZZ4IZ^8JX@8(7keU;3bp9m`KQt"
    "7O^2v&-=B7L!s!J3xpJ;UU9#<2Dm=Rg>&(V7XAr`0)Dl<r5@@=VX4~4*B)%y0J1PRBJg78i{xH=0O$Ex_TZV+aM&"
    "I1`7Qz8kIYN?<Y82QhN>gDkI{wLlLUL^K1mmbYMcmO3Hk%w{~~#nRYW56iA_)I7bg6|kV`mhZhUWypp~id^;Vlc@"
    "cbPO>7Jg1i6qX??pUC1{d{Vg9CDMFkMsdqZ_{Tlowe;T=s}BnF}knN_yjYUwCGP>f_6XQUt>5UY9A{$G$FIPM2G1"
    "+Y+!+Y`<=_S`-Qr4L)+mUI(qhAy*cR3C*&@y>mF4|mBDx2s;$)I6hoJ8s~0*9*-6-V<6go?f4hC8LKVAbMS$=@BL"
    "gs?RnL1*mj?|-4nbA`HqFRb!g+f@{3W4faZ%&%Z16t1>`}~q$h_0rBu6+4E`>{>w^&-;3V)!77nXTd^waKiyKrcN"
    "U<(ZyD5Fx42iuOEr@Ygy?a>RT*>-(`S@-bfmoN22PKOid*a+N+-ljo|ZbQFNGw0t9>FM{HNi0%amTUmO^7Hdaxc%"
    "+k@;AV{Xf)*)GC_&cXhQ&C^fEN@{Q192+0p*<=cXMkMf&vCUSZAJptXrydwOeoLhpCj+(_HgU2xYVO}1)Ua{5<=-"
    "!@+cU4Q#FFYBqy?PiVq2DGNtRhF(ih5Sdo+P5iT6au>-)F4VT^9%JR73fg-r<8OARzv#YUShtWsID%uJtd3wRrhp"
    "J_$8A~s{-N2FBa+?<>ZHs4NWlR{iu!+cGt!)9iN=@rv*i6aYx;|z(T^Ho>c@Fuu_%r?Rv%-L3p(&?F~0u4D~k{*K"
    "Bojmt3sB+(pa?tRv(g%Gp|BC@m|C3B*--ZwqJobn;NkRk%P*)1*pT7+zDYs19y7F$*K<pIrSZFDXWX#U}f=R-DC$"
    "W9Mg*5mj5SMxZE9t_4|^!9MY)DSu?Lv~Z5TlgMXUc5;iEg(1*62`iQqM>st@>zEsODPT79w8DhKbb>K(6fQi^q%<"
    "h?Is@J#u)<W-lr(Ry278l!$f<f=*SPU;RA#LhvK0M!7*hw$QB2pGj_ro_@JPQPCkh6LO&KG)wyL)&)dxE~KRY;jO"
    "~(u>fkRV~v_@f!^AbPLDdLp5{KvN7QJFMh6X1pi2$ZlahA2`AV{E8-N)^OUbP_E$C^Us`MqEsoU&aGkuPA)zmN0^"
    "`xb1tixu*hO<&NbU&A!%NqU}SK#qqrJ7nlt^gIy!~k<IwThe3OrFA3BYYe7@dHiRQ8rU}=#f=R@Rt7F;bbb^v9kY"
    "||Ox{#GeUn~J&kvceWtA}d_qstNujgfB^7T@&cJDR_}@6Qg7_YbHak=L2xsX}tWH*ijrRH1V`ovhx_#Zu$&CmEXH"
    "Z*dRsewVbQ@fvfhraVlS!}K@<8WsxAW>S(_P`tRlD}|)aiIhH}p6ahHhT3Sv*i@!8`hw5!#Ae}KBQ%{p=!RVTxH9"
    "XH1;i_i{v^m84*tTrzD%`TyBoh%A}uc^Q5&Y})xqn%pN`IlXXkrI2gAMB=Le_5vxEJU<5y>(NB(hlcdIgmhDDxnL"
    "|+I@h=r#t8^Z@}6+q^-i7sxw;<JCbaxG4TUcgU~mnBKQzzFRl3eZme3!V5l0Qvj)WcdBT-uaoT#`yUmepN#c1=K0"
    "L>y}UR9;u3TInL^@!lDgjuKR3<^k2i}84{kXeT<NQMP<*}M%zOBL|{VIR2u{l)43T8yupRZH)^@mC;GTGttvpVRt"
    "yE_=B=YlabtBP)SEu+PE9Sil%8;AAf6vf90l#4VSDlHB2p-7Ik=#&5ed;a?t`X4`D2#BH+Zcmn+Tu9&p*_&F;EW="
    "2hi{BP9F%Nz<s*?$a)A7#usBM_u*)cBYVJXc-g4h-8zjtRBg8d(o}s)h~!PnSc?PAf*YFU^5B+R*Rx2h4#*13EgY"
    ";d49=|(AOeV^l7N@5Zi4BuCRA)}Xeh7++^z4ivyQj3a5l%Y9KG4GO36zp)?U+!rI@CvEtp%d#XZEShOtO$57j74B"
    "U&46mGu%gKUt{-TvW>jN>l(`!qY5BL{<j{#E~^~wk^)r)LtS4TV)sx1FCH{i$yI7{knNgtU0-P_b_X{$yLvZ<n@l"
    "+a{Gz-O*dAlZAmY5F`BCo#<PfOuZxI_S0=0n$;kVbZcN{X94y#UknlS7G%#40&<%o3V$C-Rty9#%I3n&gQ^td2_V"
    "+btEo^1B+1qAM_v$$V+boX>LEEqr9GqsC%@40kPEKDPoF?D@&3)t5!P$Pt&=~$ojt<`(o+mH$<)`ER1(O!gm@vkH"
    "E2RQ*aryQDztMO<UB&M6%*5_EoILtsomK{sYjrZE9#LB1#t1Px@z%78ffpdm%!Ww1+FHA}0u6MgU)AY1lEu+(5Rn"
    "$z`O_da1a+2*`r~b^=C#swl7F2sd&|QE)BWki1A5COV{!r1c$EY|jeZ0Wc+O(M-#+%*6V_>ynPs(F4vA}$`^by3O"
    "E4>e81;|m=WnT|F&_964$h(zig?q<v-Jdo-mBxY4(`4Qm8r$@8<;hOv8|kMa!$}Lw#LEuCI=Buh{6nGy_%rs6Tj9"
    "=_REZdEYlgBp39=bbhSyokR*<aMOt2e=p?h^y5bT7h{cc-VuN&)EY-c_ula1Ir4m7KV$TJuevIZv1em;{Sa-_mU7"
    "=NSmSj_e_%-<>?6XkB3<TpR+erB#=QHM~Iek$j`R1#5l;ND*zV(npj4@AV_NS?yZ7<!~zt<&<{i-L$r~HdDOWPmp"
    "8iE-4a5FqEPBS(lwEPeBa5?qfj}#+Us%T~fh;I$$d1nWrl7>j!|BxuJ=~Dhcw*({jCG+Z95~YOj<Pnfb&=04obZ8"
    "#8srV;n2RK13)a<w~0(3ng9b=oL9SyO<pmM*Ww5dytJ3*p3UER+ev355=C3NCI<=li>F_v|kVOy6hg`CBnMZR3DS"
    "9%N^BrkV6T3_m8K3~s=^c__XzWnCP;mfbSQc%O%C<Q(TX%(~>ObrByE#GKsUgU1_C;cw6=a*mZ>YbPP+xsv*Fx>s"
    ">+u_&$`b}+}e#XcUT`Gb+gdIt&$*>|;a)FmE$mGfq(neF1$i^lY+I^@C!iu2p8vf~ow{TVP-m!rBvoEM}@H}~U_p"
    "ZMAO5AAV*Fh^k`P6DH$~t1B%0jWm-$U&|nM{08{;WMBlZuac^XokL;5lnB4k}w{=%<alO#Zy>dblFO9JBDF$rWmY"
    "R$b2)AM&!`93U@f04-L1ju7&r)YvV?VNd8tu6ojj`qq3vCyYae$L=q75LbsIhtB?Xc7E{Y^yK7RexDr;_d(AezCJ"
    "{az`OM7@bqHm!HXU6<BVBs4IJi+AZ?*53iz;Sv24Y>*y+ysOQAi>m%;Uvf_$-DuLj}T)HJsVP{P3J)7!(h2la<Q7"
    "Pt?+I`|ng?1JZnt_E@Xg4rK9s~FrRr~cqI#-%maCc_!*u?9xGJcf{B*)q|VnIM8wc6K!@bI6u-W8*wkE&d44OFcT"
    "!GP4%H?19)iyH_@>c?dZ<J)%INEDB7;J1X|+%<wtS;Q?n()i#mdc86-%nWS5Nrz(fImeoeQUc6r*ZvT!HnY2bF=|"
    ";<L(N6N$?2i6wZxDd_f)O8s8Rx+V-!ZX{b2#L+NJ8WWKF!}T)iN9Vi-Ws^^ts;E8g#9)hl*B9dCkAJeR{b`t8}$0"
    "Tde)i9)dFlQfCRB3aAHx)KPP#O#9N&_XJmx%pW?%z2xo5+2MaMMV4gp!&t1aMeECwP>HT2`!cxrEG;P#74=}eAOY"
    "klqQ~Bn?C%8|kp|M^e`Hv_v%??uj!xfn68n4j>h)1O{;E!ZzI}Lp_y&&erw4mS9h&fWj;OeF8X-|N&_`I1U3y_c*"
    "9G=|5NL|M)0%>&Yx_=QWyra(@xeACQZ^Zh$e;}oh6DMI5tEm3?ouzvO!lE*C|7G(?jfd$zy!LwYrEZ}<dM2ZTj!-"
    "?xMOXSgM_Dqd_Am;MB=6Ca5OMa@D7kRjR3z)exJOIghY$L#x_t$*Iw(#tJezi`?7x5q@0@m2sc~=b&TCJ1?l$0JD"
    "Q3bYXZ3pmfym)hD+88#0d+SDCa0<_m&~|O*_he`*r<_=ECS#50QxQU7tA$+v_ATF4;-W@0MAeVVVh~gB)-_%145u"
    "9@)8v#0-Z+W9nuGdv=GpPzN9LRZF<#h9h}C@w45|fCC4P&@P9~qY0YM$QbTfS(hLNZ%@*4lE6ZhDFO<7+5xr7#xU"
    "L{$KFrp`yJ1_$KpVYwA@3R?Gsw6xtLor8u5d}zrp|Bym|HN{Kp^Pyg57j&*4Y;Uyy&Jt`cKrLYonEg~Ilycm>4R@"
    "Ba3?`R^v@zx(lbZ+>_7pGH%#{szrE7>e%${^hauC^vI>lYMM`g;^bTT#kL}&*tl~A))E~7OPr7uk4cfR!@GiHiiv"
    "EQ57@B19nN{b+InH%UMbp4Dvw2P~;s_geT%T<k$kY2uOF9eaL1m)-suBUSo70Q7ayySM2>CTT_g<B#Q!TVw4y+Fe"
    "S(PD$!u53PftkIDHsGsl`U-5=VqV2N<G(kC}iB?K)*bONO__Fy>GX3X8eQYzgM?+&YO4?kbo5m}Z130=i97L6@(J"
    "kDu!E9v7fXNThdqHP%NFI0d)m_6C$~^FvV_A$>G@%!!Md&j^y>R)&hVNGqNxpQy(%leiA#8XUKCb%J`5+E=#t@}V"
    "yBTO!ZC6Fy7iHpI}t3XZgt+{W>Zy<QLFUG;z`^f*M=S#%}SS3nQa6gzW4U$AsbOnR$#U{wpuVI~sa<^}jdzU}kY>"
    "Sa)+hDa4HwshHCNn$eihkNV<GNuCuv`R^`AgPPlhY)KtUEBrQi}NB!z1lYuO0)N_z|q;fAbGe|JsFGwIVp%@HtmJ"
    "0=qP4!kFWWFZ|my~+3p4$+%`#x!l3(`ciIgTDdZt@i9`~UK8%Ba@m2)sHJ}H3CFguy?DR0V2q~Zp%?kD%G%ld!A^"
    "w(^??j{W==LE#Bewa*DUoJyKCq>RS+F!O6TxPc_(VA768cze!^Hb)@b4qNv`t_~C09GvQQR<3=;FemH+RdCJn{zN"
    "@8GA80N;!D9bw~9d6Ug5P!J@Q`bHeQdw0oMe1Qd)h9=C-GGXR%{dz&80<lxPPt-z7yt}RTW3dp<S6i`oUG*cxqj?"
    "XGU!R=rBaRiWh|^1Pt^IVo_w(N2(cbq*2MsM~z$8_DhaNXPrnMxmGOi>sY5L-#U{$~s@f&d{x0wWw?QEWh=xt%6l"
    "P<+a5G7)=LsNY9J)YsBEVTVVEVfm(fAyFw-}r<9xn<*?FdUEN!C3HL7|VAY076TaQHV1IG~YtYzj~OClKN>wWqtX"
    "oEZ$SKq^-vqGEEpR{!7CpqctkEc<M7@vaF&1>Jbxz`?Rq_hwr)w3eu&4Hub1BR*$!~A5>fFB=!-PIl~kD^D%%}{_"
    "$^k%Fo9bfn7{2-&NLZRaJxzx%zuH_Ru6)X|5SJ<3QVV2E_Ir$hphaeeb1JjEmzyUGf6fQJ!IbQ^G1UXD&H|QH~Xc"
    "O>zFFp(3>5QngzyCX17j&SLF`q1?8xll@xlH4LDeOuX((EikQglIUQ0p%Y5XD-dFi9Ond&GZ6rYTJsK`wdn(|N$P"
    "Lg4d>U{Y(50}=$&5Qu2+gR51qSSV*m%`7D-(f8iB;mqv>_@25*i)UZ?XOEV#lq&Wd75hu3`$vQPeypnVS;$6FF0h"
    "J}&V7{ta!D)2MUL4aTaZS@?{f`DKJz>C7F^J>X)!50g)^mAEbf)K%WIY3U%w1m1Pe3EJwy{|a@iBHTKqnlZ1;B>;"
    "1ez7oxB*jzKO9%>$vk>xycgkJP*4GtB=uxyG^<%w|GQT}rH(7F7_y|rQd{ZoB4DaDdJmV}C%D#|Eg{fE-aMWch(u"
    "i}sa6@5sb6<BT;(gAtRn`JNSHXIL0z(_UlRP(e(GL0?hn$foH9BdB(udCFT#I=orYDkMQr)Cf9gWs<bT$Uv8YW2k"
    "NBRDDFxk*RmE0BU<hDeY2xj1S7%2@TXa&=c;KE`T8*5etm)a^9KpdR%4B7*MU%<a2t5}gNV5S$@9Zpn*t4rBB4sP"
    "80OfzSsgy|JWTJ|M~pR61hoMK|O@mSoET3AA1oR5ulNIA-_;}ox^Sj`GYI;vy_Mm!-W(4W0Svj>#&sI-YLhiOQPf"
    "x`zYpy7E+{4FIpOm)VP{8u+6m6WI0%@LZt(|lxXhMa?g^d;_-RVJzJ2+5zq$#4}^Z6dVCzH74~Y<@~WN)sIoUBeh"
    "r*LXz4Ug^%8YA%N~Ox*=0fN_OPxzwNA;$mT&promE&XGnxWDFvm;ws}N+6TUMb+PD1{|B4{Z)<g|5&D-$WSdZ;sB"
    "U=hh#|c$Kjd6|ii?Gh;a1g4&e(wHra$Smi^USf0~PtA{)`zMoAC#y7}Yb$uF{fWZ^*-Ul@hQvFVN_^D6VH&Z;ZX{"
    "fk-NmsE{m1qHqq=WsV8GSc44K?0qF^P*ih4;J@U9ng-?i;bn&uSS0Q}W?9WTyli}w09wRT2W-NWaiW3UkaWdNl4L"
    "ItoGKn0Cj^zSKT-niT}*OY4h=K}tzCGrFciUvPof&Ki{O)ks%ltmk6PzC9C^Gc$|-7vqyG+Rhse`M@HhLEH{omyI"
    "R=|wdBYpG!`x9k4~A2Al5^O?c(mjS(WC3-s{3{C<;bLe7-R}!EZB1?u{Y*gk;JZvy8^?Y4T`n<2r?PH1S@8pROgw"
    "d7n7OkFpW{$u;yLzL$iGGmLGV@nl`TTki1;o;TmQru`4HQ=FQ2ggCh#ol-}d2o*nF;9-I%45o;Q6oxD9b-a8!by*"
    "(WM_26%=-MvQPVk7Wtj)xX_W|l;ev=X$zfraQU#SJNGl$pB~=o+?bqT`RreoeZh7#k#il2CDFOGm=i(GiKRWBPL6"
    "We4(c$_S-|MV`XwCU^YCG!FM6r6GNm9MyMAjEuWp0DpbQ_q(tt-6@7kU0yhjZH}iIn74bNdbFHn@y%b1ViYx|IG{"
    "a(oaDLL4(K1h{M{EY#h60KlVjF_eK3@z#vG+1p<+Z+s;IMl4WBBe)1KSt$goCTuL{=+n3@$6VmoI{d{lt3f?@R?>"
    "4%&KG2)Jo+?EN2m{xm^N<AqN7|`bE0=F4Kv#OMwvxub3A*YkeR12Q!{5#=H@fDD1X60P5seBwLKOjT-DlwWCqRXi"
    "1o{=ebxQ4C*G5A=4F|(E7M-gZSTOz^e6{rP){y;}0!oz{3y65vXI&OQt9{O?9@_J2Z$$0G^E<QYXp!A+=6ZI)9h$"
    "E?39R<9^br89RgZ<7b=VkVHk~Db0pioYZb2DuMHBnG8$v5JHp~fjbR#|nE(ai?L_54awm4jUm{Cdbb-hj=0&cRce"
    "c`KhF9wt84y~h*d#|Jey4hY~*C+iZ#uujte*Qq79oyoflLEWf9i#?Y?Un!Zp#odA@T5ZY-DOZD+K4ycEnptlpo`L"
    ");gfp<C>?EF|KR`2pJlsxRyhy&1_yylXq)s7k#sf}{>b|8cRzn<(RS$;Y`Nh!CFIxVTw*wyw=y+lefPz6@QFb-41"
    "Y=Sr6}&1`#Z`4%vK^4ZjGBF$-sw4(n-z|LaYi(sl#Ct_i;xQrOZK6e^~-ubCGK0@)=FwaQ012zs!J+NOL1IwQMxQ"
    "kj>7Y7*yaEiL|NOPdX&&!@lQ9}MqFJ@x1YO@dI87oSHdHrTaZ1<blluR8hY~QL1L^<G?5M7raC!u!mSX7X#LZ5$="
    "VIJMDVmeWq<1i8DX=Mu1U|ov)#H39ShXg-w%?Pt}8FjAUq}!3Hl+np>)u_x9vZ4?<rTAkxiJB&;^d2wM>LATJF(="
    "(5$?K+4q75+@oGcgRW{5&Ch#Gqk{~bZ+H_MGZ!>64Cf47%b%vbsBEA^CnyUPPrDPeOOJ)r&b+qLkw_85^sTt`wmH"
    "F@1GQ%*GPxqx7*j^ZB2w7i-c3@pM2P)_&mfvI>Dg*Xl)@gxFnUzzwX(ICrZ@)$4w^sVhD#Wzo{ovO#yCL|yggKV*"
    "&3f5B?Vap9ofjZTVaA8Tc7A^^`1*XMtPPf;!Z38aXn>Jp4zWsC52NNA{l2>Xw}h0X2q=u><QQ%#e68M<HQ|G?Wi$"
    "3%5P}mcf;Ybs8&Oq)8WvjkOz4nv{FnA22g+~%~hCrw@C`oKptqxYz){u&OiPy;<zU1%hwY9$bCsVz}G2O52u2D)e"
    "{qBsFazYCd5eg!qA>vrMHsH;16L_ZUj8sdfD4GX32Iv`9VZV+)+&9erLQaIAs2_CXH(3-PBb0Ah#NAV^ct@NpKl>"
    "G}*%=f6qDc_c+_K_58VXp<N5+G>0=AzbWC)$=R#F>M3fD&_sB$tQ;o7_?opc-|Td;){K@AhRw>;=zZRGlAC6;2a0"
    "^0xnZb$rFyq}8Ke;4<sR1~8}jsNkN`!F7E8{yu)6BS&O`r^&Q7(r_&(yzVAW?}b@#E)`Jm4#(_Ij5M;$NI+dv!V7"
    "G)RooPz^t=%FrCCj&;i7D?_$*TctpY8bN89vi;cxqql(EDJGE16Wky6~)jVM8bJBzMdxu&%0P!0SIJ<X}&OD_&Ns"
    "wk}Yq(Twyu8<&rZnS@d${_LWtq{no8a1v#eTQ?o6QRQYI!f=a8vpyWsAj$(At(J$6EyJ08*5oG7Y%wNZ|ZH>#cVh"
    "kw%@E)7>`-d7(I#Hp;P&Q9*0xfTDkZ2-a?j$@@;<D!xD*4Cqvv#`l2qV-D&0p<Cy^u5tcX!f-pn5Hi0%N)9Ua!W<"
    "$#}sHxgjlN$k^SWQwAGGv`Z#x93U&xG+k{`HXl<kQ9g4j01<R+)1i!9Txb)>O0McmQ9dwKhS1!k1Cey~&brBeHL9"
    "|2b1A7wjs)Il;!;uj`Uha491(87+r&TS9C$rt*0mu4MU^GS;*MD58j&^%>p&!r{xldwmd@#5v?`M8HCo;H7+j_cH"
    "26bDEcOQ4!8~nRt0~Y9pgbH<%iw@T%#9rzh11cFd)|(iRB+UTh#8oog3NNbhA`QOsHAR|qckbbLKtn1e1kOi1Nv`"
    "WavqYJ7~_$g$UsHc@xURARsqAiYMiM`M3+q1cQqERjiU2x^t)xg)Q1yoOHyCatRq%w^yA=EBjlVRD2f~nBjP>UZ1"
    "Gvz?hq19s}j-HIT5VycsguhufUGz6Lp%G!hGp4qsjnQ9pF4OK8qVGo9j;x9PXJ#u0aG6&Fyzu;p&j-ozK-*<+@tw"
    "(_9M^PK#KwOx%nnd_e2lT;)<E%<YZo;v9t()d?}OTMO%opAAlME9V4<o2O3RPTQ5QRtu+l=jbpDG0}Hry?shJqMz"
    "+GCFr<{+3i9y`FchVcU3CotZ0S?N-Jg=YH5_$!ZDFSPHakwnp?4}`9u9JzVt8nB}^S4&r}U93Wt|3!sKAJQ20%{N"
    "?#|UO&PD*fEvKsTymwB#-;Vt&{Xd%6@5tFW!w)`JB#;t^x))IEZI)VEnLBH#i8>$sG{vqzk}&)7W4P<d@fy?z8R5"
    "YJ8pW#v%EW$<TT;gmm3@6(VBvDJoR|7`4!D1t-Z#1-)MF7uges+V@*Cp^%UW0G@(x2pbVMARg8ss09(;yCG?o0b%"
    "(%EuBfsh!UF;`?z4?Xj|<AGI;I>SMv<)S&oS|LFBvEfOs`$K=RY1o=y*k#xR;H_ziW@FqE7A}eU{zObnzi^!cy!L"
    "cK<vi9s=5w(6N^&$i#@CuXqa9Lx|8$aOY?UMPp(pPdub9NpT(sebFf!UVO(tFImn{k&-Al4`&E(KjWsJT|T(o4eQ"
    "M$`ZV?do^9Pb35R^gkp8pF_5)FaV)NUBQ`jt{lG?f8-|DP;*Z*pF_wpeWx)F@{=J>h!c&W#HAEQTcFgT4FQ>u&P&"
    "Hh_~x&e(fUo5yngo*I_a`(%xySv|XUw%u1^oYVfK#c%lS(IHE6^2z$2;YWKC>H3=J1!_Gypx<D+H?ocTuY8OC@~n"
    "5B`=piLB!Q^r4^R3k>na=-%22qEhqwoBZ*u0JL+{<h2qmww;n0o$AKtC`4nUw&U4f#5gSQzj--rwEoO{v1C|3L-D"
    "iWQYp4_(Wuuu8>tDlkIAz5eOn?%U8zv(;PdEV&A#O~gDG_$$*PUi49oVKtMMp}O<A^K#5jLD)y-4R9Kw-YwjT&Y="
    "fDt0_j*Vy)%F>1zZi@GUwp;^%F=kv7x6Cdad46EynbnZ!zgD5zx*)Y@H@L+x25=)tYo?nTbLC-%yp1H9%V_Gb9r@"
    "yMXphf_|FIe2gU%R3%=4|F3D|I4MI!1Ma)DCyn=~AYj_O?YW*o=~NOwr$7Aqgr+c32jJBeEUw|yDDwBhagSrIp<w"
    "bjOO5LjCv=M5!tMT6-Z)i`C&KO>46m(01?v5Y#}nB+aAOE{>^;InL2uOS9Gj}p^4Tucjk(1v8x;?BD(3{E15bkt)"
    "%xV?G_%4<v+>umHUVqGzq8`0`&!xin{9Wh&W#Qd(NUE9Xuv8m|POldLGTZGfB7ZP0utOSLUjGjQaCDKuJCi&c5?Y"
    "J(U*(P0{3TBkcu`F|Mm#0}0ALP8SGPSI#7nZCh@!6*|@_7Mo6^ndK#p~kWJ+-2Nd?pS_o9F$7WWc~o)|XRWl@-OR"
    "*!%0UDk6w14fCutrm%d%t}$juIr)0AOs^4UC7X!z)j^W-ykjr|ze7Se^?pZIB(T^@NIO-%ivWR?6n4M~F3F#hKYS"
    "T|rk;n}@HMBHX8d`PnZYYM@3e&}pr?G~eJ`>o{-~R~8hE=J2x!Z-R$w9APqdIsS+Q+1$tw!Cqa*jd-|Kn@>*jZxi"
    "DVig?qU~hyDm@Gocfm8PE&rD*K4r`exFuZEYQ&mYCJ2dEG!*NAN9P|#4$L(R16xS=e1*?i$pJrDPxUN*G-PP^>Og"
    "#8i`Cg&~TA1#GP&s$AG6?c@;6835VtgEbg1(AHMzSab*r?bQ`cZgWqHH^`5}`pUH(5!R+Ym`qa~9;A_{Ig;hqBh>"
    "p|t!OsWB=fhu456=&RrMkVrYycQ#KZ?bJ`^$Wc|7f8Dde<&j(ycM+cDo6tCk73Mb9T$+u++;P+3@(pDqC=1DVLbq"
    "s5s%m#kK=d2mJS)wAa7%=oBk<<R3C2)fh$kRQot>daB=Vy5tlC7_K?iZ;LLuQoNUd&dUD(zocNI05(y>_-4I$&$P"
    "hsQXAFauXg|VO}lYW)YiscS{ym-pdQd>RHBlrP)e8C!4&PWdzkwDfIr#@f8{)k+~=FGhhP8Un~hzJa3Sf_V{8Z)t"
    "`nT~oL{{Pq{XVG<kIm_yVNf3Iq9*%5M#oV@`fXmZje~}x`=+GM5^+PdgSB0*A>Nf^otMK3=X6Lsv;Sx<f|?NP(4v"
    "a73!^$nTrLZ=2f%=eIrls57&OIq}eosn3C(B-)n)Fb@jVZ_0A_Ia!LE)YvlYFUgH7cHU8_tZtUn07*&=bxkNCDru"
    "FihaI0JDP$UXwuG(r{g|!`XTpx6z=8-6~QXL|~7{r-^K@s1Jvh5u?w3eczDC%xT;w;x%?05^+8ZBilpKh^-?Y4D#"
    "uA=(0^=pxP1xegnp6E-)U*L@Xlk`<rLE(rcg38hD!g&N3+mcu02Mml%9wuqv?NThw$KpmxaZWS^jXb`!W8aZIEq5"
    "1>Oo2-h8X%f|yh+#9%AjK_Pk@gX@3Ron#R)KZ8c&D;zleD*5l~<s6vk-#Q5N_Xv)svA<&IBZy0iFUWU7{sTdklN<"
    "BHMq@|ck<T-ypq*#urU^W(vf6{S-`Q<Ul#6v`nR5g}l2(hpSB{=H)9m)YVw%swDL6zA$^1}FwbR;-sevfd_37pMw"
    "|p1KTdW=pELVSq{hdU$kHKL!b++fh-xUoWGv5hnd9w2k&|QxKmDt@(ANppd7*#?Dy2id#EzMcP5@_U49AK{745*7"
    "^){>fMmy(5N4fO7Ql_&9?scIU4$rcfRwEmYSW_3G(>*{t2}H)JlC6ecxT-KN+Js|M=SIpW=$@9&Y8Fz!ZR=Vfl6T"
    "_uO5Tz@GSFoSibyp#QAzGnx<8n#Mp$+Lf?7%dGb~d_P`6g);jM>)Dx-pYp;h`TcnLJ5%<~Kr7#3>B|-t(RG~D;?L"
    "=O-b6&0D=9#Ag3*8=0^g<Gf9`hwc=>w@j)Nu?q0Ehb8;*+#i>qN8x`OX<<TxQy!TB)1zKPwTuF&tk2O*CQ8FLH0+"
    "};cvkL5S-NOuvk$mUns1jBl&WDatMxg79WO5+5kS<y1@SopnyfS3zZ$f*=T^^X!X)AhXdF?pVRB>n3nk`#5V4c9h"
    "4#eMc&weCihHyBppV<#bafq&*p8oA6DS>v#F3`2t_FT8Fd7P9k`10Q?4CKGQ9G{rYGRX^rt@+VF@hMVyzxfQsL<a"
    "90`Y~Vm3th{SgHm6uy?;_Ra9N&4@m|StEdY3<d^1}9T_tVnoPy-eWU?iU-=D6IYOz`BYZ?=mTrl65(O~Oungh9EC"
    "pc52Fuv}lw^0D!u)Vh!Eyq-EY4f#cgK3Y`6)-<XWMzjxxoYhyB*+a_FTZ_PKyNeD|+hr<|;XTx{Ll)Po3|GJ_R?e"
    "LC$ahyEzlE)rvi)R7sr`|iD*Mx<b=hVqPuuAu0U?np>Q`yoP@(PV)!C>!<mm~YYN4)Tx@i{F@3HN!U(2oDTu|N3{"
    "9mNZTU|>x^xKIa!s_l-{GVf&HQlF(SM#eLI~^(K<!^|{O=lA7H(O4bG+18)fb5m5dkojhR5`RMjgehWLLj!CwRE|"
    "Aj~*UAd7sYmImUBxzO3$c7|>(8mRmO**Mn@7QyW#Xq4x2QFLyWZBc2R-o<!VLX3%6_(ysk-*K8afEhz#W4*I15h-"
    "yH0+X$X=>#dQnCdEwEaQ50*A`)Nqi_1$Vy0a{9(Z#lPk-q0#icj}w^2?70rw0x#LR-(6Pd!UcPW>By@%9zPR}rJS"
    "H+Agc0aHSrtMegswQZ;wmFHVfubs7^DYJ8jz!g%K&PL9<7C)Ae3F|V>Iwb!uH-&<o(#$%wC;m&GXuI{~#;l}pqJo"
    ">QL!B@LP2G?pgTZy)=`Amuh2?9#9;~W%!FK6LN9YT|y&A@-^x0QY>h)aAOo1Skzz*pZY=_-P<9M;o-2~(RsT@==j"
    "9tv(YboJ(pHg42RzDEd>)UU>+TCqPVkS)ot75@(t(VE~ZO2|Df7o@0Y(?FGRS5aMz2Qe;lLAI+#vi_hy`l5<d%a-"
    "h3$MJyE7}`#!D-qwdqY7fW;=(KIShT11+88&C_?_>GuZF2_#}5ed{Rcx3C&G3jIg3nli0C+vK%4Ot&5$tL56(_31"
    "e)B$({+J3u|!MCc?9IgRGJp>i8R*9X#3O*Ya0(HrY>0k{r1>=mYKKPa?tGoMe=(^La@D0sZ7jUw34iJm4HEP5U_o"
    "zYtsY_P;S~2lFE4IG&S;cLzo=OG|FBAv{9)7J2?(UK)NCe;VV8_(5m2<Bt*v;GEJ6UtTt_alIR1;SDhm;Y?v;=6A"
    ";#bleu(+U@--?Qs0??q!deMHeRgOT6r~q)+6Nwo3)K7~@;Yhb;|tF!yKx<l#p@(%L9#^Q&>{$D&goGXD_`t|t*D-"
    "3bxTnO-;8id<|-YcIkedjTdSC?EJMzoJ~(*&P~cL1>IuoHU%mekowT>>nKpPAaC2Traqc#b>h?eR5^Y4q8Gfz|C}"
    "Hsfn!e6x!=3-Kvx97mI0r{R(T$Ca)QauEAF1SBguFHA^aaUM$`iSCVg6ccYI@#;ECnp2H+BfVu-s*nYLLkMPyO#S"
    "X0W6$%sIz~R{-;6)llYo0HLu%E71H-nd)gDJnh+*Mg>yabQG^m2EX3M62G)<Jo(^S{x&wb%X6-R>WU-OJzqKSp0}"
    "bT@2gSP3u?BIsGFT2sOVGf<t<TFHt!-~xvZTU)R=ha5X{&1a_>D|T`3HEF8vXH21=!3cA4XUgw~x*?p05OZ3+^E0"
    "R}{p^%SgIU>`Du6VN(Wq$M<`LN3tHy`zBVORDgK-nfYvL2Mk9pI6cs!FROfIw2<v({>Gxe)q%?b9WoJ!>fZsptmi"
    "O3*G;I+~5!S-~$z)yH3vouSkN-=;Hi)R?_^}-?!gF?1OP`4_b5=1ek7X_K24p(=J?$*<%)tSv%y<MDRVD(zWy2Ey"
    ";li4htr-^|0Fz%_q$(Y>I1HsFD!TfMtni54ORi?OIAn39dkE;|Z7f9z8%WtJvSH8^3uo?|v@h%vJfXa^~r|GS6H("
    "wQ#Tok~}ICOqGJz^9*seaA8X_-?w5@?QL4H2}Lu%$VX)%Y|`u5ii0`_MCixgcj^6y|5Uq!hH_47GAGF-VkA{TDB2"
    "QmF{b%a>pM;j0%PUV6LROP9ac`NwUx_=ER=i!!9Jg>kx$qYK3>K#kBpQqyjkmey?p*C?dNRkY}V30Fpxcpn+Re;y"
    "9IWPnK+s|cgJ7a6l_LO|kBlS#go3b8l&^^IIjKQ_UZG{&r(ucNZRBEvzL|5EGVAZbRRsRwrOJoE?&D|1j+aP4IT@"
    "K<HZ=msWjc^#?4uf!tH$bCff+;ktE$*7_?-KUdb)6Hp_5|;FaT1CzA6$a*yID|L7h)Uqi&OkSX803S&JF{oD3{T<"
    "9FaNa%XD-Cc#h?BD%dIFuO2ztJtTecuxZqixAe4?fE_##1BQXGjK4GgKy`Z>rc~ti6|5aFn0o6CxI<FC#liRjize"
    "yocb&UL`fG7-x3ZG8?<a&X&AYIJITUkUAG9^^;3^}PZ?JJzW71)=Cf@;=$3=Hf^2w>Tq#4{)q_`>d!P`_m4pM?75"
    "8lD=P{Uii1EeB6}|30hp-E*ToJ0*Hv&>?mwqU#TRFcha*=+&MS<q~KDDq9Dd6zML>y?NiutlkJq)|?^dF`MM~(ES"
    "$(TlT_%EsLH4sFJXw)60~$o64a(102Y|4Ovsob<XP%dO>YmbhpA`wlOv@1}sLEweN$5>X2Mgq}g>6=qps`_OakWt"
    "~#+fbTA6iCTpl}Da7(8_{drh1(&U3Frf^HIGjQG9?1viGJ{2ZQc9Nj+UBGzd5i*3UPhmaxBG7QvM~j#{?ghB%icD"
    "+)SK+Wn7Rb-4iy8QN1p9CWA*^@Vz_vIG_e3?@!V@L?Bj8#e%Sd_s7F8jIPq8jKkl7}tA_#YPet<Ej;iy8>LeV^J7"
    "qUQy>ns6uGBhu;$EWW1%8%IboFRlx=v?`O$avcF1H95mZoHn=$0_oIahJJ5orFU*khqDU9yFwWtrY>AkGcA#*bhd"
    "3%;?W`!S+UL;9oxlkTAQJPLecf$kix8g1t>^qY3vTBIg$Gvgb@iQ?CV3vcXqjnCs*n0Am{0mZ{cfz-l?JXpT9_n{"
    "iZ>Z3$vf@&xjQFYn60!z14QQh5+=KRBz1Mk-;HslL`j;O~f4+stL34|}lCdvh(qqOc%R+yW@>1z<<2J~9yrWPvwS"
    "oQfs1a90^iGJe%tdGFWT5vEl0~A)q&D-d(@r%;GT9*{jYw$U_a#ht!4$xJ=5Y23{VxPezTl7Au{C0EvE#t>7)^oj"
    "ewki+c=cAQ;p6ZJ^+yC+4&ED|mgVVFaljDR`3u}iwBTopMd4GjVMIFk7E<O~@0d*PpJ#fE%!q`MuCNgWu1n9@#o}"
    "Rn~GJ8clLw~3ezqfyW_%j#Z;Xm~TeB|);-wuy|pnK+*eQ*EZ?YT6nKlJAJM<@G#m3#8H-g>=vcqDiDPrb3fcf5aa"
    "r1#7(-`IOr+(w7^>U8h*IlV}KX`7hN`8T>uf0@3YogMygtbLas=AEC8k9E}Yw{7m{!-HR>J^XX4$=LsK@A!v<v*G"
    "E%zyEY_rcc$be(K!W$=Nf`&*&WO!yK5e^WR&HdH>|i+oJ>Xp8k4tIU9!IxC~g_MZ0<|vwUo)c>iec@QwC@|JGZtP"
    "L7#?@egwm7Mw4_AO4q5i&<ok93Jl<zTM*rRS2^=&X=hHJAAVTOLR*2<|(EV>y4AQ2d8`ICwxmi0($f8?cV9B&TF+"
    "qyj8TqI{WKT8ijpM<!Jnl%BF5Ptfl5r!Rbo~VKT!&h1n#j;1$#ZZc_pq#xuoDaf{9d0{qv?irC6XN`(?yC1KNX%`"
    "mD9fJ}Su`;(u}lZ*A2yDz_DIPkyz)X@@hRK1TXBhIK2Ua_#{2Nb`}Mc%y1kP&k^XL9VU5+1iCmLWUuz*FNCp-NNh"
    "V8wEcH-(fcm2!vNadVAvX?X&!vACAxo1h*{)$~&79N9soiULJ$5isXXmd;i;cbI%KSwpiNhhr*6;B;1KC?h26sGr"
    "0Oy<g?4S?2tnWECpP6#VX9cgxp$Ze`oQA+Lr5_a(1#Q!d{ZU-RuED~DddY;%CRFTmg;a*vbgFGcx&6V<H|1_=vOz"
    ";k_=K8(@83R_oFDv^L#DQ6P&4y^Z$h{F5~<$zlP)H4KHyI>}UnDI1X6yV#NOlSv)^X%joK2J&wIz#S;z-3jiq8KL"
    ")&9dtp#)$g^-zG1ZP;!b0LO`;s{F+IR3Llo41by6TXMJ?zdGUd3v3`I_!Vq|Att#+TN@aF25Ek3B87rs=mig715+"
    "%hm$j#!(7-te?JkS^dmus2PRAJ1e>lv&NA>v$NKNuZPN;CS@!X+NF1<d<6vn54nYhx*6X=(B}3CjldNvIkZOP79Q"
    "s~7RRX^iz^cwMBkIxRco6S)Zu3=#R-`7Vd~WZ4kIANs`5y<MSd!ghpzx<&-U7`=Ogry~F<W6r)F=aqlSB#XwjAlY"
    "cM3Qi~Pqy|jkvF`2>_{C$r4QB?^>hcMqQ`Wm$n{(XPAg_S?aG_|+pwO;fV3C|5JG)^Un940SvxgqV><+Ho5>rtg9"
    "Y9sw29sBxPZ$(1WGq7MT(q6{+v8~tl%(yZTy&Mk`;55MrME#qjmU#6EQjd}CnzR&-b>5bozh5bC&^G;4a(FN%I8C"
    "p0F5v6Gug)_Vr*^5R^q3>NPa?I|7~CE?oHvX8^!R(mr`z#Gzj2)EyfEFyl$X4pciY2_=1WwP{c&pT`#y76FEM&d)"
    "8Ojeu1zDL--r9TiVP}m+);a6Kr}%9F9-dj24FSoIAwoglJZHy_icS=x&!&tgGa8_ouJAFP~M~92)tw#vCd*=?p_f"
    "F^f}$K$$JFTQ2Jc{Ctuj-@^hF^Yp!difdck650%?0fgJX6F6|H>BQ2FOIY%(a$LqtYfVfuP(l~iY|G#yU}S|befA"
    "EHmg~jJi7eZSkr2ddI(w9?ZB(VdrG)EG@@uLM<cS3`mkh7&0&Y367h{9*7%HpcTt&~s+dVR-17vb&qS~OnNOf&oh"
    "lOans-#?D?oGK~bcC2dX;#Q)%1f@S=3)ipsFRGS6~cW-b!6nt*oahVs;!kTBvt7qyF)F9^;TcLkf5g8TOASjtlY{"
    "6JIQ2SQl(L@NT@nTFZqQ@)F|O|s=Xo;0xODy_V+cFm?y9wuKR&o#_A7lk#C|^Aw@F5;JlH(^tk%aL^4K0Foom;Fk"
    "3Aeo3DoG(d%13ID!dJVYef@kEjVD5ymMcqT2ZJoU)GfJJp&1icP%_@>9Fm{TTgUE06Wstx-0dk_@{WI4&dN<?a^p"
    "KC0(JUzsqEI64f1#Vl9NWd93QAXqp$>Lj1^YLtqYnMmzYngeAi{#4j>OaH%^k{{46nfXYAre1L91#vZ4zy|8F>V4"
    ")-@N_*h?c{iZz<qd?%?iu}mu}fX@R^c7v5i_=r_12n71J?7#YrzI@U2lmgrx;ftwR7mAn9#sql}X<)xU^b_p+;L<"
    "8n~t5CIIYi?W&X>VpPvu;Dr7C-q%uiScLWRNqXITz_2ra9Gd;7&5vFd3QduhZQkM7}DEIt`KWSO2s44K8V+4j>o4"
    "{=w5b9e3pm>d+*s8@=5gA<Y11L+=Q4^Sihj}iKyncxWqb^4A3E+iG4>JAdg>O>2S>1FR76A;-PGwrHj~ms{Vp*g="
    "NRENU>q!wA-*CPnF|O7FSsEXN<?oPd(MuH0>sN-?;WJ>#W~NudmDOI^c7%Nyr++Om)lC8cov%`M#i9Yg8hJEIqKR"
    "keI|%@pnWonv+Y3<v$#-4P||=LZ6o2NX`{ieK3{{wz=t57PMSIlS(K7MW(CFs6rTYLM75bq+1)CEH>7kUad(ftuX"
    "dCUZ(~*x4XZE-xkDD$sV!==c}!9loqsKvD51^E2+Gjy;)ysce6c(cp@k1nq=Jec&xiRMkCQdtN8HM)y*9??=+gz2"
    "qfuI-8xW+oDwA7X)!qCQbBtkVMCRWh*Xd$srp=k5LquXr;KZ0WjG~^*yBnC(Sz8}xVBd>*_(XGE08$Crp4BfqD{a"
    "m(I6w2hzluJPSKvtRV-vx08>GGW5sH;_)E@u$t#c><s2hMOkLf#ckq>k95mD@tmbUpXees%GmZk1@E236QC}ewi0"
    "&uf!olKObCE7~{&!2I+2p?na320;|7zQ&CB=u<c({|@JyhM-rNc%I!ikLv=J$zj>xty4@4<p+Rg<Rrb`5&-Nts{g"
    "8*~FgI3t8X&`IDNL^0fAUdEa#$fMB}vp_f?AU$f74>NRBK|cEzyKrpb!-^;0ba%h)e)-2PPWvCbOMI=HSKTT@5XV"
    "*4#kac^Y>JYox0BoyGs-8{z=0ID8S-6JRxt69@a~x3bqvJXthlZ^Y*gkxb_*IX0}_a};rQg7k61l8wW2u%O}*W&y"
    "a9v?Vx5Y%==i$A`tTw2ap+OWmW^hm1<L>yw_IKNVuv>YvKcN(mLrTl>M^rhw6dq5gU#0Sg%wvFfqWz*`7|qOxMo)"
    "IRe`_XLfxQI4{JQ`QGFw}7jDz{APz)MY<iGZb(np4q`k*Y3DCeP*$QHWT4n!e+_sxIya}rg(-NEe)D)0Wl-KD(;&"
    "uHTTIUAPLIJID>_I0v`}ZTnjs~uDot3;}uCZB0TmyRid#13SpCN&^x`AWbELJ)PsBWfTO0P@|28M-ER{mB|A6Uh3"
    "mS5@Jw>Dk3IqD-!rX}`ea(YQl@}&;LY)jNe!`oUzU3!ndw3-;m8D_hm2Oy49yY%5xiA8L9_5)Rs)pepAZ{84%FQ~"
    "37^Guq;P-wO3C36aww;1}9r%z{(CE!p_^bIYErBmB!sftC1vZ49T5M}Lrx$5}$K@}ydtf-}AZdF_#xGGF}s9>!fW"
    "p(sm<R!fm`)<2o1kN6kLC97b8nc~VC`lMS4g-jNM+7Sa2N->UgR+8|vpR4`FW{2M--g@PE|4ohuBs(feu}d}eu>-"
    "J|K+~zNcoNy=_Cp;zwn%)KZ=>Y$C6rps2fjz`VMNj>KYq1ED$@gLJFIFARl|-4M(qnoa)pB)I7Z#qJh|e3|-}uA^"
    "Ky7shHC{o^Nz$ylk5~C#E8^jv(HLda>ahpwjft?!2qwBPO!a)gk@d<~?*++1Kz_!&}Cw7R=x;C#Qcsd%L%PFnoJ*"
    "bhv+baMp2-(rI~jwn&%NO`+>P$*0rdmE1Ek#Xc$X4Y`haz(XvHr@y5s_x-jPFXM>4SWPu{o3lJbS<#4dijQFa3jE"
    "WPio>liRgT5N5Jiy5-NDyhxMh@jt71N@)d8DaVR2|-_bva`o_QD4G`!#m`N>tJh#3p88juR(Wc5%N;qw^=WAI;yf"
    "@uX^D;!U|UQH!@1eibQ`&C%Vgkq1~dP{8=w|GzdTn089t7nefRU0K5V~k2Js#W-iaPUrYb>}t*-7zTS9kGa!&CT2"
    ">s5ocEmJ+9>XBCFYxNX5XYck8!^yAHWa?I**^7immAOFLlQDsJ9{akzAZHlA7DDU>JqM|-z6w<SS)TXc2b2K+jF+"
    "qD)RP0f#+;*&Z74gGPP&`dz=*Sg!cUBbd;dJ&M9kEv>jH0_h>m|%wI9V9dHqo;S41-6|OU|-PU5%hb!qk9B!RV7o"
    "F~$^6qvwaX$VQ+7>BZ!%g-ZT6+Ma?{?*N78tJWBUqk|n8*~T2v0K0Miev+4P=q@ROpKGoYDGrPGE((d(KvDIr)wn"
    "mE7wkh;oa-)R34xK{PwK;lCRq>o6)hU0fNi4bB_L?b1e#U!c34#h?)Elda%y6O;T`xqvyL9YPFJm1MvSz&T(1;kl"
    "yX><E9qYx8jb0EE&Ox9r5P+5sYL>?T5OBk?u6{otB=-Ue3XJQPzX^BhW=28aEB(`d}ZpE$O_L2O2oMr6r0JX<{=-"
    "Wo(3EZ)EC`7TD$J2#e2~8#G=-V=0INT?D0ZKV7=j(IYL8XA29Z(YI>PhQ7XDcyHHWeRxYL#f4|gQZGgn*@xRl#x%"
    "A71po3=EIME&7>DF<Asx~c!c}nFmf53g&>ujK(*#~<#fgRqWe#VKbm$mc{x6Y+tJG!5jk%dngr4Jsrs-BbP!>Izb"
    "lxsgT0BQSWE&Ew_TR(Y6HR2lgScus*4fpkBJaO7%t)Xtvk={p&cTFGTGy2SL!ZjN5kpDmS-iEo2BRd=YD--Ef3Gf"
    "9V$(y7SI7q^!Ae&j5R7lE>OH=_vVo1&v2w*XQC`93ZzkR;CPk+n+q-1Y4>o;$$Ma)c3PxtBbeV$_&N$o+gyJSpER"
    "6A?>c|MVC#<mW2ve@F1wiX)2@W0`ABc0(+MVt3q4^~c~b_!Yn-9=)))B`NIeB_P>4Gfc#b(i7LU#zaV{IZS)M2}L"
    "LHM9boi2cT+f&(`nQR?Z%$I~o9IkTVd9aPsp{5V=1t}!J0x`nbm?p2RVHo*T4u6XM<@cs&6ENM*!{NLbel;b_1|H"
    "N%}&1<xY-IE%g;7&jDdw_oiw>baez+wca;V&O~Vx6AUkv+hJApd^Uxs_Au^spX(2upc7cJ6&z$OnEHXKr;|MwM4r"
    "D_Q|lm9H6;AM=$ow+Uj2DQ#gVvQJ2eZIln8ff{-zoCf(?H^=zq9tE-op&O*-UGI4AogNj5wWB6m`N!yay<f6)lT;"
    "6##8Qu#wLz?4K5OcRE-=)6L|lwMG5`(tv)DC!l+Bm!1e=u@VaL4p8ibk=1t>T;!U>LkUYTZ{f!nLEVYVe!hVr<|#"
    "%|Td60V0p6a+l8y+bU5>mI)u9;tQfX=E#`+JveZuvuj^nl5-}#+b+eVNOW7L0g+zQ6jhCas{v3%naaWz&wYG&W%Q"
    "l2ro!h1xLt?Hd~-Wt1^<(4Fx4$W5Z?2TL8#{GuR$yiY;ZW*WI`O45_@?Rr#syWl}(YVGT9}W++(ch>eBCLG#<&5+"
    "Sm%KOyMf-7cki+~f<+x`DnPfH<0eD6|Zva1^JPY=8!GESbj@0dO}M72P7R3mL{t1?63nG0dRq`8(Kxw70u9#qDst"
    "XBnZTn`H+MX{0a|;w+$Q+gT+132Jq?3>kNfR-CyadmsR&jzHrSA{y7ibGZoz1@T=Fk>nW*Iv?)>wwiFzbc+90u%s"
    "7eJ!~>8RdzkI{UB{i26UIuRd0nB<R-z~2MGI0uoIE*;M7g?<uz=&nh=)Xc)&fbCZ?bqb^4O5C4}f=VC<eLSMBTu1"
    "(NP{C*iSQnXwx}fWqIPHmhElsQ^eWRAwA69JqhR7~hLxfdAWx(J4Z1H%R^134yY>;Aa5v^`91)YV3Nc!RJ;V%7sm"
    "|i7^{=VbB0^lfd`fBb6b#Sqg=WQX#<$@}dxmVvf#dh-Y(F7$(x$Y(1z-3w3+1&S<clPm82-CUJ@$79T%a<=VaR$?"
    "-{cGJJEmw?CvFC}z{EmQu4YZbWJB?JVe9l4w_A9!Dh&{;NlTzn#K1f@N>DYbIZ(u)!E9WsTl>@A-$nJWWH7_H7>#"
    "7CCo9C14OuoIhcID)O}p;z?*xlvEOUr3d3w6T`y_o2!9!ra27R!KxD$X<T?h<6;KIQe%KTrSw2Xu%>JhNM@q@G9$"
    "H$ti@=Z#S#HqfT;BVH3~!|u6c;c6|#=;;#d!cDJfi0NK%(8F86*M`ZB~wui}nK9$``FLwZr~+Vu1y7?WmNj~o5yQ"
    "JLCZdP#?~N}8MaM2&o&(Y`*bI~sUAEN@+arx3ub^nr2j)BSMT+r4De;Vm%b&9C*!?%#|`yN`=u2o92SvE3!9Js9P"
    "=o)&~c1iq#|Yb31n1iGhCu3=%Ae@rKVm1UzejD0g>+!3_~_0?Id#Pn*EVo<Ka!7{3loT@MkxN0%O%4su3^B^BQ>Z"
    "?38K8H@HNq!e_qpD!_l+;=ZY$ZcCp}taY;6p%I*;RqWLw$sdzB(H%KIDmGRjY_tdQSYF5W$+LQ%`KyQ)&r#ko>j&"
    "WYemI4u_-(o@N4od^Xw0f)Y;-EnIk}AD*Cx8H!ML&+m!N#C(buyKt_2Gf_r^fMH1NkYO)Ghfd|Yn+?ek1W0C?+Y5"
    ";h7-;B)02XL}@7N@e9$K$|3+fWCe?nQp>sai|Kj9zuTdB%!HdB<!zuZDM`mpo1_+<PQn21O6ietb{ThEri1>4UTD"
    "f9`C(r(8rj#FWZZcryd!71zOXmr@ngmylKikJ?L_7C5_0(2QM_~{@mjdaA4RwEtEzp+LIlu8N>-kN_I;}?rdv{p*"
    "m=*(6e;bUfHoj&LZRAr(&S*C>44Yqz<Q85e}<;~8UgjCggzbcKmM|B&WGJuzT{zRbj-Rek*6#;KRPLWh$d2Xqzat"
    "XoD?0TI;lW*W=ybaGH&xxc-U&D~bL<HvNM*2!zkg3Rb9yro!bRY0-)`37@;<*rDIg9PCiSml?#IXQ66;78Aweiq!"
    "HYlHvE`AFIbhY7ZdsHf{+(W%bk_|Yv%^n^s)_P=I`%P&Mg)LUm9!pd!8YA16>*bPA7Zqsac8f;ZAacby_Cf^V!+j"
    "9T3AZ`4GNsLZ49&N;+V4_dK|_UxjRJo)kBO9c?-|#Kg$A5S(9hVdh{r*4jJ`|2m8oa+fMtc>1?F&%h@g;m-B`rL{"
    "D^@L4ZVWP_-+n-Dc9pn=0>+SOlu1J(*k22d#;2GfzKv8p8+Qq3O@8e)ZdRGBPZnjg%tGpddgl&U~88*bRw_vr2tt"
    "GLr^1OL1o+JTiKe;OEFCNT`orp-v!?B!2S6YGSGY*S%^u%ZG8=gLhnlNi8h4pxPRbbyaMP0Aa-~qPvKrT=7l)tp^"
    "`9te2!<}GzG81ipxMyLSdPUEla)0CtR~sWeSNlZHHeXCK#sP6%%TP!lCnQk6<mDb|5|GmVKekNPnPBbm3lNRP9xB"
    "^Urxn=vL@K<_)!P?GWB3HFA;lKq_nGGIiRpMLpyfwH0;9$<(@~3$qL~;!eHOIIpf_r!gse1LjO&?3#njHI|nH=E3"
    "Jv=A4G<aWlEA5)(luYmlYhV+g~)O>gT1dt^I`poxpG%<f*@^wVFUy6nls{n6A7UuqDkp;B(-U@D0`oRRNkmQ))1o"
    "EPB7Ut=?Ao8Diq@o%-Do@QsZq#X5j3YEIhsSS{FWVE`002(MmR-M+Pg=#uTTt_XoHx)+Wp!nV)KK5$NI;FKY8g(A"
    "qp)YpkR$$m^Vo55xk2CkuyXrY{49{*bg;m)K`#qD^n=4JtR9peX0V}Dlj<c>hH8KL0j#9R@*Y;X$*E+(zs>)7OKG"
    "_NCBs+<g_p0+d>aLy(o|Ra7UDU5zSRIV)9eJhT`pvSiG&a>Yg*VrgSE?U%HE|^0RM+D$AnF#3?^3_Sx3eguJL!-3"
    "CU3p@UhlW~k#JA=sqp9cL4WJ`G5^Q-Atf6h&^_B{*UFc2XH+0OPMRw0xdIDdR3Qd}&n0J@=t#Yp8}t5RSr%7D!4s"
    "tl`ptqFZPj@&0Ni1N(uW-D^xbHO*ujr0ToohawCGu}LjCpN`Eg%@SvS-<bp_q&wRru=zyL-lmb2VwqL;ZG;XE_y;"
    "kuj^nC`JQMhiFIZRKW(^XkSJypygP%%-{^l-@tHAp`3SH=Bni5VOZOV6F#dns6n`toWoX6I^Lx+fZWxt{nQbYolp"
    "a2y%zMo(8u+c5BA=1fZ3+zI_pa$v=z_dA#UuVx+J!7BipE%zMI<%s;&&L2M<h%CqUG&q8J1kp0K;!BN187W0}hj*"
    "sA#;dwIOM>8c3X8s-0Ym%KYOY`sSM3KHEgY%hOO@k=iKolI8VUMC-H7$xo>qYOyx3TOa_80{eodI1RSJaWb<jIY%"
    "d)4(dX~17OavA7cozTJcRf3w!g1aM__e(AMyLaz97|MKK-%gSm07vd(Rcq^wkkl%SYBrw%M5Rh4&`wffA05;$D)x"
    "B(q3v<N6GpEbw@ArSuV=2_9)oVe{?-Wse`9zS{myzF%yJv%a)<c{E?r9;(}?wneiTB;8i#bFaty?$Oo}Yj=Rx#V1"
    "8rii0o9EG+Fhm7_f+OyIl~-1E^w=Q?sH*H$L2@L>l(X##812~4ZS+#FaE;0<VJwcfRybSRMgF`u_G&Vu4qAkmDBL"
    "dx|z$uM-<VRU(KEXC-zocvi}%*%G;=KzM*_Y2s|v8)QkO_Z_pM1Zsp!0K1w4sELFfldc}h1IC^d!d(L>M!o*AZn+"
    "2G1WFwovD&LVM4Lsvff+nyqV^&Mr+=CM}aTNhF@T1YAIiH8O^Gp{~((3?{2S9aT?hMs!?8IWiGY-VV_!){;GJSQ}"
    "-Ns0wsUcDih5L!b>0?`f)cLWTAQDS5`kqhQUbbdOM^!r-26RltHGf{Ka(ag7oMm@QXww<2FLph?!ml5PfwghZ=um"
    "o@SV3`3f;qd?OksoOA0|qI_Z8P%5;t1{Joii|eG))vCd6qD2_oW~Rgr9lKIC0o-uRiSMq5Guqgr!WWOF1bjgs=KI"
    "A4}$(Pm{QBzu)%8z$BQ_p%#4c*)CF4PKyMX7B>}TMmX0cM=GxJfN9K_9Md>zdbtm&$mO^NOnbDf*V<#dG;rF8EhC"
    "`%{W9q8>e;SF@sso<{_1fM$5J4<O`k9k{UAd^%qfyHH+oM64+|?$wTr7xfXCz2r4^YE(}98BQ6S~?$6Mn+L26Uua"
    "0hRtby{9T8^R>E1rJVn9X~L9x{t!QmrA*w+YjT;k~q0j*)5gmuMp)`YzVsmNsixcxgCPGUq^-SaEjbOvPtQ3jLW)"
    "!C(>ztw3WiB=WJ$h4(Es5WX9aurwR^HB&@2M$TUnfPS8t!)A8NtE^ei084kmsyvWti7Cd04;{Q3ran#*?qG5&Z@p"
    "~%kk@IkEFl_#MAo7<1MJz$FXr|*d$HVVGrPQ5&S&#=1&6OnWrRcRA2{m``<Y#1K$xJV09rD?Ds<;vz^^thTF)f(;"
    "t8_X<tM6wFQ{|?b|4IkJ|BBge)!vZhTyn*ERn*yiGqgbioZS&1LuZ=69BhX7;1v(`m{(HfO&Dbghk@s>9!MGkbn*"
    "~`$l<L-7Jk>u$ZnZ%e%Ukw~?c+!yu9(L;a8Rs~yZkAUCy>j8ni;;#668+t&x+DGjYbe-`i?n$IFgIoN4Rs#AoclI"
    "zU00j`|7Mnl>w1kOP2=TwKl1qgh`BnQtc5{xPXR2tqKiE@kta8pcSB*<o)Grv*ip{z*Wm`z#FR`d1cO+iqclocR_"
    "4NN!Ozy*77U`Cu*7$MR8Njdq>s%NO-UO_YhFdisb7!*l_xzMDpmC6q3nW$HGGS+F$#Ey^lhaEZixY3KEE-O)sNaA"
    "z}V&cP2T9d9~S$dBFDjOBH0GBeG2c1?(0Q}jkXL+?@)<}A;f)gluMo^qTVQe^P@WU&MTCZXJM#F&e)iy~$POe}gi"
    "V9i0!VaJTg`DaqkvKp`!f}caFep_G)U)qwQVYTEdMX9n02^=vkf_qe=+>-Z70e2gVi0r}uytwg8IARJj&AD`8+)6"
    "9D~Ldj(JmTmivfVWz&K@!(_aIimzcMW<8on?k<+wuam7%l-f9r0Vg5yIqHPy2Dq~uD77#RR1<+U{mnoqq8*@N--1"
    "iL~@2iZ?K?`dog{Y8r_hgk3%X5|$)R7Pok>k=DcoU}HTX~1G;l(i$8(=97-{agENb)z-qTuGKUAqy3pRB!ER7TI3"
    "mKB_SaS>YGcRlM8;HJ3gu+Pdw_s(8ga2LK4Mels>o$&qnj6$q{6jf2b3BXjfUuMo09l3suGFk6PLG6OIN=B&3OKR"
    "Im=M4!L;23!hD=*yVe4r^S2GH~n@|1yyNlW%`QpW*K2m48>{))a5H~H-waLOH>LG>9j7ce7i(m&$qv^{?ig_!WnS"
    "C%QyxC3ahB<+FZD@%3RKj7F}`oKzkN7ywm6=eA3l(riD0ne(Swu>woh_%C+bVI>mWSg!i(UWjRh~PH}jcJK$Mb#E"
    "l+g8kIFom}3jhbvY6tp<)V5d>`OBeJ;V1Rh+tzd9HH6bXYG?AGy(ApiIj&KVu$b)91C>o970=2yEZC-I7cxDZIV$"
    "h%<+XZysj}}<Sx~h4tlqQW#OnmOGI*WxkPw1*q(@{PfLvl{Lzyq(P(^dJY!-I8gPZkYPq*(za`na<Qy~N<+gn2%A"
    "fT*7fR^wmK8XVrf-`CZ0nBToDxf%MsZPI|Y6=voF0P1*Q-6%OU1qABHg>?6!y1O40dc~gfqMK+3GZkb4B#gbB#Oi"
    "qpebWNT^&Kwt7$(GS65g5p;~#%KI3xWaHIyw4ol(C$U+W<}S`gUz@^%V{Smak*rUx@8hkTGrL#bFtiiE=HYQ0(qy"
    "1%NVdu{qnH3|&@j=EwbpZTXk5cDJ`T?CPX(3jp3?|H|z%Bd@2iVB&U@-?ig=S5{6GMyP@c+?j+CE8kZ*5A-Nr9dk"
    "Mr6I8ehI-GRkYqHvfq*EjmMwgMSkU<s!y5j)E>bu2)1MnSr2ONoy0>`wud~Ep4=H)sTK2NF^rfl%rJ)4IkC4<o`^"
    "ZY(<|-M)E8D3(`XloGAD3NXBSJOlC5bpX<lHrb1vLW(si39jN3T7OpVL3nIB^O<-wUcXJsX~EDi;Y(`wj!ROoD#I"
    "8=4=#8+mmrO*aP_5@AMH`qBH{$c^bV5d2ic`IRL>ZCPrZc2m#K!-SlgOrC8Ou5pzs4*X0@iDp4jzhQPs8#Z+}I#n"
    "OrOe0%~XcvlM4Npt4nme}$x2M?~hY!K15ag2Bdkrn3L%#rdX>U+_i#)YYQTIXb_|<$m!M4cg8tY_OF@e}2=yq4-q"
    "3D>R)b-K>3?&fURzpzAdIiy&$Juqtq2eVHibvG@9B9l|wR=I;NFo&wQx*MehvYqquh-uCfVxV*_REielM3$x(mHE"
    "93~*EYcjd+9tyhjLSbzCB(9&Y#mJ}NC@Ddpqn{8$7OsQ!ByUj;xWje85n9y~`diWoQ-ya-h2S5Hee08vQHjKl<Pn"
    "lpKd;!kusszwjGNXL!!i>0H0II@ll~F+SV!aB1ZTX8X#U1+rG`yVFh@5%Sd6+x}VKXD2@(HG29C-N@5-J?kGmh`1"
    "fY_1^8DR*~!sb^2xn_b34UIX=>atu+jp^I&Wr_SU=!cA^bqocpLUPb3)a}LwIEVlZN9%{50q(_>Kdmx!T3|H_b*T"
    "nN8@$W;IqD|mC4y*oLq~ZO(VeI%o*apZkAo2D6d`m7+-73Q-hJ=fcXE{8e6H5hX-|9pN@`Xmx>-$fV4#Kg8K8EMn"
    "l#W|3S7J>GVV1W%g^Dv|898?FQNv5H3cdh6f-+7#fF07Y`*7ag%YKvKxC-evLqM?G#SV5MObPsn5rphVZWHRdjn1"
    ")DH@u3YDU8h$O(hhvZG0Qqk*Z<B~h?{h6hZpi`B06GL)Ry?am3k8)1sy?4A8k^Y{ry)e&&XW;Lc?CA|v=p;~Ms;Y"
    "~#~LRF(E6@SHe$>yR?>uskV_RNn~N<6tc!jZ!y;C5S6d*TMd3-jfmU*7{FB{jFC2xWPw7owATx+7MxDji?XybmL+"
    "-l$zqef>kN*@okJBPA=Cq~C(BIYDRiw)$3gd!p3UNPg-aGNG!hj<_oKj($1&0cxrXqGcCY6!%$|?(FKp^4SKRXI%"
    "+TR@1qajA1Wzid}AQjcoeBFsphjY|x9YH7*!nb%H#tmzau?S5T#%V@SF{jtMYX!kauc&3XzKz24H`;7cR$dKYzsq"
    "(Z>>cKcPWg3=O@Wb}a@FJ5U|L)ez^7!W1qNna5ray%8JHBRTKGDb^+1~L<`R9(G^nih$F(c6KHdcm3H!D&Nd+q&*"
    "CV^TIOx*n*%9_~J({X_p{3X2Nsx2zY|8Wz@2$|(luRoTfC$`$c+upCsS4a*VVl;h~htAp3ChbP0MGhL}ATd&8$L`"
    "m99QY283=TB8CyUZ2W9!h<n=^ZM5-X54&+Y~&eo}%h_aXkLHJ2lHP1-IUGU6mgJWcxZ_=)uO2x$>Mr?Vno=uYWZ1"
    "py<jdM%Z;3z<DyxC~L;cjd+SJ)e#8`!*v`J;H-?2+b3Z6_P(tb?cU5uanN0SSeb?c<|rNFFm8#v=x3YQLS=-C!!#"
    "^7VbpxP=Y3;S%b_u(z!Vf_!r-B5HNidLOAk{F^AWVMfmG=QHVJ={JC#CWYS(P!EC4!lIB0N!p(mZyQs`z2nYe|zk"
    "kJu!<(EriFJL@)T3%tTNSlgUfpb&{d#}hA&V*M$%@d&SD)lO=6$6)B!-BdpK*lA&6O-yd(bgFjp_l(@_7n5&NiCa"
    "iVuayn-2U~^%rG1ewp9<Ixgs+}NclA90Fv;oXVBdsV_5=RJRHvuaJ61u!5q-C=S-q;)MjVgk^BdAF+eLIOcm9J6{"
    "Fu_vH|p8;qVRS1^KhpMg(x1E2I`6y7-g#kAHk~I0S3~%&Ch^4~f(hzsGz|SPIz2a43SBUsGTD3@hWM<R5cAP)A-%"
    "`8PRis8GfjKpj7+MkG^?sUYrN(ynK0W6nQ(C<^Q@XR%X7p!O0G1*F_a3E&_`+&(E)60*hcVdF<yM>rDXcYUszgt3"
    "5nwLU;FruccvE|R7&Ma2O{rbVwSO}#tP7VxV~LypZqW6FF6=k6IS?lTW8wti5cFNE%)>}u%!VL1N0yeul0w{9s^!"
    "96w%$)xLmLNIljm%_m%u%~0vFqDJVtzBiu*y^{nD!8|2Kl}WwlRfJ}ODtnb12$wUCZKk^VONzYwI*^Ig;bGzwp~-"
    "ZA9cQp+E+oo2>w%P<ht}fVht>?39<+@wQI&8vYViCEy%5w(lA-g4;ej*IFj!G<;F>a0QZ42ql{@*&H*1Nnjdr1h?"
    "x?vy`m=aU&K|RRg}?~rT|UkECn3XmfI|_(`67TXEr)50?urcxX2s0x>?TG*VxWpcy!;_1XypipC*1aFGs_ii)kSt"
    ";*7d(0eC9<Z^E%asiRZRbHgt+>w+jQO4~=}&hYK^0&-mV<HOM~9{{*}g{gd*;6P2-H*O|n^ug5{Uzp+YMcNL}%L-"
    "|oLJ3Mg=zf@oKb=CRd4ak*v3Vt|!|`gYs5)&y>j;rxi|waIqY0CAo#Gy8EkNjyn$$(*dBUnC8>zzHFh>$iP&`?^a"
    "FjEY%K4Qz8c<oCQLo}l#KjTA7Sb&3HeeBj&gvCsr0d<(g?1GawIaxbar64w*s+!8z)+r#qhm=R<=}kRH;>!w;Bzy"
    "(L)~Dt%%Ou$v`pw{rAAz^jtF1|-%BgQ1qJ2`v|Yo4K6dI<dQRdnb~pCQYQ(dF+&#o10`^2-Y;OyPL(&%Pog5S23v"
    "w}vwcr-7VmN#9_2&^W(A!bBxr9dK%U<?#KK&qxTk4~-^#Ycm1@VA{vSdDOx`r%(b~d(>U~Fq|^pCPf1UuD43v4sV"
    "(VLJS>Anu!@{$c)QpI!3ykM6v3U{MR`qf8WJfTSQbwt4c^WO1$2Cn0q+<aVsEO2#2X%SIomsDTNl7s%&ay>7zZyb"
    "SeC%ASxS;h`9P|~+13Fg8q-3J245;4uNUx@|xm$~uX9u3#LTQ7w?*D%XScXrQjDVg3)KmOV2#c-0ao&##2vd`eJw"
    "J&RPV8C*WW*ylbB_}U&nW2B>(v70dT7$~yXk5q*4?Tp0VL+nlNWeEL$Xi5zho~Epk8PD!{dmYhxhN#ZDdkQ(s1@?"
    "{<28x@vl`tUH1r0gn-idOZ3hwOj8DCAn5OY6|5%g)B8}?LU2Z-bs)in|;h#S_n0+*4Q9@x%b^~>Qz~TcE1$KI?<!"
    "k+fSyjNIMa%7!^1X{~U};ua2h>S%yKO*9f~EC4BUV^VM}0bQif1Rs$7e{PnCCzR0-<7yPlFTi!01y@zhe`pQA<+-"
    "zia*;cecrwu9GasZ_nPmJ<IlgI5>O-UM#AE03`?9o!_8~_?u?!SWY`CbZgs~gjEKdJlh$!1*Aup)omx5-2xy~!3#"
    "U5!tI_XgF%}j)DN^N)X1Q~>5@13Sk?#v!D-A4L$u*~iA_T#j*;4-jFDWi#lFvjSgoRxX801%L(fQv1@)ts-G*@JG"
    "zVX=v@*3EidycN*K{1GN{VI6xWM_koOz#XKFIQ_r0Wgp63PFlJB?rkF<E5b<=|ez)i(R9G`be#50dH#9|?v!cy)<"
    "?W38#}X+0)<Uaa@6Vi%OG0!N>$6$tn<*f*}SZBwkWCy+1^HCPzmB4yO&TzX@@pLbXUx+*Kk(T_}k6OJ8`fxbP0q-"
    "~#YEPh&(x>FK&Fo44GLVL)rU#;Pz4{10W!W0B)S)$jLtcBZpE1zM9Ljg39IeQ%00^btz$2OO3aP6fZ7|iC;$<|B7"
    "`92wIi{hNBipXw@IW(*<eLBX%(5At}9wXi$q=gZcDL26CM=T@WNZ-hkGL;i7c)yyjsm~L%+R0k`FQ4y!+vZ~Ulu^"
    "!16ys}G<)`@d5mTC3mKTxhaPLraKq#-s?dM^I5)@dYCgW5!+^lF5$EyF(m{<$Si}gx)zEbC_d0;QZ+z`t0smL*(V"
    "fcqihJ}%>06BZ5ls1gOM8@1zez7b`nkg;@BzFa$C~hI)5-SD+_hD*Xx){_fUTnO%cZf*qxTRzLk>o~J<#QNN-z=z"
    "v`6lSEPJUoIm|FFY#v{ctCI`%j6mxqXo@|tzF_%RLv#hSGEoQ!<3_ULwi_hWqmfd64SAj*Wmls%0*p;-4L>Oa*DH"
    "xR!X~2ku%F*Xlt(PCMybFuOWV`C5$6Q>0PFD1yzF><rWM(+A;5%`<*c&yr%<#EwHsFKpGM*0ZCK+Y;!=o)S9uE(5"
    "o$X|ml}0OSXT8O<tm;RMZLWl6HERkkY(I<+O+;xE4FMXElYx>^uVYxHqJF@~sT&OgHW`H0?3;O1geqJ8h;`;5>bb"
    "t|{OeeFkzMz7tv6bVk#p(nWWTY{HbkX__V8t!G=5)0VcX322FHrjtgC#J+*1>BBv5HGdj@#|;PBUS{rKe7!O`ByF"
    "X3pf4-SXud5z2%E>E{pY=v^boc=2I(#ip$N;5l(n=#8LsHv`Q)<$vYEpJ!LBKG*Y<Sjmj!~(}h^VQxf8EyzgYk-M"
    "G8$36Ink6uAOE{1_wq+=_aAWjytj1K(IwH5tV8y3}c@20^@>Q%Uz)0wCcIt3BV=!Rw;6ttkZpi%da=nBFM4Wfz;E"
    "~93Wz+sn5FigzGLJ{WbPl_J7fDl_q}5w&`hC*iDHR0D=3VX^x)4B78Ve)nF7vy1;kdH_d@smv+&=uIC1P-8{Ot~I"
    "Cf}&di%tYYqt~RRLlir`p(vpYGpHc0lV8t3#k{2S_ef`>%qJF&9fgeNGTx!_1v)<$2uU#`I|`qS#}j=P0h^{!;bI"
    "LPLlD#QvILt{XXJw*#PV>X|6WFRlr7tw6xHRjyuf{g^tH=N+>BoKJtFD}UW9O;WI~0up~m&hY1~&<6*uaP0vGs6t"
    "i-!^p40L}fd&kiW-WjeLjYIQe;Eh^ag-tzd_6;4y}Y^+h*-!g%9kZt@BqSJEa6W>dN6C^5P2L$l!+K?1yGun#qFF"
    "x4{#3LGmwi(Xr&}crOG3ANv;R1-bNe?4-OHaO<0WwY#DO})r~HbT;U}j29*}K@NL%x*?fU2Xp{)6*HI>1t8J^tox"
    "TT3@2{@wsiv(lH*Qk?B9R~ouc0)@Kp{5YT(wbQYgS_%<3-+%DT23>c>vnsVm(Dy#|qK2rW=rD4RwA~qpT2h!aRsQ"
    "`9gAL7(v?x{c)A*$0Jz-m^Yz-Y7#(OUC5rEESgr;(ePP0y6cyn#*hXQCfcMdNf_#><SruQPf~meZJj3N8Q=dU8rg"
    "||Kxv_!QugIK81z22yD6*=y@oreU}2?#&V3L22S|nF&Rz809vvMVeP5T*)7x&>MmaXtnSNy~j+?mI80X;jxh<GiF"
    "lHELEH0KAx`=u)HRHBb&T=ZNlqQ%E-w^{K88X{A7mzi<jf&1@S*$|wP1!Z6yGu+e`uX7OhvT<rAm|Kx@H}DSOJXN"
    "cY^p=GXd(VY07yeKtL2nf0%Btqz1B+6=N3DaV1*`xmc|nh#|XnPa*&$@a+`a(fdXMfL$nuoIHHe1JCy=`rG<B7_s"
    "K;v{RHQgPtBIzmKFFq4LOawV8NPSVL{P5ZZ>cZDf_^nssZ6|ktQ9DhkOk(z*Js@O-`iBs!g#{a3j*{J@%;*exz@%"
    "!unMNPc|#=+TW4p>9Z;3Ly^1vDy!~tp#=Jt>|#03CsS!|kF*FNoUj%M83c-XDvyEilsKQ)R|LrCYV#_MG@CCk1oR"
    "D$aWb=&h*aF`pl#u??GRQ=CwWdZfSHR5*?K)W6d(}HiGsp+Teo5b2sk{z*V5pv!t4liJV?(stQ)0f8dmEeEKI6Xi"
    ";w3mMjpuAYoP`~UR732L<j1#WcU0Dk(R!bd!fdO5cw`+p8|mDSroh#vf4|Ab=rT4y2bvtF#jlx<Y|WDYgt?yqC^Z"
    "Gv-Cvik!PD#X6H(bB08<J*sSN=Szjp$)58!8ur3YJ%5{c~g;|Vg@x}rrI0we)C^}EN$W>0n(nWr8p*^>~Rwk&bE1"
    "FuSG_MB5OOHei#o*jV?&D2ngM$c6jb-$SIm4Hss%iZliSLxQbWpO~lZCRHxYR5WA6s%U3&xv_#E8!n^c};*3wgkk"
    "99DmYR!S0(T9~8osl3e-@KR5C6H|U1oxl%eh9DKdn&!ASF{}h5ni29d9Qjbno9RLM_MGalU`g}4$YYSuXnXBCN3|"
    "?t3fxD(Ta1vDm%LdsLRl55Mu^z|PkpI!nPh()zCJ!7U{F@X6j*zQoTQxYQ<Jf}<gK+p`pu<o98Tr3o#^B%M^Kvp?"
    "mSi3)hFRTVC9>XmTA~tIbN;<qkt+npk@h?QIV0?1cU;Y$?%LZxXOYw^$iwH12^VWkiEmxV_T5a(ztRVD80?c4Dl>"
    "dO>v#QjO$tjc$q3E1($5>m4KnWDlG(pIxt*5Dtw9;Pta#r$U$k|75J*Ez-yC#<XdhL+1ceB#M$MXY*I;kM)bfz<O"
    "miPDVKBw-cd6{cq2I_Kg3}r!B)lTNwuX1fr`d4m9#QEA4)ds2~0_A*c4k1^!$&9$NPUW|9!o8a5#KLjxl^`qIxM2"
    "{}(0gVpErcFVY$X2Nw=guF1Sg<zbYxC>Tyvb#@Gg&MriCU_i}B`U#3Hg#z11#H7_hwmdWdGFlN9FJkv1kWCfAZ_L"
    ">5Z1MXIQ6$Jl)xI#k<{gaA-H|-V6+XJI>@MOM3D=FS!V7xsZ7a&_=u*EPlh!CfTJ5?%TGprydp|PoOqJnRMkPs?m"
    "@_n(*HTcbDMLIc^Wr5pK1*UkqC3m*&NU#x{?UA&1G=lhb;LARj)9E?L-vpS!|5zvR5$Zg)5B@_!l&6;ZWdGv7FYL"
    "y-Wv8h+V~qOakb!$@N`jWh-A#M!(0r<%vo)~OB2I%S18R><B=ma=q?WK$LzIo3saA5kPKk#Qh1|PCI>{V3^W+5Xy"
    "y}dXzhkwQe;wZ+I<^3VKY577=mBtEQ8_v9-pEvfq`?&i@`ugrR2IGYlP=evwn*lBYg<)3n(F+A2RmA6vnBXrqqZC"
    "=&ci*R6Z1#TZR`E<$~H1a3H87f+96uz_F->nIUvhNLnKF4Y#XGl!z?tz!pr6Xe6E$2;AzL^z&Y}pRZvFIH81g7_s"
    "xA>n|V%Cow;<zCp+sHxaR>0iu;tM-=2cwAwP;La@83;bei(sPSL|Ja8?Jj?J{3sM%qhK>~X;IN;#K<C8s-OD&s--"
    "*N7Sb_&K6C*6^x$w8*0Vyz~}r@}zwTqM$91LTf@$Io{~^b|X~0nby`dqDDNL_0I$pPQ#%e~~^VeH~}gvq7jD=tc_"
    "|T6=>q{hAvZmTxyeLc5nSdsh<0T*rAn9#QqT-vLZ%!L&8<-qrfZug;%*UTqcyZ$)o3f{5m5bl=ZD<4^askN#EckF"
    "N|g?9tQgPsQe9Zp7CCtlV<V9O`sqSnloc6QDzwcO4y{xjjdHebXd<is}-qa`M4fAIil-q?mAXP-aQMlD>}U{?4pO"
    "^J6P5h`m$Rr3egm5jsArd^1$SpBl8vF}Q+wRETr{jP-h1RFy4qGdhM*6Tn1;E*c$bi&f$JBn2fZ$x&UZB-mm*cUP"
    "@$cp|6}?Dm~b672kG>MeUS@~y#!VYipcEegb;Q6`H-A$k!2fz)s(!|uu6!Rhc-Uw7Ff0|7#7*jEK*yM3$VMAz(=u"
    "5?hwC<c;AW4q(^W$hP&l{b)A@xi<_HDc@Z;QK!v93Hk+{re>ec51`|H5ugVaE+p1vL%=6C5g&{gz%uOIf#`$DX9O"
    "-{~F##OaHgW*mz~JeLH}k`MIKe6?3AE8Px;TakMHvty+fD%n={@{K<NC)%~Z)$a<Q+g2ai5LQYj^A{Al`lEVk0<h"
    "0KjhOE%lol0PKi7V)8g=4cq`-uG2h9ymkRiRuzizQ+t;@^vuqq4}Zfu6ChoxqLy)~_R>NZSraRa(^63!x@!BURiz"
    "Zcc4=s?~h4z=++p4F2!M?!n`jgE4u*MeI~|H|C9@yd>7>1?VqmwPNE|Hm>ThPbiRL%X|rm#j!sZV5^S<h{OQTV7{"
    "QX>4ue$nd-)EU_hMZMqwVXHls+G*vL@l4rZG(C?e|(4PL@&lgDDm2}U4FZO<v=O+4$<jW#mzTd@;JI#l5a1`UXFQ"
    "DA#XVwvO_=LEq5^X}3ZG-@=i&~@~ULYMIvmc<m~@0c>QN>SgK;-#|U7-h(2M!ZnPLF6Cvgi$g83w==yEy#*fzYm3"
    "tqmo2ms7TjIez6UP3H>?BKqDSq-mr)rPZ5a&Dr6H*H(hE#VVxh$2W_7wJbrSFAZsHW=wmsba-YFANnHvGVtki~2G"
    "|2-kwX}TTh0NS0ZTK6XR>53g$B3i9KD5!<&Z)K>Ezs}?5>=JW@g$AWDQU1`|<^Lrya?Pj2e*&NpEiS!1C<`Gis;D"
    "Fb63#nQK9yU7}iqjoECm3W-9RxvWZ^QXYSO`b}oyA~VxqwSG0MD_Ns(Otrp*W<Q30T5~G%kZ>bbKSRf%l+t9qEz}"
    "fJX5fJ97SK!<vVRX*p?AcVuj<C*=E-=#?tI`Z$8Ja=wfwP4njcPPGUvdgijenE4lfxW4m783G-~Ip7F(!e-0SsZi"
    ";;6(7%^}Oy>nKeGS?aTPq_#-Z4%|#RdI*hvBJ9U7;7>div=c^hK;d4S%e}1df;YPmC<Gz+<Z2~Vq+nc!VMF+C}+8"
    "}P8R#1C@3&mRw<tsjmCuE5gauvo#xpfOl9REJx<ChH}+Q%W8MV;5ngCbb_C;}{mho2_<3d9>WPIZmYQW+5l<|i(1"
    "|NQ;KW1Lt{@(;zS|GTsw$09jIshYL~r_Hy<Eg`A7%Kc?%$aC%PDTGi;5{?B|w$7$t-Rl8m5*SRA*YqWHQtIVBPh~"
    "XW4YlcxQ3nNF}f#I;IqjWfWJ2rrDH*1F5)P0Lw}x(P*+HC6%I6{if;3{!8L9SVU;gx-6=i3CUDOvpGh98d_2q!%I"
    "P3Ef5zi`^=@9WcB|Y7+>`xVEZiO_gkfpl|cHX)TS9dATUbZtJ-x<c^+ZVZZ&FmF>D{?xKo&RUH_ndr-Dls-TtCbj"
    "hLGj-)vv&v$x&%ZDTT{DecQ^-=_Aj-8asAtAYJ+BYXRXetm;^M{C}<=>2sH(tdTbIj_rnW4k$>-11BU<QP}%NLxN"
    "OPYPRK$><;bI<M8+H?N?Fg;EQ0Y)6G+4(h2;58$+tM5as9#fVBv0S$0jia_w$rOvp#97$`KFVbLrl2QS-5!fW0IY"
    "1sq39FMHCy4<P^0G+-X_qDD>a8lLB3A1Qag1Su4Z-kj<t#yJkNwlk_V^H(0!ip_om-DjjUF(YT+BaV7Jgyx=`A+x"
    "bo4AoQ~;ZuCgnF{P3L2lk52BcYFYy>5SGss$x@>c(sax<c3YxSB?^G;pU|(1Xa4-d@MH+q9DMXG;~4yRvBb85Mjs"
    "m^jZVhwtHf-rPFlE1vKtXD7koIs3dE_wtuBeSp2POKSS1NZe41k&{+*MD8k=j_<HC>`E6N6$ZW<TSY~Y)XA<0?BS"
    "^luctP-r2YcnJjS_B$++8Y}vzVtz~o9yKZasbQ+P~X@jDKcK1>#&Wcb`@zYsW7T=B&eA%uPE~=U>>(D@2ntiQTQn"
    "2pJ+;KC#^MA!tH4WfT4E&M7%xFfGo{VMgJVtrKDKBecSW%yHToEBP`I+B^$$^4u(G`z6)!%n!oIVx*b3MyEr53>w"
    "gswocye+c<gj3aqR2Qmd0)DOK7u|{7ELeASUjWIVJj^te22;Hh4&fIu@rI@cndnCNY))G=Qs>rJz{6Jv?lvz#?{w"
    "ef9n=+dF#IIM%;Crq3Ll<lba`yQp;a)9rjxOh@o@3;t;oCDx*#3li$01L#Kb6?(-<f7yE7Z@0h;$sO1`+{B&{M@C"
    "16ZYYE7Ws*}N>JUEF)Yo)NsU<7cs@?Es@5`ae5?cs?WU`xPHJK)T-762YW;sbqQvb<k(%WK5oO#NTmr?2GAdA1I0"
    "m*^ODs85%L-)v~CAp|kMj{4EQS+dl%4E%RrKBx$OsZuOLTTLVZKJ}nvw02qpsE*>laJ4o;v)yQc~tDYltaOiYF9#"
    "Tnr*ugHgh5wvgM(JSp{GNK}H$Oo3p=>p?zl*3Wkh_<i31uEQEYTxxvlTQuUM(V;KSY);^sKfnp+RBIQ+gj}3BM6&"
    "o<$`|9{;m^8|i!qUP{QmCPD<4XK*E$2#!lrL{Xt3HFWj2rvVK1p?61)^Xg=toj+#|Es>VUc5wo$SwRqgG@15knk)"
    "@sgpwNqM>Ib4Bq?Tq(1pla$@)7M;dRaJ?y}6W91C$XQLBb(H=OR19@Gmj#zL!;#KQaBPl)zySIc$#I@c!2tUeE!N"
    "yQHF?q~roi)$5j0AyL?}RtXQhUt0v_{1(fs=v*GB5v0Jwp|RqlqgYR<+XRlrd`uyfoPMtS~(!H3-SC1TbkXGb`0t"
    "n0(0%R(a}<d<B^Z!>SI8@MIux`3*WIqZM$*FF{w*wk(<*C{`)Ve_N<81tjtpbVbcR=RE_9mNsc6Betj={cbvcrFZ"
    "eDc5JSq=24Di2-_e!3*idBfIEb<2!_mQ?Ietn%ub!Q`q9y-8whU^?<2Ojbv?w^W*F7Uuk~t-Z#_IWYRD<yxQJrkG"
    "8yr>&$E4#MgiGRoFo=rMn4(kgn}0%$UYrpGB+sLRVz;7`a09$Y&N6-dT4+Cu2hx`i5s@W}@1PWwrwBWYd>yB2Fq("
    "Nu{abWI77P7Lb>Dbc=7%1yceb&l4c8l$Zo1B)0e&KP^b~7gPaPARX5|t5O5d#M!t8QE#&jX>6{y-nMv<ty+XQ(vU"
    "wo#q_G6;(xis_@b(GOyJ|9>TQ;{Hi@wl#J~!47uDe^KCLSRbxu@F8#Nz_3X#(nFly%f>9p}NtR|<)+(9?soGdwd3"
    "XMaf2(Wo*v7Ljq<Wa39MZX1xN@l1xWYT7DB3I(ER)UEt30$R$dr#Obt=P)MJts0}=u;uC6fSAu_ay{thyN+o2HV="
    "uNMuR1qBPUcXab)$`u(XY41BM1EVnBrjNL(HtP-T8t>|kQfx2Wj?h1u5PO1zy+V3=qaz@3Bx(`H6x30LjIgu1mi_"
    "DY^n{#8>RI9ry*oJA`O7DcMsEOHKSR<^Bg&RA-28TZlPktdbXfbhh$z_y7MzQdYl!k3=bxAAy`i_9`)gZ%4^oh=b"
    "rM0fm8nj7nceong%$-v4Y<^3!(T#vfFbE#9mx-i|i9JbY7t~`8jwV|@5ePNWC%H-t$#;yhOw0=NRF~^QvgP*o4iB"
    "@_gR^0b8Y}?u=G^1kB2wyvTcb;1qkP$!Io9B=pbj*c0$SiYmns|YWbdfYGH&d7pAtCG(y`vFo>qOjsD%!Ai68(+n"
    "D>%Z6ek&OE1|>ma|*{`T7jUG#<cdjd-84fC6-eO_%PIC_jRKPY0fvdWLAfLh}Z?>ssS2MCTC$Q^ufn-c6La8-hss"
    "s1Z#|>LVhGpfaHKA_8)Zlqs6BZ)Bcf9Ba=$hQcJ?>w752_ehUs}a=Fa?W}QkR*MJPDHnR+$M|m$i*B*rV$eR)tzX"
    "SYPq9G-2HVO<}4Hk8-I$pF0oBxS@LlZOOKB{;qXCEq?OKqeeBzj}D=@QSWEeI`F?Y>0dQmbZ+(XOGRZdGt^CxkSU"
    "xHE1GDJ~LM{NwT256M&R9FS52jm~k(q(hWoj6audpBWDb1G}-1;*YHy@Z@aXoiD7;<#>>{!3iMyyRHaH1xJ8&*`Y"
    "*;wza7u{A-qgtES@!IolF6?>p%--r+07((5~Zf<G!rW#qm2KdjTS=m<>BG=S3`ZS@nT(@A<fskXgyHOZrSHinK{f"
    "UF6x2h8!MVd{nj_a&E*E<)bKZJ|IUR0yV2BRWSfBouHMnbhE1vfk{V;3+34NF*lldtK?Q0tqs6M`vKWC>6c$I70@"
    "7kiHis_9~wHL*fhsfN>@FLjPY23KWE?xGcJq1PEYTWDOv7j|tHUFl;W-OZCC!sL6hM-GPY%RQX+xx3+ZsaiO-#PL"
    "*e=z<Ma7+KqO4{4?jWjVDGs8Uf!Ki}vSG(diT}(1ijeX{->!7x}600Ccs?!BI&Wlk>~<Ew$%Co{S@S082!Q?r-^E"
    "zgfK^>$bj^FdFi;nU2vJHuk>Wat;nvu)^U7&m|pV2S$K_ictAJ_shuqx84%w>`8kDz~<sMq;7~1W5@h_QBFqiq7f"
    "}nK5gkyyi?uQwE8qV78QU0?Fovm3t+*$>=a7I5M2$G62pq2GZV&1%;!V;@(Qyn!<ul`6CstOn$Ija75I~cH^7A9S"
    "LV!YKT>-yjBR-Y@ziFjpgBz+GVywbW7dQtM8c>MkF;498vSC!oX&@M+rS6u(ZEM+yK^H3EbUZ}Pc{`RU>jUOx{@{"
    "@g*UDq(6A>%!-k#ei80J1aMuWX5`I)?cLLw0K3ESU1g3uj5=#?idF4M`Z`L?dl3!r+H<WT%|Dwdp<lFvkAlqPQ-M"
    "hg@EHd}mNjx46_b2_ipS{<WlY3Vr21!T+6%Kg$pJ|3$dN;$JWfe3fqEa^QRYyt@Q$0H8QFE=2`p+HSv;BDTiy#go"
    "WS*Hb`K)T1SQux-kKQyqfNR8+ZSE9pLt||ws{~1H+p+T}Mg#E1K@c@qyYvhwz)dr@vL_Zj2^m+W_W)v`B$XFjdYC"
    "%_#0hjFog_k5H?;@s!ugYvwa>K}Tu*vTq?bU;F+iIf*cj>7B$o3hr^CbH{#k}<rML)C=@_xD@%rTWN2do+Hj2k&C"
    "^aRTRVz4S9i7F|HVUedE=K#%NI#R}vaE>JK%@p#8E|_?3<O)uOe8m)f&dlv=qM_DLQ6J2bOYY}U;)a>U{=5p$Beg"
    "+klqsE{X&W|{ihRw)v@Fr_=3C>YWgg6CHgc_VmP?hiEFvJ8pMJ>cqrJ9LAdk*OXtlrD|S^4-T_vJp__LUnto3h-5"
    "}eIOapof-T$&n1Nlc}1MP{PI+u<sKmTxiI3$gtW7}6ubKrww_t`SoRRVa+XvCPiX*GQeaQ7l0DNDBg66Dv{5CXSX"
    "gBf%8vr)bpSo|qXtR91NMCwy%|M57{d;9ytH)meT8>Sn&F^mkfcklnOcl7=6baXQO&$q)<^Vk=>IU37T3hPtW`-w"
    "2mF8qdbS&mMJCuiBg(b=(Bi7igvKqXZjr1<P~><)Blc(+7Lf>Y7Xe%d=UUzxT3t&@fSznx^rt-6{3WW=?B<0P}t+"
    "f&OaB92jeN6q02rsz^(FkiP-m#){$Fj6^q?KA~^c~;Jr)Pwr81AJ{yRORG;+VmTlm^178YF7bCpO+UdXnMQYxLa|"
    "1?(5g(Q8pZy6&qv1%_c4D`q9*o`SzUqfDUN6T4&8Z%f#<}tMy?qSq@zAYn1DV6d7VIvHOVeL4EfTgs<Q2gOPNC33"
    "=}$PtuUs2ATZQ`HNvLUmu@fzr>@xABV44-E+-sLeGm73t(+GdHxyxhCB!YVA=ze87ZRNdvjpq&-_EsT8W^jQ4E1&"
    "W>KP*my_auYeCA%ge1F>y31jyfku+F))PEiq2bJZsQ{uppONhVFaxmM;2~@9aBTHIxcoa*(jH;IagwYa=z-dNNR@"
    "y#GMlS~a2Do@)&5PLF6|j{C1pfb5(t0<PY9~OF0)2~usgdd<_&3>q?jwaNW1kxLvL2f=>*X}k#HJmh8vtcCkNFT>"
    "Udk=xp0$1`o~?1R6d`Lht+=@{)9TY5Z{i6`Ghf_!h?)wh)RR$1b|)$dxzJ%gv_kM{chYbO?ylL`sjV~Tr*wjC5;3"
    "2x#bAvjbQl<8<SqE2})ex5FW=uW(etrJcHZ;)D3Dbjbqo4VZfx;a6DyIeFvmk>qZBp+~*vS>lvlZRUSJR#w3hD7<"
    "!VK6HGTcv8-ZwOh1r9_|x#@;Po$%GLkfPBE>Rzn<$v+G268uvcWL$xiTVg1Obj!bj_$^12;GNMK3DQB^bo-?BY48"
    "iht61qX)_Ik)N>{0FUe%CGZZs*E5N&VQW$XY?9tAYkC>84yI*qEIv-4Ljg=+goYPQ{k@VwV#Ao{$ch;)^38OfPXe"
    "a<ImN#mHGuxosDGj!HL`kA-Az#vre+z*Cxm$W*}K~8Xjy&KvU+Zd%%sRWK^Ls60(u_7TJX=x0=%zr1%h#_Rye*Zw"
    "0G~5mSEs}{VC0S*~Ji0NWB}Oc4L~{5PmUr!#4Pazox~|Am(+i2JhS^L`xSgRA^-n><^)j1N}Dx@c!7Xj7D!i*hv3"
    "v4OhLVWWJ_ExVJZT25aP=;1%lF#6S1(?V2$fY}<#Lx6RZVQ*AB!3sklV+!Gv7khQP>gy<OHr*ui`gl|PM-RK%nA>"
    "CwIL%^URcX$gU@<_Gj`pZV2<BMIa=tr5}Zl8N)H3vH{UnQU1VvfUMQs=v4@kM6Yf0v7vcl71Jb#Un~SJZhd5oxhb"
    ";6XOzf7VbCup#yKU4RyM*tA{vWXQn=^l?s-)X)_%A-P+`OU*pE7F+IasLhVtlJbI8tus>oA9QxwarTfrXLRbpyU3"
    "^kw*YD(6mrOd@!r>-pmH^W{-}c&RM4$gh0egsx?SZi-RxYhdjl^=qaw3oJ%~~+L~+<@)gGlB1&Wf=Np_(e^-880_"
    "2?Ed3RID8^|9Ijad8K2QP$8>vzTotKzooZjpeB@j8;NyiWt-qR_lhf5ztgb>tT-JTH(2+sM?yZjbyX~*YgJ3RjBM"
    "Fpq+`d%Tak*#|d6+AASdRx4Yu8137-74_RD;6nbQxgQJa}Sz6ZmnP*>x)9hr5aT%AtcJRb*%PBtX?X2Pa2`NE1oA"
    "qt$Wu&tsi3oMHYlm6QSNRmnnTlDfM%_;p7^S?@Y{W%wY3tWcyT2akp5_b*N@W7KCbnU;J{aqE%v1hN&y%$WUMEAJ"
    "CDp(puA%d&k2?fNB;})+3W(09F1&S8+|DukPnoY51+*@A6&CrepwUCp5cKe(^r`E$*_)!m2H?C375BKBP8-wdaH;"
    "$8DuE;8edP8sB4oBPm#{e24~kS2T*hMvmH?*0DSuTz${*UvbKQ#{^}RqYL29F(@rWTI*Mjc>?KqL~Lf4~UPU_Y2r"
    "Pl4((sC_58TP|By=%K4p1pF}XZOCpW`BG>dz2r3E6-3H^L4q$@vP1tt$o<fs>mUIglT_nxL4Q=_LAG5S#D&W^sLE"
    "jkAEcxyGBv>o#5J`Ej@Q8-+9>U4ls-BW++D!>nOxIs=VsuEn$9fvt^rmsapC5$(IzBvuN`$bLG&1o(zV)A@nxnjW"
    "jZ<E#Ve@+ThXf%sIM{JN;-)iYAZ(yyNgcVd@*r^Xx&v3hw<y+t`b~)W!cEl<dU-Cz#pgxv@CC%YB;#9SU{q^CuiD"
    "%nnWo!RYuzG^IiI>{;9V{c3oU{qYx=rTOvI@N_>rJoxe8EPEN}im5G0q=}hzY{lpJr`X%_F`t$bP&H9GrlcnNSWI"
    "jJ?ZhmZLbVQ9K$JHd#<d@`&9`&R^SrcKfAY-nYn!S3o9(IHn}2)Q&am3~7uprb7Oz%c`~2yR5xK`a(qfs2p8pp*b"
    "AM&0r&%>io+9(#<mO26R7xSy2PYe%yBHOtS>comB_`iM>kSY;i(-j-v#8UQn~jan-PK-pic(6{W`K6meahX0bkkl"
    "}9YD>H#1xno6x$BcR621i5XEGH0IVQkXV_)|yM{2RxdV8CZ$Nc{8=&9#p7Nu73FKntfBuAKk0lLHK#{Y*STqE__J"
    "Kg%3+^!;H9IofYi9PHx&<p}F{}?)nk4a;WFzYXqwBhMVP_9vV?hpbko+2(B8Zj;-pVREBE9PZv){00>q#3jL~Efd"
    "d*-yQlQrb5z64ph(E+BVR%sy2D?Qg)1GB6>e~EL)DxXtO6$eFVgyjcYoZ`kjDONdj<>1Z(T(avcKd41^sZz)u2&k"
    "4bRQw%jwq7|E9%DKj*K<@$msspOZsI`W1{ziNDApoX1t;F64Ab_P7RU5b#W9W5EwtJ8maSxfg$d=w8rYb_U#pr3p"
    ";$o<cwH_Y$|%2MjI>~KW<V@9Jvzu$qi=y~Fwc*P>s8|nYBNdKEoX+;Eu}L!jgANE*Wfd+4o=Swj`q)j9_du_z>wG"
    "}@%&H`9Pk+4y3g*62gww168^p3W189sB1A}{Zl8IZz2SD)>7U6Y1Vhc3@Sqnc(&pWUAhZ#6U8!+%NHtVw4!DPE(}"
    "&azoWxpLF;L}-+EMxKq`0Lyns^nBMHPW+I37saA7Xhp7bOxzkTD|7PBM2D;el-t&FWuu8Qe#u4^g5L3RqZYXu^z5"
    "A|~9_{DyjZ>!ecXZ-Fh%pw<hzfm3gb4SLtGf($xHLJAj@WCNmNFFU&f--?+GG#1hIkyPbRo@#6n0ugZfO0t`IDew"
    "~Xby&;klNSdaD-e5~811!dTUc_7a<bCV(dT8n0?V^3UYFTV=9d(Tw<sJ?pE<vnbG@_lPs{m*{3+k*mTMiILOYQ*l"
    "+|37Pca)YOu^8S#T69K17>(JFoQQWEXAsf%J!d!i0}b8AAlnOHC=+jle+=?P|Xb6Ym_uBjm8Jm?3Nd$nb2}WyyOx"
    "=5eYm5WtM952-2^(MVKONQ8mwI>)Q)#9j|mnJSr=!aOb2)E>psJnH_LMg5}H>(#cIlc|Y*$5HzR44%%2iIH$&%7I"
    "Mg_?)e4O{u@2E@b~dKb<?Y!fBWLwf9$^ar>^<m>d#X%YL{283&;$#a$Pf6R~D{!JNZ=^FYvGwzx5e1vD~cXhXvc)"
    "_^c4_K(ktSV-1H5oUQzLKMCZ+7qxjHrvoZ{h1KHftU?77zq*{&yumQJS%KLmgNG(4@$&8;zdbr@ebdhNPP0p?;6v"
    ">>ojgQqj<XVn52(3Dt{6(ZT(vkp-^rf+KYnrUvvw`$bPJkv!jShp%llyyz2~DemZZtbds5C;ExR^mCogdu|22D&("
    "3|vb02E&fW)h2FeVdlBVVVBJm8YK#qp=DTm}>%q(J>av$-z&?{=$7Z`(c<J4qtsgJn=Cw2z8|T;57#{W6I3jfFY!"
    "XhObCK5!Az5G@)8Flpt^}>t|ALcM9;_KZu10Rok38&Sr>gLum1`qrPQfKx0P0j*fRO`1+nIckoL+MQntuSTzu8RK"
    "HH>rifGy=Q;J0w0-E=6XQ@9s`+{eo&u$FVcX*>Dtmz<^iL?Pr|a8UWr0K-y!C&a9v`8gT-{+8C8LL!nX)rV3o$}<"
    "fEIV4!NX)63>=P*P7Y98Cgn=NO<42Fr|>kyi#6Ve1PWANIKyJFBa+LOM_QgZ9Wj7FS<mQBl&z#TNf9OoC_c=9h|P"
    "R13dY(p>RdjfKGCcBeA+D0zQDZ~C9ZIL2qaW#sL>$d0;3`jcUxV1?4f&H)%_Kg-AjWkOdzx-z-NE5=GwCsc-`91?"
    "(3p?d&+2yx|SoP7xb?4kZ?+Xj{BPBIz=OPfyW@EEf}BCojjuc!t;X>c144c_wXI!=|Rgi>Bw?#n+aC5&gF`rC_W)"
    "n#1`;|^CxFXE?^HoW$EJhXf4ec8?dZ0W`191!;0?mVSA?5oKKmz*z&fow#ryY_}PEueMhY}-(cSUjIKU=fB!eJ=u"
    "JI+c3ADR8x2@0M^U;V@oU0`ulxR=ZMFfs$ff@)2tfLC!99GO*l@9)FJIHw<tMKlBlQY;=sMd}1^nos+K(#541X%k"
    "yg&?AF2vH$(9aAnIKKKB)lKJKw3<jVGDaR7TdSwWCvrqc6!G5JL5(?VF&%>hCnF)cWYs|jPH^0c4J^&7crf(x*?u"
    "3aWO%sC6HIuxUYFGkg*SM1n4^cDLc^E|HlNpyviC^Im7HX+QQE>h1-&GD*?+7j*XWm6U*2$0FE^BP4sQUxvZg$B?"
    "!5?l&jXa)bM)$GW?=MCNz?Fhr8>A0Tz3Z#JK?ym7Y!PT3N}fJpZlq0_rb3ST&(Tg=qG??h&@ZkW@VmJL1BgeOhWa"
    "W<KsWoHRFb!b4?_qBlk32_7lh;>Iqn}jM~mI^rZz&5`F4|u;EH>EfZk@1Hi0E=?T}40M6*R*LyxT3vi7KM^Lo+MP"
    "<}h06_)RT%hR~yb+ses)pl5bqOJ_01}B;cv1ph*&O^;^CU<v=%?o0h<OGZ4l2A;f{~S10d6n(1X76ONI|Y+#uaGL"
    "`D}AXP@f1XOO0)NVYQX{+5w`4j{d)SiTN*P_8q+yv9S$H0Z;ZyW4)PIwc3xz-je!nl%sO)0G`0U{~k}Sux!pi%9<"
    "J*0q&NUwp0@K6XBhLRMwP6r?1o4gXsK;eN>AhU?vSPTcB~!g4XA|Cgm)!yOL1niz=LOEz(xf_EZp_OArBjvrQ9Pr"
    "?NNUx@T@`6ON5dtKm4SvX{nMv>;0lRG)#97}F1A02`KumjvX*fQ&s2#^FFZ!nK#X6X-F5n4x~Ge?Cm1P9<7<c3B)"
    "R#t+lFDShJmFE~%M$e<H3Vo9?N@R{D&2x9juDWnfppy+|)3y2(BDC8#Ww_T7*7!|c9nUmE(KbdpSvgsJ?mLe&rrj"
    "%Dcz=33cm~}Zjc{|Kb4!-~4EK1*WgFD<oa_Z-pMG7l#O=Iw`K`e^oQMq#NJ`G}^{eI%cTS)o~i8T!6Q1Gso9hj31"
    "VObD9eLc6AJy2IChR7*bH05#Zu(<Znb`{9(cW$_Edm4vNvgXM*Bl@?x{SUqDWY``4*Kq&s+3=K~@ZlpYU-BEDxiS"
    "7;y%N>7iSOl14cehd5jn8}uxX9_g0flxGGbKAc9~a`_y;u!ihBDKff`r@x}F#fV_A|e$>DB7_x0wWdXpHvqeXr$2"
    "3f;X3A@nti0pJ#EV4g{3JeDsspJ+=`j=JDmT+?LG+%=gk6Axr)91l7q&|&OfuO~7K3f&O0#|(yA;Rgw*LaS}V|hF"
    "G`yR}%ls42e6NbJR)f`o8g0}avCNVS0ot)eJL+InCUKv-m;jnZQ0Knp^NyTOk-~)9izR(ENA@^CJ4*KEYARQ0D4g"
    "O6rgZ+i@eE)WSDKCE%P^;pEs-3Vvfn~7$l*rGlb3e+Oi}Mk+MD_yQ<R1Ze$&i>eB)^LFzmL_ENP9N1lq|~a<q0K}"
    "5^Y*(&_96)^ujA<Iol6jPsE)vHYglSV|>>7Ta}R7%E7;q=LDK3T4?B9)@w!~@H9rtgI7k%V^}m`S&U*hH0llnH=A"
    "F~CmT#6;D&!hbQc8`Q%tb`NZmj#H}yFWShrxWXr91c0ra2pO~VN%mr#RJpE8b4$$0WMQOjcSh}&$6Xlciw_}#%;r"
    "V2lva(6@cR_NhgP>D!(Q{>at&4x|8l?nhsXL|C5pydTgy^2+fkROCKl~S?V&l;h90&JiJOu|lhKkhLVx+KJND3Jy"
    "(NR0N9BcPW)=mLL6&)9mmRjVzu>zC8|wCzTJxJz}P{8TUmW|yoyw?lbb^s~>;I@z-x`UBjX+V{=e!0e`j+)63E*j"
    "UG?y8`l>+g=6f!~<%?LlHsj;7JEYVZlD6VyqEbSsb(MY(zw5dO&Fwq_Au~Gba+tgX8DiPj7}N<UK5=fFK6V>hjAQ"
    "<u}r$pxP<MxMF^4ta!p{NwDX_IGN<DJC8nfE!m8%*(C^js=h)Uiqh4gLk!9RYT^LtSezZEb>F9;oSN6zeoPPu##V"
    "z~?bfouw-kQ19JO^~C^zd)K{FDC@BZ=8*~!5l-$E*Mc7o|i`eBu*BwP?vlx$^O)dlf~zY)N?D#HbhRu6_*^=SUsx"
    ";or)0dCJdPZH%Gy7K}x&&!p!E*Ep@K3D@E$GvDItI{oiZHVM|1|T<iFZ-FRcj2i{P~aFQ{u{nx_5hgX<q{(BdORu"
    "|0E~IisnIWnXv;>c23to}6|+nGszlGZ(O5tTQ#OVEU?cVa^wuU5u$?0Pz9pj*wH9<$a&jT6To~*vS02d^ts-FtaR"
    "<mO(81YhcKq`Z8LxayeOElb+?P1A{wTw`*2sMWy2N~48ABa=ZMu|Jlu?zjD=NghFZ=_f>NvPHMXK<^9I#0d!10HW"
    "fPuF5tE7*6_?%zKNn2kO+~nt>UG==O?!c3_jc|_}$+rEfPNQ0g&aI9k2Sym?^Q6KnAqBfnd^J2g_-S|o{Y72e3%q"
    "4>bF^P$5F#9=oP9Khw7iy5;KFlTADmKaA~*~EKs=yFAsKam&R`o$rQ|Y@R&zNAR#7IiSD}|$iFB9|#9G~&Fkm@9I"
    "2oxd^_r9vO4OUJ%Go;l5@-Tds&a<;l5&}Pz1|p|4-+bxCD5=-Zr+7(2WKb80BU{~4hbeL5GM56_L#Cd)R>`YUW0F"
    "N4sqMUGU}E|-q!3kpA_M}hOu3)4g0aZG&#P&J{VA@=3XVUz&=^4x*^g3F}pzZ74(Y7Gm4>03$l~AcY@8Zjn8#6xU"
    "UVqm~lDz9ayI3MU7r-KJLzB6O|JWC54-v#G=MM_3<AkNT8$XT>*Xc=2I7iB=IiN6Wrr?rbub1AJ(atKu{R2qX;s|"
    "?NCKPlFDWB^~07f#{qm{UzL}>n!C1bt8kGq0x((57u?i_+bFUQ(;T^C=IPX8a#Gt4N}ettj%>e=Q&ge&)N8DB!3Y"
    "J|S`9)MTwiZn&3aD7sK?aYnzyX=veU!1V1f)gvR;*rNO};lR=)|BT}Iom3W<;^{Yj6~U=SKBfzxn{>Bdv=*}5=Nb"
    "ezH`7=uy|bto4bA5DR+s)~F!dPEOdK{a(oA8=k<D<Vx>1B(IO*%Q*Ro1UG32Ya%!vIP0J4{3On)Rm$^>IKu|)ut8"
    "cIu>BQDTb|`Y~bHSb<(L_5H_A)B|)_78G{RQ_(0WPzf+W$x4UUrX6>aX<YNmPBrU{6ffEtl5RaL&Z|TiV1rVyJ80"
    "@!Qx*SPyv9!4u1)Vf%3LJt2b>BxWtMqksdFGMaELZ$$-gFx!t*RB^96Ho4RX~QhuUA%(H_)kV(5M?xGUAD29E8h&"
    "u_^XKd`&_31L*C!>lG<IIGr7_`%1M#??(fZhdlr@*B5Q@>6T}EPFl;p$tiYG1aLTrj874m_E@$Y{W5`Lg(~kZslr"
    "ldg1ki7_EwemG6FuXf7;i(BCtp(-K1|dqQ`c?aBdgF&@nbeCOx~@8oL-Kfp_XcOJAksoWkYN4xQZ@x>1ao8wzBSs"
    "4u{Mztc_(uH>6rIH)vJN`gcsoK0WFJ!*UZxmi-v^Fq67T-VLU<W;z7^yuQiug~O#!EXmy`NGO>>({p{@R)cfA4?9"
    "#?;P?>1nlxuV`jrY&|P6wT3bo>HNtqc9JNSm3T@x9P8*o^t7B(-(w`F$T5SJ&ZqNv9O@o&SxK`x+EmwT-V;ckOeC"
    "^2wc85z%#Zh9{L5zg&5BkSHg=^KC{R6%iU2adf5SJF9qK2$O?-gbQn)?zOu&t0tq`|#M%o3dt^=K93vl``IlUiB1"
    "Zr~gk&8ODmz9r|AGv9(#5TF(@mVm}9bTO(Q=F0~)N~L20nONI22cV@lX7?}4MJ_e=J1PfOMPibSXtkHUDyGJiA`="
    "izIx3CRBiU_qxkZAsFKk?szo!dYTK4Q;B5M`6;sfj%=XesS`fegnqb2!n@`Pc|fG+Gpmy|auD4-*=!WZVYt8#TyF"
    "2d7HCZjwJEUXu1Cy_W%K=q%)7Lj$RI>AwUoOxogLw0GGn&^;P%Ng&zj;3D%tE9W$B*C#$P$=>_JId8vji&_eY0_}"
    "2m9?L@^)9`KB$^ayJW4;@VgOmvyk(Q6+QDdms0oh>E_s3<S%L1(g(7iA#<OZ?wUJaf4#AT?K^~}5KtV%}P&1|{^O"
    "DR#aABO+3U1|^p7f};Oa`0sQOcihJ#xI!Zw3uaBt4*YLYJ!!>+LkEH)6h}ne>Be=txhi<GJY1twWe?)Q2uMlz!6B"
    "04e1iW-BAg?A~ni9-t*Y-|q@sCPVeAVl^qQ^7VApa)-w?Pk7(%WbfX$dj#gfDnyhiIl=A@3<b?F7a9V3=e(L=mX}"
    "~Kf`kG7W~U6OYL0Ead!KfkxMv@)v>eU-RN)}=_}OQf#{IMHanRslL2q#>wnl<cD{|=Vy`Ftl2VK-ioEx6oIK)maJ"
    "F{94hJ^lUhO!iesf}V_4z9YDh8UztzI>nDDjN0+B2apd^rqOVQLeshTGH2;^`!Fb{mse2iZ`>o6)OSybCy-L#ZUI"
    "&jgqvawXx8aQ^ZH&7bCBd45f5hQew-V)|yAjR)(rLl*;Tpo$Dc1lv_G5glbwO(tvM@W!J^KL^*^Y*v#zcB?W(i)G"
    "2mDp#>PQHq0>^FjYka=QjfPkU8STl(A|W)CH%2kB4Vf#Yk@E9MsPt(S9!eiH{9Vu3s~=9Zt^H(<7xKx)frU%#T2i"
    "p;7?G+kgm$RgBOv#?FkU?2kvCCC`tgky6BiyDcLmahj<9C`k_iEzqKQq@eX`p#+}GJKKTD>y6^SCCxl>O1}p0#B{"
    "EFT5JmgP@0!GiAlpGO3{ie=az^+r9KKE5kp|V<SIu6&#)+9SKxre%>S<|9jPGGFE2@z745`wJ*7xACm;jds(0O&@"
    "2!2}DN|q4Q&s8#+DUkwfhsX;J-peZ{h*7@K)G=myGeSBP&ZzE??#1v_OQ;4)No#9%G+ht>EF9HpMP9G$m5gjWccQ"
    "AZ+}RwtlUm`7A{FhzuQzzV@Ca$s*#G?KW%9P_yv8Ce3iYn&(V{plaXyGq$wwZ4!6!d<q^w$lS3H1UdEnWiOS&thJ"
    "rHC$L^5`a>y;E;UzWrg;CRc0Z8cRe9yZoE-KaWFIQN)Tu-IL(4W_k$HyQWE_NX`rcy1Y%1)_TbF`W(gfPs5?&~uR"
    "o=CqeO%1iBF3sGox<^k7uOy8iA)#a&{}DH>wY`bWopFV<eD6U15nPuA7}zLIK$`Y5Y;!vOWu1tSd9eoWpJ9t!V2l"
    "H*3ZEnhc6$TaFJwXtvWa~b@t??o_@BFSAn(Z9f)*LP=RVFIKKru!c1-GYQBykolBk>JBz#BS<?LeqNigkrmx6vbK"
    "N@S#2wjbTXv?stx!FlO1b&B%;vpH>$aOu;BEBm?w(;J%JBpyjm4`QP0Syc^zhDjz1Ug9gX(Ao(F>mN;2kbztpd0<"
    "YhaJ(_9Sv8UwGF+-xrW9gsCzAUi5&H40dQ1)_vq;Su`R8GAj5iw0ca4w6N(j9D?!c39Q0R57i3!3oD>#r!(KY}R0"
    "moAmiY=FhNHg2MX-}wmXc`EEhCNg$R)%Kphqv3SFjqdOf!YXE2Q9x8u2k*uY@g2<w1VB74wm0zZ&hiX+3;J=~)VR"
    "?n-#>ecNd-|5&8Ya$o4TgX!M2&|iOHeLF4fV8)$Dx$Kc1$=x;jzWJm@9|glhUC)h@SVQj+Cot50jWv`5ud)Zf?z+"
    "jqYRznM`S$gKTNCgEZp|8wbzc$jZ@HuaV^9tszp3zp?ZMw@$Gi#O`)i)EUDBdESjz^ZrxuK&Q;+K4%?coc9yu)n;"
    "dryYn3k93ZTT%1Ei#m~L$-(5;xw-qJC8hah(KZs<)d$Pp-*r_VdlYH;nOg18$~F`)!G=2AIr)ZON-6;S>?gP&M}m"
    "O5NZlZMc}sQlYE0|8pSonLijBRTfA77A3fmWn_{}K`E=#1OCLo|2Ji*k=KxB5D?vkCVqk&`h<s>f^{pl3i{A=zlb"
    "QE*zMM><Lo*_|KpLk^d0Adx1FlHf)VQgUgGTB*%Dd63__W%&-Ox^WC=bUOF$N5V4&Olnl4JPyw&N)?Klk^lTuqC6"
    "qeBOS^Z=K7HUSX(%%xI)cKnn74fu`sfI%6+a-{n7m_>U+75DfGbC2OAPpakRbL+qyp#$^zVr~w_#*m}o2~XspK=e"
    "*5WC9+7iF9vs=!C+a5h{(g@NDNZ^u>=xS8M3FGa3P<5c;W6Whl|c-W5!uS1gxMbjMGyhE#JeazT4<(Dcf8U3Rh)b"
    "V&%b3B3RK?b-hEkHgW~$==cF!P&v_(J9Bg{U-r!U;jcua9V56J^JS4_|5U@@Krzi9Jo!-4t^R2zSRA_qy6FG;qaA"
    "sq7skvbtaK_{ior{!RucRj=t~I-0;W4<NZGkU)5cHy?1a}f7Q;7Z%9tjPN9C5;xF#hUdM%b)ExZ}OwN#RdDwPzQj"
    ">t;F&oO*C<%HIsv=sEzcig#NS#+Fd#}&TjO-65!@XC(IKosf^q#}p^mBWsrw893!F=scvLssvlV`noygfPsdV0ig"
    "{HXs`KOGEze$-(2r1zylMee5kANHWwc62iQ&$q+Vvt7oG9!V{x-RG0z!{KP}?b#2<CkJQ0@HP_*k>(p}cj1CL{Rc"
    "<;2XFQc;XFJsGRp8r5iw+!2}BqC`x<b}M#U#gi~!Zmxl3j0IO>mkX09hV<YJoheWbCm6*^lL*Gts231$*qqwIkT2"
    "0MN;JlQ)trr|*B(=(_Ij4TMR%w;ApG(0eH*<iraH+v^1%mUPa42D?uO~^S8_^aagVDDt-xVL+9J|pEXbUA~wxzGH"
    "a6!xV02S`_>xNt?XzsK)j7|*-cV53V_%m8pP0l48aJbj-*iS;ca)_kUSB?^h}ZZ<|=-?Kv1Xj(`N)Bub;=NJ&*P&"
    "x=K#FAQu0g7!Z)t8%~4<3|MJTuD12#P6<R389(&wO4LgisF8+}*&RFdb++HeF8&1`VbU^C!`E`xC|!IkMRg#IgC5"
    "g?Yim|6Mx)@dw@y!A2fr3877?TJ)L@H9l(FEtmJmrt?UT*k|zua{4%ANmA0mXMXoRXyTvcg|#~`<Deo%o*bjc-5K"
    "4vi|C%j6KuONhNXt6aZx>F>uVASgKd8cd!B(QF;&W3hS<1MEU6$rf4JRB$&@dSX#gA?cK@A_bbBwqk>`^Ci1s`Xy"
    "1&tWBXs;1?lm?B;Em?edIp-O2BOTw{u@)msGH%}-e6LTApm1bnmUx{i-N+U<F6|Lp4dM;c-VGtMRRPzy!AP>ha_2"
    "B6|&P7Qr-v`A3<_Q3@HnSDJ4EP)Pc}W9?j7d?8^7`B?&pG3Ssf&HBhFQXv5AX(Dw*-#BTX>-3+idx!AVru^hnflW"
    "JMWL%9H4JSidpLvoQXm#L#}Pqp)O-{u>mVax~;wjY{aiG8JP6F!rlqyEH3yG11~yug~}{UeUAa-f&kg$wOxKG4a;"
    "S7y&}J~?Vj=LDHAmBr66`CcIq17ru3#m+v?Kcos2zx4Fl;K&R}&3zJ1tXf08WOgx~V-9?j+}334vtCg>AC1acxf+"
    "dpyI<6fWpQnEhvlZ1?XQ>Bd`Stb7*t?aQa;HS*k}Mdfx=nZpXNqeKmy)37W${qG4LfOznypQ0>O9anFAvxr_=Hp6"
    "h@i))&VYQnmhzediRIn!|b#0$L^2vLh`ft*Uk?Ec4}S%fh-Iwz&ubI=h$4>JJ`3s?>r*p!J)>=1D*2UZh-UIo0H?"
    "84qgpUPIXN{YSEQVWGJ3T0v~fYs!f78e?t2JH~D*@Z-E8IJM>EH8*mlz4sSixE%WI#zs=#6x~0OKm8D_SjFGHU3%"
    "Z6lp_Te}=22E-A7pmfP-B4+JUxYOivxtaa=5oM>N#hJ`V6nAw>U(zzd*1j5PJ4_V^b7{&xGI6vzE=u%MWnjA#Ba4"
    "tt;4x?OLahM<*i+=wPYcr%pzjiAoA>+7@ku$#grb!#=f|&FO9I+GP~5f?l>qysa|R2RIwRU#f1*6N58?(tVh}lYh"
    "lXjr=jM>^}iljsIEQtXJjK{kgs{lfx1RdKEO?MebWzwrPLrQ11u66I}e$@<Q%<WB%kTtIY!Q-`ROO+jKHR$*cM0e"
    "ELvM4gdG=b^<N)=zkY8TqCnrBqhwy7sb#ogJW{&XRGyMS`bs|^?K|SFFut(F%xs@N<&xwgQtWpRjY|nlkhZVgUkg"
    "H%<pD~@$Wco`k96?S7|i5{_mjD7R%Mfg%@mGArVGk$^&mdMF(&?_vhy``?q=H{rQs~m>$bkd)F00^4rfB`9(Q3W|"
    "*xh%0K4i6pL4~i}{?}5izt;{I#Ie84V3r4sJIWUjsP3zIrvyuagVH<*Ef1*QTB)t)u?RXosgqmD%=-`KQz!=JE9<"
    "93x261f1gJP4&;aR#NEIO5L)C+_C0oEp~0{HnZ{<#sErPvW1>Z(;nFqb(;qy;cEhpy9s`2UddKQ6uOmi4vg|i>Et"
    "J5)AfVT>GQeg7}x^Nj{Ak2O89cwB=WE&2npWn-_%48bVp1O@hCg(y1lu6_vMxys6cM5rG|K{Mye3;VeZ0uEirPxX"
    "hTnplockhy#A<aADM;TP4re4vyWOs;~Ghn2Q99@99^Ljuo=K@593V3k1k2d=27s+Q>$+Ma;O&Nh0O2Nt+)A<tnkz"
    "#uAtm)2G(`r&{IoA`(TQ5H7~t7{BE9x#&=pI*_v4KYl+;HG!d&SiX?+%P~zX=A%h4ueKI9!2!~fq!GVQ1QIr%Dz*"
    "zJ%7wd958I_idq)ivIhnQoqQtOdjIOrl@R)tC>>0r#->BJtH@Y35sNTZ(4=O0GvMJrelk+JfSr{Iw;)WduN^`P=g"
    "+~gGsv=#_$b~RZ6hhxK<`lBw3URC5vGvw09@z%fn%ip~_Kfmj~Z+|vdsQq3G#%SNS{!K1Hd;(t4mXbAhpwT@-p2m"
    "?mgynKhDN5e}DO7GE{@Lt{Z36$dKVNJzb^tG?<z)$(BFYJD)zgpp65CK$u0-E#4b_)9EkL@D6D`iG9#88X{O}$#2"
    "e1)hIm7>AMXmhc?pD^2SrTB-;ofz!ZwzOuJTj=$^g#5v$N5Q?g;O9s^!CO?;;bgQD`7Oz_j+${iNV4D?Kq`!0FQS"
    "_Gc@*ydzZ_$v`MJOKJs3K?G*+}EAN3T%(r*m@l5$6-**yyBnHUb!Yj1QBa+j|h=V(T1e3p)w}p9X@bX1iqJSn#__"
    "DSzCv*(9j!%cM79IUrXEfsQ(*mGY+W@#ms`S@cb|_ZEf3<y+&L2#5<p_p#SKRpA+k!@dU({Wsr^_w$mw(yJMqM_4"
    "@#S_Le#D|u*>$sN<^-fzbH{P}H0R|TzTy93vG<Hv7yrbzw*E<5)AD=5=}G_vi>l`gh~2ylVA}9Z?uFSwnIZxK#oh"
    "qrFWf&oppX`1GA*Hk+Z`?LglSZ%4@L%O0uXkYjB7p0vk;x7RdEes95FgbJ6q4}Vx+tZ<(2GJFQL#8@DM_+(LI3{{"
    "D{>>%y+<B$whksJfA!6$iO~ci1DZDhoK#*dJ4V!<f^zR9J1o1H1Z4~SnB*Z(XasIAbk*X?MSEoee)}tSrXAftvZ`"
    "~OLi0_y*P~H?13i1eu2>swg-6ZTH$&-)1*Tb?takKRgi<s#s?cd$<gdhJed94AB(;wIRahc$LWt~9&F&S0I8dZZw"
    "9#u`M(E)lR=aolCH@>^q2p*HE<{`6o(1Q6@ozn^C}i$Rj>XQ|K+HUCufdVc;5K$x>;MZ>_IcPPc_dzb(>7&-s9P$"
    "OU3v7>U~tKMCIyatvgKj=nyi2;oOL_M+ZSSYogmM)1kX*)c2NMrQY86UtOVp2$E|k5j6Ek`w_g0gK31XU{A6gb<-"
    "#Hv${`lE<i%bE~k_Skc*@BmU>7Soqjp#BJ|pN#<*92No6$h3S*UpVfU-@vf7oU?ItDM)a!Vbr~zaQfh%_eR#0mPQ"
    "^@+a%Ef{dUGq#2|8BKCnJxFkdX}?eeWjG`Z!;)NsR#eAS~85U>ER9kae938s(|$!)+%)F3tDlr2(wt$kdL;2XEXS"
    "G{sfd&ECJ!Ugk{&u{B9uEf=hP%P}%httE^Bn0acOT+d(s{{p)?y$9%d*p2fd?#gD>{8Pv6z2j}Xu)n);e)Ij|H1$"
    "crl7!j4<S+gbi(fFBE{~;e_S4~fQr_eFQZM=vI$9^GB2fCmf>|Umo;*3fn!Fq)@FIl$>RSM+k_zR?wr(?=YA9V`5"
    "?=0aT8!P~C8#-QwllB;NtU&?a%zuf4qa&s=8ps`Sy?LCd6Z&vLW`KF1y;y#rRe7yYP)I;F^j;+{)_AczA1~xM6~L"
    "?+3(<Wn_ye>^-#a?{;pF(u!TxCP&B5qT!(Y5Z=v{w%_QUAx_)o*5;FkTvy|=H1qy1y^KgWr?+7ETDc?F%~nxHm0&"
    "OcFC<>{Y5J#NcdA!L}hJ!En;H*j`liNx^|ycEQFx63zs1+#FNc6%D`^d40hrY&zC9W`n@Y({DB2Km}*f$oBO4*sK"
    "52#A2!W`65gOC2CGU$i^8Y^fHM+Q;^QWsOT|gN07uiO3`e@{hzlL8xXxlO#5S$&yAddgiyb?6JDhzDNHArX<d~|6"
    "MHSP3Vi#v1H)W0lO<iUFcN{^TAlq(+YPUM6P+<?N<+lu&P#*2%vxd=m2#WVXbhfJgoKw9lkZFH!REwBW2-Bb{|RZ"
    "PYvgEo^<8%4s_sXAmKOTbsq44-@SOx0B*Ps{6(=kU=7ZJT2Mu_$@}3Zb$^5<!glANZkfo4?ScxC!*Zc*AXaXdYCz"
    "%KxyQnz1Ey*1@M7V%<B9q9XYB|ug>H3uQ$VUsI80y@4icxemOd;FVwao(^68Y=IGg~Wv<<j>OAs8jc=sWgTl+zLJ"
    "^q*`uF?ML!5HNQHTJ3P&yE5tfyd){C-sw^q<I`Fsbt^{oV2e^|KTJ$5hcx8KL_MO%(Rlo`A8VXu#EyFH7J?*6FN5"
    "~9RE;+1)jQR#M=F)(n@!%>QH<6Q`DWV4FZA+V>2-8J4KzCtXS%&LK{^#dh_biJ#QB%nI5~S@xm&9n((woAz1L_rC"
    "S^=FtpggCBYZqS;qCKZ7(5?f#MdRJt=oymKCQ*2%*J9&OAH%{=!T8Fvmi$2@vX!;U7Z{F5$MSl`IL_5&PS<5J^05"
    "Ibp}c_tAJK&2GYgg5WEq;Q3vW$9F>h{=S`jU!A93d1JS|TO?nnY0&q<9$CC<_sH#H6>BIyFK@+D8NmO98+tbx$iQ"
    "|XLm4zPkEX)TgxpqZc(v<f)uUqk+I%3ZF6ABbw~p>)){;@{IH>5h$stLVA8$%|z36HF+ug8>H^q0F_*o?QDf&5g$"
    "$J9b)6vcB+E(|?;OtGI+-D?@1k`}N1wIs;c0WTe6Urg;cZdHZ{NL+ByNQ(t3~$1mmiB$5d#n4{x6bJ;k;<(R-qm$"
    "6^3AkqWd|G;nR=?eP1NxcZ+H?m!zW;F>X~54*B7!|_&y8vZT;eq-4X0>S&h&%ixE-8#cGp@V!q8(bN+;fc(@-C9c"
    "*d$p?KS3k0H^p`BxP0rxhE>KRPu_H?aQ-@32%mP_*q+guBq8({63APK3^WT?|4>erVMRrh5CHL#(LyEq#WGENbrd"
    "_q$v1ac)Ijoe_BzsfHu%RMgkLf=}@Y`2YS(c@h5>+<tJ+E>FW>q+2B%fE=-Z&@fJSdZ<s)O}XQ}`4Jw*cl~eQ|L$"
    "e{O}vb_Ysh^EY6k-^BX1|)rZ+db@qdRGFEM7qA7{Vaxw~T55PR9Yk9H(!w3rv{ypoec2>^D%lEaM>v(e9NosXn~G"
    "(2t-Ng@Ye_-L>WwGW0azXuPn?bw7zCUG|XeUP)nQU@tm@~l{?hz?S+IY!O)0>??5{@9ZpdL#d0PQzwPx*zG!wdqq"
    "<BUgsED*t#~_Xyc1-lD)=SMQtS#6--DrcEZl8zd)U@0be4qvHR?0{lt@qsQ+tW(RZDrs3;IsNoUoT*61^)T<=UwX"
    "1*Y!`w;<eE!rH((y}gAeY<x8r#QXH!bnchHs#v$Rk+yYT<Q$Np2mqj{}nbzqW&XoY`7wrCg7ZtKS!B$rGA-f*F5;"
    "AQE?n+<yC0zh>-$jEefuh1>ZDhA*t8`sm=r?)*0G3*PPzCQ@Z3J$1=y?Wv31v>RBtdqJSpOm&ORK_fSNj?+9R^4e"
    "Ohp`#N*yPU@Q{!7+8;oA+L`rRA+x8Mz4-2kp#${B30{O$|J=o_SantcI_bTKWcdr!u{k+FLI<UZ{tcJAbG1no0UY"
    "0>6#_<ng;$GLFt`>~hy|Ei1E5v;$@_V?e$!HXaszK559Z}za7$8+=!5jv=xu@*;|B+}whY9P6z=(3z#7r!To{s!J"
    "$4@oC-=Q83>(w~b<_Er74Z%<B-PyWUny1(af{+`GAdmiWSd7NJ_k26u$Ry&4*gWlPx8w`PMmFu0!sdM}{kyT0c%q"
    "`Z3j3(4>a8uCD5A;xkn%1Ko6<;eE(0%LwwuHdO^$i?;?j!yZ>41^w4|D#KX?`JF`Qns4c5~<h9+ON8G--=7$HSk;"
    "e%7JCqy2mS-|rru-}C=|&;R>9|L?Co|1ZKZ_B=&|(A(80#|n4NL1DFy5g!(y%o(|@jc8+UXVdaSAz=25A7fwMp*|"
    "MCc#O96fuL|_*$-!DZ?f_8k1wBJ-sG$2?1Kac()fI4*!;qnghsK<5rk@*@vBkSSgIKyZf!o>WbsGPz2~#m$HT)PJ"
    "K5on+39LMDd!!&m&29qo>8U12ZpHQd6kXFgo8UCXBWj~zNVH9FpKjUPlMaUfmLeWIJ+vZWj?qdCq+J~thQvH*B%x"
    "NDAtEtyXJML$3G2Eh6mptjrP7D9-WQMbVq;OI~|VRo*bG<oUgxq@$&EG1?K*n)oRgy{v4-tGdJq@%a?!uhrc&VIU"
    "e`wNBr^l)i62SpYMv<AIyc8dA!#f4gYJn|Mu+o#6DmMFR$7SBeS2#jXlREJ7(7|ihNltzsoMB`RoHSSG}9KR);`3"
    ")Gtp+rh|)1pvbt0-*6Lz>KmY(@punZz!U6{Gai2jcc0HRV!z=WU1_KaUGTE}I)|gD+XG${W;&n{Zwz_Pt`Y94gpL"
    "riuM9L?ZK{W(1J^oHVed!SIRtODiL}&R!cgx8fT^L!1%KMDmz!J9zaD>V>|{mV3J7v|^wYt~@zIZlKqI(grvyOHk"
    "@|yYO@#DqcsRD)<DaB0H|rXF^C7Q>ulL>_p4sW3gseUIK(6uxz6@{2gAJEPKkXeJyc(UJ?VY_nMeL_1LDYzw8qgm"
    "qdNexy<@9X$<LJ%F@sDrL^xFM0Ut@Alo}CJ<umud@&N<j<)QBU4JGoaM`ZB)DHs%)s&Z1KXM^psAF%i+0z{C~qqh"
    "an}W`Mm8j|01g1R`u7dwg{G3t)Mf(_=V3;H(&f6dGDWI0G08xuJ06XY(auo@ZAe){I=j5xDIpHph}C5&g_tp#M?p"
    "^FMBRI@vQG7y-|)OA8e2uFS2Y^$bg>`q{r=$1rLsHCs=o|Jupa?b3>?pS}ARa8k~${}qT-4{g?=ppmK@<R^67eJ^"
    "{BU8*20rI?k~4K?EBp@C7#n|V&zpVxrmv)ahu5L3-pM&B(KRYteu*y|#{0AGRm0Q2a438EjR@psf4wSm!M=W7qXu"
    "bNLk79*08Ei`J>c}zodo{-wt0!}kpFQ*+61)VHklp|2qT?&!{>{JZGL*_(&HBca%tg~)8`&oDZ+r1@uk<Xtzw^jz"
    "pD9^0e=|#*Cl(G!|@Liq^d5S-T#{(<`htj2CHSBus^g_p%aC^L%Rb6X`FnT4;Ad=Cmg%QBuDcKgjQrN_e@vA@pJU"
    "(*u)ac`eO|5|G^cfEk`p9gm>?#LgI|FFGE5wyDJSjJNEP0tgJtXI)IZt{#h3yCMp@sut^IvmR*Rv%JFa>3il;3Ov"
    "Aj#MOhGIL^6HvAE^>%YaiQnFN`_;Vu2uud=z0dwV`wa8Ae{{BY`eJ~9khm%Ii^mX8zncGgXHV0+l!H?!KAj78TXW"
    "$7U22jeXdfSWE!&+`_O^Deg$Zf@2b^Zo$RzDE6TvkCqqOBD2!k&p$xC}Rl16gH81!aeD#ncWk*AG3XSm>gb~T*?Q"
    "wSPeT+AmMQq1rbAny5Cn_qZn{E`3d{LJtxg?2!m7q_T<nUe#*zhKAGjj>0;iH|SXpCi0!_YB=Upz1(EHt)c5@><`"
    "!9-jP_I$DZ@y|Ya<NfkJMg1GMIPyUEDU-p@wymy@4m@G3C#(|BZ4i4}Y<R+0<00a<}5DqX0eX_n?R4rJwwvl0=)w"
    "S9knc9H=Ygc{1|Mesy)fC{AdZhS4aQ)jCFCtu725WBd=8)?`OfJy|eK`w<O<@Dt7vYS}(p}!n%S+hO_wQc3e`og?"
    "{sz?(cZgCdEkzceuuTrpEGfATf<1schi(8C0Wn`1wXi@Z8{FT!Dlwk$8A65h%aVV(x1T{h<czjC7-Zd-=rJ|}{L6"
    "rTjaKL<aD@7cv_vHxKE;^c7{%A>xqT6y!vIMU=JbwU-^cg<zuC+84KRc-LIQ=bd1iNc#TiejX=yGo(QIK}ERDcH?"
    "VjAfeSQ>opbR-q(q9Z7RCI<1U&5DLCFt?UC&)S2-W{2eFPjl)v;cM-&O8H;yM?J8-fHn{!z8D-Bho)wx~EA;_cQ5"
    "a--L|LZ0yT#U-Vw!>L@pZr||DpA5fbotp!ngX{T0mZO*92JE(l2*axe_&^x!AP->J}UmM?ub*forL@=D+@t98Vcx"
    "?46Wj$~(^Y+7}grEjgw^XEPKz2&C8qGgQ_l`&*V+L5OmiaqZT^cdY(GztRILP&mjMD<!LC&u*a7fGopL5yQvePNt"
    "(N6ZKV#EKkl+aGhfnJ)LC9@`TkCu?0J{pAKaV-MPh!!UJHK8g&zv}svrBt=4%=eQWVmV|#^F0*zoh_rRt6~|A;rF"
    "k^Rp?`XDfkz3nlk@iaS3!v_FR|kI`xQ;LOR-S8DEmI^W;33;JXovDUSHrkPUk+)Xn5p2ycwM4xW909=(A+Wvx&th"
    "xcF~0XG>8iK)4jv&{E4aVC)VH-%<G%5^gES#A0|0%uFR9rb;HX1kM-kt8Mbn5m3D{=^soW@YEgP4CuB=6&64XpK?"
    "@jv!)Nmu+-sU&05|t?!d%i;BI|Z5>n)+ch<ddVZta9QEZ0oiQVJ#Eg)OF#+e*%?SFX&MplDtGrx;6!seGE1*gZ-i"
    "2R{KBhs7BDZR#+4t1uTs_<E`C^l?`3I~1uKy1&UcBF-*@crijumPCgReuUKpf4n9Guv7KXXoS>ds2aC3~a5Hzk_c"
    "79wY|)_%PjlB8}Lv{v}P^x^!qEEluq7^Ou?!u7#D6jYe0)#59-cq7na@z@)YKQWs=__ht2nqk<KxwKwgb^pm8Q~d"
    "%<(W!U14}SJJr1w6}&Up-7gXt&t&r)wsxsjF}D-aFg*64Vxpk<cd4ocJ`*IuhaOm3t78^+#)XWzZ-V-6uE;7G0lo"
    "(lLyCgAHLpo74RE2Bo6wZnhC#8J!_;)Qnhuh~nNkLZ8L3;G0e`)CB-s?ms|-lGwG(P(7WOPXqdGI@$3X!xmIweXA"
    "EI|W~Do|2BazADJUWfq{k%&y8$V6$P*W602Vj;Akcds!cL`fHC1)kJ^9GZ{9(4Ly>sS?<^HNj}!Y_?4V;zdPD~BS"
    ")K~n*SaCwcp+^Mp8!BVXH-0WA;7Js?vhbIm6ogeCi3`Xeo>YoRVb|TUKccOdk2m*<D){a;voj#e1a2n153fDH_@W"
    "^|BbWnvS*@9;7Ni&GtB^yLZTyV>85E1$JVNX-^cfLUbqy6|z~v*&g}Q3y#dM(wQ1$>n|~-27U!y%-Esedb17rmh*"
    "{uuO1Eb;-z`aP-L+*H<{_-?Ka;7DA|};8AM=uy38Y~`u$@kaSNLWU#7FGfol|WQaGK=5^X`F?EkKSK2QPG$vI!Bl"
    "BRj$|6<K_Jq;SOzky#2!_JNR17QhsZ$3qjvZtlq<sXXd+MH>)WOmJLKVSo1!}#FhC4JS*dJmeQt;*TuD!VO!vy{~"
    ">9lvq4UKGoZB^9fVjj+JeDTBblT&|7Gxjvt@#*_JF^_>2!o`3t|+kfo7_^0l-|J;Qm`OjVajBZ(VtHQ7nGpjDVp{"
    "rhSI~fC)9iO_N%x8RPwa1)&LPStef}%MQYe@6w#FTsrdN6w$;fC`W-4Q$+d{HkuGhbs=cSvnP&n2e;F6Zm(n=Cha"
    "^n6)dFChYgFDVev1iu_ymyp5*i5HOVA|J*XHDJ?X$_igUpV=F*t=$6ZDtLA|hK=XzrMX?$O-Vx-LRsK09nXqjgBP"
    "GWx5i*&;p&debH%uwP38aqLy0ok9psGoTXuT<^Z87)<PP>UU6Rs$K6?qVaYT9{wx3Udm2bLN*u9EL?d}Fv>N20rX"
    "C>qZ>Lz%Qno>@w4f}ZiWVm-Wd^LtIMVIl?Fx2jy;a>AQ^E^<o8|Bix2|t;#jIamTh2dYbIS$5sH*sDW`i;$m@Z;U"
    "<$6S|b7VKLL@=vnKdWm)dO`U=Wn_^{#$){^<mkJ54bXX?EWeM@}PBx!TFj`bDD;Vq#z07*OkqCfp7t<0>kv(O1Hw"
    "8*Bqzm9Yux5~<`1j`N)%+Gd5@IaVyu9V1<kRKFRG0zlK>4|5r#fnNNr2$-r=)%&_xZBCHk)V;-UpzEW0mpKqrsRy"
    ";KYw1HS`~PsH1ZhFsfug7%Z4!BK|1;D#M9{b<S}*v*HfE3g0uq_G9@~VSd4)5nOtW`ZN1S*carPdFJ)~<7A2R8Jt"
    "MBs+9E$bVYq0F;mqHe{_6?%0OSUgAC67WDY#Fn_ti7cuZQk&~0gUHg}6nA)OoUf7lk@VV2#9zv3C6TH>JH4D#mbU"
    "H^Y|-@@I-k)8QhdgPo4kO4@tEoTNAj6;j?3^OvRkkmM{k``zJO|l~p&7c9%jF$g>?{^>d=m!YNO0s)=js*hU)zww"
    "E?)!fC<gc%V$dfbDI&UoNsuv$TP=K;r8XW+w#FEnW?2@!S8V)$E?0=oEvU7S5I=YiESF3znViv@6>F$y&0eQCe2Y"
    "pEIdA1>a3$a3dU|QDCIeiJ5AO%2Ps*l3C{G3*WU#sAZYj7nZYC6YfCHuA|fZP3y<XXOJRxGrtiNx~R%r1RF58=+D"
    "tpKy`tDbZm*DKFAB$|rCJ363?=IP>#Ko?Y8DE_PkpHE;@^pfKO0_TKjsb#b%+fK&}Ptr~;<$odK-&Z1yB5%JKFZa"
    "g-#EhB-a34NWLg|2vpl!}LeII<tH7kFSu2y-bTD=heeH??1csA#eJZmzL1>;~$Ys+~k3Y6yu(-Z>z<u7}uNrzjOJ"
    "NpvH1MfiJi4A0ba8hd7eV$Ak=9Mmrr5jsKNqWFvXfB=9aok>TBvBthEV?97J2RQk9fWIa>!gzc{*muXFR`YePkn("
    "#-=GV1b1hPM1ml}9*XnoH4|0;7pVLv9peAM*ba{8hLHG~!@Mo;z$ep1#Z^At@qI}njXh+9-w-eE^R5>86G@>{t9k"
    "NPbhq5Hh`;{5-Q7uF#Y~be6ipn^Z1!cQf-ki)plOq2|(A#eLWBFcsLgGt0$^1#xl8NeKI#_XIqgR)aEe1!LJ6^@E"
    "gw_j57bCk|ejX+EqPwkg<X+)oHA{SV+u+jQnG<%j{$p~^2jX_bS38H&Kf@@?R_j~uU(%)Y&dtX0>mDV(td4QP>0d"
    "lkhjL-zO$I!Xr@4ev&c4_zosu<C^{Yb+au{($o*Ns1O2ZNTjadnebvV(gmqo0zL8+_hZ8FrJ-N^aVN;&{(AbvSje"
    "nLY{Y^ZWd2m1#6OL!3LN6KH=JYYVO;wfOCZU&^+3Ws~KcOsgc6seez;&mnl$<W*75XqC+HZ7f2LNfr?f@-||;{2S"
    "8o&<|i2KqDU*F*fMOU-pDYvMVZ#XQM!R!CRq0~{-yrfZx3EnSu(_a$|FL5eosb0w!c^$TdaE|0%t<p*cd-2ALS0z"
    "wpOA<>N#TC<0VwQ+`l?0HwvY_nnr(o}NOph<ktH)DN;8AMjoaUg9R)FsOq=!e)(hQB`<zZ}0fWk;7DYI=3H7eHu("
    "7J?8H2Ns9eH-RW4TCsf->%r`g)R%o0-ZJD#b6RnZGK6Gv?To{P<x!m7Cew-2k?nj;Ri(6dV%3Lr2`x|)bMXxA&kx"
    "7H$WXi^w*OGNVtFQl>IU8tI(>ur*?<hpr6_1xF`q@9CS~~&REM)yj;L8b{d9cvv$LeiBn;NReeiPp(`oWAM+b*V)"
    "0s+c=E>0^{eK|BcjCkWe7J*rUK#C|zl@K^xSW1DI7tp)zkHb-9q*5ilOO+%sTDW53kP)v=NT#1BpW-iTSj?`y3d@"
    "ClU-;u!W;Ou@M3TbGo|C)18$m@>s`RfYWuW}j|rodCu`A!S0&#y@wZ*5vBlapF$!zsH=El^nQU`^lD!QZ3r(q$_h"
    "J>TZ!+t}y%zrp7k-wc5#tae1jem;%Tiw2<bEz``hq0XRab<Q?>U>Sddtb)&*NYzp5tEi1@T~D1|?i6^MvyNtTxnf"
    "PF?g+9I&Sb7jKsNe{8ZX!r{N*i0OHdFM7m>2cpmL$4GY}Lp8WBEid$@$_d(fSijgg4F(cF1aZ9rBhaj)k!1uq&<#"
    "WQH^k1-{pmm;1}ZP#$R;=driob{Tby3<@E=%7$sTrTpoe-o9#%&9bf)6(u7o!4<u=hCgXz@cyLKh-eZwW5m27#Ar"
    "-{l4A*xx-?&OD%>FNHnqlxBHXL-GfN^eQ>akNs-2%I`oc&rDG-AondVl7rJJcp{^(NVn0xl9Ze-UYlLPMLdI6e?2"
    "B1l*=XlE5^ifGKh)NG>mvX=snb-}_MCa~jxP<%E`EBBzutn>v=TDNVa@s;9zctMw~y!oFaB6BJm&m&~ldB35)F;J"
    "rCI9EW<AhG?d;OB1Zjv`Y)h#rDCvXl3OYtS<PVxdQ1bOI6d9Ju>oKi2T3Iuc0p}q!Ji!z9fEBqG%qD4be3tKY}^C"
    "4DPN!TX5zW5*x9kNe3!dDI5*_i<L8XJ95shHsxBi!341LO$_o=`D3ms2QNsO$YECmiia^ZRgd-F;eN~(Tqk#M1*2"
    "Q$3_nDn)sFkIXD3Hl0nv1)UN;~oPR=T4SK>^0gtQRe%^xku>xpyHG##xAwmr@Cx1%;x9>YfsiRtx2w#tknOxam|m"
    "d@TcdQT)~a&UNZus`-e3N~`CiEcxqpz~Az^&k3AiAv7%U%NOHWO1--k+pG%Vpc+($mM!DOY)v;&`1)%QJUL}BE9R"
    "?M*PnLaGI)`5yUi9m7t?<Kme>(1T$nCjlrb?f|E_c%&@|?hTU*`;<S1H$oscMvNUSey!V^bgEgEfRxYv(@Bv)%ye"
    "JCynWl?4d$Gu8x6ym3gMgJwXTQTW@J3TexgD$No2oQ~TH>-rgAJ1!_#uYbG!az`v2n{8@#{BW6qMRydZxuG)@Qdm"
    "H=aj}PasOKh~*A)t{X&AFq;@Wsd{@eC|mTp^}HXq%q@)@{7SU-K~S$%YnuacAB~W->)eqMLsKarY~Q)u<iWeNL8x"
    "{`AWohyHv!&|^IMGSM<iNNci|38=@%{_mT)!viw90@1-*mKQwJrg&-|+-<VQngMpa&f)Rdm_w;KO5O+d3*Zk9E!*"
    "GuxNt8AXL)m{T2$(@Af7;-omIAG3PiMNbr!^tP?Ft{rCP^K3}(qU$2@g2b8fH`*KvEXRAOh06n^J97sSZs|A(mxv"
    "xkEJv5j)Y@@$9o<OE}mkp&If}=FG2nfieQW@v;QR=%bBd|24?RIyCo1#<)RDm9a%m-j5*0Da`v1qJ=_{zNbuCKxX"
    "^yCQrLS)>VjSA<mKB3tOC)wxypDqqN?q+;?W52<B&8>2(ihf<UU=I4uvJEUI@JtI}+p<#hGaaF1lE&B2%NP26j<3"
    "qek0!M}>KfDt|ZKvEdRF8&&@Va$>{9KBzIWLp|`{HI0sdhrd=rGYx5y#Ui*0e>Gg>gCqV@|6NPNl*;w)tCn2NYD^"
    "`VRKu^0gP8U-(kNr6s;$A5aUt4(<CpFDl$vR%K}a|-IXd|nJXE6}0T1QWN6t>XpJ!@MuEqNQd4cHV0xL*MV4{dOj"
    "Q#EvmPayxSq2X8C1S>3LNt<g)2P~Lv%bapx9ClS7QLw(+ZKUp+3`V{vKvNNYL8R>{XR>*7skrM$qb_ixK3=ymWCF"
    "=H^&K&H_J+dA=E$5l?|&0=6O;;`M*IXoaW7Xn_7iY=vL2{{qseBak*B<I^sW&G-tPvJP=W@k!1RNMhc=oov&be{Q"
    "B_l;PB5=JY1fHP`PG=@!HKrPY_|K#!J=7X|e7F@XcVKTT+w`AHJ&uMlK4MLgw*z;i%AX1Y&soMV4}<>^yP4hd%rk"
    "SHv##O*9FMm&?-6ILU<WvfwhFr;gRL%!NpCNA_G_T7yD@Uh<*H=Oszj<p#0D&B}>S_BX7IPc2z<zJku9rMDv9Z=A"
    "P=#lBNG3|Lr&=k&$V&#zvN;f?Mk(;r_Rz4$AC#JJO+_6}acP0juigS^zdCfS^eO@_n}_0$Ter9fKR-if1diO5lb5"
    "YsHOpJIQ-vu=Ys0(qj|mnM`o8dbAC2D--$Wgsma(Yp_-sPomJb(K@8O;stE@N?Yu8_$0rCF!;2E<J@MMq$v3)X&8"
    "+GiPBm9pNSn?56emU48xZ%zugXvz&ncwuSRc0lkA^B$Zm9vm!}$hjNjo1*(+#r%P2DE6H@xJmd0&ElNXe5&g2osz"
    "TjRXZa(=k%0nHmpzreY1)?{@Xz4ZDkU{Zx^cg1dqoQ~sC`l2l`R?4aD3jz<$9Vhkk02TFp@bk&KKz6$hiZOg30_B"
    "`76l1o4Zm5GA+OBKm7uQd{83UNb}iknczs_|MP6IPFpkBkV6ud=<Vy@Um)R4eW~^qthh`RJG$`(hzq@XnF%qG$uL"
    "<KH#?=&{VXLwJ^R3HfuSGAdnaR{oY-n~=xA+FJn{4y?e@=m|28=upB^8Kfr0pKp!Fa&FyTF%tm*JAJM*)lTcJwff"
    "YQS%y>U$_`5vEw!105tf;JOp9R~N3PI)plW#amF%8>x4RY=U%(s&WFH5vHJ!QqKZ0C9nQd+y=*7Xt)Jd?v`6v|X$"
    "p3Tl{9U$d&q#My(b54V7T=;zDXVly|BoDq8Q_<!G&Yiny%vLQ<ky~sF@ChrO)JWiju-~*~|R}3t_Yp_LK9J$rG;j"
    "a&<Z-rkupOe@q7)=5z)-P_zZtHKBHepwgM(3-;?=FexG8D3PS%HFx8S2IMChW7(UEypKSzEwPy69}Nn7e3q;2Pis"
    ";AaN&3w_H-U0JX~8LTq^DpgayS;|s3C<xNTiD>Wsa0TuA`1mwAI6OU);e;^D4qKVV7boeuoBVC><!hqo&O_x$LdX"
    "w$$q#X#i;kYLPIr)(h2+t6x;`XfE^(~dNas3Oq_ou>#I#(tY_-;lBByr+e1@+G42u%ROn9n#{8hG6gJDHh^>xnnf"
    ">;ycb<n?nn&bn5dhGQ)+5s5Z_rW@np)U*u*gxe(+#5xnKazh!X<<_txliF;<{goLgI_So5&qYUtMsx_$fpK$Xv4B"
    "Qw~-^aJ@JOHd?A7fEYwcu+@_zdH^6G}m5~mOj0LlO_7z_pE){<JKr6SxHVXmsrtJ#Q#|EWnZ9r4W=K&O%^Cjq7;V"
    "1XUU91Hd%9SUJn=HE)f-NiLK}#_VBwS1&4W(VK>?=-(0W-N3Yt1~S+W78jqdo4VAmF)L0yxs*(=;~Aj46tr*q%6d"
    "Zl?>C%Ae^_uaYc|t><0)p1j&8#nwT*B`4!kwNFRMLn0eG(judHLU{MrFJJbOYP%>)LDFj1NtvPOuadvevk~c=U{L"
    "x3gLWGRl~Adh&x@CP2R|eC0bx-YK^S*Qv<#rI9~#EMwVfY=>?^;mh?;g263?%X*#ge%N_l4qS4Y6Q{N2IFC^?~)a"
    "Uom*RUhZMAmWv5!*^<d*Ge`+CC|Z+feV5WtDR5U50oq#oq+53T=~H&rzd!dKSBADSbpW`uyBuZDEM$F8*;#K@!4}"
    "a7#7w>=th}HJ4e~W<UU8vLO{`mGw}#X9UPJbQ<5~=s>m;!R5gm;kWlk;#PdEoO^+9+vbg#_fv>B!+OdGrNIHCwtd"
    "5b&Rl+`2g^a;#U|bCn2GT|7X*utg*}A7DVLI;vBvbk<JEajSl&CeFrm6_oQ)ME9!62!eSS;>T^c&8sNZD;|=Akb!"
    "LNZ#iM>9=V3(&W<bmPzxGfvaLwNwNP_ll7gdVw2hRdB6Uf^31I7DO8D0HvM_6KO=qL-~_$5r+={O*&sr2WRfm{%)"
    "BS&$TvObS(Mt(IYXkz#)-lGI;ce7f2Gw$l&!FX2K}i{aL=6Z7@Ams@2IvHm4JK=D>->x6&rhGCs-5l}CX`j;SJ+e"
    "Vj@u&gae2#r3qR1c<?0c7t7V`XsUC((9GUWjc3Stm?{^frA*<+U$ie14pk@4<XGLIW?VW6W=BdFzvGQI|S3yl8j("
    "ZLy5Dc$)kDBY2?fGBQ+}|#K_Y0lEK{(s>5-U{u(L6u;{ifa^Sy*3bv@%3nZ-mYFD+@0)OA1qt<PeF1RT8yS~|2DE"
    ";**nji{sS(?s>bz<^mC;+y(oQqVnTiy(kRJ2{<41UPY8aji8Hp`W<_{Z-aaw^8nPz=C`!g!gua?|!!sTT+L5h(qU"
    "GGtGqkBGb;CEgb5NW3yIN!Sd8gEH5`YnDU^`&x=eNHdzT%Ql=dkmC2nIkg_ZNVSJvr8dloH_y&C>%L9uoYQ^GElp"
    "Z~;Y?NIC)^iC?NUc3LM2#Ev!Kj{$i8RAc0}H1zV-(7O=^lYj7!WrB>^)&`Ag+JXkn1^rac?o+A!Z+WE>cfMN#@ou"
    "O$~+)xT@HFVjPW?tYmLOD{JysEtl{`gl4=cW3%*4PXuR=nFH!^f|tsTLS~<#Ez1Q(i@Sf0<{*Z@1hEXvL?W+O>Y_"
    "kZrfS{zI~t^%o6zO4fD|GPaIn%`_Lu6piY8$*>r>R(P+OPRzw=Ed(G{0h?6Ybc#RzpYj#{kcms3LuY$2&uTK1K<a"
    "zFH>vGA;SvF@dbG!G>5+p^orfy!|^GBrcvG)AC`WoF_qWR#S)-y|l0VVI7GhMOL1E<V0=!wGj9G-&o&)CwevbqPd"
    "z)<$?YhC$*-;P-m8#CNk(Y@i;jaqWnrBfE&mISN2lL!s0&Q@9KwshOYf&8kuB<{WAPYJsn`TgqN@W5d8VwCS=L79"
    "A=u+Q<+twM9NG`Sw5bRDjjGz6lk>XkSoW5tbgm7OqhX-*K`@C<gikRoDsG9(lT<>B2*&Ps94e~A*wx~XQd(5i~pP"
    "HzmyJ6okoQa*U?ZxXLFXj&1=8re`fEqGIP)8*3Bg*k9EplZh0Nv2TvEUV%Jd|q@u$=M20Y@D0zx7yrhhg9wEA9{6"
    "*m%puByegX}w%<SOX0LDg&}7OxgQ;osnuY&EH!%DCEBIfcN%PmO{s7LV6g#dHSsF0zJD=b!=+>L^HgzR86R-h3)r"
    "}YV2<jK|TlM~X$M%A};m4|5qaDSy()m?fv~=b<!~hBS^piUUn`)q(llKOvx2=CK3l38f)RY|(i<OK5IhydTm(tZF"
    "iareP1KiuHN+{W-`C1yuv0}^P-ww9+^9@}v@l_2D8HsULotzp4b<&7_apY1x<@k|5+%*98=`-53oL%+7*x_MQ_nr"
    "$=RX@df!T9aby9@(F`&QS+&*|#D#aJ>YYLoq=LlPmhv-$b01!g4U1ROik**&y^&$MY#1Pr4=>D6d3U*8TjC&<Yh_"
    "V)&vC|Bt`Q@FUS53{ZRdl$u(1e)fMkE=vR&Pd-oaN3Phnqc3qzb30m6gk+W&eH&gh+aZs2hH5LvSyh%<x89(k_t="
    "0cN%TX)Wxoj$N&2J;CM{@_kDIt#?HJCnaTP8)}#|JJR?RxqLfV|&HGVB*X(UILf_}tW(0}J%<IY?qchEw6N5-nJ9"
    "IxG$gc{n*O|Gd!J1}szFFvY0_R64Hk*5J9Ff5f%|oc(3B?LDlRd-*wCa6z+PMw)dXhx(vK4r08I+3H>bnZ~Iguxt"
    "m%HFCkGU57Of8{jZw8`+Vh}FT4%Zc;tVzKzZ3iV$27s7!bTnNYmxd+;zaVqAv_r%oKHNVI&jn5n3d-5|w3^vqNBk"
    "BDprIVRfX-2PN@m`S=9D2;3w*MYoBgsP#X$`OI+lz=WR3!}mqq!qw7*F45>Wa%Z@3@{SaKLAf<;kM>G(qvRqGBsf"
    "^%Nxe0p&jZ-aD9B`u|Y34YHDNxiEY&i7i1yYf)H-^aVUQ5mwHPd6)3t0RqHRhllj=+3cZZ&Nmz)jumknl;GTrt90"
    "xZZTgOwxY?1`xIN{i|Nyl2oFC$V8yrZq>5J5b^b2a#1Bp?MS84ohSJ{4_vp_5QgtkLMEKJo3Kb|SmYdLnKKe=jZg"
    "tnDVzCzjJfF#e4lf&LQpivk16T8`k~mUbZyC@>FDllVV-k3ZXGQS!EjhS4Xc_T^_IjeXlj4mua=-~2h6gWoTv42Q"
    "5IfC7I`dcY3}P<yCDc)rpg8zFV@#U%GV?FQoiQ5*m=S4T0DY&TLr(b3ch+iSJr?iQqQq7rioab4HGMPmhBm64Lwi"
    "`O8hOmwwyxPB%_v7+6w}x>HZJG>#{1*F{Ukj{(ovAm<@CnCLEp^PMWRv@FcY>o6)nnZo}q@J4(mY8&@F`)!PS+{E"
    "j`c6S$++aY;GMMxQK^Fz=k!^zsjy?uiadxTCQb<U`{eCMWHyA-Q%iBNJX@VjUk!I^IMaq2Q5YpH0Oy(v6!IsR8>d"
    "jed@68oc!y{oQt*5nzj$1#U$gpl=Uq=PW2LE#l#xc0v5CMQ4C81QjHxk{iy^dSikC5ECS^++}O*3+K5+4J2{oMR8"
    "qbc7oq_Rj)}f>741C<FoZenr6dD-NNdLNAVT<%7aKqjNnp}S<Rod8m101fBv<*o&uL{dWjCpz2YFAhp+%|GB5rwe"
    "dCMwI@uAVv@5s=(ff}i?!MRN*Vj|Myk0G@W>#o-D+OJ9Sv^ryxYBo~+%1V|=<V<aKq_$mH^?=1!Y3aRZUK-MJeHj"
    "2uyyLroGi(_-U{QX2t>HIhcxfwmZ^l&5Oe+*j{SRtXKYUrwq*KFw*hR_OMWJf-gl)-^Z=u9{uWEME)%E&dX&jQmm"
    "cgUfY$`%j6o~c_8l8R>p77u4^gH)nzmI;7q&x~vN->836=PA|dLociPBp7qEPHUo`f|iVIV8MP>d@PiF3t#U5RuN"
    "!AQ;!M)fo{QilN|>d}y6gQS%lE&IC(c&i&vQV%FIh7X2)JkaLnEeNg%rtegClUsws0?BLcEO(!D4AA_&k(ly)aBu"
    "aWSWE=xaH!7E4w2GYA)w+L;FcsIxaX%vf0cy68YYw_fcmQBoTykFr1sVBmB@_BbQM!+-%zZ2~016i?|D)m{xIZ^%"
    "YGt^ukfU&(FZ>|LOm%;3Hu-#8!zJ-B-CnafpxD66Tg>{a<P>-%MA@$n_LHaD>Vg#vc?0Q|lI#Um)@!;FN)1<D2+D"
    "~xMEFX)LZp@w(TnLJ=MpOFa|S}gxAG({K3c1~?Dm6mGs^d<P?)?pIy~JwI2<2O4h|1a4Vd(STiqUdDD-qKw971g9"
    "=HMs;=x}_Gti)|0@|j`F7pL0FUr9=D&4!>?m)jCCDw<RelD{$5c5eizp;KR`fWb%eE;m(x8FtIZtCAcx_;p2`%X{"
    "2<W2R9w-5RUV(j#Plz$)ROImz%^SW52S48B}^5uqRnblwPk7!e;^F9Yq%OyzPwQZz{+@$&Xn&!u^*~2%#93K5;@9"
    "@vw4P`e5Y@IHfVCy<haDfgZ!_wj7pSTCI^<>2IiFA8vdHt9wBgJ%{44&XyH|EoCuu%T21?V+=PCEvM3*-O^6sUnj"
    "M&1xqtbaf1S#J$C`22+>Dc8glwLy^HT+C2-j|1P3(rq_#{cP!*$v(3jp!C=LYD21lb{@((q4eqZlW%|jT~7;(8`~"
    "jk$bx03Ca@{qyg6?<p%HCP=J|?w#O-sW>2vZefbZav<4{>~owK^{^D+1NooHQ1iiyR-OOY_PzqkaCPNe&FO45Mt2"
    "@yHD4%g+Cq3e{5NayiAQbHCa`wGG2lJ>U9u3DYtBx_f<!aF@RmyDaQ=E#wBZpo3=w^nY0?F%eAJ^j)G6`uQSUN%>"
    "`66J6swcl~8w4%&O8d^K!6=_UlO0ww~=pL)L58kBx|J>{UuP6OKyz?IikB5`~yGQ?AUZ&qX`+i72oa2Iz-+y<9^T"
    "*5AkeyL)?fmNK<lx`LNMzU5BA?~!SO)24q%86UyCLj%-HAHx(E0hJkskuo-#!UWqrB?VZ+?$oVp7C6-#?o?`}X_j"
    "dh~pe1LWG3bNd%2*qvT5U$TEDQJE`=lfH+mj9M{du){s^#ZQ*$QgM{r4BV?@b~*rNCG+1t9h-(66_l3((f#ZeSTL"
    "AbFtHE$st~f`{`0T)PX7Y^16)~tQ*V>}z&w!{5QJ#g_n{BjMWhg8CxRab>|Q8gjnR;sW&Z2%@#Dudn?@x$dZjfoS"
    "J*M3@8$r3Qy@a53p?K>{#i%ubAz{h^Y+0$iqnrLe>pliC2@f)KR-cty3e@Rm{T)Q#T$?yjUqRx?~M<Fe3bMrcRW~"
    "H^~K(iD?WZ49L(?T;^tDb^qO@iA=7FPKeTPCeJAaUN6&iEdyay4jZ2ks?SD8B{Sow3BO>hui!Q$5p`;_Ci<>Pk;7"
    "r>rUCYDgL9w~3L+(bB<^EQ3(v^Gkr1+;NPrB7+kWRrj66g~{`<hj{0si-0r#raJehmzL(**~oh!}(Y?whpekY0A4"
    "|2l#JQY`w6u9B}tI#YHEILQ){G7b`y1a2JVuIO^NE&egIa=6o54@J^~87OxT(le3|@FH|~pm!s4otacUTK1y|16n"
    "ka7yaT|ItK~lG_>ZB_VwAa1-8o1o>eMluv%F0p6ek_!*{Cwf(N0Z)k~@@v*urT02Ze$$a=;E8!pqvsxoRtr)?a*x"
    "_-PkBip6N?se){X(KeS!m^={x4Ue1No&=4QhfK_cVXvlNznurU)2NS_(3gvwpliO+wZTg8o%ag*YZQttE}l-vD!v"
    "Ui7C`CSQHn1_CBxLui+9FC|ixc5@VtfitEwd%a^Ser1SacWPD0y&wZEtx#bd)<r~_VTM#o%mEP>8e@zpoeUu1C{T"
    "9;G%RWo9(YN0;ULo#^(f8jquk`GCQ;wcC{<KjkS^H^OfV61H;rHJ)-&xXHKN&u0{Bccesp(}N(+|VdO>bF%m(o8a"
    "v9(^A|7SM(ee>L}#7|K9<(#<M?R7RfgQKBb%|;(<oae4LFV`cnn|j##)}5z=vAX5<0Hc;pts>xRcOEni_hZv*i}e"
    "<s{yILgYI))5e;0Lo<XB@Qt6u@yuTuqm;*(o@z#K9(y!YVMxPDQ#T7?&#obDgJKCNGtFT<<$$A9A*(D<@u86A`)u"
    "htWkMVB-LvGs;_z5%KU%DwGz@-Bg1D;n>J)xLDKN^iq5OKa`|3G1+XLK$XWiDr+1?#edgJeI`HlQY;CpZtk_A^vy"
    "!dDs9&r$3RpasjN@RVRMYUNH9fZ{x$$$?<q^zuN#S$IbvO<FFZtOx0BPK>5%i%c1k6=hvZMTZft$Z@}K;1wK9ac|"
    "3V}@bkfGlP}bjsMB$L-~99Ja<hCdE()C4%2Eti+!ZJd{qD&hzVB{*O&)6aS+h`A7b&B_3*dp;p9QN$8!eO3Qt=4v"
    "wrq69UcEm3tc8OeY$H`jyy4+>;`MA}uC0H0z2VsDnC8s{GI;Xz9vW#~p^65+D*@T9c(JG7d}ru8r$<LGCxW!qv{n"
    "i+6tJgLd5y6ok_=n7{2nSk&$&KwSX+O4&UJwb;1(Fd?W<4Zjt&#o7mnbs8B|a3^-d1{{MUn*FT1TT`$}#Cg#6}u+"
    "yKMqHNLW}Hf?X%@MqoTi}Vz7acie?O{)pnVoI`BXg1@FjY=qg?;2a0SA|!z#A%jc?bkM0mb*!>%DaD+OrhpZIh)W"
    "o-uM6y4@cuUb@o6kW^^M2GLzO-Up*|@9X_bSv7*@{+yJ9bUfS!@mX-+Ct#ZCt%LSx7VWmg^`y>9j`-fm3Lfie2ek"
    "`lz`)+3ZHgo=qFFpf+>S6^Zzf`o__e!|{47%<#Nwcb3z^u~QB1@N>YYiT1z6+@Y=lSX?Z~$ni>SKsPAYO3xF=->f"
    "@K;$m{3<4z{QYJa3y^o+!JIp|3!EAHZ!`KB4oo*1PhB&^nzBl}E!LAXy{?%@YSvG#EFy<TG+9c>=H$hYi-JYai|)"
    "3B=)&&AK0tTMA)}}-Fp%Si4#Ui{|0EB!r$w!+d7m5d;8rBvxb~|4F_wal_7tW&`)pvXU{jbY4KLee+-ntZ$%$mvb"
    "L;i~lm7R8>l%R^`ks_rKO1sdqi+)A8(YlM4X`~KivT6L%M0!`shFNN_hFDosP}3Dgr!8&T*yu*d3YMOf6hw-wv=&"
    "XZLGr@%SzNBXPLgmho@Yd{`;Uab^q;BBfWjMlJsV-@gY3uzEg(uB12voH?z?W+vsF1Ap^8|PWb8AC(bOFw0N}ml0"
    "LHft;dp(ZFswEN~>RF^9yeB7Nm18Z-eN(v@vweoh1@0rKe0ikalY=&5;~8rs?PQRaC)&gg?W-)z&DQvS|>cIKidj"
    "j|&K&0I@I9|IAV8fLl=Bsxe3oRVj?Owxn>-YYJjMktADw4!1A<W{{i!4#koERh)*+EiX_4emMSRN>f=C+Q;fP05s"
    "`X=Adtl4$dwKVni@gffW?Qmagv#!<%R?b8S^ra<mn9qbn_=kA+yG)<)9Is}9GB)LVTUP`Yj|4=OsGYZ^|%$fL5$>"
    ")Rk!qJf;u4N_V)RY96@D|R*#aHp~j0dB1}w&BitB8ma_N^7C`r#+Ww$#98C=D>DnT?kQvMCUlslYw&2<=7$3L<tr"
    "B6ln_Ob*dd}6sk3qPTJBa`!G0|l5808s<^)w2J5-n5Cq{<0j?CH(ta4)dQk%d4qMuz03&T<VbvTAc(Fv-4`{aeOa"
    "pQ!88qs##i`J}k)hDVqZ@Z!CN9EfUR%4ZGj7Jixti;O^I0}aY_S}h@a)k{ZVjiHSBwNrzIeOz=L2Xn3hYl4evXt?"
    "01|m*89jwc_;T<BhzJ1@ly@k4#u7?QSm<-(8x3d|$N6(c0$>`>!p^>05Qb!mk_Er~%x#&iCRs53f`m|}2JLSNLUR"
    "Dm(%}(r8Mcq1157-*3>z$lD9f7D=~@>A2Y`Du8h>A8=WAJZevQxQXx)^gQb|4$Mz(uX>t@(YyIz^!{|CUJo{Q-{4"
    "lj42%!(nLda~{I-G2?r==R3l^5kA}Qrsx~=x28CZoEzTm@VA=1NvP|%GQ~)V6n?XT(6ev9oI};W|ZVc2JDpclC&h"
    "N%Kk;SP<@EGo}5GCwm|k_Sp8nYfjSz6<>U=Y#5mR3PSTuIEHVqS^a{-$O&Edivc^Kkv|Qs~IZhY|YE+j6n;t-Duh"
    "Jlm47>%GVS-&C8!<EB7iIB?^;u5Y@|UAy#Aja~ok&7cAjsq-pB}vU>*V0@bbS1`y_b`d@r$FweSpS(GkCI7Pv&D|"
    "a-MRAZ9Sv)dto@$rrtvI?#mq>ed45BLl-IT_s%%4;D?5=&RlMulivMmrNFI{tn%XJ!E<#2>zA}AWu*(Z>I|Vy<(f"
    "}(_RUUhrxlToUN(X;{mhY^kO^?H-B1mivvY6k5Vq1@Jf3i+{AGq-5<}NW;03pqaPTQxkSmX~GFz*TX=<5)k6B_V9"
    "Rr3>YgR~oE%i3VlaI1#pN#+J6k3++0>5ef1-YAz<SnV4$5k*Zo~-I!UjOB`K|D1+ke9Bly)K!R*v8#?Q0J2npW49"
    "RdGh)d9m0c?qhoFYR4dE&s?1twdvUA4KEfq7OMx8YY7gnuqV;XOw^k`4U4)$F$4k|O*`!_is?dqN%blo`239IWWv"
    "@Uq*4O}(LXBNiK%xR_4r{Wa(S8e5)H#{dUMcz*jf(_v5=5Mu$aON_2~ZEb2~><q^NBJy!KY#HH()|@U*OnkK;9|z"
    ")Oz_rPz=d^b-B)HsY(T#mu9z?m*O#EzP~60ehLkC@5it*$5HLVgXIU}d^z`!5et<cC0QD<Y^9ajrSnw@3D%z(<a&"
    "eCt^k0~DpgaFu2NfTgI0yaib;;NgeuUo@61xki!2z!_+2xtmFVFb5Sa|~8>tJ{;71whljv!08EWg+85FtDGY2n5W"
    "B>oV$+Vh5?yaoEgf?)AYR*WEwYTKiE^FQf9mN|&U{(5vr$IzYQ(Kz*-40Iv9EKfO3>89bac>Qp0?2Jd*jtrW92G("
    "O)l@aoNwCzB5;xuE)o>Ub3|qi{D9P{Pzs1Y2JO@0m6p<Dm@;RIQme74!+=vq(UHL{sK3E{p2!k<T3;3cyV?U2b$>"
    "Xm$*-(4YKvB0o;tMA0ymUB<>=3~Esqa%uDZv(9^FW?as>?i&5IEjGAVDZ7o@Wf_ryFzN@lGo66+_z@23m{`pE_#9"
    "=vK2`Fgn$Ep41rs)H%=uT{;Bqh-y5`pvAjc>1<lC<>1_Srg_yR%#@CIab1Q-OM4X+%g|9M-3kK&XtVAy&M(efGQ+"
    "HNx(-X8y`RWZ(6-aT>qx~@sh%N&h(yiN&=s6&YkTWzFBPYum!fCox5ke+$Ju%{*~H9Dl2-%VgjBp+N&lJkF)}w*T"
    "5+A(mFlNsv(d`%^}*tB5iq#qmh?UK!!_zjdaQ@-{HD@w*0m8@Ciic1N18q>%Nz0k!{AatuA{mtW;g3-gC_Oq6B-i"
    "L8#+m7a!=K4^?okRs*3zxIL2zJ2Bc6OO8t4Pr=o4vhfH0wxj6L=4wjC~DxGO1xD^&u2V?2UiqQowMzBEuZOI_m(0"
    "=w~>fhSbZX!y9S3TU?1`8J|4jw^Lb>^t?0!x6AxmPOcL)gt>g#_qsYZE54c--2qNkKM7js%*)-;DQ<@LGILr+P<s"
    "-~<HdrSdDt+1*=OCPhtSupulb3*9zH4TY)hx()2V(Z{={<SuC^;b)?4D${i>Pi!ui(tgy(Asq<?i44Y2PXnxq-@v"
    "2Na;e&^qvnFtaZQo<XfFULlunF$;(m+jCGWb8g`hOLR{;F2&E>*(&J!%v7UmC@BiaUC;@F!VaUWukgQa?e2Q5KkN"
    "wZ?yFU^B*k4?7M4f7U*THre*dMZb6-ZiKBg}zlB%tohcNB;=!^WsPQkQFpfq^l2{&P|%fW64l1`D1V>-Q5wq>sQG"
    "y(gc}<#W|WV7e!B?D60Jnbw&?0B9sHQ!YOx}9x~A)j)~%laAnl=@l=4Br;lHd5|0qmx5|r2)~tY)mPpBQ8cl7gPv"
    "nGis2XJLAkys6!~BY1EhLoXLLRr_P=UHDICj#dQ3guaKKlFbg1jbbqob8@C=<z|&Cs$bn#S7nETS9IB+$x`X(p6!"
    "Zo&humMD=lDbeiUr@Wk$w^xgN`M#FH5jo;J?v`Fsr<Qte#F`}4<gySaffY(f5W7c(&KpVd$lgA9SIbw;OY0Hcsg1"
    "xb>bkKEv!Me=d&eC6^%1(>>#q|Ij|8}f$iTQ`Pb(IL+HwQw<3j>ql@sUr&y1y<EFzoXMtX>2gy*u_dUj`Mi3naIb"
    "in{&!b3syl2)}|ThO%dtvV{#mT`V)tc-7I4IEUsrB&a^y=WaR&4RaS3+@^xk(xRJ-<vG819XEN=$D0NWQZ<Tu#*$"
    "6S*Q;WOUF+b;@O8f9+pjm3B>X`>!&MJJ3xj;mQ^=0L0Fk&1+!@^r*ldx62#WI+>#R?h1D=)=ATius=Y%R=XIV~d{"
    "BU+o!II5=SbLALeLV%ZhS{G-@G@$H6IQ3wIP|VrqU*wk02>+(s`{$uN{B3YHctB8i8UkesT0SItKeu!Bn6-2W(7v"
    "TL6qw)4xCAK*M`iImt<QBAd@!aI$oQmBZ7Z*Keo$E$F+R^EE<g1Wz*0OXH*++C^n2!aTsL?791In6x9tmRYxSHII"
    "y#`fIh`=HiEZ&o)lgfd3QTb06T1-d?c)FhaW#z)6bjYp!XU6DCc6GW^%~NO^x@RlKuWnvv23NB2ap3$Bl__V+@c&"
    "XPN}pRWyn&3JC)uVPEwXCw`(%3>T;pIT0k_-3*tCtwF*G}W>mi>oG97ulh%{=a`pvJ!z3J`~R_g-+a;bq7*7PLnS"
    "waw9FIooAyLDR@0e_ZtPaEk_M%#&J+bC9X4tQw_9#^QoO1^0DvXVD|FbifkvYE;iITY6~4IqB4AJ?Z~+t$T6=R@C"
    "H{^6A=9tS3?lXABEz;NApKsnQJ{0mGFRLCN4;TJ?eaN6o6v@TXO`CH%pEK1KSuBL}mf^LXVP#QP04DJq#(rkcb?i"
    "E3O4d$-4s0iKkBEkp$s`B^79R=P>cu?hT&6Fvp<L2N>0(ODdZ^acj`NX{>54fg5Ric!q{*8HabWy7s|JG`;00Uca"
    "!nXhXKdh`;PL5PLYqk^9!y?+36iO+@vm$4NcI<g6%2LF2F%=_nqUr7>fsv2`-SKJbA9(PudivoT-1JV>}EG~uF9>"
    "v~pP<g*^SK5YQLa&eumg3fPKOp7yMrkH!s3NNN#=4cAUMcYtXu5n5BzbabdT0n}68O|g(NKL&;*Q@+jZrR*ZG+U%"
    ">GT;THG$H3ukAZK1N54o`Uvf#`EyQ`{-3#lc1bli?6%m8*?HIOW%BKr6ut!a87p4xV#HsT1wsa|{dnT4D;oJax-)"
    "bX8{hgD8KhwS?kCPYc)uR7`@m8mQ&2G<%bTvP)OQ#aqom($2iHX9jeJ_2w3XZ&BSvCD$628F7Evh0B4>pmlS2Zjg"
    "={)9K9K?NyA^<bMBVJn+FD@~lW03)?$D%5iDF8lK*1-&I;bv=r6wBvxS`q=}QGy=E9`Z0i11KsB*?@*phCpS<419"
    "0wmnjyD(2&v!fGGXfbzy7D0T$xp8UobGln$^4Ef^(BnzMnE4$25zJRnL524-uq>|Yc_9NmTx4DZG$VcN07!dU`Lj"
    "@hI{XT)^}G`hKB0Hq$iC21i;O$*?|TZ!(|69owcqlayd`B^xHZ(X|tL0r|xL08bCI{ByLOYDgHdX;GzXjN3Vr*LQ"
    "^C;0+tIk`sW+C(nt$Uku;huK%P)QdTCfb1icyj-hGuT;4_fY7p&S2yw-?rSL^-S#>=yiz=Qtw*dK+hN-c^`gqH+f"
    "&`nFzuvap2M1$t5Or+6v)1FGS~b8$C3<_kErmK0UI@d?p@s7zEf5jAOTN37^6vI(ilO;`+Xxcic=b*DXE>tvXQzz"
    "%<1e1ber8W=rBYez*5mnLS5ve%a(~$(YvJM0x13pr;pzCk|0f@%U+4L%CU8}$N<GM0gm!As{=fq>II%(>y<-Sp+O"
    "T*-!l}C7CNL?XZgj32+84le-V(!)%~E1HR#12s(07LtXQ-q(DTy5#9Xs!VfRk5<$r9lP4<Nn>OVC}{&Ky(p0E|lc"
    "eoXxIRRY?|4AnBkHxxUuV{YzbjH3%mriU_0d-Ox>3V{E%EB4~3B+HFq$in*%iAH6X2S;>K@0<FGa&_RJ(=j(+EmC"
    "g(JInK@dF|VIRM825$@}u2aTKb-+c|2xHM$AALz)S(;UHiIKRYdZ^MuP^e=~t96)osA9WS&*Fj0tjg+||X7#lD=E"
    "=L?ytdJ*$ZfnhIci-Wkgfgt8YzI9p;r>oD5me*2Y2_c2r0^&>uc_OUOmP+`^>k&Zmcq*yk&`qiBesoBNB944j(^G"
    "uk(TN5)?!{J}cG?uNAKI*8pqbZ{=MZ{6|=>Q3c%2W7##_aLJ_v<>(`NOE3&m|Md1clOkHq-<k32K9)Ga-IiMEZ=d"
    "Z@3N5QLP_)nAjgoJkJlUb(*{%OPn*ris-m($8^l<bj$RBX0%Z_{SSuww@&x?u1yUJvQ9+O>HO11HY=6n|K>5=AvX"
    "#q58Ag51z1$AiPvD}CqA0h{zDl;8jqh9c^9#kCtgw5oS-FoWHtAphA@ypWTn7MWZ1I<Pxi6jY(coa+kz8vjLig})"
    "ugQg?YuxEMzv}wh2>&@z%^=M4S)<J+EiX~>wE>QSRkK*i}i3!uP<30@&DfB3_^&66?@2b30ciCOfeVdlI9UwJzSY"
    "dK|3Y^r!`t<z~D6!}6&)i#H<vn1OPM(wPkgdpSbt(XtdL!p6#@Mu%WT=ifJ(<|S5VES5Y=7ZunMC_~b$$N_V5W}P"
    "gJ_}&Jcb@=JUr-V4kuYV;@^(Y{^GjY3EBT-{Br!_G<lT#bbR!4;&lz3w|UI8E1G;cLf|Ip=wH3iUpQdkaiWS&Z1~"
    "8GK!g10jitksh&la9tQ!2U(=16}!N}#LB-?yfwqI}?Ih1jUIek{FO~Htc{SIq!aCkC4K26BhIBH!9_tw%6K;NR9{"
    "B7^$>+wm_`JqSuHT8!&I!s<19scz4;Kiwp(M|S`wDBBA$#}>SciNg~^Fj0k|Fv7VD!`!4OvdSji%R77-IE49|Eg`"
    "vToKOj1@}9cb6v?<bS!#F{G4u^DfcM^`w5}N{V@QJK8;*C@-M3!lWz11QJ+jREB#WaF7>Hwqvs70DR;mVRrPITDK"
    "2?})^6*XxWikVpQG}rWl40r9Zqol^y<hXofPSmK8HZ!B5KKRL=glG8?iN3Hp7WVs-pjalp=Wo!=&&hD3XdwI82^C"
    "d4j)H0m3)m@D~c@G1=IdLxA8|r+^3V?rM;*6$M0Z?D67v4I5d%WlZEqYuZJfmz$F_7z`fKnZ@mSjx>IsY5a*@T2_"
    ")lygM_0`uV4WKP!j%(+{7-V<Ps_CI=XrO<rk7Mz0KBGRUp*cgWZ;^NUMpKO>{oe%N>jnuTr+sTR7!!}}CexlR?--"
    "PF%Ef)GDuO#_u*CD<&VRr_^6)NY|^vNGkas47%`%s(biK5f>vL`<*i+uF0gO7;uM&d$pj&~A`%ldcv-*<>tTok0Y"
    "jOSff4dqEZ|V<K~bjWCSrh&1`@jmD2dpbZIuNNywwIkh`dV}v^<06^90Up>DXl~?hdJEL`X+@t5)akdkPUj5rB#A"
    "eb$BBgXN^o_b?qFkfXG|Sl~2f^a2@#T*1B+m=1vdZrm>bJeHzL7ZT)@|=?VSTw;-=pC?0AH;3zWB1~<TU6K70V=F"
    "t{Xz^$W5pjCe7F3oop6t;&%m<5dgoOUDbRWPb0XO-*o$os#m+-)XkR*>}R-`<%Ino-RA3qJ;!oZ(^;a))9;3>)_e"
    "s7D_`YX4*YQx^&DtJyOwYvLNTa`fBWF03ZJ{-M|ZaGnn56Q?k%xn{%IsTiCinflfAAYGG#WZJjoxuhSzSEe!halb"
    "OO|@s2jJ_hRf-5{PcO1mEdjXHWji}fj|y4bs!82r8msBVT$LP56<h@h9~QF8%tvGUwui#OQeT4yjaRd7T4$6TRc)"
    "=aH%fZs`Nm<n3`%*=j-HYx7%7#8!S@Tr<9`(6A;MfxgmV3nqB=6pQ3ZFq%`XDod=pF+o)(-$Yu2K)%bA#;PB56n>"
    "O!we|(($_;(yfhGI>gHuUvtcc}DsQbxJWdLv$|?q1v`(jo)J4SNg~pn}YeL0-=3Y@*R03yO88eofaL=YC^<OJ;3-"
    "twGR!ZTH8A2jl&RF56almduM&8GGHW&SYHy*xMK>+@i0NJ<X!9%tQcYahWL>rCM~YCw+Z**^<AUp1zV6dQ!0NdX("
    "<SB6fW56Qil!UcAu_qI!kg0)KYo7go$?Tm(b$+dtI&>v})_c{BX>_fN=ZMr7gb+vOX@DO|5MOXRH1pF7`eikkk_n"
    "hT0JAp0&(E>xGhx31%G3-{ZDTA;bNEkwxHG;2shp5I-3AS$cA&1+w+9T7Dq^5gp^&8E<(tx~(!`QgJ`-mz=Ay%|P"
    ">!pWv1GE<ZuT+x0MS+hoH;9rNQK1HzA-yc3Xxcl|tUk{IdIkW*jg~N*eGXJFJtM`!p4?TU^(GLOfS6Hqck6oIi%9"
    "}RCqk{0)$9T(zEjxMFm8=w5I=}K;d!L3!cGt$FATV89SK=~kVQiJ{bEz}cNe(|LEq_Z&K5yQ@5*f;@p|i!-q<lm1"
    "m4(4ylcv=PTCzwxMt95ht94@ja`(lyCphLZY!HmC_w7P7yJznkAd*yCwC9o(#bPqg%WHN_L_oyEyXM^g(}Rf&+0~"
    "(GGG(G&%r<M{(uSpXjT1Kq2*vV4Az|F#mPo?4%;4~1j(~<HGrR8vaeV<#y%&<vC!6>me@;1x@ztvM^_BzBTY7;?|"
    "Ipic3V==f?MG5je@1m1b4Eb_n3JwGb47~bL=TohPHBnpB0GV|ja?T(+&1+6vI1~ATKyRrpR!>d$8L48F|;*$*Eeq"
    "ND#tZ{Z0HvC%^T!BNcMwz;StRy(ah0O$vAFGWGqSVzDhZ<qP^W?Geo$Ygtbcsa7YPtP$2))u!%hgqC0-%Y=(v|O4"
    "_^0FP6JF_^$CDG~2pD5_9QpajUBv4BDOOLR3>A!V`NJrs?eKIm}i~i8^trOV|#M_MucfkC;9}e(@;ytg(X7j6$#_"
    "xI)lSCR{HVl7tZ}(FH`*yT<0A0wnkAM0l7q+^Tf~WnR^gYsAaRuY@-8l@r?e$PI~w;F&jZJt00ImjHL&b!&R5AF_"
    "+=4^~zAuN_(sVrV?B6m*U=K=tNy2I59*=as&b(W|p>XY%B`-%p<X)Aze4Me(Cm$!%!g=yRTAGkfw^xN)fIu^+?lD"
    "+AQ#TYrW6@h<)OX2OdPdBZ7x!#ih3g7;0j&e`sjob?oJ)_|sZRl+%j^+g#Lt_of`O6G#Rd7o)I7tDd7<E-1c&|27"
    "7@LZ_s7=h_5-e#Gs*vIU%wad(u4d>UaWqp)vo}n;KSRV>OHcW)xCN$JUhj{zoZd=BeV>_JjM(bPULk^LSC+dD>?-"
    "wnI371NOPeqv3vUn=L^I(8@MPZsH_5gpzPY+(tGMmv7)G~N>SQR}I6E|M8EV?a&NIdBit0!WsYh&vi1W-Yho%QX+"
    "XVGlkp~lG#8|&6GX@6dyu~pqQcFKw`=Y6giqFl0U1fpWT<Cd~p#hz(sSIZ;R`_<OoG-y{Fb<=HRGfnZ59ri(opqH"
    "5}=q0jf{hJ1nCZlg3NaZ$t!5{AGS#4o5n@eE}^V%wbSh`C4D9K-HC3ipf*c+tJ-F9`ojMVfWQLAN&y3@`F$xr!m&"
    "Sg*Xi`2ketWq4tYxf=~{$bR+_2(+-tKF3EHYjk{HCt~vurFR|rLD_4A=_?VvWv;5DVyRljBTC_)efjlpTjGp9j-Z"
    "7*<u0%FxQo|=-NT+{#0H2eRj*!ZNf<I?Doig+e&?|DtR*ADcAa8K>Kl>E+(9pt(unk@YJU!%6gO%&a#niD=xNWg?"
    "r7C^~uK4Bi4>aD&Scb)|9fkuaNI@>KL|6zWHK0nI$ocBB_<8qGIruJ?zqGkzSq6(*&BvkpC|-zZ+^6cB*ty=t1aF"
    "!+XjqnW?tVcy+297wU)51o;+L37_2ms@~j|+w6U<obV}&xu;K}H@``j;z!dn!xIh*l+xvU2LLDp#YJYk!y)>g<%&"
    "2B%`a(X>NLw0M9jCzBi>J)!aurWYot-_i6=LHJ!-!zIAN_ff79~Vw-11M_3uS43je^)Wvw+|elCMG#_+LP7R~GMW"
    "pXmQwKW}pz&bU$>h$sNn<r#6@rS4HYHM-MCAUVW&a#<!^;n+pX2^u_u3m5E=&r+K^>{(#rf&2{@+ToCN8|qtCs96"
    "={C-dN=GT$wh&F9i`@<@uX3`JXqz4ulxN(?r0#c~G!kT$ho9y$jSE2m#5TJ|vJe%Fl7TM5n2W++m=pcad0<C}|<e"
    "6YvpJBaH?U}X5$mAY)p)>WEX=qnlKK^5fkM^g>)2^VT1L7g|n6&6iwJsLiT8sOFp|R4swDvVL2kXr6Bdc$QAHmh9"
    "HX}w5OW!Wx7Zv2$Wwo16w)~JSP?2gKfgBKn)wsgX&DHyvKu4YiEg}Th9k;nhhPdr8ae_V>tlkUKrNM8ITu*1~o(?"
    "qKYlM)Pa=7y%6D;`ve^=1pX=LEZ^`t~wMv{Cd#{Na2+EViJQ?0ZWRAQj#bkZcik7KFOwGKRQmpJ(xgFx->O}bzxd"
    "HT$l^VkiPMQ~3Wpu%a-v{jZ_%}CDBbvcqEVeiSJ1r^bY1+4+DPghw07J|z4A@(h3=Yjfnzcm8VtUbs}zMboSO6kR"
    "h_CTmuz%<hYg&V!MOKfnK&Mtj%w1MPe<a5T{##`PZ>ugTum&4xY{-kisl6+a*etu`1%e1^)<Y&G)&gF)?7VYYM#d"
    "gyD_VX+HvsE)}X=me`p8$OMrVwR*3*`av`I64zAlXwx$o7BDz2m-uy2w=`XmG?E5cXGN$Y)f4pQln<Zg|P5!7n+y"
    "0`58gl@_=sqGc(hezkGbYQtl7Bw`Vvt&mdZP_uG=UB)}0ry?s(xCeWIw2jjW-P4&m7wIhu<GD+MrXAvtTr7cErzS"
    "eay8+dZ?V2%uHFwzJo=z=jF5npBpI;pv?;ZbrvVU+qesOwq{CBP0XheT`H9kH$I5{03N)MN7K#i4aj($jomy=g}F"
    "UFHsM=uXv9E{Pu#knCn9~+)UhL;=ht}8TftnkU!6AVzk%*e`YXb=tz<7nN^=J^Fe%Gmi?y0Qby8>S_(f+>+M1MGB"
    "?m_5f>wW+p0#2~9uAI3qYr2w%B?{cgq;7^>)aw%ADjO%R;7a1S}Z4`vFVx%d37t|e39X>{<1v;~r7<Ohaseos4vm"
    "XVx=ne!I70XBZ(fKM<3Bb8ffb7hP_m#XPq<O)nNEES0u`DrKC>PMKRpCsDSSGKI$0y_Czm4}NM~4&ILbOJK-Q!Rb"
    "2U6D8OX6<^#5ccr_C2ez!5~Bi@jxMpX`fTzgZ?kX`6sOJfuRqX#Q@(2s>+AV8;<xs!an&INQ$XlIHd!Hrh*t`+7p"
    "Z?!4SC(TAIiKB=wZoJzLO*e1g#jlL=X0**yO+nM~!FG1f$SMvBvBO*8|5(*7m8shH1~j1`VJkb)4Przy*LZL|io4"
    "v$<aGZhgDCMSSUGg9r&7^>n!u23G+!2mcU7uv={n!*V?=#x-5&wo{+u6VYBY_Tdf7ng>6g~B!M50n22W|AQU!r)T"
    "Ua)#t(vA_vr`j&Nb2M7CshNbj3`yxFQi_)>spZ^^aFy}5eNZ{u5SUF|<5E0hKc6sVrSWp_4yt@+J(aT$6J|cXCg!"
    "Lj>0=H{>!QKRfz%O@>j#*e$-ZT)zMY@_V01eDNBv}qCLD-w|3^dg{Y8dLoH}`mAltl?v1*(_GejTddvRnovhIbDz"
    "j*Qeo1aU#y$rYB2=&KZW4v!QP8dC^53K{&(S~?#D@M3*OPJB0wa+Y1F>ZBCMoQ2h=rAS{*@VG=a(>m<zvtX7h$_w"
    "w5S27hWjaVX#DQv`zc6QKrmG?u}LBDaq(AV6ThF#5}khTql-lc~{DFSVLW8j_;iN%$*>&tW2jeNHJT}gU~5+1fSQ"
    "hEDee09AxJl}?HDNSoGM;MlUOa=7;kg|#;?bZf9A?*>x0t`Kq@f@P@xAsE81pqDpC}_H9>V-lp1*X=qF}r{sHVW%"
    ">cW*O;Q2>A;!=TfQ@K0%45u-GJ#sZ#Y?zI(g$W8$rpL$9q=i+hKHP6rW<VF<inE<!Ds1HPB%;cELT%eO%sfOVdf#"
    "OR~@;q*Rpn%v*>y43z$Dy4l20HV&>PXY21frVFDZHxmAJtck@Ued*p%~|#@cWIDcw%<QjnR*ijzW`r!m3;xM^xOc"
    "1G{0eE;`XeyHV<z_ohL>W|e5x|17aqD6M9X_8PlwfynuKypq6Nu3LyAT9*F_nh>j9;vAue-fd&x-v==9gy}re-5v"
    "p>hI7%wYz6!l6rb~-am_vNi9x3~M5C?22_85MMyWJEk>l)w(?ZS{i{gyb*+)p>tb2Kx-4c7m(6!R-I<PU@YPTJJ5"
    "D6PgyvO#s&-qeDC9R8<xbw=7`uYBc@#~r|6GO(?V*Io0$ydoQqA5;)RL{`KGQBP@q1Zk4UrO@s)H`+92ML%qwtR_"
    "Ms==V3S`1wZZMA@)Ru5Gu%NJ-@NLDtn$mxe1K1R5z6=?5_hq}s3LBodP<c&4ZZ#HivU}@fbkuAwqT98h5Q>Ypt%}"
    "Y(ejGSG}nAkDHt(VA1#OvkD4|$oxHd+^&<P8N>3_FY_P*PCFBJ1C|+!Q+z4d~a}!-+3>wL%g+iS2J`Vc0AUTGanj"
    "-!l^D<{VtjhwW`^)O)F`?*LpMIdAOzk?%;bc0FJvUELEQ5#DA6zZ8p8UHuYXWXwDCjfRUin4dkGCLOPz(#qXv_lU"
    "Dw?|Ff`qkR)}>H&za2yoZ8!}aje{em^`n(OdroLa(4TyYb=n3Rp#zVSC_u+On-WDW0mqmF(>lQL{$pntNN@4ZG%b"
    "b_${ir*3~9~5s;paR*26DrhVxxi=at`)<Nu7@&v?j}Mi>yJmT5BK2>IeBsPYRuMe_;hCN6WK06Lwk1;ZO=rogv~y"
    "_C*W8;=8<{4XZ{lbhZnTv*?YCH+~Po$il{LVA=Yw^Q6TwsgEg+cIo60*Z!YJoVa<EKBN@}tdL@XAjn45IH+~QO+="
    "GaCUFW_E2?u9E&f3Ypz64z<N;4X?Hqf|2Uurkzkji`J3)CrBnx>0WyYvQ3?P$|D7b_m<zQe($XSEwyEjSP!c5`bx"
    "XHb=4Sg<)fT+id^fxNMj5N3-gOKDy3^q?WbUCpr*+O%m*<Wubtpo@g~f^?3bi;qOSxM?6!Os!n4Zq34nEyRv-&u6"
    "uRwdh{fX_pL!MNx2EAYE5XL_<^s;g=yE7*Y;g@a$R{w-1~_t_JCGagJqO74gnbNj{b5g-wlhIVZNtz@(gnN|M`P`"
    "GOzYa-Qv0fe4>8>E}uikzY2%r-=K^xD)P1sg_Z=M>cjKsvJ7fslL!i{TryGUu?AU@~UmLy9imMg<xnoKi<_9%TVv"
    "N2|1N_)S%cYBOX~aM%|{Y%?-HQ8)sLM6$qRpxjL-z)9GPic8|BDYzEyf<|~&*8e)~IIy&4aCfgllO<N;$2^Y>Iq3"
    "fBL!%{|jd7X!Eohgm(vBVs0%$W;)fRevIJ{`X}9q$W|0B|b8svH?2bt*O3&*X|eBk9f~Av;0$2m&0QVir!*M{cI`"
    "%}P{=Jgj`^scXuRRW&v&(Z6&qKKe`U5|tdC^cOTE(gH|ypB2Bl7NaTBTxOT}Hyq8mEx1{D=na)`7?{HO*`j`_fMj"
    "OW>&4uUM_MkNif4s*%vjoJE+^yX+dG4ogVjnu2G`nL0w8>@v`cIwTX$@Gijbw_Xj4pXzL_B<sMLk8tN$81FN5}~w"
    "*JtqxXY(g$;H&jvYr{ys%n)I8v742S5SjIR}>Xq%H50!9!(c~|3~NM4uZW3F1_-aQS0Qqs-W^t^wQeu)$9fqiDje"
    "6@(U+fUxvAM!CFk5k*0daeBSz-1lQVrWuoA~3Neg$&Ovc^xYr%)v|8mQ+SQ}}LnO~4o?+WxZ(g7Vd!<VwN1P)sPr"
    "!<0UIP~2$v?_u<gZ$?kX~xM^qM^fzZ>a2(bqK>SvOenYGzvS%%mSp$TusHuBDY5qq+CPx!a9K6kIS{EIN+Iu5>De"
    "#Zl+oMwYK#5p0~1edyUPjP&203^?Nd_iWISA3W%$-PRt&G#g7dvcTP$Pcc%<g#F%A3-@zm-k(Hi>6mib%?yw_zWa"
    "(CASX7CHM;6Nxn>pK@ZH*im$+a<(0i(OHV4R%c5jDOG6cF|eEQxntLu{(D9ma!`1expW;M{=6s9&7gTNfgJPtZ}U"
    "0=G&a3Fe@xUzdq7hv{rWo6HF$yE@_R;DLS8+nOo4Sh<$H0p8e`aO%WMRF2x`68DX=<Kp6N^KgQOQ;Dgbz~JbOAGl"
    "h&L=}6A*L54L1>OeYqkfs=njK|@DynbRKiP=t0PJD652llbU|i~de0c7i4iW?kHdmY@?-|9E7+*U$z5lJp*^ghOz"
    "Rzq&N4AxY!>w5$K#(~pN#i|c%+<u(5!JArnr<#RTN~Li8ma-j8cxyq`^a=^tyJPNc-n3V(F;iZO9#R<DUDe+i>EO"
    "5hV+;E^ST6G{~%&%-M3CuQzP*CH&T65vJ?Pl%&twQnO%6(ZD2fZQ)q#QMMKVthplT!iMp$!tr%HiKz{X1_=)>wi2"
    "{eZOzqz*igj>?b<{?A_t3>^!-w>G&CJexxhf;4cZ$%O{N-tm^y<(8f8f45&h9Gu7i{_3jxF1B;i=sO5A*~js`YM&"
    "Nh;UD2OO!$`Nz$2gX1e80qaf3VS4-UPSeI#8iO|x}h`PX99?_+BQqvL^}n|*q$sI5b{%}OMK(zGM`;WY*2_<6(!f"
    "C<GetL31>LzP&pDYppULm?6K}~9}jqci6K-DmVXRFb)~k8C%VX@!5l&206PL;DndAj6jv?en6iIy89)(-?@0T6v0"
    ">D=N?af38~z98c_kbrooU#!XAta9nBddxRWb>n6JMtnoH60rorNADccLPZW(Pu~0@#B3IwaA_d8r^=*HVw<Y33>|"
    "*%{)Fi!xW+Dv%AGMWr5DvF6CS@>(s6tEYYK9)^3p#7PR>+B)_}`S*9LyXNSdUKV)Yy=mm6f=1psuIAJI>XEk~Q!d"
    "MyV?ES^_Yf=c@O_qDKLo|Fq{X`9ur$T+;yN{wYWWO`d{YR|y>iugaW3&YPR2MNCLbU6l82J$t_op&!MokNt%1CaE"
    "c2wAlGu_DU~S_@L3Uo<xuwP7L3r%9G&XJ=^!~fHlh-d%95?wGuREf?%%^qaCQ7R&BQnn^ohS+!P8>9D&Pu4cyG;O"
    ">8tn+#mNFm7Zo)#=$MebqvlrnlNXl_qLRCgO23;S_%SUCz#&x%gNtTbFNaJrG94tv(taE08mn2N<oxE8vBH_usqv"
    "}FLDyv&<Ju58|w~)TupMdx!?W!rmL2UsKePD*92~IOU1Ii>8O`F!K#*6umfz>uQr%u|yav7bs*5t^0!@uF&r6*Kv"
    "E?ZiPBkQ(NfcI+ByDGM$=I=5V1OLm9NMB_AQ_LO6cnxUP30`7{@lcNH94lWJo7v@{TG@*CGo>Ub|6GJG&%0EuZVJ"
    "_m4qqDGUsmgenjYo*MamYuT|T(`zor`0_y"
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if (
    hashlib.sha256(course_bytes).hexdigest()
    != "db2f64d72ea110c6e773f87417c637c0f414dbde0cdfdf530db3bdb275f994cd"
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
# Reviewed local subprocesses import the same supplied modules. Colab installs no
# package, so register the scratch runtime the way an editable install does: a .pth
# file in the interpreter's site-packages, or in the user site when that is read-only.
course_pth = str(COURSE_ROOT / "src") + "\n" + str(COURSE_ROOT) + "\n"
for course_site in (sysconfig.get_paths()["purelib"], site.getusersitepackages()):
    try:
        Path(course_site).mkdir(parents=True, exist_ok=True)
        (Path(course_site) / "lucy-course-runtime.pth").write_text(course_pth)
        break
    except OSError:
        continue
os.environ["PYTHONPATH"] = os.pathsep.join(
    [str(COURSE_ROOT / "src"), str(COURSE_ROOT)]
    + [entry for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep) if entry]
)
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch06-a"
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
your connected work. Reference: Python's [JSON](https://docs.python.org/3/library/json.html),
[dataclasses](https://docs.python.org/3/library/dataclasses.html), and
[pathlib](https://docs.python.org/3/library/pathlib.html) documentation.


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


### SQLite from the first row to an atomic change

A dictionary disappears when its process ends. A database can retain records so a later process
can resume from evidence. **SQLite** is an embedded database: Python's `sqlite3` library opens
a local database file without starting a separate database server. **SQL** is the language used
to define, select and change its records. A **table** has named columns and rows. A **primary
key** identifies a row; a **query** asks for rows satisfying a condition.

Start with a deliberately small preference table. Read the SQL as instructions: create the
table, insert one named value, then select the value for one session. `?` is a parameter
placeholder; the values are passed separately so they are data, not SQL instructions.
`fetchone()` returns one row or `None`; it does not guarantee that a matching row exists.

```python tags=["foundation", "worked-example"]
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as intro_sql_folder:
    intro_db_path = Path(intro_sql_folder) / "example.sqlite"
    intro_db = sqlite3.connect(intro_db_path, autocommit=True)
    intro_db.execute("CREATE TABLE preference (id INTEGER PRIMARY KEY, session TEXT, value TEXT)")
    intro_db.execute("INSERT INTO preference (session,value) VALUES (?,?)", ("lucy", "09:00"))
    intro_row = intro_db.execute(
        "SELECT value FROM preference WHERE session=?", ("lucy",)
    ).fetchone()
    print("Matching row:", intro_row)
    assert intro_row == ("09:00",)
    assert (
        intro_db.execute(
            "SELECT value FROM preference WHERE session=?", ("another-session",)
        ).fetchone()
        is None
    )
    intro_db.close()
    intro_reopen = sqlite3.connect(intro_db_path, autocommit=True)
    assert intro_reopen.execute("SELECT count(*) FROM preference").fetchone()[0] == 1
    intro_reopen.close()
print("The row survived closing and reopening its connection.")
```

Index `[0]` selects the first column of a returned tuple. `sqlite3.Row` is an alternative row
factory that also permits named-column access. `dict(row)` then produces an ordinary dictionary.
The book's `Database` wrapper supplies that configuration and its schema; the wrapper is course
code, while `sqlite3` is the standard library. You will use the public connection and transaction
methods explained at the exercise boundary, rather than needing to reconstruct the wrapper.

Now consider a budget. Moving five pence from reserved to spent requires two values to change
together. A **transaction** makes a group of local changes commit together or roll back together.
The example explicitly controls SQL transactions with `autocommit=True` and SQL statements.
`BEGIN IMMEDIATE` starts a write transaction; `COMMIT` keeps its changes; `ROLLBACK` discards them.
Predict the row after the deliberately raised exception. Catching an error alone would not undo
the first update; the rollback is the operation that restores the prior state.

```python tags=["foundation", "worked-example"]
intro_ledger = sqlite3.connect(":memory:", autocommit=True)
intro_ledger.execute(
    "CREATE TABLE budget (id INTEGER PRIMARY KEY, reserved INTEGER, spent INTEGER)"
)
intro_ledger.execute("INSERT INTO budget VALUES (1,5,0)")
intro_ledger.execute("BEGIN IMMEDIATE")
try:
    intro_ledger.execute("UPDATE budget SET reserved=0 WHERE id=1")
    raise ValueError("injected failure before the matching spend update")
except ValueError:
    intro_ledger.execute("ROLLBACK")
assert intro_ledger.execute("SELECT reserved,spent FROM budget").fetchone() == (5, 0)
intro_ledger.execute("BEGIN IMMEDIATE")
intro_ledger.execute("UPDATE budget SET reserved=0,spent=5 WHERE id=1")
intro_ledger.execute("COMMIT")
print(
    "After a complete change:", intro_ledger.execute("SELECT reserved,spent FROM budget").fetchone()
)
intro_ledger.close()
```

The literal `:memory:` creates a temporary database inside this connection; it is useful for the
small experiment, but the earlier file example establishes persistence. Neither example proves
that a remote supplier rolls back when the local transaction rolls back. An external operation
has its own state and evidence.

**SQL you will meet later.** `UPDATE ... SET ... WHERE ...` changes selected rows. `AND` combines
conditions. `ORDER BY` makes an ordering explicit; absent that clause, do not rely on row order.
`count(*)` counts rows; `sum(amount)` totals a column and can be `NULL` on an empty input;
`coalesce(sum(amount),0)` uses zero for that empty aggregate. A `UNIQUE` constraint rejects
duplicate identities. `GROUP BY status` computes one aggregate per status.

An **invariant** is a condition that must remain true across operations, such as nonnegative
reserved money. A **snapshot** is a consistent view at one point; two separate reads can describe
different moments unless their transaction contract binds them. In the book, `with db.immediate()`
groups related writes. It is a course-defined context manager with the commit/rollback purpose
you just observed. Do not assume that an arbitrary `with connection` has identical behavior under
every SQLite autocommit setting.

**Your prediction:** two workers both read ten remaining pence outside a transaction and each
approve seven. Why can both believe the next order fits? Explain what must be checked together
with the write. Then change the example's initial reserved amount and repeat the failure.
Reference: Python's [SQLite tutorial and transaction control](https://docs.python.org/3/library/sqlite3.html).


## A skill is versioned guidance with declared requirements

Lucy wants the same opening check every morning: inspect stock, review deliveries and prepare
drafts for shortages. A **skill** packages a reusable procedure with a name, version and declared
tool requirements. Its text guides a model; it does not create a new Python capability or grant
permission to call a registered tool. Keep “what the procedure requests” separate from “what
this worker is allowed to execute.”

The book stores readable skill definitions in **TOML**, a configuration format with named keys,
strings, arrays and tables. Python's `tomllib` reads TOML into ordinary Python objects. The `loads`
method reads a string; `load` reads a binary file. Parsing checks syntax, while your application
still checks required fields and meaning. You do not need a separate TOML package on Python 3.11 or newer.

### Read one procedure as data

Predict the Python type of `requires`, then compare the required capabilities with the worker's
allowlist. A subset test means *all* requirements must be available; a nonempty intersection
would prove only that at least one requirement is available.

```python tags=["foundation", "worked-example"]
import tomllib

intro_skill = tomllib.loads("""
name = "opening-review"
version = 2
requires = ["list_stock", "supplier"]
instructions = "Inspect stock and compare the supplier quote before drafting."
""")
intro_required = set(intro_skill["requires"])
for intro_allowed in ({"list_stock"}, {"list_stock", "supplier"}, set()):
    print(sorted(intro_allowed), "eligible:", intro_required <= intro_allowed)
assert not intro_required <= {"list_stock"}
assert intro_required <= {"list_stock", "supplier"}
```

A **staged** version is available for inspection and evaluation. An **active** version is the
one admitted into current context. Staging alone should not change behavior. Keeping versions
immutable lets an evaluation name the exact procedure it tested. If a file's contents change
under the same version identity, the evidence no longer has a stable subject.

### Build context within an explicit byte budget

Context is the input assembled for the next model request: selected skills, current preferences,
relevant history and the new user request. More context is not automatically better. A limit
forces an explicit admission policy and prevents an unbounded history from consuming the budget.
This implementation measures UTF-8 encoded JSON bytes, which differ from characters and model
tokens. Predict why the non-ASCII example below has a larger encoded length.

```python tags=["foundation", "worked-example"]
import json

for intro_text in ("cafe", "café", "🍦"):
    intro_bytes = intro_text.encode("utf-8")
    print(repr(intro_text), "characters:", len(intro_text), "UTF-8 bytes:", len(intro_bytes))
intro_items = [{"kind": "skill", "text": "Inspect stock."}, {"kind": "memory", "text": "10:00"}]
intro_context = []
intro_limit = 60
for intro_item in intro_items:
    intro_candidate = [*intro_context, intro_item]
    if len(json.dumps(intro_candidate, ensure_ascii=False).encode("utf-8")) <= intro_limit:
        intro_context = intro_candidate
print("Admitted context:", intro_context)
assert len(json.dumps(intro_context, ensure_ascii=False).encode("utf-8")) <= intro_limit
```

Notice that the example measures the complete candidate representation, including JSON brackets,
keys and separators. Adding the lengths of text values alone would undercount it. The actual
exercise preserves provenance and the declared ordering while admitting only bounded items.
It does not silently truncate an instruction halfway through a sentence and call that the same
procedure.

### History has a configuration boundary

A completed old conversation may have used another preference or skill revision. Replaying it
as current guidance can reintroduce an obsolete decision. The context builder therefore needs
to select revision-matching completed history. “Completed” concerns that prior episode's state;
it is not proof that every sentence it produced was factually correct.

In the core exercise, the `context` function assembles active eligible skills, explicit preferences
and bounded history. Its caller is the model-request path. Unit B removes the requirement check
and demonstrates that an active skill requiring an unavailable tool enters context. The repair
belongs in eligibility. Strengthening the skill's prose cannot replace the missing set condition.

**Explain before constructing:** what differs between a malformed TOML file, a staged but inactive
skill, an active ineligible skill and an active eligible skill that does not fit the byte budget?
Give one observation for each. Then write a new procedure with no tool requirements and explain
why an empty required set is eligible even for an empty allowlist. Eligibility still grants no
new capabilities. Reference: Python's [tomllib documentation](https://docs.python.org/3/library/tomllib.html).


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



**Design question:** Guidance cannot create capability?

Construct context assembly from active eligible skills, explicit preferences and revision-matching completed history. Enforce the byte budget and retain provenance before adding the current user request.

You edit a complete function in a temporary copy of `src/sovereign_agent/assistant_context.py`. The real callers, database and tool boundaries remain connected. The self-contained setup above supplies the frozen development runtime. The notebook runs reviewed local subprocesses; it is not a security sandbox. No live account is required.

## Predict before running

Stage and activate a local skill through the existing API, then inspect context with and without its required tool capability.

Write the expected result and a falsifying observation before running. Include one legal action, one refusal, and the exact-empty case where the interface permits it. Explain the consequence for Lucy if your prediction is wrong.
<!-- #endregion -->

```python tags=["setup"]
import json
import os
import runpy
from pathlib import Path

ROOT = COURSE_ROOT

SourceTask = runpy.run_path(str(ROOT / "book/always_on/exercises/source_tasks_v1.py"))["SourceTask"]
REFERENCE_LESSON = 5
HANDOFF = Path("ch06-unit-a-handoff-v1.json")
```

## Construct the complete mechanism

Implement `context` in the string below. Keep the named signature and existing helper interfaces. The starter is intentionally incomplete; its failed connection is reported separately from whether the notebook itself executed. A constant answer cannot stand in for the real mechanism.

Inspect the supplied caller around the function in `src/sovereign_agent/assistant_context.py`. Draw the data path from the observed output through this function to its actual input or query. Then write your implementation from the contract.

```python tags=["exercise", "learner-owned"]
implementation_source = """
def context(
    db: Database, session: str, prompt: str, *, allowed: frozenset[str], byte_budget: int = 16_384
) -> list[dict[str, Any]]:
    raise NotImplementedError("Construct this chapter mechanism")
"""
```

<details><summary>Hint 1 — the design</summary>

An active procedure may require a tool the current worker cannot call.

</details>

<details><summary>Hint 2 — the boundary</summary>

Inspect the parameters and the caller in `src/sovereign_agent/assistant_context.py`. Identify validation, durable state and the first externally observable effect. Preserve the existing surrounding helper contracts.

</details>

<details><summary>Hint 3 — the structure</summary>

Read active rows; require the full requires set; append preferences and bounded matching history; admit items only within the JSON byte budget.

</details>

## Connect to the cumulative runtime

The following installs your complete function into the copied runtime and executes the chapter probe against it. It saves your implementation and the observed connection for Unit B only after that connection succeeds.

```python tags=["integration", "handoff"]
def connect_build(source):
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        task.install(source)
        result = task.visible()
        if result["status"] == "PASS":
            task.save(HANDOFF, result)
        return result
    finally:
        task.close()


build_result = connect_build(implementation_source)
print("CONNECTION", build_result["status"])
print("OBSERVATION", build_result["observation"])
```

## Challenge and transfer

Compare staged-only, active-empty-requirements, partially permitted and fully permitted skills. A prompt must never expand the dispatcher allowlist.

Use a fresh `SourceTask`, install your implementation and edit **only its copied probe** to run the changed input. Keep the expected result in your prediction notes, independent of your implementation. Call `task.run("MY_TRANSFER", expected=your_expected)` and close the task in `finally`. Retain both a valid and a refused case so rejecting everything cannot pass.

The instructor runs additional cases with different identities and boundaries against the real source. Passing the visible connection alone is not the transfer verdict. Do not put instructor solutions or holdouts into a student submission.

## Save and explain

After success, submit `ch05-unit-a-handoff-v1.json`, your source, prediction notes and changed-input observations. Unit B checks the chapter, runtime hash and exact implementation hash and re-executes your code.

Explain which input or state caused the output, which observation would refute the explanation and what remains outside the guarantee: Eligibility and fixture activation checks do not prove live model quality.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch06-a",
    "attempted": 1,
    "completed": int(build_result["status"] == "PASS"),
    "failed": int(build_result["status"] != "PASS"),
    "skipped": 0,
    "connection": build_result["status"],
    "handoff": "WRITTEN" if build_result["status"] == "PASS" else "NOT_READY",
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: Admit only complete skill requirements

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

Implement transfer_check(skills, allowed). Return names, preserving input order, for skills with active=True whose complete requires list is a subset of allowed. Inputs have unique names. An empty requirement list is eligible even when allowed is empty. Never change allowed based on instruction text.

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
def transfer_check(skills, allowed):
    raise NotImplementedError("Separate active state from capability eligibility")
```

```python tags=["assessment", "transfer-invocation"]
import copy
import json

TRANSFER_CASES = [
    (
        "partial capabilities",
        [[{"name": "opening", "active": True, "requires": ["stock", "price"]}], ["stock"]],
        [],
    ),
    (
        "all capabilities",
        [[{"name": "opening", "active": True, "requires": ["stock", "price"]}], ["stock", "price"]],
        ["opening"],
    ),
    (
        "empty requirements",
        [[{"name": "greeting", "active": True, "requires": []}], []],
        ["greeting"],
    ),
    ("staged only", [[{"name": "greeting", "active": False, "requires": []}], []], []),
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
    "unit": "ch06-a",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch06-a-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch06-a",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

## Extension: put a language model behind the assembled context

Everything above assembled context and then inspected it. In production that output is the
first message a model reads, and the model then asks for tools. This closing section puts a
real model behind the function you constructed and shows what the eligibility rule does to
a run, not only to a printed list.

The boundary is the pair `context` builds and `Dispatcher` enforces. `context` admits a skill
only when its complete `requires` list is inside the worker's `allowed` set; the dispatcher
refuses any call outside that same set with `tool_not_allowed`. The model sees guidance only
when it can act on it, and cannot act on guidance it was not given. Preferences are
operator-owned: `remember` is never a tool. Completed work returns as `past_work` only while
the memory revision still matches.

The loop is `agent_loop.run_loop` from Chapter 3. `llm_lab.py` supplies two models for it:
`ScriptedModel` replays turns written in this notebook, `OpenAIModel` sends the same messages
to a hosted model when a key is present. The record always says which one ran.

**Prediction:** the next cell activates `opening_check` through the real activation gate,
records one preference, and builds two workers over the same shop: one with all three shop
tools, one without `draft_order`. Write down which item kinds each worker's context will
hold before you run it.


```python tags=["extension", "worked-example"]
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from reference_organizations.store.agent import OfflineShopModel, seed_lucy, shop_dispatcher
from reference_organizations.store.evaluation import CASES, candidate_checks, evaluate
from sovereign_agent.agent_loop import Limits, run_loop
from sovereign_agent.assistant_context import (
    activate_skill,
    context,
    preferences,
    remember,
    skill_snapshot,
    stage_skill,
)
from sovereign_agent.assistant_work import claim, enqueue, finish
from sovereign_agent.database import Database
from sovereign_agent.llm_lab import ScriptedModel, describe, scripted_turn, tool_trace
from sovereign_agent.tool_dispatch import Dispatcher, ExecutableTool

LLM_SKILLS_DB = COURSE_WORK / "ch06-llm-skills.sqlite"
SESSION = "lucy:morning"
PROMPT = "Prepare replenishment drafts from current stock. State GBP amounts."


def fresh_shop_database(path):
    """Start from an empty ledger so reruns and replays observe the same rows."""
    for stale in (path, Path(f"{path}-wal"), Path(f"{path}-shm"), path.with_suffix(".authority")):
        stale.unlink(missing_ok=True)
    db = Database(path)
    seed_lucy(db)
    return db


class PreferenceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=200)


def build_worker(db, allowed):
    """A worker is the shop's real tools behind one explicit allowlist."""

    def recall_preferences(args: PreferenceQuery) -> list[dict[str, Any]]:
        return preferences(db, SESSION, args.query, maximum=5)

    tools = [
        *shop_dispatcher(db).tools.values(),
        ExecutableTool(
            "recall_preferences",
            "Search Lucy's explicit preferences for this session. Read only.",
            PreferenceQuery,
            recall_preferences,
        ),
    ]
    return Dispatcher(tools, allowed=frozenset(allowed))


def context_kinds(db, allowed, **options):
    system_text = context(db, SESSION, PROMPT, allowed=allowed, **options)[0]["content"]
    return [item["kind"] for item in json.loads(system_text.split("provenance:\n", 1)[1])]


skills_db = fresh_shop_database(LLM_SKILLS_DB)
candidate = stage_skill(skills_db, COURSE_ROOT / "book/always_on/skills/opening-check-v1.toml")
activation = activate_skill(
    skills_db,
    candidate.name,
    candidate.version,
    evaluate=lambda skill: candidate_checks(
        evaluate(OfflineShopModel, skill=skill, cases=CASES[:3])
    ),
    required_cases=frozenset(f"{case.name}:0" for case in CASES[:3]),
)
print("Activation cases:", activation)
print("Active skills:", [(skill.name, skill.version) for skill in skill_snapshot(skills_db)[1]])
print("Skill requires:", candidate.requires)
remember(skills_db, SESSION, "format", "three bullets", "lucy/explicit-message")

phone_worker = build_worker(
    skills_db, ["list_stock", "supplier", "draft_order", "recall_preferences"]
)
readonly_worker = build_worker(skills_db, ["list_stock", "supplier", "recall_preferences"])
for label, worker in (("phone", phone_worker), ("read-only", readonly_worker)):
    names = [schema["function"]["name"] for schema in worker.schemas()]
    print(f"{label} worker sees tools {names}")
    print(f"{label} worker context kinds {context_kinds(skills_db, worker.allowed)}")
assert context_kinds(skills_db, phone_worker.allowed) == ["skill_guidance", "preference"]
assert context_kinds(skills_db, readonly_worker.allowed) == ["preference"]
```

The activation gate ran the candidate through the real `evaluate` against three authored
cases with the offline model, and activated the version only because every named case
passed. The preference is in both contexts because it does not depend on tools. The skill is
only in the phone worker's context: the read-only worker cannot call `draft_order`, so the
procedure that says "call `draft_order`" would be guidance it cannot follow.

### Run the loop against a recorded transcript

The turns below are what a model replied, written down, and this run uses the **read-only
worker**. Read them as a conversation. Turn one asks for stock. Turn two searches the
preferences, asks for a supplier price and, having seen the shortage, tries to draft. Turn
three answers in the three bullets Lucy asked for. The run is real work: it is queued with
`enqueue`, claimed with `claim`, and its answer is recorded with `finish`, so the next
`context` call for this session can return it as `past_work`.

**Prediction:** which call is refused, with which error, and what does the phone worker's
context hold once this work is `DONE`? Recall that the dispatcher checks `allowed` before it
even looks at the arguments, so the quantity `6` is never validated.


```python tags=["extension", "worked-example"]
RECORDED_TURNS = [
    scripted_turn(calls=[{"name": "list_stock", "arguments": {}}]),
    scripted_turn(
        calls=[
            {"name": "recall_preferences", "arguments": {"query": "format of the brief"}},
            {"name": "supplier", "arguments": {"sku": "SKU-VANILLA"}},
            {"name": "draft_order", "arguments": {"sku": "SKU-VANILLA", "quantity": 6}},
        ]
    ),
    scripted_turn(
        "- Vanilla is 6 tubs below its reorder point; the supplier price is 250p, so a draft "
        "would total £15.00 GBP.\n"
        "- Strawberry is 4 tubs short at 275p, £11.00 GBP.\n"
        "- No draft was created: drafting is not available to this worker, so this is a "
        "recommendation, not a draft."
    ),
]
LOOP_LIMITS = Limits(model_calls=8, tool_calls=16, seconds=120, output_tokens=4096)

scripted_work = claim(
    skills_db, "read-only-worker", identifier=enqueue(skills_db, "ch06:scripted", SESSION, PROMPT)
)
assert scripted_work is not None
scripted_messages = context(skills_db, SESSION, PROMPT, allowed=readonly_worker.allowed)
scripted_result = run_loop(
    ScriptedModel(RECORDED_TURNS), readonly_worker, scripted_messages, limits=LOOP_LIMITS
)
print(describe(scripted_result, "scripted"))
scripted_trace = tool_trace(scripted_result)
assert scripted_result.status == "COMPLETED"
assert [step["ok"] for step in scripted_trace] == [True, True, True, False]
assert scripted_trace[3]["tool"] == "draft_order"
assert scripted_trace[3]["result"] == "tool_not_allowed"
assert scripted_trace[1]["result"][0]["value"] == "three bullets"
assert all(
    message.get("tool_call_id") for message in scripted_result.messages if message["role"] == "tool"
)
finish(skills_db, scripted_work, "DONE", scripted_result.answer)
print("Phone worker context now:", context_kinds(skills_db, phone_worker.allowed))
assert context_kinds(skills_db, phone_worker.allowed) == [
    "skill_guidance",
    "preference",
    "past_work",
]
assert skills_db.connection.execute("SELECT count(*) FROM assistant_orders").fetchone()[0] == 0
```

The refused draft is an ordinary failed observation and the loop carries on. Nothing about
the arguments was inspected: `tool_not_allowed` came before Pydantic, because authorisation
precedes validation in `Dispatcher.invoke`. The finished answer is now a row in
`assistant_work`, and `context` returns it as `past_work` with the work identifier as its
`source`, because the session's memory revision has not moved since.

### Run the same loop against a live model

Nothing changes except the model. `build_model` looks for an `OPENAI_API_KEY` in Colab's
**Secrets** pane (the key icon in the left sidebar: add a secret with that name and switch on
notebook access for it), then in the process environment for a local kernel. Without a key it
returns the scripted model again and the record says so. A missing key is a normal condition,
never a silent substitution.

The live model is `gpt-5.1` through the `openai` library, which Colab ships preinstalled; on a
local kernel run `%pip install openai` once. One run costs a few thousand tokens. It runs as
the same read-only worker, with a context that now includes the recorded result. It may read
stock again, trust the past work, or try to draft anyway; what it cannot do is create a
draft, because `draft_order` is outside this worker's allowlist.

**Prediction:** should a careful assistant call `list_stock` again when the context already
holds a recorded result? Write down why, then run the cell and compare.


```python tags=["extension", "live-model"]
from sovereign_agent.llm_lab import DEFAULT_MODEL, build_model, resolve_api_key

chosen_model = build_model(RECORDED_TURNS, model=DEFAULT_MODEL)
print("Model source:", chosen_model.source, "| key found:", resolve_api_key() is not None)
live_work = claim(
    skills_db, "read-only-worker", identifier=enqueue(skills_db, "ch06:live", SESSION, PROMPT)
)
assert live_work is not None
live_kinds = context_kinds(skills_db, readonly_worker.allowed)
print("Live context kinds:", live_kinds)
assert live_kinds == ["preference", "past_work"]
live_messages = context(skills_db, SESSION, PROMPT, allowed=readonly_worker.allowed)
live_result = run_loop(chosen_model, readonly_worker, live_messages, limits=LOOP_LIMITS)
print(describe(live_result, chosen_model.source))
live_trace = tool_trace(live_result)
finish(
    skills_db,
    live_work,
    "DONE" if live_result.status == "COMPLETED" else "BLOCKED",
    live_result.answer,
)
assert live_result.status in {"COMPLETED", "MODEL_CALL_LIMIT", "TOOL_LIMIT", "MODEL_FAILED"}
# Whatever the model did, guidance it was not given cannot become a capability it has.
for step in live_trace:
    if step["tool"] == "draft_order":
        assert step["ok"] is False and step["result"] == "tool_not_allowed", step
assert "skill_guidance" not in live_messages[0]["content"]
assert skills_db.connection.execute("SELECT count(*) FROM assistant_orders").fetchone()[0] == 0
```

### Challenge: shrink the budget, then move the revision

Both rules in `context` are data. First the byte budget: rerun `context` for the phone worker
with `byte_budget=256`, the smallest the function accepts, and predict which kinds survive.
Items are admitted in order, skill first, and an item is dropped when the JSON of everything
selected so far plus that item exceeds the budget; a dropped item does not stop later, smaller
items from being admitted. The skill's instructions alone are longer than 256 bytes.

Then the revision: `forget` this session's `format` preference. It deletes the preference
rows and increments `assistant_memory_revisions`, so every completed work item recorded under
the old revision stops matching. Predict the phone worker's kinds after that, then replay the
recorded transcript against the phone worker. The transcript did not change, the worker did:
the draft now succeeds, and the recorded final answer, which says no draft was created, is
wrong. The observation with the matching `tool_call_id` is the evidence, not the prose.

In your notes, separate what the scripted run proves (eligibility, the allowlist, the budget,
the revision, the transcript accounting) from what only a live run can show (the model's
judgment about when to read stock again). The saved record keeps the two apart.


```python tags=["extension", "retained-evidence"]
from sovereign_agent.assistant_context import forget

tight_kinds = context_kinds(skills_db, phone_worker.allowed, byte_budget=256)
print("Kinds under a 256-byte budget:", tight_kinds)
assert tight_kinds == ["preference"]

forget(skills_db, SESSION, "format")
forgotten_kinds = context_kinds(skills_db, phone_worker.allowed)
print("Phone worker kinds after forget:", forgotten_kinds)
assert forgotten_kinds == ["skill_guidance"]

phone_result = run_loop(
    ScriptedModel(RECORDED_TURNS),
    phone_worker,
    context(skills_db, SESSION, PROMPT, allowed=phone_worker.allowed),
    limits=LOOP_LIMITS,
)
phone_trace = tool_trace(phone_result)
print("Same transcript, phone worker:", [step["ok"] for step in phone_trace])
assert phone_result.status == "COMPLETED"
assert [step["ok"] for step in phone_trace] == [True, True, True, True]
assert phone_trace[3]["result"]["total_pence"] == 6 * 250
assert phone_trace[1]["result"] == []
assert "No draft was created" in phone_result.answer

llm_lab_report = {
    "unit": "ch06-a",
    "scripted": {
        "status": scripted_result.status,
        "tool_calls": scripted_result.tool_calls,
        "refused": [step["tool"] for step in scripted_trace if not step["ok"]],
        "context_kinds_after": ["skill_guidance", "preference", "past_work"],
    },
    "session": {
        "source": chosen_model.source,
        "model": DEFAULT_MODEL if chosen_model.source == "live" else None,
        "status": live_result.status,
        "model_calls": live_result.model_calls,
        "tool_calls": live_result.tool_calls,
        "context_kinds": live_kinds,
        "refused": [step["tool"] for step in live_trace if not step["ok"]],
        "answer": live_result.answer[:400],
    },
    "tight_budget": {"byte_budget": 256, "kinds": tight_kinds},
    "after_forget": {
        "kinds": forgotten_kinds,
        "phone_worker_draft_pence": phone_trace[3]["result"]["total_pence"],
    },
}
llm_report_path = COURSE_WORK / "ch06-a-llm-lab-report-v1.json"
llm_report_path.write_text(json.dumps(llm_lab_report, indent=2, sort_keys=True), encoding="utf-8")
print("Saved evidence:", llm_report_path)
print("LLM_LAB_REPORT=" + json.dumps(llm_lab_report["session"], sort_keys=True))
skills_db.close()
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.

<!-- #endregion -->
