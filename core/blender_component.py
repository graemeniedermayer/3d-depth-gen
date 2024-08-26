
from PIL import Image
import shutil
import numpy as np
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

def add_material(texture_image, tangentmap, obj, isAlpha = False, useNormalMap = True):
    # normal maps 
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

    # set specular to zero 
    mat.node_tree.nodes["Principled BSDF"].inputs[12].default_value = 0
    mat.node_tree.links.new(image_node.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])

    # create node and assing the texture to it
    if useNormalMap:
        tangent_image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tangent_image_node.image = bpy.data.images.load(tangentmap)
        tangent_image_node.image.colorspace_settings.name = 'Non-Color'

        tangent_node = mat.node_tree.nodes.new("ShaderNodeNormalMap")

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
    mod.use_hole_tolerant = True

    with bpy.context.temp_override(active_object=obj):
        bpy.ops.object.modifier_apply(modifier="Boolean")

    # delete extra mesh. This need to be last to avoid path
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["Grid.001"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Grid.001"]
    bpy.ops.object.delete() 


def clean_mesh(rigging = False):
    import bpy
    bpy.ops.object.select_all(action='DESELECT')
    grid = bpy.data.objects["Grid"]
    grid.select_set(True)   

    # flip normals back
    if not rigging:
        grid.location[0] = 0
        grid.location[1] = 0
        grid.location[2] = 0.5

    bpy.context.view_layer.objects.active = bpy.data.objects["Grid"]
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.editmode_toggle()
    if not rigging:
        bpy.context.view_layer.objects.active = bpy.data.objects["Grid"]
        # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', centreduced_er='MEDIAN')

def image_cut(reduced_depth_image):
    import bmesh,bpy
    import numpy as np
    import cv2
    from PIL import Image

    ob = bpy.context.active_object
    me = ob.data
    bm = bmesh.from_edit_mesh(me)

    # image = bpy.data.images.load('/media/grae/Secondary/Arts/aiToGameAssets/buildings/elvenHouse.small.png')
    np_array = np.asarray(reduced_depth_image.pixels)
    # pick out alpha
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51,51))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    erode = cv2.morphologyEx(Image.fromarray(np_array), cv2.MORPH_ERODE, kernel)

    alpha = np_array.reshape(128,128,4)[:,:]
    alpha = np_array.reshape(128,128,4)[:,:]<2
    alphaOrig = np.array(alpha)
    alphaOrig[1:,:] = alpha[:-1,:]|alpha[1:,:]
    alphaOrig[:-1,:] = alpha[:-1,:]|alpha[1:,:]
    alphaOrig[:,1:] = alpha[:,1:]|alpha[:,:-1]
    alphaOrig[:,:-1] = alpha[:,:-1]|alpha[:,1:]
    alpha = alphaOrig.flatten()

    faces_select = []
    for i, face in enumerate(bm.faces):
        if alpha[i]:
            faces_select.append(face)

    bmesh.ops.delete(bm, geom=faces_select, context='FACES')  
    bmesh.update_edit_mesh(me)

def save_mesh_fbx(filename, filetype = 'fbx'):
    import bpy
    if filetype == 'fbx':
        # bpy.ops.export_scene.fbx(filepath=filename, path_mode="COPY", embed_textures=True)
        bpy.ops.export_scene.fbx(filepath=filename)
    # glb really doesn't like alpha channels
    elif filetype == 'glb':
        # TODO hacky way to include all animations otherwise enum issue? (save fbx)
        # BLENDER ISSUE
        #         **Page Information**
        # Blender Version:  4.2.0

        # **Short description of issue**
        # ```
        # bpy.ops.export_scene.fbx(filepath=filename + '.fbx')
        # bpy.ops.export_scene.gltf(filepath=filename + '.glb')
        # ```
        # exports all animations to gltf file whereas
        # ```
        # bpy.ops.export_scene.gltf(filepath=filename+ '.glb')
        # bpy.ops.export_scene.fbx(filepath=filename + '.fbx')
        # ```
        # only keeps one animation for the gltf file.

        # This isn't only an api issues it exists while manual saving gltf files and glb
        # bpy.ops.export_scene.fbx(filepath=filename)
        bpy.ops.export_scene.gltf(filepath=filename)
        # , export_animations = True, export_anim_single_armature = True,
                                #   export_reset_pose_bones = True,
                                #   export_animation_mode='ACTIONS', export_optimize_animation_size = True, 
                                #   export_force_sampling=True,
                                #   export_optimize_animation_keep_anim_armature= True, export_bake_animation= True)
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
    add_material(image, tangent_image, bpy.data.objects["Grid"], isAlpha, blender_pipe['use_normal_map'])
    cut_middle(blender_pipe['width'], blender_pipe['height'])
    # save_mesh_fbx(blender_pipe['file_name']+'inbetween.fbx', blender_pipe['file_type'])
    boolean_union()
    clean_mesh(blender_pipe['rigging'])
    if blender_pipe['rigging']:
        auto_rigging_pipeline(blender_pipe['file_name'])
    else:
        bpy.context.object.rotation_euler[0] = 1.5708
    save_mesh_fbx(blender_pipe['file_name'], blender_pipe['file_type'])
    clear_blender()
    bpy.ops.wm.quit_blender()
    

