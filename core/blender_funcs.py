import bpy

def remove_keyframes(object, action, frame_number):
    for curve in action.fcurves:
        object.keyframe_delete(data_path=curve.data_path, frame=frame_number)

def delete_all_keyframes(object, frame_number):
    animation_data = object.animation_data
    if animation_data.action:
        remove_keyframes(object, animation_data.action, frame_number)
    for track in animation_data.nla_tracks:
        for strip in track.strips:
            remove_keyframes(object, strip.action, frame_number)

# loop over all the fcurves
def set_initial_frame(obj, initFrame = 0):
    curves = obj.animation_data.action.fcurves
    for c in curves:
        # each curve has a keyframe_points attribute, thats where we can get the
        # keyframe_point.co attribute (coordinates)
        kfs = c.keyframe_points
        # use the enumerate keyword to get an index for free along with the iterable
        # you are already looping over.
        for i, kf in enumerate(kfs):
            # so every loop looks like
            # i = 0, kf = keyframe1
            # then
            # i = 1, kf = keyframe2
            # etc.

            # kf.co.x is the location in time, e.g what frame, kf.co.y would be the
            # 'magnitude' of the keyframe. All we need is to change the x axis.
            kf.co.x = i + 1 + initFrame
            
def rename_strips(arma):
    if arma.animation_data:
        for track in arma.animation_data.nla_tracks:
            if track.strips and '|' in track.name:
                track.name = track.strips[0].action.name.split('|')[2].split('_')[0]