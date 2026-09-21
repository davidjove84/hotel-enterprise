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

MENU_PLATILLOS = {
    "Arroz con Pato": 40.0,
    "Lomo Saltado": 35.0,
    "Ceviche Clásico": 38.0,
    "Ají de Gallina": 30.0,
    "Seco de Carne": 36.0,
    "Bebida / Gaseosa 500ml": 8.0,
}

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


# ===== Helper: datos del dashboard (evita duplicar la misma lógica) =====
def obtener_datos_dashboard():
    try:
        res_habs = supabase.table("habitaciones").select("*").order("numero").execute()
        habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        habitaciones = []
        flash("No se pudo cargar la lista de habitaciones.", "warning")

    for h in habitaciones:
        precio = h.get('precio', 0) if isinstance(h, dict) else 0
        h['precio_noche'] = precio  # alias usado por el template

    try:
        res_peds = supabase.table("pedidos").select("*, habitaciones(numero)").order("id", desc=True).execute()
        pedidos = res_peds.data if res_peds and res_peds.data else []
    except Exception:
        pedidos = []
        flash("No se pudo cargar la lista de pedidos.", "warning")

    total_habs = len(habitaciones)
    ocupadas = sum(1 for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    disponibles = total_habs - ocupadas
    porcentaje_ocupacion = int((ocupadas / total_habs * 100) if total_habs > 0 else 0)

    ingreso_habs = sum(
        float(h.get('precio', 0)) * int(h.get('noches', 0))
        for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada'
    )
    ingreso_pedidos = sum(float(p.get('precio', 0)) for p in pedidos if isinstance(p, dict))
    ingresos_totales = ingreso_habs + ingreso_pedidos

    return {
        "habitaciones": habitaciones,
        "pedidos": pedidos,
        "total_habs": total_habs,
        "ocupadas": ocupadas,
        "disponibles": disponibles,
        "porcentaje_ocupacion": porcentaje_ocupacion,
        "ingresos_totales": ingresos_totales,
        "ubicacion": UBICACION_HOTEL,
        "menu_platillos": MENU_PLATILLOS,
    }


# ===== Login / Logout =====
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


# ===== Dashboard principal =====
@app.route('/')
@login_required
def index():
    return render_template('index.html', **obtener_datos_dashboard())


@app.route('/habitaciones')
@login_required
def ver_habitaciones():
    return render_template('habitaciones.html', **obtener_datos_dashboard())


@app.route('/huespedes')
@login_required
def ver_huespedes():
    try:
        res_huespedes = supabase.table("huespedes").select("*").order("id", desc=True).execute()
        huespedes_historial = res_huespedes.data if res_huespedes and res_huespedes.data else []
    except Exception:
        huespedes_historial = []
        flash("No se pudo cargar el historial de huéspedes.", "warning")

    return render_template('huespedes.html', huespedes=huespedes_historial, ubicacion=UBICACION_HOTEL)


# ===== Acciones =====
@app.route('/agregar_habitacion', methods=['POST'])
@login_required
def agregar_habitacion():
    try:
        numero = request.form.get('numero', '').strip()
        tipo = request.form.get('tipo', '').strip()
        precio = float(request.form.get('precio', 0))

        if not numero or not tipo:
            flash("El número y el tipo de habitación son obligatorios.", "warning")
            return redirect(url_for('index'))

        if precio <= 0:
            flash("El precio debe ser mayor a cero.", "warning")
            return redirect(url_for('index'))

        existente = supabase.table("habitaciones").select("id").eq("numero", numero).execute()
        if existente.data:
            flash(f"Ya existe una habitación con el número {numero}.", "warning")
            return redirect(url_for('index'))

        supabase.table("habitaciones").insert({
            "numero": numero, "tipo": tipo, "precio": precio,
            "estado": "Disponible", "huesped": "", "noches": 0
        }).execute()
        flash(f"Habitación #{numero} registrada correctamente.", "success")
    except ValueError:
        flash("El precio ingresado no es válido.", "warning")
    except Exception:
        flash("No se pudo registrar la habitación. Intenta de nuevo.", "warning")
    return redirect(url_for('index'))


@app.route('/checkin/<int:hab_id>', methods=['POST'])
@login_required
def checkin(hab_id):
    try:
        huesped = request.form.get('huesped', '').strip().upper()
        documento = request.form.get('documento', 'S/D').strip() or 'S/D'
        metodo_pago = request.form.get('metodo_pago', '')
        noches = int(request.form.get('noches', 1))

        if not huesped:
            flash("El nombre del huésped es obligatorio.", "warning")
            return redirect(url_for('index'))
        if noches < 1:
            flash("La cantidad de noches debe ser al menos 1.", "warning")
            return redirect(url_for('index'))

        supabase.table("habitaciones").update({
            "estado": "Ocupada", "huesped": huesped, "documento": documento,
            "noches": noches, "metodo_pago": metodo_pago
        }).eq("id", hab_id).execute()

        res_hab = supabase.table("habitaciones").select("numero").eq("id", hab_id).execute()
        num_hab = res_hab.data[0]['numero'] if res_hab.data else ""

        supabase.table("huespedes").insert({
            "nombre": huesped, "documento": documento,
            "habitacion": num_hab, "noches": noches
        }).execute()
        flash(f"Check-in registrado para {huesped} en la habitación #{num_hab}.", "success")
    except ValueError:
        flash("La cantidad de noches no es válida.", "warning")
    except Exception:
        flash("No se pudo completar el check-in. Intenta de nuevo.", "warning")
    return redirect(url_for('index'))


@app.route('/checkout/<int:hab_id>', methods=['POST'])
@login_required
def checkout(hab_id):
    try:
        supabase.table("habitaciones").update({
            "estado": "Disponible", "huesped": "", "documento": "",
            "noches": 0, "metodo_pago": ""
        }).eq("id", hab_id).execute()
        flash("Check-out realizado. La habitación quedó disponible.", "success")
    except Exception:
        flash("No se pudo completar el check-out. Intenta de nuevo.", "warning")
    return redirect(url_for('index'))


@app.route('/pedir_comida', methods=['POST'])
@login_required
def pedir_comida():
    try:
        habitacion_num = request.form.get('habitacion_num', '').strip()
        platillo = request.form.get('platillo_nombre')

        if not habitacion_num:
            flash("Debes indicar el número de habitación.", "warning")
            return redirect(url_for('index'))

        res_hab = supabase.table("habitaciones").select("id").eq("numero", habitacion_num).execute()
        if not res_hab.data:
            flash(f"No existe la habitación #{habitacion_num}.", "warning")
            return redirect(url_for('index'))
        habitacion_id = res_hab.data[0]['id']

        precio = MENU_PLATILLOS.get(platillo, 25.0)
        supabase.table("pedidos").insert({
            "habitacion_id": habitacion_id,
            "descripcion": platillo,
            "platillo_nombre": platillo,
            "precio": precio,
            "estado": "En Preparación"
        }).execute()
        flash(f"Pedido de {platillo} enviado a cocina para la habitación #{habitacion_num}.", "success")
    except Exception as e:
        print("ERROR EN PEDIR_COMIDA:", e)
        flash("No se pudo enviar el pedido a cocina. Intenta de nuevo.", "warning")
    return redirect(url_for('index'))


@app.route('/cambiar_estado_pedido/<int:pedido_id>', methods=['POST'])
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
    return redirect(url_for('index'))


# ===== Reservas a futuro =====
@app.route('/reservas')
@login_required
def ver_reservas():
    try:
        res = supabase.table("reservas").select("*, habitaciones(numero, tipo)").order("fecha_inicio").execute()
        reservas = res.data if res and res.data else []
    except Exception:
        reservas = []
        flash("No se pudo cargar la lista de reservas.", "warning")

    try:
        res_habs = supabase.table("habitaciones").select("id, numero, tipo").order("numero").execute()
        habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        habitaciones = []

    return render_template('reservas.html', reservas=reservas, habitaciones=habitaciones, ubicacion=UBICACION_HOTEL)


@app.route('/crear_reserva', methods=['POST'])
@login_required
def crear_reserva():
    from datetime import datetime
    try:
        habitacion_id = int(request.form.get('habitacion_id'))
        huesped = request.form.get('huesped', '').strip().upper()
        documento = request.form.get('documento', '').strip()
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        if not huesped or not fecha_inicio or not fecha_fin:
            flash("Nombre del huésped y ambas fechas son obligatorias.", "warning")
            return redirect(url_for('ver_reservas'))

        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        if fin <= inicio:
            flash("La fecha de salida debe ser posterior a la fecha de llegada.", "warning")
            return redirect(url_for('ver_reservas'))

        if inicio < datetime.now().date():
            flash("No puedes reservar en una fecha que ya pasó.", "warning")
            return redirect(url_for('ver_reservas'))

        # Verifica que no se cruce con otra reserva confirmada de la misma habitación
        existentes = supabase.table("reservas") \
            .select("id, fecha_inicio, fecha_fin") \
            .eq("habitacion_id", habitacion_id) \
            .eq("estado", "Confirmada") \
            .execute()

        for r in (existentes.data or []):
            r_inicio = datetime.strptime(r['fecha_inicio'], '%Y-%m-%d').date()
            r_fin = datetime.strptime(r['fecha_fin'], '%Y-%m-%d').date()
            if inicio < r_fin and fin > r_inicio:
                flash(f"Esa habitación ya tiene una reserva entre {r['fecha_inicio']} y {r['fecha_fin']}.", "warning")
                return redirect(url_for('ver_reservas'))

        supabase.table("reservas").insert({
            "habitacion_id": habitacion_id,
            "huesped": huesped,
            "documento": documento,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "estado": "Confirmada"
        }).execute()
        flash(f"Reserva creada para {huesped} del {fecha_inicio} al {fecha_fin}.", "success")
    except ValueError:
        flash("Alguno de los datos ingresados no es válido.", "warning")
    except Exception:
        flash("No se pudo crear la reserva. Intenta de nuevo.", "warning")
    return redirect(url_for('ver_reservas'))


@app.route('/cancelar_reserva/<int:reserva_id>', methods=['POST'])
@login_required
def cancelar_reserva(reserva_id):
    try:
        supabase.table("reservas").update({"estado": "Cancelada"}).eq("id", reserva_id).execute()
        flash("Reserva cancelada correctamente.", "success")
    except Exception:
        flash("No se pudo cancelar la reserva.", "warning")
    return redirect(url_for('ver_reservas'))


if __name__ == '__main__':
    app.run(debug=True)
