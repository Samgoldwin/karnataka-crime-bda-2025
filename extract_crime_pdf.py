"""Extract Crime in Karnataka 2025 (520pp PDF) into analytics-ready CSVs.

Outputs land in ./crime_karnataka_2025_csv/ :
  - 13 district x year trend tables (2023-2025) per crime domain
  - district_master_2025.csv  (merged overview KPIs per district)
  - state_trend_2011_2025.csv (15-year state time series)
  - ipc_crime_heads_trend.csv / sll_crime_heads_trend.csv (2023-2025)
  - violent_crime_heads_by_district_2025.csv
  - missing_children_district_2025.csv / missing_persons_district_2025.csv
  - property_stolen_recovered_district_2023_2025.csv
  - property_by_nature_2025.csv
  - recidivism_ipc_district_2025.csv / recidivism_sll_district_2025.csv
  - master_district_trends_long.csv (tidy long format across all domains)
  - data_dictionary.csv
"""
import csv
import re
from pathlib import Path

import pdfplumber

PDF = r"C:\Users\David\Downloads\Crime_In_Karnataka_2025.pdf"
OUT = Path(__file__).parent / "crime_karnataka_2025_csv"
OUT.mkdir(exist_ok=True)

NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
BRACKET_RE = re.compile(r"^\[(\d+)\]$")
SL_TOKEN_RE = re.compile(r"^\d+(?:\.\d+)*[A-Z]?$")

DISTRICTS = [
    "Bagalkot", "Bengaluru City", "Bengaluru District", "Belagavi District",
    "Ballari", "Bidar", "Vijayapura", "Chikkaballapura", "Chamarajnagar",
    "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere",
    "Dharwad", "Gadag", "Kalaburgi", "Hassan", "Haveri",
    "Hubballi Dharwad City", "KGF", "Kodagu", "Kolar", "Koppal", "Mandya",
    "Mangaluru City", "Mysuru City", "Mysuru District", "Raichur",
    "KRailways", "Bengaluru South", "Shimoga", "Tumakuru", "Udupi",
    "Uttara Kannada", "Yadgiri", "Belagavi City", "Kalaburgi City",
    "Vijayanagara",
]
_CANON_NORM = {re.sub(r"[^a-z0-9]", "", d.lower()): d for d in DISTRICTS}
_CANON_CHARS = {"".join(sorted(re.sub(r"[^a-z0-9]", "", d.lower()))): d for d in DISTRICTS}


def canon_name(name):
    n = re.sub(r"\s+", " ", name).strip()
    key = re.sub(r"[^a-z0-9]", "", n.lower())
    if not key:
        return n
    if key in _CANON_NORM:
        return _CANON_NORM[key]
    ckey = "".join(sorted(key))
    if ckey in _CANON_CHARS:
        return _CANON_CHARS[ckey]
    return n


def is_total_row(name):
    n = name.lower()
    return "total" in n and ("district" in n or n.strip() == "total" or n.endswith("total"))


def cluster_bands(words, gap=10.0):
    if not words:
        return []
    ws = sorted(words, key=lambda w: w["top"])
    bands = [[ws[0]]]
    for w in ws[1:]:
        if w["top"] - bands[-1][-1]["top"] > gap:
            bands.append([w])
        else:
            bands[-1].append(w)
    return bands


def bracket_anchors(words, n_num):
    """Return (sl_anchor, name_right, num_anchors[ n_num ])."""
    brackets = sorted(
        (w for w in words if BRACKET_RE.match(w["text"])),
        key=lambda w: w["x0"],
    )
    if len(brackets) < 2:
        raise ValueError("no bracket row found")
    xs = [(w["x0"] + w["x1"]) / 2 for w in brackets]
    # de-duplicate near-identical x (within 3pt)
    uniq = [xs[0]]
    for x in xs[1:]:
        if x - uniq[-1] > 3:
            uniq.append(x)
    if len(uniq) < 2 + n_num:
        # interpolate missing interior anchors to reach required count
        while len(uniq) < 2 + n_num:
            # find widest gap and insert midpoint
            gaps = [(uniq[i + 1] - uniq[i], i) for i in range(len(uniq) - 1)]
            _, i = max(gaps)
            uniq.insert(i + 1, (uniq[i] + uniq[i + 1]) / 2)
    sl_anchor = uniq[0]
    name_right = uniq[1] + 30
    num_anchors = uniq[2 : 2 + n_num]
    bracket_top = max(w["top"] for w in brackets)
    return sl_anchor, name_right, num_anchors, bracket_top


