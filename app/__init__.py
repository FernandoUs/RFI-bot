from flask import Flask

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Configurar la aplicación
    if config_class:
        app.config.from_object(config_class)
    
    # Registrar rutas
    from app.routes import configure_routes
    configure_routes(app)
    
    return app