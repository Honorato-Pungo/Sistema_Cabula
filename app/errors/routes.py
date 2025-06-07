from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)

@errors.route('/limite_excedido')
def limite_excedido():
    return render_template('errors/limite_excedido.html')
