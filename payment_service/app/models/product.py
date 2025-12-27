"""
Product Model - Quản lý sản phẩm trong máy bán hàng
"""
from typing import List, Optional
from pydantic import BaseModel


class Product(BaseModel):
    """Model sản phẩm"""
    id: int
    name: str
    price: int  # Giá tính bằng VND
    stock: int
    image_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_available: bool = True


class ProductResponse(BaseModel):
    """Response model cho API products"""
    success: bool
    data: List[Product]
    message: Optional[str] = None


# Dữ liệu sản phẩm mẫu
SAMPLE_PRODUCTS = [
    Product(
        id=1,
        name="Coca Cola",
        price=15000,
        stock=10,
        image_url="/images/coca-cola.jpg",
        description="Nước ngọt Coca Cola 330ml",
        category="Nước ngọt",
        is_available=True
    ),
    Product(
        id=2,
        name="Pepsi",
        price=15000,
        stock=8,
        image_url="/images/pepsi.jpg",
        description="Nước ngọt Pepsi 330ml",
        category="Nước ngọt",
        is_available=True
    ),
    Product(
        id=3,
        name="Sprite",
        price=12000,
        stock=5,
        image_url="/images/sprite.jpg",
        description="Nước ngọt Sprite 330ml",
        category="Nước ngọt",
        is_available=True
    ),
    Product(
        id=4,
        name="Fanta",
        price=12000,
        stock=7,
        image_url="/images/fanta.jpg",
        description="Nước ngọt Fanta 330ml",
        category="Nước ngọt",
        is_available=True
    ),
    Product(
        id=5,
        name="Aquafina",
        price=8000,
        stock=15,
        image_url="/images/aquafina.jpg",
        description="Nước suối Aquafina 500ml",
        category="Nước suối",
        is_available=True
    ),
    Product(
        id=6,
        name="Lavie",
        price=8000,
        stock=12,
        image_url="/images/lavie.jpg",
        description="Nước suối Lavie 500ml",
        category="Nước suối",
        is_available=True
    ),
    Product(
        id=7,
        name="Snack Oishi",
        price=10000,
        stock=6,
        image_url="/images/oishi.jpg",
        description="Snack khoai tây Oishi",
        category="Snack",
        is_available=True
    ),
    Product(
        id=8,
        name="Bánh Oreo",
        price=18000,
        stock=4,
        image_url="/images/oreo.jpg",
        description="Bánh quy Oreo",
        category="Bánh kẹo",
        is_available=True
    )
]


def get_all_products() -> List[Product]:
    """Lấy tất cả sản phẩm"""
    return [p for p in SAMPLE_PRODUCTS if p.is_available]


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Lấy sản phẩm theo ID"""
    for product in SAMPLE_PRODUCTS:
        if product.id == product_id and product.is_available:
            return product
    return None


def update_product_stock(product_id: int, new_stock: int) -> bool:
    """Cập nhật stock sản phẩm"""
    for product in SAMPLE_PRODUCTS:
        if product.id == product_id:
            product.stock = new_stock
            return True
    return False


def decrease_product_stock(product_id: int, quantity: int = 1) -> bool:
    """Giảm stock sản phẩm khi bán"""
    product = get_product_by_id(product_id)
    if product and product.stock >= quantity:
        product.stock -= quantity
        return True
    return False