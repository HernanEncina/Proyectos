from flask import Flask, request, jsonify, session, g, send_file, render_template  # AÑADÍ render_template
import sqlite3
from datetime import datetime
import hashlib
import os
import uuid
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import threading
import time

# Configuración
app = Flask(__name__)
app.secret_key = 'Sistema-secret-key-2025'

DATABASE = '/home/hernansote/dbs/sys-donaciones/sys-donaciones'
UPLOAD_FOLDER = '/home/hernansote/dbs/sys-donaciones/certificados'
TEMPLATES_FOLDER = '/home/hernansote/dbs/sys-donaciones/plantillas'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ============================================
# FUNCIÓN GENERADORA DE CERTIFICADOS (MEJORADA)
# ============================================

def generar_imagen_certificado(datos_certificado, output_path=None):
    """
    Genera un certificado y retorna los bytes de la imagen o la guarda en output_path
    datos_certificado: {
        'nombre_titular': 'Juan Pérez',
        'nombre_beneficiario': 'María García',
        'email': 'juan@email.com',
        'mensaje': 'Gracias por tu apoyo...',
        'certificado_nombre': 'Certificado por damnificados',
        'cantidad': 2,
        'monto': 5000,
        'fecha': '15 de enero, 2024',
        'folio': 'DON-2024-0001',
        'plantilla': 'plantilla_default.jpg'
    }
    """
    try:
        # Determinar qué plantilla usar
        plantilla = datos_certificado.get('plantilla', 'plantilla_default.jpg')
        plantilla_path = os.path.join(TEMPLATES_FOLDER, plantilla)
        
        # Si no existe la plantilla específica, usar default
        if not os.path.exists(plantilla_path):
            plantilla_path = os.path.join(TEMPLATES_FOLDER, 'plantilla_default.jpg')
            if not os.path.exists(plantilla_path):
                # Si no hay plantilla, crear imagen blanca
                img = Image.new('RGB', (1200, 1600), color='white')
                draw = ImageDraw.Draw(img)
                # Marco
                draw.rectangle([(50, 50), (1150, 1550)], outline='#2c3e50', width=5)
            else:
                img = Image.open(plantilla_path)
                draw = ImageDraw.Draw(img)
        else:
            img = Image.open(plantilla_path)
            draw = ImageDraw.Draw(img)
        
        # Cargar fuentes
        try:
            font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            font_nombre = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_texto = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            font_mensaje = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Italic.ttf", 35)
            font_folio = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font_titulo = ImageFont.load_default()
            font_nombre = ImageFont.load_default()
            font_texto = ImageFont.load_default()
            font_mensaje = ImageFont.load_default()
            font_folio = ImageFont.load_default()
        
        # Título
        titulo = "CERTIFICADO DE DONACIÓN"
        bbox = draw.textbbox((0, 0), titulo, font=font_titulo)
        titulo_ancho = bbox[2] - bbox[0]
        titulo_x = (img.width - titulo_ancho) // 2
        draw.text((titulo_x, 150), titulo, fill='#2c3e50', font=font_titulo)
        
        # Folio
        folio = datos_certificado.get('folio', '')
        if folio:
            bbox_folio = draw.textbbox((0, 0), folio, font=font_folio)
            folio_ancho = bbox_folio[2] - bbox_folio[0]
            draw.text((img.width - folio_ancho - 50, 100), folio, fill='#95a5a6', font=font_folio)
        
        # Otorgado a
        draw.text((150, 300), "Otorgado a:", fill='#34495e', font=font_texto)
        draw.text((150, 370), datos_certificado['nombre_titular'], fill='#e74c3c', font=font_nombre)
        
        # A nombre de
        if datos_certificado.get('nombre_beneficiario') and datos_certificado['nombre_beneficiario'] != datos_certificado['nombre_titular']:
            draw.text((150, 500), "A nombre de:", fill='#34495e', font=font_texto)
            draw.text((150, 570), datos_certificado['nombre_beneficiario'], fill='#2980b9', font=font_nombre)
        
        # Tipo de certificado
        draw.text((150, 700), f"Certificado: {datos_certificado['certificado_nombre']}", 
                 fill='#16a085', font=font_texto)
        
        # Cantidad y monto
        draw.text((150, 770), f"Cantidad: {datos_certificado['cantidad']} | Monto: ${datos_certificado['monto']:,.2f} MXN", 
                 fill='#27ae60', font=font_texto)
        
        # Mensaje personalizado
        if datos_certificado.get('mensaje'):
            mensaje = datos_certificado['mensaje']
            wrapper = textwrap.TextWrapper(width=50)
            lines = wrapper.wrap(text=mensaje)
            
            y_position = 900
            for line in lines:
                draw.text((150, y_position), line, fill='#8e44ad', font=font_mensaje)
                y_position += 50
        
        # Fecha
        fecha = datos_certificado.get('fecha', datetime.now().strftime("%d de %B, %Y"))
        draw.text((150, 1100), f"Fecha: {fecha}", fill='#7f8c8d', font=font_texto)
        
        # Firma
        draw.line([(150, 1300), (500, 1300)], fill='black', width=2)
        draw.text((150, 1320), "Firma TecSalud", fill='#2c3e50', font=font_texto)
        
        # Guardar o retornar bytes
        if output_path:
            img.save(output_path, 'PNG', quality=95)
            return output_path
        else:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
        
    except Exception as e:
        print(f"Error generando certificado: {e}")
        return None

