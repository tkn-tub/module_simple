import time
import logging
import random

from datetime import datetime

from sbi.wifi.net_device import WiFiNetDevice
from sbi.wifi.events import PacketLossEvent, SpectralScanSampleEvent

from uniflex.core import modules
from uniflex.core import exceptions
from uniflex.core.common import UniFlexThread

__author__ = "Piotr Gawlowicz, Sascha Rösler"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de, s.roesler@campus.tu-berlin.de"


class SpectralScanner(UniFlexThread):
    """docstring for SpectralScanner"""

    def __init__(self, module):
        super().__init__(module)

    def task(self):
        while not self.is_stopped():
            self.module.log.info("Spectral scan sample")
            sample = SpectralScanSampleEvent(
                sample=random.uniform(0, 64))
            self.module.send_event(sample)
            time.sleep(1)


class PacketLossMonitor(UniFlexThread):
    """docstring for SpectralScanner"""

    def __init__(self, module):
        super().__init__(module)

    def task(self):
        while not self.is_stopped():
            self.module.log.debug("Packet Lost")
            event = PacketLossEvent()
            # yeld or send Event to controller
            self.module.send_event(event)
            time.sleep(random.uniform(0, 10))


class SimpleModule4(modules.DeviceModule, WiFiNetDevice):
    def __init__(self, **kwargs):
        super(SimpleModule4, self).__init__()
        self.log = logging.getLogger('SimpleModule')
        self.channel = 1
        self.chw = 'HT20'       # channel bandwidth
        self.power = 1

        self.stopRssi = True

        self._packetLossMonitor = PacketLossMonitor(self)
        self._spectralScanner = SpectralScanner(self)
        
        self.connectedDevices = {}
        
        if "MAC_List" in kwargs:
            for connectedMAC in kwargs["MAC_List"]:
                self.connectedDevices[connectedMAC] = {
                    "inactive time": 0,
                    "rx bytes":	            0,
                    "rx packets":           0,
                    "tx bytes":             0,
                    "tx packets":           0,
                    "tx retries":           0,
                    "tx failed":            0,
                    "signal":               -60,
                    "signal avg":           -59,
                    "tx bitrate":           144.4,
                    "rx bitrate":           144.4,
                    "expected throughput":  46.875,
                    "authorized":           "yes",
                    "authenticated":        "yes",
                    "preamble":             "long",
                    "WMM/WME":              "yes",
                    "MFP":                  "no",
                    "TDLS peer":            "no",
                    "last update":          datetime.now()}
        else:
            self.log.warning("There are no conneted devices!")

    @modules.on_start()
    def _myFunc_1(self):
        self.log.info("This function is executed on agent start".format())

    @modules.on_exit()
    def _myFunc_2(self):
        self.log.info("This function is executed on agent exit".format())

    @modules.on_connected()
    def _myFunc_3(self):
        self.log.info("This function is executed on connection"
                      " to global controller".format())

    @modules.on_disconnected()
    def _myFunc_4(self):
        self.log.info(
            "This function is executed after connection with global"
            " controller was lost".format())

    @modules.on_first_call_to_module()
    def _myFunc_5(self):
        self.log.info(
            "This function is executed before first UPI"
            " call to module".format())

    def _before_set_channel(self):
        self.log.info("This function is executed before set_channel".format())

    def _after_set_channel(self):
        self.log.info("This function is executed after set_channel".format())

    @modules.before_call(_before_set_channel)
    @modules.after_call(_after_set_channel)
    def set_channel(self, channel, iface, **kwargs):
        self.log.info(("Simple Module sets channel: {} " +
                       "on device: {} and iface: {}")
                      .format(channel, self.device, iface))
        self.channel = channel
        if "channel_width" in kwargs:
            if kwargs["channel_width"] in [None|'HT20'|'HT40-'|'HT40+']:
                self.chw = kwargs["channel_width"]
            else:
                self.log.error("The given channel_width is invalid")
        return ["SET_CHANNEL_OK", channel, 0]

    def get_channel(self, iface):
        self.log.debug(
            "Simple Module gets channel of device: {} and iface: {}"
            .format(self.device, iface))
        return self.channel

    def get_channel_width(self, iface):
        self.log.debug(
            "Simple Module gets channel of device: {} and iface: {}"
            .format(self.device, iface))
        return self.chw

    def set_tx_power(self, power, iface):
        self.log.debug("Set power: {} on device: {} and iface: {}"
                       .format(power, self.device, iface))
        self.power = power
        return {"SET_TX_POWER_OK_value": power}

    def get_tx_power(self, iface):
        self.log.debug(
            "Simple Module gets TX power on device: {} and iface: {}"
            .format(self.device, iface))
        return self.power

    def packet_loss_monitor_start(self):
        if self._packetLossMonitor.is_running():
            return True

        self.log.info("Start Packet Loss Monitor")
        self._packetLossMonitor.start()
        return True

    def packet_loss_monitor_stop(self):
        self.log.info("Stop Packet Loss Monitor")
        self._packetLossMonitor.stop()
        return True

    def is_packet_loss_monitor_running(self):
        return self._packetLossMonitor.is_running()

    def get_interfaces(self):
        self.log.info("read interfaces")
        return ['wlan0']

    def spectral_scan_start(self):
        if self._spectralScanner.is_running():
            return True

        self.log.info("Start spectral scanner")
        self._spectralScanner.start()
        return True

    def spectral_scan_stop(self):
        self.log.info("Stop spectral scanner")
        self._spectralScanner.stop()
        return True

    def is_spectral_scan_running(self):
        return self._spectralScanner.is_running()

    def clean_per_flow_tx_power_table(self, iface):
        self.log.debug("clean per flow tx power table".format())
        raise exceptions.FunctionExecutionFailedException(
            func_name='radio.clean_per_flow_tx_power_table', err_msg='wrong')

    def get_info_of_connected_devices(self, ifaceName):
        '''
            Returns information about associated STAs
            for a node running in AP mode
            tbd: use Netlink API
        '''

        self.log.info("Simple Module generates info on assoc clients on iface: %s" % str(ifaceName))

        res = {}
        
        for mac_addr in self.connectedDevices:
            values = self.connectedDevices[mac_addr]
            
            res[mac_addr] = {
                "inactive time":    (str(values["inactive time"]), "ms"),
                "rx bytes":         (str(values["rx bytes"]), None),
                "rx packets":       (str(values["rx packets"]), None),
                "tx bytes":         (str(values["tx bytes"]), None),
                "tx packets":       (str(values["tx packets"]), None),
                "tx retries":       (str(values["tx retries"]), None),
                "tx failed":        (str(values["tx failed"]), None),
                "signal":           (str(values["signal"]), "dBm"),
                "signal avg":       (str(values["signal avg"]), "dBm"),
                "tx bitrate":       (str(values["tx bitrate"]), "MBit/sec"),
                "rx bitrate":       (str(values["rx bitrate"]), "MBit/sec"),
                "expected throughput":(str(values["expected throughput"]), "Mbps"),
                "authorized":       (values["authorized"], None),
                "authenticated":    (values["authenticated"], None),
                "preamble":         (values["preamble"], None),
                "WMM/WME":          (values["WMM/WME"], None),
                "MFP":              (values["MFP"], None),
                "TDLS peer":        (values["TDLS peer"], None),
                "timestamp":        (str(datetime.now()), None)}
        return res

    def set_packet_counter(self, flows, ifaceName):
        self.log.info("Simple Module generates some traffic for clients on iface: %s" % str(ifaceName))
        for mac_addr in self.connectedDevices:
            flowsOnChannel = 0
            for flow in flows:
                if flow["channel number"] == self.channel:
                    flowsOnChannel += 1
            
            lastUpdate = self.connectedDevices[mac_addr]["last update"]
            timestamp = datetime.now()
            
            
            dif = timestamp - lastUpdate
            difMs = (dif.total_seconds() * 1000 *  + 1 + dif.microseconds / 1000.0)
            
            newRxPackets = random.uniform(0, (dif.total_seconds() / 2.0 + 1))
            self.connectedDevices[mac_addr]["rx packets"] += int(newRxPackets)
            self.connectedDevices[mac_addr]["rx bytes"] += int(newRxPackets * random.uniform(100, 200))
            
            newTxPackets = difMs / 1000.0 * 7.0 / flowsOnChannel #+ random.uniform(0, difMs / 10)
            self.connectedDevices[mac_addr]["tx packets"] += int(newTxPackets)
            self.connectedDevices[mac_addr]["tx bytes"] += int(newTxPackets * random.uniform(700000, 800000))
            
            self.connectedDevices[mac_addr]["last update"] = timestamp
