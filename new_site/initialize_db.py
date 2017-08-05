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
    Hex,
    Base,
    Team,
    gen_hexes,
)


# If invalid arguments used
def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)

    # SQLAlchemy setup
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    hexes = gen_hexes()
    with transaction.manager:
        DBSession.add_all(hexes)
        DBSession.add(Team(name='Black', capital='2.9'))
        DBSession.add(Team(name='Blue', capital='9.9'))
        DBSession.add(Team(name='Yellow', capital='9.2'))
        DBSession.add(Team(name='Red', capital='2.2'))

        transaction.commit()

    ''''
    with transaction.manager:
        user_model = User(username='admin', email='ee@gmail.com',
            password=hash_password('pw'),
            created_at=datetime.utcnow())
        DBSession.add(user_model)
        transaction.commit()
        player_model = Player(id=user_model.id, username=user_model.username, squad_type="Captain",
            team='Black', experience=1, level=1, troops=50, location=2.2, last_active=datetime.utcnow())
        print(player_model.id)
        DBSession.add(player_model)
    '''

