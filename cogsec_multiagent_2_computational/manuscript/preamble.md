\newpage

# LaTeX Preamble

This file contains LaTeX packages and commands for the Cognitive Security Framework manuscript.

```latex
% Core mathematical packages
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}

% Dense 9pt body via class-agnostic global rescaling
\usepackage{fontsize}
\changefontsize[11pt]{9pt}

% Category theory and diagrammatic formalisms (Section 8)
\usepackage{tikz-cd}          % Commutative diagrams (functors, natural transformations)
\usepackage{stmaryrd}         % ⟦⟧ semantic brackets, \llbracket, \rrbracket
\usepackage{mathrsfs}         % \mathscr for category names (\mathscr{C}, \mathscr{D})

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
\usetikzlibrary{shapes,arrows,positioning,calc,fit,backgrounds,cd}
\pgfplotsset{compat=1.18}

% Lists of figures and tables (injected by auto_number_figures.py)
\usepackage{tocloft}          % Fine-grained LoF/LoT formatting
\renewcommand{\cftfigpresnum}{Fig.~}
\renewcommand{\cfttabpresnum}{Table~}

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
% Category-theory specific environments
\crefname{axiom}{Axiom}{Axioms}
\crefname{proposition}{Proposition}{Propositions}
\crefname{remark}{Remark}{Remarks}

% Theorem environments with consistent numbering
\newtheorem{definition}{Definition}[section]
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{property}{Property}[section]
\newtheorem{axiom}{Axiom}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{remark}[theorem]{Remark}
\newtheorem{warning}[theorem]{Warning}
\newtheorem{example}[theorem]{Example}

% Code listings and raw implementation examples in the supplements
\usepackage{listings}
\usepackage{seqsplit}
\protected\def\breaktt#1{\begingroup\ttfamily\seqsplit{#1}\endgroup}
\lstset{basicstyle=\ttfamily\small,breaklines=true,columns=fullflexible}

% Math operators
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator{\sign}{sign}
\DeclareMathOperator{\KL}{KL}
\DeclareMathOperator{\Tr}{Tr}
% Category-theory operators
\DeclareMathOperator{\Ob}{Ob}      % Objects of a category
\DeclareMathOperator{\Hom}{Hom}    % Hom-sets
\DeclareMathOperator{\colim}{colim} % Colimit
\DeclareMathOperator{\DR}{DR}       % Detection rate

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

% Category-theory shorthand macros (Section 8)
\newcommand{\Def}{\mathbf{Def}}         % Defense category
\newcommand{\Arch}{\mathbf{Arch}}       % Architecture category
\newcommand{\Ldef}{\mathcal{L}_{\mathrm{def}}}  % Defense lattice
\newcommand{\bBot}{\bot_{\mathcal{L}}}  % Lattice bottom
\newcommand{\bTop}{\top_{\mathcal{L}}}  % Lattice top
\newcommand{\PipeT}{\mathbb{T}}         % Pipeline monad
\newcommand{\LanF}{\mathrm{Lan}}        % Left Kan extension
\newcommand{\RanF}{\mathrm{Ran}}        % Right Kan extension

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

% Page Layout (Tighter margins for denser content)
\usepackage[margin=0.75in]{geometry}

% Hyperlink Styling
\hypersetup{
    colorlinks=true,
    linkcolor=red,
    filecolor=red,
    urlcolor=red,
    citecolor=red
}

% Front matter opens on the cover/title page (no list of figures/tables precedes it).
```
