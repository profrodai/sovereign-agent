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
    lesson_id: memory
    planned_minutes: 90
    resource_id: profrod-sovereign-agent-ch05-b-memory-repair-transfer-exercise
    self_contained_runtime: true
    source_basis: 444c5f6
    source_unit: ch04-b
    source_url: https://github.com/profrodai/sovereign-agent
    unit: ch05-b
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
# Chapter 5, Unit B: Break, repair and transfer durable memory

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

**Student edition · 90 minutes of dedicated work · 2026-09-09**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/profrodai/sovereign-agent/blob/main/book/exercises/ch05/profrod-sovereign-agent-ch05-b-memory-repair-transfer-exercise.ipynb) Runs on Google Colab as it ships today, or on any local Python 3.12+ kernel.

This is one of two practical units for Chapter 5. Unit A constructs and connects the
mechanism; Unit B investigates a controlled failure, repairs it and transfers the invariant.
Each is a complete ninety-minute session, with its own setup and required conceptual introductions.
Basic Python variables, conditions, loops, functions, lists and dictionaries are the starting
knowledge. Libraries and specialized concepts used here are introduced below before the main task.

By the end you should be able to:

1. Explain the chapter's mechanism using a prediction and an observed intermediate result.
2. Repair the failure: Putting the new preference first does not remove contradictory old guidance. Remember, correct, close and reopen SQLite; invoke context and inspect the actual system message seen by the model.
3. Solve **retrieve the newest eligible memory under a limit** using changed inputs and an independent expectation.
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

The collapsed cell contains 91 frozen teaching files. Base85 represents compressed bytes
as text; `zlib` decompresses them; SHA-256 checks that the decoded files match this edition.
These are supplied packaging operations, not learner algorithms. `tempfile` creates an isolated
working copy; `Path` handles file locations; `sys.path` tells Python where the supplied modules
live; a `.pth` file, the mechanism an editable install uses, tells reviewed local subprocesses the same. The code is available for inspection below and performs no package installation itself.
The subsequent lesson teaches the libraries used by the mechanisms you will implement.

