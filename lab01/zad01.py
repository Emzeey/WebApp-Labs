import sys


def zad01():
    with open(sys.argv[1], 'r') as src, open(sys.argv[2], 'w') as dst:
        for line in src:
            dst.write(line)


zad01()
