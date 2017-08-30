import vk_api
import json
from vk_api.audio import VkAudio



def dumpData(data, filename=dumpFile):
    dump = json.dumps(data, indent=4, ensure_ascii=False)
    with open(filename, "w") as file:
        print(dump, file=file)
    print("Dumped.")



def getDataFromJson(fileName):
    with open(fileName, "r") as file:
        data = json.load(file)
    print(data)



def main():
    print("Hello.")



    doAuth(vk_session)


    begin = 0
    end = 3
    dialogs = getDialogs(vk_session, begin, end)

    dumpData(dialogs, filename="json/dialogs.json")



if __name__ == '__main__':
    main()
