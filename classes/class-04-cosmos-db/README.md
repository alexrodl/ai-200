# Class 04 - Azure Kubernetes Service (configuración y troubleshooting) e introducción a Azure Cosmos DB

## Datos de la clase

- **Fecha:** lunes 2 de noviembre de 2026, de 19:00 a 22:00.
- **Duración:** 3 horas, incluido un corte de 15 minutos (20:22 - 20:37).
- **Tiempo neto de clase:** 2 horas y 45 minutos, con prioridad para la práctica.
- **Material de referencia:** presentaciones `AI-200T00-PowerPoint_03.es-ES.pptx` (AKS) y `AI-200T00-PowerPoint_04.es-ES.pptx` (Cosmos DB, módulo 1).
- **Bloques:** ejercicio pendiente de despliegue en AKS, configuración de aplicaciones en AKS, troubleshooting en AKS e introducción a Azure Cosmos DB for NoSQL.

## Dónde quedamos

En la [clase 03](../class-03-aks/) vimos la arquitectura de AKS y el módulo 1 (*Deploy applications to Azure Kubernetes Service*). El primer ejercicio del módulo quedó pendiente. Esta clase empieza con ese ejercicio.

## Objetivos

Al finalizar la clase, podrás:

- Desplegar una API de inferencia en AKS con manifiestos de Deployment y Service, y comprobar su estado con `kubectl`.
- Externalizar la configuración con ConfigMaps, proteger valores confidenciales con Secrets y conservar datos con PersistentVolumeClaims.
- Diagnosticar fallos habituales de pods y Services: selectores que no coinciden, `CrashLoopBackOff` y sondeos de preparación con errores.
- Explicar el modelo de recursos de Azure Cosmos DB for NoSQL, la clave de partición y las unidades de solicitud (RU).

## Agenda

La suscripción temporal de laboratorio dura **2 horas desde que la inicias**. La agenda usa dos ventanas: la primera de 19:00 a 21:00 y la segunda desde las 21:00.

| Horario | Actividad | Diapositivas | Tipo |
|---|---|---|---|
| 19:00 - 19:05 | Iniciar la suscripción de laboratorio (ventana 1) y lanzar el despliegue de Lab 07 | - | Práctica |
| 19:05 - 19:20 | Repaso de manifiestos, Services y señales de error mientras se crea el clúster | PPT 03: 3-8 | Teoría |
| 19:20 - 19:45 | **Lab 07** - Deploy an AI inference API to AKS | PPT 03: 9 | Práctica |
| 19:45 - 19:50 | Prueba de conocimientos del módulo 1, limpieza y lanzamiento del despliegue de Lab 08 | PPT 03: 10, 12 | Repaso |
| 19:50 - 20:02 | ConfigMaps, Secrets y almacenamiento persistente | PPT 03: 13-18 | Teoría |
| 20:02 - 20:22 | **Lab 08** (parte 1) - Configure apps on AKS | PPT 03: 19 | Práctica |
| 20:22 - 20:37 | **Corte** | - | - |
| 20:37 - 20:52 | **Lab 08** (parte 2) - Pruebas y persistencia | PPT 03: 19 | Práctica |
| 20:52 - 21:00 | Prueba de conocimientos del módulo 2 y limpieza (la ventana 1 termina a las 21:00) | PPT 03: 20, 22 | Repaso |
| 21:00 - 21:12 | Iniciar la ventana 2, lanzar el despliegue de Lab 09 y ver supervisión y troubleshooting | PPT 03: 23-28 | Teoría |
| 21:12 - 21:42 | **Lab 09** - Troubleshoot apps on AKS | PPT 03: 29 | Práctica |
| 21:42 - 21:45 | Prueba de conocimientos del módulo 3 y debate | PPT 03: 30, 32, 34 | Repaso |
| 21:45 - 22:00 | Azure Cosmos DB for NoSQL: modelo de recursos, partición, RU y consultas | PPT 04: 1-9 | Teoría |

**Resultado:** unos 100 minutos de práctica y 50 minutos de teoría.

## Temas y resumen

### Despliegue de aplicaciones en AKS (repaso y Lab 07)

