import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'clave_secreta_hotel_libertadores'

UBICACION_HOTEL = "Azángaro, Puno, Perú"

url: str = "https://pmtvgmgreymgybqdaxrm.supabase.co"
key: str = "sb_publishable_5_O8LP_cVMecHLjdZd6fHQ_HGR5Kk79"
supabase: Client = create_client(url, key)

# ===== Configuración de Login =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Debes iniciar sesión para acceder a esta página."
login_manager.login_message_category = "warning"


class Usuario(UserMixin):
    def __init__(self, id, email, nombre, rol):
        self.id = id
        self.email = email
        self.nombre = nombre
        self.rol = rol


@login_manager.user_loader
def load_user(user_id):
    try:
        res = supabase.table("usuarios").select("*").eq("id", user_id).execute()
        if res.data:
            u = res.data[0]
            return Usuario(u['id'], u['email'], u['nombre'], u['rol'])
    except Exception:
        pass
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            res = supabase.table("usuarios").select("*").eq("email", email).execute()
            usuario_data = res.data[0] if res.data else None
        except Exception:
            usuario_data = None

        if usuario_data and check_password_hash(usuario_data['password_hash'], password):
            usuario = Usuario(
                usuario_data['id'], usuario_data['email'],
                usuario_data['nombre'], usuario_data['rol']
            )
            login_user(usuario)
            flash(f"Bienvenido, {usuario.nombre}.", "success")
            siguiente = request.args.get('next')
            return redirect(siguiente or url_for('index'))
        else:
            flash("Email o contraseña incorrectos.", "warning")

    return render_template('login.html', ubicacion=UBICACION_HOTEL)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        res_habs = supabase.table("habitaciones").select("*").execute()
        habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        habitaciones = []
        flash("No se pudo cargar la lista de habitaciones.", "warning")

    for h in habitaciones:
        p = h.get('precio', 0) if isinstance(h, dict) else 0
        h['precio'] = p
        h['precio_noche'] = p

    try:
        res_peds = supabase.table("pedidos").select("*").execute()
        pedidos = res_peds.data if res_peds and res_peds.data else []
    except Exception:
        pedidos = []
        flash("No se pudo cargar la lista de pedidos.", "warning")

    total_habs = len(habitaciones)
    ocupadas = sum(1 for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    disponibles = total_habs - ocupadas
    porcentaje_ocupacion = int((ocupadas / total_habs * 100) if total_habs > 0 else 0)
    
    ingreso_habs = sum(float(h.get('precio', 0)) * int(h.get('noches', 0)) for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    ingreso_pedidos = sum(float(p.get('precio', 0)) for p in pedidos if isinstance(p, dict))
    ingresos_totales = ingreso_habs + ingreso_pedidos

    return render_template('index.html', 
                           habitaciones=habitaciones, 
                           pedidos=pedidos,
                           total_habs=total_habs,
                           ocupadas=ocupadas,
                           disponibles=disponibles,
                           porcentaje_ocupacion=porcentaje_ocupacion,
                           ingresos_totales=ingresos_totales,
                           ubicacion=UBICACION_HOTEL)

@app.route('/habitaciones')
@login_required
def ver_habitaciones():
    try:
        res_habs = supabase.table("habitaciones").select("*").execute()
        habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        habitaciones = []
        flash("No se pudo cargar la lista de habitaciones.", "warning")

    for h in habitaciones:
        p = h.get('precio', 0) if isinstance(h, dict) else 0
        h['precio'] = p
        h['precio_noche'] = p

    try:
        res_peds = supabase.table("pedidos").select("*").execute()
        pedidos = res_peds.data if res_peds and res_peds.data else []
    except Exception:
        pedidos = []
        flash("No se pudo cargar la lista de pedidos.", "warning")

    total_habs = len(habitaciones)
    ocupadas = sum(1 for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    disponibles = total_habs - ocupadas
    porcentaje_ocupacion = int((ocupadas / total_habs * 100) if total_habs > 0 else 0)
    
    ingreso_habs = sum(float(h.get('precio', 0)) * int(h.get('noches', 0)) for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    ingreso_pedidos = sum(float(p.get('precio', 0)) for p in pedidos if isinstance(p, dict))
    ingresos_totales = ingreso_habs + ingreso_pedidos

    return render_template('habitaciones.html', 
                           habitaciones=habitaciones,
                           pedidos=pedidos,
                           total_habs=total_habs,
                           ocupadas=ocupadas,
                           disponibles=disponibles,
                           porcentaje_ocupacion=porcentaje_ocupacion,
                           ingresos_totales=ingresos_totales,
                           ubicacion=UBICACION_HOTEL)

@app.route('/huespedes')
@login_required
def ver_huespedes():
    try:
        res_huespedes = supabase.table("huespedes").select("*").execute()
        huespedes_historial = res_huespedes.data if res_huespedes and res_huespedes.data else []
    except Exception:
        huespedes_historial = []
        flash("No se pudo cargar el historial de huéspedes.", "warning")
    
    return render_template('huespedes.html', huespedes=huespedes_historial, ubicacion=UBICACION_HOTEL)

@app.route('/agregar_habitacion', methods=['POST'])
@login_required
def agregar_habitacion():
    try:
        numero = request.form.get('numero')
        tipo = request.form.get('tipo')
        precio = float(request.form.get('precio', 0))
        supabase.table("habitaciones").insert({
            "numero": numero, "tipo": tipo, "precio": precio,
            "estado": "Disponible", "huesped": "", "noches": 0
        }).execute()
        flash(f"Habitación #{numero} registrada correctamente.", "success")
    except Exception:
        flash("No se pudo registrar la habitación. Verifica los datos e intenta de nuevo.", "warning")
    return redirect(url_for('ver_habitaciones'))

@app.route('/checkin/<int:hab_id>', methods=['POST'])
@login_required
def checkin(hab_id):
    try:
        huesped = request.form.get('huesped', '').upper()
        documento = request.form.get('documento', 'S/D')
        noches = int(request.form.get('noches', 1))
        supabase.table("habitaciones").update({
            "estado": "Ocupada", "huesped": huesped, "noches": noches
        }).eq("id", hab_id).execute()
        
        res_hab = supabase.table("habitaciones").select("numero").eq("id", hab_id).execute()
        num_hab = res_hab.data[0]['numero'] if res_hab.data else ""

        supabase.table("huespedes").insert({
            "nombre": huesped, "documento": documento,
            "habitacion": num_hab, "noches": noches
        }).execute()
        flash(f"Check-in registrado para {huesped} en la habitación #{num_hab}.", "success")
    except Exception:
        flash("No se pudo completar el check-in. Verifica los datos e intenta de nuevo.", "warning")
    return redirect(url_for('ver_habitaciones'))

@app.route('/checkout/<int:hab_id>')
@login_required
def checkout(hab_id):
    try:
        supabase.table("habitaciones").update({
            "estado": "Disponible", "huesped": "", "noches": 0
        }).eq("id", hab_id).execute()
        flash("Check-out realizado. La habitación quedó disponible.", "success")
    except Exception:
        flash("No se pudo completar el check-out. Intenta de nuevo.", "warning")
    return redirect(url_for('ver_habitaciones'))

@app.route('/pedir_comida', methods=['POST'])
@login_required
def pedir_comida():
    try:
        habitacion_num = request.form.get('habitacion_num')
        platillo = request.form.get('platillo_nombre')
        precios_menu = {"Arroz con Pato": 40.0, "Lomo Saltado": 35.0, "Ceviche Clásico": 38.0, "Ají de Gallina": 30.0, "Seco de Carne": 36.0, "Bebida / Gaseosa 500ml": 8.0}
        precio = precios_menu.get(platillo, 25.0)
        supabase.table("pedidos").insert({
            "habitacion_num": habitacion_num, "platillo_nombre": platillo,
            "precio": precio, "estado": "En Preparación"
        }).execute()
        flash(f"Pedido de {platillo} enviado a cocina para la habitación #{habitacion_num}.", "success")
    except Exception:
        flash("No se pudo enviar el pedido a cocina. Intenta de nuevo.", "warning")
    return redirect(url_for('ver_habitaciones'))

@app.route('/cambiar_estado_pedido/<int:pedido_id>')
@login_required
def cambiar_estado_pedido(pedido_id):
    try:
        res_ped = supabase.table("pedidos").select("estado").eq("id", pedido_id).execute()
        if res_ped.data:
            estado_actual = res_ped.data[0]['estado']
            nuevo_estado = 'Entregado' if estado_actual == 'En Preparación' else 'En Preparación'
            supabase.table("pedidos").update({"estado": nuevo_estado}).eq("id", pedido_id).execute()
            flash(f"Pedido actualizado a estado: {nuevo_estado}.", "success")
        else:
            flash("No se encontró el pedido indicado.", "warning")
    except Exception:
        flash("No se pudo actualizar el estado del pedido.", "warning")
    return redirect(url_for('ver_habitaciones'))

if __name__ == '__main__':
    app.run(debug=True)
