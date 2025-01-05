import sys
from concurrent import futures
from typing import TypedDict

import grpc

import order_pb2
import order_pb2_grpc
import stock_pb2
import stock_pb2_grpc
from order_shared import Item

stock_stub = None


class Items(TypedDict):
    id: int
    active: bool
    items: list[Item]


orders: list[Items] = []


class Order(order_pb2_grpc.OrderServicer):
    def create_order(self, request: Items, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        orders.append(Items(id=len(orders) + 1, items=request.items, active=True))

        result = []

        for item in request.items:
            response = stock_stub.update_product_quantity(
                stock_pb2.UpdateProductParams(id=item.prod_id, value=-item.quantity)
            )
            status = (response.status < 0 and response.status) or 0
            result.append({"prod_id": item.prod_id, "status": status})

        return order_pb2.CreateOrderResponse(result=result)

    def kill_server(self, _request, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        response = stock_stub.kill_server(stock_pb2.KillServerParams())

        active_orders = len(list(filter(lambda x: x.active, orders)))

        return order_pb2.KillServerResponse(
            num_products=response.quantity, num_orders=active_orders
        )


MIN_PORT = 2048
MAX_PORT = 65535

if __name__ == "__main__":
    port = int(sys.argv[1])
    assert port >= MIN_PORT and port <= MAX_PORT, f"Port must be between {MIN_PORT} and {MAX_PORT}"

    channel = grpc.insecure_channel(sys.argv[2])

    stock_stub = stock_pb2_grpc.StockStub(channel)

    # O servidor usa um modelo de pool de threads do pacote concurrent
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # O servidor precisa ser ligado ao objeto que identifica os procedimentos a serem executados.
    order_pb2_grpc.add_OrderServicer_to_server(Order(), server)

    # O método add_insecure_port permite a conexão direta por TCP
    #   Outros recursos estão disponíveis, como uso de um registry
    #   (dicionário de serviços), criptografia e autenticação.

    # TODO creio que precise alterar o IP
    server.add_insecure_port(f"localhost:{port}")

    # O servidor é iniciado e esse código não tem nada para fazer a não ser esperar pelo término da execução.
    server.start()
    server.wait_for_termination()
