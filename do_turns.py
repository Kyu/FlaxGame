import sys
from flax.jobs import turns

file = 'production.ini'

if len(sys.argv) > 1:
    file = sys.argv[1]

turns.start(file)
