import sys

import numpy as np
import cv2
import glob


def read_image(im_loc, samples, responses):
    im = cv2.imread(im_loc)

    manual_key = []

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, 1, 1, 11, 2)

    #################      Now finding Contours         ###################

    image, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    keys = [i for i in range(48, 58)]

    for cnt in contours:
        if 200 > cv2.contourArea(cnt) > 40:
            print('stage 1')
            [x, y, w, h] = cv2.boundingRect(cnt)

            if h > 5:
                print('stage 2')
                cv2.rectangle(im, (x, y), (x + w, y + h), (0, 0, 255), 1)
                roi = thresh[y:y + h, x:x + w]
                roismall = cv2.resize(roi, (10, 10))
                cv2.imshow('norm', im)
                key = cv2.waitKey(0)

                if key == 27:  # (escape to quit)
                    sys.exit()
                elif key in keys:
                    manual_key.append(int(chr(key)))
                    sample = roismall.reshape((1, 100))
                    samples = np.append(samples, sample, 0)

    responses.extend(manual_key)
    print(im_loc + ' reading complete')

    return samples, responses


if __name__ == '__main__':
    samples = np.empty((0, 100))
    responses = []
    images = glob.glob('./ocr_imgs/*.png')
    print(images)
    for im_loc in images:
        samples, responses = read_image(im_loc, samples, responses)

    print(responses)
    responses = np.array(responses, np.float32)
    responses = responses.reshape((responses.size, 1))

    np.savetxt('generalsamples.data', samples)
    np.savetxt('generalresponses.data', responses)
