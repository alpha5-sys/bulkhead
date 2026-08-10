"""The operator.

Every setting lives on the operator rather than in a scene panel, so Blender's redo
panel (F9) drives the whole tool: nudge the seed and the hull re-plates instantly.
Rerolling until a layout looks right is the actual workflow, and this is the cheapest
possible way to give artists that loop.
"""
import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from bpy.types import Operator

from . import edition, mesh
from .core.features import FeatureParams
from .core.subdivide import PanelParams


class BULKHEAD_OT_plate(Operator):
    bl_idname = "bulkhead.plate"
    bl_label = "Panel Surface"
    bl_description = ("Plate the selected quads with hierarchical hull panelling. "
                      "Select faces in Edit Mode, then run this in Object Mode")
    bl_options = {"REGISTER", "UNDO"}

    seed: IntProperty(
        name="Seed", default=0, min=0, soft_max=999,
        description="Reroll for a different layout of the same character")

    # -- plating -------------------------------------------------------------
    max_depth: IntProperty(
        name="Subdivision", default=4, min=0, max=8,
        description="How many times a plate may split. The main density control")
    min_size: FloatProperty(
        name="Min Plate", default=0.08, min=0.005, max=0.5, subtype="FACTOR",
        description="Smallest plate, as a fraction of the face")
    stop_chance: FloatProperty(
        name="Variation", default=0.25, min=0.0, max=1.0, subtype="FACTOR",
        description="Chance a plate stops splitting early. This is what produces a "
                    "mix of large and small plates instead of a uniform grid")
    split_jitter: FloatProperty(
        name="Irregularity", default=0.18, min=0.0, max=0.45, subtype="FACTOR",
        description="How far off-centre plates may split")
    max_aspect: FloatProperty(
        name="Max Aspect", default=4.0, min=1.0, max=12.0,
        description="Upper bound on plate elongation. Stops long thin slivers")

    gap: FloatProperty(
        name="Panel Line", default=0.02, min=0.0, soft_max=0.5, unit="LENGTH",
        description="Width of the seam between plates, in world units")
    chamfer: FloatProperty(
        name="Chamfer", default=0.004, min=0.0, soft_max=0.1, unit="LENGTH",
        description="Draft angle on plate edges. This is what catches the light "
                    "along every seam and stops plating reading as flat tiles")
    base_height: FloatProperty(
        name="Plate Depth", default=0.02, min=0.0, soft_max=1.0, unit="LENGTH",
        description="How far every plate stands off the hull")
    levels: IntProperty(
        name="Height Steps", default=3, min=1, max=8,
        description="Number of machined levels plates may sit at")
    step_height: FloatProperty(
        name="Step", default=0.02, min=0.0, soft_max=1.0, unit="LENGTH",
        description="Height difference between levels")
    flush_bias: FloatProperty(
        name="Flush", default=0.55, min=0.0, max=1.0, subtype="FACTOR",
        description="Share of plates that stay at the base level. Lowering this "
                    "turns the surface into a skyline, which rarely looks right")

    quadrangulate: BoolProperty(
        name="Convert Non-Quads", default=True,
        description="Turn triangles and ngons into quads before plating. Off, they "
                    "are skipped - which on a boolean-cut model can mean half the "
                    "surface is left bare")

    # -- fittings ------------------------------------------------------------
    use_features: BoolProperty(
        name="Fittings", default=True,
        description="Bolt greebles and vents onto the plates")
    density: FloatProperty(
        name="Density", default=0.35, min=0.0, max=1.0, subtype="FACTOR")
    cell: FloatProperty(
        name="Fitting Size", default=0.045, min=0.002, max=0.5, subtype="FACTOR")
    margin: FloatProperty(
        name="Edge Margin", default=0.14, min=0.0, max=0.45, subtype="FACTOR",
        description="Keep fittings clear of the plate edge")
    vent_chance: FloatProperty(
        name="Vents", default=0.22, min=0.0, max=1.0, subtype="FACTOR")
    feature_height: FloatProperty(
        name="Fitting Height", default=0.015, min=0.0, soft_max=1.0, unit="LENGTH")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "MESH"
                and context.mode == "OBJECT")

    def panel_params(self):
        return PanelParams(
            max_depth=self.max_depth, min_size=self.min_size,
            max_aspect=self.max_aspect, split_jitter=self.split_jitter,
            stop_chance=self.stop_chance, levels=self.levels,
            flush_bias=self.flush_bias)

    def feature_params(self):
        return FeatureParams(
            density=self.density, cell=self.cell, margin=self.margin,
            vent_chance=self.vent_chance)

    def execute(self, context):
        obj = context.active_object
        # Free edition ships plating only; the flag is what the build strips.
        settings = _Settings(self, edition.HAS_FEATURES and self.use_features)
        settings.quadrangulate = self.quadrangulate

        panelled, skipped = mesh.plate_object(obj, settings, self.seed)

        if not panelled:
            self.report({"WARNING"},
                        "No quads to panel — Bulkhead plates four-sided faces")
            return {"CANCELLED"}
        if skipped:
            self.report({"INFO"},
                        f"Panelled {panelled} quads, skipped {skipped} non-quad")
        else:
            self.report({"INFO"}, f"Panelled {panelled} quads")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "seed")

        box = layout.box()
        box.label(text="Plating")
        col = box.column(align=True)
        col.prop(self, "max_depth")
        col.prop(self, "stop_chance", slider=True)
        col.prop(self, "split_jitter", slider=True)
        col.prop(self, "min_size", slider=True)
        col.prop(self, "max_aspect")
        col.prop(self, "quadrangulate")

        col = box.column(align=True)
        col.prop(self, "gap")
        col.prop(self, "chamfer")
        col.prop(self, "base_height")
        col.prop(self, "levels")
        col.prop(self, "step_height")
        col.prop(self, "flush_bias", slider=True)

        box = layout.box()
        if edition.HAS_FEATURES:
            box.prop(self, "use_features")
            col = box.column(align=True)
            col.enabled = self.use_features
            col.prop(self, "density", slider=True)
            col.prop(self, "cell", slider=True)
            col.prop(self, "margin", slider=True)
            col.prop(self, "vent_chance", slider=True)
            col.prop(self, "feature_height")
        else:
            row = box.row()
            row.enabled = False
            row.label(text="Fittings: greebles, vents", icon="LOCKED")


class _Settings:
    """Adapts operator properties to what mesh.py expects."""

    def __init__(self, op, use_features):
        self._op = op
        self.use_features = use_features
        self.gap = op.gap
        self.chamfer = op.chamfer
        self.base_height = op.base_height
        self.step_height = op.step_height
        self.feature_height = op.feature_height

    def panel_params(self):
        return self._op.panel_params()

    def feature_params(self):
        return self._op.feature_params()


CLASSES = (BULKHEAD_OT_plate,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
