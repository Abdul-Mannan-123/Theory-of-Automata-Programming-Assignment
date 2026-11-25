# Theory of Automata Programming Assignment

## Technical report and practical run guide

**Implementation:** Python 3 command-line toolkit
**Scope:** Seven assignment programs, integrated menu, and an epsilon-then-unit normalization pipeline
**Dependencies:** Python standard library only

## 1. Overview

The toolkit implements pumping-lemma experiments, a controlled Simple Present CFG, CFG membership and derivation tools, selected mathematical grammars, right-linear grammar conversion, epsilon elimination, and unit elimination. Each program prints its input, method, intermediate steps, result, verification notes, and elapsed time. Completed runs are appended to `execution_history.jsonl`.

The methods have bounded scopes; this is a teaching implementation, not a general English parser or proof assistant. Finite membership samples are sanity checks and never establish language equivalence by themselves.

## 2. Run the program

Open PowerShell or a VS Code terminal and type:

```powershell
cd "c:\Fast Fall 2026\TOA\Programing_Assignments"
python automata_toolkit.py
```

At `Choose program:`, type a number from the menu, then press Enter:

```text
1 - Pumping Lemma
2 - Simple Present English CFG
3 - Left/Right Derivation
4 - Guided Mathematical CFG
5 - Right-Linear Grammar to DFA
6 - Epsilon Production Elimination
7 - Unit Production Elimination
8 - Epsilon then Unit Elimination Pipeline
0 - Exit
```

At each prompt, type only the answer—not the prompt label—and press Enter. To skip an optional prompt, press Enter without typing anything.

Run the automated tests with:

```powershell
python -m unittest -v test_automata_toolkit.py
```

## 3. Grammar notation

- Separate grammar productions with semicolons or put each on a new line.
- Use `->` or `→` for the production arrow and `|` between alternatives.
- Write the empty production as `epsilon`, `eps`, or `ε`.
- Give the start symbol at its prompt; it must be one of the production left sides.
- Nonterminals are identified from production left sides. Multi-character uppercase-starting nonterminal names are supported.
- Grammar terminals are single characters. For example, `S->AB;A->aA|a;B->bB|b`.
- At a target-string prompt, press Enter to test the empty string.

## 4. How the programs work

### 4.1 Program 1 — Pumping lemma

Supports exactly `a^n b^n`, `a^n b^n c^n`, `a^n b^m`, and `a*`. It validates the alphabet, positive pumping length, witness membership, and `|w| >= p`, then enumerates all `x,y,z` decompositions satisfying `|xy| <= p` and `|y| > 0`. It tests pump counts 0–3. A symbolic non-regularity result is used only for supported witnesses in the first two language families; finite experiments alone return `INCONCLUSIVE`.

Example: at the four prompts enter `a^n b^n`, `a,b`, `2`, and `aabb`, one answer per line. You do not need to provide a decomposition.

The final optional prompt allows a manual decomposition check:

```text
Check a manual x,y,z decomposition too? (y/N):
```

Type `y` to enter `x`, `y`, and `z`; type nothing or `n` to skip. Use `lambda`, `epsilon`, `λ`, `ε`, or a blank answer to represent an empty component. The program validates that `xyz` equals the witness, `|xy| <= p`, and `|y| > 0`.

If a manual split is invalid (for example, `y=lambda`), the report prints why that split was rejected and still proceeds with the automatically enumerated valid decompositions. The overall result refers to the witness analysis, not to the optional manual split.

### 4.2 Program 2 — Simple Present CFG

The program prints the actual controlled CFG and asks for `validate` or `generate`. Validate mode reads a complete sentence and prints its parse tree when accepted. Generate mode asks how many sentences (1–100) to display; every displayed sentence comes from the grammar.

The vocabulary is intentionally finite: subjects `I`, `You`, `We`, `They`, `He`, `She`, `It`; ten base verbs (`play`, `study`, `work`, `eat`, `drive`, `read`, `write`, `watch`, `walk`, `teach`); and five objects (`cricket`, `English`, `home`, `football`, `books`). The grammar covers affirmative, negative, and interrogative forms with agreement rules.

Example validate inputs:

```text
Mode (validate/generate): validate
Enter a sentence: He plays cricket.
```

Expected: grammar match / `ACCEPT` and a parse tree. `He play cricket.` should be rejected because third-person singular requires the inflected verb.

### 4.3 Program 3 — CFG membership and derivations

