#! /usr/bin/python
# coding: utf-8

from PIL import Image
import math, random

def rescale_crop(img, size):
    "Rescale and crop image to fit in size"

    # calculate the factor of aimed size to scale it in order to
    # initially crop from original image
    crop_factor = img.size[0]/float(size[0]) if \
                  abs(img.size[0] - size[0]) < \
                  abs(img.size[1] - size[1]) else \
                  img.size[1]/float(size[1])

    # width and height of crop
    w, h = size[0] * crop_factor, size[1] * crop_factor    

    # crop from image from center then resize to desired size
    return img.crop(( int(img.size[0]-w)/2, 
                      int(img.size[1]-h)/2, 
                      int(img.size[0]+w)/2, 
                      int(img.size[1]+h)/2 )).resize(size, Image.ANTIALIAS)

def image_mean(img):
    "calculate the mean of image"

    pixels = img.resize((1,1), Image.ANTIALIAS).load()
    return pixels[0,0][:3]

def distance(pointA, pointB):
    # squared euclidean distance
    distance = 0
    dimensions = len(pointA) # assumes both points have the same dimensions
    for dimension in range(dimensions):
        distance += (pointA[dimension] - pointB[dimension])**2
        return distance

class ImgPoint(tuple):
    pass

def ImagePoint(img):

    pixel = img.resize((1,1), Image.ANTIALIAS).load()[0,0][:3] 
    image_point = ImgPoint( pixel )
    image_point.image = img
    return image_point

def mosaic(img_set, img_target, tile_size, noise=0, blend=0):
    """
    Return an image of img_target composed of images
    from img_set with tile_size. The images in img_set
    might be rescaled and cropped to fit tile_size.
    """
    noise = min(noise, 1)

    # number of tiles to be used
    tx, ty = img_target.size[0]/tile_size[0], img_target.size[1]/tile_size[1]

    # transform all images in set to tile_size
    img_set = [ImagePoint(rescale_crop(img, tile_size)) for img in img_set]

    # calculate, for each image, the mean color vector
#    img_set = [(img, image_mean(img)) for img in img_set]

    # build mosaic image
    mosaic_img = Image.new('RGB', img_target.size)

    # rescale image into each pixel as a tile
    target_pixels = img_target.resize((tx, ty), Image.ANTIALIAS).load()

    # for each tile, select the best image and compose mosaic
    for x in xrange(tx):
        for y in xrange(ty):
            # calculate target's tile mean
            target_mean = target_pixels[x,y][:3]

            # sorts img_set acording to distance:
            img_set.sort(key=lambda e: distance(e, target_mean))

            # selects with higher probability the firsts elements
            for imgpoint in img_set:
                if random.random() > noise:
                    best_tile = imgpoint.image
                    break
            else:
                best_tile = random.choice(img_set).image

            # apply best tile to mosaic image
            mosaic_img.paste(best_tile, (tile_size[0]*x, tile_size[1]*y))

    return Image.blend(mosaic_img, img_target, blend)

if __name__ == "__main__":

    import argparse

    # Read command line arguments
    parser = argparse.ArgumentParser(description='Create a mosaic')
    parser.add_argument('-t', '--target', nargs=1, type=file, 
                        help='The image to build mosaic on')
    parser.add_argument('-z', '--zoom', nargs='?', type=float, default=1,
                        help='The zoom of target image')
    parser.add_argument('-n', '--noise', nargs='?', type=float, default=0,
                        help='Noise of mosaic')
    parser.add_argument('-b', '--blend', nargs='?', type=float, default=0,
                        help='Blend factor with original image')
    parser.add_argument('-x', '--tile-x', nargs='?', type=int, default=24,
                        help='The width of the tile')
    parser.add_argument('-y', '--tile-y', nargs='?', type=int, default=24,
                        help='The height of the tile')
    parser.add_argument('-o', '--output', nargs=1, type=argparse.FileType('w'),
                        help='The output create mosaic image file')
    parser.add_argument('image', nargs='+', type=file, 
                        help='An image to be used in building the mosaic')
    namespace = parser.parse_args()

    # load target image and zooms
    img_target = Image.open(namespace.target[0]).convert("RGB")
    if namespace.zoom != 1:
        img_target = img_target.resize((int(img_target.size[0]*namespace.zoom),
                                        int(img_target.size[1]*namespace.zoom)))

    # load images
    img_set = [Image.open(img).convert("RGB") for img in namespace.image]

    # build mosaic
    output = mosaic(img_set, img_target, (namespace.tile_x, namespace.tile_y), 
                    namespace.noise, namespace.blend)

    # closes files
    namespace.target[0].close()
    for img_file in namespace.image: img_file.close()

    # saves file
    output.save(namespace.output[0])
    namespace.output[0].close()

