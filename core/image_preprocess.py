from PIL import Image, ImageOps
# contour 
def contour_outline(cv2_img):
    from PIL import Image
    import cv2
    import numpy as np

    #convert img to grey for rgb image (remove for greyscale)
    img_grey = cv2.cvtColor(cv2_img,cv2.COLOR_BGR2GRAY)
    #set a thresh
    thresh = 100
    #get threshold image
    ret,thresh_img = cv2.threshold(img_grey, thresh, 255, cv2.THRESH_BINARY)
    #find contours
    contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #create an empty image for contours
    img_contours = np.zeros(cv2_img.shape) 
    # make mask
    cv2.drawContours(img_contours, contours, -1, (255,255,255), -1)
    # cv2.drawContours(img_contours, contours, -1, (255,255,255), 20)
    #invert mask
    img_contours = -1*(img_contours-255)
    
    # TODO non-functional
    cv2_img.putalpha(255)
    #mask contour to zero
    imArr = np.array(cv2_img)
    imArr[:,:,:3][img_contours[:,:,:3]>10] = 0
    imArr[img_contours[:,:,0]>10,3] = 0
    return Image.fromarray(imArr.astype('uint8'), 'RGBA')

# pinch image.
def use_pinch_depth(depthmap_bg_removed):
    pinch_depthmap = contour_outline(depthmap_bg_removed)

    return pinch_depthmap

def clearAlpha():
    pass

def image_double(image):

    new_im = Image.new(image.mode, (2*image.size[0], image.size[1]))
    new_im.paste(image, (0, 0))
    new_im.paste(ImageOps.mirror(image), (image.size[0], 0))
    return new_im