def parse_row_words(band, sl_anchor, name_right, num_anchors, sl_tol=18.0):
    """Assemble one logical row from a word band."""
    nums, names, sl_seen = {}, [], False
    for w in sorted(band, key=lambda w: w["x0"]):
        t = w["text"]
        cx = (w["x0"] + w["x1"]) / 2
        if BRACKET_RE.match(t):
            continue
        near_sl = abs(cx - sl_anchor) < sl_tol
        if NUM_RE.match(t):
            dists = [abs(cx - a) for a in num_anchors]
            idx = dists.index(min(dists))
            if min(dists) < 45:
                nums[idx] = t
                continue
            if near_sl and SL_TOKEN_RE.match(t):
                sl_seen = True
                continue
            continue
        if near_sl and SL_TOKEN_RE.match(t):
            sl_seen = True
            continue
        if cx <= name_right:
            names.append((w["top"], t))
    name = " ".join(t for _, t in sorted(names)).strip()
    return sl_seen, name, [nums.get(i, "") for i in range(len(num_anchors))]


def split_band_by_sl(band, sl_anchor, sl_tol=18.0):
    """Split a band containing multiple SL numbers into sub-bands.

    Non-SL words are assigned to the nearest SL token vertically.
    """
    sls = sorted(
        (w for w in band
         if SL_TOKEN_RE.match(w["text"])
         and abs((w["x0"] + w["x1"]) / 2 - sl_anchor) < sl_tol),
        key=lambda w: w["top"],
    )
    if len(sls) <= 1:
        return [band]
    subs = [[] for _ in sls]
    for w in band:
        if any(w is s for s in sls):
            idx = sls.index(next(s for s in sls if s is w))
            subs[idx].append(w)
            continue
        best = min(range(len(sls)), key=lambda i: abs(w["top"] - sls[i]["top"]))
        subs[best].append(w)
    return [s for s in subs if s]


def parse_grid_table(page, n_num, gap=10.0):
    """Parse bracket-anchored table -> rows [name, v1..vn] (+TOTAL row)."""
    words = page.extract_words()
    sl_anchor, name_right, num_anchors, btop = bracket_anchors(words, n_num)
    data_words = [w for w in words if w["top"] > btop + 4]
    rows = []
    for band in cluster_bands(data_words, gap=gap):
        for sub in split_band_by_sl(band, sl_anchor):
            sl_seen, name, vals = parse_row_words(
                sub, sl_anchor, name_right, num_anchors
            )
            if not any(vals):
                continue
            if not sl_seen and not name:
                continue
            rows.append([canon_name(name)] + vals)
    return rows


def write_csv(name, header, rows):
    path = OUT / name
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {name}: {len(rows)} data rows")


def as_int(v):
    v = v.replace(",", "")
    try:
        return int(float(v))
    except (ValueError, AttributeError):
        return v


def as_float(v):
    v = v.replace(",", "")
    try:
        return float(v)
    except (ValueError, AttributeError):
        return v


# ---------------------------------------------------------------- district
# trend tables -------------------------------------------------------------
def extract_district_trend(pdf, page_idx, tid, label, rate_col, n_num=6):
    page = pdf.pages[page_idx]
    rows = parse_grid_table(page, n_num)
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if not name:
            continue
        out.append([tid, name] + vals)
    header = ["table_id", "district"]
    if n_num == 6:
        header += [
            "cases_2023", "cases_2024", "cases_2025",
            "population_lakhs_2025", f"rate_2025_{rate_col}",
            "chargesheeting_rate_2025",
        ]
    else:  # 4 cols: 2023 2024 2025 cs-rate
        header += ["cases_2023", "cases_2024", "cases_2025",
                   "chargesheeting_rate_2025"]
    if total:
        out.append([tid, "TOTAL_DISTRICTS"] + total)
    write_csv(f"{label}.csv", header, out)
    n_dist = sum(1 for r in out if r[1] != "TOTAL_DISTRICTS")
    if n_dist != 38:
        print(f"    WARNING {label}: {n_dist} districts (expected 38)")
    return out


