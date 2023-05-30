#!/usr/bin/env python
# coding: utf-8

# **********************************************************************
# file: revcom.py
# **********************************************************************

import sys

TRANS_TABLE = str.maketrans("ACGTRYMKWSNacgtrymkwsn", "TGCAYRKMWSNtgcayrkmwsn")


def revcom(seq):
    return "".join(reversed(seq.translate(TRANS_TABLE)))


def show_revcom_seq(seq):
    print(revcom(seq))


def main():
    list(map(show_revcom_seq, sys.argv[1:]))


if __name__ == "__main__":
    main()
