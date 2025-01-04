import sys
from concurrent import futures

import grpc

import stock_pb2
import stock_pb2_grpc
from stock_shared import Product, UpdateProduct

stock: list[Product] = []


class Stock(stock_pb2_grpc.StockServicer):
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
        return stock_pb2.KillServerResponse(quantity=len(stock))
        # TODO kill server


MIN_PORT = 2048
MAX_PORT = 65535

if __name__ == "__main__":
    port = int(sys.argv[1])
    assert port >= MIN_PORT and port <= MAX_PORT, f"Port must be between {MIN_PORT} and {MAX_PORT}"

    # O servidor usa um modelo de pool de threads do pacote concurrent
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # O servidor precisa ser ligado ao objeto que identifica os procedimentos a serem executados.
    stock_pb2_grpc.add_StockServicer_to_server(Stock(), server)

    # O método add_insecure_port permite a conexão direta por TCP
    #   Outros recursos estão disponíveis, como uso de um registry
    #   (dicionário de serviços), criptografia e autenticação.

    # TODO creio que precise alterar o IP
    server.add_insecure_port(f"localhost:{port}")

    # O servidor é iniciado e esse código não tem nada para fazer a não ser esperar pelo término da execução.
    server.start()
    server.wait_for_termination()
