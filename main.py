import sys

print('TODO: PYTHONPATH alternative')

import spyd.wrapper_service
import spyd.options

opt = spyd.options.Options()
opt.parseOptions(sys.argv[1:])

print(opt)
w = spyd.wrapper_service.WrapperService(opt)
w.startService()

from twisted.internet import reactor
reactor.run()
