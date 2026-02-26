#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Majority (n-input) Verilog + BLIF generator (canonical BLIF)
------------------------------------------------------------
Outputs:
  - Verilog bundle with:
      1) maj_fb_<n>                : Folded-bias (CSA-only to bit w)
      2) maj_baseline_strict_<n>   : STRICT 2-step baseline
  - BLIFs with canonical .names encodings:
      - maj_fb_<n>.blif
      - maj_baseline_strict_<n>.blif
    Written under:
      - results/
          - folded_bias_threshold/
          - folded_bias_carryonly/
          - baseline_threshold/

Notes on BLIF canonicalization:
  * Gate inputs are SORTED (alphabetically) at emission time.
  * Truth-table cubes are MINIMAL + DEDUPED.
  * Encodings used:
      - MAJ3: 11- 1 ; 1-1 1 ; -11 1
      - NOT : 0 1
      - XOR3: 001 1 ; 010 1 ; 100 1 ; 111 1   (only if maj_only=False)
  * Constants are explicit: .names CONST1\n1  (and empty .names CONST0 when needed)
"""

# ===================== CONFIG =====================
N = 43  # majority input size (odd, >=3)

OUTPUT_ROOT_DIRNAME = "results"
OUTPUT_NAME = f"maj{N}_generated_canon.v"
BLIF_DIR_FOLDED_BIAS_THRESHOLD = "folded_bias_threshold"
BLIF_DIR_FOLDED_BIAS_CARRYONLY = "folded_bias_carryonly"
BLIF_DIR_BASELINE_THRESHOLD = "baseline_threshold"

INCLUDE_FOLDED_BIAS_FULL      = True   # maj_fb_<n> (legacy/full scheduler)
INCLUDE_FOLDED_BIAS_CARRYONLY = False   # maj_fb_carryonly_<n> (stop at w-1, maj = carry into w)
INCLUDE_BASELINE_STRICT       = True   # maj_baseline_strict_<n>
# BLIF adder style:
#   True  = expand FA as MAJ-only (3x MAJ + 2x INV)  [best for MIG passes]
#   False = expand FA with {XOR3 for sum, MAJ3 for cout}
MAJ_ONLY_FA = True
RUN_EQUIV_SELF_CHECK = True
SELF_CHECK_MAX_N = 7
SCHEDULE_MODE = "dadda"  # serial | wallace | dadda

# Structural-bias sweeps (paper II-E style)
ENABLE_STRUCTURAL_BIAS_SWEEP_BASELINE = True
ENABLE_STRUCTURAL_BIAS_SWEEP_HWK = True
ENABLE_FOLDED_MAJ_EMBED_SWEEP = True
ENABLE_FOLDED_DIRECT_PERM_SWEEP = True
SWEEP_RANDOM_LAYOUTS = 12
SWEEP_RANDOM_PERMUTATIONS = 12
SWEEP_MAX_VARIANTS = 24

# Local mockturtle flow: repeated mig_resubstitution + cleanup_dangling
USE_MOCKTURTLE_SCORING = True
MOCKTURTLE_BIN = "tools/mockturtle_mig_opt/build/mockturtle_mig_opt"
MOCKTURTLE_ROUNDS = 6
MOCKTURTLE_MAX_PIS = 8
MOCKTURTLE_MAX_INSERTS = 1
MOCKTURTLE_RECIPES = (
    "resub",
    "resub2",
    "depth_resub2",
    "resub_depth_resub2",
)
# ===================================================

import os, math, random, shutil, subprocess, tempfile
from collections import defaultdict, deque

# ---------- common helpers ----------
def _verilog_header(n, title):
    return [
        f"// -----------------------------------------------------------------------------",
        f"// {title}",
        f"// n = {n}",
        f"// Expect FA primitive: module fa(input a,b,cin, output sum,cout);",
        f"// -----------------------------------------------------------------------------",
        ""
    ]


def _fa_max_levels(fa_ops):
    """Return the maximum FA level depth in a sequential FA list."""
    if not fa_ops:
        return 0

    levels = {}

    def get_level(sig):
        if sig in ("1'b0", "1'b1", None):
            return 0
        return levels.get(sig, 0)

    max_level = 0
    for a, b, cin, s, k in fa_ops:
        curr = max(get_level(a), get_level(b), get_level(cin)) + 1
        levels[s] = curr
        levels[k] = curr
        if curr > max_level:
            max_level = curr
    return max_level


def _normalize_schedule_mode(mode: str) -> str:
    m = (mode or "serial").strip().lower()
    if m not in ("serial", "wallace", "dadda"):
        raise ValueError(f"Unsupported SCHEDULE_MODE='{mode}'. Use: serial|wallace|dadda")
    return m


def _dadda_stage_targets(height: int):
    """Return descending local height targets for Dadda-like reduction."""
    if height <= 2:
        return []
    seq = [2]
    while seq[-1] < height:
        seq.append((3 * seq[-1]) // 2)
    return list(reversed(seq[:-1]))


def _reduce_column_bits(col, queue, mode, new_wires, append_op):
    """
    Reduce one column queue to a single residual bit and emit carries to col+1.
    mode:
      - serial : accumulator chain (legacy behavior)
      - wallace: per-level greedy triple compression
      - dadda  : per-level target-height compression, then finalize
    """
    mode = _normalize_schedule_mode(mode)
    bits = list(queue)
    carries_out = []
    if not bits:
        return None, carries_out

    if mode == "serial":
        acc = bits[0]
        idx = 1
        while idx + 1 < len(bits):
            b = bits[idx]
            c = bits[idx + 1]
            idx += 2
            s, k = new_wires(col, "")
            append_op(col, "triple", acc, b, c, s, k)
            carries_out.append(k)
            acc = s
        if idx < len(bits):
            b = bits[idx]
            s, k = new_wires(col, "p_")
            append_op(col, "pair", acc, b, "1'b0", s, k)
            carries_out.append(k)
            acc = s
        return acc, carries_out

    if mode == "wallace":
        level = 0
        current = bits
        while len(current) > 2:
            next_bits = []
            i = 0
            while i + 2 < len(current):
                a, b, c = current[i], current[i + 1], current[i + 2]
                s, k = new_wires(col, f"w{level}_")
                append_op(col, f"w{level}_triple", a, b, c, s, k)
                carries_out.append(k)
                next_bits.append(s)
                i += 3
            next_bits.extend(current[i:])
            current = next_bits
            level += 1

        if len(current) == 2:
            a, b = current
            s, k = new_wires(col, f"w{level}_p_")
            append_op(col, f"w{level}_pair", a, b, "1'b0", s, k)
            carries_out.append(k)
            current = [s]

        return current[0], carries_out

    # dadda
    current = bits
    stage_targets = _dadda_stage_targets(len(current))
    for stg, target in enumerate(stage_targets):
        if len(current) <= target:
            continue
        work = deque(current)
        next_bits = []
        while len(work) > target and len(work) >= 3:
            a = work.popleft()
            b = work.popleft()
            c = work.popleft()
            s, k = new_wires(col, f"d{stg}_")
            append_op(col, f"d{stg}_triple", a, b, c, s, k)
            carries_out.append(k)
            next_bits.append(s)
        next_bits.extend(list(work))
        current = next_bits

    # Safety fallback: if still tall, finish with Wallace-like levels.
    fallback_level = len(stage_targets)
    while len(current) > 2:
        next_bits = []
        i = 0
        while i + 2 < len(current):
            a, b, c = current[i], current[i + 1], current[i + 2]
            s, k = new_wires(col, f"d{fallback_level}_")
            append_op(col, f"d{fallback_level}_triple", a, b, c, s, k)
            carries_out.append(k)
            next_bits.append(s)
            i += 3
        next_bits.extend(current[i:])
        current = next_bits
        fallback_level += 1

    if len(current) == 2:
        a, b = current
        s, k = new_wires(col, f"d{fallback_level}_p_")
        append_op(col, f"d{fallback_level}_pair", a, b, "1'b0", s, k)
        carries_out.append(k)
        current = [s]

    return current[0], carries_out

# ======== CSA MACRO SCHEDULER (used by both variants) ========
def csa_macro_schedule_all_columns(raw_inputs, const_names_per_col):
    """
    Build a CSA macro tree:
      Stage A (col 0): only RAW input triples -> (s@0, c@1)
      Stage B (col 0): fold [sums + leftover raw + const@0...] -> ONE bit; carries -> col 1
      Columns 1..: fold each column j to ONE bit (serial chain); carries -> j+1
    Returns:
      ops             : list[(col, kind, a,b,cin, s,k)]  // FA instances
      wires           : list[(s,k)]                      // wire names to declare
      residual_by_col : {col: residual_bit_name}        // final single bit per column
      const_decl      : list[str]                        // const wires to declare (e.g., K0..)
    Compression style is selected globally via SCHEDULE_MODE.
    """
    mode = _normalize_schedule_mode(SCHEDULE_MODE)

    fa_id = 0
    ops   = []
    wires = []

    def new_wires(col, tag=""):
        nonlocal fa_id
        s = f"{tag}s_c{col}_{fa_id}"
        k = f"{tag}c_c{col}_{fa_id}"
        fa_id += 1
        wires.append((s, k))
        return s, k

    # ---- Stage A: RAW triples at col 0 ----
    raw = list(raw_inputs)
    col0_sums = deque()
    col_bits  = {1: deque()}  # carries from col 0 land here

    while len(raw) >= 3:
        a = raw.pop(0); b = raw.pop(0); c = raw.pop(0)
        s, k = new_wires(0, "raw_")
        ops.append((0, "raw_triple", a, b, c, s, k))
        col0_sums.append(s)
        col_bits[1].append(k)

    def append_op(col, kind, a, b, cin, s, k):
        ops.append((col, kind, a, b, cin, s, k))

    # ---- Stage B: fold col 0 to ONE bit (include constants at col 0 if any) ----
    col0_queue = deque(list(col0_sums) + raw)
    const_decl = []
    for cname in const_names_per_col.get(0, []):
        col0_queue.append(cname)
        const_decl.append(cname)

    residual_by_col = {}

    # fold col 0
    res0, carries_to_1 = _reduce_column_bits(0, col0_queue, mode, new_wires, append_op)
    if res0 is not None:
        residual_by_col[0] = res0
    for k in carries_to_1:
        col_bits.setdefault(1, deque()).append(k)

    # ---- Columns 1.. : fold each to ONE bit; push carries upward ----
    pending_cols = set(col_bits.keys()) | set(const_names_per_col.keys())
    current = 1
    while True:
        candidates = [c for c in pending_cols if c >= current and (
            (c in col_bits and len(col_bits[c]) > 0) or (c in const_names_per_col and len(const_names_per_col[c]) > 0)
        )]
        if not candidates:
            break
        j = min(candidates)

        qj = col_bits.get(j, deque())
        if j in const_names_per_col:
            for cname in const_names_per_col[j]:
                qj.append(cname)
                const_decl.append(cname)

        residual_j, carries_to_next = _reduce_column_bits(j, qj, mode, new_wires, append_op)
        if residual_j is not None:
            residual_by_col[j] = residual_j
        if carries_to_next:
            col_bits.setdefault(j+1, deque()).extend(carries_to_next)
            pending_cols.add(j+1)

        # mark processed
        if j in col_bits: col_bits[j] = deque()
        if j in const_names_per_col: const_names_per_col[j] = []
        current = j + 1

    return ops, wires, residual_by_col, const_decl


def csa_macro_schedule_upto_column(raw_inputs, const_names_per_col, stop_col):
    """
    Build the same CSA macro structure as csa_macro_schedule_all_columns, but stop
    scheduling at column stop_col (inclusive).

    Returns:
      ops             : list[(col, kind, a,b,cin, s,k)]
      wires           : list[(s,k)]
      residual_by_col : {col: residual_bit_name}
      const_decl      : list[str]
      last_k_stop     : name of the last carry created at stop_col, or None
    Compression style is selected globally via SCHEDULE_MODE.
    """
    assert stop_col >= 0

    mode = _normalize_schedule_mode(SCHEDULE_MODE)

    fa_id = 0
    ops = []
    wires = []
    last_k_stop = None

    # Work on a local copy so caller data is not mutated.
    const_map = defaultdict(list)
    for col, names in (const_names_per_col or {}).items():
        const_map[col] = list(names)

    def new_wires(col, tag=""):
        nonlocal fa_id
        s = f"{tag}s_c{col}_{fa_id}"
        k = f"{tag}c_c{col}_{fa_id}"
        fa_id += 1
        wires.append((s, k))
        return s, k

    def append_op(col, kind, a, b, cin, s, k):
        nonlocal last_k_stop
        ops.append((col, kind, a, b, cin, s, k))
        if col == stop_col:
            last_k_stop = k

    raw = list(raw_inputs)
    col0_sums = deque()
    col_bits = {1: deque()}

    # Stage A: RAW triples at col 0.
    while len(raw) >= 3:
        a = raw.pop(0)
        b = raw.pop(0)
        c = raw.pop(0)
        s, k = new_wires(0, "raw_")
        append_op(0, "raw_triple", a, b, c, s, k)
        col0_sums.append(s)
        col_bits[1].append(k)

    residual_by_col = {}
    const_decl = []

    # Stage B: fold col 0 to one bit (include col-0 constants).
    col0_queue = deque(list(col0_sums) + raw)
    for cname in const_map.get(0, []):
        col0_queue.append(cname)
        const_decl.append(cname)

    res0, carries_to_1 = _reduce_column_bits(0, col0_queue, mode, new_wires, append_op)
    if res0 is not None:
        residual_by_col[0] = res0

    if stop_col >= 1:
        for carry in carries_to_1:
            col_bits.setdefault(1, deque()).append(carry)

    # Fold only columns 1..stop_col.
    for j in range(1, stop_col + 1):
        qj = col_bits.get(j, deque())
        for cname in const_map.get(j, []):
            qj.append(cname)
            const_decl.append(cname)

        residual_j, carries_to_next = _reduce_column_bits(j, qj, mode, new_wires, append_op)
        if residual_j is not None:
            residual_by_col[j] = residual_j

        # Propagate only if the next column is still in-range.
        if j < stop_col and carries_to_next:
            col_bits.setdefault(j + 1, deque()).extend(carries_to_next)

    return ops, wires, residual_by_col, const_decl, last_k_stop


# ---------- scaffold + reduction helpers ----------
def _is_const(sig: str) -> bool:
    return sig in ("1'b0", "1'b1")


def _prune_fa_netlist(fa_ops, maj_signal):
    needed = {maj_signal}
    pruned_rev = []
    for a, b, cin, s, k in reversed(fa_ops):
        if s in needed or k in needed:
            pruned_rev.append((a, b, cin, s, k))
            for sig in (a, b, cin):
                if not _is_const(sig):
                    needed.add(sig)
    return list(reversed(pruned_rev))


def _constant_fold_and_prune(fa_ops, maj_signal):
    const_map = {}

    def resolve(sig):
        while sig in const_map:
            sig = const_map[sig]
        return sig

    processed = []
    for a, b, cin, s, k in fa_ops:
        a = resolve(a); b = resolve(b); cin = resolve(cin)
        if _is_const(a) and _is_const(b) and _is_const(cin):
            ones = (a == "1'b1") + (b == "1'b1") + (cin == "1'b1")
            const_map[s] = "1'b1" if (ones & 1) else "1'b0"
            const_map[k] = "1'b1" if ones >= 2 else "1'b0"
            continue
        processed.append((a, b, cin, s, k))

    maj_signal = resolve(maj_signal)
    folded = []
    for a, b, cin, s, k in processed:
        folded.append((resolve(a), resolve(b), resolve(cin), resolve(s), resolve(k)))

    folded = _prune_fa_netlist(folded, maj_signal)
    return folded, maj_signal


def _collect_const_names(fa_ops, maj_signal, candidates):
    used = set()
    candidate_set = set(candidates or [])
    for a, b, cin, s, k in fa_ops:
        for sig in (a, b, cin, s, k):
            if sig in candidate_set:
                used.add(sig)
    if maj_signal in candidate_set:
        used.add(maj_signal)
    return sorted(used)


def _prepare_for_emit(fa_ops, maj_signal, const_candidates):
    fa_ops_prepped, maj_signal_prepped = _constant_fold_and_prune(list(fa_ops), maj_signal)
    const_used = _collect_const_names(fa_ops_prepped, maj_signal_prepped, const_candidates)
    return fa_ops_prepped, maj_signal_prepped, const_used


def _baseline_hw_layout_variants(n: int, num_fix: int, n_big: int, random_layouts: int):
    """
    Generate structurally equivalent scaffold input layouts for baseline:
      Maj_n embedded in Maj_N with fixed 1/0 inputs placed at different positions.
    Returns list[(label, hw_inputs)] where hw_inputs entries are x[i], 1'b1, 1'b0.
    """
    if num_fix <= 0:
        return [("identity", [f"x[{i}]" for i in range(n)])]

    one_tokens = [("1", i) for i in range(num_fix)]
    zero_tokens = [("0", i) for i in range(num_fix)]
    x_tokens = [("x", i) for i in range(n)]
    base_tokens = x_tokens + one_tokens + zero_tokens

    def to_signals(seq):
        out = []
        for kind, idx in seq[:n_big]:
            if kind == "x":
                out.append(f"x[{idx}]")
            elif kind == "1":
                out.append("1'b1")
            else:
                out.append("1'b0")
        return out

    variants = []

    # Current baseline ordering.
    variants.append(("identity", to_signals(base_tokens)))
    variants.append(("reverse", to_signals(list(reversed(base_tokens)))))
    variants.append(("x_then_pairs_10", to_signals(x_tokens + [(t, i) for i in range(num_fix) for t in ("1", "0")])))
    variants.append(("x_then_pairs_01", to_signals(x_tokens + [(t, i) for i in range(num_fix) for t in ("0", "1")])))

    interleave = []
    ones_i = 0
    zeros_i = 0
    for i in range(n):
        interleave.append(("x", i))
        if ones_i < num_fix:
            interleave.append(("1", ones_i))
            ones_i += 1
        if zeros_i < num_fix:
            interleave.append(("0", zeros_i))
            zeros_i += 1
    while ones_i < num_fix:
        interleave.append(("1", ones_i))
        ones_i += 1
    while zeros_i < num_fix:
        interleave.append(("0", zeros_i))
        zeros_i += 1
    variants.append(("interleave_x10", to_signals(interleave)))

    alt = []
    xi = 0
    oi = 0
    zi = 0
    while len(alt) < n_big:
        if xi < n:
            alt.append(("x", xi))
            xi += 1
        if oi < num_fix and len(alt) < n_big:
            alt.append(("1", oi))
            oi += 1
        if xi < n and len(alt) < n_big:
            alt.append(("x", xi))
            xi += 1
        if zi < num_fix and len(alt) < n_big:
            alt.append(("0", zi))
            zi += 1
    variants.append(("alternating", to_signals(alt)))

    for seed in range(max(0, random_layouts)):
        rng = random.Random(1009 + n * 37 + seed)
        seq = list(base_tokens)
        rng.shuffle(seq)
        variants.append((f"rand_{seed}", to_signals(seq)))

    dedup = []
    seen = set()
    for label, seq in variants:
        key = tuple(seq)
        if key in seen:
            continue
        seen.add(key)
        dedup.append((label, seq))
    return dedup


def _input_permutation_variants(n: int, random_perms: int):
    """Generate structurally equivalent input permutations for HW+K sweeps."""
    base = list(range(n))
    variants = []

    variants.append(("identity", list(base)))
    variants.append(("reverse", list(reversed(base))))

    even_then_odd = [i for i in range(n) if (i % 2 == 0)] + [i for i in range(n) if (i % 2 == 1)]
    variants.append(("even_then_odd", even_then_odd))
    variants.append(("odd_then_even", [i for i in range(n) if (i % 2 == 1)] + [i for i in range(n) if (i % 2 == 0)]))

    mid = n // 2
    center_out = [mid]
    for delta in range(1, n):
        lo = mid - delta
        hi = mid + delta
        if lo >= 0:
            center_out.append(lo)
        if hi < n:
            center_out.append(hi)
        if len(center_out) >= n:
            break
    variants.append(("center_out", center_out[:n]))

    pair_swap = []
    i = 0
    while i + 1 < n:
        pair_swap.extend([i + 1, i])
        i += 2
    if i < n:
        pair_swap.append(i)
    variants.append(("pair_swap", pair_swap))

    for rot in (1, 2):
        if n > 1:
            variants.append((f"rotate_{rot}", base[rot:] + base[:rot]))

    for seed in range(max(0, random_perms)):
        rng = random.Random(2003 + n * 53 + seed)
        perm = list(base)
        rng.shuffle(perm)
        variants.append((f"rand_{seed}", perm))

    dedup = []
    seen = set()
    for label, order in variants:
        key = tuple(order)
        if key in seen:
            continue
        seen.add(key)
        dedup.append((label, order))
    return dedup


def _limit_variants(variants, max_count: int):
    if max_count <= 0 or len(variants) <= max_count:
        return variants
    return variants[:max_count]

# ======== 1) Proposed: Folded-Bias (CSA-only to bit w) ========
def emit_folded_bias(n: int):
    """
    CSA-only up to bit (w-1). Majority decision is the carry into 2^w
    (the last cout created at column w-1). No finishing CPA.
    """
    assert n % 2 == 1 and n >= 3
    th = (n + 1) // 2
    w  = math.ceil(math.log2(th))
    K  = (1 << w) - th

    # Build K constants per column < w
    consts = defaultdict(list)
    for j in range(w):
        if ((K >> j) & 1) == 1:
            consts[j].append(f"K{j}")

    # Run CSA macro
    raw_inputs = [f"x[{i}]" for i in range(n)]
    ops, wires, residual_by_col, const_decl = csa_macro_schedule_all_columns(raw_inputs, consts)

    # Extract final maj bit (last carry produced at column w-1)
    # Re-simulate the last column cheaply:
    # Build the column queue again to learn last cout
    from collections import deque as _dq
    col_bits = defaultdict(_dq)
    # collect carries from ops by column
    for col, kind, a, b, cin, s, k in ops:
        if col+1 >= 1:
            col_bits[col+1].append(k)
    # inject Ks
    if w > 0:
        for j in range(w):
            if ((K >> j) & 1) == 1:
                col_bits[j].append(f"K{j}")
    # last column is (w-1)
    last_cout = None
    def fold_for_last(queue):
        nonlocal last_cout
        if not queue: return
        acc = queue.popleft()
        while len(queue) >= 2:
            queue.popleft(); queue.popleft()
            last_cout = "temp_carry"  # just mark something non-None
        if len(queue) == 1:
            queue.popleft()
            last_cout = "temp_carry"

    if w == 0:
        maj_cout = "1'b0"
    else:
        q = _dq(col_bits.get(w-1, []))
        fold_for_last(q)
        # We don’t know the exact name without replaying IDs; use a robust rule:
        # In our ops list, the largest FA id at column (w-1) produced the last carry.
        last_k = None
        for col, kind, a, b, cin, s, k in ops:
            if col == (w-1):
                last_k = k
        maj_cout = last_k if last_k is not None else "1'b0"

    # Verilog (unchanged behavior)
    lines = []
    lines += _verilog_header(n, "Folded-Bias Majority (CSA-only, macro-structured)")
    lines.append(f"module maj_fb_{n} (input  wire [{n-1}:0] x, output wire maj);")
    lines.append(f"  // Parameters: th={th}, w={w}, K={K}, schedule={_normalize_schedule_mode(SCHEDULE_MODE)}")
    for j in range(w):
        if ((K >> j) & 1) == 1:
            lines.append(f"  wire K{j} = 1'b1;")

    if ops:
        lines.append("")
        lines.append("  // -------- CSA macro schedule --------")
        for (s,k) in wires:
            lines.append(f"  wire {s}, {k};")
        for (col, kind, a, b, cin, s, k) in ops:
            lines.append(f"  fa u_c{col}_{kind}_{s}(.a({a}), .b({b}), .cin({cin}), .sum({s}), .cout({k}));")

    lines.append("")
    lines.append(f"  assign maj = {maj_cout};")
    lines.append("endmodule")
    lines.append("")
    lines.append(f"// FA count (folded-bias, CSA-only) for n={n}: total={len(ops)}")
    fa_level_count = _fa_max_levels([(a, b, cin, s, k) for (_, _, a, b, cin, s, k) in ops])

    stats = {
        "n": n,
        "threshold": th,
        "w_bits": w,
        "bias_K": K,
        "schedule_mode": _normalize_schedule_mode(SCHEDULE_MODE),
        "K_bits_set": [j for j in range(w) if ((K >> j) & 1) == 1],
        "fa_count": len(ops),
        "fa_levels": fa_level_count,
        "maj_signal": maj_cout,
    }

    return "\n".join(lines), len(ops), ops, [f"K{j}" for j in range(w) if ((K >> j) & 1) == 1], maj_cout, stats


def emit_folded_bias_carryonly(n: int):
    """
    Folded-bias variant that stops CSA scheduling at column (w-1) and outputs
    maj as the carry out of that column (carry into column w).
    """
    assert n % 2 == 1 and n >= 3

    # Decision-only decomposition for n=7:
    #   FA0: (x0,x1,x2) -> (s0,c0)
    #   FA1: (x3,x4,x5) -> (s1,c1)
    #   m0 = MAJ3(s0,s1,x6)
    #   maj = MAJ3(c0,c1,m0)
    # This computes only the needed decision bit (no full HW reconstruction).
    if n == 7:
        lines = []
        lines += _verilog_header(n, "Folded-Bias Carry-Only Majority (decision-only n=7: 2 FA + 2 MAJ3)")
        lines.append("module maj_fb_carryonly_7 (input  wire [6:0] x, output wire maj);")
        lines.append("  // Decision-only path: 2 FAs + 2 majority gates")
        lines.append("  wire raw_s_c0_0, raw_c_c0_0;")
        lines.append("  wire raw_s_c0_1, raw_c_c0_1;")
        lines.append("  wire m_decision_0;")
        lines.append("  fa u_c0_raw_triple_raw_s_c0_0(.a(x[0]), .b(x[1]), .cin(x[2]), .sum(raw_s_c0_0), .cout(raw_c_c0_0));")
        lines.append("  fa u_c0_raw_triple_raw_s_c0_1(.a(x[3]), .b(x[4]), .cin(x[5]), .sum(raw_s_c0_1), .cout(raw_c_c0_1));")
        lines.append("  assign m_decision_0 = (raw_s_c0_0 & raw_s_c0_1) | (raw_s_c0_0 & x[6]) | (raw_s_c0_1 & x[6]);")
        lines.append("  assign maj = (raw_c_c0_0 & raw_c_c0_1) | (raw_c_c0_0 & m_decision_0) | (raw_c_c0_1 & m_decision_0);")
        lines.append("endmodule")
        lines.append("")
        lines.append("// Resource count (folded-bias carry-only, decision-only n=7): FA=2, MAJ3=2")

        stats = {
            "n": 7,
            "threshold": 4,
            "decision_only": True,
            "schedule_mode": "decision_only_n7",
            "fa_count": 2,
            "maj3_count": 2,
            "fa_levels": 1,
            "decision_levels": 3,  # FA -> MAJ -> MAJ
            "maj_signal": "maj",
        }

        return "\n".join(lines), 2, [], [], "maj", stats

    th = (n + 1) // 2
    w = math.ceil(math.log2(th))
    K = (1 << w) - th
    stop_col = w - 1

    consts = defaultdict(list)
    for j in range(w):
        if ((K >> j) & 1) == 1:
            consts[j].append(f"K{j}")

    raw_inputs = [f"x[{i}]" for i in range(n)]
    ops, wires, residual_by_col, const_decl, last_k_stop = csa_macro_schedule_upto_column(
        raw_inputs,
        consts,
        stop_col,
    )

    maj_cout = last_k_stop if last_k_stop is not None else "1'b0"

    lines = []
    lines += _verilog_header(n, "Folded-Bias Carry-Only Majority (CSA stops at w-1)")
    lines.append(f"module maj_fb_carryonly_{n} (input  wire [{n-1}:0] x, output wire maj);")
    lines.append(f"  // Parameters: th={th}, w={w}, K={K}, stop_col={stop_col}, schedule={_normalize_schedule_mode(SCHEDULE_MODE)}")
    for j in range(w):
        if ((K >> j) & 1) == 1:
            lines.append(f"  wire K{j} = 1'b1;")

    if ops:
        lines.append("")
        lines.append("  // -------- CSA macro schedule (up to stop_col) --------")
        for (s, k) in wires:
            lines.append(f"  wire {s}, {k};")
        for (col, kind, a, b, cin, s, k) in ops:
            lines.append(f"  fa u_c{col}_{kind}_{s}(.a({a}), .b({b}), .cin({cin}), .sum({s}), .cout({k}));")

    lines.append("")
    lines.append(f"  assign maj = {maj_cout};")
    lines.append("endmodule")
    lines.append("")
    lines.append(f"// FA count (folded-bias carry-only) for n={n}: total={len(ops)}")
    fa_level_count = _fa_max_levels([(a, b, cin, s, k) for (_, _, a, b, cin, s, k) in ops])

    stats = {
        "n": n,
        "threshold": th,
        "w_bits": w,
        "bias_K": K,
        "stop_col": stop_col,
        "schedule_mode": _normalize_schedule_mode(SCHEDULE_MODE),
        "K_bits_set": [j for j in range(w) if ((K >> j) & 1) == 1],
        "fa_count": len(ops),
        "fa_levels": fa_level_count,
        "maj_signal": maj_cout,
    }

    return "\n".join(lines), len(ops), ops, [f"K{j}" for j in range(w) if ((K >> j) & 1) == 1], maj_cout, stats


# ======== 2) Baseline STRICT (paper scaffold) ========
def emit_baseline_strict(n: int):
    """
    Literal paper flow:
      * Embed Maj_n into Maj_N with N = 2^p - 1 (p = ceil(log2(n+1))).
      * Fix (n_big - k) inputs to 1 and (n_big - k) inputs to 0 so the scaffold
        still has N inputs, where n_big = (N-1)//2 and k=(n-1)//2.
      * Build CSA HW tree on those N inputs.
      * Compare HW against Maj_N threshold by adding (th_N - 1) with Cin=1 and
        reading the final carry (overflow).
    """
    assert n % 2 == 1 and n >= 3

    p       = math.ceil(math.log2(n + 1))
    N       = (1 << p) - 1                    # scaffold input count (2^p - 1)
    m       = p                               # comparator width so that 2^m = N + 1
    th_N    = (N + 1) // 2                    # majority threshold for the scaffold
    k       = (n - 1) // 2
    n_big   = (N - 1) // 2
    num_fix = n_big - k                       # number of paired 1/0 constants to add
    assert num_fix >= 0

    # Build HW tree inputs: real signals + num_fix ones + num_fix zeros.
    hw_inputs = [f"x[{i}]" for i in range(n)]
    hw_inputs += ["1'b1"] * num_fix
    hw_inputs += ["1'b0"] * num_fix

    consts = defaultdict(list)  # no per-column constants in baseline
    ops, wires, residual_by_col, _ = csa_macro_schedule_all_columns(hw_inputs, consts)
    hw_bits = [residual_by_col.get(i, "1'b0") for i in range(m)]

    th_mask_bits = [((th_N - 1) >> j) & 1 for j in range(m)]

    lines = []
    lines += _verilog_header(n, "Baseline STRICT (paper scaffold): CSA (N=2^p-1) → HW + th_N - 1 + Cin")
    lines.append(f"module maj_baseline_strict_{n} (input  wire [{n-1}:0] x, output wire maj);")
    lines.append(
        f"  // Scaffold parameters: p={p}, N=2^{p}-1={N}, th_N={th_N}, paired constants={num_fix}, "
        f"schedule={_normalize_schedule_mode(SCHEDULE_MODE)}"
    )

    if ops:
        lines.append("")
        lines.append("  // -------- CSA macro schedule on scaffold inputs --------")
        for (s, ksig) in wires:
            lines.append(f"  wire {s}, {ksig};")
        for (col, kind, a, b, cin, s, ksig) in ops:
            lines.append(f"  fa u_c{col}_{kind}_{s}(.a({a}), .b({b}), .cin({cin}), .sum({s}), .cout({ksig}));")

    lines.append("")
    lines.append("  // -------- HW bits after CSA (single-rail) --------")
    for i in range(m):
        lines.append(f"  wire hw_{i} = {hw_bits[i]};")

    if any(th_mask_bits):
        lines.append("")
        lines.append("  // Threshold constant bits (th_N - 1)")
        for j, bit in enumerate(th_mask_bits):
            if bit:
                lines.append(f"  wire T{j} = 1'b1;")

    lines.append("")
    lines.append("  // -------- Full ripple (m bits) for HW + (th_N - 1) + Cin=1 --------")
    lines.append("  wire c2_0 = 1'b1; // Cin = 1 (paper comparator)")
    for i in range(m):
        b_term = f"T{i}" if th_mask_bits[i] else "1'b0"
        lines.append(f"  wire s2_{i}, c2_{i+1};")
        lines.append(f"  fa u_th_{i}(.a(hw_{i}), .b({b_term}), .cin(c2_{i}), .sum(s2_{i}), .cout(c2_{i+1}));")

    lines.append(f"  wire c2_m = c2_{m};")
    lines.append("")
    lines.append("  assign maj = c2_m;")
    lines.append("endmodule")
    lines.append("")

    total_fas = len(ops) + m
    lines.append(f"// FA count (baseline STRICT, scaffold) for n={n}: CSA={len(ops)}, CPA(th)={m}, total={total_fas}")

    # Collect FA ops (CSA + comparator) for optional BLIF logging
    fa_ops = [(a, b, cin, s, ksig) for (_, _, a, b, cin, s, ksig) in ops]
    for i in range(m):
        a   = f"hw_{i}"
        b   = f"T{i}" if th_mask_bits[i] else "1'b0"
        cin = f"c2_{i}" if i > 0 else "c2_0"
        s   = f"s2_{i}"
        c   = f"c2_{i+1}"
        fa_ops.append((a, b, cin, s, c))

    maj_out = f"c2_{m}"
    const1_names = ["c2_0"] + [f"T{j}" for j, bit in enumerate(th_mask_bits) if bit]
    csa_levels = _fa_max_levels([(a, b, cin, s, k) for (_, _, a, b, cin, s, k) in ops])
    total_levels = csa_levels + m  # ripple comparator adds m sequential FA levels

    stats = {
        "n": n,
        "threshold": (n + 1) // 2,
        "scaffold_p": p,
        "scaffold_inputs": N,
        "scaffold_threshold": th_N,
        "comparator_width": m,
        "schedule_mode": _normalize_schedule_mode(SCHEDULE_MODE),
        "num_fixed_pairs": num_fix,
        "cin_init": 1,
        "csa_fa_count": len(ops),
        "comparator_fa_count": m,
        "total_fa_count": total_fas,
        "csa_levels": csa_levels,
        "total_levels": total_levels,
        "maj_signal": maj_out,
    }

    return '\n'.join(lines), total_fas, fa_ops, const1_names, maj_out, stats

# ========================= BLIF SUPPORT (Canonical) =========================
def _sanitize(sig: str) -> str:
    """Make signal names BLIF-safe: x[3]->x3; keep 1'b0/1'b1 literal."""
    if sig in ("1'b0", "1'b1"):
        return sig
    return sig.replace('[','').replace(']','').replace(' ','_').replace('.', '_')

def _sorted3(a,b,c):
    """Return tuple of three signal names sorted alphabetically, and their permutation map."""
    lst = [a,b,c]
    srt = sorted(lst)
    perm = tuple(lst.index(srt[i]) for i in range(3))  # new_index -> old_index
    return tuple(srt), perm

def _permute_pattern(p, perm):
    """Permute a 3-bit pattern 'p' according to perm (length 3)."""
    if len(p) != 3: return p
    return "".join(p[perm[i]] for i in range(3))

def _emit_names_lines_for_const1(name):
    return [f".names {name}", "1"]

def _write_blif_from_fas_canonical(model_name, n, fa_ops, maj_signal, const1_names, path, maj_only=True, maj_ops=None):
    """
    Emit canonical BLIF:
      * Every 3-input gate sorts its inputs alphabetically.
      * Truth-table rows are minimal, deduped, and patterns are permuted to the sorted order.
      * Constants are explicit (.names CONST1\n1) and CONST0 created on-demand.
    FA expansion:
      - maj_only=True  -> 3x MAJ + 2x NOT per FA (cout MAJ(A,B,C); sum = MAJ(MAJ(~A,B,C), A, ~cout))
      - maj_only=False -> sum as XOR3; cout as MAJ3
    """
    inputs = [f"x{i}" for i in range(n)]
    out = [f".model {model_name}"]
    if inputs: out.append(".inputs " + " ".join(inputs))
    out.append(".outputs maj")

    used_const0 = False
    used_const1 = False

    # Named const-1 declarations
    const1_set = set()
    for k in (const1_names or []):
        ksan = _sanitize(k)
        if ksan not in const1_set:
            const1_set.add(ksan)
            out.extend(_emit_names_lines_for_const1(ksan))

    def map_in(sig):
        nonlocal used_const0, used_const1
        s = _sanitize(sig)
        if s == "1'b0":
            used_const0 = True
            return "CONST0"
        if s == "1'b1":
            used_const1 = True
            return "CONST1"
        if "[" in sig:
            return s.replace("[","").replace("]","")
        return s

    def emit_maj3(A,B,C,OUT, mask=None):
        na, nb, nc = (False, False, False) if mask is None else mask
        (A1,B1,C1), perm = _sorted3(A,B,C)
        mask_orig = [na, nb, nc]
        mask_sorted = [mask_orig[perm_idx] for perm_idx in perm]

        rows = []
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    adjusted = (a ^ mask_sorted[0]) + (b ^ mask_sorted[1]) + (c ^ mask_sorted[2])
                    if adjusted >= 2:
                        rows.append(f"{a}{b}{c}")

        rows = sorted(set(rows))
        out.append(f".names {A1} {B1} {C1} {OUT}")
        for r in rows:
            out.append(f"{r} 1")

    def emit_xor3(A,B,C,S):
        # XOR3 canonical minterms (odd parity): 001,010,100,111
        (A1,B1,C1), perm = _sorted3(A,B,C)
        rows = ["001","010","100","111"]
        rows = [_permute_pattern(r, perm) for r in rows]
        out.append(f".names {A1} {B1} {C1} {S}")
        for r in rows:
            out.append(f"{r} 1")

    # Expand each FA
    for i,(a,b,cin,s,k) in enumerate(fa_ops):
        A = map_in(a); B = map_in(b); C = map_in(cin)
        S = _sanitize(s); K = _sanitize(k)

        if maj_only:
            # MAJ-only FA without explicit NOT nodes
            emit_maj3(A,B,C,K)
            op1  = f"fa{i}_op1";  emit_maj3(A,B,C,op1, mask=(True, False, False))
            emit_maj3(op1,A,K,S, mask=(False, False, True))
        else:
            emit_xor3(A,B,C,S)                 # sum
            emit_maj3(A,B,C,K)                 # cout

    # Optional explicit MAJ3-only nodes (used by decision-only variants)
    for (a, b, c, out_sig) in (maj_ops or []):
        A = map_in(a); B = map_in(b); C = map_in(c)
        OUT = _sanitize(out_sig)
        emit_maj3(A, B, C, OUT)

    # Literal constants
    if used_const1 and "CONST1" not in const1_set:
        out.extend(_emit_names_lines_for_const1("CONST1"))
    if used_const0:
        out.append(".names CONST0")  # const-0, no cubes

    # Connect top output
    out.append(f".names {_sanitize(maj_signal)} maj")
    out.append("1 1")
    out.append(".end")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(out))


def _resolve_mockturtle_bin():
    if not USE_MOCKTURTLE_SCORING:
        return None

    local_root = os.path.dirname(os.path.abspath(__file__))
    candidate = MOCKTURTLE_BIN
    if not os.path.isabs(candidate):
        candidate = os.path.join(local_root, candidate)

    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate

    via_path = shutil.which(MOCKTURTLE_BIN)
    if via_path:
        return via_path
    return None


def _parse_mockturtle_result(stdout_text: str):
    for line in stdout_text.splitlines():
        s = line.strip()
        if not s.startswith("RESULT "):
            continue
        fields = {}
        for token in s.split()[1:]:
            if "=" not in token:
                continue
            key, val = token.split("=", 1)
            try:
                fields[key] = int(val)
            except ValueError:
                fields[key] = val
        if "mig_after" in fields:
            return fields
    return None


def _mockturtle_recipe_list():
    if isinstance(MOCKTURTLE_RECIPES, str):
        recipes = [MOCKTURTLE_RECIPES.strip()] if MOCKTURTLE_RECIPES.strip() else []
    else:
        recipes = [str(r).strip() for r in (MOCKTURTLE_RECIPES or []) if str(r).strip()]
    return recipes or ["resub"]


def _run_mockturtle_on_blif(mock_bin: str, blif_path: str, recipe: str = "resub"):
    base_cmd = [
        mock_bin,
        "--input", blif_path,
        "--rounds", str(MOCKTURTLE_ROUNDS),
        "--max-pis", str(MOCKTURTLE_MAX_PIS),
        "--max-inserts", str(MOCKTURTLE_MAX_INSERTS),
    ]

    cmd = base_cmd + ["--recipe", recipe]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)

    # Backward-compat fallback for binaries that do not support --recipe.
    if proc.returncode != 0 and recipe == "resub":
        if "Unknown argument: --recipe" in (proc.stderr or ""):
            proc = subprocess.run(base_cmd, check=False, capture_output=True, text=True)

    if proc.returncode != 0:
        return None
    fields = _parse_mockturtle_result(proc.stdout)
    if fields is not None and "recipe" not in fields:
        fields["recipe"] = recipe
    return fields


def _estimated_structural_cost(fa_ops, maj_ops):
    if MAJ_ONLY_FA:
        # FA -> 3 MAJ nodes in canonical MAJ-only expansion.
        return (3 * len(fa_ops)) + len(maj_ops)
    # FA -> XOR3 + MAJ3 in mixed form.
    return (2 * len(fa_ops)) + len(maj_ops)


def _normalize_net_data_for_blif(net_data):
    """
    Normalize supported netlist tuple shapes to:
      (fa_ops, maj_ops, const1_names, maj_signal)
    """
    if len(net_data) == 3:
        fa_ops, const1_names, maj_signal = net_data
        fa_ops, maj_signal, const1_names = _prepare_for_emit(fa_ops, maj_signal, const1_names)
        return fa_ops, [], const1_names, maj_signal

    if len(net_data) == 4:
        fa_ops, maj_ops, const1_names, maj_signal = net_data
        return list(fa_ops), list(maj_ops), sorted(set(const1_names or [])), maj_signal

    raise AssertionError(f"Unsupported net_data tuple size: {len(net_data)}")


def _select_best_variant_with_mockturtle(design_name: str, n: int, variants, mock_bin):
    """
    variants: list[(label, net_data)]
      net_data tuple shape:
        * (fa_ops, const1_names, maj_signal)
        * (fa_ops, maj_ops, const1_names, maj_signal)
    """
    evaluations = []
    for idx, (label, net_data) in enumerate(variants):
        fa_ops, maj_ops, const1_names, maj_signal = _normalize_net_data_for_blif(net_data)
        estimated = _estimated_structural_cost(fa_ops, maj_ops)

        mt = None
        if mock_bin is not None:
            with tempfile.TemporaryDirectory(prefix=f"mt_{design_name}_") as td:
                in_blif = os.path.join(td, f"{design_name}_{idx}.blif")
                _write_blif_from_fas_canonical(
                    model_name=f"{design_name}_{idx}",
                    n=n,
                    fa_ops=fa_ops,
                    maj_signal=maj_signal,
                    const1_names=const1_names,
                    path=in_blif,
                    maj_only=MAJ_ONLY_FA,
                    maj_ops=maj_ops,
                )
                recipe_results = []
                for ridx, recipe in enumerate(_mockturtle_recipe_list()):
                    mt_curr = _run_mockturtle_on_blif(mock_bin, in_blif, recipe=recipe)
                    if mt_curr is None:
                        continue
                    mt_curr["recipe_index"] = ridx
                    recipe_results.append(mt_curr)

                if recipe_results:
                    def _mt_score(item):
                        return (
                            item.get("mig_after", 10**9),
                            item.get("depth_after", 10**9),
                            item.get("mig_before", 10**9),
                            item.get("depth_before", 10**9),
                            item.get("klut_gates", 10**9),
                            item.get("recipe_index", 10**9),
                        )

                    mt = min(recipe_results, key=_mt_score)

        if mt is not None:
            score = (
                mt.get("mig_after", 10**9),
                mt.get("depth_after", 10**9),
                mt.get("mig_before", 10**9),
                mt.get("depth_before", 10**9),
                mt.get("klut_gates", 10**9),
                estimated,
                idx,
            )
        else:
            score = (estimated, len(fa_ops), idx)

        evaluations.append({
            "label": label,
            "score": score,
            "mockturtle": mt,
            "net_data": (fa_ops, maj_ops, const1_names, maj_signal),
            "estimated": estimated,
        })

    if not evaluations:
        return None, []

    best = min(evaluations, key=lambda item: item["score"])
    return best, evaluations

# ---------- build BLIF netlists from FA ops ----------
def build_folded_bias_full_netlist(n: int, raw_inputs=None):
    """Return (fa_ops, const1_names, maj_out) matching emit_folded_bias (v1/full)."""
    assert n % 2 == 1 and n >= 3

    th = (n + 1) // 2
    w = math.ceil(math.log2(th))
    K = (1 << w) - th

    consts = defaultdict(list)
    const1_names = []
    for j in range(w):
        if ((K >> j) & 1) == 1:
            name = f"K{j}"
            consts[j].append(name)
            const1_names.append(name)

    if raw_inputs is None:
        raw_inputs = [f"x[{i}]" for i in range(n)]
    ops, wires, residual_by_col, const_decl = csa_macro_schedule_all_columns(raw_inputs, consts)

    last_k = None
    for col, kind, a, b, cin, s, k in ops:
        if col == (w - 1):
            last_k = k
    maj_out = last_k if last_k is not None else "1'b0"

    fa_ops = [(a, b, cin, s, k) for (_, _, a, b, cin, s, k) in ops]
    return fa_ops, const1_names, maj_out


def build_folded_bias_carryonly_netlist(n: int, raw_inputs=None):
    """Return a canonical netlist matching emit_folded_bias_carryonly.

    Returns either:
      * (fa_ops, const1_names, maj_out) for generic n
      * (fa_ops, maj_ops, const1_names, maj_out) for n=7 decision-only variant
    """
    assert n % 2 == 1 and n >= 3

    if n == 7:
        if raw_inputs is None:
            raw_inputs = [f"x[{i}]" for i in range(n)]
        assert len(raw_inputs) == 7, "raw_inputs must have exactly 7 entries for n=7 decision-only path"
        fa_ops = [
            (raw_inputs[0], raw_inputs[1], raw_inputs[2], "raw_s_c0_0", "raw_c_c0_0"),
            (raw_inputs[3], raw_inputs[4], raw_inputs[5], "raw_s_c0_1", "raw_c_c0_1"),
        ]
        maj_ops = [
            ("raw_s_c0_0", "raw_s_c0_1", raw_inputs[6], "m_decision_0"),
            ("raw_c_c0_0", "raw_c_c0_1", "m_decision_0", "m_decision_1"),
        ]
        return fa_ops, maj_ops, [], "m_decision_1"

    th = (n + 1) // 2
    w = math.ceil(math.log2(th))
    K = (1 << w) - th
    stop_col = w - 1

    consts = defaultdict(list)
    const1_names = []
    for j in range(w):
        if ((K >> j) & 1) == 1:
            name = f"K{j}"
            consts[j].append(name)
            const1_names.append(name)

    if raw_inputs is None:
        raw_inputs = [f"x[{i}]" for i in range(n)]
    ops, wires, residual_by_col, const_decl, last_k_stop = csa_macro_schedule_upto_column(
        raw_inputs,
        consts,
        stop_col,
    )

    maj_out = last_k_stop if last_k_stop is not None else "1'b0"
    fa_ops = [(a, b, cin, s, k) for (_, _, a, b, cin, s, k) in ops]
    return fa_ops, const1_names, maj_out


def build_folded_bias_netlist(n: int):
    """Return (fa_ops, const1_names, maj_out) for folded-bias CSA-only design.

    fa_ops: list of 5-tuples (a, b, cin, s, k)
    const1_names: list of named CONST1 signals (e.g., K0, K1, ...)
    maj_out: signal name of the final majority decision (last cout at column w-1)
    """
    assert n % 2 == 1 and n >= 3
    import math
    from collections import deque, defaultdict

    th = (n + 1) // 2
    w  = math.ceil(math.log2(th))
    K  = (1 << w) - th

    const1_names = [f"K{j}" for j in range(w) if ((K >> j) & 1) == 1]

    fa_id = 0
    fa_ops = []
    last_cout_wm1 = None  # <-- track the last carry created specifically at column (w-1)

    def new_wires(col, tag=""):
        nonlocal fa_id, last_cout_wm1
        s = f"{tag}s_c{col}_{fa_id}"
        k = f"{tag}c_c{col}_{fa_id}"
        fa_id += 1
        # remember the most recent carry created in column (w-1)
        if col == (w - 1):
            last_cout_wm1 = k
        return s, k

    raw = [f"x[{i}]" for i in range(n)]
    col0_sums = deque()
    col_bits  = {1: deque()}

    # Stage A: raw triples at col 0
    while len(raw) >= 3:
        a = raw.pop(0); b = raw.pop(0); c = raw.pop(0)
        s, k = new_wires(0, "raw_")
        fa_ops.append((a, b, c, s, k))
        col0_sums.append(s)
        col_bits[1].append(k)

    # Fold column 0 (+K0 if set)
    col0_queue = deque(list(col0_sums) + raw)
    if ((K >> 0) & 1) == 1:
        col0_queue.append("K0")

    def fold_column(col, queue):
        if not queue:
            return None, []
        carries_out = []
        acc = queue.popleft()
        while len(queue) >= 2:
            b = queue.popleft()
            c = queue.popleft()
            s, k = new_wires(col, "")
            fa_ops.append((acc, b, c, s, k))
            carries_out.append(k)
            acc = s
        if len(queue) == 1:
            b = queue.popleft()
            s, k = new_wires(col, "p_")
            fa_ops.append((acc, b, "1'b0", s, k))
            carries_out.append(k)
            acc = s
        return acc, carries_out

    _, carries_to_1 = fold_column(0, col0_queue)
    for k in carries_to_1:
        col_bits.setdefault(1, deque()).append(k)

    # Columns 1 .. w-2 (serial fold)
    for j in range(1, max(1, w - 1)):
        qj = col_bits.get(j, deque())
        if ((K >> j) & 1) == 1:
            qj.append(f"K{j}")
        _, carries_to_next = fold_column(j, qj)
        if carries_to_next:
            col_bits.setdefault(j + 1, deque()).extend(carries_to_next)

    # Final decision is the LAST carry created at column (w-1)
    if w == 0:
        maj_out = "1'b0"
    else:
        # Ensure we actually fold column (w-1) so last_cout_wm1 gets set when needed
        q = col_bits.get(w - 1, deque())
        if ((K >> (w - 1)) & 1) == 1:
            q.append(f"K{w-1}")
        # If there's work, perform one more fold to generate couts at col (w-1)
        if len(q) >= 1:
            _, _ = fold_column(w - 1, q)
        maj_out = last_cout_wm1 if last_cout_wm1 is not None else "1'b0"

    return fa_ops, const1_names, maj_out

def build_baseline_strict_netlist(n: int, hw_inputs=None):
    assert n % 2 == 1 and n >= 3

    p       = math.ceil(math.log2(n + 1))
    N       = (1 << p) - 1
    m       = p
    th_N    = (N + 1) // 2
    k       = (n - 1) // 2
    n_big   = (N - 1) // 2
    num_fix = n_big - k
    assert num_fix >= 0

    if hw_inputs is None:
        hw_inputs = [f"x[{i}]" for i in range(n)]
        hw_inputs += ["1'b1"] * num_fix
        hw_inputs += ["1'b0"] * num_fix
    assert len(hw_inputs) == N, f"Baseline hw_inputs length must be {N}, got {len(hw_inputs)}"

    consts = defaultdict(list)
    ops, wires, residual_by_col, _ = csa_macro_schedule_all_columns(hw_inputs, consts)

    fa_ops = [(a, b, cin, s, ksig) for (_, _, a, b, cin, s, ksig) in ops]

    th_mask_bits = [((th_N - 1) >> j) & 1 for j in range(m)]
    hw_bits = [residual_by_col.get(i, "1'b0") for i in range(m)]
    for i in range(m):
        a   = hw_bits[i]
        b   = f"T{i}" if th_mask_bits[i] else "1'b0"
        cin = f"c2_{i}" if i > 0 else "c2_0"
        s   = f"s2_{i}"
        c   = f"c2_{i+1}"
        fa_ops.append((a, b, cin, s, c))

    const1_names = ["c2_0"] + [f"T{j}" for j, bit in enumerate(th_mask_bits) if bit]
    maj_out = f"c2_{m}"
    return fa_ops, const1_names, maj_out


def _build_baseline_structural_variants(n: int):
    p = math.ceil(math.log2(n + 1))
    n_big = (1 << p) - 1
    k = (n - 1) // 2
    k_big = (n_big - 1) // 2
    num_fix = k_big - k

    layouts = _baseline_hw_layout_variants(n, num_fix, n_big, SWEEP_RANDOM_LAYOUTS)
    layouts = _limit_variants(layouts, SWEEP_MAX_VARIANTS)

    variants = []
    for label, hw_inputs in layouts:
        variants.append((label, build_baseline_strict_netlist(n, hw_inputs=hw_inputs)))
    return variants


def _build_folded_full_structural_variants(n: int):
    variants = []

    # Paper II-E style: build from smallest scaffold N=2^p-1 and fix 1/0 constants.
    if ENABLE_FOLDED_MAJ_EMBED_SWEEP:
        p = math.ceil(math.log2(n + 1))
        n_big = (1 << p) - 1
        num_fix = (n_big - n) // 2
        if num_fix > 0:
            layouts = _baseline_hw_layout_variants(n, num_fix, n_big, SWEEP_RANDOM_LAYOUTS)
            for label, raw_inputs in layouts:
                variants.append(
                    (f"embedN{n_big}_{label}", build_folded_bias_full_netlist(n_big, raw_inputs=raw_inputs))
                )

    # Direct n-input structural sweep through input permutations.
    if ENABLE_FOLDED_DIRECT_PERM_SWEEP or not variants:
        perms = _input_permutation_variants(n, SWEEP_RANDOM_PERMUTATIONS)
        for label, order in perms:
            raw_inputs = [f"x[{i}]" for i in order]
            variants.append((f"direct_{label}", build_folded_bias_full_netlist(n, raw_inputs=raw_inputs)))

    variants = _limit_variants(variants, SWEEP_MAX_VARIANTS)
    return variants


def _build_folded_carry_structural_variants(n: int):
    variants = []

    if ENABLE_FOLDED_MAJ_EMBED_SWEEP:
        p = math.ceil(math.log2(n + 1))
        n_big = (1 << p) - 1
        num_fix = (n_big - n) // 2
        if num_fix > 0:
            layouts = _baseline_hw_layout_variants(n, num_fix, n_big, SWEEP_RANDOM_LAYOUTS)
            for label, raw_inputs in layouts:
                variants.append(
                    (f"embedN{n_big}_{label}", build_folded_bias_carryonly_netlist(n_big, raw_inputs=raw_inputs))
                )

    if ENABLE_FOLDED_DIRECT_PERM_SWEEP or not variants:
        perms = _input_permutation_variants(n, SWEEP_RANDOM_PERMUTATIONS)
        for label, order in perms:
            raw_inputs = [f"x[{i}]" for i in order]
            variants.append((f"direct_{label}", build_folded_bias_carryonly_netlist(n, raw_inputs=raw_inputs)))

    variants = _limit_variants(variants, SWEEP_MAX_VARIANTS)
    return variants


def _eval_signal(sig, env):
    if sig == "1'b0":
        return 0
    if sig == "1'b1":
        return 1
    if sig in env:
        return env[sig]
    raise KeyError(sig)


def _simulate_fa_netlist(n, fa_ops, const1_names, maj_signal, x_bits):
    env = {}
    for i in range(n):
        env[f"x[{i}]"] = x_bits[i]
    for cname in (const1_names or []):
        env[cname] = 1

    for a, b, cin, s, k in fa_ops:
        av = _eval_signal(a, env)
        bv = _eval_signal(b, env)
        cv = _eval_signal(cin, env)
        env[s] = av ^ bv ^ cv
        env[k] = (av & bv) | (av & cv) | (bv & cv)

    return _eval_signal(maj_signal, env)


def _simulate_logic_netlist(n, fa_ops, maj_ops, const1_names, maj_signal, x_bits):
    env = {}
    for i in range(n):
        env[f"x[{i}]"] = x_bits[i]
    for cname in (const1_names or []):
        env[cname] = 1

    for a, b, cin, s, k in (fa_ops or []):
        av = _eval_signal(a, env)
        bv = _eval_signal(b, env)
        cv = _eval_signal(cin, env)
        env[s] = av ^ bv ^ cv
        env[k] = (av & bv) | (av & cv) | (bv & cv)

    for a, b, c, out_sig in (maj_ops or []):
        av = _eval_signal(a, env)
        bv = _eval_signal(b, env)
        cv = _eval_signal(c, env)
        env[out_sig] = 1 if (av + bv + cv) >= 2 else 0

    return _eval_signal(maj_signal, env)


def run_equivalence_self_check(n: int, design_netlists):
    """
    Exhaustive equivalence check against ground-truth majority.
    design_netlists:
      dict[name] =
        * (fa_ops, const1_names, maj_signal)
        * or (fa_ops, maj_ops, const1_names, maj_signal)
    """
    if not design_netlists:
        return

    th = (n + 1) // 2
    total_patterns = 1 << n
    for pat in range(total_patterns):
        x_bits = [(pat >> i) & 1 for i in range(n)]
        gold = 1 if sum(x_bits) >= th else 0

        for name, net_data in design_netlists.items():
            if len(net_data) == 3:
                fa_ops, const1_names, maj_signal = net_data
                maj_ops = []
            elif len(net_data) == 4:
                fa_ops, maj_ops, const1_names, maj_signal = net_data
            else:
                raise AssertionError(f"Self-check failed ({name}): unsupported netlist tuple shape")
            try:
                got = _simulate_logic_netlist(n, fa_ops, maj_ops, const1_names, maj_signal, x_bits)
            except KeyError as exc:
                raise AssertionError(f"Self-check failed ({name}): undefined signal {exc}") from exc
            if got != gold:
                bitstr = "".join(str(x_bits[i]) for i in range(n - 1, -1, -1))
                raise AssertionError(
                    f"Self-check failed ({name}): n={n}, x={bitstr}, expected={gold}, got={got}"
                )

    print(
        f"Equivalence self-check passed: n={n}, patterns={total_patterns}, "
        f"designs={len(design_netlists)}"
    )


# ---------- main ----------
def main():
    assert N >= 3 and (N % 2 == 1), "N must be odd and >= 3"
    output_root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_ROOT_DIRNAME)

    modules = []
    emitted = set()
    counts = []
    fb_full_stats = None
    fb_carry_stats = None
    bs_stats = None

    def add_module(src: str, name: str):
        if src and name not in emitted:
            modules.append(src)
            emitted.add(name)

    banner = [
        "// Auto-generated majority circuits (canonical BLIF emission)",
        f"// n = {N}",
        f"// schedule_mode = {_normalize_schedule_mode(SCHEDULE_MODE)}",
        "// Top modules present (depending on config):",
        "//   - maj_fb_<n>                (folded-bias full scheduler; legacy)",
        "//   - maj_fb_carryonly_<n>      (folded-bias carry-only, stop at w-1)",
        "//   - maj_baseline_strict_<n>   (baseline threshold path)",
        "// You must provide: module fa(input a,b,cin, output sum,cout);",
        ""
    ]

    fb_full_direct_data = None
    fb_carry_direct_data = None
    bs_direct_data = None
    fb_full_blif_data = None
    fb_carry_blif_data = None
    bs_blif_data = None
    mock_bin = _resolve_mockturtle_bin()

    if INCLUDE_FOLDED_BIAS_FULL:
        v_fb, cnt_fb, _, _, _, fb_full_stats = emit_folded_bias(N)
        add_module(v_fb, f"maj_fb_{N}")
        counts.append(("folded_bias_full", cnt_fb))
        fb_full_direct_data = build_folded_bias_full_netlist(N)

    if INCLUDE_FOLDED_BIAS_CARRYONLY:
        v_fb_carry, cnt_fb_carry, _, _, _, fb_carry_stats = emit_folded_bias_carryonly(N)
        add_module(v_fb_carry, f"maj_fb_carryonly_{N}")
        counts.append(("folded_bias_carryonly", cnt_fb_carry))
        fb_carry_direct_data = build_folded_bias_carryonly_netlist(N)

    if INCLUDE_BASELINE_STRICT:
        v_bs, cnt_bs, _, _, _, bs_stats = emit_baseline_strict(N)
        add_module(v_bs, f"maj_baseline_strict_{N}")
        counts.append(("baseline_strict", cnt_bs))
        bs_direct_data = build_baseline_strict_netlist(N)

    os.makedirs(output_root_dir, exist_ok=True)
    out_v = os.path.join(output_root_dir, OUTPUT_NAME)
    with open(out_v, "w") as f:
        f.write("\n".join(banner + modules))
    print("Wrote Verilog:", out_v)
    for name, cnt in counts:
        print(f"FA count [{name}]: {cnt}")
    count_map = {name: cnt for name, cnt in counts}
    if "folded_bias_full" in count_map and "folded_bias_carryonly" in count_map:
        print(f"FA delta [full - carryonly]: {count_map['folded_bias_full'] - count_map['folded_bias_carryonly']}")

    if USE_MOCKTURTLE_SCORING:
        if mock_bin is not None:
            print(
                f"Mockturtle scorer: {mock_bin} (rounds={MOCKTURTLE_ROUNDS}, "
                f"max_pis={MOCKTURTLE_MAX_PIS}, max_inserts={MOCKTURTLE_MAX_INSERTS}, "
                f"recipes={','.join(_mockturtle_recipe_list())})"
            )
        else:
            print("Mockturtle scorer: binary not found, fallback to structural estimate only.")

    def _print_stats(title: str, stats):
        if not stats:
            return
        print(f"\n[{title}]")
        for key, value in stats.items():
            if isinstance(value, list):
                formatted = ", ".join(str(v) for v in value) if value else "-"
            else:
                formatted = value
            print(f"  {key}: {formatted}")

    if INCLUDE_FOLDED_BIAS_FULL:
        _print_stats("Folded-Bias Full Stats", fb_full_stats)
    if INCLUDE_FOLDED_BIAS_CARRYONLY:
        _print_stats("Folded-Bias Carry-Only Stats", fb_carry_stats)
    if INCLUDE_BASELINE_STRICT:
        _print_stats("Baseline STRICT Stats", bs_stats)

    def _select_design_variant(design_name: str, variants):
        if not variants:
            return None
        best, evaluations = _select_best_variant_with_mockturtle(design_name, N, variants, mock_bin)
        if best is None:
            return None

        mt = best["mockturtle"]
        if mt is not None:
            depth_suffix = ""
            if "depth_after" in mt or "depth_before" in mt:
                depth_suffix = (
                    f", depth_after={mt.get('depth_after')}, depth_before={mt.get('depth_before')}"
                )
            recipe_suffix = ""
            if "recipe" in mt:
                recipe_suffix = f", recipe={mt.get('recipe')}"
            print(
                f"[Variant {design_name}] selected={best['label']}, variants={len(evaluations)}, "
                f"mig_after={mt.get('mig_after')}, mig_before={mt.get('mig_before')}, klut={mt.get('klut_gates')}"
                f"{depth_suffix}{recipe_suffix}"
            )
        else:
            print(
                f"[Variant {design_name}] selected={best['label']}, variants={len(evaluations)}, "
                f"estimated_cost={best['estimated']}"
            )
        return best["net_data"]

    if INCLUDE_FOLDED_BIAS_FULL and fb_full_direct_data is not None:
        if ENABLE_STRUCTURAL_BIAS_SWEEP_HWK:
            fb_full_variants = _build_folded_full_structural_variants(N)
        else:
            fb_full_variants = [("identity", fb_full_direct_data)]
        fb_full_blif_data = _select_design_variant("maj_fb", fb_full_variants)
        if fb_full_blif_data is None:
            fb_full_blif_data = _normalize_net_data_for_blif(fb_full_direct_data)

    if INCLUDE_FOLDED_BIAS_CARRYONLY and fb_carry_direct_data is not None:
        if ENABLE_STRUCTURAL_BIAS_SWEEP_HWK:
            fb_carry_variants = _build_folded_carry_structural_variants(N)
        else:
            fb_carry_variants = [("identity", fb_carry_direct_data)]
        fb_carry_blif_data = _select_design_variant("maj_fb_carryonly", fb_carry_variants)
        if fb_carry_blif_data is None:
            fb_carry_blif_data = _normalize_net_data_for_blif(fb_carry_direct_data)

    if INCLUDE_BASELINE_STRICT and bs_direct_data is not None:
        if ENABLE_STRUCTURAL_BIAS_SWEEP_BASELINE:
            bs_variants = _build_baseline_structural_variants(N)
        else:
            bs_variants = [("identity", bs_direct_data)]
        bs_blif_data = _select_design_variant("maj_baseline_strict", bs_variants)
        if bs_blif_data is None:
            bs_blif_data = _normalize_net_data_for_blif(bs_direct_data)

    if INCLUDE_FOLDED_BIAS_FULL and fb_full_blif_data is not None:
        fb_fa_ops, fb_maj_ops, fb_const_used, fb_out = fb_full_blif_data
        fb_blif = os.path.join(output_root_dir, BLIF_DIR_FOLDED_BIAS_THRESHOLD, f"maj_fb_{N}.blif")
        _write_blif_from_fas_canonical(
            model_name=f"maj_fb_{N}",
            n=N,
            fa_ops=fb_fa_ops,
            maj_signal=fb_out,
            const1_names=fb_const_used,
            path=fb_blif,
            maj_only=MAJ_ONLY_FA,
            maj_ops=fb_maj_ops,
        )
        print("Wrote BLIF (folded-bias threshold):", fb_blif)

    if INCLUDE_FOLDED_BIAS_CARRYONLY and fb_carry_blif_data is not None:
        fb2_fa_ops, fb2_maj_ops, fb2_const_used, fb2_out = fb_carry_blif_data
        fb2_blif = os.path.join(output_root_dir, BLIF_DIR_FOLDED_BIAS_CARRYONLY, f"maj_fb_carryonly_{N}.blif")
        _write_blif_from_fas_canonical(
            model_name=f"maj_fb_carryonly_{N}",
            n=N,
            fa_ops=fb2_fa_ops,
            maj_signal=fb2_out,
            const1_names=fb2_const_used,
            path=fb2_blif,
            maj_only=MAJ_ONLY_FA,
            maj_ops=fb2_maj_ops,
        )
        print("Wrote BLIF (folded-bias carry-only):", fb2_blif)

    if INCLUDE_BASELINE_STRICT and bs_blif_data is not None:
        bs_fa_ops, bs_maj_ops, bs_const_used, bs_out = bs_blif_data
        bs_blif = os.path.join(output_root_dir, BLIF_DIR_BASELINE_THRESHOLD, f"maj_baseline_strict_{N}.blif")
        _write_blif_from_fas_canonical(
            model_name=f"maj_baseline_strict_{N}",
            n=N,
            fa_ops=bs_fa_ops,
            maj_signal=bs_out,
            const1_names=bs_const_used,
            path=bs_blif,
            maj_only=MAJ_ONLY_FA,
            maj_ops=bs_maj_ops,
        )
        print("Wrote BLIF (baseline threshold):", bs_blif)

    if RUN_EQUIV_SELF_CHECK:
        if N <= SELF_CHECK_MAX_N:
            design_netlists = {}
            if INCLUDE_FOLDED_BIAS_FULL and fb_full_blif_data is not None:
                design_netlists[f"maj_fb_{N}"] = fb_full_blif_data
            if INCLUDE_FOLDED_BIAS_CARRYONLY and fb_carry_blif_data is not None:
                design_netlists[f"maj_fb_carryonly_{N}"] = fb_carry_blif_data
            if INCLUDE_BASELINE_STRICT and bs_blif_data is not None:
                design_netlists[f"maj_baseline_strict_{N}"] = bs_blif_data
            run_equivalence_self_check(N, design_netlists)
        else:
            print(f"Skipped equivalence self-check: N={N} exceeds limit {SELF_CHECK_MAX_N}")

if __name__ == "__main__":
    main()
