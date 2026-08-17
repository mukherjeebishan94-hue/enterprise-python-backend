from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import UserRole
from app.api.deps import RoleChecker
from app.schemas.product import (
    CategoryCreate, CategoryResponse, 
    ProductCreate, ProductUpdate, ProductResponse
)
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products & Catalog"])


# --- Category Endpoints ---
@router.post(
    "/categories", 
    response_model=CategoryResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))]
)
async def create_new_category(category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Admin/Manager-only: Create a new product category."""
    return await product_service.create_category(db, category_in)


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Public: Get list of all categories."""
    return await product_service.get_categories(db)


# --- Product Endpoints ---
@router.post(
    "/", 
    response_model=ProductResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))]
)
async def create_new_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Admin/Manager-only: Create a new product."""
    category = await product_service.get_category_by_id(db, product_in.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Specified category ID does not exist."
        )
    return await product_service.create_product(db, product_in)


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Public: Retrieve products with pagination, category filter, and search."""
    return await product_service.get_products(
        db, skip=skip, limit=limit, category_id=category_id, search=search
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_details(product_id: int, db: AsyncSession = Depends(get_db)):
    """Public: Get detailed product information by ID."""
    product = await product_service.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )
    return product


@router.put(
    "/{product_id}", 
    response_model=ProductResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))]
)
async def update_existing_product(
    product_id: int, 
    product_in: ProductUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Admin/Manager-only: Update product information."""
    db_product = await product_service.get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found"
        )
    return await product_service.update_product(db, db_product, product_in)