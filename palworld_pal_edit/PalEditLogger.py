import os

class Logger:

    def __init__(self):
        if os.path.exists("log.txt"):
            os.remove("log.txt")
        self.log = open("log.txt", "a", buffering=1)
        self.WriteLog("= START OF LOG =")

    def WriteLog(self, string):
        print(string)
        self.log.write(string)
        self.log.write("\n")

    def Close(self):
        self.WriteLog("= END OF LOG =")
        self.log.close()

    def Space(self):
        self.WriteLog("")

if __name__ == "__main__":
    test = Logger()
    test.WriteLog("testing logger")
    test.Close()
