# Generated majority netlists

This directory contains structural BLIF and Verilog for every odd majority
size from (n=5) through (n=61). Each method has separate `blif/` and
`verilog/` subdirectories.

| Directory | Implementation |
| --- | --- |
| `fb/` | Folded-bias carry-save construction |
| `b/` | Strict scaffolded HW-plus-threshold baseline |
| `apc/` | Parhami accumulative parallel counter |
| `sn/` | Padded-bitonic, Piestrak-style sorting network |
| `csa_pa/` | Representative Dadda/CSA plus Kogge-Stone-style prefix threshold |

The Verilog files are structural and self-contained: each includes the
full-adder primitive it instantiates. The sorting-network and CSA+PA files use
explicit AND, OR, and inversion operations.

`manifest.json` records the method, threshold, byte size, SHA-256 digest, and
functional-check mode for every file. Generated BLIFs are exhaustively checked
through (n=13); larger sizes use the repository's deterministic
boundary-weight plus 1,024 seeded vectors.

The CSA+PA implementation is a representative prefix-family baseline, not a
claim that it is a published state-of-the-art implementation.
