"""The evidence base: published empirical benchmarks the model is confronted with.

A benchmark is one observable quantity with a published value: what was measured, where, with what uncertainty,
the model quantity it is compared with (a moment of the simulation, or a declared assumption), and how far the
measured setting is from the model's. Every benchmark carries its source. The set below is what the literature
review behind the Lab could support in November 2026; it is deliberately small and mostly made of analogues from
other regulation (data protection, carbon pricing) and other technologies (autonomous vehicles, cyber incidents),
because that is what exists. An authority with its own data replaces or extends it with a JSON file
(PSL_BENCHMARKS, same fields); the set in force is hashed into the battery approved at Gate 1.

Fields
  id, title          short name and what was measured
  mechanisms         the mechanisms of the register (mechanisms.py) the benchmark bears on
  kind               direct      the same quantity observed for AI
                     official    an official ex ante estimate for an AI law
                     analogue    the corresponding quantity in another sector, technology or body of regulation
  moment             the model quantity (validation.MOMENTS), or "assumption" with `assumption` and optionally
                     `transform` for a benchmark that bears on one declared assumption directly
  instrument         the library instrument the moment is computed under ("baseline" for the status quo)
  observations       the published values, each with a label; the benchmark's value is their mean
  se                 standard error of the value: given, or the standard deviation of the observations over root n
  se_basis           where the standard error comes from (an honest note when it is an allowance, not an estimate)
  transport          standard deviation allowed for the distance between the measured setting and the model's (the
                     model discrepancy of the calibration literature); a declared judgement, stated with its reason
  unit, sources, mapping, caveat

NOT_USED lists evidence that was examined and set aside, with the reason: what the layer cannot test is part of
its result.
"""

import hashlib
import json
import math
import os

KINDS = ("direct", "official", "analogue")


def _annual(a, b, years):
    return (b / a) ** (1.0 / years) - 1.0


