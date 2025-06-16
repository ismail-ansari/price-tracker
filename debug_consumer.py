# debug_consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "price-events",
    bootstrap_servers=["localhost:9092"],
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

print("Listening for enriched events…")
for msg in consumer:
    print(msg.value)
    # exit after first for a quick test:
    break