
from fastapi import FastAPI, Body
from fastapi.exceptions import HTTPException

from typing import Dict, List
from PIL import Image
import os

import numpy as np
from PIL import PngImagePlugin, Image
import base64
from io import BytesIO
from fastapi.exceptions import HTTPException

from core.pipeline import pipeline
from ui import get_outpath

#model diction TODO find a way to remove without forcing people do know indexes of models
models_to_index = {
    'res101':0, 
    'dpt_beit_large_512 (midas 3.1)':1,
    'dpt_beit_large_384 (midas 3.1)':2, 
    'dpt_large_384 (midas 3.0)':3,
    'dpt_hybrid_384 (midas 3.0)':4,
    'midas_v21':5, 
    'midas_v21_small':6,
    'zoedepth_n (indoor)':7, 
    'zoedepth_k (outdoor)':8, 
    'zoedepth_nk':9,
    'marigold':10 
}

def decode_base64_to_image(encoding):
    if encoding.startswith("data:image/"):
        encoding = encoding.split(";")[1].split(",")[1]
    try:
        image = Image.open(BytesIO(base64.b64decode(encoding)))
        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail="Invalid encoded image") from e

# TODO check that internally we always use png.
def encode_pil_to_base64(image, image_type='png'):
    with BytesIO() as output_bytes:

        if image_type == 'png':
            use_metadata = False
            metadata = PngImagePlugin.PngInfo()
            for key, value in image.info.items():
                if isinstance(key, str) and isinstance(value, str):
                    metadata.add_text(key, value)
                    use_metadata = True
            image.save(output_bytes, format="PNG", pnginfo=(metadata if use_metadata else None))

        else:
            raise HTTPException(status_code=500, detail="Invalid image format")

        bytes_data = output_bytes.getvalue()

    return base64.b64encode(bytes_data)

def encode_to_base64(image):
    if type(image) is str:
        return image
    elif type(image) is Image.Image:
        return encode_pil_to_base64(image)
    elif type(image) is np.ndarray:
        return encode_np_to_base64(image)
    else:
        return ""

def encode_np_to_base64(image):
    pil = Image.fromarray(image)
    return encode_pil_to_base64(pil)

def to_base64_PIL(encoding: str):
    return Image.fromarray(np.array(decode_base64_to_image(encoding)).astype('uint8'))

def to_base64_PIL16(encoding: str):
    return Image.fromarray(np.array(decode_base64_to_image(encoding)).astype('uint16'))

def api_gen(input_images, depth_images, gen_options):

    print(f"Processing {str(len(input_images))} images through the API")

    pil_images = []
    for input_image in input_images:
        pil_images.append(to_base64_PIL(input_image))

    pil_depth_images = []
    for input_image in depth_images:
        pil_depth_images.append(to_base64_PIL16(input_image))
    
    outpath = os.path.join(os.path.dirname( os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ), 'static')
    # create dir if not already there
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    # better method for naming?
    file_count = "{:04d}".format(len([name for name in os.listdir(outpath)]))+'.'+gen_options['file_type']
    filepath = os.path.join(outpath, file_count)
    gen_obj = pipeline({
            'file_name': filepath, 
            'image': pil_images[0], 
            'depth_image': pil_depth_images[0],
            'double_sided': gen_options['double_sided'],
            'depth_model': 'not used',
            'depth_size': (gen_options['net_width'], gen_options['net_height']),
            'reduced_size': (128, 128),
            'remove_bg': True,
            'file_type': gen_options['file_type'],
            'pre_blur': True,
            'pre_scale': 0.5
    })
    return file_count

# _ parameter is needed for auto1111 extensions (_ is type gr.Blocks)
def api_routes(_, app: FastAPI):
    @app.post("/depthcreation/generate")
    async def process(
        input_images: List[str] = Body([], title='Input Images'),
        depth_images: List[str] = Body([], title='Depth Images'),
        generate_options: Dict[str, object] = Body({}, title='Generation options'),
        ):
        
        if len(input_images)==0:
            raise HTTPException(status_code=422, detail="No images supplied")

        obj_path = api_gen(input_images, depth_images, generate_options)

        return {"path": obj_path , "info": "Success"}
        
        