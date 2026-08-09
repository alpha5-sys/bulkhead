"""N-panel entry point.

Deliberately thin: the settings live on the operator so the redo panel drives
iteration. This panel exists to make the tool discoverable and to say plainly what
Bulkhead needs from the mesh, which is the one thing that trips people up.
"""
import bpy
from bpy.types import Panel

from . import edition


class BULKHEAD_PT_main(Panel):
    bl_label = "Bulkhead"
    bl_idname = "BULKHEAD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bulkhead"

    def draw(self, context):
        layout = self.layout
        layout.operator("bulkhead.plate", icon="MOD_BUILD")

        obj = context.active_object
        col = layout.column()
        col.scale_y = 0.8
        if obj is None or obj.type != "MESH":
            col.label(text="Select a mesh object.", icon="INFO")
            return
        if context.mode != "OBJECT":
            col.label(text="Select faces here, then", icon="INFO")
            col.label(text="Tab to Object Mode to plate.")
            return
        col.label(text="Plates the selected quads,", icon="INFO")
        col.label(text="or all of them if none are selected.")
        col.separator()
        col.label(text="Press F9 to reroll the seed.")


def _add_menu(self, context):
    self.layout.operator("bulkhead.plate", icon="MOD_BUILD")


CLASSES = (BULKHEAD_PT_main,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(_add_menu)


def unregister():
    bpy.types.VIEW3D_MT_object.remove(_add_menu)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
