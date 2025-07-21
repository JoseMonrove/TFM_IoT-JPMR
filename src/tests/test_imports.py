# tests/test_imports.py
"""
Verifica que los tres paquetes principales se puedan importar.
Si este test falla
  → hay un problema de rutas o __init__.py ausente.
"""
def test_imports():
    import sensors.manager
    import control.ventilador
    import gui.scada
