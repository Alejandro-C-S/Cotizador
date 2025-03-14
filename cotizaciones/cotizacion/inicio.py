#constantes globales
Tolerancia = 0.2756
Centimeter = 2.54
Pi = 3.1416
material = 0.5
Ajuste = 0.15  # 15%
Infill = 0.02  # 2%
###procentaje
diseño = 0.31 #31%
cnc = 0.51 #51%
laser = 1.50 #150%

#Material Años
DMVC=[9.4,9.7,5.3,7.0,3.9,8.5,7.5,3.8,3.0,8.8] #AÑO UTILIZABLE
DMVT=[9.1,9.4,5.0,6.7,4.6,8.2,7.2,6.9,4.6,8.5]
DMVD=[7.7,7.9,4.0,5.0,4.5,7.2,6.8,5.3,5.3,7.5]

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_file, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from functools import wraps

import bcrypt
from io import BytesIO
import base64
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import joinedload

from sqlalchemy import event
from sqlalchemy.orm import Session

import asyncio
import nest_asyncio
import subprocess
from xhtml2pdf import pisa

app = Flask(__name__)
app.secret_key = "ADIMMA_Cotizacion" #Palabra secreta

################################ Base de datos #############################################

app.config['UPLOAD_FOLDER'] = 'static/images'# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Cotizaciones.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) 

##################### Crear tablas #####################
class Usuario (db.Model):
    idusuario = db.Column(db.Integer, primary_key=True)
    nombre =  db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    usuario = db.Column(db.String(100), unique = True)
    contraseña = db.Column(db.String(100))
    img = db.Column(db.LargeBinary, nullable=True)
    rol = db.Column(db.String(50))

