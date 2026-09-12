"""Author Akhani's ten-hit combo. Blender --background --python this.py [-- --render].

No external packages; preview stills are the default, full PNG sequence optional.
"""
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/muay-thai-fighter/combat-v2'
WEB = ROOT / 'web-assets'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'frames').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT.parent / 'akhani-hero.blend'))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
rig, hero = bpy.data.objects['AkhaniRig'], bpy.data.objects['Akhani']
rig.animation_data_clear()
bpy.data.materials['Skin | warm bronze'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .57
for action in list(bpy.data.actions):
    bpy.data.actions.remove(action)
scene.frame_start, scene.frame_end, scene.render.fps = 1, 300, 30
scene.render.fps_base = 1
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
heads = {b.name: b.head_local.copy() for b in rig.data.bones}
tails = {b.name: b.tail_local.copy() for b in rig.data.bones}
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# The original shorts had a hard pelvis/thigh cutoff. Blend the waistband into
# each leg continuously so the raised knee does not pull through a rigid panel.
cloth_ids = set()
for polygon in hero.data.polygons:
    if hero.data.materials[polygon.material_index].name in {
        'Shorts | midnight satin', 'Leather | burnt orange', 'Piping | warm ivory', 'Gloves | tangerine leather'
    }:
        cloth_ids.update(i for i in polygon.vertices if .79 < hero.data.vertices[i].co.z < 1.175)
for index in cloth_ids:
    v = hero.data.vertices[index].co
    weight = max(0, min(1, (1.145 - v.z) / .085))
    left = max(0, min(1, (v.x + .045) / .09))
    for group in hero.vertex_groups:
        group.remove([index])
    for name, value in [('pelvis', 1 - weight), ('thigh.L', weight * left), ('thigh.R', weight * (1 - left))]:
        hero.vertex_groups[name].add([index], value, 'REPLACE')

# The original merged sculpt's nearest-bone weights pulled feet toward the shins.
# Rigid soles keep contact clean; retain a short smooth ankle transition.
for vertex in hero.data.vertices:
    if vertex.co.z < .245:
        side = 'L' if vertex.co.x > 0 else 'R'
        for group in hero.vertex_groups:
            group.remove([vertex.index])
        foot_weight = max(0, min(1, (.245 - vertex.co.z) / .055))
        hero.vertex_groups['foot.' + side].add([vertex.index], foot_weight, 'REPLACE')
        hero.vertex_groups['shin.' + side].add([vertex.index], 1 - foot_weight, 'REPLACE')


def pose(l=(.18, -.245, 1.47), r=(-.15, -.20, 1.48), turn=-22, hip=-17,
         x=0, y=0, z=-.11, lean=.09, roll=0, lh=(1, -.2, -1), rh=(-1, -.2, -1),
         ld=(0, -.3, 1), rd=(0, -.3, 1), pivot=0,
         lf=(.29, -.18, .147), rf=(-.31, .23, .147), rk=(-.28, -1, .1)):
    return [Vector(l), Vector(r), math.radians(turn), math.radians(hip),
            Vector((x, y, z)), lean, roll, Vector(lh), Vector(rh), Vector(ld), Vector(rd), pivot,
            Vector(lf), Vector(rf), Vector(rk)]


guard = pose()
jab = pose(l=(.15, -.866, 1.49), turn=-46, hip=-28, x=.035, y=-.038,
           z=-.095, lean=.12, lh=(1, 0, -.3), ld=(0, -1, .08), pivot=.06)
cross = pose(r=(-.03, -.72, 1.52), turn=28, hip=8, x=.065, y=-.047,
             z=-.10, lean=.12, rh=(-1, 0, -.25), rd=(0, -1, .05), pivot=.28)
hook = pose(l=(-.15, -.45, 1.57), turn=-43, hip=-30, x=.032, y=-.018,
            z=-.13, lean=.07, roll=-.05, lh=(1, -.1, .4), ld=(-1, -.25, .08), pivot=.08)
upper = pose(r=(-.035, -.47, 1.89), turn=28, hip=12, x=.055, y=-.04,
             z=-.065, lean=.015, roll=.035, rh=(-.4, -.4, -1), rd=(0, -.25, 1), pivot=.26)
wind_l = pose(l=(.38, -.09, 1.45), turn=4, hip=-7, z=-.135, roll=.04)
wind_r = pose(r=(-.31, -.09, 1.34), turn=-38, hip=-26, z=-.19, lean=.10)
knee = pose(l=(.19, -.28, 1.53), r=(-.17, -.23, 1.56), turn=-8, hip=-7,
            x=.10, y=-.04, z=-.075, lean=-.08, rf=(-.10, -.34, .73), rk=(0, -1, 1))
jump = pose(l=(.19, -.24, 2.03), r=(-.015, -.75, 2.18), turn=23, hip=6,
            x=.04, y=-.10, z=.43, lean=.12, rh=(-1, 0, -.15), rd=(0, -1, -.06),
            lf=(.26, -.29, .91), rf=(-.29, .40, .80), rk=(-.25, -.8, .4))
air_guard = pose(l=(.19, -.245, 1.90), r=(-.15, -.20, 1.91), turn=-18, hip=-13,
                 x=.02, y=-.04, z=.29, lean=.05, lf=(.29, -.18, .63), rf=(-.31, .23, .63))
beats = [
    (1, guard), (10, pose(z=-.125)), (17, pose(turn=-10, hip=-10, z=-.145)),
    (21, pose(l=(.22, -.40, 1.51), turn=-29, z=-.11)), (24, jab), (26, jab),
    (30, pose(turn=-34, hip=-23, r=(-.27, -.13, 1.5), z=-.13)),
    (35, cross), (37, cross), (42, pose(turn=-10, hip=-14, z=-.135)),
    (48, jab), (50, jab), (55, pose(turn=-36, hip=-24, z=-.14)),
    (62, cross), (64, cross), (71, wind_l), (78, hook), (80, hook),
    (87, wind_r), (95, upper), (97, upper), (105, wind_l),
    (113, hook), (115, hook), (123, pose(turn=-40, hip=-24, r=(-.30, -.10, 1.45), z=-.16)),
    (132, cross), (135, cross), (143, pose(z=-.145)), (151, guard),
    (160, pose(x=.08, z=-.13, rf=(-.20, .09, .33), rk=(0, -1, .4))),
    (168, pose(x=.10, y=-.025, z=-.11, lean=-.06, rf=(-.12, -.20, .58), rk=(0, -1, 1))),
    (175, knee), (178, knee), (185, pose(z=-.23, lean=.17)),
    (193, pose(l=(.18, -.24, 1.65), r=(-.19, -.14, 1.56), x=.02, y=-.025, z=.05,
               lf=(.29, -.18, .38), rf=(-.31, .23, .38))),
    (205, pose(l=(.18, -.36, 1.98), r=(-.24, -.12, 1.93), turn=-35, hip=-22,
               x=.04, y=-.07, z=.38, lf=(.27, -.27, .84), rf=(-.30, .38, .72))),
    (215, jump), (218, jump), (231, air_guard), (240, air_guard),
    (251, pose(l=(.18, -.24, 1.55), r=(-.15, -.20, 1.56), z=-.02,
               lf=(.29, -.18, .23), rf=(-.31, .23, .23))),
    (258, pose(z=-.18, lean=.13)), (265, pose(z=-.23, lean=.16)),
    (279, pose(z=-.125)), (291, guard), (300, guard), (301, guard),
]
HITS = [(24, 'JAB'), (35, 'CROSS'), (48, 'DOUBLE JAB'), (62, 'CROSS'),
        (78, 'LEFT HOOK'), (95, 'RIGHT UPPERCUT'), (113, 'LEFT HOOK'), (132, 'CROSS'),
        (175, 'RIGHT KNEE'), (215, 'JUMPING PUNCH')]


def state_at(frame):
    for (fa, a), (fb, b) in zip(beats, beats[1:]):
        if fa <= frame <= fb:
            t = (frame - fa) / (fb - fa)
            t = t * t * (3 - 2 * t)
            return [av * (1 - t) + bv * t for av, bv in zip(a, b)]
    raise ValueError(frame)


def global_rotation(name, rotation):
    pb = rig.pose.bones[name]
    pb.matrix = Matrix.LocRotScale(pb.head.copy(), rotation @ rest[name].to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def orient(name, head, tail):
    direction = (tail - head).normalized()
    original = (tails[name] - heads[name]).normalized()
    q = original.rotation_difference(direction) @ rest[name].to_quaternion()
    rig.pose.bones[name].matrix = Matrix.LocRotScale(head, q, Vector((1, 1, 1)))
    bpy.context.view_layer.update()


def limb(upper, lower, target, hint):
    head = rig.pose.bones[upper].head.copy()
    a, b = rig.data.bones[upper].length, rig.data.bones[lower].length
    delta = target - head
    distance = delta.length
    assert abs(a - b) + .001 < distance < a + b - .001, (scene.frame_current, upper, distance, a + b)
    direction = delta / distance
    along = (a * a - b * b + distance * distance) / (2 * distance)
    bend = hint - direction * hint.dot(direction)
    elbow = head + direction * along + bend.normalized() * math.sqrt(max(0, a * a - along * along))
    orient(upper, head, elbow)
    orient(lower, elbow, target)


foot_ids = {s: [v.index for v in hero.data.vertices if v.co.z < .19 and (v.co.x > 0) == (s == 'L')] for s in ('L', 'R')}
for frame in range(1, 302):
    scene.frame_set(frame)
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    left, right, yaw, hip, shift, lean, roll, lh, rh, ld, rd, pivot, lf, rf, rk = state_at(frame)
    rig.pose.bones['root'].matrix = Matrix.Translation(shift) @ rest['root']
    bpy.context.view_layer.update()
    global_rotation('pelvis', Quaternion((0, 0, 1), hip))
    global_rotation('spine', Quaternion((0, 0, 1), (hip + yaw) * .5) @ Quaternion((1, 0, 0), lean * .45))
    global_rotation('chest', Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), lean) @ Quaternion((0, 1, 0), roll))
    # Keep the chin tucked and eyes on the same imaginary opponent throughout.
    global_rotation('neck', Quaternion((0, 0, 1), yaw * .2) @ Quaternion((1, 0, 0), .07))
    global_rotation('head', Quaternion((0, 0, 1), -.08) @ Quaternion((1, 0, 0), .09))
    limb('upper_arm.L', 'forearm.L', left + Vector((shift.x * .2, 0, 0)), lh)
    limb('upper_arm.R', 'forearm.R', right + Vector((shift.x * .2, 0, 0)), rh)
    for side, direction in [('L', ld), ('R', rd)]:
        pb = rig.pose.bones['hand.' + side]
        orient(pb.name, pb.head.copy(), pb.head + direction.normalized() * pb.length)
    foot_points = {'L': lf, 'R': rf}
    for side in ('L', 'R'):
        turn = -.12 if side == 'L' else -.32 + pivot
        pitch = 0 if side == 'L' else pivot * .35
        q = Quaternion((0, 0, 1), turn) @ Quaternion((1, 0, 0), pitch)
        # Pivot around the planted forefoot. The rear heel lifts on crosses.
        toe = foot_points[side] + Vector((0, -.16, -.105))
        ankle = toe + q @ Vector((0, .16, .105))
        limb('thigh.' + side, 'shin.' + side, ankle, Vector((.28, -1, .1)) if side == 'L' else rk)
        rig.pose.bones['foot.' + side].matrix = Matrix.LocRotScale(ankle, q @ rest['foot.' + side].to_quaternion(), Vector((1, 1, 1)))
        bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = hero.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    clearances = {s: min((evaluated.matrix_world @ mesh.vertices[i].co).z for i in ids) for s, ids in foot_ids.items()}
    evaluated.to_mesh_clear()
    # A uniform millimetric rest-foot correction is baked into the FK feet.
    for side, clearance in clearances.items():
        pb = rig.pose.bones['foot.' + side]
        matrix = pb.matrix.copy()
        matrix.translation.z += .002 + foot_points[side].z - .147 - clearance
        limb('thigh.' + side, 'shin.' + side, matrix.translation, Vector((.28, -1, .1)) if side == 'L' else rk)
        pb.matrix = matrix
        bpy.context.view_layer.update()
    for pb in rig.pose.bones:
        pb.keyframe_insert(data_path='location', frame=frame, group=pb.name)
        pb.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=pb.name)
