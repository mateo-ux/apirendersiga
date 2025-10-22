# app.py (antes api.py)
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db_connection():
    """Conectar a la base de datos PostgreSQL"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    return conn

@app.route('/')
def home():
    return jsonify({
        "status": "API para consulta de aspirantes",
        "version": "1.0",
        "endpoints": {
            "consultar_documento": "/consultar-documento (POST)",
            "consultar_multiples": "/consultar-multiples (POST)"
        }
    })

@app.route('/consultar-documento', methods=['POST'])
def consultar_documento():
    """Consultar un documento individual"""
    try:
        data = request.get_json()
        documento = data.get('documento')
        
        if not documento:
            return jsonify({"error": "Documento requerido"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT documento_numero, inscripcion_aprobada 
            FROM aspirantes 
            WHERE documento_numero = %s
        """, (documento,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
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
    """Consultar múltiples documentos en lote"""
    try:
        data = request.get_json()
        documentos = data.get('documentos', [])
        
        if not documentos:
            return jsonify({"error": "Lista de documentos requerida"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
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

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return jsonify({"status": "healthy", "message": "API funcionando correctamente"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)