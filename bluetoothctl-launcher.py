#!/usr/bin/env python

import subprocess
import sys
from typing import Optional

class Device:
    def __init__(self, name: str, id: str, connected: bool, paired: bool, trusted: bool):
        self.name = name
        self.id = id
        self.connected = connected
        self.paired = paired
        self.trusted = trusted

    def __str__(self):
        return f"{self.name} [{self.id}] ({'Connected' if self.connected else 'Disconnected'})"

def spawn_fzf(input: str) -> Optional[str]:
    try:
        result = subprocess.run(["fzf"], input=input, stdout=subprocess.PIPE, check=True, encoding="utf-8")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if e.returncode == 130:
            return None
        else:
            raise

def get_devices() -> list[Device]:
    result = subprocess.run(["bluetoothctl", "devices"], capture_output=True, check=True, encoding="utf-8")
    devices = []
    for d in result.stdout.strip().splitlines():
        _, id, name = d.split(' ', maxsplit=2)
        status = subprocess.run(["bluetoothctl", "info", id], capture_output=True, check=True, encoding="utf-8")
        connected = status.stdout.find('Connected: yes') != -1
        paired = status.stdout.find('Paired: yes') != -1
        trusted = status.stdout.find('Trusted: yes') != -1
        devices.append(Device(name, id, connected, paired, trusted))
    return devices

def select_device_via_menu(devices: list[Device]) -> Optional[Device]:
    input = "\n".join([str(d) for d in devices])
    selected_device = spawn_fzf(input)
    if selected_device == None:
        return None
    for d in devices:
        if selected_device == str(d):
            return d
    return None

def select_action_via_menu(device: Device) -> Optional[str]:
    actions = [
        "Disconnect" if device.connected else "Connect",
        "Remove" if device.paired else "Pair",
        "Untrust" if device.trusted else "Trust",
    ]
    input = "\n".join(actions)
    selected_action = spawn_fzf(input)
    return selected_action

def perform_action(selected_device: Device, action: str):
    commands = {
        "Disconnect": ["bluetoothctl", "disconnect", selected_device.id],
        "Connect": ["bluetoothctl", "connect", selected_device.id],
        "Trust": ["bluetoothctl", "trust", selected_device.id],
        "Untrust": ["bluetoothctl", "untrust", selected_device.id],
        "Pair": ["bluetoothctl", "pair", selected_device.id],
        "Remove": ["bluetoothctl", "remove", selected_device.id],
    }
    command = commands[action]
    subprocess.run(command, check=True, encoding="utf-8")

if __name__ == "__main__":
    while True:
        try:
            devices = get_devices()
            selected_device = select_device_via_menu(devices)
            if selected_device == None:
                exit(0)
            selected_action = select_action_via_menu(selected_device)
            if selected_action == None:
                continue
            perform_action(selected_device, selected_action)
            break
        except subprocess.CalledProcessError as e:
            print(f"Error spawning process:\n\tcode: {e.returncode}\n\tstderr: {e.stderr}\n\tstdout: {e.stdout}\nPress Enter to continue", file=sys.stderr)
            input()
    
