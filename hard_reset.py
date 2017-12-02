import sys
from flax.jobs import reset

file = 'production.ini'

if len(sys.argv) > 1:
    file = sys.argv[1]

reset.hard(file)
