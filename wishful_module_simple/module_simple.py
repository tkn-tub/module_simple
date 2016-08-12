import logging
import random
import time
import queue
import wishful_upis as upis
import wishful_framework as wishful_module

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


@wishful_module.build_module
class SimpleModule(wishful_module.AgentModule):
    def __init__(self):
        super(SimpleModule, self).__init__()
        self.log = logging.getLogger('SimpleModule')
        self.channel = 1
        self.power = 1

        self.stopRssi = True
        self.rssiSampleQueue = queue.Queue()

        self._packetLossEventRunning = False
        self._spectralScanServiceRunning = False

    @wishful_module.on_start()
    def myFunc_1(self):
        self.log.info("This function is executed on agent start".format())

    @wishful_module.on_exit()
    def myFunc_2(self):
        self.log.info("This function is executed on agent exit".format())

    @wishful_module.on_connected()
    def myFunc_3(self):
        self.log.info("This function is executed on connection"
                      " to global controller".format())

    @wishful_module.on_disconnected()
    def myFunc_4(self):
        self.log.info(
            "This function is executed after connection with global"
            " controller was lost".format())

    @wishful_module.on_first_call_to_module()
    def myFunc_5(self):
        self.log.info(
            "This function is executed before first UPI"
            " call to module".format())

    def before_set_channel(self):
        self.log.info("This function is executed before set_channel".format())

    def after_set_channel(self):
        self.log.info("This function is executed after set_channel".format())

    @wishful_module.before_call(before_set_channel)
    @wishful_module.after_call(after_set_channel)
    @wishful_module.on_function(upis.wifi.radio.set_channel)
    def set_channel(self, channel):
        self.log.info("Simple Module sets channel: {} on device: {}".format(
            channel, self.device))
        self.channel = channel
        return ["SET_CHANNEL_OK", channel, 0]

    @wishful_module.on_function(upis.wifi.radio.get_channel)
    def get_channel(self):
        self.log.debug(
            "Simple Module gets channel of device: {}"
            .format(self.device))
        return self.channel

    @wishful_module.on_function(upis.radio.set_power)
    def set_power(self, power):
        self.log.debug("Simple Module sets power: {} on device: {}".format(
            power, self.device))
        self.power = power
        return {"SET_POWER_OK_value": power}

    @wishful_module.bind_function(upis.radio.get_power)
    def get_power(self):
        self.log.debug(
            "Simple Module gets power on device: {}".format(self.device))
        return self.power

    @wishful_module.run_in_thread()
    def before_get_rssi(self):
        self.log.info("This function is executed before get_rssi".format())
        self.stopRssi = False
        while not self.stopRssi:
            time.sleep(0.2)
            sample = random.randint(-90, 30)
            self.rssiSampleQueue.put(sample)

        # empty sample queue
        self.log.info("Empty sample queue".format())
        while True:
            try:
                self.rssiSampleQueue.get(block=True, timeout=0.1)
            except:
                self.log.info("Sample queue is empty".format())
                break

    def after_get_rssi(self):
        self.log.info("This function is executed after get_rssi".format())
        self.stopRssi = True

    @wishful_module.before_call(before_get_rssi)
    @wishful_module.after_call(after_get_rssi)
    @wishful_module.bind_function(upis.radio.get_rssi)
    def get_rssi(self):
        self.log.debug("Get RSSI".format())
        while True:
            yield self.rssiSampleQueue.get()

    @wishful_module.bind_event_start(upis.radio.PacketLossEvent)
    def packet_loss_event_start(self):
        self._packetLossEventRunning = True

        while self._packetLossEventRunning:
            self.log.info("Packet Lost")
            event = upis.radio.PacketLossEvent()
            # yeld or send Event to controller
            self.send_event(event)
            time.sleep(5)

    @wishful_module.bind_event_stop(upis.radio.PacketLossEvent)
    def packet_loss_event_stop(self):
        self._packetLossEventRunning = False

    @wishful_module.bind_service_start(upis.radio.SpectralScanService)
    def spectral_scan_service_start(self):
        self._spectralScanServiceRunning = True

        while self._spectralScanServiceRunning:
            self.log.info("Spectral scan sample")
            service = upis.radio.SpectralScanServiceMsg(samples=[1, 3, 4])
            self.send_service(service)
            # yeld or send Service (sample) to controller
            time.sleep(5)

    @wishful_module.bind_service_stop(upis.radio.SpectralScanService)
    def spectral_scan_service_stop(self):
        self._spectralScanServiceRunning = False
