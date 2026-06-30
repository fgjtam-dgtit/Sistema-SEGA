import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from app.models.hipervinculo import Hipervinculo
from app.models.cat_organigrama import CatOrganigrama
from app import db
from app.controllers.utils import registrar_bitacora
import openpyxl
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename

hipervinculos_bp = Blueprint('hipervinculos', __name__)

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx',
    'xls', 'xlsx',
    'jpg', 'jpeg', 'png',
    'rar', 'zip'
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def requiere_admin():
    if not current_user.is_authenticated or not current_user.es_admin():
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return False
    return True


@hipervinculos_bp.route('/hipervinculos')
@login_required
def listar():

    busqueda = request.args.get('q', '').strip()

    if busqueda:
        registros = Hipervinculo.query.filter(
            (Hipervinculo.entidad.ilike(f'%{busqueda}%')) |
            (Hipervinculo.tipo_documento.ilike(f'%{busqueda}%')) |
            (Hipervinculo.observaciones.ilike(f'%{busqueda}%'))
        ).order_by(
            Hipervinculo.fecha_creacion.desc()
        ).all()

    else:
        registros = Hipervinculo.query.order_by(
            Hipervinculo.fecha_creacion.desc()
        ).all()

    return render_template(
        'hipervinculos/listar.html',
        registros=registros,
        busqueda=busqueda
    )


@hipervinculos_bp.route('/hipervinculos/crear', methods=['GET', 'POST'])
@login_required
def crear():

    if not requiere_admin():
        return redirect(url_for('hipervinculos.listar'))

    organigramas = CatOrganigrama.query.order_by(
        CatOrganigrama.codigo
    ).all()

    if request.method == 'POST':

        entidad = request.form.get('entidad')
        tipo_documento = request.form.get('tipo_documento')
        fecha = request.form.get('fecha')
        observaciones = request.form.get('observaciones')

        file = request.files.get('documento')

        url_pdf = None

        if file and file.filename != '':

            if allowed_file(file.filename):

                filename = secure_filename(file.filename)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                filename = f"{timestamp}_{filename}"

                filepath = os.path.join(
                    current_app.root_path,
                    'static',
                    'uploads',
                    filename
                )

                file.save(filepath)

                url_pdf = url_for(
                    'static',
                    filename=f'uploads/{filename}'
                )

            else:

                flash(
                    'Tipo de archivo no permitido. Extensiones válidas: pdf, doc, docx, xls, xlsx, jpg, png, rar, zip',
                    'danger'
                )

                return redirect(url_for('hipervinculos.crear'))

        nuevo = Hipervinculo(
            entidad=entidad,
            tipo_documento=tipo_documento,
            fecha=fecha,
            url_pdf=url_pdf,
            observaciones=observaciones,
            user_id=current_user.id
        )

        db.session.add(nuevo)
        db.session.commit()

        registrar_bitacora(
            accion='CREAR',
            modulo='Hipervínculos',
            descripcion=f'Se creó el registro de {entidad}'
        )

        flash('Registro guardado exitosamente!', 'success')

        return redirect(url_for('hipervinculos.listar'))

    return render_template(
        'hipervinculos/crear.html',
        organigramas=organigramas
    )


@hipervinculos_bp.route('/hipervinculos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):

    if not requiere_admin():
        return redirect(url_for('hipervinculos.listar'))

    registro = Hipervinculo.query.get_or_404(id)

    if request.method == 'POST':

        registro.entidad = request.form.get('entidad')
        registro.tipo_documento = request.form.get('tipo_documento')
        registro.fecha = request.form.get('fecha')
        registro.observaciones = request.form.get('observaciones')

        file = request.files.get('documento')

        if file and file.filename != '':

            if allowed_file(file.filename):

                if registro.url_pdf:

                    old_path = os.path.join(
                        current_app.root_path,
                        'static',
                        'uploads',
                        os.path.basename(registro.url_pdf)
                    )

                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(file.filename)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                filename = f"{timestamp}_{filename}"

                filepath = os.path.join(
                    current_app.root_path,
                    'static',
                    'uploads',
                    filename
                )

                file.save(filepath)

                registro.url_pdf = url_for(
                    'static',
                    filename=f'uploads/{filename}'
                )

            else:

                flash('Tipo de archivo no permitido', 'danger')

                return redirect(
                    url_for('hipervinculos.editar', id=id)
                )

        db.session.commit()

        registrar_bitacora(
            accion='EDITAR',
            modulo='Hipervínculos',
            descripcion=f'Se editó el registro {registro.id} de {registro.entidad}'
        )

        flash('Registro actualizado!', 'success')

        return redirect(url_for('hipervinculos.listar'))

    return render_template(
        'hipervinculos/editar.html',
        registro=registro
    )


@hipervinculos_bp.route('/hipervinculos/eliminar/<int:id>')
@login_required
def eliminar(id):

    if not requiere_admin():
        return redirect(url_for('hipervinculos.listar'))

    registro = Hipervinculo.query.get_or_404(id)

    if registro.url_pdf:

        filepath = os.path.join(
            current_app.root_path,
            'static',
            'uploads',
            os.path.basename(registro.url_pdf)
        )

        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(registro)
    db.session.commit()

    registrar_bitacora(
        accion='ELIMINAR',
        modulo='Hipervínculos',
        descripcion=f'Se eliminó el registro {registro.id} de {registro.entidad}'
    )

    flash('Registro eliminado!', 'success')

    return redirect(url_for('hipervinculos.listar'))


@hipervinculos_bp.route('/hipervinculos/exportar')
@login_required
def exportar():

    if not requiere_admin():
        return redirect(url_for('hipervinculos.listar'))

    registros = Hipervinculo.query.order_by(
        Hipervinculo.fecha_creacion.desc()
    ).all()

    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = "Hipervinculos"

    ws.append([
        "ENTIDAD",
        "TIPO DE DOCUMENTO",
        "FECHA",
        "HIPERVÍNCULO",
        "OBSERVACIONES"
    ])

    for r in registros:

        ws.append([
            r.entidad,
            r.tipo_documento,
            r.fecha,
            r.url_pdf or 'Sin archivo',
            r.observaciones
        ])

    output = BytesIO()

    wb.save(output)

    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"hipervinculos_{timestamp}.xlsx"
    )