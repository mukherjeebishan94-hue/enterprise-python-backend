from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate


# --- Category Operations ---
async def create_category(db: AsyncSession, category_in: CategoryCreate) -> Category:
    """Create a new product category."""
    db_category = Category(name=category_in.name, description=category_in.description)
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


async def get_categories(db: AsyncSession) -> List[Category]:
    """Retrieve all categories."""
    result = await db.execute(select(Category))
    return result.scalars().all()


async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
    """Retrieve category by ID."""
    result = await db.execute(select(Category).filter(Category.id == category_id))
    return result.scalars().first()


# --- Product Operations ---
async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    """Create a new product."""
    db_product = Product(**product_in.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Reload with relationship loaded for response schema
    return await get_product_by_id(db, db_product.id)


async def get_products(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 20, 
    category_id: Optional[int] = None,
    search: Optional[str] = None
) -> List[Product]:
    """Fetch paginated products with optional filtering and search."""
    query = select(Product).options(selectinload(Product.category)).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Retrieve single product by ID with eager loaded category."""
    query = select(Product).options(selectinload(Product.category)).filter(Product.id == product_id)
    result = await db.execute(query)
    return result.scalars().first()


async def update_product(
    db: AsyncSession, db_product: Product, product_in: ProductUpdate
) -> Product:
    """Update existing product fields dynamically."""
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return await get_product_by_id(db, db_product.id)