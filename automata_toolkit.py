"""Interactive Theory of Automata assignment toolkit.

This module contains Programs 1-7 plus a menu-driven command-line interface.
"""

import itertools
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


EPSILON = "ε"


class ResourceLimitError(Exception):
    """Raised when a configured computation limit is exceeded."""


def normalize_eps(s: str) -> str:
    return EPSILON if s.strip() in ("", EPSILON, "epsilon") else s.strip()


@dataclass(frozen=True)
class Grammar:
    variables: Tuple[str, ...]
    terminals: Tuple[str, ...]
    start: str
    productions: Dict[str, Tuple[str, ...]]


def parse_alternatives(rule: str) -> List[str]:
    alternatives = []
    for item in rule.split("|"):
        item = item.strip()
        if item == "":
            raise ValueError("An alternative cannot be empty; use ε for epsilon.")
        alternatives.append(EPSILON if item.lower() in ("epsilon", "eps") else item)
    return alternatives


def tokenize_rhs(rhs: str, variables: Iterable[str]) -> Tuple[str, ...]:
    if rhs == EPSILON:
        return ()
    variable_names = sorted(variables, key=len, reverse=True)
    tokens: List[str] = []
    position = 0
    while position < len(rhs):
        if rhs[position].isspace():
            position += 1
            continue
        if rhs[position].isupper():
            match = next((name for name in variable_names
                          if rhs.startswith(name, position)), None)
            if match is None:
                raise ValueError("Undefined nonterminal near: " + rhs[position:])
            tokens.append(match)
            position += len(match)
        else:
            tokens.append(rhs[position])
            position += 1
    return tuple(tokens)


def parse_grammar(text: str, start_symbol: Optional[str] = None) -> Grammar:
    text = text.strip()
    if not text:
        raise ValueError("Grammar input is empty.")

    lines = [line.strip() for line in text.replace(";", "\n").splitlines() if line.strip()]
    variables: Set[str] = set()
    terminals: Set[str] = set()
    productions: Dict[str, List[str]] = {}
    start: Optional[str] = None

    for line in lines:
        if "→" in line:
            left, right = line.split("→", 1)
        elif "->" in line:
            left, right = line.split("->", 1)
        else:
            raise ValueError("Malformed production: expected 'A→aB' or 'A->aB'.")
        left = left.strip()
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", left):
            raise ValueError("Malformed nonterminal: " + left)
        variables.add(left)
        if start is None:
            start = left
        productions.setdefault(left, [])
        productions[left].extend(parse_alternatives(right))

    if start is None:
        raise ValueError("Grammar has no productions.")
    if start_symbol is not None:
        if not start_symbol:
            raise ValueError("Missing start symbol.")
        if start_symbol not in variables:
            raise ValueError("Start symbol is not a declared nonterminal: " + start_symbol)
        start = start_symbol

    for left, rhs_list in productions.items():
        for rhs in rhs_list:
            if EPSILON in rhs and rhs != EPSILON:
                raise ValueError("Epsilon must be the entire right-hand side.")
            terminals.update(symbol for symbol in tokenize_rhs(rhs, variables)
                             if symbol not in variables)

    return Grammar(tuple(sorted(variables)), tuple(sorted(terminals)), start,
                   {v: tuple(sorted(set(rs), key=lambda x: str(x))) for v, rs in productions.items()})


def report(program: str, user_input: str, validation: str, original: str,
           algorithm: str, steps: List[str], intermediate: str, result: str,
           verification: str, warnings: str = ""):
    elapsed = time.perf_counter() - report_start
    display = lambda value: (str(value).replace(EPSILON, "epsilon")
                             .replace("λ", "lambda").replace("Σ", "Sigma")
                             .replace("→", "->").replace("∅", "EMPTY"))
    print("\n" + "=" * 72)
    print("Program Name:", display(program))
    print("Input:", display(user_input))
    print("Validation:", display(validation))
    print("Original Grammar/Language:", display(original))
    print("Algorithm:", display(algorithm))
    print("Step-by-Step Execution:")
    for i, step in enumerate(steps, 1):
        print(" ", i, "-", display(step))
    print("Intermediate Results:", display(intermediate))
    print("Final Result:", display(result))
    print("Verification:", display(verification))
    print("Warnings/Limitations:", display(warnings or "None"))
    print("Execution Time:", f"{elapsed:.6f} seconds")
    print("=" * 72)
    history_path = Path(__file__).with_name("execution_history.jsonl")
    record = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "program": program,
        "input": user_input,
        "validation": validation,
        "original": original,
        "algorithm": algorithm,
        "steps": steps,
        "intermediate": intermediate,
        "result": result,
        "verification": verification,
        "warnings": warnings,
        "execution_time_seconds": elapsed,
    }
    try:
        with history_path.open("a", encoding="utf-8") as history:
            history.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print("History warning: could not save execution record:", exc)


report_start = time.perf_counter()


def start_execution():
    global report_start
    report_start = time.perf_counter()


# ======================== Program 1 ========================

def in_supported_language(language: str, w: str) -> bool:
    if language == "a^n b^n":
        a = w.count("a")
        b = w.count("b")
        return set(w) <= {"a", "b"} and w == "a" * a + "b" * b and a == b
    if language == "a^n b^n c^n":
        return bool(re.fullmatch(r"a*b*c*", w)) and w.count("a") == w.count("b") == w.count("c")
    if language == "a^n b^m":
        return bool(re.fullmatch(r"a*b*", w))
    if language == "a*":
        return bool(re.fullmatch(r"a*", w))
    return False


def enumerate_decompositions(w: str, p: int) -> Iterable[Tuple[str, str, str]]:
    for i in range(len(w) + 1):
        for j in range(i + 1, len(w) + 1):
            x, y, z = w[:i], w[i:j], w[j:]
            if y and len(x + y) <= p:
                yield x, y, z


def validate_decomposition(w: str, p: int, x: str, y: str, z: str) -> Tuple[bool, str]:
    if x + y + z != w:
        return False, "xyz must equal the witness."
    if not y:
        return False, "y must contain at least one symbol."
    if len(x + y) > p:
        return False, "|xy| must be at most p."
    return True, "Valid pumping-lemma decomposition."


def validate_alphabet(language: str, alphabet: str) -> bool:
    expected = {
        "a^n b^n": {"a", "b"},
        "a^n b^n c^n": {"a", "b", "c"},
        "a^n b^m": {"a", "b"},
        "a*": {"a"},
    }
    entered = {symbol.strip() for symbol in alphabet.split(",") if symbol.strip()}
    return language in expected and entered == expected[language]


def pumping_proof_status(language: str, witness: str, p: int) -> Tuple[str, str]:
    if language == "a^n b^n":
        count_a = len(witness) - len(witness.lstrip("a"))
        count_b = len(witness) - count_a
        if (witness == "a" * count_a + "b" * count_b
                and count_a == count_b and count_a >= p):
            return ("NON_REGULAR_PROVED",
                    f"For w=a^{count_a}b^{count_b}, |xy|<=p places y entirely in the a-block. "
                    "Pumping with i=0 decreases the number of a symbols but not b symbols.")
    elif language == "a^n b^n c^n":
        count_a = len(witness) - len(witness.lstrip("a"))
        after_a = witness[count_a:]
        count_b = len(after_a) - len(after_a.lstrip("b"))
        count_c = len(after_a) - count_b
        if (witness == "a" * count_a + "b" * count_b + "c" * count_c
                and count_a == count_b == count_c and count_a >= p):
            return ("NON_REGULAR_PROVED",
                    f"For w=a^{count_a}b^{count_b}c^{count_c}, |xy|<=p places y entirely in the a-block. "
                    "Pumping with i=0 changes the a-count but leaves the b- and c-counts unchanged.")
    return ("INCONCLUSIVE",
            "The supplied witness does not instantiate a supported universal non-regularity proof.")


def parse_witness(value: str) -> str:
    value = value.strip()
    if value.lower() in ("", "lambda", "epsilon") or value in ("λ", "ε"):
        return ""
    return value