Enter a grammar, start symbol, target string, and maximum parse-tree count. For example:

```text
Grammar: S->AB;A->aA|a;B->bB|b
Start symbol: S
Target string: aabb
Maximum parse trees (default 20): 20
```

The Earley-style parser decides membership. The program enumerates distinct parse trees up to the requested bound, and displays leftmost and rightmost derivations for each tree. If the bound truncates the tree list, membership is reported separately from the tree limit. Large chart computations have a resource guard and are reported as `RESOURCE_LIMIT`, not as non-membership.

### 4.4 Program 4 — Guided mathematical CFGs

Choose one of `equal-ab`, `palindrome`, `balanced`, `divisibility`, or `factorial`.

- For the first three, enter the test string at `Test string:`. Examples: `aabb` for `equal-ab`, `abba` for `palindrome`, and `()()` for `balanced`.
- For `divisibility`, enter an expression such as `125 divisible 5`. Supported divisors are 2, 3, 5, 7, 10, 12, and 24. Decimal strings must be canonical: `0` is valid, but `000` and negative numbers are not.
- For `factorial`, enter an expression such as `24 factorial 5`. The tested number is accepted if it equals `k!` for some `0 <= k <= N`; `N` is capped at 20.

The program prints each generated grammar, sample derivations, and a membership result. The factorial grammar is finite and bounded; this option is not a general grammar for arbitrary factorial descriptions.

### 4.5 Program 5 — Right-linear grammar to DFA

Enter a right-linear grammar, start symbol, maximum DFA-state count, then (optionally) a reference DFA as JSON. Legal production shapes include `A->aB`, `A->a`, and `A->epsilon`.

```text
Grammar: S->aS|bA|epsilon;A->bA|a
Start symbol: S
Maximum DFA states (default 10000): 10000
Optional reference DFA JSON (press Enter to skip):
```

The tool constructs an NFA and subset DFA, compares grammar/NFA/DFA membership on 100 generated strings, prints the DFA table, and exports `right_linear_dfa.dot`. The 100 samples are consistency checks only.

To request exact comparison against a complete reference DFA, paste one JSON object with `alphabet`, `start`, `accepting`, and `transitions`, for example:

```json
{"alphabet":["a"],"start":"q","accepting":["q"],"transitions":{"q":{"a":"q"}}}
```

The reference alphabet must match the grammar alphabet, and every state must define every alphabet transition. Exact comparison uses product-state reachability and returns a counterexample if the two DFAs differ. It has a product-state resource guard; hitting that guard means equivalence was not decided.

### 4.6 Program 6 — Epsilon-production elimination

Enter the grammar, start symbol, and maximum generated alternatives. Example:

```text
Grammar: S->AB;A->epsilon;B->b
Start symbol: S
Maximum generated alternatives (default 10000):
```

The report shows nullable-set iterations, original and transformed grammars, production counts, whether a fresh start was required, empty-string behavior, and 50 finite membership comparisons. The mathematical nullable-variable transformation—not those samples—is the basis for language preservation.

### 4.7 Program 7 — Unit-production elimination

Enter the grammar, start symbol, and maximum unit-closure visits:

```text
Grammar: S->A;A->B;B->b
Start symbol: S
Maximum unit-closure visits (default 100000):
```

The report shows unit-closure reachability, original and transformed grammars, empty-string behavior, remaining unit rules, and 50 finite membership comparisons. A completed transformation should have no unit rules remaining.

### 4.8 Program 8 — Epsilon then unit pipeline

Enter a grammar, start symbol, and operation limit. The pipeline prints the original grammar, the result after epsilon elimination, the result after unit elimination, unit closures, empty-string/membership checks, and final status.

```text
Enter grammar for epsilon then unit elimination: S->A;A->epsilon|a
Start symbol: S
Maximum transformation operations (default 100000):
```

`PIPELINE_COMPLETE` means the transformations and bounded checks completed; finite comparisons are not a proof of equivalence.

## 5. Reproducible interactive test cases

For each table, choose its program number from the menu. Unless shown otherwise, prompts not listed in a row use the normal example values and optional prompts are skipped by pressing Enter.

### Program 1

Enter formula / alphabet / `p` / witness:

