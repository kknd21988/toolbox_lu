import logging
import time
from approot import get_root
import os
import re
import traceback

record_time_raw = str(time.strftime("%Y-%m-%d %H:%M:%S"))
record_time = re.sub(r'[\s:]', '_', record_time_raw)


def get_logger(folder, file_prefix=""):
    # 当前时间
    record_time = str(time.strftime("%Y-%m-%d %H:%M:%S"))
    record_time = re.sub(r'[\s:]', '_', record_time)

    # 日志设置
    # folder = os.path.join(get_root(), r'logs\debug_log')
    if os.path.exists(folder) == False:
        try:
            os.makedirs(folder)
        except Exception as e:
            print(e)
            raise
    log_file = os.path.join(folder, "{prefix}_{time}.log".format(prefix=file_prefix, time=record_time))
    log_level = logging.DEBUG
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler(log_file, "a", encoding='UTF-8')
    handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(log_level)
    logger.info("日志产生时间：{}".format(str(time.strftime("%Y-%m-%d %H:%M:%S"))))
    return logger




# 每次启动服务的logger
logger = get_logger(folder=os.path.join(get_root(), 'logs', 'debug_log'), file_prefix="service_start")
a=1


# 每个文件修改自己的日志文件
# record_time = str(time.strftime("%Y-%m-%d"))
# folder = os.path.join(get_root(), r"logs\debug_log\{}".format(record_time))
# pure_title, _ = os.path.splitext(process_info.title)
# log_file = os.path.join(folder, "{prefix}_{time}.log".format(prefix=pure_title, time=record_time))
# handler = logging.FileHandler(log_file, "a", encoding='UTF-8')
# handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
# logger.removeHandler()