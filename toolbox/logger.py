import logging
from os import path, makedirs


# Logs dir
logs_dir_path = path.join(path.dirname(path.abspath(__file__)), "..", "logs")
makedirs(name=logs_dir_path, exist_ok=True)

# Formatters
file_formatter = logging.Formatter("%(asctime)s %(funcName)-10s [%(levelname)s] %(message)s")
console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Redirect all logs to the file
file_handler = logging.FileHandler(filename=f"{logs_dir_path}/bridge.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Show on the console only INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
console_handler.addFilter(type("", (logging.Filter,), {"filter": lambda s, r: r.levelno == logging.INFO})())

# Add handlers to the root loger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Setup custom loggers
for lib in ["WDM", "urllib3", "selenium"]:
    lib_logger = logging.getLogger(lib)
    lib_logger.setLevel(logging.DEBUG)
    lib_logger.propagate = False
    lib_file_handler = logging.FileHandler(f"{logs_dir_path}/{lib}.log", mode="w")
    lib_file_handler.setLevel(logging.DEBUG)
    lib_file_handler.setFormatter(file_formatter)
    lib_logger.addHandler(lib_file_handler)