# ------------------------------------------------------------ text-line
# helpers (overview pages) -------------------------------------------------
def parse_simple_rows(page, n_num, name_first=True):
    """Fallback: parse 'SL NAME n n ... n' text lines with Hubballi wrap fix."""
    text = page.extract_text() or ""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    num_tok = r"-?[\d,]+(?:\.\d+)?"
    row_re = re.compile(
        rf"^(\d+(?:\.\d+)*[A-Z]?)\s+(.+?)\s+((?:{num_tok}\s+){{{n_num - 1}}}{num_tok})\s*$"
    )
    sl_only = re.compile(r"^(\d+(?:\.\d+)*[A-Z]?)$")
    city_re = re.compile(rf"^City\s+((?:{num_tok}\s+){{{n_num - 1}}}{num_tok})\s*$")
    name_only = re.compile(r"^[A-Za-z][A-Za-z\s/()\-\.]*$")

    rows, pending_name, pending_sl = [], None, None
    for ln in lines:
        if ln.startswith(("TABLE", "[1]", "(Continued)", "(Concluded)")):
            continue
        if re.fullmatch(r"\[\d+\](\s+\[\d+\])+", ln):
            continue
        m = row_re.match(ln)
        if m:
            rows.append([canon_name(m.group(2))] + m.group(3).split())
            pending_name, pending_sl = None, None
            continue
        m = city_re.match(ln)
        if m and pending_sl is not None:
            rows.append(["Hubballi Dharwad City"] + m.group(1).split())
            pending_sl, pending_name = None, None
            continue
        m = sl_only.match(ln)
        if m:
            pending_sl = m.group(1)
            continue
        if name_only.match(ln) and len(ln) < 45:
            if pending_sl is not None and ln == "City":
                continue  # wait for city_re with numbers
            pending_name = ln
            continue
    return rows


LEGEND_PREFIX_RE = re.compile(r"^(?:ABOVE\s*-\s*\d+|\d+\s*-\s*\d+)\s+")


def extract_overview_page(pdf, page_idx, skip_total=False):
    """Single-metric district pages p16-22: returns dict district->value.

    Uses word-band extraction so values slightly offset vertically
    (e.g. 41.08 sitting 5pt above '5 Mysuru District') are still paired.
    """
    page = pdf.pages[page_idx]
    words = page.extract_words()
    result, total = {}, None
    pending_name = None

    def store(name, value):
        nonlocal total
        name = canon_name(name)
        if name in DISTRICTS:
            result[name] = as_float(value)
            return True
        if name in ("Hubballi Dharwad",):
            result["Hubballi Dharwad City"] = as_float(value)
            return True
        if re.fullmatch(r"total( districts)?", name.lower()):
            total = as_float(value)
            return True
        return False

    for band in cluster_bands(words, gap=7.0):
        band = sorted(band, key=lambda w: w["x0"])
        nums = [w for w in band if NUM_RE.match(w["text"])]
        alphas = [w for w in band if re.match(r"^[A-Za-z][A-Za-z\s\-]*$", w["text"])]
        if not nums:
            joined = " ".join(w["text"] for w in alphas).strip()
            if joined:
                pending_name = joined
            continue
        value_w = max(nums, key=lambda w: w["x0"])
        left_words = [w for w in band if w["x0"] < value_w["x0"] - 2]
        if not left_words:
            if pending_name:
                store(pending_name, value_w["text"])
                pending_name = None
            continue
        # first alpha token anchors the name block
        alpha_left = [w for w in left_words if re.match(r"^[A-Za-z]", w["text"])]
        digits_left = [w for w in left_words if w["text"].isdigit()]
        name_toks, sl_value = [], None
        if alpha_left:
            first_alpha_x = alpha_left[0]["x0"]
            sl_candidates = [w for w in digits_left if w["x0"] < first_alpha_x]
            if sl_candidates:
                sl_w = max(sl_candidates, key=lambda w: w["x0"])
                sl_value = sl_w["text"]
                name_toks = [
                    w["text"] for w in left_words
                    if w["x0"] >= first_alpha_x - 2 and not NUM_RE.match(w["text"])
                ]
            else:
                # roman-numeral range row, e.g. 'IX KRailways 663'
                name_toks = [
                    w["text"] for w in left_words
                    if not re.fullmatch(r"[IVX]+", w["text"])
                    and not NUM_RE.match(w["text"])
                ]
        joined = " ".join(name_toks).strip()
        joined = re.sub(r"\b(Range|Commissionerates)\b.*$", "", joined).strip()
        if joined:
            if store(joined, value_w["text"]):
                pending_name = None
                continue
        if pending_name and store(pending_name, value_w["text"]):
            pending_name = None
            continue
        # bare SL + value: Hubballi wrapped (City follows on its own band)
        if sl_value and not joined:
            pending_name = "Hubballi Dharwad"

    # final normalisation: 'Hubballi Dharwad' -> 'Hubballi Dharwad City'
    if "Hubballi Dharwad City" not in result and "Hubballi Dharwad" in result:
        result["Hubballi Dharwad City"] = result.pop("Hubballi Dharwad")
    return result, total


