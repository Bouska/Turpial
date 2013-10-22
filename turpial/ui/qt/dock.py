# -*- coding: utf-8 -*-

# Qt dock for Turpial

from functools import partial

from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QCursor
from PyQt4.QtGui import QToolBar
from PyQt4.QtGui import QStatusBar
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QSizePolicy

from PyQt4.QtCore import QPoint
from PyQt4.QtCore import pyqtSignal

from turpial.ui.lang import i18n
from turpial.ui.qt.widgets import ImageButton

class Dock(QStatusBar):

    accounts_clicked = pyqtSignal()
    columns_clicked = pyqtSignal(QPoint)
    search_clicked = pyqtSignal()
    updates_clicked = pyqtSignal()
    messages_clicked = pyqtSignal()

    EMPTY = 0
    WITH_ACCOUNTS = 1
    NORMAL = 2

    def __init__(self, base):
        QStatusBar.__init__(self)
        self.base = base
        self.status = self.EMPTY

        bg_color = "#333"
        style = "background-color: %s; border: 0px solid %s;" % (bg_color, bg_color)

        self.updates_button = ImageButton(base, 'dock-updates.png',
                i18n.get('update_status'))
        self.messages_button = ImageButton(base, 'dock-messages.png',
                i18n.get('send_direct_message'))
        self.search_button = ImageButton(base, 'dock-search.png',
                i18n.get('search'))
        self.settings_button = ImageButton(base, 'dock-preferences.png',
                i18n.get('settings'))

        self.updates_button.clicked.connect(self.__updates_clicked)
        self.messages_button.clicked.connect(self.__messages_clicked)
        self.search_button.clicked.connect(self.__search_clicked)
        self.settings_button.clicked.connect(self.__settings_clicked)

        separator = QWidget()
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        toolbar = QToolBar()
        toolbar.addWidget(self.settings_button)
        toolbar.addWidget(separator)
        toolbar.addWidget(self.search_button)
        toolbar.addWidget(self.messages_button)
        toolbar.addWidget(self.updates_button)
        toolbar.setStyleSheet("QToolBar { %s }" % style)
        toolbar.setMinimumHeight(24)
        self.addPermanentWidget(toolbar, 1)
        self.setStyleSheet("QStatusBar { %s }" % style)
        self.setSizeGripEnabled(False)

    def __accounts_clicked(self):
        self.accounts_clicked.emit()

    def __columns_clicked(self):
        self.columns_clicked.emit(QCursor.pos())

    def __search_clicked(self):
        self.search_clicked.emit()

    def __updates_clicked(self):
        self.updates_clicked.emit()

    def __messages_clicked(self):
        self.messages_clicked.emit()

    def __settings_clicked(self):
        self.settings_menu = QMenu(self)

        accounts = QAction(i18n.get('add_accounts'), self)
        accounts.triggered.connect(partial(self.__accounts_clicked))

        columns = QAction(i18n.get('add_columns'), self)
        if self.status > self.EMPTY:
            columns_menu = self.base.build_columns_menu()
            columns.setMenu(columns_menu)
        else:
            columns.setEnabled(False)

        preferences = QAction(i18n.get('preferences'), self)
        about_turpial = QAction(i18n.get('about_turpial'), self)

        self.settings_menu.addAction(accounts)
        self.settings_menu.addAction(columns)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(preferences)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(about_turpial)
        self.settings_menu.exec_(QCursor.pos())

    def empty(self, with_accounts=None):
        self.updates_button.setEnabled(False)
        self.messages_button.setEnabled(False)
        if with_accounts:
            self.status = self.WITH_ACCOUNTS
        else:
            self.status = self.EMPTY


    def normal(self):
        self.updates_button.setEnabled(True)
        self.messages_button.setEnabled(True)
        self.status = self.NORMAL
