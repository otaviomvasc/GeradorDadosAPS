# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
Data Consistency Checker for AMPL Healthcare Facility Location Models (aps.mod)
Validates data files for feasibility BEFORE running the optimizer.

Usage:
    py check_data_consistency.py LS.dat LS_distdur.dat
    py check_data_consistency.py LS.dat LS_distdur.dat > report.txt
    py check_data_consistency.py LS.dat LS_distdur.dat --output report.txt
    py check_data_consistency.py LS.dat LS_distdur.dat --output report.txt --ascii

Output notes:
    - Progress lines ([CHECK N] ...) always go to STDERR.
    - Full report (including INFO) goes to STDOUT or --output file.
    - When --output is used, the complete report is also mirrored to stderr.
    - Unicode symbols are used on a TTY; plain ASCII when redirected or --ascii is passed.
"""

import argparse
import math
import re
import sys
from collections import defaultdict


# ──────────────────────────────────────────────────────────────────────────────
# Output routing
# ──────────────────────────────────────────────────────────────────────────────

_report_file = None   # set when --output is used


def _rprint(*args, **kwargs):
    """Print to report destination.
    - If --output is active: writes to file + mirrors to stderr.
    - Otherwise: writes to stdout.
    """
    if _report_file is not None:
        file_kwargs = {k: v for k, v in kwargs.items() if k != 'file'}
        print(*args, file=_report_file, **file_kwargs)
        print(*args, file=sys.stderr, **file_kwargs)
    else:
        print(*args, **kwargs)


def _progress(msg):
    """Progress messages always go to stderr only."""
    print(msg, file=sys.stderr)


# # ──────────────────────────────────────────────────────────────────────────────
# # Unicode vs ASCII
# # ──────────────────────────────────────────────────────────────────────────────

# USE_UNICODE = True


# def _sym(u, a):
#     return u if USE_UNICODE else a


# def _ellipsis():
#     return _sym('\u2026', '...')


# def _dash():
#     return _sym('\u2014', '-')


# def _rule(n=76):
#     return _sym('\u00b7', '-') * n


# def _arrow():
#     return _sym('\u25b8', '>')

# ------------------------------------------------------------------
# ASCII-only output (prevents encoding issues in Windows, AMPL, GLPK,
# redirected files, CI pipelines, editors, etc.)
# ------------------------------------------------------------------
USE_UNICODE = False

def _sym(unused_unicode, ascii_text):
    return ascii_text

def _ellipsis():
    return "..."

def _dash():
    return "-"

def _rule(n=76):
    return "-" * n

def _arrow():
    return ">"
# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def strip_comments(content):
    """Remove AMPL-style # comments."""
    return re.sub(r'#[^\n]*', '', content)


def _fmt_table(headers, rows):
    """Return lines for a plain-text table."""
    widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in row] for row in rows]
    for row in str_rows:
        for k, cell in enumerate(row):
            widths[k] = max(widths[k], len(cell))
    border = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'

    def fmt_row(cells):
        return '|' + '|'.join(f' {c:<{widths[k]}} ' for k, c in enumerate(cells)) + '|'

    lines = [border, fmt_row(headers), border]
    for row in str_rows:
        lines.append(fmt_row(row))
    lines.append(border)
    return lines


def _scalar(content, name):
    """Parse a scalar AMPL param, e.g. 'param BUDGET := 123.45;'. Returns float or None."""
    m = re.search(rf'\bparam\s+{re.escape(name)}\s*:=\s*([0-9eE+\-.]+)\s*;', content)
    return float(m.group(1)) if m else None


def _parse_triplets(content, param_name):
    """Parse triplet blocks: param NAME := i j value ... ;
    Returns dict[(i,j)] = float."""
    m = re.search(rf'\bparam\s+{re.escape(param_name)}\b[^:=]*:=\s*([\s\S]*?);', content)
    if not m:
        return {}
    result = {}
    tokens = m.group(1).split()
    it = iter(tokens)
    try:
        while True:
            i = next(it)
            j = next(it)
            v = next(it)
            if v == '.':
                continue
            try:
                result[(i, j)] = float(v)
            except ValueError:
                pass
    except StopIteration:
        pass
    return result


def _parse_key_value(content, param_name):
    """Parse key-value blocks: param NAME := key val key val ... ;
    Returns dict[key] = float."""
    m = re.search(rf'\bparam\s+{re.escape(param_name)}\b[^:=]*:=\s*([\s\S]*?);', content)
    if not m:
        return {}
    result = {}
    tokens = m.group(1).split()
    it = iter(tokens)
    try:
        while True:
            k = next(it)
            v = next(it)
            if v != '.':
                try:
                    result[k] = float(v)
                except ValueError:
                    pass
    except StopIteration:
        pass
    return result


def _parse_multicolumn(content, col_names):
    """Parse a multi-column param block:
        param : col1 col2 col3 :=
            row_id  v1  v2  v3
            ...
        ;
    Returns dict[col_name] -> dict[row_id] -> float | None (for '.')
    col_names is the list of column headers as they appear in the param line.
    """
    # Build regex matching any ordering/spacing of the given column names
    header_pattern = r'\bparam\s*:\s*' + r'\s+'.join(re.escape(c) for c in col_names) + r'\s*:=\s*([\s\S]*?);'
    # Also try with colons: param : I : W IVS :=
    header_pattern2 = (r'\bparam\s*:\s*' +
                       r'(?:\w+\s*:\s*)?' +      # optional "I :" prefix
                       r'\s+'.join(re.escape(c) for c in col_names) + r'\s*:=\s*([\s\S]*?);')
    m = re.search(header_pattern, content) or re.search(header_pattern2, content)
    if not m:
        return {c: {} for c in col_names}
    result = {c: {} for c in col_names}
    n = len(col_names)
    for line in m.group(1).strip().split('\n'):
        parts = line.split()
        if len(parts) < n + 1:
            continue
        row_id = parts[0]
        for idx, col in enumerate(col_names):
            v = parts[idx + 1]
            if v != '.':
                try:
                    result[col][row_id] = float(v)
                except ValueError:
                    pass
    return result


def _parse_cnes_transposed(content, param_name):
    """Parse CNES1(tr) style: rows are locations, columns are team types.
    Returns dict[(team_type, location)] = float.
    Also returns list of team_types parsed from the header.
    """
    m = re.search(
        rf'\bparam\s+{re.escape(param_name)}\s*\(tr\)\s*:\s*([\w\s]+)\s*:=\s*([\s\S]*?);',
        content
    )
    if not m:
        return {}, []
    col_header_str = m.group(1).strip()
    team_types = col_header_str.split()
    result = {}
    for line in m.group(2).strip().split('\n'):
        parts = line.split()
        if len(parts) < len(team_types) + 1:
            continue
        loc = parts[0]
        for idx, tt in enumerate(team_types):
            v = parts[idx + 1]
            if v != '.':
                try:
                    result[(tt, loc)] = float(v)
                except ValueError:
                    pass
    return result, team_types


