# Supreme Commander Forged alliance replay parser

Usage
-----

Ensure that zstandard dependency is installed

    pip install zstandard

Convert compressed replay file into the .csv table

    python main.py 24835293.fafreplay replay.csv

Load replay.csv as sqlite database

- `tick` seconds from the start (each tick is equal to 100msec)
- `cmd`  is numeric constant from constatns.py:CommandStates
- `data` is Json structure of the command

```
    sqlite3 -cmd "create table replay(tick float, cmd int, data text)" -cmd ".mode tab" -cmd ".import replay.csv replay"

    > select * from replay where cmd = 23;
1166.6  23      {"type": "end_game"}

    >select * from replay where
        cmd = 22
        and json_extract(data,'$.lua_name') = 'GiveResourcesToPlayer'
        and json_extract(data,'$.lua.Msg.text') = 'Starting T2';

436.6   22      {"type": "lua_sim_callback", "lua_name": "GiveResourcesToPlayer", "lua": {"Mass": 0.0, "To": 3.0, "From": 3.0, "Msg": {"to": "notify", "text": "Starting T2", "data": {"trigger": "started", "source": "AdvancedEngineering", "category": "uef"}, "Chat": true}, "Energy": 0.0, "Sender": "PlayerName"}, "size": 1, "data": "73002000"}

    
    -- "xsa0304": "T3 Strategic Bomber: Sinntha"
    -- "uea0304": "T3 Strategic Bomber: Ambassador"
    -- "uaa0304": "T3 Strategic Bomber: Shocker"
    -- "ura0304": "T3 Strategic Bomber: Revenant"
    -- Find if someone is queued strat before min 11

    >select * from replay where
        cmd = 12 
        and tick < 11*60
        and json_extract(data,'$.cmd_data.command_type') = 7
        and json_extract(data,'$.cmd_data.blueprint_id') in ('xsa0304','uea0304','uaa0304','ura0304');
    
36.0 12 {'type': 'issue', 'entity_ids_set': {'units_number': 1, 'unit_ids': [2]}, 'cmd_data': {'command_id': 0, 'command_type': 7, 'target': {'target': 0, 'entity_id': 'null', 'position': 'null'}, 'formation': 'null', 'blueprint_id': 'xsa0304', 'cells': '', 'arg1': -1, 'arg2': -1, 'arg3': 0, 'arg4': [0, 1, 1], 'arg5': ''}}
```
