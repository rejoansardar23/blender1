"""Original procedural market and a rigged robot. Run inside Blender.

blender -b --python-exit-code 1 --python blender/scene_builder/build_scene.py -- \
  --config projects/example_project/scene.json --blend artifacts/scene.blend \
  --glb artifacts/scene.glb

Materials and animation intentionally use portable glTF features. Area lights,
soft shadows, world lighting and Blender color management differ in WebGL.
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, color, metallic=0.0, roughness=0.5, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def finish(obj, name, mat, bevel=0, smooth=False):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Crafted soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    return obj


def box(name, loc, size, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, bevel)


def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, name, mat, smooth=True)


def cylinder(name, loc, radius, depth, mat, rotation=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                      depth=depth, location=loc, rotation=rotation)
    return finish(bpy.context.object, name, mat, bevel=0.015, smooth=True)


def rod(name, start, end, radius, mat):
    midpoint = (Vector(start) + Vector(end)) / 2
    obj = cylinder(name, midpoint, radius, (Vector(end) - Vector(start)).length, mat)
    obj.rotation_euler = (Vector(end) - Vector(start)).to_track_quat("Z", "Y").to_euler()
    return obj


def text(name, value, loc, size, mat, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = value
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.008
    obj.data.bevel_depth = 0.002
    obj.data.materials.append(mat)
    # glTF does not export font curves; turn signage into portable geometry.
    bpy.ops.object.convert(target="MESH")
    return obj


def bulb(name, loc, mats, energy=15):
    cylinder(name + " cap", (loc[0], loc[1], loc[2] + .06), .055, .08, mats["metal"])
    sphere(name + " glowing glass", loc, (.09, .09, .13), mats["glow"])
    if energy:
        data = bpy.data.lights.new(name + " light", "POINT")
        data.color = (1, .51, .20)
        data.energy = energy
        data.shadow_soft_size = .5
        obj = bpy.data.objects.new(name + " light", data)
        bpy.context.collection.objects.link(obj)
        obj.location = loc


def area(name, loc, energy, color, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.color, data.shape, data.size = energy, color, "DISK", size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def market(m):
    """A compact but complete set: architecture, stalls, street dressing and lamps."""
    box("Floating diorama foundation", (0, 1.1, -.28), (13, 10.4, .48), m["stone"], .18)
    box("Asphalt street", (0, -1.2, -.02), (12.8, 5.7, .12), m["road"])
    box("Raised market pavement", (0, 3.2, .07), (12.8, 4.3, .3), m["sand"])
    for x in range(-6, 7):
        for y in range(1, 6):
            box("Pavement sandstone", (x + .04 * (y % 2), y, .235), (.96, .96, .045),
                m["sand"] if (x+y) % 3 else m["rose"], .012)
    for x in range(-6, 7):
        box("Pavement curb", (x, .9, .19), (.96, .32, .34), m["cream"], .035)
    for x in (-4.8, -2.4, 0, 2.4, 4.8):
        box("Road marking", (x, -2.9, .052), (1.05, .075, .006), m["gold"], .002)
    # Facades. Their differing heights make an intentionally asymmetric skyline.
    for i, (x, width, height, color) in enumerate([
        (-4.7, 3.0, 4.9, "teal"), (-1.4, 3.3, 5.6, "rose"),
        (2.0, 3.1, 4.8, "sand"), (4.9, 2.5, 5.7, "teal")
    ]):
        box("Shop facade", (x, 4.6, height/2 + .25), (width, 1.8, height), m[color], .07)
        box("Facade cornice", (x, 3.64, height + .17), (width + .12, .25, .18), m["cream"])
        box("Facade upper cornice", (x, 4.45, height + .42), (width + .2, 2.05, .24), m["stone"])
        for wx in (x-width*.24, x+width*.24):
            box("Window cream frame", (wx, 3.66, height - 1), (.77, .11, 1.18), m["cream"], .07)
            box("Night blue window", (wx, 3.58, height - 1), (.64, .08, 1.04), m["glass"], .05)
            for z in (height-1.2, height-.8):
                box("Window cross bar", (wx, 3.51, z), (.66, .04, .035), m["gold"], .006)
            box("Window central bar", (wx, 3.51, height-1), (.035, .04, 1.02), m["gold"], .006)
        for px in (x-width/2+.13, x+width/2-.13):
            box("Facade pilaster", (px, 3.65, 1.8), (.14, .15, 3.0), m["cream"])
        box("Shop dark doorway", (x, 3.63, 1.45), (width*.57, .16, 2.4), m["glass"])
    # Main chai stall, open on all sides so the product and props are visible.
    for x in (-3.8, -.6):
        for y in (1.9, 3.3):
            box("Chai stall timber pillar", (x, y, 1.8), (.13, .13, 3.1), m["wood"])
    box("Chai counter wood", (-2.2, 2.35, .87), (3.4, 1.35, 1.25), m["wood"])
    box("Chai counter front teal", (-2.2, 1.65, .89), (3.12, .06, 1.03), m["teal"])
    for x in (-3.5, -2.85, -2.2, -1.55, -.9):
        box("Counter golden trim", (x, 1.60, .89), (.035, .03, .94), m["gold"], .006)
    box("Chai worktop", (-2.2, 2.32, 1.54), (3.6, 1.54, .13), m["cream"], .08)
    for i in range(10):
        x = -3.96 + i * .39
        roof = box("Striped chai canopy", (x, 2.45, 3.5), (.395, 2.25, .12),
                   m["saffron"] if i % 2 else m["cream"])
        roof.rotation_euler.x = -.09
        box("Scalloped valance", (x, 1.33, 3.35), (.39, .10, .26),
            m["saffron"] if i % 2 else m["cream"], .07)
    box("Chai sign panel", (-2.2, 1.72, 2.98), (2.36, .12, .57), m["teal"], .07)
    text("Chai sign lettering", "CHAI  /  07", (-2.2, 1.64, 3), .32, m["cream"])
    text("Counter lettering", "A LITTLE CUP OF JOY", (-2.2, 1.55, .96), .15, m["cream"])
    # Kettle: body, lid, spout and handle all original geometry.
    sphere("Brass kettle", (-2.8, 2.1, 1.91), (.32, .28, .32), m["brass"])
    cylinder("Kettle lid", (-2.8, 2.1, 2.19), .2, .05, m["brass"])
    sphere("Kettle knob", (-2.8, 2.1, 2.26), (.05, .05, .05), m["wood"])
    rod("Kettle spout", (-2.57, 2.1, 1.99), (-2.29, 2.1, 2.15), .06, m["brass"])
    bpy.ops.mesh.primitive_torus_add(major_radius=.23, minor_radius=.036,
                                    location=(-3.06, 2.1, 2.01), rotation=(math.pi/2, 0, 0))
    finish(bpy.context.object, "Kettle loop handle", m["wood"], smooth=True)
    for i in range(6):
        cylinder("Earthen chai cup", (-2.1 + (i % 3)*.23, 1.95+(i//3)*.27, 1.73),
                 .075, .23, m["terra"])
        cylinder("Chai surface", (-2.1 + (i % 3)*.23, 1.95+(i//3)*.27, 1.85),
                 .061, .005, m["wood"])
    for x in (-3.3, -1.1):
        bulb("Stall pendant", (x, 2.2, 3.15), m, 28)
    # Neighboring produce cart and vivid fruit crates.
    box("Produce cart base", (2.9, 2.15, .78), (2.35, 1.25, .22), m["wood"])
    for x in (2, 3.8):
        for y in (1.65, 2.65):
            cylinder("Cart wheel", (x, y, .5), .32, .12, m["rubber"], (math.pi/2,0,0))
            cylinder("Cart hub", (x, y-.07, .5), .11, .13, m["brass"], (math.pi/2,0,0))
    for i in range(3):
        x = 2.14 + i * .75
        box("Produce crate", (x, 2.15, 1.0), (.68, 1.08, .3), m["wood"])
        for n in range(12):
            sphere("Fresh market produce", (x + random.uniform(-.23,.23),
                                             2.15 + random.uniform(-.4,.4),
                                             1.17 + .04*(n%2)),
                   (.105,.105,.105), m[("orange","apple","green")[i]])
    for x in (1.7, 4.1):
        box("Produce awning pole", (x, 2.8, 1.8), (.09,.09,2.7), m["wood"])
    box("Produce shade", (2.9, 2.45, 3.17), (2.7,1.8,.12), m["rose"])
    text("Produce sign", "FRESH DAILY", (2.9, 1.5, 2.95), .23, m["cream"])
    # Stacked sacks, plants, crates and a chalkboard make the set lived in.
    for x,y in [(4.8,1.5),(5.4,2.3),(-5.2,2.2)]:
        cylinder("Terracotta planter", (x,y,.5), .31,.6,m["terra"])
        for j in range(7):
            leaf = sphere("Planter leaf", (x+random.uniform(-.25,.25), y+random.uniform(-.18,.18),
                                           .85+random.uniform(0,.35)), (.1,.08,.4),m["green"])
            leaf.rotation_euler = (random.uniform(-.5,.5), random.uniform(-.6,.6), j)
    board = box("Menu chalkboard", (-4.55, .9, .94), (.7,.10,1.25),m["teal"])
    board.rotation_euler.y = -.08
    text("Chalkboard title", "TODAY", (-4.55,.82,1.25),.16,m["cream"])
    text("Chalkboard menu", "MASALA\nCHAI\n\nHOT & HAPPY",(-4.55,.81,.87),.13,m["cream"])
    for x in (-5.7,5.7):
        cylinder("Street lamp mast", (x, .4, 1.95), .055, 3.8, m["metal"])
        bulb("Street lantern", (x,.4,3.8), m,40)
        box("Street lantern top", (x,.4,4.02),(.4,.4,.1),m["metal"])
    # Hanging cable and decorative flags across the street.
    for i in range(15):
        x = -6 + i * 12/14
        z = 4.6 - .65 * (1-(x/6)**2)
        if i:
            rod("String light cable", (last_x, .1,last_z), (x,.1,z), .012,m["metal"])
        bulb("Festoon bulb",(x,.1,z-.13),m,8)
        last_x,last_z=x,z
    for i in range(12):
        x = -5.7 + i
        z = 4.3 - .5*(1-(x/6)**2)
        mesh = bpy.data.meshes.new("Festival pennant mesh")
        mesh.from_pydata([(x,2.9,z),(x+.48,2.9,z),(x+.24,2.9,z-.55)],[],[(0,1,2)])
        mesh.materials.append(m[("saffron","teal","rose","cream")[i%4]])
        obj=bpy.data.objects.new("Festival pennant",mesh)
        bpy.context.collection.objects.link(obj)


def courier(m):
    """Rigid weighted articulated robot. No implied human auto-rigging."""
    armature = bpy.data.armatures.new("Courier mechanical skeleton")
    rig = bpy.data.objects.new("Milo the courier — rig", armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = {}
    for name,head,tail,parent in [
        ("root",(0,0,.25),(0,0,.8),None),
        ("body",(0,0,.8),(0,0,1.65),"root"),
        ("head",(0,0,1.7),(0,0,2.3),"body"),
        ("arm.L",(-.5,0,1.5),(-.95,0,1.1),"body"),
        ("arm.R",(.5,0,1.5),(.95,0,1.1),"body"),
        ("hand.L",(-.95,0,1.1),(-1.08,0,.9),"arm.L"),
        ("hand.R",(.95,0,1.1),(1.08,0,.9),"arm.R"),
        ("antenna",(.25,0,2.3),(.38,0,2.7),"head")
    ]:
        bone=armature.edit_bones.new(name)
        bone.head, bone.tail=head,tail
        if name.startswith(("arm.","hand.")):
            # Fix mechanical hinge axes so raising an arm stays in the XZ plane.
            bone.align_roll(Vector((0,-1,0)))
        if parent:
            bone.parent=bones[parent]
        bones[name]=bone
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)
    def bind(obj,bone):
        group=obj.vertex_groups.new(name=bone)
        group.add(list(range(len(obj.data.vertices))),1,"REPLACE")
        modifier=obj.modifiers.new("Mechanical skeleton","ARMATURE")
        modifier.object=rig
        obj.parent=rig
        return obj
    bind(box("Courier chassis",(0,0,.63),(.85,.62,.55),m["teal"],.16),"root")
    for x in (-.47,.47):
        bind(cylinder("Courier wheel",(x,0,.29),.29,.18,m["rubber"],(0,math.pi/2,0)),"root")
        bind(cylinder("Wheel brass hub",(x*1.2,0,.29),.13,.04,m["brass"],(0,math.pi/2,0)),"root")
    bind(box("Courier enamel body",(0,0,1.21),(.95,.66,1.08),m["saffron"],.20),"body")
    bind(box("Courier chest inset",(0,-.345,1.22),(.55,.055,.52),m["cream"],.08),"body")
    bind(box("Courier chest badge",(0,-.38,1.25),(.26,.02,.11),m["teal"],.03),"body")
    for x in (-.15,0,.15):
        bind(sphere("Courier chest light",(x,-.38,1.07),(.025,.018,.025),m["mint_glow"]),"body")
    bind(box("Courier delivery satchel",(0,.45,1.12),(.72,.35,.8),m["rose"],.12),"body")
    bind(box("Satchel strap",(0,.64,1.14),(.1,.03,.65),m["cream"]),"body")
    bind(cylinder("Neck bearing",(0,0,1.78),.18,.18,m["metal"]),"head")
    bind(box("Courier rounded helmet",(0,-.02,2.08),(1.04,.72,.67),m["cream"],.22),"head")
    bind(box("Courier glass face",(0,-.396,2.08),(.88,.055,.45),m["glass"],.16),"head")
    for x in (-.2,.2):
        eye=bind(box("Friendly illuminated eye",(x,-.432,2.1),(.10,.02,.17),m["mint_glow"],.045),"head")
        for frame,height in [(1,1),(44,1),(46,.08),(48,1),(104,1),(106,.08),(108,1),(144,1)]:
            eye.scale.z=height
            eye.keyframe_insert("scale",frame=frame)
        bind(box("Courier eyebrow",(x,-.432,2.28),(.16,.025,.035),m["saffron"],.012),"head")
    bind(box("Courier smile",(0,-.435,1.97),(.17,.02,.025),m["mint_glow"],.01),"head")
    for x in (-.56,.56):
        bind(cylinder("Helmet ear panel",(x,-.02,2.1),.13,.07,m["brass"],(0,math.pi/2,0)),"head")
    for side,x in [("L",-1),("R",1)]:
        bind(sphere("Shoulder swivel",(x*.5,0,1.5),(.17,.17,.17),m["metal"]),"arm."+side)
        bind(rod("Telescoping arm",(x*.55,0,1.47),(x*.95,0,1.1),.105,m["saffron"]),"arm."+side)
        bind(sphere("Wrist swivel",(x*.95,0,1.1),(.12,.12,.12),m["metal"]),"hand."+side)
        bind(box("Robot mitten palm",(x*1.05,0,.96),(.23,.20,.25),m["cream"],.075),"hand."+side)
        for finger in range(3):
            bind(box("Mechanical finger",(x*(.98+finger*.07),-.015,.79),(.055,.15,.15),m["cream"],.02),"hand."+side)
    bind(rod("Spring antenna",(.25,0,2.35),(.38,0,2.7),.025,m["brass"]),"antenna")
    bind(sphere("Antenna lamp",(.38,0,2.72),(.085,.085,.085),m["glow"]),"antenna")
    return rig


def animate(rig):
    # Ease in, settle, greet. Mechanical armature action exports to glTF.
    for frame,x,y,zrot in [(1,-2.8,-.9,-.15),(26,-1.3,-.8,-.08),(52,0,-.65,0),
                           (78,.05,-.65,.06),(116,.05,-.65,.02),(144,.05,-.65,-.09)]:
        rig.location=(x,y,0)
        rig.rotation_euler=(0,0,zrot)
        rig.keyframe_insert("location",frame=frame)
        rig.keyframe_insert("rotation_euler",frame=frame)
    poses = {
        "body": [(1,(.03,0,-.05)),(20,(-.03,0,.04)),(40,(.03,0,-.03)),(55,(0,0,.01)),
                 (75,(-.03,0,-.04)),(100,(.02,0,-.04)),(122,(0,0,.025)),(144,(0,0,0))],
        "head": [(1,(0,.04,-.18)),(35,(0,-.04,-.12)),(56,(0,0,-.23)),(72,(-.07,0,.12)),
                 (94,(.02,0,.03)),(112,(-.05,0,-.05)),(144,(0,0,.08))],
        "arm.R": [(1,(0,0,.05)),(40,(0,0,-.04)),(55,(0,0,.05)),(72,(.1,0,2.45)),
                  (84,(-.12,0,2.15)),(96,(.1,0,2.48)),(108,(-.09,0,2.14)),
                  (120,(0,0,2.3)),(140,(0,0,.03)),(144,(0,0,.03))],
        "hand.R": [(1,(0,0,0)),(70,(0,.12,.1)),(82,(0,-.2,-.14)),(94,(0,.2,.18)),
                   (106,(0,-.2,-.15)),(118,(0,.15,.1)),(144,(0,0,0))],
        "arm.L": [(1,(0,0,-.04)),(30,(.04,0,.08)),(55,(0,0,0)),(80,(.05,0,-.06)),
                  (115,(0,0,-.04)),(144,(0,0,0))],
        "antenna": [(1,(.1,0,0)),(35,(-.12,0,0)),(58,(.1,0,0)),(75,(-.13,0,0)),
                    (90,(.08,0,0)),(110,(-.05,0,0)),(144,(0,0,0))]
    }
    for name,keyframes in poses.items():
        bone=rig.pose.bones[name]
        bone.rotation_mode="XYZ"
        for frame,rotation in keyframes:
            bone.rotation_euler=rotation
            bone.keyframe_insert("rotation_euler",frame=frame,group=name)
    rig.animation_data.action.name="Milo arrives and waves"
    action = rig.animation_data.action
    # Blender 5 uses layered actions; Blender 4.3 also exposes legacy fcurves.
    if hasattr(action, "fcurves"):
        curves = action.fcurves
    else:
        curves = [curve for layer in action.layers for strip in layer.strips
                  for bag in strip.channelbags for curve in bag.fcurves]
    for curve in curves:
        for key in curve.keyframe_points:
            key.interpolation="BEZIER"
            key.handle_left_type=key.handle_right_type="AUTO_CLAMPED"


def build(config, output_blend, output_glb=None):
    if not isinstance(config,dict):
        config=json.loads(Path(config).read_text())
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    random.seed(config.get("seed",23))
    colors={
        "teal":(.025,.22,.23),"rose":(.49,.14,.15),"sand":(.56,.38,.22),
        "cream":(.92,.77,.49),"stone":(.06,.09,.14),"road":(.035,.07,.10),
        "gold":(.70,.40,.13),"saffron":(.95,.32,.055),"wood":(.16,.065,.027),
        "terra":(.48,.16,.08),"green":(.07,.28,.12),"apple":(.67,.045,.03),
        "orange":(.95,.27,.025),"metal":(.06,.09,.12),"rubber":(.018,.025,.034),
        "glass":(.008,.027,.055),"brass":(.65,.34,.075),
        "glow":(1,.48,.13),"mint_glow":(.15,1,.72)
    }
    m={key:material(key,color,
                    metallic=.65 if key in ("brass","metal") else .15 if key=="saffron" else 0,
                    roughness=.28 if key in ("brass","metal","road","glass") else .6,
                    emission=4 if key in ("glow","mint_glow") else 0)
       for key,color in colors.items()}
    market(m)
    rig=courier(m)
    animate(rig)
    scene=bpy.context.scene
    scene.frame_start=config.get("frame_start",1)
    scene.frame_end=config.get("frame_end",144)
    scene.render.fps=config.get("fps",24)
    width,height=config.get("resolution",[1920,1080])
    scene.render.resolution_x,scene.render.resolution_y=width,height
    scene.render.resolution_percentage=100
    scene.render.engine="CYCLES"
    scene.cycles.samples=32
    # Portable CPU baseline; the render runner can enable supported denoisers.
    # The cloud Debian Blender build lacks OpenImageDenoise.
    scene.cycles.use_denoising=False
    scene.cycles.max_bounces=5
    scene.world.use_nodes=True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.045,.09,.22,1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.45
    area("Moon blue softbox",(1,0,9),1500,(.35,.55,1),8,(0,1,0))
    area("Warm market key",(-4,-3,6),1800,(1,.56,.27),6,(0,1,1))
    area("Cool rim light",(5,4,7),2100,(.28,.65,1),5,(0,0,1.5))
    area("Gentle face fill",(1,-5,4),350,(.75,.85,1),4,(0,0,1.5))
    bpy.ops.object.camera_add(location=(9,-13,8))
    camera=bpy.context.object
    camera.name="Cinematic market dolly"
    camera.data.lens=47
    camera.data.clip_end=150
    scene.camera=camera
    for frame,position,target,lens in [
        (1,(10,-15,9),(0,1.3,1.6),47),
        (72,(8.3,-13.8,7.4),(0,1.2,1.65),49),
        (144,(6.8,-12.5,6.0),(0,1.05,1.6),51)
    ]:
        camera.location=position
        camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
        camera.data.lens=lens
        camera.keyframe_insert("location",frame=frame)
        camera.keyframe_insert("rotation_euler",frame=frame)
        camera.data.keyframe_insert("lens",frame=frame)
    for frame,label in [(1,"ARRIVAL / establishing"),(57,"GREETING / wave"),(117,"SETTLE / reaction")]:
        scene.timeline_markers.new(label,frame=frame)
    scene.view_settings.view_transform="AgX"
    scene.render.image_settings.file_format="PNG"
    scene.frame_set(88)
    scene["project_title"]=config.get("title","Chai at Blue Hour")
    scene["quality_level"]="Original stylized proof of concept; professional human rigs and lip-sync not implemented."
    scene["animation_notes"]="Rigid weighted mechanical character, body anticipation, overlapping head and antenna, arm and wrist wave."
    for path in (output_blend,output_glb):
        if path:
            Path(path).resolve().parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(output_blend).resolve()))
    if output_glb:
        # Bake all scene animations, including weighted armature and camera.
        bpy.ops.export_scene.gltf(filepath=str(Path(output_glb).resolve()),export_format="GLB",
                                  export_cameras=True,export_lights=True,
                                  export_animations=True,export_frame_range=True,
                                  export_force_sampling=True,export_apply=True,
                                  export_yup=True)
    print(json.dumps({"status":"built","blend":str(output_blend),"glb":str(output_glb),
                      "objects":len(scene.objects),"frames":[scene.frame_start,scene.frame_end],
                      "fps":scene.render.fps,"blender":bpy.app.version_string}))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    parser.add_argument("--blend",required=True)
    parser.add_argument("--glb")
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    build(args.config,args.blend,args.glb)
