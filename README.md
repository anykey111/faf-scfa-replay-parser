# Supreme Commander Forged alliance replay parser

Usage
-----

Ensure that zstandard dependency is installed

    pip install zstandard

Convert compressed replay file into the .csv table

    python main.py 24835293.fafreplay replay.csv

Load replay.csv as sqlite database

```
    sqlite3 -cmd "create table replay(tick float, cmd int, data text)" -cmd ".mode tab" -cmd ".import replay.csv replay"

    > select * from replay where cmd = 23;
1166.6  23      {"type": "end_game"}

    >select * from replay where
        cmd = 22
        and json_extract(data,'$.lua_name') = 'GiveResourcesToPlayer'
        and json_extract(data,'$.lua.Msg.text') = 'Starting T2';

436.6   22      {"type": "lua_sim_callback", "lua_name": "GiveResourcesToPlayer", "lua": {"Mass": 0.0, "To": 3.0, "From": 3.0, "Msg": {"to": "notify", "text": "Starting T2", "data": {"trigger": "started", "source": "AdvancedEngineering", "category": "uef"}, "Chat": true}, "Energy": 0.0, "Sender": "PlayerName"}, "size": 1, "data": "73002000"}
```
