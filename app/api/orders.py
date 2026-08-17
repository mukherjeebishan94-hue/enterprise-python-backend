from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User, UserRole
from app.api.deps import get_current_user, RoleChecker
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services import order_service
from app.services.email_service import send_order_confirmation_email

router = APIRouter(prefix="/orders", tags=["Orders & Checkout"])


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def checkout_cart(
    order_in: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated user: Process cart checkout, create order, deduct stock,
    and trigger background order receipt email.
    """
    order = await order_service.create_order(db, current_user.id, order_in)
    
    # Trigger non-blocking background email notification
    background_tasks.add_task(
        send_order_confirmation_email, 
        user_email=current_user.email, 
        order=order
    )

    return order


@router.get("/me", response_model=List[OrderResponse])
async def list_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Authenticated user: Fetch personal order history."""
    return await order_service.get_user_orders(db, current_user.id)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve order details by ID."""
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    
    if current_user.role == UserRole.CUSTOMER and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this order."
        )

    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))],
)
async def update_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Admin/Manager-only: Update order status."""
    return await order_service.update_order_status(db, order_id, status_in)