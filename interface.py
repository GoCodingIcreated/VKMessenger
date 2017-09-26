from PyQt5 import QtWidgets, QtCore
from PyQt5 import uic
from PyQt5.QtWidgets import qApp
from PyQt5.QtGui import QPixmap
import requests


import myvk
import sys
import time
import datetime
import os

class MainWindow(QtWidgets.QMainWindow):
    defaultUiFile = "ui/mainWindow_v2.ui"

    def __init__(self, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)
        slots = {"Exit": self.slotExit, "Log in" : self.slotLogIn, "Log out" : self.slotLogOut,
                    "Refresh" : self.slotRefresh, "Settings" : self.slotSettings}
        for action in self.menuMenu.actions():
            if action.text() != '':
                action.triggered[(bool)].connect(slots[action.text()])

        self.listWidget.itemClicked.connect(self.slotDialogSelected)

        self.frame.hide()
        self.min_width = self.minimumWidth()
        self.max_width = self.maximumWidth()
        self.min_height = self.minimumHeight()
        self.max_height = self.maximumHeight()
        self.setFixedWidth(self.min_width)
        self.resize(self.maximumWidth(), self.height())
        self.VK = None
        self.me = None
        self.dialogs = None
        self.mw = None
        try:
            self.VK = myvk.VK()
        except FileNotFoundError:
            self.slotSettings(True)

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
        if "chat_id" in dialog["message"]:
            dialogShort = DialogChatWidget(dialog, body, user_name, title, pixmap)
        elif "random_id" in dialog["message"]:
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
        if self.VK is None:
            data = {"login" : self.loginDialog.loginLE.text(),
                    "password" : self.loginDialog.passwordLE.text()}
            myvk.dumpData(data, "json/data.json")
            self.VK = myvk.VK()
        self.VK.setUp(self.loginDialog.loginLE.text(), self.loginDialog.passwordLE.text())

    @QtCore.pyqtSlot()
    def slotSettingsWindowCancel(self):
        print("Slot settings window cancel ")
        if self.VK is None:
            self.slotSettings(True)

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def slotDialogSelected(self, item):
        print("Slot dialog selected")
        dialogWidget = self.listWidget.itemWidget(item)
        id = dialogWidget.id
        if self.mw is None:
            self.mw = MessengerWindow(dialogWidget, self.me)
            self.frameLayout.addWidget(self.mw)
            self.mw.refreshButton.clicked.connect(self.slotDialogRefresh)
            self.mw.backButton.clicked.connect(self.slotDialogBack)
            self.mw.sendButton.clicked.connect(self.slotDialogSend)
            self.mw.getMoreButton.clicked.connect(self.slotDialogGetMore)
            self.mw.stickersButton.clicked.connect(self.slotDialogStickers)
        else:
            self.mw.reload(dialogWidget)
        self.frame.show()
        self.mw.show()

        self.setFixedWidth(self.max_width)
        self.resize(self.maximumWidth(), self.height())


        self.slotDialogRefresh()

    @QtCore.pyqtSlot()
    def slotDialogGetMore(self):
        end = len(self.mw.listWidget) + 5
        begin = 0
        self.slotDialogRefresh(begin, end)

    @QtCore.pyqtSlot()
    def slotDialogSend(self):
        print("slot Dialog send")
        if self.mw.dialogWidget.chat_id is not None:
            self.VK.sendMessageToChat(self.mw.dialogWidget.id - self.mw.dialogWidget.MAGIC_NUMBER,
                                      self.mw.inputPText.toPlainText())
        else:
            self.VK.sendMessageToDialog(self.mw.dialogWidget.id,
                                        self.mw.inputPText.toPlainText())
        self.mw.inputPText.setPlainText("")
        self.slotDialogRefresh()

    @QtCore.pyqtSlot()
    def slotDialogBack(self):
        print("slot dialog back")
        self.mw.hide()
        self.frame.hide()
        self.mw = None
        self.setFixedWidth(self.min_width)
        self.resize(self.minimumWidth(), self.height())

    @QtCore.pyqtSlot()
    def slotDialogRefresh(self, begin=0, end=5):
        print("slot Dialog Refresh")
        end = max(end, len(self.mw.listWidget))
        messages = self.VK.getMessagesFromDialog(self.mw.dialogWidget.id, begin, end)
        print(messages)
        self.mw.listWidget.clear()
        users = {self.me.user["id"] : self.me.user}
        for message in messages["items"]:
            if message["from_id"] not in users:
                users[message["from_id"]] = self.VK.getUserById(message["from_id"])
                if users[message["from_id"]] == myvk.dummyUser.getJson():
                    pass
                else:
                    iconUrl = users[message["from_id"]]["photo_100"]
                    req = requests.get(iconUrl, timeout=(5, 6))
                    pixmap = QPixmap()
                    pixmap.loadFromData(req.content)
                    users[message["from_id"]]["pixmap"] = pixmap

        for message in messages["items"]:
            messageWidget = MessageWidget(self.mw.dialogWidget.dialog, message, users[message["from_id"]])

            item = QtWidgets.QListWidgetItem("", self.mw.listWidget)
            item.setSizeHint(messageWidget.sizeHint())
            self.mw.listWidget.setItemWidget(item, messageWidget)

    @QtCore.pyqtSlot()
    def slotDialogStickers(self):
        self.stickersList = StickersListWidget()
        self.stickersList.show()

    @QtCore.pyqtSlot()
    def slotDialogStickerSend(self):
        pass


class DialogChatWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/dialogTo.ui"

    def __init__(self, dialog, body, userName,
                 title, pixmap, uiFile=defaultUiFile,
                 parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)

        self.dialog = dialog
        self.MAGIC_NUMBER = 2000000000

        self.chat_id = dialog["message"]["chat_id"]
        self.id = self.chat_id + self.MAGIC_NUMBER

        curTime = int(dialog["message"]["date"])
        curTime = datetime.datetime.fromtimestamp(curTime).strftime("%H:%M:%S")
        self.timeLabel.setText(curTime)

        if dialog["message"]["read_state"] == 0:
           self.bodyLabel.setStyleSheet("QLabel { background-color : rgba(90, 90, 90, 45); }")
        self.bodyLabel.setText(body)
        #self.iconLabel.setPixmap(pixmapTo.scaledToHeight(50, 1))
        pixmapChat = QPixmap()
        if "photo_50" in dialog["message"]:
            try:
                req = requests.get(dialog["message"]["photo_50"], timeout=(5, 6))
                pixmapChat.loadFromData(req.content)
            except requests.exceptions.ConnectionError:
                print("ConnectionError")
        self.iconLabel.setPixmap(pixmapChat.scaledToHeight(50, 1))
        self.mIconLabel.setPixmap(pixmap.scaledToHeight(25, 1))

        self.titleLabel.setText(title)


class DialogToWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/dialogTo.ui"

    def __init__(self, dialog, body, userName,
                 title, pixmapTo, pixmapFrom,
                 uiFile = defaultUiFile,
                 parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)

        self.dialog = dialog
        self.id = dialog["message"]["user_id"]
        self.chat_id = None
        curTime = int(dialog["message"]["date"])
        curTime = datetime.datetime.fromtimestamp(curTime).strftime("%H:%M:%S")
        self.timeLabel.setText(curTime)

        if dialog["message"]["read_state"] == 0:
           self.bodyLabel.setStyleSheet("QLabel { background-color : rgba(90, 90, 90, 45); }")
        self.bodyLabel.setText(body)
        self.iconLabel.setPixmap(pixmapTo.scaledToHeight(50, 1))
        self.mIconLabel.setPixmap(pixmapFrom.scaledToHeight(25, 1))

        #if title == " ... ":
        if not "chat_id" in dialog["message"]:
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

        self.dialog = dialog
        if "unread" in dialog:
            self.unreadLabel.setText(str(dialog["unread"]))
            self.unreadLabel.setStyleSheet("QLabel { background-color : rgba(90, 90, 90, 45); }")
            self.bodyLabel.setStyleSheet("QLabel { background-color : rgba(90, 90, 90, 45); }")
        else:
            self.unreadLabel.setText("")
        curTime = int(dialog["message"]["date"])
        curTime = datetime.datetime.fromtimestamp(curTime).strftime("%H:%M:%S")
        self.timeLabel.setText(curTime)
        self.id = dialog["message"]["user_id"]
        self.chat_id = None
        self.bodyLabel.setText(body)
        self.iconLabel.setPixmap(pixmap.scaledToHeight(50, 1))
        if not "chat_id" in dialog["message"]:
            self.titleLabel.setText(userName)
        else:
            self.titleLabel.setText(title)


class MessageWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/message.ui"

    def __init__(self, dialog, message, user, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)
        curTime = int(message["date"])
        curTime = datetime.datetime.fromtimestamp(curTime).strftime("%H:%M:%S")
        self.timeLabel.setText(curTime)
        self.message = message
        user_id = message["from_id"]
        if message["read_state"] == 0:
            self.bodyLabel.setStyleSheet("QLabel { background-color : rgba(90, 90, 90, 45); }")
        self.nameLabel.setText(user["first_name"] + " " + user["last_name"])
        self.iconLabel.setPixmap(user["pixmap"].scaledToHeight(32, 1))
        self.bodyLabel.setText(message["body"])


class MessengerWindow(QtWidgets.QWidget):
    defaultUiFile = "ui/messenger.ui"

    def __init__(self, dialogWidget, me, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)
        self.dialogWidget = dialogWidget
        self.me = me
        self.iconLabel.setPixmap(dialogWidget.iconLabel.pixmap())

    def reload(self, dialogWidget):
        self.dialogWidget = dialogWidget
        self.iconLabel.setPixmap(dialogWidget.iconLabel.pixmap())



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


class StickersListWidget(QtWidgets.QWidget):
    defaultUiFile = "ui/stickers.ui"
    defaultStickersDir = "stickers/"

    def __init__(self, stickersDir=defaultStickersDir, uiFile = defaultUiFile, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        uic.loadUi(uiFile, self)

        dirs = [dir for dir in os.listdir(stickersDir)
                if os.path.isdir(os.path.join(stickersDir, dir))]

        self.stickersByProduct = { dir : [] for dir in dirs }
        self.stickersById = {}
        print("Dirs:")
        print(dirs)
        for dir in dirs:
            dirpath = os.path.join(stickersDir, dir)
            path64 = os.path.join(dirpath, "64")
            path128 = os.path.join(dirpath, "128")
            for stickerName in os.listdir(path64):
                sticker64 = os.path.join(path64, stickerName)
                sticker128 = os.path.join(path128, stickerName)
                stickerId = os.path.splitext(stickerName)[0]

                sticker = Sticker(stickerId, dir, sticker64, sticker128)
                self.stickersById[stickerId] =  sticker
                self.stickersByProduct[dir].append(sticker)


        print("StickerByProduct and ById:")
        print(self.stickersByProduct)
        print(self.stickersById)
        count = 0
        for stickersPackId in self.stickersByProduct:
            count += 1
            print("Sticker pack "  + str(count))


            stickersTable = StickersTable()
            stickersTable.addPack(self.stickersByProduct[stickersPackId])
            self.tabWidget.addTab(stickersTable, str(count))


class StickersTable(QtWidgets.QWidget):
    defaultUiFile = "ui/stickersTable.ui"

    def __init__(self, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)

    def addPack(self, stickerPack):
        self.tableWidget.setColumnCount(3)
        if len(stickerPack) == 0:
            self.tableWidget.setRowCount(0)
            return

        maxCols = 3
        rows = 1 + (len(stickerPack) - 1) / maxCols
        self.tableWidget.setRowCount(rows)

        row = 0
        col = 0
        for sticker in stickerPack:
            stickerWidget = StickerWidget(sticker)
            print(str(row) + " " + str(col))
            self.tableWidget.setCellWidget(row, col, stickerWidget)
            col += 1
            row += col // maxCols
            col %= maxCols


class Sticker(object):
    def __init__(self, id, product_id, path64, path128):
        self.pixmap64 =  QPixmap(path64)
        self.pixmap128 = QPixmap(path128)
        self.product_id = product_id
        self.id = id

    def getSmallIcon(self):
        return self.pixmap64

    def getIcon(self):
        return self.pixmap128

    def getId(self):
        return self.id

    def getProductId(self):
        return self.product_id


class StickerWidget(QtWidgets.QWidget):
    defaultUiFile="ui/stickerWidget.ui"

    def __init__(self, sticker, uiFile=defaultUiFile, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(uiFile, self)
        self.sticker = sticker
        self.label.setPixmap(sticker.getSmallIcon())


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
        self.user["pixmap"] = self.photo_100
        print(user)

        self.id = user["id"]


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
