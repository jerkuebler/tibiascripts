import collections
import configparser
import re
import sys
import time
import ast
import win32gui
import win32ui
from ctypes import windll

import pywinauto
from multiprocessing import Process

from PIL import Image
from appJar import gui

HWND = 0


def window_enum_callback(hwnd, wildcard):
    """Pass to win32gui.EnumWindows() to check all the opened windows"""
    if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
        global HWND
        HWND = hwnd


def find_window_wildcard(wildcard):
    """find a window whose title matches the wildcard regex"""
    win32gui.EnumWindows(window_enum_callback, wildcard)


def key_timer(key, interval):
    global HWND
    if HWND == 0:
        HWND = win32gui.FindWindow(None, 'Tibia')

    if HWND == 0:
        find_window_wildcard('Tibia -*')

    pwa_app = pywinauto.application.Application()
    connect = pwa_app.connect(handle=HWND)
    window = pwa_app.window(handle=HWND)

    while True:
        print('Sending Key')
        window.send_keystrokes(key)
        print('Sleeping ' + interval)
        time.sleep(int(interval))


def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    sv = config['saved']
    health_pack = [ast.literal_eval(sv['health_loc']),
                   ast.literal_eval(sv['health_target']),
                   ast.literal_eval(sv['health_box'])]

    mana_pack = [ast.literal_eval(sv['mana_loc']),
                 ast.literal_eval(sv['mana_target']),
                 ast.literal_eval(sv['mana_box'])]

    ring_pack = [ast.literal_eval(sv['ring_loc']),
                 ast.literal_eval(sv['ring_target']),
                 ast.literal_eval(sv['ring_box'])]

    return {'Health': health_pack, 'Mana': mana_pack, 'Ring': ring_pack}


def most_common(lst):
    data = collections.Counter(lst)
    return data.most_common(1)[0][0]


