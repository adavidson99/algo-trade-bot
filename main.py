import yfinance as yf
from pathlib import Path
import csv
import pandas as pd
import pandas_ta as ta
import time
import requests
from pytimedinput import timedInput
import bs4 as bs
from telegram_bot import Telegram


# have csv file for the stocks held so if program goes down then the information will still be there
class Stocks:

    def __init__(self, held, tickers):
        self.tickers = tickers
        self.ticker_list = []
        self.held = held
        self.count = 0
        self.waitingBuy = {}  # company and recommended price of the stock to buy at
        self.waitingSell = {}  # company and recommended price of the stock to sell at
        self.timer = time.time()

    def add_company(self, stock, price):
        self.waitingBuy[stock] = price
        telegram = Telegram()
        telegram.send(f"buy {stock} at {price}")
        print(f"buy {stock} at {price}")

    def buy_company(self, stock, recommended_price):
        price, timed_out = timedInput(f"Price {stock} bought at? ", timeout=30)
        if not timed_out:
            shares = input(f"Number of shares? ")
            try:
                price = float(price)
                shares = float(shares)
            except ValueError:
                print("Error, not a valid value")
                self.buy_company(stock, recommended_price)
            self.held[stock] = (price, shares)
            df = pd.read_csv('nzx_50_stocks.csv')
            df.loc[df['Ticker'] == stock, 'Price'] = price
            df.loc[df['Ticker'] == stock, 'Held'] = 1
            df.loc[df['Ticker'] == stock, 'Shares'] = shares
            df.loc[df['Ticker'] == stock, 'Profit'] -= (price * shares)
            df.to_csv('nzx_50_stocks.csv')
            print(f"Bought {shares} shares of {stock} at {price}")

    def sell_company(self, stock, recommended_price):
        price, timed_out = timedInput(f"Price {stock} sold at? ", timeout=30)
        if not timed_out:
            bought_price = self.held[stock][0]
            shares = self.held[stock][1]
            try:
                price = float(price)
                shares = float(shares)
            except ValueError:
                print("Error, Try again")
                self.sell_company(stock, recommended_price)
            del self.held[stock]
            df = pd.read_csv('nzx_50_stocks.csv')
            df.loc[df['Ticker'] == stock, 'Price'] = 0
            df.loc[df['Ticker'] == stock, 'Held'] = 0
            df.loc[df['Ticker'] == stock, 'Shares'] = 0
            df.loc[df['Ticker'] == stock, 'Profit'] += (price * shares)
            df.loc[df['Ticker'] == stock, 'Pct_dif'] += ((price - bought_price) / bought_price) * 100
            df.to_csv('nzx_50_stocks.csv')
            print(f"Sold {stock} at {price}")

    def remove_company(self, stock, price):
        self.waitingSell[stock] = price
        # telegram = Telegram()
        # telegram.send(f"sell {stock} at {price}")  # to do: calculate the lowest price to sell / max price to buy
        print(f"sell {stock} at {price}")

    def check_waiting_list(self):
        if self.waitingSell:
            for stock, price in self.waitingSell.items():
                self.count += 1
                self.sell_company(stock, price)
                if self.count == len(self.waitingSell):
                    self.waitingBuy = {}
                    self.count = 0

        if self.waitingBuy:
            for stock, price in self.waitingBuy.items():
                self.count += 1
                self.buy_company(stock, price)
                if self.count == len(self.waitingBuy):
                    self.waitingBuy = {}
                    self.count = 0

    def refresh_program(self):
        self.update_tickers()
        self.ticker_data()

        for stock, trend, rsi, price in self.ticker_list:
            if trend > 0 and rsi < 30 and stock not in self.held:
                self.add_company(stock, price)

            if stock in self.held and rsi > 70:
                self.remove_company(stock, price)

            if stock in self.held and (self.held[stock][0] - (self.held[stock][0] / 10)) > price:
                # if equity is being held and the current price is 10% less than the buy price
                self.remove_company(stock, price)

            # if stock in self.held and self.held[stock][2] (days held) > 30:
                # self.remove_company(stock, price)

        print(f"held stocks: {self.held}")
        self.check_waiting_list()

    def update_tickers(self):
        yf.pdr_override()
        for ticker in self.tickers:
            data = yf.download(ticker, group_by='Ticker', period="1mo", interval='1h')
            if not data.empty:
                data['Ticker'] = ticker
                data.to_csv(f'ticker_{ticker}.csv')

    def ticker_data(self):
        p = Path('C:\\Users\\adamg\\ticker')
        files = p.glob('ticker_*.csv')
        for file in files:
            rsi_calculation(file)
            with open(file, 'r') as _filehandler:
                csv_file_reader = csv.DictReader(_filehandler)
                rownum = 0
                for row in csv_file_reader:
                    if rownum == 1:
                        start = float(row['Open'])

                    rownum += 1

                try:
                    end = float(row['Close'])
                    rsi = float(row['RSI'])
                    name = row['Ticker']
                    trend = end - start
                    self.ticker_list.append((name, trend, rsi, end))

                except ValueError:
                    pass


