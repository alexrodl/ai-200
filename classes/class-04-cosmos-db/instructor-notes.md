# Instructor Notes - Class 04

> Notas complementarias del instructor (MCT). No reemplazan ni reproducen el material oficial de Microsoft. Las diapositivas se refieren a `AI-200T00-PowerPoint_03.es-ES.pptx` (PPT 03) y `AI-200T00-PowerPoint_04.es-ES.pptx` (PPT 04).

## Objective

Cerrar el learning path de AKS con mucha práctica (3 ejercicios) y dejar presentado el modelo de Cosmos DB para que la clase 05 empiece directamente con un ejercicio.

## Teaching Goal

- Fijar un **bucle de diagnóstico** repetible: estado → Service/endpoints → eventos/logs → corregir manifiesto.
- Que los alumnos distingan **ConfigMap vs. Secret vs. PVC** por el problema que resuelve cada uno.
- Mantener la teoría en bloques de 12-15 minutos, siempre **mientras se despliega** un ejercicio.

## Before the Class

- [ ] Abrir en una pestaña cada ejercicio oficial (Lab 07, 08, 09) y descargar los ZIP de inicio.
- [ ] En **tu propia suscripción**, tener un clúster de Lab 09 ya desplegado (namespace `aks-troubleshoot`). Es el plan B si hay que convertir el Lab 09 en demo.
- [ ] Confirmar con XtremeLabs que la suscripción es de pago (ACR Tasks no funciona con créditos gratuitos), qué región usar y qué cuota de vCPU Dsv5 y de `gpt-5-mini` tiene (Lab 07).
- [ ] Recordar a los alumnos que traigan `kubectl` instalado (`az aks install-cli`).
- [ ] La carpeta [class-03-aks/aks-deploy-python](../class-03-aks/aks-deploy-python/) tiene los manifiestos **ya completados**. Úsala como solución de referencia, pero los alumnos deben partir del ZIP oficial.

## Detailed Agenda

| Horario | Bloque | Diapos | Notas |
|---|---|---|---|
| 19:00 - 19:05 | Inicio de la ventana 1 de XtremeLabs. `az login`, registro de providers, `azdeploy.py` opciones 1-4 | - | **Lo primero de la clase.** El despliegue tarda 15-20 minutos |
| 19:05 - 19:20 | Repaso del módulo 1 | 3-8 | Mientras se despliega. Pedir que abran `deployment.yaml` y lo completen en paralelo |
| 19:20 - 19:45 | Lab 07 | 9 | Opción 5 (estado), opción 6 (aplicar), `kubectl get deploy,svc`, `kubectl rollout status`, cliente Python |
| 19:45 - 19:50 | KC M1 y resumen | 10, 12 | Eliminar el RG de Lab 07 (`--no-wait`) y **lanzar ya el despliegue de Lab 08** |
| 19:50 - 20:02 | Módulo 2: ConfigMap, Secret, PVC | 13-18 | Mientras se despliega Lab 08 (10-15 minutos) |
| 20:02 - 20:22 | Lab 08 (parte 1) | 19 | Completar ConfigMap, Secret y PVC, poner el endpoint de ACR y aplicar |
| 20:22 - 20:37 | Corte | - | - |
| 20:37 - 20:52 | Lab 08 (parte 2) | 19 | Probar con el cliente. Eliminar el pod y comprobar que el log del PVC persiste |
| 20:52 - 21:00 | KC M2, resumen y limpieza | 20, 22 | La ventana 1 termina a las 21:00. No empezar nada nuevo en ella |
| 21:00 - 21:12 | Inicio de la ventana 2 y despliegue de Lab 09. Módulo 3 | 23-28 | Mientras se despliega (10-15 minutos) |
| 21:12 - 21:42 | Lab 09 | 29 | Tres fallos inyectados: selector, CrashLoopBackOff, readiness probe |
| 21:42 - 21:45 | KC M3 y debate | 30, 32, 34 | Elegir **una** pregunta de debate (la 2 encaja con Lab 09) |
| 21:45 - 22:00 | Cosmos DB: introducción al módulo 1 | PPT 04: 1-9 | Partición, RU, lectura puntual vs. consulta, consultas con parámetros |

### Contingencias

