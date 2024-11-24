import asyncio
from aiokafka import AIOKafkaConsumer

async def consume():
    consumer = AIOKafkaConsumer(
        "crowd-nav-routing",  # 替换为你的 Kafka 主题
        bootstrap_servers="10.255.255.254:9092",  # 替换为宿主机 IP 和 Kafka 端口
        
        group_id=None,
        auto_offset_reset="earliest"
    )
    await consumer.start()
    try:
        print("Connected to Kafka. Listening for messages...")
        async for msg in consumer:
            print(f"Consumed message: {msg.value.decode('utf-8')}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())

