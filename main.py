import sys

import cipolla.wrapper_service
import cipolla.options
from cipolla.utils.tracing import setup_logger

setup_logger('tracing.log')

# TODO: PYTHONPATH alternative

opt  = cipolla.options.Options()
opt.parseOptions(sys.argv[1:])

w = cipolla.wrapper_service.WrapperService(opt)
w.startService()

from twisted.internet import reactor
reactor.run()
