import sys
import traceback
from typing import Any, Dict, Optional, Tuple

from shravs_utils.exceptions.exception_meta import ExceptionMeta

class ShravsError(Exception, metaclass=ExceptionMeta):
    """
    Base Shravs error class for tracking errors.
    Provides error formatting with error code, details, additional context, and traceback.
    """
    details: Dict[str, Any]      # additional keyword arguments (always a dict)
    objects: Tuple[Any, ...]      # additional positional arguments (excluding the fixed ones)

    # Declare the properties with type hints
    @property
    def tb(self) -> Optional[str]:
        """
        Returns the formatted traceback if present.
        """
        # The actual implementation will be injected by the metaclass,
        # but you can provide a default here or simply rely on the metaclass.
        ...

    @property
    def context(self) -> Optional[BaseException]:
        """
        Returns the __context__ of the exception.
        """
        ...

    @property
    def cause(self) -> Optional[BaseException]:
        """
        Returns the __cause__ of the exception.
        """
        ...

    def __init__(self, message: str, error_code: Optional[int] = None, *args: Any, **kwargs: Any) -> None:
        """
        :param message: The error message.
        :param error_code: A generic error code for tracking.
        :param args: Additional objects providing context.
        :param kwargs: Additional details as key/value pairs.
        """
        super().__init__(message)
        self.error_code = error_code

    def format_error(self) -> str:
        base_message = f"Error: {self.args[0]}"
        if self.error_code is not None:
            base_message += f"\tError Code: {self.error_code}"
        if self.details:
            base_message += f"\nDetails: {self.details}"
        if self.objects:
            base_message += f"\nAdditional Objects: {self.objects}"
        return base_message

    def __str__(self) -> str:
        return self.format_error()

class ShravsException(Exception, metaclass=ExceptionMeta):
    """
    Base Shravs exception class that provides standard formatting and traceback capture.
    """
    details: Dict[str, Any]      # additional keyword arguments (always a dict)
    # additional positional arguments (excluding the fixed ones)
    objects: Tuple[Any, ...]
    def __init__(self, message, *args, **kwargs):
        """
        :param message: The exception message.
        :param args: Additional objects providing context.
        :param kwargs: Additional details as key/value pairs.
        """
        super().__init__(message)

    def format_exception(self):
        base_message = f"Exception: {self.args[0]}"
        if self.details:
            base_message += f"\nDetails: {self.details}"
        if self.objects:
            base_message += f"\nAdditional Objects: {self.objects}"
        return base_message

    def __str__(self):
        return self.format_exception()

    @property
    def tb(self) -> Optional[str]:
        """
        Returns the formatted traceback if present.
        """
        # The actual implementation will be injected by the metaclass,
        # but you can provide a default here or simply rely on the metaclass.
        ...

    @property
    def context(self) -> Optional[BaseException]:
        """
        Returns the __context__ of the exception.
        """
        ...

    @property
    def cause(self) -> Optional[BaseException]:
        """
        Returns the __cause__ of the exception.
        """
        ...

# Example custom error usage:
if __name__ == "__main__":
    import sys
    def check():
        try:
            raise ShravsError("A critical error occurred.", 500, details={"key": "value"})
        except ShravsError as e:
            try:
                raise ValueError("An error occurred in the application.", 45)
            except ShravsError as ae:
                # print(ae)
                # print(ae.tb)
                print(ae.context)
                # print(ae.cause)
                # raise ShravsException("An error occurred in the application.", 45, details={"key": "value"})
            # print(e.cause)
            # print(e.context)
            # print(e.tb)
    check()

    # try:
    #     raise ShravsException("An error occurred in the application.", 45, details={"key": "value"})
    # except ShravsException as e:
    #     print(e)
