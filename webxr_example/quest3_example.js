
// This requires some cleanup
import * as THREE from "three"
import {XRButton} from "xrbutton"
import { XRControllerModelFactory } from 'XRControllerModelFactory';
import { GLTFLoader } from 'GLTFLoader';
import { OBJLoader } from 'OBJLoader';

let scene, camera, renderer;
let buttonCanvas, promptCanvas, promptTexture, buttonTexture;
let group
let static_group
let raycaster
let controller1, controller2;
let controllerGrip1, controllerGrip2;
let intersected = []
let click_lock = false

// Three different fetch methods
// 1. fetch diffuse layers (for transparent objects)
// 2. fetch with controlnet
// 2. fetch basic txt2img

let fetch3d_diffuselayer = (prompt)=>{
    const loader = new OBJLoader();
    const url_base = "url"
    const url_depth = url_base + 'depth/generate'
    const url_sd = url_base + 'sdapi/v1/txt2img'
    const url_3d = url_base + 'depthcreation/generate'
    const dic_sd = {
        'prompt': prompt,
        'negative_prompt': '',
        'steps': 20,
        'width': 1024,
        'height': 1024, 
        "alwayson_scripts": {
            "LayerDiffuse": {
              "args": [
                {
                  "method": 4
                }
              ]
            }
          }
    }
    // add status information
    fetch(url_sd,
        {
            method: 'POST',
            body: JSON.stringify(dic_sd), 
            headers: {
                'Content-Type': 'application/json'
                // 'Content-Type': 'application/x-www-form-urlencoded',
              },
            mode:'cors',  
        }
    )
    .then((e)=>e.json())
    .then((e)=>{
        const color_image = e['images'][0]
        const alpha_image = e['images'][1]
        const dic_depth = {
            "depth_input_images": [ color_image],
            "options":{
              "compute_device": "GPU",
              "model_type": 7,
              "net_width": 512,
              "net_height":512,
              "net_size_match": false,
              "boost": false,
              "invert_depth": false
            }
        }
        // add status information
    fetch(url_depth,
        {
            method: 'POST',
            body: JSON.stringify(dic_depth), 
            headers: {
                'Content-Type': 'application/json'
                // 'Content-Type': 'application/x-www-form-urlencoded',
              },
            mode:'cors',  
        }
    )
    .then((e)=>e.json())
    .then((e)=>{
        // use index 1 if background is removed
        const depth_image = e['images'][0]

        // add status information
        const dic_3d = {
            'input_images': [alpha_image],
            'depth_images': [depth_image],
            'generate_options':{
                'double_sided':true,
                'net_width': 512,
                'net_height':512,
                'file_type':'obj'
            }
        }
        fetch(url_3d,
            {
                method: 'POST',
                body: JSON.stringify(dic_3d), 
                headers: {
                    'Content-Type': 'application/json'
                    // 'Content-Type': 'application/x-www-form-urlencoded',
                  },
                mode:'cors',  
            }
        )
        .then((e)=>e.json())
        .then((e)=>{
            // create 3d object
            const file_path = e['path']
            console.log(file_path)

            click_lock = false
            // add 3d object
            loader.load( url_base+'file=static/'+file_path, function ( obj ) {

                // scene.add( gltf.scene );
                static_group.add(obj.children[0])
                let buttonContext = buttonCanvas.getContext('2d');
                buttonContext.fillStyle = "#ffffcc";
                buttonContext.clearRect(0, 0, buttonCanvas.width, buttonCanvas.height);
                buttonContext.font = "250px Arial"
                buttonContext.fillStyle = "#333399";
                buttonContext.fillText("button", 512, 512)
                buttonTexture.needsUpdate = true

            }, undefined, function ( error ) {
            
                console.error( error );
            
            } );
        })
    })
    })
}