def extract_state_trend(pdf):
    page = pdf.pages[23]
    text = page.extract_text() or ""
    rows = []
    num = r"-?[\d,]+(?:\.\d+)?"
    row_re = re.compile(
        rf"^(\d+)\s+(\d{{4}})\s+((?:{num}\s+){{7}}{num})\s*$"
    )
    for ln in (x.strip() for x in text.split("\n")):
        m = row_re.match(ln)
        if m:
            sl, year = int(m.group(1)), int(m.group(2))
            if sl != year - 2010:
                continue  # footer year-label rows
            rows.append([m.group(2)] + m.group(3).split())
    return rows


def extract_heads_trend(pdf, page_indices):
    """Crime-head wise 2023-2025 (7 numeric cols)."""
    all_rows = []
    for pi in page_indices:
        page = pdf.pages[pi]
        rows = parse_grid_table(page, 7, gap=12.0)
        for r in rows:
            name = re.sub(r"\s+", " ", r[0]).strip()
            vals = r[1:]
            if not name or not any(vals):
                continue
            if is_total_row(name):
                all_rows.append(["TOTAL"] + vals)
                continue
            all_rows.append([name] + vals)
    return all_rows


def extract_violent_heads(pdf):
    p44 = parse_grid_table(pdf.pages[43], 8, gap=12.0)
    p45 = parse_grid_table(pdf.pages[44], 8, gap=12.0)
    left = {r[0]: r[1:] for r in p44 if r[0] and not is_total_row(r[0])}
    right = {r[0]: r[1:] for r in p45 if r[0] and not is_total_row(r[0])}
    cols_l = [
        "murder_bns302", "culpable_homicide_bns304", "infanticide_bns315",
        "foeticide_bns316", "dowry_deaths_bns304b", "attempt_murder_bns307",
        "attempt_culpable_homicide_bns308", "grievous_hurt_bns325_326",
    ]
    cols_r = [
        "attempt_rape", "rape", "kidnapping_abduction", "rioting",
        "robbery", "dacoity", "arson", "total_violent_crimes",
    ]
    names = list(dict.fromkeys(list(left) + list(right)))
    rows = []
    for d in names:
        vals = left.get(d, [""] * 8) + right.get(d, [""] * 8)
        rows.append([d] + vals)
    write_csv(
        "violent_crime_heads_by_district_2025.csv",
        ["district"] + cols_l + cols_r,
        rows,
    )
    return rows


def extract_property_district(pdf):
    rows = parse_grid_table(pdf.pages[508], 9, gap=12.0)
    cols = [
        "stolen_2023_cr", "recovered_2023_cr", "recovery_pct_2023",
        "stolen_2024_cr", "recovered_2024_cr", "recovery_pct_2024",
        "stolen_2025_cr", "recovered_2025_cr", "recovery_pct_2025",
    ]
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if name:
            out.append([name] + vals)
    if total:
        out.append(["TOTAL_DISTRICTS"] + total)
    write_csv("property_stolen_recovered_district_2023_2025.csv",
              ["district"] + cols, out)
    return out


