"""
=============================================================
Mawārith Analytics — Project 1 (v2)
Fiqh al-Mawārith Engine: Automated Islamic Inheritance Calculator
=============================================================
FIXES in v2:
  1. Full estate valuation — cash + Nigerian market-valued assets
  2. Son's son Asaba logic corrected (residue with daughters)
  3. Dhul Arham Tanzeel distribution implemented (Hanafi method)
  4. "0 naira" heirs now show correct status (Excluded/No Residue)
=============================================================
"""

from fractions import Fraction
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from math import gcd


# ─────────────────────────────────────────────
# NIGERIAN ASSET VALUATION TABLE (₦)
# ─────────────────────────────────────────────

ASSET_VALUES = {
    # Vehicles
    "2019 Toyota Camry":                     12_000_000,
    "2018 Toyota Camry (fairly used)":        9_000_000,
    "2015 Sienna car":                        8_500_000,
    "3 Toyota Hilux (2019)":                 36_000_000,
    "Hyundai Accent 2020":                    6_500_000,
    "4 Bajaj motorcycles (new)":              2_800_000,
    "Jincheng motorcycle":                      650_000,
    "Bajaj tricycle":                           800_000,
    "Dell Vostro laptop":                       450_000,
    "3 HP Laptops":                             750_000,

    # Residential Property
    "4-bedroom flat in Lekki":               80_000_000,
    "2 four-bedroom flats in Abuja":        120_000_000,
    "4-room apartment in Ilorin":            12_000_000,
    "10 uncompleted rooms in Malete":        25_000_000,
    "8 rooms on the Island, Lagos":          64_000_000,
    "6 self-contained units in Ondo":        18_000_000,
    "3-bedroom flats in Kano":               15_000_000,
    "2-bedroom flat in Maryland, Lagos":     28_000_000,
    "10-bedroom flat in Maitama, Abuja":    150_000_000,
    "2-bedroom flat in Iyana Ipaja":         18_000_000,
    "25 self-contained rooms in Ile-Ife":    50_000_000,
    "3-bedroom apartment in USA":           180_000_000,
    "Secondary school in Garki, Abuja":     200_000_000,
    "4 three-bedroom flats":                 80_000_000,
    "Self-contained room in Ikotun, Lagos":   5_000_000,
    "Estate with 30 houses (3-bedroom each) in Isolo": 600_000_000,
    "8 uncompleted rooms in Abuja (upstairs)": 40_000_000,
    "12 completed rooms (downstairs)":       60_000_000,

    # Land
    "Farm 3 plots in Ewekoro":               3_000_000,
    "2 plots of land in Lagos":              20_000_000,
    "3 plots of land in Ibadan":             12_000_000,
    "12 plots of land in Magodo, Lagos":    120_000_000,
    "5 plots of land in GRA Ilorin":         75_000_000,
    "2 plots of land in Saare, Kwara":        3_000_000,
    "2 hectares in Victoria Island":        500_000_000,
    "3 plots of land":                        6_000_000,
    "Cassava farm 5 plots in Mowe":           5_000_000,
    "Plot of land with 5-bedroom foundation in Taiwo": 35_000_000,

    # Commercial / Business
    "Pharmaceutical company in Ikeja":      150_000_000,
    "Petrol station in Iwo Road, Ibadan":   120_000_000,
    "Petrol station in Onitsha":            130_000_000,
    "Textile industry at Oshodi":            80_000_000,
    "30-shop complex in Idumota":           200_000_000,
    "10 shops in Ikare":                     30_000_000,

    # Investments / Shares
    "Jaiz Bank shares ₦5M":                  5_000_000,
    "Lotus Capital investment ₦3M":           3_000_000,
    "Lotus Capital shares ₦5M":              5_000_000,
    "Taj Bank shares ₦7M":                   7_000_000,

    # Other
    "10 uncompleted rooms in Abule Egba":   20_000_000,
}