| Inputs | Expected result |
|---|---|
| `a^n b^n` / `a,b` / `2` / `aabb` | `NON_REGULAR_PROVED`; decomposition trace |
| `a^n b^n c^n` / `a,b,c` / `2` / `aabbcc` | `NON_REGULAR_PROVED` |
| `a^n b^m` / `a,b` / `2` / `aabb` | `INCONCLUSIVE` |
| `a*` / `a` / `2` / `aa` | `INCONCLUSIVE` |
| `a^n b^n` / `a,b` / `0` / `ab` | `INVALID_INPUT`; `p` must be positive |
| `a^n b^n` / `a,b` / `3` / `ab` | `INVALID_INPUT`; witness shorter than `p` |
| `a^n b^n` / `a,b` / `2` / `aab` | `INVALID_INPUT`; witness not in language |
| `a^n b^n` / blank alphabet / `2` / `aabb` | `INVALID_INPUT`; alphabet required |
| `a^n` / `a` / `2` / `aa` | `UNSUPPORTED_LANGUAGE` |
| `a*` / `a` / `1` / `lambda` | Empty string recognized, then `INVALID_INPUT` because `|w| < p` |
| `a^n b^n` / `a,b` / `2` / `aabb`; manual `x=a`, `y=lambda`, `z=abb` | Manual split rejected (`y` must be nonempty); automatic witness analysis continues and reports `NON_REGULAR_PROVED` |

### Program 2

Choose `validate` for sentence tests. Choose `generate`, then a limit such as `10`, to display sentences derived from the grammar.

| Sentence | Expected result |
|---|---|
| `He plays cricket.` | Accept |
| `He play cricket.` | Reject |
| `She does not play cricket.` | Accept |
| `She does not plays cricket.` | Reject |
| `Does he play cricket?` | Accept |
| `Does he plays cricket?` | Reject |
| `They play cricket.` | Accept |
| `They plays cricket.` | Reject |
| `Do you study English?` | Accept |
| `Does they study English?` | Reject |
| `I does not work.` | Reject |
| Blank sentence | `INVALID_INPUT` |

### Program 3

For each row, use the grammar, start symbol, target, and tree limit shown:

| Grammar | Start | Target | Limit | Expected |
|---|---:|---|---:|---|
| `S->AB;A->aA|a;B->bB|b` | `S` | `aabb` | 20 | `MEMBER`; leftmost/rightmost traces |
| `S->AB;A->aA|a;B->bB|b` | `S` | `ababa` | 20 | `NON_MEMBER` |
| `S->AZ;A->a` | `S` | `a` | 20 | `INVALID_INPUT`; undefined `Z` |
| `S->epsilon` | `S` | blank | 20 | `MEMBER`; epsilon derivation |
| `S->Sa|a` | `S` | `aaa` | 20 | `MEMBER`; left recursion |
| `S->A;A->S|a` | `S` | `a` | 20 | `MEMBER`; unit cycle with exit |
| `S->SS|a` | `S` | `aaa` | 20 | `MEMBER`; ambiguous trees enumerated |
| Blank grammar | `S` | `a` | 20 | `INVALID_INPUT` |
| `S->a` | `S` | `a` | 0 | `INVALID_INPUT`; tree limit must be positive |
| `Start->AUnit;AUnit->a` | `Start` | `a` | 20 | `MEMBER`; multi-character nonterminal names |

### Program 4

Select the problem first, then enter the test string or expression:

| Problem | Test input | Expected |
|---|---|---|
| `equal-ab` | `aabb` | Accept |
| `equal-ab` | `aab` | Reject |
| `palindrome` | `abba` | Accept |
| `palindrome` | `abab` | Reject |
| `balanced` | `()()` | Accept |
| `balanced` | `(()` | Reject |
| `divisibility` | `125 divisible 5` | Accept |
| `divisibility` | `126 divisible 2` | Accept |
| `divisibility` | `135 divisible 10` | Reject |
| `divisibility` | `123 divisible 3` | Accept |
| `divisibility` | `121 divisible 7` | Reject |
| `divisibility` | `24 divisible 24` | Accept |
| `divisibility` | `36 divisible 24` | Reject |
| `divisibility` | `000 divisible 5` | `INVALID_INPUT`; leading zeros |
| `factorial` | `24 factorial 5` | Accept |
| `factorial` | `25 factorial 5` | Reject |
| `factorial` | `24 factorial 21` | `INVALID_INPUT`; bound exceeds 20 |

### Program 5

Enter the grammar/start/limit as in section 4.5; press Enter to skip the optional reference unless testing exact equivalence.

