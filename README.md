# algo-trade-bot
An algorithmic trading scripts that recommends and logs buy and sell orders on the Australian and New Zealand stock markets

## Instructions

- Clone repository 
- go to https://my.telegram.org/auth?to=apps to use an api linking to your telegram account, so that the script can ping your phone whenever an update comes through
- Enter details in telegram_bot.py so that the api works
- run main.py during the nz and aus market open hours of 10am - 6pm every day (NZST)

## Algorithm

- recommends buying shares in a company if the relative stength index (rsi) is below 30 and the stock is trending upwards
- recommends selling shares if the rsi is above 70 or the 10% stop-loss value has been reached. 