def _parse_cnes_normal(content, param_name):
    """Parse CNES2/CNES3 style: param CNES2: SHC1 := EQ2 10 ;
    Returns dict[(team_type, facility)] = float.
    Also returns list of facilities parsed from the header.
    """
    m = re.search(
        rf'\bparam\s+{re.escape(param_name)}\s*:\s*([\w\s]+)\s*:=\s*([\s\S]*?);',
        content
    )
    if not m:
        return {}, []
    facilities = m.group(1).strip().split()
    result = {}
    for line in m.group(2).strip().split('\n'):
        parts = line.split()
        if len(parts) < len(facilities) + 1:
            continue
        team_type = parts[0]
        for idx, fac in enumerate(facilities):
            v = parts[idx + 1]
            if v != '.':
                try:
                    result[(team_type, fac)] = float(v)
                except ValueError:
                    pass
    return result, facilities


# ──────────────────────────────────────────────────────────────────────────────
# Diagnostic class
# ──────────────────────────────────────────────────────────────────────────────

class Diagnostic:
    def __init__(self, level, title, what='', why='', fix='',
                 table_headers=None, table_rows=None):
        self.level = level
        self.title = title
        self.what = what
        self.why = why
        self.fix = fix
        self.table_headers = table_headers or []
        self.table_rows = table_rows or []

    def render(self):
        # if USE_UNICODE:
        #     icons = {'ERROR': '\u274c', 'WARNING': '\u26a0 ', 'INFO': '\u2139 '}
        # else:
        #     icons = {'ERROR': '[ERROR]  ', 'WARNING': '[WARNING]', 'INFO': '[INFO]   '}
        icons = {
            'ERROR':   '[ERROR]',
            'WARNING': '[WARNING]',
            'INFO':    '[INFO]'
        }

        icon = icons.get(self.level, '[?]')
        lines = [
            f"{icon} {self.level}: {self.title}",
            "  " + _rule(76),
        ]
        if self.what:
            lines.append(f"  {_arrow()} WHAT:")
            for sub in self._wrap(self.what, 72):
                lines.append(f"      {sub}")
        if self.why:
            lines.append(f"  {_arrow()} WHY:")
            for sub in self.why.split('\n'):
                lines.append(f"      {sub}")
        if self.table_headers and self.table_rows:
            lines.append(f"  {_arrow()} DETAILS:")
            for tline in _fmt_table(self.table_headers, self.table_rows):
                lines.append(f"      {tline}")
        if self.fix:
            lines.append(f"  {_arrow()} FIX:")
            for sub in self.fix.split('\n'):
                lines.append(f"      {sub}")
        lines.append("  " + _rule(76))
        return '\n'.join(lines)

    @staticmethod
    def _wrap(text, width):
        words, line, out = text.split(), [], []
        for w in words:
            if sum(len(x) + 1 for x in line) + len(w) > width and line:
                out.append(' '.join(line))
                line = [w]
            else:
                line.append(w)
        if line:
            out.append(' '.join(line))
        return out


# ──────────────────────────────────────────────────────────────────────────────
# DataValidator class
# ──────────────────────────────────────────────────────────────────────────────