def pumping_lemma():
    start_execution()
    print("\nSupported languages: a^n b^n | a^n b^n c^n | a^n b^m | a*")
    language = input("Language formula: ").strip()
    alphabet = input("Alphabet (comma separated): ").strip()
    p_text = input("Pumping length p: ").strip()
    w = parse_witness(input("Witness w (type lambda for the empty string): "))

    supported = {"a^n b^n", "a^n b^n c^n", "a^n b^m", "a*"}
    if language not in supported:
        report("Program 1 - Pumping Lemma", f"language={language}, p={p_text}, w={w}",
               "FAILED", language, "Supported-family dispatch",
               ["Checked formula against supported families"], "No family selected",
               "UNSUPPORTED_LANGUAGE", "No membership or pumping conclusion is possible.",
               "Unknown formula cannot be proved or disproved.")
        return
    if not alphabet:
        report("Program 1 - Pumping Lemma", f"p={p_text}, w={w}",
               "FAILED", language, "Input validation", ["Alphabet is missing"],
               "", "INVALID_INPUT", "Alphabet is required.")
        return
    if not validate_alphabet(language, alphabet):
        report("Program 1 - Pumping Lemma", f"alphabet={alphabet}; p={p_text}; w={w}",
               "FAILED", language, "Alphabet validation",
               [f"Alphabet does not match the symbols for {language}"],
               "", "INVALID_INPUT", "Alphabet does not match the selected language.")
        return
    try:
        p = int(p_text)
        if p <= 0:
            raise ValueError
    except ValueError:
        report("Program 1 - Pumping Lemma", f"p={p_text}, w={w}",
               "FAILED", language, "Positive integer validation",
               ["Accepted only positive p"], "", "INVALID_INPUT", "p must be a positive integer.")
        return
    if not in_supported_language(language, w):
        report("Program 1 - Pumping Lemma", f"p={p}, w={w}",
               "FAILED", language, "Witness membership",
               [f"Membership test for {w} failed"], "w not in L",
               "INVALID_INPUT", "Witness outside the specified language.")
        return
    if len(w) < p:
        report("Program 1 - Pumping Lemma", f"p={p}, w={w}",
               "FAILED", language, "Witness length",
               [f"|w|={len(w)} is shorter than p={p}"], "", "INVALID_INPUT",
               "Witness must satisfy |w| >= p.")
        return

    decomposition_limit = 100000
    decomposition_count = p * (p + 1) // 2
    if decomposition_count > decomposition_limit:
        report("Program 1 - Pumping Lemma", f"p={p}; w_length={len(w)}",
               "VALID", language, "Decomposition enumeration",
               [f"Required decomposition count {decomposition_count} exceeds limit "
                f"{decomposition_limit}"],
               "", "RESOURCE_LIMIT", "Input is not classified as a language rejection.",
               "Reduce p or use a shorter witness.")
        return

    manual_result = None
    if input("Check a manual x,y,z decomposition too? (y/N): ").strip().lower() == "y":
        x = parse_witness(input("Enter x (use lambda for empty): "))
        y = parse_witness(input("Enter y (use lambda for empty): "))
        z = parse_witness(input("Enter z (use lambda for empty): "))
        manual_result = (x, y, z) + validate_decomposition(w, p, x, y, z)

    decompositions = list(enumerate_decompositions(w, p))
    steps = []
    counterexample_count = 0
    for x, y, z in decompositions:
        pumped = [x + y * i + z for i in range(4)]
        memberships = [in_supported_language(language, s) for s in pumped]
        steps.append(f"x={x!r}, y={y!r}, z={z!r}; pumped={list(zip(pumped, memberships))}")
        if not all(memberships):
            counterexample_count += 1
    steps.append(f"Decompositions with a failing tested pump: {counterexample_count}")
    if manual_result is not None:
        steps.append("Manual decomposition: " + "; ".join(
            [f"x={manual_result[0]!r}", f"y={manual_result[1]!r}",
             f"z={manual_result[2]!r}", manual_result[4]]))

    result, symbolic = pumping_proof_status(language, w, p)
    if result == "NON_REGULAR_PROVED":
        verification = "Symbolic proof applies to every permitted decomposition of this witness."
    else:
        verification = "Finite pumped samples are not a universal regularity proof."

    report("Program 1 - Pumping Lemma", f"alphabet={alphabet}; p={p}; w={w}",
           "VALID", language, "Decomposition enumeration and symbolic proof",
           steps, f"{len(decompositions)} valid decompositions",
           result, verification,
           symbolic if symbolic else "The selected family is inconclusive.")


# ======================== Program 2 ======================

VERBS = ("play", "study", "work", "eat", "drive", "read", "write", "watch", "walk", "teach")
OBJECTS = ("cricket", "English", "home", "football", "books")
THIRD = {"He", "She", "It"}


def third_inflect(verb: str) -> str:
    if verb.endswith(("s", "x", "z", "ch", "sh")):
        return verb + "es"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        return verb[:-1] + "ies"
    return verb + "s"


def english_cfg_productions() -> Dict[str, Tuple[Tuple[str, ...], ...]]:
    productions: Dict[str, Tuple[Tuple[str, ...], ...]] = {
        "Start": (("Affirmative",), ("Negative",), ("Interrogative",)),
        "Affirmative": (
            ("NonThirdCapital", "BaseVerb", "Object", "."),
            ("ThirdCapital", "ThirdVerb", "Object", "."),
        ),
        "Negative": (
            ("NonThirdCapital", "DoNot", "BaseVerb", "Object", "."),
            ("ThirdCapital", "DoesNot", "BaseVerb", "Object", "."),
        ),
        "Interrogative": (
            ("AuxDo", "NonThirdQuestion", "BaseVerb", "Object", "?"),
            ("AuxDoes", "ThirdQuestion", "BaseVerb", "Object", "?"),
        ),
        "NonThirdCapital": (
            ("FirstSingular",), ("SecondSingular",), ("FirstPlural",),
            ("SecondPlural",), ("ThirdPlural",),
        ),
        "NonThirdQuestion": (
            ("FirstSingularQuestion",), ("SecondSingularQuestion",),
            ("FirstPluralQuestion",), ("SecondPluralQuestion",),
            ("ThirdPluralQuestion",),
        ),
        "ThirdCapital": (("ThirdSingular",),),
        "ThirdQuestion": (("ThirdSingularQuestion",),),
        "FirstSingular": (("I",),),
        "SecondSingular": (("You",),),
        "FirstPlural": (("We",),),
        "SecondPlural": (("You",),),
        "ThirdPlural": (("They",),),
        "ThirdSingular": (("He",), ("She",), ("It",)),
        "FirstSingularQuestion": (("I",),),
        "SecondSingularQuestion": (("you",),),
        "FirstPluralQuestion": (("we",),),
        "SecondPluralQuestion": (("you",),),
        "ThirdPluralQuestion": (("they",),),
        "ThirdSingularQuestion": (("he",), ("she",), ("it",)),
        "DoNot": (("do", "not"),),
        "DoesNot": (("does", "not"),),
        "AuxDo": (("Do",),),
        "AuxDoes": (("Does",),),
        "BaseVerb": tuple((verb,) for verb in VERBS),
        "ThirdVerb": tuple((third_inflect(verb),) for verb in VERBS),
        "Object": tuple((obj,) for obj in OBJECTS),
    }
    return productions


def grammar_sentences(productions: Dict[str, Tuple[Tuple[str, ...], ...]],
                      start: str = "Start") -> Set[Tuple[str, ...]]:
    def expand(symbol: str, active: Set[str]) -> Set[Tuple[str, ...]]:
        if symbol not in productions:
            return {(symbol,)}
        if symbol in active:
            return set()
        results: Set[Tuple[str, ...]] = set()
        next_active = active | {symbol}
        for rhs in productions[symbol]:
            phrases = {()}
            for child in rhs:
                child_phrases = expand(child, next_active)
                phrases = {prefix + phrase for prefix in phrases for phrase in child_phrases}
            results.update(phrases)
        return results

    return expand(start, set())


def generate_simple_sentences() -> Set[str]:
    token_sequences = grammar_sentences(english_cfg_productions())
    return {tokens_to_sentence(tokens) for tokens in token_sequences}


