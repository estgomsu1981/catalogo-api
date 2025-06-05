from pydantic import BaseModel

class Producto(BaseModel):
    id: int | None = None
    nombre: str
    cantidad: int