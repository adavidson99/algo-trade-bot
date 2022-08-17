import yfinance as yf
from pathlib import Path
import csv
import pandas as pd
import pandas_ta as ta
import time
import requests
import bs4 as bs
from telegram_bot import Telegram
from apscheduler.schedulers.background import BackgroundScheduler


# have csv file for the stocks held so if program goes down then the information will still be there
class Stocks:

    def __init__(self, held, tickers):
        self.tickers = tickers
        self.ticker_list = []
        self.held = held
        self.count = 0
        self.waitingBuy = {}  # company and recommended price of the stock to buy at
        self.waitingSell = {}  # company and recommended price of the stock to sell at

    def add_company(self, stock, price):
        self.waitingBuy[stock] = price
        telegram = Telegram()
        telegram.send(f"buy {stock} at {price}")
        print(f"buy {stock} at {price}")

    def buy_company(self, stock, recommended_price):
        price = input(f"Price {stock} bought at? ")
        try:
            price = float(price)
        except ValueError:
            print("Error, Try again")
            self.buy_company(stock, recommended_price)  # have maximum price instead of recommended
        self.held[stock] = price
        df = pd.read_csv('nzx_50_stocks.csv')
        df.loc[df['Ticker'] == stock, 'Price'] = price
        df.loc[df['Ticker'] == stock, 'Held'] = 1
        df.loc[df['Ticker'] == stock, 'Profit'] -= price
        df.to_csv('nzx_50_stocks.csv')
        print(f"Bought {stock} at {price}")

    def sell_company(self, stock, recommended_price):
        price = input(f"Price {stock} sold at? ")
        try:
            price = float(price)
        except ValueError:
            print("Error, Try again")
            self.sell_company(stock, recommended_price)
        del self.held[stock]
        df = pd.read_csv('sp_500_stocks.csv')
        df.loc[df['Ticker'] == stock, 'Price'] = 0
        df.loc[df['Ticker'] == stock, 'Held'] = 0
        df.loc[df['Ticker'] == stock, 'Profit'] += price
        df.to_csv('nzx_50_stocks.csv')
        print(f"Sold {stock} at {price}")

    def remove_company(self, stock, price):
        self.waitingSell[stock] = price
        telegram = Telegram()
        telegram.send(f"sell {stock} at {price}")  # to do: calculate the lowest price to sell / max price to buy
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

            if stock in self.held and (self.held[stock] - (self.held[stock] / 10)) > price:
                # if equity is being held and the current price is 10% less than the buy price
                self.remove_company(stock, price)

        print(f"updated_stocks: {self.ticker_list}")

    def update_tickers(self):
        yf.pdr_override()
        for ticker in self.tickers:
            data = yf.download(ticker, group_by='Ticker', period="1mo", interval='1h')
            data['Ticker'] = ticker
            data.to_csv(f'ticker_{ticker}.csv')

    def ticker_data(self):
        p = Path('C:\\Users\\adamg\\algo-trade-bot')
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

                end = float(row['Close'])
                rsi = float(row['RSI'])
                name = row['Ticker']
                trend = end - start
                self.ticker_list.append((name, trend, rsi, end))


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
            if held == 1:
                holding_list[name] = price

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
                ticker = row[0].split(',')[0]
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


def save_sp500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/S%26P/NZX_50_Index')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)

    result = [s.replace("\n", "") for s in tickers]

    return set(result)


def main():
    tickers = save_sp500_tickers()
    update_ticker_file(tickers)
    currently_held = holding_data()
    s = Stocks(currently_held, tickers)
    s.refresh_program()

    print(s.held)

    sched = BackgroundScheduler()
    sched.configure(timezone='US/Eastern')
    sched.add_job(s.refresh_program, trigger='cron', day_of_week='mon-fri',
                  hour='1-23',
                  minute='*/5')
    sched.start()

    while True:
        s.check_waiting_list()
        time.sleep(60)


if __name__ == '__main__':
    main()
