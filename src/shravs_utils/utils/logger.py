import os
import sys
import logging
import traceback
import re
from logging.handlers import TimedRotatingFileHandler
from rich.console import Console
from rich.traceback import Traceback
from rich.logging import RichHandler
from shravs_utils.exceptions.enhanced_exception import EnrichException

# --- Global Configuration ---
LOG_TO_CONSOLE = os.environ.get("LOG_TO_CONSOLE", "true").lower() != "false"
LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "false").lower() == "true"
ENABLE_COLOR_LOGGING = os.environ.get("ENABLE_COLOR_LOGGING", "true").lower() != "false"
ENABLE_RICH_LOGGING = os.environ.get("ENABLE_RICH_LOGGING", "true").lower() != "false"
ENABLE_THIRD_PARTY_LOGGING = os.environ.get("ENABLE_THIRD_PARTY_LOGGING", "false").lower() == "true"
PRINT_AS_LOG = os.environ.get("PRINT_AS_LOG", "false").lower() == "true"
DEFAULT_LOG_LEVEL = os.environ.get("DEFAULT_LOG_LEVEL", "DEBUG").upper()
THIRD_PARTY_ENDPOINT = os.environ.get("THIRD_PARTY_ENDPOINT", "http://your-elk-server:9200")
LOGS_DIR = os.environ.get("LOG_DIR", default=None)

# Base format for non-rich configuration.
BASE_FORMAT = ("[%(asctime)s] [%(levelname)s] [%(name)s] "
               "[Module: %(module)s] [Func: %(funcName)s] [Line: %(lineno)d] "
               "- %(message)s")


def convert_markup_to_ansi(text: str) -> str:
    ansi_codes = {
        "cyan": "\033[36m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "magenta": "\033[35m",
        "white": "\033[37m"
    }
    # Replace opening tags like [cyan]
    text = re.sub(r'\[([a-z]+)\]',
                  lambda m: ansi_codes.get(m.group(1), ""), text)
    # Replace closing tags like [/cyan] with reset
    text = re.sub(r'\[/[a-z]+\]', "\033[0m", text)
    return text

# --- Plain Formatter for non-rich logging ---
class PlainCustomFormatter(logging.Formatter):
    COLOR_MAP = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "magenta",
    }

    def __init__(self, use_color: bool = True):
        super().__init__(fmt=BASE_FORMAT)
        self.use_color = use_color

    def formatException(self, ei):
        exc_type, exc_value, exc_tb = ei
        if exc_value is None:
            raise ValueError("Exception value cannot be None")
        enriched = EnrichException(exc_value)
        extra = ("[Module: {module}] [Func: {function}] [Line: {line_no}] "
                 "[Class: {defining_class}]").format(
                    module=enriched.module,
                    function=enriched.function,
                    line_no=enriched.line_no,
                    defining_class=enriched.defining_class,
                )
        original = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        return f"{original}\nAdditional Exception Info-> {extra}"

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        record.message = record.getMessage()
        s = self._fmt % record.__dict__  # type: ignore[assignment]
        if record.exc_info:
            s += "\n" + self.formatException(record.exc_info)
        if self.use_color:
            level = record.levelname.strip("[]").split()[0]
            color = self.COLOR_MAP.get(level, "white")
            s = f"[{color}]{s}[/{color}]"
            s = convert_markup_to_ansi(s)  # Convert our markup tags into ANSI escapes.
        return s

# --- Custom Rich Formatter ---
class CustomRichFormatter(logging.Formatter):
    """
    A custom formatter that uses rich formatting.
    RichHandler generally controls most console details, but this formatter
    ignores any pre-set formatting from inbuilt libraries and enforces our BASE_FORMAT.
    """
    def formatException(self, ei):
        base = "".join(traceback.format_exception(*ei))
        exc_type, exc_value, exc_tb = ei
        if exc_value is None:
            raise ValueError("Exception value cannot be None")
        enriched = EnrichException(exc_value)
        extra = ("[Module: {module}] [Func: {function}] [Line: {line_no}] "
                 "[Class: {defining_class}]").format(
                    module=enriched.module,
                    function=enriched.function,
                    line_no=enriched.line_no,
                    defining_class=enriched.defining_class,
                )
        return f"{base}\nAdditional Exception Info -> {extra}"

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        record.message = record.getMessage()
        s = BASE_FORMAT % record.__dict__
        if record.exc_info:
            s += "\n" + self.formatException(record.exc_info)
        return s

# --- Custom Rich Handler ---
class CustomRichHandler(RichHandler):
    def formatException(self, ei):
        """Override the default exception formatting to include enriched information."""
        base = super().formatException(ei) #type: ignore[no-untyped-call]
        exc_type, exc_value, exc_tb = ei
        if exc_value is None:
            raise ValueError("Exception value cannot be None")
        enriched = EnrichException(exc_value)
        extra = ("[Module: {module}] [Func: {function}] [Line: {line_no}] "
                 "[Class: {defining_class}]").format(
                    module=enriched.module,
                    function=enriched.function,
                    line_no=enriched.line_no,
                    defining_class=enriched.defining_class,
                )
        return f"{base}\nAdditional Exception Info -> {extra}"

# --- Third Party Handler (stub) ---
class ThirdPartyHandler(logging.Handler):
    def __init__(self, endpoint: str):
        super().__init__()
        self.endpoint = endpoint

    def emit(self, record):
        try:
            msg = self.format(record)
            sys.stderr.write(f"[ThirdParty Log to {self.endpoint}] {msg}\n")
        except Exception:
            self.handleError(record)

