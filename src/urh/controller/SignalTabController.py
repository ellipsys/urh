from PyQt5.QtCore import pyqtSignal, Qt, QCoreApplication, pyqtSlot
from PyQt5.QtWidgets import QSplitter, QWidget, QVBoxLayout, QSizePolicy, QUndoStack

from urh import constants
from urh.controller.SignalFrameController import SignalFrameController
from urh.signalprocessing.Signal import Signal
from urh.ui.SaveAllDialog import SaveAllDialog
from urh.ui.ui_tab_interpretation import Ui_Interpretation


class SignalTabController(QWidget):
    frame_closed = pyqtSignal(SignalFrameController)
    not_show_again_changed = pyqtSignal()
    signal_frame_updated = pyqtSignal(SignalFrameController)
    signal_created = pyqtSignal(Signal)
    files_dropped = pyqtSignal(list)
    frame_was_dropped = pyqtSignal(int, int)

    @property
    def num_signals(self):
        return self.splitter.count() - 1

    @property
    def signal_frames(self):
        """

        :rtype: list of SignalFrameController
        """
        return [self.splitter.widget(i) for i in range(self.num_signals)]

    @property
    def signal_views(self):
        """

        :rtype: list of EpicGraphicView
        """
        return [sWidget.ui.gvSignal for sWidget in self.signal_frames]

    @property
    def signal_numbers(self):
        """

        :rtype: list of int
        """
        return [sw.signal.signal_frame_number for sw in self.signal_frames]

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.ui = Ui_Interpretation()
        self.ui.setupUi(self)
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setChildrenCollapsible(True)
        self.placeholder_widget = QWidget()
        # self.placeholder_widget.setMaximumHeight(1)
        self.placeholder_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.undo_stack = QUndoStack()
        self.project_manager = project_manager

        self.splitter.addWidget(self.placeholder_widget)
        self.signal_vlay = QVBoxLayout()
        self.signal_vlay.addWidget(self.splitter)
        self.ui.scrlAreaSignals.setLayout(self.signal_vlay)

        self.drag_pos = None

    @property
    def signal_undo_stack(self):
        return self.undo_stack

    def frame_dragged(self, pos):
        self.drag_pos = pos

    def frame_dropped(self, pos):
        start = self.drag_pos
        if start is None:
            return

        end = pos
        start_index = -1
        end_index = -1
        if self.num_signals > 1:
            for i, w in enumerate(self.signal_frames):
                if w.geometry().contains(start):
                    start_index = i

                if w.geometry().contains(end):
                    end_index = i

        self.swap_frames(start_index, end_index)
        self.frame_was_dropped.emit(start_index, end_index)

    @pyqtSlot(int, int)
    def swap_frames(self, from_index: int, to_index: int):
        if from_index != to_index:
            start_sig_widget = self.splitter.widget(from_index)
            self.splitter.insertWidget(to_index, start_sig_widget)

    def handle_files_dropped(self, files):
        self.files_dropped.emit(files)

    def close_frame(self, frame:SignalFrameController):
        self.frame_closed.emit(frame)

    @pyqtSlot(bool)
    def set_shift_statuslabel(self, shift_pressed):
        if shift_pressed and constants.SETTINGS.value('hold_shift_to_drag', type=bool):
            self.ui.lShiftStatus.setText("[SHIFT] Use Mouse to scroll signal.")
            self.ui.lCtrlStatus.clear()

        elif shift_pressed and not constants.SETTINGS.value('hold_shift_to_drag', type=bool):
            self.ui.lShiftStatus.setText("[SHIFT] Use mouse to create a selection.")
            self.ui.lCtrlStatus.clear()
        else:
            self.ui.lShiftStatus.clear()

    @pyqtSlot(bool)
    def set_ctrl_statuslabel(self, ctrl_pressed):
        if ctrl_pressed and len(self.ui.lShiftStatus.text()) == 0:
            self.ui.lCtrlStatus.setText("[CTRL] Zoom signal with mousclicks or arrow up/down.")
        else:
            self.ui.lCtrlStatus.clear()

    def reset_all_signalx_zoom(self):
        for gvs in self.signal_views:
            gvs.showing_full_signal = True

    def add_signal_frame(self, proto_analyzer):
        # self.set_tab_busy(True)
        sig_frame = SignalFrameController(proto_analyzer, self.undo_stack, self.project_manager, parent=self)
        sframes = self.signal_frames
        prev_signal_frame = sframes[-1] if len(sframes) > 0 else None

        if len(proto_analyzer.signal.filename) == 0:
            # Neues Signal aus "Create Signal from Selection"
            sig_frame.ui.btnSaveSignal.show()

        sig_frame.hold_shift = constants.SETTINGS.value('hold_shift_to_drag', type=bool)
        sig_frame.closed.connect(self.close_frame)
        sig_frame.signal_created.connect(self.signal_created.emit)
        sig_frame.drag_started.connect(self.frame_dragged)
        sig_frame.frame_dropped.connect(self.frame_dropped)
        sig_frame.not_show_again_changed.connect(self.not_show_again_changed.emit)
        sig_frame.ui.gvSignal.shift_state_changed.connect(self.set_shift_statuslabel)
        sig_frame.ui.gvSignal.ctrl_state_changed.connect(self.set_ctrl_statuslabel)
        sig_frame.ui.lineEditSignalName.setToolTip(self.tr("Sourcefile: ") + proto_analyzer.signal.filename)
        sig_frame.files_dropped.connect(self.handle_files_dropped)
        sig_frame.apply_to_all_clicked.connect(self.handle_apply_to_all_clicked)


        if prev_signal_frame is not None:
            sig_frame.ui.cbProtoView.setCurrentIndex(prev_signal_frame.ui.cbProtoView.currentIndex())

        sig_frame.blockSignals(True)
        sig_frame.ui.gvSignal.is_locked = True
        sig_frame.ui.gvSignal.horizontalScrollBar().blockSignals(True)

        if proto_analyzer.signal.qad_demod_file_loaded:
            sig_frame.ui.cbSignalView.setCurrentIndex(1)
            sig_frame.ui.cbSignalView.setDisabled(True)

        self.splitter.insertWidget(self.num_signals, sig_frame)

        self.reset_all_signalx_zoom()
        sig_frame.ui.gvSignal.is_locked = False
        sig_frame.ui.gvSignal.horizontalScrollBar().blockSignals(False)
        sig_frame.blockSignals(False)

        default_view = constants.SETTINGS.value('default_view', 0, int)
        sig_frame.ui.cbProtoView.setCurrentIndex(default_view)

        return sig_frame

    def add_empty_frame(self, filename: str, proto):
        sig_frame = SignalFrameController(proto_analyzer=proto, undo_stack=self.undo_stack,
                                          project_manager=self.project_manager, proto_bits=proto.decoded_proto_bits_str,
                                          parent=self)

        sig_frame.ui.lineEditSignalName.setText(filename)
        sig_frame.drag_started.connect(self.frame_dragged)
        sig_frame.frame_dropped.connect(self.frame_dropped)
        sig_frame.files_dropped.connect(self.handle_files_dropped)
        sig_frame.setMinimumHeight(sig_frame.height())
        sig_frame.closed.connect(self.close_frame)
        sig_frame.hold_shift = constants.SETTINGS.value('hold_shift_to_drag', type=bool)
        sig_frame.set_empty_frame_visibilities()


        self.splitter.insertWidget(self.num_signals, sig_frame)
        QCoreApplication.processEvents()

        return sig_frame

    def set_frame_numbers(self):
        for i, f in enumerate(self.signal_frames):
            f.ui.lSignalNr.setText("{0:d}:".format(i + 1))

    def minimize_all(self):
        for f in self.signal_frames:
            f.is_minimized = False
            f.minimize_maximize()

    def maximize_all(self):
        for f in self.signal_frames:
            f.is_minimized = True
            f.minimize_maximize()

    @pyqtSlot()
    def save_all(self):
        if self.num_signals == 0:
            return

        settings = constants.SETTINGS
        try:
            not_show = settings.value('not_show_save_dialog', type=bool)
        except TypeError:
            not_show = False

        if not not_show:
            ok, notshowagain = SaveAllDialog.dialog(self)
            settings.setValue("not_show_save_dialog", notshowagain)
            self.not_show_again_changed.emit()
            if not ok:
                return

        for f in self.signal_frames:
            if f.signal is None or f.signal.filename == "":
                continue
            f.signal.save()

    @pyqtSlot()
    def close_all(self):
        for f in self.signal_frames:
            f.my_close()

    @pyqtSlot(Signal)
    def handle_apply_to_all_clicked(self, signal: Signal):
        for frame in self.signal_frames:
            if frame.signal is not None:
                frame.signal.noise_min_plot = signal.noise_min_plot
                frame.signal.noise_max_plot = signal.noise_max_plot

                frame.signal.block_protocol_update = True
                proto_needs_update = False

                if frame.signal.modulation_type != signal.modulation_type:
                    frame.signal.modulation_type = signal.modulation_type
                    proto_needs_update = True

                if frame.signal.qad_center != signal.qad_center:
                    frame.signal.qad_center = signal.qad_center
                    proto_needs_update = True

                if frame.signal.tolerance != signal.tolerance:
                    frame.signal.tolerance = signal.tolerance
                    proto_needs_update = True

                if frame.signal.noise_treshold != signal.noise_treshold:
                    frame.signal.noise_treshold = signal.noise_treshold
                    proto_needs_update = True

                if frame.signal.bit_len != signal.bit_len:
                    frame.signal.bit_len = signal.bit_len
                    proto_needs_update = True

                frame.signal.block_protocol_update = False

                if proto_needs_update:
                    frame.signal.protocol_needs_update.emit()

    def __get_sorted_positions(self):
        frame_names = [sf.ui.lineEditSignalName.text() for sf in self.signal_frames]
        sorted_frame_names = frame_names[:]
        sorted_frame_names.sort()
        sorted_positions = []
        for name in frame_names:
            pos = sorted_frame_names.index(name)
            if pos in sorted_positions:
                pos += 1
            sorted_positions.append(pos)
        return sorted_positions

    def refresh_participant_information(self):
        for sframe in self.signal_frames:
            sframe.on_participant_changed()