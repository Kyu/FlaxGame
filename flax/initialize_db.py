import os
import sys

import transaction
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    Team,
    gen_hexes,
)


# If invalid arguments used
# only arg needed is path to config file
def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    # Set up a DB from config file
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name='flax')
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    # Generate hexes and teams, insert into DB
    hexes = gen_hexes()
    with transaction.manager:
        DBSession.add_all(hexes)
        DBSession.add(Team(name='Black', capital='2.9'))
        DBSession.add(Team(name='Blue', capital='9.9'))
        DBSession.add(Team(name='Yellow', capital='9.2'))
        DBSession.add(Team(name='Red', capital='2.2'))

        transaction.commit()
