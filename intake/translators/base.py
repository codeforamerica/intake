

class AttributeTranslatorBase:

    def __init__(self, config, att_object_extractor=None):
        self.att_object_extractor = att_object_extractor
        self.config = config

    def get_attribute_data(self, data, extractor):
        if self.att_object_extractor:
            attributes = getattr(data, self.att_object_extractor)
            return attributes.get(extractor, '')
        else:
            return data.get(extractor, '')


    def __call__(self, data):
        result = {}
        for key, extractor in self.config.items():
            if hasattr(extractor, '__call__'):
                result[key] = extractor(data)
            else:
                result[key] = self.get_attribute_data(
                    data, extractor)
        return result