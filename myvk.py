import vk_api
import json
import requests
import os
from urllib import parse
dataFile = "json/data.json"
dumpFile = "json/dump.json"

USERFILESDIR = "json/user/"
USERFILE = "id*.json"
USERFILEPATH = USERFILESDIR + USERFILE
MEFILE = "me.json"
MEPATH = USERFILESDIR + MEFILE

DIALOGSDIR = "json/dialogs/"
DIALOGSLISTFILE = "dialog_list.json"
DIALOGSLISTPATH = DIALOGSDIR + DIALOGSLISTFILE

def dumpData(data, filename=dumpFile):
    dump = json.dumps(data, indent=4, ensure_ascii=False)
    with open(filename, "w") as file:
        print(dump, file=file)
    print("Dumped %s." % filename)

def getDataFromJson(fileName):
    with open(fileName, "r") as file:
        data = json.load(file)
    print(data)
    return data


class VK(object):
    defaultDataFile = "json/data.json"

    def __init__(self, dataFile=defaultDataFile):

        self.hasInternet = True
        with open(dataFile) as file:
           data = json.load(file)
        login = data["login"]
        password = data["password"]
        self.setUp(login, password)
        self.isAuth = True




    def setUp(self, login, password):
        self.vk_session = vk_api.VkApi(login, password)

    def doLogIn(self):
        if not self.hasInternet:
            return
        try:
            self.vk_session.auth()
            self.isAuth = True
            print("Success auth.")
        except vk_api.AuthError as err:
            print(err)
            self.isAuth = False
        except requests.exceptions.ConnectionError as err:
            print(err)


    def doLogOut(self):
        self.vk_session = None
        self.isAuth = False

    def getDialogs(self, begin = 0, end = 5):
        if not self.hasInternet:
            if DIALOGSLISTFILE in os.listdir(DIALOGSDIR):
                dialogs = getDataFromJson(DIALOGSLISTPATH)
            else:
                dialogs = dummyDialogList.getJson()
            return dialogs

        if not self.isAuth:
            return None
        try:
            dialogs = self.vk_session.get_api().messages.getDialogs(
                            offset=begin,
                            count=end - begin,
                            timeout=(0.001, 0.001))
            print("Got dialogs.")
            dumpData(dialogs, DIALOGSLISTPATH)
        except requests.exceptions.ConnectionError:
            print("ConnectionError Dialogs")
            if DIALOGSLISTFILE in os.listdir(DIALOGSDIR):
                dialogs = getDataFromJson(DIALOGSLISTPATH)
            else:
                dialogs = dummyDialogList.getJson()
        print(dialogs)
        return dialogs

    def getMessagesFromDialog(self, dialog, begin = 0, end = 5):
        if not self.hasInternet:
            return None
        if self.vk_session is None:
            return None
        messages = self.vk_session.get_api().messages\
            .getHistory(count=end-begin,
                        user_id=dialog["message"]["user_id"],
                        rev=0,
                        #start_message_id=0,
                        #offset=0
                        )
        dumpData(messages)
        return messages

    def sendMessageToDialog(self, dialog, text):
        self.vk_session.get_api().messages.send(user_id=dialog["message"]["user_id"],
                                                message=text)

    def getUserById(self, userId):
        userfile = USERFILE.replace("*", str(userId))
        if self.hasInternet: # TODO: replace for NOT condition
            if userfile in os.listdir(USERFILESDIR):
                print(os.path.getmtime(USERFILEPATH.replace("*", str(userId))))
                return getDataFromJson(USERFILEPATH.replace("*", str(userId)))
            return dummyUser.getJson()

        try:
            #if userfile in os.listdir(USERFILESDIR) and
            #    os.path.getmtime(USERFILEPATH.replace("*", str(userId))) :

            user = self.vk_session.get_api().users.get(user_ids=userId,
                                                       fields='photo_50,photo_100',
                                                       timeout=(5, 6))
            dumpData(user[0], USERFILEPATH.replace("*", str(userId)))
        except requests.exceptions.ConnectionError as e:
            if userfile in os.listdir(USERFILESDIR):
                return getDataFromJson(USERFILEPATH.replace("*", str(userId)))
            return dummyUser.getJson()
        if len(user) > 0:
            return user[0]

    def getMyId(self):
        if self.vk_session is not None:
            return self.vk_session.token["user_id"]
        return dummyUser.getJson()["id"]

    def getMe(self):
        mepath = USERFILEPATH.replace("*", str(self.getMyId()))
        mefile = USERFILE.replace("*", str(self.getMyId()))
        if not self.hasInternet:
            if mefile in os.listdir(USERFILESDIR):
                return getDataFromJson(mefile)
            else:
                return dummyUser.getJson()
        if self.vk_session is not None:
            try:
                user = self.vk_session.get_api().users.get(
                    user_ids=self.getMyId(),
                    fields='photo_50,photo_100')

                dumpData(user[0], mepath)
            except requests.exceptions.ConnectionError:
                print("ConnectionError")
                if mefile in os.listdir(USERFILESDIR):
                    return getDataFromJson(mepath)
            if len(user) > 0:
                return user[0]

        return dummyUser.getJson()




class DummyUser(object):

    def __init__(self):
        pass

    def getJson(self):
        return {"id" : 0,
                "photo_50" : 0,
                "photo_100" : 0,
                "first_name" : "Dummy",
                "last_name" : "User"}

class DummyDialogList(object):
    def __init__(self):
        pass

    def getJson(self):
        return getDataFromJson("json/dialogs.json")


dummyUser = DummyUser()
dummyDialogList = DummyDialogList()

if __name__ == "__main__":
    vk = VK()
    dialogs = vk.getDialogs()
    for dialog in dialogs["items"]:
        print(str(dialog["message"]["user_id"])
              + ":"
              + dialog["message"]["body"])