Un **Deployment** declara el estado deseado: imagen, número de réplicas, puertos, sondeos y recursos. Un **Service** busca los pods por **etiquetas**. Si el selector no coincide con las etiquetas del pod, el Service se queda sin endpoints. Elige el tipo de Service según quién necesita acceder: `ClusterIP` para tráfico interno y `LoadBalancer` para clientes externos. Los *requests* y *limits* deciden en qué nodo se programa el pod y cuánto puede consumir.

### Configuración de aplicaciones en AKS (Lab 08)

- **ConfigMap:** configuración no confidencial. Se consume como variables de entorno o como archivos montados en un volumen.
- **Secret:** credenciales y claves. Un Secret de Kubernetes está codificado en **base64, no cifrado**. En producción, intégralo con Azure Key Vault mediante el Secrets Store CSI Driver.
- **PersistentVolumeClaim (PVC):** almacenamiento que sobrevive a los reinicios del pod. Una StorageClass lo aprovisiona en Azure Disk (`ReadWriteOnce`) o en Azure Files (`ReadWriteMany`).

### Supervisión y troubleshooting en AKS (Lab 09)

Sigue siempre el mismo orden: **estado del pod → Service y endpoints → eventos y registros → corrección**. Cada estado de error apunta a una causa distinta:

| Señal | Causa probable | Primer comando |
|---|---|---|
| `ImagePullBackOff` | Ruta de imagen incorrecta o falta el permiso `AcrPull` | `kubectl describe pod <pod>` |
| `CrashLoopBackOff` | La aplicación arranca y termina: falta configuración, puerto incorrecto o comando incorrecto | `kubectl logs <pod> --previous` |
| `Pending` | Los *requests* superan la capacidad libre de los nodos | `kubectl describe pod <pod>` (eventos `FailedScheduling`) |
| Service sin endpoints | El selector no coincide con las etiquetas del pod | `kubectl describe service <svc>` / `kubectl get endpointslices` |
| Pod `Running` pero no `Ready` | El sondeo de preparación falla | `kubectl describe pod <pod>` (eventos `Unhealthy`) |

### Azure Cosmos DB for NoSQL (introducción)

Jerarquía **cuenta → base de datos → contenedor → elemento**. La **clave de partición** es la decisión de diseño más importante, porque no se puede cambiar sin crear un contenedor nuevo y migrar los datos. Todas las operaciones se miden en **RU**. Una lectura puntual (`id` + clave de partición) cuesta alrededor de 1 RU y siempre es más barata que una consulta.

## Ejercicios

Los tres ejercicios de AKS forman parte del material oficial del curso. Cada uno crea **su propio** clúster de AKS. La creación de recursos tarda entre 10 y 20 minutos, así que lánzala al principio y sigue con la teoría mientras termina.

| Ejercicio | Actividad | Tiempo estimado | Archivos del laboratorio |
|---|---|---:|---|
| [Deploy an AI inference API to Azure Kubernetes Service](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-kubernetes-service/01-aks-deploy-container.html) | **Lab 07.** Desplegar un modelo de Microsoft Foundry, ACR y AKS. Completar `deployment.yaml` y `service.yaml` y probar la API con un cliente Python. | 30 minutos (15-20 de despliegue) | [Lab 07](../class-03-aks/aks-deploy-python/) |
| [Configure apps on Azure Kubernetes Service](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-kubernetes-service/02-aks-configure-container.html) | **Lab 08.** Crear un ConfigMap, un Secret y un PVC, y conectarlos a un Deployment. | 30 minutos (10-15 de despliegue) | Starter oficial `aks-configure-python.zip` |
| [Troubleshoot apps on Azure Kubernetes Service](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/azure-kubernetes-service/03-aks-troubleshoot-container.html) | **Lab 09.** Diagnosticar y corregir un selector que no coincide, un `CrashLoopBackOff` y un sondeo de preparación con errores. | 30 minutos (10-15 de despliegue) | Starter oficial `aks-troubleshoot-python.zip` |

