"""
Test básico de funcionalidad esencial del RFI Bot
Este archivo debe mantenerse en el repositorio para verificar la instalación
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.services.session_manager import SessionManager
    from app.services.menu_manager import show_main_menu
    from app.services.prompt_generator import PromptGenerator
    from config import Config
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("Asegúrate de que todas las dependencias estén instaladas")
    sys.exit(1)


class TestBasicFunctionality(unittest.TestCase):
    """Tests básicos para verificar que el sistema funciona correctamente"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.test_phone = "51999888777"
        
    def test_config_variables(self):
        """Verificar que las variables de configuración están definidas"""
        # Verificar que Config existe y tiene las propiedades necesarias
        self.assertTrue(hasattr(Config, 'TWILIO_ACCOUNT_SID'))
        self.assertTrue(hasattr(Config, 'TWILIO_AUTH_TOKEN'))
        self.assertTrue(hasattr(Config, 'AWS_ACCESS_KEY_ID'))
        self.assertTrue(hasattr(Config, 'AWS_S3_BUCKET'))
        
        print("✅ Variables de configuración verificadas")

    def test_session_manager_creation(self):
        """Test de creación de sesión de usuario"""
        try:
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
        """Test de generación de menú principal"""
        try:
            menu = show_main_menu()
            
            # Verificar que el menú contiene elementos esenciales
            self.assertIsInstance(menu, str)
            self.assertIn('RFI', menu)
            self.assertIn('1', menu)
            self.assertIn('2', menu)
            
            print("✅ Generación de menú funciona correctamente")
        except Exception as e:
            self.fail(f"Error en generación de menú: {e}")

    def test_prompt_generator(self):
        """Test de generación de prompts"""
        try:
            # Crear sesión de prueba
            session = {'step': 1, 'data': {}}
            
            prompt = PromptGenerator.get_step_prompt(session)
            
            # Verificar que se genera un prompt válido
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 10)
            
            print("✅ PromptGenerator funciona correctamente")
        except Exception as e:
            self.fail(f"Error en PromptGenerator: {e}")

    @patch('app.services.session_manager.DatabaseManager')
    def test_session_save_load(self, mock_db):
        """Test de guardado y carga de sesiones"""
        try:
            # Mock de la base de datos
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            
            # Crear sesión de prueba
            test_session = {
                'step': 1,
                'data': {'test': 'value'},
                'menu_state': 'main_menu'
            }
            
            # Simular guardado exitoso
            mock_db_instance.save_session.return_value = True
            
            # Test de guardado
            result = SessionManager.save_session(self.test_phone, test_session)
            
            # Verificar que se llamó al método de guardado
            mock_db_instance.save_session.assert_called_once()
            
            print("✅ Guardado y carga de sesiones funciona correctamente")
        except Exception as e:
            self.fail(f"Error en save/load de sesiones: {e}")

    def test_imports_and_dependencies(self):
        """Verificar que todas las dependencias críticas se pueden importar"""
        try:
            # Test de importaciones críticas
            import flask
            import twilio
            import boto3
            import reportlab
            
            print("✅ Todas las dependencias críticas están disponibles")
            print(f"   - Flask: {flask.__version__}")
            print(f"   - Twilio: {twilio.__version__}")
            print(f"   - Boto3: {boto3.__version__}")
            print(f"   - ReportLab: {reportlab.Version}")
            
        except ImportError as e:
            self.fail(f"Dependencia faltante: {e}")

    def test_directory_structure(self):
        """Verificar que la estructura de directorios es correcta"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Verificar directorios esenciales
        required_dirs = ['app', 'app/services']
        for dir_path in required_dirs:
            full_path = os.path.join(base_dir, dir_path)
            self.assertTrue(os.path.exists(full_path), f"Directorio faltante: {dir_path}")
        
        # Verificar archivos esenciales
        required_files = [
            'app.py',
            'config.py',
            'requirements.txt',
            'app/routes.py',
            'app/services/whatsapp_api.py',
            'app/services/session_manager.py'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(base_dir, file_path)
            self.assertTrue(os.path.exists(full_path), f"Archivo faltante: {file_path}")
        
        print("✅ Estructura de directorios verificada")


class TestSystemReadiness(unittest.TestCase):
    """Tests para verificar que el sistema está listo para producción"""

    def test_environment_variables(self):
        """Verificar configuración de variables de entorno"""
        # Verificar que .env.example existe
        env_example_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.example')
        self.assertTrue(os.path.exists(env_example_path), "Archivo .env.example faltante")
        
        print("✅ Configuración de entorno lista")

    def test_documentation_exists(self):
        """Verificar que existe documentación esencial"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        required_docs = [
            'README.md',
            'USER_GUIDE.md',
            'SETUP_GUIDE.md'
        ]
        
        for doc in required_docs:
            doc_path = os.path.join(base_dir, doc)
            self.assertTrue(os.path.exists(doc_path), f"Documentación faltante: {doc}")
        
        print("✅ Documentación completa")

    def test_gitignore_exists(self):
        """Verificar que .gitignore existe y contiene reglas esenciales"""
        gitignore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.gitignore')
        self.assertTrue(os.path.exists(gitignore_path), "Archivo .gitignore faltante")
        
        # Leer contenido de .gitignore
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        # Verificar reglas esenciales
        essential_rules = ['.env', '__pycache__/', '*.log', 'temp/']
        for rule in essential_rules:
            self.assertIn(rule, gitignore_content, f"Regla faltante en .gitignore: {rule}")
        
        print("✅ Archivo .gitignore configurado correctamente")


def run_installation_check():
    """Ejecutar verificación completa de instalación"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE INSTALACIÓN RFI BOT")
    print("="*60)
    
    # Ejecutar tests
    test_suite = unittest.TestSuite()
    
    # Agregar tests básicos
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBasicFunctionality))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSystemReadiness))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(test_suite)
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DE VERIFICACIÓN:")
    print(f"   Tests ejecutados: {result.testsRun}")
    print(f"   Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   Fallos: {len(result.failures)}")
    print(f"   Errores: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ FALLOS ENCONTRADOS:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n❌ ERRORES ENCONTRADOS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    # Resultado final
    if len(result.failures) == 0 and len(result.errors) == 0:
        print(f"\n🎉 ¡INSTALACIÓN VERIFICADA EXITOSAMENTE!")
        print(f"   El sistema RFI Bot está listo para usar")
        print(f"   Ejecuta 'python app.py' para iniciar el servidor")
        return True
    else:
        print(f"\n⚠️ SE ENCONTRARON PROBLEMAS EN LA INSTALACIÓN")
        print(f"   Revisa los errores arriba y verifica la configuración")
        print(f"   Consulta SETUP_GUIDE.md para más información")
        return False


if __name__ == '__main__':
    success = run_installation_check()
    sys.exit(0 if success else 1)
