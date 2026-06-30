from app import db
from datetime import datetime


class Bitacora(db.Model):
    __tablename__ = "bitacora"

    id = db.Column(db.Integer, primary_key=True)

    usuario = db.Column(db.String(100), nullable=False)

    accion = db.Column(db.String(100), nullable=False)

    modulo = db.Column(db.String(100), nullable=False)

    descripcion = db.Column(db.Text)

    ip = db.Column(db.String(50))

    navegador = db.Column(db.String(300))

    fecha = db.Column(db.DateTime, default=datetime.utcnow)