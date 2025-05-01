import psycopg2
from psycopg2 import pool

# Configuración (ajusta según tu entorno)
DB_CONFIG = {
    "dbname": "inventarios_db",
    "user": "postgres",
    "password": "PanchoLaika4445.@",
    "host": "localhost",
    "port": "5423"  # ¡Cambiado aquí!
}

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_CONFIG
)

def get_connection():
    return connection_pool.getconn()

def return_connection(conn):
    connection_pool.putconn(conn)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS producto (
                id SERIAL PRIMARY KEY,
                codigo_barras VARCHAR(20) UNIQUE,
                nombre VARCHAR(100),
                departamento VARCHAR(100),
                precio_costo DECIMAL(10,2),
                precio_venta DECIMAL(10,2)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER REFERENCES producto(id),
                ubicacion VARCHAR(50) CHECK (ubicacion IN ('local', 'almacen')),
                cantidad DECIMAL(10,2),
                UNIQUE(producto_id, ubicacion)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimiento (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER REFERENCES producto(id),
                cantidad DECIMAL(10,2),
                origen VARCHAR(50),
                destino VARCHAR(50),
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        return_connection(conn)