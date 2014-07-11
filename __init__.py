bl_info = {
        "name": "UserPrefsBaseline",
        "description":"Save and load named sets of preferences.",
        "author":"dustractor@gmail.com",
        "version":(0,9),
        "blender":(2,65,0),
        "location":"This Location, when enabled.",
        "warning":"Color-properties, enabled addons, and selected theme are not taken into consideration.",
        "wiki_url":"",
        "category": "System"
    }

import bpy
import json
import os
import sys
import subprocess
import datetime

from . import baseline_lib_funcs

class BPREFS_OT_baseline_calibrate(bpy.types.Operator):
    bl_idname = "bprefs.create_baseline_file"
    bl_label = "Create Baseline File"
    bl_description = "Represents prefs at default state. Calculate this data per each updated version of blender."
    bl_options = {"INTERNAL"}
    def execute(self,context):
        run_script = os.path.join(os.path.dirname(__file__),"as_run.py")
        p = subprocess.Popen([bpy.app.binary_path,"-b","--factory-startup","-P",run_script],stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        a,b = p.communicate()
        a = a.decode()
        ok = a.count("SENTINEL_TOKEN")
        if not ok:
            self.report({"ERROR"},"An error occured. See console.")
            print(b.decode())
            return {"CANCELLED"}
        context.area.tag_redraw()
        return {"FINISHED"}

class BPREFS_OT_baseline_set(bpy.types.Operator):
    bl_idname = "bprefs.create_configuration_file"
    bl_label = "Output Current Configuration"
    bl_description = "Write changed preferences to file."
    bl_options = {"INTERNAL"}
    name = bpy.props.StringProperty(default="mybaseline")
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self)
    def execute(self,context):
        Z = baseline_lib_funcs.propdict(context.user_preferences)
        A = json.loads(open(baseline_lib_funcs.baseline_file,"r").read())
        commands = ""
        comments = ""
        commentline = "# %s changed from %s to %s.\n".__mod__
        commandline = "    C.user_preferences.%s = %s\n".__mod__
        for k in A:
            before,after = A[k],Z[k]
            if before != after:
                comments += commentline((k,before,after))
                commands += commandline((k,after))
        comments += "\n"
        fname = os.path.join(baseline_lib_funcs.baseline_data_storage,self.name+".py")
        flines = "\n".join([
                '# File created on %s and labeled %s.' %(datetime.datetime.now().ctime(),self.name),
                'import bpy',
                comments,
                'def register():',
                '    C = bpy.context',
                commands
                ])
        with open(fname,'w') as outputfile:
            outputfile.write(flines)
        if sys.platform == "darwin":
            os.system("open --reveal '%s'"%fname)
        context.area.tag_redraw()
        return {"FINISHED"}


class BPREFS_OT_baseline_load(bpy.types.Operator):
    bl_idname = "baseline.load_configuration"
    bl_label = "Load Configuration File"
    bl_options = {"INTERNAL"}
    configuration = bpy.props.StringProperty(default="")
    def execute(self,context):
        cfile = os.path.join(baseline_lib_funcs.baseline_data_storage,self.configuration)
        if not os.path.isfile(cfile):
            return {"CANCELLED"}
        cname = self.configuration.rpartition(".")[0]
        syspath = sys.path.copy()
        sys.path.append(baseline_lib_funcs.baseline_data_storage)
        __import__(cname).register()
        sys.path = syspath
        return {"FINISHED"}

class UserPrefsBaselineAddon(bpy.types.AddonPreferences):
    bl_idname = __package__
    prop = bpy.props.StringProperty(default="prop")
    def draw(self,context):
        layout = self.layout
        box = layout.box()
        if not os.path.isfile(baseline_lib_funcs.baseline_file):
            box.label("A %s baseline file has not been created yet."%(str(bpy.app.version)))
            box.operator("bprefs.create_baseline_file")
        else:
            box.label("Baseline file for %s located at:"%str(bpy.app.version))
            box.label(baseline_lib_funcs.baseline_file)
            box.operator("bprefs.create_baseline_file",text="Recalibrate baseline")
        layout.separator()
        box = layout.box()
        for cf in os.listdir(baseline_lib_funcs.baseline_data_storage):
            if not cf.endswith(".py"):
                continue
            row = box.row()
            row.label(cf)
            row.operator('baseline.load_configuration',text="Load %s"%cf.rpartition(".")[0]).configuration = cf
        layout.operator("bprefs.create_configuration_file")


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

