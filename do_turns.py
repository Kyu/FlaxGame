import sys
from new_site.jobs import turns

file = 'development.ini'

if len(sys.argv) > 1:
    file = sys.argv[1]

turns.start(file)
