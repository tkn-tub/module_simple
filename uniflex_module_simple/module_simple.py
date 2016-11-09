import logging
import random
import time
import queue
import wishful_upis as upis
from uniflex.core import modules
from uniflex.core import exceptions

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class SimpleModule(modules.DeviceModule):
    def __init__(self):
        super(SimpleModule, self).__init__()
        self.log = logging.getLogger('SimpleModule')
        self.channel = 1
        self.power = 1

        self.stopRssi = True
        self.rssiSampleQueue = queue.Queue()

        self._packetLossEventRunning = False
        self._spectralScanServiceRunning = False

    @modules.on_start()
    def myFunc_1(self):
        self.log.info("This function is executed on agent start".format())

    @modules.on_exit()
    def myFunc_2(self):
        self.log.info("This function is executed on agent exit".format())

    @modules.on_connected()
    def myFunc_3(self):
        self.log.info("This function is executed on connection"
                      " to global controller".format())

    @modules.on_disconnected()
    def myFunc_4(self):
        self.log.info(
            "This function is executed after connection with global"
            " controller was lost".format())

    @modules.on_first_call_to_module()
    def myFunc_5(self):
        self.log.info(
            "This function is executed before first UPI"
            " call to module".format())

    def before_set_channel(self):
        self.log.info("This function is executed before set_channel".format())

    def after_set_channel(self):
        self.log.info("This function is executed after set_channel".format())

    @modules.before_call(before_set_channel)
    @modules.after_call(after_set_channel)
    @modules.bind_function(upis.wifi.radio.set_channel)
    def set_channel(self, channel, iface):
        self.log.info("Simple Module sets channel: {} on device: {} and iface: {}".format(
            channel, self.device, iface))
        self.channel = channel
        return ["SET_CHANNEL_OK", channel, 0]

    @modules.bind_function(upis.wifi.radio.get_channel)
    def get_channel(self, iface):
        self.log.debug(
            "Simple Module gets channel of device: {} and iface: {}"
            .format(self.device, iface))
        return self.channel

    @modules.bind_function(upis.radio.set_tx_power)
    def set_tx_power(self, power, iface):
        self.log.debug("Simple Module sets power: {} on device: {} and iface: {}".format(
            power, self.device, iface))
        self.power = power
        return {"SET_TX_POWER_OK_value": power}

    @modules.bind_function(upis.radio.get_tx_power)
    def get_tx_power(self, iface):
        self.log.debug(
            "Simple Module gets TX power on device: {} and iface: {}".format(self.device, iface))
        return self.power

    @modules.event_enable(upis.radio.PacketLossEvent)
    def packet_loss_event_enable(self):
        self._packetLossEventRunning = True

        while self._packetLossEventRunning:
            self.log.debug("Packet Lost")
            event = upis.radio.PacketLossEvent()
            # yeld or send Event to controller
            self.send_event(event)
            time.sleep(random.uniform(0, 10))

    @modules.event_disable(upis.radio.PacketLossEvent)
    def packet_loss_event_disable(self):
        self._packetLossEventRunning = False

    @modules.service_start(upis.radio.SpectralScanService)
    def spectral_scan_service_start(self):
        self._spectralScanServiceRunning = True

        while self._spectralScanServiceRunning:
            self.log.debug("Spectral scan sample")
            sample = upis.radio.SpectralScanSampleEvent(
                sample=random.uniform(0, 64))
            self.send_event(sample)
            time.sleep(1)

    @modules.service_stop(upis.radio.SpectralScanService)
    def spectral_scan_service_stop(self):
        self._spectralScanServiceRunning = False

    @modules.on_function(upis.radio.clean_per_flow_tx_power_table)
    def clean_per_flow_tx_power_table(self, iface):
        self.log.debug("clean per flow tx power table".format())
        raise exceptions.FunctionExecutionFailedException(
            func_name='radio.clean_per_flow_tx_power_table', err_msg='wrong')
