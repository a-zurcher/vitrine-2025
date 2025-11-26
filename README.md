# Vitrine 2025

## Librairies

Pour intéragir avec le PLC du robot KUKA, utiliser la librairie [pyads](https://pyads.readthedocs.io/en/latest/quickstart.html)

Le PLC tourne sur Windows 10 IOT

## Interrupteurs Tasmota

| Numéro | Adresse IP (réseau de l'Antenne) | Adresse MAC       |
| ------ | -------------------------------- | ----------------- |
| 1      | 172.22.22.11                     | 2c:bc:bb:d5:ec:18 |
| 2      | 172.22.22.12                     | 2c:bc:bb:d5:b5:ac |
| 3      | 172.22.22.13                     | 2c:bc:bb:d7:6d:cc |
| 4      | 172.22.22.14                     | 2c:bc:bb:d5:cc:64 |

Allumer un interrupteur: `<adresse_ip>/cm?cmnd=Power%20On`

Éteindre un interrupteur: `<adresse_ip>/cm?cmnd=Power%20Off`

Basculer on/off un interrupteur: `<adresse_ip>/cm?cmnd=Power%20TOGGLE`

```

```