def value_assets(assets: List[str]) -> int:
    total = 0
    for a in assets:
        total += ASSET_VALUES.get(a, 0)
    return total


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class Estate:
    deceased_name: str
    gender: str
    location: str
    cash: int = 0
    assets: List[str] = field(default_factory=list)
    heirs_input: Dict[str, int] = field(default_factory=dict)

    @property
    def total_value(self):
        return self.cash + value_assets(self.assets)

    @property
    def asset_value(self):
        return value_assets(self.assets)


@dataclass
class Result:
    estate: Estate
    total_estate_value: int
    base: int
    awl_applied: bool
    radd_applied: bool
    tanzeel_applied: bool
    shares_table: List[dict]
    notes: List[str]


# ─────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────

def lcm(a, b): return a * b // gcd(a, b)

def compute_base(shares: Dict[str, Fraction]) -> int:
    denoms = [s.denominator for s in shares.values() if s > 0]
    base = 1
    for d in denoms:
        base = lcm(base, d)
    return base


# ─────────────────────────────────────────────
# THE ENGINE (v2)
# ─────────────────────────────────────────────

class MawaarithEngine:

    def compute(self, estate: Estate) -> Result:
        heirs_input = estate.heirs_input
        notes = []
        tanzeel_applied = False

        present = {role: count for role, count in heirs_input.items() if count > 0}

        # ── BLOCKING RULES ────────────────────────────────────────────────
        blocked = {}

        if "father" in present:
            for r in ["grandfather", "paternal_uncle", "full_uncle"]:
                if r in present: blocked[r] = "father"

        has_son_asaba = "son" in present
        has_sons_son  = "sons_son" in present and "sons_son" not in blocked

        if has_son_asaba:
            for r in ["full_brother","full_sister","paternal_brother","paternal_sister",
                      "maternal_brother","maternal_sister","full_uncle","paternal_uncle"]:
                if r in present: blocked[r] = "son"

        if has_sons_son and not has_son_asaba:
            for r in ["full_brother","full_sister","paternal_brother","paternal_sister",
                      "full_uncle","paternal_uncle"]:
                if r in present: blocked[r] = "sons_son"

        if "full_brother" in present and "full_brother" not in blocked:
            for r in ["paternal_brother","paternal_sister"]:
                if r in present: blocked[r] = "full_brother"

        if "mother" in present:
            for r in ["grandmother","maternal_grandfather"]:
                if r in present: blocked[r] = "mother"

        dhul_arham_roles = {
            "daughters_son","daughters_daughter","full_sisters_daughter",
            "maternal_uncles_son","maternal_aunt","paternal_aunt",
            "maternal_brothers_son","maternal_grandfather",
        }

        # ── PRESENCE FLAGS ────────────────────────────────────────────────
        def P(role): return role in present and role not in blocked

        has_son        = P("son")
        has_sons_son   = P("sons_son")
        has_daughter   = P("daughter")
        has_sons_daughter = P("sons_daughter")
        has_father     = P("father")
        has_mother     = P("mother")
        has_grandfather= P("grandfather")
        has_grandmother= P("grandmother")
        has_husband    = P("husband")
        has_wife       = P("wife")
        has_full_brother   = P("full_brother")
        has_full_sister    = P("full_sister")
        has_pat_sister     = P("paternal_sister")
        has_mat_brother    = P("maternal_brother")
        has_mat_sister     = P("maternal_sister")

        n = lambda r: present.get(r, 0)

        # ── ASSIGN FURUD SHARES ───────────────────────────────────────────
        shares: Dict[str, Fraction] = {}

        # Husband
        if has_husband:
            if has_son or has_sons_son or has_daughter or has_sons_daughter:
                shares["husband"] = Fraction(1, 4)
            else:
                shares["husband"] = Fraction(1, 2)

        # Wife/Wives
        if has_wife:
            if has_son or has_sons_son or has_daughter or has_sons_daughter:
                shares["wife"] = Fraction(1, 8)
            else:
                shares["wife"] = Fraction(1, 4)

        # Mother
        if has_mother:
            has_children = has_son or has_sons_son or has_daughter or has_sons_daughter
            sibling_count = sum(n(r) for r in [
                "full_brother","full_sister","paternal_brother","paternal_sister",
                "maternal_brother","maternal_sister"
            ] if r not in blocked)
            if has_children or sibling_count >= 2:
                shares["mother"] = Fraction(1, 6)
            else:
                shares["mother"] = Fraction(1, 3)

        # Grandmother
        if has_grandmother and "grandmother" not in blocked:
            shares["grandmother"] = Fraction(1, 6)

        # Father
        if has_father:
            if has_son or has_sons_son:
                shares["father"] = Fraction(1, 6)
            elif has_daughter or has_sons_daughter:
                shares["father"] = Fraction(1, 6)
                # will get residue too (added in Asaba step)
                notes.append("Father receives 1/6 fixed share + residue as Asaba (daughters present, no sons).")
            # else pure Asaba — handled below

        # Grandfather (acts like father when no father)
        if has_grandfather and "grandfather" not in blocked and not has_father:
            if has_son or has_sons_son:
                shares["grandfather"] = Fraction(1, 6)
            elif has_daughter or has_sons_daughter:
                shares["grandfather"] = Fraction(1, 6)
            # else pure Asaba

        # Daughters
        if has_daughter and not has_son:
            if n("daughter") == 1:
                shares["daughter"] = Fraction(1, 2)
            else:
                shares["daughter"] = Fraction(2, 3)

        # Son's Daughter
        if has_sons_daughter and not has_son and not has_sons_son:
            nd = n("daughters_on") # wrong key
            nsd = n("sons_daughter")
            nda = n("daughter")
            if nsd >= 1:
                if nda == 0:
                    shares["sons_daughter"] = Fraction(1, 2) if nsd == 1 else Fraction(2, 3)
                elif nda == 1:
                    shares["sons_daughter"] = Fraction(1, 6)
                else:
                    blocked["sons_daughter"] = "2+ daughters (ceiling reached)"
                    notes.append("Son's daughter blocked — 2+ daughters already reach 2/3 ceiling.")

        # Full Sisters (when no son/sons_son/father/grandfather)
        if has_full_sister and not has_son and not has_sons_son and not has_father and not has_grandfather:
            if not has_full_brother:
                if n("full_sister") == 1:
                    shares["full_sister"] = Fraction(1, 2)
                else:
                    shares["full_sister"] = Fraction(2, 3)

        # Paternal Sisters
        if has_pat_sister and "paternal_sister" not in blocked:
            if not has_full_brother and not has_full_sister and not has_son and not has_father and not has_grandfather:
                nps = n("paternal_sister")
                shares["paternal_sister"] = Fraction(1, 2) if nps == 1 else Fraction(2, 3)

        # Maternal Siblings
        for mat_role in ["maternal_brother", "maternal_sister"]:
            if P(mat_role):
                total_mat = sum(n(r) for r in ["maternal_brother","maternal_sister"] if P(r))
                has_children = has_son or has_sons_son or has_daughter or has_sons_daughter
                if not has_children and not has_father and not has_grandfather:
                    shares[mat_role] = Fraction(1, 6) if total_mat == 1 else Fraction(1, 3)

        # ── ASABA (RESIDUARIES) ────────────────────────────────────────────
        furud_sum = sum(shares.values())
        residue   = Fraction(1) - furud_sum

        # Sons + Daughters → 2:1
        if has_son and has_daughter:
            ns = n("son"); nd2 = n("daughter")
            parts = ns * 2 + nd2
            child_base = Fraction(1) - sum(v for k, v in shares.items() if k not in ("son","daughter"))
            shares["son"]      = child_base * Fraction(ns * 2, parts)
            shares["daughter"] = child_base * Fraction(nd2,    parts)
            notes.append("Sons and daughters share residue 2:1 (male:female).")
            residue = Fraction(0)

        # Sons_son + daughters (no son) → sons_son is Asaba
        elif has_sons_son and has_daughter and not has_son:
            nss = n("sons_son"); nd2 = n("daughter")
            # daughters get 2/3 (fixed), sons_son gets residue
            if n("daughter") == 1:
                shares["daughter"] = Fraction(1, 2)
            else:
                shares["daughter"] = Fraction(2, 3)
            furud_without_ss = sum(v for k, v in shares.items() if k != "sons_son")
            sons_son_share = max(Fraction(1) - furud_without_ss, Fraction(0))
            shares["sons_son"] = sons_son_share
            if sons_son_share > 0:
                notes.append(f"Son's son inherits as Asaba (residue after daughters' fixed share): {sons_son_share}.")
            else:
                notes.append("Son's son present but residue is zero after daughters' fixed shares — excluded.")
            residue = Fraction(0)

        elif has_sons_son and not has_son and not has_daughter:
            # Pure Asaba
            furud_others = sum(v for k, v in shares.items() if k != "sons_son")
            shares["sons_son"] = max(Fraction(1) - furud_others, Fraction(0))
            residue = Fraction(0)

        elif has_father:
            # Father gets residue (already has 1/6 if daughters present)
            furud_without_f = sum(v for k, v in shares.items() if k != "father")
            shares["father"] = max(Fraction(1) - furud_without_f, Fraction(0))
            residue = Fraction(0)

        elif has_grandfather and not has_father:
            furud_without_gf = sum(v for k, v in shares.items() if k != "grandfather")
            shares["grandfather"] = max(Fraction(1) - furud_without_gf, Fraction(0))
            residue = Fraction(0)

        elif has_full_brother:
            if has_full_sister and "full_brother" not in blocked:
                nb = n("full_brother"); ns2 = n("full_sister")
                parts = nb * 2 + ns2
                furud_sibs = sum(v for k, v in shares.items() if k not in ("full_brother","full_sister"))
                sib_res = max(Fraction(1) - furud_sibs, Fraction(0))
                shares["full_brother"] = sib_res * Fraction(nb * 2, parts)
                shares["full_sister"]  = sib_res * Fraction(ns2,    parts)
            else:
                furud_others = sum(v for k, v in shares.items() if k != "full_brother")
                shares["full_brother"] = max(Fraction(1) - furud_others, Fraction(0))
            residue = Fraction(0)

        elif has_full_sister and (has_daughter or has_sons_daughter):
            # Asaba ma'al-Ghair
            furud_others = sum(v for k, v in shares.items() if k != "full_sister")
            shares["full_sister"] = max(Fraction(1) - furud_others, Fraction(0))
            notes.append("Full sister(s) inherit as Asaba ma'al-Ghair (alongside daughter).")
            residue = Fraction(0)

        elif P("paternal_brother") and "paternal_brother" not in blocked:
            furud_others = sum(v for k, v in shares.items() if k != "paternal_brother")
            shares["paternal_brother"] = max(Fraction(1) - furud_others, Fraction(0))
            residue = Fraction(0)

        elif P("full_uncle"):
            furud_others = sum(v for k, v in shares.items() if k != "full_uncle")
            shares["full_uncle"] = max(Fraction(1) - furud_others, Fraction(0))
            residue = Fraction(0)

        elif P("paternal_uncle"):
            furud_others = sum(v for k, v in shares.items() if k != "paternal_uncle")
            shares["paternal_uncle"] = max(Fraction(1) - furud_others, Fraction(0))
            residue = Fraction(0)

        # ── 'AWL ──────────────────────────────────────────────────────────
        awl_applied = False
        total_shares = sum(shares.values())
        if total_shares > Fraction(1):
            awl_applied = True
            notes.append(f"'Awl applied: total shares = {total_shares}. All reduced proportionally.")
            for k in shares:
                shares[k] = shares[k] / total_shares

        # ── RADD ──────────────────────────────────────────────────────────
        radd_applied = False
        total_shares = sum(shares.values())
        if total_shares < Fraction(1) and not awl_applied:
            radd_eligible = {r: s for r, s in shares.items()
                             if r not in ("husband","wife") and s > 0}
            if radd_eligible:
                surplus = Fraction(1) - total_shares
                radd_total = sum(radd_eligible.values())
                for role in radd_eligible:
                    shares[role] += surplus * (shares[role] / radd_total)
                radd_applied = True
                notes.append(f"Radd applied: surplus {surplus} redistributed among Furud heirs (excl. spouse).")

        # ── DHUL ARHAM — TANZEEL (Hanafi) ─────────────────────────────────
        all_furud_asaba_inherit = any(
            r not in dhul_arham_roles and r not in blocked and shares.get(r, Fraction(0)) > 0
            for r in present
        )
        is_all_dhul = all(r in dhul_arham_roles for r in present if r not in blocked)

        if is_all_dhul and not all_furud_asaba_inherit:
            tanzeel_applied = True
            notes.append("All heirs are Dhul Arham. Tanzeel (Hanafi) applied — each heir steps down to their nearest Furud/Asaba root.")
            shares = self._tanzeel(present, dhul_arham_roles, notes)

        # ── BUILD RESULT TABLE ────────────────────────────────────────────
        total_value = estate.total_value
        shares_table = []

        for role, count in present.items():
            if role in blocked:
                shares_table.append({
                    "heir": role.replace("_"," ").title(),
                    "count": count,
                    "status": f"Blocked by {blocked[role]}",
                    "share_fraction": "—",
                    "share_per_person": "—",
                    "naira_amount": "—",
                    "category": "Mahjub"
                })
            elif role in dhul_arham_roles and role not in shares:
                shares_table.append({
                    "heir": role.replace("_"," ").title(),
                    "count": count,
                    "status": "Dhul Arham — no Furud/Asaba present",
                    "share_fraction": "—",
                    "share_per_person": "—",
                    "naira_amount": "—",
                    "category": "Dhul Arham"
                })
            elif role in shares:
                gs = shares[role]
                pp = gs / count
                n_grp = int(total_value * gs)
                n_pp  = int(total_value * pp)
                # determine status label
                if gs == Fraction(0):
                    status = "Excluded (no residue)"
                else:
                    status = "Inherits"
                shares_table.append({
                    "heir": role.replace("_"," ").title(),
                    "count": count,
                    "status": status,
                    "share_fraction": str(gs),
                    "share_per_person": str(pp),
                    "naira_amount": f"₦{n_grp:,} (₦{n_pp:,} each)" if gs > 0 else "₦0 (excluded)",
                    "category": "Furud/Asaba"
                })
            else:
                shares_table.append({
                    "heir": role.replace("_"," ").title(),
                    "count": count,
                    "status": "Not assigned",
                    "share_fraction": "—",
                    "share_per_person": "—",
                    "naira_amount": "—",
                    "category": "Unknown"
                })

        base = compute_base(shares)

        return Result(
            estate=estate,
            total_estate_value=total_value,
            base=base,
            awl_applied=awl_applied,
            radd_applied=radd_applied,
            tanzeel_applied=tanzeel_applied,
            shares_table=shares_table,
            notes=notes
        )

    def _tanzeel(self, present, dhul_arham_roles, notes):
        """
        Hanafi Tanzeel: step each Dhul Arham heir down to their root Furud/Asaba ancestor.
        Then distribute as if those roots were the actual heirs.
        """
        # Map each Dhul Arham to their root
        root_map = {
            "daughters_son":        "daughter",      # steps to daughter
            "daughters_daughter":   "daughter",
            "full_sisters_daughter":"full_sister",
            "maternal_uncles_son":  "maternal_brother",
            "maternal_aunt":        "mother",
            "paternal_aunt":        "father",
            "maternal_brothers_son":"maternal_brother",
            "maternal_grandfather": "mother",
        }

        # Gather virtual roots
        virtual_present: Dict[str, int] = {}
        for role, count in present.items():
            root = root_map.get(role, role)
            virtual_present[root] = virtual_present.get(root, 0) + count
            notes.append(f"  · {role.replace('_',' ').title()} (×{count}) → steps down to root: {root.replace('_',' ').title()}")

        # Now compute shares as if virtual_present were the actual heirs
        virtual_shares: Dict[str, Fraction] = {}
        vp = virtual_present

        def VP(r): return r in vp

        has_son     = VP("son")
        has_daughter= VP("daughter")
        has_father  = VP("father")
        has_mother  = VP("mother")
        has_fb      = VP("full_brother")
        has_fs      = VP("full_sister")
        has_mb      = VP("maternal_brother")
        has_husband = VP("husband")
        has_wife    = VP("wife")

        # Daughters
        if has_daughter and not has_son:
            virtual_shares["daughter"] = Fraction(1,2) if vp["daughter"]==1 else Fraction(2,3)

        # Mother
        if has_mother:
            virtual_shares["mother"] = Fraction(1,3)

        # Father
        if has_father:
            if has_daughter:
                virtual_shares["father"] = Fraction(1,6)
            # else pure Asaba below

        # Full Sister
        if has_fs and not has_son and not has_father:
            if not has_fb:
                virtual_shares["full_sister"] = Fraction(1,2) if vp.get("full_sister",1)==1 else Fraction(2,3)

        # Maternal Brother
        if has_mb:
            total_mat = vp.get("maternal_brother",0) + vp.get("maternal_sister",0)
            virtual_shares["maternal_brother"] = Fraction(1,6) if total_mat==1 else Fraction(1,3)

        # Asaba
        total_furud = sum(virtual_shares.values())
        residue = Fraction(1) - total_furud

        if has_father:
            furud_no_father = sum(v for k,v in virtual_shares.items() if k!="father")
            virtual_shares["father"] = max(Fraction(1)-furud_no_father, Fraction(0))
        elif has_fb:
            furud_no_fb = sum(v for k,v in virtual_shares.items() if k!="full_brother")
            virtual_shares["full_brother"] = max(Fraction(1)-furud_no_fb, Fraction(0))
        elif has_daughter and not has_father and not has_son:
            # Radd to daughter if no asaba
            radd = Fraction(1) - sum(virtual_shares.values())
            if radd > 0:
                virtual_shares["daughter"] = virtual_shares.get("daughter", Fraction(0)) + radd

        # Radd to mother if she's alone
        total_virtual = sum(virtual_shares.values())
        if total_virtual < Fraction(1) and has_mother and len(virtual_shares)==1:
            virtual_shares["mother"] = Fraction(1)

        # Now map virtual shares back to original Dhul Arham roles
        result_shares: Dict[str, Fraction] = {}
        for role, count in present.items():
            root = root_map.get(role, role)
            root_share = virtual_shares.get(root, Fraction(0))
            # split share among same-root heirs proportionally by count
            same_root_total = sum(c for r2, c in present.items() if root_map.get(r2, r2)==root)
            result_shares[role] = root_share * Fraction(count, same_root_total)

        return result_shares

    def format_report(self, result: Result) -> str:
        e = result.estate
        lines = [
            "=" * 72,
            f"  MAWĀRITH ANALYTICS v2 — Estate of: {e.deceased_name}",
            f"  Location    : {e.location}",
            f"  Cash        : ₦{e.cash:,}",
            f"  Asset Value : ₦{e.asset_value:,}",
            f"  TOTAL ESTATE: ₦{e.total_value:,}",
            "=" * 72,
            f"  Asl al-Masala   : {result.base}",
            f"  'Awl Applied    : {'Yes' if result.awl_applied else 'No'}",
            f"  Radd Applied    : {'Yes' if result.radd_applied else 'No'}",
            f"  Tanzeel Applied : {'Yes' if result.tanzeel_applied else 'No'}",
            "-" * 72,
            f"  {'HEIR':<26} {'N':>3}  {'STATUS':<22} {'SHARE':>8}  {'NAIRA AMOUNT'}",
            "-" * 72,
        ]
        for row in result.shares_table:
            lines.append(
                f"  {row['heir']:<26} {row['count']:>3}  {row['status']:<22} "
                f"{row['share_fraction']:>8}  {row['naira_amount']}"
            )
        if result.notes:
            lines.append("-" * 72)
            lines.append("  FIQH NOTES:")
            for n in result.notes:
                lines.append(f"  • {n}")
        lines.append("=" * 72)
        return "\n".join(lines)


