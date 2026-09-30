\newpage

# LaTeX Preamble

This file contains LaTeX packages and commands for the Cognitive Integrity Framework (Part 3: Practitioner Guide and Applications) manuscript.

```latex
% Core mathematical packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
% Keep long deployment prose and references within the text block.
\setlength{\emergencystretch}{3em}
\sloppy

% Algorithm formatting
\usepackage{algorithm}
\usepackage{algpseudocode}

% Tables
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{array}
\usepackage{longtable}

% Graphics and floats
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{pgfplots}
\usetikzlibrary{shapes,arrows,positioning,calc,fit,backgrounds}
\pgfplotsset{compat=1.18}
\usepackage{float}
\floatplacement{figure}{H}

% Typography and layout
\usepackage{microtype}
\usepackage{setspace}
\setstretch{1.15}

% Page layout (slightly smaller margins for academic journal style)
\usepackage[margin=0.75in]{geometry}

% Running headers/footers
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead[L]{\small\itshape{CIF Practical \& Applications}}
\fancyhead[R]{\small\thepage}
\fancyfoot{}

% Caption formatting
\usepackage{caption}
\captionsetup{font=small, labelfont=bf, margin=10pt}

% Colored boxes for callouts
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}

% Cross-referencing with smart naming
\usepackage{hyperref}
\usepackage[capitalise,noabbrev,nameinlink]{cleveref}

% Hyperlink styling
\hypersetup{
    colorlinks=true,
    linkcolor=blue!70!black,
    filecolor=blue!70!black,
    urlcolor=teal!80!black,
    citecolor=teal!80!black
}

% Configure cleveref for custom environments
\crefname{definition}{Definition}{Definitions}
\crefname{theorem}{Theorem}{Theorems}
\crefname{lemma}{Lemma}{Lemmas}
\crefname{property}{Property}{Properties}
\crefname{corollary}{Corollary}{Corollaries}
\crefname{algorithm}{Algorithm}{Algorithms}
\crefname{equation}{Equation}{Equations}
\crefname{table}{Table}{Tables}
\crefname{figure}{Figure}{Figures}

% Theorem environments with consistent numbering
\newtheorem{definition}{Definition}[section]
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{property}{Property}[section]
\newtheorem{axiom}{Axiom}[section]
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}

% Code listings and raw implementation examples in the manuscript
\usepackage{listings}
\lstset{basicstyle=\ttfamily\small,breaklines=true,columns=fullflexible}

% Math operators
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator{\sign}{sign}
\DeclareMathOperator{\KL}{KL}
\DeclareMathOperator{\Tr}{Tr}

% Custom commands for notation consistency
\newcommand{\calA}{\mathcal{A}}
\newcommand{\calB}{\mathcal{B}}
\newcommand{\calC}{\mathcal{C}}
\newcommand{\calD}{\mathcal{D}}
\newcommand{\calF}{\mathcal{F}}
\newcommand{\calG}{\mathcal{G}}
\newcommand{\calH}{\mathcal{H}}
\newcommand{\calI}{\mathcal{I}}
\newcommand{\calM}{\mathcal{M}}
\newcommand{\calO}{\mathcal{O}}
\newcommand{\calP}{\mathcal{P}}
\newcommand{\calS}{\mathcal{S}}
\newcommand{\calT}{\mathcal{T}}
\newcommand{\calW}{\mathcal{W}}
% Note: \Phi is a standard LaTeX command, do not redefine

% Trust notation
\newcommand{\trust}[2]{\mathcal{T}_{#1 \to #2}}
\newcommand{\trustt}[3]{\mathcal{T}_{#1 \to #2}^{#3}}

% Belief notation
\newcommand{\belief}[2]{\mathcal{B}_{#1}(#2)}
\newcommand{\belieft}[3]{\mathcal{B}_{#1}^{#2}(#3)}

% Cognitive state
\newcommand{\cogstate}[1]{\sigma_{#1}}

% Attack notation
\newcommand{\attack}[1]{\mathcal{A}_{#1}}
\newcommand{\adversary}[1]{\Omega_{#1}}

% Defense notation
\newcommand{\firewall}{\mathcal{F}}
\newcommand{\sandbox}{\mathcal{S}_{box}}

% Probability and expectation
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\indicator}{\mathbb{1}}

% QED symbol
\renewcommand{\qedsymbol}{$\blacksquare$}

% Front matter opens on the cover/title page (no list of figures/tables precedes it).
```
