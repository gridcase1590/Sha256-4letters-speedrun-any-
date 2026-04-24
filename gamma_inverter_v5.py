#!/usr/bin/env python3
"""
SHA-256 γ-Guided Inverter v3
Triadic cascade [3,9,27,81,243] × prime walk [5,7,11,23]
Per-position narrowing → brute force remainder.
"""
import hashlib, sys, time, math
from itertools import product

GAMMA = 0.5772156649015329

LOWER = list('abcdefghijklmnopqrstuvwxyz')
UPPER = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
DIGIT = list('0123456789')

def hex_to_bits(h):
    b = []
    for ch in h:
        n = int(ch, 16)
        for j in range(3, -1, -1):
            b.append((n >> j) & 1)
    return b

def read_at_scale(bits, start, end, scale):
    seg = bits[start:end]
    n = len(seg)
    part = max(1, n // scale)
    counts = []
    for i in range(min(scale, n)):
        ps = i * part
        pe = min(ps + part, n)
        counts.append(sum(seg[ps:pe]))
    return counts

def triadic_prime_reading(bits, N):
    """9-angle reading: [3,9,27,81,243] × [5,7,11,23] → gamma per position"""
    seg_size = 256 / N
    triadic = [3, 9, 27, 81, 243]
    primes = [5, 7, 11, 23]

    readings = []
    for pos in range(N):
        start = int(round(pos * seg_size))
        end = int(round((pos + 1) * seg_size))

        tri_vals = []
        for scale in triadic:
            counts = read_at_scale(bits, start, end, scale)
            tri_vals.append(sum(counts) / max(len(counts), 1))

        prime_vals = []
        for scale in primes:
            counts = read_at_scale(bits, start, end, scale)
            prime_vals.append(sum(counts) / max(len(counts), 1))

        prod = sum(tri_vals[i] * prime_vals[i] for i in range(4))
        readings.append(prod)

    return readings

def narrow_candidates(readings, charset, width=5):
    """Map readings to charset, return per-position candidate lists."""
    sorted_cs = sorted(charset, key=lambda c: ord(c))
    n_chars = len(sorted_cs)

    r_min = min(readings)
    r_max = max(readings)
    r_range = r_max - r_min if r_max > r_min else 1

    per_pos = []
    for r in readings:
        norm = (r - r_min) / r_range
        center_idx = int(norm * (n_chars - 1))
        half = width // 2
        lo = max(0, center_idx - half)
        hi = min(n_chars, lo + width)
        if hi - lo < width:
            lo = max(0, hi - width)
        per_pos.append(sorted_cs[lo:hi])

    return per_pos

def search(per_pos, target_hex):
    count = 0
    for combo in product(*per_pos):
        w = ''.join(combo)
        count += 1
        if hashlib.sha256(w.encode('ascii')).hexdigest() == target_hex:
            return w, count
    return None, count

def try_class(charset, length, target, cap=15_000_000):
    count = 0
    for combo in product(charset, repeat=length):
        w = ''.join(combo)
        count += 1
        if hashlib.sha256(w.encode('ascii')).hexdigest() == target:
            return w, count
        if count >= cap:
            return None, count
    return None, count

def try_class_combos(classes, length, target, cap_per=500_000):
    total = 0
    for pattern in product(classes, repeat=length):
        space = 1
        for p in pattern:
            space *= len(p)
        if space > cap_per:
            continue
        for combo in product(*pattern):
            w = ''.join(combo)
            total += 1
            if hashlib.sha256(w.encode('ascii')).hexdigest() == target:
                return w, total, pattern
    return None, total, None

def invert(target_hex, max_length=8):
    target_hex = target_hex.lower().strip()
    bits = hex_to_bits(target_hex)
    total_ones = sum(bits)

    print(f"\n{'='*65}")
    print(f"  SHA-256 γ-GUIDED INVERTER v5")
    print(f"  Triadic×Prime: [3,9,27,81,243]·[5,7,11,23]")
    print(f"{'='*65}")
    print(f"  Target: {target_hex[:32]}...")
    print(f"  Ones: {total_ones}/256")
    print(f"{'='*65}\n")
    print(f"  by...")
    print(f" ██▒   █ █████▓▓  ██▀███  ▓█████▄  ▄▄▄      ▓█████▄ ")
    print(f" ▓██░   █ ▀   █▓▒ ▓██ ▒ ██▒▒██▀ ██▌▒████▄    ▒██▀ ██▌")
    print(f"  ▓██  █▒   ███▒░ ▓██ ░▄█ ▒░██   █▌▒██  ▀█▄  ░██   █▌")
    print(f"   ▒██ █░ ▄  █▓▒░ ▒██▀▀█▄  ░▓█▄   ▌░██▄▄▄▄██ ░▓█▄   ▌")
    print(f"    ▒▀█░  ████▒░ ▒░██▓ ▒██▒░▒████▓  ▓█   ▓██▒░▒████▓ ")
    print(f"    ░ ▐░   ░▒ ░░ ░░ ▒▓ ░▒▓░ ▒▒▓  ▒  ▒▒   ▓▒█░ ▒▒▓  ▒ ")
    print(f"    ░ ░░    ░ ░  ░  ░▒ ░ ▒░ ░ ▒  ▒   ▒   ▒▒ ░ ░ ▒  ▒ ")
    print(f"      ░░    ░       ░░   ░  ░ ░  ░   ░   ▒    ░ ░  ░ ")
    print(f"       ░    ░    ░   ░        ░          ░  ░   ░    ")
    print(f"      ░                     ░                 ░      ")

    t0 = time.time()
    total_hashes = 0

    for length in range(1, max_length + 1):
        print(f"  [LEN={length}]")
        brute_95 = 95 ** length

        # ── Phase 1: γ-guided per-position (0 pre-hashes) ──
        readings = triadic_prime_reading(bits, length)

        for cs_name, charset in [('lower', LOWER), ('upper', UPPER), ('digit', DIGIT),
                                  ('mixed', LOWER + UPPER), ('alnum', LOWER + UPPER + DIGIT)]:
            for width in [3, 5, 7, 10]:
                per_pos = narrow_candidates(readings, charset, width=width)
                space = 1
                for pp in per_pos:
                    space *= len(pp)

                if space > 5_000_000:
                    continue

                t1 = time.time()
                result, count = search(per_pos, target_hex)
                total_hashes += count
                elapsed = time.time() - t1
                rate = count / elapsed if elapsed > 0 else 0

                if result:
                    pruning = brute_95 / total_hashes if total_hashes > 0 else 0
                    chars_per = '/'.join(str(len(pp)) for pp in per_pos)
                    print(f"\n  {'★'*55}")
                    print(f"  ★  FOUND: \"{result}\"")
                    print(f"  ★  Method: γ-guided {cs_name} w={width} ({chars_per})")
                    print(f"  ★  Hashes: {total_hashes:,} ({time.time()-t0:.3f}s)")
                    print(f"  ★  This search: {count:,} ({elapsed:.3f}s, {rate:,.0f} h/s)")
                    print(f"  ★  vs brute-95: {pruning:,.0f}x pruning")
                    print(f"  {'★'*55}")
                    h = hashlib.sha256(result.encode()).hexdigest()
                    print(f"\n  VERIFY: {'✓' if h == target_hex else '✗'}\n")
                    return result
                else:
                    if width == 5:  # only print main width
                        print(f"    γ {cs_name} w={width}: {count:,} ({elapsed:.2f}s)")

        # ── Phase 2: Single-class brute ──
        for cname, cs in [('lower', LOWER), ('upper', UPPER), ('digit', DIGIT)]:
            space = len(cs) ** length
            if space > 15_000_000:
                continue

            t1 = time.time()
            r, count = try_class(cs, length, target_hex)
            total_hashes += count
            elapsed = time.time() - t1
            rate = count / elapsed if elapsed > 0 else 0

            if r:
                print(f"\n  {'★'*55}")
                print(f"  ★  FOUND: \"{r}\"")
                print(f"  ★  Method: brute {cname}")
                print(f"  ★  Hashes: {total_hashes:,} ({time.time()-t0:.3f}s)")
                print(f"  ★  vs brute-95: {brute_95/total_hashes:,.0f}x")
                print(f"  {'★'*55}")
                h = hashlib.sha256(r.encode()).hexdigest()
                print(f"\n  VERIFY: {'✓' if h == target_hex else '✗'}\n")
                return r
            else:
                print(f"    brute {cname}: {count:,} ({elapsed:.2f}s)")

        # ── Phase 3: Class combos for mixed case ──
        n_patterns = 3 ** length
        if n_patterns <= 300:
            t1 = time.time()
            r, count, pattern = try_class_combos(
                [LOWER, UPPER, DIGIT], length, target_hex, cap_per=500_000
            )
            total_hashes += count
            elapsed = time.time() - t1

            if r:
                pnames = ['L' if p is LOWER else 'U' if p is UPPER else 'D' for p in pattern]
                print(f"\n  {'★'*55}")
                print(f"  ★  FOUND: \"{r}\"")
                print(f"  ★  Pattern: {''.join(pnames)}")
                print(f"  ★  Hashes: {total_hashes:,} ({time.time()-t0:.3f}s)")
                print(f"  ★  vs brute-95: {brute_95/total_hashes:,.0f}x")
                print(f"  {'★'*55}")
                h = hashlib.sha256(r.encode()).hexdigest()
                print(f"\n  VERIFY: {'✓' if h == target_hex else '✗'}\n")
                return r
            else:
                print(f"    mixed combos: {count:,} ({elapsed:.2f}s)")

        print()

    print(f"  Not found in {total_hashes:,} hashes ({time.time()-t0:.2f}s)\n")
    return None

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        ml = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        invert(target, ml)
    else:
        demos = [('abc',4), ('cat',4), ('Hi',4), ('42',3),
                 ('Test',5), ('HELLO',6), ('truth',6), ('opus',6)]
        for word, ml in demos:
            h = hashlib.sha256(word.encode()).hexdigest()
            print(f"\n{'#'*60}")
            print(f"# \"{word}\"")
            print(f"{'#'*60}")
            r = invert(h, ml)
            print(f"# {'✓ ' + repr(r) if r else '✗ MISS'}")
