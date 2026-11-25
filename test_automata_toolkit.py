import unittest
from unittest.mock import patch

import automata_toolkit as toolkit


class PumpingTests(unittest.TestCase):
    def test_empty_witness_spellings(self):
        for value in ("", "lambda", "Lambda", "λ", "ε", "epsilon"):
            self.assertEqual(toolkit.parse_witness(value), "")

    def test_nonempty_witness_is_preserved(self):
        self.assertEqual(toolkit.parse_witness("  aa  "), "aa")

    def test_anbn_member(self):
        self.assertTrue(toolkit.in_supported_language("a^n b^n", "aa bb".replace(" ", "")))

    def test_anbn_not_member(self):
        self.assertFalse(toolkit.in_supported_language("a^n b^n", "aab"))

    def test_decompositions(self):
        parts = list(toolkit.enumerate_decompositions("aabb", 3))
        self.assertTrue(parts)
        self.assertTrue(all(y and len(x + y) <= 3 for x, y, z in parts))

    def test_alphabet_matches_language(self):
        self.assertTrue(toolkit.validate_alphabet("a^n b^n c^n", "a,b,c"))

    def test_alphabet_mismatch_rejected(self):
        self.assertFalse(toolkit.validate_alphabet("a*", "a,b"))

    def test_anbn_symbolic_proof(self):
        status, _ = toolkit.pumping_proof_status("a^n b^n", "aabb", 2)
        self.assertEqual(status, "NON_REGULAR_PROVED")

    def test_abc_symbolic_proof(self):
        status, _ = toolkit.pumping_proof_status("a^n b^n c^n", "aabbcc", 2)
        self.assertEqual(status, "NON_REGULAR_PROVED")

    def test_noncanonical_witness_is_inconclusive(self):
        status, _ = toolkit.pumping_proof_status("a^n b^n", "aabb", 3)
        self.assertEqual(status, "INCONCLUSIVE")

    def test_empty_y_rejected(self):
        self.assertFalse(toolkit.validate_decomposition("aabb", 2, "a", "", "abb")[0])

    def test_wrong_decomposition_rejected(self):
        self.assertFalse(toolkit.validate_decomposition("aabb", 2, "a", "a", "b")[0])

    def test_xy_longer_than_p_rejected(self):
        self.assertFalse(toolkit.validate_decomposition("aabb", 1, "", "aa", "bb")[0])


class EnglishCfgTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sentences = toolkit.generate_simple_sentences()

    def test_valid_affirmative(self):
        self.assertIn("He plays cricket.", self.sentences)

    def test_valid_negative(self):
        self.assertIn("She does not play cricket.", self.sentences)

    def test_valid_interrogative(self):
        self.assertIn("Does he play cricket?", self.sentences)

    def test_no_irregular_form(self):
        self.assertNotIn("He play cricket.", self.sentences)

    def test_cfg_has_three_start_forms(self):
        self.assertEqual(len(toolkit.english_cfg_productions()["Start"]), 3)

    def test_singular_and_plural_you_have_separate_feature_rules(self):
        productions = toolkit.english_cfg_productions()
        self.assertIn(("You",), productions["SecondSingular"])
        self.assertIn(("You",), productions["SecondPlural"])
        self.assertIn(("you",), productions["SecondSingularQuestion"])
        self.assertIn(("you",), productions["SecondPluralQuestion"])

    def test_cfg_generates_expected_sentence_count(self):
        self.assertEqual(len(self.sentences), 1050)

    def test_first_person_plural_base_verb(self):
        self.assertIn("We study English.", self.sentences)

    def test_third_person_plural_base_verb(self):
        self.assertIn("They teach cricket.", self.sentences)

    def test_question_first_person(self):
        self.assertIn("Do I read books?", self.sentences)

    def test_rejects_bad_auxiliary_agreement(self):
        tokens = ("Does", "they", "study", "English", "?")
        trees, _ = toolkit.parse_cfg_trees(toolkit.english_cfg_productions(),
                                           tokens, "Start", 5)
        self.assertFalse(trees)