class Bot:
    def __init__(self):

        self.app = gui('Monitor', useTtk=True, showIcon=False)
        self.app.setTtkTheme('vista')
        self.app.favicon = None
        self.app.setStopFunction(self.shut_down)

        self.pool = []
        self.packs = load_config()

        global HWND
        HWND = win32gui.FindWindow(None, 'Tibia')
        if HWND == 0:
            find_window_wildcard('Tibia -*')

        self.pwa_app = pywinauto.application.Application()
        self.connect = self.pwa_app.connect(handle=HWND)
        self.window = self.pwa_app.window(handle=HWND)

        # Change the line below depending on whether you want the whole window
        # or just the client area.
        left, top, right, bot = win32gui.GetClientRect(HWND)  # client area
        # left, top, right, bot = win32gui.GetWindowRect(hwnd) # window area
        w = right - left
        h = bot - top

        self.hwndDC = win32gui.GetWindowDC(HWND)
        self.mfcDC = win32ui.CreateDCFromHandle(self.hwndDC)
        self.saveDC = self.mfcDC.CreateCompatibleDC()

        self.saveBitMap = win32ui.CreateBitmap()
        self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)

        def press(button):
            if button == 'New Monitor':
                self.monitor_setup()
            elif button == 'New Repeat Key':
                self.repeat_key()
            elif button == 'Stop All':
                for index, p in enumerate(self.pool):
                    p.terminate()
                self.app.deleteAllTableRows('process')
                del self.pool[:]
            elif button == 'Test Pic':
                self.bg_test_pic()
            elif button == 'Update Colors':
                self.bg_update_color()
                print('Loading config')
                self.packs = load_config()

        self.app.addButtons(['New Monitor', 'New Repeat Key', 'Stop All', 'Test Pic', 'Update Colors'], press)
        data = [['Process', 'Stat', 'Key', 'Target Value']]
        self.app.addTable(title="process", data=data, action=self.stop_process)
        self.app.go()

    def take_pic(self, coords=None):

        self.saveDC.SelectObject(self.saveBitMap)
        result = windll.user32.PrintWindow(HWND, self.saveDC.GetSafeHdc(), 1)  # client area
        # result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0) # window area

        bmpinfo = self.saveBitMap.GetInfo()
        bmpstr = self.saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        if coords:
            im = im.crop(coords)

        return im

    def bg_update_color(self):
        bar = (8, 88)
        config = configparser.ConfigParser()
        config.read('config.ini')
        sv = config['saved']
        print('Updating color targets')

        for pack in self.packs:
            print(pack)
            y, target, bbox = self.packs[pack]
            img = self.take_pic(coords=bbox)
            px = img.load()
            img.save("./imgs/" + pack + " test.png")

            colors = []
            if pack == 'Ring':
                bar = (0, 1)

            for i in range(bar[0], bar[1]):
                colors.append(px[i, y])

            color = most_common(colors)
            setting = pack.lower() + "_target"
            sv[setting] = str(color)

            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print(color)
            print('Saved ' + pack + ': ' + str(color))

    def bg_test_pic(self):
        bar = (8, 82)

        print("Test img")
        img = self.take_pic()
        img.save("./imgs/test.png")
        for pack in self.packs:
            print("Test img for " + pack)
            y, target, bbox = self.packs[pack]
            img = self.take_pic(coords=bbox)
            px = img.load()

            colors = []
            if pack == 'Ring':
                bar = (0, 1)

            print(bar)
            for i in range(bar[0], bar[1]):
                colors.append(px[i, y])

            print(pack + ' ' + str(target))
            print(colors)

            img.save('./imgs/' + pack + ' test.png')

        print('Images Saved')

    def shut_down(self):

        for p in self.pool:
            p.terminate()
        sys.exit()

    def stop_process(self, pnum):
        p = self.pool[pnum]
        p.terminate()
        del self.pool[pnum]
        self.app.deleteTableRow('process', pnum)

    def check_stat(self, key, at, pack):

        y, target, bbox = pack
        bar = (8, 82)
        bar_len = bar[1] - bar[0]
        req_health = int(bar_len * (int(at) / 100)) + bar[0]

        while True:

            img = self.take_pic(coords=bbox)
            px = img.load()

            if px[req_health, y] != target:
                self.window.send_keystrokes(key)
                time.sleep(0.8)

            """print(target)
            colors = []
            for i in range(bar[0], bar[1]):
                colors.append(px[i, y])

            print(colors)"""  # easy color debugging. Maybe used for color recognition in future.

            time.sleep(0.2)

    def check_ring(self, key, interval, pack):

        y, target, bbox = pack
        x = 0

        while True:

            img = self.take_pic(coords=bbox)
            px = img.load()

            if px[x, y] != target:
                self.window.send_keystrokes(key)
                time.sleep(int(interval))

            """print(target)
            colors = []
            for i in range(bar[0], bar[1]):
                colors.append(px[i, y])

            print(colors)"""  # easy color debugging. Maybe used for color recognition in future.

            time.sleep(0.2)

    def repeat_key(self):
        self.app.startSubWindow("monitor", modal=True)
        self.app.favicon = None

        self.app.addLabel('Key')
        self.app.addEntry('key')
        self.app.setEntry("key", "6")

        self.app.addLabel("Interval (Seconds)")
        self.app.addEntry('at')
        self.app.setEntry("at", "15")

        def press(button):
            key = self.app.getEntry('key')
            at = self.app.getEntry('at')

            if button == 'Start':
                p = Process(name=key + ' Repeat', target=key_timer, args=(self.window, key, at,))
                self.app.addTableRow('process', [p, 'Repeat', key, at])
                p.start()
                self.pool.append(p)
                self.app.destroySubWindow('monitor')

            elif button == 'Cancel':
                self.app.destroySubWindow('monitor')

        self.app.addButtons(['Start', 'Cancel'], press)

        self.app.stopSubWindow()

        self.app.showSubWindow('monitor')

    def monitor_setup(self):
        self.app.startSubWindow("monitor", modal=True)
        self.app.favicon = None

        self.app.addLabel('Monitor Type')
        self.app.addRadioButton("stat", "Health")
        self.app.addRadioButton("stat", "Mana")
        self.app.addRadioButton("stat", "Ring")
        self.app.addRadioButton("stat", "Temp")

        self.app.addLabel('Key')
        self.app.addEntry('key')
        self.app.setEntry("key", "3")

        self.app.addLabel("Trigger % (20 - 80)")
        self.app.addEntry('at')
        self.app.setEntry("at", "75")

        def press(button):
            if button == 'Start':

                stat = self.app.getRadioButton('stat')
                key = self.app.getEntry('key')
                at = self.app.getEntry('at')
                if stat == "Ring":
                    p = Process(name=str(self.packs[stat][0]), target=self.check_ring,
                                args=(key, at, self.packs[stat],))
                elif stat == 'Temp':
                    p = 'Temp'
                    self.check_stat(key, at, self.packs[stat])
                else:
                    p = Process(name=str(self.packs[stat][0]), target=self.check_stat,
                                args=(key, at, self.packs[stat],))
                self.app.addTableRow('process', [p, stat, key, at])
                p.start()
                self.pool.append(p)
                self.app.destroySubWindow('monitor')

            elif button == 'Cancel':
                self.app.destroySubWindow('monitor')

        self.app.addButtons(['Start', 'Cancel'], press)

        self.app.stopSubWindow()

        self.app.showSubWindow('monitor')


if __name__ == '__main__':
    Bot()