- **A las 20:22, si Lab 08 no está aplicado:** acortar el módulo 3 a 8 minutos (diapositivas 26-28) y pasar el Lab 09 a demo del instructor con el clúster preparado. Los alumnos lo hacen como tarea en la ventana 2.
- **Si el Lab 07 se alarga (cuota, región o modelo de Foundry):** que los alumnos con problemas sigan la demo en pantalla y pasen al Lab 08, que no depende de Foundry.
- **La introducción a Cosmos DB es lo primero que se recorta.** Si no hay tiempo, la clase 05 empieza con las diapositivas 5-9 del PPT 04 mientras se despliega el Lab 10.
- **Ventana 2 después de clase:** sigue activa hasta unos 60 minutos después de las 22:00. Los alumnos que quieran pueden empezar el Lab 10 (Cosmos DB) en casa.

## Key Concepts and Talking Points

### Module 1 (repaso, diapositivas 5-8)

- Cuatro ideas: **los pods ejecutan, los Deployments administran, los Services enrutan y kubectl verifica.**
- Etiquetas: `selector.matchLabels` = `template.metadata.labels` = `Service.spec.selector`. Es el error n.º 1.
- `port` (lo que ve el cliente) vs. `targetPort` (el puerto del contenedor). En Lab 07: 80 → `http` (8000).
- *Requests* = reserva para el scheduler. *Limits* = techo. Si se supera el límite de CPU hay *throttling*; si se supera el de memoria, `OOMKilled`.
- Conectar con la clase 02: `livenessProbe` / `readinessProbe` son los mismos conceptos que en Container Apps.

### Module 2 (diapositivas 14-18)

- Tres pilares: **configuración (ConfigMap), credenciales (Secret) y durabilidad (PVC)**. Los tres siguen el mismo flujo: YAML → referencia en el Deployment → `kubectl apply` → verificar con `describe` / `exec`.
- Variables de entorno: hay que reiniciar el pod para que cambien. Volumen: se actualiza solo, pero la aplicación tiene que releer el archivo.
- ConfigMap `immutable: true`: menos carga en el API server, pero para cambiarlo hay que eliminarlo y crearlo de nuevo.
- **Base64 no es cifrado.** Demostrarlo en vivo (ver la demo de abajo).
- Producción: Key Vault + Secrets Store CSI Driver + Workload Identity (enlazar con `aks-conceptos.md`, sección 5).
- StorageClasses integradas: `managed-csi`, `managed-csi-premium`, `azurefile-csi` y `azurefile-csi-premium`. Disk = RWO, Files = RWX.

### Module 3 (diapositivas 24-28)

- El portal sirve para la vista general (Container Insights, Live Logs, *Diagnose and solve problems*). `kubectl` sirve para el detalle.
- `kubectl top` necesita metrics-server (AKS lo trae por defecto).
- `kubectl logs --previous` es clave en `CrashLoopBackOff`: muestra los logs del contenedor que ya terminó.
- `kubectl port-forward` permite probar antes de exponer.

### Cosmos DB intro (PPT 04, diapositivas 5-9)

- Jerarquía y **clave de partición con alta cardinalidad** (`userId`, `tenantId`). Comparar con una mala clave (booleana, fecha).
- RU: la "moneda" del servicio. El encabezado `x-ms-request-charge` muestra el costo de cada operación.
- `CosmosClient` **singleton**. `read_item()` (≈1 RU) vs. `query_items()`.
- Consultas con parámetros (`@param`): seguridad y caché del plan. Nunca concatenar texto del usuario.

## Demo Suggestions

1. **Base64 no es cifrado (2 minutos, durante el módulo 2):**

   ```bash
   kubectl create secret generic demo-secret --from-literal=API_KEY=not-a-real-key
   kubectl get secret demo-secret -o jsonpath='{.data.API_KEY}' | base64 --decode
   kubectl delete secret demo-secret
   ```

   *Qué deben observar:* cualquiera con permiso de lectura sobre Secrets ve el valor. De ahí la importancia de RBAC, Key Vault y el cifrado de etcd.

2. **Romper el selector en vivo (3 minutos, antes del Lab 09):** con el clúster de Lab 07, editar `service.yaml` (`app: aks-api-x`), aplicarlo y mostrar `kubectl describe service aks-api-service` y `kubectl get endpointslices`. Luego revertirlo.

3. **Persistencia del PVC (dentro del Lab 08):** `kubectl delete pod <pod>`, esperar al nuevo pod y comprobar que el log sigue ahí.

## Likely Student Questions