class GrammarTests(unittest.TestCase):
    def test_parse_grammar(self):
        grammar = toolkit.parse_grammar("S->AB\nA->aA|a\nB->bB|b")
        self.assertEqual(grammar.start, "S")
        self.assertIn("a", grammar.terminals)

    def test_nullable_fixed_point_indirect(self):
        grammar = toolkit.parse_grammar("S->AB\nA->ε\nB->A")
        _, nullable = toolkit.nullable_fixed_point(grammar.productions)
        self.assertIn("S", nullable)
        self.assertIn("A", nullable)
        self.assertIn("B", nullable)

    def test_epsilon_preserves_empty_start(self):
        grammar = toolkit.parse_grammar("S->A|a\nA->ε")
        eliminated = toolkit.eliminate_epsilon(grammar)
        self.assertNotEqual(eliminated.start, grammar.start)

    def test_epsilon_no_fresh_start(self):
        grammar = toolkit.parse_grammar("S->a\nA->ε")
        eliminated = toolkit.eliminate_epsilon(grammar)
        self.assertEqual(eliminated.start, grammar.start)

    def test_unit_chain(self):
        grammar = toolkit.parse_grammar("S->A\nA->B\nB->b")
        eliminated, closure, _ = toolkit.unit_elimination(grammar)
        self.assertIn("b", eliminated.productions["S"])
        self.assertIn("B", closure["S"])

    def test_unit_cycle(self):
        grammar = toolkit.parse_grammar("A->B\nB->A")
        eliminated, closure, _ = toolkit.unit_elimination(grammar)
        self.assertEqual(eliminated.productions["A"], ())
        self.assertIn("B", closure["A"])

    def test_right_linear_accept(self):
        rhs = toolkit.parse_right_linear("S->aS|bA|ε\nA->bA|a")
        self.assertIn("ε", rhs["S"])

    def test_reject_left_linear(self):
        with self.assertRaises(ValueError):
            toolkit.parse_right_linear("S->Sa")


class DerivationTests(unittest.TestCase):
    def test_left_right_aabb(self):
        grammar = toolkit.parse_grammar("S->AB\nA->aA|a\nB->bB|b")
        left, right = toolkit.left_right_derivations(grammar, "aabb")
        self.assertTrue(left)
        self.assertTrue(right)

    def test_derivation_steps_show_rule_and_sentential_form(self):
        grammar = toolkit.parse_grammar("S->AB;A->a;B->b")
        tree, _ = toolkit.grammar_parse_trees(grammar, "ab", 1)
        steps = toolkit.derivation_steps_from_tree(tree[0], "left")
        self.assertIn("S -> A B; sentential form: A B", steps[0])
        self.assertTrue(any("A -> a; sentential form: a B" in step for step in steps))

    def test_earley_epsilon(self):
        grammar = toolkit.parse_grammar("S->ε")
        self.assertTrue(toolkit.earley_parse(grammar, ""))

    def test_earley_nonmember(self):
        grammar = toolkit.parse_grammar("S->a")
        self.assertFalse(toolkit.earley_parse(grammar, "b"))

    def test_earley_left_recursion(self):
        grammar = toolkit.parse_grammar("S->Sa|a")
        self.assertTrue(toolkit.earley_parse(grammar, "aaa"))

    def test_earley_unit_cycle_with_exit(self):
        grammar = toolkit.parse_grammar("S->A\nA->S|a")
        self.assertTrue(toolkit.earley_parse(grammar, "a"))

    def test_enumerates_ambiguous_trees(self):
        grammar = toolkit.parse_grammar("S->SS|a")
        trees, truncated = toolkit.grammar_parse_trees(grammar, "aaa", 10)
        self.assertEqual(len(trees), 2)
        self.assertFalse(truncated)

    def test_tree_limit_is_reported(self):
        grammar = toolkit.parse_grammar("S->SS|a")
        trees, truncated = toolkit.grammar_parse_trees(grammar, "aaaa", 1)
        self.assertEqual(len(trees), 1)
        self.assertTrue(truncated)

    def test_missing_start_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_grammar("S->a", "")

    def test_undefined_nonterminal_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_grammar("S->A")

    def test_multi_character_nonterminal(self):
        grammar = toolkit.parse_grammar("Start->AUnit\nAUnit->a", "Start")
        self.assertTrue(toolkit.earley_parse(grammar, "a"))