BENCHMARKS = (
    {"id": "incident_growth", "title": "Annual growth of recorded AI incidents",
     "mechanisms": ["incident_hazard", "capability_and_release"], "kind": "direct",
     "moment": "incident_growth", "instrument": "baseline", "unit": "a year",
     "observations": [{"label": "AI Incident Database, 2023 to 2024", "value": 0.564},
                      {"label": "AI Incident Database, 2024 to 2025 (233 to 362)", "value": 362.0 / 233.0 - 1.0}],
     "se": 0.08, "se_basis": "Poisson error of the annual counts (about 149, 233 and 362)",
     "transport": 0.25,
     "transport_basis": "the database is compiled from media reports and its curators attribute an unknown share of the rise to "
                        "reporting and attention; the model counts incidents at eight firm archetypes, not in the whole economy",
     "sources": [{"cite": "Stanford HAI, AI Index Report 2025, chapter 3 (233 incidents in 2024, up 56.4% on 2023)",
                  "url": "https://hai-production.s3.amazonaws.com/files/hai_ai-index-report-2025_chapter3_final.pdf"},
                 {"cite": "Stanford HAI, AI Index Report 2026, responsible AI (362 incidents in 2025)",
                  "url": "https://hai.stanford.edu/ai-index/2026-ai-index-report/responsible-ai"}],
     "mapping": "the status quo's expected number of incidents in each year of the horizon; the benchmark is compared with the "
                "average annual growth of that count",
     "caveat": "growth in recorded incidents is joint growth in harms, deployment and attention"},

    {"id": "trust_trend", "title": "Annual change in public trust in AI and AI companies",
     "mechanisms": ["adoption_and_trust"], "kind": "direct",
     "moment": "trust_trend", "instrument": "baseline", "unit": "a year, relative",
     "observations": [{"label": "Edelman, trust in AI companies, 28 country average, 61% to 53% over five years", "value": _annual(61, 53, 5)},
                      {"label": "Edelman, trust in AI companies, United States, 50% to 35% over five years", "value": _annual(50, 35, 5)},
                      {"label": "Pew, US adults not more concerned than excited about AI, 63% (2021) to 50% (2025)", "value": _annual(63, 50, 4)}],
     "se": None, "se_basis": "standard deviation of the three series over root three",
     "transport": 0.02,
     "transport_basis": "a survey share is compared with the model's trust index, which starts at one and has no survey counterpart",
     "sources": [{"cite": "Edelman Trust Barometer 2024, key insights around AI",
                  "url": "https://www.edelman.com/sites/g/files/aatuss191/files/2024-03/Trust%20Tech%20Sector%20Top%20Findings.pdf"},
                 {"cite": "Pew Research Center, How Americans view AI and its impact on people and society, September 2025",
                  "url": "https://www.pewresearch.org/wp-content/uploads/sites/20/2025/09/PS_2025.9.15_AI-and-its-impact_report.pdf"}],
     "mapping": "the status quo's trust index at the end of the horizon, as an annual relative change from its starting value",
     "caveat": "the period measured had no AI specific regulation in most of the countries surveyed, which is what the status quo "
               "represents; the fall may have causes other than harm"},

    {"id": "trust_recovery", "title": "Share of a fall in trust recovered about nine months after a salient incident",
     "mechanisms": ["adoption_and_trust"], "kind": "analogue",
     "moment": "assumption", "assumption": "trust_recovery", "transform": {"name": "recovered_fraction", "months": 9},
     "instrument": None, "unit": "share",
     "observations": [{"label": "AAA: afraid to ride in a self driving vehicle, 63% before the 2018 crashes, 73% after, 71% in January 2019",
                       "value": (73.0 - 71.0) / (73.0 - 63.0)}],
     "se": 0.29, "se_basis": "each survey has a margin of error of four points at 95% (about 1,000 interviews); delta method on the ratio",
     "transport": 0.20,
     "transport_basis": "another technology, and fear of using it is not trust in the firms that build it; the interval between "
                        "the two surveys is known to within a few months",
     "sources": [{"cite": "AAA, Three in four Americans remain afraid of fully self driving vehicles, March 2019",
                  "url": "https://newsroom.aaa.com/2019/03/americans-fear-self-driving-cars-survey"},
                 {"cite": "Smart Cities Dive, AAA poll, March 2019 (the 2018 figure and the crashes)",
                  "url": "https://www.smartcitiesdive.com/news/aaa-poll-autonomous-vehicles-fear/550766/"}],
     "mapping": "with monthly recovery r and no further incident, the share of a fall recovered after nine months is 1 - (1 - r)^9",
     "caveat": "one episode"},

    {"id": "compliance_cost_share", "title": "Compliance cost of a high risk regime as a share of development spending in scope",
     "mechanisms": ["firm_choice", "enforcement"], "kind": "official",
     "moment": "compliance_cost_share", "instrument": "risk_tiering", "unit": "share",
     "observations": [{"label": "European Commission impact assessment: roughly 4 to 5% of a EUR 170,000 system", "value": 0.045},
                      {"label": "Supporting study (Renda et al.): about 17% with external services and staff", "value": 0.17}],
     "se": None, "se_basis": "standard deviation of the two ex ante estimates over root two",
     "transport": 0.03,
     "transport_basis": "an ex ante estimate per system built from a standard cost model, which its authors call a theoretical maximum; "
                        "the model's cost is an instrument parameter applied to revenue in scope",
     "sources": [{"cite": "European Commission, SWD(2021) 84 final, impact assessment of the AI Act",
                  "url": "https://data.consilium.europa.eu/doc/document/ST-8115-2021-ADD-2/en/pdf"},
                 {"cite": "Renda et al. (2021), Study to support an impact assessment of regulatory requirements for AI in Europe",
                  "url": "https://artificialintelligenceact.eu/wp-content/uploads/2022/06/AIA-COM-Impact-Assessment-3-21-April.pdf"}],
     "mapping": "under risk tiering, compliance spending over the R&D spending of the firms in scope on the activity in scope, while in force",
     "caveat": "the share of systems that are high risk was never estimated by any party to the assessment"},

    {"id": "profit_effect", "title": "Effect of a horizontal compliance regime on the profits of firms in scope",
     "mechanisms": ["revenue_growth", "firm_choice"], "kind": "analogue",
     "moment": "profit_effect", "instrument": "risk_tiering", "unit": "relative",
     "observations": [{"label": "GDPR, exposed firms in 61 countries: profits down about 8% (Chen, Frey and Presidente)", "value": -0.08},
                      {"label": "GDPR, data intensive EU sectors: profit margin down 1.9% (Koski and Valmari)", "value": -0.019},
                      {"label": "GDPR, large technology firms: no significant effect (Chen, Frey and Presidente)", "value": 0.0}],
     "se": None, "se_basis": "standard deviation of the three estimates over root three",
     "transport": 0.03,
     "transport_basis": "data protection, not AI; a broad cross section of firms against eight archetypes that are mostly large",
     "sources": [{"cite": "Chen, Frey and Presidente (2022), Privacy regulation and firm performance, Oxford Martin working paper 2022-1",
                  "url": "https://oms-www.files.svdcdn.com/production/downloads/Privacy-Regulation-and-Firm-Performance-Giorgio-WP-Upload-2022-1.pdf"},
                 {"cite": "Johnson (2022), Economic research on privacy regulation: lessons from the GDPR and beyond, NBER working paper 30705",
                  "url": "https://www.nber.org/system/files/working_papers/w30705/w30705.pdf"}],
     "mapping": "under risk tiering, the industry's earnings against the status quo on the same paths, over the months in force",
     "caveat": "the estimates differ in sample, outcome and period; the mean of three is a summary, not a pooled estimate"},

    {"id": "enforcement_return", "title": "Equity return when a horizontal regime becomes enforceable",
     "mechanisms": ["market"], "kind": "analogue",
     "moment": "enforcement_return", "instrument": "risk_tiering", "unit": "return",
     "observations": [{"label": "GDPR, 1,013 US firms, week of enforcement: lower bound", "value": -0.006},
                      {"label": "GDPR, 1,013 US firms, week of enforcement: upper bound", "value": -0.011}],
     "se": None, "se_basis": "half the published range",
     "transport": 0.01,
     "transport_basis": "a week against the model's month; most of the cost of a law announced years earlier is in the price before it applies",
     "sources": [{"cite": "Motoki and Pinto (2024), Journal of Business Finance and Accounting (press summary)",
                  "url": "https://www.eurekalert.org/news-releases/1051661"}],
     "mapping": "under risk tiering, the value weighted index's change in the month the instrument takes effect, less the status quo's on the same path",
     "caveat": "the enforcement date return understates the total cost capitalised"},

    {"id": "fine_return", "title": "Equity return of a firm when a regulatory fine is announced",
     "mechanisms": ["market", "enforcement"], "kind": "analogue",
     "moment": "fine_return", "instrument": "risk_tiering", "unit": "return",
     "observations": [{"label": "GDPR fines, 25 announcements, window (0,1)", "value": -0.0064},
                      {"label": "window (0,2)", "value": -0.0072},
                      {"label": "window (0,3)", "value": -0.0096},
                      {"label": "window (0,4)", "value": -0.0064}],
     "se": 0.0025, "se_basis": "the published t statistics (about 3 on estimates of about 0.007)",
     "transport": 0.01,
     "transport_basis": "data protection fines, most of them small against the firm's size; days against the model's month",
     "sources": [{"cite": "Ford et al. (2021), The impact of GDPR infringement fines on the market value of firms, ECCWS",
                  "url": "https://repository.uel.ac.uk/download/55420e51e0d25c813c8ab1d701f7b6e5093ba609fac84a9d9a3a874cb19e3a0d/689257/The%20Impact%20of%20GDPR%20Infringement%20Fines%20on%20the%20Market%20Value%20of%20Firms.pdf"}],
     "mapping": "under risk tiering, a fined firm's log return in the month of the fine less the index's",
     "caveat": "25 announcements; windows beyond five days are not significant in the source"},

    {"id": "incident_return", "title": "Equity return of a firm when a serious incident becomes public",
     "mechanisms": ["market"], "kind": "analogue",
     "moment": "incident_return", "instrument": "baseline", "unit": "return",
     "observations": [{"label": "Cyberattacks with loss of personal financial information, 2005 to 2014, three day window", "value": -0.0112}],
     "se": 0.004, "se_basis": "an allowance: the standard error was not in the summary consulted",
     "transport": 0.01,
     "transport_basis": "data breaches, not AI incidents; three days against the model's month",
     "sources": [{"cite": "Kamiya, Kang, Kim, Milidonis and Stulz, What is the impact of successful cyberattacks on target firms? "
                          "(authors' summary, Harvard Law School Forum on Corporate Governance, March 2018; Journal of Financial Economics 139(3), 2021)",
                  "url": "https://corpgov.law.harvard.edu/2018/03/30/what-is-the-impact-of-successful-cyberattacks-on-target-firms/"}],
     "mapping": "under the status quo, the log return of a firm in a month with a major incident at that firm, less the index's",
     "caveat": "the model's major incident is defined by monetised harm, a breach by the data lost"},

    {"id": "leakage_share", "title": "Share of regulated activity displaced abroad by a unilateral regime",
     "mechanisms": ["relocation"], "kind": "analogue",
     "moment": "leakage_share", "instrument": "frontier_licensing", "unit": "share",
     "observations": [{"label": "Carbon leakage ratio without border adjustment, 25 studies, 310 estimates: mean", "value": 0.14}],
     "se": 0.05, "se_basis": "a quarter of the published range (5% to 25%)",
     "transport": 0.07,
     "transport_basis": "carbon pricing, and mostly ex ante models; AI activity is divisible in some respects (where a model is "
                        "trained) and not in others (one set of weights)",
     "sources": [{"cite": "Branger and Quirion (2014), Ecological Economics 99",
                  "url": "https://econpapers.repec.org/RePEc:hal:journl:hal-01137932"}],
     "mapping": "under frontier licensing, the revenue of the firms in scope booked offshore in the last year of the horizon, as a share of their revenue",
     "caveat": "for AI regulation leakage is theorised, surveyed and anecdotal, not measured"},

    {"id": "insurance_loading", "title": "Premium above expected claims in liability insurance",
     "mechanisms": ["liability_and_insurance"], "kind": "analogue",
     "moment": "assumption", "assumption": "insurance_loading", "transform": None, "instrument": None, "unit": "share",
     "observations": [{"label": "US property and casualty industry 2023: premiums over losses and loss expenses (76.2%), less one", "value": 1.0 / 0.762 - 1.0},
                      {"label": "2022 (76.4%)", "value": 1.0 / 0.764 - 1.0}],
     "se": 0.005, "se_basis": "two years of an industry aggregate",
     "transport": 0.15,
     "transport_basis": "all property and casualty lines; cover for AI liability is not an established line",
     "sources": [{"cite": "NAIC, U.S. property and casualty and title insurance industries, 2023 full year results",
                  "url": "https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf"}],
     "mapping": "the assumption itself: the premium charged above the expected liability under a mandate",
     "caveat": "an industry average over lines with very different tails"},

    {"id": "insurance_resource_share", "title": "Share of the insurance loading used up by underwriting and administration",
     "mechanisms": ["liability_and_insurance", "welfare_bases"], "kind": "analogue",
     "moment": "assumption", "assumption": "insurance_admin_share", "transform": None, "instrument": None, "unit": "share",
     "observations": [{"label": "US property and casualty industry 2023: expense ratio 24.9% over premiums less losses and loss expenses (23.8%)",
                       "value": 0.249 / (1.0 - 0.762)},
                      {"label": "2022: 25.7% over 23.6%", "value": 0.257 / (1.0 - 0.764)}],
     "se": 0.02, "se_basis": "two years of an industry aggregate",
     "transport": 0.25,
     "transport_basis": "all property and casualty lines, in two years with an underwriting loss (the share is above one because "
                        "expenses exceeded the loading)",
     "sources": [{"cite": "NAIC, U.S. property and casualty and title insurance industries, 2023 full year results",
                  "url": "https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf"}],
     "mapping": "the assumption itself: the share of the loading that is a real resource cost and not a transfer to insurers",
     "caveat": "the model's range (0.25 to 0.75) treats part of the loading as insurers' margin; in these two years there was none"},
)

