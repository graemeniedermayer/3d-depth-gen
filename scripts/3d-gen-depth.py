import traceback
import gradio as gr
from modules import shared
import modules.scripts as scripts

from ui import main_ui_panel, on_ui_tabs
from versions import *
from core.pipeline import pipeline


class Script(scripts.Script):
    def title(self):
        return SCRIPT_NAME

    def show(self, is_img2img):
        return True

    def ui(self, is_img2img):
        gr.HTML()  # Work around a Gradio bug
        with gr.Column(variant='panel'):
            gr.HTML()  # Work around a Gradio bug
            ret = main_ui_panel(False)
            ret += ret.enkey_tail()
        return ret.enkey_body()

    # run from script in txt2img or img2img
    def run(self, p, *inputs):
        from modules import processing
        from modules.processing import create_infotext

        # sd process
        processed = processing.process_images(p)
        processed.sampler = p.sampler  # for create_infotext

        inputimages = []
        for count in range(0, len(processed.images)):
            # skip first grid image
            if count == 0 and len(processed.images) > 1 and shared.opts.return_grid:
                continue
            inputimages.append(processed.images[count])

        outputs = (p.outpath_samples, inputimages)

        file_name = './'
        rigging_enabled = False
        for input_i, imgs in enumerate(outputs):
            pipeline({
                'image': input_i,
                'file_namne': file_name,
                'rigging_enabled': rigging_enabled,
            })
            # get generation parameters
            if hasattr(processed, 'all_prompts') and shared.opts.enable_pnginfo:
                info = create_infotext(processed, processed.all_prompts, processed.all_seeds, processed.all_subseeds,
                                       "", 0, input_i)
            else:
                info = None
            for image_type, image in list(imgs.items()):
                processed.images.append(image)
                # if inputs["save_outputs"]:
                #     try:
                #         suffix = "" if image_type == "depth" else f"{image_type}"
                #         save_image(image, path=p.outpath_samples, basename="", seed=processed.all_seeds[input_i],
                #                    prompt=processed.all_prompts[input_i], extension=shared.opts.samples_format,
                #                    info=info,
                #                    p=processed,
                #                    suffix=suffix)
                #     except Exception as e:
                #         if not ('image has wrong mode' in str(e) or 'I;16' in str(e)):
                #             raise e
                #         print('Catched exception: image has wrong mode!')
                #         traceback.print_exc()
        return processed


# TODO: some of them may be put into the main ui pane
def on_ui_settings():
    section = ('depth creation', "depth creation extension")

from modules import script_callbacks
script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_ui_tabs(lambda: [(on_ui_tabs(), "Depth Creation", "depth_creation_interface")])


# API script
from api import api

try:
    import modules.script_callbacks as script_callbacks
    script_callbacks.on_app_started(api.api_routes)
except:
    print('DepthMap API could not start')