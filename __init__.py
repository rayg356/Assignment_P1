from .calculator import *  # noqa
except ImportError:
    # Allows running tests when package is executed directly from source tree.
    from calculator import *  # noqa