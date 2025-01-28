SRC_DIR = src
PROTO_DIR = proto

PROTOC_COMMAND = python3 -m grpc_tools.protoc
PROTOC_FLAGS = --python_out=$(SRC_DIR) --grpc_python_out=$(SRC_DIR)

GRPC_FILES = $(wildcard $(SRC_DIR)/*_pb2*.py)

PROTOBUF_STOCK = $(PROTO_DIR)/stock/v1/stock.proto
PROTOBUF_ORDER = $(PROTO_DIR)/order/v1/order.proto

GRPC_STOCK = $(SRC_DIR)/stock_pb2.py
GRPC_ORDER = $(SRC_DIR)/order_pb2.py

clean:
	find $(SRC_DIR) -name "*_pb2*.py" -delete

stubs: $(GRPC_STOCK) $(GRPC_ORDER)

$(GRPC_STOCK): $(PROTOBUF_STOCK)
	$(PROTOC_COMMAND) -I$(PROTO_DIR)/stock/v1 $(PROTOC_FLAGS) $(PROTOBUF_STOCK)

$(GRPC_ORDER): $(PROTOBUF_ORDER)
	$(PROTOC_COMMAND) -I$(PROTO_DIR)/order/v1 $(PROTOC_FLAGS) $(PROTOBUF_ORDER)

run_serv_estoque: stubs
	python3 $(SRC_DIR)/stock_server.py $(arg1)

run_cli_estoque: stubs
	python3 $(SRC_DIR)/stock_client.py $(arg1)

run_serv_pedidos: stubs
	python3 $(SRC_DIR)/order_server.py $(arg1) $(arg2)

run_cli_pedidos: stubs
	python3 $(SRC_DIR)/order_client.py $(arg1) $(arg2)

.PHONY: all clean stubs run_serv_estoque run_cli_estoque run_serv_pedidos run_cli_pedidos
