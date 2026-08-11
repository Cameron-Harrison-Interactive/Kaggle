#!/usr/bin/env python3
"""Generate submit/main.py with specified tapes."""
import json, base64, zlib, sys, ast

DATA = '/home/user/kaggriculture/V18 - Adapt-2-Survive/data'
OUTPUT = '/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py'

s0_seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
s1_seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5

print(f"Generating agent with seat0=seed{s0_seed}, seat1=seed{s1_seed}")

with open(f'{DATA}/route_v18_opt_seat0_s{s0_seed}.json') as f:
    s0_tape = json.load(f)
with open(f'{DATA}/route_v18_opt_seat1_s{s1_seed}.json') as f:
    s1_tape = json.load(f)

print(f"Loaded: seat0={len(s0_tape)} actions, seat1={len(s1_tape)} actions")

s0_enc = base64.b85encode(zlib.compress(json.dumps(s0_tape).encode())).decode('ascii')
s1_enc = base64.b85encode(zlib.compress(json.dumps(s1_tape).encode())).decode('ascii')

print(f"Encoded: s0={len(s0_enc)} chars, s1={len(s1_enc)} chars")

with open(OUTPUT) as f:
    template = f.read()

def format_tape_string(encoded: str, chunk_size: int = 90) -> str:
    lines = []
    for i in range(0, len(encoded), chunk_size):
        chunk = encoded[i:i+chunk_size]
        lines.append(f"    '{chunk}'")
    return '\n'.join(lines)

def find_tape_bounds_lines(template: str, seat_num: int):
    """Find tape data bounds using line-based parsing."""
    lines = template.split('\n')
    
    # Find the marker line
    marker = f'_SEAT{seat_num}_ACTIONS = json.loads(zlib.decompress(base64.b85decode('
    marker_line_idx = None
    for i, line in enumerate(lines):
        if marker in line:
            marker_line_idx = i
            break
    
    if marker_line_idx is None:
        return None, None, None, None
    
    print(f"SEAT{seat_num}: marker at line {marker_line_idx}")
    
    # Find the line with just '    (' (start of tuple)
    tuple_open_idx = None
    for i in range(marker_line_idx + 1, len(lines)):
        if lines[i].strip() == '(':
            tuple_open_idx = i
            break
    
    if tuple_open_idx is None:
        return None, None, None, None
    
    print(f"SEAT{seat_num}: tuple open at line {tuple_open_idx}")
    
    # Find the line with just '    )' (end of tuple)
    tuple_close_idx = None
    for i in range(tuple_open_idx + 1, len(lines)):
        if lines[i].strip() == ')':
            tuple_close_idx = i
            break
    
    if tuple_close_idx is None:
        return None, None, None, None
    
    print(f"SEAT{seat_num}: tuple close at line {tuple_close_idx}")
    
    # Calculate character positions
    # Data starts after the newline following '    ('
    data_start_line = tuple_open_idx + 1
    data_end_line = tuple_close_idx  # exclusive
    
    # Calculate byte positions
    prefix = '\n'.join(lines[:data_start_line]) + '\n'
    data_end_pos = len(prefix)
    
    # Find where data ends (before the '    )' line)
    data_content = '\n'.join(lines[data_start_line:data_end_line])
    
    # The suffix starts with '    )\n'
    suffix_start_line = data_end_line
    suffix = '\n'.join(lines[suffix_start_line:])
    
    return len(prefix), len(prefix) + len(data_content), prefix, suffix

def replace_tape_section(template: str, seat_num: int, new_encoded: str) -> str:
    start, end, prefix, suffix = find_tape_bounds_lines(template, seat_num)
    if start is None:
        return None
    
    print(f"SEAT{seat_num}: data bounds {start}-{end} ({end-start} chars)")
    
    new_tape_str = format_tape_string(new_encoded)
    return prefix + new_tape_str + '\n' + suffix

# Replace SEAT0
new_code = replace_tape_section(template, 0, s0_enc)
if new_code is None:
    sys.exit(1)

# Replace SEAT1 (on the modified code)
new_code = replace_tape_section(new_code, 1, s1_enc)
if new_code is None:
    sys.exit(1)

# Verify syntax
try:
    ast.parse(new_code)
    print("✓ Syntax OK")
except SyntaxError as e:
    print(f"✗ SyntaxError: {e}")
    lines = new_code.split('\n')
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
        print(f"  {i+1}: {lines[i][:120]}")
    sys.exit(1)

with open(OUTPUT, 'w') as f:
    f.write(new_code)

print(f"Written {OUTPUT}")
print(f"File size: {len(new_code):,} bytes")
