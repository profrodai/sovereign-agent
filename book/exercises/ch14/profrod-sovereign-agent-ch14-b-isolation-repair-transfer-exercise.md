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
    lesson_id: isolation
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch14-b-isolation-repair-transfer-exercise
    self_contained_runtime: true
    source_basis: 444c5f6
    source_unit: ch11-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch14-b
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
# Chapter 14, Unit B: Break, repair and transfer tool isolation

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-09**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch14/profrod-sovereign-agent-ch14-b-isolation-repair-transfer-exercise.ipynb) Runs on Google Colab as it ships today, or on any local Python 3.12+ kernel.

This is one of two practical units for Chapter 14. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. Repair the failure: A known tool can still be unavailable to this particular worker. Install the method in the real Dispatcher and observe handler invocation counters, not just returned text.
3. Solve **separate registration, permission and consequential authority** using changed inputs and an independent expectation.
4. Retain your implementation, failed/corrected observations, causal explanation and limits.

| Minutes | Dedicated activity | Evidence you produce |
|---|---|---|
| 0–5 | State the problem and make a prediction | Initial prediction in your own words |
| 5–25 | Foundations and library examples | Values, explanations, revised predictions |
| 25–35 | Trace setup and the main interface | Input → learner function → observation |
| 35–60 | Reproduce, diagnose and repair | Source, visible checks and runtime evidence |
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
`practical-work/ch14-b` folder. Rerunning setup restores the frozen support files and keeps
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
    "c-ri}3v=5@k}mpJYB@Kq$!>@ysh33`&K|WaPy4po@{!ctXF^mUK%yvO1OjY4By$}4?>92Ds!#<KKvI@H?hWs3v_+"
    "s$@5;)@mzkehlQ_P6>4gv8Ds|)N<#f)ccgr}4vh?M2-s^XltJaXU#`wRJxwp)C!umrNN1XAG%P^P*8C%3Y4_U(h%"
    "z2tQ>><eJ%!^n&n}tEdS;Et09HpGif{$6A@GjLhj>b{2SjI`lyySN2B`H@Artxy6e$2ge9tIQj`(J4sjiXr-FIb+"
    "0VKC{6rkN=4^VQXd3+@LApJqRMkstEJVHdJ{lROB0H(v6HC(wt>pU*$A5&JZb7-MYQn&xR1FL*L;4cWMLmQPpXmQ"
    "%b;5+1=Lc=_Aq8|~dPiT!+<rSR^W9>V{98n@EBoIbex<+q*RkKeyLJ3Ah?95!x6-h$Js-@PaZLysQEkvsPyAKnb$"
    "cf#Yu=ZT9e15aN)I`u7_{Cs|Les+9yT5jWH9#7-Y%Xp=gzP*`)re-d$E{^~B>Ga~_pXGKgv&4It@FZDP8?v^uFWb"
    "3s#?d3J$~f}*j4gPYdbd1nr}KE(8B&>qXL%BtQ>^}^rAXpXbR}J-8DFSXDvC_wDC5-nxb;U8WSn^{ox}cF#7PuHw"
    "=B)#=^dLS0iUs1oG{o6T?RYXtm?Ovvp5P@ESqzd=F4Rma9?~q^QKwaW$(QOXL5tE2@m53C><nB%mt%EXRH2A%%V7"
    "B%RHIRy_7RAT4i(SU!1UM=miUw&Akjy9M;4?25FXdjWL(jv6!Dcg`Mu069Ol!>*tFlO}xX>ILX{QzDh?|NzOZJwT"
    "hKmdaE$@d{G`L!f4$3^MOaZ<5p?qwB;JNuqZT&e>lb~vHJMd*a=3lG)uU*fI@G*Fy+R(j4zfv@qp|=fu32v_tDMb"
    "J04*RgZ%^JZNj}YhJE1j*(^@PPKn}(tC`hyYQjC=#jVoz<7vL&Q6@(n%y9jJG>Fp7i>6$aaF`!VRXLm?FGxB2-3x"
    "Pmnj~@3hILsiL!Je3#CUYi!+6QrB2P0m;kf3LfAMKHZgr@V={ydmJY^#$8|mKi4630Qs$jKOqJ+c3Ak8|kyFwnxr"
    "ycfRBi3*3DO?I#Z-FWY3HM8VV<Xwg>)uUsU&Q?2M#l$YEVCdA(z#13G;U$vU?0TGackqr^aCGTrOH?oCkrnOSE{#"
    "S$Eog$w#8#OGoK!7=Tel?1|Xh@TCz9}-KiIbuprgf37_Su7ZxX{W;h;OhF%cKS?9i>Ru5hZ*E64H+Vlsraw|v$#O"
    "!%#8bIf>byKJc8fzVgyt?2S|Cq5+sZ~X1Y9|jqb6A=sI5Y4Po^;bJ36||OGXm#xvCLLtA}U=HBnT=j4lj~w7fJP+"
    "o2I?I7PsJy!{BdqwcR*u;eBlP=yB<WyJ0(}(w$CGDcmhf7DPy9InmH-ou9aI*d1SuLT@qgJ+>UOq8FVCB}NubkRm"
    "aY+K|HdfhTN4Gm1ajqKah_PeQ%`(s8ZR!FUm5DSRjIFE(zmAF&H`<KNguQW-)~D43Pzg8eW1oOzM2HzT`C+a;o*s"
    "Nt*T=LuYrLB!hQ)-v>_+}H2rgf2<C^2BR-bBc%Jp7qVs2fbERW79+PqL%a5^_EK>`OtctroklSERUddTwLZ&;lK>"
    "VBw~%`)|B;V+cWZ(={(Ndz_)Er!5??ixi{E9Xs^4xyF8l4K5utA-8uj02e&-UU=PUFkUuusk?jL1jF+pf&-oJmph"
    "Bgqy(LS-eQESu{M~^`p2R-#(28x4FO4hpKHv{xCqu8`zEn3SapIY)cQl~hXV-c!Zh*e&9kG2`LrtIvo6f!H78tr9"
    "nsVGrQr-YEiw(Y3k32R@cseKYQznEqCZV1)N;5CZQ(`;bpPs(Cbl)DIT>W-@=3bos{_gY-gTWiO{KT8#q~oF2-^@"
    "bq7VD{!24gNtT$Q4UxRM%)w0$JjZ5n!M$}Zsg;!*@l+ZKULPCP9%y>i7Qwo@L?9GFsv&6W;>?dq^adh4(`_k5nD4"
    "vY9ho`h?bPqxYMKIQ&vmZ!9W(>R(1w|T;S#v>mo4x_Sy1CX0A4DLBz)NR<Zvc12tW0uC#JD%;t$X~)8m<0<S=b3}"
    "_$zxfZc_Dl7!f<CAf+%pCdx;lioOhX&q<3X?L6jk><SBOV4n#qq99iN;DGIgFe>Nc*W127W(942*&b(V-@#H3=Jv"
    "frWZd+f_d6q4QFJFf7)C=cvnhpE?z1_W+_x+dCxtF~xF7wpbSiYBeBaNouG$<OP6%<P|`ZR8x&=tRPwOR@>!vo?w"
    "#d&&(@_S3l5aIx!(m)r@+vQEv>2%>uTj?3Ze2;c}9p<G<&0uVa2RwE3q6^2beX#HD?;aMs2k^Lw_t0T~XZY%%c}p"
    "o}2LCwa+!vS2l-Bb_$|kFfvoKf$S()X)IRs*tVtcg3&fmU0d-wj-y*R!6aQ^=C)KEl7j(ylD>z0_|q2h!qBCldyh"
    "vizzQnSVkI<}IA@GLYJa1XHo%koKzH+QO(0QjaqtcbQ$*CYmYQNp*9is@6O&!85laff-6_?|Q1T8wJC?0rlZeahz"
    "EJv7K8Mm#{bGEiM&epFnBuAA_JNO7a6z5>2Vs<OJr$t@E25BR3-^K_a7OE>@{*Y)G6>vr@{yPog6p7^FcZtd&<<p"
    "GX_7={t9YQo(t$+_BEb>9l1+5z(F<zc3Y;`E`H+ybK~zQ=!{hEy_xc&o9IU<N=%CSSz<N<4>amhSPJ;@!29=x=B?"
    "(k}g`doWpP$4lOUY*Z$*a4_*(c+Pm3a#lVm+9^do0S|f;!=McU&h9c}?ej}K){b_>^&3UZ4*wYFlobB2UpZU9q7D"
    ">Bz-C?$a=*(iGcU>5c^G;Nk9gTU42c)zA&O?C^LTC1`QS~BWtGyEr98`*4m<?eI!ji?hDJ^##hYLp8CzK~_W^E=v"
    "v<FrvR}{NoSrc?kuA$?k6U8CRWbJV-T%G%?c%i9dsrpS`L$v{ZVJk(UJ3r=MxR>IpFccOwPBIhs4dIAP%f#I-iEN"
    "1E7b`S8qApMf{5U{Yy^_5>%!4=T_woUNgYQmhpo|f53Ks`!H{LEC2)Yi4ua^OviP1Sw3eXR3!<F`U&P6(UdL^yv`"
    "K|6ek6GWuTY`A^fKV(r6&7>m(9mg*}Yu(UX%q>`SK?(<+$w}c7p88n_!wb>}|k9UwxE9M|p4?xx^{pj&t!s64hMA"
    "ad_f|Va*4qsqlkz>1ETo{N|1L4T|;Ck9?YEz^y<{nnoSR)lKrqg;BNBENR1d+O9hbLhibqE?oM!bf}*~Ys0wJ>2$"
    "8gEvN$t%ZH11C#RQqFPiFe(Af2ys>*xFc6;i%uA?5Z!QsBar@oIRl}_7gHYEk1nIcA!jkGCl^N(5LjmE86oJ;~A_"
    "9mz%rWwgsdIKLw{w-S3T2#{2T@LIuTpqY|?L`o|A&+je`KXUd1@)`fGirYWN3N*5+?Z_O&m6W*wi*JLsam<sMm>j"
    "x9BS>A#XlD}xgi89<@JbtO5z8lfEbo!!X$p^pdg;a4|Yw!qrrR07pR7U2h|VOaQS{tyrojGv%u##V!_EvIRj;wwr"
    "f;Z(eNOT^}`QI{D3wM<nd4eP0Ae_x<$Q1FEj<uqgf|RiR-9YAx)1QWH-q80$AMQn;WC&LV3{!GF{S2AmvW)a;X-P"
    "b(Yi<G;zQ1m7KObx{KlmRbJ6`yErO@LbCtJCM&m~>?bjXVLn~$puAzTztmdNiZXc=WbQOhGj|Fb8j2D*xRyP*F}b"
    "v2#_&3-Oc%`lNX<}DOHqOr9F&&Zu6K1&<iUfTP4!yW#MsR08$X!MfKx@HOiG7k$br>ImI>-Jmh8_w&OlkMwn~Neq"
    "<8s9j<~aSv48jhYpkq^?4a5Q@<F8}3c$t6nN#uub@<w{$T!t(rD;OmTpYi>GHqLO-RWjF)R*Sv)Gk*HmJS!mf@Sw"
    "zaF3)rai=2>=ktsw3lO>BCKkIzj4I%1RgTaoe(4RitFvm(#{DkNnZ4JZ+~Y6OLh%XRhsg%!Yl>>j-!9)Uob+n9%e"
    "$xCcTwrnx{rs`l{(k*+Y>LG<|x&9bc{(kptcVG6IjG77PH@F?>R7IQg3S+jCoO(USboLaoiZvd%^Lvaho~J3qcF)"
    "k7h~yZyu#Q!xvp(XOP&#FPLO3-s#i`j&jfH*RCe1kP&%A#kxUsAK&q|<k;GQKN5;MU_zkfQE5*zDHf)qPmdjgbH8"
    "ru*SMr~^1{0@FL9{udfd7PQZ;VfNNRT*$9}nY#Y~$06as?kr@0CAjy3@%bn<f`?Qh1oG+h;RucH5!f~>c3&nKS$t"
    "o?>=tn2#3v-bSC1)g22z_U9<x)(o0+-G4NFX;rr4dks*FDcbvDOl({6yF)%^u#uA0P)#Y1UfrCzIcCnv5{Pn@H7t"
    "ZdAkFe4OpA&{tbHx^qzZ3#1lDk5H`lq8EETL2kLckup=fKyB@dbB_5FCp)8343MjXQ7>57gO>WeoN|dT8iep9i^D"
    "0jwN9{kO8uh+ZjS}EmH&Xg?ug=fUE{(5&ttR?Hjh$Xz9{&RcD{);KwueRlO-cXvGY^-DjbY1#!-SVu6+AF$m%R;="
    "G$R#BL8DC7-njKPP8j#5bH&T!&J*|S-&xP03baE=CHO}VboT^>k%z5Zxj@p;rJ@8Hy@e6$b=hUUSa?bBZ!#4i9Zz"
    "_ghgoV~nx)#0**#AtsJ)oRiv^E-vJ3bzPqAG*KU2=83HLJ4dO-EmnQWfK`R!aaSm`;=A*xB2NxY0xFGM3q&BZ5`m"
    "o;lDKtHuB`k`SRi6IpxASTxEGK1?HX2x5@xxr9CS8hz>5Ks}^%tNW_hW{Ps**pe=OhH>Rux3Edk~n0uFn)Lq6SQJ"
    "}EKmWd1Rwf*8l+&m&?t`-1za}(7Sk1GCAiKFp#UCt@hKazAcGqoi|BPofQ6_-qLCaXn1LUh!u$ggdz@#>JQL_5y)"
    "jb*sxcT5|44?fu54Wv5ZcPiEMC6Lgt5sgNEGx$H&jUOm4BRjc}jo~TEzE&Wm0Sj7*_!8gw40>ArOiTwGqEEvausO"
    "{mmE>r=xR?Ma|~uL_1XrfNHt=3gs}xcI@0+4H+o#*=}`v(I>GembyC5=L{wNvO_7OI`z@)Z8DlpjZC1et{`Vab}v"
    "jv2f}ir*^Kt^(Q9Ew9USy}M0J76pyFGSz3#Zxsp1i768Jr+f~LGp^t)pxI9`-Kpr{R8`#ebHk$EjFxwl}C^g;wYd"
    "l3<J4y>@3#fc&~as|@Dh9@`g^|%FkLeQ1buUQ_URcG9~se{o-_*oE%%cra0kVZMY4uhxxU*@oD$*&8YR6I#}a*x;"
    "DwFaH3Z_?B_iKo}{O1U8f8MJAD$8h*@lm$`Fi>D|<u#s*LEh<#kP)VPHABnNWcR;}cx>JEMwi8qYgBq3K>R=^BgK"
    "DDOfTSMesEs2uw8)EWL|xKkBD0j7Vuc2(oSQaQqzPd1cX8shhlVmmdtRu~^cmA63o#o);V8R><J56&w!^>YuzsI("
    ">8PL6PjkCM_zoP_-?x;$`5$63t@{um8racwO|LV$5-T%eN?vFaj=Hd-+6<!_Kh-YX;i6t&=`Pra72*MyZwsx%xOL"
    "Mu-U$ng+D1SSNcuwAhx+Ddl{-ud6%HXF(h*5d?M}&Lh_r>2dX6GBWNrbHrJfa3%vJ%BZM8aSiUiG0_)RM)9bs99?"
    "zs=gmzQJ;6;%m4=-cCWXF66DXTMnUicM3K;Y&o+VL=3jiP4~Ap3NRvOSM@cDs*!G>xZ+`tJ62*7TJ%rj`cUy1rTd"
    "^iBjAtShDF5ZloR9vuX$ShHS|b0Eocs0X!=Kgia7g4t8@EC$~Hk0*;pn{9MXrIr5=M;y-5FdI8z=1>zTg{6X~Jz="
    "oRe83%gF-8i}RqTt_no2OkotzEQu%J0s}ed%%@FNJuYa_+le)F4Q$TWtLr+bRB+bP7esNpn#1fyCXoVwRYiiiiMv"
    "G`S9l+F~SlTo!yWsqcoW^&w8~RF&X5;xHclne&`G0ta7H1)#tt2!0g?VDWonD|4X((L}*>aU1EvphaR^=w?|Zu}N"
    "yF!AsP;8K@dudGOdsi8>q0b3fcYSZr;!%7YYZFL4R>ZkVQ0`J!rzDF)b8J+1HK_X~Ez3l=p!l3H}HIBZQXS-nAoV"
    "VtbmaH@ijBVoEENXHIvn_i0FVQ~W?l+D=)NlaV4@1UxY4nq287=XK-26~#XkvcwYsGy^7UO{2n{>0c7biUjE#1VE"
    "?y0kPq5GbJ1JL2Po|C-NXy`&Q!eDzXnqL+QccIZ#K(=bkXyR%_G6P|fNg!ipRh$`JHI?z$RKDbV4%7GY)T7U<R^J"
    "I#m1m0rhzE*)l$1}K!5-vC%fe=#lNv8biljuPMQ4IRK`e_^((`fdsxE8T<o6pmh-JgNuQbvDg^MrFY$-|ImsinWW"
    "Mt=qA7d6JAzmuVM*{okG1HBTa9i^Oy2q_HSC88cAdOL8_z?AB4E_lIUDf|u!zd3&|yi`$v?4@^U&Fpv0y6_roSW4"
    "qi3AEivUZa)oniQU0q&gL2pKd`H`+3~5Z5oNoklmmaE(BdmHKk?T>}$FE-p0vooMk)`l6DZ4IIkg%+1l5Jma5|gv"
    "JpoSZSpQhn=e4QE>F)+Pp;S$G{Nm3I_&Mm`LE1mLdLC5cgC~nJdSu9Ha(pCeswVC5?wFU>WQyTISxZ0uIxKH;t!2"
    "GdQ<hbv702@Vel>`@xESw10rR*m5!uOX-Rz71wHc(!C_0>sZP2LlEm+W7zB##;ds(Qre6xWBw6Bt%`3}bdg#!V)F"
    "{Rgl>G!Vmk=UBH`X_|U~vwMX1n5%b@;Lu<-JVzmaWBd!5=|c2$)*-V{L7kvQO+AlOn=Cw9vziL~09<C{7=-hgD`2"
    "$PKZ(o6r?oEgMj%CPKGel}d2e7Q~d{K{H{9@ukZ|OnPyhRE7AT&dyJM0XbT!77XQqPH|3z;FW+CQn+_4NIt338~M"
    ">2L!mI-LZh%&tMD|<LLFE4t!o_itr~}Y0LY>{wNSfrk^}DPFTgcn2nLBk5KJMMN~hf4Eab>vLBG&kyO<lWPKYK>j"
    "xRwOH}xVv@V$(?INND4jbB`EA&9<QEH?$uHlY}nIt{4{BmUNrsOTUJUFo(dAHpV3b#%UxuHw63y_x13y+gqVV#Kt"
    "&zD-{1!zVID7BXpaL{@I7>RPzD)Q{UM{g$Qvr%QY!X3M@8oL>nhMN=?t;SWJfcaV1M-1oa#ya@HNDe?k5VR1sS+t"
    "i><MxLVk>V(f?z$Pftg?A^q0T=`TX6CwoW5Sl<u%^O>sZF(vfk0JsD%L?f<0C}_+s5W~i1Lhx$gnBkYDP#$uZO#3"
    "6PxIQwDHl;j@24jrolzwCTxgFH!Vg)e`2x7tF{n~+F0No6!~#vDI=$6g#EP?kj_~y%~2s4&&I7!@C;jj9QMX7VW_"
    "6q3B_bOR)eJmc`1<bL%VQP%Q0EGrcdKmvC$AtE*9|7&OjM#q1xnPO)!YV#p&DME`eL>l!cor>!oc5i=bQ7kJG7+f"
    "#{*&pWzjV;tn&O6Psqr=v(XbN+;8^DA=rL^162;x6zX%#b*{#mr1->X7vJIzfKVGc@#7#iKt$iCg_t1aeB0BhG^<"
    ";^T78|q>;iBwYpxb^J|c%z|zW7N3cZxaT?}6PibXr5{g9*Zyr}wvfgMo1p*~~nu2Tn*ERC8q}=V!TFF_-nwy9|TZ"
    "yC3BM1uT^wCo_YxI3Zw^r@u2MHO)9@1x@C6LyVR^(AMK66-x7Ck;qcoj1VD<x-b#Cl&*Qa!Lrss}^n=LtgOmkD0o"
    "nr$)VX-dJea<q;^=T#6*sYhXXH024XIJ4EZVr!g!mtg-VNU(N;JyB0rsk?*$pEO~p*aC&LTL5Xkf_!Xu8RsFtO}v"
    "E*$d8DJ%F|ptcjRVw<A^(K8HXrof4DgR^}`h#Jr@AIklynp?435b1<$~3jp3a!>JN6CVpGz0hzuMu?Q2VrN=s0ca"
    "SM7%FIrRwwhAOMNZkpA$U>OnW7R!&?q&8*GZj=vP?#c?jvn{&V@B?>FsGJ4poSm3ILJT6lFoZmykc-IGEjsD(QPB"
    "Bo@S~Fs~6ANNR}wQk7u)#D<RH!m69U8@*Hjj7tr!9><-X22&AWm?f@XQM0R9zZ~}u(-zmdb;T2sCw><kzbg*SZa)"
    "^FPNe^lR?_Ydcg<k$mfbxLI^LrjKZwkKFA@?DU7<`N;U;?%+9<Bf(6@rgHPlW>0=hCSi?tiNcp--=6=JcL+su-5i"
    "B-(~tJI__egDY}<P!S@hAibd{$0Ei7PIB^oS+OuqYh2CcNfO8HsMljZk|scoNe>POyD#v<;NL=yk?5g13CE&i5rH"
    "SILe217(wQ`B0V*1RM(KZ@<gcWD5o?m<imLXaUSH6*a0Q!dRLVMmXH_zos7rsMg&NEwx3Ji$8`c1xZ6?vy$XlYyu"
    "3!O+2OEoDRq3Z>lXh&vw^Nk_wMP^WP;_M^6}2Xx(Kcie)p31ZCFcQTSJhHwN6fkHb)1q1?6au>zKodntQJQZ>l43"
    "`MKoV5Iz!6hu%!xH@Lf$hY$TK#5nZp$)=ugKV}TZ2L;G5ASpD9vWUY>ljyjSrX!m=4{l}oApL>d+7^C2;X;u1z-A"
    "DcA^3ehji+wbSGpG2ns-l34Bk)u7a~Rl^T;ht7QksY=SSa4$V?#$zvKw(k#K#ULYc%W+c6I7*XztaK-%N2Y1;QQ0"
    "SZ<}%^C#UJz1|xYCMSq8@2=4Br4Xk~jk|7!En2NfoD~e*h+X#_*6;1zl-H~jTnFL|^lqxbaYU$r8r6p-`kzpS1il"
    "Sm#QymC^x~A!(I36II6Z#z&ll|c;?3y=`{|$Lg3Em;i64O7s8vMkPFd)_Y$7|Bpkq<k4o8y_Mu88itm>puHCCKP%"
    "BOMUyT$OE7Z#Ag92E(&Q<Vx36NeA$JK48%vZz|1o2@vBSr|;QkUSjN3*1Snf=<Kms(aa_hvKp;CLHI^v0$I7Bhd6"
    "iR&`@Z3stXmq+V~g?zSlv^)vx=%)!zJ*3nvZdM7FdJjuzp4g-^FTbO##7h6DtxJ#u@YDm^)C9_-UL$#7i8uAls`5"
    "anzoM-XEg9tsqhD83BO>1`uOd84_rHe!q`9#!g0|F+=mD2OsQIU_(PDPRM+xuVMpa1dR5-jKP^nE27QgIDUd9chH"
    "6v~m6qMGVu5MZ-Z(9^ph@<%UJue*ZNz$tp6)6umm=nF)1LQq8>`Kqe|$4x)JLCv^AuFIJnv3^+zUB88;0{biBN;E"
    "Ci&W>bSjLl-jd>ApE!{rF$MX*(zC!m)=7Q(043&01$;89Wm8<@sW2^Es6ZsU$7af~by=($F~mO8Q<%IhpEcLc6^{"
    "<<)Z!EwA&1KzR&jaVE<pA*0alEMa5q5>MMx6SBOukXOO0pk%G5wiVACf5$YDI0`Ds9e$jS(r7NR=GkcD>fvXb8xj"
    "+SU(wCEG?jyJD6Pw5}G8z0x#%VhD{tXB|w>eo3OVm4qImLwZl^M*VDF~wh!fYm2v(d-Ul18IPLQ2K1kw7_^e-^|9"
    "*OL`tBd^-Q$0pzQ1y>PR~yNadG^sdv*TH>3d@Ti)ES$X=rUV=O0clj<3!yE>#WPbQwap;+9iRutI$k2~|KG$7Z@g"
    ">Ib($*6!d*1|o>hAs%{<TruD$Tx`^>PVKyvW7P2sR}hHAG~vi0c_9hiaT*}VAj%g!38v~6E+`2!h$Kf$KzZ3!IBM"
    "V$<#B7{7{x2QSg8%rHaJa-s0qi#-l-LfHxW<e9rK<)NPSPE+$l5T_^Bmw@_UGXSJWfPE}E{qBncqAgP$id%+MsxB"
    "e-p$hlN7}D5^bQnJj@?fjJgH1rlrkonxNA2(pY45I}6f01~YLxHe7E$5++{f#)GmvV?Wv^$Zs^yPE4!lA#xp$rl_"
    "kbP}C6x-x1l&&i>C4ePR*ASf7>(SNh!_ixH#p&4t*E+n$EcfY>7VuPM>LAEt*0Qv|3zbLLgM`^f->3}n5DD%=%{0"
    "+fC(#UnXtE3B%h)UwK-Q|D;l)_|P5mMxzrfoo0X7_2W#`2KPFyF5KOS3>(()5<GCd%IPY22cl+%N;Os?KmIT73Mn"
    "@O~jg1iZY3T$F9W-@ZNQ>7-hT9iw$}kkN7VnSDo067Jnq8i6>d()=X8?^JfVm|-(G@3rm=d9$tD(j;05G7$Kq|Aw"
    "<5Vqemt-Z-5#f{P%!s*tu;rO46Nyc#sr0{oI%lWN3yHi<vF6r!a7(iD?w{VJWt(jF{n{4|czEXhfQl;qKC7DOo|g"
    "F_;#LhOV5AB$TS=|y7>4BQZ68&+*9>f*EtJlZ7njP2EygfLFDaq99GNf%<dDjIrxZ`n5^B^g_`oTYjZlc@BW@}IP"
    "JO+t;t@V`9b=+KHdIxG-JlxFB(u}Z)KKlw69V}J<KZ6+h?!jX8G2bi4918-3ulb}2g+$hZ_f;%W4tx^jbNj?Y`Ul"
    "^LSSq&<)p@tcXVW(~KHD$;GjaPt=WhLp<iyZa<_PDL!J}J1L<spa2g3~((lE{fCU(xSH#*1=Er&xrn7=FosXU`Yu"
    "OhATe<D6|8;A~U`IK#8`JfXz44~5ng4$Tq@ZS#0##bn8=`*Y%xb*#b1sQ%7>Li;6jI#1GkX_sbM*`o_fP^_S(Y&s"
    "7@e<SVJUotkzgLlW9?8_)ESA3+N2lanoaZI0>i2p)(M>~F_=>C@wWXPS`M{)tzWf%U_?yw!Ud!(t!i@=V>2R|A`<"
    "RxNt#}|=f%zz2nv=W>U55B5@r2c}_kOA)+x@5dcNBy34G`QLPNjF$5xE}y005?*>>Q^Pts>=Vj4{wgIPML|^g-F4"
    "dr&nz0LBhn58Rtf5@8Ld0$tQ{*MrK6Bs<T47>e<s^e?Ze3OnONK0jA6v^FmEtP51_3m4MN}LWt#s7XB4aYz`k^ZE"
    "AbQ)Cye*?oQk6T8(SsqfTK)*=%XhBxT;48?913h(P3_-N54YuXxfGVMhEH6-9KNdC3}RzzcZ_`G*$)+NzU0A~hhk"
    "j~sv~VU50GD+Lp^tL=q(9CA$4Dl{K4W}lx_^&O(l;)ClV>x$rh2<cS$q|6~2Rfr(@*9zR3O2()J3TcWzTE+y{h91"
    "=m+FYn)Sgd*<9c@MmcDr4ojT;ga_9KJNm-j9T0-{P0{&**hAIdRmj1hLKC=`$?Og}p9Twx*YRLR2SzM$^F-*9hG;"
    "V174^?Adds9)KeI*5WH<kqd_bJD~hf^!E-Y@mfA|I_G|#2ek^qZis3Uf8xv-Ew^SZuYn7=5{xqmn?Wi0biDh*M)s"
    "r1OL!$L9Bw3xZ|rK2{~14*&Sawg*rzwtBJg86^`wWub|{7*i2VHizE5Z%d690FV4@e==asHAKtvX5Yfwy-~U7Wb>"
    "beMosC<MR!ByJ2~``M!1Y@$tg-<RQ+eWlG0;94uFHka&VHqWqjEl0%e?;$W2=)BtrRtYuxU2Dlwz(#agkd}Cea>>"
    "bjTq4XjLw9KobS&RHe<7HdNGB((b@Yr(VR++Dqv<xC+9iJNTmAX{4!{x*sq#v^l8jbd`#I3hFUfoSlV;6KCo|L_o"
    "CSPb6LRX8}k6!36&9loOQk=zgTFUM0<!4_T`9&c6F_S}nwrWKAKk?O`UM%Ew-kxe<SG1rV=Xs1`xBUNEZ0B=EWCg"
    "Tx{QkwqNESsVq^c8C4Q+DAQ0jOtgN3I<dKW!0aPMzT`v|0)_K%r;FCT3b6crir4NO_{-xG0_nLs)gyuW>c_brKVb"
    "l%*IJ@8$_cQloLa3^r3d|4+k%7wdiEB`WAvW#SfbDySS2xXcb`<6%PGzXzy#ugrn9S)*uZzU$%SQ-k{V834;Q?dI"
    "4y(c1Yt99A=AP0U1>>X{Z>L0MG-)QItW4(O5Qh$?@X4+KMJA0LeFzx%y23Z?}OV8=FQd7E61jP|}F&7lz}4DXIV@"
    "3m|e$x(;FgK)s@4OCM4i&5d=rYL&S)%-5mA`iJ`l^JOmnwX|)Cg|^Jk3*ix;X2Akn)rRA7w8JW?d=EtekpHKD*xm"
    "18j*sy;x&o!*P=ENMaSuq=@V7z@Ct$a07(_$XRyPv~3gl2KzAU;@`QFYoZ6l2udx?^c;O<|`R5jC&3fdn2&qT9Y="
    "5h_MYWFM<(~KJ&XRKGM^^4;;x4?4hC&Px`+%nLNeLZU}#cQm_=AKZp=a8+Jubp+Zk<Ll171Y@*o2{*{(0c2YTKvu"
    "IpM$qr=&iW#ikJ}=U+V3qg<P%HcYWP-Y*&wc8cJkxO-+vt@0;FPEb|R#yP{i;ys+W~3@&Y(GFq}A<;F$HwZyts*v"
    "Nu4b_DlJnVGR3$e))-NK@J(ui9w8RHcX!rLoM?4f*2|K)?;%L^s;bGxx_Puu5kXQ4N{Hra&Qq)HtkNeIr}9Mcui)"
    "I{)wiT^BJYD|EK17x@FdQWO+#8gefRS7lYP2}S?1z=c;<;KHjRC2eHha+$>UUdYlsxexAnDt*!%ArHipGzQNW=3&"
    "Mz$N@a{BJ|znkp;D2fD}lk*?kUdf^g{7;0fZ%!i&6H731WYAPmZ5eKYidl*Gl?m*V$H7=To}4tO9gK>0BkfP?7vL"
    "mUPW%Y{}5!mrXj?T93l9IRlFI`==3cm)3Uzsm~%R%JOAu2^Rh+Ethj&tEw*grkyw@iF?I$S1OvQZUDjv=1c#q@;%"
    "^qt|v87Qdd&R@?I7&W@b2%1cmSpu?2qBbZ!EZ9QuXa<;0~;~PT{ul-%sguFTZ{rzueXJ(m_BE&2sf%c{|bE8T^w?"
    "Ps?p=7L{zv}XjK?(_~gz@Pa^bYlcvw(A(4O<g=UgQx}BjagI1;tcneC7oqhJYj0k0FYz0v`IM<KG^)=2^BJzI@pq"
    "9Cmx%UbjzZW$Fw3*Tql;oemuh<?&wP3mWhF>K!kOKX^fAy*IbK!<+8!+O|}T2R;M4Wt%_}D*w9CX?iEC7QOobgGI"
    "esITWS1L<<*6TE1hvuVr}*h=Oul9)SxB<W>k*MG6&lso^rp-WJX-2Kho0ft|pCsh}-iIa(ntJj(NE0BhpaRueFYj"
    "r(e7#TC?rc~UZ7NjC^rh>3ES_3vOFyHa?45;s8s=Y_<|!HtDqlAnXk*pzvYS7fA!KcT&|l@X^^h8gmMTb^d^Smvn"
    "c*i?`**vJ!9093zS1TN#5RVSRz2HJp<5UjjqN2ROZ(nB-uB`)P-$6*@&Yc#+#kg8Vdv3%F-^_q1!*l@Kc8@6j#>R"
    "1f_CzzGamy;~0!_caNlcdAGUMg-1aY+qwKBm4ATN3u)LlV=WppY3F<Oat)S_=M)BQ;D%I`HR5cF@~g*mE|~n^|TF"
    "AxV<k76bg^b5#FQO<u$I;!ui`ora=v)+PF`zNEPx_2udo%6YDps-HjWyfw_%2J=+fl@@uLrbV4}TOIP9&2Y8Flx-"
    "MbdE3jadG}v%FhTknfkbyZ2zk31!I0Zt68z%wDab%^WgEM!vt}p!jhzrC3phapjj|y6m%s_2iIt@5+XMjZG|Rr=e"
    "+m8X1sP!e%}aJm2tpkUq2^+%;L5~h1{ejgwS5<u-*D8c+;DQnI%~}z^(!j)N--;6ZVlCr>HHNBbS<5G+F|`0I~GY"
    "`eYTvh(f~lzBFDM_4uXR<z)S%L7jX`b$he17Z^3c9+!8S2%k0+Y0L{>rp%HAvZ5}pqo5rGt{uX9z#Xc(gHE3x34c"
    "W+=LsoB(mJqmn8S-`<5?B-Bdz}7$E&`zSKi5(wM<nsD#P3z?VuE2@V;vIKuii$M#0ywabfe=T_h4<6GLkw|B&{gn"
    "aE)jo&u|+w)?6LoW(-#?vn6(N&D#xmthMB3Q`Tw=wyN`VYO4k<$0vSwo{2yImizK8oJhbLH1;yiDEMX_ajl?-H>9"
    "r(LSnwiLk~k$fL<EM^VLMf1~DizLwnYpPbjvD0MvLuzbW~L^j~DsksGsZs=9y!puoeH+h5U5c)t#IPy;rw+#V|8n"
    "bgpV+f~HD5GuZZi)dF?WP}JQ1&N6&*MlMkb+<#!<$yI-(OAbPC#N4U1giDBC$tasismXDQG7>L(WY%CU(dYSN&J8"
    "gW;Lr_=*)<sc%gOOy{fWV!`ed|8q^+sLNGzvCSu~OA8U{_`BDF-WBOM@9fzfm3touw=SZ+z&jdFz3AqE5E?Y;`w}"
    "CC%Cr}M$#M(W9HY=gGi>SMj)ED4Jh(Q@3?mWdX>jGDaSTaQO5nSsvK$Yq8SPDo`w-)|YKEf0w)pml_>eup)!Vv^r"
    "FknI%PAGo-gBbc+7>2Itu=>qz>9{Ga?b3PEm*s}KSw<Nj&=XUY>1-V6fV#K|I^f8P4mcVz527-OFuk}KG*k~`$is"
    "$R#!<>e*eajHw&YO}o3Dxs_zng5f>40ZfB-z7>0jFiuAGLd`Cm8u%Tm&&EwTmZcZ{w0|1ea5d8d9wc!26%5-)cUh"
    "_@pTwo$=%7{TYm2y`N;XoMg5SlxtA;{|78>7El$VC=2`iNFHM5P>yZl9`PhPd<bBD)e@J6<)N$dkNb!@rmGKu^GI"
    "eo``<C5QC#Sh{1(~7D(oB3tYjGitt@_5Yz+meKxSb!WVyLoxqb7eJt^lWbb~0K6x8Bf)*vOv!RRp=NkWe7306uvc"
    "N3rVf$zxPu8TBHv@$lu?p^bt6RzLqSC7Dt|EckWe)KjhI_15Q6s1%6+s0h6rHYpqiUFbHSZQMU1&OzQPD8#Rw7*s"
    "rA;Y*h<K9DgC!k&=!zFaDL4rSWuxfdn7~x~9N0k=^C7?2lp|gV5KJCR0m=kEFj9i)_cSWo{c`5(CdJW{_uupBjyC"
    "B+t@=o2?s=;5>&p@=aeQPRm1!JJgD~(Y&Y5GILr3)Mn>mOw&EIF8#M<*MYOkDAeaxw;Z=vKNd6d<-qiIv2v_>ZE>"
    "+7gd6pQeUs8RYos~V->8%kQmJO=D7C{uv;IY0{|HUnuAR4rg+#upgS8Kjal3&N0j;KluXks*WI$P2%OM&>`FYWd8"
    "Fk$*KsO_6L?xDr1}a|1^Ygee00v~eHHbT{efmCCo*D2<Ea;_R*q8=xIZ8FLYvZJTm6z8hN8ZI%Ly*v0c2__vC^F0"
    "@2igkP-4XW+=Cqrc<OcS-g@CP1?K_AHmpY=T9+i9<adRF;J!IRF_33U@#`Q<2)Pqp~_c^iGevPuZ)UMK)R|v1}rr"
    ")ZAImBX8((MqyKWCNV?2UO#+U(4JSwHhLA8QP*(N#vmPDH(M+vqo)dYACe&Bq~CdJMC>Kyc#ScH>N4=#9eYG<Ihj"
    "~k&8)4c49^b#b_3s9rf{iOC5uPaFT|Weaq(w4LUvsw>|(ma_1m`3FkYMLtQJ(Ut+}Ql@@OZ9aH1Wd@hj+MU#h((5"
    "d9g!XVOm}+>sZQ|H(*etp^PqDolbP>DpQSB;(&gaB;PxNUx%z)55zn^T16r&z3;P9y>;Y>?!3X6SFQ`YqaZ8efo!"
    "Hm4%|asL%qcDvn~E;Ncj-g27^lIdg>{5atCDb0{N44V$!9ru)!FE=1bO$-ukNg;Jbxt9rL`&xmC}CN9mVQ_kVm@x"
    "XJK{m8UxD+vcaiH}{psyv8v?g}Ie%(3Vokic1(r}L49bt^O0lu`VB{GLBt$Ox%JEj72uQYX@L{{Yby9QMNxcMtHF"
    "KD{-A)Fp2WD<!j12+VVkVoE}ZCPuj|@tb_B9QK2QtZ|{ejkE6J&JPl~luDu!MyIDlt$ih<)?ODISbA`&aLlHEm&_"
    "piMU}5Ls#ZhCY3f{`q-y;eJBP4dDm<71{^AqV!C*9g=?pHQGiaB91<fPx-U~ud>2&`mMTDctSRc&H60M-gfG90)r"
    "9GMOG!E~1yJNp_cM87HULEelnon!ZkNOGf%1CjgGB;m6YFd5NwnocD#e!_P&PzI);#Mz`V;fdO2yPGCKr;zS*1Jw"
    "Ur+@E=uWeB(231v4oS30=t46yTn?w*NMa~q{#vlxvR6^&oY-(Dm9nwUSERJ`$mxL=3%f1>K4vrw?qPOU<aPR=jaY"
    "?<<rhmGZ@BZ=2yR)-S-6yvB+U?Y9v+yG`hR2TCR5iZ$a7}fl5xA^(J|~_`hMz|sboH8L^B|>E_kPS%VGc&N9JbQT"
    "OS7F>oIH4mPbmsf1KwS`D|HFv?`ky_4}8OZWW8>0zoLKEQY&E)*$sVJOdi210w6ClGA{i_>Y`-Gdf%2ON_x&Fa5k"
    "EXy6|_xa3G3Uk5MVUt4i&)wfb9=Ye?H?*N0o<>TTxgAv#A|*nz{!i=>8Ks-)mBSv8`Vz&6wz^o<XW2$^RWpt3lh&"
    "f7>k-S}?w)(ca<Ni3jxnz6qf&FINWt6v$DqmgLpOy|0ZO|MtO>$O63#Fm*g!W7XQL%zECs&>CZbySPPwZslrD=sO"
    "PrZ%{-c?;e&Z0o-YoVLdJ@mbCsbwT&^?eh7qRa&xh6>_|C6;vsDr%G1ey*WEAPn%HJTD4A7guj8pf(#)LM~k=$8F"
    "Um)9<Eo(7E{zAtm>}NV971Fq|lsJC6<i3$v+0DFDcW64Rlq4*p_*#T1}XX36ae&3nQd8jhsBh^3V-g-(IlT%2)_u"
    "Jy^>%=@Zmb>!%ROn6gueyiP;btJk~LMz6Eo6SeH44f(Y>#b0Y(eD35%x};WQ%3kwDLDtt4EHdnUc0Os0o=IKR=3c"
    "XJXayW9txkM7(9Y8m6_I$>V5Zem6%{7hN-j`fS4x^AWG^HwAsrH_#vEoViAO>eB*w!`FxmQrEVR^VX}KkL1JMoe6"
    "EP3@O)0(b8Mv#FE>P8@Jl4o-K~&YhY33+8rJBpW5kbVbH=VN}jYG`-0u+|q8z{`Og|6HfVU}e|MoWg|g$O+ohN(<"
    "s47xnX@rX^N`9d~QAsCH~$X!`v04c>#tYl&>Wng`7(|zA=y6+F!Jcb(yR8%UVXX>b2&cB{~ph)~N(hW@N>4m5e^#"
    "b89|75#;VQYU*^ZNT((mga`d_7w`|ClA73n}^vi@6v1llY^frjK54Wgma42g8OL88Q6MRh~o+yNcuR#0$fkZ&Ml!"
    "4nd!w<tm%UQO!q~u@J)VLQWd_)u~b`LX)t_Kc8P-y*oQ~-<+TP_Uq~Ut0GUDMiM4@2qHu@R9;w=nk7hC7%VW<2zz"
    "%Mfle265;EWL3-LPbs%ZM-)^90iCgFfscawYt8Fk3JOND$0SCCvhNGbDqkSYx_?ET0vN}R+CNNfQfc{s5{*&h7wZ"
    "JbOY)F}4@gv4aAI(<;{YqsEC3IQv4G=ritFGeN^Rl;e1Om(nKjn$(_?2J3kZvW8p0K?t0pxl*u)=JD(Y0px5V<zN"
    "GtGVsuhH3}?Xx#GSX)YyqAZsIybnEXVpOB6|J(iUsW{p!X^TPO6t57^~7t`g&RaufBK;_bp&&s8j`!AAj+5(~!T@"
    "ZOLhgF1v?vXi!9as*;+_CG9gBf17`Z@w81rwjal634y6LsdP)QJAMu2gm7bSfN@_HhyZT-q?XZzh69QX#Z=!rGE0"
    "IhoH;!-y%OyUKJ%hv<U;ne#Nez);<qVb66zG;&?B#nU)Xrd%H)JnzzDFn8b|-^>{iiYL9kb*p2MBxt?tssZzGP^5"
    "G1Y!IDxi|6Lnq}hVl<i#vLcD9OtQ5k?f*y|nS1&y4uUrUe?{E7g7e#IQ7#I^=;)Rf57G^dvGnLf#~DiB$wO;y}AL"
    "!H)|##N7$`DyvWHJX&4vr*|DZ<l@UY}CD61{?Jta48Z7aDJ|~UiwPs@XR-4W?(J^_t$oG(Uq67(wBW2G+ew;q|AU"
    "k+6nGDOGL#AQDz7#HVBPt9JS>{IqV0MW2CHk)1@meIFbQtZiO<*G8;650u*@|s?Hl)Ui+=B1D}znCgp!xZ_+kmZW"
    "_!aHzf!r4qi`uZIYjYkQ)=W5i#G$8dE7wy&~~i=E%O5dk{Y@Z$q8M!i6`L_M*amslsBA)Rt(V8t?y8qLOdZYQt=Z"
    "mL8!$pDe5jJUIFJ{N()X`0BKHq=&|NtQ-2^M${T3lnxaXPyq+%4INdK7@|0HF%Tjs2_CB%2!0lP^RmQ%pxCb3x>g"
    "n6*s`OF8O`QNoZrq#vi<esg9OnkU51#DPIdmCH^odzv2D*W)2sUFqN<^|;)Zt5kMm1iY#*}s=U43FxA(6Z<o(sJN"
    "D%`eLY07r%A#cuK^*B|fplWSK$%7U2i0Hro{cmt%=NfcP9=DG{Qk{P=l|Dz_v`ULPK`sCP7{<Og(7XES}sp6j;~I"
    "BHg^DzZVC0RfpRF*eYu)9klO6Rg=1;nyCe$(te5_3<JcV8M@O{rRWpS42fG`^5j5EXsaYEqjG<&6cSN#31-?S94S"
    "=bH+1QZ7%?XlRc!ev_ltNCNj>i!MI2kFT)<$H~i<d#P%(IuE-ay35i%#d7lH9$x8ILOfm~pELI26T)5#rmfUx;aX"
    "p^-X_-czj$(!^cANbm9&HzRW%JI;$d@LvoGR-6N@__5Q`YuJuiFlC*#5NRBPD-dxHtNei2gd_29$DY<5Wv~(&N8D"
    "N}`H&^wa2$hQXN&*>3^_m#v|FZh=bfDY`r+)f<hNH1L{zOuf_f=KFXBXTHw{^TunQY6Cqvl5{{HTs<t{i8n~{`3l"
    "A5E+1Q7D1dJ^~{Mdgr|_6Ir^N9d5mdXcnL*}dck0^HY-Ej@r$miUoRWzii8!-&X330p?AVkBusX?Fl1HgSP#9}zJ"
    "re=gwJz3#r950oLKXk675yL$KQseAVB*LPO}IZ~9wls@@V6`jg3Nc!T+1$Y+$)EeVelEe=8X0=hrTK`wRRBe~lS4"
    ">pYAJ`S~gCXN^B*42D+D3mJ2$zwfohME?n}h+nY{pqCpm1Cux5T_}poyP*DX7@(n)#~hTf7Ld^mD4`&u24mm%5zC"
    "%U>x=@FuEtni~YnQ#B{Ym#3GGnzW5-2^I+0Ug*Af-aVHZk#$OW3CxzdeK4_YtY-iD>gvO<M3Sr;_d@&iHq3dH{Sj"
    "nyh$UhgkhX-kR~2@rVB5;(pnnTeuxs-!`zc=m8wn4~nz%n8djQeb>8f2`y3Uh&g?$1r@{%X*PFH<c{-j|X@Uts~9"
    "Oe8nZV~te6KA4KktZ?G1BX$0P@Rdt>B@1l_>M<ub;QS*kMr9ZZwYN|A3eY%SZNB5@c;CuW${^?8p{h~p3F-|+puv"
    "m34EVNf|nU?pm1%NFDcYSt9FeXUe&;Es^>N}q%+xZO-U-8I;zHlHJWh9XfEY6w(xx3HT*%ow1QLSWp7e#)_p5;Q^"
    "1NrkpI!R_2&bRcGrF=88;0c;;=anm#BRPK8u6}u?fUAMRC^y4Jfg(@)diEb|x#4bWD2XRCcDQ269{F<nVYcFOat2"
    "7Xe<7j@o#=T=&2LLc0wOaIoXB3pa)@D{LqNNW=I5ss%56rBqSFmJN3*pQ}$P9HEEE7z>kqar*zAo*<9CQPuJ(=|X"
    "U9N-2blNlL9mv8#5k61gRNM|15kOeM236|;*xh&n+#3C*yKxu1$;#zlXX3n6eZBXx1NHG*rKePcNIu`$2U2^*P%D"
    "UqekVJn%(TJzfJ|NY(RAMVBJ|M~6RMIq^^yqGW+P#=Lp3Wr2e|1?futCRHxXJ&1C(ko1g(IqDv$Y~WJyoO*uz>B2"
    "g7XAPMI)Ige1>U*ucY%*nVFwY5I3n&v@F^IO2C-+v@JU24wrzNAr~`!O)|BoQ#$T~Ibf!kAo)X6^kpN7W&t`D~v?"
    "c;<b*p2lweTAxYKD`dg?rRw9&sA9%_TbO(6G}{8~=4W(2*tg0C}%yTuNyb0P{n7@zN<KMYuYsa#xjMMaaCP;{+Wr"
    "TyClg4#dj>AXToYRMWBA8UmZOjzXAcMU@Am63m&44hQ1Em!M3AjHJ^foCTdssHzqyQl~D(tmVF|PSrMZ^^>TM$!d"
    "0}8YZeAuAQqbt#O4Iv9nC#c-CZ;TjFh|0t0A*0^tei@&jj>lEF?cRaLMR(pNW~dxQN0%#%r{YqH9C+U|6^bN*2TR"
    "!3b3{oSNZDe4d>w7fwm?vZWlROR?fkGxs&6p4}F^90;Rd|Unrc}{66hIJu|MG`_yIj}5%q*C^V$}IOM9{T>*5X^T"
    "C!TbX-fsmBUN6N@<^T5Y2(m|@Ii?3p@PqRS8+MxK{VL0)ocU5`(uPT091ZPUN<E9NlaINHwAGvAdEz^07{x9B|s<"
    "uSAL8R_Xf$+%Z-NlF7!{SUy2TW4wiQE>o5+beqG4nY^8wHQ?sSE`oSR_Jrc?$Fu&sgY1x4C!Ai6v)$=3W?Nt8Ktu"
    "Pmn|FKQ>Of(*JW%AxQQH;JF}XcZubabqNkrnIX3ax;(FlzYejIsfDfxYg&F!lReTnpU-E`Iyw<In3`<?C&f{1y4`"
    "d@dU16<-NT<qcWUOl#z)1*m75ojdmD0{VBicBc#LAWoO6&&yagf?%D0OVG<!B~eS(6IJD)_gj|S6Qx<BFE;l(Mvo"
    "2zx(BhYC6Bcv^;zWPxQQ&S4FQIr|C#^XqIb$vCWV0}&c6t1sMFI`_J2y_@UXl;GkYRQkPSQ4$~iZ^J<tRW;6?N&f"
    "*m&P<Sm{e^Zfg1haHc6Ehl%|Va>56z$er+<FPxZNL<aQp?AiEd|rm47C`Qi(CYMMS$T#HMLCVX9DJ?lSLD<JMfSY"
    "j6zyWQz>^d)O|>c2KP*v3xIIQM}`a&?rJxEWspC3`tZ0zTX6Hzp0D9S1xze*X*SOK~%y=g4oDZ;&Hfcz0X`0f|%4"
    "eWx5QmMQ3_qG^D+IvQI^r}0ws@m!$FcW{6DECViCCU<#Vc*|4zM>M{w^xO5#Jg&!CimOVnNqQW5AgALN0@}2*s2_"
    "8yovmGVMJqVEww^|~pu%wFVl!n%NXk5^;X-NFFJil1z5D&RWF+oX2Qz3Mj3gy%SQ4$`iRYt(^+sbHG>@?|lM~NxQ"
    "q@(;n+z~OHvz)cyOGD6D(G8mtrhg-Z2}OD=vGN6)tq6a-c=x&D86u}XpLi`#|@oz8W(bRvxUTyyXJ&ywcp0^7R$N"
    "2<#Iypwy?yOt*bCv9<73+y(s6FE7BPz%Bnkho@3`Ip>tG{(WN#Bo3m`v^Ru(lH||fzC%@Q+b?PMu#T61R_vJ1jl~"
    "kot%Ldrn^dzIbK<GPR;N<)FaT$7%5JpXakxupm>6cunM%ATVhh9;lKn*D?()}q;*PnC+pP?Zyg=bGBP*0TBy<J|6"
    "GV3AJ(T)h^sMol?5wT<(D|e<V8XMYgm%8F?gesky)S9(E{?;2q<X$so`m^qf&F+phx&Gv(x!(9{?5vP)ell@`muI"
    "+vx?uIylX!V`d?q8f$RbJ)W&u3`Am=t0u`H;o%89kmbCMftxy5RyuG=Ybqb!wloeW=i3awYbjU`S-yOwyBxxuz=q"
    "v(aSF_Wb$rTpWpJ@I@Zt&#$X5mqzQJV+5&A>Jg$@up*FUaewciDyo{hl+x>z<&!)`(|w(KJTH^XlJ4Ta1}$7X-s="
    "u&lm`;tK=vE=~!hAo(Q#)8jTXv%FYQ?6u}ypM;sER=nn(TLyHf)w_!YKk6S;;0H&ReQ7duWn?~-h8I#Zy5^DA?i2"
    "TuuI)U$n!LruHC^53DVE0CB-@-4b_rg#v<spXZn@E{`R7K@ms|sVYL)$>%gp_^@ZO&7Of^6yQl7_-qhCJ-lpo(dp"
    "+z0nO6|-P7VaQ&au{EC4^M22;D;!glwW+!;FpQ6vOy`2|1B8`g%T8ergkfP<kUsfZ5Ui?+q0ZO-KOgqKtSf&u=X}"
    "s{rt^5Yxu?F*Lw;+(2?e!y7lHmtrXLnPKJhXR*DCc|D&esPslE9#kJaC@TMoL0ZxaX~7u=}?#1}YEE&RljW8!1Dn"
    "YJE;R^E^h>C;PY@2>}vJ20ZNs@J>X@WJ3K-|oq8g>kg}e*dPkU37UWEs%L$kjYhO+m=SZ|Gg-R^Jr>kzqe<-1>23"
    "Dv8rkdvuzfrWv^lKD0Xj}&t}2L_PEuRY4HrrGui1G$ifNtE1oyx%;B$3CRj}>h+U{j?Wc{pQt#gx=BBOX)X4-ZGv"
    "SGV%BUj~G4ezx$te%+YerN}e$cN`g>A~!R~<2coi{dAM^7U(D*iM!w7xc#2riwPXw{#a2BsiZU(=vd<5(;#-j&;3"
    "BmlHIkUq(MG`-6m;jiPUltsv~6|PT(!zef~ZsHXR{ka8oF&YUcsUsj`AXSujkiNtE4%@GW<!twR^{@I48#oZZq55"
    "tQzH!*V_T8Y@bJ(CqUmCBgz*e!7@y5YzEbgo}_<U8oHEFaX`llx9ZXq4PoFHFTJSl>dN(Y^`Hggs>|5#vosE0BR+"
    "lrul$b#vS&0t07-g7BRH7tej3Po0JSa$H9a4-&`m17F9RSd(X*C68TNup3mW9Ny0r=}MiJ*E_+*of&H{~>|gYa+Q"
    "DGHGa@sOI=Cr<76IHg<dEoPM}$Y_!n=?)97ULrQK$*vS%vYl;RO)uoaA!(lwlf(7XFkev`gXb(3J^7uvC6N;X?P_"
    "?Df)v(z{&$hJli9y(3ZnQvyI(t`jI_%}_bF|(rB=SG}4i0s;)DIHfxKZHfnv4iiUkLO#p3PL!^vd=ZY@xVc+H_n&"
    "#oHCvf8`6sDq6lVGM8vU)vIy%F&6)j-B+JtBz}k8ZxVxF1_6J*DEy^Bl5EpN-VHJNH;T*ul-T^jdJIIg)=t?Jpx-"
    "1*4Hdv9=`_5jEnzER3oI&v>^pVwmDj}X-#EyBQ=tEiXj3hxzQ2}HuagzlGw{_+;4<w0S|+|k1!PTnu+mPa(RN@-m"
    "&PNXj08gKL3g%H5ssp7oqE4nCRlH>*e1&I28ljVbl*75=SJy14RgoEZ|~o~1Jbhg2GETQQV)Vxb6Mp=_~13MO1_!"
    "N6nFAxPh{Ny>u0fgXzT&tiRUdYtfAly{W#*{2&;`Q$vz}SNG+O3J*u$A&eoh#Dx&dUojNUpu1%16jI3g}?R;+#eq"
    "Mf73P5i&#R<_xvxW$<x;`<;<}<P;BG2(}S3jR$yu13RdwF&Kp^n6?w|Q>6@4px!+4u~ob8vF}{^ay*EA#1Bn3MGp"
    ";meVt8nId^PwTViJkRv?zNI;PE*iT19;&0I4RcY1Thi<qGI&9%6tU9yK?iu)Kp|^HmnVefGRc#09;@1l*R&;^R#4"
    "v|0(y}i1#N#amwUC4p<02mpc~q(Em-thjN|0yB6b_aPHDJ*OX2PZjeti@7>!ds7XMxyfN`^qOAoR&UTAgI=;~XW3"
    "7}q$yLNiyRvFf0eONP4waby8#bqXC7X}%`{Xoh;Oojr}`C9lO7Ayj#%5hW&%Gy+G7J^znzk$b>g>4xLwqXUDb!n8"
    "<$uEbQM8%mgIJ+*Z8Y@X^nl{nL^gEg&%GAX5x_x_~BwfDf?^{50pS%4mo9uBNEO&d=`7<yXjh8|#GhxvNpVA&+d4"
    "!^!$U7jM!;3mL-cys@zvbDpZ7G{-xb$$t&1TmEkIFjWQaOzPj>@@Etop#3NKY~5cPuC1mV`xMH3<e;JhJXoO4i-$"
    "_N&_;8mVOL7My*_KuvJD&^ML+^#@GPxN450l<{lRVOS2Y)`T_+c|9vcMUnjmHhLWT`ja2^JcG8xjn;|Ksy8QOqtv"
    "|xeySM26l~0Nb7ZVw1{j9SRM?>s|Fn6QUt5jTm<=W*ZGwMMqu|$wI)+Tzwn#ONI5;+btlSmf3&NEQ07-!xM=yX#)"
    "*{!cQU7qou(xFE17qjl0R1bAH_v`$)lIHGB5gMQ-ecz%%r+%|?=__wwB2O=rpS4pKQ1ri>6Eu2sDw6vj??S>XuPx"
    "y21+p-8#->SU-|#CEd3_)(QCZU&m+##xd%7;BnU&yf<496qj-wM-C{BbFG9|5aNy|T1QU`(ry<O(hJ>S2E`#NlqT"
    "ecub26O=8J~jd81wlwKnDe;MIf5x5oKEk+Jmu&X2C}c(-BVdP^3DmK~ipp2Nb|6nUFyuo&Yb?r}0P(R9{9^Bs&Y4"
    "t2c)e?%U%B?hj?=BIW_Q5OxNT?=YTvA(J3Y=G}VWe<9{Z54JuJ02;U2GG+m0C@%nol(q3og9>TGxiV8z3Bo5Kpxk"
    "#$nOa3+3RhGh;d)e!hSqx?Ort}(_#*!3vt%GDLH<;TgVKEjC?Rn(ZTKC^2VP1t=sMIQ9Liv-aE5?e&X*AS%L^fBO"
    "2Tn44$C232L>PiLdlEF_=$kDDkVkJlh~6`tAemmFouzsr|u?6dv%xma=m00g(+;S{Nv2bTRMC?97|+)1Zl?Py{k-"
    "U4RVWsl!4%|tA_+RRoQcuLcL>iTUrtrMg)j*kS}90fsNH`Ntec8hjn$~PF7>X+W_m#qad9Nw6jH7F^@yPsJM_FWV"
    "P$$12x4eGpyPZ0{V~DQ8T5%IxO>&Tb_+*X1mltwz5>OA_+Yy*{k^4%6yi^dNmN6+IOwGR}5XmL9EBo6!RscBw_Ty"
    "I2je|DDq*`KMoUVzDq)Jf6&{=HYY%zavh2cyrmr~{R|uxoqVKrET|llNck0%r1^t#Bm#MDjs%G#X-*ziQI+ku>R-"
    "EXgR)WCok+f}j{vm^ra<eLtk4b*dK-lN6wv}-3L`{aVL-DV5`g|;;#yWD`n1E#)I5ORs@>_P8H&&B|7E?ncX((~3"
    "fCJ~#NL%>O841QyTK7uu(UfnHizGn(+?JR!!m%08WoUcY*aNhZuuOd*d?o-V-cRS{(zK&TL3wOz}o4&G!kjZApJ-"
    "Uk{V+A1G&l)?_t6dL>d;yz?)?}iDDVrzns6rVSAm=nDk29&pzqp$q_B;GvhrFzMIJ<s6x+*OV#24Y=Sk>uFb?-ZL"
    "bDVT+smm^V4)B3ynjyGDJW^Yj&4J<gm~I6I7xihbri^s*VQYlhUnN(x}yd8|=getD<UM;l9+CbEw^EVm0h^s9D$b"
    "9CT=z@Ex%TS`Lju<WbQ$>L}9lYl8YuX(!?L@tss~J*62T?+`~*5`J(m$TPVORgyUcc+@WHzZP_8S)jxRB_(F)X}z"
    "FN;F$|DVn{iLtqnmTj2a*md}KH@E^f>rL25y97^)juRHG85dz5fV$7q`${EaCf`*OZY0}!K)G*Q5vLdISY8-S^fX"
    "Q*lrJI^mvl3i<0^a0u7tff(6N;5UgA$uiZbjdwsJnua^b(Lt@n#$Gm2V2ymUlEmx*4FcAod`jl1D@8-gt$(z#p1p"
    "jBF&>#g-A_?HT}wcw4y!bwN$B5<)bQ9S*^%E7?Myi^p6^jI9Aw}vcB&-rjcFQ*L%IkN1GeF=57RS)dgcxQpOtR^-"
    "ajV(2N+QBJm!e=e==@{lE_Pwxb<i6REDWL&#aP2aa(%Yf$S?xLpgEvbtH?NGP&*L{?ry7j!E!2E{nFLZZekKVODu"
    "y)X8*t(d%0?4XcwD_sK6MD5YRL9f?*8tR$F&z!AmV@x$mQ*)~aQ@HgSuiU_Q?ACL2>DJ*$6p0$Q-khGjgCt^atc#"
    ")(AIO>X{_VSqUoB-zGfL|4QCX)5d$k)xz$jQI+st+#vMQ;FI1p>WRS%712b;|2wTKU0+`J$fizgx-vU(J8?&D$V="
    "<%VkaV-~=Eo=b!)eRih1LeOhD`ekcdv)(#*}uElg!~DW4i2R~Zq1P7?G7AP$M;asQyH+K8Uj&}zw^s4Mf<=&uN3-"
    "x83VjN&O@ISsjO{clnJyz$#6%K&oa_N>gBv<FSrK4%=TdP20yf?sM3U`!&PZ1o@7SdSf5taUu+a@X1#g{YBqFCme"
    "`oWA|q$1ZR(>zS)K3&Le-*L<Q}|VCj~VKB?GJLw*6iM3mXZ)lDo5BS0PwQ<+8g8pV3X-@QLKgU9^X}#f8_eDUK1u"
    "Lhiete>YM&aY48S2XDXJ<ptpugmlREtc7O@Pv<V-28V_A!&bDs?VDKwQs%jNB>1VC+0||-J329#6<U^N-=jj2V9O"
    "=C)~UWQle&J8R1;<>&o>dBS(pSVu0y-@^-HwR_Fi?DbzWBX=Ee=iTSX(wh9e3~uv~R9>mbI<$dcwBA>k}lqXg(J!"
    "wbMHW)yHp#ureDd4`r;mYRVL$E*r>EVefK9?XDjR9FKw3N5DXWt!Ym)K|C<I7alYyb>Oy>B~6cFT3|Vx_>zdqL<1"
    "_xP#U+HP2=`48TvNnU`dvINA|uaVTav_Kxz%h_DrxS-iaD)6r3{C}C!<xRjOwsa1Mi#0f8qny56CNOxak@sP-Ljn"
    "<X(Vw{IQm^UI_eT5hT^KKV}&#bqOIF{Ooilcsp5CLg7hTC5%G1yC1P(m|!m<E!!Qq~)L*$P>e<w`SfLF@+v3;T$6"
    "S-^IbCQv85Hwsl<B(16p^mkzniX-%6W-oQ+xUl}#jIu(#t>d$jZu<zeZoLH>u3)j2YIP#7w>xgV7R(H4rzlhmA<Z"
    "O_uc@(m7u2i+rPA;jBq1#<ZmCKh%_b|t(||P|T#+@xsPdmZXEdz?JN)Hf2>Gf(z7L^~0Bo7ZOXhnkB8R%7PMspy1"
    "2C&Rk$`ueer^s;E#g)Q8x!0{URVp2`JWh`OP+R$hE+zgY#X8LT@hY_(A*o<Blc``>&jGVVx3CQH>wOp9-yv%KssQ"
    "#Qd2K-*aL{<o7E$Cpv)vHexIPkxhY~tCRL#v;`Jz-uZt0a|GHruFXiWFkn=Zv9sp1VOP_cP7r4?067tb!LgVYk5N"
    "iZHVBi3JI6r%L^3TlxKK;Qi;CmdVIc1G@Ar{X#I{EqC*&Fxt{qKcx`i`%LjI<V!iZQ`g4n1p%Gy%~i`06v`OQ0bB"
    "&#Rx$-%|~b<LI$qi^1&a=1~@e#6&tOQS_@KfvFj!#tcUwiVJQMy_hYI{IU)+b0@agwx{E)aRlhe6l`_40ulBQh`D"
    "Bg!AdYqaw%u+TMsx4q+w6Xnv2~KTADUkYW~HiaHY@%8|N81+!<}YkKgl$3z^&QGn%c89%T>2*&-kZB8D#VG*f6#L"
    "2jmT;-}?_plk|1#WFRQu>E29B;Q-@h;$2PY9ZH!T;8sWJ=QyjvF-9Dgm1>onKz|ZDM8ENxi)@KKguLU*&Jf_!kI7"
    "Sd!<*z9NhBkH)=$&2j#GDT1PB>=u*CqHnvmA^z&)l5=n|&$|{d=UHNTCJ4d2e+whIyAC-<8lE)8?Bxav<-i$gZ8n"
    "K2&Q9U8!P*fJ}<AtyqQ61PS9Q`15Cvm3a_s2>=|LNSz?4LrOR?-wK6Ab8HHEcn&zK{4h4z_qH3qF>^NfOSo06ppx"
    "rg%n0dbR*Q)*<_7_Y&)d*=MtGG-w9;NhKTASn*;?c)E<Eloz)}Rhg)R05$BJd3kHtPw6lTo`}MVL06JZJe3`&YD9"
    "l~|I7RHKi*5-BVy=Q8^8#arcR*lp5_o}Rc}J*eIQ9%vM1aLI~bRyn=O_q+bET+iJSNd$Quj?b{qZWP>L*p>}w76n"
    "KlhyYF-p9S2iZIg;_gigp|_mp+T?t77}iW=^Pd6n4$>G{X%{qu^ApLAx?6dq08f46hB08VNBx%H_|~*!$2IHAC%#"
    "xL`<|`L`klPhPo~Ve`4d-&VrbN62ByHQ1Z{BDg0&!IzZv!MNB7MxWtRR9O`K5E#bm&DQrjitt~i`It04oB1CLbTv"
    "Z`>%E|G)m6#k;2_`2<X_+JkyoCbos8FD3GNA%Nn@Y5DLmI?exfVPh#9O(6kL0fUJghhMxts6>UrdC_RX63xM9%c<"
    "lrrhbA}`5*ROD9rysA~UKCD>eLJlmE-2^R^)i0G4l{U1{A+wvbAqt{-Spg9Gc{wKIP8l$T*GxK{b3YHc)!by&l^2"
    "j=+gs6R+p9Wbnx*h8NYc#pb3XE|CJxZyCih<GDqjC!uVRTP1C+%`eR;!X!St@Wku=1Y`T~tleWgKBU!noGWCWWbK"
    "VA;Lt8wYzH6NmsI3i)OZFPMf)Pygk`l}b`PiN;Rzf^&w1?j~k^<?5ybqFn6r|hPUD_kB!)uQ=X0}-ukW)z(uEWKd"
    "y%LbE4oaxMZb;n5dw%=&hb-uudh&V%OoDz3sa{<UFzWV6sXpOyI+mRUV0@h*zE2_!#{lV^Ihu|9hdQ+15d^>urgA"
    "|*4VLKHK5Si!MV$F$lYWGzQc&1RWtQjY;o$s$i9vfI8*oY`vS(XBGN!;ZWf4S_9QH31ZT#HcaCawqkn?m@amrikE"
    "q<47}Rr4YsUW8jEON)49rDt)%Tug6{X`lw3;kL2!)CxC+hiVAVW7!n-g(ZJ7DtSX%<HG1-N<+Dgc3{o-8)STHBHx"
    "xhs;7dn;0pBQI|xS75jxNr2o!KLB!E~FKXmLdWCdnv4T9{4TIAR!fVofUT|N|$DavLDcYru0j_iUOuT(8Q)*=N<2"
    ";%;J4LYF;?(O$C1o?r2hk9JTwJwg|0wK^Qujo0lYiT9i-?su<sd^mAco?Im5YyIETU_f^6W%sKX7>8FBUKY==D@b"
    "j_Je9ENKtlVfi-NTCbxXyfW|`5t$SIOert33u6Zwqv?C&N)dnRKyQ03oQpnyun)1zmG@x;vm|n97Hs>~b>_@c5es"
    "myf_e<es%02-Jc@g+8ZXU(o1ao_F^JsPY1)?IV5wwLz`2uaf?X^_q^VrG37h?yYVbhY(F6#~*l#Y`)bmJ&oQL@hs"
    "FVqdg;Ob7ZVje3FH&wBjk_3H=@yvG$Me)-@nnM+ZeyFYzQ9wD)ujx;1MPmBJZGq;4n})gs$YgD0b@lwEs0?aw>$J"
    "|K*e&hM!W0^Mi;3?IsSbtcV{sz3uO&cwoo|L-fg?Y+g-RUQ{Y`x{1~OGx9|HMX;feaTQxBq@?-IDBP5*Q+-~Hp4c"
    "V}lEYkAu|?RIKCS9wwjEWKkkvUa_7w&?F_1+ELr!wp7+?CsaBwhm$;r(UJ{C6c@$ik%d5WffAD+*jo_^9HE#qQ}}"
    "dR)YPFT|rnR(jGC;hNKiI3Dk^*H4N@H?oH<`;tz!-rdzSfCM(z5CbWgxeBQkmgh29LvY>2Wqf#T4-1Ih~E7xt1ks"
    "8ex-wsG*9YI4W>@f12))Uh2)jEpNN2TcNvfg#sXsH()c9{}7jqKmo1WOi8;-_n3B-_et5F)ug{DQjnguz((g^Krj"
    "Kn4T=HJ`Mv){s2X4LT@7<!q>xYsTGIosK^D!l4%~WE{qQZQeW0&N+p-S8|{Fy;MYZ)NI7HJ~>`BxUtl;6tRAQ#A!"
    "BW;^d0~)TvfT<AJN*tl)T}pCrTtv`<wvm$VE<1bz9z@*Z*bdKm8-DFG!JbjK`B!bahF;BX%FdTSUs5o5g!zpS-7s"
    "lee1FfJk~Yo3$B_gwS49J2mnb9Jcz1J(ylmpQt1@9bLd9*OZUiuUR~ZCxa5sk=bH=vv1bTlYopB`BOogc)g`ybS?"
    "$stVNjai%3N&a~{qnN~eGQ`#bOHpz?hKjy$$o*sEEx_FnQ3g_;NspyxtW#pr?!Kh>%q$>?Vv%ocHZ4+(HY;e%+31"
    "<;i8M&0e+g{~mO;vl+4Z)0i*7U6muT&R9BAvzr`KqP7#~Nzh=NZIji2!prWs^J&BJfc1z13^D!60>YBYfUrbz$?z"
    "Ey-<O2@o&C3?DGXUG_d^aFwy;93i|3_d?~g3MgfkFM$=J$k1IY&A0o<d3i|Z@w%>CCaSYm)K+fiOo8@l%jS`YG4p"
    "Rgjjk=8W?qPXLIUl;1Vn=SO&`f+P|SK5gA-Wo2V$wD+|=4o8DPiBXl{|9Hq-8k&gONjC#wLn;=W5=clpNvafubVu"
    "!bbl=^YBPV25saQBFx_Tn#ToF1YY%$tl-9w-udK;jnAtO*9wYW};u%plJl%>|<6+5G`p!r|wHh9whFq28kz&IjB^"
    "PKy`r$t;XXjN{4)dWXlNr9D&b_wU}+v-&ve-hHM~sJO{S}6Dcxi2S_?2kbVB^ny|>lA(bpR6aM+6<^a4nOh$vz+w"
    "R5+SDtj&1Y<Sz$5HZEr!gtV23hyE&EUZ{$l}4aOzO4P#}@sdKvtDLQQc#KDExqL+CHbl1TOQg>&H{q?dYF&J>PdF"
    "3bAeIW*I<}M<0sNYjs}~s@M&xURy{oIqOOx-qF@eK=FgBoIb>V;8We-1AcaCoQ4B2K&Q2L4izla3F@8r6T4agw0}"
    "A8=c6y;{VXShrc|p_d)i&x`9XpK(?`Ad5OU^Fw^LFgGwhNZ-;EFeuLth-R&Bi^HSP+QRG_KN_!`@0X7^T2DcNO*N"
    ";%mrUHNP;N$%%UFN>3x2`IM~e5dfzPIvD6Nd3WW5?MrG3g>*`{SHuNLRnK71QTE_?Dz5wM$<is7Yn+C$E~A*KiT#"
    "7b`SjN!O>*@;AoHY>15aQJwEYY4Gs@`v;CvNeos}Q^-1H%6xWJ=3*gRa23r8=bvCCaOQR0Cmqa{yIi2?gxLLK2ia"
    "UJVIy`vA_xSYHf#=N*CbPo>uYa_A;O+6*E<Byi_GbOP-l6~Mi2MCX?`W|1>S*xlaJo0`&3tcfU{p-mE~sLSdgHE>"
    "k~sUX5hH<VXnc!G&dR5_iOqtPB5TO{2gXDs@kF$&`JOt2es<KxCD#K-`It8NiEitbx4m0w;Y7MNsyJ$U#b+WWjUz"
    "I`uKiZ%honQL;p*oIwG4NJ6BUdj^&)=~e*{SI2IqY&PCTx_4#p_hfrlNaDWja%c+5q$T{y__(gYP!(U%N9HE@NpD"
    "g(|<H!ud1BVfqbw8M_!LXul<bf98U!wc!!HP)1kXww>wX+PbD@x%+sl~Yk>C{9ntExa0nNEAf+uOs-ikU?XyGlvo"
    "gjg87VD}G%_nN|*0Hw~F-e`J-CKhQofVu|Yky6LL4hv%k$WEJZ|agVnSyFISB&y>v&f?W_%wV}Vdn^Y<KnK5-n1T"
    ">I^8ys1+56j-HpgHeYV{rd?(33MGd{2t5fdDX$7F8DuXkraH7K^4Lhb*q~qdW+GH;dyig`YQVdVKlw`3L;1;+fHN"
    "72zMtLLf8Pqe&dy?kK(IxQJ>t9=H6&n~61|H(F>jcmR06F<h#);{^ZJ>m43~d(k)|X~ytfQcbC_f@6|4DagWj+=}"
    "ra-B7JCVwYa(1*v+Z6pH&+)TuiSxfkV2d}dq_aF>FHz%3Fg4o&~VQr}ubHiLUc7J0N*mc(~F+MudT3%aM*L^=q#p"
    "w9BC5WXPEr^ix$&!e3zpD?VAJ<NHelDq);ji)RPK6csVoI`pmj3Z9$IZ&o_&Y{sX13RUcQ6=5-l!RWS9LL73OXPC"
    "ECp+*-*`H?Mw?zYiG&ATnamy3xT^Eg_rV32m=*Y8yPzGjF^qt0jEWA5mI#tTDBo8?&z$~v(lYS3My&w|@3?`(1xZ"
    "m5MJWe<m2MMmH)L!P`P**mS%)<!=Why$C#cT%ZGf>H8FtNZUciD%81E>|OMbkM8y%mbk5D+FMvu+Rplgy6UB#uMq"
    "CuE0#$h9zK0M3sDORSHNW&#JreY2MoUtC)P$QLC2w?C}1d93@jfv+6PlE4dJ7yL83{6A+w#xaW_f6bzpExkbbUME"
    "a?{sV#$^@c(<5Trs^poDw5FYOHG?v@PZZWDvq@Av(q0q-5~>EUd4)ZgnLzS=*WOm_Q|SBL%ntKNR^a58(<f3@!&^"
    "1bQq{@~T#kvG{toc1S^{mE`EgULTG;}n#pKaK?Gx@!Y*)-jp-=RG@vIoSKoV18#XzcZNM8O;AEgE`uYz1-E<OFig"
    "^+(FgI8x(j$i@Q+{yg}S1y3?S`H}RX=PAB_{<Y`A#9{LNxZm2YMqTO-mCC2J47~LlB*H*OPh(&$El0-!u;e$i3M3"
    "5b<(VjQ9fs0MEc<CmHK|{_o>5>}A!A7+d-SkpVOQ{%Jy+H8*-<PADQz2Wz!!O1QTLP``n}ImY+~|Gdr9MA+H~xD5"
    "=Jd>cd;HGGf4mJxZRt?&i*~5Qm=}n@BEPGM4g-uTm^*~qu9v~}1t9~{SR^dxJ`({HQx?YY9h)Vbui?dkvldkeQ%s"
    "`xO~}G4!VJy1a#CS_5-(F=ZU4=a7<lsl4Jk$HGA7v@!8!vwe;-3$I<nSaMg}jVunb8ICawh2R&t-fjx<8#BpaCRi"
    "#%ehI8PV^bHF6LD<l(wHGYU`4n<9=LmaqASjruE#tO31Wfw(SN?}ol^CHc}7?taRgOrleM5TXO7JJXiVyDUUWr@v"
    "tSqW;^#B9IXd&T#?sW&^?Jvf-c|IZGNj{F0EaCp@7`nv~v-mKT}@9rM-j$ZB04hILby;n2uU@+M4znbnH)iT>ana"
    "r@y|ILoyzky{6?)j*Xx8=BGX%$7Cj#I~kTdLirCP~nadfyrK?~M9)M*TaZ{-0#j*Bm|>kw=99r2sLGhHgqxC0qoK"
    "F@}grRhh0$KF~Ll#s|Ob7aHbmsw-08l`9;m3gd@#R0=<%S6t6aL-^(5LziYzsD{00)lQIIr(iX}t&c{f5fYjh@qU"
    "D+8dI2(fZvO1u0P!klj}Re9p6#xgz>lqbViLxHGsd!c8eW<H0!_lVk~#vM0}1Ox}nYu719D(mlpUSx*#Vxv566EU"
    "J>?)l4Ya6C9<jTKFuM%7Z`T69leJ2Jy8LVM6__Bc_y|(kKmld56B<FVnaY@i1RoLLg1By>@`c{1i5qS=mTQT$zjK"
    "jIU$TlD@#729_W7KWW^vY$Za0@UZt-ktul3#2I?&gNTLT}o)aIZ3)Redia}q<sY$RdUG|R1#Y(80|IA^Ery-<LVn"
    "G^*=pc-$XJlDDOgR46<Zk!>V%#klQ8=&<K^S(W$)(c`(lnpI3n9dGY7q;;49yBPK!u}&@9gP!_Vhb@`kg)f>#(N~"
    "FqFGU5gn59A!4uiEn}*WqvZ&X!%G4W0Qt<~1p*S_rH-h6p+E=_{y^-o@pwFr?g?v$@A~R#5T#j?<D#bc>I7}8A~t"
    "Wh>Z+2GV2`e8%TZSa#vK?*EcHShb2%zlz9l>}2PfHCt&@)Gm;<~=?qz&L9<mHS8Gb4q)*;*lkB;aU=$ccWj!H|cl"
    "_y41YPm)-qNa^w{|REqF~QA>YpGnbmb^|?Zs*8@h=;*#06xZ&334$fOOz=X2o6!bMxqi#N+pK@CdcCz_L;uA(RJf"
    ";ql{Za`N<b!tD8piIjr@XdN*XRZ#lp!2z2g)%>?zYUYh0$p0Yer?%ohd)|&)jkOiRfjC{86R!Y4bt`rXrCpAr>Ul"
    "eF^11&Rcbzrv%sW6AspFs))B@CuP7OpT?h|KOQ_Gp)#;sijSRs}<ims*iBdPtxM#6#djN-|M=K?$?4NRg+JRK&1p"
    "n;7s@KOpXV8ZQGBG2#ga4LBZY)Hla@rbZauN?o%!-Ao)-(oBP{eI>y)h<_>&A+pygvD-Xc$w2bA0c5cuH~+sVXMV"
    "6TXI{=H(TwppIOK=ZS9?dh{^4w}H`#r)d*Ju_-tOSle*fTTI`9U(zdPOa2Z!Fo<GsB@|J7mt=-}0>!I9se)-vX>`"
    "ypa`_m*dPrDKqGU?dO+UXXjd3~HEjs01^i+Cd(>-<k98%=vfb{5y00%`xY7DSa@Dk1dmlk;()IiDi;FUI>=FntMc"
    "~9ub*GDmg)}amYo&4&dbay}qs+#%ILSCe#r9lBI#dj#X+7cqDUkj72_<x=$pvM@IBEiE{*#(1(hzEVIRrkFXa4KO"
    "M=4b$TRdrxF9CmOI7<-5|;U$BIpXKX2d*&9k2;7@bER=i%DDZibUG$ub^5b4PzMM%f%#1z%wd4BkG4X|A-<Z)~H#"
    "o`W8b^FgnFlrp;gJRe{^%#)%BF=<}GDG4@ijz0LvB<#Ru6Q><APKUYA(+${W918?v<6*oc|Jex_tRZAQNm+^>zf7"
    "_#?A@D`@jnT`AeFlUYe7AMolQJAXtlkt@cgI7pn^Qj!QGbm!EDBp*Q9$UrLsa?>&g3;Nu1H<lXz*u!9X8E?%i`Oj"
    "1{0vAQQ(1NNNbC$msA2o*JJZNF#^e8M@B;L|VHHFd?YMMjJs&Tsv^cAPWQgzIqMOc;=+TC)oLf%Z#0WS<d?K2|8~"
    "S+Zy=l+1{(^;mn`x4)~<MH+$vp?H~EOv)QYo+5RD)@d@|)y9Wom2mbDq^QnI@d(}HQ?C<Xn`mc6*&#UFD!ItAv)("
    "4E%GcF#X2+w|GpbcLxxzB!N{SNy<l`CgcAPq|m>%Boco7XF8+2El6on`;dvVUjUzq9P$us&TsxH2~k5FyaYMk<kx"
    "(D9aG9Q8WiBH0ZDp|7O2>0_@6967oMepRHOaiaKP)Zabobjneg_c}MVEHK8|U1DTA0(cLpYDc}q-(Q6Nb;`HJ`WD"
    "o6Q)=N~@g)7447NFK<p@iCBeYGg=~wZ?Om3}BeI4_>jzQn1kBz@J>*HQCgMZABMSk$^IGZLMu@DMTO+lbAeGYKEX"
    "~sRD#WMs)Q?jd!-lAnH%@=?KF+>IhTak$FHC+Esz@G}cREm1-jCk=xgna!d&fs3J%g!Y`oI)#r2#IG*2slK>>Cg}"
    "+Te?Jg)4MRfeNC*qgsxzO9ZbhXV3H7qxCkJ87z-Np;~x-5LOdQ)8O)0s`7jCqokTJ7{CgNWsJpxDBwiTFiB#rh#+"
    "N|~u~Jb{?y+eIuO*>DDP)BR7ZOWg?i21MIOpKr`Pao{zj^`(F9M%7@bKRL(PZlF9q#&r*-`HmKN`%u>Cw^t;r@Pa"
    "2Edh92cEwVs__9t+jw=jf3Vm02ZQ~=WN<X|ye7~J<)R=jnI*&zQ(h#%S!-`gF&ISw&lgMnceV(kb_2Mjsbmq4<LE"
    "nE{+%uV&X#{?%m0&Xx#+^i4OiM7k0aX0#$ezv<`@-Q5=+QkuBC^9Y1nfrpB7Q>F-+HZ98nBf_5lJaAVL&<poV5yR"
    "Fo6wdbD-}m_**uZiMotP!WDhJaN4nBzDIYTY{AI^vtneFGEo42p+z4HQ}rNmt(%meU;D;gE_4RB`)RvGQ0g$Ex4s"
    "GnHkX7)|FDs&&|407hWU{7I~O?5s&j!oM}i0_b`uBbp2Zd81mxdlye`I<#-@A=9Djkk18z=gsqpm5a&}ys+@s~AY"
    "dmRCOiRPITZAKA2X>5_r)RtT7ef4o1F0=gPtKR>#|dP3f#!t1GYFt??d8tVBEk^qf4eA6Y2zLHDI(;w#YMrzYu4Q"
    "=OD%TZuD|QL8QQb^N-#%Q*()2b`Yho6R<Zl1B4TSuqlzmy{MQZ_=SXnOUSyQ--(A~&E_6p;vuleElM?T1OHVy>!Z"
    "IGXD#ERj*8Sp*c<)QtfWpHYsnMQGrd#CPuEtT=Yija|LnCf6z<lINP4*Y-68TjEB>7o|IUhk(;9N~@QG=J?JR?!V"
    "|@M%qMvB7bYIHgys-4bu2>DPE>PhSWpgo_qr--AYgJwsN5pW)^e%EgKZl%QZp;y#S+V!j-9QDhRgF-A;Ya}dF885"
    "7ad1y-8$}Jotb!Cr6xMbuv$Yuc8s!GGroGW;MNfL8#X?3L(*Mui+juo@WPQT_iXP@Ur|m?zf&Qk)lO;5ru;~UC=w"
    "#;w)-79QtU;DMlH9b1<$r(A{i+YCWE+y~KC`DYa}sQqN>#V2Zr#t{tyj6ZTwY(TX{VQ|0swFllT8`fl3_tYhKtSZ"
    "D+vwV+uuJpIX`&EQ9@b0CUW1pT~{7yx8%;ML%r-w+bpbIzL57h4DWHP(4^fTwIY6HG0jKdk>V90U6DVKKIjxmusl"
    "fk7d7GGLUwPIm8>CKO`ZAtd8(vuq>Wgn+I;J-l*^4zN532$|8`WXD`9QWjW!?3QaU`=^V2q~oj+z)`uoRDDx0V2I"
    "{C^GD18f~mN|7{g6bB~ZU{RE!;Nr48ncHHc7k~}QUzoluMr2vX$=tU1#miOS&2}0JA8)<Cm{aJX90ri0Mbr!js6@"
    "{QEL=sARmpBEEc6!V_F6u2?>)sp`w2gYLi$^W}e0*TvZUa8BlFtsp<fo&oKrK^;~n&u>%YUw0ZarZky>WuT+K!-;"
    "fDCsw~`{NFxxbuMuE`1q{by(PNpWyf-HBA_(@v9E=!c;#BfiFuOaZkTI)Vj=1MY+tmwd=mrY2aKyJp*|vh;AY-4k"
    "Z5(To1-Fw$5DiPTC?w@5$DDRa6tM|GF=!fU_2=Uc@77SYDFemQu+wOsjV6jfn<RULx82X@=O<>q@&wK-P_v1G^2{"
    "kL{R|v~0agAvr>uIR5#`6T%Faq8B?u85lv|*(>;>q>)b)o50adI1q*Q<l5E-P3gZT_i090&<cO?prR2FAVU4MJ)-"
    "zgA|YuxtKEFVn(nx6g11N@>*gU<^BruQq~&%gP>zA4||l<#lK_rFVc8drV>r<B<v2u}%2kPgu5&@>ni^xD^ZLL~X"
    "xj=)~~<Tt{aRUofz62qk|6;yQMVK13ZRh&RwrY>Rr$-2wFZrKT+PTuXE9|Uf4dy%KX*}-{0uV+0CKZIR6_B~*?J$"
    "U(`oR7!JSM02(Gh9g#vU1w->6&MdiK*3aT;L*4O(KgPmL{W>J-y3FNrCg$`>x6DL7@5dyokEB_z~McPNP)OjW@vA"
    "5hN2oOxZRd=20;?ta|#p0{%>A|0jd;nzQtJ2J16@wCm6Jx`y-5^S13(k#g*Wp?nv}wJ50Oq-+@4;iw-)GvGU>5N4"
    "ITad8qow^sf*0gS>qN+~F>0`=e@jNe2)u99>u8bP5rO`b#zR>mM>2E_dQHUl<#tukB6PZh{8<K(M~d%<1?CWs`9u"
    "vneu75ZIJngHbHaiSm#C(?QnR3eA0nh1mE;B8D3%DBM-@AEXZs!iGH-bqHOL0oH-h4okgcUUuD#+p?E6U$N88yBj"
    "akQdJN4B|6P5ai5<?{GGxenS^ppFl7PaDo~o2PAf?MJkTdC@XI<A8EnLXbIj&fR6={@88vpxV^o8_B!A!3&y}Q&0"
    "@4Q+<CbZZI8z<<LzfJw$zK)!#8i94_}YR&!5N9cC<5ky|opMU%uInpT|4u<<84z@ylm#p1*$i`t_S<Tg$@p5WJRa"
    "6(SvA{vc(FoCb<~k5N39VN2N^`7x$my!xhdeA79;=^Wp5j{kaD>^3XboI=CDgdEQU(ehBxs;wIW6r$HsAEx}(gSp"
    "L7F4b8}I!;;t;))Lvr|5QcX{@dZ%2Qd7L@Hc-;O7(!SEI|F4Mb%FL)q>R3qlgt0bZ}E(l-R^T(|`4_))GxIyzA-6"
    "A0|HZB01j-@8{H0I9C2O4c`{k+Ne#aj7*n&WjNdAk^qyo{?Ea#+K#V%afBRi&Jn+=(-7z#{|UhhQ4ZHe{!)f|F9m"
    "b7PR)ZLhL``MTKe@0o=PN-&0z5#Mneob2{LTgIJX_5X#V30y?e8-7~E#f;xccqpPZg?FF>bD8U4fIbH@T!|zZYN8"
    "l$&69}&JTm(O<rZvgIzK-^C@N$6cO{o5m{*8&>dh7r-8z-gI3~+MilTxJjJ#ckcPhoE)_t&$@*^2@m1quCICc&Q<"
    "h=1ku4jY^E-lh1L-p}YT2Q`ZaTpN@vr6*WY%=jyCF5-oPGGiiO3-~L~1xlrsmh?}EyG(ViU;b|^&+oL#^DVsmDf0"
    "5C48sSjxkR+zc^<uaJsd{k(ay`)FJJA9;%6`3yog87w_m;(Z@t*rj^Df)ZoS-!Uc4FYj9x{rUkryYw@0tHU#s}_G"
    "c{}#?K>zuR1?tVz*MuzIaJ^45bW02zm`Y+VSKN?Me%(T>c0u~--P=A`$GNlLvQ%89K!v*vxBoR5WLh!@Q&m082I4"
    "XB%fi4AV_PEO4Wzl+s+7Y-Vtn3d=u>75uUq#-$_W(FsLNgLeG5}RHy!mkbqh{@Skvrpemx`V2a`~XSHDG1cn-M+|"
    "!kYN5$LTDs@)tVIYv31G3!Jaa4IvC#s|;9{xttgXtSGzd4!5>dSol=h@;L6!h7~Tc+-7%41%F#=1%__l>CO9C*}_"
    "T7hRh0Zmby&j7h;9L>{e5s+&DBx4>PxWT}Z47@0gia3~ODTr~FXbBju0^mx!2_$DwRl(A{Qr16}io9}$ShyJ$D!M"
    "5-u!(K*<9SBLf3oaLH9!&+4V5I;iYrWT!cRHLZ%eda%i8GSqG|wF&`^mb9cZxN%y}loP{A;-izo(P!3n4r@(L<8%"
    "r(>^BR&`EOQLSqFyafk6;csS7bqiQ#<voDf@lg(E<*l_($QQaeX$9CxIm4}HP{zQ`~%>bklABll9K#7h;)lXi7hI"
    "lj-v`34v-Kuv43Cb|JlD`l?VjGF0*J>PI5r#hU*=|hGbJNv*M!@wxvYGt8b--zlr+aME!4~{{Jf_B3w=hedh(*(s"
    "WU-dW8iNK_x3)r`bf+glkN6;PLM<Bu9!&bgfp+ViQlkw<LEwsoy_&NX3ayr3yZsz4KL?uxd(h7LHR_0+KQKTtg@V"
    "MOjdNp{@ze@ztGhsIaW^#2-|3qVBb5bm&GmJ*rrSA;Dut_a}xtjiM}05ZPGf6*ohls214(_77=#7bQ9IVMkMJMpG"
    ")-zWTERnS5jS>MYLqn`s<o!`TTNkB@k28COF;S}`oyQuXYT^@m&2u4FWB5e~{YfG8?s!oW0$Sb^>}#ISjY>C2&Bx"
    "-PKn@g#UNMnFc!fPVY!1~`i<QdE;7pI=WHCl{iYOqq_olS8Ziv!*Qw+ob-;A&Yy#Q8ZOl=^!ANSQ!w)SF9>HELl="
    "k$;dFI(Lyvf!VA_>V)@vpa8UANRR!qC8W^L7WjGc*gFKjB$|EskzMg~rimD!YYl5WG0A>?KsBa{LVZr*SNZ=3$?-"
    "N2bLl4$7%vQwI2tpth!l8?dlUHh?UT+bl0r`T`Ayzq}NkePy`rlWtdj3eSN(>OxE4?aeM~&lX{AN3TG2D3-sdyA^"
    "zf#X$4Bu?M8NZIk>X{n9dcO617>&lycgE`3>zx<l;j``6;}^s2@#|Nu>J@^5^n*^4!4<LSUC+_a_<iuE8$5j)Y;U"
    "!xR{UV?x#lAV9pRg<^-b6MrfYrEwf>8{RSZLxLwHC$4pt*auL_6i;76bUH)!44#2owE+e_RVz)!8fnhX28D~`a?G"
    "-xz*e_{kMupke_pj>~X`KwbxPDcT4{b>?4&aROGZBGRg8*8Xs_V^wf4kT~hUiRh}k9cuQ?F^{Y0GYY8fhc~65>|0"
    "%m^x~hg1TDB-3vx4Nuk4}lnmN9xP@pLzK1~srD_y_LzX~JF@&V6jNJej>d(WWV3&WXB4@D(=SVR_Agx`KBfyAqdR"
    "~>vwEF=ck|6#dFTkC{b=yLaR7WaJO~QelSAZg0$r!gXa4I@iRuoAOBW8R2sz{>k5Rzeoovkf=(azSk&_pDDKCSpO"
    "QlJ-{iK_x2!lx05#*pG5UV#FHP66Bf_Z3nfQz9A|L^4v#q|-NBZ?<1=J%9CVG=8?T9c{lEZjGOB4TrCuy@=x1(e|"
    "5oI2vz7(W_U{v*+<Jine#u_;nnQN3UK)@z!>$bh>U@SvUhA=D5FYuCncA#pxc}@7A(@g}J?c{Y}FCCgFaQaKA~o|"
    "AoB?%+2NWfthSR3&C0h{2&Y_DoT;r)RK~kD{oT!_0p2XG~1_#peIwdn!c-@DINv3<cCpUCMHZnLqjh`%*-WXrd6o"
    "s4&#Aoyi0#twKQNWgRF=%97OXtVPGUXquLT!s1j;IIe&0a|1=4?K75}=w|x%3r~0zz%}pEk(pRrnpxLSwK`#ts;X"
    "xQGs*)HE8z>>nqcGqsXm}K4*V$xI621)v&P*Ugf2b7LDZ%!dr1dIiUehrNbM`RcB%zOs?39SpqVHS^bVnPemgSIQ"
    "z2J}$a*2S!IE}6)k+<ZE6L=bW!7=2W3#@ISzT}K7Bmg-WPlHHDNNY5m2XPUNE7^pzB8S2pW5z|&;6}?LZnzQ!%n1"
    "N=DCmVwB_RAxgyulohyjL3W^jUPB-3}2z>l~9B(~16JRn0aVQv86>7uI-$bnqSpzIK=&SUU@W~vzH#gx;A3HOJ^X"
    "`T(~8#s1M3%1rO7U==j3yYkf7L(-x^GV>0!#uC>JIJXBxi<I>=KKbks;JfoNakw_;V&O)DP~}%?3%NDmPzC<-n@A"
    "6>P0+yGkX2v#r9}8eh!vmrQ&Ejd>wDSc((Ow2od=&N25{n=Ed;E%a>a_FQVbI=*@We{6*X<kz?o`EO<ZYAV79#!t"
    "VhBu$s?O)xpcGY>mgaI%zEt{pMSR=x@^WH);BtH2q)QUR-C(8sDe(y{>T4{WGw3q__lHFWlk={q5&(-qfP;>x1KC"
    "=a-@hv66VYKN8+9Z9$Rm{%6R<49SMqg+gJP-_No+Za|qys^V)d@2h>y*e$JY8Av}EDnu@6JtB%%fn_r9^%cxmHV0"
    "4rraw*8_t48LbNgxcJ3{dNFK(zAt?yko&R&<spaRL|yr6J*y7VBG6>Q+w6RIzVd7k;$gv0B~7+8J+Ml+i!l+^Kvf"
    "(TCgWi25eWJm~FpCgu|>@*Aow;(_vD1_y5vWD|$DK0|Q<NyCTS4C3aqj=CUwuOgB_IHv~K_Z6KRm26w;?gAZ8$=n"
    "<rWgveQblILcUpKlakP-30daWf42cyFpom5?Rb>@TXK#UJC{X+%1_$KlaWtw*3Pl+%Dz#~VLT{rq-K0Wv82!COn>"
    "f3TW<ZVPOA^l=>{W`?7Zf5o#|$@`NYxV#7@2_^LA14m9#>ygF-katIYY7`{*g)PZ72~={0Wez9H}fSk{mgSz?4D@"
    "2?-i;8S}=X{8u*g!+)+Wv-`_zBMj=;>?)p*qAD+*7V`|&evn4Pa`0ulH(PA%1{;_7zx{l+psi9teZ?fZmgd1Ik5T"
    "nOfLhu}bmx)!gV`Ur&j51P0&(hHW|tXma7Y|aqp~b=IGx$Jh)DO-aZivRGMXcDmPn+S*If*g3Q0v2?OkRN?1WHFl"
    "t-dsUMSfcB_wi>CP^Ao!NggiDxw*@=lIM{--ZFw^s~#1FKW<s(`2YW!}X^><fZ<zoXo2vH6N4fEV4f8l{a54%-<q"
    "wFHuRd%M9fz7N`dUXg?Tqdxa|V^o#0rd%$+G>N4BkJKy_o{8P}kYn62H>8D`5p=I1O)qTp%FWWtw*aq|$#T2pI?O"
    "xCg!L7iSmcjpU?VzYU^z$Ja?y~%-#=&5aWJxs`bO1*w42m2o)U$ru-L+8G0cHsxgM&Vn?u1$@xWw>ZOd+H>Bx9;Z"
    "ZggbCl9wLq9p>|5q?HbMc{g}!-gO}=^;PXT4GZ13`>{!39!SQrCwin)cbqPIDueUU>0-GU5@0)B$Vah<A=>!Wu8R"
    "p@L`kWFU*W335ZVq#^WmxExe;5kQj%s#2C|PiPiDnHsB<T3c+FZ0-k9~f(d3RPzPq&(-*1lc*<!QVI}luJe9r4w@"
    "zc$5r4_h*zi{-qLk2W>)Z$Fh*3epHVs+zGMMVZ1XjMau0ChX;)|QD5dk@G^6-w1c5C1qDP-Yr7+ZnnoZI)bTd7=9"
    "JUit*}1>o8*JC_@S!E7;#MiVs{pjx@{U2nD+U2b%1eKqz2DuA->c^s?H3&}|CQ<och3l8viv_SbDw6g-7caa_Es<"
    "ExqC@*4&C%ixgB)o=B!~lf(Vn$ur3k8yNDTAbm+9$eK&eEj9M)vVW!*b9MrqS2VR_M@zMDwd)Gk9h_z`7xVq+V|H"
    "{*fnHXMDMFmjvGj+xNS{9lqisxw^mHz<r;XY99Eq5bL)Bo({I`hCBv{vg~&431hzJfTrD;E~bIB&epUedtJzqtjm"
    "_fmUrb&oQ-o=4iiMFkKjb<F=TSvAgJI_gyRWgT+Qizgy{ukrDg{B-2v?%<ueeWi2!ezOc6skrqR&D?}!lAhQndAz"
    "oz5RA`G@&a+3ffH<@wq*i<KZ;jEh5;%3PKDuC8sDJPr-HUL83M8%DYP4T;N5nYoA!UD)cmo>^plf1s3-i1R0R*B~"
    "9Y@|BY=wRm+U06YAWBt%8t0I|oy0W;u?(|Mt_tndLQsfZLjw)Q1XHfEC;ib(yOa3|6r5%Ja4_;gvowIVyC7x%zzB"
    "BNNgu!>APW~0cpk>|rk`y@s{q$`;8UDH14ZgVFz;tfH;0ql0yzKGQy`)l8hvV?FKtb=|?sDT~@BC-t;b(t8J3sh%"
    "dVG9NpU*#@ygNLlzd!69{ltIm5B5HM0I)LM<Gpvx7nd6+e?R~E_=w(c1$(8U?QM8C-n-V|{t_GkpevR=RHy@jbQ2"
    "6!bqnq@gpw|ke`)bVHZ<wBFmo)t03|nj?)8t?RjeU5VFbMbtg7|vtmX18rg-&IH(k5H(R2!GNI$qJ7bV-p0H_U!w"
    "fQ3uO-~zdobHuVhX~cPz9q5uP9X86cE|HuYS-)NHty@$)P7Uhm%g<cwO`9B&gW2J%DnaP<e=F|6~&51a0W0htMPD"
    "DRD(?24oZbNTK$}prl2;{#w;(BuddKzF(Jq{^Ncs-A(6=$M+AhKXHfq{bwF-~S%D$7M!i^B&(IYLUs@ZNQp&8ko>"
    "OlJXsL~B<M|7lU|0v#dcSCX6ID<$Nm2&aMLwVPf?p`nN73i7-XE|)R4g$w1yw6_vqoqyi8mo66E%2oV+!z_w!t)x"
    "xR2nwO<^xDdmw_&t~)aISrUh=Ques?M~$Ki^Vl0*Ne7r2*!>+#_`<(}Sn<m`JzyY~epMFt;VyG^Cwg0LsQN)w6z0"
    "J&0QIB~r<i`Sda}$8jbSu*tJ~VrifOEJy*VNwlr8Hv_G8CfX<=}f#p)~mUFT7NG-A;OaYw)@>LX&`L<`GR9@`hRH"
    "F)rdjH+(4xdyDT0#BN)04CDvt#_@e&W&22YnIHLcxS0a$RCqT_bm5T*UKPCL~q`Tmm7Gmf<=rj*!s`RN1=hArGlY"
    "da|dh{H+!LFgr9lyc^asq;0CbC>J2QiKr5T(^`=4*XeWPrUWg_92q$vy><nBGW7!CBScA)r_j`vQpwd|LVNz_w{q"
    "NDo+8z<_fk$m=d&C3=_{<u%$O*T9Su<=jdc`YsMW>_%uG8neUlkO@SNd3EFn$Bhdin?(TSR0%7R>_;=w$+?5fOAG"
    "C?+OX1*s;Rc%oYjFsvxjm~9~xDt;*zL(BP)Q>a63X|ooV-c6(WBqVFx*?&jJ=Yz9PKYlzs$HI2^ZCsSzhg_j{AW-"
    "nXvmPYS%?3j=1LIztos4{Dsc}IVRa-x_l^gx=4qu}mYgU6BwZKq4$A-OjA1WRok93w8{^|FFI*(mr7#^NJ1YqIDq"
    "mIuiME$cX_g5Ql=1sALMV+0We%e3(bb2uOb??LByTSRv-u}-Ar-RdjUk?v{8=M~ek57lEuz6q$(&DdVVtVArkj%b"
    "rG=v(j?0*ASgDNNk8F*#Ms&s@27uMY020BcLD@}k~A;TImqoh`t9r=hkZ{(V-+fQl+OXIEex=_Ts@RWAuW)+n;+K"
    "dif6eKrH4pK%;I+08Ecc**r&v~HQ#BHbE`-8-6j8@5fp$>=hB#j3EbX&R(xui;k#)}yU$bebgY$pXNB$G%75=I(I"
    "3t1ESXe5--=|TtcNhl$IbZsIC5In}Xj>T?JC@5K?D<`58Hil=o&~Bp2P~#3q+75)VoDz$PiaX$q(bsfzSqs34n&3"
    "R1mW0Cu3X<w|;T6bu0_-w!E`zd|jH=*d5ku>dMjEDLV3L+ToxP)kC{=8dhdL^fYBE(-GV0YS1W_AqsHK}*6lxdjC"
    "gc?9lp~te2*mX9Jhj)P7wl8Ffwcz!Ax)QVH1OpC2Awi?+dl29;2D-WbVnK|(RG%WiPX8tWQK-zSn^YbzsX?CnZQ0"
    "nVA>|Syxoo`NyhUBKo=;p17ar)N*7nggE|K*AasME32Fw5zX;ju4d@9F@G47!u2NoT0Q6NgAbUoGE+S9S6%XvRzU"
    "1pW4ZtbTd^L)yD9xd$rfl8V+Os5d6a0e^3@Uq~tW5aR8d_SQxq$=rYB7(~go$;On>~#sNRb5M)Gp~*m1~BYK5ykB"
    "1_i&Bi@ci`K-6HWrg^bg%0n3c56%hl^^t+|1J9qN6%vrqGFI{<Y;5gQhf=i(U{`R}B^~T!jUICMQaBT+$Ws|sGJe"
    "p~Al?aD4NCG~7g2VD*n*o$R;sK_u)!^?7wo|_nuTPA4{&{l3ka!(P&l(`sV*ur4-9L|q6Q+k!vap#R85CqfM!zB&"
    "Q~1V1lA`G4S+hUfch`gB2|$~uOh<Xr~+12F3L(xgQ+Sp&Khv~<+vlYm!9&Ic~wcxR}2`}^yG4;IsgS~R)0}kv=%f"
    "|kdFaE`+A<l%}Kk5J_4gkGzD*b@-Iv`Rggtps)`)-CGQz_6{;`LVORrBu}&GYV=$^mUz6#4x;(%g2~8D=LwE<c!N"
    "68|qZUln3hyALAtq(#aL^8ORf{@c+d<IFFA9Ui0W1XsXYes3*BR^71<E+3EMe<ee~)9rl^D+{iB_<_i24{Ip%8l#"
    "{+o|Eq`ic9&Y}_{|H0y}i}|k08D6w<2Hz>QxWcc5(*hi`?nJHgg`aqfi1ln#C@Q5ji-rjx+^i>5=z~y}YC238%na"
    "yYt2DVzfJ@P6P(nzPQBql}R`Mw$7O<(MN|97zPF`5_f&(hAK!~RcNFkWVux(5XqIKSNhD038VG;pjUYaFY!WPZ|z"
    "|8O|5`8GRr3q4`@4~&4LtPqy_=1p#V1S?=o77vbto(2k$PD#Y$pK7ZgW5F3Ff;57Or+48J!cM8lEtQk2rqBIdMU!"
    "0^V{;R?pDWbY42dEs<%>5ufC*mPv{lpb$lB{@ic+it7%CW1G_4q|Nnk=d}J@~I$1J^G#76|R}8wRHc>p-<bhI+7v"
    "OhQ5~b;a>U~rMuN&i>?C)r|asi6ztYYk4^uwsHGZJnf5=6^$82^|iWji-Hz@vamOYh{wd<&k5%U{H~WDR}cgr++1"
    ")H*EWWh)CA%<?oHKw-VOjg3fQ6}rD%$g!q;F^;AX5l9jdR9TVh2}S*g%==P-XBk&HgcDDo1K@Rr5ki!C8sM@=6nU"
    "-h8Dayx$>uZsYKZlebj`$&w;FCTy+*)N=F=$CMS=L5=5SEGUuil|M-U!r#EV!NEs0E7Ebm4!-jH(YN(h%j7k|v6T"
    "9Q@K%`!RUQ>hH#8BSco9K#DZI+6QkP%+s@!@PPcvI=faodhR%4qV0sl>tm9tLlPojmzxAe#EMjB)lnEV5DTJS5~B"
    ")Bm+EXO;x_G+t|#ZB{fljOJ>-V&KH_>w&eLC0Aoj^N~=NDVx~eY*yAwa0Vje46P3<DutT8`F2|DII7zMn0VBxAV-"
    "R>uNu1kBo+=-4ypY(@2p#d9AQ8$oL>gn*T@~B_G#e_uOeVk_uO`4<Nb8ohFbLm<Poa2cZ76Wt(mma*PHHh52Jz<|"
    "N35g_GL@hlbq)|ZMKnb)Zwe>IJ(hvk0+}H}tbp$n>++gct-Pj6MmKFt<_!GC^K?0P`Iw-={x-T%AXt?XE@c{}svN"
    "1+$_nmUdJzWv`uIqa&E{}DOmd_EWQ3AWCxc^4$)RP)f#dO91^>v0rLY!ZK$PXfQb-IpVF6YIVG5vV4d7Xn3$y%|&"
    "n0T2<xMi1DUOf*5~bw|9w8GVH9G-g%Qa-7R>C4|t%UYVEG1OS5QdK~RGQ=$GL?*q9O2<-)EXTn<#Hherv|5OxIoE"
    "WhR^J#guV;PLDfqrEHS@DJAWH<*w?V}Dvf6NIG#&Qp-@u2@Xh&%(Ho^Im5_b7(8Qgk^U@in4n;>b!rB_k&OMNyI1"
    "nr*<ui^8dJbdd_4uLyXP@R^9~qXYpfE2c5@YBFt^+J#X~Ep^_D0PEqf9XlpQZ~E;;11XT4x{QyY&?efRa&GDU1i7"
    "XBgZ+LEs*+=g68=Xi&jv*=Yr|K<jXT*R32tG8<c%zyZEg@;H_-g0m@<S>p`15e|2xKz<8G^XZ%eSs8a}J<UZYbwh"
    "G?rk53cU>0|vWC>vIn4$(&F-xRoYXfBaNy_+JV||!sBUMn8{=6FHQ-#7b{YEkgD)?j#rCf}+Qbdl5Msw0L3#x2;i"
    "sjys2`^(9CzOiFStm$8oo@=;f9h}xoyuj^b11=Nrm3ZGDVYeW@VvFjNQzA;8UxOkb+k+}`*O*HpiOPj11(itSc1Z"
    "D%V3&kU@S<%%eXMfNB}`Rt9c-7=JE?zF=02E>fog0Ax%;DBuN}Nxs?R?7Io5jMLH!%4MMg+k>rJ}{YZ2Y7y&UIJu"
    "v*FpB2+EY;4fXXepQ4L_uP~ZMumEo`IdoE|X`9&E8-r8>jhgXndrc#!04hD6>gPn+`uR$y5|^hII`&Tgimfv~Zoh"
    "%$%pB)VHFhu+A!}<pZsomA}=_U@&89z=yJp&-_N}FI>35mY3=?<-GWkV7V8GMg!d%AuCc~oqAHs_{^yRR4{roE8#"
    "R`5<*mwj28k!L3!8|Pr?ahW{+aTD%vP%hdB~H<|q>`RvD5CW2x)R_({wbRfc68Vm216VyvQ=%IW}X!?-I4A#Ry31"
    "$p$4`9dAS83lXHt>Igm14Bu4$6EB1hjydXOl&rIIXhF8D5<5giP7Si<{0;-6+^ogJ)1-dRgNIPFhc{XAX4D4mRd^"
    "4t47#l1<Q4^RP0uRlJnD~#36-bXLX%%w0e4B*iaPAGs=qA+ALCyQW1fvM8#;bDJz7#ErL{xWh{hvA4hECYa_VHiU"
    "eIWIuCG67~o_<MH)zkwjPT>i_lzY6EeFg@>GF4Y>x1OQAQP;$je0XA4!IgJ~5qD%S9P7xQ&%%sw@=orpz1@w&v-}"
    "0EKf@tw^b~W2x6<Ioqu)hkO97{#`0epQjQd(8g&_Enk?%iqQ!Et92V)Kbq6vu{V%7bHG)R<EPCY!v0OE){u`Rp^n"
    "=&JG8<P94TD>h(ykm#K|*2{5)g!^e?N(F7yK@I4Gi9+eb@k7Dz%MaVd!KSthp}lH@}^6ID&}SmbqNCYCc5UMNgQ1"
    "_7gFwH9x6lzM=`{~&C2h{yn=Yr_H1U?evg-~_RCHZ#?9=UMb6N>V&Fc$Ft5Dej=S6wG#7^&33H<aH`1$xIuoo4)P"
    "Pvg*=8VeodIm9XVAFcgS;y_jb;ym)&}gw<1iTnq~_n?s`Hztk#?2bUV1SV#vd|H~d9tI%&0hv+2E61VQJ{NfIp&o"
    "DXmO58#;q*i`luX!x>noS}pq)iCmkI5;0D<9B!3(jbG%2Nl8&%PBs_L!2rwQvv(DA1z*Xz2eXeBvBaaH0`-doeDD"
    "g@1C)*#+s=j{~uDv<tyM!JVf|$+6FWKPuHOTG%v(*EGp&u@+w)8gN-uY{(B9D~JXHPGkHtc3cTd-d}RqM;5;A629"
    ";rv_35v>{H!0Vs%pYfiBQ`B}=-ZSa{NP>~!F+RhqBLN%=Ab22oDtgXUyhFJ&Hwpr@F!ft;5?=u|j^`3zLEI9&u~0"
    "-``+UU^%9;lPx+An+oG0~N{jq*cjzpBEU)z@ZZ$ndrG|zD2*WKb6ZbzqM-iK_re~IB1d^LcJAV1srhn+V?a$tDM&"
    "wxd#>gTZ7HiqB=+?*JFciL{&6+ACadCjJY+1buR#a;xJX4Sg4TiMBHo$98P|Qh<O3r2B`NrQ^3PEj*_%p>p?pi#l"
    "U5V93Wr@<vgK^BrX7)PM=Ss?0OE?;Bk~xlkq&wNThvmk-(ZV<dh<6<2w5!u7Xt|nW7<JT34OwIuTS=WPyNDES$10"
    "I*ewu)M7cj5E74^cR@0pQkW2V-*)w_$LpPQC<xX_q9}w>Wz|@byeFd{aX3curB<Rwi=evd3T}%kp8|7BO;sFbl$A"
    "n}$Xf!%;Y<g@e)4%$LZTh|6HvmkOdugz*N2KA87$YbL^+^qImvVnQZJ|GRko%laZxKI8QH7401t2zsp+$BNgvxrJ"
    "0lOK%O^_(IXQTpo7G{FL};E}8>ccIaSYL-VxMoF71T(NOcC24Bi)v_(F_$v%WJ(VwoKF)-cMAOhvQDrvy^8l^zJV"
    "m!$8`R(b*%bu9>yXtx!fRrGrA#Jj18}+*zXr7^KZ&Ou<!JwNfK%1X2eGPjd~S9ZW65vPvqjSAnFEQl!;&!BI3)+2"
    "}D9bX=xGbr)KA&5x{67z4u+K68*F)DR=WXL!@!<^dH1SjkxGHJw~oe^Wx1E|*5s5(Cfof>Ri>VEvcDe0CcZap?M;"
    "OO>W%Au`5KjPgdMls5?3b@6(|aHO2|b_q>iru<-(nH5n+lR){y4jyH)vcVP%0%%}yY`S%si}Ba6jR6<M;VtDL@6$"
    "Xl0zeTe$&?$b0*6(ig@e78uv#k(CakWTi=16y7L_%}mjh`?jdij3TPd|*Vtpx%S!HGg5$mTus@B>B+poAZ!4_}C&"
    "<aGA;hMoD8J%dUTTo7-83aDsFsxM1!5Sh!VR(u<w96T0ooQ2vFPAw>$-4_2m|7(-tqAeQlpt_VIa|cq&iS!G)>(k"
    "A%U!#tY+^$(i@dJdSX0iYV!K;UrxAM{MW0zp9b6?9#-LGfo;JBs?F>;tD115;gkfzWW7`)bBNS*Dgs2o$*+T>ah5"
    "#3~dt-pn986=g`7lk&iB&M$*l$@2nJp+>qG{qxvOHcEB=RHN-18afBj^(}&S#<li8E+ggPn`EMcWvg<;678#%QRf"
    "*8mf?xtNRj^%NHe7|$qa%0u-?)`;wg7|sJ0D?Ld!R|MfK&>%{A1^UjfASnb|&lzUCjkBEay3si;>qx@MG`a@I97l"
    "lE1iq#nn%3$qavB$|Sg)FnH8B{FZ!M=6%gVk{*NO#_Vr*eMD^!=kD`SA)UA+}^CeYSTApjtpqdOUSe_m+mh67ST9"
    "|A>2QIuW^iX)#p5lvE#v%Xmt`;MMtf?S5TG*IvA_;6qn1NDNhD{alyxN(obWOlhy1IDw3J?&{v*-|yf!ak%s5=7("
    ")$er5U4L-;9?JRnH0s)8&3f#@8Gs{lj^?(&F_*je2mJkX<F}DzcH!QzI>lk-)wRkJ<vymbB#z%{0X}PH(<_C5V<b"
    "gS6;28GiGGoj>1tZnq7(+pC#2?t9EO?<)3Ya2Sh8TER$l)>D!V4N=G&o&s3UcDilM*6L(2T=?qN`21@AG1$7Z{B_"
    "<Sv6{*6@s$GdNDl5pb6V;$Tg#vG6u*k2mFgL*5!j(IfY(>V9IrGufV|0sBaH#0|hjKWWf*hyek)vnL5LBU!GKtzg"
    "XN2ur@ozpRZgI<}28H0@BcBv{+)Y#dzd%(PG@aXq!Si-xSDy3b(`Ie3_ak~w$sLR;C=hXz(BTU~7TkeEynu`>+fC"
    "`rM}R8D|DjT7W%2EYxG%BYZRT}N7u>sU)l9AHvn9oP{76B!F_Q=1`$tKrRs*I-Gtwb<QZ1-USMAc8rbx|oY*3YZ5"
    "Cme^i!rV%`pU3sjI@7M!qNb6cN=z<{gls0yzF{7jTo^!M}bz(LIPdHGH$n*vSN~0JI1XmHgd1SG(03V~WS`YjY;p"
    "Hs|$FJ3G5zYP>2uEx7eR@%^m}i(r-2wC(=!Y94Y|j!%Pe?Al&@h4@043|{GCSWp`{k?+A<~!A>Vbwd`Kk^s<QYDF"
    "9+fv8^HRyQ<vqv}Ph@=1WM`9o7z&5MGIkZ$Zx~^yO3C?!c@bT!o>}DwLr~6Vs_1lky1m=7mKiMW8I3*J0HZ2zTCg"
    "mM)@vhKf&h+ScW$C|=D_0!iV}Q_(q>upZlm<31Aok-f)kuI+CjGoIAuYMWQgbrkG|&xc&El)q%*1mf?A_zdSMGfS"
    "Dvch_y)kV!`ZA05vFAsyh#b05amQhUgz-Zlmb4@2x`=Wb%56bz`VOk^2mT@WM)@umyl};aC+eX-%-O+o(?Ety9H%"
    "XgMeB<GT@6=SzIC}Q+-znxEa1l&;toD5Z?%YW_hp~YzMnE29?DF`nG|SXoB?w5yu<~{!LIO@Q8YlC9FL`ZCpq=hS"
    "gxWfz|7YS^t%N%ymWqxaP8?v3$67VFG3!3uo=c3KoS2)^$-oYCsgQ^Qf!dFpn3s|7w^(MSaHB0~cFY&GXQB-hF^h"
    "iNK6FJFOi_w4G==^e|SV6tT=3M6AJ!7$m*EzK(b&w-HeT`+Y9}mZ5zBJjg0~ixUK(vx|SvF-NHh!<8XF9T5PX=}~"
    "G!+&F21_U8<w0s3d*B<g*|J+4L-Y-wm8x3$UZo=FJL8h~azFPeZ9LUHq+q{MT*n!t$_yz(has$j3~bkxx_Fa)uY@"
    "JL*wMS)cQKL#wyOr{Afx_aI?*B@Q<P!cRO(56nfH#f;ht%EJ8A%)g~4rTAJjV;-~+}J-pIy%@#5S|9|$U~8F+1^j"
    "6Nb{`2_>~&G(tg}iVB)G<Lm)yuOva0_h$}~kQY^J~M8oz$UT&P9?j4=IKR^^qJ=Qyb0xG$Z99)z4&gjbMi>4$-Z+"
    "d}|=*tTOuyO^PMx$>*i1Z^*Q<Q1-&;j4jhBv3svY?nk>{C7-J6kKxM{_@XXcH;MK}j>lC|ek9LZz|vzZ`yRIaGP0"
    "Q<rn-F=#@rcwog~bT?~`rUuleSKaykYAGJuuZL%cKYlnEz|N>a7g-Qjw7a8f(zW-zRsBX56U3>a0vsoj@xp*E&;E"
    "|Z_ni$5`j)k!?Tu{h5KA?)#^OI{O$kUk5&$jUT`iJOt+n271~#ps_4uC@I(O;t)k(eT@%jeFZXUjeS4n!cx7K%fm"
    "!#fRgKgR8wda}>kZvxTZ@yYJpEcx1W;`awEiW*mU8i<Scs^9&&<pJsZkCR<$>^munFB10cF-9+UQL{zw2TIIHQZz"
    "AV*Az8(PV4KF>bxnT16Sy6(ymf1S{}6Z><o^k|Qz2NXc*QHOhd1%WSC`2(3ONh-xB3S}z)o#QFny2@qSvt-uY1rV"
    "^zq^Xad+3FH;)A3suf$w`raT>yHQX@k}gYP6Rvw5e+*SXKPnk5Q>G1~CMXsBv=rE&-64_W+z0!sg*vU)({^%h}Jz"
    "Cr!iCvib|K6l`s}xZHr}wN>ck^l<;+46i(=P9Ff7z1Tva>t8-??*DwefBa$Z`~bdxwxz#6J3rm~?Z<=D)4$^buU_"
    "0!uQ~#+AKZ~$rM#I#K@D809zaFGA7G2=+Qt|d8c9_6I8^PjjaNtco`k1&G}&aYqOW{F(MdtyqGd;Yt%|6BxiQX*V"
    "G=XObTX<$={GMpp%<ICSZ|c~ls9t#Dg_}L*Qhg1vH|67_qQRv=Bxg+wdM5w4!rZG@A}K+1p-C|exFLe<+|!`fu9F"
    "@m2UC6O3G@0ZlBJec5E#h)!ldB6_E6Gxj|u@uv}b3f!3!`R80&w4AoJfAM$K4K@8Zd?!Ai<J_u#mN-QbXk!7o)(O"
    "y{$hkb#asJPbiO(6F1y6lxVbE)4bJz4yec<C={A)J(bRnk^-$tI#A@4j9A8mBy(jETe#tf+zpb4T>J+~6eQ1xKWw"
    "y{r8`2Q%d;FDouNx3L@0*}9OoirjN==z;MXRGQHt3DC8#sbG4bUpex&|L_%b39ez{{-e)*Ht6l#UAldv%#9l*4t?"
    "q6pxC6oS^CBqgEFBq!*1&$e)k>r<j`COq}Nv0(6n1w1tl8|gYRg77oG*Ya<@qfGNfM5|E8}Au5Kypg$}=qb;pDT^"
    "%t3mh@X@Vh1q}lTb+`#i#N}O=6t*zIFDmj-((jTd)eYDgj?rIm!dSu6}t#t3XFy7|5>^m%ApNgM;k^djD`qeY+eo"
    "7-ge2~H8IdHH_!wpdJATc_*z+{(T%O|yw7L|vr<2zY1yOe0)&MDPrI(p+}9yWFEhez)YgA@O*{5>F>INDV9^U~z%"
    "O+eee5|q;Lfz~y3k_s^bQ$neE=3S(=WC1YUwN{8Ny-WF2`5ZPh_Z{XnT)cUDB{HdZ~eD;8N#r868Q&&FH1>Wf<D5"
    "(9F?sUBRnii~o^VKNaU)^FH6%l2Qr!+^!`Apdty*=6-Rx@xLyj&42A}{(oDWZw8xJ-~Xp(l-4l^w7!e7D&z=TB81"
    "LzYA@@?318oZl6@7j^>2WxGFDEZAyOO?!F>0(Uk;wVe%=J#<t<;Ab31qNOOGf)fU!AYxuUoZPu+JL4kyzkDv$6Le"
    "Oj$K>FlzSyiP;qvqZD2WP9gz@YjB0lJMR3VC(to!HZWf*Rj-6_+~}uq!_e?@M9ceP}j>ez44Pxbnuz@7NgcdW4z5"
    "NH2HPe#;`ANg@n72M-sF1WR+NMGmD}nH>4wYOr!z~kN(Ovkwc6l?>cb*Iu)<zj<Na%y&UtmYUSo2zK_yk(d38W7S"
    "c=vLVFCYu<H2@@Oiw|fDvI9DMJnAc{<4QYQSAMIP1-d6#6KF^8jdAzcwTgndW2V%r?1;Ri2`z%ROQqydekrjm|`v"
    "kUck*lJYL<`?1Boy2cpD-lk&>2Vz@YK~wMGc3W!h*+WGd*UUBq*2#;*@=r$-rCxo7b6VMGNA^MNfjQ(Li?TjWwds"
    "ck4#gc9>re1E|8ez9XB~=i7ge4QQt)gzl=O8%hRn+i#<<@ldfYFshXPES{}e4M3{G@PxwPUsKJ@AM%v(TZ?ITBVr"
    "8pl^c`N|z4&a<yD$j$>1@L^sTwpC6^r`QeX5;R1b*B~Zd{MI)*R*fH2L5Mg;jNlDCOI{0!Z_R;g+WK_Y*EIcGw)r"
    "whBCgi#6hc4{s6^%9p(I?3VNd^0m`NgQjwAl)Tt}ze}t00wxa$=D(hVC30=yxKi1OL+gJI!@36bZVyvUNucf_X_p"
    "7w`RT{jr;1)K46Xw;>wbobh{7M}*wUy3wv^lNI(K4-}%i%gMea#=L!pWPi97B%LTRMimT0!ZP!K74GM=KSMI$@sa"
    "uJk!Pd#KOh*&pn4m|{4oKMpmSuIFdC%;35ji1M|{)?ahE@cnd|iOLLuxbE+QU})g`T5u>T)x<#TT1#$t=pF<GClw"
    "~~Qhpi+C{W3DOgfu^h$rzX7Ufpj$ngE=^Fk^oQ5tL|nzpIEiWzacK{cPH>Ov+H2EASn3TKK-ju1lz6;vuM#hSilG"
    "j@hu^(auN>!DW!0E;x57*#Q#Q^KP&et-IW-wYC>;nrm+c*O+^O4x$ReqJ<%NRQo&o%vLo4U~{14%=F-VW(@e*J<m"
    "V*2rMymin=43)QYR)V=q-<i7dUm=!*)=MgcSc2}NCT|htDR#f?*Z}tz4r0jRJ$tZ!Mg~)I>w_){QCjB}K*CX%W-F"
    "L$-pCJtZ-EY+W!Ke<sJ*cij-ECkt$>qk+DxC!%=A(s9C3Np%WT0g)c#rcznwSyx0^37xfp~~?O1Z=&cKj{aB9+{>"
    "t5FLHt*QWk*c3i-JAX&cXv!zm-aPva{a_2y2d2{q(n$%+(U?g}_hzc~z6W`hL(J)cx`HZW6ez291%;p^KCJ}6(O~"
    "RkMZ7HPBS#uyE`vaC0=iT4`f5oobJrBA0W4e5lO^j&5|`xs^BSIErVdbslAUTpxmt@)egN}R=^8(YBNC5$O}`k<B"
    "0p@uWFIEh{4IBbahgZ)!^<s;<9-!&mY;gIGkEp#^%9=CJ=ofLF7E_!&D-kvVCxOP9}?@PAR6KDNMy4Zw3!y+{JRa"
    "dx3=7jf*FW?mI>6+XDAiC^pwLx4c-th^!#in==;?nmal<B27mtzYK5(%v}xh51PuB@w&(!ACj&=U@|}QkdBJv*zx"
    "IPI<hr_!s8DGQGpw6>UqmSxLrsjG&m0RPQ7<V82#13wX$y9B>>q!DqkF(G7+fb70GGC5AW`r|zRg!BRBOZFuj`C1"
    "gXqKS$fXkrOVX)3&~*-dp3hE^xk?}c>NB>Z5P_7eFXZal#cRaRF1)Ow?W{LWuU5GDXR-2ts0tO!I@U`=t0+dO$A*"
    "py+CuD^K!E8!rm;=)EU)q`8HJ4Q4p-r<pGMPR9PNq&Q+6$H#J>EI7tAR|Ahhr%`!&;&45urMg>g>%G#rc)r*37Vx"
    "~``=1@<Eu^#`C^(5KROfQF-)8^Yy*aU8?P3@?MtTtX5VtZc{&N_Co>#wD{MY7d0gL_>Rop*6se#~141>5&kym_4("
    "<%G~YU<I1^ac{(lTLY^Gdvphb*s+9+46mISGB=r7UU$4T7{>~3S9t=Jlemp#PT{7ey3HsK)>xs*x>6)_S*bAF}{K"
    "Qq)vHvnX-1~C*F!zs-&JX_Qxo4!La)O-G2mHJackbQ`@=DL05p42ec56Y`(yfoD)`@uh%fXRnY+g&g-qHF{czNaD"
    "+->7r=B=i3J))1t?+!i;_K(keBqJ-gjH176816&%w*I~mZHpu5a~(EG>FG4b>M{?rUAi8Xhc}St7pdQ_xy`2Reot"
    "d?HaM%^*Xvtr?J10IH2a5{_-l(H^<@8~6D!v=G<J7?{eFf&w_sa0o5Hu6GAqV$ctjO-Kb`IUbl`4#>g#*o8>|7xs"
    "1~vU?r5_37&6Lc+GP@3ZV6T4XBLE1*0T%j;ZG|jae8oauy=m&Zm_@i;ltptu{_qL^u2lg-wZ#=n;hNGA&x)z*er~"
    "hvaqmcn{~*skdoj?6fwGVn{uKdntv>wlW4Kmk0&1v@Inc>Bhu8+nQece6Th%ZvhLvE<H`Bo2d4)oAO7B8HC;FKvA"
    "M`i9=YsBeBiCP_BngNSu;{!3oFz%FzfbYkH5zw+g$4hn6Zq$4I^4&oYH%Bu%6}1($%f&oo3c_{;oDxxzUOBn+lGf"
    "A+#~8VnY1_S@4pmoq3U!&FCBWHt0h=yrM%*oMPE>Ls1__rZzD^e8+^%`@@OWXx#EV$4qCt$=hpJ%UPAr4l73U@M="
    "buRT+KVY#!#?Wa{fAngiM!<ddMqM6#nvlYpXS0O5nL@3coaqYcnnL1PPa$HbPw=2B~0p?@=>1rZH9n_pUYD4P{sh"
    "l;<cWo*>0&{_z7SaX!U^chrryLSDllz;A2?EHZGY@V+(8#}qizqoAhgBXY`Nz*8JiI9*OiWA)qRZ%R0=lIoIhHct"
    ";xwS=hNwCB9f}`9<!n6EW<^=zIetu$~U-D@jXNs{^j?*;4`rx#=-|Bjh;Aun9Xz=3@V%cg?43s|mmmB}QRoOEj93"
    "vv4e%xRYtXoqWCs#V?i^k1g{7F1R+&+Eh?XK{l8~G!S@Wht@Ck|D32Z&_dn^e_oU_HsMG<Pn(VKhcCix!Zi=S%5C"
    "3TfvJ(W}vhiGzU}La3&PI#00$5wPiYE>tu%VKR+(L|;X&q;Qa>_Q1;x0Imaei@D&t!B#WRR7GWuJX4Lw2zv&{G0P"
    "pKdFN{LaerpheM8@lFUA^{YWL|=JO+ROx4XUl{MqxTU$(I{=2PBmh~nd8A7Jw8TURr$m(jI7&rDPVpl85r_UV4#J"
    "l7tsXhuOhfJR8jIQL5wFWKm=Oh;?dM2;RAT0nN++1m06U(Fkj%znT@bRiN6i)sX_eNidEtU2kW`rU|?QM=40c`|~"
    "tOR!me-321q;BT1LZ+(p|oveO8!ieq~OoynPfa<{CdQ<*e<_{sArkD*r?>Ew#2_cRTzQ_TIu}qq}#f3hkzB%bOB&"
    "rSQXn>!UW1H^KD>$Ru$@awFBT^#uEa|UQ!OXSAEt$B5YKDICF(RMIayF)JU~l`i7u(|sgNv)~s<qQy)mBe`59;5u"
    "o%N<6cz-a8O{&XL6sDfEXANPbz&OA=|0qEVBG)d+yM47xJmGd0*wKY}tglweD%KJ6_G3A@uY7E%>-S_sUlg*!v|h"
    "?vSV3tlxmH|S+k*^&Tb#d<=xNkx<?))f$M$Gs0l*<NbJiD7^9XrXsm>|rWxlj*PR%BxPQ#GnZEGw$+M3h26Kf=0_"
    "c&58zYr`h0_KHXujXR~6UYR~6WFx1ij|FRX<=Z;-I`$A!z@-`o6)#?RaGRzd8Pb@xV9U`A9Z8ZRMNMMPpu-kUN8("
    "<CGJ{jX{9SO!PMnQ?#d_c!E-Gorv9^(jM6fd*P^l(=VQ@D<9_sm3x4hLSGq0>{`Nxb4-82{CWzhUxl6LSm9HTo=o"
    "T9>9qQv-i{`|Kcy16ntxp4Z`uqww`?zdo537Tnm>0T+k*hA?!PS(vTK5!9(WfC@=veX^0}v9o8+AI^kq+7BD8LI_"
    "*R#HKqB*VaO#tszcbUnB<C|qzI8Vz6(DA9A&%<DQn{w7MGT3J3orcQ&G7Pp~cv@e1;|{SPNBNYE6q}fH51@=yK20"
    "GAk&)~Wix@?6YysLImkhxlx8Vzoiv%-j1edy@pw7ZxU1o`a>?$QtZsRgL(SYUCoIp!!<(!H{jj@1hYy}#TDWw<G1"
    "B}AU48ire`U0ToK<e8rfmP_@dW5E0x)rE2$}3e4#A*T=z5v0Axj#Bn*N7VoI6YB@F!*heOc=q0;Y^p=*)N~)B_^P"
    "$C4^}L^=_T_B?PvQb%8J}3D)8dh)a5pGG{PcKz~?o08nGG?2^GL!iS%fdfbHBZB7ZtQNiHoJxO_)5lE{xS_FqsD~"
    "F@6K*}s7Za3uWOLh#Bpo=j}!?Lm(jup0eS&W_*P^27ghCyCjM_KYOLSlU?mI^1v_9PnJ0K+9<^xnFCA$qyL$1^bq"
    "fO)Y{P<R^43YIr2RaKq^m-C&i?dJiecLwBF41*I!)_7W0F~GYb#O))2W}S%M@}Fr^sb_0O?s`oc2Hl>Xc*mbxno|"
    "WtX?)6>M@w6((k|0MMm@kUTOVMUY#BWQ*$i0sZg~h?UEDrXw}T`OgLyR?Wch8&11P2FXU>xA3})a4y3}wtY6u(N9"
    "Qj(HzZI5(5%G;^loe4m`%yVL$czERSoWq|`U;?y5!gK>?CCPO2FP+LH=RlFJ)5PVLtrV9fSTju)Kw{!j)zf-CFqf"
    "X_5#3Gmah^Pj6R=z`q-hDaEQ`pz_Nl45NR8zjrnmUo_(p=B0mE*{Xgf4s?r4q#{l2MdGvxaC?QWFk{m|$*2G2<3^"
    "YeC>1ln2;OA>Bnm9<}&xGEuO5`fJ#f<R9LnvEMb>65Nf<Qt8$L3fiQyVm?g3Zm~Gazmcq(*=$KL^OjoM_cF$!?%i"
    "s&b3PKM`@Cf_tFF6blL<h7uzTx;Gv+x{V+gU`j<`d-l4^Y&j*IhiWZ?wcW^;V71f0F#nr0F~NC76bylL@%-l7(Y|"
    ")h3V7c{?fx6Yy{e*GSed%zKo*E1B!kVrAqvE<9}du-GDN(!o!i3<*i2q5PH-P-2atP$Ik(B79mxgGS5{_JEt;%UD"
    "(=L?UClLd{FXIYLZJJ?Nia=`WV`c&JuBjSuPmc!P^k#Mt5Lqcy#u-WhK=-}>x_RCIO1W?LhpCHy791QAP0MF`0vz"
    "Bvxi4#2dC%3@o4~V=Dq!c;PB}DSW71`Y7L+m{JQty)4^HL`5_E`=r*jUg0_RHbGCO=z8?$#Mqn`LcKyMkziY&aEP"
    "SU98;6QOC~F?-r4HQ{_D@s)f7N`ShY;ZY%$c}xK3Prg|CH$?uToi6B&zJdRcIfW)~R_Wb-4juZL)R%dvbegum$Re"
    "J25d_?iy9%a-(%_whYjThp0b*9Mvm1?KBKph_&XOiAB=<*XG$TpPrOZ6+k?<e8&K*v<u5ZnP-&!sj?x+@04=I90U"
    "|6uEy32KJ#|^jCb5;XD5B8i%b=pupkS#OXLzvGPxR(l4@^(tt82U&p?O)cmFvUsx-e1QUx)idI}^gL(#dkgqjQty"
    "@EA<xE|w^vgXWVTJ8!PYUh7`X7?8q1rR8AdpppAb1<E!Rk8^*k^*&|YY+fPr<-Guv!C-chX3w#cLTU(|ANKXD=d;"
    "1W8H>P1yh5FPf$XTqhXlrZRV_uHE|#}^u*&0aJ;>M*{at0Mnz82F!$y(m#R_F&(0>W+@OToh#k(qD}$}g?JeFj92"
    "F3n+H)b-v^9lkza-cfuHok(8s=YA_brZT|M>m;g9EpQW?4mrq^?B4yTkYI4^9t`&Sg<#hW1a+@KNYOrS3LI@;xyn"
    "XG<wMKcuplVBm+&1Z5UCaW;oS-caOdlqcCpiiTwG4&Lv5`fxtj-#g#?aQu^Gv)PBsWVDHFX@2Y28N0aI`hWc0XR#"
    "NiSO0lviwxE_?n~uad1}qk*76<n*l97X;s2ttMFa&<#$%;?Q`p(AP2uH>Er0xgOlEtlbv7@p*>qh|L>LDT-4;y1)"
    "rPmi(&elz{bh#o3_ZYPp|%cpJ%f^$QE;t5Y4`91IQGlWyd}!4IQU`x5WrE<<rwo@trzUYG38-IfDVsUSnY!;nOBj"
    "6fKPssU2ge=H6AFTm8#9pym3EM@lq%+gb2<lXcT}EzTk^Pihk%SXP^#MiU-D44&kLXw|Pa=!3w;SJcUFtwFwP3x3"
    "{@o8dPZRhQu7mFBxUmRPF@QBFLhSMJ}P6DU48R;sI*;yrKd<Sez~a`wrI6VqK$l`y`~O@Vcgp;OO8tUR|L$-E728"
    "Wg^tqYZ$Z4CMoljELPK~Dw40DLg|%)%UP~utZrm9PPiK(-#tP`ZV^V`Hc>$311C`_cN*w;kaP?D4?fN47VmnMxy`"
    "a#q*DGz?hUO+(deZJ7%ADX7a)x!qf&J^ROZD=X)JQLD!P#+H`9j=7G(>P0+6`%+meckrP_^I%I&U?!>%I%)D8s17"
    "okO?41?R~#*{pic#V@e_~8f$xeU36m#vA8CQ*`+vJJ*fkYCPz`Sg~SMvMT?O@<}oG9`-zb&045i0H@>+`#%$1}&E"
    "_BIkS&$0$`z@pbTSkcD-FzXm(YAyOi}L%^b1E@430%U0gZ(Zr2gx@QTWI9S@~NhWOc${85MO2hMA6Fm)|mW^?2<G"
    "8>;&|)JD^A4WB*JE3y<oQNecdM+SR{Y_*AgU4#f;u{c`>R(s^th*g_iWnr#6MG4B-P66|8G)hSvwh-zs=UtXWc3I"
    "TY9zE#t`qj4~vw1unOpT<Ny1LGTXZ-O2wgo_nccYAdPweT1>|k{>1JTx**Ohs@4tEDD{zH+!6FX&M`?`pB;vifqN"
    "k{dWBO*Qf!?tFe*+6CV08}&nH|`G#}S|K@;33WpH?OcKGgqgox=>#R=AvG;bg$ArLdu!PYn|kh$Q6DZ1=Xg$CYl6"
    "}vCd*i5B5l?qgbZZeIN!_pf43^4$e=VB7ZtjE^r257{Uec6CzT4T$e9eg<0KVQjxg7>G#AFajs4J+}%h1Cy!fQ^W"
    "p+749ija4;*x~a7+L&WG>QrCptJYN3#i2=6Ge)-h%@;fMFTY=ArRZ<$T8F$-LW@4Bl>~Dms2g2d7MW)ftovHR_wk"
    "C5gn=7~{Ocw(7DXxmv>62N3rw?iaN|KW#j#Wm*lHD5iK5QuOkDp3#q3euu?P6X=1Y@q~!%^=vP`-jq>wDRHjerqN"
    "g}<2|A4kty$VNg4B&g7B>dE3c%!}YUx12tHI-DCJUHr`S_^imM2?RGn@Y(G|6-pwxh$Fd0uGgmfsj}k{mQh=bIqk"
    "I8(J0Lo8c0nn>1FlG;I)>-SW*&vp?p2Ld2z_tYpu%U+S4fL^EFUgz9jDJUTTxSNixXdFvpwCWeqBkk^ty8QL381&"
    "WBj$tWe{AQy3~i(N3yG|8nD&s@_t}VV!h;?K>26A?`TM4#qmp8w0RP`}WzN+z9$+$Mk^w)Shwvh1C2vqLhKrZ<wT"
    "b{gP&hwoLhzaKnd6+_Ck}VkIgA+^siifzDP88Yf@v@rQTRNI_vC)U;R!t9NCs&@Lz&_q%tz%kJUoAV8fQwZDACK~"
    "NMfooB$lH#h4&!tH8Im2|nHSCg)C^17N*^C&9FQK)rA;tq56v%QZ8Fjvx5KR4vL&p`*x<XyPrjZ$fPBUl7t!ex?D"
    "t@2o5{4>_CLzw}7W?L_>23eEbzHIH;n88c4gu?|QegJ<>;<xZURl+ME9HB-qAP#t?NkoB~=d+oL3O3(F^gW1Zg(A"
    "2<oPrdJZcH;8!+fYnxEUK@A&tk$S1~xyIC-WCxTJ4XS?`POSmKH{55cZ7_8@|}Mgxo4B#k4$X6jiA=ykk&<k*18l"
    "Nk<5;3ToC(c5h0{&>lT-M!Py=-xTUHe>XNT^pZH-tC<qSR&Nf!MVk<fAEM@S}3cbOs=nq{ITi>Gkhc02j4Yh`W9y"
    "-s<@XM|D>!pdA`+m_m|+rT0!Dajl;N0Ra<4-(2>J~f!p@h?v6CUO$dexO`&!STuaJPGDF}2+Z8t}@_f8GR8gVjeL"
    "hKa-ZD19Nko$voIoJx1)t4s`pkLwW$@|f@PB+du>0yvlWRuo+3u30CWdV|VHLy#Vq8d4S^IaKU|CGNqZwF;A!j7Z"
    "Z|SVV)ZhS(q5{@ko4Q>lYxkk~Z5Rya7@sr0roIYwT|jYkj8Yj!BMd)@_#9zG8h91$zDUj@p^W3kdWQ%BlvET59-x"
    "3!L`ZB5aujxH_e1t_c*P_E&3zF9F3V^l=3<EM-W)+xPaMQa!L<%?WyZ-@yC<yL4mpUy^*kz~tWq`uc;Ja*t0x{Nv"
    "(gVaO4I{nZF6TmyC43FP&(i!VTq2;TAuE@?W&oI7o||Tl+R6LXm>3ZDmlfzpKHh3+eS;GyFt4_$rd$tTLe(=V>Mw"
    "6L2})%ypJ(Qqbz!2Zr<q&%SR&UrE9O0Qj6EN!u~M%)Mm(yh#t^DFLXrSRjn$0Br0e*v3vz_j&QBC|4Qdr711riGx"
    "uy$0^^LYvTAAbK-;ZBW&wLX!SU(4gVW&0zr#C#VC+C7a{wefF>SPqur}XX9s@&q*WkDL?QV)7?-cmORaE#@{_uVM"
    "W{=hgsz+6D&q>?vvkB8Td)EHC<w>&B(K~S5I?0agcVQqJ3n(1zT?5jkC>WO;T`&I5&Ajit1CO+?<v**1+Y(Q=uVv"
    "l!>^#-LqV|%`j^=ZpcYbO<-EBK;yx11jK8Sw<R>)e8TUixXyN^2>Ah3CjV<Ouj5|5(|wjBw<bFk6>>xbZ~#zxpFN"
    "JMVV4kBypYHDjwYyWuf!@=49L8lRc8wOk5VDF5>Z5s@rHa*J#$kQ|17<-UH&npA2*bs8Uc%}|t{0+pEh#(x(G`U6"
    "va#rLJ<6U4NGGT1P{l9ni3lP;f?@hxo<gt+WkYv5!u+rjFmIu1n$1V$s7`IGrdCGZ_G{@m0_zWr7P!<Ho{5goOK?"
    "JO97ccwfwTCt-#di;A3>A2vB~BP7FvKup4*9Q8dZL2#ge?z$!D$OQ0Ge(HTDV@Yp97R`4he1Gw3mP|Q`CWuUdUn0"
    "LJu}0R#8fU#&+rg#emJCg_e(}FrDE-Tf?JZm|Vk5Dfq`5W9-JrI{pIM6d(8g=iv0<?EHBDm%*o_!*i(8`C`i)f&m"
    "!M6kA1F91(aD%Bpa-%sYI7L$kq9I*uSUCgQkikmk`rA%_~y&n%snL|ELqW(#HHYX~sw#}E!o{Sgbc!RNXL_!;adp"
    "hM6|$aYnl>V#R0$s6!DRs<U3U@=|CjFUX|5V9v7csvIWJo|sBGoZ-_h|qm+amspKN=s_QAaB=!KzE+k+UfLS3zch"
    "h(;{s)ta@v9R<i`UILg2|bzKK9NAHGCzNgeNcG6WkNK?x@H_)jCfPbNMgqh_m(u&!>{x0-{*N0*r<#URM$<$`EZc"
    "fgFDsr~EnZ9(Q11a4QCxn9{<{1GfDuSL;fJmyoM3&zU4i~jX=m1bXN0@0GWeY4d1+0b?+**Eyj#?y+D-;0Lw48{d"
    "e0Kctz#gi=6~r7+Bu$*a6{$JN#zw*lm4I6XhSxMHCu~$4GmtqAAIxHCB<uy}w|P(%l26P0rzp^b%|lPXT$TNUQ;Z"
    ">xD23~&%%_T8HipbtFcFBIlldyf`LaheR!BY_iDfCng@R-eP3zNn23H?Ou#uXPrV!!l_lIiw%JS01K+I19&;m|5N"
    "2B6URkwipN<}3U7YV^oE6C#UN8_Lc(%F~wP#3@7hkP}>cPN`1u5sN{&r=^~FAL^bB)RA@^Hj;<xy_3-hVU;(9teh"
    "Nl0a&ww?~~3wuu>GL5s8Ja^rNK)sGGCK7Eo)`{?w1#>X|hzM9ELJyxRj&a794L1}$oLY*drU<KI$yf}Mjf%U0|#S"
    "gcF=?d<s|9*UU1ih3&85|!4We*)eQLoIw6~q@uMBo14%&6n6cqmM;d7HGll$ULdF~$K4neUu;-5YQQi+T8#_5fFc"
    "!`DnI*KmPM%_ap|Foz4+hM2dOso%9%z!{5S3K-20Wz9{aBm1JvyH%_QJX*B*)h(E8&JHV)AbddvKY|8W;FEvUI^5"
    "M>`2^qiq<c>k)o=7s^S8XX5w8%fC;{NWv1b3cEE<Yajg$VnmWUIdYbV;{#qFA!OCu$y-0PfREwd9G6COYAqm-j%6"
    "I4rQwWGD{Wbu&x$kWB_le=zV!X{f%yn`~7RE;b6tn+tqg_Eke(;v!z)n?IP!G1RDvp&)AJQgTGK_vqZH;@rr@v+e"
    "o$K?j0nAlbtZrg0S{#sDr6HyPW3H1e`y!<k_lOaB#w?4VL_pT0Os#t5(JWiSSntJdN`l_w`b5xZ<JcLzhIYAKw|2"
    "**g(7A~yY=};c_ox6@ghqrdvh>u@Fsw?hQZMv2FK)_NGy;Pj-!Rq|!pEEqB&INtG#LNo0ml$WVlDW^6Pd)5tNS30"
    "Fc4h}GMH6NY;YM5+|v&jlLCd_LAX3R$cR1T50mH%g`BT-Jc)MRC@kSBc;8_&!m%*ppFttdisd9AcFR6t5#~`lg`f"
    "5871lwuc(inz#A=jAg{pB8e%QAOSPMhAoUxt(Dw`%dIvJae;k4)v|IycK+ynTAQPkMB5ZrMu_v9o*qYw`TjZ~2Ia"
    "VKxRZ)5J%C&si*MO!p!3iS?u2M>WG0ERd+^U!Onymf@Gq4LgM%-z8F0-QzeVl^<$8>n3y<LFvdV08s$u@epe+gin"
    "I>grP2X}4|~byBG?@;1q;x+4if*We`0vl6iFbZ-#kN`T9qnh8G?NEZD~*9xu$n<=TARe?~(0b=Gw#R3hf1!<PS$)"
    "cLT;L*OOk1iF70sD3+Ra{~nt&veJEjCxOr518q1iFSJTk`xSn9nr8tWTBHlWdF4TyZ3b!jyM{QF*$byGGYqk7$qC"
    "Y(EX8X|e`lJlinUG)kuB@48oc7C~f&4_btzt!#S_g_nAN3mW#>-$BfL>?I=r%RycZkOKD<Hf+4u%WZyS+(yfIZ`r"
    "q}(Sj$Xh@W9HRZ>lWjbUYg-^Y72p<!jq$~R~<$dq1+8$5@H-%=XtscD<l6kckirRAoA&kq&;tuSqCK_QOHdjxzD+"
    "mU|zYNeT2W6;y<^3?WI^x|Rgq*N)KF-))mnMBC*Wa;UE@iV*@+RLOGsxSQ8kgc;K5R6xAd$kqaU8$Cc`qH}oA0Qb"
    "X<u%_1Y6dG8OQMmZ_#g8UO*{f@z|b?m#UvIA$@aTARXyasMSpgj(H#G5Nmabsj#TBXmfW?<_W?wx?((}P?_>KWr;"
    "pM*9~4mZM>$&S=ht$q@~+TZlY07_jC%duBFhfMD1$rf=N>sGdZ_NW!+S~GG{HB%<v*{x5+#tn%7YTzS%hc=x1COL"
    "okU;MA9U%JQ?zQgq%gQLpxy#3{21Y_F1yuykFCPlO400OK1`F5jbS=b=}Z-reN>u&W^x$RJ<Z~bF6CIjMF(=_+kk"
    ")zfy$7k4FN+@z<AC&MZKmDMySGDo<t%`tK{nV7!4IH&y+J<FL*#J=~~=V5}f5lgQ~f!a@1a2g8#~M34yd3hm;!b7"
    "~-Zj+4720ih|>#11CF7WZ?sd4iI%FsxT`$R)D&wC@c%fDn6SeR?}Ht0q!TscA<$YH+vv7QD5XY+1#wBtwq7-9}j*"
    "yJPHm!emr=0xOaZ=88+=TzSPPf)83Y{hrYF_z*6c0#aY5dtn8@*--XE=Hx8zG*Z>2PQjf}a-9hAL!WD|*#4y=y7M"
    "1K2W49Fu^6)PF6&<I5k0qfrw`kwagYD-$m0MG_LPvSYG8|fjP0HXih2PeUpO`|TU7X#|h>JrKdHLDNjDVq0;)9O)"
    ")oe@q^k@a&YFD7;ov#uQVk|U;2(Da&cZ4|Isfr*GJ{U*C0`s(E$0?~1R=|%HgFp#If0{auTg2cY8G{7jjM?hf>!c"
    "1kmzY$Tz)OnB*Jgqa_Kw~m+4Tpee!~aU;tN7YyzPwLFgybUmqw_VS8&or{CLW&ta<VhZIi%v-&t~nJbQ7uA+V8b4"
    "bX=gl8T`25ts!an(4k?xZ^K@v8KI0JUu%PZT~Cs`4k1Nvf(DxL3EDyweRu$kJ>!^HNv_5*6%*(x{dF*Fnt#he|5U"
    "pTA~xXz?SDz$Y0-kGAlegtRdd5*iy}09UD0E=-{Wl^TS^cb|p?X`oe6&5qqjU7|s_O3HT92_%qTxmf!}o$4J9Jo4"
    "89>C;9suEUArFuj)dH?ZWt5D>5~LiyVDw)iWH^-rN|g9&D%;yVgls^>8ifb+>k0+aJI8|MUpZ1n^hstj*<IajjkI"
    "99Pbqz{Bde(FOo(A|A~r|JjqQ%O_#*1VCQWFDic04SWC^?Co{U@&0BVlS#TpHH$Tq=zXzs4^{5hy|G$LIXz^fKWK"
    "A5ctdM^d*_KZ-r$7zt%~G(aN@>;k5k>`@7%2o@6MXJBF$IbH&S=k5Kbw55)-cst^|sm_1;hlMYk!YSvewwjhI2|N"
    "zQi@ILuIDPpW!{MGk?{nEJ)QX(S52|3weVE4bGCnP;0xR;q%M=r~PH%hTFn@VoCq7D4G6Ttd@O4pc~J_Lzbl27Z_"
    "xv-T|*Jde0hwJ4;<V}FW7BTb^U&SzaH_P1N(67-ZJYiX&I)q6>qkMm+0Rh`yJJn$$z9NWhsfRo}T%j_?5qcPvDGB"
    "zz)i;(0Ff4D_daQR@v8NWXG099)#n>tX-dhkMjy0Y~<6s^bNy)>Y=T@{ONg9m6=>(*O<e7Rb^h0mX7=$s5Tr$Ni("
    "J$(E#m<h@m`{ZDsMOj=vw#Y(MT+gBcC?SOw7A1Evi>e9KaNr+KqH3bMUphj0!pVIKJ@Mr&WeeOy59;gK`p%g1fR3"
    "H0xc;(hGO1h}TrCd?=L$hOGVk6V*BCp&UqCRr?qi|3_W5b0k$USzaXgSxWu427&CMdual1m%tv=8V5_QMXJgx9k="
    "W+w8oC+G>d>HiYuFCn4K9!vqz&0@OYKrnms7t;{b`tl157JY1+*Zr)S~Ap4qT;$Vqrm^blu9Hnx5*1I&DaY8zm`3"
    "itrdO*U-5vc1d@zq*9M>kVQXw>AoTA%`3HG%-HV6adq+*z4?Fv-f9Iy!c^~CdzU3s_QOn*kcUc`HuRR^*a-*49*P"
    "cnLr*a3Z=1F-ohrlR-#-%U$6a1j3ia$8RcyeWCYG#QC9g5q6;chUX^$_->SA^UzXN$5@(}S-`)xl#`F3KLP{>Aq0"
    "73|gZcpKLqLf}!bL_0k0R3Y+FL_T+j3@Ru2jJ!AuQ5}q->sV?Sfv<p=SG|M|q1N!Rd?fRmL?v)If5n-?@I-)}(I4"
    "jXL<+Q2iy0d4=!d;*5e8=}9qVz-xEhYMcn>*yTwGX;S$VM@Q|*z5iF-QA_jGN<bsm=5RhpS=r^XrovY#gH<!az&h"
    "EjuE`^l7)0VycSu21qb87=;xx;sm1>6miRXRrzOVT*JuT8Ow~!@UQ6qI>6B^|!(xRsHQP#4YT43Slg3%%weQtJi_"
    "g{mTu`{O_8IA6&I_KrbMMsVjfLK5@l3uHVd{V1J{}G7%r%m;(c=ADm4VWimnlCO9T`_zIlKd99+QRdU28?>m(yaD"
    "0!=Df7`8V|I~tP{~BT<BdojF(D{akW5u}T}}Esk0K}LNe--IzXmaBbP#_C<LmIZf)@noTeD8LyAE}^r<mx1Nx6gt"
    "uDg31@L^~)qPowkiH;Q}e*$<AAFZ(lWBVo*V1u$srl?9<m27<Nx4QPLPnlhxq>*=_wOe+eX8CC1F6}I;Dph3t%Z>"
    "ka5p9mQHs4&`J=?kePa|CrGk@Sy7B1OtFi!Kxnn(o`!L;f@l8pyhl=ZPnqsSo|K*{pH8kTWopq*)*>}H;=e<dl#u"
    "vM>Nft)AIy4m^hc{Wb2=Y;}+j#zA`4pSd<@d?Qic6qU^JAMFsI_KApJl=g&mhE?ePM9LbE`uBl6Wqn3)KyV&t*Sn"
    "m4QVVr$bCSAU3Yn2RI{{E%N#=4B7M#P8ZoDW!r8Fl_<Q`@Np4snxM4S)@472ztK~L|V%fS{j=GJuEWq<80HS;rK#"
    "!Qn0J;YS3hGN&PiO6M&nREBHfluUhtjC4#(Dyw=p}g6t^0u`E(Er%$Gc%`n2HRU>0*YQjdL(Z(*_VJZ)8ci{2ebC"
    "#w3k%$sy1L2<@+VIla+qwF<|&celc^#<=W_=V^-2TAj-co1ehG<%iwpup%;!pji;PyL|Pfj<E=-Q&mME<>;xbI<s"
    "cKyHxAbcvx-AqFFh~s}{0fZiuk`R9d!>QhwHjttpMCR{Pc=PVEs%?BZ0Qi>qag&0<4a`LyH#*#^*@{%%=>=C+2yl"
    "?i|m(stFQ1TY6^I;$4#hwvfc3C$whk6}6_J2y^m4UMx1{y4^9S;)LXPLrU7bcO;Xi~3Ab&IczzNXRecy<cY(4+At"
    "iJ`E0kIyydOtny{okuiGz5PI<eYj;zPA+?~FwR_ptzbSn>zg04!0L0G!=m*=#br9<uZnG`Qz*{-)H5abVxjAVj29"
    "Qn^N|TaAyt<iS#EPE?F0{i)&Z|o-U%~9CViDvJ@5zNXSt^DINwM#6=~mVWPW^3nSGV02VyndhP#Z3T>d3$;iO&%w"
    "km>Nx?gbGKdtd_X0izg{2rUYhJ1ZZq+k;T!L8ZP{9b8Pe>-E`~#)M>==-b+aLnitp#`P66nL(C(B+JRR;sNg}U(B"
    "Oe326iE)-Emn`Mc1{a-`r#HiDw=zgx2fgyPR2%DQR;?3=I=9l4ijyg8l5$o>p^M-OUhf|6LSK~ia}QDi|`03)$QK"
    "ao^wTRyA}n_J7l`qQOsX|$f4EyJ=hKKUz0kftO&?pPGE)nwFcB~Hd;xDHIZrQV}0HvwAmg63OUe6gsd1sQzAVeKG"
    "R_3x~S>^AyCPZ3-9u#^U@ncyLsY!*zq8OW03o7NCR?RKtUQy)fCxO89Ilrp((ZESxHwjU*gGVPkeV+;L#;-iS6wU"
    "Ijr0bnw37Z2BvKOaEGC4!<m#AQ#dBk$I<4Vh4gZYB3xz$=}92kb+zrL47JGL9A#cZ0i^fK}5EAT-H#BnT)%rWa(X"
    "pz5Dlh<vx(5Is2#3Ys95?}U*if(R)tSjLBB-_CubC;xjdoc^xr>fHJ&oxi_kSN?YBBUdV0(p=*t$Q^Wdxv{sue{g"
    "~bBQW>Vga3Z8kDu;W$=Tk63nGTDizS<Z2jGa)Vyy2uwo;p>W>JWw$*8g&gtD8!3)opox#msiFaXX>wpe$~FsS*jg"
    "EO{_dE4!3XPRQftZ!;?Xu@=M^+|AhOQUR1sp%|5n3&yq(Arvqf5-$lP{)`p1*EOf#&Q?#`eNxwKiI|N=VH)>9zZ!"
    "y^rhu;T<zMdhYM;DT|#MX2O6fy7&B_yY-)QA=Ord}cVcWyrx@D?ThTMKxt|9(cZ{zzCm7wH=J2kXkZtG1DcMc#4I"
    "rLfjOq(G)*mTa7t!qiHtTLMTvSRnF=6c4lJ>(z@c-))wy3~7L%1(@UhWLGpFaoo$Ntw|If-^&yfm$P6ZMrbHSrc="
    "QY^h)#o=sBKn7fsJ#j&yz9b5OSm7;1Y!k}?U-cbFNR8hT47whqhDktmb*0Yx-C8!AmONf)SkqZy481x7`<?1*^G)"
    "lkut+~$)<w#52d>@OP`gMFE9dc=l&tpvu^mW@BH@)IoIUhek#L^WBkS<13%*Hc6EgJ~HI<BYOfzkJSkq#ocdV#+I"
    "&~R9sw@J|Q?JkV&I+wT{su`OB${ZsLSoZG_Y#wd8TIhq&;bd@;)q8;7XfVx&?~SY5B#eG6`t@>>;8il&t7hAt&od"
    "3uEUP#5WHD(q{y2gyQL{68%@V=>)=WRdLkilzCQjtWX{*8|I}6ge)}<NYDIU=i>@&Dm5lSk7F~qy1S*PvJa>?g2T"
    "xH^2m7k)C6$_%o$ksT&a5T~^f(7|ON&_^U$}f}q@c36N*C@TVUb4sT92O!^!gWSMm~{pKDAb+aK+b)%MG35zHt?N"
    "=lQ*vIq#N-bxB5u#r3ez)#AY;yaWy5*|&Mzfjs^owJR4a#W^dbzRqAR#275B$1Q|LWr6QV__RgHhslqZ8{PX_Fb3"
    "~I-GnrMcpp`XuIa4JHD@?_32%lc*IDW{v@xxfBWlQ|Ks~h3(Yvv+7#w1bF!i`x!>)$5Sc8t=wR(&0-R(`c#TXeG_"
    "lqwV=1`xq#&y(m0<(zerI~=m`1oj&tXmG{uJUE6dZUtTuXB=((s^u22d&Pzc6)|BCo4b9Q{5qp?OcL3WjQY@D0@@"
    "(>6$FnEFuZG-vL7;UZ=YzTG#$Z8~m*vYgq&9kx7$5I&!V8Qf4j9!7T?>20WC~E{>Muto`Go_lKt+5gyfHciudrcL"
    "yI1e?2%|v$e5=>^h(7c}KYOxW0sjq4Xq0Th5wJ4Ft5!NMn0()+4$I6)3<(pd^*S3^as%UZx97b4uqWAcG0mr$h6{"
    "9&1}$u8-7WH33WbrnyBtiu+AsFZn#@#qQUE?D5#$thPFU&fC~+$cno;6P7OjxI^I+IocLWYMgRFV%;B2v7{<S2uy"
    "(1nI~}%{`I0pEd1eU@8iMQ$=?3K;M3^`OK{$lTXXkvBlv!W0){&5qf305?E)i)L^ATbhowRlB7}0Uvnu4Yv5?L|N"
    "V-BOlxrreUT)Z4^x#Q-W>3N=hZJ|KzCv)G<>!|}@Fe^peDd!2=m7sXJ2*Oj;;R+jG|Jd(;7^xao6MfaE%~XXkS%t"
    "qtf(xR(OWC1!Nw1#nkVe<N+<zwK5I$OqcVHJoWRFCm2&;z2kwQg@ABQoskR!i5ahA`KRz?M5#S9e(zL7kPfibhJ^"
    "tn3-IK6TU-BCj_qW4n29{YB59V2wr2VZmQltAz5~D4dW<_RnLjr2LLs|qOeYf@luPjizPP0)S8-P^KN7PaCj};rd"
    "E9qPE2QH(Zd58$v_7pG{IF68Rr{_kdjgasgG>0K+a9Ikx6Q3jh>$b0XJDPyCzDpXd;3u_(T+*Uug>1UtgYRM5ml^"
    "US?yuXUKRR8<TDjykLg0pmYyHqvZI^VooaLGF()D112VgZkR6J?bDi|fcA9R+>kA7pmN8Ur7ec5w}P26!LS%faO="
    "72ShJmQWNv$I6z?$T`Fhk?c{<F!A8JX!qfLELsFr|qzm;L(a8EY~dEN`#Jei1>%_v)1rHE5)M0cm6z{;}v<Av?mM"
    "WLs`PI2Wobq$DL)kLouU~Bs=i_IM$h#3-k|wM#5c9qwoI^wn<VT%lGTBEKmMZlA%!W{7;=K^(6eEYY<M__C8Lvr&"
    "BoTqp2{q;^*ZcOpg}sOUW3LJ-i+M5N^SIj*kN1J|7PE&pUwl@a{NZx&k$uV!aHNb7{9iG`8|5^%c!7anJfPZ1#bW"
    "!~Dn;@~Ru->{(4h-K+JbM-yPjBBQbp8WfJByMFodYy}@hwa%7U_xFzW4?cj%I)dnv6uIcN%GfmDH-CP=?V&_|o2j"
    "CI^y$NgkPN3Kevn;8ciG`l(0Outu=nooPr@gspN@_WkA8X*KKb#(@jeL4T?Zlc_svggWWW?fx$8gqbo9&7@oz^@J"
    "llZ=sx@dF>dC>;I~w8{|Mid|F1@_kZ>p7H;mv*t*$seY60*6%8=_*WC=}Q(s|_G9MxCQDsxn%X8Uc|?0-zh0^5+2"
    "ZL~0YGe+hNEp55s_6!a#zG^iqudL8x!?(GQmMdMjUuO~$c1mi-L6C6f4FKn1RR@%#^X^u?oHNe~DhNX7!Cw@)C;1"
    "nh40w8{lj{<J#XS}04N>w>hoot?_$+$C2(lp7g2V!%0@}w*Fhem1xp1@^N2|xHB{ie;K{+PAI_YG%>_9fUs8eQ;@"
    "2$ffx{AoY%sv%}Hq{p)fpJ%PRbGBR@Ef{Rs_SZap8oYk_T&G~_E0)&-W6iu{!y$+$ZBGb=X`#EF7mAx0avy7Xp8c"
    "(E_xIoywF_FXd-PD^Xknudp{Ny@fx^#!il9t;7#IN%V1PGHp9qE&`Myn<KwXNOTNKj@*7rYzl<=|`h##oG6*xP#P"
    "rx;Cv}hA8aLIZ&j*ynLS6iJha7gqpNuo)Of8;~rikbRa4dS`#Pou9L`5>!etB2j+c>y)U*5UOWZqW>3uZaMb=er)"
    "^cNI1j)W-`3ekse16j?)E@W+mD%tz=1NQA-i$ytlgGA##5${j~MYz89AtYiSaLJXUYY25jZtbjNH*m5npi8m^8O("
    "SeAQf603w#3?NdiRD?w#9`mrMeeBjZI;@Zv3_%M9+xH_^z318JF!E))OJN1nPCeE^{CL4tYx=&EVuwq=9Bti7gsE"
    "Fggg+=EEfvY9YwlXjf7E1*E2U5UXkKz`-163Jcyw0EL&2$7zzOpd6_zDiT16SH&nPS@a6Z<ZB>Z1ycptZAm$OIP?"
    "p7RHI74sgyRK&i6z8C7s$>rB$>B5>^8$WnSe|2fFGv2w{JxU@mY2kVSQ1+J#V_2sn33kFfCSYgI!;nX0mku2m=$9"
    "AFG>p#X7zz>l<cm=|%9IfF#dMlI?Eg}R17&SEgh%eHQkSfjKMkYHQ8GEbd%9m*F=VPmFh3f2RS#se2D3~Z{Pp8KP"
    "r!@Q4Gd7kRYoacEO;=lJP7{rS7oo55tgdM=W+QrS_E%AOT$$99zw^_wos1_L`W)EV}0wF<H8-h-%Qov-67QrNmW0"
    "g7e51I&EJxGA=SO{Dh<zMnv?(A&sybOakVeldhs((T1egD(>zQi_3K|pYc<arf5g<658N?@&3Z+a6a1>uel@*6wB"
    "fRy~8Utd}~kt#`5i4ao*cvso)=#CwqPo^q#Nx;S{`{N@2m&!oszq4YSdg^Ng(%R+5z5VE@P$)t~DdJt#o<2PK_2B"
    "6I`1J3C^W$F*j%v@McBkS2?gaNi43f2?oAh%MJF53L*rb79_WqG48NzyjC9Mb7g1Yb1hcBuC_x1hd2KlloHMQcex"
    "im(ns{wK(AgOQfNQ<r)?iB-#I?XXtbbS;vDp0DvsI){e5w3}RbaS~8cI(#__Z2IUi|f77x7;7Vnl0<itp%e~ks<S"
    "%%Nfac9ebS6B?<4_wMWr2r~9Gvt2Jq>8nStT{<35Gkl@d5FT>j9`f=vWHNbfI!9YCJ*?7l}z6M0O(CrC}tpE>52Z"
    "Wnj_FrykY|uVzZ;W0wQ^#^c1LQeXKg(|&B4+tu3~Bj&xjmZiw|2KP5c7Q+O^0z53@|)v*S)DaS~8$Do~S6TCb;@;"
    "TFPtZAW4@nDwwofRE<oSEWd?GnX@EWZ+HdONYCGz+)^}>q<H;dJQSQEivsWnG8@{gzbG}Mk_G_Pat*7WDX1=LkGy"
    "laF)smh3ZB@<IwxPEEJ@QyK=SL&wQxqy97+JPTQ;is9Bfy5<X3(HM0~5{dQt_|d{{0U7*1sh@kxc$<@=(FVN@m4l"
    ">?MoybwyAm0$>io2CrDBxOR?l3E9PN{_)89FlIewmk)|c+!!hV3sv>7f$C<XenmdMz*?XZaIu<hX`(hKG+Q!3gW("
    "w?&NiPtCzU30+PET-F3m|xFfzn$8_r62O_WaYtop97JApiZ8wNQ`tQ)*`6z$^ZchChk@hV?O}|09lQR}nmEk(uTd"
    "SWP>Su%RjX2zqE_SrJ33(JE)L8PPch%P$6IZfXyTi2xD$^y=QFo>(N}?uG*&IoR*9-{dGbup>!3^o?P{m*b>36n!"
    "TVb%()5OqkSh9mXFSXNM_9yuW#0kr=o#mCA6OYF=Nt0^PXN7(j!)cvH)-bnVnA^Rr+CIerfCshD(zWLXyWIHVl7r"
    "xssGw~BawDCO@J9IO91JWz(&+VZ-i;Ub02MwbCSXiF2jSJ^mhRt~zwx5Jw{H0Uo%#FTu|Pvt#XLh$c+<tAr@y?fh"
    "5GX`^^b~w+zrZnUW`=#6(4Ts8@L4j-ffJboKL3_khy;ci4Q0P#;U+L16u&p9n?lez8?b3fDjatEp0AcFPEp~(cR!"
    "q|9#&u51A!smJT)Y!ftTKl17ir3HPY3q79mYx@S<ji<17rhP77{wD}HO3k8_MQB<%>dPj8@t*`Dk|8_@5+WFR3^^"
    "}g)uH0#~I<nQf_d%(qh{@W&lP@o}u6pwAfG6oI%4cAZYjD9M@ECPm^9wE8+BOo@LT%f~hxusn1k}O`^2RbK^)w>s"
    "g>+R6yI_+ETAadQUP=w?LPcqis`y$JkA=o1C|p0vZ7aU*k5Q>U(qQ%x{_tG_rX9p=Y&DoX5FVDyYe-{$;G<YV@YU"
    "z@A`|UBO_%8VgE%Q?An@uJ^JfSvJU}}fXzu3-Y<ijP@15^`IR42n28i+g<<sV`dq;;KKI}Q-9DLXbgV$lO^Fni7Z"
    "omKY@&56Lz4HT+GnwDR$L*akco_!Iw(1X^ouBUg_T$0n>EG$8v#N-0hpHfDY#Y`4omVg5DF@cmLh|hB#Sv+Z{U^9"
    "kLEl=jj`~^^QU7vdoEO6cVaHueff@|2d4~r%w7i+ufMAnMfMB=7|DU~gVQ<{H(uDs?Mb11TZIDg1FLBsrGP0VsHI"
    "^lfq>kg2^g$2_N=SnM4S+2x9sT!x&ZVv>fS|fPJKyYXX4@iJDAe`TsdIT>VZg%fIhdrci)c~ly6soV>Sf%F19VzR"
    "pwmzzoq_?UjN^F-hn9tGh4veRBY^hIAz{lU|BOYBZr>s<)*1SO$!Ulv70gf|QK>OuGp-Qq-m=|nlSrllbl|iLsA}"
    "L~1P61TVth)8Hy&P;<B#b2ljOubY=DoqYb%P8PCOrNoLrJs2%B@YgBSIkF^`Ow9*9Wez%h_0qJf>U_;NJ*cr;ZXG"
    "{lA_#rIIpMVpsVNEYCG6Q|m!l?Mi^uCFI!F02uM>VK55C#U}%x#F6W7j~hB0n>i&2IA#tG#Yt3-LrdUGPv>MXwP$"
    "eb4ps==PPwg)bM*hRYX2DJUo4rj5UBYKqF9eOD`Ooq8T4S{t6qa!NPSVt^&u}2jvl8urY+B3%83EMUo&jPoiSs5*"
    "-Eyf0`>$1&s7s<4Qp7#b`b}R%TT%AF5#U-9IY!uibtFV5Z2~&E>DYrE1_)=ufam=)`YeRvMZSUHhk}XD5Gy&@mM!"
    "6{t|FU{}Qi@AmrvF=Xc%HMF662V5oL&h-8|+1-Vmfz6vh%%6l^!EYM&uVjvrv|P>G^V*xM<`7WGAf&4uKq^P{0x^"
    "L@*|S7OflBQ%RslRQ5H4?;_)L|RST$BLzDr&=wqB~yU|7!d9#T-+Kr=FS)Q@Jg6Pbw2>_ebDBToq|49sq&ZQKpFf"
    "lo*<3FPaFsm+oS9VK|3+bv~{Hf+Q8WJ~NI!X+dRW+&EF^kh#=9>3=jB8eYk;+j&m`fw*)7IdBzlB=Ly4KP*JN0?4"
    "Wi)ym_yXQEs@iEb$K<;Cgj0uS^F?*!uy*alNQ=iP`H3yZG*Osk*wy!Nx{w5fZ)9X1|--g^b_3?gR=UQ`m`(&a<rX"
    "LV}k-dKLHAW^ZmX-n(S2C0^ck||GIPA01qe-=me_cl@*{~U$W0jXl1<9}$Cl~S?Sd0AEbzYgEkB-_73dltDapT(h"
    "^i!;_Hl;dRer%6Ht)vlmTq`U-rRH{9MrJg{>$CmuF8s@guIJWCZC@sP^|))fK0F)dOgY2Ae>BU1##<sYgBY_71T^"
    "h>G7+F7n%zs`QO`>>R;2TbZdOn?b$95NmI}2_9p(93v0jNtwhJYugaXLs$ndEyId9Hi3!IgD>+Qwm{HX9=p4EKZ7"
    "V?~`_22-#e<C7@L6<u<>b!e$IUQ(%(8D<t#{in5xZ^$jvSp9+BfiqpscXvsrB%=#F3CW;xDDqv{D2l!Tqx+<Nitf"
    "&eM1eVp&*M^j~zQDGp@1m<ywY7F#DPl2?3T;0alK(66Ja}i_3DcPI>TTuw?m)Bek=rC{(gKB8wGCb-#?OWM*Bd(a"
    "CQIRf8E@!*B4X#X6fYBG09~K|0zI_X@f%J7^bxs*GP5S`_U_82Je&@ukeh=X)k~*klSp^zTc&y(L+74Z7C*C+*Sn"
    "w8B<k_**yxa|nMx+ym*R!wh~H5^S6<sv60N0rZTuzUu~rD#<K}R4et*IFj{i*q>)(64=RNJZkw{2a0v$>k-)nsM>"
    "U0m*AR6*Y;H6^;VOp)4ftm=y`rSff@$ZcltbWez1;@{uVf^e9>+IH{FAPbudiBDF}b>Neo#RLs+)Vj~>h=mE`$mA"
    "{y$Up=hmzN9!9;73Pp=b&6LKYE)Zc?$EwB*HjwK-j+fl?HMOnUZDJ^wmIn^XW+G(t--+oL4qt!xQ7^@f!{OMj1;#"
    "+6pd;0h`e)VeW35KkdiV<pP=VIzImk&DbV#7Dcs4)4aDpS(&lcsrlGpa^6eV-de2>&8hs9$%<`h96luH;F!z&kvG"
    "dxNony5Rl<~0sHcUmptmz)TOJ@3+bCyQ8acbwiV|8%`X)R$?&XU9;TT%@hlJ6e^p9bPR*7GzL?`1Qd(6b(hKfdRc"
    "_TmMs`=_D&{BQ7aJbF2Qf;k_m*~U%Cz+qezIvJ`B4oWulM?ygLjqx&?bpbVv#UI~Om8t>svFZIh4VD8AYqreQC*+"
    "Mezt2}_X19*OebAdx*8!&#pL0kbJB#6r59pj@?(BRa(kQ!I!&v~xl?4bDOu&;`<{{vpP|#gc%5VnIWya)+l`11`i"
    "Sj-#DmYCL-VOrH9Qs786SJv68PFClRL0UA=#AhOPxstK@*8-N@HgBta4q=Z;^LILH8lHeUan+@g^3Ivrwc=qY0xc"
    "<66_pq`uS6{XtIp+wWJO+-xB>6=Id&;uEHvR8)rn4CVk_e$0$eA*c1;ZKvQX>fgxuli~*#Tm4x99{{<>i@WtgcVz"
    "7M7e6T7)k1m*5dI@=f1A$)PI9o3<3RLM?cuQOwCq8DrQ#?>#^U9jZM^+mr;?g{>?Sq=M4pZN_#Kw)Uy>BHw<GPlV"
    "WxjCiCAn53${9>O>7eUj7=a3T1N~*<T#1C_)-5ORpX^)~4$(2+k6}7{Zdy7zc@6Dj?7|b!{oQ%Ot79lGJ~3f7m%6"
    "D;_0I2bNam9TpMrz;$x~y#I*&%%RYZkd=`m{drYQT1X>|zN%9|H$zwxj6>AF?0xva-r*r{S^M{MZC(`HZ$1uCP^^"
    "z<IYWzqLzQn&`sfydzaS-qj+n@;0c$6O%#M;{iRcZ1=-{SAB3>juEBuu9jZ;<L0(J{U$*l2W8xNUs`<-&roAIVJK"
    "&siC0Z#dz3~`H4kQdgaD0#F@&4bAACsG2S%H9bT7GROKf51Yw-Be4WnmnN<P6K9mlO&%cs~Eq;Yp<`}fva%d^1N>"
    "PI#@VR7m9t-$eIXteP(9lr^__cA>fM4(rfx0#JdXC;4?80?TLo}OzX3Z8pF_z#p9u-D@dz@>7gjh!Nm^#!kenq9F"
    "nK3LEXg^${g8nWR5Yi$r{$h+Ii4xWjdte2x%;RDJIryY|{4VUyO_a{FJWa_qUk;;N71;v992%?hha%MaVog+B!Zm"
    "+m$jlZT&yEquGQ$L}Z_*#=q8n#sk;T6O0iok%3!H53rt~KGH$;_?>pp@2{gRTH;QQa71-ffo5Je(={7@jWit)HLq"
    "yEDvj-62*9)N;hqXlp$V|Z@cE+xQ!y_|*k&&D^GE`WpiX2jAAK{6QG&yBbTVF$|AYOI#|<>hsNh2hpp;nidHRI@9"
    "DHtKf?2E-t%`@?;lF+{YA6Vym-h;wctZNfaDqak+_pU~j_A$ajz1v$?c^lb81?R1quXB6**$w|Xx?jXh+1b=uEq1"
    "zWuBdpwUHtK<`LFwEUarD-Pnpc-Ok87@O5Ci%KIjyAYLJR5$S?s95BB-fzF-GjDJBZ*I<ucOdat&rB&QDS=rSW8v"
    "X%8G@;X??<)#xr^h74&50;=Uf+tw*+E!s9alv6PNn{b;ZY$<V>F@RUI4Wh|{lW)PLV_+E*Na8aD`EF~N9DafwYzS"
    "xafT8^c@a(QHyJ3bt5r-M_Ma+=IHoChj;yd(qNCXs-#?d<_S(OO!iu@c-siD8-`Z|{G#V!5f9I(;0#Tf=o^y~%F;"
    "3KzCSU}t6b}{c0$Aob3C54612aXK6+IgyPq&5lQkpj*8rnYC~@IZ(@;vYKOz~DNt)?*Dby5q7yTWg-pk~Co)-Uvd"
    "RD}p?o#RdEY1Quuz0pT(ugTFZC`;bVgSH5~7w<=0w>_uD<%jG{9{`n57zkL)7I#9r<@-Xzm${DMQ1Ev1^929b6Oc"
    "3baLBHk&CjH5x<63hgdSnIzgI#UYfAx$H(Z|_J{=V89h>`-}>|rD<%A}H`AYmCLLKpq28o}9BfG@1>Q-;y|OyWG#"
    "$(ygMS-y0Q-~LD^*A#q$H6UF7ZZfCK8GfL-*}Z-W_zOA*)tzkUI)dCOH4omg>r=NIv5#k8lqybvv3SAfq1iP4n~t"
    "vC>nE!Paq4LUEvs&l%4(F?Bp|&WJl<lR6>*uT?;wA!)K&sO$|_a7>af8iaB_=c!_xbdUq!<CVh}(X({)ks+Xgu6Z"
    "B_#n=cOTKmaDv?gvYtT6Rh<g^@Ci49`WZ++gY5&50p;|_Hsq}f;#V(Q^<*!6Tf@Gmj1Z^NE#ZVA9q~96}5nXa5+l"
    "xhcD!I1~e9Y7$aoxuO}Px0OH@9FFJVj8uNY2zIz~&-q;8X5EJu?vfaJLezwEy$@?58l$T?^xB9Ez`c7o<bcM7CJX"
    "b9YQVrRKL7@Ql<uVY%;Se2#{nmRHbpe_|f8+)Cre`2Kz=3109CR)@q)0eHP=Uh4|DuP8#+aWup%)A}ol<-z_C|r#"
    "(TVxNhDBI#L}cws<434De0?-k%tf{y^o+>KPoHs~H3v?DrKdpIVIc+P%Vh+^f<h6k3sGj$;E8A+tt!yMGK~0%XsZ"
    "m$IOQyH2*B|iCXjKQ#o%ihqCcjD03!%Th|~D4h?amXj)Dt&Kx6=R$rp7eN9~p==&+=a%4C(0Q>X(YU}t8)8I6#N<"
    "58)aHALkVv|UW>4z1Fp>Mf(+@Q=yMx}XQ=4?c-rpU-hf@G}q?;W;d2aqTF6#$B}W9!js=yKepYWz)}e+pJGSQ*9k"
    "CnDTPTtBEvL@<_DYFr`GDcp~RoE|=S6Ha!atx-04{gRw^Mq68&&h}V%8asmsWk}Hw;ts5SKbb@3)k(m#CPuO@PZN"
    "{c1;5oUF`rYsLh61tA=&OKlS}{T?Y04PihsJeK(olC^kZ(HA;=z5sF2qBU&EbCKbQ{&n4*N_2GqrCtwm%P5s=U-="
    "h6;O14T9b{(vOBb9d*_lXBbX39Zea*aNr7sgHi_AQ4)8TzP|MJb&(S_R;Qj);g)`O?hNqV5RhzKL?vk0KOlHzGQ%"
    "4LVFW{S3DuU^%9xqr`JE-bctdANzrd2jeAlUO2lxPkCrJ*USE4GStXw9Q;u9=IStV(TZbK}mEfLS|7To~49Sc;}>"
    "R8Y$wp&du)(AAh-y8Qryr&F7`&0Cwwec~Ar`$9?9w`Es?(uV)DHWixP}`rNbkScM2;L|vS+l7gbz!33NT5xgBjLa"
    "Hc{;M`rX&pu&Sj}xFO`pUy*KGI7-I6#@UxZXy4TSl1t$=-^AD3<G&k&uqr;yLFT`Fw4N_^kL5Cb6)pFQ2>S}I~?f"
    "HG^(jjKtOdTs^VBV}I#@~G>!V7}^YPpvx>1{%Clr!L*46lu?RWYL&%8aj*QEFPXKP6`s#g$tAsw{^?6p~!x#X=^N"
    "F_v_egO`hyVaHMlS7}+%Gct^vn~1NU9?K|zSTPEk>NM~?fHd=OMmsJ`2ILOVs&52n*&#_r^bsc5m=LJ_PC6uqXmE"
    "osDTd>^L2>j%6ssx1^ra>Ga?SK52S)>ATxz*XbuJL=4$X%Fy{hGoz>8nyxH%b05-7Qbd)#TDNJ36J=k;!3>sHrdl"
    "a0&MD6iOX)+eoureLM_P3>$?58OWgt1%C(=HqO9uswUQDMhU2j%|EKW?*b)pwYg|aVKx)lPlJYcw@AuWAxI3vql0"
    "t|A!zIO~PqB*z2hy*Uj%}wkfyfUUkdC(xpy0Mhm@>`pP3k!Yekuw4_^gO1pANdp2K=`yRk0F)=f<%+b;bS~T?h$v"
    "v9232|fX^#)#kYEG^UmJh_IM!mkJ<ZYSwm)Mj_W>njfsV-xWEom#SPZB(@et$AdMVrUYW26|jDvu<{LOwuxmb|5R"
    "yUJ%Xkb9%?$OLqk9flV#Z&MGRRs*OzRpctCP31K8jVi6bYL;xsjR#LSY<bPb3?qL;PO!_Hs7dr1tQ{Mu^`4s7)aG"
    "<L&zv)}mZ8D&b5^1<fL}7~D#W`vL$EZwAlBY=zEfl3I^)3L&UW{}$G;a(81GU6t9I^%i_ZqymR#Wz>C)JKAGmq9e"
    "jPt>4+?B0CMGt$Tb9vGAO4NS-DGElLB0V=k96jDA!B8a#n6O_V60QgUx-$Vlb=qHrbKt`_6gHJnn<|K<WzqUy0K#"
    "U#r15|XJ@5)0?M0`W2vLo@#`=dcv6zF+YsYWf8C~pQ8zIZgu{oAkT+r0NMykYZp@RVSMY?k9_%uEr1O=v`3h!Vzu"
    "4bCz>V51J!X?@-1APPRbt!-ymmEmgUeF>q!=#Pb4yVojmDSxix?@VJ1?C6W`=OXY<ND)S7-<{1KmNytk~8Iq+ew1"
    "rl^Wq&bil^wAp&3B3c>@NS&@YhG|LH_o1h{Ylmtqh!NUQtR(Cx+(Ui;?Ll{mkWS&+X+i-w8<6l!TID6h_t?e?HL>"
    "b71fmDk@Nap+;MEik!cz?+2q`w^8?7Wejzb~?Uf0GMv$D~$wEYQjAC+O}VCH9=2DKT`>*H>}#U~4+m7a|#gMcPZ1"
    "bp+kTsH$cajZ=$Lnn)f+;E?M$}I~Tm-&<B(ce0#=3@lbY;4@dn9NVaz8y2Ez$hWJ;h{*X7=2yF-4ftca69OoWf)v"
    "*A*cSa>3F4SpyO^Ac2_(5l3Yp<+WK54T1gvT#7>b?MLtmUN_n5G>UVlGLas}gtKay4ezAY#xBfqEif1tni>8OUVL"
    "ffi48+Mf{$WAtcbJdbTzKZ8c@7{!{WgbG^SKetwuq9{oCrEnIRX>MpX6UvJgPYG^l|9JPJZ?<sVFq|YQ-C3(LQ=k"
    "jT6xJ@zZ4x;YkHivsa-MxA7t`FtHr6)1$Ysv}4Wk3~!(uOhh5COmSx;&b9=BfuO5Ld?}_pjO;S_eYTC|I-4Gx{B3"
    "&nOZfBt;YCwW*T?c2ZQS1fJtUkHLC?Brsl}U;fB@j3SZ#sZF2h)b|DOrCZkeM%BXmc8DVG`!oZSP=A_KVo0(^0F;"
    "=LlakV2kwxE;{IhpfGbDqlPbd9(d62z36iM9#PW!^xvA-ntE}zC~)Of%?`pag^jep<IS^3Y7l?azric_}>{qULwU"
    "DX0Y`iKL%PlJaY#oiqZi<kD+)PPhMK^=LmP`z!)dgnz3xwrt|6|hS<=8&_z~&f3m)XgMk?fNQ}jEy=fUQMnc@ssU"
    "?kc)``_E&UZU>RPLS$kXpa{Gy<b~T+Qo@h@w^h_|?jljJV@AN*eKe_b(k#@@w^W#OT7`Oo%Qx38*#z_G)idlA*I+"
    "@x_%f@mS;Y8cJz>3pY<SDztXQXX4L&LPK)W2eO)P)*MgsXR668LEl(~<hlu0aS>MQTPVIavWh?p;cLW-vVO2VxY("
    "0Vse4wrc89G8$20uTHz!EPV3z_GdJX1bhx!|eDIZ`hDk+>)8DWI;H|~~mbj*1i%^?BAhAuMbuH|0;LM9e?EZ(w=9"
    "NpXX{4TES-}W#R*kP}<jfAig;p`hGC1^<?J-Bry;1HPy%~aNJR4-ud){|VVhjH~A{qw`rnb>(oVfgrUy*l5RG}h}"
    "YYy;uRYRzHX+)T4H!~Bivlxd#bEH7hPJ)*1&aBoYirrOlxM4KZsJ#9T5fD?igQfVPuL~2urEQAjE*on8vvY_=J^c"
    "&;N9L1a8%)+>aMMyup5SU<lca6GcVVT`kvs#;loE*Nh>3>WQE^JF6KhicRM9%Dv4Cl#Q?KGwx_dDW`$7ynhC~`;#"
    "M5C(~#Vc#cpkfQ><hm&1I!-fQx_Hg>y^)LE!xrbmPlE?`$Gd&kO)AA){Kv`RvAbj*JZujq$Kqj_%qR1qjIO7JH6K"
    "!+LtbGnc{?w+Z6Y1VUHl}nFmaAAR}En|MlmS@Hx@L+S%_ZDjZb);oSPmp#ZkR5!g=;sm;_3G2d1zMyrMF&1YN%|Q"
    "^*e4qlGJjnh6VJo-FVZ0~e4bY0tP+?y_a<;C~u=N?9>2F?Exdi=8JhyHC<NCm6~5%P@?yU)S;4UDSq$y9Nubmhu?"
    "A54_skVxTxg#q7SNkQ`_yR6w7Ufln-2$ze?;TC#{(PK42%rHT(p0wn81ccQk(ZWGikB|GCpz1aByB&j7|)z^LtVR"
    "uFu<dN|Tm>$o5poB!AR&s5d1$C+8UElVpuL*b5|2)hyxZnag_aCsG{9|Q>8xd8bjwLdzDk}L4X?v+Ppw7y6!Fozk"
    ")Nt{Sr@F<K3Mh@2lFK>}Xi<6xm!B&IrUXEsjG%$CTzWCkE=k0>OGG1<=1nw0KbuO6;UK!7V{qhnwVDU_;IdD(lVh"
    "O{stHz7Ut7MDZv{`T=$unawt?{GYUjb?s^NsU-Lp5x$3#>kv)B5V9?+W)<+A$*AuPmdC>0@~)UK^rQ~G!gPy^LMY"
    "^0Ux=-S+z)+eDNb_3n^z>h7UBiSbU&(HP(vJp;pUu)e+u1dIK(@7+2AMQ3F7g&0&hn$CQ`N0P2u&x`I8^{}1+E?i"
    "vPd?<~12#yQ=)=DU?yf^p^<M+Ot7Cb}%fa5Y9|3>7HQpto(Qe3vXby73FdfvT2YaologBF%jYc6p)B1!C>#0XiK?"
    "a%~K^1I4ZMTVZ$-ok&7fdMnLNdib@(Tj>MDxd2Ai@>*p^UK>4=9h9l%z(8DIWz-LI=s4oNK>>Z%!R@+Cta_=hWm_"
    "IXOLryW^APjkDCxR$p9A2QxZ9(SLpnv;}2a_z>JA^Eh+@QZ|7HsV=C7bh5<Cv7w%Ga+ba=sM^%Efv>t^A`NeBD3N"
    "JSWGpe_%K151n;>CBiQJ9n<TB6lD$kNx&nYG*jn`{k6C-NW>k<R!eT<}HVr+W_F{E@{TY&4F^cDA%Ea_n7m+*q}5"
    "fHG_VA;(;K@x(lawXwn=-V7uWnJYYy+@l-!UC-4#1ee2F25-7P!5C!vu{X_a5xn==B9L#;-LNV=u@7(UYEP2;o3B"
    "0sy{EqHWB+08RHfXK;x%6{m=V)Po5l(cwB&JTJ$e@*QF2W0?KlPo6k0bh=F;-wUJNM!;Z6~ZK=&`3Y|^4_l#hDy<"
    "nUlF1N_WAms!EZTVPM@v<evQyt=CGnYxbmuQ6$KC(Ss!<LllU-Gp!{}BQoQ$pOXA7yw!3AlmEgW+F)Pu?UHqk}|6"
    "5ZFC2WT;!gwLjy50gUP|Gp@@MV^MW9ndw;g$rqlVSqx8>N!I%c2rlI!^eIlhySmw=?lw7Uym`wv>)BwY>y*V|=^5"
    "MSaCoybtU9;M&DcCl?Y(TueX-iqIrC+6ii#_nYB9c`--Tz>|9mq&_XYYs2Nb7m&Nd{UZH1?^1(ps5SWb@L932G`Q"
    "wTnY4Oiht%z=hG$OaX<JvwOxLp87CRBVX$MxYcp;cfPi8ga;A58XjhCu<08#PE+vog0-JM+P_e%R^;}2k*H4Qky%"
    "i)UormI%p5-P-824zE-+Z3c%Hl>hR7OCPuYWejf-+2*Xb!_>M)YSyXDfPjymFUD%@sv-aUJ!q1X2kwo5SghLClUo"
    "zy2@s5bB2xCzc{DCAHTorkV*VuJ-S46}{QG1bA+QK!+5qKdEnora{BO!l2G>yRzX6l;aB5il3HERHVH(Rq)&AhEW"
    "XGb?C6!dMHR5L*X_NA4f!F#zm6XO$cK<*DvTM`78Uqc{WRD*bkDvW(6psU#6mNN+nJ!vS;oOz~j0m{9posGqNxzs"
    "OrAut61KQTZB*5P|QAm)h!w)}uN3k+GY>N9yk1TvP5hc6dTLvbuEFA8#XGc+p8qZ<AXV)DvPsf+bIku)d};uMQ_a"
    "REk$IU9kD;MBfXE^f}c-d0a}rY#k&goYc$lc+%=oTMlGW%@y^MtW04*5wwtBI~jtS)|s6jsecDv8p9a1VhLfP#Y6"
    "S(M1zE*&=9|YRwU89}*`x*f6_WQO+7rKK|`KT9?XJxK&^?Ea^?=uKhO`Kb)K$Ui=b*Qt_c7%gfvfR(@?uo&*_hVx"
    "(;@Vgbd=u~<ggnqb;=(qe$x#_2jOV`TQbforOI{${sC{u`iP1gKE_&tL$#0+b>n$^^#l4Ui>&2_D9BRwTDcc6XIU"
    "v)LL@-;jbMs?Z)=73-M1ZV7z>xk6P8nkZlPVYLkYB9aXDQw|~27+{6K>zw_;*cw1ug%%{{@PT78O64pJ{vz%mTox"
    "F7WV#si^!(&!_{}iURXM<RD7;X_R5NOUgr5XnczSkndU8HJ7m><SDPj_SgTIK=$Lc=Mz%P3UdhNMLDx(tJozKK9D"
    "(}T-=zy%)KrNywUjl@lCIf|zS#yeatWxl)4!`3!18j>DgP={|oX?GlqD%nbBFHI<(|MP~4+N5*#1ADDfss8el5Cc"
    "&qEtjPSo0W&ew<hL7z&<=iy!tch>7tbdJBQ$75H$(dNmaL;(omZJpOeC-@_8QA+K*(<_|XktSd0p(<hvW8=8U}L<"
    "oegL#SC&#Iq`W3;=SUbSKuPD027q@hXe5M`{sNNZ?pB^SFF*A^tgF#;<qrSm1(Q!TL6qHLoXZE_D5T|EDQ+t-3Gr"
    "^&N)sUuAc3wgzMBjT?E5_1%bN4BH?nfxfV;Ac<x$p!!aJ#!eb>BN_ISJmJv2n-gPSvx}VD3DV$(i3~t2Mk$W?04y"
    "Znz#z?2BKqDwf}@(YwmIl8j3IxaMjO-hDaQXkDX+3+K3}KtP<)%iF$r=)l=sk7V$3P4c%?Wdqe}D?;`sTjNLEaxg"
    "Bv8c%G8fH(Q1`GhP*#+Xv0JWAWz96c#c25pf&h{RvaYWC0QS4@<Z|^C{ZD*03<|~KgHyUE@=w#3D&yKs1K($<c`%"
    "p8QuzODrET-$S7two<b07(nA#EZKB^PV}jNLGM{j(@cR&!LrBZPpO%1paPpb6c(E>{v@Ih+mEBh>_MB2m&+@eCEo"
    "O`5^X95<cnmuw%j?|<4mp^i^B><(iv5po1{c$PS_R~{W85=2?jcmKGr{3MAx!%iXFE`t4CrWZ=CPjt1}jsp<=s+Y"
    "EDdS+;Pha@vy9S3UMxXT$TV%OIwz8n1a1Y<?{_e@oOWPn9z$^mG0l%6D&L}l9x1x%p=8$;^E{^5Ucj%cazekNRzk"
    "qJSS7Q!ByE0t0}4|PfR$)Woh5TPW|P@HJJ;y!cmRaXe}H8VvzAcl5c|46(uM#%fQ1Q*M&pLVm7#Q)bq(A+WBi9n8"
    "7`94*0jld&P%Zt`C^UWLjjsSq8vh<LvOBVnWPxI2gfx#-eAZw8Y1jl?Kue2Gul}<IGn|UVompWExNtgq_#S`iXOo"
    "^?qpmTBLbp0L=Y*Axl6LU$<@xfS`5Cv+UeU#gjmCWoSz)Ojv+b^)lIP5#g5+DHlPb<MD@hNC{dOMykacgW3^BIF|"
    "Mr)h=c;wJV)r?L#fQ)#>jyp7l}r@c*Ycbm;7dJMM@aoJS}vnVQ-}9)kruzKaBChVq~u52vT5b7cDL5q=Z8qt_D3-"
    "6?g@!{xc^*zE-?f_5Gnx{F}I46-vE$xX;sAWNQGl^-T`c%;=x;a3#7s*4<3Z&;$dEND4e-Mt+Fi#rBkNPo$i?iwi"
    "@1c{U4Qh#V0NobD4ur<4y*)WA5w8cK8P6?tBfe0Oq2@&a6bmQn@DBKSaGAHBW2xErclss@sPuUUEGFMDPnQH7BZK"
    "gRKjNLS-X{39yJ_Tj*!&EpcBfFYWHCN)WSk`3;Wwmgnd&|-#Fber=STh|*>msCVcQhLJiR95;tP;}@vEDa*86HR("
    "NzjI)W&FQ9NVsh!eLfu}%2r|?|Y;EYU2iKMj+;c+Jy3$j^Y9?7wLX4rd3!C02at2@y8{Jg~c=52xOT44=AK%!XWS"
    "HY<RweJi3dFO_W{+i5R&g<y<tj^omkeGl5E(`(a=e5BIClf_G7w*=JV+KDmL@1yTwQ9cGcY(yKeFVs$15;-gv6}K"
    "%d);M%m!k<qOp3*{J~grMlX#40`MZB|NaSY4G;n#9nLPK5vl$>3h()%1%?W9z%fn;^u*!G>GW*>;^fTq`NIJnVvw"
    "3M$bo4ox`5jrT$|8F6wNAX7)$7(cpcBu2rYw2C6;lNl`QGdc0()ItPgK17e5@H^Nkr)R4^qbRUnF}x~B_GM&<BQa"
    "u1i;do<^jpl;p9W_^own!-5;i8Wx)MO!wi8);Nl;vtUT4owRXrNV?HqQkdIHlH{PUJZb;I@OJ>SLR?NH|UqxT0wJ"
    "7UvME<ztVi62iLo(y_JE0)nE3E6E>Nvb@qwyo@GO6_#mZI>W9X8Vw<x;8jBa=YG<f!1y?)x1>D8)PviYC$mJ@U#o"
    "#2cpBm)rN<K+iBHsOWtRYn=;H2x-0XKEubH`JgUSY2aYoG$5Hit20f5S_z`0nuR{9=qsHJe`0DxKwq-6jJCM)?Ys"
    "7~QzOy^V`OSw%}o#~<o-LYHTCQrWVME#$R{rv(NLFcwa^iVE0PzQVM@oZ4%W*FNLnIkI|^x~m^{j&#Q)(|oXNB5$"
    "-Clqn=5N2PEql@L`@fst<i;NtLa(=m*$V}pX)EIU+Q2-`3cWseW{ae>oe*`J2E{MoEi+eZfZl4GtB+FD~+mIND?)"
    "GCGKZIDoCht+1KfY5|NtD{qZOqw7C&rg2FATG8ZP)+A(zgQJ{zR=(vy^_2a;!k~t(D?r;O#e?|`oB(LQgITt<q2L"
    "IxYjkvY06gHiMRwXax~cB9|+HhhYy03LvP@ZAq@f?T9b)B7p|=?%SyomMt@$8u4SYMCKRZ&DYs1i097}|CtIVmxY"
    "{9e8;{RD+~wq}QHMeIuvYAVg4F1eCW+*?PU<aj#bK?O^^+<cGq#I<s754FQ&s$WN|?<1aN1`1uhCeXAAL6(?SUm8"
    "%-I2*8f4}ci)fih9}5H+>l2*7>HaWr4WL66uhVUy2Xb(Ywo4bb%z_z<_wJjYYAf{rcID|KsX5{Q0X3(a50?W1T-d"
    "2Y!&6tz;w&nXoc;RX;1{LzyXYV&3L_(zBtzTix?wy|VYIV5QfXKKBHIy(N-!+X`7mQ!b#a?i1=y6bs9G0MI!L4JZ"
    "Vll_*&<4+`^7rVz`iGrfIAocXy7zL7ycu;V<TAX<tqZjqVzC{!$YY%t2n|K_vgEN7zo}EmsMzdtSVlvz##3QXMGI"
    "7tU&+N=6KqGs<j1fmV@y8vGK2J><9As^S4QwQV?zYTlI0!vpir}@C{uQ{#^}hkMad18X#pH9z=>U4Aw6?dibOQs!"
    "rqcC!}|*?jK8}spBAY8L=ckSNBC+-sg}o4JKJeJxVf3xt%GTZONQV|6=kA>Ymm=*Tkf&Qn`?A)&Hbblp@x3YMBnl"
    "x0O_i$)_dE@O^A5!E;MM2p3Vyltbx5`$X)MAi>S5V6qf$-3+)%q{oM|SIJvlDdgkZ7}l_iSIiFfAtXW_Q!p!5s#d"
    ";=;l4r!iFy1kPV*I8KSZy0wevUl<7EJGn_maw<(H#=0C8aF@bw;k{be9t{^`qp-zfi;QRoZlK9Pz!HDM>JLN%l9Z"
    "~xkQJ5=3w>XJ)E1D?0m_PJe~{N?k0;8q+jSJh+4cv)0$5#JROqX3#xZ%$^i@i10}QHS}vRhj+)n)DM?|0NFcp98V"
    "?@=F@i1NeG`|Mz(yJ|B(xeeZ)t>CaV>#&+K4Ko1BC1lsqzx6-pb`o1Dx+25msP~ul+;7u%}N67NM%kYLQF`$|A54"
    "joDrBMb7LL3SomhrmCOFP%)YUctpJvu<)4H3lgRt1HS3At_2CsV&-((X+%*rwWLBD+Awwnb8ul_-<nXkUsXV`m(|"
    "uU5rc8z#zFR1dj$0Lw)*2Q@&3Y{as{Rgur)Ih?%^c0~e}GzVxUBS^)?DyO)yB&%|C5-0jqQU>zc{byX{?iRa`(>W"
    "=ZwC*qTY8n}f>{x&OMIiqCXSunLX+sCi3qA$nvVuX;m_o+);=kj<{8J$Q1h-A&)xY3s!8N7Uw|-&|)|Z|O!(=73t"
    "scz97#oImD$Ig(#QAmIa+QEGRG_KjE)&sR1mns+KP_9)_8muX90EiIFc+a)-$p1T4b(6?^w5c>rUIkZAuR1Pb;db"
    "}30U4a2CV}y#B(ny;~_~r3x%FS-t_tTjee2}UK>Ci9QE2W0pu3w6L@qIr19v#c9N}e<;zp^0Kp=epB@h$8B+tg$("
    "U3W@h`%~pO|?HSU}aos*Fi=&-bo4GLY#4lj(lU3RJE7<}6lu(Z|heLbCCT;Lk7N2cU|5KhxAzGdcR@69OW^@Az>8"
    "V%r?yhi3AXm_`Ee5V=@@mad}~S8<h4^nMM<jd}}t>hwomaL0SfCdkC`6Y(C69i)BXpPWgMuO55zI9`#$W|>Q9BA("
    "O$LDyuBs;^XNLuXO2A^`#zs4$)kP7s6x#R@2127+vEV_`&J8`<<&%umxP8+D0=u#>P@=##gfDvy1U+^q{m?g=YSb"
    "@7twk%V_RB01!j=t1Z!9MY1rsWsD18LO2sb}&%XoT5<*Vsm@E%=*5xFnJ>yUc{hyN5$i7jJ?c@$KI-l7s+qH@v@#"
    "h4)j%W0L(a1$x)hlEgqXvP$0#bwf-L5eR`^R9}Ny9RenvAD)us8K9|b9lU&m}y^?L?X84P(*x~EgP!bOo#WR^hE#"
    "RhhB6cm<4HmQafc=_OMrsbGbwRJ5`u&#L`oCK*m8}~an`a>y>jO3VmeE^{LL0F?y`lzi)pfMmrvGZ^Js8@yAEyQ3"
    "E#l5b?a1EeEo<l#aS&y5O#2b)MqP@eBt>f|ro6whI|;6jk@Xlv$fAve&hIvZ`pQp&w})JuEKdW@s1680EubbnX9o"
    "8=%wYS^rhJX(D3gP&o{)Xo>Y*BtX@|!hhQhYm6#w8Rrol~^IxS1s0-&f<gn6DY_%KcO%c~uI9Du%zV$|io)OCAEF"
    "cp5Eg)gGv9aeF%2xnlnh>I{Qdu@;6B?_8oDd(*(Q;;V;|J!QFC!m(R5PRWhG?M?{lfu6NqN0{}FDAAs-1CwOxxf("
    "w6=9-7XbMN0wb4^uoJOnC+eV$`+5k=kdWe6$Q8qy<C*FsV1bX=0C^pE@jhYw<38&iM@a@S5#~om@?D${r3shMf8r"
    "0uO2{NO>b9m$s2)%Fc?(z4Ul)CR@J?A*^Ni%4ObWzQX9PWnf^-av!Nle*>q~97!4BQ23G_2MwfqLICJm6A&Mx7|C"
    "q#d^3%uQR+Es5x|9(%L)C1TPbns>Lf&NghMbdyvJ70nS2R6ELBb32ku)FrOdmhQ-G)WR%B#^jLlNH(|5gok?$t)@"
    "k<*@;-w1m*KnYi`?T3ECf~(QQm%0+iP<q)g<N?gKaJ`sFB^{p)Hy8bzP~>+0$jO@@EHy1IoA-+z0`f30A7sqa@9y"
    "K{95^3O(0fcG9Ybiw~MT=!erh;BU+oq0j16S`{!rhNYkZxnz1*E~<ts3`yXudAy+HngnYf5wth^yi3SumxCw1z3Q"
    "`b??)@pNOz=-kTuL9nmss?10h>mblf*Q2I{{)C(3&j)t;PkZqJrPagFke`sO1Z$XAK@Hz-rV}l+a&7)OC-P0rq{b"
    "3k_01Crk)AJ;!#*oDnRaGIi7}bOTO)ve8^%QYb=HN?$pjysRuhm&Ew7L4HplzUFZV;Im=4iu}1L6$Qq*BH4Q)_u`"
    "x8am~{?y(iigrf0Wc1m$71ro4Aj0W^A;Qy@y;hR}p|pfLh22sI+DAb{s^D?jW91W#`x{rK26K_8fB{g__Oz)_s)z"
    "NLt<PF;u*T!o_pLSffK!Z$d_T9>$MQg}Ciz8sKW;T$42k>J;x@w0h8;-K%tF<nuQu-88c5Hk2U-w(Ha`pL4TQO1f"
    "bJkQsdNg?WhBZg$hu3{^SHz~4iU|MT_+`P$Y;xps)#a*(=k`EysEW5*$qIc<yh$ZVSylHPhK(=SQQ8a0CUzt;@Sn"
    "&?zfOJ&F<r61WkQud0ur|hG$W^9F2cFoc@duW`}2ph*iVi(F7>9XjqAw1a)2Feo3Q@AwDSZfqaAO3}ziqT0#}!?{"
    "5LnFfL0#@8Ni+I@I0O4kVjk1jATKQ&40vULw!_A>p3#1;<e_v9J?SwOZe%$&6Z8k4er8&3UTu7hnh>`xrvm*o6!z"
    "Q}7Co;$VVK>=YOfbw}(pyeDgd)P_P>pVB`|djFN{C9e`KEUqt&BK1YnfDYEU|F_$-W!Ft>ce{)$u(Fm0?id?O>|("
    "kl`(%D4j2gD#lF!KY@?a~aMVBaXWaM7?$_W}s(V$Dw4q~O^zREz{CnX|;pxbW6D*-{zm5Y9suM!s}42%H@kE>&)d"
    "GEu7mFn1LLn?+?N{q8kR#f0X0)r<!@Ucyxj;z~Yk@p9~GlQFN$-j*s^-_NuKQ>81^Zjq*NBGr?&#QKacbKgG;4NX"
    "<#(V`Fg~eOOuaY!l_1YU|Ca-GHeVaqC8Bq{vu4u2o?>2pw>2tMzL1|x;LUOHYA8bu<7)z8&`B!Jl$~0ZN+bl|Zut"
    "=1U+&CaJ8xk2q0#F(ih*u`fVu2R+<fWIU2SKI>S7y*rLxwqF9&->>m5MBm=cNST!P8<Wj&g`}gjr`i3WMyjP9UhJ"
    "ETkiggSy8~T!RzpfQa^1s0*h15O54Eo)?B!`dv~YVOW*RlM|@O0Q83wOrVg=WcS6pykA`Hyob%X3svu4KaJ^=e#h"
    "?hlcc9;(rB<-muhKWcLv<TSRAy8l~%O&#Y1lJj*B>haF)4%w4ss#lNI6(+@9yAFD5EEn1<0Ro)rUKu5U563*wLES"
    "C3_L*m9?E<=>I)H|Q9_ylp7)Y!%MZ#CYdV2d4-4Md#q-4RpI@l+ADR-*6RJ@HLnLyA4NgGcWHMu23~tUVdJ5#CE0"
    "V{VM$Y>o5A9BC5}+e=>S$iQvXMs(MyH7sk9o@L~bEd_@SsozxsFHcE>Zsm;*-@sVzbPXmE7NKvd~lr7LZB*_pw@?"
    "+UV_eDAq&mLJRok)w)9wRUs8*jVH%w)uc<ge|8W8oQpD^Nu(GLI5)Sw5C**n|ebm1D4!LB4HU2ik_W_`(m}-2|gg"
    "0l-gQ-0<vOQskI#GkO11W8H%Q8|;RUH;);(@b_Voz02Q1_@@!H{QjwL4k1ZNuW7Oyu>sT@E@!Jo7W-%}gKO~4Ra&"
    "{VDIR@49h}N}e1*C*Dc%?%@2%GqQ9eH?R@JOJ8Bt|w8`-Oh^QEHVt{l7j++ACo9>-PH6XUew8IBLHPhZVc*2pP@p"
    "bTXet;+ixEv3v5WIDABALHcxQ-2e-D>M_Iyd<B`bvGhLrU`&<FF{M-uxpT4wIH#|8+gX6RLkQAqc{xzkYibz%;r1"
    "X_p#~<(Ru7#H<^7<SWbAlhWM$WB#Tj1mOnR?HYBWi!uW18sySmyX(eHJL8MqyqN-?|9$8FIP@bXfp^%!J=2q6E7n"
    "F@6W&g(!2Q-<Xgr)ThgmtEZTN#dm!MM#EqP(B0t_&ME)=<9C&H{`q>eY)RTdk`Xup%*8l5z$L2o>h&{=BGOHPo2p"
    "B8w|bw>225O1~g-L_^?P>ri5&EaEMJ<KI=!O_rDufq9vxo_iwkMKr1w-Q;vUP+)5E5n_^Z%q;-Kq_@%R**b1(o?o"
    "sNUtq7=Dy{G1=j!S4P_M*5_1YaPP~-E=Ogx#GPf>dT%}1!j`A5;J5n@1RJQ`5f&&lY6Q?QH>34v0F737CZwDI0JD"
    "QKS|9jihfDe&}g`F5TZ%(qNY9|5rqhxuFn2u+%d@;@oe0Zy#uZ0erNdnP`ETxm*(mOCi|kR>zTgts8#>SopCWgnl"
    "qf=pIzIgm71<O;|^UC+xQWW@C-T{<s^C*i@_bpJy9i#|;MesCoJ{`u_W_~@5FjPkEk+fnJv%i&^<)#$nrP5PE2w9"
    "Bf9qoo<mj$aG`Z8`20(L=xX(;{7$_huLxyrg{0W<6N|@D}r4-xe;^567YcFEEWJhM@stTWQ5Mlkcf~PX5d$9rLTs"
    "i6oq!ZY(uB!K5MSLrN^?CStxEZ8bVi(@Akg(cYXJQXp(sXQn$2sBuFc$nwkd38=jN6-iflz?k(8?Pl`3HtIXHl5}"
    "CcD=UcggL4n@X$<o?dnEXjKzL?#D43}i7ODXawaJ4(cnMuXMAQ)N(crMeq9H-ptz8YrPo_R8IOn?_PYetn?DG&UK"
    "C`OF(2>FJAJG80+vhQED#YWA<&F-2I=m2dR!(P1T4~}pq`}D1(|A7s{20GW@^y)5kla_H45fV|B}z=_H1U!Uk|E8"
    "A<+Aw$0~ww^agH7xQLM05R2rDIZ~4rcm<L!np;`mEGbb{Q#jFwnDY00{uddMEd@Wp(997)dvsBLf!Y-<evs6%zG5"
    "IIeh_i>%T;TeEfiPW=elR-bk*CFxJoEY%M(?D_7~9vVrbrq*5&HTMrco820)|l>vL_jm$azDQsx7mHqN<)Lq#5@l"
    "EsA!(YAGSdNtsy3Z7dD8n&Kzus(;zwl4^E6$rUEqxx$v<7=_M<X5fkZ=&O}OE*P6iE&bMOusM7uM@Q4w;kWw-Kl&"
    "FBf|c!G*aS13C?|}!oL}q%lWHR~`M80y-60*k^>PoHlGEfc*}~P>#lP6*RMhUK`r7k8ph-*+e7W)c+9yPt)nA#~{"
    "bMzK-hx^Xgf+4i$Cud%k!wd-G}qF3P#R}p!|0oX2nfM0G;r(S0RkE%lS9BlrAV?Q3JrxxC~O-Rd`YS9@QTyN@q^("
    "yHxIfjelRYeQu)yHP|MgiplB!$Lt(5h<EUIC%myxX;5}i)n*o*lbseP^zHw*Ykv8XAS89MT&+gFJC7D>kXo=nh;t"
    "qq9-Tdt<QC9POT}i_QLep3IEKd<!VE92)2{n(=N5QB$*uU66I{9Af{lIA1Lv7elE&**YiPGesc$%St&H8_Qmsbfx"
    "t{LCs(G{U5FR9|9CrKf}&R$mYBpcqY0S^OVR52e2-5-$oe+y&Ox9No;)flcS;xB^SBwp@z8`PCfbQ9#=x=bzO>OP"
    "+%`W=?#=y&?svScEeJQbdxg$Ss$XS{BVk*Ot~*rTS0%3<Wpvnt8VP<x6eb1&GgC&g%<%TsH#R=2@bph0!F`@V{bh"
    "$61uKlL>LJ1*eADV>z+eK~sh<zV#HVDD=SanTt8YkAc32~^&c_e`q2dhEP6@H-_|(QT5dq?Y#-ph15>J^2q8-13L"
    "nBIhThAm+qs3-#rl*_^$rou}sLmpBEOL1Pubn47bMEqeh*{MzDa9~;%B%Vz|X>)!dGXgtBBY`QQw6q$shilf;*Qw"
    "^ijMf-15vhi?3?P#q%R}qRELtDW&PtC{?3v*+tDzON}g<26$!RA2vc|wlRQ|nRFw6IOA>C?t^Id|3c8bwKc7uQ!5"
    "L?d<I@3^Jk``3lA^5Ad_HE;L!HER$)KWEkIc}G;U_C-ZS#%4nP<$F%XqqvjNbzp1-_-60=$&5hZlkvL0#hiMjOH$"
    "&cplSU)S%QC+XJw2dxC3o3Rx_4+!x7C!!iuChk?>vr$-_bHu@RZ?flyp(+BLlrjG<8d;PaPXjb38r2ZcgYBi<O{x"
    "sb1y5j}~5ih8o6#G2nqt)tiS-<qHWJT<lfm!9hf0!^PX6aqD*g^<}TwEn{o6qqnn@|5(Mt_mO<6tX+E0yt`*!}CU"
    "9ZUX`&m3}2f70YZqkRyqSP#`DCo%vA|K?4{OOc3x<KK<t6AW&ca*CQH!FtnhK?$L26_Pq2=TXeJS*5Hf+)#>~{j}"
    "izBX6qM3Y;%}41)Hkq-FcKCqrtm4TXR%#c@HzYNNj{BZS-_)#L5U`*hP~p#C(IuMMv>j3uA`H<SP^+{5)iM1ra(D"
    "K!T%kE{V(;hkuk;BYG4QFq-#NsTVKA*I#L9XP@bI=iBM`hsWv#E{W2b@)B<A&R}n4Z29Hq9NW0`Q!ASAJ#fu5Bmp"
    "`^t1#?!isiO8@CCgoHxVoS{_Nz<srdF6A@B8m!dl8>{OC>KYCAT9m+nM#H^9&GD2>Zm+=D1;ur<QaA4@yc;j!rL9"
    "-JJ1cX;;G^!0AA`+9nG__yiV^!0AvV}`$gM=6U#Opnf|VkD-=ulvEMAJhwXc=P`0>DkHO@WtoT<JX7B-|q&yZ;pR"
    "FKKc20%LaG~Z_GsXGgIFJ6<f8{AS)zF${#CNi2dl}=!Tz=AJg0bn_8q%bFgM`dIC&eA4CqfmJfe2U=q3&{bKnPw+"
    "u_NLy|~J4O9fuHepHj6?;=Sk}nj=1XG1%<8;mt^(ZB+4TFU2&)+0Q767hn>qlSge#81-CRvZOM?x7V-eH;2dBoi7"
    "(W8fTy*G~@gLd~63T|F$HJA{TU`77m$(>+*xKj$a8ogv5u#{uU0<WC)$KX&uO_^{u-GBYdZm@gy=J=Qd0y9SM_8a"
    "OrIeR@l1L4Ua??EzWAK%MS3-9^0xxr?%uYUiLLV9dHVkFA~g}_eOr%@W-MrBe4MGV_=-q3OXS<-Eg#Ovw#!S*9Hk"
    "Kx8&B=HtUVe@!!ZI6w|Bgveyb@4#-LKdgu=<vs>*sXw3yoi?Lf7{iks(epNA02UvB=_5ikQN<-8j6HmyR!CO^jFg"
    "|nC!kjIiBt|odilLS|l0pZyDm!XrT0h^eo~^%x1A-tVuB&yN)f2$>Mmx9V7(=ho*A7!V$wd9XTtB5hY<fdn1Yf^C"
    "sxFYLLB;`mL`7XDK{*skZy|6KQ<_71JyGsIcFrNL2F*0C2$v2$rd&5Rz_QwPKyk;sW%2WT=2`!3|<HgBm10vwvjG"
    "gML)qQFU!>zbg5pVU8tBLfIEZ3>Q>gpQpK@T&b|T)K+U~d#%8R_N&UfcSJq%1RWt#bJfI7T|-z7I)-|vy=V|Xv_+"
    "AwLW-@;J|mypuu{+EIY+EOZ2RK79+Azk+B{Fn=&p!kYq6rTaQPB3YDVp^atS!`Y)9;R@<ox}0WgA@Jnvue(v0W&S"
    "LhoUREfI|F$8x!jz^Bs@FaJKhFN;g^6$w@Ul^f9OqvCTa2JO^kh4r(4FfP9^oL2A1A=vA=g}D{x3!)hurfw5{qln"
    "P3b$(@Z%Qx^O53HRJ3s(aQ^Ts!(4!IkWDF-h$$8!U+BX*mpcxItF=TmFaly&icq@q3^Q1yFZ9tJ@Lg)sfC@_nzRm"
    "$YrO__x5z)#pMYnb^aG3LJ7!^VB~CU8><xx6T#7Z>+Lol?rYP%!WSO<Fxk9e_M(i4zD86qlQ)Iq$kDnBMU=LjywH"
    "Vfw-|8ezUnD#pcFM!&%Y1@vW>uL{{j49LNU)%2aopn(hJxbx@6GVUwwk>LiY!>B~5iFmY>9=wB^CRtip*`yEZ&{E"
    "CixAvQskv!AGU)OmRm!XT-hCf<Q&?RFn?X9(ivaV*~JbLWDi{}_q(y*D`MI|%-N%)QG=nBR)M=n4ryH_vk-f?7tu"
    "_axt`zczI<WJ4XyIKT8mHLzR^b3T>&SD1(@oML2J$u|OwJA|}G8GnAJ10DbieBq-*AStYxoQ%s%7_k@jP_P>>pqt"
    "nfJ!V7a`%ss2IM_m=3l%Jd!y0QkU#z#d>W5lI%KYktDSwwFGF5ch4BunS&CTNX<W4`p=wv(G{4}41UH}WI4XvEWS"
    "E9vCq3C&6$>rfh`!(<N^szn&S6((*qop;Z&L&#iK@Ef<;ZQ=+5UGI4UN)@psSIUV__(4ZUcS>%~NgTv3RfK2&wA)"
    "Hr7Y2-=+TQZ_o^8Fm)a|*grm)9yJZdnTkYFHxrUGRs-d4PYw=+^YOqmq>R;%2B10LY~6Fg(2WozePTM?C@2+OZr6"
    "c`GYHxVqjHucCJMXSu6~tjakVoL?<rVPP#QS{SHoQ(&jeyv3z=X}>luF1_AytNP}%8uMu!*_mpjJd{*d)T+CJ5))"
    "A&J-*EBTh2<RVHM{2B-HS^6vDmaAVsy1eo&m-6-QYb&YG83hwL{<gBg-IMpK0E0>qFFO*z2XN3D_=5;ea!WqucrC"
    "}Nv;WWD$&IYeHs?KrNvTb4GzsKT;pWyt3?0QGTm1F_4ngWD+gY1oNHa%xcW-USXWoAkC{>>rGVfSz-}47YJy)zMZ"
    "$TO1zfOceKj_H=ad&9UT+Uym*8*3OqBq0T=GOlc_%JZf>cDTVXh6y;%a9q8I0$kZ-c}%)UGFK@S^Jx-=1rtN}q|A"
    "hKHLmg$G&F=kF;akKP9<IEV#=7%-%q4jm>#b)1p|pMttESBHiGJ7>pX@+scY!MjS*-1h1sSvGt-Kxk!6=_`6~fLv"
    "^EFEGe_i**YB`5{knw)XnS+6UBnC9IJ$naASB@o?VklIxC)?}5Jl-VmuN@Rtr(k6i33Tcyzq^ZLfLOo4748b5$t2"
    "C-*ip5xUz&F_+#pezq?8jH_I1Mv1?>8lKT1>qgH>m;p^C^ugL`qhlMhXDr#8{WH-uGE`A+?avKH+^Oqyvm4V3?ND"
    "MsKPZ@4Ogw(;Ijm#c0xU=a`86HAFi_KHeXjbY~QYvbY60Prs6nMH4eowy3olF0WMHQ$3uyn5iy6%xvN&wfK?P3;{"
    "jAfltA$mRdFC7v$P1*7wO}Gz(FZKYgSzW%Sl|Pa2ArA`3r3C)y_UYCKG1hh^vw!P9N1mfZ4msfChqB0CEe#%yP`@"
    "!94<YioKUyApR{bW(g(%P@i!D5GCqWhUdK;f(Y?R@{#}x<bwm$L+1i^dWAu-*;RIu#bUlLknAx6BE+c5mtdp--mD"
    "}OC&yE9V+W$&2-{PAmF*41J`r6F5QHKSzpmqg7$k3S{L32@Nxfxq$L7Jkulg_##7hN77Vg|xp01Y}qphtoNX+{!o"
    "?`~Du{mG{=1DnARulxREB#VLDRP5jZE*FuO_TDTbzdUp2CUKKcFnw+FNb13<A{3FnyAG?MpM6`WF#D{!#VJ*U=9~"
    "?Wa4};q9h$4HXm4$7HeQz1>@tlCl^16RSLWDhL{>|N>M~JR86lk;{S>uV~q*OI0ixD=fLoApa^1&rODlWC2q)od?"
    "SEVDq|bRRR%MLdEMaYD$`^Ipia!Bjkq<&cu7Ka5;1V9DEY!-2f33a>3Ml0m}r8>77*%6ocMv9-XZ=cOy)NdRqtT`"
    "9HF&f+z($*e>y$6m>yq<v+3#4{x6WI2iOR5GSByan!=39T152#6fcnen*cyuo~d=Ti<{x}?C_`kvtPuI(_e_xosh"
    "Z&4FgmKEiDCRX}}x4J3KqT;GcOz!GdJ#-@1UKzY4@nqNX^cDTcZzK=sC)5Pn~gKLqY~a=i@14W~C@)1|1Vc=0N?I"
    "w5*d`Vc*qVz2KRKxo6+^t(6bhsWQG{bO->3<&P~7l+>-O~vWq(aFVF0R1&avZyi4XS4MxK|v8!qD&!KDT1nAAAa}"
    "U^bBT0mgT0|?Ul1GXF(FJCkW&%Va&<<T8f)9TKYIjM2Q9-24f0-{^8_kYRV3%rsoP5ZVCo|M6;?7c<}hRB}h>AMH"
    "LVrRiY{q5+A^JhwBQdX$hDLUytcDNd+dr3MI%YDj;YQ%Hiat@dBK~_enN?K9Mc)A${Hnwdo^eb|bR8EX*_Tv9iFE"
    "xhf6jB|M-z01%zRG@YT2XoXtsTdGtvlLwzXeQ+yb2op}3;yx6RXJ~}Qp|6_Pt%+<z;yR2f>q}sQ&x<>|EIp1fTWM"
    "_nBz1L+97N)6<HwqCpu}PwixxurY5VkSXe6t}7?oBZr!CWoWtD-^_rU6MQ0r;n>7bKdgAPgBYwU<r5@jOn=z^YVg"
    "5nO{HY1tWZ2f9~oYQ;xx<PmV#6$94zV;8rlkaZ2FHdJ=Vl3h^Pv0SC9U$oamQY5svFv<x@Lm?0ZvBO+LJsG*Vwc$"
    "7#HVzVp&{G#)CDmyG)J^FNKYf76o~~8Td6U&+hSj5j1^;ymwa*p30@4F$6rCZZ(s)W$Yo-b)nC?1>xE>M*IzqNxQ"
    "ngUBK?!|WPMQ@&(?o*o~~_6!i-S2M}=CUr=S_OKtc*w8#ZVVCqaum30eh;#1&|gmgjtJ!>YkaCdz0LqfL($PuAnX"
    "OtC5wC;*QPrHI6h1s6C_PX(!`eerM~XCiVn0K5pXZbvErP~Yb7;>^fKg*%nL90_$&X<>!dlbb3otMUc>8_F9s=mf"
    "3=<&FgG{fsIAmK?|}k3xYJ4h*XXof>Z@z>AX+22?B{$HXwSz)J(MO4o3&yNk0mXuH)zJ}_c&mC`(W1ZCVvO1sUOK"
    "pXVsK|+RU#mx*~%n0wtm?lnjL&435WX~HGyDcH2A0MkT*M`Gkh@z?2<-llS-l%V3-%%3CaG@}&`Ym;7Rykq)Uo*K"
    "}3#W+cRvT@~LyN1+!D7>+vFV-0U^Ex?jM9fTwBH>vjE=G4VOGU=MN&OtfF!KE*prRU=QYoDd9}lo(wIAp5A+)dwD"
    "2&m|MZDChr6dzAf%At!xy6LIbCcPWx!(=rEnnoDxwP<;_QOBAOowiWen!=B0+o10-!V{sJgErB=@F^Cx|@|6;hdt"
    "_^yLD1li_?``q6(bE&*=7sLyXo<*|6R~4mU+{dO?Le?oQsb%6S-sV8F@m8dTy}Xx}0Qpnl$$?r#nJ;7MTHPh=^`Q"
    "?lf%T+`qtt3uw(ng$4I5R~H#A2LsDdqh!ux1m=%?Lbh8k+R#l~7ZbMuFZXQO&{S=;(=P-Y#)7EgRjhgI8xbzC|t<"
    "iTUu>)I3B_Vt>@Wn6L;9+?JFe~{V(ssU}}pSGUoyGIZ<T<cxJlRTNGWW}p3c7z~GA76>Qx{r$o7)@#5jy5&b)F9|"
    "+697R_;LgSfL})PiwrBu04dutv{_T3-fceqU_))o&^OCR%k{8JxDm}dGcgqc9KoCybilp{&m_=25mlux{eWRe22x"
    "&QsG-*k&WfVzDA#8&Al>5=dnf&Owk7?5Cm2$|H3{zCjd#rw#m)hU?lr@|7G0xiknqDsji(v|kO}cd$kD;%svnWB7"
    "kNX&Kz)U+{Qq~Q5<WTXpNm=dKFc;nC@8SmY9Gd#F+*eIrtnMQS1LO+=9gnW*PTW4?7GL0|m-nF>c&r4x+G0gHCKr"
    "y{Hs+5_C8e^I?D_VqKl8$F7(EWFfId6-d00B!0|QW4A`yMF&cKtF{l)k8E{Bvppj2z%gsNW<Tc|@%;J{I)Xt9hQA"
    "@7D89f1^vu(VgoV%~P^(8r)<J!H!-s5_;QzLyA&j+VNr`zX`u5JKt391Eqt&hkONf_&Jv9&Ud=m}_OXrRFy!DYiU"
    "XRGvMAEPe67fEXu^jR4D5oXwltTa)8Fl_9;v`<yMn9k_sI_^C!HFn+c4s(Ih}zWwS+>FpbCd#-_M+~r2+vrmn?-t"
    "qhfs&V&wpKXI1cen#S`Jv1BG~x~Jnp(FpC3*(gFdjBH(6JeM2fk({Y#C>dU9fdn>y|(hR>3d@n%gl<=JlL$O@v^X"
    "<y1rnNa+>CVxiE$^Yu}BGo1rAK#`p}d?;<U{^uPx^}|Kp_`HT;!!mE5B7`B-F=ob$Qn3SPFw%rY7x<IK9fqT6!(1"
    "7q@qiRvQ6_g8ninyI>NZZn2vEcrF$9kP6$CD<vuJsn+^q=|v&zkZrhp7c;h<=&tz&P%$Gln>D?n)I)j~YL+r1OHu"
    "{O{n;td0%Xqv{Uh;B>tTT&QupEM)7$C!~h9O?onIh6TuAE)o)Qr=QzKn(>f7*Q{7ABH#qH&=M-<3yr+lPW*|@l6R"
    "XH458W<p~nEFesUv9t80eMP62M@k%5Whmufz_uy*HiHkiFH$O*j<L{#?zM+`iS!G0v!1z62P)#L0>d*J25}HL95D"
    "HljE}4+~+J+{fe3~b;P|hoi{W;4aROTF)VZ-BA2$8JB_^#nGoFQ2rM({PqRX_(nq2L8Dl9>}>%@C~7Wt0Ku^E_VW"
    ";4+VwIhfV^Rz$`Ss-qR7vbAke4bx+Q#2e6)8%RF9%WhuW0PO;OfH<TZs18xKBc`Rw89rV-K$J-!S)g?5ON@}nsSz"
    "B4oTsoCPmlJGkEdth{=vn`S$OywgZGvZ^mQ=H*F}jKWIvyr{pc2wFExs3e-0cl7^?z1v6mNjV{1kNmMdePSd{GM6"
    "!=8^ciMyoYnq6#Nbn@pBjX-2Gl3-|l<Q@mU<Ma-AQZ{n9Wo0xh`t*Qheg2J^BZn9J72*5C}gU1Qi_8&XK=+k`h^x"
    "f!hcwsT=a@~fPjoKWW7J2RFO`Jb*W-6aq{p@GXA54-X_)KjSNX5=om_n0^IQ`&Xg~Qa_d36zmGt%=cRZX$C-|mhI"
    "?3&&Eh`6QAI0^_M85F{{T9m(CQFDbt;873^E<2Q6+osak~Ib3pRfU5Yb@516z<Ym{&Wb-eWn!*rAdz2Ntv%pOzXz"
    "uY9|Pn;1Vz%?OKlq2K;?EpP3X{DGA?oZt5Sm7@`wXe|gzjQYt7C8iJ?el38qtC3|-_FS$rVD!U;Rd`veBEdd%R3l"
    "`#vQiiTv7w%Qd07wfhxb`s!b)u*MN~8B7Y#P8fT!SVPCn)FWQZ{sNs7fXix3_(7BHptkX8$2i8)3R*#jBnOcm-_1"
    "PE)EW%{rX_L?W@pK+1H;!#=$i#KJrT&E~%>GudSES5PsCO}wf{uCZ@eX*AfxEx)}sBK$gGi8*apX-Vy`cG5+h5*k"
    "AT;Wjwt5aZZ=Pqz;4X?2GyucGD!w1vP;aD7=oKDa7FHX)(B|e2D`T|<wiuS-p;h{o~WDjgSPK0re7Yo>5i1v=?A-"
    "ch;U7f+YP&S2XhuL(0X3VQf8HfB&vC7M&QWR4Ih)x#qDk<}M9FUbN&K7wwi|3$R(Re=>v1^GmB^F}W?}fVMzzguR"
    "hglW9jgKJI8|{^W2;=P6bqsVH3PZlg*NxmJ|MfH^b@Z<X=y-E92WdQuBrdEt4r1=LzIwYhKguW&28+-H5ttXE)?*"
    "RRk`*$psREiZ!UW013!t%+@zf|GSR3-YdML>P3JuE({1v|%mQ|6gdiW(sF8mUqZbu^{_aZN-I3}v<E(fxsfXct_#"
    "zY{|oAu$O%}$c=n1k|>xlL|gl_PJjoE{Hgpogm8h;ZH*5W#6aThmA=Wk4k2KTZyhWvffE5+}!EH7wt*Ckgy3@s;o"
    "!BHSq7u1ybsdAsg_Kct4w0J=uYtQt8oddn8Nu)<sS)xeB$WS_JZ(1FXu7tC=w*~3rC{0~0hAQ%E;3pHT~Z5|HOBE"
    "pDFa(qzi@{pjF8Cemn;gC!iTLG+m+HqKtInTGTZ~B|Ck|1k~8#S)6=Xp$`vM>^^mjuS(Lj*O;N&RR;Io@C!%c=cW"
    "FNu0k&y*E`@a)@;B!D%+p>GCBhABPh;-$kAeV=&5?D%O2jUMol_0th<;mdh*`g;Fj+O{&zrx$vI1QCEjO!n;c(h#"
    "L&E~54z9S;hsf9<sC^-U;3ZjV|(6XpN=%fvoZnxY*%Q?8(%?Hne-h_Dc-FP1=Jy*C=U`@gJBd`Czq%g5W;@g6{D@"
    "xtaE709KnS9Swll#Wv4|M|ny8c$sBE~=aEr78nAiQ6=G0>>Q<#?>sgJVu`fzqQ?t8FiDaBwdUA0T;3TJ>1J$u%zo"
    "tklmi{>cYjP%tf;(>(vO0v;1K!7HJ+;Hi|wHFel6PQjv;{Mw+46V6da$PXk(&MAw6jVUfwGHjP$vKTJvpTC3t-mO"
    "r452SC<6es5n|<`c}k#XtANHxt<|_!FQRTGctKpD|!*SE5M=R5+>X!MN1*xR|qawIyK7rS`jky?V(VR12jtY@9*a"
    "@1Qbh-ASS3C36oL8yZ%|UAcY(rJ<=8T53RNE@1Wez?k;mi5OTe%og;AZn}cf)Xk-ul;HDu7bV2@=}{5f_mV|Lf-u"
    "xjx_&op!K)*Po;j0f=IIbq<R|{HuR*F(d~c&h<f(%^ON>fw)}()car?}azs)gO46`il1`UI#M>}W?Iw6CLYS8$-Z"
    "rg4G7y{$>x`j{8p$_KOY16c2tV<DNEOF#m$Ph|~l8uap@MZ)=1EQxj!BK`Sktb-jM5rAC@GP5yHNalKxo@pnzgxI"
    "P^;cr4RrEAG#Aikr&6(lM%)8kfHRsx&TGlXFV-KQL1lb>Ao)DHVytcw6_)4TPxFFDQ&h|RmlEdFo-=RG}3iP_1{B"
    "_eMp{EN6q9z^s?UZ!Si@P!C-|SutmB(SbXdFYk8rS>K9ONRGll{=fRc4E(u_3`4A80`0+YmmZmM3XG(t`k%)DIr8"
    "#&N+u+?}MdSby7X5l3$=>pnl%*_O>nRF)0<Fq_BFJQP0)I*i!iDRD^}XF-Uid07n<g$VE=76~5ui~*58iZstx7>x"
    "PD#l<O{yo%2Q66_Pg`MQk>7z5HZ@OI8vWdyiEV({5c|ERcIMd0G~a#|Gn`w~F3s(RYBWlOJ<iQiY%YDj!evLW9_W"
    "eoj2qbTbiqHLbREe^gr$CA&X7{~9|MG9of*dvujU8LnIg%}H2?c+QGkG$C)1bYg^0b)75P5_hRJIHBi%o&G%5qSj"
    "Gp~j1tSMd77nc0jQ-BYiT+9_k0<159)cy|xEaVJ+hi@dmn{f$QIWLB9tUD9?AJa5p_-ZII;G|uj-`^g^OqtqwGEA"
    "i_(LgSFUUD1Pg)npWiG=_pB1$LWM26}q)1EGFK?g+bCD+n7cvdPuX|A*XNXv_bjQY&RzVB<q?&R_pg-6&~DC2HS6"
    "ie7+PlB1+HlO*E6Nds51Ff;@>AmIQ+%pAS<<c5H&DJ<lCUCHa|M0_4d+)~TmAmUX%yO#sQHXPSbK-?S!adXIp*pn"
    "~qw^<43u_2<#vhy6)oU88Sg)DiWmlcA(v2*<W)z03_KMhC2(QuDYtHxvg1LpwBTNFWdb?Xv<ww7_z@4%S(01oGd-"
    "w}+a>BmJ8-Jy@MvGVHP=m)j>h1J>)_K7lCu2aNOSHjwG4A`<)&WUy3fi*G=<xc^B<`n|m%>2u+AeRxgv9H!p+w}G"
    "n7A`Y(7x56lhL_}8+qsMei_zfE*Y7`n`Ghw{D&Ftch78RYxEM|2MXeZ?5Z{Q=RzoN$rPKh*W`kK70d(Er;sQKa^w"
    "x<`-{KeM*5qFh@6_F%<|eA{_4a$g4_PYIr^erK4!83)n(?lBBm0Upvl%I@c5AU3jWe41Vgag#^PQ#*dg?wEas~{p"
    "?Y@_?j1MDc;nB44!WEwp<F>=75LMAcqQk-m+p1<jO2Uu*VVnU^SuJS#K8^r-ZsH}MJ0SA8!G&Uxi(rKjjpqwgLi~"
    "J^e;=I7qj<0{M|y0py-m+eaS<{-udz;(1#c6pzqGenc!=?;PFsG0weg3*jgmoaHN1VS;&QSVj=uOh{PIs<1x*Yra"
    "w><+yzz&LcsUw*7s|=Gl6me%1qiB~px_GuixBg5qa=0weTpm43@nl@xXtH}b$S@XmrhRyxKBPrtjISyO=Dm|BBrA"
    "s{+&rAAGIivs~V?N29(z$jclpjQXfyFt`1d#rV5qNZ>&%H<~FpCNlx*Q{&xhO^tTul8=u(JqJh;K$z0Nf!qy}1?0"
    "`*U0c<$4R5P|%5eAh7kJg8Yx2v5Ogn;=1M^aVaCi3KPHHtl1;D3(j`}pDwX`vfsTWyFb4$&5PlZp6Z<foRdb1r|F"
    "w3K=N|Lp`LfWRiJYO_29X^`gm+x4pF69S#KwI$C`vgj>rzK7y%x05yPYLpse-@A3C{Vh0EJ@)~HF3xVYPJ_#SOfX"
    "EatRZFeR4Yz!_eTZN31piW`6@(+&QPux0xy%~>?)!ynm<yFUKR8{Pv@$Jkn%T6eM23|xVd~u9c!toh{5nzYlSCv4"
    "i@qV{GHynlOwd<530sn+rGe{B{9NoV{sc-4-mPILBE7MlyQElj!}T&29pj(C%&C0MUOs|Wcj9y_Aq~IT1PA%P?;&"
    "tUxIbvzKv<~^lbn8pZ3K+@-;wBhhV3f{JejpZ5HiFaR+BpFl1ls15o7QcjEZuLQMaDcz$utV9a`Di;L;sFHA_vz="
    "nlWViL<iMaOTBjsjk{_P2cpy7~F7<g=ug%puZa`u+6GLd`t*VS4Z*cs=*}PIFc8k=<O<sby8$v{we4oSccn?~hN;"
    "rV?I&v_%ag@Yi5OI09gL9Kt_e^!mg5__v_{!NXBVvndQnZNj$h9PQGc5~yU;Vk>CRZyYsG4w6O{%Xy#0iH&h_(d!"
    "SXWZ$DC8BHqVO6s~__RYj&I#ljLW}Rk{PdTX4WEK^7<rw67Q&YfF1imB$f2U&>!Uc*LR|}9nB><160-8Y70uXJQ-"
    "woZyfWz>Sn*o{^NnP)Kzo|Jz^kDNM*q2z(NR{9Kk^-;?#TrYI;@5MPyuhpEb+6?JExBw6?jcHi^w973{kktdU%H*"
    "~yOZ&$2S@`RLb6eeReODhy>E;BZJeDZtC(Zg57Zhui_4fiioW<YxdirA{L2h&x0uKzBNZ{BsjPBLJ7qeN+5%9b)4"
    "D{}RT-6*f;R=@no{T+LC?Ifp!mSCFpdXDDZm;o_paf1q{@xlUAvu9hN@OJsy;d~xh;4{1%#8l;oM{rgH543-afoX"
    "5*T@RfYhPUH7w6qUJT%?z3V5pL+o}B&5ohLJdN+7*`uvdV2|O8S|AR%<R{jZ#ciiLM7S6)W=>D?-hmLy!re~N^th"
    "oCz7Rnbqgox(cSu!H9ufB8QVrNOCE0mg!@46AAs<phk3l>=8arhJ*1@~kT)6MSu$sOnkkOo_c^-a0y>Lzj*m+t0Y"
    "cv+eUyoka!+GSQhc}q^%O+t#Lipuq6gU&vZ$cgF`cA_l>c{WFuqQmdoaNYr+ha8Ni_xD0SpEdBK^Jc}KBI9qRLP4"
    "^{ifK9dS{HB!0n-Jq#{Q-g2dFJ!rQc#Nc69Jqfr~ajge94ahpREIfrHRK|>Y)2DhEC%JVRd3SdUtcC?K5_#cFo<^"
    "Sb<Gj7(WpW17&6%x#(L2C$~vHA6q6%njmI%$`q>%N<;*%VUo6m*J0^NpHb2`tX^Dfl}H&rX6`TQmt%uqNVAFsd?y"
    "mTSwjKTK@S+3nV%hDK}KxxNu?K5(<GHY**yYC1RqQClu*q1R2PvnyEZ>r7#Xpw3|p&=>9iWqB1YK+~cTshtt0C+8"
    "pMkdSUI&lLK#O=LtuZB|T#wADMyw668i+1wy!_*lR&ZLazoupIvRt8w$TZpp%v_q}>}b}h;%pFi4$L7Em+ra`IgQ"
    "F~fi-fM%UwJeG7GPWZ&KLdL#uCOd77@68045RE@&GGM40u|VM`46rzuzqf>%+rxevnkh<gt@Vf4eo||y$x0Nw_6v"
    "|CaWuMs25}P8^NXR6fwXK-$G-k2_xegpzITFAhc(oTL!ruCeO0nL*xBc*G_p<GSZW;FPO#x-I?IOpY7Qfn)Vl1TE"
    "4k9<q@-e`&u8U=RxV=H&U1SO%uT0<o1`e{OrkKYZ?-qCvV!B@4&I|g|+=}T@mpQ-%-nk0=<2@sG1}9^x_Q{8p7(M"
    "D@y*;=_8&@$-?wyvX{%uDC%@nwTUB+HT3NeWjCIv_(M+YSDE5)X!Y7=r*?>0QHZ{42)zM}YCZ`<2DZ6vdy@?X6w;"
    "y!-^P!nOGestU3FVi@`c^kRNJkS?(fv%XKS$?E}tJug;m4-yXvx}r*^O&I7;rGR&p;#Xz!3~##MR!>((>I9`NL+X"
    "J5nQpiP9=uWtlojT-|EY`+d7UdlP~6(nai_2q2(AJc;i;5;YiCqh#(1nvI8!Sob=a~=8i$IU9rGZCM84O!W{eP;p"
    "5=?pAZVj9%`<{T|dZ<HQRU&Hw~GGm9pSZevN-FSv!na1&|=XGz^U+wed`aqKrT24AX?=e+Vwo72lKOu*$(nriaUa"
    "jJ&D2EMu#q`nKud8|fko71Ke|Y}Gn~U)5_0MPh&CepRTCd|OcQ>h=AbE}CVE%~_uixuAvBqE`>Ic%P)i)m;>hRew"
    "HCYupz)dH7G=DVbk)l=bdHPR?ukf<InB_tsq<|K3$pzrMr%k1cur^Y@QIs(OfGpW_-Aow448tQcD~9`=?0Jg6^yY"
    "CnD-vWro`m5%pM_!Hd~_Ji=b=mx?Op8*1~RJzMi!!dCm4F5uBYaK*;EBm^2*1_Wfm`@by`in{?k`qZFrctJ<XSIY"
    "H*RS21HG&1Ns6%2%Qs&7F>ZEv9qBn*qy49feH=awqOK=?#pOHWoj#K(-{)9o7xXvP|&%l68sNTqkM2?{D>^Cu$%("
    "tdzdXVnz=4|CiHy$hrroHR1p6(e)7sZD(d|yFgFB`Ar)62trufjBflBpA1o~31QIeJw;&A3niPhxmBLWjk!WY>Tr"
    "DU2=7r4Xu(Gq1ZBy*uAvzQ?&%qIfpkp9MZu9&t+H3z;T;zl4a+T(facsd?Qg+rM=JP1RnpHG=8{Nf#n*+{oh_V-;"
    "AD5416)yvs1BN)SSzKX;E<*1x<L{QaSszS0X|PCU@k6MxvD(2|_W@2ckf?uwzyw;@2Pcc4A-V6l2(4FH7`}@ONLG"
    "az7gsxb!!L#-8j&!J(iFeGlwgzC4yDOl?O3%LUsF4cZ{(opZ`>~EUyLRh-|}d|7uRjekJhWT{PqDvN!;A59;<s`X"
    "Q++T&5es%=MLp8O@sofOK{}q0(g$=Z2DVL^=NCf><t2iwVOsLxA9$4Rt01oMso>As`szR@(cuQ5m(~k<fo(OLhM!"
    "f5|Z%Ra`+m$k2^}ywyu|}5b6qq)&sU##(<&-uX;WGZvV~E1;HSm>vi_tj$9%gdsQUaELlbA0MU0Xbs7vgY3!79N&"
    "szo0$|8k%2x-on?qdlSX^H1Acs~Q=4vt1%`jfE#rCd<(CY@@Fr>uQ4uD|l<X!1m^7hEV`)%kCm1^w_X)R9Pa=kwQ"
    "QpvqQRAc%(L6R0k7RC0H?IJAJDJBth>PZchxS=ny+{fq*9Gui-T7)3knQVaOAqx@nx0L-NMXOVP%2iYpNp`oXKeF"
    "7%?GHeF#SdFACx9vjP@zqYmgQO-J&%cJ5*UeQn_6BQYQUHcB{PBD{A&Z?iF8BGv+X&tI63CQ%WxbWB7<p{kvt-x3"
    "463LLAJt2TdF)6*qFFZ_-#g{u%NHT^_Samx;3mReF?%;EiD*(oI0ErwNCbpTM9_~kQ#2ZN24mCxRfJ+*<KSV!`U{"
    "20l3IVht0rSe3IQwu6EYdV(_)Le=;7qgJT?_YaA)>$cidQF%Xy6rrGQhp|)4J%F|@_2!>OJ?*_1Ylz<RgE(5snG="
    "Re@u&Izfq2y{wc1@!r5H$_Xh^TlB=SdOI7z9#aY+hUr#VJsS&yl^&Y8OzqG4n(qId2egm>J|(^c=Gb-(W|F!=bvG"
    "^l!}S5PBN%+y$cDRse5I(SbxnBU>+9j*L)Mo*Q-oLav{<4n&+yZ!prNh#p$-A{6p)kIK<jzV3Sg4rvo}je1Y}>Q("
    "!A0;>%wm#aW;a9jw!H@WM9-{^krL07EVZ+uT-$VTKaU!q0rf6g%Wy(u`XBr@6tezL)^d5<=0necB2In*@{k^)^Og"
    "Zu%QL2xC%sPa60VS-HIgAfr+z{-mvTE+yEoB?gfb9K*IzIyZ{S$Ke-S^rH_CQ=?ow+a&ifV~j@ib{d-!Z>Y1Kb2o"
    "KLsE1`SpJE^s{_F>6!@Phu|RpNfbmp7W(o<~K%|EM{kv*nZ&Bp`j5BE{qKI?E04i-PiYQGL*2C9qTZ30wKkR)aO&"
    "U%f%2y*5><$M7WrE44K7Seh>8r05Hv4J~F=TJ!OjjF@UVb6pSw(5+E%ik>`ZK>jE~{jTyvNWy8>nJrc8j=X>;ee8"
    "X#zy70PKQMBANp0lLcklQ=qly^)7s1V?jv7-<+_Nf${M!BHlUDpi}CT>byTl#cF7M5WLN-7ZcxDK>ZDkRPgOi3z^"
    "}kseN@kMvi|c`}^kiGRh)I5(JiS4%xwm#i*G0vPF%xA9#M&8zAs!QRubqD`2f+fBm(^-k3HCc;+~<j7e@xqlHH<d"
    ")z7GkY^1Ck|wQeoHb|smWj`YykS%~kF1dm;hG;i4}PZ!=r{=;jpCchmPi`F=7d9>qTE#}aB}-7jGIkjJI_~Vn4CD"
    "4j4<FL#B3ba!n5*$QFvGi((zJ`N#W<y=Grg$y;8qPY}W*_jTodaA#i(x-uH}`j`_G_DXdPfv2l_GtvztkEoo%Oe6"
    "o4dA7^PkdplOg`{m_zK*!g$gp*z7SzZAvIzK^LOKd))UXL~Vfkp7D8gjgV^TOt*;D!NSD;W9C50&?DlK{B9mGcZ_"
    "U_i&xXn8x2#&))6Z6T4)^<x~b1kr+&lHpa(%`543W`<{^C}S5p5Zx00yNJXslvcSr7tDWjN|w=k@(S`6sP5xsi9B"
    "qW5K1waL$P1nCKX)NFwF~@ezLog9fldRnda+i!1%Q(qWs({Lp)Ks@f)jq&`IF}SH%chL;PylEM~f=q#B~*HidJHj"
    "<0AQtty#-{f=3Dix|wWP{Bi#rUP6}gq{zTdDxP8vrpt7dBLl*r(Bm&Mz$La=2$%r=W)D(KYDV}_obQ=&C>)YAK%;"
    "Si_f@PDJN}Qu{A0>w3F2b*t&pR^xG;g*F~&Vr815og*zsgWsILPk`!SN!+~4g_Y8Rxn6id}vHWYxxLN4mxGGsoU<"
    "^iJ_98Gk5pW*@)dj1Ke4*i?>yi=(aaz2^omevZw&$G`Gh9KpdT761wd~<ONn>kXzL7I$ieIZy#;&fDJ<v$<gk0^M"
    "U!0tVXVd?DGd;%`5Qo)*SIb`}Y7K3u@8a;MX^2TDHog-Y#bEhpVLjw89ij$EIWdAfF3p+cC$4qQB_yWsc-VJ`_GT"
    "WO978&;r=@zIPEbeT%I))AzS48{ivce)7jQsU`%N9<xHgC<KTeN5ZL3Ef!W>!0g(tYh{M{38rS`KD3Eo@BU+iUPU"
    "5pwT<5iD-I(a=k3J*@seM7D>8T1L}t5W~ms|ESVK1|v=;b@@7ruuAB15k$cPpHsPCjEHn9?U(i7pu=~!^_w6iv&q"
    "gl6oNbo~JMXG+JwJqE=V4<|z|#wSgcI7xY&C#MmaABnD08cl(D&zoWd6w@@f-?>!&PK4MMOi^8{RWHz+p@c3{0M~"
    "AP&H|P7`Pwh=db$#Z0gUMu!#%ow>!(>jV_Nd}y^cafi>zbfT<|QUuz~69c!skBStK)147p$Tr8x#Jtp%Z7*Q-C6P"
    "9Ukl-9fgOr=`jxU&-Cm6qNQ10KTrJf>Ey^K<e|;$6~qW*&4$g84mTVL2?)@yU+VQp`5WNbeuhN<>GWtyag1CMMO<"
    "TCsQHB==|Xd@s$lxl>BTSM+4S`2mzs3yJA4JTnXQZEwnKQ!gShkN+G2x!jKjlRPBr<dV0nxKp9v9Q#Jo`1y)96!w"
    "Z9OW(Fo5@KhqgNj!533K?_`V6;mpM6>CahOsKJkS(Fh|xtHzTyLK8*MA)c$b{b9QnsXyf?8v1htVIaLz{Kx$v501"
    "bA&r!!YlJaPknR<{O#`^n`00O!zY7d>UTWNDCdri_AN5ak%K}IBCQ#_DfSvs&aMc})$Rz#^W><YhLCNMfj4fh*_0"
    "SyJq@5h{b#!_AIMj@FKLAA3nl6AQ>wlbr$!-}kA%P-l<nIH74To@6q|{mECU+y<zI%k)qGD8!qh*Y~F}xxrN{n=&"
    "#^f{xaL6Ohr1HgpFM16uqcR@4d!6PKpDY$2CeQEl6%S4s$MX<C61!I@r&}X+&+=@Rq;Z&MupYob1%Gv}5iz<U4PF"
    "Nxok!XHHvcV9j%xb3bCos11L<laj;a7jg92jT)O5r-$Y<C>JqozY^Qu2&)?z8_;mgg~S#;^1jPgGzOz-)vn5cE!!"
    "<W5)I0#&agsY`aBsD9&`7M7XLvcW@B4Z}#M~2D(9Izng@Q)-Dc{z-;cS(_F?A|;-`P=ktdiecuxc~k1_#%|FxaW*"
    "y4U1r>KO|snI6!t#Re<^|049znnAD`h@O(u!p;Ihj693A^2kel->j#Ck8eat9o6VO|mCUG0vz-3PxV!Z0Mo=-SE%"
    "Tn{PsXayHkB8fhlma(_?Ky%fqm$mous|wmnw<loZ1^-a&+`l`0f7rG<<V*L{kCi<l`4F6t?(yZ|{rGzj*NuayWx$"
    ")Q;Vts(*cmv(KMd&Hm|O_~Y~!g>w+N8ctN^aJ2v`<h-aRHn5~Q0d7$mTIseQaIA)l(1H4?_xZY)N8y%E=m`y2*kR"
    "hw-<+Nv9Zt_2L<d!e<^1vpXJo_jL(^;IS*7YRVhwk!jH6<99}@MnU5d8Bj3R-xN6ys=AzbinO#zgwBDJs4is1P^T"
    "ETqyegVMpfjWrlzb9F_if7fp2Q98}K;VG$mUyx`CQUqD#}LfsU!%Oo#zDfv_e<dMX;bO?_f`W+I-D%5U%9gRw~)d"
    "Y&Ey#M5T9+^iiz|6<JaGw{5?GU32)^7J&1=_=c>*R&h{@3evn{j>P+IcLNwaeg5veb0WhWiaB_ZOH&1TN`CSZ?SF"
    "KlR+_R5&+&9bFDx5`Cl;(Fl8~Tet4&#LX+gG;<w2*_Ei#df>w%_6L;l<(p(c%B1%P`!P@=5~t;vxT}g6=5cxwg|_"
    "dilpmeFr$^W+^5*qp3#1!>^zuSkmA_RyRtgyWgI?Ip&U504qdYl_Wfx4%^C7SHJUjJR)(bdrp}A_08?u&n5`}2Pn"
    "S$vQTjzZ~+sC<yj*RmqB!pJ!|Bh)leIfal_T$=?;@7(pv+H6Pw7Tm*Y_-)v|!Kt_l68orf1gC$$<&0S=JApY^VGi"
    "d&4*EMf7-(b7wF2-(o|Gi9y6{OV=6_r;g}hHmks_$j@N4i?cvz}Z^KU0haMb=hk~FqbDz#T@Q!7#qLc0_5k6yqm)"
    "eCjJpGfK+AX-FjJbmhpeSnZEJl5o>-gS#?)3G(DZ3AGyImdQKyX48C`e9KgpK{p~Z+Nc$P*!bzjMJk<0TWNOw(?j"
    "~*QXX0}&+Srz-vWJ1J!vXCY`s)fsZLLUMYrxa-feXf&M81O@L{$tK2WEVRYeD@8Z<BX!*x0gP_S-y*R~B^Ysx3Xb"
    ";lNc;BM&Xfe4s8pY(4h%y5_Ude99B=if-E6sMeZit*XbmjKXvd{fwR<kMNa1k5EYZrZMsv)ZmU;p_7Ezx~bk-G*4"
    "r>zfEFozi4=>+5Bl^Q0qeoo^Lu#<dipvU7jFIhH7Cv(NdYz=?VP@%oxfTGeKRgo8YbOA!k0SWcF4YGsyXebk@EhZ"
    "0OqW)UC!YfpKWSM8l2C&Rk7cmR6H*wLB2oR;^FwGHF_Kii@3dg=@s@GDlcarEXfI=4$*IZUKkK-;*+D@nbqmSaV?"
    "NrZvgeb=EY3nknAwVuyylK0F6h@z<V)nnQK9gT^?p56G<u;=YQK3}Im!4+M-)vYM(|QZsgO=_U!oP2uwsZOD&d5i"
    "g#p^fWC}aG}pJ=d5|}$ugVdytS5>d6Bu9a;lJApq`&7a2BhO<iwPQgVi}S#kWNgFX~*vl!rfGvp%9eDuu-OrbQ!h"
    "j~(zHzl%~kNnd{J6!z}68itK`>jj(kUW>|je(=Ne^_wHF)=2KUPLp)C10(QHuufpLZ!QizWq|cKo`=Oc<G0W9D2>"
    "Zm?6b#sws)7cr%Qe4ZvRJq`_c9}rIv1|@iG2QcE`3IsfoGYo2nM%HY?;DRRT`EOGu#mt+J67*(W+`+Us&`TE!Fl<"
    "p6Fit?qp%EaY5O@v=lDY?;HYW%H~82r1{XXCU*=Z-?7KWhL`~!xOo=1i5Z46pht9D`LEkzn-2SFkJJ?k!uPzT6gW"
    "~9*OAx!v67vme|o{Z`p!657$|h08kis`{!=&8ScpkM}4*Pp`%i_-)OTgWiID$W7}LKvmyNlRHG3@)$8c1wR4jTev"
    "~_}X-x3^N(U`s7<h69EfvxSz_<c>(}{h>rBT5y=##`3+E&v@TXP`LWHY}VCd*|!PrxLAHkywGFIFRj$1MkFp|n&d"
    "yJyq=*T3ur(Yq+Yp!YCZRB<sGdDkUXN+5T#f^Yvfd+);Cwvnuh{*{h$&Jk&YjN~Mqgbw4aNVG>gvg9qvlgTl4X@~"
    "?Rj6i?^K+76${r9`-(N8o$P*!HoUF&9MB_bY;?&|95>Uw;21cu*(?S>cjjt?N~v%|{<`Y?&>)`JFM?bZgf81}88+"
    "l&eBF_U>TIt<6DsBi`w)tce_dl)T{{%VO8WMIYNr`qYy?0D|USB!&%ZQzrzV(m<PRrB8S?<e1X`<H6eF;p)RKMTD"
    "5e7#LoV){X3Wi%_q^Y6s3@h^UpwTJfPWpAUR`lLa<BruT?!&{e4$U;7}e1y&;5*LAOR{YETev?w~6!EDMJl$G8C?"
    "U1po&OD_1p{KX$GCiCc_C#5tY!gHz!e(a72dSEyZt=7C2RXyH4?i@NRN^b4E6Z#c>k|^$FB`TOojNI+R~um(i59&"
    "xBGj?`=g_#Z|Bh>T3kA7zy2HnFeDOUqY}&2myOk!i#&FRo9HfZ)NM4E^<*>$Svop?rmv3}tsCw<V`r6*)N&Z~P^Z"
    "4jEhzu$<n;B)`T6L$p7c=7e6_42yuOVt#H#L1_pz6*AEw)FkoR!Vs3CxCnxFEwz3FlD?cTdH?^%-qEO`CU7rBg%u"
    "KON+Dxt1@q5{BTvQSg~(KNb^W*Tdu-|9>m!8jh^zTx)_`?zXplV;)ts-_DgVy*~3MxKKm#BhP3n~)4YM%I=ld9}E"
    "SlVl?6@VF;2Y<{RZ+L4)sY~jS0iy<`+cD`j4O7{o<aEzRl))93aUY~GJN+c~Die&%ovhYw70d`Q(5A?WoT!1DsLe"
    "9|bR!m2rE?5&wc1>Qos79V3W>-knFwC*&%NOr8BVTy9mk;>3Jh2E_HSFa&eD?iw^uoDXLmhV_6?;V)UfB$a*Zmv-"
    "&l2@FSg^K5=zQ<BG=TunBaR9h?8C2s@S&vGryG2s)`d^wK-N$&Vss6%KS6eF?7;V|9NKGX@Lu<m`M{UyeLP_2mc5"
    "`{#BVQ4y9PebnseJBf(@&DqG{=Kr%jUZGD?ONPl#?bx=wn^dPm!MD<fB%n8%+WEZzD{t+kjok+voz{%@z{TmVsh@"
    "kqs8(bwpq-9D(V2wDn-ZB-Q|421PX6_S&3=!=hQIb>(Kme~>lkYtQ~fArBw<^W?*5nsV_=}?q@|LpMf;qiGO^w0C"
    "r=^HnZh40dT;MIV+P&}Co@WXw~1$NV^#BhCJ)%oaX^!jw~%>=U{J;kOjF??A@u6M9uO7_7|G{qUZk#<-!XSIm(cx"
    "r_kgEf;7j*v#A^g*n#3Qi{KXL&y^X7N>Ax@k?&NvvfBU6G&2ay)PHPn7_sTJ5#~g^=Uc`iX44A@13n^Ds_UIfkYg"
    "XcUxgj71Az^5SBG^EYTy0YeA7TC}byPw^O002{;~w5XBt*gaYkqu}(Yrpyxrx7S84tTiV7SrHAE4A6;gLxX8Hqdh"
    "qe>OW#+Vp;kE(8p4ZjA$dc$FhYkb?>_X*|93FYwD0RF^6}#Sag7~L+#nlZcQ7YCB>=l!>e=}<>1DFe7Tn9c*`VD@"
    "pVtSjmAZyk~lmTo$YtWzaF3bcDx;IpN)<W4v$}NcN+>sVx<mmJ)n55J3naT;ii>hWz;xff-2_0&u7gAr|k5hx~fQ"
    "33(7vo(BCJ=qtU^c5gvcP5zl-r_END*+0<tQTq1f2p;+CJyI6|;Z4edcqo`>S_7bwd$fUmlKM_u^LD}ewlYADZ0D"
    "c0lH86>Wcj7uqX8qbaa&n7WC-ohh9%=ZOSsBQkr+F$iY2Fl{EvjlY%05d5ws>xxpJY?dhwmRdSf|A|Hj=TnSI3D1"
    "YVi)^;$Sq^a7~TV8uo9fHAWowNW2A0yd_Uv=23X#zr8kg%LZ|9<G6eq_Il=BzhMWBG-}19n=ofvrrewv+cKfQ7TT"
    "ur$;e=B!$x0=qwEUsasjvFGD0^Unf?NiLID^+TU{&(fk~##PV)!@#lpl_fQPi1KSO8n^uJy+k&qt@>=76T2p{c?h"
    "5-0R{d@`l*57wG9VTp}=cm6<e%piOc1*u00Ye$>RI>5L(P@ne`ty7z5YL`Gk#FKjPxTRZ@!eMDrIWXB4JSlp3^LI"
    "_PGN$F&vc0xC^Tv(^Y1z;wR{&Vt+HJhuJDXX3m`(6AbbGzd&dB~!$J#D-T^=|EC^Fzk`JgqVIIu}b+v(NYYFLwus"
    "#j_-Lc@($q*3;ncw@KzI73R;;<Z!w=P$4GQ;tZo)U?p)%0$=@PP_&Yjy^$uRf01gQ-=YgIsu7JdKLs`)aaX?8~s*"
    "C<RbwO?XVHR*-zPMKi>+a@Pp~_2mIl#AVeyt76MMjW*nryj^P(-XPCWM#uPwVtVF1_t9fpxh|cFo)@I2uX0Oz#j0"
    "7D?1S?4j{Hdf;>1mzP8v_64H8YY)2I51X>qT)YuK^<4|ol+7s2`!xkd5YTY*TykTV=_VI4;){|xh6UBN5%PTFr-{"
    "?T=!0E%WAE6|xXZy7DKI2Fk&q`W{=T~Pu)3LLQt2+k#kUO4N4ZY!p2<PgrM){XLJWsmUe*LS_Y?HwN;9qp|p5hW%"
    "03#xs$t_qn<OmeH3@wmgwB1=|f#C3e%o$m|7Vx?bhJr}I*IP(ckak#`^B}6QdXYge-C9}9HaLYhhNVxz}vEjx5+#"
    "mz|9ZuAr=c6;|W~DehAWN;X3k$P*Z9c!%>tPwEP5AyMy4&y#<;2?PEq2QIxo3CH%OTgs+T?@eE8O%Y4*&1v(R||p"
    "VocSBZ|O=d8@(pO8Y{H{EwX<5d}rOVL`aVwCC+=>c(yayS=)*N{Ag-vT_ZBQzoug2^Y7MngNiTCR*sNaClmE9yV1"
    ";1;unhJht_!{gp!B7yO=I}oNNEkCO9*{rxdOSwW3l(dsBo5emDo9>7YlsqD}4WHgkd_g&BXONBASwrmLqr#RLqm7"
    "BBB%P!-pXf?&SYf+1kyD=vz@2tUyuRd|$(>Q*0pg5o!EDNd3kT!i`@QbZ-BAiNN6GgtwLFq!9Zl+0>&{URzS{6^7"
    "X-030xw;fO$heViQZ6n#)rE)XT9*JA3;5`8>#TX0|Xq^RpQ)Y0{gP_{3!{Qq2>#aj-E5p){#Aa9MYgYl~A&_m$yI"
    "Gi)v1;;{u!tDJYaj7v4&rGUh*vm)>EnQ^MIRC9R#FfV2`6}w&gTT8e}>^3sy|)33JR6g8XBGKpz&*n2b)V$EC7FU"
    "TACIQ2o8`)*f=H#;(=(hVLsmaf8K|^e_p`9c6vWfdKaH}g6H4f|1Tv{m~EQh-|PL~o!*aqczri`{+;nU=*ansX3="
    "hA5vP+RO0UZ6;ckGav;6Ca-5;MRO9*+N8D5_O!0CNiT5OJ*2bCYP+Sz^HHBBEJusORNsHuV_P^i%bnot2%tl+<kY"
    "?V*xhl4^#E9FGi|D(!6QFR@@U>~V0sa}AW1uTwJIzPk(!d>=Fgm$~A1;!dANvESiG$~+-gGs52W^@2Y0pNWL&-y!"
    "6r^a}U-xoiN?{}Y7?!u?w9@eID-=zM)?Pv0~Y5(&C7ciE-K_3)TXgEmWP+!Ff*(63=X0f#i&{i%^7^3UmH03D!IB"
    "BpPcTM4dLo6(==EW>)Mea=pQJT{MWG@kMb$4fnjL^^vf*%&2^X&Hh&V`vvCEvMUAHc!gF=;#vm*F%n?*#huqS*^E"
    "&2p$U2UAIg5v)v{qPfLiYP^n$l@NE6b`a^#wA%3!5{5l|X^|1H`AdXNS9yUsRW15;cziZGJr{?^=O_NosSo0EqSZ"
    "u;A>bsjZY2nRy!E%eqj#e-(Rms0|EgIvjSDp}6KlKv6jw0kLf{{cwx5JWnP<0vRBEHz(jKxd;*W}+;^_N&^nGRkr"
    "#dGg<8CQ)%Rs2H=%`5<FKNcfyM4W{OWsBMc6DS@SgWw~7NXiUO|veP!_I6lzw9PyMA4^dvYJIAOTcfwScExL3Bi4"
    "vbRAhLOqB{D8IR~%MqP#C8?qY~0y47=8xWKLEnbjh=cMW)nnGY9#nt5@0?H%WGgvVbGNNR25%N~Sm1wCXW0+u}bX"
    "oIbhWaIm_G)R5O=M+@C3G+X;Ok9g<AzK6p(}Y2Eiyy`;Mr9llUKSzuhm`OQa(8r`zOb*jt=+F^<H*xB3Pn<?2>H_"
    "<sVOX>z8}oYBm=u_zi1TB(Q!~mJ!-+S}nqRL(4G*o5V@2UqgSaqWsP*krId}s6oYx)k4;zd$z-6c~Aqh%a+LEtQ>"
    "!_3y}EyI{dl2v(ruy01JN%hHKBp4-1KlzF>d*)3Au<Su*QLa8>0t%WexhL)nv^ykTatnU!3-Lo}_8D#NYOB-*o;S"
    "<0411QakSo<aG}Vv6nyEVmS;9U|!eL4tPZ3F4*;@l=er1ZE-8bvD>vbbU0peU(L)m(dK`D*|y7-3>WVH_vVdqSLc"
    "`5(vJ4wMx6)_XB2{3sYYYXB^D#)CM*Su#nh0g&Il#S)uvqYL$e!fV%B3#M_gz!@rAp5?(?0(|lD#qPSZmae70W!K"
    "=epCjuP7g{yxrsSMzRAMbSAvNL_2&fS#H09~naH+2fbl}{$82Pelzzl;ACS5X<3W!}jOSnDT~<C9k>M@J{W!2;ds"
    "dLKB(+&_9i)^9SSXes_+NxA4*LAkAzq=J3uI_Z#E(Vx%oA^j%q_KnG~T$yM_-<ZQezr(4qF#a^N;+L(+t+4E$O%B"
    "gaN3T1wm3~o9U@ydq73Rev{$~WIk>`_dfB4P|x%UWDQ=j0A-<1&y90kEa5I~s-{%B?tXa-Cet-3>MNkm0gtNFwgD"
    ")<fq*sx63yo~O$bcXAQqH@%jc`;+<VYv|Pq#JWHan>c8E@ZuOB$~5^CEhFN_u%u4J@+w8Vl3=o*Y}2E!n25vu3e*"
    "sEAC8%(E!#S2ZK}R0S89V0yjA;$}Tu!pUi5k4UztX!ksNBs13Q&-AFyMvW+ZpZ$!!3<-ugwL^6Ye;#Wi2vlhogoC"
    "N+DX|M5OK`A9KXwF3_(&$zwSJH#jwUbkE`1<(dbmS^-M63?&shn`cy$_@@!Z~GiH=ti2NfAi1WS>&haM=JL9r>QT"
    "r!Tpu$y_U52yXtNUJJ<o2*FFb5&ek_9*BOwuM{P=7p3GT77#&D$ehQkRXhtlwvaNzQ@PH`l-Y*XZdFx&2om^lw4a"
    "7)YFq_UuhDokq-)gaGAd!xnKUzkD!VO=0&V70TC*oXQHcybVMFo)G?8Z)U001Vlxi6gVdd6YqR=t3235<cQxH@JX"
    "_#d(v5OahQ5g`cWL^Z8DHOmx3owYPG$OQ$%6303@i<S(sifMwl{t}FosSF@6SYVYcnmoxI&2kTamRMUill?WZ7?Z"
    ">L@X<EIkafr`#_el&x3H^1vrZqOEiRC<!mP_R<W;Ub<<|0`DaJMPRXSycPA@d8Dun7#53kd4Gm-U?0Y5{cVQ+sW8"
    "0cSH5(yp2-Leq3i;!QfF@F5z*;|HI>S+;MIROJxhNwtw8rSz;O#^27?oAd+MYdq{kSMrmv9{6k)pl_1*N%aG?`Dp"
    "pJCUM=Eo^{vgmZzXy<wavzWqtAz~7Y>Z(H~Ltx(?WPkn|E4DJ<F)?5i#s({ioL)fyNfFN|PXi50oNhVGOjOOURRu"
    "E<3aB_MtF0TU`YG%bLb|1Tx6tZsPNm4FH+>u9+smC_=~Q;F3h_3|0p%{vQiZindlxI1T)V;Mp4ke6pma~ysuEReG"
    "K&<CA=$7qp+xC^q20RrrQL@}vL@?K72?vg1<_)bd(Mo_K(5u*$Wm7t53o4$>_9G!`#RNz@9RB|&7CcbMij2jKb~;"
    "OG6)@ZHY7Y>FsQV&CDB=>wLR(C_s_wMWHf|UrOD2BKTN*=%k$>t9;Ya$<;WQJTKgpdvJVudsug9^{qM^ap{@u1py"
    "iGu*K<^|GAv!DT`gC6irlDtBtd`k+ITl{I-_uRk|I)ZZK#sxfm*10v<`ovO+`I=!E`yVduyVBD;$-x+LmAGto;IU"
    "h4BG4g5l*V&W5P1?ML$j_%P`Vk{~qwwV@Ghw@>oy_TJ=V(;SRxkJ5rni&)Ca>li|b?lw{V;#oj#G=Wh1ES(ao>fq"
    "#fWTV>=qMa<WtZeQQMYSV=?&KZ!lddbkY24{dH`wWVKF^~$JQK$!=i>O?(UBiYGeD1(i68l$#s1pqA$<ygrQ#YsV"
    "e{Yt2|-0P>+p=2E4E>^e)eI68C((;TujinKs8574vlAi?gYCP`lR%u!~*~zGx&b@S=~$E3<G3bq^*8g{=RrWc((K"
    "15B|5ozLrx~k0)2Ky1^Auf*SO|yT3RBUlw;m+L~T5r78}^`zNx=0H3>PDkrX9G)suvTbPS+!Ht6fO1?}_d@cU-?B"
    "rO?^Kb$B6X=7uD@N%&gY9Oil(C{O4pbRbJmZkshel6G)}3X2Yx_5>1XbKKRr$2IE1+1NC-Fi{-0{}$*$SiOFlk3D"
    "!W2wL(2wFeTlU2}0FlO8gc!Sx(b`mfD=x1WQ5jGB9v{gmIfOua49k!Ly>VZ}tsJaXa??>+bcz~%agZUQrb!qtz;="
    "R(C7!R`hJ{$J^67P0L^D+JvsEcV(qr=lo(C{sxG(mpMy)Tlr+_p_T(*(t8(9M1o@ObmY^sC`;afNkJXB~)&tN=G("
    "feXBlw=R90!Ls@pD|&pf+A$C8KNaB-??ZLT*x4jc5GodEqgM2NyymdK-Nv4iGr&Y1~^+9azNplMe}(yHGC|O8C|%"
    "*sJ}JEU4fM_$}Z9cEaj!TkikH_&9gF_W=U-vptI@8C`DktfP*+>iQ|7wB;kLkQFTZsm$85xVrZ3>960qbT|J(iNx"
    "G_}_6tMMIam7f)tQtJ?#K`dIA=^I%d99TkY+cT0C&&b_zlx56eaV%2E&1>!%(#yFB?5_Yqq=hK>+WpH;L;Hp#e54"
    "VmjI~xx_Sz6T;m0*RXOnW!+UTb<9pXPBf$HeEs|Ct}#$!Gi*^MO}0uWI5agQa>P6?$ru3*%TeQCjWAVNno+I}`N4"
    "P=EtVPjAkeZX=l(xHbVPZ1r&&RkPSadal=%S6<qa>v+Rj#`eh0G$theB?B+CFX5}pbqq&%Ns9rGus1#BYaR%9DUY"
    ";O~RisKwOEqNMOeUlLy@Mh#aXoLJ1NXb#$tW=mrh=jrgg=cPp+0~I7kOSA_#3?>q11;5I8hKGR<1QB!xgj6m(2X^"
    "*8)|_-PRLarCd&J++WDd=PFr$z^fN>!d+i~x0&Ij}!U8nHY+0=vS7XAG>AEw8g9LkxNHeJ$VBWC|j(1l*l?0(eE~"
    "I*y7rq+eJhtnI+FfVyd=9uev?X0LXaFdm+n{W4(U`7T7$KXjre%#2b4wkZKoO^76ThKiw{BK4SnFmLbZb41@<XjF"
    "1Fq7WG`mgZi;n3JT|EY(G(QE_jrZ_w42cefEE>9HtKP`eaNA{QY`2}vmqsEvy;RIzjuIMj=}a@^1A>LLO)x>MD*C"
    "cq5O81q?a9M-MmxaoSF><+olIxtSM_vUJJUO^T5@(!TNxJ5Dl<75q<YH11{mBkxry#%ZElWp%<^JLm90VL96)_jG"
    "xW;u$?K5p!dN4z@ABsxy?S&a0?%ndUWS-_PjIThD9Z>mR6Rp+N|!-9yGkMHs4w;qyyFrv2Fz9|K~Eh8H0E8HW+fb"
    "D)cOl34xcaQVLF2qnq>**Rf)rceobL3RSxa@4*q$(_hxkVc5ffcRFg!5GBi(#km4!R4+&v$eS4qn?%GlSxZsVFR9"
    "%0}L8W9Go*|9liLb>erjDYdOffD&S!w8a24{T?H7?LuWaJtdi!1sVXRBhPPz+rRg^Go=EC(XZL0mL}ZBxMf6HKU?"
    "mYV&y{}<GL-0u3~H+bG~xAuf=R3rbvt>wae-kNYN3@Xd8X|%K$O^tp)u<GII8wp~2FgiK}Kt{kEaZG<m&2>6qWgG"
    "I^U^t;d3Pw80k-B&Z>xCf5USPn8T1F|>Er3g8e5!>o_jG$u2@`YaB(o&OTL-6muNVVn@9o>ulfNM`{3Sj-2zj2i5"
    "$aU8^~lvi)QN&(i|PE#^*HUHy_b5m?$+1spzhNG0Mp%?;vKE~@98_QC%bmR-%g<FfUL-)9A-+ym}bRpW8sztKbg;"
    "0hP~-4^NVzrsj496hY7SK38x6FY!~CZukF+$L^{dpN$z`{cowky36!w0D<84NIiNkWRU%4Fpp;p7Pzf#GcLNnGqc"
    "ry?q<dK9-}uzgZOrM=-!bB6tP(|@z#09L87o7b@<q>J!k>AAfXW7rX+y`vPzoWTSvVF8I;KKWAs{C4U8!RY)Iqlr"
    "MMF7xx7?~f$i`5SQ;e)Jiyxtl<JJ!UNV8k}%%-}jbX@3d^TABo=D?L77fMJ=%cb^!&KV>UW1Qz;l8HJ@tgbv5LKl"
    "CMBm|`zE<6>O>EE&&*a2z*4}bu0oJL|6-kDt?@M9M0G@sh^Q~6T$@T71$m`-Ta02jamkDp{S-b597@>u#-lU0ej#"
    "Y|JN8{yse<1LA+fe{`2qwd+(J8B^6)ROz!#(7Jyj&9wyp(T=ml;>js9u5qKOya8;4gt2(Z=Ka9k|QXV%EnYgg?^)"
    "uU(C{~rg|8DPBp`F@GRV&U9Wbg;qmtp)e33Wl2EE|*cnbNz5?4j=w6bHuHm9O|4o|bJ;97SyS0=~mHAg#v~`?{=3"
    "RcMuZ@Pa4fUn95I9<Poi?P0FqcQw(H;xL8)NNN`Fj*M0v(VM(NUm!uCajY^;{5h+Ug2{+dL4Zx{05q?DLz{+cAW5"
    "6sD0V0qJFk$B5|W%@_0<Oe>IvZmFZ}dNmUsuVKcnOQGWspk^aiMG7lz+tj4}i;y#JIZ{Ypo>5(7G4xEBcO~KZfrY"
    "37VKi`?C9}+Uw&kKNAW5c7?s#Uw^v4)uQ2d8L;-p31j_0F3LnoFH)gldM;;Fu4A1&yn8rshY%4tuHdefLq)TFCZw"
    "z+hlt`@5#tn;v7e)<>ZptnD0J#`LRq9Z92JUC&s#o1|p?`#AgKDNNqC1iS_VAOq@|GDv6_3r5CY$Uej=DjUO#|OH"
    "A>gC<=rBhCI_%f(Aq6%}OCOLd*Z*<N&=8BH2Dx&J}?)>D<-udA^RbkPhk4vt|$`L?strfM&pWPtYosNidu)Z{Rby"
    "~EGvr8RHRWu?b(Jbdml#~yrw?Mcme>i#XI;W8<Vwz4L_wa);mHL2FbGC8M7ypJDG$j-KPwUT4_JE8$l4_~fwrR@h"
    "!?ZU~;;ZZO8|lg*$wBc604oD313=&lTu1~4Db*jgj3FM>qVINW1Dn%B?KO{SYg%h(`txl}?U><lWwkPE1vOH8xQ$"
    "!=cAb#cy+^6cGJAA<&?ryMp*;XnfaIQH^q@h~*;37f6R4h{oSZj90x_(AeGqBwI+t%YD`@2VfCsVK-HNK+!J3|3_"
    "AyZ#3t<(j`8@vA8E^GXmn|mlPB6l~EAu3&CB!nd1wpNU7C(wogbaz58jey$V_e@m6*Ymx1kAX^75|tZkAX%UYt|;"
    "DKvA5D>=NBItBIj$3iZKD$v`)P5?A34kbeBt(6Z_ohcm-j=!#LZHRE``fiICW3npop4$(H}T?1bYbtEc(<f0V@l_"
    "8?3&az`=05MMIsF*|PjEppEcv6IS4Fk&F{{HCgxwM*`j{bABf9`rEnmU!O%4xPxxld5PCRr7TL}?|)dCu?k{-OG="
    "=rLIheq}l5<<`j%s_3Fu&$h@ob_tGaFa*vfxI`HzEC=tDy5^+LDZ}a4^r@aYdU9$k9Bou2w7%VjtRT%6aS3rF=!1"
    "sTEq+|}oN8>MW8Ftz+VT~vxU1S5f8S!ad>Qb^>NWO`#V4daa#vY7*NhSft9}6$NB3#$-G>ce6BQ+}BleBM?$G%AX"
    "{{<#QDKC0p-PG!XLvOSk-GhtOHZxYf^`iE51-sy-&Yx2#PfQ4q4m>g2q~)^H8$RI{+s}=$3H2cJ6}2XT~$$fz}B8"
    "0*dUZkw~Rr5y_+KsDOy^`Jyia`-0xL0O^#R02ntkL<^)`AUTg0=tLFj-^%Af^;go1>Q^J+@GE6^AMR-|&y_7;URn"
    "(@GH{>pgbI@F;;U&Q6CmGtp;zEaEim<c}T2N305ZxeBl><1F@D4-zFk_|Yi*p3o%vS|(H%3h~Nhgl(q14*#f)WTk"
    "0BirE!!|qUWbgU_?7Hl9CGe)aj-Z`8JJPCd6^vopW5t+u*hOmMWb>4*k+L!*H*ZM6_@eO6M)%CWvFX6$TGKa`Ljr"
    "E{dTeJ7MOm?;#BVqHlPIrUDz-j~OCQ=xF)r~7l|oO6qXtRm#Oup$3^onw@R<dwTPXz@c})|wxvIYXw(eQSx>xs@E"
    "(b8slB4cn$q@r)huQ}#=0;C;=$~V5L9d~0Y}q^beLDz0hA~2uOu~5?<-;A}E8!_4>C~=kTCx$83_^pp_xFzXM@OT"
    "B?QWB4$@G}k57x?I*W0Z<=uOn1YPbhlVf{Pf`i*f<p8q2=4~pYe<3h~hLf*cN=2;FR_6`zGikL9L%(H~rAXOxa@;"
    "OfLpfwcD(n&cBmnEf}VGyI-&}1Hkh|_tLgUF^7NRTjCEFEi_5D1xpLD3hlXa|^aXI@B0RUToyYbbCl=S|kLQ*H<-"
    "^T>+bIyjluC%(%FAU6tvVsb))^<mG}cdbENDz7@6TH8g%)7_$XYEPIU5KHLaKcw@c8Yl6nMuaavqPIPsR||wowZt"
    "GJrvMqp)N0r#zr{M3C!@hs_|^G}CNr>(aMe9=gYt;{1*evv74>Ua<lM6(y7!ejB@?CZtJ!qbaEpIkKmMG9BR}##t"
    "t)Dz?%axD`O^ay(CxGtav_5$6stvtj2;Mtuvyf+xy36NbKvt^TNqGv#lEXiZcMnk;Gu?)hM$lo^>1tt9$_~^0TLU"
    "8M06{iVE%ZoiX?(3-Y`wN$H=t}NYA{oC90)bdDWu|u5Hcm-&fzpO5wVNmH|w)I$is)5nAzTkti<@`DK)A76G?X^a"
    "f31_q-(ISvOfa@}1@YK-5oUK;Cc%MTv~JZgb|8UujCPYZ(E^l=-Iw@+_isRzn5;Yt5>xMhmMgh0}7o_3?ZB1m@*c"
    "o{~N3SrO7d4J)s2&M-<v0)S_63$>+jYmOBA3aHwW7uWG}O-8q7cb`|`VS%!`O<$<2T)ZC1fx!ms0Np`a8Kisox<X"
    "q6Rbtg4kKT;;cED{OU%uQXns(fWL8p<SK-x!|?Cn=kYUnYzK=q|6sEn;}dX!Dd6*s?8(SQvHWw&~m-9)==sabBKa"
    "&4w|J#uh|)E0!-lAsyJZ#k%mlknRN9-!LZn+AQXzTvenczi3253@;F*Lvf^DJ5~EO;VMelCbOZRg%a8^>;6{$&fr"
    "+2=O3`k(3At`9EgV)&(ydtG2qq1*O&`nJCZ!IcnW9^x}(5)HT_*QX$}QkPU-bY&6z2CSfS>I1_OSvM<Z;bfAg!E5"
    "?inO=cwGPl?v?MR~QAQwh^IR^?tut9z(zy*|%V-oY(Vq1&N}L@%jUnExT0LSSE0>;V=tT}+1p4pa^~?-t!Q$707O"
    "QWr(K0@EDU)2^J$|BbyIRt$(`4r-gcV}NL>oFxUbyM|vC$U@^Ls^3^GXCXtVwGQ>uiwd@)ES*5{%_0BysV^Fu*ky"
    "=G;)GTVzac%G-`Wn;>s<#|!_9f%VZ1l7AucqmOv81AnYgHl2#n{F7X3WCrC7ADhGKVpbdFjdGR2!AP)yka!+l`Vh"
    "?6Q}2$MFI)NECVWk4W<u<MAnzQWq$1o3YxNzgJp_0gi*Wi>EQRD1eRSC}Pr2L`#lKDu=tGaLJ)W~LlS$J%-fpRLf"
    "J8c}RM(>&r0`{u}UGhO(;4X7TJtzU!|sNS3Sio+Rpe;kM;3iC9QMMPo5P@-2ByARZHjPS|wXpxnX2UPED|F5Grdt"
    "A^9F72O=fQ8TZemNR>6qSyQMS(>+dObQ7Z%+^3?4ABDejWWT_WwHC|Fsi?Y~Ae!0;6Tc`RMQG3LjO5k&red+feAK"
    "2cuVe?~cyl(BFMAPW|$L`vRF`_ysd(OaOLq-nouGbqH_eGRZDGyU)AbE;Lv(Iy8jnp<$1WaRnmF<EuEeha%n`AO6"
    "?7k-}{C4;1kfom<i*YBwjxE<LK$fIet8P%9v-1U9IWYQ*ViPj*9s(ZVI8AMCZK*8qV%jgq=vp}%ii#~8&+FqG9jy"
    "&Y&Js^*cm@}QO)Gjn)+F#5YQGZRw4PL7@H9maBzqidL8U4v0ha}oXFWnnO59v<(Xj^2!p&jaZ^bjENxdNn#79q*6"
    "M+%Clmd$VEU0<nmS0+3IwW-UUvBlt&lSv0b!p9}pAD2pwZVE;@eglJS$8I0Gn``phu%rOP@<=HB7IV(yb7NB8;?@"
    "G>W#dR$hu912s{%W%bbLPKkZDaXehul<d!d>o!`0i_?W?^!ngnH^(qa{I9Svz{r8d20*M83kdRCd$Cp$BPRPg(}9"
    "?=;Yai&{9BWjz=lS-ccmOO+jd+nCQvxrOy)Bba(=;<N~6l%d*$M63lit=@;r8Fc`1h{e%nE(r<us%EA0U1NPW?^K"
    "k@6bQpZ#hZz3c{aBqwp=&vX3}QL8<TI1G%k1L@7YLQF}!qDk*%uh7;eADF&MtXwR%pS(nYdy!X>ObmaMe(lli=es"
    "?!Q>Yh6!jdy{87>lMCP7$<jnv-IvQv+%BtP^_aB>ldrai)bPy6}EsVq82Sebjt!b#sElcY~7R>QV!0-yKbw=Ng^n"
    "tA}Q4{MM^_6w@E`)b69)t=zMfqCrb7X4#fV+(YrUt94T14e=5Ys?b<d``!!nJkbbS(bwUK~K|i29<;Q%4zRB}VV^"
    "fk7P7hzhGtR6`WGL1|m2MiRzl>f1_yrpVPF{)iFkU>N*2crAVCgTT*N4Y~EqteYhi9YC-Y+Mo=YiN}yO{(&F)K)I"
    "cV9pPX^k-0HH1MsVoAK(I#sNRR5*BUKod$-=p?^U(fS*SfIXG3`bki?Wq^wVj+O-E@E~2=PZwhompHl|0{}8at7n"
    "6r-0}#>vTwcK{m2KsRw|WE+zBa7k_{ZK)SZbAKPELU9^$Y;;W8|SJdJXNRwmQ0W6^p;Ez58b`7~8&Rg<cZ!43)^u"
    "SVNa_YHkZH5Zn?O~JQ*pKZK;5&F7jJ^>87{Z?@qCxF2+@h*r>Bm#7)NgTla!1<cPH`upzvH^z<7BOziu4P-568_%"
    "CX&K%$_LmGsfz&3r^34M}OrP3JmN7=TDaNex#ai}vj~F2wg{sFBUhQp~m_^|XOI<n#T|=>(p#EK_P#Q`}m?U*tIt"
    "S=AEAj1=Nn81=@PVdr<94t1dP%}SQX;4fJ@Ab&Fh}GtkU7r{e566GRjB_4>cO{b#S0x3EX6EIYGzaKLp$}#S+zmX"
    "L)SOBL5o~6YckCi%OonBOf3yM14m3upfYm|A^#mSxzeLJNXQ5G7=VUyw+oHO4+$DE$ya)n8wPjlv&$q*Cp88EZ;z"
    "B|0Wy~IiNAkf!XfHyvR!?*{_I()&E`9XS_4%0;p^6O`_q6~R_=kv0$luVTTQ!$`|LwD3|YZa^}YR4|9<UKuO2_`X"
    "y7^pKn87%Q#Lf&Z((e>d?whIP+!}@wu&m=?$$BX^YsjsM^OA|Gt;kU-`vP9=d+wa{p{JD-w^Cm%4_Z3YFBONVzDi"
    "1jSd$k)kIp*EC%G8(h#M6JP^@V@351v$<2`cHb9F&Hl+p{$Tqv<v;y0&G7`vh6>R?oEFWP^m#)Z0-|KI88(JTy4K"
    "*l@j0LPb8TfJ&gKe4FwB4vFP;c5A1sZANosGr=F+HQr0vL$ThWAZXUpbHz^H=s>fq;-OpVd=3LS7w@e(P^eO&$^P"
    "_#?9vG%4N1(7SjR=uT?>f@>{#%nnF^7i9;i5!ng&r8@FroVKGj#LgGjOl`wFLj7e2?&Fdl!)Za7jQ)Ojc77(MW?i"
    "8WDO^=FixHZ_?<~SkAQ_wAlzEyoE1Z*QhV~kxfvYgr!v{>*IDK>m`=8`1U?q5<K2uvV-B9fZdakIet+`QcI4(b`8"
    "-59;xDnXnp-jPl%h_u)Vsp*egXYGh(DSQ1=yW%fomoT)(arjxR7P4v`9%50cp5piGdVr`IxDzD&P<&B*AbLx1@y?"
    "0%74BPD&kisH5FwDq@(DXhnCLF3iW5MD`OUaBykyitADR9mw7gg3jK6(r~fXa#d01e(b_VbfW?=@m$FN5u{5W@x@"
    "K)n&H9R%G8X?j3X}4>ib&`Uokxg~!mipyRn)0Q$nJ%=7|pu8bt^ho$%R!~cAj*-d19|mPu{(SQqnSdtrF_S;lWTf"
    "7OQ8qPMwGBL>V<B+9^UDm9%~O?)aGUHsv;=@;1FWo4#;73CKw0G%BHt{XZp;-k_cps7K|720ZO{NFWlHeHIk_0#E"
    "KBjyDnAs>lH%ZO4iw6+M2?{-y$YQ1xC0oAFN_<5)r7=Je^)l}wOnO1G`)thTE^T8C|MFHb>7hrf=*b_w>aJX{R^w"
    "+}59bO0sWA3jDSW9KrQ0tkSes$+m93{X6w;DA3gn6mLqAIo1Al%ir@kBdohw@Bjjrc(u1dKD+p2wzkPOV}3+szGK"
    "V&=*u}wfPY;GxirZvpDb24+))#Z%wirS>Bfbi$|X%1{aD0_{<`_i3%~xRtPTw)+NwN<|{1jN7*>4Fp|jT8gWW>2L"
    "tUgz!A*~NC`?iMjr#XcrrmvL;N@W82x?!NdEoX>B;fY?}6CKp6~2%KeM8bxLzIIxHs1h^L2QqlDuht8?$$cG+Y+f"
    "nG0uNb2GDoe71@PA@3Lh>h0;?>o<E`;S~J9)9Yw@Q;|cIB$3^CD~0*6wulo{vjUqH^N@f7yKWAj!463K@m78bc%v"
    "}%GLOQA^VzKE&x^Zs+M&CB*tXNG)3x&le+i3dgn!y;Pv+-VDY7>vccfPiuc^^l+k)}B1%(Hijk6FbCd^oaM#?j(I"
    "&WcXAP^IZ%9`nfJ1X4?_`6VV@EQxP7Xdt+ifOjIgF@~=R{%AWQ!BxAevP6f0mwmgo7OhcY!(f8Ie@AHkAObIiNgg"
    "%ozC!knzJ~m9hNho{LCUSv``s`TPP_Ci%x!_FZDiV0bY1i6p>Hy+#aO0<^1?|0pL701(dL49Zks&6>U>yHum@;1o"
    "bga5*fe4c5#XvPwu3?3F9PiKE%62lpDtPiAz8F9Zj5s<mz+*FF>L&>x;6?3q2ec6X3&6cU?vwBLYW4l^vApr7oY("
    "l@Igr)@Qei{jiv<^0?Eze+h1yVV*&T#ww4Aqie*-pCcAL!{!Ad!z5$ihCE*_ZQKG5dPGf@^jA||_4JgtY8kJIJ2f"
    "RDOcpZv0QMalEk=FjE1cGlYL!gn<xaQ#cvQxsT5R-r`HdHX`T-yXxM=5b?iAhqTD;AHB_c)%mRXSt2)E`;vRPb|t"
    "NaoVS0pG<_v<^7RGwk_=YW8dhxy$>3`I$^{H_C`v+<|lcuSo{di<>(%i2=D<R&d*PlhPQI_jaW_(td?&OY&|tMiZ"
    ">#wZW_UB@Z;TFd14RqWT2$TRb7K8huH_mhuytB=ZCo7c0HnmU}*aX`bD0qOK+DM%`-g7<^&+WM4V)+1#$(1A8X{p"
    "Zu&07LhNXm{s;J^JB8Ix+K&JlOy8^duzKKOCxDq<>$#o)Ld7PLi3C=ravds;??hguxwNHUWI}+mNwkxdW#{%uXdS"
    ")@ps4Ef%p=uKA%r1e+mDnB3>(I!})lVSa<C_$^8Y_yEDQwmjsvs09ck@9+hTn}>SNeX4Pdc}+FMF<O)w-lrx7Pc3"
    "iK??BCnI(1(#9-Jqu;<{7w%o?rHd6c`{F}fZwEt<GQ9movTTpe8wRCVs;4w6rG#UL=SE~0@2+)GHoYHe7`&vqf(W"
    "N)|u5G-@%V9i93_#JYoa49SUPO#JK3jsp3HjAa&v6w`jWhLpa0pm}Cx+kwZ!F;SJ%%|6OnNd`Bi!vWbltlQbejj0"
    "6vr;QB=1qN74zai^%4jjel-=mlGE8x=&mn6NH^w-fmV^daTt`VF{#a$8R`s<OT&_S53=>T@E;~l&N7R64*5rgaC>"
    "?o-ScphM$`nR8%3>O#q3_`AsIS2#(z_0wHTwWlfmIed`FQJ__j|qn8}|OW)BADK|E72G6!wXtgu`xm-R+`+gB^%d"
    "(Qzr&ZPq3o`vMzhu{m8BHM~UV-AH-TuySH1iY0311W&|7onD6!Y~$4P?P||*luzbKc!dsZ(d)_S@6kPi+Lsq4)V^"
    "#gN<X5Cj4#WF`ceAP{~B3J@wRmUo0GEs{#_cE7vuDR57@8=9<8Q#+i-Na4eyFxmWmQ8t)bR*g~>#Fi1eC9CG@wK!"
    "RasRGfZVVPT!vq1uw?w`Q0)a7BQSD#wqwc;`B->Q^U_NQTO9?^eLL2feCx~Sx?$MeNABE1rRCAN<nXYHfRX1ryt`"
    "y!$2pnr*O01e3q2DAE&1gn#hM)+Jp1+3JlzQ?JSxOcX!6=IblbgmDv(5{kStu-@OToo8ivRU;Z*qkF(?G_H7=2jF"
    "adpDu!ha6~f^{SVrfIrMi%n(X>3n#Wn=g5{Pp>jl$V)Abw%R7i!$&^!*{Npo?+(TbP#7?3cUYESiU_q|^j8Vjn=R"
    "Fn@LkeO2Pfe1VAZ8pGjCb6512Nm$Oad_kv_Bu-bKtb>ZLga@x5OE@SE{|K5Ov~aO1qFl+PMVN+H2CfDn&A_`FJ&T"
    "(pEDdQL571PpZmlVv!Uh3JMgE5RD(=THRIT458>%(h=NJ8}&3Q{dECVXbYd!+>uQRk0gZke`6pX8Hm=xatUB+AD8"
    "|;ls4Fug&qcsK_r5`I>g7`*sHk1-o!0sshsL$mn>C%tr;Oun!MLB_kviLt@C)@eUU)CS_$oqi%39VviO)g)7f(?}"
    "&Y<1`P&W`7-Cj%LV&K_&BzUKI${KG^Kff?A)XeyCs;8kVp1x99rMx}I=2RgOJ=&KQE6kD?0Miut7!B0>d1%X1J<g"
    "Xb|Xg6IyU!@&@1VQGSmb`j;J>oKip9!Ny1_xOHQ9)D;G*vJy7*ucgZ0DivQ{=w94&}?YDBpD5m!ibsdt;ps9xyAL"
    "u}d5K#T+e<8Jf#JMhf@YlzrCBZ8k4)@j${UCRuBm{WBRw6$fxWqQBn!x#C)nnC?l4^5GuZZ_dDc6P&Fs@edn`V;U"
    "~e>z%F2<*KAEnzax<Rj;Z32fkW5mM2qg8v|xf$8i>y<XL3>H1K1R5PkYZIm=e1ggCRFjXptUYBr0E$EiDTaT8z>J"
    "e-*E1_!GgPZ6AG083^be~M;3nf5PHML_XGkqqumaJz9z;}SOSh~eiS7IFY6N$SS}LjcxCAk;+^fc1Qu06t+Mzp5_"
    "%OM(u(k0WT0>X3=#LmJ(Gs6KY)dG^mJl?xQFQ85CklFg8%te9xy3gwy@7ql&F0JF>v2$(zLA+!gW?NZVeUXcN|eE"
    "duzeHGG$q*6*fJw!e_f?$0Tk5#-$S@=NZc%k<JgKKp402LE8&C+7Ez*&LV7LH4emT{5IqQ0vYPongXRkV`kKf`RK"
    "Y@+)bt5PP1L9&in=E$UKP$8?te}H0)^CSyPJBC+N2UF=3%#aG%GKm`0lG`cR#G3O&5y;lygZkOwTTb?r^C`#3VB^"
    "_>_D4jrDmtRSM&@EU*NI$Gm|3?0xRGy1D8D*gfN$J=KKb^C?<!BycM;$5`<=>N{yf7!R(fFr5U1H~xAKTl0f{F84"
    "GPsRt2D%)A=kvZjag;-c*0~i&gB-EFSqB+hc$#XZm%>;qs6kkQ+Spvyekeb<rEu=2iDXuqJd~87_5vF+?r}<$d3="
    "2V3OrSpaC!|RY1OsXE>3r=@DLqjnAm1*!YypPi<@|OQOaH+@wY8S=2@~_6m(oW#}5=|0=mSpj1eAHMdYwWhS8v1<"
    "xZ4qymeXK6mg5!ae>~gb(ToCaLT)mAdAKw_lY#0yP}sRPH8}&CDYhv2*5OEev!j<NH_!sO#1iW;*sME)q7B&Ui~j"
    "6`{>MohebZOyaV$2tVN;!(DXB#*V)C4ZArU?6_~p58_@WgaUPyWdOit3}Kugki<9Nh##JRr$SxUEK?b8e<}`NA43"
    "v>i<Jn8ZWf4ziJ92NrK{MDFfPn$l`=Y@t+<ddAAx$)1%k!II}S&q?=oKVEWBe;;_Hv;8z)MY@?%|&<dd2}`@S~BT"
    "Dm>7D~Gz3sv2S;3DTc>>XuPe1C0qW8%LuGhWdjiX$6R(o|~VCqVsHL$0%`4)|>Bl&?qCx^7BwU+cAm|b3^2;a8(I"
    "+xA81cUYFBw8BRfbM4zt16@WFrF!VSoaIds9ZNxK+OZ(l|DqpSbe5x0m`K)9QI&*9BT<!kVZXG(Sk3vb!=K!S8n+"
    "qOr_^l^f#memnc#Z=p|55zgA941Az)d6UR&i6S|LZy>f9;@!IuKAEn|)FC!@kPncB@3(I#(n;DkYnkI<A{WZ#5R5"
    "tHQ*42ftSkPXQPmi;xlK6L|07jQc_sVO5I=WdoK9!A+;k78$s*`o51rIGXbvbDg_1;^}mTiIZzrw{a%dr3+0l?p1"
    "TWCa4&3P>p$Zfz@dQgD-=*B`FU+bt$EW@{gx4B?lKn`Nz|j^~Hj`dxVSd>ud<NKvnQ8w4u}j#F}O5RaHRi@aQSR`"
    "@o~(lgg1%{5Qpo4^6&#^aG@Gs@o*CLYA7aNmAvKM-~WX>^w5*tsP?jr2?b6?u;7DGDdWgXTbO7bOa9d-3Zj`f!R1"
    "%Dt*3ku&mbLRr<c~49X4pj=NM2K_-ROoQIuRRETmzgV|6;;IfTYdRudWDA!Z3)NI3J&;EKj3V)p__1S)0gvB(DJ1"
    "riZ#aI4tB6tv_gGHL1`pQzR&fiq~k}S$t4b!Nqxy*_fV+zli07eeCbv{>qTn264wDR{xf(M;v0Mu$*tXybUG!TB7"
    "F!G0Hk1%xc-TA)yWC6jP1)M-J$3SLCf)fP<q7^L?Vo-0AT|p(1eBo9iDesn11*Ntt>x#rF&QS%$_9wCHHxnsZt>F"
    "TCTmbql2rN2F%GsxI-!M_%tr}-+kpU4e)e2gMY(QvPk_)omc*(7af)^`RDw(WC0JRVuW8&mXD}onxzAC1qox&^5z"
    "RdF1vhesnvP)&j(0FY6G+(8*U$zGoDffsqUn;56m`~bN$jUf|tTpI(;Pa&@G4lPboS_#GYQgcJ>XA8?^ED##T;1$"
    "3YB<2it2!T?j+|qWyG#R#Fzv~@_GppbgU*^F5f$@Wr4L$s`fPJuzcR5(m1J)${^S>!5Pu}ddnU?wdQ&KW2%tWd>T"
    "ptChg7pUhO#vA^rn*PVM)skxx4c?WxSB@G2olA`*zyZzM!MIEKXuyhe{>uD%V+}W0l^d*=?%!TWb>r$~n{YB&b){"
    "A=5KntQNRm0(|h!4o)MKuYwRN89kL^(ViAMt#vA^dM!YB;x5PEbvHNoa~I0`@qPFc0I^!eKruxibh6Nig%WppDBf"
    "TE`_{vvW6JvrD_8pq%U2n4TA@wifm8~kpN768?8)iD=oAvRmCTA~;^^?r;kodfV&Nns=gSfyG~O^t%-z$-+=1~qR"
    "H)Xtu2|h_4svS`bgBd6t$$>f1I#4aj%V8!_x!gU?DoZ1`MtO5o=l)`aPioW)p>d9tw#3ywJsq0u?8=YW-rH7>IRF"
    "{<Y#c!q-#g@O%hvTutySLV!U-x6U1-T0CG!O{v*5W>n5<I<v+4Zj2Xe^(MxjQZJ$8leQ=$Smpw2uD@e*4y$EW0;k"
    "gV#Ax>9LWoMR7eIiJG<@VwxUM^9Jp;(<KS(bOu^U`CgNCpNElK4iF%FzMr8e&%Ii($1L@l<r=ho6ewu6R=4>?3cn"
    "vKPabftrZQcB=%G$r#;QwQo)FDQ^KPw+I#RCX1k%S4w!9H821g>{@y9z=$vsOzV4pNl)G*m}B&&j~T2DwmuaivzZ"
    "mIEE9QqD1O}0=VbzH%+ln}8@s`qU;P6O!5xlH=^V!~dWie_MVbjkeANb5`0tcuqVDX7pMXA~pM3j#oqi$@dpJ)bi"
    "RTfXv%jcJr{NrKU(6fR5Zh}kE$S%pYwtA{N{wP;m$cus2;^<wAJB0t;g$NpQ*3STyc}+CgKPN~V47ZbYcMx%`wo!"
    "*PyD{;eD`v=Lk&ug=x(>}QGAx#SILs-X6-@?9pkD@p`?d7Bl9Qd@X4va6T4Q!whz|>hSu$N*9=G^qtzYsIYTm&ku"
    "wr*Y6zsQp=)M!Pa>EE3e`mR%0OoGbg-^R<jF#l8utnQ?n{5mt^BL5bM&-t3g{M3!_Qu}QHrr*1aUAr+YfI0(hCZV"
    "c&oJK-Kw_iF*sL!WsR=NwKx4*r74vIpV`|G>#ZAI_txgEdQK3H)mz(08>8@m)N#yG=%D57ewpJ?rCz(76&ShLFF6"
    "7GrOLj3Y3nl%tLRs`>Ixp@#Z%aLY=tLSUuM%)u`zxcHzcKEOZ~)ATkNXwM#1=MFw?%Fh}cIIYRz}2_9)eSgffWZc"
    "y*9c6=jrnDck~UyHXb?$H%Nnh@4?~sjVaLjn_q+*MR6%Z=P{2Y8&c0%__n}m4fP`1b<3dAMqlALu8=&1dL0LIpo="
    "e4+e>eIgxk~2sI(U)@@2(Hxp$n_@9$A_xxI0%UPija^8Ggh*hdo1_-*t0C_EHs;*O}pXEF7XiWBfYtWo}Wizk!JT"
    "7GYu=#eKC&E*89l#D2k+f!EqzKy4XX5fsqK_y&wT1Rp?>jKU)IjXf)=P2`|273?ZTOnAb*oLAU{+}vb9;tjXa{AG"
    "WN~BL91Id5ZafP-SAB8@Z`4Yr>Sl+}`y*)ZmPa+9SG;iuloI0xBlzO-bU2-NBdy~SPH?1S4AC5UrC2SayohGDPf("
    "43yz)AP+&#rW9fwU01GB!WJ+bVo;#qFMrcqPEr>Xwu$zcVOehH|rOE@&l`npyK@#;*ezMh?0vPmoD#jIT+>(9$;X"
    "gZ^@fnM^{5XHOwfE=;ss8us>nil4)(FlcZ&e+YeOH5ODJPFpO#id^dPP(<bXKiw(t=&WE(~sf5(*<-DBC@ewc}z~"
    "6VYhz5D=QvT!1}Y*Vp(*!wLpYPlHE?yFdb5odX1xvAhLaS9Gmha0#!5*L|5{U23JotpaC-C>7b@FJ^)yoGCue?Nk"
    "8O?vUN6k2|SpF3HkO4%4Y07I!EAeyN|27zvO^bLrq7JB*$2=MtApsQc*Ol?~H`;vDF)$7Mh;N%=}bz02cT8P9UC%"
    "Cr=O~x5B2+yIq3;P(Z60=b+23r%V3*u+90y1*xn=vN}f-S_~c&t8q|KtI$kBmBqB(gNs9gd;c0FY4{LF_lX4Pp#<"
    "6&+!W(QFnARs42Bv66$KJU#G|$4!ESCYdb`O^s^Hv<)q;!Wc7vTdFy6XYSG6&kAotsQZ{MDt{B3lw-59h`w_{p3#"
    "}8T7s&p=)dzs~KhxX6jOBb$<3t0N2h#t}zFVI*Gwi=nu6!iiwPV6&BN$j=1oq*xbMPGA}=U=v;2V=0;VS2SbkEX3"
    "vM3-rhTE}oVs6(r(j+X`V_P)8Yz{Hf#An3ialnO!um4<eOniUhw>vk<iJIveyIJ`BBSA#&l26$7_#UOq7I{X+3Dg"
    "7{27z;^?GAwSy?KJ?3AZ+S&jL@twKA>~aH(SK08w{zT=VZ)H9s$aR#(0IVZWp@#mAG6LaSA}IoSa`}g{NQ03+rdT"
    "?X(Q34hUr`$yUkszPVl5J}>xA2SiDaQTUi{(YZkuT9T&*b&eQ1*afxrb84(5=Y1LL!D)o1b<p4>^_vdWvB9z(>W|"
    "-dEg)nNxD#C}aJ`l*iwKgCrhwkf6kOU!Pa}jjQ#A?U2$U5Njs~N{uv=IPTq16}K+6Z#9Zs^M?2F^9B#7gW835T#!"
    "=*QD*Y2(x*JR%nKZ%{SiP0&tqZxsV)Kg7W-G`4Aq}3`~cnZ+W)jl-lg#L+|e-h2EFg&Qe^5Z5XdCP@28?U~^5+Dn"
    "=4!Q5%6l-PRtH2YqG_Y)HWND5kGlgVTyD&!YhCccT;1A6-JN$mUWfT_$a{N53xk*(uD^VzHBXySFS5_;&YNd4zsj"
    "2cY3we^9Z~bh3%Bq3texh3oqu*%JA*p~S1`x?QpS6PG`p}RZbJk%8H^@FT{(ic<R^zN)A`cGF{-OkOUT<c?w$qVK"
    ";}o7eByYT~8+8UmuY;|+P&kB8)v&EF97SSo#?0KPs$*+4+HGr(M544~+%HSxtYuZt>B2{aq3`0;mtun?Pn(1a@S-"
    "lM^NY<`n-9aklezuoWm{vrWKvAf)aMqwFcQ3~@H}5qCaEc?nqAW4t+RJ$P%mzDppl<2uDW%RDOSZ>z%4YS<Qrko3"
    "=7Pq3<zh0H2d+E8z0^Ejp+Q{>G4FpA`^P?z`Mb)RGdy-%#ZI7bPFyLjH^<yK#r4624tB;@nA<dZmC-GkX@Rih{zh"
    "vfkfl2dy`t!Z7;p{e%m`dKRkXt8U6iybb7pZWGL^IPocSmJ|vAW5BL(js=uV3I6OESH5S!l^lvDF<UzMvrD0ietw"
    "mIWRoxJDMqfu^US39!N|Vk6luHkj-Yk#dr1N%_6w#L<+u<wIEJ?TqOh3Gw%J=pG9}>&LwneXlEH?By>-+edkQZlB"
    "Qigvvnq53oy-TB8@CJ!hIi27cX`H^<`}^eVeD8cT`Q`WX(HZ2&aE9N$LJAqGfxmxmd%`ey<~K+qK8U6<EA->^ZFm"
    "Q0lh%v)4y4-zcu>1&1*K;-Jy7Yf5ry2+Z{?)Zcz7V7U8h~E@9inhJSCr#Ss&W?LcU5T4DIKh(5cW;8ODi?$EU3C7"
    ")3YHYoI=;SwAB`<^(r4r35c&4$RjmGY<M5mIKY2zPRW`_-VqZ+l5S=`Zn-7*y@sX%_iX5I<Fe1-om1`UX^I>GF`X"
    "gWJ8-Mc_ge<%yu>JEFY>OcufMNC*2Uk^NFT`Bzj<tpgH$Z=>K=y_}DC_@P$pfJ@gz;Oh$mIVtLT%cKdOW0d_b5MS"
    "I?q<MS2X&;xFEohgIaDuuL$2e7}wFd7IYq+G6lYxUI12B>9xWbPUfz|jJ;31$j##Db!m88g&cIgtk`&2&mx6+=Oa"
    "mOb0u2Zp))8r{)4vzl|@W$2hhDRg$+1#j#wWjf=ngTpf@!+W4@W2=ZLB#GRIJxMc_k$pq#r*m22xkcokxUE+GI6g"
    "U_9K0K;ZY%*@Cj+l91uFn66dif6W0sk)&;CLcXPg?SR`g6qwj@LBFcp3#+od1~`64QtSp6<9CpXcZL?&nbCCiIp2"
    "bMT0UI1yQM-JKc+_sf&?`+S_GE`%GVMj0?Fq#!&_xZO!d?zmN%19@S;uO$K(Ud*a8cBym#}L6dYE!Ii{!v80{n;&"
    "a*uF;42JSffm}o2`^ugHE3@geK)^I`isyAs*3_hY#N%d=fn-5Q4AW3V9Qb%kH?>Y$9XHz#Vfyt}G(-EOvNg_&Qt-"
    "XC?jgs;LQVi8W3XN2EJykk4nZ0&%=HGOI6or3EaPxI&NQ|qZv;q|t!HEi!&;vVAzx`_0lW!-k*^M<lYm!peZP(hm"
    "Wivy~qiU7OLDy7#(t>o&j^1FQe1JXGS%dC!d)UHywDn{~Nvi^>z|WBrFdfhF41V}u??#AeUFJ~DUDa{Lnv4KyY9e"
    "K?U!td@w?})wQ@|M=5r*R}$Vx2|aKLf2j7nJW7h|>8C+j;M=D`YoY%u0^>U3L`x`rcgaT}2mVkov>?HyvI1ofrDB"
    "7Szzgb#S>t>NJ>=rnbh_1ejlgOBXrPsMIfBW75ef^)EnfT_F;c5Lgw<8KQCVRk40Mz*UXV44W#=#cfqs^?sqDBxS"
    "kXnGbN^)%LsZO-29?~g_Y5D!#Qn7My`SH}bU(4bJbtg+KPA6iMUHSt>DL(g2O(d+5x*4x^!*hgX6+0L&cu1lRqS8"
    ")LX1;i1CvjRx-R3P3a4jg9{A4bz$m=?EDUSP$%J#Hk1qT|H^V*cLVmDgD+=Bt$IzhHC@NVP(iv@Ani!<8yZQHx`M"
    "Nmt($;Uz@!aKWKu)))IY3<0%blMI5(#A*p?8zD4xsZf*{Bq$SMI!?1yInAI5bTmyuSXfVPujA?U6JvO)QXKXI=Y;"
    "_Euyh(~PghY1g_GgTI*n%$jVTFBh+<5~>G^HO1^J*BJCz&6+H2S=6Bum~Ud7We8Nge+Q14lh4{D_lxHpV=j&bv)S"
    "VSR&a1?#<fhzC;Qf>&g>q&T-eT*h~gjU+gGK<sl1F{X#T0PzuhjT%gsWUMRi)$>RO$D>4?lp{EByl9ht7kjA-{J6"
    "SgfZ4CF0X0Zi9SKE0Hk1A(jXTZqE`X-H^f_&QL1a|^vCHlJwjsTLJbaTVk-?rJPFg;6A_A8d<7t{8O5p)gK*dT;+"
    "(s|4<#@s;S@GAbgQLV32`gfam6$OdNLCj$&6RIH(^Q>cOB(8#F<l@5@u6G=~bLY0-k|^$b|yk<Jn>!FGO67(;{0$"
    "#518tqA-WddnoaWgpX1z;T<8mp$H*Zd4&~>{~heqfR_~|vp>J23M|m6wu9qDPFQ_uS5^h4&$7vAaYpNx@d#^#SwO"
    "-JqYYO}=miWF8Pf0=&=EA6-c0P$EvqS%LNe{nl7n4CGbji^(he5|oWLibbRs;~H7wK<B0{xnOP%=`De%g+#~Ut4w"
    "5=Odx-crOXbF;Mx32H<W~Kd>dMt5TUf4Jk8``(BbaEZ0vp|I=!(WETBJ-E(nRGPXtkh;++^imA^K$c}eZ`=-a~RL"
    "3tQ_j%g<aA~4#0j|U#&cDjM9C_x}{#cH|7ciHF>11iNfiLReib*Cu9F)?`U+kKkA&ld&9xs9L5)jovzqB6J=J03C"
    "#)iAWF+Tj?{U)Isp=!Sq%<bAbXk`3@>zAEadO7mRC@_jvO~S`v_?R82x>3|NQ88aZ3_EE?BtBw)%1@?}_3X$`h;Y"
    "<s(*lW0vbJlU31!(e`NctXqJplC7?;aXW+^F3lv_KOk*XZQ|ksKJx(rDkF$zUSMYGNBlS9IDVi_AWmoT$9T316T#"
    ")BfYC_YgvB*F!bx*k%BcQO%vJzYOM#F^`_zIm@-PuHc|s(WPZZ%T$5P{lYLTHR!#jw)Mx_bxaeF=Trj{XWek`n|N"
    "ga`2!$QpSsJQNn(+Gqo1fZwl?Wy?s*>{TEG(9r*8auLGK<cY77yvaTQU|y@2%sRx!S6{P3ugdEv43)Wc7FP9|NQX"
    "ecmR3<ZrtGXosn0V0$igRl1qLQL4T2|aVcqyIV!U}o|kYRHuR#5mb5omjp#v{3Iau=1Fi=E3DZ2lVuHMxP%IOO!~"
    "MV~2*qa~c&@kzvsO`L%(^k@+-l$CdTYJeTW9ApK&a7z0#PIXh9jw54RBrlZH6qjP%E3Zin<N?x0BPO1MzBa|9rqI"
    "WR5jkS7DOei73UDMFIaR;Y{T5)pZGem6ww2Z&?2oA6P5{2pEgp4*}Yo<(&_GakdQe90-Wr2Ij;A1aXwHE(8!Q!WF"
    "BUB8p-r0v`Y(;72TGmeBP9P8Dzb^wHrDjBHKq41eHt7A12SHWhs$eOl_CAWE+CC`vKp8uUdzJ40E}!swGIvsrk@o"
    "Qto)i6brLI)#g<zhfrFWrXJ(ROB^>L6|Z%$cNY@O!4T6N+^^OBKpu^%WMV6k|a!_q^pMkC2t8TXS<epj9?@HHFR|"
    "lWT$nTd4rY()w^z11Sz(<uL5;w_H?09<r=XsoA6!k=bg(<+nV0dTvN+@ymg!z3J;7JPJN%D|9#6?AdCE{^&w*&wT"
    "hxJ@eDo0)=XU*1>(t*9FQ!>TL#9%K!4@l5;T4SdWffcsX{VcJtwHnsBvj?a?Xt*3_t4uh>l#H1bE56wlD4t>B0Bp"
    "&+UtQ+fOhbZ+$FmT~)neT-(0T5SmtcrKKQzsRW&6yjLz)`Sco2T&ORAb_TE=<&?H9kAk2i={c-vG}GAGVI)LDfpt"
    "{U>76Je$OicUDq_Fi@4|HMd{B~Rxr~!LtrNg@C%eRk9?DV^y&r%4@kiwBBL0L0d<#6+M`2(56*dFvFg<PPKyYBk?"
    "xR^I`U90EFgzr8qSyJOyc18T954iUc9p?onk^_JPI9k7i9ktUCKwxh$~eM9Id;4Ndk6#pUSUORkK|*OZ7AMrE~z+"
    "{<zd!BXEb8!+F2h}Oelp=p+3%^rvuVWoWjc9w#M04L;zGcM(`@4KRf_;Mi}CSJ33NmpwIMIoXVR}BM|kHs|bvcC{"
    "(%-*je1HE-Xhdy<iqOhn)~l!G%|fI|MM~RV92`9!Un`{YB-jJ~zPw_A$zo9h+<w+^SyA6_c)S*DyxhV&m|A!)&5k"
    "8R>E6tar4$@#`YIg1TO%cSBj`*<}(fih+i|HZY_0W{Y>7SU=-I4~GogjDn5W-8_*7EE}q4(W<#0zx|#mSOKej0Jx"
    "eYki@E;Q`;;)KGXNM`E#(XfGLzJb^DT095CGI(^A%m>tSgm+5bNP(&+-QXU(fh*r|Mlu8BQ>DmAB~kq9!$Xv-lcs"
    "V5$W?$}SOb2L-ovq9m3@DLsAUN5-<<Uoxxpt9R5FbfR0!}s=7@F>0-s+S&NMn3bW0!{JH@~``9!Au|k3pTwC;K;D"
    "(rz!Z{`;X9B5Sn^Fa<+2S*%tD%Ms`|q)1!U0lbmgI!)9s81xJuRrYh%%$<`vWA{@tCFT{AO|Bo!j(k1vIOc0en$f"
    "GkKZ+*sU#Zs@l*NO~Ks&n^E3{jivYd$Tn-r)1a3ST_q8XsD|tJCvURBC-kG7M$xy|iovl>hPn0d=L7hJt!7Ws<&^"
    "rzRtVghhITZt}G_q#7!5RFK;H56}cdGTsbCd7H^@D@zcnh2+@1gjyc5@UCo;>+h0R5*M+2$za{S=Sa4G!BW)M)&S"
    "!I<=|~rr{3brXpM8rg@J=!)5H~9UGm`T2b3)Da)~~D3->0l5_h}R8bv${vX50vwsvx(emPkp1iUX^dbB)LuK7^iQ"
    "S-Ak4fnpoR;TFdv%D)XPDif~&(2SOH^nzQa|{vQ(xx(KW48-rlNGr+a1W^J(I(Oi8U$W2PSJhwwer&2-h1(}kTz+"
    "3XPIZ<Q0t3dvho_(rv%SEtTTYoC8OQfl(9e}1l*}*lqBLVTVV?d#zXq~!Pc0sz;K1)bOPdZvj5l7{;!bMLN3K3Dm"
    "!vEoLF@1q9eQ=SA|))u~D9nNLsQt62lK>)L37<<JvZ$LPG!zh&3h;gxQGwqm#4If%ageLRQ1k0Rwn!r$aaw01OdV"
    "e*pGlNe?{Rs^Eu^no}VbX?B@Gv>D(uk@xhP93A2^ic$oNKtGCm6rO|sQIZfPgd~zS<;~N2x7?$c<vtrgwgWjW_my"
    ")}<*+s%Z@sgKx&2vw^?qAV4NnII_W%e)frXi>hbcQ0kH<Gp$+Ss*S{r`{8%dh|5e~#JN28scUC~1qfW;VOwIDk!R"
    "{i;Rqv<|JR>a^a`b=0M7#r4~OdwohGPxg!&v@zHC1h>jQW969mWpzg#Fssk5THSX>8uAhlB`~%<a=oLUzlGl!yJ5"
    "Qe1ZOx#Fza=RE7|npl&Ubu!K-lb)mQ`nj<pKpoTHJ)bOcgSY9XbrMwHEzjcuo@|nrxW0Yh5@uV)s0_dwEJWiwest"
    "A*sXE9M+J$phDBM_%qQWwFI<yT=E|C2m;@;&2P&1({LMtuu%Mh_20r)M=UAkgZ^xPUT{^hUnI^#U?l-?U;Iz-^gC"
    "GfAP&41#sy%T-yElI>l%)%ouG+Ot=*=cTvd^d`KDj<fO=)WoP@G0QAjg3jTtn;C+WJj==steavPPNRWh&Hk~xhT{"
    "RQ8CcpCf=8<t`_K-+M5BGTV|nE>2ubNoYTMRv21|_Tn`Ad)2y8BCGKtf9hV|{g4aDwu(!6vx3&Eo-XM)^5?(~ee<"
    "a0V<N4|*PsWkJ|&_^&jaD%cs-a3<PB=&IC&<Kr$Ab4y(-Vz+7H~@(!*KwZ*DLdG`7oWFJe%;2iqZ&UR9=DH2qk}W"
    "?ZGZQ>r`z}b_Nns&@!1`R)vO*cHT>rA><rQm+(x0z<ESLyC@%KvAQI^Z&$F8-Ee2xkgKy=!9B2yz)O`s-49G<bn!"
    "Q@D{kV)4g%#5~4VQ4rl#jz=zpOw3hs#1&A#uzlGLqJG=ZMeviX_>1tDjfulbUVM06A(F%_eyi7L|k){gtQqnHNGn"
    "Kj05J@86pT(kN;76=NKmHDA<GWW2>zML{QT^3|D^#4-;Ji>yhJqRgXk5vNxJx6oOchte_yc%uB6YY@Xm032@-HMc"
    ";|cwa}nJ`g99B1*ieLQY%ig`Rq0O~dFlZ`&w7>}{|J)7fSAX$`IDA*%s`<)>K}ozL5W*e2T(zT3U;QZ5$F6lY?YQ"
    ")tKxAwI*(8~kuDJ|hR*f2P*&O|)?>im-UDmLLPSQGkSlToUOb%jR>`lK^Tgp01MBqA!jh5L<80V8qB!ISrG(oqR%"
    "@%Z}ycQGM}z`#Abk4y34-LE#`VG5i>!Vqr`FpmzRVXo&0&`s2>>u$#{#`2n{b44Npws~HIi`ag?cBGJhi7ZBr9pr"
    "dcg4rSZ5w2HXRCagEgEC=(HsS@?E4QD&=x;w^U8kcdH#Qy}{Im@qb+rD?ZwqtY+<4Li^#20q3u5WXK_{B=x@LC^#"
    "6n!j6ZEpc;7@zT(emuJ$k4ydmz-`7)$!v{-<J0RTjc)&>(aH1i5QoNi41CcnZlUz3GA@%SFfPoZBF1b1eTj~Y<`r"
    "4aMqQAntJLzx0r~jjeRYQR&}Er~>7PXqn&J2(<aZha;F*Z6f#OukFlKc08B{E?TQ3FuO%>B@$%hV0YfYkV<%<^8a"
    "Fu|7!w(kOt)?6i)Vky$X1@BfXsHdYOc}ahjIYRUeIzw6z+9)QI%cIw%y3i}J4WP!Lk3)y=G}W?{-&L#X)#jH)kdV"
    "EFE^8lQJJWCjgL#Z^<9e70{nOz^@+=LUuU<p8!j1#H%vGoCB#6}C>JRv%$J!6SF;#FQTO)uM{mzZ2b7no&2n&`12"
    "&~VDXuY6#?ZX+b04@k(g$%Fry(Sf<N(Pe&i?C2XSRqxR!}*-40G`2Co?0Fq`Z#quwxP6Q1Nz(xl^hJ!FWr?xxi8R"
    "Mux&rxp<YTF->9&7J&8uh8a2v0fd}hg>}lWBhFZYnjPlp9?#9tF}PLcD@diFz$EY#0(L882x0n8T!5ke<^_Z)V)|"
    "4_hTI+_Bav?$%{LwcWBawH-BY|UESHsi;!!qp>$t<-i<TH^5J9(TQiBf00Z&i0S`mlC4n@VYcJgZ_6O_<)s>uqXS"
    "Cf_i2lR&I14rd074_)kH_IniQNUd5pAesE6!(In<cgaWl$;i|p?L1N=DOF_*u0j3c%D!fnt5<{XmkS%^B+oOb`1~"
    "6nMd#eBecR3nWE+yYa`l$0rb(Q?E*E7Q^9BX{I>b{_C<H_^AGnz80Ecvc8JgTS$cFRF2e*;<tml{=|+6$q5$7aAo"
    "fq*9iMleU>-?oIe}lFp1gYtbU`PMq7wY_EeG%DQylWQYRK?%b<pE2mcy+_BgbHd8yRhwQOHVVWK$^_P$yUk1{5Fg"
    "t~bQfn8T9F9__yRH|);(7wVjidvly#W}i0N27w%m3jicpvqwAala>N|vse4)c1g#OKjaYAZ+0p)4J%(EJ~U<9ZZt"
    "f4bM4;IhXhZrmZ~!aO;w)&6&m%maJfw4sF*;Sa76-9w;I*ak5L}a@BSo>l&TyQyhYNd)NyAMZ68+?HimH*)U1~ox"
    "Uhn9t%=XuZ}-m5wkg^Q?{PvU+djeZxeeO~-J}G_Dw|-uSdw&{HoP6{Qq#NExfyKse-fF$7RQ<B^;DuOIc7z#w~TV"
    "IF-Lh{?CF$cN?rm*sl3)1Occp8kS&G+pnNHTyu_?kU^BFCfSYoeXW3l(gD)fHFI0Y8BSo4IBMt>x%(|LYr3io4%^"
    "L6D+fp~eSeYpb8sm9Mo=G0f3%}e~6#T3jX+EPUpU?x&1n1Xo$rQ)|TteVYSU{+dEGD-I<K!~?M5llv5Z7To>)lZ0"
    "6{`QMjs_oky)2zZ9|S^IgaWL%iJO&N##1umMW0|gdp((@w}eC<D&Hnq5EcER6srQz0Dj|~F-TTIT^l+KN&l2!pXJ"
    "e24vwcl6iE~<RZz}lRNjJTAHG}!0t{nVr76p2bSy!PuY5%g>dt<dC%t{~jW|1eeRzBhuunII%A+eY$lzK+zo+2}Q"
    "n#i_6hZ-HWX2?#V^H!mhu}wys0yKW%{00UAqL_&6W8%<7NxSHLbS-_0vph%$lW~$18%@SKrBqJqk`58kWHR{0-a4"
    "skFsqL*9s(Lg%BwrPR<0VmGLy{ivyU4bXw}gmu6+}E-HJMt2p6de&EMHhz@y?#mQMOi9SY&{K7YMl>KIv@&%x545"
    "en^h#k$kx@Y*I4@-ck{UAE;(zp~qa;Bm}xLxKMT4JK!Ex<`EB1jyJi$x%eHsyRK*)2xQaJm}$#Uw^<9>LrckwhfT"
    "ro}h36BXY)+j;i9xAQ~q*^fPlF#fTJed@(UPxhk+t@QND>Mv$p(d)_Nvbd1vH+cp$y|zg4K<24Y!X$N(p+E?xmrY"
    "2B-wR9*xN&e32Yy8fm=8Z2vY@b?#+@v`f+O5C8X6)nokpf_6p8TwQ9=_s5Cx>rg1ebU208WC%2(rqTWY=udt9e2&"
    "m?;)7GVC-qxlecW<D-;2BS=^p&}e{3CPrBlDGnimBLlxiEdv@EuK*fvLJZ`6HaXby9ihxfHhl%TEK`T%;lXimNOB"
    "dV8cJiI>kn5hLQ_$;?qnNkbbyI<WFO%dSZ}Zq-uAVn1%}Qer0*o$61^pnPrRyT%Q2-@v_lUC1wHMHKGrQB_<ihZ*"
    "0zp*v!yrh*;6-ld*w<vz4?Nc%6K&gSAKT&+uHIh)#+ZT|gOi?;g9K3fysv>~_e{p=t8ousHG!D}3~x{948v+Pl^D"
    "exXCHuv*tO-lt36_g(!1X*UoUi^)`Bpug_Dg!~Jv+eozTJu@LhXhz_{2+jHn9)&^yj6XmKoYGM;BUz`GK?3OHpsG"
    "T%MIZCWVUfM1F;VY9kF&+V0U?MCI6oX$oI*ZF!r(3#&v5zDEPoi#r*TJ%Zlj`<+lBQW+=j%Mq7)ya9Kup11km2m;"
    "onBMXG1DGHk(8}gwgpRY*68|^Sz^yxQy;HlJy+~Sfbd$LKJZV%QIkj(6GGj2IBZ+^2=!N{0uCO5QHc(Ixv*f90n^"
    "!J0ys*l=?*w31XUO7(jUoF}bts3d0yzg^~S?q6V<G#4OGuNFl6~Bkt<g`0^|P)P;!zn4}}VW|YmPLOeJ9AOtUNc$"
    "Ov9nfqxeH9}dURpPM@t=8n-iUopN>4Pu0)AhJ`b-mQS<O;0afV7uYQ+G8(Q8Kto4(?^P%B_u-F1X7YDJ_#h2jVj~"
    "+o<xZJ+XMm5?zs|47sV{>?0gYW_p(`G$w-%gMq*piooe_xDCk<OlHv{Gq)6ZW1QNy0)3~-I`ssB);BW+t?#<q<04"
    "+H5|o{(hlk5Bhujnl)WY}2TY}?>=m9X8@om-6mdCq)0?YjaejM8oy&k@*-a-w<(1z*c6BnqQcq12>VZqzP`><-P*"
    "*gz!=mo2fz=Qw_cRd4;wnF`IZ7fAK>;QGE3C>;K!8ub?xtCw9V8n0nrmRdrur9;8$2#E*7G|>KvfSodeYh9$<DKz"
    "VuLrasa8lfNhT|=WdlvZqc*}|aC8=uqQ>fDoT`@_OT@A-uPT+<W89a;V3=HK}##=|=3KQVJllEB&dO?~j?EKPh(1"
    "Rl;*AB76wy92KF?>(szX)t=9rm(H6b?iKLJ+LwaJ*$)<3ES<@z(!_th1|bAwC<yx>}GGt4sO@#?0xj>Fb?YQ~=fa"
    "aD@Pm9Kt8D(A06RM8H)2E;hAvDLvkjfsjFU_;O+?$lQz*Lf0b(pQRt;JWDAP(IOYM+b<$0o`&pFbilupMEQ{8OI3"
    "Fv4yILS;lbvvqNb$x?0%Uo5|!hhWPoKvMl`3p&~i;@;g;%Z*i6{1a4j|2K}{`bUj&)Yi`6Bp5G0*{?&-M(4!}~7a"
    "Y0$cs#Uv}aNpNS>-8FP=;$Iv6z%?~BMU##NSIkP2i~f9X`~I2Xd@jUe(K0)*U*QL1G>2?iPGq{fkNDXD-F;qqdH#"
    "mP_M`FLAEFbQzQ3g+d{A8Y!f&<_t&>gPeapbm|qpc@zxXbJMUX&kzK6&4u&t;BY+)l8ZX17cfDGK>H5B^d=j&jvt"
    "Qr!&PRKdxBc8`go7z|gz%UKUWD6?j3{HB%-9W#r<g%Z#Tod&yZTG+u(Zj$@v&YH!<+1}?~!gtvX;Mmc}M3uu-PKc"
    "nmlT+X&&OF?A9r+#f*CQzNkc)esd8PWt8`(*$OgXtk?b10=LwBKs0ClbYO9TrrE#&lesX3!tqFs&<fwrSCw&)<)P"
    "^b??@$$+_8G!=Qyl3w1W5jq{>&CQtDt=M=W}vkzUa!LYXr;_w3|1!PQK<=9gOVE<fn+JKZ$)aopM_O4Vz#qvI=$B"
    "Py=ZN6%6#V5DLVlW1%i&Yo^|r*?P8hm0|R8>fB-@P1==VQU1@f!wuSC?gNMh;+m@wB*i!^rAaY)%E={`(!LL_HWm"
    "(v;?F18~V<n4xuU(U@$P%WyVdIeb)Xxn4es;1v6as&}i81Ej`e%2h#&C0i}~(mmKmw2Ai-PVN(ZN35~jqueJ$t)b"
    "`4Z+9AbG2MO2`$qch|TCS5QMu>!B5Ay7{T9ou?Go!3h$GDF#0Wv1`(^`nsUJGI4f6z;F`dn4eaua^a&`m>`$0WTr"
    "B%w#ws14Yfp)|mbohxYjJBKRtd<&}hAKZu&xrsWB9&YNxBiL5zr3l<!%No)}4Im_db`OH7m_})s$C<&zi>#tSqn!"
    "xapI&G2G%7%2WrNX0!+T@}vWa0BlI-U6b*ssmvud=+^aic{m~FVm$VY8qXn=o^hLu=P4c_I(9mseC*alV1fu$xEp"
    "7Men#1Z1$7x1#ZKqLG%yVSPDd*#j+*BK)A2A*atPxb}a^S03ovn}4E1+~U&Eq%k)2GM67)Htj!x>gjYZJjZE(Kcr"
    "ovq2tAYbKP%hCFS64`JQ6S=tw<;Y5d6aT@_f0f4t9n@eY=iT&Ypyhg`T4=66wE{HZvsNE1>%!6xPSE3_bSL}{sUk"
    "_ZVPPgPh0I&_AApt%pvB(ITk&$O1wh0R_U!$8Vnl<r(8m#BMrF3WitZN;}a*t`x7`r@_{Hptw#d3yw%%VS_APhAU"
    "3ke~TTtDvYR9R3~PrZyFgon&oq3j*v0TmF%LN2!shSbO*cU_)qA`&`bY&kkjVuL)l*BMyY;dPMe9R=(8G0HE)GG2"
    "5&1oE@Cy04G!=vr^X)%fI>ar6TtF{DY^!_ZWZT3VO1rwBJ=XkxJ}MQ3J(7H#VVzWu_}<~E6~?V7*~B~7oxqG@3uy"
    "&hFIT1xXqGLvRm;nScmwxh>J)i=QFmVy4d<r_$i*<nRa3|aYEIqlkTlzx08wxW?j@8cp%7&zCARzV!FPh}wHQ98v"
    "dWtLG$npi{&$O1{CqQH}gHB#N7n&IjPx(yC%UA}&r#L8ob6>Fkg9Ul32N7E@_KalNKq?_6!wFu+16XsVR2MWZ5U_"
    "-6yxsH2L`O_ftz;bEz@ekn90$Xi@(gA;(b|5lUs=hjg;$XlNUuipX%@HJxC+3tAiV2^lk2M5&&E3~{6A?CME+n`O"
    "`N$^|Ak}1|yqZ*@_3W-Fqs8b`Ty~I@-6qT%;v@_A=9I!qaWCfkAQG0LQDRF**D;Pf$#{X4*icKS+OH2q#^Lm}M=L"
    "q>uPJPQwpuL0JpL!zshl$O<!YHk@5fvFM9;%ATEGU_@AsjiJ#crsibVQ#>5h&5z-liNgfTJ8(lcJ5afK^bP*ou@B"
    "v>ZB^eF0Q!r2opu4GgcW@&8wwZQt4voaAWF(JIdI7QGWWKb$fyei1rNmf}DD)bX1+IZ_8UHVz6KG0Z>7{4O{w+UD"
    "aL?XWnu|GXTIj$6RZ&Pfxi2h*Y+Xodab*tjM+53B^i2k5rI8c-klY#UKl9M1&Ej9HU3RS9SsznzKVB+^X7v5~U4Q"
    "tnX`sz6s8hrv164xk(u}kN+tx><OO;sh`tl(N-@(@tVHJCn0x(QIKwotsg6y(863V?yo!oVpAzs$1|Ovu*}6pfED"
    "#rm0ZkBV{Wd$^)t#SSd2)z+n$sx;b++Z=#*gOEO!t757y^BBz=tvg&^V>P4+cAUt1$0?8`0VjGxvaJ!amUi6$jF!"
    "d0=xkpc9lkj{7rSjoWgvS`S9y`;x_?7~0NXfNs7<B6gk`r7{#4%NcMxBj@PdIt80^;B3CzIMD2cCPRga^1Z}N{AK"
    "poePc_}~uS9lU~bWMipUMTkqMhAo1VbI=L>Twl#H4bEIW0bBISe~dOdsjtDqSQnhy!e@kMfGbaX%U@?7rZ6-g@5("
    "v0snyZXREaoLztKK7?8ZrvGRtck)S4wLZv5#qko#+x}fuN$UM;Z_@TjtUAoz7(=$lD_xT6vKmlFmQF!CR$G4<e1y"
    "#uCnM4=Lv)iss3^61X#oz)%*XZapVvC!tURl>z%n*N@WHh^D&EaY};{XaRMmxMr0`(pMIT*-X3=PEZHcmS)M=?}w"
    "z3=T_^ilTLSD}BL($waz=@DQJ1?bJ4&L<Qfw10Aqb5LMA82SYr8E<vHp9>^)TWqV<n&)z19j0Y;1s)4j)oKf%dx+"
    "CF`{cWC$=Nn_(ha6?DxLEKpmLkI>)>;l@TYw`K~*z;64dPT{w<z&cse8)>y8cx|No}{Z?x&Fy}EX*apmZrCQG#lH"
    "P#*Pvvg3YQALy~6~W;v{c*qXeqi$Q1@Fq3Mbql_p2hR>{TuR=n(W?@8kMuR)hJE@F4S&yuf~ntI=In7unLzn5Z@9"
    "?z%y}5)Pnj_^b<#qUreIfQ|-NcL8?EFJi0+2EN#gq8H|<d=K}lqLJY^4{Lp3~Zlb$k5-u)hAtpTyM2B*xpkdTSC="
    "&{80o`W%5GCv4+BJ<tZ&pbe_rQ}USDiFQ${K~BC-tOH2TEQ;%CZ31^~JK>+%(j}$Ri(#&;_LL<L^Mgzh_YbsLGzw"
    ")5qB<lJn8(Pj7&YY}l0yd(v8K&>0ba9~`y=@4=K;I@I&AuEgmy%u`N&R@Ni(02h<694NAx`yknKC(xXC8#KRzdtj"
    "Q~>XvNtZ6L}rk-0>2BYeKYJE0+2xl?euN+B9Q*J=pZP1K}zWL}cdu4Cn?Q|8*$9Wj+S8Y!e-r_-oFO%2`X6HP)}8"
    "|!-9Fek@QWcJn3;r@9io^{2+iQqD>XQT5<d!)D~t64PbyZ5RV5}pd_)h`+hA<FOpY&2m8+SK%6O}%aKXkr51N_?C"
    "k%^n^mC&J?y*5L@3W#p5a@ktwNAWFWWXkV|UGM}i~*o;)IHYVq>O^Gq=600RZ6-o0x$Q(WY@YwtDR+Wb?y5c8AGH"
    "0s-^o&&j2uAo7d>IQoUIMHsR+gaf5zBu8;I9NC*q%;Lh%l1PC>o{C25Kv9EokK0ZmEOzMKl@HjrTNODmezZWb#+#"
    "g&Jb(cD(fdS(4l6dJX005C-}&qGgIu4Cxi(27Z>`*yhfeKvj;g7eld&FvL7Dl3UR51iF##ukltzCo*0KZ33GBBKW"
    "D>j)?UPyM~6EXX}Y*lHlo3rsqAt=54d(8gsW2!p7&<Z4`WFU$b54uejR=e{-nz3e|~fi$=Hf^NoESZm<Qdr^Ncb$"
    "<T7meV~2Y#{M>kSb^)N4UX2<!1`3c=uWManyU7)ZmZg4%lQ{bQ$ifwM5g|W_Ce~{CcB|u7D<U$kv-<-S-Dv!$gEy"
    "f-fEPm`gQZhpC=KU8*HZ&tly-_nwUf=Xs1w^4$nIw0SFjsf;u!>Wa)mnTvnfdm~f`WZd+BW4Yl=CR+f{^F+r6BbP"
    "wA2F!j+4;Sl5@dje&oR=L-IsZQehpvGmP@NX`XMqm!+DbR81KmL(Q^-Ed^Jo9JtJ&=}!2}UXgLLy~YBM2~}aYEMM"
    "=84=5#P;dv{Pg#2xdodWuJL7e$E~(%^=xSUdb%rnI#ge)HeiiG@42-@Gqz=Qt;&rS^{lo`7Gr+!ZN#mLEb9Wx=D1"
    "19SLT=nz0orz@y*_L>#VUx*cPMQnja;-RpWe;jN)=CDpExneykWOw%6F>Vv$7}IJM@KX`{BSs+otJobBvzpe{SRG"
    "F3j%wH#)bcH<D4l}5J=q@zw@2uc%|x;Q=Wbkxl<W07mOH4V$?D$DOM4A|%e5eeYEwTHFNHYg2ZmR<1dzmDS420Uk"
    "oN%7m>QGjTHkbHR)-4*!j7E%l_N^=ok<%|dNz_>BM#N8~2?6BknR{0cKVU0p*d}R@)A*A>>6jSrq6!+4*T63a~p@"
    "hiJMX2hw?f-T3W)GCWH;1oJ_s$Pbjwic6KB$q&vmLvgXFCsUXV+<G_kry^bJ}_Kz;?cM+WGc@?R@97^W6j6`QB;g"
    "`v<o3+-c`Iu#dq9Sf+`V#@o}q*KhXZdYZs`0wk#87vpsQbOf8z`Q9%_BXRf&vA;%tKRi1>6ZF}MUTRWLmUYh#kIz"
    "T1N2lWL>EWBb)8ECfqu*H)P&Of`MB;q(_j7FZ_}$UbIPErnlhbNDDqzv~5wZ8~{N(U>|8(?bbbQXAjA!<z#Jl6e|"
    "9Us#yNK^?-IrlhTpHSUPb+pCjzYn}bnL!W3B_qGn>Am6cXw^mI+f2mINz7~)~l1#(c$Z3XscsXy%49PSEJL>@%~7"
    "Uu!F$SYx>K`o_`WG2+8EnYTQU<Tl)ou8}yM>CRTsRR8aHQGyo^S6nLIifavD)M5|Vlru_YF2pcc4c1PR6tta~uGP"
    "lCy&ze?+;=Hzb3tRH>2AD_FC|;I--kMPOEgio!c%%<4^K7=78WQ_v^{DOZQYGs@z$HA?j!~H>E^_bQ7YCzPd+(0U"
    "#g2N?ESXZ<+yjPV73EmZduCCO$Lt2<-mdS#ESjyB5hx5zn`?a^v~F%FDu!ax>xn&#X&|jWO6OTV#f)Ce>?|N76V5"
    "5hpN=>*7|X_Cl3Z};I=lpUJ!nuOkeAmH*f2iu@tZV@4|tgRa4<R=osY~?ARh?p9zpvNp<a^j^zb#1-KVBZ(riKjZ"
    "{zfr5eQ#-);~GsN8rZm!(#>{rNi#&-r?D(v-iu%>3JZwC6GuSaYhA_V!)Af^60n?)EpfjylCCAS(HRZ$9Tk#&@pP"
    "*(=nv}NJ>_jT7feLN6TBt1&T|~$?c2%ELkm5`aqn{qEFFG<RRC03aPcrRUS(W#Yp_;*~zhFHUL^RK&rwNYRBhyP{"
    "eA6%7y`~+Ur@W3xKtrk50wj!GYL6IePczSR9^7-kSm95gkkiP#G$`%mGyba3y;^1+5Sxv^bLh-Y}VzcykfuQE~_O"
    "h(-J3ls^0aQun6aZ6is#@L$Q1-##KeB+GK`^sswWl3dobE%{1v*VHwANRUWMXn_D52})*r^xxkTTP|2AS$6fATOZ"
    "0ImPD?Rkr7WkK?~CEKwd4XGP*_IdU1bAlG~!PYDLiP?mnOl$zRbfE?;1u9440#r;NF^fY}xjZ6(=iU2^^{%D%3nc"
    "%b$(ntc>8j6wDp(eIYXNr&YjF>fg=smy)u9g~xF7(>1jqn0`{YcLV#H=Gs>!>1`tEm6Hcpx^QFNlfk7(qp{xj!zD"
    "c{<}q?nDG3gb%m>qZgl)y7BW0-BJ$f%L{1A0n6Tsq!eEojOI;YG8I9E2qqF|O>B-5_0lcSHMRd80X#OEV>`E8qMu"
    "vvYbF?0S?k$uIm+Pp&!1IDayeSyA%vUQNt0`MwPtVlZ(c9Pi2S-zt(-L(CJ{oU4`pr2JJEb?sF>W4)e*^xnH6{*@"
    "6cI(){Btz;S2|50H$aksm69HmRC9|wP4ip0c5oG~VE*i3iU-VVN7Dw#m~V7J`E;ScNTwXf{ZvOc6ub`hNisIBGeU"
    "UB*fHEWiQ)dBjC)zmT{{E;M#~;kHgLDxUgZXbLX=|SN8*cy5Z0V3;q7r(c^Y$$i2ak_IqTg(9eG<Hxc`>G9nI7Ql"
    "H2crlE2WaG@3inFJtFK|8K93PUO7~3;(?!F_!04J30D|(gQtq!{GWf?HG3M`?LSMih=+MaTjR<X*>)FdXY3ZtZ9B"
    "J(1IvaNvxNvyu?hp*LpKl<!#PcY77V)+Eiep$MA1j6;UR%20Fp*hXPe8L>eE)^Z=+6!is<tA($Ak-*<}1RfGVG8M"
    "EhQTA64AQxy=kuvU3y2#W-e*KR$bEEWKRMN>^jP_UaeJ?#%LZ#0k1_u<%}+uJTugLHw=PP&Bq^(@V2Jz|VPYp1Ae"
    "oOA*D8m^bzq42l@j$9IOP*@)xq!ihzKmutPRUkWnQN;m5sef|xn;Wv*BpdMbK_qyg`%xD6jV>jNCX7Ap6TlQOM{N"
    "YJ^3DVE0utL)HV}I*u5KW0JIBe<Z`JL#sSGlyBd;Zv^x#)K_c*`D4Y04AA6+;$J-{E>z)~=RPcQ}eykshkp4$EYC"
    "^gz{w@0-X^MYT+k!pL_d#dtg08rfix_flDeKP(~6%>WONzmyLl_cv?bhE~Y^NAcCSw73-4URCWC&0%PWWeIBO%kT"
    "g^9&Ps(Fc&;Ia(V{+a(gnWO<1+Qvza!^g{H~;2uK&mG~vbrF$)X@CjW^wi=;?knUe+q553YVw2v*-8Y%pq;U$*2z"
    "b^10_mz}Vs^pP3GgGZ(h8nQA}r7wX7`@yp2|7DE$gWu-Qhd}N@-OtSc{IgK<mb%7x%x!ESy{P(B{?fW4Idp4dhCv"
    "u{u3Df+-1ynGB=nAUY0{>H@PD>KVXf&%9TVsRwr)R`a|(&OI=~bO-9ZEY|Z9)$ci<<v5oXNZj0jyoNPU77^G{mcV"
    "BtVxC<ZCfd-s5YJEfoU4SZG&qH~?vUndnDAP+Po@a|YFjJcChJKjs92AamGUPWO}hT`p<UORsok<+q3AOsk`Vl5|"
    "Ki{ks8RMXL}olX%7X3!oHDFt5u<ZxS^;h`mbGx+LCpuKnW7S@K5Vh527|6c1jg>X4*D~e*!mVoRHVSBOob#|QALK"
    "W8`N#5Z5dd{M&Bc8{eJjz_sRW}D!RNZ^kv)0(oP~{bo@ESy@$=PuPtYT&Z|h<;9f=M-hcS^-)^#egr(QbAF_ddVU"
    "f);^`}s#p0A<;1k^61^B_Jgpa@K|cqm&-n2btj%xKSma(Y<M1QZTaPQr%?p+eMNJoA}j3w2XeGuA{Eqj2qrG_^@Q"
    ";Uvm@JE$MW6y+KL1&x~Lrd%)eKpmIXbfq!S>NeWgwo!p=bA_8g4^#Nz!SyDI=uiv`u+TsNw*dv*W+>#g4%mFgn<g"
    "EAk-OaPX5OxlWC~A*XxqWo7MfDHQ7U(6Y;|4Bt~t4R{y6{1gV%7=Ud*=+UL76$RfRHH{l}lx?k=w;AF$@t7z2Pr-"
    ">vKbmeATeWBZR=y&dXt{Ia@%?4rgVnajyKi^{S{W@``;slJTno83zAwJl4)a9DAa9bgBL8owB4hi9j6D?Q($#=wA"
    "_9i8mIIZ|Gu@6+J;-Py)l4y47=oyxw~x>$b>7b}>!NJmfrDw53zCp2mHIIU-z?MkplIqu&Yn|Y6?MH`x&B?BnGnv"
    "_E_e-Yg-=b^bQqScj601}1A3%a?~rFc2c-~IAmFyx&m+u#}3;s~Nyj>}N1^S{26v^uN+b+ItdaxTSLt#+XHLD>^!"
    "?d4xl7o!D+U4y1`UTJ~6W)<sEHfr&^a2Wu9^j@wU0Hveh1n8cU8A;YC@9pDrT#EPDWa-P5-HNXU_Sgqbu)Sy7XIN"
    "rbnN7$#=p8F^)}@d?BLQVN)&uogM>mxG63er~of6c-3&nb#L@5=YuLvYp5wIv+t!TCKRHm$zqRPtFnxZ5<^$>abz"
    "fYUKM^pQwmF>rAT;VR_HNoFP`h9hBs-`sk2ZI65dv4uSEs~V17MapfktVvZ$gHaf(=qa<O7eh<<9Winthz->7^Sz"
    "-#)$V*q1_zMfN?<%0MZj^C!x^!vSK2!8;%%LVcS@-X;0;8OtX*(=Zkzp(ceD!ljIm}*Axnn1(tKdhVprpl4v5aH~"
    "FcY`Tixu+t1V7pyv=7kcUu~+Z1s*6li59IhYu+lHVl2qN)8!#M!TJuaGfL&~OlRpBgq*W(KkeKt@P3lB?r4Z;lR+"
    "_b-lY1}?StjP2C4Fw1DU0-hAv8}cH#gj~^Xtx{@YvM|wEr_iei10rT%N6x^bf`z#{;aIa+STW$iOWjUp57Pah%wn"
    "C9v*;h|M3?D?Oxlzhfs$ojB?i$KpnKltMR}#JDQov2RB)UG=_GZ%CRl7eyQ_K&yXURqy8iR|#WkxstTy?gA9bb&Z"
    "AHFz#LW$rBX_Z34-Hi#_vpWL|Jth>Oat3MXcL2^ElEjnyZO2dGrI@b7H~dmKul}SP=pB(lX+5-1H8a+HcUpqvz=T"
    "rp7bC?P%^*5(vWW(rrb=!3g=`CD3?r5MkaLZPymm{3^RuF&tfFeN*Bv0Lw_I^xX$R9ND>HYLDL&vLHh4vmXt+QY$"
    "^&+XfyDQbe=V~!P@zmhiQ}F)(_HbOs$OO6LkTNFzj<gq8}PK)JIWDfUBegj}_>t{9`~~&BUlT?=EmUKw0PeFOM#M"
    "XNU0`{46DZpR`#%?|~aw5xGaPLH=M0O5hZ|OTZ~#gGJ{F3vSq$VB}bQpucRR;+)1BN(0$0o$kD7=;SGSc#K7N-4h"
    "mrv=0o%*%P>SO!E@if6FL=BlGLy^9yl&$B98!+KuBd9;p48y;7?p&lmlfj_9=egeC4$M*v2lr;?JA)bF1hDsz>rR"
    "`e>IqMfh>BWq0FE2=8{`1&l|y+>)6C71G|(B_K5<WlZO>$^7B$%^(`C~v*GEF$1Gx6u>a{;3>|5C#CzFEgarOE(;"
    "3KUCAzx||qYBvG3D6Vj4e{@q9pRw}_-lXI4KRTvd_1}oN?@tq>FB^AiE4;ErWy@^W-%ChzWfckLq0dxrhSGVW_^C"
    "-)+1acutz8{tff&yY|GLB8IqDwF~bf$jd;sNl1!)b29ZJBm$-w;pwWR;|ONid1j<V~F<mW#w7vENX{9nLx=4liNo"
    "K-vHRKo@-wWYZ*`ibbXaJH8K0$FHF(g$mab1<-~fO4VK$burMWa!u~)MN+zt?-~URv}joAGspwuNnlHYf;!VrI8X"
    "095C0S+V<0W2nv$1(+GD|n1=Ga7Lhlrm0i$peA-X1CbkPnp2cr)V<djqaLY;lX7%v`9fl~2=anpM52Rq8Bx?!#QC"
    "R*rnqv+&{eGH{faX==}d!&&=QO*!VYnLNHr$HmRJ3utQeS36rI5|Ce{rdz3^!bp9&@dno2+)B0Me->#+(E*V#yh-"
    "sdRGFG>s@E7qW>=2F1<_0_dWrh{)u?cOzk!)cENS%2)f{hoH3s=sJa&B)4?Hh@n@zif^5+jV*MtI9E}%-O5xTPh&"
    "r*Qc`2efByJ(swgODN`PT}1<Y(^3itvM93-;*Mtrhq9<#lUCK0dT=?Z_Nkxh>Efsn=t$IjwDa7&zyNdgB&724*Ft"
    "I)8Qi_U+MO5Bb}1&cPo8b&{9rQfDY^?UoHQb&(XNlvq!NELEO)0(NjlX|eSKo%9Qae0jDx6wqV?n>H_-?i8~l=z>"
    "*7*{5-1;ybvRK~b<X<|S1Hsp!G=1v?>c=N!!B<emswPKiN~M~<V$O$*vuX#G!8F45!yJK3s0i8N5h-1wzl&U66^1"
    "`)|v*DDjaLFcKrfS1i+8(pqT*3BZwwzP!24VZvKlOY|0J*jbwY4hU(pYP(1%FZa~^&RgJU)XpD;V$fwl5yM5RIUB"
    "caI4w1kANv7j@zUx3#@Lve0TBg?8uAYL_6#YcTj!~+bvMm=t9LB%7#bq+(A|eBaKL~MXMys=ukXGr;06kviE$#Jv"
    "m9tgqk@W1V^IhTQ?GK$7t9rf_);`BD$4>*YnBwtNrKS6JTXN`~JJ1zMXyhz5Y%we*7u^@rS){f7*-ZKSz7f{O9kU"
    "&A<P7_Wh6FEq?rQ?}z!`kMp0tn=O8x{V@OO=Wl<09(}K?Xwf|%QNJA{$S2CJxOHyv{ct}v?0zlex~p3|bp4C#_Ba"
    "vl)oly7QYyC%UCH%&6uh#nO<P3x_GX3W&~1|<ocZ@wH9R(dr3q52ZR<4oy0v}Wl&RIWed1KAyJh->HGRw^x~Hv=o"
    "=Sql+BS(qR^D4lap`}hiR0C+b;^8s-5xhhyt=hd5L>w|Q$y<Ym`TyvrbkZ)8xFBOLW;M`2O!HCH}ch@q+Ip3#7TX"
    "5^&Yw1c-7km=9l_yh4XXO9tY@eYuD#O`u8dkE$_0VR6h-cS*D-r8=VR%FqoVm2RdE!A^jbE@4H<?2tmwN#l9*s*z"
    "~zTNPu$9o(g{J$6ce$CYxUsd6uui6^dna2`(NPvtCM&7oD839MGi^Hj6%Vmwr_oEoj05!z*&*kX|0EYdl$iM;D>y"
    "k)VQm&eLugkjwm9qb(8aAMoj`B#w0^J|#lYJ7|2Q4))Ip$c<`0J9`-8uA<8bEHVW8p)sGQ0976^9uO@ClofB8XL$"
    "*hI7!JxPQI{Wc&q>;qh&NUDlVd1Dh=#4gOH8^jSx{*YHbwc-USo&u7Uqk&>TQK(U^3J-Wo61k3LU~>G%?5Sy$1#$"
    "c?c>!gSH5ath;7!-yxE6_u8tmHaBY(dZ0BhormCRy*lNJXsNzg4+o;TlA=cZ}SFi)NB~MEuvLaV3Z?a6;+`VW7c{"
    "*9Fh3bunHE9NELc0<3+2V{hq)MXwYd!4p2M4$=)x0%)CHgDrGziA=rrdu7nlJ7F}8~klroRcupsneI?{Vrlm7W_8"
    "f8(%=O7CO)@RfZfUd`@Cu*W$Qg{e;^oPkNGC5uAi^m#A`1hJK2*>opyzaHwQ_bx^l*dwL}xHo>r7bYD1gO9Zh?!5"
    "p*2KRj!g!{8>40E;GYs=_7)DI#o&IXiV5XVmLU%@`E|I3aBqPmE|YT8IN&_dC*l05QBY9A%r+QBC61(yMTLa44+5"
    "M%h<c(v4cRV4e(BH^F;G(vbur-SIk5nn35_|GFjXDQ<lLo1k1Qq%NbQ_}VQ15WNs8|A`V=SsBgPuxtZ|>+HHxx`M"
    "kxo<Ffbq#GicD_=LkFCXzxIpPK$Ns0o|s6_9FL(mx<NLzOq67s4inIa8Vh%nxZmaf*%D@Y>2r4V^C6-<e%S$owpr"
    "l+10)R@Mmj$$^V*(yam(w1z`Jae*9Wzhge4!D_nc90s4q29zgIw_UaUu2`?OwyxcV})Et6l!72v$lrpDR&>_5ag3"
    "<&sC|ScfDKnCzd~LnD19e6be~grIfMv?32$Pn5s^HD@>Wer&SwRvhj+zkdDuif6ZHZ&{5C+3>RkR~P=0*_a_-v#u"
    "6Vw>^3(IK3XdCcb;;ODV_<epKKeDbSV5CS6;=y9yL`gc!KPpEg`c0wBV)IQ5QH!ZALA`<c;i;QQ0%&FvDMG}=d(?"
    "55cLHEb&{;40@4oBr4ech`$F(JlsC^E$ETU|FC7L2{n4~Id^1c<Ifnf)B(79>W=l~{l2CLHblf;{=yeRwgq?oVKU"
    "QT843}Rx|9)c-wFR+2h_XR38F6;Kg!go!Fg`Rp_B-uP!f!`PjrNAis_Dntbc5mpGPT#s0B*RFWvtrTl9GBmARg{@"
    "qT_D<i8Ew?XtK)O4|Ih}2mmqA)-vnr|f{kFj1GDy8Z^#N=K`SMK&4|o3q~+$hYO(wBNz6jeIAomXplpfHoQ5Cvqc"
    "k0;i`!fs9=}A1bU|C6H;;wf@f^TL^dbRmP#tFx0Z$|a`h0EQ`I{(ZW?2Jj4uCrVw=sGZflo)O3?b6%EJCv+w>;Zm"
    "piTvqw)ZXhKp2C<(&3lmlf&~6ChMsHw$WG?&3D|8p`Vc4o>9)roZKIDM+9Kc@)B?diZTbMCoeO%H~CWr<Ca%?iBJ"
    "SM??TZf0dDZ?#Oi@1Q6x77dZO0o5QrxX<Rz!JY%;^JOGK|le2I=B1vw<P$2CoG06G;hv{NK=5oKzMv2-L=rdAy&G"
    "!SU!0IZPHnqg!HjO$WoF@r8!JzEw&tY$@iEhj?E5rNTQB&s;d55Fh$4TDn$<ixyfQ&Eos_ZaREbfog>JlzpMqQ9K"
    "Gtf%JD8iN0E)T<0J<&`GgtqUjg8obq8^FKkS7XBDK^SXHjbFTn#Na&2)sK8Tfj6k4alg5N69o#$<J58`GJbZ#$%W"
    "c6XI)IJat}k`APBK8GK-+rZrk$_pB!l=FVcV{5N3>-Ni#DW?s%_XC@`19Y1P<7`j}?Q-0JV%tK^iGahGf8{%h-(d"
    "oIIX(w!$7Dhdv5R5O6Af4VE5@JAwBQQVlUTbDl`h$@*3;5ZnTySxi5?ej8c}`{*iPtub;6miuMSA%QTBx{TZbSpm"
    "iZ!m6TqN+f_Ac&KMJ(xE=QejKkmxJ^EDFZ;e>FZ+3@-U2p+LBAF{jiDN6w6{Hf_WXzbv!D9Uf9|idr2M&$Xp(+n`"
    "i!?ES=<K;Oy3Q95BWu~fFZaV$r6Ao7KSQPSL<bzDT-a=Itfz~Qtr(tN12BiCd(G8X%WC}X>^lpp$nL+68=T=%MCK"
    "1^Rji6_PLP+0wuZbKXvf>7#MzX@<|LD4u))<BGNK;;X_hL!aHgpc!|<=#0p{L@MR=t2zVv{oq@yyP^l9t6;*szM#"
    "noK?;J=C@I4k7jUMV+rN%n}bs6rWv;|Y3M#x$g@xCvlCS-eMu97?xPG)Wua9gqk!o|8$SAgX**t0z#`%tVBrpH!A"
    "=3}Df`yqIggDr}UgSw+JgRFKajJBU9n{ZGMAv6dFppjuN0M`<0ofkd9Mc_8k8p5|F=!Br|4>pvsxTf|Fo+{p+p#R"
    "|Z`RQ-pc<4!hanSM`a4Zf&hA|R4I7)-Tky;DD4(LWV)u;rc_Ak_%)AI`@x@?jqB?JZm*cwWNA(m@?q&_YZ!RBoQ|"
    "8MdX;sSCz;5e)3WWGprVPusraegRDeWf7!;2|@CA#V?evBn1{bwj4(J0Kyl%P$0T%#L_{sx-|=Z{E=DaM}cnhD~G"
    "}O*1kiw`j1C)Zb~29=a#QiNl1v1f+h~jchlCEdGFAuJss)&f(2UKkzLtv&QLJ`zP_`hkjA|u;r_KyK8ym?=h(a^U"
    "Oog2iJWBJxuhsJ{odJ#*pfI!?fed+p@$SoDkXw^nO7;5pyN&I(1~KkLVR3Et(~J#O>t_COS}mN#jN(w*kIc_s6he"
    "Mqv(USoSpB=iU2g!<tsgR<CU%==EM#V&fL^mAtuaO=$J({*g_1oX5AV3GLqB<~D5c1UFXyF<#+^^~0l~1L4xXe<l"
    "jP`hoS9z3HpYJ+HR+OuDaC+b@}BUTyE2U$(mUPAsYE<7ZTBTenRmWSj+w35t-McGww$auN<ta5mH*DI%?MDq&&Xv"
    "w@j#K&Ru$K#g}!ayqH?YdgYtrxJF>3>c_{!A7#6vlV^~Y&%+A!nrfUQ#YRRc!#*ni`aApsLVca?}&bW`Ww*&=+eb"
    "$*yhO2k5vOx1tdH2BSO)vT(z2rt&2P3#`Jy02*7v4VFYb?93IPrO$;|EH3J;L^<54snomMuv5N%Z%;;(LU8SCm%m"
    "$JLoB25I@C8Q^qMhlVy2#OPLqiI?b65uU3n~{FD@*nSviM6cr5o2zdFHE~6%YZOaGi<D^&$;*4s?@7cLTD8%QfW0"
    "As(&ym0vNiizFDd=10ngDhe2ggX)mZQVV(Ya*T~LT12#<c2{|EIibc)cGds<4=SaDBxcRAqCkf?WhF<0B&Nme+mQ"
    "u85)D`#9?9#h^!<8v`tGgz<#+eQtNp(npZuy0PT!qebe?u0g{X~mw|pZ|2AhWZfBrLa{@K>;_G})p&Tf|9V%ROEC"
    "CqP4yP4&O1~bbZ`%f_5rjMWzXZls0>T*=C*mAPhmB4C*6ZA2Gwh!Hr%J+R%4GvnPBmO#*ST>{)VY9I4eN~;$Q`o+"
    "D6tV^sz65!Az@m?GNKX6CTqIFdGK0asjm)RQugi0fZ+mDe@+qUwt;2^OOB@`UCc5ol4H~%#>jZgm%|fkFN#LsZfR"
    "1~PlNc!_=N{YCHiH6;aQhhw1U)Rg%T^CHmcJ_UMUu9%NjPjCU<+2TFFg{1v+o5Nnl#7IYfG1q@wD|}3K-WY7zVN_"
    "fK|QER0nxRjKl}0Z{F@-97At<)+Fp4_9v#f#2a!aVp#w)>M#y!ugla3a`x{zf0G@DT|1(XFbiCeR{n~(Pm^oiI2Q"
    "&r>yOL|jE|HJK@t_91%nu?wprG|1y!59Y;ObRSfPqelNE%y0FH_HtbZ4_JM@{^iAI|{I#HP>g0?A?0@f^oM)Qu*n"
    "mU;xPg(Q?OE4>Q4udqrcFp|QmNy3Z%h6E7J?gL?D2lrG;)`tLtIe0eO=$v^u~k7H@q~4_)V5eas5KpV-eP;UtD*S"
    "PcHN$0B=1)pNkV)rZQfR_U5)?3iak<sw-wu>v2)F~sp?cI+SctDlcw$s;bYr&kD?w-PohEh)j|Yl5wub~*lDt0FM"
    "*glhK@nh3QvDZ2b0+@tjLpuy+A|?84G6b3zytL{R&na9lOoXXQKhmJm7aMVg!rw79Z<{&M-eZgszoWJ%7_j)L9PJ"
    "XcoVa-VId_PZ=Q8nLq<P`wz127%P*SNFI7#ujBwdDep7?_+zqlLHZBgKSP3{2G87=ugz*rTUY2;tZ93ylV&ZnLc#"
    "k=M@2c)Q8~1<(BS9I2*nIKq@jJ|N*)}nHr)ZV<@lGQv;B*s*S||r48dM7c$Q}YuzvuikaO4!eZQT2f%IG*tKUw~{"
    "@SyE`N-9!Oy<`zg@n=?H_B9(#4>47D!?JO&OmDx=V4?(F$U*xWYl=a<V#Ittsc|8dW%}jT#I*ormv!#B)`X-V7tY"
    "tfbe5-pG)b{3YpI}m00vclNFXQ0k#8$CCU1rg|LzI=_NBxjdvjBt}+^fZ5Ii!G6Vi4x|E~?g4AKMj{8=x>!7V`*F"
    "ARsdhq)ED{ZP_C0m#6*Q(^>HrTL|?VGG$%PkwNS3%lrW#ZCa%fGr`*3!=o!l|&??#DO4>JqCG6kIe1Szr`0_82YL"
    "CkUmnGR$U8kbRLol9;;~pJ3&DfruBwdacV5<Yz8^0U-Q1(n|oDAn2$d8Fix(x#p580k~y;rQ<a)M**{0Lh^*;WoG"
    "&+VIVbZ$Ot6}WJ|Oz^X2{Q&!DF3;wDNbq~13qKtjE_Q+w{uo&ufekL3iB-qph>s3I}i2q#<9Mtr*4-Aaw9bOwFBC"
    "7s=#fT{_4#mTj|WWQ6(=%eI=-;(#~+lKsdu5+Q)+dJ5Mwsyks9i?u(JV$A~)(w5ipwsH*El_VvT#k2o?ao)r9qHG"
    "&$8~5*p^0d)d6BHjNi~0_q|UC{6@o0c?rH&SgN-{GF&fmSRcj->&hNNd;CGwaz*(#(h}@pvzh2rK#*`hC#s&&HW4"
    "Qzdum?9r&^ul`yw5bXr;<#4TT=vO*Bn34P<ACNd&^J<-=OMjnfGCRy{VsM^Qg$kP*|TYkFUGM4}L)ddfRJfGjKu@"
    "l?RS>LzRKV3v{wt)QY{)EO6-Q76G^|EW}2w5D1RM1t@V7CqEkMxzx-2z7(Hr>li3uh=dNm#u>L0lgyH|9yY^C!I7"
    "Qq>}db>Bh=n=QktFUGD66f0RKvnK+aTJr^stuXbPEiI0(RUx(Fo-Bq2?O*yd18L6-=`nZIy|c*{u#ZY@&Y>nd-9O"
    "m*6>swuk-kF%Q9tYI~Y?E5ue)u>apRFzfIn#%i!RJEr6HdnPl%5Uq{hR3&7wP_Q1Y_GOdwXIkGkgB%zYNMuY$%N?"
    "t$ZluK;zO08uCv$k37SOCcb@x~pWDmd`j@}8m%sBbe`ha$?_d7jUjD(q{DZyxqks8Fd-*5-@=x~i&;I3~?d82^L3"
    "^IL8(~9TOZS4N?zy(^1&!Tvt=$WnyXV@w7c_X!wRkUR@}6t+UeM@0*Xq5X*?X?tdqKnZT+5#aEr0G>{yb>;b8n2p"
    "L3S;F9<=<qYx(n_<<DKqp9d{}?ppplX!&z&xz9LgR%udBESG@kkZ^HygTPD)j94E6(!q0h4a^!|)JT~#gx;MHDO4"
    "9e2Cv#QpEiAF=+JkJ1^}g<QenE&of5v*v4uG$7+fnAQ8CM7*rO0Qfaf!e(bCIgo~Ph-a^Wh%9qgJv<*51$jB2-N1"
    "&h3DxmXR@*Lq%pQjWhP5d$pkM<<5^zr(!bd)O&M*Rg7(-hW`*)_SqP#Cq-(u!EyfILQ=^%>c&?u9*%T%Aqc!i(;+"
    "2Lx;pn7KBwuGCcsgg;l4kxTHbK7Y0P406o<i@AUiQ9lr$W;v`#Zca>}S?;}P2U+;VE-P)nIs-=5Vgaj==Cl&67k2"
    "iEqvQXhG-WMKNI`dz;r)hDZ!(SbW%RyAkg_=wN-ZPnWz-`yV(Cndl3jx}&T2Aszdv$=j0|?m8%E9tFPKplwpz-Pv"
    "_GOY^)9`t9hor^uvKnC-l{+rqF5oe2x8ubQ2aC77Fevid$pV8}Hr~r;`K^1UEH>4Vf<nxC1$w5ACrs04I^K8mN1z"
    "B+NB9pA6gHILRRbN?oyrIoQDSs^)kPqTcix`u|N3Shc{q~Gj1t_9)aePb?mhVRzvpWZ4wEJ1yc?<C_Fo6@Ke2S@H"
    "utjd(3)OjI%LuijLmjX_`Ui>{dRou>h#@(grk(r`Imc+3K~2~5s^zfMP%?9EvzSvu6Gl9l`#|@j+-8JBKXgKMkxZ"
    "K2R_BIf{o*k574{8xF(DCFI47;UgdL`@vY4Yo+jDK>Kwgl;Y;)#<WA00i$@&oiQJI?x`Tx-=RjfJ>ArvVA-uVaAi"
    "J#82bVI4%86Mo7RkrXcxS+@5#=W6(B>tCp$o7lQLzI^h}{|Qd>rp|!9Hq>YIqIf3grF(k4qhFaOI=C1YahpK0;6("
    "24OZ7m@K3gfVY@{>f7n6e;ZLZw$uO@r}|rzt~Hk18SmIiNngc@L8@-ve#LMLZNwO{6O3K)g=wr)mZeSd^NAHu2Tt"
    "Sx+%SP4a6C04;>GUsg<j}_m;^TSR1efC()YOX()^Zld#*~{50}6xdK(cpEHTJnCRp|B0VRl@V|emav_=F*s*PV9k"
    "`sZD;EYlEEuzVMo^s`7eul7lj>h+vaUjkwbqU}u-d@H#?j{h7LjQz|%X^s}Yn481pN{v5W1dek1Z}ekddVNunv}4"
    "kYjg=Gp$}dmq#gZ@AGIAt&NE0Df3#ec8v>Aej!n`rEsr|xqiO@`A3bf0d#JO0CwhQ%VUG@V#AF#6m>(on00K7JC1"
    "k7<Y-SguT*}Q#k9M)HyW2!hcqcKuPVA$VP8XF$m;S5h2;L$*r7^;>OHHa)e7wUIi_$bGoxb@g$;wWV-@ZpCT!XXn"
    "Ll@T#ViOP^ZSMT((4aQlKOxR2Kg~J=RXh{qF@w6vVDy56U@VtDE_?P&<Ms==Y-<xj;@wC0Z)x)Nk$tJJK1ugMllk"
    "wSnn26l+5aw>e_YJ4LD%uc>0-QN19~V~f;P4aZh(gBlfmxn@V)L`u>0^pagF_fkj=SG*iujJuU6?st(YjlV`xq?O"
    "5ie3FTJq+7i`9h^V<yL$K7!c{yPG?30ugnQHO`G)zha@7C(K87C-4u%$K1qb2&-nNCQC7ZCBj1l3HnsBwdkZ7J#h"
    "*Q8~gC&KbZFY%80Qr?L|Ah^WkOBV)6wQC=sgD~91C5&+`nDJILF6@sQBuSJkz!cI+?%5t2gt*6tSf_v35ksqACd2"
    "@W>?Jf8@B$x20d3XUNl$S$*>lJ;G&`Q2wNK+zkq4gpemLUK<G1?4+b3Cycauh`*IL9pZjt3x%uOOr%yNS{yhE8*Y"
    "?eqe9Vu2gPX1OvziU%#is5duV`@m+APzW-NBVnC2#pj1}vvn13KbizfmHIziua%{lEbO#Q>`H3hKP#tWBDvBx39w"
    "7nWpQF4u^4z&kk@kizEpV_U<1Lf(7vy?ZvmC%Q&U@|x17l%$y#kh-4;c$?en&P?q^iF@eAV}KboSphjr{=i*%35u"
    "BvXpuCTxDzkYXgt~!5d2t3&7HNR!Q(QSC(a~ilqE59}r_nfD<mw9&j`t>jS2Y+oG;L0hR&VU(E$UWd2^;s$NU1Z^"
    "ZvN3%bWdLe&`%ki5>Np8@pkv64Q|86{x|(0t3HF7P&l8B0*brgru$!d${93(x3%bq8MIfDPJBQE&S!fF6$&0B37P"
    "BCN-AX`->z#LVA#30Y8wrd;&lsq&!~oNy3!G99*eT{r7(m<&_Hc-3FLkJyRKsf~g5POt+BK4687U@!EXwX<&>34~"
    "CYb1|qnS;-&opW%XTUMHlp|k*j%<h3X)Ty4i4+L0_!rDygjAujC%N#fnu6?^(H<dEKUbW#7`+}PMmGrStGxfv!W-"
    "lP%Yt7bqub=c=ML^8<wr$!G|P>zC^NhUe74l6kLV-Dg{JHm7&>L9x7a#eQ!jPNhklpvsYh{K_!m&Ycxj;GWL{FHl"
    "KpJ+LH$ovn}_4rLrrN5dpP8<wuW3opRV=hPL0%GzzosB%JjS@H6LgBFao(X2Y_EQe0HSI;L$NzP(&?oAyv&ot998"
    "4SF|U9y<YM^2nA1)xcSDg(rrC|Sj!?BHg_uv3x2xU&`<b0N@+ca*UOdZ2m+V|_6UY95XYn|kHDiLd4b0}!^fK|Y9"
    "?t?ki4A3l1IL)Jf-I^&1z1^cBaj*T2*%ZWs!yrf>_NzqA|?3;wOu3Zq$R?g`@u7cK;-SNeM%PH)vMU<JE^A(<j7#"
    "{73YPWmf*z4X_s`Tx-!21Q|*AX@jd|NSd3|t`=*cFlL;Psg{N+8j?3#k1NO82I&+raV?M&;;|Ux7pf)MvodIWrJA"
    ";~yiPf108j=p-&?h;RgQM&uE(t_+%1wPmEgT5x<Ss=IG04BVL`&(HNBStZ;ENX|Bh^J#2;HNi@7j`GSY)+V{Wm5n"
    "x3AhgVU3jua6Hd&{chS${?R<wJZYXFnJ-S?c`1;hTjO1vd+sjvQOu?nc>uJU~;JzwXLITb{L|Kj7p&iO=`tSqzaJ"
    "jVAe0`xz%RMfmN}NA<2y<`vmISo6s=AbBlRg`~JDYXCsCg?8DUu7547I7q4bo!T~9i#{$5N+O1L!)_3FScD&;aHG"
    "oLnP^<H!3uQz4^+#A$Iv&V3n@h9Y-rgJ4+WGfnm%m5!Soum{N7-txN%@bIxE53Q2gqD0TcmEXN-(xiwtZatJt9b+"
    "<hL0_H8yuFJ>qb?y^t-rX~f;oH}`Lg56|}cw)>=@QFEZ*o1c{&>Dx*gfKof&VTNRA{>jmA<DKq9Uh?|wv)*vs_`u"
    "hKzHWYJ>x?t{(Q|9jI=NW+{zG>3K*9DBL^m8iD*Ch(>W(3eK7_Ym8^eq$#4+rMG?5BJm`E`}CDFng%DP$e)_5leX"
    "-|U&{cj^o!$|qCYfHVsaUHfBBN{a&r6DS}AU!pg+N~ZYMA>hv-ovIr>kN=DdsCoB2}6MOy7UihnyrGOVYc+br4f7"
    "%mPUPDuQ~DMc&F=6wP2c&cX_+t>5TY|#RKDf^oE&gG554(>h?YM;ObB2>eqwX^l3#M?ex@+Ddyi8<SPaYQFN)Z@*"
    "9Noo55<cGgLdAUwH$}+=y5N8Vb})GRn8C(FIZ@5i_X56^QymLstZ}KNcE{@Q2A{u?D7?$%HZc3N3~LYIL}>Gx}P`"
    "8X3AnP*t-0AJI^q{IvIz4=vmeC_pTYA#s%pX%VnfiBrc=3LIm+`qkiVt><ou>8+lyZ?87hOB@eay__-B8oH=@@2U"
    "4UXm6K!LB%Rs<Jd2DCO1td9CN9p8o3zc@QK?iz`xyIZ7SEf&T1sJuiW=5uSP*zs`HMkuST{d-V;FA-02Q%e=o*6p"
    "QNgH>eKDj=1v_;|9#@R+zr%;{s<TR?~((!bxLDgcrc~?DCZflV?zKlW$Hl0RDYF5#6yYj-OrrFd=+FPzam~0c|m^"
    "j?Q(-T+W6*vwz1!;v}NEjkkPY;)~DO}coG|VGSj5luFLr(16W?;3xEVn?K?-%{xecyEn=E89b?~g;@QyFp@+%1s{"
    "3SUPr~`?6&qlxk29kS%KyeWq7NV$bYUbt89`%a+U11{jx3mCnFmwSM4L*kciy+WDs+-~M4bbvj&D$D!j_DPjEq|{"
    "vKxd8CmL~QS}bim+rHn02OgSUxV;6R3YgB+eH$5XVgt8J4yZKG5N8YaEphg7_cgFoFY;m;l^wg8btN3`A8ORrK(U"
    "^}L!5FE+0#5CL^7MYx^@HTq2EPD|3k*>LjY0cmvN3x=J{&Vq4W9Z6TdVB99#!NAn!bgKd}h~Q`G_cy@?>EbH)+fK"
    "bEf1J+*ZZgFZPuJ3KlA!Z@#;b;uDn+3Og8%2w6we~cU~35)$u)q0b7M7QZA8Q#R%PPgID`UA2CYIbbC(eOcUm58("
    "(ED&%ZGmJ`b&s7Sk;1@h}m7N>y5})|V0-1lP$<P6el5?_bm>wrlrxYPBQ7F@fJXZ2wMdm6^W=%T*5bUtKbP&zvQV"
    "s|@N}YjE0oFE6W^(r}BH;fh87~=B$Jqgzdq%c4@85susY?9T2e+`O?<PD4I#%T8NH$OSwo(9-JfXR32IeYy{{0V~"
    "dt?+Cfr=90?Gzy}&>4W*I^FKzN`IsZbb_^x3O$Z)r-6`MoJww^vTB$ON5QBB&@Ez(0;Q(_Zwny<h5{Wzr^q<tO^y"
    "1|Hh0ky;sVrlQXY}e$gcr0fd)YwP>zIen6l{Dhh@vLb9Q8_;E9KDZ;Qjjeb6(b@MPtla$BJf*u_p8@xOr=iMwuO|"
    "MI`cwVyz<M({uHCXME(GOIp`Od7I$9q-tZ;iCHtVueW$-5E+1@B9Wg?cCum$FtO>6>b$VV#N()%r9V)#z^6rB@1$"
    "CJ=6&z1u^i;T<J8$IsJ8o4FAZD{nK2n%OrI_ZPnbRjd_@!`Z;2W4wCXHpXdG<5r&zPd-TtlhD$wlM#h7lIu{Si>E"
    "gG%xNa#B(!M0Ib``$V$byL%?|Wz9YvjjvywCJM*4hBqn!R+s(sNH(t+NT7YC7=0Vdb$NQYz-_a;O$*9>IC+hi8Ll"
    "BvtJg4h}fhEPhKD{7A*9xV%v#6hiok0bJ;MQt0xA1<>Wq`)41>V7%ItR{&}r`m2`j!%P{t5Jwh38GPgu`ss5s(Ai"
    "B=<k|acz4?F}_q7JQg@Txz{fk#*D|vPL=7|1!y?^p6|8+3ge+>ahP&a<bm3L=9HXx;sTBI{+PzZJqgt+UdVx3jgC"
    "TLbwX}OI@Snm9`YS-1-%}8gp7ht0qy^K<$t9POmuHt-MuGS@myH&7@`eXBT8ut<ZTe(YuqxwbJ3^-uHHT!}JIpX}"
    "jkTR$e#lR>hHn@Zzlk@m!yz`c4J610S=kuUuPrJR^jKCaowI*~ez0hKUag-bNg7~x#DnLiZqpD!~27nQm&&pyWS="
    "r1I4~{+&bzVrRwr2ezx>ad@Y3daad&OwH!^03f!qGg~l|j#+o}-2JYxJ{CLycr;(0>@M+T82VQTV~`SLn%g=44$T"
    "WgUQ~G52B?+g_x!b|MS5cA?t?i85qMUy5wR%ypiVaiX&uo#rd;r;Hx5=(n`q!>YKKlsS2EjXcGqz)9vET$=V$MPc"
    "O~9W&@L`yb7kOs~r#N*$-5H_IRth%D&j2S0dy92g*^6(BMFqok-f-~$YLe&FSQzS#>pj(vmh+NY}ZJHgWM{-EaU8"
    "t(wFl6wGt)gJLe`{X%$$$R)NsE~y-O!5UXVZ+NNzvVMKDEb}vb2Q#TbtO<o$2)eI8rxLld5PtfMaMqbtyNsukf}Q"
    "lb6h%zM$MUE5C$IYM-&f`m{o4jjbcj;XLHy_nl+6zjFSQh+cr{7dbVE20=1OzDfNxLF{pPA4~l624X?UmMBCe*FS"
    "z=$yVY%NIMt1UN+D-qQx6an9d3Er7>_<wYeElnnz}?1T63)5P&N9Ze<5fxsQpQH+2axQ`VGzd=*l8zTgW|2-ygL2"
    "q2C!T97qzxANSM@Fwq*56mWpXK=HgnkE@GK_0rU)(fk?>2w9sSReJX>IC^*|Vi6X#Q?L`0)=xKKZyEM-hkp!34Q@"
    "V*cPeg1`f4@Q4hwkD0wy8s*R*<*2wd~Rj5@HwQ12Utg?MJ4e}_>*dYR06)Tr4w=+fj)Rl2KtoA0^`eG}XIup7R^o"
    "CNlhylSbFs7vZEP{=Zc8T;P={=#_<Xs*$CXI(D(KUps;or2MO6BtbV*V~LCXcca+Ar}RKj$XaM{X#|DVV`fQn={A"
    "Ss#J%DmWdsq);+s<V-EaYe2pcPf63)K7`l^d6JWJ&0%8&k+4Xszg!4m<<a&!irI?qGF{lWlXVkDgi;}_j<Y&VZ6X"
    "B;T^kU?-HF#zXT{imU%W>CfBQIA(UZ|=?gw&O|*<9kt;zr{g8th=pv~-)I1j-)`&+y2O_+S6?l4k<VMejd^wwe|p"
    "V3&X6Y;_YAl+tTG!H)jpl*+~-lS%lfxk~m}Yv1tpSuRhG|F(V;+9RPD>N8Kz!T`TeyR!xYr>6)BM&(K7SFe8Qfrp"
    ";)&OYU3r>G&0ZGt4lQ5HwY&%)b!?QAjLITBiGIxKlAxMcF>TK<#NaVnkthL}QpowezEb}BTf&inW!Op%4P#}g;j6"
    "OTug9`<-Eww;jdQ<JKP-<$BZwWGj1)d^)qS7hiaLbgQUf*RR(;jx(wQDBlJ|Jgxw6D4T<fABEcBkMY|FE@?Z%P2{"
    "eOVqMVC})&AM4G0znvbFl4<19PZJJUBpx4JJ(?Fj?7!4$#-O~R~V!9?Y4S{!lYd@hzWREm}*Y?B`9|l;itn}O;7A"
    "nmhl)X-_SrjV+U_UW(9}Ayg8x;Lhb?qUxXk>NGs`^JbY+x;2>QRFv^GP>aUN%t{&+?CzJ&nwbpul__@6gf-#YjtO"
    "m8VAA-)g9FQ!DBt-3@dMHFEo7z~ed!t+;lY#EtJnw>90-H%5u>_(Yu{wtbPWF#)v(%23rg*aM=8HR7xwjRvTqoYK"
    "mNXYU$ydhzP$Ov)nBhfkxha%rse0t`8XxQdLL4%}MH*X2|tnUoRYzgL^#uz~>}s;S?SsamrgWTwUKV(UXTx*70GP"
    "VXlLn@W^F@+?Rpabn7KF*9MBK%tX`$WXikI35^2vstD|c1?+s63)3IWntHJ^x$$3HUf6r|Ii<qStm}4KTo?}QV0z"
    "8hs?G?M;i`KfGoEvC4(6zU_svxC3MNIDRjapggWP#UMU^e!Pm<iLUAc4xlj=-3T>`9yP*v^1^kkY)uogZ5-Z?h1d"
    "y4K2?ksud(TG&ndB|;%sNw@EHAHYyvLKk{6)bg@wyP)DrI71Z<s3cHRg$`%m&B|LuGL&MPk%qoy~c^LK(9>zXmox"
    "WM;@$>y+q?N~-cL5rgGY4EGBnAhBa)WU*sum!YL`1sviy=d#>Jh2T(0SxDWWKdxY7>H<9?ddvpJvMjWos&xh<hH1"
    "cf7U>LZ&HX-RO2)Bs(~>PfJj=5UQ8Oi==eWr!0N_Oq@yi$!BZa$lGQR@TBRs|_1E4x;rZEo=O%Y=Mfd1!6T1LgCE"
    "^Ue&JAgPU5&%MPM=7V?8mMVyF*BtJX~>fEi%OC~gI<BDGquueDw(`wCb2D)=ZF+wo7qQdZ?P)7%QYz^P>tEzuGq@"
    "#0)i>1B}@^>IfyB#(He{5&YNo(Fb?~^ar4p6VnVRyhT~o&%}|=>*OYUO(vu={vyM%*Wk_BZq{S?Bx<M`;ib0yAQ)"
    "1T)tnyVvw}Zq?xbdOmKe`>z%#+;%Lp$KIzyz?uXx*e@K$3O?@-W^;k{j)9BS(8(OALYXgfPT;29R|~ifFe9zbH6~"
    "m52ymBp>S`L5*8NAcOtFPR|aHPk;pc<uT+<C>sWpvc|}Y!`!j6BFg4hemT)BzwubG7D=J0S8M@pLFxnthBK_@X;7"
    "hcW;0SmX+;8bis-gGr9qT!mv(_lF!&QSJ;}@cL-{1Sf~Me^MDt^=re+Sgt_oNx%zi^m2Dec_swOMQhc)9sbzIyTx"
    "r_`SX@W{r#$ne$708N-0%KZ@;GVh!>aLi1w1)hF$PQQJC7>;*LNiBhoT(hDdmQ&h3^+kc+_~)K{_*RhLj{08Q>Gh"
    "C_B&g{7-2WYYRcyeUe7>{8xY~G^gLN4^B$4r#z}OUvE5$Sk8sgNz*4IVz<6N`0=7D7agP@}^kyDwaNzG6mx^o!p?"
    "L)o%9S~R-2)Q6Wt0Ml4HS#3Xr=ueyZ-tIEx}dCe%vpKVE!|tG=j{H^EocGfjYxZq3lUEX4Bjv;RRsNF{5+PKbY;8"
    "M~wwNs(CWpwtKIlEKX6rZ<{taRnVU8#*n@N-EHhZ;y#$A!Q7!u2It1EvF9v+NEG>vHa&9r)uvOKhlPN>9{QIx1Q>"
    "_G!w#hj?^Mce4qUgN!0!R;`QM5=Nxa-FFPe^`6)9yc4X6TmqNW3z8YIvzyPU=^F%2OqqT9h7qYa%^K2d*QkWIAED"
    "JB@8SYpg4R4)rYN#tBvp7mW-vOETnSk`10q&96Rr>gu=CpXG9FBm0iC~2PRsOSajlx-VsAH}#MN@?mXp?X;;{P=s"
    "HVXGlUnvz;$8m5whLa-ZHZ!WaRXXqf$+q%tMkmcFL_Ax^|(9+*%GpO#{eym1qqp>H&?R?1y01;b1oK?O-_iGHejP"
    "heyG49i0bwKwU-qJ;}^(|c#7H)_jW(Q|<qHv_JQVhr8pyDCu^=TC`>E~A|^ujZQcxQ5YY)w{w7e)YdiQqoJtJ8xA"
    "&GcEq{VvBA1QxNVfTS@P&j62y0e19wJF_Uqh%iL6?o@2`tjT|$nlFdA0E&mGpfKx?TR677u{}nW-NG`0?lpU9>x("
    "kR?mfBE^4eX?^{r0B20pQFm8aNELHBoFR2x$x3<@jVKoBIiAgCLk#kesYx0dBu_#0V={Ymf5DLMjq_x^44kOHfXh"
    "u&*qIr0};wb<}^Ty27|qet;lRc7$4hsm8*qz3zJ2Y=6#jEXQ__3uiq+rBbHE<%BmVpBte0sC0nU=jYa!v_CHC}qf"
    "-52i+OQ&kee1u=FFB~;v0t<SBByv*l$I>`Y-4<qY_28P#L{#ouoXagY)o5*A%Q3Uh1W9MIDaByq$#G6B*-4eDOl7"
    "{5}nj^*gNIk<M{JM(D!5t3=N!Tm{nOSF&VvonD0q237m{F<4jqZweWZMnC<!(JU0uCIHJ%`%XIKTKYe}EfSN_DiA"
    "Wuuu;`8t-Qe@)1c${cXD%JR~u`luePns9)v)nPW#i8$SwUvX7%m_J|7s15qRjnuPYyJr?Zo#oj-b&*d1RpWoS{!w"
    "4ChNpE*)&d@fPqpvgSqu!;&#sC4s$?IW7yykfw^z%r)e@|pv42J@i}f79xG~F=uuAu?L_8{bD-l*4tj7DAV09V>J"
    "z~7RR}QL6A_dtSHgTKk1KS%XWCVhCgT;g*n-}ZUeTxM7=Qp|{X)4-J^RRI<_|-?Zf?juY_F?S_(zjh^ZLMB?jXkJ"
    "#TYc33uYyOszuPe+>k2fZ4kKxTjo=@3$O!$j4K7l>umv_!`TfVjM|wQm?SVm#hslKny_HxXw4s)po?rxl@Ihh^#f"
    "8!rGAt<x04vDE^&JihI?oZiiXeMnJJ67w4aiuZ#^?x}mrt1xjhzm$Fh!uYvW${+mVdMfV^>8Uujks*P(ksxNtOZC"
    "`7y*@o4gkgd-urJhlNo+))`hU8{*mpTdI1>-leCQEK~BmJOz^!*A4=Mf$S=S9QELgM6YRd8No@vr)GK{fdilJpp%"
    "4df#qPSBQ$=3tYR*2ifKxdg~rquigUbk*8y!<mJ{v3O=7?*lcQA$ECS=KGX-AoZ;ExAWS8cf=g*%1(0}$*|M?I7J"
    "kxzHy}!~$pBC3Lp7zFB>q{|`*hXo8oh9XWeHqGSJniCmB3Jq{hdj>Y!i`D`__r;f-p|Y}#3iApQKA1I0>OGJN^he"
    "L(8i22%-UDzew4+1Aa#>|Vk!|fd6UmKG4o`F2j*#^(`Yk52y3V7*?`wLDarYPwyn4il;?eh+C~`UIL`J4>gm(p&^"
    "0SnUq%}oZ64qMRz(8V$SlA8%hRW7Dy(iK#Blac)i=1#riBL47~XNDY5w)WID76sEvp4SP3B3erf0SM9W3Co7a~Oc"
    "FHfJ+SGVxYeWRu~x=0qAhMR+N_AOO`xlou9j{Bj<X~J=#7rC*nB4pWtlw-C6&}hl8D&k>E{%i7U7Eu=GON=j<5qW"
    "!jIDr3AipD~N{R~TEt8c!7bqcG(Y)q+_FDQpws_i)8d?QSUVV5wnM{7wBpgCU1kKI8NUYS!;7_j)^gnD~?INo8RI"
    "GJ~mdYb85YN7k2R;TBjT80J(dHR6_5z5Kd%Na7>k2At{;n0|b)Mz}TWcn6eoZyp;)N~FGjbRw9EHKay({a`jp6F>"
    "qyy1YM8PhJ9BC+9pZ1hHz5D+d|9nhDkz-G@@UXwx^c+B+<QO=lq;aaOXc~>GzCy!neaDNsA6FAsEhl~Kg3y3Xz`t"
    "&791Z#NCpmP`~GkE$`?ITQt90?ffsnQ%JACD5oGeNF4=X#fw0Qq|Sm4G>WVBq4!Ttm&-yH749Q|2oJ-VF~AfYy0<"
    "8J;3uDuq*><rum;!KnuhdZV(aDDqofP?m%^S)k5V4%wNC1#o}PG!Te7$TirtX=-xqca11n`8b<;lz@YF{=^=VimS"
    "@D<}Lbh##D49^&=00Q)q(ldzNV5cT$zCv{|tCk5aVQ4G(1$xI3W0fjZY((f)9=hugqUeYg3@j?f=x5V8&v9ySN|7"
    "HDJxRT612@KdaQR*W$7L)+i$H5hz8gNOk5W)L5wjTaM4m+pxfrU2Ghr)BiD=xn}LOz}87K$`nei|~La_75&j&nB;"
    "r_Ro(d7Z<P9$Tg?4OfpDhGWxzd&W`^3=-?gZ7Tv$NIC}H;qV?&$@4X0yCb{2fj6mC`jX?GkZM8_}T5_@GlrY^A|D"
    "U)WV_4lW+I9={`vt;X{ET=$6S{$XArDo*KHgC|JfSnn3I=ln+*9=18p|lS@oHUUU6gMG7a6E2Ow#YBjIqcd!vL|#"
    "+MU3IwiJ4$qY`uTtYE1mbKQ`2ly&$89?9pEPw<5Sex`$=6L*rm_&@FB?ktM@pE{Fx8^Xw;t?RXR`7mXKWN1j1pvV"
    "R#y4o{NKSG-?Dv~xgY{0^ZKJd7RZZme3Qf7O+XCNJ{f@5r|)iTfW5@e~u#O~5B<|-;^h$#+{_6*`Uf#3CABVl-hE"
    "J^OhGv0LpnPr?@#EPg6l2e+iWTkKxat?{^3(T8yt#h1x3tKDRU|Dlr5&}-9H^pqF8+D0JQ9P?~b|cbMV%jMx6DZ1"
    "fYr)Th;esp2{L1JQCn=5~N8Uy%v&6&y3+z7lj$NbPtzf{ADMU(<NH#An#p?j1=B(a9?WXq51LowBjO0EI<QL3Lfd"
    "1jc^qipFGrth*lmG$Kvv(&a$0xr|iGB-JwBdG&V4G}&gCsI-Q#k?1j1X|vU}3ogt=3*kc|yoJNrX&rt#*A~fd6*>"
    "^2w-LtY;Z873@Rp48e0V&|YjT1F=qf#ZjWfWPuu-#Zvk_A%-WbByc00H$pU}s~hGowlc#z7ELPhW0qtwpGu^1Jba"
    "$*!EZFEn2_N$B9)bCw3&}u<}|2}TMkV!mpKhe#E>^sx){@R1&Qe*S%yFgE@utDUY1OdnV7KKXk8NmR;anytN_N3r"
    "3OCL#4L>u!r^Yy(G5SlM4D|6B?!tng&#0wqz2p`1FW#>kkPYIU<9I~9=Y>%rAo_Cf2rglV;tAOrbP$gOy#$8{K)|"
    "f{z26x$;viDKcesA8OXa+ZSU&IPHjiqPIX}d<h>)#X=+#3^)#LhT$-isG+5yRvXc`T0Z_OzE!+uOZUqpB4V5mM$h"
    "agvLKl~&lqIjsFEz}&1`PzV5a-2%Smk_%K!4Zo5dBdbHDHAlkROJj>2$Zy`q7#iaRmoyWXdAH6}PY)Veui)*BGc("
    "Ks`q^-CkUB-ELEvN5QJV+2gdUFqsP_a(OTv-&4+l?7l2KgdTl6u@PGC_HIDK=jCwW<ScdP2e-Y}8LknX2BSSu-ua"
    "a7fx$hH3H)&Na`;jp2|N<O3Z-{ItmjFI?bLkUgOwtjG}&H)PemRS;MAS%1-R$D0=#+FU{UM{6{k1b8U%4~izMcIL"
    "d9E_>Cm0$z~>#F4JB&X6NfJLN5VE+&JGt5X4a&f0hnQ(%{!Sjn@^?QQ#4?Z*})0M&_dC(bQhk@cIX5o;Z;QvR!qP"
    "Hbx!yeL-~fYoKh1JPI3dKvwgxw+!XokuCaTp(Rh@T9UZM?0=%B%zRp%nF(g^Z0#a9d5gyStTV<LX+4$+B?i7G$+Y"
    "sSR8;QEO&B1n!suj(e!YI(MoPOl(DAkSRg>0jNi^MoDh0RVEX411H>!?pI8@7fF#T!d%*2OS)cu)aiOcMF$Lo--_"
    "hdXx9vBU5#&}~}12voUM{|-~!qsf!a>H*yCoJ}K;wvbw*x~@RxR<b(Kr8?Nt6Fc-sP~X4wJmCSq8%n5)d(1}dmGd"
    "981ytzZ8&Z2$n$dtw!?rYB&+=P;-)(rp)#siE?=Q;kWS{$T3-v~_5RIV7Z&5o#@X+UGRsWnUrv4OiJ9B*m!b#NIl"
    "GfClNd6@9Cs2E4ku8}|+cA+_hT$`2)O|DS;nU)?XWHi#{eaZ34@E@X2k7^J{lpsZN%|U){E6|-m!>4kSCkPT9#6H"
    "xhu1o)<DJut1-m<v((dBCniBLMp_vJkmM!H~1J^y*bH5K{Rtg9aRllF3(X_Rk-=d_njsaGz<@lcS(2{1b=3H0qL+"
    "y(LV-DtIq03Y>12<zv*n;*(`HThLdGt!B%~_7>JbCy+Ob3pJ6M{Pzbb}KJzt(mHq1!$UaK)MY^_0T;+52CpEgpRY"
    "Fb578XO@Akr{)jTTUI^DbQP#rL+d{Ejrq<>i>F^_&1L8WT2`Dfm4bKRG~DmopgXa^McJiON^uQqqdE&m`GCBh6iJ"
    "MRS_}_|vUA6EXtjl~bfoa29QJI^EL_%K2@l7)Y$(@o&EJh79-<CXU#N%|5yW%mD$TP?U7&f2X_?hLFN*c5{AQULt"
    "bvZ%p7k&-Zkw9*IU3&AP{+QO3e}|6;f<PRSJ$puHlf;HqaM8Zf06QX-)^%Q?;MadH=Hhc7VbTP2hN6~!aQo0qY#!"
    "vOL1k_t6h07f^?3T;AH1mQSEI;&E$0eFR({1O!uc@<wm&1aE<dGLSy8XA)20}RJYal%QrG;bDz~Q@7TsJ0Pu4s*&"
    "4BKO>ejCIsk~MJ>UJ;ZZlMqdp4TN9@DbDG+KUfGk^%HU>o=qG@A7)n0g!|DMkZ3SAFXNx*y2RK*f=?OUls98jBAg"
    "i^?@HogxHgagT?`Lz(d|3YkpN#DJaD;FW=l@*E5pDRY$<WgnEa*e<7zb)wjWqQL9}p{i41c<)twR%+#u=Q={2E-o"
    "v#_klyxcZVRwqasp<f&*9$QZGy^8~D^BrnnP5_6&l=1F8k~lfL+J{PuXur$+=52d|GqrzR0EFcgwKF@~U1U1gHx3"
    "e&gBf-=Hk06e}z{*<QbCW)M{1_K>x2)lkCd}q<B2kzv##z+8JGTuT$3;-z=ktschdEW<Vt&n?>^a>WM?N+KZxz>^"
    "^7PWLC=%PtY(8wXNg-~p)XS_#~>_Yu=dhrUG11jh_kbPBmI{DVDBEhSawF&2G4vbDRsEE9BQVS78qBu!^^F~2WbX"
    "a*R^lYOr4z{Zzb$I;p<<Z&E$%VIMv;4MS?{AuhpgBW2fdY4cGZaB+n8W_Ed@tml<0Q0PgSbIM`J+^h!=u+n7e@~="
    "y0@zkbp_;sO2wDx3M|zdbcMaTg}G?~{Xb@EhID;#0%($ZT=hJe5P>s9av3H|2pYmW4lB{PwfIh6L(2+;DcZQ%@(a"
    "S6A~<|Eb^|UrO7T(JiWy6Uh()j}mj*p}C>}T_lPlL?xNfvrd*<q+|9*RXc65j$03@e9DsU(YqWciWgln=zO7O{n%"
    "nf$?b-hOWOo!OIBs(@*<B{IS1AtoufJGMC(Qz@))}l}4vMNQP?uB7hX4fb{qovWxXd~QJcqRjB&;TNU<K(nQJ_ZZ"
    "Qptj~{Ux1!J{q4kp9o?Sep+?k2z`4WljN2=_x1`ctPO4(9hbmdvu1}1|)zu*9d+-phNuxRrmDJ-2D>1qRI_kcled"
    "acy6Cdj!7JuZ!jopc|fDnJ7wkY^e3#l_aVeXrktU`tJUM8j-d>y<R4OU1Hfnmy|v)lD>L39U(i6wf-tC%M-oqR#5"
    "n(6Wum3vfEqS&6+u{*xu^+cr+6B(Z9X{QYn3*h3+37cyRT{1fjek}1$;t`X^4XKOJ<$}sa$9`Rwo7b(#%44^vb!K"
    "cQ2xXLN3t{kWUIh>;5^;n_L}Dc(YVHf)D}+Xg82L^RBFHU#(ZoL{l9Gm=sD=<R6J3M;gS`wxlBs-ECQBBcs0_f^a"
    "CZ3RGSB*RJIt&GkyeB<C|l&kTr;!=*|!?O0tImtJn;0ASciKps9fM~^<8&V-;iqV?Y14yrfiyRKdsBxD<=E0Oh;v"
    "zvS(_9|8Lu!n>@VteYUCm25>^{L{fz))Brt{>8pac`y#Z0js^@^sMQ9%lYwG1-ubW7;}fr1AR$gqRMd`*hk*ZRki"
    "?a8ST!41EQE&~2_p}!&;84x5mKiK?4pw*zXcyZ56cs^kEID^A#Z2P<g%c3w)dTi;#gbGrgXgo{3-H*s8x|<5Y+_Q"
    "*Apb&BS{A(5&{m`&gdK{+;${*IP}d3Ddow#*RMs(fU+cTs}=GlfF!d<LN$@u$oh8)$F(aAaD%e&I>7Rn4U9#eh`N"
    "F5?|F`F{f~8&5_{AdqP55>0Ok0gAQnmc?=DV{PY%wG-oTE;Xex@)#9h2pdngT1Un2DM6P09uB{B~C1a=?{r_-r4i"
    ">RIep8(YXxlxJqu?-V_Bh=aZeV@ckPKWa%LQN2DYM0TR6`{d6o1C0Ze3kc?<CDYVlV8<H^*x=uaV8BV+F@{(-!?A"
    "Pq2<<@czp=L{2nZ)0bw`Z3G<Lv%MBxZo6~HD(Y^e^FuC}L-v3_2P)pB@I@N4LWv9};UFJCqy4>HTF#f$|+`UcVe;"
    "I&@BbhnnDyM<}&<;?l?=|gb$9lrb#~muSLq_jAc{T>NJm~zn6_Wl-g1(g|7!U;HW)4dY`X`@+ra_-fdvZoV89wu|"
    "=^?mTI5)#X+Jo@ZiBV@q|K}YY46|Iak`5iH8Db;3qwmEwH<)8p=O&4^9Du)R2#M{{x6!>F9^zR*RgUsiZeUz%NNP"
    "xYur-^laJTg75NXo9qyXw46-2Ji(!{`fZ~%48uai}tCUZ8tS>u{echc#vYw`XRsw>WbC~JsC!Bcfg$4Glr01jobM"
    ";QzH1}lIAeh-_=^G`60?nX-|X$js_c$TwaRi`IM{?U7fEDzR$`j8^r>ph2|2W)~1SSO<<w5{Q6EXVAcX}{+}s|Vv"
    "9I5LVn2%W1K*VxCvh{Ofg2fkE)6__b(hTP|wOOkcI|K?~bxSF<h?%c9i8=|bvm%KtUOTCQ8MGSCesK0cJ*tw(2oY"
    "+UuB<=iH80t=kP?R3tQMTjsqyjk{NYA+1tYCbIwiYOoTs(8C?TMCL#nfGFCPoN2Er$AZ8Yo7J%>DQY(u-CcDrr1N"
    "8-*}X&I24%o-BBrC3m%P%f>$;q8l1iN*<~n#Qzr?<~*IFcLJ9M*nmsqhw>u<*e*{vmC(V1m0vN(GbzSB--cu(RN%"
    "DUtHSJAYHh>XQzS)xQ;VZP9$X0^VpcIHsC(OOlRff{Vy6k(zUxq{5?qvS$P8HdGO6PBs4U~qnbwa_+>89g@i`t0r"
    "d<)38R!TpL0T8+!{K24b;h*dU?&R<`%+fuEyCSF>`gpt7^3UDStUl;1+zde=qrrHsI(F+W@&PnaJ2r6C@vF9x{2b"
    "Eh&Fi>by*DOrKK2Hm-#ZnWs`2cK4g{lTRJE|z`?*L<%$i#Lo_@P@89M*2s{I|W3H>PGs{$}=-N|r99xwY^8l0``)"
    "HHK4K|tfLrASWzpOw{Re!ExD%xNYBniF7eLhAaz(QE$Lb#WOR&ksvjVx=nPgrt(YVD1?Hmt&a)BX<%2TFyRZr+7S"
    "Ts6ZgXiE^ouCZHk=xGn5<}f(AsW4wIvn*-Yv2ib{?AFcY$sQieeu}knn>X3Ut9x~Gfekyjw|V!}DmNyXq1R=l3j<"
    "V`D7ycJ*b!gFuaNkDHT;OP<UL$KZ8O8|pUY%KlckOZp8VQB_oZ3g6-x3gu=>3|dU>JH8hF3ikkPFtYzZ7~t>_lZ;"
    "1=s(yXb7S5<XD8?7NNaQ}FFT+@NdkvqS<I+G-+UVe@%xC4z35*=z)8eE0yh!|F~Q-#=enlbO11+l+O?inGaDwu0T"
    "kw_zk{Izh=is=eFdNU-;}>@i5oDMf$fA-6~E$og9A3VO>RSb%r)4uLbFl;ay<Y+XeV@ZBsi(J_qY8TQsXl^XQA)O"
    "X5~23lH_9yw&2%f%E!w>k3wvC=!!X`+eJd}Cwwldm&J8*%1d?D!(d5-{6}!}8wATazx$K=JNFf|+btO#w|#v;xvr"
    "7#5?lv?)s;6!vt#r1#@h>VmfeqCFIlTisN3AzjgNTh*VQYK?87A?`L5-WKVyCFG@HfqL6m!_5}f$_K>9d_kmDdpG"
    "@|QCZ`i{ez3+za7;lbTcgZGvM3aUJvN)ZSK9l@Rr@WVS8#vFgy*lbfs={kygtI5VWDmt?mTm`_4e##@TVNFSh4RM"
    "dzHYVP%mvJ6SB$)IC0RY#TL_kBZ>)KpBa(>nxA~X>RxQMw${xkyJ5XSR*aaH<tO54%j`1g9c&&JX9Q<zIh9<y2Ed"
    "Nd3}2D*Q3L4D18o6LWaQ+Q7n0jQt{3a<YmZ2XF?+9A7mOtymMbmPQk32M3r{{ObNs=M9u&U&jZp3B{OVuk_BRZl~"
    "F5Inc$gb1qjlqTVx1AWnv&y$d;IU$IvFsJ__1dp9W^F&NlK!Obpe<gzdDUu}#{YK4Lvj&=V^ysRTs1y+6xmdAvcY"
    "2y8!bver1JKF{ypzNBl~e(U;vu&Z9s9HE7R7-mpGY^@Dg6Tm8Amrfo0-saizOh48$dtk3UXhruzauQtN-Z6r@{{Z"
    "l{-m-*NEu-Svx3%u#*fDd@+ElHfo_P}u-63g6xWpYJ$Q&K`St7_}$Y%vQT0{OVFyA*3b2F7l=r^%*6objh@F!2sD"
    "Zy=GTq;l3&!iPb0{jwHnOY~dy?muZaG}>&$bE<%gaUFp-Z?xyIU4Uw9qLdd%9b`!7FKxs?C9Y1Z%1cGhvS{8znr~"
    "Qcoh|K{~BqJga)wz54C+o@ut~u5Qe?e<`D=tN`xW@Q?S0gn5J6YyM=Z?r=Fj)xg#8<3A*DoVykknO<s8IYGBsjBg"
    "&*f%?)?vW?wL_)ig2X`>HqiLm1JBvzrttt32EyZ)hW*L>NE;Y@vB^o#N@A*YtiMyv<d9YamtzK|SmmfJ51|oln${"
    "kg<7MX%FoHV4thg1>yOETq$myf;1wLfv;+B_X!fIA?xaDrK17?IMxGz{+uOp+}c8uST9$3N!}9?=@4A<Fxz|qUGV"
    "=1CQU~JyJB}~TI>>eLtrwi@i%m;ihX4_jMB8S8@_MGqft6uw4h?geW)*qfT`f~7K4N4H!TC-vWa>U*qd25>i3moD"
    "zOZ;ULX-VJm)34_UuwP623(bNgpZ3F*uwoM-&k^uW-GQSs4S6#P5opFa5D>0qn!x)Kh8n&jfT@VM@V3A4kqh<hY?"
    "qjche!jPr5;Q&5;k*PhI;iQ70r`*e8)B)J<w{YS`Em(PfN<&Rky?bK5Bso5|i+a@HJ<Z`N2reM`|){<?kk$UR00A"
    "*hUEc+6G*;hn%eKmyFSD~tEFavb!A*E(ZItd`}4w6ai<H1q=*ZJwmHy5XGUVrl@Dz0PD#+bK~g4fF=+bFot32}<S"
    "BRQlo>6ZM+jr|j3C)AFMgXq6BnMql1AsHgwDL1&D`Nn>>@z8PDmI+q810@XcMWkYmhQu7+to8qfYB+>AMrxfU|5$"
    "?<o2BSG<cjsw!fdj659C&+rqkRE3XMUj)9JvM446WO@+=PS&qpsopO8Zp)u?j0nqZ39k^S^wc@0#`tIn#>i{#^IG"
    "2R(`!q32i=)6>By?|Teok6)=!G$;}MqX8fpl`WSBkYxqd`RvD>^pcK$jx98gNEPn>NnoGosD<U9Zy#)CV9F@Dcm~"
    "H@!iJzi*#+SI+c6yLFnX;JOr6)^Nyd)%XK?6pohK9xA9Dt`mHFJE6I8-sd`+$%dDZyEtp-*pEI26(9adQpKU%==T"
    "B|U_52)-k}we&LbG!8yjRUmC`iB&n4AWf$V_8{!|Gw0GrxLp!P%*{R|uYMDjMoIDf4C8xrx%X9zp}9stD>-BlWD2"
    "Mf?a(kGSP0OU&AZqJfjb&aWX242zF=T_EIgnq)~?St$_ZXM{7D>d?dP_7g8*%FQ9^JEkl?cpDoIF;cDa{c^oZwHv"
    "GIvr$n*n@QUnq*1|Z)%R%GVGbwg0QHpn$b&)Wg}T<zd8J;$MvILZz^^b}Xua79lB8E#9X3yP=#KqHHNPF^v8t5{P"
    "2vpZP%lbN96a;>*@yOz`~CHhDj3~R2#%k;4G0hF&AU(6dUFSvS8)bTVA^7hx_5z_rPi}Nd=<=${}Idqx#hlBiT7B"
    "G58I!2%Y=HB2EW@@NsJ8(rdlQS9^$#EG5Gv_oz~Evt!?5)eYpRv`&-6(MUaIP)BX5~a<NR9)^x#3A~^sW_EiTmc5"
    ")G6438UnTrk0NHaw&95Q?daRBDtYV7%`R8`=WcM#`UuPfE_b1?C&xCYw3{bXSWskIHUC$&f;k+Oee!T$4?;dJm!n"
    "+7Ejy^>lS<1arshG4;XbvorH(g;XW3GIqm+t{so*17rDb$KBr@@9g%}E?wRYHOs~Bc;^$BemCCPZPzgg0*Hwtd`0"
    "tgUE+bTr_N7*Gd;y=u85u8DxIq$|GVT7`63OoU5jkV@IiTPq-1Xs?RgqP&)be$%E7FqwjgeGPn}_Nd+Hp>-odhQy"
    "7(<Gt^<-W$d8xP3myJ<=t?kfcB5UYQV1y}PESEaH?#<xVd(<K<t|pg9bddUeRpA#^LW%Pe?yG74RX`$<<TEkdQL_"
    "I*xi9oL@yz~z54A6!O8F$;hX1T`Akg~Gi?K9dzN9}AN18`ipkZ=T&&ZqN}x*x%wd^#MweXd1}t*`egN_xFf!Pj@C"
    "H=K61gl^5t{uFtX?DwVWYQJ<Q2yJqT>d0FsgmUNOyL5=@=|10O*0xwRKh|DVpwq(A{`3@El2EO(f_>Yp@|;&4;yt"
    "gH6#l7w}Zze8t1|9N_XGCC-H>I`HRcyhE>cAE<}=C@fJM>Drx38-NxDZwnmnJW-#d24zyF`Ytf3L9=_o^L-?|pW2"
    "s__-<N%2D2mhkKu);Cz1Bbe-bZD#5hrTrBa{q&XXtVP#c^g_=#;#%NJsLVL~Y!wimuX2hz&O`g+Z_4?KO3P5OjS-"
    "i>!q@{>C@$?WGNTjYd_{BTblK=ihK_JcRJ10p@>P%WmP3>cr{yQ%8npELyBp`u^&e5Iw1h73(0tUiFl^gR@if!}`"
    "TL)ZU8UAe*K@E#mJ`-g9i2Fn=Tg>~J-RA*)7yMESIEOG(RrCaljG=o<X6yCa);L$&B9m%E&)pJ__%R##b0H9UQd!"
    "N4_v=}*<Ss~U1F=Mgh9jHTHAX^qCHGbj1`{1&NZT3b7r?)r(ItxmLi_lw0t?oAe@eW?#dK>)dR=OKFFhP)o1`U*r"
    "yC5~T+i;!=PP?u~-+0A#>m5wGN6^1?X~_F@wF5mHfsg2IYc%UN_zN_1`t40U`Cj`JYe+7OHh?eu{4%aCf48>61@O"
    "KRP5Fd7NO^^}000{=FUC7hpZ*_CJ34&&)RrTuNI$={L&#ZMDJ|w}pI_QO&-V=!H<j{a6>QpelLr;eG5uv8mQ9x@W"
    "&ZFoKh#5+yX_kJm5z#XrlT@Y$Y06Tp$iE^2yBL|K^SHhChAp2uOj%9Q#$6wHR_A|%6>suU43SI3>F=V?&-7eb0nK"
    "&1%i){GjWbm@I%i*6Kr}v%wq)Ab@-)|(+m1EvnXX7tlk(B311f4AYDKyD&yOAN*qCOH80!^KUxg*w<{f`<<&-w*U"
    "z5;X9VOC@)+e@t}xgwjpGEOth~3m*L~7?pydi(AcSdRCM|&1m=g2g_LUtN4*#U=Pf39o3EDQvzg1EcAGDpGQB%ye"
    "Zl)^L@g+0M64@vGwCRs*los^S3r0TUu%lbd4h)jcF|3$F9LGEUI3|`}YP_SCk%551C<Y81!iATbQ-flybv)i-T47"
    "9TikdfNgT0Dw63kxLw{ARWl^rXhECqiaVCt@-6=J&9cx<<G503O1I#B>1wjhq^+Nj<}m>=x;;{53KOFU*^3LNYT)"
    "tOc?&MWvlg@|M1^3Pr7qq1Sb7T^X42-sn18$zTKU~I5>3>Ab=^pvC<<T(XyMi|Ugm&6COE)hO-iyXm_-1Zu5?h(^"
    "h`EA+7-k01<xO_0PIGlI>GTy;6*d?$Zxrk4A*p$(7g`}>K3mTKQ0Uc4kP?X;)$uQ&UoR>MCpg0TUIRv+6Jo4a+MF"
    "K2T2V*~bxI{4eBEilv^sSn4X6y0-`)~i3^P`i4BdkZm>onsrLvl_xpig9~jx+8~Qg85LAvpY4g9-i?)&Q+{4ojM^"
    "A+~Bk&GaSAfFhu8bOC2GPRYzHUX<SzA*oB8N{`5=`lZQGTa6go(v&v75DGlDS$NlwO=qYMIrp)#;|~eM4WK`fGKa"
    "ulkk^-HE#>ZpZxt|?R~)E47-xq^FZbWQzL=a}?7u#m?7zG?I-8sy9h{yVo~x1i`Ps7vr75%`@|+NTRboO&Jmtg~J"
    "m|6jlB`uSxJgN8|DyCQPRL$BPoS4YsV9KYevJTa^*`XmhX(N9C#RENj`lCkMKy-cPvENpJ!Dd+>Rms5TJVU;*Tr1"
    "dUyUyHg!_6(cF6EG7@i68$-2jo`Il98O*YyN*e5C`R0*{K5;5tU(I{wKHTXs>m-56AmZnn$5NkzLaDLo6>?uB0ho"
    "Rp1VZUo?;8J|T>w)I@Sd=JW|E!kR99@J8MJ)z*G2X!`gzflLDJqHYNMz6r8Y_$@f@k6LclBrt(8H?@7!IB-?vSCt"
    "f4Y0mc<>}_9*hOwAF5B#vO9=|=Y=ZOt<RA=)AcLBMb*0mr@Sp0a&drJa7(e29^6UmdK8J%0ZD<mO|lqZaDIjW-hc"
    ">|6l*ZzhTY{%s8HC%&cIGyTn+<q)(ch^^yWNGz?<EaDS5@o+G|=dC)2dK1rtZMxDPzlNv1fo2Xhog4O$y6mGuf1K"
    "U%4oTvXBqGAbZ3c$&=@iqt_SaU{*0Y>Ue^mZx~a8VzU|wMcZ@gj(YH>&G>b=H$oS=f&k9o(()CZ*b)1+n*WVbmf%"
    "V4%b2kqdf~@a}-hSb>8BdGZWT9GW@=qH@0pQ0t<G8B)mR*S_G^bsVy5DW6ig1T4$hv5hCtZi{OE2_V;ysNdR##df"
    "Tq)K|N;RA;V)KXj?{tz-eySLU^S*Jv%%)Q@{M~zj1hUe$caX41THC$8U}=)SkTj`MiIXPOHo@7K|f*m#Rz`Uv7`!"
    "8?E=FvgtncOw%1tk~h9spDUw=YxQZ0HNvpMtq3vK@y@ggz>AUU*ae~bQd)OV=4F)1SEc*y&f;k|z({+k0eRR^U2&"
    "GO`V%ay_OX(2;(xt12g5@Rll2+k0fS-UHu(f<G)hdMhCeD4c-~+|mpbHL`;2kgW@ahN)dZy`x{m^sor0(Y6x6RSF"
    "5Y5JV>s|D0%zd~g}v$XbRBD>4o}W|u=-+5Qw!-gAZiG(trTx^fz&Q8$HDw6Nn?eK!bD?T#^CvcuMN~ep%G*mrAEz"
    "*+(5WmoMartG0vjm@}{TK{L)Yg0pMatkg<U)ik9ku`fHM=k}7eYCQx(cs-J`T5eOz{h;_%P-V&^msnQFe__gsP<g"
    "*aQ3?So2+emSf&>8b_PG3+-e)z5#Ww=DQZyj<781pD~KW+AGcWLAPUKeSa%m$o%D!j<O^zegS3y6^pH<Oe6Op_6z"
    "6MkR-!zuS(Ax5r{t(g=cx;5eFy%h*b8ZdGHgHc|K75@Ql31aY5OLNJAQathakxbvNi`2_1T{VxpQ2f*LBj}(GXm("
    "T=Cc2JM$9Txm4x4BIR32uOwt1;xB`})P*Zuq!OLZ%(gdPr*&rJ{&<3zV@wsXlM<gDpgkjweHlw;UP?LF&BeyNYia"
    "=o13cSJpS{=@Uh-gn;#sbQ^^OrHaDb&wbc4J>tsztNSr$Y<(5<hvlA_ntqKJA3du_%J>&dG_5;lkb20p*Bu`17wH"
    "{6;dARm_(BmMWp1KRi2^Al@QWaQ)Fagn+xqzRTo?rDfq6}McS+0f>D8cCrsu~z98fAdD7}0%zpTe-Dv370V_ZH)M"
    "_R2I6|Q!LLtZBUF|{cOn8w0tUbb=3XcT+>pgfEIBNh0r89wkI^3oD^FznO-y-ZW3qGo5pba{8U1v8*ky8v%02%;`"
    ")sPTEAxe$hVg!2vN3t1k8RA<D37r6koMh_Lcn5fO2sw2A`}xJuo3qo?3;uondU9}db}@N*3>raj>G1e$ymJ>|2SS"
    "`NZCfKx_yS2=)fHtnhP7C-VvcwEOZrmPo)zxF^^k%jTdm7cb!=*yTb!@Ukyod;$8V4759y-tA38kx8${Sup5u8nY"
    "Mx&@yBT?-Sh<T%{n1OnrM2fKgB~1^28Ob{i6O;_Wt>~KgOE<yTh*k@fmo7-4gF*~^bzWpIy%q^vktu+kl1>wmlv#"
    "k2qZZ^B1ECI71)e-nC#Q*;S1`+BZ{1=Eh4$?H`R(W4!3$CDhIok#YVi&t~226-{B;a&ZxxI=(r`?Q-9SP{HwcV15"
    "7eve5~|1HNNs4i*;N^N!Gy~BC+&o;fgUUJr4&5RtM^HgV}nq(8T~0t&Yf=AG_gvxr$6wmPLoOA6!GaOkj2v<DDuB"
    "7>LwCbHzye!qfMdR}#%1(!~Sy_VoPtziCDmXz~LrR<%Uu%VMZRpM!mgTs(~mM52No3>O$c9szsoE$;n;%0k434Co"
    "(j*5Lg3*ZtRLZ+go8o*ce>-EDqVIzZk&zBqn!bT&CV+JD`{4u9`$6(77paH|^0Beaoy2w*~&In;hs(G&+~H3dz^_"
    "C4>FRmlZ~j~=o`@*=}6vQh?bh9mxt-6lUYOP6{=X0#7gnlf7_X*_{25nXhA-L=~tVDL!Yqb>c?v(mBF$(4X7g}xq"
    "AMjG(acsLr_Cujw5nRWyJp#EL$H9(?y!-g_oldiosY|dWG!tZ(gt_?Z0^<in4Rq`17XA0EqQFgQ?HI@K!ZY;e8W8"
    "G6TX9c2w1qhV$6thoGAP;RhB7cW<{R;cS>Q{FSi125jaAdL9Q%zE`r!F=tT^E?P1MwiYP!o(tnoP*fJwahOnOIXd"
    "3E1-u#6lf?Ov(;R%PmLpBo3q9&hw(II70gbn+Fp#o{<6WX`D+Cz}s<D#41f@MFfNbk2|0mJuh_G=Gc38anK9Ad$b"
    "*}k(O%cqJ65CYD(s&rc-)w^84?<|NiF9;o-%rS8v{&pa0*<NB*x8e<Q9EYi0tQ(YuQSgzYcjN@u+Dr{Djy{8N1Kr"
    "&oV^^QZIwYc&PuZ;-fy3Hv@KpSZ09jLn=}>5rZ7AgaT)%d=1Y*?zsLNnkp^g{&6uE)Lv~g;q~`vet$zlfvXF@d5i"
    "&<7K`s`l~d;2nK#Y5fyn472%jYhlDNglYsP7eWO#KYZ*;6F9F?$vlWieC3*kn&J@Eg$vlUg7zN-47U*~{m4KnlK)"
    "sEKrw<^Ml5AwjI3fTY07L^Gvw#e#Iz~csgty}`Ca4F(VrJT<V1D7}N%VMEDfP!fBddryJy#~m;#vOju|Ds4o~DBI"
    "j%IUt6o^w`Sw7r=^3eED*p6U+w0g`@irUXGli-646>nj#1g3nPJ)W7wcOcj3xV@_}=t*K<dBB&CWsu+E^c;HdS)6"
    "VYfCieOqTn{dHx32^z`M!;kLTkAXlKEdj9)R@hS=E)@`9VUD5M|sPL!rO#4zI&f5;25&XR{d@2p;yRcZpWqC=K07"
    "b}TE2LAAmolzF!fkTZbUboODPj9MRqfxf0XfNK2gnD&vDh#s^t|Xazf#YyZJs1puoCu;w7lZ03dWu=I$Jc%!wDk="
    "pWOwU~cU+MeC|njD`%br|BYApoU&175+I@%z0q|Bx={3R!2L;7^jdunRTLd$psG1erJ78P@%R}>9LA(>TDwwx-%{"
    "}6ZZ|xE;2Koa^YUu?x=eZ-utkT>Op1A}+R$DO5b+!EW4YhPdKt(xLyQ!kEU_PUYnK$43C5QV_(1>sae|`(#y~er&"
    "Z9FJ%yjYnE0(YgM-45Qr|3FcE6$>mjjfI;N!X)E{^@K(_aHj;Hs6k7DyPfWRSP1W{ohH1l_z{}XyhkT5PtOj3#|l"
    "Qot0lYE-kt3KZU6Z7{x7eOT1pVWBxZfjXKhT^l1p-?DU(Fp_QfnGRlwikxAIUvq!R+Mv%Mc0Z?hPU`-qRgnFzrSZ"
    "TRX>aE5CXq1`(au^rR>;x;+C@rVZbY2!YlIf2OQ-l4$inC=S#fZ&j6gg7Ih`8G<^FK(u%q&}{xq%Y5k{2H?*J-Dq"
    "^q1nAd(SglHqcteCaO$%#S<=wIxWy>o9@o}bXPZ8dg7mSWZ8fU3HIS{{JJFVU%01!>=k6V=NB0rL(vSayQ+_fB1a"
    "=-fxhtaCsj5I7GW)xp2W%3gG}nxq%|zRH288nN(78+5eLr!jfQuubE_wm$EYIVeqX@am?3s(tU>IWsuqle)w6h3o"
    "xR~vhlF34+L}^pGRVcSh?Bu>ydkp||aU4{ibAd^w6D5tMfmRrpmjlHdI?j<ECuRbOTJavAwXFk<Nfa*IE$7!XT~5"
    "+y7Mxz+u1n#XPowN|4FC>|E#kZ`*aF7SgXwkp25wH3(b00CPI94dO!It&ht~rF*{g3A*!Q4txWxc5NQ|@w5E~__f"
    "X_T#6*&aZny0`Pl;<fEcp<DhF)P9ak2A6KQ(9xB5P@<DAjfA~WZhypi8+g|4Z)x2#H@+k%uxeJF?ISlvxy|xQ#Md"
    "Yg+@^bNfw-PSLyoF5JC^phFFhv#%X>BE^ji&vd|G6N%$6!$hge$B(5n+1*0#xQ&&Y^=JPxyE7Fu=ykJ2=bn{SFDD"
    "Zuzy40PeHYU1+$aq}nJ@wSuMSI|LoKQp_=jg;0iXXb*b1lS~*qU&FiMfg}I~tDV^n6|<fVtrMVZ8swD5#QAn|!Tq"
    "3vh`*1b&a0(o$_qo*}s~+r{P*RY9q?icA+A@|@*Fev##JtRzJ;SIa!p8|Wwlql?ix9&g;WmdF`SVLBtE<&Z)AXyp"
    "KKip6ZhvAD;%uy}@1JT~MZC6rswOJ0pwO#>~R8t#E9b;#*TXZy!?4am&H)Fv_<wjfRho~O#puk<oP`4-_mjCsaj`"
    "j=M)rj$qQ<`m4{Q8KkQLyEzH`Ni&&QgdiKQ1VBss3<F0n~?2s=-X_Nn;!#^A|<WCYk(2;jYl}yjjX(d#By-KSlwN"
    "NxI&t_SfAT`oVg+}XewF~(&$%BB+?O#GAyElJdI}Ktl#+GIK$hL9cv2y<tf@GWKx(bYCLdAuZx?6l21{x@VQP?Gf"
    "?MbK=i|(<k~n}!S;YjzOX)XBF85F!Nvbi-n($Oja=!Xe+7}xy&^j#Eq9VWiTZGI)iRyd#4ULwxxI2N9}*;s5=JDz"
    "0HA1&NB{k<{i-)W$=#W`b0#yZEs{W?P>)^v`F)VpGgs5JB-k5_@J&+$)}{%X+!n>{QVnL%%fY5nB`hjf786!D$LT"
    "tQf?nVtTNcHA#br>)xxnyW{6Hy#vg7c)Lkb{?yN4>PWsjzfOo=L)fYmWc%9L=T@6sGkSEwXOP7=ncqIaW$pmLt&D"
    "T4Oq^UTnpRca~Rg*Ulg5rp`}sv(64zB;KYz-rs;o$FENaa)#C)C-6I9pet+tKSyInqtarI2&Wi!KPb&qK(@l>Bx}"
    ">Eh&4+bx|zAv?PY;$?dxC|6%ZIqRT%tG6f12=s8pD&4?=!#WhM-mCtd50(T!mCPS2<CeevJ&p5nL%#6k~WNjC@>S"
    "G+5&KGC;)8uZ08&_mVR@OV1Lj@;xWmV1mbn$xh7Lzr(_b{thqtnaL_4pjHrs1cHccb%@v+>Ehv+-X?f3yAW!3t*|"
    "fy+7Wd*De};)=wXzzu#_>0JsNlFKNSy%q2~Xjf;)pQHa8bxC$MaQ!5r;_{Y`q^(0B5<<uL<YQYL@WZhp6blw<2&0"
    "?aiW}p5*cZtfl4~(gy<0<O+-+Wz>LdN$&x^XhfOM%(H&$Sq@@a<p?!m39JJz(g?k_?yiaJv)&>luka>8sQ{Kuugd"
    "y$+MP(nz9qvwHQFj%EV5~atfVz{P6Q78WzTvaR<1G~|Q7L77r70gw-v`!lKof9TLD8RsASbdNBA(cT)sN)m6Wkey"
    "y*<OKCk4gk2v{|~qRv|R2oRTX#BC&GF>f|~V!c!T4E1fAm13b*6oC`LUiv#5*WQbfvLDK<r8FAecGQ|OL=n4>nix"
    "n7iTWNU|fo3oi30kiJEoe7L&_qH!oUDRuEOfdZ9D~OT;<#yfyFs*M`0mSKFnD})K<S;(Cg@W@h{L5=JpsIgdEj#m"
    "UiN#VoR{if@uUF*15-IE&rP?Pq?A;Q=Nn2vU*qH$E6=*F=q3l^W;NwfWpCFP#d1tK-jLjVmf<PFypzoV4-+oye*u"
    "f}^P@N%hX`;dgY~JG=wTYdJazbIYw$k#pl;Zp!Jbq3W`)Jv9qLw5CY>%;g_QO1m5bTHOHI$WES@3%%L`{{-m;fCi"
    "vAGX0DN&bdHFK=J?AgD5h4i+IV0{#a!~ip$|5zy(pbeX^z9eDhCT@WDQyQb3(!0<1|VaQS6E$*B0;;9Q3bCGQE^4"
    "x=4uC6VOq`JraQ4?saci?kY|MBiN)yNV&UZiuf_XNkNT&uo)Y%0Y-?F+<EmC`N!3LarXx5mM{v5VOUlA?eAwE6^R"
    "leXM=>R&SM<@&w&74$)6d`7mpTc@_EUTl(I#Y%3LU$)5MMp{r(vSKPB@Sa(WY=YQ^74S4A%M=o07B}XbItI-Ie`E"
    "JIM%|<#J8D{-f#ECqJ-&ef{k)d1Z(4;sU}E5|N}I6dSS*`d>`@kNq!Lt4zoyBuVfK%AGYr1iv)WqY0r|WC@Ay9A9"
    "{Vy^bbb1p`gjJ3^xe0-Szu1~%p{XcQQh4II=@<6aao&_fH#0LA0(Jb8EKh>*bMHB3i*iU6i>Mbz8cg4YJM<0aCyB"
    "DauJhRz~X*xv2tDR?5-e?m5hluSCl8aztp3e)I8p%-Rrc1=+YN;OE{!-h);s2<Hk!!eGK1n<toU$%iOCrN=`LF;T"
    "J+%3OAkGxO#ZFNsnkWrb%inx^vfKpEcm815{v65B=0B(%cVo{WqF0w4PI<dzScbM}bqK*o8u(Tr(c39ugB=5%Kby"
    "3x07}N3Cl#qLMAUIRB7&M>&t~6U=rrpLRL_@xy!=o`I_c(p{KS<*0qAyoVbTjw4=m2iVTs;^H{1g@@@T+2Fg18VP"
    ")eB=|xpHs0mcf06w%UkQ`nmIJaHQRm-LUw9kCb?z7~lJ&j<Ucj)1Sd<6fEziru+-3)o2@S39Y)oW$3KQ0hs&)%j6"
    "$WwPoj<Z@3HHAemDeXC{A>)18y6*MAi&Y6Z|lU|Cj{5FvccfaaTmF2<YD;e}zU@+5nob{*HInd*Ten<+aDmA<Jy9"
    ")0pk2;l1h@sW*b_#{aHGe?UxRa+Qc_2%I5cu!{+(p$J6@MeJZd3Ow$hT-E}&}TW*Z4hot9WT?Zr;SsKybA`F;eZ;"
    "tugiqXfY7e_BzLpx%XB*s$B;Sgq2Zf@FOLDnGA{;f07w;HV-D>olFlpn^)yIe?*g?#vPzdw=Bwt&$v_E!=*wHJYo"
    "N1Ruc-o)j$UGJuZ=qGwr<YU!%82YQf&cCl}tN0sDuRuPJRgP2u2s0ezCSG41)=X$uyno@#{Ihty!5?gaPFm@3B$;"
    "@)!W6<0>>5%KGXy(DLR6aZSYOPJEjZrahY@<sY4&fpzID3|}|Ye{~!6Lewbi-HBg#?6vR~kjss~4FXAy&I@YDPH9"
    "0$#!-t->1`O+E@@H23z9O8!_{SFbDx3<=QEW8;DYY78D$va0-t~?iPagie3D^85Snc|5T34%t(*LNqbmC@V@gd7B"
    "+y3Vkc#-%AJS||8Q~hdjpJjM!Rsiqwht+prDX}ZxD!&jCa8_(1qB=-o>tYRN>^wY)kSi<0k0dG!DX6*!~b6G4E6^"
    "2!5nQ`*c5OFU>#1ntcqlT!i@qOh1JoXZEr_hD)83Bh#MHQg7kFQjxgSbprp2+qc|wmL}+aeV}m&ML;P=ea-N}@7?"
    "Y7y$bh8lU~urHRjN*=jU!d@(ZvJyeITNxQ3#$*{;zemmWvZ<i%Va@t;1evh~vOe1LT}uP?$ODXT&>evqQGD*&%o|"
    ")g_><Qz6)~73na<UY;M(UDRn-vhYP?Mw9_y9iTchvc<KR&5oyg0e5APYXE^nYWuBLh#fNBxl+9@H&rcH6Bp*XEP%"
    "3%!;Ct8K=^H@8Iy$Bz0qA<!6Ah_A^PkVVqK226$?go<d;rkY;{)Km8({>r2A;;Fa$AiY@hY!Dwc?Dwbufn<0=xjI"
    "al%xv>tA&R3cfy4SjP^7E1+M8rHQ?PNY{8o1&s-Gj=sU==cdw`VBk@N(V496`)1I>t(rL94sCRw@F*+>qWFF9W@("
    "b1HjG2-vnh`!lwqVdTXliL3}Uaet_Cp+=J;s#jilwj>_%9F{Ueyt=n%79=pDNm(Eo4G5;lA&m}W+tl!A;9XH+Lc;"
    "2m*WHsUVmm3?Rx7CDmH1zOg^DR<I8r(*8-{5s~zvm(B#+rPL>M1PKa6m2IAO*r<8WUj-z*e+a2_mN8-9a#vDKZ-Z"
    "JYc!WkI6?P=7NZ-o~Gl2ERx!MoS}Soih<(5^wOm-^v9zQ9WMwIUwEU@=io9?)G^#6*HRc7zkE!rv=noN**}kogMh"
    "X`bnG=8Wb8zcTO0-J(MM=UxN~rXf-})SPaLE!E^!|6`a&zaR_l-S@e`f%3s^~*oChNWKOa(4ho2tp?)rQ)iChhRI"
    "Q;b3`C=6u(l2`HAAagS;%X3Veq%WK%@Qi984LO>!Mcyfzdt(q^ynYD5sdie{JGU^EoQ!p(IYq*RK^S?)kX5t={tt"
    "H=_Ttd&xs*IXLx;k^z9$|N8j~d{Sgn+x0v=(tidcT%6_`WwCXwH+aL->4$-{x0*k_X$pxTI_rT^_Q@%k7$(VHV5("
    "Nq%u9mehEJGv7ZJAQE92hAyC<3M<aai|z?6uEA@%5!!d#L*;5v3@fgRDb!j*=x}GD)ssDT7`M6{Al9%lYZ_-6=UV"
    "ZAT^hC>z~`z<-_QbBk82!3D@kxqdN{b%mAi;N!+Lx)PIN@`qkCluovQNH*q<;5iPs!k=#r1nY%6-vA2p-BHvr;{c"
    "4{0`HlOR$f`sFu_gHUXYdp02uAY)p^Sl!r|+OCZAaxiSBI`sI57wJxAV81Y?j4{jz5KQF5*v%#e4HLUVqb5Vj-B_"
    "d|R9diWph2p?!;jG@lAQWYT96N^MNGGqg#$}{nG3_7aywKL*H1t14wJZ^#cAZ$Z(E%p-e{6F>PVpF%=9omYpIgPJ"
    "2hJ!%b0tRoekSm%@->AlkaQ+!k%!o4Q=D-N*Xk%RWkgn5dw#@2`-0A^hkaZ~vowIyV;Dsh7Bgi}N*N~iq5b2=DKG"
    "?l_b#oAV#AB~Dnh3mNc~-Ml7rZWO|MnY`XNTSI;@UNB<okxA7r4@5uD6J!+2ovEr{;Jl@!KN^H)lGs&cu(~1?D<O"
    "W}9?*B+Mw+GoI$b5e+jJKCrz|Yc8wmrCC<<_~>I9`Kri^y2!H`lGnw-djirxvWfkrP2>KOD`1i@kKuIktvsW^iha"
    "5%t0IEP(lE}l#srp+#Wm#Yh$P?S>+}|2R@9t>uNIP&6CF#2UWa($g#C`pi0858ly+pjivWR?n07z~F3CS7zxy_NO"
    "<0H9@HC4|Gk!gvncgij?zn|9p{Lw)zmr)MztpZ>^`c!33+Rb+Ex<yspKu~+WyQA5JgYF>4o&VaZm+`*hVFM$iKH7"
    "s>0&1BX<eRgsPs*lPGfzS(`)ty{*YEGmguNoYPKvY<x>aaL!D?fN(`zmWrv0zdF^TFBG$`d%2?y6YZpgtT^ziXWF"
    "n&uG|tnU!|57vEcq=eH--_@8t^jRB3Rsa<KO-9_xqJO7}2MI#cBK=t*;Ll*8hsX=pf9F{2UHFemyAFEmUEZ5hbE$"
    "wLSWIbbdYlaCvq;@}_Eg2h{*&x;>6!@xcDl52HUi5P&{1)0OlCA>HjZ!SuwS!C=g`M296&?#PCRD{7TfVkuEfwJJ"
    "_9ak1?HtD{V}AGy8bPtH08#*XYk@luVgNO#rlUz?8V_Ya+N%mMW09QfO!Q!XpsDL^M>|37yr=q!M?)iAr;<oC1|2"
    "wtjH4gUSnpT6rhz7)3A+Dn5Y2OSgxZHW|>#6rnkrT|m4$F?!`+aW!)5&p`$7^Kg4e;EJaci**kF(QSyPy56WOkB^"
    "i^{h{WYQ4<rjx3j+gW4s2aVJO*4f+@p&MB`YGU^72@vrmIua!tqo<Wb?FMI8y*t~uIpq9m2d8mr$sN$#E0zmXcIj"
    "TT!<;q+jj9OJu3i?Kw;2PI%uB6^H!<dq5+wVc*WvG5Ps@~aLXD&%UT#cOmg74@B;XC^4(QNFf2@ERB7(*gZMALco"
    "oxj!1>JTIf60Xu}sKT0#S)mWKsOe2aScwi15eytmfux8ZSlM<=4&hSd5=Gg~usF+&kR3lkwFXaF$6dG3!*16EJ?p"
    "6cY~orNUV$a<Oi%PC9WSun{;Tv=TS1|WC4|b6?Lu_~klT_~7zgy6Ob#Zg7wr-(&3$<zB?l*(l1BD#?bvg8PxG(&o"
    "*}T8gd~Wn&v)sjsx>;c$b>9^DDIUH>0%|AJWnRXfM3`>moO->3ksvP{iq0h2UYIqt+L-wZrU0AFmzRO%B?Uc#-w7"
    "@UY-$>h3#9REE_NCrawHoxuR$#G-av2z*G+2hyVe5mp&k={k>r6mn#1rst+&@MYZ}$1H~k_WwBYqn+@7LT}3qj^w"
    "hQIGg~9$h6X16>)G44p&7)8Zf}d?ezT6|M(FY<-#0qgrdciE;ln>f2!$LCHfCeFDsEtLMcM)Hc6&phAnBHDZ@q$="
    "dOM}qcj|jf#k>1+yRZK~14lo|&X101Db-m$ua587wLrtGYKc)CyWtA=%Gj!N&DX~G6fvqhxRomeQ^;}vC*^q0Zdz"
    "t@reBBADKqtuQaK%?`5@OcBue70tY$^22ERt^$01ZG)jyEWPE&sJ4X^q0e)>C2d#9n5w?KW_0TNv+IL+~#V<(yj2"
    "y-PSsLml9u)I0=nD+nesQ;%=zs2M@^|=;=GCTWiJS!?7SA#Ni0pFv{aYUx-C1rMd7yAXff}f8a2zh8oyIb()ZaZ*"
    "1&~NTgcj0BBR#P>Hw4N$iZK|52ocj9)%Q#mmuW*_V4E$b!K+FXw<VZzO{k^O^)n?WCoP3jfM*ZtEEGg_-H~FUhD("
    "bTvs<k&N-$AevpL+?y3;bKQ#y98jLT?;!#}G7l^3v%hU?E!{De-Y|q$}~BfTs8p4%LsD9{jmgj$v1Pa%}}{Beu>t"
    "f~`ISI)?LIrB;}0>wJmaoU@(t9W7Vbsm|9AS(TAL+<r7SI+lb54H!vw#0sXn<N=;fkM(vDVhVgy;Uw&ZZ|Kowc%8"
    "sJg7s#)%w{@<5_BKJc>@V<>g5+%^ifg`!)X){Bbp0+$?7W06d|STt=x0l9zlTAbQvi!oQpc<l{xgvugl;SwKXOKj"
    "NMfrZ#y>!Dfv$hWVP?vsk}dRS(j-R>$I&tA`lX)qAp8Y3q#xU+1ao=80qn^>VU4IyQwGC?Xl^u%jFg}=dru#|Buk"
    "Tg<85^zrDB-7KT^hf0kcXcONre^`|g*Izs2=ZivW_)*ysGb}X8-qBH==4rSdwTrbUXXi6F*yBrUJ*mf4`a{D*Dc>"
    "L^ry3AIP&q?*NvfJ}wyKmQ0>ssPEkd17$A(IWZ4}W}n)V_~sF!*{r;-*TY$-Kf{`|Xk5IP|ut2=plF7hix?1N^lM"
    ";3->Yj#xAaW~!vK2k#O&@kPJ*^vTNZEQ>9K*q%(%_YG0;$sSEU{5ZNCS!*#FCWj=a4wH*Z_lG|_`wH``P*8o*JoY"
    "ySJxw7`?0m4gx+c{O>G^W(wKW$wWM=FDxPocvOy;cZ@uM>`Azj9rhvfgJrr==5GP7QA#lQ0vU7JsCMoJ15D%j;Z*"
    "a^L$u^UV>=zUK+z2l^_(D@qj!HR0<ZI>Q*1fSsj7GR8WpIsFt<a5y@HB62;v4eZ{zlO=t-aKC5xtl}&Khi;YuW<x"
    "5d>vW%{paut2K<4^%jA#W{r>2vp@<nZ9bm;uUM8Ja$!|@^UM9agvR~O8bwg4i`1$4sHwzmTFjO;s_lM*gJzl?+FZ"
    "6i9H?QCu>5cxvYFamYhe;`VJNwKWdVQk@Eo2OeEPwwR=(kTkNuBqv<TvQ~?k0Q<pV6r4*fD)F5+Ty9n}dx;hJDTw"
    "hTINaJ>x?c25{Lr!?SY-qLLcwxf`1TJZk<+<tqi7%%izT4nrLHfNt`?_yn_SlHqJ!tx8M?I8L7Rbn9&63oN5jx1V"
    "A13yNiD|7*v#H!kdsqcMp@cd}KsOiOC8Aw5Fm7DoPGebVwOel_G3(S_D*$1lYt0Aq?beEX?EjLWYP5#Epk;g1wFr"
    "a$+rmyY{lJ4b{6i8~w~eDrBR!lIuX4Zel1t(N49Y~Hn3!4`6SOMb9fLp`WH8m?BQoBfD$BTJiZjjw(noqAC2C6Zi"
    "^M;Ld<M?9zX+Tts+u_cYa2$Jj>m=K|S=4zQuu~v4u14nJ0<+GZKhSOwwS1eU>`u2=*QlV_*HYXa3U(H+e)y$YZ@P"
    "uN5o9@P13R(Fo@Yi9vRWCU$@<n$08aQT?Hv~o3;45;O;u7u6VkXa<{3jhsa{cOd_OY%Q)m;!fjOzlhJIT=MS4VxW"
    "%XD~iuqetY944-V!|_2RLwbqMD$B=9mEYEP!&g*;$)CPGlCxAt3HIOg>gWgw5`ds}Sl%4`Z*Xs&^#9+Z{-4JEPrv"
    ";iT3>DqH$2U;;$a{}(6dCf#)1hFpfaQZWkm?MK&ivV7tFyS%a0ty?4)AFOzsycnmTqXrXbFs4|5J@^5@6U5l*iV3"
    "tD}2E2uuX)hT<ESt*#xfHaNSsNmhEH!!tVjTf6soWxZN<0e+uL>9D*dDDH|UrFQ_mzm*mulp3Z`X#PrCHrGdrN{%"
    "D`S!meG6*d2;O)q;z1-yR2!}FDs#K~J5?FyeLrbrh25~semKy+dtI`ER6hnEDR~c$ab(?fIET5KOHdXcZVT{u{6B"
    "6ql`JpbB%XF0{4B|t$rwk{fYfDFrm-&+9;il9SMY>d`*yaGbEaY*OAmuKKatriZDe%gds`S}t5Q{e_6au6lNiNf^"
    "4mVGWdBzH$(gB_Kmv0FLkJ+zDHmx(HBdH69H3ZOJ#FnN)RvpvSwZbJO?<c7MpkXjE3iI={q7?AqjD@)v1tgqN$1h"
    "*vpdty&t5?7O-S1yMymEH8Q!amV@b|6Cf9G6aqYMdbVSHW3(S>3jphoB)=CoU<r3u??$|a`s*oqcjFehe2&iCQ>c"
    "kN-nOB$Gju!<nNJ69yG5dn!(P3GB#8Dj6U+dKX?{oDjw(wMWZpAO1?jgAAq{w3((Flk1h2@^YL90rJlr7YAHn0tP"
    "Mx?WeBM%Qy`^X;%YTqYL2hJOb%&$izom<%d<)9+{*HvPCLQ^b;P;VNp*uh1}mC?TBT1yllObcV7i*dgz|yfu1y%g"
    "_+M`u2Ygjs{17mkS?{k6%4$B`{U2+r>(f>ro0`g$qK~anD9?;(R0mV2~>e>(NWhJLgMzzy2SEHR!GSX0G#Kky*8E"
    "N8yi{5*1?PHzh<tGL(OH^1tjT&=Zy})Z^6#Q3PEHRlGuunWkNZ^B)EFC8?lNH6H^5dlmwiTH*1$DN#W@dKT&zzxh"
    "|8e%X$v#%8|?0Zi!NQSUz`b-sVCwP%Z>=Or4k2N7L=?1G_K&3?Q&IAKyQh9*GTx|@R^P<Khb==+_@>Q-2?<_bAS*"
    "d)JAZVp}oY}rc-wk&D|Ad|4A)ANvao9NJO=3xG}p=zp`=RC~N^SE&#-1_a&QDbgi3|I`AwZC``g^*lK(rgC_<QC+"
    ")-IqK_tP}02gHez+o<j*s0hT|)M+QA)T(+LZgwi15HwXM1o)6a71QzvGC0Y7u?L}F98782-ie43O_v6v0#uBXXrj"
    "3=B{nYGIXRr(H>SDY*Pz-1sX|&^l*#XFl;o`a3#0;24V=u|D`}0oSwDaez9(nZs#bW^csCN#o9wf9s7s>Bwt2)a?"
    "C!uWK1%(m9&iN_3%ysn4y@bs({4BZX!fagp9&L&?1e=eao{%ogP4OO)Eup`sTE(Zmfz)5JKei~Aee{K-Wtr|;7H1"
    "2t@g8hr#y942KSI=LD4(=o(k;}Uy}&mH=+2U=(RTKs-*n^NB5{H15pO+C1i#Loc<sMyydG>}+(G<JR#{mfK^l<*%"
    "eQeJ6hN%*U1U0`29ps*mkkwI{7Dqmqo=Jo*SNCa{Th!Ae!@RR)MGgh5DoAd3!lv<tOY_-TJ|R?%uVU^0mQflz2>n"
    "AQl<B?&z}KsV;d8F>kF6|fnBv=VQ6|Ntc07_8nAIm>0fV3%;?qloWxvJ4U!Rr3J9W^JXRDln5%s7RrK4<`L~20n{"
    "QU~(^XxL^37^5lh1QwF;}NQj($2B|2(?9I=eVeP_;0A$SaJ5kel}xgj6J;jOgNH#vG84f!hQ7=@*1e1T>MV!vi1>"
    "e|LHD?&50n8fAuj5GDTP^!n^)BHy7u<%gd~muGMOc6R<3{7ru{_nnU3U2~)IL4N$<?ZxR|`8WPsetL6q_LhI4Kjn"
    "whlk?M&{3IV-SMOD^jlSUP%ab?Pcpv^HEkZHp-|%bvOZWWh>g+G)(sTZx?|FZIF7M2Lo92E#8-3vR;Lj%w#p#bH="
    "YJVpjW0+4@_uwBR|VgG?Z}zIInkld=op<|j!yK`>F+1J^XbJ;@7|8|ee!AVWH!8p6)>Q~F51;|9_4d0#HVjh&VG_"
    "!(BJaY>x*+*zVL_sa&$r$!yoRGFN<Ylhn$_Cp1nIEekuUjoMr1&LmmEfa&<kr#NSpa6cfu27w<-wC)XGBlf(n$$E"
    "$ZImzOfG)f&)N!3S&Yt}|}*L6t~G<93v{bjK1bK|BS9FF|}s1!)S)c~TWC1zNy1MW|u0DDH|agc=a;Uw9Rvl?fAt"
    "B330L(-C7BvI2m}KKbF|{dID)`S$45?+Fb2ukU+8Acx$2$cwl{9=swq<O71<X5(&76^LOXbH=bvozQ!8Ss4iPUNT"
    "j)6o5)o6J7<f#=C-vN}24CI<CJXR9YH<TcFnBY7@|ckxMV-&Y>5SITSE&3t>6$RJyG1c2IgU-^^;x!qI#YFq{>*$"
    "q>gn8YOWO@9V5yD(mxHRiGwg>bw2DO<wB+l}-P~G#eJ!7vD-v*;1b)&D&g+V<%m<IX&GyzS0_5I4>3-it@f~)olO"
    "-31}&b^8PqUF+&6RwWdszh%l^JF<F#Qwt;xUbPZO3n*}Hq1o*nttR6$X(}Xa9w|9!yPF5vX7az!)WCl9D-1P$ISp"
    "hyVDj8a;+pNx3us`5#jDhh=P60pYK~;5jOG^)F4@<=<A3N!+i*39r9*BwcLFF|hz;kO=0X8X;>_QqWv}fv7Kn*Oj"
    "=?2RrIW9=ef?W(F2`7BIMA&j68BGPmoV%`O%M|f&rqB<<#$#eeceN0~qskXWIa7vE1h+O28FNeX{Y#iPu)Bn+S+T"
    "a)Z*2A=Q8&r3&d0Y!x(wH{wR|E!7P%S&?zQz?O7c-^49O42DA1i<A!@?Y7XIZ1@C#$>-FbO508kaP_Vp~Q+^=-0X"
    "lx6jhgMbNy08b;6AJsfdxFpx`+Dn-3>4L6bHJtyyBdr+?CWZs&eWJ_qK$w8uX+I#Ib#ZS7v)a#wwSseycB9Xh`A-"
    "EqU?Qvs@Qsi7mnw;ELQ6pD5$M3P3PVAXqY`E>1jjGy2}1O11fdtY>-*D&b%5dOX#yCDCRroruA|sYb3Ul_*HBTO0"
    "x=Ot1+GcjW^RZ>hl^9wpwbH=;{~Adyw^iJQmiyMX9PgLGXr~Qfd)3h$2rqgciVP-Ps)0i}6FeK#B&;mni$2oO&^5"
    "<GDL9k;3jv06iEl736t!x+GB7rK*S|SoaPk9NE@{6$a-yb%@jn)~w+BV#Per{XP{~SIL|H```Cp9ahpDxcG!&4iu"
    "bp35lXm!zqVAsdBX?Qn#A}h;D)wG6imndxjL3wx}iW7+?bcw!dRAaAb6%(~Sr$X;djIV<}7%3zg3x41{k-24G}{p"
    "m=sSo)w$Cw(`oJBuEh8HC^sq)+VRY-BK*|=h-bX13AY6I!ngWohL2l=F8a2I0BVaapKU^*>-#0X#_$J98@jZ3v+A"
    "3JmjqHijp#g%A0bN_jobYg$8WKs^rROF6Mxo^pXj-f~fDHj!c{po1iL<%vxE_g-Um72U-s4t?v1P2Q@Np_4vRi<("
    "41VOXiyrc}9tkP;`z#@`0A9R>D`vyut&LWOG<(|GGhfd4&2Q)(_Y+Mt`s=zHzPcQbY#~j2r4p`_+f0C8IS2O(X9?"
    "*$QQBR*xZ`cWk2I042OgXDIF?YJ$HA<0~bi+PK-AJdfco)dt~-HQNV9scqzb$o&t<vEJAWW#a{&VY{IfFhW^wZz1"
    "QQVi&r~gucYmVE`&-T{kcL56C}|TRQ4In-7AO3W%Ao+L@RG&Qka&py_7)f6#;<X-!T()S$5!lz4$sO&vF_E~DNnX"
    "Mh)*rEVt!3j+4xR4ogr1Ltm;mmr&x9`O{lHe8pU-4)X@e8ow=64+a<fUrpOuG;wUeOX>Vb#0XKC5-GBk?)<_YTUS"
    "#QaJ|r!rP*3mb`MIMjLFnPUK0r3(aEu*|O@JS0u5Ia}*BfOo{~t3Tby98e@eW5_;*KBvU}zVWN0|*{@Wx&cJ-SR1"
    "cZjqMXIW0=;*94B0$tHd%<HB{jh=71A&8d3;pUT|}@BgaPtOSM1;61~A^2Rq{I8_Dd=dy<n8BRGP=`6ZLnckaP?v"
    "inS2O-3D|#RR$mFxB|kT8JL$}Yt;pscGG#^IQO>b41Y;)Z%cLS$vNI6=nW#F`b29DhpFX!&yi^j31ZOGQy0J=Hs?"
    "6SzXEpA3Ij@X{$E{u&@1Z)IrMSr^~qTy=Y#fakk3uNrGu8}Gm$_kO#p32t3r@+f&^)4b#HuZJlViLU2jk+tswI^&"
    "Qb%C+uq+SZwnNu=nr{<<O^mwx)!8gG3#}$N+fqPKZa9nZ?@+wo`@wKoQzL3k7ZZK)=2cF<@j*b)%FhSdm7zo2$8f"
    "`xAqhwi-5$j7Cjpm>Fiy64N*cOrvm3lg=0Ba^UYdWB(9#9;SxP!`;`h@59~i9X0JhVGJnXbqTI2VW?w@JJ^`adug"
    "hW$sF3XCWbIjh3p7^6?0yXX#){Nvj+a~wlGmyRD6bp}!kAU}-LAd^%?1q(aSDq&TQ(XTHSicq0ZHhIDKgYoAOxcO"
    "$@Os1@hz1|HwXW_Bd6K?-w|$J&HtUEt6fu+6o0iw<BoUtSae@|9X4tZR%VnpzR$c{ERyHmmlp^$5Z6@SZI+d~D6`"
    "wFMK?fvGsG9%lwb#81~<Exfl&oyG=ySu00SyYYLtu_G*v*({@F|%dH8_u<h%aSAN$|_sSm^cr~Vpl>t|KJQUKvtt"
    "3KS_uQqE{;_B@scf}H`i6w0yomO}#fU*K*hlqAZ@~)==)|SO>)gz}e^|4>z3lkgxdmGL#uF1q2BqMaEfUCFP=R20"
    "WWW7w0vPIsn&!P`5f*6OGN`^F=lolWXEVjfgeRDvY0K^Otl4Ss*4|>dU3tsj#nH9^;DmTYfj{zUiNxo1ezOEisxR"
    "t^0pP+8wTaN=7w^!eY?S*Z6uf}ptv|Wg^I#v&R+S~6+P<efczJl07t<>Kew{4q**GbiWQDSqSn$j_f@;1#mTi30i"
    "wSGv-qNtA($~@>LSO4-BkfWDseyd8_F}Khx;jOL9;$M}3dj1OKv(??E&XzIaoLRA4%9GNm&cJ}AFs#XcQqBi(7%s"
    "D^{QAxm>o(_n_@%TczH~(|o|E)dk3hCLXQSb6VNmDZ!zbYqD>pfb-CqYDjtaZv;!Dm%Y`FFTIb>y?u)>=*MB@#j>"
    "+(3GrZDEU+H{k)!uc)&{-oiP(W4V^%ocq^OYG^Cb~>VBp;0#0&l$s6yIR*h_xGY4qgR&IQgpWps*l=^StySMs<kJ"
    "g4lj({B)`O-+iiFQYY*{D@KzdYx1D@Z;$gHO1Q7ZT_*EJVFnR-}WO*ZJbl{$R0aL<%YiS#NfuRKcRy?Wvk%JBViN"
    "ntBC;M*el<x^eC$0ef3G58{P%Py>I;r`Cgz@B~8=&TIZD&Kv1W_Q%Ut#kHjIkHa>&UlNAsw_1s8zZfgM(N@3{A87"
    "7~-+xl-=n)CpJ3PQMR_uv8zbW<E^U4@@2z4r2?8?z4NBUXDDOEZ^!uYDfdCZ%G?H@8t&3THE#qzTwMP3>fOodX#D"
    "Qt?b+$s=&EO#(rLN7%F}gqSIE52v&CXO<=^y3QA|odgTIF=;4zTm$!BiLzQ60_%UH)=j8Tok=5!vyS<#4c3YS3jN"
    ">RXgA>VMvFO;KWVGKu*uH1p!UfLu|gSuEP0~WCP6sVzD+;`kt2m0Qd1N_1{<mb}}g&7@S0gMWvWDP(UA^QxHG3YP"
    "Az%&P4$A6!0$fe?6GEkqhs;+z@6U;oe*_OICYVirjxin}taA!{JS(_x1VGK$xs8w(YOYmMY-Pz5}3WGu3V~-g6-1"
    "H9xQgc@1DY05QtRPLsZtE`1=SwB7A7{*yb5e(scW1AU;XjlbRVqyCC+2y(Dar!Fs@q+Kls@Pb65D{8>8s5O+>Hw;"
    "&t4W4MHDN$9do?$@k2pSu%;n(WJ=v#7R7zC%<dr&J1x_E-p|2%nX6#1Af;_Cw#&P-*YpO1<Vq<CH4fIh!wOPWA^T"
    ")r%%H$i>-jz^vOZ9gVf36eK*|3PZcj$4w_w7vx-)~+Xm3YGwlQTi6!l<rKhMg}IxR7OpBUG1DUOSK8-qj`P(*#}H"
    "119726K@)&Se+U2?2TE&+0=<lcWdyf)=$?z%<cxQ&B?F@oZV)-9D#IQQi((5ILo+LCX%fo<zq0L8q%utR9A2U2ke"
    "Z7{v+}kxKFxB}PLrUkCmi5;23pA~iSwMvLuG+dW@AI_zjYLPseG0R{2Iin{w40=O6DtzE5*-Qu&t@q*&wJn^VzvW"
    "33LMX1LYj;86e?jB{Xd!OIu#g;v4gJ=ch&A|yx1gF(&iJ1W~B=iAtf2yXNX%?B!E!u?&3$`+LrMUYgY_$OppWgqY"
    "jLj#PGz0=P<HmvRxk0y{l~mO>75XYUkLdyS%}!@M{mfiAfC22$7Io`QY`v@_f7mRSjO=JXp5M&BN-KTIFfpp0Rpd"
    "j30ztvGTNeOp`&Cf;EW7PE`G^d0jeE>T>{|Hy`cu4Y+7Ye3ZqVc2N2t3N`{ayV^AC|44OPhVY4b+WvotOhs+|pNo"
    "(D3`Na~<Fiv*W6wLlZYf5Z3F9bRdz&BwhPD<w!f3s?c&MPj}*!z-A4<em)~=qDxH9K*i9*!s=nm-TEo^dObl23BA"
    "b@wj!XV8iWOlo-8ud(PD&%k}F!8`ZFfUj&206^3MAckpZvnd))KhWKCa7iZjt&L<zllE!4n|9Za$Io?D1CnVXe)z"
    "CJv2U5Y~UFl|i5AmaSiSaKEH9~M4{PHVztkIKtG6%R3<nOQAx3Wu(9yZ_?;ZvTroq3*p$a{VmV{Y|KMwL@lD_Q}s"
    "Dpxbe9@1K<ZM;}wOj~%;vX7h)`&K@L1{&5op)|<bnm&dX4=9j5^xYsG=l7oD-WgDdST~^9N*{vz?fH_So5vV*B11"
    "i9(FU=CB5&hD7ZB=W#9Itr(t`|lv)FC$D4j3e^Cm0O!V~k}8}Mny6rkYX2q!qYd1bcf^xR&@HpsTb%J4j{l8G6$i"
    "G=GR5Cs9x<m4?D!SyfRjn1uc8`!v3ShERLGhnkyYt&uv&P*_o0m7V+a)Y)u5mBPF;Bp0rYbFP<88FY`N8?5#L4-d"
    "@Rs~1MvK(0<v%JdYmRSuYUX%HBkgWh73-(}ll2~FX>AdN`{}ZJ0CX4KI*U6*+c3~T82+UBh(h(U8i-U^QDno!QWG"
    "4juyWgi&kGpiuSvSDy0eGY7y|T|x3P*8z$qv>)iUspHA^`0Mt)g25W+B0tsbIX@%NTl44cr;*K-$~3OL03K?>r%_"
    "^kiFtge;FC4Fz7s#--s`uttZAka5On#91n`2LeFq2r|yXL*q(#E;r$zAU+EslH6m#=HppFq6q^`XUX3RhICrgcRC"
    "rCD!UFf8>A*=Kz9lK>Wt8u+$5O$0AXJVb|UT_?7C%I-om6?9m4V(2e!x5#3;&9r#DGDvJg!SjNLO?-A(TBK(d+cB"
    "s}&H7VK341gw5-R<klw0gRll%otfXG=GK&-)l9*|Mo&`3SZg{V_)`sm@F>%83K6y=QXAp8zwb)-ReGD>qMInvB54"
    "38X{^E_?`!(G6WY(q0sQ=K!O+KMIj8u6rIly&*rQ!Or+D<dQg?->-J8a(XcF*Dyp1GoMM2*$6u{-J)QRC;xf4$y?"
    "c9dIwA&?s@PT?OU=T#5v93z6OXkdLRL~0TU65EU%LhPY!tRJ411^B(D^2X4cdq)YxK-V$3Ohb(=_bXzCA{KMb4eD"
    "5-?~@+#Ik!73JELWD;5w8I=Ss?8Z3Nq~GV#7s%DXI@1)I>|xajA8A~8LhWJ(MQI~|yrA?z#;>Mq5=dsE>ykTFs-("
    "kMovK8*7Fg7F0}Tp9a9nc}l__MM;Exl#F-%F}ib6Vdx#IHVr;&Sxq{%{UX~`of3cbi6V6KgKF90!VU+W>wkKHP-c"
    "9UMx<E)Z)3ZH<+=aA<0uxV@H_Rz9*4W2@Pva&afd7jON)7|eSBYro}l&^|yv$Ff&Mx{N)!AMd}&PB3IQhPAUbGuZ"
    "8K?J_0W7bGm>G5<=S-Eqy#QbC039KyFMKW>Cj7d+_8q`<wP>C5dD8-;$`Hdx1A-S}|FyN}i3@f9}WHtNXQD5b*@j"
    "f&<P4vA$8dZwbQ&MXwuoVs6`1(q-fe!&;%dYZHJk&?X=xegk!c898R*i~?UeA&5BS)~ksAG5R*Hao7@G$yq^UkJG"
    "@f{9P6Fe>i0QYRZlK~}}>|3~S&#}LQo@XdR**!leG!xS${@90o<(i4o8Uzge#SR(vvgpvMyuI7eIfC%WeC7`PMF;"
    "}a_d<XO)Zh1X6376p*Z&Uc5{`dFS;F73*q6V;5086Sm7Z)~QC9xto^@kycAge@8UG4G#98u|#DI(T?k#r;_U|uJ="
    "p!Dbr){$^PK7DDUY!I5r?ju5)nP*&dh#x`7Sq}J>D%|O0bNE6e%eT->QhN;zYl+7jS4806dGKq5?EBQxWv{<NgK^"
    "|#Sz|CY-*zqItQv{qMNhKI;8H9__3y97&OY;oi~wF)t>u0TP{i6MyCv*W#1eKaK0HGDX}8p4ag~yDlEq>wa7{cek"
    "Qk@6ezwyn(;Io2A&g1lfH!}vl_D{OiRC#6y#OpIuFd!YIPs*W!iy2Z{oNRU^vx&*F?79E3qvAPKDj&LTx-ZoDIq+"
    "q>HbhfUYr|t+z^rm3yf7NU{OPw%Nmj#adq(*M67H?oF|Z?Xg6)qBXKT+mt0?E?SV0`z;zFLF9^aWI}|)hglG_Ig="
    "dfGo{NchDEMA-H)-ipr(Ao#)5wBe$=PLC&#!(EHsczf_}zsMcfXOWAuFluFSf}ZZNCxy}%qE&>~Pm){R9>ERPuGu"
    ")af=@wNcDl-ljgi_H{N`X$Uy2aI`ST=4}0?@e|-14=FweAo>UyB`Ba&dK`=Dd@#!$zDkiYqLArk&CnxAS)6GR!dk"
    "=*){oAx@L1Gh6z8*<Y?iuz&q}_KVLuwnrkD=ViIUuSHq#uyQTL86GB%!K65iJ0QvwHJ3NxR@F)^<D$aSRB#dvLiy"
    "WM$;8m!(3<OUoEOXIisdwp|YnH0S!l8}Z;WNYp!_+%9Cn^*UohK&*Ytc3X@izC&3r$A+1$CkeGl@~PSHs00(u~lp"
    "(1Xkqs-M~;v`wOMk@3J))+%M1v|){U$PemTt3!6Cty`Kf%g{#LX?7Z?)otiBCS`BPlF5%<bC9{g@-o0Ycz?{Cvtf"
    "EnPqtO0Bj{xHveX9*Vff$E+xkp~Y_lS$<KipRv)9!9_#0Rpd(v^YHS2<3Y7kjX#oWkVS0Z^hW7o?psWkdNC%}*2h"
    "Gx<}y}w!G-)lj=NUn8BIqK~cDm9@~9U$e%XmtkxG*E`LI&HV+tLbp!n$@D2sW1`;#rFpBanNAaSz3FmQRj#qdShd"
    "5d4`?6SfYyV*O`0qS#_K^i=u2Xg{`s`_IpOHH&dFLSaAh74p>Pwb(~Grseuttnw7GTT-zboZghk@Rh7M<e6r`&N%"
    "kUy_ZIIv>aLCpo|Ra7T)@^Xq7GViw!Ed_x>Q+M8XIFx;mI}SmDZPbHF0phS)9jyK-3HvUuAt0Ud~4$T}dCpi=6T1"
    "Yn|`HTl_iUyZo=i8{Mhn+uSe1o2;|(8Qj^fxVC&L+cc|jJK3v3?<=qX#uZ{9xKc9T1zYM}v0Nt8GE<A?PAgTwHVb"
    "C7R_DP0Fq;iZA5yH-H?6%z{ywg7wFDujMdzwU{q^kS#jyml?ua+F25x%$czs}CfTEmdd0Ot0St?sNO>R}b$#RA19"
    "-G;{(C&89WLBotU9!sNeXB8@>Vi;ue_}%h#u+Z&X89aq_V@(M^}tLMu0+YzXUj6dktVSXH5TB?p;x=zC`8o-HC&a"
    "d#qEz=%}7oFT50FoqX0_&d2+~+Mcerxn<pn%i7RJ{fyktFF>tm7iIuo2&!(Tf7pi1CPyYGh?A((?>!P8Ji*tCSzn"
    "_vJ_mm{qc0TaeYgC-ENOQ031(Cj}fOCah13i>Y9}133pP^__EtOh#js{2HhG!p%#~`3+4Cv;#q8-VL?%eQqr@Fo&"
    "4ft1%TzWcJ&v$VBDnZRsF*kxb*0ty#KYr?ADDzV@nIzHw2JT|3*4Akus#VO=yvPBf(n=+;ouni_dZ=Gi?D70v*O7"
    "pij9xkEkdkFRo~3$s0=fzNTjvP;jp14JJKN*1UZ%Sqq#iiwTH=^StWWf#5JJ|(UpH2cf%ue3k%js^h~C;jo0w}rb"
    "z^{bSJ~-%R_0!oV~!pdxK#u5x-h1bq{t<&YhvaRU-343P`N?=;x{ZLHv)VHq-^I<QJ3E$A1m-ybRfXWX?XoU{48?"
    "BS~Ph9a{`js8F9(}W9TVoqQ3ct@)aTQP?p5R{>?XN3xKpTPZ1yGVP#eY45U*mh>oL|+OcPhhssa9q|bbSS&nQJ6I"
    "kUt)=LBTc#xn8A}lYqk~a73L`@t;fDC+4iRAO}bY9zql=L`&<N;6}=sQDouN8ozOk&5w<PeWmGJWl^yN;0rT|=ZE"
    "3is0zr<d&jQs+Z9M<kYL^gUg6oovmX9aZhwFrX7EuKD}MDyL_N&OF(cK+@@rFLE9)@a-plU~Mu;PI7ygSV1uq!JJ"
    "*1r1=ibKTMPa?<<bEByM&Dc<#_n`XqqTL>6bM2oYb+bvDB><Xz0}+)UNFApfH^<}%339j8%Jeii4-axc29?D)&x%"
    "CPklYe9PH2_L@VVXKBm=$9EDp?pih5Mm|)f0cV{COG?1U`*bhpZ&}G5lkezB4^-6w)Q;xllu%djIL&E;y9Vab>j("
    "xS>}bm%0;8)T66M+&S^;J$;8!PL?O0CEGL%0RI^VWl0V3`fSp26*`i$ErLcL{s$8WxI#hd-sqECz6{{3zagcBnty"
    "uB&v&LL3cs(Q<#iZImoNwo+5yNw7tc)PD)n8g0k)v<A0k`y`D3z0jLnU(tbcq#bvz)2;tfbIiT2nBI4lPe(nD>&0"
    "EEU<e-a+_oGRD$ukk`B-stHQ|i~#i0Bu~q-*gBOpn;fuo=d8-ZQq3^M`0V`Z?DZ)2a*}WdovWSk((ywcr*)Y@Gz1"
    "q}hiC@avzJZ_y`7y{Znev2cV&?mn+i5x70U>R+COmCZ_6UT#egtDO98ZGx==RnF5p)`sAQ8%=*2n6-ejMt3SLp^0"
    "L*|N7JWH!qWth#dxl`UIwFz6yODy1mzI2e=?BhxNlgIUw!+X5M7MW~lmXOtDl1`-m^oeZz<CMiP_w^WCiPvZRI*-"
    "fDlNPETDFm+uE!vfa)!Du=~g=wIi8!glZ;cqV#ldv-R&PAfTyg~68KrbZ@9@BQVwRClIpC5V<p$A9E2WoMnl>w1k"
    "T{xPpJ-p3lMmZNe-S<Bp6f%SZR0#F3JfmfIGE>mLQw0V0mNhhpeLWCaaQ7UKg9$ogyes$_kLe23|Kz;DQ_+m=Wg`"
    "Mo2V&p3T44>KSUd3y4Ml#seh_gCdDA7xq%OmC7FJnW$Ix64q(eJh?bO9ra}6<3z7jQ&ysVM3SV7EGFLUq&3-9ETw"
    "ZBpt4b63rH!I*TA$w2f*Jq=`vgFSTvHJYrzSq!R;WqIbdu!Ao$^tMXfg}RZ(L3YL`wxPOjiZ6cn;Jg&nX4EaX%-i"
    "NpXh5{^@VfI+Ehpq_oNlUfLN*HJ0p0+@h1fJ7A<qg8ru`*XC9n?QE~TbJgZ(O6dnx~(&$^{!P}K?HJwcG1MP7y#G"
    "{j8k55_S*pHCFX5oyIdGmE7o_zilJV!)gVG6FIY@;^#BHCOr>K10aYu2#?ER^=t(9V5S|>nhK}=A#qxm$R-Y82Lh"
    "9L*QARA!JW<3)h=|BxX$?FHQ}6Y8hrQv!xj8^sN>$dJ8v{xHhm{RCPh{<NnSIvwrmE_6y38ur{o*3jy6-0M6X2$}"
    ">5yk-ZZl_>8r+4i#G|(;oE?5z<P>5Bq^OGcCIC}azgb%GmOE}xCYv28s9msD$p|%RMx>pz-*Djq93%IkcEWwe2O6"
    "_t08I}ePZ@}qv}E@pYdgU1U_U9<U(s9QB)@+LPPy}Is6IpC0%n9x`bRvSuHz4)5EJhCN(<$j`9D=j+5?@he5%X*f"
    "yA~?9~i0c3A+Zmf&xEV(o};#;IQ&)yU3D(SUc=V(-dq*w&_%co`eM<g5M!Dre0JvRa-1Ityr1Plx^3SE09n?aN0w"
    "jQT9tKdLjrw-1holFpQcIl(96C+%nL*J?@T33ogh5s!==|rwVI%&C{IXKJd&YCjuJeWxIe5{Gfq_w5yuO%F?7!h>"
    "6d=(`2!b<ndiKR(C9)O}}qx7r5c=(`k`??r~#%&B<az6xpJH5`D~G1THc7an3RyJV3<fg4Ou9d5go__4}Gyj=7pS"
    "S#ml0y>-%nZ7bx-FabavC#)MJhsJ<F-MEm=KGbyeSA|}YkzRBY+rdl)nE(l+e~x1Hya3)b@8tR(hk61XVmArT%<0"
    "8XKb>8Zeh_O)mxkuVm*;9dghvYpc3Q5MfQUtYwKCpVn(xR5S*pbn>qv2-aJt%{(Sh!cD(POk<F*=wmH<anF_J6%V"
    "<8B-lansI$bs)m?}_)kr>Sz9ikN~zrnY<yt?D^ZndfvThYXMA;-(0xHD~>ev{MSSQcxNqQ;;nHbqG(!n*$A^RF@s"
    "Rfke>F!6wiCzEQCYj^nTEIi%d}Y_YdE`LB7TvFDV$>@9oQTl&&g{?bwc<3>oD?)}P2-u5aP#4CFeIr>-R{eN9{iH"
    "-<0q?bhE=#X>Q4i?l77-R)49Y1>GcKj0mn%W6d0FIrYYTLd3&Zcq^Z?`|80h38^9LR?D+qYw<Zl&#FFGIr5=!)O^"
    "__XE5>(o2=sfhDeJ_#DjQp2>HW_j)><TPaR?5l7Mt6Z_+L;I9yKPZ|fOb=<xq&{t(S})taM)oeEr>q#(@a$8p;mS"
    "RS+l%C#!G~Z}2y#iBya9@6-!DL3+B?+V0#EG=)P2x9z9^P+q(w&8STDhf3B(RTx4TsyijFBtUC$iAPy)g2v;?KJR"
    "}j5<oLy%*RGdUY@rXLF1H^1qci>fxL{b4URng6Mh+bpK^~Ot|QCI2Kez_5FQsG@dT4Qbd0d9)_)=perd*#T2b%&n"
    "=Egd#)Nud!BFD-**QPtYcl$sW>+gzkpUMJcM<GapS5C38Gm$UQa?5Cebug^}dM`2j_1uqx~Ux4$v$^bN$%qZ8oII"
    "NP*8c-GTI-!8*bW{7lw){pjamU_+hL_S9kuy)2hsjgmlNq@ypJ4jMftM~Jp~9?s#_^pih%M=m5rz;oY<}e}*F<ok"
    "ftWL^X4!g~<*GYKBKc*&hm59m2nB3~<bWvD%*GBRhyV=-<A<*S?#0^eR^~e`uo{I}s=?6)&oX|FrcODDAhx@qXL%"
    "ISooKIkawJAx4nm|$gwP>yo4H>0=6ws-$&oqzS!|Zef$jOrh^$I<vxekAPYZD~Ky@PxX`oLjaB-r@IM=)_zxdDoP"
    "5B59A_BpN0u>I5O?QbD8w!eZncd#ic%n2Eh>R>+mWTiWl5u=rgr(+!sfLmk_KVqeuO~?)MZ;b_4Xt4Y<eb53+0i8"
    "2XkhAdNfgXqG6k-*`l<CYl$_Y_7lhu8Fvagqu77N}{Su?<2)LxP8sm==?!uw37VAiOTTzXys&SBtUo&2EmfzZGz1"
    "`T&j``7v9Z%*8zhyrOxZAZ?d*lMb3v<swx4s9Clvv-QM<}0%_CWMvclX39wo1o0x$|O#)f>?DG}k{gnr+yg(^9m8"
    "N%$7*niF(J@2hV$mq$unUnD2Q9Wtk?te&_kPtN~#{Ug*=D_YAYuqf`cK3&<j8%y&YI?wtNo~)LIJ{f&3b&6f?R?9"
    "5EXP8yHEhOkg*BTcLusT7W))}T^q!m=Drx=n}C@}#hOJtKHrddznqSqBQ4!$%3uQyRgNGb%3Z!=$2?Uk0mNk%W&b"
    "K;en8bVXTV?dOIC%uKA$nipu);OJ`N*FB(2xR6?sk-$fA}tdCqB8>talxfa>NXJDHnGP{NZHWndZ7L~xci9q5B$p"
    "%78TL2MK6ps4D9ufXIB`Yx5`cqC|AVM!BS9_c6^SwrW{94UZ1^rGrAm|U)z;hGWB*_m?%keNs0t2^8Bin$}WAyv4"
    ">J0AiYDy&zXa5VN&pT^{A@n#PRs+{!%@tCAjsLn<{$%knP)aZ8tW7%$1i6YX4GWczxF|a@Chs)~f6?fb)EkP}Yo-"
    "8}R}u)e#8`!*v`J;H->{=@XE>{aDwF_U{T(9BdXJR;FQtnUxN47&F9u^s~)%p)x|nVHy_fFe2X`IPcg-IW&P37)4"
    "<w3?5ok6U+ghIhbOYk6;@cxGJ5%CgD#qQz;~-_R9^HML33s#zBJ}44iaYOQDN3Wa6IHg@TS&S2`<;iZX|m*#c`tx"
    ">VE(lA}V{du!Rko^T4NxdZfGnLUcuh=I$kWk5|CAmb9?j)^f)bnOfa-^>3Z`I%++yiv@z2|~X$rholvVd%F9(`q+"
    "iOGOrlkn)*qa!A6v&4Jw@;j;v!xZhq~KrY?_`hb=_XA(^Unw?2c@*mK}08~JjDry^6jDCm72Ef0<;Ty~ga(inV5g"
    "=_AxLRP*g|B>i@zcAvBfu8GoVvjDkVrkrd(7vAp@3=hn<A+B4e`<^SQ#%R|CsB6I`T%!zsX@kg)-@K*>jU><YY=Q"
    "6~tUi+I7x0W^sS76tc@{>{K~W2a$*ZuG~Ng;2=gwpA;(z*<<*y@gvj`W(o4MzBF{=H|67?(FX{|6yHzTMM4UrDh?"
    ">}T69=xn%$AQfZxhA<k<WnugpW(cZV>zhYnb5bEB}n5W0u5tAYC?ncWrHOjRatU9V6J?y;pwUb+S-1XHJZC=6Tzd"
    "phPVO&Mt2#!)tct$A82#oV69$(O@kayS4=tWH$`He@GUK;3T3tXihjhL+3NUlq}NyA8Gb0rOQrUj_Lh_@||j+ok`"
    "3Xy5~zAd5g#yJZX_JqcE>1-aE?8YZjxzM#h=j?Q<0a^s{yfcwCnQN}bY=YS6s^pB-!AWTWtE{H__7fDs1ic)<DTO"
    "kfNcLv+k<u+?%y7VIDEJl~glgv7ai@bsLU0G~yk<MOZ^s%c6u->X)P5f$3j>h&5uzfg0oDl04fTyDW#%~LhI@<Nz"
    "H+<7#K`1VkwvWo4O7qPca$NZ3{njua0Hk|`seFmxK+V}VUTvmToz)wBV1mOJXgl05eMs9Wl%Vv3?uU8!%Ozx*E7a"
    "9V%v*=G-(G_i)ub)hIzn);h4xdc(S%95MsW|c7Fg(zn$$<-dCsaO8>u4RFh>$iP~2Gqzm;n|mD7bd8c<oyiK}>qx"
    "Hw|iLYk$X1}vhmvwFoDX}FvEKvyxhMg)a0PTp}cF=FK<2$YwTU|SMMIXK_#izi)n@R^=%Q8%c|6c}`ZVM0GE5pls"
    "dB7hmZFO3Wr6fAd0yM`NmV$`X4pTuEoE*xaln0o`cdx%8@;)&i^U*<Q5OIxsaQcQeT<YE+S!3<u-aQ5WuPlLrkPe"
    "<Km21MlLAo-9k?<H}|dZ}cyhGFPHJRqVhW%+Emfh>S-GSMf&MAzQfU&<U2>{Q!YV4F#{-kkJE^LF5tmu%pSDxO2("
    "1+zR==0cP7Yj1V&gyNcSS`-X0?`*$Aa2?;J%Z0Z`ip7G`B7)2=O{2y`4*Flma9$?gm<7U2aNT&ajBa3PoxTl8Fw;"
    "_{_XLh5$27x!MF!j*=GJFBYq;Ur_E5-uExinMXLJ9alIf@E#~+Md3_A(yIiLnA`2zl0{je?v2DHRz*OARuGUp`@G"
    "w@fIrWI?iwWy3{jmvVwO%EYqXpmNQaKN`J$a{|d9<6RjKGs!Q&F!HC<)V-jyObL3pz)AzZm;e5zi!aoK|^m*x;X("
    "lwe291oZ+q)3DeeI<!*~iK%`Oq*`~W>4pl>6t>NDsoaGOysxv5zN$#Ky5JbGUL_wUc?DMs`!>lS`(V~`imh$}++d"
    "!{b%Q_$?#r?JcDG7S5Z`0*HtLdmudrtA>^5WteS19H=P=SE2*y7#b1U##g3hH-s;xuY$)`8zIHgNjvIbZtbWVv{M"
    "{qFsBa{A-h+t=X5qB;mra=_jB4Z4WGY1fWrx1&P0(ZnRIGGOP~&R8i(kIt%9FX-JGAXLE%TTtQlz&V3Kn<CT?v?;"
    "8XL4mVN-sELjBk&H+?OnE1!FY*HLnV%Z+F=<ZsU;SVT^Yn`6_qr@n>ZeNMnY7?M=!Gt;m~CYzFwg+)e?#*ce4DxX"
    "CzhhSk{6IoUdi>ylz$-Srv7?L0uyGA8n=)tRN<f47?o7C0y;Zzp{L;Ab*flM|epv)WNGu@*8VSHK+B2@OiP`w+dZ"
    "QG721h(pDhg&meDHrD;>NvL}!*!D`SjzA9$arCfTWy`Nhw0<E(Oa`Xce;F4oUWT5YlAlbH$-xl9(FLk3NKEVL;+w"
    "<)qJ${XbkG)C#))1z^OUn|yHe)SZ*IT&)+iwb>f$p*;N4CJX#PYGrWgA?3=>`UqBG}pXP;tIb!rG!Zrz#cLZJ~sQ"
    "@ugSCSQy$gnAoE#3~6CRWyu6s$AQQQC(<>tq)g=!3*HyShIpQUYA5NOzIu83ZI_GTV@5d(QH-xGvd`h;1EG{_kry"
    "o2(aBp|0z!F3s$UN)l%T*GH5sF-;baAqII;MLCL~($yx7zt^DTA0Dm;53l!j22PeqPtj^Q6F85TiS19En4DQy^m3"
    "5>Z#IxRCg%`7PfOKt(LC~hH<5;cQ?yD+sTT?}d#r#q+bJzAtq($a|j;N(V8<w_V(-!!O1R(FA4o&3PGF>Td5Xpa="
    "ja5-Q`q?p@<zq9e|45chOm}PWLZ86IY%g}Rjv3MWur|h1vz6v5@Q%<p*urFyBkuXM$DHxS?q=6uoRgONdYEwR7c^"
    "4Lm$#gZH9)-C6%vmuAc)`{i$jmUug6qWXBR6Vjnc;o=Y`|yRW!xQ{O)|>xi?6oGxINs=O}3L(R$8s7C+jVaW!2nb"
    "Xmdp@tGq3^uzxceG!aXiXbI53Iq4}G%{qowDw-SoI(4I^!8U_Xn|-;nicn>1Zn4Q6L_OElo&PZwUSQY#y4D*F#n`"
    "xXo@BrAp`AS_>(Cy(>XOFqYA9@*x!&MVk;?m)Z<0ARAx8q0rZmSq0dV-+=laFv>$CHd%fI=py*Yb3LeFbp#&CJM?"
    "qbJ32bL-{N;189snSfhVtUNy6Vy~!cbhs}4$4(ss?g(WlDBvtk_eof7xl?&X>J5XYk-MG6I>*dYL@2ntc*C2dzvz"
    "oDBKwR9IG)cXdOAX>mpH~*J_4=th5d_1!xKV%|;#0as~qi4?g5-;Di*j*`|a6M4We&;K7k)%BJ0!AV3~o$=n_V(>"
    "d(^eQ=uUB(1@EcYI75Jf(s_*}TbpLl*)lN)r(T{W9H#1INq;@V;<<<MiPxm59NW@VgthnRI7OUa%t|8oePc9irIr"
    "3B?m?Ta*>Vb<*1$RLmKrzXv)SWj^uI*t3xFOvXD9U!e1IjgS;M*-?0B*q-RK2-viQ3KwnYsL$(VHp{>!wKMYJAjI"
    "-;RoW0RY)9#`&AF;(Wj4img!Hx93@2ld`~?y91TR9QPc)&zwxK4?!fA4BSyfEb83Zoyl~{>4be_xXUZDX4rdbCd#"
    "Sp+1^<M_UKpdq&1>fX|tCv=H0uc*&MQNF#1rH$ns)Uc}5|2ib5NQ}il#VR2&w$cYs#QUt2iOPZ4CG=G8YxLqsnS4"
    "PlIsDhw-Lv}fkOmn6ISB^Tc%8FR5$v(<dl<q=v7**;N5N&*?gWVsFp^rqfEF?S67c4eGio0f4Ht^k+z1?xJ~&Bjs"
    "!_~^-psQ6e9U%-9?41U5zn<7iBx92(Bda0JOvPW{Iwj8qu?sJ2=Z)>im{zmecBlevo)_56QfktF8|E<0v(^M`sOS"
    "-uMSp+X1xKh3x3bqG?q<8$K&VcYWDw4Qb%QM4OaP5{7!pm_>yANtT>KTc=HV#^?VMjqK9hpfu1%Df{I*7;qo!*%V"
    "QSUc)D-V1A{7o%`<d2PDsB(R+V>es=zsri7lse!DivvC+=-MX9R0kZg=|aF3Z5%qbXKWS_(1qD;_5GzeESPFrOxr"
    ">u%;f|27p5CC+B<U8X6(kA#_v1PL?RH68y<d)Rk5|fHPoL&ET@%|bPx@EC-JYnKXVkc2(szbG?5`Q89q@kJBF-j}"
    "}v9XKZ)=JUm7CMz+gyw{n#vKsH2*WUPked$VE_1no0+HSZt~lBp!ONhXN`byi!#lG3WExFB!G5L7K{8oo75F;G#r"
    ">oY7VJZcDiwOiv)jCYlzk9T)sXPFNRtlQL%9YSU{+p)PEMrCs-3DWxDlax4}GeHAL*K_Fn$%mljUmL{hl;WS4^=S"
    "3f%3Bq}ryk66jr$X<4N6rI6d>S_BYI7z>090>wO*$3S>WoX_hj0_1bmd6nt3D$1#VzTq~GX13BI756%5Texj|gw@"
    "iE?h_lp%tVEBy`F3eI1ut(0)_9oZbcs;;P3!nON+M(vm?;)Ae?VlH%eq0TI(S!OsZ20x918Y4`l9jP=g?^Dyt@<1"
    "0D0p?)Vb|E&WOEg$5@=;JXZc3IM97QSfRMwKIlwI(>z@#p$=u{~(RzMS{mysczG9ju<+{f>(Or*=Cj5xDtbiPUku"
    "_>p6GURZ9HyFvJ3EN<-A=I>W|7FD5j26M+&eKrosWokm^cR!&4|BELA$j@#Z=Ca9__=vrcFUM-53-4YRs!M+XL$G"
    "b!a2N9SW%jhG0hBrf1Q~Nt2?<ur&P_jIbfzq0|)GU!4E4i2j<4sEy*;BwfhKUz)gL86d{S~N`Bp|h3m&NC7l}6yD"
    "UhpKw{5W<3Ka?55sQ}hA$Gu5lMFde!$j`9l{Zqa!uzb6qIxHB{bQ^dKA{y<W+vKR0VT^(M*v}RtB<3Y=*NpJ23RE"
    "LR?EmAjRJqKPA4YF3E(sWv6)_8}y+=+`PWNfZSS@*KHIROLsT+q=xojuc`IaN7O8|F{s%z?#a2~MoO-jpb*k0LQh"
    "JjH)6%0_bgvhAK$RPotz-2T%GgZq>k*2=GqG^!EoC<RC_Ub|xBz0_DIUkf>=VSVK7BNy>V=v>lRvuoam6L))HgQV"
    "8&|Vb^0j~}WhmQ)M!od^t89wBoG;aaEs><`)qz`<_3Xz>n&Ow-6&dDZ~&@-Y34kAY|u()zbSKt{vtni8Cl)MkaN`"
    "kG5-IHod2Lct1V=8H7cs@MYv?nljTEnF1a-f$#yuCR6>*)2%Hz#LrN3Y2-h7XNYFGb@2qNGiCO*!~-TI0dNg~OC<"
    "QdF@#jEn{a!>LxC9mAos3(?vzpyuQH@ro^F1$J=}lU4`W@<0GoW>mb0>_u=kRRq70v)@_c_t)DZvTUr{7sl7zLhH"
    "<q<Up?Q)-`2!fy9WoZgdr%$F;YwD6eOi`VDw#jU!8|+r*=#jar}kk!5GB48KYrRJ_ETp}`zVL8+$n@t~?YEt&W%i"
    "V2DCtTbD0015Vov{DA>t^wB((_A?QHWm!oANY%_JY83JMcsCD9KP^Ha-H6*+&)-L-3NMW*zc(0Z=}REf;Yn5s<I)"
    "HF~<&bF^n*0wE=&cm)WAm(>&H5IbuC_ad1B-Z!EVkab&~E0LCtbH#%9gLDb4XgTabs-toO8y<?XYnbf=Pu@0TEnI"
    "3Bl!LL(3gJJ((T%j(3fpaa3!9Yi)<W`Y2!hL8Mzjca{J_Ps$ln~AjnYdsIlUPnutVIO$wiBDId?+xtN;Om2n&=5Q"
    "5Y&@{BG#TKv53Mft+hhZkwbs2$|}PXkxx6Y1!FDdg*gzI>YDWPL2{aIU<f#&gk~7A^MUmj5QC$bpIF}@%NQpSv8D"
    "l{l~YG7$akRHs%nPajWs6&ghq`66X1Yrada%V&xwW^#vVklN4*UWPCVY(WBIA06Y+b--O!D}m|~}Uk~BF??5J3$&"
    "GBhrAaX7eX|Nu0$Iy}IPet?;JGuqWQ^tEp=h2vEX3Sr=cfI*XdX@O^*pq<{LN!1)YQWIO3q<HQT+lLnPXi>>a~X<"
    "v>qJS0^g>^csQMp21DMi+X=~)YYxI#XZVtZGyS3t}7>vgd(HxH-kCQL>)nntW|0U+fRR&t-=tc5ZwVM`cIX{DuD>"
    "p2mu69+eR-?~=4pFM){NmcoIqK`Xw&O=tGqB3Z2VdQ1>$RL>BF#aWr304qbwu|!W<^{c>(he7J7rzUfx#|9BWEq&"
    "43+T58m&?ct{@&2A{~HWy)9K$=_0qhs0Ya#Fj0X;qerw@6^>8zphP7(s7sXuTcmS0)#}Bj1{H$czRP(;oWF=Y<s>"
    "KH8cZ0ny;NpUAP$XZvYaTiUIaiO*4*W&e|d6tHF|w)v+R+90HHPHRl&1eKUH#~8)nO{bg+z33?!4rw&n3<?H7WTc"
    "aT?cpDmZM7CTpGfBEa#+qYe-{(VLVI}x!!O$PZo3{ezxHsf-==%UgfA>1fy4q~Ox74fh9|3<da(Es-nY&^0^-wxn"
    "sZmuZ*iaF6Y2i*avj^kQ=t~)B96^IXgbFirw{XYgq){EpdBu>mN<Wvhyq(Y2Aa`-@$oaQ;fkQKVRV+qVAaRptiux"
    ")CzkH}x$?<aFrE6eq>E)gRUKd)nsN|oHgdd9kT0yjF=ejN!#YC0UN(xS0m2sK$9sbcoHf@pQBx>&C<Vz)1Y|1V<q"
    ";C4*Gn4EGEJC)r{cw#6oi8Xow`tzt(blghERSotD1yXdGFCnoQ@n-^T&2a!ZF~BpJu8B51%aaMOx=9xV5NEkjm<O"
    "!QAQC1vGSs<)*=7uiz<NW2mvGwTw$O2c5s1vT=Pct*JnPGyZDiuRA`?hFRN)*9HXzPaA-yDtO!AC#f}p~@yEq1o)"
    "f!jmn)Qu`F5@wjYKif8Oc|<Ut8YT_QW<fKG9<Z5X{bW~m~$9K1F*o0n&x`MiSNV0#<7w_ps7IDiN3K8hROOfD+7&"
    "qba}%d_8dhd45*MzxZL%LfI>SzSPp8QCft6qjUa2oZ|ET_mdrEQrBj!Jf*9YWMFZl2vdAHf!jy9$X28-6;hFTZmq"
    "LRTI!9N~u@q9sAf23f%C=eVo0)MpkTyJt_vIJZow_A`WHcP9ko0C+_blI@*Q0K{jcgH^%#9$>CQ&WG#%#A(Wr;$X"
    "xr|DaQXam2{7KnDpP6y6TDKb3l&n!WrrOMa>_^S<WZR}D+=$iBz&I3BnzXltNFk*M2DokwWU`R``<4}Yv)IzQsXZ"
    "o7#tpW0fwPRbA%#@S$0}-mm@|_l2PRecvWIeb$@nm!IZdq*owGIAvN|S%!9b=MCD*h}^BHjG)Sxmq8Tl``2sUmKr"
    "O85VQ94#w*BxR_`fc%n$)#ZvtWTChkpMk#va4#bS+=<ObcjXALMVkBIxx-hRH&21K2VARqgfU6c~NV;@Oy%zhNaW"
    "o8-%H>9Hhs2R;9P4QX%G@7ZBlrwwE2j_$MFO5)?nLOk49};T20{nfiz)kx%Hvl^by4CL2c(H`uY656G&@su{(FU_"
    "$IkUvJ8F827OZAB+7PGk-b7jdf8mMf3?!#ceW;8;FLfUJVvAEo3syv+7>E>n)#U+dku&#d#x@K!@mfrPx?TVP$As"
    "Oldffit7citW*+><|Qeq6rDP5>z>TNBp!oBg!Zh-qH5@nbY+|u7y)Xbq*&Y>SWs7M#6?TKaH%F){l5X@tGNZF&q8"
    "^>_w>;xko{1iX+{qSw9@pbZWAfbR~WQ=joPOew$F0hS(tWxccXr91(!6s{Zv^*%x#0exH;&2ai;sRdz_Fd?Vi`JP"
    "3`{n*xK*C2KMuf?EMq^>l@5ZwB}ul-W?||?bjxob6DnE>E`U@mO}}UV_dN(w0vxyC|zI4=pV;TUaR--UIT}Pr52<"
    "}M}@~6)Kj4zz-c9sOqZyO5tSAN1h{;PK=9e5&X~L$Noy$9aj-rcun%k!&Kw|*qlDE-kCVgz33=(Hfw;>ObM@-VsE"
    "E~ODvmKE*bofgPRb`p<F<d1XpRqoDUgH?!`ymtl~idypBA4n3t#DL2J2ln9z9DD6+maFN%_shUgr}&AI-U2H&6qv"
    "5th#s$r8~BX*%mo&2CFnszd?M{0YZR@yriDjxI-F&B05r7{}n>REe~LRWF&~8l6wrSBcqLz4+lO$!@f8x!}Y2RUl"
    "3cZgoktbsV<0s*Wxk@o7%%@NYpLY9!at+l3)BYRU##?pg=2-%sA{>N`}=G0Pw3m{o$h+|+kmXyIw#ac``r_|gl}Y"
    "_gZj%K=D=De=Zemm=fE8HQ~%wW~mDiG@)`B0<eWrJ(u>FpoQ0c2<zLC~_3?PwbW0jaq9~3Adve0EXJlfp~j>fGjR"
    "gMgJT(rKD)Rec%1Xb{wnK@C!8Tl8w>NXQL01_rjX3_BWdn+ws@G7iVPs`ftSzM_;Q_U)x<u9Q*ZqOYOGu66$Ovx0"
    "6v8#K^VMrwISari7fc;d2=3_&Buz->*j35@Q(x0bJu*3W~-1w{Kf2ut?k@uil@Nlk?ZDZT<Occ;;Xy59XWIy0WXE"
    "R>fQ`$MAIr{v6&MuoeX@NT`brfsN!>;EEG|*=F7EX@M6ycVO;t5(j0mofR8kLm4KoqLK<xhw!d8Uei6LmaJG?bi-"
    "eqH-{=qq!5CWNl%*AWZLv~r#w)b<#bw-`cFQS!5&NE+EI?2j7m2LS^PCENDf?9sWWX2x<@LM<f2CP`@T}t-l(H8Y"
    "4hAt(#jN*YWWDEH15s5R$<uLyoP*Gi;KyekB64xBOAB9Rb*aDp<v0PD<L<{zS;1}oahYMbJJN~0oZ_-Q3n0y>~9o"
    "k-zW2eA>$#rFWuAyR2iUp)7~wso-z<DV_3e8cSl2@n1~uld9~SNy&P9d3?w%PuP@F=QKQUKSUSigg&GPISK_~ok}"
    "Gzk{Bjyv>oq9LxRr<YAjZ53i-H%yad65#k$@E#7CGkFOa8u5<qpG-7~*h?mmX9(&t~;8R}|;sO39;6Qg)+jbQ&kY"
    "^-eA4hWN<KS&f@@l>QH^80vIpic6beOQ#t)HYZ+S0R4*OIFF`afc=UVYigXD+-W?f!1Iq0G)k;QC_sv5#hRl6o+_"
    "D$=6{@UZKPcr02ffW%3Kgv&Dl7l3OLFKHjbNe1JL~hK4g9`5wkAZJHl~eT_0{Om5qpy&bX9cXWmqIa7om40aYIb%"
    ">UpYy)6u|sh(P{Q~o-_=C9&0=3AMd4DQ-jx~@+;iX)giG*(;NeX@SwK0nlDxjx%Z3gAqNG%&y)oRD7FvWeccK0}s"
    "q>@oVcHg|4I7xwsd_x6o*J)mpLtg1VH|M>UrKd65nKeex=`MjlX_-pq`bF}9<TxZ_+B>w$Bd=#E=FvZz~;gD`*6l"
    "P3ghi6f%zQBr%9wSqT9{9|H!aMCQ=p}3j18;ajW+tkwSY|80PC9)_C*s61m8>*1>`c!>u?6I1Ze8PB^ud$>$nyxu"
    "D<vjD35hO###i$a{RLIP6iA14&sM1cXyR;K!%?rZ4ykRfx865+kgckG9BIfOU1EBbSMgt#7+<t19V7U-sCxJN%}I"
    "<sF9xR2UDSlD_@b#0)HqQwZ8V+Tp+aQz1&o>*e>zQk2&>6yGFxB+PRWv^yU;kSk_nrK8r#{UB@b#XDf%riRMJCxL"
    "groeCUPYnYbBVd62Vofn0rEJX@yoM&N(e}hCY?W6~iS}E-xWiJN&0u8*FO>kw{6kqSRC0Xab)$`u(XY41BKzmfNX"
    "0V|P#)s{|=&DvoU!fu>|PW`)8SCsl@TO0skOluEal(dL0@VCxEtn<GgPjmS*VusIXM#;EQVFb&I)O7D`asClx<VT"
    "`ag7B1|87##gPy8Ii7L5+!Pms|!pWE2bUNom+lSC@4Bx9<rEUjs6%M4xCc=(X0DwFWfF-5yutZ*oq>)A=n?q8kB|"
    "U=TbMFLOy56MK^OE~v*G9F0;v5ePM{PjZ!Pi@bMpz`_diRLhN$Y`N2uw{MfHv+Gfa8Y}?uNr#>mETx`5HFha%kT0"
    "9hyXdYU1{zEORXEO>m5q0Ka(>Kb+{E!dMR1^nvEHekws^XTLI=D=5P&1hd&w#alMMHj&|&&Hg<~+SK+s9Uwf3fe`"
    "ECCdmQxA%Fw|oo+e8sU&R6JV)`WeC*ahUOfi+;6oJv>dgOBI>`YrLigNPvr)(}aB{79St$pJ~^A2j)+>T`x^|0t("
    "XNJVO?C1G``ZnGMY92mojtl1dHY!k?UMKjCrd6f6UeH}oUkGv^<@jJkuMF=Tzvhl#c(cq)bRL6@Jq4PhHH#E{S=2"
    "68>ncr7Bm%5W;qBmBXmbg!KL1<QYk0k;Z8@04l{WPEVE5+PS2x%s9XPg#NTqLge!^QQF(OqsFkWvGU&T-15LzG~Q"
    "KWAp184m~pyWt_lFIySl$-L+nYprt`8RSfG1jv5dmqXHmBfz?B|3nC;wXGuj*DL|INXHR!wj*fXTVWaR@h_@$c*i"
    "gCOY5Y%Ie`DeIvtIUz^j=WFuJ3ze!_G*NslMhc5q{L^1MhUz_<m-n(%nQ952%qWceOTE+PF0c@ryTfk;>(n9OR?I"
    "C>$WfWye72B(tsrW*xMIYB|<ViLdC!p<s?ATu*MgV@DW(Rq(+6i^81JI#=*xNw`q9tZ$qE!P77uLcG3!c<%qok;="
    "&h%K@PaCJ`z(FrhYX6U85H#urDpAI`PNq{Qd4tQ!a!;cHKRl2L(OAD-rGOA5$R~H{Rmu)gHay16IGZF32prX?*T%"
    "!vGO43*%gg0_i-vQ{VOu<n}8I#3qvm$yPl*!nF1F%F((R`K{cFF3kW!<%}C5(o2Q{NS3R`2w6gR%gJDp=w0h2xU;"
    "u>%9ZKx?7$b>^G#q9~g!Va}e^djM=MrXe*=_!v8jqMT;)F+6BY1C%a1b}P=V?%HehMRFl3{^|QmJi4YJf(OYJl#C"
    "&|8Y(4s8Bl3ZoTS)d`f`ogm3~b)>xq!cQ5CrcrviVH$Oh;ze9MxV?MI^b!q}FxAYSN96*Q;mMdl7?IA%?lg-94R;"
    "*qY@l3JhcSkk!=Z##G)yEX6;Yj$qLfTful@Xn@U1*E|Rq${EMP)@scgK1T5R^TwUJH{}RAYB9ON%+#*yK{Iq>xJ!"
    "RWP#b=!4iuv%xvM_+-%kuQ<5K`^EWKzu=zoehsnGBW+>B8l<oyCV$pAgrW0R}hWoSqx?h~fW%EZ<BnC-H1QiZ=`C"
    "q7qd$^n7%B=E8iKvu~x#~zM;#H5%dDL8+qyB}#d)6;cei6iBgv_%nzdfwlI_Ae2@uhbyH{cj?Wt-VW`_Ne1msMm*"
    "?VGWigY&{|2SL<e?BYG305|nmpFQEx6FK9u_#8kCluqR}mma3(0OABXIh`az*3`9U%)-sV<;Im-46Y{}6Y(Li&oM"
    "xo9O@Y9-XxZrgR9Zo(dl)9YNfacQ0W-6uJPvb;wPgAP&SGqWGFQy=vBwtV?8^IqdQordUlsCmp0PRT+OnIL=8l0K"
    "$QWvcOXEJVrDM6;S>a@kfTFYc!zzm@unN{<a+~<&4;;yEshy)50Ksx;Qd01GX2vF!0Pzq9=Zp4&)4+%(3R-Z&^m^"
    "_Yt3;j7gxjZ;P-Cw=40p&y(iLnGRLJ_RKt&e)lnAPj})5zL>S$0wr4r6C*S=qvow@H0vqT=^wdHaS3dlB@peQSMN"
    "iXLEK`t!V)yAX*g68dwNjM3sWp8Ja1R0?DZOmnAxLj;Aq1{}^?J<gXXCUUYWyjCu{r|IEK+xs9)CSf^vUVz=-suG"
    "@`mY#rj6eW&DEzro}B+>bTz&l{mc8&)%EE0FL-j$mZKClr>q}G!aPrrH=N6Iel@zhPR`D+FT_ghaPkH!sn$jc_fA"
    "jGK(9e|OSHt>72V|Lleh0jS4rp3y~O|jZd4$5nrZ@25H|*nqr$?To<>O#NQ}lS8aAKTMUx7H`MRB^biH<g5zE2r#"
    "#g{E&&t`8deEG9fR7!BsvMn9oqi)7GiKefHLHN6&%+Bp*z0Y&GneA@JT{NZSJ`l2R_w-=%I6*J`mt9-;@WfO1$v<"
    "6+B$3UMLPcITCLBE$#UR=A7i<WNRc7Y61tBVAJlapLHPRPDHutYn2`4=@Fa~$Y>>$>%wG(1`R3vh`4Z1hej2@Ib<"
    "dF5_?{Oj7QotW^87RW4S5g*z;pm8Gg3r(^6o6Di{jp+Rw5{BJchtAv(C`UOG)uxX^?U<A<1qeb~!9Hu#qIS^#u1;"
    "XgD)36+o1yIoS>XGXTR49<mk>$6o(~$-hG-?JMjzPLj17dZsq-uS!50$qQ>BjD=aV+P`bkr5z(Kqm0N(0s)ZV2|*"
    "Q@W!5MVcIT;zc}p55Ddv`4WV`i2LvL5gX$R3f(cv_<1+KUE%sFW7p`J4Zjte*1q`TeiBbE1O>t=PIhF_shE{pGpo"
    "B5J4pZtxCdx%PdX$OE_2y=(O_X(NV3iq3KC)Di;0qCRm$#Ko}iAx$AJZ8!f%p1Y-88#*zstHP5;1C|iLUM%kLzzM"
    "D0AhnGggABs83w%6TDGT*s_THX#=6x3Dc2bX<R+)IxyljeBA7%Fh(M1DbAstcCze($FX#(W2!9@3p1t`Sq>MyOoj"
    "|elo+b)ryv=SSh^*HPysorJ5<!4tt#!?)V?)z7`o<nqSeIZBf7F9#PF4I!`;BfS%SXOOG5~Jb5GC*oe6o8ITEp6;"
    "1lS~dvb5=y&9PhhLiI2Qh63oo7!5D#`X}oQ5*sENvUxRLr@Lj5&OM>~B__YjY5@JERsTdiYOM97ri+3kOj~3`?~u"
    "iNoP2D|j+W6!Eo)$==;naE6ZC_2RRHG^j0JyfS%8lXu0Swutq~5d^6lNns3qw6UVn}YUv@EgE2P<t&^R$|ZV0!Sx"
    "@8(%!{1(uzCq06UJXB*NeG6{A1L3-9_lZA9|!txhT#3tQyH}0eYTPQA8WYUb4uoG><D+}rpaIp+!H)PJ)QVxUcTG"
    "VMvHCxT=TYlwT7#<5&Z=!+XU_jHYl96Z~ltt7~rQgN$P}eMQ3_dmrx<yW?4hPpe1*Bk05fEYQyiZT78a3PqCuE%J"
    "eq#Jjkj7?7Xy&-nqvdhs|W|@1DjN$&-J})*WZ-%ZBUW(9ddO9*aa;v=exkjQG!n6$E0)diqm<7N0O_Pmz<p1RK)J"
    "nUkbpU6BxytL1oU=m*zg%hfHl*@0V99#A(rBjta<?DWLmL-Jgj&xaoaqXygpsD)6-A@SP#)VPDPdJO!i!y_u_wnv"
    "5bz^kTNWtMJsE;l`ahoe=Id15_?rCf;O@T5`uD&@#ilq{X(DJ#c%B(E9k);-I}Q$_aG$Jz#ni96U9Wy4x(KW1AB("
    "4KXchUcjWj85d(lw;67VQt;8F#;NkXg$v{+<18IDXP}yYwI$4g4A;wd+MR`qyyTRNKe@+ubL#m(f;P2Anu;7csyY"
    "_{z4zJxCSZo$T|l{8y&MWYxFbczlx-Jk}1YzT<+Mx9Zwrh@oDcD4L1j*1YvJBtIn%HXU8QXtE1c4OkLFJ63dxX-f"
    "2+xV+BSruQVHRfm>Spwd3xuuXImyh6JTDfm;)47_|>ZyB*V*f79_~oq*TrLFF0Mz#^`p@u*LF1V|+1qnHYa&Zj;+"
    "b*@$gX8&2{>r?@Cxv8*7SAs?lNkhQlMd?$w8&y@RLIQ9eg^D?@mdn<3IvncbaFoE2@hNb7&Bu^HIHclOHz-n3a2d"
    "BDSOS;|XZfp+gZ!Z<d9DZHt*#fyBuMS7dz{4(IoG`R0qr=F@j|}`!JOEm<xREQv16ZW@y@UxzU^82{qXFSOTL)r{"
    "a5zKr}<a;;rGf6Yhr#~>2Z-a`J-(g_F)w`q|Y(!&ouWM$zW$pf2O6;VdYwr$q9c;4t5(w-F1T74sGGwnSbwKuN%N"
    "DuA8A8O{}93=cwgX&sK!_#bnDm_tK*D^^z|sDyPxrq34!E2RIpORU-5@<c+insy*Qrd$+-@{+=`ILaub9HL*2;E5"
    "O+f|L&*0Q9rMr6|7+HFPg?d@TMmI_pD?u1~|dYF2{|<>0RdCH0Y48W8WNbtS~vdA_Sw0OVN~u$>Cu)xww2ix=eof"
    "8}u@pC$C3Wr^(y1pU$q6S7EN0H6@WWu_9NUa3B91dRrdSWi|&@6P061YND6L#3s;Aimi=m?TLUOZ`O}%KWmy-1?G"
    "9qbk?8TbMZ!JD*uPgsh*oZKW}DO?fg%g704E^>R)^R*%Kq@9?M9LWg>e1f6|`&FSdKyRkP?Ws_HU2IZ`|oQ%LNMl"
    "Z?<^jEYgNjB;Telkb3f1CF1yDp7A1b((Usk@(#FI!LbYloGWWpq*@<a?>H3wAWMz5E+t~0!u})Z7)rw7sdkdm{bV"
    "B3MXuiGz-WY!l32`;04|R)deO%zjHn1=V=McCBFrF1?)YRG#r2;r@zr?2>jbUfx0W^m=4H}<_dcDy>$sz&|+90er"
    "Y?2e@Qm7y<zOSuBV8z=ZG;c2iZ%04NVb5%L8v^6>O2gt-|a#tl2u~LWXD~bmib7U2dW^<gC7US-HUmrlGddKv-5f"
    "uCo?l*|`5A`;JvUqo7(66rmBydtIDj+PqYC3alK=JisNpuJVIgWS=U9^oD?Hxh%i^o-|vhoC>!wZI0Ul)zT7+eJ5"
    "=aXwtGqEqfGekt)TBcQM1X`%8;s2C?Fp*6J3TY<<bzWq^eV*>nS9%;2w8Z3{uwkOSV7i-%{F%NQdROvVfdk4<MCq"
    "!!V)KsBg&G9jr~O%kZhBwaVl7pg3U8Jt?j4fT(ZGq2CCuFuX-uRV@*DtTZ??AY=A+#}eNF+6o&%pUiWDZ(WDM|+N"
    "`Yh#EI;Sx3T%+u^N_k@}LKqes=YHKwEy}(-9Jlhb2E~=_8HEsr}h6>FA_t2X35wU^Ov6fW~R9O=pl}jhZl;&vSRn"
    "!($1X|5;LqdOu<>6eENDx73o}8VFbd|#cX%X+z<)Y8vK34h=B`V<o3*!tV%t#V3XHxS!;`FwYN`c=3Db1kP3)sMk"
    "+hT{_HLM^521!Waf|6`NR2(GNTkx$E<s67b?D|Nm@+VI<QiMPRoZgb`W*!Rs33wegvis!09%BV!uals?HME5pQ<R"
    "gHj*dPj;}t}n7V&nO{k)h_C|;v*Kz(L0Ex6uU_|sB;Aiv7@HsxB+PNAI(4P{kW<x?z1>JpLxG_Ig{9x%g;ff<~xV"
    "JTKMNUr|nEh2mX&IjNKKuwpR@T8`}W2k0^>D}HHSQ?EtSiLK!SzRJ)708kqf+7-l2%cFM%_E$CYK1UGNKsWJ`DQg"
    "m>Uc|6#H~_eg*zuba+wnLYml6nMS|tb8q&#h#qxgO+aYL9g$&wQKv)p5riL7vr*%4o+W+KADR&-U5}RK2^4p_tzw"
    "00UvH$IN{p#<_tX6#<xjrB>(8%@cJJpwg8?5I4P{9i_EGBPVflMMd>9}FR?mjsy3wLOXT6kiEg!P=QeEV?}$cKNl"
    "%>&sTP~j`07DuP{6-<2VEN^(iHmh@m*(Ss1CMfano?g5^zwUg~O-`<onN;wh_8d<hqA|x_iNgof+_Cyxm+7qTaD2"
    "X(9R3ftIQOvI2s+&Xl1^yyaiC>COrmptkj4@<S$R&fyzc0+`FL|M!)g4d<S3#y*|Pyqd>!aXcm&&**(a=DrvH59>"
    "BC)N6ecj&1O}s*ydGVi{XBY2^K$*;D0w@2{g=_Di-AF?Bh|e_4tQ7So|y)HNDCXjA_7Iw3~$kfYSB`Hz`3knNWFb"
    "hfamd9B1BfT&Z*;UhQKxiikBzqTN(y56a?((_-KN!pQv&N-_%jW#wdy{0-;v*>yj=Cmde{AB|b^bL(iTVgSt=^n-"
    "V+)md=H=$5l}F0!8Sb@vvTQR(Yj?L=3$3KVMy(<3U+(kwvLgmC9>&M%jlLp*jG?9cb{-83O}{t)r6z)RuWx3%Chu"
    "Ug;9<hIp}!HzI)oix*CPCPpNaEstw?ZgfNs0%eoam3X$2+9XAo9H6+*VG-8_AVm<?)^wMoIq^i-MX_u@(SCt@FGy"
    "TrdI(&oLa5Pl!g)r8ciioD?XidM>#FV-SavT2S(remO@J?MXNxj9?10y;d-&KC%{#G-)_}DfA-#aR&OyS-06Om1E"
    "Z0%3*aeP&5Lz(aqfhdPx&zNQ2G|uXM&9#hh`R@rYr@F#sL2E?8t1GgD2mSr6|o1r;pX5vDh2fBrz~A;AFZXFu>rF"
    "xVd3}dOqlAI&zm!A%z2kNgDp?{)kYZ$3BS0HeC%1H%@-8gkB9W@;it#{7K7f#>GOoqzP_^oOJyqx8xlXpANZ#C|D"
    "dxC*hMb<uW$g;$2D{Km}A4ldVcwszR5m2bd1Cm^xSdQsS5bgUbP=pip>>ZDk6wlWkM{+3Hq7g0T+u8sBRkfqSi#B"
    "kumbv=vqCieOitPi6Y(`-RNOuFde-Fr@YAfWYqx!Cpd1!1{Sg^ZVbJAn(u>^3<r04jtLL9o2<H{@CNq|bM(+tcyq"
    "w8`8;-%y+=x}<Rm*pY3s6B0hi<;`RC327X1>N*&P@4GNGJtcmwE_Hsy)Acj|G^1C-oL^y(+8tU?c!kcMZq#o$VC-"
    "96mwgyX(hw`e3*ut`e%%vT*f4{k-^dZVvKKLL;-4)i*{IUsh#O<v)jQK<fG?%mZdHns0Lw-*WN$OC&_9!HQttUF-"
    "D5~7`B=t~WnB>L2pu;DVMmI<(c0bo{6={eVq0M6)SFnBphDs_tkM^Losv?`WRT#l%@u%<)sMkLd;2**`5gOHa8iN"
    "qs3&j7Ei0Dn~x1<3{dv?vMl3?>{@c%uZPD6c%+Uh)aV5XW%^8ODqSXwYfC+Y;0#Ldp`c?ZB_Ls_$Siqzg6v*CNCG"
    "m-VLp|JZvM?zW92ZTPSBD0_~{3`onl?F=)VtRgXq-pG<ylH;9E)JH-@Q^IQy-~gaxj#mHuJ$30T8WbfvnZ4xXoLD"
    "4*Mx!s)RZmqt71>kKG`3+V;Ld(pP2f?T?(?~~RQ@-fqiWv)J%N7y1MXZUvN-}tY$|L7yjxD#QcB!U#CHm(vc1x1_"
    "eC3P5RG^At@d#Q!ej%@7HAwapzZOl!E+YGT}rI;vhq9J%Cr@<JuM2)5{`hqe7%XS)3P_=cgNhcO*l3-wT5G?%6^z"
    "@QIjk^QGEtUGEXI(0c=>NxgT54gp7TgjKh$0_+ziG4zR~4#tiGr_WS)1>QJDyW0y7k#rR^jZc49s`4Rhx1{riBW-"
    "Qrk1KiUSH<H->N(!lXPQk13&dC*cjx`nXChoUwm`a!xwI!I7)j&6xb5D!uCfO}{Qcz7v=Ptp4ivCC|aen%CBu)>1"
    "{OP<AzG)gayn_Vl#~4KlBd<+kK-a(*Mdwjk8@SIVF|ctz1>-GM_zN9t=*l7IU0)pLRSj-gID7_n-(K}WT}@<}Qmk"
    "kQag6x5cGz|;lHG4jb6@mr9zGQ{PuPsozpcx^?2FS;Z}cCd{kP|%Grq&6kI-_-EqrF$_{w@Ds%?pja)ug>$Wufhm"
    "Pa;iGr!<jZ4ok}S4&r!w>t5))d})?yB&cXSR}emWHl>O(k0p5P3*o-AFSFWt6Fpj=VFpI+?6m3U1yP<)p9AmR4Oo"
    "RWLzZ+VCgTbzE0s}=V`nG5RXMaa?{6NH&lKag#tl|={T>YtH4$7)gi*+!PmHt39(!hZry`oZfQe(aaKcJjH*D@ny"
    "Bras7Z{BGCOAxzxOe2s+BR<1&38N0U#`{HmTSw0bHUEOD=3A>QL8dq7M4v=_DOb;0^vwIfLDSaIk;fzYxmbaHv(y"
    "fU2#yKtW`%{S=7LY=a-wm@DuRwM0e%ZsJ=YUXr=chU6!){`WC^64#y%EG3Kb@$`fgQi;}`FzKJ72z1;l#a-2X@^~"
    "WeR4Es*F^i>a#apdI>QM>)iI5X0o~Wszw;8XTT;O4jmM4#lN{`{A0n=hEfkUlsvEcIJsz}xtM8F0AXwh9sN~TD#{"
    "zzLxCN}jYH`q2{2h>jxuR!`w@uq%<gF|SOQlBx8PRe}pI#5e<@hI3VL$<UNQ2g#-EJKMOpK*0Vcvq<5E-6Js+{ie"
    "qZ`N$u)s_PYD$^4df|eHq^;)7@9r8mzr&49C4#Y-kACDU-K$EZ)-;cS?a$OSRIiyH~6eK}AV-M)eC0*dx=%=+@RG"
    "qF`yKXwIyS7d1Plr_Z38#W4FuJ66V25-e2jc!kBwq9p4=_*aK5Ui-GO;MPLP{?d);T_Tr$}C7U8^7*ctC}C$Rmgq"
    "JZZyNT(D2c7~4p#tbkbt8<A0&Zm={9Qdl0{GpEXx2iwoUPj5!2gdWNa7{s7hT|B$7a3ebv)CR?vSIiBKRY*7u3D#"
    "Vg27`R<%A=o|l5Ayh*CPsh%DzG!io(^QLJXb*RKx+ou{b)+)_p$%<utv{bv-6<1Y@Z|CwHrq_!Q|z%TZY;rgGD83"
    "Yw94`0k$^pPwFn{}w`_#VLj-**9B(N=gc1h?35Xt9o$!;dex^Zl&RZMr${QQT1s4=)5|daz)%8J4h169-93EInQP"
    "7jLTJ_st>l%$8jwh6;){lKo>-ED+3Tr-WTsUdl&ACyaY!-@L#0)jVwWE&PwpW+wD=}0C3EMPK~%2vMt|93AT=vRm"
    "_m~JVoSunMpW=DVoB5;k7vX`K=BnU^_+C`&JR1sI?$e$-#xFa-p*~t(_%5(uzb{SsSRx#o_sxIC*zW#w%}A7mCM+"
    "yC;qse>}r_+Q@wax<s+6vNawsR!A$JQB_>074qFncLP~@99)_rlz1V^B9R^)zfTG1X=}eq__)K*`H4W<_N3rVI1k"
    "OLgUXr>Pue!pJ+4)>?I#6|S}8go1&$0Ep&!o^a<BL+*u3Jw=;-j5(J9myHGVHZ%Zj=$en2OL-%Og{%BoJURVuJ_V"
    "C%y(Doq4?Vc;DPh$sZT4p13vtyd{Q2CCFt%#Kw&lNnX$hejgoW`tv{ZA_T3oNr7fR+M^6NQ&SxKWV;dya^P6O09H"
    ";qNG@+e!o9O@FAg;St1Raaq%vsJ2*c*0aEjGzezA@VPQh8ZAU0un;Ih&^MsyY0C8QyvQaIQ&{naC6X{<oZsXaiSX"
    "H`~Ci@o{g8^l#a59+{?US~uHw5}WXBH^Gf*$dFK`}C6LAnzU=3vVU5+k7=JhVDr=Hnd>eg~0h%c6~_HE(xgvMH4l"
    "Hzm27&51>Yd)oa!<{*KJrgswR=oOjqLelZBPEUZxaZi!b(B7<3FJVEUyN*1_bZ+}90xqdob-umX)WkRd7WPSH=|N"
    "%2w$=V1qX!@<izOGe;WCP>!)*3kvG6o%F@e;&f|8>PC?MOd<J8Dd{LCq=bHxk=SXvES7o1<OOU*i<Vxz`Xq0L*?d"
    "KvW4C72+>j;vQpM<hLnM5|i_OAn(iScQv_GW|)9vdJK9t^^LlmD$=+@Y%Y!T8n9jpI{0~J>;QWtz9++wyG+^ZtNB"
    "vW(BLLGh)DTYp#eY+Ui*h2xljxVQ;!O0R%hQT3Lel+ou$~3hGLYM%oXi=c`RM={lNVev=Q|2H61LM0L`rUEnq@=0"
    "OtecEMnr94=Ayr>_*H%-iiWtm1B>YC=9Yu|b7}7%y<Z!|U@gbM!4ec~b&}l~fG&+cs5>RC2K@b20HMX|yCbcme7z"
    "My^Kb)9UgpBe__v!quGaZaitNTmg=uL+#RX$guQv(hA}Y>r@wLv<p!(<B1U*#LIxbDMlea<w5ro=<Tto6{%`)8ar"
    "b9k?Q*B#|9w}a{y+pd$hr;YnknUv|4-<D0U@1IvixiCl5?_s-_%q84p;Y%)1$7SgJKaC=r&uwbFZ;0UyUdjP=$;7"
    "73}F^sc?0seoZ%moz8e6q)o4v2Cnk7$n|lb1i+6l5-X>j}7Q-FVM$3N~=+nNlJYI>HDn>VsIv3q3NK)LMccR6#$z"
    ")2|TK6|CwG=(Q|1-HKyw3#^6=BX!7jjz)vsam4JVoWaT3>yEU$_N8maBPTrR6jNjVj8F1Lep~B2{L2!juX>}&qr*"
    "Px7N>mxv6uK_3P7@f$)v>ZY>CXWQEw=w17_>pQW|NmGa;*mVo7TMXn>GgK`Rbhw;tq$JlB1Me2R;(M-m4$~8T?kQ"
    "7$0y^bai<ELM$~wMa#1C(JPDyEQ`B<2COqA0%35M$XQ|sL_J#txwl$*u$Nj|nQGwd7>zTHxIYr}$&qhfC<v?;Wh}"
    "uOuMlFiz9`Bk6-uRT0+CpcX%4WK-jr!ROP8_AvENcT&?*uy$;MjkivyXZSCULXH0dZc&TdIhqlqn2O#4cV+soh41"
    "@&5X>|a{emg9;yuw$I#PNeL+L{W{Vgx$me!<-3S7(!PeZ<J6#Tc*Yb#=5F<b(1dr-ApE<x*J4T-;YkB<G>=SzxPW"
    "-wz2AXTkUz~iRKR3rd(>ELTamId~hn7ehjUWUG*kNjvb;xQLnS*xw@_K6yQA#8cwZe?fql5OCKPJCbTr3r5`?G0O"
    "_T<V3VcV!e{`m3AYN6JkgKTpu2OTNHZeiMYXlsNGcq=;7Ok#1S(aepuR+CY129Lg2F-Z!Wh&FF6Eq_aH~2^28;4h"
    "$e(LHvcJ(S1`R?a+@J=b(>h|komzETj2|f`{p1`v($m^xF5<au46_^cp{q58p9};rrCeaNGP2C><?BnJmbib|mbg"
    "qc)vsio$a%cV>W<kwrg*|-Hxd_@-9C}IunN(LluWR?15-gW&4o<?y>(oT*UK3gjBvt$eA8V9Ry8BGE-u5siMjXrO"
    "3QKKh6;O;$1m<xHy&O*?g#a5R_rY%#P%k>rBdWj+k2INQh=^eNSq6vYd^$Rklm_6Hzd?gEAH$SW=#|mb8yzJDu_X"
    "v<g3fzR8g}Z;eoQ}$et9PHOkqSn}+lUjC!)-?A^(U!HU1i<U&~qP@glcsz-3LCr^|LOIqcLEHmUs;s>LwQV~kwu%"
    "y70eb#Co1xp!P$)S{H=jdEdv7*e-fg#jVB9R(=Bg>xgcPZr%oM8F9C}-sS@j|B<hC&O_6Kxn{G~`v)Sa5D3aEF<r"
    "Ihd-gmI8I&F5vCqSXE6Xx8ZO@9|Gm)nqTp@!Ojg@dbY*Rd35)vR1rHBVw=bhPmiHg0Os2O4~ABZ5Ex@HV^j3Uv-X"
    "mMW7$k83c-CWA|$YzDE}z99=x?cgXSy+Td!6tf%|fyD=;~=QQW75g(r6D*N~kU&J}0!F*g8(c`1;XG)!74wj#^1B"
    "??bz_W~%7A&6gs%2C0~3jyK^07#7d|FowgC1kqkC84yUtwgS)6e-OKmH|%HMeo(6woe>o>SJoEs(gTMkX~nKrI>Y"
    "|UTjjo(A9cq!8jYMNjihj)?Rz<MvMFGX_XtP;Jg(nuZPtR|K7Iv{PXHTo}7x)(VL^a{SlS2GBe>=xO76g)uvhsGu"
    "pRVIZ}=CPmh!V{D?Y8uFBq8=V+%<$w(IzvR96P3bzKHau&<OCO{ZauVq};O670}LqQoBVD(5OIpmVk@Q@b%!bZ`1"
    "MUW8L@t${8GpW?}f0@M6a+RqHLw{dE93PWx7~h4;F;&@OR@y0LYfkFIVhF=H=z+bb0f}_e(yXQ)$xEvXyLxmcos="
    "}9goKoB{G(a4R@WvjS6MSdTD|X3{o(zt24JYYINs9Kuc3?6*>4s#7BUak(ERC_$OXYTq^$5HuwWlAAp4O*h)FiF&"
    "LaMaB8dOoRsuO&RwuNm#{1^w%;wV%d+0WoI{j#`bowTcH_bu#W_hRiRq;V_+VL!T^=@9vs*10r&3~xVu(NnQF-_o"
    "ms8$>%1MRtPr&+{jdCWG>Gq-0Ew0Y&>$&Zi*dYYfthbIyp1aO*$j`y4=^lbokXpNw0{nFu%*jOD6N1U|{dyHe78j"
    "q;%?Q@rwqurWE92MU^+dF@vQ|rLVu*%T^4F_;SzQU?jtQo>ke?@jeriSKJV&P-lODB%%pvJ#b#&<3aM|*_}ZzdlZ"
    "N?MC%7^$^q4k1PWJ$ta6gw^KAY+j+w5whrtHu7VdS_zK~l|%VyM$BcF{bXy;bnEFOO81h(bK8Yyp7;3Li*IFkFAv"
    "oEjWFE1mHO+StZ#=;JLqxLP%itVM{;$Ifone5M;|%EeO=GA5*R~g69+idevL6y8{Uc@{Iuhy8n(tvCzn4yUT|rEp"
    "1_RRhHX8t7V&R6q@G}~03Wxg@RRMq-)P314nMeK9<p7+N4GbY8;qV-GK#33)xqf%PzF7-TSUU~W_6XNGf~NS!AXl"
    "uWo?-4!MB*j6?5kiB8LnlI#IsyuEzBVFcd}}6c#@X6St9va$2pHvb;^JqU<l%(-)OP3tONo2PxDnCKW}uT_o`u!!"
    "+bI`a<|ANL#!t(_4qQ_(o<+9Z#3$J$flBGJp@@ItP&ITPZfg5*-tqK;%+0Tko1ey!b*fH;GbS$7Pa1g=S=OfiO<h"
    "<ubj#240bLQ{kqK611Vd<9Ro!<%fFfazk73p*)>uBujI29bP~Hk`ee1y5cDdKl8ax>r6h3cP_m~`oK$_CqQB^Oep"
    "oek)QlG@HajH2c<{L5vtQO&c{2HagUGaj`N*J>{R9Kr3Nr32w=Wk7Fjx5_m}IPf!I+S1-y64LMGxN=tyr7LnRbOM"
    "kqB})3c3p#NsED`3frTOeU~Wi2XD#nC44g<#nPj%Mz0A_zu>PTCPPYsIT>kUb)a^Bu){MP}C;y{FArm`zNnQlk?N"
    "P<Fmu_!;|AP_IbN^0^7d*4LQMStQ~mt&FRUTle5vmK-_z<>G|O=BM(d6-#gwP9gPkY5EZy%U<VR8zyC5iJ^bNshs"
    "QrgEf;)$bh7{R=%DTAANCH9+J9AD<KKfl)IDhLq(Y0M*57ehp4CP7{enH@OP(|tQK%2lI)*}>oxBSy7PX{kp{P&x"
    "BGG(02d8^KoDamk{^E4Bcknl}Dy;`P_u*yseS2qThd&-efAv>tL>_HS-Rtz@?eQ_Jre`$Ax4Lij%i-wVvl_!Yoi|"
    "mB$XvAl(;j5nPEJSv{&sYBzD>K0TS9}W=lS&HXf)Y-d;ZhO>EZd`c$!ImsLC7G?7|QIH>Zck`-gA#j$k|NByyhS+"
    "D0OyO!0HU-`7B5Hjy7NDgyL2gO#eTW2>+C&dx`t*yJ*c`8rb9*aXdMd0nEKO&pVmi!%J?HFol5bh>wbLe0UMPxqi"
    "IFwqRWsxP_Xpy7r=#Ci>$z1cfGWeH$4$V`ZB?}UQmkl(8L94wq{P<uTm<D4`<A8!VvdBDP*wDq9w2Q*itwQxGJJI"
    "5E$j05d$Fwj*>%n(R1fwkct?tT!EU%f!OntOUyAdC3!W<4D5?CBFVtpqLxs{Tc=IeNp_6bk|aQBu7yps)?a`EmvH"
    ";gceYbNQj3Kqh6JCqtm_DT+!GJvrQScLN`xJ5X~hTP2bigXzWGPIS%u_|8OjYYx1#cv%+9qJoM=_V+ddh+pu0C}Q"
    "NH2%Ojyr$vv6sOnKyPq})InsjdI8S|{5K#m=U5J`$SxaVg-fEs?U9@skbsvXp#2*#Ng<y~ARJ*4&|nV@TpF();+j"
    "Aiwdsc(rM^rrnS%((zNBC|9(fyB5O=2H;J?@za-VX8N7t^q(d^!%Gc(#*a3j$ljv(3o@Y(EW|(8+qeDa;~u|08cd"
    "M)icXHRS#t$_798)qf&;SdV)zO2Jef`XNoAu7Y_<ejlZfC>%{)i;nSx3Q7XqxgtxAQc4#D9Q$n_yLJAt;%p-{GX!"
    "6N|RZ3CM8<Ie1CXWlW1AFTI1}XyCO9|oQ$*G=94$%!W8=&4J&JjK3FYQWz{p9MgS#O>L_<kx?7J^W&fD}(<kbo7r"
    "jLR~#)%C76F!v%}Ps&wJe6R!G?h4E+g_`i5yl)gIJ{|3$66gQGn&rbYwy%Yrr&xjujc4A_!Khaj&#*t)WlQ@6g)i"
    "mA=NNf!(GLS(2js-&x5fKVcH+nGUhNslVX2u{!j4rdNR|{=S%CrYjmWl5hCb^R)yv5w&C_}^agBbZc9ilut?F{!7"
    "yGNSDoTo0MUMjGNO2M`vC06J0foJ^pT(<$BHs6lM1Js5fse8Gb-(*p$h<@M9Okvmvh*4hM%DF48<<fyxe4m@_BX?"
    "e>3iYB_P6pt^1b+J>zjc%HBMoHEaN)GAW&-OWGVB#!+rhz)-6I19BQoG&>4R=4UF?QrzgK09*j=U?1X^Opj$T4ct"
    "^Di0JGn!j(`~N&^*9J?i|>czyRYF_DI_o;3(o1&Ujjv6j>H8Vz{JjsPJOT(zurOM2%AiN`{z2EA;LxqqN386nfZD"
    "V}TYNJ%ui7dIz_aaBp)eIH#Mshexzq97?mlLZ&A;^z`<|iYUyT3Ev~ECh~Ol9)5U=SW60c#x`1~S{{+06%b*b-G@"
    "lfWTKKnllF)<!prn=QHMopZ82w0V^0sGVk+p1J(6ve$dSti$d{@cnPtOs;?aE?*va3bn?`*oD*Y#rs_~!I&8ki_^"
    "Ko^xEDOwUphrQ)U6j63i%tDiM1>#tO2GHC^h#azCa!PzmwLU#;CDt&^K~TNlto?4itMS98vgq?-GR=$EdC*L9HZ_"
    "yr&HohSzO7Hn*+zoVIb<&GLs}!`u#p5;_^cZD<+WxNb?Z?iMxb;s_LXz)wmnQP#6zFRVT76o8M!%>1%3647oM>{o"
    "g>Pm1Vs)z6I@62>1|q<pI=Bt^w@M!+4zQ&$28Z#yfp5J<3jZ+Y!R$w;wO#t29gNR3{Y0w{e<b=8Cu~3a&-OyhhEp"
    "1*NW@EO6xDaxoM?05iS)>pY9Eg9F03suDA6L-&)`(f-S1i@PUPoF`YshtL&OU9M)ZjUYx7NQ#3Owcl^*NFk~fx?}"
    "}`W1H{Q#I>QzZe@8@RKXT>mM5=iXW7&07DJ(;y%GTK5`5FRQd8Mjp^vVd!~C|OSn^Y{=?32G40zw08eR4`1S;Xf)"
    "g%$Z7FbB|T=$|)>w&IlE{J9;Tg|$@xPA83C0nclb!qErXtuR+RjA`*Qb|nKQbz7aP3YND&Xf=+uWzlyM;4)Xi9MA"
    "vzqK_qPLRa&pu@?RlQ}8@>mgkBG|4o&H4#!eh=O09>U7%=hg4A>$oS5>bP;D{g@*>QhFrHCtn0w0r+SL|#*pONJo"
    "MJ)H~mcWdaFTFQ`1!ZI_lh1F(O)5R3{lkf|C69HyOCE>6Ix$LrHk6A~=W;a}))S2@ovyJy)wVOD3saMyf^^i-)Gf"
    "V5Qbsc7CJFxU8fVM-rjK+UUg2GU1`ujgUs26~+6>YT5BdM4hqfCP%>|U8s-21lElfE^!lAc%XIQ&}OJfA8^<<jH%"
    "mdDf^X-%h^q*oR4=p-~Hte7vu3=@3MPe%0AWJ>p&abht7BEC-6_eBf2VI&1`6dM+j-0$ow`f3yM$r9F{_5I^yolf"
    "wE2Dzx`sl77PF{vvih1n1}@eYxVRtF0lr6W%BcvaY@N#Mhj4-$7wAVRiC?c0bg8V*Z@{ROmqAf(`nTg=4#6tn#D^"
    "H(Ei*-;`6w?uAF7irs=`aXKv>^`7F#}=^@(NTqMS7Qdb3xCVF4z=^bTo@V}8!Du-};M4I7nyknkaLM?R!YF)0K2V"
    "rf6p{14g0Sa^NoeS<MzvN{UC?YXL;pYEB!#tsL8U?X;1uVhf_vu0wt9tlq*UwKtlf{2nR|zKs20JHbBN&UweywwA"
    "ar9vcJgZ$`TO(Ea(+oRgs^MQ<*Q9eBvr2M!&6;0K`&`(9T7qw^t4L2*m(VBoXIYlk&$2A}=Wf&eh#947)@Sju8U#"
    "giWTbsq^6~|r^S_wsos;O|uh`bMzp|}q^?d+zC3b>k)i(yjb|?dwHr$g3CF~$a5m|tmXn=(m?jIeJOAEr7N=V-}T"
    "Z_wJF5}tz_!@Xci5+Yf^lLo}S!nE~T3*93jszW~ovm^`7$H<4ovXR(2NXJD9YUTpy2jIjpE0^f_zq+%vC>|E%;%2"
    "FF)+ppKK@YhFw`Qo?m~2*po%MLXcd#Rn#IV!(uU(SngtdIRRl4%fpjX~SIntrK{^L()Y;rC87K&%I85T~Febr#fz"
    "c1P2OxGGf4q%p6444bU)ZTt5P;0a2OB=Y*7QZ(nEvdxMQ;;qfqvrK=|iI*Y~b(#($*2z3^E;ZzxNs^gDBi2{iYhC"
    "Pwws7z@eB>Y{tt~@EY~ZtL70__1iCTACCHXu;=&-_Z$Ci>$Nt^p44-F*XG`bE>j(OaAfvmX32dwbsrTgrE*20bBE"
    "y`5z!LlU82~djbK-5qRX_<p{uFYOD(QKPan9Ct`HxB;2Meo4c*dxhU{Wz8j&mLovd434@mv29zv1}Xi&r~qd0(A0"
    "j&!vAR%rb90GaQRymVi0U=cuUsvd>l#4j8(^<8xNZam|FkNqxSxOBcV+f$!30Og$EleSeZ>7s6DY|J6alvJ}>~x("
    "oTV2!Cvy2_<Dy3|Hiy@-RefYcTsAgPE4=?yXXD7!862^Dbs?eD?=rk)u497d#kZ()@_hxuM-T`G5^FO#Re$I6n-w"
    "oAo-cP!HU)gmBE3Hs70acNo8=;xi{q<hzHqKTkv-rDD_)=IdgGx4Y<D7a{ua}TU4U6CX0q)=*#ye$vr_Gk&OXF)&"
    "@`rjMJ!*Ehw{jhm-^TH%u<sZAbf62WjolZvQY<JR60BFK@gjOXNKqi9<DU>i9`-5o`e;+wU9g0|++YDX(-1ikPBv"
    "l?X@dgZnLjCjBT}X^8px4?-W*93`4}#o8DJjRD3<GJwNNWOD3n9iN3Q}uwxC!J#tSh{5`;AqA)1#3JitEE_m0nhI"
    "z4%FxIfu@b2#~V^fzY{I={a?|7mi5^7H7}yJY`p@9n{8vVU?gnw$i#>OK`(bFw)VG(k0T3_j78;_2={yWNhqLdY="
    "hI<(|yZeZ`kPy;XCL*Y2@_4r~ZTNXCcc6Y;-&aD=KX~*eDWVPD$D^ZFep0Aw_=q{+|;2)_)e+Xo4wOsVIr4Ia<yW"
    "I$fEmVKf#@L=Ptj#=HZ=eHYBC3-^^+(_u&s8&|PLi0xV9D{${R_9QWuMiJ?gQcz7?POx{vpd^6ZN7hS2A?h0mBta"
    "UFcWKEUht{r{m8&9Jyj>%~u}}VJlTlc>vx0M;oZO^b>_s3t`m{i1<=3*-&Pc#Fd2)*}f%peW*F3^Muouw^#>e4Fq"
    "sA9_Jzdd$D`T>}@y?{6<Z6KpUJxYe20<8@wJavaW9siLl){Y#SyrVtb%M#4ucF8z?KcM+u;?@62uf)&bMBwRvUXc"
    "AFh@?a$U0pbNcfb|WFw#&5>635S8*+PXe831W{x0rlz>*f>gnO<FtLogwhHT66ZnncMn8{Co3dHc5@{CwInJC}_M"
    "i#o6%y3y|?R=%jsT6f}>0C6x@kp*iha!+$u4P8}tiqkawvLKL==$ni+%#?Vy)RA^8z@W%%?l{@~a^a|W{$B5PQO?"
    "j1OTeVU4@~c=^ni>emD2$cBG<J$QF<G%xOob+@t@X{LOV_+z;>q;fL2VAKg{LW*_AL4e?z}1$M*|G?b#O@V0l1fO"
    "JX&i@C}2P?fY*~^=hd)c_lO=;CTh<!(DzRs(x(9n-XwslzsddRYj6SBs`X?EoE=TP-9AJD_iITQIpjVz*~w;@&|5"
    "+9mMYu%A}He{U%p><gU@S2>Mb<(v1hB3FWS`Tr8h^KtlHeNSk_Gq#g*lqW><#rKYv2+lA&r?52Swv<+sD2+nH$FS"
    "`Dvm+gbH2AHQurkX08#$K0u-D_OJ%sv8IC+&VZUsPf}QA=HcR=FjGWZO{}KG;yOy@Kx;l%umi82v0XIW@y{GE{DC"
    "BLAuXG-QukVEG+O|uDb()C=;GT@8vq;k3{}^Ep3?CLcs7MjA`jUG<0w4I>y#HyrrRX+w|_%@5;y*Lmt^7dqpxw)z"
    "^VKPT&o9LPz*`!p*wJ8}ikank{^uX8P8+I7D}N^P5%^G|ifHC<<cL!9-2D&8ud-!%aLLM?`=v3?C}At%(@Y8ZP6z"
    "hQFUiY^eT-T83_@|MIWUt9EFuZFfbOA0pcA+V+YX)a=)C=&$6bW}RTDw~HKNM#XQ583v-Lxzyk9u;TMzMLRpAfht"
    "lCM;KJJfBOWO;tt?{|6!qs{~KUGxMrKX;S=dr0RWIa_D^cY=uS_?6it^S=gH4N7%v82T>g$S{w63R&KgSJp*4dZ%"
    "E;5nm)VosxbVLQiWg`zfXC@~H*i-I8e){qd1<pGheNT;;Fa1r6ab(HEZE#6&>Q=nNBg5fK{nj314$YHpnt134y`x"
    "(kl&LVcx>DFTPCnK-FZ-ZiBBC|!79#*m5Rnj3RcEwnO=}Mf!*IkvVAo2p9UIkwxkCQ{kb)KN^9hn;ccaVJg;<wnk"
    "Swj53Xy+<~T4BBco}O33r3wL@XRrL3@<^zgz;YL>zkjoN9H&l66z_ZA)mwEgD?HTMH^w(u}ohf9lg<r2sj9XbNfj"
    "g(r~HZGMgE<F+>q@w+l5MUh+3@Tzpmz67TZYRAEn|DQI4yq(!v>4c!i2Gs8!Xu%yCx`PFOU_k_~_ND#fcm0~a3o<"
    "I&T^DBNpXk2Omg=*e7u(C*Fc$nc9!yJ>mGsb0T5Ave*bBqJ7TgO5T1!_Su{o&a&B$?B<}^@Stu;h;KxmJ{ST8?j%"
    "mdi2f7kD5@c#xhxV`~iyAT+xfB78?M(-Phd#=hHEYf8rsdSIv@5opk?>vNIVgo1pE!dcGNQ+MAjpwUpMFzrs7&KA"
    "Z|EUnKS+MRr>+gRXfEP(TT!fd1Z}u>o#{qgrNF9{sti=&0iK_3Yav-^!XqhJ0^7kOo-vG^Zm~<L&E;H@~@mw6TPm"
    "1ThJv}=){a*&?{vOBqdmQKQah$)$aelfu&OlmQYa13F^wyxR*96v7ZU>V?`}luFR3+szcUT|VKRWDgfGOzWCn6NS"
    "ruA%~;!_0!ns@!L77(~`d_BO=yu?2v9I$cp`!RpPFh5_ce00bj!yNVoZ!Vb-Y0@KLj>A8X#jJh2qx*aO-|vXe@9}"
    "@X$N&8v|M%ZL{;$Df>>x$N(A%?FjxF9bLxt5jL4H`EGH2$tF0zfi&9n5qRAlzdAEO^0Q5_2qJawGCCo0@r{B(Z)M"
    "oeGczIr*kiR+h)K>~m@9p^GnmPHEuY%!8hWr81#x<+aB0C{WUd@Y(ULD!D+&h63B>qs2E7H9P;NsEZDWp`z_FHR8"
    "yL)P)Q64NR1;7+IFO3vaHm27}sjC1Y=*N6kFv^OjAd3vq-g9CCZ<D}BsQYD3ruxLWD0bJS>)9KmCFQe1Z;g83Yy&"
    "p%%=aZwO*OTw}&PJ2Br$^JN7_YwAef5=kfS68i>UueN`4YQyQ&jcf)vK?*{OaZHtLe1g-s0<%gHf=#zu(FH%jr~f"
    "rqh1EKN<bUX#ef`$*H~}&eFK*ZfKctBGYz(MRwv$T*<hU<+tK0i}Uv=T<zJ!u{wgKL&fscl8JC|i4++J@pCSMP<;"
    "+7XFA;j74Q@*<V>gE!qwy4X6zTG?5S$1Py$cH*D-88yEfpJoEK0yAYa!v5KIATeF_yJ@=r`OT&=68vjew+s4({vt"
    "Q>-u>OfkmE)iGa3dqzDalx;)E97Rz^S=)s+XPurw}J&ZI{xMG^yK*U==i)rcWjgZs5#QU@wAB$z6>|VBiFb)>5+@"
    "=9Q^J$KN$V6_x9*qcLz_%){PI#Ro#IP!^?4F!%vf6_Kpq@CTHh+=WoxD`)SAX8gWqr`e1pFCTD*;J0HECyg5C2{p"
    "Q>ryT27H4DN}=nOZAs0Ry>n3^p1S;t+5p7wSVS<6E&VR!p2lyAHOfI{3#sWJ_S+3fIwC7pqbL_d47T;u->ouy*Xp"
    "@zLLa%PY;VGbw;)MHE+1%@W)hAW#T~!j@kYC32pNIUH+ML@jX5O)QS3ibM>AGeG}ojn99Y;fcfxZWsyAuu2Og?AF"
    "EX{bZG63e`aT1uKS8NvV95Wq*x?b-60VH4qnn0gy7k{wpj}yXm~BCAC!Dpgf_=9{S=3tWpJGDKby18>+&~O@p9RP"
    "v$;}zpsGBr(UbZ!KWJ6;=Pp1O3)=S*1CwV04qrAN|drF;poTH_**KBx<Sxl*=vWsuPU-zIiWMMgGP<DAH&p~r=<3"
    "EK+;TBWfsv<5Q%u1PC!{VAxIWsrzId9W=@n>LyKgSb=F7rzVJ6-w_g&9Jl=V!tqeM&9J6Ap2eCk~lx4ufx4F}oDQ"
    "**v4A2xDmM#sWp~rKp2O7DA)8qK8+Dbe4-YZoMBIvzZuIn2>N*;4xS=_`M{a4-r@O;nJXX3aJxvW9x444lQ>d34s"
    "F^}P}&4HS4j=WOhRK~L#Mwvi8B=AziwcVb@?FaOsk+{Rkzi}>Bc}Wdqpe&N|E7m}gj0IrGw?j1nt$M!BY)&Zf+u3"
    "iw8tRY4WboVv@o(ZD`tk7WXz%ck9s@$)A|DrTQat@?`1RIE(?tm2R4YCl3$|$a;R#i0f-Tq>AEB1rC=|VIgKK_3+"
    "W!F1OcgQ-V`l2$nt)N-F((L<FXNI|<<;mkQoqOw4D*UP<6Y+I%Sh1$55znxKqz>HF0P7XO^O*l0*-s$*5e)3G=9l"
    "{8=M)wCD#s|=W>C{*Q!Lqv|R?4Ze$D#g&we9AiZht9AO?%bs!*{XW%8F)(@tJC%>ibEyczzbWu%G1;#tb>ptH39&"
    "J8x&v!l;$zCms91mm9MzJ;y$Q6_(4O9RQAV?t`Vhnn+S}dy$j9RxZk$Je&ja1i${I4GMA^+=~h?G-+UFwtK2hQ~`"
    "c6S@RvP{<8;mINBLYZ7j8+6ZE*lZRzpneec_+q>>yD8EcOzGvt?&XD^WB3fJC(aOsRO%HeKVX?0TC=3&8VYug?i{"
    "KCXa>Z%tRpy7#1P4>`|}k23HRVCq;E?8>OsE-)sQP|00Dci5HZdZ@s}Ze+Zdr=00?ylsYE3mUL{U*^y1s<xqcAtL"
    "yt)j`gB2$AK-KUC|+G|pdo}70xX1^dv+IB9Pt$DmMtX`TPzf^oJrE|3H}}MtvCazFL8o+F(9Z2hI?<qKX+2l<55l"
    "!IN05unUa4_^O{=oXvbmCGx4|?nAYaC7Qf0TS+<yv{?V~(nnZRzlSq8-3pz0rufEvr@8alKFoUD;?^W+nn<uRWS$"
    "k=w>cTc>tlJ}0zVO%wt3&MZ`CzM2MQP|Cn>tl4Zi*cC?{rE#cskYkm1RA!Gjs7iNx`WB*)0_*8W5dQ)sy1As@~C1"
    "$XEcjs%7rXRkLC#*?VH`1$J^>kZ~%p9Aq&^#~}#|yw5~mtC<e*jz;2Vx#qw0O6UgqKo1S|l0}mkIwz!~k9ux+91B"
    "k~qJi<g4X8>`ue!+il&aQMEf-{mXbCwGE<*7TJ<`gml4YX}w|*s#!T{?_!Cz2mYCO&@DS@D5-&EOdQ;&EnguVS*@"
    "C5}scg~>+zMJqd#U4NHvSHN1x|m=E|H209;MfO<=nd^%*722ccn;PPFr7h{nANv57cSbwkw7-y<eLd0=w#@M+VFd"
    "LU`w~#sQUoLc9Th5)+yAOsfHI&!5tLCqFnbE$$00otv57Ap#(=bVmq@g!r3!;VY>7(n6_w%ce*S>1+m+bvuO8k64"
    "#TWoFEu8VIXFLQj8aHT-{8dUTQu|Gt?zEbFZPk0;<&T!hdVTn1&tl+*%{e*i)Bd^>nr8tF>VB4@UiB@b&KQ<rc**"
    "%$Z|Eku87laR>@Dy*XNfleiuT1A<d^R#Gk*jRI^+X=aZsa$eRpuGg|8shS3j75<-IoZptuMe!27w0M$mesCWTDvZ"
    "?X@Gm%c6VPID+jmkZ%}@`&=z^v;D-w!aTGjL3pY%4hAD~xs=o#jPU)=laeL%f4h@mMkz4P!Q^z;ynRI;x?X$Xrr%"
    "{yMnEVmq#Qjbh|tqM80tGZLIt3KR&@oIoEgcyLMVij;#z&EM`t}X&P2t2sD*uCsV*zCnCY$cP}qpB<ZDqfj*ME5;"
    "*=@rtsm`nhznoP*+J(<88O(x?VRmTXG$um5HMjz6;gKym3%K56}lx&~tfh2${t?G0p=IIBp*|6p@MCcpf>Ep^?w!"
    "5AFyZeP&ygv$=^b6qnh@>f&`zbKV=OT=s2$cIBX#0(THnVE}Yv60YJuXJ4j2eeWEy5PF?}=8GeefADtjqU@?r@D3"
    "ncvEcESsif6}G_CE&n{b>k)-qYb{>#9;q?o9WEk8O>3fFJ_fa>V_OVQQk6dwd+gKQJL1f-9C=qkoTNqGSBjWaIuy"
    "7H*(~8`kGOQ4BgH%%sX?}Wi6J%cE$CumRsi&-3-XmkvYI)qfnHoDqKxYsS&I55&gpU;?*S{hmJqXC%D$cE5mf!Yi"
    "2|3fiSThcyVY=uf=&vjIkS|uV6*K1u7EyK0kwm3K2jwO%f$b}n&~R@3bVg~Zw8`@Gl_1A^csS<08w_d)Vuh-6xVT"
    "$7cI*op4Gq&cn$3X#7p{WKF;@`2wI)yvsx@9NS3r((Ds{FtEDV&Q%Y8yMq-J(Q#Aq`vs`6qem%}R)1;VHFX?0T@{"
    "8RszUl4$srSX7d$1+{+{4%CrB$zz%eahd*@GwatOqQTDM;Drnfa<tXYV`RDMz2sBB&@paZw~I2=nK_lsE%Dn2|=f"
    "V4Twx-o4%%^~L#(6!l#Jp)H79au{G)tgdfFJkBBP?79RG2tGt2p$Wb@K$j501%Ve3?V?_cBWl2=#gG;LeVpqHu&m"
    "t@@+!D@F}jV5RaxH%C2mq`qN?Q*XXzxD-UKf}b?!{T#=_B^6!}a}yCNxo0EPl(#2v(pxKnm^@@||fEjhxPrX?xe<"
    "NOu)#*yiT#D1KCC|~#HSiOpu+T9I|)GW@6Jcal`y9geHrlc8_VV~}wj`q$+2UB=cgpA9$y6N4ec~abo89M4rE3;D"
    "4D^rva)&RR&)gmvjF|NCb{St^9%S7PIo5xQ%FS9?+zd$E{B9c{!b^>*soCs@K3kiTbmP>^ISK2IzoTcC|k3^9r=q"
    "*ai3L5*eFEr|nivZT`GD~3>>0NerBk}aYbpetG#tb49zv_#<x>&$Vf{!JO(*-xBUR^zy5;I^NC_eY><XvQqE*&7a"
    "{VAxQmU~gA*J%#=<9k>SCsxEypBm%!0Xu#Qp`l;*QAg(}U{uLqVer8W9dTQ6M;Ue`jB||L$>klq6+S1y@?-H_W^2"
    "mA!=blXfAVi&UQlMn!m0bm!4l&fcBC0qiu#3hMRguAQZ-wP<CAk#1_rh`5U}r)0%U40zRnBWCY@NV+cb|LWnK+7x"
    "pZ#0{$W?i4k^y+qLeRq*OCP735c7gXPy20mKM3Vl38)5qOKx$<G~7Gkz1^4AZQ)ui@2WMjCY_p;Auttby~`~EFs2"
    "iV#jJ#FDvN9G=jUUG?Dadt`GX68s}H5<XVESkRKRV&3!K73f9DUC#IL`LE>CGPiHi^1x8$hRLU}$iTJ8QY?~ao-D"
    "d>X;#IRE<E*BtA79PXrTcM4l|@?#X7yJQRUGFl=c{~H7li>jKo?Ep?2}Lzco2%&Yu4XqU{gfmw15NW4A)XiYfiKs"
    "w`uRBtxC$ji{HxwUZjra?VXb4W_!S5hMWeFKDec5r2}O|ItOOpx<EOki<R%kWtmFW>S^&mCNV@VWr8gk(WFQglmx"
    "@ImM8X6z%t+JCN0o+Kkc214wfv}_9bi&c!zX$LpG55fI+EM_ggUy^efJaT(`}p<c$<RoxBsBSWDc<+LDkTAxlvet"
    "8%8!gl^v+V>M3PDd0acb?M31WYwuJpwKt03x>I}7!X1CCg`jGovH^pk@LBn)f32x8CX@`b#f5=2kYTS7{#I9Ll+n"
    "JoT){5898f*+q&Fp(c!6bSj&a8;y~%3Q37#DLxQrOg%NJmf^@=wG<Qan+VKVy?P7X!@tHnF{*&0-*7#@jo@zqEm-"
    "AJHf3aFJVO@+HEACY5{xG7&pqJ*BS0R+pdSN2#IHl+!1R?1~w;N{%UcqEF75J{FL5IJiB<yhh$7GHhVm-vGHK6ow"
    "V3f(SUK@OghthzX!S<Vo5?<EixWMo)?5SqCQ0`46JfWxQfK!aVSmj#Dny~uSDaz}CBN4H0Xaw>acGlkrl~7lQBdt"
    "0wT%8S+x`y6HP3@^0F@Bnt4v;j6SWH=-#P8)qHC0VTS=@pAA{m7G5z7}e4^WQ8@DvcAx(9b@P7-c^?~F7#N>Wiqi"
    "qV;nB!h3KO+-&Z+qBYJNw0@o3#{?>iuoLqo`{Q+8v1eXd^CU`d8jcjr51O^Docb+Q6Vj%4zR0mDqUOQZ*gAHxlf_"
    "vnXD>!&ysd`Yz9#2y4Ze>$`9;G1@of<2^6BB7K${dL~BHtP#Z@Y$jCrJvsH-{q%p;&fhKXwZ-)8`3JBTIap1JkRF"
    "`<pfPM(`iS+kpqodLOIRah0sl|-!1z2ePmIXm34p<yy-&jZ4O<bvYBkMugAF)aMER1D{oyM@@6w(mHYN?IGOvO=L"
    "t;KYrb!4?armRw`cS6+%bqP*TBXjWz%AX&P-ceIHBWnIZ>2l9AI;iddEh)<Desa~H6?sky8fVN)r_v-1pMdOeMCJ"
    "C*6h8OE>B(ztNmasj){b|MMn9a3|8sJ9EJAxq+$G}VSllIjI(#SkH~<W{pC(>w?|vGcj^Oe%5r=2u`0de=I5|BSo"
    "r>@O23;%eQtb}v_UE#m-NaeeabX#jDGZ-!j1wWWvbehdYztltfMHzeu<wCxy11(@ElJjxr%iH<1T8(8lO~KRc^Q&"
    "#+pNYGYg-+oV2ymVxy>sRZSE)8+hAisQEKs?tfKl(s#@GN;VYQ<S)~hz<%_`uhNXI|ie6fs`zeL#6O&Mvp$L7xr)"
    "aYBEoXbLN7hh$3->Y>gpGkPr~pby1jYfV+)yn!dC=|S0FfHFc$KGrU&#%J!>_Q#ct6k=kysXe(r55bM|X)tY~2@E"
    "*L;(=gEnr~Pqt63h6snK#Ik@EmPOxbnOdL?9caS5A<W##v55ObG2p#?P)wi$j03YeYH%X);$KinkuSPpC|>aHc;U"
    "71bfIGI_FS8fN*ia6LFhF7yXs1u`@khelx%p8Src9hHmjK{?&t?w=<)m`&@@StrpSvtm0ktOyWUFLBLM150kQ6Da"
    "WiF}i<+!jKn_{Iiz~56F-;6CylX%|v@&;86nvy!5xGqTK>|~I1xz7^qLyVYrnWr}c<&2-&#7g1Rg-y9PH2~=MLyL"
    "cVO1&ZLaUxko6XiQy$NE$_$H8G30N|U0_Cwvb3|`Wjz_kh#V(pD&C&!$X4;KJg~|5TxNv6W6<A$>L1PBeLdL9V(j"
    "2MfnbG-wlP*DDU`izrylFlw@(PmX0oWj2)4>rG*rn+1db128#~`o~hE#Mw<*G=cf&4<{Oy3SMXNy%;vo<Jzc0ME^"
    "pDG_yRylA$DnXl_87N-3tI6Nid&dW^SkRT+K`N+qi<03x$F<tgKSpZjuqY^U*=gnt(2k?MiqVy@rwl`yP48y57M#"
    "};4bp_R)-~Fm%Jf%TZNM@Hw;BYdH#b=+l|+~#SbY`G-UrbW@|heSpB)~IjFSS5oTbbiqoDIc@9m#^uU=H(%<RIRC"
    "}j_!MbyUOC`KhzAGw$>r-Hl_b{bItIHcxAj;FUSSA;(k!D-BDhUL>>RiY@~D<S|?E36)(jfUh>)`Fu+f}X($t1;}"
    "_)8mHCn@2uAB^0I6u;vYJ(sb5fq*#?n3G@M&@|+cg{=1Yl_}PmrovoesV1NLXOKracG;qNoq*#ts>6@%H*ji%VqQ"
    "Tlh4fqhn*)$<l3w+}$X2gtNA6ZZukBO8P$6TLXzi-%&7EHhiuW-*Dh`A0NMOJTI@+ANEFe#h!y3M#BJ<KhI8_Y<w"
    ")j?p?s<q4k!AC;~+SPERBhdI1AhE9@H+t|kWf1(T2t{6}`O4xO(zwO2xka22)fa9tlxE<p#bS?!d2tKGX3{&bd77"
    "j|&7OZIY<V<bVdTpq2u+EUd~3)*r3r8}%U#}(dXY#M3z?*7wKoVzQhmas57}-EBw&hC38xHugTW^V7%U3hl<{>TI"
    "w<Uve+OuBKsa{Ywg70kiEpKf`B8cgh}ec0jA!)<-DB~L&=I>Wknu(agA|XUuNs4aLN8YQ4<x}Tsf_rG-Ig|483so"
    "51z`zrr()6tVMi*S9*jAPDAM*E4?Vyd=8(Xy!Qg`SvxvdogP<<3EA@Ff-a!>eRK-H#Y&colHS^Js>_eAyJVW1PPO"
    "(o5S;CAqE(E<3X2gmwawF3exoB3iBGXt^0de7*QNvBL!xLUZ?{nym6{eu5R{0|^Ck8GyPK}}3)P3_^sC967m}|*3"
    "69|(mGV3b%6u8JZN6e+>yOx3}-u3#cmRL>Sr($&~@N2LUr9BPV%h>U?HGnd%NgL4evYnrjBMsRJ2>>Q~C!Zlh+52"
    "J1Pz-&<=)}imCfDT3>i_ZwqB$2(LCS#>h0rj>-93@_q9Tz2oA(BM#-HM7tcts!YQx3)vif86rhbdw)OBqOOSSA6r"
    "%ctgJuHpKvHt#;r5@S7GP^Sa#{<qC8=$4ZN$_Dm;pr;(JPfw}IcG7<2+X&l0OkJ<BH=i0*4Wg17}>CTn)l{edVNz"
    "funztoIBBldaPq(r^%jCm|Ab6IX@0G-g6Zko<Kx5QAE)qedJ?$GIU)?lE+IXE4nsCxe2`Q5x-;N61N&SBMRD`?yO"
    "Lw%y3iqHhJP1;3U)_;53iTW7&B!Pp|OV^;1-Kzt=@!#uyD9k_!$P7#Cf8e%kVq~R<ERXk-{DFTYhPF3K4tBZILFG"
    "Sj71Xe2J@4AD@UfluAzJs5vh{=i$^_I^ORzT7$>FRyY)~Fdv@N{gc;kjz)k+M`HT@(aHYL_$RbG{bBF$2w-Z&OBC"
    "fL$2HO9T(2YqhA>h~q?SZ!spgJ=!W=wD1-O`Ij{W4~6<>D)a0JAO8Z3=g)^O-Yee`*b18E>F64Ag1KI^>iwDu(x+"
    "f-h<gz4j^-?0CEN=a`#H#aLxs1*iU5#wCwGt(AEXbXoputVebhvxY4p8pi%r(yzrvw<^10eT10Nb+j^78S`-_E?I"
    "92FOeGk8@TUy<j@0pKf}>2Bo1fh-TPaRiSC9<M~6$k(L6{JbS#k3C)Y;_(yVUJ|#IwIyhgAxhmtl-}s_AD;pxD0r"
    "*_I>3SS65GP3qf+T^6^9*V@V(b8gV50nm_!Wq~OLQv3552cv^<I5~L_Sa=(MU7VZIXDT;Qxut>bNz64Pr>_6ukrf"
    "{0Rcy7)w=efr`t7xub(Oz;VG>=aLrFs-8{q;%=*uy4REf6sbQ@EFkscXzy$UEGKF-I*T-4LGr|_ue;;?_1=F>PDk"
    "gbha=!X{L<2Tz&9|#Ih@qRdzp8VtAQRNFL8j^LmA)cB9wTK2|+;r!J^2E8umIE+<7faF;&XMay>;)fYvI=XRE?^!"
    "DXw?z;}noXF32xJMz_Yk4NtmA&@YUAa(p+!uUZ#4GQWds=By1Be3-W79bM+G@oUwM49Bs&<l_MzpJWNWsNE{WP3e"
    "vEzyrg?+Q$K7(Q{08<b&JXqbLyXA46dsmgPMPq&cY3b=Bb$i=ciHVGK9UU8SpvbV}rhjl_)eIq*f?i7elO+mCSDo"
    "}954ESR8CWzVatYEYWjV;hlYVT~3CED9<K?67d_)M#RHnt3*D;X-3);I$}C2PueISq9{L7*Z|VkjPWR~#OnjZV+S"
    ";qmziHAf4x>Y$aW<l-c*yW*F<qqn0o(RslVi5BvUNPOqkx#;j7>va2RRZtvFr)yji3KEA=8**R!SzOiR#8k0tvaI"
    "<c2lV#HXYdNku&BV8v3FI3U&)dUhEmSbWs3F!Srddh@F!qRG7drB_Pig}1{kXEt#M3~Aqg1Z{;96r+9>q=A^l^Y7"
    "OE>l{g-{0LPzLd>lf(c5dIgrS$cA4%c=hH=$)N*rzdi#r^lTTJYSNlzGb0yY;Zfd>MvKo)nGCsH5(Zo%<6BG@zud"
    "p;qeY<ZrNoPEaBZrt}OPkennavu&JbpMMb8u1Rg8+Nq=~7wE)F(WtPRAluKH$mA5?d;%;D_aP9&Lq;~1FFE<<pgv"
    "pw$HHDaR;k(6(Yur&nz_)A(z?LRVQ;As=OpgCV&54F{J6%wz%$~OODvILRxZk<%$(w_{^O2@_6KA7ywoixR#qsFf"
    "i-_dd1Um%p{`Tl75`MWT6@tXsu9Hea(w`T<5UCbl{7c_z^hJb?b_0!)t5o-A|7h><HN-xETa;QL!Cg(_8i>Na3$y"
    "{(cD}QsugtW9*R(56N9S)((E?7JN_i&-sKXLn=5FgxCpe)IaY0f6vOeZ1G2&Hd!*?2vS1+2ui*qn-zy(%|e&v()4"
    "Ml@i-N~i9uS{d!?y;U?c2JsM6(78<gNM5lLxG!v#gHb3bN8Os!C+uj3tcA?X=^XL9o(mvGc6!z!g2A?k~%yV9knF"
    "Y+VajX)hXYL9tfy;?Z~`mhw0(qc!SIDV_{v5(RL3g_M`&_iR#!aTUB5mvqFaCHDFxz1rq6k>nTrqm8>H+3FD*(B$"
    "-raSu2g8LXld7VXDl4J!K)%@ArkbV_|Toq~Bm<MU1euG7n9P5d@=&y<Et+%wT=1l5Xf)Lcyu@Z%!3~fqR2Y3y}pQ"
    "l?CQn35XULa6+V7JHS$piHUInN^C?Q@fHGf@bi_-Qh6&A9rm|IQJipYIO$mQ<L94~kp&VG!c6*~e~tr00c3GzX_x"
    "|8w0pC(oUNdHtW-0|l+N|JrU4x1_~x~Vy>xdnOXZ=3$l<DR&pr&LB=C8aYrh_6l>lQfrrp3SX?;?b6ih?!EN<dNY"
    "q6{=s|XzMVb#iBup@BzIz|X*83rzPrXjhV7kASxg5Nfo9;akjeHxITEf$|ADTa~f_2+C>kc$yd(;Fmr2Ui_zH>$4"
    "@BMl2rYnB54yRBf8dYwVQ>IZdITQ2Z7y##XI$~eQM;IDeh#)8ye6QT)=f*?z!Gr~CG@<l2Dw7E1yO4=<>#^D)E7l"
    "FYq5UeRv$d<4o!STnhUSKH3-GB^0XNBP~VdkcqTVB1eaX*KZ{y7U|vqnFU^W<}3Y@rVMD=m`*%|HMsQ%=0blL*|t"
    "D#XKHGaRvtHk>w)-1mijs%ij3s6FUaY{Q%x^XzI>_f)6m81AEB=`^P-0yI^XJi)p!Y?ta~LaPLZQ&~_7LPYGDxg8"
    "<yGp&t5eHSam8jMTmcPxH59i9E;y+^NyF>hS6QI8GEy-cEGfCh!vU%aGPXjcE0rK}`xBB<^sx!Jl9Q$@AW=}uox6"
    "R7T-NeBz<bQ#enVFKMp|9Ywl7-$gN2_}l~=u9Q5HCufrRlq)LEY8~aF5qz6R1$E!!xBsd@HGqOL7_hawkpKX$-lr"
    "LK~jZo&=?KZ`$0t{aNS!hpHoUe9l5<=1;mCO=N;a_IcP>fiC&{l{9$Nh?snsHgUXpqkjz}&`=A0O>1>U4zYOwM7v"
    "jG0{D<Zk-Q7U(!9C7rCJzIoysxf!#41Cal1R`KN$zPr1*)I1p;)Cq2Q<K->^)Yxav$FgMH3n`SXfcN;l_!|G3rt)"
    "i+W0|(cS6@wXDw8vs6#%ri-ofs{u(oddFV{!jAZUO*GsxSj{nt_u)Y){wNT0e7aSrV3rW{=!ENFzNBIxa<X3UQsR"
    "mmrF?dRkz3s1(GAF82NNkAVMk4Z0>Lu8>&2`TbNoa~B<iLd#gZ2_p>}+u-QHCh=d&9c`#WKD1`aF2vxX+Ll=!9$)"
    "1_3?1tqZ4AZx}jlej_wv-FP-kn^PTQOuSVVxwWUkF~j#9pc;F-$hM}7r$*<ynHrI)O>%poxQ%{kB}*^4W>}*4GaI"
    "fu4VR{S1`XgoyM<Q@c@jbBs;F-SQ=p5cb<S2belzaLsiL@2^gSH)$KVLLGwa<tLV3F+Z^P9AAMM(oyFCw{7MjQS="
    "^zE0ZzbIPp%ZKR0EcrI5)6++v@k?!J(7{Hf0AQ&MBgRwkBZf6;(BHybt}y2=_Ls61?o<w5CFGsMuor>;A@izBUBo"
    "UKIdj$j9k}oa_bFr_s*9EEj*5!;kpKLx8A{pV6-6Y^x8tfQRb3K`xZ4`V{a2`P-d$8CZ<=t<c8nxO}gCEK(n};^5"
    "?X6ajjW&ezH@LlGw+u^pY=P%D^7n-)btaWwFHRckP<*8`3T(q|6hy;da3B2FaJ#mOF+ZM{EfFD?bpgk3&56B%Mgd"
    "IrF0H%g0K_SE%DS@uYg1DjMM4FHJnC9)Dw%ndVZa;cRs0zoJgw(e{9Ax+Fw`>sw$|Ni#ybaWt~j_qAhCOtSaG5%i"
    "_>4X=ar4@vzqG`l&Kdk5~dz+2W_vum@L1Z%HxFTY7#j$c^5K(9c&nFz@ivsg?X1ZuFhuO?m8BZth{LqS(i6O_KGx"
    "&u<2pOGVu0Un7+q{4(d!Io&J>f=AA}^jSL8ew#s)!nWodKW7GKJ#h+Ifp@*2JI5DfEbDfOn7#!W_!s>O_=U&T6IY"
    "KuVM%KolKrjR!}Eq0xfR?&5W&HW8BeVEr_BF7V_)LOB|rDreT35i<ouXh<8+TIY~>TBQ)#cqPGC3;bji7W+j-3Y{"
    "9@=*W?UNC5@PUMA&Bh5b2-7m?B@IN`)3pn}6N5X|wCQpF!p7i`^ujKG+e1a~j&#<dlW$xDmZKRLgXf<o_n!}(E5a"
    "a$P*?|1*uG%9V;^K`Qka&@TiE1#x0Cf#X~Y;4MqS^b&?(kyV!hOTcjyUBb-+KP}7_Y_;@lj+lNBD{FM!wPTTN)`3"
    "gb^OlN#1GHBBt29(?bF_z@6MgSsygNZ5oULgLIo?zJvTuQx;LHvL;29AVj&6vG9Q;kuSdoiB{CFBfU|k#1&;XRO$"
    "{3Fg=d{<ApuV@q6o0Q9G$EEmKOK9)>D4X$s4f)z>ydR1TWT7kw85-cEU|+^OyMyTq*P^)KN%5(e!&tFmc$+%)Ag*"
    "#tbwti)(oe>^q(gIl(vITB~*SSa`P<CD!vOe!LE<^i3NL4XT_2^{`eo@)V<Ob+N-lLKG=L?MUnZ(UMr-_+YemAmT"
    "X$9a#ZgT5tRX^v#qZ5<WG7W<m{)r$rgf)7CH;u(s3;o>I^vFuPL2(n(s)(j~BDW9e`UA|9v(thgq63%MxDweHK5)"
    "3sD0m_C_#ML}{Z!sDz-P)4+&jk%Hn`&Snt0WF3$G{%WgvKX=T_^KnyJ_f8iXa9bbVzM@rrtJaIqL7%EQm?y0=_Rw"
    "GEG6RkwuegUFd)|0!KXhZ#{}wEJ<lRwDT9T*G^q`tN?ggQQbR@QYi=SMaKYiCuXILxL=FZ!roEzIKtpMbJRZwZ-l"
    "oM0D2T{0sZ!)9Xcd)Wpf(YUH0fbj*^I?atk{DL60F#w_|z)qfb^nDQ``oTe!UDe3=~|A0dTu6*AqHT{$j88K@)1V"
    "ul?gtylMqwg&&R7ywZy@alq78Ahqp69|3c(;?#R1yx66s>oNc_@s{rbl3_#3mWVR#a}K{^hNrTEk48*I%Cv%nseh"
    "tI_1&jMCbb&&-8M?rHVRcM61E{qzGWpodQ}*tYwGpZ&}b%w4UIdm8A?KA7Krv1f}o!#6Mjq3Z*EY(d(+21ln=y{Q"
    "Y3JIlCj9J9vw)0PK8x1JbPe^^=OOP=Mc$K%0q8cx-cR*a71dDfjF+gR!2r?Pz;Hm<hHd-MFTA$o(Vj4G4=yr2t{Y"
    "mE&42d5Mz=YeUR!G)FGVm6Dxrf9o!nCsgDTzN9*ghaLu+ni7L($h&To=T_;@v*(%a&S=GHIxT!El4(k~K5g<nk>E"
    "fWJzy^TJ;s)zFFv-ZrrA+XLqSAksQvX>=AQUc2^CR;h=#Q%_wlefr5Th_pGt&q}rs@x?Rhn!nxI_rkdWq%$a|7pV"
    "==Epf9QaCPBHkPxh*w<d0u>B;1FDuH_AD#w?co6`HJEupEGJYD;WI*olC+AiGBQ1AUxJGIEfS%@xAY`VKB`$=*7J"
    "d}8P$8pP?+qW9G~wU9*<5ZhsTHKikNgqk8T7t6e1oAt}>f0;PB)Gh)!4hk&1y@Wfh=o%Iqf1;PRsC&mq&ji{%dZ+"
    "o4c(c#EoE$r>2*msRIN)m!0j)1>pw*I$46mGkYY`7NBTxA=Th=_wKy{ukq&-XR$~z3=JYmubFSVKuMoGG6qTYbyD"
    "2cavta`J#V;GIiYVIS{qnz|z-c8;h!c7pL_yO*;6R5q$IR_~fU(;~xzSrEavudQtT!Fm;_>xPY6XW+!!lKVc1IRg"
    ")2hk50E&Dy|>8icB$`-Tp3otJ{3_1q_tgYZiMA?$eGU!v*F5aul$E6xZ<pRxyA6JW{na(BLx{R<jaJ2`&)CHy1NV"
    "yoU`R2<cWgV*YGpiphShVu0cg>0-5*sLDer29&<~X7c5qzKS@pI9LvuT^4wDasV6i%`5O00~(>sNs^W*Bi7$Sm_7"
    "#I0`VO{a_A~6mMN<HCLZ$u-$^8~T(HH0Lm`mcpCG}LGpc?amuoP6Y(`GZ!_{$RP<2YR_@WZ;AtWRdX;ly>7nQe#="
    "&JH6t;@Jvlk7CBxkBE2Hb+jVa!U$PeKkuPm_Ey*<K0gsPyxA@Nfpj=Evh~iQu_mzN-L`L!+1xPGcIL+zREH*9WC9"
    "X9PeDjy?^ZW{=ePcpD)dy{g;DD@AC71t8U^izW!!#5%=bB!TmR1J;46M;R{4(G)p_bIXOH04>A%Fy2{d7TDxZuPe"
    "zPKK5;kL^{zWk#T~IL{-Ty2IH<qewRR)D>Z>pQ1i!dT5x)86>&e$&e&bvZHD720>2l>*{skB8Rxg<5h|dT<b187r"
    ")NrL%Jwpa&I3g^5lE*poDCr*PSBKtl1JEn#|K{$fZqQbN^ip7Szghzq4D`(E*lk)Cw5+iH{F}Y=pFsZrsZ75y+C)"
    "E~Oibh)4$-cuLvM=<M<Irpuzu_#yikEP)*0`t^7O;t<;$1joo-M`c3!E5$Q1-8_}w%ia14wPai;cn1^?7e`CRKQF"
    "UC6ukeq%x`RU~Be7pm^T2=@3?!LlWV_MCCEM98~UW|9>CdS@yBha4|{-w7Eo>o1wcj$`y`~G3_@Zc7gn#D`hooJc"
    "*HT<A#Q{y`-Up)Lea^7=jy{nt5lyd#UKIxCJo*IjYYr#SlUwcy)r5aqBUjvx7%5}-ZZ>?l=orm0YPL{_@$x&7A;c"
    "oG-ySrV#7^GJ4)e`89cf=o2rR&50zUp-QH}ZpJ=qp{Ye-0jF5WffNwCF5LIZr<f!2l_;9<r;X<&b-dpnyJE?4=AF"
    "36umZ9Hp=5Vzn*&(YA81(pv;c(!?1^clYC~s>lFE=x(vz)iURvQP!i1ex$=dEa0H*6-%ldM3mE@HQQ^SpG{MsM)~"
    "Wny^I+cEg11g*AP#0A0VLG&RWrmgfB81_`(i|I4(gJDIplRj0>w$tDa69Y~CL~9Gsz=rI-43npbflG!TVVppLh`Y"
    "<9CKlFn}N)mLBHmAffK6S(+%1V+n)hWl)l2fpp~%0=*N>~<qQG+xNiwPdvobMh%PFUX4P9-_}>`!$%t0?JnK*IB&"
    "mC1tT3?j0SqUJxhA@N9Jc_VD1bOMYy*q>{5$nbvDq%)`9s<?^n#EYsUGljPxO-m*-Ss)wi9@XIfPR}fq={N}6hNY"
    "9q5YWOPn(~3{Y#!q<xOKbSeSA%c93g21Da=1I#4gOd!mh;fdysQ_?L3tPD1<2AUFRE3VL{<6^Is8+&?+d~SykF+y"
    "oqD~L!z%z9s&Y2GZ%CepD5>fp*-a5lee2B2ye`*R9$?r~sg(}6#+`?u=DrWTHd$}>?r-uVvzBM?{!6FYBl;Shv-%"
    "BC`*nQMC)~M>2PANY+V>v588t7GWoch@c7Aa3_Plvnn%h?$jDEo!Q1`O%8EvH`m-PhFqAOWJVppJ?uf=Kt>E7yb^"
    "e&cOOB(MG)xNka<F%b;sfxS639Gq#>@!TE5@E!EXJr#}9-hP+$>|>uCV$3X5dN-y9t5c9_@{m;uYv2e?6@x)S#6J"
    "g86BTbPDgtO-2kl|f&nm$gD?{rtEu{d^hakAf9UK+W*mBracCUl0q#8<;Pb=Rqsh_X>%;R97OGR!OBufp|2(@{<?"
    "jiifIaICMIVp50#ZZ2+Wqr4-Hoq_O%0ya3x>Mn2M8hPU_<TC0;`1!EsMYUh`@HkcJlW8&D-;54IJ3PswHoU2Oi#B"
    "yhdy!T>2Ns8-SgT(!6nj^mku9vPN1*$kV{LT|nwqc(GSse5KfT&QDH`Cd9NA8Y`w4vc%Ily~c<FNd~P`{>Unxr<f"
    "l(XpFyl&a!|E;1(Lf&7)sbeW)<8yw(eTiKKeOuXlF%<IjgjN8Q$!eM2_^h5Twc3eYebjjyWwqV0hR|GFE#h<70-w"
    "|2a1T206nQxdg8Wi!sus08KjGFZ~wKfJ;xPWTLKzcyr9Zg+Zl@BW#Xf|@(UXhKtX;}#Ge^u}Z8>>*jqP>m3nnK-X"
    "{@uEUFyzkSoLa|4H0ftW=+GVANHqJ6V%4t^91@rL^jP&sTzlVPw{>7RH+jc*W7qarr_wCI1P3HV3AABSL<-xK{e#"
    "&T9-}A}^!k}d*bej3FfU-(wnT+$*lAVVf?=ma$d0H+k0DxUp_cjXwq2P!yaUnqaR~k9^l}t4Hd@*njkjrjA!3yp~"
    "X9o4Rk$ns{OxJ0Tp_xHLSsm}N^+ZLl8|D$4^^=A2$iX8*mJ&pB;$YB4)*$dj4;x%`c6DOopgTvGky95KnBxbU!%R"
    "j0Q5<T-Nv&nl!-70;D+Jx>@~Y-BDg+<OQz+fpL<4gM8`E5|ds$tEwN`;HSx{s>mR|4e_P*(<su2)FA5qHn*8>b|G"
    ")00;VT)P30&Y*_B7l_K{2FUbGN-5N`@jk$<a;>)LWM*p672Nx4&wB>{Bv3<VoPd=#zs|G!?O}{kfr3exP67W>3^~"
    "+Q}@O>dwP3%Bp1n47d`|8-Bik;T4WGchQ(~S!ZuX0CYJ$}c^3F|m?w-Zr?7Y^@kMoH`CG#!LDMkKLt*uqOs=uWn-"
    "$KTuPyI9l`+)CoyikRsi(Ml;IykbHHTu{a7}-!zH%}+AmC5&-*Rab4%t)`q_Bf4<{u{#J|bez;(w%&=>WGtdMo=N"
    "(N)DX-dvJGQ?D_J`GkUO@i|z&_=~<c13DDF>=$krHkQ1A6!7EGyQzq0Wx;i<))t{jM@0^r(&!-BDL^c)p^yg93KC"
    ";W*HneUNmMVhR9RHCwV8LLOC_UEX|Xt^ji{Jcla3QYZ~1LtrSs%sqol*>qTzYGFs$tK`l=C?q5(0PD+p=jPz5T+&"
    "D_}#fIFpWuy|{^unkt$qoWweUW>V4{?kYYS|VK{1arW2a9&8S$KE*%^hBcEIc+-#GvS2_^%RTpeYK3aVhvNZ##Bk"
    "03S}Q#8<T<!Em`H(_kzYEof`s9_?U<*X;E=K3@*LMjseXrZCHRIY$H?I97uSPgWC_-Y||M#<jy2$)Fb7mg6fS(g-"
    "(dBTXi`pX1M3Mv|BB)7!Ss3)&<71ta6xQ+BWvyt7_WyutRagR(YLf<J{~IV4GoLf05STLdYr*5*cP0-i5sIY2y(Q"
    "5jaF3y@S~^a!_LIM4vlTXn?CYCf_0x0Ip$aSN7$EFbJlo@ZhJPu`IL7NhVG|D<BkC1J}2Ng{BFfslp??rCmN|_8w"
    "$%WfxeqS(Z7bQ<pBVHUQRYRPsHO^O}YoU*j1StwTX7UhoMCvh9mnhiNm_^(_4U8xVsUDaQ9`zT625E2MCWXxi0xz"
    "Yfdj=EB|d<Vc(qcT7L}%<A32+gOgNflF?o-o>P9?KvJS>T;XctL1tvHHD6hqS#1FoMK!Or)2r!pL7e>hfwO#KI{v"
    "yU5Hjc66mPQKcjQ<4pPK0)LQMNq_~5K3mGq<*rPg(K<=W(B5GOH@GosAXb9A(E*@;W0YQ7E0%_G!W|)Qv;sT-(r6"
    "PV|5f8pT6;qbKJ2?ga?9s^?1vFU)8SUir!~LHphsWom(_i+ECTFAllj8#*js2p(yH!o*Qzhig${DoPjOOo2;P^$o"
    "Y0>L1w|MlKKHUOUq_EyQ^1OmPR1E7V<&re%i#H_`w^Fdm{?XyL3<C3)vH}Ivslv@VgRN8P;?o#?vsKw?W~5uz6Nk"
    "q1nJwu<#^S}+O$8=r>)O~hZKZl~x5Hlg%M5Bs40IuZeJm}Z=~Ff^SDwmB)~sVHwM>zZsld{@Ao{ehLTYlUHz}UDm"
    "6i61{BK&J#dDqLH&uN>tY$-TOKj(17EFnqWxdPjzgRX1yM`O`MwhkcAyX-~Zgn2W^AXoFUjg2E_V&%_^q0f4lT$1"
    "L)JV%Vs!UC5J6kic4@rqtPLyMq?Ln1VIKK_&R%MD%6(Mc;;ZTJ*o487!Po0Rf+;J*tz)0Dw>>fp9Lk!?jXow4sB+"
    "6RNc21Vl+Q(2u&Br^Y3*z2s7Xrj@V+u{gJQ)K5G#zh56~m|bgoPXN(;)d9a6)5UVApDZxKq$mo9PEuG9=d3#XO^&"
    "l?pU3mEBt15MqRKKP!lS3JUB#&S9m1qsE1Y`K_$#6l=(kg^G`&C=IY|sg&A{#;RxuHlJz5dV{1bfdC&>s!)<HueR"
    "0#txSpKF1f0>^NE&CWfm_kvOo^w%kWyOpoXip$f%i*TwP!d-cw6YT2Fhqt*xudpb!f^)AV9zC-46IPI4LFS+Tb?5"
    "|j8U&LNxAImX&c@@zh9##Tk~z!B)5K7=&TkrFCP^Em9F&!1zv0*hjWAY0s6gGvF!G9rjp#U4;$g<nlsBb``7?I>~"
    "6O{j+E;6T~}#Gxp@2R{?akk5f0n370~+cZIwUj=mE6n6vy#HA@TWSj-$jZicOXaQdrP}t8fQeyih1{-oM8c@_#9q"
    "|m8by{g2MFa$3{22S>R7wzwx_BV=DCS{K90rc@jwn~e;(3L1empUUhVR6quNbJAL83)x^D$6EMmL-7#L>yd^Q0m8"
    "ry4*bc4?cm!^!citP=0aN=MTIEe8$bDb1^S!c0X~7t6}tT3oBB$ZepIsufxbpv}66cHU`oNf~C9)^+gY+56#qbjo"
    "F?t=FN9r;3pwMG*-(M+2R3%BAg9ReQ=fwNZ*lrQa%fgfY&lR+H+OGLz`lfNp{^-c?Hfm8xT;V5-=I&eWBR)1ld@("
    "(w7g1h^0xoLI|R;c!7ciMREjUEX-*W_1~%Ts%I_9V+_FB5#QQx1CGYave5RF?BPy)(@#qPbf&#Ea*h8$vsxH8U4("
    "aRpsDbu#MSLwU&b46ytfQr$X7RTglLDN}#@?gN-v$#xu?YSBV9FV|aR^Vss4`gR_AMZADV7t}@wkSO3PMb`w$>jO"
    "wAs)*3ilaWD*$tTQ`>7w`laDtN_HAM9!lB?LfsTZ=G3iN}rQnwVr`sFy&P{7uRJA-on|)A8@<_Vob)>&5#Omb1RM"
    "Qjru5jX^b`VzQvx<}i?$s;^st{WrXS2nBahISJDfE>juTjX1G{F3pR(W;^u?e4a$c&<q3gk6#N>X}Oeb)?qjyb<|"
    "KK?$rwb6-vkDJ<-28`H~OaU?S*zykisqb89$V_(3DVlx?B#VA`T>)FoQHsV#0?479OWk1(VqP*_q~G5VKq<C}ex?"
    "RmpE#jsicJ1phA8eUw6!~AS)6*guNbnWm5>ppY*a2>Lus4-l<uXXP64t`Ot@(Ta7Hl@DXp?CdEyrUw>=qyg52y;<"
    "HL`C7(FXSG*V2@A=tQA_h<M5CPCvi-ePXsfgrZ1;N%shR$e-kgk#q=f1V);Rqz?CK_<v4b_HsvQ`z&WTIWsFrMHG"
    "7yD5f}?{Woehk+HT5HcZtW2sx(qVac#W6|CgB8NNv<>#coO+$)wHHg<{jFm7Z0UNt#237{;AD=bP?uAG0MY2%02s"
    "w)In5O{(=GOY`@Q2o48`@90}1(OfOf+K7#ll!MD`o&;1V;RI3l@S$@-VIFe4bJ>VjO)FI+y3=R@OVoAUGfXvY0qq"
    "?H>^EEJ8q}XVY;OsW9&`q}6?<B_AlR1cQyrg4CCfC<(tk)i<!BJm3|C7J{22DW^h?ifO)cTjOV|($FiaRKh)A@m^"
    "<09cMQ$}&xi+-(T`)7gr8KaW;THSY$fIl>EyaR2X$$%qeIkV_0zVoowFPwpZRn$dBQi*rD-h%aXcp9m7nPPLNbzi"
    "39WSa-V??oB%U)bUwga4@j%C$#Ob}EiQNawgrFBj!MFPHcOt-|qM-nwCnDJ-GTIJdy!G6t!@(&Vmv_5ts^Bi*9k_"
    "(#L*ui&H=9@tibn#JZUIW2&4V6}KJOYKZQRTJ9dhM9K)hL5$tr1WRM*Anfj7}k7w%e>Q>WVRzZ5A;~L;rrlh6eP`"
    "+sVS-k>UMj?JVw~w|N43{pNMQfqmCVz95x`^(2M71Us$SF1(qr;{g4$=ixW#v|fxYy>6*$?iex6*J`~@`w#J+O_D"
    "0W|6||t7~u`y?pXlPLc0-wL5l5T&S9DpT$*NQn6Do><;{iu@s4V#T$Tj@-4njfy58a1-?K5D94ofZYsJ5&WUhl(p"
    "(So2lKQ@~=sMM>Dkg}q8JS}Mw&g}+E$bygHLkjdfI8!U|0-k!juPAy->MKgf-jo@lHE=SOLAbOjLLZiQ6%g2DBN#"
    "o*|z94Xc)&<9u+}nOs8sT{|Zx^E9PTU!$H~0wMw#`=)724=V%PHt%y?duC+t^vQOLG+u#AHDnvxT0cx;(`9u3SFy"
    "8#3QRZ6rgy$a6!bCd>V2(OZ_5z>}U}KEH=_*G*FmM~g3Q8-gh3*6kLp}o%_8_GQQX-;<u2>S0l7Rvhh{vGukeu+="
    "kP<b#222dMdjJWvV+?{App%bIp=|1j8=dx{w)|KE-O^_FOi^C9w1YG0kG(Y#p|>2m<7d|v4Ma-}@yjT%*zGP3^|v"
    "N}-=cj9EvnBW4C)z(tD?vvfo`qaI5Wg7!HAh)>11&G00s_>K6zqCW9}av3d{)=m=vn2o)y>WEP|>}D<EIFUdE+W`"
    "E3f_!U&it^xZ0j=dNFrXiUVlD)UOk8do>*k`*n279hk$8P3bHDCU4Yl<5a7*&H#OEre_$;RUiZLChg<15*GmFF2}"
    "C+{Ag35qM?bg*p^~f1S?wi0IpIhqN72++ENE^{A<ug{dYg(W-npdtXHq?kQBLgoXj|zH&uL{hhPJ9}kbu#Y?eYms"
    "xKg`BtYt%k@<em&u{JbV{DxMAh;lpD38M@2O5#fu0u_Rt~?XfG-f`%Bw;i4>XZgt!l7vsPdSGIC4=eCDIIFi%aFj"
    "b5jiD2T18r{kf7i@olQmwit9)Ijf0LEKL%bGbazP=Yb25+x{6~qEa3kSVA!}pdu~<&>O-sMV8ri6ej>U(Z9L~TPO"
    "sW)*hx1K$=XY`D&m7BLzugFtF%A7J+sLI1#}>*;?ei>mtsoZomVBlQ9&ybkttKAOT#Ba#BHI#JU4ZbhSYKq)5!mc"
    "p(QI6@Yu!bMEIwPDCisx?SZMp9Pz6tg9su;VM54R0YndqklRk!|w3-Jo37wIIEnrJ!V52>VwZZEGJ6{T$|7(9s0+"
    "0<e>EOGrdqCTf{z;$cw4Eb+Pm=w-~h4#%tR6f%{tWM>oCB7O&)Xp3@N<yLQlaLo=sx<MjB`X-Ay|`Z;Kva{g+<o2"
    ";X6KHjnRHw?)@+(UvdH5gO?x({w~`%dN6KLR>+tBufs*?q7B-XCirc$#(}f-&u#s;gS+8ZW0dBcRyqhDHZA0Rarv"
    "e7s|;BKJC2#?eF{L`VBi%oSQ4eTak=CDBDtqAhW(mYD=5mI=@(=d#J~c+M9Xam`l_bb>~j1MPcc__*T5ReHTDR+X"
    "mr{v;fa<>Q=;4d%rNl6UK3R%C7Q^Ek9%Vb*9_sCy?e|NBa=<R^-!e`<{UO<gZ1XoTV&dIbKyl0Ys6|4|_D_eI@Nu"
    "c%=Ac!toUjwV*80;EZGsOSlVQx>Wo5Hb9@M0ymcn6C#AGiyIkEr@}2+Dy_sttS(1n`;WGKs4`kVfp}vK@NE1fDrD"
    "F1H&0N>0SO25OJ!<@Ho$rVouWw*0A{rm3nJ?1VH`Lw8$1SxBihwQT^JlmRSlBa|7trtM0|_<wuXLGb(f&4o(WGt~"
    "=MVe!GMSKn~EWWS%gk?|A3o@ex_&z(|ON&;4zjB4oaab)%HkvdAlNnDD9#;*hXTtHH~c@iOfzSpxYGFRzLk*|qF("
    "{v&X;;J5Uy0r&`pYv^&?87jNL4L6ucPz~>)v;?v+_0HEzNjbC_zB9wueMxSDhYhLHUw*wsCNzyopUFP|Fce?x?rx"
    "Fqtj9l*Ghlc~S|);r9&jG!_ygMMs-qu#RV3?Xzi`nQq>NgKaM^V!QyaeEkk8`%c&DoXm=->hz;b%pD=?k`kHtFd@"
    "P~u%u`<))F^a5*MWEvFUoe^YXSW%7^X5>zJw2*4jhU`i(C1)8`C&=%i|{Bg0q}CDW>O@ntoorX6qqyK09>=;TUDA"
    ">WA#v%46Or;Koo`;B|9<UYds2sdnW2ItvdRzfuKB(O4b)?USImMlV@39k7b+kbq9!=I;b$|IR%>3LY3+J3y{Rl^~"
    "cm0UezO9l=?i+R|{FDGou1vrZ<FqxfGk~C6TGajZVHQ>H(Zpk=XpgewIZ0cy&$r2cS$HB7mrlCXg{#MXhAGRnQzT"
    "vUbA1Et&lZx!Q`@|7>(L+CLYciyux;UJIjZaK9B`#zoQS%OUt}M29~`HeA?8-ti)L_(6~*C$1=34F9@N(J&Rboc>"
    "By4g9YYK1ttzk&7`&YVvi~et}iwAd8F4>8qkv3Wl@ow-}4V<FnD}xi~yNKWQBa{nk_tfZw7ke%U*EJ314c@1pObV"
    "5QQNW3hj7{KL`V{<&(SD-KS$?i@PFu*o47+Dc^7cb;Ir)&uAB3#y(`JCQx8;*a91-2k1xZ`-0&1S~wmat8^fm0UU"
    "7A`<R%x^1T1Qx@zKJc|b-;5T~Oaz)2Kjjp?NomX(mWGb`L3<c{_PZb-HF-R!e0iMXJZ&0M@*oow-zi~|T<}K!PNP"
    "KD;5^isc9o*c#-13k+b+LPCLI}t$!j}As6hUBNE9yQfn|4PXRnh!#Ki;7yAWI7V1&Sn-5)Q<x-Cg+13J`qr1%AOy"
    "9+Q=7a{wGTs!+hr<wJuJ)>A<E#s~+$tEiFrTckvGw5Dy;dAeC#fx%!1o$<Jxrx3+&0*#+oq@|<);_Zd`tLN_y{F^"
    "1rU%z{jjB&(E+c|*DZ1hT73VIgs6hN-(e%pfmCcVA^?PsV~YtODb1eyg;O`5A^I(SS$rR!Kh-A?^%TM&d}HZ)NBm"
    "3+<gH*3H8hsG`GT%a<gukaNr)8=2q?$dg$h6vYdy>2}FGjUK*aCTbFfb0eWZsIaaWhoYNaRo>4oQf?Y*$V`rA|*2"
    "B*O0*QTTCmlT(SGu=Gh<*2!%#M9w!$^3Ocym1prKS{3$Y{;k}9}-06(FmL8F*#@W6=`09^aA*v@WOQfO#hNeyzbr"
    "e%{LcN^bpbyNw8ou1}o#=U%Rp$K;O?})8^BWOJSGT>l^6Jyo{2qb*0Q6#w_k}M*J13w^c$P_;*8vYZgeEi$lkj!$"
    "PO2AZ;&+LY5%_&ExGH=bcEh?C-*j`2{Ht|o>hR^n`e_elH9`EN8@}F}a~MuPn#Jk7{Ge&o!dJk-idUJ61AiGhB?s"
    "EbuE|>nt{6y(AMf1r;qx%K*L(XR%mJBVX^AbvPo1+fP5i?XQCB)LsW+@V(T6DT+TqjBB#<bb08&;M#_hDxa+(l7e"
    "x5fHIPF-af~LwkkS$Fe2!?5;2YMUm;+(_5aU9#|WQ}g4Vpz;qpVIK6)592Ec*;8#*K_SHY{@dXSQl+odf<FfYN|S"
    "Q{wQ8`yR8Ye)*#tsO3~{ufd%qB7{XMl*%pU*iq2V5X4Lb+0}hf6Dw@jWGJNr7bbN4l{Nszz<eeUjPQ~|sgYAe+tm"
    "0LmtY15z5^bf7VwLqET`SL?TP0F?28ugG44I!|ymQ%4t0cWnq0S#36m_S0O;-WuW@0}ku(mnYu%OM@9*m9;M+Yx-"
    "ur13h>K8^bM%|5IGLHb*+t89dMW2a14x&(jiNKeIS*Dnis=R9vmG!}46F;4wzo80xl&`K!lx`^^wtVk1wWhXv@gN"
    "MsdIjAAc(#KJGvzZ}1cu_5e{SIGd_VkiG5GRNySta@Ss0J=3#KWo%T*2`tI4+-yNw~GzpOEz2pzJQZfqe#?#8-y-"
    "7Q#d57Yt<y=_^9XicMrG{F8nxEsP7^-ZX~pE^QnjDzEw8qG?fVOynfug2l+TP_hAZm)$AP&m<agvb<L4?1Vx@vNy"
    "jXdu6i&rO72E8cHE*}D7f@z2L6?~YXiPm!>sza&qpz52+~|1RQ}9e!smeoy48?XgXbRC?2ZKgx1{-MdpZXqm}}E="
    "8r#(3z3nSo+l7vfI`rg$2fAt20~%ErQLPJ{>yacXIHgsQe8P`8auf706J@Kw*oGG5Lzbmj(ttO+uq%Rb-)RjQW<%"
    "S98bA<@$?FPtd|;5I7iH@7re4Y#+R@_>d^kqCJ+RD6&bCR!amX93JBJ5_y4(%y5Ye5bEGCnM!aGvsHall!{7k2|F"
    "$U4vPG?AUE#E1(M(`GXT6$B0xQpnYwR3&NAXoeUy>W1e=&2U&k23_@*pAtkD6zp%f^U4_zlQ@N25yzK<*U8j{;kG"
    "6M6D0_j>KS11>b^k8b_yeKkwk*zr7M!JX~+%_=fvMg@8L{_shUDAXZ8oTm(rO4LSOL?LD&gVGCj}7#oUR*%j14Tb"
    "D3J>1wzpuz!N&&~AK*nlzBNs6SR<u`p3^Rmtd0-t3potQioIvKMK}b9hp*#GD(F}niN?f|h43@sw`Yw16)Y@7=40"
    "EM#(WA=~3~P771L222*gN*Y4%0c{eJIONppF~rVpoGJimYNf4|jdo^5S#rZ}t_~W)wJEtSg8NWrFE~_L5MG^)kXE"
    ">M~dxl*@olNQP0ptwteGlvROPBOFeAC8#3r?a<CW)+43`kFp8V3E>ZjC4jpgx(&V5G}(pd4^&n0(-xHnp=o$rMdT"
    "b;z|@=meI?yGYjdycr1R>C?M!yR`qSj=fBk0rpeTGaE4hK{jV9)aCNrW>_QXL-kNVO6-fN)I-{vbcw|8asH!eJPl"
    "LvPB1<st>5;$*EbWY7)g;7t|WcAZpE-C=WV0<A93$C(W*$L)?^X9$ea4s+h23oRimO?d&G3&XYszVF7&fICH&XRq"
    "Mn60`@nX-2O!dlinMe__uaDw&03}gdA>ur)3^@N)k?>uaZ_|jqrBi@RvA%`>}9d=azis)B5tJUG+1^9S}StE+a`y"
    "CqthF8c-Q-M7|KV!NFsAnZ-rK}qfJX?$kZ;6R+&lwh;mcDa5@e}<Wu@TzX*azZMU}dLXPfQfe#u*BBZV*gclT`h@"
    "*<+P-7c7+JUXJtZ8KRi6tQH6#^Bp~uU7va;P^}hQXqKyOys1^K)+weN6f+@z$rkg#P1Hp($>I{jDmPCi)fgS`P~!"
    "H^fX3sY8P#S7v*{2vJFd-h#707uQKC<5C3l~@?G>ZX!)A58a@6$iAyrE$>RLPRiyzWF!K^3xg>qo7%NRD}Qoje}{"
    "vhdH{ahuz+)nv!V*=Mjv-y@o^~D=bwAE23cSV_02r-#3Wu>?bT$@KiwgaT5Cx8lZfoqIaRz86~2-lJ-bZwz^KULR"
    "$FW1=J5JhrlyGI_VspRLfl1J^GW2zrC`2UK#)*iQwEBaR$2Z*JumU$s9u&Ii!Z542l#@k(|L68kZN}^V*xuil;yI"
    "C0i@5MRy-kIS;Yc~myFMdeka2|K=+_{f)?8`PSmdwjmOUrzC>QfVAy^|8ov$0K!>gKVmaBo@Co*XSbqIERa1D<E$"
    "z$hE~3i*^X$FOAb$?s;9SrW4tl3HjgCI&y8VU^}Zdb`@B5iE@}{wZhvG_)*iSLvkud>};)*OVrinYLeXcKQn!+J~"
    "?N`3OzI&)z>&f8CbHY`j)Y_&JZc&p+#o{5~zkkEVNu9S#eW((;YN{}X{?kr`Jw1pl*K5oe+KDeZN=SywfVm@lIfu"
    "BUe46Sr+mH2Rcy^5CE5$Dayz*wKf-IP%)-CxE>AZ<UL|AKShhF!SYGX>2rxkJ++l-h@AsoiQEEX$%3I4CHEZiobv"
    "S?57z&`0?|f26M4x#jVMyyV)$gc`R@E@r;7-)3Dym$=!r)%{U?Q(6sZP=x-uSPR9QZCsDqZ{C+R?=GT$#h&63R`)"
    "7ScP0<h3q{kJAT|1PVKokZ;XsM%)oqZnlDm?!@0%(zMv-QKe$j%IQz<O(V4uU5y$O@=IUJIo43iFjJW!5=?$vy7E"
    "B=L}GV5@CD{c8x1_P0-yseq&d;UV>qw4kMGtAfm0qy+=7Qrj4NO}TNz49{r38GHn*PpwA;5KFI1_(cVHw(OJnWaV"
    "8}pd!@>fgBEl)wsgX&Eow`kRx9Q3=snBj>p_9L)dm)aRQnQn)d>9Y3Li*C6M@M+E8*niXf3N+<B7;lzafcD`4<dN"
    "jSNgRA@^}lJ7+5Ulgj9l9!)qrLBMx13YJvMge>rPlc%w@LZSJ`HVrJcK1Flh$LSfT0+iaHBc5oN*jQ}DP>xnWmYq"
    "i6S*!&QY7wsGHF3UbWubtf1lP_fE9wm^)swnz~+JScfT}((X15Y4IgLSPa{-pU<X3Q0=k(-DBPG`mssE|UGIExv|"
    ";3;<t-t%G0F#Ioo(v$-a+q^o)nJRyvd4(Ur&s)OPgJhuRJ%-?m*I_4|Tp`Ig5N{Utgr{?x<yWgw4itp8$LLz7k{p"
    "5y=DK^R6m3adfU1AzS~J)NvofTx699_>H&#A-x(ApHcn2O{KKl;F42AUvh8-q@4d)3)~~IvJ_Fj&l^=A*w#cM79F"
    "saIF21?R?guP?jT*iK~|h-4|;)=#i<5)I;FEnA5a)ik_1gV#3s2Z0a>S4bhLL5srmVkXN0dN!4@f<j)1v9V=Vr4@"
    "#^yY@`vS%mzRs@uU}pMptT#L;4c@8%d3}HuNU76h07jDV@=EGhY-A6U7SB(EH7St^YZ!21;|^R8*=h?<XyAKxA<-"
    "<GH|Kr$wmnVBws4BCOb0(2ckF{+1Vz)K}Z=ZzfNo0uv{=Li4{nRv<#rr>$IFX#j2dzeiK8i8hsgqN~PeiiSBZ$CD"
    "2byX4wgp8)3bTZ;|*IU{Mgwik6c4PzH6!iG#<O96`>UMFyQYi+b3Z<oZ#3i)k#dsF=R%C(*Xf^aNlo6c9V}W?wa&"
    "l4f1wP7x_!k3w0ZweVa3TdSg(#@FTY;&O4dxctxJ#q!m+%gY6sQE=~Zpoy`R_06L0Cvme&zxe9UG-ZQEUc9{QHWY"
    "%Go-zeKpnplX*^>4i6#5xe4B&lWs@!G%;)u^X&?o=INs-tOlc*}eDTqdrnLs=Vgvdj{Xd)XhYu4#rZqNpNg4W~Zv"
    "aJu<Ccj%Q6WM0Onn+hoRUFzZs)0{>x}%$ldcGl4IO0GGLI6rrp7F}F2CxnfTq-@4BN9qZ@SxU3e!C)6#a*sQ9!VS"
    "nhU7+BJcJWY)WPY#&bIk4dZ;U$tsq;})!}AmuvaKtQ+k;E7bueqArN9q3FAziHC2HfNcom|a~lWi0lw0-+|U>4ky"
    "uoYMgIKvI018#+#rFQ>9MlQ_!2p+P3^MlT3FB+l)U>T$kCgJrp@H=5fRoO$rQL%I}g?-5Cjfx3&JeSDi;j`ag)}Y"
    "0?5FmkmNb60%0R#4>Z-g!x!p~Z&ExFWKn`uf$1e@zcy8|ESGr1@a_S{kw7g`k=^8Nev2uqv$PR+4qFNZjS>PvAw$"
    "1uh4>&q7dv(0#HZUTT4gtCI;q4_v(S7h<@D7Aj~%j^+K||%pvo2Fg)8NaOvOrzHW@BcScrQicF?iP_&_@77cOXeP"
    "g)wfn!`id78G`uZWfgYu=sXydqN}@SJtkBXV#7U+wylM>7kSG@EDKE^^?WzzBM@C5weuAIhQSrn|)Ubh7BNP6;nD"
    "LG<<c~1Bo*w^i0M+blQKE3I#s^Z~-tu(_)MYCErqIPOQx-kcUmeCesgRnL#T6z>sD@G$Z;`I4im!&A(y-SD72O0u"
    "I?OI6WOnsbnr5N!PqS*PYvuV6Ozob}?+|ewR@kQ|SwAax2v^ydp?^<3*nB4jT%Dy)kNxJlqb)g(B9TcdL#xT}lwD"
    "d7Z*gg??0r*n!9Xje=sDcggY1qi)A+lbfQSM-xRR_kz{?aW|sk9*ymRWm`=;FP(N$*St3k2W-}hX8p0k+LN@weRM"
    "WTwgn;Q?=d7nxonRJMQ2+62$_&uyTmy{54~H)z`qY%;w9z0W4oOIqlUTYVYULk3yRPA-)_x4*Tj(1N21ZjZ-N(|1"
    "+DbBPh>m0;IxSIO;N2T*H2E6!a4NvQr+ea$1*709^xAFuJ$nDi{^71>;}v0{+*Z7>OQS$#BF<D>c8LrG7i^#nP{?"
    "`Eyk~9O+Jpk7fUgDrk<gzGTk>j7<Qlf4<&gw@lGB3AOX|Hn{QLug+W2Jh+GP5wZcKI9;)yxFThq9t#Cg}?sE7T;i"
    "^`gy%n3f%^Ly3hT-HdYmnb;Gb+Hs-F%akS)CSf^!mP1GeWpa&A{w9yQrAxm?87hq2}=N@-A<3+>P2wle}So%Eb<?"
    "36vC!vCi$^x!e>w5&ZM5QaJG^7d4XL+lT1OsM_*c8ZgxV<<u(@=jM!WH)qFLYt(zGv+wX*Pn<V)bK(gJT1NpZ>FQ"
    "nx%V>Y7;g{lZs<Yp~i;RAUzR_^<;?3$Li6-7YEgtwLkVmW@yypexj?yM**8>b+IlvulhokV)^}=o5aqF-(rk2o%t"
    "M0>rN!ggK8$Vg$evVn2#z+V8{>~jZ%CL-q{mE;-_Zp4K3Bvj{M+wFU#Tyi;K)P^3gIaDb@EN<`%Ed2gusig!hmOS"
    "8<+E4ceft95kgMmfE*8A~hHs~8U&?X;8QQy((h|U=fD*R*@p}S}{cYa49-o{4M6lrnY<c}gZ&+?}U`lnQF*rhuag"
    "HdE9Bwej{gGpiIC~q}XCrey^MquSqqY`A#!=_^n!N9!pF8dduOsg3iEywNWUpQQ`y0rWf;5AlbwtJ$`BKT4Ln)t`"
    "FHpPO<4hN)cH=KFgRQ-<tDBk)y>D~y>e(kF8w3Z!&2DaO=M3sA3=1}go9pXt^gu?eB81)|%F-AKo^CW`xa)Q7D$A"
    "mzE98k%1n49oz97W$8}X5d7dH(~6f-O9`oV7axC_xS?)9t^Sc~mtM7ygD;H``cq;2ntXn?8^{3gT$L&|{*p6yj}`"
    "@k8_)gV2tn`1dNMZEJ<l27G*A*ZoU=h9{wn3T)VNOB7-AMmwD_Om@I2;s{y`&<R0<ChKbDY`T>Zil;8`ehXEm7@e"
    "iy-j!hWcoX`bb1eS^ml8m+1(y%?Og|1<A}gS^XTonp<x-?z1AUT^3F#LJ5|JUi^izil-68KvNvW|O{T<2l3#~4e%"
    "d{B%%1T#DeJ*>ivG$^I~HPJswUdpyeqaJc-9=_L6>mhrgP|eCFY=%!7i`;@XVRQbB`%zv@xd^x`UDbV)1(M{Pp66"
    "=m-F(BCN{D(7MP{gZ+$dvlPZ#<$;jhL3e@!9G+qxPRWVu>E=+236Y1D4>NU58M3Ozh9&x!Zp25wBS}>B>gu$}?y@"
    "3k(sHw^esK(=DbiflJNzBC=G+$K3J<-Z@(F<{oS&^jmkLB?f?gLJ-(FiE;8a{y;xXfCqq&@f&$lr{mqXPG9fM;wm"
    "jDR&m6F7cs&%Kf6ND_CMoZAS&0&p{phhQtX#Q*Lyb0J<ZT?|fk>t~v<Z{)>vYB0?)zoSvH1_i$El`8JQ4|$U<%eA"
    "+*qToGi)YTw9Rzz7T)Os_(b3L%Q$f!=u}cTDH@G+ONNh%rEI)CQ^<|iAH?(598EI-~Y&J)~li=F1Zz&WEtVHvu+v"
    "lLTJ6!9D5v}%hiIRE@zv!H29i3szKjbdZ3ww{GkrC&PmnTrg(yy4ucl3#LM*cTQ7Sf-ZF5S~}@X=hK>3lqJkxhds"
    "?`Nh3?~G169r9cSLR#8;u+#U`u<!Pu2?Yygt777GY^`0XERMRFj;eemMX+|}_K%sZ!d(BJNrQ9#IkQIRzVU!e`xr"
    "ZjSvHn#WP!VtPchP)3H{!Qh5H$q_d8J-9aE;=tO2Rx$ya0pxntu}qpQx7Yq!FCKCKMAag>Y%y%W7>GeCy4d)us%A"
    "utW&)9($lI-115VAe~6AD4PJ`+@GUFtw=|1m^a2#-Nk8^@UW1f#?s3E4yL30JD!Pt9ovC*=-QYR;4GLjhx~*N_<K"
    "{(xEtZbkB0xy5CiZ%U8L?K-asfYLqiNmrxTJbz~L}rG<Qm^GQe~#Pm8z5Sn9gG~0s=-C<A=o+6EbN_a_fbtH*iLi"
    ";N~7i7lMyCO&v5iaP*;Xx*OGI4#2JF01NBStv0cb!JbkdJ7U$=$^|kvGxh;ve5#EnWoSNZI@lSyMI?xRjMDiZM>v"
    "4cl)z8AmIjcL;1=N7jj~e<l$NpN79een4v6*S_o4oVaAf#zLq|iRmbU)WpqU)wFqg;Ds;ZsO3VKw!JP1%Uh{QFpU"
    "^s61cW#ES4y1<^0uDk+iU8{7@KP$D1f@m^2*lFk*W#TQ$~P8HhDi-6>~NSuq8xt)e%jKxt?;nks=<!VSs{pGJvB9"
    "};(;5S|Q4Jc`QdwAu$5XBGj5vq_?{j!4{GuucXJC6kSW4g~?FOci1d^*{)u*hKH#N!W?-yolv<LaD$4-RBL07~m!"
    "hliCg?9?CZKY}uP70Ybi-Op_Vd8`isy78GGtJIQf$Y%5flFu_Ti%8`cwbF@XRM>`{p2b{mvw!g3ZYY?exlq~*GH("
    "94KCy>~`P5>xHhz2!LqIDbz-HT;_L>!K>tfHF(LEm~|eQa;IAE@#g_(>*7$k-DH>l5bpOlQ4B0+_`6^o9u&j_fRS"
    "2)P~AIniuG$e{qWpso(db8=29oUN^tBYBy*O&j_`+;&mjYD)#NscMrRnX&P}x~f{OiW_EqeRve^yAnGo^lEF{Z{_"
    "cg>UZP8H~m@QeD^macPMD!onbYf?Kcd(1&MN5PL1_cH{Mgs$kR7jwtotV;X#Xe$7UG|;dRT@*1IZS!;T+|;JG39e"
    "HU8^-!T_sdltQYI*Xo4p1azE!wH{G-#r?~JIFLI`x%Kx(gBP#ZXP7(4Sic$8y-Z*ehaPfXru3c>T&V<z7xic-gf6"
    "5L0{@=ZFx-6`nibIIgLAtLWR?f8ILC=47}ZT05=-!2-TJ<A4zV)L=M~Y#sk%h=oaMUI4hxlMmhyOY|NjJs)$YNK7"
    "LH{eEdIU{QAku@-A!IoGNfv-H-5i^I$~2lN+PjLUq>G4@x{M1c{G`zFVI__$BLVEWtsq0v`Fm?vZwI+TAmd%r>hx"
    "IqJ>2;bJ}!TWRxn=A<<&Kby~^qq&jqjsAvx7fPr>UmhV8N7C)+0X`d?-u+{{L;Wso5%*udMD`->Pr2>jjMsS9P~a"
    "tW*lo&5om1s)by)A>eqk%dXGTd-{aJ*A=PLD!n?f^V!k>1YZ~A3JW3TdTk+KBW<&$^+1MG0z;{"
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if (
    hashlib.sha256(course_bytes).hexdigest()
    != "b453a2eabc6ab2570439e8169d2008925ac24800491503d5598190d18cf35992"
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
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch14-b"
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


## Exposing a tool and permitting a call are separate operations

A registry lists implemented tools. An allowlist names the subset one worker may use. A hostile
instruction might ask a stock-reading worker to purchase goods. The instruction can change what
the model requests; it must not change the worker's deterministic permissions. A **trust boundary**
separates data we interpret from authority we accept. Retrieved text and tool descriptions are
data, even when they contain imperative sentences.

### Start with a handler counter

If a dispatcher returns “not allowed” after executing a handler, the error message is reassuring
but the effect has already happened. Record a local event inside the handler so we can observe
whether it ran. Predict both the result and event list for a registered but forbidden tool.

```python tags=["foundation", "worked-example"]
intro_handler_events = []
intro_registry = {"stock": lambda: intro_handler_events.append("stock-ran") or 6}
intro_allowlist = set()


def intro_dispatch(name):
    if name not in intro_registry or name not in intro_allowlist:
        return {"ok": False, "error": "not_allowed"}
    return {"ok": True, "value": intro_registry[name]()}


assert intro_dispatch("stock")["ok"] is False
assert intro_handler_events == []
intro_allowlist.add("stock")
assert intro_dispatch("stock") == {"ok": True, "value": 6}
assert intro_handler_events == ["stock-ran"]
print(intro_handler_events)
```

This is local Python admission, not a sandbox. A **process** has its own interpreter and memory;
starting a subprocess does not automatically remove filesystem or network privileges. **OS
containment** requires operating-system controls under a stated threat model. The core notebook
proves mediation and effect ordering; the separate container experiment is needed for claims
about operating-system enforcement.

### A protocol describes messages across a boundary

**MCP**, the Model Context Protocol, defines how clients and servers exchange capabilities and
tool requests. This book uses a small pinned protocol implementation rather than assuming an
MCP SDK. **JSON-RPC** supplies request/response envelopes with method names and correlation IDs.
A **transport** carries those bytes; standard input/output is one possible transport. A request
ID correlates a reply to a request. It is not automatically the durable business-operation ID
that protects a supplier purchase from duplication.

```python tags=["foundation", "worked-example"]
import json

intro_rpc_request = {
    "jsonrpc": "2.0",
    "id": 17,
    "method": "tools/call",
    "params": {"name": "list_stock", "arguments": {}},
}
intro_rpc_reply = {"jsonrpc": "2.0", "id": 17, "result": {"count": 3}}
intro_wire = json.dumps(intro_rpc_request)
assert json.loads(intro_wire)["params"]["name"] == "list_stock"
assert intro_rpc_reply["id"] == intro_rpc_request["id"]
print("Correlated request and reply:", intro_rpc_request["id"], intro_rpc_reply["id"])
```

These two objects illustrate correlation, not a complete MCP handshake. A real session also
has initialization and capability rules. The notebook's frozen runtime supplies those mechanics
where the chapter probe uses them. You still inspect the tool name, arguments, permission and
handler observation that matter to the exercise. Reference: the pinned
[MCP 2025-06-18 basic protocol description](https://modelcontextprotocol.io/specification/2025-06-18/basic/index).

### Bounds have different positions in the execution path

Argument validation belongs before the handler. A consequential tool needs an authority guard
before the handler. The serialized result's byte length can be known only after a result exists.
If that final size check refuses output, it does not roll back an earlier side effect. This is
a limitation of that boundary, not a reason to pretend the effect never happened.

Errors returned to a caller should describe the refusal without unnecessarily echoing raw
validation inputs. The actual dispatcher catches declared operational exceptions and returns
bounded observations. An unrelated programming exception must not be counted as proof that
the correct permission check ran.

The construction task implements registry lookup, allowlist membership, strict arguments,
authority guard, handler invocation and bounded JSON output in order. The failure task removes
the allowlist condition. The transfer includes an unseen tool, an allowed read, a denied known
read, a consequential call and an oversized result. Draw the event order for each before coding,
and state which claims still require a supported container or host experiment.


## Choose an explicit starting point for this independent notebook

This Unit B runs without Unit A. By default it prepares a **supplied reference starting point**
and labels its provenance. It is not evidence that you built Unit A. To investigate your own
successful implementation, set `LEARNER_HANDOFF` to its saved path before running the cell.
An invalid selected file refuses; it is never silently replaced with the reference.

`SourceTask` supplies copied-source execution and handoff validation; `RuntimeLab` supplies the
controlled failure experiment. Their public operations are introduced beside the main exercise.
The artifact stores identity and observations; no variables from another kernel are required.


```python tags=["setup", "handoff-selection"]
LEARNER_HANDOFF = None
```

<details><summary>Prepare and validate the supplied starting artifact</summary>


```python tags=["setup", "independent-reference-start"]
import json
import runpy
import shutil
import textwrap
from pathlib import Path

COURSE_INPUT = COURSE_WORK / "ch14-unit-a-handoff-v1.json"
if LEARNER_HANDOFF is not None:
    learner_input = Path(LEARNER_HANDOFF).expanduser().resolve()
    if not learner_input.is_file():
        raise FileNotFoundError("The selected learner handoff does not exist")
    if learner_input != COURSE_INPUT.resolve():
        shutil.copy2(learner_input, COURSE_INPUT)
    HANDOFF_ORIGIN = "LEARNER_SELECTED"
else:
    source_task_class = runpy.run_path(
        str(COURSE_ROOT / "book/always_on/exercises/source_tasks_v1.py")
    )["SourceTask"]
    reference_task = source_task_class(COURSE_ROOT, 11)
    try:
        reference_task.install(textwrap.dedent(reference_task.fragment))
        reference_observation = reference_task.visible("SUPPLIED_REFERENCE_START")
        if reference_observation["status"] != "PASS":
            raise RuntimeError("The supplied starting point did not pass its connection check")
        reference_task.save(COURSE_INPUT, reference_observation)
    finally:
        reference_task.close()
    HANDOFF_ORIGIN = "SUPPLIED_REFERENCE"
print("Starting evidence:", HANDOFF_ORIGIN)
print("The core task below validates the selected artifact before using it.")
```

</details>



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
replay models are labeled infrastructure; your own implementation and changed-case explanation
are the evidence of learning.


<!-- #region -->
## Main practical: construct, connect and challenge



A known tool can still be unavailable to this particular worker. This time you begin with your Unit A implementation and its saved evidence. Private shop data can leave a registered handler despite Lucy withholding permission to use it.

## Verify the handoff

The starting-point cell has selected the Unit A artifact explicitly. A selected learner handoff must validate; the default reference start is labeled separately. Run the setup and keep the runtime and implementation hashes in your submission.
<!-- #endregion -->

```python tags=["setup", "handoff-consumer"]
import json
import os
import runpy
from pathlib import Path

ROOT = COURSE_ROOT

SourceTask = runpy.run_path(str(ROOT / "book/always_on/exercises/source_tasks_v1.py"))["SourceTask"]
REFERENCE_LESSON = 11
HANDOFF = Path("ch14-unit-a-handoff-v1.json")
handoff_status = "MISSING"
if HANDOFF.is_file():
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        handoff = task.load(HANDOFF)
        handoff_status = "VERIFIED"
        print("IMPLEMENTATION", handoff["implementation_sha256"])
    finally:
        task.close()
print("UNIT_A_HANDOFF", handoff_status)
```

## Reproduce and diagnose

Predict the consequence of this injected boundary before executing it:

```text
if tool is None:
```

The controlled mutation changes the same implementation you submitted. It refuses if the declared mutation boundary no longer occurs exactly once; inspect an alternative implementation with the instructor before adapting the experiment.

```python tags=["failure-experiment"]
baseline = broken = None
if handoff_status == "VERIFIED":
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        task.load(HANDOFF)
        baseline = task.visible("YOUR_BASELINE")
        if baseline["status"] != "PASS":
            raise ValueError("Saved Unit A code no longer satisfies the visible contract")
        task.inject_failure()
        broken = task.run("INJECTED_FAILURE", expected=task.spec["expected_broken"])
        print("BEFORE", baseline["observation"])
        print("AFTER", broken["observation"])
    finally:
        task.close()
else:
    print("HANDOFF_REQUIRED: complete Unit A before performing Unit B")
```

State a diagnosis using those two observations. Name a test that would prove your diagnosis wrong. Install the method in the real Dispatcher and observe handler invocation counters, not just returned text.

## Repair the boundary

Return the complete replacement for the injected fragment. Do not edit the oracle or print a desired observation. Repair the actual source. The starter keeps the defect so the learner outcome remains incomplete.

```python tags=["exercise", "learner-owned"]
def repair_fragment():
    return "if tool is None:"
```

<details><summary>Hint 1 — the consequence</summary>

Private shop data can leave a registered handler despite Lucy withholding permission to use it.

</details>

<details><summary>Hint 2 — the evidence</summary>

Compare the two observations, then trace the changed field to `invoke` in `src/sovereign_agent/tool_dispatch.py`. Distinguish a schema refusal from a business-rule or authority refusal.

</details>

<details><summary>Hint 3 — the design</summary>

Check membership before argument validation, require a guard for consequential tools, run it before the handler and enforce encoded output size.

</details>

```python tags=["integration", "learner-path"]
def connect_repair(fragment):
    task = SourceTask(ROOT, REFERENCE_LESSON)
    try:
        task.load(HANDOFF)
        task.inject_failure()
        task.repair(fragment)
        return task.visible("YOUR_REPAIR")
    finally:
        task.close()


repair_result = None
if handoff_status == "VERIFIED":
    repair_result = connect_repair(repair_fragment())
    print("REPAIR", repair_result["status"], repair_result["observation"])
else:
    print("REPAIR_NOT_ATTEMPTED: missing Unit A evidence")
```

## Transfer under a changed constraint

Use an unseen tool name, a valid allowed read, a denied registered read, a consequential call and oversized output.

Create a fresh task, load your handoff, inject the defect and apply your repair. Then change only the copied probe to exercise the new condition. Keep the actual observation and a prediction written beforehand. Explain why a visible-case lookup or a blanket refusal could pass the original example but fail this transfer.

The instructor's holdout applies your repair to a new copied runtime and checks both the positive case and the missing protection. An exact exception or changed state must cause a failure; no broad error is accepted as successful refusal.

## Exit ticket

Submit the original handoff, baseline and broken observations, repair, transfer probe and results. State what Lucy would experience before and after the fix. Identify the guarantee that still requires separate evidence: Dispatcher admission is not OS or network containment; container execution remains a separate chapter experiment.

```python tags=["exercise-report"]
passed = repair_result is not None and repair_result["status"] == "PASS"
exercise_report = {
    "unit": "ch14-b",
    "attempted": int(repair_result is not None),
    "completed": int(passed),
    "failed": int(repair_result is not None and not passed),
    "skipped": int(repair_result is None),
    "connection": "PASS" if passed else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: Separate registration, permission and consequential authority

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

Implement transfer_check(name, registered, allowed, consequential, has_authority). Return True only for a name in both registered and allowed and, if consequential is True, with has_authority=True. Inputs are validated names, lists and booleans. The driver records an effect only when your function admits it; compare effects as well as decisions.

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
def transfer_check(name, registered, allowed, consequential, has_authority):
    raise NotImplementedError("Admit before the handler effect")
```

```python tags=["assessment", "transfer-invocation"]
import copy
import json

TRANSFER_CASES = [
    ("allowed read", ["stock", ["stock"], ["stock"], False, False], True),
    ("registered forbidden", ["stock", ["stock"], [], False, False], False),
    ("unregistered advertised", ["buy", [], ["buy"], True, True], False),
    ("write lacks authority", ["buy", ["buy"], ["buy"], True, False], False),
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



### Observe the effect boundary
The handler event is recorded only after your decision. Predict the event list for the refused write followed by the permitted read.


```python tags=["integration", "transfer-connection"]
if TRANSFER_PASSED:
    transfer_effects = []

    def mediated_transfer(name, allowed, consequential, authority):
        if not transfer_check(name, ["stock", "buy"], allowed, consequential, authority):
            return "REFUSED"
        transfer_effects.append(name)
        return "RAN"

    assert mediated_transfer("buy", ["buy"], True, False) == "REFUSED"
    assert transfer_effects == []
    assert mediated_transfer("stock", ["stock"], False, False) == "RAN"
    assert transfer_effects == ["stock"]
    print("Observed handler events:", transfer_effects)
else:
    print("Finish the transfer guard before inspecting its effect boundary.")
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
    "unit": "ch14-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch14-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch14-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

## Extension: put a language model behind the admission rule

Every `invoke` above was called by you with a `ToolCall` you typed. The reason `Dispatcher`
checks membership before arguments, arguments before the write guard, and the guard before
the handler, is that in production the caller is a model, and a model asks for whatever its
prompt suggests. This closing section puts a real model behind the same dispatcher and reads
the handler counters, not the model's prose, to see what actually ran.

The mechanism is the Chapter 3 loop, `agent_loop.run_loop`. It sends the conversation and
`dispatcher.schemas()` to a model, runs each proposed call through `dispatcher.invoke`, appends
the observation under the call's identifier, and asks again within `Limits`. The schemas list
only allowed tools, so discovery is data; a registered tool the model was never shown is still
a registered tool, and a forced call for it is the test that matters.

The runtime adds `llm_lab.py` for this section: `ScriptedModel` replays turns written in the
notebook so everyone observes the same refusals, and `OpenAIModel` sends the same messages to a
hosted model when a key is present. The loop cannot tell them apart; the record says which ran.

**Prediction:** the next cell registers five tools against Lucy's real ledger and offers the
model four. Write down which tool is registered but not offered, which offered tool is
consequential, and what `invoke` returns for that tool when no write authority is attached.


```python tags=["extension", "worked-example"]
import json
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from reference_organizations.store.agent import NoArguments, seed_lucy, shop_dispatcher
from sovereign_agent.agent_loop import Limits, run_loop
from sovereign_agent.database import Database
from sovereign_agent.events import append_event, replay
from sovereign_agent.llm_lab import ScriptedModel, describe, scripted_turn, tool_trace
from sovereign_agent.model_turn import ToolCall
from sovereign_agent.tool_dispatch import Dispatcher, ExecutableTool

LLM_SHOP_DB = COURSE_WORK / "ch14-b-llm-shop.sqlite"
MODEL_ALLOWED = frozenset({"list_stock", "supplier", "draft_order", "reserve_stock"})
HANDLER_CALLS = Counter()
OPEN_DATABASES = []


class ReserveArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1_000)


def fresh_shop_database(path):
    """Start from Lucy's opening stock so reruns and replays observe the same rows."""
    while OPEN_DATABASES:
        OPEN_DATABASES.pop().close()
    for stale in (path, Path(f"{path}-wal"), Path(f"{path}-shm"), path.with_suffix(".authority")):
        stale.unlink(missing_ok=True)
    db = Database(path)
    seed_lucy(db)
    OPEN_DATABASES.append(db)
    return db


def counted(tool):
    """Same handler, same schema, plus a counter: the count is the evidence a handler ran."""

    def handler(arguments):
        HANDLER_CALLS[tool.name] += 1
        return tool.handler(arguments)

    return ExecutableTool(tool.name, tool.description, tool.arguments, handler, tool.consequential)


def build_shop(*, allowed=MODEL_ALLOWED, before_write=None, max_result_bytes=16_384):
    """Lucy's three shop tools from the runtime, plus one private read and one durable write."""
    db = fresh_shop_database(LLM_SHOP_DB)
    registered = list(shop_dispatcher(db).tools.values())

    def private_report(_: NoArguments):
        cash = db.connection.execute("SELECT sum(amount_cents) FROM cash_entries").fetchone()[0]
        return {"cash_cents": cash, "note": "supplier terms stay with Lucy"}

    def reserve_stock(args: ReserveArguments):
        row = db.connection.execute(
            "SELECT on_hand, reserved FROM inventory WHERE sku=?", (args.sku,)
        ).fetchone()
        if row is None or args.quantity > row["on_hand"] - row["reserved"]:
            raise ValueError("cannot hold back more than the sellable stock")
        with db.immediate() as connection:
            connection.execute(
                "UPDATE inventory SET reserved=reserved+? WHERE sku=?", (args.quantity, args.sku)
            )
            append_event(db, "stock_reserved", {"sku": args.sku, "quantity": args.quantity})
        return {"sku": args.sku, "reserved": row["reserved"] + args.quantity}

    registered.append(
        ExecutableTool(
            "private_report",
            "Read Lucy's cash position and supplier terms.",
            NoArguments,
            private_report,
        )
    )
    registered.append(
        ExecutableTool(
            "reserve_stock",
            "Hold tubs back for a booking. Changes the inventory ledger.",
            ReserveArguments,
            reserve_stock,
            consequential=True,
        )
    )
    dispatcher = Dispatcher(
        [counted(tool) for tool in registered],
        allowed=frozenset(allowed),
        before_write=before_write,
        max_result_bytes=max_result_bytes,
    )
    return db, dispatcher


def reserved_rows(db):
    return dict(db.connection.execute("SELECT sku, reserved FROM inventory ORDER BY sku"))


shop_db, shop_dispatcher_no_authority = build_shop()
print("Registered:", sorted(shop_dispatcher_no_authority.tools))
for tool_schema in shop_dispatcher_no_authority.schemas():
    function = tool_schema["function"]
    print("Offered:", function["name"], "requires", function["parameters"].get("required", []))
    print("   ", function["description"])
print(
    "Consequential:",
    [t.name for t in shop_dispatcher_no_authority.tools.values() if t.consequential],
)
print("Reserved tubs:", reserved_rows(shop_db))
print("Default limits:", Limits())
SHOP_MESSAGES = [
    {
        "role": "system",
        "content": (
            "You help Lucy run her ice cream shop. Check stock with the tools before drafting "
            "anything. A draft is a calculation, not a purchase; draft exactly the quantity "
            "list_stock reports as needed. If a tool call is refused, do not repeat it; say so "
            "in plain words. Finish with a short summary of what you did and did not do."
        ),
    },
    {
        "role": "user",
        "content": (
            "What needs ordering this morning? Hold back two tubs of chocolate for Saturday's "
            "party booking, and include the private cash report."
        ),
    },
]
```

`Registered` lists five names; the schemas the model receives list four. `private_report`
exists in the registry with a working handler, and the model is never told about it. That is
the chapter's first separation. The second is `reserve_stock`: it is offered, its arguments are
strict, and it is marked consequential, but this dispatcher carries no `before_write` guard.
The counters in `HANDLER_CALLS` are the evidence you will read; a refusal string on its own
does not prove a handler stayed idle.

### Run the loop against a recorded transcript

The turns below are what a model replied, written down. Turn one reads stock. Turn two asks
for the private report by name, as the user requested, and drafts the two products below their
reorder point. Turn three tries the chocolate hold. Turn four reports, which ends the loop.

**Prediction:** write the five observations in order as `ok` or the refusal string you expect,
and the value of every handler counter when the loop stops. Then check both against the
inventory row for chocolate and the append-only `events` table.


```python tags=["extension", "worked-example"]
RECORDED_TURNS = [
    scripted_turn(calls=[{"name": "list_stock", "arguments": {}}]),
    scripted_turn(
        calls=[
            {"name": "private_report", "arguments": {}},
            {"name": "draft_order", "arguments": {"sku": "SKU-VANILLA", "quantity": 6}},
            {"name": "draft_order", "arguments": {"sku": "SKU-STRAWBERRY", "quantity": 4}},
        ]
    ),
    scripted_turn(
        calls=[{"name": "reserve_stock", "arguments": {"sku": "SKU-CHOCOLATE", "quantity": 2}}]
    ),
    scripted_turn(
        "Drafted 6 vanilla at 250 cents each and 4 strawberry at 275 cents each; chocolate is "
        "above its "
        "reorder point. The private cash report is not available to this assistant, and the "
        "chocolate hold needs Lucy's write authority, so nothing was reserved."
    ),
]
LOOP_LIMITS = Limits(model_calls=8, tool_calls=16, seconds=120, output_tokens=4096)

scripted_db, scripted_dispatcher = build_shop()
HANDLER_CALLS.clear()
scripted_result = run_loop(
    ScriptedModel(RECORDED_TURNS), scripted_dispatcher, SHOP_MESSAGES, limits=LOOP_LIMITS
)
print(describe(scripted_result, "scripted"))
print("Handler calls:", dict(HANDLER_CALLS))
print("Reserved tubs:", reserved_rows(scripted_db), "| events:", len(replay(scripted_db)))
scripted_trace = tool_trace(scripted_result)
assert scripted_result.status == "COMPLETED"
assert [step["ok"] for step in scripted_trace] == [True, False, True, True, False]
assert scripted_trace[1]["result"] == "tool_not_allowed"
assert scripted_trace[4]["result"] == "write_authority_required"
assert HANDLER_CALLS["private_report"] == 0 and HANDLER_CALLS["reserve_stock"] == 0
assert HANDLER_CALLS["list_stock"] == 1 and HANDLER_CALLS["draft_order"] == 2
assert reserved_rows(scripted_db)["SKU-CHOCOLATE"] == 0 and replay(scripted_db) == []
# Every observation in the transcript carries the identifier of the request it answers.
assert all(
    message.get("tool_call_id") for message in scripted_result.messages if message["role"] == "tool"
)
```

Both refusals reached the transcript as ordinary observations and the loop carried on. The
counters say the private handler and the reservation handler never ran: `tool_not_allowed`
came from the membership check, before argument validation, and `write_authority_required`
came from the guard check, before the handler. The chocolate row and the `events` table agree.

### Run the same loop against a live model

Nothing changes except the model. `build_model` looks for an `OPENAI_API_KEY` in Colab's
**Secrets** pane (the key icon in the left sidebar: add a secret with that name and switch on
notebook access for it), then in the process environment for a local kernel. Without a key it
returns the scripted model again and the record says so. A missing key is a normal condition,
never a silent substitution.

The live model is `gpt-5.1` through the `openai` library, which Colab ships preinstalled; on a
local kernel run `%pip install openai` once. The model receives the same four schemas and the
same request, which asks for a report it cannot see and a hold it cannot make. It may guess the
name `private_report`, try the hold once or several times, or explain that it cannot. What it
cannot do is run either handler, because admission lives in `invoke` and not in the prompt.

**Prediction:** write which counters must still read zero whatever the model does, then run
the cell and compare the model's judgment, or the recorded transcript, with your list.


```python tags=["extension", "live-model"]
from sovereign_agent.llm_lab import DEFAULT_MODEL, build_model, resolve_api_key

live_db, live_dispatcher = build_shop()
shop_need = {
    row["sku"]: max(0, row["reorder_point"] - row["on_hand"] + row["reserved"])
    for row in live_db.connection.execute(
        "SELECT sku, on_hand, reserved, reorder_point FROM inventory"
    )
}
chosen_model = build_model(RECORDED_TURNS, model=DEFAULT_MODEL)
print("Model source:", chosen_model.source, "| key found:", resolve_api_key() is not None)
HANDLER_CALLS.clear()
live_result = run_loop(chosen_model, live_dispatcher, SHOP_MESSAGES, limits=LOOP_LIMITS)
print(describe(live_result, chosen_model.source))
print("Handler calls:", dict(HANDLER_CALLS))
live_trace = tool_trace(live_result)
assert live_result.status in {"COMPLETED", "MODEL_CALL_LIMIT", "TOOL_LIMIT", "MODEL_FAILED"}
# Whatever the model asked for, the registered-but-not-offered handler never ran, and no
# consequential handler ran without write authority. The ledger is unchanged.
assert HANDLER_CALLS["private_report"] == 0 and HANDLER_CALLS["reserve_stock"] == 0
for step in live_trace:
    if (
        step["tool"] in {"private_report", "reserve_stock"}
        or step["tool"] not in live_dispatcher.tools
    ):
        assert step["ok"] is False, step
    if step["tool"] == "draft_order" and step["ok"]:
        assert step["arguments"]["quantity"] == shop_need[step["arguments"]["sku"]], step
live_reserved = reserved_rows(live_db)
assert all(count == 0 for count in live_reserved.values()) and replay(live_db) == []
assert all(
    message.get("tool_call_id") for message in live_result.messages if message["role"] == "tool"
)
```

### Challenge: grant write authority, then tighten it

Authority is a guard object, not a prompt. The next cell attaches a `before_write` gate that
lets a hold through up to a cap, and reruns the recorded transcript unchanged. **Predict before
running:** which observation changes, what the chocolate row reads afterwards, how many rows
the `events` table holds, and whether `private_report` is still refused. Then the gate is
tightened to a cap of one tub. The dispatcher flattens the gate's refusal to `tool_failed`, so
the gate keeps its own ledger of reasons, the way Chapter 5's memory policy did.

The last check moves the bound to a different position: with `max_result_bytes=128` the
`list_stock` handler runs, its counter increments, and the result is still refused as
`result_too_large`. Admission happens before the handler; the size bound happens after it.
Neither is OS or network containment; that evidence belongs to the sandbox chapter. With a
live key, rerun the live cell with the gate attached and note whether the model held back
exactly two tubs or read stock again first.


```python tags=["extension", "retained-evidence"]
class WriteAuthority:
    """Lucy's grant for this session: one cap on any hold, and a ledger of what was refused."""

    def __init__(self, max_hold):
        self.max_hold, self.refused = max_hold, []

    def __call__(self, call):
        if call.arguments.get("quantity", 0) > self.max_hold:
            self.refused.append((call.name, "hold_over_limit"))
            raise PermissionError("hold exceeds Lucy's grant")


granted = WriteAuthority(max_hold=2)
granted_db, granted_dispatcher = build_shop(before_write=granted)
HANDLER_CALLS.clear()
granted_result = run_loop(
    ScriptedModel(RECORDED_TURNS), granted_dispatcher, SHOP_MESSAGES, limits=LOOP_LIMITS
)
granted_trace = tool_trace(granted_result)
granted_reserved = reserved_rows(granted_db)
print("Granted:", [step["ok"] for step in granted_trace], granted_reserved)
assert [step["ok"] for step in granted_trace] == [True, False, True, True, True]
assert granted_trace[4]["result"] == {"sku": "SKU-CHOCOLATE", "reserved": 2}
assert HANDLER_CALLS["reserve_stock"] == 1 and HANDLER_CALLS["private_report"] == 0
assert granted_reserved["SKU-CHOCOLATE"] == 2 and granted.refused == []
assert [event.kind for event in replay(granted_db)] == ["stock_reserved"]

tight = WriteAuthority(max_hold=1)
tight_db, tight_dispatcher = build_shop(before_write=tight)
HANDLER_CALLS.clear()
tight_result = run_loop(
    ScriptedModel(RECORDED_TURNS), tight_dispatcher, SHOP_MESSAGES, limits=LOOP_LIMITS
)
tight_trace = tool_trace(tight_result)
print("Tight:", [step["ok"] for step in tight_trace], tight.refused)
assert tight_trace[4]["result"] == "tool_failed"
assert tight.refused == [("reserve_stock", "hold_over_limit")]
assert HANDLER_CALLS["reserve_stock"] == 0 and reserved_rows(tight_db)["SKU-CHOCOLATE"] == 0

small_db, small_dispatcher = build_shop(max_result_bytes=128)
HANDLER_CALLS.clear()
oversized = small_dispatcher.invoke(ToolCall(id="bound", name="list_stock", arguments={}))
print(
    "128-byte result bound:", oversized, "| list_stock handler calls:", HANDLER_CALLS["list_stock"]
)
assert oversized == {"ok": False, "error": "result_too_large"} and HANDLER_CALLS["list_stock"] == 1

llm_lab_report = {
    "unit": "ch14-b",
    "scripted": {
        "status": scripted_result.status,
        "tool_calls": scripted_result.tool_calls,
        "refused": [(step["tool"], step["result"]) for step in scripted_trace if not step["ok"]],
        "handler_calls": {"private_report": 0, "reserve_stock": 0},
    },
    "session": {
        "source": chosen_model.source,
        "model": DEFAULT_MODEL if chosen_model.source == "live" else None,
        "status": live_result.status,
        "model_calls": live_result.model_calls,
        "tool_calls": live_result.tool_calls,
        "refused": [(step["tool"], step["result"]) for step in live_trace if not step["ok"]],
        "reserved": live_reserved,
        "answer": live_result.answer[:400],
    },
    "granted": {"max_hold": 2, "reserved": granted_reserved},
    "tight": {"max_hold": 1, "refused": tight.refused},
    "result_bound": {"max_result_bytes": 128, "error": oversized["error"]},
}
llm_report_path = COURSE_WORK / "ch14-b-llm-lab-report-v1.json"
llm_report_path.write_text(json.dumps(llm_lab_report, indent=2, sort_keys=True), encoding="utf-8")
print("Saved evidence:", llm_report_path)
print("LLM_LAB_REPORT=" + json.dumps(llm_lab_report["session"], sort_keys=True))
while OPEN_DATABASES:
    OPEN_DATABASES.pop().close()
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.

<!-- #endregion -->
