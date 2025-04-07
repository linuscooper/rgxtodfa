# RegEx Password Demo

A small side project exploring the use of regular expressions and finite automata for password verification. 

The core idea: having users enter two different strings that both match a shared pattern — effectively doubling the entropy of the password without significantly increasing the memory load.

## How It Works

Under the hood, the regex is converted into a Deterministic Finite Automaton using Brzozowski derivatives, incrementally building a DFA by repeatedly applying derivatives of the regex with respect to each character in the input string.

Currently it supports the following operations:

- Kleene Star: a*
- Union: a|b
- Concatenation: ab
- Groups: (a|b)

## Built With

- **HTML5 + CSS3**
- **Vanilla JavaScript (ES Modules)**
- [**Pyodide**](https://pyodide.org) – to run Python code client-side
- [**Viz.js**](https://github.com/mdaines/viz.js) – for Graphviz-style rendering in the browser

---

Made out of curiosity and for exploration.
