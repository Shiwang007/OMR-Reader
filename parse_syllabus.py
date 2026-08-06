"""
Syllabus Parser
---------------
Parses a structured class syllabus text (like the Biology XII example)
and extracts it into a clean JSON structure.

Output JSON shape:
{
  "class": "XII",
  "subject": "BIOLOGY",
  "chapters": [
    {
      "chapter_no": 1,
      "chapter_name": "SEXUAL REPRODUCTION IN FLOWERING PLANTS",
      "topics": [
        {
          "lecture_no": 1,
          "title": "Stamen, Microsporogenesis"
        },
        ...
      ]
    },
    ...
  ]
}
"""

import re
import json


# ── helpers ──────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    """Strip extra whitespace from a string."""
    return re.sub(r"\s+", " ", text).strip()


# ── topic splitter ───────────────────────────────────────────────────────────

def split_topics(title: str) -> list:
    """
    Split a lecture title into individual topics.

    Rules:
      1. Split on ' ; ' always (explicit multi-topic separator).
      2. Within each chunk, split on ', ' ONLY when the comma is NOT
         inside parentheses — i.e. "Stamen, Microsporogenesis" → two topics,
         but "Pollen grain (Structure, Benefits etc.)" stays as one.
    """
    results = []
    # Step 1: split on semicolons
    chunks = [c.strip() for c in title.split(';')]

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        # Step 2: split on commas outside parentheses
        parts = []
        current = []
        depth = 0
        for char in chunk:
            if char == '(':
                depth += 1
                current.append(char)
            elif char == ')':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                part = ''.join(current).strip()
                if part:
                    parts.append(part)
                current = []
            else:
                current.append(char)
        # flush remainder
        part = ''.join(current).strip()
        if part:
            parts.append(part)

        results.extend(parts)

    return results


# ── core parser ───────────────────────────────────────────────────────────────

def parse_syllabus(raw_text: str) -> dict:
    """
    Parse a plain-text syllabus into a structured dict.

    Recognised patterns
    -------------------
    Header line  : "CLASS – XII" / "CLASS - XII" / "CLASS XII"
    Subject line : any ALL-CAPS line that looks like a subject name
    Chapter line : "<digit>.\t<CHAPTER NAME>\t<digit>" (tab-separated table row)
    Lecture line : "Lec. – N : <topic title>" or "Lec. - N : <topic title>"
    """

    lines = [clean(ln) for ln in raw_text.splitlines()]
    lines = [ln for ln in lines if ln]          # drop blanks

    result = {
        "class": None,
        "subject": None,
        "chapters": []
    }

    # ── 1. Extract class & subject from the first few lines ──────────────────
    # Patterns like: "CLASS – XII", "CLASS - XII", "CLASS XII"
    class_pattern   = re.compile(r"CLASS\s*[–\-]?\s*(\w+)", re.IGNORECASE)
    subject_pattern = re.compile(r"^[A-Z][A-Z &/\-]+$")   # all-caps subject name

    for line in lines[:10]:
        if result["class"] is None:
            m = class_pattern.search(line)
            if m:
                result["class"] = m.group(1).strip()
        if result["subject"] is None and subject_pattern.match(line):
            # Skip if it also matched the class line
            if not class_pattern.search(line):
                result["subject"] = line

    # ── 2. Chapter & lecture patterns ────────────────────────────────────────
    # Chapter row (from a tab-separated table):
    #   "1. TITLE   10"   or   "1.\tTITLE\t10"
    chapter_pattern = re.compile(
        r"^(\d+)\.?\s+([A-Z][A-Z &,/\(\)\-&':]+?)\s+(\d+)$"
    )

    # Lecture line:
    #   "Lec. – 1 : Some Topic"  or  "Lec. - 1 ; Some Topic"
    lecture_pattern = re.compile(
        r"Lec\.?\s*[–\-]\s*(\d+)\s*[;:]\s*(.+)", re.IGNORECASE
    )

    current_chapter = None

    for line in lines:
        # ── chapter? ─────────────────────────────────────────────────────────
        m = chapter_pattern.match(line)
        if m:
            current_chapter = {
                "chapter_no":     int(m.group(1)),
                "chapter_name":   clean(m.group(2)),
                "topics":         []
            }
            result["chapters"].append(current_chapter)
            continue

        # ── lecture? ─────────────────────────────────────────────────────────
        m = lecture_pattern.match(line)
        if m and current_chapter is not None:
            title = clean(m.group(2))
            current_chapter["topics"].extend(split_topics(title))

    return result


# ── CLI entry-point ───────────────────────────────────────────────────────────

