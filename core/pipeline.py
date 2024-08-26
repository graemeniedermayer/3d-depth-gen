from timeit import default_timer as timer
from core.depth_wrapper import use_depth_api
from core.image_preprocess import use_pinch_depth, image_double
from core.normalmap_gen import create_normalmap, create_tangent_normal
from core.blender_component import blender_pipeline
import numpy as np
from PIL import Image, ImageOps

def pipeline(opts):
    # opts required 

    # Ensure black behind alpha. For Layered Diffusion
    numpy_image = np.array(opts['image'])
    image = opts['image']
    total_start = timer()
    if numpy_image.shape[2]>3:
        alpha_channel = np.array(opts['image'])[:,:,3]
        rgb_channel = np.array(opts['image'])[:,:,:3]
        alpha_mask = 10 > alpha_channel
        numpy_image[alpha_mask] = 0
        image = Image.fromarray(numpy_image)
        rgb_image = Image.fromarray(rgb_channel)

    # one at a time (see process), all at once (quicker)
    # 1. generate with api (startup stop)
    # 2. depth gen (zoedepth)
    # depth measurements mixing 4 parts 512/ 1 part 768 0.1/ 1 part 1024 (low res high rest) 
    # scale 0.2 depth
    if 'depth_image' in opts:
        depth_bg_removed = opts['depth_image']
    else:
        print('starting depth')
        start = timer()
        total_start = timer()
        depth_bg_removed = use_depth_api(rgb_image, opts['depth_model'], opts['remove_bg'])
        end = timer()
        print('bg removed')
        print(end - start)
    #This cut is usually correct but for intentionally transparent objects is likely the wrong choice
    # if numpy_image.shape[2]>3:
    #     depth_arr = np.array(depth_bg_removed)
    #     depth_arr[alpha_mask] = 0
    #     depth_bg_removed = Image.fromarray(depth_arr)


    def addBorder(image,size):
        return ImageOps.expand(image,border=size,fill='black')        

    # 3. normalmap gen
    # tangent normal maps
    if opts['calc_normal_map']:
        start = timer()
        normalmap = create_normalmap(np.array(depth_bg_removed))
        tangentmap, reduced_depth = create_tangent_normal(
            np.array(normalmap), 
            np.array(depth_bg_removed), 
            opts['reduced_size'],
            opts['pre_scale'],
            True
        )
        end = timer()
        print('normal preprocess')
        print(end - start)

    else:

        # extra conversion should clone object
        reduced_depth = np.array(Image.fromarray(np.array(depth_bg_removed)).resize(opts['reduced_size']))
        # TODO non-ideal. used as filler
        tangentmap = np.array(depth_bg_removed)
    
    # ensures that there are no edges  
    # todo fix inconsistencies with numpy/pil images
    reduce_factor = int(tangentmap.shape[0]/opts['reduced_size'][0])
    tangentmap = np.array(addBorder(Image.fromarray(tangentmap), reduce_factor))
    reduced_depth = np.array(addBorder(Image.fromarray(reduced_depth), 1))
    image = addBorder(image, reduce_factor)
    depth_bg_removed = addBorder(depth_bg_removed, reduce_factor)

    # tangentmap = opts['image']
    # reduced_depth = np.array(opts['image'].resize(opts["grid_size"]))
    if opts['double_sided']:
        tangentmap = np.array(image_double(Image.fromarray(tangentmap)))
        image = image_double(image)
        reduced_depth = np.array(image_double(Image.fromarray(reduced_depth)))
        depth_bg_removed = image_double(depth_bg_removed)
    else:
        half = int(reduced_depth.shape[1]/2)
        reduced_depth[:, half] = 0
        reduced_depth[:, half - 1] = 0
        reduced_depth[:, half + 1] = 0

    # 4. blender component (3d mesh) (single mesh)
    # gen create grid -> modifier add displacements.
    # add shaders
    # cut and boolean modifier
    # move orgin
    start = timer()
    # save texture images
    height = int(reduced_depth.shape[0])
    width = int(reduced_depth.shape[1])
    blender_out = blender_pipeline({
        'image': image,
        'use_normal_map': opts['calc_normal_map'],
        'tangent_image':tangentmap, 
        'depth_image': depth_bg_removed,
        'reduced_depth':reduced_depth, 
        'width': width,
        'height': height,
        'file_name': opts['file_name'],
        'file_type': opts['file_type'],
        'rigging': opts['rigging'],
        'scale': opts['pre_scale']
    })
    end = timer()
    print('blender component')
    print(end - start)
    total_end = timer()
    print('gen3d total time')
    print(total_end- total_start)
    # 5. Rigging automated
    # if opts["rigging_enabled"]:
    #     start = timer()
    #     rigging_out = rigging_pipeline(blender_out)
    #     end = timer()
    #     print('rigging component')
    #     print(end - start)

    return opts['file_name']
    # final scale
