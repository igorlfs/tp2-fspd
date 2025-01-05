import sys
from concurrent import futures
from threading import Event

import grpc

import stock_pb2
import stock_pb2_grpc
from stock_shared import Product, UpdateProduct
from util import is_valid_port

stock: list[Product] = []


class Stock(stock_pb2_grpc.StockServicer):
    def __init__(self, stop_event: Event) -> None:
        self._stop_event = stop_event

    def add_product(self, request: Product, _context):  # noqa: ANN001, ANN201
        product: Product | None = next(
            filter(lambda x: request.description == x.description, stock), None
        )

        prod_id = (product is None and len(stock) + 1) or stock[stock.index(product)].id

        if product is None:
            stock.append(Product(prod_id, request.quantity, request.description))
        else:
            product.quantity += 1

        return stock_pb2.NewProductResponse(id=prod_id)

    def update_product_quantity(self, request: UpdateProduct, _context):  # noqa: ANN001, ANN201
        if request.id > len(stock) or request.id <= 0:
            return stock_pb2.UpdateProductResponse(status=-2)

        product = stock[request.id - 1]

        if product.quantity + request.value < 0:
            return stock_pb2.UpdateProductResponse(status=-1)
        else:  # noqa: RET505
            product.quantity += request.value
            return stock_pb2.UpdateProductResponse(status=product.quantity)

    def list_products(self, _request, _context):  # noqa: ANN001, ANN201
        products = [
            {"id": product.id, "quantity": product.quantity, "description": product.description}
            for product in stock
        ]

        return stock_pb2.ListProductsResponse(products=products)

    def kill_server(self, _request, _context):  # noqa: ANN001, ANN201
        self._stop_event.set()
        return stock_pb2.KillServerResponse(quantity=len(stock))


if __name__ == "__main__":
    port = int(sys.argv[1])
    is_valid_port(port)

    # O servidor usa um modelo de pool de threads do pacote concurrent
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # O servidor precisa ser ligado ao objeto que identifica os procedimentos a serem executados.
    stop_event = Event()
    stock_pb2_grpc.add_StockServicer_to_server(Stock(stop_event), server)

    # TODO creio que precise alterar o IP
    server.add_insecure_port(f"localhost:{port}")

    server.start()

    stop_event.wait()
    server.stop(1)