def tokens_to_sentence(tokens: Tuple[str, ...]) -> str:
    if tokens and tokens[-1] in (".", "?"):
        return " ".join(tokens[:-1]) + tokens[-1]
    return " ".join(tokens)


def parse_cfg_trees(productions: Dict[str, Tuple[Tuple[str, ...], ...]],
                    tokens: Tuple[str, ...], start: str,
                    limit: int = 20) -> Tuple[List[Tuple[str, Tuple]], bool]:
    variables = set(productions)
    trees: List[Tuple[str, Tuple]] = []
    root_seen: Set[str] = set()
    truncated = False

    def parse_variable(variable: str, begin: int, end: int,
                       active: Set[Tuple[str, int, int]]) -> List[Tuple[str, Tuple]]:
        nonlocal truncated
        key = (variable, begin, end)
        if key in active:
            return []
        next_active = active | {key}
        found: List[Tuple[str, Tuple]] = []
        found_seen: Set[str] = set()
        for rhs in productions.get(variable, ()):
            for children in parse_rhs(rhs, 0, begin, end, next_active):
                tree = (variable, tuple(children))
                identity = repr(tree)
                if identity not in found_seen:
                    found_seen.add(identity)
                    found.append(tree)
                    if len(found) > limit:
                        truncated = True
                        return found[:limit]
        return found

    def parse_rhs(rhs: Tuple[str, ...], offset: int, position: int, end: int,
                  active: Set[Tuple[str, int, int]]) -> List[List]:
        if offset == len(rhs):
            return [[]] if position == end else []
        symbol = rhs[offset]
        results: List[List] = []
        if symbol in variables:
            for split in range(position, end + 1):
                for subtree in parse_variable(symbol, position, split, active):
                    for rest in parse_rhs(rhs, offset + 1, split, end, active):
                        results.append([subtree] + rest)
                        if len(results) > limit:
                            return results
        elif position < end and tokens[position] == symbol:
            for rest in parse_rhs(rhs, offset + 1, position + 1, end, active):
                results.append([symbol] + rest)
        return results

    for tree in parse_variable(start, 0, len(tokens), set()):
        identity = repr(tree)
        if identity not in root_seen:
            root_seen.add(identity)
            trees.append(tree)
            if len(trees) > limit:
                truncated = True
                trees.pop()
                break
    return trees, truncated


def format_parse_tree(tree: Tuple[str, Tuple], depth: int = 0) -> List[str]:
    symbol, children = tree
    lines = ["  " * depth + symbol]
    for child in children:
        if isinstance(child, tuple):
            lines.extend(format_parse_tree(child, depth + 1))
        else:
            lines.append("  " * (depth + 1) + repr(child))
    return lines


def english_cfg():
    start_execution()
    productions = english_cfg_productions()
    print("Simple Present CFG productions:")
    for variable, alternatives in productions.items():
        print(variable, "->", " | ".join(" ".join(rhs) for rhs in alternatives))
    mode = input("Mode (validate/generate): ").strip().lower()
    grammar_description = "Controlled Simple Present CFG"

    if mode == "generate":
        try:
            count = int(input("Maximum sentences to display (1-100): ").strip())
            if not 1 <= count <= 100:
                raise ValueError
        except ValueError:
            report("Program 2 - English CFG", "mode=generate", "FAILED",
                   grammar_description, "CFG generation", [],
                   "", "INVALID_INPUT", "Choose a display limit from 1 to 100.")
            return
        sentences = sorted(generate_simple_sentences())
        shown = sentences[:count]
        steps = [
            "Subject/number combinations: I (first singular), We (first plural), "
            "You (second singular), You (second plural), He/She/It (third singular), "
            "They (third plural).",
            "Productions: " + "; ".join(
                variable + " -> " + " | ".join(" ".join(rhs) for rhs in alternatives)
                for variable, alternatives in productions.items()),
        ]
        for sentence in shown:
            tokens = tuple(re.findall(r"[A-Za-z]+|[?.]", sentence))
            trees, _ = parse_cfg_trees(productions, tokens, "Start", 1)
            if trees:
                steps.append(sentence + "\n" + "\n".join(format_parse_tree(trees[0])))
        report("Program 2 - English CFG", f"mode=generate; limit={count}",
               "VALID", grammar_description, "Expand grammar productions",
               steps, f"Generated {len(shown)} displayed sentences of {len(sentences)} total.",
               "SENTENCES_GENERATED", "Every displayed sentence is derived from the CFG.")
        return

    if mode != "validate":
        report("Program 2 - English CFG", f"mode={mode}", "FAILED",
               grammar_description, "Mode validation", [],
               "", "INVALID_INPUT", "Choose validate or generate.")
        return

    text = input("Enter a sentence: ").strip()
    if not text:
        report("Program 2 - English CFG", "empty", "FAILED", grammar_description,
               "CFG parsing", ["No sentence supplied"], "", "INVALID_INPUT",
               "Sentence input is required.")
        return
    tokens = tuple(re.findall(r"[A-Za-z]+|[?.]", text))
    if tokens_to_sentence(tokens) != text:
        report("Program 2 - English CFG", text, "FAILED", grammar_description,
               "Input tokenization", ["Sentence contains unsupported punctuation or spacing"],
               "", "INVALID_INPUT", "Enter a sentence using the documented vocabulary and punctuation.")
        return
    trees, truncated = parse_cfg_trees(productions, tokens, "Start", 20)
    steps = [
        "Subject/number combinations: I (first singular), We (first plural), "
        "You (second singular), You (second plural), He/She/It (third singular), "
        "They (third plural).",
        "Productions: " + "; ".join(
        variable + " -> " + " | ".join(" ".join(rhs) for rhs in alternatives)
        for variable, alternatives in productions.items())]
    for index, tree in enumerate(trees, 1):
        steps.append(f"Parse tree {index}:\n" + "\n".join(format_parse_tree(tree)))
    accepted = bool(trees)
    report("Program 2 - English CFG", text,
           "GRAMMAR_MATCH" if accepted else "NO_GRAMMAR_DERIVATION", grammar_description,
           "Bounded CFG parse-tree search", steps,
           f"Parse trees found={len(trees)}",
           "ACCEPT" if accepted else "REJECT",
           "Acceptance requires a derivation from the displayed grammar.",
           "Parse-tree enumeration limit reached." if truncated else
           "Controlled vocabulary; irregular verbs, contractions, and complex sentences are excluded.")


# ======================== Program 3 ======================

@dataclass(frozen=True)
class EarleyItem:
    lhs: str
    rhs: Tuple[str, ...]
    dot: int
    origin: int


def grammar_as_token_productions(grammar: Grammar) -> Dict[str, Tuple[Tuple[str, ...], ...]]:
    return {
        variable: tuple(tokenize_rhs(rhs, grammar.variables) for rhs in alternatives)
        for variable, alternatives in grammar.productions.items()
    }


def earley_accepts(productions: Dict[str, Tuple[Tuple[str, ...], ...]],
                   start: str, tokens: Tuple[str, ...],
                   max_items: int = 100000) -> bool:
    if max_items <= 0:
        raise ValueError("Earley item limit must be positive.")
    augmented = "__AUGMENTED_START__"
    while augmented in productions:
        augmented += "_"
    all_productions = dict(productions)
    all_productions[augmented] = ((start,),)
    variables = set(all_productions)
    chart = [set() for _ in range(len(tokens) + 1)]
    chart[0].add(EarleyItem(augmented, (start,), 0, 0))
    item_count = 1

    def add_item(position: int, item: EarleyItem) -> bool:
        nonlocal item_count
        if item in chart[position]:
            return False
        item_count += 1
        if item_count > max_items:
            raise ResourceLimitError(f"Earley chart exceeded {max_items} items.")
        chart[position].add(item)
        return True

    for position in range(len(tokens) + 1):
        changed = True
        while changed:
            changed = False
            for item in list(chart[position]):
                if item.dot < len(item.rhs):
                    symbol = item.rhs[item.dot]
                    if symbol in variables:
                        for rhs in all_productions.get(symbol, ()):
                            predicted = EarleyItem(symbol, rhs, 0, position)
                            if add_item(position, predicted):
                                changed = True
                else:
                    for previous in list(chart[item.origin]):
                        if (previous.dot < len(previous.rhs)
                                and previous.rhs[previous.dot] == item.lhs):
                            completed = EarleyItem(
                                previous.lhs, previous.rhs, previous.dot + 1, previous.origin)
                            if add_item(position, completed):
                                changed = True

        if position < len(tokens):
            for item in chart[position]:
                if item.dot < len(item.rhs):
                    symbol = item.rhs[item.dot]
                    if symbol not in variables and symbol == tokens[position]:
                        add_item(position + 1,
                                 EarleyItem(item.lhs, item.rhs, item.dot + 1, item.origin))

    return any(item.lhs == augmented and item.dot == len(item.rhs) and item.origin == 0
               for item in chart[len(tokens)])


