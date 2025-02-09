# -*- coding: utf-8 -*-

#
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1017, 884)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/data/icons/appicon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
        MainWindow.setDockNestingEnabled(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.lnEdtTreeFilter = QtWidgets.QLineEdit(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lnEdtTreeFilter.sizePolicy().hasHeightForWidth())
        self.lnEdtTreeFilter.setSizePolicy(sizePolicy)
        self.lnEdtTreeFilter.setAcceptDrops(False)
        self.lnEdtTreeFilter.setInputMethodHints(QtCore.Qt.ImhDialableCharactersOnly)
        self.lnEdtTreeFilter.setClearButtonEnabled(True)
        self.lnEdtTreeFilter.setObjectName("lnEdtTreeFilter")
        self.verticalLayout_3.addWidget(self.lnEdtTreeFilter)
        self.fileTree = DirectoryTreeView(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fileTree.sizePolicy().hasHeightForWidth())
        self.fileTree.setSizePolicy(sizePolicy)
        self.fileTree.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.fileTree.setAutoScroll(True)
        self.fileTree.setDragEnabled(True)
        self.fileTree.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.fileTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.fileTree.setSortingEnabled(False)
        self.fileTree.setObjectName("fileTree")
        self.fileTree.header().setCascadingSectionResizes(True)
        self.fileTree.header().setStretchLastSection(False)
        self.verticalLayout_3.addWidget(self.fileTree)
        self.tabWidget_Project = QtWidgets.QTabWidget(self.layoutWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_Project.sizePolicy().hasHeightForWidth())
        self.tabWidget_Project.setSizePolicy(sizePolicy)
        self.tabWidget_Project.setObjectName("tabWidget_Project")
        self.tabParticipants = QtWidgets.QWidget()
        self.tabParticipants.setObjectName("tabParticipants")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.tabParticipants)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listViewParticipants = QtWidgets.QListView(self.tabParticipants)
        self.listViewParticipants.setObjectName("listViewParticipants")
        self.horizontalLayout.addWidget(self.listViewParticipants)
        self.tabWidget_Project.addTab(self.tabParticipants, "")
        self.tabDescription = QtWidgets.QWidget()
        self.tabDescription.setObjectName("tabDescription")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tabDescription)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.textEditProjectDescription = QtWidgets.QTextEdit(self.tabDescription)
        self.textEditProjectDescription.setObjectName("textEditProjectDescription")
        self.horizontalLayout_2.addWidget(self.textEditProjectDescription)
        self.tabWidget_Project.addTab(self.tabDescription, "")
        self.verticalLayout_3.addWidget(self.tabWidget_Project)
        self.verticalLayout_3.setStretch(1, 3)
        self.tabWidget = QtWidgets.QTabWidget(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_interpretation = QtWidgets.QWidget()
        self.tab_interpretation.setObjectName("tab_interpretation")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab_interpretation)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget.addTab(self.tab_interpretation, "")
        self.tab_protocol = QtWidgets.QWidget()
        self.tab_protocol.setObjectName("tab_protocol")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab_protocol)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget.addTab(self.tab_protocol, "")
        self.tab_generator = QtWidgets.QWidget()
        self.tab_generator.setObjectName("tab_generator")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.tab_generator)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.tabWidget.addTab(self.tab_generator, "")
        self.verticalLayout_4.addWidget(self.splitter)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout_4.addWidget(self.progressBar)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1017, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionFSK = QtWidgets.QAction(MainWindow)
        self.actionFSK.setCheckable(True)
        self.actionFSK.setObjectName("actionFSK")
        self.actionOOK = QtWidgets.QAction(MainWindow)
        self.actionOOK.setCheckable(True)
        self.actionOOK.setChecked(True)
        self.actionOOK.setObjectName("actionOOK")
        self.actionPSK = QtWidgets.QAction(MainWindow)
        self.actionPSK.setCheckable(True)
        self.actionPSK.setObjectName("actionPSK")
        self.actionNone = QtWidgets.QAction(MainWindow)
        self.actionNone.setCheckable(True)
        self.actionNone.setObjectName("actionNone")
        self.actionAuto_Fit_Y = QtWidgets.QAction(MainWindow)
        self.actionAuto_Fit_Y.setCheckable(True)
        self.actionAuto_Fit_Y.setChecked(True)
        self.actionAuto_Fit_Y.setObjectName("actionAuto_Fit_Y")
        self.actionUndo = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("edit-undo")
        self.actionUndo.setIcon(icon)
        self.actionUndo.setObjectName("actionUndo")
        self.actionRedo = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("edit-redo")
        self.actionRedo.setIcon(icon)
        self.actionRedo.setObjectName("actionRedo")
        self.actionCommon_Zoom = QtWidgets.QAction(MainWindow)
        self.actionCommon_Zoom.setCheckable(True)
        self.actionCommon_Zoom.setChecked(False)
        self.actionCommon_Zoom.setObjectName("actionCommon_Zoom")
        self.actionShow_Confirm_Close_Dialog = QtWidgets.QAction(MainWindow)
        self.actionShow_Confirm_Close_Dialog.setCheckable(True)
        self.actionShow_Confirm_Close_Dialog.setChecked(False)
        self.actionShow_Confirm_Close_Dialog.setObjectName("actionShow_Confirm_Close_Dialog")
        self.actionTest = QtWidgets.QAction(MainWindow)
        self.actionTest.setObjectName("actionTest")
        self.actionHold_Shift_to_Drag = QtWidgets.QAction(MainWindow)
        self.actionHold_Shift_to_Drag.setCheckable(True)
        self.actionHold_Shift_to_Drag.setChecked(False)
        self.actionHold_Shift_to_Drag.setObjectName("actionHold_Shift_to_Drag")
        self.actionDocumentation = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("help-contents")
        self.actionDocumentation.setIcon(icon)
        self.actionDocumentation.setIconVisibleInMenu(True)
        self.actionDocumentation.setObjectName("actionDocumentation")
        self.actionAbout_AutomaticHacker = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("help-about")
        self.actionAbout_AutomaticHacker.setIcon(icon)
        self.actionAbout_AutomaticHacker.setIconVisibleInMenu(True)
        self.actionAbout_AutomaticHacker.setObjectName("actionAbout_AutomaticHacker")
        self.actionOpenSignal = QtWidgets.QAction(MainWindow)
        self.actionOpenSignal.setObjectName("actionOpenSignal")
        self.actionOpenProtocol = QtWidgets.QAction(MainWindow)
        self.actionOpenProtocol.setObjectName("actionOpenProtocol")
        self.actionShow_Compare_Frame = QtWidgets.QAction(MainWindow)
        self.actionShow_Compare_Frame.setCheckable(True)
        self.actionShow_Compare_Frame.setChecked(True)
        self.actionShow_Compare_Frame.setObjectName("actionShow_Compare_Frame")
        self.actionClose_all = QtWidgets.QAction(MainWindow)
        self.actionClose_all.setIconVisibleInMenu(True)
        self.actionClose_all.setObjectName("actionClose_all")
        self.actionMinimize_all = QtWidgets.QAction(MainWindow)
        self.actionMinimize_all.setIconVisibleInMenu(True)
        self.actionMinimize_all.setObjectName("actionMinimize_all")
        self.actionMaximize_all = QtWidgets.QAction(MainWindow)
        self.actionMaximize_all.setIconVisibleInMenu(True)
        self.actionMaximize_all.setObjectName("actionMaximize_all")
        self.actionSaveAllSignals = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("document-save")
        self.actionSaveAllSignals.setIcon(icon)
        self.actionSaveAllSignals.setIconVisibleInMenu(True)
        self.actionSaveAllSignals.setObjectName("actionSaveAllSignals")
        self.actionSeperate_Protocols_in_Compare_Frame = QtWidgets.QAction(MainWindow)
        self.actionSeperate_Protocols_in_Compare_Frame.setCheckable(True)
        self.actionSeperate_Protocols_in_Compare_Frame.setChecked(True)
        self.actionSeperate_Protocols_in_Compare_Frame.setObjectName("actionSeperate_Protocols_in_Compare_Frame")
        self.actionOpenArchive = QtWidgets.QAction(MainWindow)
        self.actionOpenArchive.setObjectName("actionOpenArchive")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("document-open")
        self.actionOpen.setIcon(icon)
        self.actionOpen.setIconVisibleInMenu(True)
        self.actionOpen.setObjectName("actionOpen")
        self.actionOpen_Folder = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("folder-open")
        self.actionOpen_Folder.setIcon(icon)
        self.actionOpen_Folder.setObjectName("actionOpen_Folder")
        self.actionShow_only_Compare_Frame = QtWidgets.QAction(MainWindow)
        self.actionShow_only_Compare_Frame.setCheckable(True)
        self.actionShow_only_Compare_Frame.setChecked(True)
        self.actionShow_only_Compare_Frame.setObjectName("actionShow_only_Compare_Frame")
        self.actionConfigurePlugins = QtWidgets.QAction(MainWindow)
        self.actionConfigurePlugins.setIconVisibleInMenu(True)
        self.actionConfigurePlugins.setObjectName("actionConfigurePlugins")
        self.actionSort_Frames_by_Name = QtWidgets.QAction(MainWindow)
        self.actionSort_Frames_by_Name.setObjectName("actionSort_Frames_by_Name")
        self.actionConvert_Folder_to_Project = QtWidgets.QAction(MainWindow)
        self.actionConvert_Folder_to_Project.setIconVisibleInMenu(True)
        self.actionConvert_Folder_to_Project.setObjectName("actionConvert_Folder_to_Project")
        self.actionDecoding = QtWidgets.QAction(MainWindow)
        self.actionDecoding.setObjectName("actionDecoding")
        self.actionRecord = QtWidgets.QAction(MainWindow)
        self.actionRecord.setIconVisibleInMenu(True)
        self.actionRecord.setObjectName("actionRecord")
        self.actionSpectrum_Analyzer = QtWidgets.QAction(MainWindow)
        self.actionSpectrum_Analyzer.setIconVisibleInMenu(True)
        self.actionSpectrum_Analyzer.setObjectName("actionSpectrum_Analyzer")
        self.actionOptions = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("configure")
        self.actionOptions.setIcon(icon)
        self.actionOptions.setIconVisibleInMenu(True)
        self.actionOptions.setObjectName("actionOptions")
        self.actionShow_file_tree = QtWidgets.QAction(MainWindow)
        self.actionShow_file_tree.setCheckable(True)
        self.actionShow_file_tree.setObjectName("actionShow_file_tree")
        self.actionNew_Project = QtWidgets.QAction(MainWindow)
        self.actionNew_Project.setObjectName("actionNew_Project")
        self.actionSniff_protocol = QtWidgets.QAction(MainWindow)
        self.actionSniff_protocol.setObjectName("actionSniff_protocol")
        self.actionProject_settings = QtWidgets.QAction(MainWindow)
        self.actionProject_settings.setObjectName("actionProject_settings")
        self.actionSave_project = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("document-save")
        self.actionSave_project.setIcon(icon)
        self.actionSave_project.setObjectName("actionSave_project")
        self.actionFullscreen_mode = QtWidgets.QAction(MainWindow)
        self.actionFullscreen_mode.setCheckable(True)
        self.actionFullscreen_mode.setObjectName("actionFullscreen_mode")
        self.menuFile.addAction(self.actionNew_Project)
        self.menuFile.addAction(self.actionProject_settings)
        self.menuFile.addAction(self.actionSave_project)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionRecord)
        self.menuFile.addAction(self.actionSniff_protocol)
        self.menuFile.addAction(self.actionSpectrum_Analyzer)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSaveAllSignals)
        self.menuFile.addAction(self.actionClose_all)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionConvert_Folder_to_Project)
        self.menuEdit.addAction(self.actionMinimize_all)
        self.menuEdit.addAction(self.actionMaximize_all)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionDecoding)
        self.menuEdit.addAction(self.actionOptions)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionFullscreen_mode)
        self.menuHelp.addAction(self.actionAbout_AutomaticHacker)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget_Project.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Universal Radio Hacker"))
        self.lnEdtTreeFilter.setPlaceholderText(_translate("MainWindow", "Filter"))
        self.tabWidget_Project.setTabText(self.tabWidget_Project.indexOf(self.tabParticipants), _translate("MainWindow", "Participants"))
        self.tabWidget_Project.setTabText(self.tabWidget_Project.indexOf(self.tabDescription), _translate("MainWindow", "Description"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_interpretation), _translate("MainWindow", "Interpretation"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_protocol), _translate("MainWindow", "Analysis"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_generator), _translate("MainWindow", "Generator"))
        self.menuFile.setTitle(_translate("MainWindow", "Fi&le"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edi&t"))
        self.menuHelp.setTitle(_translate("MainWindow", "Hel&p"))
        self.actionFSK.setText(_translate("MainWindow", "Undo"))
        self.actionOOK.setText(_translate("MainWindow", "Redo"))
        self.actionPSK.setText(_translate("MainWindow", "PSK"))
        self.actionNone.setText(_translate("MainWindow", "None (bei .bin)"))
        self.actionAuto_Fit_Y.setText(_translate("MainWindow", "&Auto Fit Y"))
        self.actionUndo.setText(_translate("MainWindow", "&Undo"))
        self.actionRedo.setText(_translate("MainWindow", "&Redo"))
        self.actionCommon_Zoom.setText(_translate("MainWindow", "&Common Zoom"))
        self.actionShow_Confirm_Close_Dialog.setText(_translate("MainWindow", "&Show Confirm Close Dialog"))
        self.actionTest.setText(_translate("MainWindow", "test"))
        self.actionHold_Shift_to_Drag.setText(_translate("MainWindow", "&Hold Shift to Drag"))
        self.actionDocumentation.setText(_translate("MainWindow", "&Documentation"))
        self.actionAbout_AutomaticHacker.setText(_translate("MainWindow", "&About Universal Radio Hacker..."))
        self.actionOpenSignal.setText(_translate("MainWindow", "&Signal"))
        self.actionOpenProtocol.setText(_translate("MainWindow", "&Protocol"))
        self.actionShow_Compare_Frame.setText(_translate("MainWindow", "Show &Compare Frame"))
        self.actionClose_all.setText(_translate("MainWindow", "&Close all"))
        self.actionMinimize_all.setText(_translate("MainWindow", "&Minimize all"))
        self.actionMaximize_all.setText(_translate("MainWindow", "Maximize &all"))
        self.actionSaveAllSignals.setText(_translate("MainWindow", "&Save all signals"))
        self.actionSeperate_Protocols_in_Compare_Frame.setText(_translate("MainWindow", "Seperate &Protocols in Compare Frame"))
        self.actionOpenArchive.setText(_translate("MainWindow", "&Archive"))
        self.actionOpen.setText(_translate("MainWindow", "&Open..."))
        self.actionOpen_Folder.setText(_translate("MainWindow", "Open &Folder.."))
        self.actionShow_only_Compare_Frame.setText(_translate("MainWindow", "Show Compare Frame only"))
        self.actionConfigurePlugins.setText(_translate("MainWindow", "Configure..."))
        self.actionSort_Frames_by_Name.setText(_translate("MainWindow", "Sort &Frames by Name"))
        self.actionConvert_Folder_to_Project.setText(_translate("MainWindow", "Convert &Folder to Project"))
        self.actionDecoding.setText(_translate("MainWindow", "&Decoding..."))
        self.actionRecord.setText(_translate("MainWindow", "&Record signal..."))
        self.actionSpectrum_Analyzer.setText(_translate("MainWindow", "Spectrum &Analyzer..."))
        self.actionOptions.setText(_translate("MainWindow", "&Options..."))
        self.actionShow_file_tree.setText(_translate("MainWindow", "Sh&ow file tree"))
        self.actionNew_Project.setText(_translate("MainWindow", "&New Project.."))
        self.actionSniff_protocol.setText(_translate("MainWindow", "Sn&iff protocol..."))
        self.actionProject_settings.setText(_translate("MainWindow", "&Project settings..."))
        self.actionSave_project.setText(_translate("MainWindow", "Sa&ve project"))
        self.actionFullscreen_mode.setText(_translate("MainWindow", "Fullscreen mode"))

from urh.ui.views.DirectoryTreeView import DirectoryTreeView
from . import urh_rc
