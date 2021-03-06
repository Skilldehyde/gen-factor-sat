import re
from collections import Counter

import pytest

import gen_factor_sat.circuit.tseitin.encoding as te
from gen_factor_sat.factoring_sat import FactoringSat
from gen_factor_sat.formula.cnf import CNF
from gen_factor_sat.formula.symbol import variable

comment_line = re.compile('c (?P<comment>.*)')
problem_line = re.compile('p cnf (?P<variables>\\d*) (?P<clauses>\\d*)')
clause_line = re.compile('(-?[1-9][0-9]* )*0')


@pytest.mark.parametrize('clause', [
    te.empty_clause(),
    te.unit_clause(variable(42)),
    te.clause(list(map(variable, [1, -2, -4, 17])))
])
def test_clauses_to_dimacs_conversion(clause):
    dimacs_clause = CNF.clause_to_dimacs(clause)
    assert clause_line.match(dimacs_clause), 'Clauses should match the DIMACS format'

    numbers = list(map(int, dimacs_clause.split(' ')))
    assert numbers[-1] == 0, 'Clauses (including empty clauses) should have a trailing zero'

    literals = numbers[:-1]
    assert literals == list(clause), 'The conversion should write the same literals in the same order'


@pytest.mark.parametrize('num_vars, clauses', [
    (0, {}),
    (1, {te.clause(list(map(variable, [-1, 3])))}),
    (17, {te.clause(list(map(variable, [-1, -12, -4]))), te.empty_clause()})
])
def test_cnf_to_dimacs_conversion(num_vars, clauses):
    cnf = CNF(num_vars, clauses)
    dimacs = cnf.to_dimacs()

    lines = dimacs.splitlines(keepends=False)
    assert len(lines) == 1 + len(clauses), "All clauses should be written"

    assert problem_line.match(lines[0]), "The first line should contain the instance parameters"
    match = problem_line.match(lines[0])

    num_variables = int(match.group('variables'))
    num_clauses = int(match.group('clauses'))

    assert num_variables == num_vars, "The conversion should use the provided number of variables"
    assert num_clauses == len(clauses), "The conversion should write the number of clauses"


@pytest.mark.parametrize('comments', [[], ['Comment 1'], ['Comment 1', ' ', '', 'Comment 2']])
def test_comments_should_be_prepended(comments):
    num_vars = 13
    clauses = {te.clause(list(map(variable, [-1, 3]))),
               te.clause(list(map(variable, [-10, -5, 14])))}

    cnf = CNF(num_vars, clauses)
    dimacs = cnf.to_dimacs(comments=comments)

    lines = dimacs.splitlines(keepends=False)
    assert len(lines) == len(comments) + 1 + len(clauses)

    for index in range(len(comments)):
        assert comment_line.match(lines[index])
        match = comment_line.match(lines[index])
        parsed_comment = match.group('comment')
        assert parsed_comment == comments[index]


@pytest.fixture(scope='module', params=[2, 17, 2 ** 15 + 17896, 2 ** 23 + 1247561])
def factoring_instance(request):
    factor_sat = FactoringSat.factorize_number(request.param)
    return factor_sat


def test_dimacs_format(factoring_instance):
    dimacs = factoring_instance.to_dimacs()

    parsed_problem_line = False
    lines = dimacs.splitlines(keepends=False)
    for line in lines:
        if comment_line.match(line):
            assert not parsed_problem_line, 'Comments are only permitted before the problem line'
        elif problem_line.match(line):
            assert not parsed_problem_line, 'The DIMACS format should have exactly one problem line'
            parsed_problem_line = True
        elif clause_line.match(line):
            assert parsed_problem_line, 'Clauses are only permitted after the problem line'
        else:
            assert not line, "Only comment lines, problem lines, or clauses are allowed"

    assert parsed_problem_line, 'The DIMACS format should have exactly one problem line'


def test_encoded_cnf(factoring_instance):
    dimacs = factoring_instance.to_dimacs()

    clauses = []
    lines = dimacs.splitlines(keepends=False)
    for line in lines:
        if problem_line.match(line):
            match = problem_line.match(line)

            num_variables = int(match.group('variables'))
            num_clauses = int(match.group('clauses'))

            assert num_variables == factoring_instance.cnf.number_of_variables
            assert num_clauses == len(factoring_instance.cnf.clauses)

        elif clause_line.match(line):
            clause = list(map(int, line.split(' ')[:-1]))

            occurrences = Counter(clause)
            assert all(occurrences[-literal] == 0 for literal in clause)
            assert all(occurrences[literal] == 1 for literal in clause)

            clauses.append(frozenset(clause))

    assert len(clauses) == len(factoring_instance.cnf.clauses)
    assert set(clauses) == factoring_instance.cnf.clauses