def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse a class syllabus text file into JSON."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to the input text file. Reads from stdin if omitted."
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to write the JSON output. Prints to stdout if omitted."
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)."
    )
    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        print("Paste your syllabus below. Press Ctrl+D (or Ctrl+Z on Windows) when done.\n",
              file=sys.stderr)
        raw = sys.stdin.read()

    data = parse_syllabus(raw)
    output_json = json.dumps(data, indent=args.indent, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"✅  JSON written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


# ── built-in demo ─────────────────────────────────────────────────────────────

SAMPLE = """
CLASS – XII
MATHEMATICS
S.No.\tTOPIC\tNo. of Lecture
1.\tMOLE CONCEPT\t11
\tLec. – 1 : Basics of Chemistry : Matter & Its Classification 
\tLec. – 2 : Introduction to Elements, Atoms, Molecules, Ions & Compounds
\tLec. – 3 : Atomic mass, Atomic mass unit, Molecular mass and All types of different masses.
\tLec. – 4 : Mole, Mole of an atom, Mole of molecules etc.
\tLec. – 5 : Mole of gas, Mole of ions.
\tLec. – 6 : % Composition/Least Molecular weight/Vapour density
\tLec. – 7 : Empirical formula
\tLec. – 8 : Stoichiometry and Limiting Reagent.
\tLec. – 9 : % yield, % purity & Sequential Reactions
\tLec. – 10 : Concentration terms
\tLec. – 11 : Concentration terms, dilution & Question Practice
2.\tATOMIC STRUCTURE\t15
\tLec. – 1 : Discovery of fundamental particles of an atom : electron, proton and neutron
\tLec. – 2 : e/m Ratio & Millikan oil drop experiment
\tLec. – 3 : Thomson’s model + Rutherford’s model and its applications.
\tLec. – 4 : EM Waves and some important definitions.
\tLec. – 5 : Planck Quantum theory + Photoelectric effect.
\tLec. – 6 : Quantisation of energy levels & Hydrogen spectrum.
\tLec. – 7 : Questions on Hydrogen spectrum.
\tLec. – 8 : Bohr’s model.
\tLec. – 9 : Application of Bohr’s model.
\tLec. – 10 : Questions on Bohr’s model.
\tLec. – 11 : Rydberg formula and Drawbacks of Bohr’s model.
\tLec. – 12 : De-Broglie and Heisenberg Uncertainty Principle.
\tLec. – 13 : Wave Mechanical model and Quantum Numbers.
\tLec. – 14 : Shape, Energy and filling of orbitals.
\tLec. – 15 : Electronic configuration, Magnetic moment and Question practice.
3.\tPERIODIC CLASSIFICATION OF ELEMENTS\t11
\tLec. – 1 : Development of Periodic Table.
\tLec. – 2 : Mendeleev’s Periodic Table.
\tLec. – 3 : Modern Periodic Table
\tLec. – 4 : IUPAC Naming, Period and Block Identification & Exceptional Electronic Configuration.
\tLec. – 5 : Periodicity/Effective Nuclear Charge
\tLec. – 6 : Periodicity/Effective Nuclear Charge
\tLec. – 7 : Atomic Radius
\tLec. – 8 : Ionisation Energy and Its Application
\tLec. – 9 : Electron Affinity
\tLec. – 10 : Electronegativity and Its Applications
\tLec. – 11 : Question Practice
4.\tCHEMICAL BONDING\t20
\tLec. – 1 : Valency, Lewis Octet rule and Lewis Structure
\tLec. – 2 : Drawback of Lewis Octet Rule and Classification of Chemical Bonds.
\tLec. – 3 : Ionic Bond : Favourable Conditions of Ionic Bond Formation.
\tLec. – 4 : Lattice Energy and Born -Haber Cycle.
\tLec. – 5 : General Properties of Ionic Compounds and Hydration Energy.
\tLec. – 6 : Polarisation
\tLec. – 7 : Application of Polarisation
\tLec. – 8 : Solubility of Ionic Compounds
\tLec. – 9 : Covalent Bond / Covalency
\tLec. – 10 : VBT and Types of Overlapping
\tLec. – 11 : Question Practice
\tLec. – 12 : Hybridisation
\tLec. – 13 ; VSEPR
\tLec. – 14 : Different Shell Hybridisation Solid State Hybridisation & Hybridisation of Odd Electron Species.
\tLec. – 15 : Bond Parameters
\tLec. – 16 : Drago’s Hypothesis and Existence of Molecules.
\tLec. – 17 : Coordinate Bond and Dipole Moment
\tLec. – 18 : Dipole Moment
\tLec. – 19 : Molecular Orbital Theory
\tLec. – 20 : H-Bonding and Its Applications & Question Practice
5.\tINTRODUCTION TO P-BLOCK\t4
\tLec. – 1 : Inert Pair Effect and Back Bonding
\tLec. – 2 : Hydrolysis and Bridge Bonding
\tLec. – 3 : Silicates and Silicones
\tLec. – 4 : Allotropy
6.\tREDOX REACTIONS\t8
\tLec. – 1 : Introduction : Oxidation and Reduction
\tLec. – 2 : Oxidation Number and State
\tLec. – 3 : Types of Redox Reactions
\tLec. – 4 : Equivalent Weight
\tLec. – 5 : Normality
\tLec. – 6 : Law of Equivalence & Titrations
\tLec. – 7 : Balancing of Equations
\tLec. – 8 : Question Practice
7.\tEQUILIBRIUM (CHEMICAL)\t6
\tLec. – 1 : Introduction, Active Mass and Low of Mass Action
\tLec. – 2 : Equilibrium Constant : KC and Kp
\tLec. – 3 : Characteristics and Application of KC
\tLec. – 4 : Degree of Dissociation and Its Application.
\tLec. – 5 : Le-Chatlier’s Principle
\tLec. – 6 : Le-Chatlier’s Principle & Question Practice
8.\tIONIC EQUILIBRIUM\t14
\tLec. – 1 : Electrolytes : Acids, Bases and Salts.
\tLec. – 2 : Theory of Acids and Bases.
\tLec. – 3 : Properties of Water.
\tLec. – 4 : pH and Calculation of pH of Strong Acids and Bases.
\tLec. – 5 : pH Calculation of Mixtures of Strong Acids and Bases and Extremely diluted solutions.
\tLec. – 6 : Ostwald’s dilution law and factors affecting alpha.
\tLec. – 7 : Relation between Ka and Kb and Common Ion Effect.
\tLec. – 8 : Hydrolysis of Salts.
\tLec. – 9 : Hydrolysis of Salts.
\tLec. – 10 : Buffer Solution
\tLec. – 11 : Buffer Solutions and Its Applications.
\tLec. – 12 : Solubility
\tLec. – 13 : KSP and its applications
\tLec. – 14 : Types of Solvent & Question Practice
9.\tTHERMODYNAMICS\t18
\tLec. – 1 : Ideal Gas Equation
\tLec. – 2 : Dalton’s Law of Partial Pressure and Graham’s Law
\tLec. – 3 : KTG
\tLec. – 4 : System and Types
\tLec. – 5 : State of System, State and Path Function
\tLec. – 6 : Thermodynamic Properties
\tLec. – 7 : Types of Processes
\tLec. – 8 : Heat and Work PV-Graph
\tLec. – 9 : Internal Energy
\tLec. – 10 : Enthalpy
\tLec. – 11 : Heat Capacities
\tLec. – 12 : Degree of Freedom and Calorimetry
\tLec. – 13 : Work done in various process
\tLec. – 14 : Entropy
\tLec. – 15 : Gibbs Free Energy
\tLec. – 16 : Thermochemistry
\tLec. – 17 : Thermochemistry
\tLec. – 18 : Hess’s Law & Question Practice
10.\tORGANIC CHEMISTRY\t20
\tIUPAC Nomenclature and Isomerism :
\tLec. – 1 : Introduction : Vital Force Theory and Classification of Organic Compounds (Hydrogen)
\tLec. – 2 : Hydrocarbon Classification and Representation of Organic Compounds.
\tLec. – 3 : Homologous Series and Functional Groups.
\tLec. – 4 : IUPAC Nomenclature
\tLec. – 5 : IUPAC Nomenclature
\tLec. – 6 : IUPAC Nomenclature of Functional Groups
\tLec. – 8 : IUPAC Nomenclature of Mixed Functional Groups
\tLec. – 9 : IUPAC Nomenclature of Cyclic Compounds
\tLec. – 10 : IUPAC Nomenclature of Aromatic Compounds
\tLec. – 11 : Isomerism : Structural Chain
\tLec. – 12 : Position and Metamerism
\tLec. – 13 : Functional Isomerism and Calculation of Total no. of Structural Isomerism.
\tLec. – 14 : Geometrical Isomerism
\tLec. – 15 : Geometrical Isomerism
\tLec. – 16 : Optical Isomerism (Optical Activity, Chirality and Elements of Symmetry)
\tLec. – 17 : Enantiomers, Diastereo-isomers, Meso Compounds and Racemic Mixtures.
\tLec. – 18 : Calculation of Total no. of Optical and Stereoisomers.
\tLec. – 19 : Conformational Isomerism.
\tLec. – 20 : Question Practice
11.\tGENERAL ORGANIC CHEMISTRY\t10
\tLec. – 1 : Electronic Effects and their Applications : Inductive Effect
\tLec. – 2 : Resonance Effect (Mesomeric Effect)
\tLec. – 3 : Resonance Effect (Mesomeric Effect)
\tLec. – 4 : Aromaticity
\tLec. – 5 : Aromaticity and Hyperconjugation
\tLec. – 6 : Stability of Intermediates
\tLec. – 7 : Stability of Intermediates
\tLec. – 8 : Acidic and Basic Strength
\tLec. – 9 : Tautomerism
\tLec. – 10 : Question Practice
12\tHYDROCARBONS\t8
\tLec. – 1 : Alkanes : Method of Preparation & Physical Properties
\tLec. – 2 : Chemical Properties of Alkane : Free Radical Substitution Reaction.
\tLec. – 3 : Alkene : Method of Preparation & Physical Properties
\tLec. – 4 : Chemical Properties of Alkene : Electrophilic Addition Reaction
\tLec. – 5 : Alkyne : Method of Preparation & Physical Properties
\tLec. – 6 : Chemical Properties of Alkyne.
\tLec. – 7 : Benzene : Method of Preparation
\tLec. – 8 : Chemical Properties of Benzene : Electrophilic Substitution Reaction.
"""

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        # No args → run the built-in demo instead of asking for stdin
        data = parse_syllabus(SAMPLE)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        main()