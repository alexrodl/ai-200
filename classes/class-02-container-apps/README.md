# Class 02 - Azure Container Apps

## Datos de la clase

- **Duración:** 3 horas, incluido un corte de 15 minutos.
- **Tiempo neto de clase:** 2 horas y 45 minutos.
- **Material de referencia:** presentación `AI-200T00-PowerPoint_02.es-ES.pptx`.
- **Bloques:** implementación, administración y escalado de aplicaciones en Azure Container Apps.

## Objetivos

Al finalizar la clase, podrás:

- Explicar cómo un entorno de Azure Container Apps proporciona límites compartidos de red, registro y aislamiento.
- Implementar aplicaciones contenedorizadas con Azure CLI y YAML.
- Configurar variables de entorno, secretos y autenticación para extraer imágenes de registros privados.
- Administrar revisiones y diagnosticar errores de implementación y ejecución.
- Configurar reglas de escalado y relacionar el rendimiento, la capacidad y el coste.

## Temas y resumen

### Implementación de aplicaciones contenedorizadas

Revisaremos qué ofrece un entorno de Azure Container Apps y cómo agrupar aplicaciones según sus necesidades de red, comunicación privada y observabilidad. Compararemos las rutas de implementación con Azure CLI: `az containerapp up` para empezar rápidamente, `az containerapp create` para controlar la creación y YAML para mantener una configuración revisable en el control de código fuente.

Cada actualización genera una revisión. Antes de dirigir tráfico a una nueva versión, comprobaremos su estado. También veremos cómo separar la configuración no confidencial en variables de entorno y los valores confidenciales en secretos. Para extraer imágenes de Azure Container Registry (ACR), priorizaremos Managed Identity con el permiso mínimo `AcrPull` frente a credenciales almacenadas.

### Administración y diagnóstico

Compararemos las etiquetas de imagen, que pueden cambiar, con los resúmenes (*digests*), que identifican un artefacto inmutable y facilitan su rastreo. Practicaremos un flujo seguro de revisión: actualizar, validar el estado y después cambiar el tráfico; una revisión problemática se puede desactivar para aislarla.

Para diagnosticar, distinguiremos los registros de consola de la aplicación de los registros del sistema de la plataforma y revisaremos el estado de revisiones y réplicas. También veremos los sondeos de preparación y vivacidad, y cómo investigar problemas habituales de extracción de imágenes, puertos, configuración, sondeos y recursos de CPU o memoria.

### Escalado de contenedores

Veremos el escalado horizontal según demanda, incluidos los desencadenadores HTTP, TCP, CPU y memoria, y el escalado basado en eventos mediante KEDA. Revisaremos ejemplos con Azure Service Bus, Event Hubs y Storage, así como reglas combinadas —por ejemplo, una programación con Cron y demanda HTTP—. La configuración de recursos y réplicas debe responder al comportamiento observado: afecta tanto a la latencia y capacidad como al coste.

Por último, compararemos el modo de revisión única con el modo de revisiones múltiples, que permite mantener versiones activas y distribuir tráfico para escenarios como despliegues progresivos y pruebas A/B.

## Ejercicios

Los tres ejercicios forman parte del material oficial del curso. La presentación estima 30 minutos para cada uno; reserva tiempo adicional para preparar el entorno y revisar los resultados.

| Ejercicio | Actividad | Tiempo estimado | Archivos del laboratorio |
|---|---|---:|---|
| [Deploy a containerized backend API to Azure Container Apps](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-container-apps/01-aca-deploy-containers.html) | Desplegar una API, configurar Managed Identity para extraer la imagen de ACR y usar secretos como variables de entorno. | 30 minutos | [Lab 04](labs/04-aca-deploy-python/) |
| [Diagnose and fix a failing deployment](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-container-apps/02-aca-manage-containers.html) | Investigar una implementación con errores usando el estado de las revisiones, registros y Azure CLI. | 30 minutos | [Lab 05](labs/05-aca-manage-python/) |
| [Configure autoscaling using KEDA triggers](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-container-apps/03-aca-scale-containers.html) | Configurar el escalado automático por concurrencia de solicitudes HTTP y observar el cambio en el número de réplicas. | 30 minutos | [Lab 06](labs/06-aca-scale-python/) |

Consulta las instrucciones oficiales para conocer los requisitos, pasos de validación y limpieza de cada ejercicio. Los laboratorios indican que se necesita una suscripción de Azure con permisos y cuota suficientes; revisa sus avisos de coste y disponibilidad antes de comenzar.

## Preguntas para revisar

- ¿Cuándo conviene usar un archivo YAML en lugar de configurar cada cambio de forma imperativa?
- ¿Por qué una Managed Identity con `AcrPull` es preferible a guardar credenciales del registro?
- ¿Qué revisarías primero si una nueva revisión no inicia: registros de consola, registros del sistema, estado de la revisión o réplicas?
- ¿Qué diferencia hay entre un sondeo de preparación y uno de vivacidad?
- ¿Qué regla de escalado elegirías para una API HTTP y cuál para un procesador de mensajes que puede quedar inactivo?
- ¿Qué estrategia de revisiones permite probar una versión sin enviarle todo el tráfico de producción?

## Preparación y cierre

Antes de la clase, verifica el acceso a una suscripción de Azure autorizada y los requisitos específicos de cada ejercicio. Las prácticas pueden crear recursos facturables. Al terminar, sigue las instrucciones oficiales de limpieza y confirma que no queden recursos activos.
