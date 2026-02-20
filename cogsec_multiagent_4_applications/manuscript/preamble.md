\newpage

# LaTeX Preamble

This file contains LaTeX packages and commands for the Cognitive Security Framework manuscript.

```latex
% Core mathematical packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}

% Algorithm formatting
\usepackage{algorithm}
\usepackage{algpseudocode}

% Tables
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{array}
\usepackage{longtable}

% Graphics
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{pgfplots}
\usetikzlibrary{shapes,arrows,positioning,calc,fit,backgrounds}
\pgfplotsset{compat=1.18}

% Cross-referencing with smart naming
\usepackage{hyperref}
\usepackage[capitalise,noabbrev,nameinlink]{cleveref}

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
\crefname{observation}{Observation}{Observations}
\crefname{formalization}{Formalization}{Formalizations}
\crefname{principle}{Principle}{Principles}

% Theorem environments with consistent numbering
\newtheorem{definition}{Definition}[section]
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{property}{Property}[section]
\newtheorem{axiom}{Axiom}[section]
\newtheorem{observation}[theorem]{Observation}
\newtheorem{formalization}[theorem]{Formalization}
\newtheorem{principle}[theorem]{Principle}

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

% Unicode character support
\usepackage{newunicodechar}
\newunicodechar{°}{\ensuremath{{}^{\circ}}}

% Page Layout (Slightly smaller margins)
\usepackage[margin=1in]{geometry}

% Hyperlink Styling
\hypersetup{
    colorlinks=true,
    linkcolor=red,
    filecolor=red,
    urlcolor=red,
    citecolor=red
}
```
