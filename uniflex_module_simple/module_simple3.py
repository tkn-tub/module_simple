import logging
import wishful_upis as upis
from uniflex.core import modules
from random import randint

__author__ = "Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


@modules.build_module
class SimpleModule3(modules.AgentModule):
    def __init__(self):
        super(SimpleModule3, self).__init__()
        self.log = logging.getLogger('SimpleModule3')

    @modules.on_function(upis.wifi.net.get_inactivity_time_of_connected_devices)
    def get_inactivity_time_of_connected_devices(self):
        self.log.info("SimpleModule3 get_inactivity_time_of_connected_devices")
        res = {}
        res['00:11:22:33:44:55'] = [str(randint(0,100)), 'ms']
        self.log.info(str(res))

        return res
