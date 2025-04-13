import abc
import sys
import traceback
import inspect

try:
    from rich.console import Console
    from rich.traceback import Traceback
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Helper functions to compute property values:
def get_tb(instance):
    return "".join(traceback.format_tb(instance.__traceback__) if instance.__traceback__ else "")

def get_context(instance):
    return instance.__context__

def get_cause(instance):
    return instance.__cause__

class ExceptionMeta(abc.ABCMeta):
    """
    An abstract metaclass for custom exceptions.
    It injects properties for traceback (tb), context, and cause into any exception class that uses it.
    These properties are computed on demand so that when the exception is raised,
    they reflect the current exception state.

    Additionally, the metaclass stores extra keyword arguments as 'kwargs' and positional arguments as:
      - 'details': additional information (always a dict), and
      - 'objects': extra positional arguments excluding those corresponding to fixed parameters
        defined in the child class (e.g. the message, error_code, etc.),
    so that information already captured by the child class is not duplicated.
    """
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Inject dynamic properties if they are not already defined.
        if 'tb' not in namespace:
            namespace['tb'] = property(get_tb)
        if 'context' not in namespace:
            namespace['context'] = property(get_context)
        if 'cause' not in namespace:
            namespace['cause'] = property(get_cause)
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        # Ensure details is always a dict.
        details = kwargs.pop('details', {})
        if not isinstance(details, dict):
            details = {'value': details}
        instance.details = details
        # Store any leftover keyword arguments.
        instance.kwargs = kwargs

        # Use inspect to determine how many fixed positional parameters (excluding self) the child class defines.
        sig = inspect.signature(cls.__init__)
        fixed_params = [
            p for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        # Exclude "self"
        fixed_count = len(fixed_params) - 1 if len(fixed_params) >= 1 else 0

        # Set additional objects to only those beyond the fixed parameters.
        instance.objects = args[fixed_count:] if len(args) > fixed_count else ()
        return instance