Run setup on every fresh kernel. It writes scratch runtime files separately from your retained
`practical-work/ch05-b` folder. Rerunning setup restores the frozen support files and keeps
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
    "?MbK=i|(<k~n}!S;YjzOX)XBF85F!Nvbi-n+23ja}J-e+7|e#-u~iva6Dtu$rAw$*hznw&a%N@?<Pu5+n~Lv_OCX"
    "K+|lu{`-9Ub>1LlSLM#!+uixfA_*KEoX0-<vG&@4>RG5+S`qCHM)+na5^K{0O>fKcHdli=^m4GNRRxO*mc^76&Pl"
    "q?AfXp(kmY50UvnB1)?8rvFMgn;LD_M5-XSFviMxj^tGq|kMy5oaOu_1yCRIv2(RXQqrz>QVBqs^;RMERpLQu8Hi"
    "WEtEi$!M2q17sv+J!fTUJ=Cj#Ht~M2)-Fq6>zm3^v?ANdAtwh6!pU4e<!#@`0CeXxu%%%KAw#UVX*0zH?(nkBpo^"
    "Ope1E5xh~5bOiQW|J-uBw{XYy|Om+H)W~M;F0zKyvdvmH4iQ*cit11?_L7{dZQYJ%`pdrzTb)Io}A(<JCX+Uk4h3"
    "aD*n$8zz`qSiYgBw?5NLDpFm_r38c5P+Nyt#NaevM#F?mf)v)%f&sd_6e_u4(w`;_dkS<ZN>C_H6RE@!xH~d$7XU"
    "N8r{R_dW0=EOABROyCB8TI*d38<Nu~mAw`4J7`y<<ImB5jk+W|8#sRwS#fzwM_}s^h=kBFK6z-11AaJWgkr)X4Pk"
    "VXTXAE25BnlnLvk$!s&{KZ#@!ZWr9RN_{i1C8OMpv#ys-k?gr^zly9c+b=~&a^y1$6UDC$hHNPCz$$qBQK@gKMR-"
    "IL_JgcL#=96b*dgTX8{k|;ffis70PMV<U>a8<cn4(vv!S~SXh)i76SZk;sjJ10(jP=KL=Vf_Q@hm-~}rH)VSmXU="
    "RXL|)oJt`3ZXtQ*ItwL&6IVD$gL}KQU)yZ`#1y5!CEjUwr26&iBITvm!mj}uPWQbfvLDK<t8FAecGsO|r&=n#Emn"
    "$&lw$kz_Ld{@GBxt<?w4mJ}K@$o2aIzZESm<;+8iL0Q;<#ybyFs>O`0mSKFnD-yNa>x>Cg@X85QkH-dO~;!^T6jC"
    "yzCD~Ij_{e<4FSs20}Rr=ce0CQUVp@`G!)^*El)G%CoLBy2*jKS<N_A+1vGHnNLW^8<D%uGCW0?cd`ZWVZvqoFJL"
    "i#eh`P_2np_Fus-$@Jxn8*rw;#Y4c<qe)D0Un+;ghftT36oL)|K?q|?Q$kg6HIa5)=zsp<Ka#WUi6dEt!ATlNx1("
    "I0^ufG_SQ&z~pXGk(F15J^zT8F5dNgSu~47O5eY#wv!PZ@=g@^j^xJ(sm%T0L>F)05S)8joH;G60}PhRq(nL6<5@"
    "4&USzmrq%3ix)VE=nq`RqI3pZSOh)$>3ojRVE#8NE)IWy#l(27QTgy_L)QwsTR2Nm4j_|k~!|AfF2!-ePu(bi_p{"
    "&hEF(sr|^wCD!aHy;8=V$h%4&c~+if<y?1=*uQ$IdOpS5N+RlxVLL4rEKTDO}E!aLWsWwf^O%BJBoRLV8+vW&g<r"
    "89}q0u8G%wFx~p-2NtlezaJ$p>`-1@KsZ7o0{TI*A?u+3#kBv>|AM*7#B4&61iv8ctPvvkrI8+O49y}-NPHLg!UO"
    "De6m%5~G+plqjUEVa`oS64n7g1=U|2SAkUx!kQN%zGEhs}2kGu2a?U^G&0-M)VI^t6VIDKm>y{#>HZBRR2BAqL83"
    "z#x=7NNrScDG2u6T$uyvOy$e((%>cQMynFqX&gvDqFK_igHluLGlhZTtY<kXeOE(<48&H_DuX`8@O_sl;{<-&PL+"
    "h@)PvP`-I=t_f!fpDzjJ-x3B;x^+ZrPYQG#SX<Y*0#zZZbWo79idAZfV9#7mM=0ijsCGKEqM<DDlzoAXuO(yHIZY"
    "D6MlZi<o_wqn+rf4x}LIGT9w!%!ijZ=t5d_jjtV?^$8`tZMy#MMb(u9oN`_c`eRZbz&h3<Z7)6BGDVF*8A2h>`4t"
    "iLqR{x17u1zQVrTh*kQz^I~wU-ICof`GJp=c%T^H`-6_Mz$??A!D$pM@3yA=3#rv;8~XsQI>BY+tjPhG`~%D6A5g"
    "Ys=h-vvLN@?&YU9k{HyQ4nT)q06SWzpWCIZW{wuA`rYX)V$Dd=Ln86932CM!?S`?TvgH_c=Zl-XR_FjV@c{&4)!O"
    "Cf--2UL%2Lc=E@0Yr|LYs$7Ty6Vl*!|*_7m(p9fANXdV>ho?0oQC1!T+(Mb(`^!NOC7J$t*4Dsi@Xa4mf?UJy06Q"
    "G%YfLf`6PGI^;NnZh-1i{_R#Rn(U*sSW0@BNHULExULl5d9D(x+zMcjN>|H3WkgU=i(tOndYcdc35Pf;8bpz$>)@"
    "#bZq@$NAw>L(ec3U@R>eE^upOS3>OO;GJIH;rw44nKB+!2m0H2q?2Qy2yTh{-Hn=<(}0zO8wc*2Dqj8t<`D|MCzJ"
    "rQ<3z9LoCYeWc~>4dR-Jmpk!oN|^R+fhGUw{0yv1XJPodq5iAesu!Y0Ved}-!mC~jZvj|t{B00Oa&%r$LpG!Z9T~"
    "@abV_f-uy#p{8eWi;X&kODE1QQDOgNt@6#y4>XP;4qAujL<sEVpOBg!WkB}AdQPY1%&)v<Mx|7=xd-)3A=69Wmf("
    "Kw_c{`F63mJ=deleckv%rbZ#W!Cl~CG)hZ0E;^%m1~OHXi-wY5#nieQ>k=?hEY={w;S-fkr`a21vvcg)y{BlfFI1"
    "!rlpz!?f}fgN%Oi)mMGjPuu)na?b-Hr#H9jnJ&L%25f!AT!*+!6J_IFo|2c|-VoikB<}fyhV?V<Gh9~D4s);cfNr"
    "?<tbR7&1p0rvu$*gsxYCgJnz<vlsv@{CAv+4i7&en2qB5iT%E4X#oD-CfR7;2!L(+dibqdp?uS(_cQrOgh(qp7KY"
    "ZJiRqhE}A*6!!A`i0-0Jvx<c;8Z)8{K-B@tGb3AEd)e%Gx)*R)hPeh9NF=x4YK5vpraM=vH`S(Y<Z7ygxvokmS;k"
    ">T4IhyDHnWV2gxS5(U0lH-g>^#o*)4^2InGutnc0zFI*nDUv)Zm*wVEZ}2TO+`iix3p)|;zXBD&dLOQepgN!%8k$"
    "v4n?xUEu&WCb_$%~4h63bZuLYavXemlK<!qGng@YJbr15l{LZJPA?<FftXeMZxQ3g`XTO9tyWfTj}dXv?(1m8({-"
    "bn~T2*(zv9a8o27Mslo^Gy~O(gYG-*5rUxazLdkYiZjXitSDaY4-yA)3ef=(-tM+65OFW-TW@f10$nqVx-QsxOt("
    "9ao;rN$Z8=|+>1?On!;mh`0B$G6_jq<+1>*jvXL)eWq`4H7pSf=5CT6KdI2!~lrggFFT(PSlvn1Xi)$xvok*%0Uf"
    "t4%Q^AB~s`BC2}293P-a8uM|E^4&=WiWAdIm%h*+4?cCgFid>mjYgk?%S2JfaF1L|VQBpFA+ca7<_fca9ukKEZHe"
    "sIYdFZ*i6FN)3f6<q(2jKH;0Oh0qJN$^OkJGfJmU3*R(7M-AL!#pI_H<Lk`SB+BLqJ`rKX;Ke6YLg*PBV?YUsn$j"
    "}M(MR>C3uqL=>DkKG4c4Z_WD3@5)?VkI?WL7yd9_hI<`@$tt8|Im$a#JA(;R`a!(`7TF~@L*6HGo)0P$(z%+Om)*"
    "s)>%<dg$RxCdU^cv5B=jm_Fw!757O5N`zY67mX=jNT_db|f&4beLQz08@4UpM@LqBOY|}lkxz>a?r~r&fCoh#i0m"
    "jv;kqXPuNOD`H6fK8}6q*zP;Yb|T{Q-OJSE2a!)U5-h`v{0qR$s%cLwSyZ5-~`UYgo#l*FwhVW5{yeoW4CJho<eQ"
    "WFKX#n-J<>r^Ui5E7sxyWKgc3jAUJ50Umtbm{wO}GD`l?Yp2r5mJrEC><FIYz$^Uu=190+xbrQfFn>IbI%XV#5nS"
    "LsgJ|WIB@GkZ6zv6RIUs=1Zd{F9rVtKaKQee`aU{C8)u6T(sP-ItKM{>VGV;@!@kha2Ih-MHBZ=nxHX&_CRvf1G`"
    "0e;V_A`8-jWK~d-&)ncSWi_XqLCq+C{><`uVdIzt*@OCFKZw<nBZ{>l@G!;bgji+BA)-p-dt{)J$Hw;B5Y3MtBvs"
    ">khXxq8%*Sig6Uh;I1$dj0E-!w%(*!-f;!q5=RKtBbe82=laX6JU<|S@MWJ(6EK9u5Kr#Z{dA|X05>ljt9{b7e)r"
    "*^>*drc#d!va^SFFey*6M=SW$oX7WAf~<`(0eSrj6pzQ1k*<TFmtpku;lv(RFHphZ4U%l5jK9k##11+%7QJIWpU("
    "%VWWeYCY#^9vss!bK(Qr3yrR2RX;b&Y7rlOOe0^FMcI@^Hpk+1aq^y^Xdv0d{?ev#f6f^&$(M(4I{8+fQK*W2x~b"
    "|i!pPDx&a%dYmXF0XV0J{3Z;Ew#3p6Wg!NFIHNy>?iB_ppxyl}#PM`pzH*fOLYtKLP3Kq`bCP=ZVHugP~Wqt}Fax"
    "Ghh!ifP8L=QGp0MaCVsFamn21NS?~qWGnD?y48<YFR*!oNFN#g8hUONh>S1Z5COLa62@)zqq{)I~cm(O(v3V2&Id"
    "ew8wRMv7yvAWjc-dT~4pr8~9^ds~FHxztlW0Yvq>?#)mr5YLpn1U&;;*Kl0ks)J3e9#gwtuQ`b(8+PXY=D?uWo4m"
    "2s!g2U;WaV+^gDmSJgrZwPIx<#_MKTf{;)Axs!IT+E$ki}{K9<8qrnAZP_zvv*%j{F=BJ$^l?)GcITRS_kkXSF^4"
    "Wqf`;d4G9!J@%$*dk5J7Rk|HUxp-iI>4(uD9SA@lo9RmWfspQY+h}@X)L<}XTPlYoQSQiwhbtOY5U`X=Ozl;iVB%"
    "ui0aizqZa;8)!;j87g^C^7C&f!Owj$kCdw6X+s^33#$`J$T&pFg@i%z+$cqaj!l>Ps2mx4wC>{|`<yG?OVYk}yc_"
    "Nu|(AOHD}-PV`Fw)XbY@W??2#X!rkL?u<B<StWyDcWP(nEL&Q9@<KOWnB!?=Z}Aw{NcMl?(Jek3UQwfi6NM{o@eV"
    ">p9b|h&zg=bm!8AgC4O-yNDmGA923qduO%|-28r>n^U<%BNKu|ak31}U?W5Sdeep@<<yv{His-1~r`iHQ^h7zTKy"
    "T&DTqqc|s-q?7TV;Z4T)S9Fy=g`<CD*p!1K?$-ez&UL*+L_iq#v$EPJh97^n&mm{q<lrcGLt0m1Tk<5lEuxy!fNP"
    ")y?V<CJGX+(rT!}nvPka545Q1O+;9U4iOOy983XF#E-0OJ0^$JQsfjx+0C#xtBn*peuQcbp0bX+ZlQ<Wt_gZJQT^"
    "G(wJ^K_OWc{B=uJ9aV7>h}>8rMaLWm`#%8~6tc?5uM$!d%PdQK*XlhliL376&}+(^a2i8j#4;jJBe4)1CHwKy;Y_"
    "L2~QsQP@DZt6y}V~b44icjUe@+n;`fXUa%gc$J)yXO)n1$Iecw6-4=fo~zp9lcfd`^il^!yksOYKGiO1;v<DjM~d"
    "{VzRJ(D}=J~qHg-bgNqeKE1?ag`UIgIyb*x{_AdQ|MeXl}OTSXZ50HI;aVW~wSDGj$xvk308s2QM&(l@b17J^Gdp"
    "@%@R@~6Uq<=em{W>&*n9=QZS>A8fQEY@xfAW2!gKe5MLLNT)L!_XPqrt{(ELX)1EUrj9;N9Ne5GY8xCEHuCAgA7j"
    "6#GtnZ>e~9f8Ouwzt6zY53=)vV_HgfR?o}h8@d)~cvT}YilG~>aIcK5I@f${jZaZUb%(cdg=7j@0pz3{@7c|&Y{B"
    "K%VRWiYeM%{vj@f*$)-(VmaaY#!vQmTJBKG4HRH)QHv7VhS`N=oD;?IZ6-|4b<np$}ar7t^BMAr&Vb3AA0L=%Bwu"
    "0nw70?>ff&C!Rn{~yQwKY#o^g5%WZMi|O$^xI@!)=*px($Ix`kC5ZYOw~)O?Dj793w8xR4;>15Xh^$T@aFD*;&>>"
    "(xkKHBmxWr*)B<2Vb+X#j4M{omj}4}Au2fOuG#?rIy%LF-OHjzM6hZxus_E35Rp)c^EcuN3*JoH#*tKr*Z2wi%XE"
    "#)9Z&bd6XeB=P5~LUSk8F)^&f|sNIH(;%)Zoc;r<=fqY<(o)<KS3l;yr>*@eK~u&zT<lg_VwBXMA#Q1#Ba>&N+gu"
    "J_9?3^Iff0h_!XT#M+$mo%0<nSJ<h}*PpUFBY(L4Xl`^OfCWt$Np{2vrn}++Ud)DiyGUUQd{e1O*bCp#E0^JQ0&x"
    "WE%`DI6I))N-AHsP932y4;7g_Ytq8g^AQBWAsT<A+yS6QYADWSIt&ux1Q0aDXtERo?{)G@Ejp;vxgCa-9$F&SX&t"
    "_FGAxj9P7e{v+N{lHG;{i)NsOtYA$ZS@g}kWdwMtF-N@(DwD!*|0kp>G7}XfUcsusVCI!vFWZ`%PnlqtL~=%7b)`"
    "=YUz6Y_TolZ7+!_{v;4BU`-phepF-?(q@0(#AtFCogAo4MvC5>Cl_5ZOO4c3X_0m-iO-f^Am*XK2+s;zD-2M$Oo_"
    "zH_&9fEYIVoROc6(875A9lNT}xbtvXQMetYm}j!yhk?_wOSb489(ZxS7&yGB0q~zC6|&hu#(yfgXW=@da2lz+byS"
    "p0ai3h((idrV5-rc$dhDFZ#vDj~2SKDz^|~dvuY$XH<$$_Gt3{=kev(T8qgjc}jBXX>xJt{_q!PUm?B<1=SZ_$Nu"
    "K1r%T9Fbv{^KT>~}4@_YsM+L{X-GBb8ST)}1O406`?_|X}ekS=4*L-K!6Q*f|jnprQn;y?L{u3b-VPD%<TD%j~d*"
    "a^L$u^U`u(EFZtddGpY(D@qHgB8`z+b%us2tL94E#MgCKD#PPSkFa|)F?S-U<dc=Uq;FCK^!mCxmy7KAIm{`uW<}"
    "Hd>vW%{jaGn7}O6;o+p3$<M+qMElJF%=|EMi<ayG0k^J6t?0NFtvHi;Cs2h<A!Ou58xF~E?z);Qj?hnZ`Jzl?;FZ"
    "6i9H!t8D>5cxvYFamYhoBU_o&CxjdVQk@Evy(6S^oYt&~Lx^Bz4}ulHZ``yPNPe{E9|x$ByZfkqD7)-5hN+Gwjza"
    "VZe6i>=~cBFrdrU2+z(Ph)Qax=Wc8Y@TkSFm9G?RGLPmYISg^&1G>q-@Cjz;B*WRdT2%-L7$#r!bn9&63oN5jx1S"
    ";S1;w(n|FvV=8y9xR(U?S{JJ~AB(~25wfk%kk!pQ%Nk6K>EuLfKZU1-gA{8C&3Fs69J%a1K$Tz-v+@D>b&KT^<`{"
    "@k-(I_`_@91s2*?r?bU@y7uPi+*xEcnM!yEy)$xqHC{$Ens{rey~|XJ;*&8tyYzbe#E(vrA@cSS3eY;`lQ@T1YD0"
    "t7<b2KJg4<~$X7%Rv5v=xRxSj0Q_PntmqN(Gd2rzLB#KU*g+meXd#p@TEL4@0n+lJZin(AUtLG01=Ac!W)&|0%zD"
    "t2C>)Ec{JWCd84$Qm=(|^60@16o3CDI6yfm$;m-c(zx-6=gAcocvv(U5fBE45~<v!-v=BoArL<W&e-T}TSGRL?;A"
    "wsOsB1(2M6r;=y*_R`7vFYsFDoUbP&5^1um(v<=xOUTee|22NiS)QB#v8I~PsY$FQhXPF@GFM6}Dt3@LvEJ^QyRy"
    "(pCIiSFblq48>X+2r!7H7^JH07{8N<-1x(^{FKlGI*b5rD)aflzZ4;~qL0hpI(m;v@)5wjBvr=8}N6`vqB!{~D)h"
    "$Vi(nVP2?WW2S$rZM6#09;m-OH3uE)JN3-&1i9}%hw_>4Tue$+9OrEt!)xdOh(TdE|9JzwjmyRdwKEp;%a;aD;pO"
    "*CDy}|WAYB_!>h9^xDIv#^P-+;^3D_soAEHga-l*iO_FE#ib-M@n+hGTY`SM=E6M#g#k$O(yX0`yEP(8q9VAy}q8"
    "I&Sna&%`a9gDqb(jK=AO_?Bo`^oGDen}I9z`a(DUkp)Yh;?!WI9vJvQiU#lPPX+%o2s(HVu;G!3G02ll|Kkmp*S+"
    "8ZOGq&1hgaO<Y!$8GKD|V)c|R)-`B=g%zkut#wrcOagXrz2z_z(Xx^?ha*!@Mf-4uWuWsEArCZNsvodRMp>b^OVW"
    "C`TB!!-iF&oYD`9ylh`W4y4#cCp-7X8}L8tdx#0Osh;Rnnf?IovWvCM8?LCNgoCu;Mb=P8fVZ1QTC*QX;x7V)FGI"
    "Suz_^ae-b=~vJzzL$)3q6@S{44$%miFul&)ZM07AbXw|%Rm)hFw-0_D0-zHpB+V+)j&+}=H&mLuqb&oc{6@<ad|e"
    "rn!FufPOipRS7#UJ$td~LP4VXJd~$kmehomU)1OZ+PfoALmseouyredwKcbyPy*|g{lSQ&9=it~bZtJ0SfRyV@X~"
    "FWeHdm1hVlHX0cPGT1)ag!p&@2f|NT0*6X;Y^SP$}MtFohIqCR@UstvZ=nC)sq6jG-z=K@sYeg2YiEGc7CRh(?Yj"
    "5H2A7kuixG3XC*ZgMEhtxDbM%!kY84z~r)IwiBu*XjKE2fs)cN{X)_P9%d+zq~m53>INPGGrFnOa+4#JXmC?JK}u"
    "IEQb0-EQ}wy2($US)vaDucxlNOq0+N1sJ6C?wS%-%|Y&3MkA~Q7h7AwJF4{nZ*2Y<dfVv(7$*Be?z)@2lV|Bh-~L"
    "b4dp%Qy!)r8(9jfS<UM(x!b@$kGUl^{!k?p0(z4Pd|Y|$`>I4RffkZsUMfTH%~+{=xBk`buuya1)Nb>R>XO$^ic<"
    "bI7w&1N&rXdz$LKa^hXp^$;gsd9e?EAIF2DfcNjHM#&uR%G09bN+uV)f+l^=_<dW#7>$b-y=pnaigzk`Bjb03nyE"
    "eO4Yj3`D9{lq7xNE1PU7~RO+F@5|MH>OPs|>TIK+{U|Z#?kEOB{RA7m*hY{JuXq)M4NCl3O);K?8c+$~s4O3G$sf"
    ")ywGZ91VmP9u5o05=04jT9`%50dW$j29akoBn1NdAgNb;TyefJ(YJZz%kvzyJs>KkashID;{rn3Q_xI727)dG!8a"
    "@)oaE(ZL0s@KWnikP$}UmBbseA$G^#}UY4*CRgqnE3l2Z}^v|2@J;$SYwK$5XPcv{hovlKE`C+oWkn0dvkfe;}n2"
    "nQg%x(4%{(0g+zc1fJ9QewLTC2V2vjBxZ)ljy0zvqq)&2`cKSau2m^1zaCL-fdi%J-`3{<qO1^HKnx9*SQzKux``"
    "*9w?vTnGKj`Yp4Q&MbJP`U=n|@MVZzf^giTIza6*(Lifc-qypUO47zZ0GrPHY_2szt^81IIo5h#!dgv~fa0(zql$"
    "}KC^XZ``3)McX^cS6LZ8^Dg#^}KoEPNBleMX4cQZ&x#9q@Wv#ub<m*eOlejf)x-^MOOz?WEfK&|w*lE^vtwZJk-Q"
    "QD4o?5&k+MEZoGx!dY<xfLUPn3cuq3IHs3nzUX+cP+pK4R_?C+03c{C=SRd)fznTY_M|AAi7xTtr1C=tcrE%pkfj"
    "!Mp;7~q{vE!iCw=Mus?MNh%xb%o?tmFZFD@S|GFxPObMC1q$c5S_>J!{Mw<)`TDUOMvG>B04K+6Q{yq`(AoXEu!>"
    "YUwWzQJ&B(_w+f#3gMQiuifZL-%C8gjEVP1+g-eX9|<>b<Jp^{Z9pz3Q958P9WYgeY{M)=b~{6<5`kdiE`Md#$p)"
    "|f^(_|oF$ah2+)!s%@d%If+84v{EK1j)PAsfD0DE0U^L`$P?tip<tKFssAdqK3i(rXaS`#IF&*k!RUiV8RXJId4$"
    "+l0RL-%w%wf4g83Z~k(<}!+2bd@Av@J4EXz2-W;ltE+B|)N$(y%*LxAAmLtBUBjsPd0iptj19saR<Ss-dtG0CaJH"
    "5OGZo<gHz(bzbhUQU{zUo8nI8YcM1-QU&-_?nx*Clzj9XlCXRxnmV}?s7%fvnbLGmz?I63hGJ<{s?VMmi}ac$FL9"
    "-AD)dt2YH^FA*61cVl$9z(|Hqm>3u{^eU7=m!0;_peeh!F!IX#nX4=iUTHWznCGw05m4c6JYLvOc59Q8M)w28tsc"
    "W~5PM<V{L%MXD0MdRq|K@4y-E<U6qWUb9?4sc&KX?{=X!xYL_=>m77FjJ+(^9AG^o7IXKi9^lG#!p005?t4p6xC3"
    "7<we42U0<gMkk=xOln$WR{rIR>CIaCX#qihx$3iCYM8jqbz}Bq`Dk&b(oDr+gH;a4*4)pVUrFpZZ7suZ%9<0%|U}"
    "@NU)>kYTdtj}4NOm5KK#egK6ZojJybx50Y=OQ)EDM75uhS*i58kODD0uJ)d&-R-Hl0l3jiwXtcCdGD4(_by=cvSC"
    "OnOuXaWIpyWevULpf&t!!uKQYJz!blVOqR^m$5{%bT9quXgBDiU#<^&AHw{JOBP8)hD`M+NVrMHnL+&F!CgYeEgV"
    "}xj@kXl^>c-qmn<F%onR;Lz=Y8uF$+jdLJ`ZN$)S#=@q&eeEsR{8*8UY?#tzML|5x5|BWM5lNCL3Tt#yH)y=#hcd"
    "w4DAx$;l~@K!KIAHIT#gC_MZ1AlWnlZGHB=*o5=A6IpRh%Q`QLHG#Z1Qg`$CEvGGr7_OJy-mOu`)*{+g?pm_G4|b"
    "PqgU*EZK&k;k04?b>jK~@8LdwDf{zXrw=Mh2tr7SVbO;kFESQ_Q*%p#wW2SjN)PDR}c7xF>ZlT_JatT#JEFY*7$Y"
    "Et$9L1!;4eUs~r-DML*^hpbreZ}vEed`wC_CF(2^@En=?gAY2uo5K94K4Eix1WNb){-i6H&K8RT4D)L4pC(K6EC@"
    "8jt&a>ehvrY7MtxofI2Ow^XRluAl<utv{SLXBF9ABQD`?KZNt)^j7NO-Q8}OA4EEb2<<P1^w27C;p|EN^T81jWVn"
    "o+1A!b8q3}mbS3AN4PZZ4+qK2eYtRRLo`k0&P#;6}6wxV1fCf3<{y5!yKl{Rz&PmyJR_;5MHr!ZG3EpntC7FC~BZ"
    "82K_UR0+$;ROa~qb`?gZHV^}2*Cl|f^F`Zvrn0H9v5ehHNL=ks!$1kR&J_i=CKr#wLpV<hNza8*oh1fVR(fwf|Kd"
    "Ob;j6Q)kXsr2DM47(fK+^&d5*}V{s08J%<8Uip(ssRHv4OI0a`bR1MK(S*<?9pz0Cf;$iT-d%*8*?{<5(62EOdVd"
    "-QQzj4=~v*<Ymb>SQNxEK8ek0!ds;t6XXjba;(7CbKbSHExGKAH4n0!Fbt^P&IZW7HM%1qv5X4y;9`N=@|=%>X%>"
    "?U=*ru3S%~lJ!GyXh_Pd*;r;&%%NlUQK-IWY*!N~sR^7jQkF`~{7uXODRf1iQsPF7V<bgD;0|wX*(On5Fe^Sf>a?"
    "BpS6G3yC2+<e4XDI0M=Ed(@8DM2W;s+xfdBfL5_Sa-@C}lCf)OS2vH%!cO7Nj~gxjGQUP?Z5RF%n<wIovaHrm-j^"
    "~>cFOI$Xp8ZZ~PWS$(u%)A)H?vLp%hW|b=>mpZkOmxKAzt&X5^E*6n%z=vUk6#1ExcC)IfXs;lF+8IU0jDW5e)4z"
    "ib0m>j<I`&-CZ-J$g<`MxrkQfgr^EAPhHK9Zd<;Z}5eA(I<(O~skXb&`tec>z_`5anC-1?3Q(KLt?%UtQ(`y>?ly"
    "#iU8mL#`IEJXK(gvhsFM0M%JVc}rP!4me-|ZB(Z;_#|1#8Cw2?Xq3h$Lzk8I(fCvlEKyp>QFngCzl_tb_fe&SExN"
    "%uH`b+Fs=2e-wDJI@14cHz<3WR=0il;^Q6&s$JgP08oMFnc)>!P1128FOXht-jE8AvN!eg^%+qn0<lqci+q{CVZ!"
    "obvy=nA*&Zb0Bgf)zi`lwsn)L*e_^=I)u|fbV-1SDYnYh#rc8o+9EeYTT-wqM5(qO*^9iWLS4&U_R__!w#vr%<(^"
    "xq-F`lSE=9QXe`>3{tF|E6Qjt&A6s%kA~ba77BZN_H1=c2hW3hSY?FxiewSFW=+J{3I5YK|mWLr0HgIzX)&t&?W8"
    "nEHPpaU~??wVxU)u@uqxmN&G*C3ezLJI9wC4)!_kBg5JQ;|F>RjE^)Y19UC;H)~6&+*YfQ?Jl=;Q^$pB$wYpLQJ="
    "a-L9gzp!;s4yl>0p5eZ%5Yi<)(l~M8d2mKqa0vK%kmv>GfPwqO*zDLwGKdrEh}bBm+BUMUMtX^ss`D@F`JYnLdnh"
    "+GL<&6N5TBYA^CUU8MqT%#nkgV<y^w9&^d|=Ohm|RVuhU&DLIS3kn)6vI^@R&+%x1rLzS*N}9}6T8VW#uhc@jvXZ"
    "o*LRi4UK1eRpt!6x$m5YpXkW6s%-Q{a4#EisHBAeD3Mz5QaD{FHqM7p4?3r(w|%hgoGAFaVQ#Ag!^bUlg}9h9BPr"
    "pk?ggfnXR{5cLPyxj1`i|@bt{`sdD&hB<9Hr*WkW2=hqoD1wimr^-9zOLg1E@Mf^t<@(tRi0<F!8)xB9(q&d$SP+"
    "$RPX`_@5qlGd4J!Uce|u(<59UxAQ&zbiEAvvNnwpewpr2NciHV7f17@8tDM(Lo2;J>ITa1&uKIqxpo62Ny$E8+Ek"
    "@%oK;*Ep3je{}^BXkHx^^4^7OMi^4yywNxql7+4h7}+{jOnXEx%)Er0vILmENu#%7^ab+52>*X_OGo@B&iE8J&@A"
    "3WlV4FK>;W-ZC_VFJAt)!SUdD@Pa-Lhc6zr5+HG`QC=5o;de$Ucoi-PS;sxQfG9^XsRo!_F{r4r#?8@lq(0_LdB6"
    "TIRqnduN5jZ47-Tip30A_G)eRPzRbJsZ{1I9Cg0gt6oP5B?=U<)tiyd-*#L|U?hsG4O!)RX}FVe71caR$IDxCkUd"
    "b7etDhQxhJ=(7-LaSDIJZ~uGcl=d_XZg*)sqpNcScPf!n~KohsdNFpAk_O$NuBRsYwbB*6J#zci|1&>9z}HhiCd4"
    ")YWBm;(Fvvb{RdaaLLAA>(T}LRBwzIXPH~^Tm2umPG&sU0`F(P8^c*~i&#lV2ai3b+q$5kG=OH!x*fBR0z2J!dZ6"
    "WRl#=A$c^^=#LDsK{>5-|R}JU(uvhm6&>1^J7mitL8Ms<80BURhbWWmYbB2l*@E{zL4Q(K^9Ahr)~kkV14(1wG`_"
    "z&%}-6doyIMfwfT2kUF9SNcs=0rb=M*9G9qkOS>S^s0EfAC5n^Rsjfa+E~oMk0m&D2D{X*E-tx@$U+=PNjQiJW~W"
    "ATtTeMrXv;NQY3zlM^)U6R%Y6Jbt4AJvc=4DT($qVrv@-<1zP6b3<5qQ6h)zO;vP)vJ2s`Jq#$tqRUu})(QyF85F"
    "h_FHg@my9J=zreiYR{g_z1>YZi@GaYzh56mCJbC8%PNd_Q#fG-bY_ZT2+X>Xj`0IhMO1)_S8#mp_5pQxZ(sAb!@5"
    "N0bv-v&MF*vu=b*fU|3Q$+RmW@jNQ1mNLU#3i0?g43_8P|c<sMyy&h~~2U}lTL}USzol_Zl<2=Z#4gCn&ppg}rHz"
    "K-hsKDY+qNpA}Zq2#Il~rN7_1NGi{A)x#mh%7$Qh&w5XR`_E=+Tsx{YeUQ8>6#TC|gDdAKl|VhHSkZ=IifSYI-mE"
    "o7(YTXHYww{{~&pajPAC0TUyziL<RT?gFUqk^_YDDE0<yT(*!`9Jkh>DZ+@<kP_TfoDxeOD~cH`RPoi3nFHDI__H"
    "cDEBWcFsm8@-wXX``H^pMEPJbT1Ihp)2zT~v-7q%br3L_!p=KU2R72!0(Z0re_y^@fD+XMUQ7gQee3UUlPJOJ`=$"
    "@fE<As<AEKRLZV`(=zj(Vz0eFXPLzpZ<P!{#X1>e=_%-j^AE$qw+z1{PFe0>EHM_{#$<f>E!G+|3ZJt52q*Rr(^j"
    "^KDe&lt8yEC!B>|jKV9Q}_?NT@^+f)TU*li8=T}!}e?6C;^9Oy;yYq8-Xa3tX_siM%J+}vcK58gVe?B??>-cJNIs"
    "UhI<14u;`1V^z&J50p4t++)==5@YqMuHGKjNKFFW$U;J=XWhr-PH(@)}mafDXH8SI>Er&&?2@zCJm7BfX%%<)>E{"
    "=d^s`5B=r%gf50Z+$Ud_d1Qy2ou8h)J$X%3wN+NkvvsPgZNE9Wx*lKRZ>tpQ*~kwUZ^xG>*BA7Y!~^8VtG6eYmol"
    "#P8nU&(2W#!FGj8;gs<LH9%?4Y#V+ocZo<b?bOG#MG7YOzMEno}9UI~JCS8gHHfH+H`u)*ZCdV^~DRFghnVhvnIB"
    "KzdWi+9(_&F1Cti|_HbtG~VLNlp$YOr15z!2n1DlYJuvgzZ$GnF28k&RPss0LqZwn=2cDFt@V0On6mQ5atI%p{yl"
    "UmpZP$BLE}~z^!U($p->07)Ag&b|@nU1SzE;AXW*J+3r-DH+MS#?JqX-hKb-f(={ieDsYpj)w+qN1376wP1fYf`V"
    "8DLm0BSCvi&{3MHo~z{hQEiSSdn$D>Y?HeU3D53sp@bxkxdFWcT<=8wJwiV)?$T?)R;_4b<U;{I0UPA0n$2tN>C3"
    "1kl-F(GI|$r=MWn`5Mlckp(Cg1o*ntyqN&y{uCgswML*KsPyXMJz0~4<}}M)FL0if^RnUW!d%^EO}2vl0e52zj8`"
    "%fRMky(OG}Tl{221Flg=8_Wbomx%1=b60(2jc`@yZ%CD^2QimS9B1&XFjM-sGbw!utWjtg=^Ilz231@g+JIf8d_G"
    "a23h+;Gr!HP6#Z^BPcjW~NPYR}1EHCaPGL)m(Wgn~?g(EiDc&Vcx**5~}Cr+Frl0*^5NogygrF+?FP7&8%f>`9yv"
    "!3pD`@wDnv9`6x93@WT)Vy0a@pO?ceGzuZ6x?bv#EUS7!IoP9mdYWFM6los29=%H2hq$%w|^@PHq?w(-vwL`u2M+"
    "VZ7vISt&!>$Hn4*R-Zr*kzCc$x?(@T!+pTJ0tj>bA16EoynZ6zIi2sWuhm;0x5{)*HM?dSz9v*3G0+OY2M1dAB_p"
    "W=~0a+>o=ba=6c`aEG{3^K6}YWdJOp&yt{A?3|m{`A*hIY$x%n*cz0k2FX?vJONs7rfbyaH57T>Lzgd<8t*{X|7n"
    "=4C?$4Tsrrs3EZ&q-i>N`AMbasl5{0VYEMUDDKg1JE%SF6I)!!7<3rV2s4osx5`yA?SO>zY|uTGZ)s^rz^WauZHY"
    "=E{ku>!(*P8}k3f;B7nzFa}lR=!L6eX8+OCqMPyecylav^M-9)D>1TniMm&f$l*Lfl3u>i^o87a|F>%&_ZUrWR>1"
    "?PL8xiErG`X8=zG5byb#2N{yz|ji|(ER0)-l3v<F!6>|s!;oFe`7?~j;3EWMP2FAjbJxY+QK`5m8!DVeQmF|{esl"
    "Ui>Ro!^U0y;}3vz;d`7v{^@%Qym+RB_^R(P+B^?=)ueiGA7&r<%h&6s+xvk}?DG_i9u0cri64Q-C&<&siJI#T<~+"
    "UNXg2;BO)ib4F~6sx+o0WCe5O->IER+;PtrJgAW!v8RcQK)K}y_8?V&SfAiqt#b^L_q0T{621aGN7y)$Yyk`H-(e"
    "qtS0-0XNeWxW=no8BY5+ovYn7KGI$&VjD0SeV`p~vyw1yzarPV4e7Qq38m6;%(H#AZ3v}!VdYlFCts0scejIWf4Y"
    "U83gc^<=G>dhR=Q4Jxt1QOUVO3e+<5I(i=fu=swl}^LA0!Apy?JeXyRP4e@2qE`uTBugIZrYdqd!%A0EFE=`Ee63"
    "#ZIJn}k+d2(OW`ABGR&;?&x?%`3ed@i8Z`ETfEOs$)Ua)J8TDQ{0}PBB(her4z&>P>Jn5Es39>15M)^0aOV93#=@"
    "`D^BwtOK{YEPwEYiHIHhu-^tY{v)Hmdj%20bJ8y;I%?H!eXcC%~k0TUPCoS1!~AuUoDYc@pkIvlxG|tors92{3;h"
    "g#$L)a*2UL+MQ30vBC}sz4T6!8Ki><-wslpB<l>!r%UxIQ(Kg?wGbCMK89=&HJhxW_Z2n4E)~)*W<)MZwi(_<e20"
    "+wE3b6L{vB>W2$J}9wC!gYY>`MZa-XQbE0w6U$}=E56CsYf4f2`m3_j9vrPg^m2lMh<t-3(dZaeQ==iU~b;V<d!Z"
    "KZBKImep>y+I^YA8D=OFzq?t!M0y0&>Jux1a=iHCXQ45J5Yupi4ULuR~PT~%KA|beVlrIa$@T0LVGsI=O*9MK}+f"
    "5#L<*M!AGqM0ptW3YSQ}N_}F-|E5nXc1M=7MmT5W~ob%M)-z;xS6seTmdU)!CS&ps+=~v8pU8@Spd{{q*Q*CdyuU"
    "R}1OFB3iA8Q`Vu8ysd=u2yQF-Kk9-(h`Et2+&=bRN{LJ%y+)H`P4iBJ^zB8jLKr#G5D~kyC*&QsG!G)MB$%8eScE"
    "87|Qyc37#v^`KeNfEs*|oGd<NHL@k6m}Xx?3O)g&L<`{#dpTKq*56jDZp!)n1pJLPsnHxSxf&#|R0Gs%1tf&c*^5"
    "sE`OMJI8nU>vWuw7S!+G_hfM`l3<OT;J5ZzC%hl7r9$waz2`tKb%%@+ST%ggz_TKp$PSGy)DDgJ7$#vSkOiRiwyO"
    "BMCg<EWza_<rTxVv&69eMrpQrm4Q&<h8n}vfFHrZg5Sk$(uQZg%>^IoMrbiB*21<hEPla^(f1V8YN=}O%;%{e=!q"
    "B9=_z|@ykE<kN?zv`R6_i`=9%3xUHYn{aOLrXruaYcfa1ORfVg!m)w;(=0yu^Af45CD1fp8X@|%QLGrGrYy9RV5I"
    "Un%nfll-@r9`(7JD1cFRsbN67E=V_4fOGN4|ri55NPd->=W24=#cjhnPy_<29UuwZf8HJ#tLbCIB%*3?f+#pb=n1"
    "*@BlnP3C33Srz8E>T%6+bdoPsg|Dke70V6)pP?p3-KTEgTTcQRcTnGm?S*Z6uO@O%?7I+Wb)r5UXz#EqK^4s<`U+"
    "wTwO0RV-M0HAyarYKNr~-!YJ+2x)oofZTG!2>wSGvdvTTryWtrXflB<7v4fJQk(MLPx7Mdlds&!Q|uXz2Nq|erOn"
    "<mTkM+>eoFY{cUl+H8)13+O|7V1%$52ziIXEXWrtx48x$9(vyv?#uGMlYU|^i_{aRxoCx<!(M)r1$XYlG!q<O+jM"
    "!x2d~8iCuE>B_k1At|dZxnI~k!p$*Y`gXp?E&ZsF&c&)bGq^)qiiz#wau0(~SM<?KfE&7(0*wZQPbVS8Mqimv|Gl"
    "8>qwQhRu?`1VXuPm#j=x&w5l4?6)p*$f*TU~&&Qg~tHCix}y+-}PoSbK<Hg16E{yY1wQ3J;^h)it2+kbHlj$_7HR"
    "ypc0Ha8JH~DdE4hv<<$%Py&A|o>czG!3O@sVQ2S~eYbVW^Ed3F(x1T2kPl@p_t8nsA0&(?AKd^oe``A%_Dm2n7<n"
    "sf@d;z>rSm%SZCy$StpjS6?k3<M)>STN*<u3m*h$Ln^qvzNo#-grzRt0$NY5j%TFaL$_f#rRcV_3!%FmF-ir-G~<"
    "74iFfR(uoKDFGXgKFLgzQ4Hq+tu5X)A8i(#p|=vv+-5WGNsdMcU7e8`mU6DUu4VWM9Memk)oKCeg=OJS-_KjFZBw"
    "lxhea8r;LJq><uHys}we;^AOI8SQ;p$;FKk1LY5_rS6$|xRL4)0qhn!$<*P>4ZO@VTo=0!cl&jp%mSGmhWTeG?$G"
    "vr+@4Y#~FPuYuF$**H_y7wk`B9<P0q7!RpCOkq{)OD-`k?Fh@6&w<5Vrm$11hT3@lddcJpS?!rH2G^af)+^BnFQ{"
    "GPP%Inh3%elw44&;1ZVLJ%@_#iD5uN-J3jO=yS8FQJ`!Jc}lF7sJfTk7BSU`>&F>$CbCbHw`Z@0@E?LkVc9dNO=C"
    "RR)D)q>Fza?#H)_RBA+ZgZ3a#Ei9UNko&8Y^FL(urda&q(WLqSlmrU5!KqwXSK8`K(uB=agQ7JcAghmrFK3m|O^v"
    "0dJty`nc5Bv(pFsBy3c!YQezCZ%%*As3)?peCc}Ics<!|4-bWKtWV4Y(l-P>C6Ed?d{0OHYP+v*$h_qi>&Ib(+ct"
    "X!~}~=aZ=vf93;Z7Eb3dQb#GcXn2XGDF1wIU2*7=RRUh^=NqWGqXi+-_OcQN4l@)-F=Xs5H+hYVQ2xWCU*i#f<(i"
    "*hvfa^(g3_by7z3#;FVYt=xrja7|n86}aN&X^WG$iwN;Lp*`5#=uWT#dFC+o865zIcQsm8CiGOTeR$9i=1&6f9|5"
    "Hr<Diu(qsj?QCW2mXHP8UQk?|s7blm!E%x0Dp^uF3e#uZJ(Bx!bM&r2HZC5UXa?lX(Fsii!|Juf%oa@C2H2mv?Pi"
    ")q@Yb|k@D7;<AyVRM0=QqoR>SeM-v5J)%}1A&83Htu)`9N1LARa-s@gXdrby+;>O;rA+3BpOpP35>Fn~SUqHey4t"
    "(SG=59{}oi;LTj=Qs1O(n?=4N{p&!CHYXIK#*|l<^{moei7t8%WfMcA0QX0eUJG?W0(HE{uoc2c0{YM8}zvMzL;U"
    "%XRn-*YyK%xqa_PDAl0@8QP0w(QmA%DH_aEmnz_hLX8}siQ+qVj(+uAeU8cP@9}aG;l&UIQ#0uyx67!{<Ucumzdv"
    "?`oACzqU82F2=-weLY`Z5A#wuu$kL>%tjD%kM;Es7&6+jF6oS)pIw*{Fg)A88Q1r_wG)WM6miY=;D8FH;VNY=r;y"
    "esRWa<b3k$sMDB?_}_q>-NSf~=%1h%J3PiVu?LdD<6Y?@zeo77o!VcscgM-xzj4PJJ*g*ifEz*n{-%8^yVU4m1AY"
    "-c<!RfQ=h=t6=Z7)oR?i@+oUB^W3V2nynnCs{)x73jEHS1nJZjlTPKZM*A3_5y>z!B{<ZVqK!;1$L$R7D_kdE_v&"
    "vEYzC`GIrlmJOT1^3(YB}3<?3bzmSghd;~3d*8gvdzn)AUE<5`4)qh)U#tXp;7EMd6dRW_q@r9wD3sWdka6!gaQ;"
    "C9ASW?iz~B5r|0&H(&lpw^r;!Osf6nx5Cs9x<m5Fb!SyfRj?b-ebBMw*XA>)sBBwpIM%@MP%#=$Gt{|vLwl){OmZ"
    "}$57w>IqkhB1@88FY0ZeP36NDxsGbVgNhge)s+g$^yK#ATX-6tC%GHpo^$j|F?MJ54OHlyrXTzxy*ld6Q-Kx$7V)"
    "pp=VEH3ViTSn0@&g~>tX3TmOT4URnP{l2LPNG5x(mRQC*y;t@bO5rGmm+W8-q?j;|BT|&6k`~TFf-%!%rkbr%g}s"
    "cS2lc?6!4B4e>I(Bew3Vzkvpkz8+X^IPg=MzkRcu}weg$iEI0+eNj7FTLB6}c!q>d=#EIu^Ogy(b<4hrJ4AR@^<7"
    "H&SC1!&qLrnBU44MRFBn>!7LrOYm<*-2^1*(}S!O-k+(`qddBF4c_K2MGI0uoHRjkmfe6pzxI4Axyt<XnRaf3=`q"
    "gn<O1sh$aTc?wPFVa_y>m4>SBfNwC-D7Sevb+^lwGrUn{0UzstoaAf}U^$d`TBm8eK<fibY-6-~DP&9@UenuZ|j@"
    "0KhLXG9UxkBiDw$?zKkg>r|3>qP868N46q%s5-OQO)|=177U<V7J4#T1>-5YJ{*7y{`uS`X_u`6`;7XEdtHKo=zC"
    "OyU#+Og{c*mCKUJ<oolL)|;cV^Q-aYb#if;T#nzqJ~<sHXXn=!ut@5TrDkE=h+yvB<d>7z@5Wb2=P$hk{?`rOvQw"
    "8^RMOyIy9M}c6gI3K-s!e<zD;3+He$*eJ@diw5C3|YhTYoBA@VCScESQ+(3-e8Vt*>iwHe7Iv?wx430&HZG1R2r="
    "hPR#YG9se3QhJf>x7RqPCTJ@5kXPe3?NSk9?1OFgeCzn6J19I@H))ZsVbyv+1@F~S>2*Q1jjWuQJX~8DgHRM8$(D"
    "6XB2Y%OUk%Bc{6s;kThAUEiHK}nu9OmmidH^$GaDhnCxHc&U(j1Znw&--M~wFj4J6_`>h*g#=kkTHpEk!*Qae;1G"
    "k5kt!wZU0+p4$Va)ReSzUt0l{W4!Y4MUlNH;L$>vG$!?EaTgX-{!5k`%$YSk8&m9*pwb=88Coz}GZnjf9mRPxq9S"
    "yHGjekGTLRDa%lG)HO4vJyC0VR#8-2i5avg#h_gIjU|*JnOk8Pt~S}Tw3)17A3W--+%?{ZMyH9s7f7R8v3g2sEd{"
    "osp&MUcX*cj8AZ*!H-ie3$2pN5CHd?sJBipJ~5z*^8@_pn8wik8mj>CFN>jEA{zir>yG%CKsA!>rhg}?-Ba>#({3"
    "f+!{3-=8D9rSgEBBb5(b3!wb3xo7wU%6(Yv<3k~f3X9?UKSlXmA7|0t`H6M$b9AoRd_&v`d$bSf%^NN27wIFdi}4"
    "UF5&n`lqLKflYRLs{P1vaRq4s*6=mTs53Cz|v-7mL%lJ1CBF>VxBnDh`aBsO&aCm=_LLc!cJ#L$YaVmu9dU+BQoY"
    "KCIy$&1d(4%*uwV2M%PhY=#1?)0n@Y6=BRG(5>`+Z$$kjfMyZLzALiV7x|*jg!RqlL~m!rRJCWAs7iK($PCbC%g<"
    "60@4j@>GoS{mz@nscO$X7P>-pTUU0zITGT0GdhxDMZ_C`DUvKK$1SzYDhPfix0|#|iw2|_Ps7u|b0RS5TWB(C5G`"
    "R^`i-O@uOioZV3yWi_W@s~9SHO$jtc>XQyq3qWJ|sh+XCWL*j+Bw#@B|kLHPu@_zDu}TEp3TtJIjehkB2I4LG*V9"
    "v)2A`o_5S+iZSsl2vSvC8`yBBir*$RT1Z+MHzY6qB*)6zaF1nOUC(6mltpF@JZhPJiZ(!SRnc@AnD~y>2?Q8)y(h"
    "8LUp<yVsAlB`G$=}{o4JYPl=C?agAJPAen^yjNOX39Ry?aLxir(y2oxXtMR?S93IdjP;4Ai5);cKra5fx&}F<WK`"
    "y0sJBxBN1C>69`RRZ$j}=#Zfxvr{ozK9M3ke@~L$#Wh=*<P<#RYkP0fJs`a`sAsSexI`j$Edd5LuBxuv)@|%C5m%"
    ">732E7$*EIgVDlgfp^?<e?9>OnrkD=ViIawSHq#uyQTL86GB%!eC1|b0`&nbc6cOr;Xx$kOq}zONf_Tg7f=Zuy$V"
    "u|7EdTlbJ1z3cj<z2mg>afp^e+&bL0d==$%?nDHIN!CnrQ}v2O<AZ625xnvD1hYM={O5~FOdmW$t~TsRRu$ULF?s"
    "Xb!bq%tlt9=OW(N|`ooShF7TgSyu0kezAkmL|+HvKe>UoyKW>8#;|i*&DHBYAGz<VtE;29=tzh&e=3QrYGAv(h+p"
    "BdMNb)QyBi&^tL{}^VnmvBB<lyD>D`TTDl*91FOcKblh#ty5QFuL{?KVH?r522o7iBdYJ`EqwjM9{P=BXCLPlI+c"
    "o}!7SxmETBnqw-cF%X6FSuaQjUz)cPW>Q)#|j}ny;qAiECDiu1tlII7q%XjE{pBv(D1m_ZoGM*r7Kz=9XvJ*^4Er"
    "=zg2I7oSzfiL)%LJ*Kdgw!(hTsP$%2Qxhw$0LK9<sV0xJEju+Z0xGjo7PG-4HaP2+t&VUftFjlQPxib#$?%lEIWp"
    "3ebXUg(&q^#kjuqKZ)IrP6mbVmKw^SCU#>T3q@Z_5GO6yBIn>aY%s&d;xA#V*BUuAt0Ud~4$T}dCpi=6T1Yn|`HT"
    "l_iUyZo=i8{Mhn+uSe1o2;`@@+b$e9!=PS+A-I8wD(=dm$FT>2Dg*FD)hbr3t&<s2ZAdli(Rm#-j;cu%&JT+^PN_"
    "zwpoDy4Xw_D0bn*8q&}pDTju^X*6-sCS4$8wEV@t)>aS<dFNPA#x}&<OO_izIK3+dDF+f=@vLdZ^$vl-UoF=!b*k"
    "px5xW{IGk6l$&(n*tfmDYF3DqHle#x&Fgsr3HLh761|T)fSS1;p&}35fMTqzPxD6za2Onczs1*oGVnaOKde-EI`J"
    ">Vg`sDz(S$55qgb;sl_Tc3vI_RPtXZha6e7T@12Ca&ncpa;6-JOj?%%XG@S+iL3H#`q_J-PPU8W|GGFk_axD}Y-!"
    "`-93JWKr)0!EB?-1&4E*&P6=y8c+$(!Qq%SJqTp`y|9?C8s3XV&^LeZekm0EX>2gfhNvya4M5KuG*bbDOUj^ssmZ"
    "uq;CUEcx&{*5D-p3c?t9bCUjP_t588$k_qF8YTLAA1<e{McShlFI)E?qVy~)@dQCRm{_(EP$fYf)dzHQW76M)Guo"
    "Gcz)M)B;X~pS57;mWLb}AsotG}Zo>Z71rmQ_cozN6_BgEbbk_sufdkjlb>p{aTW8EMoJ{?7V_^)$r%Z}0<maVWpx"
    "h8`BG!QN#(?dvw&8mgaxW_oqsIwu^}xI?jOjEf3&C|w%{<~O-e#XvVVJ-84NJjBfX{%G?E*6Did(G53Uw<w5MX5("
    "UcV1NiyW~QO;N&}fFyQCT+n|^J>^W)vuA`?gup{pAyN6@*)y~SKw6onh>!AVZB_*gq?0U&j-%(=v1g2j+6P|JXFk"
    "9zM>dKH%<`S+rGa}q0BC{;E6T0F=Dr%JiK7UVfuB?&cpje4YdevW9tV^>K&k_MXR7YC0#cM|?0A?y#iNx>UpwrsV"
    "<bV>kg12l{j|jCWjnys`6*i<6H7Gup5|Q#t=Y4qsy&+qbV|uJ|JYdR^i0uNB-;v#bb8~9HIJA0_ESHwHXS4<g*{B"
    "HpqLWDj4n;mVu$7*0wuxwieoOo&5jVyJ+(ofL{OT@;;a-g;;V&5GYkQDF~4(>s!d7$M{CSwkn<hGC<$N1cv<d6mz"
    "5oV*;@!(A6N_0OHcUd1rJ+2I!3?D=osZ&3Wg9@67W~Kw`PK~9|gwr-TB$Sy&J<svMX{9Ze(lEvp>1dWW(rc#wLcz"
    "G_D&@nar{%{Z%d+E$5n(FLXgex=5z3{vryoEn*p10#nUCc>sTqYXLijq_SnTzDr^AtW~v23v{UV1gY%g(Uq$d%Hm"
    "+bQM6*k)6W`nx#abbXcm)t1985c4<m->(pVWmW~;xnHX=vgYy)oTWmzc)hC?ZHhIEM)XS19s`K+SQU)oSGi4HAKV"
    "_5W(PgyFmZ@q)?-E@Mf*&wfZMbuN2{23AGr%91kRk?LCYc>UN=`L86hozb!#Q5y|>g?4x_HqKagU&V1c<J~dkJGx"
    "!AR2;;tV3l6*t3_;O1+((SZ=*5=66+Dl$#nhUmZh)L+&3q>$g=|++skOsHK2fGF>XW?k@0Ge^SY&kkE^Bko}Z>rY"
    "v|xsRJ+repvMR)QR%LXYCn+?dpg`3hzb|8lGG7^|>E7?<EZpaN7z)OAy`OEs_S%+^MXBLE_5kx(=KNK!=?DJWrat"
    "N~vU>Z)z>O`dYS;qprs!l5&Q+FX?7Glm(ufwv&t@V6o%WvhEI#571NADu?<k;5Xb9OeqI5O`tk!;aK20Re;drn$Z"
    "Azg}@n{`zhriZ~_AFF~Q(DNrFLUfCa-VaZyfj0o<t^S^_j%$@0e94_Qs;O;#tHqA54?J4IBSgbI+v23|K@zy)h?A"
    "R^95jF4#lB3t~R)icy^mk^Brjt2q@gCdDE7xq%OmC7FJnW$Ix64q(eBDpv}9rtA8<3z7j8!FL0B1zIk787rF(wgi"
    "nmdd#eSlKAC1*DWJ8mP2F2f#lzX`U^2EE-AAwde%Y;C7JQ95FW>6!_thMXfifR9RvAYL`wx23PPR3KChI#12>k7I"
    "Uf#A~A%F#N!k&U=UOd)UzKnsD)^E9hCwufC;z*N>nLhv`X)7e~$KX6X`B+>(bma8|$h>w{?bPy&F~45P_VcT{N{V"
    "1|aqV<CIsN{Wd^)iMVZSmlLBJ#rkfTG1P0f8boLmC5wr!9>5@tsd6kJDAfw2vGaxjJ;{^<!qcH^=s0gx=AUR_^+_"
    "Qrq@Fz)W#sZK5=He0kr6pet$`;Y^j@EL*c%?4n<J#9R8_;+7y$V{t!=t_D%Rdq*=KEUs=7&Mc~-;j7Z;({eK$p)2"
    "sgz|hjmsKcIE6!le_Shc=VQ~v%^ozf<mmo6jf8b3E))KZ<f})<%TWFWV<5;wF}lNnV}}lsAwncH(a<t$H;wXoN%A"
    "<fyS&DVADg&QzjxNE!n-u+77Tg*iTCNSM-)R$?x8RQ||m4vd>VsfEl4d|H!A)b^JjTV!}ONYoT0l{ZCbq_CV(=pX"
    "xGyAhGS!2S(}#;;w<Npuo>^nriR|JgvRlF0y1G)((5pGzFWHZ90{qCt*p9;CD!ksTWm4*%rAjD^{g*W!v@D3M3R1"
    "IPGDbQT9tKdLjrw-1holFcmc+C}U|Ng=L_1d)yt77Mzd=rAF~+oGHxZHBWPr`@l1soCs-<hjsxS_>(3U(ynSAD@&"
    "6`AtpZePMgI-lE-(|SlzLFHvPV(UEqedPp4(}xyOz5bxjtVqR18n1oSa`5o(FSj|-Oh-~pm~E|`sfTkLUoyMAAj%"
    "dt>%2PIda-&=zQY+Ip7MhOt=IAPrY92z46b>l*I^`W+_zbW*J73oDcu^r5mkO`D9`sXND&l9Md=AB$W;80JYL+mE"
    "unK`|9^XBZD^n+MaIyJPQdU>waLwvMwV5ik82SzONt5xyF(qczG$Vx49%p=8x!f>@gs{`E~Rnon7!+kjldjcG7$w"
    ";p7kA)!UP6l0gkpthC-V^V6PnXJROJWKVnfBo|w5sPsWxl361t2`ylba$%tr_(<)=nwVN<nFeOhL8;)*(C@Z;mvH"
    "Qd4#C1`<IxN1G!1$41327{*`Mb4a<{*{a^+;9rYKV_%c<axm@XVCu`h^p`y;Fm8mT?cQ(9<lUbogM4L=DvtgQxc_"
    "fMm*|L43%n!}M+eN^ezKtbgh5u&(($9WZpSb2uc@670x)!fs{8KscQ&Pqc)R@(4HzWBFpv%VZ{JRwyp??ydk6_1("
    "G|b-;c?52*Qs~#QxfNId=j*#rG~JZc6sgta$1l)hcaBlELUv!seMZ9KPcKKOb_XvNqyWpwO)4r8acR#9<yRt!?RD"
    "ZmMae&Zcmc8h981iA;=|h@)MMZ_Wc6nrM*M#E%4MnLEQ(v<I6H%U|D2zjr9`Dm_Y6jbh}&Wq3D<*=z8W5h7t*GXH"
    "QT{dj-*($LKoCq2d4u#Utvx4isjqy8|z4BmxCQsG^H@h+bpK_0~(jBCpcT{c<DVq{6#|w8q-@1Kbq<ZJfBg_R5h3"
    ">kdB$S~_gpl0qXMURnluSvT6wl$;i@+gzqrUMJcM<GapS5C3ue*R%8F?9H3;tFx2qaTpeU!V3n%7vQ|EGa!v6Gs?"
    "9tp4Q1`4Xg@9lTbi(wrPA~TYjUtxMS}@!%Jz5$eAaVhsjgm7c+8KKGF1x124@1P+?X*^Y|_l#Fli(2t$aPHox|kY"
    "a+bRP?$5T=h-^X3e_DX5qufcLq^j&qyn}=a!@GL%*GBRh!712<A<*S?#0IKR^~e`FdK!cRD+`po@M+TZJly}Ahx@"
    "qXL%ISooKIkawJAx4nm|kQs@x5%|b7G^S-6)<j9=<EH`;Ruswen6{`~6tOXqCX(28GR5#KB1AR<_ixWl0x#n&8#e"
    "eqist0%w6%cGmP~o81Y?nx~p|Cht+3j6}CrV3#$k-~&5)mL!WE|fYX{kA3swJg`{bIJ=>q!!UXxOW#r8PuAE|{#A"
    "9Zgaj4NQGbiGuk{W>71wd2GH6ffM`vlGwYErugm2_0KK0Ut&}p370ggG5#p2T{!a9VjT(JmsBIGY7#*48|F*Sid!"
    "4j+l}4qm>-?k@no*>TlPV~-LAdbBNq@~n0pSo`8{x?#QGLJLis$j2cj3dyC+t$l{&sDoEIam-k@Ahd;UYK*@o>oE"
    "k!e!q~3y^bArz3L;0=d@<^)dljMYIhb$;7t0%6?lk>k{{|q_Riq^6TEQ<TAPgnNs#?oSk&a=LRC+ob_C!=3Wonn`"
    "}Rh||1OtWgYg#~)iwZ;hptWJ=pb&gPsw1zD86hqPqB__~hiEMJjH0vpx^tz(P!Iwtl^(N{FphDpIHuF_CUTO)PWb"
    "}ePCtj&bL+Fz57!W1lNpIl;Ii3j98pAp2gxQjyfXu>4Rkxl*MT^A0=*&Puwcyg6x($VG+p5P*N!ifsdZ7L~y!*)Z"
    "5A~NREGnX3i(VLO7})Ed&#o{)Z>60a5mv;}!BS9_c6^SwrW{94UY-5))A(|Her;!J$<*6zAyAU$k`xJ4<oQ)Cm0k"
    "LZV-Kl5Q1lKJKW7fMrGen_>QQyiiR1Ct{ak%gIk@%mO`UxLlI`1cZ8tUr<jQj<wSTTTy#ClP3)Poa)~f0=f%9UT5"
    "NgK3Mm)ii>d1tJ;W~~9Fe)SC@(EbIeW>$A`*$TN4t5nER;FQtnUxN47&F9u^s_B=qB2s&Aq)$47!}_hIPbWx<j@o"
    "#Fp9!V7(BE}O>hnP%;6M6Jc4a(;Hq>2o5VlKl}Z7a+OIa47U38kng<PbFw~^eS_)mPDH9K@E);aMy3%=7)`T3&vn"
    "A$=bSbG7Bu9<3_tvt7J>eu!a|h_XGJ6!Q5d)Xoo&hy!fXqvPJ0@0vqH7~8d@ui#<QJCRi&inePZ0X8arxJ87KVO%"
    "Fs*hIwp3(+2$0WYQve9>wt(se37;h(#r^i060mqn=mT2zj3k-{Wp<`L!9Spj0ZIWORMa-CnEejH22g*6!#9Wva(i"
    "nV5g=`rxLRP*g|B>i@#gL8F>nhYrY<l&BvMcE9`T$o6fli`Q$#htp}O=5X2wg(KVm&lN8U*KH#ux5Q6|mvo(rmxl"
    "PN_gh`E-u>w;~}^8Q{atS+ayQ{_M%L?Q~faswrRgBW4?q*zMG0mFxlA1NJSmLNatOG_tyS3L|`eSlz0@%@A@lA<u"
    "G=71uvMW-rFyE{@R@LNbjj?F*imH8C*-BTFcrw&<cd!w+vkh+J^)lmB*nctP!T-64*u2-l<_qeA?Ub==T1fkPB6o"
    "xK=JspcZO&Mz4)=@Tst$kW+#kD<$$(N_S<mmuPVs+{gxFI{?0_t}6%&KKdZD_en{8bUXx7(7tA5^{y%2xqi1pl-&"
    "ay#`u5Dk1_6J-%-YPZZmq$k0`T98{UreU(0?+bc7;^=$_DmMlV0^JApj1beToC7~l&_9-@fiNXmyQCuWze=h?sVL"
    "Qluod!fb7!zkoo=(nN|#=woW*FaJjtv<T;vUG?y7Qgi{<P^Mh{(0fb~}WYT{ROFdExC;P&AVaY9wMfIJobH-1~7)"
    "X}czzTumeOJZ@cw0%_WR9bA-fN|lM_gh0e07&;5p?rz(KrPreUT<b~lQkQBV1mOJXgl05eMs97N>KVi_d^_ho&(Z"
    "cp{`D1-a4%P_FAl{Hf_Py5rTs)w4e4GO$gF8ihH27z(NOTQXiG)1*?{9q>6Y$j3k<%xU&X+E7y1`r%Q1(pt4#}t>"
    "QWI;)r1jFiSlRm_%Wtdc_%OYB%+vT*bl~5fs8WdBbFC#L9CJD9@+Cwj`2raK76YPrK~kGd<g)ZqQUIRL}{A3H_{8"
    "hzrIM3C!SqX=FH|Am3rxHQeY^qfW*9Bo1S9;UKFg+#A5|Ar}#dCwgOjnco~PZQ<TY5%{ji#VFQ-8N8b5?8(=k28)"
    "57j=Iep3XxZX<b9go3vkPNsbsT;Vdy|SAfhZ~#XR2t3ZR=z^+_<*xi|KgGDk!^wQnu3%_LiIL3*TlJ8;Vj8aShj="
    "TLaTEYFm=(13pJtuCHWT=Q*<f(hoG?e`R1$9HMI^!7-(ToNoIKz8XeYCPni|8-2w%jB6^AY2Kq8wbni21eHD+X8}"
    "_RVuwFax6Kfnf5C(;O;Q*eYUfPTb^wXh1|ENmx1nV?mv(+{W$&jz0r$dCt*GZ<Ul1~z+bB$*5$x}mKghWWV4mbd5"
    "Oae^(!mWinZ7FsElTf%W}g_4<TV_kXChY!0%O%4;=kHTHOFX)>&HZ?V$waq>vQ5lp5`z^^k9GZ{P8M-J-jLhQ3GX"
    "W&m_*+d(8b!(A^DW?y@?yDc&ykw*1ro9>bYWDR|@hJSN(R(w)*lR;ukatC>UAmY6x3gUESpRes5W>o=`7PYjql<&"
    "vb271j})&W&gJZu|~lAzc6HqGx@O-Fs&bBZUI7Z=yKLJ{Xc2?D-ii+6()@T^H{$luYxY1GoJ1HWHx;Pg3gzVyw>a"
    "`Eo^?Yryb^yjnJufU5%c@UuFfV=Y<x`?0c*N$bkqe8dQg-KXtz|OOsu~Gn!&gxY!=-nD9RKW{dQsVZ&IfFr)BGwP"
    "IDXf-3fwNQI<YieS@D9%HU6!k0yu_xV6vsgAu#Az^5{pAu2C-U2Db4UEj)$I^5Ea#<m)VAJXr6+vS4x>`2}LD$vf"
    "{pHBvtfS)`AP1uT|l^Zq^uC6?MHqULyG)?Mfq<K};4IcsaP1aDB-B%8G>o{2-~0@RDGtgIAa2H|Cn^n$}a|=f!;A"
    "I&?wFC~)*iTY<nogLUI-T{cB4dqN2ltOiZvt71l7%BeTn`?<v=&?c(^qaT<6mmE7H1O0FW$+ms`w)k#)sT(En5eA"
    "Uoo^KE7@oP1F>`m&ohBO5pEKBs-jJ0r`Z{-SXzbT*wy32BoY=Liy<ztuAHaPdv4Gbn_u(R!<V!Thn+M+n8Y8BXRp"
    "@fF<rB}yT7}_)l>`^s_v@oKQa{;VjATq*<bd4-YQ@O;1_hq@EI!{n)C+VENcz*h_%gOLDqnw2(#@CkF=kW1?P%5;"
    "@3zqBn<h3mUA-y8iuZI~*kYJ6Pj8WBavVuvRTJ?vfBwFyi*fb*ZEp@&wJ$oUPhLDy|NseiO;U7vF7D3hkb9Q4XZ5"
    "V+GjJahxt1>#xEGY&{ZV9g_ZXuBp4U>VpG_?jU204qfozwRoEz&k=X+(c;a-*nnB@C!<np7fdx=>%8{J^v^ZPhzy"
    "j}*&rIUpiZ%<a<O*?4w_QWhP|GP)+WnB|6L=s8#{-iL=vc28Mf1rf2SW|&Uc7uZE4jL{$jqqdGT5X7>|(dSifs!y"
    "2Sg-K#EU2UgFDXu?rRt$o=VCxMaGt9BzI&u408#T1d@V-Mf;8)va+#Q@vGRp9aZ??#|J>1M~wv$#?_F7So)>|CQs"
    "=dX~=89NW#lGOe;mv5+L@aG$Pk;u_Nl(dW*D<tG(ca*<sT+G5+-DGKv#)Sg5vpwMEw-71sOP%6^FPPJ3+%ez)_S9"
    "%m>8GNqwF_6w6jmjI<&_xx}@>D8VcKHt~WSTq>8@fo8+3BfRR9@DJ>8u01kiqT)(({b#{Jo`FFpypUz&7(eoOZF`"
    "S;RyV&v1fn0?~Nv1b1Wt!<$Opp0|f}HC5ZqsD>pjtJR3O&9Cyv6&FMBwziY))QDb7M$a15PZO;4+!k^R!rGRm6eZ"
    "(<MWxgd4M;V>YHmtt01lQzq*3TFo(#l{TTK04<@v*{H)=!DPVT!3V4cPDnYQZz>o-<atL49voRFZQ7j)BIMzf%<W"
    "Myox|=w1gEJ6X${u9;gB?Vf`UNWyurSq3jq|RsR)98m2Sg<<H`o`zHoly^x-R2$ibEHyBoThbZ1Roup=NEy&)|fq"
    "S)~X#S>~<RyD+R(%S-5%sIi|1D%bKPkc1?EM`1|c!$Cl==@wGB}GAY6y6!OC;BWBHsz4vq75DOd7WqT3~W*xkq-w"
    "UriZJ_rhs8PN~diuR6Vb<8O|fX*XDDaj6w2OWYiPB2$4QfK!t5XP1}XjbZA*sT&Ob$T;MCQ5^u_R=GnbM0|rd94p"
    "53Afh+32OoV|vN`VT#DUeq$t?z^)7H~yrm7xU>B>bv^k7<raBT0xfj3P=$mf2@uX{yw!B+>)y1J?}XWD*)F0jbn!"
    "ATG)EfZ5x~W8u&t0<{UN@xU!pr46bZeO_|P0Uvsq7AttSTSYdXrwXdv=yimI>vVPYxY74O>HVkcdREcaP#W)3{(>"
    "Vx0I&XOj)6ifzS(q9VcW097{QCO9U+1%K^}m1xZdRG>S&NXE8oFcwkOXoPqTtnC-j5FlY2-O<wA9J&>u&sy*)Z>f"
    "b+&bp!OX=2VKaHo-CSH-LvVlQgqi>y}cm~T$pH+@=3x}PZ?JcA%Bu3r_k2fr#$2He~m_V>26ROXrq+<dL0aEAM4o"
    "^QHNf`N2p+arh<)q_v;5FUt2}*-TC?1`Cr=rJ%ht`ZGf@S&h%xa>btPm7-MjUTo%kp7+Yqa!{ee#&_y%|S2IpqZ7"
    "ip(j%k9C<2w)lbcPf=;{wtq_+7bWvn*7h_@d;N)ZGd}Meon9f4+Ek4F_FbZXHjU_>$O36q@RgEvm$y2n1<pW_64b"
    "OGIq!qPMkD^tpvjB^aRvv88bb#4*A&j2z^q1G&q!+(3ayZv$5xZI0k&&`za5U#96D*?lsL!cVYYX+B7%tE>iJ=cK"
    "%!_Q8Vvl%h(7-tp|VC;_q$0;(Pn{}yS|L3=3I00Cy<A~ZOWGOKo~vFJvm)O+YtCH_d)T!rzgiJq)b+wKpfdAeeX<"
    "xt>mUncc7m6bs6lFX_yUF1^S9@ip}aKcz1We_OlF&qQ&DKVbcRRqZAs&SR+tS+mWkiOwIjv`xWk&1gAv@P7WJ>qK"
    "VMfZtKU}mC1I$uvV1sn*)E`h{%owuS75O8>auVs(73egehc#xWJm^VtrG_=-3T$q%n7H-cKMjpuA>!1cfUR732L<"
    "bu3$?o_Q0xkVf?u8a7Lg2d$eF{LTr&;hC6t#1vbvk{4y2a^B=zjnsd6MAqRjJ#wS|Eo`x#X1|c(z$(Hm<}VqSLt!"
    "&3eYpx=M);4?`}%HW;El*O@jJdNHNJn+la+34+nA=rrmgw=fZviTvU~J8pYhnV_t$plgYxdF@fW?3SpY80_1?eY{"
    "I_a1e>9F^xXbXLvJIHMPGZ@}5$b4pNo}GEiC*mz*V%V-+W}V7w_;kv#=<#}IfSH#jGU)?cBNk_4pI>#F>mt<ng+)"
    "Dxb>m><Um@I#s*oC;t~bKIK*RzwgL#QY3f-aqA=64SR!%EN*oO}Bx^AfnL@x^0eX8O9j7kNs>hLSkO>{hAS;Re@@"
    "RjQxKaN|wta`EmTy#U&AgvLa@YwfD$L%5a|+#A?M;tBLgYr@C=CmD6^Doo_jUx<qj2sJbRU3FiSb-z2rnrtOvOWh"
    "yWVse&PDmJk^w897BjC~z4K&&*VwDbmz;m^2O2n4usiudgn2LQ==(mGepIH6GLFvxpVNHTE)&Ywhu6T9_0ZvZ<2-"
    "hW4tI5b*NAaQG<kDI7dupW#CeQuCJJtExS(P5Oy1Ss}Bt!5oC>at52!Ql1e#a1c3yfyI?ex&qJW(;A;hPRaW)tR&"
    "p3*geU%bSO~KIHr_Vrsu<xO?v`kr!`E9P6vAa<Lislzl~o#|LNrH_4pMz#_*w$?4?NjUzD`jt__1Pr!^iNoH$Hal"
    "d_KCFftkx45wOoc1(xPE<|g?fSQl%$4j=971+f^Oj;eF<)Hvjl~M8{Rxg6HsV4f3g8j~#zrWd*k!54$zA(S$7Fy@"
    "(NDk!+Z(Wmi7f6hV>qckcdA0TqCFS+(RKEc)tx05Qb=&G_X`|M!{m8O2mWE%apHw`>oT<T_l7f;=>GMI=O<Hl`vn"
    "VGdy0g+O-vATrk7=z8(OnC#Bf?xc1~w56*&q3ft0G<3cV)Bh<~V)fljJ(RSA~7Bn7j}4*0A4E$KObaYb9@lyH#yd"
    "BqPQSu^2{}v)X_^EvjtU;AtLfj~uaHb#ZV%CO=tjVXBc0Cj%I}6yE4$(FRc~0}Tc<nt8|flJt&UQe;x^x<eg0VKY"
    "6}7?NM7d<Mh*y|_YM0t4q-7K4F~O3AGvYlQpIGJfk6BYjBl3oIdw51G1T3ey;-Db^wqdfUJz3l9b6R;A`DTT^)g4"
    "g~e&poq2SNh~U1mNr@;>BynKR#lzhiO8oN*n+VZi_#njT<V(i^FeZ&ZeR!)P(m||-1$)T7Z`)1oS&HAAj=ph5xJ&"
    ";qLrZ|7UesX+Nv9--HkOT1B6D6LlfYTYjJd}u+NE>8O9z&xJSJW4o*DY*%SGxqk;H6<8J82XiTxwJpoOQ5<4o^+2"
    "{DQI1m|&L>jEe+%a<G`C}P9#g5*?=PBboqVs4%Gc)0@_jkShM|zd`@7R-p4nnn1H)_Jr)(b@Fw_LDi_#Q_{sOK^i"
    "@79TujOc~Fol*6F{0tzZ1z~ICy=(Q6FK>>%G`qFpsTfQq5Ye1W9)`&m{OY0g*8eHy$5jUQ%+ZtNZ)!Iy(`s=BBUf"
    "!$LS60ZMy<x5fgPe!$@#^#nRC?Fcl(YXRnNgHCm(!$pRLz&iitD_WtI+D($|sQ-<TC~d8|(h67Ph%lmmlZghtL<z"
    "8Om4k2PAS7+gU<Dr7nU!FpS%y4Fc<McE9JpTI<gDjGd1i&f+JL=Q?-l7qZd0oY<WcayDNZW>S_*zKDyBI5i>>?tP"
    "&`PN{<u-Z#)1_k2KcqYq<LhD5c1Y*ryj{BD<XIJA_L%Yfz83+(s!@4SXw(F+~Cc0&|>`VvC7{x#`X>3~_U)FvhSa"
    "}Dyiu)|jV=Z>B&i?whv)8Y?R{r~(4t6TU0y!Dv>oA3)ptBjL>qQrpCJEt2S#uC8eW9rS%KvX<8x8$`J;BB!i{;ya"
    "{LICQ@~?=AzB%d+Ky{on>T}ak#k@p*=$oTWv+VyVFtVN`uK+l)u$WUVHjx@R2Fc+AQF5B+1VdKn>W%@J4R8frt*~"
    "txw2#PN-R~z0)hNsLv#yXM5kIeEj!Ko>!g|KMb|N<#YQK(zB6T?&E7PJiUkEi>9jW5#aV3@2she`W#)#b^1pi;f?"
    "!oPtf-yPcBz8)>oASgEE{QdIA^P)5t?0Owj;k8(6AGm0G+$z3G2+hz*xKU&a$<mIFkMsG^sGpxyy~W15I~G_qc9I"
    "xn?WQ@Y-GrD2eZu>6oK`I1~2in$!($I1S1fcZO>W8n|Rjqoo!^|yJ97fc&NfT7;HkEnZojtBr?e}&HzD$xVtz9jn"
    "x`w=$iG7hc5FmR4T{#J3@w<*y@{7yi`UUqYO!*QW~nzKjs`p(Eu#eMNJDm;#BX$;>NK+BG6Qz>qOsJ2g79jnU#S?"
    "Ji5GL5POay5(ZSrCd_wzDnOx~A1nuTohICVvW)<>;WzXtD|4<h*rijKf`S;|r9}hcfl%ZSM&XikAZEbQ4C$HlvX?"
    "}I6*@;((6JOCWB@1UI%V6e@XgG)8%P_TRQKgq*qyp1ePpy8sQ`L2t$UVl&+Ab)-bS_zOy*V+XaiIWxH0!ztg=J_W"
    "-g=Brj&<oAAeG|)MsX#tk%tjH7RQpj;S|uDE6Zkc(QF%6K=%pXQ((7Q<}85g^EH-4-9eL8j8sR`u8;}^k%W8O<Q|"
    "hJQ+9G)+Np|;)WDbEg$Qs`C-mXmK+GG@MRBSc**!Mq&aP^Q8{O8uw`{j2ZMo3F-opkl@@cTozsBI+-BrI;Uw6&Nt"
    "7l_wMFSzV_tX2HR-p-2PUV6O))=N4n-pLz{#%b<tE?b=F=e-9Sb1{H*{c@6{(a?7W+Uc3XEoT%;!a|@xt#3j~b><"
    "b8nEQvUZpr7g?R&R!W7OcV0k*2ijhCMB|^lXG>80yfSU=i-lJ#70c8|Jc)c_C$8Oq6F1p9g1EtkW<CH_mDO{K3&D"
    "iglfK?m>oD$P89r9^Z$$nw#Eo@PF-7zVP{(aD%^Qe@sa_3MWm-ToEwcJvyX!5V<-UE!GmG;^DuE8s@k+6|jKa*&x"
    "R}y(AT{R;U|OjFjTRLtsT7?W?(3e+zW|THB0_uCpr~3pBwd*lB}Rbul%!bR99dLXYve^szHq80S^d8Q<Ey;|ET4t"
    "){^04OPaylDRHhj{Aka$Nqq=QHdA`A*J!sTE#<2Y=$DPG#*LOGS4_0tVv)j*<Rfu`t;4g2EI$xaWe&`MpGNs+~+O"
    "?_O-yZh%`=EjS^+xvL3H|L2=0{rdu0`*TlLz~?i_JMz=J%GHv%xJ-B|wgG#h#SqWAjAm{7Pp37`Az>-o1SVH7qQ("
    "AjNW2c+5dQ73u*DD~TXoqAo^MS`-w(<x>QL&jvbUa5(~NDA#eaKAW%)Y!XHekjGKN>ZHdBFhD|H8Z;1hSt3@isf~"
    "(QZ)V~c!vY(^;oC|11Zmy&PZC|@Lud*F&|xaKUR))0S}bPeXGGyEea&FK>&ByJDY61+beg2!Ozm|(<@3>;yG=`Jz"
    "%|nHnIu^%G(wurdegAm5|t`Z0CfF?VOu=&{m<jeF<5i((ktdM_zzWKS;4xOOmU4artGUkv{o;ExC+>f7A_}z7{3a"
    "{sllx-KwHOQd#jr0!V#b5)DHia<e|pm8hX1hWky42kbJjy5c~b)?XI~)^&C<DFvqMCG}WfL<3tNj1CM)SJ;j$^h-"
    "Q<$Tpk7>DQ8qSHo6p<FV0lhMpL^Ew3b*HRU{JROw<apuYmKoqh)6exJ8kpfIqQUVmE57St;C(W&j*&H%H>_fdXW4"
    "c`Ewnqz#gy_4Y&em)l7!SHn-xuv0e1znqQVN8Sr_w)Vf-jH(@f`+G4W>$iU^ZaDf{wfffX5^(Id?=7{vw=SVZE4i"
    "JFRzZwhD}9R8KiO1(IU9XVg*rY?ZNm4f@wLQQMo<8*^(+O&;@#`ldor*{++tn5za%H;ulBa}mv5;v2RnJN*sRvIo"
    "&B^b7b>5?*B$tCbaTX76jVV%U33K1NPdG_aZ+ElUH5xj;Dyc|m^+-rK~-+&<p!#ujFJ~oNrkLKc-OwVrUz0jS+Ta"
    "t4S#Xo9I`C2gb<uedeXEevrk`l(gU?wPNyZQ|Ku|n9Izy=9p%VDRJs^s@z?BOa^SQ|jkGoF9;uWh7d5Ki_m!gkjX"
    "ElmHqR|3tx6G8%SQ;oxHpGdg<)s&8t|Z2Ehck5KD87d*|_^##mY-5BrI9wO2|!fXg2&}PIQJGxaq8@fo#A-ltI54"
    "{fz?chh$MQWjuiU(oIuBmI10a`@3c3QwD-%0?W7c?q~=Ufv6G4t6e?T!?;>vAh|hub#Xq98fBKk(!oknsG)G-O8m"
    "D~a>b66UtfmSdJRGu@2x|76sx=ni-H%yFgWENS%4KPEON}Tm;7U+svU+OF~s2}FMU$gBAYiu&L}R#l~P2Vr0ho5>"
    "@*I*^-kprQ~1cktj5hcg8#!RhCH3Q;?!o?(rE^c&8Zg{K))h6&Z7_vuwT()O^s8NJB`N_c>XbhM!-s>0;G6WtT{^"
    "HsgtQ_{=<ZGBkkM(xPZb{=7P9t&c-2Sz!4tUIBu#9Q1=u0komnr&bnyth{ug}eYmw!HX}kh=Tv@;ys7WtlBnwfvO"
    "Y?f|G__dTNq+fJ++*t{A~rBzp0Kf-^vBb;I2cd>-walID)xDbG7ZePu36I=ZCs1*XRC|0%|5j8W`XYPDn3o*+lR5"
    "K0}sq>@oVceeT>nT{z&^J=izKdO+9mtZq7f|M>UrKdFBoKJH&ji^ZP4;ji6C&C!A9aGrVVllb@l;iK?~gDGB37!K"
    "*yio(ok?9^G*sxMSUMvsw6L=SvsLE@cu7xWS~grRPDLS`nat(ayj#7-K%q=7gwq>=?w!_M?97F%Fm=GHa8MITHFp"
    "gfO|yb>@8Qb=_2GrpP!^cPkElOP@DJzJ>;poz0_4M)939a7tzZ+&R+0IjNg9%;aj<_NFyGXARy<BL|NV}u_URquY"
    "k9mLr4Vqgm0MQyx_PudbejT04Nqv`w(6(XZAVARa`(`n*ET1|$@Y@r%(N|qemg~nl>OxZlt+|FKE@*vleqTfP8B|"
    "Wq!WYJ}BB4^^UR)Rp42(MDjwI?)6E3`6k&S{x5^{Fhb7%!=E>k@*s!+(mk!L~LO5~(OxlzQqLP2kf;zdvP#f$z1%"
    "bUU?R?hZ<0l^`We#n7e^Xal=(RVa*cQfBz3B0I;2RJzHGb{&Y8YF%M+a|9I8%FGlEn{#2<SgE@uOhX=)(z_%pYLR"
    "RT7$eM$g$sKi2FJgQFaJ(rP;=tiDVG6;jAG$ENe$cS?2?ZE_B|otYhi|!=o9S)z1I4&)}Tysx5wG|n}VTu8s8Evb"
    "R%REOoE5vWg(C;u_tNof_lus(P*hBBB7@BNv@J@S@dp>SXd!Wwc02_%blLQew|#MU5`W7U?GT4I`p()DfRrRu~T6"
    "Kylk=PqPv1B&>#d<;W%d&8t?Mte8^|q)bTz=c%Y?Xy^}p{)#;)VI^ZRO0331N3#upt86HZZL-;v`V-Qv#?4;pZ`>"
    "B8Vvi}0psf2tO^09|@p$I9?SL$Wf#(jv~1>~xMHDH;XN@wVUkLUXOHPv|s5knNLA(IOEkr)8U0ZFVsXz-)zbB3^g"
    "l+!4rBDvH8Sk2XK)&P?Ob6Alz8>=zfMlxWPnPvJs!o6@`2N32XZ;GG%4)kY{f|NMfcwpdY@KI;7<3)?m_)n}G8tE"
    "C=QN>MJ+}9dQ-ANJXjoGFZ?o*u*nl;^_MBrkhmR72t7K?tZxV95gnn~Olr-c+3i7Wnias6|2mm3G9<UpfyoRD<L5"
    "{&WZ%*-?M0byV_Jf!$#YePI)l>Kt8buJ@=oC%H)*>C%DNLq9Rn3wIJ2*I@O%LxB1Q^2jF<48H%5jO9wR2lE_FRF6"
    "tj$h)J)=7191pkkDI+`7US2HzWbVr^2gm5~6$CGM1xUo8UUM5qhxCP9b@Oa=HuhJEue20Q1q#pq{u~HU^gcX9xtQ"
    "L)<7XSquMkX~l71Wz<6g=fb1&NDE{9a2NRUkoTuILP67f(g!J+4teA*Jsu!&=3q+a&ft2pAi=7V7_MQXnr(#c9!*"
    "03bkYku`v;drFK>z+p2-FV(%lsL6af)qzO@)aiD>Q=6IkxR6_=yUM+^$a)A-ZCbm!c+Xh2>7p#u1mw<Cv_Hd&PP="
    "f8E)+;fV}%gj$c4TG(N&d#qmmGl<$SZE@;oS$u?2@<iI$@IEHCU9tGAYQ*S?lG8q!U3S5{fG)7K5E5*(^vg~Jz)O"
    "WNlS3<v|Qh052NZzjvKYPW<LJ*oEq*j!wO)HLC9>@3S_mMtdmpa~67ns@A0oL$|u*XonxLR9?Icb9l{%|HYXk}F6"
    "VLv}S(O71c!r9p9$a*Ocg2GNy%PB`m{0OhF5LX%U0KS^W*bQr#6$;|d6mG{Efma`z9Xrv07)AS+>r)D^!Cd@)4jv"
    "Dbu*D9yhXFHa3F2&mpUdV0@e8jpsH*&zzObvKvQ?de<!3Cx(Df6M6cI^h!y56k7VQhDdX(mCs2HcbIrL}h#@NU)%"
    "+s()Vv%iBS7GIdz(!IIetTCn}KS1L*EakBML6L{ayZvq?(@<9K1ukRJ??$E*-_C~ni~YJ^oX2I02a_ZQAS9v+2fq"
    "9-)WZX{o8ii=_KFfwDjV0TBc+H}Jv!%6b8V0Mmxk|IzdZRxkcSbFXIXLkwBFY-KhB6Rz1wpGjuB_JnO$^<jdlOBi"
    "Y%!^Gj?-yUb^idi5iSuyayEErXK6FCp>y0XIvJa1Bijrsl4XY!_*u=44{+KNg`xzUHghzxH-DqxKfMB^`yo`d<g7"
    "w4A>?|I!1aB#By_VHGVxly-rZA6c+(19TV0ye!9GPWAp$*qc}o_peaGGI^G`Z*(i?gV5yq<U7F`M)6YW9vzkN=L~"
    "1~l0k?M`K(NHjLa^Z!1gNn_hpO=o`()!yH{!|n1|VCE3I$sn5pSOW-V*Tr0z{eq=>=qUd~%Q6gS_W!`h4h0^l4-r"
    "!``*#xR#6SQF!osH+l0h@`v6N={%W}N-gWr2jJ?c%IyaVO@AbgZaCYs0@su8{+C%A$sd6YbRv3cDHT`V|9tU!Od3"
    "T`m#@fEkb`3P=``3TLcFz7gx%DdJ_fi40g;qmw(bz5x3>@i*S~r_=IUpYv>9psDSNRx0?sT_ca;vmohSO_^mP38+"
    "JU?w+|ab~yOFv2^yicFzmBgam*anXH@><azxowV4%%{*!gk2|FcRi@jJ#ni%lXy#@;W&?zrGMFvBTgER8p;t6z-j"
    "#o`GJA?3QSWw=25IFDI|xjjxi<UwVoEziw0@ciM6SP!P8Uj-$fDo}N}o5lD>ID_S<6*F^(`LA-9K4X(FeV8k$Z-S"
    "`Ul^{AW!(1Ui^0X}vhs&aHbHT*_8X3V;wHLJj+&%+Bp*z0Y!GneA@JhYF?H`#DtR_rFVDi$5>`mt9-;@WfO1$v<6"
    "+B$3UMLPcATCHCfljXn#KgMz$ks?E)C3GJ#Kd9?Ig7Ec+Q!tV)5s>#W@Fa~%Y>>$>mA{zg@~4YSte1Fx@@D*s)jd"
    "<p#`nBPvH<3Gljoo5Z^(ln1f~OEnUN&QlecF{Q<nE$X(ghf#$yN^GwTekyp$CGl_n`C6O!yksxF7A1~!wVww~bL8"
    "VzTzO9d3=X+gFF&<wzEgNJO7hvT6C!Qk)yU-sUGt8pYr8~!Uf^qzy=YrCrY_RhM-)60Onn{5hef$G}%FrO`3322c"
    "euO#F0u>AM;#3ipv8AH)MJMZ?)IbGP6QmMQ|Mm!Pm1S)CIu-`aH)^6yD+PuFifo&wqt${EWX2oj%x=ELIjJSj%B1"
    "`26fB;W$s=zF>MuD_D+bZT8!Z1lOx9lPt)&~uJvr<kwh~|k7r?D+?y}f77L2D0noGEZ1++dULcDIjI-k%#ctNS$k"
    "3UzX|__o~4r_A}}Z)Ds<lp0Js0Q5qbJN&&%%*>X%-?TfSZcm6nAJHcVn(0z4X>731B}XuB1k-2Om~=`_P~ZZ)@Yo"
    "lUA*CP641xow8dR<d$1WklfS1~a?Wso91t6`l-UvXd>kI(7%qVQGbi}z5OiB<afgTj*MAMBRmR2lJ=nGN^e;J-0{"
    "_s}_83~#?HO10<no=;sZMGXpWW8qKbybTb5fpK(wXT_UY+(9E-`Il+>k<s&3q5$|RK<_9-{?lNeAL%i41ilUg%Wr"
    "MF72Mwtzm6a0&S8#S=#hUV(gZ_P~OE*p#VBCM#GD`ercUS%7zgGHm}BuXr1O!><Qibko+>M0rZ!R`X}m9W34AOT~"
    "rIgv_(en4z+mu;-WD+T8%zxSv@mFqa8*k=m!l|K+Pi<3;x=&03RBlKrn8t5w2h5+q(}zOVGn!e+dg;h8VmR(hMUs"
    "PRu44!cC^$Fb%HZZ?8q)Am(u|2Nz}%YD4D_ly7AZ^cOzHf%we;&>uaOwbt8DHqw7v!_}TsGG9YSxHC6R25SwT;1T"
    "NRz(4cy?S?is*tSnKZ#S>j`l@YYe}T+4MfU_76wcZoenxf-z$s0TI`Lc4nO;@}WJqtatifThA$Ir?LF6pehTq?8#"
    "2jC5V?{s9^fvR{OUfMVyr>G^`G`3Vo5|YW9nCM2iN7U_mb3NMhU?(a&nl`s7Vxxa5O^Sl{Aa@o0x@JgeH)_1EhcR"
    "nIq6HV0ll0#NgCD_2_bd0I$j$3!MWJ#>J7QsHCR$TplSpo)&HQf)0Vx5;JGM^2NyM?24DfyLdfMHy!I{|cTiG|p+"
    "4&1H6?W0qe6S&P1CG$m2L)?o1VbKu~CuPG9ScJE|lW1)u=s7Ir0=GODEZ8<yep8HDlfS$TIR&k;n35Z3D#k9c+uT"
    "VJ&SwW;Z0DJ?Sj1pQlP-v;xPbItJ|%*47OhJ)j|v*3*FD#>4ZGq-t%xZd^uNNIj>qZ4Z^L4rpT{ZL?M0G)aQjk2k"
    "-CxZ7Uw*kU<;CWfq_L2^B^&cWVB$1F`6apvqrB+XW)7^iW$V+VI^H=GL7eq1z+c1Q`r-Yn;>H#MCdmxx*&?Z#%Ry"
    "oypxXOdZ~LER4}7==)2HsWfqw8pi=@YgfpX^xPfP$qyiu?(ZeU^MI)h44)W$=U<d=}u+|<-j7Zp+VFq9U>%B>7y7"
    "5h~QHfo*K(}j?sUX`8t(Qy4++~M03SP4?#mv!;8YFu9vbbWr+pAc@#>nah0YU!|8CS`}I)*Amg$Id&Of2ARJI~tm"
    "_mh$+?W%5G(-<g|qOgel31zE9AOYztu&7On}tdy2n`zfpg7!AJC2i5ij(6&6yK=w0ctwJGSg|E!-K#;Ws_&aU7me"
    "IdN~E_m7OnN7=J*_(x@iH8C$MJx;PFJle*vcgq?eeT-p$rnv(w20P>OXIdKVmaa7^_V`-@*liYd7X-HfZB=t8e(P"
    "|r8^SEko1qv@%%f1?sD-L0bK?BsV#_-A(kkie1z(a^PP5HJ&n-X)YBE%^K<aIX8`&tR9&xwWyA5vj_ncW5>PpvJ6"
    "Iv6v0-Wve-+t&D_4E8m&I+#mMbp@;y{Ym4Jt^3W2~IGw%Ym^tyvw|sCLQv1?9mSU3dP|WF&LekDotr1c6Zz2<n&;"
    "8D*p0U=w%X%gW=h}I68cHcrM=5W5ui~351E|nQYbf@h^3><t|E-7*tJEjwz^#UKRtJKs(7-HmkKK0%~!yzF+%E(>"
    "%{H&U2=t{?t7uKj=v1-)v6x+<gDEnPIi_?=&kAEnZeHz5ncqQRg1ZNX=!U^!&fmp8E&eJ)2dt;4UhwA~-oJc`Brk"
    "*c(R-5iUl>D3eCHu#U<1P<jK7pM@+?Z&vCw#b#sSbMtFYoZ%^@)MlV|vg?$a4%tO}O?ChkLsF(dD#^F)g{gGvzCb"
    ")CB@(d037cV=1*{svq~?a;1>OPG1ulSo<09q9Q31;(yN2=#*n3QA*a1aOf1}wD__tdkb(dUYx>oEcme8}e)+Lxhi"
    "*9}RWz$LgInl`WhOzUywh?Df5o2BqvKRbXH${*w575f8wnci^5~JTRXKSYo5u%OMmA$(tT?TW=S$*-Ma%&ryhS~}"
    "PVOi-wXB&iN<NgcmJ68FOf@(=nq(&%ib#jVn^Hf$5ROR5x1Dvw!DnF=2b}3UxZwSbiOS0>?q}e*@RJe_4b6n@BmK"
    "K=oJJ}?GCL7kMWshPmQYks`E@YUtKQ}q17fO!VnB78?tuJ|W8DL^UGF^fgGyH4iriCCYhyibk#lthotr(+9Fc~wT"
    "er!7HAhHU5E2;(=iwQ}+av~r%lXTrAyOKqrDuYw&xS@UxIdgD$c7Axgf9};tr<4b##10+LPd$P?8N*X|Z}zwsOi>"
    "TQf3WA6x;6$65iU_P&pgdeb6d>xM=}Y)P+Q0u=mpl&=Gg`(bY7NSmE&fZYADehcn_^fA5t}NI@Xesi7G29N9C52;"
    "*#cQ;+51EWdvHyaYL&7A*P3OQX)|VMVUA}R?<}+9#|IfCQ7fmOzvZa4^f~J9<VUZP=pzaM8sUw{Dx|J+d-vJ-vUd"
    "TL9Q261E<;+Yed&DgA6K2LI@Y6WCNpOPn@p+Tgi(U3X9nJk(A|6NHvxS0S`F6CE3k96!;U=by%w1rylH8tU&H{61"
    "3N*Y+=GB%E?McpwEeT1(Bykyq#tr=QDD}YZea3&&;Pe=R2$VX%Rn=U*)Y`a;;;B(8j6^Wtm&)Q!GZR0)hcFub@I6"
    "Fv5$88Jw<RDpuJOXa9bL3?IPr0Xzbb)1_E=BGX_WvYBCeS2sDPM&k`u?}}+s6<D<jWXTLk5s5qm&n&CVBb<J6jx<"
    "GBqAC~Jaz4e<@s_TLTcyGbcMf{wG$rg;PwbgRg6Yhf(#dqiLO<~BkTj>n3fh=Jm{Va*O*s@tRWya%e{m+IJCCoZn"
    "qK+ptJhzB*M0rR?pNP+%l}G~N_KhVy1>jpBiF5NWLFJbZyx`uf)`|1NZz^vnMAH=xo*MsV{%q4+<`4>;fW0r)&pD"
    "l_I{Aahkvxq1GPIK!&iw~9G%KnF!8OEtl<f(q{<{ln+%>Bpv1$wfAZn@y!B;U?4603%HTuoIUGDhV~)L2fDfp-WB"
    "I8nqFL2q|9nU6{*#-WyW4Igoo+#qPH6I>r)57(qH}*Oj3sEY@|+}D)zV{gG1{5oH2zt<4(LtxYycHs3wlyNg6+%f"
    "6V^}Df4cJY@g_G46PRm?2BRYmhNp+W3=e2t&VL$;qv64i!&8?7gIGt(Tc<eSO|E-p8uTeGZ2F1-6+tt-#U@sZ4Ji"
    "m5%X&}h?N$z+hbM^;wW@VY9Y-_NY(psVvZcPIX+Z0OfPsz+<9xlO%pH7FM-dyND7Fd+ZB)Nb>7v?FIm#odC#mbuG"
    "ZJH17s`BD08(J-Tv+zFtfjp`68a}RtkdN@D>adbp|}3Gvy)>yD617#Q7U99vx>ne`w$~m2Pkm|8a#By(7<8q2y%e"
    "h5+{`+H(|{yO5tws7u$Rz%28m|g_EDCB9e)g$F&?A9nqseS!Q%4o~@)dsU%ExP~2v)h^ri!B8Y2ix)xDJb)u_0Pd"
    "A@vp8@aH0#~>^1TIunP-DXh=NT2=arY>+#|Yi?vhJ@i?Oqkg!T>^T0^GZu%?q*H0@SU&`_Sag+p~<;TGeu-^n%)T"
    "4iioS)NwDFt|K>c7dQe!l?CHHx)mbo4m{sj<F43X<UM_cxO-4?O;u!h(8UBx8t0@UDvD1?74Zmp!)WI`C<XN9rzl"
    "-)AFZW~xdD?>u<(1C36tI8X>(?cIqx!Ou+`IEY?LvP@ZNpoL&q9zz93&+?9#8hmk<9d27OaapDjlF{Kh6MRa;S2L"
    "*mEy1K;%iA9b_=L*%OdD;$9Ialtiw%&}p7J)b|OKO~==a*R|f=&9qZLly9)y=*_q6pJNrDk6zmX<RIQfjBcf;N<E"
    "fs+$I0)S5`pGe(Gw&egNpr{##0C<?vNjqa9))6olX%JQsBRvlE}1mITLz^YgkH-;#muJ^%8hQqrYW5C1pGAVD!y}"
    "`Z17(GM^M>|ZL&tpf?d!*#5m}I9=+M>wkP)o8W{%sjwBQCL=-EdMb7nC!AH;`UwQ=TgKPQBXmKqdDIQGGE_N<^qs"
    "(eR|QD!39|cLz5+@whJ+8#EHj*`!kZ%vUWv4{k=_VyUl2oB)a;_VhX)?ND{ZWme*!L8|^F_U`KD%gRU2?L|U5a?f"
    "6u{QxtFbq9=?pt5sJeW^*4ls+{jZn%U?%hb4lfnZjh(lO_b0MF>8*LyV)rM$+0BP!ZxTIMMvmm_N~tm!&=BNo%N3"
    "XaQi1}-m;5{XARPJpj02fQi|lH`JZnis@*1``e{yitNtl$RcFFJS^9#&KLhreekwXwXr%UJ=zNQp!?c+n%3oRo%d"
    "1h_2-LKl23RUlz-%V^2lh*oL8iJ9|kvhDWv9&*$D!`QLbss(lCa1p4_8xO0`r<_ILQsjw07ZaHB~32{FW-zl8R_D"
    "ZAO*V$NuXtbkmwT~kZCL3tBK;xhRZH{*hp0gnC5@MZ~rQhL3rmdjuX;F9<a0KjS>rHH(mc0qTJLaZs!m+WbH5_AA"
    "_QG6?nq=vT>N7}^t3<*Xz=ma#`LXp($k?;VI1EXLKlbYC0DFvL%&@*}zTXd_4h32}c3ItDj4x*Eru2%JpRu24kU="
    "M6#*)o8z&$;2BZ=Lwq>zf|6ucVkoJ_%Utf`PUaldWDRKl#N4Z)nO2D-tVds<A_$!^J$f@(@~<q{mI=#Qin=cgZr;"
    "`H#xpU!LHo2GHYJ4m2@gi)k0^4c^8bPaq_bRH#@f%|L{0~_~KFy2CiztFLUt{igS^~7OTR^XO}!>4ce?M)BV)mRn"
    "@#fpXy#||IY4%@CpvisIF_f^m4;Zsrbgv}`Z+q(Sgo;V$LhyO9$|8PD$<2zjX2rZY~!e^$9Z>&e6+7`PgXQ<H*d5"
    "Q?c^2nxb<`+DxEkZ{0YUwKTRwur-Ize7<w<C}Pi$vG4EN4YRx+J^1iQU)fgH@YkS&0_mTuictyAo!h?JTmhN-o6L"
    "N(F|EjH_f0Ed52<(<z+nJdKtB;<4yQZu-dUhRRQ)P#`EV9c7ht6}a+N9U>eae2x2<5X*V));-9tEN!SK&MK&jQRb"
    "*x6Sch)HHnc?X6MYKTOZ@5S{YZm;IOJD0EETmCKa0{fJ@Y2$%TzX9qKww)Inc7ouuOlyurUIXRtdE4)(A67ee`K4"
    "z;o#P_-2oD2NQUp91ljP4J@{a|J%4mdGf;O>_suOEMGMkbDvAe;>0aaqa2AQnDx?Pfti7m1x}xlm01+K*zn3ugdn"
    "5#}j#{3OR?3nJ;7`-fA6Ek4o?tLQbG~qNax4X1p?TfrmL-o;)%tJ%*14OpCDu4z;?)g3I!09<MQofD8W7qMJ%eri"
    "iirNK->5HuV)Z*fd}V)K3tvK>APdrhbQmLuivypD~Y4!hG^NP)l?1DA+7TwzLya{8liQp~R0bxVj;{E7Wk8lp-Q-"
    "WRzAnYc}mF%K-$H=?M!#%L{^fEm5rw`GKEPsWMjkVk5PW#|;#qN!W_-$J}PQE{X9RQlvo&lAxWj2Xy9=F7Rvgl1k"
    "3YR$HxIH=Wj9+otuWL#q3PQ$Z6LT~ax)Lo%0ralhLUyFJ7M%#+#=o27w_Ey}Hs(u;+4j!!-+lGjMrDhLN2P$3@j2"
    "x0|K+AtOu>{BwvHc~4qV3xr~WK^abEX{%xmPhx@sdDAP_A~I)`{5~}hcX2QF(_6S&2B8*$W8^dK{4hPb3<bl5>7*"
    "cH5VqqAYZ%k=oh9WTamB2L}5?aSExf#xH?pb!E=C$I6ycSM~B(E?-!t)CfAv+#{`aGEH&ulZWR)rBHd^?D(l2lZW"
    ">NOGZGKq{gdPK)5E`ffKX_0is4E2%~qh2l7bkbq%-5nE*yXO9TBWsX}F-#+KpjUJ(@o{uMVeN5w}MUl0>nGX1_qr"
    "b5S|tGR;->!3O#`u0^AwD$M}sf=F&<0D{ST;v;A8!d)FN!O;)=7fE&_3lN&K0zB|`dz3f;9P^-4BQAz)%PT3t*0H"
    "jR8PdK=5IJ9@5)NUCrm$alEzW-apo0n6PEqx~RYWIhEeKU|a3QK(=<H1@XUPw>B9WBV2Ff#Wczz~MJ|2_t%G=b1;"
    "_>0`iKE6J&#<mGa^Hh4kuS@1jR%Ys(u!wP8C6M%eD~7bKvo_Hm!=3MUWg)(rANo_Qv!P0+OHBm?(lQI5J=mc6ub%"
    "Np;>iMS+n6u+eW&_wTiZVQP8N7qVrMU$dD2G@jM~-iob%*D;^Aw4u2V*LVZ!=_X4ymuX^GKbVB&eB-x!TtK?dx0!"
    "s(BK0Kq+M6eh7-tmBlLeT2~mBH3}l@es2O3g*=Sj97$QH5S;B*Jb+IM$lRgbB;}#&~Q+sW*hA2rl!JWXsx{KoO|K"
    "N@vImie>8cdJ_a6VoI4M(y$p9??SqR^V1U`H9z;81d|pPCe+$?gtE1%F+wqm=?Ml9*Ci}#)iMcf74s;T{<Y#Rnl1"
    "BXscUJne}OR=P^NMxlUdO|X{&lep#O7bf$}Tp5ziMCLlYLHJMmx+wk#(x66(Q2qx0ozw8O#gATn)Pv=O!D?QTpqr"
    "E=n?BzLnpv8ZrQv;W5&Bv8?GC83U9o*FMC9q;P&1b7_x6e$hO%^LL*78JVc$b(Ghwyz@Kl8RL4o10Bcj00d{FDgq"
    "9a#Oag@&_3`0CABoxTp=6QDhxvv*(J1r%{Uuq}COb99=*G*=`-DT882mPGOxXGZbKHHE>;Ue!VU=>wt>28dJG8Z&"
    "~YQ&_kDCf(SdZUM(Gw^dJ(gZV@a!jJjYIE<(!mCq2q0gRr?0I1E>&Ye&In>tebVlMp|_1eAKnLz%8!HU+k-O2TgJ"
    "79C~<tEe+#z)@qah$`CZSqung$E0Czx;F*{JKkDZg818~6ub)RO0`Cs52oj<O%>@nnqYpD58DRW0N+G)(x_eFHqN"
    "htB-+h_!8kcwqUx8g6s64D?KG@>HC8ntpPSgA!a|G}IN;&+`ItHSmY%#R0m4cu2K#NBDn}~0Se3aLdzCaA5*)k$b"
    "r&O7qx7=6Jj+NfmaA|zr@I?ZS}Rw8W9U%3v>Y-leVw#|Xu~?y1sd%_l+1Wy1PAdlpl^y%h?hL*egeHcGPNRA4NhZ"
    "6Y(G+MAN|-M<Y5lL%yo}8cy%qa9gtRwZvw@p(xbycW_<F%v?prH5ts3R70SGuQHG^j6ND0B*;^~Uml^PJ{KHspMP"
    "!kXx=HWa?V1W026jm@@=cLR&k)<jDuzMgohH}Pi<F$RczJ9<XM2G@+EH4KqD)fi3rOF$Hi*HQe7UBB3JawmNmKxA"
    "dJ%Y3*ZwoTq@w52hH6aJ&5gmUaMAeL$$>8~<duMboMh!QGrKjeuSeiH{!ZSO?2O;q<r#3;MWMpXRZeh)R%vx6*-N"
    "<b8YQX>YYJ@_Sf>dL<LX%1p7iGcg%;cY4h&i&TeHc_6uDLn{7ov}_;nit^L+Kr262Z&P03Npt^*$lU+>kA{{nt1m"
    "y8d%D7v~l03jBdprT<}`REl!1Qz)!paJU)i9i_KC32S70a4FZLGG<q9_*!-l%^UuJ4T~aBkqsHd~)QQ7YYKaMHx%"
    "5#!G}4tuON8Nrh5rn?NMiW10i3rT0aW&5}i=a_qNM4z!BIOR~0Bd*VQ*$yAaFh$bDS#@Q|DX*97#ifLboaeMhYx}"
    "aXmj{Qr^+Hzd+26l{d+=-NZ7b~jKgs__^V3;$Z3q$BC<c$&vXv<Xiz(`kBE^m^BznjTqRCj|2>-o`1bR1Yj_4j^>"
    "$R<`DZ>v4eJki`C+muTUR7h=<j1Nvl)6bz*va8+%$+1IJDC%{#JXg0ho&vn5LBpx>ti6A%cIg8I(S(-9v-HD93?R"
    "KU=WMc+TNn-CHQ`nPk|+9+3Uqf)6sbpK?3P=rjikb{3!d}|LZA{w3hGOQhBlouFDM)oFN{I0;8M=%3Ad`#WUwe7h"
    "5WhJBl{cOV$dK&!VPK=I;lFWw^OT5i_s&+q@SEaM|xV5%tbu6iD7o5J~UlZ_(@*?Q_2NKD<jM7UbemjYKi-YZHdc"
    "NQ@v7FvAl|wY1J~D#}rSvY<I-PWxGdYF04Y-A|+$2?!Z*gOmksVKyMva<Mna|1|ys>Am4PCfmO|jt&7VraANL#zS"
    "44>yP?8f<nivk>c+$F<9<-@X2srOLTqoMJ1RvEwY`_wivo1DLgHNTT>Bxmg6x(hx*?%{TE4PZm^D#M%)wc=svrhw"
    "l5Z}9Q$@{wh6l=?BYRSG)+lFRZW_`bFzU&Qvv(&a0xN!+%DJ)<pgw0(mXF|MPo5|hmbA=bS)|C1#1BSUr6QEVVM&"
    "20`=Zf23YIdol0zxY&e6G^Vnvyu14F2xL?Si#UKU;B?^4PkIKi^3yqJ;m#|xce7z!;wPqbl-(STP~ZNa&Pz#V3e`"
    "e3TI8Vb~TyMVWcV^!6e+y;XUeF&7FtAEAY20Pbp=-C!K=h5AxQbp`kh;1T2JUxa|0hn(CJQ!LrLST%+j7`xW&)Q2"
    "4j%72YC<OPhh>*Z;qWq)adhpf)4VtqQY`t2o1n$d)uE6BfMsc4K7M|FpUqg0cI9HU)$J_uE=A}Sl(lBYI*orL2mM"
    "A=>*$bdNh9G_kDn|t`%LRxl03b2)|7A}{O2~B6OG0TyTZvppDN>pfECZaXi|(6CZJ#*G)aTSxRrvtzAid7ON-=9a"
    "z1XCFq3L>H!8jYMNjihj)LwJ#MvMFGX_XtP;Jg(nuZPtR|K7Iv{PXHTo}7x);rpY#{UMdIGBe>=xO76g)utK>Gup"
    "RVIa0OqPmh!V{ERwCuFBq6=V+%^$w(IzvR96P3bzKHau&<OCO{ZauSHZ;O670}LqQqnWA#WRIpmVk@Q?=n!dlULM"
    "Uc?3<2_epJ*m|8f0@M6VwtK6L;tmeI6fxXFun_wW2&;nth7_g)*M&4#Sn&Z(0zMP0}|<`rCCiql9yKHcJ=5~Iw@&"
    "H2?;6N_(#2Ht*%X6EYo_1w0hrx`osHO4ZuKqalECeUqctCv)`;!TgW_E1M{a}A{PYXfU?5lz=D0efb3@qAtu?xI*"
    "a%xiXi@TTM6WBS)I_L8t<8xGn-F8?4ey>>hz<%(&?K(-ZTf{o8_Hk)BKa-wBuRw>fOAPWf@&doBvR!VW-i0Y?{FL"
    "P^~yj2HJDoOtXm3@|bO$XKv3TX!FX$lOG`s^fW)O4^JdI2;ej|9q&0$=-B}5z#2i*`lZ7iv9UTDjyP)@_83PtH6B"
    "sj+vhGVN4qtTI4W8_+dF@vQ|rLVu*}c_4F_;czQVFntQo>ke|7AHObyMc#KOn8mrfkjL5+W_h*mBQM{|V>ZzdlZN"
    "?MC%7^$^q4k1PWJ$ta6gw^`UY+j-D5whrtHu7VdS_zK~l|%VyM$BcFeX+G?y7lxCrF+TYx$VL;&wG6BMRzj1m-}k"
    "{b}-z#k^1ZJtZ#=;JLqwzrd;+&kL2naeb;=lk3MpS`?{WKB`}80CJu0@{TgGaHoO%*__E`s8n(tvCzn4yUT|rEp1"
    "_RRhHc%q7V&R6q@G}~03Wxg@RRMq-)P314nMeK9<p7+N4GbY8;qVtGKx+!tAo=kpbUCuw}^z}{c@TnGf~QD&Pj_*"
    "Wo?-4!MB)3C3EKyB8LnlI#Is%uEzBVFcd}}<Q6{-6St9va#AiAvbamiyyz{~likvxh0W2GgA{5OlZv9-&f{o}VH)"
    "xpeIfi5q%B?)$(=)7d?V9^j;BkqF1-{L8Ndf{odZbqEfpJLfsP4IAabdht#?fzUVN^Yn?xb6qaseBLNhYCKp3a$a"
    "*<qL1FuN3sc_Rq30hO%@w^*X@>8{SxuLE2P@c{+k|r6t4lf`8$q4)hUGbEKpZQ!RRVp7wJC|M~J>aFzVj!^>CY1W"
    "#$WQ(o_!}R9gVLkr2-WEsWuqO+xW`AdN7+tC?3Bgql?E`!2w=Wi<Y_Wn_ZI7&zSvP41-y64LMGxN=ty@SK_wJMMk"
    "qB})3c2-#Nx-}t0h$28INJ55c_GCGtHO2%Iic=76l~T@g1xoHC&5QP+#j6y>g+;jyOd~LQ$K*^G`mU@1MLIj?Yi`"
    "j?WIy4^NKI*yruu32giJH{=ATv3B6m_opZCPtJx1eR1!>rss#h3_UD$fA4sIcr-jvKvdw4z8y&9{Qk@E^zetj9v="
    "VLX}I7oM<@F~4-cAt{$cO%sQFjbHU2%=L*0YsPAasx)A&0M%d@)ZzF)A1e94n0qZ8@_w2q-rXD1&6i$yIdS}5w1y"
    "+|~l&cW&459fVxufI4Q?j8KqtV-*F&V6{9ec#^M+2N1J&|m$P8j(jEQ};Uk_;7p-tLYid@vZJ#{c<?`_^ih8PUlV"
    "4A~F~4|Fj30w&T;`zke8>oo~}_?UvAB>UlmrIU0`lKAit_a(a0FSDt2)AFA?(HM{Ub@BQiF@&4iay(8ETJF&b<GH"
    "oM~QKtC0;O}c7F&oQI7!?6}o54y|*Rj=iduQjvQ*3gPMtmKqYixpMmAo!c%_fdX#6=l?^BOyOKRn$#KcVK}%%^)$"
    "6&Py<Ue%XOanNwXAY#1+&))Byp0Wh68e}HKrguWYama5~e-0K-HmJRxlTk*RpN}^K(%fg^PTG1<_XC<M(poqj*`4"
    "DHXvTr|HW=tCC1wDmn84a_4|hKZ$giFwUCli`E09IJx>*lKJA3*>O-g}_fvSHIY>wXWHN}F!KonFj3@B_valTvue"
    "ek4+;!J+3#*j%FW$^&0d-A-LL{AR)tZv{VbO&mVrOQ|{V=%p#+ljWBAK#hCZq2@T7B7l?k(W@h$o}3&0Pzc+4@Hb"
    "T5P=h$;<V^79jbcN)>E#Yqb8kOdd55}D3D{vAw-fQ4(|Ec51@wMs|PmDylMxvD1vdW@?sSgaTlpQNhau8W6VhnE@"
    "N3fW$GKE2fb<k0CO(Djz}#{P9QOEiun`-^83?mX_)Gb>uUhe4L$$nkTi3zz9ZO@Kh);jJ9K}e`9|LO&zx(l3cwT1"
    "dG*XPPt`+Ni2V)Y!KjqsOHVNA#Nd6=`Ai)O^2LKfQ{yj7#X7NnbojLCew4~_6XC5Zp&c5@#*~n)rjUY0IP(Z1JL-"
    "J0V3ktT^M)i4n#toF?ZB>jzrKn<_EJLlcyg*IlS6dF%m%3Uh;u|w`765;U@x9NHtY3s0N+og%0dvz6iD$@1_@Y^i"
    ">N3<TV3yJ19Q)#^|)AO#0T5=?XJMQQm6^<$@^My;?v<CDslb~tXV!hWBXd@d4eUl(0Jwz9gKQq@eKQuUADAOQ20_"
    "#e1?(t7X2{rbwEyRc9-9VvJ*dd_iE2b220Jn5_YUyLb9Zora1<{*CN|C8TzbOl&{9)BulFC*fsi<+EK{sq^yc{Pw"
    "X#?GA}4v6+H@!BSmqvz$yb+1{C(vei|)fig@48WBJKP1wO~#*ZuBIk$H#iIm{}VrpYxZjH>I8HZY@Zaud|)?Qez`"
    ")Az!M?Qi9Q<a_bc);9xjYLvhNSwvNWL7>#m$wFp(hx_{bty_d3IMi6Vp)>w$8W?5oPfvb1JQ$vy*$DxmLAPw8(T-"
    "{v0A{~c9RV@gp?QFd+&Qo>fdR%V?2)!Fz){32obj|S$<s8NM{r5gP~pXvrEx8*u^OiqlngP4R_NVXMrn<GAoQ@I#"
    "sV!kdJ0`u_YQ6=;XY(ka85UM507ZJIFx2TMW!b>^z`<|iYUyT3Ev~ECbDF93qL$Xti?GzV;ikgEsu_%70|&vyH6c"
    "KlZi?SP1+;c2rtveMI9EYwZ)u0ja@yAim9L{_DHssB10}4AYUqPWSS1niAVQoU?+czZW{F=FZG{5s>XkoH_IwX&B"
    "x_*QRJB4K#zioyC{977MuF34i$djD*@k6lc~DueN^4>FV%X1!S9TmX6uf4U*uIj%hRVyYWV-Z>JGH7iu`Xf!!c@)"
    "GCC#R7x`2U-5fYx4t-HA7pWwn((CmY5tpA5STV8eLz;*9Z`>vHQ(49Nvclac2Eup{$|{ycQU4yhO<z+pV!*A@@Ba"
    "!att_gw@hxblLcoW>D-WQ4at&a29!8@~f0jk@Fxu&X=~1-W+l~+}zx`+tO_MaK5}i;K-9<@?nJZ$N=Uj`3d5!9C3"
    "rbxzp5w^D<zgUy0A_mo*Q+$T4h{(Cs!GhP4c$*#NAoY^E$$wdQ5H}0PoXQys#wlo8$paFkQ4_mYQEppkwR1}bjcC"
    "|$2Q-qiEBfb-N|B_m%$cvmM5=iXW7&076YN8y<!0FVtmu6R8v`7p^vVd!|X1nSn^Y{>H6O5^m*T#8eR4`1S;Xf)g"
    "%$Z7FbB|T=$|)>w&JQFNk_8Tg|$@xOw)~C0nclb!p>jsJFFoRjA`*TuMyVQbz7)P3YM|&Xf=+uJ5eGM;4*0*q%z6"
    "-Psx%CrILX(BkCF@f9io>j7N$G|4o)GZ9ich=O09>U7%=hg4A>$Y^C<I*(Ga!b5{tL9SZ{)^%XhQ$0m}V@Pss9(r"
    "r@n|>x)wbdZ0si`Y|Ep=|H7!j>2s*?;NK}ml5n+)97^vV>Wp(MOj5gbH_If{bE1PB)Up6N14<8h*wk*d+f;-M}vS"
    "gCcEo!{spDoSa^k#x{uZFFL1nefo-Mo6Ph^Za(aT(rCqQD>~W$x-k~7wTa!fpw#WOWZ^y9%wB%v>9sB2OPEyW9qh"
    "A$X+R<Vs_Iiu0}hp@Bj3Ni_vJ+y=>nXvPZS|TF^%Oq4mA`3H%fAh_=dCGaDM=5keZrGP_HPoZ^$dgr!iLj<|cXuW"
    "S?e|9-w$3kHA}X);S7OvD0#wR(CN6<CA1H2L|9sG#IBqXnqa<Fpp@vd7)JfG;jFYyhhuCK>*V>9pz#bG2m+&7uVe"
    "Xn*cH;>)PGE}do2r0K!YXKv>^`7BIf=^@%%UnItAQdb3xCVF4z=`Ce&@V_0SR1V<w4rzvi(T;hR3ANM_s8z9c9)z"
    "_O29{Rd11QY3cP_Z6{F0ZQKoN-n3OD~38s;&b(<q3&D_{u*zfa~eUsi)Rul@W4G+F$IwUux}V6b&^HiWV0*spa?E"
    "e<~|fM>N0Y-^-Szs#^hrW*d$c1=3BF{>np*R1))w9kbts3rKux{CC4bqRfPf0jjI{Va=ue{R>^kC;)aW_=bd%6?E"
    "ZcZ{?TOJ2U<Oa2!#y)zPB{1w~U_E)wwt-cR{uEb8TD0{|$*bZd?(}sKUpoAUdC?X3`9SyMX!u_K|a%n*rQvvDQW@"
    "~X7%tbW2jjn-Ll-R*$LBH0skcHY_s^m2s<4Dj!+SxMGgAqa%k}EY=y?{bTtV77NM%Q>+@H0ji3EzQiB~sc8kol~*"
    "90Oy#;NuS^4?`_d>n=q1396V%L#r4k<t#$}l_ngg)-13%s3M4w4Wv`?zWj=M7Nm2qMxD*Qf`Nh{io+z%4r3C`7a0"
    "9udjMkB^2ghlCLLPg<_kNu3IdSX_+Y~)*qXkG8`GcNw&-nwEznPVJAJ72gAE)$K$<$@nn9*R?)P5fWDtd$q~BCS^"
    "vS(l8#ojbip_Yr3SOh0c~w8c%3kv&?!!?Z5B3~?;eO-aO}*A;*^_#%@7mn^&}FJ4501<p&n&s`rtYI+rBtqtXss~"
    "ZqeHX=S(_;KXd~E_n&>hubm(eo^-_zg(9`?wqf5kxAh?F2Kts2*pCP;0nMULadME2v*L_ky%ZHHU0vZ%CODPT@Qb"
    "6mR3P^|>2!}x4wPnVnS3pRWM%N|!D&;)Ns$^DfE7G<*B}~_wWR_9`$QS}BcMMigYYS6I<6FsML5gmYL0oW=ELv^n"
    "%vRUb^(<q@x=JbA-(rC1au5D4TdEmX)58n??d;_EK*IPA8x=b92CaIfh{0$_8}hX&;NA@GM?0XbV*UsB#m~7eqSZ"
    "kC=KZAG_my3Du#yrr6HpcTxg9jK+P~gQ-9_mVWfp(;f-i;TGN@!TH_oYN)p`MG)Uf#7AK(uDVYE|3D{Zy}Um9PNl"
    "0Vc7=~1)0y_M^j{5Fn9g?+!^rvqJ3ZS0<~m105pkYK$+jTh1FLW%+*9e;-y@~}^t*GH4W?t&%!<pvADnTC!N;bbE"
    "Q9c@s+JM$+6aCDTZj0SQ?L2r&E>i8HgoEcyq*eI6kXthu)JSdby)<>@bKQ^FP4#o>HP7;JQ6Cs+H1w6n$()W(fe>"
    "y#Rf4D#1dw)3odH7dn6FR?tIR9yUe)9A1*t=x^Xz#<paJ+wVFdUx*u4+FOT63~F6*NILatuDvl;Y{`K)c<RwnE4-"
    "Z#%T)Xl`Kd#6SZt-b3Ly?{@iOCtDUa({^{mmCmgefoaR>N5^Wl?N_1{13X__Ezn(1&%r+ui~bPE+A2BkX-ggWF<-"
    "YkIBcQ%lQzcogki1c(Ru?NAQMrY9H>76*Lbd)0d<nZ3<gV%cJ6oGx|TgwH`)(~Phd!5*8Q6-@=er>s$9vyT?Y(TD"
    "0QJ%F4CmJY@U`s^Kj&ffi+(}JcO-OHRS<x_aAMb?!r$LPAr5~KcK^xddY?|EhVlje8~1Ksp~_{8J#Dbw!FnUFl!)"
    "yoAEdg_}`1ym(1RV^T2OZR|mAgIj{!QTC~CI;Ueq$8j%Rwor9)fA|tj7Dntasg|>mRa=VlO3j5C7=5HM^O&gn67H"
    "+%VG1vZVYyrB^EoV0pLT&tJJezP3*sYE0Lz5tO2^3JTPJxZX7}%t>!`&GIZ>!a3ADp?3FT}ssUuKikXur5K#zH}("
    "g(=RC2UviN$3Z9UJ3B%1*jG}?z#Ev;zA^lVgXq*zvN`JKkRU{1D~TMBgl-I7B|wD+1p|M4a8tSCpGvR5U3ZLFJ>Q"
    "g9X|`1pWiP*qb)~6+fQ-Ue2~1<Bs1uVFOT|=ZqMBOYJi2tvhXtNY&mGkIz*=~kl4;MPui(zBQgJlEP+td!1RsEV8"
    "ONiswuAx(<Q#ZCDRy2BD|V0QL1nD=JOh1y=OKL>u;5JsxcckdkG=*MfUO!&mcZFj$J^~gByhi$gdK<6$0j@33=?`"
    "Q2;Nd<J6{B4e8-pXm+j#5nvi-6jeYFd>g4NeYV^{ZBTZIqZkaEtx`yJ)@>abo1Ne_Wp{sbH8rB2ppF!E(An0}`+O"
    "|f+tKD=~J<G>$n-65wh0rl~>gY-qErROCK{~e%4hgFKcu@%TqPzLCxnLVK#RW~=C=z@X`#$rNa|goHwTl_rwyw)y"
    "@1>CLGgh~Fs{soO+{$&kFA!zIbLdvCJN%Kzf3Kwt6I%!vUW73%?T4D~ZC%IMI)}H^RBoHz-TGY_`C`B$J7BL!>Zt"
    "lUP{#?p;ZEoXA5XYh_jp6ToT}Nv=V_*Ijf+Echc~}TIY!g0PKTl(Rvk=Km)pE*MmyZZ({V%u*uwCkLfh(yA+6yeT"
    "GjmhG-3nwN2g)v2Kq1m3cYFv*4lPgg!!REyItE}of<X!wH){>`Keha80zgJhnP|ETVjTRC~7YC_dBfkJXq1r&Zwb"
    "^l*17Q746?%08`un{O><36!Cup><8Cub2oe<-6{Y8vd8{O%^2P3shFbaa>se{GZ4m${#Td3ql~`^%80Xu(sy9Zpo"
    "cQ@bn<2P<kl|ypMl~9+6>@v`rQrORfmQcWpiHIEXlz@yk_u9?HmdK&;u51ZXD>1eb1x)QK29kZr6b%H2~1R)f<P#"
    "8-2*{$qhWVZTu}0*qiP=sJ+Ce4z6GoXT?fIZ6gIMV>C=JNSwg#uOrz$8u@nv4L4iT{hI#V7(S&na?9|x(m$S8Izr"
    "78Pmu@LHDhxen23?lG|7a!L2x1#jwzu%O8#Fg09PUoJ$_EPoU&xy)O^zt+Hi{om+;n{3YFAj?V6wZG*~G>&L5gW+"
    "J4~)<aC=~WBR!5O+);#NJvrS7Bsvnow6^%se{^au;l+=n?c^rY^}6H&|?kicMr7S4h`MGf<Lez0$2Oe{_(qhP2U9"
    ">70s>-GxJY$UuaA9+0KjY<!u-XejE>`rOHZr=qIhUhkopaVPFgHg#)djtB=?m)beKJI4pB&sIAr-I(9&4m%~^uKW"
    "EGX*sg!q?`ZJ<1~j<30baWh7_5K!9ScV98-#l<iwrE%MJlOukKpgfSRL&=gkfR>C;Khfm~lvpPOfUtSI_Dg2=}31"
    "M`{0Gg?P<^b>~@s|Jwk(NaEolyhMDnhuJ(1&^tuxpd@20jyOqFeMgl8$>l_gB)*ov2Z{a$Xs*MgQ-gDvaVLo9;*h"
    ";4p8MhS?Bw)+8KC=n9Ov(GoWI9${vOBqa&er2w6?}JEIR0|L0zv2tf|}#CWrR%|B9$e%4cq|KD2*y*xmqB(8W(gD"
    "11%p*+9ih1p}IQ{ht;PxN&?vz|XwI-y<BbcJ%u(f59+6U#xs~$R5KS_6DynnGk8xBVdlhKaa(%eY~Und;H(;h|ll"
    "wf4|57{T~1Kj~@S5<1u!SB4X(6+APNw@0y{)YMmfIEKr#<b6XqP#y(_eaw`>?J@d!thj*xs1qhxhN^gk@HxoadpT"
    "8HAS9fn-&2FOV6=RS9AWcS@%;H6!06$xVBvh&3N29J$SUo`A+9+F#`b*HYqpWpzbo8zxj^2s0Y8fYahp%OKWxFR%"
    "5d%Zk@u(D&3Gv`gCSodQ(UM9wKrcoacY|xhfmPa_<=Itot@?ulaw?;^)Y?)hg^jRiLa{zv+7*+@*~u@%)8XNd$K$"
    ";phsWpRqoa4@zwDh2#~)6QCKEAQe)amzH|hamGP$X$MgP?+?9xqMR{b|`zWMr_S9fnFlU{R+?@kVe!RG#JC9|(56"
    "VaMXdcEFw_#eal59cSR`i3Y?qO!fAWyXn2+c_55iBd6@Q6Y=BVwy(TEecnAHgT+uVChh?JhfyxIJiWLjDz?k7eOe"
    "$gq1Uy?12h+iWPDulecj7D6<*+MIpPYnktmQ6VY`9ThFcyIF(m96b{JN)eQtwfLfnGMTqQ$iH6H{`E+*RMi3R|ev"
    "Fkv@KPN}OVuT!QcQtN4G|aoYP&*iW<39K@Yp)Yin<jn$l>uXho>jU?}o?cHM(P?1VGJ^=8dOKgz#m!IUc#j-ARvJ"
    "Z0F#&N7=#fhrJI+=ej$1LN;!ESgz_0d>CGi8ykKa|FU;<crZRY-#h<shTKm(p4W(r8qf#Jdo(`#>)HA6-T3|K$-D"
    "RG_SpS3Ut(}iB+k@YVG9_@og=W(s1S#ME4fe~Vi|A6I$ttz7VSFNqUzuu?T{^jfh$}`W1TMx0o?0wJBVutAi~<QC"
    "&x#B1um~7yH2G5o)wW#p_(PQGeDpa423Q4<^^(|iz_(R$_}-_H8-(1mMRj_7tR3vw>3WhZHA{KcDZ3BJi{t2kg!|"
    "jv)l19!xXB%_!CwPqmokDGEM*75!U6Z6jxtd{0TtH?E25JNbRPxypq&Xd4uwVE_>*SAFxUlgr&$VDQ~C>FE<T>Qa"
    "zdbB>rm&EI!p*H4Z-2s1mnQE=oa{L|E%0ngUjkRHZ0nUck|hr}0}VjJiS4V%cklzOT&FJ2|E^vV}&CwI9ROoTsGr"
    "wLsF0mqps4qo5<AMKT6u-Gm@ngq@avaF{t!UJWdgP1ac-+55uZfbCvEDDr6Mm9{eIjB?D1tscYz!BUn158viaU#7"
    "TCI5I#}a9FxDjD{Z1tsZFP5>AifvuY~s;CruBF^Hh|YO$_v04aIQePwYIZ}eYz2f*_^S6_(ZTx7BWq0?tRM5rUPF"
    "2z*@hiwMbd{@XTB~E2DyJ3_G)I$O<MO4}CS=@d=AKDQsto$2gVwn}xKnlttDZgS3B*|C+hI~6z6VR&X>&)hu0>7R"
    "8_N$@(NK6LLeGvaD?x7zK&yMyE|L8Fw1TOM%@jAuRuZCZ5jWk_^08X{y!?9rVh990#r6$;djqwp`+3tj*w{39E4@"
    "moe05nsDOv0F%I=IGQl(x(X!sN@i<W+e!I*rsXvIN7tWX^b(dHS-W=z{y=D$PMCc!e&edAugY3?Bi<J#XvLj%pge"
    "<i8Eh4BwJ#2hMXjN9Ai-AYs~T29|DQ1Pg^8u%9EnY4;pq9#C~4Ae(346`|G-riLfKrR^=n#x8VGO;QC$JIL!k+W8"
    "CGeBz$(d@z!|T;v%Z#-5F0Z5)s*C{1dp031M&LO8$}^msX6lr0#wc26SnaI4)>T^sPfdejH}uX7?&P62kQM~WXf*"
    "S~uGy2dNZWX&y}9D**C$)&VG_nd{zW^n`R2VsvdMmw{cJek3iUS7PuywGzDpF#D+8KRI%y&~l&ER#cPmXusW!S2z"
    "WLp1=+fEX232M!f6Kr-vzRf7J6dvF!fHwAz7pkIS($Q2cUfZaEU7-zBg(}2FMjnFRugt~)Nppp)+5+xaW@on{7KM"
    "41s$D{~-x}eAR@wxvj-dt{=A%qqJEQFhTwu(xQcnWpPmJ+co7IIn4Bx&~q|MvM-oPorbI6=G^5L5)iy*J^XTM6j#"
    "C?^OUY;Vs@$v-DqMXh<X<FMzMc-#z3WAj>zUuNSposUWXXxTMQI(9vij`-3SbYdXheD%8b8b`;1861Uwue?QVp0p"
    "NZ?WLKja@(A-ZttM-g~vWv9b%8q2V0HG3q$`{*QqjblV`AhCllJilZn=^EbD=tne*E?0jCCJx0Ix4Ky*r3jq_Voy"
    "`!d(u>fpT%iNhOXZb?1_r%%@?Bu#2<5Xff$ovW&ha@cUJ`;VdW;(<>+7Um?HUFhoLOak0dT6MZESki?IUyZ=)N{k"
    "*Sa_Nd4UG3~KvjZz)p^RNRJkrIIVU?rOUS-(5sHV-Bdsh;S=8Ea>sR6^^s&Aa`~{V!Mx)G<5(rB6OqJ~>^@z7Z*x"
    "RoKUr?}f=Ny{g)tHYd_V{U+4Wky;#RMz(7uHY*$38$rZ(#4Tmamk<bFhwp=?uEWtiC0gaM31?1hVla-%JQWCj(d1"
    "hTp>jTiWef-3KVP8;_%+N}$F}Ik<od?w}av#kx0-M?05Iy`eD*B{;$n+nTiz&Yr;w)1{Zev_(t2(`6l05Zetoi+2"
    "CUQ8mtsF@iB;24co2#drZn<;@uCrDn4vMO|Vu_ZsReph^uc{I^DoY0x6itu@k&J+(PjPgi@Mt_7QaFzOfmZ(qN@+"
    "@jcpIdhCCvgHpx4ncvsH%Ciw64!lUKya$gO3EdpQGiV;&Fqmy&db`y^%|BWRnwrc!vE5X^V{;dC|;qL7Ecn+5ANY"
    "Xg^^k<{sjkb3|cI1`&I&_8LGioZP3(ac}$T@%j&B8N4-t$2j~?YdWL!7-Ftt%_o;UVF*F6HcOG^_PY=OJ1^Wt=hA"
    "@wktmT!=a?3#}^~jXhDv^`BtXk!|?7_VkZ~7QRhyge%RsnYfe4{$x>LQ?nz=O++*O%=MHhb{~TS+DMsBDWri#H}7"
    "(S48C^a{z97>@z18js2AJs!gwjmM)MRmTXG$um5HhM$tEg>T&6%K56}lx&~tfh2${DXU~Au98n+vti9+h|o8{)90"
    "1FY<4^Sqx*##ygv$=^b6qnh@>f&`x2Psa}mZD0_A=O+I}OT&8(XL8Ti_7kBiYMqsHM;i?G4$d!kikAAAN3YxDh~J"
    "6xkhW_L0r%cgEwg)K03%iquLdPE`DT8o#wM{3Myhl@y2)0(K4k3p^J*cQW+ROK(k9{Y6njyQ8HL*7*oCrO_5lp-d"
    "T4h614HcL3#BPtx{NPZQL)F4~Gz>pgF7IZN&%K>`R1^J3RUe27>Krb$0QAE{^EJSq^WpufY_kfjLNr+i4WY13X2&"
    "#VHbpn^LiST(kyVY=mf=&vjIkS|uV6*K1u7EyK0kwm3K2s$P%f$b|n&~q23bVh5Z~CH)Qi*Pf<Qjsv08w_d)KzpV"
    "#dTESMT;VjW)*M)UPJo;@shrpjj}x`f>tHjtP*nxk|inUwEZUKav_VmgpyS!9kIaOsTzTeSuE2eyB=k&Nu1BhSM;"
    "%b_0{XIzU#jJWB03n>B5%$moC0WHz~WNTtr1w$u2yhYdv5dPe95}&dgU;GP`ZHCmel3i=d<c#d#htA<UlxQ=$~~U"
    "`86@f>B0Sc=vj5)D!17QdFxPLR%2I<S@V@UtZscXp}+N*>wRP5PXP4LKA#*fG#0~3j!}7+C{w>N7R5#iy<rg`zX^"
    "FU|G8b<W+F*B6J()%c8mwO57yWL|MrN&eBOHy$N1`>fD-ujfJB-&a;`Ev_+f)0SpDoh!w<)xKnm^@^O?YExCg=O$"
    "$=GN7)<jjU&?wiTx-AQNHe8Vf89rYO5O<sacfeSpxBab`d-XO-WKJ!#>$R9qyeE4<_)Y2pJbqdDC4bS)8xL3>|f*"
    "m02O_l_|;yYk*CcmB?~zjO%V<zXamOG8Xvq=J6BG%j}J^uh7XKi+EX}oj_eDC&F4*LIU89<x(NQl{QN(X9@VrJ0e"
    "eG^cE#W35|W-6B_l#MF8t|ktVQ<^e$W7NIbo8U4Z0)F@p%jZ+c>{%IENs;A2UnWX?^gS62_F#0(e*iqAbe`Pi{Wm"
    "ktoz{uI<t%RMiW>m&pH@fOy@i52nFqsDlBz>c3lXy~^+)X_N#7*#S@7<@28N8DE2QHC7};~ZgkGP#1c!so<Tek{6"
    "@>6)_eaOiE;pX@uB7nGTiaO(bXu*4{X9cf0DqJCjrQJqJOR8807_~aawfxayc1nm1b2btQ9uCpAsNh?z8Hpx1WGO"
    "q@kTsk*g|FErOhZJX3UdUbEwIo5i0^;WBS!X|gphYgGGR;>i>Z;>zJXirNa`R;c1g)cN9#ylO(GD~RJgtboP6~M?"
    "3y5(W+p${Zs}g!K>A>A(5=(kE*9YA#N7-~4UrX>6@&lu?zRyKe!kQTEMD$W!NSsTqk{JzdjuF=&mC{tEBAS+nZIc"
    "7H{fyvRylR%GoYhqJqUlUsx*w%fS+tR0R)5u@isO9c)iRq^d2WCX&_$CdeG%#c4?;0}&HDQcY>JLJ&Edc~!?o1Vn"
    "iFluZQ46&tCI2`qg#2vi`4PFeN?jCY!6t>kkbIt2e%ZhbfAn#u7DZ1%25vKV&(f$Q6!SJdRqLCNeq!m8DmREG%1n"
    "=CBbm5WwCt}u*|o*NelGjPkZO0g(b_ieF@tG-XWRYkPW0hU{Gq=ek&${enn}X>9*OFypiIklaHbmX^Gphwj|_7$U"
    ">C)vY4qeq205`Sd9~R3iyvqU3&60S#|1jDD(~Mf?=*S0z}Zg3Hs`Pr|LnD<<*s(Rb$AB>04Fab#f5=AJ)T<Fp2}c"
    "hb}JcIa7=Bvg52BZtHTZMTe)#VI}9ziUXyCMhV0r4GGGA7Dl*LbJ7U|(%czQYR4N;w2SG@#TWV%`EO!xTjQVQE!B"
    "jCFRzv*{>5s^m~}C3EMKYC{b59lK`+fMuR<uH@xoYEQ9{v02tv|}Za2;jyn@MUD)3!TgARX3N!a52kMR|5i1h%k)"
    "_~H#f>9=mYHjc(9!djl2HUSAN_bhF;{wCKu&0{kLb*4Q@PwYG15PpeVwq_rYs~6bD=)75jzq-1p%KVy*jax=R6<="
    "Hj<o75cXc*U>S}r$HMOU1#Q14mIzZAOA~9ik65YzNYO0)wB42_0A{m7G5z7}e4^WOo@DvcAx(BNyBMG;^cSf2VC8"
    ";PQ#pp~(lEJsrCZZ>yZCYxrq}xTV1=e`G`PCIBJrNftHT2`&`LGW^@=#-5N+nkLGL3~yP$4a#4zR0mDqUOQZ&6m#"
    "xlf_vsVqx)&w_S$WCl>_y4Ze($`9;G1@of<2^6BB7K$XJL~BHtP#Z@Y$c}-6X3GL8NF$0(15M(N-wgE?6cDne<G^"
    "X7sV?!H0sRo>6Y1~IhDXEwa|F70Q;Qkd3$W074GV%y9I!aZzOjz7o2XRtM%II}KO&R%nH$RxJB?w*38W#2<w6^Ws"
    "fweRuEk`mb!4?aCahAbcS6+%bqP*TBXe;I<<F0YAE_yv5jFpybh+ml9aJkoOY-8n7f*Y$Jj+Ny<BWOfRGOsW6ObK"
    "_sNCL}!smWCJ$a`ssZ!X^+R@I@@P~8pZzqSxBDAN(Di$ZlViou3@Ez;p05IHM5__$E{AqYPgv*my9G;2e4@XDh<n"
    "&;8D*p0U=vux?v^%KXyOP!HCQ8$m3(K%fVfajAoCu*6`RW3&EqE~ihH<6Cz6ZMLd{tgrlB_mQo8%Y?T6!`kO&C@3"
    "G9=%&S&a?WwmL?^8u@H<n^z{<+)uK%!N!83)Z&(`qG}~oE$)i&6-@jrlR3olMc@L%QoUtKFRjk~gu?WRNvO?Ggg)"
    "OBG+FtUv%PmiYbf5ry^IB6V;~GlfKp<CaR4eeR7*}Cbo)3!qy{ctX32jo<%YxISJ+~_ALxsYSmZs@XYfx)cj<`8x"
    "-TlP`6h1%ZQQIcwok2w2!|-eB8L_hdCzH?TA&RbXu`Z9%-qSbh<ZdZ;JtiMOrQgd1G8Fca5`f5pHNAWyKONLySzJ"
    "gy%wG>RLtF;Yx7ZQ<IFJ#ow|QlU5RraxWtH(4bL%a!fU~1HFL!s{a_0{o__?I#z|Zkc^yxsS3&Zwx03b<fI1UEtb"
    "1DAOql1QBC8gVL)P!2Qp^)f69WtH8qg1|%pK)9AE{F!w<#e=U}CR;3B*uTvdF~5w#NbQ-R1Y3Saw%AzRHU+?b0OA"
    "CR!vcOQl_C)stzn+4`k7K`a>G1QIL(OGZ(kJXT4D=*`LT(AKlqMKhsU8pFs;+8t41vb{AfoLM;qs|zq_%s`sUh&4"
    "@`BegtJI{$By1?US*sRV*I$!2+0Lee|{8>DMGID!JZ6y05SmSW@>1UABuiWaC`B}p`pU#Ohv+acy`zAP)&1_jX0h"
    "XmwP<zvDs2M$OnXtOf|#jd-W{B6B=eBg=&UCAA!f?BsI8NPR1t1bOwN9`OI1$ic0^}GSvakN)4x)S!3VMw#--OSd"
    "4^Lng7n$Xs|M%z=F{%WiBS;pX2gTVCqCM%?p2onUWr_t;-h@Ozo<nZ|H@L*`16lmluWabzJtslA{{-yh7w*+Tq8}"
    ">vYy9h0!HV#KIDxvzw#e6vx<Q=oqhyuVNHMiq<daGhd_%jilMyzI7J`GkS^88j20iar8^$=||B$u)l98D7R3`SUu"
    "VcVV_H*DTK^6@F5D2<vmZ*Y^kvj!u@%2Z0A55Sb?G|%<lg{;8Oo~Oxd?YsvA1gKnU`yHTx3l1U0a;!?<WTnB@60-"
    "&k)(&dGhbYdbF{xVM8&@$SX8d}{f>L`-M`>})_1X6OhW%*31f1{+_uPS)>%dWD^~NPn@^255vN^9?kNeTX+)%i|j"
    "6_o%1V*hI%N!7VG=QL84M#cxjZXm*`x<hi2X9jb!LN#tXH}9dExsX*TMX)3#2Hb2;TA(_2F_Y6_Gp+Fw?J$ry#t%"
    "4PD)ho`4_^LM|~DXzAS>!l#Y^bHTkDB0gh%_Wi_eS5y^Zm;{>ht8Uab7Pk8hp+l_$)Oi(J}lwof$_yhrid5)Vhy3"
    "R!lg`M*604)v($F|!R04+Dsom4SDO78&?TN8uPtXiUbESeEIVz&h{-pF8(;t}*!V=z$Y#ftxdBp4-?5r47U(k3gz"
    "z=*yeECKFROu8WKNX65GF-H+a+MeT~2Ux=#64*5uT+n{z5!ibW)CG2>J}*Z*r~-*HpG%w#Cu_T6J{ppJ=#q|R=$p"
    "(a_GvB)n9<sWpm)NISn)+}WSSxuO)FMpYO5+BE_^d;ut|1!!fW7t4&AZD6cp7ee+1^lz{SR?F;JVjXTA%y4h|1<E"
    "xBd_VUl@jT?L;47a8Y>xzv2uP%y>2UVqgPtLghxtWE`f4K|{*rvZBzTfVjiP{uWB16p1-^HXx9Av+-fz(nulGh`@"
    "xKP(xFp^q4y__)mEnp|o1KmI^8=K?B78E~Qy8iu&LC-Qbn5*e_0Z@_2#5=Ud1uY#%#7wb!_&(WKD4SG}CwJj{wvS"
    "pkyW!v_!)E>wB`(u`R$M%)ko#{IsaPC+iEe%eB5BmvEmzn2bu=UR?7Q>9dycIbp|0{@u<G5L4Q}bbD!|F-ay-Jho"
    "n~H&T@c+O`GhM^U14q;c2r~U6G6f~swZ;l2ryq`w508JGz{BZD;40^cFdVy>^aMH#*?93mPUY)Pf!_@5a}^ZD&D-"
    "xvj*;tJhmaZmT>vWB9RWVPZYm?pl#PYP9=d>A%omk<6Ar?{;Zose7-SM<v2rfM^B7p2O6?+rJLFq_X?6+`d&ym%#"
    "HE-=*%Ew-%R(QYh&L2UPGzV$&q3$m)LS~<R~oIsV_z#AiddKr&&mGDyZ1*!K%+Zi@|UBN{h#qqXm|3%-r*6z)QFc"
    "T%1e%GqRF{lN(c;Lq?Sl6iPBQd9RY<Ic#d*#G0hzN$;B(aZ3o~8h!Ztf8m+9sz>oUq@f-)zKpG^Xfe(DvdEaU6OD"
    "eXhymSfE$4$Rs|9g~@UVCn4R+vyL474J~xzJ~(EsW3>4sl?I#_tdH@#8)J662?00)DfBGeZG-2hvFLYJH1}WFfmO"
    "MM4AQrTRx1D~(<-ozqV@Jz;~=P#Z)uY_6(MH`MX`q2x$QfvBH7-rR)d#d7>3xiz1X93&l_ui9J{QP!({QJ<9!5z+"
    "vBuHAG!4j72yxBx*CL&SLsH5@T^fI=`){zCi;#NNd^mEni(hi|%XULcVVlt?tvOmv$h9x3>5EYm7#j9`Np5<5ljf"
    "Iq)Lz#C(!>Mc-l88dfu@CG<8`07m3Vp>+Sah9*P3aNWXDL@_d2Z{xxejM(d4T0rEjYeypWJ^e%c=K(0l)c;gkMZg"
    "7{Pb`L9Ee|AS`YXJ#yE%LD!-LkE1vfC2ziMEydH{ZrHfGFJthPJ{Ri_r%PZLHU~p%ZEW|`96N~i(Jpo#)AfK%Y;{"
    "}(kIs-o*9-rv|5belU&pjS~RD?jnM1oY&t%UJ|gc=mo3siM+adyDg2Uvhe^pk9sE@NeqBSSAd{y&#xrOFzWXvlWE"
    ";##5~jouZQ@GyMh8aF7zuFx?3&dwHwI1-iT2A}RAzZG!hB$o3<j%*SzV%>a|$)dZ=REKp!T6H5@`0f;lPEA3yE-F"
    "xP#Ps=M^(Khf@T_3835_k#PHOLLp2phSZ9xM#0QgL+e>S!Zp(`mWl-4){K_zR-tBi&^pde5YCovF@yDJWl&xWVx;"
    "_&$Vgqov;S+>y1RB~|~Rc-Oh-qDBQnP}~@M52Yf+Y#TpbuL=G$6D=PQsxv#(`p-+go4Cj)CSzwUK*7ZIWbi%n=C5"
    "6$N{}Q@)^9sGAv3kX6#+n!LMY&216ld$s$2}fvgEa9rzQlCK-nyZ+qU4Y6A?^_trQj@qh#jaQ~FoZfz8L{(%0mPY"
    "czRf&R<BOQ9q5uk{ObasdD7xLJB~V9TlA@$jRacBdzDpr^;35IkSvY0t7yTQ;~IPkW0ca5b3BNX<ru2ebOyWPG(S"
    "Rd}?+nOk<51xt9h;;F?x)+<SC12&Z;wy4N7mcU~LKj{w-t`?wJuFSGnNx7f}TYAeQ%U6BtgmV{2Ahk=UeYxQ<AWY"
    "U|ttrHm3*XI`T;q-s0^YJE09%?cO(kYgFggAcH76R*ZM8wAGJD$At0;<N<9_G5C+`pT&WD=fO`HwS**+bJ-Q(fM-"
    "44mIF?I;v{ln2wNBHHUR0tAhyN*i<Nq=7aLPxc@`%gWq(cKO<+72{Iu2S8f{iD6ZcM$skZc%E11a~=(Dj*8`KF|h"
    "S+xp&$zB1DaUemTX9iD$UMGH8oE9I>WpbkrPnY*n&o#2F8#05zO$ojZSh!L+u8@^R@yn4|LUYvtz11_*y^edk<Zz"
    "vkHawQk;zA}w@yT^Kp*+EG*%|Cft2M>2Ah5|PSiy=)6=k7hNgTcV67TQiE($-#fJGf6TXIencgyZ6&C3Sc#T53tE"
    "wdI{(s#CrfJrGdy&XIY~4%5TI@dlUQ$HKa5qwOA0>`4a<64kL;x-7vyW`zvNYrweb2_(`5*HadEOIdZ;B#h!NkYr"
    "MwWvw)V3PoxShN&_G_JoB<uh$daj)lRUkbZ-a6%oSL$~-hFMi7i9_A()(B8By>O1hzI2?eLpzd2O|2JSsFEp#jxs"
    "mL+cN<g$gpA#b0+5wh&OiYYoP+~ju5pN+t2R~0`n#emD>#)ByisG1a!%4@YAHV#Pj4Y6l5N6W*@=F{b3LuM8OT!e"
    "%qTQV(#cT=PW2KrwrsPVWYZ}0Dj&EL@*h_aOvs4~fh#am8_w2(^N&=sknfB{(RtYc$W7-YOlGZ0>LBTZi&f+GDwH"
    "C{|vWma~A6BL81v>(VuVaL8mSW&yYZ8*%S-zUI5&X8v^f)EM>QkTmY?1gfPB4r-tG;Bjf?SMvn%*F}JGkm#yHS0O"
    "2x(Y&TGIsh-)#k()aw)iRzIn$nsR}^>&B4lRzxW#1%K03HWsA*nh;G`6a-l+oe{<fmoHKQpv|QrQqpd5G7isRx(E"
    "#3MX;twAX~zU1jir0*~L(dRi6w%XNBP~VdkcqTVB1ealeF>{v``!vqry+viM73Y@rtUD=m`*%|HMs6HdIwlL*|tD"
    "#XKHGaRvtHk>w)-1mijs%ij3s6FUaY{Q%x^K81Tx~fxG81AEB=_I2p0yI^XJi)p!Y?ta~LaPLZQ&~_7LPYGDxg8<"
    "yGpUS0y^54#4aOz(I}$&f4$pq_-lN;am^ZH3sK*B7UMkTsK!d{TFIrG6G^>A$LY9&@5mfh++-#MLiK5zQwI{D8F;"
    "sU>C4>dG+KlLvFoEu)e?3tJ3^a)C1QSIoI#Y>i%~sz@6|m15i?cRb1srahN&=2{Sc0hlzIwqtDD+3bR*4uo`4<=@"
    "h|ACo8l&NQKd6WVuKR%Ha|#KlBexf<fLOERyu%wf2hAub(QDL+KMah_-ELfNP&tz^l9{V}A5?%Oovo4XmqGrjT-?"
    "{5|4<*J)eRIM+~a&^@-RTk`*O-7RvO}zSc0BNa!>OqQ2mSz#VY+dpaBMD@3GRA`}lS!n$VcR!ixG0H%?TBQI}d-)"
    "Kg-O?p8;rWpy^5rFu#?U2L6SHAv#oJN_&XcEtCqqv4jpYK~F74-ZQ5&jK;Wr(1;zW(h%$PPh){ODYB;C+l^U5Let"
    "V;j<Hr+<b*cHz0#8Or&sx9W@CG1k3QY7qgOI;U`ieQ8(o%mMpIbwc{J@_NGOY&2DJySHkEF99D#94NYhv@l6?~OQ"
    "@y`N?@l!){J2$afJeA=^q~;=Sk<Im@O;BM#F5MYjZ0*#J9V@@6;_`{I+iK^4T<2^ZosH_WFiDLZ-Ynm_n`BEd1}="
    "mf3G!!TjQM8ozGD12CGB?6{U=X@GIxdIDO|t{3GERV7y@V1PbVx94C4^$YQ>I=^k(<{%IJ=))S#EUsSVSAuAZe1$"
    "FsI04^0xl*uF4OnvG+`#T_s^5zThf)&Ql<kWsqlg09nt-jBRMo`sKJ*?V+}o&1@Un}NiVDf0VvFssdmHQd+7OI;R"
    "REA7AEys;vKLgJMmv48T>M=QKjI$`0ir&BMzfZ)tv=`i9;)jGxlpR=Q@{)4Z+G6MZ!y|8LL2X*;#T=sq&{lJ!O8K"
    "k1L#3=wN{Q9iZ}s@?da@=TERrxG$;a!qk-3}T7yZo?sH6#K64Q7wIWgGQ7oA*PIkd;>;6%DaVdZ%?DEl>$PhEqH2"
    "_YtQJQD6tFB+jqDzV#*rXb106>H<k)?oQZkSn<Nv(Vl2tuK-RZqJQX<{bYcXc}a_Ya4s!vg_zY*%>^cj3&$_<vQT"
    "6JB_hln|ndrV+>eu%fH%Z8k!0lZ7&Z$YjQGMZ{>zv2tV(QD_IxCmiJS9P@Q%x@a(m*<3ACo=)KTp%p7*Lykjd@UB"
    "7#8J%FRKxMMqynrfupFul4;YLp)FP<zwrj}N!h#GyJ0UygEf#T)bd5djU#GlD2^oVAFcaRLi49el^M3hR-Dy8i}N"
    "|Yi%6fJIz2S<mY(SlD`(YjQd2uXafei}R%cyb`29F0$vGi%L=nF1m-q>X2-b4WZb6Nqe_O7PVJKUs;zeo>J^rv^A"
    "WGGrlAK!LKCN%>M?e~#isr1UXPI57#R;4lmXbG)Qf@kdlSTX!HMFy<x3-3z;MZG~g<(&F_`&hI#<&^zC7e$-OjR)"
    ")g+-9OZgN?Y_i-K>OM9V-0Fr)h>scUmMHn=)ipzhi+k3!Jl|>zmAOGGCFlB4orp#a4MSeHu=L-RC>3@b;}#QBPgR"
    "?_5p%@XSlnLxs~m?ale_-1)1jV=fS3b_Xd`u%g^^6ZD{a)9F7H4^1i-q7WeSaanY`WSmhVL#_lkn`d6&h(F%cpz&"
    "UK)|nO(@DwA80PD-px!P-Jai42FW!Id%5jg-HiD5wSA}tjO)PrLu+@v;tna{wLLNB3?LJEqe-&2B#!(L|Qg|ISap"
    "n+Lb$!lQW@pQ;BzWLT#t*ghvyEQ1Wo=5TXbx@^m+GuD{<?O46HL8)P7;USI9mW!(NC9d`Vh4zp#QMeu!@UC$T|v;"
    "170{*i#$Q0+Oc)~JQxj+=)Zlnpl+iqG4TAw|OU>XZ1uX)zD>W<~C*>?z082KO4!0oUzFNSFYoa@s^SoH=zDzh>OC"
    "^HolbKf(B&Q-g&YA>eL>t<esTA11Di<+mF|?sEPK1)hh^@z09Z~i%VBI?V_oD=pwV^a^7l;;x#JrSh-4;qOndL<x"
    "5zn_hR8oflvBnNQ{RufHP`~PW76D5cEbOI8Z3tE3N=~I3DoS5-6VZSR4i|l?Guk`kV6bD_O9}=wl-9`Ou_)wSk}r"
    "XRh#ZqDMUH}2Q7Hy$6ERQXE{2uOSlmR4J;)%ziY<yyt^5j*UQ}uFyCBl9m!XD%f~zqAZdb*6OsC18?A6|{L#_6;|"
    "2z<H8o^lMM<dm*^rB20Ftrg#ZMx7$z}%}i_1*|Cc4_Il3_wi0<-34n*wC^iqD=do!>^d(sjT3m5mOyyT0z3p-%+F"
    "b{$-I#t%iNSjgqyELe+?bZHSU@Sc#8b6$a_*dc8F?nn__p<IZb_k`S2%qPc}2=;z6V-xBn@GN|9Z>Ej=Y2jWS|V>"
    "m#`SY%j_4kSLO!m1XYJ+Q^Pw8iXmh-4|{p*JaA7!e#eA~noF9M@p0BO^2@hQv>D*Vv`Jh87Ud1fIGW`++ZnqBH0g"
    "eU?6mF-eX-Nc9V<5Kj5RN+3lCH->2HBf|dC`noAxvnfxajItOaj)6<pNtZyjisV|BRd)eyD$J3?dPYD5$k9T&IA|"
    "fT0pPN@!MYAiGV*yT6Z|1B^`C{*f0hymh4aGv$UF%8<8sPYhW-j-6t0rgGy;*S`onUW#G48(5yG@ypgF+Yz}Xsl{"
    "e?IOz7iRW_lF1K4VSt=1%uvzs-=iM%gXw2cz{X`W?m4>2^B>6f>5D2DWhphrU&gyP*L9^5gL3;PvYdGiq&O39~hf"
    "a-a>}Lc>m=1eDCmhcsf2jK0H^%q&s?aJ5WQR!(+i!W|KJ_o}2*DYKwoSVxU%81t^;`yGc^GJTH4!km=sWatHkFK&"
    "U#rdD$yv1&sNNvUQ>At?;)=-1_d@Z@>P=`F2_V7EaeYe7>pl)Dai{7o(l-AsIW}ztF$0l5DZWYF^hxH193eRPtqY"
    "lcci#qJM%ib=>bOAZodRrLW62=4EdcCDkH{TlktC_~zsB$xnO7KN=WH-DrvRyzGr(>RPYi0&a$y9alO2gf);=O-2"
    "|#I^Eu=xPIs=GR3rB_g=%dy3IFV!9bb4X0g}cK5Z#7Two3$M*$m1Q5E%J74zpWJF2z@8hqx$a#nyT!3Bc&=6nW;_"
    "pspuA>Ham%%3eyG1+fb3{dnbnJ?#KRe31EfYLYLjlcfmHyuta4wge^mj#}k9KgnW^9sDhfJP{D5+?=9i1k|t)5qX"
    "jAie`g4qavWB0+WE#A6=dJBc`wbGBG;C<Jo*6C`+YM%AyQVhyH`&B%#)xH_&3s!pjEcS~^#At9+q%A7d4sJtyiR~"
    "6HwDxzXdveT^Q5_$94966!NEeS;RRV-~_`Yel%cR!Ut1>|1FWjM<<FMC)>?GIQgEiaQ#qa9VwxRAZ8WtyVtXz3os"
    "Xy+p8{%x=O|Gn=1%cc3V_o_ecUVizn<xTX}x8L<IqV5%3aR1#m53v7m_yW-x_0rDoPtFeigN#IkuF_<dRPGtXlM&"
    "&OPuvZ5z3Y}!aYwuse^Sd29MoUGwss@E>YK0r2*0>X5x)8E+wr$wf9G5eHD720>2l>*{skB8Rxg-jh|dT<b187r)"
    "NrL%Jwpa&xI<X{IEymoQPMrouMWNA2B25e|IOV|-Jq=k>7~HvK3xMB4D`(E*j-ZOw5+iH{QJH0pFsZrsZ75y+C)E"
    "~OpN6f9HMPghu#(!jzSDGVg1-cc%cMqtTozMX33}it5>f^JMEy7?7UJ1kt+yH@VjY3;0PEYqEzkg68@>2^10SqUW"
    "|4QAUXYX{L{(V`Dh1twX6>6-95!xV_MCCEM98~UW|6=CdS@yBha4|{-w7Eo>pD5cj$`y``%&v@Zc7gnnerLooJc*"
    "HT<A#Q|&t{Up)A><Gkm<dRI49DdGBuJ<=axJ=GQw*MfyAzV@cf3pKbhy9O|Andy>;Z>?l=orm0ZPL{_@$x&7A!R!"
    "40ynfyGi$Q7yUoC;|Xh-}rs&qa0&o`}h??!&I41J{w_Rhg$4C41doffS{A+M581291Hw2SO2NipD_A}F9w7JDhfM"
    "gk=P3rFcI+E{H1f3&R}tn}7_Bx&Ldq`Q03w9HdL5!zd<ceTv9XO#7*q95rn5OX*vyZM4D2NC5oXwCN8=V#Lts8Rm"
    "*TQ6e<Mhix~qicvKnGX<9ZD*}$b%ZZ6Yxu$rh&V1m)=@$*a2Xd?rB*$iHrTvBemFP-HA}Db>(sB}LTDfg%Rn7(ec"
    "9}0p2w}%`8VHuV^{8`5KZ9X^AQ*=4{GkSWfu6h+b!n7ud&;;_|RxBL)VhkHps}QP`@C}ue*po7tPmT3JWM(!Cz<5"
    "q8k_aVz75~)ObM@$Ah!s`G>=U$1eG?;gV9$mPJynVKEP~yqn2YcTpsFNh-<1QNLx8#AO#xv%%M21+O5uV({HJ;gO"
    "y#mgV40@TVo8lC__*9G2GLyKnm6eG|U3l*Qn6|8?-kYQDG%z09j>zUUXLPL_i#?PPhmOyW+N{7nx281DO=a02g_t"
    "I<xiUdX`|fQGV|4eo1_=b;mq)qw1#4orRH%*(7Q)>s~3&`_zB4!GK#hoR>F5_)a2-t669=SOBO&))r)PPIq$H9BY"
    "Yd!Y7f`J_*{b88QX;S9C!J$yf`UnGmdzUb`y;N-)3{jwypuR0k1f;ph>W#Kd0N=YuNF{DM8vV_F0KsjHF)dbSL)#"
    "K=0EWMUA-T|t8QBg!|JIzuRcYzaDbNAS1m_jAOhyl;aCgwami8YebJ0MK{jK3iKUH#k-P|@*Ey+U3C*K5&oU$kSj"
    "J^W>Od_F!M?j5uPv~marz%cg1Ok}L4>Ic#vt$FmR^}1ump<5e=+A$vB-opVtKYTYFA056sJP%=^Iz_#Z(QWwW+08"
    "P$C5Qs{tTz-rJnnKx4gKczzkJu;_?p;M|5?3Ys7ro=5P}vq)ch>4TDZ`%__L1)Y&UEtAI{%@IDgi_fgP+`@|Jku;"
    "q}F9#74}ee{sA4*l8)v8y86L^_xf5NaF~38u+#gNZkrA_U5Z^6#LHk$;r`}n6^S=#S}x9csi%o7*Zffzj4YRS;bc"
    "g=12Bx<FB5x$RPu`frfDN=;vh*DoiY{^@3j@sUGp`ogM!8^Wo7^yYXe;(@j7jzg!FhG>k^$D@(s<dtk!9ZHF)7U5"
    "Lr8E$^B}6SBdSM6FQSj59PULHWB3mNfSdukeWzKEs-?4Oy1konGF%e<3EI=1wr0&=lUd1B3^?@fbRLNES0xBLrq9"
    "&a0m9mI#OUd^%Pr_6RV*;K@U~DAmwLX{tv#Nh`YGYP16*J^26c;h%?pvgX0I-H)TWEPeBRJ2QThIsf8=j|8ARSeD"
    "688SUzOUb#RRv}lD+GanXER_QF2QMO#L^N{0RW_fm%6mtszU{}?>%|bvZIATm(2+;nOMh<=@6OBG!^xXsGvfYcZf"
    ";-WfLH%uHAA=3kcG_cTre9N5M>}jiQPJy~dBkS@c&<Eh@Q9G51ks#07<7>}2z=4Q1{a-Oo!B_&&e3J$)CC6S_`c>"
    "aQ_+7EhuYz!)*|j=K_0jjf^KwqRr44Xf)C{>l<sVzfjNVXX|CA4tS-Y^t3a15D6$?)uXkT}zw4^15fDS)p_J=y`x"
    "w?}iUgU$7PDvx+@8oq04cfIHP)JBPEXbMz7<Hw_i_M)3W<&-*y*Dk#OZbU=cH7`medZ7jjFJQXC>qyOUZ9>_Xcy*"
    "|7caF?v66{^mg?~&f|$Ld<Y1-sgyyr$RMr^i`j66ZKz~TE(0j@Eb!?tPZ(KFVewGni|WYow}wlCreTzY!s=5QUt^"
    "IsE1Wx9Ti$spW2lQelP8u^PjU6YX;*P-4#l|PntrRkaxyp|;7{@2a%mI}*;Evyu!BqHA14w%B4SUYza^0A0JlJTE"
    "BhePRmC*kT#`aluQ7@Fn1XEaIat2<tDZOmIuyO^=WZA_mb`!z@Z;gfiHK%J&ULKT7NJQ?MGl(M=pflCKrE`DkOt5"
    "S5@So-RE5DwR4=noSyZ&OnRla2C8JMiu{foTsF+usjuS#}`E6jO^W<Wqq{Hc=;aM~{tnBpqsu7i<0Wq0N2x;X|1u"
    "DkP+}RL-JE3W?cx$<^4OZ5pqZr6u^DDvpryU(=iFAn&%mLHEc_G~{d*?9F6Nz%KXxl-U2`^Nrr<fPF<s#yWHB8kS"
    "Q6+6ElznV%ObRx%WR+Xr3mWU_+z@cWM?_pni;C-EaOp*M3}|j?!vYLp8>!0XK*Ea*+<w4jo6OiDcP2rj9x6W-RBu"
    "EobV799s>^Xc!#&TX-71O2craG8$}yg0nZXp(wz2nKS<$YC9f~8i%&H_EWoCZ>+YA%?i==uBA*(=0WSC`m7xKcVj"
    "YmX8;1GfI4rb5DK#8#veO9K>09SF0-y#zLu3>3c_T_{y2&O3U;HRIlEVIf<CQd&qAQV>v*SCa)rU{;@!Xvz;T|Q="
    "Z3o^O13oP0!%N*0GOBYxh0BbcW`JT$FiiRCu;~5pLLqRHD@CgaB?TcE6X*1RJEd2ffh(V1M<9jq;?wExYQaE*J+S"
    "PZz4$J7~!rk=bjyTI#Oh5X}>fOQHSdOWIi|?S`#kg$jIUX$Pa+}wy;d(7Kg^rA(*hov9Vq6lZWclKsbPLvpQ0mb>"
    "><O@4h*rNN&{3CtLFeQOQp7OSTJ5AbUqQr$jOI}6Q5{AgcTr;zl`Jdxm$nl$1Zq?p4>sO_puJLov~nR+Ov40m0nv"
    "z35x=mA2Vb9xDa$^doPvM$=;Vw7nyiD2cJle*{?FsX<MZL^FMCJhv*G^9@d1#=e${)uRZZqoCFIP?={MDk=I=@1_"
    "(i>G(d#d_c=VY*-2zplu--fJyn;Mb4C^T6;w0{g_XQKTQn1SY(cxPLf%!{Wf&%JP;bxt|)~R&yX^g(vs_Zl~(k-g"
    "7Lu2~Pmh>TG@nY+y0+X|KZETyiQoXp_VK4n<2DK#mx{$y=mX^@;DI1t8Ph}}9)-jb@rpU)sU}=>TeOg!{HM!KA6i"
    "?jBO8Z3qH?7d(xlZ((s=gprv!S>pw(~Fxrohg!-evS(EE|Mf!wq?(%i8mhsT5ncIuGReh-;ZG0q;Ef@P2su%i-C{"
    "DHZ{$rDYpcrlPf-u9?_}q{K2K$}!CLph_*A--dImGDWD0khc7As6w1gT&2&aPQ+PmIh8bEq-<7pkD{?A25>3V#Dz"
    "x^WvymAC(CK=bEu-OMmwep;@)W&0>tkk3Qfd383O{;9dASx!>9R}g&XnHAo&|`LStQE*J^;cQ_xfE=?7LaB-Yi%J"
    "fn=23N$a3-CEudVuW%(&53>r3hX}4VWohh+J%SNoh+*aYsip=ijSfw4X|vfl-iBPs%Qz;pJ~N<gQP8h03TJVP?9d"
    "Mw#EXjOo`<#xiVk*M9Zc!ix(G}BZu*2c&(LC!_``3)XZnDF0cmgsih~ar@hS9)>UOth=rbMda<*UkN>!nTtq7?_L"
    "fFs98IGPvN@e&thpr5=CfvGRTK{#f&S@3NCO=yp|UiO!w&lVIkqdXC{_rv#f>$n6hJH^f@oFb0TovG)r2+Du{G3="
    "5;xg|YG@7)q%A-kisF0lGocLG70?4y5@~*y#Ax!XfbN@oMIb;_m_kFwSwP+hMPq;#@O2J_{R|@|wqIbdA=jb-MP1"
    "bqPjOi%rRGsYKmf*%u}@B=1hJ@#2V##R9_H9#;27<QVo5BXQ>63bi8(ZUCmwx8U(E~>EjpWzff_Qp*=#3{PBxy$H"
    "Nij802;AN+oT;%j%R6=cvn_Bnigm|Xc$jvUiA}ZBFZXXl=jx*T19zg1BFzr&{_aZ);+ZIQJYK3Fe|mLgD21459h;"
    "EE<0_#4rM%*j0`D?NXR+r>x5G-ZLg}@Q^u){Qgl@Mt&&F=<E&~msg5Z#iCzupCMe@wrSwl#9U}!(MILmfu4J4J%|"
    "?}m&krWRg~;H<T2=~&3+hR{t^3XL#w$0g%LrxS@o8>R(PtKU1N^V;T(XwypstFko4K`KNPT)jL85v=Cvr{hv6{{3"
    "XQr$w2ls+)%$BOP6#S+b&qF;G%4Xe3hGr82^%Wg#l!_vnaVEG*Ebtq{(-Re=Yq%Jk4Mb=w;(R$xW!GK(8;jbFNog"
    ">uhaOvN;B3XgFi5h_>=a(W6JVg=6;FMzt2q=90NrjZ!UQEAH<oK+l8u300%7tuCHn{PT6j&%zoXsL2L!Aa?^jsP`"
    "rcASQq(jC)r5-4f@+(CKw_%CZVC3^;Qk>L+(qRiOi#E>WmMJT#A3QM%UAVwswMb5iHxBh2IwEZ7NXK{Dch`ra6;;"
    "^rbyhY7XT`hmdkshe{=FBAKJl0(5umoQ2@-X;dJ2#jRaG+g~Eeri#Ac0Xz`}DxN$Mi#$r9fkd{DUNoB?8U&4)V_D"
    "weD4dWEUY60x9kXPm4;xZiOXJf0dF@vCMi$7TRnd67+kmY%W;p#oDbB}iLi(;9T_@}ig_1zA=>lfl96+uR4aRNn{"
    "^Snb;6n_0e?$IuLgc4w_(8?W$hm1LiW6XRam>D&BH6dc=$*cXFXaO#!uUQt$PqF~6G(joHk<+yaKM@1YLDeWCtRk"
    "t|!_0`lSdc4AyFAu*Q<l0*Ja$y2ks69B<Nf_lVqPP)QLh!dDRm^1HdEz_O`}qJR$jzO1{q=)ckY~Ty2CxpmM9@;l"
    "Dyg0Pf0m0*Yh;VZfg-74iMkcw{%2(wbW}P)=p9mF0*+OP@#kqMBT%O&IN^e$kEPaEnYP#RgLIYtpzMm*LKe^)wBh"
    ")w-m5nZ=r2af9|loB|v)68R%B*Y2<=nTdqfSe8#0Lk|<67Ch?S`K}0iLEj{pK*!$8iJ-aovghMZ3LomQFVW=QFqE"
    "W5q5;P5RtIo=`p`Gu8neh#!fvpU;$j3$=W$S1t7Q9JY(AVe_DO3^o(O{`9s2gZQALSg8LAqRyASXbxpg!!DTAm=q"
    "vvGComZ8RoV!4vtsDNw-I71!Fs_mE{s7#`Q8EQ-GoK%VgeCwEQiGhzKYEUra&ycmswL^max)RDiNW{_l*y)((klU"
    "7A(B#GrzN0eV44R;ek6QB@2&Sv4w1VRiD5Q-luhrIT%j~UM8BA-9fMPJ*Klx>N3IVh2dWBI}jInI9h*4_#_Y*cWp"
    "m*L*7WR$|?>B2_aR<H46VU57ulo(`yGHT_sWhx7DdZ*CY0Y-w&4e8X=$}0gzd@(<Vr=MjLsfIfh^fC;<89i1i1%!"
    "gQ~~}U`<}-LZ}@i40)Q5pjQ|W%Y#wtC(;VZ{G&{q5{m3bAF7%IgR7>Te$N}gc^L5ts4%hykjp<}qvHhx2{A)_)I("
    "QXY;wB=g=PQe@Q+=Xhf(V<D83tfmZZy`iUJ+E|s*4DyGyeB~ge<{Pf}7&43ZWzTvJN2G?S!x-2S!S%oM#Y4vR;qE"
    "{RWn8i(Z48act#L5p>3Ms+RVzFtsbid~9ksD0{h5Nw#C17i;SrwSl%3QEJ|`c4%MrXq$T*JOEXNi0C&!4VEu|U>^"
    "s@n?EqhT;rbb+yh#eXeR;8QR~TG0Q3QDj1f3pX6Oe7Zev(MNlCTPonT?eXF$Rpq!d9)MD)<*3nEf7P@n?w7&IP`6"
    "W$t9qK4OiiQ#q+Ac1y_K@bCU^3f@jO+9g=(>~OeA4{NH+U%ami|dAVa3=k+w?-oLmIHVE?AoG%Xo&%S*$FImyNd("
    ";t;yfFXkS8$>dOuW_4LIw&(n@Tx7J;h8e*1U#7wYsGPr#J0|!Q*EViRD_m2(*=7b7N3RP9l^6O;QfvQhSAYZv&M1"
    "@uPZ35lG2$%`<-71CWu3waBOvJS;vQotwmp9RZ6)l1mAjCx(&Wj??uK;@}l22H&xx;L>5VDDc7s%2CF^9YjOaZ(s"
    "=cqn$6J>Eq;FW<Fs!#y_bu!~4qG!Jy(soR6cR>%-qb6z=CYq>3tMbY0w(L;2r%<618V11oiX|oWx6TfKJUl)Zuf%"
    ">;q}_ewTb=wY*V8;I;zM=mggm>ks^vvKQ7~(7sZLjpo);Ka4!@^>FA(L*t3n<RG?7)UYOrvq@|cD=GLbJN(hOjW3"
    "+2UgQw-!MNa<1inaZ2!E>UP(1UjpnRm3Qk#IeknlZV%H-v!8R{|qouDUS^-p$HjJ5tjkz4Plu)O>H~s{}y*8%xxQ"
    "4`mZ2L)tGP~T23Z2vrL$*Z85vrO(d-(&(xHpB0&-qF{S_-0IjH0`tMucJNm#uQFf}PQWaA;8hyO(e*KQ`lLP=S`q"
    "z-KwS@q)>`@8<(qu}5R|5t{4w9x|;Gl;r0^<(wB7y<gnrHhrdAusa77q*!#xNk!(YZoF0wj&exCAj`)q{v`ZV5jr"
    "3Km6tn+zl>faY$^xu4}31EHXFm*tqgg-Lj2*b*3URXzt*L2~N&pPtRIJ379IYSmKADlctM(9niv<8wC4@fv|^V}7"
    "K^|M-p^TD|I-UbG-Pz&@PFOR2h5zOFs)AZY2tYo762-s{L8-PW8Pn&ekr(h(c8cF^@gGpBOv@YILXjXG(m=b*96)"
    "uoAEa<;z3)t)oI(Itc60SUfbV5<TUKKkVLy|TuC1UPl4jJ6Fkd~^fepDLksHw_<KW7>OVs3nEg%V~}gAe-G%=)eU"
    "aKvylU_FPru!34{An&@NDGyW6%gi%Kyqri!h2+1hXl{i)<s{}|aW56h9NfY1kLLRWowLCd62^whz*!RfdamBaO^k"
    "$Q9N(1lxhhRJwPh&DRkQXB)?^gLNUv<ULQ`h2zS<%Tt-yJ8}$4#<H{-AjJ=f=n{t7<)_Lnysrdf?+G0k{<Y<3QlI"
    "dDYV<s@XoCk?GMy6YH*kG^rkwo*<kuS3V#{`167EI8ZUWA0TGd{h$iOz}aoaX_i*wv6L;GLK=ux+g$`cz(bG&ZX5"
    "vNz8P4|xbgn=H?W8^AH&l)M~a+g1lFSY1)6&6dIX?;8CYZoncLiyUevq&a=l6sF*iW1UWb<l*I(SXUa#<L)Hx|qU"
    "H5L1>irrKfD)irCfQsdeXsT&pYD-O21G(4KCe&XluYK^P&bOCT<2K{hlxmCs~r+@S`J>liq~mh*AnDIyqe|}p=-J"
    "Q{0*>L=qk6h#e9VB8rHDwER<c#3ror*D2ETAmLL?S{fql`!a1}QzB8ldzG64Q<CawE@4nw56PkOaFJPZv4TEnF4t"
    "B_QHvK<OW<YqDcMODdJ?uP!@dw!HvS&U#&FA;cdXdmrOBt6Ck=TWtsf`N~@|l0Q+6&bH(}8EwB2Le1g4i?gS>j>G"
    "56`|Q%1lrCC~`g)LB)|@7)<&ZHY0CNkAnASzm^8Z%&-;oB^WXJea-QU_!N!+^f=f|@_Cw+{kAF8GG;OXgtOuYrDi"
    "p@dhn9b>A(RHMHkb`&Pe!1kD}n7v2Lbi&-@w$oaa#{)n%Gh*Y&kiM%g@1v`yK44?s;lQkcw`0wy(An!X<a61y;er"
    "uN`fK7mDP_Va9Wn-uBHssNPfjgT)NVpAJQNF9E3@-(jo*sG#odxPs)65ah3TKWe-rVhz~s9O`(m}y?=8txF9!$#H"
    "(__rgnKU=PL0`@;2{W^Mg5xfk3IXn3+u)2oSTMcGHipCd*@Y@7E`73hGg?+*u&od7ngivzglB31w*QG|olyEuy#H"
    "Skkuh+hlp5l;8F-bc3CTl+@7CB^b@o{>ZSE^um(|(7(I66Kbom~V+#}_A^Jz-kSbO6$dF!=kMU*C_;gWk{4&rvH="
    ">B({M?&SEFUyt5hXc=K}cp|)W<RqgaheWhBPv(8^3-+?<xH`U|){M)E+)fR?3I2T00_R^p+tR8CTlk9T4(60rGWD"
    "iK6!_l>yN+_t5!h#V77s_jH+r79lH;Fy*B4!{2_8+R9xH8Eh%WWqWh1f&63%wO7e)1LT~bW!#C+P{+9zi6=8FXqp"
    "E|lk%G+TEH)pSuJd{dZ9$ecH0(OhYNq)nMAW+!ys!z(MTTxF{v^O5E_V^2gl0v_rND3(7Ab5RnfWJin!j*67f*^T"
    "}H(KTZ7&uB4uy_5~K!mL+Ao5~FogXSRvRoxdWKV0_MV;rDgDDOS7SNft+eL~fej8}~Op=y@1BiED%wK>0?4aMW!u"
    "<5}v(^}IdFk2*2$_wWwBtfA3p@vqEAO|vurJe_CA6QRO6$JMI|R)_h9=EaOb1UXsQjELsJp43T>`;&%!UTaciGp>"
    "zeW2sHyW>`i-43V^F&>tvSt1l96Ybq+C?O<)qUgJUk8Ud2WO|{3}811xQUBZniRopay!KqykN3r0((IaDnTMsehn"
    "`e^%B!ESZ~CA?BZ;&2ZTc-k;f_INUaWTUjTqqCx1n@H)>6>#GPKho7E$-Y@FQ!B2RyrglJ7VM5JT_L(9{}6{QrNw"
    "pz}X<OB1c#>E}m#NTsHWwrY#>dP7|En*{G)zxnG>hsgmj+XfVc(F!%aj|XYwCEDGlS!IYEgp7+CNvHv?a!f2S_?Y"
    "jhm6Sxd|wK#YJZKY;k-*N-Cm>m(}tS5{c%S9bUU*gll>!Xf8H5$bZ0%9#jAYsyMa|}e*zmTJ!KgOejIv~16^R(>@"
    "9>V1}X7Zdk?btJPsbr+<t7wfJ}*6V#n}PZ|_X!_05y4uDoS(ZA5wEKcbdqx9@&7fkbrzq^yV;x7P*BX+!+vd$pdR"
    "VJDUf9x7);b~JSW46~%S)V8IH3ke6Oe(ZviwYrVQu-Hp~<iU$~4}0*UUEVu!eeQXSN^%ZdqKkGaJ=kAVP1RlJo8W"
    "aAb|%z1o#fJ#lGkAj0r@;Lgk`GP)ei9-owMM~sLwYZNRVu+qNy&I;fvGJ@!`?&f4yiMytBj6S@8Csn2v<R8oX|y_"
    "3JjML^~;?#IoKB*D9muvqY+AAipDvq2N<o?OpfNa-QC#;Q6DCqUtrD3Dt0J2lh(>Yny!yfwp~nI66KW9lkKZwz6h"
    "%y(p3~3bz`Qr3Y}{MoI1veI2}!APNmk1YQ<pnNm)wde<VR^`UMH{`=zMlo|9mU)@lY?zlwk*zR+csofghY6cO#f?"
    "t6>+p`M`<TD<^LGio)XxP`~ef)Dd`0j592iN3TxVp+N1*WhnHW@-z=RX+RZH$!uqN02va>!o$v4vuCx2J30-9mJG"
    "PzxmVwnGT%G))@Pfa>??Pl#HtZ?oFhQ%6{h@$C4PqgfRiIjc0@HFkLSm1{B$cXMI1D4cY3L}ZG{gUQ+VJZs8>hV|"
    "?C!bS*o+WXxvJ8!=~{@>%1e;jK8&skwvf0;jvd-Vy?|2dMz4u5upzqaJ+^w@<Xm0Q~4k8<2!5B`u1I!5v_<fs(xI"
    "@|MGsZZT0yDKj#1WfwYWVj4E7Pi{(nb4VfB?r%n%HI-^PlMOjK!!4DA-32WldmAY+%foT+}1k|BMY-Jnpd_zEfuq"
    "mn+w~%U>27_%f{IG-Y!D3d+@&EA#tKbcPvSsug3GVT$5qK!y&$36E1MRvREPmGIdCpOc@A?*``|Ng+l4AG2`aIpv"
    "XSu?8g1FKoWXo27?!^2;eiB>3i?u)rzrGpG0J|!6x?RZ!yI%o)-D<_vC=yLIuk7q4)C`_?mj}ZCob5A-RoKMj-#F"
    "k*+gxg>&Ip59UHH@_dDc?1UjVG9-d{ZD8rL9BjIIQqGEW%>!m(?24O>g00=JlS@-~*~cY*Y+yR|@)B_m9Q`0xczC"
    "lvZrEGO0mp5DjOA>Z+{P4G(arYQju0;Nz$O^L03|drf$Xh8+w#DG?zl<O3@s!|LfvFL%RKB{Ykdb?TepZ|F3l^Zc"
    "V&PfyJP8ydI*F&V;|ixokN+2NzoRl<A=JqY;bwLDh1BNmk)Qnc<KBWUx9m!g0sbWg27P6lrHFsgbM3*L|fE#D>ta"
    "nfR1?$W4^5h5h$%yEwM(_ozx_-$k%3Q?}7M;S>S1HqI5$1Kr8{?dJG$SsVy=@^arV`^w$o|gD4uGD;b<)3Z&lj<0"
    "kQW))qC|Nw4W-+ZiAH`ETRz|N58RgQDouqU5%)H`<sd9?XdUat976J$lo<UMrwc-)0k<)4R0un*`6F<Sn!Ol15Ia"
    "1dSV$&gtlt6!qi`RzIzh+Y-hx^e?io@RZYJFPIDa&4)z7xo{j9n3Z+=Dpc_@=6n~bI!Yip^M{!$%jaXV+3I6@ly&"
    "RZu4O%NG|zw+PMkgjfou@4yp6NG8cPvZdym^9zRa>i5pVgbu?`tPI;yC-OV+P+R_W$a3-GCJW{oJG+I=bv2(QRX)"
    "4(3U&)Dk0>RBeUBB>e?JUjG?Oo_26&+8T$mcF+=$rtN0VykImYaJL*L6n{9er%&?wvJG1<p!;3YYDTTH*2g(cdbN"
    "O{^K;xwSy>SEUSRXHs3Q{8P=g^TG(o-geF~Wqood8tw*NYy3DlsOLiCsDWb~r@hUDTtaAHcGRNrE9w%<^4Y)rZn^"
    "A3UFq;WsbK}}-j@T$r8YTWqPRZftPJ2c4dEBn9m!6vb7O7gQs2lCPAN-PLbIN++JDdY^Q^c5zYts(o{t)P0^|?xV"
    "v77SUg#>O$v*nc|y>KdtwkGQ2E-&UKnV4*tvMMeE|ICvh+X1QRb6ACh;F@BU)hE!$;#x36*A80ub9L<x$vsuK4I;"
    "U>+b0ioDCN7N<Z*cyl<J29^=1{X#uS$=nwHw|#HPl|x)%~odt()^@|$f@;a0OGeX=$6h_s`jZ1A)fHk7iat&rX_>"
    "KKNMul!*;nFcYlA}NWctYXl`2%|Jy#kbRW96-|;(EoYQ4_(bdXO(oy#|=@`(3p}+rmF4t)I0TobM-@Lg7gZhga=P"
    "I)gHI`HEpkE6TYTx?)8D!^1C==JDSWHs<4}&6lWg{{vQhzC7IC(yWoEsD`GS>+oiRtm$SUU7V};3lEzc2@Fz2ERW"
    "$09c>Llw!|u178P@sow;i9o+5_a(zw(q7{=Ux31~Xr};KEvc_~<S5=Jn_?o*7}IPx}zCUPG>W`}p_r;5woUm#?oI"
    "eX*d7Ta{CDvKd?Tn7?p2AVIip=9?M0>rq(|bqK!{dVd5zu`n4K|4$f+(izA1Td`NW4p)b@X-(Q6)E8<JeP@}pxB`"
    "7s4oQw93XLXIv_^I9eHQh~-Ty2C=qg<#v-{a987S<4)>iQx7*C#&6_A5GV@T^M`YRU7tTzNqZgCfS6APIJw%YR5k"
    "1jmgPp>8+gQNrDA-0gTprxwv6)|fOEf{!}s#4i&vbiB<cuVS=!bec{sn&=9#Nw+Ac2NeN&FW-6N%kpOAtO}@fea3"
    "V=D5PnP09NSBS&613=s_Lj@Qg5UD$RUaU7ZqQtuh)QqecAG9d9sQqbg0D}uy?+?_WGL&-bvy9@@OX9On~afUXR#P"
    "Lo9{fk7kjN|fS$+TrqVu0uL;=qBAqg^3X0-mc3GoO4A$lbk*SA-;=Zz_VE$7moef+%eO3MZ6lMUrUFNJ_|cDS{$#"
    "-s4Vl5~5eDprYsFB5|-nkhng;xH)VdNPo9O!x+s%L0;19l=o9I6&u)rkg<Sj#sLyHqN@x8oW!%GO^#NKT$H>Z$Zf"
    "Rp9#LoWBEB=w`$SI)!)#h6tNYI<##zSYa+OXkH_mcHq(!?LUoo7kbgH*c<7(Nd8FsMQSnd;GFW=>?%x{rA06s7C)"
    "x00Pk%N$qe?`=BUqfA_ED`V<(EzygYJ~WV?C(X)spSfn94q>gfh!=&`L89xJzy<M5cTW4QN@PJ>aoYd16%3$`vx>"
    "CrREacK|K3_s5o9d$O<GZP6f!*Njg{YJrd)IBtgOsF-dMRK-S3-9p&9YYCdk#gy5@*V2dc7I>218VvK$}Jvn=G_R"
    "sO*(b?$T#mU(}C3mA0{N;3Xc7AkzF*;@nmo<>a%8I-nOz?7k`sUqee0uWh(YvD&$XkpVviH#PtthZ1K87p<XM&!r"
    "lwd&erG>0a28!T7D2_^YHcxNhQpU*7;zB1Z4Va|FGNeSDIne1voJD3~6;5qCi6K^{e2kn*8RM|=+GUm&XMLhzmL)"
    "^E5v;fJEfPKkSQL0=MM;xllR0_E69bRY>p;$o0)@_uf*N)vas3FsMc8LpRCM3fUa%+<*#RgP3W%L)xz0=Kl5$qyO"
    "c4lRk3d<XG<RPBTdSa%_OG(>>DlOfboTer;rQfud^RFx6r6huXkwq!`l7(U(l3|sx8MJTR9UBx!=p35AQ!}RpF-d"
    "r`j>c-j7i_af<B-n2Jk*mRX!#5;E3xU^vVBVr<mx2lOWH)DTqQQ5kovNgvh<aXu=aPDQEGTPtXc{g3|lraaC-RdH"
    "QKQp71mytciG9=BrJW1O@O(_m^a*qIJF`sBrj!1cU&TrnJWk&l<owEO05;l($GMa*PKxTcx*Cf~xqG3X;d9-v<oI"
    "jj(tyCmb&a`|BcEq`%9iE^xMtY*FN!o29~DA#qLUVbb5Rm?Ut45VjOE&J;<RuP_5izPaDb#KCxguQbl)WQ(*&EF#"
    "A&fA&6hz?4XC5Wr30u{_J@BfMGbvP)H$#DY?x<js>HM=$ToD&ftCMOYr<E-<6^#u*z&5U6nr5N4rQY0w}LH*qmv0"
    "U4MmBxxTOfzXyw4J6dt;|n$0H&Hwh$Razd9My~Wekm%av|Pd?hIJ1pjs(;atdg6wN^j9+MG}{6&Y_ZAK_dwPp^&2"
    "AR7`x}po{GraiX`YJeVdoqB@Dh(aJ*VQ^vcm1b8eF%~ZL>J}X*sS$Uz6vP!04r3Lc@hbauioe(=nTe*E89kc`I6u"
    "l-|8ZtGzo3sun^e&k!A`xKm^>KS#Bo>p_E{&(C8~&~FyBzf31w3ryQMuY1-L5Nz^KBtZY3p;I!Z_LcQqU{_A*<-p"
    "uu<^&W(_3Hn4o78s)JYlRw@)c0N?^(g2t;hDwK3VOJ+~Y41qkX64ncMXPH4M0Knj4Ks3YaCv#T#AkClAfz!k^TL6"
    "c27VPi0gj7;29+9ru^;~AIC&6|RAhwHUL3hi9#4+Z&KquE!4aF;h#Ftj&soZ8kj<A<Xjgh+3p<5{WQgc7+NW!HUp"
    "_-0UXe!f>N)tVJ>@O4)U3tgUzG2{3OeeW6^uwSh$mCYAY7hG!74vFeUl><;&--ZTg|1m^8aCLZ=FR%|3TsW$8t2i"
    "dm23+_PS2xBjB;6Z2!+=z{|=epQ#<=PTnoJ!M#sJnT;egwxu?6m1V#<TqPx)wxaTCF)1Q9MJ&lPXr?+^cmEQy(95"
    "|)axKDUG8|O5O^UW%s_OA9`B80PP<)!5|EvYSy)a@p&F`d=!d-S2<P#ZhP@S5Lg#-*;~f|R&L?WX*G`eW2wwPm76"
    "KU$1#^O$@c{DU>c$y>1uooDg7TtcyXWiN8@?!+2($OZ|RHahv1xgHn<REv;Hp{?fFsKr9%?&T}66$VqB&nBNz*cf"
    "4|7M#5)6?L1I42BKG$sX1qzsbB+fSJ4bCdrZ_UiE{EyIj-=<}OtQ(=&F_!bFA{VqV%5)VwtNl$I&ZMpZ6B-cUgKV"
    "29EeN(#!DcltLbH-SzB|9mABPV~rWfgt$mKKL%k7j!Ij80!DJZx<3{=Ir0j2i>eSV!f2!H~6hDjWu@u(h?F>h60w"
    "u)vXX_!Fp4`E=Aj^^nM8|GV1NxM%~Wq&!;aZLC@-^t9$wq$Rnor*75>%M`#nI>JEl4Z{UWu!%%q1c;Pf}xOJ#B3N"
    "0ZeF28dd#%W_ZZggde^ErAg>?0h++B=uvD8n#1`X?Rpt<|VaPT<xrsFh%R5WGQ#3M3Pbt5EaF1vX>zEFb)W60<`N"
    "d#FhNDtmkK{`e5qkn?vZrz1N3x?iWIeayoJWN2$niZcL{0!moV$4@vM>(ksj9=}oh31h=E*z)XyoUlyiK$Y^O(b+"
    "<jagI<Rsku%c*ISN0qTZYHJZtIm$P$u~990D)GPWAWXT<yN+PV9l@EYR2ng}~{f#=%!|NRQN5|C!_v$n{%AYTd@v"
    "n%D1+5)A@HO_Q4YM1r^)0o=pBEKo9pr<AW9X;!0WDVzlJK5E&ZHz(n1w)<9?&SKx_a1PIMTAgWcv(s%!IO!G2zNP"
    "-ohL~!@r8UM6amsn@GmfN{G4qhY{iY89Yxj3qPW)+KF&g97`N-J5LmPBr9`{a1mLaY7l^Cc5m5nEA^4?>2ZoRX<2"
    "+l-!fhRA*jJtKI6ua+sft+RCkLPM_gqe6>CUnCGB7E}u99R1m@m+0JLa>#$_U}(HvL=#!n4b|_!K_PjG5u4lzJM4"
    "`D7~rQEk#)?S+3(N&9zDNB^+W%H?fWX^$SVMu)%z!{FhusaU#tuU5#Yyu%j7P8Q;!dSk?FO4?kX$lfTrsuvPY5<l"
    "(c_(}CpF@49Lq_hTMi2CxQo`zVLs-6@#^u>0^y{3x?o!y0VZ_~Aln1NCTyS&uHGG{W+J-V2@jVY}{pP=L)jxI*;E"
    "=GsEMgTY!ZdLLO%~naQu%E$g5<_{*EfBKV=w4z2hozV{r^!oG)A^=g6(V&rA0jbLDYB~ghS~cU&)G)5B$BA$<a~d"
    "Xd`eb98E5lp{<~oqjS=QDTjF20G-I|Pu5i~H%2x=O!r0k7x>O)C6X^A7Zp*8R4UCG@oGoUw+ej=Y!RKq6v6f@0Wj"
    "Y4KY|ai4npZ*++q$fqWqSgbrCHG?sN8%rLr7359p6;{#dlsh?5f)T(5;B%)2QTp)JT#@57DA(mFyb(xQSQDL7oeW"
    "3U%dfhY2c8I{fghF>^c4UICXbtY*|%Ijbtje#d%gqxTx;2HFzK)-B6+97laA=GqNuF@8jv=o#~Q=RJ0=b=@VQAje"
    "8D4E#Df$=&W)_mpV0zLp57NArfapLuJB4u6xoKo0CRl1B14dsZH2Ddu|hY5NZT#FgQ{8o@&HsIH}JvK)Lhly|(#4"
    "HH@Dba_28&G}}q?^Vch6)<UO?M1Kd`)=L!MHLE4n9Wx`v&I%um0bO(^RRWv7g7W*XQ)3S9fhI%8*za{`hTQ_4sGE"
    "MnRXXDh-x+(ZlsR8sSPoblL^_qC+hAe&%B+9%;*?X*v$-(I+lEeCy?1T&cwTFEV+6ryrZ{;fwvz_TAbb!IcJlD3}"
    "N>=Svf)=bp6v$x>*fPqN6a&p~1FGtebU5cbl79ml!za)<r^2C#&l-sSG)yckwHmW*P^x^()KrTrHDZ$CWLM9&<KQ"
    "7x#mS4GEZd6vu|{nGaic%N&0BJY^r~Y?<e!a7L%>Y67DU_rfMqmk;555+o9QdR`EO#8`Ajdk{mn>lB2gNPM8|UgB"
    "6C4x(q*{uIy!iSqPL38aY-F365U8yUyR^ov`ZQFSF(VuXQyYd@GY`G}?opIx*PX&Ic2etCaBI&|ETJozEAy4aAw#"
    "gwTc7~>?nZuzAbaWrLm2S?{MWSxlmryyeH)38U#9YW)NuvORM*d)U`7F=CIOh+O}D{;A*mQ`A9=)f0HtNB0}SG6i"
    "J%UdQvFeNKs?6_8MEQTnlc>k49k$9!W*rt$s9bY10L#JVbhZ0-!*^07e(m=GR{F87tWjTdlReA6sV<-)YMw3OL&+"
    "Z0chL3}ZcpoO_Ji$B}9C#FD`F_53BF@wU3}X{}V-1nGnqZ9#Y%&TqVmcH!loDAGQ!Ebzfz(&gdt)T*CG)(n=JS%I"
    "0t0lHmT+Q#o6rqv+hlktnUiHpzsvy;e5)5uBCt2imfkAJ!Yq1{;pkZ8$S|P*Cn+jL90t_U3b`ItL^K{S{^pDNyt1"
    "Exr>+#T_)SqJUSUQcF@KE!kQBiiR0b2t<Cu_nF>{cJ-8N=<aI+!Mx0+iY(;MaoTJlQRNqQ5Pv8V5hj~m|;Mzuf!s"
    "Ko2|h5{xG*_mq)GBe8C(R4!arhsKZOdTBOWQ<hUTPsdSvNCfUmt+eu(?!-+9V&=TUa0hNkF`72WvP{{xMtMX?q0a"
    "}8D^4e)t0g!_}{OJ$9CtNJmwhR?a9b&3gUPtx0;RiYdYSXK)EEP73+meycg(^7ax*j{Q?q08!h@Blcmjt=clR7mU"
    "%jZ9^dA{Gfl4BE*9**qgaf^Ab5BY1ur<xUG%|bhlk<gRzKc`yLnuXNbCp)P|~=e6P(wyZAosp;~o1FTI1G2pMGn*"
    "c>Tk3;|33Yzr*QE>$H^ICTaCpL|Su7vlY1uj_)&W4@ziQyLAID#o6I5TeA3Ya1%PRS)NrMXnEna1u;2BOQ`RWW`S"
    "-NX7@)~h;`N7zD?5p_)HnU+B?cVC1sV;61dFoT6nx^V??}@X`|>uMN$>_LOja^iCaY9jE^Jy9Cg(e;2=i<i+rHxN"
    "ZmN~?CD5ml@#+7`DVVmnBM4XYIA$!q!!GN4TnKzY~+*PU$^c|3Du~}7D90Z-L`JvQDgV6Z`&UAJC{Yc|9lhCi==<"
    "@X$O0}__LY<&#ptiC?j=dDX;R)Y}v0TwxWHilsMU+E4T49O7-L>SIy|rqu%>vJ#DD%Q<g1~hu|vPd;EU|kog?"
)
course_bytes = zlib.decompress(base64.b85decode(COURSE_ARCHIVE))
if (
    hashlib.sha256(course_bytes).hexdigest()
    != "02654835acabcbbc75b10d055d11bfcd2bd03dbd4367a6c64803b3828aa74f7c"
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
COURSE_WORK = COURSE_START_DIRECTORY / "practical-work" / "ch05-b"
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

Now consider a budget. Moving five cents from reserved to spent requires two values to change
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

**Your prediction:** two workers both read ten remaining cents outside a transaction and each
approve seven. Why can both believe the next order fits? Explain what must be checked together
with the write. Then change the example's initial reserved amount and repeat the failure.
Reference: Python's [SQLite tutorial and transaction control](https://docs.python.org/3/library/sqlite3.html).


## Memory means selecting retained evidence for a new request

Lucy says deliveries should arrive at nine, then corrects herself to ten. A useful assistant
must retain the correction after a restart and avoid presenting both times as current guidance.
**Persistence** means the record survives the process. **Retrieval** means choosing which retained
records to include now. They are separate mechanisms: a database can preserve every revision
while retrieval returns only the currently active revision for this session.

A **session** identifies the conversation or work context that owns a memory. **Provenance**
records where a value came from. A **revision** is a new version of an earlier value. Here a
correction creates current guidance while old evidence can remain available for audit. Forgetting
excludes a value from future context; it does not erase already sent provider requests or backups.

### Derive a retrieval rule on visible rows

Our small table has two sessions and two revisions. First filter by session and active status.
Then rank the remaining rows for this query. Reversing those operations can waste a limited
context budget on a foreign or superseded row. Predict the returned identities for Lucy.

```python tags=["foundation", "worked-example"]
intro_memories = [
    {"id": 1, "session": "lucy", "active": False, "name": "delivery", "value": "09:00"},
    {"id": 2, "session": "lucy", "active": True, "name": "delivery", "value": "10:00"},
    {"id": 3, "session": "another-shop", "active": True, "name": "delivery", "value": "06:00"},
    {"id": 4, "session": "lucy", "active": True, "name": "invoice", "value": "email"},
]
intro_eligible = [row for row in intro_memories if row["session"] == "lucy" and row["active"]]
print([(row["id"], row["value"]) for row in intro_eligible])
assert [row["id"] for row in intro_eligible] == [2, 4]
```

The database exercise performs the same filtering with a parameterized `WHERE` clause. The
bounded result must retain identity, name, value, source and creation evidence. Returning only
a friendly sentence would discard the provenance needed to investigate a bad answer.

### Understand the deliberately simple relevance score

We lowercase using `casefold`, split into whitespace-separated words, and count the intersection
with query words. A set intersection keeps words present in both sets. This lexical score is
easy to inspect; it is not a semantic embedding or a claim that similar meanings always match.
An **embedding** would represent text numerically for another similarity method; we do not need
that additional model or library for this lesson's explicit rule.

```python tags=["foundation", "worked-example"]
intro_query_words = set("DELIVERY time".casefold().split())
intro_ranked = []
for intro_row in intro_eligible:
    intro_words = set((intro_row["name"] + " " + intro_row["value"]).casefold().split())
    intro_ranked.append((len(intro_query_words & intro_words), intro_row["id"], intro_row["value"]))
intro_ranked.sort(key=lambda item: (-item[0], -item[1]))
print(intro_ranked)
assert intro_ranked[0] == (1, 2, "10:00")
```

The negative signs turn ascending Python sorting into descending score and descending identity.
Identity breaks ties deterministically in favor of the newer row. Slicing `[:maximum]` then
limits the output. Validate the maximum first; accepting negative slicing would quietly turn
an invalid requested budget into a different selection rule.

### Follow the context all the way to the model seam

The course's `Database` supplies durable rows. `preferences` retrieves them. The context builder
places selected values in the next request. The replay model records the actual messages it
received. A successful insert proves only persistence; a successful query proves retrieval;
the recorded message proves that the retrieved data was connected to the model input.

In Unit A you implement retrieval, close and reopen the database, then inspect the context.
In Unit B a query loses its `active=1` condition. The old value can reappear even if the new value
ranks first. The repair must exclude stale guidance rather than merely move it lower in the list.

**Before the main task:** explain which records survive an empty query, why another session's
matching word cannot grant eligibility, and what happens when two rows have the same score.
For transfer, correct twice, forget one preference, and vary the retrieval limit. Keep actual
row identities beside the final context text so a plausible-looking answer cannot conceal the
wrong revision. Authoritative current stock still comes from the shop tool, not remembered prose.


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

COURSE_INPUT = COURSE_WORK / "ch05-unit-a-handoff-v1.json"
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
    reference_task = source_task_class(COURSE_ROOT, 4)
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



Putting the new preference first does not remove contradictory old guidance. This time you begin with your Unit A implementation and its saved evidence. Lucy corrects delivery time, but the next request again contains the superseded preference.

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
REFERENCE_LESSON = 4
HANDOFF = Path("ch05-unit-a-handoff-v1.json")
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
"WHERE session=?",
            (session,),
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

State a diagnosis using those two observations. Name a test that would prove your diagnosis wrong. Remember, correct, close and reopen SQLite; invoke context and inspect the actual system message seen by the model.

## Repair the boundary

Return the complete replacement for the injected fragment. Do not edit the oracle or print a desired observation. Repair the actual source. The starter keeps the defect so the learner outcome remains incomplete.

```python tags=["exercise", "learner-owned"]
def repair_fragment():
    return '"WHERE session=?",\n            (session,),'
```

<details><summary>Hint 1 — the consequence</summary>

Lucy corrects delivery time, but the next request again contains the superseded preference.

</details>

<details><summary>Hint 2 — the evidence</summary>

Compare the two observations, then trace the changed field to `preferences` in `src/sovereign_agent/assistant_context.py`. Distinguish a schema refusal from a business-rule or authority refusal.

</details>

<details><summary>Hint 3 — the design</summary>

Use a parameterized query, set intersection for relevance, deterministic ties and a validated maximum.

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

Correct twice, forget one key and introduce another session with the same preference name. Prove no stale or foreign value reaches context.

Create a fresh task, load your handoff, inject the defect and apply your repair. Then change only the copied probe to exercise the new condition. Keep the actual observation and a prediction written beforehand. Explain why a visible-case lookup or a blanket refusal could pass the original example but fail this transfer.

The instructor's holdout applies your repair to a new copied runtime and checks both the positive case and the missing protection. An exact exception or changed state must cause a failure; no broad error is accepted as successful refusal.

## Exit ticket

Submit the original handoff, baseline and broken observations, repair, transfer probe and results. State what Lucy would experience before and after the fix. Identify the guarantee that still requires separate evidence: Forgetting future context is not secure erasure of backups or past provider requests.

```python tags=["exercise-report"]
passed = repair_result is not None and repair_result["status"] == "PASS"
exercise_report = {
    "unit": "ch05-b",
    "attempted": int(repair_result is not None),
    "completed": int(passed),
    "failed": int(repair_result is not None and not passed),
    "skipped": int(repair_result is None),
    "connection": "PASS" if passed else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```

## Changed-constraint construction: Retrieve the newest eligible memory under a limit

**Allow twenty minutes.** Spend three minutes predicting, ten implementing and tracing, five
on a new case of your own, and two explaining the surviving limitation. This is dedicated work,
not an invitation to run a supplied answer. Both units revisit the same invariant after different
core experiences; in Unit B, attempt this task from memory before consulting Unit A.

Implement transfer_check(rows, session, limit). Each row has unique integer id, session and boolean active. Return eligible row IDs newest first, at most limit. Require an exact integer limit in 1..100; otherwise raise ValueError. Empty eligible input returns an empty list. Do not mutate rows. This deliberately isolates eligibility and tie order from lexical scoring.

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
def transfer_check(rows, session, limit):
    raise NotImplementedError("Filter before ordering and limiting")
```

```python tags=["assessment", "transfer-invocation"]
import copy
import json

TRANSFER_CASES = [
    (
        "current own row",
        [
            [
                {"id": 1, "session": "lucy", "active": False},
                {"id": 2, "session": "lucy", "active": True},
                {"id": 3, "session": "other", "active": True},
            ],
            "lucy",
            2,
        ],
        [2],
    ),
    (
        "newest first",
        [
            [
                {"id": 8, "session": "lucy", "active": True},
                {"id": 9, "session": "lucy", "active": True},
            ],
            "lucy",
            1,
        ],
        [9],
    ),
    ("empty", [[], "lucy", 3], []),
    ("zero limit", [[], "lucy", 0], {"raises": "ValueError"}),
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
    "unit": "ch05-b",
    "planned_minutes": 90,
    "starting_evidence": globals().get("HANDOFF_ORIGIN", "INDEPENDENT_UNIT_A"),
    "prediction": prediction_notes,
    "explanation": explanation_notes,
    "core_report": exercise_report,
    "transfer": transfer_observations,
    "explanation_review": "HUMAN_REVIEW_REQUIRED",
}
submission_path = COURSE_WORK / "ch05-b-submission-v1.json"
submission_path.write_text(
    json.dumps(course_submission, indent=2, sort_keys=True), encoding="utf-8"
)
print("Saved evidence:", submission_path)
print(
    "COURSE_REPORT="
    + json.dumps(
        {
            "unit": "ch05-b",
            "transfer_passed": TRANSFER_PASSED,
            "starting_evidence": course_submission["starting_evidence"],
            "edition": "student",
        },
        sort_keys=True,
    )
)
```

## Extension: let the model manage Lucy's memory

Everything above kept one rule fixed: *you* decided what the shop remembers, and your code
wrote it. The remaining question in this chapter is what changes when the **model** decides.
Lucy tells the assistant that mango sold out again on Saturday. Nobody calls `remember`.
The model reads the message, judges whether that fact will still matter next week, and asks
to store it.

The mechanism is the loop from Chapter 3, shipped in the embedded runtime as
`agent_loop.run_loop`: send the conversation and the tool schemas, read back an answer or tool
calls, run each call through the dispatcher, append the observation under its `tool_call_id`,
ask again, and count every attempt against `Limits`. The model only ever *proposes* a write.
`memory_tools` wires `remember_fact` and `recall_facts` to the same `Dispatcher` the book uses
for every tool. Writing is marked *consequential*, so the dispatcher refuses it unless a
`before_write` gate is attached, and that gate, `MemoryWritePolicy`, can refuse a write and
records why. Reading is not consequential. That asymmetry is the whole design.

`llm_lab` supplies the model seam: `ScriptedModel` replays turns written in this notebook and
runs everywhere; `OpenAIModel` sends the same messages to a hosted model when a key is present.
The loop cannot tell them apart; the record always says which one ran.

**Prediction:** the next cell seeds one memory and prints the two tool contracts. Before
running it, write which fields the model must supply to store a fact, and which shop rule
would refuse a correctly shaped fact.


```python tags=["extension", "worked-example"]
import json
from pathlib import Path

from sovereign_agent.agent_loop import Limits, run_loop
from sovereign_agent.database import Database
from sovereign_agent.llm_lab import ScriptedModel, describe, scripted_turn, tool_trace
from sovereign_agent.memory import remember
from sovereign_agent.memory_tools import toolbox
from sovereign_agent.model_turn import ToolCall

LLM_MEMORY_DB = COURSE_WORK / "ch05-llm-memory.sqlite"
SEED_MEMORY = "Deliveries from the dairy supplier arrive at ten on weekdays."


def fresh_memory_database(path):
    """Start from an empty shop memory so reruns and replays observe the same rows."""
    for stale in (path, Path(f"{path}-wal"), Path(f"{path}-shm"), path.with_suffix(".authority")):
        stale.unlink(missing_ok=True)
    return Database(path)


def seeded_toolbox(**policy):
    """A fresh memory holding only the seed row, behind the gated tools."""
    box = toolbox(fresh_memory_database(LLM_MEMORY_DB), actor_id="lucy", **policy)
    remember(box.db, "lucy-seed-001", SEED_MEMORY, importance=0.8)
    return box


memory_box = seeded_toolbox()
memory_dispatcher = memory_box.dispatcher()
for tool_schema in memory_dispatcher.schemas():
    function = tool_schema["function"]
    print(function["name"], "requires", function["parameters"]["required"])
    print("   ", function["description"])
print("Writes allowed per session:", memory_box.policy.max_writes)
print("Phrases the shop never stores:", memory_box.policy.banned_phrases)
print("Patterns the shop never stores:", memory_box.policy.banned_patterns)
MEMORY_MESSAGES = [
    {
        "role": "system",
        "content": (
            "You help Lucy run her ice cream shop. You have two tools: recall_facts to search "
            "what the shop already remembers, and remember_fact to store a durable fact. Store "
            "a fact only when it will still matter in a future conversation: a standing pattern, "
            "a supplier arrangement, a recurring problem. Search before you store. The shop may "
            "refuse a write; if it does, read the result and adapt rather than retrying the same "
            "thing. Finish with plain words about what you stored and why."
        ),
    },
    {
        "role": "user",
        "content": (
            "Mango sold out again on Saturday afternoon, so we should order extra on Fridays. "
            "Also remember the dairy account is paid by card, number ending 4421."
        ),
    },
]
```

The schema the model reads is the `model_json_schema()` you inspected earlier, wrapped in the
`{"type": "function", ...}` envelope the API expects. `required` lists the fields without
defaults; `strict=True` and `extra="forbid"` still apply, so a call with `importance` as the
string `"0.9"` is refused before any handler runs, exactly like the bad `IntroCourseRequest`
payloads above.

Hand-build three tool calls and dispatch them yourself, with no model involved. Predict each
result: one valid write, one write that names a card number, and one with a string where a
float belongs. Then read the `memories` table directly to see which rows SQLite actually
holds. `invoke_with_reason` adds the shop rule that refused a write. A Pydantic refusal stays
`invalid_arguments`, because the dispatcher never copies raw arguments into an error message.


```python tags=["extension", "worked-example"]
manual_calls = [
    ToolCall(
        id="manual-1",
        name="remember_fact",
        arguments={
            "content": "Mango sells out most Saturday afternoons; order extra on Friday.",
            "importance": 0.7,
            "reason": "recurring pattern",
        },
    ),
    ToolCall(
        id="manual-2",
        name="remember_fact",
        arguments={
            "content": "Lucy's card number ends in 4421 for the dairy account.",
            "importance": 0.3,
            "reason": "billing detail",
        },
    ),
    ToolCall(
        id="manual-3",
        name="remember_fact",
        arguments={
            "content": "Pistachio is the slowest seller in winter.",
            "importance": "0.9",
            "reason": "seasonal pattern",
        },
    ),
]
manual_results = [memory_box.invoke_with_reason(memory_dispatcher, call) for call in manual_calls]
for call, result in zip(manual_calls, manual_results, strict=True):
    print(call.id, result)
assert manual_results[0] == {"ok": True, "value": {"stored": True, "memory_id": "lucy-llm-001"}}
assert manual_results[1]["error"] == "content_not_permitted"
assert manual_results[2] == {"ok": False, "error": "invalid_arguments"}
stored_rows = memory_box.db.connection.execute(
    "SELECT id, content, importance FROM memories ORDER BY id"
).fetchall()
for stored_row in stored_rows:
    print(dict(stored_row))
assert [row["id"] for row in stored_rows] == ["lucy-llm-001", "lucy-seed-001"]
memory_box.db.connection.close()
```

### Run the loop against a recorded transcript

`ScriptedModel` replays what a model replied at each step. It is not a stand-in pretending to
be live: the record says `scripted`, while the tool calls, the refusals and the SQLite rows
are real. Read the script as a conversation. Turn one searches memory before storing anything.
Turn two proposes two facts, one of which the shop refuses. Turn three adapts and stores the
arrangement without the secret. Turn four asks for no tools, which ends the loop.

Inside the loop a refusal arrives as an ordinary failed observation, `tool_failed`, because
`Dispatcher.invoke` never copies a raw error into the transcript. The policy's own ledger,
`memory_box.policy.refused`, keeps the reason for you and for the classroom. The cell starts
from a fresh shop memory holding only the seed row, so your manual write above is gone.
**Prediction:** how many rows will `memories` hold after this run, and which turn produces the
refusal?


```python tags=["extension", "worked-example"]
RECORDED_TURNS = [
    scripted_turn(calls=[{"name": "recall_facts", "arguments": {"query": "mango saturday dairy"}}]),
    scripted_turn(
        calls=[
            {
                "name": "remember_fact",
                "arguments": {
                    "content": "Mango sells out most Saturday afternoons; order extra on Friday.",
                    "importance": 0.7,
                    "reason": "recurring stock pattern",
                },
            },
            {
                "name": "remember_fact",
                "arguments": {
                    "content": "The dairy account is paid by card number ending 4421.",
                    "importance": 0.3,
                    "reason": "billing arrangement",
                },
            },
        ]
    ),
    scripted_turn(
        calls=[
            {
                "name": "remember_fact",
                "arguments": {
                    "content": "The dairy account is paid by card; the details stay with Lucy.",
                    "importance": 0.3,
                    "reason": "billing arrangement without the secret",
                },
            }
        ]
    ),
    scripted_turn(
        "Stored the Saturday mango pattern and the dairy billing arrangement. The shop refused "
        "the card number, so I kept only that a card is used."
    ),
]
LOOP_LIMITS = Limits(model_calls=8, tool_calls=16, seconds=120, output_tokens=4096)

scripted_box = seeded_toolbox()
scripted_result = run_loop(
    ScriptedModel(RECORDED_TURNS), scripted_box.dispatcher(), MEMORY_MESSAGES, limits=LOOP_LIMITS
)
print(describe(scripted_result, "scripted"))
print("Refused by policy:", scripted_box.policy.refused)
scripted_trace = tool_trace(scripted_result)
assert scripted_result.status == "COMPLETED"
assert [step["ok"] for step in scripted_trace] == [True, True, False, True]
assert scripted_box.written == ["lucy-llm-001", "lucy-llm-002"]
assert [reason for _, reason in scripted_box.policy.refused] == ["content_not_permitted"]
scripted_rows = scripted_box.db.connection.execute(
    "SELECT id, content FROM memories ORDER BY id"
).fetchall()
for scripted_row in scripted_rows:
    print(dict(scripted_row))
assert len(scripted_rows) == 3
scripted_box.db.connection.close()
```

### Run the same loop against a live model

The loop, the tools and the shop rules do not change. Only the model does. `build_model` looks
for an `OPENAI_API_KEY` in Colab's **Secrets** pane (the key icon in the left sidebar: add a
secret with that name and switch on notebook access for it), then in the process environment
for a local kernel. Without a key it returns the scripted model again and the record says so.
A missing key is a normal condition, never a silent substitution.

The live model is `gpt-5.1` through the `openai` library, which Colab ships preinstalled; on a
local kernel run `%pip install openai` once. One run costs a few thousand tokens. The model
receives the same two schemas and the same system message, and the shop policy still decides
every write. Compare the live record with the scripted one: what did the model search for
first, what did it store, what did it decline to store on its own, and what did the shop
refuse for it?

One more thing to watch. The policy bans the phrase `card number`, and a live model tends to
paraphrase: "card ending 4421" carries the same secret in different words. A phrase list is
weak against that; so `MemoryWritePolicy` also refuses a *pattern*, the word card followed by
digits. Read both rules in the embedded `memory_tools.py` and decide which one the live run
will trip.

**Prediction:** write down which facts from Lucy's message a careful assistant should keep.
Then run the cell and compare that list with the model's judgment, or with the recorded
transcript when the run is scripted; the printed source says which you are reading.


```python tags=["extension", "live-model"]
from sovereign_agent.llm_lab import DEFAULT_MODEL, build_model, resolve_api_key

chosen_model = build_model(RECORDED_TURNS, model=DEFAULT_MODEL)
print("Model source:", chosen_model.source, "| key found:", resolve_api_key() is not None)
live_box = seeded_toolbox()
live_result = run_loop(chosen_model, live_box.dispatcher(), MEMORY_MESSAGES, limits=LOOP_LIMITS)
print(describe(live_result, chosen_model.source))
print("Refused by policy:", live_box.policy.refused)
live_rows = live_box.db.connection.execute(
    "SELECT id, content, importance FROM memories ORDER BY id"
).fetchall()
for live_row in live_rows:
    print(dict(live_row))
assert live_result.status in {"COMPLETED", "MODEL_CALL_LIMIT", "TOOL_LIMIT", "MODEL_FAILED"}
# Whatever the model proposed, nothing the policy bans reached SQLite: re-run every rule.
for live_row in live_rows:
    assert live_box.policy.check(live_row["content"]) in {None, "duplicate_of_accepted_memory"}
assert len(live_rows) - 1 == len(live_box.written) <= live_box.policy.max_writes
live_box.db.connection.close()
```

### Challenge: tighten the shop's rules and save the evidence

The policy is data you can change. `seeded_toolbox(max_writes=1)` lets one write through;
`banned_phrases=("card number", "delivery")` refuses more. The next cell reruns the recorded
transcript under a one-write budget. **Predict before running:** the card-number write is still
refused, but is the reason still `content_not_permitted`? Read `MemoryWritePolicy.check` in the
embedded `memory_tools.py` and note the order of its rules. With a live key, rerun the live cell
under the same budget and explain what the model did after its second write was refused; a
model that keeps retrying the same write is a finding about the model, not a bug in your policy.

Explain in your notes which part of this run is a local fixture result and which claim needs
the live model: the scripted transcript proves the loop, the gate and the SQLite rows; only a
live run proves the model's judgment. The saved record keeps the two sources separate.


```python tags=["extension", "retained-evidence"]
tight_box = seeded_toolbox(max_writes=1)
tight_result = run_loop(
    ScriptedModel(RECORDED_TURNS), tight_box.dispatcher(), MEMORY_MESSAGES, limits=LOOP_LIMITS
)
print(describe(tight_result, "scripted"))
print("Refused by policy:", tight_box.policy.refused)
assert tight_box.written == ["lucy-llm-001"]
assert [reason for _, reason in tight_box.policy.refused] == [
    "write_budget_exhausted",
    "write_budget_exhausted",
]
tight_box.db.connection.close()

llm_lab_report = {
    "unit": "ch05-b",
    "scripted": {
        "status": scripted_result.status,
        "written": list(scripted_box.written),
        "refused": [reason for _, reason in scripted_box.policy.refused],
    },
    "session": {
        "source": chosen_model.source,
        "model": DEFAULT_MODEL if chosen_model.source == "live" else None,
        "status": live_result.status,
        "model_calls": live_result.model_calls,
        "written": list(live_box.written),
        "refused": [reason for _, reason in live_box.policy.refused],
        "answer": live_result.answer[:400],
    },
    "tightened": {"max_writes": 1, "refused": [reason for _, reason in tight_box.policy.refused]},
}
llm_report_path = COURSE_WORK / "ch05-b-llm-lab-report-v1.json"
llm_report_path.write_text(json.dumps(llm_lab_report, indent=2, sort_keys=True), encoding="utf-8")
print("Saved evidence:", llm_report_path)
print("LLM_LAB_REPORT=" + json.dumps(llm_lab_report["session"], sort_keys=True))
```

<!-- #region tags=["profrod-community"] -->
## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.

<!-- #endregion -->
