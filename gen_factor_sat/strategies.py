import heapq
import operator as op
from typing import Generic, TypeVar

from gen_factor_sat import tseitin
from gen_factor_sat.tseitin import Symbol, Constant, ZERO, ONE

T = TypeVar('T')


class Strategy(Generic[T]):
    def wire_and(self, x: T, y: T) -> T:
        pass

    def wire_or(self, x: T, y: T) -> T:
        pass

    def wire_not(self, x: T) -> T:
        pass


class EvalStrategy(Strategy[Constant]):

    def wire_and(self, x: Constant, y: Constant) -> Constant:
        return bin((x == '1') and (y == '1'))[2:]

    def wire_or(self, x: Constant, y: Constant) -> Constant:
        return bin((x == '1') or (y == '1'))[2:]

    def wire_not(self, x: Constant) -> Constant:
        return bin(not (x == '1'))[2:]


class TseitinStrategy(Strategy[Symbol]):

    def __init__(self, variables):
        self.variables = list(map(op.neg, variables))
        heapq.heapify(self.variables)

        self.clauses = set()

    def wire_and(self, x: Symbol, y: Symbol) -> Symbol:
        if is_constant(x) or is_constant(y):
            return constant_and(x, y)
        else:
            z = self.__next_variable()
            self.clauses.update(tseitin.and_equality(x, y, z))
            return z

    def wire_or(self, x: Symbol, y: Symbol) -> Symbol:
        if is_constant(x) or is_constant(y):
            return constant_or(x, y)
        else:
            z = self.__next_variable()
            self.clauses.update(tseitin.or_equality(x, y, z))
            return z

    def wire_not(self, x: Symbol) -> Symbol:
        if is_constant(x):
            return constant_not(x)
        else:
            return -x

    def assume(self, x: Symbol, value: Constant) -> Constant:
        if is_constant(x) and x != value:
            z = self.__next_variable()
            self.clauses.update(tseitin.empty_clause(z))
        elif not is_constant(x):
            if value == ONE:
                self.clauses.add(frozenset([x]))
            else:
                self.clauses.add(frozenset([-x]))

        return value

    def __next_variable(self):
        # heapq does not support a max heap => Reverse order
        try:
            z = -self.variables[0] + 1
        except IndexError:
            z = 1

        heapq.heappush(self.variables, -z)
        return z


def is_constant(x):
    return x == ZERO or x == ONE


def constant_and(x, y):
    if x == ZERO or y == ZERO:
        return ZERO
    elif x == ONE:
        return y
    elif y == ONE:
        return x


def constant_or(x, y):
    if x == ONE or y == ONE:
        return ONE
    elif x == ZERO:
        return y
    elif y == ZERO:
        return x


def constant_not(x):
    if x == ZERO:
        return ONE
    elif x == ONE:
        return ZERO