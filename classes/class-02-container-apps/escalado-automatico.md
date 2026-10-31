# Escalado automático en Azure Container Apps

## 1. Concepto base

- Container Apps escala **réplicas** (instancias de la revisión activa) de forma horizontal y automática.
- Por debajo usa **KEDA** (Kubernetes Event-Driven Autoscaling), pero el alumno no administra Kubernetes: solo declara reglas.
- **El escalado es por revisión.** Cambiar las reglas de escalado crea una revisión nueva, porque forman parte de la plantilla.

## 2. Límites de réplicas

| Parámetro | Qué hace | Valor por defecto |
|---|---|---|
| `min-replicas` | Mínimo siempre encendido | 0 |
| `max-replicas` | Techo de escalado | 10 (configurable hasta 1000) |

- **Scale to zero:** con `min-replicas 0` no pagas cómputo cuando no hay tráfico, a cambio de un *cold start* en la primera solicitud.
- **Mensaje clave:** con `min-replicas 1` la latencia es estable y la app nunca se apaga, pero pagas siempre.

## 3. Tipos de reglas de escalado

| Tipo | Métrica | Caso de uso |
|---|---|---|
| **HTTP** | Solicitudes concurrentes por réplica (por defecto 10) | APIs web |
| **TCP** | Conexiones concurrentes | Servicios TCP no HTTP |
| **Custom (KEDA)** | Cualquier scaler de KEDA: Service Bus, Storage Queue, Event Hubs, Kafka, Redis, etc. | Workers y procesamiento asíncrono |
| **CPU / Memoria** | Uso de recursos | Cargas intensivas de cómputo. **No pueden escalar a 0.** |

- Una app puede tener **varias reglas**. Escala cuando cualquiera de ellas lo pide, y se queda con el número de réplicas más alto que calcule alguna.
- Si no defines ninguna regla, Container Apps aplica una **regla HTTP por defecto** (si hay ingress).

## 4. Cómo calcula las réplicas

Fórmula simplificada para HTTP:

```text
réplicas = ceil(solicitudes concurrentes totales / concurrencia objetivo)
```

Ejemplo: 50 solicitudes concurrentes con una concurrencia de 10 dan **5 réplicas**, siempre dentro de los límites min/max.

## 5. Comportamiento en el tiempo

- **Polling interval (30 s):** cada cuánto KEDA consulta el origen de eventos.
- **Cooldown period (300 s):** cuánto espera después del último evento antes de bajar al mínimo o a 0.
- **Escala rápido hacia arriba y lento hacia abajo.** Es intencional, para evitar *flapping*.
- La reducción gradual de N réplicas a menos la maneja el HPA, con una ventana de estabilización que no se configura.

```text
t=0s      llegan 100 mensajes a la cola
t<=30s    polling detecta la carga -> escala de 0 a N réplicas
...       se procesan los mensajes
t=X       la cola queda vacía (último evento)
t=X+300s  termina el cooldown -> escala a min-replicas (ej. 0)
```

## 6. Autenticación de los scalers

- Las reglas custom necesitan credenciales para leer la métrica (por ejemplo, la longitud de la cola).
- Opción recomendada: **identidad administrada** (`--scale-rule-identity`). La alternativa es guardar el connection string como un **secret** de la app y referenciarlo desde la regla.

## 7. Comandos clave

```bash
# Límites y regla HTTP
az containerapp update -n <app> -g <rg> \
  --min-replicas 0 --max-replicas 10 \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 10

# Ver réplicas en vivo
az containerapp replica list -n <app> -g <rg> -o table
```

## 8. Buenas prácticas y preguntas frecuentes del examen

- APIs con usuarios: **HTTP con min ≥ 1** si importa la latencia.
- Workers de cola: **regla KEDA de cola con min 0**, para ahorrar costo.
- La concurrencia objetivo se ajusta midiendo cuánto aguanta **una** réplica.
- Con CPU/Memoria no hay *scale to zero*. Si el escenario pide 0, la respuesta es HTTP o eventos.
- Cambiar las reglas crea una revisión nueva.
- Ojo con `max-replicas`: protege el costo y también los sistemas de los que depende la app (bases de datos, APIs con límites de llamadas).

## 9. Demo sugerida (lab 06)

Lab: [labs/06-aca-scale-python](labs/06-aca-scale-python/)

1. Mostrar la app con min = max = 1: con carga, la latencia sube porque no puede escalar.
2. Cambiar a min 0 o 1, max 10, con una regla HTTP de concurrencia baja (por ejemplo, 5).
3. Lanzar carga desde el `client` contra `/agent/process` y mirar `replica list` en vivo.
4. Detener la carga y mostrar que las réplicas bajan unos 5 minutos después (cooldown).
5. Opcional: bajar el cooldown a 60 s para que la reducción se vea dentro del tiempo de clase.

## 10. Parámetros del generador de carga (client)

El dashboard de [labs/06-aca-scale-python/client](labs/06-aca-scale-python/client/) tiene tres parámetros.

### Concurrency (concurrencia)

**Cuántos "usuarios virtuales" mandan solicitudes en paralelo.**

- El cliente crea esa cantidad de *workers* asíncronos.
- Cada worker funciona en bucle: manda un `POST`, **espera la respuesta** y recién ahí manda el siguiente. Cada worker tiene una sola solicitud abierta a la vez.
- Por eso, **concurrency = número de solicitudes simultáneas** que llegan a la app. Es justo la métrica que mide la regla de escalado HTTP.
- Rango: 1 a 500. Por defecto: 25.

### Duration (sec) (duración)

**Cuánto tiempo dura la prueba de carga.**

- Los workers siguen mandando solicitudes hasta que se cumple ese tiempo o se presiona Stop.
- Rango: 1 a 600 s. Por defecto: 30 s.

### delayMs (per request) (retardo por solicitud)

**Cuánto tarda la API en "procesar" cada solicitud.**

- El cliente lo manda en el cuerpo del request (`{"delayMs": 500}`) y la API hace un `time.sleep(delayMs)` antes de responder. Así simula un agente de IA o un LLM lento.
- Un retardo más alto mantiene cada solicitud abierta más tiempo, y la carga concurrente se nota más.
- Rango: 0 a 30 000 ms. Por defecto: 500 ms.

### Cómo se relacionan con el escalado

```text
solicitudes simultáneas  ≈ concurrency
réplicas esperadas       ≈ ceil(concurrency / http-concurrency de la regla)
throughput aproximado    ≈ concurrency × (1000 / delayMs)  req/s
```

Ejemplo con una regla HTTP de concurrencia **10**:

| concurrency | delayMs | Simultáneas | Réplicas esperadas | req/s aprox. |
|---|---|---|---|---|
| 25 | 500 | 25 | 3 | 50 |
| 50 | 1000 | 50 | 5 | 50 |
| 100 | 2000 | 100 | 10 (si max ≥ 10) | 50 |

### Tips para la demo

- **No uses `delayMs` en 0 o muy bajo.** Las solicitudes terminan tan rápido que casi no se acumulan, y el escalado puede no notarse.
- **Sube Duration a 120–300 s.** Con 30 s, a veces la prueba termina antes de que se note el escalado: hace falta tiempo para detectar la carga y arrancar las réplicas nuevas.
- Para mostrar el "antes y después", usa los mismos valores con `max-replicas 1` (la latencia sube y algunas solicitudes fallan por timeout) y después con `max-replicas 10`.
