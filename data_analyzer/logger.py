import datetime
import os


class Log:
    def __init__(self, log_file: str):
        self.__log_file = log_file

    def write(self, message: str) -> None:
        log_msg = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        
        print(log_msg)

        log_arr = []
        if os.path.isfile(self.__log_file):
            with open(self.__log_file) as f_log:
                log_arr = f_log.read().split("\n")
            
        while len(log_arr) > 10000:
            log_arr.pop()
            
        log_arr.insert(0, log_msg)
        
        with open(self.__log_file, "w") as f_log_w:
            f_log_w.write("\n".join(log_arr))

    def print_console(self, message: str) -> None:
        print((datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message))