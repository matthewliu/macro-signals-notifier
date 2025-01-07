# Macro Signals Notifier To Do List

Below is our project plan. We will use the following status indicators:  
- ✅ = Completed  
- 🔄 = In Progress  
- ❌ = Not Started  

---

## 1. Get CBBI indicators working ✅
- ✅ Fork CBBI repo and confirm that we can generate our 9 indicators using a daily cron job

## 2. Set up notification service ✅
- ✅ Output Telegram and SendGrid notifications for CBBI indicators
- ✅ Generalize notification service to support other indicators
- ✅ Create notifications that link to TechDev indicators (TradingView charts)

## 3. Get TechDev indicators working ✅
- ✅ Analyze and understand technical indicators from https://www.techdev52.com/p/techdev-newsletter-market-update-5b4
- ✅ Add TechDev indicator links to notifications
- ✅ Decision: Use TradingView chart links instead of calculating indicators locally

## 4. Database and Schema ❌
- ❌ Create a new PostgreSQL database for the project
- ❌ Store data that is being scraped from CBBI, TechDev, and other sources
- ❌ Design schema for historical tracking of indicators

## 5. Add additional indicators ❌
- ❌ Consider calculcating TechDev indicators in code vs. referring to TradingView charts
- ❌ ETF inflows and outflows
- ❌ Open interest on crypto futures
- ❌ Sentiment analysis
- ❌ Additional technical indicators as identified

## 6. Monitoring and Reliability ❌
- ❌ Add logging and monitoring
- ❌ Implement error handling and retries
- ❌ Set up alerts for service health
- ❌ Create dashboard for system status

## 7. Documentation ❌
- ❌ Add comprehensive README
- ❌ Document API endpoints and data structures
- ❌ Add setup instructions
- ❌ Create contribution guidelines