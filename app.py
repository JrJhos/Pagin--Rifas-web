import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_cambiala_por_algo_mas_seguro'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- BASE DE DATOS (SIMULADA CON ARCHIVOS JSON) ---
def load_data():
    if not os.path.exists('rifas.json'):
        with open('rifas.json', 'w') as f:
            json.dump([], f)
    if not os.path.exists('settings.json'):
        # Añadimos los nuevos campos para la configuración
        with open('settings.json', 'w') as f:
            json.dump({
                "whatsapp_number": "527779421271",
                "main_color": "#DC3545",
                "background_color": "#212529",
                "text_color": "#FFFFFF",
                "main_title": "$250,000 MXN",
                "raffle_date": "31 DE JULIO 2025",
                "ticket_price_info": "1 BOLETO POR $10\n2 BOLETOS POR $20",
                "logo_image": "",
                "logo_size": "80",
                "contact_info": "Escribe aquí la información de contacto.",
                "payment_methods_info": "Escribe aquí tus métodos de pago.",
                "tiktok_link": "",
                "instagram_link": ""
            }, f)

    with open('rifas.json', 'r', encoding='utf-8') as f:
        rifas = json.load(f)
    with open('settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)

    return rifas, settings

def save_data(rifas=None, settings=None):
    if rifas is not None:
        with open('rifas.json', 'w', encoding='utf-8') as f:
            json.dump(rifas, f, indent=4, ensure_ascii=False)
    if settings is not None:
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

# --- RUTAS PÚBLICAS (PARA USUARIOS) ---

@app.route('/')
def comprar_boletos():
    rifas, settings = load_data()
    active_raffle = next((r for r in rifas if r.get('is_active')), None)
    return render_template('comprar_boletos.html', raffle=active_raffle, settings=settings)

@app.route('/inicio')
def inicio():
    rifas, settings = load_data()
    # Ordenar rifas por ID descendente para mostrar las más recientes primero y tomar 6
    historial_rifas = sorted(rifas, key=lambda r: r['id'], reverse=True)[:6]
    return render_template('inicio.html', rifas=historial_rifas, settings=settings)

@app.route('/verificador', methods=['GET', 'POST'])
def verificador():
    rifas, settings = load_data()
    active_raffle = next((r for r in rifas if r.get('is_active')), None)
    
    ticket_details = None
    if request.method == 'POST' and active_raffle:
        phone_number = request.form['phone_number']
        found_tickets = []
        for ticket in active_raffle.get('tickets', []):
            if ticket.get('phone') == phone_number:
                found_tickets.append(ticket)
        ticket_details = found_tickets

    return render_template('verificador.html', raffle=active_raffle, settings=settings, ticket_details=ticket_details)

@app.route('/contacto')
def contacto():
    _, settings = load_data()
    return render_template('contacto.html', settings=settings)

@app.route('/metodos-de-pago')
def metodos_de_pago():
    _, settings = load_data()
    return render_template('metodos.html', settings=settings)

@app.route('/apartar', methods=['POST'])
def apartar_boletos():
    data = request.get_json()
    rifas, _ = load_data()
    
    active_raffle = next((r for r in rifas if r.get('is_active')), None)
    if not active_raffle:
        return {"success": False, "message": "No hay rifa activa."}

    # Verificar si el teléfono ya ha apartado boletos si la opción está activa
    if active_raffle.get('prevent_duplicates'):
        for ticket in active_raffle.get('tickets', []):
            if ticket.get('phone') == data['phone']:
                return {"success": False, "message": "Este número de teléfono ya ha apartado boletos para esta rifa."}

    for ticket_number in data['tickets']:
        for ticket in active_raffle.get('tickets', []):
            if ticket['number'] == ticket_number and ticket['status'] == 'disponible':
                ticket['status'] = 'apartado'
                ticket['name'] = data['name']
                ticket['lastname'] = data['lastname']
                ticket['phone'] = data['phone']
                ticket['paid'] = 'No' # Por defecto no está pagado
    
    save_data(rifas=rifas)
    return {"success": True}

# --- RUTAS DEL PANEL DE ADMINISTRACIÓN ---

@app.route('/admin', methods=['GET', 'POST'])
def login():
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin770533':
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    rifas, settings = load_data()
    active_raffle_tickets = []
    active_raffle = next((r for r in rifas if r.get('is_active')), None)
    if active_raffle:
        active_raffle_tickets = [t for t in active_raffle.get('tickets', []) if t['status'] != 'disponible']
    return render_template('admin/dashboard.html', rifas=rifas, settings=settings, active_raffle_tickets=active_raffle_tickets, active_raffle=active_raffle)

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/raffle/new', methods=['POST'])
def new_raffle():
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    
    title = request.form['title']
    ticket_count = int(request.form['ticket_count'])
    images = request.files.getlist('images')
    
    image_filenames = []
    for image in images:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filenames.append(filename)

    nueva_rifa = {
        "id": len(rifas) + 1,
        "title": title,
        "images": image_filenames, # Ahora es una lista de imágenes
        "is_active": False,
        "prevent_duplicates": False, # Nueva opción
        "tickets": [{"number": f"{i:0{len(str(ticket_count-1))}}", "status": "disponible"} for i in range(ticket_count)]
    }
    rifas.append(nueva_rifa)
    save_data(rifas=rifas)
    flash(f'Rifa "{title}" creada.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/settings/update', methods=['POST'])
def update_settings():
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    _, settings = load_data()
    
    settings['whatsapp_number'] = request.form['whatsapp_number']
    settings['main_color'] = request.form['main_color']
    settings['background_color'] = request.form['background_color']
    settings['text_color'] = request.form['text_color']
    settings['main_title'] = request.form['main_title']
    settings['raffle_date'] = request.form['raffle_date']
    settings['ticket_price_info'] = request.form['ticket_price_info']
    settings['contact_info'] = request.form['contact_info']
    settings['payment_methods_info'] = request.form['payment_methods_info']
    settings['tiktok_link'] = request.form['tiktok_link']
    settings['instagram_link'] = request.form['instagram_link']
    settings['logo_size'] = request.form['logo_size']

    logo = request.files['logo_image']
    if logo and allowed_file(logo.filename):
        filename = secure_filename(logo.filename)
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        settings['logo_image'] = filename

    save_data(settings=settings)
    flash('Configuración actualizada.', 'success')
    return redirect(url_for('dashboard'))

# Rutas para gestionar la rifa (activar, borrar, control de duplicados)
@app.route('/admin/raffle/activate/<int:raffle_id>')
def activate_raffle(raffle_id):
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    for rifa in rifas:
        rifa['is_active'] = (rifa['id'] == raffle_id)
    save_data(rifas=rifas)
    return redirect(url_for('dashboard'))

@app.route('/admin/raffle/delete/<int:raffle_id>')
def delete_raffle(raffle_id):
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    rifas = [r for r in rifas if r['id'] != raffle_id]
    save_data(rifas=rifas)
    flash('Rifa eliminada.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/raffle/toggle_duplicates/<int:raffle_id>')
def toggle_duplicates(raffle_id):
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    for rifa in rifas:
        if rifa['id'] == raffle_id:
            rifa['prevent_duplicates'] = not rifa.get('prevent_duplicates', False)
            break
    save_data(rifas=rifas)
    return redirect(url_for('dashboard'))

# Rutas para gestionar los boletos de la rifa activa
@app.route('/admin/ticket/update_payment/<int:raffle_id>/<ticket_number>')
def update_payment_status(raffle_id, ticket_number):
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    for rifa in rifas:
        if rifa['id'] == raffle_id:
            for ticket in rifa.get('tickets', []):
                if ticket['number'] == ticket_number:
                    ticket['paid'] = 'Sí' if ticket.get('paid', 'No') == 'No' else 'No'
                    break
            break
    save_data(rifas=rifas)
    return redirect(url_for('dashboard'))

@app.route('/admin/ticket/release/<int:raffle_id>/<ticket_number>')
def release_ticket(raffle_id, ticket_number):
    if 'admin_logged_in' not in session: return redirect(url_for('login'))
    rifas, _ = load_data()
    for rifa in rifas:
        if rifa['id'] == raffle_id:
            for ticket in rifa.get('tickets', []):
                if ticket['number'] == ticket_number:
                    ticket['status'] = 'disponible'
                    ticket.pop('name', None)
                    ticket.pop('lastname', None)
                    ticket.pop('phone', None)
                    ticket.pop('paid', None)
                    break
            break
    save_data(rifas=rifas)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)