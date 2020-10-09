#!/bin/sh

autoclone ~/sigs fridge:git/sigs.git

printf "\nMarius Gedminas\n-- \n"
python3 ~/sigs/tools/sig.py
