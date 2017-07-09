import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from .models import (
    DBSession,
    Hex,
    Base
)


def gen_hexes():
    hexes = {}
    for x in range(1, 11):
        for y in range(1, 11):
            value = "{0}.{1}".format(x, y)
            if value not in hexes:
                hexes[value] = [x, y]
    return hexes


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    # TODO: Figure this shit out
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    hexes = gen_hexes()
    hex_objects = []
    for k, v in hexes.items():
        hex_objects.append(Hex(name=k, x=v[0], y=v[1]))

    with transaction.manager:
        for i in hex_objects:
            DBSession.add(i)
        transaction.commit()

    ''''
    with transaction.manager:
        user_model = User(username='admin', email='ee@gmail.com',
            password=hash_password('pw'),
            created_at=datetime.utcnow())
        DBSession.add(user_model)
        transaction.commit()
        player_model = Player(uid=user_model.uid, username=user_model.username, squad_type="Captain",
            team='Black', experience=1, level=1, troops=50, location=2.2, last_active=datetime.utcnow())
        print(player_model.uid)
        DBSession.add(player_model)
    '''