def extract_property_nature(pdf):
    rows = parse_grid_table(pdf.pages[509], 8, gap=12.0)
    cols = [
        "cases_stolen_2025", "pct_share_of_total_cases_stolen",
        "cases_recovered_2025", "detection_pct",
        "value_stolen_cr_2025", "pct_share_of_total_value_stolen",
        "value_recovered_cr_2025", "recovery_pct",
    ]
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if name:
            out.append([name] + vals)
    if total:
        out.append(["TOTAL"] + total)
    write_csv("property_by_nature_2025.csv", ["nature_of_property"] + cols, out)
    return out


def extract_recidivism(pdf, page_idx, label):
    rows = parse_grid_table(pdf.pages[page_idx], 8, gap=12.0)
    cols = [
        "persons_arrested", "juveniles_apprehended_convicted_past",
        "juveniles_apprehended_not_convicted_past",
        "juveniles_arrested_first_time_not_convicted",
        "adults_arrested_not_convicted_past",
        "adults_arrested_convicted_past", "adults_arrested_first_time_not_convicted",
        "recidivism_pct",
    ]
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if name:
            out.append([name] + vals)
    if total:
        out.append(["TOTAL_DISTRICTS"] + total)
    write_csv(f"{label}.csv", ["district"] + cols, out)
    return out


def extract_missing_children(pdf):
    rows = parse_grid_table(pdf.pages[371], 12, gap=12.0)
    cols = [
        "prev_years_unrecovered_boys", "prev_years_unrecovered_girls",
        "prev_years_unrecovered_trans", "prev_years_unrecovered_total",
        "missing_2025_boys", "missing_2025_girls",
        "missing_2025_trans", "missing_2025_total",
        "total_boys", "total_girls", "total_trans", "grand_total",
    ]
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if name:
            out.append([name] + vals)
    if total:
        out.append(["TOTAL_DISTRICTS"] + total)
    write_csv("missing_children_district_2025.csv", ["district"] + cols, out)
    return out


def extract_missing_persons(pdf):
    rows = parse_grid_table(pdf.pages[373], 9, gap=12.0)
    cols = [
        "prev_years_unrecovered_males", "prev_years_unrecovered_females",
        "prev_years_unrecovered_total",
        "missing_2025_males", "missing_2025_females", "missing_2025_total",
        "total_persons_males", "total_persons_females", "grand_total",
    ]
    out, total = [], None
    for r in rows:
        name, vals = r[0], r[1:]
        if is_total_row(name):
            total = vals
            continue
        if name:
            out.append([name] + vals)
    if total:
        out.append(["TOTAL_DISTRICTS"] + total)
    write_csv("missing_persons_district_2025.csv", ["district"] + cols, out)
    return out


