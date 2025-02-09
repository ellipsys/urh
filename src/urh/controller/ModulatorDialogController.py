import numpy
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QResizeEvent, QKeyEvent
from PyQt5.QtWidgets import QDialog, QMessageBox

from urh.signalprocessing.Modulator import Modulator
from urh.ui.ui_modulation import Ui_DialogModulation


class ModulatorDialogController(QDialog):
    def __init__(self, modulators, parent = None):
        """
        :type modulators: list of Modulator
        """
        super().__init__(parent)

        self.ui = Ui_DialogModulation()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.lock_samples_in_view = False

        self.ui.comboBoxCustomModulations.clear()
        for modulator in modulators:
            self.ui.comboBoxCustomModulations.addItem(modulator.name)
        if len(modulators) == 1:
            self.ui.btnRemoveModulation.setDisabled(True)

        self.modulators = modulators

        self.set_ui_for_current_modulator()

        self.ui.cbShowDataBitsOnly.setText(self.tr("Show Only Data Sequence\n"))
        self.ui.cbShowDataBitsOnly.setEnabled(False)
        self.protocol = None
        """:type: ProtocolAnalyzer """
        self.search_results = []
        self.ui.cbShowDataBitsOnly.setEnabled(False)
        self.ui.btnSearchNext.setEnabled(False)
        self.ui.btnSearchPrev.setEnabled(False)

        self.ui.chkBoxLockSIV.setDisabled(True)


        self.create_connects()
        self.on_modulation_type_changed()

        self.original_bits = ""
        self.ui.btnRestoreBits.setEnabled(False)


    @property
    def current_modulator(self):
        mod = self.modulators[self.ui.comboBoxCustomModulations.currentIndex()]
        return mod

    def set_ui_for_current_modulator(self):
        index = self.ui.comboBoxModulationType.findText("*("+self.current_modulator.modulation_type_str+")", Qt.MatchWildcard)
        self.ui.comboBoxModulationType.setCurrentIndex(index)
        self.ui.doubleSpinBoxCarrierFreq.setValue(self.current_modulator.carrier_freq_hz)
        self.ui.doubleSpinBoxCarrierPhase.setValue(self.current_modulator.carrier_phase_deg)
        self.ui.spinBoxBitLength.setValue(self.current_modulator.samples_per_bit)
        self.ui.spinBoxSampleRate.setValue(self.current_modulator.sample_rate)
        self.ui.spinBoxParameter0.setValue(self.current_modulator.param_for_zero)
        self.ui.spinBoxParameter1.setValue(self.current_modulator.param_for_one)


    def create_connects(self):
        self.ui.doubleSpinBoxCarrierFreq.editingFinished.connect(self.on_carrier_freq_changed)
        self.ui.doubleSpinBoxCarrierPhase.editingFinished.connect(self.on_carrier_phase_changed)
        self.ui.spinBoxBitLength.editingFinished.connect(self.on_bit_len_changed)
        self.ui.spinBoxSampleRate.editingFinished.connect(self.on_sample_rate_changed)
        self.ui.linEdDataBits.textChanged.connect(self.on_data_bits_changed)
        self.ui.spinBoxParameter0.editingFinished.connect(self.on_modulation_parameter_zero_changed)
        self.ui.spinBoxParameter1.editingFinished.connect(self.on_modulation_parameter_one_changed)
        self.ui.comboBoxModulationType.currentIndexChanged.connect(self.on_modulation_type_changed)
        self.ui.gVOriginalSignal.zoomed.connect(self.on_orig_signal_zoomed)
        self.ui.cbShowDataBitsOnly.stateChanged.connect(self.on_show_data_bits_only_changed)
        self.ui.btnSearchNext.clicked.connect(self.on_btn_next_search_result_clicked)
        self.ui.btnSearchPrev.clicked.connect(self.on_btn_prev_search_result_clicked)
        self.ui.comboBoxCustomModulations.editTextChanged.connect(self.on_custom_modulation_name_edited)
        self.ui.comboBoxCustomModulations.currentIndexChanged.connect(self.on_custom_modulation_index_changed)
        self.ui.btnAddModulation.clicked.connect(self.add_modulator)
        self.ui.btnRemoveModulation.clicked.connect(self.on_remove_modulator_clicked)
        self.ui.gVModulated.zoomed.connect(self.on_carrier_data_modulated_zoomed)
        self.ui.gVCarrier.zoomed.connect(self.on_carrier_data_modulated_zoomed)
        self.ui.gVData.zoomed.connect(self.on_carrier_data_modulated_zoomed)
        self.ui.gVModulated.sel_area_width_changed.connect(self.on_modulated_selection_changed)
        self.ui.gVOriginalSignal.sel_area_width_changed.connect(self.on_original_selection_changed)
        self.ui.spinBoxGaussBT.editingFinished.connect(self.on_gauss_bt_edited)
        self.ui.spinBoxGaussFilterWidth.editingFinished.connect(self.on_gaus_filter_wdith_edited)

        self.ui.chkBoxLockSIV.stateChanged.connect(self.on_lock_siv_changed)
        self.ui.btnRestoreBits.clicked.connect(self.on_btn_restore_bits_clicked)
        self.ui.btnSaveAndClose.clicked.connect(self.close)
        self.ui.gVOriginalSignal.signal_loaded.connect(self.handle_signal_loaded)
        self.ui.btnAutoDetect.clicked.connect(self.on_btnautodetect_clicked)

    def draw_carrier(self):
        self.ui.gVCarrier.plot_data(self.current_modulator.carrier_data)

    def draw_data_bits(self):
        self.ui.gVData.setScene(self.current_modulator.data_scene)
        self.ui.gVData.update()

    def draw_modulated(self):
        self.current_modulator.modulate(pause = 0)
        self.ui.gVModulated.plot_data(self.current_modulator.modulated_samples.imag.astype(numpy.float32))
        if self.lock_samples_in_view:
            siv = self.ui.gVOriginalSignal.view_rect().width()
            self.adjust_samples_in_view(siv)
        else:
            self.mark_samples_in_view()

    def draw_original_signal(self, start=0, end=-1):
        scene_creator = self.ui.gVOriginalSignal.scene_creator
        if scene_creator is None:
            return

        if end == -1:
            end = scene_creator.signal.num_samples

        self.ui.gVOriginalSignal.horizontalScrollBar().blockSignals(True)
        y = scene_creator.scene.sceneRect().y()
        h = scene_creator.scene.sceneRect().height()
        self.ui.gVOriginalSignal.setSceneRect(start, y, end - start, h)
        self.ui.gVOriginalSignal.fitInView(self.ui.gVOriginalSignal.sceneRect())
        scene_creator.show_scene_section(start, end)
        self.ui.gVOriginalSignal.update()

        if self.lock_samples_in_view:
            self.adjust_samples_in_view(self.ui.gVModulated.view_rect().width())
        else:
            self.mark_samples_in_view()

    @pyqtSlot()
    def on_carrier_freq_changed(self):
        self.current_modulator.carrier_freq_hz = self.ui.doubleSpinBoxCarrierFreq.value()
        self.draw_carrier()
        self.draw_modulated()

    @pyqtSlot()
    def on_carrier_phase_changed(self):
        self.current_modulator.carrier_phase_deg = self.ui.doubleSpinBoxCarrierPhase.value()
        self.draw_carrier()
        self.draw_modulated()

    @pyqtSlot()
    def on_bit_len_changed(self):
        self.current_modulator.samples_per_bit = self.ui.spinBoxBitLength.value()
        self.draw_carrier()
        self.draw_data_bits()
        self.draw_modulated()

    @pyqtSlot()
    def on_data_bits_changed(self):
        text = self.ui.linEdDataBits.text()
        text = ''.join(c for c in text if c == "1" or c == "0")
        self.ui.linEdDataBits.blockSignals(True)
        self.ui.linEdDataBits.setText(text)
        self.ui.linEdDataBits.blockSignals(False)
        self.current_modulator.display_bits = text
        self.draw_carrier()
        self.draw_data_bits()
        self.draw_modulated()
        if len(text) > 0:
            self.ui.cbShowDataBitsOnly.setText(self.tr("Show Only Data Sequence\n") + "(" + text + ")")
        else:
            self.ui.cbShowDataBitsOnly.setText(self.tr("Show Only Data Sequence\n"))

        self.search_data_sequence()

        if text == self.original_bits:
            self.ui.btnRestoreBits.setDisabled(True)
        else:
            self.ui.btnRestoreBits.setEnabled(True)

    def __cur_selected_mod_type(self):
        s = self.ui.comboBoxModulationType.currentText()
        return s[s.rindex("(")+1:s.rindex(")")]


    @pyqtSlot()
    def on_sample_rate_changed(self):
        if int(self.ui.spinBoxSampleRate.value()) > 0:
            self.current_modulator.sample_rate = int(self.ui.spinBoxSampleRate.value())
            self.draw_carrier()
            self.draw_modulated()

    @pyqtSlot()
    def on_modulation_parameter_zero_changed(self):
        self.current_modulator.param_for_zero = self.ui.spinBoxParameter0.value()
        self.draw_modulated()

    @pyqtSlot()
    def on_modulation_parameter_one_changed(self):
        self.current_modulator.param_for_one = self.ui.spinBoxParameter1.value()
        self.draw_modulated()

    @pyqtSlot()
    def on_gauss_bt_edited(self):
        self.current_modulator.gauss_bt = self.ui.spinBoxGaussBT.value()
        self.draw_modulated()

    @pyqtSlot()
    def on_gaus_filter_wdith_edited(self):
        self.current_modulator.gauss_filter_width = self.ui.spinBoxGaussFilterWidth.value()
        self.draw_modulated()

    @pyqtSlot()
    def on_modulation_type_changed(self):
        if self.current_modulator.modulation_type_str == self.__cur_selected_mod_type():
            write_standard_parameters = False
        else:
            self.current_modulator.modulation_type_str = self.__cur_selected_mod_type()
            write_standard_parameters = True

        self.__set_gauss_ui_visibility(self.__cur_selected_mod_type() == "GFSK")

        if self.__cur_selected_mod_type() == "ASK":
            self.ui.lParameterfor0.setText(self.tr("Amplitude for 0:"))
            self.ui.lParameterfor1.setText(self.tr("Amplitude for 1:"))
            self.ui.spinBoxParameter0.auto_suffix = False
            self.ui.spinBoxParameter1.auto_suffix = False
            self.ui.spinBoxParameter0.setMaximum(100)
            self.ui.spinBoxParameter0.setMinimum(0)
            self.ui.spinBoxParameter0.setDecimals(0)
            self.ui.spinBoxParameter0.setSuffix("%")
            self.ui.spinBoxParameter1.setMaximum(100)
            self.ui.spinBoxParameter1.setMinimum(0)
            self.ui.spinBoxParameter1.setDecimals(0)
            self.ui.spinBoxParameter1.setSuffix("%")
            if write_standard_parameters:
                self.ui.spinBoxParameter0.setValue(0)
                self.ui.spinBoxParameter1.setValue(100)
            else:
                self.ui.spinBoxParameter0.setValue(self.current_modulator.param_for_zero)
                self.ui.spinBoxParameter1.setValue(self.current_modulator.param_for_one)

        elif self.__cur_selected_mod_type() in ("FSK", "GFSK"):
            self.ui.spinBoxParameter0.auto_suffix = True
            self.ui.spinBoxParameter1.auto_suffix = True
            self.ui.lParameterfor0.setText(self.tr("Frequency for 0:"))
            self.ui.lParameterfor1.setText(self.tr("Frequency for 1:"))
            self.ui.spinBoxParameter0.setMaximum(1e12)
            self.ui.spinBoxParameter0.setMinimum(-1e12)
            self.ui.spinBoxParameter0.setDecimals(4)
            self.ui.spinBoxParameter1.setMaximum(1e12)
            self.ui.spinBoxParameter1.setMinimum(-1e12)
            self.ui.spinBoxParameter1.setDecimals(4)
            if write_standard_parameters:
                self.autodetect_fsk_freqs()
            else:
                self.ui.spinBoxParameter0.setValue(self.current_modulator.param_for_zero)
                self.ui.spinBoxParameter1.setValue(self.current_modulator.param_for_one)

        elif self.__cur_selected_mod_type() == "PSK":
            self.ui.spinBoxParameter0.auto_suffix = False
            self.ui.spinBoxParameter1.auto_suffix = False
            self.ui.lParameterfor0.setText(self.tr("Phase (degree) for 0:"))
            self.ui.lParameterfor1.setText(self.tr("Phase (degree) for 1:"))
            self.ui.spinBoxParameter0.setMaximum(360)
            self.ui.spinBoxParameter0.setMinimum(-360)
            self.ui.spinBoxParameter0.setDecimals(0)
            self.ui.spinBoxParameter0.setSuffix("°")
            self.ui.spinBoxParameter1.setMaximum(360)
            self.ui.spinBoxParameter1.setMinimum(-360)
            self.ui.spinBoxParameter1.setDecimals(0)
            self.ui.spinBoxParameter1.setSuffix("°")
            if write_standard_parameters:
                self.ui.spinBoxParameter0.setValue(90)
                self.ui.spinBoxParameter1.setValue(270)
            else:
                self.ui.spinBoxParameter0.setValue(self.current_modulator.param_for_zero)
                self.ui.spinBoxParameter1.setValue(self.current_modulator.param_for_one)

        self.ui.spinBoxParameter0.editingFinished.emit()
        self.ui.spinBoxParameter1.editingFinished.emit()


    def resizeEvent(self, event: QResizeEvent):
        self.update_views()

    def update_views(self):
        self.ui.gVCarrier.update()
        self.ui.gVData.update()
        self.ui.gVModulated.update()
        self.ui.gVOriginalSignal.update()

    @pyqtSlot()
    def on_orig_signal_zoomed(self):
        start = self.ui.gVOriginalSignal.view_rect().x()
        end = start + self.ui.gVOriginalSignal.view_rect().width()

        self.ui.gVOriginalSignal.centerOn(start + (end - start) / 2, 0)
        if self.lock_samples_in_view:
            self.adjust_samples_in_view(self.ui.gVOriginalSignal.view_rect().width())

            x = self.ui.gVOriginalSignal.view_rect().x() + self.ui.gVOriginalSignal.view_rect().width() / 2
            y = 0

            self.ui.gVModulated.centerOn(x, y)
            self.ui.gVCarrier.centerOn(x, y)
            self.ui.gVData.centerOn(x, y)
        else:
            self.mark_samples_in_view()

    @pyqtSlot(float)
    def on_carrier_data_modulated_zoomed(self, factor: float):

        x = self.sender().view_rect().x() + self.sender().view_rect().width() / 2
        y = 0
        for gv in (self.ui.gVCarrier, self.ui.gVData, self.ui.gVModulated):
            if gv == self.sender():
                continue
            gv.scale(factor, 1)
            gv.centerOn(x, y)

        if self.lock_samples_in_view:
            self.adjust_samples_in_view(self.ui.gVModulated.view_rect().width())
            self.ui.gVOriginalSignal.centerOn(x, y)
        else:
            self.mark_samples_in_view()

    def mark_samples_in_view(self):
        self.ui.lSamplesInViewModulated.setText(str(int(self.ui.gVModulated.view_rect().width())))
        if self.ui.gVOriginalSignal.scene_creator is not None:
            self.ui.lSamplesInViewOrigSignal.setText(str(int(self.ui.gVOriginalSignal.view_rect().width())))
        else:
            self.ui.lSamplesInViewOrigSignal.setText("-")

        if int(self.ui.gVOriginalSignal.view_rect().width()) != int(self.ui.gVModulated.view_rect().width()):
            font = self.ui.lSamplesInViewModulated.font()
            font.setBold(False)
            self.ui.lSamplesInViewModulated.setFont(font)
            self.ui.lSamplesInViewOrigSignal.setFont(font)

            self.ui.lSamplesInViewOrigSignal.setStyleSheet("QLabel { color : red; }")
            self.ui.lSamplesInViewModulated.setStyleSheet("QLabel { color : red; }")
        else:
            font = self.ui.lSamplesInViewModulated.font()
            font.setBold(True)
            self.ui.lSamplesInViewModulated.setFont(font)
            self.ui.lSamplesInViewOrigSignal.setFont(font)

            self.ui.lSamplesInViewOrigSignal.setStyleSheet("")
            self.ui.lSamplesInViewModulated.setStyleSheet("")

    @pyqtSlot()
    def on_custom_modulation_name_edited(self):
        self.current_modulator.name = self.ui.comboBoxCustomModulations.currentText()

    @pyqtSlot()
    def on_custom_modulation_index_changed(self):
        self.set_ui_for_current_modulator()
        self.draw_carrier()
        self.draw_data_bits()
        self.draw_modulated()

    @pyqtSlot()
    def on_btn_next_search_result_clicked(self):
        cur_search_result = int(self.ui.lCurrentSearchResult.text()) - 1
        self.show_search_result(cur_search_result + 1)

    @pyqtSlot()
    def on_btn_prev_search_result_clicked(self):
        cur_search_result = int(self.ui.lCurrentSearchResult.text()) - 1
        self.show_search_result(cur_search_result - 1)

    @pyqtSlot()
    def on_show_data_bits_only_changed(self, redraw=True):
        show_data_bits_only = self.ui.cbShowDataBitsOnly.isChecked()
        if not self.ui.cbShowDataBitsOnly.isEnabled() or not show_data_bits_only:
            self.ui.btnSearchPrev.setEnabled(False)
            self.ui.btnSearchNext.setEnabled(False)
            self.ui.lCurrentSearchResult.setText("-")
            self.ui.lTotalSearchresults.setText("-")
        else:
            self.search_data_sequence()

        if not redraw:
            return

        if self.ui.cbShowDataBitsOnly.isEnabled() and not show_data_bits_only:
            self.draw_original_signal()


    def search_data_sequence(self):
        if not self.ui.cbShowDataBitsOnly.isEnabled() or not self.ui.cbShowDataBitsOnly.isChecked():
            return

        search_seq = self.ui.linEdDataBits.text()
        if len(search_seq) == 0 or self.protocol is None:
            return

        self.search_results[:] = []
        proto_bits = self.protocol.plain_bits_str
        len_seq = len(search_seq)

        for i, message in enumerate(proto_bits):
            j = message.find(search_seq)
            while j != -1:
                self.search_results.append((i, j, j + len_seq))
                j = message.find(search_seq, j + 1)

        self.ui.lTotalSearchresults.setText(str(len(self.search_results)))
        self.show_search_result(0)


    def show_search_result(self, i: int):
        if len(self.search_results) == 0:
            self.ui.lCurrentSearchResult.setText("0")
            self.ui.gVOriginalSignal.scene_creator.clear_path()
            return

        message, start_index, end_index = self.search_results[i]

        start, nsamples = self.protocol.get_samplepos_of_bitseq(message, start_index, message, end_index, False)
        self.draw_original_signal(start=start, end=start + nsamples)

        self.ui.lCurrentSearchResult.setText(str(i + 1))
        if i == len(self.search_results) - 1:
            self.ui.btnSearchNext.setEnabled(False)
        else:
            self.ui.btnSearchNext.setEnabled(True)

        if i == 0:
            self.ui.btnSearchPrev.setEnabled(False)
        else:
            self.ui.btnSearchPrev.setEnabled(True)


    def add_modulator(self):
        names = [m.name for m in self.modulators]
        name = "Modulation"
        number = 1
        while name in names:
            name = "Modulation " + str(number)
            number += 1
        self.modulators.append(Modulator(name))
        self.ui.comboBoxCustomModulations.addItem(name)
        self.ui.comboBoxCustomModulations.setCurrentIndex(len(self.modulators) - 1)
        self.ui.btnRemoveModulation.setEnabled(True)

    @pyqtSlot()
    def on_remove_modulator_clicked(self):
        index = self.ui.comboBoxCustomModulations.currentIndex()
        self.ui.comboBoxCustomModulations.removeItem(index)
        self.modulators.remove(self.modulators[index])

        if len(self.modulators) == 1:
            self.ui.btnRemoveModulation.setDisabled(True)



    def adjust_samples_in_view(self, target_siv: float):
        self.ui.gVOriginalSignal.scale(self.ui.gVOriginalSignal.view_rect().width() / target_siv, 1)
        mod_zoom_factor = self.ui.gVModulated.view_rect().width() / target_siv
        self.ui.gVModulated.scale(mod_zoom_factor, 1)
        self.ui.gVCarrier.scale(mod_zoom_factor, 1)
        self.ui.gVData.scale(mod_zoom_factor, 1)
        self.mark_samples_in_view()

    @pyqtSlot()
    def on_lock_siv_changed(self):
        self.lock_samples_in_view = self.ui.chkBoxLockSIV.isChecked()
        if self.lock_samples_in_view:
            self.adjust_samples_in_view(self.ui.gVModulated.view_rect().width())

    @pyqtSlot()
    def on_btn_restore_bits_clicked(self):
        self.ui.linEdDataBits.setText(self.original_bits)

    @pyqtSlot()
    def on_btnautodetect_clicked(self):
        proto_bits = self.protocol.plain_bits_str

        message_index = -1
        pos = -1

        # Lets find a one
        for i, message in enumerate(proto_bits):
            j = message.find("1")
            if j != -1:
                message_index = i
                pos = j
                break

        if message_index == -1 or pos == -1:
            QMessageBox.information(self, self.tr("No results"),
                                    self.tr("Unable to detect parameters from current signal"))
            return

        start, nsamples = self.protocol.get_samplepos_of_bitseq(message_index, pos, message_index, pos + 1, False)
        signal = self.ui.gVOriginalSignal.scene_creator.signal
        freq = signal.estimate_frequency(start, start + nsamples, self.current_modulator.sample_rate)
        self.ui.doubleSpinBoxCarrierFreq.setValue(freq)
        self.ui.doubleSpinBoxCarrierFreq.editingFinished.emit()
        self.autodetect_fsk_freqs()

    def autodetect_fsk_freqs(self):
        if self.__cur_selected_mod_type() not in ("FSK", "GFSK"):
            return

        try:
            zero_freq = self.protocol.estimate_frequency_for_zero(self.current_modulator.sample_rate)
            one_freq = self.protocol.estimate_frequency_for_one(self.current_modulator.sample_rate)
            zero_freq = self.__trim_number(zero_freq)
            one_freq = self.__trim_number(one_freq)
            zero_freq, one_freq = self.__ensure_multitude(zero_freq, one_freq)

            self.ui.spinBoxParameter0.setValue(zero_freq)
            self.ui.spinBoxParameter1.setValue(one_freq)

        except AttributeError:
            self.ui.spinBoxParameter0.setValue(self.current_modulator.carrier_freq_hz / 2)
            self.ui.spinBoxParameter1.setValue(self.current_modulator.carrier_freq_hz)

        self.ui.spinBoxParameter0.editingFinished.emit()
        self.ui.spinBoxParameter1.editingFinished.emit()

    def __trim_number(self, number):
        if abs(number) >= 1e9:  # giga
            return numpy.round(number / 1e9) * 1e9
        elif abs(number) >= 1e6:  # mega
            return numpy.round(number / 1e6) * 1e6
        elif abs(number) >= 1e3:  # Kilo
            return numpy.round(number / 1e3) * 1e3
        else:
            return number

    def __ensure_multitude(self, num1, num2):
        try:
            if abs(num1) > abs(num2):
                num1 = abs(int(num1 / num2)) * num2
            else:
                num2 = abs(int(num2 / num1)) * num1
            return num1, num2
        except Exception:
            return num1, num2

    def handle_signal_loaded(self, protocol):
        self.setCursor(Qt.WaitCursor)
        self.ui.cbShowDataBitsOnly.setEnabled(True)
        self.ui.chkBoxLockSIV.setEnabled(True)
        self.ui.btnAutoDetect.setEnabled(True)
        self.protocol = protocol
        self.ui.spinBoxBitLength.setValue(self.ui.gVOriginalSignal.signal.bit_len)
        self.ui.spinBoxBitLength.editingFinished.emit()
        self.unsetCursor()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            return
        else:
            super().keyPressEvent(event)

    @pyqtSlot(int)
    def on_modulated_selection_changed(self, new_width: int):
        self.ui.lModulatedSelectedSamples.setText(str(abs(new_width)))

    @pyqtSlot(int)
    def on_original_selection_changed(self, new_width: int):
        self.ui.lOriginalSignalSamplesSelected.setText(str(abs(new_width)))


    def __set_gauss_ui_visibility(self, show:bool):
        self.ui.lGaussBT.setVisible(show)
        self.ui.lGaussWidth.setVisible(show)
        self.ui.spinBoxGaussBT.setVisible(show)
        self.ui.spinBoxGaussFilterWidth.setVisible(show)

        self.ui.spinBoxGaussFilterWidth.setValue(self.current_modulator.gauss_filter_width)
        self.ui.spinBoxGaussBT.setValue(self.current_modulator.gauss_bt)