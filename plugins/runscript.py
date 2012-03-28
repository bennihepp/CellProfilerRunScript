'''<b>RunScript</b> - an easy way to write scripts for CellProfiler
<hr>
This module allows you to write small python scripts that are run as part
of the CellProfiler pipeline.
'''
#################################
#
# Imports from useful Python libraries
#
#################################

import os
import sys
import ast
import datetime
import tempfile

import numpy as np

#################################
#
# Imports from CellProfiler
#
# The package aliases are the standard ones we use
# throughout the code.
#
##################################

#import cellprofiler
import cellprofiler.cpimage as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.measurements as cpmeas
import cellprofiler.objects as cpo
import cellprofiler.settings as cps
from cellprofiler.preferences import \
     DEFAULT_INPUT_FOLDER_NAME, DEFAULT_OUTPUT_FOLDER_NAME, NO_FOLDER_NAME, \
     ABSOLUTE_FOLDER_NAME

DIR_ALL = [DEFAULT_INPUT_FOLDER_NAME, DEFAULT_OUTPUT_FOLDER_NAME,
           NO_FOLDER_NAME, ABSOLUTE_FOLDER_NAME]

WC_OBJECTS = 'CellProfiler Objects'
WC_FILTERED_OBJECTS = 'Filtered segmentation'
WC_UNFILTERED_OBJECTS = 'Unfiltered segmentation'
WC_SMALLREMOVED_OBJECTS = 'Segmentation with small objects removed'
WD_NO = "No"
WD_PDB = "Use pdb"
WD_WINGDB = "Use wingdbstub"
WD_RPDB2 = "Use rpdb2"
WT_FLOAT = "Float"
WT_INT = "Integer"
WT_LIST = "List"
WT_DICT = "Dictionary"
WT_NPARRAY = "Numpy float array"
WT_FLOATDICT = "Dictionary with float values"
WT_STRING = "String"

SETTINGS_OFFSET = 4

MT_TYPES = [
    cpmeas.COLTYPE_FLOAT,
    cpmeas.COLTYPE_INTEGER,
]


