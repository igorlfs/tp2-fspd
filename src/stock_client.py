import sys

import grpc

import stock_pb2
import stock_pb2_grpc
from shared import list_products

if __name__ == "__main__":
    channel = grpc.insecure_channel(sys.argv[1])

    stub = stock_pb2_grpc.StockStub(channel)

    while True:
        try:
            command = input()
            # Não tem match nas máquinas do DCC >:(
            if command[0] == "P":
                quantity = command.split(" ")[1]
                description = " ".join(str(x) for x in command.split(" ")[2:])

                response = stub.add_product(
                    stock_pb2.NewProductParams(description=description, quantity=int(quantity))
                )

                print(response.id)

            elif command[0] == "Q":
                _, prod_id, value = command.split(" ")

                response = stub.update_product_quantity(
                    stock_pb2.UpdateProductParams(id=int(prod_id), value=int(value))
                )

                print(response.status)

            elif command[0] == "L":
                list_products(stub)

            elif command[0] == "F":
                response = stub.kill_server(stock_pb2.KillServerParams())

                print(response.quantity)

                break

        except EOFError:
            break

    channel.close()