class DataValidator:

    # Constants mirrored from aps.mod
    POP_PER_TEAM    = 3000
    SIZE_DEFAULT    = 3
    SIZE_MAX        = 5
    MULTI_SIZE      = 9     # eMulti covers 9 eSF-equivalent teams
    RATIO_TOL       = 0.02  # tolerance for sum-to-1 on step-down ratios
    DIST_SCALE      = 1000  # metres -> km divisor

    def __init__(self):
        # ── sets ──────────────────────────────────────────────────────────────
        self.I   = set()
        self.E   = {1: set(), 2: set(), 3: set()}
        self.EL  = {1: set(), 2: set(), 3: set()}
        self.CL  = {1: set(), 2: set(), 3: set()}
        self.L   = {1: set(), 2: set(), 3: set()}

        # ── scalar params ─────────────────────────────────────────────────────
        self.BUDGET      = None
        self.I_L1        = None
        self.I_L1_exp    = None
        self.Dmax        = {}      # {1: float, 2: float, 3: float}
        self.U           = {}      # {1: int, 2: int, 3: int}
        self.MAX_TELE    = {}      # {'PHC': float, 'SHC': float, 'THC': float}
        self.MAX_HOME    = {}

        # ── per-facility params ───────────────────────────────────────────────
        self.W      = {}           # {i: float}
        self.IVS    = {}           # {i: float}
        self.SIZE0  = {}           # {j1: int}   (existing L1)
        self.ITEM1  = {}           # {j1: int}
        self.ITEM2  = {}
        self.ITEM3  = {}
        self.FC1    = {}           # {j1: float}
        self.FC2    = {}
        self.FC3    = {}
        self.VC1    = {}
        self.VC2    = {}
        self.VC3    = {}
        self.C2     = {}           # {j2: float}
        self.C3     = {}

        # ── team params ───────────────────────────────────────────────────────
        self.CE1    = {}           # {team: float}
        self.CE2    = {}
        self.CE3    = {}
        self.CNES1  = {}           # {(team, loc): float}
        self.CNES2  = {}
        self.CNES3  = {}

        # ── step-down ratios ──────────────────────────────────────────────────
        # O{level}_0 = fraction returning home; O1_2 = L1->L2; etc.
        self.O1 = {'O1_0': {}, 'O1_2': {}, 'O1_3': {}}
        self.O2 = {'O2_0': {}, 'O2_1': {}, 'O2_3': {}}
        self.O3 = {'O3_0': {}, 'O3_1': {}, 'O3_2': {}}

        # ── distance matrices ─────────────────────────────────────────────────
        self.D0_1 = {}    # {(i, j1): float}  metres
        self.D0_2 = {}    # {(i, j2): float}
        self.D0_3 = {}    # {(i, j3): float}
        self.D1_2 = {}    # {(j1, j2): float}
        self.D1_3 = {}    # {(j1, j3): float}
        self.D2_3 = {}    # {(j2, j3): float}
        self.DL1  = {}    # {(from, to): float}  EL[1] × L[1]

        # ── diagnostics ───────────────────────────────────────────────────────
        self.errors      = []
        self.warnings    = []
        self.info        = []
        self.diagnostics = []
        self._files_read = []

    # ──────────────────────────────────────────────────────────────────────────
    # Entry point
    # ──────────────────────────────────────────────────────────────────────────

    def validate_files(self, filenames):
        for filename in filenames:
            try:
                with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                    raw = f.read()
                n_lines = raw.count('\n')
                _progress(f"  Reading {filename}  ({n_lines} lines)")
                self._parse(strip_comments(raw))
                self._files_read.append((filename, n_lines))
            except FileNotFoundError:
                _progress(f"ERROR: File not found: {filename}")
                return False

        # Derive L[k] = EL[k] ∪ CL[k]
        for k in (1, 2, 3):
            self.L[k] = self.EL[k] | self.CL[k]

        self._run_all_checks()
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Parsing
    # ──────────────────────────────────────────────────────────────────────────

    def _parse(self, content):
        self._parse_sets(content)
        self._parse_scalars(content)
        self._parse_demand(content)
        self._parse_facility_params(content)
        self._parse_teams(content)
        self._parse_step_down(content)
        self._parse_distances(content)

    def _parse_sets(self, content):
        # E[k], EL[k], CL[k]
        for k in (1, 2, 3):
            for key, target in (('E', self.E), ('EL', self.EL), ('CL', self.CL)):
                m = re.search(rf'\bset\s+{key}\[{k}\]\s*:=\s*([\s\S]*?);', content)
                if m:
                    target[k].update(m.group(1).strip().split())

    def _parse_scalars(self, content):
        # Only assign when actually found - never overwrite with None from a later file
        for attr, name in (('BUDGET', 'BUDGET'), ('I_L1', 'I_L1'), ('I_L1_exp', 'I_L1_exp')):
            v = _scalar(content, name)
            if v is not None:
                setattr(self, attr, v)

        # Dmax (indexed by K)
        m = re.search(r'\bparam\s*:\s*K\s*:\s*Dmax\s*:=\s*([\s\S]*?);', content)
        if m:
            tokens = m.group(1).split()
            it = iter(tokens)
            try:
                while True:
                    k = int(next(it))
                    v = float(next(it))
                    self.Dmax[k] = v
            except (StopIteration, ValueError):
                pass

        # U[K]
        u_raw = _parse_key_value(content, 'U')
        for k_str, v in u_raw.items():
            try:
                self.U[int(k_str)] = int(v)
            except ValueError:
                pass

        # MAX_TELE / MAX_HOME (scalar per level)
        for lvl in ('PHC', 'SHC', 'THC'):
            v = _scalar(content, f'MAX_TELE_{lvl}')
            if v is not None:
                self.MAX_TELE[lvl] = v
            v = _scalar(content, f'MAX_HOME_{lvl}')
            if v is not None:
                self.MAX_HOME[lvl] = v

    def _parse_demand(self, content):
        """Parse param: I: W IVS := ... ;"""
        # Try the format with 'I :' prefix: param : I : W IVS :=
        m = re.search(
            r'\bparam\s*:\s*I\s*:\s*W\s+IVS\s*:=\s*([\s\S]*?);', content
        )
        if not m:
            # Fallback: param : I : W := (no IVS column)
            m = re.search(r'\bparam\s*:\s*I\s*:\s*W\s*:=\s*([\s\S]*?);', content)
            if m:
                for line in m.group(1).strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            self.W[parts[0]] = float(parts[1])
                            self.I.add(parts[0])
                        except ValueError:
                            pass
            return
        for line in m.group(1).strip().split('\n'):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    self.W[parts[0]]   = float(parts[1])
                    self.IVS[parts[0]] = float(parts[2])
                    self.I.add(parts[0])
                except ValueError:
                    pass
            elif len(parts) == 2:
                try:
                    self.W[parts[0]] = float(parts[1])
                    self.I.add(parts[0])
                except ValueError:
                    pass

    def _parse_facility_params(self, content):
        """Parse multi-column blocks for L[1], L[2], L[3] facility params."""
        # L[1]: ITEM1 SIZE0 FC1 VC1
        m = re.search(
            r'\bparam\s*:\s*ITEM1\s+SIZE0\s+FC1\s+VC1\s*:=\s*([\s\S]*?);', content
        )
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 5:
                    continue
                loc = parts[0]
                for idx, (attr, target) in enumerate([
                    ('ITEM1', self.ITEM1), ('SIZE0', self.SIZE0),
                    ('FC1',   self.FC1),   ('VC1',   self.VC1)
                ]):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            target[loc] = float(v)
                        except ValueError:
                            pass

        # L[2]: ITEM2 FC2 VC2
        m = re.search(
            r'\bparam\s*:\s*ITEM2\s+FC2\s+VC2\s*:=\s*([\s\S]*?);', content
        )
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                loc = parts[0]
                for idx, (attr, target) in enumerate([
                    ('ITEM2', self.ITEM2), ('FC2', self.FC2), ('VC2', self.VC2)
                ]):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            target[loc] = float(v)
                        except ValueError:
                            pass

        # L[3]: ITEM3 FC3 VC3
        m = re.search(
            r'\bparam\s*:\s*ITEM3\s+FC3\s+VC3\s*:=\s*([\s\S]*?);', content
        )
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                loc = parts[0]
                for idx, (attr, target) in enumerate([
                    ('ITEM3', self.ITEM3), ('FC3', self.FC3), ('VC3', self.VC3)
                ]):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            target[loc] = float(v)
                        except ValueError:
                            pass

        # C2, C3 (simple key-value)
        self.C2 = _parse_key_value(content, 'C2')
        self.C3 = _parse_key_value(content, 'C3')

    def _parse_teams(self, content):
        """Parse CE[k] and CNES[k] params."""
        self.CE1 = _parse_key_value(content, 'CE1')
        self.CE2 = _parse_key_value(content, 'CE2')
        self.CE3 = _parse_key_value(content, 'CE3')

        # CNES1 (transposed): rows = locations, cols = team types
        self.CNES1, _ = _parse_cnes_transposed(content, 'CNES1')

        # CNES2, CNES3 (normal): rows = team types, col headers = facilities
        self.CNES2, _ = _parse_cnes_normal(content, 'CNES2')
        self.CNES3, _ = _parse_cnes_normal(content, 'CNES3')

    def _parse_step_down(self, content):
        """Parse all six step-down ratio params."""
        # O1_0, O1_2, O1_3 - three columns over L[1]
        m = re.search(r'\bparam\s*:\s*O1_0\s+O1_2\s+O1_3\s*:=\s*([\s\S]*?);', content)
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                loc = parts[0]
                for idx, key in enumerate(('O1_0', 'O1_2', 'O1_3')):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            self.O1[key][loc] = float(v)
                        except ValueError:
                            pass

        # O2_0, O2_1, O2_3 - three columns over L[2]
        m = re.search(r'\bparam\s*:\s*O2_0\s+O2_1\s+O2_3\s*:=\s*([\s\S]*?);', content)
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                loc = parts[0]
                for idx, key in enumerate(('O2_0', 'O2_1', 'O2_3')):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            self.O2[key][loc] = float(v)
                        except ValueError:
                            pass

        # O3_0, O3_1, O3_2 - three columns over L[3]
        m = re.search(r'\bparam\s*:\s*O3_0\s+O3_1\s+O3_2\s*:=\s*([\s\S]*?);', content)
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) < 4:
                    continue
                loc = parts[0]
                for idx, key in enumerate(('O3_0', 'O3_1', 'O3_2')):
                    v = parts[idx + 1]
                    if v != '.':
                        try:
                            self.O3[key][loc] = float(v)
                        except ValueError:
                            pass

    def _parse_distances(self, content):
        """Parse all distance/travel-time matrices (metres)."""
        for attr, name in [
            ('D0_1', 'D0_1'), ('D0_2', 'D0_2'), ('D0_3', 'D0_3'),
            ('D1_2', 'D1_2'), ('D1_3', 'D1_3'), ('D2_3', 'D2_3'),
            ('DL1',  'DL1'),
        ]:
            setattr(self, attr, _parse_triplets(content, name))

    # ──────────────────────────────────────────────────────────────────────────
    # Check runner
    # ──────────────────────────────────────────────────────────────────────────

    def _run_all_checks(self):
        W = 80
        _rprint("\n" + "=" * W)
        _rprint("DATA CONSISTENCY VALIDATION  -  aps.mod")
        _rprint("=" * W)
        for fname, nlines in self._files_read:
            _rprint(f"  File : {fname}  ({nlines} lines)")
        _rprint("")

        checks = [
            ("Set Definitions",              self._check_sets),
            ("Parameter Index Consistency",  self._check_param_indices),
            ("Scalar Parameters",            self._check_scalars),
            ("Capacity Values",              self._check_capacities),
            ("Team Data",                    self._check_teams),
            ("Step-Down Ratios",             self._check_step_down),
            ("Demand & IVS Distribution",    self._check_demand_ivs),
            ("Budget Feasibility",           self._check_budget),
            ("Adaptive Connectivity (L1)",   self._check_connectivity),
            ("Distance Matrix Coverage",     self._check_distance_coverage),
        ]

        for idx, (name, fn) in enumerate(checks, 1):
            _progress(f"  [CHECK {idx:2d}] {name} ...")
            _rprint(f"\n[CHECK {idx}] {name}")
            _rprint("-" * W)
            fn()

        self._print_results()

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1 - Set Definitions
    # ──────────────────────────────────────────────────────────────────────────

    def _check_sets(self):
        if not self.I:
            self.errors.append("Set I (demand origins) not found - no W data parsed")
        else:
            self.info.append(f"Set I: {len(self.I)} demand origins")

        for k in (1, 2, 3):
            label = {1: 'PHC', 2: 'SHC', 3: 'THC'}[k]
            el, cl, lk = self.EL[k], self.CL[k], self.L[k]
            if not lk:
                self.errors.append(f"Set L[{k}] ({label}) is empty - no EL or CL defined")
            else:
                self.info.append(
                    f"Set L[{k}] ({label}): {len(lk)} total "
                    f"({len(el)} existing EL[{k}], {len(cl)} candidates CL[{k}])"
                )
            if not self.E[k]:
                self.warnings.append(f"Set E[{k}] (team types for level {k}) not found")
            else:
                self.info.append(f"Set E[{k}]: {sorted(self.E[k])}")

        # EL[k] ⊆ L[k]
        for k in (1, 2, 3):
            stray = self.EL[k] - self.L[k]
            if stray:
                self.errors.append(f"EL[{k}] members not in L[{k}]: {stray}")
        # CL[1] ⊆ I (candidates must be census sectors)
        stray_cl1 = self.CL[1] - self.I
        if self.CL[1] and stray_cl1:
            self.warnings.append(
                f"CL[1] has {len(stray_cl1)} elements not in I "
                f"(candidates should be census sectors): e.g. {list(stray_cl1)[:3]}"
            )

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2 - Parameter Index Consistency
    # ──────────────────────────────────────────────────────────────────────────

    def _check_param_indices(self):
        # W indices ⊆ I
        invalid_w = set(self.W) - self.I
        if invalid_w:
            self.errors.append(f"W has {len(invalid_w)} key(s) not in I: {list(invalid_w)[:5]}")
        elif self.W:
            self.info.append("All W indices are in set I")

        # ITEM / SIZE0 / FC1 indices ⊆ L[1]
        for attr_name, d in (('ITEM1', self.ITEM1), ('SIZE0', self.SIZE0), ('FC1', self.FC1)):
            if d:
                bad = set(d) - self.L[1]
                if bad:
                    self.errors.append(f"{attr_name} has {len(bad)} indices not in L[1]: {list(bad)[:5]}")
                else:
                    self.info.append(f"{attr_name} indices all in L[1] ({len(d)} entries)")

        # ITEM ordering: should be a permutation 1..card(L[1])
        if self.ITEM1:
            vals = sorted(int(v) for v in self.ITEM1.values())
            expected = list(range(1, len(self.ITEM1) + 1))
            if vals != expected:
                self.warnings.append(
                    f"ITEM1 values are not a clean permutation 1..{len(self.L[1])}; "
                    f"got {len(set(vals))} unique values out of {len(vals)}"
                )
            else:
                self.info.append(f"ITEM1 is a valid permutation 1..{len(self.ITEM1)}")

        # C2, C3 ⊆ L[2], L[3]
        for cap_name, d, k in (('C2', self.C2, 2), ('C3', self.C3, 3)):
            if d:
                bad = set(d) - self.L[k]
                if bad:
                    self.errors.append(f"{cap_name} has indices not in L[{k}]: {list(bad)[:5]}")
                else:
                    self.info.append(f"{cap_name} indices all in L[{k}]")

        # CNES1 rows ⊆ EL[1]
        if self.CNES1:
            cnes1_locs = {loc for (_, loc) in self.CNES1}
            bad = cnes1_locs - self.EL[1]
            if bad:
                self.errors.append(f"CNES1 has {len(bad)} location(s) not in EL[1]: {list(bad)[:5]}")
            else:
                self.info.append(f"CNES1: {len(cnes1_locs)} locations × team types parsed")

        # CE1 keys ⊆ E[1]
        if self.CE1 and self.E[1]:
            missing_ce1 = self.E[1] - set(self.CE1)
            if missing_ce1:
                self.errors.append(f"CE1 missing team types: {missing_ce1}")
            else:
                self.info.append(f"CE1 defined for all E[1] team types: {sorted(self.CE1)}")

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3 - Scalar Parameters
    # ──────────────────────────────────────────────────────────────────────────

    def _check_scalars(self):
        # BUDGET
        if self.BUDGET is None:
            self.errors.append("param BUDGET not found")
        elif self.BUDGET <= 0:
            self.errors.append(f"BUDGET = {self.BUDGET:.2f} must be > 0")
        else:
            self.info.append(f"BUDGET = R$ {self.BUDGET:,.2f}")

        # I_L1 / I_L1_exp
        if self.I_L1 is None:
            self.warnings.append("param I_L1 (new PHC construction cost) not found")
        else:
            self.info.append(f"I_L1 = R$ {self.I_L1:,.0f} (annualized with R=4%, N=25yr)")
        if self.I_L1_exp is None:
            self.warnings.append("param I_L1_exp (expansion cost per SIZE unit) not found")
        else:
            self.info.append(f"I_L1_exp = R$ {self.I_L1_exp:,.0f}")

        # Dmax
        if not self.Dmax:
            self.errors.append("param Dmax[K] not found - model cannot build link sets")
        else:
            for k in (1, 2, 3):
                if k not in self.Dmax:
                    self.errors.append(f"Dmax[{k}] missing")
                else:
                    self.info.append(f"Dmax[{k}] = {self.Dmax[k]:,.0f} m")

        # U[K]
        if not self.U:
            self.warnings.append("param U[K] (max new units per level) not found")
        else:
            for k in (1, 2, 3):
                if k not in self.U:
                    self.warnings.append(f"U[{k}] missing")
                else:
                    n_cand = len(self.CL[k])
                    if self.U[k] > n_cand:
                        self.warnings.append(
                            f"U[{k}] = {self.U[k]} > card(CL[{k}]) = {n_cand}; "
                            f"effective limit will be {n_cand}"
                        )
                    else:
                        self.info.append(f"U[{k}] = {self.U[k]}  (CL[{k}] has {n_cand} candidates)")

        # MAX_TELE / MAX_HOME
        for lvl in ('PHC', 'SHC', 'THC'):
            if lvl not in self.MAX_TELE:
                self.warnings.append(f"MAX_TELE_{lvl} not found (defaults to 0)")
            else:
                self.info.append(f"MAX_TELE_{lvl} = {self.MAX_TELE[lvl]:.0%}")
            if lvl not in self.MAX_HOME:
                self.warnings.append(f"MAX_HOME_{lvl} not found (defaults to 0)")
            else:
                self.info.append(f"MAX_HOME_{lvl} = {self.MAX_HOME[lvl]:.0%}")

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4 - Capacity Values
    # ──────────────────────────────────────────────────────────────────────────

    def _check_capacities(self):
        # C1 derived from SIZE0
        if self.SIZE0:
            c1_vals = []
            for j in self.EL[1]:
                sz = int(self.SIZE0.get(j, self.SIZE_DEFAULT))
                c1_vals.append(sz * self.POP_PER_TEAM)
            if c1_vals:
                self.info.append(
                    f"C1 = SIZE0 × {self.POP_PER_TEAM}: "
                    f"min={min(c1_vals):,}, max={max(c1_vals):,} "
                    f"(max expandable={self.SIZE_MAX * self.POP_PER_TEAM:,})"
                )
        else:
            self.info.append(
                f"SIZE0 not explicitly set for any L[1]; "
                f"model default SIZE={self.SIZE_DEFAULT} -> C1_default={self.SIZE_DEFAULT * self.POP_PER_TEAM:,}"
            )

        # SIZE0 values out of valid range
        bad_sz = {j: int(v) for j, v in self.SIZE0.items() if not (1 <= int(v) <= self.SIZE_MAX)}
        if bad_sz:
            self.errors.append(
                f"SIZE0 out of [1,{self.SIZE_MAX}] for {len(bad_sz)} facilities: "
                + ', '.join(f"{j}={v}" for j, v in list(bad_sz.items())[:5])
            )

        # C2
        if self.C2:
            mn, mx = min(self.C2.values()), max(self.C2.values())
            self.info.append(f"C2: {len(self.C2)} entries, min={mn:,.0f}, max={mx:,.0f}")
            if mn < 1000:
                self.warnings.append(f"C2 min capacity {mn:.0f} < 1,000 - seems low for SHC")
        elif self.EL[2]:
            self.errors.append("C2 not defined but EL[2] is non-empty")

        # C3
        if self.C3:
            mn, mx = min(self.C3.values()), max(self.C3.values())
            self.info.append(f"C3: {len(self.C3)} entries, min={mn:,.0f}, max={mx:,.0f}")
            if mn < 500:
                self.warnings.append(f"C3 min capacity {mn:.0f} < 500 - seems low for THC")
        elif self.EL[3]:
            self.errors.append("C3 not defined but EL[3] is non-empty")

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5 - Team Data
    # ──────────────────────────────────────────────────────────────────────────

    def _check_teams(self):
        # CE costs must be positive
        for lvl, ce, e_set in ((1, self.CE1, self.E[1]), (2, self.CE2, self.E[2]),
                               (3, self.CE3, self.E[3])):
            if not ce:
                continue
            non_pos = {t: v for t, v in ce.items() if v < 0}
            if non_pos:
                self.errors.append(f"CE{lvl} has negative team costs: {non_pos}")
            zero_cost = {t: v for t, v in ce.items() if v == 0}
            if zero_cost:
                self.info.append(f"CE{lvl} - zero-cost teams (acceptable placeholder): {list(zero_cost)}")

        # CNES1 completeness: every EL[1] × E[1] pair
        if self.CNES1 and self.EL[1] and self.E[1]:
            missing = [
                (e, j) for j in self.EL[1] for e in self.E[1]
                if (e, j) not in self.CNES1
            ]
            if missing:
                self.warnings.append(
                    f"CNES1 missing {len(missing)} (team, location) pairs "
                    f"(AMPL will use default 0): e.g. {missing[:3]}"
                )
            else:
                self.info.append(
                    f"CNES1 complete: {len(self.EL[1])} locations × {len(self.E[1])} team types"
                )

            # Check eSF == eSB per location (model constraint Team_SF_equal_SBe)
            if 'eSF' in self.E[1] and 'eSB' in self.E[1]:
                mismatch = [
                    j for j in self.EL[1]
                    if self.CNES1.get(('eSF', j), 0) != self.CNES1.get(('eSB', j), 0)
                ]
                if mismatch:
                    rows = [[j, int(self.CNES1.get(('eSF', j), 0)),
                             int(self.CNES1.get(('eSB', j), 0))] for j in mismatch[:10]]
                    self.diagnostics.append(Diagnostic(
                        'WARNING',
                        "eSF <> eSB team counts at some existing PHC",
                        what=(f"{len(mismatch)} existing PHC(s) have CNES1['eSF'] <> CNES1['eSB']. "
                              f"Constraint Team_SF_equal_SBe forces them equal after optimization, "
                              f"so the initial imbalance must be resolved by transfers or hires."),
                        why="aps.mod enforces eSF = eSB at all existing PHC locations.",
                        fix="Set CNES1['eSB', j] = CNES1['eSF', j] in the data, or ensure "
                            "transfers can balance them.",
                        table_headers=["Location", "eSF", "eSB"],
                        table_rows=rows,
                    ))
                else:
                    self.info.append("eSF = eSB parity satisfied at all existing PHC (CNES1)")

            # eMulti sanity: <= ceil(SIZE/MULTI_SIZE)
            if 'eMulti' in self.E[1]:
                bad_multi = []
                for j in self.EL[1]:
                    sz = int(self.SIZE0.get(j, self.SIZE_DEFAULT))
                    expected_max = math.ceil(sz / self.MULTI_SIZE)
                    actual = int(self.CNES1.get(('eMulti', j), 0))
                    if actual > expected_max:
                        bad_multi.append((j, sz, expected_max, actual))
                if bad_multi:
                    self.warnings.append(
                        f"eMulti count exceeds ceil(SIZE/{self.MULTI_SIZE}) at "
                        f"{len(bad_multi)} PHC(s): " +
                        ', '.join(f"{j}(sz={sz},max={em},got={act})"
                                  for j, sz, em, act in bad_multi[:5])
                    )
                else:
                    self.info.append("eMulti counts <= ceil(SIZE/MULTI_SIZE) at all existing PHC")

        # CNES2 / CNES3 completeness
        for lvl, cnes, el_k, e_k, label in (
            (2, self.CNES2, self.EL[2], self.E[2], 'CNES2'),
            (3, self.CNES3, self.EL[3], self.E[3], 'CNES3'),
        ):
            if cnes and el_k and e_k:
                missing = [(e, j) for j in el_k for e in e_k if (e, j) not in cnes]
                if missing:
                    self.warnings.append(
                        f"{label} missing {len(missing)} pairs (AMPL will default to 0): "
                        f"{missing[:3]}"
                    )
                else:
                    self.info.append(f"{label} complete for all EL[{lvl}] × E[{lvl}]")

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6 - Step-Down Ratios
    # ──────────────────────────────────────────────────────────────────────────

    def _check_step_down(self):
        checks = [
            (self.O1, ('O1_0', 'O1_2', 'O1_3'), self.L[1], 'L[1]', 'PHC'),
            (self.O2, ('O2_0', 'O2_1', 'O2_3'), self.L[2], 'L[2]', 'SHC'),
            (self.O3, ('O3_0', 'O3_1', 'O3_2'), self.L[3], 'L[3]', 'THC'),
        ]
        for o_dict, keys, lk, lk_name, label in checks:
            if not any(o_dict[k] for k in keys):
                self.warnings.append(f"Step-down ratios for {label} ({keys[0]}...) not found")
                continue

            sums = {}
            bad_range = []
            for loc in lk:
                total = sum(o_dict[k].get(loc, 0.0) for k in keys)
                sums[loc] = total
                for k in keys:
                    v = o_dict[k].get(loc, 0.0)
                    if not (0.0 <= v <= 1.0):
                        bad_range.append((loc, k, v))

            missing_locs = [loc for loc in lk if not any(o_dict[k].get(loc) is not None for k in keys)]
            bad_sum = {loc: s for loc, s in sums.items()
                       if loc not in missing_locs and abs(s - 1.0) > self.RATIO_TOL}

            if bad_range:
                self.errors.append(
                    f"{label} step-down ratio out of [0,1] at {len(bad_range)} location(s): "
                    + ', '.join(f"{loc}.{k}={v:.3f}" for loc, k, v in bad_range[:3])
                )
            if missing_locs:
                self.warnings.append(
                    f"{label} ratios missing for {len(missing_locs)} of {len(lk)} {lk_name} location(s); "
                    "AMPL will use 0 - flow may be unbalanced"
                )
            if bad_sum:
                rows = [[loc, f"{sums[loc]:.4f}",
                         f"{o_dict[keys[0]].get(loc,0):.3f}",
                         f"{o_dict[keys[1]].get(loc,0):.3f}",
                         f"{o_dict[keys[2]].get(loc,0):.3f}"]
                        for loc in sorted(bad_sum)[:10]]
                self.diagnostics.append(Diagnostic(
                    'WARNING',
                    f"{label} step-down ratios do not sum to 1 at {len(bad_sum)} location(s)",
                    what=(f"Ratios {keys[0]} + {keys[1]} + {keys[2]} should sum to = 1.0 "
                          f"(tolerance +/-{self.RATIO_TOL}). {len(bad_sum)} location(s) deviate."),
                    why="Flow balance constraints R1/R2/R3 distribute patient outflows proportionally. "
                        "Ratios <> 1 create systematic flow imbalances.",
                    fix="Adjust the ratios so their sum = 1.0 per location.",
                    table_headers=["Location", "Sum", keys[0], keys[1], keys[2]],
                    table_rows=rows,
                ))
            if not bad_sum and not missing_locs and not bad_range:
                self.info.append(
                    f"{label} step-down ratios: OK ({len(lk)} locations, all sum to 1 +/-{self.RATIO_TOL})"
                )
            else:
                if bad_sum:
                    self.warnings.append(
                        f"{label} step-down ratios sum <> 1 at {len(bad_sum)} location(s) "
                        f"(worst: {max(bad_sum, key=lambda x: abs(bad_sum[x]-1))}: "
                        f"{max(bad_sum.values(), key=lambda x: abs(x-1)):.4f})"
                    )

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7 - Demand & IVS Distribution
    # ──────────────────────────────────────────────────────────────────────────

    def _check_demand_ivs(self):
        if not self.W:
            self.warnings.append("No demand data (W) found - skipping demand checks")
            return

        vals  = list(self.W.values())
        total = sum(vals)
        lo, hi = min(vals), max(vals)
        sv    = sorted(vals)
        n     = len(sv)
        med   = sv[n // 2] if n % 2 else (sv[n // 2 - 1] + sv[n // 2]) / 2
        avg   = total / n

        self.info.append(f"Total population demand: {total:,.0f}")
        self.info.append(f"Origins: {n}   min={lo:.0f}   max={hi:.0f}   avg={avg:.1f}   median={med:.1f}")

        zero_demand = [i for i, w in self.W.items() if w == 0]
        if zero_demand:
            self.info.append(
                f"Origins with W=0: {len(zero_demand)} "
                f"(e.g. {zero_demand[:3]}) - included in model sets but no patient load"
            )

        # IVS distribution
        if self.IVS:
            ivs_vals = list(self.IVS.values())
            bad_ivs  = [i for i, v in self.IVS.items() if not (0.0 <= v <= 1.0)]
            if bad_ivs:
                self.errors.append(
                    f"IVS out of [0,1] at {len(bad_ivs)} origin(s): "
                    + ', '.join(f"{i}={self.IVS[i]:.4f}" for i in bad_ivs[:5])
                )
            missing_ivs = self.I - set(self.IVS)
            if missing_ivs:
                self.warnings.append(
                    f"IVS missing for {len(missing_ivs)} origin(s) - "
                    f"model will use POP_PER_TEAM default for those"
                )
            # Compute IVS bins (mirrors model: 33%, 66%, 100% percentiles)
            sv_ivs = sorted(ivs_vals)
            m = len(sv_ivs)  # use actual IVS count, not total origin count n
            t33 = sv_ivs[math.ceil(m * 0.33) - 1]
            t66 = sv_ivs[math.ceil(m * 0.66) - 1]
            n_low  = sum(1 for v in ivs_vals if v <= t33)
            n_med  = sum(1 for v in ivs_vals if t33 < v <= t66)
            n_high = sum(1 for v in ivs_vals if v > t66)
            self.info.append(
                f"IVS distribution: low <= {t33:.4f} ({n_low} origins -> POP_IVS=3,500), "
                f"mid <= {t66:.4f} ({n_med} -> 3,000), "
                f"high ({n_high} -> 2,500)"
            )
        else:
            self.warnings.append("IVS not parsed - model will use POP_PER_TEAM=3,000 as default")

        # Total demand vs total L1 capacity (max expandable)
        total_c1_max = len(self.EL[1]) * self.SIZE_MAX * self.POP_PER_TEAM
        total_c1_cur = sum(
            int(self.SIZE0.get(j, self.SIZE_DEFAULT)) * self.POP_PER_TEAM
            for j in self.EL[1]
        ) if self.EL[1] else 0
        if total_c1_max > 0:
            if total > total_c1_max:
                self.errors.append(
                    f"Total demand {total:,.0f} exceeds maximum expandable L1 capacity "
                    f"{total_c1_max:,.0f} (even with all EL[1] at SIZE={self.SIZE_MAX}). "
                    f"New CL[1] units are required."
                )
            elif total > total_c1_cur:
                shortage = total - total_c1_cur
                self.warnings.append(
                    f"Current L1 capacity {total_c1_cur:,.0f} < total demand {total:,.0f} "
                    f"(shortage = {shortage:,.0f}). Expansion or new PHC needed."
                )
            else:
                self.info.append(
                    f"Existing L1 capacity {total_c1_cur:,.0f} >= total demand {total:,.0f} - "
                    f"no new PHC strictly required"
                )

        # Total demand vs C2, C3
        for cap_dict, label, frac_key in (
            (self.C2, 'SHC (L2)', 'O1_2'),
            (self.C3, 'THC (L3)', 'O1_3'),
        ):
            if cap_dict:
                total_cap = sum(cap_dict.values())
                # Rough upper bound on demand routed to this level
                max_ratio = max(
                    (self.O1.get(frac_key, {}).get(j, 0) for j in self.L[1]),
                    default=0.3
                )
                approx_demand = total * max_ratio
                if approx_demand > total_cap:
                    self.warnings.append(
                        f"Approximate {label} demand {approx_demand:,.0f} "
                        f"may exceed total capacity {total_cap:,.0f}"
                    )
                else:
                    self.info.append(
                        f"{label} capacity {total_cap:,.0f} appears sufficient "
                        f"(approx demand <= {approx_demand:,.0f})"
                    )

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 8 - Budget Feasibility
    # ──────────────────────────────────────────────────────────────────────────

    def _check_budget(self):
        if self.BUDGET is None:
            self.warnings.append("Budget check skipped - BUDGET not parsed")
            return

        # ExistingCost = FC1 (existing) + CNES1 × CE1 + FC2 + CNES2×CE2 + FC3 + CNES3×CE3
        fc1_cost = sum(self.FC1.get(j, int(self.SIZE0.get(j, self.SIZE_DEFAULT)) * 3000)
                       for j in self.EL[1])
        cnes1_cost = sum(
            cnt * self.CE1.get(e, 0)
            for (e, j), cnt in self.CNES1.items()
        )
        fc2_cost = sum(self.FC2.get(j, 0) for j in self.EL[2])
        cnes2_cost = sum(cnt * self.CE2.get(e, 0) for (e, j), cnt in self.CNES2.items())
        fc3_cost = sum(self.FC3.get(j, 0) for j in self.EL[3])
        cnes3_cost = sum(cnt * self.CE3.get(e, 0) for (e, j), cnt in self.CNES3.items())

        existing_cost = fc1_cost + cnes1_cost + fc2_cost + cnes2_cost + fc3_cost + cnes3_cost
        available     = self.BUDGET - existing_cost

        self.info.append(f"Estimated ExistingCost = R$ {existing_cost:,.2f}")
        self.info.append(f"  PHC fixed: {fc1_cost:,.2f}   PHC teams: {cnes1_cost:,.2f}")
        self.info.append(f"  SHC fixed: {fc2_cost:,.2f}   SHC teams: {cnes2_cost:,.2f}")
        self.info.append(f"  THC fixed: {fc3_cost:,.2f}   THC teams: {cnes3_cost:,.2f}")
        self.info.append(f"AvailableBudget = R$ {available:,.2f}")

        if existing_cost > self.BUDGET:
            self.errors.append(
                f"ExistingCost R${existing_cost:,.2f} exceeds BUDGET R${self.BUDGET:,.2f}. "
                f"Model will activate budget_slack at high penalty cost."
            )
        else:
            usage_pct = (existing_cost / self.BUDGET) * 100
            self.info.append(
                f"Existing cost uses {usage_pct:.1f}% of budget; "
                f"R${available:,.2f} available for expansion"
            )

        # Annualized I_L1 cost vs available budget
        if self.I_L1 and self.U.get(1, 0) > 0:
            R, N = 0.04, 25
            ia1 = round(self.I_L1 * (R * (1 + R)**N) / ((1 + R)**N - 1), 0)
            min_new_phc_cost = ia1 + sum(self.CE1.values())
            max_affordable = int(available / min_new_phc_cost) if min_new_phc_cost > 0 else 0
            self.info.append(
                f"Annualized I_L1 = R${ia1:,.0f}/yr; "
                f"min new PHC cost = R${min_new_phc_cost:,.0f}/yr; "
                f"budget allows = {max_affordable} new PHC unit(s)"
            )

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 9 - Adaptive Connectivity (replaces R0b spatial-lock)
    # ──────────────────────────────────────────────────────────────────────────

    def _check_connectivity(self):
        """
        Mirrors the adaptive Dmax logic from aps.mod:

            adap_Dmax1[i] = max(Dmax[1], min{j1 in L[1]} D0_1[i,j1])

        Every demand origin must reach >= 1 L1 facility.  Also checks that
        the nearest L1 facility has sufficient capacity for the origin's demand
        (capacity filter mirrors Link01 definition in the model).
        """
        W      = self.W
        d01    = self.D0_1
        dmax1  = self.Dmax.get(1)
        el1    = self.EL[1]
        cl1    = self.CL[1]
        L1     = el1 | cl1

        if not W:
            self.info.append("Connectivity check skipped - no demand data")
            return
        if not d01:
            self.warnings.append("Connectivity check skipped - D0_1 not loaded")
            return
        if dmax1 is None:
            self.warnings.append("Connectivity check skipped - Dmax[1] not found")
            return

        MAX_C1 = self.SIZE_MAX * self.POP_PER_TEAM  # max expandable capacity per EL[1]

        def cap_of(j):
            if j in el1:
                return MAX_C1
            return int(self.SIZE0.get(j, self.SIZE_DEFAULT)) * self.POP_PER_TEAM

        unreachable, adaptive_extensions = [], []
        single_option_load = defaultdict(float)   # j1 -> total demand locked to it alone

        for i in sorted(W):
            # All distances from i to L1
            dists = {j: d01.get((i, j), float('inf')) for j in L1}
            # Adaptive threshold
            min_d = min(dists.values()) if dists else float('inf')
            adap  = max(dmax1, min_d) if min_d < float('inf') else dmax1

            # Link01: within adap_Dmax AND capacity filter
            linked = [j for j in L1
                      if dists.get(j, float('inf')) <= adap and cap_of(j) >= W[i]]

            if not linked:
                unreachable.append((i, W[i], min_d))
            else:
                if min_d > dmax1:
                    adaptive_extensions.append((i, W[i], min_d, dmax1))
                if len(linked) == 1:
                    single_option_load[linked[0]] += W[i]

        # Report unreachable origins
        if unreachable:
            tbl_rows = [[i, f"{w:.0f}", f"{d:.0f}"] for i, w, d in unreachable[:15]]
            self.diagnostics.append(Diagnostic(
                'ERROR',
                f"{len(unreachable)} demand origin(s) have no reachable L1 facility",
                what=(f"{len(unreachable)} origins cannot be assigned to any PHC even "
                      f"after adaptive Dmax extension. This makes the model infeasible."),
                why="DemandOut constraint requires every origin to route all W[i] patients.",
                fix="Add closer CL[1] candidate locations, or increase Dmax[1].",
                table_headers=["Origin", "W", "Min dist (m)"],
                table_rows=tbl_rows,
            ))
            self.errors.append(
                f"Connectivity: {len(unreachable)} origin(s) unreachable from any L1 facility"
            )
        else:
            self.info.append(f"Connectivity: all {len(W)} origins reach >= 1 L1 facility")

        # Report adaptive extensions
        if adaptive_extensions:
            total_ext_pop = sum(w for _, w, _, _ in adaptive_extensions)
            self.info.append(
                f"Adaptive Dmax extended for {len(adaptive_extensions)} origin(s) "
                f"(total pop {total_ext_pop:,.0f}) beyond Dmax[1]={dmax1:,.0f} m"
            )

        # Report capacity stress from single-option demand
        overloaded = {
            j: load for j, load in single_option_load.items()
            if load > MAX_C1
        }
        if overloaded:
            rows = [[j, f"{load:,.0f}", f"{MAX_C1:,}"]
                    for j, load in sorted(overloaded.items(), key=lambda x: -x[1])[:10]]
            self.diagnostics.append(Diagnostic(
                'ERROR',
                f"{len(overloaded)} PHC(s) have single-option locked demand exceeding max capacity",
                what=(f"These PHC(s) are the sole reachable option for their locked origins, "
                      f"and the total locked demand exceeds the maximum expandable capacity "
                      f"of {MAX_C1:,} patients (SIZE={self.SIZE_MAX})."),
                why="Even with full expansion (SIZE=5) the capacity cannot satisfy all locked demand.",
                fix="Add CL[1] candidates closer to the affected origins, or increase Dmax[1].",
                table_headers=["PHC", "Locked demand", "Max C1"],
                table_rows=rows,
            ))
            self.errors.append(
                f"Connectivity: {len(overloaded)} PHC(s) have locked demand > max capacity"
            )
        elif single_option_load:
            self.info.append(
                f"{len(single_option_load)} PHC(s) are sole option for some origins "
                f"(all within max capacity)"
            )

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 10 - Distance Matrix Coverage
    # ──────────────────────────────────────────────────────────────────────────

    def _check_distance_coverage(self):
        MAX_LISTED = 50

        # D0_* full coverage required
        for dist_attr, d_dict, src_set, dst_set, level in [
            ('D0_1', self.D0_1, self.I, self.L[1], 1),
            ('D0_2', self.D0_2, self.I, self.L[2], 2),
            ('D0_3', self.D0_3, self.I, self.L[3], 3),
        ]:
            if not src_set or not dst_set:
                continue
            if not d_dict:
                self.warnings.append(f"{dist_attr} not parsed - model will abort if required")
                continue
            expected  = len(src_set) * len(dst_set)
            defined   = len(d_dict)
            missing   = [(i, j) for i in sorted(src_set)
                         for j in sorted(dst_set) if (i, j) not in d_dict]
            n_missing = len(missing)
            if n_missing == 0:
                self.info.append(f"{dist_attr}: complete ({defined}/{expected} pairs)")
            else:
                by_origin = defaultdict(list)
                for i, j in missing:
                    by_origin[i].append(j)
                tbl_rows = []
                for origin in sorted(by_origin)[:MAX_LISTED]:
                    miss = by_origin[origin]
                    samp = ', '.join(miss[:5])
                    if len(miss) > 5:
                        samp += f" {_ellipsis()} (+{len(miss) - 5} more)"
                    tbl_rows.append([origin, str(len(miss)), samp])
                self.diagnostics.append(Diagnostic(
                    'ERROR',
                    f"{dist_attr} missing {n_missing} of {expected} O-D pairs",
                    what=f"{dist_attr} requires all {expected} pairs. {n_missing} are missing.",
                    why="AMPL aborts on missing parameter values without a default.",
                    fix=f"Add the missing entries to the {dist_attr} block in the data file.",
                    table_headers=["Origin", "# missing", "Missing destinations (first 5)"],
                    table_rows=tbl_rows,
                ))
                self.errors.append(
                    f"{dist_attr}: {n_missing}/{expected} pairs missing - model will abort"
                )

        # D1_2, D1_3, D2_3
        for dist_attr, d_dict, src_set, dst_set in [
            ('D1_2', self.D1_2, self.L[1], self.L[2]),
            ('D1_3', self.D1_3, self.L[1], self.L[3]),
            ('D2_3', self.D2_3, self.L[2], self.L[3]),
        ]:
            if not src_set or not dst_set:
                continue
            if d_dict:
                self.info.append(
                    f"{dist_attr}: {len(d_dict)} entries "
                    f"(expected <= {len(src_set) * len(dst_set)})"
                )
            else:
                self.warnings.append(
                    f"{dist_attr} not found - inter-level flows will use Dmax filter "
                    f"but travel costs cannot be computed"
                )

        # DL1 coverage: EL[1] × L[1]  (required for team transfer penalties)
        if self.EL[1] and self.L[1]:
            if not self.DL1:
                self.warnings.append(
                    "DL1 not parsed - team transfer relocation costs cannot be computed"
                )
            else:
                expected  = len(self.EL[1]) * len(self.L[1])
                missing_dl = [
                    (fr, to) for fr in sorted(self.EL[1])
                    for to in sorted(self.L[1]) if (fr, to) not in self.DL1
                ]
                if not missing_dl:
                    self.info.append(
                        f"DL1: complete ({len(self.DL1)}/{expected} EL[1]xL[1] pairs)"
                    )
                else:
                    self.warnings.append(
                        f"DL1 missing {len(missing_dl)}/{expected} EL[1]xL[1] pairs - "
                        f"AMPL will use the computed default (average of DL1)"
                    )

    # ──────────────────────────────────────────────────────────────────────────
    # Results summary
    # ──────────────────────────────────────────────────────────────────────────

    def _print_results(self):
        W = 80
        _rprint("\n" + "=" * W)
        _rprint("VALIDATION RESULTS")
        _rprint("=" * W)

        if self.errors:
            _rprint(f"\nERRORS ({len(self.errors)}):")
            _rprint("-" * W)
            for i, err in enumerate(self.errors, 1):
                _rprint(f"{i}. {err}")

        if self.warnings:
            _rprint(f"\nWARNINGS ({len(self.warnings)}):")
            _rprint("-" * W)
            for i, warn in enumerate(self.warnings, 1):
                _rprint(f"{i}. {warn}")

        if self.info:
            _rprint(f"\nINFO ({len(self.info)}):")
            _rprint("-" * W)
            for i, inf in enumerate(self.info, 1):
                _rprint(f"{i}. {inf}")

        if self.diagnostics:
            _rprint("\n" + "=" * W)
            _rprint("DETAILED DIAGNOSTICS")
            _rprint("=" * W)
            for diag in self.diagnostics:
                _rprint()
                _rprint(diag.render())

        _rprint("\n" + "=" * W)
        if self.errors:
            _rprint("RESULT: FAILED - fix errors before running model")
            ret = 1
        elif self.warnings:
            _rprint("RESULT: PASSED WITH WARNINGS")
            ret = 0
        else:
            _rprint("RESULT: PASSED - data is consistent")
            ret = 0
        _rprint("=" * W)
        return ret


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    global USE_UNICODE, _report_file

    parser = argparse.ArgumentParser(
        prog='check_data_consistency.py',
        description='Validate AMPL healthcare facility location data files (aps.mod).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('files', nargs='+', metavar='FILE.dat',
                        help='One or more .dat files (e.g. LS.dat LS_distdur.dat)')
    parser.add_argument('--output', '-o', metavar='REPORT', default=None,
                        help='Write report to this file (UTF-8)')
    parser.add_argument('--ascii', action='store_true', default=False,
                        help='Force plain ASCII output (no Unicode symbols)')
    args = parser.parse_args()

    # Unicode decision
    if args.ascii or (args.output is None and not sys.stdout.isatty()):
        USE_UNICODE = False

    # Output file setup
    if args.output:
        try:
            _report_file = open(args.output, 'w', encoding='utf-8')
            _progress(f"Writing report to: {args.output}")
        except OSError as e:
            print(f"Cannot open output file: {e}", file=sys.stderr)
            return 1
    else:
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

    try:
        validator = DataValidator()
        ok = validator.validate_files(args.files)
        if not ok:
            return 2
        return 0
    finally:
        if _report_file is not None:
            _report_file.close()
            _progress(f"Report saved: {args.output}")


if __name__ == "__main__":
    sys.exit(main())
