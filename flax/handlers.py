import logging
import traceback

import transaction

from .models import Log, DBSession


class SQLAlchemyHandler(logging.Handler):
    # A very basic logger that commits a LogRecord to tDB
    def emit(self, record):
        trace = None
        exc = record.__dict__['exc_info']
        if exc:
            trace = traceback.format_exc(exc)
        log = Log(
            logger=record.__dict__['name'],
            level=record.__dict__['levelname'],
            trace=trace,
            msg=record.__dict__['msg'],)
        DBSession.add(log)
        transaction.commit()