class Proyecto (db.Model):
    idproyecto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique = True)
    consecutivo = db.Column(db.String(50), unique = True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    usuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    

class Producto (db.Model):
    idproducto = db.Column(db.Integer, primary_key=True)
    tipo_perfil = db.Column(db.String(100), unique = True)
    calculo = db.Column(db.String(60), nullable=False)
    diametro = db.Column(db.Boolean, nullable=False, default=False)
    longitud = db.Column(db.Boolean, nullable=False, default=False)
    ancho = db.Column(db.Boolean, nullable=False, default=False)
    alto = db.Column(db.Boolean, nullable=False, default=False)
    espesor = db.Column(db.Boolean, nullable=False, default=False)
    v_final = db.Column(db.Boolean, nullable=False, default=False)
    n_cortes = db.Column(db.Boolean, nullable=False, default=False)
    vmm3 = db.Column(db.Boolean, nullable=False, default=False)
    kg = db.Column(db.Boolean, nullable=False, default=False)
    materiales = db.relationship('Material', backref='producto', cascade='all, delete-orphan')

class Material (db.Model):
    idmaterial = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    densidad = db.Column(db.Float, nullable=True)
    dmvc = db.Column(db.Float, nullable=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.idproducto'))
    precio = db.relationship('Precio', backref='material', cascade='all, delete-orphan')

class Precio (db.Model):
    idprecio = db.Column(db.Integer, primary_key=True)
    precio = db.Column(db.Double)
    fecha = db.Column(db.DateTime, default=datetime.now)
    material_id = db.Column(db.Integer, db.ForeignKey('material.idmaterial'))


class Fabricacion (db.Model):
    idfabricacion = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(100))
    precio = db.Column(db.Double) 

class Cotizaciones (db.Model):
    idcotizacion = db.Column(db.Integer, primary_key=True)
    tipo_perfil = db.Column(db.String(100))
    Material = db.Column(db.String(100))
    fabricacion = db.Column(db.Float, nullable=True)
    diametro = db.Column(db.Float, nullable=True)  # Cambiado a Float
    longitud = db.Column(db.Float, nullable=True)  # Cambiado a Float
    n_cortes = db.Column(db.Integer, nullable=True)
    v_final = db.Column(db.Float, nullable=True)  # Cambiado a Float
    v_inicial = db.Column(db.Float, nullable=True)  # Cambiado a Float
    cantidad = db.Column(db.Float, nullable=True)
    long = db.Column(db.Float, nullable =True)
    precio_mp = db.Column(db.Float, nullable=True)
    cost_FAB = db.Column(db.Float, nullable=True)
    espesor = db.Column(db.Float, nullable=True)  # Cambiado a Float
    alto = db.Column(db.Float, nullable=True)  # Cambiado a Float
    ancho = db.Column(db.Float, nullable=True)  # Cambiado a Float
    vmm3 = db.Column(db.Float, nullable=True)  # Cambiado a Float
    kg = db.Column(db.Float, nullable=True)
    segundos = db.Column(db.Double)
    minutos = db.Column(db.Double)
    horas = db.Column(db.Double)
    fecha = db.Column(db.DateTime, default=datetime.now)
    diseño = db.Column(db.Float, nullable=True)
    cnc = db.Column(db.Float, nullable=True)
    laser = db.Column(db.Float, nullable=True)
    mro = db.Column(db.Float, nullable=True)
    hora_mro = db.Column(db.Float, nullable=True)
    com = db.Column(db.Float, nullable=True)
    precio_com = db.Column(db.Float, nullable=True)
    usuario = db.Column(db.Integer, db.ForeignKey('usuario.idusuario'))
    proyecto = db.Column(db.Integer, db.ForeignKey('proyecto.idproyecto'))


class Cabeza(db.Model):
    idcabeza = db.Column(db.Integer, primary_key=True)
    tipo_cabeza = db.Column(db.String(100))  # Tipo de cabeza (Cabeza de barril, etc.)

class Componentes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_componente = db.Column(db.String(100))  # Tipo del componente (Tornillo métrico, Opresor, etc.)
    id_cabeza = db.Column(db.Integer, db.ForeignKey('cabeza.idcabeza'))
    tornillo = db.Column(db.Integer, nullable=True)  # Medida de tornillo (3, 4, 5, 6, 8, 9, 10, 12)
    longitud = db.Column(db.Integer, nullable=True)  # Longitud de la pieza (10, 12, 16, 20, etc.)


# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()


######################### Inserta usuario de administrador ################################
    # Verificar si ya existe un usuario admin
    admin_user = Usuario.query.filter_by(usuario='admin').first()
    if not admin_user:
        # Crear un nuevo usuario admin
        hashed_password = bcrypt.hashpw('admin_password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        nuevo_admin = Usuario(nombre='Admin', apellido='User ', usuario='admin', contraseña=hashed_password, rol='admin')
        db.session.add(nuevo_admin)
        db.session.commit()
        print("Usuario admin creado.")
    else:
        print("El usuario admin ya existe.")



################################# Endpoints paginas #################################

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if session.get('rol') not in roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Buscar el usuario en la base de datos
        usuario = Usuario.query.filter_by(usuario=username).first()
        
        if usuario and bcrypt.checkpw(password.encode('utf-8'), usuario.contraseña.encode('utf-8')):
            # Si las credenciales son correctas, guardar el usuario en la sesión
            session['username'] = usuario.usuario
            session['rol'] = usuario.rol
            
            # Redirigir según el rol
            if usuario.rol == 'admin':
                return redirect(url_for('ad_cotizacion'))  # Redirige a la página de cotizaciones para administradores
            else:
                return redirect(url_for('pro_cotizacion'))  # Redirige a la página de cotizaciones para usuarios normales
        else:
            error = "Usuario o contraseña incorrectos"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Elimina al usuario de la sesión
    return redirect(url_for('login'))

@app.context_processor
def inject_user():
    # Esto hace que 'username' esté disponible en todas las plantillas
    return {'username': session.get('username')}

@app.route('/proyecto', methods=['GET', 'POST'])

def proyecto():
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        consecutivo = request.form.get('consecutivo')
        usuario = session.get('username')
        print(usuario)
        if not usuario:
            return redirect(url_for('login'))  # Redirige al usuario a la página de inicio de sesión si no está autenticado
        
        user_data = Usuario.query.filter_by(usuario=usuario).first()
        if not user_data:
            return "Usuario no encontrado", 404
        
        user_id = user_data.idusuario

        nuevo_proyecto = Proyecto(
            nombre=nombre,
            consecutivo=consecutivo,
            usuario=user_id
        )

        try:
            db.session.add(nuevo_proyecto)
            db.session.commit()
            return redirect(url_for('nuevo', proyecto_id=nuevo_proyecto.idproyecto))
        except IntegrityError:
            db.session.rollback()
            error_message = "El nombre o el consecutivo ya existen. Por favor, elige valores diferentes."
            return render_template('proyecto.html', error=error_message)
        return redirect(url_for('nuevo'))

    return render_template('proyecto.html')

@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'GET':
        # Obtener los tipos de componentes de la base de datos
        tipos_componentes = Componentes.query.all()
        tipos_cabezas =Cabeza.query.all()
        
       
        # Aquí puedes obtener otros datos que ya tienes (como productos, materiales, proyecto, etc.)
        usuario = session.get('username')
        user_data = Usuario.query.filter_by(usuario=usuario).first()  # No usa get
        user_id = user_data.idusuario if user_data else None
        productos = Producto.query.all()
        material = Material.query.all()      
        proyecto_id = request.args.get('proyecto_id')
        proyecto = db.session.get(Proyecto, proyecto_id)
        
        # Formateo de la fecha y hora
        fecha_formateada = None
        hora_formateada = None
        if proyecto is not None:
            fecha_hora = proyecto.fecha
            if fecha_hora is not None:
                fecha_formateada = fecha_hora.strftime('%d-%m-%Y')
                hora_formateada = fecha_hora.strftime('%H:%M')
        if fecha_formateada is None:
            fecha_formateada = 'Fecha no disponible'
        if hora_formateada is None:
            hora_formateada = 'Hora no disponible'

        cotizaciones = Cotizaciones.query.filter_by(proyecto=proyecto_id).all()

        # Renderizar el template con los datos obtenidos
        return render_template(
            'n_cotizacion.html',  # Nombre de tu plantilla
            user_id=user_id,
            productos=productos,
            material=material,
            fecha=fecha_formateada,
            hora=hora_formateada,
            proyecto=proyecto,
            cotizaciones=cotizaciones,
            tipos_componentes=tipos_componentes  # Pasar los tipos de componentes al template
        )
    
    elif request.method == 'POST':
        perfil_id = request.form.get('perfil')
        material_id = request.form.get('material')
        diametro = request.form.get('diametro')
        longitud = request.form.get('longitud')
        ancho = request.form.get('ancho')
        alto = request.form.get('alto')
        espesor = request.form.get('espesor')
        vfinal = request.form.get('vfinal')
        ncortes = request.form.get('ncortes')
        vmm = request.form.get('vmm')
        kg = request.form.get('kg')
        proyecto_id = request.args.get('proyecto_id')

        usuario = session.get('username')
        user_data = Usuario.query.filter_by(usuario=usuario).first()
        user_id = user_data.idusuario if user_data else None
        
        perfil = db.session.get(Producto, perfil_id)  # Reemplazado
        perfil_nombre = perfil.tipo_perfil if perfil else None
        
        material = db.session.get(Material, material_id)  # Reemplazado
        material_nombre = material.nombre if material else None

        nueva_cotizacion = Cotizaciones(
            tipo_perfil=perfil_nombre,
            Material=material_nombre,
            diametro=float(diametro) if diametro else None,
            longitud=float(longitud) if longitud else None,
            ancho=float(ancho) if ancho else None,
            alto=float(alto) if alto else None,
            espesor=float(espesor) if espesor else None,
            v_final=float(vfinal) if vfinal else None,
            n_cortes=int(ncortes) if ncortes else None,
            vmm3=float(vmm) if vmm else None,
            kg=float(kg) if kg else None,
            usuario=user_id,
            proyecto=proyecto_id
        )

        db.session.add(nueva_cotizacion)
        
        try:
            db.session.commit()
            cotizacion_id = nueva_cotizacion.idcotizacion
            nombre_material = nueva_cotizacion.Material
            cotizar_perfil(cotizacion_id, nombre_material)
            db.session.commit()  # Commit adicional para guardar los cálculos
            return redirect(url_for('nuevo', proyecto_id=proyecto_id))
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar cotización: {e}")
            return redirect(url_for('nuevo', proyecto_id=proyecto_id))




@app.route('/actualizar_c/<int:id>', methods=['POST'])
def actualizar_c(id):
    cotizacion = db.session.get(Cotizaciones, id)  # Reemplazado
    if not cotizacion:
        return jsonify({'error': f'No se encontró cotización con ID {id}'}), 404

    data = request.get_json()
    print(f"Datos recibidos del frontend: {data}")
    print(f"Estado inicial de cotización ID {id}: {cotizacion.__dict__}")

    campos_relevantes = [
        'longitud', 'espesor', 'ancho', 'alto', 'diametro', 
        'v_final', 'n_cortes', 'vmm3', 'kg', 'tipo_perfil', 'Material'
    ]
    campos_cambiados = False

    for field, value in data.items():
        if hasattr(cotizacion, field):
            print(f"Actualizando {field} con valor {value}")
            if field in ['longitud', 'espesor', 'ancho', 'alto', 'diametro', 'v_final', 'vmm3', 'kg']:
                try:
                    setattr(cotizacion, field, float(value))
                    print(f"{field} actualizado a {float(value)}")
                    if field in campos_relevantes:
                        campos_cambiados = True
                except ValueError:
                    return jsonify({'error': f'Valor inválido para {field}: {value}'}), 400
            elif field == 'n_cortes':
                try:
                    setattr(cotizacion, field, int(value))
                    print(f"{field} actualizado a {int(value)}")
                    campos_cambiados = True
                except ValueError:
                    return jsonify({'error': f'Valor inválido para {field}: {value}'}), 400
            else:
                setattr(cotizacion, field, value)
                print(f"{field} actualizado a {value}")
                if field in campos_relevantes:
                    campos_cambiados = True
        else:
            print(f"Campo ignorado: {field} no existe en Cotizaciones")

    if campos_cambiados:
        print(f"Detectado cambio en cotización ID {id}. Recalculando...")
        nombre_material = cotizacion.Material
        if not nombre_material:
            return jsonify({'error': 'El campo Material es requerido para recalcular'}), 400
        cotizar_perfil(id, nombre_material)

    try:
        db.session.commit()
        print(f"Estado final después de cotizar_perfil: {cotizacion.__dict__}")
        return jsonify({'message': 'Cotización actualizada', 'id': id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al guardar cambios: {str(e)}'}), 500

@app.route('/eliminar_c/<int:id>', methods=['POST', 'GET', 'DELETE'])
def eliminar_c(id):
    # Obtener la cotización por ID
    cotizacion = Cotizaciones.query.get(id)
    
    if cotizacion:
        proyecto_id = cotizacion.proyecto  # Obtener el ID del proyecto antes de eliminar
        # Eliminar la cotización de la base de datos
        db.session.delete(cotizacion)
        db.session.commit()
        mensaje = f"Cotización con ID {id} eliminada exitosamente."
    else:
        mensaje = f"Cotización con ID {id} no encontrada."
        proyecto_id = None  # Manejar el caso donde no se encuentra la cotización

    # Redirigir a la ruta 'nuevo' con el proyecto_id
    return redirect(url_for('nuevo', proyecto_id=proyecto_id))

@app.route('/obtener-materiales/<int:producto_id>', methods=['GET'])
def obtener_materiales(producto_id):
    """Devuelve los materiales asociados a un producto en formato JSON"""
    materiales = Material.query.filter_by(producto_id=producto_id).all()
    
    materiales_json = [{"idmaterial": m.idmaterial, "nombre": m.nombre} for m in materiales]
    
    return jsonify(materiales_json)


@app.route('/obtener-campos/<int:producto_id>', methods=['GET'])
def obtener_campos(producto_id):
    producto = db.session.get(Producto, producto_id)  # Reemplazado
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    campos_activos = {
        'diametro': producto.diametro,
        'longitud': producto.longitud,
        'ancho': producto.ancho,
        'alto': producto.alto,
        'espesor': producto.espesor,
        'vfinal': producto.v_final,
        'ncortes': producto.n_cortes,
        'vmm': producto.vmm3,
        'kg': producto.kg
    }
    
    campos = [campo for campo, activo in campos_activos.items() if activo]
    return jsonify({'campos': campos})



##################################################### PRODUCTO #####################################################################
@app.route('/producto', methods=['GET', 'POST'])
@role_required(['admin'])
def producto():
    accion = request.form.get('accion')
    id_producto = request.form.get('idProducto')
    id_material = request.form.get('idMaterial')
    id_precio = request.form.get('idPrecio')
    perfil = request.form.get('taskPerfil')
    material_nuevo = request.form.get('taskMaterial')
    precio_nuevo = request.form.get('taskPrecio')
    
    mensaje_error = None
    mensaje_exito = None
    editar = {}

    print(f"Valor de accion: '{accion}'")

    if request.method == 'POST':

        # Actualizar producto existente
        if accion == "actualizar" and id_producto:
            producto = Producto.query.get(id_producto)
            if not producto:
                mensaje_error = "Producto no encontrado."
            else:
                producto.tipo_perfil = perfil

                if id_material:
                    material = Material.query.get(id_material)
                    if material:
                        material.nombre = material_nuevo
                    else:
                        mensaje_error = "Material no encontrado."

                if precio_nuevo and id_precio:
                    try:
                        precio_nuevo_float = float(precio_nuevo)
                        precio = Precio.query.get(id_precio)
                        if precio:
                            precio.precio = precio_nuevo_float
                        else:
                            mensaje_error = "Precio no encontrado."
                    except ValueError:
                        mensaje_error = f"Precio inválido: {precio_nuevo}"

                try:
                    db.session.commit()
                    mensaje_exito = "Producto actualizado con éxito."
                    editar = {
                        'idproducto': producto.idproducto,
                        'perfil': producto.tipo_perfil,
                        'idmaterial': id_material if id_material else '',
                        'material': material_nuevo if id_material else '',
                        'idprecio': id_precio if id_precio else '',
                        'precio': precio_nuevo if id_precio else ''
                    }
                except Exception as e:
                    db.session.rollback()
                    mensaje_error = f"Error al actualizar: {str(e)}"

        # Agregar nuevo perfil
        elif accion == "agregar_perfil":
            try:
                nombre_perfil = request.form.get('nombrePerfil')
                calculo = request.form.get('calculo') 
                diametro = 'checkbox1' in request.form
                longitud = 'checkbox2' in request.form
                ancho = 'checkbox3' in request.form
                alto = 'checkbox4' in request.form
                espesor = 'checkbox5' in request.form
                v_final = 'checkbox6' in request.form
                n_cortes = 'checkbox7' in request.form
                vmm3 = 'checkbox8' in request.form
                kg = 'checkbox9' in request.form
            except Exception as e:
                db.session.rollback()
                return render_template('producto.html', active_page='productos', productos=productos, tipos_perfil=tipos_perfil, mensaje_error=mensaje_error, mensaje_exito=mensaje_exito, tipos_calculo=tipos_calculo, editar=editar)

            if nombre_perfil:
                try:
                    nuevo_perfil = Producto(
                        tipo_perfil=nombre_perfil,
                        calculo=calculo,
                        diametro=diametro,
                        longitud=longitud,
                        ancho=ancho,
                        alto=alto,
                        espesor=espesor,
                        v_final=v_final,
                        n_cortes=n_cortes,
                        vmm3=vmm3,
                        kg=kg
                    )
                    db.session.add(nuevo_perfil)
                    db.session.commit()
                    print(f"Perfil agregado, redirigiendo a id_perfil={nuevo_perfil.idproducto}")
                    mensaje_exito = "Perfil agregado con éxito."
                    return redirect(url_for('nuevo_perfil', id_perfil=nuevo_perfil.idproducto))
                except Exception as e:
                    db.session.rollback()
  
            else:
                print("Error: nombre_perfil no proporcionado")
                mensaje_error = "Nombre del perfil es obligatorio"

        # Agregar nuevo material
        elif accion == "agregar_material":
            try:
                perfil_seleccionado = request.form.get('taskPerfil')
                nombre_material = request.form.get('taskMaterial')
                densidad_material = request.form.get('densidadMaterial')
                precio_material = request.form.get('precioMaterial')  # Nuevo campo para el precio

                if not perfil_seleccionado or not nombre_material or not densidad_material:
                    mensaje_error = "Todos los campos son obligatorios para agregar un material."
                else:
                    try:
                        densidad_material = float(densidad_material)
                        if densidad_material <= 0:
                            raise ValueError("La densidad debe ser un número positivo.")
                    except ValueError:
                        mensaje_error = "La densidad debe ser un número válido."

                    # Validar el precio si se proporciona
                    precio_material_float = None
                    if precio_material:
                        try:
                            precio_material_float = float(precio_material)
                            if precio_material_float <= 0:
                                raise ValueError("El precio debe ser un número positivo.")
                        except ValueError:
                            mensaje_error = "El precio debe ser un número válido."

                    if not mensaje_error:
                        # Crear el nuevo material
                        nuevo_material = Material(nombre=nombre_material, densidad=densidad_material)
                        db.session.add(nuevo_material)
                        db.session.flush()  # Para obtener el ID antes del commit

                        # Asociar el material a un producto existente o nuevo
                        producto_existente = Producto.query.filter_by(tipo_perfil=perfil_seleccionado).first()
                        if producto_existente:
                            producto_existente.materiales.append(nuevo_material)
                        else:
                            nuevo_producto = Producto(tipo_perfil=perfil_seleccionado, materiales=[nuevo_material])
                            db.session.add(nuevo_producto)

                        # Guardar el precio si se proporcionó
                        if precio_material_float:
                            nuevo_precio = Precio(
                                precio=precio_material_float,
                                fecha=datetime.now(),
                                material_id=nuevo_material.idmaterial
                            )
                            db.session.add(nuevo_precio)

                        db.session.commit()
                        mensaje_exito = f"Material '{nombre_material}' agregado con éxito con densidad {densidad_material}."
                        if precio_material_float:
                            mensaje_exito += f" Precio: ${precio_material_float}."
            except Exception as e:
                db.session.rollback()
                mensaje_error = f"Error al agregar material: {str(e)}"


    productos = Producto.query.options(
        joinedload(Producto.materiales).joinedload(Material.precio)
    ).all()

    tipos_perfil = db.session.query(Producto.tipo_perfil).distinct().all()
    tipos_perfil = [tipo[0] for tipo in tipos_perfil]
    tipos_calculo = db.session.query(Producto.calculo).distinct().all()
    tipos_calculo = [calculo[0] for calculo in tipos_calculo]

    return render_template('producto.html', active_page='productos', productos=productos, tipos_perfil=tipos_perfil, mensaje_error=mensaje_error, mensaje_exito=mensaje_exito, tipos_calculo=tipos_calculo, editar=editar)

    # Recargar los productos y materiales para la vista
    productos = Producto.query.options(
        joinedload(Producto.materiales).joinedload(Material.precio)
    ).all()

    tipos_perfil = db.session.query(Producto.tipo_perfil).distinct().all()
    tipos_perfil = [tipo[0] for tipo in tipos_perfil]

    return render_template(
        'producto.html',
        active_page='productos',
        productos=productos,
        tipos_perfil=tipos_perfil,
        mensaje_error=mensaje_error,
        mensaje_exito=mensaje_exito
    )


@app.route('/eliminar_material/<int:id>', methods=['GET', 'POST'])
def eliminar_material(id):
    try:
        material = Material.query.get(id)
        if material:
            db.session.query(Precio).filter(Precio.material_id == material.idmaterial).delete()
            db.session.delete(material)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        print("Error al eliminar el material:", e)

    return redirect(url_for('producto')) 

@app.route('/eliminar_perfil', methods=['POST'])
def eliminar_perfil():
    tipo_perfil = request.form.get('tipoPerfil')

    if not tipo_perfil:
        flash('Debe ingresar un tipo de perfil válido.', 'danger')
        return redirect(url_for('producto'))

    perfil = Perfil.query.filter_by(tipo_perfil=tipo_perfil).first()

    if perfil:
        db.session.delete(perfil)
        db.session.commit()
        flash(f'Perfil "{tipo_perfil}" eliminado correctamente.', 'success')
    else:
        flash('Perfil no encontrado.', 'danger')

    return redirect(url_for('producto'))

############################################## FABRICACIÓN #################################################################

@app.route('/fabricacion', methods=['GET', 'POST'])
@role_required(['admin'])
def fabricacion():
    mensaje_error = None  
    mensaje_exito = None  

    if request.method == 'POST':
        tipo = request.form.get('taskPerfil')
        precio = request.form.get('taskPrecio')
        id_fabricacion = request.form.get('idFabricacion')
        accion = request.form.get('accion')

        if tipo and precio:
            try:
                fabricacion_existente = Fabricacion.query.filter_by(tipo=tipo, precio=float(precio)).first()
                if accion == "agregar":
                    if fabricacion_existente:
                        mensaje_error = "El tipo y precio ya están registrados."
                    else:
                        nueva_fabricacion = Fabricacion(tipo=tipo, precio=float(precio))
                        db.session.add(nueva_fabricacion)
                        db.session.commit()
                        mensaje_exito = "Producto agregado correctamente."

                elif accion == "actualizar" and id_fabricacion:
                    fabricacion = Fabricacion.query.get(id_fabricacion)
                    if fabricacion:
                        fabricacion.tipo = tipo
                        fabricacion.precio = float(precio)
                        db.session.commit()
                        mensaje_exito = "Producto actualizado correctamente."

            except Exception as e:
                db.session.rollback()
                mensaje_error = f"Error en la base de datos: {e}"

    fabricaciones = Fabricacion.query.all()
    return render_template('fabricacion.html', active_page='fabricacion', fabricacion=fabricaciones, mensaje_error=mensaje_error, mensaje_exito=mensaje_exito)

@app.route('/eliminar_fabricacion/<int:id>', methods=['GET'])
def eliminar_fabricacion(id):
    fabricacion = Fabricacion.query.get(id)
    if fabricacion:
        try:
            db.session.delete(fabricacion)
            db.session.commit()
            print("Registro eliminado correctamente de Cotizaciones.db")
        except Exception as e:
            db.session.rollback()
            print("Error al eliminar de Cotizaciones.db:", e)
    return redirect(url_for('fabricacion'))

#### G_USUARIO ####    

@app.route('/g_usuario', methods=['GET', 'POST'])
@role_required(['admin'])
def g_usuario():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')

        # Encriptar la contraseña antes de guardarla
        hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Crear un nuevo usuario
        nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, usuario=usuario, contraseña=hashed_password, rol="usuario")

        try:
            # Guardar en la base de datos
            db.session.add(nuevo_usuario)
            db.session.commit()
            return redirect(url_for('g_usuario'))  # Redirigir al formulario de usuarios
        except Exception as e:
            db.session.rollback()
            print(e)

    # Obtener todos los usuarios desde la base de datos
    usuarios = Usuario.query.all()
    return render_template('g_usuario.html', active_page='usuarios', usuarios=usuarios)

def encrypt_password(password):
    # Genera un salt y encripta la contraseña
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')  # Guardar como string

@app.route('/actualizar_usuario', methods=['POST'])
def actualizar_usuario():
    idusuario = request.form.get('idusuario')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    usuario = request.form.get('usuario')
    contraseña = request.form.get('contraseña')

    try:
        usuario_a_actualizar = Usuario.query.get(idusuario)
        if usuario_a_actualizar:
            usuario_a_actualizar.nombre = nombre
            usuario_a_actualizar.apellido = apellido
            usuario_a_actualizar.usuario = usuario
            if contraseña:
                # Encripta la contraseña usando bcrypt
                usuario_a_actualizar.contraseña = encrypt_password(contraseña)
            db.session.commit()
            print(f"Usuario {idusuario} actualizado correctamente")
    except Exception as e:
        db.session.rollback()
        print("Error:", e)
    finally:
        db.session.close()
        
    return redirect(url_for('g_usuario'))
    
@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    usuario = Usuario.query.get(id)
    if usuario:
        try:
            db.session.delete(usuario)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
        finally:
            db.session.close()
    return redirect(url_for('g_usuario'))  # Redirigir a la lista de usuarios


@app.route('/pro_cotizacion')
@role_required(['usuario'])
def pro_cotizacion():
    busqueda = request.args.get('busqueda')

    # Filtrar proyectos por nombre o consecutivo si se proporciona
    proyectos_query = Proyecto.query

    if busqueda:
        proyectos_query = proyectos_query.filter(
            (Proyecto.nombre.ilike(f'{busqueda}%')) |  # Filtra por la inicial de nombre
            (Proyecto.consecutivo.ilike(f'{busqueda}%'))  # Filtra por la inicial de consecutivo
        )

    proyectos = Proyecto.query.all()
    # Obtener todos los proyectos de la base de datos
    if 'username' not in session:
        return redirect(url_for('login'))  # Si no está autenticado, redirige al login
    
    # Obtener el nombre de usuario desde la sesión
    username = session['username']
    
    # Buscar el usuario en la base de datos
    usuario = Usuario.query.filter_by(usuario=username).first()
    
    if usuario:
        # Obtener todos los proyectos asociados a este usuario
        proyectos = Proyecto.query.filter_by(usuario=usuario.idusuario).all()
    # Pasar los proyectos a la plantilla pro_cotizacion.html
    return render_template('pro_cotizacion.html', proyectos=proyectos)

@app.route('/ver_proyecto/<int:id>', methods=['GET'])
def ver_proyecto(id):
    # Buscar el proyecto por su ID
    proyecto = Proyecto.query.get_or_404(id)
    
    # Incluye las cotizaciones relacionadas con el proyecto
    cotizaciones = Cotizaciones.query.filter_by(proyecto=id).all()
    
    # Retorna la plantilla para ver el proyecto con las cotizaciones
    return render_template('ver_proyecto.html', proyecto=proyecto, cotizaciones=cotizaciones)



@app.route('/r_cotizacion/<int:id>', methods=['GET'])
def r_cotizacion(id):    
    # Buscar el proyecto por su ID
    proyecto = Proyecto.query.get_or_404(id)
    # Incluye las cotizaciones relacionadas con el proyecto
    cotizaciones = Cotizaciones.query.filter_by(proyecto=id).all()
    return render_template('r_cotizacion.html',proyecto=proyecto, cotizaciones=cotizaciones)


@app.route('/ad_cotizacion', methods=["GET"])
def ad_cotizacion():
    busqueda = request.args.get('busqueda')

    # Filtrar proyectos por nombre o consecutivo si se proporciona
    proyectos_query = Proyecto.query

    if busqueda:
        proyectos_query = proyectos_query.filter(
            (Proyecto.nombre.ilike(f'{busqueda}%')) |  # Filtra por la inicial de nombre
            (Proyecto.consecutivo.ilike(f'{busqueda}%'))  # Filtra por la inicial de consecutivo
        )

    proyectos = proyectos_query.all()

    # Obtener el nombre del usuario relacionado con el primer proyecto (si es necesario)
    usuarios_proyectos = {}
    for proyecto in proyectos:
        usuario = Usuario.query.filter_by(idusuario=proyecto.usuario).first()
        usuarios_proyectos[proyecto.idproyecto] = usuario.nombre if usuario else "Sin usuario"

    return render_template('ad_cotizacion.html',proyectos=proyectos,active_page='cotizaciones',usuarios_proyectos=usuarios_proyectos)

@app.route('/ver_proyecto2/<int:id>', methods=['GET'])
def ver_proyecto2(id):
    # Buscar el proyecto por su ID
    proyecto = Proyecto.query.get_or_404(id)
    
    # Incluye las cotizaciones relacionadas con el proyecto
    cotizaciones = Cotizaciones.query.filter_by(proyecto=id).all()
    
    # Retorna la plantilla para ver el proyecto con las cotizaciones
    return render_template('ver_proyecto_admin.html', proyecto=proyecto, cotizaciones=cotizaciones)            

@app.context_processor
def inject_user():
    if 'username' in session:
        usuario_actual = Usuario.query.filter_by(usuario=session['username']).first()
        if usuario_actual:
            img_url = (
                f"data:image/jpeg;base64,{base64.b64encode(usuario_actual.img).decode('utf-8')}"
                if usuario_actual.img else url_for('static', filename='images/perfil.png')
            )
            es_admin = usuario_actual.rol == 'admin'  # Verificar si el usuario es administrador
            return dict(img_url=img_url, es_admin=es_admin, usuario=usuario_actual)
    
    return dict(img_url=url_for('static', filename='images/perfil.png'), es_admin=False)


@app.route('/p_usuario', methods=["GET", "POST"])
@role_required(['admin', 'usuario'])
def p_usuario():
    # Verificación de sesión
    if 'username' not in session:
        return redirect(url_for('login'))

    # Obtener el usuario actual
    usuario_actual = Usuario.query.filter_by(usuario=session['username']).first()

    # Si no existe el usuario, redirigir al login
    if not usuario_actual:
        return redirect(url_for('login'))

    # Procesar el formulario si es POST
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # Formulario de imagen
        if form_type == 'image':
            if 'profileImage' in request.files:
                image = request.files['profileImage']
                if image.filename != '':
                    usuario_actual.img = image.read()  # Guardar la imagen como binario
                    try:
                        db.session.commit()
                        flash('Imagen actualizada correctamente', 'image_success')
                    except Exception as e:
                        db.session.rollback()
                        flash('Error al actualizar la imagen', 'image_danger')
                        print(e)
            return redirect(url_for('p_usuario'))

        # Formulario de datos personales
        elif form_type == 'data':
            nombre = request.form['taskNombre']
            apellido = request.form['taskApellido']
            nuevo_usuario = request.form['taskUsuario']
            contrasena_actual = request.form['taskContrasenaActual']
            contrasena_nueva = request.form['taskContrasena']

            # Verificar que la contraseña actual sea correcta
            if not bcrypt.checkpw(contrasena_actual.encode('utf-8'), usuario_actual.contraseña.encode('utf-8')):
                flash('La contraseña actual es incorrecta', 'danger')
                return redirect(url_for('p_usuario'))

            # Verificar si el nombre de usuario ya está en uso
            if nuevo_usuario != usuario_actual.usuario:
                usuario_existente = Usuario.query.filter_by(usuario=nuevo_usuario).first()
                if usuario_existente:
                    flash('El nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
                    return redirect(url_for('p_usuario'))
                else:
                    usuario_actual.usuario = nuevo_usuario
                    session['username'] = nuevo_usuario  # Actualizar sesión

            # Actualizar datos del usuario
            usuario_actual.nombre = nombre
            usuario_actual.apellido = apellido

            # Actualizar la contraseña si se proporciona
            if contrasena_nueva:
                usuario_actual.contraseña = encrypt_password(contrasena_nueva)

            try:
                # Guardar cambios en la base de datos
                db.session.commit()
                flash('Datos actualizados correctamente', 'success')
                return redirect(url_for('p_usuario'))
            except Exception as e:
                db.session.rollback()
                flash('Ocurrió un error al actualizar los datos', 'danger')
                print(e)

    # Generar URL de la imagen
    img_url = None
    if usuario_actual.img:
        img_url = f"data:image/jpeg;base64,{base64.b64encode(usuario_actual.img).decode('utf-8')}"
    if not img_url:
        img_url = url_for('static', filename='images/perfil.png')

    return render_template('p_usuario.html', usuario=usuario_actual, img_url=img_url)
    return redirect(url_for('login'))

########################### Funciones para calculos ################################

###############Actualiza calculos###############################
def recalcular_cotizacion_al_actualizar(mapper, connection, target):
    campos_relevantes = [
        'longitud', 'espesor', 'ancho', 'alto', 'diametro', 
        'v_final', 'n_cortes', 'vmm3', 'kg', 'tipo_perfil', 'Material'
    ]
    campos_cambiados = any(campo in target.__dict__ for campo in campos_relevantes)
    if campos_cambiados:
        print(f"Detectado cambio en cotización ID {target.idcotizacion}. Recalculando...")
        nombre_material = target.Material
        tipo_perfil = target.tipo_perfil
        print(f"Nombre del material: {nombre_material}, Tipo de perfil: {tipo_perfil}")
        
        producto = Producto.query.filter_by(tipo_perfil=tipo_perfil).first()  # No usamos get aquí porque no es clave primaria
        if not producto:
            print(f"No se encontró producto para '{tipo_perfil}'")
            return
        
        material = Material.query.filter_by(nombre=nombre_material, producto_id=producto.idproducto).first()
        if material:
            print(f"Material encontrado: {material.nombre}, ID: {material.idmaterial}")
            cotizar_perfil(target.idcotizacion, material.nombre)
        else:
            print(f"No se encontró material '{nombre_material}' para producto_id {producto.idproducto}")

event.listen(Cotizaciones, 'after_update', recalcular_cotizacion_al_actualizar)

# Función cotizar_perfil sin commit interno
def cotizar_perfil(cotizacion_id, nombre_material):
    # Usamos db.session.get() para Cotizaciones
    cotizacion = db.session.get(Cotizaciones, cotizacion_id)
    if not cotizacion:
        print(f"No se encontró cotización con ID {cotizacion_id}")
        return

    if getattr(cotizacion, '_recalculando', False):
        print(f"Cotización ID {cotizacion_id} ya está siendo recalculada. Evitando bucle.")
        return
    cotizacion._recalculando = True

    try:
        nombre_producto = cotizacion.tipo_perfil
        producto = Producto.query.filter_by(tipo_perfil=nombre_producto).first()
        if not producto:
            print(f"No se encontró producto con tipo_perfil '{nombre_producto}'")
            return

        tipo_calculo = producto.calculo.strip()
        print(f"Tipo de cálculo automático: '{tipo_calculo}'")

        mater = Material.query.filter_by(nombre=nombre_material, producto_id=producto.idproducto).first()
        if not mater:
            print(f"Material '{nombre_material}' no encontrado para el producto '{producto.tipo_perfil}'.")
            return

        material_id = mater.idmaterial
        # Si en otro lugar usas Material.query.get(material_id), aquí no es necesario, pero por si acaso:
        # mater = db.session.get(Material, material_id) ya lo tenemos con el filter_by anterior
        precio = Precio.query.filter_by(material_id=material_id).first()
        if not precio:
            print(f"No se encontró precio para el material ID {material_id}")
            return

        Br_Precio_Kg = precio.precio
        Preciokg = Br_Precio_Kg * (1 + Ajuste)

        if tipo_calculo == "Impresión 3D":
            Vmm3 = cotizacion.vmm3
            Kg = cotizacion.kg
            if Vmm3 is None or Kg is None:
                print("Error: vmm3 o kg son None")
                return
            Vcm3 = Vmm3 * 0.001 * Infill
            Dgcm3 = 1.1 * 1.05
            WKg = (Dgcm3 * Vcm3) * 0.1
            Import_e = round((Preciokg * WKg), 2)
            cotizacion.precio_mp = Import_e
            print(f"Calculado para 3D: precio_mp={Import_e}")
            return

        densidad = mater.densidad
        if densidad is None:
            print(f"El material '{nombre_material}' no tiene densidad definida.")
            return

        if mater.dmvc is None:
            print(f"El material '{nombre_material}' no tiene un valor definido para dmvc_index.")
            return
        dmvc_value = float(mater.dmvc)

        fabricaciones = Fabricacion.query.all()
        for fabricacion in fabricaciones:
            if fabricacion.tipo != "Convencional":
                continue

            Longitud = cotizacion.longitud
            Cortes = cotizacion.n_cortes
            VolF = cotizacion.v_final
            CantidadCM = float((Longitud + (Tolerancia * Cortes)) * Centimeter)
            Long = CantidadCM+material

            if tipo_calculo == "Cilindro":
                Diametro = cotizacion.diametro
                VolI = ((Pi / 4) * (Diametro ** 2) * (Long / Centimeter))
                Fab = ((VolF / VolI) - 1) * -100
                DiaMM = Diametro * 25.4
                LongMM = Long * 10
                Vmm3 = ((Pi / 4) * (DiaMM ** 2) * LongMM)
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = Fab / 100

            elif tipo_calculo == "Placa plana":
                Espesor = cotizacion.espesor
                Ancho = cotizacion.ancho
                VolI = ((Espesor * Ancho) * (Long / Centimeter))
                Fab = ((VolF / VolI) - 1) * -100
                EspMM = Espesor * 25.4
                AnchoMM = Ancho * 25.4
                LongMM = Long * 10
                Vmm3 = (EspMM * AnchoMM * LongMM)
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = (Fab * 0.5) / 100

            elif tipo_calculo == "Hexágono":
                Espesor = cotizacion.espesor
                Ancho = cotizacion.ancho
                VolI = ((Espesor * Ancho) * (Long / Centimeter))
                Fab = ((VolF / VolI) - 1) * -100
                EspMM = Espesor * 25.4
                AnchoMM = Ancho * 25.4
                LongMM = Long * 10
                Vmm3 = ((AnchoMM * 1.1547 * 0.5) ** 2) * 2.5981 * LongMM
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = Fab / 100

            elif tipo_calculo == "Ángulo (L)":
                Espesor = cotizacion.espesor
                Ancho = cotizacion.ancho
                VolI = ((Ancho ** 2) - ((Ancho - Espesor) ** 2)) * (Long / Centimeter)
                Fab = ((VolF / VolI) - 1) * -100
                EspMM = Espesor * 25.4
                AnchoMM = Ancho * 25.4
                LongMM = Long * 10
                Vmm3 = (((AnchoMM ** 2) - ((AnchoMM - EspMM) ** 2)) * LongMM) * 1.06
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = (Fab * 0.5) / 100

            elif tipo_calculo == "Tubo hueco":
                Espesor = cotizacion.espesor
                Diametro = cotizacion.diametro
                VolI = ((Long / Centimeter) * (Espesor * Pi) * (Diametro - Espesor))
                Fab = ((VolF / VolI) - 1) * -100
                EspMM = Espesor * 25.4
                DiaMM = Diametro * 25.4
                LongMM = Long * 10
                Vmm3 = (LongMM * EspMM * Pi * (DiaMM - EspMM))
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = Fab / 100

            elif tipo_calculo == "Canal":
                Espesor = cotizacion.espesor
                Ancho = cotizacion.ancho
                Alto = cotizacion.alto
                Longitud = cotizacion.longitud
                Cortes = cotizacion.n_cortes
                VolF = cotizacion.v_final

                if None in [Espesor, Ancho, Alto, Longitud, Cortes, VolF]:
                    print(f"Error: Valores None detectados en Canal")
                    return

                CantidadCM = round(((Longitud + (Tolerancia * Cortes)) * 2.54), 1)
                Long = CantidadCM
                VolI = ((Ancho * Alto) - ((Ancho - (2 * Espesor)) * (Alto - Espesor))) * Longitud
                Fab = ((VolF / VolI) - 1) * -100
                EspMM = Espesor * 25.4
                AncMM = Ancho * 25.4
                AltMM = Alto * 25.4
                LongMM = Long * 10
                Vmm3 = ((AncMM * AltMM) - ((AncMM - (2 * EspMM)) * (AltMM - EspMM))) * LongMM
                Vcm3 = Vmm3 * 0.001
                Fabric_factor = (Fab * 0.5) / 100

                print(f"VolI={VolI} in³, VolF={VolF} in³, Fab={Fab}, Fabric_factor={Fabric_factor}, Vcm3={Vcm3} cm³")

            else:
                print(f"Tipo de cálculo '{tipo_calculo}' no reconocido.")
                return

            WKg = (densidad * Vcm3) * 0.001
            Import_e = round((Preciokg * WKg), 2)
            Fabric = round((Vcm3 * dmvc_value * Fabric_factor), 2)

            convencional_precio = fabricacion.precio
            T_seg_conv = float(round((Fabric / (convencional_precio / 60) * 60), 2))
            T_min_conv = float(round((T_seg_conv / 60), 2))
            T_hr = float(round((T_min_conv / 60), 2))

            cotizacion.cantidad = CantidadCM
            cotizacion.long = Long
            cotizacion.fabricacion = Fab
            cotizacion.v_inicial = VolI
            cotizacion.precio_mp = Import_e
            cotizacion.cost_FAB = Fabric
            cotizacion.segundos = T_seg_conv
            cotizacion.minutos = T_min_conv
            cotizacion.horas = T_hr

            print("Cálculos completados, esperando commit externo")
            break

    except Exception as e:
        print(f"Error en cotizar_perfil: {e}")
        raise  # Propagamos la excepción para que el llamador la maneje
    finally:
        cotizacion._recalculando = False

@app.route('/agregar_c', methods=['POST'])
def agregar_c():
    data = request.get_json()
    print(f"Datos recibidos del frontend para agregar: {data}")

    # Crear una nueva cotización
    cotizacion = Cotizaciones()
    
    # Asignar los valores recibidos
    campos_relevantes = [
        'longitud', 'espesor', 'ancho', 'alto', 'diametro', 
        'v_final', 'n_cortes', 'vmm3', 'kg', 'tipo_perfil', 'Material'
    ]

    for field, value in data.items():
        if hasattr(cotizacion, field):
            print(f"Asignando {field} con valor {value}")
            if field in ['longitud', 'espesor', 'ancho', 'alto', 'diametro', 'v_final', 'vmm3', 'kg']:
                try:
                    setattr(cotizacion, field, float(value))
                except ValueError:
                    return jsonify({'error': f'Valor inválido para {field}: {value}'}), 400
            elif field == 'n_cortes':
                try:
                    setattr(cotizacion, field, int(value))
                except ValueError:
                    return jsonify({'error': f'Valor inválido para {field}: {value}'}), 400
            else:
                setattr(cotizacion, field, value)
        else:
            print(f"Campo ignorado: {field} no existe en Cotizaciones")

    # Agregar el objeto a la sesión
    db.session.add(cotizacion)

    # Commit inicial para obtener el ID
    try:
        db.session.commit()
        print(f"Cotización creada con ID {cotizacion.idcotizacion}")
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear cotización: {str(e)}'}), 500

    # Recalcular con cotizar_perfil
    nombre_material = cotizacion.Material
    if not nombre_material:
        db.session.rollback()
        return jsonify({'error': 'El campo Material es requerido para calcular'}), 400

    try:
        cotizar_perfil(cotizacion.idcotizacion, nombre_material)
        db.session.commit()  # Commit final para guardar los cálculos
        print(f"Estado final después de cotizar_perfil: {cotizacion.__dict__}")
        return jsonify({'message': 'Cotización agregada', 'id': cotizacion.idcotizacion}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al calcular cotización: {str(e)}'}), 500


##########################Ticket#################################
@app.route('/ticket')
def ticket():
    return render_template('ticket.html')


if __name__ == "__main__":
    # Cambia el host a '0.0.0.0' para que escuche en todas las interfaces
    app.run(host='0.0.0.0', port=5002, debug=True)