def earley_parse(grammar: Grammar, target: str) -> bool:
    return earley_accepts(grammar_as_token_productions(grammar),
                          grammar.start, tuple(target))


def grammar_parse_trees(grammar: Grammar, target: str,
                        limit: int = 20) -> Tuple[List[Tuple[str, Tuple]], bool]:
    return parse_cfg_trees(grammar_as_token_productions(grammar),
                           tuple(target), grammar.start, limit)


def derivation_from_tree(tree: Tuple[str, Tuple], direction: str) -> List[str]:
    ordered_nodes: List[Tuple[str, Tuple]] = []

    def visit(node: Tuple[str, Tuple]):
        ordered_nodes.append(node)
        children = [child for child in node[1] if isinstance(child, tuple)]
        if direction == "right":
            children.reverse()
        for child in children:
            visit(child)

    visit(tree)
    sentential = [tree[0]]
    trace = [tree[0]]
    for node in ordered_nodes:
        variable, children = node
        positions = [index for index, symbol in enumerate(sentential) if symbol == variable]
        if not positions:
            continue
        position = positions[0] if direction == "left" else positions[-1]
        rhs = [child[0] if isinstance(child, tuple) else child for child in children]
        sentential[position:position + 1] = rhs
        trace.append("".join(sentential) if sentential else EPSILON)
    return trace


def derivation_steps_from_tree(tree: Tuple[str, Tuple], direction: str) -> List[str]:
    ordered_nodes: List[Tuple[str, Tuple]] = []

    def visit(node: Tuple[str, Tuple]):
        ordered_nodes.append(node)
        children = [child for child in node[1] if isinstance(child, tuple)]
        if direction == "right":
            children.reverse()
        for child in children:
            visit(child)

    visit(tree)
    sentential = [tree[0]]
    steps = []
    for index, (variable, children) in enumerate(ordered_nodes, 1):
        positions = [position for position, symbol in enumerate(sentential)
                     if symbol == variable]
        if not positions:
            continue
        position = positions[0] if direction == "left" else positions[-1]
        rhs = [child[0] if isinstance(child, tuple) else child for child in children]
        sentential[position:position + 1] = rhs
        rendered_rhs = " ".join(rhs) if rhs else EPSILON
        rendered_form = " ".join(sentential) if sentential else EPSILON
        steps.append(
            f"Step {len(steps) + 1}: {variable} -> {rendered_rhs}; "
            f"sentential form: {rendered_form}")
    return steps


def left_right_derivations(grammar: Grammar, target: str,
                           limit: int = 300) -> Tuple[List[str], List[str]]:
    trees, _ = grammar_parse_trees(grammar, target, max(1, limit))
    if not trees:
        return [], []
    return (derivation_from_tree(trees[0], "left"),
            derivation_from_tree(trees[0], "right"))


def derivation_program():
    start_execution()
    print("Enter productions, one per line (A->aB|b; epsilon spelled 'epsilon'):")
    text = input("Grammar: ").strip().replace(";", "\n")
    start = input("Start symbol: ").strip()
    target = input("Target string: ").strip()
    limit_text = input("Maximum parse trees (default 20): ").strip()
    try:
        grammar = parse_grammar(text, start)
        limit = int(limit_text) if limit_text else 20
        if limit <= 0:
            raise ValueError("Parse-tree limit must be positive.")
    except ValueError as exc:
        report("Program 3 - Derivations", f"grammar={text}; start={start}; target={target}",
               "FAILED", text, "Grammar and target validation",
               [str(exc)], "", "INVALID_INPUT", "No derivation performed.")
        return

    productions = grammar_as_token_productions(grammar)
    try:
        member = earley_accepts(productions, grammar.start, tuple(target))
    except ResourceLimitError as exc:
        report("Program 3 - Derivations", f"grammar={text}; start={start}; target={target}",
               "VALID", text, "Earley membership resource guard",
               [str(exc)], "", "RESOURCE_LIMIT",
               "The target is not classified as a non-member because parsing did not finish.")
        return
    trees, truncated = parse_cfg_trees(productions, tuple(target), grammar.start, limit)
    steps = []
    for index, tree in enumerate(trees, 1):
        steps.append(f"Parse tree {index}:\n" + "\n".join(format_parse_tree(tree)))
        steps.append("Leftmost derivation:\n" + "\n".join(
            derivation_steps_from_tree(tree, "left")))
        steps.append("Rightmost derivation:\n" + "\n".join(
            derivation_steps_from_tree(tree, "right")))
    if not steps:
        steps.append("No parse tree was enumerated within the configured limit.")
    if not member:
        result = "NON_MEMBER"
    elif truncated:
        result = "MEMBER (PARSE_TREE_LIMIT_REACHED)"
    else:
        result = "MEMBER"
    report("Program 3 - Derivations", f"grammar={text}; start={start}; target={target}",
           "VALID", text, "Earley membership and bounded parse-tree enumeration",
           steps, f"parse_trees={len(trees)}; limit={limit}; earley_member={member}",
           result, "Membership and parse-tree enumeration are reported separately.",
           "More parse trees may exist than the configured enumeration limit." if truncated else "")


# ======================== Programs 4-7 ======================

def decimal_is_valid(s: str) -> bool:
    return bool(re.fullmatch(r"(0|[1-9][0-9]*)", s))


def decimal_remainder(number: str, divisor: int) -> int:
    remainder = 0
    for digit in number:
        remainder = (remainder * 10 + ord(digit) - ord("0")) % divisor
    return remainder


def divisibility_problems(problem: Optional[str] = None):
    if problem is None:
        problem = input("Problem (e.g. 24 divisible 5 or 24 factorial 5): ").strip()
    parts = problem.split()
    if len(parts) == 3 and parts[1].lower() == "divisible":
        number, divisor_text = parts[0], parts[2]
        if not decimal_is_valid(number) or not divisor_text.isdigit():
            return "INVALID_INPUT", "Leading zeros, negative signs, whitespace and non-digits are not accepted."
        if divisor_text not in ("2", "3", "5", "7", "10", "12", "24"):
            return "INVALID_INPUT", "Unsupported divisor."
        divisor = int(divisor_text)
        remainder = decimal_remainder(number, divisor)
        accepted = remainder == 0
        return ("ACCEPT" if accepted else "REJECT",
                f"Canonical decimal {number}; remainder {remainder}; divisor {divisor}.")
    if len(parts) == 3 and parts[1].lower() == "factorial":
        number, n_text = parts[0], parts[2]
        if not decimal_is_valid(number) or not decimal_is_valid(n_text):
            return "INVALID_INPUT", "Invalid canonical decimal or factorial bound."
        if len(n_text) > 2:
            return "INVALID_INPUT", "Factorial bound must be at most 20."
        n = int(n_text)
        if n > 20:
            return "INVALID_INPUT", "Factorial bound must be at most 20."
        values = {str(math.factorial(i)) for i in range(n + 1)}
        return ("ACCEPT" if number in values else "REJECT",
                f"Factorial set {sorted(values, key=int)}.")
    return "INVALID_INPUT", "Use: <number> divisible <divisor> or <number> factorial <N>"


def remainder_dfa_grammar(divisor: int):
    start = "StartD"
    variables = [start] + [f"R{remainder}" for remainder in range(divisor)]
    productions: Dict[str, Tuple[Tuple[str, ...], ...]] = {}
    start_rules = [(str(digit), f"R{digit % divisor}") for digit in range(1, 10)]
    start_rules.append(("0",))
    productions[start] = tuple(start_rules)
    for remainder in range(divisor):
        rules = [(str(digit), f"R{(remainder * 10 + digit) % divisor}")
                 for digit in range(10)]
        if remainder == 0:
            rules.append(())
        productions[f"R{remainder}"] = tuple(rules)
    return variables, set("0123456789"), productions, start