rig.animation_data.action.name = 'Combat_Combo'
rig['motion_notes'] = 'Eight rapid punches followed by a right knee and jumping punch; airborne guard and cushioned landing. Baked FK, 30 fps, ten-second loop, front -Y.'
rig['skinning_notes'] = 'Original authored Akhani sculpt; rigid sole cleanup for grounded combat.'
for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)
for frame, name in HITS:
    scene.timeline_markers.new(name, frame=frame)
scene.timeline_markers.new('AIRBORNE GUARD', frame=240)
scene.timeline_markers.new('LANDING', frame=265)
scene.timeline_markers.new('GUARD / LOOP', frame=300)

# Character-only export. Frame301 repeats1 to give glTF an exact10s action.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
hero.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(WEB / 'akhani-combat.glb'), export_format='GLB', use_selection=True,
    export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False, export_anim_slide_to_zero=True,
    export_skins=True, export_yup=True, export_cameras=False, export_lights=False)

# Restrained arena lighting, with a grounded stage and a readable silhouette.
for obj in list(bpy.data.collections['STUDIO'].objects):
    bpy.data.objects.remove(obj, do_unlink=True)
studio = bpy.data.collections['STUDIO']


def mat(name, color, roughness=.45, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def stage_object(obj, name, material=None):
    obj.name = name
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    studio.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


floor_mat = mat('Arena | graphite', (.012, .018, .026), .42)
bpy.ops.mesh.primitive_plane_add(size=200)
stage_object(bpy.context.object, 'Arena floor', floor_mat)
stripe = mat('Arena | warm perimeter', (.43, .17, .035), .6, .18)
# A low-contrast circular training mark emphasizes pivots without hiding legs.
bpy.ops.mesh.primitive_torus_add(major_radius=1.34, minor_radius=.007, major_segments=96, minor_segments=8, location=(0, -.1, .002))
stage_object(bpy.context.object, 'Training perimeter', stripe)


def light(name, location, energy, color, size, target=(0, 0, 1)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


light('Key | soft amber', (2.5, -4, 4.5), 550, (1, .73, .48), 4)
light('Fill | cold steel', (-3, -2, 2.5), 380, (.38, .65, 1), 3)
light('Rim | orange', (-1.8, 2, 2.8), 700, (1, .33, .08), 2)
light('Top | arena', (0, .7, 5), 420, (.65, .78, 1), 3)
scene.world.color = (.025, .025, .025)
if scene.world.use_nodes:
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.022, .035, .06, 1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .35
camera_data = bpy.data.cameras.new('Combat camera')
camera = bpy.data.objects.new('Combat camera', camera_data)
studio.objects.link(camera)
scene.camera = camera
camera.location = (3.6, -6.0, 2.55)
target = Vector((0, -.18, 1.28))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.type, camera_data.ortho_scale = 'ORTHO', 5.35
scene.render.engine = 'BLENDER_EEVEE'
scene.render.film_transparent = False
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = str(OUT / 'frames/frame_')
scene.render.use_file_extension = True
scene.view_settings.view_transform = 'AgX'
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'akhani-combat.blend'))

# Small runnable inspection: every frame, actual evaluated mesh, not bone-only.
from bpy_extras.object_utils import world_to_camera_view
sampled = {}
minimum_z, max_step, clip_margin = 999, 0, 999
previous = None
for frame in range(1, 302):
    scene.frame_set(frame)
    obj = hero.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    points = [obj.matrix_world @ v.co for v in mesh.vertices]
    assert all(math.isfinite(value) for p in points for value in p), frame
    bounds = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]
    minimum_z = min(minimum_z, bounds[2][0])
    contacts = {s: min(points[i].z for i in ids) for s, ids in foot_ids.items()}
    lf, rf = state_at(frame)[12:14]
    expected = {'L': lf.z - .147 + .002, 'R': rf.z - .147 + .002}
    assert all(abs(contacts[s] - expected[s]) < .007 for s in contacts), (frame, contacts, expected)
    assert bounds[2][0] > -.008 and bounds[2][1] < 2.8, (frame, bounds)
    for x in bounds[0]:
        for y in bounds[1]:
            for z in bounds[2]:
                uv = world_to_camera_view(scene, camera, Vector((x, y, z)))
                clip_margin = min(clip_margin, uv.x, uv.y, 1 - uv.x, 1 - uv.y)
    if previous:
        max_step = max(max_step, max((points[i] - previous[i]).length for i in range(len(points))))
    previous = points
    if frame in [1, 240, 265, 301] + [f for f, _ in HITS]:
        sampled[str(frame)] = {'bounds': bounds, 'contact_z': contacts}
    if frame == 1:
        first = points
    if frame == 301:
        closure = max((a - b).length for a, b in zip(first, points))
    obj.to_mesh_clear()
