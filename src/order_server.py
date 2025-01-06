import sys
from concurrent import futures
from threading import Event
from typing import TypedDict

import grpc

import order_pb2
import order_pb2_grpc
import stock_pb2
import stock_pb2_grpc
from util import is_valid_port

stock_stub = None


class Item(TypedDict):
    prod_id: int
    quantity: int


class ItemWithStatus(Item):
    status: int


class OrderId(TypedDict):
    id: int


class RequestItems(TypedDict):
    items: list


class Items(TypedDict):
    id: int
    active: bool
    items: list


orders = []


class Order(order_pb2_grpc.OrderServicer):
    def __init__(self, stop_event: Event) -> None:
        self._stop_event = stop_event

    def create_order(self, request: RequestItems, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        result = []

        items = [
            ItemWithStatus(prod_id=item.prod_id, quantity=item.quantity, status=0)
            for item in request.items
        ]

        for item in items:
            response = stock_stub.update_product_quantity(
                stock_pb2.UpdateProductParams(id=item["prod_id"], value=-item["quantity"])
            )
            status = (response.status < 0 and response.status) or 0
            item["status"] = status
            result.append({"prod_id": item["prod_id"], "status": status})

        orders.append(Items(id=len(orders) + 1, items=items, active=True))

        return order_pb2.CreateOrderResponse(result=result)

    def cancel_order(self, request: OrderId, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        order: Items | None = next((filter(lambda x: request.id == x["id"], orders)), None)

        if order is None:
            return order_pb2.CancelOrderResponse(status=-1)

        order["active"] = False

        successfully_ordered = [item for item in order["items"] if item["status"] == 0]

        for item in successfully_ordered:
            stock_stub.update_product_quantity(
                stock_pb2.UpdateProductParams(id=item["prod_id"], value=item["quantity"])
            )

        return order_pb2.CancelOrderResponse(status=0)

    def kill_server(self, _request, _context):  # noqa: ANN001, ANN201
        assert stock_stub is not None

        response = stock_stub.kill_server(stock_pb2.KillServerParams())

        active_orders = len(list(filter(lambda x: x["active"], orders)))

        self._stop_event.set()

        return order_pb2.KillServerResponse(
            num_products=response.quantity, num_orders=active_orders
        )


if __name__ == "__main__":
    port = int(sys.argv[1])
    is_valid_port(port)

    channel = grpc.insecure_channel(sys.argv[2])

    stock_stub = stock_pb2_grpc.StockStub(channel)

    # O servidor usa um modelo de pool de threads do pacote concurrent
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # O servidor precisa ser ligado ao objeto que identifica os procedimentos a serem executados.
    stop_event = Event()
    order_pb2_grpc.add_OrderServicer_to_server(Order(stop_event), server)

    server.add_insecure_port(f"0.0.0.0:{port}")

    server.start()

    stop_event.wait()
    server.stop(1)
