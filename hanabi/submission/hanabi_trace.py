#!/usr/bin/env python3

import sys 



if len(sys.argv) != 3:
    print("Usage: hanabi_trace.py file.in file.ans")
    sys.exit(0)

    #BLUE='\x1B[34m'
    #RED='\x1B[31m'
    #RESET='\x1B[0m'

BLUE='# '
RED='  '
RESET=''


def readlines(filename):
    L = [] 
    for line in open(filename, "r"):
        L.append(line.strip())
    return L 

IN = readlines(sys.argv[1])
ANS = readlines(sys.argv[2])

d = {"t 1": 1, "m": 2, "r": 3, "s": 3}

i = 0
for line in IN:
    print(RED, line, RESET, sep='')
    if line in d:
        for _ in range(d[line]):
            if i < len(ANS):
                s = ANS[i]
            else:
                s = "#EOF"
            print(BLUE, s, RESET, sep='')
            i += 1 


    
