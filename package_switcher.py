import importlib
import importlib.abc
import importlib.util


class PackageAliasFinder(importlib.abc.MetaPathFinder):
    """
    Intercepts the top-level import for an aliased package and redirects it
    to a target package. Submodules are deliberately ignored so Python's native
    PathFinder can naturally resolve them using the parent's directory.
    """

    def __init__(self, alias_name, target_name):
        self.alias_name = alias_name
        self.target_name = target_name

    def find_spec(self, fullname, path, target=None):
        # ONLY intercept the exact top-level package name
        if fullname == self.alias_name:
            spec = importlib.util.find_spec(self.target_name)
            if spec is None:
                raise ModuleNotFoundError(f"Target package '{self.target_name}' is not installed.")
            # Disguise the spec name
            spec.name = fullname
            # Disguise the loader
            if hasattr(spec, "loader") and spec.loader is not None:
                try:
                    spec.loader.name = fullname
                except AttributeError:
                    if hasattr(spec, "origin") and spec.origin:
                        spec.loader = spec.loader.__class__(fullname, spec.origin)
            return spec
        # For submodules (like music21.common.deprecated) return None
        return None