# --- Logger Setup ---
def get_logger(name: str = __name__, propagate: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL, logging.DEBUG))
    logger.propagate = propagate

    if not logger.handlers:  # avoid duplicate handlers
        if LOG_TO_CONSOLE:
            if ENABLE_RICH_LOGGING:
                # Use our CustomRichHandler which leverages Rich's formatting.
                handler = CustomRichHandler(markup=True, rich_tracebacks=True)
            else:
                handler = logging.StreamHandler(sys.stdout)
                formatter = PlainCustomFormatter(use_color=ENABLE_COLOR_LOGGING)
                handler.setFormatter(formatter)
            logger.addHandler(handler)

        if LOG_TO_FILE:
            # Determine logs folder.
            log_dir = LOGS_DIR
            if not log_dir:
                log_dir = os.path.join(os.getcwd(), ".logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, f"{name}.log")
            file_handler = TimedRotatingFileHandler(log_file, when="h", interval=1, backupCount=0)
            # For file logging, we keep plain (non-colored) output.
            file_formatter = PlainCustomFormatter(use_color=False)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        if ENABLE_THIRD_PARTY_LOGGING:
            thirdparty = ThirdPartyHandler(THIRD_PARTY_ENDPOINT)
            third_party_formatter = PlainCustomFormatter(use_color=False)
            thirdparty.setFormatter(third_party_formatter)
            logger.addHandler(thirdparty)

    return logger

# --- Print Patch ---
_original_print = print
def patched_print(*args, **kwargs):
    logger = get_logger("print_redir")
    msg = " ".join(str(x) for x in args)
    logger.info(msg)

def patch_print():
    if PRINT_AS_LOG:
        builtins = __import__("builtins")
        builtins.print = patched_print

# --- Auto-Attach to Parent Loggers ---
def auto_attach_logger(logger: logging.Logger):
    parts = logger.name.split('.')
    if len(parts) > 1:
        parent_name = ".".join(parts[:-1])
        parent_logger = logging.getLogger(parent_name)
        logger.propagate = True
        for handler in parent_logger.handlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)

def get_all_loggers() -> dict:
    """
    Returns all registered loggers (both built-in and custom ones).
    """
    loggers = {}
    manager = logging.root.manager
    for name, logger in manager.loggerDict.items():
        # Some entries in loggerDict can be placeholders; only include Logger instances.
        if isinstance(logger, logging.Logger):
            loggers[name] = logger
    return loggers


def force_custom_formatter(force: bool, use_rich: bool = False):
    """
    When force is True, overrides eligible handlers for all registered loggers by
    replacing them with handlers that use a custom formatter.

    Eligible handlers are those that are not instances of RichHandler or CustomRichHandler
    and are not already using our custom formatters.

    Set use_rich to True to force use of CustomRichFormatter, otherwise PlainCustomFormatter is used.
    """
    if not force:
        return

    # Select the custom formatter to use.
    custom_formatter = CustomRichFormatter() if use_rich else PlainCustomFormatter(use_color=ENABLE_COLOR_LOGGING)

    # Iterate through all registered loggers.
    for name, logger in get_all_loggers().items():
        # Skip the logger that Rich creates.
        if name == "rich":
            continue

        new_handlers = []
        # Iterate over a shallow copy of the handlers.
        for handler in logger.handlers[:]:
            # Exclude Rich based handlers.
            if isinstance(handler, (RichHandler, CustomRichHandler)):
                new_handlers.append(handler)
                continue

            current_formatter = handler.getFormatter()
            # Skip if already set to one of our custom formatters.
            if current_formatter is not None and isinstance(current_formatter, (PlainCustomFormatter, CustomRichFormatter)):
                new_handlers.append(handler)
                continue

            # Remove and replace the handler.
            if hasattr(handler, "setFormatter"):
                try:
                    # Update the formatter.
                    handler.setFormatter(custom_formatter)
                    new_handlers.append(handler)
                except Exception as e:
                    print(f"Error setting formatter for handler {handler}: {e}")
            else:
                new_handlers.append(handler)
        logger.handlers = new_handlers

# --- Initialization ---
patch_print()

# Example usage: demonstrate the separate logging configurations.
if __name__ == "__main__":
    logger = get_logger("super_logger.demo")

    def test_logging():
        auto_attach_logger(logger)
        logger.debug("This is a debug message with rich context.")
        logger.info("Regular info message.")
        logger.warning("A warning message with extra parent info.")
        logger.error("This is an error message")
        # print("hello world")
        try:
            1 / 0
        except Exception:
            # logger.error("An exception occurred.", exc_info=True)
            logger.critical("Critical error with traceback.", exc_info=True)

    test_logging()
    # logger = logging.getLogger("super_logger.demo2")
    # # Retrieve and print all registered loggers
    # all_loggers = get_all_loggers()
    # print("Registered Loggers:", list(all_loggers.keys()))

    # # Toggle forced custom formatting on all registered loggers.
    # # To force plain formatting:
    # force_custom_formatter(True, use_rich=False)
    # logger.info("This log now uses the forced custom formatter (plain format).")

    # # To force rich formatting:
    # force_custom_formatter(True, use_rich=True)
    # logger.info("This log now uses the forced custom formatter (rich format).")



