# AKS vs. Azure Container Apps

## La diferencia principal

La diferencia está en **cuánto de Kubernetes ves y administras tú**.

- **AKS (Azure Kubernetes Service)** es Kubernetes administrado. Azure se ocupa del *control plane* (API server, etcd, scheduler), pero el clúster es tuyo: los nodos, la red, el ingress, el escalado y todo lo que instales encima.
- **Azure Container Apps** es una plataforma *serverless* construida **sobre** Kubernetes, con KEDA, Envoy y Dapr por debajo, pero **no ves Kubernetes**. Declaras apps, revisiones y reglas de escalado, y Azure administra el resto. No hay `kubectl` ni nodos.

> **Analogía:** AKS es alquilar un auto y manejarlo tú; Container Apps es pedir un taxi y decir a dónde vas.

## Qué administras en cada uno

| Tema | AKS | Container Apps |
|---|---|---|
| Control plane | Azure (tú eliges la versión y las actualizaciones) | Azure (invisible) |
| Nodos / VMs | **Tú**: tamaño, pools, actualización del sistema operativo, escalado | Azure (no existen para ti) |
| Versión de Kubernetes | **Tú** planificas las actualizaciones (cada versión tiene un ciclo de soporte) | No aplica |
| Ingress / TLS | **Tú** instalas y configuras (NGINX, Application Gateway, cert-manager...) | Incluido: `ingress: external` y listo |
| Escalado de pods | **Tú** configuras HPA o instalas KEDA | Incluido: reglas HTTP, TCP, CPU, KEDA |
| Escalado a cero | Posible con KEDA, pero los nodos siguen encendidos | Incluido; en el plan Consumption no pagas |
| Despliegue / tráfico | Deployments, Services y herramientas tipo Argo o Flagger | Revisiones y división de tráfico incluidas |
| Identidades | Workload Identity (federación por *service account*) | Identidad administrada asignada a la app |
| Red | CNI, *network policies*, *service mesh*: todo configurable | VNet integration, ingress interno o externo; menos control fino |
| Observabilidad | Container Insights, Prometheus, Grafana (los configuras tú) | Log Analytics integrado |

## Ventajas y desventajas

### Container Apps

**Ventajas**

- Casi nada que mantener: no hay nodos que parchear ni versiones que actualizar.
- Escala a cero y cobra por uso (plan Consumption): ideal para cargas variables y workers de colas.
- Trae incluidas cosas que en AKS montas tú: HTTPS, revisiones, división de tráfico, KEDA, Dapr.

**Desventajas**

- **Menos control**: no hay acceso a la API de Kubernetes, así que no puedes usar Helm charts, operadores, CRDs ni DaemonSets, ni configurar el scheduler.
- Opciones de red y seguridad más limitadas (sin *service mesh* propio ni *network policies* detalladas).
- Hay límites de la plataforma (recursos por contenedor, réplicas, contenedores con privilegios no permitidos).
- Si el sistema crece mucho y necesitas algo que la plataforma no ofrece, migrar a AKS lleva trabajo.

### AKS

**Ventajas**

- **Control total**: cualquier cosa que corra en Kubernetes corre en AKS.
- Todo el ecosistema disponible: Helm, operadores (bases de datos, Kafka...), GitOps con Flux o Argo, *service mesh*.
- Portable: los mismos manifiestos sirven en otras nubes u on-premises.
- Más eficiente en costo a gran escala, porque empaquetas muchas cargas en los mismos nodos.

**Desventajas**

- **Necesitas saber Kubernetes**, y alguien tiene que operar el clúster: actualizaciones, seguridad, capacidad.
- Pagas los nodos aunque no haya tráfico (los *node pools* tienen un mínimo).
- Lo que Container Apps trae listo (ingress, certificados, escalado por eventos, revisiones), en AKS lo instalas y mantienes tú.

> **Punto intermedio:** **AKS Automatic** es un modo de AKS que preconfigura y administra los nodos, el escalado, la seguridad y el ingress con buenas prácticas, pero sigue dándote la API de Kubernetes completa. Conviene revisar su estado y limitaciones actuales en la documentación antes de recomendarlo.

## Cuándo usar cada uno

| Escenario | Recomendación |
|---|---|
| APIs, webs y microservicios "normales" | **Container Apps** |
| Workers de colas o eventos que pueden quedar inactivos | **Container Apps** (escala a cero) |
| Equipo chico, sin experiencia en Kubernetes | **Container Apps** |
| Necesitas operadores, CRDs, Helm charts de terceros o DaemonSets | **AKS** |
| Requisitos de red estrictos (*service mesh*, *network policies*, multi-tenant) | **AKS** |
| Ya tienes plataforma y equipo de Kubernetes, o necesitas portabilidad entre nubes | **AKS** |
| Cientos de servicios con carga estable y foco en optimizar costos | **AKS** |

## Aplicado al ejemplo de la clase

El ejemplo [samples/aca-dotnet-bicep](../../samples/aca-dotnet-bicep/) tiene tres apps: web, api y worker. Para correrlo en AKS tendrías que crear y mantener:

- el clúster y su *node pool*;
- un **Deployment** y un **Service** por app;
- un **ingress controller** con certificado TLS para la web;
- **KEDA** instalado en el clúster, con un `ScaledObject` para el worker;
- un **HPA** para la web y la API;
- **Workload Identity**: *service accounts* federadas con las identidades administradas;
- herramientas como Argo Rollouts o Flagger para imitar la división de tráfico 80/20.

En Container Apps, todo eso son unas 300 líneas en [apps.bicep](../../samples/aca-dotnet-bicep/infra/apps.bicep). Esa diferencia en cantidad de piezas es lo que conviene mostrarles a los alumnos.

## Para cerrar el tema

> *"Container Apps es Kubernetes cuando no quieres administrar Kubernetes; AKS es Kubernetes cuando lo necesitas entero."*