def auto_rigging_pipeline(filename):
    # run openpose first?
    import bpy
    import os

    grid = bpy.data.objects["Grid"]
    grid.location[0] = 0.5
    bpy.ops.import_scene.gltf( filepath =  os.path.join(
        os.path.dirname(__file__),os.path.join('templates','templateFull1.glb')) )
    
    arma = bpy.data.objects["Armature"]
    bpy.ops.object.select_all(action='DESELECT') 
    grid.select_set(True) 
    arma.select_set(True)   
    # bpy.context.scene.objects.active = arma
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    weight_painting()

    # Removes default pose used for weight painting 
    from .blender_funcs import rename_strips, delete_all_keyframes
    # set_initial_frame(arma, -1)
    delete_all_keyframes(arma, 1)
    delete_all_keyframes(arma, 0.8)
    delete_all_keyframes(arma, 1.8)
    rename_strips(arma)
    # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # mat = arma.matrix_local
    # Matrix = arma.data.transform(mat)
    # arma.matrix_local = Matrix()

def blender_auto_rigging(filename):
    import bpy
    grid = bpy.data.objects["Grid"]
    bpy.ops.object.select_all(action='DESELECT') 
    arma = bpy.data.objects["Armature"]
    arma.select_set(True)   
    bpy.ops.object.posemode_toggle()
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.posemode_toggle()

    bpy.ops.object.select_all(action='DESELECT') 
    grid.select_set(True) 
    arma.select_set(True)   
    # bpy.context.scene.objects.active = arma
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
    # bpy.context.object.rotation_euler[0] = -1.5708

def kdtree_to_vectices(obj, point):
    import bpy 
    import mathutils
    mesh = obj.data
    size = len(mesh.vertices)
    kd = mathutils.kdtree.KDTree(size)
    for i, v in enumerate(mesh.vertices):
        kd.insert(v.co, i)
    kd.balance()
    co_find = (point[0], point[1], point[2])
    co, index, dist = kd.find(co_find)
    
    return dist, index

def kdtree_to_points(kd_points, obj):
    import bpy 
    import mathutils
    size = len(kd_points)
    kd = mathutils.kdtree.KDTree(size)
    for i, v in enumerate(kd_points):
        kd.insert((v[0],v[1],v[2]), i)
    kd.balance()
    i_d = []
    mesh = obj.data
    print(kd_points)
    for i, v in enumerate(mesh.vertices):
        if i % 1000 == 0:
            print(v.co)
            
        co, index, dist = kd.find(v.co)
        i_d.append([index, dist, v.index])    
    return i_d


def raycasted_rigging():
    pass

def nearest_point_bpy():
    pass

def open_pose_to_mixamo():
    pass

def armature_to_positions():
    import bpy
    arma = bpy.data.objects["Armature"]
    arma_pos_dic = {}
    for bone_key in arma.pose.bones.keys():
        arma_pos_dic[bone_key] = [list(arma.pose.bones[bone_key].head*0.01 + arma.location), list(arma.pose.bones[bone_key].tail*0.01 + arma.location)]
    return arma_pos_dic