def factorial_trie_grammar(bound: int):
    values = sorted({str(math.factorial(number)) for number in range(bound + 1)}, key=int)
    start = "FactStart"
    nodes = [{"terminal": False, "children": {}}]
    for value in values:
        current = 0
        for digit in value:
            child = nodes[current]["children"].get(digit)
            if child is None:
                child = len(nodes)
                nodes[current]["children"][digit] = child
                nodes.append({"terminal": False, "children": {}})
            current = child
        nodes[current]["terminal"] = True

    names = [start] + [f"F{index}" for index in range(1, len(nodes))]
    productions: Dict[str, Tuple[Tuple[str, ...], ...]] = {}
    for index, node in enumerate(nodes):
        rules = [(digit, names[child]) for digit, child in sorted(node["children"].items())]
        if node["terminal"]:
            rules.append(())
        productions[names[index]] = tuple(rules)
    return values, names, set("0123456789"), productions, start


def production_text(productions: Dict[str, Tuple[Tuple[str, ...], ...]]) -> List[str]:
    lines = []
    for variable, alternatives in productions.items():
        rendered = ["".join(rhs) if rhs else EPSILON for rhs in alternatives]
        lines.append(variable + " -> " + " | ".join(rendered))
    return lines


def example_derivation(productions: Dict[str, Tuple[Tuple[str, ...], ...]],
                       start: str, word: str) -> str:
    trees, _ = parse_cfg_trees(productions, tuple(word), start, 1)
    if not trees:
        return f"No derivation found for {word or EPSILON}."
    return " => ".join(derivation_from_tree(trees[0], "left"))


def mathematical_cfg():
    start_execution()
    problem = input("Choose equal-ab, palindrome, balanced, divisibility, factorial: ").strip().lower()
    if problem == "equal":
        problem = "equal-ab"
    if problem in ("equal-ab", "equal", "palindrome", "balanced"):
        examples = {
            "equal-ab": ("{a^n b^n | n >= 0}", {"a", "b"},
                         {"S": (("a", "S", "b"), ())}, ["", "ab", "aabb"]),
            "palindrome": ("{w in {a,b}* | w=w^R}", {"a", "b"},
                           {"S": (("a", "S", "a"), ("b", "S", "b"),
                                  ("a",), ("b",), ())}, ["", "a", "abba"]),
            "balanced": ("balanced parentheses", {"(", ")"},
                         {"S": (("(", "S", ")", "S"), ())}, ["", "()", "()()"]),
        }
        language, alphabet, productions, derivation_examples = examples[problem]
        variables = set(productions)
        start = "S"
        test = input("Test string: ").strip()
        tokens = tuple(test)
        accepted = earley_accepts(productions, start, tokens)
        rejected_example = {"equal-ab": "aab", "palindrome": "abab",
                            "balanced": "(()"}[problem]
        derivations = [
            f"{word or EPSILON}: {example_derivation(productions, start, word)}"
            for word in derivation_examples
        ]
        details = [
            f"V = {sorted(variables)}",
            f"Σ = {sorted(alphabet)}",
            "Technique: context-free grammar membership with Earley parsing",
            f"S = {start}",
            "P = " + "; ".join(production_text(productions)),
            "Example derivations: " + " || ".join(derivations),
            f"Acceptance/rejection examples: {derivation_examples[-1] or EPSILON}=ACCEPT; "
            f"{rejected_example}=REJECT; supplied {test or EPSILON}="
            f"{'ACCEPT' if accepted else 'REJECT'}",
        ]
        report("Program 4 - Mathematical CFG",
               f"{problem}; test={test}", "VALID", language,
               "CFG construction and Earley membership",
               details, "; ".join(production_text(productions)),
               "ACCEPT" if accepted else "REJECT",
               "Membership is decided by parsing against the constructed CFG.")
    elif problem in ("divisibility", "factorial"):
        expression = input("Enter <number> divisible <d> or <number> factorial <N>: ").strip()
        detail = divisibility_problems(expression)
        parts = expression.split()
        steps = [detail[1]]
        if detail[0] == "INVALID_INPUT":
            report("Program 4 - Mathematical CFG", expression, "FAILED",
                   "Canonical decimal language", "Input validation",
                   steps, "", detail[0], "Invalid decimal expression.")
            return

        if len(parts) == 3 and parts[1].lower() == "divisible":
            divisor = int(parts[2])
            variables, alphabet, productions, start = remainder_dfa_grammar(divisor)
            language = f"canonical decimal strings divisible by {divisor}"
            accepted_examples = ["0", str(divisor), str(2 * divisor)]
        else:
            bound = int(parts[2])
            values, variables, alphabet, productions, start = factorial_trie_grammar(bound)
            language = f"L_fact,{bound} = {{decimal(n!) | 0 <= n <= {bound}}}"
            accepted_examples = values[:3]

        steps.extend([
            f"V = {variables}",
            f"Σ = {sorted(alphabet)}",
            "Technique: remainder DFA converted to a right-linear grammar"
            if parts[1].lower() == "divisible" else "Technique: finite trie grammar for bounded factorial values",
            f"S = {start}",
            "Productions: " + "; ".join(production_text(productions)),
        ])
        steps.append("Example derivations: " + " || ".join(
            f"{value}: {example_derivation(productions, start, value)}"
            for value in accepted_examples))
        entered = parts[0]
        accepted = earley_accepts(productions, start, tuple(entered))
        direct_accepted = detail[0] == "ACCEPT"
        rejected_example = ("1" if parts[1].lower() == "divisible" and int(parts[2]) != 1
                            else "2") if parts[1].lower() == "divisible" else "0"
        while rejected_example in accepted_examples:
            rejected_example = str(int(rejected_example) + 1)
        rejected_member = earley_accepts(productions, start, tuple(rejected_example))
        steps.append(f"Rejection example {rejected_example}: "
                     f"{'ACCEPT' if rejected_member else 'REJECT'}")
        steps.append(f"Input test {entered}: {'ACCEPT' if accepted else 'REJECT'}")
        result = ("VERIFICATION_MISMATCH" if accepted != direct_accepted else
                  "ACCEPT" if accepted else "REJECT")
        report("Program 4 - Mathematical CFG", expression, "VALID",
               language, "DFA-derived grammar or finite trie plus CFG membership",
               steps, f"{len(variables)} variables; {sum(map(len, productions.values()))} productions",
               result, "The generated grammar and arithmetic/set membership checks agree."
               if result != "VERIFICATION_MISMATCH"
               else "Generated grammar disagrees with direct membership computation.")
    else:
        report("Program 4 - Mathematical CFG", problem, "FAILED",
               "Unsupported problem", "Supported-language dispatch",
               ["Unknown selection"], "", "INVALID_INPUT",
               "Choose a supported mathematical language.")


def parse_right_linear(text: str, start_symbol: Optional[str] = None) -> Dict[str, Tuple[str, ...]]:
    grammar = parse_grammar(text, start_symbol)
    rhs_by_left = grammar.productions
    for left, rhs_list in rhs_by_left.items():
        for rhs in rhs_list:
            if rhs == EPSILON:
                continue
            symbols = tokenize_rhs(rhs, grammar.variables)
            if len(symbols) == 1 and symbols[0] not in grammar.variables:
                continue
            if (len(symbols) == 2 and symbols[0] not in grammar.variables
                    and symbols[1] in grammar.variables):
                continue
            raise ValueError("Non-right-linear rule: " + left + "->" + rhs)
    return rhs_by_left


