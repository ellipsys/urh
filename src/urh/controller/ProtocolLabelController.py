from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QDialog

from urh import constants
from urh.models.CustomFieldListModel import CustomFieldListModel
from urh.models.PLabelTableModel import PLabelTableModel
from urh.signalprocessing.MessageType import MessageType
from urh.signalprocessing.ProtocoLabel import ProtocolLabel
from urh.signalprocessing.Message import Message
from urh.ui.delegates.CheckBoxDelegate import CheckBoxDelegate
from urh.ui.delegates.ComboBoxDelegate import ComboBoxDelegate
from urh.ui.delegates.DeleteButtonDelegate import DeleteButtonDelegate
from urh.ui.delegates.SpinBoxDelegate import SpinBoxDelegate
from urh.ui.ui_properties_dialog import Ui_DialogLabels


class ProtocolLabelController(QDialog):
    apply_decoding_changed = pyqtSignal(ProtocolLabel, MessageType)


    def __init__(self, preselected_index, message_type: MessageType, viewtype: int, max_end: int, parent=None):
        super().__init__(parent)
        self.ui = Ui_DialogLabels()
        self.ui.setupUi(self)
        self.model = PLabelTableModel(message_type)
        self.preselected_index = preselected_index

        self.ui.tblViewProtoLabels.setItemDelegateForColumn(1, SpinBoxDelegate(1, max_end, self))
        self.ui.tblViewProtoLabels.setItemDelegateForColumn(2, SpinBoxDelegate(1, max_end, self))
        self.ui.tblViewProtoLabels.setItemDelegateForColumn(3,
                                                            ComboBoxDelegate([""] * len(constants.LABEL_COLORS),
                                                                             colors=constants.LABEL_COLORS,
                                                                             parent=self))
        self.ui.tblViewProtoLabels.setItemDelegateForColumn(4, CheckBoxDelegate(self))
        self.ui.tblViewProtoLabels.setItemDelegateForColumn(5, DeleteButtonDelegate(self))

        self.ui.tblViewProtoLabels.setModel(self.model)
        self.ui.tblViewProtoLabels.selectRow(preselected_index)

        for i in range(self.model.row_count):
            self.openEditors(i)

        self.ui.tblViewProtoLabels.resizeColumnsToContents()
        self.setWindowTitle(self.tr("Edit Protocol Labels from %s") % message_type.name)

        self.custom_field_list_model = CustomFieldListModel(message_type)
        self.ui.listViewCustomFieldTypes.setModel(self.custom_field_list_model)

        self.create_connects()
        self.ui.cbProtoView.setCurrentIndex(viewtype)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def create_connects(self):
        self.ui.btnConfirm.clicked.connect(self.confirm)
        self.ui.cbProtoView.currentIndexChanged.connect(self.set_view_index)
        self.model.apply_decoding_changed.connect(self.on_apply_decoding_changed)

        self.ui.btnAddFieldType.clicked.connect(self.on_btn_add_fieldtype_clicked)
        self.ui.btnRemoveFieldType.clicked.connect(self.on_btn_remove_fieldtype_clicked)


    @pyqtSlot()
    def confirm(self):
        self.close()

    def openEditors(self, row):
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 1))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 2))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 3))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 4))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 5))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 6))
        self.ui.tblViewProtoLabels.openPersistentEditor(self.model.index(row, 7))

    @pyqtSlot(int)
    def set_view_index(self, ind):
        self.model.proto_view = ind
        self.model.update()

    @pyqtSlot(ProtocolLabel)
    def on_apply_decoding_changed(self, lbl: ProtocolLabel):
        self.apply_decoding_changed.emit(lbl, self.model.message_type)

    def on_btn_remove_fieldtype_clicked(self):
        selected_indices = [indx.row() for indx in self.ui.listViewCustomFieldTypes.selectedIndexes()]

        if len(selected_indices) == 0 and len(self.custom_field_list_model.custom_field_types) > 0:
            selected_indices.append(len(self.custom_field_list_model.custom_field_types) - 1)

        for index in selected_indices:
            self.custom_field_list_model.remove_field_type_at(index)

    def on_btn_add_fieldtype_clicked(self):
        number = 1
        name = "Custom field #"
        while name + str(number) in self.model.message_type.custom_field_types:
            number += 1

        self.custom_field_list_model.add_field_type(name + str(number))
        self.ui.btnRemoveFieldType.setEnabled(True)