let fetch3d_controlnet = (prompt)=>{
    const loader = new GLTFLoader();
    const url_base = "https://192.168.0.15:7860/"
    const url_depth = url_base + 'depth/generate'
    const url_sd = url_base + 'sdapi/v1/txt2img'
    const url_3d = url_base + 'depthcreation/generate'
    const dic_sd = {
        'prompt': prompt,
        'negative_prompt': '',
        'steps': 20,
        'width': 1024,
        'height': 1024, 
        "alwayson_scripts": {
            "controlnet": {
              "args": [
                {
                  "input_image": "base64...",
                  "model": "diff_control_sd15_depth_fp16 [978ef0a1]"
                }
              ]
            }
          }
    }
    // add status information
    fetch(url_sd,
        {
            method: 'POST',
            body: JSON.stringify(dic_sd), 
            headers: {
                'Content-Type': 'application/json'
                // 'Content-Type': 'application/x-www-form-urlencoded',
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
        // add status information
    fetch(url_depth,
        {
            method: 'POST',
            body: JSON.stringify(dic_depth), 
            headers: {
                'Content-Type': 'application/json'
                // 'Content-Type': 'application/x-www-form-urlencoded',
              },
            mode:'cors',  
        }
    )
    .then((e)=>e.json())
    .then((e)=>{
        // use index 1 if background is removed
        const depth_image = e['images'][1]

        // add status information
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
                    // 'Content-Type': 'application/x-www-form-urlencoded',
                  },
                mode:'cors',  
            }
        )
        .then((e)=>e.json())
        .then((e)=>{
            // create 3d object
            const file_path = e['path']

            click_lock = false
            // add 3d object
            loader.load( url_base+'file=static/'+file_path, function ( gltf ) {

                // scene.add( gltf.scene );
                static_group.attach(gltf.scene.children[0])
                let buttonContext = buttonCanvas.getContext('2d');
                buttonContext.fillStyle = "#ffffcc";
                buttonContext.clearRect(0, 0, buttonCanvas.width, buttonCanvas.height);
                buttonContext.font = "250px Arial"
                buttonContext.fillStyle = "#333399";
                buttonContext.fillText("button", 512, 512)
                buttonTexture.needsUpdate = true

            }, undefined, function ( error ) {
            
                console.error( error );
            
            } );
        })
    })
    })
}



let fetch3d = (prompt)=>{
    const loader = new GLTFLoader();
    const url_base = "https://192.168.0.15:7860/"
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

            click_lock = false
            // add 3d object
            loader.load( url_base+'file=static/'+file_path, function ( gltf ) {
                static_group.attach(gltf.scene.children[0])
                let buttonContext = buttonCanvas.getContext('2d');
                buttonContext.fillStyle = "#ffffcc";
                buttonContext.clearRect(0, 0, buttonCanvas.width, buttonCanvas.height);
                buttonContext.font = "250px Arial"
                buttonContext.fillStyle = "#333399";
                buttonContext.fillText("button", 512, 512)
                buttonTexture.needsUpdate = true

            }, undefined, function ( error ) {
            
                console.error( error );
            
            } );
        })
    })
    })
}

