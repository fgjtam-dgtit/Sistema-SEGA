from flask import request
from flask_login import current_user
from app import db
from app.models.bitacora import Bitacora


def registrar_bitacora(accion, modulo, descripcion):
    try:

        if current_user.is_authenticated:
            usuario = current_user.username
        else:
            usuario = "No autenticado"

        ip = request.remote_addr

        navegador = request.headers.get("User-Agent")

        bit = Bitacora(
            usuario=usuario,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip=ip,
            navegador=navegador
        )

        db.session.add(bit)
        db.session.commit()

    except Exception as e:
        print("Error al registrar bitácora:", e)