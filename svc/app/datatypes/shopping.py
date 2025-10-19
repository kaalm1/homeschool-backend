from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.common import TimestampMixin
from svc.app.datatypes.enums import ItemStatus, ShoppingCategory


class ShoppingBase(BaseModel):
    """Base shopping schema"""

    item_name: str = Field(..., min_length=1, max_length=255, description="Item name")
    quantity: Optional[str] = Field(None, description="Quantity needed")
    category: Optional[ShoppingCategory] = Field(None, description="Item category")
    notes: Optional[str] = Field(None, description="Additional notes")
    estimated_price: Optional[float] = Field(None, ge=0, description="Estimated price")
    store_name: Optional[str] = Field(None, max_length=200, description="Store name")
    priority: Optional[int] = Field(0, ge=0, le=10, description="Priority (0-10)")


class ShoppingCreate(ShoppingBase):
    """Schema for creating shopping items"""

    pass


class ShoppingUpdate(BaseModel):
    """Schema for updating shopping items"""

    item_name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[str] = None
    category: Optional[ShoppingCategory] = None
    notes: Optional[str] = None
    estimated_price: Optional[float] = Field(None, ge=0)
    actual_price: Optional[float] = Field(None, ge=0)
    store_name: Optional[str] = Field(None, max_length=200)
    priority: Optional[int] = Field(None, ge=0, le=10)
    status: Optional[ItemStatus] = None


class ShoppingResponse(ShoppingBase, TimestampMixin):
    """Schema for shopping responses"""

    id: int = Field(..., description="Shopping item ID")
    status: ItemStatus = Field(..., description="Item status")
    actual_price: Optional[float] = Field(None, description="Actual price paid")
    price_verified: Optional[bool] = Field(None, description="Price verified")
    purchased_at: Optional[datetime] = Field(None, description="Purchase timestamp")

    class Config:
        from_attributes = True


class ParsedShopping(BaseModel):
    """Parsed shopping item from AI"""

    item_name: str
    quantity: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    estimated_price: Optional[str] = None
    store_name: Optional[str] = None
    priority: Optional[int] = 0


class ShoppingSummary(BaseModel):
    """Summary statistics for shopping"""

    total: int = Field(..., description="Total items")
    pending: int = Field(..., description="Pending items")
    purchased: int = Field(..., description="Purchased items")
    total_estimated_cost: float = Field(..., description="Total estimated cost")
    total_actual_cost: float = Field(..., description="Total actual cost")