assert closure < .00001, closure
assert clip_margin > .015, clip_margin
glb = (WEB / 'akhani-combat.glb').read_bytes()
gltf = json.loads(glb[20:20 + struct.unpack_from('<I', glb, 12)[0]])
assert [a['name'] for a in gltf['animations']] == ['Combat_Combo']
time_accessors = [gltf['accessors'][s['input']] for s in gltf['animations'][0]['samplers']]
assert min(a['min'][0] for a in time_accessors) == 0
assert max(a['max'][0] for a in time_accessors) == 10
assert min(sampled['215']['contact_z'].values()) > .45
assert min(sampled['240']['contact_z'].values()) > .40
assert max(sampled['265']['contact_z'].values()) < .009
report = {'status': 'passed', 'frames': 300, 'fps': 30, 'duration_seconds': 10,
    'glb_timing_seconds': [0, 10],
    'animation': 'Combat_Combo', 'hits': [{'frame': f, 'time': (f - 1) / 30, 'name': n} for f, n in HITS],
    'min_mesh_z_m': minimum_z, 'camera_margin': clip_margin, 'max_vertex_step_m': max_step,
    'loop_error_m': closure, 'sampled_frames': sampled, 'glb_bytes': (WEB / 'akhani-combat.glb').stat().st_size}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print('COMBAT_VALIDATION', json.dumps(report), flush=True)

if '--render' in sys.argv:
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)
else:
    for frame in [1, 24, 95, 175, 215, 240, 265]:
        scene.frame_set(frame)
        scene.render.filepath = str(OUT / f'pose-{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
    # Transparent poster matches the same combat-ready hero shown in the viewer.
    scene.frame_set(1)
    for obj in studio.objects:
        if obj.type == 'MESH':
            obj.hide_render = True
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = 900, 1200
    scene.render.image_settings.color_mode = 'RGBA'
    camera_data.ortho_scale = 2.12
    camera.location = (1.5, -6, 2.15)
    camera.rotation_euler = (Vector((0, -.09, .96)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(WEB / 'akhani-combat-poster.png')
    bpy.ops.render.render(write_still=True)
print('COMBAT_DONE', flush=True)
