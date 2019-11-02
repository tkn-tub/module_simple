import time
import logging
import random
import numpy as np
import pickle
import json

from datetime import datetime

from sbi.wifi.net_device import WiFiNetDevice
from sbi.wifi.events import PacketLossEvent, SpectralScanSampleEvent

from uniflex.core import modules
from uniflex.core import exceptions
from uniflex.core.common import UniFlexThread

__author__ = "Piotr Gawlowicz, Sascha Rösler"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de, {s.roesler}@campus.tu-berlin.de"


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
        self.log.info("This is SimpleModule4 with UUID: " + self.uuid)
        self.channel = 1
        self.chw = 'HT20'       # channel bandwidth
        self.power = 1

        self.stopRssi = True
        self.channel_change = False

        self._packetLossMonitor = PacketLossMonitor(self)
        self._spectralScanner = SpectralScanner(self)
        
        self.clientconfig = None
        
        if "myMAC" in kwargs:
            self.myMAC = kwargs['myMAC']
        else:
            self.log.error("There are no MAC-Address for the AP!")
        
        self.numsClients = [0]
        if "simulation" in kwargs:
            if "numsClients" in kwargs['simulation']:
                self.numsClients = kwargs['simulation']['numsClients']
        
        self.connectedDevices = []
        for i in range(len(self.numsClients)):
            self.connectedDevices.append({})
        
        if "clients" in kwargs:
            for connectedMAC in kwargs["clients"]:
                for i in range(len(self.numsClients)):
                    self.connectedDevices[i][connectedMAC] = {
                        "inactive time":        0,
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
        
        self.clientNumber = len(self.connectedDevices[0])
        self.scenario = 0
        
        if "neighbors" in kwargs:
            self.neighbors = kwargs["neighbors"]
        
        self.channelSwitchingTime = 100
        self.channelBandwith = 54e6
        self.channelBandwidthList = []
        self.txBytesRandom = 0
        self.mode = ""
        
        self.generatorMaxNumClients = 0
        self.generatorScenariosPerAPSetting = 0
        self.clientPrefix = "cc:cc:cc:cc:cc:"
        
        if "simulation" in kwargs:
            if "channelSwitchingTime" in kwargs['simulation']:
                self.channelSwitchingTime = kwargs['simulation']['channelSwitchingTime']
            if "channelThroughputDefault" in kwargs['simulation']:
                self.channelBandwith = kwargs['simulation']['channelThroughputDefault']
            if "channelThroughput" in kwargs['simulation']:
                self.channelBandwidthList = kwargs['simulation']['channelThroughput']
            if "txBytesRandom" in kwargs['simulation']:
                self.txBytesRandom = kwargs['simulation']['txBytesRandom']
            if "clientnum" in kwargs['simulation']:
                self.clientNumber = kwargs['simulation']['clientnum']
            if "clientconf" in kwargs['simulation']:
                self.clientconfig = kwargs['simulation']['clientconf']
            if "mode" in kwargs['simulation']:
                self.mode = kwargs['simulation']['mode']
            if "scenariosPerAPSetting" in kwargs['simulation']:
                self.generatorScenariosPerAPSetting = kwargs['simulation']['scenariosPerAPSetting']
            if "maxNumClients" in kwargs['simulation']:
                self.generatorMaxNumClients = kwargs['simulation']['maxNumClients']
            if "clientPrefix" in kwargs['simulation']:
                self.clientPrefix = kwargs['simulation']['clientPrefix']
        
        if self.mode == 'generator':
            #generate client MACs
            myMACs = []
            for i in range(self.generatorMaxNumClients):
                myMACs.append(self.clientPrefix + hex(i)[2:].zfill(2))
            
            #renew connectedDevices
            self.connectedDevices = []
            for i in range(self.generatorScenariosPerAPSetting * len(self.neighbors)):
                self.connectedDevices.append({})
            
            for connectedMAC in myMACs:
                # for each scenario, generate the client list
                for i in range(self.generatorScenariosPerAPSetting * len(self.neighbors)):
                    self.connectedDevices[i][connectedMAC] = {
                        "inactive time":        0,
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
            
            #generate numsClients
            if "scenarioBackup" in kwargs['simulation']:
                try:
                    with open(kwargs['simulation']["scenarioBackup"], 'r') as f:  # Python 3: open(..., 'wb')
                        self.numsClients = np.array(json.loads(f.read()))
                        print(self.numsClients)
                        self.log.info("Load scenario of last run")
                except ValueError as e:
                    self.numsClients = np.random.randint(self.generatorMaxNumClients, size=self.generatorScenariosPerAPSetting * len(self.neighbors))
                    self.log.info("File format is wrong" + str(e))
                except IOError as e:
                    self.log.info("File not found. Skip loading" + str(e))
                    self.numsClients = np.random.randint(self.generatorMaxNumClients, size=self.generatorScenariosPerAPSetting* len(self.neighbors))
                
                with open(kwargs['simulation']["scenarioBackup"], 'w') as f:  # Python 3: open(..., 'wb')
                    f.write(json.dumps(self.numsClients.tolist()))
            else:
                self.numsClients = np.random.randint(self.generatorMaxNumClients, size=self.generatorScenariosPerAPSetting * len(self.neighbors))
            
            #generate neighbors
            temp = []
            for i in range(self.generatorScenariosPerAPSetting):
                temp.extend(self.neighbors)
            self.neighbors = temp
        
        if self.clientconfig and self.mode == 'working':
            f = open(self.clientconfig, "r")
            self.clientNumber = int(f.readline())
            f.close()
    
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
        
        if self.channel != channel:
            self.channel_change = True
        
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
        
        if self.clientconfig and self.mode == "working":
            f = open(self.clientconfig, "r")
            self.clientNumber = int(f.readline())
            f.close()
        
        if (self.mode == "training" or self.mode == 'generator') and len(self.numsClients) > self.scenario:
            self.clientNumber = self.numsClients[self.scenario]
        
        i = 0
        for mac_addr in self.connectedDevices[self.scenario]:
            values = self.connectedDevices[self.scenario][mac_addr]
            
            if i >= self.clientNumber:
                break
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
            i += 1
        return res

    def getHwAddr(self, ifaceName=""):
        return self.myMAC
    
    def get_current_neighbours(self, ifaceName, rrmPlan):
        neighborslist = []
        for device in rrmPlan:
            if device["channel number"] == self.channel and device["mac address"] in self.neighbors[self.scenario]:
                neighborslist.append(device["mac address"])
        return neighborslist
    
    def get_neighbours(self, ifaceName):
        return self.neighbors[self.scenario]
    
    def set_packet_counter(self, rrmPlan, ifaceName, steptime=None, scenario=0):
        '''
            Simulates information about associated STAs
            Takes the current state of the network: Map AP-Channel
            Simple model: Devide bandwidth by all neighbouring devices on the same channel +1
            Number of bits is calculated by time since last call. Has internal state
            Calculate number of packets by deviding the resulting throughput by 65535 Bits/packet
        '''
        self.log.info("Simple Module generates some traffic for clients on iface: %s" % str(ifaceName))
        
        '''
        for device in rrmPlan:
            if device["channel number"] == self.channel and device["mac address"] in self.neighbors:
                sameChannelAPs += 1
        '''
        
        self.scenario = scenario
        
        if self.clientconfig and self.mode == "working":
            f = open(self.clientconfig, "r")
            self.clientNumber = int(f.readline())
            f.close()
        
        self.log.info("Simple Module rrm plan: %s" % str(rrmPlan))
        self.log.info("Simple Module scenario: %s" % str(scenario))
        self.log.info("Simple Module mode: %s" % str(self.mode))
        self.log.info("Simple Module numsClients: %s" % str(self.numsClients))
        
        if (self.mode == "training" or self.mode == "generator") and len(self.numsClients) > scenario:
            self.log.info("Simple Module switches to scenario: %s" % str(scenario))
            self.clientNumber = self.numsClients[scenario]
        
        if self.clientNumber <= 0:
            return
        
        sameChannelAPs = len(self.get_current_neighbours(ifaceName, rrmPlan))
        
        
        for mac_addr in self.connectedDevices[self.scenario]:
            lastUpdate = self.connectedDevices[self.scenario][mac_addr]["last update"]
            timestamp = datetime.now()
            
            
            dif = timestamp - lastUpdate
            difMs = (dif.total_seconds() * 1000 *  + 1 + dif.microseconds / 1000.0)
            
            if steptime:
                difMs = steptime * 1000
            
            # change of channel takes 100ms
            if self.channel_change:
                difMs -= self.channelSwitchingTime
            
            #take channel specific bandwidth
            if len(self.channelBandwidthList) >= self.channel:
                bandwidth = self.channelBandwidthList[self.channel-1] / 1000
            else:
                bandwidth = self.channelBandwith / 1000            # 54 MBit/sec in ms
            
            bandwidth /= (sameChannelAPs +1)        # devide bandwidth by number of APs in range
            bandwidth /= self.clientNumber          # devide bandwidth by number of clients
            bandwidth_packet = bandwidth / (60000 * 8)    # Bits per Packet (60000 < 65535), 0.11 p ms
            newRxPackets = 5                       # low upload
            self.connectedDevices[self.scenario][mac_addr]["rx packets"] += int(newRxPackets)
            self.connectedDevices[self.scenario][mac_addr]["rx bytes"] += int(newRxPackets * 60000)#* random.uniform(10000, 60000))
            #self.log.info("Simple Module simulationtime %s" % str(difMs))
            #self.log.info("Simple Module same aps on channel %s" % str(sameChannelAPs))
            #self.log.info("Simple Module current clients %s" % str(self.clientNumber))
            
            newTxPackets = difMs * bandwidth_packet
            self.connectedDevices[self.scenario][mac_addr]["tx packets"] += int(newTxPackets)
            if(self.txBytesRandom > 0 and self.txBytesRandom < 1):
                self.connectedDevices[self.scenario][mac_addr]["tx bytes"] += int(newTxPackets *  random.uniform(int(60000 * (1-self.txBytesRandom)), 60000))
            else:
                self.connectedDevices[self.scenario][mac_addr]["tx bytes"] += int(newTxPackets *  60000)
            
            #self.log.info("Simple Module adds %s Bytes" % str(int(newTxPackets *  60000)))
            
            self.connectedDevices[self.scenario][mac_addr]["last update"] = timestamp
        self.channel_change = False
