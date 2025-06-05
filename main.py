from fastapi import FastAPI, HTTPException
from database import get_connection
from models import Producto
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token, get_current_user, verify_password, fake_user
from fastapi import FastAPI, Depends, HTTPException
from auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o pon ["http://localhost:3000"] si querés más seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"status": "Conexión exitosa a la base de datos"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/productos")
def  get_productos(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, cantidad FROM productos")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "nombre": r[1], "cantidad": r[2]} for r in rows]

@app.post("/productos")
def create_producto(producto: Producto,current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO productos (nombre, cantidad) VALUES (%s, %s) RETURNING id",
                (producto.nombre, producto.cantidad))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "nombre": producto.nombre, "cantidad": producto.cantidad}

@app.put("/productos/{id}")
def update_producto(id: int, producto: Producto,current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE productos SET nombre=%s, cantidad=%s WHERE id=%s",
                (producto.nombre, producto.cantidad, id))
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    conn.commit()
    cur.close()
    conn.close()
    return {"id": id, "nombre": producto.nombre, "cantidad": producto.cantidad}

@app.delete("/productos/{id}")
def delete_producto(id: int,current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM productos WHERE id=%s", (id,))
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": f"Producto {id} eliminado"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != fake_user["username"]:
        raise HTTPException(status_code=400, detail="Usuario incorrecto")
    if not verify_password(form_data.password, fake_user["password"]):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    
    token = create_access_token(data={"sub": fake_user["username"]})
    return {"access_token": token, "token_type": "bearer"}