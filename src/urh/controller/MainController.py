import copy
import os
import traceback

from PyQt5.QtCore import pyqtSignal, QDir, Qt, pyqtSlot, QFileInfo, QTimer
from PyQt5.QtGui import QIcon, QResizeEvent, QCloseEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QUndoGroup, QActionGroup, QHeaderView, QAction, QFileDialog, \
    QMessageBox, QApplication

from urh import constants
from urh import version
from urh.controller.CompareFrameController import CompareFrameController
from urh.controller.DecoderWidgetController import DecoderWidgetController
from urh.controller.GeneratorTabController import GeneratorTabController
from urh.controller.OptionsController import OptionsController
from urh.controller.ProjectDialogController import ProjectDialogController
from urh.controller.SendRecvDialogController import SendRecvDialogController, Mode
from urh.controller.SignalFrameController import SignalFrameController
from urh.controller.SignalTabController import SignalTabController
from urh.models.FileFilterProxyModel import FileFilterProxyModel
from urh.models.ParticipantLegendListModel import ParticipantLegendListModel
from urh.models.FileIconProvider import FileIconProvider
from urh.models.FileSystemModel import FileSystemModel
from urh.plugins.PluginManager import PluginManager
from urh.signalprocessing.ProtocolAnalyzer import ProtocolAnalyzer
from urh.signalprocessing.Signal import Signal
from urh.ui.WavFileDialog import WavFileDialog
from urh.ui.ui_main import Ui_MainWindow
from urh.util import FileOperator
from urh.util.Errors import Errors
from urh.util.Logger import logger
from urh.util.ProjectManager import ProjectManager