| Grammar or reference case | Expected |
|---|---|
| `S->aS|bA|epsilon;A->bA|a`, start `S` | NFA and DFA tables; 100 comparisons; DOT export |
| `S->a|b`, start `S` | Converted; fresh accepting state |
| `S->epsilon`, start `S` | Converted; empty string accepted |
| `S->aSb`, start `S` | `INVALID_INPUT`; not right-linear |
| `S->SS`, start `S` | `INVALID_INPUT`; unsupported production form |
| `S->aA`, start `S` | `INVALID_INPUT`; undefined variable |
| `S->a|a`, start `S` | Converted with duplicate alternatives deduplicated |
| Blank grammar | `INVALID_INPUT` |
| `S->a;A->b`, start `S` | Converted; unreachable-variable warning |
| `S->aS|epsilon`, start `S`, reference `{"alphabet":["a"],"start":"q","accepting":["q"],"transitions":{"q":{"a":"q"}}}` | Exact `EQUIVALENT` |
| Same grammar; reference has empty accepting list | Exact `NOT EQUIVALENT`, with counterexample |

### Programs 6 and 7

Use the grammar and start prompts. For Program 6, the last prompt is the maximum generated alternatives. For Program 7, it is the maximum unit-closure visits.

| Program | Grammar | Expected |
|---|---|---|
| 6 | `S->AB;A->epsilon;B->b` | Nullable `A`; `S` gains `B` |
| 6 | `S->ABC;A->epsilon;B->epsilon;C->c` | All omission alternatives generated |
| 6 | `S->A;A->epsilon` | Indirect nullability; fresh start preserves epsilon |
| 6 | `S->a|epsilon` | Fresh start preserves epsilon |
| 6 | `S->a|b` | No fresh start or new epsilon |
| 6 | `S->aA;A->b` | No epsilon rules remain |
| 6 | `S->A|A|a;A->epsilon` | Duplicate alternatives deduplicated |
| 6 | `S->A;A->S|epsilon` | Nullable cycle terminates |
| 6 | `S->A` | `INVALID_INPUT`; undefined variable |
| 6 | Blank grammar | `INVALID_INPUT` |
| 7 | `S->A;A->a` | `S` receives `a`; no unit rules remain |
| 7 | `S->A;A->B;B->b` | Transitive closure gives `S->b` |
| 7 | `A->B;B->A` | Cycle terminates; empty language preserved |
| 7 | `S->a|b` | Unchanged; no unit rules |
| 7 | `S->A;A->epsilon` | Empty-string behavior preserved |
| 7 | `S->A|B;A->C;B->C;C->c` | `S` receives `c` once |
| 7 | `S->A` | `INVALID_INPUT`; undefined variable |
| 7 | `S->A;A->S` | Unit-only cycle terminates |
| 7 | `S a` | `INVALID_INPUT`; malformed production |
| 7 | `S->a;A->b` | Unreachable variable harmless; no unit rules |

### Program 8

| Grammar | Expected |
|---|---|
| `S->A;A->epsilon|a`, start `S` | Both intermediate grammars displayed; epsilon preserved |
| `S->A;A->B;B->b`, start `S` | Epsilon stage then unit closure; final `S` derives `b` |
| Blank grammar | `INVALID_INPUT` |

## 6. Automated test report summary

The current suite is in [test_automata_toolkit.py](./test_automata_toolkit.py). It verifies 97 test cases: Program 1 (13), Program 2 (11), Program 3 (11), Program 4 helpers and grammars (20), Program 5 (12), Program 6 (11), Program 7 (11), plus 8 shared grammar tests. Run it with the command in section 2. The detailed test-to-input/result table is in [TESTING_REPORT.md](./TESTING_REPORT.md).

## 7. Status labels and known limits

- `NON_REGULAR_PROVED` is emitted only when the supported symbolic pumping argument applies to the selected witness.
- `INCONCLUSIVE` means the finite pumping experiments did not establish regularity or non-regularity.
- `INVALID_INPUT` means a validation rule failed; `UNSUPPORTED_LANGUAGE` means Program 1 does not implement that formula.
- `RESOURCE_LIMIT` means computation stopped at a documented guard; it does not mean the target is a non-member.
- `ACCEPT` / `REJECT` describe the tested input. `MEMBER` / `NON_MEMBER` describe CFG membership.
- Program 2 is intentionally restricted to its listed vocabulary and grammar forms.
- Program 4 recognizes only the documented mathematical-language families; factorial is bounded by 20.
- For factorial bounds below 3, fewer than three distinct factorial strings exist; Program 4 displays the available derivations rather than inventing additional members.
- Programs 5–7 and the pipeline include finite comparison suites. Those samples are checks, not proofs; correctness relies on the transformation/construction algorithms.
- The parser uses one-character terminals. It supports multi-character nonterminal names, but not general tokenized terminal strings.
- The DOT export is a text diagram source and can be rendered with Graphviz; a rendered image is not included.

