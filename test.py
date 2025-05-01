import psycopg2

try:
    conn = psycopg2.connect(
        dbname="inventarios_db",
        user="postgres",
        password="PanchoLaika4445.@",
        host="localhost",
        port="5423"
    )
    print("¡Conexión exitosa!")
except Exception as e:
    print(f"Error: {e}")