import importlib


def load_attribute(attribute_path):
    module, attr = attribute_path.split(':')
    module = importlib.import_module(module)
    return getattr(module, attr)
