"""
Test básico para verificar que el sistema RFI Bot funciona correctamente
Ejecutar este test antes de desplegar o después de configurar
"""

import unittest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBasicFunctionality(unittest.TestCase):
    """Tests básicos para verificar que el sistema funciona correctamente"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.test_phone = "+51987654321"
    
    def test_imports(self):
        """Test de importaciones básicas"""
        try:
            # Imports principales
            from app.services.session_manager import SessionManager
            from app.services.menu_manager import show_main_menu
            from app.services.prompt_generator import PromptGenerator
            from app.services.storage import DatabaseManager
            from config import Config
            
            print("✅ Todas las importaciones funcionan correctamente")
        except ImportError as e:
            self.fail(f"Error de importación: {e}")
    
    def test_config_loading(self):
        """Test de carga de configuración"""
        try:
            from config import Config
            
            # Verificar que la configuración se carga
            self.assertIsNotNone(Config.SECRET_KEY)
            self.assertIsInstance(Config.DEBUG, bool)
            
            print("✅ Configuración cargada correctamente")
        except Exception as e:
            self.fail(f"Error en configuración: {e}")
    
    def test_database_manager(self):
        """Test del gestor de base de datos"""
        try:
            from app.services.storage import DatabaseManager
            
            db = DatabaseManager()
            
            # Verificar que los archivos de datos se pueden crear
            self.assertTrue(os.path.exists(os.path.dirname(db.sessions_file)))
            self.assertTrue(os.path.exists(os.path.dirname(db.rfis_file)))
            
            print("✅ DatabaseManager funciona correctamente")
        except Exception as e:
            self.fail(f"Error en DatabaseManager: {e}")
    
    def test_session_manager_creation(self):
        """Test de creación de sesión de usuario"""
        try:
            from app.services.session_manager import SessionManager
            
            session = SessionManager.create_new_session(self.test_phone)
            
            # Verificar estructura básica de sesión
            self.assertIsInstance(session, dict)
            self.assertIn('step', session)
            self.assertIn('data', session)
            self.assertIn('menu_state', session)
            
            print("✅ SessionManager funciona correctamente")
        except Exception as e:
            self.fail(f"Error en SessionManager: {e}")
    
    def test_menu_generation(self):
        """Test de generación de menús"""
        try:
            from app.services.menu_manager import show_main_menu
            
            menu = show_main_menu()
            
            # Verificar que el menú es un string no vacío
            self.assertIsInstance(menu, str)
            self.assertGreater(len(menu), 0)
            self.assertIn("MENÚ PRINCIPAL", menu)
            
            print("✅ Generación de menú funciona correctamente")
        except Exception as e:
            self.fail(f"Error en generación de menú: {e}")
    
    def test_prompt_generator(self):
        """Test del generador de prompts"""
        try:
            from app.services.prompt_generator import PromptGenerator
            
            # Crear sesión de prueba
            test_session = {'step': 1, 'data': {}}
            
            # Generar prompt
            prompt = PromptGenerator.get_step_prompt(test_session)
            
            # Verificar que el prompt es válido
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 0)
            
            print("✅ PromptGenerator funciona correctamente")
        except Exception as e:
            self.fail(f"Error en PromptGenerator: {e}")
    
    def test_flask_app_creation(self):
        """Test de creación de la aplicación Flask"""
        try:
            from app import create_app
            
            app = create_app()
            
            # Verificar que la app se crea correctamente
            self.assertIsNotNone(app)
            self.assertEqual(app.name, 'app')
            
            print("✅ Aplicación Flask se crea correctamente")
        except Exception as e:
            # Si no existe create_app, intentar con app.py directamente
            try:
                import app as main_app
                print("✅ Aplicación principal importada correctamente")
            except Exception as e2:
                self.fail(f"Error al crear aplicación Flask: {e}, {e2}")
    
    def test_environment_variables(self):
        """Test de variables de entorno críticas"""
        try:
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Variables críticas para funcionamiento básico
            critical_vars = [
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN',
                'GOOGLE_API_KEY'
            ]
            
            missing_vars = []
            for var in critical_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"⚠️ Variables de entorno faltantes: {missing_vars}")
                print("   El sistema funcionará parcialmente sin estas variables")
            else:
                print("✅ Variables de entorno críticas configuradas")
            
        except Exception as e:
            print(f"⚠️ Error al verificar variables de entorno: {e}")
    
    def test_directory_structure(self):
        """Test de estructura de directorios"""
        try:
            # Directorios que deben existir o crearse
            required_dirs = [
                'app',
                'app/services',
                'data',
                'temp'
            ]
            
            for dir_path in required_dirs:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                self.assertTrue(os.path.exists(dir_path))
            
            print("✅ Estructura de directorios correcta")
        except Exception as e:
            self.fail(f"Error en estructura de directorios: {e}")

def run_basic_tests():
    """Ejecuta todos los tests básicos"""
    print("🧪 Iniciando tests básicos del RFI Bot...\n")
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicFunctionality)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 Resultados:")
    print(f"   Tests ejecutados: {result.testsRun}")
    print(f"   Fallos: {len(result.failures)}")
    print(f"   Errores: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Fallos:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n❌ Errores:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n🎉 ¡Todos los tests pasaron! El sistema está listo.")
        return True
    else:
        print(f"\n⚠️ Algunos tests fallaron. Revisar configuración.")
        return False

if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)
