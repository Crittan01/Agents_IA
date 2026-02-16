# knowledge_base.py
# Base de conocimiento de troubleshooting para operaciones TI

PLAYBOOKS_DISPONIBLES = {
    "oracle": {
        "oracle_health_check.yml": "Diagnóstico completo de Oracle Database",
        "oracle_archivelog_cleanup.yml": "Limpieza de archivelogs",
        "oracle_tablespace_extend.yml": "Extensión de tablespaces",
        "oracle_temp_cleanup.yml": "Limpieza de tablespace TEMP",
        "oracle_session_kill.yml": "Terminación de sesiones colgadas",
        "oracle_stats_gather.yml": "Recolección de estadísticas",
        "oracle_asm_rebalance.yml": "Rebalanceo de ASM diskgroups"
    },
    "weblogic": {
        "weblogic_health_check.yml": "Diagnóstico de WebLogic Server",
        "weblogic_restart.yml": "Reinicio controlado de WebLogic",
        "weblogic_heap_increase.yml": "Incrementar memoria heap",
        "weblogic_thread_dump.yml": "Generar thread dump para análisis",
        "weblogic_clear_cache.yml": "Limpiar cache y tmp",
        "weblogic_datasource_test.yml": "Probar datasources JDBC"
    },
    "linux": {
        "disk_cleanup.yml": "Limpieza de espacio en disco",
        "service_restart.yml": "Reinicio de servicios systemd",
        "process_kill.yml": "Terminación de procesos zombies",
        "network_diagnostics.yml": "Diagnóstico de red",
        "performance_analysis.yml": "Análisis de performance (CPU/MEM/IO)"
    },
    "sql_server": {
        "sqlserver_health_check.yml": "Diagnóstico SQL Server",
        "sqlserver_index_rebuild.yml": "Rebuild de índices fragmentados",
        "sqlserver_update_stats.yml": "Actualización de estadísticas",
        "sqlserver_shrink_log.yml": "Reducir transaction log",
        "sqlserver_kill_session.yml": "Terminar sesiones bloqueadas"
    },
    "postgresql": {
        "postgres_health_check.yml": "Diagnóstico PostgreSQL",
        "postgres_vacuum.yml": "Vacuum y analyze",
        "postgres_replication_check.yml": "Verificar replicación",
        "postgres_connection_reset.yml": "Reset de conexiones"
    }
}

ARBOL_DIAGNOSTICO = {
    "aplicacion_lenta": {
        "pregunta_inicial": "¿La lentitud es generalizada o solo en funcionalidades específicas?",
        "opciones": {
            "generalizada": {
                "siguiente_pregunta": "¿Revisaste el uso de recursos en el servidor (CPU, memoria, disco)?",
                "causas_probables": [
                    "Servidor con recursos saturados",
                    "Problema de red",
                    "Base de datos sobrecargada"
                ],
                "playbooks_sugeridos": ["performance_analysis.yml", "oracle_health_check.yml"]
            },
            "especifica": {
                "siguiente_pregunta": "¿Qué funcionalidad específica está lenta?",
                "causas_probables": [
                    "Query específica sin optimizar",
                    "Índice faltante o fragmentado",
                    "Estadísticas desactualizadas"
                ],
                "playbooks_sugeridos": ["oracle_stats_gather.yml", "sqlserver_index_rebuild.yml"]
            }
        }
    },
    "error_conexion_bd": {
        "pregunta_inicial": "¿Qué mensaje de error específico aparece?",
        "causas_comunes": [
            "ORA-12170: TNS connect timeout",
            "ORA-01017: Invalid username/password",
            "ORA-28000: Account locked",
            "Cannot connect to SQL Server"
        ],
        "siguiente_pregunta": "¿Puedes conectarte desde el servidor de base de datos localmente?",
        "playbooks_sugeridos": ["oracle_health_check.yml", "network_diagnostics.yml"]
    },
    "disco_lleno": {
        "pregunta_inicial": "¿Qué partición o filesystem está lleno?",
        "siguiente_pregunta": "¿Identificaste qué está consumiendo el espacio?",
        "acciones": [
            "Revisar logs antiguos",
            "Verificar archivelogs de Oracle",
            "Revisar archivos temporales",
            "Validar backups antiguos"
        ],
        "playbooks_sugeridos": ["disk_cleanup.yml", "oracle_archivelog_cleanup.yml"]
    },
    "servicio_caido": {
        "pregunta_inicial": "¿Qué servicio está caído específicamente?",
        "siguiente_pregunta": "¿Revisaste los logs del servicio?",
        "playbooks_sugeridos": ["service_restart.yml", "weblogic_restart.yml"]
    },
    "outofmemory": {
        "pregunta_inicial": "¿En qué componente ocurre el OutOfMemory? (WebLogic, JVM, BD)",
        "siguiente_pregunta": "¿Cuál es el uso actual de memoria y el máximo configurado?",
        "causas_probables": [
            "Memory leak en aplicación",
            "Heap size insuficiente",
            "Demasiadas sesiones concurrentes"
        ],
        "playbooks_sugeridos": ["weblogic_heap_increase.yml", "weblogic_thread_dump.yml"]
    }
}