class RunScript(cpm.CPModule):

    module_name = "RunScript"
    category = "Other"
    variable_revision_number = 1

    def create_settings(self):

        # add choice for debugging modes
        self.wants_debug_mode = cps.Choice("Run script in debug mode?",
                                           [WD_NO, WD_PDB,
                                            WD_WINGDB, WD_RPDB2])
        # add containers for groups
        self.input_image_groups = []
        self.input_object_groups = []
        self.input_measurement_groups = []
        self.input_constant_groups = []
        self.output_image_groups = []
        self.output_object_groups = []
        self.output_measurement_groups = []
        # add hidden counts for groups
        self.input_image_count = cps.HiddenCount(
            self.input_image_groups, 'Input image count')
        self.input_object_count = cps.HiddenCount(
            self.input_object_groups, 'input object count')
        self.input_measurement_count = cps.HiddenCount(
            self.input_measurement_groups, 'Input measurement count')
        self.input_constant_count = cps.HiddenCount(
            self.input_constant_groups, 'Input constant count')
        self.output_image_count = cps.HiddenCount(
            self.output_image_groups, 'Output image count')
        self.output_object_count = cps.HiddenCount(
            self.output_object_groups, 'Output object count')
        self.output_measurement_count = cps.HiddenCount(
            self.output_measurement_groups, 'Output measurement count')
        # add buttons for adding inputs and outputs
        self.add_input_image = cps.DoSomething(
            "", "Add another input image",
            self.add_input_image_cb)
        self.add_input_object = cps.DoSomething(
            "", "Add another input object",
            self.add_input_object_cb)
        self.add_input_measurement = cps.DoSomething(
            "", "Add another input measurement",
            self.add_input_measurement_cb)
        self.add_input_constant = cps.DoSomething(
            "", "Add another input constant",
            self.add_input_constant_cb)
        self.input_output_divider = cps.Divider()
        self.add_output_image = cps.DoSomething(
            "", "Add another output image",
            self.add_output_image_cb)
        self.add_output_object = cps.DoSomething(
            "", "Add another output object",
            self.add_output_object_cb)
        self.add_output_measurement = cps.DoSomething(
            "", "Add another output measurement",
            self.add_output_measurement_cb)
        # add directory input box for loading script
        self.script_dir = cps.DirectoryPath(
            "Name of the script file directory",
            dir_choices=DIR_ALL,
            allow_metadata=False
        )
        # add file input box for loading script
        self.script_file = cps.FilenameText(
            "Name of the script file",
            "None",
            exts=[("Script file (*.py)", "*.py"), ("Any file (*)", "*")]
        )
        # add a button to load the script
        self.script_load_btn = cps.DoSomething(
            "", "Load contents of the script file",
            self.load_script_file_cb
        )
        # add text field for entering script ...
        # ... create keyword arguments for text field constructor
        text_kwargs = {'doc': "Enter the python script to be run",
                       'multiline': True}
        # ... check if we're able to change the size of a
        #     text field (custom patch)
        if getattr(cps.Text, '__change_size_support__', False):
            text_kwargs['size'] = (600, 400)
        # ... create the text field for the script
        self.script_text = cps.Text(
            "Script to run",
            "results = 5",
            **text_kwargs
        )

        #
        # for each input and output type __settings contains ...
        #   1. the button for adding a new input/output,
        #   2. the list of corresponding inputs/outputs (SettingsGroup),
        #   3. attributes of the SettingsGroup to return from settings(),
        #   4. attributes of the SettingsGroup to return from
        #      visible_settings(),
        #   5. the callback for adding a new input/output
        #
        self.__setting_descr = (
            (
                self.add_input_image, self.input_image_groups,
                ("image",),
                ("divider", "image", "remover"),
                self.add_input_image_cb
            ),
            (
                self.add_input_object, self.input_object_groups,
                ("objects",),
                ("divider", "objects", "remover"),
                self.add_input_object_cb
            ),
            (
                self.add_input_measurement, self.input_measurement_groups,
                ("wants_image", "use_object_name", "measurement"),
                ("divider", "wants_image", "use_object_name",
                 "measurement", "remover"),
                self.add_input_measurement_cb
            ),
            (
                self.add_input_constant, self.input_constant_groups,
                ("constant", "type_choice"),
                ("divider", "constant", "type_choice", "remover"),
                self.add_input_constant_cb
            ),
            (
                self.add_output_image, self.output_image_groups,
                ("image_name", "py_name"),
                ("divider", "image_name", "py_name", "remover"),
                self.add_output_image_cb
            ),
            (
                self.add_output_object, self.output_object_groups,
                ("objects_name", "py_name"),
                ("divider", "objects_name", "py_name", "remover"),
                self.add_output_object_cb
            ),
            (
                self.add_output_measurement, self.output_measurement_groups,
                ("relate_to_object", "on_image", "object", "image",
                 "type_choice", "measurement_category", "measurement_name",
                 "py_name"),
                ("divider", "relate_to_object", "on_image", "object", "image",
                 "type_choice", "measurement_category", "measurement_name",
                 "py_name", "remover"),
                self.add_output_measurement_cb
            ),
        )

    def settings(self):
        result = [
            self.input_image_count,
            self.input_object_count,
            self.input_measurement_count,
            self.input_constant_count,
            self.output_image_count,
            self.output_object_count,
            self.output_measurement_count,
        ]
        result += [self.wants_debug_mode]
        result += [self.script_dir]
        result += [self.script_file]
        result += [self.script_text]
        for group_btn, groups, attr_names, visible_attr_names, add_cb in \
            self.__setting_descr:
            for group in groups:
                for attr_name in attr_names:
                    result += [getattr(group, attr_name)]
        return result

    def visible_settings(self):
        result = [self.wants_debug_mode]
        for group_btn, groups, attr_names, visible_attr_names, add_cb in \
            self.__setting_descr:
            for group in groups:
                skip_object = False
                skip_relate_object = True
                skip_image = False
                for attr_name in visible_attr_names:
                    setting = getattr(group, attr_name)
                    if attr_name == 'wants_image' \
                       and setting.value:
                        skip_object = True
                    if attr_name == 'relate_to_object' \
                       and setting.value:
                        skip_relate_object = False
                        skip_image = True
                    if attr_name == 'on_image':
                        if skip_relate_object and not setting.value:
                            # make sure that at least an image or an object
                            # is related to a measurement
                            setting.set_value(True)
                        if setting.value:
                            skip_image = False
                    if attr_name == 'use_object_name':
                        pass
                    skip = (attr_name == 'image' and skip_image) \
                        or (attr_name == 'object' and skip_relate_object) \
                        or (attr_name == 'use_object_name' and skip_object)
                    if not skip:
                        result += [setting]
            result += [group_btn]
        result += [cps.Divider()]
        result += [self.script_dir]
        result += [self.script_file]
        result += [self.script_load_btn]
        result += [self.script_text]
        return result

    def prepare_settings(self, setting_values):
        '''Prepare the module to receive the settings

        setting_values - one string per setting to be initialized

        Adjust the number of input and output objects to
        match the number indicated in the settings.
        '''
        counts = [int(x) for x in setting_values[:7]]
        groups = [x[1] for x in self.__setting_descr]
        callbacks = [x[4] for x in self.__setting_descr]
        for count, group, add_cb in zip(counts, groups, callbacks):
            del group[count:]
            while len(group) < count:
                add_cb()

    def load_script_file_cb(self):
        # load the script
        dir_name = self.script_dir.get_absolute_path()
        script_name = self.script_file.value
        path = os.path.join(dir_name, script_name)
        print 'Loading content from script file:', path
        with open(path) as f:
            lines = f.readlines()
        lines.insert(0, '# Loaded on: %s\n' \
                     % datetime.datetime.now().strftime('%D-%T'))
        source = ''.join(lines)
        self.script_text.value = source

    def add_input_image_cb(self):
        '''Add an image to the input_image_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('image', cps.ImageNameSubscriber(
            "Select an input image to use", None,
            doc="""Select an image you want to use as input in your script"""
        ))
        group.append('remover',
            cps.RemoveSettingButton(
                "", "Remove this image", self.input_image_groups, group)
        )
        self.input_image_groups.append(group)

    def add_input_object_cb(self):
        '''Add an object to the input_object_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('objects', cps.ObjectNameSubscriber(
            "Select an input object to use", None,
            doc="""Select an object you want to use as input in your script"""
        ))
        group.append(
            "remover",
            cps.RemoveSettingButton(
                "", "Remove this object", self.input_object_groups, group)
        )
        self.input_object_groups.append(group)

    def add_input_measurement_cb(self):
        '''Add a measurement to the input_measurement_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        wants_image_measurement = cps.Binary("Use an image measurement?", True)
        group.append('wants_image', wants_image_measurement)
        use_object_name = cps.ObjectNameSubscriber("Object name")
        group.append('use_object_name', use_object_name)

        def object_fn():
            if wants_image_measurement.value:
                return cpmeas.IMAGE
            else:
                return use_object_name.value
        group.append('measurement', cps.Measurement(
            "Select an input measurement to use", object_fn,
            doc="""Select an image you want to use as input in your script"""
        ))
        group.append("remover",
                     cps.RemoveSettingButton(
                        "", "Remove this measurement",
                        self.input_measurement_groups, group)
        )
        self.input_measurement_groups.append(group)

    def add_input_constant_cb(self):
        '''Add a constant to the input_constant_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('constant', cps.Text(
            "Enter the constant input to use",
            "1.0",
            doc="""Enter a constant you want to use as input in your script"""
        ))
        group.append('type_choice',
                     cps.Choice("Choose the type of the constant",
                                [WT_FLOAT,
                                 WT_INT,
                                 WT_LIST,
                                 WT_DICT,
                                 WT_NPARRAY,
                                 WT_FLOATDICT,
                                 WT_STRING]
        ))
        group.append('py_name', cps.Text(
            "Name for the constant-variable in Python",
            "cp_constant_in",
            doc='Select the name of the variable that can be' \
                ' used to access the constant through cpscript'
        ))
        group.append(
            "remover",
            cps.RemoveSettingButton(
               "", "Remove this constant", self.input_constant_groups, group)
        )
        self.input_constant_groups.append(group)

    def add_output_image_cb(self):
        '''Add an image to the output_image_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('image_name', cps.ImageNameProvider(
            "Output image name",
            "OutputImage"
        ))
        group.append('py_name', cps.Text(
            "Name for the image-variable in Python",
            "cp_image_out",
            doc="""Select the name of the variable that """
                """can be used to access the image"""
        ))
        group.append(
            "remover",
            cps.RemoveSettingButton(
               "", "Remove this image", self.output_image_groups, group)
        )
        self.output_image_groups.append(group)

    def add_output_object_cb(self):
        '''Add an object to the output_object_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('objects_name', cps.ObjectNameProvider(
            "Name the output objects",
            "OutputObject"
        ))
        group.append('py_name', cps.Text(
            "Name for the object-variable in Python",
            "cp_object_out",
            doc="""Select the name of the variable that """
                """can be used to access the object"""
        ))
        group.append(
            "remover",
            cps.RemoveSettingButton(
               "", "Remove this object", self.output_object_groups, group)
        )
        self.output_object_groups.append(group)

    def add_output_measurement_cb(self):
        '''Add a measurement to output_measurement_groups collection'''
        group = cps.SettingsGroup()
        group.append("divider", cps.Divider())
        group.append('relate_to_object', cps.Binary(
            "Is the measurement related to objects?", False
        ))
        group.append('on_image', cps.Binary(
            "Is the measurement performed on an image?", False
        ))
        group.append('object', cps.ObjectNameSubscriber(
            "Object name"
        ))
        group.append('image', cps.ImageNameSubscriber(
            "Image name", None
        ))
        group.append('measurement_category', cps.Text(
            "Measurement category",
            "RunScript"
        ))
        group.append('type_choice',
                     cps.Choice("Choose the type of the measurement",
                                MT_TYPES
        ))
        group.append('measurement_name', cps.Text(
            "Measurement name",
            "OutputMeasurement"
        ))
        group.append('py_name', cps.Text(
            "Name for the measurement-variable in Python",
            "cp_measurement_out",
            doc="""Select the name of the variable that """
                """can be used to access the measurement"""
        ))
        group.append(
            "remover",
            cps.RemoveSettingButton(
               "", "Remove this measurement",
               self.output_measurement_groups, group)
        )
        self.output_measurement_groups.append(group)

    def get_measurement_columns(self, pipeline):
        '''Return column definitions for measurements made by this module'''
        columns = []
        for group in self.output_measurement_groups:
            object_name = (cpmeas.IMAGE if not group.relate_to_object.value
                           else group.object.value)
            img = None
            if object_name == cpmeas.IMAGE or group.on_image.value:
                img = group.image.value
            if img is None:
                columns.append((
                    object_name,
                    '%s_%s' % (group.measurement_category.value,
                               group.measurement_name.value),
                    group.type_choice.value
                ))
            else:
                columns.append((
                    object_name,
                    '%s_%s_%s' % (group.measurement_category.value,
                               group.measurement_name.value,
                               img),
                    group.type_choice.value
                ))
        return columns

    def get_categories(self, pipeline, object_name):
        categories = []
        for group in self.output_measurement_groups:
            group_object_name = (
                cpmeas.IMAGE if not group.relate_to_object.value
                             else group.object.value
            )
            if object_name == group_object_name:
                categories.append(group.measurement_category.value)
        return categories

    def get_measurements(self, pipeline, object_name, category):
        measurements = []
        for group in self.output_measurement_groups:
            group_object_name = (
                cpmeas.IMAGE if not group.relate_to_object.value
                             else group.object.value
            )
            group_category = group.measurement_category.value
            if object_name == group_object_name \
               and category == group_category:
                measurements.append(group.measurement_name.value)
        return measurements

    def get_measurement_images(self, pipeline, object_name, \
                               category, measurement):
        images = []
        for group in self.output_measurement_groups:
            group_object_name = (
                cpmeas.IMAGE if not group.relate_to_object.value
                             else group.object.value
            )
            group_category = group.measurement_category.value
            group_name = group.measurement_name.value
            group_image = group.image.value
            img = None
            if group_object_name == cpmeas.IMAGE or group.on_image.value:
                img = group.image.value
            if object_name == group_object_name \
               and img is not None \
               and category == group_category \
               and measurement == group_name:
                images.append(group_image)
        return images

    #def get_measurement_objects(self, pipeline, object_name, \
                               #category, measurement):
        #objects = []
        #for group in self.output_measurement_groups:
            #group_object_name = (cpmeas.IMAGE if group.wants_image.value
                                 #else group.use_object_name.value)
            #group_category = group.measurement_category.value
            #group_name = group.measurement_name.value
            #group_image = group.image.value
            #if not group.wants_image.value \
               #and object_name == group_object_name \
               #and category == group_category \
               #and measurement == group_name:
                #objects.append(group_object_name)
        #return objects

    @staticmethod
    def convert_to_type(constant, type_choice):
        if type_choice == WT_FLOAT:
            return float(constant)
        elif type_choice == WT_INT:
            return int(constant)
        elif type_choice == WT_LIST:
            return constant.split(',')
        elif type_choice == WT_DICT:
            return dict([x.split(':') for x in constant.split(',')])
        elif type_choice == WT_NPARRAY:
            return np.array([float(x) for x in constant.split(',')])
        elif type_choice == WT_FLOATDICT:
            l = RunScript.convert_to_type(constant, WT_LIST)
            return dict([(k, float(v)) for k, v in l])

    class __ImageWrapper__(object):
        def __init__(self, workspace):
            self.__workspace = workspace

        def __getitem__(self, name):
            image = self.__workspace.image_set.get_image(name)
            return image

    class __ObjectWrapper__(object):
        def __init__(self, workspace):
            self.__workspace = workspace

        def __getitem__(self, name):
            objects = self.__workspace.object_set.get_objects(name)
            return objects

    class __MeasurementWrapper__(object):
        def __init__(self, workspace):
            self.__workspace = workspace

        def __getitem__(self, key):
            if hasattr(key, '__iter__'):
                parts = tuple(key)
            else:
                parts = key.split('_')
            if parts[0] == 'Image':
                measurement = self.__workspace.measurements \
                    .get_current_image_measurement('_'.join(parts[1:]))
            else:
                measurement = self.__workspace.measurements \
                    .get_current_measurement(parts[0], '_'.join(parts[1:]))
            return measurement

    class __ConstantWrapper__(object):
        def __init__(self, runscript_module):
            self.__runscript = runscript_module

        def __getitem__(self, name):
            for group in self.__runscript.input_constant_groups:
                if group.py_name.value == name:
                    constant = group.constant.value
                    type_choice = group.type_choice.value
                    return RunScript.convert_to_type(constant, type_choice)
            raise KeyError('No such constant has been declared:', name)

    # parse the AST tree to find input images, objects and measurements
    def find_inputs(self, tree):
        input_image_list = []
        input_object_list = []
        input_measurement_list = []
        input_constant_list = []
        name_to_list_map = {
            (ast.Load, 'images'): input_image_list,
            (ast.Load, 'objects'): input_object_list,
            (ast.Load, 'measurements'): input_measurement_list,
            (ast.Load, 'constants'): input_constant_list,
        }
        # get a list of AST nodes ...
        nodes = list(ast.walk(tree))

        def cmp_nodes(x, y):
            if 'lineno' in x._attributes and 'lineno' in y._attributes:
                return cmp(x.lineno, y.lineno)
            elif 'lineno' in x._attributes:
                return cmp(x.lineno, 0)
            elif 'lineno' in y._attributes:
                return cmp(0, y.lineno)
            else:
                return 0
        # and sort the by line number
        nodes.sort(cmp=cmp_nodes)
        # scan the nodes ...
        cpscript_names = []
        for node in nodes:
            # check for imports of cellprofiler.cpscript
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'cellprofiler.cpscript':
                        name = alias.name if alias.asname is None \
                            else alias.asname
                        cpscript_names.append(name)
            if isinstance(node, ast.ImportFrom):
                if node.module == 'cellprofiler':
                    for alias in node.names:
                        if alias.name == 'cpscript':
                            name = alias.name if alias.asname is None \
                                else alias.asname
                            cpscript_names.append(name)
            # check for access to cpscript attributes
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Attribute) \
                   and (type(node.ctx), node.value.attr) in name_to_list_map \
                   and isinstance(node.value.value, ast.Name) \
                   and node.value.value.id in cpscript_names:
                    cpscript_name = node.value.value.id
                    name = node.value.attr
                    sl = node.slice
                    if isinstance(sl, ast.Index):
                        value = ast.literal_eval(sl.value)
                        if hasattr(value, '__iter__'):
                            value = '_'.join(value)
                        name_to_list_map[type(node.ctx), name].append(value)
                    else:
                        raise KeyError(
                            'The key for indexing %s.%s may not be a slice' \
                            % (cpscript_name, name)
                        )
        return (input_image_list, input_object_list,
                input_measurement_list, input_constant_list)

    def prepare_run(self, *args):
        #import cellprofiler.utilities.get_revision
        #version = cellprofiler.utilities.get_revision.get_revision \
            #.get_revision()
        ## TODO: I don't know at what version the calling conventions for
        ##       prepare_run did change.
        #if version < 11429:
            #pipeline, image_set_list, frame = args
        #else:
            #workspace = args[0]

        source = self.script_text.value
        # maybe add some debugging stuff
        if self.wants_debug_mode.value == WD_PDB:
            source = u"import pdb\npdb.set_trace()\n\n" + source
        elif self.wants_debug_mode == WD_WINGDB:
            source = u"import wingdbstub\nwingdbstub.debugger.Break()\n\n" \
                     + source
        elif self.wants_debug_mode == WD_RPDB2:
            source = u"import rpdb2\nrpdb2.set_trace()\n\n" + source
        # TODO: only print when not in batch mode
        #print 'Script source:', source
        # create a temporary file with the script source for debugging
        tmpfile_handle, tmpfile_path = tempfile.mkstemp(
            suffix='.py', prefix='CPRunScript_')
        tmpfile = os.fdopen(tmpfile_handle, 'w')
        tmpfile.write(source)
        tmpfile.close()
        # keep path of temporary file for deletion in post_run()
        self.__tmpfile_path = tmpfile_path
        # compile the script source into an AST tree
        asttree = compile(source, tmpfile_path, 'exec', ast.PyCF_ONLY_AST)
        # compile the AST tree into a code object
        self.__codeobj = compile(asttree, tmpfile_path, 'exec')
        try:
            # parse the AST tree to find all images, objects and measurements
            # that the script is using as input
            input_images, input_objects, input_measurements, input_constants \
                = self.find_inputs(asttree)
        except KeyError as err:
            raise cps.ValidationError(err.message, self.script_text)
        # this is just a sanity check to see if any inputs used in the script
        # where not declared in the cellprofiler settings ..
        # ... for images
        input_images_copy = list(input_images)
        for group in self.input_image_groups:
            if group.image.value in input_images_copy:
                input_images_copy.remove(group.image.value)
            else:
                print 'WARNING: Input image %s has been declared but is' \
                      ' never used in the script' % group.image.value
        if len(input_images_copy) > 0:
            raise cps.ValidationError(
                'The script uses images that have not been declared in the' \
                ' settings: %s' % (', '.join(input_images_copy),),
                self.input_image_groups
            )
        # ... for objects
        input_objects_copy = list(input_objects)
        for group in self.input_object_groups:
            if group.objects.value in input_objects_copy:
                input_objects_copy.remove(group.objects.value)
            else:
                print 'WARNING: Input object %s has been declared but is' \
                      ' never used in the script' % group.objects.value
        if len(input_objects_copy) > 0:
            raise cps.ValidationError(
                'The script uses objects that have not been declared in the' \
                ' settings: %s' % ', '.join(input_objects_copy),
                self.input_object_groups
            )
        # ... for measurements
        input_measurements_copy = list(input_measurements)
        for group in self.input_measurement_groups:
            object_name = cpmeas.IMAGE if group.wants_image.value \
                else group.use_object_name.value
            measurement_name = '_'.join(
                (object_name, group.measurement.value)
            )
            if measurement_name in input_measurements_copy:
                input_measurements_copy.remove(measurement_name)
            else:
                print 'WARNING: Input measurements (%s, %s) has been' \
                      ' declared but is never used in the script' \
                      % (object_name, group.measurement.value)
        if len(input_measurements_copy) > 0:
            raise cps.ValidationError(
                'The script uses measurements that have not been declared' \
                ' in the settings: %s' % ', '.join(input_measurements_copy),
                self.input_measurement_groups
            )
        # ... for constants
        input_constants_copy = list(input_constants)
        for group in self.input_constant_groups:
            py_name = group.py_name.value
            if py_name in input_constants_copy:
                input_constants_copy.remove(py_name)
            else:
                print 'WARNING: Input constant %s has been' \
                      ' declared but is never used in the script' \
                      % py_name
        if len(input_constants_copy) > 0:
            raise cps.ValidationError(
                'The script uses constants that have not been declared in' \
                ' the settings: %s' % ', '.join(input_constants_copy),
                self.input_constant_groups
            )
        return True

    #
    # CellProfiler calls "run" on each image set in your pipeline.
    # This is where you do the real work.
    #
    def run(self, workspace):

        # Finder and loader object for use in the script.
        # The imported module provides access to the input objects for
        # the script.
        # This implements the importer protocol as described in PEP302
        # (see http://www.python.org/dev/peps/pep-0302/).
        # The module can be imported as:
        #   from cellprofiler import cpscript
        class cpscript_hook(object):
            def find_module(self, fullname, path=None):
                if fullname in ('cellprofiler.cpscript'):
                    return self

            def load_module(self, fullname):
                if fullname == 'cellprofiler.cpscript':
                    import sys
                    import imp
                    module = sys.modules.setdefault(fullname,
                                                    imp.new_module(fullname))
                    module.__file__ = "<%s>" % self.__class__.__name__
                    module.__loader__ = self
                    module.__dict__.update({
                        'IMAGE': cpmeas.IMAGE,
                        'images': RunScript.__ImageWrapper__(workspace),
                        'objects': RunScript.__ObjectWrapper__(workspace),
                        'measurements': RunScript \
                            .__MeasurementWrapper__(workspace),
                        'constants': RunScript \
                            .__ConstantWrapper__(workspace),
                    })
                    return module
        cpscript_hook_inst = cpscript_hook()
        # set up a namespace for the script to run in
        script_name = '<runscript script>'
        script_namespace = {
            '__name__': script_name,
            '__package__': None,
            '__doc__': None,
        }
        # add importer hook
        sys.meta_path.append(cpscript_hook_inst)
        try:
            # run script
            exec self.__codeobj in script_namespace
        finally:
            # remove importer hooks
            sys.meta_path.remove(cpscript_hook_inst)
        # retrieve output images from the script namespace
        for group in self.output_image_groups:
            image = script_namespace[group.py_name.value]
            if not isinstance(image, cpi.Image):
                image = cpi.Image(image)
            workspace.image_set.add(group.image_name.value, image)
        # retrieve output objects from the script namespace
        for group in self.output_object_groups:
            objects = script_namespace[group.py_name.value]
            if not isinstance(objects, cpo.Objects):
                new_objects = cpo.Objects()
                new_objects.segmented = objects
                objects = new_objects
            workspace.object_set.add_objects(objects, group.objects_name.value)
        # retrieve output measurements from the script namespace
        for group in self.output_measurement_groups:
            img = None
            object_name = (cpmeas.IMAGE if not group.relate_to_object.value
                           else group.object.value)
            if group.on_image.value:
                # if the value of group.relate_to_object.value is False,
                # group.on_image.value will be True (see visible_settings),
                img = group.image.value
            py_name = group.py_name.value
            measurement = script_namespace[py_name]
            if img is None:
                measurement_name = "%s_%s" % (
                    group.measurement_category.value,
                    group.measurement_name.value
                )
            else:
                measurement_name = "%s_%s_%s" % (
                    group.measurement_category.value,
                    group.measurement_name.value,
                    img
                )
            if object_name == cpmeas.IMAGE:
                workspace.measurements.add_image_measurement(
                    measurement_name,
                    measurement
                )
            else:
                workspace.measurements.add_measurement(
                    object_name,
                    measurement_name,
                    measurement
                )

    def post_run(self, workspace):
        # remove temporary file
        os.remove(self.__tmpfile_path)

    ################################
    #
    # DISPLAY
    #
    def is_interactive(self):
        return False

    def display(self, workspace):
        pass
