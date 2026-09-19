from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'clave_secreta_hotel_libertadores'

UBICACION_HOTEL = "Azángaro, Puno, Perú"

# Importación protegida para evitar errores de arranque en Vercel
try:
    from supabase import create_client
    url = "https://pmtvgmgreymgybqdaxrm.supabase.co"
    key = "sb_publishable_5_O8LP_cVMecHLjdZd6fHQ_HGR5Kk79"
    supabase = create_client(url, key)
except Exception:
    supabase = None

@app.route('/')
def index():
    habitaciones = []
    pedidos = []
    try:
        if supabase:
            res_habs = supabase.table("habitaciones").select("*").execute()
            habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        pass

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
                           ingreso_habs=ingreso_habs,
                           ingreso_pedidos=ingreso_pedidos,
                           tipos_conteo={},
                           ubicacion=UBICACION_HOTEL)

@app.route('/habitaciones')
def ver_habitaciones():
    habitaciones = []
    pedidos = []
    try:
        if supabase:
            res_habs = supabase.table("habitaciones").select("*").execute()
            habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        pass

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
def ver_huespedes():
    huespedes_historial = []
    try:
        if supabase:
            res_huespedes = supabase.table("huespedes").select("*").execute()
            huespedes_historial = res_huespedes.data if res_huespedes and res_huespedes.data else []
    except Exception:
        pass
    return render_template('huespedes.html', huespedes=huespedes_historial, ubicacion=UBICACION_HOTEL)

@app.route('/agregar_habitacion', methods=['POST'])
def agregar_habitacion():
    try:
        if supabase:
            numero = request.form.get('numero')
            tipo = request.form.get('tipo')
            precio = float(request.form.get('precio', 0))
            supabase.table("habitaciones").insert({
                "numero": numero, "tipo": tipo, "precio": precio,
                "estado": "Disponible", "huesped": "", "noches": 0
            }).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

@app.route('/checkin/<int:hab_id>', methods=['POST'])
def checkin(hab_id):
    try:
        if supabase:
            huesped = request.form.get('huesped', '').upper()
            documento = request.form.get('documento', 'S/D')
            noches = int(request.form.get('noches', 1))
            supabase.table("habitaciones").update({
                "estado": "Ocupada", "huesped": huesped, "noches": noches
            }).eq("id", hab_id).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

@app.route('/checkout/<int:hab_id>')
def checkout(hab_id):
    try:
        if supabase:
            supabase.table("habitaciones").update({
                "estado": "Disponible", "huesped": "", "noches": 0
            }).eq("id", hab_id).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

@app.route('/pedir_comida', methods=['POST'])
def pedir_comida():
    try:
        if supabase:
            habitacion_num = request.form.get('habitacion_num')
            platillo = request.form.get('platillo_nombre')
            supabase.table("pedidos").insert({
                "habitacion_num": habitacion_num, "platillo_nombre": platillo,
                "precio": 35.0, "estado": "En Preparación"
            }).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

@app.route('/cambiar_estado_pedido/<int:pedido_id>')
def cambiar_estado_pedido(pedido_id):
    try:
        if supabase:
            supabase.table("pedidos").update({"estado": "Entregado"}).eq("id", pedido_id).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

if __name__ == '__main__':
    app.run(debug=True)