NOT_USED = (
    {"evidence": "Meta analysis of trust and intention to use a technology: r = 0.503 (95% interval 0.470 to 0.535, 128 samples, 50,667 respondents)",
     "source": {"cite": "Kuen, Westmattelmann, Bruckes and Schewe (2023), Electronic Markets 33:61",
                "url": "https://link.springer.com/content/pdf/10.1007/s12525-023-00672-1.pdf"},
     "bears_on": "adoption_and_trust (trust_elasticity)",
     "why_not": "it supports the sign of the trust channel and nothing more: a correlation between stated attitudes in studies of online "
                "shopping, banking and e-health is not an elasticity of realised adoption to trust, and cannot be turned into one without "
                "the dispersion of both. The elasticity stays unidentified."},
    {"evidence": "The size of the fall in trust after a salient incident (AAA: afraid to ride rose from 63% to 73% after two fatal crashes)",
     "source": {"cite": "AAA (2019)", "url": "https://newsroom.aaa.com/2019/03/americans-fear-self-driving-cars-survey"},
     "bears_on": "adoption_and_trust (trust_harm_sensitivity)",
     "why_not": "the model moves trust with monetised harm, and two deaths are a small monetised harm: an incident of that size moves the "
                "model's trust by less than a tenth of a percent. The episode says trust answers to salience; the model's form cannot "
                "show that. Recorded as a limit of the mechanism, not scored, because the survey question is about using a vehicle."},
    {"evidence": "Estimates of AI's effect on output: total factor productivity up by no more than 0.66% over ten years (Acemoglu); 7% of global "
                 "GDP over ten years (Goldman Sachs); $2.6 to $4.4 trillion a year (McKinsey)",
     "source": {"cite": "Acemoglu (2025), Economic Policy 40(121)", "url": "https://economics.mit.edu/sites/default/files/2024-05/The%20Simple%20Macroeconomics%20of%20AI.pdf"},
     "bears_on": "welfare_bases (productivity_base_bn, consumer_surplus_base_bn)",
     "why_not": "the model declares its benefit bases in $bn a year and declares no size for the jurisdiction's economy, so there is nothing "
                "to divide by; and the estimates span an order of magnitude."},
    {"evidence": "Elicited probabilities of catastrophic harm from AI",
     "source": {"cite": "expert and forecaster elicitations (no observed frequency exists)", "url": ""},
     "bears_on": "catastrophic_tail",
     "why_not": "elicitations, not observations; they define catastrophe differently from the model and have no validation record."},
    {"evidence": "A loss distribution for AI incidents",
     "source": {"cite": "AI Incident Database; MIT AI Incident Tracker; OECD AI Incidents Monitor", "url": "https://incidentdatabase.ai"},
     "bears_on": "severity",
     "why_not": "none has been published: the taxonomies exist, the magnitudes are not recorded."},
    {"evidence": "GDPR and venture investment: monthly EU deals down 26.1% against US ventures",
     "source": {"cite": "Jia, Jin and Wagman (2021), Marketing Science 40(4)", "url": "https://econpapers.repec.org/RePEc:inm:ormksc:v:40:y:2021:i:4:p:661-684"},
     "bears_on": "revenue_growth",
     "why_not": "the model has no entry or investment margin to compare it with."},
)

