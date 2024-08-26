import traceback
from pathlib import Path
import gradio as gr
from PIL import Image
from core.gradio_args_transport import GradioComponentBundle
import os
from core.pipeline import pipeline
from core.call_sd_api import sd_api
from modules.call_queue import wrap_gradio_gpu_call
from modules import cmd_args

args, _ = cmd_args.parser.parse_known_args()

def ensure_gradio_temp_directory():
    try:
        import tempfile
        path = os.path.join(tempfile.gettempdir(), 'gradio')
        if not (os.path.exists(path)):
            os.mkdir(path)
    except Exception as e:
        traceback.print_exc()

ensure_gradio_temp_directory()

def main_ui_panel(is_3d_gen_depth_tab):
    inp = GradioComponentBundle()
    with gr.Blocks():
        # with gr.Row():
        #     inp['backend'] = gr.Dropdown(label="Backend",
        #                                      choices=['depthmap', 'gaussian'],
        #                                      value='depthmap',
        #                                      type="value")
        with gr.Box():
            with gr.Row():
                inp += 'model_type', gr.Dropdown(label="Depth Model",
                                                 choices=[ 'marigold',
                                                          'zoedepth_n (indoor)', 'zoedepth_k (outdoor)', 'zoedepth_nk', 'depthanything', 'depthanything2s', 'depthanything2'],
                                                 value='zoedepth_n (indoor)',
                                                 type="value")
                # inp += 'advanced_settings', gr.Checkbox(label="advanced settings", value=False)
            with gr.Row():
                inp += 'match_size', gr.Checkbox(label="Match net size to input size", value=False)
            with gr.Row(visible=True) as options_depend_on_match_size:
                inp += 'net_width', gr.Slider(minimum=64, maximum=2048, step=64, label='Net width', value=512)
                inp += 'net_height', gr.Slider(minimum=64, maximum=2048, step=64, label='Net height', value=512 )
        
        # with gr.Box():
        #     with gr.Row():
        #         with gr.Group():
        #             inp += "one_at_time", gr.Checkbox(label="Run gen one at a time (locked to true)", value=True)  # 50% of width
        #         with gr.Group(): 
        #             inp += "depth_mixing", gr.Checkbox(label="Depth mixing", value=False)
        #     with gr.Row(visible=True) as options_depend_on_depth_mixing_0:
        #         inp += 'depth_1024', gr.Slider(minimum=0, maximum=1, step=0.01, label='depth 1024', value=0.1)
        #         inp += 'depth_768', gr.Slider(minimum=0, maximum=1, step=0.01, label='depth 768', value=0.0)
        #         inp += 'depth_512', gr.Slider(minimum=0, maximum=1, step=0.01, label='depth 512', value=0.9)
        
        with gr.Box():
            with gr.Row():
                with gr.Group():
                    inp += "calc_normal_map", gr.Checkbox(label="calculate normal map (slow)", value=True) 
                with gr.Group():
                    inp += "invert_normal_maps", gr.Checkbox(label="invert normal map", value=True) 
                with gr.Group(): 
                    inp += 'pre_scale', gr.Slider(minimum=0, maximum=1, step=0.01, label='scaling', value=0.2)
            with gr.Row(visible=True) as options_depend_on_match_size:
                inp += 'reduced_width', gr.Slider(minimum=64, maximum=2048, step=64, label='Reduced width', value=128)
                inp += 'reduced_height', gr.Slider(minimum=64, maximum=2048, step=64, label='Reduced height', value=128 )
        
        with gr.Box():
            with gr.Row():
                with gr.Group():
                    inp += "double_sided", gr.Checkbox(label="double_sided", value=False) 
                with gr.Group(): 
                    inp += "remove_background", gr.Checkbox(label="remove background", value=True)
                with gr.Group():
                    inp += "pre_blur_edges", gr.Checkbox(label="pre-blur edges", value=True) 
                # with gr.Group(): 
                    # inp += "texture_blend_edges", gr.Checkbox(label="texture blend edges", value=True)
                with gr.Group(): 
                    inp += "attempt_rigging", gr.Checkbox(label="attempt auto rigging", value=True)
    


    # inp['boost'].change(
    #          fn=lambda a, b: (inp['match_size'].update(visible=not a),
    #                           options_depend_on_match_size.update(visible=not a and not b)),
    #          inputs=[inp['boost'], inp['match_size']],
    #          outputs=[inp['match_size'], options_depend_on_match_size]
    # )
    inp['match_size'].change(
        fn=lambda a, b: options_depend_on_match_size.update(visible=not a and not b),
        inputs=[ inp['match_size']],
        # inputs=[inp['boost'], inp['match_size']],
        outputs=[options_depend_on_match_size]
    )
    # inp['depth_mixing'].change(
    #     fn=lambda a: options_depend_on_depth_mixing_0.update(visible=a),
    #     inputs=[inp['depth_mixing']],
    #     outputs=[options_depend_on_depth_mixing_0]
    # )

    return inp