# ============================================
# RUTAS PARA CERTIFICADOS (TIPOS)
# ============================================

@app.route("/api/certificados", methods=['GET'])
def get_certificados():
    """Obtiene todos los certificados activos"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion, precio, imagen_url FROM certificados WHERE activo = 1")
        certificados = cursor.fetchall()
        
        result = []
        for cert in certificados:
            result.append({
                'id': cert['id'],
                'nombre': cert['nombre'],
                'descripcion': cert['descripcion'],
                'precio': cert['precio'],
                'imagen_url': cert['imagen_url'] or '/static/default-cert.jpg'
            })
        
        return jsonify({"certificados": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/certificados/<int:id>", methods=['GET'])
def get_certificado(id):
    """Obtiene un certificado específico"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion, precio, imagen_url FROM certificados WHERE id = ? AND activo = 1", (id,))
        cert = cursor.fetchone()
        
        if not cert:
            return jsonify({"error": "Certificado no encontrado"}), 404
        
        result = {
            'id': cert['id'],
            'nombre': cert['nombre'],
            'descripcion': cert['descripcion'],
            'precio': cert['precio'],
            'imagen_url': cert['imagen_url'] or '/static/default-cert.jpg'
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA DE PAGO (DESCARGA INMEDIATA)
# ============================================

@app.route("/api/procesar-pago", methods=['POST'])
def procesar_pago():
    """
    Procesa el pago, guarda en BD y descarga certificado inmediatamente
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # Validar campos
        required = ['nombre_titular', 'email', 'items']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Falta el campo {field}"}), 400
        
        # Calcular total
        total = 0
        for item in data['items']:
            total += item['precio'] * item['cantidad']
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Generar folio único
        fecha = datetime.now()
        folio = f"DON-{fecha.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Insertar donación
        cursor.execute("""
            INSERT INTO donaciones (nombre_titular, email, total, fecha, estado, folio)
            VALUES (?, ?, ?, datetime('now', 'localtime'), 'completada', ?)
        """, (data['nombre_titular'], data['email'], total, folio))
        
        donacion_id = cursor.lastrowid
        
        # Procesar cada item
        certificados_generados = []
        
        for item in data['items']:
            # Insertar detalle
            cursor.execute("""
                INSERT INTO donacion_detalles 
                (donacion_id, certificado_id, cantidad, precio_unitario, nombre_certificado, 
                 nombre_beneficiario, mensaje_personalizado, folio_certificado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                donacion_id,
                item.get('certificado_id'),
                item['cantidad'],
                item['precio'],
                item['nombre'],
                item.get('nombre_beneficiario', data['nombre_titular']),
                item.get('mensaje', ''),
                f"{folio}-{item.get('certificado_id', 'GEN')}"
            ))
            
            detalle_id = cursor.lastrowid
            
            # Preparar datos para el certificado
            datos_certificado = {
                'nombre_titular': data['nombre_titular'],
                'nombre_beneficiario': item.get('nombre_beneficiario', data['nombre_titular']),
                'email': data['email'],
                'mensaje': item.get('mensaje', ''),
                'certificado_nombre': item['nombre'],
                'cantidad': item['cantidad'],
                'monto': item['precio'] * item['cantidad'],
                'fecha': fecha.strftime("%d de %B, %Y"),
                'folio': f"{folio}-{item.get('certificado_id', 'GEN')}",
                'plantilla': f"plantilla_{item.get('certificado_id', 'default')}.jpg"
            }
            
            # Guardar en certificados_generados
            cursor.execute("""
                INSERT INTO certificados_generados 
                (donacion_detalle_id, nombre_donante, email_donante, nombre_beneficiario, mensaje, veces_descargado)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                detalle_id,
                data['nombre_titular'],
                data['email'],
                item.get('nombre_beneficiario', data['nombre_titular']),
                item.get('mensaje', '')
            ))
            
            cert_gen_id = cursor.lastrowid
            
            certificados_generados.append({
                'detalle_id': detalle_id,
                'cert_gen_id': cert_gen_id,
                'datos': datos_certificado
            })
        
        conn.commit()
        
        # Tomamos el primer certificado para descargar (si hay múltiples, podrías hacer un ZIP)
        cert_data = certificados_generados[0]['datos']
        
        # Generar imagen
        img_bytes = generar_imagen_certificado(cert_data)
        
        if not img_bytes:
            return jsonify({"error": "Error al generar certificado"}), 500
        
        # Crear respuesta con la imagen
        response = send_file(
            img_bytes,
            as_attachment=True,
            download_name=f"certificado_{cert_data['nombre_beneficiario'].replace(' ', '_')}.png",
            mimetype='image/png'
        )
        
        # Agregar headers con info de la donación
        response.headers['X-Donacion-ID'] = str(donacion_id)
        response.headers['X-Folio'] = folio
        response.headers['X-Certificados'] = str(len(certificados_generados))
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PARA REGENERAR CERTIFICADO POR ID
# ============================================

@app.route("/api/certificado/<int:detalle_id>", methods=['GET'])
def get_certificado_by_id(detalle_id):
    """
    Regenera un certificado usando los datos guardados en BD
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Obtener datos completos
        cursor.execute("""
            SELECT 
                d.nombre_titular,
                d.email,
                d.fecha,
                d.folio as folio_donacion,
                dd.nombre_beneficiario,
                dd.mensaje_personalizado as mensaje,
                dd.nombre_certificado,
                dd.cantidad,
                dd.precio_unitario,
                dd.certificado_id,
                dd.folio_certificado,
                cg.id as cert_gen_id,
                cg.veces_descargado
            FROM donacion_detalles dd
            JOIN donaciones d ON dd.donacion_id = d.id
            LEFT JOIN certificados_generados cg ON dd.id = cg.donacion_detalle_id
            WHERE dd.id = ?
        """, (detalle_id,))
        
        detalle = cursor.fetchone()
        
        if not detalle:
            return jsonify({"error": "Certificado no encontrado"}), 404
        
        # Actualizar contador de descargas
        if detalle['cert_gen_id']:
            cursor.execute("""
                UPDATE certificados_generados 
                SET veces_descargado = veces_descargado + 1,
                    ultima_descarga = datetime('now', 'localtime')
                WHERE id = ?
            """, (detalle['cert_gen_id'],))
            conn.commit()
        
        # Formatear fecha
        fecha_donacion = datetime.strptime(detalle['fecha'], '%Y-%m-%d %H:%M:%S')
        fecha_formateada = fecha_donacion.strftime("%d de %B, %Y")
        
        # Preparar datos para regenerar
        datos_certificado = {
            'nombre_titular': detalle['nombre_titular'],
            'nombre_beneficiario': detalle['nombre_beneficiario'] or detalle['nombre_titular'],
            'email': detalle['email'],
            'mensaje': detalle['mensaje'] or '',
            'certificado_nombre': detalle['nombre_certificado'],
            'cantidad': detalle['cantidad'],
            'monto': detalle['cantidad'] * detalle['precio_unitario'],
            'fecha': fecha_formateada,
            'folio': detalle['folio_certificado'] or detalle['folio_donacion'],
            'plantilla': f"plantilla_{detalle['certificado_id'] or 'default'}.jpg"
        }
        
        # Determinar el formato de respuesta
        formato = request.args.get('formato', 'view')
        
        if formato == 'download':
            # Forzar descarga
            img_bytes = generar_imagen_certificado(datos_certificado)
            if not img_bytes:
                return jsonify({"error": "Error al generar el certificado"}), 500
            
            nombre_archivo = f"certificado_{datos_certificado['nombre_beneficiario'].replace(' ', '_')}.png"
            return send_file(
                img_bytes,
                as_attachment=True,
                download_name=nombre_archivo,
                mimetype='image/png'
            )
        elif formato == 'json':
            return jsonify(datos_certificado), 200
        else:
            # Ver en navegador
            img_bytes = generar_imagen_certificado(datos_certificado)
            if not img_bytes:
                return jsonify({"error": "Error al generar el certificado"}), 500
            
            return send_file(img_bytes, mimetype='image/png')
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PARA VER TODOS LOS CERTIFICADOS DE UNA DONACIÓN
# ============================================

@app.route("/api/donacion/<int:donacion_id>/certificados", methods=['GET'])
def get_certificados_donacion(donacion_id):
    """
    Lista todos los certificados de una donación
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                dd.id as detalle_id,
                dd.nombre_certificado,
                dd.cantidad,
                dd.precio_unitario,
                dd.nombre_beneficiario,
                dd.folio_certificado,
                d.folio as folio_donacion,
                d.fecha,
                cg.id as cert_gen_id,
                cg.veces_descargado,
                cg.ultima_descarga
            FROM donacion_detalles dd
            JOIN donaciones d ON dd.donacion_id = d.id
            LEFT JOIN certificados_generados cg ON dd.id = cg.donacion_detalle_id
            WHERE dd.donacion_id = ?
        """, (donacion_id,))
        
        certificados = cursor.fetchall()
        
        result = []
        for cert in certificados:
            result.append({
                'detalle_id': cert['detalle_id'],
                'nombre_certificado': cert['nombre_certificado'],
                'cantidad': cert['cantidad'],
                'monto': cert['cantidad'] * cert['precio_unitario'],
                'nombre_beneficiario': cert['nombre_beneficiario'],
                'folio': cert['folio_certificado'] or cert['folio_donacion'],
                'fecha': cert['fecha'],
                'veces_descargado': cert['veces_descargado'] or 0,
                'ultima_descarga': cert['ultima_descarga'],
                'url_ver': f"/api/certificado/{cert['detalle_id']}",
                'url_descargar': f"/api/certificado/{cert['detalle_id']}?formato=download"
            })
        
        return jsonify({
            'donacion_id': donacion_id,
            'certificados': result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PARA BUSCAR CERTIFICADOS POR EMAIL
# ============================================

@app.route("/api/mis-certificados/<string:email>", methods=['GET'])
def mis_certificados(email):
    """
    Devuelve todos los certificados de un email
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                d.id as donacion_id,
                d.fecha,
                d.folio as folio_donacion,
                d.total as total_donacion,
                dd.id as detalle_id,
                dd.nombre_certificado,
                dd.cantidad,
                dd.precio_unitario,
                dd.nombre_beneficiario,
                dd.folio_certificado,
                cg.id as cert_gen_id,
                cg.veces_descargado
            FROM donaciones d
            JOIN donacion_detalles dd ON d.id = dd.donacion_id
            LEFT JOIN certificados_generados cg ON dd.id = cg.donacion_detalle_id
            WHERE d.email = ?
            ORDER BY d.fecha DESC
        """, (email,))
        
        certificados = cursor.fetchall()
        
        result = []
        for cert in certificados:
            result.append({
                'donacion_id': cert['donacion_id'],
                'detalle_id': cert['detalle_id'],
                'fecha': cert['fecha'],
                'folio': cert['folio_certificado'] or cert['folio_donacion'],
                'certificado_nombre': cert['nombre_certificado'],
                'cantidad': cert['cantidad'],
                'monto_total': cert['cantidad'] * cert['precio_unitario'],
                'nombre_beneficiario': cert['nombre_beneficiario'] or 'No especificado',
                'veces_descargado': cert['veces_descargado'] or 0,
                'url_ver': f"/api/certificado/{cert['detalle_id']}",
                'url_descargar': f"/api/certificado/{cert['detalle_id']}?formato=download"
            })
        
        return jsonify({
            'email': email,
            'total_certificados': len(result),
            'certificados': result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PARA ESTADÍSTICAS
# ============================================

@app.route("/api/estadisticas", methods=['GET'])
def get_estadisticas():
    """Obtiene estadísticas generales"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Totales generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_donaciones,
                COALESCE(SUM(total), 0) as monto_total,
                COALESCE(AVG(total), 0) as promedio_donacion
            FROM donaciones 
            WHERE estado = 'completada'
        """)
        totales = cursor.fetchone()
        
        # Donaciones hoy
        cursor.execute("""
            SELECT 
                COUNT(*) as donaciones_hoy,
                COALESCE(SUM(total), 0) as monto_hoy
            FROM donaciones 
            WHERE DATE(fecha) = DATE('now', 'localtime')
            AND estado = 'completada'
        """)
        hoy = cursor.fetchone()
        
        # Donaciones este mes
        cursor.execute("""
            SELECT 
                COUNT(*) as donaciones_mes,
                COALESCE(SUM(total), 0) as monto_mes
            FROM donaciones 
            WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now', 'localtime')
            AND estado = 'completada'
        """)
        mes = cursor.fetchone()
        
        # Top certificados
        cursor.execute("""
            SELECT 
                nombre_certificado,
                SUM(cantidad) as total_vendidos,
                SUM(cantidad * precio_unitario) as total_recaudado
            FROM donacion_detalles
            GROUP BY nombre_certificado
            ORDER BY total_recaudado DESC
            LIMIT 5
        """)
        top = cursor.fetchall()
        
        # Total certificados generados
        cursor.execute("SELECT COUNT(*) as total_gen FROM certificados_generados")
        total_gen = cursor.fetchone()
        
        # Descargas totales
        cursor.execute("SELECT COALESCE(SUM(veces_descargado), 0) as total_descargas FROM certificados_generados")
        total_desc = cursor.fetchone()
        
        top_list = []
        for t in top:
            top_list.append({
                'nombre': t['nombre_certificado'],
                'cantidad': t['total_vendidos'],
                'recaudado': t['total_recaudado']
            })
        
        result = {
            'totales': {
                'donaciones': totales['total_donaciones'] or 0,
                'monto': totales['monto_total'] or 0,
                'promedio': round(totales['promedio_donacion'] or 0, 2)
            },
            'hoy': {
                'donaciones': hoy['donaciones_hoy'] or 0,
                'monto': hoy['monto_hoy'] or 0
            },
            'mes': {
                'donaciones': mes['donaciones_mes'] or 0,
                'monto': mes['monto_mes'] or 0
            },
            'certificados': {
                'generados': total_gen['total_gen'] or 0,
                'descargas': total_desc['total_descargas'] or 0
            },
            'top_certificados': top_list
        }
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PARA TEST HTML
# ============================================

@app.route("/testcerts")
def test_certificados_html():
    """Sirve el HTML de prueba de certificados"""
    try:
        # Intentar servir desde templates
        from flask import render_template
        return render_template("testcerts.html")
    except ImportError:
        # Fallback: servir archivo estático
        return send_file('testcerts.html')
    except Exception as e:
        # Si no encuentra el archivo, mostrar instrucciones
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Archivo testcerts.html no encontrado</h1>
            <p>Crea el archivo en /templates/testcerts.html o en la raíz del proyecto</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """

# ============================================
# RUTA PARA VERIFICAR BASE DE DATOS
# ============================================

@app.route("/api/check-db", methods=['GET'])
def check_database():
    """Verifica el estado de la base de datos"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        tables = {}
        for table in ['certificados', 'donaciones', 'donacion_detalles', 'certificados_generados']:
            try:
                count = cursor.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()['count']
                tables[table] = count
            except:
                tables[table] = "Error - no existe"
        
        # Últimas donaciones
        ultimas = cursor.execute("""
            SELECT folio, nombre_titular, total, fecha 
            FROM donaciones 
            ORDER BY fecha DESC 
            LIMIT 5
        """).fetchall()
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'tablas': tables,
            'ultimas_donaciones': [dict(u) for u in ultimas]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# ============================================
# RUTA PARA MIGRAR/ACTUALIZAR BASE DE DATOS
# ============================================

@app.route("/api/migrar", methods=['GET'])
def migrar_bd():
    """Agrega columnas faltantes a las tablas"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Agregar columna folio a donaciones
        try:
            cursor.execute("ALTER TABLE donaciones ADD COLUMN folio TEXT")
            print("Columna folio agregada a donaciones")
        except:
            print("Columna folio ya existe en donaciones")
        
        # Agregar columnas a donacion_detalles
        try:
            cursor.execute("ALTER TABLE donacion_detalles ADD COLUMN nombre_beneficiario TEXT")
            print("Columna nombre_beneficiario agregada a donacion_detalles")
        except:
            print("Columna nombre_beneficiario ya existe")
        
        try:
            cursor.execute("ALTER TABLE donacion_detalles ADD COLUMN mensaje_personalizado TEXT")
            print("Columna mensaje_personalizado agregada a donacion_detalles")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE donacion_detalles ADD COLUMN folio_certificado TEXT")
            print("Columna folio_certificado agregada a donacion_detalles")
        except:
            pass
        
        # Agregar columnas a certificados_generados
        try:
            cursor.execute("ALTER TABLE certificados_generados ADD COLUMN veces_descargado INTEGER DEFAULT 0")
            print("Columna veces_descargado agregada a certificados_generados")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE certificados_generados ADD COLUMN ultima_descarga DATETIME")
            print("Columna ultima_descarga agregada a certificados_generados")
        except:
            pass
        
        conn.commit()
        
        return jsonify({
            "mensaje": "Migración completada",
            "status": "ok"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# RUTA PRINCIPAL
# ============================================

@app.route("/")
def index():
    """Página principal con información de la API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TecSalud API</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .card { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }
            .btn { 
                display: inline-block; 
                background: #3498db; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 5px;
            }
            .endpoint { 
                background: #fff; 
                padding: 10px; 
                margin: 5px 0; 
                border-left: 4px solid #3498db;
            }
        </style>
    </head>
    <body>
        <h1>🚀 TecSalud API - Certificados</h1>
        
        <div class="card">
            <h2>🧪 Interfaz de Prueba</h2>
            <a href="/testcerts" class="btn">Ir al Test de Certificados</a>
        </div>

        <div class="card">
            <h2>📡 Endpoints Disponibles</h2>
            
            <div class="endpoint">
                <strong>GET /api/certificados</strong> - Lista todos los certificados disponibles
            </div>
            
            <div class="endpoint">
                <strong>POST /api/procesar-pago</strong> - Procesa un pago y descarga certificado
            </div>
            
            <div class="endpoint">
                <strong>GET /api/certificado/&lt;id&gt;</strong> - Ver/descargar un certificado específico
                <br><small>Parámetros: ?formato=download (para descargar), ?formato=json (para datos)</small>
            </div>
            
            <div class="endpoint">
                <strong>GET /api/mis-certificados/&lt;email&gt;</strong> - Busca certificados por email
            </div>
            
            <div class="endpoint">
                <strong>GET /api/donacion/&lt;id&gt;/certificados</strong> - Certificados de una donación
            </div>
            
            <div class="endpoint">
                <strong>GET /api/estadisticas</strong> - Estadísticas generales
            </div>
            
            <div class="endpoint">
                <strong>GET /api/check-db</strong> - Verificar estado de la BD
            </div>
            
            <div class="endpoint">
                <strong>GET /api/migrar</strong> - Actualizar estructura de la BD (ejecutar una vez)
            </div>
        </div>

        <div class="card">
            <h2>📊 Estado del Sistema</h2>
            <p><a href="/api/check-db" class="btn">Verificar Base de Datos</a></p>
        </div>
    </body>
    </html>
    """

@app.route("/main")
def registro():
   if request.method == "GET":
      return render_template("proyecto.html")

# ============================================
# INICIO DEL SERVIDOR
# ============================================

if __name__ == '__main__':
    print("="*60)
    print("🚀 TecSalud - Sistema de Certificados")
    print("="*60)
    print("📌 RUTAS DISPONIBLES:")
    print("   🌐 /                          - Página principal")
    print("   🧪 /testcerts                  - Interfaz de prueba")
    print("   📦 /api/certificados           - Lista certificados")
    print("   💳 /api/procesar-pago           - Procesar pago")
    print("   📄 /api/certificado/<id>        - Ver certificado")
    print("   📧 /api/mis-certificados/<email> - Buscar por email")
    print("   📊 /api/estadisticas            - Estadísticas")
    print("   🔧 /api/migrar                  - Migrar BD (ejecutar una vez)")
    print("="*60)
    print(f"📁 BD: {DATABASE}")
    print(f"📁 Plantillas: {TEMPLATES_FOLDER}")
    print(f"📁 Certificados: {UPLOAD_FOLDER}")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=7070)