# a50x-balance-lock

Lock the game/chat balance of the **Logitech G / Astro A50 X** headset on Windows.

The A50 X has two game/chat balance buttons on the back of the right ear cup. They are easy to press by accident, which suddenly fades out the game or the chat, and Logitech G HUB offers no setting to disable them. This tool listens to the headset over USB and, whenever the balance moves, sets it straight back to the value you chose (centre by default) in under 100 ms.

## Features

- Reverts any balance change from the ear-cup buttons in under 100 ms.
- Small settings window to pick the locked balance (0 = all chat, 12 = all game) or turn the lock off.
- Settings apply instantly; no restart needed.
- Survives the headset being switched off or the base station being unplugged, and reapplies the balance on reconnect.
- Runs alongside G HUB; both share the device without conflict.
- No admin rights, no drivers, no background service beyond a scheduled task.

## Requirements

- Windows 10 or 11.
- Astro A50 X connected over USB (base station or USB adapter).
- [uv](https://docs.astral.sh/uv/getting-started/installation/). On first run it fetches Python and the `hidapi` package automatically.

## Quick start

```powershell
git clone https://github.com/pabloski2300/a50x-balance-lock.git
cd a50x-balance-lock

# Start the lock (keeps a console window open; see below to run it hidden at logon)
uv run --script a50x_balance_lock.py
```

Press either balance button on the headset: the audio should stay put. Every correction is logged to `a50x_balance_lock.log`.

## Settings window

```powershell
uv run --script ajustes.py
```

The window lets you:

- Choose the locked balance with a slider, from **0 (all chat)** to **12 (all game)**; **6** is the centre, with both at full volume.
- Turn the button lock on or off without stopping anything.

Click **Guardar** (Save) and the running lock applies the change within a second. The window's labels are in Spanish: *Chat* / *Juego* (game), *Centrar* (centre), *Guardar* (save), *Bloquear los botones del casco* (lock the headset buttons).

Settings are stored in `config.json` next to the scripts:

```json
{
  "target": 6,
  "enabled": true
}
```

If the file is missing, the lock defaults to the centre (6) and is enabled.

## Run automatically at logon

Create a scheduled task that starts the lock hidden (via `uvw`) every time you sign in, and restarts it if it ever crashes. Run this in PowerShell from the repository folder; no admin rights are required:

```powershell
$dir = (Resolve-Path .).Path
$uvw = (Get-Command uvw).Source
$action = New-ScheduledTaskAction -Execute $uvw -Argument "run --script `"$dir\a50x_balance_lock.py`"" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'A50X Balance Lock' -Action $action -Trigger $trigger -Settings $settings
Start-ScheduledTask -TaskName 'A50X Balance Lock'
```

To remove it:

```powershell
Unregister-ScheduledTask -TaskName 'A50X Balance Lock' -Confirm:$false
```

Optionally, add a Start menu shortcut for the settings window:

```powershell
$s = (New-Object -ComObject WScript.Shell).CreateShortcut("$([Environment]::GetFolderPath('Programs'))\A50 X Balance.lnk")
$s.TargetPath = (Get-Command uvw).Source
$s.Arguments = "run --script `"$((Resolve-Path .\ajustes.py).Path)`""
$s.WorkingDirectory = (Resolve-Path .).Path
$s.Save()
```

## Good to know

- While the lock is enabled, the balance slider in G HUB is reverted too. To use it, turn the lock off in the settings window.
- Pressing both buttons at once makes the headset step the balance back and forth, which sounds choppy. With the lock enabled, that is corrected immediately.
- Tested on the A50 X (USB product ID `0B0B`) on Windows 11. Other Astro models use different hardware and protocols and are not supported.

## How it works

The protocol was found by hooking `lghub_agent.exe` with [Frida](https://frida.re/) and recording what G HUB writes to the headset when the balance slider moves.

The A50 X exposes a single vendor-defined HID collection: VID `046D`, PID `0B0B`, interface 8, usage page `0xFF32`. It uses report ID `0x02`, with 64-byte reports in both directions:

| Direction | Bytes | Meaning |
|---|---|---|
| PC → headset | `02 0c 04 00 0a 1b VV` | Set the balance to `VV` |
| headset → PC | `02 0c 03 00 0a 1b` | Acknowledgement |
| headset → PC | `02 0c 04 00 0a 00 VV` | The balance changed to `VV` |

`VV` ranges from `0x00` (all chat) to `0x0c` (all game), with `0x06` as the centre. On the headset, the front button (chat) lowers the value and the rear button (game) raises it. Reports are zero-padded to 64 bytes.

The lock reads these change notifications and answers any value other than the target with a *set balance* command.

## Disclaimer

This is an unofficial project, not affiliated with or endorsed by Logitech or Astro Gaming. It only sends the same command G HUB itself sends, but use it at your own risk.

## License

[MIT](LICENSE)