def on_ui_tabs():
    inp = GradioComponentBundle()
    with gr.Blocks(analytics_enabled=False, title="DepthCreation") as depth_creation_interface:
        with gr.Row(equal_height=False):
            with gr.Column(variant='panel'):
                inp += 'depthmap_mode', gr.HTML(visible=False, value='0')
                with gr.Tabs():
                    with gr.TabItem('Single Image') as depthmap_mode_0:
                        with gr.Group():
                            with gr.Row():
                                inp += gr.Image(label="Source", source="upload", interactive=True, type="pil",
                                                elem_id="depthmap_input_image", image_mode='RGBA')
                                # TODO: depthmap generation settings should disappear when using this
                                inp += gr.File(label="Custom DepthMap", file_count="single", interactive=True,
                                               type="binary", elem_id='custom_depthmap_img',  visible=False)
                        inp += gr.Checkbox(elem_id="custom_depthmap", label="Use custom DepthMap", value=False)
                    # with gr.TabItem('Batch Process') as depthmap_mode_1:
                    #     inp += gr.File(elem_id='image_batch', label="Batch Process", file_count="multiple",
                    #                    interactive=True, type="file")
                    # with gr.TabItem('Text to 3d') as depthmap_mode_2:
                    #     inp += gr.Textbox(elem_id='txt3d', label="txt-2-3d",
                    #                       placeholder="ai positive prompt")
                    # with gr.TabItem('Batch from Directory') as depthmap_mode_2:
                    #     inp += gr.Textbox(elem_id="depthmap_batch_input_dir", label="Input directory",
                    #                       **backbone.get_hide_dirs(),
                    #                       placeholder="A directory on the same machine where the server is running.")
                    #     inp += gr.Textbox(elem_id="depthmap_batch_output_dir", label="Output directory",
                    #                       **backbone.get_hide_dirs(),
                    #                       placeholder="Leave blank to save images to the default path.")
                    #     gr.HTML("Files in the output directory may be overwritten.")
                    #     inp += gr.Checkbox(elem_id="depthmap_batch_reuse",
                    #                        label="Skip generation and use (edited/custom) depthmaps "
                    #                              "in output directory when a file already exists.",
                    #                        value=True)
                submit = gr.Button('Generate', elem_id="depthmap_generate", variant='primary')
                # unloadmodels = gr.Button('Unload models', elem_id="depthmap_unloadmodels")
                inp |= main_ui_panel(True) 
            with gr.Column(variant='panel'):
                with gr.Tabs(elem_id="mode_depthmap_output"):
                    with gr.TabItem('3D Mesh'):
                        with gr.Group():
                            result_depthmesh = gr.Model3D(scale=0.1, label="3d Mesh", clear_color=[1.0, 1.0, 1.0, 1.0])
                            with gr.Row():
                                # loadmesh = gr.Button('Load')
                                clearmesh = gr.Button('Clear')

                    # with gr.TabItem('Depth Output'):
                    #     with gr.Group():
                    #         result_images = gr.Gallery(label='Output', show_label=False,
                    #                                    elem_id=f"depthmap_gallery", columns=4)
                        with gr.Column():
                            html_info = gr.HTML()
                        folder_symbol = '\U0001f4c2'  # 📂=

        inp += inp.enkey_tail()

        depthmap_mode_0.select(lambda: '0', None, inp['depthmap_mode'])
        # depthmap_mode_1.select(lambda: '1', None, inp['depthmap_mode'])
        # depthmap_mode_2.select(lambda: '2', None, inp['depthmap_mode'])

        submit.click(
            fn=wrap_gradio_gpu_call(run_generate),
            inputs=inp.enkey_body(),
            outputs=[
                result_depthmesh,
                html_info
            ]
        )
        return depth_creation_interface
    
def get_opt(name, default):
    from modules.shared import opts
    if hasattr(opts, name):
        return opts.__getattr__(name)
    return default
def get_outpath():
    """Get path where results are saved by default"""
    path = get_opt('outdir_samples', None)
    if path is None or len(path) == 0:
        path = get_opt('outdir_extras_samples', None)
    assert path is not None and len(path) > 0
    return path

