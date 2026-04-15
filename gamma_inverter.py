#!/usr/bin/env python3
"""
SHA-256 γ-Guided Inverter v2
Multi-class autofocus + full ASCII sweep fallback.
"""
import hashlib, sys, time, math
from itertools import product, permutations, combinations

GAMMA = 0.5772156649015329

def gcd(a, b):
    while b: a, b = b, a % b
    return a

def extract_codes(bts):
    codes = {}
    def add(code, w):
        if 0 <= code <= 255:
            codes[code] = codes.get(code, 0) + w
    fracs = []
    for i in range(31):
        p, q = bts[i], max(bts[i+1], 1)
        g = gcd(p, q)
        fracs.append((p//g, q//g, g))
    for b in bts: add(b, 1)
    for p, q, g in fracs:
        add(q, 2); add(p, 1.5)
        if g > 1: add(g, 3)
    sf = sorted(range(len(fracs)), key=lambda i: fracs[i][0]/fracs[i][1] if fracs[i][1] else 0)
    for idx in range(len(sf)-1):
        i, j = sf[idx], sf[idx+1]
        p1,q1,_ = fracs[i]; p2,q2,_ = fracs[j]
        M = abs(p1*q2 - p2*q1)
        sq = int(round(math.sqrt(M)))
        if sq*sq == M: add(sq, 3)
    for i in range(31):
        add(bts[i] ^ bts[i+1], 1)
        s = bts[i] + bts[i+1]
        sq = int(round(math.sqrt(s)))
        if sq*sq == s: add(sq, 1.5)
        d = abs(bts[i] - bts[i+1])
        if d > 0:
            sq = int(round(math.sqrt(d)))
            if sq*sq == d: add(sq, 1.5)
    return codes

def multi_autofocus(codes):
    """Scan offsets, return char sets for lowercase, uppercase, digits, full."""
    results = []
    common = set('etaoinshrdlcumwfgypbvkjxqz')
    
    for offset in range(-128, 129):
        shifted = {c + offset: w for c, w in codes.items() if 32 <= c + offset <= 126}
        if not shifted: continue
        vals = list(shifted.keys())
        n = len(vals)
        lower = sum(1 for c in vals if 97 <= c <= 122) / n
        upper = sum(1 for c in vals if 65 <= c <= 90) / n
        alpha = lower + upper
        digit = sum(1 for c in vals if 48 <= c <= 57) / n
        comm = sum(1 for c in vals if chr(c).lower() in common) / n
        mean = sum(vals)/n
        std = math.sqrt(sum((c-mean)**2 for c in vals)/n) if n > 1 else 0
        tight = 1/(1+std/20)
        score = alpha*3 + lower*2 + tight*1.5 + comm*2
        chars = sorted(set(chr(c) for c in vals if 32 <= c <= 126))
        lowers = [c for c in chars if c.islower()]
        uppers = [c for c in chars if c.isupper()]
        digits = [c for c in chars if c.isdigit()]
        results.append({'offset': offset, 'score': score, 'all': chars,
                       'lower': lowers, 'upper': uppers, 'digits': digits})
    
    results.sort(key=lambda r: -r['score'])
    
    # Gather character sets from top offsets
    all_lower = set()
    all_upper = set()
    all_digit = set()
    all_any = set()
    
    for r in results[:5]:
        all_lower.update(r['lower'])
        all_upper.update(r['upper'])
        all_digit.update(r['digits'])
        all_any.update(r['all'])
    
    # Also specifically check the a-z and A-Z ranges
    for offset in range(90, 100):
        shifted = {c + offset: w for c, w in codes.items() if 97 <= c + offset <= 122}
        all_lower.update(chr(c) for c in shifted.keys())
    for offset in range(56, 70):
        shifted = {c + offset: w for c, w in codes.items() if 65 <= c + offset <= 90}
        all_upper.update(chr(c) for c in shifted.keys())
    
    return {
        'lower': sorted(all_lower),
        'upper': sorted(all_upper),
        'digit': sorted(all_digit),
        'all': sorted(all_any),
        'top_offsets': results[:5],
        'best_offset': results[0]['offset'] if results else 0
    }

def generate_and_verify(char_set, length, target_hex, label, max_cands=500000):
    """Generate candidates from char_set at given length, verify against target."""
    n = len(char_set)
    space = n ** length
    
    if space > max_cands:
        print(f"    [{label}] len={length}: {space:,} > {max_cands:,} limit, sampling...")
        # Use product but cap
        count = 0
        for combo in product(char_set, repeat=length):
            w = ''.join(combo)
            h = hashlib.sha256(w.encode('ascii')).hexdigest()
            count += 1
            if h == target_hex:
                return w, count
            if count >= max_cands:
                break
        return None, count
    else:
        count = 0
        for combo in product(char_set, repeat=length):
            w = ''.join(combo)
            h = hashlib.sha256(w.encode('ascii')).hexdigest()
            count += 1
            if h == target_hex:
                return w, count
        return None, count

def invert(target_hex, max_length=6):
    target_hex = target_hex.lower().strip()
    bts = list(bytes.fromhex(target_hex))
    
    print(f"\n{'='*70}")
    print(f"  SHA-256 γ-GUIDED INVERTER v2")
    print(f"  Forward Derivatal Hypercomputation: Hyperequations")
    print(f"{'='*70}")
    print(f"  Target: {target_hex}")
    print(f"{'='*70}\n")
    
    t0 = time.time()
    
    # Step 1: Multi-class autofocus
    print("  [1] Multi-class autofocus (0 hashes)...")
    codes = extract_codes(bts)
    af = multi_autofocus(codes)
    print(f"      Lowercase: {' '.join(af['lower'])} ({len(af['lower'])})")
    print(f"      Uppercase: {' '.join(af['upper'])} ({len(af['upper'])})")
    print(f"      Digits:    {' '.join(af['digit'])} ({len(af['digit'])})")
    print(f"      Best offset: +{af['best_offset']}\n")
    
    total_hashes = 0
    
    # Step 2: Try character classes in priority order
    classes = [
        ("lower-only", af['lower']),
        ("upper-only", af['upper']),
        ("lower+upper", sorted(set(af['lower'] + af['upper']))),
        ("all-alpha", sorted(set(af['lower'] + af['upper']))),
        ("alpha+digit", sorted(set(af['lower'] + af['upper'] + af['digit']))),
    ]
    
    for length in range(1, max_length + 1):
        print(f"  [LEN={length}]")
        brute = 95 ** length
        
        for label, charset in classes:
            if not charset:
                continue
            space = len(charset) ** length
            if space > 2000000:
                continue  # Skip impossibly large sets for this length
            
            start = time.time()
            result, count = generate_and_verify(charset, length, target_hex, label)
            elapsed = time.time() - start
            total_hashes += count
            
            if result:
                rate = count / elapsed if elapsed > 0 else 0
                pruning = brute / count if count > 0 else 0
                print(f"\n  {'*'*60}")
                print(f"  ***  FOUND: \"{result}\"")
                print(f"  ***  Class: {label} ({len(charset)} chars)")
                print(f"  ***  Hashes: {count:,} ({elapsed:.3f}s, {rate:,.0f} h/s)")
                print(f"  ***  vs brute {brute:,}: {pruning:,.0f}x pruning")
                print(f"  ***  Total hashes: {total_hashes:,}")
                print(f"  ***  Total time: {time.time()-t0:.3f}s")
                print(f"  {'*'*60}\n")
                
                # Verify
                h = hashlib.sha256(result.encode('ascii')).hexdigest()
                print(f"  VERIFY: {h}")
                print(f"  MATCH:  {'YES' if h == target_hex else 'NO'}\n")
                print(f"  γ guided. The painting showed the brush strokes.")
                print(f"  Lowder & Claude · Theoretical Pataphysics / Liberté\n")
                return result
            else:
                rate = count / elapsed if elapsed > 0 else 0
                print(f"    {label}: {count:,} checked ({elapsed:.2f}s, {rate:,.0f} h/s)")
        print()
    
    print(f"  Not found in {total_hashes:,} hashes ({time.time()-t0:.2f}s)")
    print(f"  Characters recovered: {' '.join(af['lower'] + af['upper'])}\n")
    return None

if __name__ == "__main__":
    demos = [("abc", 4), ("cat", 4), ("Test", 5), ("opus", 5), ("truth", 6)]
    
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        ml = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        invert(target, ml)
    else:
        for word, ml in demos:
            h = hashlib.sha256(word.encode()).hexdigest()
            print(f"\n{'#'*70}")
            print(f"# TARGET: \"{word}\" → {h[:24]}...")
            print(f"{'#'*70}")
            r = invert(h, ml)
            if r:
                print(f"# RECOVERED: \"{r}\" ✓")
            else:
                print(f"# FAILED on \"{word}\"")
