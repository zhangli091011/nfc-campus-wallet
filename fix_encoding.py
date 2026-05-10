"""Fix UTF-8 encoding issues in Python files."""
import os

def fix_utf8(data):
    result = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if 0xe0 <= b <= 0xef and i + 2 < len(data):
            b2 = data[i+1]
            b3 = data[i+2]
            if 0x80 <= b2 <= 0xBF:
                if 0x80 <= b3 <= 0xBF:
                    result.extend(data[i:i+3])
                    i += 3
                elif b3 == 0x3f:
                    if b == 0xe3 and b2 == 0x80:
                        result.extend(b'\xe3\x80\x82')
                    elif b == 0xef and b2 == 0xbc:
                        result.extend(b'\xef\xbc\x9a')
                    else:
                        result.extend(bytes([b, b2, 0x80]))
                    i += 3
                else:
                    result.append(b)
                    i += 1
            else:
                result.append(b)
                i += 1
        else:
            result.append(b)
            i += 1
    return bytes(result)

dirs = ['routes', 'services', 'core', 'models', 'schemas', 'middleware', 'app']
fixed = []
for d in dirs:
    if not os.path.isdir(d):
        continue
    for fname in os.listdir(d):
        if not fname.endswith('.py'):
            continue
        path = os.path.join(d, fname)
        with open(path, 'rb') as f:
            data = f.read()
        try:
            data.decode('utf-8')
        except UnicodeDecodeError:
            fx = fix_utf8(data)
            try:
                fx.decode('utf-8')
                with open(path, 'wb') as f:
                    f.write(fx)
                fixed.append(path)
            except UnicodeDecodeError:
                print(f'FAILED: {path}')

print(f'Fixed {len(fixed)} files:')
for f in fixed:
    print(f'  {f}')
