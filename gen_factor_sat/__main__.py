import argparse
import os
import sys

from gen_factor_sat import factoring_sat

parser = argparse.ArgumentParser(
    prog='GenFactorSat',
    description='''
    Convert the factorization of a number into a CNF. 
    The resulting CNF is represented in the DIMACS format.
    ''')
parser.add_argument('--version', action='version', version='%(prog)s v{0}'.format(factoring_sat.VERSION))

commands = ['number', 'random']
subparsers = parser.add_subparsers(dest='command', required=True)

parser_number = subparsers.add_parser(commands[0], help="specify a number to be factorized")
parser_number.add_argument('value', type=int, help="the number to be factorized")
parser_number.add_argument('-o', '--outfile', nargs='?', type=str, const='', default='-',
                           help='''
                           redirect the output from stdout to the specified file. If no filename or a directory is
                           specified, a default name is used. (default: stdout)
                           ''')

parser_random = subparsers.add_parser(commands[1], help="generate a random number to be factorized")
parser_random.add_argument('-s', '--seed', nargs='?', type=int, help='use the seed to generate a pseudorandom number')
parser_random.add_argument('--prime', dest='prime', action='store_true', default=None,
                           help='''generate a prime number''')
parser_random.add_argument('--no-prime', dest='prime', action='store_false', default=None,
                           help='''generate a composite number''')
parser_random.add_argument('-e', '--error', type=float, default=0.0,
                           help='''
                           the probability that a composite number is declared to be a prime number.
                           If set to 0 a deterministic but slower primality test is used. (default: 0.0)
                           ''')
parser_random.add_argument('max_value', metavar='max-value', type=int,
                           help='the largest value the random number can take.')
parser_random.add_argument('-o', '--outfile', nargs='?', type=str, const='', default='-',
                           help='''
                           redirect the output from stdout to the specified file. If no filename or a directory is
                           specified, a default name is used. (default: stdout)
                           ''')

args = parser.parse_args()


def write_cnf(cnf, filename, default_file):
    if filename == '-':
        sys.stdout.write(cnf.to_dimacs())
    else:
        if not filename:
            filename = default_file
        elif not os.path.isfile(filename):
            if not os.path.exists(filename):
                os.makedirs(filename)

            filename = os.path.join(filename, default_file)

        with open(filename, 'w') as file:
            file.write(cnf.to_dimacs())


if args.command == commands[0]:
    result = factoring_sat.factorize_number(args.value)
    default = 'factor_number{0}.cnf'.format(result.number)
    write_cnf(result, args.outfile, default)

elif args.command == commands[1]:
    result = factoring_sat.factorize_random_number(args.max_value, args.seed, args.prime, args.error)
    default = 'factor_seed{0}_maxn{1}.cnf'.format(result.seed, result.max_value)
    write_cnf(result, args.outfile, default)

else:
    parser.error('Invalid command: ' + str(args.command))