function init() {

    const getCanvas = () =>{
    	let canvas = document.createElement('canvas');
      	canvas.width = 1024;
    	canvas.height= 1024;
    	let el = document.createElement('div');
    	el.style.position= 'absolute';
    	el.style.opacity = 0;
    	el.style.pointerEvents = 'none'
    	el.style.height= '1024px' 
    	el.style.width='1024px'
    	el.appendChild(canvas)
    	document.body.appendChild(el)
      	let ctx = canvas.getContext('2d');
        ctx.textAlign="center"; 
        ctx.textBaseline="middle";
    	ctx.fillStyle=  "#FFFFFF";
    	ctx.fillRect(0, 0, canvas.width, canvas.height );
    	return canvas
    }

    scene = new THREE.Scene();
	// for debugging
	globalThis.scene = scene
    camera = new THREE.PerspectiveCamera( 50, window.innerWidth / window.innerHeight, 0.001, 10 );
	// camera.position.x = -1
	
    group = new THREE.Group()
    let geometry = new THREE.BoxGeometry( 0.2, 0.2, 0.2 );
    let material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
    const cube = new THREE.Mesh( geometry, material );
    group.attach( cube );
    camera.add(group)
    static_group = new THREE.Group()
    scene.add(static_group)

    // ui
    const alight = new THREE.AmbientLight( 0x000000 ); // soft white light
    scene.add( alight );


    buttonCanvas = getCanvas()
    let buttonContext = buttonCanvas.getContext('2d');
    buttonContext.fillStyle = "#ffffcc";
    buttonContext.clearRect(0, 0, buttonCanvas.width, buttonCanvas.height);
    buttonContext.font = "250px Arial"
    buttonContext.fillStyle = "#333399";
    buttonContext.fillText("button", 512, 512)

    buttonTexture = new THREE.CanvasTexture(buttonCanvas)

    geometry = new THREE.PlaneGeometry( 0.03, 0.03, 1, 1 );
    material = new THREE.MeshBasicMaterial( {  
        map: buttonTexture, 
        // color:'#ffff00',
        side: THREE.DoubleSide
    } );
    let button = new THREE.Mesh( geometry, material );
    buttonTexture.needsUpdate = true
    group.attach(button);
    button.position.z = -0.25
    button.position.y = -0.1
    button.position.x = 0.1
    button.userData.type = 'button'
    
    promptCanvas = getCanvas()
    
    promptCanvas.width = 8192;
    promptCanvas.height= 1024;
    promptCanvas.style.height= '1024px' 
    promptCanvas.style.width='8192px'
    promptTexture = new THREE.CanvasTexture(promptCanvas)

    geometry = new THREE.PlaneGeometry( 0.2, 0.025, 1, 1);
    material = new THREE.MeshBasicMaterial( { 
        map: promptTexture, 
        // color: '#ff00ff',
        side: THREE.DoubleSide
    } );

    promptTexture.needsUpdate = true
    let textbox = new THREE.Mesh( geometry, material );
    textbox.position.z = -0.28
    textbox.position.y = -0.14
    textbox.position.x = -0.0
    textbox.userData.type = 'textbox'
    group.attach(textbox);

    scene.add(camera)
    
	renderer = new THREE.WebGLRenderer( { antialias: true } );
	renderer.setPixelRatio( window.devicePixelRatio );
	renderer.setSize( window.innerWidth, window.innerHeight );
	renderer.xr.enabled = true;
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.outputEncoding = THREE.sRGBEncoding
	renderer.setAnimationLoop( render );
	document.body.appendChild( renderer.domElement );
	window.addEventListener( 'resize', onWindowResize, false );

    controller1 = renderer.xr.getController( 0 );
	controller1.addEventListener( 'selectstart', onSelectStart );
	controller1.addEventListener( 'selectend', onSelectEnd );
	scene.add( controller1 );

	controller2 = renderer.xr.getController( 1 );
	controller2.addEventListener( 'selectstart', onSelectStart );
	controller2.addEventListener( 'selectend', onSelectEnd );
	scene.add( controller2 );

	const controllerModelFactory = new XRControllerModelFactory();
	controllerGrip1 = renderer.xr.getControllerGrip( 0 );
	controllerGrip1.add( controllerModelFactory.createControllerModel( controllerGrip1 ) );
	scene.add( controllerGrip1 );

	controllerGrip2 = renderer.xr.getControllerGrip( 1 );
	controllerGrip2.add( controllerModelFactory.createControllerModel( controllerGrip2 ) );
	scene.add( controllerGrip2 );

    const light1 = new THREE.PointLight( 0xffffff, 2.5, 5 );
    light1.position.set( 0, 0, 0 );
    controller1.add( light1 );

    const light2 = new THREE.PointLight( 0xffffff, 2.5, 5 );
    light2.position.set( 0, 0, 0 );
    controller2.add( light2 );


    const light3 = new THREE.PointLight( 0xffffff, 2.5, 5 );
    light3.position.set( 0, 0, 0 );
    camera.add( light3 );


    geometry = new THREE.BufferGeometry().setFromPoints( [ new THREE.Vector3( 0, 0, 0 ), new THREE.Vector3( 0, 0, - 1 ) ] );
    const line = new THREE.Line( geometry );
	line.name = 'line';
	line.scale.z = 5;

	controller1.add( line.clone() );
	controller2.add( line.clone() );

    raycaster = new THREE.Raycaster();

}
function initXR() {

}
function onWindowResize() {
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix();
	renderer.setSize( window.innerWidth, window.innerHeight );
}

