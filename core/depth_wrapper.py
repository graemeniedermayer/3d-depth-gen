#packages all should be install by default
import requests
from io import BytesIO
import base64
import json
from PIL import Image
import base64
from io import BytesIO
from modules import cmd_args

args, _ = cmd_args.parser.parse_known_args()

# this is async. 
def use_depth_api(img, model='marigold', remove_bg = True):
    # TODO This probably doesn't cover all cases
    url = 'http://' + (args.server_name if args.server_name is not None else '128.0.0.1') + ':' + (args.port if args.port is not None else '7860') + '/depth/generate'
    print(url)
    buffered = BytesIO()
    img.save(buffered, format="png")
    img_str = base64.b64encode(buffered.getvalue())

    model_to_type = { 'marigold':10, 'zoedepth_n (indoor)':7, 'zoedepth_k (outdoor)':8, 'zoedepth_nk':9}
    dics = {
      "depth_input_images": [img_str],
        "options":{
          "compute_device": "GPU",
          "model_type": model_to_type[model],
          "net_width": 512,
          "net_height": 512,
          "net_size_match": False,
          "boost": False,
          "invert_depth": False,
          "gen_rembg": remove_bg,
          "rembg_model": "isnet-general-use"
        }
    }
    # httpx rather than request becasue request breaks with api call for some reason.

    # x = httpx.post(url, data = dics)
    # if remove_bg:
    #   img_byte = x.json()['images'][1]
    # else:
    #   img_byte = x.json()['images'][0]

    x = requests.post(url, json = dics)
    # index 0 is the removed background image
    if remove_bg:
      img_byte = json.loads(x.text)['images'][1]
    else:
      img_byte = json.loads(x.text)['images'][0]
       
    #Image is decoded here. this might have changed in python 3.9
    img_out = Image.open(BytesIO(base64.b64decode(img_byte)))
    return img_out