# --------------------------------------------------------------------- main
def main():
    pdf = pdfplumber.open(PDF)
    print(f"Opened PDF: {len(pdf.pages)} pages")

    # 1. district trend tables ------------------------------------------------
    trend_specs = [
        (38, "1.3", "district_trend_total_crime", "total"),
        (39, "1.4", "district_trend_sll", "sll"),
        (42, "2.1", "district_trend_violent_crime", "violent"),
        (46, "2A.1", "district_trend_murder", "murder"),
        (57, "3.1", "district_trend_crime_against_women", "women"),
        (157, "6.1", "district_trend_crime_senior_citizens", "senior_citizens"),
        (181, "7.1", "district_trend_crime_sc_atrocities", "sc_atrocities"),
        (216, "8.1", "district_trend_crime_st_atrocities", "st_atrocities"),
        (251, "9.1", "district_trend_economic_offences", "economic_offences"),
        (272, "10.1", "district_trend_cyber_crime", "cyber_crime"),
        (314, "11.1", "district_trend_environment_offences", "environment_offences"),
    ]
    trend_store = {}
    for page_idx, tid, label, rate in trend_specs:
        trend_store[label] = extract_district_trend(
            pdf, page_idx, tid, label, rate
        )

    # 12.1 / 13.1: 4 numeric cols
    for page_idx, tid, label in [
        (331, "12.1", "district_trend_crime_vs_foreigners"),
        (353, "13.1", "district_trend_crime_by_foreigners"),
    ]:
        trend_store[label] = extract_district_trend(
            pdf, page_idx, tid, label, "n/a", n_num=4
        )

    # 2. overview KPI pages p16-22 + p23 -> district_master_2025 -----------
    print("overview pages...")
    kpi_fields = [
        (15, "ipc_bns_cases_2025"),
        (16, "ipc_bns_occurrence_rate_2025"),
        (17, "sll_cases_2025"),
        (18, "sll_occurrence_rate_2025"),
        (19, "conviction_rate_ipc_bns_pct_2025"),
        (20, "chargesheet_submission_pct_ipc_bns_2025"),
        (21, "court_pendency_pct_ipc_bns_2025"),
    ]
    master = {d: {"district": d} for d in DISTRICTS}
    totals = {}
    for pi, col in kpi_fields:
        res, tot = extract_overview_page(pdf, pi)
        totals[col] = tot
        missing = [d for d in DISTRICTS if d not in res]
        if missing:
            print(f"    {col}: missing {missing}")
        for d, v in res.items():
            if d in master:
                master[d][col] = v

    # p23: IPC/SLL/total summary
    page23 = pdf.pages[22]
    for r in parse_simple_rows(page23, 3):
        d = r[0]
        if d in master:
            master[d]["ipc_bns_cases_p23"] = as_int(r[1])
            master[d]["sll_cases_p23"] = as_int(r[2])
            master[d]["total_cognizable_cases_2025"] = as_int(r[3])

    # join pop/rate/cs from 1.3
    for r in trend_store.get("district_trend_total_crime", []):
        if r[0] == "1.3" and r[1] in master:
            master[r[1]]["population_lakhs_2025"] = as_float(r[5])
            master[r[1]]["total_crime_rate_2025"] = as_float(r[6])
            master[r[1]]["total_chargesheeting_rate_2025"] = as_float(r[7])

    mcols = [
        "district", "ipc_bns_cases_2025", "ipc_bns_occurrence_rate_2025",
        "sll_cases_2025", "sll_occurrence_rate_2025",
        "total_cognizable_cases_2025", "population_lakhs_2025",
        "total_crime_rate_2025", "total_chargesheeting_rate_2025",
        "conviction_rate_ipc_bns_pct_2025",
        "chargesheet_submission_pct_ipc_bns_2025",
        "court_pendency_pct_ipc_bns_2025",
    ]
    mrows = [[master[d].get(c, "") for c in mcols] for d in DISTRICTS]
    write_csv("district_master_2025.csv", mcols, mrows)

    # 3. state trend 2011-2025 -----------------------------------------------
    st = extract_state_trend(pdf)
    write_csv(
        "state_trend_2011_2025.csv",
        ["year", "population_lakhs", "ipc_bns_cases", "sll_cases",
         "total_cases", "ipc_bns_rate", "sll_rate", "total_rate",
         "ipc_share_of_total_pct"],
        st,
    )

    # 4. crime heads trends ---------------------------------------------------
    ipc_heads = extract_heads_trend(pdf, [32, 33, 34])
    write_csv(
        "ipc_crime_heads_trend.csv",
        ["crime_head", "cases_2023", "rate_2023", "cases_2024", "rate_2024",
         "cases_2025", "rate_2025", "pct_share_of_ipc_2025"],
        ipc_heads,
    )
    sll_heads = extract_heads_trend(pdf, [35, 36, 37])
    write_csv(
        "sll_crime_heads_trend.csv",
        ["crime_head", "cases_2023", "rate_2023", "cases_2024", "rate_2024",
         "cases_2025", "rate_2025", "pct_share_of_sll_2025"],
        sll_heads,
    )

    # 5. violent heads x district --------------------------------------------
    extract_violent_heads(pdf)

    # 6. missing persons ------------------------------------------------------
    extract_missing_children(pdf)
    extract_missing_persons(pdf)

    # 7. property ------------------------------------------------------------
    extract_property_district(pdf)
    extract_property_nature(pdf)

    # 8. recidivism ----------------------------------------------------------
    extract_recidivism(pdf, 505, "recidivism_ipc_district_2025")
    extract_recidivism(pdf, 506, "recidivism_sll_district_2025")

    # 9. master long format ---------------------------------------------------
    long_rows = []
    domain_map = {
        "district_trend_total_crime": "total_cognizable",
        "district_trend_sll": "sll",
        "district_trend_violent_crime": "violent",
        "district_trend_murder": "murder",
        "district_trend_crime_against_women": "crime_against_women",
        "district_trend_crime_senior_citizens": "crime_senior_citizens",
        "district_trend_crime_sc_atrocities": "sc_atrocities",
        "district_trend_crime_st_atrocities": "st_atrocities",
        "district_trend_economic_offences": "economic_offences",
        "district_trend_cyber_crime": "cyber_crime",
        "district_trend_environment_offences": "environment_offences",
        "district_trend_crime_vs_foreigners": "crime_vs_foreigners",
        "district_trend_crime_by_foreigners": "crime_by_foreigners",
    }
    for label, domain in domain_map.items():
        for r in trend_store.get(label, []):
            tid, dist = r[0], r[1]
            vals = r[2:]
            if vals[0] == "" or vals[1] == "" or vals[2] == "":
                continue
            for year, col in zip((2023, 2024, 2025), vals[:3]):
                long_rows.append([
                    domain, tid, dist, year, as_int(col),
                    as_float(vals[3]) if len(vals) > 3 else "",
                    as_float(vals[4]) if len(vals) > 4 else "",
                    as_float(vals[5]) if len(vals) > 5 else "",
                ])
    write_csv(
        "master_district_trends_long.csv",
        ["domain", "table_id", "district", "year", "cases",
         "population_lakhs_2025", "rate_2025", "chargesheeting_rate_2025"],
        long_rows,
    )

    # 10. data dictionary ----------------------------------------------------
    dd = [
        ["file", "description"],
        ["district_master_2025.csv",
         "One row per district: IPC/SLL cases & rates, total crime rate, "
         "population, conviction/chargesheet/pendency KPIs (2025)"],
        ["master_district_trends_long.csv",
         "Tidy long format: cases per district x year (2023-2025) across all "
         "13 crime domains; 2025 rate/pop/cs-rate attached"],
        ["state_trend_2011_2025.csv",
         "Karnataka state-level IPC/SLL incidence & rates, 2011-2025"],
        ["ipc_crime_heads_trend.csv",
         "IPC/BNS crime heads: cases & rates 2023-2025 + share"],
        ["sll_crime_heads_trend.csv",
         "SLL crime heads/acts: cases & rates 2023-2025 + share"],
        ["district_trend_*.csv",
         "Per-domain district tables (cases 2023-2025, population, rate, "
         "chargesheeting rate). Table ids match the publication."],
        ["violent_crime_heads_by_district_2025.csv",
         "Violent crime heads (murder..arson, total) x district, 2025"],
        ["missing_children_district_2025.csv",
         "Missing children <18: prior-year unrecovered + 2025 by gender, 2025"],
        ["missing_persons_district_2025.csv",
         "Missing persons all ages: prior-year unrecovered + 2025 by gender"],
        ["property_stolen_recovered_district_2023_2025.csv",
         "Property value stolen/recovered (Rs crore) & recovery %, 2023-2025"],
        ["property_by_nature_2025.csv",
         "Property stolen/recovered by nature (vehicles, gold, etc.), 2025"],
        ["recidivism_ipc_district_2025.csv",
         "Repeat-offender share among persons arrested under IPC/BNS, 2025"],
        ["recidivism_sll_district_2025.csv",
         "Repeat-offender share among persons arrested under SLL, 2025"],
    ]
    write_csv("data_dictionary.csv", dd[0], dd[1:])

    pdf.close()
    print("Done.")


if __name__ == "__main__":
    main()
