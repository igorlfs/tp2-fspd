import sys
from concurrent import futures
from typing import TypedDict

import grpc

import order_pb2
import order_pb2_grpc
import stock_pb2
import stock_pb2_grpc
from order_shared import Item, ItemWithStatus

stock_stub = None


class OrderId(TypedDict):
    id: int


class RequestItems(TypedDict):
    items: list[Item]


class Items(TypedDict):
    id: int
    active: bool
    items: list[ItemWithStatus]


orders: list[Items] = []


class Order(order_pb2_grpc.OrderServicer):
    def create_order(self, request: RequestItems, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        result = []

        items = [
            ItemWithStatus(prod_id=item.prod_id, quantity=item.quantity, status=0)
            for item in request.items
        ]

        for item in items:
            response = stock_stub.update_product_quantity(
                stock_pb2.UpdateProductParams(id=item.prod_id, value=-item.quantity)
            )
            status = (response.status < 0 and response.status) or 0
            item.status = status
            result.append({"prod_id": item.prod_id, "status": status})

        orders.append(Items(id=len(orders) + 1, items=items, active=True))

        return order_pb2.CreateOrderResponse(result=result)

    def cancel_order(self, request: OrderId, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        order: Items | None = next((filter(lambda x: request.id == x["id"], orders)), None)

        if order is None:
            return order_pb2.CancelOrderResponse(status=-1)

        order["active"] = False

        successfully_ordered = [item for item in order["items"] if item.status == 0]

        for item in successfully_ordered:
            stock_stub.update_product_quantity(
                stock_pb2.UpdateProductParams(id=item.prod_id, value=item.quantity)
            )

        return order_pb2.CancelOrderResponse(status=0)

    def kill_server(self, _request, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        response = stock_stub.kill_server(stock_pb2.KillServerParams())

        active_orders = len(list(filter(lambda x: x["active"], orders)))

        return order_pb2.KillServerResponse(
            num_products=response.quantity, num_orders=active_orders
        )
        # TODO kill server


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
