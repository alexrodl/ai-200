# Conceptos generales de AKS (Azure Kubernetes Service)

AKS es **Kubernetes administrado**. Azure opera el *control plane* (el "cerebro" del clúster), y tú administras los nodos, la red, el escalado, las identidades, las actualizaciones y todo lo que despliegas con YAML.

## Ejemplo de arquitectura

La misma aplicación del ejemplo de la clase ([samples/aca-dotnet-bicep](../../samples/aca-dotnet-bicep/)) desplegada en AKS:

![La aplicación web, api y worker en un clúster AKS, con node pools, ingress controller, KEDA, control plane, Cosmos DB, Service Bus, Azure AI Language, ACR, Workload Identity, Key Vault y Azure Monitor](docs/arquitectura-aks.svg)

Compárala con [la misma aplicación en Container Apps](container-apps-conceptos.md#ejemplo-de-arquitectura): los servicios de Azure son los mismos, pero en AKS aparecen el load balancer, el ingress controller, KEDA, los node pools, las VMs y el control plane, que tienes que configurar y mantener. Diagrama editable: [docs/arquitectura-aks.drawio](docs/arquitectura-aks.drawio).

## 1. Arquitectura: control plane y nodos

```text
┌──────────────── Control plane (lo administra Azure) ─────────────────┐
│  API server · etcd (estado del clúster) · scheduler · controllers    │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │  kubectl / Helm / GitOps hablan con el API server
        ┌──────────────────────────┴──────────────────────────┐
┌───────▼──────── System node pool ───────┐   ┌──────── User node pool ────────┐
│ VM  VM   (CoreDNS, metrics, agentes)     │   │ VM  VM  VM   (tus apps)         │
│ cada nodo: kubelet + runtime + pods      │   │ cada nodo: kubelet + pods       │
└──────────────────────────────────────────┘   └─────────────────────────────────┘
         Nodos = VMs en tu suscripción (Virtual Machine Scale Sets), las pagas tú
```

- **Control plane:** recibe las órdenes (API server), guarda el estado (etcd) y decide en qué nodo va cada pod (scheduler). En AKS lo **administra Azure**, y tú no ves esas VMs.
- **Nodos:** VMs que ejecutan los contenedores. Cada una tiene el **kubelet** (el agente que habla con el control plane) y un runtime de contenedores (containerd).
- **Node pools:** grupos de nodos con el mismo tamaño de VM y la misma configuración.
  - **System pool:** para los componentes del clúster (CoreDNS, agentes de monitoreo). Es obligatorio.
  - **User pools:** para tus apps. Puedes tener varios, por ejemplo uno con GPU, uno Linux y otro Windows, o uno con VMs Spot para ahorrar.

En Container Apps no hay nodos: el "entorno" esconde todo esto.

## 2. Objetos básicos de Kubernetes

Todo en Kubernetes se declara en **YAML** y se aplica con `kubectl apply`. Kubernetes trabaja con un modelo **declarativo**: tú describes el estado deseado y los *controllers* trabajan sin parar para que el clúster quede así.

| Objeto | Qué es | Equivalente en Container Apps |
|---|---|---|
| **Pod** | La unidad mínima: uno o más contenedores que comparten red y almacenamiento | Réplica |
| **Deployment** | Declara "quiero N pods de esta imagen" y gestiona las actualizaciones (*rolling update*) | Container app |
| **ReplicaSet** | Lo crea el Deployment, una por versión; mantiene la cantidad de pods | Revisión |
| **Service** | IP y nombre DNS estables para un grupo de pods (balanceo interno) | Ingress interno / `http://api` |
| **Ingress / Gateway API** | Expone HTTP(S) hacia afuera, con rutas y TLS | Ingress externo |
| **Namespace** | Separación lógica dentro del clúster (por equipo o entorno) | Entorno (aproximadamente) |
| **ConfigMap / Secret** | Configuración y secretos que se inyectan en los pods | Variables de entorno / secretos |
| **Job / CronJob** | Tareas que se ejecutan y terminan, una vez o programadas | Container Apps Jobs |
| **StatefulSet** | Pods con identidad y disco propios (bases de datos, Kafka) | No hay equivalente directo |
| **DaemonSet** | Un pod en **cada** nodo (agentes de logs o seguridad) | No hay: no hay nodos |
| **PV / PVC / StorageClass** | Almacenamiento persistente (Azure Disk, Azure Files) | Montajes de Azure Files |

### Tipos de Service

- **ClusterIP:** solo dentro del clúster (el más común).
- **LoadBalancer:** AKS crea un **Azure Load Balancer** con IP pública o privada.
- **NodePort:** expone un puerto en cada nodo. Se usa poco.

## 3. Escalado: dos niveles

En AKS se escala en **dos capas**, y eso es una gran diferencia con Container Apps:

| Qué escala | Herramienta | Cómo |
|---|---|---|
| **Pods** (horizontal) | **HPA** (Horizontal Pod Autoscaler) | Según CPU, memoria o métricas personalizadas |
| **Pods** por eventos | **KEDA** (add-on de AKS) | Según colas, Event Hubs, cron, etc. (lo mismo que usa Container Apps) |
| **Pods** (vertical) | **VPA** | Ajusta los *requests* de CPU y memoria de cada pod |
| **Nodos** | **Cluster autoscaler** / **Node auto-provisioning** | Agrega VMs cuando hay pods pendientes por falta de espacio y las quita cuando sobran |

Así funciona: el HPA pide más pods, el scheduler no encuentra lugar en los nodos, y el cluster autoscaler agrega una VM. Tarda unos minutos, mientras que una réplica nueva en Container Apps arranca en segundos.

**Requests y limits:** cada contenedor declara cuánta CPU y memoria **necesita** (*requests*, que el scheduler usa para elegir el nodo) y cuánta **puede usar como máximo** (*limits*). Definirlos bien es clave en AKS.

## 4. Red

- **Azure CNI Overlay** (lo recomendado hoy): los nodos toman IPs de tu VNet y los pods usan un rango privado aparte, así no se agotan las IPs de la VNet.
- **Azure CNI** clásico: cada pod recibe una IP de la VNet. Consume muchas IPs.
- **Kubenet:** modelo antiguo, en proceso de retiro.
- **Network policies:** reglas de firewall entre pods, por ejemplo "solo la api puede hablar con la base de datos". Se implementan con Azure, Calico o Cilium.
- **Ingress:** el add-on **Application Routing** (NGINX administrado) o **Application Gateway for Containers**.
- **Clúster privado:** el API server sin IP pública, accesible solo desde la VNet.

## 5. Identidad y seguridad

Hay que distinguir tres identidades distintas:

| Identidad | Para qué |
|---|---|
| **Usuarios → clúster** | **Microsoft Entra ID + RBAC** (Kubernetes RBAC o Azure RBAC). Quién puede ejecutar `kubectl` y sobre qué namespaces |
| **Clúster → Azure** | **Identidad administrada** del clúster y del kubelet. Por ejemplo, el rol **AcrPull** del kubelet para descargar imágenes de ACR |
| **Pods → servicios de Azure** | **Workload Identity**: una *service account* de Kubernetes se federa con una identidad administrada, y el pod usa `DefaultAzureCredential` igual que en el ejemplo de la clase |

Otros componentes de seguridad:

- **Azure Key Vault Secrets Provider:** monta secretos de Key Vault en los pods.
- **Azure Policy:** bloquea configuraciones inseguras, como contenedores con privilegios.
- **Microsoft Defender for Containers:** escaneo de vulnerabilidades y detección de amenazas.

## 6. Operación del clúster

Esto es lo que **tú** tienes que hacer en AKS, y en Container Apps no:

- **Actualizaciones de Kubernetes:** sale una versión nueva cada pocos meses y cada una tiene soporte limitado. Hay que actualizar el control plane y después los node pools, idealmente con canales de actualización automática.
- **Parches del sistema operativo de los nodos:** actualización de la imagen de los nodos (también se puede automatizar).
- **Capacidad:** elegir tamaños de VM, mínimos y máximos de nodos, y cuántos pods entran por nodo.
- **Disponibilidad:** repartir los nodos en zonas de disponibilidad y definir *Pod Disruption Budgets* para que las actualizaciones no tumben la app.
- **Monitoreo:** Container Insights, Prometheus administrado y Grafana.

## 7. Planes y modos

| | Detalle |
|---|---|
| **Tier Free** | Control plane sin costo y sin SLA. Para pruebas y aprendizaje |
| **Tier Standard** | Control plane con SLA de disponibilidad y más escala. Para producción |
| **Tier Premium** | Standard + soporte extendido de versiones de Kubernetes (LTS) |
| **AKS Standard** (modo) | Tú configuras y operas todo |
| **AKS Automatic** (modo) | Azure preconfigura y administra nodos, escalado, red, seguridad y actualizaciones con buenas prácticas, y tú sigues teniendo la API de Kubernetes completa |

En todos los tiers, **los nodos se pagan aparte** (son VMs).

## 8. Herramientas de despliegue

- **kubectl:** la CLI de Kubernetes (`kubectl apply -f app.yaml`, `kubectl get pods`, `kubectl logs`).
- **Helm:** gestor de paquetes. Un *chart* instala una app completa con sus manifiestos.
- **GitOps (Flux o Argo CD):** el clúster aplica lo que está en un repositorio de Git.
- **Pipelines:** GitHub Actions o Azure DevOps compilan la imagen, la suben a ACR y la despliegan.

## Resumen para la clase

> AKS te da **Kubernetes completo**: Azure administra el cerebro (control plane), y tú administras los nodos, la red, el escalado de dos niveles, las identidades, las actualizaciones y todo lo que despliegas con YAML.
>
> Container Apps toma **los mismos conceptos** (pods, revisiones, KEDA, ingress) y los esconde detrás de una plataforma serverless. Ver [container-apps-conceptos.md](container-apps-conceptos.md) y [aks-vs-container-apps.md](aks-vs-container-apps.md).
