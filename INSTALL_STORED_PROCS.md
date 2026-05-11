# Stored Procedure Installation Guide

## Install Using Python Script (Recommended)

```bash
source venv/bin/activate && python3 /Users/benskan/Documents/ClaudeDev/install_stored_procs.py
```

## Install Using MySQL CLI

```bash
mysql -u supremacy supremacy_game < /Users/benskan/Documents/ClaudeDev/stored_procs_simple.sql
```

## Verify Installation

```bash
mysql -u supremacy supremacy_game -e "SHOW PROCEDURE STATUS WHERE Db='supremacy_game';"
```

---

The stored procedure `process_player_turns_batch` will process all of your player's planets in a single batch UPDATE, including:
- Food production/consumption
- Energy production/consumption
- Fuel generation from mining
- Population growth (morale-based) or starvation decline
