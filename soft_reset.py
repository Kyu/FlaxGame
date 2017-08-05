import sys
from new_site.jobs import reset

file = 'production.ini'

if len(sys.argv) > 1:
    file = sys.argv[1]

reset.soft(file)