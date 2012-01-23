from cellprofiler import cpscript

img_meas = cpscript.measurements['Image', 'RunScript_ImageMeasurement_DNA']
print 'img_meas:', img_meas

img_obj_meas = cpscript.measurements['Nuclei_RunScript_ImageObjectMeasurement_DNA']
print 'img_obj_meas:', img_obj_meas

obj_meas = cpscript.measurements['Nuclei', 'RunScript_ObjectMeasurement']
print 'obj_meas:', obj_meas
