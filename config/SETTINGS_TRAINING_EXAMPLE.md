# Training v1.4.0 - Settings.json példa

## Új struktúra (v1.4.0):

Minden épület (barracks, archery, stable, siege) konfigurációjában 
most már megadható a **tier** és **level** is!

```json
{
  "training": {
    "buildings": {
      "barracks": {
        "enabled": true,
        "tier": "t4",
        "level": "level_3"
      },
      "archery": {
        "enabled": true,
        "tier": "t5",
        "level": "level_1"
      },
      "stable": {
        "enabled": true,
        "tier": "t4",
        "level": "level_2"
      },
      "siege": {
        "enabled": false,
        "tier": "t4",
        "level": "level_1"
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

## Level opciók:
- `"level_1"` - Farm level 1 (default)
- `"level_2"` - Farm level 2
- `"level_3"` - Farm level 3
- `"level_4"` - Farm level 4
- `"level_5"` - Farm level 5

## Példák:

### 1. Csak T4 katonák, level 1
```json
{
  "barracks": {
    "enabled": true,
    "tier": "t4",
    "level": "level_1"
  }
}
```

### 2. T5 katonák, level 3 farm
```json
{
  "archery": {
    "enabled": true,
    "tier": "t5",
    "level": "level_3"
  }
}
```

### 3. Különböző tier-ek épületenként
```json
{
  "barracks": {"enabled": true, "tier": "t4", "level": "level_1"},
  "archery": {"enabled": true, "tier": "t5", "level": "level_2"},
  "stable": {"enabled": true, "tier": "t4", "level": "level_3"},
  "siege": {"enabled": false, "tier": "t4", "level": "level_1"}
}
```

## FONTOS:
- A `tier` és `level` koordinátákat a **setup wizard**-ban kell beállítani!
- Ha egy tier vagy level nincs beállítva a `training_coords.json`-ban, 
  a bot fallback-re vált vagy skip-eli a lépést.
- Default értékek: tier=t4, level=level_1
