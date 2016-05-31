

class AttributeTranslatorBase:

    def __init__(self, config):
        self.config = config

    def __call__(self, data):
        result = {}
        for key, extractor in self.config.items():
            if hasattr(extractor, '__call__'):
                result[key] = extractor(data)
            else:
                result[key] = data.get(extractor, '')
        return result