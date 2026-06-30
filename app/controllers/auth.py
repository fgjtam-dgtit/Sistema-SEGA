from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from app.controllers.utils import registrar_bitacora

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            registrar_bitacora(
                accion='LOGIN',
                modulo='Autenticación',
                descripcion=f'El usuario {username} inició sesión'
            )
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    registrar_bitacora(
        accion='LOGOUT',
        modulo='Autenticación',
        descripcion=f'El usuario {current_user.username} cerró sesión'
    )
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('auth.register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        registrar_bitacora(
            accion='REGISTRO',
            modulo='Autenticación',
            descripcion=f'Se registró el usuario {username}'
        )
        flash('Registro exitoso! Ahora inicia sesión', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')