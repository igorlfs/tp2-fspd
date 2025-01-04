from dataclasses import dataclass


@dataclass
class UpdateProduct:
    id: int
    value: int


@dataclass
class Product:
    id: int
    quantity: int
    description: str
