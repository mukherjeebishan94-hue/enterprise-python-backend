from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from app.models.order import OrderStatus


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    unit_price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    items: List[CartItemCreate] = Field(..., min_items=1)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus