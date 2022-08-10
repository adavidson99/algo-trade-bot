import yfinance as yf
from pathlib import Path
import csv
import pandas as pd
import pandas_ta as ta
import time
from telegram_bot import Telegram
from apscheduler.schedulers.background import BackgroundScheduler


class Stocks:

    def __init__(self):
        self.tickers = ['AAPL', 'MSFT', 'AMD', 'GOOGL', 'F']  # temporarily 5 stocks will be all 500
        self.ticker_list = []
        self.held = {}
        self.waitingBuy = {}  # company and recommended price of the stock to buy at
        self.waitingSell = {}  # company and recommended price of the stock to sell at

    def add_company(self, stock, price):
        self.waitingBuy[stock] = price
        telegram = Telegram()
        telegram.send(f"buy {stock} at {price}")
        print(f"buy {stock} at {price}")

    def buy_company(self, stock, recommended_price):
        price = int(input(f"Price {stock} bought at? "))
        self.held[stock] = price
        price_difference = recommended_price - price

    def remove_company(self, stock, price):
        self.waitingSell[stock] = price
        telegram = Telegram()
        telegram.send(f"sell {stock} at {price}")  # to do: calculate the lowest price to sell / max price to buy
        print(f"sell {stock} at {price}")

    def check_waiting_list(self):
        if self.waitingSell:
            for stock, price in self.waitingSell:
                self.sell_company(stock, price)
        if self.waitingBuy:
            for stock, price in self.waitingBuy:
                self.buy_company(stock, price)

    def sell_company(self, stock, recommended_price):
        price = input(f"Price {stock} sold at? ")
        try:
            price = float(price)
        except ValueError:
            print("Error, Try again")
            self.sell_company(stock, recommended_price)
        self.held[stock] = price
        price_difference = recommended_price - price

    def refresh_program(self):
        self.update_tickers()

        for stock, trend, rsi, price in self.ticker_list:
            if trend > 0 and rsi < 30 and not self.held[stock]:
                self.add_company(stock, price)

            if stock in self.held and rsi > 70:
                self.remove_company(stock, price)

            if stock in self.held and (self.held[stock] - (self.held[stock] / 10)) > price:
                # if equity is being held and the current price is 10% less than the buy price
                self.remove_company(stock, price)

        print("refreshed")

    def update_tickers(self):
        yf.pdr_override()
        self.tickers.sort()
        for ticker in self.tickers:
            data = yf.download(ticker, group_by='Ticker', period="1mo", interval='1h')
            data['Ticker'] = ticker
            data.to_csv(f'ticker_{ticker}.csv')

    def ticker_data(self):
        p = Path('C:\\Users\\adamg\\PycharmProjects\\ticker')
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


"""
def holding_data():
    holding_list = []
    tickers.sort()
    p = Path('C:\\Users\\adamg\\PycharmProjects\\ticker')
    datafile = p / 'sp_500_stocks.csv'
    if datafile.exists():

        with open(datafile, 'r') as _filehandler:

            csv_file_reader = csv.DictReader(_filehandler)

            for row in csv_file_reader:

                name = row['Ticker']
                held = int(row['Held'])
                price = float(row['Price'])
                holding_list.append((name, held, price))

    return holding_list
"""


def main():
    s = Stocks()
    s.ticker_data()
    s.refresh_program()

    sched = BackgroundScheduler()
    sched.configure(timezone='US/Eastern')
    sched.add_job(s.refresh_program, trigger='cron', day_of_week='mon-fri',
                  hour='1-4',
                  minute='*/2')
    sched.start()

    while True:
        s.check_waiting_list()
        time.sleep(60)


if __name__ == '__main__':
    main()
