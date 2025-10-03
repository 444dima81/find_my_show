from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct,VectorParams, Distance
import math

# 1️⃣ Подключение к облачному Qdrant
cloud_client = QdrantClient(
    url="https://3332fb57-c252-45fc-9af4-d01551ed3889.eu-central-1-0.aws.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.qEJ2rYHHI-rLFsI809yjzC3QLqyPPVfln99gzokKJOg",
)

# 2️⃣ Подключение к локальной базе
local_client = QdrantClient(path="../data/qdrant_db_backup/db/qdrant_db")  # путь к локальной БД

print("📁 Коллекции в локальной базе:")
print(local_client.get_collections())

# 3️⃣ Считываем все точки из локальной коллекции
points, _ = local_client.scroll(
    collection_name="demo_collection",
    with_payload=True,
    with_vectors=True,
    limit=100000  
)

print(f"📦 Найдено точек для миграции: {len(points)}")

# 4️⃣ Создаём коллекцию в облаке (если не создана)
cloud_client.recreate_collection(
    collection_name="demo_collection",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)
print("✅ Коллекция в облаке готова!")

# 5️⃣ Отправляем данные батчами
BATCH_SIZE = 500
for i in range(0, len(points), BATCH_SIZE):
    batch = points[i:i+BATCH_SIZE]
    cloud_client.upsert(
        collection_name="demo_collection",
        points=[
            PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload
            )
            for p in batch
        ]
    )
    print(f"✅ Отправлен батч {i//BATCH_SIZE + 1}/{math.ceil(len(points) / BATCH_SIZE)} ({len(batch)} точек)")

# 6️⃣ Проверяем количество точек в облачной коллекции
count = cloud_client.count(collection_name="demo_collection").count
print(f"🌐 Количество точек в облачной коллекции: {count}")