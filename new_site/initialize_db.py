import os
import sys
import transaction
from datetime import datetime

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from .models import (
    DBSession,
    User,
    Captain,
    Base
)

from .security import hash_password


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
    with transaction.manager:
        user_model = User(username='admin', email='kyuthegamer@gmail.com', 
            hash_string=hash_password('#Precious0'),
            created_at=datetime.utcnow())
        DBSession.add(user_model)
        transaction.commit()
        player_model = Captain(uid=user_model.uid, username=user_model.username,
            team='Black', experience=1, level=1, troops=50, location=2.2, last_active=datetime.utcnow())
        print(player_model.uid)
        DBSession.add(player_model)

