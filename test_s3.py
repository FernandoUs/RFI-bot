from app.services.s3_service import test_s3_public_access

if __name__ == "__main__":
    print("Iniciando prueba de acceso público a S3...")
    result = test_s3_public_access()
    print(f"Resultado de la prueba: {'ÉXITO' if result else 'FALLÓ'}")