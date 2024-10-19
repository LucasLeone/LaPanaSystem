from .sales import (
    SaleSerializer,
    SaleDetailSerializer,
    StateChangeSerializer,
    PartialChargeSerializer,
    FastSaleSerializer
)
from .returns import ReturnSerializer, ReturnDetailSerializer

__all__ = [
    "SaleSerializer",
    "SaleDetailSerializer",
    "StateChangeSerializer",
    "ReturnSerializer",
    "ReturnDetailSerializer",
    "PartialChargeSerializer",
    "FastSaleSerializer"
]
