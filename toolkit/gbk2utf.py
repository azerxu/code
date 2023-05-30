#!/usr/bin/env python
# coding: utf-8

import sys


def trans(filename):
    with open(filename, encoding="gb18030") as f:
        for line in f:
            print(line, end="")


if __name__ == "__main__":
    print (ord ('a'))
    for fname in sys.argv[1:]:
        trans(fname)
