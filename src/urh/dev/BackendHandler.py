from subprocess import call, DEVNULL

from urh import constants
import os
import sys
from enum import Enum

class Backends(Enum):
    none = 0
    native = 1
    grc = 2


class BackendContainer(object):
    def __init__(self, name, avail_backends: set, supports_rx: bool, supports_tx: bool):
        self.name = name
        self.avail_backends = avail_backends
        settings = constants.SETTINGS
        self.selected_backend = Backends[settings.value(name+"_selected_backend", "none")]
        if self.selected_backend == Backends.none:
            if Backends.native in self.avail_backends:
                self.selected_backend = Backends.native
            elif Backends.grc in self.avail_backends:
                self.selected_backend = Backends.grc
        elif self.selected_backend not in self.avail_backends:
            self.selected_backend = Backends.none

        self.is_enabled = settings.value(name+"_is_enabled", True, bool)
        self.__supports_rx = supports_rx
        self.__supports_tx = supports_tx
        if len(self.avail_backends) == 0:
            self.is_enabled = False

    def __repr__(self):
        return "avail backends: " +str(self.avail_backends) + "| selected backend:" + str(self.selected_backend)

    @property
    def supports_rx(self) -> bool:
        return self.__supports_rx

    @property
    def supports_tx(self) -> bool:
        return self.__supports_tx

    @property
    def has_gnuradio_backend(self):
        return Backends.grc in self.avail_backends

    @property
    def has_native_backend(self):
        return Backends.native in self.avail_backends

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled
        self.write_settings()

    def set_selected_backend(self, sel_backend: Backends):
        self.selected_backend = sel_backend
        self.write_settings()

    def write_settings(self):
        settings = constants.SETTINGS
        settings.setValue(self.name + "_is_enabled", self.is_enabled)
        settings.setValue(self.name + "_selected_backend", self.selected_backend.name)

class BackendHandler(object):
    """
    This class controls the devices backend.
    1) List available backends for devices
    2) List available devices (atleast one backend)
    3) Manage the selection of devices backend

    """
    DEVICE_NAMES = ("HackRF", "USRP", "RTL-SDR", "FUNcube-Dongle")

    def __init__(self):
        self.python2_exe = constants.SETTINGS.value('python2_exe', self.__get_python2_interpreter())
        if os.path.isfile(self.python2_exe) and os.access(self.python2_exe, os.X_OK):
            self.gnuradio_installed = call([self.python2_exe, "-c", "import gnuradio"], stderr=DEVNULL) == 0
        else:
            self.gnuradio_installed = False


        if not hasattr(sys, 'frozen'):
            self.path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.path = os.path.join(os.path.dirname(sys.executable), "dev")

        self.device_backends = {}
        """:type: dict[str, BackendContainer] """

        self.get_backends()

    @property
    def __hackrf_native_enabled(self) -> bool:
         try:
             from urh.dev.native.lib import hackrf
             return True
         except ImportError:
             return False

    @property
    def __usrp_native_enabled(self) -> bool:
         try:
             from urh.dev.native.lib import uhd
             return True
         except ImportError:
             return False

    def __device_has_gr_scripts(self, devname: str):
        script_path = os.path.join(self.path, "gr", "scripts")
        devname = devname.lower()
        has_send_file = False
        has_recv_file = False
        for f in os.listdir(script_path):
            if f == "{0}_send.py".format(devname):
                has_send_file = True
            elif f == "{0}_recv.py".format(devname):
                has_recv_file = True

        return has_recv_file, has_send_file

    def __avail_backends_for_device(self, devname: str):
        backends = set()
        supports_rx, supports_tx = self.__device_has_gr_scripts(devname)
        if self.gnuradio_installed and (supports_rx or supports_tx):
            backends.add(Backends.grc)

        if devname.lower() == "hackrf" and self.__hackrf_native_enabled:
            backends.add(Backends.native)

        if devname.lower() == "usrp" and self.__usrp_native_enabled:
            backends.add(Backends.native)

        return backends, supports_rx, supports_tx

    def get_backends(self):
        self.device_backends.clear()
        for device_name in self.DEVICE_NAMES:
            ab, rx_suprt, tx_suprt = self.__avail_backends_for_device(device_name)
            self.device_backends[device_name.lower()] = BackendContainer(device_name.lower(), ab, rx_suprt, tx_suprt)

    def __get_python2_interpreter(self):
        paths = os.get_exec_path()

        for p in paths:
            for prog in ["python2", "python2.exe"]:
                attempt = os.path.join(p, prog)
                if os.path.isfile(attempt):
                    return attempt

        return ""

if __name__ == "__main__":
    bh = BackendHandler()
    print(bh.device_backends)