"""
=============================================================
Mawārith Analytics — Project 1
Fiqh al-Mawārith Engine: Automated Islamic Inheritance Calculator
=============================================================
Dataset: 20 estate cases from Project_PCIED_2023 (Jāmi'at al-Hikmah, Ilorin)
Author : Mawārith Analytics / Elbaseety Institute®
=============================================================

Rules implemented (Hanafi/mainstream Sunni framework):
  - Primary Qur'anic heirs (Ashab al-Furud) with fixed shares
  - Residuaries (Asaba) by agnatic priority
  - Blocking (Hajb) rules: full blocking and reduction blocking
  - 'Awl (proportional reduction when shares exceed 1)
  - Radd (return of surplus to Furud heirs when no Asaba)
  - Mahjub (blocked heir) identification
"""

from fractions import Fraction
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class Heir:
    role: str
    count: int = 1
    share: Fraction = Fraction(0)
    blocked_by: Optional[str] = None
    category: str = ""          # furud / asaba / dhul_arham


@dataclass
class Estate:
    deceased_name: str
    gender: str                  # 'male' | 'female'
    location: str
    cash: int = 0
    assets: List[str] = field(default_factory=list)
    heirs_input: Dict[str, int] = field(default_factory=dict)


@dataclass
class Result:
    estate: Estate
    heirs: List[Heir]
    total_estate_value: int
    base: int                    # common denominator (asl al-masala)
    awl_applied: bool
    radd_applied: bool
    shares_table: List[dict]
    notes: List[str]


# ─────────────────────────────────────────────
# THE ENGINE
# ─────────────────────────────────────────────