PREGUNTAS_DIAGNOSTICO = {
    "recursos_servidor": [
        "¿Cuál es el uso actual de CPU? (comando: top o htop)",
        "¿Cuál es el uso de memoria? (comando: free -h)",
        "¿Hay espacio en disco? (comando: df -h)",
        "¿Hay procesos zombies o consumiendo recursos anormales?"
    ],
    "base_datos": [
        "¿Cuántas sesiones activas hay en la BD?",
        "¿Hay queries de larga duración ejecutándose?",
        "¿Los tablespaces tienen espacio disponible?",
        "¿Las estadísticas están actualizadas?",
        "¿Cuándo fue el último backup exitoso?"
    ],
    "aplicacion": [
        "¿Desde cuándo empezó el problema?",
        "¿Hubo algún cambio reciente? (deploy, configuración, parches)",
        "¿Cuántos usuarios están afectados? (todos o algunos)",
        "¿El problema es intermitente o constante?",
        "¿Revisaste los logs de la aplicación?"
    ],
    "red": [
        "¿Puedes hacer ping al servidor?",
        "¿El puerto está abierto? (telnet o nc)",
        "¿El firewall está bloqueando conexiones?",
        "¿Los DNS resuelven correctamente?"
    ]
}

COMANDOS_UTILES = {
    "oracle": {
        "sesiones_activas": "SELECT count(*) FROM v$session WHERE status='ACTIVE';",
        "tablespaces": "SELECT tablespace_name, round(sum(bytes)/1024/1024/1024,2) GB FROM dba_data_files GROUP BY tablespace_name;",
        "queries_lentas": "SELECT sql_id, elapsed_time/1000000 seconds FROM v$sql WHERE elapsed_time > 10000000 ORDER BY elapsed_time DESC;",
        "archivelog_space": "SELECT destination, round(space_used/1024/1024/1024,2) GB_USED FROM v$recovery_file_dest;"
    },
    "linux": {
        "disco_uso": "df -h",
        "procesos_top": "ps aux --sort=-%mem | head -10",
        "archivos_grandes": "find /var/log -type f -size +100M -exec ls -lh {} \\;",
        "conexiones_red": "netstat -tuln | grep LISTEN"
    },
    "weblogic": {
        "heap_usage": "java -jar wlst.jar -c 'connect(); serverRuntime(); print(cmo.getJVMRuntime().getHeapSizeCurrent())'",
        "threads": "cat $DOMAIN_HOME/servers/*/logs/*.out | grep 'ExecuteThread'",
        "datasources": "Verificar en consola AdminServer: /console"
    }
}