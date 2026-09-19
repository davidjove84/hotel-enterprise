from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'clave_secreta_hotel_libertadores'

UBICACION_HOTEL = "Azángaro, Puno, Perú"

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

    try:
        if supabase:
            res_peds = supabase.table("pedidos").select("*").execute()
            pedidos = res_peds.data if res_peds and res_peds.data else []
    except Exception:
        pass

    total_habs = len(habitaciones)
    ocupadas = sum(1 for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    disponibles = total_habs - ocupadas
    porcentaje_ocupacion = int((ocupadas / total_habs * 100) if total_habs > 0 else 0)
    
    # Desglose de ingresos caja
    ingreso_habs = sum(float(h.get('precio', 0)) * int(h.get('noches', 1)) for h in habitaciones if isinstance(h, dict) and h.get('estado') == 'Ocupada')
    ingreso_pedidos = sum(float(p.get('precio', 0)) for p in pedidos if isinstance(p, dict))
    ingresos_totales = ingreso_habs + ingreso_pedidos

    return render_template('index.html', 
                           habitaciones=habitaciones, 
                           pedidos=pedidos,
                           total_habs=total_habs,
                           ocupadas=ocupadas,
                           disponibles=disponibles,
                           porcentaje_ocupacion=porcentaje_ocupacion,
                           ingreso_habs=ingreso_habs,
                           ingreso_pedidos=ingreso_pedidos,
                           ingresos_totales=ingresos_totales,
                           ubicacion=UBICACION_HOTEL)

@app.route('/habitaciones')
def ver_habitaciones():
    estado_filtro = request.args.get('estado', 'todos')
    habitaciones = []
    pedidos = []
    try:
        if supabase:
            query = supabase.table("habitaciones").select("*")
            if estado_filtro != 'todos':
                query = query.eq("estado", estado_filtro)
            res_habs = query.execute()
            habitaciones = res_habs.data if res_habs and res_habs.data else []
    except Exception:
        pass

    try:
        if supabase:
            res_peds = supabase.table("pedidos").select("*").execute()
            pedidos = res_peds.data if res_peds and res_peds.data else []
    except Exception:
        pass

    return render_template('habitaciones.html', 
                           habitaciones=habitaciones,
                           pedidos=pedidos,
                           filtro_actual=estado_filtro,
                           ubicacion=UBICACION_HOTEL)

@app.route('/huespedes')
def ver_huespedes():
    busqueda = request.args.get('q', '').strip().lower()
    huespedes_historial = []
    try:
        if supabase:
            res_huespedes = supabase.table("huespedes").select("*").execute()
            datos = res_huespedes.data if res_huespedes and res_huespedes.data else []
            if busqueda:
                huespedes_historial = [h for h in datos if busqueda in h.get('nombre', '').lower() or busqueda in h.get('documento', '').lower()]
            else:
                huespedes_historial = datos
    except Exception:
        pass
    
    return render_template('huespedes.html', huespedes=huespedes_historial, busqueda=busqueda, ubicacion=UBICACION_HOTEL)

@app.route('/agregar_habitacion', methods=['POST'])
def agregar_habitacion():
    try:
        if supabase:
            numero = request.form.get('numero', '').strip()
            tipo = request.form.get('tipo', '').strip()
            precio = float(request.form.get('precio', 0))
            # Validación de datos: Evitar precios negativos o campos vacíos
            if numero and tipo and precio > 0:
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
            huesped = request.form.get('huesped', '').strip().upper()
            documento = request.form.get('documento', '').strip()
            noches = int(request.form.get('noches', 1))
            
            # Validación de datos
            if huesped and documento and noches > 0:
                supabase.table("habitaciones").update({
                    "estado": "Ocupada", "huesped": huesped, "noches": noches
                }).eq("id", hab_id).execute()
                
                res_hab = supabase.table("habitaciones").select("numero").eq("id", hab_id).execute()
                num_hab = res_hab.data[0]['numero'] if res_hab.data else ""

                supabase.table("huespedes").insert({
                    "nombre": huesped, "documento": documento,
                    "habitacion": num_hab, "noches": noches
                }).execute()
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
            precios_menu = {"Arroz con Pato": 40.0, "Lomo Saltado": 35.0, "Ceviche Clásico": 38.0, "Ají de Gallina": 30.0, "Seco de Carne": 36.0, "Bebida / Gaseosa 500ml": 8.0}
            precio = precios_menu.get(platillo, 25.0)
            if habitacion_num and platillo:
                supabase.table("pedidos").insert({
                    "habitacion_num": habitacion_num, "platillo_nombre": platillo,
                    "precio": precio, "estado": "En Preparación"
                }).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

@app.route('/cambiar_estado_pedido/<int:pedido_id>')
def cambiar_estado_pedido(pedido_id):
    try:
        if supabase:
            res_ped = supabase.table("pedidos").select("estado").eq("id", pedido_id).execute()
            if res_ped.data:
                estado_actual = res_ped.data[0]['estado']
                nuevo_estado = 'Entregado' if estado_actual == 'En Preparación' else 'En Preparación'
                supabase.table("pedidos").update({"estado": nuevo_estado}).eq("id", pedido_id).execute()
    except Exception:
        pass
    return redirect(url_for('ver_habitaciones'))

if __name__ == '__main__':
    app.run(debug=True)
