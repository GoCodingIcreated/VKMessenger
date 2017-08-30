from PyQt5 import QtWidgets, QtCore, Qt
from PyQt5 import uic
from PyQt5.QtWidgets import qApp
from PyQt5.QtGui import QPixmap
import requests


import myvk
import sys


class MainWindow(QtWidgets.QMainWindow):
    defaultUiFile = "ui/mainWindow.ui"

    def __init__(self, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)

        slots = {"Exit": self.slotExit, "Log in" : self.slotLogIn, "Log out" : self.slotLogOut,
                    "Refresh" : self.slotRefresh, "Settings" : self.slotSettings}
        for action in self.menuMenu.actions():
            if action.text() != '':
                action.triggered[(bool)].connect(slots[action.text()])

        self.listWidget.itemClicked.connect(self.slotDialogSelected)
        #[(QtWidgets.QListWidgetItem)]

        self.VK = myvk.VK()
        self.me = None
        self.dialogs = None

    @QtCore.pyqtSlot(bool)
    def slotExit(self, flag):
        print("Slot Exit " + str(flag))
        qApp.exit(0)

    @QtCore.pyqtSlot(bool)
    def slotLogIn(self, flag):
        print("Slot Log in " + str(flag))
        if self.VK.vk_session is None:
            self.loginDialog = LoginWindow(self.slotLoginWindowOK, self.slotLoginWindowCancel)
        else:
            self.VK.doLogIn()
        self.me = Myself(self.VK.getMe())

    @QtCore.pyqtSlot(bool)
    def slotLogOut(self, flag):
        print("Slot Log out " + str(flag))
        self.VK.doLogOut()

    @QtCore.pyqtSlot(bool)
    def slotRefresh(self, flag):
        print("Slot Refresh " + str(flag))
        self.dialogs = self.VK.getDialogs(0, 10)
        self.listWidget.clear()
        if self.dialogs is None:
            return
        for dialog in self.dialogs["items"]:

            user_id = str(dialog["message"]["user_id"])
            user = self.VK.getUserById(user_id)
            dialogShort = self.setUpDialogWidget(dialog, user)

            item = QtWidgets.QListWidgetItem("", self.listWidget)
            item.setSizeHint(dialogShort.sizeHint())
            self.listWidget.setItemWidget(item, dialogShort)

    def setUpDialogWidget(self, dialog, user):
        user_name = user["first_name"] + " " + user["last_name"]
        pixmap = QPixmap()
        if user == myvk.dummyUser.getJson():
            pass
        else:
            iconUrl = user["photo_100"]
            req = requests.get(iconUrl, timeout=(5, 6))
            pixmap.loadFromData(req.content)

        body = dialog["message"]["body"]
        title = dialog["message"]["title"]
        if "random_id" in dialog["message"]:
            dialogShort = DialogToWidget(dialog, body, user_name, title, pixmap, self.me.photo_100)
        else:
            dialogShort = DialogFromWidget(dialog, body, user_name, title, pixmap)

        return dialogShort

    @QtCore.pyqtSlot(bool)
    def slotSettings(self, bool):
        print("Slot Settings ")

        self.loginDialog = LoginWindow(self.slotSettingsWindowOk, self.slotSettingsWindowCancel)

    @QtCore.pyqtSlot()
    def slotLoginWindowOK(self):
        print("Slot Login Window OK ")
        self.VK.setUp(self.loginDialog.loginLE.text(), self.loginDialog.passwordLE.text())
        self.VK.doLogIn()

    @QtCore.pyqtSlot()
    def slotLoginWindowCancel(self):
        print("Slot Login Window cancel ")

    @QtCore.pyqtSlot()
    def slotSettingsWindowOk(self):
        print("Slot settings window ok")
        self.VK.setUp(self.loginDialog.loginLE.text(), self.loginDialog.passwordLE.text())

    @QtCore.pyqtSlot()
    def slotSettingsWindowCancel(self):
        print("Slot settings window cancel ")

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def slotDialogSelected(self, item):
        print("Slot dialog selected")
        dialogWidget = self.listWidget.itemWidget(item)
        id = dialogWidget.id
        self.mw = MessangerWindow()
        self.mw.show()


class DialogToWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/dialogTo.ui"

    def __init__(self, dialog, body, userName,
                 title, pixmapTo, pixmapFrom,
                 uiFile = defaultUiFile,
                 parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.id = dialog["message"]["user_id"]
        uic.loadUi(uiFile, self)
        self.bodyLabel.setText(body)
        self.iconLabel.setPixmap(pixmapTo.scaledToHeight(64, 1))
        self.mIconLabel.setPixmap(pixmapFrom.scaledToHeight(38, 1))
        if title == " ... ":
            self.titleLabel.setText(userName)
        else:
            self.titleLabel.setText(title)


class DialogFromWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/dialogFrom.ui"

    def __init__(self, dialog, body, userName,
                 title, pixmap,
                 uiFile=defaultUiFile,
                 parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)
        self.id = dialog["message"]["user_id"]
        self.bodyLabel.setText(body)
        self.iconLabel.setPixmap(pixmap.scaledToHeight(64, 1))
        if title == " ... ":
            self.titleLabel.setText(userName)
        else:
            self.titleLabel.setText(title)


class MessageWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/message.ui"

    def __init__(self, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)


class MessangerWindow(QtWidgets.QWidget):
    defaultUiFile = "ui/messenger.ui"

    def __init__(self, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)



class LoginWindow(QtWidgets.QDialog):
    defaultUiFile = "ui/login.ui"

    def __init__(self, OK_slot, cancel_slot, uiFile = defaultUiFile, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        uic.loadUi(uiFile, self)
        self.accepted[()].connect(OK_slot)
        self.rejected[()].connect(cancel_slot)
        self.show()

    @QtCore.pyqtSlot()
    def OK(self):
        print("OK:" + self.loginLE.text() + ":" + self.passwordLE.text())

    @QtCore.pyqtSlot()
    def cancel(self):
        print("Cancel:" + self.loginLE.text() + ":" + self.passwordLE.text())


class Myself(object):
    def __init__(self, user):
        self.user = user
        self.photo_100 = QPixmap()
        if user == myvk.dummyUser.getJson():
            pass
        else:
            try:
                req = requests.get(self.user["photo_100"], timeout=(5, 6))
                self.photo_100.loadFromData(req.content)
            except requests.exceptions.ConnectionError:
                print("ConnectionError")

        print(user)

        self.id = user["id"]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
