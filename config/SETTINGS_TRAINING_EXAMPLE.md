# Training v1.4.0 - Settings.json példa

## Új struktúra (v1.4.0):

Minden épület (barracks, archery, stable, siege) konfigurációjában 
most már megadható a **tier**!

```json
{
  "training": {
    "buildings": {
      "barracks": {
        "enabled": true,
        "tier": "t4"
      },
      "archery": {
        "enabled": true,
        "tier": "t5"
      },
      "stable": {
        "enabled": true,
        "tier": "t4"
      },
      "siege": {
        "enabled": false,
        "tier": "t4"
      }
    }
  }
}
```

## Tier opciók:
- `"t1"` - Tier 1
- `"t2"` - Tier 2
- `"t3"` - Tier 3
- `"t4"` - Tier 4 (default)
- `"t5"` - Tier 5

## Példák:

### 1. Csak T4 katonák
```json
{
  "barracks": {
    "enabled": true,
    "tier": "t4"
  }
}
```

### 2. T5 katonák
```json
{
  "archery": {
    "enabled": true,
    "tier": "t5"
  }
}
```

### 3. Különböző tier-ek épületenként
```json
{
  "barracks": {"enabled": true, "tier": "t4"},
  "archery": {"enabled": true, "tier": "t5"},
  "stable": {"enabled": true, "tier": "t4"},
  "siege": {"enabled": false, "tier": "t4"}
}
```

## FONTOS:
- A `tier` koordinátákat a **setup wizard**-ban kell beállítani!
- Ha egy tier nincs beállítva a `training_coords.json`-ban, 
  a bot fallback-re vált a régi 'tier' kulcsra.
- Default érték: tier=t4
