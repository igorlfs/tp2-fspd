from dataclasses import dataclass


@dataclass
class Item:
    prod_id: int
    quantity: int


@dataclass
class ItemWithStatus(Item):
    status: int