def format_exception(e: Exception):
    traceback.print_exc()
    msg = '<h3>' + 'ERROR: ' + str(e) + '</h3>' + '\n'
    if 'out of GPU memory' not in msg:
        msg += \
            'Please report this issue ' \
            f'<a href="google.com">TODO put link</a>. ' \
            'Make sure to provide the full stacktrace: \n'
        msg += '<code style="white-space: pre;">' + traceback.format_exc() + '</code>'
    return msg

def run_generate(*inputs):
    inputs = GradioComponentBundle.enkey_to_dict(inputs)
    depthmap_mode = inputs['depthmap_mode']

    outpath = os.path.join(os.path.dirname(__file__), get_outpath())
    # print(outpath)
    file_count = len([name for name in os.listdir(outpath)])
        
    if depthmap_mode == '0':  # Single image
        depthmap_input_image = inputs['depthmap_input_image']
        custom_depthmap = inputs['custom_depthmap']
        custom_depthmap_img = inputs['custom_depthmap_img']

        inputimages = []
        inputdepthmaps = []  # Allow supplying custom depthmaps
        inputnames = []  # Also keep track of original file names

        if depthmap_input_image is None:
            return [], None, None, "Please select an input image"
        inputimages.append(depthmap_input_image)
        inputnames.append(None)
        if custom_depthmap:
            if custom_depthmap_img is None:
                return [], None, None, \
                    "Custom depthmap is not specified. Please either supply it or disable this option."
            inputdepthmaps.append(Image.open(os.path.abspath(custom_depthmap_img.name)))
        else:
            inputdepthmaps.append(None)
        file_type = 'glb'
        filepath = os.path.join(outpath, "{:04d}".format(file_count) + '.' + file_type)
        gen_obj = pipeline({
            'file_name':filepath, 
            'image': inputs['depthmap_input_image'], 
            'calc_normal_map':  inputs['calc_normal_map'], 
            'double_sided':inputs['double_sided'],
            'depth_model': inputs['model_type'],
            'remove_bg': inputs['remove_background'],
            'depth_size': (inputs['net_width'], inputs['net_height']),
            'reduced_size': (inputs['reduced_width'], inputs['reduced_height']), 
            'file_type': file_type,
            'rigging': inputs['attempt_rigging'],
            'pre_blur': inputs['pre_blur_edges'],
            'pre_scale': inputs['pre_scale']
            # '':inputs
        })
        return filepath, ''.replace('\n', '<br>')
    
    if depthmap_mode == '1':  # Batch

        image_batch = inputs['image_batch']

        inputimages = []
        # inputnames = []  # Also keep track of original file names
        for img in image_batch:
            image = Image.open(os.path.abspath(img.name))
            inputimages.append(image)

        for i, inputdepthmap in enumerate(inputimages):
            filepath = os.path.join(outpath, "{:04d}".format(file_count+i)+'.obj')
            gen_obj = pipeline({
                'file_name':filepath, 
                'image':inputdepthmap, 
                # 'depth_image':inputdepthmap, 
                'double_sided':inputs['double_sided'],
                'depth_model': inputs['model_type'],
                'remove_bg': inputs['remove_background'],
                'grid_size': (inputs['net_width'], inputs['net_height']), 
                # '':inputs
            })

        return filepath, ''.replace('\n', '<br>')
    
    if depthmap_mode == '2':  # txt2img
        # first generate image
        #packages all should be install by default
        import requests
        from io import BytesIO
        import base64
        from PIL import Image
        import json
        # this points to auto1111. this is usually the default local address.
        url = 'http://' + (args.server_name if args.server_name is not None else '128.0.0.1') + ':' + (args.port if args.port is not None else '7860') + '/sdapi/v1/txt2img'
        print(url)
        # These are the options more can be found at http://127.0.01:7860/docs under txt2img
        # This could have more options
        dics = {
            'prompt': inputs['txt3d'],
            'negative_prompt': 'cgi',
            'steps': 15, 
            'sampler_name': 'Euler a', 
            'cfg_scale': 7, 
            'seed': -1, 
            'width': 512,
            'height': 512
        }

        #This is where the request is made
        x = requests.post(url, json = dics)
        img = json.loads(x.text)['images'][0]
        im = Image.open(BytesIO(base64.b64decode(img)))
        
        gen_obj = pipeline({
            'file_name':filepath, 
            'image': im, 
            'double_sided':inputs['double_sided'],
            'depth_model': inputs['model_type'],
            'remove_bg': inputs['remove_background'],
            'grid_size': (inputs['net_width'], inputs['net_height']), 
            # '':inputs
        })

        return filepath, ''.replace('\n', '<br>')
    
    # add layered sd?