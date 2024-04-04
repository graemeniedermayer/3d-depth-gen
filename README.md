# 3d-depth-gen
AUTO1111 extension for automated txt-to-3d objects. This uses monodepth maps + bpy (blender). WIP

This project has a focus on the api to generate ai 3d objects for webxr.

## Installation
Requires python3.10 + bpy (blender)

Requires https://github.com/thygate/stable-diffusion-webui-depthmap-script

Should work with install from URL 

## Goal List
Aspirational list for this project
- lots of bugfixes (put together install.py)
- simplify api calls
- unity integration
- docker image
- automated animation + rigging
- tangent normal maps don't seem accurate
- deeper integration for augmented reality

## JavaScript API Request example
threejs examples. hopefully this will be simpler in the future
```
let fetch3d = (prompt)=>{
    const loader = new GLTFLoader();
    const url_base = "https://path_to_server.com:7860/"
    const url_depth = url_base + 'depth/generate'
    const url_sd = url_base + 'sdapi/v1/txt2img'
    const url_3d = url_base + 'depthcreation/generate'
    const dic_sd = {
        'prompt': prompt,
        'negative_prompt': '',
        'steps': 20,
        'width': 1024,
        'height': 1024, 
    }
    fetch(url_sd,
        {
            method: 'POST',
            body: JSON.stringify(dic_sd), 
            headers: {
                'Content-Type': 'application/json'
              },
            mode:'cors',  
        }
    )
    .then((e)=>e.json())
    .then((e)=>{
        const color_image = e['images'][0]
        const dic_depth = {
            "depth_input_images": [ color_image],
            "options":{
              "compute_device": "GPU",
              "model_type": 7,
              "net_width": 512,
              "net_height":512,
              "net_size_match": false,
              "boost": false,
              "invert_depth": false,
              "gen_rembg": true,
              "rembg_model": "isnet-general-use"
            }
        }
    fetch(url_depth,
        {
            method: 'POST',
            body: JSON.stringify(dic_depth), 
            headers: {
                'Content-Type': 'application/json'
              },
            mode:'cors',  
        }
    )
    .then((e)=>e.json())
    .then((e)=>{
        // use index 1 if background is removed
        const depth_image = e['images'][1]

        const dic_3d = {
            'input_images': [color_image],
            'depth_images': [depth_image],
            'generate_options':{
                'double_sided':true,
                'net_width': 512,
                'net_height':512,
                'file_type':'glb'
            }
        }
        fetch(url_3d,
            {
                method: 'POST',
                body: JSON.stringify(dic_3d), 
                headers: {
                    'Content-Type': 'application/json'
                  },
                mode:'cors',  
            }
        )
        .then((e)=>e.json())
        .then((e)=>{
            const file_path = e['path']

            // add 3d object
            loader.load( url_base+'file=static/'+file_path, function ( gltf ) {
                static_group.attach(gltf.scene.children[0])
            }, undefined, function ( error ) {
            
                console.error( error );
            
            } );
        })
    })
    })
}
```

## Recognition
This uses lots of opensource tools. Thank you to everyone working on opensource. Y'all are the best.

This uses a lot of the code structure from https://github.com/thygate/stable-diffusion-webui-depthmap-script

Special thanks to thygate and semjon00

## Academic Projects used

ZoeDepth :

```
@misc{https://doi.org/10.48550/arxiv.2302.12288,
  doi = {10.48550/ARXIV.2302.12288},
  url = {https://arxiv.org/abs/2302.12288},
  author = {Bhat, Shariq Farooq and Birkl, Reiner and Wofk, Diana and Wonka, Peter and Müller, Matthias},
  keywords = {Computer Vision and Pattern Recognition (cs.CV), FOS: Computer and information sciences, FOS: Computer and information sciences},
  title = {ZoeDepth: Zero-shot Transfer by Combining Relative and Metric Depth},
  publisher = {arXiv},
  year = {2023},
  copyright = {arXiv.org perpetual, non-exclusive license}
}
```

Marigold - Repurposing Diffusion-Based Image Generators for Monocular Depth Estimation:

```
@misc{ke2023repurposing,
      title={Repurposing Diffusion-Based Image Generators for Monocular Depth Estimation}, 
      author={Bingxin Ke and Anton Obukhov and Shengyu Huang and Nando Metzger and Rodrigo Caye Daudt and Konrad Schindler},
      year={2023},
      eprint={2312.02145},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
}
```