| Tipo | Pregunta | Respuesta breve |
|---|---|---|
| Principiante | ¿Por qué cada laboratorio crea un clúster nuevo? | Cada ejercicio es independiente. En la vida real se reutiliza el clúster y se separa con namespaces |
| Práctica | ¿Tengo que reiniciar el pod si cambio un ConfigMap? | Si lo consumes como variable de entorno, sí (`kubectl rollout restart deploy/<name>`). Si lo montas como volumen, se actualiza solo, con algo de retraso |
| Troubleshooting | El pod está `Running` pero el Service no responde | Revisa si está `Ready` (readiness probe), los endpoints del Service y `targetPort` |
| Troubleshooting | `ImagePullBackOff` en el Lab 07 | Revisa el nombre del ACR en `deployment.yaml` (placeholder `ACR_ENDPOINT`) y el rol `AcrPull` del kubelet |
| Arquitectura | ¿Secret de Kubernetes o Key Vault? | Para desarrollo, un Secret. Para producción, Key Vault con CSI Driver (rotación y auditoría) |
| Producción | ¿Usarías un Service `LoadBalancer` público para la API? | Para aprender sí. En producción, un Ingress o Application Gateway for Containers con TLS, WAF y autenticación |
| Producción | ¿Cuánto cuesta el clúster del laboratorio? | El control plane en el tier Free no tiene costo. Los nodos (VMs) sí. Por eso se elimina el RG al terminar |
| Cosmos DB | ¿Puedo cambiar la clave de partición después? | No. Hay que crear un contenedor nuevo y migrar los datos |
| Certificación | ¿Esto entra en el examen? | No se puede asegurar qué preguntas habrá. Sí son habilidades del curso: manifiestos, tipos de Service, configuración y diagnóstico |

## AI-200 Exam Tips

> Se basan en los conceptos del curso oficial. No son preguntas del examen. Revisa el [skills outline de la certificación](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-cloud-developer-associate/) para la versión vigente.

- **Selector de etiquetas ↔ etiquetas del pod**: es lo que conecta un Service con sus pods, no el nombre del recurso.
- **Tipo de Service según el alcance**: `ClusterIP` interno, `LoadBalancer` externo administrado por Azure y `NodePort` casi solo para pruebas.
- **Estado → causa**: `ImagePullBackOff` = registro o credenciales. `CrashLoopBackOff` = la aplicación o su configuración. `Pending` = capacidad o *requests*.
- **Herramienta según el síntoma**: `kubectl logs -f` para errores intermitentes, `kubectl describe service` para endpoints vacíos y `kubectl describe pod` para eventos.
- **ConfigMap vs. Secret**: confidencialidad. **Variable de entorno vs. volumen**: cómo lee la aplicación la configuración.
- **RWO (Azure Disk) vs. RWX (Azure Files)**: ¿necesitan varios pods escribir a la vez?
- **Cosmos DB**: clave de partición de alta cardinalidad alineada con la consulta más frecuente. Lectura puntual siempre que conozcas `id` y la clave de partición.

## Notes on the Official Slides

- En las diapositivas de **resumen** del PPT 03 (12, 22 y 32) hay un párrafo sobrante sobre Cosmos DB ("La clave de partición es tu decisión de diseño...") que no corresponde a AKS. Ocúltalo o ignóralo al presentar.
- Las diapositivas de ejercicio tienen el marcador "Personaliza esta diapositiva... (a continuación, quita esta flecha)". Sustitúyelo por el enlace del laboratorio y las instrucciones de XtremeLabs.
- Las diapositivas ocultas de "Interactive Knowledge check" (11, 21 y 31) tienen prompts para Copilot Chat. Son opcionales; no hay tiempo para usarlas en esta clase.

## Common Mistakes

| Error | Causa | Solución |
|---|---|---|
| `kubectl` apunta al clúster del laboratorio anterior | Contextos antiguos en `~/.kube/config` | `kubectl config get-contexts` y `kubectl config use-context <name>` |
| Error de cuota de vCPU al crear el segundo clúster | El clúster anterior sigue activo | Eliminar el RG anterior antes de lanzar el siguiente |
| Error de ACR Tasks con "paused" | Suscripción con créditos gratuitos | Requiere una suscripción de pago (confirmar con XtremeLabs) |
| La IP externa queda en `<pending>` | El Azure Load Balancer todavía se está creando | Esperar 1-3 minutos con `kubectl get svc -w` |
| La sesión de XtremeLabs caducó | Ventana de 2 horas | Ver "Si la suscripción caduca" en el [README](README.md) |