class NumericTests(unittest.TestCase):
    def test_decimal_accept_divisor(self):
        self.assertTrue(toolkit.decimal_is_valid("125"))

    def test_divisible_by_three(self):
        with patch("builtins.input", return_value="123 divisible 3"):
            self.assertEqual(toolkit.divisibility_problems()[0], "ACCEPT")

    def test_leading_zero_rejected(self):
        self.assertFalse(toolkit.decimal_is_valid("000"))

    def test_zero_valid(self):
        self.assertTrue(toolkit.decimal_is_valid("0"))

    def test_canonical_zero_divisible(self):
        with patch("builtins.input", return_value="0 divisible 24"):
            self.assertEqual(toolkit.divisibility_problems()[0], "ACCEPT")

    def test_nondivisible_number_rejected(self):
        with patch("builtins.input", return_value="121 divisible 7"):
            self.assertEqual(toolkit.divisibility_problems()[0], "REJECT")

    def test_factorial_member(self):
        with patch("builtins.input", return_value="24 factorial 5"):
            self.assertEqual(toolkit.divisibility_problems()[0], "ACCEPT")

    def test_factorial_nonmember(self):
        with patch("builtins.input", return_value="25 factorial 5"):
            self.assertEqual(toolkit.divisibility_problems()[0], "REJECT")

    def test_factorial_limit_is_explicit(self):
        with patch("builtins.input", return_value="24 factorial 21"):
            self.assertEqual(toolkit.divisibility_problems()[0], "INVALID_INPUT")

    def test_modulo_handles_long_decimal(self):
        self.assertEqual(toolkit.decimal_remainder("9" * 1000, 3), 0)


class ProgramFourGrammarTests(unittest.TestCase):
    def test_equal_count_grammar_accepts(self):
        grammar = {"S": (("a", "S", "b"), ())}
        self.assertTrue(toolkit.earley_accepts(grammar, "S", tuple("aabb")))

    def test_equal_count_grammar_rejects(self):
        grammar = {"S": (("a", "S", "b"), ())}
        self.assertFalse(toolkit.earley_accepts(grammar, "S", tuple("aab")))

    def test_palindrome_grammar_accepts(self):
        grammar = {"S": (("a", "S", "a"), ("b", "S", "b"),
                         ("a",), ("b",), ())}
        self.assertTrue(toolkit.earley_accepts(grammar, "S", tuple("abba")))

    def test_palindrome_grammar_rejects(self):
        grammar = {"S": (("a", "S", "a"), ("b", "S", "b"),
                         ("a",), ("b",), ())}
        self.assertFalse(toolkit.earley_accepts(grammar, "S", tuple("abab")))

    def test_balanced_parentheses_grammar_accepts(self):
        grammar = {"S": (("(", "S", ")", "S"), ())}
        self.assertTrue(toolkit.earley_accepts(grammar, "S", tuple("()()")))

    def test_balanced_parentheses_grammar_rejects(self):
        grammar = {"S": (("(", "S", ")", "S"), ())}
        self.assertFalse(toolkit.earley_accepts(grammar, "S", tuple("(()")))

    def test_remainder_grammar_accepts_supported_divisors(self):
        for divisor in (2, 3, 5, 7, 10, 12, 24):
            _, _, productions, start = toolkit.remainder_dfa_grammar(divisor)
            self.assertTrue(toolkit.earley_accepts(productions, start, tuple(str(divisor))))

    def test_remainder_grammar_rejects_nonmultiple(self):
        _, _, productions, start = toolkit.remainder_dfa_grammar(10)
        self.assertFalse(toolkit.earley_accepts(productions, start, tuple("135")))

    def test_remainder_grammar_rejects_leading_zero(self):
        _, _, productions, start = toolkit.remainder_dfa_grammar(5)
        self.assertFalse(toolkit.earley_accepts(productions, start, tuple("0125")))

    def test_factorial_trie_is_exact(self):
        _, _, _, productions, start = toolkit.factorial_trie_grammar(5)
        self.assertTrue(toolkit.earley_accepts(productions, start, tuple("24")))
        self.assertFalse(toolkit.earley_accepts(productions, start, tuple("25")))


