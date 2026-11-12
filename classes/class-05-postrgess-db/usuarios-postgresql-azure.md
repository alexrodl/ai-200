# Usuarios y permisos en Azure Database for PostgreSQL

Crear acceso a la base siempre tiene **dos pasos**:

1. **Crear el usuario (login)**: define *cómo* se autentica (contraseña o Entra ID).
2. **Dar permisos**: define *qué* puede hacer. Esto es igual para ambos tipos de usuario.

```
Usuario (login)  ──►  Rol de grupo  ──►  Permisos sobre tablas
```

---

## 1. Usuario común (con contraseña)

Es SQL estándar de PostgreSQL. Lo puede crear el administrador del servidor.

```sql
CREATE ROLE app_reportes WITH LOGIN PASSWORD 'CambiarEsta_Pa55!';
```

- La contraseña se guarda en **Azure Key Vault**, nunca en el código.
- Conexión:

```bash
psql "host=myserver.postgres.database.azure.com dbname=ventas user=app_reportes sslmode=require"
```

---

## 2. Usuario de Microsoft Entra ID o managed identity

No hay contraseña: el usuario presenta un **token de Entra** en el campo de contraseña.

### Requisitos previos

- Autenticación del servidor en modo **PostgreSQL y Microsoft Entra**.
- Un **administrador de Entra** configurado en el servidor.

### Crear el usuario

Conectado **como administrador de Entra** a la base **`postgres`** (la función solo funciona en esa base):

```sql
-- Usuario humano: se usa su UPN
SELECT * FROM pgaadauth_create_principal('ana@contoso.com', false, false);

-- Managed identity de una app: se usa el nombre de la identidad
SELECT * FROM pgaadauth_create_principal('mi-webapp-ventas', false, false);
```

| Parámetro | Significado |
|---|---|
| 1º | Nombre del usuario o identidad |
| 2º | `isAdmin` (¿es administrador?) |
| 3º | `isMfa` (¿exige MFA?) |

> Para **grupos de Entra** o nombres ambiguos se usa `pgaadauth_create_principal_with_oid`, que identifica al principal por su Object ID.

### Conectarse

```bash
export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
psql "host=myserver.postgres.database.azure.com dbname=ventas user=ana@contoso.com sslmode=require"
```

Una app con managed identity hace lo mismo desde código (por ejemplo con `DefaultAzureCredential`): pide el token y lo usa como contraseña.

---

## Comparación rápida

| | Usuario común | Entra ID / managed identity |
|---|---|---|
| Cómo se crea | `CREATE ROLE ... LOGIN PASSWORD` | `pgaadauth_create_principal(...)` |
| Quién lo crea | Administrador del servidor | Administrador de Entra |
| En qué base | Cualquiera | Solo en `postgres` |
| Credencial | Contraseña (en Key Vault) | Token temporal (~1 hora) |
| Rotación | Manual | Automática |

---

## 3. Permisos (igual para ambos tipos)

Conectado a la base `ventas`. Los permisos se asignan a **roles de grupo**, y los usuarios se agregan a esos grupos.

```sql
-- Roles de grupo (sin login)
CREATE ROLE ventas_lectura NOLOGIN;
CREATE ROLE ventas_escritura NOLOGIN;

-- Acceso a la base y al esquema
GRANT CONNECT ON DATABASE ventas TO ventas_lectura, ventas_escritura;
GRANT USAGE ON SCHEMA public TO ventas_lectura, ventas_escritura;

-- Tablas existentes
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ventas_lectura;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ventas_escritura;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ventas_escritura;

-- Tablas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ventas_lectura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ventas_escritura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO ventas_escritura;

-- Asignar usuarios a los grupos
GRANT ventas_escritura TO "mi-webapp-ventas";
GRANT ventas_lectura   TO "ana@contoso.com", app_reportes;
```

Verificar con `\du` en psql.

### Puntos a recordar

- Los nombres de Entra llevan **comillas dobles** en SQL (por el `@` y los guiones).
- `ALTER DEFAULT PRIVILEGES` solo aplica a objetos creados por el rol que lo ejecutó. Si las tablas las crea otro rol, usar `FOR ROLE <rol>`.
- Recomendación de producción: **managed identity** para apps y **grupos de Entra** para personas; contraseñas solo cuando no hay alternativa.
