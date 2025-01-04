import sys

import grpc

import stock_pb2
import stock_pb2_grpc

if __name__ == "__main__":
    # Primeiro, é preciso abrir um canal para o servidor
    # TODO talvez precise ser um canal seguro ou algo assim
    channel = grpc.insecure_channel(sys.argv[1])
    # E criar o stub, que vai ser o objeto com referências para os procedimentos remotos
    # (código gerado pelo compilador)
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
                response = stub.list_products(stock_pb2.ListProductsParams())

                for product in response.products:
                    print(f"{product.id} {product.description} {product.quantity}")

            elif command[0] == "F":
                response = stub.kill_server(stock_pb2.KillServerParams())

                print(response.quantity)
                break

        except EOFError:
            break

    # Ao final o cliente pode fechar o canal para o servidor.
    channel.close()