> **Posibles tareas para casa:** si la clase se retrasa más de 10 minutos antes del corte, **Lab 09** se hace como demostración del instructor y queda como tarea. El **Lab 10** (Cosmos DB, primer ejercicio) puede empezarse en casa con la ventana 2, que sigue activa hasta unos 60 minutos después de la clase. Si no, se hace al principio de la clase 05.

## Trabajar con la suscripción temporal de laboratorio (2 horas)

- **Antes de empezar un ejercicio, mira cuánto tiempo le queda a la suscripción.** No empieces un ejercicio de AKS con menos de 45 minutos restantes: solo el clúster tarda 10-20 minutos.
- **Primero lanza la creación de recursos y después lee o edita.** Puedes completar los archivos YAML mientras el script crea el clúster.
- **Trabaja en una carpeta local de tu equipo.** Los archivos que edites (YAML, Python) se conservan aunque la suscripción caduque. Lo que se pierde son los recursos de Azure.
- **Al terminar cada ejercicio, elimina su Resource Group** (`az group delete --name <rg-name> --no-wait --yes`) antes de lanzar el siguiente. Así liberas cuota de vCPU para el próximo clúster.

### Si la suscripción caduca a mitad de un ejercicio

1. Inicia una nueva sesión de laboratorio y vuelve a iniciar sesión: `az login`, y después `az account show` para confirmar que estás en la suscripción nueva.
2. Los valores de `.env` / `.env.ps1` y el contexto de `kubectl` apuntan a recursos que ya no existen. Vuelve a ejecutar `azdeploy.py` para crear los recursos y obtener las credenciales del clúster.
3. Vuelve a aplicar tus manifiestos (`kubectl apply -f k8s/`). Tus cambios locales siguen intactos.
4. Si `kubectl` apunta a un clúster antiguo, revisa `kubectl config get-contexts` y selecciona el nuevo con `kubectl config use-context <name>`.

## Preguntas para revisar

- ¿Qué tiene que coincidir entre un Deployment y un Service para que el tráfico llegue a los pods?
- ¿Cuándo usarías `ClusterIP` y cuándo `LoadBalancer`?
- ¿Por qué un Secret de Kubernetes, por sí solo, no basta para proteger una credencial en producción?
- La aplicación lee un archivo JSON de configuración al iniciar. ¿Cómo se lo entregarías sin recompilar la imagen?
- ¿Qué indica cada estado: `ImagePullBackOff`, `CrashLoopBackOff` y `Pending`?
- En Cosmos DB, ¿por qué una propiedad booleana es una mala clave de partición?

## Recursos de Microsoft Learn

- [Learning path: Deploy and monitor applications on Azure Kubernetes Service](https://learn.microsoft.com/training/paths/deploy-monitor-apps-azure-kubernetes-service/)
  - [Deploy applications to Azure Kubernetes Service](https://learn.microsoft.com/training/modules/deploy-apps-azure-kubernetes-service/)
  - [Configure applications on Azure Kubernetes Service](https://learn.microsoft.com/training/modules/configure-apps-azure-kubernetes-service/)
  - [Monitor and troubleshoot applications on Azure Kubernetes Service](https://learn.microsoft.com/training/modules/monitor-apps-azure-kubernetes-service/)
- [Learning path: Develop AI solutions with Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/paths/develop-ai-solutions-azure-cosmos-db/)
  - [Build queries for Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/modules/build-query-azure-cosmos-db/)

Material complementario del instructor: [conceptos de AKS](../class-03-aks/aks-conceptos.md) y [AKS vs. Container Apps](../class-03-aks/aks-vs-container-apps.md).

## Preparación y cierre

Antes de la clase, comprueba que tienes instalados Azure CLI, `kubectl`, Python 3.12 o posterior y Visual Studio Code, y que puedes iniciar la suscripción de laboratorio. Los ejercicios crean recursos facturables (clústeres de AKS, ACR, Microsoft Foundry y Cosmos DB). Al terminar cada ejercicio, elimina su Resource Group y comprueba en Azure Portal que no queden recursos activos.

**Próxima clase:** [Class 05 - Azure Cosmos DB for NoSQL](../class-05-cosmos-db/README.md).
