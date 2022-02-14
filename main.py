import yfinance as yf
from pathlib import Path
import csv
import pandas as pd
import pandas_ta as ta
from apscheduler.schedulers.blocking import BlockingScheduler


tickers = ['AAPL', 'MSFT', 'AMD', 'GOOGL', 'F']   # temporarily 5 stocks will be all 500


def buy(data, holding_list, index):
    """place the order to buy the stock"""
    holding_list[index] = (holding_list[index][0], 1, data[3])  # shows the equity is now held and price it was bought
    print(f'buy {data}')
    print(holding_list)
    return holding_list


def sell(data, holding_list, index):
    """sell the already held order on a stock"""
    holding_list[index] = (holding_list[index][0], 0, data[3])  # shows the equity is now sold and price sold at
    print(f'sell {data}')
    return holding_list


def rsi_calculation(file):
    df = pd.read_csv(file, header=0)
    df['RSI'] = ta.rsi(df['Close'])
    df.to_csv(file)


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


def ticker_data():
    ticker_list = []
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
            ticker_list.append((name, trend, rsi, end))

    return ticker_list


def update_tickers():
    yf.pdr_override()

    tickers.sort()
    for ticker in tickers:
        data = yf.download(ticker, group_by='Ticker', period="1mo", interval='1h')
        data['Ticker'] = ticker
        data.to_csv(f'ticker_{ticker}.csv')


def refresh_program(ticker_list, holding_list):

    for index, data in enumerate(ticker_list):

        if data[1] > 0 and data[2] < 30 and holding_list[index][0] == 0:
            holding_list = buy(data, holding_list, index)

        if holding_list[index][0] == 1 and data[2] > 70:
            holding_list = sell(data, holding_list, index)

        if holding_list[index][0] == 1 and (holding_list[index][1] - (holding_list[index][1] / 10)) > data[3]:
            # if equity is being held and the current price is 10% less than the buy price
            holding_list = sell(data, holding_list, index)

    update_tickers()


def main():

    update_tickers()
    ticker_list = ticker_data()
    holding_list = holding_data()

    print(ticker_list)
    print(holding_list)

    refresh_program(ticker_list, holding_list)

    sched = BlockingScheduler()
    sched.configure(timezone='US/Eastern')
    sched.add_job(refresh_program, trigger='cron', args=[ticker_list, holding_list], day_of_week='mon-fri', hour='9-16',
                  minute='*/15')
    sched.start()


if __name__ == '__main__':
    main()

"""
ADD ANOTHER JOB SCHEDULE TO UPDATE THE TICKERS ABOUT A MINUTE BEFORE REFRESHING THE PROGRAM
"""