class ProgramFiveTests(unittest.TestCase):
    def test_right_linear_loop_parses(self):
        grammar = toolkit.parse_grammar("S->aS|epsilon", "S")
        toolkit.parse_right_linear("S->aS|epsilon", "S")
        self.assertIn("S", grammar.variables)

    def test_terminal_only_rule_has_fresh_accept_state(self):
        grammar = toolkit.parse_grammar("S->a", "S")
        states, transitions, accepting = toolkit.right_linear_automaton(grammar)
        self.assertEqual(len(accepting), 1)
        self.assertIn(("S", "a"), transitions)
        self.assertTrue(accepting <= states)

    def test_epsilon_rule_accepts_empty(self):
        grammar = toolkit.parse_grammar("S->epsilon", "S")
        states, transitions, accepting = toolkit.right_linear_automaton(grammar)
        self.assertTrue(toolkit.nfa_accepts("S", transitions, accepting, ""))

    def test_left_linear_rule_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_right_linear("S->Sa", "S")

    def test_undefined_state_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_right_linear("S->aA", "S")

    def test_subset_dfa_accepts_terminal_rule(self):
        grammar = toolkit.parse_grammar("S->a", "S")
        _, transitions, accepting = toolkit.right_linear_automaton(grammar)
        dfa, dfa_accepting = toolkit.subset_dfa(grammar.terminals, "S", transitions, accepting)
        self.assertTrue(toolkit.dfa_accepts(dfa, dfa_accepting, ("S",), "a"))
        self.assertFalse(toolkit.dfa_accepts(dfa, dfa_accepting, ("S",), "aa"))

    def test_generates_one_hundred_test_strings(self):
        samples = toolkit.test_strings({"a", "b"}, 100)
        self.assertEqual(len(samples), 100)
        self.assertEqual(len(set(samples)), 100)

    def test_exact_reference_dfa_equivalence(self):
        grammar = toolkit.parse_grammar("S->aS|epsilon", "S")
        _, transitions, accepting = toolkit.right_linear_automaton(grammar)
        dfa, dfa_accepting = toolkit.subset_dfa(grammar.terminals, "S", transitions, accepting)
        reference = toolkit.validate_reference_dfa(
            '{"alphabet":["a"],"start":"q","accepting":["q"],'
            '"transitions":{"q":{"a":"q"}}}', {"a"})
        self.assertTrue(toolkit.compare_dfas(
            dfa, dfa_accepting, ("S",), reference[0], reference[1],
            reference[2], {"a"})[0])

    def test_exact_reference_returns_counterexample(self):
        grammar = toolkit.parse_grammar("S->aS|epsilon", "S")
        _, transitions, accepting = toolkit.right_linear_automaton(grammar)
        dfa, dfa_accepting = toolkit.subset_dfa(grammar.terminals, "S", transitions, accepting)
        reference = toolkit.validate_reference_dfa(
            '{"alphabet":["a"],"start":"q","accepting":[],"transitions":{"q":{"a":"q"}}}',
            {"a"})
        equivalent, counterexample = toolkit.compare_dfas(
            dfa, dfa_accepting, ("S",), reference[0], reference[1],
            reference[2], {"a"})
        self.assertFalse(equivalent)
        self.assertEqual(counterexample, "")

    def test_malformed_reference_dfa_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.validate_reference_dfa("{bad json", {"a"})

    def test_subset_state_limit_is_resource_error(self):
        grammar = toolkit.parse_grammar("S->aS|b", "S")
        _, transitions, accepting = toolkit.right_linear_automaton(grammar)
        with self.assertRaises(toolkit.ResourceLimitError):
            toolkit.subset_dfa(grammar.terminals, "S", transitions, accepting, 1)

    def test_reference_product_limit_is_resource_error(self):
        grammar = toolkit.parse_grammar("S->a", "S")
        _, transitions, accepting = toolkit.right_linear_automaton(grammar)
        dfa, dfa_accepting = toolkit.subset_dfa(
            grammar.terminals, "S", transitions, accepting)
        with self.assertRaises(toolkit.ResourceLimitError):
            toolkit.compare_dfas(
                dfa, dfa_accepting, ("S",), "q", set(),
                {"q": {"a": "q"}}, {"a"}, max_pairs=1)


