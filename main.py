from io import BytesIO
from io import FileIO
import zstandard
import argparse
import json

from replay_parser.constants import CommandStates
from replay_parser.body import ReplayBody
from replay_parser.reader import ReplayReader
from replay_parser.header import ReplayHeader
from replay_parser.replay import continuous_parse, parse

parser = argparse.ArgumentParser(prog='fafreplay',description='Unpack compressed replay into the .csv file')
parser.add_argument("fafreplay")
parser.add_argument("outputcsv")
args = parser.parse_args()
fafreplay = FileIO(args.fafreplay, "rb")
faf_header = fafreplay.readline()
zdata = fafreplay.read()
dctx = zstandard.ZstdDecompressor()
dobj = dctx.decompressobj(write_size=8100200)
data = dobj.decompress(zdata)

repstream = continuous_parse(data, parse_header=True)

# skip header
next(repstream)

outcsv = open(args.outputcsv,"w",encoding='utf8')
outcsv.write("tick\tcmd\tdata\n")
for tick, cmd, cmd_data, cmd_dict in repstream:
    # skip advance command spam
    if cmd == CommandStates.Advance: continue
    outcsv.write("%(tick)f\t%(cmd)d\t%(data)s\n" % {"tick":tick/10.0, "cmd":cmd, "data": json.dumps(cmd_dict)})
