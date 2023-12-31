import asyncio
import logging
import sys
from typing import Callable, Optional, Awaitable

from hypercorn.config import Config as HyperCornConfig
from loguru import logger
from quart.logging import default_handler as quart_logging_default_handler

from duodrone.data import OuterEvent


class DuodroneLoggingConfig:
    use_default_loggers: bool = True
    """
    Or you can config your own loguru loggers:
    https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
    """

    format: str = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <5}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>")
    """Source: https://github.com/Delgan/loguru/issues/586#issuecomment-1030819250"""

    duodrone_level: str = "WARNING"
    """duodrone log level"""
    quart_level: str = "WARNING"
    """quart log level"""
    hypercorn_level: str = "WARNING"
    """hypercorn log level"""
    httpx_level: str = "WARNING"
    """httpx log level"""


class LoguruInterceptHandler(logging.Handler):
    """
    Intercept python logging module logs to loguru.
    https://stackoverflow.com/a/65331310/11397457
    https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = logging.currentframe(), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class DuodroneConfig:
    """
    Configurations for duodrone module.
    """

    __instance: 'DuodroneConfig' = None

    debug: bool = False

    logging: DuodroneLoggingConfig = DuodroneLoggingConfig()
    """duodrone uses loguru library for logging: https://loguru.readthedocs.io"""

    outer_event_handler: Callable[[OuterEvent], None] = lambda self, resp: logger.info(f'Dummy get outer response: {resp}')
    """outer event handler"""

    hypercorn_config = HyperCornConfig()
    """hypercorn config"""

    hypercorn_shutdown_trigger: Optional[Callable[..., Awaitable[None]]] = None
    """hypercorn shutdown trigger"""

    event_loop: asyncio.AbstractEventLoop = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(DuodroneConfig, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        """Default configs"""

        # Armor Class 15 (natural armor), Hit Points 11 (2d8 + 2)
        self.hypercorn_config.bind = 'localhost:1511'

    def config_behaviors(self):
        self.check_required_configs()
        self.config_logging()

    def check_required_configs(self):
        for cfg, name in {(self.event_loop, 'event_loop')}:
            if cfg is None:
                raise ValueError(f'Config `duodrone.{name}` must be set.')

    def config_logging(self):
        # remove default logging sink (stderr)
        logger.remove()

        # add loguru intercept handler to dependencies' logging library loggers
        logging.basicConfig(handlers=[LoguruInterceptHandler()], level=0, force=True)

        # add default loggers
        if self.logging.use_default_loggers:
            logger_format = self.logging.format
            log_level = self.logging.duodrone_level

            # https://clig.dev/#the-basics
            # access logs (logger.bind(a=True).info(...)) to stdout
            logger.add(sys.stdout, filter=lambda record: "o" in record["extra"], format=logger_format, level=log_level, enqueue=True)
            # other logs to stderr
            logger.add(sys.stderr, filter=lambda record: "o" not in record["extra"], format=logger_format, level=log_level, enqueue=True)


duodrone_config = DuodroneConfig()


async def config_dependencies_loggers_after_init():
    # https://pgjones.gitlab.io/quart/how_to_guides/logging.html#disabling-removing-handlers
    for _logger in {logging.getLogger('quart.app'), logging.getLogger('quart.serving')}:
        _logger.setLevel(duodrone_config.logging.quart_level)
        _logger.removeHandler(quart_logging_default_handler)

    # https://pgjones.gitlab.io/hypercorn/how_to_guides/logging.html
    # with reading the code of hypercorn.logging._create_logger
    for _logger in {logging.getLogger('hypercorn.access'), logging.getLogger('hypercorn.error')}:
        _logger.setLevel(duodrone_config.logging.hypercorn_level)
        for handler in _logger.handlers:
            if not isinstance(handler, LoguruInterceptHandler):
                _logger.removeHandler(handler)

    # https://www.python-httpx.org/logging/
    for _logger in {logging.getLogger('httpx'), logging.getLogger('httpcore')}:
        _logger.setLevel(duodrone_config.logging.httpx_level)
