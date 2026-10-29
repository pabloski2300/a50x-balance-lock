# a50x-balance-lock

Bloquea el balance juego/chat de los **Logitech G / Astro A50 X** en Windows. Los botones del auricular derecho se pulsan fácilmente sin querer y dejas de oír el juego o el chat, y G HUB no permite desactivarlos. Este programa escucha el casco por USB y, en cuanto el balance se mueve, lo devuelve al valor que elijas (por defecto, el centro) en menos de 100 ms.

## Requisitos

- Windows 10/11 con el A50 X conectado por USB (base o adaptador).
- [uv](https://docs.astral.sh/uv/). Instala Python y `hidapi` solo la primera vez que se ejecuta.
- G HUB puede seguir abierto: los dos comparten el dispositivo sin conflicto.

## Uso

```powershell
# Bloqueo (deja una consola abierta; uvw lo ejecuta sin ventana)
uv run --script a50x_balance_lock.py

# Ventana de ajustes: balance de 0 (todo chat) a 12 (todo juego) y activar o desactivar el bloqueo
uv run --script ajustes.py
```

Los ajustes se guardan en `config.json` y el bloqueo los aplica al momento, sin reiniciar. Cada corrección queda registrada en `a50x_balance_lock.log`.

### Arranque automático al iniciar sesión

```powershell
$dir = (Resolve-Path .).Path
$uvw = (Get-Command uvw).Source
$action = New-ScheduledTaskAction -Execute $uvw -Argument "run --script `"$dir\a50x_balance_lock.py`"" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'A50X Balance Lock' -Action $action -Trigger $trigger -Settings $settings
```

Para quitarlo: `Unregister-ScheduledTask -TaskName 'A50X Balance Lock'`.

> Mientras el bloqueo esté activo, el control de balance de G HUB también se revierte. Para usarlo, desmarca el bloqueo en la ventana de ajustes.

## Protocolo

Se obtuvo capturando con Frida lo que `lghub_agent.exe` escribe en el casco. Interfaz HID `VID 046D / PID 0B0B`, interfaz 8, página de uso `0xFF32`, informe `0x02` de 64 bytes:

| Dirección | Bytes | Significado |
|---|---|---|
| PC → casco | `02 0c 04 00 0a 1b VV` | Fijar el balance a `VV` |
| casco → PC | `02 0c 03 00 0a 1b` | Confirmación |
| casco → PC | `02 0c 04 00 0a 00 VV` | El balance ha cambiado a `VV` |

`VV` va de `0x00` (todo chat) a `0x0c` (todo juego); el centro es `0x06`. El botón delantero (Chat) baja el valor y el trasero (Juego) lo sube.

## Licencia

MIT
