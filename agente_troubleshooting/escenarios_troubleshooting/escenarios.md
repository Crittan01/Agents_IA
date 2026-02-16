# ESCENARIOS DE TROUBLESHOOTING PARA PRUEBAS

## ESCENARIO 1: Aplicación Lenta (Oracle)

**Síntoma inicial:**
"Los usuarios reportan que la aplicación está muy lenta desde hace 1 hora"

**Respuestas esperadas del operador:**
- Lentitud generalizada en todas las funcionalidades
- CPU al 35%, Memoria al 50%
- Hay 250 sesiones activas en Oracle (normal es 150)
- Tablespaces con espacio disponible
- Último cambio: Deploy de nueva versión hace 2 horas

**Root Cause Esperado:**
Query nueva sin índice optimizado generando full table scans

**Playbook Sugerido:**
oracle_stats_gather.yml o consultar con DBA para agregar índice

---

## ESCENARIO 2: Disco Lleno

**Síntoma inicial:**
"El servidor PRODWEB01 está dando error 'No space left on device'"

**Respuestas esperadas:**
- Partición /var al 100%
- df -h muestra 0 bytes disponibles
- Logs en /var/log ocupan 45GB
- Archivelogs de Oracle en /var/oracle/archive ocupan 120GB

**Root Cause Esperado:**
Archivelogs no se están eliminando automáticamente

**Playbook Sugerido:**
oracle_archivelog_cleanup.yml con retention de 7 días

---

## ESCENARIO 3: WebLogic OutOfMemory

**Síntoma inicial:**
"WebLogic AdminServer se cayó con OutOfMemoryError"

**Respuestas esperadas:**
- Heap configurado: -Xmx2048m
- Logs muestran: java.lang.OutOfMemoryError: Java heap space
- Problema empezó después de campaña masiva de emails (carga alta)
- Thread dump muestra 300+ threads activos

**Root Cause Esperado:**
Heap insuficiente para carga actual

**Playbook Sugerido:**
weblogic_heap_increase.yml aumentando a -Xmx4096m

---

## ESCENARIO 4: Error de Conexión BD

**Síntoma inicial:**
"La aplicación no puede conectarse a la base de datos Oracle"

**Respuestas esperadas:**
- Error: ORA-12170: TNS:Connect timeout occurred
- Ping al servidor BD: OK
- Telnet al puerto 1521: Connection refused
- Listener status: No response

**Root Cause Esperado:**
Listener de Oracle caído

**Playbook Sugerido:**
oracle_health_check.yml seguido de reinicio manual de listener

---

## ESCENARIO 5: Sesiones Colgadas SQL Server

**Síntoma inicial:**
"Los usuarios no pueden ejecutar reportes, la aplicación se queda esperando"

**Respuestas esperadas:**
- SQL Server con 15 sesiones bloqueadas (BLOCKING)
- Session ID 52 está bloqueando a todas las demás
- Query: UPDATE masivo sin commit desde hace 3 horas
- Log de transacciones creciendo rápidamente

**Root Cause Esperado:**
Transacción larga sin commit bloqueando tablas

**Playbook Sugerido:**
sqlserver_kill_session.yml para terminar session 52