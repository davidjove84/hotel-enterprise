from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

# Configuración de base de datos gratuita local
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_enterprise.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS ORM ---
class Habitacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    precio_noche = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(30), default='Disponible')

class Platillo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)

class PedidoComida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habitacion_num = db.Column(db.String(10), nullable=False)
    platillo_nombre = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(30), default='En Preparación')

# Inicializar base de datos
with app.app_context():
    db.create_all()

# --- RUTAS Y LÓGICA DE NEGOCIO ---
@app.route('/')
def index():
    habitaciones = Habitacion.query.all()
    platillos = Platillo.query.all()
    pedidos = PedidoComida.query.all()
    return render_template('index.html', habitaciones=habitaciones, platillos=platillos, pedidos=pedidos)

@app.route('/agregar_habitacion', methods=['POST'])
def agregar_habitacion():
    numero = request.form.get('numero')
    tipo = request.form.get('tipo')
    precio = float(request.form.get('precio'))
    
    nueva = Habitacion(numero=numero, tipo=tipo, precio_noche=precio)
    db.session.add(nueva)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/pedir_comida', methods=['POST'])
def pedir_comida():
    habitacion = request.form.get('habitacion_num')
    platillo = request.form.get('platillo_nombre')
    
    nuevo_pedido = PedidoComida(habitacion_num=habitacion, platillo_nombre=platillo)
    db.session.add(nuevo_pedido)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/cambiar_estado_pedido/<int:id>')
def cambiar_estado_pedido(id):
    pedido = PedidoComida.query.get_or_404(id)
    pedido.estado = 'Entregado' if pedido.estado == 'En Preparación' else 'En Preparación'
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)