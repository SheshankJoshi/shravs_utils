import os
import traceback
import inspect
from typing import Any, Dict, Optional

from shravs_utils.exceptions.exception_meta import ExceptionMeta

class EnrichException(Exception, metaclass=ExceptionMeta):
    """
    A wrapper to enrich an existing exception with additional debugging information.

    This class wraps an original exception object and gathers extra data from its
    traceback such as:
      - module (the package-style module name, e.g. a.b.c),
      - function,
      - line number, and
      - the defining class (if present).

    Attributes of the original exception are available via delegation.
    """
    def __init__(self, original_exception: BaseException) -> None:
        # Instead of replacing the original exception, store it.
        self.original_exception = original_exception
        # Preserve the original message.
        super().__init__(str(original_exception))
        # Capture the traceback from the original exception.
        self.__traceback__ = original_exception.__traceback__
        # Gather extra information for enrichment.
        self._extra_info: Dict[str, Any] = self._gather_extra_info()

    def _gather_extra_info(self) -> Dict[str, Any]:
        tb = self.__traceback__
        module_name = None
        function_name = None
        lineno = None
        frame_obj = None
        if tb is None:
            # Fallback: use the current stack if no traceback is available.
            st = inspect.stack()
            frame_info = st[2] if len(st) > 2 else None
            frame_obj = frame_info.frame if frame_info else None
            mod = inspect.getmodule(frame_obj) if frame_obj else None
            module_name = mod.__name__ if mod and mod.__name__ else None
            function_name = frame_info.function if frame_info else None
            lineno = frame_info.lineno if frame_info else None
        else:
            tb_list = traceback.extract_tb(tb)
            if tb_list:
                last_frame = tb_list[-1]
                if last_frame.name == "<module>" and len(tb_list) > 1:
                    last_frame = tb_list[-2]
                # Try to get the corresponding frame object.
                inner_frames = inspect.getinnerframes(tb)
                frame_obj = inner_frames[-1].frame if inner_frames else None
                mod = inspect.getmodule(frame_obj) if frame_obj else None
                # Instead of returning a full path, use the module's __name__.
                module_name = mod.__name__ if mod and mod.__name__ else os.path.splitext(os.path.basename(last_frame.filename))[0]
                function_name = last_frame.name
                lineno = last_frame.lineno
            else:
                module_name = None
                function_name = None
                lineno = None

        # Attempt to get the defining class via inner frames.
        if tb is not None:
            inner_frames = inspect.getinnerframes(tb)
        else:
            inner_frames = inspect.stack()
        defining_class: Optional[str] = None
        if inner_frames:
            last_frame_obj = inner_frames[-1].frame
            if "self" in last_frame_obj.f_locals:
                defining_class = last_frame_obj.f_locals["self"].__class__.__name__
            elif "cls" in last_frame_obj.f_locals:
                defining_class = last_frame_obj.f_locals["cls"].__name__
        return {
            "module": module_name,
            "function": function_name,
            "line_no": lineno,
            "defining_class": defining_class
        }

    @property
    def module(self) -> Optional[str]:
        """The module name in package style (e.g. a.b.c) where the exception occurred."""
        return self._extra_info.get("module")

    @property
    def function(self) -> Optional[str]:
        """The function name where the exception occurred."""
        return self._extra_info.get("function")

    @property
    def line_no(self) -> Optional[int]:
        """The line number where the exception occurred."""
        return self._extra_info.get("line_no")

    @property
    def defining_class(self) -> Optional[str]:
        """The name of the class in which the exception occurred (if any)."""
        return self._extra_info.get("defining_class")

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute lookup to the original exception if the attribute
        is not found in this wrapper.
        """
        return getattr(self.original_exception, name)


if __name__ == "__main__":
    from shravs_utils.exceptions.base_exception import ShravsError

    def do_something():
        # Simulate an error.
        raise ShravsError("Something went wrong.", 4542, details={"key": "value"})

    try:
        do_something()
    except Exception as exc:
        wrapped = EnrichException(exc)
        print("error_code:", getattr(wrapped, "error_code", None))
        print("Original Message:", wrapped)
        print("Module:", wrapped.module)
        print("Function:", wrapped.function)
        print("Line No:", wrapped.line_no)
        print("Defining Class:", wrapped.defining_class)
        # Demonstrating delegation: original attributes of the underlying exception are accessible.
        print("Original args:", wrapped.args)
