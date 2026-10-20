# Environment Setup

## Antes del curso

Prepara una estación de desarrollo y una suscripción autorizada. Consulta [Prerequisites](../prerequisites/README.md), [Azure setup](../prerequisites/azure.md) y [Tools setup](../prerequisites/tools.md).

## Lista de comprobación

1. Confirma tenant, suscripción, permisos, cuota y regiones con el instructor.
2. Instala Azure CLI, Git y Visual Studio Code.
3. Instala Python y sus paquetes según la práctica.
4. Instala `kubectl` antes del módulo de AKS.
5. Revisa los requerimientos específicos de cada laboratorio antes de iniciarlo.

## Validación rápida

Ejecuta los comandos disponibles en tu entorno:

```bash
az version
git --version
python --version
kubectl version --client
```

`kubectl` solo es necesario para el módulo de AKS. La versión de Python y los paquetes pueden variar; utiliza la especificada en las instrucciones oficiales del ejercicio.

## Recomendaciones de operación

- Mantén el entorno de laboratorio separado de producción.
- Usa nombres de recursos únicos siguiendo las convenciones del instructor.
- No guardes secretos en el repositorio, historial de terminal ni capturas.
- Prevé tiempo para eliminar los recursos al terminar cada lab.

## Troubleshooting

Si `az` no está reconocido:

- Reinstala Azure CLI.
- Cierra y vuelve a abrir la terminal.
- Verifica que la ruta de instalación esté en el `PATH`.

Si la suscripción o un recurso no aparece:

- Verifica tenant y suscripción seleccionados con Azure CLI.
- Comprueba permisos, región, cuota y políticas organizativas.
- Consulta [Troubleshooting](../troubleshooting/README.md) antes de repetir un despliegue que pueda crear recursos duplicados.