# ─────────────────────────────────────────────
# PCIED DATASET — 20 Cases
# ─────────────────────────────────────────────

PCIED_CASES = [
    Estate("Late Mr. Muhammad Salim of Ajah, Lagos State", "male", "Ajah, Lagos",
           cash=10_000_000,
           assets=["2019 Toyota Camry","4-bedroom flat in Lekki","Farm 3 plots in Ewekoro"],
           heirs_input={"wife":3,"mother":1,"grandmother":1,"maternal_sister":1,"full_brother":2,"paternal_uncle":2}),

    Estate("Late Mrs. Fatimah Yusuf of Ilorin, Kwara State", "female", "Ilorin, Kwara",
           cash=6_000_000,
           assets=["4-room apartment in Ilorin","10 uncompleted rooms in Malete","Pharmaceutical company in Ikeja"],
           heirs_input={"full_sister":5,"husband":1,"maternal_brother":2,"daughter":12}),

    Estate("Late Mr. Rasheed Ali of Maitama, Abuja", "male", "Maitama, Abuja",
           cash=800_000,
           assets=["2 four-bedroom flats in Abuja","2 plots of land in Lagos"],
           heirs_input={"wife":4,"daughter":2,"sons_daughter":1,"sons_son":1,
                        "full_brother":1,"maternal_sister":2,"full_uncle":1,"mother":1,"father":1}),

    Estate("Late Mrs. Safiyyah Muslim of Ibadan, Oyo State", "female", "Ibadan, Oyo",
           cash=9_000_000,
           assets=["8 rooms on the Island, Lagos","Petrol station in Iwo Road, Ibadan"],
           heirs_input={"full_brother":3,"sons_daughter":1,"mother":1,"husband":1,"paternal_aunt":1,"paternal_brother":5}),

    Estate("Late Mrs. Khadijat Saheed of Akure, Ondo State", "female", "Akure, Ondo",
           cash=100_000_000,
           assets=["8 uncompleted rooms in Abuja (upstairs)","12 completed rooms (downstairs)","10 shops in Ikare"],
           heirs_input={"sons_daughter":7,"daughter":4,"mother":1,"husband":1}),

    Estate("Late Mr. Anas Luqman of Akure, Ondo State", "male", "Akure, Ondo",
           cash=1_500_000,
           assets=["6 self-contained units in Ondo","3-bedroom flats in Kano"],
           heirs_input={"wife":3,"sons_son":4,"daughter":5,"full_sister":7}),

    Estate("Late Mr. Hadi Ridwan of Ibadan, Oyo State", "male", "Ibadan, Oyo",
           cash=2_900_000,
           assets=["3 plots of land in Ibadan","3 Toyota Hilux (2019)"],
           heirs_input={"maternal_brother":2,"mother":1,"wife":1}),

    Estate("Late Mr. Muhammad Bala of Isolo, Lagos State", "male", "Isolo, Lagos",
           cash=900_000,
           assets=["2018 Toyota Camry (fairly used)","2-bedroom flat in Maryland, Lagos"],
           heirs_input={"sons_daughter":4,"paternal_sister":8,"wife":1,"mother":1}),

    Estate("Late Mr. Siddiq Adewole of Garki, Abuja", "male", "Garki, Abuja",
           cash=0,
           assets=["12 plots of land in Magodo, Lagos","10-bedroom flat in Maitama, Abuja","3 HP Laptops"],
           heirs_input={"son":4,"daughter":3,"wife":1}),

    Estate("Late Mr. Bello Ayola of Ilorin, Kwara State", "male", "Ilorin, Kwara",
           cash=8_000_000,
           assets=["5 plots of land in GRA Ilorin","3-bedroom apartment in USA","Petrol station in Onitsha"],
           heirs_input={"wife":1,"father":1,"mother":1,"full_sister":4,"full_brother":2,"full_uncle":4,"full_aunt":4}),

    Estate("Late Mrs. Salawu Hashim of Ikeja, Lagos State", "female", "Ikeja, Lagos",
           cash=8_000_000,
           assets=["Textile industry at Oshodi","25 self-contained rooms in Ile-Ife"],
           heirs_input={"father":1,"mother":1,"full_sister":3,"full_brother":1,
                        "paternal_brother":5,"husband":1,"paternal_sister":3}),

    Estate("Late Mrs. Haleemat Oyewole of Ilorin, Kwara State", "female", "Ilorin, Kwara",
           cash=50_000_000,
           assets=["Jaiz Bank shares ₦5M","Plot of land with 5-bedroom foundation in Taiwo","Hyundai Accent 2020"],
           heirs_input={"mother":1,"husband":1,"maternal_brother":3,"full_brother":2}),

    Estate("Late Mrs. Maryam Garuba of Lekki, Lagos State", "female", "Lekki, Lagos",
           cash=500_000,
           assets=["4 Bajaj motorcycles (new)","2-bedroom flat in Iyana Ipaja","Lotus Capital investment ₦3M"],
           heirs_input={"daughters_son":1,"full_sisters_daughter":1,"paternal_aunt":1}),

    Estate("Late Mr. Yaqub Musa of Marina, Lagos State", "male", "Marina, Lagos",
           cash=4_000_000,
           assets=["2 hectares in Victoria Island","30-shop complex in Idumota","Dell Vostro laptop"],
           heirs_input={"maternal_aunt":1,"maternal_grandfather":1,"maternal_brothers_son":1,"daughters_daughter":1}),

    Estate("Late Mrs. Kabeerat Ibrahim of Igando, Lagos State", "female", "Igando, Lagos",
           cash=6_000_000,
           assets=["Estate with 30 houses (3-bedroom each) in Isolo","Taj Bank shares ₦7M"],
           heirs_input={"husband":1,"daughter":5,"grandfather":1,"paternal_brother":5}),

    Estate("Late Mrs. Zainab Bako of Benin, Edo State", "female", "Benin, Edo",
           cash=1_200_000,
           assets=["Jincheng motorcycle","3 plots of land"],
           heirs_input={"mother":1,"grandfather":1,"full_brother":2,"paternal_sister":1}),

    Estate("Late Mrs. Laraba Shetima of Zaria, Kaduna State", "female", "Zaria, Kaduna",
           cash=50_000,
           assets=["Self-contained room in Ikotun, Lagos","Lotus Capital shares ₦5M"],
           heirs_input={"husband":1,"mother":1,"grandfather":1,"full_sister":2}),

    Estate("Late Mr. Faadil Aina of Ajah, Lagos State", "male", "Ajah, Lagos",
           cash=300_000,
           assets=["Secondary school in Garki, Abuja","4 three-bedroom flats"],
           heirs_input={"wife":2,"grandmother":1,"maternal_sister":2}),

    Estate("Late Mrs. Ramat Yakubu of Otta, Ogun State", "female", "Otta, Ogun",
           cash=0,
           assets=["Cassava farm 5 plots in Mowe","Bajaj tricycle","10 uncompleted rooms in Abule Egba"],
           heirs_input={"husband":1,"grandfather":1,"paternal_aunt":1,"son":1}),

    Estate("Late Mr. Adamu Adamu of Ilorin, Kwara State", "male", "Ilorin, Kwara",
           cash=400_000,
           assets=["2015 Sienna car","2 plots of land in Saare, Kwara"],
           heirs_input={"wife":4,"grandmother":2,"maternal_sister":2,"full_sister":4}),
]


if __name__ == "__main__":
    engine = MawaarithEngine()
    all_results = []
    for i, case in enumerate(PCIED_CASES, 1):
        r = engine.compute(case)
        all_results.append(r)
        print(f"\n[CASE {i:02d}]")
        print(engine.format_report(r))

    print(f"\n{'='*72}")
    print(f"  SUMMARY — All 20 PCIED Cases")
    print(f"  'Awl cases      : {sum(1 for r in all_results if r.awl_applied)}/20")
    print(f"  Radd cases      : {sum(1 for r in all_results if r.radd_applied)}/20")
    print(f"  Tanzeel cases   : {sum(1 for r in all_results if r.tanzeel_applied)}/20")
    print(f"  Total estates   : ₦{sum(r.total_estate_value for r in all_results):,}")
    print(f"{'='*72}")
