from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from database import get_connection, return_connection, init_db

app = Flask(__name__)
app.secret_key = 'Tu_llave_secreta'

# Inicializar BD
init_db()

@app.route('/')
def index():
    return redirect(url_for('ver_inventario'))

@app.route('/inventario')
def ver_inventario():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.codigo_barras, p.nombre, 
                   COALESCE(SUM(CASE WHEN i.ubicacion = 'almacen' THEN i.cantidad ELSE 0 END), 0) as almacen,
                   COALESCE(SUM(CASE WHEN i.ubicacion = 'local' THEN i.cantidad ELSE 0 END), 0) as local
            FROM producto p
            LEFT JOIN inventario i ON p.id = i.producto_id
            GROUP BY p.codigo_barras, p.nombre
            ORDER BY p.nombre
        """)
        inventario = cursor.fetchall()
        return render_template('inventario.html', inventario=inventario)
    finally:
        cursor.close()
        return_connection(conn)

@app.route('/mover', methods=['GET', 'POST'])
def mover_producto():
    if request.method == 'POST':
        # Lógica de movimiento (similar a la anterior)
        # ... (ver versión anterior completa)
        return redirect(url_for('ver_inventario'))
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT codigo_barras, nombre FROM producto")
        productos = cursor.fetchall()
        return render_template('mover_producto.html', productos=productos)
    finally:
        cursor.close()
        return_connection(conn)

@app.route('/cargar-excel', methods=['GET', 'POST'])
def cargar_excel():
    if request.method == 'POST':
        if 'archivo' not in request.files:
            flash('No se seleccionó archivo', 'error')
            return redirect(request.url)
        
        archivo = request.files['archivo']
        if not archivo.filename.endswith('.xlsx'):
            flash('Formato no válido. Use .xlsx', 'error')
            return redirect(request.url)
        
        try:
            df = pd.read_excel(archivo)
            df = df.rename(columns={
                "Código": "codigo_barras",
                "Producto": "nombre",
                "P. Costo": "precio_costo",
                "P. Venta": "precio_venta",
                "Existencia": "cantidad",
                "Departamento": "departamento"
            })
            
            df['precio_costo'] = df['precio_costo'].str.replace('$', '').astype(float)
            df['precio_venta'] = df['precio_venta'].str.replace('$', '').astype(float)
            
            conn = get_connection()
            cursor = conn.cursor()
            
            for _, fila in df.iterrows():
                # Actualizar producto
                cursor.execute("""
                    INSERT INTO producto (codigo_barras, nombre, departamento, precio_costo, precio_venta)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (codigo_barras) DO UPDATE SET
                        nombre = EXCLUDED.nombre,
                        departamento = EXCLUDED.departamento,
                        precio_costo = EXCLUDED.precio_costo,
                        precio_venta = EXCLUDED.precio_venta
                    RETURNING id
                """, (
                    str(fila['codigo_barras']),
                    fila['nombre'],
                    fila['departamento'],
                    fila['precio_costo'],
                    fila['precio_venta']
                ))
                producto_id = cursor.fetchone()[0]
                
                # Actualizar inventario local
                cursor.execute("""
                    INSERT INTO inventario (producto_id, ubicacion, cantidad)
                    VALUES (%s, 'local', %s)
                    ON CONFLICT (producto_id, ubicacion) DO UPDATE SET
                        cantidad = EXCLUDED.cantidad
                """, (producto_id, fila['cantidad']))
            
            conn.commit()
            flash('¡Inventario actualizado correctamente!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            cursor.close()
            return_connection(conn)
        
        return redirect(url_for('cargar_excel'))
    
    return render_template('cargar_excel.html')

if __name__ == '__main__':
    app.run(debug=True)