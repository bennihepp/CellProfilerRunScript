try:
    from cellprofiler.measurement import IMAGE
except:
    IMAGE = 'Image'


class __Image__(object):
    pixel_data = None


class __Objects__(object):
    segmented = None


class __ImageWrapper__(dict):
    pass


class __ObjectWrapper__(dict):
    pass


class __MeasurementWrapper__(dict):
    def __setitem__(self, key, value):
        if hasattr(key, '__iter__'):
            key = '_'.join(key)
        super(__MeasurementWrapper__, self).__setitem__(key, value)
    def __getitem__(self, key):
        if hasattr(key, '__iter__'):
            key = '_'.join(key)
        return super(__MeasurementWrapper__, self).__getitem__(key)


class __ConstantWrapper__(dict):
    pass

def __reset__():
    global images, objects, measurements, constants
    images = __ImageWrapper__()
    objects = __ObjectWrapper__()
    measurements = __MeasurementWrapper__()
    constants = __ConstantWrapper__()

__reset__()
