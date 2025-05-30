import struct
from typing import Any, Dict, Iterator, List, Optional, Tuple

from replay_parser.exception import InvalidReplay
from replay_parser.commands import COMMAND_PARSERS
from replay_parser.constants import CommandStateNames, CommandStates
from replay_parser.reader import ACCEPTABLE_DATA_TYPE, ReplayReader

__all__ = ('ReplayBody',)


class ReplayBody:
    """
    Parses replay body.
    """
    def __init__(
            self,
            reader: ReplayReader,
            stop_on_desync: bool = False,
            parse_commands: set = None,
            store_body: bool = False,
            **kwargs
    ) -> None:
        """
        :param ReplayReader reader: Handles basic operations on stream
        :param bool stop_on_desync: stops parsing at first desync
        :param set parse_commands: set or list of commands ids to parse,
            list is defined in from `replay_parser.commands.COMMAND_PARSERS`.
            Important: you can't detect desyncs, if you won't have CommandStates.VerifyChecksum
        :param bool store_body: stores every next tick data of replay to content to self.body.
            To get list of commands use get_body
        """
        self.replay_reader: ReplayReader = reader
        self.command_reader: ReplayReader = ReplayReader()

        self.body: List = []
        self.last_players_tick: Dict = {}
        self.desync_ticks: List = []
        self.messages: Dict = {}

        self.tick: int = 0
        self.tick_data: Dict = {}
        self.player_id: int = -1

        self.previous_tick = -1
        self.previous_checksum = None

        self.stop_on_desync = bool(stop_on_desync)
        self.parse_commands = set(parse_commands or set())
        self.store_body = bool(store_body)

    def get_body(self) -> List:
        return self.body

    def get_messages(self) -> Dict:
        return self.messages

    def get_last_players_ticks(self) -> Dict:
        return self.last_players_tick

    def get_desync_ticks(self) -> List:
        return self.desync_ticks

    def parse(self) -> None:
        """
        Parses all replay data
        """
        for _ in self.continuous_parse():
            pass

    def continuous_parse(self, data: ACCEPTABLE_DATA_TYPE = None) -> Iterator:
        """
        Parses commands until it can. Should be used as iterator.
        Yields game tick, command_type and command_data.

        replay format:
            1. byte for command 0 - 23
            2. 2 bytes for size of command 3 - 65535
            3. content of command - binary stuff for `parse_next_command`
        """
        if data:
            self.replay_reader.set_data(data)

        buffer_size = self.replay_reader.size()
        while self.replay_reader.offset() + 3 <= buffer_size:
            command_type, command_data = self.parse_command_and_get_data()
            yield self.tick, command_type, command_data, self.command_unpacked

    def parse_command_and_get_data(self) -> Tuple[Optional[int], Optional[bytes]]:
        """
        Parses one command and returns its type and binary data for whole command

        Packet structure in bytestream
        ::
            char "=" is one byte

            4   7      7      7
            TLLDTLLDDDDTLLDDDDTLLDDDD
            =========================

        Where:
        ::
            T - byte - defines command type
            L - short - defines command length of T + L + D
            D - variable length - binary data, size it is in `command length`, may be empty
        """
        # seek preventing
        command_type_byte = self.replay_reader.read(1)
        command_length_byte = self.replay_reader.read(2)

        command_type = struct.unpack("B", command_type_byte)[0]
        command_length = struct.unpack("<H", command_length_byte)[0]

        data = self.replay_reader.read(command_length - 3)

        if self.can_parse_next_command(command_type):
            self.parse_next_command(command_type, data)

        return command_type, command_type_byte + command_length_byte + data

    def parse_next_command(self, command_type: int, data: bytes) -> None:
        """
        Parses one command from buffer.
        """
        self.command_reader.set_data_from_bytes(data)
        try:
            command_parser = COMMAND_PARSERS[command_type]
        except Exception as e:
            raise InvalidReplay(e)

        command_data = command_parser(self.command_reader)
        self.process_command(command_type, command_data)

    def process_command(self, command_type: int, command_data: Any) -> None:
        """
        Defines operations over some of commands, handles tick counter,
        check sum validity, players messages, some logic interactions between commands.
        """
        command_name = CommandStateNames[command_type]

        if command_type == CommandStates.Advance:
            if self.store_body and self.tick_data:
                self.body.append(self.tick_data)
            self.tick_data = {}
            self.tick += command_data["advance"]

        elif command_type == CommandStates.SetCommandSource:
            self.player_id = command_data["player_id"]

        elif command_type == CommandStates.CommandSourceTerminated:
            self.last_players_tick[self.player_id] = self.tick

        elif command_type == CommandStates.VerifyChecksum:
            checksum, tick = command_data["checksum"], command_data["tick"]
            if tick == self.previous_tick and checksum != self.previous_checksum:
                if self.stop_on_desync:
                    raise StopIteration()

                self.desync_ticks.append(self.tick)
            self.previous_tick = tick
            self.previous_checksum = checksum

        elif command_type == CommandStates.LuaSimCallback:
            cmd_string, data = command_data["lua_name"], command_data["lua"]
            if cmd_string == "GiveResourcesToPlayer" and "Msg" in data:
                self.messages[self.tick] = (data["Sender"], data["Msg"]["to"], data["Msg"]["text"])
        
        self.command_unpacked = command_data

        if self.store_body:
            self.tick_data.setdefault(self.player_id, {})[command_name] = command_data

    def can_parse_next_command(self, command_type: int):
        """
        Runs per command
        """
        return not self.parse_commands or command_type in self.parse_commands
