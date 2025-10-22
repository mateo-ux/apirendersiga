from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)  # Esto permite que Apps Script se comunique con tu API

def get_db_connection():
    """Conectar a la base de datos PostgreSQL de Render"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),           # dpg-xxx.render.com
        database=os.getenv('DB_NAME'),       # tu_base_de_datos
        user=os.getenv('DB_USER'),           # tu_usuario
        password=os.getenv('DB_PASSWORD'),   # tu_contraseña
        port=os.getenv('DB_PORT', 5432)
    )
    return conn

@app.route('/consultar-documento', methods=['POST'])
def consultar_documento():
    """Consulta UN solo documento en la base de datos"""
    try:
        # Obtener el documento del request
        data = request.get_json()
        documento = data.get('documento')
        
        if not documento:
            return jsonify({"error": "Documento requerido"}), 400
        
        # Conectar a la BD
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Ejecutar consulta SQL
        cur.execute("""
            SELECT documento_numero, inscripcion_aprobada 
            FROM aspirantes 
            WHERE documento_numero = %s
        """, (documento,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        # Preparar respuesta
        if resultado:
            return jsonify({
                "encontrado": True,
                "documento": resultado['documento_numero'],
                "inscripcion_aprobada": resultado['inscripcion_aprobada']
            })
        else:
            return jsonify({
                "encontrado": False,
                "documento": documento,
                "inscripcion_aprobada": None
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/consultar-multiples', methods=['POST'])
def consultar_multiples():
    """Consulta MÚLTIPLES documentos en una sola consulta (más eficiente)"""
    try:
        data = request.get_json()
        documentos = data.get('documentos', [])
        
        if not documentos:
            return jsonify({"error": "Lista de documentos requerida"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Crear consulta SQL dinámica con múltiples placeholders
        placeholders = ','.join(['%s'] * len(documentos))
        query = f"""
            SELECT documento_numero, inscripcion_aprobada 
            FROM aspirantes 
            WHERE documento_numero IN ({placeholders})
        """
        
        cur.execute(query, documentos)
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convertir resultados a diccionario para fácil acceso
        resultados_dict = {
            str(row['documento_numero']): row['inscripcion_aprobada'] 
            for row in resultados
        }
        
        return jsonify({
            "total_encontrados": len(resultados),
            "resultados": resultados_dict
        })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)