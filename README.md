# Theory of Automata Integrated Toolkit

Python 3 CLI implementation of the seven required Theory of Automata modules.

## Run

```powershell
cd "c:\Fast Fall 2026\TOA\Programing_Assignments"
python automata_toolkit.py
```

Run the automated suite (97 tests):

```powershell
python -m unittest -v test_automata_toolkit.py
```

There are no third-party runtime dependencies. `requirements.txt` records that the implementation uses only the Python standard library.

## Menu

Programs 1-7 are available from the menu. Option 8 runs epsilon elimination followed by unit elimination and prints each intermediate grammar. Enter `0` to exit.

## Grammar input

- Separate productions with semicolons or new lines: `S->AB;A->aA|a;B->bB|b`
- Separate alternatives with `|`.
- Use `epsilon`, `eps`, or `ε` for the empty production.
- The start symbol is entered separately for Programs 3, 5, 6, 7, and 8.
- Right sides are parsed using declared left-side nonterminals and single-character terminals.

## Modules

1. **Pumping lemma:** validates family, alphabet, positive pumping length, witness, and enumerates every valid decomposition; includes an optional manual-decomposition validator. Symbolic proof conclusions are restricted to supported witnesses.
2. **Simple Present CFG:** displays the productions, validates and generates controlled-vocabulary sentences, and prints parse trees.
3. **CFG derivations:** Earley membership, bounded distinct parse-tree enumeration, and leftmost/rightmost derivations.
4. **Guided CFGs:** equal-count strings, palindromes, balanced parentheses, canonical decimal divisibility, and bounded factorial-value languages.
5. **Right-linear conversion:** NFA, subset-construction DFA, 100 membership checks, DOT export, and optional exact comparison with a reference DFA.
6. **Epsilon elimination:** nullable fixed point, production expansion, empty-string preservation, and 50 membership comparisons.
7. **Unit elimination:** unit-closure graph, transformed productions, empty-string check, and 50 membership comparisons.
8. **Normalization pipeline:** epsilon elimination followed by unit elimination, exposing intermediate grammars.

Membership samples are sanity checks, not language-equivalence proofs. See [STUDENT_HELP.md](./STUDENT_HELP.md) for the technical report and input walkthroughs, and [TESTING_REPORT.md](./TESTING_REPORT.md) for test cases and recorded outcomes.
The combined Word report is [Theory_of_Automata_Submission_Report.docx](./Theory_of_Automata_Submission_Report.docx).

Each completed program execution is appended to `execution_history.jsonl`. Program 5 exports a Graphviz-compatible `right_linear_dfa.dot` file.
