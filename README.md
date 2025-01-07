# Macro Signals Notifier

This project monitors multiple crypto macro market signals and sends Telegram messages and emails to users. The objective of the project is to provide daily reminders that influence trading decisions. For example, as the market becomes overheated, we may want to de-risk our positions.

This project is forked from [CBBI](https://github.com/Zaczero/CBBI) project.

# Data Sources

To start, there are two main data sources:

1. [CBBI](https://github.com/Zaczero/CBBI) - A Python implementation of the ColinTalksCrypto Bitcoin Bull Run Index (CBBI).
2. [TechDev](https://www.techdev52.com/) - A newsletter that provides technical analysis of the crypto market.

In the near future, we will add additional data sources, including:

1. [ETF Inflows and Outflows](https://farside.co.uk/)
2. [Open Interest on Crypto Futures](https://www.coinglass.com/)
3. Reminders for upcoming events(e.g. FOMC meetings, CPI, etc.)