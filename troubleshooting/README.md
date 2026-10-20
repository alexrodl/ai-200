# Troubleshooting

## Antes de investigar

Registra el módulo, el paso del ejercicio y el mensaje de error. No incluyas claves, tokens, cadenas de conexión, payloads sensibles ni datos personales en capturas o mensajes compartidos.

## Problemas frecuentes

### El recurso no se puede crear

Comprueba:

- Que tenant, suscripción y Resource Group sean los correctos.
- Que el servicio esté disponible en la región y haya cuota.
- Que el nombre y las propiedades cumplan las restricciones del servicio.
- Que los permisos de control, políticas y roles de datos permitan la operación.

### Error de autenticación

Comprueba:

- La identidad seleccionada (usuario o Managed Identity) y su tenant.
- Que la sesión/token siga vigente y la CLI utilice la suscripción esperada.
- Que la identidad tenga el rol requerido en el scope correcto.
- Que Key Vault, App Configuration y el servicio de datos permitan el acceso necesario.

### Contenedor o aplicación no saludable

- Confirma el nombre/tag de imagen y la autenticación al registro.
- Revisa startup command, puerto, variables de runtime y health probes.
- En ACA o AKS, inspecciona revisión/replicas, eventos y logs del contenedor.
- No reinicies o recrees recursos antes de guardar la evidencia diagnóstica necesaria.

### Mensajes, eventos o Functions no se procesan

- Verifica endpoint, topic/queue, suscripciones y permisos del productor/consumidor.
- Comprueba logs, delivery attempts, estado de Function y mensajes dead-letter cuando aplique.
- Distingue errores transitorios de mensajes no válidos; evita reintentos ilimitados.

### Consultas o telemetría sin resultados

- Comprueba que usas el workspace/recurso y el intervalo de tiempo correctos.
- Verifica que los datos se hayan ingerido y que la consulta KQL use la tabla y campos adecuados.
- Revisa credenciales, conectividad y configuración de exportación de OpenTelemetry.

## Escalación

Si el problema continúa, comparte con el instructor el mensaje de error sanitizado, el nombre del ejercicio y las comprobaciones realizadas. Consulta la documentación oficial del servicio enlazada en [Additional Resources](../docs/additional-resources.md).
