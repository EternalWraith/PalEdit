import os
import logging
import sys

class Logger(logging.Logger):

    def __init__(self):
        super().__init__("PalEdit", logging.DEBUG)
        if os.path.exists("log.txt"):
            os.remove("log.txt")
        self.log = open("log.txt", "a", encoding="UTF-8", buffering=1)
        log_steam = logging.StreamHandler(self.log)
        log_steam.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s :: %(message)s'))
        self.addHandler(log_steam)
        log_steam = logging.StreamHandler(sys.stderr)
        log_steam.setFormatter(logging.Formatter(fmt='%(levelname)-8s :: %(message)s'))
        log_steam.setLevel(logging.INFO)
        self.addHandler(log_steam)
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
