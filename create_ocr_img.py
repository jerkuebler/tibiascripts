import sys

import numpy

from PIL import Image
import PIL.ImageGrab
from appJar import gui


def binarize_image(img_path, target_path):
    """Binarize an image."""
    image_file = Image.open(img_path)
    image = image_file.convert('L')  # convert image to monochrome
    image = numpy.array(image)
    image = binarize_array(image)
    im = Image.fromarray(image)
    im.save(target_path)


def binarize_array(numpy_array):
    """Binarize a numpy array."""
    for i in range(len(numpy_array)):
        rng = len(numpy_array[0])
        for j in range(rng):
            if 78 > numpy_array[i][j] or numpy_array[i][j] > 150:
                print(numpy_array[i][j])
                numpy_array[i][j] = 255
            else:
                numpy_array[i][j] = 0

    return numpy_array


class Bot:
    def __init__(self):

        self.app = gui('Monitor', useTtk=True, showIcon=False)
        self.app.setTtkTheme('vista')
        self.app.favicon = None
        self.counter = 0

        def press(button):
            if button == 'Start':
                # (970, 307, 1065, 324) Sell offer
                # (970, 533, 1065, 550) Buy offer
                # (900, 307, 957, 324) Sell Amount
                # (900, 533, 957, 550) Buy Amount
                self.process_image((900, 307, 957, 324))
                self.counter += 1
                print('Taking img ' + str(self.counter))
            elif button == 'Exit':
                sys.exit()

        self.app.addLabel('')
        self.app.addButtons(['Start', 'Exit'], press)
        self.app.go()

    def process_image(self, bbox):
        img = PIL.ImageGrab.grab(bbox=bbox)
        img.save('test.png')
        binarize_image('test.png', './ocr_imgs/test' + str(self.counter) + '.png')


if __name__ == '__main__':
    Bot()