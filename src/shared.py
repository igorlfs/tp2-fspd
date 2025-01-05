import stock_pb2
from stock_pb2_grpc import StockStub


def list_products(stub: StockStub) -> None:
    response = stub.list_products(stock_pb2.ListProductsParams())

    for product in response.products:
        print(f"{product.id} {product.quantity} {product.description}")
