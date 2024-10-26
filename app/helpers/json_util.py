import json
from constants import CLASS_NAMES

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        for class_name in CLASS_NAMES:
            if hasattr(obj, '__class__') and obj.__class__.__name__ == class_name:
                return vars(obj)
        return super().default(obj)
