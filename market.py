import datetime
import sys
import time
import win32api
from win32gui import GetWindowText, GetForegroundWindow

import numpy
import pandas as pd
import win32com.client
import win32con

from PIL import Image
import PIL.ImageGrab
from appJar import gui

import use_ocr


def binarize_image(img_path):
    """Binarize an image."""
    image_file = Image.open(img_path)
    image = image_file.convert('L')  # convert image to monochrome
    image = numpy.array(image)
    image = binarize_array(image)
    im = Image.fromarray(image)
    return im


def binarize_array(numpy_array):
    """Binarize a numpy array."""
    for i in range(len(numpy_array)):
        rng = len(numpy_array[0])
        for j in range(rng):
            if 78 > numpy_array[i][j] or numpy_array[i][j] > 150:
                numpy_array[i][j] = 255
            else:
                numpy_array[i][j] = 0

    return numpy_array


def click(x, y):
    win32api.SetCursorPos((x, y))
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    time.sleep(0.01)


def slow_keys(shell, keys):
    for key in keys:
        shell.SendKeys(key)
        time.sleep(0.05)


class Bot:
    def __init__(self):

        self.app = gui('Market', useTtk=True, showIcon=False)
        self.app.setPadding([20, 20])
        self.app.setTtkTheme('vista')
        self.app.favicon = None
        self.model = use_ocr.train_model()
        self.xl = pd.ExcelFile('.\\xl\\npc_items.xlsx')
        self.sheets = self.xl.sheet_names

        def press(button):

            if button == 'Start' or button == 'Auto':
                self.writer = pd.ExcelWriter('.\\xl\\npc_items_output.xlsx', engine='xlsxwriter')

            if button == 'Start':

                start = datetime.datetime.now()
                sheets = self.app.getAllCheckBoxes()

                for sheet in sheets:
                    print(sheet)
                    current = datetime.datetime.now() - start
                    cont = self.app.questionBox('Continue', 'Reading %s, %s since start, continue?' % (sheet, current))
                    if cont:
                        df = self.xl.parse(sheet)
                        self.check_market(df, sheet)
                    else:
                        sys.exit()

                self.writer.save()
                print('All done!')

            elif button == 'Auto':

                for sheet in self.sheets:
                    df = self.xl.parse(sheet)
                    self.check_market(df, sheet)

                self.writer.save()
                print('All done!')

            elif button == 'Coin':
                print('Updating Coin Spreadsheet')
                self.update_coin()

            elif button == 'Exit':
                sys.exit()

        self.app.addLabel('Press Start with Tibia in full screen and market open in default position')

        self.app.addLabel('Select categories to scan')

        for sheet in self.sheets:
            self.app.addCheckBox(sheet)

        self.app.addButtons(['Start', 'Auto', 'Coin', 'Exit'], press)
        self.app.go()

    def process_image(self, bbox):
        img = PIL.ImageGrab.grab(bbox=bbox)
        img.save('test.png')
        im = binarize_image('test.png')
        im.save('test.png')

        value = use_ocr.use_model(self.model, 'test.png')

        return value

    def update_coin(self):

        df = pd.read_excel('.\\xl\\coin.xlsx', index_col=None)
        write = pd.ExcelWriter('.\\xl\\coin.xlsx', engine='xlsxwriter')
        shell = win32com.client.Dispatch("WScript.Shell")

        while True:
            if "Tibia" in GetWindowText(GetForegroundWindow()):
                click(600, 800)
                click(600, 800)
                click(600, 800)
                slow_keys(shell, 'tibia coins')
                click(575, 410)
                time.sleep(0.5)
                buy_offer = self.process_image((970, 533, 1065, 550))
                sell_offer = self.process_image((970, 307, 1065, 324))
                buy_amount = self.process_image((900, 533, 957, 550))
                sell_amount = self.process_image((900, 307, 957, 324))
                offers = (buy_offer, buy_amount, sell_offer, sell_amount)
                print('Buy Offer: %s Amount: %s \nSell Offer: %s Amount: %s\n' % offers)
                now = [datetime.datetime.now()]
                now.extend(offers)

                values = dict(zip(['time', 'buy_offer', 'buy_amount', 'sell_offer', 'sell_amount'], now))
                mdf = pd.DataFrame(data=values, index=[1])

                print(mdf)
                df = df.append(mdf, ignore_index=True)

                print(df)
                df.to_excel(write, index=False)
                write.save()
                print('All done!')

                break
            else:
                print('Click on Tibia and don\'t touch until the next popup!')
                time.sleep(3)

    def check_market(self, market_df, xl_sheet):

        shell = win32com.client.Dispatch("WScript.Shell")

        while True:
            if "Tibia" in GetWindowText(GetForegroundWindow()):
                buy_offers = []
                sell_offers = []
                buy_amounts = []
                sell_amounts = []
                for index, row in market_df.iterrows():
                    print(row['item'])
                    click(600, 800)
                    click(600, 800)
                    click(600, 800)
                    slow_keys(shell, row['item'])
                    click(575, 410)
                    time.sleep(0.5)
                    # (970, 307, 1065, 324) Sell offer
                    # (970, 533, 1065, 550) Buy offer
                    # (900, 307, 957, 324) Sell Amount
                    # (900, 533, 957, 550) Buy Amount
                    buy_offer = self.process_image((970, 533, 1065, 550))
                    sell_offer = self.process_image((970, 307, 1065, 324))
                    buy_amount = self.process_image((900, 533, 957, 550))
                    sell_amount = self.process_image((900, 307, 957, 324))
                    buy_offers.append(buy_offer)
                    sell_offers.append(sell_offer)
                    buy_amounts.append(buy_amount)
                    sell_amounts.append(sell_amount)
                    offers = (buy_offer, buy_amount, sell_offer, sell_amount)
                    print('Buy Offer: %s Amount: %s \nSell Offer: %s Amount: %s\n' % offers)
                    time.sleep(0.1)

                break
            else:
                print('Click on Tibia and don\'t touch until the next popup!')
                time.sleep(3)

        mdf = market_df
        tn = pd.to_numeric
        mdf['Buy Offers'] = buy_offers
        mdf['Sell Offers'] = sell_offers
        mdf['Buy Amounts'] = buy_amounts
        mdf['Sell Amounts'] = sell_amounts
        mdf['1 Sell Offer to NPC'] = tn(mdf['npc_price'], errors='coerce') - tn(mdf['Sell Offers'], errors='coerce')
        mdf['2 Buy Offer to NPC'] = tn(mdf['npc_price'], errors='coerce') - tn(mdf['Buy Offers'], errors='coerce')
        mdf['Percent Return 1'] = mdf['1 Sell Offer to NPC'] / mdf['Sell Offers']
        mdf['Percent Return 2'] = mdf['2 Buy Offer to NPC'] / mdf['Buy Offers']
        mdf['Potential 1'] = mdf['1 Sell Offer to NPC'] * mdf['Sell Amounts']
        mdf['Potential 2'] = mdf['2 Buy Offer to NPC'] * mdf['Buy Amounts']

        mdf.to_excel(self.writer, sheet_name=xl_sheet)
        print('%s complete\n' % xl_sheet)


if __name__ == '__main__':
    Bot()
