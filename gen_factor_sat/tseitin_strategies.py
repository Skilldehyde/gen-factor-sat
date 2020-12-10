from abc import ABC
from typing import List, TypeVar, Callable, Set, Tuple, cast

from gen_factor_sat import tseitin_encoding
from gen_factor_sat.circuit import GateStrategy, GeneralSimpleCircuitStrategy
from gen_factor_sat.tseitin_encoding import Symbol, Constant, Variable, constant, variable, Clause

T = TypeVar('T')


class CNFBuilder:
    def __init__(self, number_of_variables=0):
        self.number_of_variables = number_of_variables
        self.__clauses = set()

    def build_clauses(self) -> Set[Clause]:
        return set(filter(tseitin_encoding.is_no_tautology, self.__clauses))

    def from_tseitin(self, tseitin_transformation, *args) -> Variable:
        output = self.next_variable()
        clauses = tseitin_transformation(*args, output)
        self.append_clauses(clauses)
        return output

    def next_variables(self, amount: int) -> List[Variable]:
        return [self.next_variable() for _ in range(amount)]

    def next_variable(self) -> Variable:
        self.number_of_variables += 1
        return variable(self.number_of_variables)

    def append_clauses(self, clauses: Set[Clause]):
        self.__clauses.update(clauses)


class TseitinGateStrategy(GateStrategy[Symbol, CNFBuilder]):
    zero: Constant = constant('0')
    one: Constant = constant('1')

    def assume(self, symbol: Symbol, value: Constant, writer: CNFBuilder) -> Constant:
        if self.is_constant(symbol) and symbol != value:
            writer.append_clauses({tseitin_encoding.empty_clause()})
        elif not self.is_constant(symbol):
            var = cast(Variable, symbol)  # Type hint
            if value == self.one:
                writer.append_clauses({tseitin_encoding.unit_clause(var)})
            else:
                writer.append_clauses({tseitin_encoding.unit_clause(variable(-var))})

        return value

    def wire_and(self, input_1: Symbol, input_2: Symbol, writer: CNFBuilder) -> Symbol:
        if self.is_constant(input_1) or self.is_constant(input_2):
            return self._constant_and(input_1, input_2)
        else:
            return writer.from_tseitin(tseitin_encoding.and_equality, input_1, input_2)

    def wire_or(self, input_1: Symbol, input_2: Symbol, writer: CNFBuilder) -> Symbol:
        if self.is_constant(input_1) or self.is_constant(input_2):
            return self._constant_or(input_1, input_2)
        else:
            return writer.from_tseitin(tseitin_encoding.or_equality, input_1, input_2)

    def wire_not(self, input: Symbol, writer: CNFBuilder) -> Symbol:
        if self.is_constant(input):
            return self._constant_not(input)
        else:
            var = cast(Variable, input)  # Type hint
            return variable(-var)

    def _constant_and(self, x, y):
        if x == self.zero or y == self.zero:
            return self.zero
        elif x == self.one:
            return y
        elif y == self.one:
            return x
        else:
            raise ValueError('Neither {0} nor {1} is a constant'.format(x, y))

    def _constant_or(self, x, y):
        if x == self.one or y == self.one:
            return self.one
        if x == self.zero:
            return y
        elif y == self.zero:
            return x
        else:
            raise ValueError('Neither {0} nor {1} is a constant'.format(x, y))

    def _constant_not(self, x):
        if x == self.zero:
            return self.one
        elif x == self.one:
            return self.zero
        else:
            raise ValueError('{0} is no constant'.format(x))


class TseitinCircuitStrategy(GeneralSimpleCircuitStrategy[Symbol, CNFBuilder], ABC):

    def xor(self, x: Symbol, y: Symbol, writer: CNFBuilder) -> Symbol:
        if self.is_constant(x) or self.is_constant(y):
            return self._constant_xor(x, y, writer)
        else:
            return writer.from_tseitin(tseitin_encoding.xor_equality, x, y)

    # def equality(self, x: Symbol, y: Symbol) -> Symbol:
    #     if _is_constant(x):
    #         return self.assume(y, x)
    #     elif _is_constant(y):
    #         return self.assume(x, y)
    #     else:
    #         z = self.gate_builder.cnf_builder.next_variable()
    #         self.gate_builder.cnf_builder.append_clauses(tseitin.equal_equality(x, y, z))
    #         return z

    def _constant_xor(self, x, y, writer: CNFBuilder):
        if x == self.one:
            return self.wire_not(y, writer)
        elif y == self.one:
            return self.wire_not(x, writer)
        elif x == self.zero:
            return y
        elif y == self.zero:
            return x
        else:
            raise ValueError('Neither {0} nor {1} is a constant'.format(x, y))
