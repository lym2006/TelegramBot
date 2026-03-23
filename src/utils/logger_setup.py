import logging

def setup_logger(
    name:str="BotLogger",
    level:int=logging.INFO,
    format:str="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt:str="%Y-%m-%d %H:%M:%S"
) -> logging.Logger:
    logger=logging.getLogger(name)
    logger.propagate=False
    logger.setLevel(level)
    if not logger.handlers:
        console_handler=logging.StreamHandler()
        console_handler.setLevel(level)
        formatter=logging.Formatter(format,datefmt)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger