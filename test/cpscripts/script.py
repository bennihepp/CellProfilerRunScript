import numpy as np
import scipy.ndimage as nd

from cellprofiler import cpscript

obj = cpscript.objects['Nuclei']
print 'obj:', obj
img = cpscript.images['DNA']
print 'img:', img

obj_labels = obj.segmented

py_img_output = np.sum(img.pixel_data[obj_labels > 0])

nobjects = np.int32(np.max(obj_labels))
lindexes = np.arange(nobjects, dtype=np.int32)+1

py_img_obj_output = nd.sum(img.pixel_data, obj_labels, lindexes)

py_obj_output = nd.sum(obj.segmented > 0, obj_labels, lindexes)
