# herramientas-empresa/

Herramientas **internas**. Corren en la estacion de trabajo de la empresa o en el banco, y **nunca se
entregan al cliente**. Esa distincion no es organizativa: determina si una licencia copyleft genera
obligacion de distribucion. Ver el ADR de la linea divisoria en `docs/DECISIONES.md`.

| Directorio | Contenido |
|---|---|
| `generador/` | `generar.py`, que produce el paquete completo en `salida/<cliente>/` |
| `validador/` | `validar.py` y sus pruebas de regresion. Convierte las reglas inviolables en rechazos |
| `calculadoras/` | Almacenamiento, PoE y ancho de banda, con sus pruebas |
| `ansible/` | Roles y playbooks para aprovisionar el controlador |
| `runbooks/` | Procedimientos operativos, en espanol |
| `detectar_secretos.py` | Hook de pre-commit. Implementa ADR-005 |
| `verificar_todo.py` | Verificacion de extremo a extremo del repositorio |