def right_linear_automaton(grammar: Grammar):
    transitions: Dict[Tuple[str, str], Set[str]] = {}
    accepting = set()
    fresh = "F"
    while fresh in grammar.variables:
        fresh += "F"
    has_terminal_rule = False
    for left, alternatives in grammar.productions.items():
        for rule in alternatives:
            if rule == EPSILON:
                accepting.add(left)
                continue
            symbols = tokenize_rhs(rule, grammar.variables)
            if len(symbols) == 1:
                has_terminal_rule = True
                transitions.setdefault((left, symbols[0]), set()).add(fresh)
            else:
                transitions.setdefault((left, symbols[0]), set()).add(symbols[1])
    states = set(grammar.variables)
    if has_terminal_rule:
        states.add(fresh)
        accepting.add(fresh)
    return states, transitions, accepting


def subset_dfa(alphabet: Iterable[str], start: str,
               transitions: Dict[Tuple[str, str], Set[str]],
               nfa_accepting: Set[str], max_states: int = 10000):
    if max_states <= 0:
        raise ValueError("DFA state limit must be positive.")
    alphabet = tuple(sorted(alphabet))
    initial = (start,)
    queue = [initial]
    dfa: Dict[Tuple[str, ...], Dict[str, Tuple[str, ...]]] = {}
    while queue:
        state_set = queue.pop(0)
        if state_set in dfa:
            continue
        if len(dfa) >= max_states:
            raise ResourceLimitError(f"Subset construction exceeded {max_states} DFA states.")
        row = {}
        for symbol in alphabet:
            target = tuple(sorted({
                target_state
                for state in state_set
                for target_state in transitions.get((state, symbol), set())
            }))
            row[symbol] = target
            if target not in dfa:
                queue.append(target)
        dfa[state_set] = row
    accepting = {state for state in dfa if set(state) & nfa_accepting}
    return dfa, accepting


def dfa_accepts(dfa: Dict[Tuple[str, ...], Dict[str, Tuple[str, ...]]],
                accepting: Set[Tuple[str, ...]], start: Tuple[str, ...],
                word: str) -> bool:
    state = start
    for symbol in word:
        state = dfa[state][symbol]
    return state in accepting


def nfa_accepts(start: str, transitions: Dict[Tuple[str, str], Set[str]],
                accepting: Set[str], word: str) -> bool:
    current = {start}
    for symbol in word:
        current = {target for state in current
                   for target in transitions.get((state, symbol), set())}
    return bool(current & accepting)


def test_strings(alphabet: Iterable[str], count: int = 100) -> List[str]:
    alphabet = tuple(sorted(alphabet))
    if not alphabet:
        return [""] * count
    words = [""]
    length = 1
    while len(words) < count:
        words.extend("".join(items) for items in itertools.product(alphabet, repeat=length))
        length += 1
    return words[:count]


def validate_reference_dfa(document: str, alphabet: Set[str]):
    try:
        data = json.loads(document)
        if not isinstance(data, dict):
            raise ValueError("Reference DFA must be a JSON object.")
        start = data["start"]
        raw_accepting = data["accepting"]
        transitions = data["transitions"]
        raw_alphabet = data["alphabet"]
        if (not isinstance(raw_accepting, list) or not isinstance(raw_alphabet, list)
                or not isinstance(transitions, dict)):
            raise ValueError("DFA accepting/alphabet fields must be arrays and transitions an object.")
        if not all(isinstance(item, str) for item in raw_accepting + raw_alphabet):
            raise ValueError("DFA state and alphabet names must be strings.")
        accepting = set(raw_accepting)
        reference_alphabet = set(raw_alphabet)
        if not all(isinstance(state, str) and isinstance(row, dict)
                   for state, row in transitions.items()):
            raise ValueError("Transition rows must map state names to objects.")
        if not all(isinstance(symbol, str) and isinstance(target, str)
                   for row in transitions.values() for symbol, target in row.items()):
            raise ValueError("Transition labels and targets must be strings.")
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("Reference DFA JSON needs alphabet, start, accepting, and transitions.") from exc
    if reference_alphabet != alphabet:
        raise ValueError("Reference DFA alphabet must match the grammar alphabet.")
    if not isinstance(start, str) or not all(isinstance(state, str) for state in accepting):
        raise ValueError("Reference DFA states must be strings.")
    if not isinstance(start, str):
        raise ValueError("Reference DFA start state must be a string.")
    states = {start} | accepting | set(transitions)
    for row in transitions.values():
        states.update(row.values())
    if not accepting <= states:
        raise ValueError("Reference DFA contains an unknown accepting state.")
    for state in states:
        if state not in transitions or set(transitions[state]) != alphabet:
            raise ValueError(f"Reference DFA state {state} must define every alphabet transition.")
        if not all(isinstance(target, str) for target in transitions[state].values()):
            raise ValueError("Reference DFA transition targets must be strings.")
    return start, accepting, transitions


def compare_dfas(generated, generated_accepting, generated_start,
                 reference_start, reference_accepting, reference_transitions,
                 alphabet: Set[str], max_pairs: int = 100000) -> Tuple[bool, Optional[str]]:
    if max_pairs <= 0:
        raise ResourceLimitError("Exact DFA comparison requires a positive product-state limit.")
    initial = (generated_start, reference_start)
    queue = [(initial, "")]
    visited = {initial}
    while queue:
        (left, right), word = queue.pop(0)
        if ((left in generated_accepting) != (right in reference_accepting)):
            return False, word
        for symbol in sorted(alphabet):
            pair = (generated[left][symbol], reference_transitions[right][symbol])
            if pair not in visited:
                visited.add(pair)
                if len(visited) > max_pairs:
                    raise ResourceLimitError(
                        f"Exact DFA comparison exceeded {max_pairs} product states.")
                queue.append((pair, word + symbol))
    return True, None


def dfa_dot(dfa, accepting, start):
    state_names = {state: f"D{index}" for index, state in enumerate(dfa)}
    lines = ["digraph DFA {", "  rankdir=LR;", '  start [shape=point];',
             f"  start -> {state_names[start]};"]
    for state, name in state_names.items():
        shape = "doublecircle" if state in accepting else "circle"
        lines.append(f'  {name} [shape={shape}, label="{name} {state}"];')
    for state, row in dfa.items():
        for symbol, target in row.items():
            lines.append(f'  {state_names[state]} -> {state_names[target]} [label="{symbol}"];')
    lines.append("}")
    return "\n".join(lines)