## 8. Formal definitions, pseudocode, complexity, and correctness

### 8.1 Formal definitions

- An alphabet `Σ` is a finite set of symbols; `Σ*` is the set of all finite strings over it. A language is a subset of `Σ*`.
- The pumping lemma for a regular language states that there is a positive `p` such that every `w` in the language with `|w| >= p` can be written `w=xyz`, with `|xy| <= p` and `|y| > 0`, and `xy^i z` belongs to the language for every `i >= 0`.
- A CFG is `G=(V,Σ,P,S)`: nonterminals `V`, terminals `Σ`, productions `P`, and start symbol `S`. `L(G)` contains the terminal strings derivable from `S`; epsilon is the empty string.
- A right-linear production has a terminal followed optionally by one nonterminal, or is epsilon: `A->aB`, `A->a`, or `A->epsilon`. This restriction permits finite-automaton construction; arbitrary CFGs are not converted to DFAs.

### 8.2 Program 1 — Pumping-lemma analysis

**Pseudocode**

```text
validate selected family, alphabet, p, and witness w
reject unless w is in the family and |w| >= p
for i from 0 to p:
    for j from 1 to p-i:
        x = w[0:i]; y = w[i:i+j]; z = w[i+j:]
        test membership of x + y^k + z for k = 0,1,2,3
apply a symbolic rule only for a supported proof-family/witness pattern
otherwise report INCONCLUSIVE
```

For `n=|w|`, the program visits `p(p+1)/2` valid decompositions, with `p<=n`. The output contains four pumped strings per decomposition; time and stored trace size are `O(p²(n+p))`, excluding constant-time status formatting. The enumeration is resource-capped.

**Correctness:** The nested index bounds enumerate exactly the splits satisfying both pumping constraints. Family membership is checked with the selected language recognizer. The program does not infer a universal proof from finite pump values; only the explicit supported symbolic argument can produce `NON_REGULAR_PROVED`.

### 8.3 Program 2 — Simple Present CFG

**Pseudocode**

```text
construct Start -> Affirmative | Negative | Interrogative
use separate subject groups for third-person singular and other subjects
use BaseVerb after do/does auxiliaries; use ThirdVerb only in affirmative third-person singular
validate: tokenize sentence, then enumerate bounded CFG parse trees
generate: expand the CFG and display selected sentences with parse trees
```

The vocabulary is finite: 7 subject words representing 8 person/number combinations (`You` occurs as singular and plural), 10 regular base verbs, and 5 objects. Sentence generation yields 1,050 unique sentences. Generation time/storage are proportional to the generated strings' total size; parsing is bounded by the fixed grammar and parse-tree limit.

**Correctness:** Agreement is encoded in the production alternatives: third-person singular affirmative clauses select `ThirdVerb`, while negative and interrogative clauses use the appropriate `Does` form and `BaseVerb`. A sentence is accepted only if it has a derivation from the CFG, not merely because it is nonempty.

### 8.4 Program 3 — CFG membership and derivations

**Pseudocode**

```text
parse and validate grammar G and explicit start symbol S
run Earley predictor, scanner, and completer over target w
enumerate distinct parse trees up to the user's tree limit
for each tree, expand leftmost and rightmost nonterminals in turn
report membership separately from parse-tree truncation/resource limits
```

For input length `n` and grammar size `|G|`, Earley membership has worst-case time `O(n³|G|)` and chart space `O(n²|G|)` under the standard CFG model. Tree enumeration can be exponential for ambiguous grammars and is bounded by the requested tree count; Earley chart processing also has a resource guard.

**Correctness:** Earley parsing recognizes CFG membership, including epsilon, recursion, and cycles. Each displayed derivation is read from a parse tree, applying the leftmost or rightmost eligible nonterminal at each step. A tree limit never turns an established member into a non-member.

### 8.5 Program 4 — Guided mathematical CFG construction

**Pseudocode**

