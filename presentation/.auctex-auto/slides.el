;; -*- lexical-binding: t; -*-

(TeX-add-style-hook
 "slides"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("beamer" "bigger")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("inputenc" "utf8") ("fontenc" "T1") ("microtype" "activate={true,nocompatibility}" "final" "tracking=true" "kerning=true" "spacing=true" "factor=1100" "stretch=10" "shrink=10") ("xcolor" "dvipsnames" "svgnames") ("fixltx2e" "") ("longtable" "") ("float" "") ("wrapfig" "") ("rotating" "") ("ulem" "normalem") ("textcomp" "") ("marvosym" "") ("wasysym" "") ("multicol" "") ("hyperref" "" "colorlinks=true" "linkcolor=DarkBlue" "citecolor=BrickRed" "urlcolor=DarkGreen") ("minted" "") ("biblatex" "style=apa" "backend=bibtex") ("amsmath" "") ("amsfonts" "") ("amssymb" "") ("amsthm" "") ("enumerate" "") ("multirow" "") ("array" "") ("graphicx" "") ("lscape" "") ("lastpage" "") ("mathabx" "") ("csquotes" "") ("fontawesome" "") ("tikz" "") ("subfig" "") ("appendixnumberbeamer" "")))
   (TeX-run-style-hooks
    "latex2e"
    "beamer"
    "beamer10"
    "inputenc"
    "fontenc"
    "microtype"
    "xcolor"
    "hyperref"
    "fixltx2e"
    "graphicx"
    "longtable"
    "float"
    "wrapfig"
    "rotating"
    "ulem"
    "amsmath"
    "textcomp"
    "marvosym"
    "wasysym"
    "multicol"
    "amssymb"
    "minted"
    "biblatex"
    "amsfonts"
    "amsthm"
    "enumerate"
    "multirow"
    "array"
    "lscape"
    "lastpage"
    "mathabx"
    "csquotes"
    "fontawesome"
    "tikz"
    "subfig"
    "appendixnumberbeamer")
   (LaTeX-add-labels
    "sec:org5d5ef09"
    "fig:openhw"
    "fig:inria"
    "sec:org0d7a0a5"
    "roadmap"
    "sec:org6aca28c"
    "sec:org2f4558b"
    "sec:org982bb94"
    "sec:org0b8bb41"
    "fig:iot"
    "fig:iotvar_energy"
    "sec:org5047c6f"
    "sec:org176ca70"
    "fig:hardware"
    "fig:process"
    "fig:process_2"
    "sec:org09f624d"
    "fig:results_1"
    "fig:results_2"
    "tab:metrics_results"
    "tab:metrics_results_20segs"
    "fig:results_3"
    "sec:org832806c"))
 :latex)

