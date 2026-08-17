import json
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate, ProductResponse
from app.core.redis import get_redis

CACHE_EXPIRE_SECONDS = 300  # 5 minutes cache TTL


# --- Helper: Cache Invalidation ---
async def invalidate_product_cache(product_id: Optional[int] = None):
    """Invalidates product cache keys in Redis upon mutation."""
    redis = await get_redis()
    keys_to_delete = ["products:list"]
    if product_id:
        keys_to_delete.append(f"product:{product_id}")
    await redis.delete(*keys_to_delete)


# --- Category Operations ---
async def create_category(db: AsyncSession, category_in: CategoryCreate) -> Category:
    db_category = Category(name=category_in.name, description=category_in.description)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


async def get_categories(db: AsyncSession) -> List[Category]:
    result = await db.execute(select(Category))
    return result.scalars().all()


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
    result = await db.execute(select(Category).filter(Category.id == category_id))
    return result.scalars().first()


# --- Product Operations with Redis Caching ---
async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    db_product = Product(**product_in.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Invalidate list cache so newly created product appears
    await invalidate_product_cache()
    
    return await get_product_by_id(db, db_product.id)


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    redis = await get_redis()
    cache_key = f"product:{product_id}"

    # 1. Try fetching from Redis Cache
    cached_data = await redis.get(cache_key)
    if cached_data:
        # Cache Hit: Construct response from cached JSON
        data = json.loads(cached_data)
        return ProductResponse(**data)

    # 2. Cache Miss: Query PostgreSQL Database
    query = select(Product).options(selectinload(Product.category)).filter(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalars().first()

    if product:
        # Serialize Pydantic object and store in Redis with expiration
        product_schema = ProductResponse.model_validate(product)
        await redis.setex(
            cache_key, 
            CACHE_EXPIRE_SECONDS, 
            product_schema.model_dump_json()
        )

    return product


async def get_products(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 20, 
    category_id: Optional[int] = None,
    search: Optional[str] = None
) -> List[Product]:
    query = select(Product).options(selectinload(Product.category)).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_product(
    db: AsyncSession, db_product: Product, product_in: ProductUpdate
) -> Product:
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    # Invalidate specific product and list caches
    await invalidate_product_cache(product_id=db_product.id)

    return await get_product_by_id(db, db_product.id)