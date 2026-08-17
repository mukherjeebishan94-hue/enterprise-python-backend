from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.services.product_service import invalidate_product_cache


async def create_order(
    db: AsyncSession, user_id: int, order_in: OrderCreate
) -> Order:
    """
    Creates an order inside an atomic database transaction:
    1. Validates product availability & stock levels.
    2. Deducts product stock.
    3. Calculates total amount.
    4. Creates Order and OrderItem records.
    5. Invalidates product cache in Redis.
    """
    total_amount = 0.0
    order_items = []

    # 1. Fetch and validate all products in a single pass
    for item in order_in.items:
        result = await db.execute(select(Product).filter(Product.id == item.product_id))
        product = result.scalars().first()

        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ID {item.product_id} is unavailable or does not exist."
            )

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. Requested: {item.quantity}, Available: {product.stock_quantity}"
            )

        # Calculate pricing
        item_total = float(product.price) * item.quantity
        total_amount += item_total

        # Deduct product stock
        product.stock_quantity -= item.quantity
        db.add(product)

        # Prepare order item
        order_items.append(
            OrderItem(
                product_id=product.id,
                unit_price=product.price,
                quantity=item.quantity
            )
        )

    # 2. Save Order and OrderItems to DB
    new_order = Order(
        user_id=user_id,
        total_amount=round(total_amount, 2),
        status=OrderStatus.PENDING,
        items=order_items
    )
    db.add(new_order)
    
    await db.commit()
    await db.refresh(new_order)

    # 3. Invalidate Redis cache for updated products
    await invalidate_product_cache()

    # Re-fetch order with eager-loaded items for response schema
    return await get_order_by_id(db, new_order.id)


async def get_user_orders(db: AsyncSession, user_id: int) -> List[Order]:
    """Retrieve all orders for a specific user."""
    query = select(Order).options(selectinload(Order.items)).filter(Order.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    """Retrieve an order by ID with line items eager loaded."""
    query = select(Order).options(selectinload(Order.items)).filter(Order.id == order_id)
    result = await db.execute(query)
    return result.scalars().first()


async def update_order_status(
    db: AsyncSession, order_id: int, status_in: OrderStatusUpdate
) -> Order:
    """Admin/Manager-only: Update order status."""
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order.status = status_in.status
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order