import collections
import itertools
from typing import List, Tuple, DefaultDict, Iterable

import Circuit
from Circuit import ZERO
from Strategy import Strategy, T


def karatsuba(xs: List[T], ys: List[T], circuit: Strategy[T]) -> List[T]:
    if len(xs) < 20 or len(ys) < 20:
        return wallace_tree(xs, ys, circuit)

    n = max(len(xs), len(ys))
    half = (n + 1) // 2

    x1 = xs[:-half]
    x0 = xs[-half:]

    y1 = ys[:-half]
    y0 = ys[-half:]

    z0 = karatsuba(x0, y0, circuit)
    z2 = karatsuba(x1, y1, circuit) if x1 and y1 else ['0']

    # z1 = karatsuba((x1 + x0), (y1 + y0)) - z2 - z0
    sum_x = Circuit.n_bit_adder(x1, x0, ZERO, circuit) if x1 else x0
    sum_y = Circuit.n_bit_adder(y1, y0, ZERO, circuit) if y1 else y0

    z1 = karatsuba(sum_x, sum_y, circuit)
    z1 = Circuit.subtract(z1, z2, circuit)
    z1 = Circuit.subtract(z1, z0, circuit)

    # x * y = z2 * 2^(2 * half) + z1 * 2^(half) + z0
    sum = Circuit.n_bit_adder(Circuit.shift(z2, half), z1, ZERO, circuit)
    sum = Circuit.n_bit_adder(Circuit.shift(sum, half), z0, ZERO, circuit)

    return sum


def wallace_tree(xs: List[T], ys: List[T], circuit: Strategy[T]) -> List[T]:
    products = weighted_product(xs, ys, circuit)
    merged = group(products)

    while any(len(xs) > 2 for _, xs in merged.items()):
        products = itertools.chain.from_iterable([add_layer(w, xs, circuit) for w, xs in merged.items()])
        merged = group(products)

    last_carry = ZERO
    result = []
    for key in sorted(merged):
        xs = merged[key]

        if len(xs) == 1:
            x, = xs
            sum, carry = Circuit.half_adder(x, last_carry, circuit)
            last_carry = carry
            result = [sum] + result
        else:
            x, y = xs
            sum, carry = Circuit.full_adder(x, y, last_carry, circuit)
            last_carry = carry
            result = [sum] + result

    return [last_carry] + result


def weighted_product(xs: List[T], ys: List[T], circuit: Strategy[T]):
    len_xs = len(xs)
    len_ys = len(ys)

    for i, x in enumerate(xs):
        w_x = len_xs - i

        for j, y in enumerate(ys):
            w_y = len_ys - j

            weight_sum = w_x + w_y
            product = circuit.wire_and(x, y)

            yield weight_sum, product


def add_layer(w: int, xs: List[T], circuit: Strategy[T]) -> List[Tuple[int, T]]:
    if len(xs) == 1:
        return [(w, xs[0])]

    elif len(xs) == 2:
        x, y = xs
        sum, carry = Circuit.half_adder(x, y, circuit)

        return [(w, sum), (w + 1, carry)]

    elif len(xs) > 2:
        x, y, z = xs[:3]
        sum, carry = Circuit.full_adder(x, y, z, circuit)
        return [(w, sum), (w + 1, carry)] + [(w, x) for x in xs[3:]]


def group(xs: Iterable[Tuple[int, T]]) -> DefaultDict[int, List[T]]:
    result = collections.defaultdict(list)
    for k, v in xs:
        result[k].append(v)

    return result
