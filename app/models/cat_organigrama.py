from app import db

class CatOrganigrama(db.Model):
    __tablename__ = 'CAT_ORGANIGRAMA_2'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return f'<CatOrganigrama {self.nombre}>'