class MawaarithEngine:
    """
    Computes Islamic inheritance shares according to classical Fiqh rules.
    Returns exact Fraction objects — no floating point rounding errors.
    """

    # Roles recognised by the engine
    FURUD_ROLES = {
        "husband", "wife",
        "father", "mother",
        "grandfather", "grandmother", "maternal_grandfather",
        "son", "daughter",
        "sons_son", "sons_daughter",
        "full_brother", "full_sister",
        "paternal_brother", "paternal_sister",
        "maternal_brother", "maternal_sister",
        "full_uncle", "paternal_uncle",
        "full_aunt", "paternal_aunt", "maternal_aunt",
        "daughters_son", "daughters_daughter",
        "full_sisters_daughter", "maternal_uncles_son",
        "sons_sons_son",
    }

    def compute(self, estate: Estate) -> Result:
        heirs_input = estate.heirs_input
        gender = estate.gender
        notes = []

        # ── Step 1: Parse heirs ──────────────────────────────────────────
        present = {role: count for role, count in heirs_input.items() if count > 0}

        # ── Step 2: Apply blocking (Hajb) rules ──────────────────────────
        blocked = {}

        # Father blocks grandfather, paternal uncle
        if "father" in present:
            for r in ["grandfather", "paternal_uncle", "full_uncle"]:
                if r in present:
                    blocked[r] = "father"

        # Son / sons_son blocks brothers, sisters, paternal uncles
        if "son" in present or "sons_son" in present:
            for r in ["full_brother", "full_sister", "paternal_brother",
                      "paternal_sister", "maternal_brother", "maternal_sister",
                      "full_uncle", "paternal_uncle"]:
                if r in present:
                    blocked[r] = "son or son's son"

        # Full brother blocks paternal brother
        if "full_brother" in present and "full_brother" not in blocked:
            for r in ["paternal_brother", "paternal_sister"]:
                if r in present:
                    blocked[r] = "full_brother"

        # Son blocks son's daughter (unless son's son present)
        if "son" in present and "sons_daughter" in present and "sons_son" not in present:
            blocked["sons_daughter"] = "son"

        # Mother blocks grandmother
        if "mother" in present:
            for r in ["grandmother", "maternal_grandfather"]:
                if r in present:
                    blocked[r] = "mother"

        # Husband/wife get fixed shares regardless — never blocked

        # Daughters_son, daughters_daughter, full_sisters_daughter → Dhul Arham (no fixed share in Hanafi here)
        dhul_arham_roles = {"daughters_son", "daughters_daughter", "full_sisters_daughter",
                            "maternal_uncles_son", "maternal_aunt", "paternal_aunt"}

        # ── Step 3: Assign Furud shares ──────────────────────────────────
        shares: Dict[str, Fraction] = {}

        def add(role, frac):
            shares[role] = frac

        has_son = "son" in present and "son" not in blocked
        has_sons_son = "sons_son" in present and "sons_son" not in blocked
        has_daughter = "daughter" in present and "daughter" not in blocked
        has_sons_daughter = "sons_daughter" in present and "sons_daughter" not in blocked
        has_father = "father" in present and "father" not in blocked
        has_mother = "mother" in present and "mother" not in blocked
        has_grandfather = "grandfather" in present and "grandfather" not in blocked
        has_grandmother = "grandmother" in present and "grandmother" not in blocked
        has_full_brother = "full_brother" in present and "full_brother" not in blocked
        has_full_sister = "full_sister" in present and "full_sister" not in blocked
        has_paternal_sister = "paternal_sister" in present and "paternal_sister" not in blocked
        has_maternal_brother = "maternal_brother" in present and "maternal_brother" not in blocked
        has_maternal_sister = "maternal_sister" in present and "maternal_sister" not in blocked
        has_husband = "husband" in present
        has_wife = "wife" in present

        n_wives = present.get("wife", 0)
        n_daughters = present.get("daughter", 0)
        n_sons = present.get("son", 0)
        n_sons_sons = present.get("sons_son", 0)
        n_sons_daughters = present.get("sons_daughter", 0)
        n_full_brothers = present.get("full_brother", 0)
        n_full_sisters = present.get("full_sister", 0)
        n_paternal_sisters = present.get("paternal_sister", 0)
        n_maternal_brothers = present.get("maternal_brother", 0)
        n_maternal_sisters = present.get("maternal_sister", 0)

        # Husband
        if has_husband:
            if has_son or has_sons_son or has_daughter or has_sons_daughter:
                add("husband", Fraction(1, 4))
            else:
                add("husband", Fraction(1, 2))

        # Wife / Wives (shared equally)
        if has_wife:
            if has_son or has_sons_son or has_daughter or has_sons_daughter:
                add("wife", Fraction(1, 8))
            else:
                add("wife", Fraction(1, 4))

        # Father
        if has_father:
            if has_son or has_sons_son:
                add("father", Fraction(1, 6))   # Furud only
            elif has_daughter or has_sons_daughter:
                add("father", Fraction(1, 6))   # Furud + residue (handled in Asaba step)
                notes.append("Father gets 1/6 fixed + residue as Asaba (daughters present, no sons).")
            else:
                # Father is pure Asaba — assigned below
                pass

        # Mother
        if has_mother:
            # 1/3 normally, 1/6 if children or 2+ siblings
            has_children = has_son or has_sons_son or has_daughter or has_sons_daughter
            sibling_count = (n_full_brothers + n_full_sisters +
                             (present.get("paternal_brother", 0) if "paternal_brother" not in blocked else 0) +
                             (present.get("paternal_sister", 0) if "paternal_sister" not in blocked else 0) +
                             (n_maternal_brothers if "maternal_brother" not in blocked else 0) +
                             (n_maternal_sisters if "maternal_sister" not in blocked else 0))
            if has_children or sibling_count >= 2:
                add("mother", Fraction(1, 6))
            else:
                add("mother", Fraction(1, 3))

        # Grandfather (if not blocked — acts like father)
        if has_grandfather and "grandfather" not in blocked:
            has_children = has_son or has_sons_son or has_daughter or has_sons_daughter
            if has_children:
                add("grandfather", Fraction(1, 6))
            else:
                pass  # Pure Asaba

        # Grandmother
        if has_grandmother and "grandmother" not in blocked:
            add("grandmother", Fraction(1, 6))

        # Daughters
        if has_daughter and not has_son:
            if n_daughters == 1:
                add("daughter", Fraction(1, 2))
            else:
                add("daughter", Fraction(2, 3))  # shared among all daughters

        # Son's Daughter
        if has_sons_daughter and not has_son and not has_sons_son:
            if n_sons_daughters == 1:
                if n_daughters == 0:
                    add("sons_daughter", Fraction(1, 2))
                elif n_daughters == 1:
                    add("sons_daughter", Fraction(1, 6))   # complement to 2/3
                else:
                    blocked["sons_daughter"] = "2+ daughters (no complement)"
                    notes.append("Son's daughter blocked — two or more daughters already reach 2/3 ceiling.")
            else:
                if n_daughters == 0:
                    add("sons_daughter", Fraction(2, 3))

        # Full Sisters (when no son, father, grandfather)
        if has_full_sister and not has_son and not has_sons_son and not has_father and not has_grandfather:
            if not has_full_brother:
                if n_full_sisters == 1:
                    add("full_sister", Fraction(1, 2))
                else:
                    add("full_sister", Fraction(2, 3))
            # If full_brother present → Asaba bil-Ghair (handled below)

        # Paternal Sisters
        if has_paternal_sister and "paternal_sister" not in blocked:
            if not has_full_brother and not has_full_sister and not has_son and not has_father:
                if n_paternal_sisters == 1:
                    add("paternal_sister", Fraction(1, 2))
                else:
                    add("paternal_sister", Fraction(2, 3))

        # Maternal Siblings (1/6 each or 1/3 shared)
        if has_maternal_brother and "maternal_brother" not in blocked:
            total_mat = n_maternal_brothers + n_maternal_sisters
            if total_mat == 1:
                add("maternal_brother", Fraction(1, 6))
            else:
                add("maternal_brother", Fraction(1, 3))  # shared
        if has_maternal_sister and "maternal_sister" not in blocked:
            total_mat = n_maternal_brothers + n_maternal_sisters
            if total_mat == 1:
                add("maternal_sister", Fraction(1, 6))
            else:
                add("maternal_sister", Fraction(1, 3))   # shared

        # ── Step 4: Compute total Furud ───────────────────────────────────
        furud_total = sum(shares.values())

        # ── Step 5: Asaba (Residuaries) ───────────────────────────────────
        residue = Fraction(1) - furud_total
        asaba_role = None

        if has_son:
            asaba_role = "son"
        elif has_sons_son:
            asaba_role = "sons_son"
        elif has_father and "father" not in blocked:
            asaba_role = "father"
            if "father" in shares:
                residue = Fraction(1) - (furud_total - shares["father"])
            else:
                residue = Fraction(1) - furud_total
            shares["father"] = shares.get("father", Fraction(0)) + max(residue, Fraction(0))
            asaba_role = None   # already merged
        elif has_grandfather and "grandfather" not in blocked and not has_father:
            asaba_role = "grandfather"
            if "grandfather" in shares:
                residue = Fraction(1) - (furud_total - shares["grandfather"])
            else:
                residue = Fraction(1) - furud_total
            shares["grandfather"] = shares.get("grandfather", Fraction(0)) + max(residue, Fraction(0))
            asaba_role = None
        elif has_full_brother:
            asaba_role = "full_brother"
        elif has_full_sister and has_daughter:
            # Full sister becomes Asaba ma'al-Ghair with daughter
            asaba_role = "full_sister_asaba"
            shares["full_sister"] = max(residue, Fraction(0))
            notes.append("Full sister(s) inherit as Asaba ma'al-Ghair (with daughter).")
            asaba_role = None
        elif "paternal_brother" in present and "paternal_brother" not in blocked:
            asaba_role = "paternal_brother"
        elif "full_uncle" in present and "full_uncle" not in blocked:
            asaba_role = "full_uncle"
        elif "paternal_uncle" in present and "paternal_uncle" not in blocked:
            asaba_role = "paternal_uncle"

        if asaba_role:
            shares[asaba_role] = max(residue, Fraction(0))

        # Son + Daughter → 2:1 Asaba split
        if has_son and has_daughter:
            total_children_parts = n_sons * 2 + n_daughters * 1
            child_residue = Fraction(1) - (furud_total - shares.get("son", Fraction(0)))
            shares["son"] = child_residue * Fraction(n_sons * 2, total_children_parts)
            shares["daughter"] = child_residue * Fraction(n_daughters, total_children_parts)
            notes.append(f"Sons and daughters share residue 2:1 (male:female).")

        # Full Brother + Full Sister → 2:1
        if has_full_brother and has_full_sister and "full_brother" not in blocked:
            total_parts = n_full_brothers * 2 + n_full_sisters
            shares["full_brother"] = residue * Fraction(n_full_brothers * 2, total_parts)
            shares["full_sister"] = residue * Fraction(n_full_sisters, total_parts)

        # ── Step 6: 'Awl — if total shares > 1 ───────────────────────────
        furud_total_final = sum(shares.values())
        awl_applied = False
        if furud_total_final > Fraction(1):
            awl_applied = True
            notes.append(f"'Awl applied: total shares = {furud_total_final} > 1. All shares reduced proportionally.")
            for role in shares:
                shares[role] = shares[role] / furud_total_final

        # ── Step 7: Radd — surplus returned to Furud heirs ───────────────
        radd_applied = False
        final_total = sum(shares.values())
        if final_total < Fraction(1) and not asaba_role and "father" not in [
            k for k, v in blocked.items()]:
            # Check if there are Furud heirs who qualify for Radd (not husband/wife)
            radd_eligible = {r: s for r, s in shares.items() if r not in ("husband", "wife") and s > 0}
            if radd_eligible:
                surplus = Fraction(1) - final_total
                radd_total = sum(radd_eligible.values())
                for role in radd_eligible:
                    shares[role] += surplus * (shares[role] / radd_total)
                radd_applied = True
                notes.append(f"Radd applied: surplus {surplus} redistributed proportionally among Furud heirs.")

        # ── Step 8: Build result table ────────────────────────────────────
        total_value = estate.cash   # use cash as distributable estate for now
        shares_table = []

        for role, count in present.items():
            if role in blocked:
                shares_table.append({
                    "heir": role.replace("_", " ").title(),
                    "count": count,
                    "status": f"Blocked by {blocked[role]}",
                    "share_fraction": "—",
                    "share_per_person": "—",
                    "naira_amount": "—",
                    "category": "Mahjub"
                })
            elif role in dhul_arham_roles and role not in shares:
                shares_table.append({
                    "heir": role.replace("_", " ").title(),
                    "count": count,
                    "status": "Dhul Arham (inherits only if no Furud/Asaba)",
                    "share_fraction": "—",
                    "share_per_person": "—",
                    "naira_amount": "—",
                    "category": "Dhul Arham"
                })
            elif role in shares:
                group_share = shares[role]
                per_person = group_share / count
                naira_group = int(total_value * group_share)
                naira_per = int(total_value * per_person)
                shares_table.append({
                    "heir": role.replace("_", " ").title(),
                    "count": count,
                    "status": "Inherits",
                    "share_fraction": str(group_share),
                    "share_per_person": str(per_person),
                    "naira_amount": f"₦{naira_group:,} (₦{naira_per:,} each)",
                    "category": "Furud/Asaba"
                })

        # Base (Asl al-Masala) — LCM of denominators
        denoms = [s.denominator for s in shares.values() if s > 0]
        from math import gcd
        def lcm(a, b): return a * b // gcd(a, b)
        base = 1
        for d in denoms:
            base = lcm(base, d)

        return Result(
            estate=estate,
            heirs=[], 
            total_estate_value=total_value,
            base=base,
            awl_applied=awl_applied,
            radd_applied=radd_applied,
            shares_table=shares_table,
            notes=notes
        )

    def format_report(self, result: Result) -> str:
        e = result.estate
        lines = [
            "=" * 65,
            f"  MAWĀRITH ANALYTICS — Fiqh al-Mawārith Engine",
            f"  Estate of: {e.deceased_name}",
            f"  Location  : {e.location}",
            f"  Cash      : ₦{e.cash:,}",
            "=" * 65,
            f"  Asl al-Masala (Base): {result.base}",
            f"  'Awl Applied        : {'Yes' if result.awl_applied else 'No'}",
            f"  Radd Applied        : {'Yes' if result.radd_applied else 'No'}",
            "-" * 65,
            f"  {'HEIR':<25} {'COUNT':>5}  {'SHARE':>10}  {'NAIRA AMOUNT'}",
            "-" * 65,
        ]
        for row in result.shares_table:
            lines.append(
                f"  {row['heir']:<25} {row['count']:>5}  {row['share_fraction']:>10}  {row['naira_amount']}"
            )
        if result.notes:
            lines.append("-" * 65)
            lines.append("  FIQH NOTES:")
            for n in result.notes:
                lines.append(f"  • {n}")
        lines.append("=" * 65)
        return "\n".join(lines)


