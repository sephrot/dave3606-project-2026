import struct
import sys

def read_string(data, offset):
    length = struct.unpack(">H", data[offset:offset+2])[0]
    text = data[offset+2:offset+2+length].decode("utf-8")
    return text, offset + 2 + length

with open(sys.argv[1], "rb") as f:
    data = f.read()

offset = 0
set_id, offset = read_string(data, offset)
name, offset = read_string(data, offset)
year = struct.unpack(">H", data[offset:offset+2])[0]
offset += 2
category, offset = read_string(data, offset)
num_bricks = struct.unpack(">I", data[offset:offset+4])[0]
offset += 4

print(f"Set: {set_id} - {name} ({year})")
print(f"Category: {category}")
print(f"Inventory ({num_bricks} bricks):")

for _ in range(num_bricks):
    brick_type_id, offset = read_string(data, offset)
    color_id = struct.unpack(">H", data[offset:offset+2])[0]
    offset += 2
    count = struct.unpack(">H", data[offset:offset+2])[0]
    offset += 2
    print(f"  - {brick_type_id} (color {color_id}): {count} stk")