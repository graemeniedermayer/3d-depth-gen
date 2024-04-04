
from PIL import Image
import shutil
def clear_blender():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_grid(width = 256, height = 256, scale=1):
    import bpy
    height_scale= height/width
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=width, y_subdivisions=height, 
                                    enter_editmode=False, align='WORLD', 
                                    location=(0, 0, 0), scale=(scale, scale*height_scale, scale))
    


def saveImages(images, names):
    import os 
    import tempfile
    temp_dir = tempfile.mkdtemp()
    file_names = []
    for image, name in zip(images, names):
        path = os.path.join(temp_dir, name+'.png')
        image.save(path)
        file_names.append(path)

    return file_names


# 512 depth
def depth_modifier(depth_filename, obj, strength = 0.2):
    import bpy
    mod = obj.modifiers.new("Displace", 'DISPLACE')
    mod.strength = strength
    mod.mid_level = 0
    mod.direction = 'Z'

    disTex = bpy.data.textures.new('displacement', type = 'IMAGE')
    bpy.data.images.load(depth_filename)
    disTex.image = bpy.data.images[0]
    mod.texture = disTex
    
    with bpy.context.temp_override(active_object=obj):
        bpy.ops.object.modifier_apply(modifier="Displace")

def add_material(texture_image, tangentmap, obj, isAlpha = False):
    import bpy
    mat = bpy.data.materials.new(name = obj.name)
    obj.data.materials.append(mat)

    # tangent normal
    bpy.data.images.load(tangentmap)
    
    mat.use_nodes = True
    # create node and assing the texture to it
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = bpy.data.images.load(texture_image)
    # image_node.image.interpolation = 'Cubic' this is nodes

    # create node and assing the texture to it
    tangent_image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tangent_image_node.image = bpy.data.images.load(tangentmap)
    tangent_image_node.image.colorspace_settings.name = 'Non-Color'

    tangent_node = mat.node_tree.nodes.new("ShaderNodeNormalMap")

    # set specular to zero 
    mat.node_tree.nodes["Principled BSDF"].inputs[12].default_value = 0

    mat.node_tree.links.new(image_node.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    mat.node_tree.links.new(tangent_image_node.outputs[0], tangent_node.inputs[1])
    mat.node_tree.links.new(tangent_node.outputs[0], mat.node_tree.nodes["Principled BSDF"].inputs[5])
    import numpy as np
    if isAlpha:
        alpha_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        alpha_node.image = bpy.data.images.load(texture_image)
        mat.node_tree.links.new(alpha_node.outputs["Alpha"], mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"])


def find_3d_viewport_area(ctx = None):
    import bpy
    # allow the user to pass in a context, but handle it for them if there isn't one.
    # it is always best to use a local context (ie: from an operator or callback) rather than
    # the global context, but sometimes that's all you've got.
    
    for a in bpy.data.screens['Layout'].areas:
        if a.type == 'VIEW_3D':
            return a
    return None

def cut_middle(width,height):
    import bpy
    import bmesh
    v3d = find_3d_viewport_area()
    # ctx_override.view_layer.objects.active = bpy.data.objects["Grid"]
    # obj = bpy.data.objects["Grid"]
    obj = bpy.data.objects["Grid"]
    
    with bpy.context.temp_override( active_object=obj, mesh = obj.data,
        selected_objects=[obj], selected_editable_objects=[obj], area=v3d):
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.flip_normals()

    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()

    for vert in bm.verts:
        if int(width/2) == ( int(vert.index) % (width + 1) ):
            vert.select = True
        else:
            vert.select = False

    bm.verts[int(width/2)].select = True
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.separate(type='LOOSE')
    #ensure you are selecting the write point
    bpy.ops.object.editmode_toggle()

    grid2 = bpy.data.objects["Grid.001"]
    grid2.rotation_euler[1] = 3.14159
    # overlayer
    grid2.location[2] = 0.08

def seperate_loose():
    import bpy
    import bmesh
    v3d = find_3d_viewport_area()
    # ctx_override.view_layer.objects.active = bpy.data.objects["Grid"]
    # obj = bpy.data.objects["Grid"]
    obj = bpy.data.objects["Grid"]
    
    bpy.ops.object.editmode_toggle()

    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()

    for vert in bm.verts:
        vert.select = True

    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.separate(type='LOOSE')
    #ensure you are selecting the write point
    bpy.ops.object.editmode_toggle()


def position_mesh():
    import bpy
    grid2 = bpy.data.objects["Grid.001"]
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.editmode_toggle()

    grid2 = bpy.data.objects["Grid.001"]
    grid2.rotation_euler[1] = 3.14159
    # overlayer
    # This should be marigold
    grid2.location[2] = 0.08

def boolean_union():
    import bpy
    obj = bpy.data.objects["Grid"]
    mod = obj.modifiers.new("Boolean", 'BOOLEAN')
    mod.operation = 'UNION'
    mod.object = bpy.data.objects["Grid.001"]

    # hole tolerant add complexity. risky...
    # mod.modifiers["Boolean"].use_hole_tolerant = True

    with bpy.context.temp_override(active_object=obj):
        bpy.ops.object.modifier_apply(modifier="Boolean")

    # delete extra mesh. This need to be last to avoid path
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["Grid.001"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Grid.001"]
    bpy.ops.object.delete() 


def clean_mesh():
    import bpy

    # flip normals back
    bpy.ops.object.select_all(action='DESELECT')
    grid = bpy.data.objects["Grid"]
    grid.select_set(True)   
    grid.location[0] = 0
    grid.location[1] = 0
    grid.location[2] = 0.5
    grid.rotation_euler[0] = 1.571

    bpy.context.view_layer.objects.active = bpy.data.objects["Grid"]
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.editmode_toggle()

    bpy.context.view_layer.objects.active = bpy.data.objects["Grid"]
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

def save_mesh_fbx(filename, filetype = 'fbx'):
    import bpy

    # automatic type identification?
    if filetype == 'fbx':
        # bpy.ops.export_scene.fbx(filepath=filename, path_mode="COPY", embed_textures=True)
        bpy.ops.export_scene.fbx(filepath=filename)
    # glb really doesn't like alpha channels
    elif filetype == 'glb':
        bpy.ops.export_scene.gltf(filepath=filename)
    elif filetype == 'obj':
        bpy.ops.wm.obj_export(filepath=filename, embed_textures=True)

def export_file():
    import bpy
    bpy.context.space_data.params.filename = "test.glb"

def setup_blender():
    import bpy
    blender_bin = shutil.which("blender")
    if blender_bin:
       print("Found:", blender_bin)
       bpy.app.binary_path = blender_bin
    else:
       print("Unable to find blender!")

def blender_pipeline(blender_pipe):
    import bpy
    import numpy as np
    isAlpha = np.array(blender_pipe['image']).shape[2] > 3
    print(isAlpha)
    clear_blender()
    # These are now strings (file locations) for blender
    image, depth_image, reduced_depth, tangent_image = saveImages(
        [blender_pipe['image'], blender_pipe['depth_image'], Image.fromarray(
            blender_pipe['reduced_depth']), Image.fromarray(blender_pipe['tangent_image'])],
        ['image','depth_image', 'reduced_depth', 'tangent_image'])
    setup_blender()
    create_grid(blender_pipe['width'], blender_pipe['height'], scale=1)
    obj = bpy.data.objects["Grid"]
    obj.scale[1] = blender_pipe['height']/blender_pipe['width']
    depth_modifier(reduced_depth, bpy.data.objects["Grid"], blender_pipe['scale'])
    add_material(image, tangent_image, bpy.data.objects["Grid"], isAlpha)
    cut_middle(blender_pipe['width'], blender_pipe['height'])
    boolean_union()
    clean_mesh()
    save_mesh_fbx(blender_pipe['file_name'], blender_pipe['file_type'])
    bpy.ops.wm.quit_blender()
    

def rigging_pipeline(blender_pipe):
    import bpy
    # ensure riggify is installed
    bpy.ops.object.armature_basic_human_metarig_add()
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
    bpy.context.object.rotation_euler[0] = -1.5708