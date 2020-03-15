import sys

import spyd.wrapper_service
import spyd.options
from spyd.utils.tracing import setup_logger

setup_logger('tracing.log')

# TODO: PYTHONPATH alternative

opt = spyd.options.Options()
opt.parseOptions(sys.argv[1:])

w = spyd.wrapper_service.WrapperService(opt)
w.startService()

from twisted.internet import reactor
reactor.run()