def right_linear_dfa():
    start_execution()
    print("Enter right-linear grammar (epsilon allowed; separate rules with semicolons):")
    text = input("Grammar: ").strip().replace(";", "\n")
    start = input("Start symbol: ").strip()
    limit_text = input("Maximum DFA states (default 10000): ").strip()
    reference_text = input("Optional reference DFA JSON (press Enter to skip): ").strip()
    try:
        max_states = int(limit_text) if limit_text else 10000
        if max_states <= 0:
            raise ValueError("DFA state limit must be positive.")
        grammar = parse_grammar(text, start)
        parse_right_linear(text, start)
        states, transitions, nfa_accepting = right_linear_automaton(grammar)
        alphabet = set(grammar.terminals)
        dfa, dfa_accepting = subset_dfa(
            alphabet, grammar.start, transitions, nfa_accepting, max_states)
        start_subset = (grammar.start,)
        reference = validate_reference_dfa(reference_text, alphabet) if reference_text else None
    except ResourceLimitError as exc:
        report("Program 5 - Right-Linear to DFA", f"{text}; start={start}", "VALID", text,
               "Subset-construction resource guard", [str(exc)], "",
               "RESOURCE_LIMIT", "No language rejection was inferred.")
        return
    except ValueError as exc:
        report("Program 5 - Right-Linear to DFA", f"{text}; start={start}", "FAILED", text,
               "Right-linear syntax/reference validation", [str(exc)], "",
               "INVALID_INPUT", "Grammar or optional reference DFA was invalid.")
        return

    nfa_steps = [
        f"NFA row {state}: " + ", ".join(
            f"{symbol}->{sorted(transitions.get((state, symbol), set()))}"
            for symbol in sorted(alphabet))
        for state in sorted(states)
    ]
    nfa_steps.append(f"NFA states={sorted(states)}; start={grammar.start}; accepting={sorted(nfa_accepting)}")
    reachable = {grammar.start}
    frontier = [grammar.start]
    while frontier:
        current = frontier.pop()
        for symbol in alphabet:
            for target in transitions.get((current, symbol), set()):
                if target not in reachable:
                    reachable.add(target)
                    frontier.append(target)
    unreachable = sorted(set(grammar.variables) - reachable)
    if unreachable:
        nfa_steps.append(f"Warning: unreachable grammar variables={unreachable}")
    dfa_names = {state: f"D{index}" for index, state in enumerate(dfa)}
    dfa_steps = [
        f"{dfa_names[state]}={state}; accepting={state in dfa_accepting}; "
        + ", ".join(f"{symbol}->{dfa_names[target]}" for symbol, target in row.items())
        for state, row in dfa.items()
    ]
    samples = test_strings(alphabet, 100)
    token_productions = grammar_as_token_productions(grammar)
    mismatches = []
    try:
        for sample in samples:
            grammar_member = earley_accepts(token_productions, grammar.start, tuple(sample))
            nfa_member = nfa_accepts(grammar.start, transitions, nfa_accepting, sample)
            dfa_member = dfa_accepts(dfa, dfa_accepting, start_subset, sample)
            if grammar_member != nfa_member or nfa_member != dfa_member:
                mismatches.append(sample or EPSILON)
    except ResourceLimitError as exc:
        report("Program 5 - Right-Linear to DFA", f"{text}; start={start}", "VALID", text,
               "Membership verification resource guard", [str(exc)], "",
               "RESOURCE_LIMIT", "No language rejection was inferred.")
        return

    steps = nfa_steps + ["DFA subset-construction table:"] + dfa_steps
    steps.append(f"Compared grammar/NFA/DFA membership for {len(samples)} generated strings.")
    if reference is not None:
        try:
            equivalent, counterexample = compare_dfas(
                dfa, dfa_accepting, start_subset, reference[0], reference[1],
                reference[2], alphabet)
        except ResourceLimitError as exc:
            report("Program 5 - Right-Linear to DFA", f"{text}; start={start}", "VALID", text,
                   "Reference-DFA comparison resource guard", [str(exc)], "",
                   "RESOURCE_LIMIT", "Exact equivalence was not decided.")
            return
        steps.append("Reference DFA exact equivalence: "
                     + ("EQUIVALENT" if equivalent else
                        f"NOT EQUIVALENT; counterexample={counterexample!r}"))
    dot = dfa_dot(dfa, dfa_accepting, start_subset)
    dot_path = Path(__file__).with_name("right_linear_dfa.dot")
    try:
        dot_path.write_text(dot, encoding="utf-8")
        steps.append(f"Graphviz DOT diagram exported to {dot_path.name}.")
    except OSError as exc:
        steps.append(f"Diagram export failed: {exc}")
    steps.append("DOT diagram:\n" + dot)

    report("Program 5 - Right-Linear to DFA", f"{text}; start={start}", "VALID", text,
           "NFA construction, subset construction, and bounded verification",
           steps, f"NFA states={len(states)}; DFA states={len(dfa)}",
           "CONVERTED" if not mismatches else "VERIFICATION_MISMATCH",
           f"Membership comparison count={len(samples)}; mismatches={mismatches}",
           "Finite comparisons are consistency checks, not a proof of equivalence."
           if reference is None else
           "Reference DFA was compared exactly by product-state reachability.")


def nullable_fixed_point(productions: Dict[str, Tuple[str, ...]]) -> Tuple[List[str], Set[str]]:
    nullable: Set[str] = set()
    trace = []
    while True:
        before = set(nullable)
        for left, rhs_list in productions.items():
            for rhs in rhs_list:
                symbols = tokenize_rhs(rhs, productions)
                if rhs == EPSILON or (symbols and all(symbol in nullable for symbol in symbols)):
                    nullable.add(left)
        trace.append(",".join(sorted(nullable)) or "EMPTY")
        if nullable == before:
            break
    return trace, nullable


def eliminate_epsilon(grammar: Grammar, max_generated: int = 10000) -> Grammar:
    if max_generated <= 0:
        raise ValueError("Alternative-generation limit must be positive.")
    productions = {v: tuple(rs) for v, rs in grammar.productions.items()}
    _, nullable = nullable_fixed_point(productions)
    new: Dict[str, Tuple[str, ...]] = {}
    generated_count = 0
    for left, rhs_list in productions.items():
        alternatives = set()
        for rhs in rhs_list:
            if rhs == EPSILON:
                alternatives.add(EPSILON)
                continue
            symbols = list(tokenize_rhs(rhs, grammar.variables))
            optional_positions = [i for i, symbol in enumerate(symbols) if symbol in nullable]
            generated_count += 1 << len(optional_positions)
            if generated_count > max_generated:
                raise ResourceLimitError(
                    f"Epsilon elimination exceeded {max_generated} generated alternatives.")
            for mask in range(1 << len(optional_positions)):
                kept = list(symbols)
                for k, pos in enumerate(optional_positions):
                    if mask & (1 << k):
                        kept[pos] = ""
                alt = "".join(kept)
                alternatives.add(alt if alt else EPSILON)
        alternatives.discard(EPSILON)
        new[left] = tuple(sorted(alternatives))

    start = grammar.start
    if grammar.start in nullable:
        fresh = "S0"
        while fresh in grammar.variables:
            fresh += "0"
        new[fresh] = tuple(sorted(set(new.get(grammar.start, ()) + (EPSILON, grammar.start))))
        variables = grammar.variables + (fresh,)
        start = fresh
    else:
        variables = grammar.variables
    if sum(map(len, new.values())) > max_generated:
        raise ResourceLimitError(
            f"Epsilon elimination exceeded {max_generated} output productions.")
    return Grammar(variables, grammar.terminals, start, new)


def epsilon_elimination():
    start_execution()
    print("Enter grammar (A->BC|epsilon):")
    text = input("Grammar: ").strip().replace(";", "\n")
    start = input("Start symbol: ").strip()
    limit_text = input("Maximum generated alternatives (default 10000): ").strip()
    try:
        max_generated = int(limit_text) if limit_text else 10000
        if max_generated <= 0:
            raise ValueError("Alternative-generation limit must be positive.")
        grammar = parse_grammar(text, start)
        eliminated, details, comparisons, mismatches = epsilon_elimination_result(
            grammar, max_generated)
    except ResourceLimitError as exc:
        report("Program 6 - Epsilon Elimination", text, "VALID", text,
               "Alternative-generation resource guard", [str(exc)], "",
               "RESOURCE_LIMIT", "Input is not reported as a language rejection.")
        return
    except ValueError as exc:
        report("Program 6 - Epsilon Elimination", text, "FAILED", text,
               "Grammar parsing", [str(exc)], "", "INVALID_INPUT", "Undefined or malformed input.")
        return
    report("Program 6 - Epsilon Elimination", text, "VALID", text,
           "Fixed-point nullable computation and alternative expansion",
           details, grammar_to_text(eliminated),
           "EPSILON_ELIMINATION_COMPLETE" if not mismatches else "VERIFICATION_MISMATCH",
           f"Ran {comparisons} finite membership comparisons; mismatches={mismatches}. "
           "The transformation algorithm, not finite sampling, is the language-preservation argument.",
           "Finite comparisons are sanity checks and do not prove language equivalence.")


def eliminate_nullable(grammar: Grammar) -> Set[str]:
    _, nullable = nullable_fixed_point(grammar.productions)
    return nullable


def grammar_to_text(grammar: Grammar) -> str:
    lines = []
    for variable in grammar.variables:
        alternatives = grammar.productions.get(variable, ())
        if alternatives:
            lines.append(variable + " -> " + " | ".join(alternatives))
    return "\n".join(lines)


def compare_grammar_membership(original: Grammar, transformed: Grammar,
                               minimum: int = 50) -> Tuple[int, List[str]]:
    samples = test_strings(original.terminals, minimum)
    original_productions = grammar_as_token_productions(original)
    transformed_productions = grammar_as_token_productions(transformed)
    mismatches = []
    for sample in samples:
        word = tuple(sample)
        if (earley_accepts(original_productions, original.start, word)
                != earley_accepts(transformed_productions, transformed.start, word)):
            mismatches.append(sample or EPSILON)
    return len(samples), mismatches


