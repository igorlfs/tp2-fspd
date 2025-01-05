import sys

import grpc

import order_pb2
import order_pb2_grpc
import stock_pb2_grpc
from stock_shared import list_products

if __name__ == "__main__":
    # Primeiro, é preciso abrir um canal para o servidor
    # TODO talvez precise ser um canal seguro ou algo assim
    stock_channel = grpc.insecure_channel(sys.argv[1])
    order_channel = grpc.insecure_channel(sys.argv[2])
    # E criar o stub, que vai ser o objeto com referências para os procedimentos remotos
    # (código gerado pelo compilador)
    stock_stub = stock_pb2_grpc.StockStub(stock_channel)
    order_stub = order_pb2_grpc.OrderStub(order_channel)

    list_products(stock_stub)

    while True:
        try:
            command = input()
            # Não tem match nas máquinas do DCC >:(
            if command[0] == "P":
                split_items = command.split(" ")[1:]
                products = [x for i, x in enumerate(split_items) if i % 2 == 0]
                quantities = [x for i, x in enumerate(split_items) if i % 2 == 1]
                items = [
                    {"prod_id": int(p), "quantity": int(q)}
                    for p, q in zip(products, quantities, strict=True)
                ]

                response = order_stub.create_order(order_pb2.CreateOrderParams(items=items))

                for item in response.result:
                    print(f"{item.prod_id} {item.status}")

            elif command[0] == "X":
                _, order_id = command.split(" ")
                response = order_stub.cancel_order(order_pb2.CancelOrderParams(id=int(order_id)))
                print(response.status)

            elif command[0] == "T":
                response = order_stub.kill_server(order_pb2.KillServerParams())
                print(f"{response.num_products} {response.num_orders}")
                break

        except EOFError:
            break

    # Ao final o cliente pode fechar o canal para o servidor.
    stock_channel.close()