def weight_painting():
    # default_mixamo = {'mixamorig:Hips': [0.0033414363861083984, 0.0922660231590271, 0.03514666110277176], 'mixamorig:Spine': [0.0033414363861083984, 0.1827908158302307, 0.03569098934531212], 
    #                 'mixamorig:Spine1': [0.0033414363861083984, 0.2884030342102051, 0.03632603958249092], 'mixamorig:Spine2': [0.0033414363861083984, 0.4091026186943054, 0.03705180808901787], 
    #                 'mixamorig:Neck': [0.0033414363861083984, 0.5448898077011108, 0.03786829859018326], 'mixamorig:Head': [0.0033414363861083984, 0.6565576791763306, 0.030981842428445816], 
    #                 'mixamorig:HeadTop_End': [0.0033414363861083984, 0.8350178003311157, 0.019976375624537468], 'mixamorig:LeftShoulder': [0.05772370100021362, 0.5151323080062866, 0.03888464719057083], 
    #                 'mixamorig:LeftArm': [0.1662139892578125, 0.45878201723098755, 0.04091734439134598], 'mixamorig:LeftForeArm': [0.25209006667137146, 0.161282479763031, 0.03470224142074585], 
    #                 'mixamorig:LeftHand': [0.35935407876968384, -0.09707263112068176, 0.037286218255758286], 'mixamorig:LeftHandIndex1': [0.3633813261985779, -0.10808563232421875, 0.04404895752668381], 
    #                 'mixamorig:LeftHandIndex2': [0.37801334261894226, -0.13390907645225525, 0.048051413148641586], 'mixamorig:LeftHandIndex3': [0.39421480894088745, -0.17578023672103882, 0.04788880795240402], 
    #                 'mixamorig:LeftHandIndex4': [0.39773496985435486, -0.21089014410972595, 0.0679498165845871], 'mixamorig:RightShoulder': [-0.051040828227996826, 0.5151323080062866, 0.03685195371508598], 
    #                 'mixamorig:RightArm': [-0.1595311164855957, 0.45878201723098755, 0.034819260239601135], 'mixamorig:RightForeArm': [-0.24540716409683228, 0.16128265857696533, 0.03082195483148098], 
    #                 'mixamorig:RightHand': [-0.35267114639282227, -0.09707260131835938, 0.039637982845306396], 'mixamorig:RightHandIndex1': [-0.37746918201446533, -0.14255595207214355, 0.040976013988256454], 
    #                 'mixamorig:RightHandIndex2': [-0.3837234377861023, -0.16237929463386536, 0.037580933421850204], 'mixamorig:RightHandIndex3': [-0.3817182779312134, -0.19681835174560547, 0.045161012560129166],
    #                 'mixamorig:RightHandIndex4': [-0.3865465521812439, -0.21542006731033325, 0.047281231731176376], 'mixamorig:LeftUpLeg': [0.09038519859313965, 0.04194808006286621, 0.04006670042872429], 
    #                 'mixamorig:LeftLeg': [0.12314572930335999, -0.402015745639801, 0.05845637246966362], 'mixamorig:LeftFoot': [0.13205984234809875, -0.8847541809082031, 0.045720916241407394], 
    #                 'mixamorig:LeftToeBase': [0.13844382762908936, -0.921697735786438, 0.07487259805202484], 'mixamorig:LeftToe_End': [0.14193853735923767, -0.9252091646194458, 0.0976247563958168], 
    #                 'mixamorig:RightUpLeg': [-0.08370232582092285, 0.04194808006286621, 0.040921472012996674], 'mixamorig:RightLeg': [-0.11646288633346558, -0.4020158052444458, 0.029600409790873528], 
    #                 'mixamorig:RightFoot': [-0.1253771185874939, -0.8847520351409912, 0.052390191704034805], 'mixamorig:RightToeBase': [-0.13176089525222778, -0.9216904640197754, 0.05161752924323082], 
    #                 'mixamorig:RightToe_End': [-0.1352553367614746, -0.9251959323883057, 0.06189439818263054]}

    size_of_body_part = {'Toe':4,'Hand':4, "Index":2, "Foot":7, "Head":10, "Top_End":4}
    default_mixamo = {'mixamorig:Hips': [[0.0053452616557478905, 0.06783605366945267, 0.05235214903950691], [0.0053452616557478905, 0.06783605366945267, -0.07598820328712463]], 'mixamorig:Spine': [[0.0053452616557478905, 0.06804865598678589, -0.04255196452140808], [0.0053452616557478905, 0.06829670071601868, -0.15327341854572296]], 'mixamorig:Spine1': [[0.0053452616557478905, 0.06829670071601868, -0.15327341854572296], [0.005345261190086603, 0.06858016550540924, -0.2798122465610504]], 'mixamorig:Spine2': [[0.005345261190086603, 0.06858016550540924, -0.2798122763633728], [0.005345261190086603, 0.06892745196819305, -0.4348411560058594]], 'mixamorig:Neck': [[0.005345261190086603, 0.06889906525611877, -0.42216840386390686], [0.005345261190086603, 0.06889906525611877, -0.6032448410987854]], 'mixamorig:Head': [[0.0053452616557478905, 0.05948483198881149, -0.6029999256134033], [0.0053452616557478905, 0.05948483198881149, -0.8646137714385986]], 'mixamorig:HeadTop_End': [[0.0053452616557478905, 0.045883432030677795, -0.8642600178718567], [0.0053452616557478905, 0.045883432030677795, -1.1258738040924072]], 'mixamorig:LeftShoulder': [[0.06146799027919769, 0.07003555446863174, -0.43109914660453796], [0.16364745795726776, 0.07230853289365768, -0.473489373922348]], 'mixamorig:LeftArm': [[0.16364745795726776, 0.07230852544307709, -0.473489373922348], [0.24918441474437714, 0.07221300154924393, -0.23770315945148468]], 'mixamorig:LeftForeArm': [[0.24918441474437714, 0.07221299409866333, -0.2377031445503235], [0.38763904571533203, 0.06966884434223175, 0.06756126135587692]], 'mixamorig:LeftHand': [[0.38763904571533203, 0.06966883689165115, 0.06756126135587692], [0.39849063754081726, 0.07130726426839828, 0.07129859179258347]], 'mixamorig:LeftHandIndex1': [[0.39849063754081726, 0.07130725681781769, 0.07129859179258347], [0.4029403328895569, 0.07113944739103317, 0.07840202003717422]], 'mixamorig:LeftHandIndex2': [[0.4029403328895569, 0.07113943994045258, 0.07840202003717422], [0.4080376625061035, 0.07094719260931015, 0.08653944730758667]], 'mixamorig:LeftHandIndex3': [[0.4051356017589569, 0.07134781032800674, 0.08774949610233307], [0.4078255295753479, 0.07124637067317963, 0.0920436829328537]], 'mixamorig:LeftHandIndex4': [[0.40630272030830383, 0.07030736654996872, 0.09257044643163681], [0.4089926481246948, 0.070205919444561, 0.09686464071273804]], 'mixamorig:RightShoulder': [[-0.05077747255563736, 0.0677625760436058, -0.43109914660453796], [-0.15295693278312683, 0.06548959761857986, -0.473489373922348]], 'mixamorig:RightArm': [[-0.15295696258544922, 0.06548959761857986, -0.473489373922348], [-0.23849385976791382, 0.06090879440307617, -0.2377031147480011]], 'mixamorig:RightForeArm': [[-0.2384938895702362, 0.06090879440307617, -0.2377030849456787], [-0.3769484758377075, 0.06747686862945557, 0.06756135821342468]], 'mixamorig:RightHand': [[-0.3769485056400299, 0.06747686862945557, 0.06756139546632767], [-0.37036171555519104, 0.06786391884088516, 0.08379904925823212]], 'mixamorig:RightHandIndex1': [[-0.3703617453575134, 0.06786391884088516, 0.0837990865111351], [-0.3792797327041626, 0.06821344047784805, 0.10047177970409393]], 'mixamorig:RightHandIndex2': [[-0.379279762506485, 0.06821344047784805, 0.10047181695699692], [-0.3920004665851593, 0.06871199607849121, 0.12425409257411957]], 'mixamorig:RightHandIndex3': [[-0.38883933424949646, 0.07248527556657791, 0.1253320276737213], [-0.3964940309524536, 0.07278528809547424, 0.13964293897151947]], 'mixamorig:RightHandIndex4': [[-0.39341315627098083, 0.07364591211080551, 0.1408633142709732], [-0.401067852973938, 0.07394591718912125, 0.15517422556877136]], 'mixamorig:LeftUpLeg': [[0.14043229818344116, 0.06303007900714874, 0.10509558767080307], [0.12139645963907242, 0.07634232193231583, 0.5444207787513733]], 'mixamorig:LeftLeg': [[0.12139645963907242, 0.07634232193231583, 0.5444207787513733], [0.1302471160888672, 0.08562898635864258, 0.9239494204521179]], 'mixamorig:LeftFoot': [[0.1302471160888672, 0.08562898635864258, 0.9239494204521179], [0.1322653591632843, 0.09195560216903687, 0.9232555031776428]], 'mixamorig:LeftToeBase': [[0.1322653591632843, 0.09195560216903687, 0.9232555031776428], [0.13781890273094177, 0.1100168377161026, 0.9288330674171448]], 'mixamorig:LeftToe_End': [[0.13781890273094177, 0.1100168377161026, 0.9288330674171448], [0.14337243139743805, 0.12807807326316833, 0.9344104528427124]], 'mixamorig:RightUpLeg': [[-0.12974177300930023, 0.0679483562707901, 0.10509558767080307], [-0.11070594191551208, 0.07732252776622772, 0.5444207191467285]], 'mixamorig:RightLeg': [[-0.11070594191551208, 0.07732252776622772, 0.5444207191467285], [-0.11955656856298447, 0.06542704999446869, 0.9239488244056702]], 'mixamorig:RightFoot': [[-0.11955656856298447, 0.06542704999446869, 0.9239488244056702], [-0.12157484889030457, 0.07819001376628876, 0.9232556223869324]], 'mixamorig:RightToeBase': [[-0.12157484889030457, 0.07819001376628876, 0.9232556223869324], [-0.12712834775447845, 0.08008856326341629, 0.9288328886032104]], 'mixamorig:RightToe_End': [[-0.12712834775447845, 0.08008856326341629, 0.9288328886032104], [-0.1326819360256195, 0.0819871723651886, 0.9344100952148438]]}
    default_mixamo ={'mixamorig:Hips': [[-0.00014307498349808156, 0.03514666110277176, -0.0945964828133583], [-0.00014307498349808156, 0.03514666482806206, -0.19189472496509552]], 'mixamorig:Spine': [[-0.00014307498349808156, 0.03569098934531212, -0.18512126803398132], [-0.00014307498349808156, 0.03632604330778122, -0.2907334566116333]], 'mixamorig:Spine1': [[-0.00014307498349808156, 0.03632604330778122, -0.2907334566116333], [-0.00014307498349808156, 0.037051811814308167, -0.41143307089805603]], 'mixamorig:Spine2': [[-0.00014307498349808156, 0.037051811814308167, -0.41143307089805603], [-0.00014307498349808156, 0.037801679223775864, -0.5361405611038208]], 'mixamorig:Neck': [[-0.00014307498349808156, 0.037868306040763855, -0.5472201704978943], [-0.00014307498349808156, 0.037868306040763855, -0.659100353717804]], 'mixamorig:Head': [[-0.00014307498349808156, 0.030981849879026413, -0.6588881015777588], [-0.00014307498349808156, 0.030981851741671562, -0.8376873731613159]], 'mixamorig:HeadTop_End': [[-0.00014307498349808156, 0.019976384937763214, -0.8373482823371887], [-0.00014307498349808156, 0.019976388663053513, -1.016147494316101]], 'mixamorig:LeftShoulder': [[0.054239172488451004, 0.03888465464115143, -0.5174627304077148], [0.16272947192192078, 0.04091734439134598, -0.46111246943473816]], 'mixamorig:LeftArm': [[0.16272947192192078, 0.040917348116636276, -0.46111249923706055], [0.24860554933547974, 0.03470224142074585, -0.16361293196678162]], 'mixamorig:LeftForeArm': [[0.24860556423664093, 0.03470224514603615, -0.1636129468679428], [0.3558695614337921, 0.03728621453046799, 0.09474223852157593]], 'mixamorig:LeftHand': [[0.3558695912361145, 0.037286218255758286, 0.09474223852157593], [0.35989683866500854, 0.04404888674616814, 0.1057552695274353]], 'mixamorig:LeftHandIndex1': [[0.35989683866500854, 0.04404895752668381, 0.10575523227453232], [0.37452879548072815, 0.04805140569806099, 0.13157866895198822]], 'mixamorig:LeftHandIndex2': [[0.37452882528305054, 0.04805140942335129, 0.13157868385314941], [0.39646342396736145, 0.054051417857408524, 0.17029021680355072]], 'mixamorig:LeftHandIndex3': [[0.3907302916049957, 0.04788879677653313, 0.17344985902309418], [0.4105607569217682, 0.053313255310058594, 0.20844796299934387]], 'mixamorig:LeftHandIndex4': [[0.3942504823207855, 0.0679498016834259, 0.20855973660945892], [0.414080947637558, 0.07337425649166107, 0.24355782568454742]], 'mixamorig:RightShoulder': [[-0.05452532321214676, 0.03685196116566658, -0.5174627304077148], [-0.16301560401916504, 0.034819263964891434, -0.46111246943473816]], 'mixamorig:RightArm': [[-0.16301560401916504, 0.03481926769018173, -0.46111246943473816], [-0.2488916963338852, 0.03082195483148098, -0.16361308097839355]], 'mixamorig:RightForeArm': [[-0.2488916963338852, 0.03082195855677128, -0.16361308097839355], [-0.356155663728714, 0.039637982845306396, 0.09474212676286697]], 'mixamorig:RightHand': [[-0.356155663728714, 0.039637986570596695, 0.09474214166402817], [-0.38095369935035706, 0.040976010262966156, 0.14022548496723175]], 'mixamorig:RightHandIndex1': [[-0.38095369935035706, 0.040976013988256454, 0.14022549986839294], [-0.3872079849243164, 0.03758092597126961, 0.16004882752895355]], 'mixamorig:RightHandIndex2': [[-0.3872079849243164, 0.037580929696559906, 0.16004884243011475], [-0.3976965546607971, 0.0318874754011631, 0.19329188764095306]], 'mixamorig:RightHandIndex3': [[-0.3852028250694275, 0.045161012560129166, 0.19448788464069366], [-0.39094433188438416, 0.04204434156417847, 0.21268552541732788]], 'mixamorig:RightHandIndex4': [[-0.3900310695171356, 0.04728122428059578, 0.21308963000774384], [-0.3957725763320923, 0.044164564460515976, 0.23128724098205566]], 'mixamorig:LeftUpLeg': [[0.08690068870782852, 0.04006670042872429, -0.04427848756313324], [0.11966123431921005, 0.05845636874437332, 0.3996853232383728]], 'mixamorig:LeftLeg': [[0.11966123431921005, 0.05845636874437332, 0.3996853232383728], [0.12857533991336823, 0.0457209050655365, 0.8824236989021301]], 'mixamorig:LeftFoot': [[0.12857533991336823, 0.0457209050655365, 0.8824236989021301], [0.13495931029319763, 0.07487259060144424, 0.9193671941757202]], 'mixamorig:LeftToeBase': [[0.13495931029319763, 0.07487259060144424, 0.9193671941757202], [0.13845403492450714, 0.0976247489452362, 0.9228786826133728]], 'mixamorig:LeftToe_End': [[0.13845403492450714, 0.0976247489452362, 0.9228786826133728], [0.14194875955581665, 0.12037691473960876, 0.9263902306556702]], 'mixamorig:RightUpLeg': [[-0.08718682825565338, 0.040921472012996674, -0.04427848756313324], [-0.11994737386703491, 0.02960040234029293, 0.3996853828430176]], 'mixamorig:RightLeg': [[-0.11994737386703491, 0.02960040234029293, 0.3996853530406952], [-0.12886163592338562, 0.05239018425345421, 0.8824217319488525]], 'mixamorig:RightFoot': [[-0.12886163592338562, 0.05239018425345421, 0.882421612739563], [-0.13524538278579712, 0.05161752179265022, 0.9193601608276367]], 'mixamorig:RightToeBase': [[-0.13524538278579712, 0.05161752179265022, 0.9193601012229919], [-0.13873982429504395, 0.061894387006759644, 0.9228655695915222]], 'mixamorig:RightToe_End': [[-0.13873982429504395, 0.061894387006759644, 0.9228655099868774], [-0.14223432540893555, 0.07217127084732056, 0.9263709187507629]]}
    default_mixamo = {'mixamorig:Hips': [[-0.004293136298656464, 0.010969316586852074, -0.05488601699471474], [-0.004293136298656464, 0.0109693119302392, -0.15218424797058105]], 'mixamorig:Spine': [[-0.004293136298656464, 0.011513639241456985, -0.14541080594062805], [-0.004293136298656464, 0.012148686684668064, -0.25102299451828003]], 'mixamorig:Spine1': [[-0.004293136298656464, 0.012148686684668064, -0.25102299451828003], [-0.004293136298656464, 0.012874447740614414, -0.37172260880470276]], 'mixamorig:Spine2': [[-0.004293136298656464, 0.012874447740614414, -0.37172260880470276], [-0.004293136298656464, 0.013624307699501514, -0.49643006920814514]], 'mixamorig:Neck': [[-0.004293136298656464, 0.013690932653844357, -0.507509708404541], [-0.004293136298656464, 0.013690927997231483, -0.6193898320198059]], 'mixamorig:Head': [[-0.004293136298656464, 0.006804472766816616, -0.6191776394844055], [-0.004293136298656464, 0.0068044643849134445, -0.7979767918586731]], 'mixamorig:HeadTop_End': [[-0.004293136298656464, -0.0042010024189949036, -0.7976377606391907], [-0.004293136298656464, -0.004201009403914213, -0.9764369130134583]], 'mixamorig:LeftShoulder': [[0.05008910968899727, 0.01470728125423193, -0.47775229811668396], [0.17043565213680267, 0.0167399775236845, -0.456253319978714]], 'mixamorig:LeftArm': [[0.17043565213680267, 0.0167399775236845, -0.456253319978714], [0.34098106622695923, 0.010524886660277843, -0.19780614972114563]], 'mixamorig:LeftForeArm': [[0.34098106622695923, 0.010524886660277843, -0.19780614972114563], [0.5202918648719788, 0.013108870945870876, 0.01690441183745861]], 'mixamorig:LeftHand': [[0.5202918648719788, 0.013108870945870876, 0.01690441183745861], [0.5274150967597961, 0.0198715440928936, 0.02621925249695778]], 'mixamorig:LeftHandIndex1': [[0.5274149775505066, 0.019871611148118973, 0.02621922828257084], [0.5490710139274597, 0.023874063044786453, 0.046516094356775284]], 'mixamorig:LeftHandIndex2': [[0.5490710139274597, 0.023874063044786453, 0.046516094356775284], [0.5815352201461792, 0.029874077066779137, 0.07694283127784729]], 'mixamorig:LeftHandIndex3': [[0.5770025253295898, 0.02371145598590374, 0.08166593313217163], [0.6063526272773743, 0.029135920107364655, 0.1091739758849144]], 'mixamorig:LeftHandIndex4': [[0.590815007686615, 0.04377247393131256, 0.11413609236478806], [0.6201650500297546, 0.04919692873954773, 0.14164412021636963]], 'mixamorig:RightShoulder': [[-0.058675382286310196, 0.012674588710069656, -0.4777522683143616], [-0.17465917766094208, 0.01064190361648798, -0.43910959362983704]], 'mixamorig:RightArm': [[-0.17465917766094208, 0.01064190361648798, -0.43910959362983704], [-0.3061191737651825, 0.006644613109529018, -0.15875476598739624]], 'mixamorig:RightForeArm': [[-0.3061191737651825, 0.006644613109529018, -0.15875476598739624], [-0.4525649845600128, 0.015460657887160778, 0.07958661764860153]], 'mixamorig:RightHand': [[-0.4525649845600128, 0.015460657887160778, 0.07958661764860153], [-0.4841878414154053, 0.016798686236143112, 0.12061921507120132]], 'mixamorig:RightHandIndex1': [[-0.4841878414154053, 0.016798686236143112, 0.12061921507120132], [-0.4934729337692261, 0.013403605669736862, 0.13921673595905304]], 'mixamorig:RightHandIndex2': [[-0.4934729337692261, 0.013403605669736862, 0.13921673595905304], [-0.5090441107749939, 0.007710156496614218, 0.1704040914773941]], 'mixamorig:RightHandIndex3': [[-0.49689242243766785, 0.020983686670660973, 0.17354422807693481], [-0.505416214466095, 0.01786702498793602, 0.19061656296253204]], 'mixamorig:RightHandIndex4': [[-0.50457763671875, 0.023103903979063034, 0.19115886092185974], [-0.5131013989448547, 0.01998724974691868, 0.20823118090629578]], 'mixamorig:LeftUpLeg': [[0.08275062590837479, 0.015889355912804604, -0.004568023607134819], [0.11551116406917572, 0.03427904471755028, 0.4393957853317261]], 'mixamorig:LeftLeg': [[0.11551116406917572, 0.03427904471755028, 0.4393957853317261], [0.12442527711391449, 0.021543607115745544, 0.9221342206001282]], 'mixamorig:LeftFoot': [[0.12442527711391449, 0.021543607115745544, 0.9221342206001282], [0.1308092474937439, 0.05069529265165329, 0.9590778350830078]], 'mixamorig:LeftToeBase': [[0.1308092474937439, 0.05069529265165329, 0.9590778350830078], [0.1343039721250534, 0.07344745099544525, 0.9625893235206604]], 'mixamorig:LeftToe_End': [[0.1343039721250534, 0.07344745099544525, 0.9625893235206604], [0.13779868185520172, 0.09619962424039841, 0.9661007523536682]], 'mixamorig:RightUpLeg': [[-0.09133689850568771, 0.016744129359722137, -0.004568023607134819], [-0.12409743666648865, 0.00542308297008276, 0.43939584493637085]], 'mixamorig:RightLeg': [[-0.12409743666648865, 0.00542308297008276, 0.43939584493637085], [-0.13301168382167816, 0.028212884441018105, 0.9221320748329163]], 'mixamorig:RightFoot': [[-0.13301168382167816, 0.028212884441018105, 0.9221320748329163], [-0.13939543068408966, 0.027440225705504417, 0.9590705633163452]], 'mixamorig:RightToeBase': [[-0.13939543068408966, 0.027440225705504417, 0.9590705633163452], [-0.14288988709449768, 0.03771709278225899, 0.9625759720802307]], 'mixamorig:RightToe_End': [[-0.14288988709449768, 0.03771709278225899, 0.9625759720802307], [-0.1463843733072281, 0.0479939728975296, 0.9660813212394714]]}
    
    # Head Finetunning
    # default_mixamo['mixamorig:Neck'][0][2]-=0.02
    # default_mixamo['mixamorig:Neck'][1][2]-=0.02
    # default_mixamo['mixamorig:Head'][0][2]-=0.02
    # default_mixamo['mixamorig:Head'][1][2]-=0.02
    # default_mixamo['mixamorig:HeadTop_End'][0][2]-=0.02
    # default_mixamo['mixamorig:HeadTop_End'][1][2]-=0.02
    import bpy, bmesh
    grid = bpy.data.objects["Grid"]
    bpy.ops.object.select_all(action='DESELECT') 
    grid.select_set(True) 
    bpy.context.view_layer.objects.active = grid

    bpy.ops.object.editmode_toggle()
    me = bpy.context.edit_object.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()
    # TODO scaling factor?
    front = np.array([0,0, 0.15])
    offset = np.array([-0.5,0,0])
    back = np.array([0,0,-0.15])
    verts_name = {}

    # earlier attempts
    # for group_label in default_mixamo:
    #     for vert in bm.verts:
    #         vert.select = False
    #     group = grid.vertex_groups[group_label]
    #     vec_head = default_mixamo[group_label][0]
    #     vec_head = np.array([vec_head[0], -vec_head[2], vec_head[1]])
    #     vec_tail = default_mixamo[group_label][1]
    #     vec_tail = np.array([vec_tail[0], -vec_tail[2], vec_tail[1]])

    #     dist, index = kdtree_to_vectices(grid, vec_head+front+offset)
    #     bm.verts[index].select = True
    #     dist, index = kdtree_to_vectices(grid, vec_head+back+offset)
    #     bm.verts[index].select = True
    #     dist, index = kdtree_to_vectices(grid, vec_tail+front+offset)
    #     bm.verts[index].select = True
    #     dist, index = kdtree_to_vectices(grid, vec_tail+back+offset)
    #     bm.verts[index].select = True
    #     bm.verts.index_update()
    #     verts_name[group_label] = []
    #     body_part_size = 15
    #     for body_part, size in size_of_body_part.items(): 
    #         if body_part in group_label:
    #             body_part_size = size
    #     for i in range(body_part_size):
    #         wanted_weight = 0.8/(i+20)
    #         bpy.ops.mesh.select_more()
    #         # bpy.ops.object.editmode_toggle()
    #         verts =  [v.index for v in bm.verts if v.select]
    #         # bm = bmesh.from_edit_mesh(me)
    #         # group.add( vertex_indices, 0., 'ADD' )
    #         verts_name[group_label].append(verts)

        # bpy.ops.mesh.select_all(action='DESELECT')

    # bpy.ops.object.editmode_toggle()
    # for group_label in default_mixamo:

    #     print(group_label)
    #     verts = verts_name[group_label]
    #     verts.reverse()
    #     body_part_size = 15
    #     for body_part, size in size_of_body_part.items(): 
    #         if body_part in group_label:
    #             body_part_size = size
    #     for i in range(body_part_size):
    #         wanted_weight = 0.95* (1 - np.e**(-i/6))
    #         group = grid.vertex_groups[group_label]
    #         group.add( verts[i], wanted_weight, 'REPLACE' )
    print(grid.rotation_euler)
    # 5 points for each line?
    # for i in range(5)
    pose_points = []
    segments = 5
    for point in default_mixamo.values():
        for i in range(segments):
            pose_points.append(i/segments*np.array(point[0]) + (segments-i)/segments*np.array(point[1]))
    
    pose_points = np.array(pose_points)
    print(pose_points.shape)
    # pose_points = np.array([point[1]+point[0] for point in default_mixamo.values()])
    # pose_points = np.array([point[0] for point in default_mixamo.values()])
    pose_points[:,[2,1]] = pose_points[:,[1,2]]
    pose_points[:,1] *= -1
    pose_points = pose_points + offset

    index_distance = kdtree_to_points(pose_points, grid)
    keys = list(default_mixamo.keys())
    # bpy.ops.object.editmode_toggle()
    index_distance = np.array(index_distance)
    index_distance = index_distance[index_distance[:, 0].argsort()]
    
    verts_name = {}
    body_part_size = 4
    for group_index, group_label in enumerate(keys):
        verts_name[group_label] = []
        for vert in bm.verts:
            vert.select = False
        for i in range(segments):
            # numpy is a god
            v_indexs= index_distance[(index_distance[:,0] == segments*group_index+i), 2]
            # v_indexs = v_indexs[:,2] 
            for v_i in v_indexs:
                bm.verts[int(v_i)].select = True
        # overlap?
        bm.verts.index_update()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()

        for j in range(body_part_size):
            bpy.ops.mesh.select_less()
            verts =  [v.index for v in bm.verts if v.select]
            verts_name[group_label].append(verts)


    bpy.ops.object.editmode_toggle()

    for group_label in keys:

        verts = verts_name[group_label]
        # verts.reverse()
        body_part_size = 4
        for i in range(body_part_size):
            wanted_weight = 0.2*i +0.3
            group = grid.vertex_groups[group_label]
            group.add( verts[i], wanted_weight, 'REPLACE' )


    # bpy.ops.object.editmode_toggle()

    # for index, distance, v_index in index_distance:
    #     wanted_weight = 0.95* (1 - np.e**(-distance/2))

    #     group = grid.vertex_groups[ keys[int(np.floor(index/segments))] ]
    #     # print(wanted_weight)
    #     # async?
    #     group.add( [int(v_index)], wanted_weight, 'REPLACE' )