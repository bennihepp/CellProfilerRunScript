CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:11047

LoadImages:[module_num:1|svn_version:\'11031\'|variable_revision_number:11|show_window:False|notes:\x5B\x5D]
    File type to be loaded:individual images
    File selection method:Text-Regular expressions
    Number of images in each group?:3
    Type the text that the excluded images have in common:Do not use
    Analyze all subfolders within the selected folder?:None
    Input image file location:Default Input Folder\x7CNone
    Check image sets for missing or duplicate files?:Yes
    Group images by metadata?:No
    Exclude certain files?:No
    Specify metadata fields to group by:
    Select subfolders to analyze:
    Image count:1
    Text that these images have in common (case-sensitive):bfa--W00028--P00001.+--dapi.tif
    Position of this image in each group:1
    Extract metadata from where?:None
    Regular expression that finds metadata in the file name:^(?P<Plate>.*)_(?P<Well>\x5BA-P\x5D\x5B0-9\x5D{2})_s(?P<Site>\x5B0-9\x5D)
    Type the regular expression that finds metadata in the subfolder path:.*\x5B\\\\/\x5D(?P<Date>.*)\x5B\\\\/\x5D(?P<Run>.*)$
    Channel count:1
    Group the movie frames?:No
    Grouping method:Interleaved
    Number of channels per group:3
    Load the input as images or objects?:Images
    Name this loaded image:DNA
    Name this loaded object:Nuclei
    Retain outlines of loaded objects?:No
    Name the outline image:LoadedImageOutlines
    Channel number:1
    Rescale intensities?:Yes

IdentifyPrimaryObjects:[module_num:2|svn_version:\'11047\'|variable_revision_number:8|show_window:False|notes:\x5B\x5D]
    Select the input image:DNA
    Name the primary objects to be identified:Nuclei
    Typical diameter of objects, in pixel units (Min,Max):10,40
    Discard objects outside the diameter range?:Yes
    Try to merge too small objects with nearby larger objects?:No
    Discard objects touching the border of the image?:Yes
    Select the thresholding method:Otsu Global
    Threshold correction factor:1
    Lower and upper bounds on threshold:0.000000,1.000000
    Approximate fraction of image covered by objects?:0.01
    Method to distinguish clumped objects:Intensity
    Method to draw dividing lines between clumped objects:Intensity
    Size of smoothing filter:10
    Suppress local maxima that are closer than this minimum allowed distance:7
    Speed up by using lower-resolution image to find local maxima?:Yes
    Name the outline image:PrimaryOutlines
    Fill holes in identified objects?:Yes
    Automatically calculate size of smoothing filter?:Yes
    Automatically calculate minimum allowed distance between local maxima?:Yes
    Manual threshold:0.0
    Select binary image:None
    Retain outlines of the identified objects?:No
    Automatically calculate the threshold using the Otsu method?:Yes
    Enter Laplacian of Gaussian threshold:0.5
    Two-class or three-class thresholding?:Two classes
    Minimize the weighted variance or the entropy?:Weighted variance
    Assign pixels in the middle intensity class to the foreground or the background?:Foreground
    Automatically calculate the size of objects for the Laplacian of Gaussian filter?:Yes
    Enter LoG filter diameter:5
    Handling of objects if excessive number of objects identified:Continue
    Maximum number of objects:500
    Select the measurement to threshold with:None

MeasureImageIntensity:[module_num:3|svn_version:\'11025\'|variable_revision_number:2|show_window:False|notes:\x5B\x5D]
    Select the image to measure:DNA
    Measure the intensity only from areas enclosed by objects?:No
    Select the input objects:None

MeasureObjectIntensity:[module_num:4|svn_version:\'11025\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    Hidden:1
    Select an image to measure:DNA
    Select objects to measure:Nuclei

RunScript:[module_num:5|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\x5D]
    Input image count:1
    input object count:1
    Input measurement count:0
    Input constant count:0
    Output image count:0
    Output object count:0
    Output measurement count:3
    Run script in debug mode?:No
    Name of the script file directory:Elsewhere...\x7C/home/hepp/hepp/code/CellProfilerRunScript/test/cpscripts
    Name of the script file:script.py
    Script to run:# Loaded on\x3A 01/23/12-15\x3A54\x3A53\nimport numpy as np\nimport scipy.ndimage as nd\n\nfrom cellprofiler import cpscript\n\nobj = cpscript.objects\x5B\'Nuclei\'\x5D\nprint \'obj\x3A\', obj\nimg = cpscript.images\x5B\'DNA\'\x5D\nprint \'img\x3A\', img\n\nobj_labels = obj.segmented\n\npy_img_output = np.sum(img.pixel_data\x5Bobj_labels > 0\x5D)\n\nnobjects = np.int32(np.max(obj_labels))\nlindexes = np.arange(nobjects, dtype=np.int32)+1\n\npy_img_obj_output = nd.sum(img.pixel_data, obj_labels, lindexes)\n\npy_obj_output = nd.sum(obj.segmented > 0, obj_labels, lindexes)\n
    Select an input image to use:DNA
    Select an input object to use:Nuclei
    Is the measurement related to objects?:No
    Is the measurement performed on an image?:Yes
    Object name:Nuclei
    Image name:DNA
    Choose the type of the measurement:float
    Measurement category:RunScript
    Measurement name:ImageMeasurement
    Name for the measurement-variable in Python:py_img_output
    Is the measurement related to objects?:Yes
    Is the measurement performed on an image?:Yes
    Object name:Nuclei
    Image name:DNA
    Choose the type of the measurement:float
    Measurement category:RunScript
    Measurement name:ImageObjectMeasurement
    Name for the measurement-variable in Python:py_img_obj_output
    Is the measurement related to objects?:Yes
    Is the measurement performed on an image?:No
    Object name:Nuclei
    Image name:DNA
    Choose the type of the measurement:float
    Measurement category:RunScript
    Measurement name:ObjectMeasurement
    Name for the measurement-variable in Python:py_obj_output

CalculateMath:[module_num:6|svn_version:\'11025\'|variable_revision_number:1|show_window:False|notes:\x5B\x5D]
    Name the output measurement:Measurement
    Operation:Multiply
    Select the first operand measurement type:Object
    Select the first operand objects:Nuclei
    Select the first operand measurement:RunScript_ImageObjectMeasurement_DNA
    Multiply the above operand by:1
    Raise the power of above operand by:1
    Select the second operand measurement type:Object
    Select the second operand objects:Nuclei
    Select the second operand measurement:RunScript_ObjectMeasurement
    Multiply the above operand by:1
    Raise the power of above operand by:1
    Take log10 of result?:No
    Multiply the result by:1
    Raise the power of result by:1

RunScript:[module_num:7|svn_version:\'Unknown\'|variable_revision_number:1|show_window:False|notes:\x5B\x5D]
    Input image count:0
    input object count:0
    Input measurement count:3
    Input constant count:0
    Output image count:0
    Output object count:0
    Output measurement count:0
    Run script in debug mode?:No
    Name of the script file directory:Elsewhere...\x7C/home/hepp/hepp/code/CellProfilerRunScript/test/cpscripts
    Name of the script file:script2.py
    Script to run:# Loaded on\x3A 01/23/12-15\x3A54\x3A56\nfrom cellprofiler import cpscript\n\nimg_meas = cpscript.measurements\x5B\'Image\', \'RunScript_ImageMeasurement_DNA\'\x5D\nprint \'img_meas\x3A\', img_meas\n\nimg_obj_meas = cpscript.measurements\x5B\'Nuclei_RunScript_ImageObjectMeasurement_DNA\'\x5D\nprint \'img_obj_meas\x3A\', img_obj_meas\n\nobj_meas = cpscript.measurements\x5B\'Nuclei\', \'RunScript_ObjectMeasurement\'\x5D\nprint \'obj_meas\x3A\', obj_meas\n
    Use an image measurement?:No
    Object name:Nuclei
    Select an input measurement to use:RunScript_ObjectMeasurement
    Use an image measurement?:No
    Object name:Nuclei
    Select an input measurement to use:RunScript_ImageObjectMeasurement_DNA
    Use an image measurement?:Yes
    Object name:Do not use
    Select an input measurement to use:RunScript_ImageMeasurement_DNA
