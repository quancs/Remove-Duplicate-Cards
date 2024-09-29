# import the main window object (mw)from aqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *
# from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QFontComboBox, QLineEdit, QMessageBox, QVBoxLayout, QLabel, QFormLayout, QTextEdit
# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
from collections import defaultdict
from .checkable_combobox import CheckableComboBox

class DuplicateConfigWindow(QWidget):
    selectedDecks = None
    selectedMethod = "keep old cards, remove new cards"
    selectedKey = ""
    deck_list = []
    method_list = ['keep old cards, remove new cards', 'keep new cards, remove old cards']
    key_list = None
    COMBINE = "Combine All Keys"

    def __init__(self, deckNameList):
        super(DuplicateConfigWindow, self).__init__()
        self.selectedDecks = []
        self.deck_list = deckNameList
        self.key_list = set()
        self.combobox_1 = CheckableComboBox(self)
        self.combobox_2 = QComboBox(self)
        self.combobox_3 = QComboBox(self)
        self.executePlanBtn = QPushButton(self)
        self.makePlanBtn = QPushButton(self)
        self.console = QTextEdit(self)
        self.executePlanBtn.setText("2: Execute plan")
        self.makePlanBtn.setText("1: Make a plan")
        self.v_layout = QFormLayout(self)
        self.layout_init()
        self.combobox_init()

        if not deckNameList:
            showInfo("there is no deck in your collection")

    def layout_init(self):
        self.v_layout.addRow("Select decks:", self.combobox_1)
        self.v_layout.addRow("Select one method:", self.combobox_2)
        self.v_layout.addRow("Select the main key:", self.combobox_3)
        self.v_layout.addRow(self.makePlanBtn)
        self.v_layout.addRow(self.executePlanBtn)
        self.v_layout.addRow(self.console)
        self.setLayout(self.v_layout)
        self.executePlanBtn.clicked.connect(lambda: self.plan(True))
        self.makePlanBtn.clicked.connect(lambda: self.plan(False))

    def combobox_init(self):
        self.combobox_1.addItems(self.deck_list)
        self.combobox_1.changed.connect(self.on_deck_selected)
        self.combobox_2.addItems(self.method_list)
        self.combobox_2.currentIndexChanged.connect(lambda: self.on_method_selected(self.combobox_2))
        self.combobox_3.currentIndexChanged.connect(lambda: self.on_key_selected())

    def on_deck_selected(self, name):
        if name in self.selectedDecks:
            self.selectedDecks.remove(name)
        else:
            self.selectedDecks.append(name)
        self.update_key_set(name)

    def on_method_selected(self, combobox):
        self.selectedMethod = combobox.currentText()

    def on_key_selected(self):
        self.selectedKey = self.combobox_3.currentText()

    def plan(self, execute):
        has_valid_deck = any([mw.col.decks.byName(d) for d in self.selectedDecks])
        if has_valid_deck:
            if self.selectedMethod == self.method_list[0]:
                self.do_plan(None, True, execute)
            else:
                self.do_plan(None, False, execute)
        else:
            showInfo(f'No valid deck ')

    def do_plan(self, deck, keep_old, execute):
        # 如果queue队列是新队列，则随机删除一个
        self.console.clear()
        self.console.append('find duplicates in deck: {}'.format(', '.join(self.selectedDecks)))

        q = ' OR '.join([f'"deck: {d}"' for d in self.selectedDecks])
        notes = mw.col.findNotes(q)
        if len(notes):
            md = defaultdict(list)
            for noteId1 in notes:
                note1 = mw.col.getNote(noteId1)
                if self.selectedKey == self.COMBINE:
                    md[tuple(note1.values())].append((noteId1, note1.cards()[0].due))
                if self.selectedKey in note1.keys():
                    index1 = note1.keys().index(self.selectedKey)
                    if index1 >= 0:
                        val1 = note1.values()[index1]
                        md[val1].append((noteId1, note1.cards()[0].due))
                else:
                    pass
            total = 0
            for k, v in md.items():
                if len(v) > 1:
                    if type(k) is tuple:
                        k = "(combined keys)"
                    (noteId, min_due) = v[0]
                    for (noteId1, due1) in v:
                        if (keep_old and due1 < min_due) or (keep_old == False and due1 > min_due):
                            noteId = noteId1
                            min_due = due1
                    for (noteId1, due1) in v:
                        if execute and noteId1 != noteId:
                            mw.col.remNotes([noteId1])
                            total = total + 1
                            self.console.append(k + ": note_id:" + str(noteId1) + " due:" + str(due1) + " X done")
                        elif execute == False and noteId1 == noteId:
                            self.console.append(k + ": note_id:" + str(noteId1) + " due:" + str(due1))
                        elif execute == False:
                            total = total + 1
                            self.console.append(k + ": note_id:" + str(noteId1) + " due:" + str(due1) + " X")
            if execute:
                self.console.append("totally, %d notes were removed" % total)
            else:
                self.console.append("totally, %d notes will be removed" % total)
        else:
            showInfo(f'decks have no card')

    def update_key_set(self, deck):
        if not self.selectedDecks:
            return

        notes = mw.col.findNotes(f'"deck:{deck}"')

        if len(notes):
            m = getattr(mw.col, "field_names_for_note_ids", None)
            if callable(m):
                nks = m(notes)
                for key in nks:
                    self.key_list.add(key)
            else:
                for note_id in notes:
                    note = mw.col.getNote(note_id)
                    nks = note.keys()
                    for key in nks:
                        self.key_list.add(key)

            self.combobox_3.clear()
            self.combobox_3.addItem(self.COMBINE)
            for key in self.key_list:
                self.combobox_3.addItem(key)
            self.selectedKey = self.COMBINE
        else:
            showInfo(f'deck "{self.selectedDeck}" has no card')


def showWindow():
    deckNames = mw.col.decks.allNames()
    mw.duplicateConfigWindow = DuplicateConfigWindow(deckNames)
    mw.duplicateConfigWindow.show()


# create a new menu item, "test"
action = QAction("Remove Duplicate Cards", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(showWindow)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