```text
if equal-ab: use S -> a S b | epsilon
if palindrome: use S -> a S a | b S b | a | b | epsilon
if balanced parentheses: use S -> ( S ) S | epsilon
if decimal divisibility: construct remainder states r with transition (10r+d) mod divisor
if bounded factorial: build a trie for the decimal strings in {n! | 0 <= n <= N}
parse the supplied example against the constructed grammar
```

Direct string checks run in `O(n)`. The remainder-grammar construction has `O(d*10)` transitions for divisor `d`; membership then follows the generated automaton/grammar. The factorial trie is built in time proportional to the total digits in its bounded values.

**Correctness:** The equal-count and balanced grammars add/remove matching symbols in recursive layers. The palindrome grammar adds matching ends around a shorter palindrome, with single-symbol and epsilon bases. Remainder-state transitions maintain the decimal-prefix remainder invariant; acceptance occurs exactly at remainder zero. A trie accepts exactly the listed factorial strings. Numeric syntax validation rejects noncanonical decimal forms.

### 8.6 Program 5 — Right-linear grammar to DFA

**Pseudocode**

```text
validate each production is A->aB, A->a, or A->epsilon
map nonterminals to NFA states; map terminal-only rules to a fresh accepting state
mark epsilon-producing states accepting
start with DFA subset {S}; repeatedly compute moves for each alphabet symbol
compare grammar/NFA/DFA on 100 generated strings
if supplied, explore product states against the reference DFA for exact equivalence
```

For `q` NFA states, subset construction can produce at most `2^q` DFA states; each state-symbol transition examines the NFA moves. Exact reference comparison visits at most `|Q_generated|*|Q_reference|` product states and processes each alphabet symbol once. Both computations have explicit resource limits.

**Correctness:** Each NFA path corresponds to a right-linear derivation, with a terminal-only production ending at the fresh final state. The subset construction tracks all NFA states reachable after the same input prefix, preserving acceptance. Product-state reachability is exact: a reachable pair with different acceptance yields a counterexample; exhausting reachable pairs proves equivalence. The separate 100-string comparison is only a sanity check.

### 8.7 Program 6 — Epsilon-production elimination

**Pseudocode**

```text
nullable = empty set
repeat: add A when A has an epsilon rule or a rule consisting only of nullable variables
until nullable stops changing
for every production, generate all omissions of nullable occurrences
remove empty alternatives from ordinary variables and deduplicate
if S was nullable, add fresh S0 -> S | epsilon and make S0 the start
compare original/transformed membership on 50 finite samples
```

The fixed point takes at most `|V|+1` scans; each scan visits production right sides. A right side with `k` nullable occurrences can yield up to `2^k` alternatives, so output generation is exponential in the largest such `k` and has a configurable cap.

**Correctness:** The fixed point captures direct and indirect nullability. Every subset of nullable occurrences can disappear in a derivation, and enumerating those subsets preserves the nonempty derivations. The fresh start preserves epsilon without allowing the original start to disappear from other derivations. The finite comparisons detect sample mismatches but do not replace this argument.

### 8.8 Program 7 — Unit-production elimination

**Pseudocode**

```text
build directed edges A -> B for unit productions
for each A, compute all variables reachable from A
copy each reachable variable's non-unit productions to A
deduplicate alternatives and remove all unit productions
check epsilon behavior and compare 50 finite strings
```

For `|V|` variables and `|E|` unit edges, depth-first reachability from every variable costs `O(|V|(|V|+|E|))`; copying productions costs proportional to the closure and productions copied. A closure-visit limit prevents unbounded work.

**Correctness:** A unit chain from `A` to `B` exists exactly when `B` is reachable from `A`. Replacing that chain by any non-unit production of `B` preserves the derived terminal strings. Cycles terminate because each variable is visited once per start vertex. The resulting grammar contains no unit rules.

### 8.9 Program 8 — Combined normalization pipeline

The pipeline runs the Program 6 transformation followed by the Program 7 transformation and displays both intermediate grammars. Its work is bounded by the two configured transformation limits; the 50 finite comparisons are diagnostic checks. Correctness follows from applying the language-preserving argument for each stage in sequence.

## 9. Source files and academic disclosure

- [automata_toolkit.py](./automata_toolkit.py) — integrated implementation and CLI.
- [test_automata_toolkit.py](./test_automata_toolkit.py) — automated tests.
- [README.md](./README.md) — quick-start reference.
- [TESTING_REPORT.md](./TESTING_REPORT.md) — test cases and outcomes.
- [requirements.txt](./requirements.txt) — standard-library-only dependency declaration.

AI assistance was used while developing code and documentation.
