import sys
from PyQt5.QtWidgets import QMessageBox, QWidget


class Errors:

    @staticmethod
    def generic_error(title: str, msg: str, detailed_msg:str=None):
        w = QWidget()
        if detailed_msg:
            msg = "Error: <b>"+msg.replace("\n","<br>")+"</b>" +"<br><br>----------<br><br>" + detailed_msg.replace("\n", "<br>")
        QMessageBox.critical(w, title, msg)

    @staticmethod
    def no_device():
        w = QWidget()
        QMessageBox.critical(w, w.tr("No devices"),
                             w.tr("You have to choose at least one available "
                                  "device in Edit->Options->Device."))

    @staticmethod
    def empty_selection():
        w = QWidget()
        QMessageBox.critical(w, w.tr("No selection"),
                             w.tr("Your selection is empty!"))

    @staticmethod
    def write_error(msg):
        w = QWidget()
        QMessageBox.critical(w, w.tr("Write error"),
                             w.tr("There was a error writing this file! {0}".format(msg)))

    @staticmethod
    def usrp_ip_not_found():
        w = QWidget()
        QMessageBox.critical(w, w.tr("USRP not found"),
                             w.tr("USRP could not be found . Is the IP "
                                  "correct?"))

    @staticmethod
    def hackrf_not_found():
        w = QWidget()

        if sys.platform == "win32":
            msg = "Could not connect to HackRF. Try these solutions:" \
                                           "<br/><br/> 1. Ensure HackRF is plugged in." \
                                           "<br/> 2. <b>Install HackRF USB driver</b> with <a href='http://zadig.akeo.ie/'>Zadig</a>."
        else:
            msg = "Could not connect to HackRF. Try these solutions:" \
                                           "<br/><br/> 1. Ensure HackRF is plugged in." \
                                           "<br/> 2. Run the command <b>hackrf_info</b> in terminal as root." \
                                           "<br/> 3. If 2. works for you, follow the instructions "\
                                           "<a href='https://github.com/mossmann/hackrf/wiki/FAQ'>here</a>."\

        QMessageBox.critical(w, w.tr("HackRF not found"),
                             w.tr(msg))

    @staticmethod
    def gnuradio_not_installed():
        w = QWidget()
        QMessageBox.critical(w, w.tr("Gnuradio not found"),
                             w.tr("You need to install Gnuradio for this "
                                  "feature."))

    @staticmethod
    def empty_group():
        w = QWidget()
        QMessageBox.critical(w, w.tr("Empty group"),
                             w.tr("The group may not be empty."))

    @staticmethod
    def invalid_path(path: str):
        w = QWidget()
        QMessageBox.critical(w, w.tr("Invalid Path"),
                             w.tr("The path {0} is invalid.".format(path)))