REQUIRED = ("id", "title", "mechanisms", "kind", "moment", "unit", "observations", "transport", "sources")


def resolve(b):
    """A benchmark with its value and standard error worked out from the observations."""
    obs = [float(o["value"]) for o in b["observations"]]
    n = len(obs)
    value = sum(obs) / n
    se = b.get("se")
    if se is None:
        if n < 2:
            raise ValueError(f"benchmark {b['id']}: a single observation needs a standard error")
        sd = math.sqrt(sum((x - value) ** 2 for x in obs) / (n - 1))
        se = sd / math.sqrt(n)
    out = dict(b)
    out["value"], out["se"], out["n_observations"] = value, float(se), n
    out["sd_total"] = math.sqrt(float(se) ** 2 + float(b["transport"]) ** 2)
    return out


def validate(items, mechanism_ids=None, assumption_keys=None, moments=None):
    """Check a list of benchmarks and return (resolved, problems). A benchmark with a problem is dropped and reported."""
    good, problems, seen = [], [], set()
    for b in items:
        bid = str(b.get("id", "?"))
        miss = [k for k in REQUIRED if b.get(k) in (None, "", [])]
        if miss:
            problems.append(f"{bid}: missing {', '.join(miss)}"); continue
        if bid in seen:
            problems.append(f"{bid}: listed twice"); continue
        if b["kind"] not in KINDS:
            problems.append(f"{bid}: kind must be one of {', '.join(KINDS)}"); continue
        if not all(isinstance(s, dict) and s.get("cite") for s in b["sources"]):
            problems.append(f"{bid}: every source needs a citation"); continue
        if not (float(b["transport"]) >= 0):
            problems.append(f"{bid}: transport must be zero or more"); continue
        if b["moment"] == "assumption":
            if assumption_keys is not None and b.get("assumption") not in assumption_keys:
                problems.append(f"{bid}: unknown assumption {b.get('assumption')}"); continue
        elif moments is not None and b["moment"] not in moments:
            problems.append(f"{bid}: unknown moment {b['moment']}"); continue
        if mechanism_ids is not None and any(m not in mechanism_ids for m in b["mechanisms"]):
            problems.append(f"{bid}: unknown mechanism in {b['mechanisms']}"); continue
        try:
            good.append(resolve(b))
        except (ValueError, TypeError, KeyError) as e:
            problems.append(f"{bid}: {e}"); continue
        seen.add(bid)
    return good, problems


def load(path=None):
    """The benchmarks in force: the built in set, or the JSON file at `path` ({"benchmarks": [...], "replace": bool}; a
    plain list replaces). Returns the raw items; validate() resolves them."""
    items = [dict(b) for b in BENCHMARKS]
    if not path:
        return items
    with open(os.path.expanduser(path)) as f:
        doc = json.load(f)
    extra = doc if isinstance(doc, list) else doc.get("benchmarks", [])
    if isinstance(doc, list) or doc.get("replace"):
        return [dict(b) for b in extra]
    by = {b["id"]: b for b in items}
    for b in extra:
        by[b.get("id")] = dict(b)
    return list(by.values())


def digest(items):
    return hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def table(items=None):
    return [resolve(b) for b in (items if items is not None else BENCHMARKS)]