def epsilon_elimination_result(grammar: Grammar, max_generated: int = 10000):
    trace, nullable = nullable_fixed_point(grammar.productions)
    transformed = eliminate_epsilon(grammar, max_generated)
    comparisons, mismatches = compare_grammar_membership(grammar, transformed)
    original_empty = earley_accepts(grammar_as_token_productions(grammar), grammar.start, ())
    transformed_empty = earley_accepts(
        grammar_as_token_productions(transformed), transformed.start, ())
    details = [
        f"Nullable iterations: {trace}",
        f"Nullable set: {sorted(nullable)}",
        f"Original grammar:\n{grammar_to_text(grammar)}",
        f"Transformed grammar:\n{grammar_to_text(transformed)}",
        f"Production counts: {sum(map(len, grammar.productions.values()))}"
        f" -> {sum(map(len, transformed.productions.values()))}",
        f"Fresh start introduced: {transformed.start != grammar.start}",
        f"Empty-string membership: {original_empty} -> {transformed_empty}",
        f"Finite comparison: {comparisons} words; mismatches={mismatches}",
    ]
    return transformed, details, comparisons, mismatches


def unit_elimination(grammar: Grammar, max_visits: int = 100000) -> Tuple[Grammar, Dict[str, Set[str]], List[str]]:
    if max_visits <= 0:
        raise ValueError("Unit-closure visit limit must be positive.")
    unit_edges = {v: set() for v in grammar.variables}
    nonunit = {v: [] for v in grammar.variables}
    for left, rhs_list in grammar.productions.items():
        for rhs in rhs_list:
            if rhs in grammar.variables:
                unit_edges[left].add(rhs)
            elif rhs != EPSILON:
                nonunit[left].append(rhs)
            else:
                nonunit[left].append(EPSILON)

    closure = {}
    visits = 0
    for start in grammar.variables:
        reached = {start}
        stack = [start]
        while stack:
            cur = stack.pop()
            for nxt in unit_edges[cur]:
                if nxt not in reached:
                    reached.add(nxt)
                    visits += 1
                    if visits > max_visits:
                        raise ResourceLimitError(
                            f"Unit-closure computation exceeded {max_visits} visits.")
                    stack.append(nxt)
        closure[start] = reached

    new: Dict[str, Tuple[str, ...]] = {}
    for left in grammar.variables:
        alternatives = set(nonunit[left])
        for reachable in closure[left]:
            alternatives.update(nonunit.get(reachable, []))
        if not alternatives:
            alternatives = set()
        new[left] = tuple(sorted(alternatives))
    return Grammar(grammar.variables, grammar.terminals, grammar.start, new), closure, []


def unit_elimination_result(grammar: Grammar, max_visits: int = 100000):
    transformed, closure, _ = unit_elimination(grammar, max_visits)
    comparisons, mismatches = compare_grammar_membership(grammar, transformed)
    original_empty = earley_accepts(grammar_as_token_productions(grammar), grammar.start, ())
    transformed_empty = earley_accepts(
        grammar_as_token_productions(transformed), transformed.start, ())
    remaining = [
        left + "->" + rhs
        for left, rhs_list in transformed.productions.items()
        for rhs in rhs_list if rhs in transformed.variables
    ]
    details = [
        f"Unit closure {variable}: {sorted(reachable)}"
        for variable, reachable in sorted(closure.items())
    ]
    details.extend([
        f"Original grammar:\n{grammar_to_text(grammar)}",
        f"Transformed grammar:\n{grammar_to_text(transformed)}",
        f"Empty-string membership: {original_empty} -> {transformed_empty}",
        f"Finite comparison: {comparisons} words; mismatches={mismatches}",
        f"Remaining unit rules: {remaining}",
    ])
    return transformed, details, comparisons, mismatches, remaining


def unit_elimination_program():
    start_execution()
    print("Enter grammar (unit rules use A->B):")
    text = input("Grammar: ").strip().replace(";", "\n")
    start = input("Start symbol: ").strip()
    limit_text = input("Maximum unit-closure visits (default 100000): ").strip()
    try:
        max_visits = int(limit_text) if limit_text else 100000
        if max_visits <= 0:
            raise ValueError("Unit-closure visit limit must be positive.")
        grammar = parse_grammar(text, start)
        eliminated, details, comparisons, mismatches, remaining = unit_elimination_result(
            grammar, max_visits)
    except ResourceLimitError as exc:
        report("Program 7 - Unit Elimination", f"{text}; start={start}", "VALID", text,
               "Unit-closure resource guard", [str(exc)], "",
               "RESOURCE_LIMIT", "Input is not reported as a language rejection.")
        return
    except ValueError as exc:
        report("Program 7 - Unit Elimination", text, "FAILED", text,
               "Grammar parsing", [str(exc)], "", "INVALID_INPUT", "Malformed grammar.")
        return
    report("Program 7 - Unit Elimination", text, "VALID", text,
           "Directed unit-edge reachability and transitive closure",
           details, grammar_to_text(eliminated),
           "UNIT_ELIMINATION_COMPLETE" if not mismatches and not remaining
           else "VERIFICATION_MISMATCH",
           f"Ran {comparisons} finite membership comparisons; remaining unit rules={remaining}; "
           f"mismatches={mismatches}.",
           "Finite comparisons are sanity checks and do not prove language equivalence.")


def grammar_normalization_pipeline():
    start_execution()
    text = input("Enter grammar for epsilon then unit elimination: ").strip().replace(";", "\n")
    start = input("Start symbol: ").strip()
    limit_text = input("Maximum transformation operations (default 100000): ").strip()
    try:
        max_operations = int(limit_text) if limit_text else 100000
        if max_operations <= 0:
            raise ValueError("Transformation operation limit must be positive.")
        original = parse_grammar(text, start)
        after_epsilon = eliminate_epsilon(original, max_operations)
        after_unit, closure, _ = unit_elimination(after_epsilon, max_operations)
        comparisons, mismatches = compare_grammar_membership(original, after_unit)
    except ResourceLimitError as exc:
        report("Grammar Normalization Pipeline", text, "VALID", text,
               "Pipeline resource guard", [str(exc)], "",
               "RESOURCE_LIMIT", "Input is not reported as a language rejection.")
        return
    except ValueError as exc:
        report("Grammar Normalization Pipeline", text, "FAILED", text,
               "Grammar parsing", [str(exc)], "", "INVALID_INPUT", str(exc))
        return
    steps = [
        "Original grammar:\n" + grammar_to_text(original),
        "After epsilon elimination:\n" + grammar_to_text(after_epsilon),
        "After unit elimination:\n" + grammar_to_text(after_unit),
    ]
    steps.extend(f"Unit closure {variable}: {sorted(reachable)}"
                 for variable, reachable in sorted(closure.items()))
    steps.append(f"Finite comparison: {comparisons} words; mismatches={mismatches}")
    report("Grammar Normalization Pipeline", text, "VALID", grammar_to_text(original),
           "Epsilon elimination followed by unit elimination", steps,
           grammar_to_text(after_unit),
           "PIPELINE_COMPLETE" if not mismatches else "VERIFICATION_MISMATCH",
           "Intermediate grammars are shown; transformation reasoning is the equivalence basis.",
           "Finite comparisons are sanity checks and do not prove language equivalence.")


def menu():
    print("\nTheory of Automata Integrated Toolkit")
    print("1 - Pumping Lemma")
    print("2 - Simple Present English CFG")
    print("3 - Left/Right Derivation")
    print("4 - Guided Mathematical CFG")
    print("5 - Right-Linear Grammar to DFA")
    print("6 - Epsilon Production Elimination")
    print("7 - Unit Production Elimination")
    print("8 - Epsilon then Unit Elimination Pipeline")
    print("0 - Exit")
    choice = input("Choose program: ").strip()
    actions = {
        "1": pumping_lemma, "2": english_cfg, "3": derivation_program,
        "4": mathematical_cfg, "5": right_linear_dfa,
        "6": epsilon_elimination, "7": unit_elimination_program,
        "8": grammar_normalization_pipeline,
    }
    if choice == "0":
        return False
    if choice not in actions:
        print("INVALID_INPUT: Unknown menu choice.")
    else:
        actions[choice]()
    return True


if __name__ == "__main__":
    while menu():
        pass
