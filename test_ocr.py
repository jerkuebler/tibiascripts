import glob

import cv2.ml
import numpy as np


def train_model():
    samples = np.loadtxt('generalsamples.data', np.float32)
    responses = np.loadtxt('generalresponses.data', np.float32)
    responses = responses.reshape((responses.size, 1))

    model = cv2.ml.KNearest_create()
    model.train(samples, cv2.ml.ROW_SAMPLE, responses)

    return model


def test_model(model, img_loc):
    im = cv2.imread(img_loc)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 2)

    img, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    num_dict = {}
    for cnt in contours:
        if 140 > cv2.contourArea(cnt) > 40:
            print(cv2.contourArea(cnt))
            [x, y, w, h] = cv2.boundingRect(cnt)
            if h > 5:
                cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 1)
                roi = thresh[y:y + h, x:x + w]
                roismall = cv2.resize(roi, (10, 10))
                roismall = roismall.reshape((1, 100))
                roismall = np.float32(roismall)
                retval, results, neigh_resp, dists = model.findNearest(roismall, k=1)
                string = str(int((results[0][0])))

                num_dict[x] = string

    order = sorted(num_dict.keys())
    num = ''.join((num_dict[o] for o in order))

    try:
        value = int(num)
    except ValueError:
        value = 'No Offer'

    print(value)

    im = cv2.resize(im, (200, 100))

    cv2.imshow('im', im)
    cv2.waitKey(0)


if __name__ == '__main__':
    ocr = train_model()
    images = glob.glob('.\ocr_imgs\*.png')
    for im_loc in images:
        print(im_loc)
        test_model(ocr, im_loc)