function render() {
    cleanIntersected();

    intersectObjects( controller1 );
    intersectObjects( controller2 );

	renderer.render( scene, camera );
}

// click button 

// canvas

function onXRFrame(t, frame) {
    const session = frame.session;
    session.requestAnimationFrame(onXRFrame);
    const baseLayer = session.renderState.baseLayer;
    const pose = frame.getViewerPose(xrRefSpace);
	render()
}
init();

const textbox = document.getElementById('textbox')
textbox.addEventListener('input', ()=>{
    const promptContext = promptCanvas.getContext("2d")
    promptContext.fillStyle = "#FFCCCC";
    promptContext.clearRect(0, 0, promptCanvas.width, promptCanvas.height);
    promptContext.fillStyle = "#333399";
    promptContext.font = "500px Arial"
    promptContext.fillText(textbox.value, 128, 600)
    promptTexture.needsUpdate = true
})

function onSelectStart( event ) {
    const controller = event.target;
    const intersections = getIntersections( controller );
    if ( intersections.length > 0 ) {
        const intersection = intersections[ 0 ];
        const object = intersection.object;
        controller.attach( object );
        controller.userData.selected = object;
        if(object.userData.type=='textbox'){
            textbox.focus()
        }
        if(object.userData.type=='button'){
            document.getElementById('button').focus()
            if(!click_lock){
                click_lock = true
                document.getElementById('button').click()

                let buttonContext = buttonCanvas.getContext('2d');
                buttonContext.fillStyle = "#5555FF";
                buttonContext.clearRect(0, 0, buttonCanvas.width, buttonCanvas.height);
                buttonContext.font = "250px Arial"
                buttonContext.fillStyle = "#333399";
                buttonContext.fillText("button", 512, 512)
                buttonTexture.needsUpdate = true
                // change fetch3d here if for controlnet or diffuselayer
                fetch3d(textbox.value)
            }
        }
    }
    controller.userData.targetRayMode = event.data.targetRayMode;
}

function onSelectEnd( event ) {
    const controller = event.target;
    if ( controller.userData.selected !== undefined ) {
        const object = controller.userData.selected;
        if(object.userData.type == 'button' || object.userData.type == 'textbox'){
            group.attach( object );
        }else{
            static_group.attach( object );
        }
        controller.userData.selected = undefined;
    }
}


function getIntersections( controller ) {
    controller.updateMatrixWorld();
    raycaster.setFromXRController( controller );
    return raycaster.intersectObjects( group.children.concat(static_group.children), false );
}

function intersectObjects( controller ) {
    // Do not highlight in mobile-ar
    if ( controller.userData.targetRayMode === 'screen' ) return;
    // Do not highlight when already selected
    if ( controller.userData.selected !== undefined ) return;
    const line = controller.getObjectByName( 'line' );
    const intersections = getIntersections( controller );
    if ( intersections.length > 0 ) {
        const intersection = intersections[ 0 ];
        const object = intersection.object;
        intersected.push( object );
        line.scale.z = intersection.distance;
    } else {
        line.scale.z = 5;
    }
}

function cleanIntersected() {
    while ( intersected.length ) {
        const object = intersected.pop();
        // object.material.emissive.r = 0;
    }
}

let xrButton = XRButton.createButton( renderer,
	{ 
	   'optionalFeatures': [ 'depth-sensing'],
	//    'optionalFeatures': [ 'local'] 
   } 
)
document.body.appendChild( xrButton );
xrButton.addEventListener('click' , e => {
    initXR()

})