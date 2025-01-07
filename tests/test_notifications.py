import asyncio
from notifications.service import NotificationService
from techdev_metrics.base_metric import TechnicalIndicator

async def test_basic_notifications():
    service = NotificationService()
    
    print("Testing CBBI notification...")
    await service.send_cbbi_update(
        price=45000.0,
        confidence_score=0.65,
        confidence_details={
            "Pi Cycle Top": 0.7,
            "RHODL Ratio": 0.6,
            "Puell Multiple": 0.4,
        }
    )
    print("CBBI notification sent!")
    
    print("\nTesting TechDev notification...")
    sample_indicator = TechnicalIndicator(
        name="MACD",
        description="MACD showing bullish crossover",
        trigger_value="Above signal line",
        reference_urls=["https://www.tradingview.com/chart"]
    )
    
    await service.send_techdev_update(
        price=45000.0,
        indicators=[sample_indicator]
    )
    print("TechDev notification sent!")

if __name__ == "__main__":
    asyncio.run(test_basic_notifications()) 