class MainController(QMainWindow):

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.project_save_timer = QTimer()
        self.project_manager = ProjectManager(self)
        self.plugin_manager = PluginManager()
        self.signal_tab_controller = SignalTabController(self.project_manager,
                                                                         parent=self.ui.tab_interpretation)
        self.ui.tab_interpretation.layout().addWidget(self.signal_tab_controller)
        self.compare_frame_controller = CompareFrameController(parent=self.ui.tab_protocol,
                                                               plugin_manager=self.plugin_manager,
                                                               project_manager=self.project_manager)

        self.ui.tab_protocol.layout().addWidget(self.compare_frame_controller)

        self.generator_tab_controller = GeneratorTabController(self.compare_frame_controller,
                                                               self.project_manager,
                                                               parent=self.ui.tab_generator)

        self.undo_group = QUndoGroup()
        self.undo_group.addStack(self.signal_tab_controller.signal_undo_stack)
        self.undo_group.addStack(self.compare_frame_controller.protocol_undo_stack)
        self.undo_group.addStack(self.generator_tab_controller.generator_undo_stack)
        self.undo_group.setActiveStack(self.signal_tab_controller.signal_undo_stack)
        self.ui.progressBar.hide()

        self.participant_legend_model = ParticipantLegendListModel(self.project_manager.participants)
        self.ui.listViewParticipants.setModel(self.participant_legend_model)

        gtc = self.generator_tab_controller
        gtc.ui.splitter.setSizes([gtc.width() / 0.7, gtc.width() / 0.3])

        self.ui.tab_generator.layout().addWidget(self.generator_tab_controller)

        self.signal_protocol_dict = {}
        """:type: dict[SignalFrameController,ProtocolAnalyzer]"""
        self.signal_tab_controller.ui.lLoadingFile.setText("")

        self.ui.lnEdtTreeFilter.setClearButtonEnabled(True)

        group = QActionGroup(self)
        self.ui.actionFSK.setActionGroup(group)
        self.ui.actionOOK.setActionGroup(group)
        self.ui.actionNone.setActionGroup(group)
        self.ui.actionPSK.setActionGroup(group)

        self.signal_tab_controller.ui.lCtrlStatus.clear()
        self.signal_tab_controller.ui.lShiftStatus.clear()

        self.recentFileActionList = []
        self.create_connects()
        self.updateRecentActionList()

        OptionsController.write_default_options()

        self.filemodel = FileSystemModel(self)
        path = QDir.homePath()

        self.filemodel.setIconProvider(FileIconProvider())
        self.filemodel.setRootPath(path)
        self.file_proxy_model = FileFilterProxyModel(self)
        self.file_proxy_model.setSourceModel(self.filemodel)
        self.ui.fileTree.setModel(self.file_proxy_model)

        self.ui.fileTree.setRootIndex(self.file_proxy_model.mapFromSource(self.filemodel.index(path)))
        self.ui.fileTree.setToolTip(path)
        self.ui.fileTree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.ui.fileTree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.ui.fileTree.setFocus()

        self.generator_tab_controller.table_model.cfc = self.compare_frame_controller

        self.ui.actionConvert_Folder_to_Project.setEnabled(False)

        undo_action = self.undo_group.createUndoAction(self)
        undo_action.setIcon(QIcon.fromTheme("edit-undo"))
        undo_action.setShortcut(QKeySequence.Undo)
        self.ui.menuEdit.insertAction(self.ui.actionMinimize_all, undo_action)

        redo_action = self.undo_group.createRedoAction(self)
        redo_action.setIcon(QIcon.fromTheme("edit-redo"))
        redo_action.setShortcut(QKeySequence.Redo)

        self.ui.splitter.setSizes([0, 1])

        self.ui.menuEdit.insertAction(self.ui.actionMinimize_all, redo_action)
        self.refresh_main_menu()

        self.apply_default_view()
        self.project_save_timer.start(ProjectManager.AUTOSAVE_INTERVAL_MINUTES * 60 * 1000)

        self.ui.actionProject_settings.setVisible(False)
        self.ui.actionSave_project.setVisible(False)

        # Disabled because never used
        self.ui.actionMinimize_all.setVisible(False)
        self.ui.actionMaximize_all.setVisible(False)


    def create_connects(self):
        self.ui.actionNew_Project.triggered.connect(self.on_new_project_clicked)
        self.ui.actionProject_settings.triggered.connect(self.on_project_settings_clicked)
        self.ui.actionSave_project.triggered.connect(self.project_manager.saveProject)
        self.ui.actionCommon_Zoom.setShortcut(QKeySequence(Qt.SHIFT + Qt.Key_Z))
        self.ui.actionAbout_AutomaticHacker.triggered.connect(self.show_about)
        self.ui.actionRecord.triggered.connect(self.show_record_dialog)

        self.ui.actionFullscreen_mode.setShortcut(QKeySequence.FullScreen)
        self.ui.actionFullscreen_mode.triggered.connect(self.toggle_fullscreen)

        self.signal_tab_controller.frame_closed.connect(self.close_signal_frame)
        self.signal_tab_controller.signal_created.connect(self.add_signal)
        self.compare_frame_controller.show_interpretation_clicked.connect(
            self.show_protocol_selection_in_interpretation)
        self.signal_tab_controller.ui.scrollArea.files_dropped.connect(self.handle_files_dropped)
        self.signal_tab_controller.files_dropped.connect(self.handle_files_dropped)
        self.compare_frame_controller.files_dropped.connect(self.handle_files_dropped)
        self.signal_tab_controller.frame_was_dropped.connect(self.set_frame_numbers)
        self.ui.actionMinimize_all.triggered.connect(self.minimize_all)
        self.ui.actionMaximize_all.triggered.connect(self.maximize_all)
        self.ui.actionSaveAllSignals.triggered.connect(self.signal_tab_controller.save_all)
        self.ui.actionClose_all.triggered.connect(self.close_all)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionOpen.setShortcut(QKeySequence(QKeySequence.Open))
        self.ui.actionMinimize_all.setShortcut("F10")
        self.ui.actionMaximize_all.setShortcut("F11")
        self.ui.lnEdtTreeFilter.textChanged.connect(self.handle_filtetree_filter_text_changed)
        self.ui.actionConvert_Folder_to_Project.triggered.connect(self.project_manager.convert_folder_to_project)
        self.ui.actionDecoding.triggered.connect(self.show_decoding_dialog)
        self.compare_frame_controller.show_decoding_clicked.connect(self.show_decoding_dialog)
        self.ui.tabWidget.currentChanged.connect(self.on_selected_tab_changed)
        self.ui.actionSpectrum_Analyzer.triggered.connect(self.show_spectrum_dialog)
        self.ui.actionOptions.triggered.connect(self.show_options_dialog)
        self.project_save_timer.timeout.connect(self.project_manager.saveProject)
        self.ui.actionSniff_protocol.triggered.connect(
            self.compare_frame_controller.show_proto_sniff_dialog)

        self.compare_frame_controller.ui.treeViewProtocols.files_dropped_on_group.connect(
            self.handle_files_dropped)

        self.project_manager.project_loaded_status_changed.connect(self.ui.actionProject_settings.setVisible)
        self.project_manager.project_loaded_status_changed.connect(self.ui.actionSave_project.setVisible)
        self.project_manager.project_loaded_status_changed.connect(self.ui.actionConvert_Folder_to_Project.setDisabled)
        self.project_manager.project_updated.connect(self.on_project_updated)

        self.ui.textEditProjectDescription.textChanged.connect(self.on_textEditProjectDescription_edited)
        self.ui.tabWidget_Project.tabBarDoubleClicked.connect(self.on_project_tab_bar_double_clicked)

        self.compare_frame_controller.participant_changed.connect(self.signal_tab_controller.refresh_participant_information)
        self.compare_frame_controller.ui.treeViewProtocols.close_wanted.connect(self.on_cfc_close_wanted)
        self.ui.listViewParticipants.doubleClicked.connect(self.on_project_settings_clicked)

        self.ui.menuFile.addSeparator()
        for i in range(constants.MAX_RECENT_FILE_NR):
            recentFileAction = QAction(self)
            recentFileAction.setVisible(False)
            recentFileAction.triggered.connect(self.openRecent)
            self.recentFileActionList.append(recentFileAction)
            self.ui.menuFile.addAction(self.recentFileActionList[i])

    @pyqtSlot()
    def open(self):
        fip = FileIconProvider()
        self.dialog = QFileDialog(self)
        self.dialog.setIconProvider(fip)
        self.dialog.setDirectory(FileOperator.RECENT_PATH)
        self.dialog.setWindowTitle("Open Folder")
        self.dialog.setFileMode(QFileDialog.ExistingFiles)
        self.dialog.setOptions(QFileDialog.DontUseNativeDialog | QFileDialog.DontResolveSymlinks)
        self.dialog.setViewMode(QFileDialog.Detail)
        self.dialog.setNameFilter(
            "All files (*);;Complex (*.complex);;Complex16 unsigned (*.complex16u);;Complex16 signed (*.complex16s);;Wave (*.wav);;Protocols (*.proto);;"
            "Fuzzprofiles (*.fuzz);;Tar Archives (*.tar *.tar.gz *.tar.bz2);;Zip Archives (*.zip)")

        self.dialog.currentChanged.connect(self.handle_dialog_selection_changed)


        if self.dialog.exec_():
            try:
                fileNames = self.dialog.selectedFiles()
                folders = [folder for folder in fileNames if os.path.isdir(folder)]

                if len(folders) > 0:
                    folder = folders[0]
                    for f in self.signal_tab_controller.signal_frames:
                        self.close_signal_frame(f)

                    self.project_manager.set_project_folder(folder)
                else:
                    fileNames = FileOperator.uncompress_archives(fileNames, QDir.tempPath())
                    self.add_files(fileNames)
            except Exception as e:
                Errors.generic_error(self.tr("Failed to open"), str(e), traceback.format_exc())
                self.ui.progressBar.hide()
                QApplication.restoreOverrideCursor()

    @pyqtSlot(str)
    def handle_dialog_selection_changed(self, path: str):
        if os.path.isdir(path):
            self.dialog.setFileMode(QFileDialog.Directory)
            self.dialog.setNameFilter(
                "All files (*);;Complex Files *.complex (*.complex);;Wav Files *.wav (*.wav);;Protocols *.proto (*.proto);;"
                "Fuzzprofiles *.fuzz (*.fuzz);;Tar Archives (*.tar *.tar.gz *.tar.bz2);;Zip Archives (*.zip)")
        else:
            self.dialog.setFileMode(QFileDialog.ExistingFiles)
            self.dialog.setNameFilter(
                "All files (*);;Complex Files *.complex (*.complex);;Wav Files *.wav (*.wav);;Protocols *.proto (*.proto);;"
                "Fuzzprofiles *.fuzz (*.fuzz);;Tar Archives (*.tar *.tar.gz *.tar.bz2);;Zip Archives (*.zip)")


    def add_protocol_file(self, filename):

        proto = self.compare_frame_controller.add_protocol_from_file(filename)
        if proto:
            sf = self.signal_tab_controller.add_empty_frame(filename, proto)
            self.signal_protocol_dict[sf] = proto
            self.set_frame_numbers()
            self.file_proxy_model.open_files.add(filename)


    def add_fuzz_profile(self, filename):
        self.ui.tabWidget.setCurrentIndex(2)
        self.generator_tab_controller.load_from_file(filename)



    def add_signalfile(self, filename: str, group_id=0):
        if not os.path.exists(filename):
            QMessageBox.critical(self, self.tr("File not Found"),
                                       self.tr("The file {0} could not be found. Was it moved or renamed?").format(
                                           filename))
            return

        alrdy_qad_demod = False
        if filename.endswith(".wav"):
            accept, alrdy_qad_demod = WavFileDialog.dialog(self)
            if not accept:
                return

        sig_name = os.path.splitext(os.path.basename(filename))[0]

        # Use default sample rate for signal
        # Sample rate will be overriden in case of a project later
        signal = Signal(filename, sig_name, wav_is_qad_demod=alrdy_qad_demod,
                        sample_rate=self.project_manager.sample_rate)

        if self.project_manager.project_file is None:
            self.adjustForCurrentFile(signal.filename)

        self.file_proxy_model.open_files.add(filename)
        self.add_signal(signal, group_id)

    def add_signal(self, signal, group_id=0):
        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar.show()

        pa = ProtocolAnalyzer(signal)
        sframe = self.signal_tab_controller.add_signal_frame(pa)
        self.ui.progressBar.setValue(10)
        QApplication.processEvents()

        pa = self.compare_frame_controller.add_protocol(pa, group_id)
        self.ui.progressBar.setValue(20)
        QApplication.processEvents()

        signal.blockSignals(True)
        has_entry = self.project_manager.read_project_file_for_signal(signal)
        if not has_entry:
            signal.auto_detect()
        signal.blockSignals(False)
        self.ui.progressBar.setValue(50)
        QApplication.processEvents()

        self.ui.progressBar.setValue(70)
        QApplication.processEvents()

        self.signal_protocol_dict[sframe] = pa
        self.ui.progressBar.setValue(80)
        QApplication.processEvents()

        sframe.refresh(draw_full_signal=True)  # Hier wird das Protokoll ausgelesen
        if self.project_manager.read_participants_for_signal(signal, pa.messages):
            sframe.redraw_signal()

        sframe.ui.gvSignal.autofit_view()
        self.set_frame_numbers()
        self.ui.progressBar.setValue(99)
        QApplication.processEvents()

        self.compare_frame_controller.filter_search_results()

        self.refresh_main_menu()
        self.ui.progressBar.hide()

    def on_cfc_close_wanted(self, protocols):
        frames = [sframe for sframe, protocol in self.signal_protocol_dict.items() if protocol in protocols]
        if len(frames) != len(protocols):
            logger.error("failed to close {} protocols".format(len(protocols)-len(frames)))

        for frame in frames:
            self.close_signal_frame(frame)

    def close_signal_frame(self, signal_frame: SignalFrameController):
        try:
            self.project_manager.write_signal_information_to_project_file(signal_frame.signal, signal_frame.proto_analyzer.messages)
            try:
                proto = self.signal_protocol_dict[signal_frame]
            except KeyError:
                proto = None

            if proto is not None:
                self.compare_frame_controller.remove_protocol(proto)
                # Needs to be removed in generator also, otherwise program crashes,
                # if item from tree in generator is selected and corresponding signal is closed
                self.generator_tab_controller.tree_model.remove_protocol(proto)

                proto.destroy()
                del self.signal_protocol_dict[signal_frame]

            if self.signal_tab_controller.ui.scrlAreaSignals.minimumHeight() > signal_frame.height():
                self.signal_tab_controller.ui.scrlAreaSignals.setMinimumHeight(
                    self.signal_tab_controller.ui.scrlAreaSignals.minimumHeight() - signal_frame.height())

            if signal_frame.signal is not None:
                # Non-Empty Frame (when a signal and not a protocol is opended)
                self.file_proxy_model.open_files.discard(signal_frame.signal.filename)
                signal_frame.scene_creator.deleteLater()
                signal_frame.signal.destroy()
                signal_frame.signal.deleteLater()
                signal_frame.proto_analyzer.destroy()
            signal_frame.proto_analyzer = None
            signal_frame.close()
            QApplication.processEvents()
            signal_frame.destroy()
            QApplication.processEvents()

            self.compare_frame_controller.ui.treeViewProtocols.expandAll()
            self.set_frame_numbers()
            self.refresh_main_menu()
        except Exception as e:
            Errors.generic_error(self.tr("Failed to close"), str(e), traceback.format_exc())
            self.ui.progressBar.hide()
            self.unsetCursor()


    def updateRecentActionList(self):
        recentFilePaths = constants.SETTINGS.value("recentFiles")
        recentFilePaths = [p for p in recentFilePaths if os.path.exists(p)] if recentFilePaths else []
        itEnd = len(recentFilePaths) if len(
            recentFilePaths) < constants.MAX_RECENT_FILE_NR else constants.MAX_RECENT_FILE_NR

        for i in range(itEnd):
            suffix = " (Directory)" if os.path.isdir(recentFilePaths[i]) else ""
            strippedName = QFileInfo(recentFilePaths[i]).fileName() + suffix
            self.recentFileActionList[i].setText(strippedName)
            self.recentFileActionList[i].setData(recentFilePaths[i])
            self.recentFileActionList[i].setVisible(True)

        for i in range(itEnd, constants.MAX_RECENT_FILE_NR):
            self.recentFileActionList[i].setVisible(False)

        constants.SETTINGS.setValue("recentFiles", recentFilePaths)

    @pyqtSlot(str)
    def adjustForCurrentFile(self, filePath):
        if filePath in FileOperator.archives.keys():
            filePath = copy.copy(FileOperator.archives[filePath])

        settings = constants.SETTINGS
        recentFilePaths = settings.value("recentFiles")
        if recentFilePaths is None:
            recentFilePaths = []

        recentFilePaths = [p for p in recentFilePaths if p != filePath]
        recentFilePaths.insert(0, filePath)

        while len(recentFilePaths) > constants.MAX_RECENT_FILE_NR:
            recentFilePaths.pop()

        settings.setValue("recentFiles", recentFilePaths)

        self.updateRecentActionList()

    @pyqtSlot()
    def openRecent(self):
        action = self.sender()
        try:
            if os.path.isdir(action.data()):
                self.project_manager.set_project_folder(action.data())
            elif os.path.isfile(action.data()):
                self.add_files(FileOperator.uncompress_archives([action.data()], QDir.tempPath()))
        except Exception as e:
            Errors.generic_error(self.tr("Failed to open"), str(e), traceback.format_exc())
            self.ui.progressBar.hide()
            self.unsetCursor()

    @pyqtSlot()
    def show_about(self):
        QMessageBox.about(self, self.tr("About"), self.tr("<b><h2>Universal Radio Hacker</h2></b>Version: {0}<br />GitHub: <a href='https://github.com/jopohl/urh'>https://github.com/jopohl/urh</a><br /><br />Contributors:<i><ul><li>Johannes Pohl &lt;<a href='mailto:joahnnes.pohl90@gmail.com'>johannes.pohl90@gmail.com</a>&gt;</li><li>Andreas Noack &lt;<a href='mailto:andreas.noack@fh-stralsund.de'>andreas.noack@fh-stralsund.de</a>&gt;</li></ul></i>").format(version.VERSION))

    @pyqtSlot(int, int, int, int)
    def show_protocol_selection_in_interpretation(self, startmessage, start, endmessage, end):
        cfc = self.compare_frame_controller
        msg_total = 0
        last_sig_frame = None
        for protocol in cfc.protocol_list:
            if not protocol.show:
                continue
            n = protocol.num_messages
            view_type = cfc.ui.cbProtoView.currentIndex()
            messages = [i - msg_total for i in range(msg_total, msg_total + n) if startmessage <= i <= endmessage]
            if len(messages) > 0:
                try:
                    signal_frame = next((sf for sf, pf in self.signal_protocol_dict.items() if pf == protocol))
                except StopIteration:
                    QMessageBox.critical(self, self.tr("Error"),
                                         self.tr("Could not find corresponding signal frame."))
                    return
                signal_frame.set_roi_from_protocol_analysis(min(messages), start, max(messages), end + 1, view_type)
                last_sig_frame = signal_frame
            msg_total += n
        focus_frame = last_sig_frame
        if last_sig_frame is not None:
            self.signal_tab_controller.ui.scrollArea.ensureWidgetVisible(last_sig_frame, 0, 0)

        QApplication.processEvents()
        self.ui.tabWidget.setCurrentIndex(0)
        if focus_frame is not None:
            focus_frame.ui.txtEdProto.setFocus()

    def handle_files_dropped(self, files, group_id=0):
        """
        :type files: list of QtCore.QUrl
        """
        localfiles = [fileurl.toLocalFile() for fileurl in files if fileurl.isLocalFile()]

        if len(localfiles) > 0:
            self.add_files(FileOperator.uncompress_archives(localfiles, QDir.tempPath()), group_id)

    def add_files(self, filepaths, group_id=0):
        num_files = len(filepaths)
        if num_files == 0:
            return

        for i, file in enumerate(filepaths):
            if not os.path.exists(file):
                continue

            if os.path.isdir(file):
                for f in self.signal_tab_controller.signal_frames:
                    self.close_signal_frame(f)

                FileOperator.RECENT_PATH = file
                self.project_manager.set_project_folder(file)
                return

            _, fileExtension = os.path.splitext(file)
            FileOperator.RECENT_PATH = os.path.split(file)[0]

            self.signal_tab_controller.ui.lLoadingFile.setText(
                self.tr("Loading File {0:d}/{1:d}".format(i + 1, num_files)))
            QApplication.processEvents()

            QApplication.setOverrideCursor(Qt.WaitCursor)

            if fileExtension == ".complex":
                self.add_signalfile(file, group_id)
            elif fileExtension == ".coco":
                self.add_signalfile(file, group_id)
            elif fileExtension == ".proto":
                self.add_protocol_file(file)
            elif fileExtension == ".wav":
                self.add_signalfile(file, group_id)
            elif fileExtension == ".fuzz":
                self.add_fuzz_profile(file)
            else:
                self.add_signalfile(file, group_id)

            QApplication.restoreOverrideCursor()
        self.signal_tab_controller.ui.lLoadingFile.setText("")

    def set_frame_numbers(self):
        self.signal_tab_controller.set_frame_numbers()

    @pyqtSlot()
    def minimize_all(self):
        self.signal_tab_controller.minimize_all()

    @pyqtSlot()
    def maximize_all(self):
        self.signal_tab_controller.maximize_all()

    @pyqtSlot()
    def handle_filtetree_filter_text_changed(self):
        text = self.ui.lnEdtTreeFilter.text()

        if len(text) > 0:
            self.filemodel.setNameFilters(["*"+text+"*"])
        else:
            self.filemodel.setNameFilters(["*"])



    def closeEvent(self, event: QCloseEvent):
        self.project_manager.saveProject()
        event.accept()

    @pyqtSlot()
    def show_decoding_dialog(self):
        signals = [sf.signal for sf in self.signal_tab_controller.signal_frames]
        decoding_controller = DecoderWidgetController(
            self.compare_frame_controller.decodings, signals,
            self.project_manager, parent=self)
        decoding_controller.finished.connect(self.update_decodings)
        decoding_controller.show()
        decoding_controller.decoder_update()

    @pyqtSlot()
    def update_decodings(self):
        self.compare_frame_controller.load_decodings()
        self.compare_frame_controller.fill_decoding_combobox()
        self.compare_frame_controller.refresh_existing_encodings()

        self.generator_tab_controller.refresh_existing_encodings(self.compare_frame_controller.decodings)


    @pyqtSlot()
    def on_selected_tab_changed(self):
        indx = self.ui.tabWidget.currentIndex()
        if indx == 0:
            self.undo_group.setActiveStack(self.signal_tab_controller.signal_undo_stack)
        elif indx == 1:
            self.undo_group.setActiveStack(self.compare_frame_controller.protocol_undo_stack)
            self.compare_frame_controller.ui.tblViewProtocol.resize_columns()
            self.compare_frame_controller.ui.tblViewProtocol.resize_vertical_header()
        elif indx == 2:
            self.undo_group.setActiveStack(self.generator_tab_controller.generator_undo_stack)


    def close_all(self):
        self.filemodel.setRootPath(QDir.homePath())
        self.ui.fileTree.setRootIndex(self.file_proxy_model.mapFromSource(self.filemodel.index(QDir.homePath())))
        self.project_manager.saveProject()

        self.signal_tab_controller.close_all()
        self.compare_frame_controller.reset()
        self.generator_tab_controller.close_all()

        self.project_manager.project_path = ""
        self.project_manager.project_file = None
        self.signal_tab_controller.signal_undo_stack.clear()
        self.compare_frame_controller.protocol_undo_stack.clear()
        self.generator_tab_controller.generator_undo_stack.clear()

    @pyqtSlot()
    def show_record_dialog(self):
        pm = self.project_manager
        r = SendRecvDialogController(pm.frequency, pm.sample_rate,
                                     pm.bandwidth, pm.gain,
                                     pm.device, Mode.receive,
                                     parent=self)
        if r.has_empty_device_list:
            Errors.no_device()
            r.close()
            return

        r.recording_parameters.connect(pm.set_recording_parameters)
        r.files_recorded.connect(self.load_recorded_signals)
        r.show()

    @pyqtSlot()
    def show_spectrum_dialog(self):
        pm = self.project_manager
        r = SendRecvDialogController(pm.frequency, pm.sample_rate,
                                     pm.bandwidth, pm.gain, pm.device,
                                     Mode.spectrum, parent=self)
        if r.has_empty_device_list:
            Errors.no_device()
            r.close()
            return

        r.recording_parameters.connect(pm.set_recording_parameters)
        r.show()

    @pyqtSlot(list)
    def load_recorded_signals(self, filenames):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        for filename in filenames:
            self.add_signalfile(filename)
        QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def show_options_dialog(self):

        op = OptionsController(self.plugin_manager.installed_plugins, parent=self)
        op.values_changed.connect(self.on_options_changed)
        op.exec_()

    def on_options_changed(self, changed_options: dict):
        refresh_protocol_needed = False
        for key in changed_options.keys():
            if key == "rel_symbol_length":
                st = changed_options[key]
                constants.SETTINGS.setValue('rel_symbol_length', st)
                refresh_protocol_needed = True
            elif key == "show_pause_as_time":
                refresh_protocol_needed = True

        if refresh_protocol_needed:
            for sf in self.signal_tab_controller.signal_frames:
                sf.refresh_protocol()

        self.compare_frame_controller.set_shown_protocols()

        if "default_view" in changed_options.keys():
            self.apply_default_view()

    def refresh_main_menu(self):
        enable = len(self.signal_protocol_dict) > 0
        self.ui.actionSaveAllSignals.setEnabled(enable)
        self.ui.actionClose_all.setEnabled(enable)

    @pyqtSlot()
    def on_new_project_clicked(self):
        pdc = ProjectDialogController(parent=self)
        pdc.finished.connect(self.on_project_dialog_finished)
        pdc.show()

    @pyqtSlot()
    def on_project_settings_clicked(self):
        pdc = ProjectDialogController(new_project=False, project_manager=self.project_manager, parent=self)
        pdc.finished.connect(self.on_project_dialog_finished)
        pdc.show()


    @pyqtSlot()
    def on_project_dialog_finished(self):
        if self.sender().commited:
            if self.sender().new_project:
                for f in self.signal_tab_controller.signal_frames:
                    self.close_signal_frame(f)

            self.project_manager.from_dialog(self.sender())

    def apply_default_view(self):
        view_index = constants.SETTINGS.value('default_view', type=int)
        self.compare_frame_controller.ui.cbProtoView.setCurrentIndex(view_index)
        self.generator_tab_controller.ui.cbViewType.setCurrentIndex(view_index)
        for sig_frame in self.signal_tab_controller.signal_frames:
            sig_frame.ui.cbProtoView.setCurrentIndex(view_index)

    def on_project_updated(self):
        self.participant_legend_model.participants = self.project_manager.participants
        self.participant_legend_model.update()
        self.ui.textEditProjectDescription.setText(self.project_manager.description)

    def on_textEditProjectDescription_edited(self):
        self.project_manager.description = self.ui.textEditProjectDescription.toPlainText()

    def on_project_tab_bar_double_clicked(self):
        if self.ui.tabParticipants.isVisible():
            self.collapse_project_tab_bar()
        else:
            self.uncollapse_project_tab_bar()

    def collapse_project_tab_bar(self):
        self.ui.tabParticipants.hide()
        self.ui.tabDescription.hide()
        self.ui.tabWidget_Project.setMaximumHeight(self.ui.tabWidget_Project.tabBar().height())

    def uncollapse_project_tab_bar(self):
        self.ui.tabDescription.show()
        self.ui.tabParticipants.show()
        self.ui.tabWidget_Project.setMaximumHeight(9000)

    def toggle_fullscreen(self):
        if self.ui.actionFullscreen_mode.isChecked():
            self.showFullScreen()
        else:
            self.showMaximized()