def rsi_calculation(file):
    df = pd.read_csv(file, header=0)
    df['RSI'] = ta.rsi(df['Close'])
    df.to_csv(file)


def holding_data():
    # returns a list of all currently held stocks
    holding_list = {}
    datafile = 'nzx_50_stocks.csv'
    with open(datafile, 'r') as _filehandler:
        csv_file_reader = csv.DictReader(_filehandler)
        for row in csv_file_reader:
            name = row['Ticker']
            held = int(row['Held'])
            price = float(row['Price'])
            shares = float(row['Shares'])
            if held == 1:
                holding_list[name] = (price, shares)

    return holding_list


def update_ticker_file(tickers):
    # writes a new file containing the stocks and initializes the other parameters if file does
    # not already exist. Otherwise, appends any missing stocks onto current file if any have been
    # added to the index
    current_tickers = set()
    datafile = 'nzx_50_stocks.csv'
    try:
        with open(datafile, 'r', newline='') as csvfile:
            info = csv.reader(csvfile, delimiter='\t')
            for row in info:
                ticker = row[0].split(',')[1]
                current_tickers.add(ticker)

            csvfile.close()

        with open(datafile, 'a', newline='') as csvfile:
            # add new tickers into the csv file in case there has been new stocks added to the index.
            new_tickers = tickers.difference(current_tickers)
            for t in new_tickers:
                info = csv.writer(csvfile)
                info.writerow([t, 0, 0, 0])

            csvfile.close()

    except FileNotFoundError:
        # create a csv file with all the tickers if a current one doesn't exist.
        with open(datafile, 'w', newline='') as csvfile:
            info = csv.writer(csvfile)
            info.writerow(['Ticker', 'Held', 'Price', 'Profit'])
            for key in tickers:
                info = csv.writer(csvfile)
                info.writerow([key, 0, 0, 0])

            csvfile.close()


def save_tickers():
    tickers = []
    nz = requests.get('https://en.wikipedia.org/wiki/S%26P/NZX_50_Index')
    nz_soup = bs.BeautifulSoup(nz.text, 'lxml')
    nz_table = nz_soup.find('table', {'class': 'wikitable sortable'})
    for row in nz_table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        nz_ticker = ticker.replace("\n", "")
        tickers.append(nz_ticker)

    aus = requests.get('https://en.wikipedia.org/wiki/S%26P/ASX_200')
    aus_soup = bs.BeautifulSoup(aus.text, 'lxml')
    aus_table = aus_soup.find('table', {'class': 'wikitable sortable'})
    for row in aus_table.findAll('tr')[1:]:#
        ticker = row.findAll('td')[0].text
        aus_ticker = ticker.replace("\n", ".AX")
        tickers.append(aus_ticker)

    return set(tickers)


def main():
    tickers = save_tickers()
    update_ticker_file(tickers)
    currently_held = holding_data()
    s = Stocks(currently_held, tickers)

    while True:
        # refresh every 5 minutes
        s.refresh_program()
        time.sleep(300)


if __name__ == '__main__':
    main()
