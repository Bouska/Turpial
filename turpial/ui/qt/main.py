# -*- coding: utf-8 -*-

# Qt main view for Turpial

import os
import sys
import urllib2

from functools import partial

from PyQt4 import QtCore
from PyQt4.QtGui import QMenu
from PyQt4.QtGui import QImage
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QFontDatabase
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QApplication

from PyQt4.QtCore import pyqtSignal

from turpial import DESC
from turpial.ui.base import *

from turpial.ui.qt.dock import Dock
from turpial.ui.qt.tray import TrayIcon
from turpial.ui.qt.update import UpdateBox
from turpial.ui.qt.worker import CoreWorker
from turpial.ui.qt.search import SearchDialog
from turpial.ui.qt.container import Container
from turpial.ui.qt.profile import ProfileDialog
from turpial.ui.qt.accounts import AccountsDialog
from turpial.ui.qt.selectfriend import SelectFriendDialog

from libturpial.common import ColumnType, is_preview_service_supported

class Main(Base, QWidget):

    account_deleted = pyqtSignal()
    account_registered = pyqtSignal()

    def __init__(self):
        self.app = QApplication(sys.argv)

        Base.__init__(self)
        QWidget.__init__(self)

        QFontDatabase.addApplicationFont(os.path.join(self.fonts_path, 'Ubuntu-L.ttf'))
        QFontDatabase.addApplicationFont(os.path.join(self.fonts_path, 'TitilliumWeb-Bold.ttf'))
        QFontDatabase.addApplicationFont(os.path.join(self.fonts_path, 'TitilliumWeb-Regular.ttf'))

        database = QFontDatabase()
        for f in database.families():
            print f

        self.templates_path = os.path.realpath(os.path.join(
            os.path.dirname(__file__), 'templates'))

        self.setWindowTitle('Turpial')
        self.ignore_quit = True
        self.resize(320, 480)
        self.showed = True

        self.update_box = UpdateBox(self)

        self.tray = TrayIcon(self)
        self.tray.activated.connect(self.__on_tray_click)

        self.core = CoreWorker()
        self.core.status_updated.connect(self.after_update_status)
        self.core.status_repeated.connect(self.after_repeat_status)
        self.core.status_deleted.connect(self.after_delete_status)
        self.core.column_updated.connect(self.after_update_column)
        self.core.account_saved.connect(self.after_save_account)
        self.core.account_deleted.connect(self.after_delete_account)
        self.core.column_saved.connect(self.after_save_column)
        self.core.column_deleted.connect(self.after_delete_column)
        self.core.urls_shorted.connect(self.update_box.after_short_url)
        self.core.media_uploaded.connect(self.update_box.after_upload_media)

        self.core.start()

        self._container = Container(self)

        self.dock = Dock(self)
        self.dock.empty()

        self.dock.accounts_clicked.connect(self.show_accounts_dialog)
        self.dock.columns_clicked.connect(self.show_column_menu)
        self.dock.search_clicked.connect(self.show_search_dialog)
        self.dock.updates_clicked.connect(self.show_update_box)

        #self.profile = ProfileDialog(self)
        #self.profile.show()
        #friend = SelectFriendDialog(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._container, 1)
        layout.addWidget(self.dock)
        layout.setMargin(0)

        self.setLayout(layout)

    def __open_in_browser(self, url):
        browser = self.core.get_default_browser()

        if browser != '':
            cmd = browser.split(' ')
            cmd.append(url)
            subprocess.Popen(cmd)
        else:
            webbrowser.open(url)


    #================================================================
    # Tray icon
    #================================================================

    def __on_tray_click(self):
        if self.showed:
            self.showed = False
            self.hide()
        else:
            self.showed = True
            self.show()

    #================================================================
    # Overrided methods
    #================================================================

    def start(self):
        #if self.core.play_sounds_in_login():
        #    self.sound.login()
        print 'start'

    def main_loop(self):
        try:
            self.app.exec_()
        except Exception:
            sys.exit(0)

    def main_quit(self, widget=None, force=False):
        self.app.quit()
        sys.exit(0)

    def show_main(self):
        self.start()
        self.show()
        self.update_container()

    #================================================================
    # Main methods
    #================================================================

    def add_column(self, column_id):
        self.core.save_column(column_id)

    def delete_account(self, account_id):
        self.core.delete_account(account_id)

    def add_search_column(self, account_id, criteria):
        column_id = "%s-%s:%s" % (account_id, ColumnType.SEARCH, urllib2.quote(criteria))
        self.add_column(column_id)

    def open_url(self, url):
        if is_preview_service_supported(url):
            pass
            #try:
            #    bla
            #except:
            #    self.__open_in_browser(url)
        else:
            self.__open_in_browser(url)

    def load_image(self, filename, pixbuf=False):
        img_path = os.path.join(self.images_path, filename)
        if pixbuf:
            return QPixmap(img_path)
        return QImage(img_path)

    def get_image_path(self, filename):
        return os.path.join(self.images_path, filename)

    def update_container(self):
        accounts = self.core.get_registered_accounts()
        columns = self.core.get_registered_columns()

        if len(columns) == 0:
            if len(accounts) == 0:
                self._container.empty(False)
                self.dock.empty(False)
            else:
                self._container.empty(True)
                self.dock.normal()
            self.tray.empty()
        else:
            self._container.normal()
            self.dock.normal()
            self.tray.normal()
            self.download_stream(columns[0])

    def show_accounts_dialog(self):
        accounts = AccountsDialog(self)

    def show_column_menu(self, point):
        self.columns_menu = QMenu(self)

        available_columns = self.core.get_available_columns()
        accounts = self.core.get_all_accounts()

        if len(accounts) == 0:
            empty_menu = QAction(i18n.get('no_registered_accounts'), self)
            empty_menu.setEnabled(False)
            self.columns_menu.addAction(empty_menu)
        else:
            for account in accounts:
                name = "%s (%s)" % (account.username, i18n.get(account.protocol_id))
                account_menu = QAction(name, self)

                if len(available_columns[account.id_]) > 0:
                    available_columns_menu = QMenu(self)
                    for column in available_columns[account.id_]:
                        # FIXME: Handle lists
                        if column.__class__.__name__ == 'List':
                            continue
                        item = QAction(column.slug, self)
                        item.triggered.connect(partial(self.add_column, column.id_))
                        available_columns_menu.addAction(item)

                    account_menu.setMenu(available_columns_menu)
                else:
                    account_menu.setEnabled(False)
                self.columns_menu.addAction(account_menu)

        self.columns_menu.exec_(point)

    def show_search_dialog(self):
        search = SearchDialog(self)
        if search.result() == QDialog.Accepted:
            account_id = str(search.get_account().toPyObject())
            criteria = str(search.get_criteria())
            self.add_search_column(account_id, criteria)

    def show_update_box(self):
        self.update_box.show()

    def show_update_box_for_reply(self, account_id, status):
        self.update_box.show_for_reply(account_id, status)

    def show_update_box_for_quote(self, account_id, status):
        self.update_box.show_for_quote(account_id, status)

    def update_status(self, account_id, message, in_reply_to_id=None):
        self.core.update_status(account_id, message, in_reply_to_id)

    def repeat_status(self, account_id, status):
        self.core.repeat_status(account_id, status.id_)

    def delete_status(self, account_id, status):
        self.core.delete_status(account_id, status.id_)

    def short_urls(self, message):
        self.core.short_urls(message)

    def upload_media(self, account_id, filename):
        self.core.upload_media(account_id, filename)

    #================================================================
    # Hooks definitions
    #================================================================

    def after_save_account(self, account_id):
        self.account_registered.emit()

    def after_delete_account(self):
        self.account_deleted.emit()

    def after_delete_column(self, column_id):
        column_id = str(column_id)
        self._container.remove_column(column_id)
        self.update_container()
        # TODO: Enable timers
        #self.__remove_timer(column_id)

    def after_save_column(self, column_id):
        column_id = str(column_id)
        self._container.add_column(column_id)
        self.update_container()
        # TODO: Enable timers
        #self.download_stream(column)
        #self.__add_timer(column)

    def after_update_column(self, arg, data):
        column, max_ = data

        # Notifications
        # FIXME
        count = len(arg)

        if count > 0:
            self._container.update_column(column.id_, arg)

    def after_update_status(self, response, account_id):
        self.update_box.done()

    def after_repeat_status(self, response, account_id):
        print 'repeated', response, account_id

    def after_delete_status(self, response, account_id):
        print 'deleted', response, account_id

    # ------------------------------------------------------------
    # Timer Methods
    # ------------------------------------------------------------

    def download_stream(self, column):
        if self._container.is_updating(column.id_):
            return True

        last_id = self._container.start_updating(column.id_)
        self.core.get_column_statuses(column, last_id)
        return True