class ProgramSixTests(unittest.TestCase):
    def test_one_nullable_variable_expands(self):
        grammar = toolkit.parse_grammar("S->AB;A->epsilon;B->b")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertIn("B", result.productions["S"])

    def test_multiple_nullable_symbols_generate_all_subsets(self):
        grammar = toolkit.parse_grammar("S->ABC;A->epsilon;B->epsilon;C->c")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertEqual(set(result.productions["S"]), {"ABC", "AC", "BC", "C"})

    def test_indirect_nullable_start_is_preserved(self):
        grammar = toolkit.parse_grammar("S->A;A->epsilon")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertNotEqual(result.start, grammar.start)
        self.assertTrue(toolkit.earley_parse(result, ""))

    def test_nonnullable_start_does_not_gain_epsilon(self):
        grammar = toolkit.parse_grammar("S->a|b")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertEqual(result.start, grammar.start)
        self.assertFalse(toolkit.earley_parse(result, ""))

    def test_no_epsilon_productions_remain(self):
        grammar = toolkit.parse_grammar("S->aA;A->b")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertFalse(any("epsilon" == rhs or "ε" == rhs
                             for values in result.productions.values() for rhs in values))

    def test_duplicate_rules_are_deduplicated(self):
        grammar = toolkit.parse_grammar("S->A|A|a;A->epsilon")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertEqual(len(result.productions["S"]), len(set(result.productions["S"])))

    def test_nullable_cycle_terminates(self):
        grammar = toolkit.parse_grammar("S->A;A->S|epsilon")
        _, nullable = toolkit.nullable_fixed_point(grammar.productions)
        self.assertEqual(nullable, {"S", "A"})

    def test_undefined_variable_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_grammar("S->A", "S")

    def test_fifty_membership_comparisons(self):
        grammar = toolkit.parse_grammar("S->aS|epsilon")
        transformed, _, comparisons, mismatches = toolkit.epsilon_elimination_result(grammar)
        self.assertEqual(comparisons, 50)
        self.assertFalse(mismatches)
        self.assertTrue(toolkit.earley_parse(transformed, "aaa"))

    def test_fresh_start_name_avoids_collision(self):
        grammar = toolkit.parse_grammar("S0->S;S->epsilon", "S0")
        result = toolkit.eliminate_epsilon(grammar)
        self.assertNotEqual(result.start, "S0")

    def test_alternative_limit_is_resource_error(self):
        grammar = toolkit.parse_grammar("S->AB;A->epsilon;B->epsilon")
        with self.assertRaises(toolkit.ResourceLimitError):
            toolkit.eliminate_epsilon(grammar, 1)


class ProgramSevenTests(unittest.TestCase):
    def test_basic_unit_rule_removed(self):
        grammar = toolkit.parse_grammar("S->A;A->a")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertIn("a", result.productions["S"])

    def test_unit_chain_closure(self):
        grammar = toolkit.parse_grammar("S->A;A->B;B->b")
        result, closure, _ = toolkit.unit_elimination(grammar)
        self.assertIn("B", closure["S"])
        self.assertIn("b", result.productions["S"])

    def test_unit_cycle_without_exit_preserves_empty_language(self):
        grammar = toolkit.parse_grammar("A->B;B->A")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertEqual(result.productions["A"], ())

    def test_multiple_paths_deduplicate(self):
        grammar = toolkit.parse_grammar("S->A|B;A->C;B->C;C->c")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertEqual(result.productions["S"].count("c"), 1)

    def test_epsilon_behavior_preserved(self):
        grammar = toolkit.parse_grammar("S->A;A->epsilon")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertTrue(toolkit.earley_parse(result, ""))

    def test_unit_free_grammar_unchanged(self):
        grammar = toolkit.parse_grammar("S->a|b")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertEqual(result.productions["S"], grammar.productions["S"])

    def test_no_unit_rules_after_transformation(self):
        grammar = toolkit.parse_grammar("S->A;A->B;B->b")
        result, _, _ = toolkit.unit_elimination(grammar)
        self.assertFalse(any(rhs in result.variables
                             for values in result.productions.values() for rhs in values))

    def test_undefined_unit_target_rejected(self):
        with self.assertRaises(ValueError):
            toolkit.parse_grammar("S->A", "S")

    def test_fifty_membership_comparisons(self):
        grammar = toolkit.parse_grammar("S->A;A->aA|epsilon")
        _, _, comparisons, mismatches, _ = toolkit.unit_elimination_result(grammar)
        self.assertEqual(comparisons, 50)
        self.assertFalse(mismatches)

    def test_epsilon_then_unit_pipeline_preserves_language(self):
        grammar = toolkit.parse_grammar("S->A;A->B|epsilon;B->b")
        after_epsilon = toolkit.eliminate_epsilon(grammar)
        after_unit, _, _ = toolkit.unit_elimination(after_epsilon)
        self.assertTrue(toolkit.earley_parse(grammar, ""))
        self.assertTrue(toolkit.earley_parse(after_unit, ""))
        self.assertTrue(toolkit.earley_parse(after_unit, "b"))

    def test_closure_limit_is_resource_error(self):
        grammar = toolkit.parse_grammar("S->A;A->B;B->b")
        with self.assertRaises(toolkit.ResourceLimitError):
            toolkit.unit_elimination(grammar, 1)


if __name__ == "__main__":
    unittest.main()