# ─────────────────────────────────────────────
# PCIED DATASET — 20 Cases from Jāmi'at al-Hikmah
# ─────────────────────────────────────────────

PCIED_CASES = [
    Estate(
        deceased_name="Late Mr. Muhammad Salim of Ajah, Lagos State",
        gender="male", location="Ajah, Lagos",
        cash=10_000_000,
        assets=["2019 Toyota Camry", "4-bedroom flat in Lekki", "Farm 3 plots in Ewekoro"],
        heirs_input={"wife": 3, "mother": 1, "grandmother": 1,
                     "maternal_sister": 1, "full_brother": 2, "paternal_uncle": 2}
    ),
    Estate(
        deceased_name="Late Mrs. Fatimah Yusuf of Ilorin, Kwara State",
        gender="female", location="Ilorin, Kwara",
        cash=6_000_000,
        assets=["4-room apartment in Ilorin", "10 uncompleted rooms in Malete",
                "Pharmaceutical company in Ikeja"],
        heirs_input={"full_sister": 5, "husband": 1, "maternal_brother": 2, "daughter": 12}
    ),
    Estate(
        deceased_name="Late Mr. Rasheed Ali of Maitama, Abuja",
        gender="male", location="Maitama, Abuja",
        cash=800_000,
        assets=["2 four-bedroom flats in Abuja", "2 plots of land in Lagos"],
        heirs_input={"wife": 4, "daughter": 2, "sons_daughter": 1, "sons_son": 1,
                     "full_brother": 1, "maternal_sister": 2, "full_uncle": 1,
                     "mother": 1, "father": 1}
    ),
    Estate(
        deceased_name="Late Mrs. Safiyyah Muslim of Ibadan, Oyo State",
        gender="female", location="Ibadan, Oyo",
        cash=9_000_000,
        assets=["8 rooms on the Island, Lagos", "Petrol station in Iwo Road, Ibadan"],
        heirs_input={"full_brother": 3, "sons_daughter": 1, "mother": 1,
                     "husband": 1, "paternal_aunt": 1, "paternal_brother": 5}
    ),
    Estate(
        deceased_name="Late Mrs. Khadijat Saheed of Akure, Ondo State",
        gender="female", location="Akure, Ondo",
        cash=100_000_000,
        assets=["8 uncompleted rooms in Abuja (upstairs)", "12 completed rooms (downstairs)",
                "10 shops in Ikare"],
        heirs_input={"sons_daughter": 7, "daughter": 4, "mother": 1, "husband": 1}
    ),
    Estate(
        deceased_name="Late Mr. Anas Luqman of Akure, Ondo State",
        gender="male", location="Akure, Ondo",
        cash=1_500_000,
        assets=["6 self-contained units in Ondo", "3-bedroom flats in Kano"],
        heirs_input={"wife": 3, "sons_son": 4, "daughter": 5, "full_sister": 7}
    ),
    Estate(
        deceased_name="Late Mr. Hadi Ridwan of Ibadan, Oyo State",
        gender="male", location="Ibadan, Oyo",
        cash=2_900_000,
        assets=["3 plots of land in Ibadan", "3 Toyota Hilux (2019)"],
        heirs_input={"maternal_brother": 2, "mother": 1, "wife": 1}
    ),
    Estate(
        deceased_name="Late Mr. Muhammad Bala of Isolo, Lagos State",
        gender="male", location="Isolo, Lagos",
        cash=900_000,
        assets=["2018 Toyota Camry (fairly used)", "2-bedroom flat in Maryland, Lagos"],
        heirs_input={"sons_daughter": 4, "paternal_sister": 8, "wife": 1, "mother": 1}
    ),
    Estate(
        deceased_name="Late Mr. Siddiq Adewole of Garki, Abuja",
        gender="male", location="Garki, Abuja",
        cash=0,
        assets=["12 plots of land in Magodo, Lagos", "10-bedroom flat in Maitama, Abuja",
                "3 HP Laptops"],
        heirs_input={"son": 4, "daughter": 3, "wife": 1}
    ),
    Estate(
        deceased_name="Late Mr. Bello Ayola of Ilorin, Kwara State",
        gender="male", location="Ilorin, Kwara",
        cash=8_000_000,
        assets=["5 plots of land in GRA Ilorin", "3-bedroom apartment in USA",
                "Petrol station in Onitsha"],
        heirs_input={"wife": 1, "father": 1, "mother": 1, "full_sister": 4,
                     "full_brother": 2, "full_uncle": 4, "full_aunt": 4}
    ),
    Estate(
        deceased_name="Late Mrs. Salawu Hashim of Ikeja, Lagos State",
        gender="female", location="Ikeja, Lagos",
        cash=8_000_000,
        assets=["Textile industry at Oshodi", "25 self-contained rooms in Ile-Ife"],
        heirs_input={"father": 1, "mother": 1, "full_sister": 3, "full_brother": 1,
                     "paternal_brother": 5, "husband": 1, "paternal_sister": 3}
    ),
    Estate(
        deceased_name="Late Mrs. Haleemat Oyewole of Ilorin, Kwara State",
        gender="female", location="Ilorin, Kwara",
        cash=50_000_000,
        assets=["Jaiz Bank shares ₦5M", "Plot of land with 5-bedroom foundation in Taiwo",
                "Hyundai Accent 2020"],
        heirs_input={"mother": 1, "husband": 1, "maternal_brother": 3, "full_brother": 2}
    ),
    Estate(
        deceased_name="Late Mrs. Maryam Garuba of Lekki, Lagos State",
        gender="female", location="Lekki, Lagos",
        cash=500_000,
        assets=["4 Bajaj motorcycles (new)", "2-bedroom flat in Iyana Ipaja",
                "Lotus Capital investment ₦3M"],
        heirs_input={"daughters_son": 1, "full_sisters_daughter": 1, "paternal_aunt": 1}
    ),
    Estate(
        deceased_name="Late Mr. Yaqub Musa of Marina, Lagos State",
        gender="male", location="Marina, Lagos",
        cash=4_000_000,
        assets=["2 hectares in Victoria Island", "30-shop complex in Idumota",
                "Dell Vostro laptop"],
        heirs_input={"maternal_aunt": 1, "maternal_grandfather": 1,
                     "maternal_brothers_son": 1, "daughters_daughter": 1}
    ),
    Estate(
        deceased_name="Late Mrs. Kabeerat Ibrahim of Igando, Lagos State",
        gender="female", location="Igando, Lagos",
        cash=6_000_000,
        assets=["Estate with 30 houses (3-bedroom each) in Isolo",
                "Taj Bank shares ₦7M"],
        heirs_input={"husband": 1, "daughter": 5, "grandfather": 1, "paternal_brother": 5}
    ),
    Estate(
        deceased_name="Late Mrs. Zainab Bako of Benin, Edo State",
        gender="female", location="Benin, Edo",
        cash=1_200_000,
        assets=["Jincheng motorcycle", "3 plots of land"],
        heirs_input={"mother": 1, "grandfather": 1, "full_brother": 2, "paternal_sister": 1}
    ),
    Estate(
        deceased_name="Late Mrs. Laraba Shetima of Zaria, Kaduna State",
        gender="female", location="Zaria, Kaduna",
        cash=50_000,
        assets=["Self-contained room in Ikotun, Lagos", "Lotus Capital shares ₦5M"],
        heirs_input={"husband": 1, "mother": 1, "grandfather": 1, "full_sister": 2}
    ),
    Estate(
        deceased_name="Late Mr. Faadil Aina of Ajah, Lagos State",
        gender="male", location="Ajah, Lagos",
        cash=300_000,
        assets=["Secondary school in Garki, Abuja", "4 three-bedroom flats"],
        heirs_input={"wife": 2, "grandmother": 1, "maternal_sister": 2}
    ),
    Estate(
        deceased_name="Late Mrs. Ramat Yakubu of Otta, Ogun State",
        gender="female", location="Otta, Ogun",
        cash=0,
        assets=["Cassava farm 5 plots in Mowe", "Bajaj tricycle",
                "10 uncompleted rooms in Abule Egba"],
        heirs_input={"husband": 1, "grandfather": 1, "paternal_aunt": 1, "son": 1}
    ),
    Estate(
        deceased_name="Late Mr. Adamu Adamu of Ilorin, Kwara State",
        gender="male", location="Ilorin, Kwara",
        cash=400_000,
        assets=["2015 Sienna car", "2 plots of land in Saare, Kwara"],
        heirs_input={"wife": 4, "grandmother": 2, "maternal_sister": 2, "full_sister": 4}
    ),
]


# ─────────────────────────────────────────────
# MAIN — Run all 20 cases
# ─────────────────────────────────────────────

if __name__ == "__main__":
    engine = MawaarithEngine()
    all_results = []

    for i, case in enumerate(PCIED_CASES, 1):
        result = engine.compute(case)
        all_results.append(result)
        print(f"\n[CASE {i:02d}]")
        print(engine.format_report(result))

    print(f"\n✅ All {len(PCIED_CASES)} PCIED cases processed successfully.")
    print(f"   'Awl (reduction) cases : {sum(1 for r in all_results if r.awl_applied)}")
    print(f"   Radd (return) cases    : {sum(1 for r in all_results if r.radd_applied)}")
