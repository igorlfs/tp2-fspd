from dataclasses import dataclass

import stock_pb2
from stock_pb2_grpc import StockStub


@dataclass
class UpdateProduct:
    id: int
    value: int


@dataclass
class Product:
    id: int
    quantity: int
    description: str


def list_products(stub: StockStub) -> None:
    response = stub.list_products(stock_pb2.ListProductsParams())

    for product in response.products:
        print(f"{product.id} {product.quantity} {product.description}")
