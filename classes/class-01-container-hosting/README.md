# Class 01 - Container Application Hosting

## Datos de la clase

- **Duración:** 3 horas, incluido un corte de 15 minutos.
- **Tiempo neto de clase:** 2 horas y 45 minutos.
- **Material de referencia:** presentación `AI-200T00-PowerPoint_01.es-ES.pptx`.
- **Bloques:** Azure Container Registry (ACR) y contenedores en Azure App Service.

## Objetivos

Al finalizar la clase, podrás:

- Explicar cómo se organizan las imágenes y artefactos en un container registry.
- Compilar y administrar imágenes de contenedor con ACR Tasks.
- Elegir etiquetas y resúmenes adecuados para identificar versiones de imágenes.
- Implementar una imagen de contenedor de Linux desde ACR en Azure App Service.
- Configurar aspectos básicos del runtime y reconocer opciones de diagnóstico de App Service.

## Temas y resumen

### Azure Container Registry y ACR Tasks

Veremos cómo un registro, sus repositorios y artefactos organizan imágenes de contenedor. Compararemos etiquetas, que pueden cambiar, con referencias por resumen, que permiten identificar una imagen concreta. También revisaremos ACR Tasks para compilar imágenes en Azure, automatizar compilaciones y aplicar prácticas de etiquetado y ciclo de vida.

### Contenedores en Azure App Service

Revisaremos cómo desplegar una imagen de contenedor de Linux desde un registro, cómo configurar el comportamiento de ejecución y cómo proporcionar configuración a la aplicación sin incorporarla a la imagen. También veremos las opciones de diagnóstico disponibles para investigar problemas de inicio y ejecución.

## Ejercicios

Los dos ejercicios forman parte del material oficial del curso. Los tiempos son los indicados en la presentación; reserva tiempo adicional para preparar el entorno y revisar resultados.

| Ejercicio | Actividad | Tiempo estimado |
|---|---|---:|
| [Build and run a container image with ACR Tasks](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/container-hosting/01-acr-tasks.html) | Compilar y administrar una imagen de contenedor en Azure Container Registry con ACR Tasks, sin depender de una instalación local de Docker. | 30 minutos |
| [Deploy a container to Azure App Service](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/container-hosting/02-app-svc-container.html) | Implementar en Azure App Service una imagen de contenedor de Linux almacenada en Azure Container Registry. | 30 minutos |

Consulta las instrucciones oficiales de cada ejercicio para conocer los requisitos específicos, pasos de validación y limpieza.

## Preguntas para revisar

- ¿Cuándo conviene identificar una imagen mediante un resumen en lugar de una etiqueta?
- ¿Qué tareas puede ejecutar ACR Tasks durante el ciclo de vida de una imagen?
- ¿Qué configuración de la aplicación debería mantenerse fuera de la imagen de contenedor?
- ¿Qué revisarías si la aplicación no inicia o no responde después del despliegue?

## Preparación y cierre

Antes de la clase, verifica el acceso a una suscripción de Azure autorizada y los requisitos generales y específicos de los laboratorios. Los ejercicios pueden crear recursos facturables. Al terminar, sigue las instrucciones oficiales de limpieza y confirma que no queden recursos activos.
