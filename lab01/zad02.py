import sys


def zad02():
    with open(sys.argv[1], 'rb') as src, open(sys.argv[2], 'wb') as dst:
        for line in src:
            dst.write(line)


zad02()